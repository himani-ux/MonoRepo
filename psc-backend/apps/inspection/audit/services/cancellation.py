"""DPA audit-plan cancellation workflow."""

from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import MasterAuditPlan
from apps.inspection.audit.services.extension import AuditPlanWorkflowError
from apps.inspection.audit.services.plan_persistence import save_plan_update


MIN_CANCELLATION_REASON_LENGTH = 50


def cancel_audit_plan(
    plan: MasterAuditPlan,
    *,
    cancellation_reason: str,
    next_planned_date: date,
    actor: str,
    today: date | None = None,
) -> tuple[MasterAuditPlan, MasterAuditPlan]:
    current_date = today or timezone.localdate()
    reason = str(cancellation_reason or "").strip()
    if len(reason) < MIN_CANCELLATION_REASON_LENGTH:
        raise AuditPlanWorkflowError({"cancellation_reason": "Cancellation reason must be at least 50 characters."})
    if next_planned_date <= current_date:
        raise AuditPlanWorkflowError({"next_planned_date": "Next planned date must be in the future."})
    if plan.status == "CANCELLED":
        return plan, _ensure_replacement_plan(plan, next_planned_date=next_planned_date, actor=actor)

    with transaction.atomic():
        plan.status = "CANCELLED"
        plan.cancellation_reason = reason
        plan.next_planned_date = next_planned_date
        plan.cancelled_by = actor
        plan.cancelled_at = timezone.now()
        plan.updated_by = actor
        plan.updated_date = timezone.now()
        plan = save_plan_update(
            plan,
            [
                "status",
                "cancellation_reason",
                "next_planned_date",
                "cancelled_by",
                "cancelled_at",
                "updated_by",
                "updated_date",
            ],
        )
        replacement = _ensure_replacement_plan(plan, next_planned_date=next_planned_date, actor=actor)

    return plan, replacement


def _ensure_replacement_plan(
    plan: MasterAuditPlan,
    *,
    next_planned_date: date,
    actor: str,
) -> MasterAuditPlan:
    existing = (
        MasterAuditPlan.all_objects.filter(
            target_vessel_id=plan.target_vessel_id,
            target_office_dept=plan.target_office_dept,
            planned_window_end=next_planned_date,
            is_additional=False,
        )
        .exclude(status="CANCELLED")
        .first()
    )
    if existing is not None:
        return existing

    return MasterAuditPlan.objects.create(
        target_vessel_id=plan.target_vessel_id,
        target_office_dept=plan.target_office_dept,
        audit_classification=plan.audit_classification,
        audit_standards_csv=plan.audit_standards_csv,
        planned_window_start=next_planned_date - timedelta(days=90),
        planned_window_end=next_planned_date,
        status="PLANNED",
        created_by=actor,
    )


__all__ = ["cancel_audit_plan"]
