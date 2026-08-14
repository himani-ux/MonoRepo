"""External audit v1.1 close-out API views."""

from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditDetail
from apps.inspection.audit.permissions import AUDIT_P_013, AUDIT_P_014, audit_process_ids_for_request, user_can_access_audit_detail
from apps.inspection.audit.serializers.detail import AuditDetailResponseSerializer
from apps.inspection.audit.serializers.external import ExternalAuditCloseoutSerializer, ExternalCertLinkEditSerializer
from apps.inspection.audit.services.detail import get_audit_detail_bundle
from apps.inspection.audit.services.external_closeout import (
    ExternalCloseoutError,
    amend_external_cert_links,
    confirm_external_audit_closeout,
)


def _forbidden(message: str) -> Response:
    return Response({"error": "FORBIDDEN", "message": message}, status=status.HTTP_403_FORBIDDEN)


def _error(exc: ExternalCloseoutError) -> Response:
    return Response({"error": exc.error, "message": str(exc)}, status=exc.status_code)


class AuditExternalCloseoutView(APIView):
    """POST /api/audit/audits/{id}/external/close/."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        audit_detail = _get_audit_detail(id)
        if AUDIT_P_013 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to confirm external audit closure.")
        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        serializer = ExternalAuditCloseoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = confirm_external_audit_closeout(
                audit_detail=audit_detail,
                data=serializer.validated_data,
                user=request.user,
            )
        except ExternalCloseoutError as exc:
            return _error(exc)

        bundle = get_audit_detail_bundle(result.audit_detail.id)
        return Response(
            {
                "data": AuditDetailResponseSerializer(bundle).data,
                "outbox_count": len(result.outbox_rows),
                "flag_notification_id": str(result.flag_notification.id) if result.flag_notification else None,
            }
        )


class AuditExternalCertLinkView(APIView):
    """POST /api/audit/audits/{id}/certs/link/."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        audit_detail = _get_audit_detail(id)
        if AUDIT_P_014 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to edit post-closure Certs links.")
        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        serializer = ExternalCertLinkEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rows = amend_external_cert_links(
                audit_detail=audit_detail,
                linked_cert_ids=[str(cert_id) for cert_id in serializer.validated_data["linked_cert_ids"]],
                reason=serializer.validated_data["reason"],
                user=request.user,
            )
        except ExternalCloseoutError as exc:
            return _error(exc)
        bundle = get_audit_detail_bundle(audit_detail.id)
        return Response({"data": AuditDetailResponseSerializer(bundle).data, "outbox_count": len(rows)})


def _get_audit_detail(id):
    try:
        return AuditDetail.objects.get(id=id)
    except AuditDetail.DoesNotExist as exc:
        raise Http404("Audit not found.") from exc

