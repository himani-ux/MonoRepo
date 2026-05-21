from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CONFLICT_ROLES = {
    "MASTER",
    "CO",
    "CE",
    "C/O",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
}

OFFICE_SIDE_ROLES = {"DPA", "FM", "TD", "HOD-SHORE", "HOD_SHORE"}


@dataclass(frozen=True)
class SelfReportConflictResult:
    conflict_detected: bool
    message: str
    required_approver_role: str | None = None


def _normalize(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip().upper()


def _is_office_side(user) -> bool:
    work_side = _normalize(getattr(user, "work_side", None))
    if work_side == "OFFICE":
        return True

    role_name = _normalize(getattr(user, "safety_role_name", None) or getattr(user, "role_name", None) or getattr(user, "role", None))
    return role_name in OFFICE_SIDE_ROLES


def check_self_report_conflict(
    reporter_id,
    incident_data,
    *,
    user=None,
    reporter_rank=None,
) -> SelfReportConflictResult:
    normalized_reporter_id = _normalize(reporter_id)
    if not normalized_reporter_id:
        return SelfReportConflictResult(False, "")

    candidate_keys = ("injured_party_id", "pic_candidate_id", "pic_user_id", "person_in_charge_id")
    matching_keys = [
        key
        for key in candidate_keys
        if _normalize(incident_data.get(key)) == normalized_reporter_id
    ]

    normalized_rank = _normalize(reporter_rank or incident_data.get("reporter_rank"))
    if normalized_rank not in CONFLICT_ROLES or not matching_keys:
        return SelfReportConflictResult(False, "")

    required_approver_role = "DPA" if _is_office_side(user) else "MASTER"
    return SelfReportConflictResult(
        True,
        "Conflict detected - different approver required.",
        required_approver_role=required_approver_role,
    )
