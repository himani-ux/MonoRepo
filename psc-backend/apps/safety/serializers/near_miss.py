from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.authentication.anonymity import AnonymityMixin
from apps.safety.authentication.vessel_scope import user_has_vessel_access
from apps.safety.models import Incident, MasterLossType, MasterMscatTaxonomy, MasterSafetyIncidentType
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


class NearMissSerializer(AnonymityMixin, VesselDisplayMixin, serializers.ModelSerializer):
    vessel_code = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()
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
            "near_miss_shell_tag",
            "near_miss_mscat_category_id",
            "near_miss_mscat_subcode_id",
            "near_miss_immediate_action",
            "near_miss_suggestion",
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

    def validate_near_miss_shell_tag(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip()
        allowed = {"Software", "Hardware", "Environment", "Liveware", "Liveware-Liveware"}
        if normalized not in allowed:
            raise serializers.ValidationError("SHELL tag must match the Safety SSOT values.")
        return normalized

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
        if not attrs.get("incident_type_id"):
            raise serializers.ValidationError({"incident_type_id": "This field is required."})
        if not attrs.get("loss_type_primary_id"):
            raise serializers.ValidationError({"loss_type_primary_id": "This field is required."})
        incident_type = self._resolve_incident_type(attrs["incident_type_id"])
        if incident_type is None:
            raise serializers.ValidationError({"incident_type_id": "Select a valid Safety incident type."})
        attrs["incident_type_id"] = incident_type.legacy_int_id
        if not MasterLossType.objects.filter(loss_type_id=attrs["loss_type_primary_id"], active=True).exists():
            raise serializers.ValidationError({"loss_type_primary_id": "Select a valid Safety loss type."})

        mscat_subcode = str(attrs.get("near_miss_mscat_subcode_id") or "").strip()
        if mscat_subcode:
            mscat = MasterMscatTaxonomy.objects.filter(subcode_id=mscat_subcode, active=True).first()
            if mscat is None:
                raise serializers.ValidationError({"near_miss_mscat_subcode_id": "Select a valid M-SCAT code."})
            attrs["near_miss_mscat_subcode_id"] = mscat.subcode_id
            attrs["near_miss_mscat_category_id"] = mscat.category_id

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
