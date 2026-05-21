from __future__ import annotations

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import Incident
from apps.safety.services.incident_circular_publisher import IncidentCircularPublisher
from apps.safety.views.incident import IncidentViewMixin


class IncidentCircularPublishView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    process_permission_class = HasProcessPermission.requiring("SAF_P_024")
    circular_publisher_class = IncidentCircularPublisher

    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_circular_publisher(self) -> IncidentCircularPublisher:
        return self.circular_publisher_class()

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        if incident.record_type != Incident.RecordType.INCIDENT:
            raise PermissionDenied("Circular publish is restricted to incident records.")

        result = self.get_circular_publisher().publish_from_incident(
            incident=incident,
            user=request.user,
        )
        return Response(
            {
                "status": result.status,
                "circular_id": result.circular_id,
                "detail_url": result.detail_url,
                "payload": result.payload,
            },
            status=status.HTTP_201_CREATED,
        )
