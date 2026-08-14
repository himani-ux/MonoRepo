"""QR/hash validation for uploaded Audit signed scans."""

from __future__ import annotations

from dataclasses import dataclass
import os
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import AuditAttachment, AuditPdfGeneration


MATCHED = "MATCHED"
MISMATCH_FINDING = "MISMATCH_FINDING"
MISMATCH_VESSEL = "MISMATCH_VESSEL"
MISMATCH_VERSION = "MISMATCH_VERSION"
UNREADABLE = "UNREADABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"

QUEUE_STATUSES = frozenset({MISMATCH_FINDING, MISMATCH_VESSEL, MISMATCH_VERSION, UNREADABLE})
EXTERNAL_ATTACHMENT_CATEGORIES = frozenset({"EXTERNAL_AUDIT_REPORT", "EXTERNAL_CLOSE_OUT_LETTER"})

DPA_ACCEPTED_PREFIX = "DPA_ACCEPTED"
DPA_REJECTED_PREFIX = "DPA_REJECTED_RESCAN"


@dataclass(frozen=True)
class AuditScanValidationResult:
    attachment: AuditAttachment
    status: str
    message: str


def validate_uploaded_scan(
    attachment: AuditAttachment,
    *,
    decoded_qr_payload: str | dict[str, Any] | None = None,
) -> AuditScanValidationResult:
    """Validate one uploaded scan against the recorded PDF generation payload."""

    if attachment.category in EXTERNAL_ATTACHMENT_CATEGORIES:
        return _persist_validation(
            attachment,
            status=NOT_APPLICABLE,
            linked_pdf_generation_id=None,
            message="External-audit attachments are not VIMS-generated.",
        )

    payload = _parse_payload(decoded_qr_payload)
    if payload is None:
        payload = _parse_payload(_decode_qr_payload_from_attachment(attachment))
    if payload is None:
        return _persist_validation(
            attachment,
            status=UNREADABLE,
            linked_pdf_generation_id=None,
            message="QR payload is unreadable or missing.",
        )

    status, generation, message = _compare_payload(attachment, payload)
    return _persist_validation(
        attachment,
        status=status,
        linked_pdf_generation_id=generation.id if generation else None,
        message=message,
    )


def scan_validation_queue_queryset():
    """Return unresolved mismatch/unreadable attachments for the DPA queue."""

    return (
        AuditAttachment.objects.filter(pdf_hash_validation_status__in=QUEUE_STATUSES)
        .exclude(validator_message__startswith=DPA_ACCEPTED_PREFIX)
        .exclude(validator_message__startswith=DPA_REJECTED_PREFIX)
        .order_by("validated_at", "uploaded_at", "id")
    )


def accept_scan_with_reason(
    attachment: AuditAttachment,
    *,
    reason: str,
    user: object,
) -> AuditAttachment:
    actor = _user_identifier(user)
    attachment.validator_message = f"{DPA_ACCEPTED_PREFIX} by {actor}: {reason.strip()}"
    attachment.validated_at = timezone.now()
    attachment.save(update_fields=["validator_message", "validated_at"])
    return attachment


def reject_scan_for_rescan(
    attachment: AuditAttachment,
    *,
    reason: str | None,
    user: object,
) -> AuditAttachment:
    actor = _user_identifier(user)
    cleaned_reason = (reason or "").strip()
    message = f"{DPA_REJECTED_PREFIX} by {actor}"
    if cleaned_reason:
        message = f"{message}: {cleaned_reason}"
    attachment.validator_message = message
    attachment.validated_at = timezone.now()
    attachment.save(update_fields=["validator_message", "validated_at"])
    return attachment


def _parse_payload(value: str | dict[str, Any] | None) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not value:
        return None
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _decode_qr_payload_from_attachment(attachment: AuditAttachment) -> str | None:
    path = _attachment_path(attachment)
    if path is None or not path.exists() or not path.is_file():
        return None
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError:
        return None
    image = cv2.imread(str(path))
    if image is None:
        return None
    detector = cv2.QRCodeDetector()
    payload, _points, _straight_qrcode = detector.detectAndDecode(image)
    return payload or None


def _attachment_path(attachment: AuditAttachment) -> Path | None:
    raw_path = (attachment.file_path or "").strip()
    if not raw_path:
        return None
    path = Path(raw_path)
    if path.is_absolute():
        return path
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_root:
        return Path(media_root) / raw_path.lstrip("/\\")
    return Path(os.getcwd()) / raw_path.lstrip("/\\")


def _compare_payload(
    attachment: AuditAttachment,
    payload: dict[str, Any],
) -> tuple[str, AuditPdfGeneration | None, str]:
    payload_detail_id = _uuid_or_none(payload.get("audit_detail_id"))
    payload_finding_id = _uuid_or_none(payload.get("finding_id"))
    payload_version = _int_or_none(payload.get("pdf_version"))
    payload_kind = str(payload.get("pdf_kind") or "").strip()
    payload_hash = str(payload.get("content_hash") or "").strip()

    if not payload_detail_id or not payload_kind or payload_version is None or not payload_hash:
        return UNREADABLE, None, "QR payload is missing required fields."

    if payload_detail_id != _uuid_or_none(attachment.audit_detail_id):
        generation = _find_payload_generation(payload_detail_id, payload_finding_id, payload_kind, payload_version)
        return MISMATCH_VESSEL, generation, "QR payload belongs to a different audit/vessel."

    attachment_finding_id = _uuid_or_none(attachment.audit_finding_id)
    if payload_finding_id != attachment_finding_id:
        generation = _find_payload_generation(payload_detail_id, payload_finding_id, payload_kind, payload_version)
        return MISMATCH_FINDING, generation, "QR payload belongs to a different finding."

    current_generation = (
        AuditPdfGeneration.objects.filter(
            audit_detail_id=payload_detail_id,
            audit_finding_id=payload_finding_id,
            pdf_kind=payload_kind,
            is_superseded=False,
        )
        .order_by("-pdf_version", "-generated_at")
        .first()
    )
    if current_generation is None:
        return MISMATCH_VERSION, None, "No active PDF generation exists for this payload."

    if current_generation.pdf_version != payload_version or current_generation.content_hash != payload_hash:
        generation = _find_payload_generation(payload_detail_id, payload_finding_id, payload_kind, payload_version)
        return MISMATCH_VERSION, generation, "QR payload does not match the active PDF version/hash."

    return MATCHED, current_generation, "QR payload matches the active PDF generation."


def _find_payload_generation(
    audit_detail_id: UUID,
    finding_id: UUID | None,
    pdf_kind: str,
    pdf_version: int,
) -> AuditPdfGeneration | None:
    return AuditPdfGeneration.objects.filter(
        audit_detail_id=audit_detail_id,
        audit_finding_id=finding_id,
        pdf_kind=pdf_kind,
        pdf_version=pdf_version,
    ).first()


def _persist_validation(
    attachment: AuditAttachment,
    *,
    status: str,
    linked_pdf_generation_id: UUID | None,
    message: str,
) -> AuditScanValidationResult:
    with transaction.atomic():
        attachment.pdf_hash_validation_status = status
        attachment.linked_pdf_generation_id = linked_pdf_generation_id
        attachment.validated_at = timezone.now()
        attachment.validator_message = message
        attachment.save(
            update_fields=[
                "pdf_hash_validation_status",
                "linked_pdf_generation_id",
                "validated_at",
                "validator_message",
            ]
        )
    return AuditScanValidationResult(attachment=attachment, status=status, message=message)


def _uuid_or_none(value: object) -> UUID | None:
    if value in (None, ""):
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _user_identifier(user: object) -> str:
    for attr in ("id", "pk", "username"):
        value = getattr(user, attr, None)
        if value:
            return str(value)[:100]
    return "system"


__all__ = [
    "MATCHED",
    "MISMATCH_FINDING",
    "MISMATCH_VESSEL",
    "MISMATCH_VERSION",
    "NOT_APPLICABLE",
    "QUEUE_STATUSES",
    "UNREADABLE",
    "accept_scan_with_reason",
    "reject_scan_for_rescan",
    "scan_validation_queue_queryset",
    "validate_uploaded_scan",
]
