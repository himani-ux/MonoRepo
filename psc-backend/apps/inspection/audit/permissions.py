from __future__ import annotations

from collections.abc import Iterable
import json
from uuid import UUID

from rest_framework.permissions import BasePermission


AUDIT_P_001 = "AUDIT_P_001"
AUDIT_P_002 = "AUDIT_P_002"
AUDIT_P_003 = "AUDIT_P_003"
AUDIT_P_004 = "AUDIT_P_004"
AUDIT_P_005 = "AUDIT_P_005"
AUDIT_P_006 = "AUDIT_P_006"
AUDIT_P_007 = "AUDIT_P_007"
AUDIT_P_008 = "AUDIT_P_008"
AUDIT_P_009 = "AUDIT_P_009"
AUDIT_P_010 = "AUDIT_P_010"
AUDIT_P_011 = "AUDIT_P_011"
AUDIT_P_012 = "AUDIT_P_012"
AUDIT_P_013 = "AUDIT_P_013"
AUDIT_P_014 = "AUDIT_P_014"
AUDIT_P_016 = "AUDIT_P_016"
AUDIT_P_017 = "AUDIT_P_017"
AUDIT_P_018 = "AUDIT_P_018"
AUDIT_P_019 = "AUDIT_P_019"
AUDIT_P_020 = "AUDIT_P_020"

AUDIT_GATE_IDS = (
    AUDIT_P_001,
    AUDIT_P_002,
    AUDIT_P_003,
    AUDIT_P_004,
    AUDIT_P_005,
    AUDIT_P_006,
    AUDIT_P_007,
    AUDIT_P_008,
    AUDIT_P_009,
    AUDIT_P_010,
    AUDIT_P_011,
    AUDIT_P_012,
    AUDIT_P_013,
    AUDIT_P_014,
    AUDIT_P_016,
    AUDIT_P_017,
    AUDIT_P_018,
    AUDIT_P_019,
    AUDIT_P_020,
)
AUDIT_GATE_SET = frozenset(AUDIT_GATE_IDS)

SEQ_MANAGER_GATES = frozenset(
    {
        AUDIT_P_001,
        AUDIT_P_005,
        AUDIT_P_006,
        AUDIT_P_009,
        AUDIT_P_010,
        AUDIT_P_011,
        AUDIT_P_012,
        AUDIT_P_019,
        AUDIT_P_020,
    }
)
DPA_GATES = frozenset(
    {
        AUDIT_P_001,
        AUDIT_P_005,
        AUDIT_P_006,
        AUDIT_P_007,
        AUDIT_P_013,
        AUDIT_P_014,
        AUDIT_P_016,
        AUDIT_P_018,
    }
)
LEAD_AUDITOR_GATES = frozenset({AUDIT_P_002, AUDIT_P_003, AUDIT_P_004})
CONDUCTOR_GATES = frozenset({AUDIT_P_003})
OFFICE_PIC_GATES = frozenset({AUDIT_P_004, AUDIT_P_007})
FLEET_MANAGER_GATES = frozenset({AUDIT_P_016})
MASTER_GATES = frozenset({AUDIT_P_008, AUDIT_P_017})
HOD_GATES = frozenset({AUDIT_P_008})

DEFAULT_AUDIT_GATES_BY_DESIGNATION = {
    "OFFICE_SSQE": SEQ_MANAGER_GATES,
    "SEQ_MANAGER": SEQ_MANAGER_GATES,
    "DPA": DPA_GATES,
    "OFFICE_PIC": OFFICE_PIC_GATES,
    "OFFICE_SUPT": OFFICE_PIC_GATES,
    "PIC": OFFICE_PIC_GATES,
    "FM": FLEET_MANAGER_GATES,
    "FLEET_MANAGER": FLEET_MANAGER_GATES,
    "VESSEL_MASTER": MASTER_GATES,
    "MASTER": MASTER_GATES,
}

AUDIT_CAR_WORKFLOW_ACTION_GATES = {
    "DRAFT_FOR_VESSEL": (AUDIT_P_003,),
    "SUBMIT_TO_PIC": (AUDIT_P_008, AUDIT_P_017),
    "START_PIC_REVIEW": (AUDIT_P_004,),
    "SUBMIT_TO_LEAD_AUDITOR": (AUDIT_P_004,),
    "LEAD_AUDITOR_CLOSE": (AUDIT_P_004,),
    "AWAIT_EXTERNAL_CLOSE_OUT": (AUDIT_P_004,),
    "CONFIRM_EXTERNAL_CLOSE": (AUDIT_P_013,),
    "REQUEST_REWORK": (AUDIT_P_004, AUDIT_P_013),
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


def _normalize_token(value: object) -> str:
    text = str(value or "").strip().upper()
    normalized = []
    previous_was_sep = False
    for char in text:
        if char.isalnum():
            normalized.append(char)
            previous_was_sep = False
            continue
        if not previous_was_sep:
            normalized.append("_")
            previous_was_sep = True
    return "".join(normalized).strip("_")


def _normalize_identifier(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return UUID(text).hex
    except (TypeError, ValueError, AttributeError):
        return text.lower()


def _iter_scope_ids(value: object) -> list[str]:
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
                return _iter_scope_ids(parsed)
        return [part.strip() for part in stripped.split(",") if part.strip()]
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _same_identifier(left: object, right: object) -> bool:
    return bool(_normalize_identifier(left)) and _normalize_identifier(left) == _normalize_identifier(right)


def audit_process_ids_for_user(user) -> set[str]:
    explicit_gates = _normalize_permission_ids(getattr(user, "process_ids", None))
    return (explicit_gates | default_audit_gates_for_user(user)) & AUDIT_GATE_SET


def audit_process_ids_for_request(request) -> set[str]:
    user = getattr(request, "user", None)
    return (_request_permission_ids(request, "process_ids") | default_audit_gates_for_user(user)) & AUDIT_GATE_SET


def has_audit_process_id(user, process_id: str) -> bool:
    return process_id.strip().upper() in audit_process_ids_for_user(user)


def has_request_audit_process_id(request, process_id: str) -> bool:
    return process_id.strip().upper() in audit_process_ids_for_request(request)


def has_any_audit_process_id(user) -> bool:
    return bool(audit_process_ids_for_user(user))


def default_audit_gates_for_designation(designation: object) -> frozenset[str]:
    return DEFAULT_AUDIT_GATES_BY_DESIGNATION.get(_normalize_token(designation), frozenset())


def default_audit_gates_for_user(user) -> frozenset[str]:
    if user is None:
        return frozenset()
    values = [
        getattr(user, "audit_designation", None),
        getattr(user, "designation", None),
        getattr(user, "role", None),
        getattr(user, "role_name", None),
        getattr(user, "safety_role_name", None),
        getattr(user, "employee_role", None),
        getattr(user, "profile_name", None),
        getattr(user, "rank", None),
    ]
    gates: set[str] = set()
    for value in values:
        gates.update(default_audit_gates_for_designation(value))
    return frozenset(gates)


def normalized_audit_role(user) -> str:
    for attr_name in ("audit_designation", "designation", "role", "role_name", "employee_role", "rank"):
        value = _normalize_token(getattr(user, attr_name, None))
        if value:
            return value
    return ""


def _user_type(user) -> str:
    return _normalize_token(getattr(user, "user_type", None))


def _user_identity(user) -> str:
    for attr_name in ("id", "user_id", "employee_id", "login_id", "username", "crew_id"):
        value = str(getattr(user, attr_name, "") or "").strip()
        if value:
            return value
    return ""


def _user_identity_values(user) -> list[str]:
    values: list[str] = []
    for attr_name in ("id", "user_id", "employee_id", "login_id", "username", "crew_id"):
        value = str(getattr(user, attr_name, "") or "").strip()
        if value and value not in values:
            values.append(value)
    return values


def user_identity_matches(user, target_user_id: object) -> bool:
    return any(_same_identifier(value, target_user_id) for value in _user_identity_values(user))


def is_office_user(user) -> bool:
    return _user_type(user) == "OFFICE"


def is_vessel_user(user) -> bool:
    return _user_type(user) == "VESSEL"


def is_fleet_manager(user) -> bool:
    return normalized_audit_role(user) in {"FM", "FLEET_MANAGER"}


def is_audit_lead_auditor(user, audit_detail) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return user_identity_matches(user, getattr(audit_detail, "lead_auditor_user_id", None))


def is_audit_conductor(user, audit_detail) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return user_identity_matches(user, getattr(audit_detail, "conductor_user_id", None))


def _active_hod_user_id_for_dept(office_dept: object, *, today=None) -> str:
    dept = str(office_dept or "").strip().upper()
    if not dept:
        return ""
    try:
        from django.db import DatabaseError
        from django.db.models import Q
        from django.utils import timezone

        from apps.inspection.audit.models import MasterHodAssignment

        current_date = today or timezone.localdate()
        queryset = MasterHodAssignment.objects.filter(
            dept=dept,
            effective_from__lte=current_date,
        ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=current_date))
        confirmed = queryset.filter(is_acting=False).order_by("-effective_from", "-created_date").first()
        assignment = confirmed or queryset.filter(is_acting=True).order_by("-effective_from", "-created_date").first()
    except (DatabaseError, RuntimeError, LookupError, ImportError):
        return ""
    return str(getattr(assignment, "user_id", "") or "") if assignment is not None else ""


def is_audit_hod(user, audit_detail, *, today=None) -> bool:
    if not getattr(user, "is_authenticated", False) or not is_office_user(user):
        return False
    if _normalize_token(getattr(audit_detail, "auditee_type", None)) != "OFFICE_DEPT":
        return False
    hod_user_id = _active_hod_user_id_for_dept(getattr(audit_detail, "auditee_office_dept", None), today=today)
    return user_identity_matches(user, hod_user_id)


def audit_assignment_process_ids_for_user(user, audit_detail, *, today=None) -> set[str]:
    if audit_detail is None or not getattr(user, "is_authenticated", False):
        return set()

    process_ids: set[str] = set()
    if is_audit_lead_auditor(user, audit_detail):
        process_ids.update(LEAD_AUDITOR_GATES)
    if is_audit_conductor(user, audit_detail):
        process_ids.update(CONDUCTOR_GATES)
    if is_audit_hod(user, audit_detail, today=today):
        process_ids.update(HOD_GATES)
    return process_ids & AUDIT_GATE_SET


def audit_effective_process_ids_for_user(user, audit_detail, *, today=None) -> set[str]:
    return (audit_process_ids_for_user(user) | audit_assignment_process_ids_for_user(user, audit_detail, today=today)) & AUDIT_GATE_SET


def audit_effective_process_ids_for_request(request, audit_detail, *, today=None) -> set[str]:
    return (
        audit_process_ids_for_request(request)
        | audit_assignment_process_ids_for_user(getattr(request, "user", None), audit_detail, today=today)
    ) & AUDIT_GATE_SET


def has_audit_detail_process_id(user, audit_detail, process_id: str, *, today=None) -> bool:
    return process_id.strip().upper() in audit_effective_process_ids_for_user(user, audit_detail, today=today)


def request_has_audit_detail_process_id(request, audit_detail, process_id: str, *, today=None) -> bool:
    return process_id.strip().upper() in audit_effective_process_ids_for_request(request, audit_detail, today=today)


def user_has_vessel_scope(user, vessel_id: object) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if not _normalize_identifier(vessel_id):
        return False

    if is_vessel_user(user):
        return _same_identifier(getattr(user, "vessel_id", None), vessel_id)

    if not is_office_user(user):
        return False

    if getattr(user, "has_global_vessel_access", None) is True:
        return True
    if normalized_audit_role(user) == "DPA":
        return True

    explicit_scope = _iter_scope_ids(getattr(user, "vessel_ids", None))
    if explicit_scope:
        return any(_same_identifier(scope_id, vessel_id) for scope_id in explicit_scope)

    try:
        from core.vessel_access import (
            get_office_user_identifiers,
            get_office_user_vessel_ids,
            has_global_office_vessel_access,
        )

        identifiers = get_office_user_identifiers(user)
        if has_global_office_vessel_access(user, user_identifiers=identifiers):
            return True
        mapped_vessel_ids = get_office_user_vessel_ids(identifiers)
    except Exception:
        return False

    if mapped_vessel_ids is None:
        return False
    return any(_same_identifier(mapped_vessel_id, vessel_id) for mapped_vessel_id in mapped_vessel_ids)


def user_can_access_audit_detail(user, audit_detail) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if audit_assignment_process_ids_for_user(user, audit_detail):
        return True

    auditee_type = _normalize_token(getattr(audit_detail, "auditee_type", None))
    if not has_any_audit_process_id(user):
        return False
    if auditee_type == "OFFICE_DEPT":
        return is_office_user(user)

    return user_has_vessel_scope(user, getattr(audit_detail, "vessel_id", None))


def can_authorize_acting_hod(user, target_user_id: object) -> bool:
    if not has_audit_process_id(user, AUDIT_P_016):
        return False
    if not (normalized_audit_role(user) == "DPA" or is_fleet_manager(user)):
        return False
    return not _same_identifier(_user_identity(user), target_user_id)


def audit_car_workflow_required_gates(action: object) -> tuple[str, ...]:
    return AUDIT_CAR_WORKFLOW_ACTION_GATES.get(_normalize_token(action), (AUDIT_P_004,))


class HasAuditProcessPermission(BasePermission):
    message = "You do not have the required Audit permission."
    required_process_ids: tuple[str, ...] = ()

    def __init__(self, *required_process_ids: str) -> None:
        if required_process_ids:
            self.required_process_ids = tuple(required_process_ids)

    @classmethod
    def requiring(cls, *process_ids: str):
        normalized = tuple(process_id.strip().upper() for process_id in process_ids if process_id.strip())
        return type(
            f"{cls.__name__}_{'_'.join(normalized)}",
            (cls,),
            {"required_process_ids": normalized},
        )

    def has_permission(self, request, view) -> bool:
        if not self.required_process_ids:
            return True
        request_process_ids = audit_process_ids_for_request(request)
        return all(process_id in request_process_ids for process_id in self.required_process_ids)


class HasAnyAuditProcessPermission(BasePermission):
    message = "You do not have the required Audit permission."
    required_process_ids: tuple[str, ...] = ()

    def __init__(self, *required_process_ids: str) -> None:
        if required_process_ids:
            self.required_process_ids = tuple(required_process_ids)

    @classmethod
    def requiring_any(cls, *process_ids: str):
        normalized = tuple(process_id.strip().upper() for process_id in process_ids if process_id.strip())
        return type(
            f"{cls.__name__}_{'_'.join(normalized)}",
            (cls,),
            {"required_process_ids": normalized},
        )

    def has_permission(self, request, view) -> bool:
        if not self.required_process_ids:
            return True
        request_process_ids = audit_process_ids_for_request(request)
        return any(process_id in request_process_ids for process_id in self.required_process_ids)


class CanUseAuditCarWorkflow(BasePermission):
    message = "You do not have permission to perform this Audit CAR workflow action."

    def has_permission(self, request, view) -> bool:
        action = getattr(request, "data", {}).get("action")
        required_process_ids = audit_car_workflow_required_gates(action)
        request_process_ids = audit_process_ids_for_request(request)
        if any(process_id in request_process_ids for process_id in required_process_ids):
            return True

        finding_id = getattr(view, "kwargs", {}).get("id")
        if not finding_id:
            return False
        try:
            from apps.inspection.audit.services.car_workflow import resolve_audit_car_workflow_context

            context = resolve_audit_car_workflow_context(finding_id)
        except Exception:
            return False
        effective_process_ids = audit_effective_process_ids_for_request(request, context.audit_detail)
        return any(process_id in effective_process_ids for process_id in required_process_ids)


CanCreateAudit = HasAuditProcessPermission.requiring(AUDIT_P_001)
CanEditAudit = HasAuditProcessPermission.requiring(AUDIT_P_002)
CanConductAudit = HasAuditProcessPermission.requiring(AUDIT_P_003)
CanCloseAuditNC = HasAuditProcessPermission.requiring(AUDIT_P_004)
CanApproveAuditExtension = HasAuditProcessPermission.requiring(AUDIT_P_005)
CanCancelAudit = HasAuditProcessPermission.requiring(AUDIT_P_006)
CanIssueCircularFromAuditNC = HasAuditProcessPermission.requiring(AUDIT_P_007)
CanSignAuditClosingMeeting = HasAuditProcessPermission.requiring(AUDIT_P_008)
CanManageQualifiedAuditors = HasAuditProcessPermission.requiring(AUDIT_P_009)
CanManageHodAssignment = HasAuditProcessPermission.requiring(AUDIT_P_010)
CanManageAuditSlackChannels = HasAuditProcessPermission.requiring(AUDIT_P_011)
CanManageAuditRcaTemplates = HasAuditProcessPermission.requiring(AUDIT_P_012)
CanRegisterExternalAudit = HasAuditProcessPermission.requiring(AUDIT_P_013)
CanWriteBackAuditCerts = HasAuditProcessPermission.requiring(AUDIT_P_014)
CanAuthorizeActingHod = HasAuditProcessPermission.requiring(AUDIT_P_016)
CanAcknowledgeAuditReport = HasAuditProcessPermission.requiring(AUDIT_P_017)
CanValidateAuditScan = HasAuditProcessPermission.requiring(AUDIT_P_018)
CanManageExternalAuditOrgs = HasAuditProcessPermission.requiring(AUDIT_P_019)
CanManageVesselRoDelegations = HasAuditProcessPermission.requiring(AUDIT_P_020)

__all__ = [
    "AUDIT_GATE_IDS",
    "AUDIT_GATE_SET",
    "AUDIT_P_001",
    "AUDIT_P_002",
    "AUDIT_P_003",
    "AUDIT_P_004",
    "AUDIT_P_005",
    "AUDIT_P_006",
    "AUDIT_P_007",
    "AUDIT_P_008",
    "AUDIT_P_009",
    "AUDIT_P_010",
    "AUDIT_P_011",
    "AUDIT_P_012",
    "AUDIT_P_013",
    "AUDIT_P_014",
    "AUDIT_P_016",
    "AUDIT_P_017",
    "AUDIT_P_018",
    "AUDIT_P_019",
    "AUDIT_P_020",
    "CanAcknowledgeAuditReport",
    "CanApproveAuditExtension",
    "CanAuthorizeActingHod",
    "CanCancelAudit",
    "CanCloseAuditNC",
    "CanConductAudit",
    "CanCreateAudit",
    "CanEditAudit",
    "CanIssueCircularFromAuditNC",
    "CanManageAuditRcaTemplates",
    "CanManageAuditSlackChannels",
    "CanManageHodAssignment",
    "CanManageQualifiedAuditors",
    "CanManageExternalAuditOrgs",
    "CanManageVesselRoDelegations",
    "CanRegisterExternalAudit",
    "CanUseAuditCarWorkflow",
    "CanValidateAuditScan",
    "CanWriteBackAuditCerts",
    "DEFAULT_AUDIT_GATES_BY_DESIGNATION",
    "HasAnyAuditProcessPermission",
    "HasAuditProcessPermission",
    "audit_assignment_process_ids_for_user",
    "audit_car_workflow_required_gates",
    "audit_effective_process_ids_for_request",
    "audit_effective_process_ids_for_user",
    "audit_process_ids_for_request",
    "audit_process_ids_for_user",
    "can_authorize_acting_hod",
    "default_audit_gates_for_designation",
    "default_audit_gates_for_user",
    "has_audit_detail_process_id",
    "has_any_audit_process_id",
    "has_audit_process_id",
    "has_request_audit_process_id",
    "is_audit_conductor",
    "is_audit_hod",
    "is_audit_lead_auditor",
    "is_fleet_manager",
    "is_office_user",
    "is_vessel_user",
    "normalized_audit_role",
    "request_has_audit_detail_process_id",
    "user_identity_matches",
    "user_can_access_audit_detail",
    "user_has_vessel_scope",
]
