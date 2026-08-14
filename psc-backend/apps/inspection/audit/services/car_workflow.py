from __future__ import annotations

import uuid
from dataclasses import dataclass

from apps.inspection.audit.models import AuditDetail, AuditFinding
from apps.inspection.deficiency_models import CAR, Deficiency
from apps.inspection.workflow import WorkflowAction


class AuditCarWorkflowError(ValueError):
    def __init__(self, message: str, *, error: str = "AUDIT_CAR_WORKFLOW_ERROR", status_code: int = 400):
        super().__init__(message)
        self.error = error
        self.status_code = status_code


@dataclass(frozen=True)
class AuditCarWorkflowContext:
    finding: AuditFinding
    audit_detail: AuditDetail
    deficiency: Deficiency
    car: CAR


def _identity_matches(left, right) -> bool:
    left_text = str(left or "").strip()
    right_text = str(right or "").strip()
    if not left_text or not right_text:
        return False
    if left_text == right_text:
        return True

    try:
        return uuid.UUID(left_text).hex == uuid.UUID(right_text).hex
    except (TypeError, ValueError, AttributeError):
        return left_text.lower() == right_text.lower()


def resolve_audit_car_workflow_context(finding_id: uuid.UUID | str) -> AuditCarWorkflowContext:
    try:
        finding_uuid = uuid.UUID(str(finding_id))
    except (TypeError, ValueError, AttributeError):
        raise AuditCarWorkflowError("Audit finding not found.", error="NOT_FOUND", status_code=404)

    finding = AuditFinding.all_objects.filter(id=finding_uuid, is_deleted=False).first()
    if not finding:
        raise AuditCarWorkflowError("Audit finding not found.", error="NOT_FOUND", status_code=404)

    audit_detail = AuditDetail.objects.filter(id=finding.audit_detail_id).first()
    if not audit_detail:
        raise AuditCarWorkflowError(
            "Audit detail not found for finding.",
            error="AUDIT_DETAIL_NOT_FOUND",
            status_code=400,
        )

    try:
        deficiency_uuid = uuid.UUID(str(finding.psc_deficiency_id))
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
    if finding.finding_type != "NC":
        raise AuditCarWorkflowError(
            "Audit CAR workflow is valid only for NC findings; Observations use the Observation closure flow.",
            error="NOT_NC_FINDING",
            status_code=400,
        )
    if not getattr(deficiency, "car_id", None):
        raise AuditCarWorkflowError("Linked deficiency has no CAR.", error="CAR_NOT_FOUND", status_code=404)

    return AuditCarWorkflowContext(
        finding=finding,
        audit_detail=audit_detail,
        deficiency=deficiency,
        car=deficiency.car,
    )


def validate_audit_proxy_preconditions(context: AuditCarWorkflowContext, *, action: str | None, user) -> None:
    if action == WorkflowAction.START_PIC_REVIEW:
        if _identity_matches(getattr(user, "id", None), context.audit_detail.lead_auditor_user_id):
            raise AuditCarWorkflowError(
                "Lead Auditor cannot claim PIC review for their own audit.",
                error="LEAD_AUDITOR_PIC_DENIED",
                status_code=403,
            )
