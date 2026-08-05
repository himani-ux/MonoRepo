from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, Recommendation, SafetyFieldHistory
from apps.safety.serializers.incident_phase7 import build_phase7_preflight_payload
from apps.safety.services.phase_state_machine import PhaseStateMachine
from apps.safety.views.incident import IncidentTransitionView
from apps.safety.views.incident_phase7 import IncidentPhase7AcceptView, IncidentPhase7SendBackView


def build_user(*, process_ids: list[str] | None = None, role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        role=role_name,
        safety_role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_003"],
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
        self.send_back_view = IncidentPhase7SendBackView.as_view()
        self.accept_view = IncidentPhase7AcceptView.as_view()
        self.transition_view = IncidentTransitionView.as_view()

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

        response = self.send_back_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 5)
        self.assertEqual(incident.state, "SENT_BACK")
        self.assertTrue(
            IncidentPhaseLog.objects.filter(
                incident=incident,
                phase_from=7,
                phase_to=5,
                transition_type=IncidentPhaseLog.TransitionType.REWORK,
                loop_back_reason="Preventive action narrative still misses the system-control detail.",
            ).exists()
        )
        self.assertTrue(
            SafetyFieldHistory.objects.filter(parent_id=incident.pk, field_name="current_phase").exists()
        )
        preflight = build_phase7_preflight_payload(incident)
        self.assertEqual(
            preflight["rework_summary"]["comment"],
            "Preventive action narrative still misses the system-control detail.",
        )
        self.assertEqual(preflight["rework_summary"]["requested_by"], "dpa-1")

    def test_pic_can_send_back_red_incident_for_rework(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7SB-RED",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.RED,
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
            {"target_phase": 5, "reason": "RCA needs correction before closure."},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(process_ids=["SAF_P_006"], role_name="OFFICE_PIC", user_id="pic-1"),
        )

        response = self.send_back_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 5)
        self.assertEqual(incident.state, "SENT_BACK")

    def test_send_back_does_not_require_internal_phase_seven_first(self) -> None:
        incident = Incident.objects.create(
            incident_number="YCF/2026/002",
            vessel_id="7",
            state=Incident.State.IN_PROGRESS,
            current_phase=3,
            risk_band=Incident.RiskBand.RED,
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
            {"target_phase": 6, "reason": "Please complete RCA and action details before office closure."},
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_004"], role_name="DPA", user_id="dpa-1"))

        response = self.send_back_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 6)
        self.assertEqual(incident.state, Incident.State.SENT_BACK)
        self.assertTrue(
            IncidentPhaseLog.objects.filter(
                incident=incident,
                phase_from=3,
                phase_to=6,
                transition_type=IncidentPhaseLog.TransitionType.REWORK,
                loop_back_reason="Please complete RCA and action details before office closure.",
            ).exists()
        )

    def test_sent_back_incident_can_be_corrected_resubmitted_and_accepted(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7SB2",
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

        send_back_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/send-back/",
            {"target_phase": 6, "reason": "Corrective action needs clearer ownership."},
            format="json",
        )
        force_authenticate(send_back_request, user=build_user(process_ids=["SAF_P_003"]))

        send_back_response = self.send_back_view(send_back_request, id=incident.pk)

        self.assertEqual(send_back_response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 6)
        self.assertEqual(incident.state, Incident.State.SENT_BACK)

        Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Assign a named corrective action owner",
            description="Corrected after office rework request.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        transition = PhaseStateMachine().transition(incident.pk, 7, build_user(process_ids=["SAF_P_002"]))

        incident.refresh_from_db()
        self.assertEqual(transition["phase_from"], 6)
        self.assertEqual(transition["phase_to"], 7)
        self.assertEqual(incident.current_phase, 7)
        self.assertEqual(incident.state, Incident.State.UNDER_REVIEW)
        self.assertIsNone(build_phase7_preflight_payload(incident)["rework_summary"])

        with patch("apps.safety.views.incident_phase7.generate_incident_pdf_export") as pdf_export:
            pdf_export.return_value = SimpleNamespace(
                download_path="/media/safety/incidents/ABC-2026-P7SB2.pdf",
                export_path="safety/incidents/ABC-2026-P7SB2.pdf",
                file_name="ABC-2026-P7SB2.pdf",
            )
            accept_request = self.factory.post(
                f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
                {"typed_name": "DPA Reviewer", "device_fingerprint": "device-dpa-1"},
                format="json",
            )
            force_authenticate(accept_request, user=build_user(process_ids=["SAF_P_004"]))

            accept_response = self.accept_view(accept_request, id=incident.pk)

        self.assertEqual(accept_response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 9)
        self.assertEqual(incident.state, Incident.State.CLOSED)
        self.assertEqual(incident.dpa_accepted_by, "dpa-1")

    def test_office_user_can_mark_sent_back_rework_done(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7SBDONE-OFFICE",
            vessel_id="7",
            state=Incident.State.SENT_BACK,
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Corrective action",
            description="Updated action after rework.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/transition/",
            {"target_phase": 7},
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_004"], role_name="DPA", user_id="dpa-1"))

        response = self.transition_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 7)
        self.assertEqual(incident.state, Incident.State.UNDER_REVIEW)

    def test_ship_user_can_mark_sent_back_rework_done(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7SBDONE-SHIP",
            vessel_id="7",
            state=Incident.State.SENT_BACK,
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Corrective action",
            description="Updated action after ship rework.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/transition/",
            {"target_phase": 7},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(process_ids=["SAF_P_002"], role_name="VESSEL_MASTER", user_id="master-7"),
        )

        response = self.transition_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 7)
        self.assertEqual(incident.state, Incident.State.UNDER_REVIEW)
