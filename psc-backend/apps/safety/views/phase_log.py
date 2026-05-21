from __future__ import annotations

from rest_framework import generics

from apps.safety.authentication.permissions import HasFormPermission
from apps.safety.models import IncidentPhaseLog
from apps.safety.serializers import PhaseLogSerializer


class PhaseLogView(generics.ListAPIView):
    permission_classes = [HasFormPermission.requiring("SAF_F_001")]
    serializer_class = PhaseLogSerializer
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return IncidentPhaseLog.objects.filter(incident_id=self.kwargs["id"]).order_by("occurred_at", "id")
