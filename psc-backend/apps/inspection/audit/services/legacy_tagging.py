"""Legacy AUDIT/RS discovery and Audit-owned tag loading."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from django.db import connections, transaction
from django.utils import timezone


LEGACY_INSPECTION_TYPES = ("AUDIT", "RS")
DEFAULT_TAGGED_BY = "migration"
DEFAULT_TAG_REASON = "pre-deploy AUDIT/RS row"


@dataclass(frozen=True)
class LegacyTaggingResult:
    discovered: int
    already_tagged: int
    inserted: int
    dry_run: bool


def tag_legacy_audit_inspections(
    *,
    using: str = "default",
    apply: bool = False,
    deploy_date: datetime | None = None,
    tagged_by: str = DEFAULT_TAGGED_BY,
    tag_reason: str = DEFAULT_TAG_REASON,
) -> LegacyTaggingResult:
    """Discover pre-deploy AUDIT/RS inspections and tag them in Audit-owned storage.

    The discovery query reads ``psc_inspection`` only. Writes, when explicitly
    enabled, go only to ``audit_legacy_inspection_tag``.
    """

    connection = connections[using]
    legacy_ids = _discover_legacy_inspection_ids(connection.cursor(), deploy_date=deploy_date)
    if not legacy_ids:
        return LegacyTaggingResult(discovered=0, already_tagged=0, inserted=0, dry_run=not apply)

    with connection.cursor() as cursor:
        existing_ids = _existing_tag_ids(cursor, legacy_ids)

    to_insert = [inspection_id for inspection_id in legacy_ids if inspection_id not in existing_ids]
    if not apply or not to_insert:
        return LegacyTaggingResult(
            discovered=len(legacy_ids),
            already_tagged=len(existing_ids),
            inserted=0,
            dry_run=not apply,
        )

    with transaction.atomic(using=using):
        with connection.cursor() as cursor:
            _insert_tags(
                cursor,
                inspection_ids=to_insert,
                tagged_at=timezone.now(),
                tagged_by=tagged_by,
                tag_reason=tag_reason,
            )

    return LegacyTaggingResult(
        discovered=len(legacy_ids),
        already_tagged=len(existing_ids),
        inserted=len(to_insert),
        dry_run=False,
    )


def _discover_legacy_inspection_ids(cursor, *, deploy_date: datetime | None) -> list[str]:
    query = (
        "SELECT id FROM psc_inspection "
        "WHERE inspection_type IN (%s, %s)"
    )
    params: list[object] = list(LEGACY_INSPECTION_TYPES)
    if deploy_date is not None:
        query += " AND created_date < %s"
        params.append(deploy_date)
    query += " ORDER BY id"

    try:
        cursor.execute(query, params)
        return [_legacy_key(row[0]) for row in cursor.fetchall()]
    finally:
        cursor.close()


def _existing_tag_ids(cursor, inspection_ids: Iterable[str]) -> set[str]:
    existing: set[str] = set()
    for inspection_id in inspection_ids:
        cursor.execute(
            "SELECT psc_inspection_id FROM audit_legacy_inspection_tag WHERE psc_inspection_id = %s",
            [_legacy_key(inspection_id)],
        )
        row = cursor.fetchone()
        if row:
            existing.add(_legacy_key(row[0]))
    return existing


def _insert_tags(
    cursor,
    *,
    inspection_ids: Iterable[str],
    tagged_at: datetime,
    tagged_by: str,
    tag_reason: str,
) -> None:
    rows = [
        (_legacy_key(inspection_id), True, tagged_at, tagged_by, tag_reason)
        for inspection_id in inspection_ids
    ]
    if not rows:
        return

    cursor.executemany(
        "INSERT INTO audit_legacy_inspection_tag "
        "(psc_inspection_id, is_legacy, tagged_at, tagged_by, tag_reason) "
        "VALUES (%s, %s, %s, %s, %s)",
        rows,
    )


def _legacy_key(value: object) -> str:
    text = str(value).strip()
    return text.replace("-", "")
