"""
DefIntel OpenSource persistence models.

Phase 2 scope only:
- OpenSource import run tracking
- OpenSource deficiency records with DB-level dedup key uniqueness
"""

import uuid

from django.db import models


class OpenSourceImportRun(models.Model):
    """Tracks one uploaded monthly OpenSource workbook import run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.CharField(max_length=100, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, db_index=True)

    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    inserted_rows = models.PositiveIntegerField(default=0)
    duplicate_rows = models.PositiveIntegerField(default=0)
    invalid_rows = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'psc_opensource_import_run'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} ({self.uploaded_at})"


class OpenSourceDeficiencyRecord(models.Model):
    """Normalized OpenSource deficiency row persisted for dedup + analytics."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_run = models.ForeignKey(
        OpenSourceImportRun,
        on_delete=models.CASCADE,
        related_name='records',
    )

    year = models.PositiveIntegerField(db_index=True)
    def_code_norm = models.CharField(max_length=5, db_index=True)
    action_code_norm = models.IntegerField(db_index=True)
    port_norm = models.CharField(max_length=200, db_index=True)
    mou_norm = models.CharField(max_length=20, db_index=True)

    country_norm = models.CharField(max_length=100, null=True, blank=True)
    description_raw = models.TextField(null=True, blank=True)

    dedup_key_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = 'psc_opensource_deficiency_record'
        indexes = [
            models.Index(fields=['year', 'def_code_norm']),
            models.Index(fields=['port_norm', 'mou_norm']),
        ]

    def __str__(self):
        return f"{self.year}:{self.def_code_norm}/{self.action_code_norm}"
