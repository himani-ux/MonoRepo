from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import uuid
from typing import Any

from django.db import connection
from django.utils import timezone as django_timezone
from django.utils.dateparse import parse_datetime

from apps.certs.services.slack_relay import CertSlackRelay, DEFAULT_OFFICE_SLACK_CHANNEL


logger = logging.getLogger(__name__)

SETTINGS_TABLE = "vims_certs_settings"
SETTINGS_SINGLETON_KEY = "certs"
STALE_AFTER = timedelta(hours=2)
SYSTEM_ACTOR = "system.cadence_heartbeat"


@dataclass(frozen=True)
class CadenceHeartbeatResult:
    last_heartbeat_at: datetime | None


@dataclass(frozen=True)
class CadenceDeadmanResult:
    stale: bool
    alert_sent: bool
    last_heartbeat_at: datetime | None
    heartbeat_age_seconds: int | None
    reason: str


def run_cadence_heartbeat(*, now: datetime | None = None) -> CadenceHeartbeatResult:
    current = _utc(now or django_timezone.now())
    if SETTINGS_TABLE not in connection.introspection.table_names():
        logger.error("Certs cadence heartbeat table is missing")
        return CadenceHeartbeatResult(last_heartbeat_at=None)

    existing = _fetch_settings_row()
    with connection.cursor() as cursor:
        if existing:
            cursor.execute(
                f"""
                UPDATE {_qualified(SETTINGS_TABLE)}
                SET last_heartbeat_at = %s,
                    updated_at = %s,
                    updated_by = %s
                WHERE singleton_key = %s
                """,
                [current, current, SYSTEM_ACTOR, SETTINGS_SINGLETON_KEY],
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {_qualified(SETTINGS_TABLE)} (
                    settings_id, singleton_key, last_heartbeat_at, created_at, updated_at, updated_by
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [str(uuid.uuid4()), SETTINGS_SINGLETON_KEY, current, current, current, SYSTEM_ACTOR],
            )
    logger.info("certs cadence heartbeat stamped at %s", current.isoformat())
    return CadenceHeartbeatResult(last_heartbeat_at=current)


def run_cadence_deadman_check(
    *,
    now: datetime | None = None,
    slack_relay: CertSlackRelay | None = None,
) -> CadenceDeadmanResult:
    current = _utc(now or django_timezone.now())
    last_heartbeat = get_last_cadence_heartbeat()
    if last_heartbeat is None:
        age_seconds = None
        stale = True
        reason = "missing_heartbeat"
    else:
        age_seconds = max(int((current - last_heartbeat).total_seconds()), 0)
        stale = age_seconds > int(STALE_AFTER.total_seconds())
        reason = "stale_heartbeat" if stale else "fresh_heartbeat"

    if not stale:
        logger.info("certs cadence heartbeat fresh; age_seconds=%s", age_seconds)
        return CadenceDeadmanResult(
            stale=False,
            alert_sent=False,
            last_heartbeat_at=last_heartbeat,
            heartbeat_age_seconds=age_seconds,
            reason=reason,
        )

    payload = {
        "eventType": "cadence_deadman_alert",
        "lastCadenceHeartbeat": serialize_utc(last_heartbeat),
        "heartbeatAgeSeconds": age_seconds,
        "staleThresholdSeconds": int(STALE_AFTER.total_seconds()),
    }
    status = (slack_relay or CertSlackRelay()).send_office_notification(
        channel=DEFAULT_OFFICE_SLACK_CHANNEL,
        title="Certs cadence heartbeat stale",
        message="The Certs cadence heartbeat is stale; expiry alerts may not be running.",
        payload=payload,
    )
    alert_sent = bool(status.get("attempted"))
    logger.error("certs cadence heartbeat stale; age_seconds=%s alert_sent=%s", age_seconds, alert_sent)
    return CadenceDeadmanResult(
        stale=True,
        alert_sent=alert_sent,
        last_heartbeat_at=last_heartbeat,
        heartbeat_age_seconds=age_seconds,
        reason=reason,
    )


def get_last_cadence_heartbeat() -> datetime | None:
    if SETTINGS_TABLE not in connection.introspection.table_names():
        return None
    row = _fetch_settings_row()
    return _parse_datetime(row.get("last_heartbeat_at")) if row else None


def serialize_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _utc(value).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fetch_settings_row() -> dict[str, Any] | None:
    sql = (
        f"SELECT TOP 1 singleton_key, last_heartbeat_at FROM {_qualified(SETTINGS_TABLE)} WHERE singleton_key = %s"
        if connection.vendor == "microsoft"
        else f"SELECT singleton_key, last_heartbeat_at FROM {_qualified(SETTINGS_TABLE)} WHERE singleton_key = %s LIMIT 1"
    )
    with connection.cursor() as cursor:
        cursor.execute(sql, [SETTINGS_SINGLETON_KEY])
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _utc(value)
    parsed = parse_datetime(str(value))
    if parsed is None:
        parsed = parse_datetime(str(value).replace(" ", "T"))
    return _utc(parsed) if parsed else None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _qualified(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name
