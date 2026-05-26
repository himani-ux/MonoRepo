from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.utils import timezone

from apps.safety.models import SOIInspection


@dataclass(frozen=True)
class Section12CycleStatus:
    vessel_id: str
    cycle_label: str
    cycle_start: date
    cycle_end: date
    covered_this_cycle: bool
    prompt_required: bool
    next_allowed_date: date | None
    covered_by_inspection_id: int | None
    covered_by_inspection_reference: str | None
    covered_planned_date: date | None

    def to_payload(self) -> dict[str, object]:
        return {
            "vessel_id": self.vessel_id,
            "cycle_label": self.cycle_label,
            "cycle_start": self.cycle_start.isoformat(),
            "cycle_end": self.cycle_end.isoformat(),
            "covered_this_cycle": self.covered_this_cycle,
            "prompt_required": self.prompt_required,
            "next_allowed_date": self.next_allowed_date.isoformat() if self.next_allowed_date else None,
            "covered_by_inspection_id": self.covered_by_inspection_id,
            "covered_by_inspection_reference": self.covered_by_inspection_reference,
            "covered_planned_date": self.covered_planned_date.isoformat() if self.covered_planned_date else None,
        }


class Section12CycleEnforcer:
    def __init__(self, *, inspection_model=SOIInspection, today_func=timezone.localdate) -> None:
        self.inspection_model = inspection_model
        self.today_func = today_func

    def can_pick_section_12(
        self,
        *,
        vessel_id: str,
        at_date: date | None = None,
        exclude_inspection_id: int | None = None,
    ) -> tuple[bool, date | None]:
        status = self._build_status(
            vessel_id=vessel_id,
            at_date=at_date or self.today_func(),
            exclude_inspection_id=exclude_inspection_id,
        )
        return (not status.covered_this_cycle, status.next_allowed_date)

    def get_status(
        self,
        vessel_id: str,
        *,
        at_date: date | None = None,
        exclude_inspection_id: int | None = None,
    ) -> dict[str, object]:
        status = self._build_status(
            vessel_id=vessel_id,
            at_date=at_date or self.today_func(),
            exclude_inspection_id=exclude_inspection_id,
        )
        return status.to_payload()

    def _build_status(
        self,
        *,
        vessel_id: str,
        at_date: date,
        exclude_inspection_id: int | None,
    ) -> Section12CycleStatus:
        cycle_start, cycle_end, next_cycle_start, cycle_label = self._resolve_cycle_window(at_date)
        queryset = self.inspection_model.objects.filter(
            vessel_id=str(vessel_id),
            is_deleted=False,
            section_12_included=True,
            planned_date__gte=cycle_start,
            planned_date__lt=next_cycle_start,
        )
        if exclude_inspection_id is not None:
            queryset = queryset.exclude(pk=exclude_inspection_id)
        covered_inspection = queryset.order_by("planned_date", "id").first()

        return Section12CycleStatus(
            vessel_id=str(vessel_id),
            cycle_label=cycle_label,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            covered_this_cycle=covered_inspection is not None,
            prompt_required=covered_inspection is None,
            next_allowed_date=next_cycle_start if covered_inspection is not None else None,
            covered_by_inspection_id=getattr(covered_inspection, "id", None),
            covered_by_inspection_reference=getattr(covered_inspection, "inspection_reference", None),
            covered_planned_date=getattr(covered_inspection, "planned_date", None),
        )

    @staticmethod
    def _resolve_cycle_window(target_date: date) -> tuple[date, date, date, str]:
        quarter_number = ((target_date.month - 1) // 3) + 1
        cycle_start_month = ((quarter_number - 1) * 3) + 1
        cycle_start = date(target_date.year, cycle_start_month, 1)
        if cycle_start_month == 10:
            next_cycle_start = date(target_date.year + 1, 1, 1)
        else:
            next_cycle_start = date(target_date.year, cycle_start_month + 3, 1)
        cycle_end = next_cycle_start - timedelta(days=1)
        return cycle_start, cycle_end, next_cycle_start, f"Q{quarter_number}/{target_date.year}"
