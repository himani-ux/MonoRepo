from __future__ import annotations

from rest_framework import generics, status
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission
from apps.safety.services.cross_record_search import CrossRecordSearchService


class SafetyCrossRecordSearchView(generics.GenericAPIView):
    form_permission_class = HasFormPermission.requiring("SAF_F_005")
    service_class = CrossRecordSearchService
    TRUE_VALUES = {"1", "true", "yes", "on"}

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_service(self) -> CrossRecordSearchService:
        return self.service_class()

    def parse_include_archived(self, raw_value) -> bool:
        if raw_value is None:
            return False
        return str(raw_value).strip().lower() in self.TRUE_VALUES

    def get(self, request, *args, **kwargs):
        query = str(request.query_params.get("q") or "").strip()
        if len(query) < 3:
            return Response(
                {"detail": "Search query must be at least 3 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = self.get_service().search(
            query,
            user=request.user,
            include_archived=self.parse_include_archived(
                request.query_params.get("include_archived"),
            ),
            record_type=request.query_params.get("record_type"),
        )
        return Response(payload)
