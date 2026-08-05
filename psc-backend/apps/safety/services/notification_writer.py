from __future__ import annotations

import json
import logging
import os
import uuid
import urllib.request
from dataclasses import dataclass

from django.db import connection
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.signals import (
    _get_office_user_ids_for_roles,
    _get_vessel_master_crew_ids,
    create_notification,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationDispatchResult:
    notification_rows: list[dict[str, object]]
    slack_attempted: bool
    slack_delivered: bool
    slack_error: str | None = None


class SlackWebhookNotifier:
    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.getenv("SLACK_SAFETY_CHANNEL_WEBHOOK") or os.getenv("SLACK_WEBHOOK_URL")

    def send(self, *, title: str, message: str, payload: dict[str, object]) -> bool:
        if not self.webhook_url:
            return False
        body = json.dumps(
            {
                "text": f"{title}\n{message}",
                "metadata": {"event_type": "safety_notification", "event_payload": payload or {}},
            },
            default=str,
        ).encode("utf-8")
        request = urllib.request.Request(
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            response.read()
        return True


class NotificationWriter:
    table_name = Notification._meta.db_table
    module_code = "SAFETY"
    master_recipient = "MASTER"
    vessel_recipient_prefix = "VESSEL:"
    role_recipient_map = {
        "DPA": ["DPA"],
        "FM": ["FM", "FLEET MANAGER"],
        "PIC": ["OFFICE_PIC", "OFFICE_SSQE", "OFFICE_SUPT"],
        "SAFETY_CHANNEL": ["DPA", "OFFICE_PIC", "OFFICE_SSQE", "OFFICE_SUPT"],
    }

    def __init__(self, *, slack_notifier: object | None = None) -> None:
        self.slack_notifier = slack_notifier or SlackWebhookNotifier()

    def table_exists(self) -> bool:
        return self.table_name in connection.introspection.table_names()

    def table_has_required_columns(self) -> bool:
        return self.table_exists()

    def dispatch_notification(
        self,
        *,
        record_id: object,
        recipients: list[str],
        kind: str,
        title: str,
        message: str,
        payload: dict[str, object] | None = None,
        delivery_channel: str = "IN_APP",
        send_slack: bool = False,
    ) -> NotificationDispatchResult:
        rows = self.write_notification(
            record_id=record_id,
            recipients=recipients,
            kind=kind,
            title=title,
            message=message,
            payload=payload,
            delivery_channel=delivery_channel,
        )
        if not send_slack or not rows:
            return NotificationDispatchResult(
                notification_rows=rows,
                slack_attempted=False,
                slack_delivered=False,
            )

        try:
            delivered = self.slack_notifier.send(
                title=title,
                message=message,
                payload=payload or {},
            )
        except Exception as exc:
            return NotificationDispatchResult(
                notification_rows=rows,
                slack_attempted=True,
                slack_delivered=False,
                slack_error=str(exc),
            )

        return NotificationDispatchResult(
            notification_rows=rows,
            slack_attempted=True,
            slack_delivered=bool(delivered),
        )

    def write_notification(
        self,
        *,
        record_id: object,
        recipients: list[str],
        kind: str,
        title: str,
        message: str,
        payload: dict[str, object] | None = None,
        delivery_channel: str = "IN_APP",
    ) -> list[dict[str, object]]:
        if not self.table_has_required_columns():
            return []

        unique_recipients = [recipient for recipient in dict.fromkeys(recipients) if recipient]
        now = timezone.now()
        record_id_value = str(record_id)
        rows: list[dict[str, object]] = []
        payload_data = payload or {}
        vessel_id = self._normalize_uuid(payload_data.get("vessel_id")) or self._resolve_record_vessel_id(record_id)
        entity_type = self._resolve_entity_type(kind)
        entity_id = self._normalize_uuid(record_id)
        seen_targets: set[tuple[str, str]] = set()

        for recipient in unique_recipients:
            rows.extend(
                self._create_visible_notifications(
                    recipient=str(recipient),
                    record_id_value=record_id_value,
                    kind=kind,
                    title=title,
                    message=message,
                    vessel_id=vessel_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    delivery_channel=delivery_channel,
                    now=now,
                    seen_targets=seen_targets,
                )
            )

        return rows

    def _create_visible_notifications(
        self,
        *,
        recipient: str,
        record_id_value: str,
        kind: str,
        title: str,
        message: str,
        vessel_id: str | None,
        entity_type: str,
        entity_id: str | None,
        delivery_channel: str,
        now,
        seen_targets: set[tuple[str, str]],
    ) -> list[dict[str, object]]:
        normalized_recipient = recipient.strip()
        if not normalized_recipient:
            return []

        created_rows: list[dict[str, object]] = []
        target_rows = self._resolve_notification_targets(normalized_recipient, vessel_id=vessel_id)
        for target in target_rows:
            target_key = (str(target["recipient_type"]), str(target["recipient_id"]))
            if target_key in seen_targets:
                continue
            seen_targets.add(target_key)
            notification = create_notification(
                recipient_type=target["recipient_type"],
                recipient_id=target["recipient_id"],
                notification_type=kind,
                title=str(title or "Safety notification")[:200],
                message=str(message or title or "Safety notification")[:500],
                vessel_id=target.get("vessel_id") or vessel_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            if notification is None:
                continue
            created_rows.append(
                {
                    "module_code": self.module_code,
                    "record_id": record_id_value,
                    "recipient_ref": normalized_recipient,
                    "recipient_type": notification.recipient_type,
                    "recipient_id": notification.recipient_id,
                    "notification_id": str(notification.id),
                    "notification_kind": kind,
                    "title": notification.title,
                    "message": notification.message,
                    "delivery_channel": delivery_channel,
                    "created_at": now,
                }
            )
        return created_rows

    def _resolve_notification_targets(self, recipient: str, *, vessel_id: str | None) -> list[dict[str, str | None]]:
        recipient_key = recipient.strip().upper()
        recipient_vessel_id = self._normalize_uuid(recipient)
        if recipient_vessel_id:
            master_ids = _get_vessel_master_crew_ids(recipient_vessel_id)
            if master_ids:
                return [
                    {"recipient_type": "CREW", "recipient_id": crew_id, "vessel_id": recipient_vessel_id}
                    for crew_id in master_ids
                ]
            return [{
                "recipient_type": "CREW",
                "recipient_id": f"{self.vessel_recipient_prefix}{recipient_vessel_id}",
                "vessel_id": recipient_vessel_id,
            }]

        if recipient_key == self.master_recipient and vessel_id:
            master_ids = _get_vessel_master_crew_ids(vessel_id)
            if master_ids:
                return [
                    {"recipient_type": "CREW", "recipient_id": crew_id, "vessel_id": vessel_id}
                    for crew_id in master_ids
                ]
            return [{
                "recipient_type": "CREW",
                "recipient_id": f"{self.vessel_recipient_prefix}{vessel_id}",
                "vessel_id": vessel_id,
            }]

        office_roles = self.role_recipient_map.get(recipient_key)
        if office_roles:
            return [
                {"recipient_type": "OFFICE", "recipient_id": employee_id, "vessel_id": vessel_id}
                for employee_id in _get_office_user_ids_for_roles(office_roles)
            ]

        if recipient_key.startswith("KSM"):
            return [{"recipient_type": "CREW", "recipient_id": recipient, "vessel_id": vessel_id}]
        return [{"recipient_type": "OFFICE", "recipient_id": recipient, "vessel_id": vessel_id}]

    def _resolve_entity_type(self, kind: str) -> str:
        normalized_kind = str(kind or "").upper()
        if "NEAR_MISS" in normalized_kind:
            return "SAFETY_NEAR_MISS"
        if "INCIDENT" in normalized_kind:
            return "SAFETY_INCIDENT"
        return "SAFETY"

    def _resolve_record_vessel_id(self, record_id: object) -> str | None:
        normalized_id = self._normalize_uuid(record_id)
        if not normalized_id:
            return None
        try:
            from apps.safety.models import Incident

            incident = Incident.objects.filter(pk=normalized_id).only("vessel_id").first()
            if incident is not None:
                return self._normalize_uuid(incident.vessel_id) or str(incident.vessel_id)
        except Exception:
            return None
        return None

    def _normalize_uuid(self, value: object) -> str | None:
        if value in (None, ""):
            return None
        try:
            return str(uuid.UUID(str(value).strip()))
        except (TypeError, ValueError, AttributeError):
            return None
