from __future__ import annotations

from datetime import date, datetime
import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone

from apps.safety.services.crew_rotation_coverage import CrewRotationCoverageService


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class CrewRotationCoverageServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        recreate_cms_tables()
        self.reference_at = aware(2026, 5, 6, 9, 30)
        self.service = CrewRotationCoverageService(now_func=lambda: self.reference_at)

        for crew_id, department, rank in (
            ("cadet-1", "DECK", "CADET"),
            ("oiler-2", "ENGINE", "OILER"),
            ("ab-3", "DECK", "AB"),
            ("motorman-4", "ENGINE", "MOTORMAN"),
            ("former-crew", "DECK", "AB"),
        ):
            self._insert_crew(
                crew_id=crew_id,
                vessel_id="7",
                department=department,
                rank=rank,
                is_current=crew_id != "former-crew",
            )

        first_inspection = self._insert_inspection(
            inspection_reference="SOI/ABC/26/12",
            closed_at=aware(2026, 2, 14, 11, 0),
            planned_date=date(2026, 2, 13),
        )
        second_inspection = self._insert_inspection(
            inspection_reference="SOI/ABC/26/13",
            closed_at=aware(2026, 4, 25, 16, 15),
            planned_date=date(2026, 4, 24),
        )
        old_inspection = self._insert_inspection(
            inspection_reference="SOI/ABC/25/01",
            closed_at=aware(2025, 3, 1, 9, 0),
            planned_date=date(2025, 2, 28),
        )

        self._insert_trainee(inspection_id=first_inspection, crew_id="cadet-1", trainee_slot=1)
        self._insert_trainee(inspection_id=first_inspection, crew_id="oiler-2", trainee_slot=2)
        self._insert_trainee(inspection_id=second_inspection, crew_id="cadet-1", trainee_slot=1)
        self._insert_trainee(inspection_id=old_inspection, crew_id="former-crew", trainee_slot=1)

    def test_strict_formula_counts_distinct_trainees_in_closed_soi_events_over_12_months(self) -> None:
        summary = self.service.get_summary(vessel_id="7")

        self.assertEqual(summary["vessel_id"], "7")
        self.assertEqual(summary["total_active_crew"], 4)
        self.assertEqual(summary["accompanied_crew_count"], 2)
        self.assertEqual(summary["coverage_percent"], 50)
        self.assertEqual(summary["display_value"], "50%")
        self.assertEqual(summary["window_days"], 365)
        self.assertEqual(summary["crew"][0]["crew_id"], "cadet-1")
        self.assertEqual(summary["crew"][0]["inspections_accompanied"], 2)
        self.assertEqual(summary["crew"][1]["crew_id"], "oiler-2")
        self.assertEqual(summary["crew"][1]["inspections_accompanied"], 1)

    def _insert_crew(
        self,
        *,
        crew_id: str,
        vessel_id: str,
        department: str,
        rank: str,
        is_current: bool,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Crew_Onboarding_History (
                    crew_id,
                    vessel_id,
                    department,
                    rank,
                    is_current
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                [crew_id, vessel_id, department, rank, is_current],
            )
            cursor.execute(
                """
                INSERT INTO HRM501 (
                    crew_id,
                    department,
                    rank
                ) VALUES (%s, %s, %s)
                """,
                [crew_id, department, rank],
            )

    def _insert_inspection(
        self,
        *,
        inspection_reference: str,
        closed_at,
        planned_date: date,
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
                    master_crew_id,
                    checklist_unique_id,
                    checklist_generated_at,
                    checklist_format,
                    reported_at,
                    closed_at,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by,
                    created_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "7",
                    inspection_reference,
                    "Q2/2026",
                    "CLOSED",
                    planned_date,
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    f"UID-{inspection_reference}",
                    closed_at,
                    "PDF",
                    closed_at,
                    closed_at,
                    False,
                    1,
                    False,
                    "tester",
                    closed_at,
                ],
            )
            return int(cursor.lastrowid)

    def _insert_trainee(self, *, inspection_id: int, crew_id: str, trainee_slot: int) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_trainee (
                    inspection_id,
                    crew_id,
                    trainee_slot,
                    schema_version
                ) VALUES (%s, %s, %s, %s)
                """,
                [inspection_id, crew_id, trainee_slot, 1],
            )
