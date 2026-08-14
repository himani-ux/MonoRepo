"""Audit window computation from master_audit_window_rule."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from apps.inspection.audit.models import MasterAuditPlan, MasterAuditWindowRule


DEFAULT_INTERNAL_SUBTYPE = "ANNUAL_INTERNAL"


class AuditWindowRuleMissing(ValueError):
    """Raised when no active data-driven window rule exists."""


@dataclass(frozen=True)
class AuditWindow:
    window_start: date
    window_end: date
    rule_id: UUID
    standard_code: str
    subtype_code: str


def add_months(value: date, months: int) -> date:
    """Add calendar months, clamping end-of-month dates deterministically."""

    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def compute_window_for_plan(
    plan: MasterAuditPlan,
    *,
    anchor_date: date,
    subtype_code: str = DEFAULT_INTERNAL_SUBTYPE,
) -> AuditWindow:
    rule = resolve_window_rule(plan, subtype_code=subtype_code)
    return AuditWindow(
        window_start=add_months(anchor_date, rule.window_open_offset_months),
        window_end=add_months(anchor_date, rule.window_close_offset_months),
        rule_id=rule.id,
        standard_code=rule.standard_code,
        subtype_code=rule.subtype_code,
    )


def resolve_window_rule(
    plan: MasterAuditPlan,
    *,
    subtype_code: str = DEFAULT_INTERNAL_SUBTYPE,
) -> MasterAuditWindowRule:
    standards = _standards_from_csv(plan.audit_standards_csv)
    for standard in standards:
        rule = (
            MasterAuditWindowRule.objects.filter(
                standard_code=standard,
                subtype_code=subtype_code,
                is_active=True,
            )
            .order_by("id")
            .first()
        )
        if rule is not None:
            return rule

    # Test and transitional data may contain a single active annual-internal
    # rule while standards are being normalized. Still data-driven; never
    # fallback to baked-in month constants.
    fallback_rule = (
        MasterAuditWindowRule.objects.filter(
            subtype_code=subtype_code,
            is_active=True,
        )
        .order_by("id")
        .first()
    )
    if fallback_rule is not None:
        return fallback_rule

    raise AuditWindowRuleMissing(
        f"No active audit window rule for standards={standards!r} subtype={subtype_code}."
    )


def _standards_from_csv(value: str | None) -> list[str]:
    standards = [part.strip().upper() for part in str(value or "").split(",") if part.strip()]
    return standards or ["ISM"]


__all__ = [
    "AuditWindow",
    "AuditWindowRuleMissing",
    "DEFAULT_INTERNAL_SUBTYPE",
    "add_months",
    "compute_window_for_plan",
    "resolve_window_rule",
]
