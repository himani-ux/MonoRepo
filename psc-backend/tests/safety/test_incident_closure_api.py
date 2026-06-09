from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.views.incident_closure import IncidentClosureView


def build_user(*, role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=[],
        vessel_ids=[],
        is_global=False,
    )


class IncidentClosureApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentClosureView.as_view()

    def test_closed_incident_summary_returns_audit_counts(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/C001",
            vessel_id="8",
            state="CLOSED",
            current_phase=9,
            risk_band=Incident.RiskBand.YELLOW,
            closure_reason="Effectiveness verification passed.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=8,
            phase_to=9,
            transition_type=IncidentPhaseLog.TransitionType.CLOSE,
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table="vims_safety_incident",
            parent_id=incident.pk,
            field_name="closure_reason",
            old_value=None,
            new_value="Effectiveness verification passed.",
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )

        request = self.factory.get(f"/api/safety/incidents/{incident.pk}/closure/")
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["incident"]["id"], str(incident.pk))
        self.assertEqual(response.data["audit_summary"]["phase_log_count"], 1)
        self.assertEqual(response.data["audit_summary"]["field_history_count"], 1)
        self.assertEqual(response.data["audit_summary"]["latest_phase_log"]["phase_to"], 9)
