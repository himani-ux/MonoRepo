"""Audit registration write path for Phase 4 Step 4.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import (
    AuditAttachment,
    AuditDetail,
    AuditMeetingAttendee,
    AuditScheduleBlock,
    AuditStandard,
    AuditTeamMember,
)
from apps.inspection.models import Inspection, InspectionType


@dataclass(frozen=True)
class AuditRegistrationResult:
    inspection: Inspection
    audit_detail: AuditDetail


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")


@transaction.atomic
def register_internal_audit(*, data: dict[str, Any], user: object) -> AuditRegistrationResult:
    """Create the shared PSC inspection root row and Audit F601 child rows."""

    actor_id = _user_id(user)
    vessel_id = data.get("vessel_id")

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

    audit_detail = AuditDetail.objects.create(
        psc_inspection_id=inspection.id.hex,
        vessel_id=vessel_id.hex if hasattr(vessel_id, "hex") else str(vessel_id).replace("-", ""),
        audit_classification=data["audit_classification"],
        auditee_type=data["auditee_type"],
        auditee_office_dept=data.get("auditee_office_dept") or None,
        audit_subtype=data["audit_subtype"],
        audit_subtype_other=data.get("audit_subtype_other") or None,
        lead_auditor_name=data["lead_auditor_name"],
        lead_auditor_designation=data.get("lead_auditor_designation") or None,
        lead_auditor_company=data["lead_auditor_company"],
        lead_auditor_qual=data.get("lead_auditor_qual") or None,
        conductor_user_id=actor_id,
        lead_auditor_user_id=data.get("lead_auditor_user_id") or None,
        trigger_reason=data["trigger_reason"],
        audit_plan_id=data.get("audit_plan_id"),
        parent_audit_id=data.get("parent_audit_id") or None,
        audit_start_date=data["audit_start_date"],
        audit_end_date=data.get("audit_end_date"),
        opening_meeting_at=data.get("opening_meeting_at"),
        closing_meeting_at=data.get("closing_meeting_at"),
        audit_scope=data.get("audit_scope") or None,
        terms_of_reference=data.get("terms_of_reference") or None,
        audit_summary=data.get("audit_summary") or None,
        equipment_tested=data.get("equipment_tested") or None,
        prev_internal_ca_verified=data.get("prev_internal_ca_verified") or None,
        prev_external_ca_verified=data.get("prev_external_ca_verified") or None,
        status="SUBMITTED" if is_external else "IN_PROGRESS",
        external_audit_subtypes_csv=",".join(data.get("external_audit_subtypes") or []) or None,
        external_audit_org_id=data.get("external_audit_org_id"),
        external_audit_org_type=data.get("external_audit_org_type") or None,
        external_lead_auditor_name=data.get("external_lead_auditor_name") or None,
        external_lead_auditor_credential=data.get("external_lead_auditor_credential") or None,
        flag_state_code=data.get("flag_state_code") or None,
        cycle_year=data.get("cycle_year"),
        linked_cert_ids_csv=",".join(str(cert_id) for cert_id in data.get("linked_cert_ids") or []) or None,
        late_registration_reason=late_registration_reason or None,
        late_registered_by=actor_id if late_registration_reason else None,
        late_registered_at=timezone.now() if late_registration_reason else None,
        created_by=actor_id,
    )

    if is_external:
        AuditAttachment.objects.create(
            audit_detail_id=audit_detail.id,
            file_name=data["external_report_file_name"],
            file_path=data["external_report_file_path"],
            file_size=data.get("external_report_file_size"),
            mime_type=data["external_report_mime_type"],
            category="EXTERNAL_AUDIT_REPORT",
            attachment_version="FINAL",
            uploaded_by=actor_id,
            description="External audit report PDF",
        )

    AuditStandard.objects.bulk_create(
        [
            AuditStandard(
                audit_detail_id=audit_detail.id,
                standard_code=standard_code,
                sequence_no=index,
                created_by=actor_id,
            )
            for index, standard_code in enumerate(data.get("standards") or [], start=1)
        ]
    )
    AuditTeamMember.objects.bulk_create(
        [
            AuditTeamMember(
                audit_detail_id=audit_detail.id,
                member_name=member["member_name"],
                member_designation=member.get("member_designation") or None,
                member_company=member.get("member_company") or None,
                member_role=member.get("member_role") or None,
                sequence_no=index,
                created_by=actor_id,
            )
            for index, member in enumerate(data.get("team_members") or [], start=1)
        ]
    )
    AuditMeetingAttendee.objects.bulk_create(
        [
            AuditMeetingAttendee(
                audit_detail_id=audit_detail.id,
                attendee_name=attendee["attendee_name"],
                attendee_rank=attendee.get("attendee_rank") or None,
                opening_present=attendee.get("opening_present", False),
                closing_present=attendee.get("closing_present", False),
                sequence_no=index,
                created_by=actor_id,
            )
            for index, attendee in enumerate(data.get("attendees") or [], start=1)
        ]
    )
    AuditScheduleBlock.objects.bulk_create(
        [
            AuditScheduleBlock(
                audit_detail_id=audit_detail.id,
                block_date=block.get("block_date"),
                time_from=block.get("time_from"),
                time_to=block.get("time_to"),
                activity=block.get("activity") or None,
                sequence_no=index,
                created_by=actor_id,
            )
            for index, block in enumerate(data.get("schedule_blocks") or [], start=1)
        ]
    )

    return AuditRegistrationResult(inspection=inspection, audit_detail=audit_detail)
