"""
CAR-related models per BACKEND_STRUCTURE.md Parts 4.6-4.9, 5.1-5.2.

Note: The CAR model itself lives in apps/inspection/deficiency_models.py
(already migrated with FK to Deficiency). This file contains the
additional models that reference CAR.

Tables:
- psc_car_clc_mapping: CLC codes linked to CARs (4.6)
- psc_corrective_action: Individual corrective actions (4.7)
- psc_evidence: Evidence files for CARs (4.8)
- psc_physical_verification: Physical verification visits (4.9)
- psc_activity_history: User-visible activity timeline (5.1)
- psc_audit_log: Field-level audit trail (5.2)
"""

import uuid
from django.db import models

from apps.inspection.deficiency_models import CAR


class CarClcMapping(models.Model):
    """
    Multiple CLC codes per CAR (many-to-many).
    Table: psc_car_clc_mapping

    Per BACKEND_STRUCTURE.md Part 4.6
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    car = models.ForeignKey(
        CAR,
        on_delete=models.CASCADE,
        related_name='clc_mappings'
    )

    # FK to CLC_Item - store as CLC_Code string (e.g. '2-1', 'P3')
    clc_item_id = models.CharField(max_length=10, db_index=True)

    # Optional custom cause text if CLC not sufficient
    custom_cause_text = models.CharField(max_length=500, null=True, blank=True)

    # Audit
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'psc_car_clc_mapping'
        indexes = [
            models.Index(fields=['car']),
        ]

    def __str__(self):
        return f"CAR {self.car.car_number} - CLC {self.clc_item_id}"


class ActionType(models.TextChoices):
    """Corrective action type choices."""
    IMMEDIATE = 'IMMEDIATE', 'Immediate'
    LONG_TERM = 'LONG_TERM', 'Long Term'


class CorrectiveAction(models.Model):
    """
    Individual corrective actions within a CAR.
    Table: psc_corrective_action

    Per BACKEND_STRUCTURE.md Part 4.7
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    car = models.ForeignKey(
        CAR,
        on_delete=models.CASCADE,
        related_name='corrective_actions'
    )

    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices
    )

    description = models.TextField()

    # Owner can be vessel crew or office user
    owner_crew_id = models.UUIDField(null=True, blank=True)  # FK to HRM501.id
    owner_user_id = models.CharField(max_length=100, null=True, blank=True)  # FK to users.employee_id

    due_date = models.DateField(null=True, blank=True)

    # Completion
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_remarks = models.TextField(null=True, blank=True)

    # Ordering within CAR
    sequence_no = models.IntegerField(default=1)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Audit fields
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Offline sync
    client_id = models.UUIDField(null=True, blank=True)
    sync_version = models.IntegerField(default=1)

    class Meta:
        db_table = 'psc_corrective_action'
        ordering = ['sequence_no', 'created_date']
        indexes = [
            models.Index(fields=['car']),
            models.Index(fields=['owner_crew_id']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.get_action_type_display()}: {self.description[:50]}"

    def get_next_sequence_no(self):
        """Get the next sequence number for this CAR."""
        last_action = CorrectiveAction.objects.filter(
            car=self.car,
            is_deleted=False
        ).order_by('-sequence_no').first()

        return (last_action.sequence_no + 1) if last_action else 1


class EvidenceType(models.TextChoices):
    """Evidence type choices."""
    BEFORE = 'BEFORE', 'Before'
    AFTER = 'AFTER', 'After'
    EVIDENCE = 'EVIDENCE', 'Evidence'
    OTHER = 'OTHER', 'Other'


class Evidence(models.Model):
    """
    Evidence files (photos, documents) for CAR.
    Table: psc_evidence

    Per BACKEND_STRUCTURE.md Part 4.8
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    car = models.ForeignKey(
        CAR,
        on_delete=models.CASCADE,
        related_name='evidence'
    )

    evidence_type = models.CharField(
        max_length=20,
        choices=EvidenceType.choices
    )

    # File info
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)  # bytes
    mime_type = models.CharField(max_length=100)

    # Mandatory description
    description = models.CharField(max_length=500)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Upload info
    uploaded_by = models.CharField(max_length=100, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Offline sync
    client_id = models.UUIDField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, default='SYNCED')  # PENDING, SYNCED, FAILED

    class Meta:
        db_table = 'psc_evidence'
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['car']),
            models.Index(fields=['evidence_type']),
        ]

    def __str__(self):
        return f"{self.get_evidence_type_display()}: {self.file_name}"


class PVStatus(models.TextChoices):
    """Physical verification status choices."""
    OPEN = 'OPEN', 'Open'
    CLOSED = 'CLOSED', 'Closed'


class PhysicalVerification(models.Model):
    """
    Physical verification visits for closed CARs.
    Table: psc_physical_verification

    Per BACKEND_STRUCTURE.md Part 4.9
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    car = models.ForeignKey(
        CAR,
        on_delete=models.CASCADE,
        related_name='physical_verifications'
    )

    status = models.CharField(
        max_length=20,
        choices=PVStatus.choices,
        default=PVStatus.OPEN,
        db_index=True
    )

    scheduled_date = models.DateField(null=True, blank=True)
    visit_date = models.DateField(null=True, blank=True)
    visit_port = models.CharField(max_length=200, null=True, blank=True)

    # Verifier can be office user or crew
    verifier_user_id = models.CharField(max_length=100, null=True, blank=True)  # FK to users.employee_id
    verifier_crew_id = models.UUIDField(null=True, blank=True)  # FK to HRM501.id

    comments = models.TextField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Audit fields
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Close info
    closed_by = models.CharField(max_length=100, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'psc_physical_verification'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['car']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"PV for {self.car.car_number} - {self.get_status_display()}"


class ActivityHistory(models.Model):
    """
    User-visible activity timeline (synced to vessels).
    Table: psc_activity_history

    Per BACKEND_STRUCTURE.md Part 5.1

    Event Types:
    - INSPECTION_CREATED, INSPECTION_SUBMITTED, INSPECTION_PIC_REVIEWED, INSPECTION_DPA_CLOSED
    - DEFICIENCY_ADDED, DEFICIENCY_CLEARED, DEFICIENCY_ACTION_UPDATED
    - CAR_CREATED, CAR_SUBMITTED, CAR_PIC_ACCEPTED, CAR_REWORK_REQUESTED, CAR_DPA_CLOSED
    - EVIDENCE_UPLOADED, EVIDENCE_DELETED
    - ACTION_COMPLETED
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entity_type = models.CharField(max_length=30)  # INSPECTION, DEFICIENCY, CAR, EVIDENCE, ACTION
    entity_id = models.UUIDField()

    # For sync filtering
    vessel_id = models.UUIDField(db_index=True)

    event_type = models.CharField(max_length=50)
    event_description = models.CharField(max_length=500)

    performed_by = models.CharField(max_length=100)
    performed_by_name = models.CharField(max_length=200, null=True, blank=True)
    performed_at = models.DateTimeField(auto_now_add=True)

    # JSON for additional data
    metadata = models.TextField(null=True, blank=True)  # JSON string

    class Meta:
        db_table = 'psc_activity_history'
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['vessel_id']),
            models.Index(fields=['-performed_at']),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.event_description[:50]}"


class AuditLog(models.Model):
    """
    Detailed field-level audit trail (Office only, NOT synced to vessels).
    Table: psc_audit_log

    Per BACKEND_STRUCTURE.md Part 5.2
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entity_type = models.CharField(max_length=30)
    entity_id = models.UUIDField()

    action = models.CharField(max_length=20)  # CREATE, UPDATE, DELETE
    field_name = models.CharField(max_length=100, null=True, blank=True)  # NULL for CREATE/DELETE
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    performed_by = models.CharField(max_length=100)
    performed_by_role = models.CharField(max_length=50, null=True, blank=True)
    performed_at = models.DateTimeField(auto_now_add=True)

    ip_address = models.CharField(max_length=50, null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)

    # Office editing on behalf of vessel
    is_office_edit_assist = models.BooleanField(default=False)

    class Meta:
        db_table = 'psc_audit_log'
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['-performed_at']),
            models.Index(fields=['performed_by']),
        ]

    def __str__(self):
        return f"{self.action} {self.entity_type} by {self.performed_by}"
