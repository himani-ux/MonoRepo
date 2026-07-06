from __future__ import annotations

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    CATALOG_EDIT_PROCESS_ID,
    TRACKED_ITEM_FORM_ID,
    has_request_certs_perm,
    normalized_role,
    user_can_access_vessel,
)
from apps.certs.serializers.vessel_lifecycle import (
    VesselClassChangeSerializer,
    VesselDecommissionSerializer,
    VesselFlagChangeSerializer,
    VesselSaleHandoverSerializer,
    serialize_lifecycle_result,
    serialize_vessel_config,
)
from apps.certs.services.audit_log import record_audit_event
from apps.certs.services.print_artifacts import PrintArtifactService, PrintGenerationFailed
from apps.certs.services.vessel_lifecycle import VesselLifecycleRepository


repository = VesselLifecycleRepository()
service = PrintArtifactService()
DPA_LIFECYCLE_ROLES = {"DPA", "SEQ MANAGER", "ADMIN", "SUPER ADMIN", "SYSTEM ADMIN"}


class VesselLifecycleWriteMixin:
    serializer_class = VesselDecommissionSerializer
    audit_action = ""
    audit_source = ""

    def _has_write_permission(self, request) -> bool:
        return (
            has_request_certs_perm(request, TRACKED_ITEM_FORM_ID, CATALOG_EDIT_PROCESS_ID)
            and normalized_role(request.user) in DPA_LIFECYCLE_ROLES
        )

    def _permission_error(self, detail: str = "Only DPA may update Certs vessel lifecycle events.") -> Response:
        return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)

    def _profile_or_error(self, request, imo: str) -> tuple[dict | None, Response | None]:
        profile = repository.get_profile(str(imo))
        if profile is None:
            return None, Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str((profile.get("vessel") or {}).get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return None, Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        return profile, None

    def _record_audit(self, *, request, result: dict, reason: str, metadata: dict) -> None:
        vessel_id = str(((result.get("vessel") or {}).get("vessel_id")) or "")
        record_audit_event(
            actor=request.user,
            action=self.audit_action,
            entity_type="vessel_config",
            entity_id=vessel_id,
            vessel_id=vessel_id,
            before=serialize_vessel_config(result.get("before")),
            after=serialize_vessel_config(result.get("after")),
            reason=reason,
            metadata={"source": self.audit_source, **metadata},
        )


class VesselProfileView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, imo: str, *args, **kwargs):
        if not has_request_certs_perm(request, TRACKED_ITEM_FORM_ID):
            return Response({"detail": "You do not have access to Certs vessel profiles."}, status=status.HTTP_403_FORBIDDEN)
        profile = repository.get_profile(str(imo))
        if profile is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str((profile.get("vessel") or {}).get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        return Response(serialize_lifecycle_result(profile))


class VesselFlagChangeView(VesselLifecycleWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VesselFlagChangeSerializer
    audit_action = "flag_change_event"
    audit_source = "api.certs.vessel.flag_change"

    def post(self, request, imo: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return self._permission_error()
        _, error = self._profile_or_error(request, imo)
        if error:
            return error
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            result = repository.record_flag_change(vessel_identifier=str(imo), values=dict(serializer.validated_data), actor=request.user)
            if result is None:
                return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
            self._record_audit(
                request=request,
                result=result,
                reason=serializer.validated_data["reason"],
                metadata={"affectedTrackedItems": int(result.get("affected_tracked_items") or 0)},
            )
        return Response(serialize_lifecycle_result(result))


class VesselClassChangeView(VesselLifecycleWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VesselClassChangeSerializer
    audit_action = "class_change_event"
    audit_source = "api.certs.vessel.class_change"

    def post(self, request, imo: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return self._permission_error()
        _, error = self._profile_or_error(request, imo)
        if error:
            return error
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            result = repository.record_class_change(vessel_identifier=str(imo), values=dict(serializer.validated_data), actor=request.user)
            if result is None:
                return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
            self._record_audit(
                request=request,
                result=result,
                reason=serializer.validated_data["reason"],
                metadata={"affectedTrackedItems": int(result.get("affected_tracked_items") or 0)},
            )
        return Response(serialize_lifecycle_result(result))


class VesselSaleHandoverView(VesselLifecycleWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VesselSaleHandoverSerializer
    audit_action = "sale_initiated"
    audit_source = "api.certs.vessel.sale_handover"

    def post(self, request, imo: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return self._permission_error()
        profile, error = self._profile_or_error(request, imo)
        if error:
            return error
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vessel_id = str((profile.get("vessel") or {}).get("vessel_id") or "")
        custom_cert_ids = [str(value) for value in serializer.validated_data.get("customCertIds") or []]
        if not custom_cert_ids:
            custom_cert_ids = repository.list_bundle_tracked_item_ids(vessel_id=vessel_id)
        payload = {
            "scope": "share_bundle",
            "vesselIds": [vessel_id],
            "sections": [],
            "filters": {},
            "customCertIds": custom_cert_ids,
            "watermarkApplied": "MASTER_COPY",
            "watermarkRecipient": serializer.validated_data.get("watermarkRecipient") or "Sale handover",
            "recipientEmail": "",
        }
        try:
            artifact = service.generate_share_bundle(payload=payload, actor=request.user)
        except PrintGenerationFailed as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            result = repository.record_sale_handover(
                vessel_identifier=str(imo),
                values=dict(serializer.validated_data),
                actor=request.user,
                artifact=artifact,
            )
            if result is None:
                return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
            self._record_audit(
                request=request,
                result=result,
                reason=serializer.validated_data["reason"],
                metadata={
                    "handoverDate": serializer.validated_data["handoverDate"],
                    "affectedTrackedItems": int(result.get("affected_tracked_items") or 0),
                    "printId": artifact.get("print_id"),
                    "bundleZipBlobId": str(artifact.get("bundle_zip_blob_id")) if artifact.get("bundle_zip_blob_id") else None,
                    "systemStateHash": artifact.get("system_state_hash"),
                },
            )
        return Response(serialize_lifecycle_result(result))


class VesselDecommissionView(VesselLifecycleWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VesselDecommissionSerializer
    audit_action = "decommission"
    audit_source = "api.certs.vessel.decommission"

    def post(self, request, imo: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return self._permission_error()
        _, error = self._profile_or_error(request, imo)
        if error:
            return error
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            result = repository.record_decommission(vessel_identifier=str(imo), values=dict(serializer.validated_data), actor=request.user)
            if result is None:
                return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
            self._record_audit(
                request=request,
                result=result,
                reason=serializer.validated_data["reason"],
                metadata={
                    "decommissionDate": serializer.validated_data["decommissionDate"],
                    "affectedTrackedItems": int(result.get("affected_tracked_items") or 0),
                },
            )
        return Response(serialize_lifecycle_result(result))
