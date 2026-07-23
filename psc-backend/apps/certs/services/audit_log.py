from __future__ import annotations

import json
from typing import Any
from uuid import UUID
from django.db import connection


def resolve_actor_id(user) -> str:
    for attr_name in ("user_id", "id", "employee_id", "crew_id", "login_id"):
        value = getattr(user, attr_name, None)
        if value not in (None, ""):
            return str(value)
    return "system"


def resolve_actor_role(user) -> str:
    for attr_name in ("role", "role_name", "safety_role_name", "rank"):
        value = getattr(user, attr_name, None)
        if value not in (None, ""):
            return str(value)[:32]
    return "UNKNOWN"


def record_audit_event(
    *,
    actor,
    action: str,
    entity_type: str,
    entity_id: str | None,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    vessel_id: str | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db_entity_id, metadata_payload = _audit_entity_payload(entity_id, metadata)

    params = [
        vessel_id,
        resolve_actor_id(actor),
        resolve_actor_role(actor),
        action,
        entity_type,
        db_entity_id,
        json.dumps(before, default=str) if before is not None else None,
        json.dumps(after, default=str) if after is not None else None,
        reason,
        json.dumps(metadata_payload, default=str) if metadata_payload is not None else None,
    ]

    print("\n========== AUDIT LOG ==========")
    print("vessel_id      :", vessel_id, type(vessel_id))
    print("actor_user_id  :", resolve_actor_id(actor), type(resolve_actor_id(actor)))
    print("actor_role     :", resolve_actor_role(actor))
    print("action         :", action)
    print("entity_type    :", entity_type)
    print("entity_id      :", entity_id, type(entity_id))
    print("===============================\n")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO dbo.vims_certs_audit_log (
                vessel_id,
                actor_user_id,
                actor_role,
                action,
                entity_type,
                entity_id,
                before_json,
                after_json,
                reason,
                event_metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            params,
        )


def _audit_entity_payload(
    entity_id: str | None,
    metadata: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any] | None]:
    db_entity_id = _uuid_text_or_none(entity_id)
    if db_entity_id is not None:
        return db_entity_id, metadata

    text_entity_id = str(entity_id or "").strip()
    if not text_entity_id:
        return None, metadata

    metadata_payload = dict(metadata or {})
    metadata_payload.setdefault("entityRef", text_entity_id)
    return None, metadata_payload


def _uuid_text_or_none(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return str(UUID(text))
    except (TypeError, ValueError):
        return None
