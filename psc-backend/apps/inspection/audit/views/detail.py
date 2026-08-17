"""Audit detail API views."""

from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditDetail
from apps.inspection.audit.permissions import (
    AUDIT_P_002,
    AUDIT_P_003,
    audit_effective_process_ids_for_request,
    request_has_audit_detail_process_id,
    user_can_access_audit_detail,
)
from apps.inspection.audit.serializers.detail import (
    AuditDetailPatchSerializer,
    AuditDetailResponseSerializer,
    AuditScorecardSerializer,
)
from apps.inspection.audit.services.detail import (
    get_audit_detail_bundle,
    update_audit_detail_fields,
    upsert_scorecard_rows,
)


def _forbidden(message: str) -> Response:
    return Response(
        {
            "error": "FORBIDDEN",
            "message": message,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


class AuditDetailView(APIView):
    """GET/PATCH /api/audit/audits/{id}/ for the F602 detail shell."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        audit_detail = self._get_audit_detail(id)
        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")
        return self._detail_response(audit_detail, request)

    def patch(self, request, id):
        audit_detail = self._get_audit_detail(id)
        if not request_has_audit_detail_process_id(request, audit_detail, AUDIT_P_002):
            return _forbidden("You do not have permission to edit this audit.")
        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        serializer = AuditDetailPatchSerializer(
            data=request.data,
            partial=True,
            context={"audit_detail": audit_detail},
        )
        serializer.is_valid(raise_exception=True)
        update_audit_detail_fields(
            audit_detail=audit_detail,
            data=serializer.validated_data,
            user=request.user,
        )
        return self._detail_response(audit_detail, request)

    def _get_audit_detail(self, id):
        try:
            return AuditDetail.objects.get(id=id)
        except AuditDetail.DoesNotExist as exc:
            raise Http404("Audit not found.") from exc

    def _detail_response(self, audit_detail: AuditDetail, request) -> Response:
        bundle = get_audit_detail_bundle(audit_detail.id)
        data = AuditDetailResponseSerializer(bundle).data
        data["effective_permissions"] = sorted(audit_effective_process_ids_for_request(request, audit_detail))
        return Response({"data": data})


class AuditScorecardView(APIView):
    """PUT /api/audit/audits/{id}/scorecard/ for the 14-area scorecard."""

    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            audit_detail = AuditDetail.objects.get(id=id)
        except AuditDetail.DoesNotExist as exc:
            raise Http404("Audit not found.") from exc

        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")
        if not request_has_audit_detail_process_id(request, audit_detail, AUDIT_P_003):
            return _forbidden("You do not have permission to update this audit scorecard.")

        serializer = AuditScorecardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upsert_scorecard_rows(
            audit_detail=audit_detail,
            rows=serializer.validated_data["rows"],
            user=request.user,
        )
        bundle = get_audit_detail_bundle(audit_detail.id)
        data = AuditDetailResponseSerializer(bundle).data
        data["effective_permissions"] = sorted(audit_effective_process_ids_for_request(request, audit_detail))
        return Response({"data": data})
