from __future__ import annotations

import os
import unittest
import uuid
from datetime import date

import django
from django.apps import apps
from django.db import connection, transaction


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-notification-test-secret-key-1234567890",
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

from apps.inspection.audit.models import (  # noqa: E402
    MasterAuditPlan,
    MasterHodAssignment,
    MasterSlackChannel,
    NotificationDeliveryLog,
)
from apps.inspection.audit.services.notification_dispatcher import (  # noqa: E402
    SUPPORTED_AUDIT_NOTIFICATION_TYPES,
    AuditNotificationRecipient,
    dispatch_audit_notification,
)
from apps.notifications.models import Notification  # noqa: E402


SCHEMA_MODELS = [
    Notification,
    NotificationDeliveryLog,
    MasterAuditPlan,
    MasterHodAssignment,
    MasterSlackChannel,
]


class AuditNotificationDispatcherTests(unittest.TestCase):
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
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS "VesselData"')
            cursor.execute(
                """
                CREATE TABLE "VesselData" (
                    id char(36) PRIMARY KEY,
                    vesselName varchar(255) NULL,
                    vesselCode varchar(50) NULL,
                    Email varchar(254) NULL,
                    is_active bool DEFAULT 1,
                    is_deleted bool DEFAULT 0
                )
                """
            )

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS "VesselData"')
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f'DELETE FROM "{model._meta.db_table}"')
            cursor.execute('DELETE FROM "VesselData"')
        self.vessel_id = uuid.uuid4()

    def _insert_vessel_email(self, email: str | None) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO "VesselData" (id, vesselName, vesselCode, Email, is_active, is_deleted)
                VALUES (%s, %s, %s, %s, 1, 0)
                """,
                [str(self.vessel_id), "MV Test", "MVT", email],
            )

    def _plan(self, **overrides) -> MasterAuditPlan:
        data = {
            "target_vessel_id": self.vessel_id,
            "audit_classification": "INTERNAL",
            "audit_standards_csv": "ISM",
            "planned_window_start": date(2026, 8, 1),
            "planned_window_end": date(2026, 12, 1),
            "status": "CONFIRMED",
            "created_by": "test",
        }
        data.update(overrides)
        return MasterAuditPlan.objects.create(**data)

    def test_audit_scheduled_fans_out_to_in_system_email_and_slack_logs(self) -> None:
        self._insert_vessel_email("master@example.test")
        plan = self._plan()
        MasterSlackChannel.objects.create(
            channel_name="#audit-mvt",
            webhook_url="https://hooks.slack.test/audit",
            scope_type="VESSEL",
            scope_value=str(self.vessel_id),
            notification_types_csv="AUDIT_SCHEDULED,AUDIT_CANCELLED",
            created_by="test",
        )

        result = dispatch_audit_notification(
            notification_type="AUDIT_SCHEDULED",
            title="Audit scheduled",
            message="Internal audit has been scheduled.",
            entity_type="AUDIT_PLAN",
            entity_id=plan.id,
            vessel_id=self.vessel_id,
            recipients=[
                AuditNotificationRecipient(
                    recipient_type="CREW",
                    recipient_id="MASTER001",
                )
            ],
        )

        self.assertEqual(len(result.notifications), 1)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, "AUDIT_SCHEDULED")
        self.assertEqual(notification.recipient_type, "CREW")
        self.assertEqual(notification.recipient_id, "MASTER001")

        logs = list(NotificationDeliveryLog.objects.order_by("channel"))
        self.assertEqual([log.channel for log in logs], ["EMAIL", "IN_SYSTEM", "SLACK"])
        by_channel = {log.channel: log for log in logs}
        self.assertEqual(by_channel["IN_SYSTEM"].status, "SENT")
        self.assertEqual(by_channel["IN_SYSTEM"].attempt_count, 1)
        self.assertEqual(by_channel["EMAIL"].status, "QUEUED")
        self.assertEqual(by_channel["EMAIL"].recipient_address, "master@example.test")
        self.assertEqual(by_channel["SLACK"].status, "QUEUED")
        self.assertEqual(by_channel["SLACK"].recipient_address, "#audit-mvt")
        self.assertEqual(by_channel["IN_SYSTEM"].psc_notification_id, notification.id.hex)

    def test_supported_type_set_is_the_fixed_v1_vocabulary(self) -> None:
        self.assertEqual(
            SUPPORTED_AUDIT_NOTIFICATION_TYPES,
            (
                "AUDIT_SCHEDULED",
                "AUDIT_NC_RAISED",
                "AUDIT_CANCELLED",
                "AUDIT_OVERDUE",
                "AUDIT_CRITICAL_OVERDUE",
                "AUDIT_EXTENSION_APPROVED",
                "NC_EFFECTIVENESS_REVIEW_DUE",
            ),
        )

        with self.assertRaises(ValueError):
            dispatch_audit_notification(
                notification_type="AUDIT_DUE_T30",
                title="Not a v1 notification",
                message="Internal alert-ladder events are not all dispatch notification types.",
                entity_type="AUDIT_PLAN",
                entity_id=uuid.uuid4(),
                recipients=[AuditNotificationRecipient(recipient_type="OFFICE", recipient_id="DPA001")],
            )

    def test_null_vessel_email_creates_failed_permanent_delivery_without_rollback(self) -> None:
        self._insert_vessel_email(None)
        plan = self._plan()

        result = dispatch_audit_notification(
            notification_type="AUDIT_SCHEDULED",
            title="Audit scheduled",
            message="Internal audit has been scheduled.",
            entity_type="AUDIT_PLAN",
            entity_id=plan.id,
            vessel_id=self.vessel_id,
            recipients=[
                AuditNotificationRecipient(
                    recipient_type="CREW",
                    recipient_id="MASTER001",
                )
            ],
            include_slack=False,
        )

        self.assertEqual(len(result.notifications), 1)
        self.assertEqual(Notification.objects.count(), 1)
        email_log = NotificationDeliveryLog.objects.get(channel="EMAIL")
        self.assertEqual(email_log.status, "FAILED_PERMANENT")
        self.assertEqual(email_log.last_error, "CMS_NO_EMAIL_ON_FILE")

    def test_office_audit_resolves_hod_assignment_and_skips_slack(self) -> None:
        MasterHodAssignment.objects.create(
            dept="TECH",
            user_id="HOD-ACTING",
            is_acting=True,
            effective_from=date(2026, 1, 1),
            created_by="test",
        )
        MasterHodAssignment.objects.create(
            dept="TECH",
            user_id="HOD-CONFIRMED",
            is_acting=False,
            effective_from=date(2026, 1, 2),
            created_by="test",
        )

        result = dispatch_audit_notification(
            notification_type="AUDIT_SCHEDULED",
            title="Office audit scheduled",
            message="Internal office audit has been scheduled.",
            entity_type="AUDIT_PLAN",
            entity_id=uuid.uuid4(),
            office_dept="TECH",
            include_email=False,
        )

        self.assertEqual([item.recipient_id for item in result.recipients], ["HOD-CONFIRMED"])
        self.assertEqual(Notification.objects.get().recipient_id, "HOD-CONFIRMED")
        self.assertEqual(
            set(NotificationDeliveryLog.objects.values_list("channel", flat=True)),
            {"IN_SYSTEM"},
        )

    def test_in_system_source_of_truth_rolls_back_with_caller_transaction(self) -> None:
        self._insert_vessel_email("master@example.test")
        plan = self._plan()

        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                dispatch_audit_notification(
                    notification_type="AUDIT_CANCELLED",
                    title="Audit cancelled",
                    message="Internal audit plan was cancelled.",
                    entity_type="AUDIT_PLAN",
                    entity_id=plan.id,
                    vessel_id=self.vessel_id,
                    recipients=[
                        AuditNotificationRecipient(
                            recipient_type="CREW",
                            recipient_id="MASTER001",
                        )
                    ],
                    include_slack=False,
                )
                raise RuntimeError("caller audit state change failed")

        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(NotificationDeliveryLog.objects.count(), 0)


if __name__ == "__main__":
    unittest.main()
