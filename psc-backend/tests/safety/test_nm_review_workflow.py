from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.views.near_miss_review import NearMissReviewView, NearMissReworkSubmitView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "user-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=process_ids if process_ids is not None else ["SAF_P_006"],
        vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class NearMissReviewWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.review_view = NearMissReviewView.as_view()
        self.rework_view = NearMissReworkSubmitView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T099",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state=Incident.State.PENDING_VESSEL_REVIEW,
            current_phase=1,
            occurred_at=timezone.now(),
            reported_at=timezone.now(),
            narrative=(
                "Crew observed a loose access platform pin and reported the unsafe condition "
                "before the next watch used the platform."
            ),
            reporter_id="crew-7",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-7",
            updated_by="crew-7",
            schema_version=1,
        )

    def test_master_can_submit_near_miss_to_dpa_triage(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Reviewed onboard and ready for DPA triage.",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.review_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.READY_FOR_DPA_TRIAGE)
        phase_log = IncidentPhaseLog.objects.get(incident_id=self.near_miss.pk)
        self.assertEqual(phase_log.device_fingerprint, "bridge-review-7")
        self.assertTrue(phase_log.signature_valid)
        self.assertIn(
            "state",
            set(SafetyFieldHistory.objects.filter(parent_id=self.near_miss.pk).values_list("field_name", flat=True)),
        )
        signature_row = SafetyFieldHistory.objects.get(
            parent_id=self.near_miss.pk,
            field_name="near_miss_vessel_review_signature",
        )
        self.assertEqual(signature_row.new_value["typed_name"], "Master Seven")
        self.assertEqual(signature_row.new_value["device_fingerprint"], "bridge-review-7")
        self.assertEqual(response.data["review_signature"]["typed_name"], "Master Seven")
        self.assertTrue(response.data["review_phase_log"]["signature_valid"])

    def test_master_can_send_back_and_reporter_can_resubmit_rework(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SEND_BACK",
                "comment": "Add the immediate action taken before office triage.",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.review_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.REWORK_REQUIRED)

        rework_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/rework/",
            {"comment": "Immediate action was added to the near-miss narrative."},
            format="json",
        )
        force_authenticate(
            rework_request,
            user=build_user(role_name="AB", process_ids=["SAF_P_001"], user_id="crew-7"),
        )

        rework_response = self.rework_view(rework_request, id=self.near_miss.pk)

        self.assertEqual(rework_response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.PENDING_VESSEL_REVIEW)

    def test_send_back_requires_comment(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SEND_BACK",
                "comment": "",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.review_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("comment", response.data)

    def test_vessel_review_requires_typed_signature(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Reviewed onboard and ready for DPA triage.",
                "typed_name": "",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.review_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("typed_name", response.data)

    def test_vessel_review_requires_device_fingerprint(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Reviewed onboard and ready for DPA triage.",
                "typed_name": "Master Seven",
                "device_fingerprint": "",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.review_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("device_fingerprint", response.data)
