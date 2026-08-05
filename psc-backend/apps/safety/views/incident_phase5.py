from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import (
    EvidenceItem,
    Incident,
    IncidentBiasGuardResponse,
    IncidentCauseTag,
    IncidentFact,
    IncidentPhase5Assessment,
    IncidentSafeguardFailure,
)
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers import (
    IncidentBiasGuardResponseSerializer,
    IncidentBlameOverrideSerializer,
    IncidentCauseTagSerializer,
    IncidentPhase5AssessmentSerializer,
    IncidentSafeguardFailureSerializer,
    build_phase5_workspace_payload,
)
from apps.safety.services import MscatSearchService
from apps.safety.views.incident import IncidentViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_PHASE_5_MUTATION_ROLES = {
    "MASTER",
    "CO",
    "CE",
    "HOD",
    "DPA",
    "FM",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "FLEET MANAGER",
    "HEAD OF DEPARTMENT",
}


class IncidentPhase5ViewMixin(IncidentViewMixin):
    incident_lookup_url_kwarg = "id"
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_002")

    def get_incident(self) -> Incident:
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        incident = get_by_id_or_pk(queryset, self.kwargs[self.incident_lookup_url_kwarg])
        return incident

    def get_object(self):
        return self.get_incident()

    def _enforce_phase_5_mutation_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_PHASE_5_MUTATION_ROLES:
            raise PermissionDenied("Only investigation roles may edit root cause.")

    def _require_phase_five(self) -> Incident:
        incident = self.get_incident()
        self._enforce_editable_until_office_approval(incident)
        return incident


def _ensure_root_cause_source_fact(incident: Incident, actor_id: str) -> IncidentFact:
    existing = incident.facts.order_by("sequence_index", "id").first()
    if existing is not None:
        return existing
    evidence = EvidenceItem.objects.create(
        incident=incident,
        item_type=EvidenceItem.ItemType.PHYSICAL,
        title="Initial root cause entry",
        description="Root cause was entered before evidence upload. Evidence will be added in the next phase.",
        source_label="Root cause first workflow",
        created_by=actor_id,
        updated_by=actor_id,
        updated_date=timezone.now(),
        schema_version=incident.schema_version or 1,
    )
    return IncidentFact.objects.create(
        incident=incident,
        sequence_index=1,
        fact_text="Initial root cause entered before evidence upload.",
        source_evidence_id=evidence.id,
        confidence=IncidentFact.Confidence.MEDIUM,
        created_by=actor_id,
        updated_by=actor_id,
        updated_date=timezone.now(),
        schema_version=incident.schema_version or 1,
    )


class IncidentPhase5WorkspaceView(IncidentPhase5ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentPhase5AssessmentSerializer

    def get(self, request, *args, **kwargs):
        incident = self._require_phase_five()
        return Response(build_phase5_workspace_payload(incident), status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        incident = self._require_phase_five()
        self._enforce_phase_5_mutation_role()
        try:
            instance = incident.phase5_assessment
        except IncidentPhase5Assessment.DoesNotExist:
            instance = None
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
            context={"incident": incident, "user_id": _resolve_actor_id(request.user)},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(build_phase5_workspace_payload(incident), status=status.HTTP_200_OK)


class IncidentMscatSearchView(IncidentPhase5ViewMixin, generics.GenericAPIView):
    service_class = MscatSearchService

    def get(self, request, *args, **kwargs):
        self.get_incident()
        query = request.query_params.get("q", "")
        service = self.service_class()
        results = service.search(query)
        return Response(
            {
                "results": [
                    {
                        "category_id": row.category_id,
                        "category_name": row.category_name,
                        "subcode_id": row.subcode_id,
                        "subcode_description": row.subcode_description,
                        "cause_type": row.cause_type,
                    }
                    for row in results
                ]
            },
            status=status.HTTP_200_OK,
        )


class IncidentPhase5CauseListCreateView(IncidentPhase5ViewMixin, generics.ListCreateAPIView):
    serializer_class = IncidentCauseTagSerializer
    queryset = IncidentCauseTag.objects.none()

    def get_queryset(self):
        return self.get_incident().cause_tags.order_by("id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        incident = self._require_phase_five()
        self._enforce_phase_5_mutation_role()
        data = request.data.copy()
        if not data.get("source_fact_id"):
            data["source_fact_id"] = str(_ensure_root_cause_source_fact(incident, _resolve_actor_id(request.user)).id)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class IncidentPhase5CauseDetailView(IncidentPhase5ViewMixin, generics.UpdateAPIView):
    serializer_class = IncidentCauseTagSerializer
    lookup_url_kwarg = "cause_id"

    def get_queryset(self):
        return self.get_incident().cause_tags.order_by("id")

    def get_object(self):
        return get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def update(self, request, *args, **kwargs):
        self._require_phase_five()
        self._enforce_phase_5_mutation_role()
        return super().update(request, *args, **kwargs)


class IncidentPhase5SafeguardListCreateView(IncidentPhase5ViewMixin, generics.ListCreateAPIView):
    serializer_class = IncidentSafeguardFailureSerializer
    queryset = IncidentSafeguardFailure.objects.none()

    def get_queryset(self):
        return self.get_incident().safeguard_failures.order_by("id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        self._require_phase_five()
        self._enforce_phase_5_mutation_role()
        return super().create(request, *args, **kwargs)


class IncidentPhase5SafeguardDetailView(IncidentPhase5ViewMixin, generics.UpdateAPIView):
    serializer_class = IncidentSafeguardFailureSerializer
    lookup_url_kwarg = "safeguard_id"

    def get_queryset(self):
        return self.get_incident().safeguard_failures.order_by("id")

    def get_object(self):
        return get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def update(self, request, *args, **kwargs):
        self._require_phase_five()
        self._enforce_phase_5_mutation_role()
        return super().update(request, *args, **kwargs)


class IncidentBiasGuardChecklistView(IncidentPhase5ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentBiasGuardResponseSerializer

    def get(self, request, *args, **kwargs):
        incident = self.get_incident()
        return Response(build_phase5_workspace_payload(incident)["bias_guards"], status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        incident = self._require_phase_five()
        self._enforce_phase_5_mutation_role()
        responses = request.data.get("responses", [])
        if not isinstance(responses, list):
            raise ValidationError({"responses": "Expected a list of guard responses."})
        payload = []
        for row in responses:
            serializer = self.get_serializer(
                data=row,
                context={"incident": incident, "user_id": _resolve_actor_id(request.user)},
            )
            serializer.is_valid(raise_exception=True)
            payload.append(serializer.save())
        return Response(
            IncidentBiasGuardResponseSerializer(payload, many=True).data,
            status=status.HTTP_200_OK,
        )


class IncidentBlameOverrideView(IncidentPhase5ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentBlameOverrideSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_009")

    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def post(self, request, *args, **kwargs):
        incident = self._require_phase_five()
        role = _normalized_role(request.user)
        if incident.risk_band == Incident.RiskBand.RED:
            if role not in {"FM", "FLEET MANAGER"}:
                raise PermissionDenied("RED-band blame overrides require Fleet Manager authority.")
        elif role != "DPA":
            raise PermissionDenied("GREEN/YELLOW blame overrides require DPA authority.")

        serializer = self.get_serializer(
            data=request.data,
            context={
                "incident": incident,
                "user_id": _resolve_actor_id(request.user),
                "user_role": role,
            },
        )
        serializer.is_valid(raise_exception=True)
        override = serializer.save()
        return Response(
            {
                "incident_id": incident.pk,
                "approved_by": override.approved_by,
                "approved_role": override.approved_role,
            },
            status=status.HTTP_200_OK,
        )
