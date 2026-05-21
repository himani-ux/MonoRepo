from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, Recommendation
from apps.safety.views.incident_phase8 import IncidentPhase8VerifyView


def build_user(*, role_name: str, user_id: str, process_ids: list[str]):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class RecommendationVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.verify_view = IncidentPhase8VerifyView.as_view()

    def test_effective_verification_stays_in_phase_eight(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8V1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Correct guardrail gap",
            description="Ship a corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-8/verify/",
            {
                "recommendation_id": recommendation.pk,
                "is_effective": True,
                "residual_risk": "LOW",
                "notes": "Closed-loop verification completed.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", user_id="dpa-1", process_ids=["SAF_P_004"]),
        )

        response = self.verify_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 8)
        self.assertEqual(response.data["verification"]["is_effective"], True)
        self.assertEqual(response.data["verification"]["recommendation_id"], recommendation.pk)

    def test_green_band_role_based_pic_can_verify(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8V2",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.GREEN,
            pic_user_id="OFFICE_PIC",
            created_by="pic-1",
            updated_by="pic-1",
            schema_version=1,
        )
        recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Confirm green-band closeout",
            description="Ship a corrective action.",
            created_by="pic-1",
            updated_by="pic-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-8/verify/",
            {
                "recommendation_id": recommendation.pk,
                "is_effective": True,
                "residual_risk": "LOW",
                "notes": "Role-based PIC reviewer verified effectiveness.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="OFFICE_SUPT", user_id="supt-1", process_ids=["SAF_P_004"]),
        )

        response = self.verify_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 8)
        self.assertEqual(response.data["verification"]["is_effective"], True)
