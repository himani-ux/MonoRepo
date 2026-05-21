from __future__ import annotations

from django.utils import timezone

from apps.safety.repositories.base import BaseRepository
from apps.safety.services.soi_compliance_calculator import SOI_COMPLIANCE_LABEL, SOIComplianceCalculator


class DashboardSOIComplianceService:
    def __init__(
        self,
        *,
        repository: BaseRepository | None = None,
        compliance_calculator: SOIComplianceCalculator | None = None,
    ) -> None:
        self.repository = repository or BaseRepository()
        self.compliance_calculator = compliance_calculator or SOIComplianceCalculator(
            repository=self.repository,
        )

    def build_panel(self, *, vessel_id: str | None) -> dict[str, object]:
        normalized_vessel_id = str(vessel_id).strip() if vessel_id not in (None, "") else ""
        current_summary = (
            self.compliance_calculator.get_summary(normalized_vessel_id)
            if normalized_vessel_id
            else self._empty_summary()
        )

        return {
            "label": SOI_COMPLIANCE_LABEL,
            "current_vessel": {
                "applicable_area_count": int(current_summary.get("applicable_area_count") or 0),
                "compliance_percent": current_summary.get("compliance_percent"),
                "display_value": current_summary.get("display_value") or "N/A - awaiting first cycle",
                "inspected_area_count": int(current_summary.get("inspected_area_count") or 0),
                "overdue_area_count": int(current_summary.get("overdue_area_count") or 0),
                "status": current_summary.get("status") or "NA",
                "vessel_id": normalized_vessel_id,
            },
            "fleet_average": self._build_fleet_average(),
        }

    def _build_fleet_average(self) -> dict[str, object]:
        compliance_values: list[int] = []
        for vessel_id in self._list_fleet_vessel_ids():
            summary = self.compliance_calculator.get_summary(vessel_id)
            compliance_percent = summary.get("compliance_percent")
            if isinstance(compliance_percent, int):
                compliance_values.append(compliance_percent)

        vessel_count = len(compliance_values)
        if vessel_count == 0:
            return {
                "compliance_percent": None,
                "display_value": "N/A - awaiting first cycle",
                "note": "Awaiting the first completed SOI cycle across the fleet.",
                "vessel_count": 0,
            }

        compliance_percent = round(sum(compliance_values) / vessel_count)
        vessel_label = "vessel" if vessel_count == 1 else "vessels"
        return {
            "compliance_percent": compliance_percent,
            "display_value": f"{compliance_percent}%",
            "note": f"Average across {vessel_count} {vessel_label} with completed SOI cycles.",
            "vessel_count": vessel_count,
        }

    def _list_fleet_vessel_ids(self) -> list[str]:
        rows = self.repository.execute_query(
            """
            SELECT DISTINCT vessel_id
            FROM (
                SELECT vessel_id
                FROM vims_safety_soi_vessel_area_map
                WHERE vessel_id IS NOT NULL
                  AND vessel_id <> ''
                UNION
                SELECT vessel_id
                FROM vims_safety_soi_inspection
                WHERE vessel_id IS NOT NULL
                  AND vessel_id <> ''
            ) AS fleet_vessels
            ORDER BY vessel_id ASC
            """,
            [],
        )
        return [str(row["vessel_id"]).strip() for row in rows if row.get("vessel_id") not in (None, "")]

    def _empty_summary(self) -> dict[str, object]:
        return {
            "applicable_area_count": 0,
            "calculated_at": timezone.now().isoformat(),
            "compliance_percent": None,
            "display_value": "N/A - awaiting first cycle",
            "inspected_area_count": 0,
            "label": SOI_COMPLIANCE_LABEL,
            "overdue_area_count": 0,
            "status": "NA",
            "vessel_id": "",
        }
