from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import SOIFinding, SOIInspection
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers import (
    SOIFindingApprovalSerializer,
    SOIFindingPendingClosureSerializer,
    SOIFindingReopenSerializer,
    SOIFindingSerializer,
)
from apps.safety.services.finding_closure import FindingClosureService
from apps.safety.views.soi_finding import SOIFindingViewMixin


class SOIFindingClosureMixin(SOIFindingViewMixin):
    pending_process_permission_class = HasProcessPermission.requiring("SAF_P_014")
    approve_process_permission_class = HasProcessPermission.requiring("SAF_P_015")
    reopen_process_permission_class = HasProcessPermission.requiring("SAF_P_008")
    finding_closure_service_class = FindingClosureService

    def get_finding_closure_service(self) -> FindingClosureService:
        return self.finding_closure_service_class()

    def get_finding(self, finding_id: int | str) -> SOIFinding:
        inspection_ids = self._apply_filters(
            SOIInspection.objects.filter(is_deleted=False)
        ).values("id")
        return get_by_public_id_or_pk(
            SOIFinding.objects.filter(is_deleted=False, inspection_id__in=inspection_ids),
            finding_id,
        )

    def get_inspection_for_finding(self, finding: SOIFinding) -> SOIInspection:
        return get_object_or_404(
            self._apply_filters(SOIInspection.objects.filter(is_deleted=False)),
            pk=finding.inspection_id,
        )


class SOIFindingDetailView(SOIFindingClosureMixin, generics.GenericAPIView):
    def get_permissions(self):
        return [self.form_permission_class()]

    def get(self, request, *args, **kwargs):
        finding = self.get_finding(kwargs["finding_id"])
        serializer = SOIFindingSerializer(
            finding,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class SOIFindingPendingClosureView(SOIFindingClosureMixin, generics.GenericAPIView):
    serializer_class = SOIFindingPendingClosureSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.pending_process_permission_class()]

    def post(self, request, *args, **kwargs):
        finding = self.get_finding(kwargs["finding_id"])
        inspection = self.get_inspection_for_finding(finding)
        self._ensure_safety_officer_gate(vessel_id=str(inspection.vessel_id))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transition = self.get_finding_closure_service().mark_pending_closure(
            finding=finding,
            user=request.user,
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
            closure_note=serializer.validated_data.get("closure_note"),
        )
        response_serializer = SOIFindingSerializer(
            finding,
            context=self.get_serializer_context(),
        )
        payload = dict(response_serializer.data)
        payload["transition"] = transition
        return Response(payload, status=status.HTTP_200_OK)


class SOIFindingApproveClosureView(SOIFindingClosureMixin, generics.GenericAPIView):
    serializer_class = SOIFindingApprovalSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.approve_process_permission_class()]

    def post(self, request, *args, **kwargs):
        finding = self.get_finding(kwargs["finding_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = str(serializer.validated_data["decision"]).strip().upper()
        service = self.get_finding_closure_service()
        if decision == "APPROVE":
            transition = service.approve_closure(
                finding=finding,
                user=request.user,
                typed_name=serializer.validated_data["typed_name"],
                device_fingerprint=serializer.validated_data["device_fingerprint"],
                closure_note=serializer.validated_data.get("closure_note"),
            )
        else:
            transition = service.reject_closure(
                finding=finding,
                user=request.user,
                reason=serializer.validated_data["reason"],
            )
        response_serializer = SOIFindingSerializer(
            finding,
            context=self.get_serializer_context(),
        )
        payload = dict(response_serializer.data)
        payload["transition"] = transition
        return Response(payload, status=status.HTTP_200_OK)


class SOIFindingReopenView(SOIFindingClosureMixin, generics.GenericAPIView):
    serializer_class = SOIFindingReopenSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.reopen_process_permission_class()]

    def post(self, request, *args, **kwargs):
        finding = self.get_finding(kwargs["finding_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transition = self.get_finding_closure_service().reopen_closed_finding(
            finding=finding,
            user=request.user,
            reason=serializer.validated_data["reason"],
        )
        response_serializer = SOIFindingSerializer(
            finding,
            context=self.get_serializer_context(),
        )
        payload = dict(response_serializer.data)
        payload["transition"] = transition
        return Response(payload, status=status.HTTP_200_OK)
