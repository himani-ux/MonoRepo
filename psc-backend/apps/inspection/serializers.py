"""
Inspection serializers per BACKEND_STRUCTURE.md Section 10.3.

Serializers:
- InspectionListSerializer: Summary for list view
- InspectionDetailSerializer: Full detail with related data
- InspectionCreateSerializer: Validation for create
- InspectionUpdateSerializer: Validation for update
- InspectionReportSerializer: Report file info
"""

from rest_framework import serializers
from django.utils import timezone

from .models import Inspection, InspectionReport, InspectionStatus, InspectionType


def compute_operational_status(obj):
    """Compute OPEN/CLOSED incorporating def_reported field.

    NULL is legacy only (pre-def_reported); treat as OPEN.
    """
    def_reported = getattr(obj, 'def_reported', None)
    if def_reported is None:
        return 'OPEN'  # Legacy data — no def_reported recorded
    if def_reported == 'NO':
        return 'CLOSED'
    # YES: OPEN until all defs have action_code_id=10
    # If no defs created yet, still OPEN (user said YES = defs expected)
    total_count = getattr(obj, 'deficiency_count', 0)
    if total_count == 0:
        return 'OPEN'  # YES but no defs added yet — still open
    open_count = getattr(obj, 'open_deficiency_count', 0)
    return 'OPEN' if open_count > 0 else 'CLOSED'


class InspectionReportSerializer(serializers.ModelSerializer):
    """Serializer for inspection report attachments."""

    class Meta:
        model = InspectionReport
        fields = [
            'id',
            'file_name',
            'file_path',
            'file_size',
            'mime_type',
            'description',
            'report_type',
            'uploaded_by',
            'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_at']


class InspectionListSerializer(serializers.ModelSerializer):
    """
    Serializer for inspection list view.
    Per BACKEND_STRUCTURE.md GET /api/psc/inspections/ response.
    """
    # Computed fields (will be annotated in queryset or computed)
    vessel_name = serializers.CharField(read_only=True, default='')
    vessel_code = serializers.CharField(read_only=True, default='')
    mou_name = serializers.CharField(read_only=True, default='')
    deficiency_count = serializers.IntegerField(read_only=True, default=0)
    open_deficiency_count = serializers.IntegerField(read_only=True, default=0)
    closed_deficiency_count = serializers.IntegerField(read_only=True, default=0)
    operational_status = serializers.SerializerMethodField()
    has_report = serializers.SerializerMethodField()

    class Meta:
        model = Inspection
        fields = [
            'id',
            'vessel_id',
            'vessel_name',
            'vessel_code',
            'inspection_type',
            'psc_subtype',
            'inspection_date',
            'port_place',
            'country',
            'mou_id',
            'mou_name',
            'authority',
            'inspector_name',
            'report_reference',
            'is_detention',
            'def_reported',
            'status',
            'operational_status',
            'deficiency_count',
            'open_deficiency_count',
            'closed_deficiency_count',
            'has_report',
            'created_date',
        ]

    def get_operational_status(self, obj):
        """Compute OPEN/CLOSED incorporating def_reported field."""
        return compute_operational_status(obj)

    def get_has_report(self, obj):
        """Check if inspection has at least one non-deleted report."""
        if hasattr(obj, 'report_count'):
            return obj.report_count > 0
        return obj.reports.filter(is_deleted=False).exists()


class InspectionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for inspection detail view.
    Per BACKEND_STRUCTURE.md GET /api/psc/inspections/{id}/ response.
    """
    # Computed fields
    vessel_name = serializers.CharField(read_only=True, default='')
    vessel_code = serializers.CharField(read_only=True, default='')
    mou_name = serializers.CharField(read_only=True, default='')
    operational_status = serializers.SerializerMethodField()
    open_deficiency_count = serializers.IntegerField(read_only=True, default=0)
    closed_deficiency_count = serializers.IntegerField(read_only=True, default=0)

    # Frontend-compatible field aliases
    port = serializers.CharField(source='port_place', read_only=True)
    port_state = serializers.CharField(source='country', read_only=True, default='')
    mou_code = serializers.CharField(source='mou_id', read_only=True, default='')
    imo_number = serializers.SerializerMethodField()

    # Related data
    reports = InspectionReportSerializer(many=True, read_only=True, source='active_reports')
    deficiencies = serializers.SerializerMethodField()
    activity_history = serializers.SerializerMethodField()
    audit_log = serializers.SerializerMethodField()

    # Parent inspection info (for follow-ups)
    parent_inspection_info = serializers.SerializerMethodField()

    # Follow-up inspections
    follow_ups_count = serializers.SerializerMethodField()

    class Meta:
        model = Inspection
        fields = [
            'id',
            'vessel_id',
            'vessel_name',
            'vessel_code',
            'imo_number',
            'inspection_type',
            'psc_subtype',
            'inspection_date',
            'port_place',
            'port',
            'country',
            'port_state',
            'mou_id',
            'mou_name',
            'mou_code',
            'authority',
            'inspector_name',
            'report_reference',
            'is_detention',
            'def_reported',
            'status',
            'operational_status',
            'open_deficiency_count',
            'closed_deficiency_count',
            'revision_no',
            'pic_comment',
            'pic_reviewed_by',
            'pic_reviewed_at',
            'dpa_comment',
            'dpa_closed_by',
            'dpa_closed_at',
            'parent_inspection',
            'parent_inspection_info',
            'follow_ups_count',
            'reports',
            'deficiencies',
            'activity_history',
            'audit_log',
            'created_by',
            'created_date',
            'updated_by',
            'updated_date',
            'client_id',
            'sync_version',
        ]

    def get_operational_status(self, obj):
        """Compute OPEN/CLOSED incorporating def_reported field."""
        return compute_operational_status(obj)

    def get_imo_number(self, obj):
        """Get IMO number from VesselData if available."""
        return getattr(obj, 'imo_number', None)

    def get_deficiencies(self, obj):
        """Get active deficiencies with CAR info.

        Crew members only see deficiencies assigned to them.
        """
        from .deficiency_serializers import DeficiencyListSerializer
        active = obj.active_deficiencies

        request = self.context.get('request')
        if request and getattr(request.user, 'role', None) == 'VESSEL_CREW':
            from django.db.models import Q
            active = active.filter(
                Q(assigned_crew_id=request.user.crew_id) |
                Q(assigned_crew_id=request.user.id)
            )

        return DeficiencyListSerializer(active, many=True).data

    def get_activity_history(self, obj):
        """Get activity history events for this inspection."""
        from apps.car.models import ActivityHistory
        from apps.car.serializers import ActivityHistorySerializer
        events = ActivityHistory.objects.filter(
            entity_type__startswith='INSPECTION',
            entity_id=str(obj.id)
        ).order_by('-performed_at')[:20]
        return ActivityHistorySerializer(events, many=True).data

    def get_parent_inspection_info(self, obj):
        """Get summary info about parent inspection if this is a follow-up."""
        if obj.parent_inspection:
            return {
                'id': str(obj.parent_inspection.id),
                'inspection_date': obj.parent_inspection.inspection_date,
                'port_place': obj.parent_inspection.port_place,
            }
        return None

    def get_audit_log(self, obj):
        """
        Get audit log for this inspection.
        Office/DPA users see full audit log; vessel users get empty list.
        Per PRD FEAT-INS-011: "Office/DPA can see full audit log"
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return []
        user = request.user
        if user.user_type == 'VESSEL':
            return []
        from apps.car.models import AuditLog
        from apps.car.serializers import AuditLogSerializer
        entries = AuditLog.objects.filter(
            entity_type='INSPECTION',
            entity_id=str(obj.id),
        ).order_by('-performed_at')[:50]
        return AuditLogSerializer(entries, many=True).data

    def get_follow_ups_count(self, obj):
        """Count follow-up inspections."""
        return obj.follow_ups.filter(is_deleted=False).count()


class InspectionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new inspections.
    Per BACKEND_STRUCTURE.md POST /api/psc/inspections/ request.
    """

    class Meta:
        model = Inspection
        fields = [
            'vessel_id',
            'inspection_type',
            'psc_subtype',
            'inspection_date',
            'port_place',
            'country',
            'mou_id',
            'authority',
            'inspector_name',
            'is_detention',
            'def_reported',
            'client_id',
        ]

    def validate_def_reported(self, value):
        """def_reported must be YES or NO for new inspections."""
        if value not in ('YES', 'NO'):
            raise serializers.ValidationError(
                'Please indicate if deficiencies were reported (YES or NO).'
            )
        return value

    def validate(self, data):
        """
        Validate inspection data.
        Per PRD.md FEAT-INS-001 and VALIDATION_RULES.md Section 2.1:
        - inspection_date cannot be in the future
        - port_place min length is 2
        - psc_subtype required when inspection_type is PSC
        - mou_id required when inspection_type is PSC
        - psc_subtype must be null for non-PSC types
        """
        inspection_type = data.get('inspection_type')
        psc_subtype = data.get('psc_subtype')
        inspection_date = data.get('inspection_date')
        port_place = data.get('port_place')
        mou_id = data.get('mou_id')
        errors = {}

        if inspection_date and inspection_date > timezone.localdate():
            errors['inspection_date'] = 'Inspection date cannot be in the future.'

        if not port_place or len(port_place.strip()) < 2:
            errors['port_place'] = 'Port/Place is required (2-200 characters).'

        if inspection_type == InspectionType.PSC:
            if not psc_subtype:
                errors['psc_subtype'] = 'PSC subtype is required for PSC inspections.'
            if not mou_id:
                errors['mou_id'] = 'MOU is required for PSC inspections.'
        else:
            if psc_subtype:
                errors['psc_subtype'] = 'PSC subtype should only be set for PSC inspections.'
            # Clear psc_subtype for non-PSC
            data['psc_subtype'] = None

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """Create inspection with audit fields and auto-generated report reference."""
        from .utils import generate_report_reference

        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = str(request.user.id)

        # Auto-generate report reference
        vessel_id = validated_data.get('vessel_id')
        inspection_date = validated_data.get('inspection_date')
        if vessel_id and inspection_date:
            ref = generate_report_reference(vessel_id, inspection_date)
            if ref:
                validated_data['report_reference'] = ref

        return super().create(validated_data)


class InspectionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating inspections.
    Per BACKEND_STRUCTURE.md PUT /api/psc/inspections/{id}/ request.
    """

    class Meta:
        model = Inspection
        fields = [
            'inspection_type',
            'psc_subtype',
            'inspection_date',
            'port_place',
            'country',
            'mou_id',
            'authority',
            'inspector_name',
            'report_reference',
            'is_detention',
            'def_reported',
        ]

    def validate_def_reported(self, value):
        """Safe transition: reject YES→NO if deficiencies exist."""
        if value == 'NO' and self.instance:
            def_count = self.instance.deficiencies.filter(is_deleted=False).count()
            if def_count > 0:
                raise serializers.ValidationError(
                    'Cannot set to NO — this inspection has existing deficiencies. '
                    'Remove all deficiencies first.'
                )
        return value

    def validate(self, data):
        """Validate update data with same rules as create."""
        inspection_type = data.get('inspection_type', self.instance.inspection_type)
        psc_subtype = data.get('psc_subtype', self.instance.psc_subtype)
        inspection_date = data.get('inspection_date', self.instance.inspection_date)
        port_place = data.get('port_place', self.instance.port_place)
        mou_id = data.get('mou_id', self.instance.mou_id)
        errors = {}

        if inspection_date and inspection_date > timezone.localdate():
            errors['inspection_date'] = 'Inspection date cannot be in the future.'

        if not port_place or len(port_place.strip()) < 2:
            errors['port_place'] = 'Port/Place is required (2-200 characters).'

        if inspection_type == InspectionType.PSC:
            if not psc_subtype:
                errors['psc_subtype'] = 'PSC subtype is required for PSC inspections.'
            if not mou_id:
                errors['mou_id'] = 'MOU is required for PSC inspections.'
        else:
            if psc_subtype:
                errors['psc_subtype'] = 'PSC subtype should only be set for PSC inspections.'
            data['psc_subtype'] = None

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def update(self, instance, validated_data):
        """Update inspection with audit fields."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = str(request.user.id)
        validated_data['sync_version'] = instance.sync_version + 1
        return super().update(instance, validated_data)


class InspectionSubmitSerializer(serializers.Serializer):
    """
    Serializer for submitting inspection for review.
    Per BACKEND_STRUCTURE.md POST /api/psc/inspections/{id}/submit/
    """

    def validate(self, data):
        """Validate inspection can be submitted."""
        inspection = self.context.get('inspection')

        if inspection.status != InspectionStatus.DRAFT:
            raise serializers.ValidationError({
                'status': f'Cannot submit inspection in {inspection.status} status. Must be DRAFT.'
            })

        if not inspection.reports.filter(is_deleted=False).exists():
            raise serializers.ValidationError({
                'reports': 'Inspection must have at least one report attached before submitting.'
            })

        if inspection.deficiencies.filter(is_deleted=False, car__isnull=True).exists():
            raise serializers.ValidationError({
                'deficiencies': 'All deficiencies must have associated CARs before submission.'
            })

        return data


class InspectionPICReviewSerializer(serializers.Serializer):
    """
    Serializer for PIC review of inspection.
    Per BACKEND_STRUCTURE.md POST /api/psc/inspections/{id}/pic-review/
    """
    comment = serializers.CharField(
        min_length=10,
        help_text="Review comment (minimum 10 characters)"
    )

    def validate(self, data):
        """Validate inspection can be PIC reviewed."""
        inspection = self.context.get('inspection')

        if inspection.status != InspectionStatus.SUBMITTED:
            raise serializers.ValidationError({
                'status': f'Cannot review inspection in {inspection.status} status. Must be SUBMITTED.'
            })

        return data


class InspectionDPACloseSerializer(serializers.Serializer):
    """
    Serializer for DPA closing inspection.
    Per BACKEND_STRUCTURE.md POST /api/psc/inspections/{id}/dpa-close/
    """
    comment = serializers.CharField(
        min_length=10,
        help_text="Closing comment (minimum 10 characters)"
    )

    def validate(self, data):
        """Validate inspection can be DPA closed."""
        inspection = self.context.get('inspection')

        if inspection.status != InspectionStatus.PIC_REVIEWED:
            raise serializers.ValidationError({
                'status': f'Cannot close inspection in {inspection.status} status. Must be PIC_REVIEWED.'
            })

        return data


class InspectionReportUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading inspection report.
    Per BACKEND_STRUCTURE.md POST /api/psc/inspections/{id}/upload-report/
    """
    file = serializers.FileField(
        help_text="Report file (PDF, JPG, JPEG only, max 3MB)"
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        default='',
        help_text="Optional description of the report"
    )

    def validate_file(self, value):
        """Validate file type and size per CLAUDE.md Business Rules."""
        # Check file size (3MB max)
        max_size = 3 * 1024 * 1024  # 3MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size ({value.size / 1024 / 1024:.2f}MB) exceeds maximum allowed size (3MB).'
            )

        # Check file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg']
        content_type = value.content_type.lower()
        if content_type not in allowed_types:
            raise serializers.ValidationError(
                f'File type "{content_type}" not allowed. Must be PDF, JPG, or JPEG.'
            )

        return value
