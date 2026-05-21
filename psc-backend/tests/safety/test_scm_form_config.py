from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
import unittest

from django.db import connection
from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_scm_tables


bootstrap_django()

from apps.safety.models import CorrectiveAction, SCMAgendaItem, SCMMeeting
from apps.safety.repositories import SCMRepository


class FakeCMSRepository:
    def get_current_crew_snapshot(self, *, vessel_id: str, crew_id: str, active_on):
        if crew_id == "co-7":
            return {
                "crew_id": "co-7",
                "crew_name": "Chief Officer Seven",
                "department": "DECK",
                "rank": "CO",
                "vessel_id": vessel_id,
            }
        return None

    def list_current_vessel_crew(self, *, vessel_id: str, active_on, exclude_department=None, exclude_crew_id=None):
        rows = [
            {
                "crew_id": "master-7",
                "crew_name": "Master Seven",
                "department": "DECK",
                "rank": "MASTER",
                "vessel_id": vessel_id,
            },
            {
                "crew_id": "co-7",
                "crew_name": "Chief Officer Seven",
                "department": "DECK",
                "rank": "CO",
                "vessel_id": vessel_id,
            },
        ]
        if exclude_crew_id:
            rows = [row for row in rows if row["crew_id"] != exclude_crew_id]
        if exclude_department:
            rows = [row for row in rows if row["department"] != exclude_department]
        return rows


class FakeWRHSnapshotFetcher:
    def fetch_24h_and_7d(self, *, crew_id: str, meeting_date, vessel_id: str):
        if crew_id == "master-7":
            return {
                "warning_codes": ["non_compliance"],
                "warnings": ["WRH non-compliance for review."],
                "wrh_data_available": True,
                "wrh_flag": "YELLOW",
                "wrh_non_compliance_flag": True,
                "wrh_rest_hours_24h": 9.5,
                "wrh_rest_hours_7d": 75.0,
            }
        return {
            "warning_codes": [],
            "warnings": [],
            "wrh_data_available": True,
            "wrh_flag": "GREEN",
            "wrh_non_compliance_flag": False,
            "wrh_rest_hours_24h": 10.0,
            "wrh_rest_hours_7d": 80.0,
        }

    def fetch_timezone_offset(self, *, vessel_id: str, meeting_date):
        return 330


class FakeClosedSinceLastService:
    def fetch_for_vessel(self, vessel_id: str):
        return {
            "cutoff": {"closed_at": "2026-04-01T10:00:00+05:30", "meeting_id": 11, "meeting_type": "REGULAR", "scm_number": "ARYA-01-Apr-2026"},
            "empty_message": None,
            "items": [],
            "meeting_id": None,
            "summary": {
                "corrective_action_count": 1,
                "incident_count": 1,
                "near_miss_count": 1,
                "soi_finding_count": 1,
                "total_count": 4,
            },
            "upper_bound_at": "2026-05-08T10:00:00+05:30",
            "vessel_id": vessel_id,
        }


class FakeOverdueSOIBlocker:
    def check_overdue_soi(self, vessel_id: str):
        return [
            {
                "area_id": 8,
                "area_name": "Bridge",
                "due_at": "2026-04-20",
                "message": "Bridge SOI area is overdue.",
                "overdue_days": 18,
            }
        ]


class SCMFormConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS msc_data")
        self.repository = SCMRepository(
            cms_repository=FakeCMSRepository(),
            closed_since_last_service=FakeClosedSinceLastService(),
            overdue_soi_blocker=FakeOverdueSOIBlocker(),
            wrh_snapshot_fetcher=FakeWRHSnapshotFetcher(),
        )

    def test_build_form_config_returns_generated_context_for_regular_scm(self) -> None:
        prior_date = date(2026, 4, 1)
        prior_meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ARYA-01-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=prior_date,
            meeting_time_local=datetime.strptime("09:00:00", "%H:%M:%S").time(),
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=timezone.make_aware(datetime.combine(prior_date, datetime.min.time())),
            master_signed_off_by="master-7",
            created_by="co-7",
        )
        agenda_row = SCMAgendaItem.objects.create(
            meeting_id=prior_meeting.id,
            agenda_item_number=2,
            section_label="Outstanding Items",
            auto_populated=False,
            content="Outstanding release gear follow-up remains open for the next committee discussion.",
            decision="Carry forward into the next SCM.",
            schema_version=1,
        )
        CorrectiveAction.objects.create(
            source_table=SCMAgendaItem._meta.db_table,
            source_id=agenda_row.id,
            title="Close release gear gap",
            description="Still open from the previous SCM.",
            status=CorrectiveAction.Status.OPEN,
            due_date=date(2026, 5, 12),
            created_by="co-7",
            updated_by="co-7",
            updated_date=timezone.now(),
            schema_version=1,
        )

        user = SimpleNamespace(
            vessel_id="7",
            vessel_code="ARYA",
            vessel_name="Araya",
        )

        payload = self.repository.build_form_config(
            vessel_id="7",
            actor_id="co-7",
            user=user,
            meeting_date="2026-05-08",
        )

        self.assertEqual(payload["meeting_type"], "REGULAR")
        self.assertEqual(payload["vessel"]["vessel_code"], "ARYA")
        self.assertEqual(payload["vessel"]["vessel_name"], "Araya")
        self.assertEqual(payload["prepared_by"]["crew_id"], "co-7")
        self.assertEqual(payload["chair"]["crew_id"], "master-7")
        self.assertEqual(len(payload["attendee_rows"]), 2)
        self.assertEqual(payload["attendee_rows"][0]["wrh_flag"], "YELLOW")
        self.assertEqual(payload["closed_since_last"]["summary"]["total_count"], 4)
        self.assertEqual(payload["overdue_soi_areas"][0]["area_id"], 8)
        self.assertEqual(payload["unresolved_previous_actions"][0]["source_scm_number"], "ARYA-01-Apr-2026")
        self.assertEqual(payload["cadence_status"]["next_due_date"], "2026-05-01")

    def test_build_form_config_includes_latest_published_msc_circulars(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE msc_data (
                    id TEXT PRIMARY KEY,
                    sr_no TEXT NULL,
                    title TEXT NULL,
                    category TEXT NULL,
                    office_instructions TEXT NULL,
                    hashtags TEXT NULL,
                    attachment_name TEXT NULL,
                    attachment_path TEXT NULL,
                    publish_status INTEGER NULL,
                    published_on TEXT NULL,
                    created_at TEXT NULL,
                    vessel_id TEXT NULL,
                    is_active INTEGER NULL,
                    is_deleted INTEGER NULL,
                    is_superseeded INTEGER NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO msc_data (
                    id, sr_no, title, category, office_instructions, hashtags,
                    publish_status, published_on, created_at, vessel_id,
                    is_active, is_deleted, is_superseeded
                ) VALUES
                ('fleet-alert', 'KSM/Alert/SEQ/2026-0015', 'Latest fleet alert', 'internal', 'Discuss alert with crew.', '#alert', 2, '2026-05-11 08:06:11', '2026-05-11 08:06:12', NULL, 1, 0, 0),
                ('vessel-circular', 'KSM/Circular/SEQ/2026-0002', 'Vessel circular', 'internal', 'Discuss circular on board.', '#circular', 2, '2026-04-23 06:01:40', '2026-04-23 05:44:59', '7', 1, 0, 0),
                ('draft-alert', 'KSM/Alert/SEQ/2026-0001', 'Draft alert', 'internal', 'Should not show.', '#draft', 3, NULL, '2026-05-12 09:00:00', NULL, 1, 0, 0)
                """
            )

        payload = self.repository.build_form_config(
            vessel_id="7",
            actor_id="co-7",
            user=SimpleNamespace(vessel_id="7", vessel_code="ARYA", vessel_name="Araya"),
            meeting_date="2026-05-08",
        )

        self.assertEqual([item["sr_no"] for item in payload["latest_circulars"]], [
            "KSM/Alert/SEQ/2026-0015",
            "KSM/Circular/SEQ/2026-0002",
        ])
        self.assertEqual(payload["latest_circulars"][0]["office_instructions"], "Discuss alert with crew.")
