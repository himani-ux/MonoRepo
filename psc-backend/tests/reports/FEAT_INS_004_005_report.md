# Feature Test Report — FEAT-INS-004 / FEAT-INS-005

**Date:** 2026-02-07  
**Suite:** `apps.inspection.tests.TestFEAT_INS_004_SubmitInspection`, `apps.inspection.tests.TestFEAT_INS_005_PICReviewInspection`  
**Command:**  
`python manage.py test apps.inspection.tests.TestFEAT_INS_004_SubmitInspection apps.inspection.tests.TestFEAT_INS_005_PICReviewInspection -v 1 --settings=core.settings_test`

---

## Scope

- **FEAT-INS-004** Submit Inspection (PRD.md FEAT-INS-004, VALIDATION_RULES.md §2.2, BACKEND_STRUCTURE.md §10.3, §11)
- **FEAT-INS-005** PIC Review Inspection (PRD.md FEAT-INS-005, VALIDATION_RULES.md §2.3, BACKEND_STRUCTURE.md §10.3, §11)

---

## Summary

- **Total tests:** 21
- **Passed:** 17
- **Failed:** 4
- **Status:** Partial coverage; happy path and most precondition/RBAC checks pass, with 4 implementation gaps detected.

---

## Passing Coverage

### FEAT-INS-004 (Submit Inspection)
- Happy path submit by Vessel Master (DRAFT + report attached)
- Office submit on behalf (OFFICE_PIC and DPA)
- Preconditions: requires report attachment
- Status precondition enforcement (only DRAFT allowed)
- Access controls: cross-vessel vessel user blocked, unauthenticated request blocked

### FEAT-INS-005 (PIC Review Inspection)
- Happy path review by OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
- Validation: comment required and minimum length enforced
- Preconditions: status must be SUBMITTED
- RBAC: Vessel Master and DPA blocked from PIC review
- Not found handling for missing inspection ID

---

## Detected Gaps (Expected Failures)

⚠️ **RBAC GAP (FEAT-INS-004): VESSEL_CREW can submit inspections**
- **PRD / RBAC says:** only VESSEL_MASTER + OFFICE_* may submit.
- **Observed code:** VESSEL_CREW submission returns 200.
- **Failing test:** `test_gap_rbac_vessel_crew_should_not_submit`

⚠️ **VALIDATION GAP (FEAT-INS-004): deficiency without CAR does not block submit**
- **PRD says:** all deficiencies must have associated CARs before submit.
- **Observed code:** submit succeeds (200) with deficiency `car=None`.
- **Failing test:** `test_gap_validation_all_deficiencies_must_have_car_before_submit`

⚠️ **AUDIT GAP (FEAT-INS-004): no activity event on submit**
- **PRD / backend schema says:** activity history event should be created.
- **Observed code:** no `INSPECTION_SUBMITTED` event created.
- **Failing test:** `test_gap_audit_activity_event_should_be_created_on_submit`

⚠️ **AUDIT GAP (FEAT-INS-005): no activity event on PIC review**
- **PRD / backend schema says:** activity history event should be created.
- **Observed code:** no `INSPECTION_PIC_REVIEWED` event created.
- **Failing test:** `test_gap_audit_activity_event_should_be_created_on_pic_review`

---

## Artifacts

- Test file: `psc-backend/apps/inspection/tests.py`
- Report file: `psc-backend/tests/reports/FEAT_INS_004_005_report.md`

---

## Recommendation (Next Session)

1. Implement submit/review RBAC and activity-event gap fixes for FEAT-INS-004/005.
2. Re-run FEAT-INS-001 through FEAT-INS-005 test suites.
3. Start FEAT-INS-006 backfill after inspection flow baseline is stable.

---

## Addendum — 2026-02-08 (Session 39)

**Scope re-audited:** FEAT-INS-005 (strict boundary extension)  
**Suite command:**  
`python manage.py test apps.inspection.tests.TestFEAT_INS_002_UploadInspectionReport apps.inspection.tests.TestFEAT_INS_003_AddDeficiency apps.inspection.tests.TestFEAT_INS_005_PICReviewInspection apps.inspection.tests.TestFEAT_INS_006_DPACloseInspection -v 2`

### Incremental Test Additions
- FEAT-INS-005: +1 test
  - `test_validation_comment_minimum_boundary_accepted`

### Re-Audit Result (INS-005 class)
- Total tests: 12
- Passed: 11
- Failed: 1

### Newly Confirmed Coverage
- 10-character PIC comment boundary is accepted (VALIDATION_RULES.md §2.3).

### Gap Status
- `test_gap_audit_activity_event_should_be_created_on_pic_review` still fails:
  no `INSPECTION_PIC_REVIEWED` activity history event is created by the current view implementation.
