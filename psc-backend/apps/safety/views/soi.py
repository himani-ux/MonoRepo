from __future__ import annotations

from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework import serializers as drf_serializers
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.authentication.vessel_scope import (
    filter_by_vessel_scope,
    get_scoped_vessel_ids,
    user_has_vessel_access,
)
from apps.safety.models import SOIInspection, SOIOfficerSetting
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.repositories import CMSRepository, SOIRepository
from apps.safety.services.checklist_version_resolver import ChecklistVersionResolver
from apps.safety.services.section12_cycle_enforcer import Section12CycleEnforcer
from apps.safety.services.soi_assistant_validator import SOIAssistantValidator
from apps.safety.services.soi_schema_guard import ensure_soi_runtime_schema
from apps.safety.serializers import (
    SOIApplicabilityApprovalPayloadSerializer,
    SOIApplicabilityApprovalResultSerializer,
    SOIApplicabilityRequestPayloadSerializer,
    SOIApplicabilityRequestResultSerializer,
    SOIApplicabilitySerializer,
    SOIApplicabilityUpdateSerializer,
    SOIInspectionCreateSerializer,
    SOIInspectionSerializer,
    SOIPendingApplicabilityRequestSerializer,
)


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


def _resolve_actor_ids(user) -> set[str]:
    if user is None:
        return set()
    ids: set[str] = set()
    for attr_name in ("username", "employee_id", "crew_id", "user_id", "id"):
        value = getattr(user, attr_name, None)
        if value not in (None, ""):
            ids.add(str(value).strip())
    return {value for value in ids if value}


DEFAULT_SAFETY_OFFICER_ROLES = {"CO", "CHIEF OFFICER", "SO", "SAFETY OFFICER"}
ALTERNATE_SAFETY_OFFICER_ROLES = {"2/E", "2E", "SECOND ENGINEER"}


class SOIViewMixin:
    form_permission_class = HasFormPermission.requiring("SAF_F_004")
    create_process_permission_class = HasProcessPermission.requiring("SAF_P_001")
    applicability_form_permission_class = HasFormPermission.requiring("SAF_F_013")
    applicability_request_permission_class = HasProcessPermission.requiring("SAF_P_016")
    applicability_approve_permission_class = HasProcessPermission.requiring("SAF_P_017")
    repository_class = SOIRepository
    cms_repository_class = CMSRepository
    checklist_version_resolver_class = ChecklistVersionResolver
    section12_cycle_enforcer_class = Section12CycleEnforcer

    def get_soi_repository(self) -> SOIRepository:
        return self.repository_class()

    def get_cms_repository(self) -> CMSRepository:
        return self.cms_repository_class()

    def get_assistant_validator(self) -> SOIAssistantValidator:
        return SOIAssistantValidator(cms_repository=self.get_cms_repository())

    def get_checklist_version_resolver(self) -> ChecklistVersionResolver:
        return self.checklist_version_resolver_class()

    def get_section12_cycle_enforcer(self) -> Section12CycleEnforcer:
        return self.section12_cycle_enforcer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["soi_repository"] = self.get_soi_repository()
        context["cms_repository"] = self.get_cms_repository()
        context["assistant_validator"] = self.get_assistant_validator()
        context["checklist_version_resolver"] = self.get_checklist_version_resolver()
        context["section12_cycle_enforcer"] = self.get_section12_cycle_enforcer()
        context["actor_id"] = _resolve_actor_id(getattr(self.request, "user", None))
        return context

    def _apply_filters(self, queryset):
        request = self.request
        queryset = filter_by_vessel_scope(queryset, getattr(request, "user", None))

        if vessel_id := request.query_params.get("vessel_id"):
            queryset = queryset.filter(vessel_id=str(vessel_id))
        if state := request.query_params.get("state"):
            queryset = queryset.filter(state=str(state).strip().upper())
        if cycle_label := request.query_params.get("cycle_label"):
            queryset = queryset.filter(cycle_label=str(cycle_label))
        if date_from := request.query_params.get("date_from"):
            queryset = queryset.filter(planned_date__gte=date_from)
        if date_to := request.query_params.get("date_to"):
            queryset = queryset.filter(planned_date__lte=date_to)
        return queryset

    def _resolve_vessel_id(self) -> str:
        user = getattr(self.request, "user", None)
        vessel_id = self.request.query_params.get("vessel_id") or self.request.data.get("vessel_id")
        if vessel_id not in (None, ""):
            if not user_has_vessel_access(user, vessel_id):
                self.permission_denied(self.request, message="You are not assigned to this vessel.")
            return str(vessel_id)
        vessel_ids = sorted(get_scoped_vessel_ids(user))
        return str(vessel_ids[0]) if vessel_ids else ""

    def _ensure_applicability_process_permission(self, *, is_approval: bool) -> None:
        permission_cls = (
            self.applicability_approve_permission_class
            if is_approval
            else self.applicability_request_permission_class
        )
        permission = permission_cls()
        if not permission.has_permission(self.request, self):
            self.permission_denied(self.request, message=permission.message)

    def _ensure_role_gate(self, *, roles: set[str], message: str) -> None:
        if _normalized_role(getattr(self.request, "user", None)) not in roles:
            self.permission_denied(self.request, message=message)

    def _ensure_safety_officer_gate(self, *, vessel_id: str) -> None:
        user = getattr(self.request, "user", None)
        actor_role = _normalized_role(user)
        if actor_role in DEFAULT_SAFETY_OFFICER_ROLES:
            return
        if actor_role in ALTERNATE_SAFETY_OFFICER_ROLES:
            ensure_soi_runtime_schema()
            actor_ids = _resolve_actor_ids(user)
            setting = SOIOfficerSetting.objects.filter(
                vessel_id=str(vessel_id),
                alternate_enabled=True,
                alternate_so_crew_id__in=actor_ids,
            ).first()
            if setting is not None:
                return
            self.permission_denied(
                self.request,
                message="2/E alternate Safety Officer is not enabled by Master for this vessel.",
            )
        self.permission_denied(
            self.request,
            message="SOI action is restricted to the active Safety Officer.",
        )

    def _resolve_reference_date(
        self,
        raw_value: object | None,
        *,
        field_name: str,
        default_to_today: bool = True,
    ) -> date | None:
        if raw_value in (None, ""):
            return timezone.localdate() if default_to_today else None
        try:
            return date.fromisoformat(str(raw_value))
        except ValueError as exc:
            raise drf_serializers.ValidationError({field_name: "Enter a valid date in YYYY-MM-DD format."}) from exc

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        return get_by_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])

    def get_inspection(self, inspection_id) -> SOIInspection:
        queryset = self._apply_filters(SOIInspection.objects.filter(is_deleted=False))
        return get_by_id_or_pk(queryset, inspection_id)


class SOIListCreateView(SOIViewMixin, generics.ListCreateAPIView):
    lookup_url_kwarg = "id"
    queryset = SOIInspection.objects.filter(is_deleted=False)

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method == "POST":
            permissions.append(self.create_process_permission_class())
        return permissions

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SOIInspectionCreateSerializer
        return SOIInspectionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor_id = _resolve_actor_id(request.user)
        inspection = serializer.save(created_by=actor_id, updated_by=actor_id)
        response_serializer = SOIInspectionSerializer(
            inspection,
            context=self.get_serializer_context(),
        )
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=201, headers=headers)


class SOIDetailView(SOIViewMixin, generics.RetrieveAPIView):
    lookup_url_kwarg = "id"
    queryset = SOIInspection.objects.filter(is_deleted=False)
    serializer_class = SOIInspectionSerializer

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())


class SOIApplicabilityView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIApplicabilityUpdateSerializer

    def get_permissions(self):
        return [self.applicability_form_permission_class()]

    def get(self, request, *args, **kwargs):
        vessel_id = self._resolve_vessel_id()
        payload = self.get_soi_repository().list_applicability(vessel_id=vessel_id)
        serializer = SOIApplicabilitySerializer(payload, many=True)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        is_approval = any(request.data.get(key) not in (None, "") for key in ("dpa_signature", "dpa_decision"))
        self._ensure_applicability_process_permission(is_approval=is_approval)
        if is_approval:
            self._ensure_role_gate(
                roles={"DPA"},
                message="SOI area-applicability approval is restricted to DPA (D-GAP-M19).",
            )
        else:
            self._ensure_role_gate(
                roles={"MASTER"},
                message="SOI area-applicability requests are restricted to Master (D-GAP-M19).",
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        response_serializer_cls = (
            SOIApplicabilityApprovalResultSerializer
            if is_approval
            else SOIApplicabilityRequestResultSerializer
        )
        response_serializer = response_serializer_cls(payload)
        return Response(response_serializer.data, status=200)


class SOIApplicabilityRequestView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIApplicabilityRequestPayloadSerializer

    def get_permissions(self):
        return [self.applicability_form_permission_class(), self.applicability_request_permission_class()]

    def get(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"MASTER"},
            message="SOI area-applicability requests are restricted to Master (D-GAP-M19).",
        )
        inspection = self.get_inspection(kwargs["id"])
        payload = {
            "inspection_id": inspection.id,
            "inspection_reference": inspection.inspection_reference,
            "vessel_id": inspection.vessel_id,
            "areas": self.get_soi_repository().list_applicability(vessel_id=inspection.vessel_id),
        }
        return Response(
            {
                **payload,
                "areas": SOIApplicabilitySerializer(payload["areas"], many=True).data,
            }
        )

    def post(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"MASTER"},
            message="SOI area-applicability requests are restricted to Master (D-GAP-M19).",
        )
        inspection = self.get_inspection(kwargs["id"])
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "vessel_id": inspection.vessel_id},
        )
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        response_serializer = SOIApplicabilityRequestResultSerializer(payload)
        return Response(response_serializer.data, status=201)


class SOIApplicabilityApproveView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIApplicabilityApprovalPayloadSerializer

    def get_permissions(self):
        return [self.applicability_form_permission_class(), self.applicability_approve_permission_class()]

    def get(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"DPA"},
            message="SOI area-applicability approval is restricted to DPA (D-GAP-M19).",
        )
        inspection = self.get_inspection(kwargs["id"])
        pending_requests = self.get_soi_repository().list_pending_applicability_requests(
            vessel_id=inspection.vessel_id
        )
        return Response(
            {
                "inspection_id": inspection.id,
                "inspection_reference": inspection.inspection_reference,
                "vessel_id": inspection.vessel_id,
                "pending_requests": SOIPendingApplicabilityRequestSerializer(
                    pending_requests,
                    many=True,
                ).data,
            }
        )

    def post(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"DPA"},
            message="SOI area-applicability approval is restricted to DPA (D-GAP-M19).",
        )
        inspection = self.get_inspection(kwargs["id"])
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "vessel_id": inspection.vessel_id},
        )
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        response_serializer = SOIApplicabilityApprovalResultSerializer(payload)
        return Response(response_serializer.data, status=200)
