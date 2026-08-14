"""Audit-owned legacy inspection tag model."""

from django.db import models
from django.utils import timezone

from .base import AuditUuidPrimaryKeyMixin


class AuditLegacyInspectionTag(AuditUuidPrimaryKeyMixin):
    psc_inspection_id = models.CharField(max_length=32, unique=True)
    is_legacy = models.BooleanField(default=True)
    tagged_at = models.DateTimeField(default=timezone.now)
    tagged_by = models.CharField(max_length=100)
    tag_reason = models.CharField(max_length=400, null=True, blank=True)

    class Meta:
        db_table = "audit_legacy_inspection_tag"
