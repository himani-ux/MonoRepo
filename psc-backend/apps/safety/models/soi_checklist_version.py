from __future__ import annotations

import uuid

from django.db import models


class SOIChecklistVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    version_label = models.CharField(max_length=16, unique=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    source_description = models.CharField(max_length=256)
    active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "master_soi_checklist_version"
        managed = False
        ordering = ("-effective_from", "-id")
