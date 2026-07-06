# Certs Phase 10 - Post-launch Hardening Ready

Current phase: Phase 10 - Post-launch hardening.
Current step: 10.1 - Parser anomaly monitoring / post-launch hardening ready.
Session status: Phase 9 cutover complete; B-P9-05 resolved by explicit `ASSUMPTION-OVERRIDE`.

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
12. [x] Resolve B-P9-05 by explicit Prince/DPA override instruction.
13. [ ] Begin Phase 10 only after re-reading Phase 10 traceability.

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

## B-P9-05 Override

- `ASSUMPTION-OVERRIDE`: Prince/DPA waived the missing VIMS Certificates Module training completion evidence for cutover sign-off.
- Residual risk: no retained VIMS Certificates Module training attendance proof exists in the handover record.
- Repay by appending actual session evidence later if available.

## Guardrails

- Do not treat `training_cert/CYM-IMDG-2026-0009.pdf` as VIMS Certificates Module training proof; it remains individual IMDG cargo training evidence.
- No new code, migrations, DB columns, FIELD_MAP edits, or UI changes unless Phase 10 work is explicitly started after re-reading its traceability.
- No DB writes, live/staging mutations, notification dispatch, email sends, Slack sends, onboarding writes, class snapshot upload/reparse, mapping reruns, catalog edits, reconciliation reviews, duplicate FM sign-off, Excel archive changes, mail-system mutation, class portal API work, OCR fallback, sibling integration, or Phase 10 work was performed during the override closeout.

## Outstanding Exemptions

- `ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
- `ASSUMPTION-OVERRIDE`: Prince/DPA waived the missing VIMS Certificates Module training completion evidence for Phase 9.5 cutover sign-off on 2026-07-01.
