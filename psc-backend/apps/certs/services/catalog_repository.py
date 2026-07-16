from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from django.db import connection


CATALOG_COLUMNS = (
    "canonical_code",
    "section_id",
    "display_name",
    "short_name",
    "print_section_label",
    "validity_type",
    "cadence_months",
    "cadence_custom_days",
    "issuing_authority_type",
    "is_class_tracked",
    "submission_scope",
    "parent_id",
    "relationship_type_default",
    "applicable_ship_types",
    "mandatory_for_all_vessels",
    "applicability_mode",
    "specific_vessel_ids",
    "parent_supports_dynamic_children",
    "age_gate_max_years",
    "retain_all_versions",
    "linked_pms_component_id",
    "alert_lead_overrides",
    "regulatory_anchor",
    "legacy_remarks",
    "print_order",
    "is_active",
)

CAMEL_TO_COLUMN = {
    "canonicalCode": "canonical_code",
    "sectionId": "section_id",
    "displayName": "display_name",
    "shortName": "short_name",
    "printSectionLabel": "print_section_label",
    "validityType": "validity_type",
    "cadenceMonths": "cadence_months",
    "cadenceCustomDays": "cadence_custom_days",
    "issuingAuthorityType": "issuing_authority_type",
    "isClassTracked": "is_class_tracked",
    "submissionScope": "submission_scope",
    "parentId": "parent_id",
    "relationshipTypeDefault": "relationship_type_default",
    "applicableShipTypes": "applicable_ship_types",
    "mandatoryForAllVessels": "mandatory_for_all_vessels",
    "applicabilityMode": "applicability_mode",
    "specificVesselIds": "specific_vessel_ids",
    "parentSupportsDynamicChildren": "parent_supports_dynamic_children",
    "ageGateMaxYears": "age_gate_max_years",
    "retainAllVersions": "retain_all_versions",
    "linkedPmsComponentId": "linked_pms_component_id",
    "alertLeadOverrides": "alert_lead_overrides",
    "regulatoryAnchor": "regulatory_anchor",
    "legacyRemarks": "legacy_remarks",
    "printOrder": "print_order",
    "isActive": "is_active",
}

JSON_COLUMNS = {"applicable_ship_types", "specific_vessel_ids", "alert_lead_overrides"}


@dataclass(frozen=True)
class CatalogRowPage:
    count: int
    page: int | None
    page_size: int | None
    results: list[dict[str, Any]]


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def _db_value(column: str, value: Any) -> Any:
    if column in JSON_COLUMNS and value is not None:
        return json.dumps([str(item) for item in value]) if isinstance(value, list) else json.dumps(value)
    if value == "":
        return None
    return str(value) if column.endswith("_id") and value is not None else value


def _row_select_sql(where_sql: str = "") -> str:
    return f"""
        SELECT
            r.catalog_id, r.canonical_code, r.section_id, s.section_code, s.display_name AS section_name,
            r.display_name, r.short_name, r.print_section_label, r.validity_type,
            r.cadence_months, r.cadence_custom_days, r.issuing_authority_type,
            r.is_class_tracked, r.submission_scope, r.parent_id, r.relationship_type_default,
            r.applicable_ship_types, r.mandatory_for_all_vessels, r.applicability_mode,
            r.specific_vessel_ids, r.parent_supports_dynamic_children, r.age_gate_max_years,
            r.retain_all_versions, r.linked_pms_component_id, r.alert_lead_overrides,
            r.regulatory_anchor, r.legacy_remarks, r.print_order, r.is_active,
            r.created_at, r.created_by, r.updated_at, r.updated_by
        FROM dbo.vims_certs_catalog_row r
        INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = r.section_id
        {where_sql}
    """


class CatalogRepository:
    def list_sections(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    s.section_id, s.section_code, s.display_name, s.sort_order,
                    COUNT(r.catalog_id) AS active_row_count
                FROM dbo.vims_certs_catalog_section s
                LEFT JOIN dbo.vims_certs_catalog_row r
                    ON r.section_id = s.section_id AND r.is_active = 1
                GROUP BY s.section_id, s.section_code, s.display_name, s.sort_order
                ORDER BY s.sort_order, s.section_id
                """
            )
            return _fetch_all(cursor)

    def list_rows(
        self,
        *,
        section_id: int | None = None,
        is_active: bool | None = None,
        q: str | None = None,
        applicable_ship_type: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> CatalogRowPage:
        where: list[str] = []
        params: list[Any] = []
        if section_id is not None:
            where.append("r.section_id = %s")
            params.append(section_id)
        if is_active is not None:
            where.append("r.is_active = %s")
            params.append(1 if is_active else 0)
        if q:
            where.append("(r.canonical_code LIKE %s OR r.display_name LIKE %s)")
            params.extend([f"%{q}%", f"%{q}%"])
        if applicable_ship_type:
            where.append(
                "(r.applicable_ship_types LIKE %s OR r.applicable_ship_types LIKE %s)"
            )
            params.extend(['%"all"%', f'%"{applicable_ship_type}"%'])

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        safe_page = max(1, int(page)) if page is not None else None
        safe_page_size = min(max(1, int(page_size)), 100) if page_size is not None else None
        order_sql = "ORDER BY s.sort_order, r.print_order, r.display_name"
        page_sql = ""
        page_params: list[Any] = []
        if safe_page is not None and safe_page_size is not None:
            page_sql = " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            page_params = [(safe_page - 1) * safe_page_size, safe_page_size]

        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM dbo.vims_certs_catalog_row r {where_sql}",
                params,
            )
            count = int(cursor.fetchone()[0])
            cursor.execute(
                _row_select_sql(where_sql) + f" {order_sql}{page_sql}",
                [*params, *page_params],
            )
            return CatalogRowPage(
                count=count,
                page=safe_page,
                page_size=safe_page_size,
                results=_fetch_all(cursor),
            )

    def get_row(self, catalog_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(_row_select_sql("WHERE r.catalog_id = %s"), [catalog_id])
            return _fetch_one(cursor)

    def get_row_by_code(self, canonical_code: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(_row_select_sql("WHERE r.canonical_code = %s"), [canonical_code])
            return _fetch_one(cursor)

    def has_children(self, catalog_id: str) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 1
                FROM dbo.vims_certs_catalog_row
                WHERE parent_id = %s
                """,
                [catalog_id],
            )
            return cursor.fetchone() is not None

    def list_catalog_audit_events(self, catalog_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        bounded_limit = min(max(int(limit), 1), 200)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT TOP {bounded_limit}
                    audit_id, timestamp_utc, vessel_id, actor_user_id, actor_role,
                    action, entity_type, entity_id, before_json, after_json, reason,
                    event_metadata, retention_tier, archived_at, schema_version
                FROM dbo.vims_certs_audit_log
                WHERE entity_type = %s
                  AND entity_id = %s
                  AND action IN (
                    N'create_catalog_row',
                    N'update_catalog_row',
                    N'deprecate_catalog_row',
                    N'bulk_soft_delete',
                    N'hard_purge_catalog_row'
                  )
                ORDER BY timestamp_utc DESC
                """,
                ["catalog_row", str(catalog_id)],
            )
            return _fetch_all(cursor)

    def create_row(self, values: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        data = self._db_payload(values)
        data["created_by"] = actor_id
        data["updated_by"] = actor_id
        columns = tuple(data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(columns)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO dbo.vims_certs_catalog_row ({column_sql})
                OUTPUT inserted.catalog_id
                VALUES ({placeholders})
                """,
                [data[column] for column in columns],
            )
            catalog_id = str(cursor.fetchone()[0])
        return self.get_row(catalog_id) or {}

    def update_row(self, catalog_id: str, values: dict[str, Any], *, actor_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        before = self.get_row(catalog_id)
        if before is None:
            return None, None
        data = self._db_payload(values)
        if not data:
            return before, before
        assignments = [f"{column} = %s" for column in data]
        assignments.extend(["updated_at = SYSUTCDATETIME()", "updated_by = %s"])
        params = [*data.values(), actor_id, catalog_id]
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE dbo.vims_certs_catalog_row SET {', '.join(assignments)} WHERE catalog_id = %s",
                params,
            )
        return before, self.get_row(catalog_id)

    def bulk_soft_delete_rows(self, catalog_ids: list[str], *, actor_id: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        results: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for catalog_id in catalog_ids:
            before, after = self.update_row(catalog_id, {"isActive": False}, actor_id=actor_id)
            if before is not None and after is not None:
                results.append((before, after))
        return results

    def delete_row(self, catalog_id: str) -> dict[str, Any] | None:
        before = self.get_row(catalog_id)
        if before is None:
            return None
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM dbo.vims_certs_catalog_row WHERE catalog_id = %s",
                [catalog_id],
            )
        return before

    def _db_payload(self, values: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for api_key, value in values.items():
            column = CAMEL_TO_COLUMN.get(api_key)
            if column not in CATALOG_COLUMNS:
                continue
            payload[column] = _db_value(column, value)
        return payload
