from __future__ import annotations

import unittest

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_master_notification_table


bootstrap_django()

from apps.safety.services.notification_writer import NotificationWriter


class NotificationWriterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_master_notification_table()
        self.writer = NotificationWriter()

    def test_writes_one_row_per_recipient_to_master_notification(self) -> None:
        rows = self.writer.write_notification(
            record_id=42,
            recipients=["PIC-1", "DPA", "SAFETY_CHANNEL"],
            kind="INCIDENT_PHASE_2_SUBMITTED",
            title="Incident submitted to office",
            message="Incident 42 has entered Phase 3.",
            payload={"risk_band": "YELLOW"},
        )

        self.assertEqual(len(rows), 3)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipient_ref, notification_kind, title, payload_json
                FROM master_notification
                ORDER BY id
                """
            )
            persisted = cursor.fetchall()

        self.assertEqual(len(persisted), 3)
        self.assertEqual([row[0] for row in persisted], ["PIC-1", "DPA", "SAFETY_CHANNEL"])
        self.assertTrue(all(row[1] == "INCIDENT_PHASE_2_SUBMITTED" for row in persisted))

    def test_skips_write_when_master_notification_schema_is_old(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS master_notification")
            cursor.execute(
                """
                CREATE TABLE master_notification (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(256) NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )

        rows = self.writer.write_notification(
            record_id=42,
            recipients=["PIC-1"],
            kind="INCIDENT_PHASE_2_SUBMITTED",
            title="Incident submitted to office",
            message="Incident 42 has entered Phase 3.",
        )

        self.assertEqual(rows, [])
