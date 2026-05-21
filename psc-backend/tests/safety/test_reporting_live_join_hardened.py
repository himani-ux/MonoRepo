from __future__ import annotations

from time import perf_counter
import unittest

import pyodbc

from tests.safety.test_db_connection import _build_connection_string, _is_known_sandbox_sspi_error


class ReportingLiveJoinHardenedTests(unittest.TestCase):
    def test_scoped_reporting_join_resolves_under_200ms_on_live_db(self) -> None:
        conn_str, uses_trusted_connection = _build_connection_string()

        try:
            with pyodbc.connect(conn_str, timeout=15) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT TOP 1 VesselID, ReportDate FROM dbo.NoonReport ORDER BY ReportDate DESC")
                seed_row = cursor.fetchone()
                self.assertIsNotNone(seed_row, "Expected NoonReport rows for the Step 5.1 live-join benchmark.")
                vessel_id, occurred_at = seed_row

                sql = """
                SELECT TOP 1 source_table, source_id, source_auto_id, report_date
                FROM (
                    SELECT
                        'NoonReport' AS source_table,
                        CAST(id AS VARCHAR(64)) AS source_id,
                        auto_id AS source_auto_id,
                        0 AS source_priority,
                        ReportDate AS report_date
                    FROM dbo.NoonReport
                    WHERE VesselID = ?
                      AND ReportDate >= DATEADD(HOUR, -12, ?)
                      AND ReportDate <= DATEADD(HOUR, 12, ?)
                    UNION ALL
                    SELECT
                        'DepartureReport' AS source_table,
                        CAST(id AS VARCHAR(64)) AS source_id,
                        auto_id AS source_auto_id,
                        1 AS source_priority,
                        ReportDate AS report_date
                    FROM dbo.DepartureReport
                    WHERE VesselID = ?
                      AND ReportDate >= DATEADD(HOUR, -12, ?)
                      AND ReportDate <= DATEADD(HOUR, 12, ?)
                    UNION ALL
                    SELECT
                        'ArrivalReport' AS source_table,
                        CAST(id AS VARCHAR(64)) AS source_id,
                        auto_id AS source_auto_id,
                        2 AS source_priority,
                        ReportDate AS report_date
                    FROM dbo.ArrivalReport
                    WHERE VesselID = ?
                      AND ReportDate >= DATEADD(HOUR, -12, ?)
                      AND ReportDate <= DATEADD(HOUR, 12, ?)
                    UNION ALL
                    SELECT
                        'NoonReportPort' AS source_table,
                        CAST(id AS VARCHAR(64)) AS source_id,
                        auto_id AS source_auto_id,
                        3 AS source_priority,
                        ReportDate AS report_date
                    FROM dbo.NoonReportPort
                    WHERE VesselCode = ?
                      AND ReportDate >= DATEADD(HOUR, -12, ?)
                      AND ReportDate <= DATEADD(HOUR, 12, ?)
                ) candidate
                ORDER BY ABS(DATEDIFF(MINUTE, report_date, ?)), source_priority, report_date DESC
                """
                params = [
                    vessel_id,
                    occurred_at,
                    occurred_at,
                    vessel_id,
                    occurred_at,
                    occurred_at,
                    vessel_id,
                    occurred_at,
                    occurred_at,
                    vessel_id,
                    occurred_at,
                    occurred_at,
                    occurred_at,
                ]

                cursor.execute(sql, params).fetchone()

                started = perf_counter()
                row = cursor.execute(sql, params).fetchone()
                elapsed_ms = (perf_counter() - started) * 1000

                self.assertIsNotNone(row, "Expected the hardened query to return a matching Reporting row.")
                self.assertLess(
                    elapsed_ms,
                    200,
                    f"Expected the scoped Reporting live join to stay under 200 ms, got {elapsed_ms:.2f} ms.",
                )
        except pyodbc.Error as error:
            if uses_trusted_connection and _is_known_sandbox_sspi_error(error):
                self.skipTest(
                    "Sandboxed Windows integrated auth failed with the known SSPI/ODBC handshake issue. "
                    "Re-run this test outside the sandbox or set SAFETY_SQLSERVER_USER and "
                    "SAFETY_SQLSERVER_PASSWORD for SQL authentication."
                )
            raise
