# Certs Phase 10.3 - Slack Routing Refinement

Current phase: Phase 10 - Post-launch hardening.
Current step: 10.3 - Slack routing refinement.
Session status: IN PROGRESS.

## Plan

1. [x] Re-read AGENTS.md, project skill, CLAUDE.md startup rules, progress EOF marker, Phase 10.3 traceability, BLOCKERS, Brownfield gates, and notification/security/observability surfaces.
2. [x] Add test-first coverage for office Slack routing refinement.
3. [x] Implement office Slack fallback routing to the confirmed DPA / TM / Marine office channels while preserving per-vessel office override priority.
4. [ ] Run focused backend tests for notification routing, settings API, monthly digest, cadence heartbeat, and parser anomaly notification paths.
5. [ ] Update `docsuite/progress.txt`, `BROWNFIELD_INTEGRATION_NOTES.md`, root `tasks/todo.md`, and monorepo `VimsWithSafety/tasks/todo.md`.

## Guardrails

- Preserve D-CERT-161: vessel users stay in-app + email only; office users stay in-app + Slack only.
- Do not send live Slack traffic; tests use recording relays only.
- Do not mutate live/staging DB, OCR thresholds, notification settings, class snapshots, mappings, catalog rows, or reconciliation data.
- No migration or new DB column is expected for this step.

## Outstanding Exemptions

- `ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
- `ASSUMPTION-OVERRIDE`: Prince/DPA waived the missing VIMS Certificates Module training completion evidence for Phase 9.5 cutover sign-off on 2026-07-01.
