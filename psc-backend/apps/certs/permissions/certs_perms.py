from __future__ import annotations

from collections.abc import Iterable
import json

from rest_framework.permissions import BasePermission


CATALOG_FORM_ID = "CERT_F_001"
CATALOG_CREATE_PROCESS_ID = "CERT_P_001"
CATALOG_EDIT_PROCESS_ID = "CERT_P_008"
CATALOG_BULK_PROCESS_ID = "CERT_P_009"
TRACKED_ITEM_FORM_ID = "CERT_F_002"
TRACKED_ITEM_WRITE_PROCESS_ID = "CERT_P_001"
TRACKED_ITEM_SUBMIT_PROCESS_ID = "CERT_P_002"
TRACKED_ITEM_APPROVE_PROCESS_ID = "CERT_P_003"
TRACKED_ITEM_REJECT_PROCESS_ID = "CERT_P_004"
ONBOARDING_FORM_ID = "CERT_F_005"
ONBOARDING_CREATE_PROCESS_ID = "CERT_P_001"
ONBOARDING_SIGNOFF_PROCESS_ID = "CERT_P_002"
ONBOARDING_ROLLBACK_PROCESS_ID = "CERT_P_010"
RECONCILIATION_FORM_ID = "CERT_F_003"
RECONCILIATION_UPLOAD_PROCESS_ID = "CERT_P_001"
RECONCILIATION_REVIEW_PROCESS_ID = "CERT_P_002"
RECONCILIATION_MAPPING_PROCESS_ID = "CERT_P_008"
RECONCILIATION_ROLLBACK_PROCESS_ID = "CERT_P_010"
PRINT_EXPORT_FORM_ID = "CERT_F_004"
PRINT_PROCESS_ID = "CERT_P_005"
EXPORT_BUNDLE_PROCESS_ID = "CERT_P_006"
AUDITOR_ACCESS_FORM_ID = "CERT_F_007"
AUDITOR_ACCESS_PROCESS_ID = "CERT_P_007"
AUDIT_LOG_FORM_ID = "CERT_F_008"
NOTIFICATION_CONFIG_FORM_ID = "CERT_F_006"

CATALOG_WRITER_ROLES = {
    "ADMIN",
    "DPA",
    "SEQ MANAGER",
    "SUPER ADMIN",
    "SYSTEM ADMIN",
}
RECONCILIATION_REVIEWER_ROLES = {
    "ADMIN",
    "DPA",
    "MARINE SUPERINTENDENT",
    "MARINE SUP'TT",
    "MARINE SUPT",
    "SUPER ADMIN",
    "SYSTEM ADMIN",
}
RECONCILIATION_UPLOAD_ROLES = RECONCILIATION_REVIEWER_ROLES | {
    "FM",
    "FLEET MANAGER",
    "TECHNICAL MANAGER",
    "TECHNICAL SUPERINTENDENT",
    "TECH SUP'TT",
    "TECH SUPT",
}
RECONCILIATION_MAPPING_WRITER_ROLES = {
    "ADMIN",
    "DPA",
    "SUPER ADMIN",
    "SYSTEM ADMIN",
}
AUDIT_LOG_FULL_FLEET_ROLES = {"DPA", "FM", "FLEET MANAGER"}
AUDIT_LOG_SCOPED_ROLES = {
    "MARINE SUPERINTENDENT",
    "MARINE SUP'TT",
    "MARINE SUPT",
    "TECHNICAL MANAGER",
    "TECHNICAL SUPERINTENDENT",
    "TECH SUP'TT",
    "TECH SUPT",
}
AUDITOR_ACCESS_READ_ROLES = {
    "DPA",
    "FM",
    "FLEET MANAGER",
    "MARINE SUPERINTENDENT",
    "MARINE SUP'TT",
    "MARINE SUPT",
}
AUDITOR_ACCESS_WRITE_ROLES = {
    "DPA",
    "MARINE SUPERINTENDENT",
    "MARINE SUP'TT",
    "MARINE SUPT",
}
SETTINGS_WRITER_ROLES = {
    "ADMIN",
    "DPA",
    "SUPER ADMIN",
    "SYSTEM ADMIN",
}


def _normalize_permission_ids(value: object) -> set[str]:
    if value is None:
        return set()

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return set()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                parsed = None
            if parsed is not None:
                return _normalize_permission_ids(parsed)
        return {part.strip().upper() for part in stripped.split(",") if part.strip()}

    if isinstance(value, Iterable):
        return {str(item).strip().upper() for item in value if str(item).strip()}

    text = str(value).strip().upper()
    return {text} if text else set()


def _request_permission_ids(request, attr_name: str) -> set[str]:
    user = getattr(request, "user", None)
    auth = getattr(request, "auth", None)
    auth_payload_value = auth.get(attr_name) if hasattr(auth, "get") else None
    return (
        _normalize_permission_ids(getattr(user, attr_name, None))
        | _normalize_permission_ids(getattr(auth, attr_name, None))
        | _normalize_permission_ids(auth_payload_value)
    )


def _scope_ids(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                parsed = None
            if parsed is not None:
                return _scope_ids(parsed)
        return [part.strip() for part in stripped.split(",") if part.strip()]
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _normalized_role(user) -> str:
    for attr_name in ("role", "role_name", "safety_role_name"):
        value = getattr(user, attr_name, None)
        if value:
            return str(value).strip().upper()
    return ""


def normalized_role(user) -> str:
    return _normalized_role(user)


def has_certs_perm(user, form_id: str, process_id: str | None = None) -> bool:
    form_ids = _normalize_permission_ids(getattr(user, "form_ids", None))
    process_ids = _normalize_permission_ids(getattr(user, "process_ids", None))
    if form_id.strip().upper() not in form_ids:
        return False
    if process_id is None:
        return True
    return process_id.strip().upper() in process_ids


def has_request_certs_perm(request, form_id: str, process_id: str | None = None) -> bool:
    form_ids = _request_permission_ids(request, "form_ids")
    process_ids = _request_permission_ids(request, "process_ids")
    if form_id.strip().upper() not in form_ids:
        return False
    if process_id is None:
        return True
    return process_id.strip().upper() in process_ids


def is_master_user(user) -> bool:
    role_text = " ".join(
        str(getattr(user, attr_name, "") or "").strip().upper()
        for attr_name in ("role", "role_name", "safety_role_name", "rank")
    )
    return "VESSEL_MASTER" in role_text or "MASTER" in role_text or "CAPTAIN" in role_text


def is_vessel_sub_officer(user) -> bool:
    role_text = " ".join(
        str(getattr(user, attr_name, "") or "").strip().upper()
        for attr_name in ("role", "role_name", "safety_role_name", "rank")
    )
    markers = (
        "CHIEF OFFICER",
        "CHIEF ENGINEER",
        "SECOND ENGINEER",
        "C/O",
        "C.O",
        "C/E",
        "C.E",
        "2/E",
        "2E",
    )
    return (getattr(user, "user_type", "") or "").upper() == "VESSEL" and any(marker in role_text for marker in markers)


def user_can_access_vessel(user, vessel_id: str) -> bool:
    normalized_vessel_id = str(vessel_id or "").strip().lower()
    if not normalized_vessel_id:
        return False
    if (getattr(user, "user_type", "") or "").upper() == "VESSEL":
        return str(getattr(user, "vessel_id", "") or "").strip().lower() == normalized_vessel_id
    if getattr(user, "has_global_vessel_access", None) is True:
        return True
    role_text = _normalized_role(user)
    if role_text in {"DPA", "FM", "FLEET MANAGER", "SEQ MANAGER", "SUPER ADMIN", "SYSTEM ADMIN"}:
        return True
    vessel_ids = _normalize_permission_ids(getattr(user, "vessel_ids", None))
    return normalized_vessel_id.upper() in vessel_ids or normalized_vessel_id in {value.lower() for value in vessel_ids}


class HasAnyCertsFormPermission(BasePermission):
    message = "You do not have access to this Certs form."

    def has_permission(self, request, view) -> bool:
        return any(permission_id.startswith("CERT_F_") for permission_id in _request_permission_ids(request, "form_ids"))


class HasCatalogReadPermission(BasePermission):
    message = "You do not have access to the Certs catalog."

    def has_permission(self, request, view) -> bool:
        return CATALOG_FORM_ID in _request_permission_ids(request, "form_ids")


class HasTrackedItemReadPermission(BasePermission):
    message = "You do not have access to Certs tracked items."

    def has_permission(self, request, view) -> bool:
        return TRACKED_ITEM_FORM_ID in _request_permission_ids(request, "form_ids")


class HasOnboardingReadPermission(BasePermission):
    message = "You do not have access to the Certs onboarding wizard."

    def has_permission(self, request, view) -> bool:
        return ONBOARDING_FORM_ID in _request_permission_ids(request, "form_ids")


class HasReconciliationReadPermission(BasePermission):
    message = "You do not have access to Certs reconciliation."

    def has_permission(self, request, view) -> bool:
        return RECONCILIATION_FORM_ID in _request_permission_ids(request, "form_ids")


def audit_log_vessel_scope(user) -> list[str] | None:
    role = _normalized_role(user)
    if role in AUDIT_LOG_FULL_FLEET_ROLES:
        return None
    vessel_ids = _scope_ids(getattr(user, "vessel_ids", None))
    if not vessel_ids:
        vessel_ids = _scope_ids(getattr(user, "vessel_id", None))
    return sorted(set(vessel_ids))


class HasAuditLogReadPermission(BasePermission):
    message = "You do not have access to the Certs audit log."

    def has_permission(self, request, view) -> bool:
        if AUDIT_LOG_FORM_ID not in _request_permission_ids(request, "form_ids"):
            return False
        user = getattr(request, "user", None)
        if str(getattr(user, "user_type", "") or "").upper() == "EXTERNAL_AUDITOR":
            return False
        role = _normalized_role(user)
        return role in AUDIT_LOG_FULL_FLEET_ROLES or role in AUDIT_LOG_SCOPED_ROLES


class HasAuditorAccessReadPermission(BasePermission):
    message = "You do not have access to external auditor grants."

    def has_permission(self, request, view) -> bool:
        if AUDITOR_ACCESS_FORM_ID not in _request_permission_ids(request, "form_ids"):
            return False
        user = getattr(request, "user", None)
        if str(getattr(user, "user_type", "") or "").upper() == "EXTERNAL_AUDITOR":
            return False
        return _normalized_role(user) in AUDITOR_ACCESS_READ_ROLES


class IsAuditorAccessWriter(BasePermission):
    message = "Only DPA or Marine Sup'tt may provision external auditor access."

    def has_permission(self, request, view) -> bool:
        form_ids = _request_permission_ids(request, "form_ids")
        process_ids = _request_permission_ids(request, "process_ids")
        if AUDITOR_ACCESS_FORM_ID not in form_ids or AUDITOR_ACCESS_PROCESS_ID not in process_ids:
            return False
        return _normalized_role(getattr(request, "user", None)) in AUDITOR_ACCESS_WRITE_ROLES


class HasSettingsReadPermission(BasePermission):
    message = "Only DPA may access Certs settings."

    def has_permission(self, request, view) -> bool:
        if NOTIFICATION_CONFIG_FORM_ID not in _request_permission_ids(request, "form_ids"):
            return False
        return _normalized_role(getattr(request, "user", None)) in SETTINGS_WRITER_ROLES


class IsSettingsWriter(BasePermission):
    message = "Only DPA may modify Certs settings."

    def has_permission(self, request, view) -> bool:
        form_ids = _request_permission_ids(request, "form_ids")
        process_ids = _request_permission_ids(request, "process_ids")
        if NOTIFICATION_CONFIG_FORM_ID not in form_ids or CATALOG_EDIT_PROCESS_ID not in process_ids:
            return False
        return _normalized_role(getattr(request, "user", None)) in SETTINGS_WRITER_ROLES


class HasCertsProcessPermission(BasePermission):
    message = "You do not have access to this Certs action."
    required_process_ids: tuple[str, ...] = ()

    def __init__(self, *required_process_ids: str) -> None:
        if required_process_ids:
            self.required_process_ids = tuple(required_process_ids)

    @classmethod
    def requiring_all(cls, *process_ids: str):
        return type(
            f"{cls.__name__}_{'_'.join(process_ids)}",
            (cls,),
            {"required_process_ids": tuple(process_ids)},
        )

    def has_permission(self, request, view) -> bool:
        process_ids = _request_permission_ids(request, "process_ids")
        return all(process_id.upper() in process_ids for process_id in self.required_process_ids)


class IsCatalogWriter(BasePermission):
    message = "Only DPA or System Admin may modify the Certs catalog."

    def has_permission(self, request, view) -> bool:
        form_ids = _request_permission_ids(request, "form_ids")
        process_ids = _request_permission_ids(request, "process_ids")
        if CATALOG_FORM_ID not in form_ids or CATALOG_EDIT_PROCESS_ID not in process_ids:
            return False
        return _normalized_role(getattr(request, "user", None)) in CATALOG_WRITER_ROLES


class IsCatalogBulkActionWriter(BasePermission):
    message = "Only DPA or System Admin may run Certs catalog bulk actions."
    required_process_ids: tuple[str, ...] = (CATALOG_BULK_PROCESS_ID,)

    def has_permission(self, request, view) -> bool:
        form_ids = _request_permission_ids(request, "form_ids")
        process_ids = _request_permission_ids(request, "process_ids")
        if CATALOG_FORM_ID not in form_ids:
            return False
        if not all(process_id in process_ids for process_id in self.required_process_ids):
            return False
        return _normalized_role(getattr(request, "user", None)) in CATALOG_WRITER_ROLES


class IsCatalogHardPurgeWriter(IsCatalogBulkActionWriter):
    required_process_ids = (CATALOG_EDIT_PROCESS_ID, CATALOG_BULK_PROCESS_ID)


class IsTrackedItemWriter(BasePermission):
    message = "You do not have access to modify Certs tracked items."

    def has_permission(self, request, view) -> bool:
        form_ids = _request_permission_ids(request, "form_ids")
        process_ids = _request_permission_ids(request, "process_ids")
        return TRACKED_ITEM_FORM_ID in form_ids and TRACKED_ITEM_WRITE_PROCESS_ID in process_ids


def is_reconciliation_uploader(user) -> bool:
    return _normalized_role(user) in RECONCILIATION_UPLOAD_ROLES


def is_reconciliation_reviewer(user) -> bool:
    return _normalized_role(user) in RECONCILIATION_REVIEWER_ROLES


def is_reconciliation_mapping_writer(user) -> bool:
    return _normalized_role(user) in RECONCILIATION_MAPPING_WRITER_ROLES
