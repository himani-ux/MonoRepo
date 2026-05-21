from __future__ import annotations

import unittest

import pyodbc

from tests.safety.test_db_connection import _build_connection_string, _is_known_sandbox_sspi_error


class SCMWrhLiveJoinTests(unittest.TestCase):
    def test_wrh_s520_tables_are_reachable_in_ksm_marine_live(self) -> None:
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
                    WHERE TABLE_NAME IN ('wrh_s520_day_entry', 'wrh_s520_month', 'wrh_ship_time_config')
                    """
                )
                self.assertEqual(cursor.fetchone()[0], 3)

                cursor.execute(
                    """
                    SELECT TOP 1
                        m.vessel_id,
                        d.crew_id,
                        d.work_date_local,
                        d.total_rest_24h,
                        d.total_rest_7d,
                        d.mlc_10h_24h_status,
                        d.mlc_77h_7d_status
                    FROM dbo.wrh_s520_day_entry d
                    INNER JOIN dbo.wrh_s520_month m ON m.id = d.s520_month_id
                    ORDER BY d.work_date_local DESC, d.id DESC
                    """
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row, "Expected live WRH S520 rows for Safety attendance validation.")
                self.assertIsNotNone(row[0])
                self.assertIsNotNone(row[1])
                self.assertIsNotNone(row[2])

                cursor.execute(
                    """
                    SELECT TOP 1
                        m.vessel_id,
                        cfg.effective_date,
                        cfg.tz_offset_minutes
                    FROM dbo.wrh_s520_month m
                    INNER JOIN dbo.wrh_ship_time_config cfg ON cfg.vessel_id = m.vessel_id
                    ORDER BY cfg.effective_date DESC, cfg.id DESC
                    """
                )
                tz_row = cursor.fetchone()
                self.assertIsNotNone(tz_row, "Expected WRH ship-time configuration rows for Safety attendance validation.")
                self.assertIsNotNone(tz_row[0])
                self.assertIsNotNone(tz_row[1])
                self.assertIsNotNone(tz_row[2])
        except pyodbc.Error as error:
            if uses_trusted_connection and _is_known_sandbox_sspi_error(error):
                self.skipTest(
                    "Sandboxed Windows integrated auth failed with the known SSPI/ODBC handshake issue. "
                    "Re-run this test outside the sandbox or set SAFETY_SQLSERVER_USER and "
                    "SAFETY_SQLSERVER_PASSWORD for SQL authentication."
                )
            raise
