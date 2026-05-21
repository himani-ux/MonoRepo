from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.serializers import SOIPickAreasSerializer, SOIPickAreasUpdateSerializer
from apps.safety.views.soi import SOIViewMixin


class SOIPickAreasView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIPickAreasUpdateSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.create_process_permission_class()]

    def get(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        payload = self.get_soi_repository().build_pick_areas_payload(inspection_id=inspection.id)
        payload["section_12_status"] = self.get_section12_cycle_enforcer().get_status(
            vessel_id=inspection.vessel_id,
            at_date=inspection.planned_date,
            exclude_inspection_id=inspection.id,
        )
        serializer = SOIPickAreasSerializer(payload)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "inspection": inspection},
        )
        serializer.is_valid(raise_exception=True)
        payload = serializer.save(inspection_id=inspection.id)
        payload["section_12_status"] = self.get_section12_cycle_enforcer().get_status(
            vessel_id=inspection.vessel_id,
            at_date=inspection.planned_date,
            exclude_inspection_id=inspection.id,
        )
        response_serializer = SOIPickAreasSerializer(payload)
        return Response(response_serializer.data)
