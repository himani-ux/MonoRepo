from __future__ import annotations

from dataclasses import dataclass

from apps.safety.models import Incident, IncidentPhase5Assessment, MasterMscatTaxonomy


BLAME_TERMS = (
    "fault",
    "negligence",
    "negligent",
    "careless",
    "carelessness",
    "human error",
)


@dataclass(frozen=True)
class BlameEvaluation:
    blocked: bool
    trigger_terms: tuple[str, ...]
    all_root_personal_factors: bool
    has_lack_of_control: bool


class BlameDetector:
    def evaluate_incident(self, incident: Incident) -> BlameEvaluation:
        texts = [incident.narrative or ""]
        try:
            assessment: IncidentPhase5Assessment | None = incident.phase5_assessment
        except IncidentPhase5Assessment.DoesNotExist:
            assessment = None

        if assessment is not None:
            texts.extend(
                [
                    assessment.people_contribution_text,
                    assessment.process_gap_text,
                    assessment.plant_failure_text,
                    assessment.monocausal_justification or "",
                ]
            )

        texts.extend(incident.cause_tags.values_list("rationale", flat=True))
        lower_text = " ".join(texts).lower()
        trigger_terms = tuple(term for term in BLAME_TERMS if term in lower_text)

        root_subcodes = list(
            incident.cause_tags.filter(causal_layer="ROOT").values_list("mscat_subcode_id", flat=True)
        )
        root_rows = list(MasterMscatTaxonomy.objects.filter(subcode_id__in=root_subcodes))
        all_root_personal_factors = bool(root_rows) and all(
            row.category_id in {1, 2, 3, 4} for row in root_rows
        )
        has_lack_of_control = incident.cause_tags.filter(
            mscat_subcode_id__in=MasterMscatTaxonomy.objects.filter(
                cause_type="LACK_OF_CONTROL"
            ).values_list("subcode_id", flat=True)
        ).exists()

        return BlameEvaluation(
            blocked=bool(trigger_terms) or (all_root_personal_factors and not has_lack_of_control),
            trigger_terms=trigger_terms,
            all_root_personal_factors=all_root_personal_factors,
            has_lack_of_control=has_lack_of_control,
        )
