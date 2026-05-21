from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_scm_tables,
    recreate_soi_tables,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentCauseTag, IncidentFact
from apps.safety.services.cross_record_search import CrossRecordSearchService
from apps.safety.views.search import SafetyCrossRecordSearchView


def build_user(*, role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_005"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class CrossRecordSearchAfterFtsTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        recreate_soi_tables()
        self.service = CrossRecordSearchService()
        self.factory = APIRequestFactory()
        self.view = SafetyCrossRecordSearchView.as_view()
        self.user = build_user()
        self.current_at = timezone.now()

    def test_incident_search_matches_linked_mscat_code(self) -> None:
        incident = Incident.objects.create(
            incident_number="INC/2026/355",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=5,
            narrative="Hydraulic leak during cargo transfer required causal analysis.",
            occurred_at=self.current_at,
            created_by="dpa-7",
            updated_by="dpa-7",
            schema_version=1,
        )
        fact = IncidentFact.objects.create(
            incident=incident,
            sequence_index=1,
            fact_text="Hydraulic manifold maintenance was incomplete.",
            source_evidence_id=1001,
            confidence=IncidentFact.Confidence.HIGH,
            created_by="dpa-7",
        )
        IncidentCauseTag.objects.create(
            incident=incident,
            source_fact=fact,
            mscat_subcode_id="M-220",
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Maintenance governance issue coded from the fact base.",
            created_by="dpa-7",
        )

        payload = self.service.search("M-220", user=self.user, record_type="INCIDENT")

        self.assertEqual(payload["counts"]["INCIDENT"], 1)
        self.assertEqual(payload["total_count"], 1)
        self.assertEqual(payload["groups"]["INCIDENT"][0]["id"], incident.pk)
        self.assertEqual(payload["groups"]["INCIDENT"][0]["reference"], "INC/2026/355")

    def test_search_view_payload_shape_is_unchanged_after_fts_resolution(self) -> None:
        Incident.objects.create(
            incident_number="INC/2026/356",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=3,
            narrative="Hydraulic manifold leak observed during watch handover.",
            occurred_at=self.current_at,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.get("/api/safety/search/?q=manifold")
        force_authenticate(request, user=self.user)

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"counts", "groups", "include_archived", "labels", "query", "record_type", "total_count"},
        )
        self.assertIn("INCIDENT", response.data["groups"])
        self.assertEqual(response.data["query"], "manifold")
