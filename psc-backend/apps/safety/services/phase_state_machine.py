from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone

from apps.safety.models import (
    EvidenceItem,
    Incident,
    IncidentBiasGuardResponse,
    IncidentCauseTag,
    IncidentPhase5Assessment,
    IncidentPhaseLog,
    MasterSafetyBiasGuard,
    Recommendation,
)
from apps.safety.repositories.exceptions import PhaseTransitionError

from .alarp_gate import AlarpGate
from .blame_detector import BlameDetector
from .field_history_recorder import resolve_actor_id, resolve_actor_role
from .incident_evidence_coverage import build_incident_evidence_coverage
from .signature_chain import SignatureChainService


@dataclass(frozen=True)
class TransitionResult:
    incident_id: int
    phase_from: int | None
    phase_to: int
    transition_type: str
    occurred_at: object


class PhaseStateMachine:
    allowed_forward_transitions = {
        1: 2,
        2: 3,
        3: 4,
        4: 5,
        5: 6,
        6: 7,
        7: 8,
    }
    allowed_loop_back_sources = {4, 5, 6}

    def __init__(self, *, model_class=Incident, phase_log_model=IncidentPhaseLog) -> None:
        self.model_class = model_class
        self.phase_log_model = phase_log_model
        self.alarp_gate = AlarpGate()
        self.blame_detector = BlameDetector()
        self.signature_chain = SignatureChainService()

    def transition(self, incident_id, to_phase, user, reason=None) -> dict[str, object]:
        incident = self.model_class.objects.get(pk=incident_id, is_deleted=False)
        from_phase = incident.current_phase
        transition_type = self._resolve_transition_type(from_phase=from_phase, to_phase=to_phase, reason=reason)
        self._enforce_gate(incident, to_phase)

        incident.current_phase = to_phase
        incident.updated_by = resolve_actor_id(user)
        incident.updated_date = timezone.now()
        incident.save(update_fields=["current_phase", "updated_by", "updated_date"])

        phase_log = self.phase_log_model.objects.create(
            incident=incident,
            phase_from=from_phase,
            phase_to=to_phase,
            transition_type=transition_type,
            loop_back_reason=reason if transition_type == IncidentPhaseLog.TransitionType.LOOP_BACK else None,
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            device_fingerprint=getattr(incident, "reporter_device_fingerprint", None),
            schema_version=incident.schema_version or 1,
        )
        return TransitionResult(
            incident_id=incident.pk,
            phase_from=from_phase,
            phase_to=to_phase,
            transition_type=transition_type,
            occurred_at=phase_log.occurred_at,
        ).__dict__

    def log_creation(self, incident, user) -> IncidentPhaseLog:
        return self.phase_log_model.objects.create(
            incident=incident,
            phase_from=None,
            phase_to=incident.current_phase,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            device_fingerprint=getattr(incident, "reporter_device_fingerprint", None),
            schema_version=incident.schema_version or 1,
        )

    def _resolve_transition_type(self, *, from_phase: int, to_phase: int, reason: str | None) -> str:
        if self.allowed_forward_transitions.get(from_phase) == to_phase:
            return IncidentPhaseLog.TransitionType.FORWARD
        if from_phase in self.allowed_loop_back_sources and to_phase == 3:
            if not reason:
                raise PhaseTransitionError("Loop-back to Phase 3 requires a written reason.")
            return IncidentPhaseLog.TransitionType.LOOP_BACK
        if from_phase == 8 and to_phase == 6:
            if not reason:
                raise PhaseTransitionError("Phase 8 rework to Phase 6 requires a written reason.")
            return IncidentPhaseLog.TransitionType.REWORK
        if from_phase == 8 and to_phase == 9:
            return IncidentPhaseLog.TransitionType.CLOSE
        raise PhaseTransitionError(
            f"Illegal incident phase transition from Phase {from_phase} to Phase {to_phase}."
        )

    def _enforce_gate(self, incident: Incident, to_phase: int) -> None:
        current_phase = incident.current_phase
        if current_phase == 1 and to_phase == 2:
            missing = []
            if not incident.first_hour_checklist_done:
                missing.append("first_hour_checklist_done")
            if not incident.narrative or len(incident.narrative.strip()) < 200:
                missing.append("narrative")
            if not incident.reporter_id:
                missing.append("reporter_id")
            if missing:
                raise PhaseTransitionError(
                    f"Phase 1 is incomplete for transition to Phase 2: {', '.join(missing)}."
                )
        elif current_phase == 2 and to_phase == 3:
            missing = []
            if not incident.risk_band:
                missing.append("risk_band")
            if not incident.imo_classifier:
                missing.append("imo_classifier")
            if not incident.resources_allocated:
                missing.append("resources_allocated")
            if incident.imo_classifier != Incident.ImoClassifier.NOT_APPLICABLE:
                if incident.latitude is None:
                    missing.append("latitude")
                if incident.longitude is None:
                    missing.append("longitude")
            if missing:
                raise PhaseTransitionError(
                    f"Phase 2 is incomplete for transition to Phase 3: {', '.join(missing)}."
                )
        elif current_phase == 3 and to_phase == 4:
            missing = []
            if not incident.chain_of_custody_ok:
                missing.append("chain_of_custody_ok")
            if not incident.marine_docs_checklist_done:
                missing.append("marine_docs_checklist_done")
            coverage = build_incident_evidence_coverage(incident)
            if coverage.missing_tabs:
                missing.append("evidence_tabs: " + ", ".join(coverage.missing_tabs))
            if missing:
                raise PhaseTransitionError(
                    "Phase 3 evidence preservation is incomplete: " + ", ".join(missing) + "."
                )
        elif current_phase == 4 and to_phase == 5:
            coverage = build_incident_evidence_coverage(incident)
            if coverage.missing_tabs:
                raise PhaseTransitionError(
                    "Phase 4 recency bias guard failed for evidence tabs: " + ", ".join(coverage.missing_tabs) + "."
                )
        elif current_phase == 5 and to_phase == 6:
            missing = []
            try:
                assessment = incident.phase5_assessment
            except IncidentPhase5Assessment.DoesNotExist:
                assessment = None

            root_count = incident.cause_tags.filter(causal_layer=IncidentCauseTag.CausalLayer.ROOT).count()
            if root_count < 1:
                missing.append("root_cause")
            if root_count == 1 and len((assessment.monocausal_justification or "").strip()) < 80:
                missing.append("monocausal_justification")

            if assessment is None:
                missing.extend(
                    [
                        "people_process_plant",
                        "analysis_tools_used",
                        "human_factors_payload",
                    ]
                )
            else:
                for field_name in (
                    "people_contribution_text",
                    "process_gap_text",
                    "plant_failure_text",
                ):
                    if len(getattr(assessment, field_name, "").strip()) < 50:
                        missing.append(field_name)

                minimum_tools = self._minimum_tool_count(incident)
                if len(set(assessment.analysis_tools_used or [])) < minimum_tools:
                    missing.append("analysis_tools_used")

                domains = (assessment.human_factors_payload or {}).get("domains", {})
                risk_change = domains.get("risk_change")
                if not isinstance(risk_change, dict) or not (risk_change.get("considered") or risk_change.get("notes")):
                    missing.append("human_factors_risk_change")

            safeguards = list(incident.safeguard_failures.all())
            if not safeguards:
                missing.append("safeguard_failures")
            else:
                for safeguard in safeguards:
                    if not all(
                        [
                            safeguard.design_mscat_subcode_id,
                            safeguard.installation_mscat_subcode_id,
                            safeguard.maintenance_mscat_subcode_id,
                            safeguard.operation_mscat_subcode_id,
                            safeguard.testing_mscat_subcode_id,
                            safeguard.override_mscat_subcode_id,
                        ]
                    ):
                        missing.append("safeguard_dimensions")
                        break

            major_findings = [
                row
                for row in incident.evidence_items.filter(item_type=EvidenceItem.ItemType.MATRIX)
                if (row.metadata_json or {}).get("major_finding")
            ]
            if any(not (row.con_evidence or "").strip() for row in major_findings):
                if assessment is None or len((assessment.confirmation_override_reason or "").strip()) == 0:
                    missing.append("confirmation_bias")

            if missing:
                raise PhaseTransitionError(
                    f"Phase 5 analysis gate failed: {', '.join(missing)}."
                )
            incident.causal_layering_complete = True
            incident.save(update_fields=["causal_layering_complete"])
        elif current_phase == 6 and to_phase == 7:
            errors: list[str] = []
            recommendations = list(incident.recommendations.filter(is_deleted=False).order_by("id"))
            if not recommendations:
                errors.append("recommendations")
            tier_counts = {
                Recommendation.Tier.CORRECTIVE: 0,
                Recommendation.Tier.PREVENTIVE: 0,
                Recommendation.Tier.LESSONS_LEARNT: 0,
            }
            for recommendation in recommendations:
                if recommendation.tier in tier_counts:
                    tier_counts[recommendation.tier] += 1
                if recommendation.tolerable_failure_filter and incident.risk_band != Incident.RiskBand.GREEN:
                    errors.append("tolerable_failure_filter")
                if self.alarp_gate.require_alarp(incident, recommendation):
                    if self.alarp_gate.missing_fields(recommendation):
                        errors.append("alarp_fields")
                    if not recommendation.alarp_attested:
                        errors.append("alarp_attestation")

            if incident.risk_band in {Incident.RiskBand.YELLOW, Incident.RiskBand.RED}:
                for tier, error_code in (
                    (Recommendation.Tier.CORRECTIVE, "corrective_tier"),
                    (Recommendation.Tier.PREVENTIVE, "preventive_tier"),
                    (Recommendation.Tier.LESSONS_LEARNT, "lessons_tier"),
                ):
                    if tier_counts[tier] < 1:
                        errors.append(error_code)

            if not self._bias_guards_complete(incident):
                errors.append("bias_guards")
            blame_evaluation = self.blame_detector.evaluate_incident(incident)
            if blame_evaluation.blocked and not incident.blame_fixation_override_by:
                errors.append("blame_override")

            incident.alarp_attested = self.alarp_gate.incident_attestation_complete(incident, recommendations)
            if errors:
                if incident.alarp_attested:
                    incident.save(update_fields=["alarp_attested"])
                raise PhaseTransitionError(
                    "Phase 6 recommendation gate failed: " + ", ".join(sorted(set(errors))) + "."
                )

            incident.save(update_fields=["alarp_attested"])
        elif current_phase == 7 and to_phase == 8:
            blockers = self.signature_chain.phase_seven_blockers(incident)
            if incident.risk_band in {Incident.RiskBand.GREEN, Incident.RiskBand.YELLOW}:
                if not incident.dpa_accepted_at or not incident.dpa_accepted_by:
                    blockers.append("closer_signature")
            elif incident.risk_band == Incident.RiskBand.RED:
                if not incident.dpa_accepted_at or not incident.dpa_accepted_by:
                    blockers.append("dpa_signature")
                if not incident.fm_approved_at or not incident.fm_approved_by:
                    blockers.append("fm_signature")
            if blockers:
                raise PhaseTransitionError(
                    "Phase 7 acceptance gate failed: " + ", ".join(sorted(set(blockers))) + "."
                )
        elif current_phase == 8 and to_phase == 9:
            from apps.safety.serializers.incident_phase8 import build_phase8_workspace_payload

            tracker = build_phase8_workspace_payload(incident)
            if tracker["blockers"]:
                raise PhaseTransitionError(
                    "Phase 8 follow-up gate failed: " + ", ".join(tracker["blockers"]) + "."
                )

    @staticmethod
    def _minimum_tool_count(incident: Incident) -> int:
        if incident.risk_band == Incident.RiskBand.RED:
            return 5
        if incident.investigation_depth == Incident.InvestigationDepth.DEEP:
            return 5
        if incident.investigation_depth == Incident.InvestigationDepth.MEDIUM:
            return 3
        return 2

    @staticmethod
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
