"""Effectiveness Review scheduling helpers for KSM-F-NC-001."""

from __future__ import annotations

from datetime import date, timedelta

from django.utils import timezone

from apps.inspection.audit.models import AuditFindingNC


def mark_effectiveness_reviews_overdue(*, today: date | None = None) -> int:
    """Mark incomplete EffRev rows once the T+90 expiry has passed."""

    today = today or timezone.localdate()
    expiry_cutoff_due_date = today - timedelta(days=60)
    return AuditFindingNC.objects.filter(
        effectiveness_review_date__isnull=False,
        effectiveness_review_date__lte=expiry_cutoff_due_date,
        effectiveness_outcome__isnull=True,
        effectiveness_overdue=False,
    ).update(effectiveness_overdue=True, updated_date=timezone.now())


__all__ = ["mark_effectiveness_reviews_overdue"]
