# Certs Phase 10.1 - Parser Anomaly Escalation Complete

Current phase: Phase 10 - Post-launch hardening.
Current step: 10.1 - Parser anomaly notification escalation implemented.
Session status: CLOSED. B-P10-01 resolved.

## Completed

1. [x] Re-read Phase 10.1 traceability and B-P10-01.
2. [x] Added failing tests for parser anomaly notification recipient policy, cutover suppression, and dispatch payload/idempotency behavior.
3. [x] Implemented parser anomaly escalation in `apps/certs/services/reconciliation.py`.
4. [x] Suppressed reviewed cutover anomalies.
5. [x] Kept delivery office-side only: in-app + Slack, no vessel recipients, no office email.
6. [x] Updated `notifications_sent_json` when parser anomaly notification rows are created.
7. [x] Resolved B-P10-01 in `docsuite/BLOCKERS.md`.
8. [x] Updated `docsuite/progress.txt`, `docsuite/LESSONS.md`, `BROWNFIELD_INTEGRATION_NOTES.md`, and both task files.

## Verification

- `python -m unittest tests.certs.test_reconciliation -v` PASS.
- `python -m unittest tests.certs.test_reconciliation tests.certs.test_class_snapshot_api tests.certs.test_class_snapshot_parsers -v` PASS.

## Policy

- DPA receives every parser anomaly.
- Marine Sup'tt + DPA receive mismatch-rate and unmapped-rate / unmapped-critical breaches.
- Technical Sup'tt + DPA receive parse-duration and parsed-row-count shortfall breaches.
- Reviewed Phase 9 cutover anomaly runs are suppressed.

## Explicit Non-Actions

- No live DB write, migration, seed command, live/staging mutation, onboarding write, class snapshot upload/reparse, mapping rerun, catalog edit, reconciliation review, live notification dispatch, email send, Slack send, class portal API work, OCR fallback, sibling-module integration, DB column, or frontend change was performed.

## Outstanding Exemptions

- `ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
- `ASSUMPTION-OVERRIDE`: Prince/DPA waived the missing VIMS Certificates Module training completion evidence for Phase 9.5 cutover sign-off on 2026-07-01.
