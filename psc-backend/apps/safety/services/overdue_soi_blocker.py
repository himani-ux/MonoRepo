from __future__ import annotations

from django.utils import timezone

from apps.safety.repositories.base import BaseRepository
from apps.safety.services.soi_compliance_calculator import SOIComplianceCalculator


class OverdueSOIBlocker:
    def __init__(
        self,
        *,
        repository: BaseRepository | None = None,
        now_func=timezone.now,
    ) -> None:
        self.calculator = SOIComplianceCalculator(
            repository=repository or BaseRepository(),
            now_func=now_func,
        )

    def check_overdue_soi(self, vessel_id: str) -> list[dict[str, object]]:
        return self.calculator.list_overdue_areas(str(vessel_id))
