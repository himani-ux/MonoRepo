from __future__ import annotations

from django.http import HttpResponse
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.safety.authentication.permissions import HasFormPermission
from apps.safety.services.auditor_zip_builder import AuditorZipBuilder


def _normalized_role(user) -> str:
    if user is None:
        return ""
    role_name = getattr(user, "safety_role_name", None) or getattr(user, "role_name", None) or getattr(user, "role", None) or ""
    return str(role_name).strip().upper()


class AuditorBundleExportView(generics.GenericAPIView):
    form_permission_class = HasFormPermission.requiring("SAF_F_020")
    builder_class = AuditorZipBuilder
    allowed_roles = {"MASTER", "DPA"}

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_builder(self) -> AuditorZipBuilder:
        return self.builder_class()

    def _ensure_role_gate(self) -> None:
        if _normalized_role(getattr(self.request, "user", None)) not in self.allowed_roles:
            raise PermissionDenied(
                "Auditor leave-behind export is restricted to Master or DPA in this handover workspace."
            )

    def post(self, request, *args, **kwargs):
        self._ensure_role_gate()

        record_types = request.data.get("record_types")
        if not isinstance(record_types, list):
            raise ValidationError({"record_types": "record_types must be a JSON array."})

        result = self.get_builder().build_bundle(
            record_types=record_types,
            date_from=request.data.get("date_from"),
            date_to=request.data.get("date_to"),
            vessel_id=request.data.get("vessel_id"),
            viewer_user=request.user,
            persist=True,
        )

        response = HttpResponse(result.content, content_type=result.content_type)
        response["Content-Disposition"] = f'attachment; filename="{result.file_name}"'
        response["Content-Length"] = str(len(result.content))
        response["X-Safety-Record-Count"] = str(result.record_count)
        response["X-Safety-Attachment-Count"] = str(result.attachment_count)
        response["X-Safety-Record-Types"] = ",".join(result.record_types)
        if result.export_path:
            response["X-Safety-Export-Path"] = result.export_path
        if result.missing_attachment_paths:
            response["X-Safety-Missing-Attachment-Count"] = str(len(result.missing_attachment_paths))
        return response
