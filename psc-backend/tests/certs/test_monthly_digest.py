from __future__ import annotations

import json
import os
import unittest
from datetime import datetime, timezone

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.db import connection

from apps.certs.jobs.digest_monthly import run_monthly_digest
from apps.certs.services.notification_dispatcher import CertNotificationDispatcher, CertNotificationRecipient
from tests.certs.test_notification_routing import RecordingSlackRelay, recreate_notification_tables


def recreate_digest_tables() -> None:
    recreate_notification_tables()
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS vims_certs_tracked_item")
        cursor.execute(
            """
            CREATE TABLE vims_certs_tracked_item (
                tracked_item_id CHAR(36) PRIMARY KEY,
                vessel_id CHAR(36) NOT NULL,
                status VARCHAR(32) NOT NULL,
                expiry_date DATE NULL,
                lifecycle_status VARCHAR(24) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO vims_certs_tracked_item (
                tracked_item_id, vessel_id, status, expiry_date, lifecycle_status
            ) VALUES
            ('11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'expired', '2026-06-20', 'active'),
            ('22222222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'critical', '2026-07-20', 'active'),
            ('33333333-3333-3333-3333-333333333333', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'ok', '2027-01-20', 'active'),
            ('44444444-4444-4444-4444-444444444444', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'expired', '2026-06-01', 'decommissioned')
            """
        )


class CertMonthlyDigestTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_digest_tables()

    def test_monthly_digest_dispatches_only_dpa_and_marine_superintendent_at_ict_window(self) -> None:
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher(slack_relay=relay)

        result = run_monthly_digest(
            now=datetime(2026, 7, 1, 1, 0, tzinfo=timezone.utc),
            dispatcher=dispatcher,
            candidate_recipients=[
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
                CertNotificationRecipient(user_id="marine-1", role="Marine Superintendent", side="office"),
                CertNotificationRecipient(user_id="fm-1", role="Fleet Manager", side="office"),
                CertNotificationRecipient(user_id="master-1", role="Master", side="vessel"),
            ],
        )

        self.assertTrue(result.dispatched)
        self.assertEqual(result.recipient_ids, ["dpa-1", "marine-1"])
        self.assertEqual(len(relay.calls), 2)
        self.assertEqual([call["payload"]["triggerEvent"] for call in relay.calls], ["monthly_digest", "monthly_digest"])

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT mn.recipient_ref, mn.notification_kind, meta.channels_json, mn.payload_json
                FROM master_notification mn
                JOIN vims_certs_notification_meta meta ON meta.master_notification_id = mn.id
                ORDER BY mn.recipient_ref
                """
            )
            rows = cursor.fetchall()

        self.assertEqual([row[0] for row in rows], ["dpa-1", "marine-1"])
        self.assertEqual({row[1] for row in rows}, {"monthly_digest"})
        self.assertEqual(json.loads(rows[0][2])[0]["channels"], ["in_app", "slack"])
        payload = json.loads(rows[0][3])
        self.assertEqual(payload["digestFrequency"], "monthly")
        self.assertEqual(payload["summary"]["activeTrackedItems"], 3)
        self.assertEqual(payload["summary"]["expiredItems"], 1)
        self.assertEqual(payload["summary"]["criticalItems"], 1)
        self.assertNotIn("certRows", payload)

    def test_monthly_digest_skips_outside_first_day_0800_ict_window(self) -> None:
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher(slack_relay=relay)

        result = run_monthly_digest(
            now=datetime(2026, 7, 1, 0, 59, tzinfo=timezone.utc),
            dispatcher=dispatcher,
            candidate_recipients=[
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
                CertNotificationRecipient(user_id="marine-1", role="Marine Superintendent", side="office"),
            ],
        )

        self.assertFalse(result.dispatched)
        self.assertEqual(result.reason, "outside_monthly_digest_window")
        self.assertEqual(relay.calls, [])

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM master_notification")
            self.assertEqual(cursor.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
