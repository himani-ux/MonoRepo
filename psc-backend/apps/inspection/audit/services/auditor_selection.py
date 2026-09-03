from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from django.db import DatabaseError, connection
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import HRM501, OfficeUser
from apps.inspection.audit.models import (
    MasterAuditQualifiedAuditor,
    MasterExternalAuditOrg,
    VesselAuditRoDelegation,
)


@dataclass(frozen=True)
class AuditorSnapshot:
    user_id: str
    name: str
    designation: str
    company: str
    qualification: str


def parse_standards_csv(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = str(value or "").split(",")
    standards: list[str] = []
    for raw_value in raw_values:
        standard = str(raw_value or "").strip().upper()
        if standard and standard not in standards:
            standards.append(standard)
    return standards


def get_external_org_by_id(org_id: object) -> MasterExternalAuditOrg | None:
    try:
        org_uuid = UUID(str(org_id))
    except (TypeError, ValueError):
        return None

    if connection.vendor == "microsoft":
        rows = list(
            MasterExternalAuditOrg.objects.raw(
                """
                SELECT *
                FROM dbo.master_external_audit_org
                WHERE id = CAST(%s AS uniqueidentifier)
                  AND is_active = 1
                """,
                [str(org_uuid)],
            )
        )
        return rows[0] if rows else None

    return MasterExternalAuditOrg.objects.filter(id=org_uuid, is_active=True).first()


def qualified_auditor_queryset(
    *,
    standards: object = None,
    eligible_on=None,
    target_office_dept: object = None,
):
    queryset = MasterAuditQualifiedAuditor.objects.filter(is_active=True)
    current_date = eligible_on or timezone.localdate()
    queryset = queryset.filter(expiry_date__gte=current_date)

    parsed_standards = parse_standards_csv(standards)
    if parsed_standards:
        standards_filter = Q()
        for standard in parsed_standards:
            standards_filter |= Q(scope_standards_csv__icontains=standard)
        queryset = queryset.filter(standards_filter)

    if str(target_office_dept or "").strip().upper() == "SEQ":
        queryset = queryset.filter(qualified_for_seq=True)

    return queryset.order_by("expiry_date", "user_id")


def get_qualified_auditor(
    user_id: object,
    *,
    standards: object = None,
    eligible_on=None,
    target_office_dept: object = None,
) -> MasterAuditQualifiedAuditor | None:
    normalized_user_id = str(user_id or "").strip()
    if not normalized_user_id:
        return None
    return (
        qualified_auditor_queryset(
            standards=standards,
            eligible_on=eligible_on,
            target_office_dept=target_office_dept,
        )
        .filter(user_id__iexact=normalized_user_id)
        .first()
    )


def auditor_snapshot(
    user_id: object,
    *,
    standards: object = None,
    eligible_on=None,
    target_office_dept: object = None,
) -> AuditorSnapshot | None:
    qualified = get_qualified_auditor(
        user_id,
        standards=standards,
        eligible_on=eligible_on,
        target_office_dept=target_office_dept,
    )
    if qualified is None:
        return None

    identity = resolve_user_identity(qualified.user_id)
    return AuditorSnapshot(
        user_id=qualified.user_id,
        name=identity["name"] or qualified.user_id,
        designation=identity["designation"] or "",
        company=identity["company"] or "KSM",
        qualification=qualified.qualification_text or qualified.qualifying_body or "",
    )


def _normalized_identifier(value: object) -> str:
    return str(value or "").strip()


def _office_role_name_for_identifiers(*identifiers: object) -> str:
    candidates = []
    seen = set()
    for identifier in identifiers:
        normalized = _normalized_identifier(identifier)
        key = normalized.casefold()
        if normalized and key not in seen:
            candidates.append(normalized)
            seen.add(key)

    if not candidates:
        return ""

    sql_server = """
        SELECT TOP 1 mr.role_name
        FROM mapping_role_user mru
        INNER JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
        ORDER BY mru.created_date DESC
    """
    sql_sqlite = """
        SELECT mr.role_name
        FROM mapping_role_user mru
        INNER JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
        ORDER BY mru.created_date DESC
        LIMIT 1
    """
    sql = sql_sqlite if connection.vendor == "sqlite" else sql_server

    for candidate in candidates:
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, [candidate])
                row = cursor.fetchone()
        except DatabaseError:
            continue
        if row and row[0]:
            return str(row[0]).strip()
    return ""


def resolve_user_identity(user_id: object) -> dict[str, str]:
    normalized_user_id = str(user_id or "").strip()
    if not normalized_user_id:
        return {"name": "", "designation": "", "company": "", "source": ""}

    try:
        office_user = (
            OfficeUser.objects.filter(is_active=True, is_deleted=False)
            .filter(Q(employee_id__iexact=normalized_user_id) | Q(username__iexact=normalized_user_id))
            .first()
        )
    except DatabaseError:
        office_user = None
    if office_user is not None:
        name = (
            getattr(office_user, "display_name", "")
            or getattr(office_user, "employee_name", "")
            or getattr(office_user, "full_name", "")
            or normalized_user_id
        )
        designation = _office_role_name_for_identifiers(
            normalized_user_id,
            getattr(office_user, "employee_id", ""),
            getattr(office_user, "username", ""),
        )
        return {
            "name": name,
            "designation": designation or getattr(office_user, "department", "") or "",
            "company": "KSM",
            "source": "OFFICE",
        }

    try:
        crew_user = (
            HRM501.objects.filter(is_active=True, is_deleted=False)
            .filter(Q(user_id__iexact=normalized_user_id) | Q(CrewID__iexact=normalized_user_id))
            .first()
        )
    except DatabaseError:
        crew_user = None
    if crew_user is not None:
        name_parts = [
            str(getattr(crew_user, "first_name", "") or "").strip(),
            str(getattr(crew_user, "surname", "") or "").strip(),
        ]
        return {
            "name": " ".join(part for part in name_parts if part) or normalized_user_id,
            "designation": getattr(crew_user, "rank_name", "") or "",
            "company": "Vessel",
            "source": "CREW",
        }

    return {"name": normalized_user_id, "designation": "", "company": "", "source": ""}


def resolve_external_org_for_vessel_standard(
    *,
    vessel_id: object,
    standards: object,
    effective_on=None,
) -> MasterExternalAuditOrg | None:
    parsed_standards = parse_standards_csv(standards)
    if not vessel_id or not parsed_standards:
        return None

    try:
        normalized_vessel_id = UUID(str(vessel_id))
    except (TypeError, ValueError):
        return None

    current_date = effective_on or timezone.localdate()
    if connection.vendor == "microsoft":
        standard_placeholders = ", ".join(["%s"] * len(parsed_standards))
        rows = list(
            MasterExternalAuditOrg.objects.raw(
                f"""
                SELECT TOP 1 org.*
                FROM dbo.master_external_audit_org org
                INNER JOIN dbo.vessel_audit_ro_delegation delegation
                    ON delegation.master_external_audit_org_id = org.id
                WHERE delegation.target_vessel_id = CAST(%s AS uniqueidentifier)
                  AND delegation.standard_code IN ({standard_placeholders})
                  AND delegation.effective_from <= %s
                  AND (delegation.effective_to IS NULL OR delegation.effective_to >= %s)
                  AND org.is_active = 1
                ORDER BY delegation.effective_from DESC, delegation.standard_code
                """,
                [str(normalized_vessel_id), *parsed_standards, current_date, current_date],
            )
        )
        return rows[0] if rows else None

    delegation = (
        VesselAuditRoDelegation.objects.filter(
            target_vessel_id=normalized_vessel_id,
            standard_code__in=parsed_standards,
            effective_from__lte=current_date,
        )
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=current_date))
        .order_by("-effective_from", "standard_code")
        .first()
    )
    if delegation is None:
        return None
    return get_external_org_by_id(delegation.master_external_audit_org_id)
