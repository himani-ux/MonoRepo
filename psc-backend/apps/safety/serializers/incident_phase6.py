from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import (
    CorrectiveAction,
    Incident,
    IncidentBiasGuardResponse,
    MasterSafetyBiasGuard,
    Recommendation,
)
from apps.safety.services.alarp_gate import AlarpGate, RECOMMENDATION_THEMES
from apps.safety.services.blame_detector import BlameDetector


def _resolve_actor_id_from_context(context) -> str:
    return context.get("user_id", "system")


def _sync_linked_corrective_action_ids(recommendation: Recommendation) -> None:
    linked_ids = list(
        recommendation.corrective_actions.filter(is_deleted=False).order_by("id").values_list("id", flat=True)
    )
    csv_value = ",".join(str(value) for value in linked_ids)
    if recommendation.linked_ca_ids != csv_value:
        recommendation.linked_ca_ids = csv_value
        recommendation.save(update_fields=["linked_ca_ids"])


def _model_max_length(model: type, field_name: str) -> int:
    max_length = model._meta.get_field(field_name).max_length
    if not max_length:
        raise ValueError(f"{model.__name__}.{field_name} does not define max_length.")
    return int(max_length)


CORRECTIVE_ACTION_ACTOR_ID_MAX_LENGTH = _model_max_length(CorrectiveAction, "verifier_user_id")


def sync_incident_alarp_attestation(incident: Incident) -> bool:
    gate = AlarpGate()
    recommendations = list(incident.recommendations.filter(is_deleted=False).order_by("id"))
    alarp_complete = gate.incident_attestation_complete(incident, recommendations)
    if incident.alarp_attested != alarp_complete:
        incident.alarp_attested = alarp_complete
        incident.save(update_fields=["alarp_attested"])
    return alarp_complete


def _bias_guards_complete(incident: Incident) -> bool:
    bitmask = (incident.bias_guard_attestations or "").strip()
    active_guards = list(MasterSafetyBiasGuard.objects.filter(active=True).order_by("bit_position"))
    if active_guards and len(bitmask) >= len(active_guards) and set(bitmask[: len(active_guards)]) == {"1"}:
        return True
    if not active_guards:
        return False
    acknowledged = IncidentBiasGuardResponse.objects.filter(
        incident=incident,
        guard_code__in=[guard.guard_code for guard in active_guards],
        acknowledged=True,
    ).count()
    return acknowledged == len(active_guards)


class CorrectiveActionWriteSerializer(serializers.Serializer):
    assigned_crew_id = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=CORRECTIVE_ACTION_ACTOR_ID_MAX_LENGTH,
    )
    assigned_office_user_id = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=CORRECTIVE_ACTION_ACTOR_ID_MAX_LENGTH,
    )
    verifier_user_id = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=CORRECTIVE_ACTION_ACTOR_ID_MAX_LENGTH,
    )
    due_date = serializers.DateField(required=False, allow_null=True)


class CorrectiveActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrectiveAction
        fields = (
            "id",
            "id",
            "title",
            "description",
            "assigned_crew_id",
            "assigned_office_user_id",
            "verifier_user_id",
            "due_date",
            "status",
            "purchase_req_id",
        )
        read_only_fields = fields


class RecommendationSerializer(serializers.ModelSerializer):
    corrective_action = CorrectiveActionWriteSerializer(write_only=True, required=False)
    corrective_actions = CorrectiveActionSerializer(many=True, read_only=True)

    class Meta:
        model = Recommendation
        fields = (
            "id",
            "id",
            "tier",
            "theme_code",
            "title",
            "description",
            "rationale",
            "estimated_effort",
            "estimated_likelihood_reduction",
            "residual_risk_statement",
            "alarp_attested",
            "tolerable_failure_filter",
            "linked_ca_ids",
            "corrective_action",
            "corrective_actions",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = (
            "id",
            "id",
            "linked_ca_ids",
            "corrective_actions",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        gate = AlarpGate()
        tier = attrs.get("tier") or getattr(self.instance, "tier", None)
        theme_code = attrs.get("theme_code", getattr(self.instance, "theme_code", None))
        tolerable_failure = attrs.get(
            "tolerable_failure_filter",
            getattr(self.instance, "tolerable_failure_filter", False),
        )
        errors: dict[str, object] = {}

        if tolerable_failure and incident.risk_band != Incident.RiskBand.GREEN:
            errors["tolerable_failure_filter"] = (
                "Tolerable-failure flag is restricted to GREEN-band incidents."
            )

        merged_values = self._instance_defaults()
        merged_values.update(attrs)

        if tier == Recommendation.Tier.PREVENTIVE:
            if theme_code not in (None, "") and theme_code not in gate.theme_codes:
                errors["theme_code"] = "Unknown recommendation theme."

            likelihood = merged_values.get("estimated_likelihood_reduction")
            if likelihood not in (None, "") and likelihood not in gate.likelihood_codes:
                errors["estimated_likelihood_reduction"] = "Unknown likelihood-reduction code."
        else:
            if attrs.get("theme_code") not in (None, ""):
                errors["theme_code"] = "Only preventive recommendations may carry a system-action theme."

        corrective_action = attrs.get("corrective_action")
        if tier not in {Recommendation.Tier.CORRECTIVE, Recommendation.Tier.PREVENTIVE} and corrective_action is not None:
            errors["corrective_action"] = (
                "Action linkage is only valid for corrective or preventive recommendations."
            )

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        corrective_action_data = validated_data.pop("corrective_action", None)
        actor_id = _resolve_actor_id_from_context(self.context)
        recommendation = Recommendation.objects.create(
            incident=incident,
            created_by=actor_id,
            updated_by=actor_id,
            updated_date=timezone.now(),
            schema_version=incident.schema_version or 1,
            **validated_data,
        )
        if recommendation.tier in {Recommendation.Tier.CORRECTIVE, Recommendation.Tier.PREVENTIVE} and corrective_action_data is not None:
            self._upsert_corrective_action(recommendation, corrective_action_data, actor_id)
        sync_incident_alarp_attestation(incident)
        return recommendation

    def update(self, instance, validated_data):
        corrective_action_data = validated_data.pop("corrective_action", None)
        actor_id = _resolve_actor_id_from_context(self.context)
        for field_name, value in validated_data.items():
            setattr(instance, field_name, value)
        instance.updated_by = actor_id
        instance.updated_date = timezone.now()
        instance.save()
        if instance.tier in {Recommendation.Tier.CORRECTIVE, Recommendation.Tier.PREVENTIVE} and corrective_action_data is not None:
            self._upsert_corrective_action(instance, corrective_action_data, actor_id)
        sync_incident_alarp_attestation(instance.incident)
        return instance

    def _upsert_corrective_action(
        self,
        recommendation: Recommendation,
        corrective_action_data: dict[str, object],
        actor_id: str,
    ) -> CorrectiveAction:
        action = recommendation.corrective_actions.filter(is_deleted=False).order_by("id").first()
        now = timezone.now()
        payload = {
            "source_table": "vims_safety_incident",
            "source_id": recommendation.incident_id,
            "title": recommendation.title,
            "description": recommendation.description,
            "assigned_crew_id": corrective_action_data.get("assigned_crew_id"),
            "assigned_office_user_id": corrective_action_data.get("assigned_office_user_id"),
            "verifier_user_id": corrective_action_data["verifier_user_id"],
            "due_date": corrective_action_data.get("due_date"),
            "status": CorrectiveAction.Status.OPEN,
            "schema_version": recommendation.schema_version or 1,
            "updated_by": actor_id,
            "updated_date": now,
        }
        if action is None:
            action = CorrectiveAction.objects.create(
                recommendation=recommendation,
                created_by=actor_id,
                **payload,
            )
        else:
            for field_name, value in payload.items():
                setattr(action, field_name, value)
            action.save()
        _sync_linked_corrective_action_ids(recommendation)
        return action

    def _instance_defaults(self) -> dict[str, object]:
        if self.instance is None:
            return {}
        return {
            "estimated_effort": self.instance.estimated_effort,
            "estimated_likelihood_reduction": self.instance.estimated_likelihood_reduction,
            "residual_risk_statement": self.instance.residual_risk_statement,
        }


def build_phase6_workspace_payload(incident: Incident) -> dict[str, object]:
    recommendations = incident.recommendations.filter(is_deleted=False).order_by("id")
    serialized = RecommendationSerializer(recommendations, many=True).data
    grouped = {
        Recommendation.Tier.LESSONS_LEARNT: [],
        Recommendation.Tier.CORRECTIVE: [],
        Recommendation.Tier.PREVENTIVE: [],
    }
    for row in serialized:
        grouped[row["tier"]].append(row)

    tier_counts = {tier: len(rows) for tier, rows in grouped.items()}
    gate = AlarpGate()
    recommendation_rows = list(recommendations)
    alarp_complete = gate.incident_attestation_complete(incident, recommendation_rows)
    missing_tiers: list[str] = []
    gate_blockers: list[str] = []
    if not recommendation_rows:
        gate_blockers.append("recommendations")

    bias_guards_complete = True

    blame_evaluation = BlameDetector().evaluate_incident(incident)

    return {
        "incident_id": incident.pk,
        "threshold_hint": gate.resolve_threshold(),
        "themes": list(RECOMMENDATION_THEMES),
        "tier_counts": tier_counts,
        "missing_tiers": missing_tiers,
        "alarp_complete": alarp_complete,
        "bias_guards_complete": bias_guards_complete,
        "blame_evaluation": {
            "blocked": False,
            "trigger_terms": list(blame_evaluation.trigger_terms),
            "all_root_personal_factors": blame_evaluation.all_root_personal_factors,
            "has_lack_of_control": blame_evaluation.has_lack_of_control,
            "override_by": incident.blame_fixation_override_by,
        },
        "gate_blockers": sorted(set(gate_blockers)),
        "tolerable_failure_allowed": incident.risk_band == Incident.RiskBand.GREEN,
        "recommendations": grouped,
        "corrective_actions": CorrectiveActionSerializer(
            CorrectiveAction.objects.filter(
                recommendation__incident=incident,
                is_deleted=False,
            ).order_by("id"),
            many=True,
        ).data,
    }
