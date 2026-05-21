from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import SCMMeeting
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers import SCMMeetingSerializer, SCMOfficeCommentSerializer
from apps.safety.services.field_history_recorder import capture_model_state, record_field_changes
from apps.safety.views.scm import SCMViewMixin, _normalized_role, _resolve_actor_id


class SCMOfficeCommentView(SCMViewMixin, generics.GenericAPIView):
    serializer_class = SCMOfficeCommentSerializer

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_public_id_or_pk(queryset, self.kwargs["id"])

    def post(self, request, *args, **kwargs):
        if _normalized_role(getattr(request, "user", None)) not in {"DPA", "FM", "HOD SHORE", "SHORE HOD"}:
            raise PermissionDenied("SCM office comments are restricted to DPA/FM/shore HOD oversight.")
        meeting = self.get_meeting()
        if meeting.state != SCMMeeting.State.SIGNED_OFF or meeting.master_signed_off_at is None:
            raise ValidationError(
                {"office_comment": "Section 10 office review is available after Master sign-off."}
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_state = capture_model_state(
            meeting,
            field_names=("office_comment", "office_comment_by", "office_comment_at"),
        )
        meeting.office_comment = serializer.validated_data["office_comment"].strip()
        meeting.office_comment_by = _resolve_actor_id(request.user)
        meeting.office_comment_at = timezone.now()
        meeting.save(update_fields=("office_comment", "office_comment_by", "office_comment_at"))
        self.get_scm_repository()._save_legacy_fields(
            meeting_id=meeting.id,
            agenda_item_number=10,
            values={
                "officecomments": meeting.office_comment,
                "isreviewed": bool(serializer.validated_data.get("is_reviewed", True)),
            },
        )
        record_field_changes(
            meeting,
            old_state,
            user=request.user,
            field_names=("office_comment", "office_comment_by", "office_comment_at"),
            change_reason="SCM office oversight comment updated.",
        )
        return Response(
            SCMMeetingSerializer(meeting, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )
