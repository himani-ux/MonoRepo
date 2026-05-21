from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone

from apps.safety.services.soi_compliance_calculator import SOIComplianceCalculator


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class SOIComplianceCalculatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.current_at = aware(2026, 4, 29, 12, 0)
        self.service = SOIComplianceCalculator(now_func=lambda: self.current_at)
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")

    def test_green_when_last_inspection_is_79_days_old(self) -> None:
        self._insert_area_map(vessel_id="7", area_id=3, last_inspected_at=self.current_at - timedelta(days=79))

        summary = self.service.get_summary("7")

        self.assertEqual(summary["status"], "GREEN")
        self.assertEqual(summary["compliance_percent"], 100)
        self.assertEqual(summary["display_value"], "100%")
        self.assertEqual(summary["amber_area_count"], 0)
        self.assertEqual(summary["overdue_area_count"], 0)
        self.assertEqual(summary["areas"][0]["status"], "GREEN")
        self.assertEqual(summary["areas"][0]["days_since_last_inspection"], 79)

    def test_amber_when_last_inspection_is_80_days_old(self) -> None:
        self._insert_area_map(vessel_id="7", area_id=3, last_inspected_at=self.current_at - timedelta(days=80))

        summary = self.service.get_summary("7")

        self.assertEqual(summary["status"], "AMBER")
        self.assertEqual(summary["compliance_percent"], 100)
        self.assertEqual(summary["amber_area_count"], 1)
        self.assertEqual(summary["overdue_area_count"], 0)
        self.assertEqual(summary["areas"][0]["status"], "AMBER")
        self.assertEqual(summary["areas"][0]["days_until_due"], 10)

    def test_amber_when_last_inspection_is_89_days_old(self) -> None:
        self._insert_area_map(vessel_id="7", area_id=3, last_inspected_at=self.current_at - timedelta(days=89))

        summary = self.service.get_summary("7")

        self.assertEqual(summary["status"], "AMBER")
        self.assertEqual(summary["compliance_percent"], 100)
        self.assertEqual(summary["amber_area_count"], 1)
        self.assertEqual(summary["overdue_area_count"], 0)
        self.assertEqual(summary["areas"][0]["status"], "AMBER")
        self.assertEqual(summary["areas"][0]["days_until_due"], 1)

    def test_red_when_last_inspection_is_90_days_old(self) -> None:
        self._insert_area_map(vessel_id="7", area_id=3, last_inspected_at=self.current_at - timedelta(days=90))

        summary = self.service.get_summary("7")
        overdue = self.service.list_overdue_areas("7")

        self.assertEqual(summary["status"], "RED")
        self.assertEqual(summary["compliance_percent"], 0)
        self.assertEqual(summary["display_value"], "0%")
        self.assertEqual(summary["amber_area_count"], 0)
        self.assertEqual(summary["overdue_area_count"], 1)
        self.assertEqual(summary["areas"][0]["status"], "RED")
        self.assertEqual(summary["areas"][0]["days_overdue"], 1)
        self.assertEqual(overdue[0]["message"], "Area 3 overdue by 1 day")

    def test_new_vessel_returns_na_awaiting_first_cycle(self) -> None:
        summary = self.service.get_summary("7")

        self.assertEqual(summary["status"], "NA")
        self.assertIsNone(summary["compliance_percent"])
        self.assertEqual(summary["display_value"], "N/A - awaiting first cycle")
        self.assertEqual(summary["applicable_area_count"], 1)
        self.assertEqual(summary["inspected_area_count"], 0)
        self.assertEqual(summary["overdue_area_count"], 0)
        self.assertEqual(summary["areas"][0]["status"], "NA")

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

    def _insert_area_map(self, *, vessel_id: str, area_id: int, last_inspected_at) -> None:
        due_at = last_inspected_at + timedelta(days=90)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [vessel_id, area_id, True, last_inspected_at, due_at, 1],
            )
