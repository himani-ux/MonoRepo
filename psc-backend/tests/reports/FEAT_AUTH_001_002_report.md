# FEATURE TEST REPORT: FEAT-AUTH-001, FEAT-AUTH-002

Generated: 2026-02-07  
Test File: `psc-backend/apps/accounts/tests.py`

## Summary
- Total tests: 12
- Passed: 12
- Failed: 0

## Coverage Snapshot
- FEAT-AUTH-001 (User Authentication): login success/failure flows, request validation, JWT refresh flow, logout blacklist path, current-user JWT claims surface
- FEAT-AUTH-002 (RBAC): protected endpoint rejection for unauthenticated requests, vessel own-vessel visibility enforcement, DPA global visibility, unauthorized action denial with 403, office-only access gate on sync conflict resolution

## Notes
- Coverage in this pass is backend-focused and centered on auth contract + role gate behavior.
- Additional deep cross-module RBAC permutations are already covered in feature-specific suites (`apps/inspection/tests.py`, `apps/car/tests.py`, `apps/sync/tests.py`).
