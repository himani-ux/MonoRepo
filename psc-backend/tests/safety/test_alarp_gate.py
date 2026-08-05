from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, Recommendation
from apps.safety.services.alarp_gate import AlarpGate
from apps.safety.views.incident_phase6 import IncidentRecommendationListCreateView


def build_user():
    return SimpleNamespace(
        id="dpa-1",
        username="dpa-1",
        role_name="DPA",
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


@dataclass
class RecommendationStub:
    tier: str


class AlarpGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentRecommendationListCreateView.as_view()
        self.gate = AlarpGate()

    def test_require_alarp_is_true_for_preventive_rows_on_yellow_and_red(self) -> None:
        yellow_incident = Incident(risk_band=Incident.RiskBand.YELLOW)
        red_incident = Incident(risk_band=Incident.RiskBand.RED)
        green_incident = Incident(risk_band=Incident.RiskBand.GREEN)
        preventive = RecommendationStub(tier=Recommendation.Tier.PREVENTIVE)
        corrective = RecommendationStub(tier=Recommendation.Tier.CORRECTIVE)

        self.assertTrue(self.gate.require_alarp(yellow_incident, preventive))
        self.assertTrue(self.gate.require_alarp(red_incident, preventive))
        self.assertFalse(self.gate.require_alarp(green_incident, preventive))
        self.assertFalse(self.gate.require_alarp(yellow_incident, corrective))

    def test_incident_attestation_is_complete_when_no_alarp_rows_are_required(self) -> None:
        green_incident = Incident(risk_band=Incident.RiskBand.GREEN)

        self.assertTrue(
            self.gate.incident_attestation_complete(
                green_incident,
                [RecommendationStub(tier=Recommendation.Tier.PREVENTIVE)],
            )
        )

    def test_yellow_preventive_row_saves_without_risk_reduction_or_due_date(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/ALARP1",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.PREVENTIVE,
                "title": "Revise fleet crane maintenance standard",
                "description": "System action is recorded as a description-only preventive action.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["estimated_likelihood_reduction"], None)
        self.assertEqual(response.data["corrective_actions"], [])

    def test_green_preventive_row_can_save_without_theme_effort_or_residual_fields(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/ALARP2",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.GREEN,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.PREVENTIVE,
                "title": "Refresh toolbox talk content",
                "description": "GREEN-band preventive row may save without ALARP attestation.",
                "estimated_likelihood_reduction": Recommendation.LikelihoodReduction.LOW,
                "corrective_action": {
                    "verifier_user_id": "dpa-1",
                    "due_date": "2026-07-20",
                },
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["alarp_attested"], False)
