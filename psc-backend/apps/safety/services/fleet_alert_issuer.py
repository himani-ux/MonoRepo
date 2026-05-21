from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta

from django.db import connection
from django.utils import timezone

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
            "sla": {
                "due_by": due_by,
                "status": "ISSUED_LATE_WITH_EXTENSION" if issued_late else "ISSUED_ON_TIME",
                "overdue": issued_late,
                "extension_reason": cleaned_extension_reason,
            },
            "title": title,
        }

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
                f"SELECT 1 FROM {self.notification_writer.table_name} WHERE record_id = %s AND notification_kind = %s",
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
