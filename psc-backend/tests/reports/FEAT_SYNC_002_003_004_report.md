# FEATURE TEST REPORT: FEAT-SYNC-002, FEAT-SYNC-003, FEAT-SYNC-004

Generated: 2026-02-07  
Test File: `psc-backend/apps/sync/tests.py`

## Summary
- Total tests: 30
- Passed: 24
- Failed: 6 (gap-detection failures)

## Coverage Snapshot
- FEAT-SYNC-002 (Sync Pull): happy path, RBAC, deleted-record sync, sync token updates, response-shape gap checks
- FEAT-SYNC-003 (Sync Push): event ordering, idempotency behavior, attachment upload URL flow, partial failure handling, RBAC, serializer validation, sync validation gap checks
- FEAT-SYNC-004 (Conflict Detection): stale-version conflict creation, conflicting-field capture, conflict queue/log behavior, vessel notification trigger, conflict list visibility rules

## Gap-Detection Failures (Expected)
1. Pull response is missing `data.masters` (PRD FEAT-SYNC-002).
2. Push does not reject invalid/mismatched checksum (VALIDATION_RULES 9.1).
3. Push does not reject `client_version < 1` (VALIDATION_RULES 9.1).
4. Push does not enforce unique `event_id` within a sync request (VALIDATION_RULES 9.1).
5. Push does not enforce max 100 events per request (VALIDATION_RULES 9.1).
6. Push does not reject future event `timestamp` (VALIDATION_RULES 9.1).
