from __future__ import annotations

from datetime import timedelta
import unittest

from django.db import connection
from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
)


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.tasks.fleet_alert_monitor import monitor_high_priority_near_miss_fleet_alerts


class FleetAlertNudgeScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.base_time = timezone.now().replace(microsecond=0)
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/031",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="TRIAGED",
            current_phase=1,
            near_miss_priority="HIGH",
            narrative="A heavy-weather access control gap was intercepted before injury, requiring fleet-wide preventive reinforcement and a documented follow-up alert.",
            created_by="reporter-1",
            reporter_id="crew-9",
            reporter_name="Crew Reporter",
            reporter_rank="OS",
            reporter_device_fingerprint="reporter-device",
            schema_version=1,
        )
        Incident.objects.filter(pk=self.near_miss.pk).update(created_date=self.base_time - timedelta(days=5))

    def test_day_5_day_6_and_day_8_notifications_fire_once_each(self) -> None:
        monitor_high_priority_near_miss_fleet_alerts(now=self.base_time)
        monitor_high_priority_near_miss_fleet_alerts(now=self.base_time)
        monitor_high_priority_near_miss_fleet_alerts(now=self.base_time + timedelta(days=1))
        monitor_high_priority_near_miss_fleet_alerts(now=self.base_time + timedelta(days=3))

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipient_ref, notification_kind
                FROM master_notification
                ORDER BY id
                """
            )
            rows = cursor.fetchall()

        self.assertEqual(
            rows,
            [
                ("DPA", "NEAR_MISS_FLEET_ALERT_NUDGE_DAY_5"),
                ("DPA", "NEAR_MISS_FLEET_ALERT_NUDGE_DAY_6"),
                ("FM", "NEAR_MISS_FLEET_ALERT_ESCALATION_DAY_8"),
            ],
        )
