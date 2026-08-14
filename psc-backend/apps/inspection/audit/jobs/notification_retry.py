"""Audit notification transport retry job."""

from __future__ import annotations

from dataclasses import dataclass

from apps.inspection.audit.services.email_relay import AuditEmailRelay, AuditEmailRelayResult
from apps.inspection.audit.services.slack_relay import AuditSlackRelay, AuditSlackRelayResult


@dataclass(frozen=True)
class AuditNotificationRetryResult:
    email: AuditEmailRelayResult
    slack: AuditSlackRelayResult


def run_notification_retry(
    *,
    limit: int = 100,
    email_relay: AuditEmailRelay | None = None,
    slack_relay: AuditSlackRelay | None = None,
    now=None,
) -> AuditNotificationRetryResult:
    email_result = (email_relay or AuditEmailRelay()).process_due(limit=limit, now=now)
    slack_result = (slack_relay or AuditSlackRelay()).process_due(limit=limit, now=now)
    return AuditNotificationRetryResult(email=email_result, slack=slack_result)


__all__ = ["AuditNotificationRetryResult", "run_notification_retry"]
