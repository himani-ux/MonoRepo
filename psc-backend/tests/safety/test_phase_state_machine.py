from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, IncidentEvidence, IncidentPhaseLog
from apps.safety.repositories.exceptions import PhaseTransitionError
from apps.safety.services.phase_state_machine import PhaseStateMachine


def build_user(role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
    )


class PhaseStateMachineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.machine = PhaseStateMachine()

    def test_phase_one_to_two_is_allowed_when_intake_gate_is_complete(self) -> None:
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

        result = self.machine.transition(incident.id, 2, build_user("MASTER", "master-7"))

        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 2)
        self.assertEqual(result["transition_type"], IncidentPhaseLog.TransitionType.FORWARD)
        self.assertEqual(result["phase_from"], 1)
        self.assertEqual(result["phase_to"], 2)
        self.assertEqual(IncidentPhaseLog.objects.count(), 1)

    def test_illegal_jump_from_phase_three_to_five_is_rejected(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            schema_version=1,
        )

        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(incident.id, 5, build_user("MASTER", "master-7"))

        self.assertEqual(IncidentPhaseLog.objects.count(), 0)

    def test_phase_five_to_six_requires_root_cause_and_bias_guard_attestation(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=5,
            created_by="master-7",
            schema_version=1,
            causal_layering_complete=False,
            bias_guard_attestations="",
        )

        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(incident.id, 6, build_user("DPA"))

    def test_phase_four_to_five_requires_all_evidence_tabs_or_na_justification(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            schema_version=1,
        )
        for tab_code, _ in IncidentEvidence.TabCode.choices:
            IncidentEvidence.objects.create(
                incident=incident,
                tab_code=tab_code,
                summary=f"{tab_code} evidence captured",
                entry_count=1,
                created_by="master-7",
                updated_by="master-7",
                schema_version=1,
            )

        result = self.machine.transition(incident.id, 5, build_user("DPA"))

        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 5)
        self.assertEqual(result["phase_to"], 5)

    def test_phase_four_to_five_accepts_populated_evidence_tabs_without_manual_entry_counts(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T010",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            schema_version=1,
        )
        for tab_code, _ in IncidentEvidence.TabCode.choices:
            IncidentEvidence.objects.create(
                incident=incident,
                tab_code=tab_code,
                summary=f"{tab_code} evidence narrative captured",
                entry_count=0,
                created_by="master-7",
                updated_by="master-7",
                schema_version=1,
            )

        result = self.machine.transition(incident.id, 5, build_user("DPA"))

        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 5)
        self.assertEqual(result["phase_to"], 5)

    def test_phase_four_to_five_rejects_missing_evidence_tab_coverage(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            schema_version=1,
        )
        for tab_code, _ in IncidentEvidence.TabCode.choices:
            IncidentEvidence.objects.create(
                incident=incident,
                tab_code=tab_code,
                summary="" if tab_code == IncidentEvidence.TabCode.ELECTRONIC else f"{tab_code} evidence captured",
                entry_count=1 if tab_code != IncidentEvidence.TabCode.ELECTRONIC else 0,
                na_justification="Unavailable offshore" if tab_code == IncidentEvidence.TabCode.PAPER else None,
                created_by="master-7",
                updated_by="master-7",
                schema_version=1,
            )

        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(incident.id, 5, build_user("DPA"))

    def test_phase_seven_to_eight_requires_dpa_acceptance_stamp(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=7,
            reporter_id="reporter-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="reporter-device",
            reported_at=datetime(2026, 4, 27, 9, 0, tzinfo=timezone.utc),
            created_by="master-7",
            schema_version=1,
            risk_band=Incident.RiskBand.YELLOW,
            alarp_attested=True,
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

        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(incident.id, 8, build_user("DPA"))

        incident.dpa_accepted_at = datetime(2026, 4, 27, 10, 0, tzinfo=timezone.utc)
        incident.dpa_accepted_by = "dpa-1"
        incident.save(update_fields=["dpa_accepted_at", "dpa_accepted_by"])

        result = self.machine.transition(incident.id, 8, build_user("DPA"))

        self.assertEqual(result["phase_to"], 8)
