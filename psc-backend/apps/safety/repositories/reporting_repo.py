from __future__ import annotations

from datetime import timedelta

from .base import BaseRepository


class ReportingRepository(BaseRepository):
    """Read-only access to Reporting daily-report tables in the shared DB."""

    table_definitions = (
        {
            "lat_columns": ("Lattitude1", "Lattitude2", "Lattitude3"),
            "lon_columns": ("Longitude1", "Longitud2", "Longitud3"),
            "name": "NoonReport",
            "source_priority": 0,
            "vessel_column": "VesselID",
        },
        {
            "lat_columns": ("Lattitude1", "Lattitude2", "Lattitude3"),
            "lon_columns": ("Longitude1", "Longitude2", "Longitude3"),
            "name": "DepartureReport",
            "source_priority": 1,
            "vessel_column": "VesselID",
        },
        {
            "lat_columns": ("Lattitude1", "Lattitude2", "Lattitude3"),
            "lon_columns": ("Longitude1", "Longitud2", "Longitud3"),
            "name": "ArrivalReport",
            "source_priority": 2,
            "vessel_column": "VesselID",
        },
        {
            "lat_columns": ("Latitude1", "Latitude2", "Latitude3"),
            "lon_columns": ("Longitude1", "Longitude2", "Longitude3"),
            "name": "NoonReportPort",
            "source_priority": 3,
            "vessel_column": "VesselCode",
        },
    )

    def find_position_candidates(
        self,
        *,
        vessel_id: str,
        occurred_at,
        tolerance_hours: int = 12,
    ) -> list[dict[str, object]]:
        if vessel_id in (None, "") or occurred_at is None:
            return []

        if self.connection.vendor == "microsoft":
            candidate = self._find_best_candidate_sql_server(
                vessel_id=str(vessel_id),
                occurred_at=occurred_at,
                tolerance_hours=tolerance_hours,
            )
            return [candidate] if candidate is not None else []

        return self._find_candidates_portable(
            vessel_id=str(vessel_id),
            occurred_at=occurred_at,
            tolerance_hours=tolerance_hours,
        )

    def _find_candidates_portable(
        self,
        *,
        vessel_id: str,
        occurred_at,
        tolerance_hours: int,
    ) -> list[dict[str, object]]:
        start_at = occurred_at - timedelta(hours=tolerance_hours)
        end_at = occurred_at + timedelta(hours=tolerance_hours)
        available_tables = set(self.connection.introspection.table_names())

        union_parts: list[str] = []
        params: list[object] = []
        for table in self.table_definitions:
            table_name = table["name"]
            if table_name not in available_tables:
                continue

            lat_deg, lat_min, lat_hemi = table["lat_columns"]
            lon_deg, lon_min, lon_hemi = table["lon_columns"]
            union_parts.append(
                f"""
                SELECT
                    '{table_name}' AS source_table,
                    CAST(id AS VARCHAR(64)) AS source_id,
                    auto_id AS source_auto_id,
                    {table["source_priority"]} AS source_priority,
                    {table["vessel_column"]} AS vessel_code,
                    ReportDate AS report_date,
                    {lat_deg} AS lat_deg,
                    {lat_min} AS lat_min,
                    {lat_hemi} AS lat_hemi,
                    {lon_deg} AS lon_deg,
                    {lon_min} AS lon_min,
                    {lon_hemi} AS lon_hemi
                FROM {table_name}
                WHERE {table["vessel_column"]} = %s
                  AND ReportDate >= %s
                  AND ReportDate <= %s
                """
            )
            params.extend([str(vessel_id), start_at, end_at])

        if not union_parts:
            return []

        query = " UNION ALL ".join(union_parts)
        rows = self.execute_query(query, params=tuple(params))
        return [dict(row) for row in rows]

    def _find_best_candidate_sql_server(
        self,
        *,
        vessel_id: str,
        occurred_at,
        tolerance_hours: int,
    ) -> dict[str, object] | None:
        available_tables = set(self.connection.introspection.table_names())

        union_parts: list[str] = []
        params: list[object] = []
        for table in self.table_definitions:
            table_name = table["name"]
            if table_name not in available_tables:
                continue

            lat_deg, lat_min, lat_hemi = table["lat_columns"]
            lon_deg, lon_min, lon_hemi = table["lon_columns"]
            union_parts.append(
                f"""
                SELECT
                    '{table_name}' AS source_table,
                    CAST(id AS VARCHAR(64)) AS source_id,
                    auto_id AS source_auto_id,
                    {table["source_priority"]} AS source_priority,
                    {table["vessel_column"]} AS vessel_code,
                    ReportDate AS report_date,
                    {lat_deg} AS lat_deg,
                    {lat_min} AS lat_min,
                    {lat_hemi} AS lat_hemi,
                    {lon_deg} AS lon_deg,
                    {lon_min} AS lon_min,
                    {lon_hemi} AS lon_hemi
                FROM {table_name}
                WHERE {table["vessel_column"]} = %s
                  AND ReportDate >= DATEADD(HOUR, -%s, %s)
                  AND ReportDate <= DATEADD(HOUR, %s, %s)
                """
            )
            params.extend([vessel_id, tolerance_hours, occurred_at, tolerance_hours, occurred_at])

        if not union_parts:
            return None

        query = f"""
        SELECT TOP 1
            source_table,
            source_id,
            source_auto_id,
            source_priority,
            vessel_code,
            report_date,
            lat_deg,
            lat_min,
            lat_hemi,
            lon_deg,
            lon_min,
            lon_hemi
        FROM (
            {" UNION ALL ".join(union_parts)}
        ) candidate
        ORDER BY
            ABS(DATEDIFF(MINUTE, report_date, %s)),
            source_priority,
            report_date DESC
        """
        params.append(occurred_at)
        rows = self.execute_query(query, params=tuple(params))
        return dict(rows[0]) if rows else None
