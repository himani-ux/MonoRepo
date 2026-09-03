"""Serializers for Audit registration."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.inspection.audit.models import AuditDetail, MasterAuditPlan
from apps.inspection.audit.services.auditor_selection import (
    auditor_snapshot,
    get_external_org_by_id,
    resolve_external_org_for_vessel_standard,
)
from apps.inspection.audit.services.registration import (
    get_audit_plan_by_id,
    register_internal_audit,
    validate_registerable_audit_plan,
)


STANDARD_CHOICES = ("ISM", "ISPS", "MLC", "EMS", "DOC")
AUDIT_CLASSIFICATION_CHOICES = ("INTERNAL", "EXTERNAL")
AUDITEE_TYPE_CHOICES = ("VESSEL", "OFFICE_DEPT")
OFFICE_DEPT_CHOICES = ("CREW", "TECH", "PURCHASE", "IT", "MARINE", "SEQ", "OTHER")
INTERNAL_SUBTYPE_CHOICES = ("ANNUAL_INTERNAL",)
EXTERNAL_SUBTYPE_CHOICES = (
    "DOC_INITIAL",
    "DOC_INTERIM",
    "DOC_ANNUAL",
    "DOC_RENEWAL",
    "SMC_INITIAL",
    "SMC_INTERIM",
    "SMC_INTERMEDIATE",
    "SMC_RENEWAL",
    "MLC_INITIAL",
    "MLC_INTERIM",
    "MLC_INTERMEDIATE",
    "MLC_RENEWAL",
    "ISPS_INITIAL",
    "ISPS_INTERIM",
    "ISPS_INTERMEDIATE",
    "ISPS_RENEWAL",
    "ADDITIONAL",
)
TRIGGER_REASON_CHOICES = ("SCHEDULED", "ADDITIONAL", "FOLLOW_UP", "OTHER")
VERIFY_CHOICES = ("YES", "NO", "NA")
TEAM_ROLE_CHOICES = ("CO_AUDITOR", "OBSERVER", "TRAINEE", "OTHER")
EXTERNAL_ORG_TYPE_CHOICES = ("CLASS_SOCIETY", "FLAG_STATE", "RO", "OTHER")
OPEN_EXTERNAL_STATUSES = ("DPA_CLOSED", "CANCELLED")


class AuditTeamMemberRegistrationSerializer(serializers.Serializer):
    member_name = serializers.CharField(max_length=200)
    member_designation = serializers.CharField(max_length=200, required=False, allow_blank=True)
    member_company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    member_role = serializers.ChoiceField(choices=TEAM_ROLE_CHOICES, required=False, allow_blank=True)


class AuditMeetingAttendeeRegistrationSerializer(serializers.Serializer):
    attendee_name = serializers.CharField(max_length=200)
    attendee_rank = serializers.CharField(max_length=100, required=False, allow_blank=True)
    opening_present = serializers.BooleanField(default=False)
    closing_present = serializers.BooleanField(default=False)


class AuditScheduleBlockRegistrationSerializer(serializers.Serializer):
    block_date = serializers.DateField(required=False, allow_null=True)
    time_from = serializers.TimeField(required=False, allow_null=True)
    time_to = serializers.TimeField(required=False, allow_null=True)
    activity = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate(self, data):
        if data.get("time_from") and data.get("time_to") and data["time_to"] <= data["time_from"]:
            raise serializers.ValidationError({"time_to": "Schedule block end time must be after start time."})
        return data


class AuditRegistrationSerializer(serializers.Serializer):
    vessel_id = serializers.UUIDField()
    inspection_date = serializers.DateField()
    port_place = serializers.CharField(max_length=200)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    authority = serializers.CharField(max_length=200, required=False, allow_blank=True)
    inspector_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    report_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    def_reported = serializers.ChoiceField(choices=("YES", "NO"), default="NO")

    audit_classification = serializers.ChoiceField(choices=AUDIT_CLASSIFICATION_CHOICES)
    auditee_type = serializers.ChoiceField(choices=AUDITEE_TYPE_CHOICES)
    auditee_office_dept = serializers.ChoiceField(
        choices=OFFICE_DEPT_CHOICES,
        required=False,
        allow_blank=True,
    )
    audit_subtype = serializers.ChoiceField(choices=INTERNAL_SUBTYPE_CHOICES + EXTERNAL_SUBTYPE_CHOICES, required=False, allow_blank=True)
    audit_subtype_other = serializers.CharField(max_length=200, required=False, allow_blank=True)

    lead_auditor_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    lead_auditor_designation = serializers.CharField(max_length=200, required=False, allow_blank=True)
    lead_auditor_company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    lead_auditor_qual = serializers.CharField(max_length=200, required=False, allow_blank=True)
    lead_auditor_user_id = serializers.CharField(max_length=100, required=False, allow_blank=True)

    trigger_reason = serializers.ChoiceField(choices=TRIGGER_REASON_CHOICES, required=False, allow_blank=True)
    audit_plan_id = serializers.UUIDField(required=False, allow_null=True)
    parent_audit_id = serializers.CharField(max_length=32, required=False, allow_blank=True)

    audit_start_date = serializers.DateField()
    audit_end_date = serializers.DateField(required=False, allow_null=True)
    opening_meeting_at = serializers.DateTimeField(required=False, allow_null=True)
    closing_meeting_at = serializers.DateTimeField(required=False, allow_null=True)

    audit_scope = serializers.CharField(required=False, allow_blank=True)
    terms_of_reference = serializers.CharField(required=False, allow_blank=True)
    audit_summary = serializers.CharField(required=False, allow_blank=True)
    equipment_tested = serializers.CharField(required=False, allow_blank=True)
    prev_internal_ca_verified = serializers.ChoiceField(choices=VERIFY_CHOICES, required=False, allow_blank=True)
    prev_external_ca_verified = serializers.ChoiceField(choices=VERIFY_CHOICES, required=False, allow_blank=True)

    standards = serializers.ListField(
        child=serializers.ChoiceField(choices=STANDARD_CHOICES),
        allow_empty=False,
    )
    team_members = AuditTeamMemberRegistrationSerializer(many=True, required=False, default=list)
    attendees = AuditMeetingAttendeeRegistrationSerializer(many=True, required=False, default=list)
    schedule_blocks = AuditScheduleBlockRegistrationSerializer(many=True, required=False, default=list)

    external_audit_subtypes = serializers.ListField(
        child=serializers.ChoiceField(choices=EXTERNAL_SUBTYPE_CHOICES),
        required=False,
        default=list,
    )
    external_audit_org_id = serializers.UUIDField(required=False, allow_null=True)
    external_audit_org_type = serializers.ChoiceField(choices=EXTERNAL_ORG_TYPE_CHOICES, required=False, allow_blank=True)
    external_lead_auditor_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    external_lead_auditor_credential = serializers.CharField(max_length=200, required=False, allow_blank=True)
    flag_state_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    cycle_year = serializers.IntegerField(required=False, allow_null=True)
    linked_cert_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    external_report_file_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    external_report_file_path = serializers.CharField(max_length=500, required=False, allow_blank=True)
    external_report_mime_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    external_report_file_size = serializers.IntegerField(required=False, allow_null=True)
    late_registration_reason = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if data.get("external_audit_org_id") == "":
            data.pop("external_audit_org_id", None)
        return super().to_internal_value(data)

    def validate_standards(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Standards cannot contain duplicates.")
        return value

    def validate(self, data):
        if data["audit_classification"] == "INTERNAL":
            self._validate_internal(data)
        else:
            self._validate_external(data)
        return data

    def _validate_internal(self, data):
        self._apply_internal_plan_lead_auditor(data)
        required_fields = ("audit_subtype", "lead_auditor_name", "lead_auditor_company", "trigger_reason")
        errors = {field: "This field is required for internal audit registration." for field in required_fields if not data.get(field)}
        if errors:
            raise serializers.ValidationError(errors)
        if data["auditee_type"] == "OFFICE_DEPT" and not data.get("auditee_office_dept"):
            raise serializers.ValidationError({"auditee_office_dept": "Office department is required for office audits."})
        if data["auditee_type"] == "VESSEL":
            data["auditee_office_dept"] = None
        if data.get("audit_end_date") and data["audit_end_date"] < data["audit_start_date"]:
            raise serializers.ValidationError({"audit_end_date": "Audit end date cannot be before start date."})
        if data.get("closing_meeting_at") and data.get("opening_meeting_at"):
            if data["closing_meeting_at"] < data["opening_meeting_at"]:
                raise serializers.ValidationError({"closing_meeting_at": "Closing meeting cannot be before opening meeting."})

    def _validate_external(self, data):
        errors = {}
        subtypes = data.get("external_audit_subtypes") or []
        completed_on = data.get("audit_end_date") or data["audit_start_date"]
        self._apply_external_org_default(data, subtypes, completed_on, errors)
        required_fields = (
            "external_audit_org_type",
            "external_lead_auditor_name",
            "external_lead_auditor_credential",
            "external_report_file_name",
            "external_report_file_path",
            "external_report_mime_type",
        )
        if not subtypes:
            errors["external_audit_subtypes"] = "At least one external audit subtype is required."
        for field in required_fields:
            if not data.get(field):
                errors[field] = "This field is required for external audit registration."
        if data.get("audit_end_date") and data["audit_end_date"] < data["audit_start_date"]:
            errors["audit_end_date"] = "Audit end date cannot be before start date."

        data["audit_subtype"] = subtypes[0] if subtypes else ""
        data["audit_plan_id"] = None
        data["trigger_reason"] = "OTHER"
        data["lead_auditor_name"] = data.get("external_lead_auditor_name") or ""
        data["lead_auditor_company"] = data.get("external_audit_org_type") or "EXTERNAL"
        data["lead_auditor_qual"] = data.get("external_lead_auditor_credential") or ""
        data["lead_auditor_designation"] = "External auditor"
        data["prev_internal_ca_verified"] = ""

        has_doc = any(str(subtype).startswith("DOC_") for subtype in subtypes)
        if has_doc and not data.get("flag_state_code"):
            errors["flag_state_code"] = "Flag state code is required for DOC external audits."
        if has_doc and data.get("cycle_year") is None:
            errors["cycle_year"] = "DOC cycle year is required for DOC external audits."

        if completed_on < timezone.localdate() - timedelta(days=30):
            reason = (data.get("late_registration_reason") or "").strip()
            if len(reason) < 50:
                errors["late_registration_reason"] = "DPA late-registration override reason must be at least 50 characters."

        if not errors and has_doc and self._open_doc_exists(data):
            errors["flag_state_code"] = "An open DOC external audit already exists for this flag state and cycle year."

        if errors:
            raise serializers.ValidationError(errors)

    def _apply_internal_plan_lead_auditor(self, data):
        plan_id = data.get("audit_plan_id")
        if not plan_id:
            return
        try:
            plan = get_audit_plan_by_id(plan_id)
        except MasterAuditPlan.DoesNotExist as exc:
            raise serializers.ValidationError({"audit_plan_id": "Audit plan was not found."}) from exc

        try:
            validate_registerable_audit_plan(plan)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.detail) from exc

        self._validate_internal_plan_target(plan, data)
        if not plan.lead_auditor_user_id:
            raise serializers.ValidationError(
                {"lead_auditor_user_id": "Selected audit plan does not have a lead auditor assigned."}
            )

        snapshot = auditor_snapshot(
            plan.lead_auditor_user_id,
            standards=plan.audit_standards_csv,
            target_office_dept=plan.target_office_dept,
        )
        if snapshot is None:
            raise serializers.ValidationError(
                {"lead_auditor_user_id": "Plan lead auditor is not active or no longer qualified."}
            )

        data["lead_auditor_user_id"] = snapshot.user_id
        data["lead_auditor_name"] = snapshot.name
        data["lead_auditor_designation"] = snapshot.designation
        data["lead_auditor_company"] = snapshot.company
        data["lead_auditor_qual"] = snapshot.qualification

    def _validate_internal_plan_target(self, plan: MasterAuditPlan, data):
        auditee_type = data.get("auditee_type")
        if plan.target_vessel_id:
            if auditee_type != "VESSEL":
                raise serializers.ValidationError({"audit_plan_id": "Selected audit plan is for a vessel audit."})
            if str(plan.target_vessel_id).lower() != str(data.get("vessel_id")).lower():
                raise serializers.ValidationError({"audit_plan_id": "Selected audit plan belongs to another vessel."})
            return

        if plan.target_office_dept:
            if auditee_type != "OFFICE_DEPT":
                raise serializers.ValidationError({"audit_plan_id": "Selected audit plan is for an office department audit."})
            if plan.target_office_dept != data.get("auditee_office_dept"):
                raise serializers.ValidationError({"audit_plan_id": "Selected audit plan belongs to another office department."})

    def _apply_external_org_default(self, data, subtypes, completed_on, errors):
        if not data.get("external_audit_org_id"):
            organisation = resolve_external_org_for_vessel_standard(
                vessel_id=data.get("vessel_id"),
                standards=_external_standards_for_subtypes(subtypes),
                effective_on=completed_on,
            )
            if organisation is not None:
                data["external_audit_org_id"] = organisation.id
                data["external_audit_org_type"] = organisation.org_type

        if data.get("external_audit_org_id"):
            organisation = get_external_org_by_id(data["external_audit_org_id"])
            if organisation is None:
                errors["external_audit_org_id"] = "An active external audit organisation is required."
            elif not data.get("external_audit_org_type"):
                data["external_audit_org_type"] = organisation.org_type

    def _open_doc_exists(self, data) -> bool:
        return AuditDetail.objects.filter(
            audit_classification="EXTERNAL",
            audit_subtype__startswith="DOC_",
            flag_state_code=data.get("flag_state_code"),
            cycle_year=data.get("cycle_year"),
        ).exclude(status__in=OPEN_EXTERNAL_STATUSES).exists()

    def create(self, validated_data):
        return register_internal_audit(data=validated_data, user=self.context["request"].user)


def _external_standards_for_subtypes(subtypes) -> list[str]:
    standards: list[str] = []
    for subtype in subtypes:
        text = str(subtype or "").strip().upper()
        if text.startswith(("DOC_", "SMC_")):
            standard = "ISM"
        elif text.startswith("ISPS_"):
            standard = "ISPS"
        elif text.startswith("MLC_"):
            standard = "MLC"
        else:
            continue
        if standard not in standards:
            standards.append(standard)
    return standards


class AuditRegistrationResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="audit_detail.id")
    inspection_id = serializers.UUIDField(source="inspection.id")
    status = serializers.CharField(source="audit_detail.status")
    audit_classification = serializers.CharField(source="audit_detail.audit_classification")
    auditee_type = serializers.CharField(source="audit_detail.auditee_type")


class RegisteredAuditListItemSerializer(serializers.Serializer):
    def to_representation(self, instance: AuditDetail):
        vessel_label_map = self.context.get("vessel_label_map") or {}
        vessel_id = str(instance.vessel_id or "").strip()
        auditee_type = str(instance.auditee_type or "").strip().upper()

        if auditee_type == "OFFICE_DEPT":
            target_label = f"Office - {instance.auditee_office_dept or 'Not set'}"
        else:
            target_label = vessel_label_map.get(vessel_id.lower()) or f"Vessel {vessel_id or 'Not set'}"

        return {
            "id": str(instance.id),
            "audit_plan_id": str(instance.audit_plan_id) if instance.audit_plan_id else None,
            "target_label": target_label,
            "vessel_id": vessel_id or None,
            "audit_classification": instance.audit_classification,
            "auditee_type": instance.auditee_type,
            "auditee_office_dept": instance.auditee_office_dept,
            "audit_subtype": instance.audit_subtype,
            "lead_auditor_name": instance.lead_auditor_name,
            "lead_auditor_designation": instance.lead_auditor_designation or "",
            "audit_start_date": instance.audit_start_date.isoformat(),
            "audit_end_date": instance.audit_end_date.isoformat() if instance.audit_end_date else None,
            "status": instance.status,
            "created_date": instance.created_date.isoformat() if instance.created_date else None,
        }
