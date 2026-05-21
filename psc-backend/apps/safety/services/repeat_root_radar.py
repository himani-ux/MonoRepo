from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.safety.models import Incident, IncidentCauseTag, MasterMscatTaxonomy


class RepeatRootRadarService:
    WINDOW_DAYS = 183
    MIN_REPEAT_COUNT = 3

    def __init__(
        self,
        *,
        cause_tag_model=IncidentCauseTag,
        incident_model=Incident,
        taxonomy_model=MasterMscatTaxonomy,
        now_func=timezone.now,
    ) -> None:
        self.cause_tag_model = cause_tag_model
        self.incident_model = incident_model
        self.taxonomy_model = taxonomy_model
        self.now_func = now_func

    def build_panel(self, *, vessel_id: str | None = None, as_of=None, limit: int = 10) -> dict[str, object]:
        current_at = as_of or self.now_func()
        window_end = current_at.date()
        window_start = window_end - timedelta(days=self.WINDOW_DAYS - 1)

        return {
            "fleet": self._build_scope_items(
                vessel_id=None,
                window_start=window_start,
                window_end=window_end,
                limit=limit,
            ),
            "minimum_repeat_count": self.MIN_REPEAT_COUNT,
            "scope_id": vessel_id or "",
            "scope_type": "VESSEL" if vessel_id else "FLEET",
            "vessel": self._build_scope_items(
                vessel_id=vessel_id,
                window_start=window_start,
                window_end=window_end,
                limit=limit,
            ),
            "window_end": window_end.isoformat(),
            "window_start": window_start.isoformat(),
        }

    def _build_scope_items(
        self,
        *,
        vessel_id: str | None,
        window_start: date,
        window_end: date,
        limit: int,
    ) -> list[dict[str, object]]:
        queryset = self.cause_tag_model.objects.filter(
            causal_layer=self.cause_tag_model.CausalLayer.ROOT,
            incident__is_deleted=False,
            incident__superseded_by_id__isnull=True,
        ).filter(
            Q(
                incident__occurred_at__date__gte=window_start,
                incident__occurred_at__date__lte=window_end,
            )
            | Q(
                incident__occurred_at__isnull=True,
                incident__created_date__date__gte=window_start,
                incident__created_date__date__lte=window_end,
            )
        )
        if vessel_id:
            queryset = queryset.filter(incident__vessel_id=vessel_id)

        grouped = list(
            queryset.values("mscat_subcode_id").annotate(
                occurrences=Count("incident_id", distinct=True),
                vessel_count=Count("incident__vessel_id", distinct=True),
            ).filter(
                occurrences__gte=self.MIN_REPEAT_COUNT,
            ).order_by(
                "-occurrences",
                "mscat_subcode_id",
            )[:limit]
        )

        if not grouped:
            return []

        taxonomy_map = {
            row.subcode_id: row
            for row in self.taxonomy_model.objects.filter(
                subcode_id__in=[entry["mscat_subcode_id"] for entry in grouped]
            )
        }
        max_occurrences = max(entry["occurrences"] for entry in grouped)
        items: list[dict[str, object]] = []
        for entry in grouped:
            taxonomy = taxonomy_map.get(entry["mscat_subcode_id"])
            items.append(
                {
                    "category_name": getattr(taxonomy, "category_name", ""),
                    "description": getattr(taxonomy, "subcode_description", entry["mscat_subcode_id"]),
                    "occurrences": entry["occurrences"],
                    "relative_strength": round((entry["occurrences"] / max_occurrences) * 100),
                    "subcode_id": entry["mscat_subcode_id"],
                    "vessel_count": entry["vessel_count"],
                }
            )
        return items
