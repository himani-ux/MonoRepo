from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.serializers import SOITraineePayloadSerializer, SOITraineeUpdateSerializer
from apps.safety.views.soi import SOIViewMixin


class SOITraineeView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOITraineeUpdateSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.create_process_permission_class()]

    def get(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        serializer = SOITraineePayloadSerializer(
            {"inspection_id": inspection.id, "trainees": self.get_soi_repository().list_trainees(inspection.id)}
        )
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "inspection": inspection},
        )
        serializer.is_valid(raise_exception=True)
        payload = serializer.save(inspection_id=inspection.id)
        response_serializer = SOITraineePayloadSerializer(payload)
        return Response(response_serializer.data)
