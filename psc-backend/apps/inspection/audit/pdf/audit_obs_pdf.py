"""KSM-F-OBS-001 Observation closure PDF generator."""

from __future__ import annotations

from apps.inspection.audit.models import AuditDetail, AuditFinding, AuditFindingOBS
from apps.inspection.audit.pdf.audit_nc_pdf import _clause_reference, _deficiency_for_finding, _sign_line
from apps.inspection.audit.pdf.audit_plan_pdf import _inspection_for_detail
from apps.inspection.audit.pdf.common import (
    AuditPdfResult,
    build_pdf_with_provenance,
    format_date,
    info_table,
    is_obs_pdf_draft,
    section,
    signature_table,
    sms_header,
    spacer,
)


FORM_NO = "KSM-F-OBS-001"
REVISION = "Rev 01 Jan-2026"
FILING_REF = "A-28"
PDF_KIND = "KSM_F_OBS_001"


def generate_audit_obs_pdf(finding: AuditFinding, *, generated_by=None) -> AuditPdfResult:
    audit_detail = AuditDetail.objects.get(id=finding.audit_detail_id)
    inspection = _inspection_for_detail(audit_detail)
    deficiency = _deficiency_for_finding(finding)
    car = getattr(deficiency, "car", None) if deficiency else None
    closure = AuditFindingOBS.objects.filter(audit_finding_id=finding.id).first()

    def story_factory() -> list:
        story = [
            *sms_header(FORM_NO, REVISION, FILING_REF, "KSM-F-OBS-001 - Observation Closure Form"),
            *section("Part A - Observation Details"),
            info_table(
                [
                    ("Observation Ref. No.", getattr(car, "car_number", None)),
                    ("Date of Audit", format_date(inspection.inspection_date)),
                    ("Vessel / Department", audit_detail.auditee_office_dept or f"Vessel {inspection.vessel_id}"),
                    ("Auditor", f"{audit_detail.lead_auditor_name} / {audit_detail.lead_auditor_company}"),
                    ("SMS / Regulatory Ref", _clause_reference(finding)),
                    ("Observation Category", finding.observation_category),
                    ("Observation Description", finding.description or getattr(deficiency, "description", None)),
                ]
            ),
            spacer(),
            *section("Part B - Vessel / Department Response"),
            info_table(
                [
                    ("Responded By", _responder(closure)),
                    ("Target Closure Date", format_date(getattr(closure, "target_closure_date", None))),
                    ("Immediate Action", getattr(closure, "immediate_action_text", None)),
                    ("Root Cause", getattr(closure, "root_cause_text", None)),
                    ("Corrective Action", getattr(closure, "corrective_action_text", None)),
                    ("Preventive Action", getattr(closure, "preventive_action_text", None)),
                    ("SMS Amendment", _sms_amendment(closure)),
                    ("Actual Closure Date", format_date(getattr(closure, "actual_closure_date", None))),
                    ("Master / HoD Sign", _sign_line(getattr(closure, "master_sign_name", None), getattr(closure, "master_sign_at", None))),
                ]
            ),
            spacer(),
            *section("Part C - DPA Office Review & Acceptance"),
            info_table(
                [
                    ("Review Date", format_date(getattr(closure, "acceptance_review_date", None))),
                    ("Adequacy", getattr(closure, "acceptance_adequacy_text", None)),
                    ("Decision", getattr(closure, "acceptance_decision", None)),
                    ("Return Reason", getattr(closure, "acceptance_return_reason", None)),
                    ("Signer", _sign_line(getattr(closure, "acceptance_signer_name", None), getattr(closure, "acceptance_signer_at", None))),
                ]
            ),
            spacer(),
            *section("Part D - Auditor Verification & Closure Confirmation"),
            info_table(
                [
                    ("Verifying Auditor / Org", _verifier(closure)),
                    ("Method", getattr(closure, "verification_method", None)),
                    ("Auditor Remarks", getattr(closure, "auditor_remarks_text", None)),
                    ("Closure Status", getattr(closure, "closure_status", None)),
                    ("Resubmit By", format_date(getattr(closure, "resubmit_by_date", None))),
                ]
            ),
            spacer(),
            signature_table(["Master / HoD Signature", "Auditor Signature"]),
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
        is_draft=is_obs_pdf_draft(closure),
    )
    return AuditPdfResult(content=content, file_name=f"KSM_F_OBS_001_{finding.id}.pdf")


def _responder(closure: AuditFindingOBS | None) -> str:
    if not closure:
        return "-"
    return f"{closure.responded_by_name or '-'} / {closure.responded_by_rank or '-'}"


def _sms_amendment(closure: AuditFindingOBS | None) -> str:
    if not closure:
        return "-"
    if not closure.sms_amendment_required:
        return "No"
    return f"Yes - {closure.sms_amendment_doc_ref or '-'}"


def _verifier(closure: AuditFindingOBS | None) -> str:
    if not closure:
        return "-"
    return f"{closure.verifying_auditor_name or '-'} / {closure.verifying_authority_org or '-'}"
