"""Serializers for operational Audit master-data APIs."""

from __future__ import annotations

from django.db.models import Q
from rest_framework import serializers

from apps.inspection.audit.models import (
    AuditQualifyingBody,
    MasterAuditQualifiedAuditor,
    MasterExternalAuditOrg,
    MasterHodAssignment,
    VesselAuditRoDelegation,
)
from apps.inspection.audit.services.auditor_selection import resolve_user_identity


EXTERNAL_ORG_TYPES = ("CLASS_SOCIETY", "FLAG_STATE", "RO", "OTHER")


class OfficeUserLookupSerializer(serializers.Serializer):
    employee_id = serializers.CharField()
    display_name = serializers.CharField(allow_blank=True, allow_null=True)
    employee_name = serializers.CharField(allow_blank=True, allow_null=True)
    username = serializers.CharField(allow_blank=True, allow_null=True)
    employee_role = serializers.CharField(allow_blank=True, allow_null=True)
    department = serializers.CharField(allow_blank=True, allow_null=True)
    role_name = serializers.CharField(allow_blank=True, allow_null=True)


class AuditQualifyingBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditQualifyingBody
        fields = (
            "id",
            "body_name",
            "is_active",
            "is_deleted",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = ("id", "created_by", "created_date", "updated_by", "updated_date")
        extra_kwargs = {"body_name": {"validators": []}}

    def validate_body_name(self, value):
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("Qualifying body name is required.")
        return value


class QualifiedAuditorSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    identity_source = serializers.SerializerMethodField()

    class Meta:
        model = MasterAuditQualifiedAuditor
        fields = (
            "id",
            "user_id",
            "display_name",
            "designation",
            "company",
            "identity_source",
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

    def _identity(self, obj) -> dict[str, str]:
        cache = getattr(self, "_identity_cache", None)
        if cache is None:
            cache = {}
            self._identity_cache = cache
        if obj.user_id not in cache:
            cache[obj.user_id] = resolve_user_identity(obj.user_id)
        return cache[obj.user_id]

    def get_display_name(self, obj):
        return self._identity(obj)["name"]

    def get_designation(self, obj):
        return self._identity(obj)["designation"]

    def get_company(self, obj):
        return self._identity(obj)["company"]

    def get_identity_source(self, obj):
        return self._identity(obj)["source"]


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


class HodAssignmentSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()

    class Meta:
        model = MasterHodAssignment
        fields = (
            "id",
            "dept",
            "user_id",
            "display_name",
            "designation",
            "company",
            "is_acting",
            "effective_from",
            "effective_to",
            "created_by",
            "created_date",
        )
        read_only_fields = ("id", "created_by", "created_date")

    def validate(self, attrs):
        dept = str(attrs.get("dept", getattr(self.instance, "dept", "")) or "").strip().upper()
        effective_from = attrs.get("effective_from", getattr(self.instance, "effective_from", None))
        effective_to = attrs.get("effective_to", getattr(self.instance, "effective_to", None))
        if effective_to and effective_from and effective_to < effective_from:
            raise serializers.ValidationError({"effective_to": "Effective-to date cannot be before effective-from date."})
        if attrs.get("is_acting", getattr(self.instance, "is_acting", False)) and effective_from and effective_to:
            if (effective_to - effective_from).days > 90:
                raise serializers.ValidationError({"effective_to": "Acting HoD assignment cannot exceed 90 days."})
        attrs["dept"] = dept
        return attrs

    def _identity(self, obj) -> dict[str, str]:
        cache = getattr(self, "_hod_identity_cache", None)
        if cache is None:
            cache = {}
            self._hod_identity_cache = cache
        if obj.user_id not in cache:
            cache[obj.user_id] = resolve_user_identity(obj.user_id)
        return cache[obj.user_id]

    def get_display_name(self, obj):
        return self._identity(obj)["name"]

    def get_designation(self, obj):
        return self._identity(obj)["designation"]

    def get_company(self, obj):
        return self._identity(obj)["company"]
