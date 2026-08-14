from __future__ import annotations

import os
import unittest
import uuid
from types import SimpleNamespace

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-notification-queue-test-secret-key-1234567890",
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
            ROOT_URLCONF="core.urls",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.accounts.models import RoleCodes  # noqa: E402
from apps.inspection.audit.models import NotificationDeliveryLog  # noqa: E402
from apps.inspection.audit.permissions import AUDIT_P_001  # noqa: E402
from apps.inspection.audit.views import (  # noqa: E402
    AuditFailedNotificationListView,
    AuditNotificationOfflineResolveView,
    AuditNotificationRetryView,
)
from apps.notifications.models import Notification  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Notification,
    NotificationDeliveryLog,
]


def make_user(
    *,
    role: str = "DPA",
    user_type: str = "OFFICE",
    user_id: str = "dpa-1",
    process_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        display_name="DPA User",
        username=user_id,
        is_authenticated=True,
    )


class AuditNotificationQueueApiTests(unittest.TestCase):
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
        self.factory = APIRequestFactory()

    def _notification(self, **overrides) -> Notification:
        data = {
            "recipient_type": "CREW",
            "recipient_id": "MASTER001",
            "vessel_id": uuid.uuid4(),
            "notification_type": "AUDIT_OVERDUE",
            "title": "Audit overdue",
            "message": "Internal audit is overdue.",
            "entity_type": "AUDIT_PLAN",
            "entity_id": uuid.uuid4(),
        }
        data.update(overrides)
        return Notification.objects.create(**data)

    def _delivery(self, notification: Notification, *, channel: str = "EMAIL", **overrides) -> NotificationDeliveryLog:
        data = {
            "psc_notification_id": notification.id.hex,
            "channel": channel,
            "recipient_address": "audit@example.test" if channel == "EMAIL" else "#audit-mvt",
            "status": "FAILED_PERMANENT",
            "attempt_count": 3,
            "last_error": "CMS_NO_EMAIL_ON_FILE",
            "created_by": "test",
        }
        data.update(overrides)
        return NotificationDeliveryLog.objects.create(**data)

    def _list_failed(self, user):
        request = self.factory.get("/api/audit/dpa/notifications/failed/")
        force_authenticate(request, user=user)
        return AuditFailedNotificationListView.as_view()(request)

    def _retry(self, delivery_id, user):
        request = self.factory.post(f"/api/audit/notifications/{delivery_id}/retry/", {}, format="json")
        force_authenticate(request, user=user)
        return AuditNotificationRetryView.as_view()(request, id=delivery_id)

    def _offline(self, delivery_id, payload, user):
        request = self.factory.post(f"/api/audit/notifications/{delivery_id}/offline/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditNotificationOfflineResolveView.as_view()(request, id=delivery_id)

    def test_failed_notification_list_filters_failed_permanent_rows_for_dpa(self) -> None:
        dpa_user = make_user(process_ids=[AUDIT_P_001])
        failed = self._delivery(self._notification(), last_error="webhook 404")
        self._delivery(self._notification(notification_type="AUDIT_SCHEDULED"), status="SENT", last_error=None)

        response = self._list_failed(dpa_user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["count"], 1)
        row = response.data["data"]["results"][0]
        self.assertEqual(row["id"], str(failed.id))
        self.assertEqual(row["notification_type"], "AUDIT_OVERDUE")
        self.assertEqual(row["channel"], "EMAIL")
        self.assertEqual(row["last_error"], "webhook 404")
        self.assertEqual(row["status"], "FAILED_PERMANENT")

    def test_failed_notification_queue_is_dpa_only(self) -> None:
        seq_user = make_user(role=RoleCodes.OFFICE_SSQE, user_id="seq-1", process_ids=[AUDIT_P_001])
        vessel_user = make_user(role=RoleCodes.VESSEL_MASTER, user_type="VESSEL", user_id="master-1", process_ids=[AUDIT_P_001])

        seq_response = self._list_failed(seq_user)
        vessel_response = self._list_failed(vessel_user)

        self.assertEqual(seq_response.status_code, 403)
        self.assertEqual(vessel_response.status_code, 403)

    def test_manual_retry_requeues_failed_email_row_without_transport_send(self) -> None:
        dpa_user = make_user(process_ids=[AUDIT_P_001])
        delivery = self._delivery(self._notification(), channel="EMAIL")

        response = self._retry(delivery.id, dpa_user)

        self.assertEqual(response.status_code, 200)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "QUEUED")
        self.assertEqual(delivery.attempt_count, 0)
        self.assertIsNone(delivery.last_error)
        self.assertIsNone(delivery.sent_at)
        self.assertIsNone(delivery.resolved_offline_reason)

    def test_manual_retry_rejects_non_transport_channel(self) -> None:
        dpa_user = make_user(process_ids=[AUDIT_P_001])
        delivery = self._delivery(self._notification(), channel="IN_SYSTEM")

        response = self._retry(delivery.id, dpa_user)

        self.assertEqual(response.status_code, 400)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "FAILED_PERMANENT")

    def test_offline_resolution_requires_reason_minimum(self) -> None:
        dpa_user = make_user(process_ids=[AUDIT_P_001])
        delivery = self._delivery(self._notification(), channel="SLACK")

        response = self._offline(delivery.id, {"reason": "too short"}, dpa_user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("reason", response.data)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "FAILED_PERMANENT")

    def test_offline_resolution_marks_row_resolved_with_reason(self) -> None:
        dpa_user = make_user(process_ids=[AUDIT_P_001])
        delivery = self._delivery(self._notification(), channel="SLACK", last_error="SLACK_WEBHOOK_HTTP_404")
        reason = "DPA confirmed the Master was notified by direct phone and email."

        response = self._offline(delivery.id, {"reason": reason}, dpa_user)

        self.assertEqual(response.status_code, 200)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "RESOLVED_OFFLINE")
        self.assertEqual(delivery.resolved_offline_reason, reason)
        self.assertIn("resolved offline", response.data["message"].lower())


if __name__ == "__main__":
    unittest.main()
