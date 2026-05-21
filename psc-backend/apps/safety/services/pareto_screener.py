from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.safety.models import Incident, IncidentCauseTag, MasterMscatTaxonomy
from apps.safety.serializers.vessel_display import resolve_vessel_display


class ParetoScreenerService:
    WINDOW_DAYS = 365
    DEFAULT_TOP_N = 10

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

    def build_panel(self, *, vessel_id: str | None = None, as_of=None, top_n: int | None = None) -> dict[str, object]:
        current_at = as_of or self.now_func()
        window_end = current_at.date()
        window_start = window_end - timedelta(days=self.WINDOW_DAYS - 1)
        limit = top_n or self.DEFAULT_TOP_N

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
            queryset.values("incident__vessel_id", "mscat_subcode_id").annotate(
                occurrences=Count("incident_id", distinct=True),
            ).order_by(
                "-occurrences",
                "incident__vessel_id",
                "mscat_subcode_id",
            )
        )
        top_grouped = grouped[:limit]

        taxonomy_map = {
            row.subcode_id: row
            for row in self.taxonomy_model.objects.filter(
                subcode_id__in=[entry["mscat_subcode_id"] for entry in top_grouped]
            )
        }
        total_occurrences = sum(entry["occurrences"] for entry in grouped)
        cumulative = 0.0
        entries: list[dict[str, object]] = []

        for index, entry in enumerate(top_grouped, start=1):
            vessel_id_value = entry["incident__vessel_id"] or ""
            vessel_display = resolve_vessel_display(vessel_id_value)
            share_percent = round((entry["occurrences"] / total_occurrences) * 100, 1) if total_occurrences else 0.0
            previous_cumulative = cumulative
            cumulative = round(cumulative + share_percent, 1)
            taxonomy = taxonomy_map.get(entry["mscat_subcode_id"])
            entries.append(
                {
                    "category_name": getattr(taxonomy, "category_name", ""),
                    "cumulative_percent": cumulative,
                    "description": getattr(taxonomy, "subcode_description", entry["mscat_subcode_id"]),
                    "occurrences": entry["occurrences"],
                    "rank": index,
                    "share_percent": share_percent,
                    "subcode_id": entry["mscat_subcode_id"],
                    "vessel_code": vessel_display["vessel_code"],
                    "vessel_display_name": vessel_display["vessel_display_name"],
                    "vessel_id": vessel_id_value,
                    "vessel_name": vessel_display["vessel_name"],
                    "within_80_cutoff": cumulative <= 80.0 or previous_cumulative < 80.0,
                }
            )

        return {
            "entries": entries,
            "scope_id": vessel_id or "",
            "scope_type": "VESSEL" if vessel_id else "FLEET",
            "top_n": limit,
            "total_occurrences": total_occurrences,
            "window_end": window_end.isoformat(),
            "window_start": window_start.isoformat(),
        }
