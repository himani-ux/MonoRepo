# Provenance — master_audit_subtype.csv

Source document : SSOT v0.21 enum (audit_subtype / external_audit_subtypes_csv)
Source location : SSOT §6.3 + D-AUDRS-011 / D-200 / D-207 / D-208 / D-214 / D-215
Extraction date : 2026-05-20
Extractor       : Claude Opus 4.7 (LLM) — deterministic from frozen SSOT
Reviewer        : DPA (KSM Designated Person Ashore) — review complete, CSV approved as-is
Review date     : 2026-05-20
code_version    : n/a
Change log      :
- 2026-05-20  Initial generation. 18 rows: 1 internal (ANNUAL_INTERNAL) + 17 external
              (DOC/SMC/MLC/ISPS x INITIAL/INTERIM/INTERMEDIATE-or-ANNUAL/RENEWAL +
              ADDITIONAL). NOTE: D-214 states "18 external" — the enumerable external
              values are 17; the count is flagged for confirmation at build
              (SEEDS_PROVENANCE.md §3).
- 2026-05-20  DPA review complete — seed CSV approved for commit (D-AUDRS-098).
