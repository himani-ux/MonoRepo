from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import DatabaseError, connection
from dotenv import load_dotenv
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
    cc_recipients = ["HSSEQ@kaizenship.net"]

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

        vessel_lookup = {vessel.vessel_id: vessel for vessel in self.list_vessels(vessel_ids=selected_ids)}
        missing_ids = [vessel_id for vessel_id in selected_ids if vessel_id not in vessel_lookup]
        if missing_ids:
            raise ValidationError(
                {"recipient_vessel_ids": f"Unknown or inactive ship selected: {', '.join(missing_ids)}"}
            )

        selected_vessels = [vessel_lookup[vessel_id] for vessel_id in selected_ids]
        self._require_email_delivery_ready(selected_vessels)
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

    def list_vessels(self, *, vessel_ids: list[str] | None = None) -> list[IncidentFleetAlertVessel]:
        selected_ids = self._normalize_selected_ids(vessel_ids or [])
        selected_columns = (
            self._quote("id"),
            self._quote("vesselName"),
            self._quote("vesselCode"),
            self._quote("Email"),
        )
        where_clauses = [
            f"COALESCE({self._quote('is_active')}, 1) <> 0",
            f"COALESCE({self._quote('is_deleted')}, 0) = 0",
        ]
        params: list[str] = []
        if selected_ids:
            where_clauses.append(
                f"{self._quote('id')} IN ({', '.join(['%s'] * len(selected_ids))})"
            )
            params.extend(selected_ids)

        sql = (
            f"SELECT {', '.join(selected_columns)} "
            f"FROM {self._quote(self.vessel_table_name)} "
            f"WHERE {' AND '.join(where_clauses)} "
            f"ORDER BY {self._quote('vesselCode')}, {self._quote('vesselName')}"
        )

        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            except DatabaseError:
                return []

        vessels: list[IncidentFleetAlertVessel] = []
        for vessel_id, vessel_name, vessel_code, email in rows:
            normalized_id = self._normalize_uuid(vessel_id)
            if not normalized_id:
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

    def _require_email_delivery_ready(self, selected_vessels: list[IncidentFleetAlertVessel]) -> None:
        self._refresh_email_settings_from_env()
        vessels_without_email = [
            vessel.display_name
            for vessel in selected_vessels
            if not vessel.email
        ]
        if vessels_without_email:
            raise ValidationError(
                {
                    "recipient_vessel_ids": (
                        "Email is not recorded in VesselData for: "
                        f"{', '.join(vessels_without_email)}."
                    )
                }
            )

        if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(settings, "EMAIL_HOST_PASSWORD", None):
            raise ValidationError(
                "Fleet Alert email sender credentials are not configured. "
                "Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD on the backend and restart the service."
            )

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

    def _send_email_alerts(
        self,
        *,
        incident: Incident,
        selected_vessels: list[IncidentFleetAlertVessel],
        subject: str,
        message: str,
    ) -> dict[str, Any]:
        vessels_without_email = 0
        body = self._email_body(incident=incident, message=message)
        email_connection = get_connection(timeout=getattr(settings, "EMAIL_TIMEOUT", 15))
        recipient_emails: list[str] = []
        seen_emails: set[str] = set()

        for vessel in selected_vessels:
            if not vessel.email:
                vessels_without_email += 1
                continue
            normalized_email = vessel.email.strip()
            email_key = normalized_email.lower()
            if not normalized_email or email_key in seen_emails:
                continue
            recipient_emails.append(normalized_email)
            seen_emails.add(email_key)

        if not recipient_emails:
            return {
                "emails_sent": 0,
                "email_failed": 0,
                "vessels_without_email": vessels_without_email,
            }

        try:
            pdf_attachment = self._build_pdf_attachment(incident)
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                cc=self.cc_recipients,
                bcc=recipient_emails,
                to=[],
                connection=email_connection,
            )
            email_message.attach(
                pdf_attachment.file_name,
                pdf_attachment.content,
                pdf_attachment.content_type,
            )
            send_count = email_message.send()
        except Exception:
            raise ValidationError(
                "Fleet Alert email could not be sent. Check the backend SMTP credentials and mail server settings."
            )
        emails_sent = len(recipient_emails) if send_count else 0
        email_failed = 0 if send_count else len(recipient_emails)

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
                f"An incident has occurred: {incident.incident_number}.",
                "",
                "Please review what happened in the attached PDF and take the necessary preventive action.",
                "",
                "Kaizen Ship Management",
            ]
        )

    def _build_pdf_attachment(self, incident: Incident):
        from apps.safety.services.pdf_renderer import IncidentPdfRenderer

        return IncidentPdfRenderer().render_incident_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
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
