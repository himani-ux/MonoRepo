from __future__ import annotations

from datetime import date, time
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_scm_tables, recreate_soi_tables


bootstrap_django()

from django.utils import timezone

from apps.safety.models import (
    CorrectiveAction,
    Incident,
    IncidentPhaseLog,
    Recommendation,
    SCMAgendaItem,
    SCMMeeting,
    SOIFinding,
    SOIInspection,
    SafetyFieldHistory,
)


class UUIDReferenceReadinessTests(unittest.TestCase):
    def test_incident_child_rows_keep_integer_and_uuid_references(self):
        recreate_incident_table()

        incident = Incident.objects.create(
            vessel_id="VESSEL-A",
            incident_number="DRAFT-VESSEL-A/2026/T001",
            created_by="tester",
            schema_version=Incident.ENUM_TIGHTENED_SCHEMA_VERSION,
        )

        phase_log = IncidentPhaseLog.objects.create(
            incident=incident,
            phase_to=1,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="tester",
            actor_role_code="DPA",
            schema_version=1,
        )
        recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Fix guard",
            description="Restore missing guard.",
            created_by="tester",
            schema_version=1,
        )
        action = CorrectiveAction.objects.create(
            source_table=incident._meta.db_table,
            source_id=incident.id,
            recommendation=recommendation,
            title="Action",
            description="Action description",
            status=CorrectiveAction.Status.OPEN,
            created_by="tester",
            schema_version=1,
        )

        self.assertEqual(phase_log.incident_id, incident.id)
        self.assertEqual(phase_log.incident_uuid, incident.public_id)
        self.assertEqual(recommendation.incident_id, incident.id)
        self.assertEqual(recommendation.incident_uuid, incident.public_id)
        self.assertEqual(action.source_id, incident.id)
        self.assertEqual(action.source_uuid, incident.public_id)
        self.assertEqual(action.recommendation_id, recommendation.id)
        self.assertEqual(action.recommendation_uuid, recommendation.public_id)

    def test_scm_and_soi_child_rows_keep_integer_and_uuid_references(self):
        recreate_scm_tables()
        recreate_soi_tables()

        meeting = SCMMeeting.objects.create(
            vessel_id="VESSEL-A",
            scm_number="VESSEL-A-21-May-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 5, 21),
            meeting_time_local=time(10, 0),
            chair_crew_id="master-1",
            prepared_by_crew_id="co-1",
            created_by="tester",
            schema_version=1,
        )
        agenda = SCMAgendaItem.objects.create(
            meeting_id=meeting.id,
            agenda_item_number=1,
            section_label="Safety/Deficiencies discussed",
            content="Discussed.",
            decision="Accepted.",
            schema_version=1,
        )

        inspection = SOIInspection.objects.create(
            vessel_id="VESSEL-A",
            inspection_reference="SOI-VESSEL-A-001",
            cycle_label="2026-Q2",
            planned_date=date(2026, 5, 21),
            safety_officer_crew_id="so-1",
            safety_officer_department="DECK",
            assistant_crew_id="eng-1",
            assistant_department="ENGINE",
            created_by="tester",
            schema_version=1,
        )
        finding = SOIFinding.objects.create(
            inspection_id=inspection.id,
            area_id=1,
            title="Loose rail",
            description="Loose rail found during inspection.",
            severity=SOIFinding.Severity.LOW,
            priority=SOIFinding.Priority.LOW,
            status=SOIFinding.Status.OPEN,
            created_by="tester",
            created_date=timezone.now(),
            schema_version=1,
        )

        self.assertEqual(agenda.meeting_id, meeting.id)
        self.assertEqual(agenda.meeting_uuid, meeting.public_id)
        self.assertEqual(finding.inspection_id, inspection.id)
        self.assertEqual(finding.inspection_uuid, inspection.public_id)

    def test_field_history_parent_uuid_is_populated_when_parent_exists(self):
        recreate_incident_table()

        incident = Incident.objects.create(
            vessel_id="VESSEL-A",
            incident_number="DRAFT-VESSEL-A/2026/T002",
            created_by="tester",
            schema_version=Incident.ENUM_TIGHTENED_SCHEMA_VERSION,
        )

        history = SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.id,
            field_name="state",
            old_value="DRAFT",
            new_value="SUBMITTED",
            actor_user_id="tester",
            actor_role_code="DPA",
            schema_version=1,
        )

        self.assertEqual(history.parent_id, incident.id)
        self.assertEqual(history.parent_uuid, incident.public_id)
