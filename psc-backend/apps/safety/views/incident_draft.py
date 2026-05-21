from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import Incident
from apps.safety.serializers.incident_draft import IncidentDraftSerializer
from apps.safety.services import capture_model_state, record_field_changes
from apps.safety.views.incident import IncidentViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_DRAFT_MUTATION_ROLES = {
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


class IncidentDraftSaveView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentDraftSerializer
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_002")

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def _enforce_draft_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_DRAFT_MUTATION_ROLES:
            raise PermissionDenied("Only active incident investigators may save drafts.")

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        if incident.current_phase < 1 or incident.current_phase > 6:
            raise ValidationError("Draft-save is limited to incident phases 1 through 6.")

        self._enforce_draft_role()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_state = capture_model_state(incident, field_names=("state", "updated_by", "updated_date"))
        incident.state = "DRAFT"
        incident.updated_by = _resolve_actor_id(request.user)
        incident.updated_date = timezone.now()
        incident.save(update_fields=("state", "updated_by", "updated_date"))
        record_field_changes(
            incident,
            old_state,
            user=request.user,
            field_names=("state", "updated_by", "updated_date"),
            change_reason=serializer.validated_data.get("draft_note") or f"Draft saved for Phase {incident.current_phase}.",
        )
        return Response(
            {
                "id": incident.pk,
                "current_phase": incident.current_phase,
                "state": incident.state,
                "updated_at": incident.updated_date,
            },
            status=status.HTTP_200_OK,
        )
