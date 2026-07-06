from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PdfIdempotencyResult:
    blocks: list[dict[str, Any]]
    skipped_duplicates: list[dict[str, Any]]
    superseded_pdfs: list[dict[str, Any]]

    @property
    def can_commit(self) -> bool:
        return not self.blocks


def analyze_pdf_idempotency(
    *,
    pdfs: list[dict[str, Any]],
    existing_by_certificate_number: dict[str, list[dict[str, Any]]],
    supersede_decisions: list[dict[str, Any]] | None = None,
) -> PdfIdempotencyResult:
    decisions = _decision_set(supersede_decisions or [])
    blocks: list[dict[str, Any]] = []
    skipped_duplicates: list[dict[str, Any]] = []
    superseded_pdfs: list[dict[str, Any]] = []

    for pdf in pdfs:
        blob_id = str(pdf.get("blob_id") or "")
        cert_number = _certificate_number(pdf)
        content_sha256 = str(pdf.get("content_sha256") or "")
        if not blob_id or not cert_number or not content_sha256:
            continue
        active_matches = [
            row
            for row in existing_by_certificate_number.get(_normalize(cert_number), [])
            if str(row.get("blob_id") or "") != blob_id
        ]
        if not active_matches:
            continue
        same_hash = next(
            (row for row in active_matches if str(row.get("content_sha256") or "").lower() == content_sha256.lower()),
            None,
        )
        if same_hash:
            skipped_duplicates.append(
                {
                    "blobId": blob_id,
                    "existingBlobId": str(same_hash.get("blob_id") or ""),
                    "trackedItemId": str(pdf.get("tracked_item_id") or same_hash.get("tracked_item_id") or ""),
                    "certificateNumber": cert_number,
                    "sha256": content_sha256,
                    "filename": pdf.get("filename"),
                }
            )
            continue
        predecessor = active_matches[0]
        existing_blob_id = str(predecessor.get("blob_id") or "")
        decision_key = (blob_id, existing_blob_id)
        if decision_key not in decisions:
            blocks.append(
                {
                    "code": "supersede_confirmation_required",
                    "severity": "block",
                    "message": "A certificate with this number already exists. Confirm whether this PDF supersedes it.",
                    "blobId": blob_id,
                    "filename": pdf.get("filename"),
                    "field": "certificate_number",
                    "value": existing_blob_id,
                    "certificateNumber": cert_number,
                }
            )
            continue
        superseded_pdfs.append(
            {
                "blobId": blob_id,
                "existingBlobId": existing_blob_id,
                "trackedItemId": str(pdf.get("tracked_item_id") or predecessor.get("tracked_item_id") or ""),
                "certificateNumber": cert_number,
                "oldSha256": str(predecessor.get("content_sha256") or ""),
                "newSha256": content_sha256,
                "filename": pdf.get("filename"),
            }
        )

    return PdfIdempotencyResult(
        blocks=blocks,
        skipped_duplicates=skipped_duplicates,
        superseded_pdfs=superseded_pdfs,
    )


def _decision_set(decisions: list[dict[str, Any]]) -> set[tuple[str, str]]:
    confirmed: set[tuple[str, str]] = set()
    for decision in decisions:
        if not isinstance(decision, dict) or not bool(decision.get("confirm")):
            continue
        blob_id = str(decision.get("blobId") or decision.get("newBlobId") or "")
        existing_blob_id = str(decision.get("existingBlobId") or "")
        if blob_id and existing_blob_id:
            confirmed.add((blob_id, existing_blob_id))
    return confirmed


def _certificate_number(pdf: dict[str, Any]) -> str:
    fields = _payload_fields(pdf.get("ocr_payload_json"))
    value = _payload_value(fields, "certificate_number")
    if value in (None, ""):
        value = _payload_value(fields, "cert_number")
    return str(value or "").strip()


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
        return field.get("value") if field.get("value") not in (None, "") else field.get("raw_value")
    return field


def _normalize(value: str) -> str:
    return " ".join(str(value or "").strip().upper().split())
