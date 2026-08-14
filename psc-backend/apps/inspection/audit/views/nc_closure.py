"""Audit NC closure API views."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.permissions import (
    AUDIT_P_003,
    AUDIT_P_004,
    audit_process_ids_for_request,
    user_can_access_audit_detail,
)
from apps.inspection.audit.serializers.nc_closure import AuditNcDraftSerializer, PART_SERIALIZERS
from apps.inspection.audit.services.car_workflow import AuditCarWorkflowError
from apps.inspection.audit.services.nc_closure import (
    AuditNcClosureError,
    draft_nc_for_vessel,
    get_nc_closure_bundle,
    serialize_nc_closure_bundle,
    update_nc_part,
)


def _forbidden(message: str) -> Response:
    return Response(
        {
            "error": "FORBIDDEN",
            "message": message,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _error_response(exc: AuditCarWorkflowError | AuditNcClosureError) -> Response:
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
            "error": "AUDIT_NC_CLOSURE_VALIDATION",
            "message": str(exc),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


class AuditFindingNcClosureView(APIView):
    """GET /api/audit/findings/{id}/nc/ for the KSM-F-NC-001 closure record."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            bundle = get_nc_closure_bundle(id, user=request.user)
        except (AuditCarWorkflowError, AuditNcClosureError) as exc:
            return _error_response(exc)

        if not user_can_access_audit_detail(request.user, bundle.audit_detail):
            return _forbidden("You do not have access to this audit.")
        return Response({"data": serialize_nc_closure_bundle(bundle)})


class AuditFindingNcPartView(APIView):
    """PUT /api/audit/findings/{id}/nc/{part}/ for Part B-G saves."""

    permission_classes = [IsAuthenticated]
    part_name = ""

    def put(self, request, id):
        serializer_class = PART_SERIALIZERS[self.part_name]
        serializer = serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            bundle = get_nc_closure_bundle(id, user=request.user)
        except (AuditCarWorkflowError, AuditNcClosureError) as exc:
            return _error_response(exc)

        if not user_can_access_audit_detail(request.user, bundle.audit_detail):
            return _forbidden("You do not have access to this audit.")
        if self.part_name in {"part-e", "part-f", "part-g"} and AUDIT_P_004 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to close Audit NC Parts E/F/G.")

        try:
            updated = update_nc_part(
                finding_id=id,
                part=self.part_name,
                data=serializer.validated_data,
                user=request.user,
            )
        except (AuditCarWorkflowError, AuditNcClosureError) as exc:
            return _error_response(exc)

        return Response({"data": serialize_nc_closure_bundle(updated)})


class AuditFindingNcDraftView(APIView):
    """POST /api/audit/findings/{id}/nc/draft/ for office-led Part B/C drafting."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        serializer = AuditNcDraftSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            bundle = get_nc_closure_bundle(id, user=request.user)
        except (AuditCarWorkflowError, AuditNcClosureError) as exc:
            return _error_response(exc)

        if not user_can_access_audit_detail(request.user, bundle.audit_detail):
            return _forbidden("You do not have access to this audit.")
        if AUDIT_P_003 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to draft Audit NC Parts B/C for the vessel.")

        try:
            updated = draft_nc_for_vessel(
                finding_id=id,
                data=serializer.validated_data,
                user=request.user,
            )
        except (AuditCarWorkflowError, AuditNcClosureError) as exc:
            return _error_response(exc)

        return Response({"data": serialize_nc_closure_bundle(updated)})
