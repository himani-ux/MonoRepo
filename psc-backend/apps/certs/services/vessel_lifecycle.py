from __future__ import annotations

import json
from typing import Any

from django.db import connection

from apps.certs.services.audit_log import resolve_actor_id
from apps.certs.services.vessel_dashboard import VesselDashboardRepository


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


class VesselLifecycleRepository:
    def __init__(self, dashboard_repository: VesselDashboardRepository | None = None) -> None:
        self.dashboard_repository = dashboard_repository or VesselDashboardRepository()

    def get_profile(self, vessel_identifier: str) -> dict[str, Any] | None:
        vessel = self.dashboard_repository.resolve_vessel(vessel_identifier)
        if vessel is None:
            return None
        vessel_id = str(vessel["vessel_id"])
        config = self.dashboard_repository.get_vessel_config(vessel_id)
        return {
            "vessel": vessel,
            "before": config,
            "after": config,
            "affected_tracked_items": 0,
            "artifact": None,
        }

    def record_flag_change(self, *, vessel_identifier: str, values: dict[str, Any], actor) -> dict[str, Any] | None:
        profile = self.get_profile(vessel_identifier)
        if profile is None:
            return None
        vessel = profile["vessel"]
        vessel_id = str(vessel["vessel_id"])
        before = self.dashboard_repository.get_vessel_config(vessel_id)
        event_payload = {
            "previousFlagState": vessel.get("flag"),
            "newFlagState": values.get("newFlagState"),
            "effectiveDate": values.get("effectiveDate"),
            "reason": values.get("reason"),
            "recordedBy": resolve_actor_id(actor),
        }
        self.ensure_config(vessel_id=vessel_id, actor_id=resolve_actor_id(actor))
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_vessel_config
                SET flag_change_pending = 1,
                    flag_change_event_json = %s,
                    lifecycle_status = CASE
                        WHEN lifecycle_status IN ('pending_disposal', 'sold_pending_handover') THEN lifecycle_status
                        ELSE 'active'
                    END,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                """,
                [json.dumps(event_payload, default=str), resolve_actor_id(actor), vessel_id],
            )
        affected = self.mark_statutory_invalid_due_to_reflag(vessel_id=vessel_id, actor_id=resolve_actor_id(actor))
        after = self.dashboard_repository.get_vessel_config(vessel_id)
        return {**profile, "before": before, "after": after, "affected_tracked_items": affected}

    def record_class_change(self, *, vessel_identifier: str, values: dict[str, Any], actor) -> dict[str, Any] | None:
        profile = self.get_profile(vessel_identifier)
        if profile is None:
            return None
        vessel = profile["vessel"]
        vessel_id = str(vessel["vessel_id"])
        before = self.dashboard_repository.get_vessel_config(vessel_id)
        event_payload = {
            "previousClassSociety": vessel.get("class_society"),
            "newClassSociety": values.get("newClassSociety"),
            "effectiveDate": values.get("effectiveDate"),
            "reason": values.get("reason"),
            "recordedBy": resolve_actor_id(actor),
        }
        self.ensure_config(vessel_id=vessel_id, actor_id=resolve_actor_id(actor))
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_vessel_config
                SET class_change_pending = 1,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                """,
                [resolve_actor_id(actor), vessel_id],
            )
        affected = self.mark_class_rows_pending_supersession(vessel_id=vessel_id, actor_id=resolve_actor_id(actor))
        after = self.dashboard_repository.get_vessel_config(vessel_id) or {}
        after = {**after, "class_change_event": event_payload}
        return {**profile, "before": before, "after": after, "affected_tracked_items": affected}

    def record_sale_handover(
        self,
        *,
        vessel_identifier: str,
        values: dict[str, Any],
        actor,
        artifact: dict[str, Any],
    ) -> dict[str, Any] | None:
        profile = self.get_profile(vessel_identifier)
        if profile is None:
            return None
        vessel_id = str(profile["vessel"]["vessel_id"])
        before = self.dashboard_repository.get_vessel_config(vessel_id)
        actor_id = resolve_actor_id(actor)
        bundle_blob_id = artifact.get("bundle_zip_blob_id")
        self.ensure_config(vessel_id=vessel_id, actor_id=actor_id)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_vessel_config
                SET lifecycle_status = 'sold_pending_handover',
                    sale_handover_bundle_blob_id = %s,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                """,
                [bundle_blob_id, actor_id, vessel_id],
            )
        affected = self.lock_in_flight_submissions_for_sale(vessel_id=vessel_id, actor_id=actor_id)
        after = self.dashboard_repository.get_vessel_config(vessel_id)
        return {**profile, "before": before, "after": after, "affected_tracked_items": affected, "artifact": artifact}

    def record_decommission(self, *, vessel_identifier: str, values: dict[str, Any], actor) -> dict[str, Any] | None:
        profile = self.get_profile(vessel_identifier)
        if profile is None:
            return None
        vessel_id = str(profile["vessel"]["vessel_id"])
        before = self.dashboard_repository.get_vessel_config(vessel_id)
        actor_id = resolve_actor_id(actor)
        self.ensure_config(vessel_id=vessel_id, actor_id=actor_id)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_vessel_config
                SET lifecycle_status = 'pending_disposal',
                    pending_disposal_started_at = COALESCE(pending_disposal_started_at, SYSUTCDATETIME()),
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                """,
                [actor_id, vessel_id],
            )
        affected = self.mark_vessel_items_pending_disposal(vessel_id=vessel_id, actor_id=actor_id)
        after = self.dashboard_repository.get_vessel_config(vessel_id)
        return {**profile, "before": before, "after": after, "affected_tracked_items": affected}

    def ensure_config(self, *, vessel_id: str, actor_id: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute("SELECT vessel_id FROM dbo.vims_certs_vessel_config WHERE vessel_id = %s", [vessel_id])
            if cursor.fetchone():
                return
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_vessel_config (
                    vessel_id, lifecycle_status, created_by, updated_by
                )
                VALUES (%s, 'active', %s, %s)
                """,
                [vessel_id, actor_id, actor_id],
            )

    def list_bundle_tracked_item_ids(self, *, vessel_id: str) -> list[str]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT t.tracked_item_id
                FROM dbo.vims_certs_tracked_item t
                WHERE t.vessel_id = %s
                  AND t.lifecycle_status = 'active'
                  AND t.pdf_attachment_id IS NOT NULL
                ORDER BY t.updated_at DESC, t.tracked_item_id
                """,
                [vessel_id],
            )
            return [str(row["tracked_item_id"]) for row in _fetch_all(cursor)]

    def mark_statutory_invalid_due_to_reflag(self, *, vessel_id: str, actor_id: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE t
                SET status = 'invalid_due_to_reflag',
                    lifecycle_status = 'invalid_due_to_reflag',
                    version = version + 1,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                FROM dbo.vims_certs_tracked_item t
                INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
                INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = c.section_id
                WHERE t.vessel_id = %s
                  AND t.lifecycle_status = 'active'
                  AND s.section_code = 'STATUTORY'
                  AND ISNULL(c.is_class_tracked, 0) = 0
                """,
                [actor_id, vessel_id],
            )
            cursor.execute("SELECT @@ROWCOUNT")
            return int((cursor.fetchone() or [0])[0] or 0)

    def mark_class_rows_pending_supersession(self, *, vessel_id: str, actor_id: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE t
                SET status = 'pending_supersession',
                    lifecycle_status = 'pending_supersession',
                    version = version + 1,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                FROM dbo.vims_certs_tracked_item t
                INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
                INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = c.section_id
                WHERE t.vessel_id = %s
                  AND t.lifecycle_status = 'active'
                  AND (ISNULL(c.is_class_tracked, 0) = 1 OR s.section_code = 'CLASS')
                """,
                [actor_id, vessel_id],
            )
            cursor.execute("SELECT @@ROWCOUNT")
            return int((cursor.fetchone() or [0])[0] or 0)

    def lock_in_flight_submissions_for_sale(self, *, vessel_id: str, actor_id: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_tracked_item
                SET lifecycle_status = 'pending_disposal',
                    version = version + 1,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                  AND lifecycle_status = 'active'
                  AND approval_state IN ('draft', 'pending_master_approval', 'rejected')
                """,
                [actor_id, vessel_id],
            )
            cursor.execute("SELECT @@ROWCOUNT")
            return int((cursor.fetchone() or [0])[0] or 0)

    def mark_vessel_items_pending_disposal(self, *, vessel_id: str, actor_id: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_tracked_item
                SET lifecycle_status = 'pending_disposal',
                    version = version + 1,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                  AND lifecycle_status <> 'pending_disposal'
                """,
                [actor_id, vessel_id],
            )
            cursor.execute("SELECT @@ROWCOUNT")
            return int((cursor.fetchone() or [0])[0] or 0)
