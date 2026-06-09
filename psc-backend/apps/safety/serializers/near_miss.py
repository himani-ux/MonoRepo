from __future__ import annotations

import json

from django.utils import timezone
from rest_framework import serializers

from apps.safety.authentication.anonymity import AnonymityMixin
from apps.safety.authentication.vessel_scope import user_has_vessel_access
from apps.safety.models import (
    Incident,
    IncidentPhaseLog,
    MasterLossType,
    MasterMscatTaxonomy,
    MasterSafetyIncidentType,
    NearMissGuidancePrompt,
    NearMissKpiTarget,
)
from apps.safety.identifiers import is_uuid_identifier
from apps.safety.serializers.vessel_display import VesselDisplayMixin


def _is_vessel_user(user) -> bool:
    if user is None:
        return False
    user_type = str(getattr(user, "user_type", "") or "").strip().upper()
    if user_type == "VESSEL":
        return True
    work_side = getattr(user, "work_side", None)
    return work_side in (1, True, "1", "SHIP", "VESSEL")


NEAR_MISS_CATEGORY_TAGS = {
    "Safety",
    "Security",
    "Environment",
    "MLC",
    "Training",
    "Operational",
    "Management",
    "Others",
}
NEAR_MISS_LOSS_CATEGORY_TAGS = {
    "Injury",
    "Property Damage",
    "Environment",
    "Financial",
    "Reputation",
    "Time",
    "Non-conformity",
}
NEAR_MISS_OTHER_PREFIX = "Others:"

LEGACY_SHELL_TAGS = {"Software", "Hardware", "Environment", "Liveware", "Liveware-Liveware"}

NEAR_MISS_PLACES = {
    "AT_ANCHOR",
    "AT_SEA",
    "AT_PORT",
}


class NearMissJsonListField(serializers.ListField):
    def to_representation(self, value):
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return []
        return parsed if isinstance(parsed, list) else []


def _json_dump_list(values: list[object]) -> str:
    return json.dumps(values, separators=(",", ":"))


class NearMissSerializer(AnonymityMixin, VesselDisplayMixin, serializers.ModelSerializer):
    near_miss_category_tags = NearMissJsonListField(child=serializers.CharField(), required=False)
    near_miss_incident_type_ids = NearMissJsonListField(child=serializers.CharField(), required=False)
    near_miss_mscat_subcode_ids = NearMissJsonListField(child=serializers.CharField(), required=False)
    vessel_code = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()
    rework_summary = serializers.SerializerMethodField()
    reporter_user_id = serializers.CharField(
        source="reporter_id",
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Incident
        fields = (
            "id",
            "id",
            "incident_number",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "record_type",
            "state",
            "current_phase",
            "occurred_at",
            "reported_at",
            "incident_type_id",
            "loss_type_primary_id",
            "narrative",
            "near_miss_priority",
            "near_miss_severity",
            "near_miss_place",
            "near_miss_shell_tag",
            "near_miss_category_tags",
            "near_miss_incident_type_ids",
            "near_miss_mscat_category_id",
            "near_miss_mscat_subcode_id",
            "near_miss_mscat_subcode_ids",
            "near_miss_immediate_action",
            "near_miss_suggestion",
            "near_miss_root_cause_detail",
            "near_miss_corrective_action",
            "near_miss_weather_voyage_details",
            "near_miss_equipment_details",
            "near_miss_lessons_learned",
            "reporter_user_id",
            "reporter_name",
            "reporter_rank",
            "reporter_email",
            "reporter_department",
            "reporter_device_fingerprint",
            "schema_version",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
            "rework_summary",
        )
        read_only_fields = (
            "id",
            "incident_number",
            "record_type",
            "state",
            "current_phase",
            "created_date",
            "updated_date",
        )

    def get_rework_summary(self, obj: Incident) -> dict[str, object] | None:
        phase_log = (
            IncidentPhaseLog.objects.filter(
                incident=obj,
                transition_type=IncidentPhaseLog.TransitionType.REWORK,
            )
            .order_by("-occurred_at", "-id")
            .first()
        )
        if phase_log is None:
            return None
        comment = str(phase_log.loop_back_reason or "").strip()
        if not comment:
            return None
        return {
            "comment": comment,
            "requested_at": phase_log.occurred_at,
            "requested_by": phase_log.actor_user_id,
            "requested_by_role": phase_log.actor_role_code,
        }


class NearMissListSerializer(NearMissSerializer):
    class Meta(NearMissSerializer.Meta):
        fields = (
            "id",
            "id",
            "incident_number",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "record_type",
            "state",
            "occurred_at",
            "reported_at",
            "incident_type_id",
            "loss_type_primary_id",
            "near_miss_priority",
            "near_miss_severity",
            "reporter_name",
            "schema_version",
        )


class NearMissCreateSerializer(NearMissSerializer):
    incident_type_id = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    vessel_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta(NearMissSerializer.Meta):
        fields = NearMissSerializer.Meta.fields
        read_only_fields = tuple(
            field_name
            for field_name in NearMissSerializer.Meta.read_only_fields + ("near_miss_priority",)
            if field_name != "vessel_code"
        )
        extra_kwargs = {
            "schema_version": {"required": False},
            "record_type": {"required": False},
            "state": {"required": False},
            "current_phase": {"required": False},
            "created_by": {"required": False},
            "updated_by": {"required": False},
            "reported_at": {"required": False},
            "vessel_id": {"required": False, "allow_blank": True},
        }

    def validate_narrative(self, value: str) -> str:
        if len(value.strip()) < 100:
            raise serializers.ValidationError(
                "Near-miss description must be at least 100 characters (D-GAP-M38)."
            )
        return value

    def validate_near_miss_severity(self, value: str | None) -> str:
        normalized = str(value or "").strip().upper()
        if normalized not in {"HIGH", "MED", "LOW"}:
            raise serializers.ValidationError("Select a severity level before submitting.")
        return normalized

    def validate_near_miss_place(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip().upper()
        if normalized not in NEAR_MISS_PLACES:
            raise serializers.ValidationError("Select a valid place.")
        return normalized

    def validate_near_miss_category_tags(self, value: list[str] | None) -> list[str]:
        return self._validate_limited_list(
            value or [],
            field_name="near_miss_category_tags",
            item_validator=self._validate_category_tag,
        )

    def validate_near_miss_incident_type_ids(self, value: list[object] | None) -> list[str]:
        return self._validate_limited_list(
            value or [],
            field_name="near_miss_incident_type_ids",
            item_validator=lambda item: str(item).strip(),
        )

    def validate_near_miss_mscat_subcode_ids(self, value: list[object] | None) -> list[str]:
        return self._validate_limited_list(
            value or [],
            field_name="near_miss_mscat_subcode_ids",
            item_validator=lambda item: str(item).strip(),
        )

    def validate_near_miss_shell_tag(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = self._validate_category_tag(value)
        return normalized

    def _validate_category_tag(self, value: object) -> str:
        normalized = str(value or "").strip()
        allowed = NEAR_MISS_CATEGORY_TAGS | NEAR_MISS_LOSS_CATEGORY_TAGS | LEGACY_SHELL_TAGS
        if normalized not in allowed and not normalized.startswith(NEAR_MISS_OTHER_PREFIX):
            raise serializers.ValidationError("Category must match the Safety SSOT values.")
        return normalized

    def _shell_tag_for_category(self, value: str | None) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if normalized.startswith(NEAR_MISS_OTHER_PREFIX):
            return "Others"
        if normalized in NEAR_MISS_LOSS_CATEGORY_TAGS:
            return "Others"
        return normalized[:32]

    def _validate_limited_list(self, value: list[object], *, field_name: str, item_validator) -> list[str]:
        if not isinstance(value, list):
            raise serializers.ValidationError("Expected a list.")
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            normalized = item_validator(item)
            if not normalized or normalized in seen:
                continue
            cleaned.append(normalized)
            seen.add(normalized)
        if len(cleaned) > 3:
            raise serializers.ValidationError("Select up to 3 values only.")
        return cleaned

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if _is_vessel_user(user):
            vessel_id = str(getattr(user, "vessel_id", "") or "").strip()
            vessel_code = str(getattr(user, "vessel_code", "") or "").strip()
            if not vessel_id:
                raise serializers.ValidationError(
                    {"vessel_id": "Authenticated vessel user is missing vessel assignment."}
                )
            attrs["vessel_id"] = vessel_id
            if vessel_code:
                attrs["vessel_code"] = vessel_code

        if not attrs.get("vessel_id"):
            raise serializers.ValidationError({"vessel_id": "This field is required."})
        if not user_has_vessel_access(user, attrs.get("vessel_id")):
            raise serializers.ValidationError({"vessel_id": "You are not assigned to this vessel."})
        if not str(attrs.get("reporter_device_fingerprint") or "").strip():
            raise serializers.ValidationError(
                {"reporter_device_fingerprint": "Digital signature requires device fingerprint (D-GAP-D1)."}
            )
        if not attrs.get("near_miss_severity"):
            raise serializers.ValidationError({"near_miss_severity": "Select a severity level before submitting."})
        incident_type_values = attrs.get("near_miss_incident_type_ids") or []
        if incident_type_values:
            attrs["incident_type_id"] = incident_type_values[0]
        if not attrs.get("incident_type_id"):
            raise serializers.ValidationError({"incident_type_id": "This field is required."})
        if not attrs.get("loss_type_primary_id"):
            raise serializers.ValidationError({"loss_type_primary_id": "This field is required."})
        resolved_incident_types = self._resolve_incident_types([attrs["incident_type_id"], *incident_type_values])
        if not resolved_incident_types:
            raise serializers.ValidationError({"incident_type_id": "Select a valid Safety incident type."})
        attrs["incident_type_id"] = resolved_incident_types[0]
        attrs["near_miss_incident_type_ids"] = _json_dump_list(resolved_incident_types[:3])
        if not MasterLossType.objects.filter(loss_type_id=attrs["loss_type_primary_id"], active=True).exists():
            raise serializers.ValidationError({"loss_type_primary_id": "Select a valid Safety loss type."})

        category_tags = attrs.get("near_miss_category_tags") or []
        if category_tags:
            attrs["near_miss_shell_tag"] = self._shell_tag_for_category(category_tags[0])
        if category_tags:
            attrs["near_miss_category_tags"] = _json_dump_list(category_tags[:3])

        subcode_values = attrs.get("near_miss_mscat_subcode_ids") or []
        if subcode_values:
            attrs["near_miss_mscat_subcode_id"] = subcode_values[0]
        resolved_mscat = self._resolve_mscat_subcodes([attrs.get("near_miss_mscat_subcode_id"), *subcode_values])
        if resolved_mscat:
            attrs["near_miss_mscat_subcode_id"] = resolved_mscat[0].subcode_id
            attrs["near_miss_mscat_category_id"] = resolved_mscat[0].category_id
            attrs["near_miss_mscat_subcode_ids"] = _json_dump_list([row.subcode_id for row in resolved_mscat[:3]])

        occurred_at = attrs.get("occurred_at")
        reported_at = attrs.get("reported_at")
        effective_reported_at = reported_at or timezone.now()
        if occurred_at is None:
            raise serializers.ValidationError({"occurred_at": "Occurred time is required."})
        if occurred_at > timezone.now():
            raise serializers.ValidationError({"occurred_at": "Occurred time cannot be in the future."})
        if occurred_at > effective_reported_at:
            raise serializers.ValidationError(
                {"occurred_at": "Occurred time cannot be after reported time."}
            )
        return attrs

    def _resolve_incident_types(self, values: list[object]) -> list[int]:
        resolved: list[int] = []
        seen: set[int] = set()
        for value in values:
            incident_type = self._resolve_incident_type(value)
            legacy_id = getattr(incident_type, "legacy_int_id", None)
            if legacy_id is not None and legacy_id not in seen:
                resolved.append(int(legacy_id))
                seen.add(int(legacy_id))
        return resolved[:3]

    def _resolve_mscat_subcodes(self, values: list[object]) -> list[MasterMscatTaxonomy]:
        subcodes: list[str] = []
        seen: set[str] = set()
        for value in values:
            subcode = str(value or "").strip()
            if subcode and subcode not in seen:
                subcodes.append(subcode)
                seen.add(subcode)
        if not subcodes:
            return []
        rows = MasterMscatTaxonomy.objects.filter(subcode_id__in=subcodes[:3], active=True)
        row_by_subcode = {row.subcode_id: row for row in rows}
        missing = [subcode for subcode in subcodes[:3] if subcode not in row_by_subcode]
        if missing:
            raise serializers.ValidationError({"near_miss_mscat_subcode_ids": "Select valid immediate causes."})
        return [row_by_subcode[subcode] for subcode in subcodes[:3]]

    def _resolve_incident_type(self, value: object) -> MasterSafetyIncidentType | None:
        raw_value = str(value or "").strip()
        if not raw_value:
            return None
        if is_uuid_identifier(raw_value):
            return MasterSafetyIncidentType.objects.filter(id=raw_value, active=True).first()
        if raw_value.isdigit():
            return MasterSafetyIncidentType.objects.filter(legacy_int_id=int(raw_value), active=True).first()
        return None

    def create(self, validated_data):
        repository = self.context["incident_repository"]
        validated_data["record_type"] = Incident.RecordType.NEAR_MISS
        validated_data.setdefault("state", Incident.State.PENDING_VESSEL_REVIEW)
        validated_data.setdefault("current_phase", 1)
        validated_data.setdefault("reported_at", timezone.now())
        validated_data.pop("near_miss_priority", None)
        return repository.create(validated_data)


class NearMissGuidancePromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = NearMissGuidancePrompt
        fields = (
            "id",
            "category_tag",
            "incident_type_id",
            "prompt_text",
            "display_order",
            "active",
        )
        read_only_fields = ("id",)

    def validate_category_tag(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip()
        if normalized not in NEAR_MISS_CATEGORY_TAGS:
            raise serializers.ValidationError("Category must match the Safety SSOT values.")
        return normalized


class NearMissKpiTargetSerializer(serializers.ModelSerializer):
    actual_count = serializers.IntegerField(read_only=True, required=False)
    variance = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = NearMissKpiTarget
        fields = (
            "id",
            "vessel_id",
            "year",
            "month",
            "target_count",
            "actual_count",
            "variance",
            "active",
        )
        read_only_fields = ("id", "actual_count", "variance")

    def validate_vessel_id(self, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("Vessel is required.")
        return value


class NearMissCategoryReclassifySerializer(serializers.Serializer):
    near_miss_shell_tag = serializers.ChoiceField(choices=tuple(sorted(NEAR_MISS_CATEGORY_TAGS)), required=False)
    near_miss_mscat_subcode_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def validate(self, attrs):
        if "near_miss_shell_tag" not in attrs and "near_miss_mscat_subcode_id" not in attrs:
            raise serializers.ValidationError("Select a category or root cause to reclassify.")

        subcode = str(attrs.get("near_miss_mscat_subcode_id") or "").strip()
        if subcode:
            mscat = MasterMscatTaxonomy.objects.filter(subcode_id=subcode, active=True).first()
            if mscat is None:
                raise serializers.ValidationError({"near_miss_mscat_subcode_id": "Select a valid root cause."})
            attrs["near_miss_mscat_subcode_id"] = mscat.subcode_id
            attrs["near_miss_mscat_category_id"] = mscat.category_id
        elif "near_miss_mscat_subcode_id" in attrs:
            attrs["near_miss_mscat_subcode_id"] = None
            attrs["near_miss_mscat_category_id"] = None
        return attrs
