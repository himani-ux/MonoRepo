from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, Recommendation
from apps.safety.views.incident_phase6 import IncidentRecommendationListCreateView


def build_user():
    return SimpleNamespace(
        id="master-7",
        username="master-7",
        role_name="MASTER",
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class TolerableFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentRecommendationListCreateView.as_view()

    def test_green_band_allows_tolerable_failure_flag(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/TOL1",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.GREEN,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.LESSONS_LEARNT,
                "title": "Trend already handled in fleet Pareto",
                "description": "GREEN-band preventive-maintenance repeat recorded for trend linkage.",
                "tolerable_failure_filter": True,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tolerable_failure_filter"], True)

    def test_yellow_band_rejects_tolerable_failure_flag(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/TOL2",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/recommendations/",
            {
                "tier": Recommendation.Tier.LESSONS_LEARNT,
                "title": "Attempt invalid tolerable-failure flag",
                "description": "YELLOW-band incidents cannot use the tolerable-failure storage flag.",
                "tolerable_failure_filter": True,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("tolerable_failure_filter", response.data)

