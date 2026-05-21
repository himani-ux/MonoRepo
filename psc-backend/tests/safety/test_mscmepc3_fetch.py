from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.services.mscmepc3_position_fetcher import Mscmepc3PositionFetcher


class Mscmepc3PositionFetcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self._recreate_reporting_tables()
        self.fetcher = Mscmepc3PositionFetcher()

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

    def test_returns_nearest_daily_report_with_decimal_coordinates(self) -> None:
        occurred_at = datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc)

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
                    "noon-1",
                    11560,
                    "EBK",
                    occurred_at - timedelta(hours=3),
                    9,
                    13,
                    "N",
                    115,
                    35,
                    "E",
                ],
            )
            cursor.execute(
                """
                INSERT INTO DepartureReport (
                    id, auto_id, VesselID, ReportDate,
                    Lattitude1, Lattitude2, Lattitude3,
                    Longitude1, Longitude2, Longitude3
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "dep-1",
                    2226,
                    "EBK",
                    occurred_at - timedelta(hours=6),
                    1,
                    15,
                    "N",
                    104,
                    5,
                    "E",
                ],
            )

        result = self.fetcher.fetch_position("EBK", occurred_at)

        self.assertTrue(result["matched"])
        self.assertEqual(result["position_source"], Mscmepc3PositionFetcher.AUTO_SOURCE)
        self.assertEqual(result["source_table"], "NoonReport")
        self.assertEqual(result["position_daily_report_id"], "NoonReport:11560")
        self.assertAlmostEqual(result["latitude"], 9.216667, places=5)
        self.assertAlmostEqual(result["longitude"], 115.583333, places=5)
        self.assertEqual(result["delta_minutes"], 180)

    def test_exact_12_hour_boundary_is_accepted(self) -> None:
        occurred_at = datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc)

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
                    "noon-boundary",
                    11561,
                    "EBK",
                    occurred_at - timedelta(hours=12),
                    5,
                    28,
                    "N",
                    112,
                    37,
                    "E",
                ],
            )

        result = self.fetcher.fetch_position("EBK", occurred_at)

        self.assertTrue(result["matched"])
        self.assertEqual(result["delta_minutes"], 720)

    def test_12_hours_and_one_minute_is_rejected(self) -> None:
        occurred_at = datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc)

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
                    "noon-outside-window",
                    11562,
                    "EBK",
                    occurred_at - timedelta(hours=12, minutes=1),
                    2,
                    35,
                    "N",
                    109,
                    7,
                    "E",
                ],
            )

        result = self.fetcher.fetch_position("EBK", occurred_at)

        self.assertFalse(result["matched"])
        self.assertTrue(result["awaiting_daily_report_match"])
        self.assertEqual(result["position_source"], Mscmepc3PositionFetcher.AWAITING_SOURCE)

