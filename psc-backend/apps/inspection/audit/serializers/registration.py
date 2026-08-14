"""Serializers for Audit registration."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.inspection.audit.models import AuditDetail
from apps.inspection.audit.services.registration import register_internal_audit


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
        required_fields = (
            "external_audit_org_id",
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

        completed_on = data.get("audit_end_date") or data["audit_start_date"]
        if completed_on < timezone.localdate() - timedelta(days=30):
            reason = (data.get("late_registration_reason") or "").strip()
            if len(reason) < 50:
                errors["late_registration_reason"] = "DPA late-registration override reason must be at least 50 characters."

        if not errors and has_doc and self._open_doc_exists(data):
            errors["flag_state_code"] = "An open DOC external audit already exists for this flag state and cycle year."

        if errors:
            raise serializers.ValidationError(errors)

    def _open_doc_exists(self, data) -> bool:
        return AuditDetail.objects.filter(
            audit_classification="EXTERNAL",
            audit_subtype__startswith="DOC_",
            flag_state_code=data.get("flag_state_code"),
            cycle_year=data.get("cycle_year"),
        ).exclude(status__in=OPEN_EXTERNAL_STATUSES).exists()

    def create(self, validated_data):
        return register_internal_audit(data=validated_data, user=self.context["request"].user)


class AuditRegistrationResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="audit_detail.id")
    inspection_id = serializers.UUIDField(source="inspection.id")
    status = serializers.CharField(source="audit_detail.status")
    audit_classification = serializers.CharField(source="audit_detail.audit_classification")
    auditee_type = serializers.CharField(source="audit_detail.auditee_type")
