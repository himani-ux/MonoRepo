from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from django.db import connections
from django.db import IntegrityError, models

from .base import PublicIdMixin


SCALAR_ENVELOPE_KEY = "__history_scalar__"


def _prepare_history_json_value(value, *, envelope_scalars: bool = False):
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(key): _prepare_history_nested_json_value(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [_prepare_history_nested_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_prepare_history_nested_json_value(item) for item in value]
    if isinstance(value, set):
        return [_prepare_history_nested_json_value(item) for item in sorted(value, key=lambda item: repr(item))]
    if isinstance(value, (date, datetime)):
        normalized = value.isoformat()
        return {SCALAR_ENVELOPE_KEY: normalized} if envelope_scalars else normalized
    if isinstance(value, Decimal):
        normalized = format(value, "f")
        return {SCALAR_ENVELOPE_KEY: normalized} if envelope_scalars else normalized
    if isinstance(value, (str, int, float, bool)):
        return {SCALAR_ENVELOPE_KEY: value} if envelope_scalars else value
    normalized = str(value)
    return {SCALAR_ENVELOPE_KEY: normalized} if envelope_scalars else normalized


def _prepare_history_nested_json_value(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(key): _prepare_history_nested_json_value(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [_prepare_history_nested_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_prepare_history_nested_json_value(item) for item in value]
    if isinstance(value, set):
        return [_prepare_history_nested_json_value(item) for item in sorted(value, key=lambda item: repr(item))]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class SafetyFieldHistory(PublicIdMixin):
    parent_table = models.CharField(max_length=64)
    parent_id = models.BigIntegerField()
    field_name = models.CharField(max_length=128)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    change_reason = models.TextField(null=True, blank=True)
    actor_user_id = models.CharField(max_length=64)
    actor_role_code = models.CharField(max_length=16)
    changed_at = models.DateTimeField(auto_now_add=True)
    schema_version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "vims_safety_field_history"
        ordering = ("changed_at", "id")

    def save(self, *args, **kwargs):
        if self.pk is not None and not self._state.adding:
            raise IntegrityError("Safety field history rows are append-only.")
        using = kwargs.get("using") or self._state.db or "default"
        envelope_scalars = connections[using].vendor == "microsoft"
        self.old_value = _prepare_history_json_value(self.old_value, envelope_scalars=envelope_scalars)
        self.new_value = _prepare_history_json_value(self.new_value, envelope_scalars=envelope_scalars)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise IntegrityError("Safety field history rows are append-only.")
