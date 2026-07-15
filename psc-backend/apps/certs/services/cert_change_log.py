from __future__ import annotations

import json
from typing import Any

from django.db import connection

from apps.certs.services.audit_log import resolve_actor_id


TRACKED_CHANGE_COLUMNS = (
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


def record_cert_change_log(
    *,
    tracked_item_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any],
    version_after: int,
    actor,
    source_ref: str | None = None,
    source_module: str = "CERTS",
) -> None:
    rows = []
    before = before or {}
    for column in TRACKED_CHANGE_COLUMNS:
        old_value = before.get(column)
        new_value = after.get(column)
        if before and _normalize_value(old_value) == _normalize_value(new_value):
            continue
        if not before and new_value in (None, ""):
            continue
        rows.append(
            [
                tracked_item_id,
                column,
                _json_scalar(old_value),
                _json_scalar(new_value),
                version_after,
                source_module,
                source_ref,
                resolve_actor_id(actor),
            ]
        )

    if not rows:
        return

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO dbo.vims_certs_cert_change_log (
                tracked_item_id, field_name, old_value, new_value,
                version_after, source_module, source_ref, changed_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )


def _normalize_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _json_scalar(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return json.dumps(value, default=str)
