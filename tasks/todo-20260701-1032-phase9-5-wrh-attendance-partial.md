# Certs Phase 9.5 - Training Session Blocked

Current phase: Phase 9 - Cutover.
Current step: 9.5 - Training session for office + sea staff.
Session status: BLOCKED on `docsuite/BLOCKERS.md` B-P9-05.

## Plan

1. [x] Re-read Phase 9.5 traceability and Brownfield gates.
2. [x] Confirm Phase 9.5 content source is `docsuite/USER_GUIDE.md`.
3. [x] Confirm walkthrough scope is all APP_FLOW screens 3.1 through 3.20.
4. [x] Confirm no backend, FIELD_MAP, SECURITY, or OBSERVABILITY runtime surface exists for Phase 9.5.
5. [x] Open B-P9-05 because the training completion evidence package is not specified.
6. [x] Update `BROWNFIELD_INTEGRATION_NOTES.md`, `docsuite/progress.txt`, and both task files.
7. [ ] BLOCKED: Prince/DPA must provide the Phase 9.5 operational training completion package before Phase 9.5 can be completed.

## Required B-P9-05 Package

- Training date/time and timezone.
- Trainer/facilitator.
- Office attendee scope.
- Sea-staff attendee scope per vessel.
- Attendance evidence type: signed sheet, screenshots, meeting minutes, or equivalent.
- Evidence retention path.
- Whether Codex should only record a completed live session or also prepare a training pack from `docsuite/USER_GUIDE.md`.

## Guardrails

- Do not mark Phase 9.5 complete without the B-P9-05 package.
- No new code, migrations, DB columns, FIELD_MAP edits, or UI changes unless Phase 9.5 reveals a documented defect.
- No DB writes, live/staging mutations, notification dispatch, email sends, Slack sends, onboarding writes, class snapshot upload/reparse, mapping reruns, catalog edits, reconciliation reviews, duplicate FM sign-off, Excel archive changes, mail-system mutation, class portal API work, OCR fallback, sibling integration, or Phase 10 work while blocked.

## Outstanding Exemptions

`ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
