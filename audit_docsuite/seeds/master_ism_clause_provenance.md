# Provenance — master_ism_clause.csv  [✅ EXTRACTED — DPA reviewed 2026-05-20]

Source document : IMO ISM Code, 2018 Edition (International Safety Management Code with guidelines for its implementation; ISBN 978-92-801-1696-0; IMO sales no. ID117E)
Source location : `Incident investigation/ISM code 2018.pdf` (on disk, project root) — pp. 11-27 (Preamble + Part A clauses 1-12 + Part B clauses 13-16)
Target rows     : ~80, 3-level depth per D-AUDRS-088
Actual rows     : 89
Columns         : clause_no, clause_text, section_no, code_version (='ISM 2018')
Extraction date : 2026-05-20
Extractor       : Claude Opus 4.7 (LLM) — read directly from the on-disk ISM Code 2018 PDF
Reviewer        : DPA (KSM Designated Person Ashore) — review complete, CSV approved as-is
Review date     : 2026-05-20
code_version    : ISM 2018
Change log      :
- 2026-05-20  Extracted from the source PDF. 16 section headers (1-16) + all 2-level
              clauses + the 12 definitions (1.1.1-1.1.12) + 13.5.1 = 89 rows. clause_text
              for 2-level clauses is a faithful condensation of the verbatim Code text;
              the 12 definitions are verbatim. Per D-093, future ISM amendments add new
              rows with a new code_version (rows never deleted).
- 2026-05-20  DPA review complete — seed CSV approved for commit (D-AUDRS-098).
