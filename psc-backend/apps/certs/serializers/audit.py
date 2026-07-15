from __future__ import annotations

import json
from typing import Any


def serialize_audit_event(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("audit_id")),
        "timestampUtc": row.get("timestamp_utc"),
        "vesselId": str(row["vessel_id"]) if row.get("vessel_id") else None,
        "actorUserId": row.get("actor_user_id"),
        "actorRole": row.get("actor_role"),
        "action": row.get("action"),
        "entityType": row.get("entity_type"),
        "entityId": row.get("entity_id"),
        "before": _json_load(row.get("before_json"), None),
        "after": _json_load(row.get("after_json"), None),
        "reason": row.get("reason"),
        "eventMetadata": _json_load(row.get("event_metadata"), None),
        "retentionTier": row.get("retention_tier"),
        "archivedAt": row.get("archived_at"),
        "schemaVersion": row.get("schema_version"),
    }


def _json_load(value: object, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return default
