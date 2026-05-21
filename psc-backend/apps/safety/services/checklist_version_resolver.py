from __future__ import annotations

from datetime import date

from django.db.models import Q
from django.utils import timezone

from apps.safety.models import SOIChecklistVersion


class ChecklistVersionResolutionError(ValueError):
    """Raised when no checklist version matches the requested effective window."""


class ChecklistVersionResolver:
    def __init__(self, *, version_model=SOIChecklistVersion, clock=timezone.now) -> None:
        self.version_model = version_model
        self.clock = clock

    def get_active_version(self, *, at_date: date | None = None) -> SOIChecklistVersion:
        target_date = at_date or self.clock().date()
        version = self._get_version_for_date(target_date=target_date, active_only=True)
        if version is None:
            raise ChecklistVersionResolutionError(
                "No active SOI checklist version is configured for the current create window."
            )
        return version

    def get_version_for_inspection(self, inspection) -> SOIChecklistVersion:
        target_date = inspection.created_date.date() if inspection.created_date else inspection.planned_date
        version = self._get_version_for_date(target_date=target_date, active_only=False)
        if version is None:
            raise ChecklistVersionResolutionError(
                "No checklist version matches the inspection creation window."
            )
        return version

    def _get_version_for_date(
        self,
        *,
        target_date: date,
        active_only: bool,
    ) -> SOIChecklistVersion | None:
        queryset = self.version_model.objects.filter(
            effective_from__lte=target_date,
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=target_date),
        )
        if active_only:
            queryset = queryset.filter(active=True)
        return queryset.order_by("-effective_from", "-id").first()
