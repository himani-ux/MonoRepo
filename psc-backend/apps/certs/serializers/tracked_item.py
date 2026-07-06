from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from typing import Any

from django.db import connection
from rest_framework import serializers

from apps.certs.services.tracked_item_status import compute_tracked_item_status


TRACKED_ITEM_TYPES = {
    "certificate",
    "endorsement_survey",
    "service",
    "calibration",
    "test",
    "type_approval",
    "plan_approval",
}
VALIDITY_TYPES = {"full", "conditional", "short_term", "permanent"}
RELATIONSHIP_TYPES = {"survey_of", "short_term_for", "extension_of", "dispensation_for"}
EXTENSION_AUTHORITIES = {"class", "flag", "n/a"}
SOURCES = {"manual", "class_snapshot", "migration"}
APPROVAL_STATES = {"draft", "pending_master_approval", "approved", "rejected"}
LIFECYCLE_STATUSES = {
    "active",
    "pending_disposal",
    "pending_supersession",
    "invalid_due_to_reflag",
    "onboarding_quarantine",
}
STORED_STATUSES = {
    "ok",
    "window_opening",
    "window_open",
    "window_closing",
    "overdue",
    "done",
    "postponed",
    "superseded",
    "permanent",
    "expired_at_onboarding",
    "expired",
    "pending_first_upload",
    "invalid_due_to_reflag",
    "pending_supersession",
}
READ_ONLY_DERIVED_FIELDS = {"windowOpen", "windowClose", "nextDueDate"}
WORKFLOW_CONTROLLED_FIELDS = {
    "approvalState",
    "submittedBy",
    "submittedAt",
    "approvedBy",
    "approvedAt",
    "rejectionReason",
    "rejectionCount",
    "draftExpiresAt",
}


class TrackedItemWriteSerializer(serializers.Serializer):
    vesselId = serializers.UUIDField(required=False)
    catalogId = serializers.UUIDField(required=False)
    type = serializers.ChoiceField(choices=sorted(TRACKED_ITEM_TYPES), required=False)
    validityType = serializers.ChoiceField(choices=sorted(VALIDITY_TYPES), required=False)
    formVariant = serializers.ChoiceField(choices=["A", "B", "n/a"], required=False, allow_null=True)
    cadenceMonths = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=32767)
    cadenceCustomDays = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    parentId = serializers.UUIDField(required=False, allow_null=True)
    relationshipType = serializers.ChoiceField(choices=sorted(RELATIONSHIP_TYPES), required=False, allow_null=True)
    supersedesId = serializers.UUIDField(required=False, allow_null=True)
    issueDate = serializers.DateField(required=False, allow_null=True)
    expiryDate = serializers.DateField(required=False, allow_null=True)
    anniversaryDate = serializers.DateField(required=False, allow_null=True)
    windowOpen = serializers.DateField(required=False, allow_null=True)
    windowClose = serializers.DateField(required=False, allow_null=True)
    lastDoneDate = serializers.DateField(required=False, allow_null=True)
    nextDueDate = serializers.DateField(required=False, allow_null=True)
    postponedUntil = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=sorted(STORED_STATUSES), required=False)
    certificateNumber = serializers.CharField(max_length=128, required=False, allow_blank=True, allow_null=True)
    issuingAuthority = serializers.CharField(max_length=128, required=False)
    placeOfIssue = serializers.CharField(max_length=128, required=False, allow_blank=True, allow_null=True)
    extensionAuthority = serializers.ChoiceField(choices=sorted(EXTENSION_AUTHORITIES), required=False, allow_null=True)
    extensionLetterPdfId = serializers.UUIDField(required=False, allow_null=True)
    extensionReason = serializers.CharField(max_length=512, required=False, allow_blank=True, allow_null=True)
    pdfAttachmentId = serializers.UUIDField(required=False, allow_null=True)
    pdfMissing = serializers.BooleanField(required=False)
    source = serializers.ChoiceField(choices=sorted(SOURCES), required=False)
    lastClassSyncId = serializers.UUIDField(required=False, allow_null=True)
    approvalState = serializers.ChoiceField(choices=sorted(APPROVAL_STATES), required=False)
    submittedBy = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    submittedAt = serializers.DateTimeField(required=False, allow_null=True)
    approvedBy = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    approvedAt = serializers.DateTimeField(required=False, allow_null=True)
    rejectionReason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    rejectionCount = serializers.IntegerField(required=False, min_value=0, max_value=32767)
    draftExpiresAt = serializers.DateTimeField(required=False, allow_null=True)
    lifecycleStatus = serializers.ChoiceField(choices=sorted(LIFECYCLE_STATUSES), required=False)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    create_required_fields = (
        "vesselId",
        "catalogId",
        "type",
        "validityType",
        "issuingAuthority",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        workflow_fields = sorted(field for field in WORKFLOW_CONTROLLED_FIELDS if field in attrs)
        if workflow_fields:
            raise serializers.ValidationError(
                {field: "This field is controlled by the Certs approval workflow." for field in workflow_fields}
            )

        readonly_derived = sorted(field for field in READ_ONLY_DERIVED_FIELDS if field in attrs)
        if readonly_derived:
            raise serializers.ValidationError(
                {field: "This field is computed by the Certs survey-window service." for field in readonly_derived}
            )

        if self.context.get("is_create"):
            missing = [field for field in self.create_required_fields if field not in attrs]
            if missing:
                raise serializers.ValidationError({field: "This field is required." for field in missing})

        validity_type = attrs.get("validityType")
        if validity_type == "permanent":
            attrs["expiryDate"] = None
        elif self.context.get("is_create") and "expiryDate" not in attrs:
            raise serializers.ValidationError({"expiryDate": "Expiry date is required unless validityType is permanent."})

        issue_date = attrs.get("issueDate")
        expiry_date = attrs.get("expiryDate")
        if issue_date and issue_date > date.today():
            raise serializers.ValidationError({"issueDate": "Issue date cannot be in the future."})
        if issue_date and expiry_date and expiry_date <= issue_date:
            raise serializers.ValidationError({"expiryDate": "Expiry date must be after issue date."})

        relationship_type = attrs.get("relationshipType")
        if relationship_type and not attrs.get("parentId") and relationship_type != "survey_of":
            raise serializers.ValidationError({"parentId": "parentId is required for linked TrackedItem relationships."})

        return attrs


def serialize_tracked_item(row: dict[str, Any]) -> dict[str, Any]:
    submitted_by = row.get("submitted_by")
    approved_by = row.get("approved_by")
    created_by = row.get("created_by")
    updated_by = row.get("updated_by")
    return {
        "id": str(row.get("tracked_item_id")),
        "vesselId": str(row["vessel_id"]) if row.get("vessel_id") else None,
        "vesselName": row.get("vessel_name"),
        "vesselCode": row.get("vessel_code"),
        "vesselImo": row.get("vessel_imo_number"),
        "catalogId": str(row["catalog_id"]) if row.get("catalog_id") else None,
        "catalogCode": row.get("catalog_code"),
        "catalogDisplayName": row.get("catalog_display_name"),
        "catalogShortName": row.get("catalog_short_name"),
        "submissionScope": row.get("catalog_submission_scope"),
        "type": row.get("type"),
        "validityType": row.get("validity_type"),
        "formVariant": row.get("form_variant"),
        "cadenceMonths": row.get("cadence_months"),
        "cadenceCustomDays": row.get("cadence_custom_days"),
        "parentId": str(row["parent_id"]) if row.get("parent_id") else None,
        "relationshipType": row.get("relationship_type"),
        "supersedesId": str(row["supersedes_id"]) if row.get("supersedes_id") else None,
        "issueDate": row.get("issue_date"),
        "expiryDate": row.get("expiry_date"),
        "anniversaryDate": row.get("anniversary_date"),
        "windowOpen": row.get("window_open"),
        "windowClose": row.get("window_close"),
        "lastDoneDate": row.get("last_done_date"),
        "nextDueDate": row.get("next_due_date"),
        "postponedUntil": row.get("postponed_until"),
        "status": compute_tracked_item_status(row),
        "certificateNumber": row.get("certificate_number"),
        "issuingAuthority": row.get("issuing_authority"),
        "placeOfIssue": row.get("place_of_issue"),
        "extensionAuthority": row.get("extension_authority"),
        "extensionLetterPdfId": str(row["extension_letter_pdf_id"]) if row.get("extension_letter_pdf_id") else None,
        "extensionReason": row.get("extension_reason"),
        "pdfAttachmentId": str(row["pdf_attachment_id"]) if row.get("pdf_attachment_id") else None,
        "pdfMissing": bool(row.get("pdf_missing")),
        "source": row.get("source"),
        "lastClassSyncId": str(row["last_class_sync_id"]) if row.get("last_class_sync_id") else None,
        "approvalState": row.get("approval_state"),
        "submittedBy": submitted_by,
        "submittedByDisplay": resolve_principal_display_name(submitted_by),
        "submittedAt": row.get("submitted_at"),
        "approvedBy": approved_by,
        "approvedByDisplay": resolve_principal_display_name(approved_by),
        "approvedAt": row.get("approved_at"),
        "rejectionReason": row.get("rejection_reason"),
        "rejectionCount": row.get("rejection_count"),
        "draftExpiresAt": row.get("draft_expires_at"),
        "lifecycleStatus": row.get("lifecycle_status"),
        "rowVersion": _row_version(row.get("row_version")),
        "version": row.get("version"),
        "createdAt": row.get("created_at"),
        "createdBy": created_by,
        "createdByDisplay": resolve_principal_display_name(created_by),
        "updatedAt": row.get("updated_at"),
        "updatedBy": updated_by,
        "updatedByDisplay": resolve_principal_display_name(updated_by),
    }


def serialize_pdf_blob(row: dict[str, Any]) -> dict[str, Any]:
    uploaded_by = row.get("uploaded_by")
    return {
        "id": str(row.get("blob_id")),
        "trackedItemId": str(row["tracked_item_id"]) if row.get("tracked_item_id") else None,
        "snapshotId": str(row["snapshot_id"]) if row.get("snapshot_id") else None,
        "filename": row.get("filename"),
        "sizeBytes": row.get("content_size_bytes"),
        "uploadedBy": uploaded_by,
        "uploadedByDisplay": resolve_principal_display_name(uploaded_by),
        "uploadedAt": row.get("uploaded_at"),
        "isActive": bool(row.get("is_active")),
        "supersededAt": row.get("superseded_at"),
        "retentionPolicy": row.get("retention_policy"),
        "scheduledDeleteAt": row.get("scheduled_delete_at"),
        "deletePendingSince": row.get("delete_pending_since"),
        "dpaRetentionOverrideUntil": row.get("dpa_retention_override_until"),
        "ocrPayload": _json_object(row.get("ocr_payload_json")),
        "ocrConfidencePerField": _json_object(row.get("ocr_confidence_per_field")),
        "ocrProcessedAt": row.get("ocr_processed_at"),
        "ocrEngineVersion": row.get("ocr_engine_version"),
    }


def serialize_approval_event(row: dict[str, Any]) -> dict[str, Any]:
    actor_user_id = row.get("actor_user_id")
    return {
        "id": str(row.get("event_id")),
        "fromState": row.get("from_state"),
        "toState": row.get("to_state"),
        "actorUserId": actor_user_id,
        "actorDisplayName": resolve_principal_display_name(actor_user_id),
        "actorRole": row.get("actor_role"),
        "reason": row.get("reason"),
        "timestampUtc": row.get("timestamp_utc"),
    }


def serialize_tracked_item_audit_event(row: dict[str, Any]) -> dict[str, Any]:
    actor_user_id = row.get("actor_user_id")
    return {
        "id": str(row.get("audit_id")),
        "timestampUtc": row.get("timestamp_utc"),
        "vesselId": str(row["vessel_id"]) if row.get("vessel_id") else None,
        "actorUserId": actor_user_id,
        "actorDisplayName": resolve_principal_display_name(actor_user_id),
        "actorRole": row.get("actor_role"),
        "action": row.get("action"),
        "entityType": row.get("entity_type"),
        "entityId": str(row["entity_id"]) if row.get("entity_id") else None,
        "before": _json_object(row.get("before_json")),
        "after": _json_object(row.get("after_json")),
        "reason": row.get("reason"),
        "eventMetadata": _json_object(row.get("event_metadata")),
        "retentionTier": row.get("retention_tier"),
        "archivedAt": row.get("archived_at"),
        "schemaVersion": row.get("schema_version"),
    }


def serialize_cert_change(row: dict[str, Any]) -> dict[str, Any]:
    changed_by = row.get("changed_by")
    return {
        "id": str(row.get("change_id")),
        "fieldName": row.get("field_name"),
        "oldValue": _json_scalar(row.get("old_value")),
        "newValue": _json_scalar(row.get("new_value")),
        "versionAfter": row.get("version_after"),
        "sourceModule": row.get("source_module"),
        "sourceRef": row.get("source_ref"),
        "changedBy": changed_by,
        "changedByDisplay": resolve_principal_display_name(changed_by),
        "changedAt": row.get("changed_at"),
    }


@lru_cache(maxsize=1024)
def resolve_principal_display_name(identifier: Any) -> str | None:
    raw = str(identifier or "").strip()
    if not raw:
        return None
    return _resolve_office_display_name(raw) or _resolve_crew_display_name(raw) or None


def _resolve_office_display_name(identifier: str) -> str | None:
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 employee_id, display_name, employee_name, username, employee_role
                FROM dbo.users
                WHERE employee_id = %s
                   OR username = %s
                   OR display_name = %s
                   OR employee_name = %s
                ORDER BY CASE WHEN employee_id = %s THEN 0 ELSE 1 END
                """,
                [identifier, identifier, identifier, identifier, identifier],
            )
            row = cursor.fetchone()
    except Exception:
        return None
    if not row:
        return None
    employee_id, display_name, employee_name, username, employee_role = row
    name = str(display_name or employee_name or username or employee_id or "").strip()
    role = str(employee_role or "").strip()
    return f"{role} - {name}".strip(" -") if role else name or None


def _resolve_crew_display_name(identifier: str) -> str | None:
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    h.CrewID,
                    h.first_name,
                    h.surname,
                    fcl.CrewName,
                    r.rank_name
                FROM dbo.HRM501 h
                LEFT JOIN dbo.Final_crew_list fcl
                    ON fcl.CrewID = h.CrewID
                   AND ISNULL(fcl.is_delete, 0) = 0
                LEFT JOIN dbo.master_applied_rank r
                    ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
                   AND ISNULL(r.is_deleted, 0) = 0
                WHERE (CAST(h.id AS VARCHAR(64)) = %s OR h.CrewID = %s)
                  AND ISNULL(h.is_deleted, 0) = 0
                ORDER BY ISNULL(h.is_active, 1) DESC
                """,
                [identifier, identifier],
            )
            row = cursor.fetchone()
    except Exception:
        return None
    if not row:
        return None
    crew_id, first_name, surname, crew_name, rank_name = row
    name = f"{first_name or ''} {surname or ''}".strip() or str(crew_name or "").strip() or str(crew_id or "").strip()
    rank = str(rank_name or "").strip()
    return f"{rank} - {name}".strip(" -") if rank else name or None


def _row_version(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, bytes):
        return value.hex()
    return str(value)


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


def _json_scalar(value: Any) -> Any:
    if value in (None, ""):
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value
