from __future__ import annotations

from datetime import datetime, timezone
import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_wrh_s520_tables


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.services.fatigue_live_join import FatigueLiveJoinService


class FatigueLiveJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_wrh_s520_tables()

    def test_fatigue_live_join_returns_7_day_snapshot_and_timezone(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            occurred_at=datetime(2026, 4, 27, 6, 0, tzinfo=timezone.utc),
        )

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
                    tz_offset_minutes,
                    total_rest_24h,
                    total_rest_7d,
                    mlc_10h_24h_status,
                    mlc_77h_7d_status,
                    is_not_onboard,
                    is_dateline_skip
                ) VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    month_id,
                    "crew-1",
                    "2026-04-26",
                    330,
                    8.5,
                    72.0,
                    "OK",
                    "BREACH",
                    0,
                    0,
                    month_id,
                    "crew-1",
                    "2026-04-21",
                    330,
                    9.0,
                    78.5,
                    "OK",
                    "OK",
                    0,
                    0,
                ],
            )

        result = FatigueLiveJoinService().fetch(incident=incident, crew_ids=["crew-1"])

        self.assertEqual(result["timezone_offset_minutes"], 330)
        self.assertEqual(result["warning_codes"], [])
        self.assertEqual(len(result["attendance_rows"]), 2)
        self.assertEqual(len(result["rest_hour_rows"]), 2)
        self.assertEqual(result["attendance_rows"][0]["work_date_local"].isoformat(), "2026-04-26")
        self.assertEqual(float(result["rest_hour_rows"][0]["total_rest_24h"]), 8.5)
        self.assertEqual(result["attendance_rows"][0]["mlc_77h_7d_status"], "BREACH")
        self.assertEqual(result["warnings"], [])

    def test_fatigue_live_join_warns_when_wrh_data_is_missing(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            occurred_at=datetime(2026, 4, 27, 6, 0, tzinfo=timezone.utc),
        )

        result = FatigueLiveJoinService().fetch(incident=incident, crew_ids=["crew-1"])

        self.assertEqual(result["attendance_rows"], [])
        self.assertEqual(result["rest_hour_rows"], [])
        self.assertIn("missing_data", result["warning_codes"])
        self.assertIn("WRH data unavailable for the requested crew/date.", result["warnings"])
