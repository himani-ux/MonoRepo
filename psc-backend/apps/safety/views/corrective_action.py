from __future__ import annotations

from django.db import DatabaseError
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.authentication.vessel_scope import get_scoped_vessel_ids, has_global_vessel_scope
from apps.safety.models import CorrectiveAction, Incident, Recommendation, SCMAgendaItem, SCMMeeting
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers.corrective_action import (
    CorrectiveActionLinkPurchaseSerializer,
    CorrectiveActionPhysicalVerifySerializer,
    CorrectiveActionSerializer,
    CorrectiveActionTransitionSerializer,
    CorrectiveActionWriteSerializer,
)
from apps.safety.services.ca_aging import CorrectiveActionAgingService
from apps.safety.views.incident import _resolve_actor_id


class CorrectiveActionViewMixin:
    lookup_url_kwarg = "id"
    form_permission_class = HasFormPermission.requiring("SAF_F_001")

    def get_purchase_fk_enforcer(self):
        from apps.safety.services.purchase_fk_enforcer import PurchaseFKEnforcer

        return PurchaseFKEnforcer()

    def get_aging_service(self) -> CorrectiveActionAgingService:
        return CorrectiveActionAgingService()

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        process_permission = self.get_process_permission_class()
        if process_permission is not None and self.request.method != "GET":
            permissions.append(process_permission())
        return permissions

    def get_process_permission_class(self):
        return None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["aging_service"] = self.get_aging_service()
        context["purchase_fk_enforcer"] = self.get_purchase_fk_enforcer()
        context["user_id"] = _resolve_actor_id(getattr(self.request, "user", None))
        return context

    def get_queryset(self):
        queryset = CorrectiveAction.objects.filter(is_deleted=False).select_related(
            "recommendation",
            "recommendation__incident",
        )
        return self._apply_vessel_scope(queryset)

    def _apply_vessel_scope(self, queryset):
        user = getattr(self.request, "user", None)
        if has_global_vessel_scope(user):
            return queryset

        vessel_ids = sorted(get_scoped_vessel_ids(user))
        if not vessel_ids:
            return queryset.none()

        incident_ids = list(
            Incident.objects.filter(is_deleted=False, vessel_id__in=vessel_ids).values_list("id", flat=True)
        )
        try:
            meeting_ids = list(
                SCMMeeting.objects.filter(is_deleted=False, vessel_id__in=vessel_ids).values_list("id", flat=True)
            )
            agenda_ids = (
                list(SCMAgendaItem.objects.filter(meeting_id__in=meeting_ids).values_list("id", flat=True))
                if meeting_ids
                else []
            )
        except DatabaseError:
            meeting_ids = []
            agenda_ids = []

        vessel_filter = Q(recommendation__incident__vessel_id__in=vessel_ids)
        if incident_ids:
            vessel_filter |= Q(source_table=Incident._meta.db_table, source_id__in=incident_ids)
        if agenda_ids:
            vessel_filter |= Q(source_table=SCMAgendaItem._meta.db_table, source_id__in=agenda_ids)
        return queryset.filter(vessel_filter)

    def _ensure_write_vessel_scope(self, validated_data) -> None:
        user = getattr(self.request, "user", None)
        if has_global_vessel_scope(user):
            return

        vessel_ids = sorted(get_scoped_vessel_ids(user))
        if not vessel_ids:
            raise PermissionDenied("No vessel scope is assigned to this user.")

        recommendation_id = validated_data.get("recommendation_id")
        if recommendation_id is not None and not Recommendation.objects.filter(
            pk=recommendation_id,
            is_deleted=False,
            incident__vessel_id__in=vessel_ids,
        ).exists():
            raise PermissionDenied("You are not assigned to the vessel for this corrective action.")

        source_table = str(validated_data.get("source_table") or "").strip()
        source_id = validated_data.get("source_id")
        if source_table == Incident._meta.db_table and not Incident.objects.filter(
            pk=source_id,
            is_deleted=False,
            vessel_id__in=vessel_ids,
        ).exists():
            raise PermissionDenied("You are not assigned to the vessel for this corrective action.")
        if source_table == SCMAgendaItem._meta.db_table and not SCMAgendaItem.objects.filter(
            pk=source_id,
            meeting__vessel_id__in=vessel_ids,
        ).exists():
            raise PermissionDenied("You are not assigned to the vessel for this corrective action.")

    def get_object(self):
        return get_by_public_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])

    def _filtered_actions(self) -> list[CorrectiveAction]:
        queryset = self.get_queryset()
        params = self.request.query_params
        if source_table := params.get("source_table"):
            queryset = queryset.filter(source_table=source_table)
        if source_id := params.get("source_id"):
            queryset = queryset.filter(source_id=source_id)
        if incident_id := params.get("incident_id"):
            queryset = queryset.filter(
                Q(source_table="vims_safety_incident", source_id=incident_id)
                | Q(recommendation__incident_id=incident_id)
            )
        if vessel_id := params.get("vessel_id"):
            queryset = queryset.filter(recommendation__incident__vessel_id=str(vessel_id))
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)

        actions = list(queryset.order_by("id"))
        self.get_aging_service().sync_actions(actions)

        if aging_bucket := params.get("aging_bucket"):
            actions = [action for action in actions if action.aging_bucket == aging_bucket]
        return actions


class CorrectiveActionListCreateView(CorrectiveActionViewMixin, generics.GenericAPIView):
    serializer_class = CorrectiveActionWriteSerializer

    def get_process_permission_class(self):
        return HasProcessPermission.requiring("SAF_P_020")

    def get(self, request, *args, **kwargs):
        serializer = CorrectiveActionSerializer(
            self._filtered_actions(),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self._ensure_write_vessel_scope(serializer.validated_data)
        action = serializer.save()
        return Response(
            CorrectiveActionSerializer(action, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class CorrectiveActionDetailView(CorrectiveActionViewMixin, generics.GenericAPIView):
    serializer_class = CorrectiveActionWriteSerializer

    def get_process_permission_class(self):
        return HasProcessPermission.requiring("SAF_P_020")

    def get(self, request, *args, **kwargs):
        action = self.get_object()
        self.get_aging_service().sync_bucket(action)
        return Response(
            CorrectiveActionSerializer(action, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        action = self.get_object()
        serializer = self.get_serializer(
            action,
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        self.get_aging_service().sync_bucket(updated)
        return Response(
            CorrectiveActionSerializer(updated, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )


class CorrectiveActionLinkPurchaseView(CorrectiveActionViewMixin, generics.GenericAPIView):
    serializer_class = CorrectiveActionLinkPurchaseSerializer

    def get_process_permission_class(self):
        return HasProcessPermission.requiring("SAF_P_021")

    def post(self, request, *args, **kwargs):
        action = self.get_object()
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        action.purchase_req_id = serializer.validated_data["purchase_req_id"]
        action.updated_by = _resolve_actor_id(request.user)
        action.updated_date = timezone.now()
        action.save(update_fields=["purchase_req_id", "updated_by", "updated_date"])
        self.get_aging_service().sync_bucket(action)
        return Response(
            CorrectiveActionSerializer(action, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )


class CorrectiveActionTransitionView(CorrectiveActionViewMixin, generics.GenericAPIView):
    serializer_class = CorrectiveActionTransitionSerializer

    def get_process_permission_class(self):
        return HasProcessPermission.requiring("SAF_P_020")

    def post(self, request, *args, **kwargs):
        action = self.get_object()
        serializer = self.get_serializer(data=request.data, context={"action": action})
        serializer.is_valid(raise_exception=True)

        action.status = serializer.validated_data["status"]
        action.updated_by = _resolve_actor_id(request.user)
        action.updated_date = timezone.now()
        if action.status == CorrectiveAction.Status.CLOSED:
            action.closed_at = timezone.now()
            action.closed_by = _resolve_actor_id(request.user)
        elif action.status == CorrectiveAction.Status.REOPENED:
            action.closed_at = None
            action.closed_by = None
        action.save(update_fields=["status", "updated_by", "updated_date", "closed_at", "closed_by"])
        self.get_aging_service().sync_bucket(action)

        return Response(
            CorrectiveActionSerializer(action, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )


class CorrectiveActionPhysicalVerifyView(CorrectiveActionViewMixin, generics.GenericAPIView):
    serializer_class = CorrectiveActionPhysicalVerifySerializer

    def get_process_permission_class(self):
        return HasProcessPermission.requiring("SAF_P_022")

    def post(self, request, *args, **kwargs):
        action = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action.physical_verification_done = True
        action.physical_verification_at = timezone.now()
        action.physical_verification_by = _resolve_actor_id(request.user)
        action.physical_verification_note = serializer.validated_data["note"]
        action.updated_by = _resolve_actor_id(request.user)
        action.updated_date = timezone.now()
        action.save(
            update_fields=[
                "physical_verification_done",
                "physical_verification_at",
                "physical_verification_by",
                "physical_verification_note",
                "updated_by",
                "updated_date",
            ]
        )
        self.get_aging_service().sync_bucket(action)
        return Response(
            CorrectiveActionSerializer(action, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )
