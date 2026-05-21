from __future__ import annotations

from datetime import date, datetime, time, timezone
from types import SimpleNamespace
import unittest
import uuid

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_scm_tables, recreate_soi_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, SCMMeeting, SOIInspection
from apps.safety.views.incident import IncidentDetailView
from apps.safety.views.scm import SCMDetailView
from apps.safety.views.soi import SOIDetailView


def build_user(*, form_ids: list[str], process_ids: list[str] | None = None, vessel_ids: list[str] | None = None):
    return SimpleNamespace(
        id="stage-public-id-user",
        username="stage-public-id-user",
        role_name="MASTER",
        form_ids=form_ids,
        process_ids=process_ids or [],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class SafetyPublicIdStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    def test_incident_public_id_is_generated_and_detail_accepts_public_id(self) -> None:
        recreate_incident_table()
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
            occurred_at=datetime(2026, 5, 20, 8, 0, tzinfo=timezone.utc),
        )

        uuid.UUID(str(incident.public_id))
        request = self.factory.get(f"/api/safety/incidents/{incident.public_id}/")
        force_authenticate(request, user=build_user(form_ids=["SAF_F_001"]))
        response = IncidentDetailView.as_view()(request, id=str(incident.public_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], incident.id)
        self.assertEqual(response.data["public_id"], str(incident.public_id))

    def test_scm_public_id_is_generated_and_detail_accepts_public_id(self) -> None:
        recreate_scm_tables()
        meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="SCM-ABC-001",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 5, 20),
            meeting_time_local=time(10, 30),
            location="Bridge",
            chair_crew_id="co-1",
            prepared_by_crew_id="co-1",
            state=SCMMeeting.State.DRAFT,
            created_by="co-1",
            schema_version=1,
        )

        uuid.UUID(str(meeting.public_id))
        request = self.factory.get(f"/api/safety/scm/{meeting.public_id}/")
        force_authenticate(request, user=build_user(form_ids=["SAF_F_003"]))
        response = SCMDetailView.as_view()(request, id=str(meeting.public_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], meeting.id)
        self.assertEqual(response.data["public_id"], str(meeting.public_id))

    def test_soi_public_id_is_generated_and_detail_accepts_public_id(self) -> None:
        recreate_soi_tables()
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI-ABC-001",
            cycle_label="2026-05",
            state=SOIInspection.State.PLANNED,
            planned_date=date(2026, 5, 20),
            safety_officer_crew_id="co-1",
            safety_officer_department="Deck",
            assistant_crew_id="ab-1",
            assistant_department="Engine",
            created_by="co-1",
            schema_version=1,
        )

        uuid.UUID(str(inspection.public_id))
        request = self.factory.get(f"/api/safety/soi/{inspection.public_id}/")
        force_authenticate(request, user=build_user(form_ids=["SAF_F_004"]))
        response = SOIDetailView.as_view()(request, id=str(inspection.public_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], inspection.id)
        self.assertEqual(response.data["public_id"], str(inspection.public_id))


if __name__ == "__main__":
    unittest.main()
