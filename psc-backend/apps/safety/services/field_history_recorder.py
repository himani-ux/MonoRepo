from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from apps.safety.models.field_history import SCALAR_ENVELOPE_KEY
from apps.safety.models import SafetyFieldHistory
from apps.safety.authentication.roles import normalized_authority_role


def resolve_actor_id(user) -> str:
    if user is None:
        return "system"

    for attr_name in ("username", "employee_id", "crew_id", "user_id", "id"):
        value = getattr(user, attr_name, None)
        if value not in (None, ""):
            return str(value)
    return "system"


def resolve_actor_role(user) -> str:
    return normalized_authority_role(user) or "SYSTEM"


def normalize_history_value(value) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Mapping):
        return {str(key): normalize_history_value(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [normalize_history_value(item) for item in value]
    if isinstance(value, tuple):
        return [normalize_history_value(item) for item in value]
    if isinstance(value, set):
        return [normalize_history_value(item) for item in sorted(value, key=lambda item: repr(item))]
    return str(value)


def parse_history_value(value):
    def _unwrap_scalar_envelope(payload):
        if isinstance(payload, dict) and set(payload.keys()) == {SCALAR_ENVELOPE_KEY}:
            return _unwrap_scalar_envelope(payload[SCALAR_ENVELOPE_KEY])
        if isinstance(payload, dict):
            return {key: _unwrap_scalar_envelope(nested) for key, nested in payload.items()}
        if isinstance(payload, list):
            return [_unwrap_scalar_envelope(item) for item in payload]
        return payload

    if value is None:
        return None
    if isinstance(value, (dict, list, bool, int, float)):
        return _unwrap_scalar_envelope(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return value
        should_parse_json = (
            (stripped.startswith("{") and stripped.endswith("}"))
            or (stripped.startswith("[") and stripped.endswith("]"))
            or (stripped.startswith('"') and stripped.endswith('"'))
        )
        if should_parse_json:
            try:
                return _unwrap_scalar_envelope(json.loads(stripped))
            except (TypeError, ValueError, json.JSONDecodeError):
                return value
        return value
    return value


def history_value_as_text(value) -> str | None:
    parsed = parse_history_value(value)
    if parsed is None:
        return None
    if isinstance(parsed, bool):
        return "true" if parsed else "false"
    if isinstance(parsed, (dict, list)):
        return json.dumps(parsed, sort_keys=True, default=str)
    return str(parsed)


def capture_model_state(record, *, field_names: Iterable[str] | None = None) -> dict[str, object]:
    names = set(field_names or [])
    state: dict[str, object] = {}
    for field in record._meta.concrete_fields:
        if names and field.name not in names:
            continue
        state[field.name] = getattr(record, field.name)
    return state


def record_field_changes(
    record,
    old_state: Mapping[str, object],
    *,
    user,
    field_names: Iterable[str] | None = None,
    change_reason: str | None = None,
    parent_table: str | None = None,
):
    tracked_names = tuple(field_names or old_state.keys())
    new_state = capture_model_state(record, field_names=tracked_names)
    parent_id = getattr(record, "legacy_int_id", None) or record.pk
    rows = []
    for field_name in tracked_names:
        old_value = normalize_history_value(old_state.get(field_name))
        new_value = normalize_history_value(new_state.get(field_name))
        if old_value == new_value:
            continue
        rows.append(
            SafetyFieldHistory.objects.create(
                parent_table=parent_table or record._meta.db_table,
                parent_id=parent_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                change_reason=change_reason,
                actor_user_id=resolve_actor_id(user),
                actor_role_code=resolve_actor_role(user),
                schema_version=getattr(record, "schema_version", 1) or 1,
            )
        )
    return rows
