from __future__ import annotations

import json
import os
import unittest
from datetime import timedelta
import uuid
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.certs.services.notification_dispatcher import (
    CertNotificationDispatcher,
    CertNotificationRecipient,
    build_expiry_escalation_recipients,
)
from apps.certs.services.email_delivery import CertEmailDeliveryService, EMAIL_RETRY_BACKOFF_MINUTES
from apps.certs.services.magic_link import MagicLinkExpired, build_magic_link_token
from apps.certs.views.notification_views import CertNotificationListView, CertNotificationMagicAckView
from tests.certs.test_tracked_item_api import make_user


def recreate_notification_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS vims_certs_notification_meta")
        cursor.execute("DROP TABLE IF EXISTS master_notification")
        cursor.execute(
            """
            CREATE TABLE master_notification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_code VARCHAR(32) NOT NULL,
                record_id VARCHAR(64) NOT NULL,
                recipient_ref VARCHAR(64) NOT NULL,
                notification_kind VARCHAR(64) NOT NULL,
                title VARCHAR(256) NOT NULL,
                message TEXT NOT NULL,
                delivery_channel VARCHAR(32) NOT NULL,
                payload_json TEXT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE vims_certs_notification_meta (
                notification_id CHAR(36) PRIMARY KEY,
                master_notification_id INTEGER NOT NULL,
                trigger_event VARCHAR(64) NOT NULL,
                cert_row_id CHAR(36) NULL,
                vessel_id CHAR(36) NULL,
                recipients_json TEXT NOT NULL,
                channels_json TEXT NOT NULL,
                sent_at DATETIME NOT NULL,
                delivery_status_json TEXT NULL,
                ack_user_id VARCHAR(64) NULL,
                ack_at DATETIME NULL,
                ack_channel VARCHAR(16) NULL,
                escalation_level INTEGER NOT NULL DEFAULT 0,
                body_content TEXT NULL,
                body_purged_at DATETIME NULL,
                idempotency_key VARCHAR(128) NOT NULL UNIQUE
            )
            """
        )
        cursor.execute("DROP TABLE IF EXISTS vims_certs_vessel_config")
        cursor.execute(
            """
            CREATE TABLE vims_certs_vessel_config (
                vessel_id CHAR(36) PRIMARY KEY,
                slack_channel_vessel VARCHAR(64) NULL,
                slack_channel_office_default VARCHAR(64) NULL
            )
            """
        )


class RecordingSlackRelay:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.direct_messages: list[dict[str, object]] = []

    def send_office_notification(
        self,
        *,
        channel: str,
        title: str,
        message: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        self.calls.append(
            {
                "channel": channel,
                "title": title,
                "message": message,
                "payload": payload,
            }
        )
        return {
            "attempted": True,
            "delivered": True,
            "channel": channel,
            "providerMessageId": "slack-123",
            "error": None,
        }

    def send_direct_message(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        self.direct_messages.append(
            {
                "user_id": user_id,
                "title": title,
                "message": message,
                "payload": payload,
            }
        )
        return {
            "attempted": True,
            "delivered": True,
            "channel": "slack_dm",
            "providerMessageId": "dm-123",
            "error": None,
        }


class RaisingSlackRelay:
    def send_office_notification(
        self,
        *,
        channel: str,
        title: str,
        message: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        raise RuntimeError("Slack webhook unavailable")


class CertNotificationRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_notification_tables()

    def test_per_side_routing_writes_vessel_email_only_and_office_slack_only(self) -> None:
        cert_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        dispatcher = CertNotificationDispatcher()

        result = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=cert_id,
            vessel_id=vessel_id,
            recipients=[
                CertNotificationRecipient(user_id="master-1", role="Master", side="vessel"),
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
            ],
            title="Certificate expires in 7 days",
            message="Renew IOPP for KSM Fortitude.",
            payload={"daysToGo": 7},
            escalation_level=2,
            idempotency_scope="cert-expiring-7d",
        )

        self.assertEqual(len(result.notification_rows), 2)
        self.assertEqual(result.channels_by_recipient["master-1"], ["in_app", "email"])
        self.assertEqual(result.channels_by_recipient["dpa-1"], ["in_app", "slack"])

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT mn.recipient_ref, mn.delivery_channel, meta.channels_json, meta.escalation_level
                FROM master_notification mn
                JOIN vims_certs_notification_meta meta ON meta.master_notification_id = mn.id
                ORDER BY mn.recipient_ref
                """
            )
            rows = cursor.fetchall()

        self.assertEqual(rows[0][0], "dpa-1")
        self.assertEqual(rows[0][1], "IN_APP")
        self.assertEqual(json.loads(rows[0][2])[0]["channels"], ["in_app", "slack"])
        dpa_delivery = json.loads(
            self._delivery_status_for_recipient("dpa-1")
        )[0]["channels"]
        self.assertNotIn("ackUrl", dpa_delivery[1])
        self.assertEqual(rows[0][3], 2)
        self.assertEqual(rows[1][0], "master-1")
        self.assertEqual(json.loads(rows[1][2])[0]["channels"], ["in_app", "email"])
        master_delivery = json.loads(
            self._delivery_status_for_recipient("master-1")
        )[0]["channels"]
        self.assertIn("/api/certs/notifications/ack/", master_delivery[1]["ackUrl"])

    def test_office_slack_relay_uses_vessel_office_channel_and_records_delivery(self) -> None:
        cert_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher(slack_relay=relay)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_certs_vessel_config (
                    vessel_id, slack_channel_office_default
                ) VALUES (%s, %s)
                """,
                [str(vessel_id), "#certs-office-dpa"],
            )

        dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=cert_id,
            vessel_id=vessel_id,
            recipients=[CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office")],
            title="Certificate expires in 7 days",
            message="Renew IOPP for KSM Fortitude.",
            payload={"daysToGo": 7},
            escalation_level=2,
            idempotency_scope="slack-office-delivered",
        )

        self.assertEqual(len(relay.calls), 1)
        self.assertEqual(relay.calls[0]["channel"], "#certs-office-dpa")
        self.assertEqual(relay.calls[0]["payload"]["recipient"]["userId"], "dpa-1")
        self.assertEqual(relay.calls[0]["payload"]["module"], "CERTS")

        delivery = json.loads(self._delivery_status_for_recipient("dpa-1"))[0]["channels"]
        self.assertEqual(delivery[1]["channel"], "slack")
        self.assertEqual(delivery[1]["status"], "delivered")
        self.assertEqual(delivery[1]["slackChannel"], "#certs-office-dpa")
        self.assertEqual(delivery[1]["providerMessageId"], "slack-123")
        self.assertNotIn("ackUrl", delivery[1])

    def test_office_slack_relay_uses_role_domain_channels_without_vessel_override(self) -> None:
        cert_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher(slack_relay=relay)

        dispatcher.dispatch(
            trigger_event="parser_anomaly",
            cert_row_id=cert_id,
            vessel_id=vessel_id,
            recipients=[
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
                CertNotificationRecipient(user_id="tech-1", role="Technical Superintendent", side="office"),
                CertNotificationRecipient(user_id="marine-1", role="Marine Superintendent", side="office"),
                CertNotificationRecipient(user_id="fm-1", role="Fleet Manager", side="office"),
            ],
            title="Parser anomaly detected",
            message="Review the parser anomaly for KSM Fortitude.",
            payload={"breachTypes": ["unmapped_critical", "parse_duration"]},
            idempotency_scope="role-domain-routing",
        )

        self.assertEqual(
            [call["channel"] for call in relay.calls],
            [
                "#certs-office-dpa",
                "#certs-office-tm",
                "#certs-office-marine",
                "#certs-office-fleet",
            ],
        )
        self.assertEqual(relay.direct_messages, [])

    def test_slack_relay_failure_is_best_effort_and_recorded_in_delivery_status(self) -> None:
        dispatcher = CertNotificationDispatcher(slack_relay=RaisingSlackRelay())

        result = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=uuid.uuid4(),
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="tm-1", role="Technical Manager", side="office")],
            title="Certificate expires in 7 days",
            message="Renew IOPP for KSM Fortitude.",
            idempotency_scope="slack-office-failed",
        )

        self.assertEqual(len(result.notification_rows), 1)
        delivery = json.loads(self._delivery_status_for_recipient("tm-1"))[0]["channels"]
        self.assertEqual(delivery[1]["channel"], "slack")
        self.assertEqual(delivery[1]["status"], "failed")
        self.assertEqual(delivery[1]["slackChannel"], "#certs-office-tm")
        self.assertIn("Slack webhook unavailable", delivery[1]["error"])

    def test_vessel_recipient_never_calls_slack_relay(self) -> None:
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher(slack_relay=relay)

        dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=uuid.uuid4(),
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="master-1", role="Master", side="vessel")],
            title="Certificate expires in 7 days",
            message="Renew IOPP for KSM Fortitude.",
            idempotency_scope="vessel-no-slack",
        )

        self.assertEqual(relay.calls, [])
        delivery = json.loads(self._delivery_status_for_recipient("master-1"))[0]["channels"]
        self.assertEqual([channel["channel"] for channel in delivery], ["in_app", "email"])

    def test_duplicate_notification_dispatch_is_silently_suppressed_within_24h(self) -> None:
        cert_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher(slack_relay=relay)
        recipient = CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office")

        first = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=cert_id,
            vessel_id=vessel_id,
            recipients=[recipient],
            title="Certificate expires in 7 days",
            message="Renew IOPP for KSM Fortitude.",
            idempotency_scope="duplicate-7d",
        )
        second = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=cert_id,
            vessel_id=vessel_id,
            recipients=[recipient],
            title="Certificate expires in 7 days",
            message="Renew IOPP for KSM Fortitude.",
            idempotency_scope="duplicate-7d",
        )

        self.assertEqual(len(first.notification_rows), 1)
        self.assertEqual(second.notification_rows, [])
        self.assertEqual(len(relay.calls), 1)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM master_notification")
            self.assertEqual(cursor.fetchone()[0], 1)
            cursor.execute("SELECT COUNT(*) FROM vims_certs_notification_meta")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_app_layer_idempotency_check_uses_24h_window(self) -> None:
        dispatcher = CertNotificationDispatcher()
        stale_sent_at = timezone.now() - timedelta(hours=25)
        stale_key = "stale-idempotency-key"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_notification (
                    module_code, record_id, recipient_ref, notification_kind,
                    title, message, delivery_channel, payload_json, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "CERTS",
                    "record-1",
                    "dpa-1",
                    "cert_expiring_7d",
                    "Old alert",
                    "Old body",
                    "IN_APP",
                    "{}",
                    stale_sent_at,
                ],
            )
            master_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO vims_certs_notification_meta (
                    notification_id, master_notification_id, trigger_event, cert_row_id,
                    vessel_id, recipients_json, channels_json, sent_at,
                    delivery_status_json, escalation_level, body_content, idempotency_key
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    master_id,
                    "cert_expiring_7d",
                    None,
                    None,
                    "[]",
                    "[]",
                    stale_sent_at,
                    "[]",
                    0,
                    "Old body",
                    stale_key,
                ],
            )

        self.assertFalse(dispatcher._idempotency_exists(stale_key, sent_at=timezone.now()))
        self.assertTrue(
            dispatcher._idempotency_exists(
                stale_key,
                sent_at=stale_sent_at + timedelta(minutes=30),
            )
        )

    def test_db_unique_race_rolls_back_master_row_and_skips_slack_send(self) -> None:
        cert_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        fixed_now = timezone.now()
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher(slack_relay=relay)
        idempotency_key = dispatcher._build_idempotency_key(
            cert_row_id=str(cert_id),
            trigger_event="cert_expiring_7d",
            sent_at=fixed_now,
            recipient_id="dpa-1",
            scope="race-7d",
        )
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_notification (
                    module_code, record_id, recipient_ref, notification_kind,
                    title, message, delivery_channel, payload_json, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "CERTS",
                    str(cert_id),
                    "dpa-1",
                    "cert_expiring_7d",
                    "Existing alert",
                    "Existing body",
                    "IN_APP",
                    "{}",
                    fixed_now,
                ],
            )
            master_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO vims_certs_notification_meta (
                    notification_id, master_notification_id, trigger_event, cert_row_id,
                    vessel_id, recipients_json, channels_json, sent_at,
                    delivery_status_json, escalation_level, body_content, idempotency_key
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    master_id,
                    "cert_expiring_7d",
                    str(cert_id),
                    str(vessel_id),
                    "[]",
                    "[]",
                    fixed_now,
                    "[]",
                    0,
                    "Existing body",
                    idempotency_key,
                ],
            )

        with patch("apps.certs.services.notification_dispatcher.timezone.now", return_value=fixed_now):
            with patch.object(dispatcher, "_idempotency_exists", return_value=False):
                result = dispatcher.dispatch(
                    trigger_event="cert_expiring_7d",
                    cert_row_id=cert_id,
                    vessel_id=vessel_id,
                    recipients=[CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office")],
                    title="Certificate expires in 7 days",
                    message="Renew IOPP for KSM Fortitude.",
                    idempotency_scope="race-7d",
                )

        self.assertEqual(result.notification_rows, [])
        self.assertEqual(relay.calls, [])
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM master_notification")
            self.assertEqual(cursor.fetchone()[0], 1)
            cursor.execute("SELECT COUNT(*) FROM vims_certs_notification_meta")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_email_failure_records_retry_ladder_then_critical_slack_dm_exception(self) -> None:
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher()
        result = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=uuid.uuid4(),
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="master-1", role="Master", side="vessel")],
            title="Certificate expires in 7 days",
            message="Renew IOPP for KSM Fortitude.",
            payload={"daysToGo": 7},
            idempotency_scope="critical-bounce",
        )
        notification_id = result.meta_rows[0]["notification_id"]
        service = CertEmailDeliveryService(slack_relay=relay)

        first = service.record_email_failure(
            notification_id=notification_id,
            recipient_id="master-1",
            error="SMTP temporary failure",
        )
        second = service.record_email_failure(
            notification_id=notification_id,
            recipient_id="master-1",
            error="SMTP temporary failure",
        )
        third = service.record_email_failure(
            notification_id=notification_id,
            recipient_id="master-1",
            error="SMTP hard bounce",
        )

        self.assertEqual(EMAIL_RETRY_BACKOFF_MINUTES, (1, 5, 30))
        self.assertEqual(first["email"]["status"], "retry_scheduled")
        self.assertEqual(first["email"]["nextRetryInMinutes"], 1)
        self.assertEqual(second["email"]["nextRetryInMinutes"], 5)
        self.assertEqual(third["email"]["status"], "bouncing")
        self.assertEqual(third["email"]["retryCount"], 3)
        self.assertEqual(third["slackDmFallback"]["status"], "delivered")
        self.assertTrue(third["slackDmFallback"]["criticalBounceException"])
        self.assertEqual(len(relay.direct_messages), 1)
        self.assertEqual(relay.direct_messages[0]["user_id"], "master-1")
        self.assertEqual(relay.direct_messages[0]["payload"]["criticalBounceException"], True)

        delivery = json.loads(self._delivery_status_for_recipient("master-1"))[0]["channels"]
        email_channel = next(channel for channel in delivery if channel["channel"] == "email")
        slack_dm_channel = next(channel for channel in delivery if channel["channel"] == "slack_dm")
        self.assertEqual(email_channel["status"], "bouncing")
        self.assertEqual(len(email_channel["attempts"]), 3)
        self.assertEqual(slack_dm_channel["providerMessageId"], "dm-123")
        self.assertTrue(slack_dm_channel["criticalBounceException"])

    def test_noncritical_bounced_email_does_not_use_slack_dm_exception(self) -> None:
        relay = RecordingSlackRelay()
        dispatcher = CertNotificationDispatcher()
        result = dispatcher.dispatch(
            trigger_event="cert_expiring_30d",
            cert_row_id=uuid.uuid4(),
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="master-1", role="Master", side="vessel")],
            title="Certificate expires in 30 days",
            message="Renew IOPP for KSM Fortitude.",
            payload={"daysToGo": 30},
            idempotency_scope="noncritical-bounce",
        )
        service = CertEmailDeliveryService(slack_relay=relay)
        for error in ("temporary failure", "temporary failure", "hard bounce"):
            final_result = service.record_email_failure(
                notification_id=result.meta_rows[0]["notification_id"],
                recipient_id="master-1",
                error=error,
            )

        self.assertEqual(final_result["email"]["status"], "bouncing")
        self.assertIsNone(final_result.get("slackDmFallback"))
        self.assertEqual(relay.direct_messages, [])
        delivery = json.loads(self._delivery_status_for_recipient("master-1"))[0]["channels"]
        self.assertEqual([channel["channel"] for channel in delivery], ["in_app", "email"])

    def test_day_7_critical_no_ack_escalation_adds_fleet_manager(self) -> None:
        recipients = build_expiry_escalation_recipients(
            base_recipients=[
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
                CertNotificationRecipient(user_id="tm-1", role="Technical Manager", side="office"),
                CertNotificationRecipient(user_id="master-1", role="Master", side="vessel"),
            ],
            fleet_manager_user_id="fm-1",
            days_to_expiry=7,
            critical=True,
            ack_missing=True,
        )

        self.assertIn(
            CertNotificationRecipient(user_id="fm-1", role="Fleet Manager", side="office"),
            recipients,
        )

    def test_day_14_or_noncritical_escalation_does_not_add_fleet_manager(self) -> None:
        recipients = build_expiry_escalation_recipients(
            base_recipients=[CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office")],
            fleet_manager_user_id="fm-1",
            days_to_expiry=14,
            critical=True,
            ack_missing=True,
        )

        self.assertNotIn(
            CertNotificationRecipient(user_id="fm-1", role="Fleet Manager", side="office"),
            recipients,
        )

    def test_notification_inbox_filters_to_authenticated_certs_recipient(self) -> None:
        dispatcher = CertNotificationDispatcher()
        visible_id = uuid.uuid4()
        hidden_id = uuid.uuid4()
        dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=visible_id,
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office")],
            title="Visible cert alert",
            message="Visible message",
            idempotency_scope="visible",
        )
        dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=hidden_id,
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="tm-1", role="Technical Manager", side="office")],
            title="Hidden cert alert",
            message="Hidden message",
            idempotency_scope="hidden",
        )

        request = APIRequestFactory().get("/api/certs/notifications/?module=certs")
        force_authenticate(
            request,
            user=make_user(role="DPA", form_ids=["CERT_F_002"], process_ids=[]),
        )

        response = CertNotificationListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["total_count"], 1)
        self.assertEqual(response.data["data"][0]["title"], "Visible cert alert")
        self.assertEqual(response.data["data"][0]["triggerEvent"], "cert_expiring_7d")
        self.assertEqual(response.data["data"][0]["channels"][0]["channels"], ["in_app", "slack"])

    def test_magic_link_ack_marks_notification_once_without_jwt_auth(self) -> None:
        cert_id = uuid.uuid4()
        dispatcher = CertNotificationDispatcher()
        result = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=cert_id,
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="master-1", role="Master", side="vessel")],
            title="Magic-link cert alert",
            message="Renew the cert.",
            payload={"returnPath": f"/certs/vessels/9876543/cert/{cert_id}"},
            idempotency_scope="magic-link",
        )
        notification_id = result.meta_rows[0]["notification_id"]
        token = build_magic_link_token(notification_id=notification_id, recipient_id="master-1")

        request = APIRequestFactory().get(f"/api/certs/notifications/ack/{token}/")
        response = CertNotificationMagicAckView.as_view()(request, token=token)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn(f"/certs/vessels/9876543/cert/{cert_id}", response["Location"])
        self.assertIn("ack=success", response["Location"])

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ack_user_id, ack_channel, ack_at
                FROM vims_certs_notification_meta
                WHERE notification_id = %s
                """,
                [notification_id],
            )
            ack_user_id, ack_channel, ack_at = cursor.fetchone()

        self.assertEqual(ack_user_id, "master-1")
        self.assertEqual(ack_channel, "magic_link")
        self.assertIsNotNone(ack_at)

        replay_request = APIRequestFactory().get(f"/api/certs/notifications/ack/{token}/")
        replay_response = CertNotificationMagicAckView.as_view()(replay_request, token=token)

        self.assertEqual(replay_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(replay_response.data["error"], "MAGIC_LINK_ALREADY_USED")

    def test_magic_link_token_cannot_ack_a_different_notification_or_recipient(self) -> None:
        dispatcher = CertNotificationDispatcher()
        first = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=uuid.uuid4(),
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="master-1", role="Master", side="vessel")],
            title="First alert",
            message="First body.",
            idempotency_scope="magic-link-first",
        )
        second = dispatcher.dispatch(
            trigger_event="cert_expiring_7d",
            cert_row_id=uuid.uuid4(),
            vessel_id=uuid.uuid4(),
            recipients=[CertNotificationRecipient(user_id="master-2", role="Master", side="vessel")],
            title="Second alert",
            message="Second body.",
            idempotency_scope="magic-link-second",
        )
        first_id = first.meta_rows[0]["notification_id"]
        second_id = second.meta_rows[0]["notification_id"]
        token = build_magic_link_token(notification_id=first_id, recipient_id="master-1")

        response = CertNotificationMagicAckView.as_view()(
            APIRequestFactory().get(f"/api/certs/notifications/ack/{token}/"),
            token=token,
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT notification_id, ack_user_id, ack_channel
                FROM vims_certs_notification_meta
                WHERE notification_id IN (%s, %s)
                ORDER BY notification_id
                """,
                [first_id, second_id],
            )
            rows = {row[0]: row[1:] for row in cursor.fetchall()}

        self.assertEqual(rows[first_id], ("master-1", "magic_link"))
        self.assertEqual(rows[second_id], (None, None))

        wrong_recipient_token = build_magic_link_token(notification_id=second_id, recipient_id="master-1")
        wrong_recipient_response = CertNotificationMagicAckView.as_view()(
            APIRequestFactory().get(f"/api/certs/notifications/ack/{wrong_recipient_token}/"),
            token=wrong_recipient_token,
        )
        self.assertEqual(wrong_recipient_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wrong_recipient_response.data["error"], "MAGIC_LINK_INVALID")

    def test_magic_link_ack_rejects_expired_token(self) -> None:
        token = build_magic_link_token(notification_id=str(uuid.uuid4()), recipient_id="master-1")
        request = APIRequestFactory().get(f"/api/certs/notifications/ack/{token}/")

        with patch(
            "apps.certs.views.notification_views.verify_magic_link_token",
            side_effect=MagicLinkExpired("expired"),
        ):
            response = CertNotificationMagicAckView.as_view()(request, token=token)

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data["error"], "MAGIC_LINK_EXPIRED")

    def _delivery_status_for_recipient(self, recipient_ref: str) -> str:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT meta.delivery_status_json
                FROM master_notification mn
                JOIN vims_certs_notification_meta meta ON meta.master_notification_id = mn.id
                WHERE mn.recipient_ref = %s
                """,
                [recipient_ref],
            )
            return cursor.fetchone()[0]
