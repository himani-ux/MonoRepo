from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.db import connection

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.views.incident_phase2 import IncidentPhase2SubmitView, IncidentPhase2UpdateView


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
        process_ids=process_ids or ["SAF_P_002"],
        vessel_ids=vessel_ids or [7],
        is_global=False,
    )


class IncidentPhase2SubmitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.update_view = IncidentPhase2UpdateView.as_view()
        self.submit_view = IncidentPhase2SubmitView.as_view()

    def test_update_and_submit_promotes_draft_number_and_transitions_to_phase_three(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="SUBMITTED",
            current_phase=2,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            narrative="Narrative " + ("details " * 30),
            first_hour_checklist_done=True,
            reporter_id="master-7",
            reporter_name="Master Seven",
            reporter_rank="MASTER",
            reporter_device_fingerprint="device-123",
            latitude="12.345678",
            longitude="103.456789",
        )

        update_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-2/",
            {
                "risk_band": Incident.RiskBand.RED,
                "imo_classifier": Incident.ImoClassifier.MI,
            },
            format="json",
        )
        force_authenticate(update_request, user=build_user())

        update_response = self.update_view(update_request, id=incident.pk)

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data["risk_band"], Incident.RiskBand.RED)

        submit_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-2/submit/",
            {},
            format="json",
        )
        force_authenticate(submit_request, user=build_user())

        submit_response = self.submit_view(submit_request, id=incident.pk)

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data["current_phase"], 3)
        self.assertEqual(submit_response.data["state"], "IN_PROGRESS")
        self.assertEqual(submit_response.data["incident_number"], "ABC/2026/001")
        self.assertEqual(submit_response.data["pic_user_id"], "OFFICE_PIC")
        self.assertEqual(submit_response.data["transition"]["phase_from"], 2)
        self.assertEqual(submit_response.data["transition"]["phase_to"], 3)

        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 3)
        self.assertEqual(incident.state, "IN_PROGRESS")
        self.assertEqual(incident.incident_number, "ABC/2026/001")
        self.assertEqual(incident.pic_user_id, "OFFICE_PIC")
        self.assertTrue(incident.office_notified_at is not None)
        self.assertTrue(incident.dpa_notified_at is not None)
        self.assertTrue(incident.fm_notified_at is not None)
        self.assertEqual(incident.notification_channel_count, 5)
        self.assertEqual(IncidentPhaseLog.objects.count(), 1)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM master_notification")
            row_count = cursor.fetchone()[0]

        self.assertEqual(row_count, 5)

    def test_second_engineer_cannot_mutate_phase_two_even_with_saf_p_002(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T002",
            vessel_id="7",
            state="SUBMITTED",
            current_phase=2,
            created_by="2e-7",
            updated_by="2e-7",
            schema_version=1,
            narrative="Narrative " + ("details " * 30),
            first_hour_checklist_done=True,
            reporter_id="2e-7",
            reporter_name="Second Engineer Seven",
            reporter_rank="2/E",
            reporter_device_fingerprint="device-2e",
            latitude="12.345678",
            longitude="103.456789",
        )

        update_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-2/",
            {
                "risk_band": Incident.RiskBand.YELLOW,
                "imo_classifier": Incident.ImoClassifier.MC,
            },
            format="json",
        )
        force_authenticate(update_request, user=build_user(role_name="2/E", user_id="2e-7"))

        update_response = self.update_view(update_request, id=incident.pk)

        self.assertEqual(update_response.status_code, 403)

        submit_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-2/submit/",
            {},
            format="json",
        )
        force_authenticate(submit_request, user=build_user(role_name="2/E", user_id="2e-7"))

        submit_response = self.submit_view(submit_request, id=incident.pk)

        self.assertEqual(submit_response.status_code, 403)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 2)
        self.assertEqual(incident.state, "SUBMITTED")
