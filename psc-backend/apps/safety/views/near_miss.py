from __future__ import annotations

import json

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.authentication.roles import normalized_authority_role
from apps.safety.authentication.vessel_scope import filter_by_vessel_scope, get_scoped_vessel_ids, user_has_vessel_access
from apps.safety.models import Incident
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.repositories import IncidentRepository
from apps.safety.serializers import NearMissCreateSerializer, NearMissListSerializer, NearMissSerializer
from apps.safety.services import NotificationWriter, PhaseStateMachine
from apps.safety.services.near_miss_photo_evidence import store_near_miss_photo_evidence


def _normalized_role(user) -> str:
    return normalized_authority_role(user)


def _resolve_actor_id(user) -> str:
    if user is None:
        return "system"

    for attr_name in ("username", "employee_id", "crew_id", "user_id", "id"):
        value = getattr(user, attr_name, None)
        if value not in (None, ""):
            return str(value)
    return "system"


def _first_text(*values) -> str:
    for value in values:
        if value not in (None, ""):
            text = str(value).strip()
            if text:
                return text
    return ""


def _resolve_reporter_identity(user) -> dict[str, str]:
    actor_id = _resolve_actor_id(user)
    full_name = _first_text(
        getattr(user, "full_name", None),
        getattr(user, "display_name", None),
        getattr(user, "name", None),
        " ".join(
            part
            for part in (
                _first_text(getattr(user, "first_name", None), getattr(user, "FirstName", None)),
                _first_text(getattr(user, "last_name", None), getattr(user, "LastName", None)),
            )
            if part
        ),
        actor_id,
    )
    return {
        "reporter_id": actor_id,
        "reporter_name": full_name or actor_id,
        "reporter_rank": _first_text(
            getattr(user, "rank", None),
            getattr(user, "rank_name", None),
            getattr(user, "safety_role_name", None),
            getattr(user, "role_name", None),
            getattr(user, "role", None),
        ),
        "reporter_email": _first_text(getattr(user, "email", None), getattr(user, "Email", None)),
        "reporter_department": _first_text(
            getattr(user, "department", None),
            getattr(user, "department_name", None),
            getattr(user, "dept", None),
        ),
    }


def _is_master_user(user) -> bool:
    role = _normalized_role(user)
    rank = _first_text(
        getattr(user, "rank", None),
        getattr(user, "rank_name", None),
        getattr(user, "safety_role_name", None),
        getattr(user, "role_name", None),
        getattr(user, "role", None),
    ).upper()
    return role in {"MASTER", "CAPTAIN", "VESSEL_MASTER"} or rank in {"MASTER", "CAPTAIN"}


def _resolve_vessel_id(request) -> str | None:
    vessel_id = request.query_params.get("vessel_id")
    if vessel_id not in (None, ""):
        if not user_has_vessel_access(getattr(request, "user", None), vessel_id):
            raise PermissionDenied("You are not assigned to this vessel.")
        return str(vessel_id)

    user = getattr(request, "user", None)
    vessel_ids = sorted(get_scoped_vessel_ids(user))
    if vessel_ids:
        return str(vessel_ids[0])
    return None


class NearMissViewMixin:
    incident_repository_class = IncidentRepository
    form_permission_class = HasFormPermission.requiring("SAF_F_002")
    process_permission_class = HasProcessPermission.requiring("SAF_P_001")
    phase_state_machine_class = PhaseStateMachine
    notification_writer_class = NotificationWriter

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method == "POST":
            permissions.append(self.process_permission_class())
        return permissions

    def get_incident_repository(self) -> IncidentRepository:
        return self.incident_repository_class()

    def get_phase_state_machine(self) -> PhaseStateMachine:
        return self.phase_state_machine_class()

    def get_notification_writer(self) -> NotificationWriter:
        return self.notification_writer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident_repository"] = self.get_incident_repository()
        return context

    def _apply_filters(self, queryset):
        request = self.request
        queryset = filter_by_vessel_scope(queryset, getattr(request, "user", None))
        queryset = queryset.filter(record_type=Incident.RecordType.NEAR_MISS)

        if vessel_id := request.query_params.get("vessel_id"):
            queryset = queryset.filter(vessel_id=str(vessel_id))
        if state := request.query_params.get("state"):
            queryset = queryset.filter(state=state)
        if priority := request.query_params.get("priority"):
            queryset = queryset.filter(near_miss_priority=str(priority).strip().upper())
        if reporter_id := request.query_params.get("reporter_id"):
            queryset = queryset.filter(reporter_id=reporter_id)

        if date_from := request.query_params.get("date_from"):
            queryset = queryset.filter(occurred_at__date__gte=date_from)
        if date_to := request.query_params.get("date_to"):
            queryset = queryset.filter(occurred_at__date__lte=date_to)
        return queryset

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        return get_by_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])


class NearMissListCreateView(NearMissViewMixin, generics.ListCreateAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return NearMissCreateSerializer
        return NearMissListSerializer

    def create(self, request, *args, **kwargs):
        payload = self._extract_create_payload(request)
        uploaded_file = request.FILES.get("photo") or request.FILES.get("file")

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("near_miss_severity") == "HIGH" and uploaded_file is None:
            raise ValidationError({"photo": "Image upload is required when severity is HIGH."})

        with transaction.atomic():
            self.perform_create(serializer, uploaded_file=uploaded_file)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def _extract_create_payload(self, request):
        if "payload" not in request.data:
            return request.data

        raw_payload = request.data.get("payload")
        try:
            payload = json.loads(raw_payload)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"payload": "Near miss payload must be valid JSON."}) from exc
        if not isinstance(payload, dict):
            raise ValidationError({"payload": "Near miss payload must be a JSON object."})
        return payload

    def perform_create(self, serializer, *, uploaded_file=None):
        user = self.request.user
        actor_id = _resolve_actor_id(user)
        reporter_identity = _resolve_reporter_identity(user)

        near_miss = serializer.save(
            created_by=actor_id,
            updated_by=actor_id,
            reported_at=serializer.validated_data.get("reported_at") or timezone.now(),
            state=(
                Incident.State.READY_FOR_OFFICE_COMMENTS
                if _is_master_user(user)
                else Incident.State.PENDING_VESSEL_REVIEW
            ),
            reporter_id=reporter_identity["reporter_id"],
            reporter_name=reporter_identity["reporter_name"],
            reporter_rank=reporter_identity["reporter_rank"],
            reporter_email=reporter_identity["reporter_email"],
            reporter_department=reporter_identity["reporter_department"],
        )
        if serializer.validated_data.get("near_miss_severity") == "HIGH" and uploaded_file is not None:
            store_near_miss_photo_evidence(
                near_miss=near_miss,
                uploaded_file=uploaded_file,
                actor_id=actor_id,
            )
        self.get_phase_state_machine().log_creation(near_miss, user)
        self.get_notification_writer().dispatch_notification(
            record_id=near_miss.pk,
            recipients=["PIC", "DPA", "SAFETY_CHANNEL"],
            kind="NEAR_MISS_SUBMITTED",
            title="New near miss submitted",
            message=(
                f"Near miss {near_miss.incident_number} is ready for office comments."
                if near_miss.state == Incident.State.READY_FOR_OFFICE_COMMENTS
                else f"Near miss {near_miss.incident_number} is awaiting vessel-side review."
            ),
            payload={
                "near_miss_id": near_miss.pk,
                "incident_number": near_miss.incident_number,
                "state": near_miss.state,
                "vessel_id": near_miss.vessel_id,
            },
            send_slack=True,
        )
        return near_miss


class NearMissDetailView(NearMissViewMixin, generics.RetrieveAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissSerializer

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())


class NearMissRateLimitView(NearMissViewMixin, generics.GenericAPIView):
    def get_permissions(self):
        return [self.form_permission_class()]

    def get(self, request, *args, **kwargs):
        actor_id = _resolve_actor_id(request.user)
        requested_crew_id = request.query_params.get("crew_id")

        subject_actor_id = requested_crew_id or actor_id
        return Response(
            {
                "allowed": True,
                "guidance_message": None,
                "limit": None,
                "remaining": None,
                "reset_at": None,
                "retry_after_seconds": 0,
                "scope": "unlimited",
                "used": 0,
            }
        )
