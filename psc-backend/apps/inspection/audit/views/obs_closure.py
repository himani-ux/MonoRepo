"""Audit Observation closure API views."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.permissions import (
    AUDIT_P_008,
    audit_process_ids_for_request,
    user_can_access_audit_detail,
)
from apps.inspection.audit.serializers.obs_closure import PART_SERIALIZERS
from apps.inspection.audit.services.car_workflow import AuditCarWorkflowError
from apps.inspection.audit.services.obs_closure import (
    AuditObsClosureError,
    get_obs_closure_bundle,
    serialize_obs_closure_bundle,
    update_obs_part,
)


def _forbidden(message: str) -> Response:
    return Response(
        {
            "error": "FORBIDDEN",
            "message": message,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _error_response(exc: AuditCarWorkflowError | AuditObsClosureError) -> Response:
    if isinstance(exc, AuditCarWorkflowError):
        return Response(
            {
                "error": exc.error,
                "message": str(exc),
            },
            status=exc.status_code,
        )
    return Response(
        {
            "error": "AUDIT_OBS_CLOSURE_VALIDATION",
            "message": str(exc),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


class AuditFindingObsClosureView(APIView):
    """GET /api/audit/findings/{id}/obs/ for the KSM-F-OBS-001 closure record."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            bundle = get_obs_closure_bundle(id, user=request.user)
        except (AuditCarWorkflowError, AuditObsClosureError) as exc:
            return _error_response(exc)

        if not user_can_access_audit_detail(request.user, bundle.audit_detail):
            return _forbidden("You do not have access to this audit.")
        return Response({"data": serialize_obs_closure_bundle(bundle)})


class AuditFindingObsPartView(APIView):
    """PUT /api/audit/findings/{id}/obs/{part}/ for Part B-D saves."""

    permission_classes = [IsAuthenticated]
    part_name = ""

    def put(self, request, id):
        serializer_class = PART_SERIALIZERS[self.part_name]
        serializer = serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            bundle = get_obs_closure_bundle(id, user=request.user)
        except (AuditCarWorkflowError, AuditObsClosureError) as exc:
            return _error_response(exc)

        if not user_can_access_audit_detail(request.user, bundle.audit_detail):
            return _forbidden("You do not have access to this audit.")
        if self.part_name == "part-b" and AUDIT_P_008 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to close Audit Observation Part B.")

        try:
            updated = update_obs_part(
                finding_id=id,
                part=self.part_name,
                data=serializer.validated_data,
                user=request.user,
            )
        except (AuditCarWorkflowError, AuditObsClosureError) as exc:
            return _error_response(exc)

        return Response({"data": serialize_obs_closure_bundle(updated)})
