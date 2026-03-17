"""
Notification model per BACKEND_STRUCTURE.md Section 7.1.

Table: psc_notification
Implements: PRD.md FEAT-NOTIF-001
"""

import uuid
from django.db import models


class RecipientType(models.TextChoices):
    """Notification recipient type."""
    CREW = 'CREW', 'Crew'
    OFFICE = 'OFFICE', 'Office'


class NotificationType(models.TextChoices):
    """
    Notification type choices.
    Per BACKEND_STRUCTURE.md Section 7.1
    """
    CAR_CREATED = 'CAR_CREATED', 'CAR Created'
    CAR_SUBMITTED = 'CAR_SUBMITTED', 'CAR Submitted'
    CAR_PIC_ACCEPTED = 'CAR_PIC_ACCEPTED', 'CAR PIC Accepted'
    CAR_REWORK_REQUESTED = 'CAR_REWORK_REQUESTED', 'CAR Rework Requested'
    CAR_REOPENED = 'CAR_REOPENED', 'CAR Reopened'
    CAR_DPA_CLOSED = 'CAR_DPA_CLOSED', 'CAR DPA Closed'
    INSPECTION_DPA_CLOSED = 'INSPECTION_DPA_CLOSED', 'Inspection DPA Closed'
    ACTION_OVERDUE_WARNING = 'ACTION_OVERDUE_WARNING', 'Action Overdue Warning'
    ACTION_OVERDUE = 'ACTION_OVERDUE', 'Action Overdue'
    PSC_FOLLOW_UP_RECORDED = 'PSC_FOLLOW_UP_RECORDED', 'PSC Follow-up Recorded'
    CONFLICT_DETECTED = 'CONFLICT_DETECTED', 'Conflict Detected'
    CONFLICT_RESOLVED = 'CONFLICT_RESOLVED', 'Conflict Resolved'
    PHYSICAL_VERIFICATION_CREATED = 'PHYSICAL_VERIFICATION_CREATED', 'Physical Verification Created'
    DEF_ASSIGNED = 'DEF_ASSIGNED', 'Deficiency Assigned'


class Notification(models.Model):
    """
    In-app notification record.
    Table: psc_notification

    Per BACKEND_STRUCTURE.md Section 7.1
    Implements: PRD.md FEAT-NOTIF-001
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipient info
    recipient_type = models.CharField(
        max_length=20,
        choices=RecipientType.choices,
    )
    recipient_id = models.CharField(max_length=100)

    # Vessel reference (for vessel-specific notifications)
    vessel_id = models.UUIDField(null=True, blank=True)

    # Notification content
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=200)
    message = models.CharField(max_length=500)

    # Related entity
    entity_type = models.CharField(max_length=30, null=True, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)

    # Read status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'psc_notification'
        ordering = ['-created_date']
        indexes = [
            models.Index(
                fields=['recipient_type', 'recipient_id'],
                name='ix_psc_notif_recipient',
            ),
            models.Index(
                fields=['vessel_id'],
                name='ix_psc_notif_vessel_id',
            ),
            models.Index(
                fields=['is_read'],
                name='ix_psc_notif_is_read',
            ),
            models.Index(
                fields=['-created_date'],
                name='ix_psc_notif_created_date',
            ),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.recipient_id}"
