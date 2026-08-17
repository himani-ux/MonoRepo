"""Audit vessel lookup helpers."""

from __future__ import annotations

from django.db import DatabaseError, OperationalError, ProgrammingError, connection


def list_audit_vessel_options(*, user) -> list[dict[str, str]]:
    """Return vessel options readable by the current Audit user."""

    direct_vessel_id = _normalize_vessel_id(getattr(user, "vessel_id", None))
    direct_vessel_name = str(getattr(user, "vessel_name", "") or "").strip()
    direct_vessel_code = str(getattr(user, "vessel_code", "") or "").strip()
    if direct_vessel_id and (direct_vessel_name or direct_vessel_code):
        return [
            {
                "id": direct_vessel_id,
                "vessel_code": direct_vessel_code,
                "vessel_name": direct_vessel_name or f"Vessel {direct_vessel_id}",
            }
        ]

    explicit_vessel_ids = [
        vessel_id
        for vessel_id in (_normalize_vessel_id(value) for value in (getattr(user, "vessel_ids", None) or []))
        if vessel_id
    ]
    if explicit_vessel_ids:
        return _lookup_vessel_rows(explicit_vessel_ids)

    if direct_vessel_id:
        rows = _lookup_vessel_rows([direct_vessel_id])
        return rows or [
            {
                "id": direct_vessel_id,
                "vessel_code": direct_vessel_id,
                "vessel_name": f"Vessel {direct_vessel_id}",
            }
        ]

    if str(getattr(user, "user_type", "") or "").strip().upper() == "OFFICE":
        if _has_global_office_vessel_access(user):
            return _lookup_vessel_rows(None)
        assigned_vessel_ids = _assigned_office_vessel_ids(user)
        if assigned_vessel_ids:
            return _lookup_vessel_rows(assigned_vessel_ids)
    return []


def audit_vessel_label_map(vessel_ids: list[object]) -> dict[str, str]:
    """Return normalized vessel id -> readable label for Audit plan/detail serialization."""

    normalized_ids = [
        vessel_id
        for vessel_id in (_normalize_vessel_id(value) for value in vessel_ids)
        if vessel_id
    ]
    if not normalized_ids:
        return {}
    return {
        str(row["id"]).strip().lower(): _format_vessel_label(row)
        for row in _lookup_vessel_rows(normalized_ids)
    }


def _normalize_vessel_id(value: object) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    return normalized or None


def _format_vessel_label(row: dict[str, str]) -> str:
    vessel_code = str(row.get("vessel_code") or "").strip()
    vessel_name = str(row.get("vessel_name") or "").strip()
    if vessel_code and vessel_name:
        return f"{vessel_code} - {vessel_name}"
    return vessel_name or vessel_code or str(row.get("id") or "").strip()


def _get_office_user_identifiers(user) -> list[str]:
    identifiers: list[str] = []
    for attr_name in ("login_id", "employee_id", "id", "username"):
        value = getattr(user, attr_name, None)
        normalized = str(value).strip() if value not in (None, "") else ""
        if normalized and normalized not in identifiers:
            identifiers.append(normalized)
    return identifiers


def _has_global_office_vessel_access(user) -> bool:
    if getattr(user, "has_global_vessel_access", None) is True:
        return True
    role = str(getattr(user, "role", "") or "").strip().upper()
    if role in {"DPA", "SEQ MANAGER", "FM", "FLEET MANAGER", "ADMIN", "SUPER ADMIN"}:
        return True
    try:
        from core.vessel_access import has_global_office_vessel_access
    except Exception:
        return False
    return has_global_office_vessel_access(user)


def _assigned_office_vessel_ids(user) -> list[str]:
    identifiers = _get_office_user_identifiers(user)
    if not identifiers:
        return []
    assigned: list[str] = []
    try:
        with connection.cursor() as cursor:
            for identifier in identifiers:
                cursor.execute(
                    """
                    SELECT VesselId
                    FROM master_RoleByVessel
                    WHERE IsActive = 1
                      AND COALESCE(is_deleted, 0) = 0
                      AND LOWER(UserId) = LOWER(%s)
                    """,
                    [identifier],
                )
                for row in cursor.fetchall():
                    vessel_id = _normalize_vessel_id(row[0])
                    if vessel_id and vessel_id not in assigned:
                        assigned.append(vessel_id)
    except (DatabaseError, OperationalError, ProgrammingError):
        return []
    return assigned


def _lookup_vessel_rows(vessel_ids: list[str] | None) -> list[dict[str, str]]:
    normalized_ids = [
        vessel_id
        for vessel_id in (_normalize_vessel_id(value) for value in (vessel_ids or []))
        if vessel_id
    ]
    try:
        with connection.cursor() as cursor:
            if normalized_ids:
                placeholders = ",".join(["%s"] * len(normalized_ids))
                cursor.execute(
                    f"""
                    SELECT CAST(id AS VARCHAR(64)), vesselCode, vesselName
                    FROM VesselData
                    WHERE LOWER(CAST(id AS VARCHAR(64))) IN ({placeholders})
                      AND COALESCE(is_deleted, 0) = 0
                    ORDER BY vesselCode, vesselName, id
                    """,
                    [value.lower() for value in normalized_ids],
                )
            else:
                cursor.execute(
                    """
                    SELECT CAST(id AS VARCHAR(64)), vesselCode, vesselName
                    FROM VesselData
                    WHERE COALESCE(is_deleted, 0) = 0
                    ORDER BY vesselCode, vesselName, id
                    """
                )
            return [
                {
                    "id": str(row[0] or "").strip(),
                    "vessel_code": str(row[1] or "").strip(),
                    "vessel_name": str(row[2] or "").strip(),
                }
                for row in cursor.fetchall()
                if str(row[0] or "").strip()
            ]
    except (DatabaseError, OperationalError, ProgrammingError, ValueError):
        return []
