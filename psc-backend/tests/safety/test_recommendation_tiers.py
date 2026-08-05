from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import CorrectiveAction, Incident, Recommendation
from apps.safety.views.incident_phase6 import IncidentRecommendationDetailView, IncidentRecommendationListCreateView


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


class RecommendationTierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.list_view = IncidentRecommendationListCreateView.as_view()
        self.detail_view = IncidentRecommendationDetailView.as_view()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/REC1",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

    def test_corrective_recommendation_records_description_without_linked_action(self) -> None:
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.CORRECTIVE,
                "title": "Replace failed guard on vessel crane interlock",
                "description": "Immediate vessel action to restore the failed protective control.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tier"], Recommendation.Tier.CORRECTIVE)
        self.assertEqual(response.data["corrective_actions"], [])
        self.assertEqual(CorrectiveAction.objects.count(), 0)

    def test_corrective_recommendation_rejects_long_corrective_action_ids(self) -> None:
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.CORRECTIVE,
                "title": "Replace failed guard on vessel crane interlock",
                "description": "Immediate vessel action to restore the failed protective control.",
                "corrective_action": {
                    "assigned_crew_id": "bosun-4",
                    "verifier_user_id": "x" * 65,
                    "due_date": "2026-05-30",
                },
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("corrective_action", response.data)
        self.assertEqual(CorrectiveAction.objects.count(), 0)

    def test_preventive_recommendation_records_description_without_due_date_or_risk_reduction(self) -> None:
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.PREVENTIVE,
                "title": "Revise crane maintenance governance",
                "description": "Fleet-wide system action to standardise maintenance controls.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tier"], Recommendation.Tier.PREVENTIVE)
        self.assertEqual(response.data["estimated_likelihood_reduction"], None)
        self.assertEqual(response.data["corrective_actions"], [])
        self.assertEqual(CorrectiveAction.objects.count(), 0)

    def test_preventive_recommendation_creates_due_date_action(self) -> None:
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.PREVENTIVE,
                "title": "Revise crane maintenance governance",
                "description": "Fleet-wide system action to standardise maintenance controls.",
                "estimated_likelihood_reduction": Recommendation.LikelihoodReduction.HIGH,
                "corrective_action": {
                    "verifier_user_id": "master-7",
                    "due_date": "2026-07-30",
                },
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tier"], Recommendation.Tier.PREVENTIVE)
        self.assertEqual(CorrectiveAction.objects.count(), 1)
        action = CorrectiveAction.objects.get()
        self.assertEqual(action.recommendation.tier, Recommendation.Tier.PREVENTIVE)
        self.assertEqual(action.due_date.isoformat(), "2026-07-30")

    def test_corrective_action_fields_can_be_updated_through_recommendation_detail(self) -> None:
        recommendation = Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Secure loose ladder stopper",
            description="Correct vessel-specific housekeeping control immediately.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=recommendation,
            title=recommendation.title,
            description=recommendation.description,
            verifier_user_id="master-7",
            due_date="2026-05-25",
            status=CorrectiveAction.Status.OPEN,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        recommendation.linked_ca_ids = str(action.pk)
        recommendation.save(update_fields=["linked_ca_ids"])

        request = self.factory.patch(
            f"/api/safety/incidents/{self.incident.pk}/recommendations/{recommendation.pk}/",
            {
                "corrective_action": {
                    "assigned_office_user_id": "superintendent-9",
                    "verifier_user_id": "dpa-1",
                    "due_date": "2026-06-05",
                }
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.detail_view(request, id=self.incident.pk, recommendation_id=recommendation.pk)

        self.assertEqual(response.status_code, 200)
        action.refresh_from_db()
        self.assertEqual(action.assigned_office_user_id, "superintendent-9")
        self.assertEqual(action.verifier_user_id, "dpa-1")
