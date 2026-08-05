from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.models import SCMMeeting
from apps.safety.views.scm import SCMViewMixin, _resolve_actor_id, _resolve_default_vessel_id


class SCMCreateAdHocView(SCMViewMixin, generics.GenericAPIView):
    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get(self, request, *args, **kwargs):
        self._ensure_scm_host_gate()
        vessel_id = request.query_params.get("vessel_id")
        if vessel_id in (None, ""):
            vessel_id = _resolve_default_vessel_id(request.user)

        payload = self.get_scm_repository().build_form_config(
            vessel_id=str(vessel_id),
            meeting_type=SCMMeeting.MeetingType.AD_HOC,
            meeting_date=request.query_params.get("meeting_date"),
            actor_id=_resolve_actor_id(request.user),
            user=request.user,
            include_feeds=True,
            include_rollups=False,
            include_wrh_preview=True,
        )
        return Response(payload)
