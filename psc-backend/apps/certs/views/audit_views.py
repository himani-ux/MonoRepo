from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    AUDIT_LOG_FORM_ID,
    PRINT_PROCESS_ID,
    HasAuditLogReadPermission,
    audit_log_vessel_scope,
    has_request_certs_perm,
    normalized_role,
)
from apps.certs.serializers.audit import serialize_audit_event
from apps.certs.serializers.print import serialize_print_artifact
from apps.certs.services.audit_export import AuditLogExportService
from apps.certs.services.audit_log import record_audit_event
from apps.certs.services.audit_log_repository import AuditLogRepository


repository = AuditLogRepository()
export_service = AuditLogExportService(audit_repository=repository)


class AuditLogListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasAuditLogReadPermission]

    def get(self, request, *args, **kwargs):
        page = repository.list_events(
            filters=_audit_filters(request),
            vessel_scope=audit_log_vessel_scope(request.user),
        )
        return Response(
            {
                "count": page.count,
                "page": page.page,
                "pageSize": page.page_size,
                "includesColdTier": page.includes_cold_tier,
                "results": [serialize_audit_event(row) for row in page.results],
            }
        )


class AuditLogDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasAuditLogReadPermission]

    def get(self, request, audit_id: str, *args, **kwargs):
        row = repository.get_event(str(audit_id), vessel_scope=audit_log_vessel_scope(request.user))
        if row is None:
            return Response({"detail": "Audit log entry not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_audit_event(row))


class AuditLogExportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasAuditLogReadPermission]

    def post(self, request, *args, **kwargs):
        if not has_request_certs_perm(request, AUDIT_LOG_FORM_ID, PRINT_PROCESS_ID):
            return Response({"detail": "Only DPA may export the Certs audit log."}, status=status.HTTP_403_FORBIDDEN)
        if normalized_role(request.user) != "DPA":
            return Response({"detail": "Only DPA may export the Certs audit log."}, status=status.HTTP_403_FORBIDDEN)
        filters = request.data.get("filters") if isinstance(request.data, dict) else {}
        if filters is None:
            filters = {}
        if not isinstance(filters, dict):
            return Response({"detail": "Audit export filters must be an object."}, status=status.HTTP_400_BAD_REQUEST)
        row = export_service.export(filters=filters, actor=request.user)
        serialized = serialize_print_artifact(row)
        record_audit_event(
            actor=request.user,
            action="print",
            entity_type="print_artifact",
            entity_id=serialized["printId"],
            vessel_id=_single_vessel_id(serialized["vessels"]),
            before=None,
            after={
                "printId": serialized["printId"],
                "scope": serialized["scope"],
                "filters": serialized["filters"],
                "watermarkApplied": serialized["watermarkApplied"],
                "pdfBlobId": serialized["pdfBlobId"],
                "csvBlobId": serialized["excelBlobId"],
                "systemStateHash": serialized["systemStateHash"],
            },
            reason="Exported Certs audit log.",
            metadata={"source": "api.certs.audit_log.export", "format": ["pdf", "csv"]},
        )
        return Response(serialized, status=status.HTTP_201_CREATED)


def _audit_filters(request) -> dict[str, str]:
    keys = (
        "vesselId",
        "actorUserId",
        "action",
        "entityType",
        "retentionTier",
        "dateFrom",
        "dateTo",
        "page",
        "pageSize",
    )
    return {key: request.query_params.get(key, "") for key in keys}


def _single_vessel_id(vessel_ids: list[str]) -> str | None:
    return vessel_ids[0] if len(vessel_ids) == 1 else None
