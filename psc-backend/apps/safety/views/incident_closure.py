from __future__ import annotations

from rest_framework import generics, status
from rest_framework.response import Response

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.serializers import FieldHistorySerializer, IncidentSerializer, PhaseLogSerializer
from apps.safety.services.signature_chain import SignatureChainService
from apps.safety.views.incident import IncidentViewMixin


class IncidentClosureView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_queryset(self):
        queryset = Incident.objects.filter(is_deleted=False, state="CLOSED")
        return self._apply_filters(queryset)

    def get(self, request, *args, **kwargs):
        incident = self.get_object()
        phase_logs = IncidentPhaseLog.objects.filter(incident_id=incident.pk).order_by("occurred_at", "id")
        field_history = SafetyFieldHistory.objects.filter(
            parent_table="vims_safety_incident",
            parent_id=incident.pk,
        ).order_by("changed_at", "id")

        latest_phase_log = phase_logs.last()
        incident_identifier = str(incident.id)

        return Response(
            {
                "incident": IncidentSerializer(incident, context=self.get_serializer_context()).data,
                "phase_logs": PhaseLogSerializer(phase_logs, many=True).data,
                "field_history": FieldHistorySerializer(field_history, many=True).data,
                "signature_chain": SignatureChainService().signature_status(incident),
                "exports": {
                    "incident_pdf": {
                        "available": True,
                        "endpoint": f"/api/safety/export/incident/{incident_identifier}/pdf/",
                    },
                    "msc_mepc3": {
                        "available": bool(incident.imo_classifier and incident.imo_classifier != Incident.ImoClassifier.NOT_APPLICABLE),
                        "endpoint": f"/api/safety/export/msc-mepc-3/{incident_identifier}/",
                    },
                    "auditor_zip": {
                        "available": True,
                        "endpoint": f"/api/safety/export/auditor-bundle/?incident_id={incident_identifier}",
                    },
                },
                "audit_summary": {
                    "phase_log_count": phase_logs.count(),
                    "field_history_count": field_history.count(),
                    "latest_phase_log": (
                        PhaseLogSerializer(latest_phase_log).data if latest_phase_log is not None else None
                    ),
                    "latest_field_change": (
                        FieldHistorySerializer(field_history.last()).data if field_history.exists() else None
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )
