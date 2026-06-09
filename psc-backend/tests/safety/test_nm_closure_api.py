from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.views.near_miss_closure import NearMissClosureView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_id: str = "user-1",
    work_side: str | None = None,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        work_side=work_side,
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_004"] if process_ids is None else process_ids,
        vessel_ids=["7"] if vessel_ids is None else vessel_ids,
        fleet_vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class NearMissClosureApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.view = NearMissClosureView.as_view()

    def _post_close(self, incident_id: int, payload: dict[str, object], *, user) -> object:
        request = self.factory.post(
            f"/api/safety/near-miss/{incident_id}/closure/",
            payload,
            format="json",
        )
        force_authenticate(request, user=user)
        return self.view(request, id=incident_id)

    def test_low_priority_triaged_near_miss_can_close_and_returns_read_only_summary(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="NM/2026/051",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            near_miss_priority="LOW",
            narrative="A loose ladder grating clip was spotted during rounds and secured before the watch changed over.",
            reporter_id="crew-7",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-7",
            updated_by="crew-7",
            schema_version=1,
        )

        response = self._post_close(
            near_miss.pk,
            {
                "closure_reason": "Master and DPA correspondence confirmed the local control and no wider escalation was required.",
                "typed_name": "Master Seven",
                "device_fingerprint": "tablet-close-1",
            },
            user=build_user(role_name="MASTER", user_id="master-7"),
        )

        self.assertEqual(response.status_code, 200)
        near_miss.refresh_from_db()
        self.assertEqual(near_miss.state, "CLOSED")
        self.assertIsNotNone(near_miss.closed_at)
        self.assertIn("correspondence", near_miss.closure_reason.lower())

        phase_log = IncidentPhaseLog.objects.get(incident_id=near_miss.pk)
        self.assertEqual(phase_log.transition_type, IncidentPhaseLog.TransitionType.CLOSE)

        history_fields = set(
            SafetyFieldHistory.objects.filter(parent_id=near_miss.pk).values_list("field_name", flat=True)
        )
        self.assertIn("closure_reason", history_fields)
        self.assertIn("near_miss_closure_signature", history_fields)

        get_request = self.factory.get(f"/api/safety/near-miss/{near_miss.pk}/closure/")
        force_authenticate(get_request, user=build_user(role_name="MASTER", user_id="master-7"))
        get_response = self.view(get_request, id=near_miss.pk)

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["near_miss"]["state"], "CLOSED")
        self.assertEqual(get_response.data["audit_summary"]["phase_log_count"], 1)
        self.assertGreaterEqual(get_response.data["audit_summary"]["field_history_count"], 4)

    def test_pic_can_close_low_priority_triaged_near_miss_with_green_close_authority(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="NM/2026/054",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            near_miss_priority="LOW",
            narrative="A pilot ladder setup deviation was corrected before use and recorded as a local near miss.",
            reporter_id="crew-9",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-9",
            updated_by="crew-9",
            schema_version=1,
        )

        response = self._post_close(
            near_miss.pk,
            {
                "closure_reason": "PIC reviewed the LOW-priority near miss and accepted the local control.",
                "typed_name": "PIC Reviewer",
                "device_fingerprint": "office-pic-close-1",
            },
            user=build_user(
                role_name="OFFICE_PIC",
                user_id="pic-1",
                process_ids=["SAF_P_006"],
            ),
        )

        self.assertEqual(response.status_code, 200)
        near_miss.refresh_from_db()
        self.assertEqual(near_miss.state, "CLOSED")

    def test_pic_cannot_close_high_priority_near_miss_with_green_close_authority(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="NM/2026/055",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            near_miss_priority="HIGH",
            narrative="A HIGH-priority near miss needs DPA or FM acceptance after fleet alert controls are completed.",
            reporter_id="crew-10",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-10",
            updated_by="crew-10",
            schema_version=1,
        )

        response = self._post_close(
            near_miss.pk,
            {
                "closure_reason": "PIC trying to close a HIGH-priority near miss.",
                "typed_name": "PIC Reviewer",
                "device_fingerprint": "office-pic-close-2",
            },
            user=build_user(
                role_name="OFFICE_PIC",
                user_id="pic-1",
                process_ids=["SAF_P_006"],
            ),
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("HIGH-priority near-miss closure is restricted to DPA or FM", str(response.data))

    def test_high_priority_close_does_not_require_fleet_alert_before_closure(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="NM/2026/052",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            near_miss_priority="HIGH",
            narrative="A heavy-weather mooring near miss indicates a sister-vessel control gap that needs fleet learning before the next similar operation.",
            reporter_id="crew-8",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-8",
            updated_by="crew-8",
            schema_version=1,
        )

        response = self._post_close(
            near_miss.pk,
            {
                "closure_reason": "Closing the high-priority near miss before issuing the fleet alert.",
                "typed_name": "DPA Reviewer",
                "device_fingerprint": "office-close-1",
            },
            user=build_user(role_name="DPA", user_id="dpa-1", vessel_ids=[]),
        )

        self.assertEqual(response.status_code, 200)
        near_miss.refresh_from_db()
        self.assertEqual(near_miss.state, "CLOSED")
        self.assertFalse((near_miss.near_miss_suggestion or "").strip())
        self.assertFalse(SafetyFieldHistory.objects.filter(
            parent_id=near_miss.pk,
            field_name="near_miss_preventive_measures",
        ).exists())

    def test_self_report_conflict_requires_acknowledgement_for_closing_actor(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="NM/2026/053",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            near_miss_priority="LOW",
            narrative="Master self-reported a bridge equipment exposure before the watch handover completed.",
            reporter_id="master-7",
            reporter_name="Master Seven",
            reporter_rank="MASTER",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        response = self._post_close(
            near_miss.pk,
            {
                "closure_reason": "Master and DPA correspondence confirmed the immediate control was effective.",
                "typed_name": "Master Seven",
                "device_fingerprint": "tablet-close-2",
            },
            user=build_user(role_name="MASTER", user_id="master-7"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["conflict_acknowledged"][0],
            "Acknowledge the self-report conflict before closing the near miss.",
        )
        self.assertEqual(
            response.data["conflict_approver_role"][0],
            "Conflict detected - assign MASTER as the different approver.",
        )

        response = self._post_close(
            near_miss.pk,
            {
                "closure_reason": "Master and DPA correspondence confirmed the immediate control was effective.",
                "typed_name": "Master Seven",
                "device_fingerprint": "tablet-close-2",
                "conflict_acknowledged": True,
                "conflict_approver_role": "MASTER",
            },
            user=build_user(role_name="MASTER", user_id="master-7"),
        )

        self.assertEqual(response.status_code, 200)
