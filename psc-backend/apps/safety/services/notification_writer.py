from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass

from django.db import connection
from django.utils import timezone


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
    table_name = "master_notification"
    module_code = "SAFETY"

    def __init__(self, *, slack_notifier: object | None = None) -> None:
        self.slack_notifier = slack_notifier or SlackWebhookNotifier()

    def table_exists(self) -> bool:
        return self.table_name in connection.introspection.table_names()

    def dispatch_notification(
        self,
        *,
        record_id: int,
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
        record_id: int,
        recipients: list[str],
        kind: str,
        title: str,
        message: str,
        payload: dict[str, object] | None = None,
        delivery_channel: str = "IN_APP",
    ) -> list[dict[str, object]]:
        if not self.table_exists():
            return []

        unique_recipients = [recipient for recipient in dict.fromkeys(recipients) if recipient]
        now = timezone.now()
        payload_json = json.dumps(payload or {}, sort_keys=True, default=str)
        rows: list[dict[str, object]] = []

        with connection.cursor() as cursor:
            for recipient in unique_recipients:
                cursor.execute(
                    """
                    INSERT INTO master_notification (
                        module_code,
                        record_id,
                        recipient_ref,
                        notification_kind,
                        title,
                        message,
                        delivery_channel,
                        payload_json,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        self.module_code,
                        record_id,
                        recipient,
                        kind,
                        title,
                        message,
                        delivery_channel,
                        payload_json,
                        now,
                    ],
                )
                rows.append(
                    {
                        "module_code": self.module_code,
                        "record_id": record_id,
                        "recipient_ref": recipient,
                        "notification_kind": kind,
                        "title": title,
                        "message": message,
                        "delivery_channel": delivery_channel,
                        "payload_json": payload_json,
                        "created_at": now,
                    }
                )

        return rows
