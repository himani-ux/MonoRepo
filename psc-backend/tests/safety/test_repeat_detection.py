from __future__ import annotations

from datetime import date, timedelta
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone

from apps.safety.models import SOIFinding
from apps.safety.services.repeat_finding_detector import RepeatFindingDetector


class RepeatFindingDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.inspection_id = self._insert_inspection(vessel_id="7", reference="SOI/ABC/26/08")
        self.other_inspection_id = self._insert_inspection(vessel_id="8", reference="SOI/XYZ/26/03")
        self.detector = RepeatFindingDetector(now_func=lambda: timezone.now())

    def test_same_vessel_area_and_item_closed_within_180_days_flags_repeat(self) -> None:
        closed_at = timezone.now() - timedelta(days=30)
        previous = SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=5,
            item_id=3001,
            title="Drain cover unsecured",
            description="Bilge drain cover was left unsecured after cleaning.",
            severity="MED",
            priority="MED",
            status=SOIFinding.Status.CLOSED,
            created_by="co-7",
            master_approved_by="master-7",
            master_approved_at=closed_at,
            closed_at=closed_at,
        )
        current = SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=5,
            item_id=3001,
            title="Drain cover unsecured again",
            description="The bilge drain cover was again found unsecured after cleaning.",
            severity="MED",
            priority="MED",
            status=SOIFinding.Status.OPEN,
            created_by="co-7",
        )

        result = self.detector.detect(current, reference_at=timezone.now())

        self.assertTrue(result.is_repeat)
        self.assertEqual(result.occurrence_count, 2)
        self.assertEqual(result.badge_text, "Repeat - 2nd occurrence")
        self.assertEqual(result.previous_finding_id, previous.pk)
        self.assertIsNotNone(result.previous_closed_at)

    def test_different_vessel_or_missing_item_id_does_not_flag_repeat(self) -> None:
        SOIFinding.objects.create(
            inspection_id=self.other_inspection_id,
            area_id=5,
            item_id=3001,
            title="Drain cover unsecured",
            description="Other vessel.",
            severity="MED",
            priority="MED",
            status=SOIFinding.Status.CLOSED,
            created_by="co-8",
            master_approved_by="master-8",
            master_approved_at=timezone.now() - timedelta(days=20),
            closed_at=timezone.now() - timedelta(days=20),
        )
        current = SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=5,
            item_id=None,
            title="No checklist item mapping",
            description="Cannot prove repeat against a missing item id.",
            severity="LOW",
            priority="LOW",
            status=SOIFinding.Status.OPEN,
            created_by="co-7",
        )

        result = self.detector.detect(current, reference_at=timezone.now())

        self.assertFalse(result.is_repeat)
        self.assertIsNone(result.badge_text)
        self.assertEqual(result.occurrence_count, 1)

    def test_same_area_and_item_without_similar_description_does_not_flag_repeat(self) -> None:
        closed_at = timezone.now() - timedelta(days=12)
        SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=5,
            item_id=3001,
            title="Drain cover unsecured",
            description="Bilge drain cover was left unsecured after cleaning.",
            severity="MED",
            priority="MED",
            status=SOIFinding.Status.CLOSED,
            created_by="co-7",
            master_approved_by="master-7",
            master_approved_at=closed_at,
            closed_at=closed_at,
        )
        current = SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=5,
            item_id=3001,
            title="Temperature log gap",
            description="Galley refrigerator temperature log was missing for the weekly review.",
            severity="LOW",
            priority="LOW",
            status=SOIFinding.Status.OPEN,
            created_by="co-7",
        )

        result = self.detector.detect(current, reference_at=timezone.now())

        self.assertFalse(result.is_repeat)
        self.assertEqual(result.occurrence_count, 1)
        self.assertIsNone(result.previous_finding_id)

    def _insert_inspection(self, *, vessel_id: str, reference: str) -> int:
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
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    vessel_id,
                    reference,
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 1),
                    f"co-{vessel_id}",
                    "DECK",
                    f"2e-{vessel_id}",
                    "ENGINE",
                    f"master-{vessel_id}",
                    f"SOI-{vessel_id}-UID-001",
                    "2026-05-01 08:00:00",
                    "PDF",
                    False,
                    1,
                    False,
                    f"co-{vessel_id}",
                ],
            )
            return int(cursor.lastrowid)
