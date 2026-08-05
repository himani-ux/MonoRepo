import uuid
from unittest.mock import patch

from django.test import TestCase

from apps.notifications.models import Notification
from apps.safety.services.notification_writer import NotificationWriter


class SafetyNotificationWriterTests(TestCase):
    def test_vessel_recipient_creates_notification_for_vessel_master(self):
        vessel_id = str(uuid.uuid4())
        record_id = str(uuid.uuid4())

        with patch(
            "apps.safety.services.notification_writer._get_vessel_master_crew_ids",
            return_value=["KSM0001"],
        ):
            rows = NotificationWriter().write_notification(
                record_id=record_id,
                recipients=[vessel_id],
                kind="NEAR_MISS_FLEET_ALERT",
                title="Fleet alert",
                message="Review equivalent controls.",
                payload={"vessel_id": vessel_id, "near_miss_id": record_id},
            )

        self.assertEqual(len(rows), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.recipient_type, "CREW")
        self.assertEqual(notification.recipient_id, "KSM0001")
        self.assertEqual(str(notification.vessel_id), vessel_id)
        self.assertEqual(notification.notification_type, "NEAR_MISS_FLEET_ALERT")
        self.assertEqual(notification.entity_type, "SAFETY_NEAR_MISS")

    def test_office_role_recipient_creates_notification_for_resolved_office_user(self):
        record_id = str(uuid.uuid4())

        with patch(
            "apps.safety.services.notification_writer._get_office_user_ids_for_roles",
            return_value=["EMP001"],
        ):
            rows = NotificationWriter().write_notification(
                record_id=record_id,
                recipients=["DPA"],
                kind="NEAR_MISS_READY_FOR_OFFICE_COMMENTS",
                title="Near miss ready",
                message="Near miss completed vessel review.",
                payload={"near_miss_id": record_id},
            )

        self.assertEqual(len(rows), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.recipient_type, "OFFICE")
        self.assertEqual(notification.recipient_id, "EMP001")
        self.assertEqual(notification.notification_type, "NEAR_MISS_READY_FOR_OFFICE_COMMENTS")
        self.assertEqual(notification.entity_type, "SAFETY_NEAR_MISS")
