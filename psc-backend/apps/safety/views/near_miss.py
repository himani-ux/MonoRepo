from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.safety.authentication.anonymity import REPORTER_VISIBLE_ROLES
from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.authentication.roles import normalized_authority_role
from apps.safety.authentication.vessel_scope import filter_by_vessel_scope, get_scoped_vessel_ids, user_has_vessel_access
from apps.safety.models import Incident
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.repositories import IncidentRepository
from apps.safety.serializers import NearMissCreateSerializer, NearMissListSerializer, NearMissSerializer
from apps.safety.services import NearMissRateLimiter, NotificationWriter, PhaseStateMachine


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
    rate_limiter_class = NearMissRateLimiter
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

    def get_rate_limiter(self) -> NearMissRateLimiter:
        return self.rate_limiter_class()

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
            if _normalized_role(getattr(request, "user", None)) not in REPORTER_VISIBLE_ROLES:
                raise PermissionDenied(
                    "Forbidden - reporter identity is restricted to DPA and FM (D-GAP-J1)."
                )
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

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return NearMissCreateSerializer
        return NearMissListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor_id = _resolve_actor_id(request.user)
        vessel_id = str(serializer.validated_data.get("vessel_id") or "")
        rate_limit_status = self.get_rate_limiter().check_allowed(
            actor_id=actor_id,
            vessel_id=vessel_id or None,
        )
        if not rate_limit_status.allowed:
            return Response(
                {"detail": rate_limit_status.guidance_message},
                headers={"Retry-After": str(rate_limit_status.retry_after_seconds)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        actor_id = _resolve_actor_id(user)
        reporter_identity = _resolve_reporter_identity(user)

        near_miss = serializer.save(
            created_by=actor_id,
            updated_by=actor_id,
            reported_at=serializer.validated_data.get("reported_at") or timezone.now(),
            reporter_id=reporter_identity["reporter_id"],
            reporter_name=reporter_identity["reporter_name"],
            reporter_rank=reporter_identity["reporter_rank"],
            reporter_email=reporter_identity["reporter_email"],
            reporter_department=reporter_identity["reporter_department"],
        )
        self.get_phase_state_machine().log_creation(near_miss, user)
        self.get_rate_limiter().record_submission(actor_id=actor_id, created_at=near_miss.created_date)
        self.get_notification_writer().dispatch_notification(
            record_id=near_miss.pk,
            recipients=["PIC", "DPA", "SAFETY_CHANNEL"],
            kind="NEAR_MISS_SUBMITTED",
            title="New near miss submitted",
            message=f"Near miss {near_miss.incident_number} is awaiting vessel-side review.",
            payload={
                "near_miss_id": near_miss.pk,
                "incident_number": near_miss.incident_number,
                "state": near_miss.state,
                "vessel_id": near_miss.vessel_id,
            },
            send_slack=True,
        )


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
        if requested_crew_id not in (None, "", actor_id) and _normalized_role(request.user) not in REPORTER_VISIBLE_ROLES:
            raise PermissionDenied(
                "Forbidden - reporter identity is restricted to DPA and FM (D-GAP-J1)."
            )

        subject_actor_id = requested_crew_id or actor_id
        rate_limit_status = self.get_rate_limiter().get_status(
            actor_id=subject_actor_id,
            vessel_id=_resolve_vessel_id(request),
        )
        return Response(
            {
                "allowed": rate_limit_status.allowed,
                "guidance_message": rate_limit_status.guidance_message,
                "limit": rate_limit_status.limit,
                "remaining": rate_limit_status.remaining,
                "reset_at": rate_limit_status.reset_at,
                "retry_after_seconds": rate_limit_status.retry_after_seconds,
                "scope": rate_limit_status.scope,
                "used": rate_limit_status.used,
            }
        )
