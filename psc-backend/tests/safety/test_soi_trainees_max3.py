from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi import SOIListCreateView
from apps.safety.views.soi_trainees import SOITraineeView


def build_user(user_id: str = "co-7") -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name="CO",
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_001"],
        vessel_ids=["7"],
        is_global=False,
    )


class SOITraineeLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        recreate_cms_tables()
        self.factory = APIRequestFactory()
        self.list_create_view = SOIListCreateView.as_view()
        self.trainee_view = SOITraineeView.as_view()
        self._insert_area()
        self._insert_crew("co-7", "DECK", "CO")
        self._insert_crew("2e-7", "ENGINE", "2/E")
        self._insert_crew("cadet-1", "DECK", "CADET")
        self._insert_crew("cadet-2", "ENGINE", "CADET")
        self._insert_crew("cadet-3", "DECK", "CADET")
        self._insert_crew("cadet-4", "ENGINE", "CADET")
        self.inspection_id = self._create_inspection()

    def test_create_rejects_more_than_three_trainees(self) -> None:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "inspection_reference": "SOI/ABC/26/02",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-04",
                "safety_officer_crew_id": "co-7",
                "assistant_crew_id": "2e-7",
                "area_ids": [3],
                "trainee_crew_ids": ["cadet-1", "cadet-2", "cadet-3", "cadet-4"],
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("trainee_crew_ids", response.data)

    def test_trainee_route_rejects_more_than_three_trainees(self) -> None:
        request = self.factory.put(
            f"/api/safety/soi/{self.inspection_id}/trainees/",
            {"trainee_crew_ids": ["cadet-1", "cadet-2", "cadet-3", "cadet-4"]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.trainee_view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("trainee_crew_ids", response.data)

    def _create_inspection(self) -> int:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "inspection_reference": "SOI/ABC/26/01",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "safety_officer_crew_id": "co-7",
                "assistant_crew_id": "2e-7",
                "area_ids": [3],
            },
            format="json",
        )
        force_authenticate(request, user=build_user())
        response = self.list_create_view(request)
        self.assertEqual(response.status_code, 201)
        return int(response.data["id"])

    def _insert_area(self) -> None:
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
                ) VALUES (3, 'Navigating Bridge & Monkey Island', 0, 3, 1, 'v1.0')
                """
            )

    def _insert_crew(self, crew_id: str, department: str, rank: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Crew_Onboarding_History (
                    crew_id,
                    vessel_id,
                    department,
                    rank,
                    is_current
                ) VALUES (%s, '7', %s, %s, 1)
                """,
                [crew_id, department, rank],
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
