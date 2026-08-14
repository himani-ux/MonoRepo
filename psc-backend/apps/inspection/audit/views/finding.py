"""Audit finding capture API."""

from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditDetail
from apps.inspection.audit.permissions import (
    AUDIT_P_007,
    AUDIT_P_003,
    HasAnyAuditProcessPermission,
    user_can_access_audit_detail,
)
from apps.inspection.audit.serializers.finding import (
    AuditFindingCreateSerializer,
    AuditFindingResponseSerializer,
)
from apps.inspection.audit.services.finding import (
    AuditFindingStateError,
    AuditFindingValidationError,
    create_audit_finding,
)
from apps.inspection.audit.services.circular_link import (
    AuditCircularLinkValidationError,
    issue_circular_from_finding,
)


def _forbidden(message: str) -> Response:
    return Response(
        {
            "error": "FORBIDDEN",
            "message": message,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


class AuditFindingCreateView(APIView):
    """POST /api/audit/audits/{id}/findings/ for checklist and emergent findings."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(AUDIT_P_003)]

    def post(self, request, id):
        try:
            audit_detail = AuditDetail.objects.get(id=id)
        except AuditDetail.DoesNotExist as exc:
            raise Http404("Audit not found.") from exc

        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        serializer = AuditFindingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = create_audit_finding(
                audit_detail_id=audit_detail.id,
                created_by=_user_id(request.user),
                **serializer.validated_data,
            )
        except AuditFindingStateError as exc:
            return Response(
                {
                    "error": "AUDIT_FINDING_STATE",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except AuditFindingValidationError as exc:
            return Response(
                {
                    "error": "AUDIT_FINDING_VALIDATION",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"data": AuditFindingResponseSerializer(result).data},
            status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
        )


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")


class AuditFindingIssueCircularView(APIView):
    """POST /api/audit/findings/{id}/issue-circular/ for fleet-wide NCs."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(AUDIT_P_007)]

    def post(self, request, id):
        from apps.inspection.audit.models import AuditFinding

        try:
            finding = AuditFinding.objects.get(id=id)
            audit_detail = AuditDetail.objects.get(id=finding.audit_detail_id)
        except (AuditFinding.DoesNotExist, AuditDetail.DoesNotExist) as exc:
            raise Http404("Finding not found.") from exc

        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        try:
            result = issue_circular_from_finding(finding_id=finding.id, user=request.user)
        except AuditCircularLinkValidationError as exc:
            return Response(
                {
                    "error": "AUDIT_CIRCULAR_LINK_VALIDATION",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "data": {
                    "status": result.status,
                    "circular_id": str(result.circular_id),
                    "detail_url": result.detail_url,
                    "payload": result.payload,
                }
            },
            status=status.HTTP_201_CREATED if result.status == "DRAFT_CREATED" else status.HTTP_200_OK,
        )
