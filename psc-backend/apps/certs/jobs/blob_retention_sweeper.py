from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Callable

from django.db import connection, transaction
from django.utils import timezone as django_timezone

from apps.certs.services.pdf_blob_storage import delete_stored_blob


logger = logging.getLogger(__name__)

PDF_BLOB_TABLE = "vims_certs_pdf_blob"
AUDIT_TABLE = "vims_certs_audit_log"
SYSTEM_ACTOR = "system.blob_retention_sweeper"
SYSTEM_ROLE = "SYSTEM"
RETENTION_ACTION = "retention_purge"
DELETE_PENDING_GRACE_DAYS = 7


@dataclass(frozen=True)
class BlobRetentionResult:
    soft_marked: int
    hard_deleted: int
    files_deleted: int
    audit_recorded: bool
    reason: str
    now: datetime
    grace_cutoff: datetime


def run_blob_retention_sweeper(
    *,
    now: datetime | None = None,
    delete_blob: Callable[[str], bool] = delete_stored_blob,
) -> BlobRetentionResult:
    current = _utc(now or django_timezone.now())
    grace_cutoff = current - timedelta(days=DELETE_PENDING_GRACE_DAYS)
    table_names = set(connection.introspection.table_names())
    if PDF_BLOB_TABLE not in table_names or AUDIT_TABLE not in table_names:
        logger.error("Certs blob retention sweeper skipped; required tables are missing")
        return BlobRetentionResult(
            soft_marked=0,
            hard_deleted=0,
            files_deleted=0,
            audit_recorded=False,
            reason="missing_required_table",
            now=current,
            grace_cutoff=grace_cutoff,
        )

    with transaction.atomic():
        with connection.cursor() as cursor:
            hard_delete_rows = _list_hard_delete_rows(cursor, grace_cutoff)
            files_deleted = 0
            for row in hard_delete_rows:
                path = str(row.get("blob_storage_path") or "")
                if path and delete_blob(path):
                    files_deleted += 1

            hard_deleted = _delete_blob_rows(cursor, [str(row.get("blob_id")) for row in hard_delete_rows])
            soft_marked = _soft_mark_due_rows(cursor, current)
            _record_retention_summary(
                cursor,
                now=current,
                grace_cutoff=grace_cutoff,
                soft_marked=soft_marked,
                hard_deleted=hard_deleted,
                files_deleted=files_deleted,
            )

    logger.info(
        "certs blob retention sweeper complete; soft_marked=%s hard_deleted=%s files_deleted=%s",
        soft_marked,
        hard_deleted,
        files_deleted,
    )
    return BlobRetentionResult(
        soft_marked=soft_marked,
        hard_deleted=hard_deleted,
        files_deleted=files_deleted,
        audit_recorded=True,
        reason="completed",
        now=current,
        grace_cutoff=grace_cutoff,
    )


def _list_hard_delete_rows(cursor, grace_cutoff: datetime) -> list[dict[str, str]]:
    cursor.execute(
        f"""
        SELECT CAST(blob_id AS VARCHAR(64)) AS blob_id, blob_storage_path
        FROM {_qualified(PDF_BLOB_TABLE)}
        WHERE is_active = 0
          AND delete_pending_since <= %s
          AND retention_policy NOT IN ('retain_indefinitely', 'retain_all_versions')
          AND (dpa_retention_override_until IS NULL OR dpa_retention_override_until <= %s)
        """,
        [grace_cutoff, grace_cutoff],
    )
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _delete_blob_rows(cursor, blob_ids: list[str]) -> int:
    safe_blob_ids = [blob_id for blob_id in blob_ids if blob_id]
    if not safe_blob_ids:
        return 0
    placeholders = ", ".join(["%s"] * len(safe_blob_ids))
    cursor.execute(
        f"""
        DELETE FROM {_qualified(PDF_BLOB_TABLE)}
        WHERE blob_id IN ({placeholders})
        """,
        safe_blob_ids,
    )
    return len(safe_blob_ids)


def _soft_mark_due_rows(cursor, now: datetime) -> int:
    cursor.execute(
        f"""
        UPDATE {_qualified(PDF_BLOB_TABLE)}
        SET delete_pending_since = %s
        WHERE scheduled_delete_at <= %s
          AND is_active = 0
          AND delete_pending_since IS NULL
          AND retention_policy NOT IN ('retain_indefinitely', 'retain_all_versions')
          AND (dpa_retention_override_until IS NULL OR dpa_retention_override_until <= %s)
        """,
        [now, now, now],
    )
    return max(int(cursor.rowcount or 0), 0)


def _record_retention_summary(
    cursor,
    *,
    now: datetime,
    grace_cutoff: datetime,
    soft_marked: int,
    hard_deleted: int,
    files_deleted: int,
) -> None:
    after = {
        "softMarkedForDelete": soft_marked,
        "blobRowsHardDeleted": hard_deleted,
        "filesDeleted": files_deleted,
    }
    metadata = {
        "job": "blob_retention_sweeper",
        "graceDays": DELETE_PENDING_GRACE_DAYS,
        "graceCutoffUtc": _serialize(grace_cutoff),
        "softMarked": soft_marked,
        "hardDeleted": hard_deleted,
        "filesDeleted": files_deleted,
        "dbRoleBoundary": "vims_jobs",
        "auditPreserved": True,
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
            "pdf_blob",
            json.dumps(after, default=str),
            "Nightly blob retention sweeper completed.",
            json.dumps(metadata, default=str),
            "hot",
            1,
        ],
    )


def _serialize(value: datetime) -> str:
    return _utc(value).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _qualified(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name
