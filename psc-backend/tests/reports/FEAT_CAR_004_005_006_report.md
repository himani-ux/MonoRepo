# FEATURE TEST REPORT: FEAT-CAR-004 / FEAT-CAR-005 / FEAT-CAR-006

Generated: 2026-02-07  
Test File: `psc-backend/apps/car/tests.py`  
Test Command:

```bash
python manage.py test apps.car.tests.TestFEAT_CAR_004_SubmitCAR apps.car.tests.TestFEAT_CAR_005_PICAcceptCAR apps.car.tests.TestFEAT_CAR_006_RequestCARRework --settings=core.settings_test -v 2
```

## FEAT-CAR-004 Submit CAR

PRD Reference: `Docs/PRD.md` FEAT-CAR-004  
Validation Reference: `Docs/VALIDATION_RULES.md` 4.2  
RBAC/API Reference: `Docs/BACKEND_STRUCTURE.md` 10.5, 11

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| Root cause summary min 50 chars | ✅ |
| At least 1 CLC code or custom cause | ✅ |
| At least 1 immediate action with owner and due date | ✅ |
| At least 1 long-term action with owner and due date | ✅ |
| At least 1 BEFORE evidence | ✅ |
| At least 1 AFTER evidence | ✅ |
| Status changes DRAFT → SUBMITTED | ✅ |
| Office can submit on behalf | ✅ |
| Creates activity event | ✅ |
| Triggers office notification flow | ✅ |

### Coverage Notes

- Validation coverage includes boundary and edge cases:
  - root cause exactly 50 chars is accepted
  - whitespace-only owner identifier is rejected for action owner preconditions

---

## FEAT-CAR-005 PIC Accept CAR

PRD Reference: `Docs/PRD.md` FEAT-CAR-005  
Validation Reference: `Docs/VALIDATION_RULES.md` 4.3  
RBAC/API Reference: `Docs/BACKEND_STRUCTURE.md` 10.5, 11

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| Only Office PIC/SSQE/SUPT can perform | ✅ |
| PIC comment is mandatory | ✅ |
| PIC comment minimum 10 chars | ✅ |
| Status changes SUBMITTED → PIC_ACCEPTED | ✅ |
| Creates activity event | ✅ |
| Triggers vessel notification flow | ✅ |

### Coverage Notes

- Validation coverage includes boundary and edge cases:
  - comment exactly 10 chars is accepted
  - whitespace-only comment is rejected

---

## FEAT-CAR-006 Request CAR Rework

PRD Reference: `Docs/PRD.md` FEAT-CAR-006  
Validation Reference: `Docs/VALIDATION_RULES.md` 4.4  
RBAC/API Reference: `Docs/BACKEND_STRUCTURE.md` 10.5, 11

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| Office can request from SUBMITTED | ✅ |
| DPA can request from SUBMITTED or PIC_ACCEPTED | ✅ |
| Rework reason mandatory (min 20) | ✅ |
| Status transitions to rework flow and vessel can edit again | ✅ |
| Creates activity event | ✅ |
| Triggers vessel/action-owner notification flow | ✅* |

\* Trigger path is covered by notification-function invocation tests. End-to-end recipient resolution depends on master tables not present in the test database.

---

## Test Summary

- Total tests: 44
- Passed: 44
- Failed: 0
- All targeted backend tests for FEAT-CAR-004/005/006 are passing.
- Non-failing signal log warnings in test output are expected in this suite because external master recipient tables are not present in the in-memory test database.
