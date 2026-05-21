from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.utils import timezone

from .base import PublicIdMixin


class SOIFinding(PublicIdMixin):
    class Severity(models.TextChoices):
        HIGH = "HIGH", "High"
        MED = "MED", "Medium"
        LOW = "LOW", "Low"

    class Priority(models.TextChoices):
        HIGH = "HIGH", "High"
        MED = "MED", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        PENDING_CLOSURE = "PENDING_CLOSURE", "Pending Closure"
        MASTER_APPROVED = "MASTER_APPROVED", "Master Approved"
        CLOSED = "CLOSED", "Closed"
        CARRIED_FORWARD = "CARRIED_FORWARD", "Carried Forward"

    inspection_id = models.BigIntegerField()
    area_id = models.IntegerField()
    item_id = models.BigIntegerField(null=True, blank=True)
    title = models.CharField(max_length=256)
    description = models.TextField()
    severity = models.CharField(max_length=8, choices=Severity.choices)
    priority = models.CharField(max_length=8, choices=Priority.choices)
    mscat_category_id = models.IntegerField(null=True, blank=True)
    mscat_subcode_id = models.CharField(max_length=16, null=True, blank=True)
    shell_tag = models.CharField(max_length=32, null=True, blank=True)
    assigned_crew_id = models.CharField(max_length=64, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    proposed_action = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN)
    carried_forward_count = models.IntegerField(default=0, db_default=0)
    photo_attachment_path = models.CharField(max_length=512, null=True, blank=True)
    master_approved_at = models.DateTimeField(null=True, blank=True)
    master_approved_by = models.CharField(max_length=64, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_note = models.TextField(null=True, blank=True)
    schema_version = models.IntegerField(default=1, db_default=1)
    is_deleted = models.BooleanField(default=False, db_default=False)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(default=timezone.now, db_default=Now())
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_soi_finding"
        ordering = ("-created_date", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(severity__in=["HIGH", "MED", "LOW"]),
                name="ck_vims_safety_soi_finding_severity",
            ),
            models.CheckConstraint(
                condition=Q(priority__in=["HIGH", "MED", "LOW"]),
                name="ck_vims_safety_soi_finding_priority",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "OPEN",
                        "PENDING_CLOSURE",
                        "MASTER_APPROVED",
                        "CLOSED",
                        "CARRIED_FORWARD",
                    ]
                ),
                name="ck_vims_safety_soi_finding_status",
            ),
            models.CheckConstraint(
                condition=~Q(severity="HIGH") | Q(photo_attachment_path__isnull=False),
                name="ck_vims_safety_soi_finding_high_photo",
            ),
        ]
        indexes = [
            models.Index(fields=("inspection_id",), name="ix_safe_soif_insp"),
            models.Index(fields=("status",), name="ix_safe_soif_status"),
            models.Index(fields=("assigned_crew_id", "due_date"), name="ix_safe_soif_assgn"),
            models.Index(fields=("severity", "status"), name="ix_safe_soif_sev"),
            models.Index(fields=("mscat_category_id", "mscat_subcode_id"), name="ix_safe_soif_mscat"),
        ]
