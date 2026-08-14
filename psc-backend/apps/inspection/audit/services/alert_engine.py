"""Internal audit plan alert ladder for Phase 8 Step 8.2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import MasterAuditPlan
from apps.inspection.audit.services.audit_window import (
    AuditWindowRuleMissing,
    compute_window_for_plan,
)
from apps.inspection.audit.services.notification_dispatcher import dispatch_audit_notification


SYSTEM_ACTOR = "system.audit_window_tick"
CADENCE_EXCLUDED_STATUSES = {"CANCELLED"}
OPEN_LADDER_STATUSES = {
    "PLANNED",
    "CONFIRMED",
    "IN_PROGRESS",
    "EXTENDED",
    "OVERDUE",
    "CRITICAL_OVERDUE",
}


@dataclass(frozen=True)
class AuditWindowAlertEvent:
    plan_id: UUID
    event_type: str
    days_from_window_end: int
    window_end: date
    recipient_group: str
    severity: str
    status_after: str
    created_plan_id: UUID | None = None
    cert_at_risk: bool = False


@dataclass(frozen=True)
class AuditWindowTickResult:
    dry_run: bool
    scanned: int
    due: int
    created_plans: int
    overdue_plans: int
    critical_overdue_plans: int
    skipped_missing_rule: int
    events: list[AuditWindowAlertEvent]


def run_internal_audit_window_ladder(
    *,
    today: date | None = None,
    apply: bool = False,
) -> AuditWindowTickResult:
    current_date = today or timezone.localdate()
    events: list[AuditWindowAlertEvent] = []
    created_plans = 0
    overdue_plans = 0
    critical_overdue_plans = 0
    skipped_missing_rule = 0

    queryset = MasterAuditPlan.all_objects.filter(is_additional=False).exclude(
        status__in=CADENCE_EXCLUDED_STATUSES
    )
    scanned = queryset.count()

    with transaction.atomic():
        for plan in queryset.order_by("planned_window_end", "id"):
            if plan.status == "COMPLETED":
                try:
                    created_event = _maybe_create_next_cycle_plan(
                        plan,
                        today=current_date,
                        apply=apply,
                    )
                except AuditWindowRuleMissing:
                    skipped_missing_rule += 1
                    continue
                if created_event is not None:
                    events.append(created_event)
                    if created_event.created_plan_id is not None:
                        created_plans += 1
                continue

            ladder_event, status_changed_to = _evaluate_open_plan(
                plan,
                today=current_date,
                apply=apply,
            )
            if ladder_event is None:
                continue
            events.append(ladder_event)
            if status_changed_to == "OVERDUE":
                overdue_plans += 1
            elif status_changed_to == "CRITICAL_OVERDUE":
                critical_overdue_plans += 1

        if not apply:
            transaction.set_rollback(True)

    return AuditWindowTickResult(
        dry_run=not apply,
        scanned=scanned,
        due=len(events),
        created_plans=created_plans,
        overdue_plans=overdue_plans,
        critical_overdue_plans=critical_overdue_plans,
        skipped_missing_rule=skipped_missing_rule,
        events=events,
    )


def _maybe_create_next_cycle_plan(
    plan: MasterAuditPlan,
    *,
    today: date,
    apply: bool,
) -> AuditWindowAlertEvent | None:
    anchor_date = plan.extended_due_date or plan.planned_window_end
    if anchor_date is None:
        return None

    next_window = compute_window_for_plan(plan, anchor_date=anchor_date)
    if today < next_window.window_end - timedelta(days=90):
        return None
    if _matching_plan_exists(plan, window_end=next_window.window_end):
        return None

    created_plan_id = None
    status_after = "PLANNED"
    if apply:
        created_plan = MasterAuditPlan.objects.create(
            target_vessel_id=plan.target_vessel_id,
            target_office_dept=plan.target_office_dept,
            audit_classification=plan.audit_classification,
            audit_standards_csv=plan.audit_standards_csv,
            planned_window_start=next_window.window_start,
            planned_window_end=next_window.window_end,
            status=status_after,
            created_by=SYSTEM_ACTOR,
        )
        created_plan_id = created_plan.id

    return AuditWindowAlertEvent(
        plan_id=plan.id,
        event_type="AUDIT_WINDOW_T90_PLAN_CREATED" if apply else "AUDIT_WINDOW_T90_PLAN_DUE",
        days_from_window_end=(today - next_window.window_end).days,
        window_end=next_window.window_end,
        recipient_group="SEQ_MANAGER",
        severity="warning",
        status_after=status_after,
        created_plan_id=created_plan_id,
    )


def _evaluate_open_plan(
    plan: MasterAuditPlan,
    *,
    today: date,
    apply: bool,
) -> tuple[AuditWindowAlertEvent | None, str | None]:
    if plan.status not in OPEN_LADDER_STATUSES:
        return None, None

    window_end = plan.extended_due_date or plan.planned_window_end
    if window_end is None:
        return None, None

    days_from_end = (today - window_end).days
    event_type = _event_type_for_days(days_from_end)
    if event_type is None:
        return None, None

    status_after = plan.status
    status_changed_to = None
    if days_from_end >= 90 and plan.status != "CRITICAL_OVERDUE":
        status_after = "CRITICAL_OVERDUE"
        status_changed_to = status_after
    elif days_from_end >= 0 and plan.status == "PLANNED":
        status_after = "OVERDUE"
        status_changed_to = status_after

    if apply and status_changed_to is not None:
        plan.status = status_after
        plan.updated_by = SYSTEM_ACTOR
        plan.updated_date = timezone.now()
        plan.save(update_fields=["status", "updated_by", "updated_date"])
        if event_type in {"AUDIT_OVERDUE", "AUDIT_CRITICAL_OVERDUE"}:
            _dispatch_window_notification(plan, event_type)

    return (
        AuditWindowAlertEvent(
            plan_id=plan.id,
            event_type=event_type,
            days_from_window_end=days_from_end,
            window_end=window_end,
            recipient_group=_recipient_group_for_event(event_type),
            severity=_severity_for_event(event_type),
            status_after=status_after,
            cert_at_risk=days_from_end >= 90,
        ),
        status_changed_to,
    )


def _event_type_for_days(days_from_end: int) -> str | None:
    if days_from_end >= 90:
        return "AUDIT_CRITICAL_OVERDUE"
    if days_from_end >= 60:
        return "AUDIT_CRITICAL_T60"
    if days_from_end >= 30:
        return "AUDIT_CRITICAL_T30"
    if days_from_end >= 0:
        return "AUDIT_OVERDUE"
    if days_from_end >= -30:
        return "AUDIT_DUE_T30"
    if days_from_end >= -90:
        return "AUDIT_DUE_T90"
    return None


def _recipient_group_for_event(event_type: str) -> str:
    if event_type in {"AUDIT_DUE_T90"}:
        return "SEQ_MANAGER"
    if event_type in {"AUDIT_DUE_T30", "AUDIT_OVERDUE"}:
        return "DPA"
    return "MANAGING_DIRECTOR"


def _severity_for_event(event_type: str) -> str:
    if event_type in {"AUDIT_CRITICAL_T30", "AUDIT_CRITICAL_T60", "AUDIT_CRITICAL_OVERDUE"}:
        return "critical"
    if event_type == "AUDIT_OVERDUE":
        return "warning"
    return "info"


def _matching_plan_exists(plan: MasterAuditPlan, *, window_end: date) -> bool:
    queryset = MasterAuditPlan.all_objects.filter(
        target_vessel_id=plan.target_vessel_id,
        target_office_dept=plan.target_office_dept,
        planned_window_end=window_end,
        is_additional=False,
    ).exclude(status="CANCELLED")
    return queryset.exclude(id=plan.id).exists()


def _dispatch_window_notification(plan: MasterAuditPlan, event_type: str) -> None:
    titles = {
        "AUDIT_OVERDUE": "Audit overdue",
        "AUDIT_CRITICAL_OVERDUE": "Audit critically overdue",
    }
    messages = {
        "AUDIT_OVERDUE": "Internal audit plan has reached its planned window end.",
        "AUDIT_CRITICAL_OVERDUE": "Internal audit plan is critically overdue.",
    }
    dispatch_audit_notification(
        notification_type=event_type,
        title=titles[event_type],
        message=messages[event_type],
        entity_type="AUDIT_PLAN",
        entity_id=plan.id,
        vessel_id=plan.target_vessel_id,
        office_dept=plan.target_office_dept,
        actor=SYSTEM_ACTOR,
    )


__all__ = [
    "AuditWindowAlertEvent",
    "AuditWindowTickResult",
    "run_internal_audit_window_ladder",
]
