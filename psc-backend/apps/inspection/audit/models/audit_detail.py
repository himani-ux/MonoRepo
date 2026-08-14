"""Audit inspection-level schema models for Phase 1 Step 1.1."""

from django.db import models

from .base import AuditCreatedMixin, AuditFullBaseModel, AuditSoftDeleteMixin


class AuditDetail(AuditFullBaseModel):
    psc_inspection_id = models.CharField(max_length=32, unique=True)
    vessel_id = models.CharField(max_length=32, null=True, blank=True)
    audit_classification = models.CharField(max_length=30)
    auditee_type = models.CharField(max_length=30)
    auditee_office_dept = models.CharField(max_length=40, null=True, blank=True)
    audit_subtype = models.CharField(max_length=40)
    audit_subtype_other = models.CharField(max_length=200, null=True, blank=True)
    lead_auditor_name = models.CharField(max_length=200)
    lead_auditor_designation = models.CharField(max_length=200, null=True, blank=True)
    lead_auditor_company = models.CharField(max_length=200)
    lead_auditor_qual = models.CharField(max_length=200, null=True, blank=True)
    conductor_user_id = models.CharField(max_length=100, null=True, blank=True)
    lead_auditor_user_id = models.CharField(max_length=100, null=True, blank=True)
    pic_user_id_resolved = models.CharField(max_length=100, null=True, blank=True)
    trigger_reason = models.CharField(max_length=40)
    audit_plan_id = models.UUIDField(null=True, blank=True)
    parent_audit_id = models.CharField(max_length=32, null=True, blank=True)
    audit_start_date = models.DateField()
    audit_end_date = models.DateField(null=True, blank=True)
    opening_meeting_at = models.DateTimeField(null=True, blank=True)
    closing_meeting_at = models.DateTimeField(null=True, blank=True)
    audit_scope = models.TextField(null=True, blank=True)
    terms_of_reference = models.TextField(null=True, blank=True)
    audit_summary = models.TextField(null=True, blank=True)
    equipment_tested = models.TextField(null=True, blank=True)
    prev_internal_ca_verified = models.CharField(max_length=10, null=True, blank=True)
    prev_external_ca_verified = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=30, default="PLANNED")
    external_audit_subtypes_csv = models.CharField(max_length=200, null=True, blank=True)
    external_audit_org_id = models.UUIDField(null=True, blank=True)
    external_audit_org_type = models.CharField(max_length=20, null=True, blank=True)
    external_lead_auditor_name = models.CharField(max_length=200, null=True, blank=True)
    external_lead_auditor_credential = models.CharField(max_length=200, null=True, blank=True)
    flag_state_code = models.CharField(max_length=10, null=True, blank=True)
    cycle_year = models.IntegerField(null=True, blank=True)
    parent_audit_event_id = models.UUIDField(null=True, blank=True)
    linked_cert_ids_csv = models.CharField(max_length=500, null=True, blank=True)
    certificate_impact = models.CharField(max_length=40, null=True, blank=True)
    external_closure_status = models.CharField(max_length=30, null=True, blank=True)
    is_cycle_resetting = models.BooleanField(default=False)
    cycle_reset_reason = models.TextField(null=True, blank=True)
    cycle_reset_authorised_by = models.CharField(max_length=100, null=True, blank=True)
    cycle_reset_authorised_at = models.DateTimeField(null=True, blank=True)
    late_registration_reason = models.TextField(null=True, blank=True)
    late_registered_by = models.CharField(max_length=100, null=True, blank=True)
    late_registered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_detail"


class AuditStandard(AuditCreatedMixin):
    audit_detail_id = models.UUIDField()
    standard_code = models.CharField(max_length=20)
    sequence_no = models.IntegerField(default=1)

    class Meta:
        db_table = "audit_standards"
        constraints = [
            models.UniqueConstraint(
                fields=["audit_detail_id", "standard_code"],
                name="UQ_audit_standards",
            )
        ]


class AuditTeamMember(AuditSoftDeleteMixin):
    audit_detail_id = models.UUIDField()
    member_name = models.CharField(max_length=200)
    member_designation = models.CharField(max_length=200, null=True, blank=True)
    member_company = models.CharField(max_length=200, null=True, blank=True)
    member_role = models.CharField(max_length=40, null=True, blank=True)
    sequence_no = models.IntegerField(default=1)

    class Meta:
        db_table = "audit_team_member"


class AuditMeetingAttendee(AuditSoftDeleteMixin):
    audit_detail_id = models.UUIDField()
    attendee_name = models.CharField(max_length=200)
    attendee_rank = models.CharField(max_length=100, null=True, blank=True)
    opening_present = models.BooleanField(default=False)
    closing_present = models.BooleanField(default=False)
    sequence_no = models.IntegerField(default=1)

    class Meta:
        db_table = "audit_meeting_attendee"


class AuditAreaSummary(AuditCreatedMixin):
    audit_detail_id = models.UUIDField()
    area_code = models.CharField(max_length=40)
    status = models.CharField(max_length=20, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "audit_area_summary"
        constraints = [
            models.UniqueConstraint(
                fields=["audit_detail_id", "area_code"],
                name="UQ_audit_area_summary",
            )
        ]


class AuditScheduleBlock(AuditSoftDeleteMixin):
    audit_detail_id = models.UUIDField()
    block_date = models.DateField(null=True, blank=True)
    time_from = models.TimeField(null=True, blank=True)
    time_to = models.TimeField(null=True, blank=True)
    activity = models.CharField(max_length=300, null=True, blank=True)
    sequence_no = models.IntegerField(default=1)

    class Meta:
        db_table = "audit_schedule_block"
