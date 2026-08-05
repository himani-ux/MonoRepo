from __future__ import annotations

from datetime import timedelta
import json

from rest_framework import serializers

from apps.safety.models import Incident, MasterMscatTaxonomy
from apps.safety.serializers.near_miss import NEAR_MISS_OTHER_CATEGORY, NEAR_MISS_OTHER_PREFIX, resolve_near_miss_category


def build_near_miss_priority_hint(incident: Incident) -> dict[str, object]:
    if str(incident.near_miss_severity or "").strip().upper() == "HIGH":
        return {
            "priority": "HIGH",
            "forced": False,
            "reason_type": "reporter_high",
            "rationale": "Reporter selected HIGH severity, so this should be reviewed as HIGH unless there is a recorded override reason.",
            "user_message": "The reporter marked this near miss as high severity.",
        }

    return {
        "priority": "LOW",
        "forced": False,
        "reason_type": "low",
        "rationale": "No priority was selected yet. Office reviewer may choose LOW, MEDIUM, or HIGH.",
        "user_message": "Select the priority based on office review.",
    }


class NearMissTriageSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("ACCEPT", "SEND_BACK", "REJECT"), required=False, default="ACCEPT")
    near_miss_priority = serializers.CharField(required=False)
    near_miss_shell_tag = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    near_miss_mscat_subcode_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    office_comment = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    override_reason = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    priority_change_reason = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    category_tag_change_reason = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    reason = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    supersede_to_incident = serializers.BooleanField(required=False, default=False)

    def validate_near_miss_priority(self, value: str) -> str:
        normalized = str(value).strip().upper()
        if normalized not in {"LOW", "MEDIUM", "HIGH"}:
            raise serializers.ValidationError(
                "Near-miss priority must be LOW, MEDIUM, or HIGH."
            )
        return normalized

    def validate(self, attrs):
        action = str(attrs.get("action") or "ACCEPT").strip().upper()
        attrs["action"] = action
        comment = (
            str(attrs.get("office_comment") or "").strip()
            or str(attrs.get("override_reason") or "").strip()
            or str(attrs.get("reason") or "").strip()
        )
        priority_change_reason = str(attrs.get("priority_change_reason") or "").strip()
        category_tag_change_reason = str(attrs.get("category_tag_change_reason") or "").strip()
        attrs["office_comment"] = comment
        attrs["priority_change_reason"] = priority_change_reason
        attrs["category_tag_change_reason"] = category_tag_change_reason

        if action in {"SEND_BACK", "REJECT"}:
            if not comment:
                message = (
                    "Please enter the reason before rejecting this near miss."
                    if action == "REJECT"
                    else "Please enter the reason before sending this back."
                )
                raise serializers.ValidationError({"office_comment": message})
            return attrs

        if not attrs.get("near_miss_priority"):
            raise serializers.ValidationError({"near_miss_priority": "Select LOW, MEDIUM, or HIGH before accepting."})

        incident: Incident = self.context["incident"]
        suggestion = build_near_miss_priority_hint(incident)
        selected_priority = attrs["near_miss_priority"]
        current_priority = str(incident.near_miss_priority or "").strip().upper()
        if current_priority and selected_priority != current_priority and not priority_change_reason:
            raise serializers.ValidationError(
                {"priority_change_reason": "Please enter the reason for changing the priority."}
            )

        forced_high_reason = self._forced_high_reason(incident)
        if forced_high_reason and selected_priority != "HIGH":
            raise serializers.ValidationError(
                {
                    "near_miss_priority": (
                        f"{forced_high_reason} This near miss must be reviewed as high priority."
                    )
                }
            )

        if attrs.get("supersede_to_incident") and selected_priority != "HIGH":
            raise serializers.ValidationError(
                {"supersede_to_incident": "Only HIGH-priority near misses can be superseded into incidents."}
            )
        if attrs.get("supersede_to_incident") and not comment:
            raise serializers.ValidationError(
                {"office_comment": "Please enter the reason before superseding this near miss into an incident."}
            )

        subcode = str(attrs.get("near_miss_mscat_subcode_id") or "").strip()
        if subcode:
            mscat = MasterMscatTaxonomy.objects.filter(subcode_id=subcode, active=True).first()
            if mscat is None:
                raise serializers.ValidationError({"near_miss_mscat_subcode_id": "Select a valid immediate cause."})
            attrs["near_miss_mscat_subcode_id"] = mscat.subcode_id
            attrs["near_miss_mscat_category_id"] = mscat.category_id
            attrs["near_miss_mscat_subcode_ids"] = json.dumps([mscat.subcode_id])
        elif "near_miss_mscat_subcode_id" in attrs:
            attrs["near_miss_mscat_subcode_id"] = None
            attrs["near_miss_mscat_category_id"] = None
            attrs["near_miss_mscat_subcode_ids"] = json.dumps([])

        if "near_miss_shell_tag" in attrs:
            current_shell_tag = str(incident.near_miss_shell_tag or "").strip()
            next_category_tag = resolve_near_miss_category(attrs["near_miss_shell_tag"])
            if next_category_tag is None:
                raise serializers.ValidationError({"near_miss_shell_tag": "Category must match the Safety SSOT values."})
            next_shell_tag = NEAR_MISS_OTHER_CATEGORY if next_category_tag.startswith(NEAR_MISS_OTHER_PREFIX) else next_category_tag
            if next_shell_tag != current_shell_tag and not category_tag_change_reason:
                raise serializers.ValidationError(
                    {"category_tag_change_reason": "Please enter the reason for changing the category."}
                )
            attrs["near_miss_shell_tag"] = next_shell_tag
            attrs["near_miss_category_tags"] = json.dumps([next_category_tag])

        attrs["suggestion"] = suggestion
        return attrs

    def _forced_high_reason(self, incident: Incident) -> str:
        narrative = str(incident.narrative or "").lower()
        risk_markers = (
            "oil spill",
            "pollution",
            "overboard",
            "fire risk",
            "collision risk",
            "grounding risk",
            "serious injury risk",
        )
        if any(marker in narrative for marker in risk_markers):
            return "High-risk wording was found in the near-miss narrative."

        occurred_at = incident.occurred_at
        if occurred_at is None:
            return ""
        similar = Incident.objects.filter(
            vessel_id=incident.vessel_id,
            record_type=Incident.RecordType.NEAR_MISS,
            incident_type_id=incident.incident_type_id,
            loss_type_primary_id=incident.loss_type_primary_id,
            near_miss_shell_tag=incident.near_miss_shell_tag,
            occurred_at__gte=occurred_at - timedelta(days=90),
            occurred_at__lt=occurred_at,
        ).exclude(pk=incident.pk)
        if similar.exists():
            return "A similar near miss exists within the last 90 days."
        return ""
