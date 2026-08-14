from __future__ import annotations

import os
import unittest
import uuid
from datetime import timedelta
from types import SimpleNamespace

import django
from django.apps import apps
from django.db import connection
from django.utils import timezone


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-notification-relay-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "apps.accounts",
                "apps.masters",
                "apps.inspection",
                "apps.car",
                "apps.notifications",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            DEFAULT_FROM_EMAIL="KSM Marine <audit@example.test>",
            EMAIL_TIMEOUT=2,
            ROOT_URLCONF="core.urls",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.inspection.audit.jobs.notification_retry import run_notification_retry  # noqa: E402
from apps.inspection.audit.models import MasterSlackChannel, NotificationDeliveryLog  # noqa: E402
from apps.inspection.audit.services.email_relay import AuditEmailRelay  # noqa: E402
from apps.inspection.audit.services.slack_relay import AuditSlackRelay  # noqa: E402
from apps.notifications.models import Notification  # noqa: E402


SCHEMA_MODELS = [
    Notification,
    NotificationDeliveryLog,
    MasterSlackChannel,
]


class FakeEmailMessage:
    sent_messages: list[dict[str, object]] = []
    send_error: Exception | None = None
    send_count: int = 1

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        FakeEmailMessage.sent_messages.append(kwargs)

    def send(self, *, fail_silently: bool = False) -> int:
        if FakeEmailMessage.send_error:
            raise FakeEmailMessage.send_error
        return FakeEmailMessage.send_count


class AuditNotificationRelayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            existing_tables = set(connection.introspection.table_names())
            for model in reversed(SCHEMA_MODELS):
                if model._meta.db_table in existing_tables:
                    schema_editor.delete_model(model)
            for model in SCHEMA_MODELS:
                schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f'DELETE FROM "{model._meta.db_table}"')
        FakeEmailMessage.sent_messages = []
        FakeEmailMessage.send_error = None
        FakeEmailMessage.send_count = 1
        self.vessel_id = uuid.uuid4()
        self.now = timezone.now()

    def _notification(self, *, vessel: bool = True) -> Notification:
        return Notification.objects.create(
            recipient_type="CREW" if vessel else "OFFICE",
            recipient_id="MASTER001" if vessel else "HOD001",
            vessel_id=self.vessel_id if vessel else None,
            notification_type="AUDIT_SCHEDULED",
            title="Audit scheduled",
            message="Internal audit has been scheduled.",
            entity_type="AUDIT_PLAN",
            entity_id=uuid.uuid4(),
        )

    def _delivery(self, notification: Notification, *, channel: str, **overrides) -> NotificationDeliveryLog:
        data = {
            "psc_notification_id": notification.id.hex,
            "channel": channel,
            "recipient_address": "audit@example.test" if channel == "EMAIL" else "#audit-mvt",
            "status": "QUEUED",
            "attempt_count": 0,
            "created_by": "test",
        }
        data.update(overrides)
        return NotificationDeliveryLog.objects.create(**data)

    def _email_relay(self) -> AuditEmailRelay:
        return AuditEmailRelay(
            email_message_class=FakeEmailMessage,
            connection_factory=lambda **kwargs: object(),
            now_fn=lambda: self.now,
        )

    def test_queued_email_success_marks_sent_without_real_smtp(self) -> None:
        notification = self._notification()
        delivery = self._delivery(notification, channel="EMAIL")

        result = self._email_relay().process_due(now=self.now)

        delivery.refresh_from_db()
        self.assertEqual(result.sent, 1)
        self.assertEqual(delivery.status, "SENT")
        self.assertEqual(delivery.attempt_count, 1)
        self.assertEqual(delivery.sent_at, self.now)
        self.assertEqual(FakeEmailMessage.sent_messages[0]["to"], ["audit@example.test"])

    def test_email_transient_failure_retries_then_third_attempt_fails_permanent(self) -> None:
        notification = self._notification()
        first = self._delivery(notification, channel="EMAIL")
        third = self._delivery(notification, channel="EMAIL", status="RETRYING", attempt_count=2)
        FakeEmailMessage.send_error = RuntimeError("smtp timeout")

        result = self._email_relay().process_due(now=self.now)

        first.refresh_from_db()
        third.refresh_from_db()
        self.assertEqual(result.retrying, 1)
        self.assertEqual(result.failed_permanent, 1)
        self.assertEqual(first.status, "RETRYING")
        self.assertEqual(first.attempt_count, 1)
        self.assertEqual(third.status, "FAILED_PERMANENT")
        self.assertEqual(third.attempt_count, 3)
        self.assertEqual(first.last_error, "smtp timeout")

    def test_email_bounce_marks_delivery_bounced(self) -> None:
        notification = self._notification()
        delivery = self._delivery(notification, channel="EMAIL", status="SENT", attempt_count=1)

        result = self._email_relay().mark_bounced(
            delivery_log_id=delivery.id,
            reason="mailbox rejected",
            now=self.now,
        )

        delivery.refresh_from_db()
        self.assertEqual(result.bounced, 1)
        self.assertEqual(delivery.status, "BOUNCED")
        self.assertEqual(delivery.last_error, "mailbox rejected")

    def test_slack_webhook_success_marks_sent_without_real_network(self) -> None:
        notification = self._notification()
        delivery = self._delivery(notification, channel="SLACK")
        MasterSlackChannel.objects.create(
            channel_name="#audit-mvt",
            webhook_url="https://hooks.slack.test/audit",
            scope_type="VESSEL",
            scope_value=str(self.vessel_id),
            notification_types_csv="AUDIT_SCHEDULED",
            created_by="test",
        )
        calls: list[dict[str, object]] = []

        def fake_post(url, **kwargs):
            calls.append({"url": url, **kwargs})
            return SimpleNamespace(status_code=200)

        result = AuditSlackRelay(http_post=fake_post, now_fn=lambda: self.now).process_due(now=self.now)

        delivery.refresh_from_db()
        self.assertEqual(result.sent, 1)
        self.assertEqual(delivery.status, "SENT")
        self.assertEqual(delivery.attempt_count, 1)
        self.assertEqual(calls[0]["url"], "https://hooks.slack.test/audit")
        self.assertIn("blocks", calls[0]["json"])

    def test_slack_transient_failure_retries_then_third_attempt_fails_permanent(self) -> None:
        notification = self._notification()
        first = self._delivery(notification, channel="SLACK")
        third = self._delivery(notification, channel="SLACK", status="RETRYING", attempt_count=2)
        MasterSlackChannel.objects.create(
            channel_name="#audit-mvt",
            webhook_url="https://hooks.slack.test/audit",
            scope_type="VESSEL",
            scope_value=str(self.vessel_id),
            notification_types_csv="AUDIT_SCHEDULED",
            created_by="test",
        )

        def fake_post(url, **kwargs):
            return SimpleNamespace(status_code=500)

        result = AuditSlackRelay(http_post=fake_post, now_fn=lambda: self.now).process_due(now=self.now)

        first.refresh_from_db()
        third.refresh_from_db()
        self.assertEqual(result.retrying, 1)
        self.assertEqual(result.failed_permanent, 1)
        self.assertEqual(first.status, "RETRYING")
        self.assertEqual(first.attempt_count, 1)
        self.assertEqual(third.status, "FAILED_PERMANENT")
        self.assertEqual(third.attempt_count, 3)
        self.assertEqual(third.last_error, "SLACK_WEBHOOK_HTTP_500")

    def test_retry_job_skips_not_due_transport_rows(self) -> None:
        notification = self._notification()
        last_attempt = self.now - timedelta(milliseconds=500)
        self._delivery(
            notification,
            channel="EMAIL",
            status="RETRYING",
            attempt_count=1,
            last_attempted_at=last_attempt,
        )
        self._delivery(
            notification,
            channel="SLACK",
            status="RETRYING",
            attempt_count=1,
            last_attempted_at=last_attempt,
        )

        result = run_notification_retry(
            now=self.now,
            email_relay=self._email_relay(),
            slack_relay=AuditSlackRelay(http_post=lambda *args, **kwargs: SimpleNamespace(status_code=200)),
        )

        self.assertEqual(result.email.skipped_not_due, 1)
        self.assertEqual(result.slack.skipped_not_due, 1)
        self.assertEqual(NotificationDeliveryLog.objects.filter(status="RETRYING").count(), 2)

    def test_slack_missing_configuration_fails_permanent(self) -> None:
        notification = self._notification()
        delivery = self._delivery(notification, channel="SLACK")

        result = AuditSlackRelay(http_post=lambda *args, **kwargs: SimpleNamespace(status_code=200)).process_due(
            now=self.now
        )

        delivery.refresh_from_db()
        self.assertEqual(result.failed_permanent, 1)
        self.assertEqual(delivery.status, "FAILED_PERMANENT")
        self.assertEqual(delivery.last_error, "SLACK_CHANNEL_NOT_CONFIGURED")


if __name__ == "__main__":
    unittest.main()
