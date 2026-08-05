from __future__ import annotations

import unittest
from unittest.mock import patch

from django.db import connection

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.notifications.models import Notification
from apps.safety.services.notification_writer import NotificationWriter


class RaisingSlackNotifier:
    def send(self, *, title: str, message: str, payload: dict[str, object]) -> None:
        raise RuntimeError("Slack webhook unavailable")


class SlackBestEffortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS psc_notification")
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Notification)

    def tearDown(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS psc_notification")

    def test_slack_failure_does_not_break_primary_notification_write(self) -> None:
        writer = NotificationWriter(slack_notifier=RaisingSlackNotifier())

        with patch(
            "apps.safety.services.notification_writer._get_office_user_ids_for_roles",
            return_value=["EMP001", "EMP002"],
        ):
            result = writer.dispatch_notification(
                record_id=99,
                recipients=["DPA", "FM"],
                kind="INCIDENT_PHASE_2_SUBMITTED",
                title="Incident submitted to office",
                message="RED-band incident moved forward.",
                payload={"risk_band": "RED"},
                send_slack=True,
            )

        self.assertEqual(len(result.notification_rows), 2)
        self.assertTrue(result.slack_attempted)
        self.assertFalse(result.slack_delivered)
        self.assertIn("Slack webhook unavailable", result.slack_error or "")

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM psc_notification")
            row_count = cursor.fetchone()[0]

        self.assertEqual(row_count, 2)
