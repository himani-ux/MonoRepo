from __future__ import annotations

import unittest
from types import SimpleNamespace

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import EvidenceItem, ExternalPartyInjury, Incident, Recommendation
from apps.safety.repositories import IncidentRepository
from apps.safety.serializers.incident_phase2 import IncidentPhase2Serializer
from apps.safety.views.incident_external_party import IncidentExternalPartyInjuryView
from apps.safety.views.incident_phase1 import IncidentPhase1UpdateView
from apps.safety.views.incident_phase4 import IncidentPhase4FactListCreateView
from apps.safety.views.incident_phase5 import IncidentPhase5CauseListCreateView
from apps.safety.views.incident_phase6 import IncidentRecommendationListCreateView


def build_user(
    *,
    role_name: str = "MASTER",
    process_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_001", "SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class IncidentEditUntilOfficeApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.phase1_view = IncidentPhase1UpdateView.as_view()
        self.fact_view = IncidentPhase4FactListCreateView.as_view()
        self.injury_view = IncidentExternalPartyInjuryView.as_view()
        self.rca_cause_view = IncidentPhase5CauseListCreateView.as_view()
        self.recommendation_view = IncidentRecommendationListCreateView.as_view()
        self.repository = IncidentRepository()

    def test_completed_phase_one_remains_editable_before_office_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state=Incident.State.IN_PROGRESS,
            current_phase=6,
            narrative="Initial narrative before correction.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-1/",
            {"narrative": "Corrected intake narrative after later-phase review."},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.phase1_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.narrative, "Corrected intake narrative after later-phase review.")
        self.assertEqual(incident.current_phase, 6)

    def test_phase_two_serializer_allows_edit_after_forward_movement_before_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/002",
            vessel_id="7",
            state=Incident.State.IN_PROGRESS,
            current_phase=5,
            risk_band=Incident.RiskBand.GREEN,
            office_notified=True,
            office_notification_mode=Incident.OfficeNotificationMode.EMAIL,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        serializer = IncidentPhase2Serializer(
            incident,
            data={"office_notification_mode": Incident.OfficeNotificationMode.WHATSAPP},
            context={"incident_repository": self.repository},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rca_cause_can_be_saved_before_legacy_phase_gate_before_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/005",
            vessel_id="7",
            state=Incident.State.IN_PROGRESS,
            current_phase=2,
            risk_band=Incident.RiskBand.GREEN,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-2/analysis/causes/",
            {
                "analysis_tool": "STEP",
                "causal_layer": "IMMEDIATE",
                "mscat_subcode_id": "OTHER",
                "rationale": "Direct unsafe condition recorded while the incident is still editable.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.rca_cause_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(incident.cause_tags.count(), 1)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 2)

    def test_fact_can_be_saved_before_legacy_phase_gate_before_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/006",
            vessel_id="7",
            state=Incident.State.IN_PROGRESS,
            current_phase=2,
            risk_band=Incident.RiskBand.GREEN,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        evidence = EvidenceItem.objects.create(
            incident=incident,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Engine log",
            description="Engine log reviewed before formal evidence phase.",
            created_by="master-7",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-4/facts/",
            {
                "confidence": "MEDIUM",
                "fact_text": "The engine alarm was active before the stoppage.",
                "source_evidence_id": str(evidence.id),
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.fact_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(incident.facts.count(), 1)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 2)

    def test_recommendation_can_be_saved_before_legacy_phase_gate_before_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/007",
            vessel_id="7",
            state=Incident.State.IN_PROGRESS,
            current_phase=3,
            risk_band=Incident.RiskBand.GREEN,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-3/recommendations/",
            {
                "corrective_action": {
                    "due_date": "2026-07-10",
                    "verifier_user_id": "master-7",
                },
                "description": "Replace the damaged guard and confirm the repair.",
                "tier": Recommendation.Tier.CORRECTIVE,
                "title": "Replace damaged guard",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.recommendation_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(incident.recommendations.count(), 1)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 3)

    def test_injury_record_remains_editable_at_office_check_before_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/004",
            vessel_id="7",
            state=Incident.State.UNDER_REVIEW,
            current_phase=7,
            narrative="Incident at office check with injury details.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            party_name="Crew Member",
            created_by="master-7",
            schema_version=1,
        )

        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/external-party-injury/",
            {"notes": "Office check correction before approval."},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.injury_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.external_party_injury.refresh_from_db()
        self.assertEqual(incident.external_party_injury.notes, "Office check correction before approval.")

    def test_completed_phase_one_is_locked_after_office_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/003",
            vessel_id="7",
            state=Incident.State.APPROVED,
            current_phase=8,
            narrative="Approved narrative.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-1/",
            {"narrative": "Late edit after approval should fail."},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.phase1_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("office approval", str(response.data))


if __name__ == "__main__":
    unittest.main()
