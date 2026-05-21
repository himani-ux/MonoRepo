from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SafetyFieldHistory
from apps.safety.services.crew_rotation_coverage import CrewRotationCoverageService
from apps.safety.services.soi_close_service import SOICloseService
from apps.safety.views.soi_close import SOICloseView


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def build_user(
    *,
    role_name: str = "MASTER",
    process_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_004"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class _FixedSOICloseService(SOICloseService):
    fixed_now = aware(2026, 5, 6, 9, 30)

    def __init__(self) -> None:
        super().__init__(
            now_func=lambda: self.fixed_now,
            crew_rotation_service=CrewRotationCoverageService(now_func=lambda: self.fixed_now),
        )


class _FixedSOICloseView(SOICloseView):
    close_service_class = _FixedSOICloseService


class SOICloseViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        recreate_cms_tables()
        self.factory = APIRequestFactory()
        self.view = _FixedSOICloseView.as_view()
        self.closed_at = _FixedSOICloseService.fixed_now
        self.reported_stamp_at = self.closed_at - timedelta(hours=2)
        self.inspection_id = self._insert_inspection()

        for crew_id, department, rank in (
            ("cadet-1", "DECK", "CADET"),
            ("oiler-2", "ENGINE", "OILER"),
            ("ab-3", "DECK", "AB"),
            ("motorman-4", "ENGINE", "MOTORMAN"),
        ):
            self._insert_crew(
                crew_id=crew_id,
                vessel_id="7",
                department=department,
                rank=rank,
            )

        for area_id, area_name in (
            (3, "Navigating Bridge & Monkey Island"),
            (5, "Mooring Deck + Forward Station"),
        ):
            self._insert_area(area_id=area_id, area_name=area_name)
            self._insert_selected_area(area_id=area_id)
            self._insert_area_map(
                area_id=area_id,
                last_inspected_at=self.reported_stamp_at,
                due_at=self.reported_stamp_at + timedelta(days=90),
            )

        self._insert_trainee(crew_id="cadet-1", trainee_slot=1)
        self._insert_trainee(crew_id="oiler-2", trainee_slot=2)

    def test_master_close_marks_inspection_closed_preserves_submit_time_stamps_and_returns_rotation_metric(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/close/",
            {
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-console-7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["inspection_id"], self.inspection_id)
        self.assertEqual(response.data["state"], "CLOSED")
        self.assertEqual(response.data["crew_rotation"]["coverage_percent"], 50)
        self.assertEqual(response.data["signature"]["signer_display_name"], "Master Seven")
        self.assertEqual(response.data["signature"]["device_fingerprint_last8"], "onsole-7")

        inspection_row = self._fetch_inspection_row()
        self.assertEqual(inspection_row["state"], "CLOSED")
        self.assertEqual(inspection_row["master_crew_id"], "master-7")
        self.assertIsNotNone(inspection_row["closed_at"])

        area_rows = self._fetch_area_rows()
        expected_due_at = self.reported_stamp_at + timedelta(days=90)
        for area_id in (3, 5):
            self.assertTrue(area_rows[area_id]["inspected"])
            self.assertEqual(area_rows[area_id]["last_inspected_at"], self.reported_stamp_at)
            self.assertEqual(area_rows[area_id]["map_last_inspected_at"], self.reported_stamp_at)
            self.assertEqual(area_rows[area_id]["due_at"], expected_due_at)

        signature_row = SafetyFieldHistory.objects.get(field_name="soi_close_signature")
        self.assertEqual(signature_row.actor_user_id, "master-7")
        self.assertEqual(signature_row.new_value["typed_name"], "Master Seven")

    def test_master_close_blocks_open_or_pending_findings(self) -> None:
        self._insert_finding(status="OPEN")
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/close/",
            {
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-console-7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("OPEN or PENDING_CLOSURE", str(response.data))

    def _insert_crew(
        self,
        *,
        crew_id: str,
        vessel_id: str,
        department: str,
        rank: str,
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
                [crew_id, vessel_id, department, rank, True],
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
                    reported_at,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "7",
                    "SOI/ABC/26/14",
                    "Q2/2026",
                    "REPORTED",
                    date(2026, 5, 5),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-014",
                    self.closed_at - timedelta(days=1),
                    "PDF",
                    self.closed_at - timedelta(hours=6),
                    self.closed_at - timedelta(hours=2),
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
                [self.inspection_id, area_id, True, self.reported_stamp_at, None, 1],
            )

    def _insert_area_map(self, *, area_id: int, last_inspected_at, due_at) -> None:
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
                ["7", area_id, True, last_inspected_at, due_at, 1],
            )

    def _insert_trainee(self, *, crew_id: str, trainee_slot: int) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_trainee (
                    inspection_id,
                    crew_id,
                    trainee_slot,
                    schema_version
                ) VALUES (%s, %s, %s, %s)
                """,
                [self.inspection_id, crew_id, trainee_slot, 1],
            )

    def _insert_finding(self, *, status: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_finding (
                    inspection_id,
                    area_id,
                    item_id,
                    title,
                    description,
                    severity,
                    priority,
                    status,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    self.inspection_id,
                    3,
                    None,
                    "Open finding",
                    "Open finding description",
                    "MED",
                    "MED",
                    status,
                    1,
                    False,
                    "co-7",
                ],
            )

    def _fetch_inspection_row(self) -> dict[str, object]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT state, master_crew_id, closed_at
                FROM vims_safety_soi_inspection
                WHERE id = %s
                """,
                [self.inspection_id],
            )
            row = cursor.fetchone()
        return {"state": row[0], "master_crew_id": row[1], "closed_at": row[2]}

    def _fetch_area_rows(self) -> dict[int, dict[str, object]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    selection.area_id,
                    selection.inspected,
                    selection.last_inspected_at,
                    map.last_inspected_at,
                    map.due_at
                FROM vims_safety_soi_inspection_area AS selection
                JOIN vims_safety_soi_vessel_area_map AS map
                  ON map.vessel_id = %s
                 AND map.area_id = selection.area_id
                WHERE selection.inspection_id = %s
                ORDER BY selection.area_id
                """,
                ["7", self.inspection_id],
            )
            rows = cursor.fetchall()
        return {
            int(area_id): {
                "inspected": bool(inspected),
                "last_inspected_at": selection_last_inspected_at,
                "map_last_inspected_at": map_last_inspected_at,
                "due_at": due_at,
            }
            for area_id, inspected, selection_last_inspected_at, map_last_inspected_at, due_at in rows
        }
