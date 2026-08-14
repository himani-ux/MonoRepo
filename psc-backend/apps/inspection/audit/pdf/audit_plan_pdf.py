"""SQE F 601 Audit Plan PDF generator."""

from __future__ import annotations

from uuid import UUID

from apps.inspection.audit.models import (
    AuditDetail,
    AuditMeetingAttendee,
    AuditScheduleBlock,
    AuditStandard,
    AuditTeamMember,
    MasterAuditPlan,
)
from apps.inspection.audit.pdf.common import (
    AuditPdfResult,
    additional_audit_banner,
    build_pdf_with_provenance,
    format_date,
    format_date_range,
    format_time,
    grid_table,
    info_table,
    is_audit_detail_draft,
    join_csv,
    section,
    signature_table,
    sms_header,
    spacer,
)
from apps.inspection.models import Inspection


FORM_NO = "SQE F 601"
REVISION = "KSM SSQE Manual Rev 01 Feb 2026"
FILING_REF = "A-2"
PDF_KIND = "F601"


def generate_audit_plan_pdf(audit_detail: AuditDetail, *, generated_by=None) -> AuditPdfResult:
    inspection = _inspection_for_detail(audit_detail)
    standards = list(
        AuditStandard.objects.filter(audit_detail_id=audit_detail.id).order_by("sequence_no", "standard_code")
    )
    team_members = list(
        AuditTeamMember.objects.filter(audit_detail_id=audit_detail.id).order_by("sequence_no", "member_name")
    )
    schedule_blocks = list(
        AuditScheduleBlock.objects.filter(audit_detail_id=audit_detail.id).order_by("sequence_no", "block_date")
    )
    attendees = list(
        AuditMeetingAttendee.objects.filter(audit_detail_id=audit_detail.id).order_by("sequence_no", "attendee_name")
    )
    plan = _plan_for_detail(audit_detail)

    def story_factory() -> list:
        story = [
            *additional_audit_banner(plan),
            *sms_header(FORM_NO, REVISION, FILING_REF, "F 601 - Audit Plan"),
            info_table(
                [
                    ("Audit Performed At", inspection.port_place),
                    ("Location", inspection.country),
                    ("Audit Dates", format_date_range(audit_detail.audit_start_date, audit_detail.audit_end_date)),
                    ("Type of Audit", f"{audit_detail.audit_classification} / {join_csv(s.standard_code for s in standards)}"),
                    ("Auditee", _auditee_label(audit_detail)),
                    ("Audit Subtype", audit_detail.audit_subtype),
                    ("Trigger Reason", audit_detail.trigger_reason),
                    ("Audit Plan Ref", audit_detail.audit_plan_id),
                ]
            ),
            spacer(),
            *section("Lead Auditor"),
            info_table(
                [
                    ("Name", audit_detail.lead_auditor_name),
                    ("Designation", audit_detail.lead_auditor_designation),
                    ("Company", audit_detail.lead_auditor_company),
                    ("Qualification", audit_detail.lead_auditor_qual),
                    ("PIC", audit_detail.pic_user_id_resolved or "- (assigned at first review)"),
                ]
            ),
            spacer(),
            *section("Other Auditors"),
            grid_table(
                ["Name", "Designation", "Company", "Role"],
                [
                    [
                        member.member_name,
                        member.member_designation,
                        member.member_company,
                        member.member_role,
                    ]
                    for member in team_members
                ],
                col_widths=[48, 42, 45, 45],
            ),
            spacer(),
            *section("Audit Plan Time Blocks"),
            grid_table(
                ["Date", "From", "To", "Activity"],
                [
                    [
                        format_date(block.block_date),
                        format_time(block.time_from),
                        format_time(block.time_to),
                        block.activity,
                    ]
                    for block in schedule_blocks
                ],
                col_widths=[32, 24, 24, 100],
            ),
            spacer(),
            *section("Personnel Present"),
            grid_table(
                ["Name", "Rank", "Opening", "Closing"],
                [
                    [
                        attendee.attendee_name,
                        attendee.attendee_rank,
                        "Yes" if attendee.opening_present else "No",
                        "Yes" if attendee.closing_present else "No",
                    ]
                    for attendee in attendees
                ],
                col_widths=[58, 48, 35, 35],
            ),
            spacer(),
            *section("Remarks"),
            info_table(
                [
                    ("Remarks", audit_detail.audit_summary),
                    ("Additional Audit", _additional_summary(plan)),
                ]
            ),
            spacer(),
            signature_table(["Lead Auditor Signature"]),
        ]
        return story

    content, _payload = build_pdf_with_provenance(
        story_factory,
        form_no=FORM_NO,
        filing_ref=FILING_REF,
        pdf_kind=PDF_KIND,
        audit_detail_id=audit_detail.id,
        generated_by=generated_by,
        is_draft=is_audit_detail_draft(audit_detail),
    )
    return AuditPdfResult(content=content, file_name=f"F601_AuditPlan_{audit_detail.id}.pdf")


def _inspection_for_detail(audit_detail: AuditDetail) -> Inspection:
    return Inspection.objects.get(id=UUID(hex=audit_detail.psc_inspection_id))


def _plan_for_detail(audit_detail: AuditDetail) -> MasterAuditPlan | None:
    if not audit_detail.audit_plan_id:
        return None
    return MasterAuditPlan.objects.filter(id=audit_detail.audit_plan_id).first()


def _auditee_label(audit_detail: AuditDetail) -> str:
    if audit_detail.auditee_type == "OFFICE_DEPT":
        return f"Office Department - {audit_detail.auditee_office_dept or '-'}"
    return audit_detail.auditee_type


def _additional_summary(plan: MasterAuditPlan | None) -> str:
    if not plan or not plan.is_additional:
        return "No"
    reason = (plan.additional_reason or "")[:200]
    return f"Yes - {plan.trigger_event_type or '-'} - {reason or '-'}"
