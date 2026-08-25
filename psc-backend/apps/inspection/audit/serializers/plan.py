"""Serializers for the Audit plan register."""

from __future__ import annotations

import uuid

from django.db import connection
from django.utils import timezone
from rest_framework import serializers

from apps.inspection.audit.models import MasterAuditPlan
from apps.inspection.audit.services.auditor_selection import auditor_snapshot, get_qualified_auditor


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
    lead_auditor_user_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
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

        lead_auditor_user_id = _blank_to_none(
            data.get(
                "lead_auditor_user_id",
                getattr(instance, "lead_auditor_user_id", None),
            )
        )
        if lead_auditor_user_id:
            qualified_auditor = get_qualified_auditor(
                lead_auditor_user_id,
                standards=data.get("audit_standards_csv", getattr(instance, "audit_standards_csv", "")),
                target_office_dept=target_office_dept,
            )
            if qualified_auditor is None:
                raise serializers.ValidationError(
                    {
                        "lead_auditor_user_id": (
                            "Lead auditor must be active, unexpired, and qualified for the selected standard."
                        )
                    }
                )
        if data.get("status") == "CONFIRMED" and not lead_auditor_user_id:
            raise serializers.ValidationError(
                {"lead_auditor_user_id": "Lead auditor is required before confirming an audit plan."}
            )

        data["lead_auditor_user_id"] = lead_auditor_user_id
        data["target_office_dept"] = target_office_dept
        if target_vessel_id:
            data["target_office_dept"] = None
        return data

    def create(self, validated_data):
        validated_data.pop("is_additional", None)
        validated_data.pop("additional_reason", None)
        if connection.vendor == "microsoft":
            return _create_sql_server_plan(validated_data)
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
            "lead_auditor_user_id",
            "planned_window_start",
            "planned_window_end",
            "status",
        )
        for field_name in editable_fields:
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])
                updated_fields.append(field_name)
        if connection.vendor == "microsoft":
            return _update_sql_server_plan(instance, updated_fields)
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
        vessel_label_map = self.context.get("vessel_label_map", {})
        lead_auditor = auditor_snapshot(
            instance.lead_auditor_user_id,
            standards=instance.audit_standards_csv,
            target_office_dept=instance.target_office_dept,
        )
        return {
            "id": str(instance.id),
            "target_vessel_id": str(instance.target_vessel_id) if instance.target_vessel_id else None,
            "target_office_dept": instance.target_office_dept,
            "target_label": _target_label(instance, vessel_label_map),
            "audit_classification": instance.audit_classification,
            "audit_standards_csv": instance.audit_standards_csv,
            "lead_auditor_user_id": instance.lead_auditor_user_id,
            "lead_auditor_name": lead_auditor.name if lead_auditor else "",
            "lead_auditor_designation": lead_auditor.designation if lead_auditor else "",
            "lead_auditor_company": lead_auditor.company if lead_auditor else "",
            "lead_auditor_qual": lead_auditor.qualification if lead_auditor else "",
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


def _create_sql_server_plan(validated_data) -> MasterAuditPlan:
    plan_id = uuid.uuid4()
    created_date = validated_data.get("created_date") or timezone.now()
    column_types = _master_audit_plan_column_types()
    created_by_sql, created_by_params = _sql_value_for_column(
        "created_by",
        validated_data.get("created_by"),
        column_types,
    )
    target_vessel_id = validated_data.get("target_vessel_id")

    sql = f"""
        INSERT INTO dbo.master_audit_plan (
            id,
            target_vessel_id,
            target_office_dept,
            audit_classification,
            audit_standards_csv,
            lead_auditor_user_id,
            planned_window_start,
            planned_window_end,
            status,
            created_by,
            created_date,
            flag_notified,
            is_additional,
            is_deleted
        )
        VALUES (
            CAST(%s AS uniqueidentifier),
            CAST(%s AS uniqueidentifier),
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            {created_by_sql},
            %s,
            %s,
            %s,
            %s
        )
    """
    params = [
        str(plan_id),
        str(target_vessel_id) if target_vessel_id else None,
        validated_data.get("target_office_dept"),
        validated_data["audit_classification"],
        validated_data["audit_standards_csv"],
        validated_data.get("lead_auditor_user_id"),
        validated_data.get("planned_window_start"),
        validated_data.get("planned_window_end"),
        validated_data.get("status") or "PLANNED",
        *created_by_params,
        created_date,
        False,
        False,
        False,
    ]
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
    return _fetch_sql_server_plan(plan_id)


def _update_sql_server_plan(instance: MasterAuditPlan, updated_fields: list[str]) -> MasterAuditPlan:
    column_types = _master_audit_plan_column_types()
    assignments = []
    params = []

    for field_name in updated_fields:
        value = getattr(instance, field_name)
        if field_name == "target_vessel_id":
            assignments.append("target_vessel_id = CAST(%s AS uniqueidentifier)")
            params.append(str(value) if value else None)
            continue
        value_sql, value_params = _sql_value_for_column(field_name, value, column_types)
        assignments.append(f"{field_name} = {value_sql}")
        params.extend(value_params)

    if not assignments:
        return instance

    params.append(str(instance.id))
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE dbo.master_audit_plan
            SET {", ".join(assignments)}
            WHERE id = CAST(%s AS uniqueidentifier)
            """,
            params,
        )
    return _fetch_sql_server_plan(instance.id)


def _fetch_sql_server_plan(plan_id) -> MasterAuditPlan:
    rows = list(
        MasterAuditPlan.all_objects.raw(
            """
            SELECT *
            FROM dbo.master_audit_plan
            WHERE id = CAST(%s AS uniqueidentifier)
            """,
            [str(plan_id)],
        )
    )
    if not rows:
        raise MasterAuditPlan.DoesNotExist("Audit plan was saved but could not be reloaded.")
    return rows[0]


def _master_audit_plan_column_types() -> dict[str, str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = 'master_audit_plan'
            """
        )
        return {str(name).lower(): str(data_type).lower() for name, data_type in cursor.fetchall()}


def _sql_value_for_column(column_name: str, value, column_types: dict[str, str]) -> tuple[str, list]:
    if column_types.get(column_name.lower()) == "uniqueidentifier":
        return "CAST(%s AS uniqueidentifier)", [_uuid_or_none(value)]
    return "%s", [value]


def _uuid_or_none(value) -> str | None:
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError):
        return None


def _target_label(plan: MasterAuditPlan, vessel_label_map: dict[str, str] | None = None) -> str:
    if plan.target_office_dept:
        return f"Office - {plan.target_office_dept}"
    if plan.target_vessel_id:
        vessel_id = str(plan.target_vessel_id)
        return (vessel_label_map or {}).get(vessel_id.lower()) or vessel_id
    return "Unassigned"


def _window_label(plan: MasterAuditPlan) -> str:
    if plan.planned_window_start and plan.planned_window_end:
        return f"{plan.planned_window_start.isoformat()} -> {plan.planned_window_end.isoformat()}"
    if plan.planned_window_end:
        return f"Due by {plan.planned_window_end.isoformat()}"
    return "Window not set"
