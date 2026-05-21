from __future__ import annotations

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.safety.models import Incident, IncidentPhaseLog

from .field_history_recorder import (
    capture_model_state,
    record_field_changes,
    resolve_actor_id,
    resolve_actor_role,
)


GREEN_REOPEN_ROLES = {"DPA"}
YELLOW_REOPEN_ROLES = {"DPA"}
RED_REOPEN_ROLES = {"FM", "FLEET MANAGER"}


class IncidentReopenService:
    target_phase = 5

    def reopen(self, *, incident: Incident, user, reason: str) -> dict[str, object]:
        self._assert_reopenable(incident)
        self._assert_actor(incident, user)

        old_state = capture_model_state(
            incident,
            field_names=("current_phase", "state", "closed_at", "closure_reason"),
        )
        incident.current_phase = self.target_phase
        incident.state = "REOPENED"
        incident.closed_at = None
        incident.closure_reason = None
        incident.updated_by = resolve_actor_id(user)
        incident.updated_date = timezone.now()
        incident.save(
            update_fields=("current_phase", "state", "closed_at", "closure_reason", "updated_by", "updated_date")
        )
        record_field_changes(
            incident,
            old_state,
            user=user,
            field_names=("current_phase", "state", "closed_at", "closure_reason"),
            change_reason=reason,
        )
        phase_log = IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=9,
            phase_to=self.target_phase,
            transition_type=IncidentPhaseLog.TransitionType.REOPEN,
            loop_back_reason=reason,
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            device_fingerprint=incident.reporter_device_fingerprint,
            schema_version=incident.schema_version or 1,
        )
        reopen_count = IncidentPhaseLog.objects.filter(
            incident=incident,
            transition_type=IncidentPhaseLog.TransitionType.REOPEN,
        ).count()
        return {
            "incident_id": incident.pk,
            "current_phase": incident.current_phase,
            "state": incident.state,
            "reopen_count": reopen_count,
            "reason": reason,
            "transition": {
                "phase_from": phase_log.phase_from,
                "phase_to": phase_log.phase_to,
                "transition_type": phase_log.transition_type,
                "occurred_at": phase_log.occurred_at,
            },
        }

    def _assert_reopenable(self, incident: Incident) -> None:
        if incident.state != "CLOSED" or incident.current_phase != 9:
            raise ValidationError("Only closed Phase 9 incidents can be reopened.")

    def _assert_actor(self, incident: Incident, user) -> None:
        actor_role = resolve_actor_role(user)

        if incident.risk_band == Incident.RiskBand.GREEN:
            if actor_role not in GREEN_REOPEN_ROLES:
                raise PermissionDenied("GREEN-band reopen is restricted to DPA.")
            return
        if incident.risk_band == Incident.RiskBand.YELLOW:
            if actor_role not in YELLOW_REOPEN_ROLES:
                raise PermissionDenied("YELLOW-band reopen is restricted to DPA.")
            return
        if incident.risk_band == Incident.RiskBand.RED:
            if actor_role not in RED_REOPEN_ROLES:
                raise PermissionDenied("RED-band reopen is restricted to FM.")
            return
        raise ValidationError("Incident risk band must be assigned before re-open.")
