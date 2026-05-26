from __future__ import annotations

import json
import re
import uuid
from collections.abc import Iterable

from django.db import connection
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.safety.authentication.roles import normalized_authority_role
from apps.safety.authentication.permissions import (
    HasAnyFormPermission,
    HasFormPermission,
    HasProcessPermission,
    HasRolePermission,
)
from apps.safety.models import (
    MasterImmediateCause,
    MasterLossType,
    MasterMscatTaxonomy,
    MasterSafetyBiasGuard,
    MasterSafetyIncidentType,
    MasterSoiArea,
    MasterSoiAreaItem,
    SafetyCaseStudy,
    SOIChecklistVersion,
)
from apps.safety.serializers import (
    MasterImmediateCauseSerializer,
    MasterLossTypeSerializer,
    MasterMscatTaxonomySerializer,
    MasterSOIAreaItemSerializer,
    MasterSOIAreaSerializer,
    MasterSafetyBiasGuardSerializer,
    MasterSafetyIncidentTypeSerializer,
    SafetyCaseStudySerializer,
    SOIChecklistVersionAdminSerializer,
)
from apps.safety.services.field_history_recorder import capture_model_state, record_field_changes, resolve_actor_id


_NUMBER_RE = re.compile(r"\d+")


def _natural_item_number_key(value: object) -> tuple[tuple[int, ...], str]:
    text = str(value or "").strip()
    numbers = tuple(int(part) for part in _NUMBER_RE.findall(text))
    return numbers, text.lower()


def _normalize_permission_ids(value: object) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return set()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                pass
            else:
                return _normalize_permission_ids(parsed)
        return {part.strip() for part in stripped.split(",") if part.strip()}
    if isinstance(value, Iterable):
        return {str(item).strip() for item in value if str(item).strip()}
    text = str(value).strip()
    return {text} if text else set()


class RejectNonDpaReferenceAdminRead(BasePermission):
    message = "Only DPA may access the Safety reference admin surface."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        auth = getattr(request, "auth", None)
        auth_form_ids = auth.get("form_ids") if hasattr(auth, "get") else getattr(auth, "form_ids", None)
        form_ids = _normalize_permission_ids(getattr(user, "form_ids", None)) | _normalize_permission_ids(auth_form_ids)
        if "SAF_F_018" not in form_ids:
            return True
        return normalized_authority_role(user) == "DPA"


def _build_reference_update_kwargs(instance, *, user) -> dict[str, object]:
    update_kwargs: dict[str, object] = {}
    field_names = {field.name for field in instance._meta.fields}
    if "updated_by" in field_names:
        update_kwargs["updated_by"] = resolve_actor_id(user)
    if "updated_date" in field_names:
        update_kwargs["updated_date"] = timezone.now()
    return update_kwargs


def _next_legacy_int_id(model) -> int:
    table_name = model._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COALESCE(MAX(legacy_int_id), 0) + 1 FROM {table_name}")
        return int(cursor.fetchone()[0])


def _create_reference_record(model, validated_data: dict[str, object], create_kwargs: dict[str, object]):
    data = {**validated_data, **create_kwargs}
    field_names = {field.name for field in model._meta.fields}
    if "id" in field_names:
        data["id"] = uuid.uuid4().hex
    if "legacy_int_id" in field_names and connection.vendor != "microsoft":
        data["legacy_int_id"] = _next_legacy_int_id(model)

    columns = tuple(data.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(columns)
    values = [data[column] for column in columns]
    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {model._meta.db_table} ({column_sql}) VALUES ({placeholders})",
            values,
        )
    return model.objects.get(pk=data["id"])


class DpaReferenceAdminPermissionMixin:
    form_permission_class = HasFormPermission.requiring("SAF_F_018")
    role_permission_class = HasRolePermission.requiring("DPA")
    read_permission_class = HasAnyFormPermission.requiring_any(
        "SAF_F_001",  # Incident
        "SAF_F_002",  # Near miss
        "SAF_F_003",  # SCM
        "SAF_F_004",  # SOI
        "SAF_F_013",  # Corrective action
        "SAF_F_018",  # Safety reference admin
        "SAF_F_020",  # Auditor/export surfaces
    )
    read_admin_guard_class = RejectNonDpaReferenceAdminRead

    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [self.read_permission_class(), self.read_admin_guard_class()]
        return [self.form_permission_class(), self.role_permission_class()]


class DpaReferenceWritePermissionMixin(DpaReferenceAdminPermissionMixin):
    process_permission_class = None

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.process_permission_class is not None:
            permissions.append(self.process_permission_class())
        return permissions


class ReferenceListView(DpaReferenceAdminPermissionMixin, generics.GenericAPIView):
    queryset = None
    serializer_class = None

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class ReferenceDetailView(DpaReferenceWritePermissionMixin, generics.GenericAPIView):
    queryset = None
    serializer_class = None
    lookup_field = "pk"
    history_field_names: tuple[str, ...] = ()
    write_reason = "Safety reference data updated."

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)
        if self.lookup_field == "pk" and lookup_value is not None and str(lookup_value).isdigit():
            queryset = self.filter_queryset(self.get_queryset())
            return get_object_or_404(queryset, legacy_int_id=int(lookup_value))
        return super().get_object()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        tracked_fields = self.history_field_names or tuple(self.get_serializer(instance).fields.keys())
        old_state = capture_model_state(instance, field_names=tracked_fields)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        record = serializer.save(**_build_reference_update_kwargs(instance, user=request.user))
        record_field_changes(
            record,
            old_state,
            user=request.user,
            field_names=tracked_fields,
            change_reason=self.write_reason,
            parent_table=record._meta.db_table,
        )
        return Response(self.get_serializer(record).data)


class ReferenceListCreateView(DpaReferenceWritePermissionMixin, generics.GenericAPIView):
    queryset = None
    serializer_class = None
    history_field_names: tuple[str, ...] = ()
    create_reason = "Safety reference data created."

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_kwargs = {}
        model_fields = getattr(serializer.Meta.model._meta, "fields", ())
        field_names = {field.name for field in model_fields}
        if "created_by" in field_names:
            create_kwargs["created_by"] = resolve_actor_id(request.user)
        model = serializer.Meta.model
        if any(field.name == "legacy_int_id" for field in model._meta.fields):
            record = _create_reference_record(model, serializer.validated_data, create_kwargs)
        else:
            record = serializer.save(**create_kwargs)
        tracked_fields = self.history_field_names or tuple(self.get_serializer(record).fields.keys())
        old_state = {field_name: None for field_name in tracked_fields}
        record_field_changes(
            record,
            old_state,
            user=request.user,
            field_names=tracked_fields,
            change_reason=self.create_reason,
            parent_table=record._meta.db_table,
        )
        return Response(self.get_serializer(record).data, status=201)


class ReferenceMscatListView(ReferenceListView):
    queryset = MasterMscatTaxonomy.objects.order_by("category_id", "subcode_id")
    serializer_class = MasterMscatTaxonomySerializer


class ReferenceMscatDetailView(ReferenceDetailView):
    queryset = MasterMscatTaxonomy.objects.order_by("category_id", "subcode_id")
    serializer_class = MasterMscatTaxonomySerializer
    lookup_field = "subcode_id"
    process_permission_class = HasProcessPermission.requiring("SAF_P_018")
    history_field_names = (
        "category_name",
        "subcode_description",
        "cause_type",
        "active",
        "updated_by",
        "updated_date",
    )
    write_reason = "DPA updated M-SCAT taxonomy."


class ReferenceImmediateCauseListView(ReferenceListView):
    queryset = MasterImmediateCause.objects.order_by("category_id", "subcode_id")
    serializer_class = MasterImmediateCauseSerializer


class ReferenceImmediateCauseDetailView(ReferenceDetailView):
    queryset = MasterImmediateCause.objects.order_by("category_id", "subcode_id")
    serializer_class = MasterImmediateCauseSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_018")
    history_field_names = (
        "category_name",
        "subcode_description",
        "cause_type",
        "active",
        "updated_by",
        "updated_date",
    )
    write_reason = "DPA updated immediate-cause taxonomy."


class ReferenceLossTypeListView(ReferenceListView):
    queryset = MasterLossType.objects.order_by("loss_type_id")
    serializer_class = MasterLossTypeSerializer


class ReferenceLossTypeDetailView(ReferenceDetailView):
    queryset = MasterLossType.objects.order_by("loss_type_id")
    serializer_class = MasterLossTypeSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_018")
    history_field_names = (
        "loss_type_name",
        "description",
        "active",
    )
    write_reason = "DPA updated loss-type taxonomy."


class ReferenceSOIAreaListView(ReferenceListView):
    queryset = MasterSoiArea.objects.order_by("display_order", "area_id")
    serializer_class = MasterSOIAreaSerializer


class ReferenceSOIAreaDetailView(ReferenceDetailView):
    queryset = MasterSoiArea.objects.order_by("display_order", "area_id")
    serializer_class = MasterSOIAreaSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_019")
    history_field_names = (
        "area_name",
        "section_12_flag",
        "display_order",
        "active",
    )
    write_reason = "DPA updated SOI area taxonomy."


class ReferenceSOIItemListView(ReferenceListView):
    serializer_class = MasterSOIAreaItemSerializer

    def get_queryset(self):
        queryset = MasterSoiAreaItem.objects.order_by("area_id", "subsection_id", "id")
        area_id = self.request.query_params.get("area_id")
        if area_id not in (None, ""):
            queryset = queryset.filter(area_id=area_id)
        return queryset

    def get(self, request, *args, **kwargs):
        rows = sorted(
            list(self.get_queryset()),
            key=lambda row: (
                int(row.area_id),
                int(row.subsection_id),
                _natural_item_number_key(row.item_number),
                str(row.id),
            ),
        )
        serializer = self.get_serializer(rows, many=True)
        return Response(serializer.data)


class ReferenceSOIItemDetailView(ReferenceDetailView):
    queryset = MasterSoiAreaItem.objects.order_by("area_id", "subsection_id", "item_number", "id")
    serializer_class = MasterSOIAreaItemSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_019")
    history_field_names = (
        "description",
        "tier",
        "active",
        "updated_by",
        "updated_date",
    )
    write_reason = "DPA updated SOI checklist item."


class ReferenceSOIChecklistVersionListView(ReferenceListCreateView):
    queryset = SOIChecklistVersion.objects.order_by("-effective_from", "-id")
    serializer_class = SOIChecklistVersionAdminSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_019")
    history_field_names = (
        "version_label",
        "effective_from",
        "effective_to",
        "source_description",
        "active",
        "created_by",
        "created_date",
    )
    create_reason = "DPA created SOI checklist version."


class ReferenceSOIChecklistVersionDetailView(ReferenceDetailView):
    queryset = SOIChecklistVersion.objects.order_by("-effective_from", "-id")
    serializer_class = SOIChecklistVersionAdminSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_019")
    history_field_names = (
        "version_label",
        "effective_from",
        "effective_to",
        "source_description",
        "active",
    )
    write_reason = "DPA updated SOI checklist version."


class ReferenceBiasGuardListView(ReferenceListView):
    queryset = MasterSafetyBiasGuard.objects.order_by("bit_position", "id")
    serializer_class = MasterSafetyBiasGuardSerializer


class ReferenceIncidentTypeListView(ReferenceListView):
    queryset = MasterSafetyIncidentType.objects.order_by("type_code")
    serializer_class = MasterSafetyIncidentTypeSerializer


class ReferenceIncidentTypeDetailView(ReferenceDetailView):
    queryset = MasterSafetyIncidentType.objects.order_by("type_code")
    serializer_class = MasterSafetyIncidentTypeSerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_018")
    history_field_names = (
        "type_name",
        "imo_reportable",
        "description",
        "active",
    )
    write_reason = "DPA updated incident-type taxonomy."


class ReferenceCaseStudyListCreateView(ReferenceListCreateView):
    queryset = SafetyCaseStudy.objects.order_by("display_order", "title")
    serializer_class = SafetyCaseStudySerializer
    process_permission_class = HasProcessPermission.requiring("SAF_P_018")
    history_field_names = (
        "slug",
        "title",
        "event_type",
        "loss_summary",
        "incident_date",
        "immediate_cause_codes",
        "basic_cause_codes",
        "narrative",
        "recommendations",
        "source_label",
        "active",
        "display_order",
        "created_by",
        "created_date",
    )
    create_reason = "DPA created Safety case study."


class ReferenceCaseStudyDetailView(ReferenceDetailView):
    queryset = SafetyCaseStudy.objects.order_by("display_order", "title")
    serializer_class = SafetyCaseStudySerializer
    lookup_field = "slug"
    process_permission_class = HasProcessPermission.requiring("SAF_P_018")
    history_field_names = (
        "title",
        "event_type",
        "loss_summary",
        "incident_date",
        "immediate_cause_codes",
        "basic_cause_codes",
        "narrative",
        "recommendations",
        "source_label",
        "active",
        "display_order",
        "updated_by",
        "updated_date",
    )
    write_reason = "DPA updated Safety case study."


class CaseStudyHelpDrawerListView(generics.GenericAPIView):
    serializer_class = SafetyCaseStudySerializer
    permission_class = HasAnyFormPermission.requiring_any("SAF_F_001", "SAF_F_018")

    def get_permissions(self):
        return [self.permission_class()]

    def get(self, request, *args, **kwargs):
        queryset = SafetyCaseStudy.objects.filter(active=True).order_by("display_order", "title")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
