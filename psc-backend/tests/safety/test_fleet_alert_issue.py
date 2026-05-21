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

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.views.fleet_alert import FleetAlertIssueView


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
        fleet_vessel_ids=fleet_vessel_ids or ["7"],
        vessel_ids=fleet_vessel_ids or ["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class FleetAlertIssueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.view = FleetAlertIssueView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/023",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="TRIAGED",
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

    def test_issue_writes_one_notification_row_per_vessel_in_company_scope(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/",
            {
                "alert_text": "Review suspended-access staging controls immediately and brief all deck teams before the next ladder transfer.",
                "fleet_learning_text": "Loose access components must be verified before personnel transfer and repeated after heavy weather.",
                "recipient_vessel_ids": ["7", "8"],
                "typed_name": "DPA Reviewer",
                "device_fingerprint": "dpa-browser-1",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="DPA",
                fleet_vessel_ids=["7", "8", "9"],
                user_id="dpa-1",
            ),
        )

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["issued"])
        self.assertEqual(response.data["notifications_emitted"], 2)
        self.assertEqual(response.data["circular_publish"]["status"], "WORKSPACE_SEAM")
        self.assertEqual(response.data["sla"]["status"], "ISSUED_ON_TIME")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipient_ref, notification_kind, title
                FROM master_notification
                ORDER BY id
                """
            )
            rows = cursor.fetchall()

        self.assertEqual([row[0] for row in rows], ["7", "8"])
        self.assertTrue(all(row[1] == "NEAR_MISS_FLEET_ALERT" for row in rows))
        self.assertTrue(all("Fleet alert" in row[2] for row in rows))

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
                fleet_vessel_ids=["7", "7", "8", "7"],
                user_id="dpa-1",
            ),
        )

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["recipients"], ["7", "8"])
        self.assertEqual([row["vessel_id"] for row in response.data["recipient_vessels"]], ["7", "8"])
        self.assertEqual([row["display_name"] for row in response.data["recipient_vessels"]], ["7", "8"])

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
                fleet_vessel_ids=["7", "8"],
                user_id="master-7",
            ),
        )

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
                fleet_vessel_ids=["7", "8"],
                user_id="dpa-1",
            ),
        )

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("within 1 week", str(response.data))

    def test_late_issue_requires_and_records_sla_extension_reason(self) -> None:
        Incident.objects.filter(pk=self.near_miss.pk).update(created_date=timezone.now() - timedelta(days=8))
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/fleet-alert/",
            {
                "alert_text": "Review the control gap fleet-wide.",
                "fleet_learning_text": "Late fleet learning is still circulated after DPA extension.",
                "recipient_vessel_ids": ["7"],
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
                fleet_vessel_ids=["7", "8"],
                user_id="dpa-1",
            ),
        )

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sla"]["status"], "ISSUED_LATE_WITH_EXTENSION")
        self.assertEqual(response.data["notifications_emitted"], 1)
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_id=self.near_miss.pk,
                field_name="fleet_alert_sla_extension",
            ).exists()
        )
