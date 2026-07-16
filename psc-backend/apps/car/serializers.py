"""
CAR serializers per BACKEND_STRUCTURE.md Sections 10.5-10.8.

Serializers:
- CARListSerializer: Summary for list view with counts
- CARDetailSerializer: Full detail with nested actions, evidence, history
- CARUpdateSerializer: Update root cause, CLC items, target date
- CARSubmitSerializer: Validate submission preconditions
- CARPICAcceptSerializer: PIC accept with mandatory comment
- CARReworkSerializer: Rework with reason (min 20 chars)
- CARDPACloseSerializer: DPA close with mandatory comment
- CARReopenSerializer: Reopen with mandatory reason
- CorrectiveActionSerializer: Read serializer
- CorrectiveActionCreateSerializer: Create action
- CorrectiveActionUpdateSerializer: Update action
- CorrectiveActionCompleteSerializer: Mark action complete
- EvidenceSerializer: Read serializer
- EvidenceUploadSerializer: Upload with file validation
- PhysicalVerificationSerializer: Read serializer
- PhysicalVerificationCreateSerializer: Create PV
- PhysicalVerificationCloseSerializer: Close PV
- ActivityHistorySerializer: Activity history read
- AuditLogSerializer: Audit log read (Office only)
"""

import re
from datetime import date
from typing import Any

from django.conf import settings
from django.db import DatabaseError, connection
from django.db.models import Q
from rest_framework import serializers

from apps.inspection.deficiency_models import (
    CAR,
    CARStatus,
    Deficiency,
)
from apps.masters.models import PSCActionCode, PSCDefCode
from .models import (
    CorrectiveAction,
    ActionType,
    Evidence,
    EvidenceType,
    CarClcMapping,
    ActivityHistory,
    AuditLog,
    PhysicalVerification,
    PVStatus,
)


def _fetch_active_master_clc_ids(clc_item_ids):
    """
    Resolve active CLC codes from the CLC_Item master table.

    clc_item_ids are CLC_Code strings (e.g. '2-1', 'P3') referencing CLC_Item.CLC_Code.
    """
    if not clc_item_ids:
        return set()

    normalized_ids = [str(clc_id) for clc_id in clc_item_ids]
    placeholders = ", ".join(["%s"] * len(normalized_ids))
    query = (
        f"SELECT CLC_Code FROM CLC_Item "
        f"WHERE Is_Active = 1 AND CLC_Code IN ({placeholders})"
    )

    with connection.cursor() as cursor:
        cursor.execute(query, normalized_ids)
        return {str(row[0]) for row in cursor.fetchall()}


INTERNAL_CORRECTIVE_ACTION_PATTERN = re.compile(
    r"""
    (
        inspection\s*create\s*(?:->|→)\s*submit\s*(?:->|→)\s*review\s*(?:->|→)\s*close
        | car\s*submit\s*(?:->|→)\s*(?:accept|accept/rework|rework)\s*(?:->|→)\s*close
        | sync\s+conflict\s+resolution
        | \b(?:PIC_REVIEW|SUBMITTED_TO_PIC|SUBMITTED_TO_DPA|RETURNED_FOR_REWORK)\b\s*(?:->|→)\s*\b[A-Z_]+\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
APPENDED_COMMENT_SPLIT_RE = re.compile(r"\s+(?:\u2014|-)\s+")
PIC_REVIEW_HISTORY_EVENT_TYPES = (
    'CAR_WORKFLOW_START_PIC_REVIEW',
    'CAR_PIC_ACCEPTED',
)


def _contains_internal_system_text(value: str | None) -> bool:
    """Detect internal workflow/system text that must not be user-facing."""
    text = (value or '').strip()
    if not text:
        return False
    return bool(INTERNAL_CORRECTIVE_ACTION_PATTERN.search(text))


def _extract_appended_comment(event_description: str | None) -> str:
    """Extract a user comment appended to an activity description."""
    text = (event_description or '').strip()
    if not text:
        return ''

    parts = APPENDED_COMMENT_SPLIT_RE.split(text, maxsplit=1)
    if len(parts) != 2:
        return ''
    return parts[1].strip()


def _resolve_pic_review_comment_value(
    *,
    stored_comment: str | None,
    review_comment: str | None,
    last_action: str | None,
    last_action_comment: str | None,
) -> str | None:
    """
    Resolve the correct PIC review comment for detail/report output.

    Prefer the dedicated CAR.pic_comment field unless it was clearly overwritten
    by a later workflow action. Activity-history comments are capped by the
    500-char event_description column, so they can be truncated for long input.
    """
    stored = (stored_comment or '').strip()
    review = (review_comment or '').strip()
    if not review:
        return stored or None
    if not stored:
        return review
    if stored == review:
        return stored

    # Long comments can be truncated in psc_activity_history.event_description.
    if stored.startswith(review) and len(stored) > len(review):
        return stored
    if review.startswith(stored) and len(review) > len(stored):
        return review

    normalized_last_action = str(last_action or '').strip().upper()
    latest_comment = (last_action_comment or '').strip()
    if (
        normalized_last_action
        and normalized_last_action != 'START_PIC_REVIEW'
        and latest_comment
        and latest_comment == stored
    ):
        return review

    return stored


def _lookup_def_code_title(def_code_id: str | None) -> str | None:
    """Resolve deficiency title from PSCDefCode master data."""
    if not def_code_id:
        return None
    try:
        row = PSCDefCode.objects.get(def_code=def_code_id)
        return row.def_name
    except Exception:
        return None


def _lookup_action_code_definition(action_code_id: int | None) -> str | None:
    """Resolve action code definition from PSCActionCode master data."""
    if not action_code_id:
        return None
    try:
        row = PSCActionCode.objects.get(action_code=action_code_id)
        return row.definition
    except Exception:
        return None


def _resolve_initial_action_code(car: CAR, deficiency: Deficiency) -> str | None:
    """Resolve immutable initial action code with safe fallback for legacy records."""
    snapshot = (car.initial_action_code or '').strip()
    if snapshot:
        return snapshot

    first_change = deficiency.action_history.order_by('changed_at').first()
    if first_change:
        if first_change.previous_action_code:
            return first_change.previous_action_code
        if first_change.new_action_code:
            return first_change.new_action_code

    return deficiency.action_code or None


def _resolve_action_code_change_note(
    deficiency: Deficiency,
    current_action_code: str | None,
    initial_action_code: str | None,
) -> dict[str, Any] | None:
    """Resolve latest action-code change note using existing deficiency history."""
    if not current_action_code or not initial_action_code:
        return None
    if str(current_action_code) == str(initial_action_code):
        return None

    latest = deficiency.action_history.filter(
        new_action_code=current_action_code
    ).order_by('-changed_at').first()
    if not latest:
        latest = deficiency.action_history.order_by('-changed_at').first()
    if not latest:
        return None

    return {
        'from': latest.previous_action_code or initial_action_code,
        'to': latest.new_action_code or current_action_code,
        'changed_at': latest.changed_at,
        'changed_by': latest.changed_by or '',
        'reason': latest.change_reason or '',
    }


# =============================================================================
# ACTIVITY & AUDIT SERIALIZERS
# =============================================================================

class ActivityHistorySerializer(serializers.ModelSerializer):
    """Serializer for activity history timeline."""

    class Meta:
        model = ActivityHistory
        fields = [
            'id',
            'entity_type',
            'entity_id',
            'event_type',
            'event_description',
            'performed_by',
            'performed_by_name',
            'performed_at',
            'metadata',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log (Office/DPA only)."""

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'entity_type',
            'entity_id',
            'action',
            'field_name',
            'old_value',
            'new_value',
            'performed_by',
            'performed_by_role',
            'performed_at',
            'is_office_edit_assist',
        ]


# =============================================================================
# CORRECTIVE ACTION SERIALIZERS
# =============================================================================

class CorrectiveActionSerializer(serializers.ModelSerializer):
    """Read serializer for corrective actions."""
    action_type_display = serializers.CharField(
        source='get_action_type_display', read_only=True
    )
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = CorrectiveAction
        fields = [
            'id',
            'car_id',
            'action_type',
            'action_type_display',
            'description',
            'owner_crew_id',
            'owner_user_id',
            'owner_name',
            'due_date',
            'is_completed',
            'completed_at',
            'completion_remarks',
            'sequence_no',
            'created_by',
            'created_date',
        ]

    def get_owner_name(self, obj):
        """Resolve owner name from crew or office user.

        Uses CAST workaround for HRM501 (unmanaged uniqueidentifier PK).
        """
        if obj.owner_crew_id:
            try:
                from apps.accounts.utils import get_crew_display_name

                display_name = get_crew_display_name(obj.owner_crew_id)
                if display_name:
                    return display_name
            except Exception:
                return str(obj.owner_crew_id)
        if obj.owner_user_id:
            try:
                from apps.accounts.models import OfficeUser
                user = OfficeUser.objects.filter(
                    employee_id=obj.owner_user_id, is_deleted=False
                ).first()
                if user:
                    return user.full_name
            except Exception:
                return obj.owner_user_id
        return None


class CorrectiveActionCreateSerializer(serializers.Serializer):
    """
    Create corrective action.
    Per BACKEND_STRUCTURE.md Section 10.6
    """
    action_type = serializers.ChoiceField(choices=ActionType.choices)
    description = serializers.CharField(min_length=10)
    owner_crew_id = serializers.UUIDField(required=False, allow_null=True)
    owner_user_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    client_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_description(self, value):
        """Block internal/system workflow text from being saved as corrective actions."""
        if _contains_internal_system_text(value):
            raise serializers.ValidationError(
                "Corrective action text appears to be internal/system workflow content."
            )
        return value

    def validate_owner_user_id(self, value):
        """Normalize owner_user_id and reject blank-only values."""
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    def validate_due_date(self, value):
        """Due date, if provided, must be today or in the future."""
        if value and value < date.today():
            raise serializers.ValidationError("Due date must be today or in the future")
        return value

    def validate(self, attrs):
        # Owner and due_date are optional for action create; normalize only.
        return attrs


class CorrectiveActionUpdateSerializer(serializers.Serializer):
    """Update corrective action."""
    description = serializers.CharField(min_length=10, required=False)
    owner_crew_id = serializers.UUIDField(required=False, allow_null=True)
    owner_user_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    due_date = serializers.DateField(required=False, allow_null=True)

    def validate_description(self, value):
        """Block internal/system workflow text from being saved as corrective actions."""
        if _contains_internal_system_text(value):
            raise serializers.ValidationError(
                "Corrective action text appears to be internal/system workflow content."
            )
        return value

    def validate_due_date(self, value):
        """Due date, if provided, must be today or in the future."""
        if value and value < date.today():
            raise serializers.ValidationError("Due date must be today or in the future")
        return value


class CorrectiveActionCompleteSerializer(serializers.Serializer):
    """
    Mark corrective action as completed.
    Per BACKEND_STRUCTURE.md Section 10.6
    """
    completion_remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=4000,
    )


# =============================================================================
# EVIDENCE SERIALIZERS
# =============================================================================

class EvidenceSerializer(serializers.ModelSerializer):
    """Read serializer for evidence files."""
    evidence_type_display = serializers.CharField(
        source='get_evidence_type_display', read_only=True
    )
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Evidence
        fields = [
            'id',
            'car_id',
            'evidence_type',
            'evidence_type_display',
            'file_name',
            'file_path',
            'preview_url',
            'file_size',
            'mime_type',
            'description',
            'uploaded_by',
            'uploaded_at',
        ]

    def get_preview_url(self, obj):
        """
        Build a browser-friendly URL for previewing evidence via API endpoint.
        This avoids runtime path mismatches for /uploads static serving.
        """
        request = self.context.get('request')
        api_path = f"/api/psc/evidence/{obj.id}/view/"
        if request:
            return request.build_absolute_uri(api_path)
        return api_path


class EvidenceUploadSerializer(serializers.Serializer):
    """
    Upload evidence file.
    Per BACKEND_STRUCTURE.md Section 10.7

    Validation:
    - File max 3MB
    - PDF/JPG/JPEG only
    - Description mandatory
    """
    file = serializers.FileField()
    evidence_type = serializers.ChoiceField(choices=EvidenceType.choices)
    description = serializers.CharField(min_length=5, max_length=500)
    client_id = serializers.UUIDField(required=False, allow_null=True)

    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/jpg',
    ]
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg']

    def validate_file(self, value):
        """Validate file size and type."""
        # Check size (3MB max)
        max_size = getattr(settings, 'MAX_FILE_SIZE_MB', 3) * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size {value.size} exceeds maximum of {max_size // (1024*1024)}MB."
            )

        # Check content type
        if value.content_type not in self.ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"File type '{value.content_type}' not allowed. "
                f"Allowed types: PDF, JPG, JPEG."
            )

        # Check extension
        file_ext = '.' + value.name.rsplit('.', 1)[-1].lower() if '.' in value.name else ''
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"File extension '{file_ext}' not allowed. "
                f"Allowed: .pdf, .jpg, .jpeg."
            )

        return value


# =============================================================================
# PHYSICAL VERIFICATION SERIALIZERS
# =============================================================================

class PhysicalVerificationSerializer(serializers.ModelSerializer):
    """Read serializer for physical verification."""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = PhysicalVerification
        fields = [
            'id',
            'car_id',
            'status',
            'status_display',
            'scheduled_date',
            'visit_date',
            'visit_port',
            'verifier_user_id',
            'verifier_crew_id',
            'comments',
            'created_by',
            'created_date',
            'closed_by',
            'closed_at',
        ]


class PhysicalVerificationCreateSerializer(serializers.Serializer):
    """
    Create physical verification.
    Per BACKEND_STRUCTURE.md Section 10.8
    """
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    visit_port = serializers.CharField(required=False, allow_blank=True, max_length=200)
    verifier_user_id = serializers.CharField(required=False, allow_blank=True, max_length=100)


class PhysicalVerificationCloseSerializer(serializers.Serializer):
    """
    Close physical verification.
    Per BACKEND_STRUCTURE.md Section 10.8
    """
    visit_date = serializers.DateField(required=True)
    comments = serializers.CharField(required=True, min_length=10)

    def validate_visit_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Visit date cannot be in the future")
        return value


# =============================================================================
# CLC MAPPING SERIALIZER
# =============================================================================

class CarClcMappingSerializer(serializers.ModelSerializer):
    """Serializer for CLC code mappings."""

    class Meta:
        model = CarClcMapping
        fields = [
            'id',
            'clc_item_id',
            'custom_cause_text',
        ]


# =============================================================================
# CAR SERIALIZERS
# =============================================================================

class CARListSerializer(serializers.ModelSerializer):
    """
    Serializer for CAR list view.
    Per BACKEND_STRUCTURE.md GET /api/psc/cars/ response.
    """
    # Deficiency info (denormalized for performance)
    def_code = serializers.SerializerMethodField()
    deficiency_description = serializers.SerializerMethodField()
    deficiency_is_cleared = serializers.SerializerMethodField()

    # Inspection info
    inspection_id = serializers.SerializerMethodField()
    inspection_type = serializers.SerializerMethodField()
    inspection_date = serializers.SerializerMethodField()
    vessel_id = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_code = serializers.SerializerMethodField()

    # Counts
    action_count = serializers.IntegerField(read_only=True, default=0)
    completed_action_count = serializers.IntegerField(read_only=True, default=0)
    before_evidence_count = serializers.IntegerField(read_only=True, default=0)
    after_evidence_count = serializers.IntegerField(read_only=True, default=0)

    # Status display
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    pv_due = serializers.SerializerMethodField()

    class Meta:
        model = CAR
        fields = [
            'id',
            'car_number',
            'status',
            'status_display',
            'root_cause_summary',
            'target_date',
            'is_overdue',
            'pv_due',
            'rework_count',
            'created_date',
            # Deficiency info
            'def_code',
            'deficiency_description',
            'deficiency_is_cleared',
            # Inspection info
            'inspection_id',
            'inspection_type',
            'inspection_date',
            'vessel_id',
            'vessel_name',
            'vessel_code',
            # Counts
            'action_count',
            'completed_action_count',
            'before_evidence_count',
            'after_evidence_count',
        ]

    def _get_deficiency(self, obj):
        """Get cached deficiency or query."""
        if not hasattr(obj, '_cached_deficiency'):
            try:
                obj._cached_deficiency = obj.deficiency
            except Deficiency.DoesNotExist:
                obj._cached_deficiency = None
        return obj._cached_deficiency

    def get_def_code(self, obj):
        deficiency = self._get_deficiency(obj)
        return deficiency.def_code if deficiency else None

    def get_deficiency_description(self, obj):
        deficiency = self._get_deficiency(obj)
        return deficiency.description if deficiency else None

    def get_deficiency_is_cleared(self, obj):
        deficiency = self._get_deficiency(obj)
        return deficiency.is_cleared if deficiency else None

    def get_pv_due(self, obj):
        if obj.status != CARStatus.CLOSED:
            return False

        prefetched = getattr(obj, 'prefetched_open_physical_verifications', None)
        if prefetched is not None:
            return bool(prefetched)

        return obj.physical_verifications.filter(
            status=PVStatus.OPEN,
            is_deleted=False,
        ).exists()

    def get_inspection_id(self, obj):
        deficiency = self._get_deficiency(obj)
        return str(deficiency.inspection_id) if deficiency else None

    def get_inspection_type(self, obj):
        deficiency = self._get_deficiency(obj)
        return deficiency.inspection.inspection_type if deficiency else None

    def get_inspection_date(self, obj):
        deficiency = self._get_deficiency(obj)
        return deficiency.inspection.inspection_date if deficiency else None

    def get_vessel_id(self, obj):
        deficiency = self._get_deficiency(obj)
        return str(deficiency.inspection.vessel_id) if deficiency else None

    def get_vessel_name(self, obj):
        annotated = getattr(obj, 'vessel_name', None)
        if annotated:
            return annotated
        deficiency = self._get_deficiency(obj)
        return str(deficiency.inspection.vessel_id) if deficiency else ''

    def get_vessel_code(self, obj):
        annotated = getattr(obj, 'vessel_code', None)
        return annotated or ''

    def get_is_overdue(self, obj):
        if not obj.target_date:
            return False
        if obj.status == CARStatus.CLOSED:
            return False
        return obj.target_date < date.today()


class DeficiencyNestedSerializer(serializers.Serializer):
    """Nested deficiency info for CAR detail."""
    id = serializers.UUIDField()
    def_code = serializers.CharField()
    def_code_id = serializers.CharField()
    def_code_description = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField()
    action_code = serializers.CharField(allow_null=True)
    action_code_id = serializers.IntegerField(allow_null=True)
    action_code_description = serializers.CharField(required=False, allow_null=True)
    initial_action_code = serializers.CharField(required=False, allow_null=True)
    current_action_code = serializers.CharField(required=False, allow_null=True)
    action_code_change_note = serializers.JSONField(required=False, allow_null=True)
    target_date = serializers.DateField(allow_null=True)
    is_cleared = serializers.BooleanField()
    cleared_date = serializers.DateField(allow_null=True)


class InspectionNestedSerializer(serializers.Serializer):
    """Nested inspection info for CAR detail."""
    id = serializers.UUIDField()
    inspection_type = serializers.CharField()
    psc_subtype = serializers.CharField(allow_null=True)
    inspection_date = serializers.DateField()
    port_place = serializers.CharField()
    vessel_id = serializers.UUIDField()
    vessel_name = serializers.CharField(default='')


class CARDetailSerializer(serializers.ModelSerializer):
    """
    Full CAR detail serializer with all nested data.
    Per BACKEND_STRUCTURE.md GET /api/psc/cars/{id}/ response.
    """
    # Nested related data
    deficiency = serializers.SerializerMethodField()
    inspection = serializers.SerializerMethodField()
    pic_comment = serializers.SerializerMethodField()
    clc_items = CarClcMappingSerializer(source='clc_mappings', many=True, read_only=True)
    corrective_actions = serializers.SerializerMethodField()
    evidence = serializers.SerializerMethodField()
    physical_verification = serializers.SerializerMethodField()
    activity_history = serializers.SerializerMethodField()
    audit_log = serializers.SerializerMethodField()
    available_actions = serializers.SerializerMethodField()
    follow_up_reports = serializers.SerializerMethodField()
    follow_up_summary = serializers.SerializerMethodField()
    follow_up_action_updates = serializers.SerializerMethodField()

    # Status display
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CAR
        fields = [
            'id',
            'car_number',
            'status',
            'status_display',
            'root_cause_summary',
            'target_date',
            'initial_action_code',
            # Verification
            'verification_pending',
            # PIC Review
            'pic_comment',
            'pic_accepted_by',
            'pic_accepted_at',
            # Rework
            'rework_reason',
            'rework_requested_by',
            'rework_requested_at',
            'rework_count',
            # DPA Close
            'dpa_comment',
            'dpa_closed_by',
            'dpa_closed_at',
            # Last action
            'last_action',
            'last_action_by',
            'last_action_at',
            'last_action_comment',
            # Audit
            'created_by',
            'created_date',
            'updated_by',
            'updated_date',
            # Nested
            'deficiency',
            'inspection',
            'clc_items',
            'corrective_actions',
            'evidence',
            'physical_verification',
            'activity_history',
            'audit_log',
            'available_actions',
            'follow_up_reports',
            'follow_up_summary',
            'follow_up_action_updates',
        ]

    def get_deficiency(self, obj):
        try:
            deficiency = obj.deficiency
            data = DeficiencyNestedSerializer(deficiency).data
            data['def_code_description'] = _lookup_def_code_title(deficiency.def_code_id)
            data['action_code_description'] = _lookup_action_code_definition(deficiency.action_code_id)
            initial_action_code = _resolve_initial_action_code(obj, deficiency)
            current_action_code = deficiency.action_code or None
            data['initial_action_code'] = initial_action_code
            data['current_action_code'] = current_action_code
            data['action_code_change_note'] = _resolve_action_code_change_note(
                deficiency=deficiency,
                current_action_code=current_action_code,
                initial_action_code=initial_action_code,
            )
            return data
        except Deficiency.DoesNotExist:
            return None

    def get_inspection(self, obj):
        try:
            deficiency = obj.deficiency
            inspection = deficiency.inspection
            data = InspectionNestedSerializer(inspection).data
            # Add vessel name snapshot from annotation if available.
            vessel_name = getattr(obj, 'vessel_name', '') or ''
            data['vessel_name'] = vessel_name
            data['vessel'] = {
                'id': str(inspection.vessel_id),
                'name': vessel_name,
            }
            return data
        except (Deficiency.DoesNotExist, AttributeError):
            return None

    def get_corrective_actions(self, obj):
        actions = obj.corrective_actions.filter(is_deleted=False)
        return CorrectiveActionSerializer(actions, many=True).data

    def get_evidence(self, obj):
        evidence_items = obj.evidence.filter(is_deleted=False)
        return EvidenceSerializer(evidence_items, many=True, context=self.context).data

    def get_physical_verification(self, obj):
        pv = obj.physical_verifications.filter(is_deleted=False).first()
        if pv:
            return PhysicalVerificationSerializer(pv).data
        return None

    def get_pic_comment(self, obj):
        """Return the PIC review comment, not the later submit-to-DPA note."""
        review_comment = ''
        review_events = ActivityHistory.objects.filter(
            entity_type='CAR',
            entity_id=obj.id,
            event_type__in=PIC_REVIEW_HISTORY_EVENT_TYPES,
        ).order_by('-performed_at')

        for event in review_events:
            review_comment = _extract_appended_comment(event.event_description)
            if review_comment:
                break

        return _resolve_pic_review_comment_value(
            stored_comment=obj.pic_comment,
            review_comment=review_comment,
            last_action=obj.last_action,
            last_action_comment=obj.last_action_comment,
        )

    def get_activity_history(self, obj):
        """Get activity history for this CAR."""
        history = ActivityHistory.objects.filter(
            Q(entity_type='CAR', entity_id=obj.id)
            | Q(
                entity_type='ACTION',
                entity_id__in=CorrectiveAction.objects.filter(car=obj).values_list('id', flat=True),
            )
            | Q(
                entity_type='EVIDENCE',
                entity_id__in=Evidence.objects.filter(car=obj).values_list('id', flat=True),
            )
        ).order_by('-performed_at')[:20]
        return ActivityHistorySerializer(history, many=True).data

    def get_audit_log(self, obj):
        """Get audit log (only for office/DPA users)."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if request.user.user_type == 'OFFICE':
                logs = AuditLog.objects.filter(
                    entity_type='CAR',
                    entity_id=obj.id
                ).order_by('-performed_at')[:50]
                return AuditLogSerializer(logs, many=True).data
        return []

    def get_available_actions(self, obj):
        """Get available workflow actions for the current user."""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return []
        from apps.inspection.workflow import get_available_actions
        actions = get_available_actions(obj, request.user)
        return actions

    def _follow_up_payload(self, obj):
        cached = getattr(obj, '_follow_up_payload_cache', None)
        if cached is not None:
            return cached

        from apps.car.follow_up_reports import attach_follow_up_reports

        payload = {
            'inspection': self.get_inspection(obj) or {},
            'deficiency': self.get_deficiency(obj) or {},
        }
        cached = attach_follow_up_reports(payload, request=self.context.get('request'))
        setattr(obj, '_follow_up_payload_cache', cached)
        return cached

    def get_follow_up_reports(self, obj):
        return self._follow_up_payload(obj).get('follow_up_reports') or []

    def get_follow_up_summary(self, obj):
        return self._follow_up_payload(obj).get('follow_up_summary') or {}

    def get_follow_up_action_updates(self, obj):
        return self._follow_up_payload(obj).get('follow_up_action_updates') or []


class CARUpdateSerializer(serializers.Serializer):
    """
    Update CAR (root cause, CLC codes, target date).
    Per BACKEND_STRUCTURE.md PUT /api/psc/cars/{id}/
    """
    root_cause_summary = serializers.CharField(required=False, allow_blank=True)
    target_date = serializers.DateField(required=False, allow_null=True)
    clc_item_ids = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    custom_cause_text = serializers.CharField(
        required=False, allow_blank=True, max_length=500
    )

    def validate_target_date(self, value):
        """Target date, if provided, must be today or in the future."""
        if value and value < date.today():
            raise serializers.ValidationError("Target date must be today or in the future")
        return value

    def validate_clc_item_ids(self, value):
        """Each CLC item must exist in active master data."""
        if not value:
            return value

        requested_ids = {str(clc_id) for clc_id in value}

        try:
            existing_ids = _fetch_active_master_clc_ids(value)
        except DatabaseError:
            raise serializers.ValidationError("Invalid CLC item selected")

        if requested_ids != existing_ids:
            raise serializers.ValidationError("Invalid CLC item selected")

        return value


class CARSubmitSerializer(serializers.Serializer):
    """
    Submit CAR for PIC review.
    Per BACKEND_STRUCTURE.md POST /api/psc/cars/{id}/submit/

    Preconditions:
    - root_cause_summary >= 50 chars
    - >= 1 IMMEDIATE corrective action
    - >= 1 LONG_TERM corrective action
    - >= 1 BEFORE evidence
    - >= 1 AFTER evidence
    """

    def validate(self, attrs):
        car = self.context.get('car')
        if not car:
            raise serializers.ValidationError("CAR not found in context.")

        from .validators import validate_car_submission
        errors = validate_car_submission(car)
        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class CARPICAcceptSerializer(serializers.Serializer):
    """
    PIC accept CAR.
    Per BACKEND_STRUCTURE.md POST /api/psc/cars/{id}/pic-accept/
    """
    comment = serializers.CharField(required=True, min_length=10)


class CARReworkSerializer(serializers.Serializer):
    """
    Request rework on CAR.
    Per BACKEND_STRUCTURE.md POST /api/psc/cars/{id}/rework/
    Rework reason must be >= 20 chars.
    """
    reason = serializers.CharField(required=True, min_length=20)


class CARDPACloseSerializer(serializers.Serializer):
    """
    DPA close CAR.
    Per BACKEND_STRUCTURE.md POST /api/psc/cars/{id}/dpa-close/
    """
    comment = serializers.CharField(required=True, min_length=10)


class CARReopenSerializer(serializers.Serializer):
    """
    Reopen a DPA-closed CAR.
    Per BACKEND_STRUCTURE.md POST /api/psc/cars/{id}/reopen/
    """
    reason = serializers.CharField(required=True, min_length=10)


class CARWorkflowTransitionSerializer(serializers.Serializer):
    """
    Unified workflow transition.
    POST /api/psc/cars/{id}/workflow/
    """
    action = serializers.CharField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True, default='')
