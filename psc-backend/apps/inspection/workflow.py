"""
Unified CAR workflow — state machine, transitions, and permission checks.

The CAR.status field is the single source of truth for workflow state.
DEF.def_status is deprecated.

State machine: 9 statuses, 12 named transitions, role-based permissions.
"""

import logging
from typing import Optional

from .deficiency_models import CARStatus

logger = logging.getLogger(__name__)

# ============================================================================
# Rank Classification
# ============================================================================

RANK_MASTER = 'MASTER'
RANK_CE = 'CE'
RANK_CO = 'CO'
RANK_2E = '2E'
RANK_OTHER = 'OTHER'


def classify_rank(rank_name: Optional[str]) -> str:
    """
    Classify a rank string into a workflow category.

    CE and CO both map to VESSEL_MASTER role, so we must use rank_name
    string matching instead of role codes.

    Returns one of: MASTER, CE, CO, 2E, OTHER
    """
    if not rank_name:
        return RANK_OTHER

    rank_lower = rank_name.lower().strip()

    if any(kw in rank_lower for kw in ['master', 'captain']):
        return RANK_MASTER

    if any(kw in rank_lower for kw in ['chief engineer', 'c/e']):
        return RANK_CE

    if any(kw in rank_lower for kw in ['chief officer', 'chief mate', 'c/o']):
        return RANK_CO

    if any(kw in rank_lower for kw in ['second engineer', '2nd engineer', '2/e']):
        return RANK_2E

    return RANK_OTHER


# ============================================================================
# Reviewer Routing
# ============================================================================

def determine_reviewer(owner_rank_name: Optional[str], vessel_id: str):
    """
    Determine the reviewer for a deficiency based on the owner's rank.

    Routing rules:
    - 2E owner -> CE reviewer
    - CE owner -> Master reviewer
    - CO owner -> Master reviewer
    - Master/Other -> None (no reviewer needed)

    Returns (reviewer_crew, reviewer_rank_category) or (None, None)
    """
    from apps.accounts.models import HRM501
    from django.db import connection

    rank_cat = classify_rank(owner_rank_name)

    if rank_cat == RANK_2E:
        target_ranks = ['chief engineer', 'c/e']
    elif rank_cat in (RANK_CE, RANK_CO):
        target_ranks = ['master', 'captain']
    elif rank_cat == RANK_OTHER:
        # Other ranks (Able Seaman, etc.) route to Master for review
        target_ranks = ['master', 'captain']
    else:
        return None, None

    uid = _normalize_uuid(vessel_id)
    rows = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT h.id, COALESCE(r.rank_name, h.rank_name) AS rank_name
                FROM HRM501 h
                INNER JOIN Crew_Onboarding_History coh
                    ON coh.CrewID = h.CrewID
                LEFT JOIN master_applied_rank r
                    ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
                WHERE TRY_CONVERT(uniqueidentifier, coh.Vessel) = CAST(%s AS uniqueidentifier)
                  AND coh.SignOffDate IS NULL
                  AND ISNULL(coh.is_active, 1) = 1
                  AND ISNULL(coh.is_deleted, 0) = 0
                  AND ISNULL(h.is_active, 1) = 1
                  AND h.is_deleted = 0
                """,
                [uid],
            )
            rows = cursor.fetchall()
    except Exception as e:
        logger.error(f"Reviewer lookup failed for vessel {vessel_id}: {e}")
        rows = []

    for crew_id, rank_name in rows:
        if rank_name and any(kw in rank_name.lower() for kw in target_ranks):
            reviewer = HRM501.objects.extra(
                where=["id = CAST(%s AS uniqueidentifier)", "is_deleted = 0"],
                params=[str(crew_id)],
            ).first()
            if reviewer:
                return reviewer, classify_rank(rank_name)

    return None, None


# ============================================================================
# Workflow Actions (named transitions)
# ============================================================================

class WorkflowAction:
    """Named workflow actions for the unified CAR state machine."""
    START_WORK = 'START_WORK'
    MARK_COMPLETED = 'MARK_COMPLETED'
    SUBMIT_FOR_CE_REVIEW = 'SUBMIT_FOR_CE_REVIEW'
    SUBMIT_FOR_MASTER_REVIEW = 'SUBMIT_FOR_MASTER_REVIEW'
    APPROVE_AND_FORWARD = 'APPROVE_AND_FORWARD'
    RETURN_FOR_REWORK = 'RETURN_FOR_REWORK'
    SUBMIT_TO_PIC = 'SUBMIT_TO_PIC'
    START_PIC_REVIEW = 'START_PIC_REVIEW'
    SUBMIT_TO_DPA = 'SUBMIT_TO_DPA'
    CLOSE_CAR = 'CLOSE_CAR'
    REOPEN_CAR = 'REOPEN_CAR'
    REQUEST_REWORK = 'REQUEST_REWORK'


# Human-readable labels for each action
ACTION_LABELS = {
    WorkflowAction.START_WORK: 'Start Work',
    WorkflowAction.MARK_COMPLETED: 'Mark Completed',
    WorkflowAction.SUBMIT_FOR_CE_REVIEW: 'Submit for CE Review',
    WorkflowAction.SUBMIT_FOR_MASTER_REVIEW: 'Submit for Master Review',
    WorkflowAction.APPROVE_AND_FORWARD: 'Approve & Forward',
    WorkflowAction.RETURN_FOR_REWORK: 'Return for Rework',
    WorkflowAction.SUBMIT_TO_PIC: 'Submit to PIC',
    WorkflowAction.START_PIC_REVIEW: 'Start Review',
    WorkflowAction.SUBMIT_TO_DPA: 'Submit to DPA',
    WorkflowAction.CLOSE_CAR: 'Close CAR',
    WorkflowAction.REOPEN_CAR: 'Reopen CAR',
    WorkflowAction.REQUEST_REWORK: 'Request Rework',
}


# ============================================================================
# Transition Table
# ============================================================================

# Each transition: (current_status, action) -> dict
# allowed_roles: list of role types that can perform the action
#   'owner' = assigned crew member, 'reviewer' = CE/reviewer, 'master', 'pic', 'dpa'
# comment_required: whether a comment is mandatory
TRANSITIONS = {
    # Vessel-side: owner starts work
    (CARStatus.ALLOTTED, WorkflowAction.START_WORK): {
        'target': CARStatus.IN_PROGRESS,
        'allowed_roles': ['owner', 'master'],
        'comment_required': False,
    },
    # Owner marks work completed
    (CARStatus.IN_PROGRESS, WorkflowAction.MARK_COMPLETED): {
        'target': CARStatus.PENDING_CE_REVIEW,
        'allowed_roles': ['owner', 'master'],
        'comment_required': False,
    },
    # CE reviews and approves
    (CARStatus.PENDING_CE_REVIEW, WorkflowAction.APPROVE_AND_FORWARD): {
        'target': CARStatus.PENDING_MASTER_REVIEW,
        'allowed_roles': ['reviewer', 'master'],
        'comment_required': False,
    },
    # CE returns for rework
    (CARStatus.PENDING_CE_REVIEW, WorkflowAction.RETURN_FOR_REWORK): {
        'target': CARStatus.IN_PROGRESS,
        'allowed_roles': ['reviewer', 'master'],
        'comment_required': True,
    },
    # Master reviews and submits to PIC
    (CARStatus.PENDING_MASTER_REVIEW, WorkflowAction.SUBMIT_TO_PIC): {
        'target': CARStatus.SUBMITTED_TO_PIC,
        'allowed_roles': ['master'],
        'comment_required': False,
    },
    # Master returns for rework
    (CARStatus.PENDING_MASTER_REVIEW, WorkflowAction.RETURN_FOR_REWORK): {
        'target': CARStatus.IN_PROGRESS,
        'allowed_roles': ['master'],
        'comment_required': True,
    },
    # PIC starts review (accepts submission)
    (CARStatus.SUBMITTED_TO_PIC, WorkflowAction.START_PIC_REVIEW): {
        'target': CARStatus.PIC_REVIEW,
        'allowed_roles': ['pic'],
        'comment_required': True,
    },
    # PIC requests rework
    (CARStatus.SUBMITTED_TO_PIC, WorkflowAction.REQUEST_REWORK): {
        'target': CARStatus.PENDING_MASTER_REVIEW,
        'allowed_roles': ['pic'],
        'comment_required': True,
    },
    # PIC submits to DPA
    (CARStatus.PIC_REVIEW, WorkflowAction.SUBMIT_TO_DPA): {
        'target': CARStatus.SUBMITTED_TO_DPA,
        'allowed_roles': ['pic'],
        'comment_required': True,
    },
    # PIC requests rework from PIC_REVIEW
    (CARStatus.PIC_REVIEW, WorkflowAction.REQUEST_REWORK): {
        'target': CARStatus.PENDING_MASTER_REVIEW,
        'allowed_roles': ['pic'],
        'comment_required': True,
    },
    # DPA closes CAR
    (CARStatus.SUBMITTED_TO_DPA, WorkflowAction.CLOSE_CAR): {
        'target': CARStatus.CLOSED,
        'allowed_roles': ['dpa'],
        'comment_required': True,
    },
    # DPA requests rework from SUBMITTED_TO_DPA
    (CARStatus.SUBMITTED_TO_DPA, WorkflowAction.REQUEST_REWORK): {
        'target': CARStatus.PENDING_MASTER_REVIEW,
        'allowed_roles': ['dpa'],
        'comment_required': True,
    },
    # DPA reopens closed CAR
    (CARStatus.CLOSED, WorkflowAction.REOPEN_CAR): {
        'target': CARStatus.PENDING_MASTER_REVIEW,
        'allowed_roles': ['dpa'],
        'comment_required': True,
    },
}


# ============================================================================
# Role Resolution
# ============================================================================

def _get_user_workflow_roles(user, deficiency=None):
    """
    Get the set of workflow role strings for a user.

    Returns a set like {'owner', 'master'} or {'pic'} etc.
    """
    from apps.accounts.models import RoleCodes

    roles = set()
    user_type = getattr(user, 'user_type', '')

    if user_type == 'OFFICE':
        role = getattr(user, 'role', '')
        if role in (RoleCodes.OFFICE_PIC, RoleCodes.OFFICE_SSQE, RoleCodes.OFFICE_SUPT):
            roles.add('pic')
        if role == RoleCodes.DPA:
            roles.add('dpa')
        return roles

    # Vessel user
    rank_cat = classify_rank(getattr(user, 'rank', None))
    user_crew_id = getattr(user, 'crew_id', None)
    user_id = getattr(user, 'id', None)

    if rank_cat == RANK_MASTER:
        roles.add('master')

    if deficiency:
        if deficiency.assigned_crew_id:
            if user_crew_id and str(deficiency.assigned_crew_id) == str(user_crew_id):
                roles.add('owner')
            elif _uuid_match(user_id, deficiency.assigned_crew_id):
                roles.add('owner')
        # reviewer_crew_id may be stored as either UUID or CrewID in mixed/legacy data.
        if deficiency.reviewer_crew_id:
            if user_crew_id and str(deficiency.reviewer_crew_id) == str(user_crew_id):
                roles.add('reviewer')
            elif _uuid_match(user_id, deficiency.reviewer_crew_id):
                roles.add('reviewer')

    return roles


# ============================================================================
# Core Validation
# ============================================================================

def validate_workflow_transition(car, action, user, comment=None):
    """
    Validate a named workflow transition is allowed.

    Returns (transition_info, error_message).
    transition_info is the TRANSITIONS dict entry if valid, None otherwise.
    """
    key = (car.status, action)
    transition = TRANSITIONS.get(key)

    # Idempotent START_WORK guard:
    # if client is stale and CAR already moved to IN_PROGRESS, treat as success.
    if not transition and action == WorkflowAction.START_WORK and car.status == CARStatus.IN_PROGRESS:
        transition = {
            'target': CARStatus.IN_PROGRESS,
            'allowed_roles': ['owner', 'master'],
            'comment_required': False,
        }
    # Idempotent MARK_COMPLETED guard:
    # stale/duplicate client calls after completion should not fail with 400.
    if (
        not transition
        and action == WorkflowAction.MARK_COMPLETED
        and car.status in (CARStatus.PENDING_CE_REVIEW, CARStatus.PENDING_MASTER_REVIEW)
    ):
        transition = {
            'target': car.status,
            'allowed_roles': ['owner', 'master'],
            'comment_required': False,
        }

    if not transition:
        return None, f'Action "{action}" is not allowed when CAR is in "{car.status}" status.'

    # Check comment requirement
    if transition['comment_required'] and not (comment and comment.strip()):
        return None, f'A comment is required for the "{ACTION_LABELS.get(action, action)}" action.'

    # Resolve user roles
    deficiency = getattr(car, 'deficiency', None)
    user_roles = _get_user_workflow_roles(user, deficiency)

    # Check if user has at least one allowed role
    allowed = set(transition['allowed_roles'])
    if not user_roles & allowed:
        return None, f'You do not have permission to perform "{ACTION_LABELS.get(action, action)}".'

    # Dynamic routing for vessel-side completion:
    # CE/CO owned CARs skip CE review and move directly to Master review.
    if action == WorkflowAction.MARK_COMPLETED and deficiency:
        owner_rank = getattr(deficiency, 'owner_rank', None)
        # Fallback for legacy rows where owner metadata was not denormalized.
        if not owner_rank and 'owner' in user_roles:
            owner_rank = getattr(user, 'rank', None)
        owner_rank_cat = classify_rank(owner_rank)
        if owner_rank_cat in (RANK_CE, RANK_CO):
            transition = {**transition, 'target': CARStatus.PENDING_MASTER_REVIEW}

    return transition, None


def get_available_actions(car, user):
    """
    Get list of available workflow actions for the given user on this CAR.

    Returns list of dicts: [{action, label, comment_required}, ...]
    """
    deficiency = getattr(car, 'deficiency', None)
    user_roles = _get_user_workflow_roles(user, deficiency)

    available = []
    for (status, action), transition in TRANSITIONS.items():
        if status != car.status:
            continue
        allowed = set(transition['allowed_roles'])
        if user_roles & allowed:
            available.append({
                'action': action,
                'label': ACTION_LABELS.get(action, action),
                'comment_required': transition['comment_required'],
            })

    return available


def auto_start_if_allotted(car):
    """
    Auto-transition ALLOTTED -> IN_PROGRESS when CAR content is edited.
    Returns True if transition happened.
    """
    if car.status == CARStatus.ALLOTTED:
        car.status = CARStatus.IN_PROGRESS
        car.save(update_fields=['status'])
        return True
    return False


# ============================================================================
# Legacy DEF Workflow (kept for backward compatibility)
# ============================================================================

from .deficiency_models import DefStatus  # noqa: E402

# Old DEF transitions — kept for DeficiencyWorkflowTransitionView
VALID_TRANSITIONS = {
    DefStatus.ALLOCATED: {
        DefStatus.IN_PROGRESS: 'owner',
    },
    DefStatus.IN_PROGRESS: {
        DefStatus.COMPLETED: 'owner',
    },
    DefStatus.COMPLETED: {
        DefStatus.UNDER_REVIEW: 'reviewer',
    },
    DefStatus.UNDER_REVIEW: {
        DefStatus.APPROVED: 'reviewer',
        DefStatus.IN_PROGRESS: 'reviewer',
    },
    DefStatus.APPROVED: {
        DefStatus.SUBMITTED: 'master',
    },
}


def validate_transition(current_status, target_status, user, deficiency):
    """
    Legacy: Validate a DEF workflow transition.
    Returns (is_valid, error_message).
    """
    allowed = VALID_TRANSITIONS.get(current_status, {})
    if target_status not in allowed:
        return False, f'Transition from {current_status} to {target_status} is not allowed.'

    required_actor = allowed[target_status]
    user_rank = classify_rank(getattr(user, 'rank', None))

    if required_actor == 'owner':
        user_crew_id = getattr(user, 'crew_id', None)
        if not (
            (user_crew_id and str(deficiency.assigned_crew_id) == str(user_crew_id)) or
            _uuid_match(getattr(user, 'id', None), deficiency.assigned_crew_id)
        ):
            if user_rank != RANK_MASTER:
                return False, 'Only the assigned crew member or Master can perform this action.'

    elif required_actor == 'reviewer':
        is_reviewer = deficiency.reviewer_crew_id and _uuid_match(
            getattr(user, 'id', None),
            deficiency.reviewer_crew_id,
        )
        if not is_reviewer and user_rank != RANK_MASTER:
            return False, 'Only the reviewer or Master can perform this action.'

    elif required_actor == 'master':
        if user_rank != RANK_MASTER:
            return False, 'Only the Master can perform this action.'

    return True, None


# ============================================================================
# UUID Helpers
# ============================================================================

def _normalize_uuid(value) -> str:
    """Normalize a UUID to hyphenated format."""
    if value is None:
        return ''
    s = str(value).replace('-', '').lower()
    if len(s) == 32:
        return f'{s[:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:]}'
    return str(value).lower()


def _uuid_match(a, b) -> bool:
    """Compare two UUIDs ignoring format differences."""
    if a is None or b is None:
        return False
    return _normalize_uuid(a) == _normalize_uuid(b)
