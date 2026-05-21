from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django(root_urlconf="config.urls")

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SOIInspection
from apps.safety.views.dashboard import DashboardSOIComplianceView


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def build_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="dpa-1",
        username="dpa-1",
        role_name="DPA",
        form_ids=["SAF_F_015"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=False,
    )


class DashboardSOIComplianceViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_soi_tables()
        self.current_at = aware(2026, 4, 30, 12, 0)
        self.factory = APIRequestFactory()
        self.view = DashboardSOIComplianceView.as_view()

        SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/7/2026/001",
            cycle_label="Q2/2026",
            state=SOIInspection.State.REPORTED,
            planned_date=self.current_at.date(),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            created_by="co-7",
            updated_by="co-7",
            schema_version=1,
        )
        SOIInspection.objects.create(
            vessel_id="9",
            inspection_reference="SOI/9/2026/001",
            cycle_label="Q2/2026",
            state=SOIInspection.State.REPORTED,
            planned_date=self.current_at.date(),
            safety_officer_crew_id="co-9",
            safety_officer_department="DECK",
            assistant_crew_id="2e-9",
            assistant_department="ENGINE",
            created_by="co-9",
            updated_by="co-9",
            schema_version=1,
        )

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
                [3, "Navigating Bridge & Monkey Island", False, 3, True, "v1.0"],
            )
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
                [8, "Engine Control Room + Machinery Flat", False, 8, True, "v1.0"],
            )
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
                [
                    "7",
                    3,
                    True,
                    self.current_at - timedelta(days=20),
                    self.current_at + timedelta(days=70),
                    1,
                ],
            )
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
                [
                    "7",
                    8,
                    True,
                    self.current_at - timedelta(days=95),
                    self.current_at - timedelta(days=5),
                    1,
                ],
            )
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
                [
                    "9",
                    3,
                    True,
                    self.current_at - timedelta(days=10),
                    self.current_at + timedelta(days=80),
                    1,
                ],
            )
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
                [
                    "9",
                    8,
                    True,
                    self.current_at - timedelta(days=30),
                    self.current_at + timedelta(days=60),
                    1,
                ],
            )

    def test_dashboard_panel_view_returns_current_vessel_and_fleet_average(self) -> None:
        request = self.factory.get("/api/safety/dashboard/soi-compliance/?vessel_id=7")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["label"], "SOI Compliance %")
        self.assertEqual(response.data["current_vessel"]["display_value"], "50%")
        self.assertEqual(response.data["current_vessel"]["overdue_area_count"], 1)
        self.assertEqual(response.data["fleet_average"]["display_value"], "75%")
        self.assertEqual(response.data["fleet_average"]["vessel_count"], 2)

    def test_dashboard_panel_view_defaults_to_authenticated_vessel_scope(self) -> None:
        request = self.factory.get("/api/safety/dashboard/soi-compliance/")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["current_vessel"]["vessel_id"], "7")
