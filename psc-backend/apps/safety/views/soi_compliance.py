from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.serializers import SOIComplianceSerializer
from apps.safety.services.soi_compliance_calculator import SOIComplianceCalculator
from apps.safety.views.soi import SOIViewMixin


class SOIComplianceView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIComplianceSerializer
    compliance_calculator_class = SOIComplianceCalculator

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_compliance_calculator(self) -> SOIComplianceCalculator:
        return self.compliance_calculator_class()

    def get(self, request, *args, **kwargs):
        payload = self.get_compliance_calculator().get_summary(self._resolve_vessel_id())
        serializer = self.get_serializer(payload)
        return Response(serializer.data)
