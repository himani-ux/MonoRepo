from __future__ import annotations

from django.db.models import Q


def _normalize_vessel_id(value: object) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


def _extract_row_vessel_ids(rows: object) -> set[str]:
    vessel_ids: set[str] = set()
    if not rows:
        return vessel_ids

    for row in rows:
        vessel_id = None
        is_current = True
        if isinstance(row, dict):
            vessel_id = row.get("vessel_id")
            is_current = row.get("is_current", True)
        else:
            vessel_id = getattr(row, "vessel_id", None)
            is_current = getattr(row, "is_current", True)

        normalized = _normalize_vessel_id(vessel_id)
        if normalized is not None and is_current:
            vessel_ids.add(normalized)
    return vessel_ids


def _normalized_role(user) -> str:
    if user is None:
        return ""
    role_name = getattr(user, "safety_role_name", None) or getattr(user, "role_name", None) or getattr(user, "role", None) or ""
    return str(role_name).strip().upper()


def _normalized_work_side(user) -> str:
    raw_value = getattr(user, "work_side", None)
    if raw_value in (True, 1, "1", "SHIP", "VESSEL"):
        return "SHIP"
    if raw_value in (False, 0, "0", "OFFICE"):
        return "OFFICE"
    if raw_value in (None, ""):
        return ""
    return str(raw_value).strip().upper()


def _has_global_role(user) -> bool:
    return _normalized_role(user) in {"DPA", "FM", "FLEET MANAGER"}


def _is_office_user(user) -> bool:
    user_type = str(getattr(user, "user_type", "") or "").strip().upper()
    return user_type == "OFFICE" or _normalized_work_side(user) == "OFFICE"


def _can_read_closed_incidents_fleetwide(user) -> bool:
    return _normalized_role(user) == "MASTER"


def _office_vessel_ids_from_vims(user) -> set[str] | None:
    try:
        from core.vessel_access import get_office_user_identifiers, get_office_user_vessel_ids
    except Exception:
        return None

    vessel_ids = get_office_user_vessel_ids(get_office_user_identifiers(user))
    if vessel_ids is None:
        return None
    return {
        vessel_id
        for vessel_id in (_normalize_vessel_id(value) for value in vessel_ids)
        if vessel_id is not None
    }


def has_global_vessel_scope(user) -> bool:
    if getattr(user, "is_global", False) or getattr(user, "global_access", False):
        return True
    if getattr(user, "has_global_vessel_access", False) is True:
        return True
    if _has_global_role(user):
        return True
    if not _is_office_user(user):
        return False

    try:
        from core.vessel_access import has_global_office_vessel_access
    except Exception:
        return False
    return has_global_office_vessel_access(user)


def _resolve_vessel_scope_ids(user) -> set[str]:
    explicit_vessel_ids = getattr(user, "vessel_ids", None)
    if explicit_vessel_ids:
        return {
            vessel_id
            for vessel_id in (_normalize_vessel_id(value) for value in explicit_vessel_ids)
            if vessel_id is not None
        }

    work_side = _normalized_work_side(user)
    if work_side == "OFFICE":
        office_vessel_ids = _office_vessel_ids_from_vims(user)
        if office_vessel_ids is not None:
            return office_vessel_ids
        return _extract_row_vessel_ids(getattr(user, "role_by_vessel_rows", None))

    direct_vessel_id = _normalize_vessel_id(getattr(user, "vessel_id", None))
    if direct_vessel_id:
        return {direct_vessel_id}

    if work_side == "SHIP":
        return _extract_row_vessel_ids(getattr(user, "crew_onboarding_rows", None))

    if _is_office_user(user):
        office_vessel_ids = _office_vessel_ids_from_vims(user)
        if office_vessel_ids is not None:
            return office_vessel_ids

    office_rows = _extract_row_vessel_ids(getattr(user, "role_by_vessel_rows", None))
    if office_rows:
        return office_rows
    return _extract_row_vessel_ids(getattr(user, "crew_onboarding_rows", None))


def get_scoped_vessel_ids(user) -> set[str]:
    return _resolve_vessel_scope_ids(user)


def user_has_vessel_access(user, vessel_id: object) -> bool:
    normalized_vessel_id = _normalize_vessel_id(vessel_id)
    if normalized_vessel_id is None:
        return False
    if has_global_vessel_scope(user):
        return True
    return normalized_vessel_id in _resolve_vessel_scope_ids(user)


def filter_by_vessel_scope(qs, user):
    if has_global_vessel_scope(user):
        return qs

    vessel_ids = _resolve_vessel_scope_ids(user)
    if _can_read_closed_incidents_fleetwide(user):
        if vessel_ids:
            return qs.filter(Q(vessel_id__in=sorted(vessel_ids)) | Q(state="CLOSED"))
        return qs.filter(state="CLOSED")

    if not vessel_ids:
        return qs.none()

    return qs.filter(vessel_id__in=sorted(vessel_ids))
