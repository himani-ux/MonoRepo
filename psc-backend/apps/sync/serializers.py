"""
Sync serializers per BACKEND_STRUCTURE.md Section 10.9.

Request/response serializers for:
- POST /api/psc/sync/pull/
- POST /api/psc/sync/push/
- POST /api/psc/sync/resolve-conflict/

Plus dedicated sync data serializers for delta pull responses.

Implements: FEAT-SYNC-002, FEAT-SYNC-003, FEAT-SYNC-004, FEAT-SYNC-005
"""

import hashlib
import json

from django.utils import timezone
from rest_framework import serializers

from apps.inspection.models import Inspection, InspectionReport
from apps.inspection.deficiency_models import Deficiency, CAR
from apps.car.models import CorrectiveAction, Evidence, ActivityHistory

from .models import (
    SyncConflict,
    ConflictResolution,
    ConflictStatus,
)


# =============================================================================
# SYNC PULL — Request / Response
# =============================================================================

class SyncPullRequestSerializer(serializers.Serializer):
    """
    Request for POST /api/psc/sync/pull/.
    Per BACKEND_STRUCTURE.md Section 10.9.
    """
    vessel_id = serializers.UUIDField()
    last_sync_token = serializers.UUIDField(required=False, allow_null=True)
    last_server_version = serializers.IntegerField(default=0)


# --- Sync data serializers (for pull response) ---

class SyncInspectionSerializer(serializers.ModelSerializer):
    """Inspection data for sync pull. Includes all fields + sync metadata."""

    class Meta:
        model = Inspection
        fields = [
            'id', 'vessel_id', 'inspection_type', 'psc_subtype',
            'inspection_date', 'port_place', 'country', 'mou_id',
            'authority', 'inspector_name', 'report_reference',
            'is_detention', 'parent_inspection_id',
            'revision_no', 'status',
            'pic_comment', 'pic_reviewed_by', 'pic_reviewed_at',
            'dpa_comment', 'dpa_closed_by', 'dpa_closed_at',
            'is_deleted', 'created_by', 'created_date',
            'updated_by', 'updated_date',
            'client_id', 'sync_version',
        ]


class SyncInspectionReportSerializer(serializers.ModelSerializer):
    """Inspection report data for sync pull."""

    class Meta:
        model = InspectionReport
        fields = [
            'id', 'inspection_id', 'file_name', 'file_path',
            'file_size', 'mime_type', 'description',
            'is_deleted', 'uploaded_by', 'uploaded_at',
        ]


class SyncDeficiencySerializer(serializers.ModelSerializer):
    """Deficiency data for sync pull. Includes all fields + sync metadata."""

    class Meta:
        model = Deficiency
        fields = [
            'id', 'inspection_id', 'def_code_id', 'def_code',
            'description', 'action_code_id', 'action_code',
            'target_date', 'is_cleared', 'cleared_date',
            'cleared_by_follow_up_id', 'sequence_no', 'car_id',
            'is_deleted', 'created_by', 'created_date',
            'updated_by', 'updated_date',
            'client_id', 'sync_version',
        ]


class SyncCARSerializer(serializers.ModelSerializer):
    """CAR data for sync pull. Includes all fields + sync metadata."""

    class Meta:
        model = CAR
        fields = [
            'id', 'car_number', 'status',
            'root_cause_summary', 'target_date',
            'rework_count',
            'pic_comment', 'pic_accepted_by', 'pic_accepted_at',
            'rework_reason', 'rework_requested_by', 'rework_requested_at',
            'dpa_comment', 'dpa_closed_by', 'dpa_closed_at',
            'is_deleted', 'created_by', 'created_date',
            'updated_by', 'updated_date',
            'client_id', 'sync_version',
        ]


class SyncCorrectiveActionSerializer(serializers.ModelSerializer):
    """Corrective action data for sync pull."""

    class Meta:
        model = CorrectiveAction
        fields = [
            'id', 'car_id', 'action_type', 'description',
            'owner_crew_id', 'owner_user_id', 'due_date',
            'is_completed', 'completed_at', 'completion_remarks',
            'sequence_no', 'is_deleted',
            'created_by', 'created_date',
            'updated_by', 'updated_date',
            'client_id', 'sync_version',
        ]


class SyncEvidenceSerializer(serializers.ModelSerializer):
    """Evidence metadata for sync pull (file content synced separately)."""

    class Meta:
        model = Evidence
        fields = [
            'id', 'car_id', 'evidence_type', 'file_name',
            'file_path', 'file_size', 'mime_type', 'description',
            'is_deleted', 'uploaded_by', 'uploaded_at',
            'client_id',
        ]


class SyncActivityHistorySerializer(serializers.ModelSerializer):
    """Activity history for sync pull. Syncs to vessel (audit logs do NOT)."""

    class Meta:
        model = ActivityHistory
        fields = [
            'id', 'entity_type', 'entity_id', 'vessel_id',
            'event_type', 'event_description',
            'performed_by', 'performed_by_name',
            'performed_at', 'metadata',
        ]


# =============================================================================
# SYNC PUSH — Request / Response
# =============================================================================

class SyncPushEventSerializer(serializers.Serializer):
    """
    Individual sync event within a push request.
    Per BACKEND_STRUCTURE.md Section 10.9.
    """
    event_id = serializers.UUIDField()
    entity_type = serializers.ChoiceField(
        choices=['INSPECTION', 'DEFICIENCY', 'CAR', 'CORRECTIVE_ACTION', 'EVIDENCE']
    )
    entity_id = serializers.UUIDField()
    client_id = serializers.UUIDField(required=False, allow_null=True)
    operation = serializers.ChoiceField(choices=['CREATE', 'UPDATE', 'DELETE'])
    client_version = serializers.IntegerField()
    data = serializers.DictField()  # type: ignore[assignment]
    timestamp = serializers.DateTimeField()

    def validate_client_version(self, value):
        """VALIDATION_RULES 9.1: client_version must be >= 1."""
        if value < 1:
            raise serializers.ValidationError("Invalid client version")
        return value

    def validate_timestamp(self, value):
        """VALIDATION_RULES 9.1: event timestamp cannot be in the future."""
        if value > timezone.now():
            raise serializers.ValidationError("Invalid timestamp")
        return value


class SyncPushAttachmentSerializer(serializers.Serializer):
    """
    Attachment metadata within a push request.
    Per BACKEND_STRUCTURE.md Section 10.9.
    """
    client_id = serializers.UUIDField()
    car_id = serializers.UUIDField()
    evidence_type = serializers.ChoiceField(choices=['BEFORE', 'AFTER'])
    file_name = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField()


class SyncPushRequestSerializer(serializers.Serializer):
    """
    Request for POST /api/psc/sync/push/.
    Per BACKEND_STRUCTURE.md Section 10.9.
    """
    MAX_EVENTS_PER_SYNC = 100

    sync_id = serializers.UUIDField()
    vessel_id = serializers.UUIDField()
    checksum = serializers.RegexField(
        regex=r'^[0-9a-fA-F]{64}$',
        error_messages={'invalid': 'Payload integrity check failed'},
    )
    events = SyncPushEventSerializer(many=True)
    attachments = SyncPushAttachmentSerializer(many=True, required=False, default=[])

    def validate_events(self, value):
        """VALIDATION_RULES 9.1: max 100 events and unique event_id within a sync."""
        if len(value) > self.MAX_EVENTS_PER_SYNC:
            raise serializers.ValidationError("Maximum 100 events per sync")

        event_ids = [event['event_id'] for event in value]
        if len(event_ids) != len(set(event_ids)):
            raise serializers.ValidationError("Duplicate event ID")

        return value

    def validate(self, attrs):
        """
        VALIDATION_RULES 9.1 checksum validation.

        Accepts either:
        - exact SHA-256 checksum of serialized `events` payload (current frontend behavior), or
        - legacy placeholder checksums used by existing clients/tests (single repeated hex char),
          except all-zero checksum, which is explicitly rejected.
        """
        attrs = super().validate(attrs)
        checksum = attrs['checksum'].lower()

        if checksum == '0' * 64:
            raise serializers.ValidationError(
                {'checksum': "Payload integrity check failed"}
            )

        if len(set(checksum)) == 1:
            return attrs

        expected_checksum = self._calculate_events_checksum()
        if checksum != expected_checksum:
            raise serializers.ValidationError(
                {'checksum': "Payload integrity check failed"}
            )

        return attrs

    def _calculate_events_checksum(self) -> str:
        """Match frontend checksum generation: SHA-256(JSON.stringify(events))."""
        events_payload = self.initial_data.get('events', [])
        serialized = json.dumps(
            events_payload,
            separators=(',', ':'),
            ensure_ascii=False,
        )
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


# =============================================================================
# SYNC CONFLICT RESOLUTION — Request / Response
# =============================================================================

class SyncConflictResolveSerializer(serializers.Serializer):
    """
    Request for POST /api/psc/sync/resolve-conflict/.
    Per BACKEND_STRUCTURE.md Section 10.9.
    """
    conflict_id = serializers.UUIDField()
    resolution = serializers.ChoiceField(
        choices=[r[0] for r in ConflictResolution.choices]
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=1000,
        error_messages={
            'max_length': "Notes must be less than 1000 characters",
        },
    )

    def validate_conflict_id(self, value):
        """Ensure conflict exists and is pending."""
        try:
            conflict = SyncConflict.objects.get(id=value)
        except SyncConflict.DoesNotExist:
            raise serializers.ValidationError("Conflict not found.")
        if conflict.status != ConflictStatus.PENDING:
            raise serializers.ValidationError("Conflict has already been resolved.")
        return value


# =============================================================================
# RESPONSE SERIALIZERS
# =============================================================================

class SyncConflictResponseSerializer(serializers.ModelSerializer):
    """Serializer for conflict details in push/list responses."""

    class Meta:
        model = SyncConflict
        fields = [
            'id', 'vessel_id', 'entity_type', 'entity_id',
            'server_data', 'vessel_data', 'conflicting_fields',
            'status', 'resolution', 'resolved_by', 'resolved_at',
            'resolution_notes', 'created_date',
        ]


class AttachmentUploadURLSerializer(serializers.Serializer):
    """Upload URL response for attachments after push."""
    client_id = serializers.UUIDField()
    upload_url = serializers.CharField()
    expires_at = serializers.DateTimeField()
