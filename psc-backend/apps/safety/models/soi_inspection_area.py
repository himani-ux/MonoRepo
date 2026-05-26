from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class SOIInspectionArea(PublicIdMixin):
    inspection_id = models.UUIDField()
    area_id = models.IntegerField()
    inspected = models.BooleanField(default=False, db_default=False)
    last_inspected_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    schema_version = models.IntegerField(default=1, db_default=1)

    class Meta:
        db_table = "vims_safety_soi_inspection_area"
        ordering = ("inspection_id", "area_id", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("inspection_id", "area_id"),
                name="uq_vims_safety_soi_inspection_area",
            ),
        ]
        indexes = [
            models.Index(
                fields=("inspection_id",),
                name="ix_safe_soia_insp",
            ),
            models.Index(
                fields=("area_id", "last_inspected_at"),
                name="ix_safe_soia_area",
            ),
        ]
