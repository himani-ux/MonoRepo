# Provenance — master_audit_window_rule.csv

Source document : ISM Code Ch.13, ISPS Code Part A §19, MLC 2006 Std A5.1.3, KSM SSQE Manual Rev 01 Feb 2026 §10.3.2/§10.3.3
Source location : SSOT D-AUDRS-022 / D-049 / D-203 / D-242
Extraction date : 2026-05-20
Extractor       : Claude Opus 4.7 (LLM)
Reviewer        : DPA (KSM Designated Person Ashore) — review complete, CSV approved as-is
Review date     : 2026-05-20
code_version    : n/a
Change log      :
- 2026-05-20  Initial generation. External anniversary windows = +/-3 months per ISM
              Code (D-203). Internal vessel audit interval row = 8-12 month window
              per SSQE Manual §10.3.2 (D-049). Office internal cadence (9-15 months,
              SSQE §10.3.3) to be added at build once office subtype codes finalised.
              cadence_months: 12 = annual, 30 = intermediate (2nd-3rd anniversary),
              60 = 5-year renewal. Window math reads this table (D-242) — never hardcoded.
              CONFIRM exact regulatory citations + office row with KSM SSQE Manager.
- 2026-05-20  DPA review complete — seed CSV approved for commit (D-AUDRS-098).
