from __future__ import annotations

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.authentication.vessel_scope import filter_by_vessel_scope, get_scoped_vessel_ids, user_has_vessel_access
from apps.safety.models import SCMAgendaItem, SCMMeeting
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.repositories import SCMRepository
from apps.safety.serializers import (
    SCMMeetingCreateSerializer,
    SCMMeetingDetailSerializer,
    SCMMeetingListSerializer,
    SCMSubmitSerializer,
)
from apps.safety.services.scm_state_machine import SCMStateMachine


def _normalized_role(user) -> str:
    if user is None:
        return ""
    role_name = getattr(user, "safety_role_name", None) or getattr(user, "role_name", None) or getattr(user, "role", None) or ""
    return str(role_name).strip().upper()


def _resolve_actor_id(user) -> str:
    if user is None:
        return "system"

    for attr_name in ("username", "employee_id", "crew_id", "user_id", "id"):
        value = getattr(user, attr_name, None)
        if value not in (None, ""):
            return str(value)
    return "system"


def _resolve_default_vessel_id(user) -> str:
    vessel_ids = sorted(get_scoped_vessel_ids(user))
    if vessel_ids:
        return str(vessel_ids[0]).strip()

    direct_vessel_id = getattr(user, "vessel_id", None)
    if direct_vessel_id not in (None, ""):
        return str(direct_vessel_id).strip()

    return ""


class SCMViewMixin:
    form_permission_class = HasFormPermission.requiring("SAF_F_003")
    process_permission_class = HasProcessPermission.requiring("SAF_P_001")
    repository_class = SCMRepository
    state_machine_class = SCMStateMachine

    def get_scm_repository(self) -> SCMRepository:
        return self.repository_class()

    def get_state_machine(self) -> SCMStateMachine:
        return self.state_machine_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["scm_repository"] = self.get_scm_repository()
        return context

    def _apply_filters(self, queryset):
        request = self.request
        repository = self.get_scm_repository()
        if not repository._scm_meeting_legacy_columns_available():
            queryset = queryset.defer(*repository._legacy_header_field_names())
        queryset = filter_by_vessel_scope(queryset, getattr(request, "user", None))

        if vessel_id := request.query_params.get("vessel_id"):
            queryset = queryset.filter(vessel_id=str(vessel_id))
        if meeting_type := request.query_params.get("meeting_type"):
            queryset = queryset.filter(meeting_type=str(meeting_type).strip().upper())
        if state := request.query_params.get("state"):
            queryset = queryset.filter(state=str(state).strip().upper())
        if date_from := request.query_params.get("date_from"):
            queryset = queryset.filter(meeting_date__gte=date_from)
        if date_to := request.query_params.get("date_to"):
            queryset = queryset.filter(meeting_date__lte=date_to)
        return queryset

    def _ensure_scm_host_gate(self) -> None:
        if _normalized_role(getattr(self.request, "user", None)) not in {"CO", "MASTER"}:
            raise PermissionDenied("Only Chief Officer or Master can create SCM meetings.")

    def _ensure_agenda_editor_gate(self) -> None:
        if _normalized_role(getattr(self.request, "user", None)) not in {"CO", "MASTER"}:
            raise PermissionDenied("Only Chief Officer or Master can edit this SCM meeting.")

    def _ensure_submit_gate(self, meeting: SCMMeeting) -> None:
        role = _normalized_role(getattr(self.request, "user", None))
        if role not in {"CO", "MASTER"}:
            raise PermissionDenied("Only Chief Officer or Master can finalize this SCM meeting.")

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        return get_by_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])


class SCMListCreateView(SCMViewMixin, generics.ListCreateAPIView):
    lookup_url_kwarg = "id"
    queryset = SCMMeeting.objects.filter(is_deleted=False)

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method == "POST":
            permissions.append(self.process_permission_class())
        return permissions

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SCMMeetingCreateSerializer
        return SCMMeetingListSerializer

    def list(self, request, *args, **kwargs):
        try:
            page_size = int(request.query_params.get("page_size") or 50)
        except (TypeError, ValueError):
            page_size = 50
        page_size = max(1, min(page_size, 100))
        queryset = list(self.get_queryset()[:page_size])
        repository = self.get_scm_repository()
        meeting_ids = [meeting.id for meeting in queryset]
        section_counts = {
            str(row["meeting_id"]): row["count"]
            for row in SCMAgendaItem.objects.filter(meeting_id__in=meeting_ids)
            .order_by()
            .values("meeting_id")
            .annotate(count=Count("id"))
        }
        for meeting in queryset:
            meeting.section_count = int(section_counts.get(str(meeting.id), 0) or 0)
            meeting._cadence_warning = None
        for meeting in queryset[:3]:
            if meeting.meeting_type == SCMMeeting.MeetingType.REGULAR:
                meeting._cadence_warning = repository.build_cadence_warning(
                    vessel_id=str(meeting.vessel_id),
                    meeting_date=meeting.meeting_date,
                )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._ensure_scm_host_gate()
        meeting_type = serializer.validated_data.get("meeting_type", SCMMeeting.MeetingType.REGULAR)
        vessel_id = str(serializer.validated_data.get("vessel_id") or "").strip()
        today_count = SCMMeeting.objects.filter(
            is_deleted=False,
            vessel_id=vessel_id,
            created_date__date=timezone.localdate(),
        ).exclude(state=SCMMeeting.State.DRAFT).count()
        if today_count >= 3:
            return Response(
                {"detail": "SCM creation limit: 3 per vessel per day."},
                status=429,
            )
        actor_id = _resolve_actor_id(request.user)
        meeting_date = serializer.validated_data.get("meeting_date")
        if meeting_type == SCMMeeting.MeetingType.AD_HOC:
            chair_crew_id = actor_id
            prepared_by_crew_id = actor_id
        else:
            chair_crew_id = self.get_scm_repository().resolve_current_master_id(
                vessel_id=vessel_id,
                active_on=meeting_date,
            )
            prepared_by_crew_id = actor_id
        meeting = serializer.save(
            created_by=actor_id,
            updated_by=actor_id,
            chair_crew_id=chair_crew_id,
            prepared_by_crew_id=prepared_by_crew_id,
        )
        return Response(
            {
                "id": meeting.id,
                "scm_number": meeting.scm_number,
                "state": meeting.state,
                "updated_date": meeting.updated_date,
            },
            status=201,
        )


class SCMDetailView(SCMViewMixin, generics.RetrieveAPIView):
    lookup_url_kwarg = "id"
    queryset = SCMMeeting.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        if self.request.method in {"PATCH", "PUT"}:
            return SCMMeetingCreateSerializer
        return SCMMeetingDetailSerializer

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method in {"PATCH", "PUT"}:
            permissions.append(HasProcessPermission.requiring("SAF_P_002")())
        return permissions

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_object(self):
        return super().get_object()

    def patch(self, request, *args, **kwargs):
        self._ensure_agenda_editor_gate()
        meeting = self.get_object()
        self.get_state_machine().ensure_editable_until_office_review(meeting)
        serializer = SCMMeetingCreateSerializer(
            meeting,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(
            {
                "id": updated.id,
                "scm_number": updated.scm_number,
                "state": updated.state,
                "updated_date": updated.updated_date,
            },
            status=status.HTTP_200_OK,
        )


class SCMSubmitView(SCMViewMixin, generics.GenericAPIView):
    serializer_class = SCMSubmitSerializer

    def get_permissions(self):
        return [self.form_permission_class(), HasProcessPermission.requiring("SAF_P_002")()]

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_id_or_pk(queryset, self.kwargs["id"])

    def post(self, request, *args, **kwargs):
        meeting = self.get_meeting()
        self._ensure_submit_gate(meeting)
        agenda_complete, agenda_errors = self.get_scm_repository().agenda_preflight_complete(meeting.id)
        if not agenda_complete:
            return Response({"errors": {"agenda": agenda_errors}}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        if not self.get_scm_repository().list_attendance(meeting.id).exists():
            return Response(
                {"errors": {"attendance": ["SCM attendance must be recorded before finalisation."]}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signature_payload = None
        current_role = _normalized_role(getattr(request, "user", None))
        if meeting.meeting_type == SCMMeeting.MeetingType.REGULAR and current_role == "CO":
            signature_payload = self.get_state_machine().validate_signature_payload(
                typed_name=serializer.validated_data.get("typed_name", ""),
                device_fingerprint=serializer.validated_data.get("device_fingerprint", ""),
            )
        updated = self.get_state_machine().submit_for_signoff(meeting, user=request.user)
        if (
            meeting.meeting_type == SCMMeeting.MeetingType.REGULAR
            and current_role == "CO"
            and signature_payload is not None
        ):
            self.get_state_machine().record_signature(
                updated,
                signer_role="CO",
                signer_crew_id=self.get_scm_repository().resolve_regular_co_signature_crew_id(updated),
                display_name=signature_payload.typed_name,
                typed_name=signature_payload.typed_name,
                device_fingerprint=signature_payload.device_fingerprint,
                signed_at=signature_payload.signed_at,
                user=request.user,
            )

        return Response(
            {
                "id": updated.id,
                "scm_number": updated.scm_number,
                "state": updated.state,
                "updated_date": updated.updated_date,
            },
            status=status.HTTP_200_OK,
        )


class SCMCreateRegularView(SCMViewMixin, generics.GenericAPIView):
    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get(self, request, *args, **kwargs):
        self._ensure_scm_host_gate()
        vessel_id = request.query_params.get("vessel_id")
        if vessel_id in (None, ""):
            vessel_id = _resolve_default_vessel_id(request.user)
        elif not user_has_vessel_access(request.user, vessel_id):
            raise PermissionDenied("You are not assigned to this vessel.")

        payload = self.get_scm_repository().build_form_config(
            vessel_id=str(vessel_id),
            actor_id=_resolve_actor_id(request.user),
            user=request.user,
            include_feeds=True,
            include_rollups=False,
            include_wrh_preview=True,
        )
        return Response(payload)
