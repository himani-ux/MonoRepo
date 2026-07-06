# Certs Phase 9.3 - Hard Cutover / Excel Archive

Current phase: Phase 9 - Cutover.
Current step: 9.3 - Hard cutover: retire Excel registers as read-only archive.
Session status: Phase 9.1 and Phase 9.2 complete; all six vessels active.

## Plan

1. [x] Record Prince Phase 8 exit approval in `BROWNFIELD_INTEGRATION_NOTES.md`.
2. [x] Move `docsuite/progress.txt` to Phase 9.1 active.
3. [x] Identify the six cutover vessels from the actual VIMS data and existing Certs state.
4. [x] Verify read-only prerequisites available in DB: 459 active catalog rows, six real Master ship-login mappings, and office RBV users.
5. [x] B-P9-01 resolved: operational cutover package received, including per-vessel anniversary dates.
6. [x] Execute Phase 9.1 onboarding writes per vessel using implemented services only; FM sign-off intentionally deferred to Phase 9.2.
7. [x] Verify Phase 9.1 evidence: onboarding audit events, coverage override state, class snapshot parse state, and no FM sign-off.
8. [x] Update `BROWNFIELD_INTEGRATION_NOTES.md`, `docsuite/progress.txt`, and both task files with recon/write outcomes.
9. [x] Investigate B-P9-02 reconciliation blocker and fix KR parser key normalization defect.
10. [x] Apply Prince-approved high-confidence B-P9-02 mapping tranche, reparse six snapshots, and rerun reconciliation.
11. [x] Resolve residual B-P9-02 reconciliation flags and complete Phase 9.2 FM sign-off for all six vessels.
12. [ ] Next: Phase 9.3 hard cutover / Excel register archive.

## Closeout

1. [x] Archived `docsuite/LESSONS.md` to `docsuite/LESSONS-20260630-phase9-1-blocked-closeout.md`.
2. [x] Added `L-072` to `docsuite/LESSONS.md`.
3. [x] Updated `docsuite/progress.txt`.
4. [x] Updated root and monorepo task files.
5. [x] No implementation code, migrations, DB writes, seed commands, tests, live/staging mutations, operational onboarding writes, class snapshot upload, vessel certificate PDF upload, FM sign-off, notification dispatch, email send, Slack send, Excel archive action, class portal API work, OCR fallback, sibling-module integration, Phase 9.2 work, reset/re-onboarding of YC FORTITUDE, or product verification reruns were performed during this closeout-only request.

## Guardrails

- No new code, migrations, DB columns, FIELD_MAP edits, or UI changes unless Phase 9.1 reveals a documented defect.
- No sibling-module API/FK integration, class portal API, class-status OCR fallback, offline mode, phone/tablet camera capture, 2FA, break-glass, quiet hours, per-user notification preferences, or Acting-Master behavior.
- Do not start Phase 9.2 until Phase 9.1 evidence is complete.

## Current Blocker

`B-P9-01` and `B-P9-02` are RESOLVED. Phase 9.1 writes are complete, residual reconciliation flags were reviewed, latest unresolved residual count is `0`, and Phase 9.2 FM sign-off activated all six vessels. No current blocker before Phase 9.3.

## Outstanding Exemptions

`ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
