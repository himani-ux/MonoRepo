from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import traceback
from typing import Any, Callable

from django.conf import settings
from django.db import connection

from apps.certs.services.audit_log import record_audit_event, resolve_actor_id, resolve_actor_role
from apps.certs.services.excel_renderer import render_print_excel
from apps.certs.services.pdf_blob_repository import PdfBlobRepository
from apps.certs.services.pdf_blob_storage import save_generated_print_artifact
from apps.certs.services.pdf_renderer import ReportLabPdfRenderer
from apps.certs.services.system_state_hash import compute_system_state_hash
from apps.certs.services.zip_bundler import build_share_bundle_zip

PRINT_SOFT_THROTTLE_THRESHOLD_PER_HOUR = 10
PRINT_SOFT_THROTTLE_WINDOW_MINUTES = 60


class PrintGenerationFailed(RuntimeError):
    def __init__(self, artifact: dict[str, Any]) -> None:
        self.artifact = artifact
        super().__init__(str(artifact.get("failure_message") or "Print generation failed."))


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


class PrintArtifactRepository:
    def list_rows_for_scope(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        where = ["t.lifecycle_status = 'active'"]
        params: list[Any] = []
        vessel_ids = payload.get("vesselIds") or []
        sections = payload.get("sections") or []
        custom_cert_ids = payload.get("customCertIds") or []
        filters = payload.get("filters") or {}

        if custom_cert_ids:
            where.append(f"t.tracked_item_id IN ({', '.join(['%s'] * len(custom_cert_ids))})")
            params.extend(custom_cert_ids)
        if vessel_ids:
            where.append(f"t.vessel_id IN ({', '.join(['%s'] * len(vessel_ids))})")
            params.extend(vessel_ids)

        if sections:
            section_clause = " OR ".join(["s.section_code = %s", "CAST(s.section_id AS VARCHAR(16)) = %s"] * len(sections))
            where.append(f"({section_clause})")
            for section in sections:
                params.extend([section, section])

        status_filter = str(filters.get("status") or "").strip()
        if status_filter and status_filter != "all":
            where.append("t.status = %s")
            params.append(status_filter)
        cadence_filter = str(filters.get("cadence") or "").strip()
        if cadence_filter and cadence_filter != "all":
            where.append("t.validity_type = %s")
            params.append(cadence_filter)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    t.tracked_item_id, t.vessel_id, t.catalog_id, t.type, t.validity_type,
                    t.issue_date, t.expiry_date, t.last_done_date, t.next_due_date,
                    t.status, t.certificate_number, t.issuing_authority, t.pdf_attachment_id,
                    t.pdf_missing, t.approval_state, t.lifecycle_status, t.version,
                    c.canonical_code AS catalog_code,
                    c.display_name AS catalog_display_name,
                    c.short_name AS catalog_short_name,
                    c.print_order AS catalog_print_order,
                    s.section_id AS catalog_section_id,
                    s.section_code AS catalog_section_code,
                    s.display_name AS catalog_section_name,
                    vd.vesselName AS vessel_name,
                    vd.vesselCode AS vessel_code,
                    vd.imoNumber AS vessel_imo,
                    vd.flags AS vessel_flag,
                    vd.ClassificationSociety AS class_society,
                    p.blob_storage_path,
                    p.filename AS blob_filename,
                    p.content_sha256 AS blob_content_sha256
                FROM dbo.vims_certs_tracked_item t
                INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
                INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = c.section_id
                INNER JOIN dbo.VesselData vd ON vd.id = t.vessel_id
                LEFT JOIN dbo.vims_certs_pdf_blob p ON p.blob_id = t.pdf_attachment_id
                WHERE {' AND '.join(where)}
                ORDER BY vd.vesselName, c.print_order, c.display_name, t.expiry_date
                """,
                params,
            )
            return _fetch_all(cursor)

    def next_print_id(self, imo_token: str, *, now_yyyymmdd: str | None = None) -> str:
        safe_token = re.sub(r"[^A-Z0-9]", "", str(imo_token or "FLEET").upper())[:16] or "FLEET"
        date_token = now_yyyymmdd or datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"SQE-S633-{safe_token}-{date_token}-"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM dbo.vims_certs_print_artifact
                WHERE print_id LIKE %s
                """,
                [f"{prefix}%"],
            )
            sequence = int(cursor.fetchone()[0]) + 1
        return f"{prefix}{sequence:03d}"

    def insert_artifact(self, values: dict[str, Any]) -> dict[str, Any]:
        columns = (
            "print_id",
            "scope",
            "vessels_json",
            "sections_json",
            "filters_json",
            "custom_cert_ids_json",
            "user_id",
            "user_role",
            "system_state_hash",
            "watermark_applied",
            "watermark_recipient",
            "pdf_blob_id",
            "excel_blob_id",
            "bundle_zip_blob_id",
            "recipient_email",
            "page_count",
            "generation_status",
            "failure_message",
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO dbo.vims_certs_print_artifact ({', '.join(columns)})
                VALUES ({', '.join(['%s'] * len(columns))})
                """,
                [values.get(column) for column in columns],
            )
        return self.get_artifact(str(values["print_id"])) or values

    def get_artifact(self, print_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(_artifact_select_sql("WHERE print_id = %s"), [print_id])
            return _fetch_one(cursor)

    def list_artifacts(self, *, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 200))
        with connection.cursor() as cursor:
            cursor.execute(_artifact_select_sql(f"ORDER BY timestamp_utc DESC OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY"))
            return _fetch_all(cursor)

    def count_user_prints_since(self, *, user_id: str, since: datetime) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM dbo.vims_certs_print_artifact
                WHERE user_id = %s
                  AND timestamp_utc >= %s
                """,
                [user_id, since],
            )
            return int(cursor.fetchone()[0])


class PrintArtifactService:
    def __init__(
        self,
        *,
        repository: PrintArtifactRepository | None = None,
        blob_repository: PdfBlobRepository | None = None,
        renderer: ReportLabPdfRenderer | None = None,
        save_artifact: Callable[..., dict[str, Any]] = save_generated_print_artifact,
        read_blob: Callable[[str], bytes] | None = None,
    ) -> None:
        self.repository = repository or PrintArtifactRepository()
        self.blob_repository = blob_repository or PdfBlobRepository()
        self.renderer = renderer or ReportLabPdfRenderer()
        self.save_artifact = save_artifact
        self.read_blob = read_blob or read_artifact_blob

    def generate_print(self, *, payload: dict[str, Any], actor) -> dict[str, Any]:
        rows = self.repository.list_rows_for_scope(payload)
        print_id = self.repository.next_print_id(derive_print_id_scope_token(rows))
        actor_id = resolve_actor_id(actor)
        actor_role = resolve_actor_role(actor)
        state_hash = compute_system_state_hash(rows, payload)
        try:
            pdf = self.renderer.render_print_artifact(
                print_id=print_id,
                rows=rows,
                payload=payload,
                actor_id=actor_id,
                actor_role=actor_role,
                system_state_hash=state_hash,
            ).content
            excel = render_print_excel(print_id=print_id, rows=rows, payload=payload, system_state_hash=state_hash)
            pdf_blob = self._store_blob(print_id=print_id, filename=f"{print_id}.pdf", subdir="pdf", content=pdf, actor_id=actor_id)
            excel_blob = self._store_blob(print_id=print_id, filename=f"{print_id}.xlsx", subdir="excel", content=excel, actor_id=actor_id)
        except Exception as exc:
            artifact = self._record_generation_failure(
                print_id=print_id,
                payload=payload,
                actor=actor,
                actor_id=actor_id,
                actor_role=actor_role,
                state_hash=state_hash,
                source="api.certs.print",
                exc=exc,
            )
            raise PrintGenerationFailed(artifact) from exc
        values = self._artifact_values(
            print_id=print_id,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            state_hash=state_hash,
            pdf_blob_id=pdf_blob.get("blob_id"),
            excel_blob_id=excel_blob.get("blob_id"),
            bundle_zip_blob_id=None,
            page_count=_pdf_page_count(pdf),
            generation_status="success",
            failure_message="",
        )
        artifact = self.repository.insert_artifact(values)
        self._record_print_volume_signal_if_needed(actor=actor, artifact=artifact, actor_id=actor_id, actor_role=actor_role)
        return artifact

    def generate_share_bundle(self, *, payload: dict[str, Any], actor) -> dict[str, Any]:
        rows = self.repository.list_rows_for_scope(payload)
        missing_pdf = [row for row in rows if not row.get("pdf_attachment_id") or not row.get("blob_storage_path")]
        if missing_pdf:
            raise ValueError("Every share-bundle certificate must have an attached certificate PDF.")
        print_id = self.repository.next_print_id(derive_print_id_scope_token(rows))
        actor_id = resolve_actor_id(actor)
        actor_role = resolve_actor_role(actor)
        state_hash = compute_system_state_hash(rows, payload)
        try:
            manifest_pdf = self.renderer.render_share_bundle_manifest(
                print_id=print_id,
                rows=rows,
                payload=payload,
                actor_id=actor_id,
                actor_role=actor_role,
                system_state_hash=state_hash,
            ).content
            zip_bytes = build_share_bundle_zip(print_id=print_id, rows=rows, manifest_pdf=manifest_pdf, read_blob=self.read_blob)
            manifest_blob = self._store_blob(print_id=print_id, filename=f"manifest_{print_id}.pdf", subdir="manifest", content=manifest_pdf, actor_id=actor_id)
            bundle_blob = self._store_blob(
                print_id=print_id,
                filename=f"VIMS_CertBundle_{_bundle_vessel_name(rows)}_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{print_id}.zip",
                subdir="zip",
                content=zip_bytes,
                actor_id=actor_id,
            )
        except Exception as exc:
            artifact = self._record_generation_failure(
                print_id=print_id,
                payload=payload,
                actor=actor,
                actor_id=actor_id,
                actor_role=actor_role,
                state_hash=state_hash,
                source="api.certs.print.share_bundle",
                exc=exc,
            )
            raise PrintGenerationFailed(artifact) from exc
        values = self._artifact_values(
            print_id=print_id,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            state_hash=state_hash,
            pdf_blob_id=manifest_blob.get("blob_id"),
            excel_blob_id=None,
            bundle_zip_blob_id=bundle_blob.get("blob_id"),
            page_count=_pdf_page_count(manifest_pdf),
            generation_status="success",
            failure_message="",
        )
        artifact = self.repository.insert_artifact(values)
        self._record_print_volume_signal_if_needed(actor=actor, artifact=artifact, actor_id=actor_id, actor_role=actor_role)
        return artifact

    def _store_blob(self, *, print_id: str, filename: str, subdir: str, content: bytes, actor_id: str) -> dict[str, Any]:
        stored = self.save_artifact(content=content, print_id=print_id, filename=filename, subdir=subdir)
        return self.blob_repository.create_artifact_blob(
            storage_path=str(stored.get("relative_path")),
            filename=str(stored.get("filename")),
            content_sha256=str(stored.get("sha256")),
            content_size_bytes=int(stored.get("size") or 0),
            uploaded_by=actor_id,
        )

    def _artifact_values(
        self,
        *,
        print_id: str,
        payload: dict[str, Any],
        actor_id: str,
        actor_role: str,
        state_hash: str,
        pdf_blob_id: Any,
        excel_blob_id: Any,
        bundle_zip_blob_id: Any,
        page_count: int,
        generation_status: str,
        failure_message: str,
    ) -> dict[str, Any]:
        return {
            "print_id": print_id,
            "scope": payload.get("scope"),
            "vessels_json": json.dumps(payload.get("vesselIds") or []),
            "sections_json": json.dumps(payload.get("sections") or []),
            "filters_json": json.dumps(payload.get("filters") or {}, default=str),
            "custom_cert_ids_json": json.dumps(payload.get("customCertIds") or []),
            "user_id": actor_id,
            "user_role": actor_role,
            "system_state_hash": state_hash,
            "watermark_applied": payload.get("watermarkApplied") or "NONE",
            "watermark_recipient": payload.get("watermarkRecipient") or "",
            "pdf_blob_id": pdf_blob_id,
            "excel_blob_id": excel_blob_id,
            "bundle_zip_blob_id": bundle_zip_blob_id,
            "recipient_email": payload.get("recipientEmail") or "",
            "page_count": page_count,
            "generation_status": generation_status,
            "failure_message": failure_message,
        }

    def _record_print_volume_signal_if_needed(self, *, actor, artifact: dict[str, Any], actor_id: str, actor_role: str) -> None:
        now = datetime.now(timezone.utc)
        window_started_at = now - timedelta(minutes=PRINT_SOFT_THROTTLE_WINDOW_MINUTES)
        print_count = self.repository.count_user_prints_since(user_id=actor_id, since=window_started_at)
        if print_count <= PRINT_SOFT_THROTTLE_THRESHOLD_PER_HOUR:
            return

        print_id = str(artifact.get("print_id") or "")
        record_audit_event(
            actor=actor,
            action="high_volume_print_activity",
            entity_type="print_artifact",
            entity_id=print_id,
            vessel_id=_single_vessel_from_artifact(artifact),
            before=None,
            after={"printId": print_id, "userId": actor_id, "userRole": actor_role},
            reason=f"High-volume print activity by user {actor_id}.",
            metadata={
                "source": "api.certs.print",
                "printCountLastHour": print_count,
                "thresholdPerHour": PRINT_SOFT_THROTTLE_THRESHOLD_PER_HOUR,
                "windowMinutes": PRINT_SOFT_THROTTLE_WINDOW_MINUTES,
                "windowStartedAt": window_started_at.isoformat(),
            },
        )

    def _record_generation_failure(
        self,
        *,
        print_id: str,
        payload: dict[str, Any],
        actor,
        actor_id: str,
        actor_role: str,
        state_hash: str,
        source: str,
        exc: Exception,
    ) -> dict[str, Any]:
        support_ticket_reference = f"{print_id}-ERR"
        failure_message = (
            f"Generation failed. Support ticket {support_ticket_reference} was logged. "
            "Retry manually or contact support."
        )
        values = self._artifact_values(
            print_id=print_id,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            state_hash=state_hash,
            pdf_blob_id=None,
            excel_blob_id=None,
            bundle_zip_blob_id=None,
            page_count=0,
            generation_status="failed",
            failure_message=failure_message,
        )
        artifact = self.repository.insert_artifact(values)
        record_audit_event(
            actor=actor,
            action="print_generation_failed",
            entity_type="print_artifact",
            entity_id=print_id,
            vessel_id=_single_vessel_from_artifact(artifact),
            before=None,
            after={
                "printId": print_id,
                "generationStatus": "failed",
                "supportTicketReference": support_ticket_reference,
            },
            reason=failure_message,
            metadata={
                "source": source,
                "supportTicketReference": support_ticket_reference,
                "printId": print_id,
                "autoRetry": False,
                "exceptionType": exc.__class__.__name__,
                "exceptionMessage": str(exc),
                "stackTrace": traceback.format_exc(),
            },
        )
        return artifact


def read_artifact_blob(blob_storage_path: str) -> bytes:
    upload_base = Path(getattr(settings, "UPLOAD_BASE_PATH", settings.BASE_DIR / "uploads")).resolve(strict=False)
    absolute_path = (upload_base / blob_storage_path).resolve(strict=False)
    try:
        absolute_path.relative_to(upload_base)
    except ValueError as exc:
        raise ValueError("Invalid certificate blob storage path.") from exc
    return absolute_path.read_bytes()


def _artifact_select_sql(suffix: str) -> str:
    return f"""
        SELECT
            print_id, scope, vessels_json, sections_json, filters_json,
            custom_cert_ids_json, user_id, user_role, timestamp_utc, system_state_hash,
            watermark_applied, watermark_recipient, pdf_blob_id, excel_blob_id,
            bundle_zip_blob_id, recipient_email, page_count, generation_status,
            failure_message
        FROM dbo.vims_certs_print_artifact
        {suffix}
    """


def derive_print_id_scope_token(rows: list[dict[str, Any]]) -> str:
    imo_values = {str(row.get("vessel_imo") or "").strip() for row in rows if row.get("vessel_imo")}
    return next(iter(imo_values)) if len(imo_values) == 1 else "FLEET"


def _bundle_vessel_name(rows: list[dict[str, Any]]) -> str:
    names = {str(row.get("vessel_name") or row.get("vessel_imo") or "fleet").strip() for row in rows}
    value = next(iter(names)) if len(names) == 1 else "fleet"
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_") or "fleet"


def _single_vessel_from_artifact(artifact: dict[str, Any]) -> str | None:
    vessels = artifact.get("vessels_json")
    if isinstance(vessels, str):
        try:
            vessels = json.loads(vessels)
        except ValueError:
            vessels = []
    if isinstance(vessels, list) and len(vessels) == 1:
        return str(vessels[0])
    return None


def _pdf_page_count(content: bytes) -> int:
    try:
        from PyPDF2 import PdfReader

        return len(PdfReader(bytes_as_file(content)).pages)
    except Exception:
        return 1


def bytes_as_file(content: bytes):
    from io import BytesIO

    return BytesIO(content)
