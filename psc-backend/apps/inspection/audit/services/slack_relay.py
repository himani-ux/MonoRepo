"""Audit notification Slack relay for per-vessel incoming webhooks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable

import requests
from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import MasterSlackChannel, NotificationDeliveryLog
from apps.notifications.models import Notification

SLACK_CHANNEL = "SLACK"
QUEUED_STATUSES = ("QUEUED", "RETRYING")
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (1, 2, 4)
SYSTEM_ACTOR = "system.audit_slack_relay"


@dataclass(frozen=True)
class AuditSlackRelayResult:
    scanned: int = 0
    sent: int = 0
    retrying: int = 0
    failed_permanent: int = 0
    skipped_not_due: int = 0

    def plus(self, **changes: int) -> "AuditSlackRelayResult":
        data = {
            "scanned": self.scanned,
            "sent": self.sent,
            "retrying": self.retrying,
            "failed_permanent": self.failed_permanent,
            "skipped_not_due": self.skipped_not_due,
        }
        for key, value in changes.items():
            data[key] += value
        return AuditSlackRelayResult(**data)


class AuditSlackRelay:
    def __init__(
        self,
        *,
        http_post: Callable[..., Any] | None = None,
        now_fn: Callable[[], object] = timezone.now,
        timeout_seconds: int = 5,
    ) -> None:
        self.http_post = http_post or requests.post
        self.now_fn = now_fn
        self.timeout_seconds = timeout_seconds

    def process_due(self, *, limit: int = 100, now=None) -> AuditSlackRelayResult:
        current = now or self.now_fn()
        result = AuditSlackRelayResult()
        candidates = (
            NotificationDeliveryLog.objects.filter(channel=SLACK_CHANNEL, status__in=QUEUED_STATUSES)
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

    def deliver(self, delivery_log: NotificationDeliveryLog, *, now=None) -> AuditSlackRelayResult:
        current = now or self.now_fn()
        notification = _get_notification(delivery_log)
        if notification is None:
            _mark_failed(delivery_log, "PSC_NOTIFICATION_NOT_FOUND", now=current, permanent=True)
            return AuditSlackRelayResult(scanned=1, failed_permanent=1)
        if notification.vessel_id is None:
            _mark_failed(delivery_log, "SLACK_SKIPPED_FOR_OFFICE_AUDIT", now=current, permanent=True)
            return AuditSlackRelayResult(scanned=1, failed_permanent=1)

        slack_channel = _get_configured_channel(notification=notification, delivery_log=delivery_log)
        if slack_channel is None or not str(slack_channel.webhook_url or "").strip():
            _mark_failed(delivery_log, "SLACK_CHANNEL_NOT_CONFIGURED", now=current, permanent=True)
            return AuditSlackRelayResult(scanned=1, failed_permanent=1)

        try:
            response = self.http_post(
                slack_channel.webhook_url,
                json=_slack_payload(notification=notification, channel=slack_channel),
                timeout=self.timeout_seconds,
            )
            status_code = int(getattr(response, "status_code", 200))
            if status_code < 200 or status_code >= 300:
                raise RuntimeError(f"SLACK_WEBHOOK_HTTP_{status_code}")
        except Exception as exc:
            permanent = delivery_log.attempt_count + 1 >= MAX_RETRY_ATTEMPTS
            _mark_failed(delivery_log, str(exc), now=current, permanent=permanent)
            if permanent:
                return AuditSlackRelayResult(scanned=1, failed_permanent=1)
            return AuditSlackRelayResult(scanned=1, retrying=1)

        _mark_sent(delivery_log, now=current)
        return AuditSlackRelayResult(scanned=1, sent=1)


def process_due_audit_slack_notifications(*, limit: int = 100, now=None) -> AuditSlackRelayResult:
    return AuditSlackRelay().process_due(limit=limit, now=now)


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


def _get_configured_channel(
    *,
    notification: Notification,
    delivery_log: NotificationDeliveryLog,
) -> MasterSlackChannel | None:
    vessel_id = str(notification.vessel_id)
    queryset = MasterSlackChannel.objects.filter(
        scope_type="VESSEL",
        scope_value__iexact=vessel_id,
        is_active=True,
    )
    if delivery_log.recipient_address:
        queryset = queryset.filter(channel_name=delivery_log.recipient_address)
    for channel in queryset.order_by("channel_name"):
        configured_types = {part.strip().upper() for part in channel.notification_types_csv.split(",") if part.strip()}
        if not configured_types or "ALL" in configured_types or notification.notification_type in configured_types:
            return channel
    return None


def _slack_payload(*, notification: Notification, channel: MasterSlackChannel) -> dict[str, object]:
    return {
        "text": f"{notification.title}\n{notification.message}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{notification.title}*\n{notification.message}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"Audit notification `{notification.notification_type}` "
                            f"for vessel `{notification.vessel_id}` via `{channel.channel_name}`"
                        ),
                    }
                ],
            },
        ],
    }


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
        delivery_log.last_error = str(error or "SLACK_DELIVERY_FAILED")
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


__all__ = [
    "AuditSlackRelay",
    "AuditSlackRelayResult",
    "MAX_RETRY_ATTEMPTS",
    "process_due_audit_slack_notifications",
]
