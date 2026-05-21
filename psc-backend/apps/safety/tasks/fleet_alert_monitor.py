from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.safety.models import Incident
from apps.safety.services.fleet_alert_issuer import FleetAlertIssuer


def monitor_high_priority_near_miss_fleet_alerts(*, now=None) -> list[dict[str, object]]:
    current_time = now or timezone.now()
    issuer = FleetAlertIssuer()
    if not issuer.notification_writer.table_exists():
        return []

    emitted: list[dict[str, object]] = []
    queryset = Incident.objects.filter(
        is_deleted=False,
        record_type=Incident.RecordType.NEAR_MISS,
        near_miss_priority="HIGH",
        superseded_by_id__isnull=True,
    ).order_by("id")

    for near_miss in queryset:
        if issuer.is_issued(near_miss):
            continue

        anchor = issuer.resolve_deadline_anchor(near_miss)
        age = current_time - anchor
        if age < timedelta(days=5):
            continue

        if age >= timedelta(days=8):
            recipient = "FM"
            kind = "NEAR_MISS_FLEET_ALERT_ESCALATION_DAY_8"
            title = "Fleet alert overdue for HIGH-priority near miss"
            message = (
                f"HIGH-priority near miss {near_miss.incident_number} remains without a fleet alert beyond the 7-day SLA."
            )
        elif age >= timedelta(days=6):
            recipient = "DPA"
            kind = "NEAR_MISS_FLEET_ALERT_NUDGE_DAY_6"
            title = "Fleet alert due tomorrow for HIGH-priority near miss"
            message = (
                f"HIGH-priority near miss {near_miss.incident_number} still requires a fleet alert before the 7-day SLA."
            )
        else:
            recipient = "DPA"
            kind = "NEAR_MISS_FLEET_ALERT_NUDGE_DAY_5"
            title = "Fleet alert due soon for HIGH-priority near miss"
            message = (
                f"HIGH-priority near miss {near_miss.incident_number} has reached day 5 without a fleet alert."
            )

        if issuer.notification_kind_exists(record_id=near_miss.pk, kind=kind):
            continue

        rows = issuer.notification_writer.write_notification(
            record_id=near_miss.pk,
            recipients=[recipient],
            kind=kind,
            title=title,
            message=message,
            payload={
                "incident_number": near_miss.incident_number,
                "near_miss_id": near_miss.pk,
                "priority": near_miss.near_miss_priority,
            },
        )
        if rows:
            emitted.append(
                {
                    "kind": kind,
                    "near_miss_id": near_miss.pk,
                    "recipient": recipient,
                }
            )

    return emitted
