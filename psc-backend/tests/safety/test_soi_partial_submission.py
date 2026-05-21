from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi_finding import SOISubmitFindingsView


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


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class SOIPartialSubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SOISubmitFindingsView.as_view()
        self.current_at = aware(2026, 5, 6, 9, 30)
        self.inspection_id = self._insert_inspection()
        for area_id, area_name in (
            (3, "Navigating Bridge & Monkey Island"),
            (5, "Mooring Deck + Forward Station"),
            (8, "Engine Control Room + Machinery Flat"),
        ):
            self._insert_area(area_id=area_id, area_name=area_name)
            self._insert_selected_area(area_id=area_id)
            self._insert_area_map(area_id=area_id)

    def test_partial_submit_stamps_only_selected_areas_and_keeps_inspection_resumable(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/submit/",
            {"submitted_area_ids": [3, 5]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["inspection_id"], self.inspection_id)
        self.assertEqual(response.data["submitted_area_ids"], [3, 5])
        self.assertEqual(response.data["remaining_area_ids"], [8])
        self.assertEqual(response.data["checklist_unique_id"], "SOI-UID-008")
        self.assertEqual(response.data["state"], "DOWNLOADED")

        inspection_state = self._fetch_inspection_state()
        self.assertEqual(inspection_state["state"], "DOWNLOADED")
        self.assertIsNone(inspection_state["reported_at"])

        stamped_rows = self._fetch_area_rows()
        self.assertTrue(stamped_rows[3]["inspected"])
        self.assertTrue(stamped_rows[5]["inspected"])
        self.assertFalse(stamped_rows[8]["inspected"])
        self.assertIsNotNone(stamped_rows[3]["last_inspected_at"])
        self.assertIsNotNone(stamped_rows[5]["last_inspected_at"])
        self.assertIsNone(stamped_rows[8]["last_inspected_at"])

        area_map_rows = self._fetch_area_map_rows()
        self.assertIsNotNone(area_map_rows[3]["last_inspected_at"])
        self.assertIsNotNone(area_map_rows[5]["last_inspected_at"])
        self.assertIsNone(area_map_rows[8]["last_inspected_at"])
        self.assertIsNotNone(area_map_rows[3]["due_at"])
        self.assertIsNotNone(area_map_rows[5]["due_at"])
        self.assertIsNone(area_map_rows[8]["due_at"])

    def test_final_submit_marks_inspection_reported(self) -> None:
        first_request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/submit/",
            {"submitted_area_ids": [3, 5]},
            format="json",
        )
        force_authenticate(first_request, user=build_user())
        self.view(first_request, id=self.inspection_id)

        second_request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/submit/",
            {"submitted_area_ids": [8]},
            format="json",
        )
        force_authenticate(second_request, user=build_user())

        response = self.view(second_request, id=self.inspection_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["remaining_area_ids"], [])
        self.assertEqual(response.data["state"], "REPORTED")

        inspection_state = self._fetch_inspection_state()
        self.assertEqual(inspection_state["state"], "REPORTED")
        self.assertIsNotNone(inspection_state["reported_at"])

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
                    fieldwork_started_at,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "7",
                    "SOI/ABC/26/08",
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 5),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-008",
                    self.current_at - timedelta(days=1),
                    "PDF",
                    None,
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

    def _insert_area_map(self, *, area_id: int) -> None:
        with connection.cursor() as cursor:
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
                ["7", area_id, True, None, None, 1],
            )

    def _fetch_area_rows(self) -> dict[int, dict[str, object]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT area_id, inspected, last_inspected_at
                FROM vims_safety_soi_inspection_area
                WHERE inspection_id = %s
                ORDER BY area_id
                """,
                [self.inspection_id],
            )
            rows = cursor.fetchall()
        return {
            int(area_id): {
                "inspected": bool(inspected),
                "last_inspected_at": last_inspected_at,
            }
            for area_id, inspected, last_inspected_at in rows
        }

    def _fetch_area_map_rows(self) -> dict[int, dict[str, object]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT area_id, last_inspected_at, due_at
                FROM vims_safety_soi_vessel_area_map
                WHERE vessel_id = %s
                ORDER BY area_id
                """,
                ["7"],
            )
            rows = cursor.fetchall()
        return {
            int(area_id): {
                "last_inspected_at": last_inspected_at,
                "due_at": due_at,
            }
            for area_id, last_inspected_at, due_at in rows
        }

    def _fetch_inspection_state(self) -> dict[str, object]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT state, reported_at
                FROM vims_safety_soi_inspection
                WHERE id = %s
                """,
                [self.inspection_id],
            )
            row = cursor.fetchone()
        return {"state": row[0], "reported_at": row[1]}
