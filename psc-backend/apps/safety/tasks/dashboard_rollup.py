from __future__ import annotations

import os

from apps.safety.models.dashboard_rollup import SafetyDashboardRollup
from apps.safety.services.composite_score import CompositeScoreService, RollupScope


DEFAULT_DASHBOARD_ROLLUP_CRON = "0 */6 * * *"


def get_dashboard_rollup_cron() -> str:
    return os.environ.get("SAFETY_DASHBOARD_ROLLUP_CRON", DEFAULT_DASHBOARD_ROLLUP_CRON)


def build_dashboard_rollups(*, period_codes: tuple[str, ...] | None = None) -> list[dict[str, object]]:
    service = CompositeScoreService()
    resolved_period_codes = period_codes or (
        SafetyDashboardRollup.PeriodCode.DAYS_90,
        SafetyDashboardRollup.PeriodCode.MONTHS_12,
        SafetyDashboardRollup.PeriodCode.YEARS_3,
    )
    vessel_ids = service.list_known_vessel_ids()
    payloads: list[dict[str, object]] = []

    for period_code in resolved_period_codes:
        for vessel_id in vessel_ids:
            rollup = service.save_rollup(
                scope=RollupScope(scope_type=SafetyDashboardRollup.ScopeType.VESSEL, scope_id=str(vessel_id)),
                period_code=period_code,
            )
            payloads.append(_serialize_rollup(rollup))

        fleet_rollup = service.save_rollup(
            scope=RollupScope(scope_type=SafetyDashboardRollup.ScopeType.FLEET, scope_id=""),
            period_code=period_code,
        )
        payloads.append(_serialize_rollup(fleet_rollup))

    return payloads


def _serialize_rollup(rollup: SafetyDashboardRollup) -> dict[str, object]:
    return {
        "scope_type": rollup.scope_type,
        "scope_id": rollup.scope_id,
        "period_code": rollup.period_code,
        "composite_score": rollup.composite_score,
        "score_status": rollup.score_status,
        "calculated_at": rollup.calculated_at.isoformat(),
    }
