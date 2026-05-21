from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.repositories import IncidentRepository
from apps.safety.tasks.awaiting_daily_report_matcher import retry_awaiting_daily_report_matches


def _recreate_reporting_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS NoonReport")
        cursor.execute("DROP TABLE IF EXISTS DepartureReport")
        cursor.execute("DROP TABLE IF EXISTS ArrivalReport")
        cursor.execute("DROP TABLE IF EXISTS NoonReportPort")
        cursor.execute(
            """
            CREATE TABLE NoonReport (
                id VARCHAR(64) PRIMARY KEY,
                auto_id INTEGER NOT NULL,
                VesselID VARCHAR(32) NOT NULL,
                ReportDate DATETIME NOT NULL,
                Lattitude1 INTEGER NOT NULL,
                Lattitude2 INTEGER NOT NULL,
                Lattitude3 VARCHAR(4) NOT NULL,
                Longitude1 INTEGER NOT NULL,
                Longitud2 INTEGER NOT NULL,
                Longitud3 VARCHAR(4) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE DepartureReport (
                id VARCHAR(64) PRIMARY KEY,
                auto_id INTEGER NOT NULL,
                VesselID VARCHAR(32) NOT NULL,
                ReportDate DATETIME NOT NULL,
                Lattitude1 INTEGER NOT NULL,
                Lattitude2 INTEGER NOT NULL,
                Lattitude3 VARCHAR(4) NOT NULL,
                Longitude1 INTEGER NOT NULL,
                Longitude2 INTEGER NOT NULL,
                Longitude3 VARCHAR(4) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE ArrivalReport (
                id VARCHAR(64) PRIMARY KEY,
                auto_id INTEGER NOT NULL,
                VesselID VARCHAR(32) NOT NULL,
                ReportDate DATETIME NOT NULL,
                Lattitude1 INTEGER NOT NULL,
                Lattitude2 INTEGER NOT NULL,
                Lattitude3 VARCHAR(4) NOT NULL,
                Longitude1 INTEGER NOT NULL,
                Longitud2 INTEGER NOT NULL,
                Longitud3 VARCHAR(4) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE NoonReportPort (
                id VARCHAR(64) PRIMARY KEY,
                auto_id INTEGER NOT NULL,
                VesselCode VARCHAR(32) NOT NULL,
                ReportDate DATETIME NOT NULL,
                Latitude1 INTEGER NOT NULL,
                Latitude2 INTEGER NOT NULL,
                Latitude3 VARCHAR(4) NOT NULL,
                Longitude1 INTEGER NOT NULL,
                Longitude2 INTEGER NOT NULL,
                Longitude3 VARCHAR(4) NOT NULL
            )
            """
        )


class AwaitingDailyReportMatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        _recreate_reporting_tables()
        self.repository = IncidentRepository()

    def test_retry_clears_flag_and_links_daily_report_without_overwriting_manual_position(self) -> None:
        occurred_at = datetime(2026, 4, 20, 10, 0, tzinfo=timezone.utc)
        incident = self.repository.create(
            {
                "created_by": "master-7",
                "first_hour_checklist_done": True,
                "latitude": "12.345678",
                "longitude": "103.456789",
                "narrative": "Initial intake " + ("details " * 30),
                "occurred_at": occurred_at,
                "reported_at": occurred_at + timedelta(minutes=30),
                "reporter_device_fingerprint": "device-abc",
                "reporter_id": "master-7",
                "reporter_name": "Master Seven",
                "reporter_rank": "MASTER",
                "schema_version": 1,
                "vessel_code": "ABC",
                "vessel_id": "7",
            }
        )
        self.assertTrue(incident.awaiting_daily_report_match)
        self.assertEqual(incident.position_source, "MANUAL")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO NoonReport (
                    id, auto_id, VesselID, ReportDate,
                    Lattitude1, Lattitude2, Lattitude3,
                    Longitude1, Longitud2, Longitud3
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "noon-late-match",
                    11563,
                    "7",
                    occurred_at + timedelta(hours=1),
                    9,
                    13,
                    "N",
                    115,
                    35,
                    "E",
                ],
            )

        resolved = retry_awaiting_daily_report_matches()

        incident.refresh_from_db()
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["incident_id"], incident.pk)
        self.assertFalse(incident.awaiting_daily_report_match)
        self.assertEqual(str(incident.latitude), "12.345678")
        self.assertEqual(str(incident.longitude), "103.456789")
        self.assertEqual(incident.position_source, "MANUAL")
        self.assertEqual(incident.position_daily_report_id, "NoonReport:11563")
        self.assertEqual(incident.updated_by, "system")
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_table="vims_safety_incident",
                parent_id=incident.pk,
                field_name="awaiting_daily_report_match",
                new_value="false",
            ).exists()
        )

    def test_retry_backfills_auto_position_when_reporting_row_arrives_later(self) -> None:
        occurred_at = datetime(2026, 4, 21, 5, 0, tzinfo=timezone.utc)
        incident = self.repository.create(
            {
                "created_by": "master-9",
                "first_hour_checklist_done": True,
                "narrative": "Initial intake " + ("details " * 30),
                "occurred_at": occurred_at,
                "reported_at": occurred_at + timedelta(minutes=10),
                "reporter_device_fingerprint": "device-later",
                "reporter_id": "master-9",
                "reporter_name": "Master Nine",
                "reporter_rank": "MASTER",
                "schema_version": 1,
                "vessel_code": "XYZ",
                "vessel_id": "9",
            }
        )
        self.assertTrue(incident.awaiting_daily_report_match)
        self.assertEqual(incident.position_source, "AWAITING_DAILY_REPORT")
        self.assertIsNone(incident.latitude)
        self.assertIsNone(incident.longitude)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO DepartureReport (
                    id, auto_id, VesselID, ReportDate,
                    Lattitude1, Lattitude2, Lattitude3,
                    Longitude1, Longitude2, Longitude3
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "dep-late-match",
                    3001,
                    "9",
                    occurred_at - timedelta(hours=2),
                    1,
                    15,
                    "N",
                    104,
                    5,
                    "E",
                ],
            )

        resolved = retry_awaiting_daily_report_matches()

        incident.refresh_from_db()
        self.assertEqual(len(resolved), 1)
        self.assertFalse(incident.awaiting_daily_report_match)
        self.assertEqual(incident.position_source, "AUTO_FROM_DAILY_REPORT")
        self.assertEqual(incident.position_daily_report_id, "DepartureReport:3001")
        self.assertAlmostEqual(float(incident.latitude), 1.25, places=5)
        self.assertAlmostEqual(float(incident.longitude), 104.083333, places=5)
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_table="vims_safety_incident",
                parent_id=incident.pk,
                field_name="position_daily_report_id",
                new_value="DepartureReport:3001",
            ).exists()
        )
