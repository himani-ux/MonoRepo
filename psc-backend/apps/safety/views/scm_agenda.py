from __future__ import annotations

from rest_framework import generics, status
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.models import SCMMeeting
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers.scm_agenda import SCMAgendaUpdateSerializer
from apps.safety.views.scm import SCMViewMixin, _resolve_actor_id


class SCMAgendaView(SCMViewMixin, generics.GenericAPIView):
    serializer_class = SCMAgendaUpdateSerializer
    lookup_url_kwarg = "id"
    queryset = SCMMeeting.objects.filter(is_deleted=False)

    def get_permissions(self):
        permissions = [HasFormPermission.requiring("SAF_F_003")()]
        if self.request.method != "GET":
            permissions.append(HasProcessPermission.requiring("SAF_P_002")())
        return permissions

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_meeting(self) -> SCMMeeting:
        return get_by_public_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])

    def get(self, request, *args, **kwargs):
        meeting = self.get_meeting()
        payload = self.get_scm_repository().build_agenda_payload(meeting=meeting)
        return Response(payload, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        self._ensure_agenda_editor_gate()
        meeting = self.get_meeting()
        self.get_state_machine().ensure_mutable(meeting)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_meeting = self.get_scm_repository().update_agenda(
            meeting=meeting,
            rows=serializer.validated_data["rows"],
            actor_id=_resolve_actor_id(request.user),
        )
        payload = self.get_scm_repository().build_agenda_payload(meeting=updated_meeting)
        return Response(payload, status=status.HTTP_200_OK)
