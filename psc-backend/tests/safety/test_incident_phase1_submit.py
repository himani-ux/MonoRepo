from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table
from tests.safety.support import recreate_master_notification_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.views.incident_phase1 import (
    IncidentPhase1CreateView,
    IncidentPhase1SubmitView,
    IncidentPhase1UpdateView,
)


def build_user(
    *,
    role_name: str = "MASTER",
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[int] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_001"],
        vessel_ids=vessel_ids or [7],
        is_global=False,
    )


class IncidentPhase1SubmitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.create_view = IncidentPhase1CreateView.as_view()
        self.update_view = IncidentPhase1UpdateView.as_view()
        self.submit_view = IncidentPhase1SubmitView.as_view()

    def test_create_patch_and_submit_transitions_to_phase_two(self) -> None:
        create_request = self.factory.post(
            "/api/safety/incidents/phase-1/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "occurred_at": "2026-04-20T10:00:00Z",
                "reported_at": "2026-04-20T10:30:00Z",
                "narrative": "Initial intake " + ("details " * 30),
                "first_hour_checklist_done": True,
                "reporter_user_id": "master-7",
                "reporter_name": "Master Seven",
                "reporter_rank": "MASTER",
                "reporter_device_fingerprint": "device-abc",
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())

        create_response = self.create_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        incident_id = create_response.data["id"]
        self.assertEqual(IncidentPhaseLog.objects.count(), 1)

        patch_request = self.factory.patch(
            f"/api/safety/incidents/{incident_id}/phase-1/",
            {"narrative": "Updated intake " + ("details " * 30)},
            format="json",
        )
        force_authenticate(patch_request, user=build_user())

        patch_response = self.update_view(patch_request, id=incident_id)

        self.assertEqual(patch_response.status_code, 200)
        self.assertIn("Updated intake", patch_response.data["narrative"])

        submit_request = self.factory.post(
            f"/api/safety/incidents/{incident_id}/phase-1/submit/",
            {},
            format="json",
        )
        force_authenticate(submit_request, user=build_user())

        submit_response = self.submit_view(submit_request, id=incident_id)

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data["current_phase"], 2)
        self.assertEqual(submit_response.data["state"], "SUBMITTED")
        self.assertEqual(submit_response.data["transition"]["phase_from"], 1)
        self.assertEqual(submit_response.data["transition"]["phase_to"], 2)
        self.assertTrue(submit_response.data["phase_2_handoff"]["can_edit_phase_2"])
        self.assertEqual(submit_response.data["phase_2_handoff"]["notifications_emitted"], 0)

        incident = Incident.objects.get(pk=incident_id)
        self.assertEqual(incident.current_phase, 2)
        self.assertEqual(incident.state, "SUBMITTED")
        self.assertEqual(IncidentPhaseLog.objects.count(), 2)

    def test_second_engineer_submit_routes_to_phase_two_handoff_and_notifies_authorized_roles(self) -> None:
        create_request = self.factory.post(
            "/api/safety/incidents/phase-1/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "occurred_at": "2026-04-20T10:00:00Z",
                "reported_at": "2026-04-20T10:30:00Z",
                "narrative": "Second engineer intake " + ("details " * 30),
                "first_hour_checklist_done": True,
                "reporter_user_id": "2e-7",
                "reporter_name": "Second Engineer Seven",
                "reporter_rank": "2/E",
                "reporter_device_fingerprint": "device-2e",
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user(role_name="2/E", user_id="2e-7"))

        create_response = self.create_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        incident_id = create_response.data["id"]

        submit_request = self.factory.post(
            f"/api/safety/incidents/{incident_id}/phase-1/submit/",
            {},
            format="json",
        )
        force_authenticate(submit_request, user=build_user(role_name="2/E", user_id="2e-7"))

        submit_response = self.submit_view(submit_request, id=incident_id)

        self.assertEqual(submit_response.status_code, 200)
        self.assertFalse(submit_response.data["phase_2_handoff"]["can_edit_phase_2"])
        self.assertEqual(submit_response.data["phase_2_handoff"]["notifications_emitted"], 5)
        self.assertEqual(
            submit_response.data["phase_2_handoff"]["authorized_roles"],
            ["MASTER", "CO", "CE", "DPA", "FM"],
        )

        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipient_ref, notification_kind
                FROM master_notification
                WHERE record_id = %s
                ORDER BY id
                """,
                [incident_id],
            )
            rows = cursor.fetchall()

        self.assertEqual(
            rows,
            [
                ("MASTER", "INCIDENT_PHASE_2_HANDOFF_REQUIRED"),
                ("CO", "INCIDENT_PHASE_2_HANDOFF_REQUIRED"),
                ("CE", "INCIDENT_PHASE_2_HANDOFF_REQUIRED"),
                ("DPA", "INCIDENT_PHASE_2_HANDOFF_REQUIRED"),
                ("FM", "INCIDENT_PHASE_2_HANDOFF_REQUIRED"),
            ],
        )
