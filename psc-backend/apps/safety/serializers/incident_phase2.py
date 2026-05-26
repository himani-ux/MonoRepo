from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import Incident
from apps.safety.services.band_classifier import classify_band


class IncidentPhase2Serializer(serializers.ModelSerializer):
    draft_reference = serializers.SerializerMethodField(read_only=True)
    advisory_band = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Incident
        fields = (
            "id",
            "id",
            "incident_number",
            "draft_reference",
            "state",
            "current_phase",
            "risk_band",
            "imo_classifier",
            "investigation_depth",
            "pic_user_id",
            "dpa_notified_at",
            "fm_notified_at",
            "office_notified_at",
            "notification_channel_count",
            "resources_allocated",
            "loss_type_primary_id",
            "latitude",
            "longitude",
            "schema_version",
            "advisory_band",
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
            "state",
            "current_phase",
            "dpa_notified_at",
            "fm_notified_at",
            "office_notified_at",
            "notification_channel_count",
            "resources_allocated",
            "advisory_band",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )

    def get_draft_reference(self, instance: Incident) -> str | None:
        return instance.draft_reference

    def get_advisory_band(self, instance: Incident) -> str:
        return classify_band(loss_type=instance.loss_type_primary_id).band

    def validate(self, attrs):
        attrs = super().validate(attrs)
        incident = self.instance
        current_phase = attrs.get("current_phase", getattr(incident, "current_phase", None))
        if incident is not None and current_phase != 2:
            raise serializers.ValidationError(
                {"current_phase": "Phase 2 resources can only be edited while current_phase = 2."}
            )

        imo_classifier = attrs.get("imo_classifier", getattr(incident, "imo_classifier", None))
        latitude = attrs.get("latitude", getattr(incident, "latitude", None))
        longitude = attrs.get("longitude", getattr(incident, "longitude", None))

        if imo_classifier and imo_classifier != Incident.ImoClassifier.NOT_APPLICABLE:
            errors: dict[str, str] = {}
            if latitude in (None, ""):
                errors["latitude"] = (
                    "Position is mandatory for IMO-classified casualties. Auto-fill from Daily Report within ±12h or enter manually."
                )
            if longitude in (None, ""):
                errors["longitude"] = (
                    "Position is mandatory for IMO-classified casualties. Auto-fill from Daily Report within ±12h or enter manually."
                )
            if errors:
                raise serializers.ValidationError(errors)

        return attrs

    def update(self, instance, validated_data):
        repository = self.context["incident_repository"]
        return repository.update(instance.pk, validated_data)


class IncidentPhase2SubmitSerializer(serializers.Serializer):
    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        errors: dict[str, str] = {}

        if incident.current_phase != 2:
            errors["current_phase"] = "Only Phase 2 incidents can be submitted through this endpoint."
        if not incident.risk_band:
            errors["risk_band"] = "Risk band must be GREEN, YELLOW, or RED."
        if not incident.imo_classifier:
            errors["imo_classifier"] = "IMO classifier must be SMC, MC, MI, or NOT_APPLICABLE."
        if incident.imo_classifier and incident.imo_classifier != Incident.ImoClassifier.NOT_APPLICABLE:
            if incident.latitude in (None, ""):
                errors["latitude"] = (
                    "Position is mandatory for IMO-classified casualties. Auto-fill from Daily Report within ±12h or enter manually."
                )
            if incident.longitude in (None, ""):
                errors["longitude"] = (
                    "Position is mandatory for IMO-classified casualties. Auto-fill from Daily Report within ±12h or enter manually."
                )

        for forbidden_key in attrs:
            if "acting" in forbidden_key or "deputy" in forbidden_key:
                errors[forbidden_key] = (
                    "Acting-role / deputy-chain concepts not supported (D-GAP-A3 / A4)."
                )

        if errors:
            raise serializers.ValidationError(errors)
        return attrs
