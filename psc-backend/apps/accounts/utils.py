from __future__ import annotations

import json
import logging
from typing import List, Optional, Tuple

from django.db import connection

from .models import MscProfile, OfficeUser, RoleCodes

logger = logging.getLogger(__name__)

def normalize_uuid_for_sql(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    uid = str(value)
    if '-' not in uid and len(uid) == 32:
        return f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
    return uid


def get_rank_name_by_id(rank_id: Optional[str]) -> Optional[str]:
    """Resolve master_applied_rank.rank_name for a given rank UUID."""
    if not rank_id:
        return None
    uid = normalize_uuid_for_sql(rank_id)
    if not uid:
        return None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rank_name
            FROM master_applied_rank
            WHERE id = CAST(%s AS uniqueidentifier)
              AND is_active = 1
              AND is_deleted = 0
            """,
            [uid],
        )
        row = cursor.fetchone()
    return row[0] if row else None


def get_crew_display_name(crew_uuid: Optional[str]) -> Optional[str]:
    """Resolve crew display name with actual rank text."""
    if not crew_uuid:
        return None
    uid = normalize_uuid_for_sql(crew_uuid)
    if not uid:
        return None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                h.first_name,
                h.surname,
                r.rank_name
            FROM HRM501 h
            LEFT JOIN master_applied_rank r
                ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
            WHERE h.id = CAST(%s AS uniqueidentifier)
              AND h.is_deleted = 0
            """,
            [uid],
        )
        row = cursor.fetchone()
    if not row:
        return None
    first_name, surname, rank_name = row
    full_name = f"{first_name or ''} {surname or ''}".strip()
    if rank_name:
        return f"{rank_name} - {full_name}".strip()
    return full_name or None


def get_crew_display_name_by_crewid(crew_id: Optional[str]) -> Optional[str]:
    """Resolve crew display name using CrewID."""
    if not crew_id:
        return None
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    h.first_name,
                    h.surname,
                    r.rank_name
                FROM HRM501 h
                LEFT JOIN master_applied_rank r
                    ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
                WHERE h.CrewID = %s
                  AND h.is_deleted = 0
                """,
                [str(crew_id)],
            )
            row = cursor.fetchone()
    except Exception:
        # Fallback without rank join to avoid response serialization failures.
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    h.first_name,
                    h.surname,
                    NULL as rank_name
                FROM HRM501 h
                WHERE h.CrewID = %s
                  AND h.is_deleted = 0
                """,
                [str(crew_id)],
            )
            row = cursor.fetchone()
    if not row:
        return None
    first_name, surname, rank_name = row
    full_name = f"{first_name or ''} {surname or ''}".strip()
    if rank_name:
        return f"{rank_name} - {full_name}".strip()
    return full_name or None


def parse_id_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    raw = str(value).strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass
    return [part.strip() for part in raw.split(',') if part.strip()]


def merge_audit_default_process_ids(process_ids: Optional[List[str]], *designations: Optional[str]) -> List[str]:
    merged: List[str] = []
    seen: set[str] = set()

    for process_id in process_ids or []:
        normalized = str(process_id or "").strip().upper()
        if not normalized or normalized in seen:
            continue
        merged.append(normalized)
        seen.add(normalized)

    from apps.inspection.audit.permissions import default_audit_gates_for_designation

    for designation in designations:
        for process_id in sorted(default_audit_gates_for_designation(designation)):
            normalized = str(process_id or "").strip().upper()
            if not normalized or normalized in seen:
                continue
            merged.append(normalized)
            seen.add(normalized)

    return merged


def get_profile_permissions(profile_name: Optional[str], work_side: bool) -> Tuple[List[str], List[str]]:
    if not profile_name:
        return [], []
    profile = (
        MscProfile.objects.filter(
            profile_name__iexact=profile_name,
            work_side=work_side,
            is_active=True,
            is_deleted=False,
        )
        .order_by('-created_on')
        .first()
    )
    if not profile:
        return [], []
    return (
        parse_id_list(profile.form_ids),
        merge_audit_default_process_ids(parse_id_list(profile.process_ids), profile.profile_name),
    )


def _normalized_office_identifiers(
    username: Optional[str] = None,
    employee_id: Optional[str] = None,
    identifiers: Optional[List[str]] = None,
) -> List[str]:
    if identifiers is None:
        raw_identifiers = [username, employee_id]
    else:
        raw_identifiers = identifiers

    normalized_identifiers: List[str] = []
    for value in raw_identifiers:
        normalized = str(value).strip() if value is not None else ''
        if normalized and normalized not in normalized_identifiers:
            normalized_identifiers.append(normalized)

    return normalized_identifiers


def get_office_global_reviewer_role(
    username: Optional[str] = None,
    employee_id: Optional[str] = None,
    identifiers: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Resolve global office reviewer role from profile mapping:
    mapping_role_user.role_id -> msc_profiles.profile_id -> Mapping_CrewAssReviewers.

    Returns:
    - RoleCodes.DPA
    - RoleCodes.OFFICE_PIC
    - None (no global reviewer mapping)
    """
    normalized_identifiers = _normalized_office_identifiers(
        username=username,
        employee_id=employee_id,
        identifiers=identifiers,
    )
    if not normalized_identifiers:
        return None

    sql_server = """
        SELECT TOP 1
            CASE
                WHEN mcar.DPA_RoleId = p.profile_id THEN 'DPA'
                WHEN mcar.PIC_RoleId = p.profile_id THEN 'OFFICE_PIC'
            END AS reviewer_role
        FROM mapping_role_user mru
        INNER JOIN msc_profiles p
            ON p.profile_id = mru.role_id
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        INNER JOIN Mapping_CrewAssReviewers mcar
            ON (
                mcar.DPA_RoleId = p.profile_id
                OR mcar.PIC_RoleId = p.profile_id
            )
           AND mcar.is_active = 1
           AND mcar.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
        ORDER BY CASE
            WHEN mcar.DPA_RoleId = p.profile_id THEN 0
            ELSE 1
        END
    """
    sql_sqlite = """
        SELECT
            CASE
                WHEN mcar.DPA_RoleId = p.profile_id THEN 'DPA'
                WHEN mcar.PIC_RoleId = p.profile_id THEN 'OFFICE_PIC'
            END AS reviewer_role
        FROM mapping_role_user mru
        INNER JOIN msc_profiles p
            ON p.profile_id = mru.role_id
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        INNER JOIN Mapping_CrewAssReviewers mcar
            ON (
                mcar.DPA_RoleId = p.profile_id
                OR mcar.PIC_RoleId = p.profile_id
            )
           AND mcar.is_active = 1
           AND mcar.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
        ORDER BY CASE
            WHEN mcar.DPA_RoleId = p.profile_id THEN 0
            ELSE 1
        END
        LIMIT 1
    """
    sql = sql_sqlite if connection.vendor == 'sqlite' else sql_server

    try:
        for ident in normalized_identifiers:
            with connection.cursor() as cursor:
                cursor.execute(sql, [str(ident)])
                row = cursor.fetchone()
            if not row:
                continue
            reviewer_role = str(row[0]).strip() if row[0] is not None else ''
            if reviewer_role in (RoleCodes.DPA, RoleCodes.OFFICE_PIC):
                return reviewer_role
    except Exception as e:
        error_text = str(e).lower()
        if 'no such table' in error_text or 'invalid object name' in error_text:
            logger.warning(
                "Reviewer mapping tables unavailable for %s; skipping global reviewer lookup: %s",
                normalized_identifiers,
                e,
            )
            return None
        logger.error(
            "Error resolving global reviewer role for %s: %s",
            normalized_identifiers,
            e,
        )
        return None

    return None


def get_office_permissions_by_mapping(
    username: Optional[str],
    employee_id: Optional[str],
) -> Tuple[List[str], List[str]]:
    _role_name, form_ids, process_ids = get_office_profile_bundle_by_mapping(
        username=username,
        employee_id=employee_id,
    )
    return form_ids, process_ids


def get_office_profile_bundle_by_mapping(
    username: Optional[str],
    employee_id: Optional[str],
) -> Tuple[Optional[str], List[str], List[str]]:
    """
    Resolve office profile name and permissions using mapping_role_user -> master_role -> msc_profiles.
    Falls back to empty lists if no mapping exists.
    """
    identifiers = [v for v in (username, employee_id) if v]
    if not identifiers:
        return None, [], []

    # Raw SQL to avoid UUID conversion issues from ORM on some DBs
    sql = """
        SELECT TOP 1 mr.role_name, p.form_ids, p.process_ids
        FROM mapping_role_user mru
        LEFT JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        LEFT JOIN msc_profiles p
            ON p.profile_name = mr.role_name
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
    """

    for ident in identifiers:
        with connection.cursor() as cursor:
            cursor.execute(sql, [str(ident)])
            row = cursor.fetchone()
        if row:
            role_name, form_ids, process_ids = row
            resolved_role_name = str(role_name).strip() if role_name not in (None, "") else None
            return (
                resolved_role_name,
                parse_id_list(form_ids),
                merge_audit_default_process_ids(parse_id_list(process_ids), resolved_role_name),
            )

    return None, [], []


def get_office_profile_id_by_mapping(
    username: Optional[str],
    employee_id: Optional[str],
    profile_name: Optional[str] = None,
) -> Optional[str]:
    identifiers = [v for v in (username, employee_id) if v]
    sql_server = """
        SELECT TOP 1 COALESCE(CONVERT(varchar(36), p.profile_id), CONVERT(varchar(36), mru.role_id))
        FROM mapping_role_user mru
        LEFT JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        LEFT JOIN msc_profiles p
            ON (
                p.profile_id = mru.role_id
                OR p.profile_name = mr.role_name
            )
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
    """
    sql_sqlite = """
        SELECT COALESCE(CAST(p.profile_id AS TEXT), CAST(mru.role_id AS TEXT))
        FROM mapping_role_user mru
        LEFT JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        LEFT JOIN msc_profiles p
            ON (
                p.profile_id = mru.role_id
                OR p.profile_name = mr.role_name
            )
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
        LIMIT 1
    """
    sql = sql_sqlite if connection.vendor == 'sqlite' else sql_server

    try:
        for ident in identifiers:
            with connection.cursor() as cursor:
                cursor.execute(sql, [str(ident)])
                row = cursor.fetchone()
            if row and row[0] not in (None, ""):
                return str(row[0]).strip()
    except Exception as exc:
        logger.warning("Office profile id mapping lookup failed for %s: %s", identifiers, exc)

    if profile_name:
        profile = (
            MscProfile.objects.filter(
                profile_name__iexact=profile_name,
                work_side=False,
                is_active=True,
                is_deleted=False,
            )
            .order_by('-created_on')
            .first()
        )
        if profile:
            return str(profile.profile_id)

    return None


def resolve_safety_role_name(
    *,
    user_type: Optional[str],
    role: Optional[str],
    rank: Optional[str] = None,
    profile_name: Optional[str] = None,
) -> Optional[str]:
    normalized_user_type = str(user_type or "").strip().upper()
    normalized_role = str(role or "").strip().upper()
    normalized_rank = str(rank or "").strip().upper()
    normalized_profile = str(profile_name or "").strip().upper()

    if normalized_user_type == "VESSEL":
        if normalized_rank in {"MASTER", "CAPTAIN", "ACTING MASTER"}:
            return "MASTER"
        if normalized_rank in {"CHIEF OFFICER", "CHIEF MATE", "C/O", "CO"}:
            return "CO"
        if normalized_rank in {"CHIEF ENGINEER", "C/E", "CE"}:
            return "CE"
        if normalized_rank in {"SECOND ENGINEER", "2ND ENGINEER", "2/E", "2E"}:
            return "2/E"
        return normalized_rank or normalized_role or None

    if normalized_profile == "SEQ MANAGER" or normalized_role == RoleCodes.DPA:
        return "DPA"
    if normalized_profile == "FLEET MANAGER":
        return "FM"
    if normalized_profile:
        return normalized_profile
    return normalized_role or None


GLOBAL_READ_SCOPE_OFFICE_PROFILES = {
    "CHIEF ACCOUNTING OFFICER",
}


def office_profile_has_global_read_scope(profile_name: Optional[str]) -> bool:
    normalized_profile = str(profile_name or "").strip().upper()
    return normalized_profile in GLOBAL_READ_SCOPE_OFFICE_PROFILES


def resolve_current_office_permission_snapshot(
    *,
    user_type: Optional[str] = "OFFICE",
    login_id: Optional[str],
    employee_id: Optional[str],
    role: Optional[str],
    has_global_vessel_access: Optional[bool],
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    department: Optional[str] = None,
) -> dict:
    office_user = (
        OfficeUser.objects.filter(is_active=True, is_deleted=False)
        .filter(employee_id__iexact=employee_id)
        .first()
        if employee_id
        else None
    )

    if office_user is None and login_id:
        office_user = (
            OfficeUser.objects.filter(is_active=True, is_deleted=False)
            .filter(username__iexact=login_id)
            .first()
        )

    mapped_profile_name, form_ids, process_ids = get_office_profile_bundle_by_mapping(
        username=login_id,
        employee_id=employee_id,
    )
    profile_name = mapped_profile_name or (office_user.employee_role if office_user and office_user.employee_role else None)
    profile_id = get_office_profile_id_by_mapping(
        username=login_id,
        employee_id=employee_id,
        profile_name=profile_name,
    )

    if not form_ids and not process_ids and office_user and office_user.employee_role:
        form_ids, process_ids = get_profile_permissions(office_user.employee_role, work_side=False)

    if not form_ids and not process_ids and role:
        form_ids, process_ids = get_profile_permissions(role, work_side=False)

    mapped_global_role = get_office_global_reviewer_role(
        username=login_id,
        employee_id=employee_id,
    )
    initial_safety_role_name = resolve_safety_role_name(
        user_type=user_type,
        role=role,
        profile_name=profile_name,
    )
    if mapped_global_role == RoleCodes.DPA:
        role = RoleCodes.DPA
        has_global_vessel_access = True
    elif mapped_global_role == RoleCodes.OFFICE_PIC:
        role = RoleCodes.OFFICE_PIC
        has_global_vessel_access = True
    elif initial_safety_role_name == "FM":
        has_global_vessel_access = True
    elif office_profile_has_global_read_scope(profile_name):
        has_global_vessel_access = True
    elif has_global_vessel_access is None:
        has_global_vessel_access = False

    safety_role_name = resolve_safety_role_name(
        user_type=user_type,
        role=role,
        profile_name=profile_name,
    )
    role_default = role if role == RoleCodes.DPA else None
    process_ids = merge_audit_default_process_ids(process_ids, profile_name, role_default)

    return {
        'role': role,
        'role_name': profile_name or role,
        'profile_id': profile_id,
        'safety_role_name': safety_role_name,
        'form_ids': form_ids,
        'process_ids': process_ids,
        'has_global_vessel_access': has_global_vessel_access,
        'employee_id': office_user.employee_id if office_user else employee_id,
        'email': office_user.email_id if office_user and office_user.email_id else email,
        'department': office_user.department if office_user and office_user.department else department,
        'full_name': office_user.full_name if office_user else full_name,
    }


def resolve_current_vessel_permission_snapshot(
    *,
    user_type: Optional[str] = "VESSEL",
    role: Optional[str] = None,
    rank: Optional[str],
    full_name: Optional[str] = None,
    department: Optional[str] = None,
) -> dict:
    form_ids, process_ids = get_profile_permissions(rank, work_side=True)
    process_ids = merge_audit_default_process_ids(process_ids, rank, role)
    return {
        'rank': rank,
        'role_name': rank or role,
        'safety_role_name': resolve_safety_role_name(
            user_type=user_type,
            role=role,
            rank=rank,
        ),
        'form_ids': form_ids,
        'process_ids': process_ids,
        'department': department,
        'full_name': full_name,
    }
