"""
Sync service for pull and push operations.

Per BACKEND_STRUCTURE.md Section 10.9 and PRD.md:
- FEAT-SYNC-002: Sync Pull (Server → Vessel) — delta sync using sync_version
- FEAT-SYNC-003: Sync Push (Vessel → Server) — process events, handle attachments

Pull: Returns all records where sync_version > last_server_version for the vessel.
Push: Processes CREATE/UPDATE/DELETE events, detects conflicts, returns id mappings.
"""

import logging
import uuid as uuid_module
from datetime import datetime, timedelta
from typing import Any

from django.core import signing
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.inspection.models import Inspection, InspectionReport
from apps.inspection.deficiency_models import Deficiency, CAR
from apps.car.models import CorrectiveAction, Evidence, ActivityHistory

from .models import (
    SyncLog,
    SyncLogDetail,
    SyncToken,
    SyncType,
    SyncStatus,
    SyncOperation,
    SyncDetailStatus,
)
from .serializers import (
    SyncInspectionSerializer,
    SyncInspectionReportSerializer,
    SyncDeficiencySerializer,
    SyncCARSerializer,
    SyncCorrectiveActionSerializer,
    SyncEvidenceSerializer,
    SyncActivityHistorySerializer,
)
from . import conflict_resolver

logger = logging.getLogger(__name__)

UPLOAD_TOKEN_SALT = 'psc.sync.upload'
UPLOAD_TOKEN_MAX_AGE_SECONDS = 3600

# Entity type to model mapping (for push processing)
ENTITY_MODEL_MAP = {
    'INSPECTION': Inspection,
    'DEFICIENCY': Deficiency,
    'CAR': CAR,
    'CORRECTIVE_ACTION': CorrectiveAction,
    'EVIDENCE': Evidence,
}

# Fields that should not be set from client data during push
PUSH_READONLY_FIELDS = {
    'id', 'created_date', 'created_by', 'sync_version',
    'car_number',  # Auto-generated
}


# =============================================================================
# PULL — Server → Vessel (Delta Sync)
# =============================================================================

def pull_changes(
    vessel_id,
    last_server_version: int,
    last_sync_token=None,
    user_id: str = '',
) -> dict:
    """
    Pull changes from server for a vessel since last_server_version.

    Per FEAT-SYNC-002:
    - Delta sync using last_server_version
    - Include inspections, deficiencies, CARs, corrective_actions,
      evidence_metadata, activity_history, masters
    - Handle deleted records (included with is_deleted=True)

    Args:
        vessel_id: UUID of the vessel
        last_server_version: Version to sync from (0 = full sync)
        last_sync_token: Previous sync token UUID (for idempotency tracking)
        user_id: ID of user performing the sync

    Returns:
        Dict with data, sync_token, and server_version
    """
    sync_id = uuid_module.uuid4()
    now = timezone.now()

    # Create sync log
    sync_log = SyncLog.objects.create(
        vessel_id=vessel_id,
        sync_id=sync_id,
        sync_type=SyncType.PULL,
        sync_status=SyncStatus.IN_PROGRESS,
        started_at=now,
        created_by=user_id,
    )

    try:
        # Query changed records for this vessel
        inspections = Inspection.objects.filter(
            vessel_id=vessel_id,
            sync_version__gt=last_server_version,
        )

        inspection_reports = InspectionReport.objects.filter(
            inspection__vessel_id=vessel_id,
            inspection__sync_version__gt=last_server_version,
        )

        deficiencies = Deficiency.objects.filter(
            inspection__vessel_id=vessel_id,
            sync_version__gt=last_server_version,
        )

        cars = CAR.objects.filter(
            deficiency__inspection__vessel_id=vessel_id,
            sync_version__gt=last_server_version,
        )

        corrective_actions = CorrectiveAction.objects.filter(
            car__deficiency__inspection__vessel_id=vessel_id,
            sync_version__gt=last_server_version,
        )

        evidence = Evidence.objects.filter(
            car__deficiency__inspection__vessel_id=vessel_id,
            uploaded_at__gt=_version_to_datetime(last_server_version, vessel_id),
        )

        activity_history = ActivityHistory.objects.filter(
            vessel_id=vessel_id,
            performed_at__gt=_version_to_datetime(last_server_version, vessel_id),
        )

        # Serialize data
        data = {
            'inspections': SyncInspectionSerializer(inspections, many=True).data,
            'inspection_reports': SyncInspectionReportSerializer(inspection_reports, many=True).data,
            'deficiencies': SyncDeficiencySerializer(deficiencies, many=True).data,
            'cars': SyncCARSerializer(cars, many=True).data,
            'corrective_actions': SyncCorrectiveActionSerializer(corrective_actions, many=True).data,
            'evidence_metadata': SyncEvidenceSerializer(evidence, many=True).data,
            'activity_history': SyncActivityHistorySerializer(activity_history, many=True).data,
            # FEAT-SYNC-002 response contract includes master data bucket.
            'masters': {
                'def_codes': [],
                'action_codes': [],
                'mou': [],
                'clc_items': [],
            },
        }

        # Compute current max server version across all synced entities
        max_version = _get_max_server_version(vessel_id)

        # Count total records
        total_records = 0
        for value in data.values():
            if isinstance(value, dict):
                total_records += sum(len(items) for items in value.values())
            else:
                total_records += len(value)

        # Update sync log
        sync_log.sync_status = SyncStatus.COMPLETED
        sync_log.completed_at = timezone.now()
        sync_log.records_sent = total_records
        sync_log.save()

        # Update or create sync token for this vessel
        SyncToken.objects.update_or_create(
            vessel_id=vessel_id,
            defaults={
                'last_sync_at': now,
                'last_sync_id': sync_id,
                'last_server_version': max_version,
            }
        )

        logger.info(
            f"Pull complete for vessel {vessel_id}: "
            f"{total_records} records since version {last_server_version}"
        )

        return {
            'data': data,
            'sync_token': str(sync_id),
            'server_version': max_version,
        }

    except Exception as e:
        sync_log.sync_status = SyncStatus.FAILED
        sync_log.error_message = str(e)
        sync_log.completed_at = timezone.now()
        sync_log.save()
        logger.error(f"Pull failed for vessel {vessel_id}: {e}")
        raise


def _version_to_datetime(last_server_version: int, vessel_id) -> Any:
    """
    Convert last_server_version to a datetime for non-versioned tables
    (Evidence, ActivityHistory don't have sync_version).
    Falls back to the sync token's last_sync_at if available.
    """
    if last_server_version == 0:
        # Full sync — return epoch
        return timezone.make_aware(datetime(2000, 1, 1))

    try:
        token = SyncToken.objects.get(vessel_id=vessel_id)
        return token.last_sync_at
    except SyncToken.DoesNotExist:
        return timezone.make_aware(datetime(2000, 1, 1))


def _get_max_server_version(vessel_id) -> int:
    """
    Get the maximum sync_version across all entity tables for a vessel.
    This becomes the new server_version for the sync token.
    """
    versions = []

    insp_max = Inspection.objects.filter(
        vessel_id=vessel_id
    ).aggregate(max_v=Max('sync_version'))['max_v']
    if insp_max:
        versions.append(insp_max)

    def_max = Deficiency.objects.filter(
        inspection__vessel_id=vessel_id
    ).aggregate(max_v=Max('sync_version'))['max_v']
    if def_max:
        versions.append(def_max)

    car_max = CAR.objects.filter(
        deficiency__inspection__vessel_id=vessel_id
    ).aggregate(max_v=Max('sync_version'))['max_v']
    if car_max:
        versions.append(car_max)

    action_max = CorrectiveAction.objects.filter(
        car__deficiency__inspection__vessel_id=vessel_id
    ).aggregate(max_v=Max('sync_version'))['max_v']
    if action_max:
        versions.append(action_max)

    return max(versions) if versions else 0


# =============================================================================
# PUSH — Vessel → Server (Process Events)
# =============================================================================

@transaction.atomic
def push_changes(
    sync_id,
    vessel_id,
    checksum: str,
    events: list[dict],
    attachments: list[dict],
    user_id: str = '',
) -> dict:
    """
    Push changes from vessel to server.

    Per FEAT-SYNC-003:
    - Process events in order (CREATE/UPDATE/DELETE)
    - Detect conflicts per event (FEAT-SYNC-004)
    - Generate presigned URLs for attachments
    - Return id_mappings (client_id → server_id)

    Args:
        sync_id: Idempotency key UUID
        vessel_id: UUID of the vessel
        checksum: SHA-256 checksum of the payload
        events: List of sync event dicts
        attachments: List of attachment metadata dicts
        user_id: ID of user performing the sync

    Returns:
        Dict with sync_id, processed count, conflicts, id_mappings, upload URLs
    """
    now = timezone.now()

    # Idempotency check — if this sync_id already processed, return cached result
    existing_log = SyncLog.objects.filter(sync_id=sync_id).first()
    if existing_log and existing_log.sync_status == SyncStatus.COMPLETED:
        logger.info(f"Duplicate push sync_id={sync_id}, returning cached result")
        return _build_push_response(sync_id, existing_log)

    # Create sync log
    sync_log = SyncLog.objects.create(
        vessel_id=vessel_id,
        sync_id=sync_id,
        sync_type=SyncType.PUSH,
        sync_status=SyncStatus.IN_PROGRESS,
        started_at=now,
        payload_checksum=checksum,
        records_received=len(events),
        created_by=user_id,
    )

    processed = 0
    failed = 0
    conflicts = []
    id_mappings = {}

    try:
        for event in events:
            try:
                result = _process_event(
                    sync_log=sync_log,
                    vessel_id=vessel_id,
                    event=event,
                    user_id=user_id,
                )
                if result.get('conflict'):
                    conflicts.append(result['conflict'])
                elif result.get('id_mapping'):
                    client_id, server_id = result['id_mapping']
                    id_mappings[str(client_id)] = str(server_id)
                processed += 1
            except Exception as e:
                failed += 1
                logger.error(
                    f"Failed to process event {event.get('event_id')}: {e}"
                )
                SyncLogDetail.objects.create(
                    sync_log=sync_log,
                    entity_type=event.get('entity_type', 'UNKNOWN'),
                    entity_id=event.get('entity_id', uuid_module.uuid4()),
                    client_id=event.get('client_id'),
                    operation=event.get('operation', 'UPDATE'),
                    sync_status=SyncDetailStatus.FAILED,
                    error_message=str(e),
                    client_version=event.get('client_version', 0),
                )

        # Generate upload URLs for attachments
        attachment_upload_urls = _generate_upload_urls(attachments, sync_id)

        # Update sync log
        sync_log.sync_status = SyncStatus.COMPLETED
        sync_log.completed_at = timezone.now()
        sync_log.save()

        logger.info(
            f"Push complete for vessel {vessel_id}: "
            f"processed={processed}, failed={failed}, conflicts={len(conflicts)}"
        )

        return {
            'sync_id': str(sync_id),
            'processed': processed,
            'failed': failed,
            'conflicts': conflicts,
            'id_mappings': id_mappings,
            'attachment_upload_urls': attachment_upload_urls,
        }

    except Exception as e:
        sync_log.sync_status = SyncStatus.FAILED
        sync_log.error_message = str(e)
        sync_log.completed_at = timezone.now()
        sync_log.save()
        logger.error(f"Push failed for vessel {vessel_id}: {e}")
        raise


def _process_event(
    sync_log: SyncLog,
    vessel_id,
    event: dict,
    user_id: str,
) -> dict:
    """
    Process a single sync event (CREATE, UPDATE, or DELETE).

    Returns dict with either 'conflict' or 'id_mapping' key.
    """
    entity_type = event['entity_type']
    entity_id = event.get('entity_id')
    client_id = event.get('client_id')
    operation = event['operation']
    client_version = event.get('client_version', 1)
    data = event.get('data', {})

    model = ENTITY_MODEL_MAP.get(entity_type)
    if not model:
        raise ValueError(f"Unknown entity_type: {entity_type}")

    result = {}

    if operation == SyncOperation.CREATE:
        result = _process_create(
            model, entity_type, entity_id, client_id, data, vessel_id, user_id
        )
    elif operation == SyncOperation.UPDATE:
        result = _process_update(
            model, entity_type, entity_id, client_id, client_version,
            data, vessel_id, user_id
        )
    elif operation == SyncOperation.DELETE:
        result = _process_delete(
            model, entity_type, entity_id, user_id
        )
    else:
        raise ValueError(f"Unknown operation: {operation}")

    # Create sync log detail
    SyncLogDetail.objects.create(
        sync_log=sync_log,
        entity_type=entity_type,
        entity_id=result.get('server_id', entity_id or uuid_module.uuid4()),
        client_id=client_id,
        operation=operation,
        sync_status=(
            SyncDetailStatus.CONFLICT if result.get('conflict')
            else SyncDetailStatus.SUCCESS
        ),
        server_version=result.get('server_version'),
        client_version=client_version,
    )

    return result


def _process_create(
    model, entity_type: str, entity_id, client_id, data: dict,
    vessel_id, user_id: str,
) -> dict:
    """Process a CREATE event. Returns id_mapping if client_id differs from server_id."""
    # Check if already exists (by client_id) to prevent duplicates
    if client_id:
        existing = model.objects.filter(client_id=client_id).first()
        if existing:
            logger.info(f"Duplicate create: {entity_type} client_id={client_id} already exists")
            return {
                'id_mapping': (client_id, existing.id),
                'server_id': existing.id,
                'server_version': getattr(existing, 'sync_version', 1),
            }

    # Filter writable fields
    create_data = _filter_writable_fields(model, data)
    create_data['client_id'] = client_id
    create_data['created_by'] = user_id

    # Set vessel_id if model has it
    if hasattr(model, 'vessel_id'):
        create_data['vessel_id'] = vessel_id

    instance = model.objects.create(**create_data)

    return {
        'id_mapping': (client_id, instance.id) if client_id else None,
        'server_id': instance.id,
        'server_version': getattr(instance, 'sync_version', 1),
    }


def _process_update(
    model, entity_type: str, entity_id, client_id, client_version: int,
    data: dict, vessel_id, user_id: str,
) -> dict:
    """Process an UPDATE event. Detects conflicts if versions mismatch."""
    # Find the record — by entity_id or client_id
    instance = None
    if entity_id:
        instance = model.objects.filter(id=entity_id).first()
    if not instance and client_id:
        instance = model.objects.filter(client_id=client_id).first()

    if not instance:
        raise ValueError(
            f"{entity_type} not found: entity_id={entity_id}, client_id={client_id}"
        )

    # Conflict detection per FEAT-SYNC-004
    server_version = getattr(instance, 'sync_version', 1)
    if client_version < server_version:
        # Conflict detected — create conflict record
        from .serializers import SyncInspectionSerializer, SyncCARSerializer

        serializer_map = {
            'INSPECTION': SyncInspectionSerializer,
            'DEFICIENCY': SyncDeficiencySerializer,
            'CAR': SyncCARSerializer,
            'CORRECTIVE_ACTION': SyncCorrectiveActionSerializer,
        }

        ser_class = serializer_map.get(entity_type)
        if ser_class:
            server_data = dict(ser_class(instance).data)
        else:
            server_data = {'id': str(instance.id)}

        conflict = conflict_resolver.create_conflict_record(
            vessel_id=vessel_id,
            entity_type=entity_type,
            entity_id=instance.id,
            server_data=server_data,
            vessel_data=data,
        )

        return {
            'conflict': str(conflict.id),
            'server_id': instance.id,
            'server_version': server_version,
        }

    # No conflict — apply update
    update_data = _filter_writable_fields(model, data)
    for field_name, value in update_data.items():
        setattr(instance, field_name, value)

    instance.updated_by = user_id
    if hasattr(instance, 'sync_version'):
        instance.sync_version += 1

    instance.save()

    return {
        'server_id': instance.id,
        'server_version': getattr(instance, 'sync_version', 1),
    }


def _process_delete(
    model, entity_type: str, entity_id, user_id: str,
) -> dict:
    """Process a DELETE event. Soft-deletes the record."""
    try:
        instance = model.objects.get(id=entity_id)
    except model.DoesNotExist:
        logger.warning(f"Delete target not found: {entity_type} {entity_id}")
        return {'server_id': entity_id, 'server_version': 0}

    instance.is_deleted = True
    instance.updated_by = user_id
    if hasattr(instance, 'sync_version'):
        instance.sync_version += 1
    instance.save()

    return {
        'server_id': instance.id,
        'server_version': getattr(instance, 'sync_version', 1),
    }


def _filter_writable_fields(model, data: dict) -> dict:
    """Filter data dict to only include valid, writable model fields."""
    field_names = {f.name for f in model._meta.get_fields() if hasattr(f, 'column')}
    return {
        k: v for k, v in data.items()
        if k in field_names and k not in PUSH_READONLY_FIELDS
    }


def _generate_upload_urls(
    attachments: list[dict],
    sync_id,
) -> list[dict]:
    """
    Generate upload URLs for attachment files.

    Per BACKEND_STRUCTURE.md Section 10.9:
    Returns list of {client_id, upload_url, expires_at}.

    Note: In production, these would be presigned S3/Azure URLs.
    For now, we generate internal upload endpoints with token-based auth.
    """
    urls = []
    expires_at = timezone.now() + timedelta(seconds=UPLOAD_TOKEN_MAX_AGE_SECONDS)

    for attachment in attachments:
        upload_token = signing.dumps(
            {
                'sync_id': str(sync_id),
                'client_id': str(attachment.get('client_id', '')),
            },
            salt=UPLOAD_TOKEN_SALT,
        )
        urls.append({
            'client_id': str(attachment.get('client_id', '')),
            'upload_url': f"/api/psc/sync/upload/{upload_token}/",
            'expires_at': expires_at.isoformat(),
        })

    return urls


def _build_push_response(sync_id, sync_log: SyncLog) -> dict:
    """Build response from an already-completed push (for idempotency)."""
    details = SyncLogDetail.objects.filter(sync_log=sync_log)
    id_mappings = {}
    conflicts = []

    for detail in details:
        if detail.sync_status == SyncDetailStatus.CONFLICT:
            conflicts.append(str(detail.entity_id))
        elif detail.client_id and detail.entity_id:
            id_mappings[str(detail.client_id)] = str(detail.entity_id)

    return {
        'sync_id': str(sync_id),
        'processed': details.filter(sync_status=SyncDetailStatus.SUCCESS).count(),
        'failed': details.filter(sync_status=SyncDetailStatus.FAILED).count(),
        'conflicts': conflicts,
        'id_mappings': id_mappings,
        'attachment_upload_urls': [],
    }
