"""DPA scan-validation queue API views."""

from __future__ import annotations

from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditAttachment
from apps.inspection.audit.permissions import CanValidateAuditScan, is_office_user, normalized_audit_role
from apps.inspection.audit.serializers.scan_validation import (
    AuditScanValidationActionSerializer,
    AuditScanValidationQueueSerializer,
)
from apps.inspection.audit.services.pdf_validation import (
    accept_scan_with_reason,
    reject_scan_for_rescan,
    scan_validation_queue_queryset,
    validate_uploaded_scan,
)


def _forbidden(message: str) -> Response:
    return Response({"error": "FORBIDDEN", "message": message}, status=status.HTTP_403_FORBIDDEN)


def _is_dpa_user(user: object) -> bool:
    return is_office_user(user) and normalized_audit_role(user) == "DPA"


class AuditScanValidationQueueView(APIView):
    """GET /api/audit/dpa/scan-validation-queue/ for unresolved scan mismatches."""

    permission_classes = [IsAuthenticated, CanValidateAuditScan]

    def get(self, request):
        if not _is_dpa_user(request.user):
            return _forbidden("Scan validation queue resolution is DPA-only.")

        queryset = scan_validation_queue_queryset()
        rows = AuditScanValidationQueueSerializer(list(queryset), many=True).data
        return Response({"data": {"count": len(rows), "results": rows}})


class AuditAttachmentValidateView(APIView):
    """POST /api/audit/attachments/{id}/validate/ for validation and DPA adjudication."""

    permission_classes = [IsAuthenticated, CanValidateAuditScan]

    def post(self, request, id):
        if not _is_dpa_user(request.user):
            return _forbidden("Scan validation queue resolution is DPA-only.")

        attachment = _get_attachment(id)
        payload = dict(request.data)
        if "action" not in payload:
            payload["action"] = "VALIDATE"
        serializer = AuditScanValidationActionSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        if action == "VALIDATE":
            result = validate_uploaded_scan(
                attachment,
                decoded_qr_payload=serializer.validated_data.get("qr_payload"),
            )
            attachment = result.attachment
            message = result.message
        elif action == "ACCEPT_WITH_REASON":
            attachment = accept_scan_with_reason(
                attachment,
                reason=serializer.validated_data["reason"],
                user=request.user,
            )
            message = "Scan mismatch accepted with DPA reason."
        else:
            attachment = reject_scan_for_rescan(
                attachment,
                reason=serializer.validated_data.get("reason"),
                user=request.user,
            )
            message = "Scan rejected and rescan requested."

        return Response(
            {
                "data": AuditScanValidationQueueSerializer(attachment).data,
                "message": message,
            }
        )


def _get_attachment(id):
    try:
        return AuditAttachment.objects.get(id=id)
    except AuditAttachment.DoesNotExist as exc:
        raise Http404("Audit attachment not found.") from exc


__all__ = [
    "AuditAttachmentValidateView",
    "AuditScanValidationQueueView",
]
