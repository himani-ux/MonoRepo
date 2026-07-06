from __future__ import annotations

from django.db import models

from .catalog import CatalogRow


class TrackedItem(models.Model):
    tracked_item_id = models.UUIDField(primary_key=True, editable=False)
    vessel_id = models.UUIDField()
    catalog = models.ForeignKey(CatalogRow, db_column="catalog_id", on_delete=models.DO_NOTHING)
    type = models.CharField(max_length=24)
    validity_type = models.CharField(max_length=16)
    form_variant = models.CharField(max_length=8, null=True, blank=True)
    cadence_months = models.SmallIntegerField(null=True, blank=True)
    cadence_custom_days = models.IntegerField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        db_column="parent_id",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="child_tracked_items",
    )
    relationship_type = models.CharField(max_length=32, null=True, blank=True)
    supersedes = models.ForeignKey(
        "self",
        db_column="supersedes_id",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="successor_tracked_items",
    )
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    anniversary_date = models.DateField(null=True, blank=True)
    window_open = models.DateField(null=True, blank=True)
    window_close = models.DateField(null=True, blank=True)
    last_done_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    postponed_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32)
    certificate_number = models.CharField(max_length=128, null=True, blank=True)
    issuing_authority = models.CharField(max_length=128)
    place_of_issue = models.CharField(max_length=128, null=True, blank=True)
    extension_authority = models.CharField(max_length=8, null=True, blank=True)
    extension_letter_pdf_id = models.UUIDField(null=True, blank=True)
    extension_reason = models.CharField(max_length=512, null=True, blank=True)
    pdf_attachment_id = models.UUIDField(null=True, blank=True)
    pdf_missing = models.BooleanField(default=False)
    source = models.CharField(max_length=16)
    last_class_sync_id = models.UUIDField(null=True, blank=True)
    approval_state = models.CharField(max_length=24)
    submitted_by = models.CharField(max_length=64, null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=64, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    rejection_count = models.SmallIntegerField(default=0)
    draft_expires_at = models.DateTimeField(null=True, blank=True)
    lifecycle_status = models.CharField(max_length=24)
    row_version = models.BinaryField(editable=False)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField()
    created_by = models.CharField(max_length=64)
    updated_at = models.DateTimeField()
    updated_by = models.CharField(max_length=64)

    class Meta:
        db_table = "vims_certs_tracked_item"
        managed = False


class PdfBlob(models.Model):
    blob_id = models.UUIDField(primary_key=True, editable=False)
    tracked_item = models.ForeignKey(TrackedItem, db_column="tracked_item_id", null=True, blank=True, on_delete=models.DO_NOTHING)
    snapshot_id = models.UUIDField(null=True, blank=True)
    blob_storage_path = models.CharField(max_length=512)
    filename = models.CharField(max_length=256)
    content_sha256 = models.CharField(max_length=64)
    content_size_bytes = models.BigIntegerField()
    uploaded_by = models.CharField(max_length=64)
    uploaded_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    superseded_at = models.DateTimeField(null=True, blank=True)
    retention_policy = models.CharField(max_length=32)
    scheduled_delete_at = models.DateTimeField(null=True, blank=True)
    delete_pending_since = models.DateTimeField(null=True, blank=True)
    dpa_retention_override_until = models.DateTimeField(null=True, blank=True)
    ocr_payload_json = models.TextField(null=True, blank=True)
    ocr_confidence_per_field = models.TextField(null=True, blank=True)
    ocr_processed_at = models.DateTimeField(null=True, blank=True)
    ocr_engine_version = models.CharField(max_length=32, null=True, blank=True)
    schema_version = models.SmallIntegerField(default=1)

    class Meta:
        db_table = "vims_certs_pdf_blob"
        managed = False
