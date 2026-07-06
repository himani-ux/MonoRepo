# Certs Phase 10.4 - LESSONS Loop

Current phase: Phase 10 - Post-launch hardening.
Current step: 10.4 - LESSONS loop.
Session status: IN PROGRESS.

## Plan

1. [x] Re-read AGENTS, project skill, progress, Phase 10.4 traceability, Brownfield gates, BLOCKERS, and LESSONS.
2. [x] Inventory `docsuite/LESSONS.md` for actionable implementation or repayment items.
3. [ ] Add the missing mechanical `COVERAGE.md` verifier required by `L-001`.
4. [ ] Run the verifier and record the result.
5. [ ] Record the Phase 10.4 LESSONS audit outcome in progress, Brownfield notes, and both task files.

## Current Findings

- `L-001` is actionable locally: `docsuite/COVERAGE.md` references `scripts/verify_coverage.py`, but no verifier script exists in this handover root.
- `L-027` remains a business repayment item: the prototype catalog seed defaults still require DPA/Tech Sup'tt row-by-row review/correction and cannot be repaid by code.
- `L-010` through `L-079` are mostly closeout-boundary guardrails; no additional product-code change is implied by the LESSONS inventory so far.

## Non-Actions For This Step

- No DB write, migration, seed command, live/staging mutation, notification dispatch, email send, Slack send, class snapshot upload/reparse, mapping rerun, catalog edit, reconciliation review, class portal API work, OCR threshold change, OCR fallback rule change, sibling-module integration, frontend change, or dependency change.

## Outstanding Exemptions

- `ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
- `ASSUMPTION-OVERRIDE`: Prince/DPA waived the missing VIMS Certificates Module training completion evidence for Phase 9.5 cutover sign-off on 2026-07-01.
