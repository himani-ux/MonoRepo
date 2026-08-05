from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.safety.models import Incident
from apps.safety.serializers.incident_phase1 import IncidentPhase1Serializer, IncidentPhase1SubmitSerializer
from apps.safety.services import NotificationWriter, capture_model_state, record_field_changes
from apps.safety.views.incident import IncidentViewMixin, _normalized_role, _resolve_actor_id


PHASE_2_MUTATION_ROLES = {
    "MASTER",
    "CO",
    "CE",
    "DPA",
    "FM",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "FLEET MANAGER",
}
PHASE_2_HANDOFF_RECIPIENTS = ("MASTER", "CO", "CE", "DPA", "FM")


class IncidentPhase1CreateView(IncidentViewMixin, generics.CreateAPIView):
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentPhase1Serializer

    def perform_create(self, serializer):
        self._enforce_mutation_role(record_type=Incident.RecordType.INCIDENT)
        actor_id = _resolve_actor_id(self.request.user)
        incident = serializer.save(
            record_type=Incident.RecordType.INCIDENT,
            created_by=actor_id,
            updated_by=actor_id,
            reported_at=serializer.validated_data.get("reported_at") or timezone.now(),
        )
        self.get_phase_state_machine().log_creation(incident, self.request.user)


class IncidentPhase1UpdateView(IncidentViewMixin, generics.RetrieveUpdateAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentPhase1Serializer

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_object(self):
        incident = super().get_object()
        self._enforce_phase_reached_for_edit(incident, 1, "Phase 1 intake")
        return incident

    def perform_update(self, serializer):
        incident = self.get_object()
        self._enforce_mutation_role(record_type=incident.record_type)
        tracked_fields = tuple(serializer.validated_data.keys())
        old_state = capture_model_state(incident, field_names=tracked_fields)
        updated = serializer.save(updated_by=_resolve_actor_id(self.request.user))
        record_field_changes(
            updated,
            old_state,
            user=self.request.user,
            field_names=tracked_fields,
        )


class IncidentPhase1SubmitView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentPhase1SubmitSerializer
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_001")
    notification_writer_class = NotificationWriter

    def get_notification_writer(self) -> NotificationWriter:
        return self.notification_writer_class()

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        self._enforce_mutation_role(record_type=incident.record_type)

        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "incident": incident},
        )
        serializer.is_valid(raise_exception=True)

        transition = self.get_phase_state_machine().transition(incident.pk, 2, request.user)
        incident.refresh_from_db()
        incident.state = "SUBMITTED"
        incident.updated_by = _resolve_actor_id(request.user)
        incident.updated_date = timezone.now()
        incident.save(update_fields=["state", "updated_by", "updated_date"])
        actor_role = _normalized_role(request.user)
        can_edit_phase_2 = actor_role in PHASE_2_MUTATION_ROLES
        handoff_notification_rows = []
        if not can_edit_phase_2:
            handoff_notification_rows = self.get_notification_writer().write_notification(
                record_id=incident.pk,
                recipients=list(PHASE_2_HANDOFF_RECIPIENTS),
                kind="INCIDENT_PHASE_2_HANDOFF_REQUIRED",
                title="Office communication confirmation required",
                message=(
                    f"Incident draft {incident.pk} completed Phase 1 and awaits "
                    "office communication confirmation by an authorized user."
                ),
                payload={
                    "authorized_roles": list(PHASE_2_HANDOFF_RECIPIENTS),
                    "current_phase": incident.current_phase,
                    "incident_id": incident.pk,
                    "state": incident.state,
                    "submitted_by_role": actor_role,
                },
            )

        payload = IncidentPhase1Serializer(incident, context=self.get_serializer_context()).data
        payload["transition"] = transition
        payload["self_report_conflict"] = serializer.validated_data["self_report_conflict"]
        payload["phase_2_handoff"] = {
            "authorized_roles": list(PHASE_2_HANDOFF_RECIPIENTS),
            "can_edit_phase_2": can_edit_phase_2,
            "message": (
                "Office communication can be confirmed by Master, CO, CE, DPA, or FM."
                if not can_edit_phase_2
                else "Office communication can be confirmed by your role."
            ),
            "notifications_emitted": len(handoff_notification_rows),
        }
        return Response(payload, status=status.HTTP_200_OK)
