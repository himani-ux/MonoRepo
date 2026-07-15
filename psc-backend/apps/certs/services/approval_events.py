from __future__ import annotations

from django.db import connection

from apps.certs.services.audit_log import resolve_actor_id, resolve_actor_role


def record_approval_event(
    *,
    tracked_item_id: str,
    from_state: str,
    to_state: str,
    actor,
    reason: str | None = None,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO dbo.vims_certs_approval_event (
                tracked_item_id, from_state, to_state, actor_user_id, actor_role, reason
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                tracked_item_id,
                from_state,
                to_state,
                resolve_actor_id(actor),
                resolve_actor_role(actor),
                reason,
            ],
        )
