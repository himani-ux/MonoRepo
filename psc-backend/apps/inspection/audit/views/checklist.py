"""Audit checklist master API views."""

from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditDetail
from apps.inspection.audit.permissions import user_can_access_audit_detail
from apps.inspection.audit.serializers.checklist import AuditChecklistResponseSerializer
from apps.inspection.audit.services.checklist import get_audit_checklist_bundle


class AuditChecklistMasterView(APIView):
    """GET /api/audit/masters/checklists/?audit_id={id}."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        audit_id = request.query_params.get("audit_id")
        if not audit_id:
            return Response(
                {
                    "error": "AUDIT_ID_REQUIRED",
                    "message": "audit_id query parameter is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            audit_detail = AuditDetail.objects.get(id=audit_id)
        except (AuditDetail.DoesNotExist, ValueError) as exc:
            raise Http404("Audit not found.") from exc

        if not user_can_access_audit_detail(request.user, audit_detail):
            return Response(
                {
                    "error": "FORBIDDEN",
                    "message": "You do not have access to this audit.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        bundle = get_audit_checklist_bundle(
            audit_detail_id=audit_detail.id,
            ship_type=request.query_params.get("ship_type"),
        )
        return Response({"data": AuditChecklistResponseSerializer(bundle).data})
