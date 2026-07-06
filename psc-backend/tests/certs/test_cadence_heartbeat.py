from __future__ import annotations

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.management import call_command
from django.db import connection
from django.test import RequestFactory

from apps.certs.jobs.cadence_heartbeat import run_cadence_deadman_check, run_cadence_heartbeat
from apps.certs.urls import health_check
from tests.certs.test_notification_routing import RecordingSlackRelay


def recreate_settings_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS vims_certs_settings")
        cursor.execute(
            """
            CREATE TABLE vims_certs_settings (
                settings_id CHAR(36) PRIMARY KEY,
                singleton_key VARCHAR(32) NOT NULL UNIQUE,
                last_heartbeat_at DATETIME NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                updated_by VARCHAR(64) NULL
            )
            """
        )


class CertCadenceHeartbeatTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_settings_table()

    def test_cadence_heartbeat_stamps_single_settings_row(self) -> None:
        now = datetime(2026, 6, 29, 9, 0, tzinfo=timezone.utc)

        result = run_cadence_heartbeat(now=now)

        self.assertEqual(result.last_heartbeat_at, now)
        with connection.cursor() as cursor:
            cursor.execute("SELECT singleton_key, last_heartbeat_at, updated_by FROM vims_certs_settings")
            rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "certs")
        self.assertIn("2026-06-29 09:00:00", str(rows[0][1]))
        self.assertEqual(rows[0][2], "system.cadence_heartbeat")

    def test_deadman_check_sends_office_slack_when_heartbeat_is_stale(self) -> None:
        heartbeat = datetime(2026, 6, 29, 6, 0, tzinfo=timezone.utc)
        run_cadence_heartbeat(now=heartbeat)
        relay = RecordingSlackRelay()

        result = run_cadence_deadman_check(
            now=heartbeat + timedelta(hours=2, minutes=1),
            slack_relay=relay,
        )

        self.assertTrue(result.stale)
        self.assertTrue(result.alert_sent)
        self.assertEqual(len(relay.calls), 1)
        self.assertEqual(relay.calls[0]["payload"]["eventType"], "cadence_deadman_alert")
        self.assertEqual(relay.calls[0]["payload"]["staleThresholdSeconds"], 7200)
        self.assertEqual(relay.direct_messages, [])

    def test_deadman_check_does_not_send_when_heartbeat_is_fresh(self) -> None:
        heartbeat = datetime(2026, 6, 29, 8, 30, tzinfo=timezone.utc)
        run_cadence_heartbeat(now=heartbeat)
        relay = RecordingSlackRelay()

        result = run_cadence_deadman_check(
            now=heartbeat + timedelta(minutes=45),
            slack_relay=relay,
        )

        self.assertFalse(result.stale)
        self.assertFalse(result.alert_sent)
        self.assertEqual(relay.calls, [])

    def test_health_endpoint_exposes_last_cadence_heartbeat_without_auth(self) -> None:
        heartbeat = datetime(2026, 6, 29, 9, 15, tzinfo=timezone.utc)
        run_cadence_heartbeat(now=heartbeat)

        response = health_check(RequestFactory().get("/api/certs/health/"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"status": "ok"', response.content)
        self.assertIn(b'"last_cadence_heartbeat": "2026-06-29T09:15:00Z"', response.content)

    @patch("apps.certs.management.commands.stamp_cadence_heartbeat.run_cadence_heartbeat")
    def test_stamp_heartbeat_management_command_is_scheduler_target(self, run_cadence_heartbeat_mock) -> None:
        call_command("stamp_cadence_heartbeat")

        run_cadence_heartbeat_mock.assert_called_once()

    @patch("apps.certs.management.commands.check_cadence_deadman.run_cadence_deadman_check")
    def test_deadman_management_command_is_scheduler_target(self, run_deadman_mock) -> None:
        call_command("check_cadence_deadman")

        run_deadman_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
