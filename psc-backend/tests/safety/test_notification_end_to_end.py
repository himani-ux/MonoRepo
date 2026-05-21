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

from apps.safety.models import Incident
from apps.safety.views.incident_phase2 import IncidentPhase2SubmitView


def build_user(*, role_name: str = "MASTER", user_id: str = "master-7"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class NotificationEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.view = IncidentPhase2SubmitView.as_view()

    def test_red_phase_two_submit_queues_each_notification_as_independent_row(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/NOTIFY1",
            vessel_id="7",
            state="SUBMITTED",
            current_phase=2,
            risk_band=Incident.RiskBand.RED,
            imo_classifier=Incident.ImoClassifier.MI,
            narrative="Notification path test with a RED-band incident.",
            first_hour_checklist_done=True,
            reporter_id="master-7",
            reporter_name="Master Seven",
            reporter_rank="MASTER",
            reporter_device_fingerprint="device-123",
            latitude="12.345678",
            longitude="103.456789",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-2/submit/",
            {},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["notifications_emitted"], 5)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipient_ref, notification_kind
                FROM master_notification
                WHERE record_id = %s
                ORDER BY id
                """,
                [incident.pk],
            )
            rows = cursor.fetchall()

        self.assertEqual(
            rows,
            [
                ("OFFICE_PIC", "INCIDENT_PHASE_2_SUBMITTED"),
                ("DPA", "INCIDENT_PHASE_2_SUBMITTED"),
                ("SAFETY_CHANNEL", "INCIDENT_PHASE_2_SUBMITTED"),
                ("FM", "INCIDENT_PHASE_2_SUBMITTED"),
                ("MANAGING_DIRECTOR", "INCIDENT_PHASE_2_SUBMITTED"),
            ],
        )
