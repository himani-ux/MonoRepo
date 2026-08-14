"""KSM-F-NC-001 Non-Conformity closure PDF generator."""

from __future__ import annotations

from uuid import UUID

from reportlab.platypus import PageBreak

from apps.inspection.audit.models import AuditDetail, AuditFinding, AuditFindingClause, AuditFindingNC
from apps.inspection.audit.pdf.audit_plan_pdf import _inspection_for_detail
from apps.inspection.audit.pdf.common import (
    AuditPdfResult,
    build_pdf_with_provenance,
    format_date,
    info_table,
    is_nc_pdf_draft,
    section,
    signature_table,
    sms_header,
    spacer,
)
from apps.inspection.deficiency_models import Deficiency


FORM_NO = "KSM-F-NC-001"
REVISION = "Rev 01 Jan-2026"
FILING_REF = "A-9"
PDF_KIND = "KSM_F_NC_001"


def generate_audit_nc_pdf(finding: AuditFinding, *, generated_by=None) -> AuditPdfResult:
    audit_detail = AuditDetail.objects.get(id=finding.audit_detail_id)
    inspection = _inspection_for_detail(audit_detail)
    deficiency = _deficiency_for_finding(finding)
    car = getattr(deficiency, "car", None) if deficiency else None
    closure = AuditFindingNC.objects.filter(audit_finding_id=finding.id).first()

    def story_factory() -> list:
        story = [
            *sms_header(FORM_NO, REVISION, FILING_REF, "KSM-F-NC-001 - Non-Conformity Closure Form"),
            *section("Part A - NC Details"),
            info_table(
                [
                    ("NC Reference No.", getattr(car, "car_number", None)),
                    ("Date of Audit", format_date(inspection.inspection_date)),
                    ("Vessel / Department", audit_detail.auditee_office_dept or f"Vessel {inspection.vessel_id}"),
                    ("Port / Location", inspection.port_place),
                    ("Auditor", f"{audit_detail.lead_auditor_name} / {audit_detail.lead_auditor_company}"),
                    ("Code / Regulation Reference", _clause_reference(finding)),
                    ("KSM SMS / Procedure Ref", finding.clause_ref_text),
                    ("Objective Evidence", finding.objective_evidence),
                    ("Required Closure Deadline", format_date(finding.extended_due_date or finding.original_due_date)),
                    ("Certificate at Risk", finding.certificates_at_risk),
                    ("NC Classification", finding.nc_category),
                ]
            ),
            spacer(),
            *section("Part B - Immediate / Containment Action"),
            info_table(
                [
                    ("Action Text", getattr(closure, "immediate_action_text", None)),
                    ("Date Completed", format_date(getattr(closure, "immediate_action_completed_at", None))),
                    ("Master / Responsible Officer Sign", _sign_line(getattr(closure, "master_immediate_sign_name", None), getattr(closure, "master_immediate_sign_at", None))),
                    ("Office-Led Drafting", _draft_footer(closure)),
                ]
            ),
            spacer(),
            *section("Part C - Root Cause Analysis"),
            info_table(
                [
                    ("RCA Method", getattr(closure, "rca_method", None)),
                    ("Problem Statement", getattr(closure, "problem_statement", None)),
                    ("5-Why", _why_summary(closure)),
                    ("Root Cause Categories", getattr(closure, "root_cause_categories", None)),
                    ("Root Cause Summary", getattr(closure, "root_cause_summary", None)),
                ]
            ),
            PageBreak(),
            *section("Part D - Corrective + Preventive Action"),
            info_table(
                [
                    ("Corrective Action", getattr(closure, "corrective_action_text", None)),
                    ("Target / Actual Dates", _target_actual(closure)),
                    ("Preventive Action", getattr(closure, "preventive_action_text", None)),
                    ("SMS Amendment", _sms_amendment(closure)),
                    ("Evidence Checklist", "Existing CAR evidence model"),
                ]
            ),
            spacer(),
            *section("Part E - Effectiveness Review"),
            info_table(
                [
                    ("Review Date", format_date(getattr(closure, "effectiveness_review_date", None))),
                    ("Method", getattr(closure, "effectiveness_review_method", None)),
                    ("Assessment", getattr(closure, "effectiveness_assessment_text", None)),
                    ("Outcome", getattr(closure, "effectiveness_outcome", None)),
                    ("Further Action", getattr(closure, "effectiveness_further_action_text", None)),
                    ("Signer", _sign_line(getattr(closure, "effectiveness_signer_name", None), getattr(closure, "effectiveness_signer_at", None))),
                ]
            ),
            spacer(),
            *section("Part F - Closure Acceptance"),
            info_table(
                [
                    ("Reviewed By", getattr(closure, "acceptance_signer_name", None)),
                    ("RCA Adequacy", getattr(closure, "acceptance_rca_adequacy_text", None)),
                    ("Decision", getattr(closure, "acceptance_decision", None)),
                    ("Return Reason", getattr(closure, "acceptance_return_reason", None)),
                ]
            ),
            spacer(),
            *section("Part G - Auditor Verification & Final Closure"),
            info_table(
                [
                    ("Verifying Auditor / Org", _verifier(closure)),
                    ("Method", getattr(closure, "verification_method", None)),
                    ("Certificate Endorsement", _certificate_endorsement(closure)),
                    ("Assessment", getattr(closure, "auditor_assessment_text", None)),
                    ("Final Closure Status", getattr(closure, "final_closure_status", None)),
                    ("Resubmit By", format_date(getattr(closure, "resubmit_by_date", None))),
                ]
            ),
            spacer(),
            signature_table(["Master / Responsible Officer Signature", "Lead Auditor Signature"]),
        ]
        return story

    content, _payload = build_pdf_with_provenance(
        story_factory,
        form_no=FORM_NO,
        filing_ref=FILING_REF,
        pdf_kind=PDF_KIND,
        audit_detail_id=audit_detail.id,
        finding_id=finding.id,
        generated_by=generated_by,
        is_draft=is_nc_pdf_draft(closure),
    )
    return AuditPdfResult(content=content, file_name=f"KSM_F_NC_001_{finding.id}.pdf")


def _deficiency_for_finding(finding: AuditFinding) -> Deficiency | None:
    return Deficiency.objects.select_related("car").filter(id=UUID(hex=finding.psc_deficiency_id)).first()


def _clause_reference(finding: AuditFinding) -> str:
    clauses = list(AuditFindingClause.objects.filter(audit_finding_id=finding.id).order_by("-is_primary", "id"))
    if clauses:
        return "; ".join(
            f"{clause.rule_book_type} {clause.clause_ref_text or clause.rule_clause_id or ''}".strip()
            for clause in clauses
        )
    return f"{finding.rule_book_type or '-'} {finding.clause_ref_text or ''}".strip()


def _sign_line(name, signed_at) -> str:
    if not name and not signed_at:
        return "-"
    return f"{name or '-'} / {format_date(signed_at)}"


def _draft_footer(closure: AuditFindingNC | None) -> str:
    if not closure or not closure.drafted_by_user_id:
        return "Not office-drafted"
    return f"Drafted by office: {closure.drafted_by_user_id} / Approved + signed by Master: {closure.master_immediate_sign_name or '-'}"


def _why_summary(closure: AuditFindingNC | None) -> str:
    if not closure:
        return "-"
    return " | ".join(
        value
        for value in [closure.why_1, closure.why_2, closure.why_3, closure.why_4, closure.why_5]
        if value
    ) or "-"


def _target_actual(closure: AuditFindingNC | None) -> str:
    if not closure:
        return "-"
    return f"{format_date(closure.target_completion_date)} / {format_date(closure.actual_completion_date)}"


def _sms_amendment(closure: AuditFindingNC | None) -> str:
    if not closure:
        return "-"
    if not closure.sms_amendment_required:
        return "No"
    return f"Yes - {closure.sms_amendment_doc_ref or '-'}"


def _verifier(closure: AuditFindingNC | None) -> str:
    if not closure:
        return "-"
    return f"{closure.verifying_auditor_name or '-'} / {closure.verifying_authority_org or '-'}"


def _certificate_endorsement(closure: AuditFindingNC | None) -> str:
    if not closure:
        return "-"
    return f"{closure.certificate_endorsement_type or '-'} / {closure.certificate_endorsement_ref or '-'}"
