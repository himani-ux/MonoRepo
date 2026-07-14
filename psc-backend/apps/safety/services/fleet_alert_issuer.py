from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import connection
from django.utils import timezone
from dotenv import load_dotenv

from apps.safety.authentication.roles import normalized_authority_role
from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.serializers.vessel_display import resolve_vessel_display
from apps.safety.services.incident_circular_publisher import WorkspaceCircularModuleClient
from apps.safety.services.field_history_recorder import (
    capture_model_state,
    parse_history_value,
    record_field_changes,
    resolve_actor_id,
    resolve_actor_role,
)
from apps.safety.services.notification_writer import NotificationWriter


def _normalize_role(user) -> str:
    return normalized_authority_role(user)


def _normalize_vessel_id(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip() or None


def _normalize_vessel_ids(values: object) -> list[str]:
    if not values:
        return []

    vessel_ids: list[str] = []
    seen: set[str] = set()
    if isinstance(values, (list, tuple, set)):
        iterable = values
    else:
        iterable = [values]

    for item in iterable:
        vessel_id = None
        is_current = True
        if isinstance(item, dict):
            vessel_id = item.get("vessel_id")
            is_current = item.get("is_current", True)
        else:
            vessel_id = getattr(item, "vessel_id", item)
            is_current = getattr(item, "is_current", True)
        if not is_current:
            continue
        normalized = _normalize_vessel_id(vessel_id)
        dedupe_key = normalized.lower() if normalized else ""
        if normalized and dedupe_key not in seen:
            seen.add(dedupe_key)
            vessel_ids.append(normalized)
    return vessel_ids


def _dedupe_vessel_ids(values: object) -> list[str]:
    return _normalize_vessel_ids(values)


@dataclass(frozen=True)
class FleetAlertStatus:
    due_by: object
    draft_text: str
    issued: bool
    issued_at: object | None
    recipients: list[str]
    sla_status: str
    sla_overdue: bool
    title: str


class FleetAlertIssueError(ValueError):
    """Raised when a fleet alert cannot be issued for the requested near miss."""


class FleetAlertIssuer:
    alert_kind = "NEAR_MISS_FLEET_ALERT"
    issued_field_name = "fleet_alert_issued_at"
    text_field_name = "fleet_alert_text"
    recipients_field_name = "fleet_alert_recipients"
    signature_field_name = "fleet_alert_signature"
    fleet_learning_field_name = "near_miss_fleet_learning"
    circular_publish_field_name = "near_miss_circular_publish"
    notification_writer_class = NotificationWriter
    circular_client_class = WorkspaceCircularModuleClient
    cc_recipients = ["HSSEQ@kaizenship.net"]

    def __init__(self) -> None:
        self.notification_writer = self.notification_writer_class()
        self.circular_client = self.circular_client_class()

    def build_status(self, near_miss: Incident, *, user=None) -> FleetAlertStatus:
        self._validate_near_miss(near_miss)
        recipients = self.resolve_recipient_vessel_ids(user=user, near_miss=near_miss)
        issued_at = self.get_issued_at(near_miss)
        due_by = self.resolve_deadline_anchor(near_miss) + timedelta(days=7)
        return FleetAlertStatus(
            due_by=due_by,
            draft_text=self.build_draft_text(near_miss),
            issued=issued_at is not None,
            issued_at=issued_at,
            recipients=recipients,
            sla_status=self.resolve_sla_status(near_miss, issued_at=issued_at, due_by=due_by),
            sla_overdue=issued_at is None and timezone.now() > due_by,
            title=self.build_title(near_miss),
        )

    def build_workspace_payload(self, near_miss: Incident, *, user=None) -> dict[str, object]:
        status = self.build_status(near_miss, user=user)
        return {
            "draft": {
                "title": status.title,
                "body": status.draft_text,
                "due_by": status.due_by,
                "anonymised": True,
                "fleet_learning_text": self.get_fleet_learning_text(near_miss),
            },
            "issued": status.issued,
            "issued_at": status.issued_at,
            "sla": {
                "due_by": status.due_by,
                "status": status.sla_status,
                "overdue": status.sla_overdue,
                "extension": self.get_sla_extension_payload(near_miss),
            },
            "circular_publish": self.get_circular_publish_payload(near_miss),
            "near_miss": {
                "id": near_miss.pk,
                "incident_number": near_miss.incident_number,
                "near_miss_priority": near_miss.near_miss_priority,
                "state": near_miss.state,
            },
            "recipients": status.recipients,
            "recipient_vessels": self.build_recipient_vessel_payload(status.recipients, user=user),
        }

    def issue_fleet_alert(
        self,
        near_miss: Incident,
        *,
        alert_text: str,
        device_fingerprint: str,
        fleet_learning_text: str,
        recipient_vessel_ids: list[str] | None = None,
        sla_extension_reason: str = "",
        typed_name: str,
        user,
    ) -> dict[str, object]:
        self._validate_near_miss(near_miss)
        if self.is_issued(near_miss):
            raise FleetAlertIssueError("A fleet alert has already been issued for this near miss.")

        cleaned_text = (alert_text or "").strip()
        if not cleaned_text:
            raise FleetAlertIssueError("Fleet alert text is required.")
        cleaned_learning = (fleet_learning_text or "").strip()
        if not cleaned_learning:
            raise FleetAlertIssueError("Fleet learning / lessons text is required for HIGH-priority near-miss fleet alerts.")

        cleaned_name = (typed_name or "").strip()
        cleaned_fingerprint = (device_fingerprint or "").strip()
        if len(cleaned_name) < 3:
            raise FleetAlertIssueError("DPA publish signature requires the typed full name.")
        if not cleaned_fingerprint:
            raise FleetAlertIssueError("DPA publish signature requires a device fingerprint.")

        recipients = self.resolve_issue_recipient_vessel_ids(
            requested_recipient_ids=recipient_vessel_ids,
            user=user,
            near_miss=near_miss,
        )
        if not recipients:
            raise FleetAlertIssueError("No recipient vessels could be resolved for this fleet alert.")

        actor_id = resolve_actor_id(user)
        actor_role = resolve_actor_role(user)
        issued_at = timezone.now()
        title = self.build_title(near_miss)
        due_by = self.resolve_deadline_anchor(near_miss) + timedelta(days=7)
        cleaned_extension_reason = (sla_extension_reason or "").strip()
        issued_late = issued_at > due_by
        if issued_late and not cleaned_extension_reason:
            raise FleetAlertIssueError(
                "HIGH-priority near-miss requires fleet alert within 1 week (D-GAP-R22). "
                "Record a DPA/FM extension reason before issuing late."
            )
        recipient_emails = self._require_email_delivery_ready(recipients)

        circular_result = self.circular_client.publish_draft(
            payload=self.build_circular_payload(
                near_miss=near_miss,
                alert_text=cleaned_text,
                fleet_learning_text=cleaned_learning,
                recipients=recipients,
                due_by=due_by,
                title=title,
            )
        )

        notification_rows = self.notification_writer.write_notification(
            record_id=near_miss.pk,
            recipients=recipients,
            kind=self.alert_kind,
            title=title,
            message=cleaned_text,
            payload={
                "anonymised": True,
                "due_by": due_by.isoformat(),
                "incident_number": near_miss.incident_number,
                "near_miss_id": near_miss.pk,
                "near_miss_priority": near_miss.near_miss_priority,
                "circular_id": circular_result.circular_id,
                "circular_publish_status": circular_result.status,
                "sla_extension_reason": cleaned_extension_reason,
            },
        )
        email_result = self._send_email_alert(
            near_miss=near_miss,
            recipients=recipients,
            recipient_emails=recipient_emails,
            subject=title,
            alert_text=cleaned_text,
            fleet_learning_text=cleaned_learning,
        )

        old_state = capture_model_state(near_miss, field_names=("updated_by", "updated_date"))
        near_miss.updated_by = actor_id
        near_miss.updated_date = issued_at
        near_miss.save(update_fields=["updated_by", "updated_date"])
        record_field_changes(
            near_miss,
            old_state,
            user=user,
            field_names=("updated_by", "updated_date"),
            change_reason="Fleet alert issued",
        )

        self._write_history_row(
            near_miss=near_miss,
            actor_id=actor_id,
            actor_role=actor_role,
            field_name=self.issued_field_name,
            new_value=issued_at.isoformat(),
        )
        self._write_history_row(
            near_miss=near_miss,
            actor_id=actor_id,
            actor_role=actor_role,
            field_name=self.text_field_name,
            new_value=cleaned_text,
        )
        self._write_history_row(
            near_miss=near_miss,
            actor_id=actor_id,
            actor_role=actor_role,
            field_name=self.fleet_learning_field_name,
            new_value=cleaned_learning,
            change_reason="Near-miss fleet learning recorded.",
        )
        self._write_history_row(
            near_miss=near_miss,
            actor_id=actor_id,
            actor_role=actor_role,
            field_name=self.recipients_field_name,
            new_value=recipients,
        )
        if issued_late:
            self._write_history_row(
                near_miss=near_miss,
                actor_id=actor_id,
                actor_role=actor_role,
                field_name="fleet_alert_sla_extension",
                new_value={
                    "due_by": due_by.isoformat(),
                    "issued_at": issued_at.isoformat(),
                    "reason": cleaned_extension_reason,
                },
                change_reason="Near-miss fleet alert SLA extension recorded.",
            )
        self._write_history_row(
            near_miss=near_miss,
            actor_id=actor_id,
            actor_role=actor_role,
            field_name=self.signature_field_name,
            new_value={
                "device_fingerprint": cleaned_fingerprint,
                "signed_at": issued_at.isoformat(),
                "signed_by": actor_id,
                "signed_role": actor_role,
                "typed_name": cleaned_name,
            },
        )
        self._write_history_row(
            near_miss=near_miss,
            actor_id=actor_id,
            actor_role=actor_role,
            field_name=self.circular_publish_field_name,
            new_value={
                "status": circular_result.status,
                "circular_id": circular_result.circular_id,
                "detail_url": circular_result.detail_url,
                "payload": circular_result.payload,
            },
            change_reason="Near-miss fleet alert published to Circular module seam.",
        )

        return {
            "circular_publish": {
                "status": circular_result.status,
                "circular_id": circular_result.circular_id,
                "detail_url": circular_result.detail_url,
            },
            "issued": True,
            "issued_at": issued_at,
            "notifications_emitted": len(notification_rows),
            "recipients": recipients,
            "recipient_vessels": self.build_recipient_vessel_payload(recipients, user=user),
            **email_result,
            "sla": {
                "due_by": due_by,
                "status": "ISSUED_LATE_WITH_EXTENSION" if issued_late else "ISSUED_ON_TIME",
                "overdue": issued_late,
                "extension_reason": cleaned_extension_reason,
            },
            "title": title,
        }

    def _require_email_delivery_ready(self, recipients: list[str]) -> dict[str, str]:
        self._refresh_email_settings_from_env()
        recipient_emails = self._resolve_recipient_emails(recipients)
        missing_email_vessels = [
            vessel_id
            for vessel_id in recipients
            if not str(recipient_emails.get(str(vessel_id).strip(), "")).strip()
        ]
        if missing_email_vessels:
            raise FleetAlertIssueError(
                "Email is not recorded in VesselData for: "
                f"{', '.join(missing_email_vessels)}."
            )

        if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(settings, "EMAIL_HOST_PASSWORD", None):
            raise FleetAlertIssueError(
                "Fleet Alert email sender credentials are not configured. "
                "Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD on the backend and restart the service."
            )
        return recipient_emails

    def _refresh_email_settings_from_env(self) -> None:
        if getattr(settings, "EMAIL_HOST_USER", None) and getattr(settings, "EMAIL_HOST_PASSWORD", None):
            return
        env_path = getattr(settings, "BASE_DIR", None)
        if env_path:
            load_dotenv(env_path / ".env", override=False)
        if not getattr(settings, "EMAIL_HOST_USER", None):
            settings.EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
        if not getattr(settings, "EMAIL_HOST_PASSWORD", None):
            settings.EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
        if not getattr(settings, "DEFAULT_FROM_EMAIL", None) and settings.EMAIL_HOST_USER:
            settings.DEFAULT_FROM_EMAIL = os.getenv(
                "DEFAULT_FROM_EMAIL",
                f"KSM Marine <{settings.EMAIL_HOST_USER}>",
            )

    def _resolve_recipient_emails(self, recipients: list[str]) -> dict[str, str]:
        normalized_recipients = [str(vessel_id).strip() for vessel_id in recipients if str(vessel_id or "").strip()]
        if not normalized_recipients:
            return {}
        if "VesselData" not in connection.introspection.table_names():
            return {}

        placeholders = ", ".join(["%s"] * len(normalized_recipients))
        id_expression = self._quote("id")
        if connection.vendor != "sqlite":
            id_expression = f"CONVERT(varchar(64), {id_expression})"
        sql = (
            f"SELECT {id_expression}, {self._quote('Email')} "
            f"FROM {self._quote('VesselData')} "
            f"WHERE {id_expression} IN ({placeholders}) "
            f"AND COALESCE({self._quote('is_active')}, 1) <> 0 "
            f"AND COALESCE({self._quote('is_deleted')}, 0) = 0"
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, normalized_recipients)
                rows = cursor.fetchall()
        except Exception:
            return {}
        return {str(vessel_id).strip(): str(email or "").strip() for vessel_id, email in rows}

    def _quote(self, name: str) -> str:
        return connection.ops.quote_name(name)

    def _send_email_alert(
        self,
        *,
        near_miss: Incident,
        recipients: list[str],
        recipient_emails: dict[str, str],
        subject: str,
        alert_text: str,
        fleet_learning_text: str,
    ) -> dict[str, object]:
        emails: list[str] = []
        seen: set[str] = set()
        for vessel_id in recipients:
            email = str(recipient_emails.get(str(vessel_id).strip(), "")).strip()
            email_key = email.lower()
            if not email or email_key in seen:
                continue
            emails.append(email)
            seen.add(email_key)
        if not emails:
            return {"emails_sent": 0, "email_failed": 0, "vessels_without_email": len(recipients)}

        try:
            pdf_attachment = self._build_pdf_attachment(near_miss)
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=self._email_body(
                    near_miss=near_miss,
                    alert_text=alert_text,
                    fleet_learning_text=fleet_learning_text,
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                cc=self.cc_recipients,
                bcc=emails,
                to=[],
                connection=get_connection(timeout=getattr(settings, "EMAIL_TIMEOUT", 15)),
            )
            email_message.attach(
                pdf_attachment.file_name,
                pdf_attachment.content,
                pdf_attachment.content_type,
            )
            send_count = email_message.send()
        except Exception as exc:
            raise FleetAlertIssueError(
                "Fleet Alert email could not be sent. Check the backend SMTP credentials and mail server settings."
            ) from exc

        return {
            "emails_sent": len(emails) if send_count else 0,
            "email_failed": 0 if send_count else len(emails),
            "vessels_without_email": 0,
        }

    def _email_body(self, *, near_miss: Incident, alert_text: str, fleet_learning_text: str) -> str:
        return "\n".join(
            [
                "Hello,",
                "",
                f"A near miss has occurred: {near_miss.incident_number}.",
                "",
                "Please review what happened in the attached PDF and take the necessary preventive action.",
                "",
                "Kaizen Ship Management",
            ]
        )

    def _build_pdf_attachment(self, near_miss: Incident):
        from apps.safety.services.pdf_renderer import NearMissLightweightPdfRenderer

        return NearMissLightweightPdfRenderer().render_near_miss_pdf(
            incident_id=near_miss.pk,
            viewer_user=None,
            persist=False,
        )

    def build_circular_payload(
        self,
        *,
        near_miss: Incident,
        alert_text: str,
        fleet_learning_text: str,
        recipients: list[str],
        due_by,
        title: str,
    ) -> dict[str, object]:
        return {
            "source_module": "SAFETY",
            "source_record_type": "NEAR_MISS",
            "source_record_id": near_miss.pk,
            "source_reference": near_miss.incident_number,
            "title": title,
            "summary": fleet_learning_text[:512],
            "body": alert_text,
            "fleet_learning": fleet_learning_text,
            "priority": near_miss.near_miss_priority,
            "anonymised": True,
            "due_by": due_by.isoformat() if due_by is not None else None,
            "recipient_vessel_ids": recipients,
            "vessel_id": str(near_miss.vessel_id),
        }

    def resolve_deadline_anchor(self, near_miss: Incident):
        history_row = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name="near_miss_priority",
                new_value="HIGH",
            )
            .order_by("changed_at", "id")
            .first()
        )
        if history_row is not None:
            return history_row.changed_at
        return near_miss.created_date or timezone.now()

    def get_issued_at(self, near_miss: Incident):
        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name=self.issued_field_name,
            )
            .order_by("changed_at", "id")
            .first()
        )
        if row is None:
            return None
        return row.changed_at

    def is_issued(self, near_miss: Incident) -> bool:
        return self.get_issued_at(near_miss) is not None

    def resolve_sla_status(self, near_miss: Incident, *, issued_at=None, due_by=None) -> str:
        deadline = due_by or (self.resolve_deadline_anchor(near_miss) + timedelta(days=7))
        if issued_at is not None:
            if issued_at <= deadline:
                return "ISSUED_ON_TIME"
            return "ISSUED_LATE_WITH_EXTENSION" if self.get_sla_extension_payload(near_miss) else "ISSUED_LATE"
        return "OVERDUE" if timezone.now() > deadline else "PENDING"

    def get_fleet_learning_text(self, near_miss: Incident) -> str:
        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name=self.fleet_learning_field_name,
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if row is None:
            return ""
        value = parse_history_value(row.new_value)
        return str(value or "").strip()

    def get_circular_publish_payload(self, near_miss: Incident) -> dict[str, object] | None:
        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name=self.circular_publish_field_name,
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if row is None:
            return None
        value = parse_history_value(row.new_value)
        if isinstance(value, dict):
            return {
                "status": value.get("status"),
                "circular_id": value.get("circular_id"),
                "detail_url": value.get("detail_url"),
            }
        return None

    def get_sla_extension_payload(self, near_miss: Incident) -> dict[str, object] | None:
        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name="fleet_alert_sla_extension",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if row is None:
            return None
        value = parse_history_value(row.new_value)
        return value if isinstance(value, dict) else None

    def build_title(self, near_miss: Incident) -> str:
        return f"Fleet alert: HIGH-priority near miss {near_miss.incident_number}"

    def build_draft_text(self, near_miss: Incident) -> str:
        due_by = self.resolve_deadline_anchor(near_miss) + timedelta(days=7)
        occurred_at = near_miss.occurred_at or near_miss.created_date or timezone.now()
        return (
            "A HIGH-priority near miss has been reported on a sister vessel. "
            "Vessel and crew identifiers remain withheld for fleet circulation. "
            f"Reference: {near_miss.incident_number}. "
            f"Occurred: {occurred_at:%d-%b-%Y}. "
            f"Fleet alert due by: {due_by:%d-%b-%Y}. "
            "Review equivalent controls, brief the relevant teams, and confirm immediate preventive actions before the next parallel task."
        )

    def resolve_recipient_vessel_ids(self, *, user=None, near_miss: Incident) -> list[str]:
        for attr_name in ("fleet_vessel_ids", "company_vessel_ids", "vessel_ids"):
            vessel_ids = _normalize_vessel_ids(getattr(user, attr_name, None) if user is not None else None)
            if vessel_ids:
                return _dedupe_vessel_ids(vessel_ids)

        for attr_name in ("role_by_vessel_rows", "crew_onboarding_rows"):
            vessel_ids = _normalize_vessel_ids(getattr(user, attr_name, None) if user is not None else None)
            if vessel_ids:
                return _dedupe_vessel_ids(vessel_ids)

        if getattr(user, "is_global", False) or _normalize_role(user) in {"DPA", "FM", "FLEET MANAGER"}:
            incident_vessels = [
                vessel_id
                for vessel_id in Incident.objects.filter(is_deleted=False)
                .values_list("vessel_id", flat=True)
                .distinct()
                if _normalize_vessel_id(vessel_id)
            ]
            if incident_vessels:
                return _dedupe_vessel_ids(incident_vessels)

        return _dedupe_vessel_ids([near_miss.vessel_id])

    def resolve_issue_recipient_vessel_ids(
        self,
        *,
        requested_recipient_ids: list[str] | None,
        user=None,
        near_miss: Incident,
    ) -> list[str]:
        allowed = self.resolve_recipient_vessel_ids(user=user, near_miss=near_miss)
        requested = _dedupe_vessel_ids(requested_recipient_ids or [])
        if not requested:
            return allowed
        allowed_keys = {value.lower() for value in allowed}
        invalid = [value for value in requested if value.lower() not in allowed_keys]
        if invalid:
            raise FleetAlertIssueError("Fleet alert recipients must be within the user's vessel scope.")
        return requested

    def build_recipient_vessel_payload(self, recipients: list[str], *, user=None) -> list[dict[str, str]]:
        payload: list[dict[str, str]] = []
        for vessel_id in _dedupe_vessel_ids(recipients):
            display = resolve_vessel_display(vessel_id, user=user)
            label = display["vessel_display_name"] or display["vessel_code"] or vessel_id
            payload.append(
                {
                    "vessel_id": vessel_id,
                    "vessel_code": display["vessel_code"],
                    "vessel_name": display["vessel_name"],
                    "display_name": label,
                }
            )
        return payload

    def notification_kind_exists(self, *, record_id: int, kind: str) -> bool:
        if not self.notification_writer.table_exists():
            return False
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT 1 FROM {self.notification_writer.table_name} WHERE entity_id = %s AND notification_type = %s",
                [record_id, kind],
            )
            return cursor.fetchone() is not None

    def _validate_near_miss(self, near_miss: Incident) -> None:
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise FleetAlertIssueError("Fleet alerts are only available for near-miss records.")
        if near_miss.near_miss_priority != "HIGH":
            raise FleetAlertIssueError("Fleet alerts are restricted to HIGH-priority near misses.")
        if near_miss.state == "SUPERSEDED" or near_miss.superseded_by_id:
            raise FleetAlertIssueError("Superseded near-miss records cannot issue fleet alerts.")

    def _write_history_row(
        self,
        *,
        near_miss: Incident,
        actor_id: str,
        actor_role: str,
        field_name: str,
        new_value: str,
        change_reason: str = "Fleet alert issued",
    ) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name=field_name,
            old_value=None,
            new_value=new_value,
            change_reason=change_reason,
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            schema_version=near_miss.schema_version or 1,
        )
