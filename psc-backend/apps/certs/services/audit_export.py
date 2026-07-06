from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO, StringIO
import json
from typing import Any, Callable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.certs.services.audit_log import resolve_actor_id, resolve_actor_role
from apps.certs.services.audit_log_repository import AuditLogRepository
from apps.certs.services.pdf_blob_repository import PdfBlobRepository
from apps.certs.services.pdf_blob_storage import save_generated_print_artifact
from apps.certs.services.print_artifacts import PrintArtifactRepository


AUDIT_EXPORT_SCOPE = "audit_log_export"
AUDIT_EXPORT_WATERMARK = "INTERNAL"
AUDIT_EXPORT_WATERMARK_RECIPIENT = "DPA audit export"


class AuditLogExportService:
    def __init__(
        self,
        *,
        audit_repository: AuditLogRepository | None = None,
        artifact_repository: PrintArtifactRepository | None = None,
        blob_repository: PdfBlobRepository | None = None,
        save_artifact: Callable[..., dict[str, Any]] = save_generated_print_artifact,
    ) -> None:
        self.audit_repository = audit_repository or AuditLogRepository()
        self.artifact_repository = artifact_repository or PrintArtifactRepository()
        self.blob_repository = blob_repository or PdfBlobRepository()
        self.save_artifact = save_artifact

    def export(self, *, filters: dict[str, Any], actor) -> dict[str, Any]:
        normalized_filters = normalize_export_filters(filters)
        rows = self.audit_repository.export_events(filters=normalized_filters, vessel_scope=None)
        print_id = self.artifact_repository.next_print_id("FLEET")
        actor_id = resolve_actor_id(actor)
        actor_role = resolve_actor_role(actor)
        state_hash = audit_export_state_hash(rows=rows, filters=normalized_filters)
        pdf = render_audit_export_pdf(
            print_id=print_id,
            rows=rows,
            filters=normalized_filters,
            actor_id=actor_id,
            actor_role=actor_role,
            system_state_hash=state_hash,
        )
        csv_bytes = render_audit_export_csv(rows)
        pdf_blob = self._store_blob(print_id=print_id, filename=f"{print_id}-audit-log.pdf", subdir="audit-pdf", content=pdf, actor_id=actor_id)
        csv_blob = self._store_blob(print_id=print_id, filename=f"{print_id}-audit-log.csv", subdir="audit-csv", content=csv_bytes, actor_id=actor_id)
        values = {
            "print_id": print_id,
            "scope": AUDIT_EXPORT_SCOPE,
            "vessels_json": json.dumps(_export_vessel_ids(rows, normalized_filters)),
            "sections_json": "[]",
            "filters_json": json.dumps({"auditLogFilters": normalized_filters}, default=str),
            "custom_cert_ids_json": "[]",
            "user_id": actor_id,
            "user_role": actor_role,
            "system_state_hash": state_hash,
            "watermark_applied": AUDIT_EXPORT_WATERMARK,
            "watermark_recipient": AUDIT_EXPORT_WATERMARK_RECIPIENT,
            "pdf_blob_id": pdf_blob.get("blob_id"),
            "excel_blob_id": csv_blob.get("blob_id"),
            "bundle_zip_blob_id": None,
            "recipient_email": "",
            "page_count": _pdf_page_count(pdf),
            "generation_status": "success",
            "failure_message": "",
        }
        return self.artifact_repository.insert_artifact(values)

    def _store_blob(self, *, print_id: str, filename: str, subdir: str, content: bytes, actor_id: str) -> dict[str, Any]:
        stored = self.save_artifact(content=content, print_id=print_id, filename=filename, subdir=subdir)
        return self.blob_repository.create_artifact_blob(
            storage_path=str(stored.get("relative_path")),
            filename=str(stored.get("filename")),
            content_sha256=str(stored.get("sha256")),
            content_size_bytes=int(stored.get("size") or 0),
            uploaded_by=actor_id,
        )


def normalize_export_filters(filters: dict[str, Any] | None) -> dict[str, str]:
    allowed = ("vesselId", "actorUserId", "action", "entityType", "retentionTier", "dateFrom", "dateTo")
    source = filters or {}
    return {key: str(source.get(key) or "").strip() for key in allowed if str(source.get(key) or "").strip()}


def audit_export_state_hash(*, rows: list[dict[str, Any]], filters: dict[str, str]) -> str:
    payload = {
        "filters": filters,
        "rows": [
            {
                "audit_id": str(row.get("audit_id") or ""),
                "timestamp_utc": str(row.get("timestamp_utc") or ""),
                "action": str(row.get("action") or ""),
                "entity_type": str(row.get("entity_type") or ""),
                "entity_id": str(row.get("entity_id") or ""),
                "retention_tier": str(row.get("retention_tier") or ""),
            }
            for row in rows
        ],
    }
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:8].upper()


def render_audit_export_csv(rows: list[dict[str, Any]]) -> bytes:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "audit_id",
            "timestamp_utc",
            "vessel_id",
            "actor_user_id",
            "actor_role",
            "action",
            "entity_type",
            "entity_id",
            "reason",
            "retention_tier",
            "archived_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.get("audit_id"),
                row.get("timestamp_utc"),
                row.get("vessel_id"),
                row.get("actor_user_id"),
                row.get("actor_role"),
                row.get("action"),
                row.get("entity_type"),
                row.get("entity_id"),
                row.get("reason"),
                row.get("retention_tier"),
                row.get("archived_at"),
            ]
        )
    return output.getvalue().encode("utf-8")


def render_audit_export_pdf(
    *,
    print_id: str,
    rows: list[dict[str, Any]],
    filters: dict[str, str],
    actor_id: str,
    actor_role: str,
    system_state_hash: str,
) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=32, bottomMargin=28)
    story: list[Any] = [
        Paragraph("SQE S 633 - Audit Log Export", styles["Title"]),
        Paragraph(f"Print ID: {print_id}", styles["Normal"]),
        Paragraph(f"Generated by: {actor_id} ({actor_role})", styles["Normal"]),
        Paragraph(f"Generated UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}", styles["Normal"]),
        Paragraph(f"Watermark: {AUDIT_EXPORT_WATERMARK}", styles["Normal"]),
        Paragraph(f"System-state hash: {system_state_hash}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(f"Filters: {json.dumps(filters, sort_keys=True) if filters else 'None'}", styles["Normal"]),
        Spacer(1, 12),
    ]
    table_rows = [["UTC", "Vessel", "Actor", "Action", "Entity", "Tier", "Reason"]]
    for row in rows[:250]:
        table_rows.append(
            [
                str(row.get("timestamp_utc") or ""),
                str(row.get("vessel_id") or "Fleet")[:18],
                f"{row.get('actor_role') or ''} {row.get('actor_user_id') or ''}"[:24],
                str(row.get("action") or "")[:24],
                f"{row.get('entity_type') or ''} {row.get('entity_id') or ''}"[:28],
                str(row.get("retention_tier") or ""),
                str(row.get("reason") or "")[:42],
            ]
        )
    if len(rows) > 250:
        table_rows.append(["", "", "", "", "", "", f"CSV contains all {len(rows)} exported rows."])
    table = Table(table_rows, repeatRows=1, colWidths=[92, 74, 104, 96, 122, 44, 190])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d4d4d4")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    story.append(PageBreak())
    story.append(Paragraph(f"SQE S 633 | {print_id} | {actor_id} | {actor_role} | {system_state_hash}", styles["Normal"]))
    document.build(story, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
    return buffer.getvalue()


def _draw_watermark(canvas, document) -> None:
    del document
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#a3a3a3"), alpha=0.3)
    canvas.setFont("Helvetica-Bold", 72)
    canvas.translate(420, 290)
    canvas.rotate(32)
    canvas.drawCentredString(0, 0, AUDIT_EXPORT_WATERMARK)
    canvas.restoreState()


def _export_vessel_ids(rows: list[dict[str, Any]], filters: dict[str, str]) -> list[str]:
    if filters.get("vesselId"):
        return [filters["vesselId"]]
    values = sorted({str(row.get("vessel_id")) for row in rows if row.get("vessel_id")})
    return values


def _pdf_page_count(content: bytes) -> int:
    try:
        from PyPDF2 import PdfReader

        return len(PdfReader(BytesIO(content)).pages)
    except Exception:
        return 1
