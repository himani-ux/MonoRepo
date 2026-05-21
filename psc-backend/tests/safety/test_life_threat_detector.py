from __future__ import annotations

from datetime import date
from types import SimpleNamespace
import unittest

from django.db import connection

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
    recreate_soi_tables,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.services.life_threat_detector import LifeThreatDetector
from apps.safety.views.soi_finding import SOIFindingListCreateView


def build_user(
    *,
    role_name: str = "CO",
    process_ids: list[str] | None = None,
    user_id: str = "co-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_002"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class LifeThreatDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SOIFindingListCreateView.as_view()
        self.detector = LifeThreatDetector()
        self._insert_area(area_id=8, area_name="Engine Control Room + Machinery Flat")
        self.inspection_id = self._insert_inspection()
        self._insert_selected_area(area_id=8)

    def test_detector_flags_life_threat_keywords(self) -> None:
        result = self.detector.scan(
            severity="LOW",
            title="Confined space gas leak",
            description="Crew found a gas leak inside a confined space before entry started.",
        )

        self.assertTrue(result.detected)
        self.assertIn("gas leak", result.matched_keywords)
        self.assertIn("confined space", result.matched_keywords)

    def test_life_threat_keywords_require_parallel_escalation_before_save(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 8,
                "checklist_unique_id": "SOI-UID-008",
                "description": "A gas leak was detected in a confined space next to energized equipment.",
                "photo_attachment_path": "vessel-7/soi/confined-space-gas-leak.jpg",
                "priority": "HIGH",
                "severity": "HIGH",
                "title": "Confined space gas leak",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("life_threat_escalation_target", response.data)

    def test_life_threat_near_miss_escalation_records_nudge_without_auto_creation(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 8,
                "checklist_unique_id": "SOI-UID-008",
                "description": "A gas leak was detected in a confined space next to energized equipment.",
                "life_threat_escalation_target": "NEAR_MISS",
                "photo_attachment_path": "vessel-7/soi/confined-space-gas-leak.jpg",
                "priority": "HIGH",
                "severity": "HIGH",
                "title": "Confined space gas leak",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["high_severity_nudge"]["life_threat_detected"])
        self.assertEqual(response.data["high_severity_nudge"]["life_threat_escalation_target"], "NEAR_MISS")
        self.assertEqual(response.data["high_severity_nudge"]["notifications_emitted"], 0)
        self.assertIsNone(response.data["incident_linked_id"])
        self.assertEqual(Incident.objects.count(), 0)

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

    def _insert_inspection(self) -> int:
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
                    "7",
                    "SOI/ABC/26/08",
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 1),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-008",
                    "2026-05-01 08:00:00",
                    "PDF",
                    False,
                    1,
                    False,
                    "co-7",
                ],
            )
            return int(cursor.lastrowid)

    def _insert_selected_area(self, *, area_id: int) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection_area (
                    inspection_id,
                    area_id,
                    inspected,
                    last_inspected_at,
                    notes,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [self.inspection_id, area_id, False, None, None, 1],
            )
