from __future__ import annotations

from django.http import HttpResponse
from rest_framework import generics, serializers

from apps.safety.serializers import SOIReprintRequestSerializer
from apps.safety.services import SOIChecklistGenerator
from apps.safety.views.soi import SOIViewMixin
from apps.safety.views.soi_download import SOIDownloadContentNegotiation


class SOIReprintView(SOIViewMixin, generics.GenericAPIView):
    content_negotiation_class = SOIDownloadContentNegotiation
    serializer_class = SOIReprintRequestSerializer
    checklist_generator_class = SOIChecklistGenerator

    def get_permissions(self):
        return [self.form_permission_class(), self.create_process_permission_class()]

    def get_checklist_generator(self) -> SOIChecklistGenerator:
        return self.checklist_generator_class(
            soi_repository=self.get_soi_repository(),
            checklist_version_resolver=self.get_checklist_version_resolver(),
        )

    def post(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            inspection = self.get_soi_repository().log_lost_paper_recovery(
                inspection_id=inspection.id,
                actor_id=self.get_serializer_context()["actor_id"],
                reason=serializer.validated_data["reason"],
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        inspection = self.get_soi_repository().mark_checklist_downloaded(
            inspection_id=inspection.id,
            requested_format=serializer.validated_data["format"],
        )
        render_result = self.get_checklist_generator().render_for_inspection(
            inspection_id=inspection.id,
            output_format=str(inspection.checklist_format or serializer.validated_data["format"]),
        )

        response = HttpResponse(render_result.content, content_type=render_result.content_type)
        response["Content-Disposition"] = f'attachment; filename="{render_result.file_name}"'
        response["Content-Length"] = str(len(render_result.content))
        return response
