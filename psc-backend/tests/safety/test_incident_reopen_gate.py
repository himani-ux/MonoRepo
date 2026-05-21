from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.views.incident_reopen import IncidentReopenView


def build_user(*, role_name: str, user_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_008"],
        vessel_ids=["7"],
        is_global=False,
    )


class IncidentReopenGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentReopenView.as_view()

    def _closed_incident(self, *, risk_band: str) -> Incident:
        return Incident.objects.create(
            incident_number="ABC/2026/012",
            vessel_id="7",
            state="CLOSED",
            current_phase=9,
            risk_band=risk_band,
            pic_user_id="pic-7",
            closed_at=timezone.now() - timedelta(days=2),
            closure_reason="Effectiveness confirmed.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

    def test_green_reopen_requires_dpa(self) -> None:
        incident = self._closed_incident(risk_band=Incident.RiskBand.GREEN)
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/reopen/",
            {"reason": "Fresh witness statement changes the analysis."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 5)
        self.assertEqual(incident.state, "REOPENED")
        self.assertIsNone(incident.closed_at)
        latest_log = IncidentPhaseLog.objects.order_by("-id").first()
        self.assertIsNotNone(latest_log)
        self.assertEqual(latest_log.transition_type, IncidentPhaseLog.TransitionType.REOPEN)
        self.assertEqual(latest_log.phase_from, 9)
        self.assertEqual(latest_log.phase_to, 5)
        self.assertEqual(latest_log.loop_back_reason, "Fresh witness statement changes the analysis.")

    def test_yellow_reopen_rejects_non_dpa_actor(self) -> None:
        incident = self._closed_incident(risk_band=Incident.RiskBand.YELLOW)
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/reopen/",
            {"reason": "Additional bridge audio surfaced."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="FM", user_id="fm-1"))

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 403)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 9)
        self.assertEqual(incident.state, "CLOSED")

    def test_red_reopen_requires_fm(self) -> None:
        incident = self._closed_incident(risk_band=Incident.RiskBand.RED)
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/reopen/",
            {"reason": "Class feedback requires a deeper systems review."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="FLEET MANAGER", user_id="fm-1"))

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 5)
        self.assertEqual(incident.state, "REOPENED")
