from __future__ import annotations

import json
from csv import DictWriter
from datetime import datetime, timezone
from io import StringIO
from typing import Any

from django.db import connection

from apps.certs.services.audit_log import resolve_actor_id
from apps.certs.services.coverage import compute_mandatory_coverage
from apps.certs.services.idempotency import analyze_pdf_idempotency
from apps.certs.services.pdf_blob_repository import PdfBlobRepository
from apps.certs.services.pdf_blob_storage import save_onboarding_batch_csv
from apps.certs.services.tracked_item_repository import TrackedItemRepository
from apps.certs.services.validation_gates import validate_onboarding_batch
from apps.certs.services.vessel_dashboard import VesselDashboardRepository


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    rows = _fetch_all(cursor)
    return rows[0] if rows else None


class OnboardingRepository:
    def __init__(
        self,
        *,
        tracked_items: TrackedItemRepository | None = None,
        pdf_blobs: PdfBlobRepository | None = None,
        vessel_dashboard: VesselDashboardRepository | None = None,
    ) -> None:
        self.tracked_items = tracked_items or TrackedItemRepository()
        self.pdf_blobs = pdf_blobs or PdfBlobRepository()
        self.vessels = vessel_dashboard or VesselDashboardRepository(tracked_items=self.tracked_items)

    def resolve_vessel(self, vessel_identifier: str) -> dict[str, Any] | None:
        return self.vessels.resolve_vessel(vessel_identifier)

    def list_onboarding_sessions(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CAST(vc.vessel_id AS VARCHAR(64)) AS vessel_id,
                    vc.anniversary_date, vc.ship_type, vc.marine_supt_user_id,
                    vc.technical_manager_user_id, vc.lifecycle_status,
                    vc.mandatory_coverage_override_reason,
                    vc.mandatory_coverage_override_at, vc.mandatory_coverage_override_by,
                    vc.created_at, vc.updated_at, vc.updated_by,
                    vd.vesselCode AS vessel_code,
                    vd.vesselName AS vessel_name,
                    vd.imoNumber AS imo_number,
                    vd.flags AS flag,
                    vd.ClassificationSociety AS class_society
                FROM dbo.vims_certs_vessel_config vc
                INNER JOIN dbo.VesselData vd ON vd.id = vc.vessel_id
                WHERE vc.lifecycle_status = N'onboarding_in_progress'
                  AND ISNULL(vd.is_deleted, 0) = 0
                ORDER BY vc.updated_at DESC
                """
            )
            rows = _fetch_all(cursor)

        sessions: list[dict[str, Any]] = []
        for row in rows:
            vessel_id = str(row["vessel_id"])
            batches = self.list_batches(vessel_id)
            coverage = self.mandatory_coverage(vessel_id=vessel_id, config=row)
            sessions.append(
                {
                    "vessel": row,
                    "config": row,
                    "batchCount": len(batches),
                    "currentStep": self.current_step(row, batches, coverage),
                    "mandatoryCoveragePercent": coverage["percent"],
                    "pendingFmSignoff": coverage["percent"] >= 100 or bool(coverage["overrideActive"]),
                    "lastActivity": row.get("updated_at"),
                    "startedAt": row.get("created_at"),
                    "startedBy": row.get("updated_by"),
                }
            )
        return sessions

    def get_wizard_state(self, vessel_identifier: str) -> dict[str, Any] | None:
        vessel = self.resolve_vessel(vessel_identifier)
        if vessel is None:
            return None
        vessel_id = str(vessel["vessel_id"])
        config = self.get_vessel_config(vessel_id)
        batches = self.list_batches(vessel_id)
        items = self.tracked_items.list_items(vessel_id=vessel_id).results
        return {
            "vessel": vessel,
            "config": config,
            "batches": batches,
            "items": items,
            "coverage": self.mandatory_coverage(vessel_id=vessel_id, config=config),
        }

    def get_vessel_config(self, vessel_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    CAST(vessel_id AS VARCHAR(64)) AS vessel_id,
                    anniversary_date, ship_type, marine_supt_user_id,
                    technical_manager_user_id, lifecycle_status,
                    mandatory_coverage_override_reason,
                    mandatory_coverage_override_at,
                    mandatory_coverage_override_by,
                    updated_at, updated_by
                FROM dbo.vims_certs_vessel_config
                WHERE vessel_id = %s
                """,
                [vessel_id],
            )
            return _fetch_one(cursor)

    def save_profile(
        self,
        *,
        vessel_id: str,
        values: dict[str, Any],
        actor,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        before = self.get_vessel_config(vessel_id)
        actor_id = resolve_actor_id(actor)
        params = [
            values["anniversaryDate"],
            values["shipType"],
            values.get("marineSuptUserId") or None,
            values.get("technicalManagerUserId") or None,
            actor_id,
        ]
        with connection.cursor() as cursor:
            if before:
                cursor.execute(
                    """
                    UPDATE dbo.vims_certs_vessel_config
                    SET anniversary_date = %s,
                        ship_type = %s,
                        marine_supt_user_id = %s,
                        technical_manager_user_id = %s,
                        lifecycle_status = N'onboarding_in_progress',
                        updated_at = SYSUTCDATETIME(),
                        updated_by = %s
                    WHERE vessel_id = %s
                    """,
                    [*params, vessel_id],
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO dbo.vims_certs_vessel_config (
                        vessel_id, anniversary_date, ship_type, marine_supt_user_id,
                        technical_manager_user_id, lifecycle_status, updated_by
                    )
                    VALUES (%s, %s, %s, %s, %s, N'onboarding_in_progress', %s)
                    """,
                    [
                        vessel_id,
                        values["anniversaryDate"],
                        values["shipType"],
                        values.get("marineSuptUserId") or None,
                        values.get("technicalManagerUserId") or None,
                        actor_id,
                    ],
                )
        return before, self.get_vessel_config(vessel_id) or {}

    def start_onboarding(
        self,
        *,
        vessel_identifier: str,
        ship_type: str | None,
        actor,
    ) -> dict[str, Any] | None:
        vessel = self.resolve_vessel(vessel_identifier)
        if vessel is None:
            return None
        vessel_id = str(vessel["vessel_id"])
        existing = self.get_vessel_config(vessel_id)
        if existing:
            return existing
        actor_id = resolve_actor_id(actor)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_vessel_config (
                    vessel_id, ship_type, lifecycle_status, updated_by
                )
                VALUES (%s, %s, N'onboarding_in_progress', %s)
                """,
                [vessel_id, ship_type or "all", actor_id],
            )
        return self.get_vessel_config(vessel_id)

    def list_batches(self, vessel_id: str) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CAST(batch_id AS VARCHAR(64)) AS batch_id,
                    CAST(vessel_id AS VARCHAR(64)) AS vessel_id,
                    CAST(onboarding_session_id AS VARCHAR(64)) AS onboarding_session_id,
                    pdf_blob_ids_json, pdf_count, status, created_at, created_by,
                    ocr_completed_at, review_started_at, committed_at, committed_by,
                    cancelled_at, cancelled_by, validation_blocks_json,
                    validation_warns_json,
                    CAST(report_csv_blob_id AS VARCHAR(64)) AS report_csv_blob_id
                FROM dbo.vims_certs_batch_ingest
                WHERE vessel_id = %s
                ORDER BY created_at DESC
                """,
                [vessel_id],
            )
            return _fetch_all(cursor)

    def create_batch(
        self,
        *,
        vessel_id: str,
        pdf_blob_ids: list[str],
        onboarding_session_id: str | None,
        actor,
    ) -> dict[str, Any]:
        actor_id = resolve_actor_id(actor)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_batch_ingest (
                    vessel_id, onboarding_session_id, pdf_blob_ids_json, pdf_count,
                    status, created_by, ocr_completed_at
                )
                OUTPUT inserted.batch_id
                VALUES (%s, %s, %s, %s, N'ready_for_review', %s, SYSUTCDATETIME())
                """,
                [
                    vessel_id,
                    onboarding_session_id,
                    json.dumps(pdf_blob_ids),
                    len(pdf_blob_ids),
                    actor_id,
                ],
            )
            batch_id = str(cursor.fetchone()[0])
        batch = self.get_batch(batch_id)
        return batch or {}

    def get_batch(self, batch_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    CAST(batch_id AS VARCHAR(64)) AS batch_id,
                    CAST(vessel_id AS VARCHAR(64)) AS vessel_id,
                    CAST(onboarding_session_id AS VARCHAR(64)) AS onboarding_session_id,
                    pdf_blob_ids_json, pdf_count, status, created_at, created_by,
                    ocr_completed_at, review_started_at, committed_at, committed_by,
                    cancelled_at, cancelled_by, validation_blocks_json,
                    validation_warns_json,
                    CAST(report_csv_blob_id AS VARCHAR(64)) AS report_csv_blob_id
                FROM dbo.vims_certs_batch_ingest
                WHERE batch_id = %s
                """,
                [batch_id],
            )
            return _fetch_one(cursor)

    def get_batch_gap_fill(self, batch_id: str) -> dict[str, Any] | None:
        batch = self.get_batch(batch_id)
        if batch is None:
            return None
        vessel = self.resolve_vessel(str(batch["vessel_id"]))
        pdfs = self.list_pdf_blobs(_json_list(batch.get("pdf_blob_ids_json")))
        items_by_blob_id: dict[str, dict[str, Any]] = {}
        for blob in pdfs:
            tracked_item_id = blob.get("tracked_item_id")
            if tracked_item_id:
                item = self.tracked_items.get_item(str(tracked_item_id))
                if item:
                    items_by_blob_id[str(blob["blob_id"])] = item
        return {
            "batch": batch,
            "vessel": vessel,
            "pdfs": pdfs,
            "itemsByBlobId": items_by_blob_id,
        }

    def evaluate_batch_validation(self, batch_id: str) -> dict[str, Any] | None:
        state = self.get_batch_gap_fill(batch_id)
        if state is None:
            return None
        items_by_blob_id = state.get("itemsByBlobId") or {}
        pdfs = []
        for pdf in state.get("pdfs") or []:
            pdf_copy = dict(pdf)
            tracked_item = items_by_blob_id.get(str(pdf_copy.get("blob_id")))
            if tracked_item:
                pdf_copy["tracked_item"] = tracked_item
            pdfs.append(pdf_copy)
        result = validate_onboarding_batch(
            batch=state.get("batch") or {},
            vessel=state.get("vessel") or {},
            pdfs=pdfs,
        )
        batch = self.persist_batch_validation(batch_id, blocks=result.blocks, warns=result.warns)
        return {
            "batch": batch,
            "blocks": result.blocks,
            "warns": result.warns,
            "canCommit": result.can_commit,
            "requiresWarningAck": result.requires_warning_ack,
            "preview": result.preview,
        }

    def evaluate_batch_idempotency(
        self,
        batch_id: str,
        *,
        supersede_decisions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        state = self.get_batch_gap_fill(batch_id)
        if state is None:
            return None
        vessel_id = str((state.get("batch") or {}).get("vessel_id") or "")
        pdfs = list(state.get("pdfs") or [])
        existing_by_certificate_number: dict[str, list[dict[str, Any]]] = {}
        for pdf in pdfs:
            cert_number = _certificate_number(pdf)
            if not cert_number:
                continue
            key = _normalize_cert_number(cert_number)
            if key in existing_by_certificate_number:
                continue
            existing_by_certificate_number[key] = self.list_active_pdfs_for_certificate_number(
                vessel_id=vessel_id,
                certificate_number=cert_number,
            )
        result = analyze_pdf_idempotency(
            pdfs=pdfs,
            existing_by_certificate_number=existing_by_certificate_number,
            supersede_decisions=supersede_decisions or [],
        )
        return {
            "blocks": result.blocks,
            "skippedDuplicates": result.skipped_duplicates,
            "supersededPdfs": result.superseded_pdfs,
        }

    def list_active_pdfs_for_certificate_number(self, *, vessel_id: str, certificate_number: str) -> list[dict[str, Any]]:
        normalized = _normalize_cert_number(certificate_number)
        if not vessel_id or not normalized:
            return []
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CAST(p.blob_id AS VARCHAR(64)) AS blob_id,
                    CAST(p.tracked_item_id AS VARCHAR(64)) AS tracked_item_id,
                    p.content_sha256, p.filename, p.uploaded_at
                FROM dbo.vims_certs_pdf_blob p
                INNER JOIN dbo.vims_certs_tracked_item t
                    ON t.tracked_item_id = p.tracked_item_id
                WHERE t.vessel_id = %s
                  AND p.is_active = 1
                  AND UPPER(LTRIM(RTRIM(t.certificate_number))) = %s
                ORDER BY p.uploaded_at DESC
                """,
                [vessel_id, normalized],
            )
            return _fetch_all(cursor)

    def apply_batch_idempotency(self, idempotency_result: dict[str, Any], *, actor) -> dict[str, Any]:
        actor_id = resolve_actor_id(actor)
        skipped = list(idempotency_result.get("skippedDuplicates") or [])
        superseded = list(idempotency_result.get("supersededPdfs") or [])
        with connection.cursor() as cursor:
            for entry in skipped:
                self.pdf_blobs.mark_blob_superseded_for_retention(
                    blob_id=str(entry.get("blobId") or ""),
                    section_code="STATUTORY",
                    is_class_tracked=True,
                    retain_all_versions=False,
                )
            for entry in superseded:
                tracked_item_id = str(entry.get("trackedItemId") or "")
                retention_context = self._tracked_item_retention_context(cursor, tracked_item_id)
                self.pdf_blobs.mark_blob_superseded_for_retention(
                    blob_id=str(entry.get("existingBlobId") or ""),
                    section_code=retention_context.get("section_code"),
                    is_class_tracked=bool(retention_context.get("is_class_tracked")),
                    retain_all_versions=bool(retention_context.get("retain_all_versions")),
                )
                cursor.execute(
                    """
                    UPDATE dbo.vims_certs_pdf_blob
                    SET is_active = 1,
                        superseded_at = NULL
                    WHERE blob_id = %s
                    """,
                    [entry.get("blobId")],
                )
                if tracked_item_id:
                    cursor.execute(
                        """
                        UPDATE dbo.vims_certs_tracked_item
                        SET pdf_attachment_id = %s,
                            pdf_missing = 0,
                            status = CASE WHEN status = N'pending_first_upload' THEN N'ok' ELSE status END,
                            version = version + 1,
                            updated_at = SYSUTCDATETIME(),
                            updated_by = %s
                        WHERE tracked_item_id = %s
                        """,
                        [entry.get("blobId"), actor_id, tracked_item_id],
                    )
        return idempotency_result

    def _tracked_item_retention_context(self, cursor, tracked_item_id: str) -> dict[str, Any]:
        if not tracked_item_id:
            return {}
        cursor.execute(
            """
            SELECT
                s.section_code,
                c.is_class_tracked,
                c.retain_all_versions
            FROM dbo.vims_certs_tracked_item t
            INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
            INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = c.section_id
            WHERE t.tracked_item_id = %s
            """,
            [tracked_item_id],
        )
        row = cursor.fetchone()
        if not row:
            return {}
        return {
            "section_code": row[0],
            "is_class_tracked": bool(row[1]),
            "retain_all_versions": bool(row[2]),
        }

    def persist_batch_validation(
        self,
        batch_id: str,
        *,
        blocks: list[dict[str, Any]],
        warns: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_batch_ingest
                SET validation_blocks_json = %s,
                    validation_warns_json = %s,
                    review_started_at = COALESCE(review_started_at, SYSUTCDATETIME()),
                    status = N'commit_pending'
                WHERE batch_id = %s
                """,
                [json.dumps(blocks), json.dumps(warns), batch_id],
            )
        return self.get_batch(batch_id) or {}

    def mark_batch_committed(self, batch_id: str, *, actor) -> dict[str, Any]:
        actor_id = resolve_actor_id(actor)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_batch_ingest
                SET status = N'committed',
                    committed_at = SYSUTCDATETIME(),
                    committed_by = %s
                WHERE batch_id = %s
                """,
                [actor_id, batch_id],
            )
        return self.get_batch(batch_id) or {}

    def create_batch_report_csv(self, batch_id: str, *, actor) -> str | None:
        state = self.get_batch_gap_fill(batch_id)
        if state is None:
            return None
        actor_id = resolve_actor_id(actor)
        batch = state.get("batch") or {}
        vessel = state.get("vessel") or {}
        vessel_imo = str(vessel.get("imo_number") or vessel.get("imo") or "unknown")
        generated_at = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
        filename = f"batch_ingest_{vessel_imo}_{generated_at}.csv"
        stored = save_onboarding_batch_csv(
            content=self._build_batch_report_csv(state),
            vessel_id=str(batch.get("vessel_id") or "unknown-vessel"),
            batch_id=batch_id,
            filename=filename,
        )
        blob = self.pdf_blobs.create_artifact_blob(
            storage_path=str(stored["relative_path"]),
            filename=str(stored["filename"]),
            content_sha256=str(stored["sha256"]),
            content_size_bytes=int(stored["size"]),
            uploaded_by=actor_id,
        )
        report_blob_id = str(blob.get("blob_id") or "")
        if not report_blob_id:
            return None
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_batch_ingest
                SET report_csv_blob_id = %s
                WHERE batch_id = %s
                """,
                [report_blob_id, batch_id],
            )
        return report_blob_id

    def _build_batch_report_csv(self, state: dict[str, Any]) -> str:
        output = StringIO()
        writer = DictWriter(
            output,
            fieldnames=[
                "batch_id",
                "vessel_id",
                "imo_number",
                "blob_id",
                "filename",
                "tracked_item_id",
                "certificate_number",
                "certificate_type",
                "issuing_authority",
                "issue_date",
                "expiry_date",
                "validation_block_count",
                "validation_warn_count",
            ],
        )
        writer.writeheader()
        batch = state.get("batch") or {}
        vessel = state.get("vessel") or {}
        blocks = _json_list(batch.get("validation_blocks_json"))
        warns = _json_list(batch.get("validation_warns_json"))
        for pdf in state.get("pdfs") or []:
            fields = _payload_fields(pdf.get("ocr_payload_json"))
            writer.writerow(
                {
                    "batch_id": batch.get("batch_id"),
                    "vessel_id": batch.get("vessel_id"),
                    "imo_number": vessel.get("imo_number") or vessel.get("imo"),
                    "blob_id": pdf.get("blob_id"),
                    "filename": pdf.get("filename"),
                    "tracked_item_id": pdf.get("tracked_item_id"),
                    "certificate_number": _payload_value(fields, "certificate_number"),
                    "certificate_type": _payload_value(fields, "certificate_type"),
                    "issuing_authority": _payload_value(fields, "issuing_authority"),
                    "issue_date": _payload_value(fields, "issue_date"),
                    "expiry_date": _payload_value(fields, "expiry_date"),
                    "validation_block_count": len(blocks),
                    "validation_warn_count": len(warns),
                }
            )
        return output.getvalue()

    def list_pdf_blobs(self, blob_ids: list[str]) -> list[dict[str, Any]]:
        if not blob_ids:
            return []
        placeholders = ", ".join(["%s"] * len(blob_ids))
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    CAST(blob_id AS VARCHAR(64)) AS blob_id,
                    CAST(tracked_item_id AS VARCHAR(64)) AS tracked_item_id,
                    CAST(snapshot_id AS VARCHAR(64)) AS snapshot_id,
                    filename, content_sha256, content_size_bytes, uploaded_by, uploaded_at,
                    is_active, superseded_at, retention_policy, scheduled_delete_at,
                    delete_pending_since, dpa_retention_override_until,
                    ocr_payload_json, ocr_confidence_per_field, ocr_processed_at,
                    ocr_engine_version
                FROM dbo.vims_certs_pdf_blob
                WHERE blob_id IN ({placeholders})
                ORDER BY uploaded_at DESC
                """,
                blob_ids,
            )
            return _fetch_all(cursor)

    def update_coverage_override(
        self,
        *,
        vessel_id: str,
        reason: str,
        actor,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        before = self.get_vessel_config(vessel_id)
        actor_id = resolve_actor_id(actor)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_vessel_config
                SET mandatory_coverage_override_reason = %s,
                    mandatory_coverage_override_at = SYSUTCDATETIME(),
                    mandatory_coverage_override_by = %s,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                """,
                [reason, actor_id, actor_id, vessel_id],
            )
        return before, self.get_vessel_config(vessel_id) or {}

    def mark_active(self, *, vessel_id: str, actor) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        before = self.get_vessel_config(vessel_id)
        actor_id = resolve_actor_id(actor)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_vessel_config
                SET lifecycle_status = N'active',
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                """,
                [actor_id, vessel_id],
            )
        return before, self.get_vessel_config(vessel_id) or {}

    def rollback_onboarding(self, *, vessel_id: str, actor) -> tuple[dict[str, Any] | None, dict[str, Any], dict[str, Any]]:
        before = self.get_vessel_config(vessel_id)
        actor_id = resolve_actor_id(actor)
        batches = self.list_batches(vessel_id)
        batch_ids = [str(batch.get("batch_id")) for batch in batches if batch.get("batch_id")]
        pdf_blob_ids = sorted(
            {
                blob_id
                for batch in batches
                for blob_id in _json_list(batch.get("pdf_blob_ids_json"))
                if blob_id
            }
        )
        cancelled_batch_count = len(batch_ids)
        superseded_pdf_count = len(pdf_blob_ids)
        superseded_tracked_item_count = 0
        with connection.cursor() as cursor:
            if batch_ids:
                batch_placeholders = ", ".join(["%s"] * len(batch_ids))
                cursor.execute(
                    f"""
                    UPDATE dbo.vims_certs_batch_ingest
                    SET status = N'cancelled',
                        cancelled_at = COALESCE(cancelled_at, SYSUTCDATETIME()),
                        cancelled_by = COALESCE(cancelled_by, %s)
                    WHERE batch_id IN ({batch_placeholders})
                      AND status <> N'cancelled'
                    """,
                    [actor_id, *batch_ids],
                )
            if pdf_blob_ids:
                pdf_placeholders = ", ".join(["%s"] * len(pdf_blob_ids))
                cursor.execute(
                    f"""
                    UPDATE dbo.vims_certs_pdf_blob
                    SET is_active = 0,
                        superseded_at = COALESCE(superseded_at, SYSUTCDATETIME())
                    WHERE blob_id IN ({pdf_placeholders})
                    """,
                    pdf_blob_ids,
                )
            cursor.execute(
                """
                UPDATE dbo.vims_certs_tracked_item
                SET status = N'superseded',
                    pdf_missing = 1,
                    pdf_attachment_id = NULL,
                    lifecycle_status = N'onboarding_quarantine',
                    version = version + 1,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                  AND status <> N'superseded'
                """,
                [actor_id, vessel_id],
            )
            superseded_tracked_item_count = int(cursor.rowcount or 0)
            cursor.execute(
                """
                UPDATE dbo.vims_certs_vessel_config
                SET anniversary_date = NULL,
                    ship_type = N'all',
                    marine_supt_user_id = NULL,
                    technical_manager_user_id = NULL,
                    lifecycle_status = N'onboarding_in_progress',
                    mandatory_coverage_override_reason = NULL,
                    mandatory_coverage_override_at = NULL,
                    mandatory_coverage_override_by = NULL,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE vessel_id = %s
                """,
                [actor_id, vessel_id],
            )
        summary = {
            "cancelledBatchCount": cancelled_batch_count,
            "supersededPdfCount": superseded_pdf_count,
            "supersededTrackedItemCount": superseded_tracked_item_count,
            "resetToStep": 1,
        }
        return before, self.get_vessel_config(vessel_id) or {}, summary

    def mandatory_coverage(self, *, vessel_id: str, config: dict[str, Any] | None) -> dict[str, Any]:
        return compute_mandatory_coverage(
            vessel_id=vessel_id,
            ship_type=(config or {}).get("ship_type"),
            config=config,
        )

    def current_step(self, config: dict[str, Any], batches: list[dict[str, Any]], coverage: dict[str, Any]) -> int:
        if not config.get("anniversary_date"):
            return 2
        if not batches or any(batch.get("status") in {"queued", "ocr_running", "ready_for_review", "commit_pending"} for batch in batches):
            return 3
        if coverage.get("percent", 0) < 100 and not coverage.get("overrideActive"):
            return 6
        return 7


def _json_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _payload_fields(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            return {}
    if not isinstance(payload, dict):
        return {}
    fields = payload.get("fields")
    return fields if isinstance(fields, dict) else {}


def _payload_value(fields: dict[str, Any], key: str) -> Any:
    field = fields.get(key)
    if isinstance(field, dict):
        return field.get("value")
    return field


def _certificate_number(pdf: dict[str, Any]) -> str:
    fields = _payload_fields(pdf.get("ocr_payload_json"))
    value = _payload_value(fields, "certificate_number")
    if value in (None, ""):
        value = _payload_value(fields, "cert_number")
    return str(value or "").strip()


def _normalize_cert_number(value: str) -> str:
    return " ".join(str(value or "").strip().upper().split())
