from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import (
    ExternalPartyInjury,
    Incident,
    IncidentLossEvaluation,
    InjuryDropdownOption,
    Recommendation,
    RecommendationVerification,
)
from apps.safety.services.field_history_recorder import resolve_actor_id


def _choice_options(choices) -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in choices]


def _has_injury_record(incident: Incident) -> bool:
    try:
        return bool(incident.external_party_injury)
    except ExternalPartyInjury.DoesNotExist:
        return False
    except AttributeError:
        return False


def _default_report_type(incident: Incident) -> str:
    if _has_injury_record(incident):
        return IncidentLossEvaluation.ReportType.INJURY
    return IncidentLossEvaluation.ReportType.INCIDENT


def _resolved_report_type(incident: Incident, loss_evaluation: IncidentLossEvaluation | None) -> str:
    if loss_evaluation is not None and loss_evaluation.report_type:
        return loss_evaluation.report_type
    return _default_report_type(incident)


class RecommendationVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationVerification
        fields = (
            "id",
            "recommendation_id",
            "is_effective",
            "residual_risk",
            "verified_at",
            "verified_by",
            "notes",
        )


class IncidentPhase8VerifySerializer(serializers.Serializer):
    recommendation_id = serializers.UUIDField()
    is_effective = serializers.BooleanField()
    residual_risk = serializers.CharField(max_length=32)
    notes = serializers.CharField(allow_blank=False)

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        try:
            recommendation = incident.recommendations.get(pk=attrs["recommendation_id"], is_deleted=False)
        except Recommendation.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"recommendation_id": "Recommendation must belong to the incident being verified."}
            ) from exc
        attrs["recommendation"] = recommendation
        return attrs


class IncidentPhase8CloseSerializer(serializers.Serializer):
    closure_reason = serializers.CharField(allow_blank=False)


class IncidentLossEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentLossEvaluation
        fields = (
            "id",
            "report_type",
            "consequence",
            "likelihood",
            "risk_level",
            "name_of_master",
            "name_of_chief_engineer",
            "repair_type",
            "repair_details",
            "last_overhaul_maintenance_survey_details",
            "safe_working_practice",
            "man_hours_worked",
            "hours_worked_previous_day",
            "hours_rest_last_96_hours",
            "delay_to_vessel",
            "delay_reason",
            "repair_man_hours_lost",
            "materials_used_repairs_onboard",
            "materials_specify_details",
            "materials_reason",
            "deviation",
            "off_hire",
            "injury_man_hours_lost",
            "injury_reasons",
            "repatriation",
            "hospitalization",
            "evacuation",
            "estimated_cost_off_hire",
            "estimated_cost_delay",
            "estimated_cost_man_hours",
            "estimated_cost_deviation",
            "estimated_cost_materials",
            "estimated_cost_miscellaneous",
            "total_estimated_cost",
            "miscellaneous_expenses_reason",
            "cost_medicines_onboard",
            "cost_doctor_visits",
            "cost_repatriation",
            "cost_evacuation",
            "cost_injury_delay",
            "cost_injury_man_hours",
            "cost_injury_deviation",
            "cost_injury_miscellaneous",
            "injury_total_estimated_cost",
            "injury_miscellaneous_expenses_reason",
            "updated_date",
        )
        read_only_fields = ("id", "updated_date")

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = {key: (None if value == "" else value) for key, value in data.items()}
        return super().to_internal_value(data)

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        user = self.context.get("user")
        actor_id = resolve_actor_id(user)
        validated_data.setdefault("report_type", _default_report_type(incident))
        return IncidentLossEvaluation.objects.create(
            incident=incident,
            created_by=actor_id,
            updated_by=actor_id,
            updated_date=timezone.now(),
            schema_version=incident.schema_version or 1,
            **validated_data,
        )

    def update(self, instance, validated_data):
        user = self.context.get("user")
        for field_name, value in validated_data.items():
            setattr(instance, field_name, value)
        instance.updated_by = resolve_actor_id(user)
        instance.updated_date = timezone.now()
        instance.save()
        return instance


def empty_loss_evaluation_payload() -> dict[str, object]:
    fields = IncidentLossEvaluationSerializer.Meta.fields
    return {field_name: None for field_name in fields}


def build_phase8_workspace_payload(incident: Incident) -> dict[str, object]:
    try:
        loss_evaluation = incident.loss_evaluation
    except IncidentLossEvaluation.DoesNotExist:
        loss_evaluation = None
    except AttributeError:
        loss_evaluation = None

    safe_working_practice_options = [
        {"id": str(option.pk), "label": option.option_label, "value": option.option_label}
        for option in InjuryDropdownOption.objects.filter(
            active=True,
            field_key=InjuryDropdownOption.FieldKey.SAFE_WORKING_PRACTICE,
        ).order_by("display_order", "option_label")
    ]

    return {
        "incident_id": incident.pk,
        "current_phase": incident.current_phase,
        "state": incident.state,
        "risk_band": incident.risk_band,
        "required_process_id": "SAF_P_004",
        "phase_title": "Loss Evaluation",
        "report_type": _resolved_report_type(incident, loss_evaluation),
        "has_loss_evaluation": loss_evaluation is not None,
        "loss_evaluation": (
            IncidentLossEvaluationSerializer(loss_evaluation).data
            if loss_evaluation is not None
            else empty_loss_evaluation_payload()
        ),
        "choices": {
            "consequence": _choice_options(IncidentLossEvaluation.Consequence.choices),
            "likelihood": _choice_options(IncidentLossEvaluation.Likelihood.choices),
            "risk_level": _choice_options(IncidentLossEvaluation.RiskLevel.choices),
            "repair_type": _choice_options(IncidentLossEvaluation.RepairType.choices),
            "report_type": _choice_options(IncidentLossEvaluation.ReportType.choices),
            "yes_no": [
                {"value": True, "label": "Yes"},
                {"value": False, "label": "No"},
            ],
            "safe_working_practice": safe_working_practice_options,
        },
        "ready_for_close": loss_evaluation is not None,
        "blockers": [] if loss_evaluation is not None else ["loss_evaluation_not_saved"],
        "blocker_details": []
        if loss_evaluation is not None
        else [
            {
                "code": "loss_evaluation_not_saved",
                "message": "Save Loss Evaluation before closing the incident.",
            }
        ],
    }
