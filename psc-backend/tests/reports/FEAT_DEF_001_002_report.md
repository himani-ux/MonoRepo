# Feature Test Report — FEAT-DEF-001 / FEAT-DEF-002

**Date:** 2026-02-07  
**Suite:** `apps.inspection.tests.TestFEAT_DEF_001_UpdateActionCode`, `apps.inspection.tests.TestFEAT_DEF_002_RegisterPSCFollowUp`  
**Command:**  
`python manage.py test apps.inspection.tests.TestFEAT_DEF_001_UpdateActionCode apps.inspection.tests.TestFEAT_DEF_002_RegisterPSCFollowUp --settings=core.settings_test -v 2`

---

## Scope

- **FEAT-DEF-001** Update Action Code (PRD.md FEAT-DEF-001, VALIDATION_RULES.md §3.2, BACKEND_STRUCTURE.md §10.4, §11)
- **FEAT-DEF-002** Register PSC Follow-up (PRD.md FEAT-DEF-002, VALIDATION_RULES.md §2.1/§3.2, BACKEND_STRUCTURE.md §10.4, §11)

---

## Summary

- **Total tests:** 25
- **Passed:** 25
- **Failed:** 0
- **Status:** Complete coverage for FEAT-DEF-001 and FEAT-DEF-002 in current backend scope.

---

## Passing Coverage

### FEAT-DEF-001 (Update Action Code)
- Vessel Master can update deficiency action code.
- Transition from action code 30 to other codes is accepted.
- Transition to action code 10 marks deficiency as cleared.
- Update can be linked to a follow-up inspection.
- Deficiency action history rows are created with previous/new action data.
- Validation coverage: required `action_code_id`, invalid `action_code_id`, invalid follow-up id, max length `change_reason`.
- RBAC coverage: crew denied, office denied, cross-vessel denied, unauthenticated denied.
- Missing deficiency returns 404.

### FEAT-DEF-002 (Register PSC Follow-up)
- Creates linked follow-up inspection with `inspection_type=PSC`, `psc_subtype=FOLLOW_UP`, `status=SUBMITTED`.
- Inherits parent MOU and stores follow-up metadata (date, port, authority, etc.).
- Batch deficiency updates are supported.
- Batch update creates deficiency action-history records.
- Action code 10 auto-clears deficiencies; non-clearing codes do not.
- Follow-up notification hook is triggered.
- Validation coverage: parent must be PSC, date not before parent, deficiency must belong to parent, invalid action code, required fields.
- RBAC coverage: only Vessel Master allowed.
- Validation error payload format verified.

---

## Gap Closure Verification

✅ **FEAT-DEF-001 validation fixed**
- `follow_up_inspection_id` now requires a PSC inspection with subtype `FOLLOW_UP`.
- Verified by: `test_gap_follow_up_inspection_should_be_follow_up_type` (now passing)

✅ **FEAT-DEF-002 activity history fixed**
- Follow-up registration now creates `ActivityHistory` with event type `PSC_FOLLOW_UP_RECORDED`.
- Verified by: `test_gap_follow_up_registration_should_create_activity_event` (now passing)

---

## Execution Note

- During SQLite test execution, notification helper logs table-missing warnings for unmanaged reference tables (`master_RoleByVessel`, `HRM501`), but test flow continues as expected under `core.settings_test`.

---

## Artifacts

- Test file: `psc-backend/apps/inspection/tests.py`
- Report file: `psc-backend/tests/reports/FEAT_DEF_001_002_report.md`
