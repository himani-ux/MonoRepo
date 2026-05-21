from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import EvidenceItem, Incident, IncidentEvidence, IncidentFact
from apps.safety.views.incident_phase4 import (
    IncidentPhase4EvidenceSourceListView,
    IncidentPhase4FactContradictionView,
    IncidentPhase4FactDetailView,
    IncidentPhase4FactListCreateView,
    IncidentPhase4GateView,
    IncidentPhase4FactReorderView,
)


def build_user(
    *,
    role_name: str = "MASTER",
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_002"],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class IncidentFactBaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.list_create_view = IncidentPhase4FactListCreateView.as_view()
        self.detail_view = IncidentPhase4FactDetailView.as_view()
        self.source_list_view = IncidentPhase4EvidenceSourceListView.as_view()
        self.gate_view = IncidentPhase4GateView.as_view()
        self.reorder_view = IncidentPhase4FactReorderView.as_view()
        self.contradiction_view = IncidentPhase4FactContradictionView.as_view()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/004",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            occurred_at=timezone.now(),
        )
        self.evidence = EvidenceItem.objects.create(
            incident=self.incident,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Bridge wing photo",
            description="Photo set from bridge wing.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

    def test_fact_creation_reorder_and_contradiction_flow(self) -> None:
        user = build_user()
        create_first = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/facts/",
            {
                "fact_text": "Helm order to port 10 was logged before the impact.",
                "fact_timestamp": (self.incident.occurred_at - timedelta(minutes=3)).isoformat(),
                "source_evidence_id": self.evidence.pk,
                "confidence": IncidentFact.Confidence.HIGH,
            },
            format="json",
        )
        force_authenticate(create_first, user=user)
        first_response = self.list_create_view(create_first, id=self.incident.pk)

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(first_response.data["sequence_index"], 1)
        self.assertEqual(first_response.data["confidence"], IncidentFact.Confidence.HIGH)

        create_second = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/facts/",
            {
                "fact_text": "ECDIS playback shows the vessel steady on heading 115.",
                "fact_timestamp": (self.incident.occurred_at - timedelta(minutes=1)).isoformat(),
                "source_evidence_id": self.evidence.pk,
                "confidence": IncidentFact.Confidence.MEDIUM,
            },
            format="json",
        )
        force_authenticate(create_second, user=user)
        second_response = self.list_create_view(create_second, id=self.incident.pk)
        self.assertEqual(second_response.status_code, 201)

        fact_ids = list(IncidentFact.objects.order_by("sequence_index", "id").values_list("id", flat=True))
        reorder_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/facts/reorder/",
            {"ordered_fact_ids": [fact_ids[1], fact_ids[0]]},
            format="json",
        )
        force_authenticate(reorder_request, user=user)
        reorder_response = self.reorder_view(reorder_request, id=self.incident.pk)

        self.assertEqual(reorder_response.status_code, 200)
        self.assertEqual([row["id"] for row in reorder_response.data], [fact_ids[1], fact_ids[0]])

        contradiction_request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/facts/contradictions/",
            {
                "fact_id": fact_ids[0],
                "contradicts_fact_id": fact_ids[1],
            },
            format="json",
        )
        force_authenticate(contradiction_request, user=user)
        contradiction_response = self.contradiction_view(contradiction_request, id=self.incident.pk)

        self.assertEqual(contradiction_response.status_code, 200)
        self.assertEqual(contradiction_response.data["contradicts_fact"], fact_ids[1])

    def test_fact_detail_patch_updates_fact_not_parent_incident(self) -> None:
        fact = IncidentFact.objects.create(
            incident=self.incident,
            sequence_index=1,
            fact_text="Initial fact text.",
            source_evidence_id=self.evidence.pk,
            confidence=IncidentFact.Confidence.MEDIUM,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.patch(
            f"/api/safety/incidents/{self.incident.pk}/facts/{fact.pk}/",
            {
                "fact_text": "Updated fact text.",
                "source_evidence_id": self.evidence.pk,
                "confidence": IncidentFact.Confidence.HIGH,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())
        response = self.detail_view(request, id=self.incident.pk, fact_id=fact.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], fact.pk)
        self.assertEqual(response.data["fact_text"], "Updated fact text.")
        self.assertEqual(response.data["confidence"], IncidentFact.Confidence.HIGH)
        fact.refresh_from_db()
        self.assertEqual(fact.fact_text, "Updated fact text.")
        self.assertEqual(fact.confidence, IncidentFact.Confidence.HIGH)

    def test_phase_four_lists_valid_evidence_sources(self) -> None:
        request = self.factory.get(f"/api/safety/incidents/{self.incident.pk}/facts/sources/")
        force_authenticate(request, user=build_user())
        response = self.source_list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["id"], self.evidence.pk)
        self.assertEqual(response.data[0]["label"], "Bridge wing photo")
        self.assertEqual(response.data[0]["source_type"], EvidenceItem.ItemType.PHYSICAL)

    def test_fact_can_link_to_phase_three_evidence_tab_summary(self) -> None:
        tab_only_incident = Incident.objects.create(
            incident_number="ABC/2026/004-TAB",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            occurred_at=timezone.now(),
        )
        tab = IncidentEvidence.objects.create(
            incident=tab_only_incident,
            tab_code=IncidentEvidence.TabCode.PEOPLE,
            summary="Crew statements and fatigue notes captured in Phase 3.",
            entry_count=2,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        source_request = self.factory.get(f"/api/safety/incidents/{tab_only_incident.pk}/facts/sources/")
        force_authenticate(source_request, user=build_user())
        source_response = self.source_list_view(source_request, id=tab_only_incident.pk)

        self.assertEqual(source_response.status_code, 200)
        self.assertEqual(source_response.data[0]["id"], tab.pk)
        self.assertEqual(source_response.data[0]["source_type"], "EVIDENCE_TAB")

        create_request = self.factory.post(
            f"/api/safety/incidents/{tab_only_incident.pk}/facts/",
            {
                "fact_text": "Two crew statements consistently described fatigue before the event.",
                "source_evidence_id": tab.pk,
                "confidence": IncidentFact.Confidence.MEDIUM,
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())
        create_response = self.list_create_view(create_request, id=tab_only_incident.pk)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["source_evidence_id"], tab.pk)
        self.assertIn("PEOPLE", create_response.data["evidence_summary"])

    def test_phase_four_gate_reports_missing_evidence_tabs_before_transition(self) -> None:
        request = self.factory.get(f"/api/safety/incidents/{self.incident.pk}/facts/gate/")
        force_authenticate(request, user=build_user())
        response = self.gate_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["can_continue"])
        self.assertIn("POSITION", response.data["missing_tabs"])
        self.assertIn("Complete or mark N/A", response.data["blockers"][0])

    def test_fact_requires_linked_evidence_reference(self) -> None:
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/facts/",
            {
                "fact_text": "A witness estimated low visibility during the turn.",
                "confidence": IncidentFact.Confidence.LOW,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())
        response = self.list_create_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("source_evidence_id", response.data)
