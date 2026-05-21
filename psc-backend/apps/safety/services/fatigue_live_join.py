from __future__ import annotations

from collections.abc import Sequence

from apps.safety.services.wrh_snapshot_fetcher import WRHSnapshotFetcher


class FatigueLiveJoinService:
    def __init__(self, *, wrh_snapshot_fetcher: WRHSnapshotFetcher | None = None) -> None:
        self.wrh_snapshot_fetcher = wrh_snapshot_fetcher or WRHSnapshotFetcher()

    def fetch(self, *, incident, crew_ids: Sequence[str]) -> dict[str, object]:
        if not crew_ids:
            return {
                "timezone_offset_minutes": None,
                "attendance_rows": [],
                "rest_hour_rows": [],
                "warnings": ["No crew IDs were provided for WRH lookup."],
                "warning_codes": ["missing_data"],
            }

        occurred_at = incident.occurred_at or incident.reported_at
        if occurred_at is None:
            return {
                "timezone_offset_minutes": None,
                "attendance_rows": [],
                "rest_hour_rows": [],
                "warnings": ["Incident time is required for WRH fatigue lookup."],
                "warning_codes": ["missing_data"],
            }

        lookback = self.wrh_snapshot_fetcher.fetch_fatigue_lookback(
            crew_ids=crew_ids,
            reference_date=occurred_at,
            vessel_id=str(incident.vessel_id),
        )

        raw_rows = list(lookback["rows"])
        attendance_rows = [
            {
                "crew_id": row.get("crew_id"),
                "vessel_id": row.get("vessel_id"),
                "work_date_local": row.get("work_date_local"),
                "tz_offset_minutes": row.get("tz_offset_minutes"),
                "mlc_10h_24h_status": row.get("mlc_10h_24h_status"),
                "mlc_77h_7d_status": row.get("mlc_77h_7d_status"),
            }
            for row in raw_rows
        ]
        rest_hour_rows = [
            {
                "crew_id": row.get("crew_id"),
                "vessel_id": row.get("vessel_id"),
                "work_date_local": row.get("work_date_local"),
                "total_rest_24h": row.get("total_rest_24h"),
                "total_rest_7d": row.get("total_rest_7d"),
            }
            for row in raw_rows
        ]

        return {
            "timezone_offset_minutes": lookback["timezone_offset_minutes"],
            "attendance_rows": attendance_rows,
            "rest_hour_rows": rest_hour_rows,
            "warnings": list(lookback["warnings"]),
            "warning_codes": list(lookback["warning_codes"]),
        }
