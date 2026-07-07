from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.authentication.vessel_scope import _resolve_vessel_scope_ids
from apps.safety.models import ExternalPartyInjury, Incident
from apps.safety.serializers.incident_external_party import ExternalPartyInjurySerializer
from apps.safety.serializers.vessel_display import resolve_vessel_display
from apps.safety.services.self_report_guard import check_self_report_conflict


PHASE_1_NARRATIVE_MIN_LENGTH = 200


def derive_investigation_depth(risk_band: str | None) -> str | None:
    if risk_band == Incident.RiskBand.RED:
        return Incident.InvestigationDepth.DEEP
    if risk_band == Incident.RiskBand.YELLOW:
        return Incident.InvestigationDepth.MEDIUM
    if risk_band == Incident.RiskBand.GREEN:
        return Incident.InvestigationDepth.SHALLOW
    return None


def validate_loss_type_selection(attrs, incident: Incident | None = None) -> None:
    ids = [
        attrs.get("loss_type_primary_id", getattr(incident, "loss_type_primary_id", None)),
        attrs.get("loss_type_secondary_id", getattr(incident, "loss_type_secondary_id", None)),
        attrs.get("loss_type_tertiary_id", getattr(incident, "loss_type_tertiary_id", None)),
    ]
    selected_ids = [loss_id for loss_id in ids if loss_id not in (None, "")]
    other_text = attrs.get("loss_type_other", getattr(incident, "loss_type_other", None))
    other_selected = other_text is not None
    total_count = len(selected_ids) + (1 if other_selected else 0)

    if len(selected_ids) != len(set(selected_ids)):
        raise serializers.ValidationError({"loss_type_primary_id": "Do not select the same type of loss more than once."})
    if total_count > 3:
        raise serializers.ValidationError({"loss_type_primary_id": "Select maximum three types of loss including Other."})
    if other_selected and not str(other_text or "").strip():
        raise serializers.ValidationError({"loss_type_other": "Specify the other type of loss."})


class IncidentPhase1Serializer(serializers.ModelSerializer):
    draft_reference = serializers.SerializerMethodField(read_only=True)
    external_party_injury = ExternalPartyInjurySerializer(required=False, allow_null=True)
    reporter_user_id = serializers.CharField(
        source="reporter_id",
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    vessel_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = (
            "id",
            "id",
            "incident_number",
            "draft_reference",
            "vessel_id",
            "vessel_name",
            "vessel_display_name",
            "record_type",
            "state",
            "current_phase",
            "risk_band",
            "imo_classifier",
            "incident_type_id",
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
            "narrative",
            "awaiting_daily_report_match",
            "external_party_injury",
            "office_notified",
            "office_notification_mode",
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
            "vessel_code",
        )
        read_only_fields = (
            "id",
            "id",
            "incident_number",
            "draft_reference",
            "record_type",
            "state",
            "current_phase",
            "imo_classifier",
            "investigation_depth",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        extra_kwargs = {
            "schema_version": {"required": False},
            "created_by": {"required": False},
            "updated_by": {"required": False},
        }

    def get_draft_reference(self, instance: Incident) -> str | None:
        return instance.draft_reference

    def _get_vessel_display(self, instance: Incident) -> dict[str, str]:
        request = self.context.get("request")
        return resolve_vessel_display(instance.vessel_id, user=getattr(request, "user", None))

    def get_vessel_name(self, instance: Incident) -> str:
        return self._get_vessel_display(instance)["vessel_name"]

    def get_vessel_display_name(self, instance: Incident) -> str:
        return self._get_vessel_display(instance)["vessel_display_name"]

    def to_representation(self, instance):
        payload = super().to_representation(instance)
        payload["vessel_code"] = self._get_vessel_display(instance)["vessel_code"]
        return payload

    def validate(self, attrs):
        attrs = super().validate(attrs)
        incident = self.instance

        vessel_id = attrs.get("vessel_id", getattr(incident, "vessel_id", None))
        if vessel_id:
            user = getattr(self.context.get("request"), "user", None)
            if not getattr(user, "is_global", False) and not getattr(user, "global_access", False):
                allowed_vessel_ids = _resolve_vessel_scope_ids(user)
                normalized_vessel_id = str(vessel_id).strip() if vessel_id not in (None, "") else None
                if not allowed_vessel_ids or normalized_vessel_id not in allowed_vessel_ids:
                    raise serializers.ValidationError({"vessel_id": "You are not assigned to this vessel."})

        occurred_at = attrs.get("occurred_at", getattr(incident, "occurred_at", None))
        reported_at = attrs.get("reported_at", getattr(incident, "reported_at", None))
        now = timezone.now()

        errors: dict[str, str] = {}
        if occurred_at is not None and reported_at is not None and occurred_at > reported_at:
            errors["occurred_at"] = "Incident occurred time cannot be after reported time."
        if reported_at is not None and reported_at > now:
            errors["reported_at"] = "Reported time cannot be in the future."
        if occurred_at is not None and occurred_at > now:
            errors["occurred_at"] = "Occurred time cannot be in the future."
        risk_band = attrs.get("risk_band", getattr(incident, "risk_band", None))
        office_notified = attrs.get("office_notified", getattr(incident, "office_notified", None))
        office_notification_mode = attrs.get(
            "office_notification_mode",
            getattr(incident, "office_notification_mode", None),
        )
        if office_notified is True and not office_notification_mode:
            errors["office_notification_mode"] = "Select the mode of communication."
        if office_notified is False:
            attrs["office_notification_mode"] = None
        if risk_band:
            attrs["investigation_depth"] = derive_investigation_depth(risk_band)
            attrs["imo_classifier"] = Incident.ImoClassifier.NOT_APPLICABLE
        validate_loss_type_selection(attrs, incident)
        if errors:
            raise serializers.ValidationError(errors)

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


class IncidentPhase1SubmitSerializer(serializers.Serializer):
    conflict_acknowledged = serializers.BooleanField(required=False, default=False)
    conflict_approver_role = serializers.CharField(required=False, allow_blank=False)
    injured_party_id = serializers.CharField(required=False, allow_blank=False)
    pic_candidate_id = serializers.CharField(required=False, allow_blank=False)
    person_in_charge_id = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        errors: dict[str, str] = {}

        if incident.current_phase != 1:
            errors["current_phase"] = "Only Phase 1 incidents can be submitted through this endpoint."

        narrative = (incident.narrative or "").strip()
        if len(narrative) < PHASE_1_NARRATIVE_MIN_LENGTH:
            errors["narrative"] = "Incident narrative must be at least 200 characters."

        now = timezone.now()
        if incident.reported_at and incident.reported_at > now:
            errors["reported_at"] = "Reported time cannot be in the future."
        if incident.occurred_at and incident.occurred_at > now:
            errors["occurred_at"] = "Occurred time cannot be in the future."
        if incident.occurred_at and incident.reported_at and incident.occurred_at > incident.reported_at:
            errors["occurred_at"] = "Incident occurred time cannot be after reported time."

        if not incident.reporter_id:
            errors["reporter_user_id"] = "Reporter identity is required before submitting Phase 1."
        if not incident.reporter_name:
            errors["reporter_name"] = "Reporter typed name is required before submitting Phase 1."
        if not incident.reporter_rank:
            errors["reporter_rank"] = "Reporter rank is required before submitting Phase 1."
        if not incident.reporter_device_fingerprint:
            errors["reporter_device_fingerprint"] = (
                "Reporter device fingerprint is required before submitting Phase 1."
            )
        if not incident.risk_band:
            errors["risk_band"] = "Select the internal risk band before submitting."
        if incident.office_notified is None:
            errors["office_notified"] = "Select whether office was notified."
        if incident.office_notified is True and not incident.office_notification_mode:
            errors["office_notification_mode"] = "Select the mode of communication."

        conflict = check_self_report_conflict(
            incident.reporter_id,
            {
                **attrs,
                "reporter_rank": incident.reporter_rank,
            },
            user=getattr(self.context.get("request"), "user", None),
            reporter_rank=incident.reporter_rank,
        )
        if conflict.conflict_detected:
            if not attrs.get("conflict_acknowledged"):
                errors["conflict_acknowledged"] = (
                    "Acknowledge the self-report conflict before submitting Phase 1."
                )
            provided_role = attrs.get("conflict_approver_role")
            if provided_role != conflict.required_approver_role:
                errors["conflict_approver_role"] = (
                    f"Conflict detected - assign {conflict.required_approver_role} as the different approver."
                )
            attrs["self_report_conflict"] = {
                "conflict_detected": True,
                "message": conflict.message,
                "required_approver_role": conflict.required_approver_role,
            }
        else:
            attrs["self_report_conflict"] = {
                "conflict_detected": False,
                "message": "",
                "required_approver_role": None,
            }

        if errors:
            raise serializers.ValidationError(errors)
        return attrs
