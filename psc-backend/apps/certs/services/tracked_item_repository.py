from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django.db import connection

from apps.certs.services.survey_window import computed_window_payload


TRACKED_ITEM_COLUMNS = (
    "vessel_id",
    "catalog_id",
    "type",
    "validity_type",
    "form_variant",
    "cadence_months",
    "cadence_custom_days",
    "parent_id",
    "relationship_type",
    "supersedes_id",
    "issue_date",
    "expiry_date",
    "anniversary_date",
    "window_open",
    "window_close",
    "last_done_date",
    "next_due_date",
    "postponed_until",
    "status",
    "certificate_number",
    "issuing_authority",
    "place_of_issue",
    "extension_authority",
    "extension_letter_pdf_id",
    "extension_reason",
    "pdf_attachment_id",
    "pdf_missing",
    "source",
    "last_class_sync_id",
    "approval_state",
    "submitted_by",
    "submitted_at",
    "approved_by",
    "approved_at",
    "rejection_reason",
    "rejection_count",
    "draft_expires_at",
    "lifecycle_status",
)
READ_ONLY_DERIVED_COLUMNS = {"window_open", "window_close", "next_due_date"}
WINDOW_INPUT_COLUMNS = {
    "anniversary_date",
    "cadence_months",
    "cadence_custom_days",
    "validity_type",
    "type",
    "relationship_type",
}

CAMEL_TO_COLUMN = {
    "vesselId": "vessel_id",
    "catalogId": "catalog_id",
    "type": "type",
    "validityType": "validity_type",
    "formVariant": "form_variant",
    "cadenceMonths": "cadence_months",
    "cadenceCustomDays": "cadence_custom_days",
    "parentId": "parent_id",
    "relationshipType": "relationship_type",
    "supersedesId": "supersedes_id",
    "issueDate": "issue_date",
    "expiryDate": "expiry_date",
    "anniversaryDate": "anniversary_date",
    "windowOpen": "window_open",
    "windowClose": "window_close",
    "lastDoneDate": "last_done_date",
    "nextDueDate": "next_due_date",
    "postponedUntil": "postponed_until",
    "status": "status",
    "certificateNumber": "certificate_number",
    "issuingAuthority": "issuing_authority",
    "placeOfIssue": "place_of_issue",
    "extensionAuthority": "extension_authority",
    "extensionLetterPdfId": "extension_letter_pdf_id",
    "extensionReason": "extension_reason",
    "pdfAttachmentId": "pdf_attachment_id",
    "pdfMissing": "pdf_missing",
    "source": "source",
    "lastClassSyncId": "last_class_sync_id",
    "approvalState": "approval_state",
    "submittedBy": "submitted_by",
    "submittedAt": "submitted_at",
    "approvedBy": "approved_by",
    "approvedAt": "approved_at",
    "rejectionReason": "rejection_reason",
    "rejectionCount": "rejection_count",
    "draftExpiresAt": "draft_expires_at",
    "lifecycleStatus": "lifecycle_status",
}


@dataclass(frozen=True)
class TrackedItemPage:
    count: int
    results: list[dict[str, Any]]


class ApprovalTransition(StrEnum):
    SUBMIT_FOR_MASTER = "submit_for_master"
    MASTER_DIRECT_APPROVE = "master_direct_approve"
    APPROVE = "approve"
    REJECT = "reject"
    RESUBMIT_TO_DRAFT = "resubmit_to_draft"


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def _db_value(column: str, value: Any) -> Any:
    if value == "":
        return None
    if column.endswith("_id") and value is not None:
        return str(value)
    if isinstance(value, bool):
        return 1 if value else 0
    return value


def _item_select_sql(where_sql: str = "") -> str:
    return f"""
        SELECT
            t.tracked_item_id, t.vessel_id, t.catalog_id,
            vd.vesselName AS vessel_name,
            vd.vesselCode AS vessel_code,
            vd.imoNumber AS vessel_imo_number,
            c.canonical_code AS catalog_code,
            c.display_name AS catalog_display_name,
            c.short_name AS catalog_short_name,
            c.section_id AS catalog_section_id,
            s.section_code AS catalog_section_code,
            s.display_name AS catalog_section_name,
            c.print_order AS catalog_print_order,
            c.mandatory_for_all_vessels AS catalog_mandatory_for_all_vessels,
            c.is_class_tracked AS catalog_is_class_tracked,
            c.retain_all_versions AS catalog_retain_all_versions,
            c.submission_scope AS catalog_submission_scope,
            t.type, t.validity_type, t.form_variant, t.cadence_months, t.cadence_custom_days,
            t.parent_id, t.relationship_type, t.supersedes_id,
            t.issue_date, t.expiry_date, t.anniversary_date,
            t.window_open, t.window_close, t.last_done_date, t.next_due_date, t.postponed_until,
            t.status, t.certificate_number, t.issuing_authority, t.place_of_issue,
            t.extension_authority, t.extension_letter_pdf_id, t.extension_reason,
            t.pdf_attachment_id, t.pdf_missing, t.source, t.last_class_sync_id,
            t.approval_state, t.submitted_by, t.submitted_at, t.approved_by, t.approved_at,
            t.rejection_reason, t.rejection_count, t.draft_expires_at, t.lifecycle_status,
            t.row_version, t.version, t.created_at, t.created_by, t.updated_at, t.updated_by
        FROM dbo.vims_certs_tracked_item t
        INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
        INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = c.section_id
        LEFT JOIN dbo.VesselData vd ON vd.id = t.vessel_id
        {where_sql}
    """


class TrackedItemRepository:
    def list_items(
        self,
        *,
        vessel_id: str | None = None,
        catalog_id: str | None = None,
        status_value: str | None = None,
        approval_state: str | None = None,
    ) -> TrackedItemPage:
        where: list[str] = []
        params: list[Any] = []
        if vessel_id:
            where.append("t.vessel_id = %s")
            params.append(vessel_id)
        if catalog_id:
            where.append("t.catalog_id = %s")
            params.append(catalog_id)
        if status_value:
            where.append("t.status = %s")
            params.append(status_value)
        if approval_state:
            where.append("t.approval_state = %s")
            params.append(approval_state)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM dbo.vims_certs_tracked_item t
                {where_sql}
                """,
                params,
            )
            count = int(cursor.fetchone()[0])
            cursor.execute(
                _item_select_sql(where_sql) + " ORDER BY c.print_order, c.display_name, t.expiry_date",
                params,
            )
            return TrackedItemPage(count=count, results=_fetch_all(cursor))

    def get_item(self, tracked_item_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(_item_select_sql("WHERE t.tracked_item_id = %s"), [tracked_item_id])
            return _fetch_one(cursor)

    def get_catalog_submission_scope(self, catalog_id: str) -> str | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT submission_scope
                FROM dbo.vims_certs_catalog_row
                WHERE catalog_id = %s
                """,
                [catalog_id],
            )
            row = cursor.fetchone()
            return str(row[0]) if row and row[0] else None

    def list_pdf_versions(self, tracked_item_id: str) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    blob_id, tracked_item_id, snapshot_id, filename, content_size_bytes,
                    uploaded_by, uploaded_at, is_active, superseded_at, retention_policy,
                    scheduled_delete_at, delete_pending_since, dpa_retention_override_until,
                    ocr_payload_json, ocr_confidence_per_field, ocr_processed_at,
                    ocr_engine_version
                FROM dbo.vims_certs_pdf_blob
                WHERE tracked_item_id = %s
                ORDER BY is_active DESC, uploaded_at DESC, superseded_at DESC
                """,
                [tracked_item_id],
            )
            return _fetch_all(cursor)

    def list_approval_events(self, tracked_item_id: str) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    event_id, tracked_item_id, from_state, to_state, actor_user_id,
                    actor_role, reason, timestamp_utc
                FROM dbo.vims_certs_approval_event
                WHERE tracked_item_id = %s
                ORDER BY timestamp_utc DESC
                """,
                [tracked_item_id],
            )
            return _fetch_all(cursor)

    def list_audit_events(self, tracked_item_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 200))
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT TOP {safe_limit}
                    audit_id, timestamp_utc, vessel_id, actor_user_id, actor_role,
                    action, entity_type, entity_id, before_json, after_json, reason,
                    event_metadata, retention_tier, archived_at, schema_version
                FROM dbo.vims_certs_audit_log
                WHERE entity_type = %s AND entity_id = %s
                ORDER BY timestamp_utc DESC
                """,
                ["tracked_item", tracked_item_id],
            )
            return _fetch_all(cursor)

    def list_change_history(self, tracked_item_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 500))
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT TOP {safe_limit}
                    change_id, tracked_item_id, field_name, old_value, new_value,
                    version_after, source_module, source_ref, changed_by, changed_at
                FROM dbo.vims_certs_cert_change_log
                WHERE tracked_item_id = %s
                ORDER BY changed_at DESC, version_after DESC
                """,
                [tracked_item_id],
            )
            return _fetch_all(cursor)

    def create_item(self, values: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        data = self._db_payload(values)
        data.update(computed_window_payload(data))
        data.setdefault("status", "ok")
        data.setdefault("source", "manual")
        data.setdefault("approval_state", "approved")
        data.setdefault("lifecycle_status", "active")
        data["created_by"] = actor_id
        data["updated_by"] = actor_id
        columns = tuple(data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(columns)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO dbo.vims_certs_tracked_item ({column_sql})
                OUTPUT inserted.tracked_item_id
                VALUES ({placeholders})
                """,
                [data[column] for column in columns],
            )
            tracked_item_id = str(cursor.fetchone()[0])
        return self.get_item(tracked_item_id) or {}

    def update_item(
        self,
        tracked_item_id: str,
        values: dict[str, Any],
        *,
        actor_id: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        before = self.get_item(tracked_item_id)
        if before is None:
            return None, None
        data = self._db_payload(values)
        if not data:
            return before, before
        if WINDOW_INPUT_COLUMNS.intersection(data):
            computed_source = {**before, **data}
            data.update(computed_window_payload(computed_source))
        assignments = [f"{column} = %s" for column in data]
        assignments.extend(["version = version + 1", "updated_at = SYSUTCDATETIME()", "updated_by = %s"])
        params = [*data.values(), actor_id, tracked_item_id]
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE dbo.vims_certs_tracked_item SET {', '.join(assignments)} WHERE tracked_item_id = %s",
                params,
            )
        return before, self.get_item(tracked_item_id)

    def transition_item(
        self,
        tracked_item_id: str,
        *,
        transition: str,
        actor_id: str,
        reason: str | None = None,
        expected_version: int | None = None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
        before = self.get_item(tracked_item_id)
        if before is None:
            return None, None, False
        if expected_version is not None and int(before.get("version") or 0) != expected_version:
            return before, before, False

        assignments, params = self._transition_assignments(
            transition=ApprovalTransition(transition),
            actor_id=actor_id,
            reason=reason,
        )
        assignments.extend(["version = version + 1", "updated_at = SYSUTCDATETIME()", "updated_by = %s"])
        params.extend([actor_id, tracked_item_id])
        where_sql = "tracked_item_id = %s"
        if expected_version is not None:
            where_sql += " AND version = %s"
            params.append(expected_version)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE dbo.vims_certs_tracked_item
                SET {', '.join(assignments)}
                WHERE {where_sql}
                """,
                params,
            )
            if getattr(cursor, "rowcount", 1) == 0:
                return before, self.get_item(tracked_item_id), False
        return before, self.get_item(tracked_item_id), True

    def _db_payload(self, values: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for api_key, value in values.items():
            column = CAMEL_TO_COLUMN.get(api_key)
            if column not in TRACKED_ITEM_COLUMNS:
                continue
            if column in READ_ONLY_DERIVED_COLUMNS:
                continue
            payload[column] = _db_value(column, value)
        return payload

    def _transition_assignments(
        self,
        *,
        transition: ApprovalTransition,
        actor_id: str,
        reason: str | None,
    ) -> tuple[list[str], list[Any]]:
        if transition == ApprovalTransition.SUBMIT_FOR_MASTER:
            return (
                [
                    "approval_state = %s",
                    "submitted_by = %s",
                    "submitted_at = SYSUTCDATETIME()",
                    "approved_by = NULL",
                    "approved_at = NULL",
                    "rejection_reason = NULL",
                    "draft_expires_at = NULL",
                ],
                ["pending_master_approval", actor_id],
            )
        if transition == ApprovalTransition.MASTER_DIRECT_APPROVE:
            return (
                [
                    "approval_state = %s",
                    "submitted_by = %s",
                    "submitted_at = SYSUTCDATETIME()",
                    "approved_by = %s",
                    "approved_at = SYSUTCDATETIME()",
                    "rejection_reason = NULL",
                    "draft_expires_at = NULL",
                ],
                ["approved", actor_id, actor_id],
            )
        if transition == ApprovalTransition.APPROVE:
            return (
                [
                    "approval_state = %s",
                    "approved_by = %s",
                    "approved_at = SYSUTCDATETIME()",
                    "rejection_reason = NULL",
                    "draft_expires_at = NULL",
                ],
                ["approved", actor_id],
            )
        if transition == ApprovalTransition.REJECT:
            return (
                [
                    "approval_state = %s",
                    "approved_by = NULL",
                    "approved_at = NULL",
                    "rejection_reason = %s",
                    "rejection_count = COALESCE(rejection_count, 0) + 1",
                    "draft_expires_at = NULL",
                ],
                ["rejected", reason],
            )
        if transition == ApprovalTransition.RESUBMIT_TO_DRAFT:
            return (
                [
                    "approval_state = %s",
                    "submitted_by = %s",
                    "submitted_at = NULL",
                    "approved_by = NULL",
                    "approved_at = NULL",
                    "rejection_reason = NULL",
                    "draft_expires_at = DATEADD(day, 7, SYSUTCDATETIME())",
                ],
                ["draft", actor_id],
            )
        raise ValueError(f"Unsupported approval transition: {transition}")
