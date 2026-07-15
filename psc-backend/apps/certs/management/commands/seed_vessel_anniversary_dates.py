from __future__ import annotations

import json

from django.core.management.base import BaseCommand
from django.db import connection, transaction


ACTOR_ID = "seed_vessel_anniversary:prince_dates"
REASON = "Anniversary due/window dates provided by Prince on 2026-07-06."
ANNIVERSARY_ROWS = (
    ("SFYC ARAYA", "2026-07-29", "2026-04-29", "2026-10-29"),
    ("EAST AYUTTHAYA", "2026-07-11", "2026-04-11", "2026-10-11"),
    ("EAST BANGKOK", "2026-08-24", "2026-05-24", "2026-11-24"),
    ("SF CHALISA", "2027-04-28", "2027-01-28", "2027-07-28"),
    ("SF DARIKA", "2027-01-27", "2026-10-27", "2027-04-27"),
    ("YC FORTITUDE", "2027-03-09", "2026-12-09", "2027-06-09"),
)


class Command(BaseCommand):
    help = "Seed the Prince-provided Phase 9.1 vessel anniversary due/window dates."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--apply", action="store_true", help="Persist changes. Omit for dry-run.")

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])
        results: list[dict[str, object]] = []
        with transaction.atomic():
            with connection.cursor() as cursor:
                for vessel_name, anniversary, window_open, window_close in ANNIVERSARY_ROWS:
                    result = _update_vessel(
                        cursor,
                        vessel_name=vessel_name,
                        anniversary=anniversary,
                        window_open=window_open,
                        window_close=window_close,
                        apply_changes=apply_changes,
                    )
                    results.append(result)
            if not apply_changes:
                transaction.set_rollback(True)

        for result in results:
            self.stdout.write(
                (
                    "Would update" if not apply_changes else "Updated"
                )
                + " "
                + f"{result['vesselName']}: anniversary={result['anniversaryDate']}, "
                + f"window={result['windowOpen']}..{result['windowClose']}, "
                + f"tracked_rows_touched={result['trackedRowsTouched']}"
            )
        if apply_changes:
            self.stdout.write(self.style.SUCCESS("Vessel anniversary dates saved."))
        else:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to save."))


def _fetch_one(cursor) -> tuple | None:
    return cursor.fetchone()


def _update_vessel(
    cursor,
    *,
    vessel_name: str,
    anniversary: str,
    window_open: str,
    window_close: str,
    apply_changes: bool,
) -> dict[str, object]:
    cursor.execute(
        """
        SELECT TOP 1 CAST(id AS VARCHAR(64)), vesselName, vesselCode, imoNumber
        FROM dbo.VesselData
        WHERE vesselName = %s
          AND ISNULL(is_deleted, 0) = 0
          AND ISNULL(is_active, 1) = 1
        """,
        [vessel_name],
    )
    vessel_row = _fetch_one(cursor)
    if not vessel_row:
        raise RuntimeError(f"Active vessel not found: {vessel_name}")

    vessel_id, resolved_name, vessel_code, imo_number = vessel_row
    cursor.execute(
        """
        SELECT anniversary_date, lifecycle_status, ship_type
        FROM dbo.vims_certs_vessel_config
        WHERE vessel_id = %s
        """,
        [vessel_id],
    )
    before_config = _fetch_one(cursor)
    if not before_config:
        raise RuntimeError(f"Certs vessel config not found: {vessel_name}")

    before = {
        "anniversaryDate": str(before_config[0]) if before_config[0] else None,
        "lifecycleStatus": before_config[1],
        "shipType": before_config[2],
    }

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM dbo.vims_certs_tracked_item
        WHERE vessel_id = %s
          AND lifecycle_status = N'active'
        """,
        [vessel_id],
    )
    active_tracked_count = int(cursor.fetchone()[0])

    tracked_rows_touched = active_tracked_count
    if apply_changes:
        cursor.execute(
            """
            UPDATE dbo.vims_certs_vessel_config
            SET anniversary_date = %s,
                lifecycle_status = N'active',
                updated_at = SYSUTCDATETIME(),
                updated_by = %s
            WHERE vessel_id = %s
            """,
            [anniversary, ACTOR_ID, vessel_id],
        )
        if cursor.rowcount != 1:
            raise RuntimeError(f"No vessel config row updated for {vessel_name}")

        cursor.execute(
            """
            UPDATE dbo.vims_certs_tracked_item
            SET anniversary_date = COALESCE(anniversary_date, %s),
                window_open = COALESCE(window_open, %s),
                window_close = COALESCE(window_close, %s),
                next_due_date = COALESCE(next_due_date, %s),
                updated_at = SYSUTCDATETIME(),
                updated_by = %s,
                version = version + 1
            WHERE vessel_id = %s
              AND lifecycle_status = N'active'
            """,
            [anniversary, window_open, window_close, anniversary, ACTOR_ID, vessel_id],
        )
        tracked_rows_touched = int(cursor.rowcount or 0)

        after = {
            "vesselName": resolved_name,
            "vesselCode": vessel_code,
            "imoNumber": imo_number,
            "anniversaryDate": anniversary,
            "windowOpen": window_open,
            "windowClose": window_close,
            "trackedRowsTouched": tracked_rows_touched,
        }
        cursor.execute(
            """
            INSERT INTO dbo.vims_certs_audit_log (
                vessel_id, actor_user_id, actor_role, action, entity_type, entity_id,
                before_json, after_json, reason, event_metadata
            )
            VALUES (%s, %s, N'SYSTEM', N'update_vessel_anniversary', N'vessel_config', %s, %s, %s, %s, %s)
            """,
            [
                vessel_id,
                ACTOR_ID,
                vessel_id,
                json.dumps(before, default=str),
                json.dumps(after, default=str),
                REASON,
                json.dumps({"source": "manual_prince_anniversary_dates_2026_07_06"}, default=str),
            ],
        )

    return {
        "vesselName": resolved_name,
        "anniversaryDate": anniversary,
        "windowOpen": window_open,
        "windowClose": window_close,
        "trackedRowsTouched": tracked_rows_touched,
    }
