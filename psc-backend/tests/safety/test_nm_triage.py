from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.views.near_miss_triage import NearMissTriageView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "dpa-1",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_002"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class NearMissTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = NearMissTriageView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T014",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state=Incident.State.READY_FOR_OFFICE_COMMENTS,
            current_phase=1,
            occurred_at=timezone.now(),
            reported_at=timezone.now(),
            narrative=(
                "Crew observed an unsecured staging pin during routine deck movement and "
                "reported the unsafe condition before anyone stepped onto the ladder."
            ),
            near_miss_priority="LOW",
            near_miss_shell_tag="Hardware",
            reporter_id="crew-7",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-7",
            updated_by="crew-7",
            schema_version=1,
        )

    def test_pic_can_accept_low_priority_office_comments_and_audit_rows_are_written(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "LOW", "office_comment": "PIC reviewed and accepts the report."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"], user_id="pic-1"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.near_miss_priority, "LOW")
        self.assertEqual(self.near_miss.state, "OFFICE_COMMENTS_COMPLETED")
        self.assertEqual(response.data["suggested_priority"], "LOW")
        self.assertEqual(response.data["office_comment"], "PIC reviewed and accepts the report.")

        phase_log = IncidentPhaseLog.objects.get(incident_id=self.near_miss.pk)
        self.assertEqual(phase_log.phase_from, 1)
        self.assertEqual(phase_log.phase_to, 1)
        self.assertEqual(phase_log.transition_type, IncidentPhaseLog.TransitionType.FORWARD)
        self.assertEqual(phase_log.actor_role_code, "PIC")

        history_fields = list(
            SafetyFieldHistory.objects.filter(parent_id=self.near_miss.pk).values_list("field_name", flat=True)
        )
        self.assertIn("state", history_fields)

    def test_non_office_reviewer_is_rejected_even_with_process_permission(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "LOW"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 403)

    def test_office_comments_wait_for_vessel_side_review(self) -> None:
        self.near_miss.state = Incident.State.PENDING_VESSEL_REVIEW
        self.near_miss.save(update_fields=("state",))
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "LOW"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"], user_id="pic-1"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("vessel-side", str(response.data).lower())

    def test_office_send_back_returns_vessel_rework_summary(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {
                "action": "SEND_BACK",
                "office_comment": (
                    "Office comment: Please add what was corrected onboard.\n"
                    "Suggested priority: LOW -> MEDIUM\n"
                    "Reason for priority change: More checks are needed."
                ),
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"], user_id="pic-1"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.REWORK_REQUIRED)
        self.assertIn("Please add what was corrected onboard", response.data["rework_summary"]["comment"])
        self.assertIn("Suggested priority: LOW -> MEDIUM", response.data["rework_summary"]["comment"])

    def test_office_reject_sets_rejected_state_and_keeps_reason_for_rework(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {
                "action": "REJECT",
                "office_comment": "Rejected because the report needs Master clarification before office acceptance.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"], user_id="pic-1"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, Incident.State.REJECTED)
        self.assertEqual(response.data["state"], Incident.State.REJECTED)
        self.assertIn("Master clarification", response.data["rework_summary"]["comment"])
        self.assertIn("office_rejected_phase_log", response.data)

    def test_office_reject_requires_reason(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"action": "REJECT"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"], user_id="pic-1"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("office_comment", response.data)

    def test_override_without_reason_is_rejected(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "HIGH"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"]))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("priority_change_reason", response.data)

    def test_category_tag_change_without_reason_is_rejected(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "LOW", "near_miss_shell_tag": "PPE"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"]))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("category_tag_change_reason", response.data)

    def test_category_tag_change_with_reason_is_saved(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {
                "near_miss_priority": "LOW",
                "near_miss_shell_tag": "PPE",
                "category_tag_change_reason": "Category corrected after office review.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"]))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.near_miss_shell_tag, "PPE")

    def test_repeated_near_miss_must_be_triaged_high(self) -> None:
        self.near_miss.incident_type_id = 1
        self.near_miss.loss_type_primary_id = 1
        self.near_miss.near_miss_shell_tag = "Hardware"
        self.near_miss.save(update_fields=("incident_type_id", "loss_type_primary_id", "near_miss_shell_tag"))
        Incident.objects.create(
            incident_number="NM/2026/013",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state=Incident.State.CLOSED,
            current_phase=1,
            occurred_at=self.near_miss.occurred_at - timedelta(minutes=1),
            reported_at=self.near_miss.reported_at - timedelta(minutes=1),
            narrative="Previous near miss with the same SHELL tag and event type.",
            incident_type_id=self.near_miss.incident_type_id,
            loss_type_primary_id=self.near_miss.loss_type_primary_id,
            near_miss_shell_tag=self.near_miss.near_miss_shell_tag,
            reporter_id="crew-old",
            created_by="crew-old",
            updated_by="crew-old",
            schema_version=1,
        )
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "LOW"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"]))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("must be reviewed as high priority", str(response.data))
        self.assertIn("similar near miss", str(response.data))
        self.assertNotIn("SSOT", str(response.data))
        self.assertNotIn("D-GAP-R22", str(response.data))

    def test_repeat_outside_90_days_does_not_force_high(self) -> None:
        self.near_miss.incident_type_id = 1
        self.near_miss.loss_type_primary_id = 1
        self.near_miss.near_miss_shell_tag = "Hardware"
        self.near_miss.save(update_fields=("incident_type_id", "loss_type_primary_id", "near_miss_shell_tag"))
        old_date = timezone.now() - timedelta(days=120)
        Incident.objects.create(
            incident_number="NM/2026/012",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state=Incident.State.CLOSED,
            current_phase=1,
            occurred_at=old_date,
            reported_at=old_date,
            narrative="Older near miss with the same root cause and event type.",
            incident_type_id=self.near_miss.incident_type_id,
            loss_type_primary_id=self.near_miss.loss_type_primary_id,
            near_miss_shell_tag=self.near_miss.near_miss_shell_tag,
            reporter_id="crew-old",
            created_by="crew-old",
            updated_by="crew-old",
            schema_version=1,
        )
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "LOW"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"], user_id="pic-1"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.near_miss_priority, "LOW")

    def test_auto_high_marker_must_be_high(self) -> None:
        self.near_miss.narrative = (
            "Crew stopped the task after noticing oil spill risk near the deck drain "
            "before pollution reached overboard discharge."
        )
        self.near_miss.save(update_fields=("narrative",))
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/office-comments/",
            {"near_miss_priority": "LOW"},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA"))

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("risk", str(response.data))
        self.assertIn("must be reviewed as high priority", str(response.data))
        self.assertNotIn("similar near miss exists", str(response.data))
        self.assertNotIn("SSOT", str(response.data))
        self.assertNotIn("D-GAP-R22", str(response.data))
