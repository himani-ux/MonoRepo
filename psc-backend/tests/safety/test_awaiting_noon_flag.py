from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.repositories import IncidentRepository
from apps.safety.views.incident_phase1 import IncidentPhase1SubmitView


def build_user():
    return SimpleNamespace(
        id="master-7",
        username="master-7",
        role_name="MASTER",
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_001"],
        vessel_ids=["7"],
        is_global=False,
    )


class AwaitingDailyReportFlagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self._recreate_reporting_tables()
        self.repository = IncidentRepository()
        self.factory = APIRequestFactory()
        self.submit_view = IncidentPhase1SubmitView.as_view()

    def _recreate_reporting_tables(self) -> None:
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

    def test_manual_position_without_daily_report_sets_awaiting_flag(self) -> None:
        incident = self.repository.create(
            {
                "created_by": "master-7",
                "first_hour_checklist_done": True,
                "latitude": "12.345678",
                "longitude": "103.456789",
                "narrative": "Initial intake " + ("details " * 30),
                "occurred_at": "2026-04-20T10:00:00Z",
                "reported_at": "2026-04-20T10:30:00Z",
                "reporter_device_fingerprint": "device-abc",
                "reporter_id": "master-7",
                "reporter_name": "Master Seven",
                "reporter_rank": "MASTER",
                "schema_version": 1,
                "vessel_code": "ABC",
                "vessel_id": "7",
            }
        )

        self.assertEqual(str(incident.latitude), "12.345678")
        self.assertEqual(str(incident.longitude), "103.456789")
        self.assertEqual(incident.position_source, "MANUAL")
        self.assertTrue(incident.awaiting_daily_report_match)

    def test_missing_daily_report_never_blocks_phase_one_submit(self) -> None:
        incident = self.repository.create(
            {
                "created_by": "master-7",
                "first_hour_checklist_done": True,
                "latitude": "12.345678",
                "longitude": "103.456789",
                "narrative": "Initial intake " + ("details " * 30),
                "occurred_at": "2026-04-20T10:00:00Z",
                "reported_at": "2026-04-20T10:30:00Z",
                "reporter_device_fingerprint": "device-abc",
                "reporter_id": "master-7",
                "reporter_name": "Master Seven",
                "reporter_rank": "MASTER",
                "schema_version": 1,
                "vessel_code": "ABC",
                "vessel_id": "7",
            }
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-1/submit/",
            {},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.submit_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["current_phase"], 2)
        self.assertTrue(response.data["awaiting_daily_report_match"])
