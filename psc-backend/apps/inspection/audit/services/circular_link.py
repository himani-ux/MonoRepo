"""Audit NC to Circular module link seam."""

from __future__ import annotations

from dataclasses import dataclass
import uuid

from django.db import connection, transaction
from django.utils import timezone

from apps.inspection.audit.models import AuditDetail, AuditFinding
from apps.inspection.deficiency_models import Deficiency


class AuditCircularLinkError(ValueError):
    """Base error for Issue Circular validation."""


class AuditCircularLinkValidationError(AuditCircularLinkError):
    """Raised when a finding is not eligible for Circular issue."""


@dataclass(frozen=True)
class AuditCircularLinkResult:
    status: str
    circular_id: uuid.UUID
    detail_url: str
    payload: dict[str, object]


@transaction.atomic
def issue_circular_from_finding(*, finding_id: uuid.UUID | str, user: object) -> AuditCircularLinkResult:
    finding = AuditFinding.objects.select_for_update().get(id=_coerce_uuid(finding_id))
    _validate_issue_circular(finding)

    if finding.linked_circular_id:
        return _result(
            status="ALREADY_LINKED",
            circular_id=finding.linked_circular_id,
            payload={"source_record_id": str(finding.id)},
        )

    audit_detail = AuditDetail.objects.select_for_update().get(id=finding.audit_detail_id)
    deficiency = Deficiency.objects.select_related("car").get(id=uuid.UUID(hex=finding.psc_deficiency_id))
    circular_id = uuid.uuid4()
    payload = _build_circular_payload(
        circular_id=circular_id,
        finding=finding,
        audit_detail=audit_detail,
        deficiency=deficiency,
        user=user,
    )
    _insert_circular_draft(payload)

    finding.linked_circular_id = circular_id
    finding.save(update_fields=["linked_circular_id"])

    return _result(status="DRAFT_CREATED", circular_id=circular_id, payload=payload)


def _validate_issue_circular(finding: AuditFinding) -> None:
    if finding.finding_type != "NC":
        raise AuditCircularLinkValidationError("Issue Circular is available only for NC findings.")
    if not finding.is_fleetwide_relevance:
        raise AuditCircularLinkValidationError("Issue Circular requires is_fleetwide_relevance.")


def _build_circular_payload(
    *,
    circular_id: uuid.UUID,
    finding: AuditFinding,
    audit_detail: AuditDetail,
    deficiency: Deficiency,
    user: object,
) -> dict[str, object]:
    car_number = getattr(getattr(deficiency, "car", None), "car_number", None) or finding.psc_deficiency_id
    description = (finding.description or deficiency.description or "").strip()
    evidence = (finding.objective_evidence or "").strip()
    body_parts = [
        f"Audit finding: {car_number}",
        f"NC category: {finding.nc_category or ''}",
        f"Priority: {finding.priority}",
        f"Clause: {finding.clause_ref_text or finding.standard_code or ''}",
        "",
        description,
    ]
    if evidence:
        body_parts.extend(["", f"Objective evidence: {evidence}"])

    return {
        "id": str(circular_id),
        "sr_no": None,
        "title": f"Fleet-wide audit NC circular draft - {car_number}",
        "office_instructions": "\n".join(part for part in body_parts if part is not None),
        "hashtags": "audit,nc,fleetwide",
        "created_by": _user_id(user),
        "created_at": timezone.now(),
        "publish_status": 0,
        "is_active": True,
        "is_deleted": False,
        "vessel_id": audit_detail.vessel_id,
        "category": "AUDIT_NC",
        "source_module": "AUDIT",
        "source_record_type": "AUDIT_FINDING",
        "source_record_id": str(finding.id),
    }


def _insert_circular_draft(payload: dict[str, object]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO msc_data (
                id, sr_no, title, office_instructions, hashtags, created_by,
                created_at, publish_status, is_active, is_deleted, vessel_id, category
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                payload["id"],
                payload["sr_no"],
                payload["title"],
                payload["office_instructions"],
                payload["hashtags"],
                payload["created_by"],
                payload["created_at"],
                payload["publish_status"],
                payload["is_active"],
                payload["is_deleted"],
                payload["vessel_id"],
                payload["category"],
            ],
        )


def _result(*, status: str, circular_id: uuid.UUID, payload: dict[str, object]) -> AuditCircularLinkResult:
    return AuditCircularLinkResult(
        status=status,
        circular_id=circular_id,
        detail_url=f"/circular/office?draft_id={circular_id}&source=audit_finding",
        payload=payload,
    )


def _coerce_uuid(value: uuid.UUID | str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")
