from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import connection


@dataclass(frozen=True)
class AuditLogPage:
    count: int
    page: int
    page_size: int
    includes_cold_tier: bool
    results: list[dict[str, Any]]


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def _bounded_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


class AuditLogRepository:
    def list_events(
        self,
        *,
        filters: dict[str, Any],
        vessel_scope: list[str] | None,
    ) -> AuditLogPage:
        page = _bounded_int(filters.get("page"), default=1, minimum=1, maximum=10_000)
        page_size = _bounded_int(filters.get("pageSize"), default=25, minimum=1, maximum=25)
        where, params = _build_where(filters, vessel_scope)
        if where == ["1 = 0"]:
            return AuditLogPage(count=0, page=page, page_size=page_size, includes_cold_tier=False, results=[])

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        offset = (page - 1) * page_size
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM dbo.vims_certs_audit_log
                {where_sql}
                """,
                params,
            )
            count_row = cursor.fetchone()
            count = int(count_row[0]) if count_row else 0

            cursor.execute(
                f"""
                SELECT
                    audit_id, timestamp_utc, vessel_id, actor_user_id, actor_role,
                    action, entity_type, entity_id,
                    CAST(NULL AS NVARCHAR(MAX)) AS before_json,
                    CAST(NULL AS NVARCHAR(MAX)) AS after_json,
                    reason,
                    CAST(NULL AS NVARCHAR(MAX)) AS event_metadata,
                    retention_tier, archived_at, schema_version
                FROM dbo.vims_certs_audit_log
                {where_sql}
                ORDER BY timestamp_utc DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                [*params, offset, page_size],
            )
            results = _fetch_all(cursor)

        return AuditLogPage(
            count=count,
            page=page,
            page_size=page_size,
            includes_cold_tier=any(str(row.get("retention_tier") or "").lower() == "cold" for row in results),
            results=results,
        )

    def get_event(self, audit_id: str, *, vessel_scope: list[str] | None) -> dict[str, Any] | None:
        where, params = _build_where({}, vessel_scope)
        if where == ["1 = 0"]:
            return None
        where.append("audit_id = %s")
        params.append(audit_id)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT TOP 1
                    audit_id, timestamp_utc, vessel_id, actor_user_id, actor_role,
                    action, entity_type, entity_id, before_json, after_json, reason,
                    event_metadata, retention_tier, archived_at, schema_version
                FROM dbo.vims_certs_audit_log
                WHERE {' AND '.join(where)}
                """,
                params,
            )
            return _fetch_one(cursor)

    def export_events(
        self,
        *,
        filters: dict[str, Any],
        vessel_scope: list[str] | None,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 5000))
        where, params = _build_where(filters, vessel_scope)
        if where == ["1 = 0"]:
            return []
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    audit_id, timestamp_utc, vessel_id, actor_user_id, actor_role,
                    action, entity_type, entity_id, before_json, after_json, reason,
                    event_metadata, retention_tier, archived_at, schema_version
                FROM dbo.vims_certs_audit_log
                {where_sql}
                ORDER BY timestamp_utc DESC
                OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
                """,
                params,
            )
            return _fetch_all(cursor)


def _build_where(filters: dict[str, Any], vessel_scope: list[str] | None) -> tuple[list[str], list[Any]]:
    where: list[str] = []
    params: list[Any] = []
    if vessel_scope is not None:
        scope = [str(vessel_id).strip() for vessel_id in vessel_scope if str(vessel_id or "").strip()]
        if not scope:
            return ["1 = 0"], []
        requested_vessel = str(filters.get("vesselId") or "").strip()
        if requested_vessel:
            if requested_vessel not in scope:
                return ["1 = 0"], []
            where.append("vessel_id = %s")
            params.append(requested_vessel)
        else:
            placeholders = ", ".join(["%s"] * len(scope))
            where.append(f"vessel_id IN ({placeholders})")
            params.extend(scope)
    elif filters.get("vesselId"):
        where.append("vessel_id = %s")
        params.append(str(filters["vesselId"]).strip())

    _add_text_filter(where, params, "actor_user_id", filters.get("actorUserId"))
    _add_text_filter(where, params, "action", filters.get("action"))
    _add_text_filter(where, params, "entity_type", filters.get("entityType"))
    _add_text_filter(where, params, "retention_tier", filters.get("retentionTier"))
    if filters.get("dateFrom"):
        where.append("timestamp_utc >= %s")
        params.append(filters["dateFrom"])
    if filters.get("dateTo"):
        where.append("timestamp_utc <= %s")
        params.append(filters["dateTo"])
    return where, params


def _add_text_filter(where: list[str], params: list[Any], column: str, value: object) -> None:
    text = str(value or "").strip()
    if not text or text == "all":
        return
    where.append(f"{column} = %s")
    params.append(text)
