from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from django.db import connection

from apps.certs.serializers.tracked_item import serialize_tracked_item
from apps.certs.services.coverage import compute_mandatory_coverage
from apps.certs.services.print_artifacts import (
    PRINT_SOFT_THROTTLE_THRESHOLD_PER_HOUR,
    PRINT_SOFT_THROTTLE_WINDOW_MINUTES,
)
from apps.certs.services.tracked_item_repository import TrackedItemRepository
from apps.certs.jobs.cadence_heartbeat import get_last_cadence_heartbeat, serialize_utc


ACTION_ITEM_STATUSES = {
    "overdue",
    "expired",
    "window_open",
    "window_closing",
    "pending_first_upload",
    "expired_at_onboarding",
    "invalid_due_to_reflag",
    "pending_supersession",
}
VALIDITY_SHORT_CODES = {
    "annual": "A",
    "biennial": "Bi-A",
    "full": "5-Y",
    "five_year": "5-Y",
    "ten_year": "10-Y",
    "permanent": "Perm.",
    "short_term": "ST",
    "six_month": "6-Mth",
    "conditional": "ST",
}


@dataclass(frozen=True)
class VesselDashboardData:
    vessel: dict[str, Any]
    config: dict[str, Any] | None
    last_snapshot: dict[str, Any] | None
    sections: list[dict[str, Any]]
    items: list[dict[str, Any]]
    mandatory_coverage: dict[str, Any] | None = None


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    rows = _fetch_all(cursor)
    return rows[0] if rows else None


class VesselDashboardRepository:
    def __init__(self, tracked_items: TrackedItemRepository | None = None) -> None:
        self.tracked_items = tracked_items or TrackedItemRepository()

    def get_dashboard(self, vessel_identifier: str) -> VesselDashboardData | None:
        vessel = self.resolve_vessel(vessel_identifier)
        if vessel is None:
            return None
        vessel_id = str(vessel["vessel_id"])
        config = self.get_vessel_config(vessel_id)
        current_master = self.get_current_master(vessel_id)
        vessel = {**vessel, "current_master": current_master}
        return VesselDashboardData(
            vessel=vessel,
            config=config,
            last_snapshot=self.get_last_snapshot(vessel_id),
            sections=self.list_sections(),
            items=self.tracked_items.list_items(vessel_id=vessel_id).results,
            mandatory_coverage=compute_mandatory_coverage(
                vessel_id=vessel_id,
                ship_type=(config or {}).get("ship_type"),
                config=config,
            ),
        )

    def resolve_vessel(self, vessel_identifier: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    CAST(id AS VARCHAR(64)) AS vessel_id,
                    vesselCode AS vessel_code,
                    vesselName AS vessel_name,
                    imoNumber AS imo_number,
                    flags AS flag,
                    ClassificationSociety AS class_society
                FROM dbo.VesselData
                WHERE (CAST(id AS VARCHAR(64)) = %s OR imoNumber = %s OR vesselCode = %s)
                  AND ISNULL(is_deleted, 0) = 0
                ORDER BY CASE WHEN imoNumber = %s THEN 0 ELSE 1 END
                """,
                [vessel_identifier, vessel_identifier, vessel_identifier, vessel_identifier],
            )
            return _fetch_one(cursor)

    def get_current_master(self, vessel_id: str) -> str | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    h.CrewID,
                    h.first_name,
                    h.surname,
                    fcl.CrewName,
                    r.rank_name
                FROM dbo.Crew_Onboarding_History coh
                INNER JOIN dbo.HRM501 h
                    ON h.CrewID = coh.CrewID
                   AND ISNULL(h.is_deleted, 0) = 0
                   AND ISNULL(h.is_active, 1) = 1
                LEFT JOIN dbo.Final_crew_list fcl
                    ON fcl.CrewID = coh.CrewID
                   AND ISNULL(fcl.is_delete, 0) = 0
                   AND ISNULL(fcl.is_active, 1) = 1
                LEFT JOIN dbo.master_applied_rank r
                    ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
                   AND ISNULL(r.is_deleted, 0) = 0
                   AND ISNULL(r.is_active, 1) = 1
                WHERE coh.Vessel = CAST(%s AS uniqueidentifier)
                  AND coh.SignOffDate IS NULL
                  AND ISNULL(coh.is_active, 1) = 1
                  AND ISNULL(coh.is_deleted, 0) = 0
                  AND UPPER(LTRIM(RTRIM(COALESCE(r.rank_name, h.rank_name, '')))) IN (N'MASTER', N'CAPTAIN')
                ORDER BY coh.SignOnDate DESC
                """,
                [vessel_id],
            )
            row = cursor.fetchone()
        if not row:
            return None
        crew_id, first_name, surname, crew_name, rank_name = row
        full_name = f"{first_name or ''} {surname or ''}".strip() or str(crew_name or "").strip() or str(crew_id or "").strip()
        rank = str(rank_name or "MASTER").strip()
        return f"{rank} - {full_name}".strip(" -")

    def get_vessel_config(self, vessel_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    vessel_id, anniversary_date, ship_type, lifecycle_status,
                    pending_disposal_started_at, sale_handover_bundle_blob_id,
                    flag_change_pending, flag_change_event_json, class_change_pending,
                    mandatory_coverage_override_reason, mandatory_coverage_override_at,
                    mandatory_coverage_override_by, iws_age_gate_disabled
                FROM dbo.vims_certs_vessel_config
                WHERE vessel_id = %s
                """,
                [vessel_id],
            )
            return _fetch_one(cursor)

    def get_last_snapshot(self, vessel_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    snapshot_id, class_society, uploaded_at, parse_status, reconciliation_run_id
                FROM dbo.vims_certs_class_status_snapshot
                WHERE vessel_id = %s
                  AND superseded_user_error = 0
                ORDER BY uploaded_at DESC
                """,
                [vessel_id],
            )
            return _fetch_one(cursor)

    def list_sections(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT section_id, section_code, display_name, sort_order
                FROM dbo.vims_certs_catalog_section
                ORDER BY sort_order, section_id
                """
            )
            return _fetch_all(cursor)


class FleetDashboardRepository:
    notification_meta_table = "vims_certs_notification_meta"

    def _qualified(self, table_name: str) -> str:
        if connection.vendor == "microsoft":
            return f"dbo.{table_name}"
        return table_name

    def get_high_volume_print_activity(self) -> dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(minutes=PRINT_SOFT_THROTTLE_WINDOW_MINUTES)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.user_id,
                    MAX(p.user_role) AS user_role,
                    COUNT(*) AS print_count_last_hour,
                    MAX(p.timestamp_utc) AS last_print_at,
                    MAX(a.timestamp_utc) AS last_signal_at
                FROM dbo.vims_certs_print_artifact p
                LEFT JOIN dbo.vims_certs_audit_log a
                  ON a.actor_user_id = p.user_id
                 AND a.action = 'high_volume_print_activity'
                 AND a.timestamp_utc >= %s
                WHERE p.timestamp_utc >= %s
                GROUP BY p.user_id
                HAVING COUNT(*) > %s
                ORDER BY COUNT(*) DESC, MAX(p.timestamp_utc) DESC
                """,
                [since, since, PRINT_SOFT_THROTTLE_THRESHOLD_PER_HOUR],
            )
            rows = _fetch_all(cursor)
        users = [
            {
                "userId": str(row.get("user_id") or ""),
                "userRole": row.get("user_role") or "",
                "printCountLastHour": int(row.get("print_count_last_hour") or 0),
                "lastPrintAt": row.get("last_print_at"),
                "lastSignalAt": row.get("last_signal_at"),
            }
            for row in rows
        ]
        return {
            "thresholdPerHour": PRINT_SOFT_THROTTLE_THRESHOLD_PER_HOUR,
            "windowMinutes": PRINT_SOFT_THROTTLE_WINDOW_MINUTES,
            "usersAboveThresholdCount": len(users),
            "users": users,
        }

    def get_bouncing_email_delivery(self) -> dict[str, Any]:
        table_names = set(connection.introspection.table_names())
        if self.notification_meta_table not in table_names:
            return {"bouncingUsersCount": 0, "users": []}

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT delivery_status_json, sent_at
                FROM {self._qualified(self.notification_meta_table)}
                WHERE delivery_status_json LIKE %s
                ORDER BY sent_at DESC
                """,
                ['%"bouncing"%'],
            )
            rows = _fetch_all(cursor)

        users_by_id: dict[str, dict[str, Any]] = {}
        for row in rows:
            for entry in _parse_delivery_status(row.get("delivery_status_json")):
                user_id = str(entry.get("userId") or "")
                if not user_id:
                    continue
                channels = entry.get("channels") or []
                has_bouncing_email = any(
                    channel.get("channel") == "email" and channel.get("status") == "bouncing"
                    for channel in channels
                )
                if not has_bouncing_email:
                    continue
                existing = users_by_id.setdefault(
                    user_id,
                    {
                        "userId": user_id,
                        "lastBouncedAt": row.get("sent_at"),
                        "criticalFallbackCount": 0,
                    },
                )
                if row.get("sent_at") and (
                    not existing.get("lastBouncedAt") or row.get("sent_at") > existing.get("lastBouncedAt")
                ):
                    existing["lastBouncedAt"] = row.get("sent_at")
                existing["criticalFallbackCount"] += sum(
                    1
                    for channel in channels
                    if channel.get("channel") == "slack_dm" and channel.get("criticalBounceException")
                )

        users = sorted(
            users_by_id.values(),
            key=lambda user: (user.get("lastBouncedAt") is None, user.get("lastBouncedAt")),
            reverse=True,
        )
        return {
            "bouncingUsersCount": len(users),
            "users": users,
        }

    def get_cadence_heartbeat(self) -> dict[str, Any]:
        return {
            "lastCadenceHeartbeat": serialize_utc(get_last_cadence_heartbeat()),
        }

    def list_onboarded_vessels(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CAST(vc.vessel_id AS VARCHAR(64)) AS vessel_id,
                    vd.vesselName AS vessel_name,
                    vd.vesselCode AS vessel_code,
                    vd.imoNumber AS imo_number,
                    vc.lifecycle_status,
                    COUNT(t.tracked_item_id) AS tracked_item_count,
                    SUM(CASE WHEN t.pdf_missing = 1 THEN 1 ELSE 0 END) AS pdf_missing_count,
                    SUM(CASE
                        WHEN t.status IN (
                            'overdue',
                            'expired',
                            'window_open',
                            'window_closing',
                            'pending_first_upload',
                            'expired_at_onboarding',
                            'invalid_due_to_reflag',
                            'pending_supersession'
                        )
                        OR t.pdf_missing = 1 THEN 1
                        ELSE 0
                    END) AS action_item_count
                FROM dbo.vims_certs_vessel_config vc
                INNER JOIN dbo.VesselData vd
                  ON vd.id = vc.vessel_id
                 AND ISNULL(vd.is_deleted, 0) = 0
                LEFT JOIN dbo.vims_certs_tracked_item t
                  ON t.vessel_id = vc.vessel_id
                 AND t.lifecycle_status = 'active'
                WHERE vc.lifecycle_status = 'active'
                GROUP BY
                    vc.vessel_id,
                    vd.vesselName,
                    vd.vesselCode,
                    vd.imoNumber,
                    vc.lifecycle_status
                ORDER BY vd.vesselName
                """
            )
            rows = _fetch_all(cursor)

        return [
            {
                "id": str(row.get("vessel_id") or ""),
                "name": row.get("vessel_name"),
                "code": row.get("vessel_code"),
                "imo": row.get("imo_number"),
                "lifecycleStatus": row.get("lifecycle_status"),
                "trackedItemCount": int(row.get("tracked_item_count") or 0),
                "actionItemCount": int(row.get("action_item_count") or 0),
                "pdfMissingCount": int(row.get("pdf_missing_count") or 0),
            }
            for row in rows
        ]


def serialize_vessel_dashboard(data: VesselDashboardData) -> dict[str, Any]:
    sections = _serialize_sections(data.sections, data.items)
    coverage = data.mandatory_coverage or compute_mandatory_coverage(
        vessel_id=str(data.vessel.get("vessel_id") or ""),
        ship_type=(data.config or {}).get("ship_type"),
        config=data.config,
    )
    return {
        "vessel": _serialize_vessel(data.vessel, data.config),
        "mandatoryCoverage": coverage,
        "lastClassSnapshot": _serialize_snapshot(data.last_snapshot),
        "sections": sections,
        "summary": {
            "totalTrackedItems": sum(section["activeTrackedItemCount"] for section in sections),
            "actionItemCount": sum(section["actionItemCount"] for section in sections),
            "pdfMissingCount": sum(1 for row in data.items if row.get("pdf_missing")),
            "classTrackedCount": sum(1 for row in data.items if row.get("catalog_is_class_tracked")),
        },
    }


def _serialize_vessel(vessel: dict[str, Any], config: dict[str, Any] | None) -> dict[str, Any]:
    lifecycle_status = (config or {}).get("lifecycle_status") or "not_onboarded"
    return {
        "id": str(vessel.get("vessel_id")),
        "imo": vessel.get("imo_number"),
        "code": vessel.get("vessel_code"),
        "name": vessel.get("vessel_name"),
        "flag": vessel.get("flag"),
        "classSociety": vessel.get("class_society"),
        "shipType": (config or {}).get("ship_type"),
        "currentMaster": vessel.get("current_master"),
        "lifecycleStatus": lifecycle_status,
        "pendingDisposalStartedAt": (config or {}).get("pending_disposal_started_at"),
        "saleHandoverBundleBlobId": str((config or {}).get("sale_handover_bundle_blob_id")) if (config or {}).get("sale_handover_bundle_blob_id") else None,
        "flagChangePending": bool((config or {}).get("flag_change_pending")),
        "flagChangeEvent": _parse_json((config or {}).get("flag_change_event_json")),
        "classChangePending": bool((config or {}).get("class_change_pending")),
        "iwsAgeGateDisabled": bool((config or {}).get("iws_age_gate_disabled")),
    }


def _serialize_snapshot(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    uploaded_at = snapshot.get("uploaded_at")
    return {
        "id": str(snapshot["snapshot_id"]),
        "classSociety": snapshot.get("class_society"),
        "uploadedAt": uploaded_at,
        "daysAgo": _days_ago(uploaded_at),
        "parseStatus": snapshot.get("parse_status"),
        "reconciliationRunId": str(snapshot["reconciliation_run_id"]) if snapshot.get("reconciliation_run_id") else None,
    }


def _parse_json(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _serialize_sections(sections: list[dict[str, Any]], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items_by_section: dict[int, list[dict[str, Any]]] = {}
    for row in items:
        section_id = int(row.get("catalog_section_id") or 0)
        items_by_section.setdefault(section_id, []).append(row)

    serialized_sections: list[dict[str, Any]] = []
    for section in sections:
        section_id = int(section["section_id"])
        section_items = sorted(
            items_by_section.get(section_id, []),
            key=lambda row: (row.get("catalog_print_order") or 0, row.get("catalog_display_name") or ""),
        )
        serialized_items = [_serialize_dashboard_item(row) for row in section_items]
        serialized_sections.append(
            {
                "sectionId": section_id,
                "sectionCode": section.get("section_code"),
                "displayName": section.get("display_name"),
                "activeTrackedItemCount": len(serialized_items),
                "statusBreakdown": _status_breakdown(serialized_items),
                "actionItemCount": sum(1 for item in serialized_items if item["status"] in ACTION_ITEM_STATUSES or item["pdfMissing"]),
                "items": serialized_items,
            }
        )
    return serialized_sections


def _serialize_dashboard_item(row: dict[str, Any]) -> dict[str, Any]:
    item = serialize_tracked_item(row)
    item.update(
        {
            "sectionId": row.get("catalog_section_id"),
            "sectionCode": row.get("catalog_section_code"),
            "sectionName": row.get("catalog_section_name"),
            "displayName": item.get("catalogDisplayName"),
            "shortName": item.get("catalogShortName"),
            "validityShortCode": VALIDITY_SHORT_CODES.get(str(item.get("validityType") or "").lower(), item.get("validityType")),
            "daysToGo": _days_to_go(item.get("nextDueDate") or item.get("expiryDate")),
            "isClassTracked": bool(row.get("catalog_is_class_tracked")),
            "mandatoryForAllVessels": bool(row.get("catalog_mandatory_for_all_vessels")),
        }
    )
    return item


def _status_breakdown(items: list[dict[str, Any]]) -> dict[str, int]:
    breakdown: dict[str, int] = {}
    for item in items:
        status = str(item.get("status") or "unknown")
        breakdown[status] = breakdown.get(status, 0) + 1
    return breakdown


def _days_to_go(value: Any) -> int | None:
    parsed = _parse_date(value)
    if parsed is None:
        return None
    return (parsed - date.today()).days


def _days_ago(value: Any) -> int | None:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return max((datetime.now(timezone.utc) - parsed).days, 0)


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _parse_delivery_status(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []
