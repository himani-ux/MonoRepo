"""
Sync models per BACKEND_STRUCTURE.md Section 6.

Tables:
- psc_sync_log: Track sync operations between vessel and server (6.1)
- psc_sync_log_detail: Individual record sync status (6.2)
- psc_sync_conflict: Unresolved sync conflicts (6.3)
- psc_sync_token: Last sync point per vessel (6.4)

Implements: FEAT-SYNC-002, FEAT-SYNC-003, FEAT-SYNC-004, FEAT-SYNC-005
"""

import uuid
from django.db import models


class SyncType(models.TextChoices):
    """Sync operation type choices."""
    PUSH = 'PUSH', 'Push'
    PULL = 'PULL', 'Pull'


class SyncStatus(models.TextChoices):
    """Sync operation status choices."""
    PENDING = 'PENDING', 'Pending'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'


class SyncDetailStatus(models.TextChoices):
    """Individual record sync status choices."""
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'
    CONFLICT = 'CONFLICT', 'Conflict'


class SyncOperation(models.TextChoices):
    """Sync event operation choices."""
    CREATE = 'CREATE', 'Create'
    UPDATE = 'UPDATE', 'Update'
    DELETE = 'DELETE', 'Delete'


class ConflictStatus(models.TextChoices):
    """Conflict status choices."""
    PENDING = 'PENDING', 'Pending'
    RESOLVED = 'RESOLVED', 'Resolved'


class ConflictResolution(models.TextChoices):
    """Conflict resolution choices."""
    KEEP_SERVER = 'KEEP_SERVER', 'Keep Server'
    KEEP_VESSEL = 'KEEP_VESSEL', 'Keep Vessel'
    REOPEN_FOR_MERGE = 'REOPEN_FOR_MERGE', 'Reopen for Merge'


class SyncLog(models.Model):
    """
    Track sync operations between vessel and server.
    Table: psc_sync_log

    Per BACKEND_STRUCTURE.md Section 6.1
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Vessel performing the sync
    vessel_id = models.UUIDField(db_index=True)

    # Idempotency key — prevents duplicate sync processing
    sync_id = models.UUIDField(unique=True)

    sync_type = models.CharField(
        max_length=20,
        choices=SyncType.choices,
    )

    sync_status = models.CharField(
        max_length=20,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
    )

    records_sent = models.IntegerField(null=True, blank=True)
    records_received = models.IntegerField(null=True, blank=True)

    # SHA-256 checksum for payload integrity
    payload_checksum = models.CharField(max_length=64, null=True, blank=True)

    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    # Audit
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'psc_sync_log'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['vessel_id']),
            models.Index(fields=['sync_id']),
            models.Index(fields=['-created_date']),
        ]

    def __str__(self) -> str:
        return f"SyncLog {self.sync_id} ({self.sync_type} - {self.sync_status})"


class SyncLogDetail(models.Model):
    """
    Individual record sync status within a sync operation.
    Table: psc_sync_log_detail

    Per BACKEND_STRUCTURE.md Section 6.2
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    sync_log = models.ForeignKey(
        SyncLog,
        on_delete=models.CASCADE,
        related_name='details',
    )

    entity_type = models.CharField(max_length=30)  # INSPECTION, DEFICIENCY, CAR, etc.
    entity_id = models.UUIDField()

    # Vessel-generated ID (for mapping client→server)
    client_id = models.UUIDField(null=True, blank=True)

    operation = models.CharField(
        max_length=20,
        choices=SyncOperation.choices,
    )

    sync_status = models.CharField(
        max_length=20,
        choices=SyncDetailStatus.choices,
    )

    error_message = models.TextField(null=True, blank=True)

    # Version tracking for conflict detection
    server_version = models.IntegerField(null=True, blank=True)
    client_version = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'psc_sync_log_detail'
        indexes = [
            models.Index(fields=['sync_log']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self) -> str:
        return f"SyncDetail {self.entity_type}:{self.entity_id} ({self.sync_status})"


class SyncConflict(models.Model):
    """
    Unresolved sync conflicts requiring office resolution.
    Table: psc_sync_conflict

    Per BACKEND_STRUCTURE.md Section 6.3
    Implements: FEAT-SYNC-004 (Conflict Detection), FEAT-SYNC-005 (Conflict Resolution)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    vessel_id = models.UUIDField(db_index=True)

    entity_type = models.CharField(max_length=30)  # INSPECTION, CAR, etc.
    entity_id = models.UUIDField()

    # JSON snapshots of both versions
    server_data = models.TextField()   # JSON string
    vessel_data = models.TextField()   # JSON string

    # JSON array of field names that differ
    conflicting_fields = models.TextField()  # JSON string

    status = models.CharField(
        max_length=20,
        choices=ConflictStatus.choices,
        default=ConflictStatus.PENDING,
    )

    resolution = models.CharField(
        max_length=30,
        choices=ConflictResolution.choices,
        null=True,
        blank=True,
    )

    resolved_by = models.CharField(max_length=100, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'psc_sync_conflict'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['vessel_id']),
            models.Index(fields=['status']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self) -> str:
        return f"Conflict {self.entity_type}:{self.entity_id} ({self.status})"


class SyncToken(models.Model):
    """
    Track last sync point per vessel for delta sync.
    Table: psc_sync_token

    Per BACKEND_STRUCTURE.md Section 6.4
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # One token per vessel (unique)
    vessel_id = models.UUIDField(unique=True)

    last_sync_at = models.DateTimeField()
    last_sync_id = models.UUIDField(null=True, blank=True)
    last_server_version = models.BigIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'psc_sync_token'
        indexes = [
            models.Index(fields=['vessel_id']),
        ]

    def __str__(self) -> str:
        return f"SyncToken vessel={self.vessel_id} version={self.last_server_version}"
