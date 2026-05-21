from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.serializers import SOIChecklistVersionSerializer
from apps.safety.services.checklist_version_resolver import ChecklistVersionResolutionError
from apps.safety.views.soi import SOIViewMixin


class SOIActiveChecklistVersionView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIChecklistVersionSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.create_process_permission_class()]

    def get(self, request, *args, **kwargs):
        try:
            version = self.get_checklist_version_resolver().get_active_version()
        except ChecklistVersionResolutionError:
            return Response(None)
        serializer = self.get_serializer(version)
        return Response(serializer.data)
