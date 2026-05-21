from __future__ import annotations

from apps.safety.models import Incident, SafetyFieldHistory

from .field_history_recorder import resolve_actor_id, resolve_actor_role


class DeadlinePauser:
    field_name = "yellow_deadline_pause"
    paused_value = "PAUSED"
    resumed_value = "RESUMED"

    def latest_event(self, incident: Incident) -> SafetyFieldHistory | None:
        return (
            SafetyFieldHistory.objects.filter(
                parent_table=incident._meta.db_table,
                parent_id=incident.pk,
                field_name=self.field_name,
            )
            .order_by("-changed_at", "-id")
            .first()
        )

    def status_for_incident(self, incident: Incident) -> dict[str, object]:
        latest = self.latest_event(incident)
        is_paused = bool(latest and latest.new_value == self.paused_value)
        return {
            "is_paused": is_paused,
            "state": latest.new_value if latest else self.resumed_value,
            "last_event_at": latest.changed_at.isoformat() if latest else None,
            "last_actor_user_id": latest.actor_user_id if latest else None,
        }

    def sync_incident(self, incident: Incident, *, dpa_on_leave: bool, user) -> dict[str, object]:
        if incident.risk_band != Incident.RiskBand.YELLOW:
            return {
                **self.status_for_incident(incident),
                "changed": False,
                "reason": "Deadline pause applies only to YELLOW incidents.",
            }

        status = self.status_for_incident(incident)
        target_is_paused = bool(dpa_on_leave)
        if status["is_paused"] == target_is_paused:
            return {**status, "changed": False}

        SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name=self.field_name,
            old_value=str(status["state"]),
            new_value=self.paused_value if target_is_paused else self.resumed_value,
            change_reason=(
                "DPA leave is active; YELLOW-band deadline paused."
                if target_is_paused
                else "DPA leave cleared; YELLOW-band deadline resumed."
            ),
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=incident.schema_version or 1,
        )
        return {**self.status_for_incident(incident), "changed": True}
