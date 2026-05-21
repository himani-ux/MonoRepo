from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.field_history import IncidentAuditView
from apps.safety.views.incident import IncidentTransitionView


def build_user(
    *,
    role_name: str = "MASTER",
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_002"],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class IncidentAuditApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.transition_view = IncidentTransitionView.as_view()
        self.audit_view = IncidentAuditView.as_view()

    def test_transition_endpoint_updates_phase_and_audit_endpoint_returns_log(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            schema_version=1,
            first_hour_checklist_done=True,
            narrative="N" * 220,
            imo_classifier=Incident.ImoClassifier.MI,
            risk_band=Incident.RiskBand.GREEN,
            investigation_depth=Incident.InvestigationDepth.SHALLOW,
            reporter_id="reporter-1",
        )

        transition_request = self.factory.post(
            f"/api/safety/incidents/{incident.id}/transition/",
            {"target_phase": 2},
            format="json",
        )
        force_authenticate(transition_request, user=build_user())

        transition_response = self.transition_view(transition_request, id=incident.id)

        self.assertEqual(transition_response.status_code, 200)
        self.assertEqual(transition_response.data["phase_from"], 1)
        self.assertEqual(transition_response.data["phase_to"], 2)

        audit_request = self.factory.get(f"/api/safety/incidents/{incident.id}/audit/")
        force_authenticate(audit_request, user=build_user(process_ids=[]))

        audit_response = self.audit_view(audit_request, id=incident.id)

        self.assertEqual(audit_response.status_code, 200)
        self.assertEqual(len(audit_response.data["phase_log"]), 1)
        self.assertEqual(audit_response.data["phase_log"][0]["phase_to"], 2)
        self.assertEqual(audit_response.data["field_history"], [])

    def test_transition_endpoint_returns_bad_request_for_failed_gate(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T002",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            schema_version=1,
            chain_of_custody_ok=False,
            marine_docs_checklist_done=False,
        )

        transition_request = self.factory.post(
            f"/api/safety/incidents/{incident.id}/transition/",
            {"target_phase": 4},
            format="json",
        )
        force_authenticate(transition_request, user=build_user())

        transition_response = self.transition_view(transition_request, id=incident.id)

        self.assertEqual(transition_response.status_code, 400)
        self.assertIn("chain_of_custody_ok", str(transition_response.data))
        self.assertIn("marine_docs_checklist_done", str(transition_response.data))

        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 3)
