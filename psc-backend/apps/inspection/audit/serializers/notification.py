"""Serializers for Audit notification delivery queues."""

from __future__ import annotations

import uuid

from rest_framework import serializers

from apps.inspection.audit.models import NotificationDeliveryLog
from apps.notifications.models import Notification


OFFLINE_REASON_MIN_LENGTH = 30


class AuditNotificationOfflineSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=OFFLINE_REASON_MIN_LENGTH)


class AuditNotificationDeliverySerializer(serializers.Serializer):
    def to_representation(self, instance: NotificationDeliveryLog):
        notification = _get_notification(instance)
        return {
            "id": str(instance.id),
            "psc_notification_id": instance.psc_notification_id,
            "notification_type": notification.notification_type if notification else None,
            "title": notification.title if notification else None,
            "message": notification.message if notification else None,
            "entity_type": notification.entity_type if notification else None,
            "entity_id": str(notification.entity_id) if notification and notification.entity_id else None,
            "vessel_id": str(notification.vessel_id) if notification and notification.vessel_id else None,
            "recipient_type": notification.recipient_type if notification else None,
            "recipient_id": notification.recipient_id if notification else None,
            "channel": instance.channel,
            "recipient_address": instance.recipient_address,
            "status": instance.status,
            "attempt_count": instance.attempt_count,
            "first_attempted_at": instance.first_attempted_at.isoformat() if instance.first_attempted_at else None,
            "last_attempted_at": instance.last_attempted_at.isoformat() if instance.last_attempted_at else None,
            "last_error": instance.last_error,
            "sent_at": instance.sent_at.isoformat() if instance.sent_at else None,
            "resolved_offline_reason": instance.resolved_offline_reason,
            "created_date": instance.created_date.isoformat() if instance.created_date else None,
        }


def _get_notification(delivery_log: NotificationDeliveryLog) -> Notification | None:
    try:
        notification_id = uuid.UUID(hex=str(delivery_log.psc_notification_id).replace("-", ""))
    except (TypeError, ValueError):
        return None
    return Notification.objects.filter(id=notification_id).first()


__all__ = [
    "AuditNotificationDeliverySerializer",
    "AuditNotificationOfflineSerializer",
    "OFFLINE_REASON_MIN_LENGTH",
]
