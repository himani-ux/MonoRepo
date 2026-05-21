from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.views.near_miss import NearMissDetailView, NearMissListCreateView
from apps.safety.views.near_miss_closure import (
    NearMissAuditView,
    build_near_miss_pdf_payload,
    build_near_miss_search_payload,
)


def build_user(*, role_name: str, user_id: str = "viewer-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class NearMissAnonymityAllExitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.list_view = NearMissListCreateView.as_view()
        self.detail_view = NearMissDetailView.as_view()
        self.audit_view = NearMissAuditView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/061",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="CLOSED",
            current_phase=1,
            near_miss_priority="LOW",
            occurred_at=timezone.now() - timedelta(hours=2),
            reported_at=timezone.now() - timedelta(hours=1),
            narrative="A loose hatch-dog handle was identified and secured before cargo-watch turnover, preventing the exposure from escalating.",
            reporter_id="crew-61",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            reporter_email="crew61@example.test",
            reporter_department="Deck",
            reporter_device_fingerprint="device-61",
            created_by="crew-61",
            updated_by="dpa-1",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=self.near_miss,
            phase_from=1,
            phase_to=1,
            transition_type=IncidentPhaseLog.TransitionType.CLOSE,
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table="vims_safety_incident",
            parent_id=self.near_miss.pk,
            field_name="reporter_name",
            old_value=None,
            new_value="Crew Reporter",
            actor_user_id="crew-61",
            actor_role_code="AB",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table="vims_safety_incident",
            parent_id=self.near_miss.pk,
            field_name="closure_reason",
            old_value=None,
            new_value="Master and DPA correspondence confirmed the local control.",
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )

    def test_master_view_masks_reporter_across_list_detail_pdf_search_and_audit(self) -> None:
        user = build_user(role_name="MASTER", user_id="master-7")

        list_request = self.factory.get("/api/safety/near-miss/")
        force_authenticate(list_request, user=user)
        list_response = self.list_view(list_request)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data[0]["reporter_name"], "Anonymous Reporter")

        detail_request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/")
        force_authenticate(detail_request, user=user)
        detail_response = self.detail_view(detail_request, id=self.near_miss.pk)

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["reporter_name"], "Anonymous Reporter")
        self.assertIsNone(detail_response.data["reporter_user_id"])

        pdf_payload = build_near_miss_pdf_payload(self.near_miss, user=user)
        self.assertEqual(pdf_payload["reporter_name"], "Anonymous Reporter")
        self.assertIsNone(pdf_payload["reporter_user_id"])

        search_payload = build_near_miss_search_payload(self.near_miss, user=user)
        self.assertEqual(search_payload["reporter_name"], "Anonymous Reporter")

        audit_request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/audit/")
        force_authenticate(audit_request, user=user)
        audit_response = self.audit_view(audit_request, id=self.near_miss.pk)

        self.assertEqual(audit_response.status_code, 200)
        self.assertEqual(len(audit_response.data["phase_log"]), 1)
        self.assertEqual(
            [row["field_name"] for row in audit_response.data["field_history"]],
            ["closure_reason"],
        )

    def test_dpa_view_retains_reporter_identity_across_all_exits(self) -> None:
        user = build_user(role_name="DPA", user_id="dpa-1")

        pdf_payload = build_near_miss_pdf_payload(self.near_miss, user=user)
        search_payload = build_near_miss_search_payload(self.near_miss, user=user)

        self.assertEqual(pdf_payload["reporter_name"], "Crew Reporter")
        self.assertEqual(pdf_payload["reporter_user_id"], "crew-61")
        self.assertEqual(search_payload["reporter_name"], "Crew Reporter")

        audit_request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/audit/")
        force_authenticate(audit_request, user=user)
        audit_response = self.audit_view(audit_request, id=self.near_miss.pk)

        self.assertEqual(audit_response.status_code, 200)
        self.assertEqual(
            [row["field_name"] for row in audit_response.data["field_history"]],
            ["reporter_name", "closure_reason"],
        )
