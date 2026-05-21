from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as dt_timezone
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone

from apps.safety.models import SOIInspection
from apps.safety.repositories.finding_repo import FindingRepository
from apps.safety.services.soi_close_service import SOICloseService
from apps.safety.services.soi_compliance_calculator import SOIComplianceCalculator


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def build_master_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="master-7",
        username="master-7",
        role_name="MASTER",
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_004"],
        vessel_ids=["7"],
        is_global=False,
    )


class _CrewRotationStub:
    def get_summary(self, vessel_id: str) -> dict[str, object]:
        return {
            "accompanied_crew_count": 0,
            "coverage_percent": 0,
            "crew": [],
            "display_value": "0%",
            "total_active_crew": 0,
            "vessel_id": vessel_id,
            "window_days": 365,
            "window_end": "2026-05-06T09:30:00+00:00",
            "window_start": "2025-05-06T09:30:00+00:00",
        }


class NinetyDayResetTimingFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.submitted_at = aware(2026, 5, 5, 14, 0)
        self.closed_at = aware(2026, 5, 6, 9, 30)
        self.finding_repository = FindingRepository(now_func=lambda: self.submitted_at)
        self.close_service = SOICloseService(
            now_func=lambda: self.closed_at,
            crew_rotation_service=_CrewRotationStub(),
        )
        self.compliance = SOIComplianceCalculator(now_func=lambda: self.closed_at)
        self.inspection_id = self._insert_inspection()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_selected_area(area_id=3)
        self._insert_area_map(area_id=3)

    def test_submit_time_stamp_remains_authoritative_after_final_close(self) -> None:
        inspection = SOIInspection.objects.get(pk=self.inspection_id, is_deleted=False)

        submit_payload = self.finding_repository.submit_areas(
            inspection=inspection,
            submitted_area_ids=[3],
            actor_id="co-7",
        )

        self.assertEqual(submit_payload["state"], "REPORTED")
        expected_due_at = self.submitted_at + timedelta(days=90)
        expected_submit_utc = self.submitted_at.astimezone(dt_timezone.utc)
        expected_due_utc = expected_due_at.astimezone(dt_timezone.utc)

        before_close = self._fetch_area_state(area_id=3)
        self.assertEqual(self._normalize_timestamp(before_close["selection_last_inspected_at"]), expected_submit_utc)
        self.assertEqual(self._normalize_timestamp(before_close["map_last_inspected_at"]), expected_submit_utc)
        self.assertEqual(self._normalize_timestamp(before_close["due_at"]), expected_due_utc)

        snapshot = self.close_service.close_inspection(
            inspection=SOIInspection.objects.get(pk=self.inspection_id, is_deleted=False),
            user=build_master_user(),
            typed_name="Master Seven",
            device_fingerprint="bridge-console-7",
        )

        self.assertEqual(snapshot["state"], "CLOSED")
        self.assertEqual(snapshot["closed_at"], self.closed_at)
        self.assertEqual(
            self._normalize_timestamp(snapshot["selected_areas"][0]["last_inspected_at"]),
            expected_submit_utc,
        )

        after_close = self._fetch_area_state(area_id=3)
        self.assertEqual(self._normalize_timestamp(after_close["selection_last_inspected_at"]), expected_submit_utc)
        self.assertEqual(self._normalize_timestamp(after_close["map_last_inspected_at"]), expected_submit_utc)
        self.assertEqual(self._normalize_timestamp(after_close["due_at"]), expected_due_utc)

        summary = self.compliance.get_summary("7", at_date=self.submitted_at + timedelta(days=90))
        self.assertEqual(summary["status"], "RED")
        self.assertEqual(summary["compliance_percent"], 0)
        self.assertEqual(
            self._normalize_timestamp(summary["areas"][0]["due_at"]).astimezone(
                timezone.get_current_timezone()
            ).date(),
            expected_due_at.date(),
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
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "7",
                    "SOI/ABC/26/15",
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 5),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-015",
                    self.submitted_at - timedelta(days=1),
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

    def _fetch_area_state(self, *, area_id: int) -> dict[str, object]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    selection.last_inspected_at,
                    map.last_inspected_at,
                    map.due_at
                FROM vims_safety_soi_inspection_area AS selection
                JOIN vims_safety_soi_vessel_area_map AS map
                  ON map.vessel_id = %s
                 AND map.area_id = selection.area_id
                WHERE selection.inspection_id = %s
                  AND selection.area_id = %s
                """,
                ["7", self.inspection_id, area_id],
            )
            row = cursor.fetchone()
        return {
            "selection_last_inspected_at": row[0],
            "map_last_inspected_at": row[1],
            "due_at": row[2],
        }

    def _normalize_timestamp(self, value) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timezone.is_naive(value):
            value = value.replace(tzinfo=dt_timezone.utc)
        return value.astimezone(dt_timezone.utc)
