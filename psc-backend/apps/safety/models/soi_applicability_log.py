from __future__ import annotations

from django.db import models
from django.db.models import Q

from .base import PublicIdMixin


class SOIApplicabilityLog(PublicIdMixin):
    class Decision(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    vessel_id = models.CharField(max_length=64)
    area_id = models.IntegerField()
    old_applicable = models.BooleanField()
    new_applicable = models.BooleanField()
    reason = models.TextField()
    master_requested_by = models.CharField(max_length=64)
    master_requested_at = models.DateTimeField(auto_now_add=True)
    master_signature = models.CharField(max_length=256)
    dpa_approved_by = models.CharField(max_length=64, null=True, blank=True)
    dpa_approved_at = models.DateTimeField(null=True, blank=True)
    dpa_signature = models.CharField(max_length=256, null=True, blank=True)
    dpa_decision = models.CharField(max_length=16, choices=Decision.choices, null=True, blank=True)
    schema_version = models.IntegerField(default=1, db_default=1)

    class Meta:
        db_table = "vims_safety_soi_applicability_log"
        constraints = [
            models.CheckConstraint(
                condition=Q(dpa_decision__isnull=True) | Q(dpa_decision__in=["APPROVED", "REJECTED"]),
                name="ck_vims_safety_soi_applicability_log_decision",
            ),
        ]
        indexes = [
            models.Index(
                fields=("vessel_id", "area_id", "master_requested_at"),
                name="ix_safe_soial_vsl_area",
            ),
        ]
