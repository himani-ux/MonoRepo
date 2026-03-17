# FEATURE TEST REPORT: FEAT-CAR-001 / FEAT-CAR-002 / FEAT-CAR-003

Generated: 2026-02-07  
Test File: `psc-backend/apps/car/tests.py`  
Test Command:

```bash
python manage.py test apps.car.tests.TestFEAT_CAR_001_AutoCreateCAR apps.car.tests.TestFEAT_CAR_002_EditCARDraft apps.car.tests.TestFEAT_CAR_003_UploadCAREvidence --settings=core.settings_test -v 2
```

## FEAT-CAR-001 Auto-Create CAR from Deficiency

PRD Reference: `Docs/PRD.md` FEAT-CAR-001  
Validation Reference: `Docs/VALIDATION_RULES.md` 11.2 (1:1 deficiency-CAR rule)

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| Triggered automatically on deficiency insert | ✅ |
| CAR number format SOURCE-YYYY-NNN | ✅ |
| CAR created in DRAFT status | ✅ |
| No manual CAR creation allowed | ✅ |
| Target date defaults to deficiency target or +7 days | ⚠️ GAP |

### Gap Details

- `CAR.target_date` remains `NULL` during auto-create flow.
- No `CAR_CREATED` activity history event is created on auto-create.

---

## FEAT-CAR-002 Edit CAR (Draft)

PRD Reference: `Docs/PRD.md` FEAT-CAR-002  
Validation Reference: `Docs/VALIDATION_RULES.md` 4.1

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| Root cause summary editable | ✅ |
| CLC multi-select mapping supported | ✅ |
| Custom cause text supported | ✅ |
| Office edit-assist allowed | ✅ |
| Office edit-assist does not notify vessel | ✅ |
| Immediate and long-term actions can be added | ✅ |
| Target date must be today/future | ✅ |
| CLC items must exist in master | ✅ |
| Each action has owner and due date | ✅ |

### Gap Details

- None for FEAT-CAR-002 after 2026-02-07 gap fix.

---

## FEAT-CAR-003 Upload CAR Evidence

PRD Reference: `Docs/PRD.md` FEAT-CAR-003  
Validation Reference: `Docs/VALIDATION_RULES.md` 6.1  
RBAC Reference: `Docs/BACKEND_STRUCTURE.md` 11.1

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| Evidence types BEFORE/AFTER/EVIDENCE/OTHER | ✅ |
| File formats PDF/JPG/JPEG only | ✅ |
| Max file size 3MB | ✅ |
| Description mandatory | ✅ |
| Upload creates activity event | ✅ |
| At least 1 BEFORE and AFTER required for submission | ✅ |
| Crew can upload only for assigned actions | ✅ |
| Works offline with upload queue (frontend behavior) | ⏳ FE |

### Gap Details

- None for FEAT-CAR-003 backend after 2026-02-07 RBAC gap fix.

---

## Test Summary

- Total tests: 27
- Passed: 24
- Failed: 3
- Remaining failures are FEAT-CAR-001 gap-detection checks (target_date default + CAR_CREATED activity event).
