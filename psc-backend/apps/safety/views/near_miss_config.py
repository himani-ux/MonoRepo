from __future__ import annotations

from calendar import monthrange
from datetime import datetime
import json

from django.db.models import Count
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasAnyFormPermission, HasAnyProcessPermission, HasFormPermission
from apps.safety.authentication.roles import normalized_authority_role
from apps.safety.authentication.vessel_scope import filter_by_vessel_scope, user_has_vessel_access
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.models import Incident, NearMissCategory, NearMissCauseOption, NearMissGuidancePrompt, NearMissKpiTarget
from apps.safety.serializers import (
    NearMissCategoryReclassifySerializer,
    NearMissCategorySerializer,
    NearMissCauseOptionSerializer,
    NearMissGuidancePromptSerializer,
    NearMissKpiTargetSerializer,
    NearMissSerializer,
)
from apps.safety.services import capture_model_state, record_field_changes
from apps.safety.views.near_miss import NearMissViewMixin, _resolve_actor_id


def _is_dpa_or_safety_office(user) -> bool:
    return normalized_authority_role(user) in {"DPA", "FM", "SEQ MANAGER", "SAFETY MANAGER"}


class NearMissGuidancePromptView(generics.ListCreateAPIView):
    queryset = NearMissGuidancePrompt.objects.filter(active=True)
    serializer_class = NearMissGuidancePromptSerializer
    form_permission_class = HasFormPermission.requiring("SAF_F_002")
    write_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_002", "SAF_P_006")

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method not in {"GET", "HEAD", "OPTIONS"}:
            permissions.append(self.write_permission_class())
        return permissions

    def get_queryset(self):
        queryset = super().get_queryset()
        if category_tag := self.request.query_params.get("category_tag"):
            queryset = queryset.filter(category_tag=str(category_tag).strip())
        if incident_type_id := self.request.query_params.get("incident_type_id"):
            try:
                queryset = queryset.filter(incident_type_id=int(incident_type_id))
            except (TypeError, ValueError):
                queryset = queryset.none()
        return queryset

    def perform_create(self, serializer):
        actor_id = _resolve_actor_id(self.request.user)
        serializer.save(created_by=actor_id, updated_by=actor_id, updated_date=timezone.now())


class NearMissCategoryView(generics.ListAPIView):
    queryset = NearMissCategory.objects.filter(active=True)
    serializer_class = NearMissCategorySerializer
    pagination_class = None
    form_permission_class = HasFormPermission.requiring("SAF_F_002")

    def get_permissions(self):
        return [self.form_permission_class()]


class NearMissCauseOptionView(generics.ListAPIView):
    queryset = NearMissCauseOption.objects.filter(active=True)
    serializer_class = NearMissCauseOptionSerializer
    pagination_class = None
    form_permission_class = HasAnyFormPermission.requiring_any("SAF_F_001", "SAF_F_002")

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if factor := self.request.query_params.get("factor"):
            queryset = queryset.filter(factor=str(factor).strip().upper())
        if cause_stage := self.request.query_params.get("cause_stage"):
            queryset = queryset.filter(cause_stage=str(cause_stage).strip().upper())
        return queryset


class NearMissKpiTargetView(generics.GenericAPIView):
    queryset = NearMissKpiTarget.objects.filter(active=True)
    serializer_class = NearMissKpiTargetSerializer
    form_permission_class = HasFormPermission.requiring("SAF_F_002")
    write_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_002", "SAF_P_006")

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method not in {"GET", "HEAD", "OPTIONS"}:
            permissions.append(self.write_permission_class())
        return permissions

    def get(self, request, *args, **kwargs):
        vessel_id = str(request.query_params.get("vessel_id") or "").strip()
        today = timezone.localdate()
        year = self._positive_int(request.query_params.get("year"), default=today.year)
        month = self._positive_int(request.query_params.get("month"), default=today.month)
        if not vessel_id:
            raise ValidationError({"vessel_id": "Vessel is required."})
        if not user_has_vessel_access(request.user, vessel_id):
            raise PermissionDenied("You are not assigned to this vessel.")

        target = NearMissKpiTarget.objects.filter(
            vessel_id=vessel_id,
            year=year,
            month=month,
            active=True,
        ).first()
        actual_count = self._actual_count(vessel_id=vessel_id, year=year, month=month)
        data = {
            "id": str(target.id) if target else None,
            "vessel_id": vessel_id,
            "year": year,
            "month": month,
            "target_count": target.target_count if target else 0,
            "actual_count": actual_count,
            "variance": actual_count - (target.target_count if target else 0),
            "active": True,
        }
        return Response(data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attrs = serializer.validated_data
        if not user_has_vessel_access(request.user, attrs["vessel_id"]):
            raise PermissionDenied("You are not assigned to this vessel.")
        actor_id = _resolve_actor_id(request.user)
        target, _created = NearMissKpiTarget.objects.update_or_create(
            vessel_id=attrs["vessel_id"],
            year=attrs["year"],
            month=attrs["month"],
            defaults={
                "target_count": attrs["target_count"],
                "active": attrs.get("active", True),
                "updated_by": actor_id,
                "updated_date": timezone.now(),
            },
        )
        if not target.created_by:
            target.created_by = actor_id
            target.save(update_fields=("created_by",))
        actual_count = self._actual_count(vessel_id=target.vessel_id, year=target.year, month=target.month)
        payload = NearMissKpiTargetSerializer(target).data
        payload["actual_count"] = actual_count
        payload["variance"] = actual_count - target.target_count
        return Response(payload, status=status.HTTP_200_OK)

    def _positive_int(self, value, *, default: int) -> int:
        if value in (None, ""):
            return default
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Year and month must be numeric.") from exc
        return parsed

    def _actual_count(self, *, vessel_id: str, year: int, month: int) -> int:
        start = timezone.make_aware(datetime(year, month, 1))
        end = timezone.make_aware(datetime(year, month, monthrange(year, month)[1], 23, 59, 59, 999999))
        return Incident.objects.filter(
            is_deleted=False,
            record_type=Incident.RecordType.NEAR_MISS,
            vessel_id=vessel_id,
        ).filter(
            created_date__gte=start,
            created_date__lte=end,
        ).aggregate(total=Count("id"))["total"] or 0


class NearMissCategoryReclassifyView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissCategoryReclassifySerializer
    process_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_002", "SAF_P_006")

    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get_queryset(self):
        return filter_by_vessel_scope(
            super().get_queryset().filter(record_type=Incident.RecordType.NEAR_MISS),
            getattr(self.request, "user", None),
        )

    def patch(self, request, *args, **kwargs):
        if not _is_dpa_or_safety_office(request.user):
            raise PermissionDenied("Only DPA/FM safety office users can reclassify near-miss categories.")
        near_miss = get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_state = capture_model_state(
            near_miss,
            field_names=(
                "near_miss_shell_tag",
                "near_miss_category_tags",
                "near_miss_mscat_category_id",
                "near_miss_mscat_subcode_id",
                "updated_by",
                "updated_date",
            ),
        )
        if "near_miss_shell_tag" in serializer.validated_data:
            near_miss.near_miss_shell_tag = serializer.validated_data["near_miss_shell_tag"]
            near_miss.near_miss_category_tags = json.dumps([
                serializer.validated_data.get("near_miss_category_tag") or serializer.validated_data["near_miss_shell_tag"]
            ])
        if "near_miss_mscat_subcode_id" in serializer.validated_data:
            near_miss.near_miss_mscat_subcode_id = serializer.validated_data["near_miss_mscat_subcode_id"]
            near_miss.near_miss_mscat_category_id = serializer.validated_data["near_miss_mscat_category_id"]
        near_miss.updated_by = _resolve_actor_id(request.user)
        near_miss.updated_date = timezone.now()
        near_miss.save(
            update_fields=(
                "near_miss_shell_tag",
                "near_miss_category_tags",
                "near_miss_mscat_category_id",
                "near_miss_mscat_subcode_id",
                "updated_by",
                "updated_date",
            )
        )
        record_field_changes(
            near_miss,
            old_state,
            user=request.user,
            field_names=(
                "near_miss_shell_tag",
                "near_miss_category_tags",
                "near_miss_mscat_category_id",
                "near_miss_mscat_subcode_id",
                "updated_by",
                "updated_date",
            ),
            change_reason=serializer.validated_data["reason"],
        )
        return Response(NearMissSerializer(near_miss, context=self.get_serializer_context()).data)
