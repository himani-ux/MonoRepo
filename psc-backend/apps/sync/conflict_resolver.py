"""
Sync conflict detection and resolution service.

Per BACKEND_STRUCTURE.md Section 6.3 and PRD.md:
- FEAT-SYNC-004: Conflict Detection
- FEAT-SYNC-005: Conflict Resolution

Conflict detection: Compare client_version (from push payload) vs sync_version (server).
If client_version < server sync_version, the record was modified on the server
after the vessel's last sync — this is a conflict.

Resolution options:
- KEEP_SERVER: Discard vessel changes, notify vessel
- KEEP_VESSEL: Apply vessel changes, create audit log
- REOPEN_FOR_MERGE: Set CAR to REWORK_REQUESTED status
"""

import json
import logging
from typing import Any, Optional

from django.db import transaction
from django.utils import timezone

from apps.inspection.models import Inspection
from apps.inspection.deficiency_models import Deficiency, CAR, CARStatus
from apps.car.models import CorrectiveAction, AuditLog
from apps.notifications.signals import notify_conflict_detected, notify_conflict_resolved

from .models import (
    SyncConflict,
    SyncLogDetail,
    ConflictStatus,
    ConflictResolution,
    SyncDetailStatus,
)

logger = logging.getLogger(__name__)

# Entity type to model mapping
ENTITY_MODEL_MAP: dict[str, Any] = {
    'INSPECTION': Inspection,
    'DEFICIENCY': Deficiency,
    'CAR': CAR,
    'CORRECTIVE_ACTION': CorrectiveAction,
}

# Fields to exclude from conflict comparison (always differ between versions)
EXCLUDED_FIELDS = {
    'updated_date', 'updated_by', 'sync_version', 'id',
    'created_date', 'created_by', 'client_id',
}


def detect_conflict(
    entity_type: str,
    entity_id,
    client_version: int,
) -> Optional[int]:
    """
    Check if a sync conflict exists.

    Per FEAT-SYNC-004:
    - Compare client_version (from vessel push) vs sync_version (on server)
    - If client_version < sync_version, server was modified after vessel's last sync

    Args:
        entity_type: Type of entity (INSPECTION, CAR, etc.)
        entity_id: Server-side UUID of the entity
        client_version: Version the vessel has

    Returns:
        Server sync_version if conflict detected, None otherwise
    """
    model = ENTITY_MODEL_MAP.get(entity_type)
    if not model:
        logger.warning(f"Unknown entity_type for conflict detection: {entity_type}")
        return None

    try:
        instance = model.objects.get(id=entity_id)
    except model.DoesNotExist:
        logger.warning(f"{entity_type} {entity_id} not found for conflict check")
        return None

    server_version = instance.sync_version

    if client_version < server_version:
        logger.info(
            f"Conflict detected: {entity_type} {entity_id} "
            f"client_version={client_version} server_version={server_version}"
        )
        return server_version

    return None


def compute_conflicting_fields(
    server_data: dict,
    vessel_data: dict,
) -> list[str]:
    """
    Identify which fields differ between server and vessel versions.

    Returns list of field names where values differ.
    """
    conflicting = []
    all_keys = set(server_data.keys()) | set(vessel_data.keys())

    for key in all_keys:
        if key in EXCLUDED_FIELDS:
            continue
        server_val = server_data.get(key)
        vessel_val = vessel_data.get(key)
        if str(server_val) != str(vessel_val):
            conflicting.append(key)

    return conflicting


def create_conflict_record(
    vessel_id,
    entity_type: str,
    entity_id,
    server_data: dict,
    vessel_data: dict,
    sync_log_detail: Optional[SyncLogDetail] = None,
) -> SyncConflict:
    """
    Create a SyncConflict record with field-level diff and JSON snapshots.

    Per BACKEND_STRUCTURE.md Section 6.3:
    - Store server_data and vessel_data as JSON
    - Compute conflicting_fields as JSON array
    - Status defaults to PENDING

    Args:
        vessel_id: UUID of the vessel
        entity_type: Entity type string
        entity_id: Entity UUID
        server_data: Current server state as dict
        vessel_data: Vessel's version as dict
        sync_log_detail: Optional associated sync log detail record

    Returns:
        Created SyncConflict instance
    """
    conflicting_fields = compute_conflicting_fields(server_data, vessel_data)

    conflict = SyncConflict.objects.create(
        vessel_id=vessel_id,
        entity_type=entity_type,
        entity_id=entity_id,
        server_data=json.dumps(server_data, default=str),
        vessel_data=json.dumps(vessel_data, default=str),
        conflicting_fields=json.dumps(conflicting_fields),
        status=ConflictStatus.PENDING,
    )

    # Update sync log detail if provided
    if sync_log_detail:
        sync_log_detail.sync_status = SyncDetailStatus.CONFLICT
        sync_log_detail.save(update_fields=['sync_status'])

    logger.info(
        f"Conflict record created: {conflict.id} for {entity_type} {entity_id} "
        f"({len(conflicting_fields)} conflicting fields)"
    )

    # Notify vessel master of conflict
    notify_conflict_detected(str(vessel_id), entity_type, str(entity_id))

    return conflict


@transaction.atomic
def resolve_conflict(
    conflict_id,
    resolution: str,
    resolved_by: str,
    notes: str = '',
) -> SyncConflict:
    """
    Resolve a sync conflict.

    Per PRD.md FEAT-SYNC-005:
    - KEEP_SERVER: Discard vessel changes, notify vessel
    - KEEP_VESSEL: Apply vessel changes, create audit log
    - REOPEN_FOR_MERGE: Set CAR to REWORK_REQUESTED status

    Args:
        conflict_id: UUID of the conflict
        resolution: One of KEEP_SERVER, KEEP_VESSEL, REOPEN_FOR_MERGE
        resolved_by: User ID of the resolver
        notes: Optional resolution notes

    Returns:
        Updated SyncConflict instance
    """
    conflict = SyncConflict.objects.select_for_update().get(id=conflict_id)

    if conflict.status != ConflictStatus.PENDING:
        raise ValueError(f"Conflict {conflict_id} is already resolved")

    if resolution == ConflictResolution.KEEP_SERVER:
        _resolve_keep_server(conflict, resolved_by)
    elif resolution == ConflictResolution.KEEP_VESSEL:
        _resolve_keep_vessel(conflict, resolved_by)
    elif resolution == ConflictResolution.REOPEN_FOR_MERGE:
        _resolve_reopen_for_merge(conflict, resolved_by)
    else:
        raise ValueError(f"Unknown resolution: {resolution}")

    # Mark conflict as resolved
    conflict.status = ConflictStatus.RESOLVED
    conflict.resolution = resolution
    conflict.resolved_by = resolved_by
    conflict.resolved_at = timezone.now()
    conflict.resolution_notes = notes
    conflict.save()

    # Create audit log for the resolution
    AuditLog.objects.create(
        entity_type='SYNC_CONFLICT',
        entity_id=conflict.id,
        action='RESOLVE',
        field_name='resolution',
        old_value=ConflictStatus.PENDING,
        new_value=resolution,
        performed_by=resolved_by,
    )

    logger.info(
        f"Conflict {conflict_id} resolved: {resolution} by {resolved_by}"
    )

    # Notify vessel master of resolution
    notify_conflict_resolved(
        str(conflict.vessel_id),
        conflict.entity_type,
        str(conflict.entity_id),
        resolution,
    )

    return conflict


def _resolve_keep_server(conflict: SyncConflict, resolved_by: str) -> None:
    """
    KEEP_SERVER resolution: discard vessel changes.
    Server state is already correct, no data changes needed.
    Vessel will receive updated data on next pull.
    """
    logger.info(f"KEEP_SERVER: Discarding vessel changes for {conflict.entity_type} {conflict.entity_id}")


def _resolve_keep_vessel(conflict: SyncConflict, resolved_by: str) -> None:
    """
    KEEP_VESSEL resolution: apply vessel data to server.
    Per FEAT-SYNC-005: "apply vessel changes, audit log"
    """
    model = ENTITY_MODEL_MAP.get(conflict.entity_type)
    if not model:
        raise ValueError(f"Unknown entity_type: {conflict.entity_type}")

    try:
        instance = model.objects.get(id=conflict.entity_id)
    except model.DoesNotExist:
        raise ValueError(f"{conflict.entity_type} {conflict.entity_id} not found")

    vessel_data = json.loads(conflict.vessel_data)
    conflicting_fields = json.loads(conflict.conflicting_fields)

    # Apply only the conflicting fields from vessel data
    for field_name in conflicting_fields:
        if field_name in EXCLUDED_FIELDS:
            continue
        if hasattr(instance, field_name):
            old_value = getattr(instance, field_name)
            new_value = vessel_data.get(field_name)
            setattr(instance, field_name, new_value)

            # Audit each field change
            AuditLog.objects.create(
                entity_type=conflict.entity_type,
                entity_id=conflict.entity_id,
                action='UPDATE',
                field_name=field_name,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                performed_by=resolved_by,
            )

    instance.updated_by = resolved_by
    instance.sync_version += 1
    instance.save()

    logger.info(
        f"KEEP_VESSEL: Applied {len(conflicting_fields)} field(s) "
        f"to {conflict.entity_type} {conflict.entity_id}"
    )


def _resolve_reopen_for_merge(conflict: SyncConflict, resolved_by: str) -> None:
    """
    REOPEN_FOR_MERGE resolution: set entity to REWORK_REQUESTED.
    Per FEAT-SYNC-005: "REOPEN_FOR_MERGE: set CAR to REWORK_REQUESTED"
    This allows the vessel to re-edit and resubmit.
    """
    if conflict.entity_type == 'CAR':
        try:
            car = CAR.objects.get(id=conflict.entity_id)
        except CAR.DoesNotExist:
            raise ValueError(f"CAR {conflict.entity_id} not found")

        old_status = car.status
        car.status = CARStatus.REWORK_REQUESTED
        car.rework_count += 1
        car.rework_reason = f"Sync conflict resolved via REOPEN_FOR_MERGE: {conflict.resolution_notes or 'No notes'}"
        car.rework_requested_by = resolved_by
        car.rework_requested_at = timezone.now()
        car.updated_by = resolved_by
        car.sync_version += 1
        car.save()

        AuditLog.objects.create(
            entity_type='CAR',
            entity_id=conflict.entity_id,
            action='UPDATE',
            field_name='status',
            old_value=old_status,
            new_value=CARStatus.REWORK_REQUESTED,
            performed_by=resolved_by,
        )

        logger.info(f"REOPEN_FOR_MERGE: CAR {conflict.entity_id} set to REWORK_REQUESTED")

    elif conflict.entity_type == 'INSPECTION':
        # For inspections, reopen to DRAFT
        try:
            inspection = Inspection.objects.get(id=conflict.entity_id)
        except Inspection.DoesNotExist:
            raise ValueError(f"Inspection {conflict.entity_id} not found")

        from apps.inspection.models import InspectionStatus
        old_status = inspection.status
        inspection.status = InspectionStatus.DRAFT
        inspection.updated_by = resolved_by
        inspection.sync_version += 1
        inspection.save()

        AuditLog.objects.create(
            entity_type='INSPECTION',
            entity_id=conflict.entity_id,
            action='UPDATE',
            field_name='status',
            old_value=old_status,
            new_value=InspectionStatus.DRAFT,
            performed_by=resolved_by,
        )

        logger.info(f"REOPEN_FOR_MERGE: Inspection {conflict.entity_id} set to DRAFT")
    else:
        logger.warning(
            f"REOPEN_FOR_MERGE not applicable for entity_type: {conflict.entity_type}. "
            f"Treating as KEEP_SERVER."
        )
