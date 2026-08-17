# Mock coverage gaps

Structured gap records for AFJ-touched screens deliberately shipped without a mock,
per the mock-contract gap grammar (`mocks/bin/check-mock-coverage.sh` Part 6).
Owner ruling 2026-07-13: SCR-AUD-11/12/13 got agent-authored DRAFT mocks instead
of gap records. Prince approved those three mocks as reference on 2026-08-14;
see `docs/MOCK_APPROVAL.md`. Only the reused-screen case below remains a gap.

## MOCK-GAP: SCR-AUD-14 — "auditor_pre_audit_dashboard"
  reason: existing production PSC deficiencies screen (`/deficiencies`) reused unchanged with a vessel filter (D-AUDRS-037) — no new UI is built for v1.0, so there is no new surface to mock; the screen derives P0 only because AFJ-2 step 1 passes through it
  owner: product-owner
  reviewer: PENDING-PRINCE
  expires: 2026-10-11
