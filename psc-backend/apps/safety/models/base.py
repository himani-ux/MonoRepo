from __future__ import annotations

import uuid

from django.db import models


class PublicIdMixin(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    class Meta:
        abstract = True


class BaseSafetyRecord(PublicIdMixin):
    """
    Shared abstract base for Safety transactional models.

    The real monorepo will bind these identifiers to platform masters through the
    initial Safety migration. The handover workspace keeps the contract stable
    without hard-coding unavailable platform model imports.
    """

    vessel_id = models.CharField(max_length=64, db_index=True)
    state = models.CharField(max_length=48, db_index=True)
    created_by = models.CharField(max_length=128, db_index=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    schema_version = models.PositiveIntegerField()

    class Meta:
        abstract = True
