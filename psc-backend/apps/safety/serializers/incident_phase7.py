from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import Incident, IncidentCauseTag, IncidentPhaseLog, Recommendation
from apps.safety.services.pdf_preview_generator import PdfPreviewGenerator
from apps.safety.services.signature_chain import SignatureChainService

GREEN_BAND_PIC_ROLE_CODES = (
    "PIC",
    "VESSEL SUPERINTENDENT",
    "OFFICE_PIC",
    "OFFICE_SSQE",
    "OFFICE_SUPT",
)
OFFICE_REVIEW_ROLE_CODES = ("DPA", *GREEN_BAND_PIC_ROLE_CODES)
OFFICE_REVIEW_PROCESS_IDS = ("SAF_P_004", "SAF_P_006")


class IncidentPhase7AcceptSerializer(serializers.Serializer):
    typed_name = serializers.CharField()
    device_fingerprint = serializers.CharField()
    office_comment = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)


class IncidentPhase7SendBackSerializer(serializers.Serializer):
    target_phase = serializers.IntegerField(min_value=3, max_value=6)
    reason = serializers.CharField(allow_blank=False)

    def validate_target_phase(self, value: int) -> int:
        if value not in {3, 4, 5, 6}:
            raise serializers.ValidationError("Send-back target must be one of Phases 3, 4, 5, or 6.")
        return value


def build_phase7_preflight_payload(incident: Incident) -> dict[str, object]:
    signature_chain = SignatureChainService()
    recommendations = list(incident.recommendations.filter(is_deleted=False).order_by("id"))
    tier_counts = {
        Recommendation.Tier.CORRECTIVE: 0,
        Recommendation.Tier.PREVENTIVE: 0,
        Recommendation.Tier.LESSONS_LEARNT: 0,
    }
    for recommendation in recommendations:
        if recommendation.tier in tier_counts:
            tier_counts[recommendation.tier] += 1

    bias_guards_resolved = True
    root_count = incident.cause_tags.filter(causal_layer=IncidentCauseTag.CausalLayer.ROOT).count()
    alarp_complete = True
    closer_role = signature_chain.closer_role(incident)
    signature_status = signature_chain.signature_status(incident)
    required_process_id = signature_chain.required_process_id(incident)
    allowed_role_codes = OFFICE_REVIEW_ROLE_CODES
    authority_message = (
        "PIC or DPA can accept, close, or send this incident back for rework for any risk band."
    )

    blockers = []

    if root_count < 1:
        blockers.append("root_cause")
    if not recommendations:
        blockers.append("recommendations")

    blockers.extend(signature_chain.phase_seven_blockers(incident))

    return {
        "incident_id": incident.pk,
        "current_phase": incident.current_phase,
        "risk_band": incident.risk_band,
        "bias_guards_resolved": bias_guards_resolved,
        "root_count": root_count,
        "recommendation_tier_count": tier_counts,
        "alarp_complete": alarp_complete,
        "signature_chain_status": signature_status,
        "closer_role": closer_role,
        "required_process_id": required_process_id,
        "authority": {
            "assigned_pic_user_id": incident.pic_user_id,
            "allowed_role_codes": list(allowed_role_codes),
            "allowed_process_ids": list(OFFICE_REVIEW_PROCESS_IDS),
            "required_process_id": required_process_id,
            "message": authority_message,
        },
        "ready_for_acceptance": not blockers,
        "blockers": sorted(set(blockers)),
        "office_comment": incident.office_comment or "",
        "rework_summary": build_latest_rework_summary(incident),
        "pdf_preview": PdfPreviewGenerator().build_preview(incident),
        "generated_at": timezone.now().isoformat(),
    }


def build_latest_rework_summary(incident: Incident) -> dict[str, object] | None:
    if incident.state != Incident.State.SENT_BACK:
        return None

    phase_log = (
        IncidentPhaseLog.objects.filter(
            incident=incident,
            transition_type=IncidentPhaseLog.TransitionType.REWORK,
        )
        .order_by("-occurred_at")
        .first()
    )
    if phase_log is None:
        return None

    comment = str(phase_log.loop_back_reason or "").strip()
    if not comment:
        return None

    return {
        "comment": comment,
        "requested_at": phase_log.occurred_at,
        "requested_by": phase_log.actor_user_id,
        "requested_by_role": phase_log.actor_role_code,
    }
