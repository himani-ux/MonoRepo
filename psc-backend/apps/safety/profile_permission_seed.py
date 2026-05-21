from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class PermissionBundle:
    form_ids: tuple[str, ...] = ()
    process_ids: tuple[str, ...] = ()


FORM = {
    "INCIDENTS": "SAF_F_001",
    "NEAR_MISS": "SAF_F_002",
    "SCM": "SAF_F_003",
    "SOI": "SAF_F_004",
    "SEARCH": "SAF_F_005",
    "SOI_APPLICABILITY": "SAF_F_013",
    "DASHBOARD": "SAF_F_015",
    "ADMIN": "SAF_F_018",
    "AUDITOR_EXPORT": "SAF_F_020",
}

PROCESS = {
    "CREATE": "SAF_P_001",
    "SUBMIT": "SAF_P_002",
    "SEND_BACK": "SAF_P_003",
    "APPROVE_CLOSE": "SAF_P_004",
    "FM_APPROVE": "SAF_P_005",
    "PIC_CLOSE_GREEN": "SAF_P_006",
    "REOPEN": "SAF_P_008",
    "PHASE5_OVERRIDE": "SAF_P_009",
    "SOI_PENDING_CLOSURE": "SAF_P_014",
    "SOI_APPROVE_CLOSURE": "SAF_P_015",
    "SOI_APPLICABILITY_REQUEST": "SAF_P_016",
    "SOI_APPLICABILITY_APPROVE": "SAF_P_017",
    "MSCAT_UPDATE": "SAF_P_018",
    "SOI_TEMPLATE_UPDATE": "SAF_P_019",
    "CA_CREATE": "SAF_P_020",
    "CA_LINK_PURCHASE": "SAF_P_021",
    "CA_VERIFY": "SAF_P_022",
    "EXPORT": "SAF_P_023",
    "FLEET_CIRCULAR": "SAF_P_024",
}

MASTER_PROFILES = {"MASTER"}
CHIEF_OFFICER_PROFILES = {"CHIEF OFFICER"}
CHIEF_ENGINEER_PROFILES = {"CHIEF ENGINEER"}
SECOND_ENGINEER_PROFILES = {"SECOND ENGINEER"}
TOP_FOUR_SHIP_PROFILES = (
    MASTER_PROFILES
    | CHIEF_OFFICER_PROFILES
    | CHIEF_ENGINEER_PROFILES
    | SECOND_ENGINEER_PROFILES
)
SCM_SHIP_PROFILES = MASTER_PROFILES | CHIEF_OFFICER_PROFILES | CHIEF_ENGINEER_PROFILES
SOI_SHIP_PROFILES = MASTER_PROFILES | CHIEF_OFFICER_PROFILES | SECOND_ENGINEER_PROFILES
OFFICER_SEARCH_PROFILES = TOP_FOUR_SHIP_PROFILES

OFFICE_DPA_PROFILES = {"SEQ MANAGER"}
OFFICE_FM_PROFILES = {"FLEET MANAGER"}
OFFICE_PIC_PROFILES = {
    "CREWING MANAGER",
    "MARINE SUPERINTENDENT",
    "TECHNICAL SUPERINTENDENT",
    "SENIOR TECHNICAL SUPERINTENDENT",
}
OFFICE_READ_ONLY_PROFILES = {
    "ENERGY EFFICIENCY AND OPERATIONS OFFICER",
    "OBSERVER",
}
OFFICE_SAFETY_PROFILES = (
    OFFICE_DPA_PROFILES
    | OFFICE_FM_PROFILES
    | OFFICE_PIC_PROFILES
    | OFFICE_READ_ONLY_PROFILES
)


def normalize_profile_name(profile_name: str | None) -> str:
    return (profile_name or "").strip().upper()


def parse_permission_list(value: object) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip().upper() for item in parsed if str(item).strip()]
        return [part.strip().upper() for part in raw.split(",") if part.strip()]

    if isinstance(value, (list, tuple, set)):
        return [str(item).strip().upper() for item in value if str(item).strip()]

    text = str(value).strip().upper()
    return [text] if text else []


def merge_permission_lists(existing: object, additions: tuple[str, ...]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in [*parse_permission_list(existing), *additions]:
        normalized = value.strip().upper()
        if not normalized or normalized in seen:
            continue
        merged.append(normalized)
        seen.add(normalized)
    return merged


def serialize_permission_list(values: list[str]) -> str:
    return json.dumps(values)


def target_permissions_for_profile(*, work_side: bool, profile_name: str) -> PermissionBundle:
    normalized = normalize_profile_name(profile_name)

    if work_side:
        if normalized == "NOT SELECTED":
            return PermissionBundle()

        form_ids = {FORM["NEAR_MISS"]}
        process_ids = {PROCESS["CREATE"]}

        if normalized in TOP_FOUR_SHIP_PROFILES:
            form_ids.update({FORM["INCIDENTS"], FORM["DASHBOARD"], FORM["SEARCH"]})
            process_ids.add(PROCESS["SUBMIT"])

        if normalized in SCM_SHIP_PROFILES:
            form_ids.add(FORM["SCM"])

        if normalized in SOI_SHIP_PROFILES:
            form_ids.add(FORM["SOI"])

        if normalized in MASTER_PROFILES:
            form_ids.update({FORM["SOI_APPLICABILITY"], FORM["AUDITOR_EXPORT"]})
            process_ids.update(
                {
                    PROCESS["APPROVE_CLOSE"],
                    PROCESS["SOI_APPROVE_CLOSURE"],
                    PROCESS["SOI_APPLICABILITY_REQUEST"],
                    PROCESS["EXPORT"],
                }
            )

        if normalized in CHIEF_OFFICER_PROFILES | SECOND_ENGINEER_PROFILES:
            process_ids.update(
                {
                    PROCESS["SOI_PENDING_CLOSURE"],
                    PROCESS["EXPORT"],
                }
            )

        if normalized in CHIEF_ENGINEER_PROFILES:
            process_ids.add(PROCESS["EXPORT"])

        return PermissionBundle(
            form_ids=tuple(sorted(form_ids)),
            process_ids=tuple(sorted(process_ids)),
        )

    if normalized not in OFFICE_SAFETY_PROFILES:
        return PermissionBundle()

    form_ids = {
        FORM["INCIDENTS"],
        FORM["NEAR_MISS"],
        FORM["SCM"],
        FORM["SOI"],
        FORM["SEARCH"],
        FORM["DASHBOARD"],
    }
    process_ids: set[str] = set()

    if normalized in OFFICE_DPA_PROFILES:
        form_ids.update(
            {
                FORM["SOI_APPLICABILITY"],
                FORM["ADMIN"],
                FORM["AUDITOR_EXPORT"],
            }
        )
        process_ids.update(
            {
                PROCESS["SUBMIT"],
                PROCESS["SEND_BACK"],
                PROCESS["APPROVE_CLOSE"],
                PROCESS["REOPEN"],
                PROCESS["PHASE5_OVERRIDE"],
                PROCESS["SOI_APPLICABILITY_APPROVE"],
                PROCESS["MSCAT_UPDATE"],
                PROCESS["SOI_TEMPLATE_UPDATE"],
                PROCESS["CA_CREATE"],
                PROCESS["CA_LINK_PURCHASE"],
                PROCESS["CA_VERIFY"],
                PROCESS["EXPORT"],
                PROCESS["FLEET_CIRCULAR"],
            }
        )

    if normalized in OFFICE_FM_PROFILES:
        form_ids.add(FORM["AUDITOR_EXPORT"])
        process_ids.update(
            {
                PROCESS["SUBMIT"],
                PROCESS["SEND_BACK"],
                PROCESS["FM_APPROVE"],
                PROCESS["REOPEN"],
                PROCESS["PHASE5_OVERRIDE"],
                PROCESS["CA_CREATE"],
                PROCESS["CA_LINK_PURCHASE"],
                PROCESS["CA_VERIFY"],
                PROCESS["EXPORT"],
                PROCESS["FLEET_CIRCULAR"],
            }
        )

    if normalized in OFFICE_PIC_PROFILES:
        process_ids.update(
            {
                PROCESS["APPROVE_CLOSE"],
                PROCESS["PIC_CLOSE_GREEN"],
                PROCESS["REOPEN"],
                PROCESS["CA_CREATE"],
                PROCESS["CA_LINK_PURCHASE"],
                PROCESS["CA_VERIFY"],
                PROCESS["EXPORT"],
            }
        )

    return PermissionBundle(
        form_ids=tuple(sorted(form_ids)),
        process_ids=tuple(sorted(process_ids)),
    )
