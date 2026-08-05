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

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentCauseTag, IncidentFact, MasterMscatTaxonomy, NearMissCauseOption
from apps.safety.views.incident_phase5 import IncidentMscatSearchView, IncidentPhase5CauseListCreateView, IncidentPhase5WorkspaceView


def build_user(role_name: str = "MASTER", user_id: str = "master-7"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class Phase5AnalysisApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_phase5_reference_tables()
        seed_phase5_reference_tables()
        self.factory = APIRequestFactory()
        self.workspace_view = IncidentPhase5WorkspaceView.as_view()
        self.search_view = IncidentMscatSearchView.as_view()
        self.cause_view = IncidentPhase5CauseListCreateView.as_view()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/API5",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=5,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            occurred_at=timezone.now() - timedelta(hours=2),
        )
        self.fact = IncidentFact.objects.create(
            incident=self.incident,
            sequence_index=1,
            fact_text="Shared fact base item used by the Phase 5 analysis tools.",
            fact_timestamp=self.incident.occurred_at - timedelta(minutes=10),
            source_evidence_id=51,
            confidence=IncidentFact.Confidence.HIGH,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        self.subcode = MasterMscatTaxonomy.objects.first()

    def test_mscat_search_endpoint_returns_ranked_results(self) -> None:
        request = self.factory.get(
            f"/api/safety/incidents/{self.incident.pk}/analysis/mscat/",
            {"q": "orientation"},
        )
        force_authenticate(request, user=build_user())
        response = self.search_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data["results"]), 0)

    def test_cause_create_and_workspace_load(self) -> None:
        create_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/analysis/causes/",
            {
                "source_fact_id": self.fact.pk,
                "mscat_subcode_id": self.subcode.subcode_id,
                "causal_layer": IncidentCauseTag.CausalLayer.ROOT,
                "analysis_tool": IncidentCauseTag.AnalysisTool.STEP,
                "rationale": "Root cause created from the shared fact base.",
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())
        create_response = self.cause_view(create_request, id=self.incident.pk)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["causal_layer"], IncidentCauseTag.CausalLayer.ROOT)

        workspace_request = self.factory.get(
            f"/api/safety/incidents/{self.incident.pk}/analysis/",
        )
        force_authenticate(workspace_request, user=build_user())
        workspace_response = self.workspace_view(workspace_request, id=self.incident.pk)

        self.assertEqual(workspace_response.status_code, 200)
        self.assertEqual(len(workspace_response.data["causes"]), 1)
        self.assertIn("bias_guards", workspace_response.data)

    def test_cause_create_accepts_near_miss_cause_factor_option(self) -> None:
        cause_option = NearMissCauseOption.objects.create(
            factor=NearMissCauseOption.Factor.HUMAN,
            cause_stage=NearMissCauseOption.CauseStage.ROOT,
            option_code="HUMAN_ROOT_TEST",
            option_text="Poor supervision",
            display_order=1,
        )
        create_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/analysis/causes/",
            {
                "source_fact_id": self.fact.pk,
                "cause_option_id": str(cause_option.pk),
                "causal_layer": IncidentCauseTag.CausalLayer.ROOT,
                "analysis_tool": IncidentCauseTag.AnalysisTool.STEP,
                "rationale": "Supervision gap was supported by the fact note.",
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())
        create_response = self.cause_view(create_request, id=self.incident.pk)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["cause_factor"], NearMissCauseOption.Factor.HUMAN)
        self.assertEqual(create_response.data["cause_factor_label"], "Human Factors")
        self.assertEqual(create_response.data["cause_option_text"], "Poor supervision")
        self.assertEqual(create_response.data["mscat_subcode_id"], "OTHER")

        workspace_request = self.factory.get(
            f"/api/safety/incidents/{self.incident.pk}/analysis/",
        )
        force_authenticate(workspace_request, user=build_user())
        workspace_response = self.workspace_view(workspace_request, id=self.incident.pk)

        self.assertEqual(workspace_response.status_code, 200)
        self.assertEqual(workspace_response.data["causes"][0]["cause_factor_label"], "Human Factors")
        self.assertEqual(workspace_response.data["causes"][0]["cause_option_text"], "Poor supervision")

    def test_cause_create_rejects_intermediate_layer(self) -> None:
        create_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/analysis/causes/",
            {
                "source_fact_id": self.fact.pk,
                "mscat_subcode_id": self.subcode.subcode_id,
                "causal_layer": IncidentCauseTag.CausalLayer.INTERMEDIATE,
                "analysis_tool": IncidentCauseTag.AnalysisTool.STEP,
                "rationale": "Intermediate cause should not be accepted in the current RCA flow.",
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())
        response = self.cause_view(create_request, id=self.incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("causal_layer", response.data)
