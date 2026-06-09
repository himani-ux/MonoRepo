from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from apps.safety.repositories.exceptions import SPExecutionError, SPTimeoutError
from apps.safety.repositories.wrh_repo import WRHRepository


class WRHSnapshotFetcher:
    SCM_ATTENDANCE_MODE = "SNAPSHOT_ON_SAVE"
    INCIDENT_FATIGUE_MODE = "LIVE_7_DAY_LOOKBACK"
    ATTENDANCE_LOOKBACK_HOURS = WRHRepository.ATTENDANCE_SNAPSHOT_LOOKBACK_HOURS
    ATTENDANCE_ROLLUP_DAYS = WRHRepository.ATTENDANCE_ROLLUP_DAYS
    FATIGUE_LOOKBACK_DAYS = WRHRepository.FATIGUE_LOOKBACK_DAYS
    QUERY_TIMEOUT_ENV = WRHRepository.QUERY_TIMEOUT_ENV
    LOOKUP_FAILED_MESSAGE = "WRH lookup failed. Continue with manual review (D-GAP-M11)."
    LOOKUP_TIMEOUT_MESSAGE = "WRH lookup timed out. Continue with manual review (D-GAP-M11)."
    MISSING_DATA_MESSAGE = "WRH data unavailable for the requested crew/date."
    MISSING_TIMEZONE_MESSAGE = "WRH ship-time configuration unavailable for this vessel/date."

    def __init__(self, *, wrh_repository: WRHRepository | None = None) -> None:
        self.wrh_repository = wrh_repository or WRHRepository()

    def fetch_timezone_offset(
        self,
        *,
        vessel_id: str,
        meeting_date: date | datetime | str,
    ) -> int | None:
        if not vessel_id or not self.wrh_repository.has_required_tables():
            return None

        try:
            return self.wrh_repository.get_timezone_offset_minutes(
                vessel_id=vessel_id,
                meeting_date=meeting_date,
            )
        except (SPExecutionError, SPTimeoutError):
            return None

    def fetch_24h_and_7d(
        self,
        *,
        crew_id: str,
        meeting_date: date | datetime | str,
        vessel_id: str,
    ) -> dict[str, object]:
        # SCM attendance persists the latest available WRH daily rollup as of the
        # meeting date; later Safety reads reuse the saved attendance row instead
        # of re-querying WRH rest-hour rows at render time.
        timezone_offset_minutes = self.fetch_timezone_offset(
            vessel_id=vessel_id,
            meeting_date=meeting_date,
        )

        if not crew_id or not vessel_id:
            return self._missing_snapshot(
                timezone_offset_minutes=timezone_offset_minutes,
                warning_codes=["missing_data"],
            )

        if not self.wrh_repository.has_required_tables():
            return self._missing_snapshot(
                timezone_offset_minutes=timezone_offset_minutes,
                warning_codes=["lookup_failed"],
            )

        try:
            snapshot_row = self.wrh_repository.get_latest_rest_snapshot(
                crew_id=crew_id,
                vessel_id=vessel_id,
                meeting_date=meeting_date,
            )
        except SPTimeoutError:
            return self._missing_snapshot(
                timezone_offset_minutes=timezone_offset_minutes,
                warning_codes=["lookup_timeout"],
            )
        except SPExecutionError:
            return self._missing_snapshot(
                timezone_offset_minutes=timezone_offset_minutes,
                warning_codes=["lookup_failed"],
            )

        if snapshot_row is None:
            return self._missing_snapshot(
                timezone_offset_minutes=timezone_offset_minutes,
                warning_codes=["missing_data"],
            )

        return self._snapshot_from_rest_row(
            snapshot_row,
            timezone_offset_minutes=timezone_offset_minutes,
        )

    def fetch_many_24h_and_7d(
        self,
        *,
        crew_ids: Sequence[str],
        meeting_date: date | datetime | str,
        vessel_id: str,
    ) -> dict[str, dict[str, object]]:
        timezone_offset_minutes = self.fetch_timezone_offset(
            vessel_id=vessel_id,
            meeting_date=meeting_date,
        )

        normalized_crew_ids = [str(crew_id).strip() for crew_id in crew_ids if str(crew_id).strip()]
        if not normalized_crew_ids or not vessel_id:
            return {
                crew_id: self._missing_snapshot(
                    timezone_offset_minutes=timezone_offset_minutes,
                    warning_codes=["missing_data"],
                )
                for crew_id in normalized_crew_ids
            }

        if not self.wrh_repository.has_required_tables():
            return {
                crew_id: self._missing_snapshot(
                    timezone_offset_minutes=timezone_offset_minutes,
                    warning_codes=["lookup_failed"],
                )
                for crew_id in normalized_crew_ids
            }

        try:
            rows = self.wrh_repository.list_latest_rest_snapshots(
                crew_ids=normalized_crew_ids,
                vessel_id=vessel_id,
                meeting_date=meeting_date,
            )
        except SPTimeoutError:
            return {
                crew_id: self._missing_snapshot(
                    timezone_offset_minutes=timezone_offset_minutes,
                    warning_codes=["lookup_timeout"],
                )
                for crew_id in normalized_crew_ids
            }
        except SPExecutionError:
            return {
                crew_id: self._missing_snapshot(
                    timezone_offset_minutes=timezone_offset_minutes,
                    warning_codes=["lookup_failed"],
                )
                for crew_id in normalized_crew_ids
            }

        snapshots = {
            str(row.get("crew_id")): self._snapshot_from_rest_row(
                row,
                timezone_offset_minutes=timezone_offset_minutes,
            )
            for row in rows
        }
        for crew_id in normalized_crew_ids:
            snapshots.setdefault(
                crew_id,
                self._missing_snapshot(
                    timezone_offset_minutes=timezone_offset_minutes,
                    warning_codes=["missing_data"],
                ),
            )
        return snapshots

    def _snapshot_from_rest_row(
        self,
        snapshot_row: dict[str, object],
        *,
        timezone_offset_minutes: int | None,
    ) -> dict[str, object]:
        status_24h = self._normalize_status(snapshot_row.get("mlc_10h_24h_status"))
        status_7d = self._normalize_status(snapshot_row.get("mlc_77h_7d_status"))
        wrh_non_compliance_flag = status_24h not in ("", "OK") or status_7d not in ("", "OK")

        warning_codes: list[str] = []
        if timezone_offset_minutes is None:
            warning_codes.append("missing_timezone")
        if wrh_non_compliance_flag:
            warning_codes.append("non_compliance")

        return {
            "timezone_offset_minutes": timezone_offset_minutes,
            "warning_codes": warning_codes,
            "warnings": self._build_warning_messages(warning_codes),
            "wrh_24h_status": status_24h or None,
            "wrh_7d_status": status_7d or None,
            "wrh_data_available": True,
            "wrh_flag": "YELLOW" if wrh_non_compliance_flag else "GREEN",
            "wrh_non_compliance_flag": wrh_non_compliance_flag,
            "wrh_rest_hours_24h": snapshot_row.get("total_rest_24h"),
            "wrh_rest_hours_7d": snapshot_row.get("total_rest_7d"),
            "wrh_work_date_local": snapshot_row.get("work_date_local"),
        }

    def fetch_fatigue_lookback(
        self,
        *,
        crew_ids: Sequence[str],
        reference_date: date | datetime | str,
        vessel_id: str,
    ) -> dict[str, object]:
        # Incident fatigue evidence remains a read-time trailing lookback over the
        # WRH daily rows rather than a persisted Safety-side snapshot table.
        timezone_offset_minutes = self.fetch_timezone_offset(
            vessel_id=vessel_id,
            meeting_date=reference_date,
        )

        normalized_crew_ids = [str(crew_id).strip() for crew_id in crew_ids if str(crew_id).strip()]
        if not normalized_crew_ids or not vessel_id:
            warning_codes = ["missing_data"]
            if timezone_offset_minutes is None:
                warning_codes.append("missing_timezone")
            return {
                "timezone_offset_minutes": timezone_offset_minutes,
                "warning_codes": warning_codes,
                "warnings": self._build_warning_messages(warning_codes),
                "rows": [],
            }

        if not self.wrh_repository.has_required_tables():
            warning_codes = ["lookup_failed"]
            if timezone_offset_minutes is None:
                warning_codes.append("missing_timezone")
            return {
                "timezone_offset_minutes": timezone_offset_minutes,
                "warning_codes": warning_codes,
                "warnings": self._build_warning_messages(warning_codes),
                "rows": [],
            }

        try:
            rows = self.wrh_repository.list_fatigue_lookback_rows(
                crew_ids=normalized_crew_ids,
                vessel_id=vessel_id,
                reference_date=reference_date,
            )
        except SPTimeoutError:
            warning_codes = ["lookup_timeout"]
            if timezone_offset_minutes is None:
                warning_codes.append("missing_timezone")
            return {
                "timezone_offset_minutes": timezone_offset_minutes,
                "warning_codes": warning_codes,
                "warnings": self._build_warning_messages(warning_codes),
                "rows": [],
            }
        except SPExecutionError:
            warning_codes = ["lookup_failed"]
            if timezone_offset_minutes is None:
                warning_codes.append("missing_timezone")
            return {
                "timezone_offset_minutes": timezone_offset_minutes,
                "warning_codes": warning_codes,
                "warnings": self._build_warning_messages(warning_codes),
                "rows": [],
            }

        warning_codes: list[str] = []
        if timezone_offset_minutes is None:
            warning_codes.append("missing_timezone")
        if not rows:
            warning_codes.append("missing_data")

        return {
            "timezone_offset_minutes": timezone_offset_minutes,
            "warning_codes": warning_codes,
            "warnings": self._build_warning_messages(warning_codes),
            "rows": rows,
        }

    def _missing_snapshot(
        self,
        *,
        timezone_offset_minutes: int | None,
        warning_codes: list[str],
    ) -> dict[str, object]:
        if timezone_offset_minutes is None and "missing_timezone" not in warning_codes:
            warning_codes = [*warning_codes, "missing_timezone"]

        return {
            "timezone_offset_minutes": timezone_offset_minutes,
            "warning_codes": warning_codes,
            "warnings": self._build_warning_messages(warning_codes),
            "wrh_24h_status": None,
            "wrh_7d_status": None,
            "wrh_data_available": False,
            "wrh_flag": "RED",
            "wrh_non_compliance_flag": False,
            "wrh_rest_hours_24h": None,
            "wrh_rest_hours_7d": None,
            "wrh_work_date_local": None,
        }

    def _normalize_status(self, value: object) -> str:
        if value in (None, ""):
            return ""
        return str(value).strip().upper()

    def _build_warning_messages(self, warning_codes: Sequence[str]) -> list[str]:
        messages: list[str] = []
        for code in warning_codes:
            if code == "lookup_failed":
                messages.append(self.LOOKUP_FAILED_MESSAGE)
            elif code == "lookup_timeout":
                messages.append(self.LOOKUP_TIMEOUT_MESSAGE)
            elif code == "missing_data":
                messages.append(self.MISSING_DATA_MESSAGE)
            elif code == "missing_timezone":
                messages.append(self.MISSING_TIMEZONE_MESSAGE)
        return messages
