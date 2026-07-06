from __future__ import annotations

import json
from typing import Any

from rest_framework import serializers

from apps.certs.serializers.onboarding import serialize_onboarding_vessel


class VesselLifecycleReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=20)


class VesselFlagChangeSerializer(VesselLifecycleReasonSerializer):
    newFlagState = serializers.CharField(max_length=64)
    effectiveDate = serializers.DateField()


class VesselClassChangeSerializer(VesselLifecycleReasonSerializer):
    newClassSociety = serializers.CharField(max_length=64)
    effectiveDate = serializers.DateField()


class VesselSaleHandoverSerializer(VesselLifecycleReasonSerializer):
    handoverDate = serializers.DateField()
    customCertIds = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)
    watermarkRecipient = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")


class VesselDecommissionSerializer(VesselLifecycleReasonSerializer):
    decommissionDate = serializers.DateField()


def serialize_vessel_config(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "vesselId": str(row.get("vessel_id")) if row.get("vessel_id") else None,
        "anniversaryDate": row.get("anniversary_date"),
        "shipType": row.get("ship_type"),
        "marineSuptUserId": row.get("marine_supt_user_id"),
        "technicalManagerUserId": row.get("technical_manager_user_id"),
        "lifecycleStatus": row.get("lifecycle_status") or "not_onboarded",
        "pendingDisposalStartedAt": row.get("pending_disposal_started_at"),
        "saleHandoverBundleBlobId": str(row.get("sale_handover_bundle_blob_id")) if row.get("sale_handover_bundle_blob_id") else None,
        "flagChangePending": bool(row.get("flag_change_pending")),
        "flagChangeEvent": _json_object(row.get("flag_change_event_json")),
        "classChangePending": bool(row.get("class_change_pending")),
        "mandatoryCoverageOverrideReason": row.get("mandatory_coverage_override_reason"),
        "mandatoryCoverageOverrideAt": row.get("mandatory_coverage_override_at"),
        "mandatoryCoverageOverrideBy": row.get("mandatory_coverage_override_by"),
        "iwsAgeGateDisabled": bool(row.get("iws_age_gate_disabled")),
        "updatedAt": row.get("updated_at"),
        "updatedBy": row.get("updated_by"),
    }


def serialize_lifecycle_result(result: dict[str, Any]) -> dict[str, Any]:
    artifact = result.get("artifact") or {}
    return {
        "vessel": serialize_onboarding_vessel(result.get("vessel") or {}),
        "config": serialize_vessel_config(result.get("after")),
        "affectedTrackedItems": int(result.get("affected_tracked_items") or 0),
        "saleHandoverArtifact": _serialize_artifact(artifact) if artifact else None,
    }


def _serialize_artifact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "printId": str(row.get("print_id") or ""),
        "bundleZipBlobId": str(row.get("bundle_zip_blob_id")) if row.get("bundle_zip_blob_id") else None,
        "systemStateHash": row.get("system_state_hash"),
    }


def _json_object(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None
