from __future__ import annotations

from datetime import datetime, timedelta
import os
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone

from apps.safety.models import Incident, SCMAgendaItem, SCMMeeting, SafetyDashboardRollup
from apps.safety.tasks.dashboard_rollup import build_dashboard_rollups, get_dashboard_rollup_cron


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class DashboardRollupCadenceTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_soi_tables()
        self._recreate_dashboard_support_tables()
        self.original_cron = os.environ.get("SAFETY_DASHBOARD_ROLLUP_CRON")
        self.current_at = aware(2026, 4, 30, 12, 0)

        Incident.objects.create(
            incident_number="INC/2026/081",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=6,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [3, "Navigating Bridge & Monkey Island", False, 3, True, "v1.0"],
            )
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    "7",
                    3,
                    True,
                    self.current_at - timedelta(days=20),
                    self.current_at + timedelta(days=70),
                    1,
                ],
            )

    def tearDown(self) -> None:
        if self.original_cron is None:
            os.environ.pop("SAFETY_DASHBOARD_ROLLUP_CRON", None)
        else:
            os.environ["SAFETY_DASHBOARD_ROLLUP_CRON"] = self.original_cron

    def test_default_cron_and_rollup_population(self) -> None:
        rows = build_dashboard_rollups(period_codes=(SafetyDashboardRollup.PeriodCode.YEARS_3,))

        self.assertEqual(get_dashboard_rollup_cron(), "0 */6 * * *")
        self.assertEqual(len(rows), 2)
        self.assertEqual(SafetyDashboardRollup.objects.count(), 2)
        self.assertTrue(
            SafetyDashboardRollup.objects.filter(scope_type=SafetyDashboardRollup.ScopeType.VESSEL, scope_id="7").exists()
        )
        self.assertTrue(
            SafetyDashboardRollup.objects.filter(scope_type=SafetyDashboardRollup.ScopeType.FLEET, scope_id="").exists()
        )

    def test_env_override_is_respected(self) -> None:
        os.environ["SAFETY_DASHBOARD_ROLLUP_CRON"] = "0 0 * * *"

        self.assertEqual(get_dashboard_rollup_cron(), "0 0 * * *")

    def _recreate_dashboard_support_tables(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_dashboard_rollup")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_agenda")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_meeting")
            cursor.execute("PRAGMA foreign_keys = ON")

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(SCMMeeting)
            schema_editor.create_model(SCMAgendaItem)
            schema_editor.create_model(SafetyDashboardRollup)
