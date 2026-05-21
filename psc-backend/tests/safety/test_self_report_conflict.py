from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.services.self_report_guard import check_self_report_conflict
from apps.safety.views.incident_phase1 import IncidentPhase1SubmitView


def build_user(
    *,
    role_name: str = "MASTER",
    work_side: str | None = None,
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        work_side=work_side,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_001"],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class SelfReportConflictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.submit_view = IncidentPhase1SubmitView.as_view()

    def test_service_requires_master_approver_for_vessel_side_conflict(self) -> None:
        result = check_self_report_conflict(
            "master-7",
            {"pic_candidate_id": "master-7", "reporter_rank": "MASTER"},
            user=build_user(),
            reporter_rank="MASTER",
        )

        self.assertTrue(result.conflict_detected)
        self.assertEqual(result.required_approver_role, "MASTER")

    def test_service_requires_dpa_approver_for_office_side_conflict(self) -> None:
        result = check_self_report_conflict(
            "master-7",
            {"pic_candidate_id": "master-7", "reporter_rank": "MASTER"},
            user=build_user(role_name="DPA", work_side="OFFICE", user_id="dpa-1"),
            reporter_rank="MASTER",
        )

        self.assertTrue(result.conflict_detected)
        self.assertEqual(result.required_approver_role, "DPA")

    def test_submit_requires_acknowledgement_and_different_approver_role(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            schema_version=1,
            first_hour_checklist_done=True,
            narrative="Conflict scenario " + ("details " * 30),
            reporter_id="master-7",
            reporter_name="Master Seven",
            reporter_rank="MASTER",
            reporter_device_fingerprint="device-abc",
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-1/submit/",
            {"pic_candidate_id": "master-7"},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.submit_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["conflict_acknowledged"][0],
            "Acknowledge the self-report conflict before submitting Phase 1.",
        )
        self.assertEqual(
            response.data["conflict_approver_role"][0],
            "Conflict detected - assign MASTER as the different approver.",
        )

    def test_submit_allows_conflict_when_acknowledged_with_required_role(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            schema_version=1,
            first_hour_checklist_done=True,
            narrative="Conflict scenario " + ("details " * 30),
            reporter_id="master-7",
            reporter_name="Master Seven",
            reporter_rank="MASTER",
            reporter_device_fingerprint="device-abc",
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-1/submit/",
            {
                "pic_candidate_id": "master-7",
                "conflict_acknowledged": True,
                "conflict_approver_role": "MASTER",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.submit_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["self_report_conflict"]["conflict_detected"])
        self.assertEqual(response.data["self_report_conflict"]["required_approver_role"], "MASTER")
