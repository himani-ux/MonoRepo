from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.serializers import (
    IncidentSerializer,
    NearMissSerializer,
    NearMissTriageSerializer,
    PhaseLogSerializer,
)
from apps.safety.services import NearMissSupersedeError, NearMissSupersedeService, capture_model_state, record_field_changes
from apps.safety.views.near_miss import NearMissViewMixin, _normalized_role, _resolve_actor_id


class NearMissTriageView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissTriageSerializer
    process_permission_class = NearMissViewMixin.process_permission_class.requiring("SAF_P_002")
    near_miss_supersede_service_class = NearMissSupersedeService

    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def _enforce_triage_role(self) -> None:
        if _normalized_role(self.request.user) != "DPA":
            raise PermissionDenied("Near-miss triage is restricted to DPA.")

    def patch(self, request, *args, **kwargs):
        near_miss = self.get_object()
        self._enforce_triage_role()
        if near_miss.state != Incident.State.READY_FOR_DPA_TRIAGE:
            raise ValidationError(
                "Near miss must complete vessel-side HOD/Master review before DPA triage."
            )

        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "incident": near_miss},
        )
        serializer.is_valid(raise_exception=True)

        actor_id = _resolve_actor_id(request.user)
        priority = serializer.validated_data["near_miss_priority"]
        override_reason = serializer.validated_data.get("override_reason")
        supersede_to_incident = serializer.validated_data.get("supersede_to_incident", False)
        suggestion = serializer.validated_data["suggestion"]

        tracked_fields = (
            "near_miss_priority",
            "state",
            "superseded_by_id",
            "linked_incident_id",
            "updated_by",
            "updated_date",
        )
        old_state = capture_model_state(near_miss, field_names=tracked_fields)

        near_miss.near_miss_priority = priority
        near_miss.updated_by = actor_id
        near_miss.updated_date = timezone.now()
        if not supersede_to_incident:
            near_miss.state = "TRIAGED"
        near_miss.save(update_fields=["near_miss_priority", "state", "updated_by", "updated_date"])

        superseded_incident = None
        if supersede_to_incident:
            try:
                superseded_incident = self.near_miss_supersede_service_class().supersede_near_miss(
                    near_miss.pk,
                    actor_id=actor_id,
                )
            except NearMissSupersedeError as exc:
                raise ValidationError(str(exc)) from exc
            near_miss.refresh_from_db()

        phase_log = IncidentPhaseLog.objects.create(
            incident=near_miss,
            phase_from=near_miss.current_phase,
            phase_to=near_miss.current_phase,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            loop_back_reason=override_reason or f"Near-miss triaged {priority}.",
            actor_user_id=actor_id,
            actor_role_code=_normalized_role(request.user) or "DPA",
            device_fingerprint=getattr(near_miss, "reporter_device_fingerprint", None),
            schema_version=near_miss.schema_version or 1,
        )
        record_field_changes(
            near_miss,
            old_state,
            user=request.user,
            field_names=tracked_fields,
            change_reason=override_reason or f"Near-miss triage set to {priority}.",
        )

        payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
        payload["suggested_priority"] = suggestion["priority"]
        payload["suggestion_rationale"] = suggestion["rationale"]
        payload["triage_phase_log"] = PhaseLogSerializer(phase_log).data
        payload["superseded_incident"] = (
            IncidentSerializer(superseded_incident, context={"request": request}).data
            if superseded_incident is not None
            else None
        )
        return Response(payload, status=status.HTTP_200_OK)
