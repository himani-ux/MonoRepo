from __future__ import annotations

import uuid

from django.db import DatabaseError, connection
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.safety.services.soi_assistant_validator import ALTERNATE_SAFETY_OFFICER_RANKS
from apps.safety.models import SOIOfficerSetting
from apps.safety.serializers import SOIOfficerSettingSerializer, SOIOfficerSettingUpdateSerializer
from apps.safety.services.field_history_recorder import resolve_actor_id
from apps.safety.services.soi_officer_setting_table import TABLE_NAME, ensure_soi_officer_setting_table
from apps.safety.views.soi import SOIViewMixin


class SOIOfficerSettingView(SOIViewMixin, generics.GenericAPIView):
    serializer_class = SOIOfficerSettingSerializer

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method != "GET":
            permissions.append(self.applicability_request_permission_class())
        return permissions

    def get(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"MASTER", "CO", "CHIEF OFFICER", "SO", "SAFETY OFFICER", "2E", "2/E", "SECOND ENGINEER"},
            message="SOI alternate Safety Officer setting is restricted to SOI vessel roles.",
        )
        try:
            setting, _created = self._get_or_create_setting()
        except DatabaseError:
            ensure_soi_officer_setting_table()
            setting, _created = self._get_or_create_setting()
        return Response(self._build_response(setting))

    def patch(self, request, *args, **kwargs):
        self._ensure_role_gate(
            roles={"MASTER"},
            message="SOI alternate Safety Officer setting is restricted to Master.",
        )
        payload_serializer = SOIOfficerSettingUpdateSerializer(data=request.data)
        payload_serializer.is_valid(raise_exception=True)
        try:
            setting, created = self._get_or_create_setting()
        except DatabaseError:
            ensure_soi_officer_setting_table()
            setting, created = self._get_or_create_setting()
        payload = payload_serializer.validated_data
        alternate_candidates = self._list_alternate_candidates()
        alternate_candidate_ids = {str(candidate.get("crew_id") or "").strip() for candidate in alternate_candidates}
        requested_alternate_id = str(payload.get("alternate_so_crew_id") or "").strip()
        if payload["alternate_enabled"] and requested_alternate_id not in alternate_candidate_ids:
            raise ValidationError(
                {"alternate_so_crew_id": "Select an active 2/E from the current vessel crew list."}
            )
        actor_id = resolve_actor_id(request.user)
        now_value = timezone.now()

        setting.alternate_enabled = bool(payload["alternate_enabled"])
        setting.alternate_so_crew_id = (
            requested_alternate_id if setting.alternate_enabled else None
        )
        setting.reason = str(payload.get("reason") or "").strip() or None
        setting.updated_by = actor_id
        setting.updated_date = now_value
        if created:
            setting.created_by = actor_id
        if setting.alternate_enabled:
            setting.enabled_by = actor_id
            setting.enabled_at = now_value
            setting.disabled_by = None
            setting.disabled_at = None
        else:
            setting.disabled_by = actor_id
            setting.disabled_at = now_value
        setting.save()

        return Response(self._build_response(setting, alternate_candidates=alternate_candidates))

    def _get_or_create_setting(self):
        ensure_soi_officer_setting_table()
        vessel_id = self._resolve_vessel_id()
        setting = SOIOfficerSetting.objects.filter(vessel_id=str(vessel_id)).first()
        if setting is not None:
            return setting, False

        now_value = timezone.now()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {TABLE_NAME} (
                        id,
                        vessel_id,
                        alternate_enabled,
                        schema_version,
                        created_date
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    [uuid.uuid4().hex, str(vessel_id), False, 1, now_value],
                )
        except DatabaseError:
            setting = SOIOfficerSetting.objects.filter(vessel_id=str(vessel_id)).first()
            if setting is not None:
                return setting, False
            raise

        return (
            SOIOfficerSetting.objects.get(vessel_id=str(vessel_id)),
            True,
        )

    def _list_alternate_candidates(self):
        vessel_id = self._resolve_vessel_id()
        return [
            row
            for row in self.get_cms_repository().list_current_vessel_crew(vessel_id=str(vessel_id))
            if str(row.get("rank") or "").strip().upper() in ALTERNATE_SAFETY_OFFICER_RANKS
        ]

    def _build_response(self, setting: SOIOfficerSetting, *, alternate_candidates=None):
        payload = self.get_serializer(setting).data
        payload["alternate_candidates"] = alternate_candidates if alternate_candidates is not None else self._list_alternate_candidates()
        return payload
