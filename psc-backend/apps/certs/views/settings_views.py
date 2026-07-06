from __future__ import annotations

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import HasSettingsReadPermission, IsSettingsWriter
from apps.certs.serializers.settings import (
    SettingsPatchSerializer,
    serialize_alert_config,
    serialize_settings_snapshot,
)
from apps.certs.services.audit_log import record_audit_event, resolve_actor_id
from apps.certs.services.settings_repository import SettingsRepository


repository = SettingsRepository()


class SettingsView(generics.GenericAPIView):
    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), HasSettingsReadPermission()]
        return [IsAuthenticated(), IsSettingsWriter()]

    def get(self, request, *args, **kwargs):
        return Response(serialize_settings_snapshot(repository.get_settings_snapshot()))

    def patch(self, request, *args, **kwargs):
        serializer = SettingsPatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.pop("reason")
        with transaction.atomic():
            before, after = repository.update_settings(
                values=dict(serializer.validated_data),
                actor_id=resolve_actor_id(request.user),
            )
            serialized_before = serialize_settings_snapshot(before)
            serialized_after = serialize_settings_snapshot(after)
            record_audit_event(
                actor=request.user,
                action="settings_change",
                entity_type="settings",
                entity_id="certs",
                before=serialized_before,
                after=serialized_after,
                reason=reason,
                metadata={
                    "source": "api.certs.settings",
                    "surfaces": sorted(key for key in serializer.validated_data.keys()),
                },
            )
        return Response(serialized_after)


class AlertConfigView(generics.GenericAPIView):
    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), HasSettingsReadPermission()]
        return [IsAuthenticated(), IsSettingsWriter()]

    def get(self, request, *args, **kwargs):
        return Response({"results": [serialize_alert_config(row) for row in repository.list_alert_configs()]})

    def patch(self, request, *args, **kwargs):
        payload = request.data if isinstance(request.data, dict) else {"alertConfigs": request.data}
        serializer = SettingsPatchSerializer(data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data.get("alertConfigs"):
            return Response({"alertConfigs": "At least one alert config row is required."}, status=status.HTTP_400_BAD_REQUEST)
        reason = serializer.validated_data.pop("reason")
        with transaction.atomic():
            before, after = repository.update_settings(
                values={"alertConfigs": serializer.validated_data["alertConfigs"]},
                actor_id=resolve_actor_id(request.user),
            )
            record_audit_event(
                actor=request.user,
                action="settings_change",
                entity_type="settings",
                entity_id="certs",
                before=serialize_settings_snapshot(before),
                after=serialize_settings_snapshot(after),
                reason=reason,
                metadata={"source": "api.certs.alerts.config", "surfaces": ["alertConfigs"]},
            )
        return Response({"results": serialize_settings_snapshot(after)["alertConfigs"]})
