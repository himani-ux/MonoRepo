from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.services.signature_chain import SignatureChainService


def build_user(role_name: str, user_id: str):
    return SimpleNamespace(id=user_id, username=user_id, role_name=role_name)


class SignatureChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.service = SignatureChainService()

    def test_red_band_requires_dpa_before_fm(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/SIG1",
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

        blockers = self.service.phase_seven_blockers(incident, action_role=SignatureChainService.FM)
        self.assertIn("dpa_signature", blockers)

        self.service.stamp_phase7_signature(
            incident,
            role_code=SignatureChainService.DPA,
            typed_name="DPA Reviewer",
            device_fingerprint="device-dpa-1",
            user=build_user("DPA", "dpa-1"),
        )

        preflight_blockers = self.service.phase_seven_blockers(incident)
        self.assertIn("fm_signature", preflight_blockers)

        blockers = self.service.phase_seven_blockers(incident, action_role=SignatureChainService.FM)
        self.assertNotIn("dpa_signature", blockers)

    def test_yellow_band_detects_missing_hod_signature(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/SIG2",
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
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=1,
            phase_to=2,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )

        blockers = self.service.phase_seven_blockers(incident, action_role=SignatureChainService.DPA)
        self.assertIn("hod_signature", blockers)
