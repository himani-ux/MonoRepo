from __future__ import annotations

from django.utils import timezone
from django.db.utils import OperationalError, ProgrammingError
from rest_framework import serializers

from apps.safety.models import Incident, IncidentCauseTag, MasterSafetyBiasGuard, Recommendation
from apps.safety.services.alarp_gate import AlarpGate
from apps.safety.services.pdf_preview_generator import PdfPreviewGenerator
from apps.safety.services.signature_chain import SignatureChainService

GREEN_BAND_PIC_ROLE_CODES = (
    "PIC",
    "VESSEL SUPERINTENDENT",
    "OFFICE_PIC",
    "OFFICE_SSQE",
    "OFFICE_SUPT",
)


class IncidentPhase7AcceptSerializer(serializers.Serializer):
    typed_name = serializers.CharField()
    device_fingerprint = serializers.CharField()


class IncidentPhase7SendBackSerializer(serializers.Serializer):
    target_phase = serializers.IntegerField(min_value=3, max_value=6)
    reason = serializers.CharField(allow_blank=False)

    def validate_target_phase(self, value: int) -> int:
        if value not in {3, 4, 5, 6}:
            raise serializers.ValidationError("Phase 7 send-back target must be one of Phases 3, 4, 5, or 6.")
        return value


def build_phase7_preflight_payload(incident: Incident) -> dict[str, object]:
    gate = AlarpGate()
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

    bias_guards_resolved = False
    bitmask = (incident.bias_guard_attestations or "").strip()
    try:
        active_guard_count = MasterSafetyBiasGuard.objects.filter(active=True).count()
    except (OperationalError, ProgrammingError):
        active_guard_count = 0

    if active_guard_count and len(bitmask) >= active_guard_count and set(bitmask[:active_guard_count]) == {"1"}:
        bias_guards_resolved = True
    elif active_guard_count:
        bias_guards_resolved = (
            incident.bias_guard_responses.filter(acknowledged=True).count() == active_guard_count
        )
    else:
        bias_guards_resolved = bool(bitmask)

    root_count = incident.cause_tags.filter(causal_layer=IncidentCauseTag.CausalLayer.ROOT).count()
    alarp_complete = gate.incident_attestation_complete(incident, recommendations)
    closer_role = signature_chain.closer_role(incident)
    signature_status = signature_chain.signature_status(incident)
    required_process_id = signature_chain.required_process_id(incident)
    allowed_role_codes: tuple[str, ...] = ()
    authority_message = "Incident risk band must be assigned before Phase 7 acceptance."

    if incident.risk_band == Incident.RiskBand.GREEN:
        required_process_id = "SAF_P_006"
        allowed_role_codes = GREEN_BAND_PIC_ROLE_CODES
        authority_message = (
            "GREEN-band acceptance is restricted to the assigned PIC. "
            "If the assigned PIC is a role placeholder, PIC, VESSEL SUPERINTENDENT, OFFICE_PIC, OFFICE_SSQE, or OFFICE_SUPT may accept."
        )
    elif incident.risk_band == Incident.RiskBand.YELLOW:
        required_process_id = "SAF_P_004"
        allowed_role_codes = ("DPA",)
        authority_message = "YELLOW-band acceptance is restricted to DPA."
    elif incident.risk_band == Incident.RiskBand.RED:
        if signature_status["dpa"]["present"]:
            required_process_id = "SAF_P_005"
            allowed_role_codes = ("FM", "FLEET MANAGER")
            authority_message = "RED-band final approval is restricted to FM after DPA acceptance."
        else:
            required_process_id = "SAF_P_004"
            allowed_role_codes = ("DPA",)
            authority_message = "RED-band first acceptance is restricted to DPA; FM approval follows."

    blockers = []

    if not bias_guards_resolved:
        blockers.append("bias_guards")
    if root_count < 1:
        blockers.append("root_cause")
    if incident.risk_band in {Incident.RiskBand.YELLOW, Incident.RiskBand.RED}:
        for tier, blocker_code in (
            (Recommendation.Tier.CORRECTIVE, "corrective_tier"),
            (Recommendation.Tier.PREVENTIVE, "preventive_tier"),
            (Recommendation.Tier.LESSONS_LEARNT, "lessons_tier"),
        ):
            if tier_counts[tier] < 1:
                blockers.append(blocker_code)
    if not alarp_complete:
        blockers.append("alarp")

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
            "assigned_pic_user_id": incident.pic_user_id if incident.risk_band == Incident.RiskBand.GREEN else None,
            "allowed_role_codes": list(allowed_role_codes),
            "required_process_id": required_process_id,
            "message": authority_message,
        },
        "ready_for_acceptance": not blockers,
        "blockers": sorted(set(blockers)),
        "pdf_preview": PdfPreviewGenerator().build_preview(incident),
        "generated_at": timezone.now().isoformat(),
    }
