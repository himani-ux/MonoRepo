from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_scm_tables,
    recreate_wrh_s520_tables,
)


bootstrap_django()

from django.db import connection

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SCMAttendance, SCMMeeting
from apps.safety.repositories.scm_repo import SCMRepository
from apps.safety.views.scm_attendance import SCMAttendanceListCreateView


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


class WRHMissingWarnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        recreate_wrh_s520_tables()
        self.meeting = create_meeting()
        self.factory = APIRequestFactory()
        self.view = SCMAttendanceListCreateView.as_view()

    def test_missing_wrh_data_flags_row_but_save_proceeds(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/attendance/",
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

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_id"], self.meeting.id)
        self.assertEqual(response.data["timezone_offset_minutes"], None)
        self.assertEqual(response.data["rows"][0]["crew_id"], "crew-1")
        self.assertEqual(response.data["rows"][0]["wrh_flag"], "RED")
        self.assertFalse(response.data["rows"][0]["wrh_data_available"])
        self.assertTrue(
            any(
                "WRH data unavailable for 'Crew One'." in warning
                for warning in response.data["warnings"]
            )
        )

        saved_row = SCMAttendance.objects.get(meeting_id=self.meeting.id, crew_id="crew-1")
        self.assertFalse(saved_row.wrh_data_available)
        self.assertIsNone(saved_row.wrh_rest_hours_24h)
        self.assertIsNone(saved_row.wrh_rest_hours_7d)
        self.assertFalse(saved_row.wrh_non_compliance_flag)

    def test_non_compliant_wrh_row_returns_yellow_warning(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO wrh_ship_time_config (vessel_id, effective_date, tz_offset_minutes)
                VALUES ('7', '2026-04-01', 330)
                """
            )
            cursor.execute(
                """
                INSERT INTO wrh_s520_month (crew_id, vessel_id, month, year, status)
                VALUES ('crew-1', '7', 4, 2026, 'APPROVED')
                """
            )
            month_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO wrh_s520_day_entry (
                    s520_month_id,
                    crew_id,
                    work_date_local,
                    total_rest_24h,
                    total_rest_7d,
                    mlc_10h_24h_status,
                    mlc_77h_7d_status,
                    is_not_onboard,
                    is_dateline_skip
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [month_id, "crew-1", "2026-04-27", 8.0, 70.0, "BREACH", "BREACH", 0, 0],
            )

        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/attendance/",
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

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["timezone_offset_minutes"], 330)
        self.assertEqual(response.data["rows"][0]["wrh_flag"], "YELLOW")
        self.assertTrue(response.data["rows"][0]["wrh_non_compliance_flag"])
        self.assertIn("WRH non-compliance for 'Crew One'.", response.data["warnings"][0])

    def test_attendance_identity_is_resolved_from_live_cms_not_client_display_fields(self) -> None:
        class FakeCMSRepository:
            def get_current_crew_snapshot(self, *, vessel_id, crew_id, active_on):
                return {"crew_id": crew_id, "crew_name": "Resolved Crew One", "rank": "ABLE SEAFARER"}

        class FakeWRHFetcher:
            def fetch_timezone_offset(self, *, vessel_id, meeting_date):
                return None

            def fetch_24h_and_7d(self, *, crew_id, meeting_date, vessel_id):
                return {
                    "timezone_offset_minutes": None,
                    "warning_codes": ["missing_data"],
                    "wrh_data_available": False,
                    "wrh_rest_hours_24h": None,
                    "wrh_rest_hours_7d": None,
                    "wrh_non_compliance_flag": False,
                }

        repository = SCMRepository(
            cms_repository=FakeCMSRepository(),
            wrh_snapshot_fetcher=FakeWRHFetcher(),
        )
        self.meeting.refresh_from_db()

        repository.save_attendance(
            meeting=self.meeting,
            rows=[
                {
                    "crew_id": "crew-1",
                    "display_name": "Client Spoof Name",
                    "rank_name": "Client Spoof Rank",
                    "present": True,
                }
            ],
        )

        saved_row = SCMAttendance.objects.get(meeting_id=self.meeting.id, crew_id="crew-1")
        self.assertEqual(saved_row.display_name, "Resolved Crew One")
        self.assertEqual(saved_row.rank_name, "ABLE SEAFARER")
