from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdvisoryBandResult:
    band: str
    rationale: str


_RED_INJURY_MARKERS = {"FATALITY", "MULTIPLE_FATALITIES", "LOSS_OF_LIFE"}
_YELLOW_INJURY_MARKERS = {"MAJOR", "LTI", "SERIOUS"}
_RED_POLLUTION_MARKERS = {"MAJOR", "SEVERE"}
_YELLOW_POLLUTION_MARKERS = {"MODERATE"}
_RED_DAMAGE_MARKERS = {"SEVERE", "TOTAL_LOSS"}
_YELLOW_DAMAGE_MARKERS = {"MODERATE", "HEAVY"}


def _normalize(value: object) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


def classify_band(
    loss_type: object = None,
    injuries: object = None,
    pollution: object = None,
    damage: object = None,
) -> AdvisoryBandResult:
    normalized_loss_type = _normalize(loss_type)
    normalized_injuries = _normalize(injuries)
    normalized_pollution = _normalize(pollution)
    normalized_damage = _normalize(damage)

    if (
        normalized_injuries in _RED_INJURY_MARKERS
        or normalized_pollution in _RED_POLLUTION_MARKERS
        or normalized_damage in _RED_DAMAGE_MARKERS
    ):
        return AdvisoryBandResult(
            band="RED",
            rationale=(
                "Advisory RED because the submitted incident profile includes catastrophic "
                "signals such as fatality, major pollution, or severe damage."
            ),
        )

    if (
        normalized_injuries in _YELLOW_INJURY_MARKERS
        or normalized_pollution in _YELLOW_POLLUTION_MARKERS
        or normalized_damage in _YELLOW_DAMAGE_MARKERS
        or normalized_loss_type in {"PERSONNEL_INJURY", "COLLISION", "GROUNDING", "FIRE", "POLLUTION"}
    ):
        reason_parts = []
        if normalized_injuries in _YELLOW_INJURY_MARKERS:
            reason_parts.append("major injury")
        if normalized_pollution in _YELLOW_POLLUTION_MARKERS:
            reason_parts.append("moderate pollution")
        if normalized_damage in _YELLOW_DAMAGE_MARKERS:
            reason_parts.append("moderate damage")
        if not reason_parts and normalized_loss_type:
            reason_parts.append(f"loss type {normalized_loss_type.lower().replace('_', ' ')}")
        return AdvisoryBandResult(
            band="YELLOW",
            rationale="Advisory YELLOW because the incident includes " + ", ".join(reason_parts) + ".",
        )

    return AdvisoryBandResult(
        band="GREEN",
        rationale="Advisory GREEN because only minor or non-escalating signals are present.",
    )
