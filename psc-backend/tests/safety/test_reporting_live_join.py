from __future__ import annotations

import unittest

import pyodbc

from tests.safety.test_db_connection import _build_connection_string, _is_known_sandbox_sspi_error


class ReportingLiveJoinTests(unittest.TestCase):
    def test_reporting_daily_report_tables_are_reachable_in_ksm_marine_live(self) -> None:
        expected_db_name = "ksm_marine_live"
        conn_str, uses_trusted_connection = _build_connection_string()

        try:
            with pyodbc.connect(conn_str, timeout=15) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT DB_NAME()")
                self.assertEqual(cursor.fetchone()[0], expected_db_name)

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME IN ('NoonReport', 'DepartureReport', 'ArrivalReport', 'NoonReportPort')
                    """
                )
                self.assertEqual(cursor.fetchone()[0], 4)

                cursor.execute(
                    """
                    SELECT TOP 1 VesselID, ReportDate, Lattitude1, Lattitude2, Lattitude3
                    FROM dbo.NoonReport
                    ORDER BY ReportDate DESC
                    """
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row, "Expected NoonReport rows for live Safety↔Reporting validation.")
                self.assertIsNotNone(row[0])
                self.assertIsNotNone(row[1])
        except pyodbc.Error as error:
            if uses_trusted_connection and _is_known_sandbox_sspi_error(error):
                self.skipTest(
                    "Sandboxed Windows integrated auth failed with the known SSPI/ODBC handshake issue. "
                    "Re-run this test outside the sandbox or set SAFETY_SQLSERVER_USER and "
                    "SAFETY_SQLSERVER_PASSWORD for SQL authentication."
                )
            raise
