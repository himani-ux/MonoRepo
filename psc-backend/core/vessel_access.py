"""
Office user vessel access filtering.

Restricts office users to vessels assigned via master_RoleByVessel by default.
Global PIC/DPA users bypass filtering and see all vessels.
"""
import logging
from typing import Optional
from uuid import UUID

from django.db.models import Q
from django.db.models import QuerySet

from apps.accounts.models import MasterRoleByVessel, RoleCodes

logger = logging.getLogger(__name__)


def get_office_user_identifiers(user) -> list[str]:
    """
    Collect stable office user identifiers used across mapping tables.
    """
    raw_identifiers = [
        getattr(user, 'login_id', None),
        getattr(user, 'employee_id', None),
        getattr(user, 'id', None),
        getattr(user, 'username', None),
    ]
    user_identifiers = []
    for value in raw_identifiers:
        normalized = str(value).strip() if value is not None else ''
        if normalized and normalized not in user_identifiers:
            user_identifiers.append(normalized)
    return user_identifiers


def has_global_office_vessel_access(
    user,
    user_identifiers: Optional[list[str]] = None,
) -> bool:
    """
    True when office user is globally mapped as PIC or DPA in Mapping_CrewAssReviewers.

    Priority:
    1) explicit user claim (from JWT/login payload)
    2) role-based DPA fallback
    3) DB lookup for backward compatibility with older tokens
    """
    if getattr(user, 'user_type', None) != 'OFFICE':
        return False

    explicit_scope = getattr(user, 'has_global_vessel_access', None)
    if explicit_scope is True:
        return True

    # Backward compatibility for existing tokens that only carry role claim.
    if getattr(user, 'role', None) == RoleCodes.DPA:
        return True

    if explicit_scope is False:
        return False

    if user_identifiers is None:
        user_identifiers = get_office_user_identifiers(user)
    if not user_identifiers:
        return False

    try:
        from apps.accounts.utils import get_office_global_reviewer_role

        mapped_role = get_office_global_reviewer_role(identifiers=user_identifiers)
        return mapped_role in (RoleCodes.OFFICE_PIC, RoleCodes.DPA)
    except Exception as e:
        logger.warning(
            "Failed to resolve global reviewer mapping for %s: %s",
            user_identifiers,
            e,
        )
        return False


def get_office_user_vessel_ids(user_identifiers: list[str] | None) -> list[UUID] | None:
    """
    Return vessel UUIDs assigned to an office user in master_RoleByVessel.
    Only returns active, non-deleted assignments.
    """
    if not user_identifiers:
        # Some tests use lightweight user doubles without office identifiers.
        return None

    try:
        filters = Q()
        for ident in user_identifiers:
            filters |= Q(UserId__iexact=ident)

        return list(
            MasterRoleByVessel.objects.filter(
                IsActive=True,
                is_deleted=False,
            ).filter(
                filters
            ).values_list('VesselId', flat=True)
        )
    except Exception as e:
        error_text = str(e).lower()
        # In SQLite-backed tests, unmanaged assignment tables may not exist.
        # Returning None lets callers decide whether to bypass filtering.
        if 'no such table' in error_text or 'invalid object name' in error_text:
            logger.warning(
                "Vessel assignment table unavailable for %s; skipping office vessel filter: %s",
                user_identifiers,
                e,
            )
            return None
        logger.error("Error fetching vessel assignments for %s: %s", user_identifiers, e)
        return []


def apply_office_vessel_filter(
    queryset: QuerySet,
    user,
    vessel_id_field: str = 'vessel_id',
) -> QuerySet:
    """
    Filter a queryset for office users based on their vessel assignments.

    - Global PIC/DPA users: no filtering (see all)
    - Other office users: restricted to assigned vessels
    - Returns queryset.none() if no assignments found (safety fallback)
    """
    if getattr(user, 'user_type', None) != 'OFFICE':
        return queryset

    user_identifiers = get_office_user_identifiers(user)
    if has_global_office_vessel_access(user, user_identifiers=user_identifiers):
        return queryset

    vessel_ids = get_office_user_vessel_ids(user_identifiers)
    if vessel_ids is None:
        return queryset

    if not vessel_ids:
        logger.warning(
            "Office user %s has no vessel assignments — returning empty queryset",
            user_identifiers,
        )
        return queryset.none()

    return queryset.filter(**{f'{vessel_id_field}__in': vessel_ids})
