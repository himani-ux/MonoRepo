from __future__ import annotations

import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_wrh_s520_tables


bootstrap_django()

from apps.safety.services.wrh_snapshot_fetcher import WRHSnapshotFetcher


class WRHTimezoneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_wrh_s520_tables()

    def test_timezone_uses_latest_ship_time_config_for_meeting_date(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO wrh_ship_time_config (vessel_id, effective_date, tz_offset_minutes)
                VALUES
                    ('7', '2026-04-01', 330),
                    ('7', '2026-04-20', 120),
                    ('7', '2026-05-01', 60)
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
                [month_id, "crew-1", "2026-04-27", 12.0, 84.0, "OK", "OK", 0, 0],
            )

        result = WRHSnapshotFetcher().fetch_24h_and_7d(
            crew_id="crew-1",
            meeting_date="2026-04-28",
            vessel_id="7",
        )

        self.assertTrue(result["wrh_data_available"])
        self.assertEqual(result["timezone_offset_minutes"], 120)
        self.assertEqual(result["wrh_flag"], "GREEN")
        self.assertEqual(float(result["wrh_rest_hours_24h"]), 12.0)
        self.assertEqual(float(result["wrh_rest_hours_7d"]), 84.0)
        self.assertEqual(result["warnings"], [])
