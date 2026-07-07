from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import connection
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.safety.models import Incident
from apps.safety.services.notification_writer import NotificationWriter


@dataclass(frozen=True)
class IncidentFleetAlertVessel:
    vessel_id: str
    display_name: str
    vessel_name: str
    vessel_code: str
    email: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "vessel_id": self.vessel_id,
            "display_name": self.display_name,
            "vessel_name": self.vessel_name,
            "vessel_code": self.vessel_code,
            "has_email": bool(self.email),
        }


class IncidentFleetAlertService:
    notification_kind = "INCIDENT_FLEET_ALERT"
    vessel_table_name = "VesselData"

    def __init__(self, *, notification_writer: NotificationWriter | None = None) -> None:
        self.notification_writer = notification_writer or NotificationWriter()

    def build_workspace_payload(self, incident: Incident) -> dict[str, Any]:
        vessels = self.list_vessels()
        return {
            "incident": self._incident_payload(incident),
            "recipient_vessels": [vessel.as_payload() for vessel in vessels],
        }

    def issue_fleet_alert(self, *, incident: Incident, recipient_vessel_ids: list[str]) -> dict[str, Any]:
        if incident.record_type != Incident.RecordType.INCIDENT:
            raise ValidationError("Incident Fleet Alert is only available for incident reports.")

        selected_ids = self._normalize_selected_ids(recipient_vessel_ids)
        if not selected_ids:
            raise ValidationError({"recipient_vessel_ids": "Select at least one ship."})

        vessel_lookup = {vessel.vessel_id: vessel for vessel in self.list_vessels()}
        missing_ids = [vessel_id for vessel_id in selected_ids if vessel_id not in vessel_lookup]
        if missing_ids:
            raise ValidationError(
                {"recipient_vessel_ids": f"Unknown or inactive ship selected: {', '.join(missing_ids)}"}
            )

        selected_vessels = [vessel_lookup[vessel_id] for vessel_id in selected_ids]
        title = f"Incident Fleet Alert - {incident.incident_number}"
        message = self._notification_message(incident)
        notification_rows = self.notification_writer.write_notification(
            record_id=incident.pk,
            recipients=selected_ids,
            kind=self.notification_kind,
            title=title,
            message=message,
            payload={
                "incident_id": str(incident.pk),
                "incident_number": incident.incident_number,
                "recipient_vessel_ids": selected_ids,
            },
        )
        email_result = self._send_email_alerts(
            incident=incident,
            selected_vessels=selected_vessels,
            subject=title,
            message=message,
        )

        return {
            "issued": True,
            "issued_at": timezone.now().isoformat(),
            "incident": self._incident_payload(incident),
            "recipient_vessel_ids": selected_ids,
            "recipient_vessels": [vessel.as_payload() for vessel in selected_vessels],
            "notifications_emitted": len(notification_rows),
            **email_result,
            "message": f"Fleet alert sent to {len(selected_vessels)} selected ship(s).",
        }

    def list_vessels(self) -> list[IncidentFleetAlertVessel]:
        if self.vessel_table_name not in connection.introspection.table_names():
            return []

        columns = self._vessel_columns()
        id_column = self._find_column(columns, "id")
        if not id_column:
            return []

        name_column = self._find_column(columns, "vesselName", "VesselName", "vessel_name")
        code_column = self._find_column(columns, "vesselCode", "VesselCode", "vessel_code")
        email_column = self._find_column(columns, "email", "vesselEmail", "vessel_email")
        active_column = self._find_column(columns, "is_active", "IsActive")
        deleted_column = self._find_column(columns, "is_deleted", "IsDeleted")

        selected_columns = [
            id_column,
            name_column,
            code_column,
            email_column,
            active_column,
            deleted_column,
        ]
        select_sql = ", ".join(
            self._quote(column_name) if column_name else "NULL" for column_name in selected_columns
        )
        sql = f"SELECT {select_sql} FROM {self._quote(self.vessel_table_name)}"

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        vessels: list[IncidentFleetAlertVessel] = []
        for vessel_id, vessel_name, vessel_code, email, is_active, is_deleted in rows:
            normalized_id = self._normalize_uuid(vessel_id)
            if not normalized_id or self._is_false(is_active) or self._is_true(is_deleted):
                continue

            name_value = str(vessel_name or "").strip()
            code_value = str(vessel_code or "").strip()
            email_value = str(email or "").strip()
            display_name = " - ".join(part for part in (code_value, name_value) if part) or normalized_id
            vessels.append(
                IncidentFleetAlertVessel(
                    vessel_id=normalized_id,
                    display_name=display_name,
                    vessel_name=name_value,
                    vessel_code=code_value,
                    email=email_value,
                )
            )

        return sorted(vessels, key=lambda vessel: vessel.display_name.lower())

    def _send_email_alerts(
        self,
        *,
        incident: Incident,
        selected_vessels: list[IncidentFleetAlertVessel],
        subject: str,
        message: str,
    ) -> dict[str, Any]:
        emails_sent = 0
        email_failed = 0
        vessels_without_email = 0
        body = self._email_body(incident=incident, message=message)

        for vessel in selected_vessels:
            if not vessel.email:
                vessels_without_email += 1
                continue

            try:
                EmailMultiAlternatives(
                    subject=subject,
                    body=body,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    to=[vessel.email],
                ).send()
            except Exception:
                email_failed += 1
                continue
            emails_sent += 1

        return {
            "emails_sent": emails_sent,
            "email_failed": email_failed,
            "vessels_without_email": vessels_without_email,
        }

    def _incident_payload(self, incident: Incident) -> dict[str, Any]:
        return {
            "incident_id": str(incident.pk),
            "incident_number": incident.incident_number,
            "risk_band": incident.risk_band,
            "vessel_id": str(incident.vessel_id or ""),
        }

    def _notification_message(self, incident: Incident) -> str:
        summary = str(incident.narrative or "").strip()
        if len(summary) > 220:
            summary = f"{summary[:217]}..."
        parts = [f"Incident {incident.incident_number} requires fleet attention."]
        if incident.risk_band:
            parts.append(f"Risk band: {incident.risk_band}.")
        if summary:
            parts.append(summary)
        return " ".join(parts)

    def _email_body(self, *, incident: Incident, message: str) -> str:
        return "\n".join(
            [
                "Hello,",
                "",
                "A fleet alert has been issued for an incident.",
                "",
                f"Incident number: {incident.incident_number}",
                f"Risk band: {incident.risk_band or 'Not recorded'}",
                "",
                message,
                "",
                "Please review the incident learning in VIMS.",
                "",
                "Kaizen Ship Management",
            ]
        )

    def _normalize_selected_ids(self, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values or []:
            vessel_id = self._normalize_uuid(value)
            if not vessel_id or vessel_id in seen:
                continue
            normalized.append(vessel_id)
            seen.add(vessel_id)
        return normalized

    def _vessel_columns(self) -> dict[str, str]:
        with connection.cursor() as cursor:
            table_description = connection.introspection.get_table_description(cursor, self.vessel_table_name)
        return {str(column.name).lower(): str(column.name) for column in table_description}

    def _find_column(self, columns: dict[str, str], *candidates: str) -> str | None:
        for candidate in candidates:
            column = columns.get(candidate.lower())
            if column:
                return column
        return None

    def _quote(self, name: str) -> str:
        return connection.ops.quote_name(name)

    def _normalize_uuid(self, value: object) -> str | None:
        if value in (None, ""):
            return None
        try:
            return str(uuid.UUID(str(value).strip()))
        except (TypeError, ValueError, AttributeError):
            return None

    def _is_true(self, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        return text in {"1", "true", "yes", "y"}

    def _is_false(self, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return not value
        text = str(value).strip().lower()
        return text in {"0", "false", "no", "n"}
