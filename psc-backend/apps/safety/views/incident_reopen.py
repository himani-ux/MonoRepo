from __future__ import annotations

from rest_framework import generics, status
from rest_framework.response import Response

from apps.safety.models import Incident
from apps.safety.serializers.incident_reopen import IncidentReopenSerializer
from apps.safety.services.incident_reopen import IncidentReopenService
from apps.safety.views.incident import IncidentViewMixin


class IncidentReopenView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentReopenSerializer
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_008")
    reopen_service_class = IncidentReopenService

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_reopen_service(self) -> IncidentReopenService:
        return self.reopen_service_class()

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.get_reopen_service().reopen(
            incident=incident,
            user=request.user,
            reason=serializer.validated_data["reason"],
        )
        return Response(payload, status=status.HTTP_200_OK)
