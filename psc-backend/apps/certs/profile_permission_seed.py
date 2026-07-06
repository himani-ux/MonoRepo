from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class PermissionBundle:
    form_ids: tuple[str, ...] = ()
    process_ids: tuple[str, ...] = ()


FORM = {
    "CATALOG": "CERT_F_001",
    "TRACKED_ITEMS": "CERT_F_002",
    "RECONCILIATION": "CERT_F_003",
    "PRINT_EXPORT": "CERT_F_004",
    "ONBOARDING": "CERT_F_005",
    "NOTIFICATION_CONFIG": "CERT_F_006",
    "AUDITOR_ACCESS": "CERT_F_007",
    "AUDIT_LOG": "CERT_F_008",
}

PROCESS = {
    "CREATE": "CERT_P_001",
    "SUBMIT": "CERT_P_002",
    "APPROVE": "CERT_P_003",
    "REJECT": "CERT_P_004",
    "PRINT": "CERT_P_005",
    "EXPORT_BUNDLE": "CERT_P_006",
    "PROVISION_AUDITOR": "CERT_P_007",
    "CATALOG_EDIT": "CERT_P_008",
    "BULK_ACTION": "CERT_P_009",
    "ROLLBACK": "CERT_P_010",
}

OFFICE_DPA_PROFILES = {"SEQ MANAGER"}
OFFICE_SYSTEM_ADMIN_PROFILES = {"ADMIN", "SUPER ADMIN"}
OFFICE_FM_PROFILES = {"FLEET MANAGER"}
OFFICE_TECH_SUPT_PROFILES = {
    "TECHNICAL SUPERINTENDENT",
    "SENIOR TECHNICAL SUPERINTENDENT",
}
OFFICE_MARINE_SUPT_PROFILES = {"MARINE SUPERINTENDENT"}
OFFICE_TECHNICAL_MANAGER_PROFILES = {"TECHNICAL MANAGER"}

MASTER_PROFILES = {"MASTER"}
VESSEL_SUBMITTER_PROFILES = {"CHIEF OFFICER", "CHIEF ENGINEER", "SECOND ENGINEER"}


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
        return _target_ship_permissions(normalized)

    return _target_office_permissions(normalized)


def _target_office_permissions(normalized: str) -> PermissionBundle:
    full_admin = OFFICE_DPA_PROFILES | OFFICE_SYSTEM_ADMIN_PROFILES
    if normalized in full_admin:
        return PermissionBundle(
            form_ids=tuple(FORM.values()),
            process_ids=tuple(PROCESS.values()),
        )

    if normalized in OFFICE_FM_PROFILES:
        return PermissionBundle(
            form_ids=(
                FORM["CATALOG"],
                FORM["TRACKED_ITEMS"],
                FORM["RECONCILIATION"],
                FORM["PRINT_EXPORT"],
                FORM["ONBOARDING"],
                FORM["AUDITOR_ACCESS"],
                FORM["AUDIT_LOG"],
            ),
            process_ids=(
                PROCESS["CREATE"],
                PROCESS["SUBMIT"],
                PROCESS["PRINT"],
                PROCESS["EXPORT_BUNDLE"],
                PROCESS["CATALOG_EDIT"],
            ),
        )

    if normalized in OFFICE_TECH_SUPT_PROFILES:
        return PermissionBundle(
            form_ids=(
                FORM["CATALOG"],
                FORM["TRACKED_ITEMS"],
                FORM["RECONCILIATION"],
                FORM["PRINT_EXPORT"],
                FORM["AUDIT_LOG"],
            ),
            process_ids=(
                PROCESS["CREATE"],
                PROCESS["PRINT"],
            ),
        )

    if normalized in OFFICE_MARINE_SUPT_PROFILES:
        return PermissionBundle(
            form_ids=(
                FORM["CATALOG"],
                FORM["TRACKED_ITEMS"],
                FORM["RECONCILIATION"],
                FORM["PRINT_EXPORT"],
                FORM["AUDITOR_ACCESS"],
                FORM["AUDIT_LOG"],
            ),
            process_ids=(
                PROCESS["CREATE"],
                PROCESS["SUBMIT"],
                PROCESS["PRINT"],
                PROCESS["PROVISION_AUDITOR"],
                PROCESS["ROLLBACK"],
            ),
        )

    if normalized in OFFICE_TECHNICAL_MANAGER_PROFILES:
        return PermissionBundle(
            form_ids=(
                FORM["CATALOG"],
                FORM["TRACKED_ITEMS"],
                FORM["RECONCILIATION"],
                FORM["PRINT_EXPORT"],
                FORM["AUDIT_LOG"],
            ),
            process_ids=(PROCESS["PRINT"],),
        )

    return PermissionBundle()


def _target_ship_permissions(normalized: str) -> PermissionBundle:
    if normalized == "NOT SELECTED":
        return PermissionBundle()

    if normalized in MASTER_PROFILES:
        return PermissionBundle(
            form_ids=(
                FORM["TRACKED_ITEMS"],
                FORM["RECONCILIATION"],
                FORM["PRINT_EXPORT"],
            ),
            process_ids=(
                PROCESS["CREATE"],
                PROCESS["APPROVE"],
                PROCESS["REJECT"],
                PROCESS["PRINT"],
                PROCESS["EXPORT_BUNDLE"],
            ),
        )

    if normalized in VESSEL_SUBMITTER_PROFILES:
        return PermissionBundle(
            form_ids=(FORM["TRACKED_ITEMS"],),
            process_ids=(
                PROCESS["CREATE"],
                PROCESS["SUBMIT"],
            ),
        )

    return PermissionBundle(form_ids=(FORM["TRACKED_ITEMS"],))

