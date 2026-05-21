from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi_applicability_approve import SOIApplicabilityApproveView
from apps.safety.views.soi_applicability_request import SOIApplicabilityRequestView


def build_user(
    *,
    role_name: str,
    form_ids: list[str],
    process_ids: list[str],
    user_id: str,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids,
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class SOIApplicabilityWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        recreate_cms_tables()
        self.factory = APIRequestFactory()
        self.request_view = SOIApplicabilityRequestView.as_view()
        self.approve_view = SOIApplicabilityApproveView.as_view()
        self._insert_area(area_id=5, area_name="Mooring Deck + Forward Station")
        self._insert_area(area_id=13, area_name="Cross-cutting Safety & Culture", section_12_flag=True)
        self._insert_crew(crew_id="co-7", vessel_id="7", department="DECK", rank="CO")
        self._insert_crew(crew_id="2e-7", vessel_id="7", department="ENGINE", rank="2/E")
        self.inspection_id = self._insert_inspection()

    def test_request_then_approve_updates_vessel_map_and_audit_log(self) -> None:
        request_payload = {
            "area_id": 5,
            "new_applicable": False,
            "reason": (
                "The vessel's approved arrangement plan and class documentation confirm that the "
                "forward mooring deck layout represented in Area 5 is not installed on this ship. "
                "Keeping the area active would create a false overdue signal in the 90-day SOI cycle."
            ),
            "master_signature": "Captain Rao|bridge-ipad-7",
        }
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/applicability/request/",
            request_payload,
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="MASTER",
                form_ids=["SAF_F_013"],
                process_ids=["SAF_P_016"],
                user_id="master-7",
            ),
        )

        request_response = self.request_view(request, id=self.inspection_id)

        self.assertEqual(request_response.status_code, 201)
        self.assertEqual(request_response.data["status"], "PENDING_APPROVAL")
        self.assertEqual(request_response.data["requested_applicable"], False)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM vims_safety_soi_vessel_area_map
                WHERE vessel_id = %s AND area_id = %s
                """,
                ["7", 5],
            )
            self.assertEqual(cursor.fetchone()[0], 0)

        approve_payload = {
            "area_id": 5,
            "dpa_decision": "APPROVED",
            "reason": (
                "Approved after reviewing the vessel GA plan and class attachment. Keep the "
                "area excluded until the vessel arrangement changes."
            ),
            "dpa_signature": "DPA Menon|office-lt-4",
        }
        approve_request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/applicability/approve/",
            approve_payload,
            format="json",
        )
        force_authenticate(
            approve_request,
            user=build_user(
                role_name="DPA",
                form_ids=["SAF_F_013"],
                process_ids=["SAF_P_017"],
                user_id="dpa-1",
            ),
        )

        approve_response = self.approve_view(approve_request, id=self.inspection_id)

        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.data["decision"], "APPROVED")
        self.assertEqual(approve_response.data["applicable"], False)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT applicable
                FROM vims_safety_soi_vessel_area_map
                WHERE vessel_id = %s AND area_id = %s
                """,
                ["7", 5],
            )
            map_row = cursor.fetchone()
            cursor.execute(
                """
                SELECT reason, dpa_approved_by, dpa_signature, dpa_decision
                FROM vims_safety_soi_applicability_log
                WHERE vessel_id = %s AND area_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                ["7", 5],
            )
            log_row = cursor.fetchone()

        self.assertEqual(map_row[0], False)
        self.assertIn("forward mooring deck layout represented in Area 5 is not installed", log_row[0])
        self.assertIn("Approved after reviewing the vessel GA plan", log_row[0])
        self.assertEqual(log_row[1], "dpa-1")
        self.assertEqual(log_row[2], "DPA Menon|office-lt-4")
        self.assertEqual(log_row[3], "APPROVED")

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
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by,
                    created_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "7",
                    "SOI/ABC/26/11",
                    "Q2/2026",
                    "PLANNED",
                    "2026-05-02",
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    False,
                    1,
                    False,
                    "tester",
                    "2026-05-02 00:00:00",
                ],
            )
            return int(cursor.lastrowid)
