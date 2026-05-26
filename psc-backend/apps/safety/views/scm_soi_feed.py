from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import SCMMeeting
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.services.scm_state_machine import SCMStateMachine
from apps.safety.services.soi_to_scm_feeder import SOIToSCMFeeder
from apps.safety.views.scm import _resolve_actor_id
from apps.safety.views.scm_closed_since import SCMClosedSinceLastMixin


class SCMSoIAutoFeedMixin(SCMClosedSinceLastMixin):
    service_class = SOIToSCMFeeder
    edit_permission_class = HasProcessPermission.requiring("SAF_P_002")
    state_machine_class = SCMStateMachine

    def get_service(self) -> SOIToSCMFeeder:
        return self.service_class()

    def get_state_machine(self) -> SCMStateMachine:
        return self.state_machine_class()

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method != "GET":
            permissions.append(self.edit_permission_class())
        return permissions

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_id_or_pk(queryset, self.kwargs["id"])


class SCMSoIAutoFeedMeetingView(SCMSoIAutoFeedMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        payload = self.get_service().fetch_for_meeting(self.get_meeting())
        return Response(payload)

    def patch(self, request, *args, **kwargs):
        self._ensure_agenda_editor_gate()
        meeting = self.get_meeting()
        self.get_state_machine().ensure_mutable(meeting)
        outcomes = request.data.get("outcomes")
        if not isinstance(outcomes, list):
            return Response({"outcomes": "outcomes must be a list."}, status=400)

        payload = self.get_service().apply_outcomes_for_meeting(
            meeting,
            outcomes=outcomes,
            actor_id=_resolve_actor_id(request.user),
        )
        return Response(payload)


class SOIOpenFindingsVesselView(SCMSoIAutoFeedMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        vessel_id = self._resolve_vessel_id()
        self._ensure_vessel_access(vessel_id)
        payload = self.get_service().fetch_for_vessel(vessel_id)
        return Response(payload)
