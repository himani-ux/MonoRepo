"""
DefIntel access rules shared across import/checklist/prediction views.
"""

from apps.accounts.models import RoleCodes

from .workflow import RANK_2E, RANK_CE, RANK_CO, RANK_MASTER, classify_rank

ALLOWED_VESSEL_RANK_CATEGORIES = {
    RANK_MASTER,
    RANK_CO,
    RANK_CE,
    RANK_2E,
}


def is_office_user(user) -> bool:
    return getattr(user, 'user_type', None) == 'OFFICE'


def has_allowed_defintel_vessel_rank(user) -> bool:
    if getattr(user, 'user_type', None) != 'VESSEL':
        return False

    if getattr(user, 'role', None) == RoleCodes.VESSEL_MASTER:
        return True

    rank_category = classify_rank(getattr(user, 'rank', None))
    return rank_category in ALLOWED_VESSEL_RANK_CATEGORIES


def can_access_defintel_reports(user) -> bool:
    return is_office_user(user) or has_allowed_defintel_vessel_rank(user)


def can_import_opensource(user) -> bool:
    return is_office_user(user)
