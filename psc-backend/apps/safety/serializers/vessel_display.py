from __future__ import annotations

from django.db import DatabaseError, OperationalError, ProgrammingError, connection
from rest_framework import serializers


def _normalize_vessel_id(value: object) -> str:
    return str(value or "").strip()


def resolve_vessel_display(vessel_id: object, *, user=None) -> dict[str, str]:
    normalized_vessel_id = _normalize_vessel_id(vessel_id)
    if not normalized_vessel_id:
        return {"vessel_code": "", "vessel_name": "", "vessel_display_name": ""}

    direct_vessel_id = _normalize_vessel_id(getattr(user, "vessel_id", None)) if user is not None else ""
    direct_vessel_name = str(getattr(user, "vessel_name", "") or "").strip() if user is not None else ""
    direct_vessel_code = str(getattr(user, "vessel_code", "") or "").strip() if user is not None else ""
    if direct_vessel_id == normalized_vessel_id and (direct_vessel_name or direct_vessel_code):
        return {
            "vessel_code": direct_vessel_code,
            "vessel_name": direct_vessel_name,
            "vessel_display_name": direct_vessel_name or direct_vessel_code,
        }

    cache = getattr(user, "_safety_vessel_display_cache", None) if user is not None else None
    if cache is None:
        cache = {}
        if user is not None:
            try:
                setattr(user, "_safety_vessel_display_cache", cache)
            except Exception:
                pass
    if normalized_vessel_id in cache:
        return cache[normalized_vessel_id]

    payload = {
        "vessel_code": "",
        "vessel_name": "",
        "vessel_display_name": normalized_vessel_id,
    }
    try:
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                cursor.execute(
                    """
                    SELECT vesselCode, vesselName
                    FROM VesselData
                    WHERE id = %s
                      AND COALESCE(is_deleted, 0) = 0
                    """,
                    [normalized_vessel_id],
                )
            else:
                cursor.execute(
                    """
                    SELECT vesselCode, vesselName
                    FROM VesselData
                    WHERE id = CAST(%s AS uniqueidentifier)
                      AND is_active = 1
                      AND is_deleted = 0
                    """,
                    [normalized_vessel_id],
                )
            row = cursor.fetchone()
    except (DatabaseError, OperationalError, ProgrammingError, ValueError):
        row = None

    if row is not None:
        vessel_code = str(row[0] or "").strip()
        vessel_name = str(row[1] or "").strip()
        payload = {
            "vessel_code": vessel_code,
            "vessel_name": vessel_name,
            "vessel_display_name": vessel_name or vessel_code or normalized_vessel_id,
        }

    if isinstance(cache, dict):
        cache[normalized_vessel_id] = payload
    return payload


class VesselDisplayMixin:
    vessel_code = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()

    def _get_vessel_display(self, obj) -> dict[str, str]:
        request = self.context.get("request")
        user = self.context.get("user") or getattr(request, "user", None)
        return resolve_vessel_display(getattr(obj, "vessel_id", None), user=user)

    def get_vessel_code(self, obj) -> str:
        return self._get_vessel_display(obj)["vessel_code"]

    def get_vessel_name(self, obj) -> str:
        return self._get_vessel_display(obj)["vessel_name"]

    def get_vessel_display_name(self, obj) -> str:
        return self._get_vessel_display(obj)["vessel_display_name"]
