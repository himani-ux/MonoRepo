from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection

from apps.safety.repositories.soi_repo import SOIRepository


class SOIApplicabilityLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.repository = SOIRepository()
        self._insert_area(area_id=13, area_name="Cross-cutting Safety & Culture", section_12_flag=True)

    def test_dpa_decision_fields_persist_when_supplied(self) -> None:
        self.repository.update_applicability(
            vessel_id="7",
            area_id=13,
            applicable=False,
            actor_id="master-7",
            reason="Section 12 will be covered from another vessel workflow in this cycle.",
            master_signature="Captain Example|device-abc",
            dpa_approved_by="dpa-1",
            dpa_signature="DPA Example|device-dpa",
            dpa_decision="APPROVED",
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT dpa_approved_by, dpa_signature, dpa_decision
                FROM vims_safety_soi_applicability_log
                WHERE vessel_id = %s AND area_id = %s
                """,
                ["7", 13],
            )
            row = cursor.fetchone()

        self.assertEqual(row[0], "dpa-1")
        self.assertEqual(row[1], "DPA Example|device-dpa")
        self.assertEqual(row[2], "APPROVED")

    def _insert_area(self, *, area_id: int, area_name: str, section_12_flag: bool) -> None:
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
                [area_id, area_name, section_12_flag, area_id, True, "v1.0"],
            )
