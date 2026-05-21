from __future__ import annotations

from types import SimpleNamespace
import uuid
import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi import SOIApplicabilityView, SOIDetailView, SOIListCreateView
from apps.safety.views.soi_pick_areas import SOIPickAreasView
from apps.safety.views.soi_trainees import SOITraineeView


def build_user(
    *,
    role_name: str,
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    user_id: str = "so-7",
):
    return SimpleNamespace(
        id=user_id,
        is_authenticated=True,
        username=user_id,
        role_name=role_name,
        safety_role_name=role_name,
        form_ids=["SAF_F_004"] if form_ids is None else form_ids,
        process_ids=["SAF_P_001"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class SOICrudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        recreate_cms_tables()
        self.factory = APIRequestFactory()
        self.list_create_view = SOIListCreateView.as_view()
        self.detail_view = SOIDetailView.as_view()
        self.applicability_view = SOIApplicabilityView.as_view()
        self.pick_areas_view = SOIPickAreasView.as_view()
        self.trainee_view = SOITraineeView.as_view()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=13, area_name="Cross-cutting Safety & Culture", section_12_flag=True)
        self._insert_crew(crew_id="co-7", vessel_id="7", department="DECK", rank="CO")
        self._insert_crew(crew_id="2e-7", vessel_id="7", department="ENGINE", rank="2/E")
        self._insert_crew(crew_id="cadet-7", vessel_id="7", department="DECK", rank="CADET")
        self._insert_crew(crew_id="cadet-8", vessel_id="8", department="DECK", rank="CADET")

    def test_so_can_create_planned_soi_and_read_it_back(self) -> None:
        create_request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "inspection_reference": "SOI/ABC/26/01",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "safety_officer_crew_id": "co-7",
                "assistant_crew_id": "2e-7",
                "area_ids": [3],
                "section_12_included": False,
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))

        create_response = self.list_create_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["state"], "PLANNED")
        self.assertEqual(create_response.data["inspection_reference"], "SOI/ABC/26/01")
        self.assertEqual(create_response.data["assistant_department"], "ENGINE")
        self.assertEqual(create_response.data["checklist_version"]["version_label"], "v1.0")
        self.assertEqual(create_response.data["selected_areas"][0]["area_id"], 3)

        detail_request = self.factory.get(f"/api/safety/soi/{create_response.data['id']}/")
        force_authenticate(detail_request, user=build_user(role_name="MASTER", process_ids=[], user_id="master-7"))

        detail_response = self.detail_view(detail_request, id=create_response.data["id"])

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["id"], create_response.data["id"])
        self.assertEqual(detail_response.data["assistant_department"], "ENGINE")
        self.assertEqual(detail_response.data["checklist_version"]["version_label"], "v1.0")

    def test_pick_areas_and_trainee_routes_update_existing_inspection(self) -> None:
        create_request = self.factory.post(
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
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)

        patch_areas_request = self.factory.patch(
            f"/api/safety/soi/{create_response.data['id']}/pick-areas/",
            {"area_ids": [3, 13], "section_12_included": True},
            format="json",
        )
        force_authenticate(patch_areas_request, user=build_user(role_name="CO", user_id="co-7"))
        patch_areas_response = self.pick_areas_view(patch_areas_request, id=create_response.data["id"])

        self.assertEqual(patch_areas_response.status_code, 200)
        self.assertEqual([row["area_id"] for row in patch_areas_response.data["selected_areas"]], [3, 13])

        put_trainees_request = self.factory.put(
            f"/api/safety/soi/{create_response.data['id']}/trainees/",
            {"trainee_crew_ids": ["cadet-7"]},
            format="json",
        )
        force_authenticate(put_trainees_request, user=build_user(role_name="CO", user_id="co-7"))
        put_trainees_response = self.trainee_view(put_trainees_request, id=create_response.data["id"])

        self.assertEqual(put_trainees_response.status_code, 200)
        self.assertEqual([row["crew_id"] for row in put_trainees_response.data["trainees"]], ["cadet-7"])

    def test_trainee_update_reuses_live_cms_validation(self) -> None:
        create_request = self.factory.post(
            "/api/safety/soi/",
            {
                "vessel_id": "7",
                "inspection_reference": "SOI/ABC/26/02",
                "cycle_label": "Q2/2026",
                "planned_date": "2026-05-01",
                "safety_officer_crew_id": "co-7",
                "assistant_crew_id": "2e-7",
                "area_ids": [3],
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)

        put_trainees_request = self.factory.put(
            f"/api/safety/soi/{create_response.data['id']}/trainees/",
            {"trainee_crew_ids": ["cadet-8"]},
            format="json",
        )
        force_authenticate(put_trainees_request, user=build_user(role_name="CO", user_id="co-7"))

        put_trainees_response = self.trainee_view(put_trainees_request, id=create_response.data["id"])

        self.assertEqual(put_trainees_response.status_code, 400)
        self.assertIn("trainee_crew_ids", put_trainees_response.data)

    def test_pick_areas_rejects_section12_if_another_inspection_already_carries_the_quarter(self) -> None:
        create_request = self.factory.post(
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
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)

        self._insert_inspection(
            inspection_reference="SOI/ABC/26/00",
            planned_date="2026-04-10",
            section_12_included=True,
        )

        patch_request = self.factory.patch(
            f"/api/safety/soi/{create_response.data['id']}/pick-areas/",
            {"area_ids": [3, 13], "section_12_included": True},
            format="json",
        )
        force_authenticate(patch_request, user=build_user(role_name="CO", user_id="co-7"))

        patch_response = self.pick_areas_view(patch_request, id=create_response.data["id"])

        self.assertEqual(patch_response.status_code, 400)
        self.assertEqual(
            patch_response.data["section_12_included"][0],
            "Section 12 'Cross-cutting Safety & Culture' evaluated once per 3-month cycle (D-GAP-M23). This cycle already covered.",
        )

    def test_applicability_route_lists_default_true_and_patch_creates_pending_request(self) -> None:
        list_request = self.factory.get("/api/safety/soi/applicability/?vessel_id=7")
        force_authenticate(
            list_request,
            user=build_user(
                role_name="MASTER",
                form_ids=["SAF_F_013"],
                process_ids=["SAF_P_016"],
                user_id="master-7",
            ),
        )

        list_response = self.applicability_view(list_request)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 2)
        self.assertEqual(list_response.data[0]["area_id"], 3)
        self.assertEqual(list_response.data[0]["applicable"], True)

        patch_request = self.factory.patch(
            "/api/safety/soi/applicability/",
            {
                "vessel_id": "7",
                "area_id": 3,
                "applicable": False,
                "reason": (
                    "Cargo oil room does not exist on this vessel class. The approved GA plan, "
                    "class records, and SMS arrangement for this vessel variant confirm the "
                    "forward station is structurally absent, so leaving the area active would "
                    "distort the SOI compliance cycle."
                ),
                "master_signature": "Captain Example|device-abc",
            },
            format="json",
        )
        force_authenticate(
            patch_request,
            user=build_user(
                role_name="MASTER",
                form_ids=["SAF_F_013"],
                process_ids=["SAF_P_016"],
                user_id="master-7",
            ),
        )

        patch_response = self.applicability_view(patch_request)

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data["status"], "PENDING_APPROVAL")
        self.assertEqual(patch_response.data["requested_applicable"], False)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vims_safety_soi_applicability_log")
            log_count = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM vims_safety_soi_vessel_area_map
                WHERE vessel_id = %s AND area_id = %s
                """,
                ["7", 3],
            )
            map_count = cursor.fetchone()[0]

        self.assertEqual(log_count, 1)
        self.assertEqual(map_count, 0)

    def _insert_area(self, *, area_id: int, area_name: str, section_12_flag: bool = False) -> None:
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
