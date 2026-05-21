from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_cms_tables


bootstrap_django()

from django.db import connection

from apps.safety.repositories.cms_repo import CMSRepository


class CMSLiveJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_cms_tables()
        self.repository = CMSRepository()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Crew_Onboarding_History (
                    crew_id,
                    vessel_id,
                    department,
                    rank,
                    is_current
                ) VALUES ('co-7', '7', 'DECK', 'CO', 1)
                """
            )
            cursor.execute(
                """
                INSERT INTO HRM501 (
                    crew_id,
                    department,
                    rank
                ) VALUES ('co-7', 'DECK', 'CO')
                """
            )
            cursor.execute(
                """
                INSERT INTO Crew_Onboarding_History (
                    crew_id,
                    vessel_id,
                    department,
                    rank,
                    is_current
                ) VALUES ('2e-7', '7', 'ENGINE', '2/E', 1)
                """
            )
            cursor.execute(
                """
                INSERT INTO HRM501 (
                    crew_id,
                    department,
                    rank
                ) VALUES ('2e-7', 'ENGINE', '2/E')
                """
            )
            cursor.execute(
                """
                INSERT INTO Crew_Onboarding_History (
                    crew_id,
                    vessel_id,
                    department,
                    rank,
                    is_current
                ) VALUES ('signed-off', '7', 'DECK', 'CO', 0)
                """
            )
            cursor.execute(
                """
                INSERT INTO HRM501 (
                    crew_id,
                    department,
                    rank
                ) VALUES ('signed-off', 'DECK', 'CO')
                """
            )

    def test_repository_reads_current_rank_and_department_from_live_tables(self) -> None:
        snapshot = self.repository.get_current_crew_snapshot(vessel_id="7", crew_id="co-7")

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["crew_id"], "co-7")
        self.assertEqual(snapshot["department"], "DECK")
        self.assertEqual(snapshot["rank"], "CO")

    def test_repository_lists_current_vessel_crew_without_etl_or_signed_off_rows(self) -> None:
        rows = self.repository.list_current_vessel_crew(vessel_id="7", exclude_department="DECK")

        self.assertEqual([row["crew_id"] for row in rows], ["2e-7"])
