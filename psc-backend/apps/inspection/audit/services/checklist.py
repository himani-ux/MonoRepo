"""Checklist master read helpers for Phase 5 Step 5.1."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from django.db import connection
from django.db.models import Q

from apps.inspection.audit.models import (
    AuditDetail,
    MasterAuditChecklist,
    MasterAuditChecklistItem,
)
from apps.inspection.audit.services.detail import get_audit_detail_by_id


@dataclass(frozen=True)
class AuditChecklistBundle:
    audit_detail: AuditDetail
    checklist: MasterAuditChecklist | None
    items: list[MasterAuditChecklistItem]
    ship_type_filter: str | None
    item_filter_applied: bool


def get_audit_checklist_bundle(
    *,
    audit_detail_id: UUID,
    ship_type: str | None = None,
) -> AuditChecklistBundle:
    audit_detail = get_audit_detail_by_id(audit_detail_id)
    checklist = select_checklist_for_audit(audit_detail)
    normalized_ship_type = _clean_text(ship_type) or None
    items = checklist_items_for(checklist, ship_type=normalized_ship_type)
    return AuditChecklistBundle(
        audit_detail=audit_detail,
        checklist=checklist,
        items=items,
        ship_type_filter=normalized_ship_type,
        item_filter_applied=bool(normalized_ship_type),
    )


def select_checklist_for_audit(audit_detail: AuditDetail) -> MasterAuditChecklist | None:
    auditee_type = _clean_text(audit_detail.auditee_type).upper()
    query = MasterAuditChecklist.objects.filter(is_active=True, auditee_type__iexact=auditee_type)

    if auditee_type == "OFFICE_DEPT":
        office_dept = _clean_text(audit_detail.auditee_office_dept).upper()
        if not office_dept:
            return None
        query = query.filter(scope_dept__iexact=office_dept)
    elif auditee_type == "VESSEL":
        query = query.filter(source_form_ref__iexact="F 605")
    else:
        return None

    return query.order_by("checklist_code").first()


def checklist_items_for(
    checklist: MasterAuditChecklist | None,
    *,
    ship_type: str | None = None,
) -> list[MasterAuditChecklistItem]:
    if checklist is None:
        return []

    checklist_id = _uuid_value(checklist.id)
    if connection.vendor == "microsoft":
        params = [str(checklist_id)]
        ship_type_clause = ""
        if ship_type:
            ship_type_clause = """
              AND (
                ship_type IS NULL
                OR ship_type = ''
                OR LOWER(ship_type) = LOWER(%s)
                OR LOWER(ship_type) = LOWER(%s)
              )
            """
            params.extend(["Common", ship_type])
        return list(
            MasterAuditChecklistItem.objects.raw(
                f"""
                SELECT *
                FROM dbo.master_audit_checklist_item
                WHERE master_audit_checklist_id = CAST(%s AS uniqueidentifier)
                  {ship_type_clause}
                ORDER BY [sequence_no], [item_code], [id]
                """,
                params,
            )
        )

    query = MasterAuditChecklistItem.objects.filter(master_audit_checklist_id=checklist_id)
    if ship_type:
        query = query.filter(
            Q(ship_type__isnull=True)
            | Q(ship_type="")
            | Q(ship_type__iexact="Common")
            | Q(ship_type__iexact=ship_type)
        )
    return list(query.order_by("sequence_no", "item_code", "id"))


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _uuid_value(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))
