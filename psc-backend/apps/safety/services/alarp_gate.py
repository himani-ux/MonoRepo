from __future__ import annotations

import os
from typing import Any

from apps.safety.models import Incident, Recommendation


RECOMMENDATION_THEMES = (
    {"code": "TRAINING_COMPETENCE", "label": "Training & Competence"},
    {"code": "CONTRACTOR_SUPPLIER_MANAGEMENT", "label": "Contractor / Supplier Management"},
    {"code": "COMPLIANCE_ASSURANCE", "label": "Compliance Assurance"},
    {"code": "HUMAN_RESOURCES", "label": "Human Resources"},
    {"code": "MANAGEMENT_OF_CHANGE", "label": "Management of Change"},
    {"code": "PROCEDURES_STANDARDS", "label": "Procedures & Standards"},
    {"code": "EQUIPMENT_MANAGEMENT", "label": "Equipment Management"},
)


class AlarpGate:
    theme_codes = {row["code"] for row in RECOMMENDATION_THEMES}
    likelihood_codes = {
        Recommendation.LikelihoodReduction.LOW,
        Recommendation.LikelihoodReduction.MED,
        Recommendation.LikelihoodReduction.HIGH,
    }

    def require_alarp(self, incident: Incident, recommendation_or_tier: Any) -> bool:
        return (
            self._resolve_tier(recommendation_or_tier) == Recommendation.Tier.PREVENTIVE
            and incident.risk_band in {Incident.RiskBand.YELLOW, Incident.RiskBand.RED}
        )

    def missing_fields(self, recommendation_or_payload: Any) -> list[str]:
        missing: list[str] = []
        for field_name in (
            "estimated_likelihood_reduction",
        ):
            value = self._read_field(recommendation_or_payload, field_name)
            if value in (None, ""):
                missing.append(field_name)
        return missing

    def transition_ready(self, incident: Incident, recommendation: Recommendation) -> bool:
        if not self.require_alarp(incident, recommendation):
            return True
        return not self.missing_fields(recommendation) and recommendation.alarp_attested

    def incident_attestation_complete(
        self,
        incident: Incident,
        recommendations: list[Recommendation],
    ) -> bool:
        required_rows = [row for row in recommendations if self.require_alarp(incident, row)]
        if not required_rows:
            return True
        return all(self.transition_ready(incident, row) for row in required_rows)

    @staticmethod
    def resolve_threshold() -> str | None:
        raw = os.getenv("SAFETY_ALARP_COST_THRESHOLD", "").strip()
        return raw or None

    @staticmethod
    def _resolve_tier(recommendation_or_tier: Any) -> str | None:
        if isinstance(recommendation_or_tier, str):
            return recommendation_or_tier
        return getattr(recommendation_or_tier, "tier", None)

    @staticmethod
    def _read_field(recommendation_or_payload: Any, field_name: str) -> Any:
        if isinstance(recommendation_or_payload, dict):
            return recommendation_or_payload.get(field_name)
        return getattr(recommendation_or_payload, field_name, None)
