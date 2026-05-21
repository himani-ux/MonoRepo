from __future__ import annotations

from apps.safety.services.soi_compliance_calculator import SOIComplianceCalculator


def build_soi_compliance_rollup(*, vessel_ids: list[str] | None = None) -> list[dict[str, object]]:
    calculator = SOIComplianceCalculator()
    resolved_vessel_ids = vessel_ids or _list_known_vessel_ids(calculator=calculator)
    return [calculator.get_summary(str(vessel_id)) for vessel_id in resolved_vessel_ids]


def _list_known_vessel_ids(*, calculator: SOIComplianceCalculator) -> list[str]:
    rows = calculator.repository.execute_query(
        """
        SELECT vessel_id
        FROM vims_safety_soi_vessel_area_map
        WHERE vessel_id IS NOT NULL
        UNION
        SELECT vessel_id
        FROM vims_safety_soi_inspection
        WHERE vessel_id IS NOT NULL
        ORDER BY vessel_id ASC
        """,
        [],
    )
    return [str(row["vessel_id"]) for row in rows if row.get("vessel_id") not in (None, "")]
