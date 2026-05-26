from __future__ import annotations

from rest_framework import serializers

from apps.safety.authentication.anonymity import AnonymityMixin
from apps.safety.authentication.vessel_scope import user_has_vessel_access
from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.serializers.incident_external_party import ExternalPartyInjurySerializer
from apps.safety.serializers.vessel_display import VesselDisplayMixin


def _is_vessel_user(user) -> bool:
    if user is None:
        return False
    user_type = str(getattr(user, "user_type", "") or "").strip().upper()
    if user_type == "VESSEL":
        return True
    work_side = getattr(user, "work_side", None)
    return work_side in (1, True, "1", "SHIP", "VESSEL")


class IncidentSerializer(AnonymityMixin, VesselDisplayMixin, serializers.ModelSerializer):
    draft_reference = serializers.SerializerMethodField()
    external_party_injury = ExternalPartyInjurySerializer(read_only=True)
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
            "draft_reference",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "record_type",
            "state",
            "current_phase",
            "risk_band",
            "imo_classifier",
            "incident_type_id",
            "loss_type_primary_id",
            "investigation_depth",
            "occurred_at",
            "reported_at",
            "latitude",
            "longitude",
            "position_source",
            "position_daily_report_id",
            "narrative",
            "awaiting_daily_report_match",
            "first_hour_checklist_done",
            "notification_channel_count",
            "resources_allocated",
            "pic_user_id",
            "dpa_notified_at",
            "fm_notified_at",
            "office_notified_at",
            "near_miss_priority",
            "external_party_injury",
            "reporter_user_id",
            "reporter_name",
            "reporter_rank",
            "reporter_email",
            "reporter_department",
            "reporter_device_fingerprint",
            "chain_of_custody_ok",
            "marine_docs_checklist_done",
            "cargo_evidence_applicable",
            "health_fatigue_applicable",
            "causal_layering_complete",
            "alarp_attested",
            "bias_guard_attestations",
            "blame_fixation_override_by",
            "dpa_accepted_at",
            "dpa_accepted_by",
            "fm_approved_at",
            "fm_approved_by",
            "closed_at",
            "closure_reason",
            "linked_incident_id",
            "superseded_by_id",
            "schema_version",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = (
            "id",
            "id",
            "incident_number",
            "draft_reference",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "created_date",
            "updated_date",
        )

    def get_draft_reference(self, instance: Incident) -> str | None:
        return instance.draft_reference


class IncidentListSerializer(IncidentSerializer):
    class Meta(IncidentSerializer.Meta):
        fields = (
            "id",
            "incident_number",
            "draft_reference",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "record_type",
            "state",
            "current_phase",
            "risk_band",
            "imo_classifier",
            "occurred_at",
            "reported_at",
            "schema_version",
            "created_date",
        )


class IncidentCreateSerializer(IncidentSerializer):
    vessel_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta(IncidentSerializer.Meta):
        fields = IncidentSerializer.Meta.fields
        read_only_fields = tuple(
            field_name for field_name in IncidentSerializer.Meta.read_only_fields if field_name != "vessel_code"
        )
        extra_kwargs = {
            "schema_version": {"required": False},
            "created_by": {"required": False},
            "updated_by": {"required": False},
            "record_type": {"required": False},
            "state": {"required": False},
            "current_phase": {"required": False},
            "vessel_id": {"required": False, "allow_blank": True},
        }

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

        target_vessel_id = attrs.get("vessel_id", getattr(self.instance, "vessel_id", None))
        if not target_vessel_id:
            raise serializers.ValidationError({"vessel_id": "This field is required."})
        if not user_has_vessel_access(user, target_vessel_id):
            raise serializers.ValidationError({"vessel_id": "You are not assigned to this vessel."})

        occurred_at = attrs.get("occurred_at")
        reported_at = attrs.get("reported_at")
        if occurred_at is not None and reported_at is not None and occurred_at > reported_at:
            raise serializers.ValidationError(
                {"occurred_at": "Occurred time cannot be after reported time."}
            )
        return attrs

    def create(self, validated_data):
        repository = self.context["incident_repository"]
        return repository.create(validated_data)

    def update(self, instance, validated_data):
        repository = self.context["incident_repository"]
        validated_data.pop("vessel_code", None)
        return repository.update(instance.pk, validated_data)


class IncidentTransitionSerializer(serializers.Serializer):
    target_phase = serializers.IntegerField(min_value=1, max_value=9)
    loop_back_reason = serializers.CharField(required=False, allow_blank=False)


class PhaseLogSerializer(serializers.ModelSerializer):
    incident_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = IncidentPhaseLog
        fields = (
            "id",
            "id",
            "incident_id",
            "phase_from",
            "phase_to",
            "transition_type",
            "loop_back_reason",
            "actor_user_id",
            "actor_role_code",
            "occurred_at",
            "device_fingerprint",
            "signature_valid",
            "schema_version",
        )
        read_only_fields = fields


class FieldHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyFieldHistory
        fields = (
            "id",
            "id",
            "parent_table",
            "parent_id",
            "field_name",
            "old_value",
            "new_value",
            "change_reason",
            "actor_user_id",
            "actor_role_code",
            "changed_at",
            "schema_version",
        )
        read_only_fields = fields
