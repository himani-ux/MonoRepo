from __future__ import annotations

import uuid

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import ChainOfCustody, EvidenceItem, Incident, IncidentEvidence, IncidentFact, WitnessInterview


def _uuid_or_none(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def resolve_source_evidence(incident: Incident, source_evidence_id: int | str):
    public_id = _uuid_or_none(source_evidence_id)
    if public_id is not None:
        lookups = (
            incident.evidence_items.filter(public_id=public_id).first(),
            incident.witness_interviews.filter(public_id=public_id).first(),
            incident.chain_of_custody_rows.filter(public_id=public_id).first(),
            incident.evidence_tabs.filter(public_id=public_id).first(),
        )
        for row in lookups:
            if row is not None:
                return row
        return None

    try:
        legacy_id = int(source_evidence_id)
    except (TypeError, ValueError):
        return None
    lookups = (
        incident.evidence_items.filter(pk=legacy_id).first(),
        incident.witness_interviews.filter(pk=legacy_id).first(),
        incident.chain_of_custody_rows.filter(pk=legacy_id).first(),
        incident.evidence_tabs.filter(pk=legacy_id).first(),
    )
    for row in lookups:
        if row is not None:
            return row
    return None


class IncidentFactSerializer(serializers.ModelSerializer):
    evidence_summary = serializers.SerializerMethodField()
    source_evidence_id = serializers.CharField()

    class Meta:
        model = IncidentFact
        fields = (
            "id",
            "public_id",
            "sequence_index",
            "fact_text",
            "fact_timestamp",
            "source_evidence_id",
            "evidence_summary",
            "confidence",
            "contradicts_fact",
            "hindsight_guard_triggered",
            "hindsight_override_reason",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = (
            "id",
            "public_id",
            "evidence_summary",
            "hindsight_guard_triggered",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        source_evidence_id = attrs.get("source_evidence_id")
        if source_evidence_id is None and self.instance is not None:
            source_evidence_id = self.instance.source_evidence_id
        source_evidence = resolve_source_evidence(incident, source_evidence_id)
        if source_evidence is None:
            raise serializers.ValidationError(
                {
                    "source_evidence_id": "Assumption bias guard: every fact requires a linked evidence reference."
                }
            )
        attrs["source_evidence_id"] = source_evidence.pk

        sequence_index = attrs.get("sequence_index")
        if sequence_index is not None:
            existing = incident.facts.filter(sequence_index=sequence_index)
            if self.instance is not None:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    {"sequence_index": "A fact with this sequence already exists. Use the next sequence number."}
                )

        contradicts_fact = attrs.get("contradicts_fact") or getattr(self.instance, "contradicts_fact", None)
        if contradicts_fact is not None:
            if self.instance is not None and contradicts_fact.pk == self.instance.pk:
                raise serializers.ValidationError({"contradicts_fact": "A fact cannot contradict itself."})
            if contradicts_fact.incident_id != incident.pk:
                raise serializers.ValidationError({"contradicts_fact": "Contradictions must stay within the same incident."})

        fact_timestamp = attrs.get("fact_timestamp")
        if fact_timestamp is None and self.instance is not None:
            fact_timestamp = self.instance.fact_timestamp
        if (
            fact_timestamp is not None
            and incident.occurred_at is not None
            and fact_timestamp > incident.occurred_at
            and not attrs.get("hindsight_override_reason")
            and not getattr(self.instance, "hindsight_override_reason", None)
        ):
            raise serializers.ValidationError(
                {
                    "hindsight_override_reason": "Hindsight bias guard: post-event facts require an override reason."
                }
            )
        attrs["hindsight_guard_triggered"] = bool(
            fact_timestamp is not None and incident.occurred_at is not None and fact_timestamp > incident.occurred_at
        )
        return attrs

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        actor_id: str = self.context["user_id"]
        sequence_index = validated_data.pop("sequence_index", None)
        if sequence_index is None:
            sequence_index = incident.facts.count() + 1
        return IncidentFact.objects.create(
            incident=incident,
            sequence_index=sequence_index,
            created_by=actor_id,
            updated_by=actor_id,
            updated_date=timezone.now(),
            schema_version=incident.schema_version or 1,
            **validated_data,
        )

    def update(self, instance, validated_data):
        actor_id: str = self.context["user_id"]
        for field_name, value in validated_data.items():
            setattr(instance, field_name, value)
        instance.updated_by = actor_id
        instance.updated_date = timezone.now()
        instance.save()
        return instance

    def get_evidence_summary(self, instance: IncidentFact) -> str:
        evidence = resolve_source_evidence(instance.incident, instance.source_evidence_id)
        if evidence is None:
            return "Unknown evidence"
        if isinstance(evidence, WitnessInterview):
            return f"Interview: {evidence.witness_name}"
        if isinstance(evidence, ChainOfCustody):
            return f"Physical: {evidence.description[:60]}"
        if isinstance(evidence, IncidentEvidence):
            return f"{evidence.tab_code}: {evidence.summary[:80] or 'Evidence tab'}"
        if isinstance(evidence, EvidenceItem):
            return evidence.title
        return str(evidence.pk)


class IncidentFactReorderSerializer(serializers.Serializer):
    ordered_fact_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

    def validate_ordered_fact_ids(self, value):
        incident: Incident = self.context["incident"]
        existing_ids = list(incident.facts.order_by("sequence_index", "id").values_list("id", flat=True))
        if sorted(existing_ids) != sorted(value):
            raise serializers.ValidationError("Reorder payload must include every fact exactly once.")
        return value


class IncidentFactContradictionSerializer(serializers.Serializer):
    fact_id = serializers.IntegerField(min_value=1)
    contradicts_fact_id = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if attrs["fact_id"] == attrs["contradicts_fact_id"]:
            raise serializers.ValidationError({"contradicts_fact_id": "A fact cannot contradict itself."})
        incident: Incident = self.context["incident"]
        fact_ids = set(incident.facts.values_list("id", flat=True))
        for field_name in ("fact_id", "contradicts_fact_id"):
            if attrs[field_name] not in fact_ids:
                raise serializers.ValidationError({field_name: "Fact does not belong to this incident."})
        return attrs


class IncidentLinkActionSerializer(serializers.Serializer):
    class LinkType(serializers.ChoiceField):
        pass

    target_incident_id = serializers.IntegerField(required=False, min_value=1)
    link_type = serializers.ChoiceField(choices=("RELATED", "SUPERSEDE"))

    def validate(self, attrs):
        link_type = attrs["link_type"]
        target_incident_id = attrs.get("target_incident_id")
        if link_type == "RELATED" and target_incident_id is None:
            raise serializers.ValidationError({"target_incident_id": "Related-link actions require a target incident."})
        if link_type == "SUPERSEDE" and target_incident_id is not None:
            raise serializers.ValidationError({"target_incident_id": "Supersede creates a new incident and takes no target."})
        return attrs
