"""KSM-F-OBS-001 closure persistence for Audit Observation findings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from django.db import connection, transaction
from django.utils import timezone

from apps.inspection.audit.models import (
    AuditDetail,
    AuditFinding,
    AuditFindingOBS,
    AuditFindingSignEvent,
)
from apps.inspection.audit.finding_types import is_observation_finding, normalize_observation_category
from apps.inspection.audit.services.car_workflow import AuditCarWorkflowError
from apps.inspection.audit.services.detail import get_audit_detail_by_id, get_audit_finding_by_id
from apps.inspection.deficiency_models import CAR, Deficiency
from apps.inspection.models import Inspection


ACCEPTANCE_DECISIONS = {"ACCEPTED", "RETURNED"}
VERIFICATION_METHODS = {
    "DOCUMENT_REVIEW",
    "ONBOARD_VERIFICATION",
    "NEXT_AUDIT",
    "REMOTE_REVIEW",
}
CLOSURE_STATUSES = {"CLOSED", "PARTIALLY_CLOSED", "NOT_CLOSED"}


class AuditObsClosureError(ValueError):
    """Raised when an Observation closure request violates KSM-F-OBS-001."""


@dataclass(frozen=True)
class AuditObsClosureBundle:
    finding: AuditFinding
    audit_detail: AuditDetail
    inspection: Inspection
    deficiency: Deficiency
    car: CAR
    obs: AuditFindingOBS


@dataclass(frozen=True)
class AuditObsClosureContext:
    finding: AuditFinding
    audit_detail: AuditDetail
    deficiency: Deficiency
    car: CAR


def get_obs_closure_bundle(finding_id: UUID | str, *, user: object | None = None) -> AuditObsClosureBundle:
    context = resolve_audit_obs_context(finding_id)
    obs = _ensure_obs_record(context, user=user)
    return _bundle(context=context, obs=obs)


@transaction.atomic
def update_obs_part(
    *,
    finding_id: UUID | str,
    part: str,
    data: dict[str, Any],
    user: object,
) -> AuditObsClosureBundle:
    context = resolve_audit_obs_context(finding_id)
    obs = _ensure_obs_record(context, user=user)
    part = part.lower()

    if part == "part-b":
        _update_part_b(context=context, obs=obs, data=data, user=user)
    elif part == "part-c":
        _update_part_c(obs=obs, data=data)
    elif part == "part-d":
        _update_part_d(obs=obs, data=data)
    else:
        raise AuditObsClosureError("Unknown Observation closure part.")

    _promote_audit_closure_progress(context=context, user=user)
    obs.updated_by = _user_id(user)
    obs.updated_date = timezone.now()
    obs.save()
    return _bundle(context=context, obs=obs)


def resolve_audit_obs_context(finding_id: UUID | str) -> AuditObsClosureContext:
    try:
        finding_uuid = UUID(str(finding_id))
    except (TypeError, ValueError, AttributeError):
        raise AuditCarWorkflowError("Audit finding not found.", error="NOT_FOUND", status_code=404)

    try:
        finding = get_audit_finding_by_id(finding_uuid)
    except AuditFinding.DoesNotExist:
        raise AuditCarWorkflowError("Audit finding not found.", error="NOT_FOUND", status_code=404)

    try:
        audit_detail = get_audit_detail_by_id(finding.audit_detail_id)
    except AuditDetail.DoesNotExist:
        raise AuditCarWorkflowError(
            "Audit detail not found for finding.",
            error="AUDIT_DETAIL_NOT_FOUND",
            status_code=400,
        )

    try:
        deficiency_uuid = UUID(str(finding.psc_deficiency_id))
    except (TypeError, ValueError, AttributeError):
        raise AuditCarWorkflowError(
            "Audit finding has an invalid psc_deficiency_id.",
            error="INVALID_DEFICIENCY_REFERENCE",
            status_code=400,
        )

    deficiency = (
        Deficiency.objects.select_related("inspection", "car")
        .filter(id=deficiency_uuid)
        .first()
    )
    if not deficiency:
        raise AuditCarWorkflowError("Linked CAR deficiency not found.", error="DEFICIENCY_NOT_FOUND", status_code=404)

    inspection = deficiency.inspection
    if inspection.inspection_type != "AUDIT":
        raise AuditCarWorkflowError(
            "Linked deficiency is not attached to an Audit inspection.",
            error="NOT_AUDIT_INSPECTION",
            status_code=400,
        )
    if audit_detail.psc_inspection_id != inspection.id.hex:
        raise AuditCarWorkflowError(
            "Audit detail does not match the linked inspection.",
            error="AUDIT_INSPECTION_MISMATCH",
            status_code=400,
        )
    if not is_observation_finding(finding.finding_type):
        raise AuditCarWorkflowError(
            "Observation closure is valid only for Observation findings; NC findings use the NC closure flow.",
            error="NOT_OBSERVATION_FINDING",
            status_code=400,
        )
    if not getattr(deficiency, "car_id", None):
        raise AuditCarWorkflowError("Linked deficiency has no CAR.", error="CAR_NOT_FOUND", status_code=404)

    return AuditObsClosureContext(
        finding=finding,
        audit_detail=audit_detail,
        deficiency=deficiency,
        car=deficiency.car,
    )


def serialize_obs_closure_bundle(bundle: AuditObsClosureBundle) -> dict[str, Any]:
    finding = bundle.finding
    audit_detail = bundle.audit_detail
    inspection = bundle.inspection
    deficiency = bundle.deficiency
    car = bundle.car
    obs = bundle.obs
    return {
        "id": str(obs.id),
        "finding_id": str(finding.id),
        "audit_detail_id": str(audit_detail.id),
        "state": observation_state(obs),
        "car": {
            "id": str(car.id),
            "car_number": car.car_number,
            "status": car.status,
            "target_date": _date_value(car.target_date),
        },
        "part_a": {
            "observation_reference_no": car.car_number,
            "audit_date": _date_value(inspection.inspection_date),
            "vessel_id": str(inspection.vessel_id),
            "port_place": inspection.port_place or "",
            "auditor_name": audit_detail.lead_auditor_name,
            "auditor_organisation": audit_detail.lead_auditor_company,
            "rule_book_type": finding.rule_book_type,
            "clause_ref_text": finding.clause_ref_text,
            "objective_evidence": finding.objective_evidence or "",
            "observation_issued_date": _date_value(getattr(finding, "created_date", None)),
            "required_closure_deadline": _date_value(finding.original_due_date or deficiency.target_date),
            "observation_category": normalize_observation_category(finding.observation_category),
            "description": finding.description or deficiency.description,
        },
        "part_b": {
            "responded_by_name": obs.responded_by_name or "",
            "responded_by_rank": obs.responded_by_rank or "",
            "target_closure_date": _date_value(obs.target_closure_date),
            "immediate_action_text": obs.immediate_action_text or "",
            "root_cause_text": obs.root_cause_text or "",
            "corrective_action_text": obs.corrective_action_text or "",
            "preventive_action_text": obs.preventive_action_text or "",
            "sms_amendment_required": obs.sms_amendment_required,
            "sms_amendment_doc_ref": obs.sms_amendment_doc_ref or "",
            "actual_closure_date": _date_value(obs.actual_closure_date),
            "master_sign_name": obs.master_sign_name or "",
            "master_sign_at": _datetime_value(obs.master_sign_at),
        },
        "part_c": {
            "acceptance_review_date": _date_value(obs.acceptance_review_date),
            "acceptance_adequacy_text": obs.acceptance_adequacy_text or "",
            "acceptance_decision": obs.acceptance_decision or "",
            "acceptance_return_reason": obs.acceptance_return_reason or "",
            "acceptance_signer_name": obs.acceptance_signer_name or "",
            "acceptance_signer_at": _datetime_value(obs.acceptance_signer_at),
        },
        "part_d": {
            "verifying_auditor_name": obs.verifying_auditor_name or "",
            "verifying_authority_org": obs.verifying_authority_org or "",
            "verification_method": obs.verification_method or "",
            "auditor_remarks_text": obs.auditor_remarks_text or "",
            "closure_status": obs.closure_status or "",
            "resubmit_by_date": _date_value(obs.resubmit_by_date),
            "auditor_verification_sign_at": _datetime_value(obs.auditor_verification_sign_at),
        },
    }


def observation_state(obs: AuditFindingOBS) -> str:
    if obs.master_sign_at:
        return "MASTER_CLOSED"
    if obs.actual_closure_date:
        return "SUBMITTED"
    if any(
        (
            obs.responded_by_name,
            obs.responded_by_rank,
            obs.target_closure_date,
            obs.immediate_action_text,
            obs.root_cause_text,
            obs.corrective_action_text,
            obs.preventive_action_text,
            obs.sms_amendment_doc_ref,
        )
    ) or obs.sms_amendment_required:
        return "IN_PROGRESS"
    return "NOT_STARTED"


def _ensure_obs_record(context: AuditObsClosureContext, *, user: object | None) -> AuditFindingOBS:
    if connection.vendor == "microsoft":
        existing = _get_sql_server_obs_record(context.finding.id)
        if existing:
            return existing

        obs_id = uuid4()
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO dbo.{AuditFindingOBS._meta.db_table} (
                    [id],
                    [audit_finding_id],
                    [created_by],
                    [created_date],
                    [sms_amendment_required]
                )
                VALUES (
                    CAST(%s AS uniqueidentifier),
                    CAST(%s AS uniqueidentifier),
                    %s,
                    %s,
                    %s
                )
                """,
                [
                    str(obs_id),
                    str(context.finding.id),
                    _user_id(user),
                    timezone.now(),
                    False,
                ],
            )
        created = _get_sql_server_obs_record(context.finding.id)
        if created:
            return created
        raise AuditFindingOBS.DoesNotExist("Audit OBS closure record was saved but could not be reloaded.")

    obs, _created = AuditFindingOBS.objects.get_or_create(
        audit_finding_id=context.finding.id,
        defaults={"created_by": _user_id(user)},
    )
    return obs


def _get_sql_server_obs_record(finding_id: UUID) -> AuditFindingOBS | None:
    rows = list(
        AuditFindingOBS.objects.raw(
            f"""
            SELECT *
            FROM dbo.{AuditFindingOBS._meta.db_table}
            WHERE audit_finding_id = CAST(%s AS uniqueidentifier)
            """,
            [str(finding_id)],
        )
    )
    return rows[0] if rows else None


def _bundle(*, context: AuditObsClosureContext, obs: AuditFindingOBS) -> AuditObsClosureBundle:
    return AuditObsClosureBundle(
        finding=context.finding,
        audit_detail=context.audit_detail,
        inspection=context.deficiency.inspection,
        deficiency=context.deficiency,
        car=context.car,
        obs=obs,
    )


def _update_part_b(
    *,
    context: AuditObsClosureContext,
    obs: AuditFindingOBS,
    data: dict[str, Any],
    user: object,
) -> None:
    if obs.master_sign_at:
        raise AuditObsClosureError("Observation Part B is terminal after MASTER_CLOSED.")

    master_sign_at = data.get("master_sign_at")
    master_sign_name = _clean(data.get("master_sign_name"))
    if master_sign_at and not master_sign_name:
        raise AuditObsClosureError("master_sign_name is required when the Master signs Part B.")

    obs.responded_by_name = _clean(data.get("responded_by_name"))
    obs.responded_by_rank = _clean(data.get("responded_by_rank"))
    obs.target_closure_date = data.get("target_closure_date")
    obs.immediate_action_text = _clean(data.get("immediate_action_text"))
    obs.root_cause_text = _clean(data.get("root_cause_text"))
    obs.corrective_action_text = _clean(data.get("corrective_action_text"))
    obs.preventive_action_text = _clean(data.get("preventive_action_text"))
    obs.sms_amendment_required = bool(data.get("sms_amendment_required"))
    obs.sms_amendment_doc_ref = _clean(data.get("sms_amendment_doc_ref"))
    obs.actual_closure_date = data.get("actual_closure_date")
    obs.master_sign_name = master_sign_name
    obs.master_sign_at = master_sign_at

    if obs.sms_amendment_required and not obs.sms_amendment_doc_ref:
        raise AuditObsClosureError("sms_amendment_doc_ref is required when SMS amendment is required.")
    if master_sign_at:
        _record_master_signature(context=context, user=user, signed_at=master_sign_at)


def _update_part_c(*, obs: AuditFindingOBS, data: dict[str, Any]) -> None:
    decision = _choice_or_blank(data.get("acceptance_decision"), ACCEPTANCE_DECISIONS, "acceptance_decision")
    obs.acceptance_review_date = data.get("acceptance_review_date")
    obs.acceptance_adequacy_text = _clean(data.get("acceptance_adequacy_text"))
    obs.acceptance_decision = decision
    obs.acceptance_return_reason = _clean(data.get("acceptance_return_reason"))
    obs.acceptance_signer_name = _clean(data.get("acceptance_signer_name"))
    obs.acceptance_signer_at = data.get("acceptance_signer_at")


def _update_part_d(*, obs: AuditFindingOBS, data: dict[str, Any]) -> None:
    obs.verifying_auditor_name = _clean(data.get("verifying_auditor_name"))
    obs.verifying_authority_org = _clean(data.get("verifying_authority_org"))
    obs.verification_method = _choice_or_blank(data.get("verification_method"), VERIFICATION_METHODS, "verification_method")
    obs.auditor_remarks_text = _clean(data.get("auditor_remarks_text"))
    obs.closure_status = _choice_or_blank(data.get("closure_status"), CLOSURE_STATUSES, "closure_status")
    obs.resubmit_by_date = data.get("resubmit_by_date")
    obs.auditor_verification_sign_at = data.get("auditor_verification_sign_at")


def _record_master_signature(*, context: AuditObsClosureContext, user: object, signed_at) -> None:
    if AuditFindingSignEvent.objects.filter(
        audit_finding_id=context.finding.id,
        part_label="OBS_PART_B",
    ).exists():
        return
    AuditFindingSignEvent.objects.create(
        audit_finding_id=context.finding.id,
        user_id=_user_id(user),
        rank_at_signing=_clean(getattr(user, "rank", None)),
        part_label="OBS_PART_B",
        claimed_sign_datetime=signed_at,
        actual_entered_at=timezone.now(),
        created_by=_user_id(user),
    )


def _promote_audit_closure_progress(*, context: AuditObsClosureContext, user: object) -> None:
    audit_detail = get_audit_detail_by_id(context.audit_detail.id, for_update=True)
    if audit_detail.status != "VESSEL_ACKNOWLEDGED":
        return
    audit_detail.status = "CLOSURE_IN_PROGRESS"
    audit_detail.updated_by = _user_id(user)
    audit_detail.updated_date = timezone.now()
    audit_detail.save(update_fields=["status", "updated_by", "updated_date"])


def _choice_or_blank(value: Any, allowed: set[str], field_name: str) -> str | None:
    text = _clean(value)
    if not text:
        return None
    text = text.upper()
    if text not in allowed:
        raise AuditObsClosureError(f"{field_name} must be one of: {', '.join(sorted(allowed))}.")
    return text


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


__all__ = [
    "ACCEPTANCE_DECISIONS",
    "CLOSURE_STATUSES",
    "VERIFICATION_METHODS",
    "AuditObsClosureBundle",
    "AuditObsClosureError",
    "get_obs_closure_bundle",
    "observation_state",
    "serialize_obs_closure_bundle",
    "update_obs_part",
]
