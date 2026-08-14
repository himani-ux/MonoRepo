"""Scheduled Audit window tick entry point."""

from __future__ import annotations

from datetime import date

from apps.inspection.audit.services.alert_engine import (
    AuditWindowTickResult,
    run_internal_audit_window_ladder,
)


def run_audit_window_tick(
    *,
    today: date | None = None,
    apply: bool = False,
) -> AuditWindowTickResult:
    return run_internal_audit_window_ladder(today=today, apply=apply)


__all__ = ["run_audit_window_tick"]
