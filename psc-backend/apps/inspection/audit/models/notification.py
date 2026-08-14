"""Audit notification delivery schema model for Phase 1 Step 1.1."""

from django.db import models

from .base import AuditCreatedMixin


class NotificationDeliveryLog(AuditCreatedMixin):
    psc_notification_id = models.CharField(max_length=32)
    channel = models.CharField(max_length=20)
    recipient_address = models.CharField(max_length=254, null=True, blank=True)
    status = models.CharField(max_length=30, default="PENDING")
    attempt_count = models.IntegerField(default=0)
    first_attempted_at = models.DateTimeField(null=True, blank=True)
    last_attempted_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    resolved_offline_reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "notification_delivery_log"
