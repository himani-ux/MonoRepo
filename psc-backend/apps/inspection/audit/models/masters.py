"""Audit master-table schema models for Phase 1 Step 1.2."""

from django.db import models
from django.utils import timezone

from .base import AuditActiveManager, AuditCreatedMixin, AuditUuidPrimaryKeyMixin


class MasterUpdatedMixin(AuditCreatedMixin):
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class MasterAuditPlan(MasterUpdatedMixin):
    target_vessel_id = models.UUIDField(null=True, blank=True)
    target_office_dept = models.CharField(max_length=40, null=True, blank=True)
    audit_classification = models.CharField(max_length=30)
    audit_standards_csv = models.CharField(max_length=100)
    planned_window_start = models.DateField(null=True, blank=True)
    planned_window_end = models.DateField(null=True, blank=True)
    extended_due_date = models.DateField(null=True, blank=True)
    extension_form_ref = models.CharField(max_length=100, null=True, blank=True)
    extension_requested_at = models.DateTimeField(null=True, blank=True)
    extension_requested_by = models.CharField(max_length=100, null=True, blank=True)
    extension_requested_reason = models.TextField(null=True, blank=True)
    extension_approved_at = models.DateTimeField(null=True, blank=True)
    extension_approved_by = models.CharField(max_length=100, null=True, blank=True)
    extension_approved_reason = models.TextField(null=True, blank=True)
    flag_notified = models.BooleanField(default=False)
    flag_notification_date = models.DateField(null=True, blank=True)
    flag_notification_ref = models.CharField(max_length=100, null=True, blank=True)
    flag_notification_attachment = models.CharField(max_length=500, null=True, blank=True)
    is_additional = models.BooleanField(default=False)
    additional_reason = models.TextField(null=True, blank=True)
    trigger_event_type = models.CharField(max_length=30, null=True, blank=True)
    trigger_event_ref = models.CharField(max_length=200, null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    next_planned_date = models.DateField(null=True, blank=True)
    cancelled_by = models.CharField(max_length=100, null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, default="PLANNED")
    is_deleted = models.BooleanField(default=False)
    objects = AuditActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "master_audit_plan"


class MasterAuditClassification(AuditCreatedMixin):
    classification_code = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_audit_classification"


class MasterAuditSubtype(AuditCreatedMixin):
    classification_code = models.CharField(max_length=30)
    subtype_code = models.CharField(max_length=40)
    display_name = models.CharField(max_length=120)
    is_external = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_audit_subtype"
        constraints = [
            models.UniqueConstraint(
                fields=["classification_code", "subtype_code"],
                name="UQ_master_audit_subtype",
            )
        ]


class MasterAuditFindingCategory(AuditCreatedMixin):
    category_code = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=100)
    default_target_days = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "master_audit_finding_category"


class MasterAuditArea(AuditCreatedMixin):
    area_code = models.CharField(max_length=40, unique=True)
    display_name = models.CharField(max_length=120)
    is_vessel_only = models.BooleanField(default=False)
    sequence_no = models.IntegerField()

    class Meta:
        db_table = "master_audit_area"


class MasterAuditChecklist(AuditCreatedMixin):
    checklist_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    auditee_type = models.CharField(max_length=30)
    scope_dept = models.CharField(max_length=40, null=True, blank=True)
    ship_type_scope = models.CharField(max_length=60, null=True, blank=True)
    source_form_ref = models.CharField(max_length=40)
    code_version = models.CharField(max_length=40, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_audit_checklist"


class MasterAuditChecklistItem(AuditCreatedMixin):
    master_audit_checklist_id = models.UUIDField()
    location_code = models.CharField(max_length=200, null=True, blank=True)
    item_code = models.CharField(max_length=20)
    question = models.TextField()
    guideline = models.TextField(null=True, blank=True)
    regulation_ref = models.CharField(max_length=500, null=True, blank=True)
    ksm_sms_ref = models.CharField(max_length=200, null=True, blank=True)
    ship_type = models.CharField(max_length=30, null=True, blank=True)
    sequence_no = models.IntegerField()

    class Meta:
        db_table = "master_audit_checklist_item"


class MasterAuditQualifiedAuditor(MasterUpdatedMixin):
    user_id = models.CharField(max_length=100)
    qualification_text = models.CharField(max_length=200)
    qualification_date = models.DateField()
    expiry_date = models.DateField()
    scope_standards_csv = models.CharField(max_length=60)
    qualifying_body = models.CharField(max_length=200, null=True, blank=True)
    certificate_attachment_id = models.UUIDField(null=True, blank=True)
    auditor_scope = models.CharField(max_length=20)
    qualified_for_seq = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_audit_qualified_auditor"


class MasterHodAssignment(AuditCreatedMixin):
    dept = models.CharField(max_length=40)
    user_id = models.CharField(max_length=100)
    is_acting = models.BooleanField(default=False)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "master_hod_assignment"


class MasterRcaTemplate(MasterUpdatedMixin):
    category = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    template_text = models.TextField()
    example_evidence_hint = models.CharField(max_length=500, null=True, blank=True)
    applicable_def_categories = models.CharField(max_length=200, null=True, blank=True)
    code_version = models.CharField(max_length=40, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_rca_template"


class MasterSlackChannel(AuditCreatedMixin):
    channel_name = models.CharField(max_length=80)
    webhook_url = models.CharField(max_length=500)
    scope_type = models.CharField(max_length=20)
    scope_value = models.CharField(max_length=100, null=True, blank=True)
    notification_types_csv = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_audit_slack_channel"


class MasterAuditWindowRule(AuditCreatedMixin):
    standard_code = models.CharField(max_length=20)
    subtype_code = models.CharField(max_length=40)
    window_open_offset_months = models.IntegerField()
    window_close_offset_months = models.IntegerField()
    cadence_months = models.IntegerField()
    regulatory_citation = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_audit_window_rule"


class MasterIsmClause(AuditCreatedMixin):
    clause_no = models.CharField(max_length=20)
    clause_text = models.TextField()
    section_no = models.CharField(max_length=10, null=True, blank=True)
    code_version = models.CharField(max_length=40, default="ISM 2018")

    class Meta:
        db_table = "master_ism_clause"


class MasterIspsClause(AuditCreatedMixin):
    section_no = models.CharField(max_length=20)
    section_title = models.CharField(max_length=300)
    section_text = models.TextField(null=True, blank=True)
    code_version = models.CharField(max_length=40, default="ISPS 2003")

    class Meta:
        db_table = "master_isps_clause"


class MasterMlcTitle(AuditCreatedMixin):
    title_no = models.CharField(max_length=20)
    regulation_no = models.CharField(max_length=20, null=True, blank=True)
    standard_a_code = models.CharField(max_length=20, null=True, blank=True)
    title_text = models.TextField()
    code_version = models.CharField(
        max_length=60,
        default="MLC 2006 (2014/2016/2018/2022 amendments)",
    )

    class Meta:
        db_table = "master_mlc_title"


class MasterSolasChapter(AuditCreatedMixin):
    chapter_no = models.CharField(max_length=10)
    regulation_no = models.CharField(max_length=20, null=True, blank=True)
    title = models.CharField(max_length=300)
    code_version = models.CharField(max_length=40)

    class Meta:
        db_table = "master_solas_chapter"


class MasterStcwSection(AuditCreatedMixin):
    section_no = models.CharField(max_length=20)
    title = models.CharField(max_length=300)
    code_version = models.CharField(max_length=100)

    class Meta:
        db_table = "master_stcw_section"


class MasterMarpolAnnex(AuditCreatedMixin):
    annex_no = models.CharField(max_length=10)
    regulation_no = models.CharField(max_length=20, null=True, blank=True)
    title = models.CharField(max_length=300)
    code_version = models.CharField(max_length=40)

    class Meta:
        db_table = "master_marpol_annex"


class MasterColregRule(AuditCreatedMixin):
    rule_no = models.CharField(max_length=10)
    title = models.CharField(max_length=300)
    code_version = models.CharField(max_length=40)

    class Meta:
        db_table = "master_colreg_rule"


class MasterKsmSmsChapter(AuditCreatedMixin):
    chapter_code = models.CharField(max_length=40)
    chapter_name = models.CharField(max_length=200)
    code_version = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        db_table = "master_ksm_sms_chapter"


class MasterExternalAuditOrg(AuditCreatedMixin):
    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=20)
    country = models.CharField(max_length=80, null=True, blank=True)
    linked_class_society_ref = models.CharField(max_length=40, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_external_audit_org"


class VesselAuditRoDelegation(AuditCreatedMixin):
    target_vessel_id = models.UUIDField()
    standard_code = models.CharField(max_length=20)
    master_external_audit_org_id = models.UUIDField()
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "vessel_audit_ro_delegation"


class MasterExternalAuditor(AuditUuidPrimaryKeyMixin):
    name = models.CharField(max_length=200)
    master_external_audit_org_id = models.UUIDField(null=True, blank=True)
    review_status = models.CharField(max_length=20, default="PENDING_REVIEW")
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "master_external_auditor"


class MasterExternalAuditorCategoryMap(AuditCreatedMixin):
    free_text_pattern = models.CharField(max_length=200)
    canonical_iacs_code = models.CharField(max_length=20)

    class Meta:
        db_table = "master_external_auditor_category_map"
