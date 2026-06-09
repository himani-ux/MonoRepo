from __future__ import annotations

from django.db import connection
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import SCMMeeting
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers import SCMMeetingSerializer, SCMOfficeCommentSerializer
from apps.safety.services.field_history_recorder import capture_model_state, record_field_changes
from apps.safety.views.scm import SCMViewMixin, _normalized_role, _resolve_actor_id


MARINE_SUPERINTENDENT_PROFILE_ID = "407ef017-0f1c-ef11-a9f1-f348983bae6b"
OFFICE_COMMENT_ROLES = {"DPA", "FM", "HOD SHORE", "SHORE HOD"}


def _normalized_identifier(value) -> str:
    return str(value or "").strip().lower()


def _extract_profile_ids(source) -> set[str]:
    if source is None:
        return set()
    ids = set()
    for key in ("profile_id", "profileId", "office_profile_id", "role_id"):
        value = source.get(key) if isinstance(source, dict) else getattr(source, key, None)
        if isinstance(value, (list, tuple, set)):
            ids.update(_normalized_identifier(item) for item in value if _normalized_identifier(item))
        elif _normalized_identifier(value):
            ids.add(_normalized_identifier(value))
    return ids


def _has_marine_superintendent_profile(request) -> bool:
    target_profile_id = _normalized_identifier(MARINE_SUPERINTENDENT_PROFILE_ID)
    user = getattr(request, "user", None)
    auth = getattr(request, "auth", None)
    if target_profile_id in (_extract_profile_ids(user) | _extract_profile_ids(auth)):
        return True

    identifiers = []
    for attr_name in ("login_id", "username", "employee_id", "user_id", "id"):
        value = getattr(user, attr_name, None)
        normalized = str(value or "").strip()
        if normalized and normalized not in identifiers:
            identifiers.append(normalized)
    if not identifiers:
        return False

    sql_server = """
        SELECT TOP 1 1
        FROM mapping_role_user mru
        LEFT JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        LEFT JOIN msc_profiles p
            ON (
                p.profile_id = mru.role_id
                OR p.profile_name = mr.role_name
            )
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
          AND (
              LOWER(CONVERT(varchar(36), mru.role_id)) = LOWER(%s)
              OR LOWER(CONVERT(varchar(36), p.profile_id)) = LOWER(%s)
          )
    """
    sql_sqlite = """
        SELECT 1
        FROM mapping_role_user mru
        LEFT JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        LEFT JOIN msc_profiles p
            ON (
                p.profile_id = mru.role_id
                OR p.profile_name = mr.role_name
            )
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
          AND (
              LOWER(CAST(mru.role_id AS TEXT)) = LOWER(%s)
              OR LOWER(CAST(p.profile_id AS TEXT)) = LOWER(%s)
          )
        LIMIT 1
    """
    sql = sql_sqlite if connection.vendor == "sqlite" else sql_server
    try:
        for identifier in identifiers:
            with connection.cursor() as cursor:
                cursor.execute(sql, [identifier, MARINE_SUPERINTENDENT_PROFILE_ID, MARINE_SUPERINTENDENT_PROFILE_ID])
                if cursor.fetchone():
                    return True
    except Exception:
        return False
    return False


class SCMOfficeCommentView(SCMViewMixin, generics.GenericAPIView):
    serializer_class = SCMOfficeCommentSerializer

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_id_or_pk(queryset, self.kwargs["id"])

    def post(self, request, *args, **kwargs):
        if (
            _normalized_role(getattr(request, "user", None)) not in OFFICE_COMMENT_ROLES
            and not _has_marine_superintendent_profile(request)
        ):
            raise PermissionDenied(
                "SCM office comments are restricted to DPA/FM/shore HOD/Marine Superintendent oversight."
            )
        meeting = self.get_meeting()
        if meeting.office_comment_at is not None or meeting.state == SCMMeeting.State.CLOSED:
            raise ValidationError({"office_comment": "SCM office review is already completed."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_state = capture_model_state(
            meeting,
            field_names=("state", "office_comment", "office_comment_by", "office_comment_at"),
        )
        meeting.office_comment = serializer.validated_data["office_comment"].strip()
        meeting.office_comment_by = _resolve_actor_id(request.user)
        meeting.office_comment_at = timezone.now()
        meeting.state = SCMMeeting.State.CLOSED
        meeting.save(update_fields=("state", "office_comment", "office_comment_by", "office_comment_at"))
        self.get_scm_repository()._save_legacy_fields(
            meeting_id=meeting.id,
            agenda_item_number=9,
            values={
                "officecomments": meeting.office_comment,
                "isreviewed": bool(serializer.validated_data.get("is_reviewed", True)),
            },
        )
        record_field_changes(
            meeting,
            old_state,
            user=request.user,
            field_names=("state", "office_comment", "office_comment_by", "office_comment_at"),
            change_reason="SCM office oversight comment completed and meeting closed.",
        )
        return Response(
            SCMMeetingSerializer(meeting, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )
