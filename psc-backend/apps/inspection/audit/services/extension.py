"""OPM F 713 audit-plan extension workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import MasterAuditPlan
from apps.inspection.audit.services.audit_window import add_months
from apps.inspection.audit.services.plan_persistence import save_plan_update


MIN_EXTENSION_REASON_LENGTH = 50
EXTENSION_REF_PREFIX = "OPM-F-713"


class AuditPlanWorkflowError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__(str(errors))


@dataclass(frozen=True)
class ExtensionDecisionResult:
    plan: MasterAuditPlan
    approved: bool


def request_plan_extension(
    plan: MasterAuditPlan,
    *,
    reason: str,
    proposed_new_target_date: date,
    actor: str,
) -> MasterAuditPlan:
    reason = _clean_text(reason)
    if len(reason) < MIN_EXTENSION_REASON_LENGTH:
        raise AuditPlanWorkflowError(
            {"extension_requested_reason": "Extension reason must be at least 50 characters."}
        )
    if plan.status == "CANCELLED":
        raise AuditPlanWorkflowError({"status": "Cancelled plan entries are read-only."})
    if plan.planned_window_end is None:
        raise AuditPlanWorkflowError({"planned_window_end": "Plan window end is required before extension."})
    max_extension_date = add_months(plan.planned_window_end, 3)
    if proposed_new_target_date > max_extension_date:
        raise AuditPlanWorkflowError(
            {"proposed_new_target_date": "Proposed date cannot exceed planned window end plus 3 months."}
        )

    plan.status = "EXTENSION_REQUESTED"
    plan.extended_due_date = proposed_new_target_date
    plan.extension_requested_reason = reason
    plan.extension_requested_by = actor
    plan.extension_requested_at = timezone.now()
    plan.updated_by = actor
    plan.updated_date = timezone.now()
    return save_plan_update(
        plan,
        [
            "status",
            "extended_due_date",
            "extension_requested_reason",
            "extension_requested_by",
            "extension_requested_at",
            "updated_by",
            "updated_date",
        ],
    )


def decide_plan_extension(
    plan: MasterAuditPlan,
    *,
    decision: str,
    reason: str,
    actor: str,
) -> ExtensionDecisionResult:
    decision = _clean_text(decision).upper()
    reason = _clean_text(reason)
    if plan.status != "EXTENSION_REQUESTED":
        raise AuditPlanWorkflowError({"status": "Plan must be EXTENSION_REQUESTED before DPA decision."})
    if decision not in {"APPROVE", "REJECT"}:
        raise AuditPlanWorkflowError({"decision": "Decision must be APPROVE or REJECT."})
    if len(reason) < MIN_EXTENSION_REASON_LENGTH:
        raise AuditPlanWorkflowError(
            {"extension_approved_reason": "DPA decision reason must be at least 50 characters."}
        )

    with transaction.atomic():
        if decision == "APPROVE":
            plan.extension_form_ref = _next_extension_form_ref()
            plan.extension_approved_at = timezone.now()
            plan.extension_approved_by = actor
            plan.extension_approved_reason = reason
            plan.status = "EXTENDED"
            approved = True
            update_fields = [
                "extension_form_ref",
                "extension_approved_at",
                "extension_approved_by",
                "extension_approved_reason",
                "status",
            ]
        else:
            plan.extension_approved_at = timezone.now()
            plan.extension_approved_by = actor
            plan.extension_approved_reason = reason
            plan.extended_due_date = None
            plan.status = "OVERDUE"
            approved = False
            update_fields = [
                "extension_approved_at",
                "extension_approved_by",
                "extension_approved_reason",
                "extended_due_date",
                "status",
            ]

        plan.updated_by = actor
        plan.updated_date = timezone.now()
        update_fields.extend(["updated_by", "updated_date"])
        plan = save_plan_update(plan, update_fields)

    return ExtensionDecisionResult(plan=plan, approved=approved)


def record_flag_notification(
    plan: MasterAuditPlan,
    *,
    notification_date: date,
    notification_ref: str,
    attachment: str,
    actor: str,
) -> MasterAuditPlan:
    notification_ref = _clean_text(notification_ref)
    attachment = _clean_text(attachment)
    if not notification_ref:
        raise AuditPlanWorkflowError({"flag_notification_ref": "Flag notification reference is required."})
    if not attachment:
        raise AuditPlanWorkflowError({"flag_notification_attachment": "Flag notification attachment is required."})

    plan.flag_notified = True
    plan.flag_notification_date = notification_date
    plan.flag_notification_ref = notification_ref
    plan.flag_notification_attachment = attachment
    plan.updated_by = actor
    plan.updated_date = timezone.now()
    return save_plan_update(
        plan,
        [
            "flag_notified",
            "flag_notification_date",
            "flag_notification_ref",
            "flag_notification_attachment",
            "updated_by",
            "updated_date",
        ],
    )


def _next_extension_form_ref() -> str:
    year = timezone.localdate().year
    prefix = f"{EXTENSION_REF_PREFIX}-{year}-"
    max_sequence = 0
    for value in MasterAuditPlan.all_objects.filter(extension_form_ref__startswith=prefix).values_list(
        "extension_form_ref",
        flat=True,
    ):
        match = re.fullmatch(rf"{re.escape(prefix)}(\d+)", str(value or ""))
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))
    return f"{prefix}{max_sequence + 1:03d}"


def _clean_text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "AuditPlanWorkflowError",
    "ExtensionDecisionResult",
    "decide_plan_extension",
    "record_flag_notification",
    "request_plan_extension",
]
