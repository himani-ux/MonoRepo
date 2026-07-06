from __future__ import annotations

import json
from typing import Any

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
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO dbo.vims_certs_audit_log (
                vessel_id, actor_user_id, actor_role, action, entity_type, entity_id,
                before_json, after_json, reason, event_metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                vessel_id,
                resolve_actor_id(actor),
                resolve_actor_role(actor),
                action,
                entity_type,
                entity_id,
                json.dumps(before, default=str) if before is not None else None,
                json.dumps(after, default=str) if after is not None else None,
                reason,
                json.dumps(metadata, default=str) if metadata is not None else None,
            ],
        )
