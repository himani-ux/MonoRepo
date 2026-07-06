from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import hashlib

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.utils.text import get_valid_filename


def save_uploaded_cert_pdf(
    *,
    uploaded_file,
    vessel_id: str,
    tracked_item_id: str,
) -> dict[str, object]:
    upload_base = Path(getattr(settings, "UPLOAD_BASE_PATH", settings.BASE_DIR / "uploads")).resolve(strict=False)
    safe_vessel_id = get_valid_filename(str(vessel_id or "unknown-vessel")) or "unknown-vessel"
    safe_item_id = get_valid_filename(str(tracked_item_id or "unknown-tracked-item")) or "unknown-tracked-item"
    original_name = str(getattr(uploaded_file, "name", "") or "certificate.pdf")
    safe_stem = get_valid_filename(Path(original_name).stem or "certificate")[:80] or "certificate"
    filename = f"{safe_stem}-{uuid4().hex}.pdf"
    relative_path = Path("certs") / "vessels" / safe_vessel_id / "tracked-items" / safe_item_id / filename
    absolute_path = (upload_base / relative_path).resolve(strict=False)
    try:
        absolute_path.relative_to(upload_base)
    except ValueError as exc:
        raise SuspiciousFileOperation("Invalid certificate PDF storage path.") from exc

    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    with absolute_path.open("wb") as destination:
        for chunk in uploaded_file.chunks():
            digest.update(chunk)
            size += len(chunk)
            destination.write(chunk)

    return {
        "relative_path": relative_path.as_posix(),
        "absolute_path": str(absolute_path),
        "sha256": digest.hexdigest(),
        "size": size,
        "filename": original_name,
    }


def save_onboarding_batch_csv(
    *,
    content: str,
    vessel_id: str,
    batch_id: str,
    filename: str,
) -> dict[str, object]:
    upload_base = Path(getattr(settings, "UPLOAD_BASE_PATH", settings.BASE_DIR / "uploads")).resolve(strict=False)
    safe_vessel_id = get_valid_filename(str(vessel_id or "unknown-vessel")) or "unknown-vessel"
    safe_batch_id = get_valid_filename(str(batch_id or "unknown-batch")) or "unknown-batch"
    safe_filename = get_valid_filename(filename or "batch_ingest_report.csv") or "batch_ingest_report.csv"
    if not safe_filename.lower().endswith(".csv"):
        safe_filename = f"{Path(safe_filename).stem}.csv"
    relative_path = Path("certs") / "vessels" / safe_vessel_id / "onboarding" / safe_batch_id / safe_filename
    absolute_path = (upload_base / relative_path).resolve(strict=False)
    try:
        absolute_path.relative_to(upload_base)
    except ValueError as exc:
        raise SuspiciousFileOperation("Invalid onboarding CSV storage path.") from exc

    encoded = content.encode("utf-8")
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(encoded)
    return {
        "relative_path": relative_path.as_posix(),
        "absolute_path": str(absolute_path),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "size": len(encoded),
        "filename": safe_filename,
    }


def save_uploaded_class_snapshot_pdf(
    *,
    uploaded_file,
    vessel_id: str,
) -> dict[str, object]:
    upload_base = Path(getattr(settings, "UPLOAD_BASE_PATH", settings.BASE_DIR / "uploads")).resolve(strict=False)
    safe_vessel_id = get_valid_filename(str(vessel_id or "unknown-vessel")) or "unknown-vessel"
    original_name = str(getattr(uploaded_file, "name", "") or "class-status.pdf")
    safe_stem = get_valid_filename(Path(original_name).stem or "class-status")[:80] or "class-status"
    filename = f"{safe_stem}-{uuid4().hex}.pdf"
    relative_path = Path("certs") / "vessels" / safe_vessel_id / "class-snapshots" / filename
    absolute_path = (upload_base / relative_path).resolve(strict=False)
    try:
        absolute_path.relative_to(upload_base)
    except ValueError as exc:
        raise SuspiciousFileOperation("Invalid class snapshot PDF storage path.") from exc

    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    with absolute_path.open("wb") as destination:
        for chunk in uploaded_file.chunks():
            digest.update(chunk)
            size += len(chunk)
            destination.write(chunk)

    return {
        "relative_path": relative_path.as_posix(),
        "absolute_path": str(absolute_path),
        "sha256": digest.hexdigest(),
        "size": size,
        "filename": original_name,
    }


def save_generated_print_artifact(
    *,
    content: bytes,
    print_id: str,
    filename: str,
    subdir: str,
) -> dict[str, object]:
    upload_base = Path(getattr(settings, "UPLOAD_BASE_PATH", settings.BASE_DIR / "uploads")).resolve(strict=False)
    safe_print_id = get_valid_filename(str(print_id or "print-artifact")) or "print-artifact"
    safe_subdir = get_valid_filename(str(subdir or "artifacts")) or "artifacts"
    safe_filename = get_valid_filename(filename or "artifact.bin") or "artifact.bin"
    relative_path = Path("certs") / "print-artifacts" / safe_print_id / safe_subdir / safe_filename
    absolute_path = (upload_base / relative_path).resolve(strict=False)
    try:
        absolute_path.relative_to(upload_base)
    except ValueError as exc:
        raise SuspiciousFileOperation("Invalid generated print artifact storage path.") from exc

    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(content)
    return {
        "relative_path": relative_path.as_posix(),
        "absolute_path": str(absolute_path),
        "sha256": hashlib.sha256(content).hexdigest(),
        "size": len(content),
        "filename": safe_filename,
    }


def delete_stored_blob(relative_path: str) -> bool:
    upload_base = Path(getattr(settings, "UPLOAD_BASE_PATH", settings.BASE_DIR / "uploads")).resolve(strict=False)
    normalized_path = str(relative_path or "").replace("\\", "/").lstrip("/")
    absolute_path = (upload_base / normalized_path).resolve(strict=False)
    try:
        absolute_path.relative_to(upload_base)
    except ValueError as exc:
        raise SuspiciousFileOperation("Invalid certificate blob delete path.") from exc
    if not absolute_path.exists():
        return False
    if absolute_path.is_file():
        absolute_path.unlink()
        return True
    raise SuspiciousFileOperation("Certificate blob delete path is not a file.")
