# Provenance — master_audit_finding_category.csv

Source document : KSM-F-NC-001 / KSM-F-OBS-001 Rev 01 Jan-2026 + SSOT enums
Source location : SSOT §5.3 + D-AUDRS-018 (superseded) / D-041 / D-047
Extraction date : 2026-05-20
Extractor       : Claude Opus 4.7 (LLM) — deterministic from frozen SSOT
Reviewer        : DPA (KSM Designated Person Ashore) — review complete, CSV approved as-is
Review date     : 2026-05-20
code_version    : n/a
Change log      :
- 2026-05-20  Initial generation. 5 rows = the live D-041 leaf categories
              (nc_category {MAJOR_NC, MINOR_NC} + observation_category {OBSERVATION,
              IMPROVEMENT_SUGGESTION, OFI}). default_target_days per D-047.
              RECONCILIATION: SSOT §5.3 / D-018 named a 4-row enum; D-041 superseded
              D-018. Confirm 5-row model with DPA + Prince before assigning a
              D-AUDRS-124..199 supplemental ID (see DATA_MODEL.md §14).
- 2026-05-20  DPA review complete — seed CSV approved for commit (D-AUDRS-098).
