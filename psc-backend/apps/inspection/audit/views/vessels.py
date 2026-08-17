"""Audit vessel option API views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.services.vessels import list_audit_vessel_options


class AuditVesselOptionListView(APIView):
    """GET /api/audit/vessels/ returns readable vessel options for Audit forms."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"data": list_audit_vessel_options(user=request.user)})
