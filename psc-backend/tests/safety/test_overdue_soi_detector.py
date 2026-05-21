from __future__ import annotations

from datetime import datetime
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone

from apps.safety.services.overdue_soi_blocker import OverdueSOIBlocker


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class OverdueSOIBlockerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.service = OverdueSOIBlocker(now_func=lambda: aware(2026, 4, 28, 12, 0))
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=5, area_name="Environment")

    def test_returns_only_applicable_areas_past_due_with_overdue_day_count(self) -> None:
        self._insert_area_map(
            vessel_id="7",
            area_id=3,
            last_inspected_at="2026-01-24 08:00:00",
            due_at="2026-04-23 08:00:00",
            applicable=True,
        )
        self._insert_area_map(
            vessel_id="7",
            area_id=5,
            last_inspected_at="2026-03-15 08:00:00",
            due_at="2026-06-13 08:00:00",
            applicable=True,
        )
        self._insert_area_map(
            vessel_id="7",
            area_id=9,
            last_inspected_at="2026-01-10 08:00:00",
            due_at="2026-04-10 08:00:00",
            applicable=False,
        )

        overdue = self.service.check_overdue_soi("7")

        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]["area_id"], 3)
        self.assertEqual(overdue[0]["area_name"], "Navigating Bridge & Monkey Island")
        self.assertEqual(overdue[0]["overdue_days"], 5)
        self.assertEqual(overdue[0]["message"], "Area 3 overdue by 5 days")

    def test_sorts_oldest_due_area_first(self) -> None:
        self._insert_area_map(
            vessel_id="7",
            area_id=3,
            last_inspected_at="2026-01-24 08:00:00",
            due_at="2026-04-23 08:00:00",
            applicable=True,
        )
        self._insert_area_map(
            vessel_id="7",
            area_id=5,
            last_inspected_at="2026-01-20 08:00:00",
            due_at="2026-04-19 08:00:00",
            applicable=True,
        )

        overdue = self.service.check_overdue_soi("7")

        self.assertEqual([item["area_id"] for item in overdue], [5, 3])

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

    def _insert_area_map(
        self,
        *,
        vessel_id: str,
        area_id: int,
        last_inspected_at: str | None,
        due_at: str | None,
        applicable: bool,
    ) -> None:
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
                [vessel_id, area_id, applicable, last_inspected_at, due_at, 1],
            )
