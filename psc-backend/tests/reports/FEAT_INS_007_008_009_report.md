# Feature Test Report — FEAT-INS-007 / FEAT-INS-008 / FEAT-INS-009

**Date:** 2026-02-07  
**Suite:** `apps.inspection.tests.TestFEAT_INS_007_EditInspectionDraft`, `apps.inspection.tests.TestFEAT_INS_008_EditInspectionPostSubmit`, `apps.inspection.tests.TestFEAT_INS_009_DeleteDraftInspection`  
**Command:**  
`python manage.py test apps.inspection.tests.TestFEAT_INS_007_EditInspectionDraft apps.inspection.tests.TestFEAT_INS_008_EditInspectionPostSubmit apps.inspection.tests.TestFEAT_INS_009_DeleteDraftInspection --settings=core.settings_test -v 2`

---

## Scope

- **FEAT-INS-007** Edit Inspection (Draft) (PRD.md FEAT-INS-007, BACKEND_STRUCTURE.md §10.3, §11)
- **FEAT-INS-008** Edit Inspection (Post-Submit) (PRD.md FEAT-INS-008, BACKEND_STRUCTURE.md §10.3, §11)
- **FEAT-INS-009** Delete Draft Inspection (PRD.md FEAT-INS-009, VALIDATION_RULES.md §2.5, BACKEND_STRUCTURE.md §10.3, §11)

---

## Summary

- **Total tests:** 25
- **Passed:** 21
- **Failed:** 4
- **Status:** Partial coverage with clear implementation gaps identified.

---

## Passing Coverage

### FEAT-INS-007 (Edit Inspection Draft)
- Vessel Master can edit draft inspections
- Office edit-assist on draft works
- PSC subtype validation still enforced on update
- Vessel-master draft-only restriction enforced
- Crew/unauthenticated/cross-vessel access blocked

### FEAT-INS-008 (Edit Inspection Post-Submit)
- Office can edit submitted inspections
- DPA can edit PIC-reviewed inspections
- Vessel roles cannot edit post-submit states
- Existing subtype validation still enforced
- Not-found and unauthenticated handling verified

### FEAT-INS-009 (Delete Draft Inspection)
- Vessel Master can soft-delete draft inspection
- Non-draft delete blocked
- Office/Crew/cross-vessel/unauthenticated delete blocked
- Not-found behavior verified

---

## Detected Gaps (Expected Failures)

⚠️ **AUDIT GAP (FEAT-INS-007): no office edit-assist audit log**
- **PRD says:** office edit-assist should be logged separately.
- **Observed code:** no `AuditLog` row created for inspection update.
- **Failing test:** `test_feat_ins_007_gap_office_edit_assist_should_create_audit_log`

⚠️ **REVISION GAP (FEAT-INS-008): revision_no not incremented on post-submit edit**
- **PRD says:** post-submit edit increments `revision_no`.
- **Observed code:** `revision_no` remains unchanged.
- **Failing test:** `test_feat_ins_008_gap_revision_no_should_increment_on_post_submit_edit`

⚠️ **AUDIT GAP (FEAT-INS-008): no field-level audit log for post-submit edit**
- **PRD says:** full audit log of post-submit changes.
- **Observed code:** no inspection `AuditLog` created on update.
- **Failing test:** `test_feat_ins_008_gap_post_submit_edit_should_create_audit_log`

⚠️ **CASCADE DELETE GAP (FEAT-INS-009): related deficiency/CAR not soft-deleted**
- **PRD says:** deleting draft inspection also soft-deletes associated deficiencies and CARs.
- **Observed code:** inspection soft-delete does not cascade soft-delete flags to related records.
- **Failing test:** `test_feat_ins_009_gap_delete_should_soft_delete_related_deficiencies_and_car`

---

## Artifacts

- Test file: `psc-backend/apps/inspection/tests.py`
- Report file: `psc-backend/tests/reports/FEAT_INS_007_008_009_report.md`
