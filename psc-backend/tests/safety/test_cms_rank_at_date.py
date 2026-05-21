from __future__ import annotations

from datetime import date
import unittest

from tests.safety.support import bootstrap_django


bootstrap_django()

from django.db import connection

from apps.safety.repositories.cms_repo import CMSRepository
from apps.safety.services.crew_rank_resolver import CrewRankResolver


VESSEL_ID = "11111111-1111-1111-1111-111111111111"
DECK_DEPARTMENT_ID = "22222222-2222-2222-2222-222222222222"
ENGINE_DEPARTMENT_ID = "33333333-3333-3333-3333-333333333333"
SECOND_OFFICER_RANK_ID = "44444444-4444-4444-4444-444444444444"
THIRD_ENGINEER_RANK_ID = "55555555-5555-5555-5555-555555555555"


class CMSRankAtDateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._recreate_live_like_cms_tables()
        self.repository = CMSRepository()
        self.rank_resolver = CrewRankResolver(cms_repository=self.repository)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO department (id, department_name)
                VALUES (%s, %s), (%s, %s)
                """,
                [DECK_DEPARTMENT_ID, "Deck", ENGINE_DEPARTMENT_ID, "Engine"],
            )
            cursor.execute(
                """
                INSERT INTO master_applied_rank (id, rank_name)
                VALUES (%s, %s), (%s, %s)
                """,
                [SECOND_OFFICER_RANK_ID, "SECOND OFFICER", THIRD_ENGINEER_RANK_ID, "THIRD ENGINEER"],
            )
            cursor.execute(
                """
                INSERT INTO HRM501 (
                    CrewID,
                    rank_name,
                    department_name,
                    first_name,
                    surname,
                    is_active,
                    is_deleted
                ) VALUES
                    (%s, %s, %s, %s, %s, 1, 0),
                    (%s, %s, %s, %s, %s, 1, 0),
                    (%s, %s, %s, %s, %s, 1, 0)
                """,
                [
                    "old-deck",
                    SECOND_OFFICER_RANK_ID,
                    DECK_DEPARTMENT_ID,
                    "Old",
                    "Officer",
                    "new-deck",
                    SECOND_OFFICER_RANK_ID,
                    DECK_DEPARTMENT_ID,
                    "New",
                    "Officer",
                    "engine-1",
                    THIRD_ENGINEER_RANK_ID,
                    ENGINE_DEPARTMENT_ID,
                    "Engine",
                    "Officer",
                ],
            )
            cursor.execute(
                """
                INSERT INTO Final_crew_list (
                    CrewID,
                    CrewName,
                    Assg_Vessel,
                    Tentative_join_date,
                    is_active,
                    is_delete,
                    is_planned
                ) VALUES
                    (%s, %s, %s, %s, 1, 0, 0),
                    (%s, %s, %s, %s, 1, 0, 0),
                    (%s, %s, %s, %s, 1, 0, 0)
                """,
                [
                    "old-deck",
                    "Old Officer",
                    VESSEL_ID,
                    "2026-04-01 00:00:00",
                    "new-deck",
                    "New Officer",
                    VESSEL_ID,
                    "2026-04-16 00:00:00",
                    "engine-1",
                    "Engine Officer",
                    VESSEL_ID,
                    "2026-04-10 00:00:00",
                ],
            )
            cursor.execute(
                """
                INSERT INTO Crew_Onboarding_History (
                    CrewID,
                    Vessel,
                    SignOnDate,
                    SignOffDate,
                    is_active,
                    is_deleted,
                    created_date
                ) VALUES
                    (%s, %s, %s, %s, 1, 0, %s),
                    (%s, %s, %s, NULL, 1, 0, %s),
                    (%s, %s, %s, NULL, 1, 0, %s)
                """,
                [
                    "old-deck",
                    VESSEL_ID,
                    "2026-04-01 00:00:00",
                    "2026-04-15 00:00:00",
                    "2026-04-01 00:00:00",
                    "new-deck",
                    VESSEL_ID,
                    "2026-04-16 00:00:00",
                    "2026-04-16 00:00:00",
                    "engine-1",
                    VESSEL_ID,
                    "2026-04-10 00:00:00",
                    "2026-04-10 00:00:00",
                ],
            )

    def test_rank_resolver_uses_as_of_date_across_rotation_boundary(self) -> None:
        before_rotation = self.rank_resolver.resolve_snapshot(
            vessel_id=VESSEL_ID,
            crew_id="old-deck",
            at_timestamp=date(2026, 4, 15),
        )
        after_rotation = self.rank_resolver.resolve_snapshot(
            vessel_id=VESSEL_ID,
            crew_id="old-deck",
            at_timestamp=date(2026, 4, 16),
        )

        self.assertIsNotNone(before_rotation)
        self.assertEqual(before_rotation["rank"], "SECOND OFFICER")
        self.assertEqual(before_rotation["department"], "DECK")
        self.assertEqual(before_rotation["crew_name"], "Old Officer")
        self.assertIsNone(after_rotation)

    def test_repository_lists_only_crew_onboard_for_requested_date(self) -> None:
        before_rotation = self.repository.list_current_vessel_crew(
            vessel_id=VESSEL_ID,
            active_on=date(2026, 4, 15),
        )
        after_rotation = self.repository.list_current_vessel_crew(
            vessel_id=VESSEL_ID,
            active_on=date(2026, 4, 16),
            exclude_department="DECK",
        )

        self.assertEqual([row["crew_id"] for row in before_rotation], ["old-deck", "engine-1"])
        self.assertEqual([row["crew_id"] for row in after_rotation], ["engine-1"])
        self.assertEqual(after_rotation[0]["rank"], "THIRD ENGINEER")
        self.assertEqual(after_rotation[0]["crew_name"], "Engine Officer")

    def _recreate_live_like_cms_tables(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS Final_crew_list")
            cursor.execute("DROP TABLE IF EXISTS HRM501")
            cursor.execute("DROP TABLE IF EXISTS Crew_Onboarding_History")
            cursor.execute("DROP TABLE IF EXISTS master_applied_rank")
            cursor.execute("DROP TABLE IF EXISTS department")
            cursor.execute(
                """
                CREATE TABLE Crew_Onboarding_History (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    CrewID VARCHAR(64) NOT NULL,
                    Vessel VARCHAR(64) NOT NULL,
                    SignOnDate DATETIME NULL,
                    SignOffDate DATETIME NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    is_deleted BOOLEAN NOT NULL DEFAULT 0,
                    created_date DATETIME NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE HRM501 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    CrewID VARCHAR(64) NOT NULL,
                    rank_name VARCHAR(64) NULL,
                    department_name VARCHAR(64) NULL,
                    first_name VARCHAR(128) NULL,
                    surname VARCHAR(128) NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    is_deleted BOOLEAN NOT NULL DEFAULT 0
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE Final_crew_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    CrewID VARCHAR(64) NOT NULL,
                    CrewName VARCHAR(128) NULL,
                    Assg_Vessel VARCHAR(64) NULL,
                    Tentative_join_date DATETIME NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    is_delete BOOLEAN NOT NULL DEFAULT 0,
                    is_planned BOOLEAN NOT NULL DEFAULT 0
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE master_applied_rank (
                    id VARCHAR(64) PRIMARY KEY,
                    rank_name VARCHAR(128) NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE department (
                    id VARCHAR(64) PRIMARY KEY,
                    department_name VARCHAR(128) NOT NULL
                )
                """
            )
