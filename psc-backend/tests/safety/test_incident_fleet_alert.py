from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from django.db import connection
from django.test import override_settings

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

    @patch("apps.safety.services.incident_fleet_alert.IncidentFleetAlertService._build_pdf_attachment")
    @patch("apps.safety.services.incident_fleet_alert.EmailMultiAlternatives")
    def test_issue_sends_in_app_and_email_only_to_selected_ships(self, email_class, pdf_attachment) -> None:
        pdf_attachment.return_value = SimpleNamespace(
            file_name="ARY-2026-099.pdf",
            content=b"%PDF-incident",
            content_type="application/pdf",
        )
        email_message = email_class.return_value
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_A, VESSEL_C]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        with override_settings(
            DEFAULT_FROM_EMAIL="KSM Marine <pms@cymsol.co.in>",
            EMAIL_HOST_USER="pms@cymsol.co.in",
            EMAIL_HOST_PASSWORD="smtp-password",
        ):
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

        email_class.assert_called_once()
        self.assertEqual(email_class.call_args.kwargs["to"], [])
        self.assertEqual(
            set(email_class.call_args.kwargs["bcc"]),
            {"alpha@example.com", "charlie@example.com"},
        )
        self.assertEqual(email_class.call_args.kwargs["from_email"], "KSM Marine <pms@cymsol.co.in>")
        self.assertEqual(tuple(email_class.call_args.kwargs["cc"]), ("HSSEQ@kaizenship.net",))
        self.assertIn("Please review what happened in the attached PDF", email_class.call_args.kwargs["body"])
        self.assertNotIn("Cargo hose failed", email_class.call_args.kwargs["body"])
        email_message.attach.assert_called_once_with(
            "ARY-2026-099.pdf",
            b"%PDF-incident",
            "application/pdf",
        )
        self.assertEqual(email_message.send.call_count, 1)

    def test_workspace_lists_active_vessels_for_office_selection(self) -> None:
        request = self.factory.get(f"/api/safety/incidents/{self.incident.pk}/fleet-alert/")
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"]))

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
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

    def test_workspace_allows_backend_phase_six_office_review(self) -> None:
        self.incident.current_phase = 6
        self.incident.save(update_fields=["current_phase"])
        request = self.factory.get(f"/api/safety/incidents/{self.incident.pk}/fleet-alert/")
        force_authenticate(request, user=build_user(role_name="PIC", process_ids=["SAF_P_006"]))

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["vessel_id"] for row in response.data["recipient_vessels"]],
            [VESSEL_A, VESSEL_B, VESSEL_C],
        )

    @patch("apps.safety.services.incident_fleet_alert.IncidentFleetAlertService._build_pdf_attachment")
    @patch("apps.safety.services.incident_fleet_alert.EmailMultiAlternatives")
    def test_issue_allows_backend_phase_six_office_review(self, email_class, pdf_attachment) -> None:
        pdf_attachment.return_value = SimpleNamespace(
            file_name="phase-six-incident.pdf",
            content=b"%PDF",
            content_type="application/pdf",
        )
        self.incident.current_phase = 6
        self.incident.save(update_fields=["current_phase"])
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_B]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["issued"])
        self.assertEqual(response.data["recipient_vessel_ids"], [VESSEL_B])
        self.assertEqual(response.data["notifications_emitted"], 1)
        self.assertEqual(response.data["emails_sent"], 1)
        email_class.return_value.attach.assert_called_once_with(
            "phase-six-incident.pdf",
            b"%PDF",
            "application/pdf",
        )
        self.assertEqual(email_class.return_value.send.call_count, 1)

    @patch("apps.safety.services.incident_fleet_alert.IncidentFleetAlertService._build_pdf_attachment")
    @patch("apps.safety.services.incident_fleet_alert.EmailMultiAlternatives")
    def test_issue_allows_closed_office_review_incident(self, email_class, pdf_attachment) -> None:
        pdf_attachment.return_value = SimpleNamespace(
            file_name="closed-incident.pdf",
            content=b"%PDF",
            content_type="application/pdf",
        )
        self.incident.current_phase = 9
        self.incident.state = Incident.State.CLOSED
        self.incident.save(update_fields=["current_phase", "state"])
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_B]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["issued"])
        self.assertEqual(response.data["recipient_vessel_ids"], [VESSEL_B])
        self.assertEqual(response.data["notifications_emitted"], 1)
        self.assertEqual(response.data["emails_sent"], 1)
        email_class.return_value.attach.assert_called_once_with(
            "closed-incident.pdf",
            b"%PDF",
            "application/pdf",
        )
        self.assertEqual(email_class.return_value.send.call_count, 1)

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

    @patch("apps.safety.services.incident_fleet_alert.EmailMultiAlternatives")
    def test_issue_requires_configured_sender_password_before_notification(self, email_class) -> None:
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_A]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        with (
            override_settings(EMAIL_HOST_PASSWORD=""),
            patch("apps.safety.services.incident_fleet_alert.load_dotenv"),
            patch.dict("os.environ", {"EMAIL_HOST_PASSWORD": ""}),
        ):
            response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("EMAIL_HOST_PASSWORD", str(response.data))
        self.assertEqual(Notification.objects.count(), 0)
        email_class.assert_not_called()

    @patch("apps.safety.services.incident_fleet_alert.IncidentFleetAlertService._build_pdf_attachment")
    @patch("apps.safety.services.incident_fleet_alert.EmailMultiAlternatives")
    def test_issue_loads_sender_password_from_environment_without_restart(self, email_class, pdf_attachment) -> None:
        pdf_attachment.return_value = SimpleNamespace(
            file_name="incident.pdf",
            content=b"%PDF",
            content_type="application/pdf",
        )
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_A]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        with (
            override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD=""),
            patch("apps.safety.services.incident_fleet_alert.load_dotenv"),
            patch.dict("os.environ", {"EMAIL_HOST_PASSWORD": "smtp-password"}),
        ):
            response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["emails_sent"], 1)
        email_class.return_value.attach.assert_called_once_with(
            "incident.pdf",
            b"%PDF",
            "application/pdf",
        )
        self.assertEqual(email_class.return_value.send.call_count, 1)

    @patch("apps.safety.services.incident_fleet_alert.EmailMultiAlternatives")
    def test_issue_requires_selected_ship_email_before_notification(self, email_class) -> None:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE VesselData SET email = NULL WHERE id = %s", [VESSEL_A])
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_A]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Email is not recorded in VesselData", str(response.data))
        self.assertEqual(Notification.objects.count(), 0)
        email_class.assert_not_called()

    def test_issue_blocks_before_office_review(self) -> None:
        self.incident.current_phase = 5
        self.incident.save(update_fields=["current_phase"])
        request = self.factory.post(
            f"/api/safety/incidents/{self.incident.pk}/fleet-alert/",
            {"recipient_vessel_ids": [VESSEL_B]},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data[0]), "Incident Fleet Alert is available from Office Review.")


if __name__ == "__main__":
    unittest.main()
