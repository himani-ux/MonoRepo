"""Audit submit and vessel acknowledgement API views."""

from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditDetail
from apps.inspection.audit.permissions import (
    AUDIT_P_003,
    AUDIT_P_017,
    HasAnyAuditProcessPermission,
    audit_process_ids_for_request,
    is_vessel_user,
    normalized_audit_role,
    user_can_access_audit_detail,
)
from apps.inspection.audit.serializers.detail import AuditDetailResponseSerializer
from apps.inspection.audit.services.detail import get_audit_detail_bundle
from apps.inspection.audit.services.submit_gates import (
    AuditSubmitGateError,
    AuditTransitionError,
    acknowledge_audit_report,
    submit_audit_report,
)


def _forbidden(message: str) -> Response:
    return Response(
        {
            "error": "FORBIDDEN",
            "message": message,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _conflict(message: str) -> Response:
    return Response(
        {
            "error": "INVALID_AUDIT_STATUS",
            "message": message,
        },
        status=status.HTTP_409_CONFLICT,
    )


class AuditSubmitView(APIView):
    """POST /api/audit/audits/{id}/submit/ runs the D-071 gates."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(AUDIT_P_003)]

    def post(self, request, id):
        audit_detail = _get_audit_detail(id)
        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        try:
            updated = submit_audit_report(audit_detail=audit_detail, user=request.user)
        except AuditSubmitGateError as exc:
            return Response(
                {
                    "error": "SUBMIT_GATES_FAILED",
                    "message": "Audit cannot be submitted until all D-071 gates pass.",
                    "gates": exc.gates,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AuditTransitionError as exc:
            return _conflict(str(exc))

        return _detail_response(updated)


class AuditAcknowledgeView(APIView):
    """POST /api/audit/audits/{id}/acknowledge/ records vessel acknowledgement."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        audit_detail = _get_audit_detail(id)
        if AUDIT_P_017 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to acknowledge this audit report.")
        if not _is_master_user(request.user):
            return _forbidden("Only the vessel Master can acknowledge the audit report.")
        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        try:
            updated = acknowledge_audit_report(audit_detail=audit_detail, user=request.user)
        except AuditTransitionError as exc:
            return _conflict(str(exc))

        return _detail_response(updated)


def _get_audit_detail(id):
    try:
        return AuditDetail.objects.get(id=id)
    except AuditDetail.DoesNotExist as exc:
        raise Http404("Audit not found.") from exc


def _detail_response(audit_detail: AuditDetail) -> Response:
    bundle = get_audit_detail_bundle(audit_detail.id)
    return Response({"data": AuditDetailResponseSerializer(bundle).data})


def _is_master_user(user) -> bool:
    return is_vessel_user(user) and normalized_audit_role(user) in {"MASTER", "VESSEL_MASTER"}
