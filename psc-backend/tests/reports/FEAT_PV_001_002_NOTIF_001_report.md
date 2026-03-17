# FEATURE TEST REPORT: FEAT-PV-001 / FEAT-PV-002 / FEAT-NOTIF-001

Generated: 2026-02-07  
Test run: `python manage.py test apps.car.tests.TestFEAT_PV_001_CreatePhysicalVerification apps.car.tests.TestFEAT_PV_002_ClosePhysicalVerification apps.notifications.tests --settings=core.settings_test -v 2`

## Scope

- `FEAT-PV-001` Create Physical Verification (`Docs/PRD.md` §2.4, `Docs/VALIDATION_RULES.md` §7.1, `Docs/BACKEND_STRUCTURE.md` §10.8/§11.1)
- `FEAT-PV-002` Close Physical Verification (`Docs/PRD.md` §2.4, `Docs/VALIDATION_RULES.md` §7.2, `Docs/BACKEND_STRUCTURE.md` §10.8/§11.1)
- `FEAT-NOTIF-001` In-App Notifications (`Docs/PRD.md` §2.7, `Docs/BACKEND_STRUCTURE.md` §10.11)

## Test Artifacts

- Updated: `psc-backend/apps/car/tests.py`
  - `TestFEAT_PV_001_CreatePhysicalVerification` (6 tests)
  - `TestFEAT_PV_002_ClosePhysicalVerification` (8 tests)
- Added: `psc-backend/apps/notifications/tests.py`
  - API endpoint coverage + signal trigger coverage + overdue rule coverage (16 tests)

## Result Summary

- Total tests: 30
- Passed: 28
- Failed: 2

## Acceptance Coverage Snapshot

### FEAT-PV-001 Create Physical Verification

- ✅ Created only for `DPA_CLOSED` CAR
- ✅ Created in `OPEN` status
- ✅ Optional `visit_port` and `verifier_user_id` accepted
- ✅ RBAC checks (office/DPA allowed, vessel rejected)
- ✅ Activity event + notification hook on success
- ⚠️ Gap test failing: duplicate OPEN PV allowed for same CAR

### FEAT-PV-002 Close Physical Verification

- ✅ Assigned verifier can close
- ✅ DPA can close regardless of assignment
- ✅ Comment min-length and required visit-date validated
- ✅ State precondition: only OPEN can close
- ✅ 404 behavior for unknown PV
- ⚠️ Gap test failing: future `visit_date` is accepted

### FEAT-NOTIF-001 In-App Notifications (Backend Scope)

- ✅ List/mark-read/mark-all-read endpoints covered with recipient scoping, filtering, pagination, payload validation
- ✅ Trigger helpers covered:
  - `CAR_CREATED`
  - `CAR_SUBMITTED`
  - `CAR_PIC_ACCEPTED`
  - `CAR_REWORK_REQUESTED`
  - `CAR_DPA_CLOSED`
  - `PSC_FOLLOW_UP_RECORDED`
  - `CONFLICT_DETECTED`
  - `CONFLICT_RESOLVED`
  - `PHYSICAL_VERIFICATION_CREATED`
  - `ACTION_OVERDUE_WARNING`
  - `ACTION_OVERDUE`

## Gap Log

1. `FEAT-PV-001` / `VALIDATION_RULES.md §7.1`  
   Expected: reject creation when an OPEN physical verification already exists for the CAR.  
   Actual: API returns `201` and creates a second OPEN record.

2. `FEAT-PV-002` / `VALIDATION_RULES.md §7.2`  
   Expected: reject future `visit_date`.  
   Actual: API returns `200` and closes verification with future date.
