from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection


class SOINoPerItemInDbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()

    def test_workspace_has_no_per_item_response_table_or_scan_columns(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'vims_safety_soi_item_response'
                """
            )
            table_row = cursor.fetchone()
            cursor.execute("PRAGMA table_info(vims_safety_soi_finding)")
            columns = {row[1] for row in cursor.fetchall()}

        self.assertIsNone(table_row)
        self.assertNotIn("response_value", columns)
        self.assertNotIn("yes_no_na", columns)
        self.assertNotIn("scan_upload_path", columns)
