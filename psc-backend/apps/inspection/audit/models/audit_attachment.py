"""Audit attachment and PDF provenance schema models for Phase 1 Step 1.1."""

from django.db import models
from django.utils import timezone

from .base import AuditActiveManager, AuditUuidPrimaryKeyMixin


class AuditAttachment(AuditUuidPrimaryKeyMixin):
    audit_detail_id = models.UUIDField()
    audit_finding_id = models.UUIDField(null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100)
    category = models.CharField(max_length=40)
    attachment_version = models.CharField(max_length=20, default="FINAL")
    attestation_required = models.BooleanField(default=False)
    attestation_note = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    linked_pdf_generation_id = models.UUIDField(null=True, blank=True)
    pdf_hash_validation_status = models.CharField(max_length=30, null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    validator_message = models.CharField(max_length=500, null=True, blank=True)
    uploaded_by = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)
    objects = AuditActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "audit_attachment"


class AuditPdfGeneration(AuditUuidPrimaryKeyMixin):
    audit_detail_id = models.UUIDField()
    audit_finding_id = models.UUIDField(null=True, blank=True)
    pdf_kind = models.CharField(max_length=40)
    pdf_version = models.IntegerField(default=1)
    content_hash = models.CharField(max_length=64)
    qr_payload = models.TextField(null=True, blank=True)
    is_superseded = models.BooleanField(default=False)
    generated_by = models.CharField(max_length=100)
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "audit_pdf_generation"
