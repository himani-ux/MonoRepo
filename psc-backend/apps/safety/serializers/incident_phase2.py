from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import Incident
from apps.safety.serializers.incident_phase1 import derive_investigation_depth, validate_loss_type_selection
from apps.safety.services.band_classifier import classify_band

INCIDENT_OFFICE_APPROVAL_LOCK_STATES = {
    Incident.State.APPROVED,
    Incident.State.CLOSED,
    Incident.State.SUPERSEDED,
}


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
            "office_notified",
            "office_notification_mode",
            "notification_channel_count",
            "resources_allocated",
            "loss_type_primary_id",
            "loss_type_secondary_id",
            "loss_type_tertiary_id",
            "loss_type_other",
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
        if incident is not None and getattr(incident, "state", None) in INCIDENT_OFFICE_APPROVAL_LOCK_STATES:
            raise serializers.ValidationError(
                {"state": "Incident phases cannot be edited after office approval."}
            )
        if incident is not None and current_phase < 2:
            raise serializers.ValidationError(
                {"current_phase": "Phase 2 resources can be edited after Phase 2 is reached."}
            )

        imo_classifier = attrs.get("imo_classifier", getattr(incident, "imo_classifier", None))
        latitude = attrs.get("latitude", getattr(incident, "latitude", None))
        longitude = attrs.get("longitude", getattr(incident, "longitude", None))
        risk_band = attrs.get("risk_band", getattr(incident, "risk_band", None))
        office_notified = attrs.get("office_notified", getattr(incident, "office_notified", None))
        office_notification_mode = attrs.get(
            "office_notification_mode",
            getattr(incident, "office_notification_mode", None),
        )

        if risk_band:
            attrs["investigation_depth"] = derive_investigation_depth(risk_band)
            if not imo_classifier:
                attrs["imo_classifier"] = Incident.ImoClassifier.NOT_APPLICABLE
                imo_classifier = Incident.ImoClassifier.NOT_APPLICABLE
        if office_notified is True and not office_notification_mode:
            raise serializers.ValidationError({"office_notification_mode": "Select the mode of communication."})
        if office_notified is False:
            attrs["office_notification_mode"] = None
        validate_loss_type_selection(attrs, incident)

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
        if incident.office_notified is None:
            errors["office_notified"] = "Select whether office was notified."
        if incident.office_notified is True and not incident.office_notification_mode:
            errors["office_notification_mode"] = "Select the mode of communication."
        if not incident.imo_classifier:
            incident.imo_classifier = Incident.ImoClassifier.NOT_APPLICABLE
            incident.investigation_depth = derive_investigation_depth(incident.risk_band)
            incident.save(update_fields=["imo_classifier", "investigation_depth"])
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
