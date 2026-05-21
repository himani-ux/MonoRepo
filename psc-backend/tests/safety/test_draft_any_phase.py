from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django(root_urlconf="config.urls")

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.incident import IncidentDetailView
from apps.safety.views.incident_draft import IncidentDraftSaveView


def build_user(*, role_name: str, process_ids: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        id="investigator-1",
        username="investigator-1",
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class DraftAnyPhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.save_view = IncidentDraftSaveView.as_view()
        self.detail_view = IncidentDetailView.as_view()

    def test_phase_three_draft_save_keeps_current_phase_and_restores_on_reload(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/015",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        save_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/draft/",
            {"draft_note": "People-tab interviews still incomplete."},
            format="json",
        )
        force_authenticate(save_request, user=build_user(role_name="DPA", process_ids=["SAF_P_002"]))

        save_response = self.save_view(save_request, id=incident.pk)

        self.assertEqual(save_response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 3)
        self.assertEqual(incident.state, "DRAFT")

        detail_request = self.factory.get(f"/api/safety/incidents/{incident.pk}/")
        force_authenticate(detail_request, user=build_user(role_name="DPA", process_ids=[]))
        detail_response = self.detail_view(detail_request, id=incident.pk)

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["state"], "DRAFT")
        self.assertEqual(detail_response.data["current_phase"], 3)

    def test_phase_seven_draft_save_is_rejected(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/016",
            vessel_id="7",
            state="APPROVED",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/draft/",
            {"draft_note": "Should fail."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", process_ids=["SAF_P_002"]))

        response = self.save_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
