from __future__ import annotations

import json
import re
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


DEFAULT_ACTOR_ID = "seed_vessel_certs_register"
DEFAULT_REASON = (
    "Phase 9.1 cutover pending-first-upload rows created per Prince/DPA approval; "
    "certificate PDFs to be uploaded after go-live."
)


class Command(BaseCommand):
    help = "Create an idempotent pending-first-upload Certs register for one vessel from the active catalog."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--vessel", required=True, help="VesselData id, IMO number, vessel code, or vessel name.")
        parser.add_argument("--ship-type", default="all", help="Certs ship type to store on vessel config. Default: all.")
        parser.add_argument("--actor-id", default=DEFAULT_ACTOR_ID, help="Actor id stored in created_by/updated_by/audit.")
        parser.add_argument("--reason", default=DEFAULT_REASON, help="Audit/config reason for the cutover seed.")
        parser.add_argument("--apply", action="store_true", help="Persist changes. Omit for dry-run.")

    def handle(self, *args, **options):
        vessel_identifier = str(options["vessel"]).strip()
        if not vessel_identifier:
            raise CommandError("--vessel cannot be blank.")

        actor_id = str(options["actor_id"]).strip()[:64] or DEFAULT_ACTOR_ID
        ship_type = str(options["ship_type"]).strip()[:32] or "all"
        reason = str(options["reason"]).strip() or DEFAULT_REASON
        apply_changes = bool(options["apply"])

        with transaction.atomic():
            with connection.cursor() as cursor:
                _assert_tables(cursor)
                vessel = _resolve_vessel(cursor, vessel_identifier)
                if vessel is None:
                    raise CommandError(f"Vessel not found for identifier: {vessel_identifier}")

                vessel_id = str(vessel["vessel_id"])
                active_catalog_count = _active_catalog_count(cursor)
                existing_count = _existing_tracked_count(cursor, vessel_id)
                missing_rows = _missing_catalog_rows(cursor, vessel_id)

                if not apply_changes:
                    self.stdout.write(
                        self.style.WARNING(
                            "Dry run only. "
                            f"Vessel {vessel['vessel_name']} ({vessel_id}) has {existing_count} tracked row(s). "
                            f"Would create {len(missing_rows)} missing row(s) from {active_catalog_count} active catalog row(s)."
                        )
                    )
                    return

                config_created = _ensure_vessel_config(
                    cursor,
                    vessel_id=vessel_id,
                    ship_type=ship_type,
                    actor_id=actor_id,
                    reason=reason,
                )
                created_count = _create_missing_tracked_items(
                    cursor,
                    vessel_id=vessel_id,
                    missing_rows=missing_rows,
                    actor_id=actor_id,
                )
                _record_seed_audit(
                    cursor,
                    vessel_id=vessel_id,
                    actor_id=actor_id,
                    reason=reason,
                    vessel=vessel,
                    active_catalog_count=active_catalog_count,
                    existing_count=existing_count,
                    created_count=created_count,
                    config_created=config_created,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded Certs register for {vessel['vessel_name']} ({vessel_id}). "
                f"Created {created_count} tracked row(s); existing tracked row(s) before seed: {existing_count}; "
                f"config {'created' if config_created else 'already existed/updated'}."
            )
        )


def _assert_tables(cursor) -> None:
    cursor.execute(
        """
        IF OBJECT_ID(N'dbo.vims_certs_catalog_row', N'U') IS NULL
        BEGIN
            THROW 51000, 'dbo.vims_certs_catalog_row does not exist. Run certs migrations first.', 1;
        END
        IF OBJECT_ID(N'dbo.vims_certs_tracked_item', N'U') IS NULL
        BEGIN
            THROW 51000, 'dbo.vims_certs_tracked_item does not exist. Run certs migrations first.', 1;
        END
        IF OBJECT_ID(N'dbo.vims_certs_vessel_config', N'U') IS NULL
        BEGIN
            THROW 51000, 'dbo.vims_certs_vessel_config does not exist. Run certs migrations first.', 1;
        END
        IF OBJECT_ID(N'dbo.vims_certs_audit_log', N'U') IS NULL
        BEGIN
            THROW 51000, 'dbo.vims_certs_audit_log does not exist. Run certs migrations first.', 1;
        END
        """
    )


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _resolve_vessel(cursor, vessel_identifier: str) -> dict[str, Any] | None:
    like_identifier = f"%{vessel_identifier}%"
    cursor.execute(
        """
        SELECT TOP 1
            CAST(id AS VARCHAR(64)) AS vessel_id,
            vesselName AS vessel_name,
            vesselCode AS vessel_code,
            imoNumber AS imo_number
        FROM dbo.VesselData
        WHERE (
                CAST(id AS VARCHAR(64)) = %s
             OR imoNumber = %s
             OR vesselCode = %s
             OR vesselName = %s
             OR vesselName LIKE %s
        )
          AND ISNULL(is_deleted, 0) = 0
        ORDER BY
            CASE
                WHEN CAST(id AS VARCHAR(64)) = %s THEN 0
                WHEN imoNumber = %s THEN 1
                WHEN vesselCode = %s THEN 2
                WHEN vesselName = %s THEN 3
                ELSE 4
            END,
            vesselName
        """,
        [
            vessel_identifier,
            vessel_identifier,
            vessel_identifier,
            vessel_identifier,
            like_identifier,
            vessel_identifier,
            vessel_identifier,
            vessel_identifier,
            vessel_identifier,
        ],
    )
    return _fetch_one(cursor)


def _active_catalog_count(cursor) -> int:
    cursor.execute("SELECT COUNT(*) FROM dbo.vims_certs_catalog_row WHERE is_active = 1")
    return int(cursor.fetchone()[0])


def _existing_tracked_count(cursor, vessel_id: str) -> int:
    cursor.execute("SELECT COUNT(*) FROM dbo.vims_certs_tracked_item WHERE vessel_id = %s", [vessel_id])
    return int(cursor.fetchone()[0])


def _missing_catalog_rows(cursor, vessel_id: str) -> list[dict[str, Any]]:
    cursor.execute(
        """
        SELECT
            CAST(c.catalog_id AS VARCHAR(64)) AS catalog_id,
            c.canonical_code,
            c.display_name,
            c.validity_type,
            c.cadence_months,
            c.cadence_custom_days,
            c.issuing_authority_type
        FROM dbo.vims_certs_catalog_row c
        WHERE c.is_active = 1
          AND NOT EXISTS (
              SELECT 1
              FROM dbo.vims_certs_tracked_item t
              WHERE t.vessel_id = %s
                AND t.catalog_id = c.catalog_id
          )
        ORDER BY c.print_order, c.display_name
        """,
        [vessel_id],
    )
    return _fetch_all(cursor)


def _ensure_vessel_config(cursor, *, vessel_id: str, ship_type: str, actor_id: str, reason: str) -> bool:
    cursor.execute("SELECT COUNT(*) FROM dbo.vims_certs_vessel_config WHERE vessel_id = %s", [vessel_id])
    exists = int(cursor.fetchone()[0]) > 0
    if exists:
        cursor.execute(
            """
            UPDATE dbo.vims_certs_vessel_config
            SET lifecycle_status = N'active',
                ship_type = COALESCE(NULLIF(ship_type, N''), %s),
                mandatory_coverage_override_reason = COALESCE(mandatory_coverage_override_reason, %s),
                mandatory_coverage_override_at = COALESCE(mandatory_coverage_override_at, SYSUTCDATETIME()),
                mandatory_coverage_override_by = COALESCE(mandatory_coverage_override_by, %s),
                updated_at = SYSUTCDATETIME(),
                updated_by = %s
            WHERE vessel_id = %s
            """,
            [ship_type, reason, actor_id, actor_id, vessel_id],
        )
        return False

    cursor.execute(
        """
        INSERT INTO dbo.vims_certs_vessel_config (
            vessel_id, ship_type, lifecycle_status,
            mandatory_coverage_override_reason, mandatory_coverage_override_at,
            mandatory_coverage_override_by, updated_by
        )
        VALUES (%s, %s, N'active', %s, SYSUTCDATETIME(), %s, %s)
        """,
        [vessel_id, ship_type, reason, actor_id, actor_id],
    )
    return True


def _create_missing_tracked_items(cursor, *, vessel_id: str, missing_rows: list[dict[str, Any]], actor_id: str) -> int:
    created_count = 0
    for row in missing_rows:
        cursor.execute(
            """
            INSERT INTO dbo.vims_certs_tracked_item (
                vessel_id, catalog_id, type, validity_type,
                cadence_months, cadence_custom_days,
                status, issuing_authority, pdf_missing, source,
                approval_state, approved_by, approved_at,
                lifecycle_status, created_by, updated_by
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s,
                N'pending_first_upload', %s, 1, N'migration',
                N'approved', %s, SYSUTCDATETIME(),
                N'active', %s, %s
            )
            """,
            [
                vessel_id,
                row["catalog_id"],
                _infer_tracked_type(row),
                row["validity_type"],
                row["cadence_months"],
                row["cadence_custom_days"],
                str(row["issuing_authority_type"] or "company").title(),
                actor_id,
                actor_id,
                actor_id,
            ],
        )
        created_count += 1
    return created_count


def _infer_tracked_type(row: dict[str, Any]) -> str:
    text = f"{row.get('canonical_code') or ''} {row.get('display_name') or ''}".lower()
    checks = (
        ("calibration", "calibration"),
        ("hydrostatic", "test"),
        ("pressure test", "test"),
        (" test", "test"),
        ("service", "service"),
        ("servicing", "service"),
        ("survey", "endorsement_survey"),
        ("endorsement", "endorsement_survey"),
        ("type approval", "type_approval"),
        ("approved plan", "plan_approval"),
        ("plan approval", "plan_approval"),
    )
    for needle, tracked_type in checks:
        if needle in text:
            return tracked_type
    if re.search(r"\btest\b", text):
        return "test"
    return "certificate"


def _record_seed_audit(
    cursor,
    *,
    vessel_id: str,
    actor_id: str,
    reason: str,
    vessel: dict[str, Any],
    active_catalog_count: int,
    existing_count: int,
    created_count: int,
    config_created: bool,
) -> None:
    after = {
        "vessel": vessel,
        "activeCatalogRows": active_catalog_count,
        "existingTrackedRowsBeforeSeed": existing_count,
        "createdTrackedRows": created_count,
        "configCreated": config_created,
    }
    cursor.execute(
        """
        INSERT INTO dbo.vims_certs_audit_log (
            vessel_id, actor_user_id, actor_role, action, entity_type, entity_id,
            before_json, after_json, reason, event_metadata
        )
        VALUES (%s, %s, N'SYSTEM', N'create_tracked_item', N'vessel_config', %s, NULL, %s, %s, %s)
        """,
        [
            vessel_id,
            actor_id,
            vessel_id,
            json.dumps(after, default=str),
            reason,
            json.dumps({"source": "manage.seed_vessel_certs_register"}, default=str),
        ],
    )
