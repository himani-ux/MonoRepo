"""Serializers for KSM-F-NC-001 Audit NC closure endpoints."""

from __future__ import annotations

from rest_framework import serializers

from apps.inspection.audit.services.nc_closure import (
    ACCEPTANCE_DECISIONS,
    CERTIFICATE_ENDORSEMENT_TYPES,
    CERTIFICATES_AT_RISK,
    EFFECTIVENESS_OUTCOMES,
    EFFECTIVENESS_REVIEW_METHODS,
    FINAL_CLOSURE_STATUSES,
    RCA_METHODS,
    ROOT_CAUSE_CATEGORIES,
    VERIFICATION_METHODS,
)


class AuditNcPartBSerializer(serializers.Serializer):
    immediate_action_text = serializers.CharField(required=False, allow_blank=True)
    immediate_action_completed_at = serializers.DateField(required=False, allow_null=True)
    master_immediate_sign_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    master_immediate_sign_at = serializers.DateTimeField(required=False, allow_null=True)


class AuditNcPartCSerializer(serializers.Serializer):
    rca_method = serializers.ChoiceField(choices=tuple(sorted(RCA_METHODS)), required=False, allow_blank=True)
    rca_method_other = serializers.CharField(required=False, allow_blank=True, max_length=200)
    rca_template_id = serializers.UUIDField(required=False, allow_null=True)
    problem_statement = serializers.CharField(required=False, allow_blank=True)
    why_1 = serializers.CharField(required=False, allow_blank=True)
    why_2 = serializers.CharField(required=False, allow_blank=True)
    why_3 = serializers.CharField(required=False, allow_blank=True)
    why_4 = serializers.CharField(required=False, allow_blank=True)
    why_5 = serializers.CharField(required=False, allow_blank=True)
    root_cause_categories = serializers.ListField(
        child=serializers.ChoiceField(choices=tuple(sorted(ROOT_CAUSE_CATEGORIES))),
        required=False,
        allow_empty=True,
    )
    root_cause_summary = serializers.CharField(required=False, allow_blank=True)
    clc_item_ids = serializers.ListField(
        child=serializers.CharField(max_length=10),
        required=False,
        allow_empty=True,
    )
    custom_cause_text = serializers.CharField(required=False, allow_blank=True, max_length=500)


class AuditNcDraftSerializer(AuditNcPartBSerializer, AuditNcPartCSerializer):
    comment = serializers.CharField(required=False, allow_blank=True)


class AuditNcPartDSerializer(serializers.Serializer):
    corrective_action_text = serializers.CharField(required=False, allow_blank=True)
    target_completion_date = serializers.DateField(required=False, allow_null=True)
    actual_completion_date = serializers.DateField(required=False, allow_null=True)
    preventive_action_text = serializers.CharField(required=False, allow_blank=True)
    sms_amendment_required = serializers.BooleanField(required=False, default=False)
    sms_amendment_doc_ref = serializers.CharField(required=False, allow_blank=True, max_length=200)


class AuditNcPartESerializer(serializers.Serializer):
    certificates_at_risk = serializers.ListField(
        child=serializers.ChoiceField(choices=tuple(sorted(CERTIFICATES_AT_RISK))),
        required=False,
        allow_empty=True,
    )
    effectiveness_review_date = serializers.DateField(required=False, allow_null=True)
    effectiveness_review_method = serializers.ChoiceField(
        choices=tuple(sorted(EFFECTIVENESS_REVIEW_METHODS)),
        required=False,
        allow_blank=True,
    )
    effectiveness_assessment_text = serializers.CharField(required=False, allow_blank=True)
    effectiveness_outcome = serializers.ChoiceField(
        choices=tuple(sorted(EFFECTIVENESS_OUTCOMES)),
        required=False,
        allow_blank=True,
    )
    effectiveness_further_action_text = serializers.CharField(required=False, allow_blank=True)
    effectiveness_signer_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    effectiveness_signer_at = serializers.DateTimeField(required=False, allow_null=True)


class AuditNcPartFSerializer(serializers.Serializer):
    certificates_at_risk = serializers.ListField(
        child=serializers.ChoiceField(choices=tuple(sorted(CERTIFICATES_AT_RISK))),
        required=False,
        allow_empty=True,
    )
    acceptance_review_date = serializers.DateField(required=False, allow_null=True)
    acceptance_rca_adequacy_text = serializers.CharField(required=False, allow_blank=True)
    acceptance_decision = serializers.ChoiceField(
        choices=tuple(sorted(ACCEPTANCE_DECISIONS)),
        required=False,
        allow_blank=True,
    )
    acceptance_return_reason = serializers.CharField(required=False, allow_blank=True)
    acceptance_signer_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    acceptance_signer_at = serializers.DateTimeField(required=False, allow_null=True)


class AuditNcPartGSerializer(serializers.Serializer):
    verifying_auditor_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    verifying_authority_org = serializers.CharField(required=False, allow_blank=True, max_length=200)
    verification_method = serializers.ChoiceField(
        choices=tuple(sorted(VERIFICATION_METHODS)),
        required=False,
        allow_blank=True,
    )
    certificate_endorsement_type = serializers.ChoiceField(
        choices=tuple(sorted(CERTIFICATE_ENDORSEMENT_TYPES)),
        required=False,
        allow_blank=True,
    )
    certificate_endorsement_ref = serializers.CharField(required=False, allow_blank=True, max_length=100)
    auditor_assessment_text = serializers.CharField(required=False, allow_blank=True)
    final_closure_status = serializers.ChoiceField(
        choices=tuple(sorted(FINAL_CLOSURE_STATUSES)),
        required=False,
        allow_blank=True,
    )
    resubmit_by_date = serializers.DateField(required=False, allow_null=True)
    auditor_verification_sign_at = serializers.DateTimeField(required=False, allow_null=True)


PART_SERIALIZERS = {
    "part-b": AuditNcPartBSerializer,
    "part-c": AuditNcPartCSerializer,
    "part-d": AuditNcPartDSerializer,
    "part-e": AuditNcPartESerializer,
    "part-f": AuditNcPartFSerializer,
    "part-g": AuditNcPartGSerializer,
}
