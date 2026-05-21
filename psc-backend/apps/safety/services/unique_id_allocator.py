from __future__ import annotations

import re

from django.db import connection
from django.db import transaction
from django.utils import timezone

from apps.safety.models import SOIInspection


_DIGIT_RE = re.compile(r"\D")


class UniqueIdAllocator:
    def __init__(
        self,
        *,
        inspection_model=SOIInspection,
        token_factory=None,
    ) -> None:
        self.inspection_model = inspection_model
        self.token_factory = token_factory

    def allocate(self, inspection_id: int) -> str:
        with transaction.atomic():
            inspection = self.inspection_model.objects.select_for_update().get(
                pk=int(inspection_id),
                is_deleted=False,
            )
            if inspection.checklist_unique_id:
                return str(inspection.checklist_unique_id)

            sequence = self._next_sequence(inspection)
            unique_id = self._build_unique_id(inspection, sequence=sequence)
            while self.inspection_model.objects.filter(checklist_unique_id=unique_id).exclude(
                pk=inspection.pk
            ).exists():
                sequence += 1
                unique_id = self._build_unique_id(inspection, sequence=sequence)

            inspection.checklist_unique_id = unique_id
            inspection.save(update_fields=["checklist_unique_id"])
            return unique_id

    def _next_sequence(self, inspection: SOIInspection) -> int:
        target_date = inspection.planned_date or timezone.localdate()
        return (
            self.inspection_model.objects.filter(
                vessel_id=inspection.vessel_id,
                planned_date=target_date,
                checklist_unique_id__isnull=False,
                is_deleted=False,
            )
            .exclude(pk=inspection.pk)
            .count()
            + 1
        )

    def _build_unique_id(self, inspection: SOIInspection, *, sequence: int) -> str:
        imo_number = self._resolve_imo_number(inspection)
        target_date = inspection.planned_date or timezone.localdate()
        return f"SOI-{imo_number}-{target_date:%Y%m%d}-{sequence:04d}"

    def _resolve_imo_number(self, inspection: SOIInspection) -> str:
        candidates = [self._query_vessel_imo(str(inspection.vessel_id))]
        candidates.append(str(inspection.vessel_id or ""))
        candidates.append(str(inspection.inspection_reference or ""))
        for candidate in candidates:
            digits = _DIGIT_RE.sub("", str(candidate or ""))
            if len(digits) >= 7:
                return digits[:7]
        for candidate in candidates:
            digits = _DIGIT_RE.sub("", str(candidate or ""))
            if digits:
                return digits[-7:].zfill(7)
        fallback_digits = _DIGIT_RE.sub("", str(inspection.pk or ""))[-7:]
        return fallback_digits.zfill(7)

    def _query_vessel_imo(self, vessel_id: str) -> str | None:
        try:
            with connection.cursor() as cursor:
                table_names = connection.introspection.table_names(cursor)
                if "VesselData" not in table_names:
                    return None
                cursor.execute(
                    """
                    SELECT TOP 1 imoNumber
                    FROM VesselData
                    WHERE (CAST(id AS NVARCHAR(64)) = %s OR vesselCode = %s)
                      AND (is_deleted = 0 OR is_deleted IS NULL)
                    """,
                    [vessel_id, vessel_id],
                )
                row = cursor.fetchone()
        except Exception:
            return None
        return str(row[0]) if row and row[0] not in (None, "") else None
