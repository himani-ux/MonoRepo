from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.db import connection
from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_master_notification_table,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.tasks.fleet_alert_monitor import monitor_high_priority_near_miss_fleet_alerts
from apps.safety.views.fleet_alert import FleetAlertIssueView


def build_user(
    *,
    role_name: str,
    fleet_vessel_ids: list[str] | None = None,
    user_id: str = "user-1",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_024"],
        fleet_vessel_ids=fleet_vessel_ids or ["7"],
        vessel_ids=[],
        is_global=role_name in {"DPA", "FM"},
    )


class FleetAlertEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.view = FleetAlertIssueView.as_view()
        self.base_time = timezone.now().replace(microsecond=0)
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/041",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="TRIAGED",
            current_phase=1,
            near_miss_priority="HIGH",
            narrative="A mooring-station near miss exposed a sister-vessel control weakness, so the report requires a fleet alert and follow-up before the next parallel operation.",
            created_by="reporter-1",
            reporter_id="crew-4",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            reporter_device_fingerprint="reporter-device",
            schema_version=1,
        )
        Incident.objects.filter(pk=self.near_miss.pk).update(created_date=self.base_time - timedelta(days=6))

    def test_high_priority_near_miss_issue_path_blocks_further_nudges_after_publish(self) -> None:
        get_request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/")
        force_authenticate(
            get_request,
            user=build_user(role_name="DPA", fleet_vessel_ids=["7", "8"], user_id="dpa-1"),
        )

        get_response = self.view(get_request, id=self.near_miss.pk)

        self.assertEqual(get_response.status_code, 200)
        self.assertFalse(get_response.data["issued"])
        self.assertIn("draft", get_response.data)

        post_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/",
            {
                "alert_text": "Brief mooring teams on the sister-vessel control gap before the next line-handling evolution.",
                "fleet_learning_text": "Line-handling teams must verify exclusion controls before every mooring evolution.",
                "typed_name": "DPA Reviewer",
                "device_fingerprint": "dpa-device-2",
            },
            format="json",
        )
        force_authenticate(
            post_request,
            user=build_user(role_name="DPA", fleet_vessel_ids=["7", "8"], user_id="dpa-1"),
        )

        post_response = self.view(post_request, id=self.near_miss.pk)

        self.assertEqual(post_response.status_code, 200)
        self.assertTrue(post_response.data["issued"])
        self.assertEqual(post_response.data["notifications_emitted"], 2)

        monitor_high_priority_near_miss_fleet_alerts(now=self.base_time + timedelta(days=8))

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT notification_kind, recipient_ref
                FROM master_notification
                ORDER BY id
                """
            )
            rows = cursor.fetchall()

        self.assertEqual(
            rows,
            [
                ("NEAR_MISS_FLEET_ALERT", "7"),
                ("NEAR_MISS_FLEET_ALERT", "8"),
            ],
        )
