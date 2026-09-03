"""SQE F 602 Internal Audit Report PDF generator."""

from __future__ import annotations

from apps.inspection.audit.finding_types import (
    is_nc_finding,
    is_observation_finding,
    normalize_finding_type,
    normalize_nc_category,
    normalize_observation_category,
)
from apps.inspection.audit.models import AuditAreaSummary, AuditDetail, AuditFinding, MasterAuditArea, MasterAuditPlan
from apps.inspection.audit.pdf.audit_plan_pdf import _auditee_label, _plan_for_detail
from apps.inspection.audit.pdf.common import (
    AuditPdfResult,
    additional_audit_banner,
    build_pdf_with_provenance,
    format_date,
    format_date_range,
    grid_table,
    info_table,
    is_audit_detail_draft,
    join_csv,
    section,
    signature_table,
    sms_header,
    spacer,
)
from apps.inspection.audit.services.detail import get_audit_detail_bundle


FORM_NO = "SQE F 602"
REVISION = "KSM SSQE Manual Rev 01 Feb 2026"
FILING_REF = "A-20"
PDF_KIND = "F602"


def generate_audit_report_pdf(audit_detail: AuditDetail, *, generated_by=None) -> AuditPdfResult:
    bundle = get_audit_detail_bundle(audit_detail.id)
    inspection = bundle.inspection
    plan = _plan_for_detail(audit_detail)
    findings = list(AuditFinding.objects.filter(audit_detail_id=audit_detail.id).order_by("created_date", "id"))
    nc_count = sum(1 for finding in findings if is_nc_finding(finding.finding_type))
    obs_count = sum(1 for finding in findings if is_observation_finding(finding.finding_type))

    def story_factory() -> list:
        story = [
            *additional_audit_banner(plan),
            *sms_header(FORM_NO, REVISION, FILING_REF, "F 602 - Internal Audit Report"),
            info_table(
                [
                    ("Vessel / Department", _entity_label(audit_detail, inspection)),
                    ("Location / Port", inspection.port_place),
                    ("Date(s)", format_date_range(audit_detail.audit_start_date, audit_detail.audit_end_date)),
                    ("Auditee", _auditee_label(audit_detail)),
                    ("Auditor(s)", _auditor_list(audit_detail, bundle.team_members)),
                    ("Standards", join_csv(standard.standard_code for standard in bundle.standards)),
                    ("Terms of Reference", audit_detail.terms_of_reference),
                    ("Objectives / Scope", audit_detail.audit_scope),
                ]
            ),
            spacer(),
            *section("Previous Corrective Action Verification"),
            info_table(
                [
                    ("Previous Internal CA Verified", audit_detail.prev_internal_ca_verified),
                    ("Previous External CA Verified", audit_detail.prev_external_ca_verified),
                    ("NCs Raised", nc_count),
                    ("Observations Raised", obs_count),
                    ("Additional Audit", _additional_summary(plan)),
                ]
            ),
            spacer(),
            *section("Summary of Audit"),
            info_table(
                [
                    ("Summary", audit_detail.audit_summary),
                    ("Equipment Tested Successfully", audit_detail.equipment_tested),
                    ("Opening Meeting", format_date(audit_detail.opening_meeting_at)),
                    ("Closing Meeting", format_date(audit_detail.closing_meeting_at)),
                ]
            ),
            spacer(),
            *section("14-Area Inspection Summary"),
            _scorecard_table(bundle.areas, bundle.score_rows),
            spacer(),
            *section("Audit Result"),
            grid_table(
                ["S.No", "Category", "NC / Obs", "Reference", "Due Date"],
                [
                    [
                        index,
                        normalize_nc_category(finding.nc_category)
                        or normalize_observation_category(finding.observation_category)
                        or "-",
                        normalize_finding_type(finding.finding_type),
                        finding.clause_ref_text or finding.standard_code or "-",
                        format_date(finding.extended_due_date or finding.original_due_date),
                    ]
                    for index, finding in enumerate(findings, start=1)
                ],
                col_widths=[14, 42, 30, 62, 32],
            ),
            spacer(),
            signature_table(["Lead Auditor Signature", "Master / HoD Signature"]),
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
    return AuditPdfResult(content=content, file_name=f"F602_AuditReport_{audit_detail.id}.pdf")


def _entity_label(audit_detail: AuditDetail, inspection) -> str:
    if audit_detail.auditee_type == "OFFICE_DEPT":
        return audit_detail.auditee_office_dept or "Office Department"
    return f"Vessel {inspection.vessel_id}"


def _auditor_list(audit_detail: AuditDetail, team_members) -> str:
    return join_csv([audit_detail.lead_auditor_name, *[member.member_name for member in team_members]])


def _scorecard_table(areas: list[MasterAuditArea], score_rows: dict[str, AuditAreaSummary]):
    return grid_table(
        ["Area", "Status", "Remarks"],
        [
            [
                area.display_name,
                _status_label(score_rows.get(area.area_code)),
                (score_rows.get(area.area_code).remarks if score_rows.get(area.area_code) else None),
            ]
            for area in areas
        ],
        col_widths=[60, 32, 88],
    )


def _status_label(row: AuditAreaSummary | None) -> str:
    if not row or not row.status:
        return "-"
    return "N/A" if row.status == "N_A" else row.status


def _additional_summary(plan: MasterAuditPlan | None) -> str:
    if not plan or not plan.is_additional:
        return "No"
    reason = (plan.additional_reason or "")[:200]
    return f"Yes - {plan.trigger_event_type or '-'} - {reason or '-'}"
