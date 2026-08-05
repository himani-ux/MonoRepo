from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import (
    EvidenceItem,
    Incident,
    IncidentBiasGuardResponse,
    IncidentBlameOverride,
    IncidentCauseTag,
    IncidentFact,
    IncidentPhase5Assessment,
    IncidentSafeguardFailure,
    MasterMscatTaxonomy,
    MasterSafetyBiasGuard,
    NearMissCauseOption,
)
from apps.safety.services import BlameDetector
from apps.safety.serializers.incident_phase4 import IncidentFactSerializer

OTHER_ROOT_CAUSE_SUBCODE = "OTHER"
MAX_ROOT_CAUSES = 3


def _resolve_actor_id_from_context(context) -> str:
    return context.get("user_id", "system")


def _sync_bias_guard_attestations(incident: Incident) -> None:
    active_guards = list(MasterSafetyBiasGuard.objects.filter(active=True).order_by("bit_position"))
    response_map = {
        row.guard_code: row
        for row in incident.bias_guard_responses.filter(guard_code__in=[guard.guard_code for guard in active_guards])
    }
    bits: list[str] = []
    for guard in active_guards:
        response = response_map.get(guard.guard_code)
        bits.append("1" if response and response.acknowledged else "0")
    incident.bias_guard_attestations = "".join(bits)
    incident.save(update_fields=["bias_guard_attestations"])


class IncidentCauseTagSerializer(serializers.ModelSerializer):
    source_fact_id = serializers.PrimaryKeyRelatedField(
        source="source_fact",
        queryset=IncidentFact.objects.all(),
    )
    mscat_subcode_id = serializers.CharField(required=False, allow_blank=True)
    mscat_description = serializers.SerializerMethodField()
    mscat_category_id = serializers.SerializerMethodField()
    cause_factor_label = serializers.SerializerMethodField()
    cause_stage = serializers.SerializerMethodField()

    class Meta:
        model = IncidentCauseTag
        fields = (
            "id",
            "source_fact_id",
            "mscat_subcode_id",
            "mscat_category_id",
            "mscat_description",
            "cause_factor",
            "cause_factor_label",
            "cause_option_id",
            "cause_option_text",
            "cause_other_text",
            "cause_stage",
            "causal_layer",
            "analysis_tool",
            "rationale",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = (
            "id",
            "mscat_category_id",
            "mscat_description",
            "cause_factor_label",
            "cause_option_text",
            "cause_stage",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        source_fact = attrs.get("source_fact") or getattr(self.instance, "source_fact", None)
        if source_fact is None:
            raise serializers.ValidationError({"source_fact_id": "Select the evidence note for this cause."})
        if source_fact.incident_id != incident.pk:
            raise serializers.ValidationError({"source_fact": "Cause tags must reference a fact on the same incident."})
        causal_layer = attrs.get("causal_layer") or getattr(self.instance, "causal_layer", None)
        if causal_layer == IncidentCauseTag.CausalLayer.INTERMEDIATE:
            raise serializers.ValidationError({"causal_layer": "Use Immediate Cause or Root Cause."})
        mscat_subcode_id = str(attrs.get("mscat_subcode_id") or getattr(self.instance, "mscat_subcode_id", OTHER_ROOT_CAUSE_SUBCODE)).strip()
        cause_option_id = attrs.get("cause_option_id", getattr(self.instance, "cause_option_id", None))
        cause_stage = self._cause_stage_for_layer(causal_layer)
        if cause_option_id:
            option = NearMissCauseOption.objects.filter(id=cause_option_id, active=True).first()
            if option is None:
                raise serializers.ValidationError({"cause_option_id": "Select a valid cause factor option."})
            if cause_stage and option.cause_stage != cause_stage:
                raise serializers.ValidationError({"cause_option_id": "Cause option does not match the selected cause type."})
            attrs["cause_factor"] = option.factor
            attrs["cause_option_text"] = option.option_text
            attrs["mscat_subcode_id"] = OTHER_ROOT_CAUSE_SUBCODE
            cause_other_text = str(attrs.get("cause_other_text", getattr(self.instance, "cause_other_text", "")) or "").strip()
            if option.option_text.strip().lower() == "other" and not cause_other_text:
                raise serializers.ValidationError({"cause_other_text": "Specify the other cause."})
            if option.option_text.strip().lower() != "other":
                attrs["cause_other_text"] = ""
        elif mscat_subcode_id != OTHER_ROOT_CAUSE_SUBCODE and not MasterMscatTaxonomy.objects.filter(subcode_id=mscat_subcode_id, active=True).exists():
            raise serializers.ValidationError({"mscat_subcode_id": "Unknown M-SCAT subcode."})
        rationale = str(attrs.get("rationale", getattr(self.instance, "rationale", "")) or "").strip()
        if not rationale:
            raise serializers.ValidationError({"rationale": "Every cause code requires a free-text rationale."})
        if causal_layer == IncidentCauseTag.CausalLayer.ROOT:
            existing_roots = incident.cause_tags.filter(causal_layer=IncidentCauseTag.CausalLayer.ROOT)
            if self.instance is not None:
                existing_roots = existing_roots.exclude(pk=self.instance.pk)
            if existing_roots.count() >= MAX_ROOT_CAUSES:
                raise serializers.ValidationError({"causal_layer": "Maximum three root causes are allowed."})
        return attrs

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        actor_id = _resolve_actor_id_from_context(self.context)
        return IncidentCauseTag.objects.create(
            incident=incident,
            created_by=actor_id,
            updated_by=actor_id,
            updated_date=timezone.now(),
            schema_version=incident.schema_version or 1,
            **validated_data,
        )

    def update(self, instance, validated_data):
        actor_id = _resolve_actor_id_from_context(self.context)
        for field_name, value in validated_data.items():
            setattr(instance, field_name, value)
        instance.updated_by = actor_id
        instance.updated_date = timezone.now()
        instance.save()
        return instance

    def get_mscat_description(self, instance: IncidentCauseTag) -> str:
        if instance.mscat_subcode_id == OTHER_ROOT_CAUSE_SUBCODE:
            return "Other"
        row = MasterMscatTaxonomy.objects.filter(subcode_id=instance.mscat_subcode_id).first()
        return row.subcode_description if row is not None else ""

    def get_mscat_category_id(self, instance: IncidentCauseTag) -> int | None:
        if instance.mscat_subcode_id == OTHER_ROOT_CAUSE_SUBCODE:
            return None
        row = MasterMscatTaxonomy.objects.filter(subcode_id=instance.mscat_subcode_id).first()
        return row.category_id if row is not None else None

    def get_cause_factor_label(self, instance: IncidentCauseTag) -> str:
        labels = dict(NearMissCauseOption.Factor.choices)
        return labels.get(instance.cause_factor or "", "")

    def get_cause_stage(self, instance: IncidentCauseTag) -> str:
        return self._cause_stage_for_layer(instance.causal_layer) or ""

    @staticmethod
    def _cause_stage_for_layer(causal_layer: str | None) -> str | None:
        if causal_layer == IncidentCauseTag.CausalLayer.IMMEDIATE:
            return NearMissCauseOption.CauseStage.IMMEDIATE
        if causal_layer == IncidentCauseTag.CausalLayer.ROOT:
            return NearMissCauseOption.CauseStage.ROOT
        return None


class IncidentPhase5AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentPhase5Assessment
        fields = (
            "people_contribution_text",
            "process_gap_text",
            "plant_failure_text",
            "analysis_tools_used",
            "human_factors_payload",
            "confirmation_override_reason",
            "monocausal_justification",
        )

    def validate_analysis_tools_used(self, value):
        allowed = {choice for choice, _ in IncidentPhase5Assessment.AnalysisTool.choices}
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Analysis tools must not repeat.")
        invalid = [tool for tool in value if tool not in allowed]
        if invalid:
            raise serializers.ValidationError(f"Unknown analysis tool(s): {', '.join(sorted(invalid))}.")
        return value

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        actor_id = _resolve_actor_id_from_context(self.context)
        return IncidentPhase5Assessment.objects.create(
            incident=incident,
            created_by=actor_id,
            updated_by=actor_id,
            updated_date=timezone.now(),
            schema_version=incident.schema_version or 1,
            **validated_data,
        )

    def update(self, instance, validated_data):
        actor_id = _resolve_actor_id_from_context(self.context)
        for field_name, value in validated_data.items():
            setattr(instance, field_name, value)
        instance.updated_by = actor_id
        instance.updated_date = timezone.now()
        instance.save()
        return instance


class IncidentSafeguardFailureSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentSafeguardFailure
        fields = (
            "id",
            "id",
            "safeguard_name",
            "design_mscat_subcode_id",
            "installation_mscat_subcode_id",
            "maintenance_mscat_subcode_id",
            "operation_mscat_subcode_id",
            "testing_mscat_subcode_id",
            "override_mscat_subcode_id",
            "notes",
        )
        read_only_fields = ("id", "id")

    def validate(self, attrs):
        subcode_fields = (
            "design_mscat_subcode_id",
            "installation_mscat_subcode_id",
            "maintenance_mscat_subcode_id",
            "operation_mscat_subcode_id",
            "testing_mscat_subcode_id",
            "override_mscat_subcode_id",
        )
        for field_name in subcode_fields:
            subcode = attrs.get(field_name) or getattr(self.instance, field_name, None)
            if not subcode:
                raise serializers.ValidationError({field_name: "All six safeguard dimensions require an M-SCAT code."})
            if not MasterMscatTaxonomy.objects.filter(subcode_id=subcode, active=True).exists():
                raise serializers.ValidationError({field_name: "Unknown M-SCAT subcode."})
        return attrs

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        actor_id = _resolve_actor_id_from_context(self.context)
        return IncidentSafeguardFailure.objects.create(
            incident=incident,
            created_by=actor_id,
            updated_by=actor_id,
            updated_date=timezone.now(),
            schema_version=incident.schema_version or 1,
            **validated_data,
        )

    def update(self, instance, validated_data):
        actor_id = _resolve_actor_id_from_context(self.context)
        for field_name, value in validated_data.items():
            setattr(instance, field_name, value)
        instance.updated_by = actor_id
        instance.updated_date = timezone.now()
        instance.save()
        return instance


class IncidentBiasGuardResponseSerializer(serializers.ModelSerializer):
    guard_name = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()

    class Meta:
        model = IncidentBiasGuardResponse
        fields = (
            "guard_code",
            "guard_name",
            "family",
            "acknowledged",
            "evaluation_state",
            "justification",
            "acknowledged_by",
            "acknowledged_at",
        )
        read_only_fields = ("guard_name", "family", "acknowledged_by", "acknowledged_at")

    def validate_guard_code(self, value):
        if not MasterSafetyBiasGuard.objects.filter(guard_code=value, active=True).exists():
            raise serializers.ValidationError("Unknown bias guard.")
        return value

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        actor_id = _resolve_actor_id_from_context(self.context)
        instance, _ = IncidentBiasGuardResponse.objects.update_or_create(
            incident=incident,
            guard_code=validated_data["guard_code"],
            defaults={
                **validated_data,
                "acknowledged_by": actor_id if validated_data.get("acknowledged") else None,
                "acknowledged_at": timezone.now() if validated_data.get("acknowledged") else None,
                "updated_by": actor_id,
                "updated_date": timezone.now(),
                "created_by": actor_id,
                "schema_version": incident.schema_version or 1,
            },
        )
        _sync_bias_guard_attestations(incident)
        return instance

    def update(self, instance, validated_data):
        actor_id = _resolve_actor_id_from_context(self.context)
        for field_name, value in validated_data.items():
            setattr(instance, field_name, value)
        if instance.acknowledged:
            instance.acknowledged_by = actor_id
            instance.acknowledged_at = timezone.now()
        instance.updated_by = actor_id
        instance.updated_date = timezone.now()
        instance.save()
        _sync_bias_guard_attestations(instance.incident)
        return instance

    def get_guard_name(self, instance: IncidentBiasGuardResponse) -> str:
        guard = MasterSafetyBiasGuard.objects.filter(guard_code=instance.guard_code).first()
        return guard.guard_name if guard is not None else instance.guard_code

    def get_family(self, instance: IncidentBiasGuardResponse) -> str | None:
        guard = MasterSafetyBiasGuard.objects.filter(guard_code=instance.guard_code).first()
        return guard.family if guard is not None else None


class IncidentBlameOverrideSerializer(serializers.ModelSerializer):
    justification = serializers.CharField(min_length=200)

    class Meta:
        model = IncidentBlameOverride
        fields = ("justification",)

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        actor_id = _resolve_actor_id_from_context(self.context)
        actor_role = self.context.get("user_role", "")
        instance, _ = IncidentBlameOverride.objects.update_or_create(
            incident=incident,
            defaults={
                "justification": validated_data["justification"],
                "approved_by": actor_id,
                "approved_role": actor_role,
                "approved_at": timezone.now(),
                "created_by": actor_id,
                "updated_by": actor_id,
                "updated_date": timezone.now(),
                "schema_version": incident.schema_version or 1,
            },
        )
        incident.blame_fixation_override_by = actor_id
        incident.save(update_fields=["blame_fixation_override_by"])
        return instance


def build_phase5_workspace_payload(incident: Incident) -> dict[str, object]:
    try:
        assessment = incident.phase5_assessment
        assessment_payload = IncidentPhase5AssessmentSerializer(assessment).data
    except IncidentPhase5Assessment.DoesNotExist:
        assessment_payload = None

    bias_guards = []
    minimum_tools_required = 2
    if incident.risk_band == Incident.RiskBand.RED:
        minimum_tools_required = 5
    elif incident.investigation_depth == Incident.InvestigationDepth.DEEP:
        minimum_tools_required = 5
    elif incident.investigation_depth == Incident.InvestigationDepth.MEDIUM:
        minimum_tools_required = 3

    return {
        "incident_id": incident.pk,
        "investigation_depth": incident.investigation_depth,
        "minimum_tools_required": minimum_tools_required,
        "assessment": assessment_payload,
        "causes": IncidentCauseTagSerializer(incident.cause_tags.order_by("id"), many=True).data,
        "safeguards": IncidentSafeguardFailureSerializer(incident.safeguard_failures.order_by("id"), many=True).data,
        "bias_guards": bias_guards,
        "blame_evaluation": {
            "blocked": False,
            "trigger_terms": [],
            "all_root_personal_factors": False,
            "has_lack_of_control": True,
            "override_by": incident.blame_fixation_override_by,
        },
        "analysis_tools_used": assessment_payload["analysis_tools_used"] if assessment_payload else [],
        "matrix_rows": [
            {
                "id": row.id,
                "finding": row.finding,
                "pro_evidence": row.pro_evidence,
                "con_evidence": row.con_evidence,
                "major_finding": bool((row.metadata_json or {}).get("major_finding")),
            }
            for row in incident.evidence_items.filter(item_type=EvidenceItem.ItemType.MATRIX).order_by("id")
        ],
        "facts": IncidentFactSerializer(
            incident.facts.order_by("sequence_index", "id"),
            many=True,
            context={"incident": incident, "user_id": "system"},
        ).data,
    }
