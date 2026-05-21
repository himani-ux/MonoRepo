from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response
from django.utils import timezone

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import SCMMeeting
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers import SCMAttendanceAcknowledgementSerializer
from apps.safety.serializers.scm_attendance import SCMAttendanceBulkWriteSerializer
from apps.safety.services.field_history_recorder import capture_model_state, record_field_changes
from apps.safety.views.scm import SCMViewMixin
from apps.safety.views.scm import _resolve_actor_id, _normalized_role


class SCMAttendanceListCreateView(SCMViewMixin, generics.GenericAPIView):
    serializer_class = SCMAttendanceBulkWriteSerializer

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method == "POST":
            permissions.append(self.process_permission_class())
        return permissions

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_public_id_or_pk(queryset, self.kwargs["id"])

    def get(self, request, *args, **kwargs):
        self._ensure_agenda_editor_gate()
        payload = self.get_scm_repository().build_attendance_payload(meeting=self.get_meeting())
        return Response(payload)

    def post(self, request, *args, **kwargs):
        self._ensure_agenda_editor_gate()
        meeting = self.get_meeting()
        self.get_state_machine().ensure_mutable(meeting)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.get_scm_repository().save_attendance(
            meeting=meeting,
            rows=serializer.validated_data["rows"],
        )
        return Response(payload, status=200)


class SCMAttendanceAcknowledgeView(SCMViewMixin, generics.GenericAPIView):
    serializer_class = SCMAttendanceAcknowledgementSerializer

    def get_permissions(self):
        return [self.form_permission_class(), HasProcessPermission.requiring("SAF_P_004")()]

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_public_id_or_pk(queryset, self.kwargs["id"])

    def post(self, request, *args, **kwargs):
        if _normalized_role(getattr(request, "user", None)) != "MASTER":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("SCM attendance warning acknowledgement is restricted to the Master.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data["acknowledged"]:
            return Response({"acknowledged": False}, status=200)
        meeting = self.get_meeting()
        old_state = capture_model_state(
            meeting,
            field_names=("attendance_warnings_acknowledged_at", "attendance_warnings_acknowledged_by"),
        )
        meeting.attendance_warnings_acknowledged_at = timezone.now()
        meeting.attendance_warnings_acknowledged_by = _resolve_actor_id(request.user)
        meeting.save(update_fields=("attendance_warnings_acknowledged_at", "attendance_warnings_acknowledged_by"))
        record_field_changes(
            meeting,
            old_state,
            user=request.user,
            field_names=("attendance_warnings_acknowledged_at", "attendance_warnings_acknowledged_by"),
            change_reason="SCM attendance WRH warnings acknowledged.",
        )
        return Response(
            {
                "acknowledged": True,
                "acknowledged_at": meeting.attendance_warnings_acknowledged_at,
                "acknowledged_by": meeting.attendance_warnings_acknowledged_by,
            },
            status=200,
        )
