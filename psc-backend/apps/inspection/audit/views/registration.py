"""Audit registration API views."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.permissions import (
    AUDIT_P_001,
    AUDIT_P_003,
    AUDIT_P_013,
    HasAnyAuditProcessPermission,
    is_office_user,
)
from apps.inspection.audit.serializers.registration import (
    AuditRegistrationResponseSerializer,
    AuditRegistrationSerializer,
)


class AuditRegistrationView(APIView):
    """POST /api/audit/audits/ registration endpoint for internal audits."""

    permission_classes = [
        IsAuthenticated,
        HasAnyAuditProcessPermission.requiring_any(AUDIT_P_001, AUDIT_P_003, AUDIT_P_013),
    ]

    def post(self, request):
        is_external = request.data.get("audit_classification") == "EXTERNAL"
        if not is_external and not is_office_user(request.user):
            return Response(
                {
                    "error": "FORBIDDEN",
                    "message": "Audit registration is restricted to office users.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AuditRegistrationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        response_serializer = AuditRegistrationResponseSerializer(result)
        return Response(
            {
                "data": response_serializer.data,
                "message": "Audit registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )
