from __future__ import annotations

import json
from typing import Any

from rest_framework import serializers

from apps.certs.serializers.tracked_item import serialize_pdf_blob, serialize_tracked_item


ONBOARDING_STEPS = (
    (1, "Vessel selection"),
    (2, "Vessel profile"),
    (3, "Cert PDF batch ingest"),
    (4, "Class status upload"),
    (5, "Reconciliation review"),
    (6, "Coverage gate"),
    (7, "FM sign-off"),
)


class OnboardingProfileSerializer(serializers.Serializer):
    anniversaryDate = serializers.DateField(required=True)
    shipType = serializers.CharField(max_length=32, required=True)
    marineSuptUserId = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    technicalManagerUserId = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)


class OnboardingStartSerializer(serializers.Serializer):
    vesselId = serializers.CharField(max_length=64, required=False, allow_blank=True)
    imo = serializers.CharField(max_length=32, required=False, allow_blank=True)
    shipType = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not (attrs.get("vesselId") or attrs.get("imo")):
            raise serializers.ValidationError({"vesselId": "vesselId or imo is required."})
        return attrs


class OnboardingBatchCreateSerializer(serializers.Serializer):
    pdfBlobIds = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=10,
        required=True,
    )
    onboardingSessionId = serializers.UUIDField(required=False, allow_null=True)


class OnboardingBatchCommitSerializer(serializers.Serializer):
    acknowledgeWarnings = serializers.BooleanField(required=False, default=False)
    supersedeDecisions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )


class CoverageOverrideSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=20)


class OnboardingActionReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OnboardingRollbackSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=20)


def serialize_onboarding_hub_row(row: dict[str, Any]) -> dict[str, Any]:
    vessel = row.get("vessel") or {}
    config = row.get("config") or {}
    return {
        "vessel": serialize_onboarding_vessel(vessel),
        "config": serialize_vessel_config(config),
        "batchCount": row.get("batchCount", 0),
        "currentStep": row.get("currentStep", 1),
        "mandatoryCoveragePercent": row.get("mandatoryCoveragePercent", 0),
        "pendingFmSignoff": bool(row.get("pendingFmSignoff")),
        "lastActivity": row.get("lastActivity"),
        "startedAt": row.get("startedAt"),
        "startedBy": row.get("startedBy"),
    }


def serialize_wizard_state(state: dict[str, Any]) -> dict[str, Any]:
    config = state.get("config") or {}
    batches = [serialize_batch(row) for row in state.get("batches") or []]
    coverage = serialize_coverage(state.get("coverage") or {})
    current_step = _current_step(config, batches, coverage)
    return {
        "vessel": serialize_onboarding_vessel(state.get("vessel") or {}),
        "config": serialize_vessel_config(config),
        "steps": [
            {
                "number": number,
                "label": label,
                "status": _step_status(number, current_step),
            }
            for number, label in ONBOARDING_STEPS
        ],
        "currentStep": current_step,
        "batches": batches,
        "mandatoryCoverage": coverage,
        "trackedItems": [serialize_tracked_item(row) for row in state.get("items") or []],
    }


def serialize_gap_fill_state(state: dict[str, Any]) -> dict[str, Any]:
    items_by_blob_id = state.get("itemsByBlobId") or {}
    pdfs = []
    for blob in state.get("pdfs") or []:
        serialized_blob = serialize_pdf_blob(blob)
        tracked_item = items_by_blob_id.get(str(blob.get("blob_id")))
        pdfs.append(
            {
                **serialized_blob,
                "trackedItem": serialize_tracked_item(tracked_item) if tracked_item else None,
                "fieldStates": _field_states(serialized_blob.get("ocrPayload")),
            }
        )
    return {
        "batch": serialize_batch(state.get("batch") or {}),
        "vessel": serialize_onboarding_vessel(state.get("vessel") or {}),
        "pdfs": pdfs,
    }


def serialize_validation_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "batch": serialize_batch(result.get("batch") or {}),
        "validationBlocks": result.get("blocks") or [],
        "validationWarns": result.get("warns") or [],
        "canCommit": bool(result.get("canCommit")),
        "requiresWarningAck": bool(result.get("requiresWarningAck")),
        "preview": result.get("preview") or {},
    }


def serialize_onboarding_vessel(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("vessel_id")) if row.get("vessel_id") else None,
        "code": row.get("vessel_code"),
        "name": row.get("vessel_name"),
        "imo": row.get("imo_number"),
        "flag": row.get("flag"),
        "classSociety": row.get("class_society"),
    }


def serialize_vessel_config(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "vesselId": str(row.get("vessel_id")) if row.get("vessel_id") else None,
        "anniversaryDate": row.get("anniversary_date"),
        "shipType": row.get("ship_type"),
        "marineSuptUserId": row.get("marine_supt_user_id"),
        "technicalManagerUserId": row.get("technical_manager_user_id"),
        "lifecycleStatus": row.get("lifecycle_status"),
        "mandatoryCoverageOverrideReason": row.get("mandatory_coverage_override_reason"),
        "mandatoryCoverageOverrideAt": row.get("mandatory_coverage_override_at"),
        "mandatoryCoverageOverrideBy": row.get("mandatory_coverage_override_by"),
        "updatedAt": row.get("updated_at"),
        "updatedBy": row.get("updated_by"),
    }


def serialize_batch(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("batch_id")) if row.get("batch_id") else None,
        "onboardingSessionId": str(row.get("onboarding_session_id")) if row.get("onboarding_session_id") else None,
        "pdfBlobIds": _json_list(row.get("pdf_blob_ids_json")),
        "pdfCount": row.get("pdf_count") or 0,
        "status": row.get("status"),
        "createdAt": row.get("created_at"),
        "createdBy": row.get("created_by"),
        "ocrCompletedAt": row.get("ocr_completed_at"),
        "reviewStartedAt": row.get("review_started_at"),
        "committedAt": row.get("committed_at"),
        "committedBy": row.get("committed_by"),
        "cancelledAt": row.get("cancelled_at"),
        "cancelledBy": row.get("cancelled_by"),
        "validationBlocks": _json_list(row.get("validation_blocks_json")),
        "validationWarns": _json_list(row.get("validation_warns_json")),
        "reportCsvBlobId": str(row.get("report_csv_blob_id")) if row.get("report_csv_blob_id") else None,
    }


def serialize_coverage(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "percent": row.get("percent", 0),
        "mandatoryCount": row.get("mandatoryCount", 0),
        "coveredCount": row.get("coveredCount", 0),
        "missing": [_serialize_missing_coverage_item(item) for item in row.get("missing") or []],
        "overrideActive": bool(row.get("overrideActive")),
        "overrideReason": row.get("overrideReason"),
        "overrideAt": row.get("overrideAt"),
        "overrideBy": row.get("overrideBy"),
    }


def _serialize_missing_coverage_item(row: dict[str, Any]) -> dict[str, Any]:
    if "catalogId" in row:
        return row
    return {
        "catalogId": str(row["catalog_id"]) if row.get("catalog_id") else None,
        "catalogCode": row.get("catalog_code"),
        "displayName": row.get("catalog_display_name"),
        "shortName": row.get("catalog_short_name"),
        "sectionId": row.get("catalog_section_id"),
        "sectionCode": row.get("catalog_section_code"),
        "sectionName": row.get("catalog_section_name"),
        "trackedItemId": str(row.get("tracked_item_id")) if row.get("tracked_item_id") else None,
        "status": row.get("status"),
        "reason": "pending_first_upload",
    }


def _current_step(config: dict[str, Any], batches: list[dict[str, Any]], coverage: dict[str, Any]) -> int:
    lifecycle = str(config.get("lifecycle_status") or "")
    if lifecycle == "active":
        return 7
    if (
        lifecycle == "onboarding_in_progress"
        and not config.get("anniversary_date")
        and str(config.get("ship_type") or "") == "all"
        and not config.get("marine_supt_user_id")
        and not config.get("technical_manager_user_id")
    ):
        return 1
    if not config.get("anniversary_date"):
        return 2
    if not batches or any(batch.get("status") in {"queued", "ocr_running", "ready_for_review", "commit_pending"} for batch in batches):
        return 3
    if coverage.get("percent", 0) < 100 and not coverage.get("overrideActive"):
        return 6
    return 7


def _step_status(number: int, current_step: int) -> str:
    if number < current_step:
        return "complete"
    if number == current_step:
        return "current"
    return "locked"


def _field_states(payload: Any) -> list[dict[str, Any]]:
    fields = payload.get("fields") if isinstance(payload, dict) else None
    if not isinstance(fields, dict):
        return []
    return [
        {
            "field": field_name,
            "value": field_payload.get("value"),
            "rawValue": field_payload.get("raw_value"),
            "confidence": field_payload.get("confidence"),
            "mode": field_payload.get("mode"),
            "required": bool(field_payload.get("required")),
        }
        for field_name, field_payload in fields.items()
        if isinstance(field_payload, dict)
    ]


def _json_list(value: Any) -> list[Any]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []
