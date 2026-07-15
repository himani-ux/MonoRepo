from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from typing import Iterable

from django.db import connection
from django.utils import timezone as django_timezone
from django.utils.dateparse import parse_date

from apps.certs.services.notification_dispatcher import CertNotificationDispatcher, CertNotificationRecipient


ICT = timezone(timedelta(hours=7), name="ICT")
MONTHLY_DIGEST_EVENT = "monthly_digest"
MONTHLY_DIGEST_TITLE = "Monthly Certs fleet digest"
ALLOWED_DIGEST_ROLE_KEYS = {"dpa", "marinesuperintendent", "marinesupt", "marinesuptt"}


@dataclass(frozen=True)
class MonthlyDigestResult:
    dispatched: bool
    reason: str
    recipient_ids: list[str]
    summary: dict[str, int | str]


def run_monthly_digest(
    *,
    now: datetime | None = None,
    dispatcher: CertNotificationDispatcher | None = None,
    candidate_recipients: Iterable[CertNotificationRecipient] | None = None,
) -> MonthlyDigestResult:
    current = now or django_timezone.now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    ict_now = current.astimezone(ICT)

    if not _is_monthly_digest_window(ict_now):
        return MonthlyDigestResult(
            dispatched=False,
            reason="outside_monthly_digest_window",
            recipient_ids=[],
            summary={},
        )

    recipients = _digest_recipients(
        candidate_recipients if candidate_recipients is not None else _load_default_candidate_recipients()
    )
    if not recipients:
        return MonthlyDigestResult(
            dispatched=False,
            reason="no_digest_recipients",
            recipient_ids=[],
            summary=_build_fleet_summary(ict_now),
        )

    summary = _build_fleet_summary(ict_now)
    payload = {
        "digestFrequency": "monthly",
        "period": {
            "year": ict_now.year,
            "month": ict_now.month,
            "timezone": "ICT",
        },
        "summary": summary,
    }
    message = (
        f"Fleet digest for {ict_now:%b %Y}: "
        f"{summary['activeTrackedItems']} active tracked items, "
        f"{summary['expiredItems']} expired, "
        f"{summary['criticalItems']} critical."
    )

    dispatch_result = (dispatcher or CertNotificationDispatcher()).dispatch(
        trigger_event=MONTHLY_DIGEST_EVENT,
        cert_row_id=None,
        vessel_id=None,
        recipients=recipients,
        title=MONTHLY_DIGEST_TITLE,
        message=message,
        payload=payload,
        escalation_level=0,
        idempotency_scope=f"monthly-digest-{ict_now:%Y-%m}",
    )

    return MonthlyDigestResult(
        dispatched=bool(dispatch_result.notification_rows),
        reason="dispatched" if dispatch_result.notification_rows else "already_dispatched",
        recipient_ids=[row["recipient_ref"] for row in dispatch_result.notification_rows],
        summary=summary,
    )


def _is_monthly_digest_window(ict_now: datetime) -> bool:
    return ict_now.day == 1 and ict_now.hour == 8


def _digest_recipients(candidates: Iterable[CertNotificationRecipient]) -> list[CertNotificationRecipient]:
    recipients: list[CertNotificationRecipient] = []
    seen: set[str] = set()
    for recipient in candidates:
        if recipient.normalized_side() != "office":
            continue
        if _role_key(recipient.role) not in ALLOWED_DIGEST_ROLE_KEYS:
            continue
        if recipient.user_id in seen:
            continue
        seen.add(recipient.user_id)
        recipients.append(recipient)
    return recipients


def _role_key(role: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", role.lower())


def _load_default_candidate_recipients() -> list[CertNotificationRecipient]:
    if "users" not in connection.introspection.table_names():
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT employee_id, employee_role
            FROM {_qualified("users")}
            WHERE COALESCE(is_active, 1) = 1
              AND COALESCE(is_deleted, 0) = 0
              AND employee_role IS NOT NULL
            """
        )
        rows = cursor.fetchall()

    return [
        CertNotificationRecipient(user_id=str(employee_id), role=str(role), side="office")
        for employee_id, role in rows
        if employee_id and role
    ]


def _build_fleet_summary(ict_now: datetime) -> dict[str, int | str]:
    summary: dict[str, int | str] = {
        "activeTrackedItems": 0,
        "expiredItems": 0,
        "criticalItems": 0,
        "expiringNext30Days": 0,
        "generatedAt": ict_now.isoformat(),
    }
    if "vims_certs_tracked_item" not in connection.introspection.table_names():
        return summary

    current_date = ict_now.date()
    next_30_date = current_date + timedelta(days=30)
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT status, expiry_date
            FROM {_qualified("vims_certs_tracked_item")}
            WHERE lifecycle_status = %s
            """,
            ["active"],
        )
        rows = cursor.fetchall()

    summary["activeTrackedItems"] = len(rows)
    for status, expiry_date in rows:
        status_value = str(status or "").strip().lower()
        date_value = _as_date(expiry_date)
        if status_value == "expired" or (date_value is not None and date_value < current_date):
            summary["expiredItems"] = int(summary["expiredItems"]) + 1
        if status_value == "critical":
            summary["criticalItems"] = int(summary["criticalItems"]) + 1
        if date_value is not None and current_date <= date_value <= next_30_date:
            summary["expiringNext30Days"] = int(summary["expiringNext30Days"]) + 1
    return summary


def _as_date(value):
    if value is None:
        return None
    if hasattr(value, "date") and not isinstance(value, str):
        return value.date()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value
    return parse_date(str(value))


def _qualified(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name
