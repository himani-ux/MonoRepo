"""
Notification serializers per BACKEND_STRUCTURE.md Section 10.11.

Implements: PRD.md FEAT-NOTIF-001
"""

from rest_framework import serializers
from .models import Notification


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for notification list response.

    Per BACKEND_STRUCTURE.md Section 10.11 GET /api/psc/notifications/
    """

    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient_type',
            'recipient_id',
            'vessel_id',
            'notification_type',
            'title',
            'message',
            'entity_type',
            'entity_id',
            'is_read',
            'read_at',
            'created_date',
        ]
        read_only_fields = fields


class MarkReadSerializer(serializers.Serializer):
    """
    Serializer for mark-read request.

    Per BACKEND_STRUCTURE.md Section 10.11 POST /api/psc/notifications/mark-read/
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
    )
