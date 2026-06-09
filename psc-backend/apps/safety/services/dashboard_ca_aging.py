from __future__ import annotations

from django.db.models import Q

from apps.safety.models import CorrectiveAction, Incident, SCMAgendaItem, SCMMeeting

from .ca_aging import CorrectiveActionAgingService


class DashboardCorrectiveActionAgingService:
    BUCKET_LABELS = {
        "0-15": "0-15 days",
        "15-30": "15-30 days",
        "30-45": "30-45 days",
        "45+": "45+ days",
    }
    BUCKET_ORDER = ("0-15", "15-30", "30-45", "45+")
    PANEL_LABEL = "CA Aging Pipeline"
    PANEL_NOTE = "Clock starts at CA creation date; reopened actions keep the original aging clock."

    def __init__(
        self,
        *,
        corrective_action_model=CorrectiveAction,
        incident_model=Incident,
        agenda_model=SCMAgendaItem,
        meeting_model=SCMMeeting,
        aging_service: CorrectiveActionAgingService | None = None,
    ) -> None:
        self.corrective_action_model = corrective_action_model
        self.incident_model = incident_model
        self.agenda_model = agenda_model
        self.meeting_model = meeting_model
        self.aging_service = aging_service or CorrectiveActionAgingService()

    def build_panel(self, *, vessel_id: str | None = None) -> dict[str, object]:
        normalized_vessel_id = str(vessel_id).strip() if vessel_id not in (None, "") else ""
        actions = list(self._query_actions(vessel_id=normalized_vessel_id).order_by("created_date", "id"))

        counts = {bucket: 0 for bucket in self.BUCKET_ORDER}
        oldest_age_days = 0
        for action in actions:
            bucket = self.aging_service.aging_bucket(action)
            if bucket not in counts:
                counts[bucket] = 0
            counts[bucket] += 1
            oldest_age_days = max(
                oldest_age_days,
                self.aging_service.days_open(action),
            )

        return {
            "buckets": [
                {
                    "bucket": bucket,
                    "count": counts.get(bucket, 0),
                    "label": self.BUCKET_LABELS[bucket],
                }
                for bucket in self.BUCKET_ORDER
            ],
            "label": self.PANEL_LABEL,
            "note": self.PANEL_NOTE,
            "oldest_age_days": oldest_age_days,
            "open_action_count": len(actions),
            "scope_id": normalized_vessel_id,
            "scope_type": "VESSEL" if normalized_vessel_id else "FLEET",
        }

    def _query_actions(self, *, vessel_id: str):
        queryset = self.corrective_action_model.objects.filter(is_deleted=False).exclude(
            status=self.corrective_action_model.Status.CLOSED
        )

        if not vessel_id:
            return queryset

        incident_ids = list(
            self.incident_model.objects.filter(
                is_deleted=False,
                vessel_id=vessel_id,
            ).values_list("id", flat=True)
        )
        meeting_ids = list(
            self.meeting_model.objects.filter(
                is_deleted=False,
                vessel_id=vessel_id,
            ).values_list("id", flat=True)
        )
        agenda_ids = (
            list(
                self.agenda_model.objects.filter(meeting_id__in=meeting_ids).values_list("id", flat=True)
            )
            if meeting_ids
            else []
        )

        vessel_filter = Q(recommendation__incident__vessel_id=vessel_id)
        if incident_ids:
            vessel_filter |= Q(source_table=self.incident_model._meta.db_table, source_id__in=incident_ids)
        if agenda_ids:
            vessel_filter |= Q(source_table=self.agenda_model._meta.db_table, source_id__in=agenda_ids)
        return queryset.filter(vessel_filter)
