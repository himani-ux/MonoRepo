from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.serializers import SOIClosePayloadSerializer, SOICloseSnapshotSerializer
from apps.safety.services import SOICloseService
from apps.safety.views.soi import SOIViewMixin


class SOICloseView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIClosePayloadSerializer
    close_process_permission_class = HasProcessPermission.requiring("SAF_P_004")
    close_service_class = SOICloseService

    def get_permissions(self):
        return [self.form_permission_class(), self.close_process_permission_class()]

    def get_close_service(self) -> SOICloseService:
        return self.close_service_class()

    def get(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"MASTER"},
            message="SOI close is restricted to Master (D-GAP-M15).",
        )
        inspection = self.get_inspection(kwargs["id"])
        payload = self.get_close_service().get_close_snapshot(inspection=inspection)
        serializer = SOICloseSnapshotSerializer(payload)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"MASTER"},
            message="SOI close is restricted to Master (D-GAP-M15).",
        )
        inspection = self.get_inspection(kwargs["id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.get_close_service().close_inspection(
            inspection=inspection,
            user=request.user,
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
        )
        response_serializer = SOICloseSnapshotSerializer(payload)
        return Response(response_serializer.data)
