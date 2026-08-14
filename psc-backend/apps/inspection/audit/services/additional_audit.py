"""Additional internal audit plan creation and trigger linkage."""

from __future__ import annotations

import uuid

from django.utils import timezone

from apps.inspection.audit.models import MasterAuditPlan
from apps.inspection.audit.serializers.plan import AuditPlanSerializer
from apps.inspection.audit.services.extension import AuditPlanWorkflowError


MIN_ADDITIONAL_REASON_LENGTH = 50
ADDITIONAL_TRIGGER_TYPES = {
    "PSC_INSPECTION",
    "DETENTION_NOTICE",
    "FLAG_LETTER",
    "INCIDENT_REPORT",
    "MGMT_DIRECTIVE",
    "OTHER",
}
EVIDENCE_TRIGGER_TYPES = {"DETENTION_NOTICE", "FLAG_LETTER", "MGMT_DIRECTIVE", "OTHER"}


def create_additional_audit_plan(
    *,
    data: dict,
    actor: str,
) -> MasterAuditPlan:
    normalized_data = dict(data)
    normalized_data["is_additional"] = False
    serializer = AuditPlanSerializer(data=normalized_data)
    serializer.is_valid(raise_exception=True)
    validated = dict(serializer.validated_data)

    additional_reason = str(data.get("additional_reason") or "").strip()
    if len(additional_reason) < MIN_ADDITIONAL_REASON_LENGTH:
        raise AuditPlanWorkflowError({"additional_reason": "Additional-audit reason must be at least 50 characters."})

    trigger_event_type = str(data.get("trigger_event_type") or "").strip().upper()
    trigger_event_ref = str(data.get("trigger_event_ref") or "").strip()
    if trigger_event_type not in ADDITIONAL_TRIGGER_TYPES:
        raise AuditPlanWorkflowError({"trigger_event_type": "Unsupported additional-audit trigger type."})
    if not trigger_event_ref:
        raise AuditPlanWorkflowError({"trigger_event_ref": "Trigger event reference or evidence reference is required."})
    _validate_trigger_reference(trigger_event_type, trigger_event_ref)

    validated.update(
        {
            "is_additional": True,
            "additional_reason": additional_reason,
            "trigger_event_type": trigger_event_type,
            "trigger_event_ref": trigger_event_ref,
            "status": "PLANNED",
            "created_by": actor,
            "created_date": timezone.now(),
        }
    )
    return MasterAuditPlan.objects.create(**validated)


def _validate_trigger_reference(trigger_event_type: str, trigger_event_ref: str) -> None:
    if trigger_event_type == "PSC_INSPECTION":
        try:
            from apps.inspection.models import Inspection
        except Exception as exc:
            raise AuditPlanWorkflowError({"trigger_event_ref": "PSC inspection validation is unavailable."}) from exc
        if not Inspection.objects.filter(id=trigger_event_ref, inspection_type="PSC", is_deleted=False).exists():
            raise AuditPlanWorkflowError({"trigger_event_ref": "PSC inspection trigger reference was not found."})
        return

    if trigger_event_type == "INCIDENT_REPORT":
        try:
            incident_id = uuid.UUID(trigger_event_ref)
        except ValueError as exc:
            raise AuditPlanWorkflowError({"trigger_event_ref": "Safety incident trigger reference was not found."}) from exc
        if not _safety_incident_exists(incident_id):
            raise AuditPlanWorkflowError({"trigger_event_ref": "Safety incident trigger reference was not found."})
        return

    if trigger_event_type in EVIDENCE_TRIGGER_TYPES and "TRIGGER_EVIDENCE=" not in trigger_event_ref.upper():
        raise AuditPlanWorkflowError(
            {"trigger_event_ref": "Trigger evidence attachment reference is required for this trigger type."}
        )


def _safety_incident_exists(incident_id: uuid.UUID) -> bool:
    try:
        from apps.safety.models import Incident
    except Exception as exc:
        raise AuditPlanWorkflowError({"trigger_event_ref": "Safety incident validation is unavailable."}) from exc
    return Incident.objects.filter(id=incident_id, record_type="INCIDENT", is_deleted=False).exists()


__all__ = ["ADDITIONAL_TRIGGER_TYPES", "create_additional_audit_plan"]
