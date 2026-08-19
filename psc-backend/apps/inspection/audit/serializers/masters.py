"""Serializers for operational Audit master-data APIs."""

from __future__ import annotations

from django.db.models import Q
from rest_framework import serializers

from apps.inspection.audit.models import (
    MasterAuditQualifiedAuditor,
    MasterExternalAuditOrg,
    VesselAuditRoDelegation,
)


EXTERNAL_ORG_TYPES = ("CLASS_SOCIETY", "FLAG_STATE", "RO", "OTHER")


class QualifiedAuditorSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterAuditQualifiedAuditor
        fields = (
            "id",
            "user_id",
            "qualification_text",
            "qualification_date",
            "expiry_date",
            "scope_standards_csv",
            "qualifying_body",
            "certificate_attachment_id",
            "auditor_scope",
            "qualified_for_seq",
            "is_active",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = ("id", "created_by", "created_date", "updated_by", "updated_date")

    def validate(self, attrs):
        qualification_date = attrs.get("qualification_date", getattr(self.instance, "qualification_date", None))
        expiry_date = attrs.get("expiry_date", getattr(self.instance, "expiry_date", None))
        if qualification_date and expiry_date and expiry_date < qualification_date:
            raise serializers.ValidationError({"expiry_date": "Expiry date cannot be before qualification date."})
        return attrs


class ExternalAuditOrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterExternalAuditOrg
        fields = (
            "id",
            "name",
            "org_type",
            "country",
            "linked_class_society_ref",
            "is_active",
            "created_by",
            "created_date",
        )
        read_only_fields = ("id", "created_by", "created_date")

    def validate_org_type(self, value):
        value = str(value or "").strip().upper()
        if value not in EXTERNAL_ORG_TYPES:
            raise serializers.ValidationError(
                f"Organisation type must be one of: {', '.join(EXTERNAL_ORG_TYPES)}."
            )
        return value


class VesselRoDelegationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselAuditRoDelegation
        fields = (
            "id",
            "target_vessel_id",
            "standard_code",
            "master_external_audit_org_id",
            "effective_from",
            "effective_to",
            "created_by",
            "created_date",
        )
        read_only_fields = ("id", "created_by", "created_date")

    def validate(self, attrs):
        organisation_id = attrs.get(
            "master_external_audit_org_id",
            getattr(self.instance, "master_external_audit_org_id", None),
        )
        if not MasterExternalAuditOrg.objects.filter(id=organisation_id, is_active=True).exists():
            raise serializers.ValidationError(
                {"master_external_audit_org_id": "An active external audit organisation is required."}
            )

        vessel_id = attrs.get("target_vessel_id", getattr(self.instance, "target_vessel_id", None))
        standard_code = str(attrs.get("standard_code", getattr(self.instance, "standard_code", ""))).strip().upper()
        effective_from = attrs.get("effective_from", getattr(self.instance, "effective_from", None))
        effective_to = attrs.get("effective_to", getattr(self.instance, "effective_to", None))
        if effective_to and effective_to < effective_from:
            raise serializers.ValidationError({"effective_to": "Effective-to date cannot be before effective-from date."})

        overlap = VesselAuditRoDelegation.objects.filter(
            target_vessel_id=vessel_id,
            standard_code=standard_code,
        )
        if self.instance is not None:
            overlap = overlap.exclude(id=self.instance.id)
        overlap = overlap.filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=effective_from),
            Q(effective_from__lte=effective_to) if effective_to else Q(),
        )
        if overlap.exists():
            raise serializers.ValidationError(
                "Another RO delegation already covers this vessel and standard for the selected dates."
            )
        attrs["standard_code"] = standard_code
        return attrs
