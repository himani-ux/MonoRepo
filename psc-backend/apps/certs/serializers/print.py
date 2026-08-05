from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

from rest_framework import serializers


PRINT_SCOPES = {"per_vessel_full", "per_vessel_partial", "per_section_fleetwide", "custom_selection", "share_bundle"}
WATERMARK_SCOPES = {"NONE", "INTERNAL", "AUDIT_COPY", "MASTER_COPY", "DRAFT"}


class PrintArtifactRequestSerializer(serializers.Serializer):
    scope = serializers.ChoiceField(choices=sorted(PRINT_SCOPES - {"share_bundle"}))
    vesselIds = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)
    sections = serializers.ListField(child=serializers.CharField(max_length=64), required=False, allow_empty=True)
    filters = serializers.DictField(required=False)
    customCertIds = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)
    watermarkApplied = serializers.ChoiceField(choices=sorted(WATERMARK_SCOPES), required=False, default="NONE")
    watermarkRecipient = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    recipientEmail = serializers.EmailField(required=False, allow_blank=True, default="")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        scope = attrs["scope"]
        vessel_ids = [str(value) for value in attrs.get("vesselIds", [])]
        sections = [str(value).strip() for value in attrs.get("sections", []) if str(value).strip()]
        custom_cert_ids = [str(value) for value in attrs.get("customCertIds", [])]
        if scope in {"per_vessel_full", "per_vessel_partial"} and not vessel_ids:
            raise serializers.ValidationError({"vesselIds": "Select at least one vessel."})
        if scope == "per_section_fleetwide" and not sections:
            raise serializers.ValidationError({"sections": "Select at least one section for fleet-wide print."})
        if scope == "custom_selection" and not vessel_ids:
            raise serializers.ValidationError({"vesselIds": "Select the vessel scope for custom print."})
        if scope == "custom_selection" and not custom_cert_ids:
            raise serializers.ValidationError({"customCertIds": "Select at least one certificate for custom print."})
        attrs["vesselIds"] = vessel_ids
        attrs["sections"] = sections
        attrs["customCertIds"] = custom_cert_ids
        attrs["filters"] = dict(attrs.get("filters") or {})
        attrs["watermarkApplied"] = str(attrs.get("watermarkApplied") or "NONE").upper()
        attrs["watermarkRecipient"] = str(attrs.get("watermarkRecipient") or "").strip()
        attrs["recipientEmail"] = str(attrs.get("recipientEmail") or "").strip()
        return attrs


class ShareBundleRequestSerializer(PrintArtifactRequestSerializer):
    scope = serializers.ChoiceField(choices=["share_bundle"], required=False, default="share_bundle")
    watermarkApplied = serializers.ChoiceField(choices=["MASTER_COPY"], required=False, default="MASTER_COPY")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs["scope"] = "share_bundle"
        attrs["watermarkApplied"] = "MASTER_COPY"
        attrs = super().validate(attrs)
        if not attrs.get("vesselIds"):
            raise serializers.ValidationError({"vesselIds": "Select a vessel for the share bundle."})
        if not attrs.get("sections") and not attrs.get("customCertIds"):
            raise serializers.ValidationError({"sections": "Select at least one certificate section for the share bundle."})
        return attrs


def serialize_print_artifact(row: dict[str, Any]) -> dict[str, Any]:
    pdf_blob_id = str(row["pdf_blob_id"]) if row.get("pdf_blob_id") else None
    excel_blob_id = str(row["excel_blob_id"]) if row.get("excel_blob_id") else None
    bundle_zip_blob_id = str(row["bundle_zip_blob_id"]) if row.get("bundle_zip_blob_id") else None
    return {
        "printId": str(row.get("print_id")),
        "scope": row.get("scope"),
        "vessels": _json_list(row.get("vessels_json")),
        "sections": _json_list(row.get("sections_json")),
        "filters": _json_object(row.get("filters_json")) or {},
        "customCertIds": _json_list(row.get("custom_cert_ids_json")),
        "userId": row.get("user_id"),
        "userRole": row.get("user_role"),
        "timestampUtc": row.get("timestamp_utc"),
        "systemStateHash": row.get("system_state_hash"),
        "watermarkApplied": row.get("watermark_applied"),
        "watermarkRecipient": row.get("watermark_recipient") or "",
        "pdfBlobId": pdf_blob_id,
        "excelBlobId": excel_blob_id,
        "bundleZipBlobId": bundle_zip_blob_id,
        "downloadUrls": _download_urls(
            print_id=str(row.get("print_id") or ""),
            pdf_blob_id=pdf_blob_id,
            excel_blob_id=excel_blob_id,
            bundle_zip_blob_id=bundle_zip_blob_id,
        ),
        "recipientEmail": row.get("recipient_email") or "",
        "emailDeliveryStatus": row.get("email_delivery_status") or "not_requested",
        "emailDeliveryMessage": row.get("email_delivery_message") or "",
        "pageCount": row.get("page_count"),
        "generationStatus": row.get("generation_status"),
        "failureMessage": row.get("failure_message") or "",
    }


def _json_list(value: Any) -> list[Any]:
    parsed = _json_object(value)
    return parsed if isinstance(parsed, list) else []


def _json_object(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _download_urls(
    *,
    print_id: str,
    pdf_blob_id: str | None,
    excel_blob_id: str | None,
    bundle_zip_blob_id: str | None,
) -> dict[str, str | None]:
    encoded_print_id = quote(print_id, safe="")
    return {
        "pdf": f"/api/certs/print/artifacts/{encoded_print_id}/download/pdf/" if pdf_blob_id else None,
        "excel": f"/api/certs/print/artifacts/{encoded_print_id}/download/excel/" if excel_blob_id else None,
        "zip": f"/api/certs/print/artifacts/{encoded_print_id}/download/zip/" if bundle_zip_blob_id else None,
    }
