from __future__ import annotations

from types import SimpleNamespace
import uuid
import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi import SOIDetailView, SOIListCreateView
from apps.safety.views.soi_checklist_version import SOIActiveChecklistVersionView
from apps.safety.views.soi_create import SOICreateConfigView, SOISection12StatusView
from apps.safety.views.soi_officer_setting import SOIOfficerSettingView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "co-7",
    vessel_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_001"] if process_ids is None else process_ids,
        vessel_ids=["7"] if vessel_ids is None else vessel_ids,
        is_global=False,
    )


class SOICreateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        recreate_cms_tables()
        self.factory = APIRequestFactory()
        self.create_config_view = SOICreateConfigView.as_view()
        self.section12_status_view = SOISection12StatusView.as_view()
        self.active_version_view = SOIActiveChecklistVersionView.as_view()
        self.list_create_view = SOIListCreateView.as_view()
        self.detail_view = SOIDetailView.as_view()
        self.officer_setting_view = SOIOfficerSettingView.as_view()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=13, area_name="Cross-cutting Safety & Culture", section_12_flag=True)
        self._insert_crew(crew_id="co-7", vessel_id="7", department="DECK", rank="CO")
        self._insert_crew(crew_id="2e-7", vessel_id="7", department="ENGINE", rank="2/E")
        self._insert_crew(crew_id="cadet-7", vessel_id="7", department="DECK", rank="CADET")

    def test_create_config_returns_applicable_areas_and_cross_functional_assistants(self) -> None:
        request = self.factory.get("/api/safety/soi/create/?vessel_id=7&safety_officer_crew_id=co-7")
        force_authenticate(request, user=build_user(role_name="CO"))

        response = self.create_config_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["max_trainees"], 3)
        self.assertEqual([row["area_id"] for row in response.data["areas"]], [3, 13])
        self.assertEqual(response.data["checklist_version"]["version_label"], "v1.0")
        self.assertEqual(response.data["safety_officer"]["department"], "DECK")
        self.assertEqual([row["crew_id"] for row in response.data["assistant_candidates"]], ["2e-7"])
        self.assertEqual([row["crew_id"] for row in response.data["trainee_candidates"]], ["cadet-7", "2e-7"])
        self.assertEqual(response.data["section_12_status"]["covered_this_cycle"], False)
        self.assertEqual(response.data["section_12_status"]["prompt_required"], True)

    def test_section12_status_route_reports_current_quarter_coverage(self) -> None:
        self._insert_inspection(
            inspection_reference="SOI/ABC/26/00",
            planned_date="2026-04-10",
            section_12_included=True,
        )
        request = self.factory.get("/api/safety/soi/section-12-status/?vessel_id=7&at_date=2026-05-01")
        force_authenticate(request, user=build_user(role_name="CO"))

        response = self.section12_status_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cycle_label"], "Q2/2026")
        self.assertEqual(response.data["covered_this_cycle"], True)
        self.assertEqual(response.data["next_allowed_date"], "2026-07-01")
        self.assertEqual(response.data["covered_by_inspection_reference"], "SOI/ABC/26/00")

    def test_active_checklist_version_route_returns_seeded_version(self) -> None:
        request = self.factory.get("/api/safety/master/soi-checklist-version/active/")
        force_authenticate(request, user=build_user(role_name="CO"))

        response = self.active_version_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["version_label"], "v1.0")
        self.assertEqual(response.data["active"], True)

    def test_so_can_create_planned_soi_with_area_and_trainee_rows(self) -> None:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "inspection_reference": "SOI/ABC/26/01",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "safety_officer_crew_id": "co-7",
                "assistant_crew_id": "2e-7",
                "trainee_crew_ids": ["cadet-7"],
                "area_ids": [3, 13],
                "section_12_included": True,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="CO"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["safety_officer_department"], "DECK")
        self.assertEqual(response.data["assistant_department"], "ENGINE")
        self.assertIsNone(response.data["checklist_unique_id"])
        self.assertIsNone(response.data["checklist_generated_at"])
        self.assertEqual(response.data["checklist_version"]["version_label"], "v1.0")
        self.assertEqual([row["area_id"] for row in response.data["selected_areas"]], [3, 13])
        self.assertEqual([row["crew_id"] for row in response.data["trainees"]], ["cadet-7"])

        detail_request = self.factory.get(f"/api/safety/soi/{response.data['id']}/")
        force_authenticate(detail_request, user=build_user(role_name="MASTER", process_ids=[], user_id="master-7"))

        detail_response = self.detail_view(detail_request, id=response.data["id"])

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["section_12_included"], True)
        self.assertEqual(detail_response.data["checklist_version"]["version_label"], "v1.0")
        self.assertEqual(len(detail_response.data["selected_areas"]), 2)
        self.assertEqual(detail_response.data["trainees"][0]["crew_id"], "cadet-7")

    def test_generated_reference_uses_short_vessel_code_for_uuid_scope(self) -> None:
        vessel_id = "EF9029C2-A192-EF11-A9F2-933342524037"
        self._insert_vessel(vessel_id=vessel_id, vessel_code="KSM01")
        self._insert_crew(
            crew_id="co-uuid",
            vessel_id=vessel_id,
            department="Deck Department",
            rank="CO",
        )
        self._insert_crew(
            crew_id="2e-uuid",
            vessel_id=vessel_id,
            department="Engine Department",
            rank="2/E",
        )
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": vessel_id,
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "assistant_crew_id": "2e-uuid",
                "area_ids": [3],
                "section_12_included": False,
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="CO", user_id="co-uuid", vessel_ids=[vessel_id]),
        )

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["inspection_reference"], "SOI/KSM01/26/001")
        self.assertLessEqual(len(response.data["inspection_reference"]), 32)
        self.assertEqual(response.data["safety_officer_department"], "DECK")
        self.assertEqual(response.data["assistant_department"], "ENGINE")

    def test_non_so_cannot_create_soi(self) -> None:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "assistant_crew_id": "2e-7",
                "area_ids": [3],
                "section_12_included": False,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="FM", user_id="fm-1"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("role", response.data)

    def test_spoofed_safety_officer_crew_id_is_rejected(self) -> None:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "safety_officer_crew_id": "2e-7",
                "assistant_crew_id": "2e-7",
                "area_ids": [3],
                "section_12_included": False,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("safety_officer_crew_id", response.data)

    def test_trainee_must_be_live_cms_crew_and_not_assistant_or_so(self) -> None:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "assistant_crew_id": "2e-7",
                "area_ids": [3],
                "section_12_included": False,
                "trainee_crew_ids": ["missing-7"],
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("trainee_crew_ids", response.data)

    def test_2e_requires_master_approved_alternate_toggle(self) -> None:
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "assistant_crew_id": "co-7",
                "area_ids": [3],
                "section_12_included": False,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="2/E", user_id="2e-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("safety_officer_crew_id", response.data)

    def test_master_can_enable_2e_alternate_and_2e_can_create_soi(self) -> None:
        setting_request = self.factory.patch(
            "/api/safety/soi/officer-setting/?vessel_id=7",
            {
                "alternate_enabled": True,
                "alternate_so_crew_id": "2e-7",
                "reason": "CO on leave",
            },
            format="json",
        )
        force_authenticate(
            setting_request,
            user=build_user(role_name="MASTER", user_id="master-7", process_ids=["SAF_P_016"]),
        )

        setting_response = self.officer_setting_view(setting_request)

        self.assertEqual(setting_response.status_code, 200)
        self.assertEqual(setting_response.data["alternate_enabled"], True)
        self.assertEqual(setting_response.data["alternate_so_crew_id"], "2e-7")

        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "assistant_crew_id": "co-7",
                "area_ids": [3],
                "section_12_included": False,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="2/E", user_id="2e-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["safety_officer_crew_id"], "2e-7")
        self.assertEqual(response.data["safety_officer_department"], "ENGINE")
        self.assertEqual(response.data["assistant_department"], "DECK")

    def test_create_rejects_second_section12_assignment_in_same_quarter(self) -> None:
        self._insert_inspection(
            inspection_reference="SOI/ABC/26/00",
            planned_date="2026-04-10",
            section_12_included=True,
        )
        request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "inspection_reference": "SOI/ABC/26/01",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "safety_officer_crew_id": "co-7",
                "assistant_crew_id": "2e-7",
                "area_ids": [3, 13],
                "section_12_included": True,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="CO"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["section_12_included"][0],
            "Section 12 'Cross-cutting Safety & Culture' evaluated once per 3-month cycle (D-GAP-M23). This cycle already covered.",
        )

    def _insert_area(
        self,
        *,
        area_id: int,
        area_name: str,
        section_12_flag: bool = False,
    ) -> None:
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
                [area_id, area_name, section_12_flag, area_id, True, "v1.0"],
            )

    def _insert_vessel(self, *, vessel_id: str, vessel_code: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS VesselData (
                    id VARCHAR(64) PRIMARY KEY,
                    vesselCode VARCHAR(16) NULL,
                    vesselName VARCHAR(128) NULL,
                    is_deleted BOOLEAN NULL DEFAULT 0
                )
                """
            )
            cursor.execute(
                "DELETE FROM VesselData WHERE id = %s",
                [vessel_id],
            )
            cursor.execute(
                """
                INSERT INTO VesselData (
                    id,
                    vesselCode,
                    vesselName,
                    is_deleted
                ) VALUES (%s, %s, %s, %s)
                """,
                [vessel_id, vessel_code, vessel_code, False],
            )

    def _insert_crew(
        self,
        *,
        crew_id: str,
        vessel_id: str,
        department: str,
        rank: str,
        is_current: bool = True,
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
        planned_date: str,
        section_12_included: bool,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection (
                    public_id,
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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    "7",
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
