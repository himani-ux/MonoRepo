from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


REQUIRED_FIELDS = (
    "certificate_type",
    "issuing_authority",
    "vessel_name",
    "imo_number",
    "issue_date",
    "expiry_date",
    "certificate_number",
    "place_of_issue",
)


@dataclass(frozen=True)
class ValidationGateResult:
    blocks: list[dict[str, Any]]
    warns: list[dict[str, Any]]
    preview: dict[str, Any]

    @property
    def can_commit(self) -> bool:
        return not self.blocks

    @property
    def requires_warning_ack(self) -> bool:
        return self.can_commit and bool(self.warns)


def validate_onboarding_batch(
    *,
    batch: dict[str, Any],
    vessel: dict[str, Any] | None,
    pdfs: list[dict[str, Any]],
) -> ValidationGateResult:
    blocks: list[dict[str, Any]] = []
    warns: list[dict[str, Any]] = []
    cert_numbers: dict[str, list[dict[str, Any]]] = {}
    catalog_ids: dict[str, list[dict[str, Any]]] = {}
    vessel_imo = _normalize((vessel or {}).get("imo_number") or (vessel or {}).get("imo"))

    for pdf in pdfs:
        fields = _fields(pdf.get("ocr_payload_json") or pdf.get("ocrPayload"))
        if not fields:
            blocks.append(_entry("ocr_payload_missing", "block", "OCR payload is required before commit.", pdf))
            continue

        validity_type = _normalize(_field_value(fields, "validity_type") or _field_value(fields, "validityType"))
        required_fields = tuple(field for field in REQUIRED_FIELDS if field != "expiry_date" or validity_type != "permanent")
        bypass_cert_number = _truthy(
            _field_value(fields, "certificate_number_bypass")
            or _field_value(fields, "cert_number_bypass")
            or _field_value(fields, "certificateNumberBypass")
        )

        for field_name in required_fields:
            if field_name == "certificate_number" and bypass_cert_number:
                continue
            if not _normalize(_field_value(fields, field_name)):
                blocks.append(
                    _entry(
                        "required_field_missing",
                        "block",
                        f"{field_name.replace('_', ' ').title()} is required.",
                        pdf,
                        field=field_name,
                    )
                )

        if bypass_cert_number:
            reason = _normalize(
                _field_value(fields, "certificate_number_bypass_reason")
                or _field_value(fields, "cert_number_bypass_reason")
                or _field_value(fields, "certificateNumberBypassReason")
            )
            if len(reason) < 10:
                blocks.append(
                    _entry(
                        "cert_number_bypass_reason_missing",
                        "block",
                        "Certificate-number bypass requires a reason of at least 10 characters.",
                        pdf,
                        field="certificate_number_bypass_reason",
                    )
                )

        imo = _normalize(_field_value(fields, "imo_number") or _field_value(fields, "imo"))
        if imo and vessel_imo and imo != vessel_imo:
            blocks.append(_entry("ocr_imo_unresolved", "block", "OCR IMO does not resolve to the onboarding vessel.", pdf, field="imo_number"))

        if validity_type in {"", "unknown", "undetermined"}:
            blocks.append(_entry("validity_type_unknown", "block", "Validity type must be resolved before commit.", pdf, field="validity_type"))

        issue_date = _parse_date(_field_value(fields, "issue_date") or _field_value(fields, "issueDate"))
        if issue_date and issue_date > date.today():
            blocks.append(_entry("issue_date_future", "block", "Issue date cannot be in the future.", pdf, field="issue_date"))

        expiry_date = _parse_date(_field_value(fields, "expiry_date") or _field_value(fields, "expiryDate"))
        if expiry_date and expiry_date < date.today():
            warns.append(_entry("expiry_date_in_past", "warn", "Expiry date is in the past.", pdf, field="expiry_date"))

        issuer_type = _normalize(
            _field_value(fields, "issuer_type")
            or _field_value(fields, "issuing_authority_type")
            or _field_value(fields, "issuingAuthorityType")
        )
        if issuer_type in {"unknown", "undetermined"}:
            warns.append(_entry("issuer_type_unknown", "warn", "Issuer type is undetermined.", pdf, field="issuer_type"))

        if _pdf_missing(pdf, fields):
            warns.append(_entry("pdf_missing", "warn", "The linked tracked item is marked PDF missing.", pdf))

        cert_number = _normalize(_field_value(fields, "certificate_number") or _field_value(fields, "certificateNumber"))
        if cert_number:
            cert_numbers.setdefault(cert_number.lower(), []).append(pdf)

        catalog_id = _normalize(
            _field_value(fields, "catalog_id")
            or _field_value(fields, "catalogId")
            or (pdf.get("tracked_item") or {}).get("catalog_id")
            or (pdf.get("trackedItem") or {}).get("catalogId")
        )
        if catalog_id:
            catalog_ids.setdefault(catalog_id.lower(), []).append(pdf)

    for cert_number, duplicate_pdfs in cert_numbers.items():
        if len(duplicate_pdfs) > 1:
            for pdf in duplicate_pdfs:
                blocks.append(
                    _entry(
                        "duplicate_cert_number_in_batch",
                        "block",
                        "Certificate number is duplicated within this batch.",
                        pdf,
                        field="certificate_number",
                        value=cert_number,
                    )
                )

    for catalog_id, duplicate_pdfs in catalog_ids.items():
        if len(duplicate_pdfs) > 1:
            for pdf in duplicate_pdfs:
                warns.append(
                    _entry(
                        "duplicate_catalog_for_vessel",
                        "warn",
                        "More than one certificate row maps to the same catalog item for this vessel.",
                        pdf,
                        field="catalog_id",
                        value=catalog_id,
                    )
                )

    active_pdf_count = len([pdf for pdf in pdfs if not _pdf_missing(pdf, _fields(pdf.get("ocr_payload_json") or pdf.get("ocrPayload")))])
    preview = {
        "batchId": str(batch.get("batch_id") or batch.get("id") or ""),
        "pdfCount": len(pdfs),
        "attachmentCount": active_pdf_count,
        "commitCount": 0 if blocks else active_pdf_count,
        "blockCount": len(blocks),
        "warnCount": len(warns),
    }
    return ValidationGateResult(blocks=blocks, warns=warns, preview=preview)


def _fields(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            return {}
    if not isinstance(payload, dict):
        return {}
    fields = payload.get("fields")
    return fields if isinstance(fields, dict) else {}


def _field_value(fields: dict[str, Any], field_name: str) -> Any:
    payload = fields.get(field_name)
    if isinstance(payload, dict):
        return payload.get("value")
    return payload


def _entry(
    code: str,
    severity: str,
    message: str,
    pdf: dict[str, Any],
    *,
    field: str | None = None,
    value: Any = None,
) -> dict[str, Any]:
    entry = {
        "code": code,
        "severity": severity,
        "message": message,
        "blobId": str(pdf.get("blob_id") or pdf.get("id") or ""),
        "filename": pdf.get("filename"),
    }
    if field:
        entry["field"] = field
    if value is not None:
        entry["value"] = value
    return entry


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _parse_date(value: Any) -> date | None:
    text = _normalize(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d %b %Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _pdf_missing(pdf: dict[str, Any], fields: dict[str, Any]) -> bool:
    tracked_item = pdf.get("tracked_item") or pdf.get("trackedItem") or {}
    return bool(
        pdf.get("pdf_missing")
        or tracked_item.get("pdf_missing")
        or tracked_item.get("pdfMissing")
        or _truthy(_field_value(fields, "pdf_missing") or _field_value(fields, "pdfMissing"))
    )
