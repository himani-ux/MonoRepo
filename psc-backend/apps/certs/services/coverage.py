from __future__ import annotations

import json
from typing import Any

from django.db import connection


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class MandatoryCoverageRepository:
    def list_mandatory_catalog_rows(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CAST(r.catalog_id AS VARCHAR(64)) AS catalog_id,
                    r.canonical_code,
                    r.display_name,
                    r.short_name,
                    r.section_id,
                    s.section_code,
                    s.display_name AS section_name,
                    r.applicable_ship_types,
                    r.applicability_mode,
                    r.specific_vessel_ids,
                    r.print_order,
                    r.mandatory_for_all_vessels,
                    r.is_active
                FROM dbo.vims_certs_catalog_row r
                INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = r.section_id
                WHERE r.is_active = 1
                  AND r.mandatory_for_all_vessels = 1
                ORDER BY s.sort_order, r.print_order, r.display_name
                """
            )
            return _fetch_all(cursor)

    def list_mandatory_tracked_rows(self, vessel_id: str) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CAST(t.tracked_item_id AS VARCHAR(64)) AS tracked_item_id,
                    CAST(t.catalog_id AS VARCHAR(64)) AS catalog_id,
                    t.status,
                    t.lifecycle_status,
                    t.pdf_missing,
                    c.canonical_code,
                    c.display_name,
                    c.short_name,
                    c.section_id,
                    s.section_code,
                    s.display_name AS section_name
                FROM dbo.vims_certs_tracked_item t
                INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
                INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = c.section_id
                WHERE t.vessel_id = %s
                  AND c.is_active = 1
                  AND c.mandatory_for_all_vessels = 1
                ORDER BY s.sort_order, c.print_order, c.display_name
                """,
                [vessel_id],
            )
            return _fetch_all(cursor)


def compute_mandatory_coverage(
    *,
    vessel_id: str,
    ship_type: str | None,
    config: dict[str, Any] | None = None,
    repository: MandatoryCoverageRepository | None = None,
) -> dict[str, Any]:
    repo = repository or MandatoryCoverageRepository()
    return compute_mandatory_coverage_from_rows(
        vessel_id=vessel_id,
        ship_type=ship_type,
        catalog_rows=repo.list_mandatory_catalog_rows(),
        tracked_rows=repo.list_mandatory_tracked_rows(vessel_id),
        config=config,
    )


def compute_mandatory_coverage_from_rows(
    *,
    vessel_id: str,
    ship_type: str | None,
    catalog_rows: list[dict[str, Any]],
    tracked_rows: list[dict[str, Any]],
    config: dict[str, Any] | None,
) -> dict[str, Any]:
    applicable_catalog_rows = [
        row for row in catalog_rows
        if _is_catalog_applicable(row, vessel_id=vessel_id, ship_type=ship_type)
    ]
    tracked_by_catalog = _tracked_rows_by_catalog(tracked_rows)
    covered_count = 0
    missing: list[dict[str, Any]] = []

    for catalog_row in applicable_catalog_rows:
        catalog_id = str(catalog_row.get("catalog_id") or "")
        tracked_for_catalog = tracked_by_catalog.get(catalog_id, [])
        covered = next((row for row in tracked_for_catalog if _is_tracked_row_covered(row)), None)
        if covered:
            covered_count += 1
            continue
        missing.append(_missing_entry(catalog_row, tracked_for_catalog[0] if tracked_for_catalog else None))

    mandatory_count = len(applicable_catalog_rows)
    percent = 100.0 if mandatory_count == 0 else round((covered_count / mandatory_count) * 100, 1)
    config = config or {}
    override_reason = config.get("mandatory_coverage_override_reason")
    return {
        "percent": percent,
        "mandatoryCount": mandatory_count,
        "coveredCount": covered_count,
        "missing": missing,
        "overrideActive": bool(override_reason and percent < 100),
        "overrideReason": override_reason,
        "overrideAt": config.get("mandatory_coverage_override_at"),
        "overrideBy": config.get("mandatory_coverage_override_by"),
    }


def _tracked_rows_by_catalog(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        catalog_id = str(row.get("catalog_id") or "")
        if catalog_id:
            grouped.setdefault(catalog_id, []).append(row)
    return grouped


def _is_tracked_row_covered(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "")
    lifecycle = str(row.get("lifecycle_status") or "active")
    return status not in {"pending_first_upload", "superseded"} and lifecycle != "onboarding_quarantine"


def _is_catalog_applicable(row: dict[str, Any], *, vessel_id: str, ship_type: str | None) -> bool:
    if not bool(row.get("mandatory_for_all_vessels", True)) or not bool(row.get("is_active", True)):
        return False
    mode = str(row.get("applicability_mode") or "all_matching_type")
    if mode == "specific_vessel_ids":
        return _normalized(vessel_id) in {_normalized(item) for item in _json_list(row.get("specific_vessel_ids"))}
    applicable_ship_types = {_normalized(item) for item in _json_list(row.get("applicable_ship_types"))}
    return "all" in applicable_ship_types or _normalized(ship_type) in applicable_ship_types


def _missing_entry(catalog_row: dict[str, Any], tracked_row: dict[str, Any] | None) -> dict[str, Any]:
    reason = "missing_tracked_item" if tracked_row is None else "pending_first_upload"
    return {
        "catalogId": str(catalog_row.get("catalog_id") or ""),
        "catalogCode": catalog_row.get("canonical_code"),
        "displayName": catalog_row.get("display_name"),
        "shortName": catalog_row.get("short_name"),
        "sectionId": catalog_row.get("section_id"),
        "sectionCode": catalog_row.get("section_code"),
        "sectionName": catalog_row.get("section_name"),
        "trackedItemId": str(tracked_row.get("tracked_item_id")) if tracked_row and tracked_row.get("tracked_item_id") else None,
        "status": tracked_row.get("status") if tracked_row else None,
        "reason": reason,
    }


def _json_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower()
