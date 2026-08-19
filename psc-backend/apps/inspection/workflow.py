"""
Unified CAR workflow — state machine, transitions, and permission checks.

The CAR.status field is the single source of truth for workflow state.
DEF.def_status is deprecated.

State machine: 9 statuses, 12 named transitions, role-based permissions.
"""

import logging
from typing import Optional

from django.db.models import Q

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
    DRAFT_FOR_VESSEL = 'DRAFT_FOR_VESSEL'
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
    SUBMIT_TO_LEAD_AUDITOR = 'SUBMIT_TO_LEAD_AUDITOR'
    LEAD_AUDITOR_CLOSE = 'LEAD_AUDITOR_CLOSE'
    AWAIT_EXTERNAL_CLOSE_OUT = 'AWAIT_EXTERNAL_CLOSE_OUT'
    CONFIRM_EXTERNAL_CLOSE = 'CONFIRM_EXTERNAL_CLOSE'


# Human-readable labels for each action
ACTION_LABELS = {
    WorkflowAction.START_WORK: 'Start Work',
    WorkflowAction.DRAFT_FOR_VESSEL: 'Draft for Vessel',
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
    WorkflowAction.SUBMIT_TO_LEAD_AUDITOR: 'Submit to Lead Auditor',
    WorkflowAction.LEAD_AUDITOR_CLOSE: 'Lead Auditor Close',
    WorkflowAction.AWAIT_EXTERNAL_CLOSE_OUT: 'Await External Close Out',
    WorkflowAction.CONFIRM_EXTERNAL_CLOSE: 'Confirm External Closure',
}


# ============================================================================
# Transition Table
# ============================================================================

# Each transition: (current_status, action) -> dict
# allowed_roles: list of role types that can perform the action
#   'owner' = assigned crew member, 'reviewer' = CE/reviewer, 'master',
#   'pic', 'dpa', 'lead_auditor'
# comment_required: whether a comment is mandatory
AUDIT_INTERNAL_NC_SCOPE = 'audit_internal_nc'
AUDIT_EXTERNAL_NC_SCOPE = 'audit_external_nc'

TRANSITIONS = {
    # Vessel-side: owner starts work
    (CARStatus.DRAFT, WorkflowAction.START_WORK): {
        'target': CARStatus.IN_PROGRESS,
        'allowed_roles': ['owner', 'master'],
        'comment_required': False,
    },
    # Vessel-side: owner starts work
    (CARStatus.ALLOTTED, WorkflowAction.START_WORK): {
        'target': CARStatus.IN_PROGRESS,
        'allowed_roles': ['owner', 'master'],
        'comment_required': False,
    },
    # Audit office-led drafting sub-state
    (CARStatus.ALLOTTED, WorkflowAction.DRAFT_FOR_VESSEL): {
        'target': CARStatus.OFFICE_DRAFTED,
        'allowed_roles': ['pic'],
        'comment_required': False,
        'audit_scope': AUDIT_INTERNAL_NC_SCOPE,
    },
    (CARStatus.DRAFT, WorkflowAction.DRAFT_FOR_VESSEL): {
        'target': CARStatus.OFFICE_DRAFTED,
        'allowed_roles': ['pic'],
        'comment_required': False,
        'audit_scope': AUDIT_INTERNAL_NC_SCOPE,
    },
    (CARStatus.IN_PROGRESS, WorkflowAction.DRAFT_FOR_VESSEL): {
        'target': CARStatus.OFFICE_DRAFTED,
        'allowed_roles': ['pic'],
        'comment_required': False,
        'audit_scope': AUDIT_INTERNAL_NC_SCOPE,
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
    # Master accepts an office-drafted Audit NC and submits it to the PIC pool.
    (CARStatus.OFFICE_DRAFTED, WorkflowAction.SUBMIT_TO_PIC): {
        'target': CARStatus.SUBMITTED_TO_PIC,
        'allowed_roles': ['master'],
        'comment_required': False,
        'audit_scope': AUDIT_INTERNAL_NC_SCOPE,
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
        'comment_required': False,
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
    # Internal Audit NC: PIC submits to the Lead Auditor, not the DPA.
    (CARStatus.PIC_REVIEW, WorkflowAction.SUBMIT_TO_LEAD_AUDITOR): {
        'target': CARStatus.SUBMITTED_TO_LEAD_AUDITOR,
        'allowed_roles': ['pic'],
        'comment_required': True,
        'audit_scope': AUDIT_INTERNAL_NC_SCOPE,
    },
    # External Audit NC: PIC waits for the external auditor close-out letter.
    (CARStatus.PIC_REVIEW, WorkflowAction.AWAIT_EXTERNAL_CLOSE_OUT): {
        'target': CARStatus.AWAITING_EXTERNAL_CLOSE_OUT,
        'allowed_roles': ['pic'],
        'comment_required': True,
        'audit_scope': AUDIT_EXTERNAL_NC_SCOPE,
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
    # Internal Audit NC terminal state is held by the Lead Auditor of record.
    (CARStatus.SUBMITTED_TO_LEAD_AUDITOR, WorkflowAction.LEAD_AUDITOR_CLOSE): {
        'target': CARStatus.LEAD_AUDITOR_CLOSED,
        'allowed_roles': ['lead_auditor'],
        'comment_required': True,
        'audit_scope': AUDIT_INTERNAL_NC_SCOPE,
    },
    (CARStatus.SUBMITTED_TO_LEAD_AUDITOR, WorkflowAction.REQUEST_REWORK): {
        'target': CARStatus.PENDING_MASTER_REVIEW,
        'allowed_roles': ['lead_auditor'],
        'comment_required': True,
        'audit_scope': AUDIT_INTERNAL_NC_SCOPE,
    },
    # External Audit NC terminal state is DPA confirmation after close-out letter.
    (CARStatus.AWAITING_EXTERNAL_CLOSE_OUT, WorkflowAction.CONFIRM_EXTERNAL_CLOSE): {
        'target': CARStatus.EXTERNAL_AUDITOR_CLOSED,
        'allowed_roles': ['dpa'],
        'comment_required': True,
        'audit_scope': AUDIT_EXTERNAL_NC_SCOPE,
    },
    (CARStatus.AWAITING_EXTERNAL_CLOSE_OUT, WorkflowAction.REQUEST_REWORK): {
        'target': CARStatus.PENDING_MASTER_REVIEW,
        'allowed_roles': ['dpa'],
        'comment_required': True,
        'audit_scope': AUDIT_EXTERNAL_NC_SCOPE,
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
# Audit Context
# ============================================================================

def _compact_uuid_text(value) -> str:
    """Return UUID-like values in 32-character form for loose legacy refs."""
    if value is None:
        return ''
    return str(value).strip().replace('-', '').lower()


def _get_audit_workflow_context(deficiency):
    """Return (finding, audit_detail) for an Audit CAR, or None for PSC rows."""
    if not deficiency:
        return None

    inspection = getattr(deficiency, 'inspection', None)
    if getattr(inspection, 'inspection_type', None) != 'AUDIT':
        return None

    try:
        from apps.inspection.audit.models import AuditDetail, AuditFinding

        finding = AuditFinding.all_objects.filter(
            psc_deficiency_id=_compact_uuid_text(deficiency.id),
            is_deleted=False,
        ).first()
        if not finding:
            return None

        audit_detail = AuditDetail.objects.filter(id=finding.audit_detail_id).first()
        if not audit_detail:
            return None
        return finding, audit_detail
    except Exception:
        logger.exception(
            "Failed to resolve Audit workflow context",
            extra={'deficiency_id': str(getattr(deficiency, 'id', ''))},
        )
        return None


def _audit_scope_for_context(audit_context):
    if not audit_context:
        return None
    finding, audit_detail = audit_context
    if finding.finding_type != 'NC':
        return 'audit_non_nc'
    if finding.is_external or audit_detail.audit_classification == 'EXTERNAL':
        return AUDIT_EXTERNAL_NC_SCOPE
    return AUDIT_INTERNAL_NC_SCOPE


def _transition_scope_error(car, action, transition, audit_context):
    """Prevent Audit NCs from falling through to PSC terminal transitions."""
    audit_scope = _audit_scope_for_context(audit_context)
    required_scope = transition.get('audit_scope')

    if required_scope and audit_scope != required_scope:
        if audit_scope == 'audit_non_nc':
            return 'Audit CAR workflow transitions are only valid for NC findings; Observations use their own closure state.'
        return f'Action "{action}" is not valid for this Audit finding.'

    if audit_scope in (AUDIT_INTERNAL_NC_SCOPE, AUDIT_EXTERNAL_NC_SCOPE):
        if action == WorkflowAction.SUBMIT_TO_DPA and car.status == CARStatus.PIC_REVIEW:
            return 'Audit NCs do not use the PSC SUBMITTED_TO_DPA path.'
        if action == WorkflowAction.CLOSE_CAR and car.status == CARStatus.SUBMITTED_TO_DPA:
            return 'Audit NCs do not use the PSC CLOSED terminal state.'

    return None


def _has_audit_signature(finding, *event_types):
    try:
        from apps.inspection.audit.models import AuditFindingSignature

        return AuditFindingSignature.objects.filter(
            audit_finding_id=finding.id,
            signature_event_type__in=event_types,
            signed_at__isnull=False,
        ).exists()
    except Exception:
        logger.exception(
            "Failed to check Audit finding signature",
            extra={'finding_id': str(getattr(finding, 'id', ''))},
        )
        return False


def _get_nc_record(finding):
    try:
        from apps.inspection.audit.models import AuditFindingNC

        return AuditFindingNC.objects.filter(audit_finding_id=finding.id).first()
    except Exception:
        logger.exception(
            "Failed to resolve Audit NC record",
            extra={'finding_id': str(getattr(finding, 'id', ''))},
        )
        return None


def _has_external_close_out_letter(finding, audit_detail):
    try:
        from apps.inspection.audit.models import AuditAttachment

        return AuditAttachment.objects.filter(
            audit_detail_id=audit_detail.id,
            category='EXTERNAL_CLOSE_OUT_LETTER',
            is_deleted=False,
        ).filter(
            Q(audit_finding_id=finding.id) | Q(audit_finding_id__isnull=True)
        ).exists()
    except Exception:
        logger.exception(
            "Failed to check external close-out letter",
            extra={'finding_id': str(getattr(finding, 'id', ''))},
        )
        return False


def _audit_gate_error(car, action, transition, audit_context):
    """Audit-specific signature/attachment gates enforced inside the shared engine."""
    if not audit_context:
        return None

    finding, audit_detail = audit_context
    audit_scope = _audit_scope_for_context(audit_context)
    if audit_scope == 'audit_non_nc':
        return 'Audit CAR workflow transitions are only valid for NC findings; Observations use their own closure state.'

    nc_record = _get_nc_record(finding)

    if (
        audit_scope == AUDIT_INTERNAL_NC_SCOPE
        and action in (WorkflowAction.MARK_COMPLETED, WorkflowAction.SUBMIT_TO_PIC)
        and car.status in (CARStatus.IN_PROGRESS, CARStatus.OFFICE_DRAFTED)
    ):
        has_master_signature = (
            bool(getattr(nc_record, 'master_immediate_sign_at', None))
            or _has_audit_signature(finding, 'MASTER_ACK')
        )
        if not has_master_signature:
            return 'Signature missing for Part B/C.'

    if audit_scope == AUDIT_INTERNAL_NC_SCOPE and action == WorkflowAction.SUBMIT_TO_LEAD_AUDITOR:
        if not _has_audit_signature(finding, 'SUPT_SIGN'):
            return 'Signature missing for Part C/D.'

    if audit_scope == AUDIT_INTERNAL_NC_SCOPE and action == WorkflowAction.LEAD_AUDITOR_CLOSE:
        has_acceptance_signature = (
            bool(getattr(nc_record, 'acceptance_signer_at', None))
            or _has_audit_signature(finding, 'LEAD_AUDITOR_CLOSE')
        )
        if not has_acceptance_signature:
            return 'Signature missing for Part F.'
        if getattr(nc_record, 'acceptance_decision', None) and nc_record.acceptance_decision != 'ACCEPTED':
            return 'Part F must be ACCEPTED before Lead Auditor closure.'

    if audit_scope == AUDIT_EXTERNAL_NC_SCOPE and action == WorkflowAction.CONFIRM_EXTERNAL_CLOSE:
        if not _has_external_close_out_letter(finding, audit_detail):
            return 'External close-out letter is required before external closure.'

    return None


def _audit_permission_error(user, action, audit_context):
    """Enforce Audit process gates inside the shared CAR engine for Audit-linked CARs."""
    if not audit_context:
        return None
    _finding, audit_detail = audit_context
    try:
        from apps.inspection.audit.permissions import (
            AUDIT_CAR_WORKFLOW_ACTION_GATES,
            audit_effective_process_ids_for_user,
        )

        action_key = str(action or "").strip().upper()
        if action_key not in AUDIT_CAR_WORKFLOW_ACTION_GATES:
            return None
        required_process_ids = AUDIT_CAR_WORKFLOW_ACTION_GATES[action_key]
        effective_process_ids = audit_effective_process_ids_for_user(user, audit_detail)
    except Exception:
        logger.exception("Failed to resolve Audit CAR workflow permissions")
        return 'Audit CAR workflow permission check failed.'

    if any(process_id in effective_process_ids for process_id in required_process_ids):
        return None
    return 'You do not have permission to perform this Audit CAR workflow action.'


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
    user_id = getattr(user, 'id', None)

    audit_context = _get_audit_workflow_context(deficiency)
    if audit_context:
        _finding, audit_detail = audit_context
        lead_auditor_user_id = audit_detail.lead_auditor_user_id
        if _workflow_user_matches(user, lead_auditor_user_id):
            roles.add('lead_auditor')
        if _workflow_user_matches(user, audit_detail.conductor_user_id):
            roles.add('pic')

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


def _workflow_user_matches(user, target_user_id) -> bool:
    if not target_user_id:
        return False
    for attr_name in ("id", "user_id", "employee_id", "login_id", "username", "crew_id"):
        value = getattr(user, attr_name, None)
        if value and (str(value) == str(target_user_id) or _uuid_match(value, target_user_id)):
            return True
    return False


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

    deficiency = getattr(car, 'deficiency', None)
    audit_inspection = (
        deficiency is not None
        and getattr(getattr(deficiency, 'inspection', None), 'inspection_type', None) == 'AUDIT'
    )
    audit_context = _get_audit_workflow_context(deficiency)
    if audit_inspection and not audit_context:
        return None, 'Audit CAR workflow requires an audit_finding extension row.'

    scope_error = _transition_scope_error(car, action, transition, audit_context)
    if scope_error:
        return None, scope_error

    gate_error = _audit_gate_error(car, action, transition, audit_context)
    if gate_error:
        return None, gate_error

    permission_error = _audit_permission_error(user, action, audit_context)
    if permission_error:
        return None, permission_error

    # Resolve user roles
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
    audit_context = _get_audit_workflow_context(deficiency)
    user_roles = _get_user_workflow_roles(user, deficiency)

    available = []
    for (status, action), transition in TRANSITIONS.items():
        if status != car.status:
            continue
        if _transition_scope_error(car, action, transition, audit_context):
            continue
        if _audit_permission_error(user, action, audit_context):
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
    if car.status in (CARStatus.DRAFT, CARStatus.ALLOTTED):
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
