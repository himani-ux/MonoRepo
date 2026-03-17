# FEATURE TEST REPORT: FEAT-HIST-001, FEAT-HIST-002

Generated: 2026-02-07  
Test Files:
- `psc-backend/apps/car/tests.py`
- `psc-backend/apps/sync/tests.py`

## Summary
- Total tests: 7
- Passed: 6
- Failed: 1 (gap-detection failure)

## Coverage Snapshot
- FEAT-HIST-001 (Activity History): CAR detail timeline visibility for vessel/crew/office users, status-transition event payload checks, sync pull inclusion of activity history for offline vessel clients
- FEAT-HIST-002 (Full Audit Log): office/DPA audit-log visibility with field-level old/new values and role/edit-assist metadata, vessel-side audit-log suppression, sync pull exclusion of audit logs

## Gap-Detection Failures (Expected)
1. CAR detail history currently excludes `EVIDENCE_UPLOADED` and `ACTION_COMPLETED` events because detail serializer filters activity to `entity_type='CAR'` only.
