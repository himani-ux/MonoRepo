from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.authentication.roles import normalized_authority_role
from apps.safety.authentication.vessel_scope import filter_by_vessel_scope, user_has_vessel_access
from apps.safety.models import Incident
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.repositories import IncidentRepository, PhaseTransitionError
from apps.safety.serializers import (
    IncidentCreateSerializer,
    IncidentListSerializer,
    IncidentSerializer,
    IncidentTransitionSerializer,
)
from apps.safety.services import (
    Mscmepc3PositionFetcher,
    PhaseStateMachine,
    capture_model_state,
    record_field_changes,
)


ALLOWED_INCIDENT_MUTATION_ROLES = {
    "MASTER",
    "CO",
    "CE",
    "2/E",
    "2E",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "SECOND ENGINEER",
}


def _normalized_role(user) -> str:
    return normalized_authority_role(user)


def _resolve_actor_id(user) -> str:
    if user is None:
        return "system"

    for attr_name in ("username", "employee_id", "crew_id", "user_id", "id"):
        value = getattr(user, attr_name, None)
        if value not in (None, ""):
            return str(value)
    return "system"


class IncidentViewMixin:
    incident_repository_class = IncidentRepository
    form_permission_class = HasFormPermission.requiring("SAF_F_001")
    process_permission_class = HasProcessPermission.requiring("SAF_P_001")
    phase_state_machine_class = PhaseStateMachine
    position_fetcher_class = Mscmepc3PositionFetcher

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method in {"POST", "PATCH", "PUT"}:
            permissions.append(self.process_permission_class())
        return permissions

    def get_incident_repository(self) -> IncidentRepository:
        return self.incident_repository_class()

    def get_phase_state_machine(self) -> PhaseStateMachine:
        return self.phase_state_machine_class()

    def get_position_fetcher(self) -> Mscmepc3PositionFetcher:
        return self.position_fetcher_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident_repository"] = self.get_incident_repository()
        return context

    def _enforce_incident_creation_role(self, *, record_type: str | None = None) -> None:
        if record_type == Incident.RecordType.NEAR_MISS:
            return

        if _normalized_role(self.request.user) not in ALLOWED_INCIDENT_MUTATION_ROLES:
            raise PermissionDenied("Only top-4 officers may create incident records.")

    def _enforce_mutation_role(self, *, record_type: str | None = None) -> None:
        self._enforce_incident_creation_role(record_type=record_type)

    def _apply_filters(self, queryset):
        request = self.request
        queryset = filter_by_vessel_scope(queryset, getattr(request, "user", None))

        if vessel_id := request.query_params.get("vessel_id"):
            queryset = queryset.filter(vessel_id=str(vessel_id))
        if risk_band := request.query_params.get("risk_band"):
            queryset = queryset.filter(risk_band=risk_band)
        if state := request.query_params.get("state"):
            queryset = queryset.filter(state=state)
        if record_type := request.query_params.get("record_type"):
            queryset = queryset.filter(record_type=record_type)

        if date_from := request.query_params.get("date_from"):
            queryset = queryset.filter(occurred_at__date__gte=date_from)
        if date_to := request.query_params.get("date_to"):
            queryset = queryset.filter(occurred_at__date__lte=date_to)
        return queryset

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        return get_by_public_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])


class IncidentListCreateView(IncidentViewMixin, generics.ListCreateAPIView):
    queryset = Incident.objects.filter(is_deleted=False)

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return IncidentCreateSerializer
        return IncidentListSerializer

    def perform_create(self, serializer):
        record_type = serializer.validated_data.get("record_type", Incident.RecordType.INCIDENT)
        self._enforce_incident_creation_role(record_type=record_type)

        actor_id = _resolve_actor_id(self.request.user)
        incident = serializer.save(
            created_by=actor_id,
            updated_by=actor_id,
            reported_at=serializer.validated_data.get("reported_at") or timezone.now(),
        )
        self.get_phase_state_machine().log_creation(incident, self.request.user)


class IncidentDetailView(IncidentViewMixin, generics.RetrieveUpdateAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_serializer_class(self):
        if self.request.method in {"PATCH", "PUT"}:
            return IncidentCreateSerializer
        return IncidentSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        tracked_fields = tuple(serializer.validated_data.keys())
        old_state = capture_model_state(instance, field_names=tracked_fields)
        incident = serializer.save(updated_by=_resolve_actor_id(self.request.user))
        record_field_changes(
            incident,
            old_state,
            user=self.request.user,
            field_names=tracked_fields,
        )


class IncidentTransitionView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentTransitionSerializer

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def _require_process_permission(self, process_id: str) -> None:
        permission = HasProcessPermission.requiring(process_id)()
        if not permission.has_permission(self.request, self):
            raise PermissionDenied("You do not have permission to perform this action.")

    def post(self, request, *args, **kwargs):
        incident = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_phase = serializer.validated_data["target_phase"]
        loop_back_reason = serializer.validated_data.get("loop_back_reason")
        required_process_id = "SAF_P_003" if target_phase < incident.current_phase else "SAF_P_002"
        self._require_process_permission(required_process_id)

        try:
            result = self.get_phase_state_machine().transition(
                incident.pk,
                target_phase,
                request.user,
                reason=loop_back_reason,
            )
        except PhaseTransitionError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(result, status=status.HTTP_200_OK)


class IncidentPositionPrefillView(IncidentViewMixin, generics.GenericAPIView):
    def get_permissions(self):
        return [self.form_permission_class()]

    def get(self, request, *args, **kwargs):
        vessel_id = request.query_params.get("vessel_id")
        timestamp = request.query_params.get("timestamp")
        if not vessel_id or not timestamp:
            return Response(
                {"detail": "Both vessel_id and timestamp are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user_has_vessel_access(request.user, vessel_id):
            raise PermissionDenied("You are not assigned to this vessel.")

        payload = self.get_position_fetcher().fetch_position(vessel_id=vessel_id, timestamp=timestamp)
        return Response(payload, status=status.HTTP_200_OK)
