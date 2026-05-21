from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import Incident


HIGH_PRIORITY_KEYWORDS = (
    "collision",
    "electrical",
    "explosion",
    "fall",
    "fire",
    "flood",
    "grounding",
    "injury",
    "leak",
    "machinery",
    "oil",
    "pollution",
)


def build_near_miss_priority_hint(incident: Incident) -> dict[str, str]:
    repeated = _has_repeat_near_miss(incident)
    if repeated:
        return {
            "priority": "HIGH",
            "rationale": "A similar near miss already exists for this vessel, so SSOT repeat logic forces HIGH priority.",
        }

    if incident.loss_type_primary_id:
        return {
            "priority": "HIGH",
            "rationale": "Type-of-loss metadata indicates elevated harm potential and requires full investigation.",
        }

    if incident.incident_type_id:
        return {
            "priority": "HIGH",
            "rationale": "Incident-type metadata indicates a higher-risk near miss and suggests supersede-to-incident review.",
        }

    narrative = (incident.narrative or "").strip().lower()
    matched_keywords = [keyword for keyword in HIGH_PRIORITY_KEYWORDS if keyword in narrative]
    if matched_keywords:
        return {
            "priority": "HIGH",
            "rationale": "Narrative includes SHELL-style risk markers: " + ", ".join(sorted(set(matched_keywords))) + ".",
        }

    return {
        "priority": "LOW",
        "rationale": "No incident-type, loss-type, or narrative markers currently push this near miss above LOW triage.",
    }


def _has_repeat_near_miss(incident: Incident) -> bool:
    queryset = Incident.objects.filter(
        is_deleted=False,
        record_type=Incident.RecordType.NEAR_MISS,
        vessel_id=str(incident.vessel_id),
    ).exclude(pk=incident.pk)

    if incident.near_miss_mscat_subcode_id:
        if queryset.filter(near_miss_mscat_subcode_id=incident.near_miss_mscat_subcode_id).exists():
            return True
    if incident.incident_type_id and incident.loss_type_primary_id:
        if queryset.filter(
            incident_type_id=incident.incident_type_id,
            loss_type_primary_id=incident.loss_type_primary_id,
        ).exists():
            return True
    if incident.near_miss_shell_tag:
        return queryset.filter(near_miss_shell_tag=incident.near_miss_shell_tag).exists()
    return False


class NearMissTriageSerializer(serializers.Serializer):
    near_miss_priority = serializers.CharField()
    override_reason = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    supersede_to_incident = serializers.BooleanField(required=False, default=False)

    def validate_near_miss_priority(self, value: str) -> str:
        normalized = str(value).strip().upper()
        if normalized not in {"LOW", "HIGH"}:
            raise serializers.ValidationError(
                "Near-miss priority must be LOW or HIGH (D-GAP-R22)."
            )
        return normalized

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        suggestion = build_near_miss_priority_hint(incident)
        if suggestion["priority"] == "HIGH" and "repeat logic" in suggestion["rationale"] and attrs["near_miss_priority"] != "HIGH":
            raise serializers.ValidationError(
                {"near_miss_priority": "Repeated near misses must be triaged HIGH (D-GAP-R22)."}
            )

        if attrs["near_miss_priority"] != suggestion["priority"] and not attrs.get("override_reason"):
            raise serializers.ValidationError(
                {"override_reason": "Priority override requires a reason (D-GAP-R22)."}
            )

        if attrs.get("supersede_to_incident") and attrs["near_miss_priority"] != "HIGH":
            raise serializers.ValidationError(
                {"supersede_to_incident": "Only HIGH-priority near misses can be superseded into incidents."}
            )
        if attrs.get("supersede_to_incident") and not attrs.get("override_reason"):
            raise serializers.ValidationError(
                {"override_reason": "Supersede-to-incident requires a DPA reason for the audit trail."}
            )

        attrs["suggestion"] = suggestion
        return attrs
