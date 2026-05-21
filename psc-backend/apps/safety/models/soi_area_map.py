from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class SOIVesselAreaMap(PublicIdMixin):
    vessel_id = models.CharField(max_length=64)
    area_id = models.IntegerField()
    applicable = models.BooleanField(default=True, db_default=True)
    last_inspected_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    schema_version = models.IntegerField(default=1, db_default=1)

    class Meta:
        db_table = "vims_safety_soi_vessel_area_map"
        constraints = [
            models.UniqueConstraint(fields=("vessel_id", "area_id"), name="uq_vims_safety_soi_vessel_area"),
        ]
        indexes = [
            models.Index(fields=("vessel_id", "due_at"), name="ix_safe_soivam_due"),
        ]
