from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.certs.services.settings_repository import SettingsRepository
from apps.certs.views.settings_views import AlertConfigView, SettingsView
from tests.certs.test_tracked_item_api import make_user


def alert_config_row(**overrides):
    row = {
        "config_id": str(uuid.uuid4()),
        "trigger_event": "certificate_expiry",
        "default_lead_days": 90,
        "dpa_override_lead_days": 75,
        "recipients_default_json": '["DPA","FM"]',
        "dpa_override_recipients_json": '["DPA"]',
        "escalation_cadence_json": '{"levels":[30,14,7]}',
        "ocr_threshold_office": "0.800",
        "ocr_threshold_vessel": "0.850",
        "ocr_threshold_manual_floor": "0.600",
        "class_snapshot_cadence_months": 3,
        "class_snapshot_lead_months": 1,
        "event_snapshot_grace_days": 14,
        "draft_expire_days": 7,
        "created_at": "2026-06-30T00:00:00Z",
        "updated_at": "2026-06-30T00:00:00Z",
        "updated_by": "dpa-1",
    }
    row.update(overrides)
    return row


def settings_snapshot(**overrides):
    row = {
        "settings": {
            "settings_id": str(uuid.uuid4()),
            "singleton_key": "certs",
            "last_heartbeat_at": "2026-06-30T01:00:00Z",
            "created_at": "2026-06-30T00:00:00Z",
            "updated_at": "2026-06-30T00:00:00Z",
            "updated_by": "dpa-1",
        },
        "alert_configs": [alert_config_row()],
        "slack_routes": [
            {
                "vessel_id": "vessel-1",
                "vessel_name": "KSM Fortitude",
                "imo_number": "9876543",
                "slack_channel_vessel": "#certs-ksmf",
                "slack_channel_office_default": "#certs-office",
                "updated_at": "2026-06-30T00:00:00Z",
                "updated_by": "dpa-1",
            }
        ],
    }
    row.update(overrides)
    return row


class SettingsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.dpa = make_user(
            role="DPA",
            form_ids=["CERT_F_006"],
            process_ids=["CERT_P_008"],
            has_global_vessel_access=True,
        )
        self.fm = make_user(
            role="Fleet Manager",
            form_ids=["CERT_F_006"],
            process_ids=["CERT_P_008"],
            has_global_vessel_access=True,
        )

    @patch("apps.certs.views.settings_views.repository")
    def test_settings_are_dpa_only(self, repository) -> None:
        repository.get_settings_snapshot.return_value = settings_snapshot()
        request = self.factory.get("/api/certs/settings/")
        force_authenticate(request, user=self.fm)

        denied = SettingsView.as_view()(request)

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        repository.get_settings_snapshot.assert_not_called()

        request = self.factory.get("/api/certs/settings/")
        force_authenticate(request, user=self.dpa)

        response = SettingsView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["alertConfigs"][0]["triggerEvent"], "certificate_expiry")
        self.assertEqual(response.data["slackRoutes"][0]["slackChannelVessel"], "#certs-ksmf")

    @patch("apps.certs.views.settings_views.record_audit_event")
    @patch("apps.certs.views.settings_views.repository")
    def test_patch_updates_settings_surfaces_and_audits(self, repository, record_audit_event) -> None:
        config_id = str(uuid.uuid4())
        before = settings_snapshot(alert_configs=[alert_config_row(config_id=config_id, dpa_override_lead_days=75)])
        after = settings_snapshot(alert_configs=[alert_config_row(config_id=config_id, dpa_override_lead_days=60)])
        repository.update_settings.return_value = (before, after)
        request = self.factory.patch(
            "/api/certs/settings/",
            {
                "alertConfigs": [
                    {
                        "id": config_id,
                        "dpaOverrideLeadDays": 60,
                        "dpaOverrideRecipients": ["DPA", "Fleet Manager"],
                        "escalationCadence": {"levels": [60, 30, 7]},
                        "ocrThresholdOffice": "0.810",
                        "ocrThresholdVessel": "0.860",
                        "ocrThresholdManualFloor": "0.620",
                        "classSnapshotCadenceMonths": 3,
                        "classSnapshotLeadMonths": 1,
                        "eventSnapshotGraceDays": 14,
                        "draftExpireDays": 7,
                    }
                ],
                "retentionOverride": {
                    "blobId": str(uuid.uuid4()),
                    "dpaRetentionOverrideUntil": "2027-06-30T00:00:00Z",
                },
                "slackRoutes": [
                    {
                        "vesselId": "vessel-1",
                        "slackChannelVessel": "#certs-ksmf",
                        "slackChannelOfficeDefault": "#certs-office",
                    }
                ],
                "reason": "DPA updated certificate notification and routing settings.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = SettingsView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["alertConfigs"][0]["dpaOverrideLeadDays"], 60)
        repository.update_settings.assert_called_once()
        update_payload = repository.update_settings.call_args.kwargs["values"]
        self.assertEqual(update_payload["alertConfigs"][0]["dpaOverrideLeadDays"], 60)
        self.assertEqual(update_payload["slackRoutes"][0]["slackChannelVessel"], "#certs-ksmf")
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "settings_change")
        self.assertEqual(record_audit_event.call_args.kwargs["entity_type"], "settings")
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["source"], "api.certs.settings")

    @patch("apps.certs.views.settings_views.repository")
    def test_alert_config_endpoint_returns_config_rows_only(self, repository) -> None:
        repository.list_alert_configs.return_value = [alert_config_row(trigger_event="class_snapshot_due")]
        request = self.factory.get("/api/certs/alerts/config/")
        force_authenticate(request, user=self.dpa)

        response = AlertConfigView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["triggerEvent"], "class_snapshot_due")


class SettingsRepositoryTests(unittest.TestCase):
    @patch("apps.certs.services.settings_repository.connection")
    def test_repository_updates_existing_settings_tables_only(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = [("settings_id",), ("singleton_key",), ("last_heartbeat_at",), ("created_at",), ("updated_at",), ("updated_by",)]
        cursor.fetchone.return_value = ("settings-1", "certs", None, None, None, "dpa-1")
        cursor.fetchall.side_effect = [
            [],
            [],
            [],
            [],
        ]
        connection.cursor.return_value.__enter__.return_value = cursor

        SettingsRepository().update_settings(
            {
                "alertConfigs": [
                    {
                        "id": "config-1",
                        "dpaOverrideLeadDays": 60,
                        "dpaOverrideRecipients": ["DPA"],
                        "escalationCadence": {"levels": [60, 30, 7]},
                        "ocrThresholdOffice": "0.810",
                        "ocrThresholdVessel": "0.860",
                        "ocrThresholdManualFloor": "0.620",
                        "classSnapshotCadenceMonths": 3,
                        "classSnapshotLeadMonths": 1,
                        "eventSnapshotGraceDays": 14,
                        "draftExpireDays": 7,
                    }
                ],
                "retentionOverride": {
                    "blobId": "blob-1",
                    "dpaRetentionOverrideUntil": "2027-06-30T00:00:00Z",
                },
                "slackRoutes": [
                    {
                        "vesselId": "vessel-1",
                        "slackChannelVessel": "#certs-ksmf",
                        "slackChannelOfficeDefault": "#certs-office",
                    }
                ],
            },
            actor_id="dpa-1",
        )

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        self.assertIn("UPDATE dbo.vims_certs_alert_config", sql_text)
        self.assertIn("ocr_threshold_office", sql_text)
        self.assertIn("UPDATE dbo.vims_certs_pdf_blob", sql_text)
        self.assertIn("dpa_retention_override_until", sql_text)
        self.assertIn("UPDATE dbo.vims_certs_vessel_config", sql_text)
        self.assertIn("slack_channel_vessel", sql_text)
        self.assertNotIn("ALTER TABLE", sql_text)


if __name__ == "__main__":
    unittest.main()
