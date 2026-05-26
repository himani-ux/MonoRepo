from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.authentication.vessel_scope import _resolve_vessel_scope_ids
from apps.safety.models import Incident
from apps.safety.serializers.incident_external_party import ExternalPartyInjurySerializer
from apps.safety.serializers.vessel_display import resolve_vessel_display
from apps.safety.services.self_report_guard import check_self_report_conflict


PHASE_1_NARRATIVE_MIN_LENGTH = 200


class IncidentPhase1Serializer(serializers.ModelSerializer):
    draft_reference = serializers.SerializerMethodField(read_only=True)
    external_party_injury = ExternalPartyInjurySerializer(read_only=True)
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
            "incident_type_id",
            "loss_type_primary_id",
            "occurred_at",
            "reported_at",
            "latitude",
            "longitude",
            "position_source",
            "position_daily_report_id",
            "narrative",
            "awaiting_daily_report_match",
            "first_hour_checklist_done",
            "external_party_injury",
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
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        repository = self.context["incident_repository"]
        return repository.create(validated_data)

    def update(self, instance, validated_data):
        repository = self.context["incident_repository"]
        validated_data.pop("vessel_code", None)
        return repository.update(instance.pk, validated_data)


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

        if not incident.first_hour_checklist_done:
            errors["first_hour_checklist_done"] = (
                "Complete the first-hour scene-protection checklist before submitting Phase 1."
            )

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
