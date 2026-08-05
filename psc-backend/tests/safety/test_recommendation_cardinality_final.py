from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, Recommendation
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
        process_ids=process_ids or ["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class RecommendationCardinalityFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.list_view = IncidentRecommendationListCreateView.as_view()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/REC-CARD",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

    def test_database_allows_multiple_active_rows_per_incident_tier(self) -> None:
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Share engine-room toolbox lesson",
            description="Publish the lesson learned through the standard circular flow.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Second lessons tier row",
            description="A second active row for the same tier is allowed.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        self.assertEqual(
            Recommendation.objects.filter(
                incident=self.incident,
                tier=Recommendation.Tier.LESSONS_LEARNT,
                is_deleted=False,
            ).count(),
            2,
        )

    def test_soft_deleted_recommendation_can_be_replaced_for_same_tier(self) -> None:
        recommendation = Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Retire old lesson row",
            description="This older tier row is being replaced.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        recommendation.is_deleted = True
        recommendation.save(update_fields=["is_deleted"])

        replacement = Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Replacement lesson row",
            description="The active replacement should be allowed once the prior row is soft-deleted.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        self.assertIsNotNone(replacement.pk)
        self.assertEqual(
            Recommendation.objects.filter(
                incident=self.incident,
                tier=Recommendation.Tier.LESSONS_LEARNT,
                is_deleted=False,
            ).count(),
            1,
        )

    def test_api_allows_duplicate_active_corrective_tier(self) -> None:
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Original corrective row",
            description="Inspect the damaged safety guard.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.CORRECTIVE,
                "title": "Second corrective row",
                "description": "Replace the damaged safety guard.",
                "corrective_action": {
                    "due_date": "2026-07-20",
                    "verifier_user_id": "master-7",
                },
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Recommendation.objects.filter(
                incident=self.incident,
                tier=Recommendation.Tier.CORRECTIVE,
                is_deleted=False,
            ).count(),
            2,
        )

    def test_phase3_api_allows_duplicate_active_corrective_tier(self) -> None:
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Original corrective row",
            description="Inspect the damaged safety guard.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/phase-3/recommendations/",
            {
                "tier": Recommendation.Tier.CORRECTIVE,
                "title": "Second corrective row",
                "description": "Replace the damaged safety guard.",
                "corrective_action": {
                    "due_date": "2026-07-20",
                    "verifier_user_id": "master-7",
                },
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Recommendation.objects.filter(
                incident=self.incident,
                tier=Recommendation.Tier.CORRECTIVE,
                is_deleted=False,
            ).count(),
            2,
        )

    def test_api_allows_duplicate_active_preventive_tier(self) -> None:
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.PREVENTIVE,
            title="Original preventive row",
            description="Inspect adjacent safety guards during weekly rounds.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.PREVENTIVE,
                "title": "Second preventive row",
                "description": "Add recurring guard-condition verification.",
                "estimated_likelihood_reduction": Recommendation.LikelihoodReduction.MED,
                "corrective_action": {
                    "due_date": "2026-07-21",
                    "verifier_user_id": "master-7",
                },
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Recommendation.objects.filter(
                incident=self.incident,
                tier=Recommendation.Tier.PREVENTIVE,
                is_deleted=False,
            ).count(),
            2,
        )

    def test_phase3_api_allows_duplicate_active_preventive_tier(self) -> None:
        Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.PREVENTIVE,
            title="Original preventive row",
            description="Inspect adjacent safety guards during weekly rounds.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/phase-3/recommendations/",
            {
                "tier": Recommendation.Tier.PREVENTIVE,
                "title": "Second preventive row",
                "description": "Add recurring guard-condition verification.",
                "estimated_likelihood_reduction": Recommendation.LikelihoodReduction.MED,
                "corrective_action": {
                    "due_date": "2026-07-21",
                    "verifier_user_id": "master-7",
                },
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Recommendation.objects.filter(
                incident=self.incident,
                tier=Recommendation.Tier.PREVENTIVE,
                is_deleted=False,
            ).count(),
            2,
        )
