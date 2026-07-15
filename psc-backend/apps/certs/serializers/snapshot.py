from __future__ import annotations

import json
from typing import Any

from rest_framework import serializers


CLASS_SOCIETIES = {"NK", "KR", "BV"}
PARSE_STATUSES = {"pending", "success", "partial", "failed"}
CERT_OR_SURVEY_KINDS = {"renewal", "intermediate", "annual", "periodic", "n/a"}


class ClassSnapshotUploadSerializer(serializers.Serializer):
    vesselId = serializers.UUIDField()
    classSociety = serializers.ChoiceField(choices=sorted(CLASS_SOCIETIES))
    printedOnDate = serializers.DateField(required=False, allow_null=True)


class ClassCodeMappingAddSerializer(serializers.Serializer):
    catalogId = serializers.UUIDField()
    certOrSurveyKind = serializers.ChoiceField(choices=sorted(CERT_OR_SURVEY_KINDS))
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)
    reason = serializers.CharField(min_length=10, max_length=2000)


def serialize_class_code_mapping(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": str(row.get("mapping_id")),
        "classSociety": row.get("class_society"),
        "classCodeOrName": row.get("class_code_or_name"),
        "catalogId": str(row["catalog_id"]) if row.get("catalog_id") else None,
        "certOrSurveyKind": row.get("cert_or_survey_kind"),
        "notes": row.get("notes"),
        "version": row.get("version"),
        "active": bool(row.get("active")),
        "createdAt": row.get("created_at"),
        "createdBy": row.get("created_by"),
        "updatedAt": row.get("updated_at"),
        "updatedBy": row.get("updated_by"),
    }


def serialize_class_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("snapshot_id")),
        "vesselId": str(row["vessel_id"]) if row.get("vessel_id") else None,
        "vesselName": row.get("vessel_name"),
        "imo": row.get("imo_number"),
        "classSociety": row.get("class_society"),
        "pdfBlobId": str(row["pdf_blob_id"]) if row.get("pdf_blob_id") else None,
        "filename": row.get("filename"),
        "sizeBytes": row.get("content_size_bytes"),
        "printedOnDate": row.get("printed_on_date"),
        "uploadedBy": row.get("uploaded_by"),
        "uploadedAt": row.get("uploaded_at"),
        "parserVersion": row.get("parser_version"),
        "parseStatus": row.get("parse_status"),
        "parseStartedAt": row.get("parse_started_at"),
        "parseCompletedAt": row.get("parse_completed_at"),
        "parserTimeout": bool(row.get("parser_timeout")),
        "retryCount": row.get("retry_count"),
        "parsedPayload": _json_object(row.get("parsed_payload_json")),
        "parsedPayloadSchemaVersion": row.get("parsed_payload_schema_version"),
        "reconciliationRunId": str(row["reconciliation_run_id"]) if row.get("reconciliation_run_id") else None,
        "uploadSha256": row.get("upload_sha256"),
        "supersededUserError": bool(row.get("superseded_user_error")),
    }


def serialize_reconciliation_run(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("run_id")),
        "snapshotId": str(row["snapshot_id"]) if row.get("snapshot_id") else None,
        "vesselId": str(row["vessel_id"]) if row.get("vessel_id") else None,
        "vesselName": row.get("vessel_name"),
        "imo": row.get("imo_number"),
        "classSociety": row.get("class_society"),
        "printedOnDate": row.get("printed_on_date"),
        "parseStatus": row.get("parse_status"),
        "parserVersion": row.get("parser_version"),
        "ranAt": row.get("ran_at"),
        "matchesCount": row.get("matches_count"),
        "mismatchesCount": row.get("mismatches_count"),
        "missingInCatalogCount": row.get("missing_in_catalog_count"),
        "missingInClassCount": row.get("missing_in_class_count"),
        "conditionalStcDetectedCount": row.get("conditional_stc_detected_count"),
        "extendedPostponedDetectedCount": row.get("extended_postponed_detected_count"),
        "unmappedLowConfidenceCount": row.get("unmapped_low_confidence_count"),
        "notificationsSent": _json_object(row.get("notifications_sent_json")) or [],
        "mappingVersionUsed": row.get("mapping_version_used"),
        "anomalyBreaches": _json_object(row.get("anomaly_breaches_json")) or [],
    }


def serialize_reconciliation_flag(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("flag_id")),
        "runId": str(row["run_id"]) if row.get("run_id") else None,
        "bucket": row.get("bucket"),
        "catalogId": str(row["catalog_id"]) if row.get("catalog_id") else None,
        "catalogDisplayName": row.get("catalog_display_name"),
        "trackedItemId": str(row["tracked_item_id"]) if row.get("tracked_item_id") else None,
        "classRowExtract": _json_object(row.get("class_row_extract_json")),
        "diff": _json_object(row.get("diff_json")) or {},
        "reviewedBy": row.get("reviewed_by"),
        "reviewedAt": row.get("reviewed_at"),
        "resolutionAction": row.get("resolution_action"),
        "resolvedAt": row.get("resolved_at"),
    }


def _json_object(value: Any) -> dict[str, Any] | list[Any] | None:
    if not value:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, (dict, list)) else None
