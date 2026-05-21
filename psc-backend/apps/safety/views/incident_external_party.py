from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import ExternalPartyInjury, Incident
from apps.safety.serializers.incident_external_party import ExternalPartyInjurySerializer
from apps.safety.services import capture_model_state, record_field_changes
from apps.safety.views.incident import IncidentViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_EXTERNAL_PARTY_MUTATION_ROLES = {
    "MASTER",
    "CO",
    "CE",
    "2/E",
    "2E",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "SECOND ENGINEER",
    "DPA",
    "FM",
    "FLEET MANAGER",
}


class IncidentExternalPartyInjuryView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = ExternalPartyInjurySerializer

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_object(self):
        return super().get_object()

    def _enforce_external_party_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_EXTERNAL_PARTY_MUTATION_ROLES:
            raise PermissionDenied("Only incident investigators may edit external-party injury records.")

    def _require_open_phase(self, incident: Incident) -> None:
        if incident.current_phase > 6:
            raise ValidationError("External-party injury capture is limited to open incident phases 1 to 6.")

    def get(self, request, *args, **kwargs):
        incident = self.get_object()
        record = getattr(incident, "external_party_injury", None)
        if record is None:
            raise ValidationError("No external-party injury record exists for this incident.")
        return Response(self.get_serializer(record).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        self._require_open_phase(incident)
        self._enforce_external_party_role()

        existing = getattr(incident, "external_party_injury", None)
        serializer = self.get_serializer(existing, data=request.data, partial=existing is not None)
        serializer.is_valid(raise_exception=True)

        if existing is None:
            record = serializer.save(
                incident=incident,
                created_by=_resolve_actor_id(request.user),
                updated_by=_resolve_actor_id(request.user),
                updated_date=timezone.now(),
                schema_version=incident.schema_version or 1,
            )
            return Response(self.get_serializer(record).data, status=status.HTTP_201_CREATED)

        old_state = capture_model_state(existing, field_names=tuple(serializer.validated_data.keys()))
        record = serializer.save(
            updated_by=_resolve_actor_id(request.user),
            updated_date=timezone.now(),
        )
        record_field_changes(
            record,
            old_state,
            user=request.user,
            field_names=tuple(serializer.validated_data.keys()),
        )
        return Response(self.get_serializer(record).data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        incident = self.get_object()
        self._require_open_phase(incident)
        self._enforce_external_party_role()

        record = getattr(incident, "external_party_injury", None)
        if record is None:
            raise ValidationError("No external-party injury record exists for this incident.")

        serializer = self.get_serializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_state = capture_model_state(record, field_names=tuple(serializer.validated_data.keys()))
        updated = serializer.save(
            updated_by=_resolve_actor_id(request.user),
            updated_date=timezone.now(),
        )
        record_field_changes(
            updated,
            old_state,
            user=request.user,
            field_names=tuple(serializer.validated_data.keys()),
        )
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)
