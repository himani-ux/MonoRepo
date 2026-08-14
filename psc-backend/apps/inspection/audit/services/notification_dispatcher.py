"""Audit notification dispatcher for Phase 9 Step 9.1."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from django.db import DatabaseError, connection, transaction
from django.utils import timezone

from apps.accounts.models import OfficeUser
from apps.inspection.audit.models import MasterHodAssignment, MasterSlackChannel, NotificationDeliveryLog
from apps.notifications.models import Notification


SUPPORTED_AUDIT_NOTIFICATION_TYPES = (
    "AUDIT_SCHEDULED",
    "AUDIT_NC_RAISED",
    "AUDIT_CANCELLED",
    "AUDIT_OVERDUE",
    "AUDIT_CRITICAL_OVERDUE",
    "AUDIT_EXTENSION_APPROVED",
    "NC_EFFECTIVENESS_REVIEW_DUE",
)

IN_SYSTEM = "IN_SYSTEM"
EMAIL = "EMAIL"
SLACK = "SLACK"
SYSTEM_ACTOR = "system.audit_notification_dispatcher"


@dataclass(frozen=True)
class AuditNotificationRecipient:
    recipient_type: str
    recipient_id: str
    email: str | None = None


@dataclass(frozen=True)
class AuditNotificationDispatchResult:
    notification_type: str
    recipients: list[AuditNotificationRecipient]
    notifications: list[Notification]
    delivery_logs: list[NotificationDeliveryLog]


def dispatch_audit_notification(
    *,
    notification_type: str,
    title: str,
    message: str,
    entity_type: str,
    entity_id: uuid.UUID | str,
    vessel_id: uuid.UUID | str | None = None,
    office_dept: str | None = None,
    recipients: Iterable[AuditNotificationRecipient] | None = None,
    include_email: bool = True,
    include_slack: bool = True,
    actor: str = SYSTEM_ACTOR,
) -> AuditNotificationDispatchResult:
    """Create in-system Audit notifications and per-channel delivery logs."""

    normalized_type = str(notification_type or "").strip().upper()
    if normalized_type not in SUPPORTED_AUDIT_NOTIFICATION_TYPES:
        raise ValueError(f"Unsupported Audit notification type: {notification_type}")

    resolved_recipients = list(recipients) if recipients is not None else resolve_audit_notification_recipients(
        vessel_id=vessel_id,
        office_dept=office_dept,
    )
    resolved_recipients = _dedupe_recipients(resolved_recipients)

    normalized_vessel_id = _normalize_uuid(vessel_id)
    normalized_entity_id = _normalize_uuid(entity_id)
    now = timezone.now()
    vessel_email = _get_vessel_email(normalized_vessel_id) if normalized_vessel_id else None
    slack_channel = _get_slack_channel(normalized_vessel_id, normalized_type) if normalized_vessel_id else None
    notifications: list[Notification] = []
    delivery_logs: list[NotificationDeliveryLog] = []

    with transaction.atomic():
        for recipient in resolved_recipients:
            notification = Notification.objects.create(
                recipient_type=recipient.recipient_type,
                recipient_id=recipient.recipient_id,
                vessel_id=normalized_vessel_id,
                notification_type=normalized_type,
                title=str(title or "")[:200],
                message=str(message or "")[:500],
                entity_type=str(entity_type or "")[:30],
                entity_id=normalized_entity_id,
            )
            notifications.append(notification)

            delivery_logs.append(
                NotificationDeliveryLog.objects.create(
                    psc_notification_id=_legacy_notification_id(notification.id),
                    channel=IN_SYSTEM,
                    recipient_address=recipient.recipient_id,
                    status="SENT",
                    attempt_count=1,
                    first_attempted_at=now,
                    last_attempted_at=now,
                    sent_at=now,
                    created_by=actor,
                )
            )

            if include_email:
                email_address = _email_for_recipient(recipient, vessel_email=vessel_email)
                email_status = "QUEUED" if email_address else "FAILED_PERMANENT"
                delivery_logs.append(
                    NotificationDeliveryLog.objects.create(
                        psc_notification_id=_legacy_notification_id(notification.id),
                        channel=EMAIL,
                        recipient_address=email_address,
                        status=email_status,
                        attempt_count=0,
                        last_error=None if email_address else _email_missing_error(vessel_id=normalized_vessel_id),
                        created_by=actor,
                    )
                )

            if include_slack and normalized_vessel_id and not office_dept:
                delivery_logs.append(
                    NotificationDeliveryLog.objects.create(
                        psc_notification_id=_legacy_notification_id(notification.id),
                        channel=SLACK,
                        recipient_address=slack_channel,
                        status="QUEUED" if slack_channel else "FAILED_PERMANENT",
                        attempt_count=0,
                        last_error=None if slack_channel else "SLACK_CHANNEL_NOT_CONFIGURED",
                        created_by=actor,
                    )
                )

    return AuditNotificationDispatchResult(
        notification_type=normalized_type,
        recipients=resolved_recipients,
        notifications=notifications,
        delivery_logs=delivery_logs,
    )


def resolve_audit_notification_recipients(
    *,
    vessel_id: uuid.UUID | str | None = None,
    office_dept: str | None = None,
    today: date | None = None,
) -> list[AuditNotificationRecipient]:
    if vessel_id:
        return _resolve_vessel_recipients(vessel_id)
    if office_dept:
        hod = _resolve_office_hod(office_dept, today=today)
        return [hod] if hod is not None else []
    return []


def _resolve_vessel_recipients(vessel_id: uuid.UUID | str) -> list[AuditNotificationRecipient]:
    normalized_vessel_id = _normalize_uuid(vessel_id)
    if not normalized_vessel_id:
        return []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT h.CrewID, COALESCE(r.rank_name, h.rank_name), h.department_name
                FROM HRM501 h
                INNER JOIN Crew_Onboarding_History coh
                    ON coh.CrewID = h.CrewID
                LEFT JOIN master_applied_rank r
                    ON r.id = h.rank_name
                WHERE coh.Vessel = %s
                  AND coh.SignOffDate IS NULL
                  AND COALESCE(coh.is_active, 1) <> 0
                  AND COALESCE(coh.is_deleted, 0) = 0
                  AND COALESCE(h.is_active, 1) <> 0
                  AND COALESCE(h.is_deleted, 0) = 0
                """,
                [normalized_vessel_id],
            )
            rows = cursor.fetchall()
    except DatabaseError:
        return []

    recipients: list[AuditNotificationRecipient] = []
    rank_tokens = ("master", "captain", "chief officer", "chief mate", "chief engineer")
    for crew_id, rank_name, department_name in rows:
        rank_text = str(rank_name or "").lower()
        dept_text = str(department_name or "").lower()
        if any(token in rank_text for token in rank_tokens) or "head" in rank_text or "hod" in rank_text:
            recipients.append(AuditNotificationRecipient(recipient_type="CREW", recipient_id=str(crew_id)))
            continue
        if "head" in dept_text or "hod" in dept_text:
            recipients.append(AuditNotificationRecipient(recipient_type="CREW", recipient_id=str(crew_id)))
    return recipients


def _resolve_office_hod(
    office_dept: str,
    *,
    today: date | None = None,
) -> AuditNotificationRecipient | None:
    current_date = today or timezone.localdate()
    try:
        queryset = MasterHodAssignment.objects.filter(
            dept=str(office_dept or "").strip().upper(),
            effective_from__lte=current_date,
        ).filter(models_effective_to_filter(current_date))
        confirmed = queryset.filter(is_acting=False).order_by("-effective_from", "-created_date").first()
        assignment = confirmed or queryset.filter(is_acting=True).order_by("-effective_from", "-created_date").first()
    except DatabaseError:
        return None
    if assignment is None:
        return None
    return AuditNotificationRecipient(
        recipient_type="OFFICE",
        recipient_id=assignment.user_id,
        email=_office_email(assignment.user_id),
    )


def models_effective_to_filter(current_date: date):
    from django.db.models import Q

    return Q(effective_to__isnull=True) | Q(effective_to__gte=current_date)


def _office_email(user_id: str) -> str | None:
    try:
        user = OfficeUser.objects.filter(employee_id__iexact=str(user_id), is_active=True, is_deleted=False).first()
    except DatabaseError:
        return None
    if user is None:
        return None
    email = str(user.email_id or "").strip()
    return email or None


def _get_vessel_email(vessel_id: str | None) -> str | None:
    if not vessel_id:
        return None
    compact = vessel_id.replace("-", "").lower()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT Email
                FROM VesselData
                WHERE (
                    lower(replace(CAST(id AS char), '-', '')) = %s
                    OR lower(CAST(id AS char)) = %s
                )
                  AND COALESCE(is_active, 1) <> 0
                  AND COALESCE(is_deleted, 0) = 0
                """,
                [compact, vessel_id.lower()],
            )
            row = cursor.fetchone()
    except DatabaseError:
        return None
    if not row:
        return None
    email = str(row[0] or "").strip()
    return email or None


def _get_slack_channel(vessel_id: str | None, notification_type: str) -> str | None:
    if not vessel_id:
        return None
    try:
        channel = (
            MasterSlackChannel.objects.filter(
                scope_type="VESSEL",
                scope_value__iexact=vessel_id,
                is_active=True,
            )
            .order_by("channel_name")
            .first()
        )
    except DatabaseError:
        return None
    if channel is None:
        return None
    configured_types = {part.strip().upper() for part in channel.notification_types_csv.split(",") if part.strip()}
    if configured_types and notification_type not in configured_types and "ALL" not in configured_types:
        return None
    return channel.channel_name


def _email_for_recipient(recipient: AuditNotificationRecipient, *, vessel_email: str | None) -> str | None:
    if vessel_email:
        return vessel_email
    email = str(recipient.email or "").strip()
    return email or None


def _email_missing_error(*, vessel_id: str | None) -> str:
    return "CMS_NO_EMAIL_ON_FILE" if vessel_id else "RECIPIENT_EMAIL_MISSING"


def _legacy_notification_id(value: object) -> str:
    if isinstance(value, uuid.UUID):
        return value.hex
    raw = str(value or "").strip()
    try:
        return uuid.UUID(raw).hex
    except ValueError:
        return raw.replace("-", "")[:32]


def _normalize_uuid(value: uuid.UUID | str | None) -> str | None:
    if value in (None, ""):
        return None
    try:
        return str(uuid.UUID(str(value)))
    except ValueError:
        return str(value)


def _dedupe_recipients(recipients: Iterable[AuditNotificationRecipient]) -> list[AuditNotificationRecipient]:
    seen: set[tuple[str, str]] = set()
    deduped: list[AuditNotificationRecipient] = []
    for recipient in recipients:
        recipient_type = str(recipient.recipient_type or "").strip().upper()
        recipient_id = str(recipient.recipient_id or "").strip()
        if not recipient_type or not recipient_id:
            continue
        key = (recipient_type, recipient_id.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            AuditNotificationRecipient(
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                email=recipient.email,
            )
        )
    return deduped


__all__ = [
    "SUPPORTED_AUDIT_NOTIFICATION_TYPES",
    "AuditNotificationDispatchResult",
    "AuditNotificationRecipient",
    "dispatch_audit_notification",
    "resolve_audit_notification_recipients",
]
