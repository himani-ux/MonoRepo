from __future__ import annotations

from datetime import datetime, timedelta

from django.utils import timezone

from apps.safety.models import SOIInspection
from apps.safety.repositories.base import BaseRepository
from apps.safety.repositories.cms_repo import CMSRepository


class CrewRotationCoverageService:
    # Step 8.11 finalizes the strict FEAT-SAF-SOI-022 formula:
    # current active crew with >=1 accompaniment in the rolling window / total current active crew.
    def __init__(
        self,
        *,
        repository: BaseRepository | None = None,
        cms_repository: CMSRepository | None = None,
        now_func=timezone.now,
        window_days: int = 365,
    ) -> None:
        self.repository = repository or BaseRepository()
        self.cms_repository = cms_repository or CMSRepository()
        self.now_func = now_func
        self.window_days = int(window_days)

    def get_summary(
        self,
        vessel_id: str,
        *,
        reference_at: datetime | None = None,
        window_days: int | None = None,
    ) -> dict[str, object]:
        current_at = self._coerce_datetime(reference_at or self.now_func())
        effective_window_days = int(window_days or self.window_days)
        window_start = current_at - timedelta(days=effective_window_days)
        current_crew = self.cms_repository.list_current_vessel_crew(
            vessel_id=str(vessel_id),
            active_on=current_at.date(),
        )
        active_crew_ids = [str(row["crew_id"]) for row in current_crew]

        total_active_crew = len(active_crew_ids)

        if active_crew_ids:
            trainee_placeholders = ", ".join(["%s"] * len(active_crew_ids))
            inspection_date_expr, window_start_expr, window_end_expr = self._date_window_sql()
            crew_rows = self.repository.execute_query(
                f"""
                SELECT
                    trainee.crew_id AS crew_id,
                    COUNT(DISTINCT inspection.id) AS inspections_accompanied
                FROM vims_safety_soi_trainee AS trainee
                INNER JOIN vims_safety_soi_inspection AS inspection
                    ON inspection.id = trainee.inspection_id
                WHERE inspection.vessel_id = %s
                  AND inspection.is_deleted = %s
                  AND inspection.state IN (%s, %s)
                  AND trainee.crew_id IN ({trainee_placeholders})
                  AND COALESCE(inspection.closed_at, inspection.reported_at, inspection.planned_date) IS NOT NULL
                  AND {inspection_date_expr} >= {window_start_expr}
                  AND {inspection_date_expr} <= {window_end_expr}
                GROUP BY trainee.crew_id
                ORDER BY COUNT(DISTINCT inspection.id) DESC, trainee.crew_id ASC
                """,
                [
                    str(vessel_id),
                    False,
                    SOIInspection.State.REPORTED,
                    SOIInspection.State.CLOSED,
                    *active_crew_ids,
                    window_start.date(),
                    current_at.date(),
                ],
            )
        else:
            crew_rows = []

        crew_payload = [
            {
                "crew_id": str(row["crew_id"]),
                "inspections_accompanied": int(row["inspections_accompanied"] or 0),
            }
            for row in crew_rows
        ]
        accompanied_crew_count = len(crew_payload)

        if total_active_crew <= 0:
            coverage_percent = None
            display_value = "N/A - no active crew"
        else:
            coverage_percent = int(round((accompanied_crew_count / total_active_crew) * 100))
            display_value = f"{coverage_percent}%"

        return {
            "vessel_id": str(vessel_id),
            "window_days": effective_window_days,
            "window_start": window_start.isoformat(),
            "window_end": current_at.isoformat(),
            "total_active_crew": total_active_crew,
            "accompanied_crew_count": accompanied_crew_count,
            "coverage_percent": coverage_percent,
            "display_value": display_value,
            "crew": crew_payload,
        }

    def _coerce_datetime(self, value: datetime) -> datetime:
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value

    def _date_window_sql(self) -> tuple[str, str, str]:
        value_expr = "COALESCE(inspection.closed_at, inspection.reported_at, inspection.planned_date)"
        if self.repository.connection.vendor == "microsoft":
            return f"CAST({value_expr} AS date)", "%s", "%s"
        return f"DATE({value_expr})", "DATE(%s)", "DATE(%s)"
