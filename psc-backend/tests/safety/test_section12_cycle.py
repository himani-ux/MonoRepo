from __future__ import annotations

from datetime import date
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection


class Section12CycleEnforcerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        from apps.safety.services.section12_cycle_enforcer import Section12CycleEnforcer

        self.enforcer = Section12CycleEnforcer(today_func=lambda: date(2026, 5, 1))

    def test_same_calendar_quarter_is_blocked_until_next_quarter_boundary(self) -> None:
        self._insert_inspection(
            vessel_id="7",
            inspection_reference="SOI/Q1/01",
            planned_date="2026-02-01",
            section_12_included=True,
        )

        can_pick_march, next_allowed_march = self.enforcer.can_pick_section_12(
            vessel_id="7",
            at_date=date(2026, 3, 31),
        )
        can_pick_april, next_allowed_april = self.enforcer.can_pick_section_12(
            vessel_id="7",
            at_date=date(2026, 4, 1),
        )

        self.assertEqual(can_pick_march, False)
        self.assertEqual(next_allowed_march, date(2026, 4, 1))
        self.assertEqual(can_pick_april, True)
        self.assertIsNone(next_allowed_april)

    def test_status_payload_reports_current_cycle_coverage(self) -> None:
        self._insert_inspection(
            vessel_id="7",
            inspection_reference="SOI/Q2/01",
            planned_date="2026-04-14",
            section_12_included=True,
        )

        status = self.enforcer.get_status(
            vessel_id="7",
            at_date=date(2026, 5, 10),
        )

        self.assertEqual(status["cycle_label"], "Q2/2026")
        self.assertEqual(status["covered_this_cycle"], True)
        self.assertEqual(status["prompt_required"], False)
        self.assertEqual(status["next_allowed_date"], "2026-07-01")
        self.assertEqual(status["covered_by_inspection_reference"], "SOI/Q2/01")
        self.assertEqual(status["covered_planned_date"], "2026-04-14")

    def test_current_inspection_can_keep_its_own_section12_assignment(self) -> None:
        inspection_id = self._insert_inspection(
            vessel_id="7",
            inspection_reference="SOI/Q2/02",
            planned_date="2026-05-12",
            section_12_included=True,
        )

        can_pick, next_allowed = self.enforcer.can_pick_section_12(
            vessel_id="7",
            at_date=date(2026, 5, 12),
            exclude_inspection_id=inspection_id,
        )

        self.assertEqual(can_pick, True)
        self.assertIsNone(next_allowed)

    def _insert_inspection(
        self,
        *,
        vessel_id: str,
        inspection_reference: str,
        planned_date: str,
        section_12_included: bool,
    ) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection (
                    vessel_id,
                    inspection_reference,
                    cycle_label,
                    state,
                    planned_date,
                    safety_officer_crew_id,
                    safety_officer_department,
                    assistant_crew_id,
                    assistant_department,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by,
                    created_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    vessel_id,
                    inspection_reference,
                    "Q2/2026",
                    "PLANNED",
                    planned_date,
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    section_12_included,
                    1,
                    False,
                    "tester",
                    f"{planned_date} 00:00:00",
                ],
            )
            return int(cursor.lastrowid)
