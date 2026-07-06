from __future__ import annotations

import json
from typing import Any

from django.db import connection


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def ocr_confidence_map(payload: dict[str, Any]) -> dict[str, float]:
    fields = payload.get("fields") if isinstance(payload, dict) else None
    if not isinstance(fields, dict):
        return {}
    confidence_map: dict[str, float] = {}
    for field_name, field_payload in fields.items():
        if not isinstance(field_payload, dict):
            continue
        try:
            confidence_map[str(field_name)] = round(float(field_payload.get("confidence") or 0.0), 3)
        except (TypeError, ValueError):
            confidence_map[str(field_name)] = 0.0
    return confidence_map


class PdfBlobRepository:
    def get_blob(self, blob_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    blob_id, tracked_item_id, snapshot_id, blob_storage_path,
                    filename, content_sha256, content_size_bytes, uploaded_by,
                    uploaded_at, is_active, superseded_at, retention_policy,
                    scheduled_delete_at, delete_pending_since, dpa_retention_override_until,
                    ocr_payload_json, ocr_confidence_per_field, ocr_processed_at,
                    ocr_engine_version, schema_version
                FROM dbo.vims_certs_pdf_blob
                WHERE blob_id = %s
                """,
                [blob_id],
            )
            return _fetch_one(cursor)

    def create_blob_for_tracked_item(
        self,
        *,
        tracked_item_id: str,
        storage_path: str,
        filename: str,
        content_sha256: str,
        content_size_bytes: int,
        uploaded_by: str,
        retention_policy: str = "retain_18_months_then_purge",
    ) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_pdf_blob (
                    tracked_item_id, snapshot_id, blob_storage_path, filename,
                    content_sha256, content_size_bytes, uploaded_by, retention_policy
                )
                OUTPUT inserted.blob_id
                VALUES (%s, NULL, %s, %s, %s, %s, %s, %s)
                """,
                [
                    tracked_item_id,
                    storage_path,
                    filename,
                    content_sha256,
                    content_size_bytes,
                    uploaded_by,
                    retention_policy,
                ],
            )
            blob_id = str(cursor.fetchone()[0])
        return self.get_blob(blob_id) or {}

    def create_artifact_blob(
        self,
        *,
        storage_path: str,
        filename: str,
        content_sha256: str,
        content_size_bytes: int,
        uploaded_by: str,
        retention_policy: str = "retain_5_years",
    ) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_pdf_blob (
                    tracked_item_id, snapshot_id, blob_storage_path, filename,
                    content_sha256, content_size_bytes, uploaded_by, retention_policy
                )
                OUTPUT inserted.blob_id
                VALUES (NULL, NULL, %s, %s, %s, %s, %s, %s)
                """,
                [
                    storage_path,
                    filename,
                    content_sha256,
                    content_size_bytes,
                    uploaded_by,
                    retention_policy,
                ],
            )
            blob_id = str(cursor.fetchone()[0])
        return self.get_blob(blob_id) or {}

    def create_snapshot_blob(
        self,
        *,
        storage_path: str,
        filename: str,
        content_sha256: str,
        content_size_bytes: int,
        uploaded_by: str,
    ) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_pdf_blob (
                    tracked_item_id, snapshot_id, blob_storage_path, filename,
                    content_sha256, content_size_bytes, uploaded_by, retention_policy
                )
                OUTPUT inserted.blob_id
                VALUES (NULL, NULL, %s, %s, %s, %s, %s, %s)
                """,
                [
                    storage_path,
                    filename,
                    content_sha256,
                    content_size_bytes,
                    uploaded_by,
                    "retain_indefinitely",
                ],
            )
            blob_id = str(cursor.fetchone()[0])
        return self.get_blob(blob_id) or {}

    def attach_snapshot(self, blob_id: str, snapshot_id: str) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_pdf_blob
                SET snapshot_id = %s
                WHERE blob_id = %s
                """,
                [snapshot_id, blob_id],
            )
        return self.get_blob(blob_id) or {}

    def update_ocr_result(self, blob_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        confidence_map = ocr_confidence_map(payload)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_pdf_blob
                SET
                    ocr_payload_json = %s,
                    ocr_confidence_per_field = %s,
                    ocr_processed_at = SYSUTCDATETIME(),
                    ocr_engine_version = %s
                WHERE blob_id = %s
                """,
                [
                    json.dumps(payload, default=str),
                    json.dumps(confidence_map, default=str),
                    str(payload.get("engine") or "")[:32],
                    blob_id,
                ],
            )
        return self.get_blob(blob_id) or {}

    def mark_blob_superseded_for_retention(
        self,
        *,
        blob_id: str,
        section_code: str | None,
        is_class_tracked: bool,
        retain_all_versions: bool,
    ) -> None:
        policy, schedule_sql = _superseded_retention_policy(
            section_code=section_code,
            is_class_tracked=is_class_tracked,
            retain_all_versions=retain_all_versions,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE dbo.vims_certs_pdf_blob
                SET is_active = 0,
                    superseded_at = COALESCE(superseded_at, SYSUTCDATETIME()),
                    retention_policy = %s,
                    scheduled_delete_at = {schedule_sql},
                    delete_pending_since = NULL
                WHERE blob_id = %s
                """,
                [policy, blob_id],
            )


def _superseded_retention_policy(
    *,
    section_code: str | None,
    is_class_tracked: bool,
    retain_all_versions: bool,
) -> tuple[str, str]:
    if retain_all_versions:
        return "retain_all_versions", "NULL"
    normalized_section = str(section_code or "").strip().upper()
    if is_class_tracked or normalized_section in {"CLASS", "STATUTORY"}:
        return "immediate_delete_on_supersede", "SYSUTCDATETIME()"
    return "retain_18_months_then_purge", "DATEADD(month, 18, SYSUTCDATETIME())"
