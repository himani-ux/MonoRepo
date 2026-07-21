from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.db import connection

from apps.certs.services.pdf_blob_repository import PdfBlobRepository
from apps.certs.services.parsers import ClassSnapshotParseError, parse_class_snapshot_pdf
from apps.certs.services.reconciliation import ReconciliationRepository


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    rows = _fetch_all(cursor)
    return rows[0] if rows else None


class ClassSnapshotRepository:
    def __init__(
        self,
        *,
        pdf_blobs: PdfBlobRepository | None = None,
        reconciliation: ReconciliationRepository | None = None,
    ) -> None:
        self.pdf_blobs = pdf_blobs or PdfBlobRepository()
        self.reconciliation = reconciliation or ReconciliationRepository()

    def list_snapshots(
        self,
        *,
        vessel_id: str | None = None,
        class_society: str | None = None,
        parse_status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        where = ["s.superseded_user_error = 0"]
        params: list[Any] = []
        if vessel_id:
            where.append("s.vessel_id = %s")
            params.append(vessel_id)
        if class_society:
            where.append("s.class_society = %s")
            params.append(class_society.upper())
        if parse_status:
            where.append("s.parse_status = %s")
            params.append(parse_status)
        where_sql = f"WHERE {' AND '.join(where)}"
        safe_page = max(int(page or 1), 1)
        safe_page_size = max(1, min(int(page_size or 25), 100))
        offset = (safe_page - 1) * safe_page_size
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM dbo.vims_certs_class_status_snapshot s {where_sql}", params)
            count = int(cursor.fetchone()[0] or 0)
            cursor.execute(
                _snapshot_select_sql(where_sql)
                + f" ORDER BY s.printed_on_date DESC, s.uploaded_at DESC OFFSET {offset} ROWS FETCH NEXT {safe_page_size} ROWS ONLY",
                params,
            )
            return {"count": count, "results": _fetch_all(cursor)}

    def get_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(_snapshot_select_sql("WHERE s.snapshot_id = %s"), [snapshot_id])
            return _fetch_one(cursor)

    def create_snapshot(
        self,
        *,
        vessel_id: str,
        class_society: str,
        pdf_blob_id: str,
        printed_on_date,
        uploaded_by: str,
        upload_sha256: str,
        parser_version: str = "pending-parser-v1",
    ) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_class_status_snapshot (
                    vessel_id, class_society, pdf_blob_id, printed_on_date, uploaded_by,
                    parser_version, parse_status, upload_sha256
                )
                OUTPUT inserted.snapshot_id
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    vessel_id,
                    class_society.upper(),
                    pdf_blob_id,
                    printed_on_date,
                    uploaded_by,
                    parser_version,
                    "pending",
                    upload_sha256,
                ],
            )
            snapshot_id = str(cursor.fetchone()[0])
        self.pdf_blobs.attach_snapshot(pdf_blob_id, snapshot_id)
        return self.get_snapshot(snapshot_id) or {}

    def reparse_snapshot(self, snapshot_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            return None, None
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_class_status_snapshot
                SET parse_status = %s,
                    parse_started_at = SYSUTCDATETIME(),
                    parse_completed_at = NULL,
                    parser_timeout = 0,
                    retry_count = 0
                WHERE snapshot_id = %s
                """,
                ["pending", snapshot_id],
            )
        try:
            parsed = self._parse_snapshot_pdf(snapshot)
        except ClassSnapshotParseError as exc:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE dbo.vims_certs_class_status_snapshot
                    SET parse_status = %s,
                        parse_completed_at = SYSUTCDATETIME(),
                        parsed_payload_json = %s,
                        parsed_payload_schema_version = %s
                    WHERE snapshot_id = %s
                    """,
                    [
                        "failed",
                        json.dumps(_failed_parse_payload(str(exc), snapshot), default=str),
                        1,
                        snapshot_id,
                    ],
                )
            return self.get_snapshot(snapshot_id), None
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_class_status_snapshot
                SET parse_status = %s,
                    parse_completed_at = SYSUTCDATETIME(),
                    parser_version = %s,
                    parsed_payload_json = %s,
                    parsed_payload_schema_version = %s
                WHERE snapshot_id = %s
                """,
                [
                    parsed.parse_status,
                    parsed.parser_version,
                    json.dumps(parsed.payload, default=str),
                    int(parsed.payload.get("schema_version") or 1),
                    snapshot_id,
                ],
            )
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None or parsed.parse_status == "failed":
            return snapshot, None
        _, run = self.reconciliation.reconcile_snapshot(snapshot)
        return self.get_snapshot(snapshot_id), run

    def _parse_snapshot_pdf(self, snapshot: dict[str, Any]):
        blob = self.pdf_blobs.get_blob(str(snapshot.get("pdf_blob_id") or ""))
        if not blob:
            raise ClassSnapshotParseError("Class snapshot PDF blob was not found.")
        storage_path = str(blob.get("blob_storage_path") or "")
        upload_base = Path(getattr(settings, "UPLOAD_BASE_PATH", settings.BASE_DIR / "uploads")).resolve(strict=False)
        pdf_path = (upload_base / storage_path).resolve(strict=False)
        try:
            pdf_path.relative_to(upload_base)
        except ValueError as exc:
            raise SuspiciousFileOperation("Invalid class snapshot PDF storage path.") from exc
        return parse_class_snapshot_pdf(pdf_path, str(snapshot.get("class_society") or ""))


def _snapshot_select_sql(where_sql: str) -> str:
    return f"""
        SELECT
            s.snapshot_id, s.vessel_id, v.vesselName AS vessel_name,
            v.imoNumber AS imo_number, s.class_society, s.pdf_blob_id,
            p.filename, p.content_size_bytes, s.printed_on_date, s.uploaded_by,
            s.uploaded_at, s.parser_version, s.parse_status, s.parse_started_at,
            s.parse_completed_at, s.parser_timeout, s.retry_count,
            s.parsed_payload_json, s.parsed_payload_schema_version,
            s.reconciliation_run_id, s.upload_sha256, s.superseded_user_error
        FROM dbo.vims_certs_class_status_snapshot s
        LEFT JOIN dbo.VesselData v ON v.id = s.vessel_id
        LEFT JOIN dbo.vims_certs_pdf_blob p ON p.blob_id = s.pdf_blob_id
        {where_sql}
    """


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


def _failed_parse_payload(message: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "parser_version": snapshot.get("parser_version") or "pending-parser-v1",
        "class_society": snapshot.get("class_society"),
        "source": "pdfplumber_text",
        "vessel": {},
        "rows": [],
        "conditions_of_class": [],
        "unmapped_rows": [{"error": message or "Class status PDF could not be parsed."}],
        "text_extraction": {"engine": "pdfplumber", "page_count": None, "char_count": None},
    }
