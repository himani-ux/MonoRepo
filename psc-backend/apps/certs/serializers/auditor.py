from __future__ import annotations

from datetime import timedelta
from typing import Any
import json

from django.utils import timezone
from rest_framework import serializers

from apps.certs.serializers.tracked_item import serialize_tracked_item
from apps.certs.services.auditor_access_repository import parse_scope


REDACTED_INTERNAL_NOTE = "[REDACTED - internal note]"
MAX_AUDITOR_GRANT_DAYS = 30
DEFAULT_AUDITOR_GRANT_DAYS = 7


class AuditorScopeSerializer(serializers.Serializer):
    vesselIds = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=False)
    sections = serializers.ListField(child=serializers.CharField(max_length=64), required=False, allow_empty=True)
    certIds = serializers.ListField(child=serializers.CharField(max_length=64), required=False, allow_empty=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs["vesselIds"] = _clean_list(attrs.get("vesselIds"))
        attrs["sections"] = _clean_list(attrs.get("sections"))
        attrs["certIds"] = _clean_list(attrs.get("certIds"))
        if not attrs["vesselIds"]:
            raise serializers.ValidationError({"vesselIds": "Select at least one vessel."})
        return attrs


class AuditorAccessCreateSerializer(serializers.Serializer):
    auditorName = serializers.CharField(max_length=128)
    auditorEmail = serializers.EmailField(max_length=256)
    scope = AuditorScopeSerializer()
    expiryAt = serializers.DateTimeField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        now = timezone.now()
        expiry_at = attrs.get("expiryAt") or (now + timedelta(days=DEFAULT_AUDITOR_GRANT_DAYS))
        if expiry_at <= now:
            raise serializers.ValidationError({"expiryAt": "Expiry must be in the future."})
        if expiry_at > now + timedelta(days=MAX_AUDITOR_GRANT_DAYS):
            raise serializers.ValidationError({"expiryAt": "External auditor access cannot exceed 30 days."})
        attrs["expiryAt"] = expiry_at
        return attrs


class AuditorAccessExpirySerializer(serializers.Serializer):
    expiryAt = serializers.DateTimeField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        allowed = {"expiryAt"}
        extra = sorted(set(self.initial_data.keys()) - allowed)
        if extra:
            raise serializers.ValidationError({field: "Only expiryAt can be edited." for field in extra})
        return attrs


def serialize_auditor_grant(row: dict[str, Any]) -> dict[str, Any]:
    scope = parse_scope(row.get("scope_json"))
    return {
        "id": str(row.get("grant_id")),
        "auditorName": row.get("auditor_name"),
        "auditorEmail": row.get("auditor_email"),
        "scope": scope,
        "expiryAt": row.get("expiry_at"),
        "grantedBy": row.get("granted_by"),
        "grantedAt": row.get("granted_at"),
        "signupTokenUsedAt": row.get("signup_token_used_at"),
        "lastAccessedAt": row.get("last_accessed_at"),
        "revokedViaExpiryEdit": bool(row.get("revoked_via_expiry_edit")),
    }


def serialize_auditor_vessel(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id")),
        "imo": str(row.get("imo") or ""),
        "name": row.get("name"),
        "code": row.get("code"),
    }


def serialize_auditor_tracked_item(row: dict[str, Any]) -> dict[str, Any]:
    data = serialize_tracked_item(row)
    if data.get("extensionReason"):
        data["extensionReason"] = REDACTED_INTERNAL_NOTE
    if data.get("rejectionReason"):
        data["rejectionReason"] = REDACTED_INTERNAL_NOTE
    data["vesselName"] = row.get("vessel_name")
    data["vesselImo"] = str(row.get("vessel_imo") or "")
    return data


def scope_json(scope: dict[str, Any] | str) -> str:
    return json.dumps(parse_scope(scope), default=str)


def _clean_list(value: Any) -> list[str]:
    return [str(item).strip() for item in (value or []) if str(item).strip()]
