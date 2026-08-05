from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.serializers.incident_phase7 import build_phase7_preflight_payload
from apps.safety.views.incident_phase7 import (
    IncidentPhase7AcceptView,
    IncidentPhase7ApproveRedView,
    IncidentPhase7HodSignatureView,
)


def build_user(*, role_name: str, user_id: str, process_ids: list[str], role: str | None = None, safety_role_name: str | None = None):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role=role or role_name,
        role_name=role_name,
        safety_role_name=safety_role_name or role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class Phase7AcceptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.accept_view = IncidentPhase7AcceptView.as_view()
        self.approve_red_view = IncidentPhase7ApproveRedView.as_view()
        self.hod_signature_view = IncidentPhase7HodSignatureView.as_view()

    def _seed_prior_chain(self, incident: Incident) -> None:
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=1,
            phase_to=2,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=5,
            phase_to=6,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="hod-7",
            actor_role_code="HOD",
            schema_version=1,
        )

    def _assert_closed_by_office_review(self, incident: Incident) -> None:
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 9)
        self.assertEqual(incident.state, "CLOSED")
        self.assertIsNotNone(incident.closed_at)
        self.assertTrue(incident.closure_reason)

    def test_yellow_accept_closes_incident_at_office_review(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7A1",
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
        self._seed_prior_chain(incident)

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "DPA Reviewer", "device_fingerprint": "device-dpa-1"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", user_id="dpa-1", process_ids=["SAF_P_004"]),
        )

        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self._assert_closed_by_office_review(incident)
        self.assertEqual(incident.dpa_accepted_by, "dpa-1")
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                field_name="phase7_signature_dpa",
                parent_id=incident.pk,
            ).exists()
        )

    def test_green_accept_allows_dpa_reviewer(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7DPA-G",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.GREEN,
            pic_user_id="pic-1",
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        self._seed_prior_chain(incident)

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "DPA Reviewer", "device_fingerprint": "device-dpa-green"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", user_id="dpa-green", process_ids=["SAF_P_004"]),
        )

        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self._assert_closed_by_office_review(incident)
        self.assertEqual(incident.dpa_accepted_by, "dpa-green")

    def test_yellow_accept_allows_pic_reviewer(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7PIC-Y",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        self._seed_prior_chain(incident)

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "PIC Reviewer", "device_fingerprint": "device-pic-yellow"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="OFFICE_PIC", user_id="pic-yellow", process_ids=["SAF_P_006"]),
        )

        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self._assert_closed_by_office_review(incident)
        self.assertEqual(incident.dpa_accepted_by, "pic-yellow")

    def test_green_accept_allows_role_based_pic_reviewer_assignment(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7A3",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.GREEN,
            pic_user_id="OFFICE_PIC",
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        self._seed_prior_chain(incident)

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "PIC Reviewer", "device_fingerprint": "device-pic-1"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="OFFICE_SSQE", user_id="ssqe-1", process_ids=["SAF_P_006"]),
        )

        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self._assert_closed_by_office_review(incident)

    def test_green_accept_uses_central_vims_office_role_before_profile_role(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7A4",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.GREEN,
            pic_user_id="OFFICE_PIC",
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        self._seed_prior_chain(incident)

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "PIC Reviewer", "device_fingerprint": "device-pic-2"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role="OFFICE_PIC",
                role_name="TECHNICAL SUPERINTENDENT",
                safety_role_name="TECHNICAL SUPERINTENDENT",
                user_id="pic-1",
                process_ids=["SAF_P_006"],
            ),
        )

        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self._assert_closed_by_office_review(incident)

    def test_green_accept_allows_pic_alias_role(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7A5",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.GREEN,
            pic_user_id="OFFICE_PIC",
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        self._seed_prior_chain(incident)

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "PIC Reviewer", "device_fingerprint": "device-pic-3"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="PIC", user_id="pic-2", process_ids=["SAF_P_006"]),
        )

        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self._assert_closed_by_office_review(incident)

    def test_yellow_accept_saves_office_comment_without_length_limit(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7C1",
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
        self._seed_prior_chain(incident)
        long_comment = "Office review comment. " * 600

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {
                "typed_name": "DPA Reviewer",
                "device_fingerprint": "device-dpa-2",
                "office_comment": long_comment,
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", user_id="dpa-2", process_ids=["SAF_P_004"]),
        )

        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.office_comment, long_comment.strip())
        self.assertEqual(response.data["office_comment"], long_comment.strip())
        self.assertEqual(build_phase7_preflight_payload(incident)["office_comment"], long_comment.strip())
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                field_name="office_comment",
                parent_id=incident.pk,
                actor_user_id="dpa-2",
            ).exists()
        )

    def test_phase_seven_optional_hod_signature_can_be_captured_by_chief_engineer(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7HOD",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.GREEN,
            pic_user_id="OFFICE_PIC",
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=1,
            phase_to=2,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/hod-signature/",
            {"typed_name": "Chief Engineer", "device_fingerprint": "device-ce-1"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="CE", user_id="ksm0190", process_ids=[]),
        )

        response = self.hod_signature_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertNotIn("hod_signature", build_phase7_preflight_payload(incident)["blockers"])
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                field_name="phase7_signature_hod",
                parent_id=incident.pk,
                actor_user_id="ksm0190",
                actor_role_code="CE",
            ).exists()
        )

    def test_red_band_can_be_accepted_by_dpa_without_fm(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7A2",
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
        self._seed_prior_chain(incident)

        dpa_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "DPA Reviewer", "device_fingerprint": "device-dpa-1"},
            format="json",
        )
        force_authenticate(
            dpa_request,
            user=build_user(role_name="DPA", user_id="dpa-1", process_ids=["SAF_P_004"]),
        )
        dpa_response = self.accept_view(dpa_request, id=incident.pk)
        self.assertEqual(dpa_response.status_code, 200)
        self._assert_closed_by_office_review(incident)
        self.assertEqual(incident.dpa_accepted_by, "dpa-1")
        self.assertIsNone(incident.fm_approved_by)

    def test_red_band_can_be_accepted_by_pic_without_fm(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P7PIC-R",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.RED,
            pic_user_id="pic-1",
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )
        self._seed_prior_chain(incident)

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
            {"typed_name": "PIC Reviewer", "device_fingerprint": "device-pic-red"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="PIC", user_id="pic-red", process_ids=["SAF_P_006"]),
        )
        response = self.accept_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self._assert_closed_by_office_review(incident)
        self.assertEqual(incident.dpa_accepted_by, "pic-red")
        self.assertIsNone(incident.fm_approved_by)
