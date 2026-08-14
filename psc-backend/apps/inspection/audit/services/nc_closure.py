"""KSM-F-NC-001 closure persistence for Audit NC findings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import AuditDetail, AuditFinding, AuditFindingNC
from apps.inspection.audit.services.car_workflow import (
    AuditCarWorkflowContext,
    AuditCarWorkflowError,
    resolve_audit_car_workflow_context,
)
from apps.inspection.deficiency_models import CAR, CARStatus, Deficiency
from apps.inspection.models import Inspection
from apps.inspection.workflow import WorkflowAction, validate_workflow_transition


RCA_METHODS = {"FIVE_WHY", "FISHBONE_ISHIKAWA", "STRUCTURED_NARRATIVE", "OTHER"}
ROOT_CAUSE_CATEGORIES = {
    "PROCEDURAL_GAP",
    "TRAINING_GAP",
    "SUPERVISION_FAILURE",
    "COMMUNICATION_FAILURE",
    "EQUIPMENT_FAILURE",
    "HUMAN_ERROR",
    "MANAGEMENT_SYSTEM_FAILURE",
    "OTHER",
}
CERTIFICATES_AT_RISK = {"DOC", "SMC", "ISSC", "MLC_DMLC", "NONE"}
OFFICE_CERTIFICATES_AT_RISK = {"DOC", "NONE"}
EFFECTIVENESS_REVIEW_METHODS = {
    "VESSEL_FOLLOWUP_INSPECTION",
    "REVIEW_SUBSEQUENT_AUDIT",
    "OFFICE_DOC_REVIEW",
    "MASTERS_REPORT",
}
EFFECTIVENESS_OUTCOMES = {"EFFECTIVE", "PARTIALLY_EFFECTIVE", "NOT_EFFECTIVE"}
ACCEPTANCE_DECISIONS = {"ACCEPTED", "RETURNED"}
VERIFICATION_METHODS = {
    "DOCUMENT_REVIEW",
    "ONBOARD_VERIFICATION",
    "PSC_AUTHORITY_CLEARANCE",
    "NEXT_PERIODIC_SURVEY",
}
CERTIFICATE_ENDORSEMENT_TYPES = {"DOC", "SMC", "ISSC", "MLC_DMLC", "NONE"}
FINAL_CLOSURE_STATUSES = {"CLOSED", "CONDITIONALLY_CLOSED", "NOT_CLOSED"}


class AuditNcClosureError(ValueError):
    """Raised when an NC closure request violates the KSM-F-NC-001 contract."""


@dataclass(frozen=True)
class AuditNcClosureBundle:
    finding: AuditFinding
    audit_detail: AuditDetail
    inspection: Inspection
    deficiency: Deficiency
    car: CAR
    nc: AuditFindingNC


def get_nc_closure_bundle(finding_id: UUID | str, *, user: object | None = None) -> AuditNcClosureBundle:
    context = resolve_audit_car_workflow_context(finding_id)
    nc = _ensure_nc_record(context, user=user)
    return _bundle(context=context, nc=nc)


@transaction.atomic
def update_nc_part(
    *,
    finding_id: UUID | str,
    part: str,
    data: dict[str, Any],
    user: object,
) -> AuditNcClosureBundle:
    context = resolve_audit_car_workflow_context(finding_id)
    nc = _ensure_nc_record(context, user=user)
    actor_id = _user_id(user)
    part = part.lower()

    if part == "part-b":
        _update_part_b(context=context, nc=nc, data=data)
    elif part == "part-c":
        _update_part_c(nc=nc, data=data)
    elif part == "part-d":
        _update_part_d(nc=nc, data=data)
    elif part == "part-e":
        _update_certificates_at_risk(context=context, data=data)
        _update_part_e(context=context, nc=nc, data=data, user=user)
    elif part == "part-f":
        _update_certificates_at_risk(context=context, data=data)
        _update_part_f(nc=nc, data=data)
    elif part == "part-g":
        _update_part_g(nc=nc, data=data)
    else:
        raise AuditNcClosureError("Unknown NC closure part.")

    nc.updated_by = actor_id
    nc.updated_date = timezone.now()
    nc.save()
    context.finding.refresh_from_db()
    return _bundle(context=context, nc=nc)


@transaction.atomic
def draft_nc_for_vessel(
    *,
    finding_id: UUID | str,
    data: dict[str, Any],
    user: object,
) -> AuditNcClosureBundle:
    context = resolve_audit_car_workflow_context(finding_id)
    nc = _ensure_nc_record(context, user=user)
    actor_id = _user_id(user)

    _update_part_b(context=context, nc=nc, data=data)
    _update_part_c(nc=nc, data=data)
    nc.drafted_by_user_id = actor_id
    nc.updated_by = actor_id
    nc.updated_date = timezone.now()
    nc.save()

    if context.car.status != CARStatus.OFFICE_DRAFTED:
        transition, error = validate_workflow_transition(
            context.car,
            WorkflowAction.DRAFT_FOR_VESSEL,
            user,
            data.get("comment") or "",
        )
        if error:
            raise AuditNcClosureError(error)
        _apply_car_transition(
            car=context.car,
            action=WorkflowAction.DRAFT_FOR_VESSEL,
            target_status=transition["target"],
            user=user,
            comment=data.get("comment") or "",
        )

    context.car.refresh_from_db()
    return _bundle(context=context, nc=nc)


@transaction.atomic
def schedule_effectiveness_review(
    *,
    finding_id: UUID | str,
    user: object | None = None,
    closed_at=None,
) -> AuditNcClosureBundle:
    context = resolve_audit_car_workflow_context(finding_id)
    nc = _ensure_nc_record(context, user=user)
    base_date = timezone.localtime(closed_at).date() if closed_at else timezone.localdate()
    due_date = base_date + timedelta(days=30)

    update_fields = ["updated_by", "updated_date"]
    if nc.effectiveness_review_date is None:
        nc.effectiveness_review_date = due_date
        update_fields.append("effectiveness_review_date")
    if nc.effectiveness_overdue:
        nc.effectiveness_overdue = False
        update_fields.append("effectiveness_overdue")
    nc.updated_by = _user_id(user)
    nc.updated_date = timezone.now()
    nc.save(update_fields=update_fields)
    return _bundle(context=context, nc=nc)


def serialize_nc_closure_bundle(bundle: AuditNcClosureBundle) -> dict[str, Any]:
    finding = bundle.finding
    audit_detail = bundle.audit_detail
    inspection = bundle.inspection
    deficiency = bundle.deficiency
    car = bundle.car
    nc = bundle.nc
    return {
        "id": str(nc.id),
        "finding_id": str(finding.id),
        "audit_detail_id": str(audit_detail.id),
        "car": {
            "id": str(car.id),
            "car_number": car.car_number,
            "status": car.status,
            "target_date": _date_value(car.target_date),
        },
        "part_a": {
            "nc_reference_no": car.car_number,
            "audit_date": _date_value(inspection.inspection_date),
            "vessel_id": str(inspection.vessel_id),
            "port_place": inspection.port_place or "",
            "auditor_name": audit_detail.lead_auditor_name,
            "auditor_organisation": audit_detail.lead_auditor_company,
            "rule_book_type": finding.rule_book_type,
            "clause_ref_text": finding.clause_ref_text,
            "objective_evidence": finding.objective_evidence or "",
            "nc_issued_date": _date_value(getattr(finding, "created_date", None)),
            "required_closure_deadline": _date_value(finding.original_due_date or deficiency.target_date),
            "certificates_at_risk": finding.certificates_at_risk or "",
            "nc_classification": finding.nc_category,
            "description": finding.description or deficiency.description,
        },
        "part_b": {
            "immediate_action_text": nc.immediate_action_text or "",
            "immediate_action_completed_at": _date_value(nc.immediate_action_completed_at),
            "master_immediate_sign_name": nc.master_immediate_sign_name or "",
            "master_immediate_sign_at": _datetime_value(nc.master_immediate_sign_at),
            "drafted_by_user_id": nc.drafted_by_user_id or "",
        },
        "part_c": {
            "rca_method": nc.rca_method or "",
            "rca_method_other": nc.rca_method_other or "",
            "rca_template_id": str(nc.rca_template_id) if nc.rca_template_id else None,
            "problem_statement": nc.problem_statement or "",
            "why_1": nc.why_1 or "",
            "why_2": nc.why_2 or "",
            "why_3": nc.why_3 or "",
            "why_4": nc.why_4 or "",
            "why_5": nc.why_5 or "",
            "root_cause_categories": _csv_to_list(nc.root_cause_categories),
            "root_cause_summary": nc.root_cause_summary or "",
        },
        "part_d": {
            "corrective_action_text": nc.corrective_action_text or "",
            "target_completion_date": _date_value(nc.target_completion_date),
            "actual_completion_date": _date_value(nc.actual_completion_date),
            "preventive_action_text": nc.preventive_action_text or "",
            "sms_amendment_required": nc.sms_amendment_required,
            "sms_amendment_doc_ref": nc.sms_amendment_doc_ref or "",
        },
        "part_e": {
            "effectiveness_review_date": _date_value(nc.effectiveness_review_date),
            "effectiveness_review_method": nc.effectiveness_review_method or "",
            "effectiveness_assessment_text": nc.effectiveness_assessment_text or "",
            "effectiveness_outcome": nc.effectiveness_outcome or "",
            "effectiveness_further_action_text": nc.effectiveness_further_action_text or "",
            "effectiveness_signer_name": nc.effectiveness_signer_name or "",
            "effectiveness_signer_at": _datetime_value(nc.effectiveness_signer_at),
            "effectiveness_overdue": nc.effectiveness_overdue,
        },
        "part_f": {
            "acceptance_review_date": _date_value(nc.acceptance_review_date),
            "acceptance_rca_adequacy_text": nc.acceptance_rca_adequacy_text or "",
            "acceptance_decision": nc.acceptance_decision or "",
            "acceptance_return_reason": nc.acceptance_return_reason or "",
            "acceptance_signer_name": nc.acceptance_signer_name or "",
            "acceptance_signer_at": _datetime_value(nc.acceptance_signer_at),
        },
        "part_g": {
            "verifying_auditor_name": nc.verifying_auditor_name or "",
            "verifying_authority_org": nc.verifying_authority_org or "",
            "verification_method": nc.verification_method or "",
            "certificate_endorsement_type": nc.certificate_endorsement_type or "",
            "certificate_endorsement_ref": nc.certificate_endorsement_ref or "",
            "auditor_assessment_text": nc.auditor_assessment_text or "",
            "final_closure_status": nc.final_closure_status or "",
            "resubmit_by_date": _date_value(nc.resubmit_by_date),
            "auditor_verification_sign_at": _datetime_value(nc.auditor_verification_sign_at),
        },
    }


def _ensure_nc_record(context: AuditCarWorkflowContext, *, user: object | None) -> AuditFindingNC:
    nc, _created = AuditFindingNC.objects.get_or_create(
        audit_finding_id=context.finding.id,
        defaults={"created_by": _user_id(user)},
    )
    return nc


def _bundle(*, context: AuditCarWorkflowContext, nc: AuditFindingNC) -> AuditNcClosureBundle:
    return AuditNcClosureBundle(
        finding=context.finding,
        audit_detail=context.audit_detail,
        inspection=context.deficiency.inspection,
        deficiency=context.deficiency,
        car=context.car,
        nc=nc,
    )


def _update_part_b(*, context: AuditCarWorkflowContext, nc: AuditFindingNC, data: dict[str, Any]) -> None:
    text = _clean(data.get("immediate_action_text"))
    completed_at = data.get("immediate_action_completed_at")
    if context.finding.nc_category == "MAJOR_NC":
        if completed_at is not None:
            if not text:
                raise AuditNcClosureError("Part B immediate action is required for Major NC.")
            issued_date = timezone.localtime(context.finding.created_date).date()
            if completed_at > issued_date + timedelta(hours=72):
                raise AuditNcClosureError("Part B immediate action for Major NC must be completed within 72 hours.")

    nc.immediate_action_text = text
    nc.immediate_action_completed_at = completed_at
    nc.master_immediate_sign_name = _clean(data.get("master_immediate_sign_name"))
    nc.master_immediate_sign_at = data.get("master_immediate_sign_at")


def _update_part_c(*, nc: AuditFindingNC, data: dict[str, Any]) -> None:
    rca_method = _choice_or_blank(data.get("rca_method"), RCA_METHODS, "rca_method")
    categories = data.get("root_cause_categories") or []
    unknown = sorted(set(categories) - ROOT_CAUSE_CATEGORIES)
    if unknown:
        raise AuditNcClosureError(f"Unknown root cause categories: {', '.join(unknown)}.")
    summary = _clean(data.get("root_cause_summary"))
    if summary and len(summary) < 50:
        raise AuditNcClosureError("root_cause_summary must be at least 50 characters.")
    if rca_method == "OTHER" and not _clean(data.get("rca_method_other")):
        raise AuditNcClosureError("rca_method_other is required when rca_method is OTHER.")

    nc.rca_method = rca_method
    nc.rca_method_other = _clean(data.get("rca_method_other"))
    nc.rca_template_id = data.get("rca_template_id")
    nc.problem_statement = _clean(data.get("problem_statement"))
    nc.why_1 = _clean(data.get("why_1"))
    nc.why_2 = _clean(data.get("why_2"))
    nc.why_3 = _clean(data.get("why_3"))
    nc.why_4 = _clean(data.get("why_4"))
    nc.why_5 = _clean(data.get("why_5"))
    nc.root_cause_categories = ",".join(categories) if categories else None
    nc.root_cause_summary = summary


def _update_part_d(*, nc: AuditFindingNC, data: dict[str, Any]) -> None:
    nc.corrective_action_text = _clean(data.get("corrective_action_text"))
    nc.target_completion_date = data.get("target_completion_date")
    nc.actual_completion_date = data.get("actual_completion_date")
    nc.preventive_action_text = _clean(data.get("preventive_action_text"))
    nc.sms_amendment_required = bool(data.get("sms_amendment_required"))
    nc.sms_amendment_doc_ref = _clean(data.get("sms_amendment_doc_ref"))
    if nc.sms_amendment_required and not nc.sms_amendment_doc_ref:
        raise AuditNcClosureError("sms_amendment_doc_ref is required when SMS amendment is required.")


def _update_part_e(*, context: AuditCarWorkflowContext, nc: AuditFindingNC, data: dict[str, Any], user: object) -> None:
    outcome = _choice_or_blank(data.get("effectiveness_outcome"), EFFECTIVENESS_OUTCOMES, "effectiveness_outcome")
    further_action = _clean(data.get("effectiveness_further_action_text"))
    if outcome and outcome != "EFFECTIVE" and len(further_action) < 50:
        raise AuditNcClosureError("effectiveness_further_action_text must be at least 50 characters when outcome is not EFFECTIVE.")

    nc.effectiveness_review_date = data.get("effectiveness_review_date")
    nc.effectiveness_review_method = _choice_or_blank(
        data.get("effectiveness_review_method"),
        EFFECTIVENESS_REVIEW_METHODS,
        "effectiveness_review_method",
    )
    nc.effectiveness_assessment_text = _clean(data.get("effectiveness_assessment_text"))
    nc.effectiveness_outcome = outcome
    nc.effectiveness_further_action_text = further_action
    nc.effectiveness_signer_name = _clean(data.get("effectiveness_signer_name"))
    nc.effectiveness_signer_at = data.get("effectiveness_signer_at")

    if outcome == "NOT_EFFECTIVE" and context.car.status == CARStatus.LEAD_AUDITOR_CLOSED:
        _apply_car_transition(
            car=context.car,
            action=WorkflowAction.REQUEST_REWORK,
            target_status=CARStatus.PENDING_MASTER_REVIEW,
            user=user,
            comment=further_action or "Effectiveness review found the corrective action was not effective.",
        )


def _update_part_f(*, nc: AuditFindingNC, data: dict[str, Any]) -> None:
    decision = _choice_or_blank(data.get("acceptance_decision"), ACCEPTANCE_DECISIONS, "acceptance_decision")
    return_reason = _clean(data.get("acceptance_return_reason"))
    if decision == "RETURNED" and len(return_reason) < 20:
        raise AuditNcClosureError("acceptance_return_reason must be at least 20 characters when closure is returned.")

    nc.acceptance_review_date = data.get("acceptance_review_date")
    nc.acceptance_rca_adequacy_text = _clean(data.get("acceptance_rca_adequacy_text"))
    nc.acceptance_decision = decision
    nc.acceptance_return_reason = return_reason
    nc.acceptance_signer_name = _clean(data.get("acceptance_signer_name"))
    nc.acceptance_signer_at = data.get("acceptance_signer_at")


def _update_part_g(*, nc: AuditFindingNC, data: dict[str, Any]) -> None:
    nc.verifying_auditor_name = _clean(data.get("verifying_auditor_name"))
    nc.verifying_authority_org = _clean(data.get("verifying_authority_org"))
    nc.verification_method = _choice_or_blank(data.get("verification_method"), VERIFICATION_METHODS, "verification_method")
    nc.certificate_endorsement_type = _choice_or_blank(
        data.get("certificate_endorsement_type"),
        CERTIFICATE_ENDORSEMENT_TYPES,
        "certificate_endorsement_type",
    )
    nc.certificate_endorsement_ref = _clean(data.get("certificate_endorsement_ref"))
    nc.auditor_assessment_text = _clean(data.get("auditor_assessment_text"))
    nc.final_closure_status = _choice_or_blank(
        data.get("final_closure_status"),
        FINAL_CLOSURE_STATUSES,
        "final_closure_status",
    )
    nc.resubmit_by_date = data.get("resubmit_by_date")
    nc.auditor_verification_sign_at = data.get("auditor_verification_sign_at")


def _update_certificates_at_risk(*, context: AuditCarWorkflowContext, data: dict[str, Any]) -> None:
    if "certificates_at_risk" not in data:
        return
    certificates = _csv_to_list(data.get("certificates_at_risk"))
    allowed = OFFICE_CERTIFICATES_AT_RISK if context.audit_detail.auditee_type == "OFFICE_DEPT" else CERTIFICATES_AT_RISK
    unknown = sorted(set(certificates) - allowed)
    if unknown:
        raise AuditNcClosureError(f"certificates_at_risk is not valid for this audit: {', '.join(unknown)}.")
    context.finding.certificates_at_risk = ",".join(certificates) if certificates else None
    context.finding.save(update_fields=["certificates_at_risk"])


def _choice_or_blank(value: Any, allowed: set[str], field_name: str) -> str | None:
    text = _clean(value)
    if not text:
        return None
    text = text.upper()
    if text not in allowed:
        raise AuditNcClosureError(f"{field_name} must be one of: {', '.join(sorted(allowed))}.")
    return text


def _csv_to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    return [part.strip().upper() for part in str(value).split(",") if part.strip()]


def _clean(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _date_value(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date") and not isinstance(value, str):
        value = value.date()
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _datetime_value(value: Any) -> str | None:
    return value.isoformat() if value else None


def _user_id(user: object | None) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")


def _apply_car_transition(*, car: CAR, action: str, target_status: str, user: object, comment: str = "") -> None:
    car.status = target_status
    car.last_action = action
    car.last_action_by = _user_id(user)
    car.last_action_at = timezone.now()
    car.last_action_comment = comment or None
    car.updated_by = _user_id(user)
    car.sync_version += 1
    if action == WorkflowAction.REQUEST_REWORK:
        car.rework_reason = comment or None
        car.rework_requested_by = _user_id(user)
        car.rework_requested_at = car.last_action_at
        car.rework_count += 1
    car.save()


__all__ = [
    "AuditCarWorkflowError",
    "AuditNcClosureBundle",
    "AuditNcClosureError",
    "draft_nc_for_vessel",
    "get_nc_closure_bundle",
    "schedule_effectiveness_review",
    "serialize_nc_closure_bundle",
    "update_nc_part",
]
