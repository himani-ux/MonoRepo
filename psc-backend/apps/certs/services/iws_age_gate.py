from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import json
from typing import Any

from django.db import connection


IWS_CANONICAL_CODE = "CLASS-IWS-SURVEY"
SYSTEM_ACTOR_ROLE = "SYSTEM"
DISABLED_REASON_OVERAGE = "vessel_age_exceeds_gate"


@dataclass(frozen=True)
class VesselAgeGateInput:
    vessel_id: str
    year_built: int | None
    stored_age: int | None


@dataclass(frozen=True)
class IwsAgeGateResult:
    evaluated_count: int
    disabled_count: int
    enabled_count: int
    override_preserved_count: int
    skipped_count: int


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def compute_vessel_age(*, year_built: int | None, stored_age: int | None, today: dt.date) -> int | None:
    if year_built:
        return max(today.year - int(year_built), 0)
    if stored_age is not None:
        return max(int(stored_age), 0)
    return None


class IwsAgeGateRepository:
    def get_iws_catalog_row(self) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 catalog_id, canonical_code, age_gate_max_years
                FROM dbo.vims_certs_catalog_row
                WHERE canonical_code = %s
                  AND is_active = 1
                  AND age_gate_max_years IS NOT NULL
                """,
                [IWS_CANONICAL_CODE],
            )
            return _fetch_one(cursor)

    def list_vessel_age_inputs(self) -> list[VesselAgeGateInput]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id AS vessel_id, YearBuilt AS year_built, Age AS stored_age
                FROM dbo.VesselData
                WHERE id IS NOT NULL
                """
            )
            rows = _fetch_all(cursor)
        return [
            VesselAgeGateInput(
                vessel_id=str(row["vessel_id"]),
                year_built=row.get("year_built"),
                stored_age=row.get("stored_age"),
            )
            for row in rows
        ]

    def get_vessel_config(self, vessel_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    vessel_id, ship_type, lifecycle_status,
                    iws_age_gate_disabled, iws_age_gate_disabled_at,
                    iws_age_gate_disabled_reason, iws_age_gate_last_age_years,
                    iws_age_gate_last_evaluated_at, iws_manual_override_enabled,
                    iws_manual_override_reason, iws_manual_override_by,
                    iws_manual_override_at
                FROM dbo.vims_certs_vessel_config
                WHERE vessel_id = %s
                """,
                [vessel_id],
            )
            return _fetch_one(cursor)

    def upsert_vessel_config(self, *, vessel_id: str, values: dict[str, Any], actor_id: str) -> dict[str, Any]:
        config = self.get_vessel_config(vessel_id)
        if config is None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO dbo.vims_certs_vessel_config (
                        vessel_id, ship_type, lifecycle_status,
                        iws_age_gate_disabled, iws_age_gate_disabled_at,
                        iws_age_gate_disabled_reason, iws_age_gate_last_age_years,
                        iws_age_gate_last_evaluated_at, iws_manual_override_enabled,
                        iws_manual_override_reason, iws_manual_override_by,
                        iws_manual_override_at, created_by, updated_by
                    )
                    VALUES (
                        %s, %s, N'active',
                        %s, %s, %s, %s, SYSUTCDATETIME(), %s,
                        %s, %s, %s, %s, %s
                    )
                    """,
                    [
                        vessel_id,
                        values.get("ship_type", "unknown"),
                        1 if values.get("iws_age_gate_disabled") else 0,
                        values.get("iws_age_gate_disabled_at"),
                        values.get("iws_age_gate_disabled_reason"),
                        values.get("iws_age_gate_last_age_years"),
                        1 if values.get("iws_manual_override_enabled") else 0,
                        values.get("iws_manual_override_reason"),
                        values.get("iws_manual_override_by"),
                        values.get("iws_manual_override_at"),
                        actor_id,
                        actor_id,
                    ],
                )
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE dbo.vims_certs_vessel_config
                    SET
                        iws_age_gate_disabled = %s,
                        iws_age_gate_disabled_at = %s,
                        iws_age_gate_disabled_reason = %s,
                        iws_age_gate_last_age_years = %s,
                        iws_age_gate_last_evaluated_at = SYSUTCDATETIME(),
                        iws_manual_override_enabled = %s,
                        iws_manual_override_reason = %s,
                        iws_manual_override_by = %s,
                        iws_manual_override_at = %s,
                        updated_at = SYSUTCDATETIME(),
                        updated_by = %s
                    WHERE vessel_id = %s
                    """,
                    [
                        1 if values.get("iws_age_gate_disabled") else 0,
                        values.get("iws_age_gate_disabled_at"),
                        values.get("iws_age_gate_disabled_reason"),
                        values.get("iws_age_gate_last_age_years"),
                        1 if values.get("iws_manual_override_enabled") else 0,
                        values.get("iws_manual_override_reason"),
                        values.get("iws_manual_override_by"),
                        values.get("iws_manual_override_at"),
                        actor_id,
                        vessel_id,
                    ],
                )
        return self.get_vessel_config(vessel_id) or {}

    def record_age_gate_audit(
        self,
        *,
        actor_id: str,
        catalog_id: str,
        vessel_id: str,
        before: dict[str, Any] | None,
        after: dict[str, Any],
        reason: str,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_audit_log (
                    vessel_id, actor_user_id, actor_role, action, entity_type, entity_id,
                    before_json, after_json, reason, event_metadata
                )
                VALUES (%s, %s, %s, N'update_catalog_row', N'catalog_row', %s, %s, %s, %s, %s)
                """,
                [
                    vessel_id,
                    actor_id,
                    SYSTEM_ACTOR_ROLE if actor_id == "recompute_iws_age_gate" else "DPA",
                    catalog_id,
                    json.dumps(before, default=str) if before is not None else None,
                    json.dumps(after, default=str),
                    reason,
                    json.dumps(
                        {
                            "source": "iws_age_gate",
                            "vessel_id": vessel_id,
                            "catalog_id": catalog_id,
                        },
                        default=str,
                    ),
                ],
            )


def _bool(value: Any) -> bool:
    return bool(value)


def _state_changed(before: dict[str, Any] | None, after_values: dict[str, Any]) -> bool:
    if before is None:
        return _bool(after_values.get("iws_age_gate_disabled")) or _bool(after_values.get("iws_manual_override_enabled"))
    keys = (
        "iws_age_gate_disabled",
        "iws_age_gate_disabled_reason",
        "iws_manual_override_enabled",
        "iws_manual_override_reason",
    )
    return any(before.get(key) != after_values.get(key) for key in keys)


def recompute_iws_age_gate(
    *,
    repository: IwsAgeGateRepository | None = None,
    actor_id: str = "recompute_iws_age_gate",
    today: dt.date | None = None,
) -> IwsAgeGateResult:
    repo = repository or IwsAgeGateRepository()
    run_date = today or dt.date.today()
    catalog_row = repo.get_iws_catalog_row()
    if catalog_row is None:
        return IwsAgeGateResult(0, 0, 0, 0, 0)

    catalog_id = str(catalog_row["catalog_id"])
    max_years = int(catalog_row["age_gate_max_years"])
    evaluated = disabled = enabled = override_preserved = skipped = 0

    for vessel in repo.list_vessel_age_inputs():
        age_years = compute_vessel_age(year_built=vessel.year_built, stored_age=vessel.stored_age, today=run_date)
        if age_years is None:
            skipped += 1
            continue
        evaluated += 1
        before = repo.get_vessel_config(vessel.vessel_id)
        if before is None:
            skipped += 1
            continue
        manual_override = _bool(before.get("iws_manual_override_enabled"))
        should_disable = age_years > max_years and not manual_override
        if manual_override and age_years > max_years:
            override_preserved += 1

        disabled_at = before.get("iws_age_gate_disabled_at") if should_disable else None
        if should_disable and not before.get("iws_age_gate_disabled_at"):
            disabled_at = run_date.isoformat()
        values = {
            "iws_age_gate_disabled": should_disable,
            "iws_age_gate_disabled_at": disabled_at,
            "iws_age_gate_disabled_reason": DISABLED_REASON_OVERAGE if should_disable else None,
            "iws_age_gate_last_age_years": age_years,
            "iws_manual_override_enabled": manual_override,
            "iws_manual_override_reason": before.get("iws_manual_override_reason"),
            "iws_manual_override_by": before.get("iws_manual_override_by"),
            "iws_manual_override_at": before.get("iws_manual_override_at"),
        }
        if should_disable:
            disabled += 1
        elif before.get("iws_age_gate_disabled"):
            enabled += 1

        after = repo.upsert_vessel_config(vessel_id=vessel.vessel_id, values=values, actor_id=actor_id)
        if _state_changed(before, values):
            repo.record_age_gate_audit(
                actor_id=actor_id,
                catalog_id=catalog_id,
                vessel_id=vessel.vessel_id,
            before=before,
                after=after,
                reason="IWS age-gate recompute",
            )

    return IwsAgeGateResult(evaluated, disabled, enabled, override_preserved, skipped)


def set_iws_manual_override(
    *,
    vessel_id: str,
    enabled: bool,
    reason: str | None,
    actor_id: str,
    repository: IwsAgeGateRepository | None = None,
) -> dict[str, Any]:
    if enabled and not (reason or "").strip():
        raise ValueError("manual override reason is required when enabling IWS override")
    repo = repository or IwsAgeGateRepository()
    catalog_row = repo.get_iws_catalog_row()
    if catalog_row is None:
        raise ValueError("CLASS-IWS-SURVEY catalog row with age gate was not found")

    before = repo.get_vessel_config(vessel_id)
    if before is None:
        raise ValueError("vessel config was not found for IWS manual override")
    values = {
        "iws_age_gate_disabled": False if enabled else before.get("iws_age_gate_disabled", False),
        "iws_age_gate_disabled_at": None if enabled else before.get("iws_age_gate_disabled_at"),
        "iws_age_gate_disabled_reason": None if enabled else before.get("iws_age_gate_disabled_reason"),
        "iws_age_gate_last_age_years": before.get("iws_age_gate_last_age_years"),
        "iws_manual_override_enabled": enabled,
        "iws_manual_override_reason": reason.strip() if enabled and reason else None,
        "iws_manual_override_by": actor_id if enabled else None,
        "iws_manual_override_at": dt.datetime.now(dt.UTC).isoformat() if enabled else None,
    }
    after = repo.upsert_vessel_config(vessel_id=vessel_id, values=values, actor_id=actor_id)
    repo.record_age_gate_audit(
        actor_id=actor_id,
        catalog_id=str(catalog_row["catalog_id"]),
        vessel_id=vessel_id,
        before=before,
        after=after,
        reason="IWS age-gate manual override updated",
    )
    return after
