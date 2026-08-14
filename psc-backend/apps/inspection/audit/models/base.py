"""Shared passive ORM pieces for Audit schema models."""

import uuid

from django.db import models
from django.utils import timezone


class AuditActiveManager(models.Manager):
    """Default Audit manager: hide soft-deleted rows per BACKEND_STRUCTURE.md section 4."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AuditUuidPrimaryKeyMixin(models.Model):
    """Audit tables use native SQL Server uniqueidentifier PKs in migrations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class AuditCreatedMixin(AuditUuidPrimaryKeyMixin):
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class AuditSoftDeleteMixin(AuditCreatedMixin):
    is_deleted = models.BooleanField(default=False)
    objects = AuditActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


class AuditFullBaseModel(AuditSoftDeleteMixin):
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    client_id = models.UUIDField(null=True, blank=True)
    sync_version = models.IntegerField(default=1)

    class Meta:
        abstract = True
