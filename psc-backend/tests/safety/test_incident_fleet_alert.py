from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch
import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.notifications.models import Notification
from apps.safety.models import Incident
from apps.safety.views.incident_fleet_alert import IncidentFleetAlertIssueView


VESSEL_A = "11111111-1111-1111-1111-111111111111"
VESSEL_B = "22222222-2222-2222-2222-222222222222"
VESSEL_C = "33333333-3333-3333-3333-333333333333"


def build_user(*, role_name: str = "DPA", process_ids: list[str] | None = None):
    return SimpleNamespace(
        id="dpa-1",
        username="dpa-1",
        role=role_name,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_004"],
        is_global=True,
        user_type="OFFICE",
        work_side="OFFICE",
    )


def recreate_psc_notification_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS psc_notification")
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Notification)


def recreate_vessel_data_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS VesselData")
        cursor.execute(
            """
            CREATE TABLE VesselData (
                id VARCHAR(36) PRIMARY KEY,
                vesselName VARCHAR(128) NULL,
                vesselCode VARCHAR(16) NULL,
                email VARCHAR(128) NULL,
                is_active BOOLEAN NULL DEFAULT 1,
                is_deleted BOOLEAN NULL DEFAULT 0
            )
            """
        )
        cursor.executemany(
            """
            INSERT INTO VesselData (id, vesselName, vesselCode, email, is_active, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                (VESSEL_A, "Vessel Alpha", "ALP", "alpha@example.com", 1, 0),
                (VESSEL_B, "Vessel Bravo", "BRV", "bravo@example.com", 1, 0),
                (VESSEL_C, "Vessel Charlie", "CHR", "charlie@example.com", 1, 0),
            ],
        )


class IncidentFleetAlertTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_psc_notification_table()
        recreate_vessel_data_table()
        self.factory = APIRequestFactory()
        self.view = IncidentFleetAlertIssueView.as_view()
        self.incident = Incident.objects.create(
            incident_number="ARY/2026/099",
            vessel_id=VESSEL_A,
            record_type=Incident.RecordType.INCIDENT,
            state=Incident.State.UNDER_REVIEW,
            current_phase=7,
            risk_band=Incident.RiskBand.RED,
            narrative="Cargo hose failed during transfer and the job was stopped for investigation.",
            created_by="reporter-1",
            reporter_id="crew-1",
            reporter_name="Crew Reporter",
            reporter_rank="MASTER",
            reporter_device_fingerprint="reporter-device",
            schema_version=Incident.ENUM_TIGHTENED_SCHEMA_VERSION,
        )

    @patch("apps.safety.services.incident_fleet_alert.EmailMultiAlternatives")
    def test_issue_sends_in_app_and_email_only_to_selected_ships(self, email_class) -> None:
        email_message = email_class.return_value
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_A, VESSEL_C]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["issued"])
        self.assertEqual(response.data["recipient_vessel_ids"], [VESSEL_A, VESSEL_C])
        self.assertEqual(response.data["notifications_emitted"], 2)
        self.assertEqual(response.data["emails_sent"], 2)
        self.assertEqual(response.data["vessels_without_email"], 0)
        self.assertEqual(response.data["email_failed"], 0)

        notification_vessels = {
            str(vessel_id) for vessel_id in Notification.objects.values_list("vessel_id", flat=True)
        }
        self.assertEqual(notification_vessels, {VESSEL_A, VESSEL_C})
        self.assertEqual(
            set(Notification.objects.values_list("notification_type", flat=True)),
            {"INCIDENT_FLEET_ALERT"},
        )

        sent_addresses = {
            call.kwargs["to"][0]
            for call in email_class.call_args_list
        }
        self.assertEqual(sent_addresses, {"alpha@example.com", "charlie@example.com"})
        self.assertEqual(email_message.send.call_count, 2)

    def test_workspace_lists_active_vessels_for_office_selection(self) -> None:
        request = self.factory.get(f"/api/safety/incidents/{self.incident.pk}/fleet-alert/")
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"]))

        response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["vessel_id"] for row in response.data["recipient_vessels"]],
            [VESSEL_A, VESSEL_B, VESSEL_C],
        )
        self.assertEqual(
            [row["display_name"] for row in response.data["recipient_vessels"]],
            ["ALP - Vessel Alpha", "BRV - Vessel Bravo", "CHR - Vessel Charlie"],
        )

    def test_issue_requires_at_least_one_ship(self) -> None:
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": []},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("recipient_vessel_ids", response.data)


if __name__ == "__main__":
    unittest.main()
