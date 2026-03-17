# Feature Test Report — FEAT-SYNC-005 / FEAT-CAR-008 / FEAT-RPT-001

**Date:** 2026-02-08  
**Scope:** Backend feature backfill traceability for completed features previously linked by `Coverage:` notes only.

---

## FEAT-SYNC-005 Conflict Resolution

- Status: COMPLETE (10 tests, green)
- Test location: `psc-backend/apps/sync/tests.py`
- Coverage summary:
  - Resolution validation enforced (`KEEP_SERVER`, `KEEP_VESSEL`, `REOPEN_FOR_MERGE`)
  - Conflict resolution status transitions verified
  - End-to-end conflict resolution flows verified on isolated test DB session

---

## FEAT-CAR-008 Reopen Closed CAR

- Status: COMPLETE (10 tests, green)
- Test class: `psc-backend/apps/car/tests.py::TestFEAT_CAR_008_ReopenClosedCAR`
- Coverage summary:
  - Valid status transition `DPA_CLOSED -> REWORK_REQUESTED`
  - Reopen audit log side effect
  - RBAC and invalid-state handling
  - Regression guard for test-helper falsy-dict issue

---

## FEAT-RPT-001 CAR PDF Export

- Status: COMPLETE (10 tests, green after section/logo assertion extension)
- Test class: `psc-backend/apps/car/tests.py::TestFEAT_RPT_001_CARPDFExport`
- Coverage summary:
  - Export endpoint returns downloadable valid PDF (`application/pdf`)
  - A4 page size generation
  - Full section completeness assertions in generated PDF:
    - CAR Information
    - Deficiency Details
    - Root Cause Analysis
    - Corrective Actions
    - Evidence
    - Review / Approval History
    - Physical Verification (when present)
  - Header-logo criterion regression guard:
    - Placeholder text `"[Company Logo]"` is not rendered
  - RBAC + not-found behavior

---

## Notes

- This report is added to close feature-report traceability gaps in `Docs/test_progress.txt` for these three completed features.
