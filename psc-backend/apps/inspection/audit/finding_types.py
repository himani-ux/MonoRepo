"""Audit finding enum normalization helpers."""

NC_FINDING_TYPE = "NC"
OBSERVATION_FINDING_TYPE = "OBSERVATION"

LEGACY_FINDING_TYPE_MAP = {
    "OBS": OBSERVATION_FINDING_TYPE,
}

LEGACY_NC_CATEGORY_MAP = {
    "MAJOR": "MAJOR_NC",
    "MINOR": "MINOR_NC",
}

LEGACY_OBSERVATION_CATEGORY_MAP = {
    "IMPROVEMENT": "IMPROVEMENT_SUGGESTION",
}


def normalize_finding_type(value: str | None) -> str:
    normalized = str(value or "").strip().upper()
    return LEGACY_FINDING_TYPE_MAP.get(normalized, normalized)


def normalize_nc_category(value: str | None) -> str | None:
    normalized = str(value or "").strip().upper()
    if not normalized:
        return None
    return LEGACY_NC_CATEGORY_MAP.get(normalized, normalized)


def normalize_observation_category(value: str | None) -> str | None:
    normalized = str(value or "").strip().upper()
    if not normalized:
        return None
    return LEGACY_OBSERVATION_CATEGORY_MAP.get(normalized, normalized)


def is_nc_finding(value: str | None) -> bool:
    return normalize_finding_type(value) == NC_FINDING_TYPE


def is_observation_finding(value: str | None) -> bool:
    return normalize_finding_type(value) == OBSERVATION_FINDING_TYPE
