from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection

from apps.safety.repositories.soi_repo import SOIRepository


class SOIAreaMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.repository = SOIRepository()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=5, area_name="Environment")

    def test_list_applicability_defaults_missing_rows_to_true(self) -> None:
        rows = self.repository.list_applicability(vessel_id="7")

        self.assertEqual(len(rows), 2)
        self.assertEqual([row["area_id"] for row in rows], [3, 5])
        self.assertTrue(all(row["applicable"] is True for row in rows))
        self.assertTrue(all(row["map_id"] is None for row in rows))

    def test_toggle_false_upserts_map_and_writes_log(self) -> None:
        payload = self.repository.update_applicability(
            vessel_id="7",
            area_id=3,
            applicable=False,
            actor_id="master-7",
            reason="Cargo oil room does not exist on this vessel class.",
            master_signature="Captain Example|device-abc",
        )

        self.assertEqual(payload["applicable"], False)
        self.assertEqual(payload["area_id"], 3)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT applicable
                FROM vims_safety_soi_vessel_area_map
                WHERE vessel_id = %s AND area_id = %s
                """,
                ["7", 3],
            )
            map_row = cursor.fetchone()
            cursor.execute(
                """
                SELECT old_applicable, new_applicable, reason, master_requested_by
                FROM vims_safety_soi_applicability_log
                WHERE vessel_id = %s AND area_id = %s
                """,
                ["7", 3],
            )
            log_row = cursor.fetchone()

        self.assertEqual(map_row[0], False)
        self.assertEqual(log_row[0], True)
        self.assertEqual(log_row[1], False)
        self.assertEqual(log_row[2], "Cargo oil room does not exist on this vessel class.")
        self.assertEqual(log_row[3], "master-7")

    def _insert_area(self, *, area_id: int, area_name: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [area_id, area_name, False, area_id, True, "v1.0"],
            )
