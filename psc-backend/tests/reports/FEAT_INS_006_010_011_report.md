# Feature Test Report — FEAT-INS-006 / FEAT-INS-010 / FEAT-INS-011

**Date:** 2026-02-07  
**Suite:** `apps.inspection.tests.TestFEAT_INS_006_DPACloseInspection`, `TestFEAT_INS_010_ViewInspectionList`, `TestFEAT_INS_011_ViewInspectionDetail`  
**Command:**  
`python manage.py test apps.inspection.tests.TestFEAT_INS_006_DPACloseInspection apps.inspection.tests.TestFEAT_INS_010_ViewInspectionList apps.inspection.tests.TestFEAT_INS_011_ViewInspectionDetail --settings=core.settings_test -v 2`

---

## Scope

- **FEAT-INS-006** DPA Close Inspection (PRD.md §2.1, VALIDATION_RULES.md §2.4, BACKEND_STRUCTURE.md §10.3, §11)
- **FEAT-INS-010** View Inspection List (PRD.md §2.1, BACKEND_STRUCTURE.md §10.3, APP_FLOW.md Inspection List)
- **FEAT-INS-011** View Inspection Detail (PRD.md §2.1, BACKEND_STRUCTURE.md §10.3, APP_FLOW.md Inspection Detail)

---

## Summary

- **Total tests:** 29
- **Passed:** 25
- **Failed:** 4
- **Status:** Partial coverage; core flow and RBAC checks pass, four PRD gaps detected.

---

## Passing Coverage

### FEAT-INS-006 (DPA Close Inspection)
- DPA can close PIC_REVIEWED inspection
- Mandatory comment and minimum length validation
- Status precondition enforced (PIC_REVIEWED only)
- RBAC checks (Office/Vessel denied, unauthenticated denied)
- Not-found handling for missing inspection

### FEAT-INS-010 (View Inspection List)
- Vessel user visibility limited to own vessel
- Office filtering by vessel
- Filters by status, inspection type, date range
- Pagination behavior (default 20, max cap 100)
- Detention flag exposed for UI highlighting
- Unauthenticated access blocked

### FEAT-INS-011 (View Inspection Detail)
- Full detail payload returns inspection core fields + reports + deficiencies + CAR status
- Activity history included
- RBAC/visibility checks (Office and DPA allowed, other vessel denied, unauthenticated denied)
- 404 for missing inspection
- Soft-deleted inspections excluded

---

## Detected Gaps (Expected Failures)

⚠️ **AUDIT GAP (FEAT-INS-006): no activity history event on DPA close**
- **PRD says:** DPA close creates activity event.
- **Observed code:** no `INSPECTION_DPA_CLOSED` event created.
- **Failing test:** `test_gap_audit_activity_event_should_be_created_on_dpa_close`

⚠️ **NOTIFICATION GAP (FEAT-INS-006): no vessel-master notification on DPA close**
- **PRD says:** DPA close sends notification to Vessel Master.
- **Observed code:** no inspection notification record created.
- **Failing test:** `test_gap_notification_to_vessel_master_should_be_sent_on_dpa_close`

⚠️ **LIST DATA GAP (FEAT-INS-010): deficiency/open counts not populated**
- **PRD says:** list shows total deficiencies and open deficiencies.
- **Observed code:** response returns `deficiency_count=0` and `open_deficiency_count=0` even when deficiencies exist.
- **Failing test:** `test_gap_list_should_include_deficiency_and_open_counts`

⚠️ **AUDIT VISIBILITY GAP (FEAT-INS-011): audit log missing from inspection detail**
- **PRD says:** Office/DPA can see full audit log.
- **Observed code:** detail payload has no `audit_log` field.
- **Failing test:** `test_gap_office_and_dpa_should_see_audit_log_in_detail`

---

## Execution Note

- Default SQL Server test run currently fails at `token_blacklist` migration (`0008_migrate_to_bigautofield`) due DB constraint conflict.
- Functional backfill verification for this session was executed with `core.settings_test` (SQLite in-memory) to validate test behavior and capture feature gaps.

---

## Artifacts

- Test file: `psc-backend/apps/inspection/tests.py`
- Report file: `psc-backend/tests/reports/FEAT_INS_006_010_011_report.md`

---

## Addendum — 2026-02-08 (Session 39)

**Scope re-audited:** FEAT-INS-006 (strict RBAC/boundary extension)  
**Suite command:**  
`python manage.py test apps.inspection.tests.TestFEAT_INS_002_UploadInspectionReport apps.inspection.tests.TestFEAT_INS_003_AddDeficiency apps.inspection.tests.TestFEAT_INS_005_PICReviewInspection apps.inspection.tests.TestFEAT_INS_006_DPACloseInspection -v 2`

### Incremental Test Additions
- FEAT-INS-006: +3 tests
  - `test_validation_comment_minimum_boundary_accepted`
  - `test_rbac_office_ssqe_cannot_close`
  - `test_rbac_office_supt_cannot_close`

### Re-Audit Result (INS-006 class)
- Total tests: 13
- Passed: 11
- Failed: 2

### Newly Confirmed Coverage
- 10-character DPA comment boundary is accepted (VALIDATION_RULES.md §2.4).
- OFFICE_SSQE and OFFICE_SUPT are explicitly denied DPA close action.

### Gap Status
- `test_gap_audit_activity_event_should_be_created_on_dpa_close` still fails:
  no `INSPECTION_DPA_CLOSED` activity event is written.
- `test_gap_notification_to_vessel_master_should_be_sent_on_dpa_close` still fails:
  no vessel-master notification is emitted on inspection DPA close.
