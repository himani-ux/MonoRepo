from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.serializers import SOICreateConfigSerializer, SOISection12StatusSerializer
from apps.safety.services.checklist_version_resolver import ChecklistVersionResolutionError
from apps.safety.services.field_history_recorder import resolve_actor_id, resolve_actor_role
from apps.safety.views.soi import SOIViewMixin


class SOICreateConfigView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOICreateConfigSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.create_process_permission_class()]

    def get(self, request, *args, **kwargs):
        vessel_id = self._resolve_vessel_id()
        section12_date = self._resolve_reference_date(
            request.query_params.get("planned_date"),
            field_name="planned_date",
        )
        safety_officer = self.get_assistant_validator().resolve_safety_officer(
            vessel_id=vessel_id,
            actor_id=resolve_actor_id(request.user),
            actor_role=resolve_actor_role(request.user),
            active_on=section12_date,
        )
        applicable_areas = self.get_soi_repository().list_available_areas(vessel_id=vessel_id)
        assistant_candidates = []
        trainee_candidates = []
        if safety_officer is not None:
            assistant_candidates = self.get_cms_repository().list_current_vessel_crew(
                vessel_id=vessel_id,
                active_on=section12_date,
                exclude_department=str(safety_officer.get("department") or ""),
                exclude_crew_id=str(safety_officer.get("crew_id") or ""),
            )
            trainee_candidates = self.get_cms_repository().list_current_vessel_crew(
                vessel_id=vessel_id,
                active_on=section12_date,
                exclude_crew_id=str(safety_officer.get("crew_id") or ""),
            )
        try:
            checklist_version = self.get_checklist_version_resolver().get_active_version()
        except ChecklistVersionResolutionError:
            checklist_version = None

        serializer = self.get_serializer(
            {
                "areas": applicable_areas,
                "assistant_candidates": assistant_candidates,
                "checklist_version": checklist_version,
                "max_trainees": 3,
                "section_12_status": self.get_section12_cycle_enforcer().get_status(
                    vessel_id=vessel_id,
                    at_date=section12_date,
                ),
                "safety_officer": safety_officer,
                "trainee_candidates": trainee_candidates,
            }
        )
        return Response(serializer.data)


class SOISection12StatusView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOISection12StatusSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.create_process_permission_class()]

    def get(self, request, *args, **kwargs):
        vessel_id = self._resolve_vessel_id()
        at_date = self._resolve_reference_date(
            request.query_params.get("at_date"),
            field_name="at_date",
        )
        payload = self.get_section12_cycle_enforcer().get_status(
            vessel_id=vessel_id,
            at_date=at_date,
        )
        serializer = self.get_serializer(payload)
        return Response(serializer.data)
