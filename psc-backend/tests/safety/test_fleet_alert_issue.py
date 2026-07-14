from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from django.db import connection
from django.test import override_settings
from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.views.fleet_alert import FleetAlertIssueView
from apps.notifications.models import Notification


VESSEL_7 = "11111111-1111-1111-1111-111111111111"
VESSEL_8 = "22222222-2222-2222-2222-222222222222"
VESSEL_9 = "33333333-3333-3333-3333-333333333333"


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    fleet_vessel_ids: list[str] | None = None,
    user_id: str = "user-1",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=process_ids or ["SAF_P_024"],
        fleet_vessel_ids=fleet_vessel_ids or [VESSEL_7],
        vessel_ids=fleet_vessel_ids or [VESSEL_7],
        is_global=role_name in {"DPA", "FM"},
    )


def recreate_vessel_data_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS VesselData")
        cursor.execute(
            """
            CREATE TABLE VesselData (
                id VARCHAR(36) PRIMARY KEY,
                vesselName VARCHAR(128) NULL,
                vesselCode VARCHAR(16) NULL,
                Email VARCHAR(128) NULL,
                is_active BOOLEAN NULL DEFAULT 1,
                is_deleted BOOLEAN NULL DEFAULT 0
            )
            """
        )
        cursor.executemany(
            """
            INSERT INTO VesselData (id, vesselName, vesselCode, Email, is_active, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                (VESSEL_7, "Vessel Seven", "VS7", "seven@example.com", 1, 0),
                (VESSEL_8, "Vessel Eight", "VS8", "eight@example.com", 1, 0),
                (VESSEL_9, "Vessel Nine", "VS9", "nine@example.com", 1, 0),
            ],
        )


def recreate_psc_notification_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS psc_notification")
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Notification)


class FleetAlertIssueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        recreate_psc_notification_table()
        recreate_vessel_data_table()
        self.factory = APIRequestFactory()
        self.view = FleetAlertIssueView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/023",
            vessel_id=VESSEL_7,
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            near_miss_priority="HIGH",
            narrative="A suspended-work platform staging pin was found unsecured before anyone transferred load, so the team stopped work, isolated the ladder, and reported the exposure immediately for fleet learning.",
            created_by="reporter-1",
            reporter_id="crew-7",
            reporter_name="Crew Reporter",
            reporter_rank="ABLE SEAMAN",
            reporter_device_fingerprint="reporter-device",
            schema_version=1,
        )

    @patch("apps.safety.services.fleet_alert_issuer.FleetAlertIssuer._build_pdf_attachment")
    @patch("apps.safety.services.fleet_alert_issuer.EmailMultiAlternatives")
    def test_issue_writes_notifications_and_batched_email_to_selected_vessels(self, email_class, pdf_attachment) -> None:
        pdf_attachment.return_value = SimpleNamespace(
            file_name="NM-2026-023-near-miss.pdf",
            content=b"%PDF-near-miss",
            content_type="application/pdf",
        )
        email_message = email_class.return_value
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/",
            {
                "alert_text": "Review suspended-access staging controls immediately and brief all deck teams before the next ladder transfer.",
                "fleet_learning_text": "Loose access components must be verified before personnel transfer and repeated after heavy weather.",
                "recipient_vessel_ids": [VESSEL_7, VESSEL_8],
                "typed_name": "DPA Reviewer",
                "device_fingerprint": "dpa-browser-1",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="DPA",
                fleet_vessel_ids=[VESSEL_7, VESSEL_8, VESSEL_9],
                user_id="dpa-1",
            ),
        )

        with override_settings(
            DEFAULT_FROM_EMAIL="KSM Marine <pms@cymsol.co.in>",
            EMAIL_HOST_USER="pms@cymsol.co.in",
            EMAIL_HOST_PASSWORD="smtp-password",
        ):
            response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["issued"])
        self.assertEqual(response.data["notifications_emitted"], 2)
        self.assertEqual(response.data["emails_sent"], 2)
        self.assertEqual(response.data["email_failed"], 0)
        self.assertEqual(response.data["vessels_without_email"], 0)
        self.assertEqual(response.data["circular_publish"]["status"], "WORKSPACE_SEAM")
        self.assertEqual(response.data["sla"]["status"], "ISSUED_ON_TIME")
        email_class.assert_called_once()
        self.assertEqual(email_class.call_args.kwargs["to"], [])
        self.assertEqual(set(email_class.call_args.kwargs["bcc"]), {"seven@example.com", "eight@example.com"})
        self.assertEqual(tuple(email_class.call_args.kwargs["cc"]), ("HSSEQ@kaizenship.net",))
        self.assertEqual(email_class.call_args.kwargs["from_email"], "KSM Marine <pms@cymsol.co.in>")
        self.assertIn("Please review what happened in the attached PDF", email_class.call_args.kwargs["body"])
        self.assertNotIn("Fleet learning / lessons", email_class.call_args.kwargs["body"])
        email_message.attach.assert_called_once_with(
            "NM-2026-023-near-miss.pdf",
            b"%PDF-near-miss",
            "application/pdf",
        )
        self.assertEqual(email_message.send.call_count, 1)

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(
            set(Notification.objects.values_list("notification_type", flat=True)),
            {"NEAR_MISS_FLEET_ALERT"},
        )
        self.assertTrue(
            all("Fleet alert" in title for title in Notification.objects.values_list("title", flat=True))
        )

        field_names = set(
            SafetyFieldHistory.objects.filter(parent_id=self.near_miss.pk).values_list("field_name", flat=True)
        )
        self.assertTrue(
            {
                "fleet_alert_issued_at",
                "fleet_alert_text",
                "fleet_alert_signature",
                "near_miss_circular_publish",
                "near_miss_fleet_learning",
                "updated_by",
                "updated_date",
            }.issubset(field_names)
        )

    def test_workspace_dedupes_and_labels_recipient_vessels(self) -> None:
        request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/")
        force_authenticate(
            request,
            user=build_user(
                role_name="DPA",
                fleet_vessel_ids=[VESSEL_7, VESSEL_7, VESSEL_8, VESSEL_7],
                user_id="dpa-1",
            ),
        )

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["recipients"], [VESSEL_7, VESSEL_8])
        self.assertEqual([row["vessel_id"] for row in response.data["recipient_vessels"]], [VESSEL_7, VESSEL_8])
        self.assertEqual([row["display_name"] for row in response.data["recipient_vessels"]], ["Vessel Seven", "Vessel Eight"])

    def test_issue_is_restricted_to_dpa(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/",
            {
                "alert_text": "Review the control gap fleet-wide.",
                "fleet_learning_text": "The fleet learning is withheld from this unauthorized attempt.",
                "typed_name": "Master User",
                "device_fingerprint": "master-browser-1",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="MASTER",
                fleet_vessel_ids=[VESSEL_7, VESSEL_8],
                user_id="master-7",
            ),
        )

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 403)

    def test_issue_blocks_after_7_day_sla(self) -> None:
        Incident.objects.filter(pk=self.near_miss.pk).update(created_date=timezone.now() - timedelta(days=8))
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/",
            {
                "alert_text": "Review the control gap fleet-wide.",
                "fleet_learning_text": "Late fleet learning should be rejected by the hard SLA gate.",
                "typed_name": "DPA Reviewer",
                "device_fingerprint": "dpa-browser-1",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="DPA",
                fleet_vessel_ids=[VESSEL_7, VESSEL_8],
                user_id="dpa-1",
            ),
        )

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("within 1 week", str(response.data))

    @patch("apps.safety.services.fleet_alert_issuer.FleetAlertIssuer._build_pdf_attachment")
    @patch("apps.safety.services.fleet_alert_issuer.EmailMultiAlternatives")
    def test_late_issue_requires_and_records_sla_extension_reason(self, email_class, pdf_attachment) -> None:
        pdf_attachment.return_value = SimpleNamespace(
            file_name="late-near-miss.pdf",
            content=b"%PDF",
            content_type="application/pdf",
        )
        Incident.objects.filter(pk=self.near_miss.pk).update(created_date=timezone.now() - timedelta(days=8))
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/",
            {
                "alert_text": "Review the control gap fleet-wide.",
                "fleet_learning_text": "Late fleet learning is still circulated after DPA extension.",
                "recipient_vessel_ids": [VESSEL_7],
                "sla_extension_reason": "DPA approved late issue after office review.",
                "typed_name": "DPA Reviewer",
                "device_fingerprint": "dpa-browser-1",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="DPA",
                fleet_vessel_ids=[VESSEL_7, VESSEL_8],
                user_id="dpa-1",
            ),
        )

        with override_settings(EMAIL_HOST_USER="pms@cymsol.co.in", EMAIL_HOST_PASSWORD="smtp-password"):
            response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sla"]["status"], "ISSUED_LATE_WITH_EXTENSION")
        self.assertEqual(response.data["notifications_emitted"], 1)
        email_class.return_value.attach.assert_called_once_with(
            "late-near-miss.pdf",
            b"%PDF",
            "application/pdf",
        )
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_id=self.near_miss.pk,
                field_name="fleet_alert_sla_extension",
            ).exists()
        )
