from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_phase5_reference_tables,
    seed_phase5_reference_tables,
)


bootstrap_django()

from apps.safety.models import Incident, Recommendation
from apps.safety.repositories.exceptions import PhaseTransitionError
from apps.safety.services.phase_state_machine import PhaseStateMachine


def build_user(role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
    )


class Phase6SubmitTests(unittest.TestCase):
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
            incident_number="ABC/2026/PH6",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            bias_guard_attestations="11111111",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
            narrative="Phase 6 record with neutral investigation language.",
        )

    def test_yellow_band_requires_all_three_recommendation_tiers(self) -> None:
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Replace damaged portable light",
            description="Immediate vessel corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.PREVENTIVE,
            theme_code="EQUIPMENT_MANAGEMENT",
            title="Standardise electrical inspection checklist",
            description="Fleet-wide preventive action.",
            estimated_effort="2 superintendent days",
            estimated_likelihood_reduction="MED",
            residual_risk_statement="Residual electrical risk becomes tolerable after checklist control.",
            alarp_attested=True,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(self.incident.id, 7, build_user())

    def test_green_band_requires_at_least_one_recommendation(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/PH6G",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.GREEN,
            bias_guard_attestations="11111111",
            created_by="pic-1",
            updated_by="pic-1",
            schema_version=1,
            narrative="Phase 6 green record still needs a recommendation before follow-up.",
        )

        with self.assertRaises(PhaseTransitionError) as context:
            self.machine.transition(incident.id, 7, build_user(role_name="OFFICE_PIC", user_id="pic-1"))

        self.assertIn("recommendations", str(context.exception))

    def test_yellow_band_can_advance_when_all_tiers_and_alarp_are_complete(self) -> None:
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Replace damaged portable light",
            description="Immediate vessel corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.PREVENTIVE,
            theme_code="EQUIPMENT_MANAGEMENT",
            title="Standardise electrical inspection checklist",
            description="Fleet-wide preventive action.",
            estimated_effort="2 superintendent days",
            estimated_likelihood_reduction="MED",
            residual_risk_statement="Residual electrical risk becomes tolerable after checklist control.",
            alarp_attested=True,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Share portable-light inspection lesson",
            description="Lessons learned circular summary for fleet distribution.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        result = self.machine.transition(self.incident.id, 7, build_user())

        self.assertEqual(result["phase_to"], 7)
