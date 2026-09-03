"""Audit registration write path for Phase 4 Step 4.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import uuid

from django.db import connection, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.inspection.audit.models import (
    AuditAttachment,
    AuditDetail,
    AuditMeetingAttendee,
    AuditScheduleBlock,
    AuditStandard,
    AuditTeamMember,
    MasterAuditPlan,
)
from apps.inspection.models import Inspection, InspectionType


REGISTERABLE_AUDIT_PLAN_STATUSES = {"CONFIRMED", "EXTENDED", "CRITICAL_OVERDUE"}
CONSUMED_AUDIT_PLAN_STATUS = "IN_PROGRESS"


@dataclass(frozen=True)
class AuditRegistrationResult:
    inspection: Inspection
    audit_detail: AuditDetail


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")


def get_audit_plan_by_id(plan_id: object, *, for_update: bool = False) -> MasterAuditPlan:
    try:
        plan_uuid = uuid.UUID(str(plan_id))
    except (TypeError, ValueError) as exc:
        raise MasterAuditPlan.DoesNotExist from exc

    if connection.vendor == "microsoft":
        lock_hint = " WITH (UPDLOCK, ROWLOCK)" if for_update else ""
        rows = list(
            MasterAuditPlan.objects.raw(
                f"""
                SELECT *
                FROM dbo.master_audit_plan{lock_hint}
                WHERE id = CAST(%s AS uniqueidentifier)
                  AND is_deleted = 0
                """,
                [str(plan_uuid)],
            )
        )
        if rows:
            return rows[0]
        raise MasterAuditPlan.DoesNotExist

    queryset = MasterAuditPlan.objects
    if for_update:
        queryset = queryset.select_for_update()
    return queryset.get(id=plan_uuid)


def validate_registerable_audit_plan(plan: MasterAuditPlan, *, exclude_audit_detail_id: object | None = None) -> None:
    if plan.status not in REGISTERABLE_AUDIT_PLAN_STATUSES:
        allowed = ", ".join(sorted(REGISTERABLE_AUDIT_PLAN_STATUSES))
        raise ValidationError({"audit_plan_id": f"Audit plan must be one of {allowed} before registration."})

    if _registered_audit_exists_for_plan(plan.id, exclude_audit_detail_id=exclude_audit_detail_id):
        raise ValidationError({"audit_plan_id": "Selected audit plan has already been registered."})


def _registered_audit_exists_for_plan(plan_id: object, *, exclude_audit_detail_id: object | None = None) -> bool:
    if connection.vendor == "microsoft":
        plan_uuid = _uuid_or_none(plan_id)
        if plan_uuid is None:
            return False
        params = [plan_uuid]
        exclude_clause = ""
        excluded_uuid = _uuid_or_none(exclude_audit_detail_id)
        if excluded_uuid is not None:
            exclude_clause = "AND id <> CAST(%s AS uniqueidentifier)"
            params.append(excluded_uuid)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT TOP 1 id
                FROM dbo.audit_detail
                WHERE audit_plan_id = CAST(%s AS uniqueidentifier)
                  AND is_deleted = 0
                  {exclude_clause}
                """,
                params,
            )
            return cursor.fetchone() is not None

    existing = AuditDetail.objects.filter(audit_plan_id=plan_id)
    if exclude_audit_detail_id:
        existing = existing.exclude(id=exclude_audit_detail_id)
    return existing.exists()


def _lock_registerable_audit_plan(plan_id: object | None) -> MasterAuditPlan | None:
    if not plan_id:
        return None
    try:
        plan = get_audit_plan_by_id(plan_id, for_update=True)
    except MasterAuditPlan.DoesNotExist as exc:
        raise ValidationError({"audit_plan_id": "Audit plan was not found."}) from exc
    validate_registerable_audit_plan(plan)
    return plan


def _audit_detail_uuid_reference(value: object) -> str | None:
    """Keep audit_detail model references compact unless SQL casting needs UUID text."""

    if value in (None, ""):
        return None
    if hasattr(value, "hex"):
        return value.hex
    return str(value).replace("-", "")


def _create_audit_detail(values: dict[str, Any]) -> AuditDetail:
    if connection.vendor != "microsoft":
        return AuditDetail.objects.create(**values)

    audit_detail_id = uuid.uuid4()
    insert_values = {
        "id": audit_detail_id,
        "created_by": values.get("created_by"),
        "created_date": values.get("created_date") or timezone.now(),
        "is_deleted": False,
        "updated_by": values.get("updated_by"),
        "updated_date": values.get("updated_date"),
        "client_id": values.get("client_id"),
        "sync_version": values.get("sync_version") or 1,
        **values,
    }
    _insert_sql_server_row("audit_detail", insert_values)
    return _fetch_sql_server_audit_detail(audit_detail_id)


def _fetch_sql_server_audit_detail(audit_detail_id) -> AuditDetail:
    rows = list(
        AuditDetail.all_objects.raw(
            """
            SELECT *
            FROM dbo.audit_detail
            WHERE id = CAST(%s AS uniqueidentifier)
            """,
            [str(audit_detail_id)],
        )
    )
    if not rows:
        raise AuditDetail.DoesNotExist("Audit detail was saved but could not be reloaded.")
    return rows[0]


def _audit_detail_column_types() -> dict[str, Any]:
    return _table_column_types("audit_detail")


def _table_column_types(table_name: str) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = %s
            """,
            [table_name],
        )
        return {
            str(name).lower(): {
                "data_type": str(data_type).lower(),
                "max_length": max_length,
            }
            for name, data_type, max_length in cursor.fetchall()
        }


def _sql_value_for_column(column_name: str, value, column_types: dict[str, Any]) -> tuple[str, list]:
    if _column_data_type(column_types, column_name) == "uniqueidentifier":
        return "CAST(%s AS uniqueidentifier)", [_uuid_or_none(value)]
    return "%s", [value]


def _validate_audit_detail_lengths(values: dict[str, Any], column_types: dict[str, Any]) -> None:
    _validate_column_lengths("audit_detail", values, column_types)


def _validate_column_lengths(table_name: str, values: dict[str, Any], column_types: dict[str, Any]) -> None:
    errors = {}
    for column_name, value in values.items():
        if value in (None, ""):
            continue
        data_type = _column_data_type(column_types, column_name)
        max_length = _column_max_length(column_types, column_name)
        if data_type not in {"char", "varchar", "nchar", "nvarchar"}:
            continue
        if not isinstance(max_length, int) or max_length < 0:
            continue
        actual_length = len(str(value))
        if actual_length > max_length:
            errors[column_name] = (
                f"Value is {actual_length} characters, but {table_name}.{column_name} "
                f"allows only {max_length}."
            )
    if errors:
        raise ValidationError(errors)


def _insert_sql_server_row(table_name: str, values: dict[str, Any]):
    column_types = _table_column_types(table_name)
    insert_values = _sql_server_insert_values(values, column_types)
    _validate_column_lengths(table_name, insert_values, column_types)

    columns = list(insert_values.keys())
    value_sql = []
    params = []
    for column in columns:
        expression, expression_params = _sql_value_for_column(column, insert_values[column], column_types)
        value_sql.append(expression)
        params.extend(expression_params)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO dbo.{table_name} ({", ".join(f"[{column}]" for column in columns)})
            VALUES ({", ".join(value_sql)})
            """,
            params,
        )

    return insert_values.get("id")


def _sql_server_insert_values(values: dict[str, Any], column_types: dict[str, Any]) -> dict[str, Any]:
    insert_values = dict(values)
    if "id" in column_types and not insert_values.get("id"):
        insert_values = {"id": uuid.uuid4(), **insert_values}
    if "created_date" in column_types and not insert_values.get("created_date"):
        insert_values["created_date"] = timezone.now()
    if "uploaded_at" in column_types and not insert_values.get("uploaded_at"):
        insert_values["uploaded_at"] = timezone.now()
    if "is_deleted" in column_types and "is_deleted" not in insert_values:
        insert_values["is_deleted"] = False
    if "attestation_required" in column_types and "attestation_required" not in insert_values:
        insert_values["attestation_required"] = False
    return {column: value for column, value in insert_values.items() if column.lower() in column_types}


def _bulk_create_registration_rows(model, table_name: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    if connection.vendor != "microsoft":
        model.objects.bulk_create([model(**row) for row in rows])
        return
    for row in rows:
        _insert_sql_server_row(table_name, row)


def _create_registration_row(model, table_name: str, values: dict[str, Any]) -> None:
    if connection.vendor != "microsoft":
        model.objects.create(**values)
        return
    _insert_sql_server_row(table_name, values)


def _column_data_type(column_types: dict[str, Any], column_name: str) -> str | None:
    metadata = column_types.get(column_name.lower())
    if isinstance(metadata, dict):
        return metadata.get("data_type")
    return metadata


def _column_max_length(column_types: dict[str, Any], column_name: str):
    metadata = column_types.get(column_name.lower())
    if isinstance(metadata, dict):
        return metadata.get("max_length")
    return None


def _uuid_or_none(value) -> str | None:
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (AttributeError, TypeError, ValueError):
        return None


@transaction.atomic
def register_internal_audit(*, data: dict[str, Any], user: object) -> AuditRegistrationResult:
    """Create the shared PSC inspection root row and Audit F601 child rows."""

    actor_id = _user_id(user)
    vessel_id = data.get("vessel_id")
    consumed_plan = _lock_registerable_audit_plan(data.get("audit_plan_id")) if data["audit_classification"] == "INTERNAL" else None

    inspection = Inspection.objects.create(
        vessel_id=vessel_id,
        inspection_type=InspectionType.AUDIT,
        psc_subtype=None,
        inspection_date=data["inspection_date"],
        port_place=data["port_place"],
        country=data.get("country") or "",
        authority=data.get("authority") or "",
        inspector_name=data.get("inspector_name") or data["lead_auditor_name"],
        report_reference=data.get("report_reference") or "",
        is_detention=False,
        def_reported=data.get("def_reported") or "NO",
        created_by=actor_id,
    )

    is_external = data["audit_classification"] == "EXTERNAL"
    late_registration_reason = (data.get("late_registration_reason") or "").strip()

    audit_detail = _create_audit_detail(
        {
            "psc_inspection_id": _audit_detail_uuid_reference(inspection.id),
            "vessel_id": _audit_detail_uuid_reference(vessel_id),
            "audit_classification": data["audit_classification"],
            "auditee_type": data["auditee_type"],
            "auditee_office_dept": data.get("auditee_office_dept") or None,
            "audit_subtype": data["audit_subtype"],
            "audit_subtype_other": data.get("audit_subtype_other") or None,
            "lead_auditor_name": data["lead_auditor_name"],
            "lead_auditor_designation": data.get("lead_auditor_designation") or None,
            "lead_auditor_company": data["lead_auditor_company"],
            "lead_auditor_qual": data.get("lead_auditor_qual") or None,
            "conductor_user_id": actor_id,
            "lead_auditor_user_id": data.get("lead_auditor_user_id") or None,
            "trigger_reason": data["trigger_reason"],
            "audit_plan_id": data.get("audit_plan_id"),
            "parent_audit_id": data.get("parent_audit_id") or None,
            "audit_start_date": data["audit_start_date"],
            "audit_end_date": data.get("audit_end_date"),
            "opening_meeting_at": data.get("opening_meeting_at"),
            "closing_meeting_at": data.get("closing_meeting_at"),
            "audit_scope": data.get("audit_scope") or None,
            "terms_of_reference": data.get("terms_of_reference") or None,
            "audit_summary": data.get("audit_summary") or None,
            "equipment_tested": data.get("equipment_tested") or None,
            "prev_internal_ca_verified": data.get("prev_internal_ca_verified") or None,
            "prev_external_ca_verified": data.get("prev_external_ca_verified") or None,
            "status": "SUBMITTED" if is_external else "IN_PROGRESS",
            "external_audit_subtypes_csv": ",".join(data.get("external_audit_subtypes") or []) or None,
            "external_audit_org_id": data.get("external_audit_org_id"),
            "external_audit_org_type": data.get("external_audit_org_type") or None,
            "external_lead_auditor_name": data.get("external_lead_auditor_name") or None,
            "external_lead_auditor_credential": data.get("external_lead_auditor_credential") or None,
            "flag_state_code": data.get("flag_state_code") or None,
            "cycle_year": data.get("cycle_year"),
            "linked_cert_ids_csv": ",".join(str(cert_id) for cert_id in data.get("linked_cert_ids") or []) or None,
            "late_registration_reason": late_registration_reason or None,
            "late_registered_by": actor_id if late_registration_reason else None,
            "late_registered_at": timezone.now() if late_registration_reason else None,
            "created_by": actor_id,
        }
    )
    if consumed_plan is not None:
        validate_registerable_audit_plan(consumed_plan, exclude_audit_detail_id=audit_detail.id)
        consumed_plan.status = CONSUMED_AUDIT_PLAN_STATUS
        consumed_plan.updated_by = actor_id
        consumed_plan.updated_date = timezone.now()
        from apps.inspection.audit.services.plan_persistence import save_plan_update

        save_plan_update(consumed_plan, ["status", "updated_by", "updated_date"])

    if is_external:
        _create_registration_row(
            AuditAttachment,
            "audit_attachment",
            {
                "audit_detail_id": audit_detail.id,
                "file_name": data["external_report_file_name"],
                "file_path": data["external_report_file_path"],
                "file_size": data.get("external_report_file_size"),
                "mime_type": data["external_report_mime_type"],
                "category": "EXTERNAL_AUDIT_REPORT",
                "attachment_version": "FINAL",
                "uploaded_by": actor_id,
                "description": "External audit report PDF",
            },
        )

    _bulk_create_registration_rows(
        AuditStandard,
        "audit_standards",
        [
            {
                "audit_detail_id": audit_detail.id,
                "standard_code": standard_code,
                "sequence_no": index,
                "created_by": actor_id,
            }
            for index, standard_code in enumerate(data.get("standards") or [], start=1)
        ],
    )
    _bulk_create_registration_rows(
        AuditTeamMember,
        "audit_team_member",
        [
            {
                "audit_detail_id": audit_detail.id,
                "member_name": member["member_name"],
                "member_designation": member.get("member_designation") or None,
                "member_company": member.get("member_company") or None,
                "member_role": member.get("member_role") or None,
                "sequence_no": index,
                "created_by": actor_id,
            }
            for index, member in enumerate(data.get("team_members") or [], start=1)
        ],
    )
    _bulk_create_registration_rows(
        AuditMeetingAttendee,
        "audit_meeting_attendee",
        [
            {
                "audit_detail_id": audit_detail.id,
                "attendee_name": attendee["attendee_name"],
                "attendee_rank": attendee.get("attendee_rank") or None,
                "opening_present": attendee.get("opening_present", False),
                "closing_present": attendee.get("closing_present", False),
                "sequence_no": index,
                "created_by": actor_id,
            }
            for index, attendee in enumerate(data.get("attendees") or [], start=1)
        ],
    )
    _bulk_create_registration_rows(
        AuditScheduleBlock,
        "audit_schedule_block",
        [
            {
                "audit_detail_id": audit_detail.id,
                "block_date": block.get("block_date"),
                "time_from": block.get("time_from"),
                "time_to": block.get("time_to"),
                "activity": block.get("activity") or None,
                "sequence_no": index,
                "created_by": actor_id,
            }
            for index, block in enumerate(data.get("schedule_blocks") or [], start=1)
        ],
    )

    return AuditRegistrationResult(inspection=inspection, audit_detail=audit_detail)
