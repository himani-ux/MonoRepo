from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from typing import Any

from django.db import connection, transaction
from django.utils import timezone as django_timezone


logger = logging.getLogger(__name__)

AUDIT_TABLE = "vims_certs_audit_log"
SYSTEM_ACTOR = "system.audit_archiver"
SYSTEM_ROLE = "SYSTEM"
RETENTION_ACTION = "retention_purge"


@dataclass(frozen=True)
class AuditArchiverResult:
    cold_flipped: int
    purged: int
    audit_recorded: bool
    hot_cutoff: datetime
    purge_cutoff: datetime
    reason: str


def run_audit_archiver(*, now: datetime | None = None) -> AuditArchiverResult:
    current = _utc(now or django_timezone.now())
    hot_cutoff = _subtract_years(current, 2)
    purge_cutoff = _subtract_years(current, 5)

    if AUDIT_TABLE not in connection.introspection.table_names():
        logger.error("Certs audit archiver skipped; audit table is missing")
        return AuditArchiverResult(
            cold_flipped=0,
            purged=0,
            audit_recorded=False,
            hot_cutoff=hot_cutoff,
            purge_cutoff=purge_cutoff,
            reason="missing_audit_log_table",
        )

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {_qualified(AUDIT_TABLE)}
                SET retention_tier = %s,
                    archived_at = %s
                WHERE timestamp_utc <= %s
                  AND retention_tier = %s
                """,
                ["cold", current, hot_cutoff, "hot"],
            )
            cold_flipped = max(int(cursor.rowcount or 0), 0)

            cursor.execute(
                f"""
                DELETE FROM {_qualified(AUDIT_TABLE)}
                WHERE timestamp_utc <= %s
                """,
                [purge_cutoff],
            )
            purged = max(int(cursor.rowcount or 0), 0)

            _record_retention_summary(
                cursor,
                now=current,
                hot_cutoff=hot_cutoff,
                purge_cutoff=purge_cutoff,
                cold_flipped=cold_flipped,
                purged=purged,
            )
            audit_recorded = True

    logger.info(
        "certs audit archiver complete; cold_flipped=%s purged=%s audit_recorded=%s",
        cold_flipped,
        purged,
        audit_recorded,
    )
    return AuditArchiverResult(
        cold_flipped=cold_flipped,
        purged=purged,
        audit_recorded=audit_recorded,
        hot_cutoff=hot_cutoff,
        purge_cutoff=purge_cutoff,
        reason="completed",
    )


def _record_retention_summary(
    cursor,
    *,
    now: datetime,
    hot_cutoff: datetime,
    purge_cutoff: datetime,
    cold_flipped: int,
    purged: int,
) -> None:
    metadata: dict[str, Any] = {
        "job": "audit_archiver",
        "hotCutoffUtc": _serialize(now=hot_cutoff),
        "purgeCutoffUtc": _serialize(now=purge_cutoff),
        "coldFlipped": cold_flipped,
        "purged": purged,
        "dbRoleBoundary": "vims_jobs",
    }
    after = {
        "retentionTier": "hot",
        "archivedRowsFlippedToCold": cold_flipped,
        "rowsPurgedPastFiveYears": purged,
    }
    cursor.execute(
        f"""
        INSERT INTO {_qualified(AUDIT_TABLE)} (
            timestamp_utc, vessel_id, actor_user_id, actor_role, action, entity_type, entity_id,
            before_json, after_json, reason, event_metadata, retention_tier, archived_at, schema_version
        )
        VALUES (%s, NULL, %s, %s, %s, %s, NULL, NULL, %s, %s, %s, %s, NULL, %s)
        """,
        [
            now,
            SYSTEM_ACTOR,
            SYSTEM_ROLE,
            RETENTION_ACTION,
            "audit_log",
            json.dumps(after, default=str),
            "Nightly audit retention batch completed.",
            json.dumps(metadata, default=str),
            "hot",
            1,
        ],
    )


def _subtract_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def _serialize(*, now: datetime) -> str:
    return _utc(now).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _qualified(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name
