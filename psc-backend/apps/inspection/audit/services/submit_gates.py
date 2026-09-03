"""Audit submit gates and acknowledgement transitions for Phase 4 Step 4.3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import (
    AuditAreaSummary,
    AuditDetail,
    AuditFinding,
    AuditMeetingAttendee,
)
from apps.inspection.audit.services.detail import REQUIRED_SCORECARD_ROW_COUNT, required_audit_area_codes


REPORT_OPEN_STATUS = "IN_PROGRESS"
REPORT_FINALIZED_STATUS = "REPORT_FINALIZED"
VESSEL_ACKNOWLEDGED_STATUS = "VESSEL_ACKNOWLEDGED"
SUMMARY_MIN_CHARS = 100


class AuditTransitionError(ValueError):
    """Raised when an Audit status transition is not legal."""


class AuditSubmitGateError(AuditTransitionError):
    """Raised when one or more D-071 submit gates fail."""

    def __init__(self, gates: dict[str, dict[str, str]]) -> None:
        super().__init__("Audit submit gates failed.")
        self.gates = gates


@dataclass(frozen=True)
class SubmitGateEvaluation:
    passed: bool
    gates: dict[str, dict[str, str]]


def evaluate_submit_gates(audit_detail: AuditDetail) -> SubmitGateEvaluation:
    gates: dict[str, dict[str, str]] = {}

    opening_errors = _meeting_errors(audit_detail, field_name="opening")
    if opening_errors:
        gates["opening_meeting"] = opening_errors

    closing_errors = _meeting_errors(audit_detail, field_name="closing")
    if closing_errors:
        gates["closing_meeting"] = closing_errors

    scorecard_errors = _scorecard_errors(audit_detail)
    if scorecard_errors:
        gates["scorecard"] = scorecard_errors

    summary_equipment_errors = _summary_equipment_errors(audit_detail)
    if summary_equipment_errors:
        gates["summary_equipment"] = summary_equipment_errors

    finding_errors = _finding_errors(audit_detail)
    if finding_errors:
        gates["findings"] = finding_errors

    return SubmitGateEvaluation(passed=not gates, gates=gates)


@transaction.atomic
def submit_audit_report(*, audit_detail: AuditDetail, user: object) -> AuditDetail:
    locked = AuditDetail.objects.select_for_update().get(id=audit_detail.id)
    if locked.status != REPORT_OPEN_STATUS:
        raise AuditTransitionError("Only IN_PROGRESS audits can be submitted.")

    evaluation = evaluate_submit_gates(locked)
    if not evaluation.passed:
        raise AuditSubmitGateError(evaluation.gates)

    locked.status = REPORT_FINALIZED_STATUS
    locked.updated_by = _user_id(user)
    locked.updated_date = timezone.now()
    locked.save(update_fields=["status", "updated_by", "updated_date"])
    return locked


@transaction.atomic
def acknowledge_audit_report(*, audit_detail: AuditDetail, user: object) -> AuditDetail:
    locked = AuditDetail.objects.select_for_update().get(id=audit_detail.id)
    if locked.status != REPORT_FINALIZED_STATUS:
        raise AuditTransitionError("Only REPORT_FINALIZED audits can be acknowledged.")

    locked.status = VESSEL_ACKNOWLEDGED_STATUS
    locked.updated_by = _user_id(user)
    locked.updated_date = timezone.now()
    locked.save(update_fields=["status", "updated_by", "updated_date"])
    return locked


def submit_gate_payload(audit_detail: AuditDetail) -> dict[str, Any]:
    evaluation = evaluate_submit_gates(audit_detail)
    return {
        "passed": evaluation.passed,
        "gates": evaluation.gates,
    }


def _meeting_errors(audit_detail: AuditDetail, *, field_name: str) -> dict[str, str]:
    errors: dict[str, str] = {}
    meeting_at = getattr(audit_detail, f"{field_name}_meeting_at")
    present_field = f"{field_name}_present"
    if not meeting_at:
        errors[f"{field_name}_meeting_at"] = f"{field_name.title()} meeting time is required."
    if not AuditMeetingAttendee.objects.filter(
        audit_detail_id=audit_detail.id,
        **{present_field: True},
    ).exists():
        errors[f"{field_name}_attendees"] = f"At least one {field_name} attendee is required."
    return errors


def _scorecard_errors(audit_detail: AuditDetail) -> dict[str, str]:
    required_codes = required_audit_area_codes()
    if len(required_codes) != REQUIRED_SCORECARD_ROW_COUNT:
        return {"area_count": "The 14 master audit areas must be available before submit."}

    populated_codes = set(
        AuditAreaSummary.objects.filter(
            audit_detail_id=audit_detail.id,
            area_code__in=required_codes,
        )
        .exclude(status__isnull=True)
        .exclude(status="")
        .values_list("area_code", flat=True)
    )
    missing_codes = sorted(required_codes - populated_codes)
    if missing_codes:
        return {"missing_rows": f"Populate all 14 scorecard rows before submit: {', '.join(missing_codes)}."}
    return {}


def _summary_equipment_errors(audit_detail: AuditDetail) -> dict[str, str]:
    errors: dict[str, str] = {}
    audit_summary = (audit_detail.audit_summary or "").strip()
    equipment_tested = (audit_detail.equipment_tested or "").strip()
    if len(audit_summary) < SUMMARY_MIN_CHARS:
        errors["audit_summary"] = "Audit summary must be at least 100 characters before submit."
    if not equipment_tested:
        errors["equipment_tested"] = "Equipment tested must contain at least one non-empty line."
    return errors


def _finding_errors(audit_detail: AuditDetail) -> dict[str, str]:
    missing_evidence_count = sum(
        1
        for evidence in AuditFinding.objects.filter(audit_detail_id=audit_detail.id)
        .values_list("objective_evidence", flat=True)
        if not (evidence or "").strip()
    )
    if missing_evidence_count:
        return {
            "objective_evidence": (
                f"{missing_evidence_count} finding(s) must record objective evidence before submit."
            )
        }
    return {}


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")
