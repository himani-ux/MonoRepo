from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
    recreate_near_miss_reference_tables,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.views.near_miss import NearMissDetailView
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
        recreate_near_miss_reference_tables()
        self.factory = APIRequestFactory()
        self.detail_view = NearMissDetailView.as_view()
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
                "before the next watch used the platform. The area was isolated, the pin was tagged, "
                "and the duty team was informed so nobody used the access until it was checked."
            ),
            incident_type_id=1,
            loss_type_primary_id=1,
            near_miss_incident_type_ids="[1]",
            near_miss_severity="LOW",
            near_miss_place="AT_SEA",
            near_miss_shell_tag="Safety",
            near_miss_category_tags='["Safety"]',
            near_miss_immediate_action="Area isolated and watch team warned before anyone used the access.",
            near_miss_suggestion="Inspect platform pins during every pre-work safety round.",
            reporter_id="crew-7",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-7",
            updated_by="crew-7",
            schema_version=1,
        )

    def _rework_payload(self, **overrides):
        payload = {
            "comment": "Immediate action was added to the near-miss narrative.",
            "incident_type_id": 1,
            "loss_type_primary_id": 1,
            "narrative": (
                "Crew observed a loose access platform pin and reported the unsafe condition before "
                "the next watch used the platform. The rework adds the immediate isolation action, "
                "who was informed, and how the platform was kept out of service until inspection."
            ),
            "near_miss_immediate_action": "Access platform isolated and duty officer informed immediately.",
            "near_miss_place": "AT_SEA",
            "near_miss_category_tags": ["Safety"],
            "near_miss_incident_type_ids": [1],
            "near_miss_mscat_subcode_ids": ["10.01"],
            "near_miss_severity": "LOW",
            "near_miss_shell_tag": "Safety",
            "near_miss_suggestion": "Add platform pin check to pre-work safety rounds.",
            "near_miss_root_cause_detail": "",
            "near_miss_corrective_action": "",
            "near_miss_weather_voyage_details": "",
            "near_miss_equipment_details": "",
            "near_miss_lessons_learned": "",
            "occurred_at": self.near_miss.occurred_at.isoformat(),
            "reporter_device_fingerprint": "crew-device-7",
        }
        payload.update(overrides)
        return payload

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
        self.assertEqual(self.near_miss.state, Incident.State.READY_FOR_OFFICE_COMMENTS)
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

    def test_engine_near_miss_requires_ce_review_before_master_submission(self) -> None:
        self.near_miss.reporter_department = "Engine"
        self.near_miss.save(update_fields=("reporter_department",))

        master_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Master reviewed.",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(master_request, user=build_user(role_name="MASTER", user_id="master-7"))

        blocked_response = self.review_view(master_request, id=self.near_miss.pk)

        self.assertEqual(blocked_response.status_code, 400)
        self.assertIn("Chief Engineer review", str(blocked_response.data))

        ce_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Engine HOD reviewed.",
                "typed_name": "Chief Engineer",
                "device_fingerprint": "engine-review-7",
            },
            format="json",
        )
        force_authenticate(ce_request, user=build_user(role_name="CHIEF ENGINEER", user_id="ce-7"))

        ce_response = self.review_view(ce_request, id=self.near_miss.pk)

        self.assertEqual(ce_response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.PENDING_VESSEL_REVIEW)
        self.assertEqual(ce_response.data["next_required_review"], "MASTER")
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_id=self.near_miss.pk,
                field_name="near_miss_hod_review_signature",
            ).exists()
        )

        master_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Master reviewed after CE.",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(master_request, user=build_user(role_name="MASTER", user_id="master-7"))

        master_response = self.review_view(master_request, id=self.near_miss.pk)

        self.assertEqual(master_response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.READY_FOR_OFFICE_COMMENTS)

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
        self.assertEqual(
            response.data["rework_summary"]["comment"],
            "Add the immediate action taken before office triage.",
        )
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.REWORK_REQUIRED)

        detail_request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/")
        force_authenticate(
            detail_request,
            user=build_user(role_name="AB", process_ids=["SAF_P_001"], user_id="crew-7"),
        )

        detail_response = self.detail_view(detail_request, id=self.near_miss.pk)

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(
            detail_response.data["rework_summary"]["comment"],
            "Add the immediate action taken before office triage.",
        )

        rework_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/rework/",
            self._rework_payload(),
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
        self.assertEqual(self.near_miss.near_miss_immediate_action, "Access platform isolated and duty officer informed immediately.")
        self.assertEqual(self.near_miss.near_miss_mscat_subcode_id, "10.01")
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_id=self.near_miss.pk,
                field_name="near_miss_rework_resubmission",
            ).exists()
        )

    def test_engine_rework_requires_fresh_hod_review_after_resubmission(self) -> None:
        self.near_miss.reporter_department = "Engine"
        self.near_miss.save(update_fields=("reporter_department",))

        ce_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Engine HOD reviewed initial report.",
                "typed_name": "Chief Engineer",
                "device_fingerprint": "engine-review-7",
            },
            format="json",
        )
        force_authenticate(ce_request, user=build_user(role_name="CHIEF ENGINEER", user_id="ce-7"))
        self.assertEqual(self.review_view(ce_request, id=self.near_miss.pk).status_code, 200)

        send_back_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SEND_BACK",
                "comment": "Add the immediate isolation detail before office submission.",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(send_back_request, user=build_user(role_name="MASTER", user_id="master-7"))
        self.assertEqual(self.review_view(send_back_request, id=self.near_miss.pk).status_code, 200)

        rework_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/rework/",
            self._rework_payload(),
            format="json",
        )
        force_authenticate(
            rework_request,
            user=build_user(role_name="AB", process_ids=["SAF_P_001"], user_id="crew-7"),
        )
        self.assertEqual(self.rework_view(rework_request, id=self.near_miss.pk).status_code, 200)

        master_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/review/",
            {
                "decision": "SUBMIT_TO_OFFICE",
                "comment": "Master reviewed after rework.",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-review-7",
            },
            format="json",
        )
        force_authenticate(master_request, user=build_user(role_name="MASTER", user_id="master-7"))

        blocked_response = self.review_view(master_request, id=self.near_miss.pk)

        self.assertEqual(blocked_response.status_code, 400)
        self.assertIn("Chief Engineer review before Master submits", str(blocked_response.data))

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
