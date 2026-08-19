"""Gated operational Audit master-data APIs."""

from __future__ import annotations

from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import (
    MasterAuditQualifiedAuditor,
    MasterExternalAuditOrg,
    VesselAuditRoDelegation,
)
from apps.inspection.audit.permissions import (
    AUDIT_P_009,
    AUDIT_P_019,
    AUDIT_P_020,
    HasAuditProcessPermission,
)
from apps.inspection.audit.serializers.masters import (
    ExternalAuditOrgSerializer,
    QualifiedAuditorSerializer,
    VesselRoDelegationSerializer,
)


def _actor_id(request) -> str:
    return str(getattr(request.user, "id", "") or getattr(request.user, "username", "") or "system")


def _forbidden(message: str) -> Response:
    return Response({"error": "FORBIDDEN", "message": message}, status=status.HTTP_403_FORBIDDEN)


class _MasterListCreateView(APIView):
    serializer_class = None
    model = None
    process_id = None
    active_field = None

    def get_queryset(self):
        queryset = self.model.objects.all().order_by("id")
        include_inactive = str(self.request.query_params.get("include_inactive", "false")).lower() in {
            "1",
            "true",
            "yes",
        }
        if self.active_field and not include_inactive:
            queryset = queryset.filter(**{self.active_field: True})
        return queryset

    def get(self, request):
        rows = self.serializer_class(self.get_queryset(), many=True).data
        return Response({"data": {"count": len(rows), "results": rows}})

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            instance = serializer.save(created_by=_actor_id(request))
        return Response({"data": self.serializer_class(instance).data}, status=status.HTTP_201_CREATED)


class _MasterDetailView(APIView):
    serializer_class = None
    model = None
    process_id = None
    active_field = None

    def _get_instance(self, id):
        try:
            return self.model.objects.get(id=id)
        except self.model.DoesNotExist as exc:
            raise Http404("Audit master record not found.") from exc

    def get(self, request, id):
        return Response({"data": self.serializer_class(self._get_instance(id)).data})

    def patch(self, request, id):
        instance = self._get_instance(id)
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_fields = list(serializer.validated_data)
        if hasattr(instance, "updated_by"):
            serializer.validated_data["updated_by"] = _actor_id(request)
            serializer.validated_data["updated_date"] = timezone.now()
            update_fields.extend(["updated_by", "updated_date"])
        serializer.save()
        return Response({"data": self.serializer_class(instance).data})


class QualifiedAuditorListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_009)]
    serializer_class = QualifiedAuditorSerializer
    model = MasterAuditQualifiedAuditor
    process_id = AUDIT_P_009
    active_field = "is_active"


class QualifiedAuditorDetailView(_MasterDetailView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_009)]
    serializer_class = QualifiedAuditorSerializer
    model = MasterAuditQualifiedAuditor
    process_id = AUDIT_P_009


class ExternalAuditOrgListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_019)]
    serializer_class = ExternalAuditOrgSerializer
    model = MasterExternalAuditOrg
    process_id = AUDIT_P_019
    active_field = "is_active"


class ExternalAuditOrgDetailView(_MasterDetailView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_019)]
    serializer_class = ExternalAuditOrgSerializer
    model = MasterExternalAuditOrg
    process_id = AUDIT_P_019


class VesselRoDelegationListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_020)]
    serializer_class = VesselRoDelegationSerializer
    model = VesselAuditRoDelegation
    process_id = AUDIT_P_020

    def get_queryset(self):
        queryset = super().get_queryset()
        vessel_id = self.request.query_params.get("target_vessel_id")
        standard_code = self.request.query_params.get("standard_code")
        if vessel_id:
            queryset = queryset.filter(target_vessel_id=vessel_id)
        if standard_code:
            queryset = queryset.filter(standard_code=standard_code.strip().upper())
        return queryset


class VesselRoDelegationDetailView(_MasterDetailView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_020)]
    serializer_class = VesselRoDelegationSerializer
    model = VesselAuditRoDelegation
    process_id = AUDIT_P_020
