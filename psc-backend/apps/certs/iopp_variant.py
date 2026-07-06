from __future__ import annotations


IOPP_CANONICAL_CODE = "STAT-IOPP"
FORM_VARIANT_A = "A"
FORM_VARIANT_B = "B"
FORM_VARIANT_NA = "n/a"
FORM_VARIANTS = (FORM_VARIANT_A, FORM_VARIANT_B, FORM_VARIANT_NA)

IOPP_VARIANT_CATALOG_ERROR = (
    "Model IOPP Form A/B on tracked-item formVariant; keep one STAT-IOPP catalog row."
)


def normalize_form_variant(value: object) -> str:
    if value is None:
        return FORM_VARIANT_NA
    normalized = str(value).strip()
    if normalized == "":
        return FORM_VARIANT_NA
    upper = normalized.upper()
    if upper in {FORM_VARIANT_A, FORM_VARIANT_B}:
        return upper
    if upper in {"N/A", "NA", "NONE"}:
        return FORM_VARIANT_NA
    raise ValueError("formVariant must be one of A, B, or n/a.")


def is_iopp_variant_catalog_code(value: object) -> bool:
    normalized = str(value or "").strip().upper().replace("_", "-").replace(" ", "-")
    return normalized in {"IOPP-A", "IOPP-B"} or normalized.endswith("-IOPP-A") or normalized.endswith("-IOPP-B")
