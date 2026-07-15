from __future__ import annotations

from decimal import Decimal
import json
from typing import Any

from rest_framework import serializers


THRESHOLD_MIN = Decimal("0.000")
THRESHOLD_MAX = Decimal("1.000")


class AlertConfigPatchSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    dpaOverrideLeadDays = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=365)
    dpaOverrideRecipients = serializers.JSONField(required=False, allow_null=True)
    escalationCadence = serializers.JSONField(required=False)
    ocrThresholdOffice = serializers.DecimalField(required=False, max_digits=4, decimal_places=3, min_value=THRESHOLD_MIN, max_value=THRESHOLD_MAX)
    ocrThresholdVessel = serializers.DecimalField(required=False, max_digits=4, decimal_places=3, min_value=THRESHOLD_MIN, max_value=THRESHOLD_MAX)
    ocrThresholdManualFloor = serializers.DecimalField(required=False, max_digits=4, decimal_places=3, min_value=THRESHOLD_MIN, max_value=THRESHOLD_MAX)
    classSnapshotCadenceMonths = serializers.IntegerField(required=False, min_value=1, max_value=24)
    classSnapshotLeadMonths = serializers.IntegerField(required=False, min_value=0, max_value=12)
    eventSnapshotGraceDays = serializers.IntegerField(required=False, min_value=0, max_value=90)
    draftExpireDays = serializers.IntegerField(required=False, min_value=1, max_value=30)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        office = attrs.get("ocrThresholdOffice")
        vessel = attrs.get("ocrThresholdVessel")
        manual_floor = attrs.get("ocrThresholdManualFloor")
        if manual_floor is not None:
            if office is not None and manual_floor > office:
                raise serializers.ValidationError({"ocrThresholdManualFloor": "Manual floor cannot exceed the office threshold."})
            if vessel is not None and manual_floor > vessel:
                raise serializers.ValidationError({"ocrThresholdManualFloor": "Manual floor cannot exceed the vessel threshold."})
        return attrs


class RetentionOverrideSerializer(serializers.Serializer):
    blobId = serializers.UUIDField()
    dpaRetentionOverrideUntil = serializers.DateTimeField(allow_null=True)


class SlackRouteSerializer(serializers.Serializer):
    vesselId = serializers.CharField(max_length=64)
    slackChannelVessel = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=64)
    slackChannelOfficeDefault = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=64)


class SettingsPatchSerializer(serializers.Serializer):
    alertConfigs = AlertConfigPatchSerializer(many=True, required=False)
    retentionOverride = RetentionOverrideSerializer(required=False)
    slackRoutes = SlackRouteSerializer(many=True, required=False)
    reason = serializers.CharField(min_length=20)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs.get("alertConfigs") and not attrs.get("retentionOverride") and not attrs.get("slackRoutes"):
            raise serializers.ValidationError("At least one settings surface must be supplied.")
        return attrs


def serialize_settings_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    settings = snapshot.get("settings") or {}
    return {
        "id": str(settings.get("settings_id")) if settings.get("settings_id") else None,
        "singletonKey": settings.get("singleton_key") or "certs",
        "lastHeartbeatAt": settings.get("last_heartbeat_at"),
        "updatedAt": settings.get("updated_at"),
        "updatedBy": settings.get("updated_by"),
        "alertConfigs": [serialize_alert_config(row) for row in snapshot.get("alert_configs") or []],
        "slackRoutes": [serialize_slack_route(row) for row in snapshot.get("slack_routes") or []],
    }


def serialize_alert_config(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("config_id")),
        "triggerEvent": row.get("trigger_event"),
        "defaultLeadDays": row.get("default_lead_days"),
        "dpaOverrideLeadDays": row.get("dpa_override_lead_days"),
        "recipientsDefault": _json_load(row.get("recipients_default_json"), []),
        "dpaOverrideRecipients": _json_load(row.get("dpa_override_recipients_json"), None),
        "escalationCadence": _json_load(row.get("escalation_cadence_json"), {}),
        "ocrThresholdOffice": _decimal_float(row.get("ocr_threshold_office")),
        "ocrThresholdVessel": _decimal_float(row.get("ocr_threshold_vessel")),
        "ocrThresholdManualFloor": _decimal_float(row.get("ocr_threshold_manual_floor")),
        "classSnapshotCadenceMonths": row.get("class_snapshot_cadence_months"),
        "classSnapshotLeadMonths": row.get("class_snapshot_lead_months"),
        "eventSnapshotGraceDays": row.get("event_snapshot_grace_days"),
        "draftExpireDays": row.get("draft_expire_days"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "updatedBy": row.get("updated_by"),
    }


def serialize_slack_route(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "vesselId": str(row.get("vessel_id")) if row.get("vessel_id") else None,
        "vesselName": row.get("vessel_name"),
        "imo": row.get("imo_number"),
        "slackChannelVessel": row.get("slack_channel_vessel"),
        "slackChannelOfficeDefault": row.get("slack_channel_office_default"),
        "updatedAt": row.get("updated_at"),
        "updatedBy": row.get("updated_by"),
    }


def _json_load(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return fallback


def _decimal_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
