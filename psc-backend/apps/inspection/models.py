"""
Inspection models per BACKEND_STRUCTURE.md Part 4.1 and 4.2.

Tables:
- psc_inspection: Main inspection record
- psc_inspection_report: Inspection report PDF attachments
"""

import uuid
from django.db import models

from .defintel_models import OpenSourceImportRun, OpenSourceDeficiencyRecord  # noqa: F401


class InspectionStatus(models.TextChoices):
    """Inspection status choices per BACKEND_STRUCTURE.md state machine."""
    DRAFT = 'DRAFT', 'Draft'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    PIC_REVIEWED = 'PIC_REVIEWED', 'PIC Reviewed'
    DPA_CLOSED = 'DPA_CLOSED', 'DPA Closed'


class InspectionType(models.TextChoices):
    """Inspection type choices."""
    PSC = 'PSC', 'Port State Control'
    RS = 'RS', 'RightShip'
    AUDIT = 'AUDIT', 'Audit'
    INTERNAL = 'INTERNAL', 'Internal'


class PSCSubtype(models.TextChoices):
    """PSC inspection subtype choices (only for PSC type)."""
    INITIAL = 'INITIAL', 'Initial'
    EXPANDED = 'EXPANDED', 'Expanded'
    CIC = 'CIC', 'Concentrated Inspection Campaign'
    FOLLOW_UP = 'FOLLOW_UP', 'Follow-up'


class Inspection(models.Model):
    """
    Main inspection record.
    Table: psc_inspection

    Per BACKEND_STRUCTURE.md Part 4.1
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Vessel reference (FK to existing VesselData table)
    vessel_id = models.UUIDField(db_index=True)

    # Inspection details
    inspection_type = models.CharField(
        max_length=20,
        choices=InspectionType.choices,
        db_index=True
    )
    psc_subtype = models.CharField(
        max_length=20,
        choices=PSCSubtype.choices,
        null=True,
        blank=True
    )
    inspection_date = models.DateField(db_index=True)
    port_place = models.CharField(max_length=200)
    country = models.CharField(max_length=100, null=True, blank=True)

    # MOU reference (FK to MOU_Master table - but we use code for simplicity)
    mou_id = models.CharField(max_length=20, null=True, blank=True)

    # Inspector info
    authority = models.CharField(max_length=200, null=True, blank=True)
    inspector_name = models.CharField(max_length=200, null=True, blank=True)
    report_reference = models.CharField(max_length=100, null=True, blank=True)

    # Detention flag
    is_detention = models.BooleanField(default=False)

    # Deficiencies reported flag (YES/NO, NULL for legacy records)
    def_reported = models.CharField(
        max_length=3,
        choices=[('YES', 'Yes'), ('NO', 'No')],
        null=True,
        blank=True,
    )

    # Status workflow
    status = models.CharField(
        max_length=20,
        choices=InspectionStatus.choices,
        default=InspectionStatus.DRAFT,
        db_index=True
    )

    # Follow-up reference (self FK for follow-up inspections)
    parent_inspection = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='follow_ups'
    )

    # Revision tracking
    revision_no = models.IntegerField(default=1)

    # PIC review fields
    pic_comment = models.TextField(null=True, blank=True)
    pic_reviewed_by = models.CharField(max_length=100, null=True, blank=True)
    pic_reviewed_at = models.DateTimeField(null=True, blank=True)

    # DPA close fields
    dpa_comment = models.TextField(null=True, blank=True)
    dpa_closed_by = models.CharField(max_length=100, null=True, blank=True)
    dpa_closed_at = models.DateTimeField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Audit fields
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Offline sync fields
    client_id = models.UUIDField(null=True, blank=True)
    sync_version = models.IntegerField(default=1)

    class Meta:
        db_table = 'psc_inspection'
        ordering = ['-inspection_date', '-created_date']
        indexes = [
            models.Index(fields=['vessel_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-inspection_date']),
            models.Index(fields=['inspection_type']),
        ]

    def __str__(self):
        return f"{self.inspection_type} - {self.port_place} ({self.inspection_date})"

    def can_submit(self):
        """Check if inspection can be submitted."""
        if self.status != InspectionStatus.DRAFT:
            return False
        if not self.reports.filter(is_deleted=False).exists():
            return False
        return not self.deficiencies.filter(is_deleted=False, car__isnull=True).exists()

    def can_pic_review(self):
        """Check if inspection can be PIC reviewed."""
        return self.status == InspectionStatus.SUBMITTED

    def can_dpa_close(self):
        """Check if inspection can be DPA closed."""
        return self.status == InspectionStatus.PIC_REVIEWED

    @property
    def active_reports(self):
        """Filter to non-deleted reports."""
        return self.reports.filter(is_deleted=False)

    @property
    def active_deficiencies(self):
        """Filter to non-deleted deficiencies."""
        return self.deficiencies.filter(is_deleted=False)


class InspectionReport(models.Model):
    """
    Inspection report PDF attachments.
    Table: psc_inspection_report

    Per BACKEND_STRUCTURE.md Part 4.2
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK to inspection
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='reports'
    )

    # Report type
    report_type = models.CharField(
        max_length=20,
        choices=[('ORIGINAL', 'Original'), ('FOLLOW_UP', 'Follow-up')],
        default='ORIGINAL',
    )

    # File info
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)  # bytes
    mime_type = models.CharField(max_length=100, default='application/pdf')
    description = models.TextField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Audit fields
    uploaded_by = models.CharField(max_length=100, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'psc_inspection_report'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['inspection']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.inspection})"
