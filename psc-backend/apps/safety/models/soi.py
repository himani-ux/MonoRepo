from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now

from .base import PublicIdMixin


class SOIInspection(PublicIdMixin):
    class State(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        DOWNLOADED = "DOWNLOADED", "Downloaded"
        IN_FIELDWORK = "IN_FIELDWORK", "In Fieldwork"
        REPORTED = "REPORTED", "Reported"
        CLOSED = "CLOSED", "Closed"

    class ChecklistFormat(models.TextChoices):
        PDF = "PDF", "PDF"
        XLSX = "XLSX", "Excel"

    vessel_id = models.CharField(max_length=64, db_index=True)
    inspection_reference = models.CharField(max_length=32, unique=True)
    cycle_label = models.CharField(max_length=16)
    state = models.CharField(max_length=24, choices=State.choices, default=State.PLANNED)
    planned_date = models.DateField()
    safety_officer_crew_id = models.CharField(max_length=64)
    safety_officer_department = models.CharField(max_length=16)
    assistant_crew_id = models.CharField(max_length=64)
    assistant_department = models.CharField(max_length=16)
    master_crew_id = models.CharField(max_length=64, null=True, blank=True)
    checklist_unique_id = models.CharField(max_length=32, null=True, blank=True)
    checklist_generated_at = models.DateTimeField(null=True, blank=True)
    checklist_format = models.CharField(
        max_length=8,
        choices=ChecklistFormat.choices,
        null=True,
        blank=True,
    )
    fieldwork_started_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    lost_paper_flag = models.BooleanField(default=False, db_default=False)
    lost_paper_note = models.TextField(null=True, blank=True)
    section_12_included = models.BooleanField(default=False, db_default=False)
    schema_version = models.IntegerField(default=1, db_default=1)
    is_deleted = models.BooleanField(default=False, db_default=False)
    is_archived = models.BooleanField(default=False, db_default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_soi_inspection"
        ordering = ("-planned_date", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(state__in=["PLANNED", "DOWNLOADED", "IN_FIELDWORK", "REPORTED", "CLOSED"]),
                name="ck_vims_safety_soi_inspection_state",
            ),
            models.CheckConstraint(
                condition=Q(checklist_format__isnull=True) | Q(checklist_format__in=["PDF", "XLSX"]),
                name="ck_vims_safety_soi_inspection_format",
            ),
            models.CheckConstraint(
                condition=~Q(assistant_department=models.F("safety_officer_department")),
                name="ck_vims_safety_soi_inspection_xfunc",
            ),
            models.CheckConstraint(
                condition=(Q(is_archived=False) & Q(archived_at__isnull=True))
                | (Q(is_archived=True) & Q(archived_at__isnull=False)),
                name="ck_vims_safety_soi_inspection_archive_pair",
            ),
            models.UniqueConstraint(
                fields=("checklist_unique_id",),
                condition=Q(checklist_unique_id__isnull=False),
                name="uq_vims_safety_soi_checklist_unique_id",
            ),
        ]
        indexes = [
            models.Index(fields=("vessel_id", "state"), name="ix_safe_soii_vsl_state"),
            models.Index(fields=("vessel_id", "cycle_label"), name="ix_safe_soii_cycle"),
            models.Index(fields=("checklist_unique_id",), name="ix_safe_soii_uid"),
        ]


class SOIOfficerSetting(PublicIdMixin):
    vessel_id = models.CharField(max_length=64, unique=True)
    alternate_enabled = models.BooleanField(default=False, db_default=False)
    alternate_so_crew_id = models.CharField(max_length=64, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    enabled_by = models.CharField(max_length=128, null=True, blank=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    disabled_by = models.CharField(max_length=128, null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    schema_version = models.IntegerField(default=1, db_default=1)
    created_by = models.CharField(max_length=128, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_soi_officer_setting"
        indexes = [
            models.Index(fields=("vessel_id", "alternate_enabled"), name="ix_safe_sois_vsl_enabled"),
        ]
