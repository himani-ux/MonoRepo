from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.authentication.anonymity import AnonymityMixin
from apps.safety.authentication.vessel_scope import user_has_vessel_access
from apps.safety.models import ExternalPartyInjury, Incident, IncidentPhaseLog, SafetyFieldHistory
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
            "incident_type_other",
            "loss_type_primary_id",
            "loss_type_secondary_id",
            "loss_type_tertiary_id",
            "loss_type_other",
            "investigation_depth",
            "occurred_at",
            "reported_at",
            "latitude",
            "longitude",
            "shore_assistance_required",
            "vessel_location",
            "vessel_location_detail",
            "onboard_location",
            "last_port",
            "departure_date",
            "vessel_condition",
            "position_source",
            "position_daily_report_id",
            "weather_visibility_id",
            "weather_precipitation_id",
            "weather_sea_state_id",
            "weather_wind_scale_id",
            "weather_wind_direction_id",
            "weather_lighting_source_id",
            "weather_current_direction_id",
            "weather_current_strength_knots",
            "weather_ambient_temperature_c",
            "weather_ice_condition_onboard_id",
            "weather_ice_condition_at_sea_id",
            "weather_light_condition_id",
            "risk_assessment_carried_out",
            "toolbox_meeting_carried_out",
            "permit_issued",
            "activity_type",
            "narrative",
            "awaiting_daily_report_match",
            "notification_channel_count",
            "resources_allocated",
            "pic_user_id",
            "dpa_notified_at",
            "fm_notified_at",
            "office_notified_at",
            "office_notified",
            "office_notification_mode",
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
            "office_comment",
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
    external_party_injury = ExternalPartyInjurySerializer(required=False, allow_null=True)
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
        has_injury_payload = "external_party_injury" in validated_data
        injury_payload = validated_data.pop("external_party_injury", None)
        incident = repository.create(validated_data)
        if has_injury_payload and injury_payload:
            self._upsert_injury(incident, injury_payload)
        return incident

    def update(self, instance, validated_data):
        repository = self.context["incident_repository"]
        validated_data.pop("vessel_code", None)
        has_injury_payload = "external_party_injury" in validated_data
        injury_payload = validated_data.pop("external_party_injury", None)
        incident = repository.update(instance.pk, validated_data)
        if has_injury_payload and injury_payload:
            self._upsert_injury(incident, injury_payload)
        return incident

    def _upsert_injury(self, incident: Incident, injury_payload: dict) -> None:
        user = getattr(self.context.get("request"), "user", None)
        actor_id = str(
            getattr(user, "id", None)
            or getattr(user, "username", None)
            or getattr(user, "crew_id", None)
            or "system"
        )
        record, was_created = ExternalPartyInjury.objects.get_or_create(
            incident=incident,
            defaults={
                **injury_payload,
                "created_by": actor_id,
                "schema_version": incident.schema_version or 1,
                "updated_by": actor_id,
                "updated_date": timezone.now(),
            },
        )
        if was_created:
            return

        update_fields = []
        for field_name, value in {
            **injury_payload,
            "schema_version": incident.schema_version or 1,
            "updated_by": actor_id,
            "updated_date": timezone.now(),
        }.items():
            setattr(record, field_name, value)
            update_fields.append(field_name)
        record.save(update_fields=update_fields)


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
