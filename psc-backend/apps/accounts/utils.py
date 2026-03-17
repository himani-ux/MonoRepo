from __future__ import annotations

import logging
from typing import Optional, Tuple, List
import json

from django.db import connection

from .models import MscProfile, RoleCodes

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
        parse_id_list(profile.process_ids),
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
    """
    Resolve office permissions using mapping_role_user -> master_role -> msc_profiles.
    Falls back to empty lists if no mapping exists.
    """
    identifiers = [v for v in (username, employee_id) if v]
    if not identifiers:
        return [], []

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
            _role_name, form_ids, process_ids = row
            return (
                parse_id_list(form_ids),
                parse_id_list(process_ids),
            )

    return [], []
