from __future__ import annotations

from django.db.models import Case, IntegerField, Q, Value, When

from apps.safety.models import MasterMscatTaxonomy


class MscatSearchService:
    def search(self, query: str, *, limit: int = 20):
        normalized = (query or "").strip()
        queryset = MasterMscatTaxonomy.objects.filter(active=True)

        if normalized:
            queryset = queryset.filter(
                Q(subcode_id__icontains=normalized)
                | Q(subcode_description__icontains=normalized)
                | Q(category_name__icontains=normalized)
            ).annotate(
                match_rank=Case(
                    When(subcode_id__istartswith=normalized, then=Value(0)),
                    When(subcode_description__istartswith=normalized, then=Value(1)),
                    When(category_name__istartswith=normalized, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            )
        else:
            queryset = queryset.annotate(match_rank=Value(0, output_field=IntegerField()))

        return list(queryset.order_by("match_rank", "category_id", "subcode_id")[:limit])
