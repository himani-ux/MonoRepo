from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_system_state_hash(rows: list[dict[str, Any]], payload: dict[str, Any]) -> str:
    state = {
        "scope": payload.get("scope"),
        "vesselIds": sorted(str(value) for value in payload.get("vesselIds", [])),
        "sections": sorted(str(value) for value in payload.get("sections", [])),
        "filters": payload.get("filters") or {},
        "customCertIds": sorted(str(value) for value in payload.get("customCertIds", [])),
        "rows": [
            {
                "trackedItemId": str(row.get("tracked_item_id") or ""),
                "catalogId": str(row.get("catalog_id") or ""),
                "vesselId": str(row.get("vessel_id") or ""),
                "status": str(row.get("status") or ""),
                "expiryDate": str(row.get("expiry_date") or ""),
                "pdfAttachmentId": str(row.get("pdf_attachment_id") or ""),
                "version": int(row.get("version") or 0),
            }
            for row in sorted(rows, key=lambda item: (str(item.get("vessel_id") or ""), int(item.get("catalog_print_order") or 0), str(item.get("tracked_item_id") or "")))
        ],
    }
    encoded = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:8]
