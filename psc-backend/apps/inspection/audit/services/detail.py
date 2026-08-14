"""Audit detail read/update helpers for Phase 4 Step 4.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import (
    AuditAreaSummary,
    AuditDetail,
    AuditFinding,
    AuditMeetingAttendee,
    AuditStandard,
    AuditTeamMember,
    MasterAuditArea,
)
from apps.inspection.deficiency_models import Deficiency
from apps.inspection.models import Inspection


EDITABLE_DETAIL_FIELDS = (
    "audit_scope",
    "terms_of_reference",
    "audit_summary",
    "equipment_tested",
    "opening_meeting_at",
    "closing_meeting_at",
    "prev_internal_ca_verified",
    "prev_external_ca_verified",
)


@dataclass(frozen=True)
class AuditDetailBundle:
    audit_detail: AuditDetail
    inspection: Inspection
    standards: list[AuditStandard]
    team_members: list[AuditTeamMember]
    attendees: list[AuditMeetingAttendee]
    areas: list[MasterAuditArea]
    score_rows: dict[str, AuditAreaSummary]
    findings: list[dict[str, Any]]


def _inspection_for_detail(audit_detail: AuditDetail) -> Inspection:
    return Inspection.objects.get(id=UUID(hex=audit_detail.psc_inspection_id))


def get_audit_detail_bundle(audit_detail_id: UUID) -> AuditDetailBundle:
    audit_detail = AuditDetail.objects.get(id=audit_detail_id)
    inspection = _inspection_for_detail(audit_detail)
    standards = list(
        AuditStandard.objects.filter(audit_detail_id=audit_detail.id).order_by("sequence_no", "standard_code")
    )
    team_members = list(
        AuditTeamMember.objects.filter(audit_detail_id=audit_detail.id).order_by("sequence_no", "member_name")
    )
    attendees = list(
        AuditMeetingAttendee.objects.filter(audit_detail_id=audit_detail.id).order_by("sequence_no", "attendee_name")
    )
    areas = list(MasterAuditArea.objects.order_by("sequence_no", "area_code"))
    score_rows = {
        row.area_code: row
        for row in AuditAreaSummary.objects.filter(audit_detail_id=audit_detail.id)
    }
    findings = _finding_rows(audit_detail)
    return AuditDetailBundle(
        audit_detail=audit_detail,
        inspection=inspection,
        standards=standards,
        team_members=team_members,
        attendees=attendees,
        areas=areas,
        score_rows=score_rows,
        findings=findings,
    )


@transaction.atomic
def update_audit_detail_fields(*, audit_detail: AuditDetail, data: dict[str, Any], user: object) -> AuditDetail:
    changed_fields: list[str] = []
    for field_name in EDITABLE_DETAIL_FIELDS:
        if field_name in data:
            value = data[field_name]
            if value == "":
                value = None
            setattr(audit_detail, field_name, value)
            changed_fields.append(field_name)

    if changed_fields:
        audit_detail.updated_by = _user_id(user)
        audit_detail.updated_date = timezone.now()
        audit_detail.save(update_fields=[*changed_fields, "updated_by", "updated_date"])
    return audit_detail


@transaction.atomic
def upsert_scorecard_rows(*, audit_detail: AuditDetail, rows: list[dict[str, Any]], user: object) -> None:
    actor_id = _user_id(user)
    existing = {
        row.area_code: row
        for row in AuditAreaSummary.objects.select_for_update().filter(audit_detail_id=audit_detail.id)
    }
    for row_data in rows:
        area_code = row_data["area_code"]
        score_row = existing.get(area_code)
        if score_row is None:
            AuditAreaSummary.objects.create(
                audit_detail_id=audit_detail.id,
                area_code=area_code,
                status=row_data.get("status") or None,
                remarks=row_data.get("remarks") or None,
                created_by=actor_id,
            )
            continue

        score_row.status = row_data.get("status") or None
        score_row.remarks = row_data.get("remarks") or None
        score_row.save(update_fields=["status", "remarks"])


def valid_audit_area_codes() -> set[str]:
    return set(MasterAuditArea.objects.values_list("area_code", flat=True))


def _finding_rows(audit_detail: AuditDetail) -> list[dict[str, Any]]:
    findings = list(
        AuditFinding.objects.filter(audit_detail_id=audit_detail.id).order_by("created_date", "id")
    )
    deficiency_ids = [UUID(hex=finding.psc_deficiency_id) for finding in findings]
    deficiencies = {
        deficiency.id.hex: deficiency
        for deficiency in Deficiency.objects.filter(id__in=deficiency_ids).select_related("car")
    }
    rows: list[dict[str, Any]] = []
    for finding in findings:
        deficiency = deficiencies.get(finding.psc_deficiency_id)
        car = getattr(deficiency, "car", None) if deficiency else None
        rows.append(
            {
                "id": str(finding.id),
                "finding_type": finding.finding_type,
                "nc_category": finding.nc_category,
                "observation_category": finding.observation_category,
                "standard_code": finding.standard_code,
                "clause_ref_text": finding.clause_ref_text,
                "description": finding.description or (deficiency.description if deficiency else ""),
                "objective_evidence": finding.objective_evidence,
                "priority": finding.priority,
                "is_fleetwide_relevance": finding.is_fleetwide_relevance,
                "linked_circular_id": str(finding.linked_circular_id) if finding.linked_circular_id else None,
                "psc_deficiency_id": str(deficiency.id) if deficiency else finding.psc_deficiency_id,
                "car_id": str(car.id) if car else None,
                "car_number": car.car_number if car else None,
                "car_status": car.status if car else None,
            }
        )
    return rows


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")
