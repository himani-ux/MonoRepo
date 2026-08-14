"""Serializers for the Audit plan register."""

from __future__ import annotations

from rest_framework import serializers

from apps.inspection.audit.models import MasterAuditPlan


PLAN_STATUS_CHOICES = (
    "PLANNED",
    "CONFIRMED",
    "IN_PROGRESS",
    "COMPLETED",
    "EXTENSION_REQUESTED",
    "EXTENDED",
    "OVERDUE",
    "CRITICAL_OVERDUE",
    "CANCELLED",
)
STEP_8_1_WRITABLE_STATUS_CHOICES = ("PLANNED", "CONFIRMED")
AUDIT_CLASSIFICATION_CHOICES = ("INTERNAL",)
OFFICE_DEPT_CHOICES = ("CREW", "TECH", "PURCHASE", "IT", "MARINE", "SEQ", "OTHER")


class AuditPlanSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    target_vessel_id = serializers.UUIDField(required=False, allow_null=True)
    target_office_dept = serializers.ChoiceField(
        choices=OFFICE_DEPT_CHOICES,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    audit_classification = serializers.ChoiceField(choices=AUDIT_CLASSIFICATION_CHOICES, default="INTERNAL")
    audit_standards_csv = serializers.CharField(max_length=100)
    planned_window_start = serializers.DateField(required=False, allow_null=True)
    planned_window_end = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=STEP_8_1_WRITABLE_STATUS_CHOICES, default="PLANNED")
    is_additional = serializers.BooleanField(required=False, default=False)
    additional_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_audit_standards_csv(self, value: str) -> str:
        standards = [part.strip().upper() for part in value.split(",") if part.strip()]
        if not standards:
            raise serializers.ValidationError("At least one audit standard is required.")
        if len(standards) != len(set(standards)):
            raise serializers.ValidationError("Audit standards cannot contain duplicates.")
        return ",".join(standards)

    def validate(self, data):
        instance = self.context.get("instance")
        target_vessel_id = data.get(
            "target_vessel_id",
            getattr(instance, "target_vessel_id", None),
        )
        target_office_dept = _blank_to_none(
            data.get(
                "target_office_dept",
                getattr(instance, "target_office_dept", None),
            )
        )
        if bool(target_vessel_id) == bool(target_office_dept):
            raise serializers.ValidationError(
                {"target": "Exactly one target_vessel_id or target_office_dept is required."}
            )

        window_start = data.get(
            "planned_window_start",
            getattr(instance, "planned_window_start", None),
        )
        window_end = data.get(
            "planned_window_end",
            getattr(instance, "planned_window_end", None),
        )
        if window_start and window_end and window_end < window_start:
            raise serializers.ValidationError(
                {"planned_window_end": "Planned window end cannot be before start."}
            )

        if data.get("is_additional"):
            raise serializers.ValidationError(
                {"is_additional": "Additional audit creation belongs to Phase 8 Step 8.3."}
            )

        data["target_office_dept"] = target_office_dept
        if target_vessel_id:
            data["target_office_dept"] = None
        return data

    def create(self, validated_data):
        validated_data.pop("is_additional", None)
        validated_data.pop("additional_reason", None)
        return MasterAuditPlan.objects.create(**validated_data)

    def update(self, instance: MasterAuditPlan, validated_data):
        validated_data.pop("is_additional", None)
        validated_data.pop("additional_reason", None)
        updated_fields = ["updated_by", "updated_date"]
        if "updated_by" in validated_data:
            instance.updated_by = validated_data["updated_by"]
        if "updated_date" in validated_data:
            instance.updated_date = validated_data["updated_date"]
        editable_fields = (
            "target_vessel_id",
            "target_office_dept",
            "audit_classification",
            "audit_standards_csv",
            "planned_window_start",
            "planned_window_end",
            "status",
        )
        for field_name in editable_fields:
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])
                updated_fields.append(field_name)
        instance.save(update_fields=updated_fields)
        return instance


class AuditPlanExtensionRequestSerializer(serializers.Serializer):
    extension_requested_reason = serializers.CharField()
    proposed_new_target_date = serializers.DateField()


class AuditPlanExtensionDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=("APPROVE", "REJECT"))
    extension_approved_reason = serializers.CharField()


class AuditPlanFlagNotificationSerializer(serializers.Serializer):
    flag_notification_date = serializers.DateField()
    flag_notification_ref = serializers.CharField(max_length=100)
    flag_notification_attachment = serializers.CharField(max_length=500)


class AuditPlanCancelSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField()
    next_planned_date = serializers.DateField()
    today = serializers.DateField(required=False)


class AuditPlanResponseSerializer(serializers.Serializer):
    def to_representation(self, instance: MasterAuditPlan):
        return {
            "id": str(instance.id),
            "target_vessel_id": str(instance.target_vessel_id) if instance.target_vessel_id else None,
            "target_office_dept": instance.target_office_dept,
            "target_label": _target_label(instance),
            "audit_classification": instance.audit_classification,
            "audit_standards_csv": instance.audit_standards_csv,
            "planned_window_start": instance.planned_window_start.isoformat() if instance.planned_window_start else None,
            "planned_window_end": instance.planned_window_end.isoformat() if instance.planned_window_end else None,
            "window_label": _window_label(instance),
            "extended_due_date": instance.extended_due_date.isoformat() if instance.extended_due_date else None,
            "extension_form_ref": instance.extension_form_ref,
            "extension_requested_at": instance.extension_requested_at.isoformat() if instance.extension_requested_at else None,
            "extension_requested_by": instance.extension_requested_by,
            "extension_requested_reason": instance.extension_requested_reason,
            "extension_approved_at": instance.extension_approved_at.isoformat() if instance.extension_approved_at else None,
            "extension_approved_by": instance.extension_approved_by,
            "extension_approved_reason": instance.extension_approved_reason,
            "flag_notified": instance.flag_notified,
            "flag_notification_date": instance.flag_notification_date.isoformat() if instance.flag_notification_date else None,
            "flag_notification_ref": instance.flag_notification_ref,
            "flag_notification_attachment": instance.flag_notification_attachment,
            "is_additional": instance.is_additional,
            "additional_reason": instance.additional_reason,
            "trigger_event_type": instance.trigger_event_type,
            "trigger_event_ref": instance.trigger_event_ref,
            "cancellation_reason": instance.cancellation_reason,
            "next_planned_date": instance.next_planned_date.isoformat() if instance.next_planned_date else None,
            "cancelled_by": instance.cancelled_by,
            "cancelled_at": instance.cancelled_at.isoformat() if instance.cancelled_at else None,
            "status": instance.status,
            "created_by": instance.created_by,
            "created_date": instance.created_date.isoformat() if instance.created_date else None,
            "updated_by": instance.updated_by,
            "updated_date": instance.updated_date.isoformat() if instance.updated_date else None,
        }


def _blank_to_none(value):
    if value == "":
        return None
    return value


def _target_label(plan: MasterAuditPlan) -> str:
    if plan.target_office_dept:
        return f"Office - {plan.target_office_dept}"
    if plan.target_vessel_id:
        return str(plan.target_vessel_id)
    return "Unassigned"


def _window_label(plan: MasterAuditPlan) -> str:
    if plan.planned_window_start and plan.planned_window_end:
        return f"{plan.planned_window_start.isoformat()} -> {plan.planned_window_end.isoformat()}"
    if plan.planned_window_end:
        return f"Due by {plan.planned_window_end.isoformat()}"
    return "Window not set"
