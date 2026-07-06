# Certs Phase 10.2 - OCR Tuning

Current phase: Phase 10 - Post-launch hardening.
Current step: 10.2 - OCR tuning.
Session status: IN PROGRESS.

## Scope

1. [x] Re-read AGENTS.md, the local `vims-certs-build` skill, latest progress, Phase 10.2 traceability, Brownfield gates, blockers, and relevant PRD/APP_FLOW/FIELD_MAP/BACKEND/SECURITY/OBSERVABILITY/LESSONS sections.
2. [ ] Add focused tests showing tuned OCR thresholds are consumed by office and vessel confidence banding.
3. [ ] Implement tuned threshold lookup from the existing settings/alert-config surface with locked 80/85/60 defaults as fallback.
4. [ ] Verify focused backend behavior and existing settings API behavior.
5. [ ] Update `BROWNFIELD_INTEGRATION_NOTES.md`, `docsuite/progress.txt`, and both task files for closeout.

## Guardrails

- No migrations or DB columns: threshold fields already exist in `vims_certs_alert_config` and FIELD_MAP section 10.
- No class-status OCR: class PDFs remain text-extracted only per D-CERT-048.
- No live DB writes, seed commands, notification dispatch, email, Slack, class portal API work, sibling-module integration, or frontend redesign.
- Preserve existing `settings_change` audit and `ocr_processed` audit behavior.

## Outstanding Exemptions

- `ASSUMPTION-OVERRIDE`: Prototype catalog seed defaults applied on 2026-06-25 under Prince approval because DPA/Tech Sup'tt could not provide row-by-row metadata before prototype.
- `ASSUMPTION-OVERRIDE`: Prince/DPA waived the missing VIMS Certificates Module training completion evidence for Phase 9.5 cutover sign-off on 2026-07-01.
