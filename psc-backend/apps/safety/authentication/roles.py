from __future__ import annotations


CENTRAL_OFFICE_ROLE_CODES = {
    "DPA",
    "FM",
    "FLEET MANAGER",
    "OFFICE_PIC",
    "OFFICE_SSQE",
    "OFFICE_SUPT",
    "PHYSICAL_VERIFIER",
}


def normalize_role_code(value: object) -> str:
    return str(value or "").strip().upper()


def normalized_authority_role(user) -> str:
    if user is None:
        return ""

    central_role = normalize_role_code(getattr(user, "role", None))
    if central_role in CENTRAL_OFFICE_ROLE_CODES:
        return central_role

    for attr_name in ("safety_role_name", "role_name", "rank"):
        role = normalize_role_code(getattr(user, attr_name, None))
        if role:
            return role
    return central_role

