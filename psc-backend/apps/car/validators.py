"""
Shared CAR submission validators.

Single source of truth for all content/evidence validation checks
used by both the legacy submit endpoint and the unified workflow endpoint.
"""

from .models import ActionType, EvidenceType

ROOT_CAUSE_MIN_LENGTH = 50
ACTION_DESCRIPTION_MIN_FOR_SUBMIT = 50


def validate_car_submission(car):
    """
    Validate all preconditions for CAR submission.

    Returns dict of field-keyed errors. Empty dict = valid.
    """
    errors = {}

    # 1. Root cause >= 50 trimmed chars
    if not car.root_cause_summary or len(car.root_cause_summary.strip()) < ROOT_CAUSE_MIN_LENGTH:
        errors['root_cause_summary'] = 'Root cause summary must be at least 50 characters.'

    # 2. CLC code or custom cause
    clc_mappings = car.clc_mappings.all()
    has_clc = clc_mappings.filter(clc_item_id__isnull=False).exists()
    has_custom = (
        clc_mappings.exclude(custom_cause_text__isnull=True)
        .exclude(custom_cause_text__exact='')
        .exists()
    )
    if not (has_clc or has_custom):
        errors['clc_item_ids'] = 'At least one CLC code or custom cause is required.'

    # 3. Action counts
    actions_qs = car.corrective_actions.filter(is_deleted=False)
    immediate_qs = actions_qs.filter(action_type=ActionType.IMMEDIATE)
    long_term_qs = actions_qs.filter(action_type=ActionType.LONG_TERM)
    immediate_count = immediate_qs.count()
    long_term_count = long_term_qs.count()

    action_errors = []
    if immediate_count < 1:
        action_errors.append('At least 1 immediate corrective action is required.')
    if long_term_count < 1:
        action_errors.append('At least 1 long-term corrective action is required.')
    if action_errors:
        errors['corrective_actions'] = ' '.join(action_errors)

    # 4. At least one action per category with description >= 50 trimmed chars
    desc_errors = []
    if immediate_count >= 1:
        has_substantive = any(
            len((a.description or '').strip()) >= ACTION_DESCRIPTION_MIN_FOR_SUBMIT
            for a in immediate_qs
        )
        if not has_substantive:
            desc_errors.append(
                f'At least one immediate action must have a description of '
                f'{ACTION_DESCRIPTION_MIN_FOR_SUBMIT}+ characters.'
            )
    if long_term_count >= 1:
        has_substantive = any(
            len((a.description or '').strip()) >= ACTION_DESCRIPTION_MIN_FOR_SUBMIT
            for a in long_term_qs
        )
        if not has_substantive:
            desc_errors.append(
                f'At least one long-term action must have a description of '
                f'{ACTION_DESCRIPTION_MIN_FOR_SUBMIT}+ characters.'
            )
    if desc_errors:
        errors['action_descriptions'] = ' '.join(desc_errors)

    # 5. BEFORE evidence
    evidence_qs = car.evidence.filter(is_deleted=False)
    if not evidence_qs.filter(evidence_type=EvidenceType.BEFORE).exists():
        errors['evidence_before'] = 'At least 1 BEFORE evidence is required.'

    # 6. AFTER evidence
    if not evidence_qs.filter(evidence_type=EvidenceType.AFTER).exists():
        errors['evidence_after'] = 'At least 1 AFTER evidence is required.'

    return errors
