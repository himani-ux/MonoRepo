from __future__ import annotations

from rest_framework import serializers, status
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import Incident
from apps.safety.services import FleetAlertIssueError, FleetAlertIssuer
from apps.safety.views.near_miss import NearMissViewMixin, _normalized_role


class FleetAlertIssueSerializer(serializers.Serializer):
    alert_text = serializers.CharField()
    fleet_learning_text = serializers.CharField()
    recipient_vessel_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=False,
    )
    sla_extension_reason = serializers.CharField(required=False, allow_blank=True)
    typed_name = serializers.CharField()
    device_fingerprint = serializers.CharField()

    def validate_alert_text(self, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("Fleet alert text is required.")
        return cleaned

    def validate_fleet_learning_text(self, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("Fleet learning / lessons text is required.")
        return cleaned


class FleetAlertIssueView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = FleetAlertIssueSerializer
    process_permission_class = NearMissViewMixin.process_permission_class.requiring("SAF_P_024")
    fleet_alert_issuer_class = FleetAlertIssuer

    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_fleet_alert_issuer(self) -> FleetAlertIssuer:
        return self.fleet_alert_issuer_class()

    def get_object(self):
        near_miss = super().get_object()
        issuer = self.get_fleet_alert_issuer()
        try:
            issuer.build_status(near_miss, user=self.request.user)
        except FleetAlertIssueError as exc:
            raise ValidationError(str(exc)) from exc
        return near_miss

    def _enforce_dpa_role(self) -> None:
        if _normalized_role(self.request.user) != "DPA":
            raise PermissionDenied("Fleet alert issuance is restricted to DPA.")

    def get(self, request, *args, **kwargs):
        near_miss = self.get_object()
        self._enforce_dpa_role()
        payload = self.get_fleet_alert_issuer().build_workspace_payload(near_miss, user=request.user)
        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        near_miss = self.get_object()
        self._enforce_dpa_role()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = self.get_fleet_alert_issuer().issue_fleet_alert(
                near_miss,
                alert_text=serializer.validated_data["alert_text"],
                device_fingerprint=serializer.validated_data["device_fingerprint"],
                fleet_learning_text=serializer.validated_data["fleet_learning_text"],
                recipient_vessel_ids=serializer.validated_data.get("recipient_vessel_ids"),
                sla_extension_reason=serializer.validated_data.get("sla_extension_reason", ""),
                typed_name=serializer.validated_data["typed_name"],
                user=request.user,
            )
        except FleetAlertIssueError as exc:
            raise ValidationError(str(exc)) from exc

        response_payload = self.get_fleet_alert_issuer().build_workspace_payload(near_miss, user=request.user)
        response_payload.update(payload)
        return Response(response_payload, status=status.HTTP_200_OK)
