from __future__ import annotations

from django.http import HttpResponse
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from apps.safety.authentication.roles import normalized_authority_role
from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import Incident
from apps.safety.services.pdf_renderer import MscMepc3Circ4PdfRenderer
from apps.safety.views.incident import IncidentViewMixin


class MscMepc3ExportView(IncidentViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    export_process_permission_class = HasProcessPermission.requiring("SAF_P_023")
    pdf_renderer_class = MscMepc3Circ4PdfRenderer

    def get_permissions(self):
        return [self.form_permission_class(), self.export_process_permission_class()]

    def get_queryset(self):
        return self._apply_filters(Incident.objects.filter(is_deleted=False))

    def get_pdf_renderer(self) -> MscMepc3Circ4PdfRenderer:
        return self.pdf_renderer_class()

    def get(self, request, *args, **kwargs):
        if normalized_authority_role(request.user) != "DPA":
            raise PermissionDenied("Only DPA may generate the MSC-MEPC.3/Circ.4 export.")

        incident = self.get_object()
        result = self.get_pdf_renderer().render_export_pdf(
            incident_id=incident.pk,
            viewer_user=request.user,
            persist=True,
        )

        response = HttpResponse(result.content, content_type=result.content_type)
        response["Content-Disposition"] = f'attachment; filename="{result.file_name}"'
        response["Content-Length"] = str(len(result.content))
        if result.export_path:
            response["X-Safety-Export-Path"] = result.export_path
        response["X-Safety-Download-Path"] = result.download_path
        return response
