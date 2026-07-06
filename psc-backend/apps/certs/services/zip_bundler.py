from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Callable
from zipfile import ZIP_DEFLATED, ZipFile

from django.utils.text import get_valid_filename


def build_share_bundle_zip(
    *,
    print_id: str,
    rows: list[dict[str, Any]],
    manifest_pdf: bytes,
    read_blob: Callable[[str], bytes],
) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as bundle:
        bundle.writestr(f"manifest_{print_id}.pdf", manifest_pdf)
        for index, row in enumerate(_ordered_rows(rows), start=1):
            blob_path = str(row.get("blob_storage_path") or "")
            filename = _certificate_filename(index, row)
            bundle.writestr(f"certificates/{filename}", read_blob(blob_path))
    return buffer.getvalue()


def _ordered_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (int(row.get("catalog_print_order") or 0), str(row.get("tracked_item_id") or "")))


def _certificate_filename(index: int, row: dict[str, Any]) -> str:
    source_name = str(row.get("blob_filename") or row.get("catalog_short_name") or row.get("catalog_code") or "certificate.pdf")
    stem = get_valid_filename(Path(source_name).stem or "certificate")[:64] or "certificate"
    return f"{index:02d}_{stem}.pdf"
