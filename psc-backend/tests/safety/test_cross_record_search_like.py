from __future__ import annotations

from datetime import date, time
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_scm_tables,
    recreate_soi_tables,
)


bootstrap_django()

from apps.safety.models import Incident, SCMMeeting, SOIFinding, SOIInspection
from apps.safety.services.cross_record_search import CrossRecordSearchService


def build_user(*, role_name: str = "DPA", vessel_ids: list[str] | None = None, is_global: bool = True):
    return SimpleNamespace(
        id="search-user",
        role_name=role_name,
        vessel_ids=vessel_ids or ["7"],
        is_global=is_global,
    )


class CrossRecordSearchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        recreate_soi_tables()
        self.service = CrossRecordSearchService()
        self.user = build_user()
        self.current_at = timezone.now()

    def test_search_groups_like_matches_across_all_record_families(self) -> None:
        incident = Incident.objects.create(
            incident_number="INC/2026/301",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=3,
            narrative="Hydraulic manifold leak observed during cargo watch handover.",
            occurred_at=self.current_at,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        Incident.objects.create(
            incident_number="INC/2026/399",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            current_phase=9,
            narrative="Archived manifold learning case kept only for retention review.",
            occurred_at=self.current_at,
            is_archived=True,
            archived_at=self.current_at,
            created_by="dpa-7",
            updated_by="dpa-7",
            schema_version=1,
        )
        near_miss = Incident.objects.create(
            incident_number="NM/2026/044",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            narrative="Crew noticed a manifold drip before pressure dropped and reported it immediately.",
            occurred_at=self.current_at,
            reporter_id="crew-44",
            reporter_name="Crew Reporter",
            created_by="crew-44",
            updated_by="dpa-7",
            schema_version=1,
        )
        meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="SCM/2026/088",
            meeting_type=SCMMeeting.MeetingType.AD_HOC,
            meeting_date=date(2026, 4, 30),
            meeting_time_local=time(10, 0),
            chair_crew_id="co-7",
            prepared_by_crew_id="co-7",
            ad_hoc_trigger_reason="Hydraulic manifold leak review and action tracking.",
            state=SCMMeeting.State.SUBMITTED,
            created_by="co-7",
        )
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/2026/030",
            cycle_label="2026-Q2",
            state=SOIInspection.State.REPORTED,
            planned_date=date(2026, 4, 12),
            safety_officer_crew_id="so-7",
            safety_officer_department="DECK",
            assistant_crew_id="eng-7",
            assistant_department="ENG",
            created_by="so-7",
        )
        finding = SOIFinding.objects.create(
            inspection_id=inspection.pk,
            area_id=3,
            title="Manifold guard missing",
            description="Hydraulic manifold guard remained open after maintenance and needs closure.",
            severity=SOIFinding.Severity.MED,
            priority=SOIFinding.Priority.MED,
            status=SOIFinding.Status.OPEN,
            created_by="so-7",
        )

        payload = self.service.search("manifold", user=self.user)

        self.assertEqual(payload["query"], "manifold")
        self.assertFalse(payload["include_archived"])
        self.assertEqual(payload["total_count"], 4)
        self.assertEqual(payload["counts"]["INCIDENT"], 1)
        self.assertEqual(payload["counts"]["NEAR_MISS"], 1)
        self.assertEqual(payload["counts"]["SCM"], 1)
        self.assertEqual(payload["counts"]["SOI_FINDING"], 1)
        self.assertEqual(payload["groups"]["INCIDENT"][0]["id"], incident.pk)
        self.assertEqual(payload["groups"]["NEAR_MISS"][0]["id"], near_miss.pk)
        self.assertEqual(payload["groups"]["SCM"][0]["id"], meeting.pk)
        self.assertEqual(payload["groups"]["SOI_FINDING"][0]["id"], finding.pk)
        self.assertEqual(
            payload["groups"]["SOI_FINDING"][0]["route"],
            f"/safety/soi/{inspection.pk}/findings/{finding.pk}",
        )
        self.assertNotIn("INC/2026/399", [row["reference"] for row in payload["groups"]["INCIDENT"]])

    def test_search_respects_record_type_filter(self) -> None:
        Incident.objects.create(
            incident_number="NM/2026/045",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            narrative="Anchor wash manifold spray corrected before escalation.",
            occurred_at=self.current_at,
            reporter_id="crew-45",
            reporter_name="Crew Reporter",
            created_by="crew-45",
            updated_by="crew-45",
            schema_version=1,
        )
        Incident.objects.create(
            incident_number="INC/2026/302",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=2,
            narrative="Manifold hose separation triggered a formal incident workflow.",
            occurred_at=self.current_at,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        payload = self.service.search("manifold", user=self.user, record_type="NEAR_MISS")

        self.assertFalse(payload["include_archived"])
        self.assertEqual(payload["total_count"], 1)
        self.assertEqual(payload["counts"]["NEAR_MISS"], 1)
        self.assertEqual(payload["counts"]["INCIDENT"], 0)
        self.assertEqual(payload["groups"]["NEAR_MISS"][0]["reference"], "NM/2026/045")
