from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta
import math
import os

from .base import BaseRepository


class WRHRepository(BaseRepository):
    DEFAULT_QUERY_TIMEOUT_MS = 10000
    QUERY_TIMEOUT_ENV = "SAFETY_WRH_QUERY_TIMEOUT_MS"
    REQUIRED_TABLES = {"wrh_s520_day_entry", "wrh_s520_month", "wrh_ship_time_config"}
    ATTENDANCE_SNAPSHOT_LOOKBACK_HOURS = 24
    ATTENDANCE_ROLLUP_DAYS = 7
    FATIGUE_LOOKBACK_DAYS = 7

    def __init__(self, *, timeout_ms: int | None = None, **kwargs) -> None:
        resolved_timeout_ms = self._resolve_timeout_ms(timeout_ms)
        kwargs.setdefault("timeout_seconds", self._timeout_seconds_from_ms(resolved_timeout_ms))
        super().__init__(**kwargs)
        self.timeout_ms = resolved_timeout_ms

    def has_required_tables(self) -> bool:
        return self.REQUIRED_TABLES.issubset(set(self.connection.introspection.table_names()))

    def get_timezone_offset_minutes(self, *, vessel_id: str, meeting_date: date | datetime | str) -> int | None:
        rows = self.execute_query(
            """
            SELECT effective_date, tz_offset_minutes
            FROM wrh_ship_time_config
            WHERE vessel_id = %s
              AND effective_date <= %s
            ORDER BY effective_date DESC, id DESC
            """,
            [str(vessel_id), self._coerce_date(meeting_date).isoformat()],
        )
        if not rows:
            return None
        value = rows[0].get("tz_offset_minutes")
        return None if value in (None, "") else int(value)

    def get_latest_rest_snapshot(
        self,
        *,
        crew_id: str,
        vessel_id: str,
        meeting_date: date | datetime | str,
    ) -> dict[str, object] | None:
        rows = self.execute_query(
            """
            SELECT
                d.crew_id,
                m.vessel_id,
                d.work_date_local,
                d.total_rest_24h,
                d.total_rest_7d,
                d.mlc_10h_24h_status,
                d.mlc_77h_7d_status,
                d.is_not_onboard,
                d.is_dateline_skip
            FROM wrh_s520_day_entry d
            INNER JOIN wrh_s520_month m ON m.id = d.s520_month_id
            WHERE d.crew_id = %s
              AND m.vessel_id = %s
              AND d.work_date_local <= %s
              AND COALESCE(d.is_not_onboard, 0) = 0
              AND COALESCE(d.is_dateline_skip, 0) = 0
            ORDER BY d.work_date_local DESC, d.id DESC
            """,
            [str(crew_id), str(vessel_id), self._coerce_date(meeting_date).isoformat()],
        )
        return rows[0] if rows else None

    def list_fatigue_lookback_rows(
        self,
        *,
        crew_ids: Iterable[str],
        vessel_id: str,
        reference_date: date | datetime | str,
    ) -> list[dict[str, object]]:
        normalized_crew_ids = [str(crew_id).strip() for crew_id in crew_ids if str(crew_id).strip()]
        if not normalized_crew_ids:
            return []

        window_end = self._coerce_date(reference_date)
        window_start = window_end - timedelta(days=self.FATIGUE_LOOKBACK_DAYS - 1)
        placeholders = ", ".join(["%s"] * len(normalized_crew_ids))

        return self.execute_query(
            f"""
            SELECT
                d.crew_id,
                m.vessel_id,
                d.work_date_local,
                d.tz_offset_minutes,
                d.total_rest_24h,
                d.total_rest_7d,
                d.mlc_10h_24h_status,
                d.mlc_77h_7d_status
            FROM wrh_s520_day_entry d
            INNER JOIN wrh_s520_month m ON m.id = d.s520_month_id
            WHERE m.vessel_id = %s
              AND d.crew_id IN ({placeholders})
              AND d.work_date_local >= %s
              AND d.work_date_local <= %s
              AND COALESCE(d.is_not_onboard, 0) = 0
              AND COALESCE(d.is_dateline_skip, 0) = 0
            ORDER BY d.work_date_local DESC, d.id DESC
            """,
            [str(vessel_id), *normalized_crew_ids, window_start.isoformat(), window_end.isoformat()],
        )

    def _coerce_date(self, value: date | datetime | str) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise TypeError(f"Unsupported meeting_date type: {type(value)!r}")

    def _resolve_timeout_ms(self, explicit_timeout_ms: int | None) -> int:
        if explicit_timeout_ms is not None:
            return max(1, int(explicit_timeout_ms))

        raw_value = os.getenv(self.QUERY_TIMEOUT_ENV, "").strip()
        if not raw_value:
            return self.DEFAULT_QUERY_TIMEOUT_MS

        try:
            return max(1, int(raw_value))
        except ValueError:
            return self.DEFAULT_QUERY_TIMEOUT_MS

    def _timeout_seconds_from_ms(self, timeout_ms: int) -> int:
        return max(1, math.ceil(timeout_ms / 1000))
