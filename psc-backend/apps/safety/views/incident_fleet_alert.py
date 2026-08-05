from __future__ import annotations

from rest_framework import generics, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.safety.serializers.incident_phase7 import build_phase7_preflight_payload
from apps.safety.services.incident_fleet_alert import IncidentFleetAlertService
from apps.safety.views.incident_phase7 import (
    IncidentPhase7ViewMixin,
    OFFICE_REVIEW_ACCEPT_PROCESS_IDS,
)


class IncidentFleetAlertIssueSerializer(serializers.Serializer):
    recipient_vessel_ids = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        allow_empty=False,
    )


class IncidentFleetAlertIssueView(IncidentPhase7ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentFleetAlertIssueSerializer
    service_class = IncidentFleetAlertService

    def _require_office_review_available(self, incident) -> None:
        if incident.current_phase < 6:
            raise ValidationError("Incident Fleet Alert is available from Office Review.")

    def get_service(self) -> IncidentFleetAlertService:
        return self.service_class()

    def get(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._require_office_review_available(incident)
        self._enforce_office_review_actor(incident, action="fleet-alert")
        self._require_any_process_permission(OFFICE_REVIEW_ACCEPT_PROCESS_IDS)
        payload = self.get_service().build_workspace_payload(incident)
        payload["preflight"] = build_phase7_preflight_payload(incident)
        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._require_office_review_available(incident)
        self._enforce_office_review_actor(incident, action="fleet-alert")
        self._require_any_process_permission(OFFICE_REVIEW_ACCEPT_PROCESS_IDS)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.get_service().issue_fleet_alert(
            incident=incident,
            recipient_vessel_ids=serializer.validated_data["recipient_vessel_ids"],
        )
        return Response(payload, status=status.HTTP_200_OK)
