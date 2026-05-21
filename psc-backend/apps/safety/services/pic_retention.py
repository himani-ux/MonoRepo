from __future__ import annotations

from apps.safety.models import Incident, SafetyFieldHistory

from .field_history_recorder import resolve_actor_id, resolve_actor_role


class PicRetentionService:
    field_name = "yellow_pic_retention"

    def current_status(self, incident: Incident) -> dict[str, object]:
        retained = bool(incident.risk_band == Incident.RiskBand.YELLOW and incident.pic_user_id)
        return {
            "retained": retained,
            "retained_pic_user_id": incident.pic_user_id,
            "replacement_access": "READ_ONLY" if retained else "STANDARD",
        }

    def handle_transfer(self, incident: Incident, *, incoming_pic_user_id: str | None, user) -> dict[str, object]:
        if incident.risk_band == Incident.RiskBand.YELLOW and incident.pic_user_id:
            if incoming_pic_user_id and incoming_pic_user_id != incident.pic_user_id:
                SafetyFieldHistory.objects.create(
                    parent_table=incident._meta.db_table,
                    parent_id=incident.pk,
                    field_name=self.field_name,
                    old_value=incoming_pic_user_id,
                    new_value=incident.pic_user_id,
                    change_reason="Original PIC retained after vessel transfer for YELLOW-band continuity.",
                    actor_user_id=resolve_actor_id(user),
                    actor_role_code=resolve_actor_role(user),
                    schema_version=incident.schema_version or 1,
                )
            return self.current_status(incident)

        if incoming_pic_user_id and incoming_pic_user_id != incident.pic_user_id:
            previous = incident.pic_user_id
            incident.pic_user_id = incoming_pic_user_id
            incident.updated_by = resolve_actor_id(user)
            incident.save(update_fields=["pic_user_id", "updated_by"])
            SafetyFieldHistory.objects.create(
                parent_table=incident._meta.db_table,
                parent_id=incident.pk,
                field_name="pic_user_id",
                old_value=previous,
                new_value=incoming_pic_user_id,
                change_reason="PIC assignment updated after transfer.",
                actor_user_id=resolve_actor_id(user),
                actor_role_code=resolve_actor_role(user),
                schema_version=incident.schema_version or 1,
            )
        return self.current_status(incident)
