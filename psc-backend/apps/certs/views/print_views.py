from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    EXPORT_BUNDLE_PROCESS_ID,
    PRINT_EXPORT_FORM_ID,
    PRINT_PROCESS_ID,
    has_request_certs_perm,
    is_master_user,
    normalized_role,
    user_can_access_vessel,
)
from apps.certs.serializers.print import (
    PrintArtifactRequestSerializer,
    ShareBundleRequestSerializer,
    serialize_print_artifact,
)
from apps.certs.services.audit_log import record_audit_event
from apps.certs.services.print_artifacts import PrintGenerationFailed, PrintArtifactRepository, PrintArtifactService


repository = PrintArtifactRepository()
service = PrintArtifactService(repository=repository)
FLEET_SCOPE_ROLES = {"DPA", "FM", "FLEET MANAGER", "SUPER ADMIN", "SYSTEM ADMIN"}


class PrintArtifactCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PrintArtifactRequestSerializer

    def post(self, request, *args, **kwargs):
        if not has_request_certs_perm(request, PRINT_EXPORT_FORM_ID, PRINT_PROCESS_ID):
            return Response({"detail": "You do not have access to generate Certs prints."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        access_error = _scope_access_error(request.user, payload)
        if access_error:
            return access_error
        try:
            row = service.generate_print(payload=payload, actor=request.user)
        except PrintGenerationFailed as exc:
            serialized = serialize_print_artifact(exc.artifact)
            return Response({"detail": serialized["failureMessage"], "artifact": serialized}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serialized = serialize_print_artifact(row)
        record_audit_event(
            actor=request.user,
            action="print_artifact_created",
            entity_type="print_artifact",
            entity_id=serialized["printId"],
            vessel_id=_single_vessel_id(serialized["vessels"]),
            before=None,
            after=_artifact_audit_payload(serialized),
            reason="Generated SQE S 633 print artifact.",
            metadata={"source": "api.certs.print", "systemStateHash": serialized["systemStateHash"]},
        )
        return Response(serialized, status=status.HTTP_201_CREATED)


class PrintArtifactListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not has_request_certs_perm(request, PRINT_EXPORT_FORM_ID):
            return Response({"detail": "You do not have access to Certs print history."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"results": [serialize_print_artifact(row) for row in repository.list_artifacts()]})


class PrintArtifactDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, print_id: str, *args, **kwargs):
        if not has_request_certs_perm(request, PRINT_EXPORT_FORM_ID):
            return Response({"detail": "You do not have access to Certs print artifacts."}, status=status.HTTP_403_FORBIDDEN)
        row = repository.get_artifact(str(print_id))
        if row is None:
            return Response({"detail": "Print artifact not found."}, status=status.HTTP_404_NOT_FOUND)
        serialized = serialize_print_artifact(row)
        access_error = _artifact_vessel_access_error(request.user, serialized["vessels"])
        if access_error:
            return access_error
        return Response(serialized)


class PrintShareBundleView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShareBundleRequestSerializer

    def post(self, request, *args, **kwargs):
        if not has_request_certs_perm(request, PRINT_EXPORT_FORM_ID, EXPORT_BUNDLE_PROCESS_ID):
            return Response({"detail": "You do not have access to generate Certs share bundles."}, status=status.HTTP_403_FORBIDDEN)
        if not _can_share_bundle(request.user):
            return Response({"detail": "Only Master, DPA, or Fleet Manager may generate Certs share bundles."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        access_error = _scope_access_error(request.user, payload)
        if access_error:
            return access_error
        try:
            row = service.generate_share_bundle(payload=payload, actor=request.user)
        except PrintGenerationFailed as exc:
            serialized = serialize_print_artifact(exc.artifact)
            return Response({"detail": serialized["failureMessage"], "artifact": serialized}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serialized = serialize_print_artifact(row)
        record_audit_event(
            actor=request.user,
            action="share_bundle_created",
            entity_type="print_artifact",
            entity_id=serialized["printId"],
            vessel_id=_single_vessel_id(serialized["vessels"]),
            before=None,
            after=_artifact_audit_payload(serialized),
            reason="Generated Master share bundle.",
            metadata={"source": "api.certs.print.share_bundle", "systemStateHash": serialized["systemStateHash"]},
        )
        return Response(serialized, status=status.HTTP_201_CREATED)


def _scope_access_error(user, payload: dict):
    role = normalized_role(user)
    if payload.get("scope") == "per_section_fleetwide" and role not in FLEET_SCOPE_ROLES:
        return Response({"detail": "Only DPA or Fleet Manager may generate fleet-wide prints."}, status=status.HTTP_403_FORBIDDEN)
    vessel_ids = payload.get("vesselIds") or []
    if role in FLEET_SCOPE_ROLES:
        return None
    inaccessible = [vessel_id for vessel_id in vessel_ids if not user_can_access_vessel(user, vessel_id)]
    if inaccessible:
        return Response({"detail": "You do not have access to one or more selected vessels."}, status=status.HTTP_403_FORBIDDEN)
    return None


def _artifact_vessel_access_error(user, vessel_ids: list[str]):
    if normalized_role(user) in FLEET_SCOPE_ROLES:
        return None
    inaccessible = [vessel_id for vessel_id in vessel_ids if not user_can_access_vessel(user, str(vessel_id))]
    if inaccessible:
        return Response({"detail": "You do not have access to this print artifact."}, status=status.HTTP_403_FORBIDDEN)
    return None


def _can_share_bundle(user) -> bool:
    role = normalized_role(user)
    return role in FLEET_SCOPE_ROLES or is_master_user(user)


def _single_vessel_id(vessel_ids: list[str]) -> str | None:
    return vessel_ids[0] if len(vessel_ids) == 1 else None


def _artifact_audit_payload(serialized: dict) -> dict:
    return {
        "printId": serialized.get("printId"),
        "scope": serialized.get("scope"),
        "vessels": serialized.get("vessels"),
        "sections": serialized.get("sections"),
        "systemStateHash": serialized.get("systemStateHash"),
        "watermarkApplied": serialized.get("watermarkApplied"),
        "pdfBlobId": serialized.get("pdfBlobId"),
        "excelBlobId": serialized.get("excelBlobId"),
        "bundleZipBlobId": serialized.get("bundleZipBlobId"),
        "pageCount": serialized.get("pageCount"),
        "generationStatus": serialized.get("generationStatus"),
    }
