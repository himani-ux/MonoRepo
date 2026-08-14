"""Audit signature schema models for Phase 1 Step 1.1."""

from django.db import models
from django.utils import timezone

from .base import AuditCreatedMixin, AuditUuidPrimaryKeyMixin


class AuditFindingSignature(AuditUuidPrimaryKeyMixin):
    audit_finding_id = models.UUIDField()
    signer_user_id = models.CharField(max_length=100, null=True, blank=True)
    signature_event_type = models.CharField(max_length=40)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_pdf_attachment_id = models.UUIDField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_finding_signature"


class AuditFindingSignEvent(AuditCreatedMixin):
    audit_finding_id = models.UUIDField()
    user_id = models.CharField(max_length=100)
    rank_at_signing = models.CharField(max_length=60, null=True, blank=True)
    part_label = models.CharField(max_length=20)
    claimed_sign_datetime = models.DateTimeField(null=True, blank=True)
    actual_entered_at = models.DateTimeField(default=timezone.now)
    backdate_reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "audit_finding_sign_event"


class AuditSignature(AuditUuidPrimaryKeyMixin):
    audit_detail_id = models.UUIDField()
    lead_auditor_sign_at = models.DateTimeField(null=True, blank=True)
    master_sign_at = models.DateTimeField(null=True, blank=True)
    seq_manager_close_at = models.DateTimeField(null=True, blank=True)
    signature_image_path = models.CharField(max_length=500, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_signature"
