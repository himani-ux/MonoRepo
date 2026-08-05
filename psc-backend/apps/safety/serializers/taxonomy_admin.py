from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import (
    MasterImmediateCause,
    MasterLossType,
    MasterMscatTaxonomy,
    MasterSafetyBiasGuard,
    MasterSafetyIncidentType,
    MasterSoiArea,
    MasterSoiAreaItem,
    IncidentWeatherOption,
    InjuryDropdownOption,
    SafetyCaseStudy,
    SOIChecklistVersion,
)


class MasterMscatTaxonomySerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterMscatTaxonomy
        fields = (
            "id",
            "legacy_int_id",
            "category_id",
            "category_name",
            "subcode_id",
            "subcode_description",
            "cause_type",
            "active",
            "seeded_version",
            "schema_version",
            "updated_by",
            "updated_date",
        )
        read_only_fields = ("id", "legacy_int_id", "seeded_version", "schema_version", "updated_by", "updated_date")


class MasterImmediateCauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterImmediateCause
        fields = (
            "id",
            "legacy_int_id",
            "category_id",
            "category_name",
            "subcode_id",
            "subcode_description",
            "cause_type",
            "active",
            "seeded_version",
            "schema_version",
            "updated_by",
            "updated_date",
        )
        read_only_fields = ("id", "legacy_int_id", "seeded_version", "schema_version", "updated_by", "updated_date")


class MasterLossTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterLossType
        fields = (
            "id",
            "legacy_int_id",
            "loss_type_id",
            "loss_type_name",
            "description",
            "active",
            "seeded_version",
        )
        read_only_fields = ("id", "legacy_int_id", "seeded_version")


class MasterSOIAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterSoiArea
        fields = (
            "id",
            "legacy_int_id",
            "area_id",
            "area_name",
            "section_12_flag",
            "display_order",
            "active",
            "seeded_version",
        )
        read_only_fields = ("id", "legacy_int_id", "seeded_version")


class MasterSOIAreaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterSoiAreaItem
        fields = (
            "id",
            "legacy_int_id",
            "area_id",
            "area_name",
            "subsection_id",
            "subsection_name",
            "item_number",
            "description",
            "tier",
            "active",
            "seeded_version",
            "schema_version",
            "updated_by",
            "updated_date",
        )
        read_only_fields = ("id", "legacy_int_id", "seeded_version", "schema_version", "updated_by", "updated_date")


class SOIChecklistVersionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOIChecklistVersion
        fields = (
            "id",
            "legacy_int_id",
            "version_label",
            "effective_from",
            "effective_to",
            "source_description",
            "active",
            "created_by",
            "created_date",
        )
        read_only_fields = ("id", "legacy_int_id", "created_by", "created_date")


class MasterSafetyBiasGuardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterSafetyBiasGuard
        fields = (
            "id",
            "legacy_int_id",
            "guard_code",
            "guard_name",
            "family",
            "description",
            "bit_position",
            "active",
        )
        read_only_fields = fields


class MasterSafetyIncidentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterSafetyIncidentType
        fields = (
            "id",
            "legacy_int_id",
            "type_code",
            "type_name",
            "imo_reportable",
            "description",
            "active",
        )
        read_only_fields = ("id", "legacy_int_id")


class IncidentWeatherOptionSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="get_field_key_display", read_only=True)

    class Meta:
        model = IncidentWeatherOption
        fields = (
            "id",
            "field_key",
            "field_label",
            "option_label",
            "display_order",
            "active",
        )
        read_only_fields = fields


class InjuryDropdownOptionSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="get_field_key_display", read_only=True)

    class Meta:
        model = InjuryDropdownOption
        fields = (
            "id",
            "field_key",
            "field_label",
            "option_label",
            "display_order",
            "active",
        )
        read_only_fields = fields


class SafetyCaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyCaseStudy
        fields = (
            "id",
            "legacy_int_id",
            "slug",
            "title",
            "event_type",
            "loss_summary",
            "incident_date",
            "immediate_cause_codes",
            "basic_cause_codes",
            "narrative",
            "recommendations",
            "source_label",
            "active",
            "display_order",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = ("id", "legacy_int_id", "created_by", "created_date", "updated_by", "updated_date")
