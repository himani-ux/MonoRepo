from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, Recommendation
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


class Phase8LoopbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.verify_view = IncidentPhase8VerifyView.as_view()

    def test_ineffective_verification_loops_back_to_phase_six(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8L1",
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
                "is_effective": False,
                "residual_risk": "MEDIUM",
                "notes": "Control failed on vessel follow-up; new recommendation required.",
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
        self.assertEqual(incident.current_phase, 6)
        latest_log = IncidentPhaseLog.objects.order_by("-id").first()
        self.assertIsNotNone(latest_log)
        self.assertEqual(latest_log.transition_type, IncidentPhaseLog.TransitionType.REWORK)
        self.assertEqual(latest_log.phase_from, 8)
        self.assertEqual(latest_log.phase_to, 6)
