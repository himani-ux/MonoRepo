from __future__ import annotations

import os
from types import SimpleNamespace
import unittest
from unittest import mock

from tests.safety.support import bootstrap_django, recreate_scm_tables


bootstrap_django()

from apps.safety.models import SCMAttendance, SCMMeeting
from apps.safety.repositories.exceptions import SPTimeoutError
from apps.safety.repositories.scm_repo import SCMRepository
from apps.safety.repositories.wrh_repo import WRHRepository
from apps.safety.services.wrh_snapshot_fetcher import WRHSnapshotFetcher
from apps.safety.views.scm_attendance import SCMAttendanceListCreateView
from rest_framework.test import APIRequestFactory, force_authenticate


def build_user(*, process_ids: list[str] | None = None, role_name: str = "MASTER"):
    return SimpleNamespace(
        id="master-7",
        username="master-7",
        role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=["SAF_P_001"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


def create_meeting() -> SCMMeeting:
    return SCMMeeting.objects.create(
        vessel_id="7",
        scm_number="ABC-28-Apr-2026",
        meeting_type=SCMMeeting.MeetingType.REGULAR,
        meeting_date="2026-04-28",
        meeting_time_local="10:00:00",
        location="Singapore Anchorage",
        voyage_no="V2026-03",
        chair_crew_id="master-7",
        prepared_by_crew_id="co-7",
        state=SCMMeeting.State.DRAFT,
        created_by="co-7",
        updated_by="co-7",
        schema_version=1,
    )


class TimeoutWRHRepository:
    def has_required_tables(self) -> bool:
        return True

    def get_timezone_offset_minutes(self, *, vessel_id: str, meeting_date) -> int:
        return 330

    def get_latest_rest_snapshot(self, *, crew_id: str, vessel_id: str, meeting_date):
        raise SPTimeoutError("Timed out while querying WRH.")

    def list_latest_rest_snapshots(self, *, crew_ids, vessel_id: str, meeting_date):
        raise SPTimeoutError("Timed out while querying WRH.")


class TimeoutSnapshotFetcher:
    def fetch_24h_and_7d(self, *, crew_id: str, meeting_date, vessel_id: str) -> dict[str, object]:
        return {
            "timezone_offset_minutes": 330,
            "warning_codes": ["lookup_timeout"],
            "warnings": ["WRH lookup timed out. Continue with manual review (D-GAP-M11)."],
            "wrh_24h_status": None,
            "wrh_7d_status": None,
            "wrh_data_available": False,
            "wrh_flag": "RED",
            "wrh_non_compliance_flag": False,
            "wrh_rest_hours_24h": None,
            "wrh_rest_hours_7d": None,
            "wrh_work_date_local": None,
        }

    def fetch_timezone_offset(self, *, vessel_id: str, meeting_date) -> int:
        return 330


class TimeoutSCMRepository(SCMRepository):
    def __init__(self, **kwargs) -> None:
        super().__init__(wrh_snapshot_fetcher=TimeoutSnapshotFetcher(), **kwargs)


class TimeoutAttendanceView(SCMAttendanceListCreateView):
    repository_class = TimeoutSCMRepository


class WRHTimeoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def test_repository_reads_timeout_from_env(self) -> None:
        with mock.patch.dict(os.environ, {WRHRepository.QUERY_TIMEOUT_ENV: "1500"}):
            repository = WRHRepository()

        self.assertEqual(repository.timeout_ms, 1500)
        self.assertEqual(repository.timeout_seconds, 2)

    def test_snapshot_fetcher_marks_timeout_without_raising(self) -> None:
        fetcher = WRHSnapshotFetcher(wrh_repository=TimeoutWRHRepository())

        result = fetcher.fetch_24h_and_7d(
            crew_id="crew-1",
            meeting_date="2026-04-28",
            vessel_id="7",
        )

        self.assertFalse(result["wrh_data_available"])
        self.assertEqual(result["wrh_flag"], "RED")
        self.assertEqual(result["timezone_offset_minutes"], 330)
        self.assertIn("lookup_timeout", result["warning_codes"])
        self.assertIn("WRH lookup timed out. Continue with manual review (D-GAP-M11).", result["warnings"])

    def test_batch_snapshot_fetcher_marks_timeout_for_each_crew(self) -> None:
        fetcher = WRHSnapshotFetcher(wrh_repository=TimeoutWRHRepository())

        result = fetcher.fetch_many_24h_and_7d(
            crew_ids=["crew-1", "crew-2"],
            meeting_date="2026-04-28",
            vessel_id="7",
        )

        self.assertEqual(set(result), {"crew-1", "crew-2"})
        self.assertFalse(result["crew-1"]["wrh_data_available"])
        self.assertEqual(result["crew-1"]["wrh_flag"], "RED")
        self.assertEqual(result["crew-2"]["timezone_offset_minutes"], 330)
        self.assertIn("lookup_timeout", result["crew-2"]["warning_codes"])

    def test_scm_attendance_save_proceeds_when_wrh_lookup_times_out(self) -> None:
        recreate_scm_tables()
        meeting = create_meeting()
        factory = APIRequestFactory()
        view = TimeoutAttendanceView.as_view()

        request = factory.post(
            f"/api/safety/scm/{meeting.id}/attendance/",
            {
                "rows": [
                    {
                        "crew_id": "crew-1",
                        "display_name": "Crew One",
                        "rank_name": "AB",
                        "present": True,
                    }
                ]
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = view(request, id=meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["timezone_offset_minutes"], 330)
        self.assertEqual(response.data["rows"][0]["wrh_flag"], "RED")
        self.assertFalse(response.data["rows"][0]["wrh_data_available"])
        self.assertTrue(
            any(
                "WRH lookup timed out for 'Crew One'." in warning
                for warning in response.data["warnings"]
            )
        )

        saved_row = SCMAttendance.objects.get(meeting_id=meeting.id, crew_id="crew-1")
        self.assertFalse(saved_row.wrh_data_available)
        self.assertIsNone(saved_row.wrh_rest_hours_24h)
        self.assertIsNone(saved_row.wrh_rest_hours_7d)
