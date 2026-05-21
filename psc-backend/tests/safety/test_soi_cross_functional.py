from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi import SOIListCreateView


def build_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="co-7",
        username="co-7",
        role_name="CO",
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_001"],
        vessel_ids=["7"],
        is_global=False,
    )


class SOICrossFunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        recreate_cms_tables()
        self.factory = APIRequestFactory()
        self.view = SOIListCreateView.as_view()
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
            for crew_id, rank in (("co-7", "CO"), ("deck-7", "DECK_OFFICER")):
                cursor.execute(
                    """
                    INSERT INTO Crew_Onboarding_History (
                        crew_id,
                        vessel_id,
                        department,
                        rank,
                        is_current
                    ) VALUES (%s, '7', 'DECK', %s, 1)
                    """,
                    [crew_id, rank],
                )
                cursor.execute(
                    """
                    INSERT INTO HRM501 (
                        crew_id,
                        department,
                        rank
                    ) VALUES (%s, 'DECK', %s)
                    """,
                    [crew_id, rank],
                )

    def test_same_department_assistant_is_rejected(self) -> None:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "inspection_reference": "SOI/ABC/26/01",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "safety_officer_crew_id": "co-7",
                "assistant_crew_id": "deck-7",
                "area_ids": [3],
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("assistant_crew_id", response.data)
