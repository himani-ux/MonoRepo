from __future__ import annotations

from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import Incident, IncidentFact
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers import (
    IncidentFactContradictionSerializer,
    IncidentFactReorderSerializer,
    IncidentFactSerializer,
    IncidentLinkActionSerializer,
)
from apps.safety.services import IncidentLinkError, IncidentLinker, NearMissSupersedeError, NearMissSupersedeService
from apps.safety.services.incident_evidence_coverage import build_incident_evidence_coverage
from apps.safety.views.incident import IncidentSerializer, IncidentViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_PHASE_4_MUTATION_ROLES = {
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


class IncidentPhase4ViewMixin(IncidentViewMixin):
    incident_lookup_url_kwarg = "id"
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_002")

    def get_incident(self) -> Incident:
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        incident = get_by_id_or_pk(queryset, self.kwargs[self.incident_lookup_url_kwarg])
        if incident.current_phase != 4:
            raise ValidationError("Phase 4 facts can only be edited while current_phase = 4.")
        return incident

    def get_object(self):
        return self.get_incident()

    def _enforce_phase_4_mutation_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_PHASE_4_MUTATION_ROLES:
            raise PermissionDenied("Only investigation roles may edit Phase 4 facts.")


class IncidentPhase4FactListCreateView(IncidentPhase4ViewMixin, generics.ListCreateAPIView):
    lookup_url_kwarg = "id"
    serializer_class = IncidentFactSerializer
    queryset = IncidentFact.objects.none()

    def get_queryset(self):
        return self.get_incident().facts.order_by("sequence_index", "id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        self._enforce_phase_4_mutation_role()
        return super().create(request, *args, **kwargs)


class IncidentPhase4EvidenceSourceListView(IncidentPhase4ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"

    def get(self, request, *args, **kwargs):
        incident = self.get_incident()
        sources: list[dict[str, object]] = []

        for item in incident.evidence_items.order_by("item_type", "id"):
            label = item.title or item.finding or item.source_label or f"Evidence item #{item.pk}"
            sources.append(
                {
                    "id": item.pk,
                    "source_type": item.item_type,
                    "label": label,
                    "detail": item.description or item.comments or item.source_label,
                }
            )

        coverage = build_incident_evidence_coverage(incident)
        for tab in incident.evidence_tabs.order_by("tab_code", "id"):
            if tab.tab_code not in coverage.covered_tabs:
                continue
            sources.append(
                {
                    "id": tab.pk,
                    "source_type": "EVIDENCE_TAB",
                    "label": f"{tab.get_tab_code_display()} evidence tab",
                    "detail": tab.summary or tab.status_chip,
                    "tab_code": tab.tab_code,
                }
            )

        for interview in incident.witness_interviews.order_by("id"):
            sources.append(
                {
                    "id": interview.pk,
                    "source_type": "INTERVIEW",
                    "label": f"Interview: {interview.witness_name}",
                    "detail": interview.meeting_notes,
                }
            )

        for custody in incident.chain_of_custody_rows.filter(evidence_item__isnull=True).order_by(
            "collection_timestamp",
            "id",
        ):
            sources.append(
                {
                    "id": custody.pk,
                    "source_type": "CHAIN_OF_CUSTODY",
                    "label": f"Physical: {custody.description[:80]}",
                    "detail": custody.storage_location,
                }
            )

        return Response(sources, status=status.HTTP_200_OK)


def build_phase4_gate_payload(incident: Incident) -> dict[str, object]:
    coverage = build_incident_evidence_coverage(incident)
    covered_tabs = coverage.covered_tabs
    missing_tabs = coverage.missing_tabs

    facts_count = incident.facts.count()
    blockers = []
    if missing_tabs:
        blockers.append(
            "Complete or mark N/A for evidence tabs: " + ", ".join(missing_tabs) + "."
        )
    if facts_count < 1:
        blockers.append("Add at least one fact before causal analysis.")

    return {
        "can_continue": not blockers,
        "blockers": blockers,
        "covered_tabs": covered_tabs,
        "missing_tabs": missing_tabs,
        "facts_count": facts_count,
    }


class IncidentPhase4GateView(IncidentPhase4ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"

    def get(self, request, *args, **kwargs):
        return Response(build_phase4_gate_payload(self.get_incident()), status=status.HTTP_200_OK)


class IncidentPhase4FactDetailView(IncidentPhase4ViewMixin, generics.UpdateAPIView):
    lookup_url_kwarg = "fact_id"
    serializer_class = IncidentFactSerializer

    def get_queryset(self):
        incident = self.get_incident()
        return incident.facts.order_by("sequence_index", "id")

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        return get_by_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def update(self, request, *args, **kwargs):
        self._enforce_phase_4_mutation_role()
        return super().update(request, *args, **kwargs)


class IncidentPhase4FactReorderView(IncidentPhase4ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    serializer_class = IncidentFactReorderSerializer

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._enforce_phase_4_mutation_role()
        serializer = self.get_serializer(data=request.data, context={"incident": incident})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            facts = {
                fact.id: fact
                for fact in incident.facts.select_for_update().order_by("sequence_index", "id")
            }
            offset = len(facts) + 100
            for fact in facts.values():
                fact.sequence_index += offset
                fact.updated_by = _resolve_actor_id(request.user)
                fact.save(update_fields=["sequence_index", "updated_by"])
            for index, fact_id in enumerate(serializer.validated_data["ordered_fact_ids"], start=1):
                fact = facts[fact_id]
                fact.sequence_index = index
                fact.updated_by = _resolve_actor_id(request.user)
                fact.save(update_fields=["sequence_index", "updated_by"])
        incident.refresh_from_db()
        return Response(
            IncidentFactSerializer(
                incident.facts.order_by("sequence_index", "id"),
                many=True,
                context={"incident": incident, "user_id": _resolve_actor_id(request.user)},
            ).data,
            status=status.HTTP_200_OK,
        )


class IncidentPhase4FactContradictionView(IncidentPhase4ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    serializer_class = IncidentFactContradictionSerializer

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._enforce_phase_4_mutation_role()
        serializer = self.get_serializer(data=request.data, context={"incident": incident})
        serializer.is_valid(raise_exception=True)
        fact = incident.facts.get(pk=serializer.validated_data["fact_id"])
        fact.contradicts_fact_id = serializer.validated_data["contradicts_fact_id"]
        fact.updated_by = _resolve_actor_id(request.user)
        fact.save(update_fields=["contradicts_fact_id", "updated_by"])
        return Response(
            IncidentFactSerializer(
                fact,
                context={"incident": incident, "user_id": _resolve_actor_id(request.user)},
            ).data,
            status=status.HTTP_200_OK,
        )


class IncidentLinkActionView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentLinkActionSerializer
    incident_linker_class = IncidentLinker
    near_miss_supersede_service_class = NearMissSupersedeService

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def post(self, request, *args, **kwargs):
        source_incident = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["link_type"]

        try:
            if action == "RELATED":
                first, second = self.incident_linker_class().link_multi_vessel_incidents(
                    [source_incident.pk, serializer.validated_data["target_incident_id"]]
                )
                payload = {
                    "link_type": action,
                    "source_incident_id": first.pk,
                    "target_incident_id": second.pk,
                }
                return Response(payload, status=status.HTTP_200_OK)

            new_incident = self.near_miss_supersede_service_class().supersede_near_miss(
                source_incident.pk,
                actor_id=_resolve_actor_id(request.user),
            )
        except (IncidentLinkError, NearMissSupersedeError) as exc:
            raise ValidationError(str(exc)) from exc

        return Response(
            {
                "link_type": action,
                "original_incident_id": source_incident.pk,
                "new_incident": IncidentSerializer(
                    new_incident,
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )
