from __future__ import annotations

from decimal import Decimal

from django.utils import timezone

from apps.safety.models import Incident
from apps.safety.services import Mscmepc3PositionFetcher, capture_model_state, record_field_changes


def retry_awaiting_daily_report_matches(*, now=None) -> list[dict[str, object]]:
    current_time = now or timezone.now()
    fetcher = Mscmepc3PositionFetcher()
    queryset = (
        Incident.objects.filter(
            is_deleted=False,
            record_type=Incident.RecordType.INCIDENT,
            awaiting_daily_report_match=True,
            vessel_id__isnull=False,
            occurred_at__isnull=False,
        )
        .exclude(vessel_id="")
        .order_by("id")
    )

    resolved: list[dict[str, object]] = []
    for incident in queryset:
        result = fetcher.fetch_position(vessel_id=str(incident.vessel_id), timestamp=incident.occurred_at)
        if not result["matched"]:
            continue

        tracked_fields = [
            "awaiting_daily_report_match",
            "position_daily_report_id",
            "updated_by",
            "updated_date",
        ]
        old_state = capture_model_state(
            incident,
            field_names=(
                "awaiting_daily_report_match",
                "position_daily_report_id",
                "position_source",
                "latitude",
                "longitude",
                "updated_by",
                "updated_date",
            ),
        )

        has_manual_coordinates = incident.latitude is not None and incident.longitude is not None
        if has_manual_coordinates:
            if incident.position_source in (None, "", fetcher.AWAITING_SOURCE):
                incident.position_source = fetcher.MANUAL_SOURCE
                tracked_fields.append("position_source")
        else:
            incident.latitude = Decimal(str(result["latitude"]))
            incident.longitude = Decimal(str(result["longitude"]))
            incident.position_source = str(result["position_source"])
            tracked_fields.extend(["latitude", "longitude", "position_source"])

        incident.position_daily_report_id = str(result["position_daily_report_id"])
        incident.awaiting_daily_report_match = False
        incident.updated_by = "system"
        incident.updated_date = current_time
        incident.save(update_fields=tracked_fields)

        record_field_changes(
            incident,
            old_state,
            user=None,
            field_names=tracked_fields,
            change_reason="Nightly Reporting retry resolved awaiting_daily_report_match.",
        )
        resolved.append(
            {
                "incident_id": incident.pk,
                "position_daily_report_id": incident.position_daily_report_id,
                "source_table": result["source_table"],
            }
        )

    return resolved
