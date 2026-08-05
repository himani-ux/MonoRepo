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

        update_fields = ["current_phase", "updated_by", "updated_date"]
        incident.current_phase = to_phase
        if incident.state == Incident.State.SENT_BACK and to_phase == 7:
            incident.state = Incident.State.UNDER_REVIEW
            update_fields.append("state")
        incident.updated_by = resolve_actor_id(user)
        incident.updated_date = timezone.now()
        incident.save(update_fields=update_fields)

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
        if from_phase == 3 and to_phase == 6:
            return IncidentPhaseLog.TransitionType.FORWARD
        if self.allowed_forward_transitions.get(from_phase) == to_phase:
            return IncidentPhaseLog.TransitionType.FORWARD
        if from_phase in self.allowed_loop_back_sources and to_phase == 3:
            if not reason:
                raise PhaseTransitionError("Loop-back to Phase 3 requires a written reason.")
            return IncidentPhaseLog.TransitionType.LOOP_BACK
        if from_phase == 8 and to_phase == 6:
            if not reason:
                raise PhaseTransitionError("Sending Loss Evaluation back to Phase 4 requires a written reason.")
            return IncidentPhaseLog.TransitionType.REWORK
        if from_phase in {7, 8} and to_phase == 9:
            return IncidentPhaseLog.TransitionType.CLOSE
        raise PhaseTransitionError(
            f"Illegal incident phase transition from Phase {from_phase} to Phase {to_phase}."
        )

    def _enforce_gate(self, incident: Incident, to_phase: int) -> None:
        current_phase = incident.current_phase
        if current_phase == 1 and to_phase == 2:
            missing = []
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
            if not incident.resources_allocated:
                missing.append("resources_allocated")
            if missing:
                raise PhaseTransitionError(
                    f"Office communication is incomplete before root cause: {', '.join(missing)}."
                )
        elif current_phase == 3 and to_phase in {4, 6}:
            missing = []
            required_layers = (
                (IncidentCauseTag.CausalLayer.IMMEDIATE, "immediate_cause"),
                (IncidentCauseTag.CausalLayer.ROOT, "root_cause"),
            )
            for layer, label in required_layers:
                if incident.cause_tags.filter(causal_layer=layer).count() < 1:
                    missing.append(label)
            if missing:
                raise PhaseTransitionError(
                    "Phase 2 cause selection is incomplete: " + ", ".join(missing) + "."
                )
            if to_phase == 6:
                incident.causal_layering_complete = True
                incident.save(update_fields=["causal_layering_complete"])
        elif current_phase == 4 and to_phase == 5:
            coverage = build_incident_evidence_coverage(incident)
            if not coverage.covered_tabs:
                raise PhaseTransitionError(
                    "Phase 4 evidence is incomplete: add at least one evidence note, file, interview, or N/A reason."
                )
        elif current_phase == 5 and to_phase == 6:
            missing = []

            root_count = incident.cause_tags.filter(causal_layer=IncidentCauseTag.CausalLayer.ROOT).count()
            if root_count < 1:
                missing.append("root_cause")

            for matrix_row in incident.evidence_items.filter(item_type=EvidenceItem.ItemType.MATRIX):
                metadata = matrix_row.metadata_json or {}
                if metadata.get("major_finding") and not (matrix_row.con_evidence or "").strip():
                    missing.append("major_finding_con_evidence")
                    break

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
            if not incident.dpa_accepted_at or not incident.dpa_accepted_by:
                blockers.append("closer_signature")
            if blockers:
                raise PhaseTransitionError(
                    "Phase 7 acceptance gate failed: " + ", ".join(sorted(set(blockers))) + "."
                )
        elif current_phase == 8 and to_phase == 9:
            from apps.safety.models import IncidentLossEvaluation

            if not IncidentLossEvaluation.objects.filter(incident=incident).exists():
                raise PhaseTransitionError(
                    "Phase 7 Loss Evaluation is incomplete: save Loss Evaluation before closing."
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
