"""Serializers for KSM-F-OBS-001 Audit Observation closure endpoints."""

from __future__ import annotations

from rest_framework import serializers

from apps.inspection.audit.services.obs_closure import (
    ACCEPTANCE_DECISIONS,
    CLOSURE_STATUSES,
    VERIFICATION_METHODS,
)


class AuditObsPartBSerializer(serializers.Serializer):
    responded_by_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    responded_by_rank = serializers.CharField(required=False, allow_blank=True, max_length=100)
    target_closure_date = serializers.DateField(required=False, allow_null=True)
    immediate_action_text = serializers.CharField(required=False, allow_blank=True)
    root_cause_text = serializers.CharField(required=False, allow_blank=True)
    corrective_action_text = serializers.CharField(required=False, allow_blank=True)
    preventive_action_text = serializers.CharField(required=False, allow_blank=True)
    sms_amendment_required = serializers.BooleanField(required=False, default=False)
    sms_amendment_doc_ref = serializers.CharField(required=False, allow_blank=True, max_length=200)
    actual_closure_date = serializers.DateField(required=False, allow_null=True)
    master_sign_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    master_sign_at = serializers.DateTimeField(required=False, allow_null=True)


class AuditObsPartCSerializer(serializers.Serializer):
    acceptance_review_date = serializers.DateField(required=False, allow_null=True)
    acceptance_adequacy_text = serializers.CharField(required=False, allow_blank=True)
    acceptance_decision = serializers.ChoiceField(
        choices=tuple(sorted(ACCEPTANCE_DECISIONS)),
        required=False,
        allow_blank=True,
    )
    acceptance_return_reason = serializers.CharField(required=False, allow_blank=True)
    acceptance_signer_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    acceptance_signer_at = serializers.DateTimeField(required=False, allow_null=True)


class AuditObsPartDSerializer(serializers.Serializer):
    verifying_auditor_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    verifying_authority_org = serializers.CharField(required=False, allow_blank=True, max_length=200)
    verification_method = serializers.ChoiceField(
        choices=tuple(sorted(VERIFICATION_METHODS)),
        required=False,
        allow_blank=True,
    )
    auditor_remarks_text = serializers.CharField(required=False, allow_blank=True)
    closure_status = serializers.ChoiceField(
        choices=tuple(sorted(CLOSURE_STATUSES)),
        required=False,
        allow_blank=True,
    )
    resubmit_by_date = serializers.DateField(required=False, allow_null=True)
    auditor_verification_sign_at = serializers.DateTimeField(required=False, allow_null=True)


PART_SERIALIZERS = {
    "part-b": AuditObsPartBSerializer,
    "part-c": AuditObsPartCSerializer,
    "part-d": AuditObsPartDSerializer,
}
