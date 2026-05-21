from __future__ import annotations
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, Recommendation, SafetyFieldHistory
from apps.safety.services.field_history_recorder import parse_history_value
from apps.safety.views.incident_circular import IncidentCircularPublishView


def build_user(*, role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_024"],
        vessel_ids=["7"],
        is_global=False,
    )


class RecordingCircularClient:
    published_payloads: list[dict[str, object]] = []

    def publish_draft(self, *, payload: dict[str, object]):
        self.__class__.published_payloads.append(payload)
        return SimpleNamespace(
            status="PUBLISHED",
            circular_id="CIRC-2026-001",
            detail_url="/api/circular/1/",
            payload=payload,
        )


class StubIncidentCircularPublishView(IncidentCircularPublishView):
    class StubPublisher(IncidentCircularPublishView.circular_publisher_class):
        client_class = RecordingCircularClient

    circular_publisher_class = StubPublisher


class IncidentCircularPublishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        RecordingCircularClient.published_payloads = []
        self.factory = APIRequestFactory()
        self.view = StubIncidentCircularPublishView.as_view()

    def test_closed_incident_publishes_lessons_learned_to_circular_service_seam(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/CIR-1",
            vessel_id="7",
            state="CLOSED",
            current_phase=9,
            risk_band=Incident.RiskBand.YELLOW,
            closed_at=timezone.now(),
            closure_reason="Controls verified and vessel closed the follow-up actions.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Share lifting-plan cross-check",
            description="Fleet circular should remind vessels to cross-check lifting plans against deck obstructions.",
            rationale="This was the common lesson from the closed case.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(f"/api/safety/circular/from-incident/{incident.pk}/", {}, format="json")
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "PUBLISHED")
        self.assertEqual(response.data["circular_id"], "CIRC-2026-001")
        self.assertEqual(len(RecordingCircularClient.published_payloads), 1)
        published_payload = RecordingCircularClient.published_payloads[0]
        self.assertEqual(published_payload["source_record_id"], incident.pk)
        self.assertEqual(published_payload["source_reference"], incident.incident_number)
        self.assertEqual(published_payload["risk_band"], Incident.RiskBand.YELLOW)
        self.assertIn("Share lifting-plan cross-check", published_payload["summary"])
        self.assertIn("cross-check lifting plans", published_payload["body"])

        history_row = SafetyFieldHistory.objects.get(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name="incident_circular_publish",
        )
        history_payload = parse_history_value(history_row.new_value)
        self.assertEqual(history_payload["status"], "PUBLISHED")
        self.assertEqual(history_payload["circular_id"], "CIRC-2026-001")

    def test_open_incident_cannot_publish_to_circular(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/CIR-2",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Hold back until closure",
            description="Circular publish must wait until closure.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(f"/api/safety/circular/from-incident/{incident.pk}/", {}, format="json")
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("incident closure", str(response.data))
