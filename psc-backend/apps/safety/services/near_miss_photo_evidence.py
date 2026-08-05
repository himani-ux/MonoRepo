from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from django.utils import timezone
from django.utils.text import get_valid_filename
from rest_framework.exceptions import ValidationError

from apps.safety.models import EvidenceItem, Incident, IncidentEvidence


MAX_NEAR_MISS_PHOTO_BYTES = 3 * 1024 * 1024
ALLOWED_NEAR_MISS_PHOTO_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_NEAR_MISS_PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png"}


def store_near_miss_photo_evidence(
    *,
    near_miss: Incident,
    uploaded_file,
    actor_id: str,
    title: str = "High severity image",
    description: str = "Image uploaded during high-severity near miss submission.",
    source_label: str = "NEAR_MISS_CREATE",
) -> EvidenceItem:
    actor_id = str(actor_id or "system")[:128]
    metadata = _store_photo_file(near_miss=near_miss, uploaded_file=uploaded_file)
    tab_row, _ = IncidentEvidence.objects.get_or_create(
        incident=near_miss,
        tab_code=IncidentEvidence.TabCode.ELECTRONIC,
        defaults={
            "summary": "Near miss photo evidence.",
            "entry_count": 0,
            "structured_data": {"source": "near_miss_create", "attachments": []},
            "status_chip": "Near miss photo evidence",
            "schema_version": near_miss.schema_version or 1,
            "created_by": actor_id,
            "updated_by": actor_id,
        },
    )

    structured_data = dict(tab_row.structured_data or {})
    attachments = list(structured_data.get("attachments") or [])
    attachments.append(metadata)
    structured_data["attachments"] = attachments

    evidence_item = EvidenceItem.objects.create(
        incident=near_miss,
        evidence_tab=tab_row,
        item_type=EvidenceItem.ItemType.PHYSICAL,
        title=title,
        description=description,
        source_label=source_label,
        metadata_json={
            "near_miss_evidence_type": "PHOTO",
            "high_severity_required": True,
            "recorded_at": timezone.now().isoformat(),
            **metadata,
        },
        created_by=actor_id,
        updated_by=actor_id,
        schema_version=near_miss.schema_version or 1,
    )

    tab_row.structured_data = structured_data
    tab_row.entry_count = max(int(tab_row.entry_count or 0) + 1, tab_row.items.count())
    tab_row.summary = title
    tab_row.status_chip = f"{tab_row.entry_count} near-miss photo attachment{'s' if tab_row.entry_count != 1 else ''}"
    tab_row.updated_by = actor_id
    tab_row.updated_date = timezone.now()
    tab_row.save(update_fields=("summary", "structured_data", "entry_count", "status_chip", "updated_by", "updated_date"))
    return evidence_item


def _store_photo_file(*, near_miss: Incident, uploaded_file) -> dict[str, object]:
    content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
    suffix = Path(str(uploaded_file.name or "")).suffix.lower()
    if content_type not in ALLOWED_NEAR_MISS_PHOTO_CONTENT_TYPES or suffix not in ALLOWED_NEAR_MISS_PHOTO_SUFFIXES:
        raise ValidationError({"photo": "Photo must be a JPG, JPEG, or PNG image."})

    size = int(getattr(uploaded_file, "size", 0) or 0)
    if size <= 0:
        raise ValidationError({"photo": "Photo file is empty."})
    if size > MAX_NEAR_MISS_PHOTO_BYTES:
        raise ValidationError({"photo": "Photo must be 3MB or smaller."})

    relative_path, absolute_path = _build_storage_path(
        vessel_id=str(near_miss.vessel_id),
        near_miss_id=str(near_miss.id),
        original_name=str(uploaded_file.name or "photo"),
    )
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    with absolute_path.open("wb") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return {
        "attachment_path": relative_path,
        "byte_size": size,
        "content_type": content_type,
        "file_name": Path(relative_path).name,
        "original_name": str(uploaded_file.name or ""),
        "uploaded_at": timezone.now().isoformat(),
    }


def _build_storage_path(*, vessel_id: str, near_miss_id: str, original_name: str) -> tuple[str, Path]:
    default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
    storage_root = Path(os.getenv("SAFETY_EXPORT_ROOT") or default_root).resolve(strict=False)
    suffix = Path(original_name).suffix.lower()
    safe_stem = Path(get_valid_filename(Path(original_name).stem or "photo")).stem[:80] or "photo"
    file_name = f"{safe_stem}-{uuid4().hex}{suffix}"
    safe_vessel_id = get_valid_filename(vessel_id or "unknown-vessel") or "unknown-vessel"
    relative_path = (
        Path("vessels")
        / safe_vessel_id
        / "near-miss"
        / near_miss_id
        / "create"
        / "photos"
        / file_name
    )
    absolute_path = (storage_root / relative_path).resolve(strict=False)
    try:
        absolute_path.relative_to(storage_root)
    except ValueError as exc:
        raise ValidationError({"photo": "Invalid photo storage path."}) from exc
    return relative_path.as_posix(), absolute_path
