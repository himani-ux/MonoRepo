"""
Deficiency and CAR models per BACKEND_STRUCTURE.md Part 4.3, 4.4, and 4.5.

Tables:
- psc_deficiency: Individual deficiencies within an inspection
- psc_deficiency_action_history: Track action code changes
- psc_car: Corrective Action Report (placeholder, full impl in Phase 5)
"""

import uuid
from django.db import models
from django.utils import timezone

from .models import Inspection


class DefStatus(models.TextChoices):
    """Deficiency vessel-side workflow status. DEPRECATED — use CAR.status instead."""
    ALLOCATED = 'ALLOCATED', 'Allocated'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    APPROVED = 'APPROVED', 'Approved'
    SUBMITTED = 'SUBMITTED', 'Submitted'


class CARStatus(models.TextChoices):
    """Unified CAR workflow status covering vessel + office lifecycle."""
    ALLOTTED = 'ALLOTTED', 'Allotted'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    PENDING_CE_REVIEW = 'PENDING_CE_REVIEW', 'Pending CE Review'
    PENDING_MASTER_REVIEW = 'PENDING_MASTER_REVIEW', 'Pending Master Review'
    SUBMITTED_TO_PIC = 'SUBMITTED_TO_PIC', 'Submitted to PIC'
    PIC_REVIEW = 'PIC_REVIEW', 'PIC Review'
    SUBMITTED_TO_DPA = 'SUBMITTED_TO_DPA', 'Submitted to DPA'
    CLOSED = 'CLOSED', 'Closed'
    RETURNED_FOR_REWORK = 'RETURNED_FOR_REWORK', 'Returned for Rework'


# Backward-compat aliases for legacy code/tests that still reference old states.
CARStatus.DRAFT = CARStatus.ALLOTTED
CARStatus.SUBMITTED = CARStatus.SUBMITTED_TO_PIC
# Legacy alias for backward compatibility only; do not use for permissions/workflow.
CARStatus.PIC_ACCEPTED = CARStatus.PIC_REVIEW
CARStatus.REWORK_REQUESTED = CARStatus.RETURNED_FOR_REWORK
CARStatus.DPA_CLOSED = CARStatus.CLOSED


class CAR(models.Model):
    """
    Corrective Action Report - placeholder model for Phase 4.
    Full implementation in Phase 5 (FEAT-CAR-*).
    Table: psc_car

    Per BACKEND_STRUCTURE.md Part 4.5

    Note: This is a minimal model for the auto-CAR signal.
    Additional fields will be added in Phase 5.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 1:1 relationship with deficiency (set in Deficiency model)
    # deficiency field will be set via OneToOneField from Deficiency

    # CAR number: PSC-{YEAR}-{SEQ}
    car_number = models.CharField(max_length=20, unique=True, db_index=True)

    # Status workflow
    status = models.CharField(
        max_length=30,
        choices=CARStatus.choices,
        default=CARStatus.ALLOTTED,
        db_index=True
    )

    # Root cause (filled later in Phase 5)
    root_cause_summary = models.TextField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    initial_action_code = models.CharField(max_length=10, null=True, blank=True)

    # PIC Review fields
    pic_comment = models.TextField(null=True, blank=True)
    pic_accepted_by = models.CharField(max_length=100, null=True, blank=True)
    pic_accepted_at = models.DateTimeField(null=True, blank=True)

    # Rework fields
    rework_reason = models.TextField(null=True, blank=True)
    rework_requested_by = models.CharField(max_length=100, null=True, blank=True)
    rework_requested_at = models.DateTimeField(null=True, blank=True)
    rework_count = models.IntegerField(default=0)

    # DPA Close fields
    dpa_comment = models.TextField(null=True, blank=True)
    dpa_closed_by = models.CharField(max_length=100, null=True, blank=True)
    dpa_closed_at = models.DateTimeField(null=True, blank=True)

    # Verification pending flag (set when CAR is closed but PV not yet done)
    verification_pending = models.BooleanField(default=False)

    # Last workflow action tracking
    last_action = models.CharField(max_length=50, null=True, blank=True)
    last_action_by = models.CharField(max_length=100, null=True, blank=True)
    last_action_at = models.DateTimeField(null=True, blank=True)
    last_action_comment = models.TextField(null=True, blank=True)

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
        db_table = 'psc_car'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['car_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.car_number

    @classmethod
    def generate_car_number(cls):
        """
        Generate next CAR number: PSC-{YEAR}-{SEQ}
        Format: PSC-2026-001, PSC-2026-002, etc.
        """
        current_year = timezone.now().year
        prefix = f"PSC-{current_year}-"

        # Get the highest sequence number for this year
        last_car = cls.objects.filter(
            car_number__startswith=prefix
        ).order_by('-car_number').first()

        if last_car:
            # Extract sequence number and increment
            try:
                last_seq = int(last_car.car_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"{prefix}{next_seq:03d}"


class Deficiency(models.Model):
    """
    Individual deficiency within an inspection.
    Table: psc_deficiency

    Per BACKEND_STRUCTURE.md Part 4.3
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK to inspection
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='deficiencies'
    )

    # Deficiency code - store both ID reference and denormalized code for display
    # FK to PSC_Def_Code table (def_code is the PK, a 5-digit string)
    def_code_id = models.CharField(max_length=5, db_index=True)  # FK to PSC_Def_Code.def_code
    def_code = models.CharField(max_length=10)  # Denormalized for display

    # Deficiency description
    description = models.TextField()

    # Action code - store both ID reference and denormalized code
    # FK to PSC_Action_Codes table (action_code is an integer PK)
    action_code_id = models.IntegerField(null=True, blank=True, db_index=True)
    action_code = models.CharField(max_length=10, null=True, blank=True)  # Denormalized

    # Target and clearing
    target_date = models.DateField(null=True, blank=True)
    is_cleared = models.BooleanField(default=False, db_index=True)
    cleared_date = models.DateField(null=True, blank=True)

    # Follow-up reference (which follow-up inspection cleared this)
    cleared_by_follow_up = models.ForeignKey(
        Inspection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cleared_deficiencies'
    )

    # Sequence number within inspection
    sequence_no = models.IntegerField(default=1)

    # 1:1 relationship with CAR
    car = models.OneToOneField(
        CAR,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deficiency'
    )

    # Assigned crew member (who is responsible for the CAR)
    assigned_crew_id = models.CharField(null=True, blank=True, db_index=True, max_length=50)

    # Vessel-side workflow status
    def_status = models.CharField(
        max_length=20,
        choices=DefStatus.choices,
        default=DefStatus.ALLOCATED,
        db_index=True,
    )

    # Reviewer (auto-set based on owner rank)
    reviewer_crew_id = models.CharField(max_length=100, null=True, blank=True)

    # Denormalized owner/reviewer info for display
    owner_rank = models.CharField(max_length=100, null=True, blank=True)
    owner_name = models.CharField(max_length=200, null=True, blank=True)
    reviewer_rank = models.CharField(max_length=100, null=True, blank=True)
    reviewer_name = models.CharField(max_length=200, null=True, blank=True)

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
        db_table = 'psc_deficiency'
        ordering = ['sequence_no', 'created_date']
        indexes = [
            models.Index(fields=['inspection']),
            models.Index(fields=['def_code']),
            models.Index(fields=['is_cleared']),
            models.Index(fields=['assigned_crew_id']),
        ]

    def __str__(self):
        return f"{self.def_code} - {self.description[:50]}"

    def get_next_sequence_no(self):
        """Get the next sequence number for this inspection."""
        last_def = Deficiency.objects.filter(
            inspection=self.inspection,
            is_deleted=False
        ).order_by('-sequence_no').first()

        return (last_def.sequence_no + 1) if last_def else 1


class DeficiencyActionHistory(models.Model):
    """
    Track action code changes over time.
    Table: psc_deficiency_action_history

    Per BACKEND_STRUCTURE.md Part 4.4
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK to deficiency
    deficiency = models.ForeignKey(
        Deficiency,
        on_delete=models.CASCADE,
        related_name='action_history'
    )

    # Previous action code (null for initial)
    previous_action_code_id = models.IntegerField(null=True, blank=True)
    previous_action_code = models.CharField(max_length=10, null=True, blank=True)

    # New action code
    new_action_code_id = models.IntegerField()
    new_action_code = models.CharField(max_length=10)

    # Follow-up inspection that caused this change (if any)
    follow_up_inspection = models.ForeignKey(
        Inspection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_code_changes'
    )

    # Change metadata
    change_reason = models.CharField(max_length=500, null=True, blank=True)
    changed_by = models.CharField(max_length=100)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'psc_deficiency_action_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['deficiency']),
        ]

    def __str__(self):
        prev = self.previous_action_code or 'None'
        return f"{self.deficiency.def_code}: {prev} → {self.new_action_code}"
