from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table
from tests.safety.support import recreate_master_notification_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import ExternalPartyInjury, Incident, IncidentPhaseLog
from apps.safety.views.incident_phase1 import (
    IncidentPhase1CreateView,
    IncidentPhase1SubmitView,
    IncidentPhase1UpdateView,
)


def build_user(
    *,
    direct_vessel_code: str | None = None,
    direct_vessel_id: str | None = None,
    direct_vessel_name: str | None = None,
    role_name: str = "MASTER",
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[int] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_001"],
        vessel_code=direct_vessel_code,
        vessel_id=direct_vessel_id,
        vessel_name=direct_vessel_name,
        vessel_ids=vessel_ids or [7],
        is_global=False,
    )


class IncidentPhase1SubmitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.create_view = IncidentPhase1CreateView.as_view()
        self.update_view = IncidentPhase1UpdateView.as_view()
        self.submit_view = IncidentPhase1SubmitView.as_view()

    def test_create_patch_and_submit_transitions_to_phase_two(self) -> None:
        create_request = self.factory.post(
            "/api/safety/incidents/phase-1/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "occurred_at": "2026-04-20T10:00:00Z",
                "reported_at": "2026-04-20T10:30:00Z",
                "narrative": "Initial intake " + ("details " * 30),
                "office_notified": False,
                "reporter_user_id": "master-7",
                "reporter_name": "Master Seven",
                "reporter_rank": "MASTER",
                "reporter_device_fingerprint": "device-abc",
                "risk_band": Incident.RiskBand.GREEN,
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())

        create_response = self.create_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        incident_id = create_response.data["id"]
        self.assertEqual(IncidentPhaseLog.objects.count(), 1)

        patch_request = self.factory.patch(
            f"/api/safety/incidents/{incident_id}/phase-1/",
            {"narrative": "Updated intake " + ("details " * 30)},
            format="json",
        )
        force_authenticate(patch_request, user=build_user())

        patch_response = self.update_view(patch_request, id=incident_id)

        self.assertEqual(patch_response.status_code, 200)
        self.assertIn("Updated intake", patch_response.data["narrative"])

        submit_request = self.factory.post(
            f"/api/safety/incidents/{incident_id}/phase-1/submit/",
            {},
            format="json",
        )
        force_authenticate(submit_request, user=build_user())

        submit_response = self.submit_view(submit_request, id=incident_id)

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data["current_phase"], 2)
        self.assertEqual(submit_response.data["state"], "SUBMITTED")
        self.assertEqual(submit_response.data["transition"]["phase_from"], 1)
        self.assertEqual(submit_response.data["transition"]["phase_to"], 2)
        self.assertTrue(submit_response.data["phase_2_handoff"]["can_edit_phase_2"])
        self.assertEqual(submit_response.data["phase_2_handoff"]["notifications_emitted"], 0)

        incident = Incident.objects.get(pk=incident_id)
        self.assertEqual(incident.current_phase, 2)
        self.assertEqual(incident.state, "SUBMITTED")
        self.assertEqual(IncidentPhaseLog.objects.count(), 2)

    def test_phase_one_update_with_null_injury_preserves_existing_injury_details(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T010",
            vessel_id="7",
            state="SUBMITTED",
            current_phase=2,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            crew_rank="Chief Officer",
            crew_activity_type="Hot work",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        patch_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-1/",
            {
                "narrative": "Updated Phase 1 text while the injury section was not changed.",
                "external_party_injury": None,
            },
            format="json",
        )
        force_authenticate(patch_request, user=build_user())

        patch_response = self.update_view(patch_request, id=incident.pk)

        self.assertEqual(patch_response.status_code, 200)
        injury = ExternalPartyInjury.objects.get(incident=incident)
        self.assertEqual(injury.crew_rank, "Chief Officer")
        self.assertEqual(injury.crew_activity_type, "Hot work")

    def test_phase_one_get_returns_resolved_vessel_code(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T011",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.get(f"/api/safety/incidents/{incident.pk}/phase-1/")
        force_authenticate(
            request,
            user=build_user(
                direct_vessel_code="ABC",
                direct_vessel_id="7",
                direct_vessel_name="ABC VESSEL",
            ),
        )

        response = self.update_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["vessel_code"], "ABC")
        self.assertEqual(response.data["vessel_name"], "ABC VESSEL")
        self.assertEqual(response.data["vessel_id"], "7")

    def test_second_engineer_submit_routes_to_phase_two_handoff_for_authorized_roles(self) -> None:
        create_request = self.factory.post(
            "/api/safety/incidents/phase-1/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "occurred_at": "2026-04-20T10:00:00Z",
                "reported_at": "2026-04-20T10:30:00Z",
                "narrative": "Second engineer intake " + ("details " * 30),
                "office_notified": False,
                "reporter_user_id": "2e-7",
                "reporter_name": "Second Engineer Seven",
                "reporter_rank": "2/E",
                "reporter_device_fingerprint": "device-2e",
                "risk_band": Incident.RiskBand.GREEN,
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user(role_name="2/E", user_id="2e-7"))

        create_response = self.create_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        incident_id = create_response.data["id"]

        submit_request = self.factory.post(
            f"/api/safety/incidents/{incident_id}/phase-1/submit/",
            {},
            format="json",
        )
        force_authenticate(submit_request, user=build_user(role_name="2/E", user_id="2e-7"))

        submit_response = self.submit_view(submit_request, id=incident_id)

        self.assertEqual(submit_response.status_code, 200)
        self.assertFalse(submit_response.data["phase_2_handoff"]["can_edit_phase_2"])
        self.assertEqual(submit_response.data["phase_2_handoff"]["notifications_emitted"], 0)
        self.assertEqual(
            submit_response.data["phase_2_handoff"]["authorized_roles"],
            ["MASTER", "CO", "CE", "DPA", "FM"],
        )
