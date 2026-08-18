# UAT-REPORT
report_date: 2026-08-18
repo_commit: 80154b724a8fecc8b0b6a0e8fe0ca3e1d44eef46
app_target: http://localhost:5173

Narrative prose is allowed here and carries no authority.

This report does not mark any Audit journey as passed. It records the current evidence posture after senior review: earlier narrative pass labels are not enough for ledger stamping, and the named journeys must be rerun with raw UAT evidence before they can be promoted.

## UAT-CLAIM-1: Current journey pass state is not formally verified
- journey_ids: JOURNEY-1, JOURNEY-2, JOURNEY-3, JOURNEY-4, JOURNEY-5, JOURNEY-7, JOURNEY-8, JOURNEY-9, JOURNEY-10, JOURNEY-11, JOURNEY-12, JOURNEY-13
- grade: [G]
- claim: The listed journeys cannot be treated as formally passed until each is rerun with the agreed UAT evidence package.

## UAT-CLAIM-2: NC and Observation frontend routes are registered
- journey_ids: JOURNEY-4, JOURNEY-5, JOURNEY-7, JOURNEY-8, JOURNEY-12
- grade: [C]
- claim: The frontend has specific routes for NC wizard, NC closure, and Observation closure screens.
- evidence: psc-frontend/src/App.tsx:314 — "path=\"/audit/findings/:findingId/nc/wizard\""
- evidence: psc-frontend/src/App.tsx:322 — "path=\"/audit/findings/:findingId/nc\""
- evidence: psc-frontend/src/App.tsx:330 — "path=\"/audit/findings/:findingId/obs\""

## UAT-CLAIM-3: Audit Detail exposes the findings table and specific finding links
- journey_ids: JOURNEY-3, JOURNEY-4, JOURNEY-5, JOURNEY-7, JOURNEY-8, JOURNEY-12
- grade: [C]
- claim: The Audit Detail page renders a findings table and links NC and Observation rows to their specific screens.
- evidence: psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:371 — "MOCKUP-AUDIT-02:detail.findings_table"
- evidence: psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:405 — "to={`/audit/findings/${finding.id}/nc`}"
- evidence: psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:411 — "to={`/audit/findings/${finding.id}/nc/wizard`}"
- evidence: psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:419 — "to={`/audit/findings/${finding.id}/obs`}"
- evidence: psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:661 — "NCs Raised"
- evidence: psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:665 — "Observations Raised"

## UAT-CLAIM-4: SCR-AUD-10 guard maps to canonical AUDIT_P_018
- journey_ids: JOURNEY-10
- grade: [C]
- claim: The frontend constant used for scan validation is an alias for canonical permission AUDIT_P_018.
- evidence: psc-frontend/src/App.tsx:268 — "path=\"/dpa/scan-validation-queue\""
- evidence: psc-frontend/src/lib/utils/permission-ids.ts:65 — "AUDIT_SCAN_VALIDATION: 'AUDIT_P_018'"

## UAT-CLAIM-5: JOURNEY-6 negative backend guard exists but browser evidence remains separate
- journey_ids: JOURNEY-6
- grade: [C]
- claim: The backend regression test asserts that a Lead Auditor cannot claim PIC review on their own audit and receives the uppercase backend error code.
- evidence: psc-backend/tests/audit/test_car_workflow_proxy.py:341 — "test_lead_auditor_cannot_claim_pic_review_on_own_audit"
- evidence: psc-backend/tests/audit/test_car_workflow_proxy.py:353 — "self.assertEqual(response.status_code, 403)"
- evidence: psc-backend/tests/audit/test_car_workflow_proxy.py:354 — "LEAD_AUDITOR_PIC_DENIED"
