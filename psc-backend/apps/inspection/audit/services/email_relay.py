"""Audit notification email relay using the inherited Django SMTP pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import NotificationDeliveryLog
from apps.notifications.models import Notification

EMAIL_CHANNEL = "EMAIL"
QUEUED_STATUSES = ("QUEUED", "RETRYING")
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (1, 2, 4)
SYSTEM_ACTOR = "system.audit_email_relay"


@dataclass(frozen=True)
class AuditEmailRelayResult:
    scanned: int = 0
    sent: int = 0
    retrying: int = 0
    failed_permanent: int = 0
    bounced: int = 0
    skipped_not_due: int = 0

    def plus(self, **changes: int) -> "AuditEmailRelayResult":
        data = {
            "scanned": self.scanned,
            "sent": self.sent,
            "retrying": self.retrying,
            "failed_permanent": self.failed_permanent,
            "bounced": self.bounced,
            "skipped_not_due": self.skipped_not_due,
        }
        for key, value in changes.items():
            data[key] += value
        return AuditEmailRelayResult(**data)


class AuditEmailRelay:
    def __init__(
        self,
        *,
        email_message_class=EmailMultiAlternatives,
        connection_factory: Callable[..., object] = get_connection,
        now_fn: Callable[[], object] = timezone.now,
        from_email: str | None = None,
    ) -> None:
        self.email_message_class = email_message_class
        self.connection_factory = connection_factory
        self.now_fn = now_fn
        self.from_email = from_email

    def process_due(self, *, limit: int = 100, now=None) -> AuditEmailRelayResult:
        current = now or self.now_fn()
        result = AuditEmailRelayResult()
        candidates = (
            NotificationDeliveryLog.objects.filter(channel=EMAIL_CHANNEL, status__in=QUEUED_STATUSES)
            .order_by("created_date", "id")[:limit]
        )
        for delivery_log in candidates:
            result = result.plus(scanned=1)
            if not is_delivery_due(delivery_log, now=current):
                result = result.plus(skipped_not_due=1)
                continue
            delivery_result = self.deliver(delivery_log, now=current)
            if delivery_result.sent:
                result = result.plus(sent=1)
            elif delivery_result.failed_permanent:
                result = result.plus(failed_permanent=1)
            else:
                result = result.plus(retrying=1)
        return result

    def deliver(self, delivery_log: NotificationDeliveryLog, *, now=None) -> AuditEmailRelayResult:
        current = now or self.now_fn()
        notification = _get_notification(delivery_log)
        if notification is None:
            _mark_failed(delivery_log, "PSC_NOTIFICATION_NOT_FOUND", now=current, permanent=True)
            return AuditEmailRelayResult(scanned=1, failed_permanent=1)

        if not delivery_log.recipient_address:
            _mark_failed(delivery_log, "EMAIL_RECIPIENT_MISSING", now=current, permanent=True)
            return AuditEmailRelayResult(scanned=1, failed_permanent=1)

        try:
            email_message = self.email_message_class(
                subject=notification.title,
                body=notification.message,
                from_email=self.from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=[delivery_log.recipient_address],
                connection=self.connection_factory(timeout=getattr(settings, "EMAIL_TIMEOUT", 15)),
            )
            sent_count = email_message.send(fail_silently=False)
            if not sent_count:
                raise RuntimeError("SMTP returned zero sent messages")
        except Exception as exc:
            permanent = delivery_log.attempt_count + 1 >= MAX_RETRY_ATTEMPTS
            _mark_failed(delivery_log, str(exc), now=current, permanent=permanent)
            if permanent:
                return AuditEmailRelayResult(scanned=1, failed_permanent=1)
            return AuditEmailRelayResult(scanned=1, retrying=1)

        _mark_sent(delivery_log, now=current)
        return AuditEmailRelayResult(scanned=1, sent=1)

    def mark_bounced(
        self,
        *,
        delivery_log_id: uuid.UUID | str | None = None,
        psc_notification_id: str | None = None,
        recipient_address: str | None = None,
        reason: str = "BOUNCED",
        now=None,
    ) -> AuditEmailRelayResult:
        current = now or self.now_fn()
        queryset = NotificationDeliveryLog.objects.filter(channel=EMAIL_CHANNEL)
        if delivery_log_id:
            queryset = queryset.filter(id=delivery_log_id)
        if psc_notification_id:
            queryset = queryset.filter(psc_notification_id=_legacy_notification_id(psc_notification_id))
        if recipient_address:
            queryset = queryset.filter(recipient_address__iexact=recipient_address)
        delivery_log = queryset.order_by("-created_date").first()
        if delivery_log is None:
            return AuditEmailRelayResult(scanned=0)

        with transaction.atomic():
            delivery_log.status = "BOUNCED"
            delivery_log.last_error = str(reason or "BOUNCED")
            delivery_log.last_attempted_at = current
            if delivery_log.first_attempted_at is None:
                delivery_log.first_attempted_at = current
            delivery_log.save(
                update_fields=[
                    "status",
                    "last_error",
                    "first_attempted_at",
                    "last_attempted_at",
                ]
            )
        return AuditEmailRelayResult(scanned=1, bounced=1)


def process_due_audit_email_notifications(*, limit: int = 100, now=None) -> AuditEmailRelayResult:
    return AuditEmailRelay().process_due(limit=limit, now=now)


def is_delivery_due(delivery_log: NotificationDeliveryLog, *, now=None) -> bool:
    if delivery_log.status == "QUEUED" and delivery_log.attempt_count <= 0:
        return True
    if delivery_log.status not in QUEUED_STATUSES:
        return False
    if delivery_log.last_attempted_at is None:
        return True
    current = now or timezone.now()
    delay = RETRY_BACKOFF_SECONDS[min(max(delivery_log.attempt_count, 1) - 1, len(RETRY_BACKOFF_SECONDS) - 1)]
    return delivery_log.last_attempted_at + timedelta(seconds=delay) <= current


def _get_notification(delivery_log: NotificationDeliveryLog) -> Notification | None:
    try:
        notification_id = uuid.UUID(hex=str(delivery_log.psc_notification_id).replace("-", ""))
    except (TypeError, ValueError):
        return None
    return Notification.objects.filter(id=notification_id).first()


def _mark_sent(delivery_log: NotificationDeliveryLog, *, now) -> None:
    with transaction.atomic():
        delivery_log.status = "SENT"
        delivery_log.attempt_count += 1
        delivery_log.last_error = None
        delivery_log.last_attempted_at = now
        delivery_log.sent_at = now
        if delivery_log.first_attempted_at is None:
            delivery_log.first_attempted_at = now
        delivery_log.save(
            update_fields=[
                "status",
                "attempt_count",
                "last_error",
                "first_attempted_at",
                "last_attempted_at",
                "sent_at",
            ]
        )


def _mark_failed(delivery_log: NotificationDeliveryLog, error: str, *, now, permanent: bool) -> None:
    with transaction.atomic():
        delivery_log.status = "FAILED_PERMANENT" if permanent else "RETRYING"
        delivery_log.attempt_count += 1
        delivery_log.last_error = str(error or "EMAIL_DELIVERY_FAILED")
        delivery_log.last_attempted_at = now
        if delivery_log.first_attempted_at is None:
            delivery_log.first_attempted_at = now
        delivery_log.save(
            update_fields=[
                "status",
                "attempt_count",
                "last_error",
                "first_attempted_at",
                "last_attempted_at",
            ]
        )


def _legacy_notification_id(value: uuid.UUID | str) -> str:
    try:
        return uuid.UUID(str(value)).hex
    except ValueError:
        return str(value).replace("-", "").lower()


__all__ = [
    "AuditEmailRelay",
    "AuditEmailRelayResult",
    "MAX_RETRY_ATTEMPTS",
    "process_due_audit_email_notifications",
]
