from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
import uuid

from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from apps.certs.services.magic_link import build_magic_link_ack_path
from apps.certs.services.slack_relay import (
    CertSlackRelay,
    DEFAULT_DPA_SLACK_CHANNEL,
    DEFAULT_MARINE_SLACK_CHANNEL,
    DEFAULT_OFFICE_SLACK_CHANNEL,
    DEFAULT_TECHNICAL_SLACK_CHANNEL,
)


VESSEL_CHANNELS = ["in_app", "email"]
OFFICE_CHANNELS = ["in_app", "slack"]
IDEMPOTENCY_WINDOW_HOURS = 24


@dataclass(frozen=True)
class CertNotificationRecipient:
    user_id: str
    role: str
    side: str

    def normalized_side(self) -> str:
        return self.side.strip().lower()

    def channels(self) -> list[str]:
        side = self.normalized_side()
        if side == "vessel":
            return list(VESSEL_CHANNELS)
        if side == "office":
            return list(OFFICE_CHANNELS)
        raise ValueError(f"Unsupported Certs notification side: {self.side}")

    def as_payload(self) -> dict[str, str]:
        return {
            "userId": self.user_id,
            "role": self.role,
            "side": self.normalized_side(),
        }


@dataclass(frozen=True)
class CertNotificationDispatchResult:
    notification_rows: list[dict[str, Any]]
    meta_rows: list[dict[str, Any]]
    channels_by_recipient: dict[str, list[str]]


def build_expiry_escalation_recipients(
    *,
    base_recipients: list[CertNotificationRecipient],
    fleet_manager_user_id: str | None,
    days_to_expiry: int,
    critical: bool,
    ack_missing: bool,
) -> list[CertNotificationRecipient]:
    recipients = list(dict.fromkeys(base_recipients))
    should_add_fm = bool(fleet_manager_user_id) and critical and ack_missing and days_to_expiry <= 7
    if not should_add_fm:
        return recipients

    fm = CertNotificationRecipient(
        user_id=str(fleet_manager_user_id),
        role="Fleet Manager",
        side="office",
    )
    if fm not in recipients:
        recipients.append(fm)
    return recipients


class CertNotificationDispatcher:
    module_code = "CERTS"
    master_table = "master_notification"
    meta_table = "vims_certs_notification_meta"
    vessel_config_table = "vims_certs_vessel_config"

    def __init__(self, *, slack_relay: object | None = None) -> None:
        self.slack_relay = slack_relay or CertSlackRelay()

    def _qualified(self, table_name: str) -> str:
        if connection.vendor == "microsoft":
            return f"dbo.{table_name}"
        return table_name

    def _table_exists(self, table_name: str) -> bool:
        return table_name in connection.introspection.table_names()

    def _insert_master_notification(
        self,
        *,
        record_id: str,
        recipient_ref: str,
        trigger_event: str,
        title: str,
        message: str,
        payload_json: str,
        sent_at,
    ) -> int:
        table_name = self._qualified(self.master_table)
        if connection.vendor == "microsoft":
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} (
                        module_code, record_id, recipient_ref, notification_kind,
                        title, message, delivery_channel, payload_json, created_at
                    )
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        self.module_code,
                        record_id,
                        recipient_ref,
                        trigger_event,
                        title,
                        message,
                        "IN_APP",
                        payload_json,
                        sent_at,
                    ],
                )
                return int(cursor.fetchone()[0])

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {table_name} (
                    module_code, record_id, recipient_ref, notification_kind,
                    title, message, delivery_channel, payload_json, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    self.module_code,
                    record_id,
                    recipient_ref,
                    trigger_event,
                    title,
                    message,
                    "IN_APP",
                    payload_json,
                    sent_at,
                ],
            )
            return int(cursor.lastrowid)

    def _idempotency_exists(self, idempotency_key: str, *, sent_at) -> bool:
        cutoff = sent_at - timedelta(hours=IDEMPOTENCY_WINDOW_HOURS)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {self._qualified(self.meta_table)}
                WHERE idempotency_key = %s
                  AND sent_at >= %s
                """,
                [idempotency_key, cutoff],
            )
            return int(cursor.fetchone()[0] or 0) > 0

    def _idempotency_key_exists_anywhere(self, idempotency_key: str) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM {self._qualified(self.meta_table)} WHERE idempotency_key = %s",
                [idempotency_key],
            )
            return int(cursor.fetchone()[0] or 0) > 0

    def _insert_meta(
        self,
        *,
        notification_id: str,
        master_notification_id: int,
        trigger_event: str,
        cert_row_id: str | None,
        vessel_id: str | None,
        recipients_json: str,
        channels_json: str,
        sent_at,
        delivery_status_json: str,
        escalation_level: int,
        body_content: str,
        idempotency_key: str,
    ) -> str:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {self._qualified(self.meta_table)} (
                    notification_id, master_notification_id, trigger_event, cert_row_id,
                    vessel_id, recipients_json, channels_json, sent_at,
                    delivery_status_json, escalation_level, body_content, idempotency_key
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    notification_id,
                    master_notification_id,
                    trigger_event,
                    cert_row_id,
                    vessel_id,
                    recipients_json,
                    channels_json,
                    sent_at,
                    delivery_status_json,
                    escalation_level,
                    body_content,
                    idempotency_key,
                ],
            )
        return notification_id

    def dispatch(
        self,
        *,
        trigger_event: str,
        cert_row_id: uuid.UUID | str | None,
        vessel_id: uuid.UUID | str | None,
        recipients: list[CertNotificationRecipient],
        title: str,
        message: str,
        payload: dict[str, Any] | None = None,
        escalation_level: int = 0,
        idempotency_scope: str | None = None,
    ) -> CertNotificationDispatchResult:
        sent_at = timezone.now()
        cert_row_value = str(cert_row_id) if cert_row_id else None
        vessel_value = str(vessel_id) if vessel_id else None
        record_id = cert_row_value or vessel_value or trigger_event
        payload_json = json.dumps(payload or {}, sort_keys=True, default=str)
        unique_recipients = [recipient for recipient in dict.fromkeys(recipients) if recipient.user_id]

        notification_rows: list[dict[str, Any]] = []
        meta_rows: list[dict[str, Any]] = []
        channels_by_recipient: dict[str, list[str]] = {}

        for recipient in unique_recipients:
            channels = recipient.channels()
            channels_by_recipient[recipient.user_id] = channels
            idempotency_key = self._build_idempotency_key(
                cert_row_id=cert_row_value,
                trigger_event=trigger_event,
                sent_at=sent_at,
                recipient_id=recipient.user_id,
                scope=idempotency_scope,
            )
            if self._idempotency_exists(idempotency_key, sent_at=sent_at):
                continue

            notification_id = str(uuid.uuid4())
            recipients_payload = [recipient.as_payload()]
            channels_payload = [{**recipient.as_payload(), "channels": channels}]
            delivery_payload = [
                {
                    "userId": recipient.user_id,
                    "channels": self._build_delivery_channels(
                        channels=channels,
                        notification_id=notification_id,
                        recipient_id=recipient.user_id,
                        recipient=recipient,
                        trigger_event=trigger_event,
                        cert_row_id=cert_row_value,
                        vessel_id=vessel_value,
                        title=title,
                        message=message,
                        payload=payload or {},
                        deliver_external=False,
                    ),
                }
            ]
            try:
                with transaction.atomic():
                    master_id = self._insert_master_notification(
                        record_id=record_id,
                        recipient_ref=recipient.user_id,
                        trigger_event=trigger_event,
                        title=title,
                        message=message,
                        payload_json=payload_json,
                        sent_at=sent_at,
                    )
                    self._insert_meta(
                        notification_id=notification_id,
                        master_notification_id=master_id,
                        trigger_event=trigger_event,
                        cert_row_id=cert_row_value,
                        vessel_id=vessel_value,
                        recipients_json=json.dumps(recipients_payload, sort_keys=True),
                        channels_json=json.dumps(channels_payload, sort_keys=True),
                        sent_at=sent_at,
                        delivery_status_json=json.dumps(delivery_payload, sort_keys=True),
                        escalation_level=escalation_level,
                        body_content=message,
                        idempotency_key=idempotency_key,
                    )
            except IntegrityError:
                if self._idempotency_key_exists_anywhere(idempotency_key):
                    continue
                raise

            delivery_payload = self._deliver_external_channels(
                delivery_payload=delivery_payload,
                notification_id=notification_id,
                recipient=recipient,
                trigger_event=trigger_event,
                cert_row_id=cert_row_value,
                vessel_id=vessel_value,
                title=title,
                message=message,
                payload=payload or {},
            )
            self._update_delivery_status(notification_id, delivery_payload)
            notification_rows.append(
                {
                    "id": master_id,
                    "module_code": self.module_code,
                    "record_id": record_id,
                    "recipient_ref": recipient.user_id,
                    "notification_kind": trigger_event,
                    "title": title,
                    "message": message,
                    "delivery_channel": "IN_APP",
                    "payload_json": payload_json,
                    "created_at": sent_at,
                }
            )
            meta_rows.append(
                {
                    "notification_id": notification_id,
                    "master_notification_id": master_id,
                    "trigger_event": trigger_event,
                    "cert_row_id": cert_row_value,
                    "vessel_id": vessel_value,
                    "recipients": recipients_payload,
                    "channels": channels_payload,
                    "sent_at": sent_at,
                    "escalation_level": escalation_level,
                    "idempotency_key": idempotency_key,
                }
            )

        return CertNotificationDispatchResult(
            notification_rows=notification_rows,
            meta_rows=meta_rows,
            channels_by_recipient=channels_by_recipient,
        )

    def _build_idempotency_key(
        self,
        *,
        cert_row_id: str | None,
        trigger_event: str,
        sent_at,
        recipient_id: str,
        scope: str | None,
    ) -> str:
        scope_value = scope or trigger_event
        entity_value = cert_row_id or "fleet"
        date_value = sent_at.date().isoformat()
        return f"{entity_value}:{scope_value}:{date_value}:{recipient_id}"[:128]

    def _build_delivery_channels(
        self,
        *,
        channels: list[str],
        notification_id: str,
        recipient_id: str,
        recipient: CertNotificationRecipient,
        trigger_event: str,
        cert_row_id: str | None,
        vessel_id: str | None,
        title: str,
        message: str,
        payload: dict[str, Any],
        deliver_external: bool = True,
    ) -> list[dict[str, str]]:
        delivery_channels: list[dict[str, str]] = []
        for channel in channels:
            channel_payload = {
                "channel": channel,
                "status": "created" if channel == "in_app" else "queued",
            }
            if channel == "email":
                channel_payload["ackUrl"] = build_magic_link_ack_path(
                    notification_id=notification_id,
                    recipient_id=recipient_id,
                )
            if channel == "slack":
                if deliver_external:
                    channel_payload = self._send_office_slack(
                        notification_id=notification_id,
                        recipient=recipient,
                        trigger_event=trigger_event,
                        cert_row_id=cert_row_id,
                        vessel_id=vessel_id,
                        title=title,
                        message=message,
                        payload=payload,
                    )
                else:
                    channel_payload = {
                        "channel": "slack",
                        "status": "queued",
                        "slackChannel": self._resolve_office_slack_channel(
                            vessel_id,
                            recipient=recipient,
                        ),
                    }
            delivery_channels.append(channel_payload)
        return delivery_channels

    def _deliver_external_channels(
        self,
        *,
        delivery_payload: list[dict[str, Any]],
        notification_id: str,
        recipient: CertNotificationRecipient,
        trigger_event: str,
        cert_row_id: str | None,
        vessel_id: str | None,
        title: str,
        message: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        changed = False
        for recipient_delivery in delivery_payload:
            if str(recipient_delivery.get("userId")) != str(recipient.user_id):
                continue
            channels = recipient_delivery.get("channels") or []
            for index, channel_payload in enumerate(channels):
                if channel_payload.get("channel") != "slack":
                    continue
                if channel_payload.get("status") != "queued":
                    continue
                channels[index] = self._send_office_slack(
                    notification_id=notification_id,
                    recipient=recipient,
                    trigger_event=trigger_event,
                    cert_row_id=cert_row_id,
                    vessel_id=vessel_id,
                    title=title,
                    message=message,
                    payload=payload,
                )
                changed = True
        return delivery_payload if changed else delivery_payload

    def _update_delivery_status(self, notification_id: str, delivery_payload: list[dict[str, Any]]) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {self._qualified(self.meta_table)}
                SET delivery_status_json = %s
                WHERE notification_id = %s
                """,
                [json.dumps(delivery_payload, sort_keys=True, default=str), notification_id],
            )

    def _send_office_slack(
        self,
        *,
        notification_id: str,
        recipient: CertNotificationRecipient,
        trigger_event: str,
        cert_row_id: str | None,
        vessel_id: str | None,
        title: str,
        message: str,
        payload: dict[str, Any],
    ) -> dict[str, str]:
        channel = self._resolve_office_slack_channel(vessel_id, recipient=recipient)
        slack_payload = {
            "module": self.module_code,
            "notificationId": notification_id,
            "triggerEvent": trigger_event,
            "certRowId": cert_row_id,
            "vesselId": vessel_id,
            "recipient": recipient.as_payload(),
            "payload": payload,
        }
        try:
            result = self.slack_relay.send_office_notification(
                channel=channel,
                title=title,
                message=message,
                payload=slack_payload,
            )
        except Exception as exc:
            return {
                "channel": "slack",
                "status": "failed",
                "slackChannel": channel,
                "error": str(exc),
            }

        return {
            "channel": "slack",
            "status": str(result.get("status") or ("delivered" if result.get("delivered") else "failed")),
            "slackChannel": str(result.get("slackChannel") or result.get("channel") or channel),
            **(
                {"providerMessageId": str(result.get("providerMessageId"))}
                if result.get("providerMessageId")
                else {}
            ),
            **({"error": str(result.get("error"))} if result.get("error") else {}),
        }

    def _resolve_office_slack_channel(
        self,
        vessel_id: str | None,
        *,
        recipient: CertNotificationRecipient | None = None,
    ) -> str:
        default_channel = str(
            getattr(self.slack_relay, "default_office_channel", DEFAULT_OFFICE_SLACK_CHANNEL)
            or DEFAULT_OFFICE_SLACK_CHANNEL
        )
        if not vessel_id or not self._table_exists(self.vessel_config_table):
            return self._resolve_role_office_slack_channel(recipient, default_channel=default_channel)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT slack_channel_office_default
                FROM {self._qualified(self.vessel_config_table)}
                WHERE vessel_id = %s
                """,
                [vessel_id],
            )
            row = cursor.fetchone()

        if not row or not row[0]:
            return self._resolve_role_office_slack_channel(recipient, default_channel=default_channel)
        return str(row[0])

    def _resolve_role_office_slack_channel(
        self,
        recipient: CertNotificationRecipient | None,
        *,
        default_channel: str,
    ) -> str:
        if recipient is None:
            return default_channel

        role = recipient.role.strip().lower()
        if "dpa" in role or "designated person" in role or "seq manager" in role:
            return str(getattr(self.slack_relay, "dpa_office_channel", DEFAULT_DPA_SLACK_CHANNEL) or DEFAULT_DPA_SLACK_CHANNEL)
        if "technical" in role or role in {"tm", "tech suptt", "technical suptt"}:
            return str(
                getattr(self.slack_relay, "technical_office_channel", DEFAULT_TECHNICAL_SLACK_CHANNEL)
                or DEFAULT_TECHNICAL_SLACK_CHANNEL
            )
        if "marine" in role:
            return str(
                getattr(self.slack_relay, "marine_office_channel", DEFAULT_MARINE_SLACK_CHANNEL)
                or DEFAULT_MARINE_SLACK_CHANNEL
            )
        return default_channel
