from __future__ import annotations

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import Incident, Recommendation
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers import RecommendationSerializer, build_phase6_workspace_payload
from apps.safety.services.alarp_gate import RECOMMENDATION_THEMES
from apps.safety.views.incident import IncidentViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_PHASE_6_MUTATION_ROLES = {
    "MASTER",
    "DPA",
    "FM",
    "HOD",
    "HEAD OF DEPARTMENT",
    "FLEET MANAGER",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
}


class IncidentPhase6ViewMixin(IncidentViewMixin):
    incident_lookup_url_kwarg = "id"
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_002")

    def get_incident(self) -> Incident:
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        incident = get_by_id_or_pk(queryset, self.kwargs[self.incident_lookup_url_kwarg])
        return incident

    def get_object(self):
        return self.get_incident()

    def _enforce_phase_6_mutation_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_PHASE_6_MUTATION_ROLES:
            raise PermissionDenied("Only Master, HOD, DPA, or FM roles may edit Phase 6 recommendations.")

    def _require_phase_six(self) -> Incident:
        incident = self.get_incident()
        if incident.current_phase != 6:
            raise ValidationError("Phase 6 recommendations can only be edited while current_phase = 6.")
        return incident


class IncidentPhase6WorkspaceView(IncidentPhase6ViewMixin, generics.GenericAPIView):
    serializer_class = RecommendationSerializer

    def get(self, request, *args, **kwargs):
        incident = self.get_incident()
        return Response(build_phase6_workspace_payload(incident), status=status.HTTP_200_OK)


class IncidentRecommendationListCreateView(IncidentPhase6ViewMixin, generics.ListCreateAPIView):
    serializer_class = RecommendationSerializer
    queryset = Recommendation.objects.none()

    def get_queryset(self):
        return self.get_incident().recommendations.filter(is_deleted=False).order_by("id")

    def get(self, request, *args, **kwargs):
        incident = self.get_incident()
        return Response(build_phase6_workspace_payload(incident), status=status.HTTP_200_OK)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        self._require_phase_six()
        self._enforce_phase_6_mutation_role()
        return super().create(request, *args, **kwargs)


class IncidentRecommendationDetailView(IncidentPhase6ViewMixin, generics.UpdateAPIView):
    serializer_class = RecommendationSerializer
    lookup_url_kwarg = "recommendation_id"

    def get_queryset(self):
        return self.get_incident().recommendations.filter(is_deleted=False).order_by("id")

    def get_object(self):
        return get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def update(self, request, *args, **kwargs):
        self._require_phase_six()
        self._enforce_phase_6_mutation_role()
        return super().update(request, *args, **kwargs)


class RecommendationThemeListView(IncidentViewMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response({"themes": list(RECOMMENDATION_THEMES)}, status=status.HTTP_200_OK)
