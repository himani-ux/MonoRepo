"""Audit vessel lookup helpers."""

from __future__ import annotations

import re
from uuid import UUID

from django.db import DatabaseError, OperationalError, ProgrammingError, connection


_TOP_RANK_ORDER = ("MASTER", "CO", "CE", "2E")
_TOP_RANK_LABELS = {
    "MASTER": "Master",
    "CO": "Chief Officer",
    "CE": "Chief Engineer",
    "2E": "Second Engineer",
}


def list_audit_vessel_options(*, user) -> list[dict[str, object]]:
    """Return vessel options readable by the current Audit user."""

    direct_vessel_id = _normalize_vessel_id(getattr(user, "vessel_id", None))
    direct_vessel_name = str(getattr(user, "vessel_name", "") or "").strip()
    direct_vessel_code = str(getattr(user, "vessel_code", "") or "").strip()
    if direct_vessel_id and (direct_vessel_name or direct_vessel_code):
        return _with_top_rank_personnel(
            [
                {
                    "id": direct_vessel_id,
                    "vessel_code": direct_vessel_code,
                    "vessel_name": direct_vessel_name or f"Vessel {direct_vessel_id}",
                }
            ]
        )

    explicit_vessel_ids = [
        vessel_id
        for vessel_id in (_normalize_vessel_id(value) for value in (getattr(user, "vessel_ids", None) or []))
        if vessel_id
    ]
    if explicit_vessel_ids:
        return _with_top_rank_personnel(_lookup_vessel_rows(explicit_vessel_ids))

    if direct_vessel_id:
        rows = _lookup_vessel_rows([direct_vessel_id])
        return _with_top_rank_personnel(
            rows
            or [
                {
                    "id": direct_vessel_id,
                    "vessel_code": direct_vessel_id,
                    "vessel_name": f"Vessel {direct_vessel_id}",
                }
            ]
        )

    if str(getattr(user, "user_type", "") or "").strip().upper() == "OFFICE":
        if _has_global_office_vessel_access(user):
            return _with_top_rank_personnel(_lookup_vessel_rows(None))
        assigned_vessel_ids = _assigned_office_vessel_ids(user)
        if assigned_vessel_ids:
            return _with_top_rank_personnel(_lookup_vessel_rows(assigned_vessel_ids))
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
    labels: dict[str, str] = {}
    for row in _lookup_vessel_rows(normalized_ids):
        label = _format_vessel_label(row)
        for key in _vessel_lookup_keys(row.get("id")):
            labels[key] = label
    return labels


def _normalize_vessel_id(value: object) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    return normalized or None


def _vessel_lookup_keys(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    keys = [text.lower()]
    try:
        parsed = UUID(text)
    except (TypeError, ValueError, AttributeError):
        return keys
    return list(dict.fromkeys([*keys, str(parsed).lower(), parsed.hex.lower()]))


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
    lookup_ids = list(dict.fromkeys(key for vessel_id in normalized_ids for key in _vessel_lookup_keys(vessel_id)))
    try:
        with connection.cursor() as cursor:
            if lookup_ids:
                placeholders = ",".join(["%s"] * len(lookup_ids))
                cursor.execute(
                    f"""
                    SELECT CAST(id AS VARCHAR(64)), vesselCode, vesselName
                    FROM VesselData
                    WHERE LOWER(CAST(id AS VARCHAR(64))) IN ({placeholders})
                      AND COALESCE(is_deleted, 0) = 0
                    ORDER BY vesselCode, vesselName, id
                    """,
                    lookup_ids,
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


def _with_top_rank_personnel(vessel_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if not vessel_rows:
        return vessel_rows

    personnel_by_vessel = _lookup_top_rank_personnel([row.get("id") for row in vessel_rows])
    enriched_rows: list[dict[str, object]] = []
    for row in vessel_rows:
        top_rank_personnel: list[dict[str, str]] = []
        for key in _vessel_lookup_keys(row.get("id")):
            top_rank_personnel = personnel_by_vessel.get(key.lower(), [])
            if top_rank_personnel:
                break
        enriched_rows.append({**row, "top_rank_personnel": top_rank_personnel})
    return enriched_rows


def _lookup_top_rank_personnel(vessel_ids: list[object]) -> dict[str, list[dict[str, str]]]:
    lookup_ids = list(
        dict.fromkeys(
            key
            for vessel_id in (_normalize_vessel_id(value) for value in vessel_ids)
            if vessel_id
            for key in _vessel_lookup_keys(vessel_id)
        )
    )
    if not lookup_ids:
        return {}

    rows = _fetch_top_rank_personnel_live(lookup_ids)
    if not rows:
        rows = _fetch_top_rank_personnel_legacy(lookup_ids)
    return _group_top_rank_personnel(rows)


def _fetch_top_rank_personnel_live(lookup_ids: list[str]) -> list[tuple[object, ...]]:
    placeholders = ",".join(["%s"] * len(lookup_ids))
    rank_join = (
        "LEFT JOIN master_applied_rank r ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)"
        if connection.vendor == "microsoft"
        else "LEFT JOIN master_applied_rank r ON r.id = h.rank_name"
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    CAST(coh.Vessel AS VARCHAR(64)) AS vessel_id,
                    h.CrewID,
                    h.first_name,
                    h.surname,
                    COALESCE(fcl.CrewName, '') AS crew_name,
                    COALESCE(r.rank_name, h.rank_name, '') AS rank_name
                FROM Crew_Onboarding_History coh
                INNER JOIN HRM501 h
                    ON h.CrewID = coh.CrewID
                LEFT JOIN Final_crew_list fcl
                    ON fcl.CrewID = coh.CrewID
                   AND COALESCE(fcl.is_delete, 0) = 0
                {rank_join}
                WHERE LOWER(CAST(coh.Vessel AS VARCHAR(64))) IN ({placeholders})
                  AND coh.SignOffDate IS NULL
                  AND COALESCE(coh.is_active, 1) = 1
                  AND COALESCE(coh.is_deleted, 0) = 0
                  AND COALESCE(h.is_active, 1) = 1
                  AND COALESCE(h.is_deleted, 0) = 0
                ORDER BY COALESCE(r.rank_name, h.rank_name, ''), h.first_name, h.surname, h.CrewID
                """,
                lookup_ids,
            )
            return list(cursor.fetchall())
    except (DatabaseError, OperationalError, ProgrammingError, ValueError):
        return []


def _fetch_top_rank_personnel_legacy(lookup_ids: list[str]) -> list[tuple[object, ...]]:
    placeholders = ",".join(["%s"] * len(lookup_ids))
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    coh.vessel_id AS vessel_id,
                    coh.crew_id,
                    '' AS first_name,
                    '' AS surname,
                    '' AS crew_name,
                    COALESCE(hr.rank, coh.rank, '') AS rank_name
                FROM Crew_Onboarding_History coh
                LEFT JOIN HRM501 hr
                    ON hr.crew_id = coh.crew_id
                WHERE LOWER(CAST(coh.vessel_id AS VARCHAR(64))) IN ({placeholders})
                  AND coh.is_current = %s
                ORDER BY COALESCE(hr.rank, coh.rank, ''), coh.crew_id
                """,
                [*lookup_ids, True],
            )
            return list(cursor.fetchall())
    except (DatabaseError, OperationalError, ProgrammingError, ValueError):
        return []


def _group_top_rank_personnel(rows: list[tuple[object, ...]]) -> dict[str, list[dict[str, str]]]:
    ranked_by_vessel: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        vessel_id, crew_id, first_name, surname, crew_name, rank_name = row[:6]
        rank_code = _top_rank_code(rank_name)
        if not rank_code:
            continue

        name = _format_crew_name(crew_name, first_name, surname, crew_id)
        if not name:
            continue

        item = {
            "crew_id": str(crew_id or "").strip(),
            "crew_name": name,
            "rank_code": rank_code,
            "rank_name": _TOP_RANK_LABELS[rank_code],
        }
        for key in _vessel_lookup_keys(vessel_id):
            ranked_by_vessel.setdefault(key.lower(), {}).setdefault(rank_code, item)

    return {
        vessel_key: [ranked[rank_code] for rank_code in _TOP_RANK_ORDER if rank_code in ranked]
        for vessel_key, ranked in ranked_by_vessel.items()
    }


def _format_crew_name(crew_name: object, first_name: object, surname: object, crew_id: object) -> str:
    explicit_name = str(crew_name or "").strip()
    if explicit_name:
        return explicit_name
    name = " ".join(part for part in (str(first_name or "").strip(), str(surname or "").strip()) if part)
    return name or str(crew_id or "").strip()


def _top_rank_code(rank_name: object) -> str | None:
    text = str(rank_name or "").strip().upper()
    if not text:
        return None
    normalized = re.sub(r"[^A-Z0-9]+", "", text)
    if normalized in {"MASTER", "CAPTAIN"} or normalized.startswith("MASTER"):
        return "MASTER"
    if normalized in {"CO", "CHIEFOFFICER", "CHIEFMATE", "CHIEFOFF"}:
        return "CO"
    if normalized in {"CE", "CHIEFENGINEER"}:
        return "CE"
    if normalized in {"2E", "SECONDENGINEER", "2NDENGINEER", "SECONDASSISTANTENGINEER"}:
        return "2E"
    return None
