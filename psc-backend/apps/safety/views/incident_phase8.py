from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import Incident, IncidentLossEvaluation, RecommendationVerification, SafetyFieldHistory
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers.incident_phase8 import (
    IncidentPhase8CloseSerializer,
    IncidentPhase8VerifySerializer,
    IncidentLossEvaluationSerializer,
    RecommendationVerificationSerializer,
    build_phase8_workspace_payload,
)
from apps.safety.services.field_history_recorder import capture_model_state, record_field_changes, resolve_actor_id
from apps.safety.services.phase_state_machine import PhaseStateMachine
from apps.safety.views.incident import IncidentViewMixin, _normalized_role


DPA_ROLE_CODES = {"DPA"}
GREEN_BAND_PIC_ROLE_CODES = {
    "PIC",
    "VESSEL SUPERINTENDENT",
    "OFFICE_PIC",
    "OFFICE_SSQE",
    "OFFICE_SUPT",
}
OFFICE_DECISION_ROLE_CODES = DPA_ROLE_CODES | GREEN_BAND_PIC_ROLE_CODES


class IncidentPhase8ViewMixin(IncidentViewMixin):
    incident_lookup_url_kwarg = "id"
    phase_state_machine_class = PhaseStateMachine

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_incident(self) -> Incident:
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        return get_by_id_or_pk(queryset, self.kwargs[self.incident_lookup_url_kwarg])

    def get_object(self):
        return self.get_incident()

    def get_phase_state_machine(self) -> PhaseStateMachine:
        return self.phase_state_machine_class()

    def _require_phase_eight(self, incident: Incident) -> None:
        if incident.current_phase != 8:
            raise ValidationError("Loss Evaluation is available after Office Review approval.")

    def _require_any_process_permission(self, process_ids: list[str]) -> None:
        for process_id in process_ids:
            permission = HasProcessPermission.requiring(process_id)()
            if permission.has_permission(self.request, self):
                return
        raise PermissionDenied("You do not have permission to update Loss Evaluation.")

    def _enforce_band_actor(self, incident: Incident) -> None:
        role = _normalized_role(self.request.user)
        if role not in OFFICE_DECISION_ROLE_CODES:
            raise PermissionDenied("Loss Evaluation is restricted to PIC or DPA.")


class IncidentPhase8WorkspaceView(IncidentPhase8ViewMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        incident = self.get_incident()
        return Response(build_phase8_workspace_payload(incident), status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        incident = self.get_incident()

        try:
            loss_evaluation = incident.loss_evaluation
            old_state = capture_model_state(loss_evaluation)
        except IncidentLossEvaluation.DoesNotExist:
            loss_evaluation = None
            old_state = {}

        serializer = IncidentLossEvaluationSerializer(
            loss_evaluation,
            data=request.data,
            partial=True,
            context={"incident": incident, "user": request.user},
        )
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()

        tracked_fields = tuple(
            field_name
            for field_name in IncidentLossEvaluationSerializer.Meta.fields
            if field_name not in {"id", "updated_date"}
        )
        if not old_state:
            old_state = {field_name: None for field_name in tracked_fields}
        record_field_changes(
            saved,
            old_state,
            user=request.user,
            field_names=tracked_fields,
            change_reason="Phase 7 Loss Evaluation saved.",
        )

        return Response(build_phase8_workspace_payload(incident), status=status.HTTP_200_OK)


class IncidentPhase8VerifyView(IncidentPhase8ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentPhase8VerifySerializer

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._require_phase_eight(incident)
        self._enforce_band_actor(incident)

        serializer = self.get_serializer(data=request.data, context={"incident": incident})
        serializer.is_valid(raise_exception=True)

        recommendation = serializer.validated_data["recommendation"]
        verification = RecommendationVerification.objects.create(
            recommendation=recommendation,
            is_effective=serializer.validated_data["is_effective"],
            residual_risk=serializer.validated_data["residual_risk"],
            verified_by=resolve_actor_id(request.user),
            notes=serializer.validated_data["notes"],
        )
        SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name=f"phase8_verification_{recommendation.pk}",
            old_value=None,
            new_value="EFFECTIVE" if verification.is_effective else "INEFFECTIVE",
            change_reason=verification.notes,
            actor_user_id=resolve_actor_id(request.user),
            actor_role_code=_normalized_role(request.user) or "SYSTEM",
            schema_version=incident.schema_version or 1,
        )

        if not verification.is_effective:
            old_state = capture_model_state(incident, field_names=("current_phase", "state"))
            transition = self.get_phase_state_machine().transition(
                incident.pk,
                6,
                request.user,
                reason=verification.notes,
            )
            incident.refresh_from_db()
            incident.state = "SENT_BACK"
            incident.updated_by = resolve_actor_id(request.user)
            incident.updated_date = timezone.now()
            incident.save(update_fields=["state", "updated_by", "updated_date"])
            record_field_changes(
                incident,
                old_state,
                user=request.user,
                field_names=("current_phase", "state"),
                change_reason=verification.notes,
            )
            return Response(
                {
                    "verification": RecommendationVerificationSerializer(verification).data,
                    "looped_back": True,
                    "transition": transition,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "verification": RecommendationVerificationSerializer(verification).data,
                "looped_back": False,
                "tracker": build_phase8_workspace_payload(incident),
            },
            status=status.HTTP_200_OK,
        )


class IncidentPhase8CloseView(IncidentPhase8ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentPhase8CloseSerializer

    def post(self, request, *args, **kwargs):
        raise ValidationError("Incident close is handled in Phase 6 Office Review.")
