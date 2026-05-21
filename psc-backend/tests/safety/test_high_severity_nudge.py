from __future__ import annotations

from datetime import date
from types import SimpleNamespace
import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_soi_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, SafetyFieldHistory
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


class HighSeverityNudgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SOIFindingListCreateView.as_view()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self.inspection_id = self._insert_inspection()
        self._insert_selected_area(area_id=3)

    def test_high_severity_keep_soi_only_requires_reason(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Bridge emergency marker was unreadable during the round.",
                "incident_worthy_action": "KEEP_SOI_ONLY",
                "photo_attachment_path": "vessel-7/soi/bridge-emergency-marker.jpg",
                "priority": "HIGH",
                "severity": "HIGH",
                "title": "Bridge emergency marker unreadable",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("incident_worthy_reason", response.data)

    def test_high_severity_create_incident_records_prompt_without_auto_creating_incident(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Emergency escape marker was faded and not readable in low light.",
                "incident_worthy_action": "CREATE_INCIDENT",
                "photo_attachment_path": "vessel-7/soi/escape-marker-faded.jpg",
                "priority": "HIGH",
                "severity": "HIGH",
                "title": "Emergency escape marker faded",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["high_severity_nudge"]["required"])
        self.assertEqual(response.data["high_severity_nudge"]["incident_worthy_action"], "CREATE_INCIDENT")
        self.assertIsNone(response.data["incident_linked_id"])
        self.assertIsNone(response.data["incident_linked_number"])
        self.assertEqual(Incident.objects.count(), 0)

        history_fields = set(
            SafetyFieldHistory.objects.filter(
                parent_table="vims_safety_soi_finding",
                parent_id=response.data["id"],
            ).values_list("field_name", flat=True)
        )
        self.assertIn("incident_worthy_action", history_fields)
        self.assertNotIn("incident_linked_id", history_fields)
        self.assertNotIn("incident_linked_number", history_fields)

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
                    "SOI/ABC/26/07",
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 1),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-007",
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
