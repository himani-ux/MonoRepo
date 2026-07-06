from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from django.db import connection
from django.utils import timezone

from apps.certs.services.slack_relay import CertSlackRelay


EMAIL_RETRY_BACKOFF_MINUTES = (1, 5, 30)
MAX_EMAIL_RETRY_ATTEMPTS = len(EMAIL_RETRY_BACKOFF_MINUTES)


class CertEmailDeliveryService:
    meta_table = "vims_certs_notification_meta"
    master_table = "master_notification"

    def __init__(self, *, slack_relay: object | None = None) -> None:
        self.slack_relay = slack_relay or CertSlackRelay()

    def _qualified(self, table_name: str) -> str:
        if connection.vendor == "microsoft":
            return f"dbo.{table_name}"
        return table_name

    def record_email_failure(
        self,
        *,
        notification_id: str,
        recipient_id: str,
        error: str,
    ) -> dict[str, Any]:
        row = self._get_notification_row(notification_id)
        delivery_payload = _json_value(row.get("delivery_status_json"), [])
        recipient_delivery = _find_recipient_delivery(delivery_payload, recipient_id)
        email_channel = _find_channel(recipient_delivery, "email")
        if email_channel is None:
            raise ValueError("Notification has no email channel for this recipient.")

        now = timezone.now()
        attempts = list(email_channel.get("attempts") or [])
        attempts.append(
            {
                "attempt": len(attempts) + 1,
                "status": "failed",
                "error": str(error),
                "attemptedAt": now.isoformat(),
            }
        )
        email_channel["attempts"] = attempts
        email_channel["retryCount"] = len(attempts)
        email_channel["lastError"] = str(error)

        result: dict[str, Any] = {"email": email_channel, "slackDmFallback": None}
        if len(attempts) < MAX_EMAIL_RETRY_ATTEMPTS:
            next_retry_minutes = EMAIL_RETRY_BACKOFF_MINUTES[len(attempts) - 1]
            email_channel["status"] = "retry_scheduled"
            email_channel["nextRetryInMinutes"] = next_retry_minutes
            email_channel["nextRetryAt"] = (now + timedelta(minutes=next_retry_minutes)).isoformat()
        else:
            email_channel["status"] = "bouncing"
            email_channel["bouncing"] = True
            email_channel["bouncedAt"] = now.isoformat()
            email_channel.pop("nextRetryInMinutes", None)
            email_channel.pop("nextRetryAt", None)
            self._mark_user_bouncing(recipient_id)
            if self._is_critical(row):
                slack_dm_status = self._send_critical_bounce_slack_dm(
                    notification_id=notification_id,
                    recipient_id=recipient_id,
                    row=row,
                )
                recipient_delivery["channels"].append(slack_dm_status)
                result["slackDmFallback"] = slack_dm_status

        self._update_delivery_status(notification_id, delivery_payload)
        return result

    def _get_notification_row(self, notification_id: str) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    meta.notification_id,
                    meta.trigger_event,
                    meta.cert_row_id,
                    meta.vessel_id,
                    meta.delivery_status_json,
                    mn.title,
                    mn.message,
                    mn.payload_json
                FROM {self._qualified(self.meta_table)} meta
                JOIN {self._qualified(self.master_table)} mn
                  ON mn.id = meta.master_notification_id
                WHERE meta.notification_id = %s
                """,
                [notification_id],
            )
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
        if row is None:
            raise ValueError("Notification not found.")
        return dict(zip(columns, row))

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

    def _send_critical_bounce_slack_dm(
        self,
        *,
        notification_id: str,
        recipient_id: str,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        payload = _json_value(row.get("payload_json"), {})
        slack_payload = {
            "module": "CERTS",
            "notificationId": notification_id,
            "triggerEvent": row.get("trigger_event"),
            "certRowId": row.get("cert_row_id"),
            "vesselId": row.get("vessel_id"),
            "recipient": {"userId": recipient_id, "side": "vessel"},
            "criticalBounceException": True,
            "payload": payload,
        }
        try:
            result = self.slack_relay.send_direct_message(
                user_id=recipient_id,
                title=str(row.get("title") or ""),
                message=str(row.get("message") or ""),
                payload=slack_payload,
            )
        except Exception as exc:
            return {
                "channel": "slack_dm",
                "status": "failed",
                "criticalBounceException": True,
                "error": str(exc),
            }

        status = str(result.get("status") or ("delivered" if result.get("delivered") else "failed"))
        return {
            "channel": "slack_dm",
            "status": status,
            "criticalBounceException": True,
            **(
                {"providerMessageId": str(result.get("providerMessageId"))}
                if result.get("providerMessageId")
                else {}
            ),
            **({"error": str(result.get("error"))} if result.get("error") else {}),
        }

    def _is_critical(self, row: dict[str, Any]) -> bool:
        trigger_event = str(row.get("trigger_event") or "").lower()
        if trigger_event in {"cert_expired", "cert_expiring_7d", "cert_expiring_1d"}:
            return True
        payload = _json_value(row.get("payload_json"), {})
        try:
            days_to_go = int(payload.get("daysToGo"))
        except (TypeError, ValueError):
            return False
        return days_to_go <= 7

    def _mark_user_bouncing(self, recipient_id: str) -> None:
        table_names = set(connection.introspection.table_names())
        if "users" not in table_names:
            return
        try:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    connection.cursor(),
                    "users",
                )
            }
        except Exception:
            return
        if "delivery_status" not in columns:
            return
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {self._qualified('users')} SET delivery_status = %s WHERE employee_id = %s",
                ["bouncing", recipient_id],
            )


def _json_value(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _find_recipient_delivery(delivery_payload: list[dict[str, Any]], recipient_id: str) -> dict[str, Any]:
    for entry in delivery_payload:
        if str(entry.get("userId")) == str(recipient_id):
            return entry
    raise ValueError("Recipient delivery status not found.")


def _find_channel(recipient_delivery: dict[str, Any], channel_name: str) -> dict[str, Any] | None:
    for channel in recipient_delivery.get("channels") or []:
        if channel.get("channel") == channel_name:
            return channel
    return None
