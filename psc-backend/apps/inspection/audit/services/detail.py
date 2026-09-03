"""Audit detail read/update helpers for Phase 4 Step 4.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.db import connection, transaction
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
from apps.inspection.audit.finding_types import (
    normalize_finding_type,
    normalize_nc_category,
    normalize_observation_category,
)
from apps.inspection.audit.services.registration import _insert_sql_server_row
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
REQUIRED_SCORECARD_ROW_COUNT = 14


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


def get_audit_detail_by_id(audit_detail_id: object, *, for_update: bool = False) -> AuditDetail:
    try:
        detail_uuid = UUID(str(audit_detail_id))
    except (TypeError, ValueError) as exc:
        raise AuditDetail.DoesNotExist from exc

    if connection.vendor == "microsoft":
        lock_hint = " WITH (UPDLOCK, ROWLOCK)" if for_update else ""
        rows = list(
            AuditDetail.objects.raw(
                f"""
                SELECT *
                FROM dbo.audit_detail{lock_hint}
                WHERE id = CAST(%s AS uniqueidentifier)
                  AND is_deleted = 0
                """,
                [str(detail_uuid)],
            )
        )
        if rows:
            return rows[0]
        raise AuditDetail.DoesNotExist

    queryset = AuditDetail.objects
    if for_update:
        queryset = queryset.select_for_update()
    return queryset.get(id=detail_uuid)


def get_audit_finding_by_id(finding_id: object, *, for_update: bool = False) -> AuditFinding:
    try:
        finding_uuid = UUID(str(finding_id))
    except (TypeError, ValueError) as exc:
        raise AuditFinding.DoesNotExist from exc

    if connection.vendor == "microsoft":
        lock_hint = " WITH (UPDLOCK, ROWLOCK)" if for_update else ""
        rows = list(
            AuditFinding.all_objects.raw(
                f"""
                SELECT *
                FROM dbo.{AuditFinding._meta.db_table}{lock_hint}
                WHERE id = CAST(%s AS uniqueidentifier)
                  AND is_deleted = 0
                """,
                [str(finding_uuid)],
            )
        )
        if rows:
            return rows[0]
        raise AuditFinding.DoesNotExist

    queryset = AuditFinding.all_objects
    if for_update:
        queryset = queryset.select_for_update()
    return queryset.get(id=finding_uuid, is_deleted=False)


def get_audit_detail_bundle(audit_detail_id: UUID) -> AuditDetailBundle:
    audit_detail = get_audit_detail_by_id(audit_detail_id)
    inspection = _inspection_for_detail(audit_detail)
    standards = _audit_detail_rows(
        AuditStandard,
        "audit_standards",
        audit_detail.id,
        order_by_fields=("sequence_no", "standard_code"),
        order_by_sql="[sequence_no], [standard_code]",
    )
    team_members = _audit_detail_rows(
        AuditTeamMember,
        "audit_team_member",
        audit_detail.id,
        order_by_fields=("sequence_no", "member_name"),
        order_by_sql="[sequence_no], [member_name]",
        soft_deleted=True,
    )
    attendees = _audit_detail_rows(
        AuditMeetingAttendee,
        "audit_meeting_attendee",
        audit_detail.id,
        order_by_fields=("sequence_no", "attendee_name"),
        order_by_sql="[sequence_no], [attendee_name]",
        soft_deleted=True,
    )
    areas = required_audit_scorecard_areas()
    score_rows = {
        row.area_code: row
        for row in _audit_detail_rows(
            AuditAreaSummary,
            "audit_area_summary",
            audit_detail.id,
            order_by_fields=("area_code",),
            order_by_sql="[area_code]",
        )
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
    detail_uuid = _uuid_value(audit_detail.id)
    existing = {
        row.area_code: row
        for row in _audit_detail_rows(
            AuditAreaSummary,
            "audit_area_summary",
            detail_uuid,
            order_by_fields=("area_code",),
            order_by_sql="[area_code]",
            for_update=True,
        )
    }
    for row_data in rows:
        area_code = row_data["area_code"]
        score_row = existing.get(area_code)
        if score_row is None:
            _create_scorecard_row(
                audit_detail_id=detail_uuid,
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
    return required_audit_area_codes()


def required_audit_scorecard_areas() -> list[MasterAuditArea]:
    return list(
        MasterAuditArea.objects.filter(sequence_no__lte=REQUIRED_SCORECARD_ROW_COUNT)
        .order_by("sequence_no", "area_code")[:REQUIRED_SCORECARD_ROW_COUNT]
    )


def required_audit_area_codes() -> set[str]:
    return {area.area_code for area in required_audit_scorecard_areas()}


def _create_scorecard_row(*, audit_detail_id: UUID, area_code: str, status: str | None, remarks: str | None, created_by: str) -> None:
    values = {
        "audit_detail_id": audit_detail_id,
        "area_code": area_code,
        "status": status,
        "remarks": remarks,
        "created_by": created_by,
    }
    if connection.vendor == "microsoft":
        _insert_sql_server_row("audit_area_summary", values)
        return
    AuditAreaSummary.objects.create(**values)


def _finding_rows(audit_detail: AuditDetail) -> list[dict[str, Any]]:
    findings = _audit_detail_rows(
        AuditFinding,
        "audit_finding",
        audit_detail.id,
        order_by_fields=("created_date", "finding_type", "id"),
        order_by_sql="[created_date], [finding_type], [id]",
        soft_deleted=True,
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
                "finding_type": normalize_finding_type(finding.finding_type),
                "nc_category": normalize_nc_category(finding.nc_category),
                "observation_category": normalize_observation_category(finding.observation_category),
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


def _audit_detail_rows(
    model,
    table_name: str,
    audit_detail_id: object,
    *,
    order_by_fields: tuple[str, ...],
    order_by_sql: str,
    soft_deleted: bool = False,
    for_update: bool = False,
):
    detail_uuid = _uuid_value(audit_detail_id)
    if connection.vendor == "microsoft":
        lock_hint = " WITH (UPDLOCK, ROWLOCK)" if for_update else ""
        soft_delete_clause = "AND is_deleted = 0" if soft_deleted else ""
        return list(
            model.objects.raw(
                f"""
                SELECT *
                FROM dbo.{table_name}{lock_hint}
                WHERE audit_detail_id = CAST(%s AS uniqueidentifier)
                  {soft_delete_clause}
                ORDER BY {order_by_sql}
                """,
                [str(detail_uuid)],
            )
        )

    queryset = model.objects
    if for_update:
        queryset = queryset.select_for_update()
    return list(queryset.filter(audit_detail_id=detail_uuid).order_by(*order_by_fields))


def _uuid_value(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))
