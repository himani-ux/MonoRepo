from __future__ import annotations

from datetime import date, datetime, time
import re

from django.utils import timezone

from .base import BaseRepository


_GUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class CMSRepository(BaseRepository):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._table_columns_cache: dict[str, set[str]] = {}
        self._rank_cache: dict[str, str] = {}
        self._department_cache: dict[str, str] = {}

    def get_current_crew_snapshot(
        self,
        *,
        vessel_id: str,
        crew_id: str,
        active_on: date | datetime | str | None = None,
    ) -> dict[str, object] | None:
        rows = self._fetch_crew_rows(
            vessel_id=str(vessel_id),
            crew_id=str(crew_id),
            active_on=self._coerce_active_on(active_on),
        )
        normalized_rows = self._normalize_rows(rows)
        return normalized_rows[0] if normalized_rows else None

    def list_current_vessel_crew(
        self,
        *,
        vessel_id: str,
        active_on: date | datetime | str | None = None,
        exclude_department: str | None = None,
        exclude_crew_id: str | None = None,
    ) -> list[dict[str, object]]:
        rows = self._fetch_crew_rows(
            vessel_id=str(vessel_id),
            crew_id=None,
            active_on=self._coerce_active_on(active_on),
        )
        normalized_department = None if exclude_department in (None, "") else str(exclude_department).strip().upper()
        normalized_crew_id = None if exclude_crew_id in (None, "") else str(exclude_crew_id).strip()
        normalized_rows = self._normalize_rows(rows)
        return [
            row
            for row in normalized_rows
            if row.get("department") != normalized_department and row.get("crew_id") != normalized_crew_id
        ]

    def _fetch_crew_rows(
        self,
        *,
        vessel_id: str,
        crew_id: str | None,
        active_on: date,
    ) -> list[dict[str, object]]:
        if self._uses_live_schema():
            return self.execute_query(
                self._build_live_query(filter_single_crew=crew_id is not None),
                self._build_live_params(vessel_id=vessel_id, crew_id=crew_id, active_on=active_on),
            )
        return self.execute_query(
            self._build_legacy_query(filter_single_crew=crew_id is not None),
            self._build_legacy_params(vessel_id=vessel_id, crew_id=crew_id),
        )

    def _build_live_query(self, *, filter_single_crew: bool) -> str:
        crew_filter = "  AND coh.CrewID = %s\n" if filter_single_crew else ""
        return (
            "SELECT\n"
            "    coh.CrewID AS crew_id,\n"
            "    coh.Vessel AS vessel_id,\n"
            "    hr.department_name AS raw_department,\n"
            "    hr.rank_name AS raw_rank,\n"
            "    hr.first_name AS first_name,\n"
            "    hr.surname AS surname,\n"
            "    fcl.CrewName AS crew_name,\n"
            "    coh.SignOnDate AS sign_on_date,\n"
            "    coh.SignOffDate AS sign_off_date\n"
            "FROM Crew_Onboarding_History AS coh\n"
            "LEFT JOIN HRM501 AS hr\n"
            "    ON hr.CrewID = coh.CrewID\n"
            "   AND COALESCE(hr.is_deleted, 0) = 0\n"
            "LEFT JOIN Final_crew_list AS fcl\n"
            "    ON fcl.CrewID = coh.CrewID\n"
            "   AND COALESCE(fcl.is_delete, 0) = 0\n"
            "WHERE coh.Vessel = %s\n"
            "  AND COALESCE(coh.is_deleted, 0) = 0\n"
            "  AND COALESCE(coh.is_active, 1) = 1\n"
            "  AND (coh.SignOnDate IS NULL OR coh.SignOnDate <= %s)\n"
            "  AND (coh.SignOffDate IS NULL OR coh.SignOffDate >= %s)\n"
            f"{crew_filter}"
            "ORDER BY coh.SignOnDate DESC, coh.id DESC"
        )

    def _build_live_params(
        self,
        *,
        vessel_id: str,
        crew_id: str | None,
        active_on: date,
    ) -> list[object]:
        start_of_day = datetime.combine(active_on, time.min)
        end_of_day = datetime.combine(active_on, time.max)
        params: list[object] = [vessel_id, end_of_day, start_of_day]
        if crew_id is not None:
            params.append(crew_id)
        return params

    def _build_legacy_query(self, *, filter_single_crew: bool) -> str:
        crew_filter = "  AND coh.crew_id = %s\n" if filter_single_crew else ""
        return (
            "SELECT\n"
            "    coh.crew_id AS crew_id,\n"
            "    coh.vessel_id AS vessel_id,\n"
            "    COALESCE(hr.department, coh.department, '') AS raw_department,\n"
            "    COALESCE(hr.rank, coh.rank, '') AS raw_rank,\n"
            "    '' AS first_name,\n"
            "    '' AS surname,\n"
            "    '' AS crew_name,\n"
            "    NULL AS sign_on_date,\n"
            "    NULL AS sign_off_date\n"
            "FROM Crew_Onboarding_History AS coh\n"
            "LEFT JOIN HRM501 AS hr\n"
            "    ON hr.crew_id = coh.crew_id\n"
            "WHERE coh.vessel_id = %s\n"
            "  AND coh.is_current = %s\n"
            f"{crew_filter}"
            "ORDER BY coh.id DESC"
        )

    def _build_legacy_params(self, *, vessel_id: str, crew_id: str | None) -> list[object]:
        params: list[object] = [vessel_id, True]
        if crew_id is not None:
            params.append(crew_id)
        return params

    def _normalize_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        normalized_rows: list[dict[str, object]] = []
        seen_crew_ids: set[str] = set()
        for row in rows:
            crew_id = str(row.get("crew_id") or "").strip()
            if not crew_id or crew_id in seen_crew_ids:
                continue

            department = self._resolve_department(row.get("raw_department"))
            rank = self._resolve_rank(row.get("raw_rank"))
            normalized_rows.append(
                {
                    "crew_id": crew_id,
                    "vessel_id": str(row.get("vessel_id") or "").strip(),
                    "department": department,
                    "rank": rank,
                    "crew_name": self._build_crew_name(row),
                    "sign_on_date": row.get("sign_on_date"),
                    "sign_off_date": row.get("sign_off_date"),
                }
            )
            seen_crew_ids.add(crew_id)

        return sorted(
            normalized_rows,
            key=lambda row: (str(row.get("department") or ""), str(row.get("rank") or ""), str(row.get("crew_id") or "")),
        )

    def _resolve_rank(self, raw_rank: object) -> str:
        normalized = str(raw_rank or "").strip()
        if not normalized:
            return ""
        if _GUID_RE.fullmatch(normalized):
            cached = self._rank_cache.get(normalized.lower())
            if cached is not None:
                return cached
            resolved = self.execute_scalar("SELECT rank_name FROM master_applied_rank WHERE id = %s", [normalized])
            value = str(resolved or normalized).strip().upper()
            self._rank_cache[normalized.lower()] = value
            return value
        return normalized.upper()

    def _resolve_department(self, raw_department: object) -> str:
        normalized = str(raw_department or "").strip()
        if not normalized:
            return ""
        if _GUID_RE.fullmatch(normalized):
            cached = self._department_cache.get(normalized.lower())
            if cached is not None:
                return cached
            resolved = self.execute_scalar("SELECT department_name FROM department WHERE id = %s", [normalized])
            value = str(resolved or normalized).strip().upper()
            self._department_cache[normalized.lower()] = value
            return value
        return normalized.upper()

    def _build_crew_name(self, row: dict[str, object]) -> str:
        crew_name = str(row.get("crew_name") or "").strip()
        if crew_name:
            return crew_name

        first_name = str(row.get("first_name") or "").strip()
        surname = str(row.get("surname") or "").strip()
        return " ".join(part for part in (first_name, surname) if part)

    def _uses_live_schema(self) -> bool:
        return self._table_has_columns(
            "Crew_Onboarding_History",
            {"CrewID", "Vessel", "SignOnDate", "SignOffDate"},
        )

    def _table_has_columns(self, table_name: str, expected_columns: set[str]) -> bool:
        return expected_columns.issubset(self._get_table_columns(table_name))

    def _get_table_columns(self, table_name: str) -> set[str]:
        if table_name in self._table_columns_cache:
            return self._table_columns_cache[table_name]

        try:
            with self.connection.cursor() as cursor:
                description = self.connection.introspection.get_table_description(cursor, table_name)
        except Exception:
            columns: set[str] = set()
        else:
            columns = set()
            for column in description:
                if hasattr(column, "name"):
                    columns.add(str(column.name))
                else:
                    columns.add(str(column[0]))

        self._table_columns_cache[table_name] = columns
        return columns

    def _coerce_active_on(self, active_on: date | datetime | str | None) -> date:
        if active_on is None:
            return timezone.localdate()
        if isinstance(active_on, datetime):
            return active_on.date()
        if isinstance(active_on, date):
            return active_on
        return date.fromisoformat(str(active_on))
