from __future__ import annotations

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

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import (
    Incident,
    IncidentBiasGuardResponse,
    IncidentBlameOverride,
    IncidentCauseTag,
    IncidentFact,
    MasterMscatTaxonomy,
    MasterSafetyBiasGuard,
)
from apps.safety.repositories.exceptions import PhaseTransitionError
from apps.safety.services.blame_detector import BlameDetector
from apps.safety.services.phase_state_machine import PhaseStateMachine
from apps.safety.views.incident_phase5 import IncidentBlameOverrideView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_009"],
        vessel_ids=["7"],
        is_global=False,
    )


class BlameFixationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_phase5_reference_tables()
        seed_phase5_reference_tables()
        self.factory = APIRequestFactory()
        self.override_view = IncidentBlameOverrideView.as_view()
        self.machine = PhaseStateMachine()
        self.detector = BlameDetector()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/BLAME",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.GREEN,
            alarp_attested=True,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            narrative="Initial conclusion focused on operator fault and negligence.",
        )
        self.fact = IncidentFact.objects.create(
            incident=self.incident,
            sequence_index=1,
            fact_text="Evidence fact linked into the causal analysis.",
            source_evidence_id=44,
            confidence=IncidentFact.Confidence.HIGH,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        personal_factor = MasterMscatTaxonomy.objects.filter(category_id__in=[1, 2, 3, 4]).first()
        self.assertIsNotNone(personal_factor)
        IncidentCauseTag.objects.create(
            incident=self.incident,
            source_fact=self.fact,
            mscat_subcode_id=personal_factor.subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.FACT_TREE,
            rationale="Crew fault was recorded without system context.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        guard_codes = list(
            MasterSafetyBiasGuard.objects.order_by("bit_position").values_list("guard_code", flat=True)
        )
        for index, guard_code in enumerate(guard_codes):
            IncidentBiasGuardResponse.objects.create(
                incident=self.incident,
                guard_code=guard_code,
                acknowledged=True,
                evaluation_state=IncidentBiasGuardResponse.EvaluationState.PASSED,
                acknowledged_by="dpa-1",
                created_by="dpa-1",
                updated_by="dpa-1",
                schema_version=1,
            )
        self.incident.bias_guard_attestations = "11111111"
        self.incident.save(update_fields=["bias_guard_attestations"])

    def test_detector_flags_blame_language(self) -> None:
        evaluation = self.detector.evaluate_incident(self.incident)

        self.assertTrue(evaluation.blocked)
        self.assertIn("negligence", evaluation.trigger_terms)

    def test_override_endpoint_requires_phase_authority_and_long_justification(self) -> None:
        short_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/override-blame/",
            {"justification": "too short"},
            format="json",
        )
        force_authenticate(
            short_request,
            user=build_user(role_name="DPA", user_id="dpa-1"),
        )
        short_response = self.override_view(short_request, id=self.incident.pk)
        self.assertEqual(short_response.status_code, 400)

        wrong_role_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/override-blame/",
            {"justification": "J" * 220},
            format="json",
        )
        force_authenticate(
            wrong_role_request,
            user=build_user(role_name="MASTER", user_id="master-7"),
        )
        wrong_role_response = self.override_view(wrong_role_request, id=self.incident.pk)
        self.assertEqual(wrong_role_response.status_code, 403)

        valid_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/override-blame/",
            {"justification": "J" * 220},
            format="json",
        )
        force_authenticate(
            valid_request,
            user=build_user(role_name="DPA", user_id="dpa-1"),
        )
        valid_response = self.override_view(valid_request, id=self.incident.pk)
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(IncidentBlameOverride.objects.count(), 1)

    def test_phase_six_to_seven_requires_override_when_blame_fixation_is_detected(self) -> None:
        with self.assertRaises(PhaseTransitionError):
            self.machine.transition(self.incident.id, 7, build_user(role_name="DPA", user_id="dpa-1"))

        IncidentBlameOverride.objects.create(
            incident=self.incident,
            justification="J" * 220,
            approved_by="dpa-1",
            approved_role="DPA",
            approved_at=timezone.now(),
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        self.incident.blame_fixation_override_by = "dpa-1"
        self.incident.save(update_fields=["blame_fixation_override_by"])

        result = self.machine.transition(
            self.incident.id,
            7,
            build_user(role_name="DPA", user_id="dpa-1"),
        )
        self.assertEqual(result["phase_to"], 7)
