from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.incident_phase3 import IncidentPhase3InterviewView


def build_user(user_id: str = "co-1", role_name: str = "CO"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class InterviewModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentPhase3InterviewView.as_view()

    def test_formal_interview_requires_all_four_phases_and_readback(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="co-1",
            updated_by="co-1",
            schema_version=1,
        )

        incomplete_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/interviews/",
            {
                "witness_name": "AB Kumar",
                "interview_type": "FORMAL",
                "make_acquaintance_notes": "Introduced myself.",
                "introduction_notes": "Explained purpose.",
                "meeting_notes": "Captured witness account.",
                "question_rows": [{"prompt": "What happened?", "type": "OPEN", "answer": "Smoke from relay."}],
                "read_back_confirmed": False,
            },
            format="json",
        )
        force_authenticate(incomplete_request, user=build_user())

        incomplete_response = self.view(incomplete_request, id=incident.pk)

        self.assertEqual(incomplete_response.status_code, 400)
        self.assertIn("non_field_errors", incomplete_response.data)

        complete_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/interviews/",
            {
                "witness_name": "AB Kumar",
                "interview_type": "FORMAL",
                "make_acquaintance_notes": "Introduced myself.",
                "introduction_notes": "Explained purpose.",
                "meeting_notes": "Captured witness account.",
                "conclusion_notes": "Read back and closed.",
                "question_rows": [{"prompt": "What happened?", "type": "OPEN", "answer": "Smoke from relay."}],
                "read_back_confirmed": True,
                "witness_signature": "signed on paper",
                "copy_to_witness_recorded": True,
            },
            format="json",
        )
        force_authenticate(complete_request, user=build_user())

        complete_response = self.view(complete_request, id=incident.pk)

        self.assertEqual(complete_response.status_code, 201)
        self.assertTrue(complete_response.data["is_final"])
        self.assertEqual(complete_response.data["phase_count"], 4)

    def test_informal_interview_requires_reason(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="co-1",
            updated_by="co-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/interviews/",
            {
                "witness_name": "OS Patel",
                "interview_type": "INFORMAL",
                "meeting_notes": "Stopped witness on deck because the vessel was maneuvering.",
                "question_rows": [{"prompt": "What happened?", "type": "OPEN", "answer": "Rope snapped."}],
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("reason_formal_impossible", response.data)
