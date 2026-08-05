"""
PSC Follow-up serializers — same-inspection follow-up wizard.

The follow-up wizard updates deficiency action codes on the SAME inspection
(no new inspection record is created). Optionally uploads follow-up report PDFs.
"""

from rest_framework import serializers
from django.utils import timezone

from .deficiency_models import Deficiency, DeficiencyActionHistory
from apps.masters.models import PSCActionCode


class DeficiencyActionUpdateItemSerializer(serializers.Serializer):
    """Individual deficiency action code update within a follow-up."""
    deficiency_id = serializers.UUIDField()
    action_code_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_action_code_id(self, value):
        """Validate action code exists in master table."""
        if not PSCActionCode.objects.filter(action_code=value).exists():
            raise serializers.ValidationError(f"Invalid action code: {value}")
        return value


class FollowUpSerializer(serializers.Serializer):
    """
    Same-inspection follow-up wizard serializer.

    POST /api/psc/inspections/<inspection_id>/follow-up/

    Fields:
    - deficiency_updates: array of {deficiency_id, action_code_id, notes}
    - reinspection_date: date (required, between inspection_date and today)
    - notes: optional general notes

    The inspection object is passed via serializer context.
    """
    deficiency_updates = DeficiencyActionUpdateItemSerializer(many=True, required=True)
    reinspection_date = serializers.DateField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_reinspection_date(self, value):
        """Reinspection date must be between inspection date and today."""
        today = timezone.localdate()
        if value > today:
            raise serializers.ValidationError(
                'Reinspection date cannot be in the future.'
            )
        inspection = self.context.get('inspection')
        if inspection and value < inspection.inspection_date:
            raise serializers.ValidationError(
                'Reinspection date cannot be before the original inspection date.'
            )
        return value

    def validate_deficiency_updates(self, value):
        """All deficiency_ids must belong to the inspection and not be deleted."""
        if not value:
            raise serializers.ValidationError(
                'At least one deficiency update is required.'
            )

        inspection = self.context.get('inspection')
        if not inspection:
            return value

        deficiency_ids = [item['deficiency_id'] for item in value]
        existing = Deficiency.objects.filter(
            id__in=deficiency_ids,
            inspection=inspection,
            is_deleted=False,
        )
        existing_ids = set(str(d.id) for d in existing)
        requested_ids = set(str(did) for did in deficiency_ids)

        missing = requested_ids - existing_ids
        if missing:
            raise serializers.ValidationError(
                f"Deficiencies not found or don't belong to this inspection: {missing}"
            )

        return value
