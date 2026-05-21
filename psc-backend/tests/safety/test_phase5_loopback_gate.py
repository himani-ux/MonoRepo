from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_phase5_reference_tables,
    seed_phase5_reference_tables,
)


bootstrap_django()

from apps.safety.models import (
    EvidenceItem,
    Incident,
    IncidentCauseTag,
    IncidentFact,
    IncidentPhase5Assessment,
    IncidentSafeguardFailure,
    MasterMscatTaxonomy,
)
from apps.safety.repositories.exceptions import PhaseTransitionError
from apps.safety.services.phase_state_machine import PhaseStateMachine


def build_user(role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(id=user_id, username=user_id, role_name=role_name)


class Phase5GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_phase5_reference_tables()
        seed_phase5_reference_tables()
        self.machine = PhaseStateMachine()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/PH5G",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=5,
            risk_band=Incident.RiskBand.YELLOW,
            investigation_depth=Incident.InvestigationDepth.MEDIUM,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            occurred_at=timezone.now() - timedelta(hours=1),
        )
        self.fact = IncidentFact.objects.create(
            incident=self.incident,
            sequence_index=1,
            fact_text="Captured evidence shows the bridge resource breakdown and follow-up control gaps.",
            fact_timestamp=self.incident.occurred_at - timedelta(minutes=5),
            source_evidence_id=77,
            confidence=IncidentFact.Confidence.HIGH,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        self.root_code = MasterMscatTaxonomy.objects.first()
        self.other_code = MasterMscatTaxonomy.objects.exclude(
            subcode_id=self.root_code.subcode_id
        ).first()

    def _create_complete_phase5_payload(self) -> None:
        IncidentPhase5Assessment.objects.create(
            incident=self.incident,
            people_contribution_text="P" * 60,
            process_gap_text="R" * 60,
            plant_failure_text="L" * 60,
            analysis_tools_used=[
                IncidentPhase5Assessment.AnalysisTool.STEP,
                IncidentPhase5Assessment.AnalysisTool.FACT_TREE,
                IncidentPhase5Assessment.AnalysisTool.BARRIER,
            ],
            human_factors_payload={
                "domains": {
                    "people": {"considered": True, "notes": "Crew coordination reviewed."},
                    "organisation": {"considered": True, "notes": "Office support reviewed."},
                    "working_conditions": {"considered": True, "notes": "Fatigue context reviewed."},
                    "ship_factors": {"considered": True, "notes": "Bridge layout reviewed."},
                    "shore_side": {"considered": True, "notes": "Shore oversight reviewed."},
                    "external": {"considered": True, "notes": "Traffic and weather reviewed."},
                    "sequence": {"considered": True, "notes": "Timeline interactions reviewed."},
                    "risk_change": {"considered": True, "notes": "Risk and change controls reviewed."},
                }
            },
            monocausal_justification="M" * 90,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=self.incident,
            source_fact=self.fact,
            mscat_subcode_id=self.other_code.subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.INTERMEDIATE,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Intermediate condition kept for the layered chain.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=self.incident,
            source_fact=self.fact,
            mscat_subcode_id=self.root_code.subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.BARRIER,
            rationale="Lack-of-control root cause closes the causal chain.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        IncidentSafeguardFailure.objects.create(
            incident=self.incident,
            safeguard_name="Bridge team challenge-response barrier",
            design_mscat_subcode_id=self.root_code.subcode_id,
            installation_mscat_subcode_id=self.other_code.subcode_id,
            maintenance_mscat_subcode_id=self.other_code.subcode_id,
            operation_mscat_subcode_id=self.other_code.subcode_id,
            testing_mscat_subcode_id=self.other_code.subcode_id,
            override_mscat_subcode_id=self.other_code.subcode_id,
            notes="All six safeguard dimensions coded for the failed control.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        EvidenceItem.objects.create(
            incident=self.incident,
            item_type=EvidenceItem.ItemType.MATRIX,
            title="Evidence matrix row",
            finding="Major finding 1",
            pro_evidence="Bridge log and ECDIS track support the finding.",
            con_evidence="Witness readback challenges the timing assumption.",
            metadata_json={"major_finding": True},
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

    def test_phase_five_to_six_passes_when_analysis_gate_is_complete(self) -> None:
        self._create_complete_phase5_payload()

        result = self.machine.transition(self.incident.id, 6, build_user())

        self.incident.refresh_from_db()
        self.assertEqual(self.incident.current_phase, 6)
        self.assertEqual(result["phase_to"], 6)

    def test_phase_five_to_six_rejects_missing_root_cause(self) -> None:
        assessment = IncidentPhase5Assessment.objects.create(
            incident=self.incident,
            people_contribution_text="P" * 60,
            process_gap_text="R" * 60,
            plant_failure_text="L" * 60,
            analysis_tools_used=[
                IncidentPhase5Assessment.AnalysisTool.STEP,
                IncidentPhase5Assessment.AnalysisTool.FACT_TREE,
                IncidentPhase5Assessment.AnalysisTool.BARRIER,
            ],
            human_factors_payload={"domains": {"risk_change": {"considered": True, "notes": "Reviewed."}}},
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        self.assertIsNotNone(assessment.pk)
        IncidentCauseTag.objects.create(
            incident=self.incident,
            source_fact=self.fact,
            mscat_subcode_id=self.other_code.subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.IMMEDIATE,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Immediate cause only.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(self.incident.id, 6, build_user())

    def test_phase_five_to_six_rejects_major_finding_without_con_evidence(self) -> None:
        self._create_complete_phase5_payload()
        EvidenceItem.objects.all().delete()
        EvidenceItem.objects.create(
            incident=self.incident,
            item_type=EvidenceItem.ItemType.MATRIX,
            title="Evidence matrix row",
            finding="Major finding 1",
            pro_evidence="Bridge log supports the finding.",
            con_evidence="",
            metadata_json={"major_finding": True},
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(self.incident.id, 6, build_user())
