from __future__ import annotations

import json
from typing import Any

from rest_framework import serializers

from apps.certs.iopp_variant import IOPP_VARIANT_CATALOG_ERROR, is_iopp_variant_catalog_code


VALIDITY_TYPES = {"full", "conditional", "short_term", "permanent"}
ISSUING_AUTHORITY_TYPES = {"flag", "class", "RO", "manufacturer", "company", "ko_other"}
SUBMISSION_SCOPES = {"master_only", "all_ranks_with_approval"}
APPLICABILITY_MODES = {"all_matching_type", "specific_vessel_ids"}
SHIP_TYPES = ("all", "bulk_carrier", "tanker", "container", "gas_carrier", "chemical_tanker")
SHIP_TYPE_SET = set(SHIP_TYPES)
ROLLUP_DYNAMIC_CHILDREN_ERROR = (
    "Portable equipment roll-up rows must stay one TrackedItem per vessel; "
    "keep per-unit detail in the service report PDF."
)
ROLLUP_ROW_TOKENS = (
    "PORTABLE-FIRE-EXTINGUISHER",
    "PORTABLE-EXTINGUISHER",
    "EXTINGUISHER-ANNUAL",
    "LIFEBUOY",
    "LIFEBUOYS",
    "LIFE-JACKET",
    "LIFE-JACKETS",
    "LIFEJACKET",
    "LIFEJACKETS",
    "HATCH-COVER",
    "HATCH-COVERS",
)
TONNAGE_TAX_TRADE_SECTION_ID = 3
TONNAGE_TAX_SECTION_ERROR = "Tonnage Tax catalog rows must stay in Trade & Commercial."
TONNAGE_TAX_CADENCE_ERROR = (
    "Tonnage Tax cadence is configured per vessel on TrackedItem, not on the catalog row."
)


class CatalogRowWriteSerializer(serializers.Serializer):
    canonicalCode = serializers.CharField(max_length=64, required=False)
    sectionId = serializers.IntegerField(required=False)
    displayName = serializers.CharField(max_length=256, required=False)
    shortName = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    printSectionLabel = serializers.CharField(max_length=128, required=False)
    validityType = serializers.ChoiceField(choices=sorted(VALIDITY_TYPES), required=False)
    cadenceMonths = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=32767)
    cadenceCustomDays = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    issuingAuthorityType = serializers.ChoiceField(choices=sorted(ISSUING_AUTHORITY_TYPES), required=False)
    isClassTracked = serializers.BooleanField(required=False)
    submissionScope = serializers.ChoiceField(choices=sorted(SUBMISSION_SCOPES), required=False)
    parentId = serializers.UUIDField(required=False, allow_null=True)
    relationshipTypeDefault = serializers.CharField(max_length=32, required=False, allow_blank=True, allow_null=True)
    applicableShipTypes = serializers.ListField(
        child=serializers.CharField(max_length=32),
        required=False,
        allow_empty=False,
    )
    mandatoryForAllVessels = serializers.BooleanField(required=False)
    applicabilityMode = serializers.ChoiceField(choices=sorted(APPLICABILITY_MODES), required=False)
    specificVesselIds = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)
    parentSupportsDynamicChildren = serializers.BooleanField(required=False)
    ageGateMaxYears = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=32767)
    retainAllVersions = serializers.BooleanField(required=False)
    linkedPmsComponentId = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    alertLeadOverrides = serializers.JSONField(required=False, allow_null=True)
    regulatoryAnchor = serializers.CharField(max_length=256, required=False, allow_blank=True, allow_null=True)
    legacyRemarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    printOrder = serializers.IntegerField(required=False)
    isActive = serializers.BooleanField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    create_required_fields = (
        "canonicalCode",
        "sectionId",
        "displayName",
        "printSectionLabel",
        "validityType",
        "issuingAuthorityType",
        "submissionScope",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if self.context.get("is_create"):
            missing = [field for field in self.create_required_fields if field not in attrs]
            if missing:
                raise serializers.ValidationError({field: "This field is required." for field in missing})
        if "canonicalCode" in attrs and is_iopp_variant_catalog_code(attrs["canonicalCode"]):
            raise serializers.ValidationError({"canonicalCode": IOPP_VARIANT_CATALOG_ERROR})
        if attrs.get("parentSupportsDynamicChildren") and is_portable_rollup_catalog_row(attrs):
            raise serializers.ValidationError({"parentSupportsDynamicChildren": ROLLUP_DYNAMIC_CHILDREN_ERROR})
        _validate_tonnage_tax_catalog_row(attrs, self.context.get("current_row"))
        if attrs.get("validityType") == "permanent" and attrs.get("cadenceMonths") not in (None, 0):
            raise serializers.ValidationError({"cadenceMonths": "Permanent catalog rows must not carry cadence months."})
        if "applicableShipTypes" in attrs:
            attrs["applicableShipTypes"] = _normalize_ship_types(attrs["applicableShipTypes"])
        mode = attrs.get("applicabilityMode")
        specific_vessel_ids = attrs.get("specificVesselIds")
        if mode == "specific_vessel_ids" and not specific_vessel_ids:
            raise serializers.ValidationError(
                {"specificVesselIds": "At least one vessel ID is required for specific-vessel applicability."}
            )
        if mode == "all_matching_type":
            attrs["specificVesselIds"] = []
        if self.context.get("is_create") and specific_vessel_ids and attrs.get("applicabilityMode", "all_matching_type") != "specific_vessel_ids":
            raise serializers.ValidationError(
                {"applicabilityMode": "Use specific_vessel_ids when specific vessel IDs are supplied."}
            )
        return attrs


def _json_load(value: object, fallback: object) -> object:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return fallback


def _normalize_ship_types(values: list[str]) -> list[str]:
    normalized = []
    for value in values:
        ship_type = str(value).strip().lower()
        if ship_type not in SHIP_TYPE_SET:
            raise serializers.ValidationError(
                {"applicableShipTypes": f"Unsupported ship type '{value}'."}
            )
        if ship_type not in normalized:
            normalized.append(ship_type)
    if "all" in normalized and len(normalized) > 1:
        raise serializers.ValidationError(
            {"applicableShipTypes": "'all' cannot be combined with specific ship types."}
        )
    return [ship_type for ship_type in SHIP_TYPES if ship_type in normalized]


def _normalized_token_text(value: object) -> str:
    return str(value or "").strip().upper().replace("_", "-").replace(" ", "-")


def _is_tonnage_tax_text(*values: object) -> bool:
    haystack = " ".join(_normalized_token_text(value) for value in values)
    return "TONNAGE" in haystack and "TAX" in haystack


def _validate_tonnage_tax_catalog_row(attrs: dict[str, Any], current_row: object = None) -> None:
    current = current_row if isinstance(current_row, dict) else {}
    canonical_code = attrs.get("canonicalCode", current.get("canonical_code"))
    display_name = attrs.get("displayName", current.get("display_name"))
    short_name = attrs.get("shortName", current.get("short_name"))
    if not _is_tonnage_tax_text(canonical_code, display_name, short_name):
        return

    section_id = attrs.get("sectionId", current.get("section_id"))
    if section_id is not None and int(section_id) != TONNAGE_TAX_TRADE_SECTION_ID:
        raise serializers.ValidationError({"sectionId": TONNAGE_TAX_SECTION_ERROR})
    if "cadenceMonths" in attrs and attrs.get("cadenceMonths") is not None:
        raise serializers.ValidationError({"cadenceMonths": TONNAGE_TAX_CADENCE_ERROR})
    if "cadenceCustomDays" in attrs and attrs.get("cadenceCustomDays") is not None:
        raise serializers.ValidationError({"cadenceCustomDays": TONNAGE_TAX_CADENCE_ERROR})


def is_portable_rollup_catalog_row(attrs: dict[str, Any]) -> bool:
    haystack = " ".join(
        _normalized_token_text(attrs.get(key))
        for key in ("canonicalCode", "displayName", "shortName")
    )
    return any(token in haystack for token in ROLLUP_ROW_TOKENS)


def _camel_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("catalog_id")),
        "canonicalCode": row.get("canonical_code"),
        "sectionId": row.get("section_id"),
        "sectionCode": row.get("section_code"),
        "sectionName": row.get("section_name"),
        "displayName": row.get("display_name"),
        "shortName": row.get("short_name"),
        "printSectionLabel": row.get("print_section_label"),
        "validityType": row.get("validity_type"),
        "cadenceMonths": row.get("cadence_months"),
        "cadenceCustomDays": row.get("cadence_custom_days"),
        "issuingAuthorityType": row.get("issuing_authority_type"),
        "isClassTracked": bool(row.get("is_class_tracked")),
        "submissionScope": row.get("submission_scope"),
        "parentId": str(row["parent_id"]) if row.get("parent_id") else None,
        "relationshipTypeDefault": row.get("relationship_type_default"),
        "applicableShipTypes": _json_load(row.get("applicable_ship_types"), ["all"]),
        "mandatoryForAllVessels": bool(row.get("mandatory_for_all_vessels")),
        "applicabilityMode": row.get("applicability_mode"),
        "specificVesselIds": _json_load(row.get("specific_vessel_ids"), []),
        "parentSupportsDynamicChildren": bool(row.get("parent_supports_dynamic_children")),
        "ageGateMaxYears": row.get("age_gate_max_years"),
        "retainAllVersions": bool(row.get("retain_all_versions")),
        "linkedPmsComponentId": row.get("linked_pms_component_id"),
        "alertLeadOverrides": _json_load(row.get("alert_lead_overrides"), None),
        "regulatoryAnchor": row.get("regulatory_anchor"),
        "legacyRemarks": row.get("legacy_remarks"),
        "printOrder": row.get("print_order"),
        "isActive": bool(row.get("is_active")),
        "createdAt": row.get("created_at"),
        "createdBy": row.get("created_by"),
        "updatedAt": row.get("updated_at"),
        "updatedBy": row.get("updated_by"),
    }


def serialize_catalog_row(row: dict[str, Any]) -> dict[str, Any]:
    return _camel_row(row)


def serialize_catalog_section(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("section_id"),
        "sectionId": row.get("section_id"),
        "sectionCode": row.get("section_code"),
        "displayName": row.get("display_name"),
        "sortOrder": row.get("sort_order"),
        "activeRowCount": row.get("active_row_count", 0),
    }


def serialize_catalog_audit_event(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("audit_id")),
        "timestampUtc": row.get("timestamp_utc"),
        "vesselId": str(row["vessel_id"]) if row.get("vessel_id") else None,
        "actorUserId": row.get("actor_user_id"),
        "actorRole": row.get("actor_role"),
        "action": row.get("action"),
        "entityType": row.get("entity_type"),
        "entityId": row.get("entity_id"),
        "before": _json_load(row.get("before_json"), None),
        "after": _json_load(row.get("after_json"), None),
        "reason": row.get("reason"),
        "eventMetadata": _json_load(row.get("event_metadata"), None),
        "retentionTier": row.get("retention_tier"),
        "archivedAt": row.get("archived_at"),
        "schemaVersion": row.get("schema_version"),
    }
