"""External-audit cross-module schema models for Phase 1 Step 1.1."""

from django.db import models
from django.utils import timezone

from .base import AuditUuidPrimaryKeyMixin


class CertWritebackOutbox(AuditUuidPrimaryKeyMixin):
    audit_detail_id = models.UUIDField()
    vessel_cert_id = models.UUIDField()
    writeback_payload = models.TextField()
    expected_cert_version = models.IntegerField()
    status = models.CharField(max_length=30, default="QUEUED")
    attempt_count = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
    dead_lettered_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cert_writeback_outbox"


class FlagStateNotificationLog(AuditUuidPrimaryKeyMixin):
    audit_detail_id = models.UUIDField()
    notified_at = models.DateTimeField(null=True, blank=True)
    notified_to = models.CharField(max_length=200, null=True, blank=True)
    ack_received_at = models.DateTimeField(null=True, blank=True)
    notification_ref = models.CharField(max_length=200, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "flag_state_notification_log"
