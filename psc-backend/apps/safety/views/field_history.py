from __future__ import annotations

import logging

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.safety.authentication.permissions import HasFormPermission
from apps.safety.models import IncidentPhaseLog, SafetyFieldHistory
from apps.safety.serializers import FieldHistorySerializer, PhaseLogSerializer


logger = logging.getLogger(__name__)


class FieldHistoryView(generics.ListAPIView):
    permission_classes = [HasFormPermission.requiring("SAF_F_001")]
    serializer_class = FieldHistorySerializer
    lookup_url_kwarg = "id"

    def get_queryset(self):
        queryset = SafetyFieldHistory.objects.filter(
            parent_table="vims_safety_incident",
            parent_id=self.kwargs["id"],
        ).order_by("changed_at", "id")
        logger.info(
            "Incident field history accessed for incident_id=%s by %s",
            self.kwargs["id"],
            getattr(self.request.user, "username", "anonymous"),
        )
        return queryset


class IncidentAuditView(APIView):
    permission_classes = [HasFormPermission.requiring("SAF_F_001")]

    def get(self, request, id: int):
        phase_logs = IncidentPhaseLog.objects.filter(incident_id=id).order_by("occurred_at", "id")
        field_history = SafetyFieldHistory.objects.filter(
            parent_table="vims_safety_incident",
            parent_id=id,
        ).order_by("changed_at", "id")
        logger.info(
            "Incident audit accessed for incident_id=%s by %s",
            id,
            getattr(request.user, "username", "anonymous"),
        )
        return Response(
            {
                "phase_log": PhaseLogSerializer(phase_logs, many=True).data,
                "field_history": FieldHistorySerializer(field_history, many=True).data,
            }
        )
