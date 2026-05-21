from __future__ import annotations

from datetime import datetime, timezone
import os
import unittest
from unittest import mock

from django.db import connection

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_scm_tables,
    recreate_wrh_s520_tables,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, SCMMeeting
from apps.safety.repositories.wrh_repo import WRHRepository
from apps.safety.services.fatigue_live_join import FatigueLiveJoinService
from apps.safety.services.wrh_snapshot_fetcher import WRHSnapshotFetcher
from apps.safety.views.scm_attendance import SCMAttendanceListCreateView


def build_user(*, process_ids: list[str] | None = None, role_name: str = "MASTER"):
    return type(
        "UserStub",
        (),
        {
            "id": "master-7",
            "username": "master-7",
            "role_name": role_name,
            "form_ids": ["SAF_F_003"],
            "process_ids": ["SAF_P_001"] if process_ids is None else process_ids,
            "vessel_ids": ["7"],
            "is_global": False,
        },
    )()


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


class WRHTimeoutFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        recreate_wrh_s520_tables()

    def _seed_timezone(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO wrh_ship_time_config (vessel_id, effective_date, tz_offset_minutes)
                VALUES ('7', '2026-04-01', 330)
                """
            )

    def _seed_month(self, *, crew_id: str = "crew-1") -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO wrh_s520_month (crew_id, vessel_id, month, year, status)
                VALUES (%s, '7', 4, 2026, 'APPROVED')
                """,
                [crew_id],
            )
            return cursor.lastrowid

    def _insert_day_entry(
        self,
        *,
        month_id: int,
        crew_id: str,
        work_date_local: str,
        total_rest_24h: float,
        total_rest_7d: float,
        status_24h: str = "OK",
        status_7d: str = "OK",
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO wrh_s520_day_entry (
                    s520_month_id,
                    crew_id,
                    work_date_local,
                    tz_offset_minutes,
                    total_rest_24h,
                    total_rest_7d,
                    mlc_10h_24h_status,
                    mlc_77h_7d_status,
                    is_not_onboard,
                    is_dateline_skip
                ) VALUES (%s, %s, %s, 330, %s, %s, %s, %s, 0, 0)
                """,
                [month_id, crew_id, work_date_local, total_rest_24h, total_rest_7d, status_24h, status_7d],
            )

    def test_final_timeout_contract_keeps_shared_env_override(self) -> None:
        self.assertEqual(WRHSnapshotFetcher.QUERY_TIMEOUT_ENV, WRHRepository.QUERY_TIMEOUT_ENV)

        with mock.patch.dict(os.environ, {WRHRepository.QUERY_TIMEOUT_ENV: "1750"}):
            repository = WRHRepository()

        self.assertEqual(repository.timeout_ms, 1750)
        self.assertEqual(repository.timeout_seconds, 2)

    def test_scm_attendance_reuses_saved_snapshot_instead_of_streaming_new_wrh_rows(self) -> None:
        self._seed_timezone()
        month_id = self._seed_month()
        self._insert_day_entry(
            month_id=month_id,
            crew_id="crew-1",
            work_date_local="2026-04-27",
            total_rest_24h=8.0,
            total_rest_7d=70.0,
            status_24h="BREACH",
            status_7d="BREACH",
        )

        meeting = create_meeting()
        factory = APIRequestFactory()
        attendance_view = SCMAttendanceListCreateView.as_view()

        post_request = factory.post(
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
        force_authenticate(post_request, user=build_user())
        post_response = attendance_view(post_request, id=meeting.id)

        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(float(post_response.data["rows"][0]["wrh_rest_hours_24h"]), 8.0)
        self.assertEqual(float(post_response.data["rows"][0]["wrh_rest_hours_7d"]), 70.0)
        self.assertEqual(post_response.data["rows"][0]["wrh_flag"], "YELLOW")

        self._insert_day_entry(
            month_id=month_id,
            crew_id="crew-1",
            work_date_local="2026-04-28",
            total_rest_24h=12.0,
            total_rest_7d=84.0,
            status_24h="OK",
            status_7d="OK",
        )

        get_request = factory.get(f"/api/safety/scm/{meeting.id}/attendance/")
        force_authenticate(get_request, user=build_user(process_ids=[]))
        get_response = attendance_view(get_request, id=meeting.id)

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(float(get_response.data["rows"][0]["wrh_rest_hours_24h"]), 8.0)
        self.assertEqual(float(get_response.data["rows"][0]["wrh_rest_hours_7d"]), 70.0)
        self.assertEqual(get_response.data["rows"][0]["wrh_flag"], "YELLOW")

    def test_fatigue_lookback_stays_within_trailing_seven_days(self) -> None:
        recreate_incident_table()
        self._seed_timezone()
        month_id = self._seed_month()

        self._insert_day_entry(
            month_id=month_id,
            crew_id="crew-1",
            work_date_local="2026-04-28",
            total_rest_24h=9.5,
            total_rest_7d=80.0,
        )
        self._insert_day_entry(
            month_id=month_id,
            crew_id="crew-1",
            work_date_local="2026-04-22",
            total_rest_24h=8.5,
            total_rest_7d=76.0,
            status_7d="BREACH",
        )
        self._insert_day_entry(
            month_id=month_id,
            crew_id="crew-1",
            work_date_local="2026-04-21",
            total_rest_24h=7.0,
            total_rest_7d=68.0,
            status_24h="BREACH",
            status_7d="BREACH",
        )

        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            occurred_at=datetime(2026, 4, 28, 6, 0, tzinfo=timezone.utc),
        )

        result = FatigueLiveJoinService().fetch(incident=incident, crew_ids=["crew-1"])
        returned_dates = [row["work_date_local"].isoformat() for row in result["attendance_rows"]]

        self.assertEqual(result["warning_codes"], [])
        self.assertEqual(returned_dates, ["2026-04-28", "2026-04-22"])
        self.assertNotIn("2026-04-21", returned_dates)

