# Provenance — master_audit_checklist.csv + master_audit_checklist_item.csv  [✅ EXTRACTED — DPA reviewed 2026-05-20]

Source document : SQE F 604 (Manning Office), F 605 (Vessel Internal), F 606 (Office Internal)
                  Audit Checklists — KSM SSQE Manual Rev 01 Feb 2026, Annex 1
Source location : `SSQE Manual- Rev 01 Feb 2026/SSQE Annex 1-Forms/`
                  · SQE F 604 Check List for Manning Office audit.xls
                  · SQE F 605 Vessel Internal Audit Checklist.xlsx  (sheet "Page 2")
                  · SQE F 606 Office Internal Audit Checklist -.xls  (sheets crew/tech/ops/SQA)
Target rows     : master_audit_checklist ~3 ; master_audit_checklist_item ~670 per D-AUDRS-020
Actual rows     : master_audit_checklist = 6 ; master_audit_checklist_item = 785
                  (F605=537, F604=47, F606=201 — CREW 37 / TECH 67 / OPS 51 / SQA 46)
Extraction date : 2026-05-20
Extractor       : Claude Opus 4.7 (LLM) via openpyxl/xlrd parse of the KSM source spreadsheets
Reviewer        : DPA (KSM Designated Person Ashore) — review complete, CSV approved as-is
Review date     : 2026-05-20
code_version    : SSQE Rev 01 Feb 2026
Column mapping  : F 605 — L.Code->location_code, Code->item_code, Questions->question,
                  Guideline->guideline, Related Regulations->regulation_ref, Reference->ksm_sms_ref.
                  F 604 — section header->location_code, item no->item_code, question->question,
                  HRM ref->ksm_sms_ref (prefixed "HRM "), other ref->regulation_ref.
                  F 606 — section header->location_code, item no->item_code, question->question,
                  SMS MANUAL+CHAPTER+SECTION composed->ksm_sms_ref, OTHER REF->regulation_ref.
Change log      :
- 2026-05-20  Extracted. master_audit_checklist = 6 rows: F605 (vessel), F604 (manning),
              and F606 split into 4 dept rows (F606_CREW/TECH/OPS/SQA) since F 606 has
              one sheet per department (D-020 / FIELD_MAP §8 — "each sheet -> checklist
              scoped by dept"). F 605 annotation continuation rows (blank Code) were
              merged into the preceding item's guideline/regulation_ref.
Notes / open items :
- SCHEMA DELTA: master_audit_checklist.csv carries an added `scope_dept` column (CREW/
  TECH/OPS/SQA for F 606 rows) not in DATA_MODEL §8.3. Needed for office-audit checklist
  auto-pick by department. Flag as a v1.0 supplemental schema item (reserved D-124..199,
  DPA+Prince confirm per D-284) — see DATA_MODEL.md §14.
- F 605 Page 2 has no per-row ship-type column; all 537 rows seeded ship_type='Common'.
  The Page-1 S Code legend (10 Common / 80 Bulk Carriers / 90 Others) is informational.
- F 604 manning checklist is seeded but the MANNING_AGENT auditee type is v1.3-deferred
  (D-247) — seed retained, not surfaced at v1.0/v1.1.
- item count 785 exceeds the SSOT ~670 estimate (F 606 four-department total larger
  than estimated); not a defect.
- 2026-05-20  DPA review complete — seed CSV approved for commit (D-AUDRS-098).
