"""
Deficiency serializers per BACKEND_STRUCTURE.md Section 10.4.

Serializers:
- DeficiencyListSerializer: For inspection detail view (embedded)
- DeficiencyDetailSerializer: Full detail with CAR info
- DeficiencyCreateSerializer: Create with validation
- DeficiencyActionCodeUpdateSerializer: Update action code with history
"""

import uuid
import logging

from rest_framework import serializers
from django.utils import timezone
from django.db import connection

from .deficiency_models import Deficiency, DeficiencyActionHistory, CAR, DefStatus
from apps.masters.models import PSCDefCode, PSCActionCode
from apps.accounts.models import ShipUsersLogin, HRM501

logger = logging.getLogger(__name__)


class CARSummarySerializer(serializers.ModelSerializer):
    """Minimal CAR info for deficiency responses."""

    class Meta:
        model = CAR
        fields = ['id', 'car_number', 'status']


class DeficiencyListSerializer(serializers.ModelSerializer):
    """
    Deficiency summary for inspection detail view.
    Shows DefCode prominently per business rules.
    """
    def_code_description = serializers.SerializerMethodField()
    action_code_description = serializers.SerializerMethodField()
    assigned_crew_name = serializers.SerializerMethodField()
    car = CARSummarySerializer(read_only=True)

    class Meta:
        model = Deficiency
        fields = [
            'id',
            'def_code',
            'def_code_description',
            'description',
            'action_code',
            'action_code_description',
            'target_date',
            'is_cleared',
            'cleared_date',
            'sequence_no',
            'assigned_crew_id',
            'assigned_crew_name',
            'def_status',
            'reviewer_crew_id',
            'owner_rank',
            'owner_name',
            'reviewer_rank',
            'reviewer_name',
            'car',
        ]

    def get_def_code_description(self, obj):
        """Get deficiency code description from master table."""
        try:
            def_code = PSCDefCode.objects.get(def_code=obj.def_code_id)
            return def_code.def_name
        except PSCDefCode.DoesNotExist:
            return None
        except Exception:
            return None

    def get_action_code_description(self, obj):
        """Get action code description from master table."""
        if not obj.action_code_id:
            return None
        try:
            action_code = PSCActionCode.objects.get(action_code=obj.action_code_id)
            return action_code.definition
        except PSCActionCode.DoesNotExist:
            return None
        except Exception:
            return None

    def get_assigned_crew_name(self, obj):
        """Get assigned crew member name from HRM501.

        Assigned crew is stored as CrewID.
        """
        if not obj.assigned_crew_id:
            return None
        try:
            from apps.accounts.utils import get_crew_display_name_by_crewid
            return get_crew_display_name_by_crewid(obj.assigned_crew_id)
        except Exception:
            return None


class DeficiencyDetailSerializer(serializers.ModelSerializer):
    """
    Full deficiency detail with CAR and history.
    """
    def_code_description = serializers.SerializerMethodField()
    action_code_description = serializers.SerializerMethodField()
    assigned_crew_name = serializers.SerializerMethodField()
    car = CARSummarySerializer(read_only=True)
    action_history = serializers.SerializerMethodField()
    workflow_history = serializers.SerializerMethodField()

    class Meta:
        model = Deficiency
        fields = [
            'id',
            'inspection_id',
            'def_code',
            'def_code_id',
            'def_code_description',
            'description',
            'action_code',
            'action_code_id',
            'action_code_description',
            'target_date',
            'is_cleared',
            'cleared_date',
            'cleared_by_follow_up_id',
            'sequence_no',
            'assigned_crew_id',
            'assigned_crew_name',
            'def_status',
            'reviewer_crew_id',
            'owner_rank',
            'owner_name',
            'reviewer_rank',
            'reviewer_name',
            'car',
            'action_history',
            'workflow_history',
            'created_by',
            'created_date',
            'updated_by',
            'updated_date',
        ]

    def get_def_code_description(self, obj):
        try:
            def_code = PSCDefCode.objects.get(def_code=obj.def_code_id)
            return def_code.def_name
        except PSCDefCode.DoesNotExist:
            return None
        except Exception:
            return None

    def get_action_code_description(self, obj):
        if not obj.action_code_id:
            return None
        try:
            action_code = PSCActionCode.objects.get(action_code=obj.action_code_id)
            return action_code.definition
        except PSCActionCode.DoesNotExist:
            return None
        except Exception:
            return None

    def get_assigned_crew_name(self, obj):
        """Get assigned crew member name from HRM501.

        Assigned crew is stored as CrewID.
        """
        if not obj.assigned_crew_id:
            return None
        try:
            from apps.accounts.utils import get_crew_display_name_by_crewid
            return get_crew_display_name_by_crewid(obj.assigned_crew_id)
        except Exception:
            return None

    def get_action_history(self, obj):
        """Get action code change history."""
        history = obj.action_history.all()[:10]  # Last 10 changes
        return [
            {
                'previous_action_code': h.previous_action_code,
                'new_action_code': h.new_action_code,
                'change_reason': h.change_reason,
                'changed_by': h.changed_by,
                'changed_at': h.changed_at,
            }
            for h in history
        ]

    def get_workflow_history(self, obj):
        """Get workflow transition history from ActivityHistory."""
        from apps.car.models import ActivityHistory
        events = ActivityHistory.objects.filter(
            entity_type='DEFICIENCY',
            entity_id=obj.id,
            event_type__startswith='DEF_',
        ).order_by('-performed_at')[:20]
        return [
            {
                'event_type': e.event_type,
                'event_description': e.event_description,
                'performed_by_name': e.performed_by_name,
                'performed_at': e.performed_at,
            }
            for e in events
        ]


class DeficiencyCreateSerializer(serializers.ModelSerializer):
    """
    Create deficiency with validation.
    Auto-creates CAR via signal.

    Per BACKEND_STRUCTURE.md Section 10.4:
    POST /api/psc/inspections/{inspection_id}/deficiencies/
    """
    def_code_id = serializers.CharField(max_length=5)
    description = serializers.CharField(min_length=10, max_length=4000)
    action_code_id = serializers.IntegerField(required=False, allow_null=True)
    assigned_crew_id = serializers.CharField(required=False, allow_null=True)
    client_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Deficiency
        fields = [
            'def_code_id',
            'description',
            'action_code_id',
            'assigned_crew_id',
            'target_date',
            'client_id',
        ]

    def validate_def_code_id(self, value):
        """Validate deficiency code exists in master table."""
        try:
            PSCDefCode.objects.get(def_code=value)
        except PSCDefCode.DoesNotExist:
            raise serializers.ValidationError(
                f"Invalid deficiency code: {value}"
            )
        return value

    def validate_action_code_id(self, value):
        """Validate action code exists in master table."""
        if value is None:
            return value
        try:
            PSCActionCode.objects.get(action_code=value)
        except PSCActionCode.DoesNotExist:
            raise serializers.ValidationError(
                f"Invalid action code: {value}"
            )
        return value

    def validate_assigned_crew_id(self, value):
        if not value:
            return value

        raw_value = str(value).strip()
        if not raw_value:
            return None

        inspection = self.context.get('inspection')

        def _is_onboard(crew_id: str) -> bool:
            if not inspection:
                return True
            # Crew_Onboarding_History.Vessel can contain mixed legacy formats.
            # Use TRY_CONVERT to avoid SQL conversion crashes on bad rows.
            try:
                vessel_id = str(uuid.UUID(str(inspection.vessel_id)))
            except (ValueError, TypeError, AttributeError):
                vessel_id = str(inspection.vessel_id)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TOP 1 1
                    FROM Crew_Onboarding_History coh
                    WHERE coh.CrewID = %s
                      AND coh.SignOffDate IS NULL
                      AND ISNULL(coh.is_active, 1) = 1
                      AND ISNULL(coh.is_deleted, 0) = 0
                      AND TRY_CONVERT(uniqueidentifier, coh.Vessel) = CAST(%s AS uniqueidentifier)
                    """,
                    [crew_id, vessel_id],
                )
                return cursor.fetchone() is not None

        # Accept canonical CrewID directly.
        if HRM501.objects.filter(CrewID=raw_value, is_active=True, is_deleted=False).exists():
            if _is_onboard(raw_value):
                return raw_value
            raise serializers.ValidationError("Assigned crew member is not currently onboard this vessel.")

        # Backward/compat mode: accept HRM501 UUID and normalize to CrewID.
        normalized_uuid = None
        try:
            normalized_uuid = str(uuid.UUID(raw_value))
        except (ValueError, TypeError, AttributeError):
            pass

        if normalized_uuid:
            crew_id = HRM501.objects.filter(
                id=normalized_uuid,
                is_active=True,
                is_deleted=False,
            ).values_list('CrewID', flat=True).first()
            if crew_id:
                if _is_onboard(crew_id):
                    return crew_id
                raise serializers.ValidationError("Assigned crew member is not currently onboard this vessel.")

        # Last fallback for legacy login records.
        exists = ShipUsersLogin.objects.filter(
            CrewID=raw_value,
            is_active=True,
            is_deleted=False,
        ).exists()
        if exists and _is_onboard(raw_value):
            return raw_value

        raise serializers.ValidationError("Assigned crew member is invalid.")

    def validate_target_date(self, value):
        """Validate target date is today or in the future."""
        if value is None:
            return value
        if value < timezone.localdate():
            raise serializers.ValidationError(
                "Target date must be today or in the future."
            )
        return value

    def create(self, validated_data):
        """
        Create deficiency with denormalized codes.
        CAR is auto-created via post_save signal.
        """
        # Get def code for denormalization
        def_code_id = validated_data['def_code_id']
        def_code_obj = PSCDefCode.objects.get(def_code=def_code_id)
        validated_data['def_code'] = def_code_obj.def_code

        # Get action code for denormalization (if provided)
        action_code_id = validated_data.get('action_code_id')
        if action_code_id:
            action_code_obj = PSCActionCode.objects.get(action_code=action_code_id)
            validated_data['action_code'] = str(action_code_obj.action_code)

        # Set sequence number
        inspection = validated_data.get('inspection')
        if inspection:
            last_def = Deficiency.objects.filter(
                inspection=inspection,
                is_deleted=False
            ).order_by('-sequence_no').first()
            validated_data['sequence_no'] = (last_def.sequence_no + 1) if last_def else 1

        # Create deficiency (CAR created via signal)
        deficiency = super().create(validated_data)

        # Ensure immutable initial action-code snapshot reflects creation-time value.
        initial_action_code = validated_data.get('action_code')
        if deficiency.car_id and initial_action_code:
            CAR.objects.filter(
                id=deficiency.car_id,
                initial_action_code__isnull=True,
            ).update(initial_action_code=initial_action_code)

        return deficiency


class DeficiencyActionCodeUpdateSerializer(serializers.Serializer):
    """
    Update deficiency action code with history tracking.

    Per BACKEND_STRUCTURE.md Section 10.4:
    PUT /api/psc/deficiencies/{id}/action-code/
    """
    action_code_id = serializers.IntegerField()
    follow_up_inspection_id = serializers.UUIDField(required=False, allow_null=True)
    change_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_action_code_id(self, value):
        """Validate action code exists in master table."""
        try:
            PSCActionCode.objects.get(action_code=value)
        except PSCActionCode.DoesNotExist:
            raise serializers.ValidationError(
                f"Invalid action code: {value}"
            )
        return value

    def validate_follow_up_inspection_id(self, value):
        """Validate follow-up inspection exists and is PSC FOLLOW_UP."""
        if value is None:
            return value
        from .models import Inspection, InspectionType, PSCSubtype
        try:
            inspection = Inspection.objects.get(id=value, is_deleted=False)
        except Inspection.DoesNotExist:
            raise serializers.ValidationError(
                f"Invalid follow-up inspection: {value}"
            )

        if inspection.inspection_type != InspectionType.PSC or inspection.psc_subtype != PSCSubtype.FOLLOW_UP:
            raise serializers.ValidationError(
                "Follow-up inspection must be a PSC inspection with subtype FOLLOW_UP."
            )
        return value

    def update(self, instance, validated_data):
        """
        Update action code and create history record.
        """
        action_code_id = validated_data['action_code_id']
        follow_up_id = validated_data.get('follow_up_inspection_id')
        change_reason = validated_data.get('change_reason', '')

        # Get action code for denormalization
        action_code_obj = PSCActionCode.objects.get(action_code=action_code_id)
        new_action_code = str(action_code_obj.action_code)

        # Create history record
        DeficiencyActionHistory.objects.create(
            deficiency=instance,
            previous_action_code_id=instance.action_code_id,
            previous_action_code=instance.action_code,
            new_action_code_id=action_code_id,
            new_action_code=new_action_code,
            follow_up_inspection_id=follow_up_id,
            change_reason=change_reason,
            changed_by=self.context.get('request').user.display_name or 'Unknown',
        )

        # Update deficiency
        instance.action_code_id = action_code_id
        instance.action_code = new_action_code
        instance.updated_by = self.context.get('request').user.display_name
        instance.updated_date = timezone.now()

        # Handle follow-up clearing
        if follow_up_id:
            from .models import Inspection
            follow_up = Inspection.objects.get(id=follow_up_id)
            instance.cleared_by_follow_up = follow_up

        # Check if action code 10 (rectified) - auto-clear
        RECTIFIED_CODE = 10
        if action_code_id == RECTIFIED_CODE:
            instance.is_cleared = True
            instance.cleared_date = timezone.now().date()

        instance.save()
        return instance


class DeficiencyWorkflowTransitionSerializer(serializers.Serializer):
    """
    Validate a DEF workflow transition request.

    POST /api/psc/deficiencies/{id}/workflow/
    Body: { target_status: DefStatus, comment?: string }
    """
    target_status = serializers.ChoiceField(choices=DefStatus.choices)
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class BulkSubmitSerializer(serializers.Serializer):
    """Validate a bulk DEF submission request (Master submits multiple APPROVED DEFs)."""
    deficiency_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1, max_length=100
    )
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class DeficiencyAllocateSerializer(serializers.Serializer):
    """
    Validate a DEF allocation (Master assigns to crew).

    POST /api/psc/deficiencies/{id}/allocate/
    Body: { assigned_crew_id: CrewID, reviewer_crew_id?: UUID }
    """
    assigned_crew_id = serializers.CharField()
    reviewer_crew_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_assigned_crew_id(self, value):
        exists = ShipUsersLogin.objects.filter(
            CrewID=value,
            is_active=True,
            is_deleted=False,
        ).exists()
        if not exists:
            raise serializers.ValidationError("Assigned crew member is invalid.")
        return value
