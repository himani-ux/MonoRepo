from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.views.incident_phase7 import IncidentPhase7SendBackView


def build_user():
    return SimpleNamespace(
        id="dpa-1",
        username="dpa-1",
        role_name="DPA",
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_003"],
        vessel_ids=["7"],
        is_global=False,
    )


class Phase7SendBackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentPhase7SendBackView.as_view()

    def test_send_back_moves_incident_to_requested_phase_and_logs_reason(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7SB1",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/send-back/",
            {"target_phase": 5, "reason": "Preventive action narrative still misses the system-control detail."},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 5)
        self.assertEqual(incident.state, "SENT_BACK")
        self.assertTrue(
            SafetyFieldHistory.objects.filter(parent_id=incident.pk, field_name="current_phase").exists()
        )

