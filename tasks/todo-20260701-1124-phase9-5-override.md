# Certs Phase 9.5 - Training Session Blocked

Current phase: Phase 9 - Cutover.
Current step: 9.5 - Training session for office + sea staff.
Session status: BLOCKED on `docsuite/BLOCKERS.md` B-P9-05; VIMS base office/ship role scope is resolved.

## Plan

1. [x] Re-read Phase 9.5 traceability and Brownfield gates.
2. [x] Confirm Phase 9.5 content source is `docsuite/USER_GUIDE.md`.
3. [x] Confirm walkthrough scope is all APP_FLOW screens 3.1 through 3.20.
4. [x] Confirm no backend, FIELD_MAP, SECURITY, or OBSERVABILITY runtime surface exists for Phase 9.5.
5. [x] Open B-P9-05 because the training completion evidence package is not specified.
6. [x] Update `BROWNFIELD_INTEGRATION_NOTES.md`, `docsuite/progress.txt`, and both task files.
7. [x] Record Prince's instruction to refer to WRH tables for attendance/sea-staff coverage.
8. [x] Verify SQL Server schema: no dedicated `wrh_*attendance*` or `wrh_*training*` table exists.
9. [x] Record WRH/current-onboard roster source and current active-vessel onboard counts.
10. [x] Review `training_cert/CYM-IMDG-2026-0009.pdf` and record why it is not sufficient Phase 9.5 evidence.
11. [x] Resolve office and ship role references from the existing VIMS base module.
12. [ ] BLOCKED: Prince/DPA must provide the remaining VIMS Certificates Module training evidence before Phase 9.5 can be completed.

## Partial B-P9-05 Answer

- Sea-staff roster source: `Crew_Onboarding_History` current onboard windows joined to active Certs vessels in `VesselData` / `vims_certs_vessel_config`, with crew identity/rank from `HRM501`.
- WRH corroboration where present: `wrh_s521_plan`, `wrh_s521_crew_plan`, `wrh_s520_month`, `wrh_s520_day_entry`.
- Current active Certs vessel onboard counts: EAST AYUTTHAYA 22, EAST BANGKOK 23, SF CHALISA 23, SF DARIKA 23, SFYC ARAYA 23, YC FORTITUDE 23.
- These sources define sea-staff scope only; they do not prove a Certs training session occurred.

## Evidence Reviewed

- `training_cert/CYM-IMDG-2026-0009.pdf` was reviewed in `docsuite/PHASE9_5_TRAINING_CERT_REVIEW_20260701.md`.
- Decision: not sufficient for Phase 9.5. It is individual IMDG cargo training for Aditya L, not VIMS Certificates Module training for office + sea staff.

## Base Role Scope

- Office roles are sourced from `msc_profiles`, `master_role`, `master_RoleByVessel`, and `users`: SEQ Manager / DPA-equivalent, Fleet Manager, Marine Superintendent, Technical Manager, Technical Superintendent.
- Ship roles are sourced from `Ship_UsersLogin`, current onboard rows, `HRM501`, `master_applied_rank`, and ship-side `msc_profiles`: MASTER, CHIEF OFFICER, CHIEF ENGINEER, SECOND ENGINEER, plus all active onboard ranks with `CERT_F_002` when training covers all sea staff.

## Required B-P9-05 Package

- VIMS Certificates Module training title.
- VIMS Certificates Module training date/time and timezone.
- Trainer/facilitator if not evident in the proof.
- Completion/attendance proof path for the VIMS Certificates Module session.
- Evidence retention path.
- Whether Codex should only record a completed live session or also prepare a training pack from `docsuite/USER_GUIDE.md`.

## Guardrails

- Do not mark Phase 9.5 complete without the B-P9-05 package.
- No new code, migrations, DB columns, FIELD_MAP edits, or UI changes unless Phase 9.5 reveals a documented defect.
- No DB writes, live/staging mutations, notification dispatch, email sends, Slack sends, onboarding writes, class snapshot upload/reparse, mapping reruns, catalog edits, reconciliation reviews, duplicate FM sign-off, Excel archive changes, mail-system mutation, class portal API work, OCR fallback, sibling integration, or Phase 10 work while blocked.

## Outstanding Exemptions

`ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
