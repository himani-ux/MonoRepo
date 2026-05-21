from __future__ import annotations

from django.http import HttpResponse
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.services.dashboard_export import DashboardExportService


def _normalized_role(user) -> str:
    if user is None:
        return ""
    role_name = getattr(user, "safety_role_name", None) or getattr(user, "role_name", None) or getattr(user, "role", None) or ""
    return str(role_name).strip().upper()


class DashboardExportView(generics.GenericAPIView):
    form_permission_class = HasFormPermission.requiring("SAF_F_015")
    process_permission_class = HasProcessPermission.requiring("SAF_P_023")
    export_service_class = DashboardExportService

    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get_export_service(self) -> DashboardExportService:
        return self.export_service_class()

    def post(self, request, *args, **kwargs):
        if _normalized_role(request.user) != "DPA":
            raise PermissionDenied("Only DPA may export the Safety Intelligence Dashboard in V1.")

        export_format = request.data.get("format")
        if export_format in (None, ""):
            raise ValidationError({"format": "format is required and must be either 'pdf' or 'excel'."})

        try:
            result = self.get_export_service().build_export(
                export_format=export_format,
                period_code=request.data.get("period"),
                vessel_id=request.data.get("vessel_id"),
                viewer_user=request.user,
                persist=True,
            )
        except ValueError as exc:
            raise ValidationError({"format": str(exc)}) from exc

        response = HttpResponse(result.content, content_type=result.content_type)
        response["Content-Disposition"] = f'attachment; filename="{result.file_name}"'
        response["Content-Length"] = str(len(result.content))
        response["X-Safety-Export-Format"] = result.format
        if result.export_path:
            response["X-Safety-Export-Path"] = result.export_path
        return response
