from __future__ import annotations

import os
import unittest

import pyodbc


def _build_connection_string() -> tuple[str, bool]:
    expected_db_name = os.getenv("SAFETY_SQLSERVER_DB", "ksm_marine_live")
    host = os.getenv("SAFETY_SQLSERVER_HOST", "localhost")
    port = os.getenv("SAFETY_SQLSERVER_PORT", "").strip()
    driver = os.getenv("SAFETY_SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server")
    encrypt = os.getenv("SAFETY_SQLSERVER_ENCRYPT", "no")
    trust_server_certificate = os.getenv("SAFETY_SQLSERVER_TRUST_SERVER_CERTIFICATE", "yes")
    username = os.getenv("SAFETY_SQLSERVER_USER", "").strip()
    password = os.getenv("SAFETY_SQLSERVER_PASSWORD", "")
    server = host if not port or "," in host else f"{host},{port}"

    if bool(username) ^ bool(password):
        raise AssertionError(
            "Set both SAFETY_SQLSERVER_USER and SAFETY_SQLSERVER_PASSWORD together for SQL authentication."
        )

    parts = [
        f"DRIVER={{{driver}}};",
        f"SERVER={server};",
        f"DATABASE={expected_db_name};",
        f"Encrypt={encrypt};",
        f"TrustServerCertificate={trust_server_certificate};",
    ]

    if username and password:
        parts.extend(
            [
                f"UID={username};",
                f"PWD={password};",
            ]
        )
        return "".join(parts), False

    parts.append("Trusted_Connection=yes;")
    return "".join(parts), True


def _is_known_sandbox_sspi_error(error: pyodbc.Error) -> bool:
    message = " ".join(str(part) for part in error.args).lower()
    return (
        "no credentials are available in the security package" in message
        or "encryption not supported on the client" in message
    )


class SafetyDbConnectionTests(unittest.TestCase):
    def test_ksm_marine_live_platform_tables_are_reachable(self) -> None:
        expected_db_name = os.getenv("SAFETY_SQLSERVER_DB", "ksm_marine_live")
        conn_str, uses_trusted_connection = _build_connection_string()

        try:
            with pyodbc.connect(conn_str, timeout=15) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT DB_NAME()")
                self.assertEqual(cursor.fetchone()[0], expected_db_name)
                for table_name in ("master_role", "master_RoleByVessel", "master_applied_rank"):
                    cursor.execute(f"SELECT TOP 1 1 FROM {table_name}")
                    self.assertIsNotNone(cursor.fetchone(), f"Expected at least one row in {table_name}")
        except pyodbc.Error as error:
            if uses_trusted_connection and _is_known_sandbox_sspi_error(error):
                self.skipTest(
                    "Sandboxed Windows integrated auth failed with the known SSPI/ODBC handshake issue. "
                    "Re-run this test outside the sandbox or set SAFETY_SQLSERVER_USER and "
                    "SAFETY_SQLSERVER_PASSWORD for SQL authentication."
                )
            raise

    def test_live_soi_reference_seed_counts_are_ssot_aligned(self) -> None:
        conn_str, uses_trusted_connection = _build_connection_string()

        try:
            with pyodbc.connect(conn_str, timeout=15) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM master_soi_area WHERE active = 1")
                self.assertEqual(cursor.fetchone()[0], 13)
                cursor.execute("SELECT COUNT(*) FROM master_soi_area_item WHERE active = 1")
                self.assertEqual(cursor.fetchone()[0], 329)
                cursor.execute("SELECT COUNT(*) FROM master_soi_checklist_version WHERE active = 1")
                self.assertGreaterEqual(cursor.fetchone()[0], 1)
        except pyodbc.Error as error:
            if uses_trusted_connection and _is_known_sandbox_sspi_error(error):
                self.skipTest(
                    "Sandboxed Windows integrated auth failed with the known SSPI/ODBC handshake issue. "
                    "Re-run this test outside the sandbox or set SAFETY_SQLSERVER_USER and "
                    "SAFETY_SQLSERVER_PASSWORD for SQL authentication."
                )
            raise
