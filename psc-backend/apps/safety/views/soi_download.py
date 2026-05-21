from __future__ import annotations

from django.http import HttpResponse
from rest_framework import exceptions, generics
from rest_framework.negotiation import DefaultContentNegotiation, _MediaType
from rest_framework.utils.mediatypes import media_type_matches, order_by_precedence

from apps.safety.serializers import SOIDownloadQuerySerializer
from apps.safety.services import SOIChecklistGenerator, UniqueIdAllocator
from apps.safety.services.soi_schema_guard import ensure_soi_runtime_schema
from apps.safety.views.soi import SOIViewMixin


class SOIDownloadContentNegotiation(DefaultContentNegotiation):
    def select_renderer(self, request, renderers, format_suffix=None):
        accepts = self.get_accept_list(request)

        for media_type_set in order_by_precedence(accepts):
            for renderer in renderers:
                for media_type in media_type_set:
                    if media_type_matches(renderer.media_type, media_type):
                        media_type_wrapper = _MediaType(media_type)
                        renderer_media_type = _MediaType(renderer.media_type)
                        if renderer_media_type.precedence > media_type_wrapper.precedence:
                            full_media_type = ";".join(
                                (renderer.media_type,)
                                + tuple(
                                    f"{key}={value}"
                                    for key, value in media_type_wrapper.params.items()
                                )
                            )
                            return renderer, full_media_type
                        return renderer, media_type

        raise exceptions.NotAcceptable(available_renderers=renderers)


class SOIDownloadView(SOIViewMixin, generics.GenericAPIView):
    content_negotiation_class = SOIDownloadContentNegotiation
    serializer_class = SOIDownloadQuerySerializer
    unique_id_allocator_class = UniqueIdAllocator
    checklist_generator_class = SOIChecklistGenerator

    def get_permissions(self):
        return [self.form_permission_class(), self.create_process_permission_class()]

    def get_unique_id_allocator(self) -> UniqueIdAllocator:
        return self.unique_id_allocator_class()

    def get_checklist_generator(self) -> SOIChecklistGenerator:
        return self.checklist_generator_class(
            soi_repository=self.get_soi_repository(),
            checklist_version_resolver=self.get_checklist_version_resolver(),
        )

    def get(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        self._ensure_safety_officer_gate(vessel_id=str(inspection.vessel_id))
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        ensure_soi_runtime_schema()
        self.get_unique_id_allocator().allocate(inspection.id)
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
