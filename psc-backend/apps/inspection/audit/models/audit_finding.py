"""Audit finding-level schema models for Phase 1 Step 1.1."""

from django.db import models
from django.utils import timezone

from .base import AuditSoftDeleteMixin, AuditUuidPrimaryKeyMixin


class AuditFinding(AuditSoftDeleteMixin):
    psc_deficiency_id = models.CharField(max_length=32, unique=True)
    audit_detail_id = models.UUIDField()
    audit_classification = models.CharField(max_length=30)
    finding_type = models.CharField(max_length=20)
    nc_category = models.CharField(max_length=20, null=True, blank=True)
    observation_category = models.CharField(max_length=40, null=True, blank=True)
    standard_code = models.CharField(max_length=20, null=True, blank=True)
    rule_book_type = models.CharField(max_length=20, null=True, blank=True)
    rule_clause_id = models.UUIDField(null=True, blank=True)
    clause_ref_text = models.CharField(max_length=200, null=True, blank=True)
    objective_evidence = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    checklist_item_id = models.UUIDField(null=True, blank=True)
    priority = models.CharField(max_length=20, default="MEDIUM")
    original_due_date = models.DateField(null=True, blank=True)
    extended_due_date = models.DateField(null=True, blank=True)
    extension_reason = models.TextField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    certificates_at_risk = models.CharField(max_length=100, null=True, blank=True)
    is_fleetwide_relevance = models.BooleanField(default=False)
    linked_circular_id = models.UUIDField(null=True, blank=True)
    is_external = models.BooleanField(default=False)
    applies_to_cert_ids_csv = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "audit_finding"


class AuditFindingClause(AuditSoftDeleteMixin):
    audit_finding_id = models.UUIDField()
    rule_book_type = models.CharField(max_length=20)
    rule_clause_id = models.UUIDField(null=True, blank=True)
    clause_ref_text = models.CharField(max_length=200, null=True, blank=True)
    clause_subref_text = models.CharField(max_length=200, null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "audit_finding_clause"


class AuditFindingNC(AuditUuidPrimaryKeyMixin):
    audit_finding_id = models.UUIDField(unique=True)
    immediate_action_text = models.TextField(null=True, blank=True)
    immediate_action_completed_at = models.DateField(null=True, blank=True)
    master_immediate_sign_name = models.CharField(max_length=200, null=True, blank=True)
    master_immediate_sign_at = models.DateTimeField(null=True, blank=True)
    rca_method = models.CharField(max_length=40, null=True, blank=True)
    rca_method_other = models.CharField(max_length=200, null=True, blank=True)
    rca_template_id = models.UUIDField(null=True, blank=True)
    problem_statement = models.TextField(null=True, blank=True)
    why_1 = models.TextField(null=True, blank=True)
    why_2 = models.TextField(null=True, blank=True)
    why_3 = models.TextField(null=True, blank=True)
    why_4 = models.TextField(null=True, blank=True)
    why_5 = models.TextField(null=True, blank=True)
    root_cause_categories = models.CharField(max_length=200, null=True, blank=True)
    root_cause_summary = models.TextField(null=True, blank=True)
    corrective_action_text = models.TextField(null=True, blank=True)
    target_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    preventive_action_text = models.TextField(null=True, blank=True)
    sms_amendment_required = models.BooleanField(default=False)
    sms_amendment_doc_ref = models.CharField(max_length=200, null=True, blank=True)
    drafted_by_user_id = models.CharField(max_length=100, null=True, blank=True)
    effectiveness_review_date = models.DateField(null=True, blank=True)
    effectiveness_review_method = models.CharField(max_length=40, null=True, blank=True)
    effectiveness_assessment_text = models.TextField(null=True, blank=True)
    effectiveness_outcome = models.CharField(max_length=20, null=True, blank=True)
    effectiveness_further_action_text = models.TextField(null=True, blank=True)
    effectiveness_signer_name = models.CharField(max_length=200, null=True, blank=True)
    effectiveness_signer_at = models.DateTimeField(null=True, blank=True)
    effectiveness_overdue = models.BooleanField(default=False)
    is_external_tier = models.CharField(max_length=20, null=True, blank=True)
    acceptance_review_date = models.DateField(null=True, blank=True)
    acceptance_rca_adequacy_text = models.TextField(null=True, blank=True)
    acceptance_decision = models.CharField(max_length=20, null=True, blank=True)
    acceptance_return_reason = models.TextField(null=True, blank=True)
    acceptance_signer_name = models.CharField(max_length=200, null=True, blank=True)
    acceptance_signer_at = models.DateTimeField(null=True, blank=True)
    verifying_auditor_name = models.CharField(max_length=200, null=True, blank=True)
    verifying_authority_org = models.CharField(max_length=200, null=True, blank=True)
    verification_method = models.CharField(max_length=40, null=True, blank=True)
    certificate_endorsement_type = models.CharField(max_length=40, null=True, blank=True)
    certificate_endorsement_ref = models.CharField(max_length=100, null=True, blank=True)
    auditor_assessment_text = models.TextField(null=True, blank=True)
    final_closure_status = models.CharField(max_length=30, null=True, blank=True)
    resubmit_by_date = models.DateField(null=True, blank=True)
    auditor_verification_sign_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_finding_nc"


class AuditFindingOBS(AuditUuidPrimaryKeyMixin):
    audit_finding_id = models.UUIDField(unique=True)
    responded_by_name = models.CharField(max_length=200, null=True, blank=True)
    responded_by_rank = models.CharField(max_length=100, null=True, blank=True)
    target_closure_date = models.DateField(null=True, blank=True)
    immediate_action_text = models.TextField(null=True, blank=True)
    root_cause_text = models.TextField(null=True, blank=True)
    corrective_action_text = models.TextField(null=True, blank=True)
    preventive_action_text = models.TextField(null=True, blank=True)
    sms_amendment_required = models.BooleanField(default=False)
    sms_amendment_doc_ref = models.CharField(max_length=200, null=True, blank=True)
    actual_closure_date = models.DateField(null=True, blank=True)
    master_sign_name = models.CharField(max_length=200, null=True, blank=True)
    master_sign_at = models.DateTimeField(null=True, blank=True)
    acceptance_review_date = models.DateField(null=True, blank=True)
    acceptance_adequacy_text = models.TextField(null=True, blank=True)
    acceptance_decision = models.CharField(max_length=20, null=True, blank=True)
    acceptance_return_reason = models.TextField(null=True, blank=True)
    acceptance_signer_name = models.CharField(max_length=200, null=True, blank=True)
    acceptance_signer_at = models.DateTimeField(null=True, blank=True)
    verifying_auditor_name = models.CharField(max_length=200, null=True, blank=True)
    verifying_authority_org = models.CharField(max_length=200, null=True, blank=True)
    verification_method = models.CharField(max_length=40, null=True, blank=True)
    auditor_remarks_text = models.TextField(null=True, blank=True)
    closure_status = models.CharField(max_length=30, null=True, blank=True)
    resubmit_by_date = models.DateField(null=True, blank=True)
    auditor_verification_sign_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_finding_obs"
