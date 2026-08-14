# VIMS Inspection Extension — Audit & RightShip Module
## Single Source of Truth (SSOT)

**Status:** 🔒 **v1.0 + v1.1 BOTH FROZEN at SSOT v0.21 (2026-05-19).** Total locks: **~208 active decisions** (123 v1.0 D-001..123 + 88 v1.1 D-200..287; 3 retained-superseded D-056, D-100, D-112-partial for audit trail). Interrogation cycle COMPLETE — 95/95 questions resolved (78 closed + 13 deferred to v1.2/v1.3 + 4 rejected NOT APPLICABLE). KLOSS Step 1 (Requirements Interrogation) DONE for both v1.0 + v1.1. **Ready for KLOSS Step 2 (DocSuite generation) at `VIMS-Audit-Module/` using Certs canonical pattern (D-270).** Freeze authority: Prince per D-285. **v1.0 freeze target = Vessel Internal Audit + Office Internal Audit.** **v1.1 freeze target = External Audit (DOC / SMC / MLC / ISPS — Initial / Interim / Annual / Renewal subtypes, 18 enum values).** Top v1.1 model shifts: D-254 offline-by-design (process-only, NOT software offline) + VESSEL_ACKNOWLEDGED state anchors NC SLA clocks; D-259 Flag-State acceptance of wet-ink+scan-back confirmed (D-061 HARD BLOCKER removed); D-261 QR/hash PDF replay-prevention built; D-264 vessel email via CMS API (supersedes D-112); D-271 cross-module DB Table Creation Standard (UNIQUEIDENTIFIER PK / no INT IDENTITY); D-280 vessel/office rank-source split (HRM501 vessel-side only); D-285 Prince=final freeze authority; D-287 3 deferred-to-v2 integrations explicitly locked (PMS / SMS Doc / Training = manual reference). v1.2 = RightShip RISQ 3.0 (deferred per D-247); v1.3 = Manning Agent + Security Provider audits (deferred per D-247).

---

## ▶ NEXT SESSION START HERE — KLOSS STEP 2 · DOCSUITE GENERATION

**v1.0 🔒 FROZEN at v0.18** (D-001..123 — Internal Audit). **v1.1 🔒 FROZEN at v0.21** (D-200..287 — External Audit + cross-cutting standards). Total: **~208 active decisions.** Do not re-litigate either version; if a locked decision needs to change, supersede it explicitly with a new D-AUDRS-### ID (range 124-199 for v1.0 supplemental, 288-299 for v1.1 supplemental — see §0.5).

**Begin KLOSS Step 2** at `VIMS-Audit-Module/` following the [[project_vims_certificates_module]] canonical pattern (per D-AUDRS-270) — Certs 199/199 GREEN pattern from 2026-05-13. Secondary reference [[project_vims_safety_module]] for crew-side wizard patterns (D-116 references Safety's incident-form work). Produce **11-doc DocSuite** per D-AUDRS-269: `PRD.md` · `BACKEND_STRUCTURE.md` · `APP_FLOW.md` · `DATA_MODEL.md` · `RBAC.md` · `FIELD_MAP.md` · `PDF_TEMPLATES.md` · `SEEDS_PROVENANCE.md` · `CROSS_MODULE_DEPS.md` · `MIGRATION.md` · `TEST_PLAN.md` — plus `COVERAGE.md` (target N≈700-900 mechanical re-grep mentions, ≥99% coverage per D-266) and `seeds/` CSV folder with `<file>_provenance.md` sibling per D-267. **Every new table MUST follow D-AUDRS-271 DB Table Creation Standard** (UNIQUEIDENTIFIER `id` PK + NEWSEQUENTIALID() default + `<parent_table>_id` FK; no INT IDENTITY for new tables; legacy psc_inspection family is sole exception). Use SSOT v0.21 as the immutable input.

**Verification artefacts already on disk for visual context:**
- `VIMS-AUDIT-RS-MODULE-SSOT.md` v0.17 (this file, ~1700 lines)
- `VIMS-Audit-Module-Walkthrough.html` — 11-phase end-to-end with R1.I/J/K spotlights
- `VIMS-NC-Observation-UX.html` — NC + Observation wizards (mobile + desktop) + PDF print-outs
- `VIMS-AUDIT-LIFECYCLE.html` · `VIMS-AUDIT-RS-WORKFLOW.html` — diagrams
- `VIMS-Audit-Module-Mockups.html` · `VIMS-Audit-Module-Reports.html` — vessel UX + reports
- `VIMS-Audit-Module-Office-Mockups.html` · `VIMS-Audit-Module-Office-Reports.html` — office UX + reports

---

## ▶ FROZEN STATE — 2026-05-18 (PM · session 2 close)

**State as of 2026-05-18 PM end-of-session**: SSOT v0.16 · **119 locked decisions** (D-AUDRS-001..119). Round 1 + R1.G + R1.H + R1.I + **R1.J + R1.K COMPLETE**. KLOSS Step 1 (Requirements Interrogation) DONE. Five HTML verification artefacts on disk. Two superseded decisions retained for audit trail: D-056, D-100. Three new master tables added (notification_delivery_log, master_slack_channel, master_rca_template) — audit-domain table count now **13**.

**R1.J closed 2026-05-18 PM — multi-channel notifications:**
1. **D-AUDRS-111** — Triple-channel (in-system + email + Slack) for audit-related notifications. In-system source-of-truth; email/Slack async with 3× retry.
2. **D-AUDRS-112** — Vessel email = single official mailbox on `VesselData.official_email`. Office = `users.email`.
3. **D-AUDRS-113** — Slack via incoming webhooks; new `master_slack_channel` table; new gate `AUDIT_P_011`.
4. **D-AUDRS-114** — `notification_delivery_log` table; 7-year retention; per-row PDF export for evidence packs.
5. **D-AUDRS-115** — 7 audit notification types covered at v1.0 (AUDIT_SCHEDULED, AUDIT_NC_RAISED, AUDIT_CANCELLED, AUDIT_OVERDUE, AUDIT_CRITICAL_OVERDUE, AUDIT_EXTENSION_APPROVED, NC_EFFECTIVENESS_REVIEW_DUE).

**R1.K closed 2026-05-18 PM — NC closure UX simplification:**
6. **D-AUDRS-116** — Plain-language wizard UX for KSM-F-NC-001 Parts B + C (crew side). Mobile-first single-question-per-screen. Backend fields unchanged.
7. **D-AUDRS-117** — `master_rca_template` table seeded ~25 common scenarios; new gate `AUDIT_P_012`. Crew picks template → wizard pre-fills RCA → edit to fit.
8. **D-AUDRS-118** — Office-led drafting flow: Supt drafts Part B+C, Master signs. New sub-state `OFFICE_DRAFTED`. Both names on PDF audit-trail.
9. **D-AUDRS-119** — Photo-first capture deferred to v1.1.

**R1.I closed 2026-05-18 PM — PIC model simplification:**
1. **D-AUDRS-107** — PSC-style open-pool PIC for Audit. No named PIC at plan time. Any scoped office user with `AUDIT_P_004` gate can pick up the PIC review action. **Supersedes D-056 + D-100.** Drops `audit_plan.office_pic_user_id` and `audit_plan.assigned_pic_user_id` columns.
2. **D-AUDRS-108** — DPA selects Lead Auditor at audit_plan creation from `master_audit_qualified_auditor` filtered to active + non-expired + matching standards. Modifies D-039 (was "SEQ Manager creates+assigns"). At KSM today DPA = SEQ Manager per D-034.
3. **D-AUDRS-109** — F 601 / F 602 PIC field runtime-resolved: first office user to perform PIC review action becomes PIC of record. Stored in derived `audit_detail.pic_user_id_resolved`. F 601 at plan time shows "— (assigned at first review)"; reissued at DPA_CLOSED with resolved name.
4. **D-AUDRS-110** — Lead Auditor ≠ PIC enforced server-side at action time (HTTP 403). Modifies D-058 enforcement point from plan-time to action-time.

**R1.H closed 2026-05-18 AM:**
- **D-AUDRS-105** — Single `master_audit_area` (14 rows) with N/A allowed on office audits.
- **D-AUDRS-106** — New `master_hod_assignment` table with history + acting-HoD support. Supersedes D-102 resolver portion.

**Next action: KLOSS Step 2 — DocSuite Generation** at `VIMS-Audit-Module/` following the [[project_vims_safety_module]] pattern. Produce 11 canonical docs + COVERAGE.md + FIELD_MAP.md + seeds/ CSV folder. SSOT v0.15 is the input; do not re-litigate locked decisions.

**Verification artefacts produced 2026-05-14 (open in browser to re-orient):**
- `/VIMS-Audit-Module-Mockups.html` — Vessel UX, 5 screens
- `/VIMS-Audit-Module-Reports.html` — Vessel reports, 4 PDFs (SMS-controlled headers)
- `/VIMS-Audit-Module-Office-Mockups.html` — Office UX, 2 screens
- `/VIMS-Audit-Module-Office-Reports.html` — Office reports, 4 PDFs

**Don't redo:** All 104 decisions are locked. If a locked decision needs to change, supersede it explicitly in §9 with reason and pointer.

**v1.0 scope re-confirmation (frozen):** Vessel Internal Audit + Office Internal Audit only. v1.1 = External Audit · v1.2 = RightShip RISQ 3.0 · v1.3 = Manning Agent + Security Provider audits.
- **R1.D** Master data detail (D-AUDRS-091..100): F 605 CSV column confirmation · ISM clause depth · KSM SMS chapter list · versioning when checklists revise.
- **R1.E** PDF template fine details (D-AUDRS-101..105): A4 layouts · signature blocks · watermarks/DRAFT badges · multi-page handling.
- **R1.F** Migration & seed data (D-AUDRS-106..110): production query to count existing AUDIT rows · backfill policy · F 605/F 606 seed CSV generation from Excel.

**Don't redo:** Round 0 series is complete. Don't re-interrogate already-locked decisions D-AUDRS-001..065. If a locked decision needs to change, supersede it explicitly (mark old one SUPERSEDED, add new one with reason).

**No outside-scope distractions:** RightShip (v1.2), External Audit (v1.1), Manning Agent (v1.3) are explicitly deferred. Do not silently re-include them per the [[audit-rs-scope-separation]] feedback memory.
**Version:** 0.2
**Created:** 2026-05-13
**Last Updated:** 2026-05-13 (Round 0.5 — SSQE Manual §10 + Annex 1 Forms ingested)
**KLOSS Step:** 1 (Requirements Interrogation — Rounds 0 + 0.5 complete, Round 1 pending)
**Module Scope:** Extend live VIMS Inspection module to add first-class workflows for **RightShip (RISQ 3.0)** and **Audit** inspections alongside the existing PSC workflow. CAR engine, evidence rules, sync, RBAC, and notifications are reused unchanged. **VIMS Inspection is the canonical Non-Conformity (NC) management system per KSM SSQE Manual §10.6.3 and §10.8.5** — this is the formal definition of what is being extended.

---

## 0. Resume Guidance — 🔒 v1.1 FROZEN at v0.21 (2026-05-19)

**Status:** v1.0 + v1.1 interrogation cycles COMPLETE. SSOT batch-merge of all v1.1 decisions executed 2026-05-19. **Handoff to KLOSS Step 2 (DocSuite generation) at `VIMS-Audit-Module/`** using Certs canonical pattern per D-AUDRS-270.

**SSOT version:** 0.21. **Decisions locked:** **~208 active** (123 v1.0 in D-AUDRS-001..123 + 88 v1.1 in D-AUDRS-200..287; minus D-056 + D-100 + D-112-partial superseded — retained for audit trail). All ~189 active decisions are load-bearing for DocSuite generation. Freeze authority: Prince per D-AUDRS-285.

### 0.4 Reference Document Versions (per D-AUDRS-286)

All SSOT + DocSuite citations reference these versions explicitly. Mid-build minor revisions absorbed via diff; major revisions trigger SSOT re-interrogation round R-AUD-vN.0.

| Document | Version | Path | Drives |
|----------|---------|------|--------|
| KSM SSQE Manual | **Rev 01 Feb 2026** | `SSQE Manual- Rev 01 Feb 2026/SSQE Manual- Rev 01 Feb 2026.pdf` §10 pp 206-219 | Audit procedure authority (D-016..032, D-099) |
| SQE F 601 Audit Plan | Rev as in SSQE Annex 1 (Feb 2026) | `SSQE Manual- Rev 01 Feb 2026/SSQE Annex 1-Forms/SQE F 601 Audit Plan.xls` | Field source (D-019, D-023, §18.1) |
| SQE F 602 Internal Audit Report | Rev as in SSQE Annex 1 | `SSQE Manual- Rev 01 Feb 2026/SSQE Annex 1-Forms/SQE F 602 Internal Audit Report.docx` | Audit record + 14-area scorecard (D-027..030, §18.2) |
| SQE F 604/605/606 Checklists | Rev as in SSQE Annex 1 | `SSQE Manual- Rev 01 Feb 2026/SSQE Annex 1-Forms/SQE F 604/605/606 *.xls(x)` | Checklist seeds (D-020, §18.3-5) |
| SQE S 625 Non Conformity | Rev as in SSQE Annex 1 | `SSQE Manual- Rev 01 Feb 2026/SSQE Annex 1-Forms/SQE S 625 Non Conformity.doc` | NC form field source (D-018, §18.6) — **Note:** REPLACED for audit NCs by KSM-F-NC-001 per D-AUDRS-040 family |
| KSM-F-NC-001 NC Closure Form | **Rev 01 Jan 2026** | `Audit Reports/KSM-F-NC-001_NC_Closure_Form.docx` | NC closure PDF template (D-040..048, §18.9) — 7 parts, 2 pages |
| KSM-F-OBS-001 Observation Closure Form | **Rev 01 Jan 2026** | `Audit Reports/KSM-F-OBS-001_Observation_Closure_Form.docx` | Observation closure PDF template (§18.10) — 4 parts, 1 page |
| Live VIMS Inspection module | Per `VIMS DOCS/` snapshot | `VIMS DOCS/` PRD + BACKEND_STRUCTURE + APP_FLOW + CURRENT_IMPLEMENTATION_REFERENCE + LATER_CHANGES | Inspection module live truth (D-001, D-070) |
| Certs DocSuite (canonical reference pattern) | 199/199 GREEN · 2026-05-13 | `VIMS-Certs-Module/` | DocSuite Step 2 pattern (D-AUDRS-270) |
| Safety DocSuite (secondary reference) | 159/159 GREEN · 2026-04-17 | `VIMS-Safety-Module/` | Wizard-pattern reference for D-AUDRS-116 |
| KLOSS Framework | Latest at project root | `KLOSS FRAMEWORK/` | Methodology |

**Trigger detection:** quarterly grep of "KSM SSQE Manual" references vs the live file at project root; version-stamp mismatch surfaces a flag.

### 0.5 ID Allocation Convention (per D-AUDRS-284)

| Range | Scope | Status |
|-------|-------|--------|
| D-AUDRS-001..123 | v1.0 Internal Audit | 🔒 FROZEN at v0.18 (2 superseded: D-056, D-100 retained for audit trail) |
| **D-AUDRS-124..199** | **RESERVED for v1.0 supplemental** | Open for DocSuite Step 2 schema fixes / validation gaps / seed corrections; requires DPA + Prince re-confirm before assignment |
| D-AUDRS-200..287 | v1.1 External Audit + cross-cutting standards | 🔒 FROZEN at v0.21 (D-112-partial superseded by D-264) |
| **D-AUDRS-288..299** | **RESERVED for v1.1 supplemental** | Open for v1.1 supplemental during build |
| D-AUDRS-300+ | v1.2 RightShip | Deferred per D-247 |
| D-AUDRS-400+ | v1.3 Manning + Security | Deferred per D-247 |

**Original 2026-05-18 Resume Guidance (v0.14) — preserved for audit trail:**

**Last session active:** 2026-05-18 (resumed after 4-day gap from 2026-05-14 EOD). **SSOT version:** 0.14. **Decisions locked:** **106** (D-AUDRS-001..106). Round 1 + R1.G Office + **R1.H closed today.** Four HTML verification artefacts on disk (vessel + office mockups and reports). **KLOSS Step 1 (Requirements Interrogation) officially DONE.**

**Resume order for next session (first 10 minutes):**
1. Read ▶ CURRENT START HERE (above) to re-orient on the 2 new R1.H locks (D-105 + D-106)
2. Open the 4 HTML artefacts in browser if visual context needs refreshing
3. **Begin KLOSS Step 2** — DocSuite generation at `VIMS-Audit-Module/` following the [[project_vims_safety_module]] pattern. **Round 1 status:** ALL 7 GROUPS CLOSED — R1.A schema-tactical (D-066..070) · R1.B validation rules (D-071..078) · R1.4 workflow edge cases (D-079..082) · R1.C RBAC + sidebar (D-083..086) · R1.D master data (D-087..094) · R1.E PDF templates (D-095..096) · R1.F migration & seed (D-097..098) · R1.G Office workflow (D-100..104) · **R1.H office-scorecard + HoD mapping (D-105..106)**. **v1.0 scope unchanged:** Vessel Internal + Office Internal Audit (KSM Internal Audit only — RightShip, External, Manning, Security all deferred).

**For next session:** start KLOSS Step 2. Follow the [[project_vims_safety_module]] DocSuite pattern at `VIMS-Safety-Module/` and [[project_vims_certificates_module]] at `VIMS-Certs-Module/`. Create folder `VIMS-Audit-Module/` and produce 11 canonical docs + COVERAGE.md + FIELD_MAP.md + seeds/ CSV folder. SSOT v0.14 is the input; do not re-litigate locked decisions.

**Read order for tomorrow's first 15 minutes:**

1. **This file end-to-end** (~1600 lines) — re-orient on locked scope and avoid re-opening closed decisions.
2. `VIMS-AUDIT-LIFECYCLE.html` — sanity-check the 11-phase workflow + 3 branch flows look right.
3. `VIMS-AUDIT-RS-WORKFLOW.html` — codebase mapping, decisions snapshot, and KSM form status table.
4. **§16 Open Questions** below — pick a Round 1 sub-section to start.

**Reference sources** (read only if needed):
- `VIMS DOCS/` — live Inspection module truth: PRD, BACKEND_STRUCTURE, APP_FLOW, CURRENT_IMPLEMENTATION_REFERENCE, LATER_CHANGES.
- `SSQE Manual- Rev 01 Feb 2026/SSQE Manual- Rev 01 Feb 2026.pdf` §10 pp 206–219 — KSM audit procedure authority.
- `SSQE Manual- Rev 01 Feb 2026/SSQE Annex 1-Forms/` — F 601, F 602, F 604/605/606, S 626 source forms.
- `Audit Reports/` — KSM-F-NC-001 + KSM-F-OBS-001 closure forms + 3 sample audit packages (Chalisa, East Ayutthaya, August 2025).

**Rules for tomorrow's session:**
- New decisions: append to §9 Decisions Log + §4 Locked Decisions table as `D-AUDRS-066` onwards.
- Each decision cites rationale + which table/screen/contract it changes.
- If a locked decision needs to change: mark old one `SUPERSEDED` with pointer to new ID; never silently re-edit a locked decision.
- Don't re-include RightShip / External / Manning / Security in v1.0 — explicitly out-of-scope per D-AUDRS-033/054 + the `[[audit-rs-scope-separation]]` feedback memory.

**Suggested R1 starting groups** (independent, pick any order):
| Group | Decision IDs | Focus |
|-------|-------------|-------|
| R1.A Schema tactical | D-066..075 | Polymorphic clause_ref · finding_type discriminator · denormalisation columns · master naming |
| R1.B Validation rules | D-076..085 | Mandatory-at-submit gates · 90-day soft vs hard · RCA min lengths · signature ordering |
| R1.C RBAC fine-tuning | D-086..090 | New `PSC_P_*` gates vs reuse · sidebar tabs · office vessel-scope |
| R1.D Master data detail | D-091..100 | F 605 CSV columns · ISM depth · KSM SMS chapter list · versioning |
| R1.E PDF template details | D-101..105 | A4 layouts · signature blocks · watermarks |
| R1.F Migration & seed | D-106..110 | Production query for existing AUDIT rows · backfill · F 605/606 CSV generation |

---

## 1. Module Overview

### 1.1 Why This Module
The live VIMS Inspection module (`VIMS DOCS/`) was designed and built around the PSC (Port State Control) workflow. The `psc_inspection.inspection_type` enum already includes `PSC`, `RS`, `AUDIT`, `INTERNAL`, and the create-inspection form lets the user pick any of those four — but the only well-developed branch is PSC. Today, users registering an RS or Audit inspection must:

- Type free-text into PSC-shaped fields (DefCode, Action Code) that are meaningless for those inspection types
- Skip structure that auditors and vetting parties expect (RISQ chapters/Q-numbers, ISM clause refs, audit team, opening/closing meetings)
- Receive PSC-shaped PDF exports for RS/Audit reports
- Have no way to capture RightShip vetting outcomes or Audit certificate impact

The goal of this extension is to give RS and Audit inspections **proper, first-class registration and finding-capture workflows** — while keeping the **CAR engine, evidence rules, PIC→DPA closure, sync, notifications, audit log, and RBAC** completely untouched.

### 1.2 Primary Users
Same as PSC (no new roles):

| Role | Description | Audit/RS Use |
|------|-------------|--------------|
| Vessel Master | Registers inspection, enters findings, submits | Same as PSC |
| Crew (Action Owner) | Receives assigned actions, uploads evidence | Same as PSC |
| Office (PIC/SSQE/Supt) | Reviews CARs, requests rework, accepts | Same as PSC |
| DPA | Final closure authority | Same as PSC |
| Physical Verifier | Records on-board verification | Same as PSC |

**Lead auditor / RightShip inspector / Class surveyor** are captured as **data on the inspection record**, not as system users. They do not log in.

### 1.3 Success Criteria
- A vessel Master can register an ISM Internal / ISM External / ISPS / Other audit inspection with structured fields covering audit kind, subtype, lead auditor, audit team, opening/closing meeting, and audit scope.
- A vessel Master can register a RightShip RISQ 3.0 inspection with structured fields covering RISQ version, inspector company, charterer, vetting outcome, and overall risk score.
- Every finding entered on an RS or Audit inspection creates exactly one CAR (1:1) via the same trigger PSC uses today.
- All CARs — regardless of source — flow through the unchanged CAR state machine: `ALLOTTED → IN_PROGRESS → PENDING_CE_REVIEW → PENDING_MASTER_REVIEW → SUBMITTED_TO_PIC → PIC_REVIEW → SUBMITTED_TO_DPA → CLOSED`, with the same evidence rules (≥1 BEFORE + ≥1 AFTER) and the same rework/closure semantics.
- RISQ 3.0 question bank, ISM Code 2018 clauses, ISPS Part A sections, and MLC 2006 Titles are seeded as master tables enabling finding analytics by Q-number / clause.
- Per-type PDF templates are available: PSC (existing), RS (RISQ-style), Audit (ISM/ISPS/MLC-style).
- Per-type list filters and dashboards enable Office and DPA to slice by `inspection_type`.

---

## 2. Present-State Truth (As-Of 2026-05-13)

This section freezes what is **currently live** in the production VIMS Inspection module. It exists so future rounds and the build team can distinguish "what is" from "what we're adding."

### 2.1 Live `psc_inspection` Schema (Verified)

```sql
CREATE TABLE [dbo].[psc_inspection] (
    [id]                    uniqueidentifier NOT NULL DEFAULT NEWID(),
    [vessel_id]             uniqueidentifier NOT NULL,
    [inspection_type]       varchar(20) NOT NULL,   -- PSC | RS | AUDIT | INTERNAL  (already exists)
    [psc_subtype]           varchar(20) NULL,       -- INITIAL | EXPANDED | CIC | FOLLOW_UP  (PSC-only today)
    [inspection_date]       date NOT NULL,
    [port_place]            nvarchar(200) NOT NULL,
    [country]               nvarchar(100) NULL,
    [mou_id]                uniqueidentifier NULL,  -- FK master_mou (PSC-only)
    [authority]             nvarchar(200) NULL,
    [inspector_name]        nvarchar(200) NULL,
    [report_reference]      varchar(100) NULL,
    [is_detention]          bit NOT NULL DEFAULT 0,
    [status]                varchar(20) NOT NULL DEFAULT 'DRAFT',
    [parent_inspection_id]  uniqueidentifier NULL,  -- self-FK (PSC follow-ups)
    [revision_no]           int NOT NULL DEFAULT 1,
    [pic_comment]           nvarchar(max) NULL,
    [pic_reviewed_by]       varchar(100) NULL,
    [pic_reviewed_at]       datetime NULL,
    [dpa_comment]           nvarchar(max) NULL,
    [dpa_closed_by]         varchar(100) NULL,
    [dpa_closed_at]         datetime NULL,
    [is_deleted]            bit NOT NULL DEFAULT 0,
    [created_by]            varchar(100) NULL,
    [created_date]          datetime NULL DEFAULT GETDATE(),
    [updated_by]            varchar(100) NULL,
    [updated_date]          datetime NULL,
    [client_id]             uniqueidentifier NULL,
    [sync_version]          int NOT NULL DEFAULT 1
);
```

### 2.2 Live Workflow (Across All Types Today)
```
Create Inspection (DRAFT)
  ↓ Add findings (only DefCode + ActionCode shapes available)
  ↓ Each finding auto-creates a CAR via trg_psc_deficiency_auto_create_car
  ↓ Submit inspection (DRAFT → SUBMITTED)
  ↓ PIC reviews (SUBMITTED → PIC_REVIEWED)  -- comment mandatory
  ↓ DPA closes (PIC_REVIEWED → DPA_CLOSED)  -- comment mandatory
```

### 2.3 Live CAR State Machine (Post-2026-03 Override)
```
ALLOTTED → IN_PROGRESS → PENDING_CE_REVIEW → PENDING_MASTER_REVIEW
        → SUBMITTED_TO_PIC → PIC_REVIEW → SUBMITTED_TO_DPA → CLOSED
```
Rework can be requested at any review stage; closure requires DPA. Reopen by DPA returns to `REWORK_REQUESTED`.

### 2.4 CAR Number Generation (Already Multi-Type Capable)
```
{inspection_type}-{YYYY}-{NNN}
  e.g. PSC-2026-001 | RS-2026-001 | AUDIT-2026-001
```
The existing trigger reads `psc_inspection.inspection_type` and uses it verbatim as the prefix. **No change needed** for RS/Audit numbering.

### 2.5 Live Frontend Routes (Inspection Module)
```
/inspections                List
/inspections/new            Create (type-aware)
/inspections/:id            Detail
/inspections/:id/edit       Edit
/inspections/:id/follow-up  Register Follow-up (PSC only today)
/cars                       CAR List
/cars/:id                   CAR Detail
/cars/:id/edit              Edit CAR
/deficiencies               Workflow dashboard
/dashboard                  KPI dashboard
/reports                    DefIntel/OpenSource workspace
/settings                   Company logo + masters
```

### 2.6 Live RBAC
- 7 roles: `VESSEL_MASTER`, `VESSEL_CREW`, `OFFICE_PIC`, `OFFICE_SSQE`, `OFFICE_SUPT`, `DPA`, `PHYSICAL_VERIFIER`
- 8 form gates: `PSC_F_001` … `PSC_F_008` (Inspection module set)
- 16 process gates: `PSC_P_001` … `PSC_P_016`
- Auth carries `form_ids` and `process_ids` via `msc_profiles`; office users vessel-scoped via `master_RoleByVessel` unless globally mapped via `mapping_role_user → msc_profiles → Mapping_CrewAssReviewers`.

### 2.7 Live Inspection Tables (All Reused By This Module)
`psc_inspection`, `psc_inspection_report`, `psc_deficiency`, `psc_deficiency_action_history`, `psc_car`, `psc_car_clc_mapping`, `psc_corrective_action`, `psc_evidence`, `psc_physical_verification`, `psc_activity_history`, `psc_audit_log`, `psc_notification`, `psc_sync_log`, `psc_sync_log_detail`, `psc_sync_conflict`, `psc_sync_token`, `psc_opensource_import_run`, `psc_opensource_deficiency_record`.

---

## 3. Architecture (Locked at Round 0)

### 3.1 Architectural Principle
**In-place extension of the existing Inspection module.** No new Django app, no new sidebar module, no new auth path. All RS and Audit work flows through the same `/inspections/*` routes, the same backend package, the same database, and the same CAR engine.

### 3.2 Where Type-Specific Logic Branches
Branching happens at exactly three layers:

| Layer | Branch point | What changes per type |
|-------|--------------|------------------------|
| **Registration form** | `inspection_type` dropdown on `/inspections/new` | Different field groups load below the common header (vessel / date / port / country) |
| **Finding capture** | Below the registration block, per-finding entry | PSC: DefCode + Action Code · RS: RISQ chapter + Q-number + NO/MD + comment · Audit: kind + subtype + clause + category (Maj NC / Min NC / Obs / OFI) + objective evidence |
| **PDF export template** | `cars/export-pdf/` and `inspections/.../cars/export-pdf/` | Three templates — PSC (existing), RS (RISQ format), Audit (ISM/ISPS/MLC format) |

Everything else — list screen, detail screen, CAR list, CAR detail, evidence upload, action management, sync, notifications, RBAC checks, dashboard counters — handles all three types **identically** using `inspection_type` as a filter / display label.

### 3.3 Data-Model Strategy
Decision **D-AUDRS-016** (deferred to Round 1): three sub-decisions about how to physically store type-specific data:

- **Option A — Sibling child tables.** `audit_detail`, `rs_detail`, `rs_observation`, `audit_finding`, `audit_team_member` all keyed off `psc_inspection.id` or `psc_deficiency.id`. Cleanest schema, normalized, supports indexes.
- **Option B — Single deficiency table with JSON extension.** Keep `psc_deficiency` as the lone finding table; add `type_extension_json` for RS/Audit fields. Fastest to build, weak queryability.
- **Option C — Hybrid.** Inspection-level extensions (audit_detail, rs_detail) as sibling tables; finding-level extensions stored as additional columns on `psc_deficiency` (nullable). Middle ground.

This SSOT pre-recommends Option A (sibling tables) but the formal decision is taken in Round 1 once the field-by-field schema is laid out.

### 3.4 Shared / Reused Components (Zero Change)
- CAR auto-create trigger `trg_psc_deficiency_auto_create_car`
- CAR state machine and unified workflow endpoint `POST /api/psc/cars/<id>/workflow/`
- Evidence model `psc_evidence` (BEFORE / AFTER / EVIDENCE / OTHER)
- Corrective action model `psc_corrective_action` (IMMEDIATE / LONG_TERM)
- CLC code mapping `psc_car_clc_mapping`
- Activity history `psc_activity_history`
- Audit log `psc_audit_log`
- Sync infra (`psc_sync_log`, `psc_sync_log_detail`, `psc_sync_conflict`, `psc_sync_token`)
- Notification infra `psc_notification`
- Physical verification `psc_physical_verification`
- Auth: JWT, `master_role`, `mapping_role_user`, `msc_profiles`, `Mapping_CrewAssReviewers`
- Sidebar entry "Inspection" (Inspection node remains the primary nav group)

---

## 4. Locked Decisions Summary

### 4.1 Round 0 Decisions (User Interrogation — 2026-05-13 a.m.)

| # | ID | Decision (one-liner) |
|---|----|----------------------|
| 1 | D-AUDRS-001 | Architecture: in-place extension; same `/inspections` entry; same CAR engine. |
| 2 | D-AUDRS-002 | CAR number prefix already type-driven (`PSC-`/`RS-`/`AUDIT-`); no trigger change. |
| 3 | D-AUDRS-003 | CAR state machine, evidence rules, PIC/DPA closure, rework, physical verification, notifications, sync, audit log all unchanged for RS and Audit. |
| 4 | D-AUDRS-004 | **REVISED in R0.5 (see D-AUDRS-016)**. Original: Audit kinds = ISM Internal, ISM External, ISPS, Other. Superseded by multi-standard model. |
| 5 | D-AUDRS-005 | RightShip v1 = RISQ 3.0 only. No SIRE, no legacy free-text, no generic vetting in RS branch. |
| 6 | D-AUDRS-006 | RS RISQ finding model = structured: chapter + Q-number + finding category (NO / MD) + inspector comment. |
| 7 | D-AUDRS-007 | **REVISED in R0.5 (see D-AUDRS-041)**. Original: Audit categories = Major NC / Minor NC / Observation / OFI. Re-superseded by **two distinct enums** matching KSM-F-NC-001 + KSM-F-OBS-001 (the prior D-AUDRS-018 4-tier from SQE S 625 was based on the older Rev-02 2022 form; the newer Rev-01 Jan-2026 forms split NC and Observation into separate closure templates with different categories). |
| 8 | D-AUDRS-008 | Strict 1:1 finding → CAR for all types. All categories create one CAR each. |
| 9 | D-AUDRS-009 | Evidence rule unchanged: ≥1 BEFORE + ≥1 AFTER for every CAR, regardless of type/severity. |
| 10 | D-AUDRS-010 | **REVISED in R0.5 (see D-AUDRS-019)**. Original: attendees as count. Superseded by named-attendee table matching `SQE F 601`. |
| 11 | D-AUDRS-011 | Audit subtype enums per kind: ISM Internal = `ANNUAL_INTERNAL`; ISM External = `INITIAL` / `ANNUAL` / `INTERMEDIATE` / `RENEWAL` / `ADDITIONAL`; ISPS = same as ISM External; MLC = `INITIAL` / `INTERMEDIATE` / `RENEWAL`; Other = free-text label. **Augmented in R0.5 (see D-AUDRS-022)** — interval rules and extension workflow added. |
| 12 | D-AUDRS-012 | v1: no follow-up / re-inspection for RS or Audit. PSC `FOLLOW_UP` subtype unchanged. RS/Audit findings close only via CAR closure. |
| 13 | D-AUDRS-013 | RS registration captures: RISQ version + inspector company + charterer + vetting outcome enum (`ACCEPTED` / `ACCEPTED_WITH_OBS` / `NOT_ACCEPTED` / `PENDING_REVIEW`) + optional overall risk score. |
| 14 | D-AUDRS-014 | **EXPANDED in R0.5 (see D-AUDRS-021)**. Original: masters = RISQ 3.0 + ISM + ISPS + MLC. Expanded to KSM-recognised regulatory set (SOLAS / STCW / MARPOL / COLREG / Flag / Class / KSM SMS chapters). |
| 15 | D-AUDRS-015 | Roles unchanged. Lead auditor / RS inspector are data on the record, not system users. Existing 7 roles cover everything. Existing form/process gates extended to RS/Audit; may add ≤2 new `PSC_P_*` gates as needed. |

### 4.2 Round 0.5 Decisions (SSQE Manual §10 + Annex 1 Forms — 2026-05-13 p.m.)

**Build phasing (D-AUDRS-033): Vessel Internal Audit v1.0 first → External Audit v1.1 → Manning Agent / Security Provider audits v1.2.** This SSOT covers the *full* audit & RS scope, but Round 1 interrogation and the resulting DocSuite focus on Internal Audit only. RS is part of v1.0 since it shares the same CAR engine and adds no checklist seeding.


| # | ID | Decision (one-liner) | Supersedes / Adds to |
|---|----|----------------------|-----------------------|
| 16 | D-AUDRS-016 | **Multi-standard harmonized audit.** Replace `audit_kind` single-value with `audit_standards` multi-select [`ISM`, `ISPS`, `MLC`, `EMS`] + outer `audit_classification` enum [`INTERNAL`, `EXTERNAL`, `MANNING_AGENT_AUDIT`, `SECURITY_PROVIDER_AUDIT`]. KSM internal audits harmonize ISM+ISPS+EMS+MLC by default per SSQE §10.2.1 and `SQE F 601` ("TYPE OF AUDIT: INTERNAL ISM, MLC, ISPS AND EMS AUDIT"). | Supersedes D-AUDRS-004 |
| 17 | D-AUDRS-017 | **Auditee type field.** Separate from standards. Enum: `VESSEL`, `OFFICE_DEPT`, `MANNING_AGENT`, `SECURITY_PROVIDER`. `OFFICE_DEPT` further qualified by department code (Crew / Tech / Purchase / IT / Marine). Per SSQE §10.2.3 and §10.3.3 (Manning Agents + Security Providers audited under same procedure). | New |
| 18 | D-AUDRS-018 | **KSM-native finding category enum (4-tier, matches SQE S 625):** `MAJOR_NC` (Major Non-Conformity) · `NC` (Non-Conformity — KSM does NOT use "Minor NC" — plain NC implies minor) · `OBSERVATION` · `IMPROVEMENT_PROPOSAL` (Improvement Proposal / Suggestion — the KSM equivalent of OFI). Applies to all audit standards. | Supersedes D-AUDRS-007 |
| 19 | D-AUDRS-019 | **Opening/closing meeting attendees = named list, not count.** Capture per attendee: `name`, `rank`, `opening_present` (bit), `closing_present` (bit). Matches `SQE F 601`. Master + Department Heads mandatory for on-board audits per SSQE §10.5.2. | Supersedes attendee-count part of D-AUDRS-010 |
| 20 | D-AUDRS-020 | **Audit checklist master, scoped.** Per-audit selectable checklist seeded from KSM forms: (a) `SQE F 605` vessel checklist (~543 rows, 10 location codes × 3 ship types: Common/Bulk Carrier/Others — item codes 1100–1578+), (b) `SQE F 606` office checklist (per-department: crew/tech/purchase/IT/marine), (c) `SQE F 604` manning-office checklist (~46 rows). Each item has: location_code, item_code, question, guideline, regulation_ref, ksm_sms_ref. Audit screen lets auditor pick checklist by `auditee_type` + `audit_standards` + `ship_type`. | New |
| 21 | D-AUDRS-021 | **Clause-reference master scope expansion.** Per SSQE §10.7.3, NC definition cites: ISM Code, ISPS Code, MLC 2006, SOLAS, STCW, MARPOL, COLREG, Flag-state notices, KSM SMS chapters (Apex, OPM, SSQE, HRM, EMS, SPM I–II, SOPEP/SMPEP, Ship Security Plan, Cyber Security, BCGOM, SEEMP II/III). Seed: SOLAS / STCW / MARPOL / COLREG public; KSM SMS chapter list from `SQE S 626`. | Supersedes/expands D-AUDRS-014 |
| 22 | D-AUDRS-022 | **Audit interval enforcement & extension workflow.** Max **12 months** between successive audits (ISM mandatory). Min **8 months** between successive audits. Extension up to **3 months** allowed via DPA-approved form `OPM F 713`. Flag-state must be notified if exceeded. Office audit: 9–15 month spread. New-vessel takeover: internal audit within **3 months** of takeover. Per SSQE §10.3.2 and §10.3.3. | New (augments D-AUDRS-011) |
| 23 | D-AUDRS-023 | **Audit Plan / Schedule master.** New table `master_audit_plan` — SEQ Manager maintains rolling register of planned audits per vessel/office per audit period. Fields: planned_audit_id, target_entity (vessel_id / office_dept), audit_classification, audit_standards (multi), planned_date_window_from, planned_date_window_to, status (`PLANNED`/`CONFIRMED`/`COMPLETED`/`EXTENDED`/`CANCELLED`), extension_form_ref. Per SSQE §10.3.4 / `SQE F 601 Audit Plan`. | New |
| 24 | D-AUDRS-024 | **Audit trigger reason — EXTENDED 2026-05-18 PM by D-AUDRS-122.** Enum on audit record. Original values: `SCHEDULED` · `TAKEOVER_3MONTH` · `UNSCHEDULED_INCIDENT` · `UNSCHEDULED_NEAR_MISS` · `UNSCHEDULED_QUALITY_REVIEW` · `UNSCHEDULED_COMPLAINT` · `UNSCHEDULED_ROUTINE`. **Added 2026-05-18 PM (D-122, for use when `is_additional=1` per D-121):** `FLAG_REQUEST` · `PSC_FOLLOWUP` · `DETENTION_FOLLOWUP` · `INCIDENT_FOLLOWUP` · `MGMT_DIRECTIVE`. Optional FK `triggering_event_id` to safety incident / near miss / complaint (cross-module link). Polymorphic linkage for additional-audit trigger events handled by D-122 via separate `trigger_event_type` + `trigger_event_ref` fields. Per SSQE §10.3.6 / §10.3.7. | New |
| 25 | D-AUDRS-025 | **Per-finding (NC) signature/acknowledgment workflow** matching `SQE S 625`. New table `audit_finding_signature` (or fields on `audit_finding`): `issued_by_name`, `issued_by_rank`, `master_sign_at`, `marine_hsseq_supt_sign_at` (KSM's role title), `office_notified_at` + email-attachment ref, `office_confirmed_at` + email-attachment ref, `closure_verified_by_name`, `closure_verified_by_rank`, `closure_verified_at`, `closure_signature_path`. Independent of and complementary to existing CAR `pic_accepted_*` and `dpa_closed_*` fields. | New |
| 26 | D-AUDRS-026 | **Monthly Master KPI report — SQE S 626 export.** Auto-generate the `SQE S 626 Overview of SSEQ Management` workbook on demand from VIMS data, signed by Master, e-mailed to `HSSEQ@kaizenship.net` by 7th of each month. Sections: LSA test dates · ISM documentation dates · NC summary (from VIMS) · Last PSC inspection (date, port, def count) · **Last RightShip inspection** (date, port, observation count, closure status — `SQE S 626` already cites RightShip explicitly) · MLC inspection / FW tests · SMS manuals revision status · RA counts · Tech/Marine Supdt last visit · monthly incident / near-miss counts. Per SSQE §10.6.4 / `SQE S 626`. | New |
| 27 | D-AUDRS-027 | **Audit-header 14-area inspection summary scorecard.** Captured once per audit (matches `SQE F 602`): Navigation Procedures · Safety Equipment & Procedures · Emergency Preparedness · Cargo · Mooring/Anchoring · Non-Conformity Handling · Planned Maintenance System · Training · SMS Implementation · Certificate & Document Control · Environment Management · Security · MLC Implementation · Structured Training. Each area gets a status remark per audit. | New |
| 28 | D-AUDRS-028 | **Equipment-tested list per audit.** Free-text repeatable list "Equipment tested successfully during the audit" — matches `SQE F 602` field. Captured per audit record. | New |
| 29 | D-AUDRS-029 | **Previous-audit closure verification gates.** On audit registration, two yes/no/NA flags matching `SQE F 602`: "Corrective Actions from previous Internal Audit verified" and "Corrective Actions from previous External Audit verified". Office-side dashboard surfaces prior-audit open NCs to facilitate verification. Cross-link via `parent_audit_id` self-FK optional. | New |
| 30 | D-AUDRS-030 | **NC closure target ≤ 90 days** from finding issuance (per `SQE F 602`: "Due Date (90 days maximum)"). Extension permitted by SEQ Manager with reason; extended_due_date column on finding; original_due_date preserved for audit trail. | New |
| 31 | D-AUDRS-031 | **External audits use the same finding categories and procedure as internal.** Per SSQE §10.12. External-audit findings carry the audit-body name (Class society, Flag State, RO) in `audit_body_name` on `audit_detail`. Closure by DPA with Master assistance (already standard CAR engine behaviour). | New |
| 32 | D-AUDRS-032 | **PSC and RightShip observations ARE Non-Conformities.** Per SSQE §10.8.4 ("All observations recorded through Flag state inspection and Port state inspection shall be treated as Non-conformities") and §10.13. The 14-area scorecard, monthly KPI report, and closure rules apply uniformly. UI/PDF labelling can still show "Deficiency" for PSC and "Observation" for RS to match each authority's terminology, but the underlying NC funnel is unified. | New |

---

## 5. Proposed Data Model (Round 0 — pending D-AUDRS-016 in Round 1)

### 5.1 New Inspection-Level Child Tables

#### `audit_detail`
One row per audit inspection. Linked 1:1 to `psc_inspection` via `inspection_id`.
```
inspection_id              uniqueidentifier PK FK psc_inspection.id
audit_classification       varchar(30) NOT NULL    -- INTERNAL | EXTERNAL | MANNING_AGENT_AUDIT | SECURITY_PROVIDER_AUDIT
auditee_type               varchar(30) NOT NULL    -- VESSEL | OFFICE_DEPT | MANNING_AGENT | SECURITY_PROVIDER
auditee_office_dept        varchar(40) NULL        -- when auditee_type=OFFICE_DEPT: CREW | TECH | PURCHASE | IT | MARINE | OTHER
audit_subtype              varchar(40) NOT NULL    -- per-classification enum (D-AUDRS-011)
audit_subtype_other        nvarchar(200) NULL      -- when subtype=OTHER
audit_body_name            nvarchar(200) NULL      -- external auditor org: Class society / Flag / RO  (D-AUDRS-031)
lead_auditor_name          nvarchar(200) NOT NULL
lead_auditor_designation   nvarchar(200) NULL      -- "Lead Auditor" / "Class Surveyor" / etc.
lead_auditor_company       nvarchar(200) NOT NULL
lead_auditor_qual          nvarchar(200) NULL      -- e.g. "IRCA Lead Auditor"
trigger_reason             varchar(40) NOT NULL    -- SCHEDULED | TAKEOVER_3MONTH | UNSCHEDULED_INCIDENT | UNSCHEDULED_NEAR_MISS | UNSCHEDULED_QUALITY_REVIEW | UNSCHEDULED_COMPLAINT | UNSCHEDULED_ROUTINE  (D-AUDRS-024)
conductor_user_id          varchar(100) NOT NULL    -- D-AUDRS-063: office user who physically conducted the audit (locked once status >= IN_PROGRESS)
lead_auditor_user_id       varchar(100) NOT NULL    -- D-AUDRS-063: Lead Auditor of record who signs F 602 + closes NCs
assigned_pic_user_id       varchar(100) NULL        -- D-AUDRS-056: Supt (Marine or Tech) acting as PIC for this audit. CHECK: != lead_auditor_user_id (D-AUDRS-058)
-- Cancellation fields (D-AUDRS-064)
cancellation_reason        nvarchar(max) NULL       -- mandatory >=50 chars when status=CANCELLED
next_planned_date          date NULL                -- mandatory when cancelling; system auto-creates new PLANNED at next_planned_date - 90 days
cancelled_by               varchar(100) NULL
cancelled_at               datetime NULL
triggering_event_id        uniqueidentifier NULL   -- manual cross-ref to safety incident / near miss / complaint
audit_plan_id              uniqueidentifier NULL   -- FK master_audit_plan.id (when trigger=SCHEDULED)
parent_audit_id            uniqueidentifier NULL   -- FK psc_inspection.id (verification-of-previous link)  (D-AUDRS-029)
audit_scope                nvarchar(max) NULL
terms_of_reference         nvarchar(max) NULL      -- SQE F 602 field
opening_meeting_at         datetime NULL
closing_meeting_at         datetime NULL
prev_internal_ca_verified  varchar(10) NULL        -- YES | NO | NA  (D-AUDRS-029)
prev_external_ca_verified  varchar(10) NULL        -- YES | NO | NA  (D-AUDRS-029)
audit_summary              nvarchar(max) NULL      -- SQE F 602 "Summary of Audit"
equipment_tested           nvarchar(max) NULL      -- SQE F 602 free-text list  (D-AUDRS-028)
certificate_impact         varchar(40) NULL        -- NONE | CERT_VALID | CERT_SUSPENDED | CERT_REVOKED  (Round 1 confirm)
extension_form_ref         nvarchar(100) NULL      -- OPM F 713 reference if interval-extended  (D-AUDRS-022)
flag_notified_at           datetime NULL           -- when interval exceeded
created_by, created_date, updated_by, updated_date, is_deleted, client_id, sync_version
```

#### `audit_standards`
Many-per-audit. A harmonized audit can apply multiple standards (D-AUDRS-016).
```
id                  uniqueidentifier PK
audit_detail_id     uniqueidentifier FK audit_detail.inspection_id
standard_code       varchar(20) NOT NULL    -- ISM | ISPS | MLC | EMS
sequence_no         int NOT NULL DEFAULT 1
created_by, created_date
UNIQUE (audit_detail_id, standard_code)
```

#### `audit_team_member`
Many-per-audit. Holds non-lead auditors.
```
id                  uniqueidentifier PK
audit_detail_id     uniqueidentifier FK audit_detail.inspection_id
member_name         nvarchar(200) NOT NULL
member_designation  nvarchar(200) NULL
member_company      nvarchar(200) NULL
member_role         varchar(40) NULL    -- CO_AUDITOR | OBSERVER | TRAINEE | OTHER
sequence_no         int NOT NULL DEFAULT 1
created_by, created_date, is_deleted
```

#### `audit_meeting_attendee`
Named attendees per meeting (D-AUDRS-019). Matches `SQE F 601` Personnel Present block.
```
id                  uniqueidentifier PK
audit_detail_id     uniqueidentifier FK audit_detail.inspection_id
attendee_name       nvarchar(200) NOT NULL
attendee_rank       nvarchar(100) NULL
opening_present     bit NOT NULL DEFAULT 0
closing_present     bit NOT NULL DEFAULT 0
sequence_no         int NOT NULL DEFAULT 1
created_by, created_date, is_deleted
```

#### `audit_area_summary`
14-area inspection summary scorecard per audit (D-AUDRS-027). Matches `SQE F 602` "Inspection Summary".
```
id                  uniqueidentifier PK
audit_detail_id     uniqueidentifier FK audit_detail.inspection_id
area_code           varchar(40) NOT NULL    -- NAV | SAFETY_EQUIP | EMERGENCY_PREP | CARGO | MOORING | NC_HANDLING | PMS | TRAINING | SMS_IMPL | CERT_DOC | ENV_MGMT | SECURITY | MLC_IMPL | STRUCTURED_TRAINING
status              varchar(20) NULL        -- SATISFACTORY | NEEDS_IMPROVEMENT | NC_RAISED | NA
remarks             nvarchar(max) NULL
created_by, created_date
UNIQUE (audit_detail_id, area_code)
```

#### `rs_detail`
One row per RS inspection.
```
inspection_id           uniqueidentifier PK FK psc_inspection.id
risq_version            varchar(20) NOT NULL    -- e.g. "RISQ 3.0"
inspector_company       nvarchar(200) NOT NULL
charterer_name          nvarchar(200) NULL
vetting_outcome         varchar(40) NULL        -- ACCEPTED | ACCEPTED_WITH_OBS | NOT_ACCEPTED | PENDING_REVIEW
overall_risk_score      int NULL
outcome_letter_path     nvarchar(500) NULL      -- optional later attachment
created_by, created_date, updated_by, updated_date, is_deleted, client_id, sync_version
```

### 5.2 New Finding-Level Child Tables (or Columns — D-AUDRS-016)

If Option A (sibling tables):

#### `rs_observation`
1:1 with `psc_deficiency` (the finding row). Stores RISQ-specific fields.
```
deficiency_id           uniqueidentifier PK FK psc_deficiency.id
risq_chapter_id         uniqueidentifier FK master_risq_chapter.id
risq_question_id        uniqueidentifier FK master_risq_question.id
finding_category        varchar(20) NOT NULL    -- NO (Negative Observation) | MD (Major Discrepancy)
inspector_comment       nvarchar(max) NULL
inspector_suggestion    nvarchar(max) NULL
created_by, created_date, is_deleted
```

#### `audit_finding`
1:1 with `psc_deficiency`. Stores audit-specific fields. Per D-AUDRS-041, the `finding_type` discriminator selects which sub-table extends this record.
```
deficiency_id           uniqueidentifier PK FK psc_deficiency.id
audit_classification    varchar(30) NOT NULL    -- denormalized from audit_detail
finding_type            varchar(20) NOT NULL    -- NC | OBSERVATION  (D-AUDRS-041 discriminator; determines closure workflow + PDF template)
nc_category             varchar(20) NULL        -- when finding_type=NC: MAJOR_NC | MINOR_NC  (D-AUDRS-041 / KSM-F-NC-001)
observation_category    varchar(40) NULL        -- when finding_type=OBSERVATION: OBSERVATION | IMPROVEMENT_SUGGESTION | OFI  (D-AUDRS-041 / KSM-F-OBS-001)
standard_code           varchar(20) NULL        -- ISM | ISPS | MLC | EMS
clause_ref_id           uniqueidentifier NULL   -- FK to clause master (polymorphic via clause_master_type)
clause_master_type      varchar(20) NULL        -- ISM | ISPS | MLC | SOLAS | STCW | MARPOL | COLREG | FLAG | KSM_SMS | OTHER  (D-AUDRS-021)
clause_ref_text         nvarchar(200) NULL      -- denormalized for display / mandatory when clause_master_type=OTHER
objective_evidence      nvarchar(max) NULL
checklist_item_id       uniqueidentifier NULL   -- FK master_audit_checklist_item (D-AUDRS-020) when finding was raised against a specific checklist row
original_due_date       date NULL               -- per D-AUDRS-047: Minor NC 30d / Major NC 90d / Obs 30d
extended_due_date       date NULL
extension_reason        nvarchar(max) NULL
certificates_at_risk    nvarchar(100) NULL      -- when finding_type=NC: csv of DOC|SMC|ISSC|MLC_DMLC|NONE  (D-AUDRS-046)
is_fleetwide_relevance  bit NOT NULL DEFAULT 0  -- D-AUDRS-065: flag at NC creation if root cause likely affects sister vessels
linked_circular_id      uniqueidentifier NULL   -- D-AUDRS-065: FK to msc_data.id in Circular module when "Issue Circular" used
created_by, created_date, is_deleted
```

#### `audit_attachment` (new — D-AUDRS-060)
File uploads tied to an audit: pre-audit references, signed PDFs after physical signing, supporting docs.
```
id                  uniqueidentifier PK
audit_detail_id     uniqueidentifier FK audit_detail.inspection_id
finding_id          uniqueidentifier NULL  -- when attachment relates to a specific finding (NC or Obs)
file_name           nvarchar(255) NOT NULL
file_path           nvarchar(500) NOT NULL
file_size           int NULL  -- bytes
mime_type           varchar(100) NOT NULL  -- pdf/jpg/jpeg/docx
category            varchar(40) NOT NULL  -- PRE_AUDIT_REFERENCE | OPENING_MEETING_ATTACHMENT | CLOSING_MEETING_ATTACHMENT | AUDIT_REPORT_SIGNED_PDF | NC_CLOSURE_SIGNED_PDF | OBS_CLOSURE_SIGNED_PDF | OPM_F_713_EXTENSION_DOC | FLAG_NOTIFICATION_LETTER | OTHER
description         nvarchar(500) NULL
uploaded_by         varchar(100) NOT NULL
uploaded_at         datetime NOT NULL DEFAULT GETDATE()
is_deleted          bit NOT NULL DEFAULT 0
```

#### `audit_finding_nc` (extends `audit_finding` for NCs only — KSM-F-NC-001 fields)
1:1 with `audit_finding` when finding_type=NC. Captures the additional NC closure parts.
```
deficiency_id                       uniqueidentifier PK FK audit_finding.deficiency_id
-- Part B: Immediate containment (Master, ≤72 hrs MANDATORY for Major NC)
immediate_action_text               nvarchar(max) NULL
immediate_action_completed_at       date NULL
master_immediate_sign_name          nvarchar(200) NULL
master_immediate_sign_at            datetime NULL
-- Part C: Root Cause Analysis (Master)
rca_method                          varchar(40) NULL    -- FIVE_WHY | FISHBONE_ISHIKAWA | STRUCTURED_NARRATIVE | OTHER  (D-AUDRS-045)
rca_method_other                    nvarchar(200) NULL
problem_statement                   nvarchar(max) NULL
why_1                               nvarchar(max) NULL
why_2                               nvarchar(max) NULL
why_3                               nvarchar(max) NULL
why_4                               nvarchar(max) NULL
why_5                               nvarchar(max) NULL
root_cause_categories               nvarchar(200) NULL  -- csv of PROCEDURAL_GAP|TRAINING_GAP|SUPERVISION_FAILURE|COMMUNICATION_FAILURE|EQUIPMENT_FAILURE|HUMAN_ERROR|MANAGEMENT_SYSTEM_FAILURE|OTHER (D-AUDRS-045)
root_cause_summary                  nvarchar(max) NULL  -- 2-4 sentence summary
-- Part D: Corrective + Preventive Action
corrective_action_text              nvarchar(max) NULL
target_completion_date              date NULL
actual_completion_date              date NULL
preventive_action_text              nvarchar(max) NULL  -- fleet-wide systemic action
sms_amendment_required              bit NOT NULL DEFAULT 0
sms_amendment_doc_ref               nvarchar(200) NULL
-- Part E: Effectiveness Review (30-90 days post-closure) — performed by Lead Auditor per D-AUDRS-057
effectiveness_review_date           date NULL
effectiveness_review_method         varchar(40) NULL    -- VESSEL_FOLLOWUP_INSPECTION | REVIEW_SUBSEQUENT_AUDIT | OFFICE_DOC_REVIEW | MASTERS_REPORT
effectiveness_assessment_text       nvarchar(max) NULL
effectiveness_outcome               varchar(20) NULL    -- EFFECTIVE | PARTIALLY_EFFECTIVE | NOT_EFFECTIVE
effectiveness_further_action_text   nvarchar(max) NULL
effectiveness_signer_name           nvarchar(200) NULL  -- Lead Auditor name (was effectiveness_dpa_sign_name pre-R0.8)
effectiveness_signer_at             datetime NULL
-- Part F: Closure Acceptance — performed by Lead Auditor per D-AUDRS-057
acceptance_review_date              date NULL
acceptance_rca_adequacy_text        nvarchar(max) NULL
acceptance_decision                 varchar(20) NULL    -- ACCEPTED | RETURNED
acceptance_return_reason            nvarchar(max) NULL
acceptance_signer_name              nvarchar(200) NULL  -- Lead Auditor name
acceptance_signer_at                datetime NULL
-- Part G: Auditor Verification & Final Closure
verifying_auditor_name              nvarchar(200) NULL
verifying_authority_org             nvarchar(200) NULL
verification_method                 varchar(40) NULL    -- DOCUMENT_REVIEW | ONBOARD_VERIFICATION | PSC_AUTHORITY_CLEARANCE | NEXT_PERIODIC_SURVEY
certificate_endorsement_type        varchar(40) NULL    -- DOC | SMC | ISSC | MLC_DMLC | NONE
certificate_endorsement_ref         nvarchar(100) NULL
auditor_assessment_text             nvarchar(max) NULL
final_closure_status                varchar(30) NULL    -- CLOSED | CONDITIONALLY_CLOSED | NOT_CLOSED
resubmit_by_date                    date NULL           -- when NOT_CLOSED
auditor_verification_sign_at        datetime NULL
created_by, created_date, updated_by, updated_date
```

#### `audit_finding_obs` (extends `audit_finding` for Observations only — KSM-F-OBS-001 fields)
1:1 with `audit_finding` when finding_type=OBSERVATION. Lighter than NC.
```
deficiency_id                       uniqueidentifier PK FK audit_finding.deficiency_id
-- Part B: Vessel/Department response (Master/HOD)
responded_by_name                   nvarchar(200) NULL
responded_by_rank                   nvarchar(100) NULL
target_closure_date                 date NULL
immediate_action_text               nvarchar(max) NULL
root_cause_text                     nvarchar(max) NULL
corrective_action_text              nvarchar(max) NULL
preventive_action_text              nvarchar(max) NULL
sms_amendment_required              bit NOT NULL DEFAULT 0
sms_amendment_doc_ref               nvarchar(200) NULL
actual_closure_date                 date NULL
master_sign_name                    nvarchar(200) NULL
master_sign_at                      datetime NULL
-- Part C: Office Review & Acceptance — performed by Lead Auditor per D-AUDRS-057 (audit-trail only, does NOT gate state per D-AUDRS-040)
acceptance_review_date              date NULL
acceptance_adequacy_text            nvarchar(max) NULL
acceptance_decision                 varchar(20) NULL    -- ACCEPTED | RETURNED
acceptance_return_reason            nvarchar(max) NULL
acceptance_signer_name              nvarchar(200) NULL  -- Lead Auditor name
acceptance_signer_at                datetime NULL
-- Part D: Auditor Verification & Closure Confirmation — Lead Auditor
verifying_auditor_name              nvarchar(200) NULL
verifying_authority_org             nvarchar(200) NULL
verification_method                 varchar(40) NULL    -- DOCUMENT_REVIEW | ONBOARD_VERIFICATION | CORRESPONDENCE_REVIEW | NEXT_PERIODIC_AUDIT
auditor_remarks_text                nvarchar(max) NULL
closure_status                      varchar(30) NULL    -- CLOSED | PARTIALLY_CLOSED | NOT_CLOSED
resubmit_by_date                    date NULL
auditor_verification_sign_at        datetime NULL
created_by, created_date, updated_by, updated_date
```

**Workflow state notes (revised R0.8 per D-AUDRS-057):**
- For `finding_type=NC` on AUDIT inspections: state machine is `ALLOTTED → IN_PROGRESS → SUBMITTED_TO_PIC → PIC_REVIEW → SUBMITTED_TO_LEAD_AUDITOR → LEAD_AUDITOR_CLOSED` (NOT the PSC `SUBMITTED_TO_DPA → DPA_CLOSED` path). PIC = Supt (Marine or Tech). Closer = Lead Auditor of record (`lead_auditor_user_id` on `audit_detail`). KSM-F-NC-001 Parts E + F + G all filled by Lead Auditor.
- For `finding_type=NC` on PSC inspections: existing `SUBMITTED_TO_DPA → CLOSED` path unchanged.
- For `finding_type=OBSERVATION`: simpler state machine `NOT_STARTED → IN_PROGRESS → SUBMITTED → MASTER_CLOSED`. DPA acceptance (Part C) and Auditor verification (Part D) are recorded as audit-trail timestamps + remarks on `audit_finding_obs` but do NOT gate the CAR state. Per user direction "Observation will be limited till Master."

**Two distinct user concepts on each audit (D-AUDRS-063):**
- `conductor_user_id` — physically conducted the audit, entered data in VIMS during execution
- `lead_auditor_user_id` — Lead Auditor of record; signs F 602, closes NCs (Parts E-G), issues report
- Can be same person; often different (junior conducts under senior's supervision)
- Constraint per D-AUDRS-058: `lead_auditor_user_id != assigned_pic_user_id`; DPA *can* be Lead Auditor

#### `audit_finding_signature`
KSM SQE S 625 multi-step signature workflow (D-AUDRS-025). One row per finding.
```
deficiency_id                   uniqueidentifier PK FK psc_deficiency.id
issued_by_name                  nvarchar(200) NOT NULL
issued_by_rank                  nvarchar(100) NOT NULL
issued_at                       datetime NOT NULL
master_sign_name                nvarchar(200) NULL
master_sign_at                  datetime NULL
marine_hsseq_supt_sign_name     nvarchar(200) NULL
marine_hsseq_supt_sign_at       datetime NULL
office_notified_at              datetime NULL
office_notified_email_attach    nvarchar(500) NULL  -- path to attached email
office_confirmed_at             datetime NULL
office_confirmed_email_attach   nvarchar(500) NULL
closure_verified_by_name        nvarchar(200) NULL
closure_verified_by_rank        nvarchar(100) NULL
closure_verified_at             datetime NULL
closure_signature_path          nvarchar(500) NULL  -- path to scanned signature image
created_by, created_date, updated_by, updated_date
```

### 5.3 New Master Tables

| Master | Approx rows | Source | Notes |
|--------|-------------|--------|-------|
| `master_risq_chapter` | 14 | RightShip RISQ 3.0 doc (user-supplied) | chapter_no, chapter_title |
| `master_risq_question` | ~1,000 | RightShip RISQ 3.0 doc | FK chapter, q_number, q_text, mandatory_flag, answer_type |
| `master_ism_clause` | ~80 | IMO ISM Code 2018 (public) | clause_no (e.g. "7.1"), clause_text, section_no |
| `master_isps_clause` | ~25 | ISPS Code Part A (public) | section_no, section_title, section_text |
| `master_mlc_title` | ~30 | MLC 2006 (public) | title_no (e.g. "Title 4 Reg 4.1"), title_text |
| `master_solas_chapter` | ~14 chapters / ~150 reg refs | SOLAS (public) | chapter_no, regulation_no, title — D-AUDRS-021 |
| `master_stcw_section` | ~40 | STCW (public) | section_no (I/9, II/1, III/1...) — D-AUDRS-021 |
| `master_marpol_annex` | 6 Annexes / ~80 regs | MARPOL (public) | annex_no, regulation_no — D-AUDRS-021 |
| `master_colreg_rule` | ~38 rules | COLREG (public) | rule_no, title — D-AUDRS-021 |
| `master_ksm_sms_chapter` | ~15 | KSM SMS chapter list per `SQE S 626` | Apex / OPM / SSQE / HRM / EMS / SPM I-Nav / SPM II-Eng / SOPEP-SMPEP / Ship Security Plan / Cyber Security / BCGOM / SEEMP II / SEEMP III — D-AUDRS-021 |
| `master_audit_classification` | 4 | enum | INTERNAL / EXTERNAL / MANNING_AGENT_AUDIT / SECURITY_PROVIDER_AUDIT |
| `master_audit_subtype` | ~15 | enum | per-classification subtype values |
| `master_audit_finding_category` | 4 | enum | MAJOR_NC / NC / OBSERVATION / IMPROVEMENT_PROPOSAL  (D-AUDRS-018) |
| `master_audit_area` | 14 | enum | SQE F 602 14-area scorecard codes (D-AUDRS-027) |
| `master_audit_checklist` | ~3 in v1 | KSM forms | one row per source checklist: F 604 / F 605 / F 606. fields: checklist_code, name, auditee_type, ship_type_scope, source_form_ref. (D-AUDRS-020) |
| `master_audit_checklist_item` | ~670 | F 604 (~46) + F 605 (~543) + F 606 (~80+) | FK checklist, location_code, item_code, question, guideline, regulation_ref, ksm_sms_ref, ship_type (Common/Bulk/Others). (D-AUDRS-020) |
| `master_audit_plan` | grows | KSM SEQ Manager | planned audit register per vessel/office per period (D-AUDRS-023, expanded by D-AUDRS-049..053, 064). Fields: target_entity, audit_classification, audit_standards multi, `planned_window_start`, `planned_window_end`, `extended_due_date`, `extension_form_ref` (OPM F 713 auto-numbered), `extension_requested_at`/`_by`/`_reason`, `extension_approved_at`/`_by`/`_reason`, `flag_notified` bit + `flag_notification_date` + `flag_notification_ref` + `flag_notification_attachment`, **`cancellation_reason` + `next_planned_date` + `cancelled_by` + `cancelled_at` (D-AUDRS-064)**, `status` enum (PLANNED / CONFIRMED / IN_PROGRESS / COMPLETED / EXTENSION_REQUESTED / EXTENDED / OVERDUE / CRITICAL_OVERDUE / CANCELLED). |
| `master_charterer` | grows | optional v1 | charterer_name; v1 can stay free-text per D-AUDRS-013 |

### 5.4 Indexes (Proposed)
```
IX_audit_detail_audit_kind          ON audit_detail(audit_kind)
IX_audit_team_member_audit_id       ON audit_team_member(audit_detail_id)
IX_rs_observation_chapter           ON rs_observation(risq_chapter_id)
IX_rs_observation_category          ON rs_observation(finding_category)
IX_audit_finding_category           ON audit_finding(finding_category)
IX_audit_finding_clause             ON audit_finding(clause_ref_id)
```

---

## 6. Form Branching at `/inspections/new`

Common header (all types):
```
Inspection Type *      (PSC | RS | AUDIT | INTERNAL)
Vessel                  (auto for vessel users; pick for office)
Inspection Date *
Port / Place *
Country
Inspector Name
Report Reference
Detention checkbox      (visible: PSC | RS — Audit hides)
```

Type-specific body:

### 6.1 PSC body — unchanged
```
PSC Subtype *           INITIAL | EXPANDED | CIC | FOLLOW_UP
MOU *                   (master_mou dropdown)
Authority               PSC Officer name
[Upload Inspection Report]
[Add Deficiency: DefCode + Description + Action Code + Target Date]
```

### 6.2 RS body — new
```
RISQ Version *          (default "RISQ 3.0", future: "RISQ 3.1", "SIRE 2.0")
Inspector Company *     (free-text or master)
Charterer               (free-text or master_charterer dropdown — optional)
Vetting Outcome         ACCEPTED | ACCEPTED_WITH_OBS | NOT_ACCEPTED | PENDING_REVIEW
Overall Risk Score      integer (optional)
[Upload RISQ Report PDF]
[Add Observation:
   Chapter * (master_risq_chapter)
   Q-Number * (master_risq_question, filtered by Chapter)
   Finding Category * (NO | MD)
   Inspector Comment (free-text)
   Suggestion (free-text)
   Target Date (date)
]
```

### 6.3 Audit body — new (revised per KSM SSQE §10 + Annex 1 forms)
```
Audit Classification *  INTERNAL | EXTERNAL | MANNING_AGENT_AUDIT | SECURITY_PROVIDER_AUDIT
Audit Standards *       [ ] ISM  [ ] ISPS  [ ] MLC  [ ] EMS   (multi-select, harmonized default for INTERNAL)
Auditee Type *          VESSEL | OFFICE_DEPT | MANNING_AGENT | SECURITY_PROVIDER
Office Department       CREW | TECH | PURCHASE | IT | MARINE | OTHER   (when auditee_type=OFFICE_DEPT)
Audit Body Name         (when classification=EXTERNAL: Class society / Flag / RO)
Audit Subtype *         (filtered by classification per D-AUDRS-011)
Subtype Other           (free-text — only if subtype=OTHER)

Trigger Reason *        SCHEDULED | TAKEOVER_3MONTH | UNSCHEDULED_INCIDENT | UNSCHEDULED_NEAR_MISS | UNSCHEDULED_QUALITY_REVIEW | UNSCHEDULED_COMPLAINT | UNSCHEDULED_ROUTINE
Triggering Event        (cross-ref picker: search Safety incidents / near misses / complaints — when trigger=UNSCHEDULED_*)
Audit Plan Ref          (when trigger=SCHEDULED, pick from master_audit_plan)
Parent Audit            (when this is a verification audit, link to prior audit inspection_id)

Lead Auditor Name *
Lead Auditor Designation
Lead Auditor Company *
Lead Auditor Qualification

Audit Scope             (free-text, multiline)
Terms of Reference      (free-text — SQE F 602)

Previous Internal CA Verified   YES | NO | NA   (D-AUDRS-029)
Previous External CA Verified   YES | NO | NA   (D-AUDRS-029)

Opening Meeting At      (datetime)
Closing Meeting At      (datetime)

Personnel Present (repeatable, D-AUDRS-019, matches SQE F 601):
   Name                 *
   Rank                 (auto-suggest from HRM501 for vessel staff)
   Opening Present      (bit)
   Closing Present      (bit)

Audit Team (repeatable):
   Member Name          *
   Member Designation
   Member Company
   Member Role          CO_AUDITOR | OBSERVER | TRAINEE | OTHER

Checklist *             (auto-pick by auditee_type + standards + ship_type from master_audit_checklist;
                         user can edit/customise; F 604 / F 605 / F 606 seeds preloaded)

[Upload Audit Report PDF]

[Pre-flight Checklist Walk:                ← checklist-driven (D-AUDRS-020)
   For each row in master_audit_checklist_item filtered by checklist:
     [ ] Compliant
     [ ] Add Finding…                       ← triggers Finding modal below
     Remarks (per item)
]

[Add Finding — branched by type per D-AUDRS-040/041:

  Finding Type *           NC | OBSERVATION   (discriminator — determines closure workflow + PDF template)
  Linked Checklist Item    (optional — auto-fills clause_ref + question)
  Standard                 ISM | ISPS | MLC | EMS    (which standard this finding maps to)
  Clause Reference *       (polymorphic master picker scoped by clause_master_type;
                            free-text fallback when type=OTHER)
  Objective Evidence       (free-text — SSQE §10.5.4)
  Description *            (free-text — auditor's verbatim NC/Observation text)

  IF finding_type=NC:
     NC Category *         MAJOR_NC | MINOR_NC                  (D-AUDRS-041)
     Certificates at Risk  [ ] DOC [ ] SMC [ ] ISSC [ ] MLC/DMLC [ ] None  (D-AUDRS-046)
     Required Closure Deadline   (default: Minor 30d / Major 90d per D-AUDRS-047)
     → on save: routes to NC closure flow (KSM-F-NC-001 template, 7 parts, full DPA close + Effectiveness Review + Auditor Verification)

  IF finding_type=OBSERVATION:
     Observation Category *  OBSERVATION | IMPROVEMENT_SUGGESTION | OFI   (D-AUDRS-041)
     Target Closure Date     (default: 30d per D-AUDRS-047)
     → on save: routes to Observation closure flow (KSM-F-OBS-001 template, 4 parts, terminal at Master_Closed)
]

14-Area Inspection Summary Scorecard       (D-AUDRS-027, matches SQE F 602)
   Navigation Procedures         [Satisfactory | Needs Improvement | NC Raised | NA]
   Safety Equipment & Procedures [..]
   Emergency Preparedness        [..]
   Cargo                         [..]
   Mooring / Anchoring           [..]
   Non-Conformity Handling       [..]
   Planned Maintenance System    [..]
   Training                      [..]
   SMS Implementation            [..]
   Certificate & Document Control[..]
   Environment Management        [..]
   Security                      [..]
   MLC Implementation            [..]
   Structured Training           [..]
   (Each area: Remarks free-text)

Equipment Tested Successfully    (free-text repeatable list — D-AUDRS-028 / SQE F 602)

Audit Summary                    (free-text — Summary of audit + important conclusions per SQE F 602)

Auditor Signature                (lead auditor name + date)
Master Signature                 (Master name + date, on submission)
```

**Per-finding closure forms — TWO templates** (D-AUDRS-040/042/043):

---

### 6.4 NC closure flow (KSM-F-NC-001, 7 parts, 2-page PDF)

```
PART A — NC Details (Auditor at issuance)
  NC Ref No. (auto: NC-{vessel}-{YYYY}-{NNN})
  Date of Audit · Vessel Name · Port/Location
  Auditor Name & Organisation · Survey/Report Ref.
  Code/Regulation Reference (polymorphic clause master)
  KSM SMS/Procedure Ref.
  Objective Evidence (verbatim from audit report — accuracy critical)
  Auditor Signature · NC Issued Date · Required Closure Deadline
  Certificate at Risk: [ ] DOC [ ] SMC [ ] ISSC [ ] MLC/DMLC [ ] None

PART B — Immediate / Containment Action (Master, ≤72 hrs MANDATORY for Major NC)
  Action Taken Immediately (what / who / date+time)
  Date Immediate Action Completed
  Master / Officer Sign-off + Date  ← state: SUBMITTED_TO_PIC (existing CAR engine reused)

PART C — Root Cause Analysis (Master, MANDATORY for all NCs)
  RCA Method: ( ) 5-Why ( ) Fishbone-Ishikawa ( ) Structured-Narrative ( ) Other
  Problem Statement
  Why 1 → Why 2 → Why 3 → Why 4 → Why 5
  Root Cause Category (multi): [ ] Procedural Gap [ ] Training Gap [ ] Supervision
                                [ ] Communication [ ] Equipment [ ] Human Error
                                [ ] Mgmt System [ ] Other
  Root Cause Summary (2-4 sentences)

PART D — Corrective + Preventive Action Plan (Master)
  Corrective Action(s) (what / who / target & actual dates / evidence refs)
  Target Completion Date · Actual Completion Date
  Preventive / Systemic Action (fleet-wide)
  SMS Amendment Required? [ ] Yes [ ] No   (if Yes: doc no, rev, date)
  Evidence of Closure (9 checkbox options + Other free-text)

PART E — DPA Effectiveness Review (30-90 days post-closure)    ← NEW workflow stage (D-AUDRS-044)
  Review Date
  Method: ( ) Vessel followup ( ) Subsequent audit/PSC ( ) Office doc review ( ) Master's Report
  Effectiveness Assessment text
  Outcome: ( ) EFFECTIVE ( ) PARTIALLY_EFFECTIVE ( ) NOT_EFFECTIVE
  Further Action Required (if any)
  DPA Signature + Date

PART F — DPA Closure Acceptance
  Reviewed By (Name, Designation) · Review Date
  RCA Adequacy Assessment text
  Closure Decision: ( ) ACCEPTED ( ) RETURNED + reason
  DPA Signature + Date

PART G — Auditor Verification & Final Closure
  Verifying Auditor / Authority + Survey Ref.
  Method: ( ) Doc Review ( ) Onboard Verification ( ) PSC Authority Clearance ( ) Next Periodic Survey
  Certificate / Endorsement: DOC | SMC | ISSC | MLC/DMLC | None  + Ref. No.
  Auditor's Assessment of CA Package
  NC Closure Status: ( ) CLOSED ( ) CONDITIONALLY_CLOSED + follow-up at next survey ( ) NOT_CLOSED + resubmit-by date
  Auditor Signature + Date · Official Stamp / Survey Endorsement
```

---

### 6.5 Observation closure flow (KSM-F-OBS-001, 4 parts, 1-page PDF)

```
PART A — Observation Details (Auditor / Office at issuance)
  Observation Ref. No. (auto: OBS-{vessel}-{YYYY}-{NNN})
  Date of Audit · Vessel Name · Audit Type · Location
  Auditor Name & Organisation
  SMS / Regulatory Reference
  Observation Category: ( ) Observation ( ) Improvement Suggestion ( ) OFI
  Observation Description (verbatim — do NOT paraphrase)
  Auditor Signature · Date Issued

PART B — Vessel / Department Response (Master / HOD)    ← terminal state for VIMS workflow per D-AUDRS-040
  Responded by (Name + Rank) · Target Closure Date
  Immediate / Interim Action Taken
  Root Cause (structured — 5-Why or simple cause-and-effect; not vague)
  Corrective Action(s) (what / who / when)
  Preventive / Systemic Action (fleet-wide if any)
  SMS Amendment Required? Yes/No + ref
  Evidence Checklist (8 options + Other)
  Actual Closure Date
  Master / HOD Signature  ← state: MASTER_CLOSED

PART C — DPA Office Review & Acceptance (recorded but does NOT gate VIMS state)
  Reviewed By · Review Date
  Adequacy of Corrective Action text
  Closure Decision: ( ) ACCEPTED ( ) RETURNED + reason
  DPA Signature

PART D — Auditor Verification & Closure Confirmation (recorded but does NOT gate)
  Verifying Auditor / Authority + Survey Ref.
  Method: ( ) Doc Review ( ) Onboard ( ) Correspondence ( ) Next Periodic Audit
  Auditor's Remarks on Closure
  Closure Status: ( ) CLOSED ( ) PARTIALLY_CLOSED + resubmit-by date ( ) NOT_CLOSED
  Auditor Signature + Date of Closure Confirmation
```

**State-machine comparison:**
- **NC**: ALLOTTED → IN_PROGRESS → SUBMITTED_TO_PIC → PIC_REVIEW → SUBMITTED_TO_DPA → CLOSED → (30-90d wait) → EFFECTIVENESS_REVIEWED → AUDITOR_VERIFIED. Reuses existing CAR state machine through CLOSED; adds two post-closure states (D-AUDRS-044).
- **Observation**: NOT_STARTED → IN_PROGRESS → SUBMITTED → MASTER_CLOSED (terminal). DPA Part C and Auditor Part D are audit-trail timestamps only — not state gates (D-AUDRS-040).

---

## 7. Roles & RBAC Delta

Existing roles cover everything (D-AUDRS-015). The only RBAC changes are **two new process gates**:

| New gate | Purpose | Granted to |
|----------|---------|------------|
| `PSC_P_017` | View / create RS inspections | Same as `PSC_P_003` (Master + Office) |
| `PSC_P_018` | View / create Audit inspections | Same as `PSC_P_003` (Master + Office) |

(Confirmed in Round 1 — may collapse into existing `PSC_P_003` if no UI-level differentiation is needed.)

No new form gates. The Inspection module sidebar entry (`PSC_F_002`) remains the single visibility key — RS and Audit inspections appear in the same list, just filtered by type.

---

## 8. Out of Scope (v1)

| Item | Reason | Defer to |
|------|--------|----------|
| SIRE 2.0 (OCIMF) inspections | Not asked for v1 | v1.1 if tanker fleet onboarded |
| RISQ legacy / free-text format | Not asked | v1.1 |
| Generic charterer vetting in RS branch | Folded into Audit "Other" instead | — |
| Re-inspection / follow-up for RS and Audit | D-AUDRS-012 | v1.1 |
| External auditor portal (login) | D-AUDRS-015 | v2+ |
| MLC / Navigation / Cargo / Tanker as separate audit kinds | Folded into harmonised audit_standards multi-select (D-AUDRS-016) | v1.1 if needed |
| **Superintendent Visit / Vessel Inspection Report (SQE F 607)** | Different inspection shape — KPIs (speed/consumption, M/E performance, generators, cargo discharge, downtime, financial budget vs actual) + 0–9 Condition Rating scale (Cosmetic / Structural / Safety / Overall). KSM links Supdt visit to NC verification (SSQE §10.7.5). | **v1.1 candidate as 5th inspection_type** — would reuse same module + CAR engine but add a `psc_supt_visit_detail` table and a KPI/condition-rating capture screen |
| RISQ scoring algorithm replication | Vetting outcome / score stored as data only, not computed | v2 |
| Auto-import RISQ XML from RightShip portal | No public API | v2 |
| Audit certificate-impact integration with VIMS Certificates module | Separate module (already complete) — may cross-link in v1.1 | v1.1 |
| Multi-language UI / forms | Not requested | v2 |
| Bulk finding import from PDF parser | Manual entry only at v1 | v1.1 if entry volume becomes painful |
| Auto-trigger Audit creation from incident/near-miss closure | D-AUDRS-024 captures the trigger reason and FK, but the *automatic* prompt to schedule an unscheduled audit from a Safety incident is out of v1 | v1.1 cross-module workflow |
| Auto-generation of monthly SQE S 626 as scheduled job | v1: on-demand export only (D-AUDRS-026). Automated 7th-of-month delivery to HSSEQ@kaizenship.net deferred. | v1.1 |

---

## 9. Decisions Log

| # | ID | Round | Decision | Source |
|---|----|-------|----------|--------|
| 1 | D-AUDRS-001 | R0 | In-place extension of existing Inspection module. Same `/inspections` entry, same CAR engine. | User confirmation |
| 2 | D-AUDRS-002 | R0 | CAR numbering already type-driven (PSC-/RS-/AUDIT- prefixes from `inspection_type`). No trigger change. | Derived from D-001 + verification of `trg_psc_deficiency_auto_create_car` |
| 3 | D-AUDRS-003 | R0 | CAR state machine, evidence rules, PIC/DPA closure, rework, physical verification, notifications, sync, audit log unchanged for RS/Audit. | Derived from D-001 |
| 4 | D-AUDRS-004 | R0 | Audit kinds v1: ISM Internal, ISM External, ISPS, Other (free-text bucket for MLC/Navigation/Cargo/Tanker/Vetting). | User multi-select |
| 5 | D-AUDRS-005 | R0 | RS v1: RISQ 3.0 only. | User single-select |
| 6 | D-AUDRS-006 | R0 | RS finding = Q-number + NO/MD + comment (structured). | User: "Full structured (Recommended)" |
| 7 | D-AUDRS-007 | R0 | Audit finding = category (Major NC / Minor NC / Obs / OFI) + clause-ref (per-kind master) + objective evidence. | User: "Category enum + clause reference master (Recommended)" |
| 8 | D-AUDRS-008 | R0 | Strict 1:1 finding → CAR for all types. | User: "Keep strict 1:1 (Recommended)" |
| 9 | D-AUDRS-009 | R0 | Evidence rule unchanged: ≥1 BEFORE + ≥1 AFTER per CAR. | User: "Same as PSC (Recommended)" |
| 10 | D-AUDRS-010 | R0 | Audit registration: lead auditor (name+co+qual) + team list + opening/closing meeting (datetime + attendee count) + scope. | User: "Lead auditor + team + meetings (Recommended)" |
| 11 | D-AUDRS-011 | R0 | Audit subtype enums per kind (ISM Internal = ANNUAL_INTERNAL; ISM External / ISPS = INITIAL/ANNUAL/INTERMEDIATE/RENEWAL/ADDITIONAL; MLC = INITIAL/INTERMEDIATE/RENEWAL; Other = free-text). | User: "Structured per audit kind (Recommended)" |
| 12 | D-AUDRS-012 | R0 | v1: no follow-up/re-inspection for RS or Audit. PSC FOLLOW_UP unchanged. | User: "Skip follow-up for v1" |
| 13 | D-AUDRS-013 | R0 | RS registration: RISQ version + inspector co + charterer + vetting outcome (ACCEPTED / ACCEPTED_WITH_OBS / NOT_ACCEPTED / PENDING_REVIEW) + optional risk score. | User: "RISQ version + Inspector co + Charterer + Outcome + Score (Recommended)" |
| 14 | D-AUDRS-014 | R0 | Masters: RISQ 3.0 from user PDF/Excel (LLM extract); ISM/ISPS/MLC from public regulatory text. | User multi-select |
| 15 | D-AUDRS-015 | R0 | **REVISED in R0.5 (see D-AUDRS-039)**. Original: lead auditor is data, not user. Revised: assigned auditor IS a system user (existing office user — OFFICE_PIC / OFFICE_SSQE / OFFICE_SUPT) granted per-audit capability via `audit_detail.assigned_auditor_user_id` + boolean flag on `master_qualified_auditor`. They log in to prepare audit docs post-audit. No new role; existing office users get an additional per-audit assignment. |
| 16 | D-AUDRS-016 | R0.5 | Multi-standard harmonized audit: `audit_classification` + `audit_standards` multi (ISM/ISPS/MLC/EMS). | SSQE §10.2.1 + SQE F 601 ("INTERNAL ISM, MLC, ISPS AND EMS AUDIT") |
| 17 | D-AUDRS-017 | R0.5 | Auditee type field: VESSEL / OFFICE_DEPT / MANNING_AGENT / SECURITY_PROVIDER. | SSQE §10.2.3 + SQE F 604 (Manning Office audit) + SQE F 606 (Office Internal Audit) |
| 18 | D-AUDRS-018 | R0.5 | **SUPERSEDED by D-AUDRS-041**. (Originally: 4-tier enum from older SQE S 625 Rev-02 2022 form. Re-superseded once newer KSM-F-NC-001 + KSM-F-OBS-001 Rev-01 Jan-2026 forms were introduced.) | older SQE S 625 (now replaced) |
| 19 | D-AUDRS-019 | R0.5 | Named-attendee table per meeting (name, rank, opening/closing flags). Supersedes count-only attendee in D-AUDRS-010. | SQE F 601 Personnel Present block + SSQE §10.5.2 |
| 20 | D-AUDRS-020 | R0.5 | Audit checklist master scoped by auditee_type + standards + ship_type. Seeds: F 604 (~46), F 605 (~543), F 606 (~80+). | KSM Annex 1 forms F 604/605/606 + SSQE §10.4.4 |
| 21 | D-AUDRS-021 | R0.5 | Clause-reference master scope expanded to SOLAS / STCW / MARPOL / COLREG / Flag / Class / KSM SMS chapters. Supersedes/expands D-AUDRS-014. | SSQE §10.7.3 (NC definition) |
| 22 | D-AUDRS-022 | R0.5 | Audit interval enforcement (max 12 / min 8 months) + 3-month extension via OPM F 713 + 3-month takeover audit. | SSQE §10.3.2 + §10.3.3 |
| 23 | D-AUDRS-023 | R0.5 | `master_audit_plan` register table. | SSQE §10.3.4 + SQE F 601 |
| 24 | D-AUDRS-024 | R0.5 | Audit trigger reason enum + optional FK to triggering event. | SSQE §10.3.6 + §10.3.7 |
| 25 | D-AUDRS-025 | R0.5 | **SUPERSEDED by D-AUDRS-042+043** (the SQE S 625 chain was based on the older form). Newer signature chains differ by finding_type: NC has 5-step chain (Master immediate → Master CA → DPA effectiveness → DPA acceptance → Auditor verification) per KSM-F-NC-001 Parts B/D/E/F/G; Observation has 3-step chain (Master → DPA → Auditor) per KSM-F-OBS-001 Parts B/C/D. | KSM-F-NC-001 + KSM-F-OBS-001 |
| 26 | D-AUDRS-026 | R0.5 | Monthly Master KPI export (SQE S 626) — on-demand v1, scheduled v1.1. | SSQE §10.6.4 + SQE S 626 |
| 27 | D-AUDRS-027 | R0.5 | 14-area inspection summary scorecard at audit header. | SQE F 602 §Inspection Summary |
| 28 | D-AUDRS-028 | R0.5 | Equipment-tested-successfully free-text list per audit. | SQE F 602 |
| 29 | D-AUDRS-029 | R0.5 | Previous internal/external CA verified Y/N/NA gates at registration. | SQE F 602 |
| 30 | D-AUDRS-030 | R0.5 | **SUPERSEDED by D-AUDRS-047** — closure target now per finding_type/category: Minor NC = 30 days, Major NC = 90 days (typically 3 months), Observation = 30 days. | KSM-F-NC-001 + KSM-F-OBS-001 notes |
| 31 | D-AUDRS-031 | R0.5 | External audits use same categories + DPA closure path. `audit_body_name` captures Class/Flag/RO. | SSQE §10.12 |
| 32 | D-AUDRS-032 | R0.5 | PSC + RightShip observations are NCs in the KSM model. Unified NC funnel; type-specific UI labelling preserved. | SSQE §10.8.4 + §10.13 |
| 33 | D-AUDRS-033 | R0.5 | **Build phasing: v1.0 = Vessel Internal Audit ONLY. v1.1 = External Audit. v1.2 = RightShip RISQ 3.0. v1.3+ = Manning Agent + Security Provider audits.** RightShip is explicitly OUT of v1.0 freeze per user direction — even though it shares the CAR engine and would technically slot in cheaply, the user wants the v1.0 freeze tight to Internal Audit so the spec / DocSuite / handover ship without RS noise. Internal Audit carries all the structural complexity (multi-standard harmonisation, checklist masters F 604/605/606, audit plan register, interval enforcement, named-attendee meetings, 14-area scorecard, per-NC signature chain). External Audit (v1.1) is much simpler — same finding categories + same closure path; external auditor brings their own framework so no checklist seeding needed. RightShip (v1.2) adds RISQ Q-bank master + observation entry but reuses the entire NC closure infrastructure built in v1.0. Round 1 interrogation and DocSuite generation scope to Internal Audit only. | User direction 2026-05-13 (initially conflated with RS, corrected the same day) |
| 34 | D-AUDRS-034 | R0.5 | **DPA = SEQ Manager** at KSM, per SSQE §1.2.2 ("DPA (SEQ Manager)"). The existing CAR engine's "DPA close" terminal state correctly maps to SSQE §10.6.3's "SEQ Manager signs F 602 to close audit." No new role split needed; no rename of CAR engine terminology. UI may display "SEQ Manager" or "DPA" interchangeably in audit context. | SSQE §1.2.2 + §10.6.3 |
| 35 | D-AUDRS-035 | R0.5 | **Qualified Auditor master.** SSQE §10.4.1 mandates auditor assignment from a "List of Qualified Auditors". v1 implementation: new `master_qualified_auditor` table (or boolean `is_qualified_auditor` flag on `users` with `auditor_qualification` text field — Round 1 decide). Field: user_id FK to `users`, qualification_text, qualification_date, expiry_date, scope (standards they can audit). | SSQE §10.4.1 |
| 36 | D-AUDRS-036 | R0.5 | **Audit-level signature chain** (distinct from per-NC SQE S 625 signatures). Captured on `audit_detail` or sibling `audit_signature` table: lead_auditor_sign_at, master_sign_at (closing meeting acknowledgment), seq_manager_close_at (F 602 final close-out — corresponds to existing CAR engine DPA_CLOSED at audit header). Each accompanied by optional signature-image path. | SSQE §10.5.7 + §10.6.3 + SQE F 602 |
| 37 | D-AUDRS-037 | R0.5 | **Auditor's pre-audit dashboard** surfaces (a) previous-audit findings on the target vessel/office and (b) outstanding NCs from any source (PSC/RS/Audit). Reuses existing `/deficiencies` route with vessel_id filter + status=open. New widget on auditor home for "Audits assigned to me". No new screen needed at v1. | SSQE §10.4.3 |
| 38 | D-AUDRS-038 | R0.5 | **Two new notification types** in `psc_notification`: `AUDIT_SCHEDULED` (sent to Master + HoDs when audit_plan entry confirmed), `AUDIT_NC_RAISED` (sent to assigned action owner when a finding's CAR is created). | SSQE §10.4.1 |
| 39 | D-AUDRS-039 | R0.5 | **Audit is OFFICE-initiated**, not vessel-initiated (diverges from PSC where Master creates the inspection). Workflow: (1) Office (SEQ Manager) creates audit_plan entry; **Lead Auditor assigned by DPA per D-AUDRS-108** (modified 2026-05-18); (2) System notifies vessel Master + HoDs (vessel) / HoD + key staff + DPA + auditor team (office, per D-AUDRS-102/106); (3) Audit physically takes place onboard / at office HQ; (4) **Assigned auditor logs into VIMS and prepares all audit docs in the system** — registers the audit record, enters findings, attaches evidence; (5) Findings (NCs / Observations) routed to vessel/dept for closure work. The "create inspection" entry point on `/inspections/new` for AUDIT type is restricted to office users with `is_assigned_auditor=true` for an open audit_plan entry. | User direction 2026-05-13 + modified 2026-05-18 |
| 40 | D-AUDRS-040 | R0.5 | **NC and Observation have DIVERGENT closure workflows** (per KSM-F-NC-001 and KSM-F-OBS-001 templates effective Jan-2026 Rev 01): **NC** = existing PSC CAR state machine, full Master → PIC → DPA close, with mandatory DPA Effectiveness Review 30-90 days post-closure, then Auditor Verification. **Observation** = lighter state machine, terminal at Master (`MASTER_CLOSED`); DPA acceptance and Auditor verification recorded as audit-trail fields but do NOT gate the workflow state. | User direction 2026-05-13 + KSM-F-NC-001/F-OBS-001 forms |
| 41 | D-AUDRS-041 | R0.5 | **REVISED finding category enum.** Supersedes D-AUDRS-018. Two distinct enums per closure-form template: **`nc_category` ∈ {MAJOR_NC, MINOR_NC}** (per KSM-F-NC-001 NC CLASSIFICATION) · **`observation_category` ∈ {OBSERVATION, IMPROVEMENT_SUGGESTION, OFI}** (per KSM-F-OBS-001 Observation Category). `finding_type` discriminator on `audit_finding` distinguishes which form template applies: `NC` vs `OBSERVATION`. | KSM-F-NC-001 + KSM-F-OBS-001 |
| 42 | D-AUDRS-042 | R0.5 | **NC closure form template = KSM-F-NC-001** (Form No., Rev 01, Jan-2026). 2 pages, 7 parts: A Auditor issuance + B Master immediate containment (Major NC: ≤72 hrs MANDATORY) + C Master RCA + D Master CA/PA + E **DPA Effectiveness Review 30-90 days post-closure** + F DPA Closure Acceptance + G Auditor Verification & Final Closure. PDF generator `audit_nc_pdf.py` renders this layout. | KSM-F-NC-001 |
| 43 | D-AUDRS-043 | R0.5 | **Observation closure form template = KSM-F-OBS-001** (Form No., Rev 01, Jan-2026). 1 page, 4 parts: A Auditor/Office issuance + B Master/HOD response (immediate action + root cause + CA + evidence) + C DPA Office Review & Acceptance + D Auditor Verification & Closure. PDF generator `audit_obs_pdf.py` renders this layout. | KSM-F-OBS-001 |
| 44 | D-AUDRS-044 | R0.5 | **DPA Effectiveness Review is a new workflow stage** for NCs only. After CAR moves to CLOSED (Master → PIC → DPA chain), wait 30-90 days, then DPA performs effectiveness review with method enum {`VESSEL_FOLLOWUP_INSPECTION`, `REVIEW_SUBSEQUENT_AUDIT`, `OFFICE_DOC_REVIEW`, `MASTERS_REPORT`} and outcome enum {`EFFECTIVE`, `PARTIALLY_EFFECTIVE`, `NOT_EFFECTIVE`}. If NOT_EFFECTIVE, finding re-opens (reuses existing `REWORK_REQUESTED` semantics). New table or fields on `audit_finding`. | KSM-F-NC-001 Part E |
| 45 | D-AUDRS-045 | R0.5 | **RCA Method enum on NCs**: `FIVE_WHY` / `FISHBONE_ISHIKAWA` / `STRUCTURED_NARRATIVE` / `OTHER`. Captured on `audit_finding.rca_method`. Plus **Root Cause Category multi-select** (8 options): `PROCEDURAL_GAP` / `TRAINING_GAP` / `SUPERVISION_FAILURE` / `COMMUNICATION_FAILURE` / `EQUIPMENT_FAILURE` / `HUMAN_ERROR` / `MANAGEMENT_SYSTEM_FAILURE` / `OTHER`. | KSM-F-NC-001 Part C |
| 46 | D-AUDRS-046 | R0.5 | **Certificate-at-risk capture** for NCs: multi-select from `DOC` / `SMC` / `ISSC` / `MLC_DMLC` / `NONE`. Stored as `audit_finding.certificates_at_risk` (json array) or junction table. Surfaces on dashboard as "NCs threatening certificate validity." | KSM-F-NC-001 Part A |
| 47 | D-AUDRS-047 | R0.5 | **Default closure deadlines per finding type/category**: Minor NC = 30 days · Major NC = 90 days (per auditor/class — typically 3 months) · Observation/OFI = 30 days. Encoded as `default_target_days` per category lookup. Supersedes D-AUDRS-030's flat 90-day rule. | KSM-F-NC-001 Notes §7 + KSM-F-OBS-001 Notes §5 |
| 48 | D-AUDRS-048 | R0.5 | **Returned-for-resubmit workflow** for both NC and Observation. Either DPA (NC Part F / Obs Part C) or Auditor (NC Part G / Obs Part D) can return finding with reason. Reuses existing `REWORK_REQUESTED` CAR status. NC also supports `CONDITIONALLY_CLOSED` state at Auditor Verification (Part G). | KSM-F-NC-001 Parts F+G · KSM-F-OBS-001 Parts C+D |
| 49 | D-AUDRS-049 | R0.7 | **Audit window computation.** For each vessel: `next_due_window_start = last_audit_completion_date + 8 months`, `next_due_window_end = last_audit_completion_date + 12 months`. For new-vessel takeover: `next_due_window_end = takeover_date + 3 months`, no window_start (immediate). For office audits: window = 9-15 months. Computed daily; surfaced on dashboard + audit-plan register. Stored on `master_audit_plan` as `planned_window_start`, `planned_window_end`. | SSQE §10.3.2 + §10.3.3 |
| 50 | D-AUDRS-050 | R0.7 | **Progressive audit-due alerts.** Calculated relative to `planned_window_end` (the 12-month limit, ignoring extension):<br>· **T-90 days**: notify SEQ Manager — system auto-creates draft `master_audit_plan` entry with `status=PLANNED`.<br>· **T-30 days**: escalate notification to DPA. Master + HoDs informed.<br>· **T-0 (window_end reached)**: `status=OVERDUE`. Dashboard banner on Master's home. Certificate-at-risk warning displayed.<br>· **T+30, +60 days**: dashboard banner promoted to critical-red. Notification escalated to Managing Director.<br>· **T+90 days (15-month total limit reached)**: if extension not approved AND Flag not notified, `status=CRITICAL_OVERDUE`. Certificate-at-risk flag SET on vessel. Audit registration unblocked but every audit-related action shows "Certificate at Risk — Flag must be notified" banner until resolved. | SSQE §10.3.2 / industry-standard alerting cadence |
| 51 | D-AUDRS-051 | R0.7 | **OPM F 713 extension request workflow** inside VIMS. SEQ Manager raises "Request Audit Window Extension" on an overdue (or T-30) `master_audit_plan` entry. Form: `reason_for_delay` (text, mandatory ≥50 chars), `proposed_new_target_date` (must be ≤ planned_window_end + 3 months), `justification_files[]` (uploads). Status moves to `EXTENSION_REQUESTED`. DPA reviews and either APPROVES (sets `extended_due_date`, `extension_form_ref=OPM-F-713-{YYYY}-{NNN}` auto-generated, `extension_approved_at`, `extension_approved_by`, `extension_reason` copied) or REJECTS with reason. On approval: status → `EXTENDED`. On rejection: status → previous (overdue or planned) with rejection_reason recorded. | SSQE §10.3.2 OPM F 713 reference |
| 52 | D-AUDRS-052 | R0.7 | **Flag notification capture.** Separate manual capture by DPA (not auto). Fields on `master_audit_plan`: `flag_notified` (bit), `flag_notification_date` (date), `flag_notification_ref` (correspondence reference number), `flag_notification_attachment` (file path to letter/email). Trigger: when extension is requested OR extended_due_date is approaching, DPA prompt: "Has Flag been notified per ISM Code?" UI badge "Flag Notified ✓" on vessel header. If `flag_notified=false` AND `extended_due_date < today`: critical alert continues until set. | SSQE §10.3.2 ("Flag may be notified in case of extension taken") |
| 53 | D-AUDRS-053 | R0.7 | **Status enum extension on `master_audit_plan`:** `PLANNED` (system-created draft, window open) → `CONFIRMED` (SEQ Manager finalised date + auditor) → `IN_PROGRESS` (audit started — opening meeting timestamp set) → `COMPLETED` (DPA closed audit per SSQE §10.6.3) → triggers next-cycle PLANNED entry for that vessel.<br>Parallel branches: `OVERDUE` (T-0 reached without COMPLETED) → `EXTENSION_REQUESTED` → `EXTENDED` (DPA approved) → `IN_PROGRESS` → `COMPLETED`. If extended_due_date breached: `CRITICAL_OVERDUE`. Any state → `CANCELLED` with reason (e.g. vessel sold, fleet exit). | SSQE §10.3.2 + §10.3.4 + §10.6.3 |
| 54 | D-AUDRS-054 | R0.7 | **Office Internal Audit added to v1.0 freeze** (alongside Vessel Internal Audit). SSQE §10.3.3 makes office audits a parallel mandatory track to vessel audits ("all aspects of SMS shall be audited annually in the Head Office"). Same module, same registration form, same NC/Observation closure forms, same OPM F 713 extension flow. Difference: `auditee_type=OFFICE_DEPT` (with `auditee_office_dept` enum CREW / TECH / PURCHASE / IT / MARINE / OTHER); F 606 checklist seed in addition to F 605; no `TAKEOVER_3MONTH` trigger applies (office doesn't have vessel-takeover semantics); cadence per §10.3.3 = annual with 9–15 month spread between successive office audits. Updates D-AUDRS-033 phasing: v1.0 now covers Vessel Internal + Office Internal; v1.1 = External; v1.2 = RightShip; v1.3 = Manning Agent + Security Provider. | User direction 2026-05-13 + SSQE §10.3.3 |
| 55 | D-AUDRS-055 | R0.7 | **F 601 PDF output added.** SEQ Manager / assigned auditor can generate the audit plan as a printable PDF mirroring `SQE F 601` for sharing with auditee before the audit (per SSQE §10.4.1 "auditee shall be notified about the date and scope of the audit"). Generator `audit_plan_pdf.py` renders all F 601 fields (audit performed at, dates, type, lead auditor, audit team, schedule blocks, personnel present). Closes the gap that only F 602 was previously locked as PDF output. **v1.0 PDF output summary:** F 601 (audit plan), F 602 (audit report), KSM-F-NC-001 (NC closure), KSM-F-OBS-001 (Obs closure), SQE S 626 (monthly KPI). | SSQE §10.4.1 + F 601 |
| 56 | D-AUDRS-056 | R0.8 | **[SUPERSEDED 2026-05-18 by D-AUDRS-107]** Original: Audit PIC role = Supt (Marine or Tech), same as PSC PIC. The CAR engine's PIC review step (`SUBMITTED_TO_PIC → PIC_REVIEW`) for audit findings is performed by an OFFICE_SUPT user (Marine or Tech). No new role; reuses existing OFFICE_SUPT role assignment. **Replaced by PSC's open-pool pattern — any office user with scope + AUDIT_P_004 gate can act; no named PIC at plan time.** | User direction 2026-05-13 |
| 57 | D-AUDRS-057 | R0.8 | **Audit finding closure by Lead Auditor (not DPA).** SUPERSEDES the DPA-close part of D-AUDRS-040 for audit findings. CAR state machine for audit findings: `ALLOTTED → IN_PROGRESS → SUBMITTED_TO_PIC → PIC_REVIEW → SUBMITTED_TO_LEAD_AUDITOR → LEAD_AUDITOR_CLOSED`. PSC findings continue to terminate at DPA_CLOSED (unchanged). Implementation: reuse existing state column; gate transitions with RBAC check on `assigned_lead_auditor_user_id`. KSM-F-NC-001 Parts E (Effectiveness Review), F (Closure Acceptance), G (Verification) are all performed by the Lead Auditor for audit findings (the form's "DPA" labels in Parts E + F apply only when Lead Auditor = DPA; the form fields are filled by whoever holds the Lead Auditor role for that audit). | User direction 2026-05-13 |
| 58 | D-AUDRS-058 | R0.8 | **Lead Auditor role constraints — enforcement-point modified 2026-05-18 by D-AUDRS-110.** (a) Lead Auditor **cannot be** the PIC for the same audit. Originally a plan-time uniqueness check on `assigned_lead_auditor_user_id != assigned_pic_user_id`; **now enforced at action time** (D-110) — server rejects "Start PIC Review" action if `current_user_id == audit.lead_auditor_user_id` with HTTP 403. (b) DPA **can be** Lead Auditor — DPA wearing auditor hat is allowed; orthogonal to the PIC rule. (c) Lead Auditor must be drawn from `master_audit_qualified_auditor` with active, non-expired qualification matching the audit's standards (D-094). PIC qualification dropped (open pool per D-107). | User direction 2026-05-13 + modified 2026-05-18 |
| 59 | D-AUDRS-059 | R0.8 | **External Audit closure cycle (v1.1 design note, NOT in v1.0 build).** Different from internal audits: Master ↔ Class Auditor cycle bypasses VIMS' internal CAR workflow. PIC provides comments only (advisory, no state gating). Final closure is performed **out-of-system** (paper / external system); user updates VIMS with closure timestamp + closure-attachment after Class confirms. Status: external audit findings have a simpler state machine with `EXTERNAL_CLOSED` terminal state set by Master with attachment. Captured here for v1.1 planning; not in v1.0 build. | User direction 2026-05-13 |
| 60 | D-AUDRS-060 | R0.8 | **Pre-audit document upload area.** Auditor can upload reference documents (SMS extracts, prior audit reports, previous PSC reports, vessel particulars) on the audit record **before execution begins**. New table `audit_attachment` keyed off `audit_detail.inspection_id`. Fields: `file_name`, `file_path`, `file_size`, `mime_type`, `category` enum (`PRE_AUDIT_REFERENCE` / `OPENING_MEETING_ATTACHMENT` / `CLOSING_MEETING_ATTACHMENT` / `AUDIT_REPORT_SIGNED_PDF` / `OTHER`), `description`, `uploaded_by`, `uploaded_at`. PDF/JPG/JPEG/DOCX accepted. Visible to auditor + Master + DPA + Supt. | User direction 2026-05-13 |
| 61 | D-AUDRS-061 | R0.8 | **Physical signatures only — no digital signatures at v1.0.** Workflow: VIMS generates the PDF (F 601 / F 602 / KSM-F-NC-001 / KSM-F-OBS-001), user prints, signs physically, scans back, uploads to VIMS as an attachment on the relevant record. PDF signature fields are rendered as blank signature lines. Date + name fields capture the signer info pre-print; physical signature happens on paper. The signed scan is stored in `audit_attachment` with `category=AUDIT_REPORT_SIGNED_PDF` (or per-finding) and serves as the legal record. No digital signature / DSC / e-sign infrastructure needed at v1.0. | User direction 2026-05-13 |
| 62 | D-AUDRS-062 | R0.8 | **Audit module is ONLINE-ONLY at v1.0.** Departs from PSC's offline-first/PWA pattern. Auditor must have connectivity to log into VIMS, prepare audit docs, enter findings. Vessel Master uses live VIMS for NC/Obs closure work. Rationale: audits are office-initiated and primarily office-side data entry; investing in offline sync for audit tables adds complexity without commensurate value at v1.0. New audit tables still include `client_id` + `sync_version` columns for schema consistency with PSC, but they remain unused at v1.0. Future v1.x could add offline support if vessel-side experience demands it. | User direction 2026-05-13 |
| 63 | D-AUDRS-063 | R0.8 | **Auditor reassignment + Conductor vs Lead Auditor of record.** Two distinct fields on `audit_detail`: (a) `conductor_user_id` — the person who physically conducted the audit / entered the data in VIMS; (b) `lead_auditor_user_id` — the Lead Auditor of record who issues the report (signs F 602) and closes findings (NC Parts E-G). Both can be the same person, or different (e.g. junior auditor conducts under senior's supervision). **Reassignment rules:** before audit commences (status ≤ CONFIRMED), SEQ Manager can change either field. Once audit commences (status ≥ IN_PROGRESS), `conductor_user_id` is locked — the conductor must complete; `lead_auditor_user_id` can still be edited by SEQ Manager (e.g. if assigned senior auditor is unavailable for closure). | User direction 2026-05-13 |
| 64 | D-AUDRS-064 | R0.8 | **Audit cancellation by DPA only.** Fields captured on `master_audit_plan`: `cancellation_reason` (text, mandatory ≥50 chars), `next_planned_date` (date, mandatory — when next audit will be attempted), `cancelled_by`, `cancelled_at`. Status → `CANCELLED`. Cancellation triggers `AUDIT_CANCELLED` notification to Master + HoDs + auditor pool. The cancelled audit_plan entry remains visible (read-only) for audit-trail; system auto-creates a new PLANNED entry at `next_planned_date - 90 days` to start the alert cycle again. | User direction 2026-05-13 |
| 65 | D-AUDRS-065 | R0.8 | **Fleet-wide NC → Circular cross-module link.** Two-step: (1) at NC creation, auditor can flag `is_fleetwide_relevance=true` on `audit_finding`; (2) from NC closure record, Master or DPA can click "Issue Circular" — this opens a pre-filled new entry in the existing Circular module (`/circular/*`) with the NC's reference number, description, root cause summary, and corrective-action narrative pre-populated. Cross-module link stored in `audit_finding.linked_circular_id` (FK to `msc_data.id` in Circular module). Both the audit NC record and the Circular entry surface the cross-reference. No automatic fleet-cascade; the issuance of a Circular is a manual decision per audit. | User direction 2026-05-13 |
| 66 | D-AUDRS-066 | R1.A | **No `finding_type` discriminator column on `psc_deficiency`.** PSC and Audit tracking are kept fully separate at the UX layer; the CAR engine is the only shared infrastructure. Filter audit vs PSC findings at query time via `psc_inspection.inspection_type` (already present). Audit-specific type metadata stays on `audit_finding` (`finding_type` enum `NC` / `OBSERVATION` lives there). Dashboards, list pages, and analytics for Audit are built as separate surfaces, not as PSC-list filters. Rationale (user direction): "tracking of PSC is separate and Audit is separate — these are two different types of inspection, they may share some elements but they are totally different." | User direction 2026-05-14 |
| 67 | D-AUDRS-067 | R1.A | **Audit-finding signatures in a separate `audit_finding_signature` table** (not columns on `audit_finding`). One row per signature event (issuance, Master ack, Supt sign, Lead Auditor close, DPA close); columns `signer_user_id`, `signed_at`, `signed_pdf_attachment_id`, `signature_event_type`. Supports rework re-signs and a complete signature audit trail. Co-exists with §5.2's existing `audit_finding_signature` definition; R1.B will reconcile field list with KSM-F-NC-001 + KSM-F-OBS-001 signature parts. | User direction 2026-05-14 + §16.1 |
| 68 | D-AUDRS-068 | R1.A | **Polymorphic rule-reference pointer on `audit_finding`.** Single column pair `(rule_book_type, rule_clause_id)` on `audit_finding` instead of one FK column per rule book. `rule_book_type` enum: `ISM` / `ISPS` / `MLC` / `SOLAS` / `STCW` / `MARPOL` / `COLREG` / `KSM_SMS` / `FLAG` / `OTHER`. App layer validates `rule_clause_id` against the master named by `rule_book_type`. Adding a new rule book = new enum value, no schema change. Multi-rule findings (one issue breaching multiple standards) deferred — if needed in v1.1, add bridge table `audit_finding_rule_ref` then. | User direction 2026-05-14 |
| 69 | D-AUDRS-069 | R1.A | **`master_charterer` deferred to v1.2 with RightShip.** Charterer is only used for RS registration; Internal Audit (v1.0) does not need it. No master built at v1.0. When RS lands in v1.2, build the master then with real seed data from past RS reports. Rationale (user direction): "At present we want to concentrate on Audit, then move to RightShip." Reinforces D-AUDRS-054 phasing. | User direction 2026-05-14 |
| 70 | D-AUDRS-070 | R1.A | **Hard namespace separation between PSC and Audit.** Only two surfaces are shared: (1) the registration entry point — `/inspections/new` form + `psc_inspection` root row, and (2) the CAR Engine state machine — `psc_corrective_action` + `psc_deficiency`. Everything else gets a clean `audit_*` namespace and does NOT live under the `psc_*` prefix. **Table renames applied:** `psc_audit_detail` → `audit_detail` · `psc_audit_standards` → `audit_standards` · `psc_audit_team_member` → `audit_team_member` · `psc_audit_meeting_attendee` → `audit_meeting_attendee` · `psc_audit_area_summary` → `audit_area_summary` · `psc_audit_finding` → `audit_finding` · `psc_audit_finding_nc` → `audit_finding_nc` · `psc_audit_finding_obs` → `audit_finding_obs` · `psc_audit_finding_signature` → `audit_finding_signature` · `psc_audit_attachment` → `audit_attachment` · `psc_audit_signature` (R1 proposed) → `audit_signature` · `psc_audit_schedule_block` (R1 proposed) → `audit_schedule_block` · `psc_rs_detail` → `rs_detail` · `psc_rs_observation` → `rs_observation`. **Master naming:** Audit-domain masters use `master_audit_*` prefix (`master_audit_classification`, `master_audit_subtype`, `master_audit_finding_category`, `master_audit_area`, `master_audit_checklist`, `master_audit_checklist_item`, `master_audit_plan`, `master_audit_qualified_auditor`). Generic compliance rule-book masters stay at top-level `master_*` (`master_ism_clause`, `master_isps_clause`, `master_mlc_title`, `master_solas_chapter`, `master_stcw_section`, `master_marpol_annex`, `master_colreg_rule`, `master_ksm_sms_chapter`) — they're cross-module reference data that Training / Certs / Safety may cite later. RS-domain masters (`master_risq_chapter`, `master_risq_question`, `master_charterer`) deferred to v1.2. **Preserved unchanged:** `psc_inspection` · `psc_deficiency` · `psc_corrective_action` · `psc_audit_log` (the existing system-wide event log, NOT audit-domain). | User direction 2026-05-14 |
| 71 | D-AUDRS-071 | R1.B | **Audit SUBMIT gates** (status IN_PROGRESS → SUBMITTED): all four mandatory. (a) `opening_meeting_at` set AND ≥1 `audit_meeting_attendee` row with `opening_present=true`. (b) `closing_meeting_at` set AND ≥1 `audit_meeting_attendee` row with `closing_present=true`. (c) `audit_area_summary` has all 14 rows populated (one per area code) with non-null `status`. (d) `audit_detail.audit_summary` ≥ 100 chars AND `audit_detail.equipment_tested` non-empty (≥1 line). All four hard-block submit; user gets inline field-level errors. Matches SSQE §10.5.2 + §10.5.7 + SQE F 602 mandatory blocks. | User direction 2026-05-14 + SSQE §10 |
| 72 | D-AUDRS-072 | R1.B | **Signature absence hard-blocks per-state CAR transition on audit findings.** State machine gates: (i) Master cannot move CAR from IN_PROGRESS → PENDING_CE_REVIEW until KSM-F-NC-001 Part B/C signature attached (Master immediate + RCA sign). (ii) Supt cannot move CAR from PIC_REVIEW → SUBMITTED_TO_LEAD_AUDITOR until Supt sign on Part C/D attached. (iii) Lead Auditor cannot move CAR to LEAD_AUDITOR_CLOSED until Part F (Closure Acceptance) signature attached. (iv) Lead Auditor cannot move audit_detail.status from SUBMITTED → DPA_CLOSED until signed F 602 PDF attached. Each gate fails with a clear "Signature missing for {phase}" message. Implements physical-sig-only workflow per D-AUDRS-061. | User direction 2026-05-14 + D-AUDRS-061 |
| 73 | D-AUDRS-073 | R1.B | **Overdue NC closure deadlines are SOFT** (banner + escalation, no blocking). After T+0 (original_due_date or extended_due_date passed without closure): red dashboard banner on Master + Lead Auditor home; escalation notification to DPA + SEQ Manager; finding flagged `is_overdue=true`. Evidence upload and state transitions continue working — keeps closure flowing rather than stalling at the deadline. Tracks aligned with D-AUDRS-050 progressive alert pattern. Hard-block deferred unless future operational experience demands it. | User direction 2026-05-14 + D-AUDRS-050 |
| 74 | D-AUDRS-074 | R1.B | **Free-text minimum lengths mirror PSC conventions.** `rework_reason` ≥ 20 chars (matching CAR engine PSC rule). `root_cause_summary` ≥ 50 chars (matching PSC RCA min). `extension_reason` (on audit_finding) ≥ 50 chars. `cancellation_reason` (on master_audit_plan per D-AUDRS-064) ≥ 50 chars (already locked). `effectiveness_further_action_text` ≥ 50 chars when `effectiveness_outcome != EFFECTIVE`. `acceptance_return_reason` ≥ 20 chars when `acceptance_decision=RETURNED`. Maximums match column widths (typically `nvarchar(max)`). | User direction 2026-05-14 |
| 75 | D-AUDRS-075 | R1.B | **Date-order constraints — all enforced (hard block on save).** Rules: (a) `opening_meeting_at ≤ closing_meeting_at` · (b) `closing_meeting_at ≤ today()` (cannot close in future) · (c) `original_due_date ≥ inspection_date` (finding due cannot precede the audit it came from) · (d) `extended_due_date > original_due_date` (extension must extend) · (e) `next_planned_date > today()` (cancellation re-plan must be future) · (f) `master_audit_qualified_auditor.expiry_date > qualification_date` (auditor expiry after qualification) · (g) `effectiveness_review_date ∈ [LEAD_AUDITOR_CLOSED + 30 days, LEAD_AUDITOR_CLOSED + 90 days]` (KSM-F-NC-001 Part E window). All violations produce inline field errors; cannot save until fixed. | User direction 2026-05-14 |
| 76 | D-AUDRS-076 | R1.B | **File upload constraints on `audit_attachment`.** Accepted mime types: `application/pdf` · `image/jpeg` · `image/png` · `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (.docx). Max per-file size: **10 MB**. Reject other types with inline error. Show file-size and remaining-quota indicator. Same constraints apply to NC closure scans, F 602 signed PDFs, pre-audit references, OPM F 713 extension docs, Flag notification letters. Tracks D-AUDRS-060 attachment category enum. | User direction 2026-05-14 |
| 77 | D-AUDRS-077 | R1.B | **`audit_finding.clause_ref_text` validation when `rule_book_type=OTHER`.** Free-text field with `min=5 chars`, `max=200 chars`, no regex. No format constraint — auditor can write "BHP Vetting Standard 4.7" or "Owner Standing Order #12" or any non-master clause reference. Length floor prevents single-char typos; ceiling matches `nvarchar(200)` column width. When `rule_book_type ≠ OTHER`, the field is denormalized from the chosen master row's clause text (not user-editable). | User direction 2026-05-14 |
| 78 | D-AUDRS-078 | R1.B | **Lock `audit_classification` + `audit_standards` after first finding.** Once `audit_finding` table has at least one row referencing this `audit_detail`, both `audit_classification` and `audit_standards` are read-only in the audit edit form. To change them, Lead Auditor must first delete all findings (which is permitted only at `IN_PROGRESS` state per D-AUDRS-079). Prevents clause-ref orphaning when standards are dropped. Form shows a banner: "Standards/Classification locked — findings exist; remove findings to edit." | User direction 2026-05-14 |
| 79 | D-AUDRS-079 | R1.4 | **Audit soft-delete is blocked if any finding has a CAR past `ALLOTTED`.** Soft-delete (`is_deleted=1`) on `psc_inspection` for an audit row only allowed when: (a) no findings exist, OR (b) all findings have CAR state = `ALLOTTED` (no work started). If any CAR has moved to `IN_PROGRESS` or beyond, deletion is rejected with "Audit has in-flight corrective actions; use Cancel (D-AUDRS-064) instead." Forces the auditor to use the proper `CANCELLED` status workflow which preserves audit trail + auto-creates the next planned cycle. Findings under DRAFT audits remain orphan-safe via FK cascade rules. | User direction 2026-05-14 |
| 80 | D-AUDRS-080 | R1.4 | **No finding additions after audit SUBMITTED.** Once `audit_detail.status` moves IN_PROGRESS → SUBMITTED, the findings list is frozen — UI hides the "Add Finding" button; backend rejects new `audit_finding` inserts on submitted audits with HTTP 409 "Audit submitted; findings locked." Any subsequent issue must be raised as a separate audit (unscheduled trigger). Matches SSQE §10.6.1 "auditor submits F 602 within 2 weeks" finality. Late additions allowed via UNSCHEDULED_QUALITY_REVIEW or UNSCHEDULED_INCIDENT triggered new audit per D-AUDRS-024. | User direction 2026-05-14 |
| 81 | D-AUDRS-081 | R1.4 | **Office edit-assist on AUDIT inspections = same field-set + audit-log behaviour as PSC.** Office users (Supt / SEQ Manager) can edit the same Master-entered fields on AUDIT records as on PSC records (e.g. port name correction, vessel detail fix, attendee rank typo). Every edit hits `psc_activity_history` with the existing edit-trail signature. No Lead-Auditor approval gate — consistent with PSC ergonomics. The AUDIT record's certificate-critical fields (`audit_classification`, `audit_standards`, `lead_auditor_user_id`, `conductor_user_id` after IN_PROGRESS per D-AUDRS-063, finding text) follow their existing edit-lock rules. | User direction 2026-05-14 |
| 82 | D-AUDRS-082 | R1.4 | **KSM-F-NC-001 Part E (Effectiveness Review) trigger workflow.** When an audit-NC reaches `LEAD_AUDITOR_CLOSED`, system: (i) schedules an `effectiveness_review` task on the Lead Auditor's dashboard with `due_at = LEAD_AUDITOR_CLOSED + 30 days` and `expiry_at = LEAD_AUDITOR_CLOSED + 90 days`; (ii) at T+30 days, sends `NC_EFFECTIVENESS_REVIEW_DUE` notification to Lead Auditor; (iii) Lead Auditor can complete Part E any time in the 30–90 day window via the audit finding screen; (iv) at T+90 days if not completed, status flag `effectiveness_overdue=true`, escalation notification to DPA + SEQ Manager, dashboard banner promoted to critical. Predictable cadence — eliminates manual tracking. Adds new task type to existing notification system. | User direction 2026-05-14 + KSM-F-NC-001 Part E |
| 83 | D-AUDRS-083 | R1.C | **New `AUDIT_P_*` process-gate family** (does not extend PSC_P_*). v1.0 audit gates: `AUDIT_P_001` (create audit / audit_plan), `AUDIT_P_002` (edit audit pre-IN_PROGRESS), `AUDIT_P_003` (conduct audit — enter findings while IN_PROGRESS), `AUDIT_P_004` (close NC as Lead Auditor — Parts E/F/G), `AUDIT_P_005` (DPA-approve OPM F 713 extension), `AUDIT_P_006` (cancel audit), `AUDIT_P_007` (issue Circular from NC per D-AUDRS-065), `AUDIT_P_008` (sign closing meeting acknowledgment as Master/HoD), `AUDIT_P_009` (qualified-auditor master CRUD — SEQ Manager only). Default role-mapping: SEQ Manager = AUDIT_P_001/005/006/009; Lead Auditor = AUDIT_P_002/003/004; Master = AUDIT_P_008; DPA = AUDIT_P_005/006/007. Reuses existing CAR engine gates (PSC_P_004 etc.) for the corrective-action workflow. Matches D-AUDRS-070 namespace separation. | User direction 2026-05-14 |
| 84 | D-AUDRS-084 | R1.C | **Sidebar split into top-level modules.** Today's single "Inspections" parent splits into three top-level sidebar items: **PSC** (existing list filtered to inspection_type=PSC) · **Audit** (new list filtered to inspection_type=AUDIT; with sub-tabs Vessel Internal / Office Internal at v1.0) · **RightShip** (slot reserved, disabled at v1.0, enabled v1.2). Each top-level has its own dashboard, list view, and create-flow. Aligns with user directive that PSC and Audit are "totally different types of inspection." Existing /inspections/* routes remain backwards-compatible (redirect to type-specific surfaces). | User direction 2026-05-14 + D-AUDRS-066/070 |
| 85 | D-AUDRS-085 | R1.C | **Per-audit PIC pool = any user with `OFFICE_SUPT` role** (Marine or Tech variant). No additional qualification gate beyond the existing OFFICE_SUPT role. Per D-AUDRS-056, audit PIC = Supt (same as PSC PIC). SEQ Manager picks PIC from a dropdown of OFFICE_SUPT users at audit_plan creation. D-AUDRS-058 constraint (PIC ≠ Lead Auditor) enforced at app layer. PIC's vessel-scope follows master_RoleByVessel (per D-AUDRS-086) — they must be scoped to the target vessel. | User direction 2026-05-14 + D-AUDRS-056 |
| 86 | D-AUDRS-086 | R1.C | **`master_RoleByVessel` applies to audit records same as PSC.** Office user (Supt, SEQ Manager) sees only audits for vessels in their RoleByVessel scope. SEQ Manager typically has all-vessels scope; vessel-specific Supts see only their assigned vessels. Lead Auditor / Conductor assignment further narrows visibility within scope (an audit assigned to Lead Auditor X is visible to other in-scope Supts but only X can sign/close). Single scope source for the office UX; consistent with PSC. | User direction 2026-05-14 |
| 87 | D-AUDRS-087 | R1.D | **[ACTIVATED 2026-05-18 PM by D-AUDRS-205 in v1.1 R-EXT.0]** Originally: `audit_detail.certificate_impact` field DEFERRED to v1.1. Status as of v1.1 interrogation: **ACTIVATED** for external audits with full enum (NONE/CERT_VALID/RENEWAL_AT_RISK/SUSPENDED/WITHDRAWN). Mandatory at close-out for `audit_classification=EXTERNAL`; cross-module writeback to Certs module per D-202/D-205. Internal audits cannot trigger any of these states. **Original deferral rationale preserved:** D-AUDRS-087 | Internal Audit (v1.0 scope) has no authority to suspend or withdraw certificates — only Class society / Flag State (External Audit, v1.1) do. At v1.0, only per-finding `audit_finding.certificates_at_risk` flag (csv per D-AUDRS-046) is captured — this signals "auditor flagged this NC as a threat that should be reported to Class/Flag for their action," not an actual suspension. When External Audit ships in v1.1, `audit_detail.certificate_impact` is added with proper enum (`NONE` / `CERT_VALID` / `RENEWAL_AT_RISK` / `SUSPENDED` / `WITHDRAWN`) reflecting Class/Flag authority. **Schema impact:** remove `certificate_impact` column from §5.1 `audit_detail` definition at v1.0 build. | User direction 2026-05-14 |
| 88 | D-AUDRS-088 | R1.D | **`master_ism_clause` seeded at 3-level depth (X.Y.Z), ~80 rows.** Matches standard auditor citation depth (e.g. ISM 1.4.4 "Functional requirements for SMS"). Includes section headers (1, 2, ..., 16) and clause-level (1.1, 1.2, ..., 1.4.4). Generated from IMO ISM Code 2018 public text at DocSuite Step 2 (per D-AUDRS-098). Each row: `clause_no`, `clause_text`, `section_no`, `code_version` (set to "ISM 2018"). | User direction 2026-05-14 |
| 89 | D-AUDRS-089 | R1.D | **`master_isps_clause` seeded with Part A only (mandatory), ~25 rows.** Part B (recommendations) excluded because NCs can only be raised against mandatory provisions. If an Observation needs to cite a Part B recommendation, auditor uses `rule_book_type=OTHER` + free-text `clause_ref_text` (per D-AUDRS-077). Generated from ISPS Code Part A public text at DocSuite Step 2. Each row: `section_no`, `section_title`, `section_text`, `code_version` (set to "ISPS 2003"). | User direction 2026-05-14 |
| 90 | D-AUDRS-090 | R1.D | **`master_mlc_title` seeded with Regulation + Standard-A combined rows, ~30 rows.** Format: `Title 4 / Regulation 4.3 / Standard A4.3 — Health and safety protection and accident prevention`. Matches the way auditors actually cite ("MLC A4.3"). Code B (guidelines) excluded — same reasoning as ISPS Part B. Generated from MLC 2006 public text at DocSuite Step 2. Each row: `title_no`, `regulation_no`, `standard_a_code`, `title_text`, `code_version` (set to "MLC 2006 with 2014/2016/2018/2022 amendments"). | User direction 2026-05-14 |
| 91 | D-AUDRS-091 | R1.D | **`master_ksm_sms_chapter` seeded MANUALLY at v1.0 from SQE S 626 chapter list.** 13 entries: Apex Manual / OPM / SSQE / HRM / EMS / SPM Vol I-Nav / SPM Vol II-Eng / SOPEP-SMPEP / Ship Security Plan / Cyber Security / BCGOM / SEEMP II / SEEMP III. User direction: "We want to incorporate our manuals in the system in future at the moment it can be key in." When KSM manuals module ships (post-v1.0), `master_ksm_sms_chapter` can be wired to that source via FK — but v1.0 ships with a standalone hard-coded list. Each row: `chapter_code`, `chapter_name`, `revision_ref` (optional), `code_version`. | User direction 2026-05-14 |
| 92 | D-AUDRS-092 | R1.D | **Generic compliance masters (SOLAS, STCW, MARPOL, COLREG) seeded at Regulation/Rule level.** SOLAS = ~150 regulations across 14 chapters (e.g. "SOLAS V/Reg 19 — Carriage requirements for shipborne navigational systems"). STCW = ~40 sections (I/9, II/1, III/1, ...). MARPOL = ~80 regulations across 6 Annexes. COLREG = 38 Rules. Each row in the respective `master_*` table: clause/rule identifier, title, parent chapter/annex reference, `code_version` per D-AUDRS-093. Matches auditor citation practice. | User direction 2026-05-14 |
| 93 | D-AUDRS-093 | R1.D | **Rule-book versioning via `code_version` column on each master row.** When a new revision drops (e.g. ISM 2026 amendments, RISQ 3.1), insert new rows alongside the old, tagged with the new `code_version`. UI shows current version by default; auditor can opt-in to cite a prior version when finding refers to a historical event. Audit-trail-safe: every existing finding's `rule_clause_id` remains valid forever because the row isn't deleted. `code_version` enum maintained per rule book (e.g. "ISM 2018" / "ISM 2026"). Same pattern for ISPS, MLC, SOLAS, STCW, MARPOL, COLREG, RISQ. | User direction 2026-05-14 |
| 94 | D-AUDRS-094 | R1.D | **`master_audit_qualified_auditor` = separate table FK to users.** Schema: `id` PK, `user_id` FK users, `qualification_text` (e.g. "IRCA Lead Auditor"), `qualification_date`, `expiry_date`, `scope_standards_csv` (e.g. "ISM,ISPS,MLC"), `qualifying_body` (e.g. "DNV Maritime Academy"), `certificate_attachment_id` FK audit_attachment, `is_active`. Multi-row per user supported — a user can hold multiple auditor qualifications (e.g. ISM + ISPS expiring on different dates). UI: SEQ Manager manages this table; lead-auditor dropdowns at audit_plan creation filter to active + non-expired qualifications matching the audit's `audit_standards`. | User direction 2026-05-14 |
| 95 | D-AUDRS-095 | R1.E | **PDF page orientation matches source KSM forms.** F 601 audit plan = A4 portrait · F 602 audit report = A4 portrait · KSM-F-NC-001 = A4 portrait, 2 pages · KSM-F-OBS-001 = A4 portrait, 1 page · SQE S 626 monthly KPI = A4 LANDSCAPE (matches the wide spreadsheet matrix). Direct mirror of paper-form layouts so scanned signed-PDFs are visually identical to existing KSM workflow. Implemented in respective PDF generators (`audit_plan_pdf.py`, `audit_report_pdf.py`, `audit_nc_pdf.py`, `audit_obs_pdf.py`, `monthly_kpi_pdf.py`). | KSM source forms |
| 96 | D-AUDRS-096 | R1.E | **DRAFT watermark on PDFs until terminal state.** Audit PDFs (F 601, F 602): large diagonal grey 'DRAFT' watermark on every page while `audit_detail.status ∈ {PLANNED, CONFIRMED, IN_PROGRESS}`. Watermark removed once SUBMITTED or DPA_CLOSED. NC PDFs (KSM-F-NC-001): DRAFT until `audit_finding.car_status = LEAD_AUDITOR_CLOSED`. Obs PDFs (KSM-F-OBS-001): DRAFT until `MASTER_CLOSED`. Monthly KPI PDF: no DRAFT watermark (always represents a point-in-time snapshot). Prevents draft PDFs being printed and treated as final. | User direction 2026-05-14 |
| 97 | D-AUDRS-097 | R1.F | **Production-data migration = read-only legacy tagging.** Add `legacy BIT DEFAULT 0` column to `psc_inspection`. Pre-deploy script: `UPDATE psc_inspection SET legacy=1 WHERE inspection_type IN ('AUDIT','RS') AND created_date < @deploy_date`. Legacy rows: visible (read-only) in the new Audit/RS sidebar lists with a "Legacy — read only" banner; cannot be edited, cannot have new findings added, cannot transition state. New audits (created post-deploy) use the full `audit_detail` + `audit_finding` + child-table schema. Zero risk to historical data; clean cutover. No backfill of audit_detail rows from free-text legacy data — too risky to mis-categorise. | User direction 2026-05-14 |
| 98 | D-AUDRS-098 | R1.F | **Master-data seed CSV generation happens at DocSuite Step 2** (after Round 1 close). LLM parses the source spreadsheets (SQE F 604, F 605, F 606) and source codes (ISM, ISPS, MLC, SOLAS, STCW, MARPOL, COLREG) and produces CSV files in a `seeds/` folder under the eventual DocSuite directory. User reviews each CSV before commit. The CSVs are then loaded into the respective `master_*` tables by the v1.0 build's seed runner. Decisions in this SSOT pin the schemas (D-088..094); the actual row generation is execution work for Step 2, not interrogation work. | KLOSS Step 2 methodology |
| 100 | D-AUDRS-100 | R1.G | **[SUPERSEDED 2026-05-18 by D-AUDRS-107]** Original: PIC for OFFICE NCs is selected by DPA per audit, from any active office user. Unlike vessel audits (D-AUDRS-056 fixed PIC = OFFICE_SUPT role), office audits give DPA discretion to pick the PIC at `audit_plan` creation from the full pool of active office users (HoD of a peer department, a Supt, a SEQ team member, etc.). Field added to `audit_plan`: `office_pic_user_id` — populated at creation, mandatory before audit moves to CONFIRMED. **Constraints:** (i) D-AUDRS-058 still applies — PIC ≠ Lead Auditor of record; (ii) PIC must be marked active; (iii) DPA can change PIC pre-IN_PROGRESS, locked thereafter. UI: dropdown at audit_plan edit screen showing active office users with sort-by-department + recent-PIC-history hint. **Replaced by D-107 — no named PIC at plan; office audits use open-pool any-office-user-with-AUDIT_P_004 model per D-101 scope rule.** | User direction 2026-05-14 |
| 101 | D-AUDRS-101 | R1.G | **Office audits bypass `master_RoleByVessel` scope filter.** All office users with `AUDIT_P_001+` (read) gates see all office audits regardless of which vessels they're scoped to. Rationale: office audits are not tied to a vessel, so vessel-scope filtering is structurally inapplicable. **No new scope table** needed at v1.0 — keeps the master simple. Edit/sign rights remain narrowed by per-audit role assignment (Lead Auditor, conductor, PIC, audited HoD) per existing audit_plan + audit_detail rows. Future enhancement (post-v1.0) could add `master_RoleByDepartment` if confidentiality demands it. **Schema impact:** access-layer query for office audits uses only `auditee_type=OFFICE_DEPT` filter, no JOIN to master_RoleByVessel. Vessel audits continue to filter by master_RoleByVessel per D-086. | User direction 2026-05-14 |
| 102 | D-AUDRS-102 | R1.G | **`AUDIT_SCHEDULED` notification for OFFICE audits targets: HoD of audited department + named key staff + DPA + assigned auditor team.** Replaces the vessel-pattern "Master + HoDs" target (D-AUDRS-038) when `auditee_type=OFFICE_DEPT`. **Recipient resolution:** (a) HoD = lookup `users` table where `role = HOD_<auditee_office_dept>`; (b) key staff = drawn from the draft `audit_meeting_attendee` rows SEQ Manager populates at audit_plan creation; (c) DPA = always; (d) auditor team = Lead Auditor + conductor + co-auditors from `audit_team_member`. Same notification type code `AUDIT_SCHEDULED` reused; routing logic branches on auditee_type. Adds office-audit AUDIT_SCHEDULED to `psc_notification` insert trigger. | User direction 2026-05-14 |
| 103 | D-AUDRS-103 | R1.G | **`certificates_at_risk` field restricted to DOC and NONE when `auditee_type=OFFICE_DEPT`.** UI logic: on NC creation against an office audit, the cert-at-risk multi-select only renders DOC and NONE options (SMC, ISSC, MLC_DMLC hidden — they are vessel-specific certificates). Database schema unchanged — `certificates_at_risk` remains csv on `audit_finding` (D-AUDRS-046). Backend validation rejects SMC/ISSC/MLC_DMLC values for office NCs with HTTP 400 "Cert type not applicable to office audit." Prevents auditor mis-ticking a vessel certificate on an office NC. Vessel NCs continue to show all 5 options unchanged. | User direction 2026-05-14 |
| 104 | D-AUDRS-104 | R1.G | **§17.3 Office Internal Audit — End-to-End Workflow Reference added to SSOT.** Parallel to existing §17.2 (Vessel Internal Audit), produces a step-by-step table for the office-audit lifecycle. Key deltas from vessel workflow: (1) Planning step references office cadence (9–15 months) not 8–12; (2) trigger reason `TAKEOVER_3MONTH` not applicable (office has no vessel-takeover semantics — D-AUDRS-024); (3) Opening meeting attendees = HoD of audited dept + key staff, not Master + HoDs; (4) Checklist = F 606 (office) or F 604 (manning), not F 605 (vessel) — D-AUDRS-020; (5) "Master immediate action" on NC Part B → "HoD / Responsible Officer" (form template already accommodates per source); (6) PIC selection per D-AUDRS-100; (7) RBAC scope per D-AUDRS-101; (8) certificates_at_risk per D-AUDRS-103; (9) Closing meeting attendees = HoD + key staff; (10) Audit location = office HQ address, not vessel + port. All other steps (CAR engine, Lead Auditor closure path, Effectiveness Review, signature chain, audit_attachment uploads) are identical to vessel. §17.3 to be inserted in the SSOT in next edit pass. | User direction 2026-05-14 |
| 105 | D-AUDRS-105 | R1.H | **Single `master_audit_area` (14 rows), N/A allowed on office audits.** Keeps one master matching the SQE F 602 source form — one document covers both vessel and office contexts. On office audits, auditor sets `audit_area_summary.status = N_A` for the ~6 vessel-only areas (Navigation Procedures, Cargo, Mooring/Anchoring, MLC Implementation, plus vessel-specific portions of Safety Equipment & Procedures and Planned Maintenance System where the auditor judges them inapplicable). **Schema:** no new table; `audit_area_summary.status` enum extended to include `N_A` alongside existing remark/status values. **Validation:** SUBMIT gate (D-AUDRS-071) "14-area scorecard fully filled" treats a row as satisfied when status is any of {filled remark, N_A} — N/A counts as a valid completion, not a gap. **UI:** office audit form pre-suggests N/A on the 6 vessel-only rows (auditor can override either direction); vessel audit form keeps N/A available but does not pre-suggest. **Audit-trail:** N/A selections persist to the F 602 PDF as "N/A" in the relevant area row to make the rationale explicit. Rejected alternative: parallel `master_office_audit_area` — adds a second master to maintain, divergence risk if KSM revises F 602, and the source form has no precedent for separation. | User direction 2026-05-18 |
| 107 | D-AUDRS-107 | R1.I | **PSC-style open-pool PIC for Audit — supersedes D-AUDRS-056 + D-AUDRS-100.** Adopt PSC's pattern: no named PIC at audit_plan creation. The CAR engine's PIC review step (`PIC_REVIEW`) is pickable by **any office user with the right scope/gate**: (a) Vessel audits — any user in `master_RoleByVessel` for that vessel with `AUDIT_P_004` gate (mirrors PSC's master_RoleByVessel filter); (b) Office audits — any office user with `AUDIT_P_004` gate (no vessel-scope filter, per D-AUDRS-101). **Schema impact:** DROP column `audit_plan.office_pic_user_id` (added by superseded D-100); DROP column `audit_plan.assigned_pic_user_id` (originally added by superseded D-056); no replacement column on audit_plan. **Whoever clicks "Start PIC Review" first becomes the PIC of record for the audit** — captured at action time in `psc_activity_history` (existing audit trail). Rationale: matches PSC mental model (users already know it), removes a planning step and a dropdown, eliminates DPA discretion for office PIC. The "audit PIC = administratively accountable supt" framing was already thin because D-AUDRS-057 makes the **Lead Auditor** (not PIC) the NC closer. | User direction 2026-05-18 |
| 108 | D-AUDRS-108 | R1.I | **DPA selects Lead Auditor at audit_plan creation — modifies D-AUDRS-039.** Originally D-039 read "SEQ Manager creates audit_plan entry + assigns qualified auditor." Modified: **DPA** is the gate-holder for Lead Auditor selection (gate `AUDIT_P_001` narrowed to DPA-only for this sub-action). DPA picks from `master_audit_qualified_auditor` dropdown filtered to: (i) `is_active=1`; (ii) `expiry_date > today()`; (iii) `scope_standards_csv` intersects `audit.audit_standards`. Note: at KSM today DPA = SEQ Manager per D-AUDRS-034, so this is a semantic gate name (the same person continues to act). If KSM ever splits the roles, the gate naming reflects who should own the call. Same selection rule for vessel + office audits. UI dropdown shows auditor name + qualifying body + scope standards + expiry date (highlights amber if expiry within 60 days). | User direction 2026-05-18 |
| 109 | D-AUDRS-109 | R1.I | **F 601 / F 602 PIC field — runtime-resolved from first-actor user_id.** Since PIC is no longer named at plan time (per D-107), the PIC field on F 601 (Audit Plan) and F 602 (Internal Audit Report) PDFs is resolved at runtime: **the first office user who performs a PIC review action on any CAR for this audit becomes the audit's PIC of record** (first-actor-wins for accountability). Captured in new derived field `audit_detail.pic_user_id_resolved` — populated by trigger or app-layer on first `psc_activity_history` entry where `audit_id=this AND action='pic_review'`. Field is read-only after first set. **F 601 generated at plan time** shows PIC = `— (assigned at first review)` per D-096 DRAFT watermark rules. **F 601 reissued + F 602 generated** at audit DPA_CLOSED show resolved PIC name (lookup `users.full_name` by `pic_user_id_resolved`). Per-NC reviewer history remains accessible in `psc_activity_history` for KSM-F-NC-001 Part C/D printouts; the resolved field is for audit-level reporting only. | User direction 2026-05-18 |
| 111 | D-AUDRS-111 | R1.J | **Triple-channel notification dispatch for audit-related notifications — `IN_SYSTEM` + `EMAIL` + `SLACK`.** All audit-domain notification types (AUDIT_SCHEDULED · AUDIT_NC_RAISED · AUDIT_CANCELLED · AUDIT_OVERDUE · NC_EFFECTIVENESS_REVIEW_DUE · AUDIT_EXTENSION_APPROVED · AUDIT_CRITICAL_OVERDUE) fan out to three channels simultaneously. **Failure model:** in-system delivery is the source-of-truth — it's a DB insert into `psc_notification`, succeeds in the same transaction as the audit state change. Email and Slack are best-effort, async, with **3 retries + exponential backoff (1s, 2s, 4s)** matching the existing CAR retry policy. Email/Slack failure does **not** roll back the audit action; the in-system notification still posts. **Delivery log** (D-114) records every attempt for audit-trail compliance (KSM SSQE §10.4.1 requires evidence of notification). CAR-engine notifications (existing PSC types) unchanged at v1.0; revisit for v1.1. UI on audit detail page surfaces delivery status per channel: ✓ delivered · ◯ pending · ✗ failed-after-retries (with manual resend button for office users). | User direction 2026-05-18 PM |
| 112 | D-AUDRS-112 | R1.J | **⚠️ PARTIALLY SUPERSEDED by D-AUDRS-264 (2026-05-19).** EMAIL-SOURCE PORTION RESCINDED — vessel email is NOT stored on a new `VesselData.official_email` column; instead pulled from CMS via `CmsVesselClient.getOfficialEmail(vessel_id)`. ~~Schema impact (column add) is RESCINDED.~~ **STILL IN FORCE:** (a) the "single official mailbox per vessel" PRINCIPLE — one mailbox shared by Master + onboard officers per KSM practice; (b) office-side `users.email` mechanism for individual office recipients; (c) office-audit routing to HoD email (resolved via `master_hod_assignment` per D-106) + key staff + DPA + auditor team; (d) bounce-handling to KSM admin mailbox with status=`BOUNCED` (now via `notification_delivery_log` per D-114 + DPA queue per D-262). Original decision text below for audit trail: *"Vessel email = single official mailbox on `VesselData.official_email`. Audit notifications targeting vessel side (AUDIT_SCHEDULED, AUDIT_OVERDUE, AUDIT_NC_RAISED for vessel audits) email to the one official vessel address (e.g. `vessel@kaizen-horizon.com`). Master + onboard officers share access to that mailbox per existing KSM practice. Schema impact: if `VesselData.official_email` not present, add `nvarchar(254) NULL` column; backfill from existing crewing data where possible, else manual seed at DocSuite Step 2. Office side uses `users.email` (existing) — each office recipient gets their own email. Office audits route to: HoD's email (resolved via `master_hod_assignment` per D-106) + key staff `users.email` + DPA `users.email` + auditor team `users.email`. Bounce handling: bounce-back to a designated KSM admin mailbox; not retried (cannot recover from address invalid). Bounce logged in delivery log with status=`BOUNCED`."* | User direction 2026-05-18 PM (partially superseded by D-264 on 2026-05-19) |
| 113 | D-AUDRS-113 | R1.J | **Slack integration via incoming webhooks — new `master_slack_channel` table.** Schema: `id` PK · `channel_name` nvarchar(80) (e.g. `#ksm-audits`, `#ksm-vessel-kaizen-horizon`) · `webhook_url` nvarchar(500) (HTTPS encrypted at rest) · `scope_type` enum (CENTRAL, PER_VESSEL, PER_DEPT) · `scope_value` nvarchar(100) NULL (vessel_id or dept code) · `notification_types_csv` nvarchar(500) (which types fire to this channel) · `is_active` BIT · `created_by`, `created_at`. **Routing logic:** at notification dispatch, query active channels matching the notification type + scope; POST JSON payload (Slack Block Kit format with audit ID + title + summary + link back to VIMS) to each matching webhook. Message format: 1 Slack post per notification (no threading at v1.0). **CRUD:** new gate `AUDIT_P_011` (SEQ Manager only). **Recommended seed at deploy:** central `#ksm-audits` channel for office-wide notifications; per-vessel channels created as fleet adopts them. **Security:** webhook URL never displayed in UI after creation (masked as `https://hooks.slack.com/services/****`); rotation handled via re-create + soft-delete-old. | User direction 2026-05-18 PM |
| 114 | D-AUDRS-114 | R1.J | **New `notification_delivery_log` table — per-channel delivery audit trail.** Schema: `id` PK · `notification_id` FK psc_notification · `channel` enum (IN_SYSTEM, EMAIL, SLACK) · `recipient_address` nvarchar(254) (email or slack channel name) · `status` enum (PENDING, SENT, FAILED, BOUNCED, RETRYING) · `attempt_count` INT · `first_attempted_at`, `last_attempted_at` · `last_error` nvarchar(max) NULL · `sent_at` datetime NULL. **Indexed on:** notification_id + channel; status + last_attempted_at (for retry queue lookup). **Retention:** 7 years to match KSM SMS document retention (longer than typical app logs because audit notifications are official records per SSQE §10.4.1). Surfaced in audit detail UI as a "Notification log" panel restricted to DPA + SEQ Manager. Per-row download to PDF for evidence packs. | User direction 2026-05-18 PM |
| 115 | D-AUDRS-115 | R1.J | **Audit-related notification types covered at v1.0** (triple-channel fanout per D-111). Locked set: (a) `AUDIT_SCHEDULED` — when audit_plan moves to CONFIRMED · (b) `AUDIT_NC_RAISED` — when an `audit_finding` of type NC is inserted on a submitted audit · (c) `AUDIT_CANCELLED` — D-064 cancellation · (d) `AUDIT_OVERDUE` — D-050 alert cadence at T-0, T+30, T+60 · (e) `AUDIT_CRITICAL_OVERDUE` — at T+90 with cert-at-risk · (f) `AUDIT_EXTENSION_APPROVED` — OPM F 713 (D-051..053) · (g) `NC_EFFECTIVENESS_REVIEW_DUE` — D-082 T+30 reminder. Each type has a fixed recipient resolver (per D-038/D-102/D-106) and fixed Slack channel scope. Existing CAR-engine notifications (PSC pattern) remain in-system-only at v1.0 to limit blast radius; promotion to triple-channel is a v1.1 follow-up. | User direction 2026-05-18 PM |
| 116 | D-AUDRS-116 | R1.K | **Plain-language wizard UX for KSM-F-NC-001 Parts B + C (crew side).** Replaces the dense 7-part form layout with a **single-question-per-screen mobile-first wizard** for the parts crew must fill (Part B — Immediate Action; Part C — Root Cause Analysis). Prompts use plain English aimed at low-literacy users: "What did you do right away when you saw this problem?" not "Master immediate action description." "Why did this happen — what's the underlying cause?" not "Root cause analysis ≥50 chars." **Each screen shows:** one prompt · one input field · inline example ("e.g. *We rescheduled the missed PMS tasks and ran them within 48 hours.*") · helpful hint ("Tip: focus on what you did, not what should happen next") · Save & Continue button. **Saves draft on every screen advance**; crew can resume from last screen. Submit gate identical to current (D-074 RCA ≥50 chars still applies; wizard's last screen shows char count + green check when met). **Backend storage unchanged** — same `audit_finding_nc.master_action_text` + `root_cause_summary` fields. Office side keeps the dense-form view (faster for trained users). Mobile-first per CLAUDE.md mandate. | User direction 2026-05-18 PM |
| 117 | D-AUDRS-117 | R1.K | **New `master_rca_template` table — pre-seeded RCA library to reduce blank-page paralysis.** Schema: `id` PK · `category` enum (PMS_OVERDUE, TRAINING_GAP, CERT_EXPIRED, DOC_CONTROL, EQUIPMENT_FAILURE, PROCEDURE_NOT_FOLLOWED, COMMUNICATION_BREAKDOWN, RESOURCE_CONSTRAINT, EXTERNAL_FACTOR, OTHER) · `title` nvarchar(200) (e.g. "PMS overdue — scheduling oversight") · `template_text` nvarchar(max) (~300-char drafted RCA narrative crew can edit to fit) · `example_evidence_hint` nvarchar(500) ("Attach screenshot of PMS due-task list showing overdue items") · `applicable_def_categories` nvarchar(200) CSV (links to existing PSC def categories where relevant) · `is_active` BIT · `code_version` (versioning per D-093). **Seeded ~25 templates** at DocSuite Step 2 covering the common scenarios (PMS late, training matrix gap, cert renewal missed, doc not in latest rev, alarm test missed, drill record gap, fire-equipment overdue, MARPOL log entry missing, GMDSS test late, ECDIS chart update, BWMS log gap, etc.). **UX:** RCA wizard screen (per D-116) shows "Pick a starting point" carousel of templates filtered to the NC's category; crew taps closest match → wizard pre-fills RCA field with `template_text`; crew edits to fit specifics; D-074 ≥50 char rule applies after edit. **CRUD:** new gate `AUDIT_P_012` (SEQ Manager only). | User direction 2026-05-18 PM |
| 118 | D-AUDRS-118 | R1.K | **Office-led drafting flow for NC closure — extends D-AUDRS-081 edit-assist.** Supt or SEQ Officer can draft Part B + Part C content for a vessel's NC on the vessel's behalf via a new "Draft for Vessel" mode in the office UI. Workflow: (1) Supt opens NC at CAR state `ALLOTTED` or `IN_PROGRESS`; (2) clicks "Draft for Vessel"; (3) fills Part B + Part C using the same wizard or dense form (their choice); (4) on save, CAR state moves to new sub-state `OFFICE_DRAFTED` and a notification fires to Master/HoD ("Office has drafted a corrective action for your review"); (5) Master/HoD opens NC; sees draft content with edit affordances; (6) Master/HoD either edits or accepts-as-is; (7) Master/HoD signs Part B (physical sig still required per D-061 — wet-ink scan of generated PDF); (8) CAR state moves to `IN_PROGRESS` and follows normal flow. **Audit-trail:** `psc_activity_history` records both the office drafter (`drafted_by_user_id`) and the Master/HoD signer (`signed_by_user_id`); both names appear on KSM-F-NC-001 PDF Part B footer ("Drafted by office: X · Approved + signed by Master: Y"). **Compliant under KSM SMS** — Master signature = ownership of corrective action regardless of who drafted. Helps low-literacy crew without compromising accountability. | User direction 2026-05-18 PM |
| 207 | D-AUDRS-207 | R-EXT.1 | **Initial audit subtype variants — extends D-AUDRS-200 enum.** User direction 2026-05-18 PM: "what is missed is interim, initial audits." Per ISM Code Chapter 13, **Initial audits** are first-ever verification audits conducted before a Document of Compliance (DOC) or Safety Management Certificate (SMC) is issued — typically for new vessels, new companies taking over management, or new ship managers. New enum values added to `external_audit_subtypes_csv` (D-200): `DOC_INITIAL` (office side, new company / takeover · before initial DOC issued) · `SMC_INITIAL`, `MLC_INITIAL`, `ISPS_INITIAL` (vessel side, new vessel / takeover · before initial certs issued). **Behavioural deltas vs other subtypes:** (a) **No prior anniversary date exists** in Certs module at audit registration time; field is null. (b) **No alert ladder** (D-203) applies — Initial audits are managed manually by DPA based on commercial milestones (vessel delivery, fleet entry, etc.). VIMS does not fire T-90/T-0/T+90 alerts for Initial audits; instead surfaces in DPA dashboard as "Initial audit pending — register on completion." (c) **Cert row creation:** on successful audit close-out with `certificate_impact=CERT_VALID`, Audit module's writeback (per D-202) **CREATES a new vessel_cert row** in Certs module with audit_date as both `last_done` and `anniversary_date` (anniversary is set at this moment per D-CERT-074's "set once at onboarding" rule). issue_date and expiry_date derived from Class society's issued cert (5-year validity by default). (d) **Linked_cert_ids_csv at registration:** null until close-out; cert is created at close-out time, not pre-existing. **Schema impact:** no new columns; existing fields cope with null linked_cert_ids_csv pre-closure. **Validation:** `audit_classification=EXTERNAL` + subtype starts with `*_INITIAL` → linked_cert_ids_csv NOT required at registration (overrides default mandatory rule); becomes mandatory at close-out (auto-populated from cert created by writeback). | User direction 2026-05-18 PM session 5 |
| 208 | D-AUDRS-208 | R-EXT.1 | **Interim audit subtype variants — extends D-AUDRS-200 enum.** Per ISM Code, **Interim DOC** (max 12 months validity) and **Interim SMC** (max 6 months validity) are issued when (a) a new company takes over management with prior Class confirmation, or (b) a vessel is just delivered / changes management. The Interim audit MUST happen within the interim cert's validity window to convert the Interim cert to a full DOC/SMC. New enum values: `DOC_INTERIM` (office, within 12-month Interim DOC validity) · `SMC_INTERIM`, `MLC_INTERIM`, `ISPS_INTERIM` (vessel, within 6-month Interim cert validity). **Behavioural deltas vs Annual/Intermediate/Renewal:** (a) **Alert ladder anchored on Interim cert expiry, not anniversary.** Reads `vessel_cert.expiry_date` for the interim cert from Certs module (per D-202 read path); fires alerts: **T-90 / T-60** (DPA + Master banner "interim audit due in 90/60 days — schedule with Class"); **T-30** (critical banner — risk of operating without certificate); **T-0 (expiry)** — Interim cert expires automatically per Class rules, vessel cannot trade until full cert issued. (b) **Cert conversion on success:** close-out with `certificate_impact=CERT_VALID` triggers Certs module writeback that **converts the existing Interim cert row to a full cert** — same `vessel_cert.id` retained; `issue_date` updated to audit_date or Class-specified date; `expiry_date` extended to 5 years from interim issue or from audit completion (Class society decides; captured in close-out letter); `anniversary_date` SET (per D-CERT-074 single-set rule) to audit_date if not already set. (c) **linked_cert_ids_csv at registration:** references the existing Interim cert row (pre-existing in Certs module). (d) **Failure path:** if Interim audit window closes (cert expires) without successful audit → Interim cert auto-marked expired in Certs module; vessel operationally constrained until either (i) full audit conducted retrospectively + DPA-Class negotiation, or (ii) new Interim cert re-issued (rare). | User direction 2026-05-18 PM session 5 |
| 209 | D-AUDRS-209 | R-EXT.1 | **Anniversary lifecycle for external audits — codifies the handoff between Audit ↔ Certs modules.** Per ISM Code, the anniversary date drives all audit cadence math. This decision documents which audit subtypes CREATE, UPDATE, or LEAVE_UNCHANGED the anniversary date in Certs module (`vessel_cert.anniversary_date` per D-CERT-074). **CREATE** (anniversary set for first time): `DOC_INITIAL` · `SMC_INITIAL` · `MLC_INITIAL` · `ISPS_INITIAL` — anniversary becomes audit_date on close-out. **UPDATE** (anniversary refreshed): none. Per D-CERT-074 anniversary is permanent once set — no audit refreshes it (re-anchoring via DPA manual edit only per D-CERT-074 audit-trail). **LEAVE_UNCHANGED** (read-only by Audit module): `DOC_INTERIM` · `SMC_INTERIM` · `MLC_INTERIM` · `ISPS_INTERIM` · `DOC_ANNUAL` · `DOC_RENEWAL` · `SMC_INTERMEDIATE` · `SMC_RENEWAL` · `MLC_INTERMEDIATE` · `MLC_RENEWAL` · `ISPS_INTERMEDIATE` · `ISPS_RENEWAL` — these audits operate against the existing anniversary; they update `last_done` and `next_due` (per D-202) but never the anniversary itself. **Audit-trail rule:** any anniversary CREATE event by Audit module's writeback (Initial audits) logs to `vims_certs_audit_log` per D-CERT-091 with actor=AUDIT_MODULE_SYSTEM + reference to audit_detail.id. **Edge case:** if Initial audit registered but linked_cert row already exists (rare — manual entry by DPA before audit), Initial audit's writeback fails gracefully with HTTP 409 "Cert already exists for vessel/dept × cert_type"; DPA must reconcile (delete the manual row, re-run writeback, OR re-classify audit as Annual/Renewal). | User direction 2026-05-18 PM session 5 |
| 200 | D-AUDRS-200 | R-EXT.0 | **External Audit foundation — `audit_classification=EXTERNAL` + post-facto registration (v1.1 scope).** New value `EXTERNAL` on `audit_detail.audit_classification` enum (alongside existing `INTERNAL` from D-016). New field `external_audit_subtypes_csv` nvarchar(200) — multi-value from enum `DOC_ANNUAL` · `DOC_RENEWAL` · `SMC_INTERMEDIATE` · `SMC_RENEWAL` · `MLC_INTERMEDIATE` · `MLC_RENEWAL` · `ISPS_INTERMEDIATE` · `ISPS_RENEWAL`. **Registration is post-facto** — external audits skip the PLANNED → CONFIRMED → IN_PROGRESS lifecycle entirely; created with status=SUBMITTED on registration, since the audit has already happened externally and Class/Flag schedules it (not VIMS). audit_plan table not used for external; goes straight into audit_detail. **Authority to register:** Master can register vessel-side (SMC/MLC/ISPS) per existing PSC pattern; DPA + Marine Sup'tt register DOC (office-side). Trigger reason from D-024 enum set to `SCHEDULED` by default (external audits are always pre-scheduled by Class society on the anniversary cycle); FLAG_REQUEST / DETENTION_FOLLOWUP etc. (from D-122) apply only to additional internal audits per D-121. **ISM regulatory framework codified:** DOC = office-side, annual + 5-yr renewal · SMC/MLC/ISPS = vessel-side, intermediate (between 2nd & 3rd anniversary) + 5-yr renewal · all share the ±3-month window per ISM Code (window math read from Certs module). | User direction 2026-05-18 PM session 4 |
| 201 | D-AUDRS-201 | R-EXT.0 | **External auditor identity fields — reuse Certs module class_society + free-text lead auditor (v1.1).** Schema on audit_detail (set only when `audit_classification=EXTERNAL`): (a) `external_audit_org` — reuses `vessel.class_society` enum from Certs module (NK / KR / BV / LRQA / ABS / DNV / RINA / ClassNK / etc.) — same auditing organizations that issue the certs being audited. For DOC audits, the org may differ from the vessel's class society if Flag has assigned a different RO for the company audit; field is still drawn from the same class_society enum. (b) `external_lead_auditor_name` nvarchar(200) — free text. (c) `external_lead_auditor_credential` nvarchar(200) — free text (e.g. "Lead Auditor IMO ISM/ISPS/MLC Auditor Certificate"). (d) `external_audit_report_pdf` — mandatory attachment of the external auditor's official audit report, uploaded by the registering user (Master/DPA/Marine Sup'tt) on registration. Attachment category in audit_attachment table = `EXTERNAL_AUDIT_REPORT`. **No structured fields beyond these** — the auditor's report PDF is the source of truth; VIMS captures findings (NCs/Obs) into structured rows but doesn't re-parse the report. **Validation:** all four fields mandatory at registration; backend rejects with HTTP 400 if any missing. | User direction 2026-05-18 PM session 4 |
| 202 | D-AUDRS-202 | R-EXT.0 | **Cross-module link to Certs module + harmonized SMC+MLC+ISPS as one record (v1.1) — SUPERSEDES D-CERT-025 for external audits.** New field on audit_detail: `linked_cert_ids_csv` nvarchar(500) — comma-separated FKs to `vessel_cert.id` for each cert this audit covers. Audit module READS from Certs module: anniversary date · cadence · window_open · window_close · current cert validity (issue_date, expiry_date) — for the registration UI dropdown (which certs are due in this window) and for alerts (D-203). Audit module WRITES back to Certs module on audit close-out: `last_done` = audit_date · `next_due` recomputed (= anniversary + cadence per IMO rules); on successful RENEWAL audits with `certificate_impact=CERT_VALID` (D-205), Certs module's cert `issue_date` and `expiry_date` get refreshed atomically as part of the same close-out transaction. **Harmonized handling:** when SMC + MLC + ISPS run on the same physical audit visit, registered as ONE audit_detail row with `external_audit_subtypes_csv = 'SMC_RENEWAL,MLC_RENEWAL,ISPS_RENEWAL'` AND `linked_cert_ids_csv` listing all three vessel_cert.id values. Findings link to this one audit_detail; each NC has a new optional field `applies_to_cert_ids_csv` (subset of audit's linked_cert_ids_csv) tagging which cert(s) the finding pertains to. Close-out writes `last_done` to all 3 Certs rows in one DB transaction. **DOC audit stays separate** — office-side, distinct audit_detail row, linked to a single DOC cert. **Supersedes D-CERT-025 for v1.1 external audits only** — that decision said "no Inspection module cross-link in V1"; for v1.1 external audits, the cross-link is now mandatory. Internal Audit's existing relationship with Certs (none) is unchanged. | User direction 2026-05-18 PM session 4 |
| 203 | D-AUDRS-203 | R-EXT.0 | **Anniversary window alerts ladder for external audits (v1.1) — reads from Certs module window math.** Anniversary window alerts run per ISM Code ±3-month window (computed by Certs module per D-CERT-063 from anniversary + cadence + IMO rules — Audit module never recomputes). Progressive alerts mirror D-050 internal-audit pattern but with different cadence: (a) **T-90 days before window_open**: SEQ Manager / DPA dashboard banner "external audit due in 90 days for vessel/office X — schedule with Class society"; alert notification fires triple-channel per D-111. (b) **T-0 (window_open)**: vessel + office Master/DPA banner "audit window now open — register completed audit when done"; cert remains valid. (c) **window_close (anniversary + 3 months)**: critical-red banner "audit window closing"; alert escalates to Managing Director. (d) **window_close + 30 days**: cert flagged `at_risk` in Certs module (via Audit→Certs writeback), `audit_detail.certificate_impact=RENEWAL_AT_RISK` auto-set, DPA + Marine Sup'tt paged urgently; cert visible in Certs module but with red banner. (e) **window_close + 90 days**: cert auto-marked SUSPENDED in Certs module per D-205 impact rules; Flag State notification required (manual workflow outside VIMS at v1.1; possible automation in v1.2). **No alerts for internal additional audits or routine internal cadence** — those have their own D-050 ladder. Notification channels per D-111 (in-system + email + Slack). | User direction 2026-05-18 PM session 4 |
| 204 | D-AUDRS-204 | R-EXT.0 | **Findings entry + simplified closure path for external NCs/Observations (v1.1).** **NC/Obs entry:** vessel staff (Master) or office (Marine Sup'tt/DPA) enters NCs and Observations into Audit module based on the external auditor's written report (uploaded as attachment per D-201). External auditor does NOT enter into VIMS (matches Certs D-CERT-194/196/197 read-only-only pattern). New field on audit_finding: `is_external` BIT — set to 1 when audit_detail.audit_classification=EXTERNAL. Same KSM-F-NC-001 / KSM-F-OBS-001 forms used internally — wizard (D-116) + RCA template library (D-117) + office-led drafting (D-118) all work the same way; the form just has `is_external=1` semantics for the PDF banner. **Source of finding** on PDF Part A footer reads "External Auditor: <external_lead_auditor_name>, <external_audit_org>" instead of internal auditor reference. **Closure path (simplified):** Same CAR engine as internal (Master → Supt) but **NO internal Lead Auditor closure step** — D-057's "Lead Auditor closes NCs" applies only to internal audits. Instead, new terminal state `EXTERNAL_AUDITOR_CLOSED` reached when: (a) Supt's PIC review completes (existing CAR state); (b) external auditor's close-out letter PDF uploaded as evidence (new attachment category `EXTERNAL_CLOSE_OUT_LETTER`, mandatory); (c) DPA confirms closure in VIMS (new action button "Confirm External Closure" — gate AUDIT_P_013 from D-206). **No Effectiveness Review (D-082)** for external NCs — the external auditor doesn't return for T+30/+90 review; their close-out letter is the final word. State machine for external NCs: ALLOTTED → IN_PROGRESS → PENDING_CE_REVIEW (vessel only) → PIC_REVIEW → AWAITING_EXTERNAL_CLOSE_OUT → EXTERNAL_AUDITOR_CLOSED. | User direction 2026-05-18 PM session 4 |
| 205 | D-AUDRS-205 | R-EXT.0 | **Certificate impact field ACTIVATED for v1.1 — UN-DEFERS D-AUDRS-087.** D-087 was deferred to v1.1 specifically for external audits; now activated. `audit_detail.certificate_impact` enum (set only when `audit_classification=EXTERNAL`): `NONE` · `CERT_VALID` (renewal successful, cert validity refreshed) · `RENEWAL_AT_RISK` (open NCs threaten timely closure within 3-month window) · `SUSPENDED` (Class/Flag suspended cert pending closure) · `WITHDRAWN` (Class/Flag withdrew cert — vessel cannot trade). **Mandatory at audit close-out** for external audits; backend rejects close-out attempt if null. **Cross-module effect on Certs (per D-202 writeback):** (a) `CERT_VALID` → Certs module refreshes cert issue_date + expiry_date with new validity period from external_audit_report_pdf metadata or DPA-entered renewal date. (b) `RENEWAL_AT_RISK` → Certs module flags cert with `at_risk_flag=1`; vessel dashboard shows red banner; cert remains valid but operationally constrained. (c) `SUSPENDED` → Certs module marks cert `is_suspended=1` with suspension_date and suspension_reason FK to audit_detail.id; vessel cannot trade per Flag rules. (d) `WITHDRAWN` → Certs module marks cert `is_withdrawn=1` (terminal state); new cert must be issued by Class via separate workflow. Audit module never deletes Certs rows — all transitions are soft-state via flags + writeback. Internal audits cannot trigger any of these states (Internal Audit has no authority over Class-issued certs per existing D-087 rationale). | User direction 2026-05-18 PM session 4 + un-defers D-AUDRS-087 |
| 206 | D-AUDRS-206 | R-EXT.0 | **New RBAC gates for External Audit (v1.1) — extends D-083 family.** Two new gates: (a) `AUDIT_P_013` — Register external audit + confirm external NC closure. Role mapping default: Master (vessel-side audits SMC/MLC/ISPS) · DPA + Marine Sup'tt (office-side DOC + cross-link writeback) · vessel scope per `master_RoleByVessel` for office users (matches D-086 pattern). (b) `AUDIT_P_014` — Write back to Certs module (last_done, next_due, cert_validity refresh on RENEWAL audits). Role mapping default: system-only at close-out (transactional with `Confirm External Closure` action); DPA has manual override gate for emergency corrections. No vessel-side users get AUDIT_P_014 — write-back to Certs is office-controlled to prevent vessel staff from inadvertently extending cert validity. **External auditor's existing Certs read-only access** (D-CERT-194/196) unchanged — they read Certs to verify VIMS-entered data matches their report; they cannot enter or close findings in Audit module. AUDIT_P_001..012 from v1.0 unchanged. Total process gates now: 14 (`AUDIT_P_001..014`). | User direction 2026-05-18 PM session 4 |
| 121 | D-AUDRS-121 | R1.M | **Additional Internal Audit — `is_additional` flag, window-calc exclusion, DPA-only authority.** User direction 2026-05-18 PM: "there are times when additional internal audit is required, may be flag or PSC asks for it or may be due to detention, so should have an option to activate additional internal audit for vessel with a reason to do so, but this shall not affect the audit window of the vessel and should be treated as additional." **Schema:** add to `audit_plan` — `is_additional` BIT DEFAULT 0 · `additional_reason` nvarchar(max) (≥50 char min when is_additional=1). **Window-calc exclusion:** D-049 next-due calculation `WHERE is_additional=0 AND status NOT IN (CANCELLED)` — additional audits never reset the cadence clock; the regular 8–12 month vessel cadence / 9–15 month office cadence runs independently. **Authority:** new sub-gate within `AUDIT_P_001` — only DPA (matching D-064 cancellation authority) can set `is_additional=1` at audit_plan creation. SEQ Manager creates routine audits as before; additional audits require DPA action. **Workflow:** identical to regular internal — same KSM-F-601 / F-602 / F-605 forms, same CAR engine, same Lead Auditor closure, same notification fanout (D-111/115). Only deltas are the flag, the reason text, the trigger linkage (D-122), and the UI/PDF treatment (D-123). **Validation:** `is_additional=1` requires `trigger_reason` ∈ {new additional values per D-122} AND `additional_reason` ≥50 chars AND `trigger_event_type` populated AND `trigger_event_ref` populated. **No T-90/T-30 alert ladder** for additional audits — they are reactive, not scheduled; planned_window dates remain mandatory for tracking but don't drive cadence alerts. | User direction 2026-05-18 PM |
| 122 | D-AUDRS-122 | R1.M | **Trigger reason enum extension + polymorphic triggering-event linkage — extends D-024.** **D-024 enum extended** with 5 new values applicable when `is_additional=1` (D-121): `FLAG_REQUEST` (Flag State letter / inspection) · `PSC_FOLLOWUP` (PSC follow-up audit demanded) · `DETENTION_FOLLOWUP` (post-detention internal audit) · `INCIDENT_FOLLOWUP` (post-incident — distinct from existing UNSCHEDULED_INCIDENT which is for incident-triggered audits within the cadence) · `MGMT_DIRECTIVE` (Managing Director or DPA management decision, no external trigger). **Polymorphic linkage:** add to `audit_plan` — `trigger_event_type` enum (PSC_INSPECTION, DETENTION_NOTICE, FLAG_LETTER, INCIDENT_REPORT, MGMT_DIRECTIVE, OTHER) · `trigger_event_ref` nvarchar(200). **Resolution rules:** (a) when `trigger_event_type=PSC_INSPECTION`, `trigger_event_ref` = FK `psc_inspection.id` (existing PSC record in VIMS); UI auto-resolves to inspection number + port + date. (b) when type=INCIDENT_REPORT, `trigger_event_ref` = FK to Safety module incident ID (cross-module link per D-065 pattern). (c) when type ∈ {DETENTION_NOTICE, FLAG_LETTER, MGMT_DIRECTIVE, OTHER}, `trigger_event_ref` = free text (external reference number) AND `audit_attachment` row required with category `TRIGGER_EVIDENCE` (PDF/JPG of Flag letter, detention notice, etc.). **UI:** create-additional-audit form shows type dropdown first; based on type, either a FK picker (PSC, Incident) or a text field + attachment slot (external types) appears. Backend validates that ref+attachment match the type rule. | User direction 2026-05-18 PM |
| 123 | D-AUDRS-123 | R1.M | **UI / PDF / KPI treatment for Additional Internal Audits — surfaced separately throughout.** **F 601 PDF:** generated header gets a red banner reading "ADDITIONAL AUDIT — DPA AUTHORISED" above the standard SMS-controlled letterhead; banner color = #e84f4f tint; banner includes `additional_reason` truncated to 200 chars + `trigger_event_type` label. Same for F 602 audit report PDF — banner persists on output for audit-trail clarity. **Audit register (`/inspections` list view):** "ADDITIONAL" badge inline on audit rows where `is_additional=1`; filter chip in sidebar lets DPA/Supts toggle (Show All / Routine only / Additional only); default = Show All. **KPI dashboard:** cadence compliance metric (audits-completed-vs-due) counts ONLY `is_additional=0` rows so additional audits don't inflate compliance numbers. Separate KPI card "Additional Audits This Quarter" tracks count + breakdown by trigger reason. **Audit-window UI on vessel home:** progressive alerts (D-050) for next routine audit display unchanged — additional audits sitting in the vessel's history don't change the T-90/T-30/T-0 messaging. **Notification handling:** existing `AUDIT_SCHEDULED` notification (per D-115 triple-channel) extended with badge text "ADDITIONAL" in subject line + Slack message header when fired for an additional audit; recipient resolution per D-038/D-102 unchanged. **Cross-module:** if `trigger_event_type=PSC_INSPECTION`, the underlying PSC inspection record gets a back-reference annotation "Additional internal audit raised — see AUD-YYYY-NNNN" so PSC reviewers see the audit chain. | User direction 2026-05-18 PM |
| 120 | D-AUDRS-120 | R1.L | **Adaptive 2-column desktop layout for NC + Observation wizards.** Extends D-AUDRS-116 (mobile-first wizard). User direction 2026-05-18 PM: "what you showed is on the mobile app but the user will use in desktop will it be same?" Answer: same wizard, adaptive layout. **Breakpoint:** viewport ≥1024px. **Layout:** left column (60% width) renders the wizard's single-question-per-screen content unchanged (prompt + inline example + input field + character counter + Save & Continue); right column (40% width) renders a **persistent context panel** containing: (a) read-only Part A auditor finding · (b) all previously answered wizard fields (collapsed cards, click to expand) · (c) progress indicator (which step, % complete, time spent) · (d) attachment thumbnails from prior steps. **Below 1024px** the right column collapses out of view (pure phone/tablet behaviour from D-116 remains). **Behaviour preserved across breakpoints:** still one question-per-advance; backend storage identical; D-074 ≥50 char rule applies same way; office-led drafting (D-118) continues to use dense-form view because trained Supts prefer it. **Observation wizard at ≥1024px:** same 2-column treatment with right panel showing Part A observation + corrective action drafted-so-far; because the Obs flow is only 3 questions, desktop users see all 3 inputs progressively but with full context always visible. **Keyboard support on desktop:** Enter advances; Esc returns to previous step; Cmd/Ctrl+S forces save. **Implementation note:** Tailwind responsive classes (`lg:grid-cols-[3fr_2fr]`) — no separate code path, single React component. Mobile-first principle (CLAUDE.md mandate) preserved — desktop is the enhancement. | User direction 2026-05-18 PM |
| 119 | D-AUDRS-119 | R1.K | **Photo-first capture DEFERRED to v1.1.** Considered as part of R1.K simplification options. User direction at R1.K close: keep evidence upload pattern as currently designed for v1.0 (BEFORE/AFTER photos required per CAR engine rules, 10 MB max per D-076, PDF/JPG/PNG/DOCX accepted). Photo-driven RCA suggestion + auto-text-fill is a v1.1 enhancement once we have operational data on which scenarios benefit most. v1.0 wizard (D-116) + template library (D-117) + office-led drafting (D-118) carry the simplification load. **No schema impact at v1.0.** | User direction 2026-05-18 PM |
| 110 | D-AUDRS-110 | R1.I | **Lead Auditor ≠ PIC enforced at action time — modifies D-AUDRS-058.** Original D-058 framed the constraint as a plan-time uniqueness check on `assigned_lead_auditor_user_id != assigned_pic_user_id`. With PIC no longer named at plan time (D-107), the constraint moves to action time: **when a user clicks "Start PIC Review" on any CAR for this audit, server-side check rejects if `current_user_id == audit.lead_auditor_user_id`** with HTTP 403 "Lead Auditor cannot review their own audit's findings." Returns to the action queue for another scoped reviewer to pick up. UI hides the action button for the Lead-Auditor-of-record on their own audits as a UX courtesy. The "DPA can be Lead Auditor" sub-rule of D-058 still holds — orthogonal to this enforcement change. | User direction 2026-05-18 |
| 106 | D-AUDRS-106 | R1.H | **New `master_hod_assignment` table — HoD ↔ department mapping with history + acting-HoD support.** Schema: `id` PK · `dept` enum (CREW, TECH, PURCHASE, IT, MARINE, OTHER) per D-AUDRS-017 · `user_id` FK users · `is_acting` BIT (acting/temp HoD vs. confirmed) · `effective_from` DATE · `effective_to` DATE NULL (NULL = currently active) · `created_by`, `created_at`. **Resolver for D-AUDRS-102 office `AUDIT_SCHEDULED` routing:** `SELECT user_id FROM master_hod_assignment WHERE dept = audit.auditee_office_dept AND effective_from <= GETDATE() AND (effective_to IS NULL OR effective_to >= GETDATE()) ORDER BY is_acting ASC, effective_from DESC LIMIT 1` — confirmed HoD wins over acting; latest assignment within a tier wins. **Multiple-active rows tolerated** (e.g. confirmed HoD on extended leave + acting HoD covering): resolver picks confirmed by default; future enhancement may notify both. **CRUD:** new `AUDIT_P_010` gate (SEQ Manager only) covers `master_hod_assignment` management — extends the gate family locked in D-AUDRS-083. **Supersedes the resolver portion of D-AUDRS-102** (which previously specified `users.role = HOD_<dept>` lookup); D-102's recipient list and routing-branches-on-auditee_type behaviour remain in force. **Audit-trail:** historical rows preserved; resolver respects effective_to so a past audit's notification can be retraced to the HoD-of-record at that time. Rejected alternatives: `users.role` enum (loses history, no acting semantics) and `users.is_hod + users.department` flags (still no history). | User direction 2026-05-18 |
| 99 | D-AUDRS-099 | R1.E+ | **SQE S 626 (Overview of SSEQ Management) DEFERRED from v1.0.** User direction 2026-05-14: "Overview of SSEQ Management will not be a part at the moment." **Supersedes:** (a) D-AUDRS-026 in full (monthly KPI export workflow removed from v1.0 build); (b) the S 626 portion of D-AUDRS-055's v1.0 PDF set — revised list is **F 601 + F 602 + KSM-F-NC-001 + KSM-F-OBS-001 (4 PDFs, was 5)**; (c) the landscape-orientation portion of D-AUDRS-095 — at v1.0 all generated PDFs are A4 portrait. **Implications:** `monthly_kpi_pdf.py` generator removed from v1.0 build scope; `master_ksm_sms_chapter` no longer needs to populate the SMS revision-tracking columns S 626 expected (D-091 master is still seeded but with reduced columns — `chapter_code`, `chapter_name` only at v1.0); no HSSEQ@kaizenship.net auto-mail scheduling needed at v1.0 or v1.1; the 28-column field mapping of S 626 in §18.x of this SSOT (when written) is descoped. **Deferral target:** v1.2 or later — to be re-prioritised after v1.0 ships and operational feedback determines whether VIMS auto-export is needed vs. continued manual workbook submission. | User direction 2026-05-14 |
| 134 | D-AUDRS-210 | R-EXT.1 (1A) | **v1.1 scope = ISM/ISPS/MLC/EMS/DOC system audits ONLY.** Class statutory surveys (SOLAS, MARPOL, Loadline, hull thickness, etc.) stay in Certificates module; cross-linked via `audit_detail.linked_cert_ids_csv` (D-202). Survey fields do NOT enter audit data model. | User direction 2026-05-18 PM (Batch 1A) |
| 135 | D-AUDRS-211 | R-EXT.1 (1A) | **Flag State direct audits = `audit_classification=EXTERNAL`; differentiated by `external_audit_org_type` enum {CLASS_SOCIETY, FLAG_STATE, RO, OTHER} on audit_detail.** No new sibling classification; logic identical across org_type. UI may filter/label but doesn't branch behaviour. | User direction 2026-05-18 PM (Batch 1A) |
| 136 | D-AUDRS-212 | R-EXT.1 (1A) | **Audit RO ≠ Vessel Class — first-class separation. SUPERSEDES `vessel.class_society` reuse portion of D-201.** New tables: `master_external_audit_org` (id UUID PK, name, org_type per D-211, country, optional linked_class_society_ref) + `vessel_audit_ro_delegation` (vessel_id, standard_code ISM/ISPS/MLC/EMS/DOC, delegated_org_id FK, effective_from/to). On registration: `external_audit_org_id` defaults to delegated RO for (vessel+standard); user override allowed. | User direction 2026-05-18 PM (Batch 1A) |
| 137 | D-AUDRS-213 | R-EXT.1 (1A) | **DOC audit scoped PER FLAG STATE — NOT per company.** KSM holds independent DOC certs per Flag (Thai DOC ≠ Panama DOC). New mandatory `flag_state_code` FK on audit_detail when `audit_subtype ∈ {DOC_*}`. UNIQUE constraint: at most 1 open DOC audit per (flag + cycle_year). Combined-event model: `parent_audit_event_id` self-FK; one parent DOC audit + N child vessel SMC audits (only vessels under that flag). Cert writeback per D-202 applies per-flag. | User direction 2026-05-18 PM (Batch 1A) |
| 138 | D-AUDRS-214 | R-EXT.1 (1A) | **DOC_INITIAL + DOC_INTERIM are first-class external audit subtypes.** Adds to D-200 enum. DOC_INITIAL creates DOC cert + sets first anniversary (per D-207 pattern). DOC_INTERIM = first DOC for new flag / ship type / major change; anniversary=NOT_SET, no alert ladder, superseded by next full DOC audit within 12 months. Per-flag per D-213. External audit subtype enum total = 18 (incl. ADDITIONAL). | User direction 2026-05-18 PM (Batch 1A) |
| 139 | D-AUDRS-215 | R-EXT.1 (1B) | **ISPS Initial Verification = `ISPS_INITIAL` per D-207** — no new subtype. Workflow identical to DOC_INITIAL: creates ISSC cert + sets first anniversary on close-out. | User direction 2026-05-18 PM (Batch 1B) |
| 140 | D-AUDRS-216 | R-EXT.1 (1B) | **`is_cycle_resetting` BIT on audit_detail for additional audits that legally reset cycle (operator transfer, re-Initial events).** DPA-only authority to flip ON; mandatory companion fields `cycle_reset_reason` (≥100 chars), `cycle_reset_authorised_by`, `cycle_reset_authorised_at`. When ON at close-out, cert writeback (D-202) OVERRIDES D-209's LEAVE_UNCHANGED and recomputes cert anniversary in Certs module. All events logged to psc_audit_log. | User direction 2026-05-18 PM (Batch 1B) |
| 141 | D-AUDRS-217 | R-EXT.1 (1B) | **External audit registration SLA: 7-day soft target / 30-day hard cap from audit completion.** 7-30 days = in-system warning banner + email/Slack reminder to DPA. >30 days = hard block unless DPA override with `late_registration_reason` ≥50 chars. New columns: `late_registration_reason`, `late_registered_by`, `late_registered_at`. Every override = audit-trail entry. | User direction 2026-05-18 PM (Batch 1B) |
| 142 | D-AUDRS-218 | R-EXT.1 (1B) | **Attachment versioning enum on `audit_attachment.attachment_version` {DRAFT, FINAL, SUPERSEDED}.** External-audit-report PDFs default FINAL on initial upload; DRAFT permitted only with DPA attestation reason. Re-upload of FINAL marks prior version SUPERSEDED automatically with attribution. | User direction 2026-05-18 PM (Batch 1B) |
| 143 | D-AUDRS-219 | R-EXT.1 (1B) | **Alt evidence paths via 4 new attachment categories: LETTER, EMAIL_EXPORT, MEETING_MINUTES_EXTRACT, OTHER_ATTESTATION.** Extends D-060 enum. D-076 mime whitelist extended with `.eml`. Use requires DPA attestation reason ≥50 chars on `audit_attachment.attestation_note`. | User direction 2026-05-18 PM (Batch 1B) |
| 144 | D-AUDRS-220 | R-EXT.1 (1C) | **Role-scoped registration enforcement.** Master can register VESSEL-side external audits (SMC/MLC/ISPS) for own vessel only (master_RoleByVessel scope). DPA + Marine Sup'tt can register OFFICE-side DOC audits. Marine Supt sub-scope mechanism documented as open follow-up for KLOSS Step 2. | User direction 2026-05-18 PM (Batch 1C) |
| 145 | D-AUDRS-221 | R-EXT.1 (1C) | **External audit dedup: soft-warn UI + DB UNIQUE on (vessel_id, external_audit_org_id, audit_subtype, audit_date_year_month).** DPA-only manual merge via dedicated action that consolidates findings under one canonical audit_detail row + soft-deletes the duplicate. | User direction 2026-05-18 PM (Batch 1C) |
| 146 | D-AUDRS-222 | R-EXT.1 (1C) | **Registration rework loop reuses existing PSC CAR `REWORK_REQUESTED` pattern — NO new DPA-arbiter concept.** Office reviewer can request rework on registered external audit; status flows registrant → office-review → REWORK_REQUESTED → registrant edit → re-submit → office-accept. Same state machine as PSC CAR per D-070. | User direction 2026-05-18 PM (Batch 1C) |
| 147 | D-AUDRS-223 | R-EXT.1 (1C) | **`master_external_auditor_category_map`** seeded with IACS labels (NK / ABS / DNV / BV / LRQA / KR / RINA / ClassNK) at KLOSS Step 2. Maps free-text auditor input to canonical IACS member identity for reporting + KPI rollups. | User direction 2026-05-18 PM (Batch 1C) |
| 148 | D-AUDRS-224 | R-EXT.1 (1C) | **Optional `clause_subref_text` column on `audit_finding_clause` (D-227) avoids master restructure.** Captures sub-clause precision (e.g. "MARPOL Annex VI Reg 14.1.3.b") without forcing new clause rows in master. Free text ≤200 chars. | User direction 2026-05-18 PM (Batch 1C) |
| 149 | D-AUDRS-225 | R-EXT.1 (1D) | **OTHER bucket on clause master + QA counter.** When auditor selects "OTHER" clause, free text mandatory + monthly DPA review for promotion to canonical master row. Counter on master_audit_clause_ref enables KPI on canonical-vs-other usage. | User direction 2026-05-18 PM (Batch 1D) |
| 150 | D-AUDRS-226 | R-EXT.1 (1D) | **`audit_finding_clause` junction table with `is_primary` BIT** + denormalised mirror column on audit_finding for read performance. Enforcement of single is_primary=1 per finding via app-layer or trigger — documented as open KLOSS Step 2 decision. | User direction 2026-05-18 PM (Batch 1D) |
| 151 | D-AUDRS-227 | R-EXT.1 (1D) | **Q18 REJECTED — NO VIMS dispute mechanism for external findings.** Disputes resolved at auditor's closing meeting BEFORE issue; report is immutable post-issue. **DROPS 6 columns + 1 gate** from prior proposed model (dispute_status, dispute_reason, dispute_resolved_by, etc.). | User direction 2026-05-18 PM (Batch 1D — REJECTION) |
| 152 | D-AUDRS-228 | R-EXT.1 (1D) | **Alt evidence path with DPA attestation extends D-219.** Adds `attestation_required` flag on attachment categories LETTER + EMAIL_EXPORT + MEETING_MINUTES_EXTRACT + OTHER_ATTESTATION. DPA attestation note ≥50 chars before close-out gate. | User direction 2026-05-18 PM (Batch 1D) |
| 153 | D-AUDRS-229 | R-EXT.1 (1D) | **Decouple `external_closure_status` from internal action completion.** Cert state (D-205) follows auditor's close-out letter — SMS rigour tracked separately via existing CAR engine completeness. Two distinct readings: "external auditor satisfied?" and "SMS corrective action complete?" — both must be true for full closure. | User direction 2026-05-18 PM (Batch 1D) |
| 154 | D-AUDRS-230 | R-EXT.1 (1E) | **Q21 REJECTED — NO finding reopen mechanism.** Recurrence at next audit = NEW finding; original stays CLOSED. No parent_finding_id, no reopen action, no resurrection state. | User direction 2026-05-18 PM (Batch 1E — REJECTION) |
| 155 | D-AUDRS-231 | R-EXT.1 (1E) | **Tiered EffRev for external NCs — SUPERSEDES D-204's "no Effectiveness Review" portion.** External Major NC = EffRev MANDATORY (DPA performs, T+90 days, evidence required). External Minor NC = EffRev OPTIONAL (DPA discretion). External Observation = no EffRev (matches D-082 internal logic). Wraps into existing D-082 EffRev workflow with `is_external_tier` enum. | User direction 2026-05-18 PM (Batch 1E — SUPERSEDES D-204 portion) |
| 156 | D-AUDRS-232 | R-EXT.1 (1E) | **Finding priority enum {LOW, MEDIUM, HIGH, CRITICAL}** + auto-CRITICAL escalation rule: any Major NC where `certificate_impact ∈ {SUSPENDED, WITHDRAWN}` automatically gets priority=CRITICAL with 24h SLA + 7d CA plan + daily DPA digest notification. | User direction 2026-05-18 PM (Batch 1E) |
| 157 | D-AUDRS-233 | R-EXT.1 (1E) | **Type-ahead cert linkage with vessel/flag/cert_type scoping.** External audit registration picker for `linked_cert_ids_csv` (D-202) filters available cert rows to (vessel_id matches + flag_state matches DOC scope + cert_type compatible with audit_subtype). Prevents accidental cross-vessel linkage. | User direction 2026-05-18 PM (Batch 1E) |
| 158 | D-AUDRS-234 | R-EXT.1 (1E) | **Outbox pattern for cert writeback.** Audit close-out enqueues writeback rows into `cert_writeback_outbox` table (per D-202 + D-205); background worker drains to Certs module. Audit close-out NEVER blocks on Certs availability. Retry policy: exponential backoff, dead-letter to DPA queue after 24h. | User direction 2026-05-18 PM (Batch 1E) |
| 159 | D-AUDRS-235 | R-EXT.1 (1F) | **Q25 closure — post-closure cert linkage edits.** DPA can ADD or REMOVE cert linkage on already-closed external audits with reason ≥50 chars; new outbox row writes amended state to Certs module. Audit-trail captures before/after. Gate: AUDIT_P_014 (writeback). | User direction 2026-05-18 PM (Batch 1F) |
| 160 | D-AUDRS-236 | R-EXT.1 (1F) | **CAS (Compare-And-Swap) on cert version for writeback safety.** `cert_writeback_outbox` row carries the `cert_version` read at audit close-out; Certs module rejects writeback if current cert_version != expected. CONFLICT outbox status surfaces in DPA queue with two options: ACCEPT (re-read current cert state + retry) or FORCE (DPA override with reason). Requires Certs API to expose `version` field. | User direction 2026-05-18 PM (Batch 1F) |
| 161 | D-AUDRS-237 | R-EXT.1 (1F) | **Bidirectional SSOT cross-reference table at head of both Audit + Certs SSOTs.** Documents which decisions in one SSOT directly affect the other; mechanical re-grep check at KLOSS Step 2 verifies consistency. Open action item for Certs SSOT update before KLOSS Step 2 build. | User direction 2026-05-18 PM (Batch 1F) |
| 162 | D-AUDRS-238 | R-EXT.1 (1F) | **Multi-gate cert suspension workflow.** Setting cert_impact=SUSPENDED at close-out requires: (a) external auditor's close-out letter attachment mandatory; (b) two-step DPA confirmation including typed cert# match; (c) Flag State notification tracking row in new `flag_state_notification_log` (notified_at, notified_to, ack_received_at). Quad-recipient notification (DPA + FM + Master + Flag-State-liaison) auto-fires. | User direction 2026-05-18 PM (Batch 1F) |
| 163 | D-AUDRS-239 | R-EXT.1 (1F) | **New `cert_change_log` table in Certs module (append-only).** Captures every Certs row state change with source attribution (`source_module` enum: CERTS, AUDIT, CMS, MANUAL_OVERRIDE). Audit writebacks insert rows; Certs UI shows full change history. Cross-module obligation on Certs SSOT/DocSuite for compliance. | User direction 2026-05-18 PM (Batch 1F) |
| 164 | D-AUDRS-240 | R-EXT.1 (1G) | **KEY: Cert anniversary = Class Status Report sync (existing Certs-module pattern) — NOT audit-side override.** Audit module READS anniversaries from Certs module; never writes anniversary directly. Class Status Report sync (per D-CERT-063) owns reconciliation. Drops the `cert_anniversary_date_override` column proposed in earlier draft. | User direction 2026-05-18 PM (Batch 1G) |
| 165 | D-AUDRS-241 | R-EXT.1 (1G) | **Vessel ownership/flag change handling is ENTIRELY Certs-module concern.** When vessel changes flag or owner, Certs module manages cert lifecycle (issue/withdraw). Audit module reads the new state via D-202 read pattern. No audit-side mirror columns; no audit-side branching. Documented in §11 cross-module deps. | User direction 2026-05-18 PM (Batch 1G) |
| 166 | D-AUDRS-242 | R-EXT.1 (1G) | **New `master_audit_window_rule` table — data-driven window rules with IMO/MLC/ISPS citations.** Schema: id UUID PK · standard_code (ISM/ISPS/MLC/EMS/DOC) · subtype_code · window_open_offset_months · window_close_offset_months · cadence_months · regulatory_citation (IMO/MLC/ISPS section). Seeded at KLOSS Step 2 with current ISM ±3-month / MLC ±3-month / ISPS ±3-month rules. Window math reads this table (read-only) — Audit module never hardcodes window offsets. | User direction 2026-05-18 PM (Batch 1G) |
| 167 | D-AUDRS-243 | R-EXT.1 (1G) | **Class Status Report sync cadence + reconciliation rule documented in Certs SSOT (open action).** cert_change_log (D-239) entries flagged `source_module=CMS_CLASS_STATUS_REPORT_SYNC` when received. Audit module reads this log via cross-module API. Reconciliation: Class Status Report wins on conflicts (audit-side writebacks marked SUPERSEDED with attribution). | User direction 2026-05-18 PM (Batch 1G) |
| 168 | D-AUDRS-244 | R-EXT.1 (1G) | **External auditor sign-off = attached signed PDF only; NO auditor system access at v1.1.** External auditor never logs into VIMS; their "signature" = wet-ink on the printed close-out letter scanned and attached to audit_detail. Same posture as D-AUDRS-061 wet-ink rule applied to external context. | User direction 2026-05-18 PM (Batch 1G) |
| 169 | D-AUDRS-245 | R-EXT.1 (1H) | **`master_external_auditor` table + auto-suggest + pending-review on free-text fallback.** Schema: id UUID PK · name · org_id FK · credential · last_seen_at · review_status enum {ACTIVE, PENDING_REVIEW, REJECTED}. UI auto-suggests as auditor types; if no match, free-text creates a PENDING_REVIEW row that DPA reviews monthly (promote to ACTIVE or REJECT). | User direction 2026-05-18 PM (Batch 1H) |
| 170 | D-AUDRS-246 | R-EXT.1 (1H) | **Minimal PII surface for external auditor.** Only name + org_id captured. NO credential/qualification/signature/contact/biometric fields. GDPR legal basis: Art 6(1)(f) legitimate interest + Art 6(1)(c) legal obligation (ISM). Art 17(3)(b)+(e) exemptions on erasure requests. Documented in §11 + privacy notice. | User direction 2026-05-18 PM (Batch 1H) |
| 171 | D-AUDRS-247 | R-EXT.1 (1H) | **MAJOR SCOPE LOCK — RightShip (Q38–Q45) deferred to v1.2 build cycle; Manning + Security (Q46–Q50) deferred to v1.3 build cycle.** THIS interrogation cycle = Internal + External Audit ONLY. From here forward batches focus on cross-cutting v1.0 gaps + deployment/legal/integration + meta. | User direction 2026-05-18 PM (Batch 1H — SCOPE LOCK) |
| 172 | D-AUDRS-248 | R-EXT.1 (1I) | **`audit_end_date` column on audit_detail; SLA clocks anchor on end_date.** `inspection_date` retained as audit_start_date semantically. Validation: end_date >= start_date server-side. Both editable until status=CLOSED. NC closure SLAs (D-073) count from `audit_end_date`. PDF F 601 footer renders "Audit Period: start – end". Single-day audits: end=start. | User direction 2026-05-19 (Batch 1I) |
| 173 | D-AUDRS-249 | R-EXT.1 (1I) | **Dual-TZ model: storage UTC; office display ITC; vessel display from CMS WRH module.** Same integration family as PSC inspection. `CmsWrhClient.getVesselLocalTime(vessel_id, datetime_utc)` returns vessel local time + UTC offset valid at that instant. **NC closure SLA clock = ITC (office TZ)** — vessel TZ shifts mid-voyage and would be non-deterministic. PDF rendering: office PDFs show `(ITC)` suffix; vessel-issued sign blocks (Master B + D) show vessel LT with `(LT UTC±HH:MM)`. Audit trail stores UTC + display TZ. | User direction 2026-05-19 (Batch 1I — OVERRIDE) |
| 174 | D-AUDRS-250 | R-EXT.1 (1I) | **Signatures bind to RANK (Master/CO/CE), not person; CMS live-crew lookup at sign time.** Same integration pattern as PSC inspection. `CmsCrewClient.getActiveCrewByRank(vessel_id, rank, datetime_utc)` returns active user_id at that instant. PDF parts B + D render whichever Master signed each part; no handover workflow. UI badge ("Signed by previous Master / current Master") for context. Extends to CO/CE/Safety Officer ranks on F 605 checklist rows. psc_audit_log captures every signature event with user_id + rank_at_signing + datetime + vessel_local_time + part_label. | User direction 2026-05-19 (Batch 1I — OVERRIDE) |
| 175 | D-AUDRS-251 | R-EXT.1 (1I) | **REJECTED — Lead Auditor reassignment is OPERATIONAL POLICY, not software.** Lead Auditor must complete all open audits + close all assigned NCs (incl. EffRev per D-082) BEFORE departure from company. HR offboarding checklist enforces gate operationally. **AUDIT_P_015 NOT created.** SSOT §16 adds new HR-offboarding callout. | User direction 2026-05-19 (Batch 1I — REJECTION) |
| 176 | D-AUDRS-252 | R-EXT.1 (1I) | **REJECTED — DPA-on-leave is not a real KSM scenario.** DPA retains login + completes all DPA actions regardless of physical absence. **D-AUDRS-106 `master_hod_assignment` NOT extended to DPA dept.** Edge case (DPA medically incapacitated extended period): Flag State notification of DPA succession per ISM 4.2 — appoint new permanent DPA, not acting. Saves ~2 columns + 1 audit-trail event_type + 1 gate. | User direction 2026-05-19 (Batch 1I — REJECTION) |
| 177 | D-AUDRS-253 | R-EXT.1 (1J) | **Acting HoD auth = DPA + Fleet Manager (FM) only.** New gate AUDIT_P_016. Self-acting forbidden. Auto-expiry server job at 00:01 ITC flips is_acting=0 when effective_to < today. Max acting period 90 days (re-issue required beyond). Every flip writes psc_audit_log event with both flipper user_id + affected user_id + dept. FM-only screen at `/admin/hod-coverage` lists active assignments; DPA gets same screen read-write. | User direction 2026-05-19 (Batch 1J) |
| 178 | D-AUDRS-254 | R-EXT.1 (1J) | **🔑 KEY MODEL SHIFT — Audit vessel-visit is offline-by-design (PROCESS, not software).** Workflow = pre-board prep (ashore online) → conduct onboard offline (paper notes) → enter report ashore online → vessel acknowledges. New audit_detail.status chain: `REPORT_FINALIZED → VESSEL_ACKNOWLEDGED → CLOSURE_IN_PROGRESS`. New action "Vessel Acknowledge Audit Report" Master-rank-bound (per D-250). **NC closure SLA clocks (D-073) anchor on VESSEL_ACKNOWLEDGED**, not finding_raised_at — MODIFIES D-073 deadline math. New gate AUDIT_P_017. D-062 online-only stays as-is. NO paper-attachment workflow, NO backdate-with-reason for offline period, NO offline cache. | User direction 2026-05-19 (Batch 1J — KEY SHIFT) |
| 179 | D-AUDRS-255 | R-EXT.1 (1J) | **30-day Master-signature backdate window with reason ≥50 chars.** New audit-trail child table `audit_finding_sign_event` capturing: user_id, rank_at_signing, claimed_sign_datetime (vessel local TZ), actual_entered_at (UTC server clock), backdate_reason (nullable), part_label. PDF Part B renders claimed date in vessel local TZ. Beyond 30 days = hard block; Office Memo escalation outside system. No new gate — uses AUDIT_P_004. Bounded in practice by D-254 VESSEL_ACKNOWLEDGED anchor. | User direction 2026-05-19 (Batch 1J) |
| 180 | D-AUDRS-256 | R-EXT.1 (1J) | **SEQ-dept CoI rule: when auditee_office_dept='SEQ', Lead Auditor user_id MUST NOT = DPA's user_id (HTTP 422 on save).** Primary path = cross-dept HoD with new `qualified_for_seq` BIT on master_audit_qualified_auditor. External auditor fallback (D-200 EXTERNAL classification) reserved for cases with no qualified cross-dept HoD. UI pre-filters Lead Auditor picker when auditee_office_dept=SEQ. | User direction 2026-05-19 (Batch 1J) |
| 181 | D-AUDRS-257 | R-EXT.1 (1K) | **15-year retention** for full audit graph: audit_detail + audit_finding + audit_finding_clause + audit_attachment (incl. PDF/scan blobs) + notification_delivery_log + psc_audit_log audit-linked rows + audit_finding_sign_event. Retention clock = audit_detail.created_at. **Soft-delete only at v1.0** via existing is_deleted BIT family. **No hard-delete** at v1.0 (DPA-only flip with reason ≥50 chars + audit log). Hard-delete + archival tier = v2+. Wider than D-114's 7y SMS-doc retention because Flag/RO defence horizon spans 3 ISM cycles. | User direction 2026-05-19 (Batch 1K) |
| 182 | D-AUDRS-258 | R-EXT.1 (1L) | **No OCR/biometric/handwriting signature verification at v1.0.** No image-stored separately, no third-party signature-verification SaaS. Forgery risk accepted; mitigation = audit-trail of upload user_id + wet-ink+scan-back + SMS doc control retention per D-114. §16 OPM documents known limitation. | User direction 2026-05-19 (Batch 1L) |
| 183 | D-AUDRS-259 | R-EXT.1 (1L) | **🔑 KEY UNBLOCK — KSM SSQE confirms all Flags in KSM portfolio accept wet-ink + scan-back model.** D-AUDRS-061 stands UNMODIFIED. No eIDAS / 21 CFR Part 11 / MSC.1/Circ.1593 e-sig conformity required at v1.0. **STRIPS "HARD BLOCKER — Flag State confirmation required" annotation from D-061** at this SSOT merge. Future new flags presumed compliant unless KSM SSQE flags otherwise. | User direction 2026-05-19 (Batch 1L — UNBLOCK) |
| 184 | D-AUDRS-260 | R-EXT.1 (1L) | **External auditor's official stamp captured as part of scanned `external_audit_report_pdf` (D-201) and/or close-out letter (D-204) — no separate stamp column.** §16 OPM instructs External-audit registrar to ensure stamped page is part of scan. Internal audits: no stamp; Lead Auditor signature per D-061 suffices. Saves: 1 column, 1 image-upload widget, ~3 PDF render lines. | User direction 2026-05-19 (Batch 1L) |
| 185 | D-AUDRS-261 | R-EXT.1 (1L) | **🔑 QR/hash PDF replay-prevention — closes scenarios A (same-scan reuse against diff finding), B (outdated-scan reuse after office RCA edit per D-081), C (cross-vessel scan reuse).** New table `audit_pdf_generation` (id UUID PK, finding_id, audit_detail_id, pdf_kind enum F_601/F_605/EXTERNAL_REPORT/EXTERNAL_CLOSEOUT_LETTER/OTHER, pdf_version int, content_hash SHA-256, qr_payload JSON, generated_at, generated_by, is_superseded BIT). QR embedded on every page footer of VIMS-generated PDFs. New columns on audit_attachment: linked_pdf_generation_id (nullable), pdf_hash_validation_status enum {MATCHED, MISMATCH_FINDING, MISMATCH_VESSEL, MISMATCH_VERSION, UNREADABLE, NOT_APPLICABLE}, validated_at, validator_message. Upload-time pipeline: QR decode → compare → write status. Upload NEVER blocked; MISMATCH/UNREADABLE surface in DPA queue at `/dpa/scan-validation-queue`. DPA actions: ACCEPT_WITH_REASON (≥50 chars) or REJECT_AND_REQUEST_RESCAN. New gate AUDIT_P_018 (DPA-only). External-audit attachments (D-201/204) = NOT_APPLICABLE. | User direction 2026-05-19 (Batch 1L — OPTION A selected) |
| 186 | D-AUDRS-262 | R-EXT.1 (1M) | **DPA "Failed Notifications" widget at `/dpa/notifications/failed`** listing rows from notification_delivery_log (D-114) where status=FAILED_PERMANENT. Two actions per row: Manual Retry (resets attempt_count=0, status=QUEUED) and Mark as Notified Offline (status=RESOLVED_OFFLINE with reason ≥30 chars). Logged to psc_audit_log. Widget polls every 60s. In-system notification remains source-of-truth. No automatic FM/IT escalation — DPA owns. | User direction 2026-05-19 (Batch 1M) |
| 187 | D-AUDRS-263 | R-EXT.1 (1M) | **No opt-out at v1.0 for the 7 audit notification types (D-115).** User Preferences screen displays them as read-only ("Audit notifications are mandatory — regulatory requirement"). Future v1.1+ may add opt-out for non-regulatory types (none planned at v1.0). | User direction 2026-05-19 (Batch 1M) |
| 188 | D-AUDRS-264 | R-EXT.1 (1M) | **🔑 SUPERSEDES D-AUDRS-112 email-source portion — vessel email pulled from CMS, NOT from new VesselData column.** PSC inspection does NOT send email; Audit is first VIMS feature needing email regulatory trail. New service: `CmsVesselClient.getOfficialEmail(vessel_id)`. Same integration family as D-249 WRH + D-250 crew. **NO new `VesselData.official_email` column in VIMS** — D-112 column provisioning RESCINDED. 15-min cache. Failure mode: null/empty → status=FAILED_PERMANENT with last_error='CMS_NO_EMAIL_ON_FILE', surfaces in D-262 DPA queue. Cross-module: add `GET /cms/vessels/{vessel_id}/official_email` to §11 deps. | User direction 2026-05-19 (Batch 1M — SUPERSEDES D-112) |
| 189 | D-AUDRS-265 | R-EXT.1 (1M) | **Per-vessel Slack channel only — no fleet-wide DPA channel.** master_slack_channel row per vessel: scope_type='VESSEL', scope_value=vessel_id, notification_types_csv covering all 7 audit types. Reuses KSM's existing per-vessel channels. No per-notification-type override at v1.0. **Office-internal audits SKIP Slack entirely at v1.0** — in-system + email only. Saves: fleet-wide aggregator config + override table + office-dept channel scaffolding. | User direction 2026-05-19 (Batch 1M) |
| 190 | D-AUDRS-266 | R-EXT.1 (1N) | **DocSuite acceptance criteria — mechanical re-grep ≥99% coverage matching Certs 199/199 pattern.** Each locked D-AUDRS-### tagged with `required_in:[doc_list]` listing 1-5 canonical docs where mention is mandatory. Required-mention matrix pre-defined in COVERAGE.md before generation starts. ≤1% misses tolerated with documented reason. Audit script = same Python re-grep that produced Certs 199/199. | User direction 2026-05-19 (Batch 1N) |
| 191 | D-AUDRS-267 | R-EXT.1 (1N) | **Seed CSV provenance — every seed CSV gets sibling `<file_name>_provenance.md`** capturing: source document · page range/URL · extraction date · extractor (LLM model ID or human) · reviewer (always human — KSM SSQE Manager or DPA) · review date · change log. Auditable chain from regulatory source to running DB. Applies to all audit seeds incl. master_audit_area / master_audit_qualified_auditor / master_rca_template / master_external_audit_org / master_audit_window_rule / master_external_auditor / master_audit_clause_ref. | User direction 2026-05-19 (Batch 1N) |
| 192 | D-AUDRS-268 | R-EXT.1 (1N) | **FIELD_MAP.md UI cell format = `<mockup_id>:<element_id>`** (e.g. `MOCKUP-VESSEL-04:nc_wizard_step3.rca_input`). For not-yet-wireframed features, cell = `MOCKUP-PENDING-KLOSS-STEP-2` — DocSuite Step 2 produces the mockup. Never leave a UI cell blank. | User direction 2026-05-19 (Batch 1N) |
| 193 | D-AUDRS-269 | R-EXT.1 (1N) | **COVERAGE.md formula — 11 canonical docs:** PRD · BACKEND_STRUCTURE · APP_FLOW · DATA_MODEL · RBAC · FIELD_MAP · PDF_TEMPLATES · SEEDS_PROVENANCE · CROSS_MODULE_DEPS · MIGRATION · TEST_PLAN. **Decision count at v1.1 close = ~189 active** (123 v1.0 + 66 v1.1 incl. D-271 standard; minus 3 superseded retained). **N = sum of `required_in:[]` lengths across all decisions** (NOT 189×11). Estimated N ≈ 700-900 for v1.1 Audit DocSuite. Exact N confirmed at DocSuite Step 2 kickoff. | User direction 2026-05-19 (Batch 1N) |
| 194 | D-AUDRS-270 | R-EXT.1 (1N) | **Certs DocSuite canonical, Safety secondary.** Certs (199/199 GREEN, 2026-05-13) more recent + larger scope + cross-module integration directly load-bearing for Audit. Safety (159/159 GREEN, 2026-04-17) referenced for crew-side wizard patterns (D-116 references Safety's incident-form simplification). COVERAGE.md opening section cites both with chosen-pattern declaration. | User direction 2026-05-19 (Batch 1N) |
| 195 | D-AUDRS-271 | R-EXT.1 (1N — Q-STD-1) | **🔑 CROSS-CUTTING DB TABLE CREATION STANDARD (user-supplied governance).** Every new table: (1) MUST contain `id` column (2) `id` = UNIQUEIDENTIFIER PRIMARY KEY with NEWSEQUENTIALID() default unless exception approved (3) NO INT IDENTITY for new development (4) FK columns = same UNIQUEIDENTIFIER datatype (5) Naming: PK = `id`; FK = `<parent_table_name>_id` (6) UUID-based keys immutable after create. Legacy psc_inspection / psc_corrective_action / psc_activity_history retain INT IDENTITY (read-only inheritance) as ONLY exception. MIGRATION.md must include verification grep script. Cross-module callout RESOLVED externally — dev team already handling Safety + Certs sweep. | User direction 2026-05-19 (Batch 1N — Q-STD-1 cross-cutting) |
| 196 | D-AUDRS-272 | R-EXT.1 (1O) | **Single-tenant for KSM at v1.0 — same tenancy posture as existing VIMS.** No `tenant_id` column on audit-domain tables. All KSM-specific seeds (14-area scorecard D-105, KSM SMS chapter list, F 604/605/606, NC enum D-018, per-flag DOC D-213) hardcoded. Multi-tenant retrofit = v2+ work documented in BACKEND_STRUCTURE.md future-work appendix. | User direction 2026-05-19 (Batch 1O) |
| 197 | D-AUDRS-273 | R-EXT.1 (1O) | **Data residency inherits existing VIMS deployment region.** Database lives alongside existing VIMS tables in same SQL Server instance. GDPR + per-flag residency inherit existing VIMS posture. CROSS_MODULE_DEPS.md records: "Audit data residency = same as parent VIMS deployment. Confirm regional placement with KSM IT at deployment-config phase, not audit-spec concern." | User direction 2026-05-19 (Batch 1O) |
| 198 | D-AUDRS-274 | R-EXT.1 (1O) | **🔑 Audit module is NOT part of offline capability — pure online software.** D-AUDRS-062 online-only stands. **D-AUDRS-254's "offline-by-design" is the PROCESS model only (paper notes onboard); NOT a software offline mode.** Build team MUST NOT add service workers / IndexedDB / PWA offline shells / local-storage caching of audit data for audit-module UI. Per-screen "are you online?" checks unnecessary — assume online; normal HTTP error handling for transient disconnects. | User direction 2026-05-19 (Batch 1O — CRITICAL CLARIFICATION) |
| 199 | D-AUDRS-275 | R-EXT.1 (1O) | **RPO/RTO/backup cadence inherits existing PSC inspection module configuration.** No audit-specific override. CROSS_MODULE_DEPS.md records: "Audit RPO/RTO = inherited from PSC inspection module deployment; confirm exact values with KSM IT during DocSuite Step 2." 15y audit-graph retention (D-257) sits ATOP normal backup — independent concerns. If PSC backup retention < 15y, gap covered by D-257 soft-delete retention in primary DB (no special archive tier at v1.0). | User direction 2026-05-19 (Batch 1O) |
| 200 | D-AUDRS-276 | R-EXT.1 (1O) | **Auth + MFA inherit existing VIMS — JWT issuance + lifetime + MFA matrix + SSO/AD posture.** No audit-module-specific token class or MFA override. If VIMS later strengthens MFA for DPA/FM/Lead Auditor/Master roles, applies VIMS-wide, not as audit-module patch. DocSuite RBAC.md references VIMS auth spec by link, doesn't redefine. | User direction 2026-05-19 (Batch 1O) |
| 201 | D-AUDRS-277 | R-EXT.1 (1P) | **Inherit existing VIMS SMTP** — same provider + bounce-handling pipeline. Audit emits to existing platform send queue. Bounces feed into notification_delivery_log (D-114) with delivery_status=BOUNCED → 3× retry over 24h per D-111 → permanent failures surface in D-262 DPA widget. If VIMS SMTP infra undocumented at DocSuite Step 2, escalate as VIMS-platform prerequisite (NOT audit-module build task). | User direction 2026-05-19 (Batch 1P) |
| 202 | D-AUDRS-278 | R-EXT.1 (1P) | **Single KSM Slack workspace at v1.0** matching Q80 single-tenancy. master_slack_channel webhooks all point into the one KSM workspace already used for safety + PSC + other VIMS Slack integrations. Multi-tenant Slack = v2+ requires `workspace_id` column + per-tenant webhook routing layer. | User direction 2026-05-19 (Batch 1P) |
| 203 | D-AUDRS-279 | R-EXT.1 (1P) | **CROSS_MODULE_DEPS.md pins minimum compatible versions** of: (1) Safety module (incident lookup for INCIDENT_FOLLOWUP per D-122); (2) Certs module (cert_change_log D-239 + version field D-236 + anniversary read pattern D-240/243; D-237 bidirectional SSOT xref); (3) CMS (getVesselLocalTime D-249 + getActiveCrewByRank D-250 + getOfficialEmail D-264); (4) HRM501 (vessel-side rank API per D-280); (5) Live PSC inspection module (psc_inspection / psc_corrective_action / psc_activity_history with audit_classification enum incl. EXTERNAL per D-200). Integration tests at KLOSS Step 3 verify against pinned versions; failures block Phase 0 cutover. Pin format = semver-like vMAJOR.MINOR.PATCH. | User direction 2026-05-19 (Batch 1P) |
| 204 | D-AUDRS-280 | R-EXT.1 (1P) | **🔑 KEY SPLIT — HRM501 = VESSEL-SIDE ranks only. Office-side = VIMS `users.role` standard.** Vessel users (Master, CO, CE, Safety Officer, ratings): `Hrm501Client.getCurrentRank(user_id)` live read-only API; 15-min cache. Office users (DPA, FM, Marine Sup'tt, HoD, SEQ Manager): rank/role = VIMS users.role; NO HRM501 lookup. **`master_audit_qualified_auditor` gets new `auditor_scope` enum {VESSEL_SIDE, OFFICE_SIDE}** so resolver picks right lookup at runtime. NO rank stored on qualified-auditor row (would go stale on promotion). `qualified_for_seq` BIT (D-256) is OFFICE_SIDE only. NO mirror tables in VIMS — single source of truth in HRM501 / users table. | User direction 2026-05-19 (Batch 1P — KEY SPLIT) |
| 205 | D-AUDRS-281 | R-EXT.1 (1P) | **Device/browser matrix:** Desktop = Chrome 120+ / Edge 120+ / Safari 17+ / Firefox 121+. Mobile = iOS 16+ Safari, Android 13+ Chrome. Wizard adaptive per D-120 (≥1024px=2-column; <1024px=mobile-first). Test devices = iPad 12.9" + iPhone 6.7". Not supported at v1.0: IE11, tablet-Android <13, in-app browsers (LinkedIn/WeChat) — documented in §16 Known Limitations. Audit module's matrix inherits broader VIMS or becomes VIMS-wide default if VIMS lacks formal matrix. TEST_PLAN.md records exact list. | User direction 2026-05-19 (Batch 1P) |
| 206 | D-AUDRS-282 | R-EXT.1 (1Q) | **English-only UI at v1.0; plain-language wizard (D-116) targets CEFR B1 reading level.** Short sentences + common vocabulary + jargon replaced with plain English. Inline examples + help text on every wizard step. Translation = v2+ if KSM expands to non-English-proficient crew (none currently). §16 OPM documents literacy assumption per STCW Reg. VI/1. TEST_PLAN.md includes readability check (Flesch-Kincaid grade ≤8). | User direction 2026-05-19 (Batch 1Q) |
| 207 | D-AUDRS-283 | R-EXT.1 (1Q) | **Pre-merge supersedes audit (executed at this SSOT merge).** Cataloged supersedes in v1.1 cycle: D-107..110 supersede D-056 + D-100 (PSC-style PIC); D-212 supersedes D-201 org-identity portion; D-202 supersedes D-CERT-025; D-216 modifies D-049 (cycle-reset); D-264 supersedes D-112 email-source portion; D-254 anchors NC SLA on VESSEL_ACKNOWLEDGED (modifies D-073); D-259 strips HARD BLOCKER from D-061; D-256 + D-280 extend D-039 (no supersede); D-274 re-emphasises D-062 + clarifies D-254 is process-only. Final grep at SSOT merge catches anything missed. | User direction 2026-05-19 (Batch 1Q) |
| 208 | D-AUDRS-284 | R-EXT.1 (1Q) | **🔑 ID allocation convention:** D-AUDRS-001..123 = v1.0 Internal Audit (FROZEN at v0.18). **D-AUDRS-124..199 = RESERVED for v1.0 supplemental** during DocSuite Step 2 (schema fixes / validation gaps / seed corrections; requires DPA + Prince re-confirm). D-AUDRS-200..287 = v1.1 External Audit + cross-cutting standards. **D-AUDRS-288..299 = RESERVED for v1.1 supplemental.** D-AUDRS-300+ = v1.2 RightShip. D-AUDRS-400+ = v1.3 Manning/Security. Convention published in §0.5 + §9 header. | User direction 2026-05-19 (Batch 1Q) |
| 209 | D-AUDRS-285 | R-EXT.1 (1Q) | **🔑 OVERRIDE — Prince is final freeze authority.** Drops the "named KSM DPA / SEQ Manager confirms in writing" third step. Simplified two-step protocol: (1) LLM marks freeze candidate (interrogation closes + SSOT batch-merge complete); (2) Prince confirms freeze. v1.0 status: FROZEN at v0.18 per Prince confirmation 2026-05-18. v1.1 status: FROZEN at end of Batch 1Q (Q95 closure marks completion); SSOT batch-merge runs. DPA/SEQ Manager involvement is operational rollout (training, sign-off-by-use), NOT documentation gate. | User direction 2026-05-19 (Batch 1Q — OVERRIDE) |
| 210 | D-AUDRS-286 | R-EXT.1 (1Q) | **Reference version locked: KSM SSQE Manual Rev 01 Feb 2026.** All SSOT + DocSuite citations reference this version explicitly with chapter + sub-section + page where applicable. Mid-build revision handling: Minor revision (typo/clarification) = diff & absorb in next sprint, no SSOT change. Major revision (process change / restructure / §10 overhaul / new audit-area / NC threshold change) = SSOT re-interrogation round R-AUD-vN.0; affected decisions get `REVIEW-PENDING-MANUAL-REV-<rev_number>` status; build paused on affected modules. Quarterly grep cadence on version-stamp drift. §0.4 added at this SSOT merge listing all authoritative reference doc versions. | User direction 2026-05-19 (Batch 1Q) |
| 211 | D-AUDRS-287 | R-EXT.1 (1Q) | **🔑 Internal Audit integration coverage explicitly locked — 3 deferred-to-v2 integrations.** (1) **PMS module = MANUAL REFERENCE ONLY at v1.0** — auditor enters PMS task ID/title as free text in audit_finding.description / audit_finding_nc.root_cause_summary; NO `pms_task_id` FK; NO live API. (2) **SMS Document Control = STATIC CONSTANTS ONLY at v1.0** — Filing reference tags (A-2/A-9/A-20/A-28) on F 601/F 602/KSM-F-NC-001 PDFs rendered as static derived constants; NO SMS Doc Control lookup; NO `sms_doc_id` FK. (3) **Crew Training/Competency = MANUAL REFERENCE ONLY at v1.0** — D-117's TRAINING_GAP RCA template doesn't FK to training records; auditor enters crew + gap as free text; NO `training_record_id` FK. All three deferred to v2+ for live API integration. **§11 Cross-Module Dependencies table REWRITTEN at this SSOT merge** to reflect 8 active integrations (CAR engine, PSC Inspection, Circular module D-065, Safety module D-122, CMS-WRH D-249, CMS-crew D-250, CMS-email D-264, HRM501 D-280) + 3 deferred-to-v2. Build-team posture: every cross-module call in DocSuite DATA_MODEL.md or APP_FLOW.md MUST trace to one of the 8 active integrations; anything not listed rejected at code review. | User direction 2026-05-19 (Batch 1Q — OPTION A) |

---

## 10. References

| Doc | Path | Role |
|-----|------|------|
| Existing PRD | `VIMS DOCS/PRD.md` | Live Inspection PRD — v1 baseline |
| Backend Schema | `VIMS DOCS/BACKEND_STRUCTURE.md` | Live table definitions + API contracts |
| App Flow | `VIMS DOCS/APP_FLOW.md` | Live screen inventory |
| Implementation Reference | `VIMS DOCS/CURRENT_IMPLEMENTATION_REFERENCE.md` | Snapshot of current routes / RBAC / live tables |
| Later Changes | `VIMS DOCS/LATER_CHANGES.md` | Post-baseline overrides (CAR workflow, dashboard, reports) |
| AI Governance | `VIMS DOCS/CLAUDE.md` | Inspection module AI agent rules |
| KLOSS Framework | `KLOSS FRAMEWORK/` | Methodology this module follows |
| Safety SSOT (reference pattern) | `VIMS-SAFETY-MODULE-SSOT.md` | Same SSOT structure used here |
| Certs SSOT (reference pattern) | `VIMS-CERTIFICATES-MODULE-SSOT.md` | Same SSOT structure used here |
| INDEX.md | `INDEX.md` | Master file catalog |
| **SSQE Manual §10 (Audits & Management Review)** | `SSQE Manual- Rev 01 Feb 2026/SSQE Manual- Rev 01 Feb 2026.pdf` pp 206–219 | **KSM-authoritative audit procedure** — drives D-AUDRS-016 to 032 |
| SSQE Manual §15 (PSC) | same PDF pp 251–269 | Cross-reference for existing PSC workflow |
| SSQE Manual §4 (Safety Inspection) | same PDF p 53+ | Cross-reference for Safety module + SOI; cross-link with §10 |
| SQE F 601 Audit Plan | `SSQE Annex 1-Forms/SQE F 601 Audit Plan.xls` | Audit registration field source — D-AUDRS-019, D-AUDRS-023 |
| SQE F 602 Internal Audit Report | `SSQE Annex 1-Forms/SQE F 602 Internal Audit Report.docx` | Audit-record + 14-area scorecard source — D-AUDRS-027 to 030 |
| SQE F 604 Manning Office Audit Checklist | `SSQE Annex 1-Forms/SQE F 604 Check List for Manning Office audit.xls` | Checklist seed (~46 items) — D-AUDRS-020 |
| SQE F 605 Vessel Internal Audit Checklist | `SSQE Annex 1-Forms/SQE F 605 Vessel Internal Audit Checklist.xlsx` | Checklist seed (~543 items × 3 ship types × 10 locations) — D-AUDRS-020 |
| SQE F 606 Office Internal Audit Checklist | `SSQE Annex 1-Forms/SQE F 606 Office Internal Audit Checklist -.xls` | Checklist seed (~80+ items per dept) — D-AUDRS-020 |
| SQE S 625 Non Conformity Form | `SSQE Annex 1-Forms/SQE S 625 Non Conformity.doc` | NC form field source — D-AUDRS-018, D-AUDRS-025 |
| SQE S 626 Overview of SSEQ Management | `SSQE Annex 1-Forms/SQE S 626 Overview of SSEQ Management.xls` | Monthly KPI export source — D-AUDRS-026 |
| SQE F 607 Vessel Inspection Report | `SSQE Annex 1-Forms/SQE F 607 Vessel Inspection Report.XLS` | **Superintendent Visit** — out-of-scope v1, v1.1 candidate as 5th inspection_type |
| **KSM-F-NC-001 NC Closure Form** | `Audit Reports/KSM-F-NC-001_NC_Closure_Form.docx` | **NC closure PDF template** Rev 01 Jan-2026 — drives D-AUDRS-040..048. **Replaces SQE S 625 for audit NCs.** 7 parts, 2 pages. |
| **KSM-F-OBS-001 Observation Closure Form** | `Audit Reports/KSM-F-OBS-001_Observation_Closure_Form.docx` | **Observation closure PDF template** Rev 01 Jan-2026 — drives D-AUDRS-040..048. 4 parts, 1 page. |
| Sample Internal Audit reports (3 vessels) | `Audit Reports/Chalisa Internal Audit/`, `East Ayutthaya Internal Audit- 28.Nov 2025-30.11 Dec 2025/`, `Internal audit report August 2025/` | Live audit-output examples — sample data for validation in Round 1+ |

---

## 11. Cross-Module Dependencies

**Rewritten at SSOT merge 2026-05-19 per D-AUDRS-287.** Reflects ALL integrations locked across v1.0 + v1.1 interrogation cycles. Build-team posture: every cross-module call in DocSuite DATA_MODEL.md / APP_FLOW.md MUST trace to one of the 8 ACTIVE integrations below. Anything not listed = rejected at code review.

### 11.1 ACTIVE integrations (8)

| # | Sibling Module / System | Direction | Mechanism | Source Decision |
|---|--------------------------|-----------|-----------|-----------------|
| 1 | **Inspection (PSC) — CAR engine** | Audit ↔ PSC | Same physical module + shared state machine. Audit reuses `psc_corrective_action` + `psc_deficiency` + `psc_audit_log` unchanged. Hard namespace separation per D-070 (only `/inspections/new` registration entry + CAR engine state machine are shared). | D-001 / D-070 |
| 2 | **PSC Inspection registration root** | Audit → PSC | `psc_inspection` root row owned by audit_detail (1:1). Additional internal audits triggered by PSC inspections write back-reference annotation on linked PSC inspection ("Additional internal audit raised — see AUD-YYYY-NNNN"). External audits set `audit_classification=EXTERNAL` on existing enum. | D-070 / D-122 / D-123 / D-200 |
| 3 | **Circular module** | Audit → Circular | Fleet-wide NC → Circular cross-module link via `audit_finding.linked_circular_id` FK to `msc_data.id`. From NC closure, Master or DPA can click "Issue Circular" which opens pre-filled Circular module entry. Gate AUDIT_P_007. No automatic fleet cascade; manual decision per audit. | D-065 |
| 4 | **Safety Module — incident linkage** | Audit ← Safety | Additional internal audit can be triggered by Safety incident via polymorphic `audit_plan.trigger_event_type=INCIDENT_REPORT` + `trigger_event_ref` = FK to safety incident_id. Cross-module link per D-065 pattern. INCIDENT_FOLLOWUP trigger reason per D-122 enum extension. | D-122 |
| 5 | **CMS — vessel local time (WRH)** | Audit ← CMS | Service contract: `CmsWrhClient.getVesselLocalTime(vessel_id, datetime_utc)` returns vessel local time + UTC offset valid at that instant. Used for vessel-side display TZ + frozen onto PDF Master signature blocks. Office display TZ = ITC; storage = UTC. NC closure SLA clocks computed at ITC (office TZ). | D-249 (Q52) |
| 6 | **CMS — live crew list** | Audit ← CMS | Service contract: `CmsCrewClient.getActiveCrewByRank(vessel_id, rank, datetime_utc)` returns user_id currently mustered to that rank at that instant. Same integration family as PSC inspection. Used for rank-bound NC signatures (D-250) — Master / Chief Officer / Chief Engineer / Safety Officer signatures all bind to rank, not person. | D-250 (Q53) |
| 7 | **CMS — vessel official email** | Audit ← CMS | Service contract: `CmsVesselClient.getOfficialEmail(vessel_id)` returns vessel's official mailbox. **No new column on VesselData** in VIMS (D-264 supersedes D-112 email-source portion). Read-through at notification dispatch time; 15-min cache. Failure mode (null/empty) → notification_delivery_log status=FAILED_PERMANENT with last_error='CMS_NO_EMAIL_ON_FILE', surfaces in D-262 DPA queue. **Add `GET /cms/vessels/{vessel_id}/official_email` API to CMS contract.** | D-264 (Q72 — SUPERSEDES D-112) |
| 8 | **HRM501 — vessel-side rank** | Audit ← HRM501 | Service contract: `Hrm501Client.getCurrentRank(user_id)` returns active rank at lookup time (vessel-side users only — Master / CO / CE / Safety Officer / ratings). Office-side users (DPA / FM / Marine Sup'tt / HoD / SEQ Manager) use VIMS `users.role` standard; no HRM501 lookup. `master_audit_qualified_auditor.auditor_scope` enum {VESSEL_SIDE, OFFICE_SIDE} picks right lookup at runtime. 15-min stale-while-revalidate cache. No rank mirror in VIMS. | D-280 (Q88) |

### 11.2 ACTIVE cross-module link with Certs Module (EXTERNAL audits only)

| Direction | Mechanism | Source Decision |
|-----------|-----------|-----------------|
| **Audit READS Certs** | anniversary · cadence · window_open · window_close · current cert validity (issue_date, expiry_date) via Certs API. NEVER recomputes window math — that's Certs module's job per D-CERT-063. Class Status Report sync (D-240/243) is the canonical anniversary source. | D-202 / D-240 / D-243 |
| **Audit WRITES Certs (outbox pattern)** | On external audit close-out: `last_done` = audit_date; `next_due` recomputed; on RENEWAL audits with `certificate_impact=CERT_VALID`, Certs module's cert `issue_date` + `expiry_date` refreshed atomically. Writeback queued in `cert_writeback_outbox` (D-234); background worker drains. Audit never blocks on Certs availability. CAS via cert version (D-236) prevents lost updates. | D-202 / D-205 / D-234 / D-236 |
| **Cert state changes triggered by audit** | NONE / CERT_VALID (renewal success refreshes validity) / RENEWAL_AT_RISK (sets at_risk flag) / SUSPENDED (sets is_suspended flag + suspension_reason FK + Flag-State notification per D-238) / WITHDRAWN (terminal soft-state). Internal audits cannot trigger any of these states (D-087 / D-205). | D-205 / D-238 |
| **Cross-module supersession** | D-202 SUPERSEDES D-CERT-025 for v1.1 external audits only. Internal Audit's existing relationship with Certs (none) remains unchanged. New `cert_change_log` table required in Certs module (D-239 — append-only, source_module attribution). Bidirectional SSOT cross-ref table at head of both Audit + Certs SSOTs per D-237. | D-202 / D-237 / D-239 / D-CERT-025 |

### 11.3 DEFERRED-TO-v2 integrations (3) — MANUAL FREE-TEXT REFERENCE ONLY at v1.0

Per D-AUDRS-287. Auditor enters context as free text in `audit_finding.description` / `audit_finding_nc.root_cause_summary`. NO FKs on audit tables. NO live API calls. Live integration deferred to v2+.

| # | Module | v1.0 posture | v2+ planned |
|---|--------|--------------|-------------|
| 9 | **PMS (Planned Maintenance)** | Manual reference only. Auditor enters PMS task ID / title / overdue context as free text. D-AUDRS-105's "PMS" scorecard area is a label only (not an integration). D-AUDRS-117's `PMS_OVERDUE` RCA template references PMS contextually, not via FK. | Live PMS API integration: `pms_task_id` FK on audit_finding; type-ahead lookup; overdue-task list pre-fetch. |
| 10 | **SMS Document Control** | Static derived constants only. "SMS Filing reference" tags (A-2 / A-9 / A-20 / A-28) on F 601 / F 602 / KSM-F-NC-001 PDFs rendered as constants at PDF generation time. NO lookup to SMS Doc Control. Auditor cites SMS document IDs as free text. | Live SMS Doc Control API: `sms_doc_id` FK with chapter/section/revision metadata; revision-tracking via cert_change_log-style pattern. |
| 11 | **Crew Training / Competency records** | Manual reference only. D-AUDRS-117's `TRAINING_GAP` RCA template doesn't FK to a training records system. Auditor enters crew member + rank + training gap as free text. | Live HRM training-records API: `training_record_id` FK; competency-matrix lookup; expiring-cert pre-fetch. |

### 11.4 NO LINKAGE (passive sibling modules)

| Sibling Module | Reason |
|----------------|--------|
| Reporting Module | Handles voyage / operational data, not audit findings. |
| Purchase Module | Indirect via CAR's downstream corrective actions (existing PSC behavior — CARs may produce Purchase Requisitions). No new linkage at v1.0. |
| ORB (Oil Record Book) | Rides same VIMS shell but operates on independent data. |

---

## 12. Tech Stack (Inherited)

No new technology stack. Inherits everything from `VIMS DOCS/TECH_STACK.md`:

- Backend: Python 3.12.4 · Django 5.2.7 · DRF 3.14.0 · SQL Server 2019 · JWT auth
- Frontend: React 18.3.1 · TypeScript 5.4.5 · Vite 5.4.0 · Tailwind 3.4.7 · TanStack Query 5.51.0 · Zustand 4.5.4 · shadcn/ui · Workbox 7.1.0 (PWA)
- DB: `ksm_inspection`, schema `dbo`, UUID PKs, soft delete, 4-column audit pattern

---

## 13. PDF Export Templates

**v1.0 generates 5 PDFs** per D-AUDRS-042/043/055 + D-AUDRS-026. The PSC template remains unchanged. RS templates deferred per D-AUDRS-033.

| Template | Used for | Source form | Layout | Stage |
|----------|----------|-------------|--------|-------|
| `audit_plan_pdf.py` (new) | **Audit plan** — shared with auditee before audit | **SQE F 601** | A4 portrait, 1 page. Audit performed at, dates, type, lead auditor, team, schedule blocks (DATE / FROM / TO / ACTIVITY), personnel present opening/closing | Pre-audit |
| `audit_report_pdf.py` (new) | **Audit report** — generated after audit closure | **SQE F 602** | A4 portrait. Audit metadata + 14-area scorecard + NC count + Obs count + equipment tested + audit summary + auditor & Master signatures | Post-audit |
| `audit_nc_pdf.py` (new) | **NC closure form** when `finding_type=NC` | **KSM-F-NC-001 Rev 01 Jan-2026** | A4 portrait, **2 pages**. 7 parts: A Auditor issuance · B Master immediate containment · C Master RCA (5-Why or equivalent) · D Master CA/PA + Evidence checklist · E DPA Effectiveness Review (30-90 days) · F DPA Closure Acceptance · G Auditor Verification & Final Closure | Per finding (NC type) |
| `audit_obs_pdf.py` (new) | **Observation closure form** when `finding_type=OBSERVATION` | **KSM-F-OBS-001 Rev 01 Jan-2026** | A4 portrait, **1 page**. 4 parts: A Auditor/Office issuance · B Master/HOD response (root cause + CA + evidence) · C DPA Office Review & Acceptance · D Auditor Verification & Closure Confirmation | Per finding (Observation type) |
| `s626_export.py` (new) | **Monthly KPI export** | **SQE S 626** | Multi-tab workbook | Monthly (on-demand v1, scheduled v1.1) |
| `psc_car_pdf.py` (existing) | PSC inspection CAR export | (existing) | unchanged | Existing PSC flow |
| `rs_car_pdf.py` (v1.2 deferred) | RS RISQ inspection CAR export | (deferred per D-AUDRS-033) | — | — |

Whole-audit export (`/inspections/.../cars/export-pdf/`) emits one PDF per finding, choosing template based on each finding's `finding_type` (NC vs Observation).

---

## 14. Sync Behavior (Inherited, No Change)

All new tables follow the same sync pattern as existing PSC tables:
- `client_id` (uniqueidentifier) for offline-generated IDs
- `sync_version` (int) for conflict detection
- Soft delete via `is_deleted` bit
- Standard audit columns (`created_by`, `created_date`, `updated_by`, `updated_date`)
- Participate in `psc_sync_log` / `psc_sync_log_detail` / `psc_sync_conflict` flow

Conflict resolution semantics inherit unchanged: `KEEP_SERVER` / `KEEP_VESSEL` / `REOPEN_FOR_MERGE`. Office/DPA only.

---

## 15. Migration Strategy

| Step | Action | Risk |
|------|--------|------|
| 1 | Create new tables (`audit_detail`, `audit_team_member`, `rs_detail`, `rs_observation`, `audit_finding`, masters). | Zero — additive only |
| 2 | Seed master_risq_chapter, master_risq_question (from user-supplied RISQ 3.0 doc), master_ism_clause, master_isps_clause, master_mlc_title. | Low — one-shot, idempotent script |
| 3 | Backfill: existing `psc_inspection` rows with `inspection_type IN ('RS','AUDIT')` that already exist in production. | Round 1 discovery: query DB for count; if non-zero, decide between (a) leave as-is with NULL extension rows, (b) office-side migration form to fill new fields. |
| 4 | Frontend deploy: type-branching forms, new components for finding entry, type-aware list filters. | Standard release. |
| 5 | Backend deploy: new endpoints under `/api/psc/inspections/` (audit-detail CRUD, rs-detail CRUD, finding CRUD per type). | Standard. |
| 6 | PDF templates deploy. | Low. |

No schema-breaking changes to existing tables. All new fields are in new tables.

---

## 16. Open Questions / Round 1 Plan

After Round 0 (15 user decisions) and Round 0.5 (17 SSQE-§10/Forms-driven decisions = D-AUDRS-016..032), the remaining open questions are noticeably fewer and more tactical. Most schema-shape, scope, and finding-model questions are now closed. Suggested grouping for Round 1:

### 16.1 Schema-Shape Final Tactical (D-AUDRS-033 to D-AUDRS-040)
- Polymorphic `clause_ref_id` strategy: single `(clause_master_type, clause_ref_id)` pair vs. separate FK columns per master. (Preferred: polymorphic pair, validated at app layer.)
- Should `psc_deficiency` gain a `finding_type` discriminator column for fast list-page filtering? (Likely yes.)
- Denormalization strategy for `audit_classification` + `finding_category` onto `psc_deficiency` for list-page perf.
- Should `audit_finding_signature` columns live on `audit_finding` directly (single-row) or as a separate signature table? (Inclined: separate table for clarity.)
- `master_charterer` v1 yes/no.
- `certificate_impact` enum values + v1.1 linkage strategy to Certificates module.
- Where do masters live: top-level `master_*` global tables, or under `master_psc_*` prefix matching existing convention?

### 16.2 Checklist-Walk UX (D-AUDRS-041 to D-AUDRS-045)
- Should the pre-flight checklist walk be a separate sub-screen, or inline on `/inspections/new`?
- Auditor's discretion to "amend / add / modify" checklist items per §10.4.4 — store per-audit overrides or only at master level?
- How are checklist items grouped on the UI? By location_code (F 605) vs. department vs. category?
- Offline behavior — preload entire checklist on vessel-side login?
- Bulk-mark "all compliant" then individually add findings — UX pattern?

### 16.3 Validation Rules (D-AUDRS-046 to D-AUDRS-055)
- Field-level validation: min/max lengths, regex on Q-number, date constraints.
- Submission gates for Audit: opening meeting, closing meeting, ≥1 attendee, 14-area scorecard fully filled, equipment-tested list, audit summary text — which are MANDATORY at SUBMIT vs. nice-to-have?
- Submission gates for RS: RISQ report PDF mandatory? Vetting outcome mandatory at submit or can come later?
- Master + Marine & HSSEQ Supt signatures on NC — block CAR submission until both signed? Or only display warnings?
- 90-day target — hard rule or soft warning? Extension reason min-length?
- Rework reason length parity (≥20 chars) — confirm.
- Root cause length parity (≥50 chars) — confirm.

### 16.4 Workflow Edge Cases (D-AUDRS-056 to D-AUDRS-065)
- What happens to an in-flight Audit CAR if the Audit inspection is deleted (soft delete)?
- Can Audit findings be added after inspection submission?
- Can `audit_standards` multi-select be changed after the first finding has been created? Mass re-validate clause refs?
- Office edit-assist boundaries for RS/Audit (anything different from PSC)?
- A finding cites multiple standards (e.g. an issue that breaches both ISM 7.1 and MLC Title 4) — supported via multiple clause_ref rows, or pick one primary?
- Interval extension via OPM F 713 — is that a VIMS workflow or external? (Likely external for v1; capture extension_form_ref text only.)

### 16.5 RBAC + Sidebar (D-AUDRS-066 to D-AUDRS-070)
- Final answer on new process gates `PSC_P_017` (RS workflow) / `PSC_P_018` (Audit workflow) vs. collapsing into existing gates.
- Should the sidebar split "Inspections" into PSC / RS / Audit tabs, or stay as one filtered list?
- Office user vessel-scope rules — do RS/Audit obey the same `master_RoleByVessel` filtering?
- Manning Agent audits and Security Provider audits — does `master_RoleByVessel` apply, or do we need a separate `master_RoleByOffice` lookup?

### 16.6 Masters Detail (D-AUDRS-071 to D-AUDRS-080)
- After user uploads RISQ 3.0 PDF/Excel: confirm CSV columns, mandatory_flag interpretation, answer-type values.
- F 605 seed extraction confirmation — produce CSV and review with user.
- F 606 seed extraction — confirm per-department split (crew/tech/...).
- ISM Code 2018 — clause depth (3-level vs. 4-level).
- ISPS Part A only or Part A + Part B (recommendations)?
- MLC — Regulation level or Standard A-code level?
- KSM SMS chapter master — pull live from existing VIMS tables or seed separately?
- Versioning: when RightShip publishes RISQ 3.1, how do we version? Snapshot table per version, or `version_id` column on each row?
- Should `audit_kind=OTHER` (now `audit_classification=OTHER` after D-AUDRS-016) still accept free-text clause? Yes per D-AUDRS-021.

### 16.7 Reporting, Dashboard & Monthly KPI Export (D-AUDRS-081 to D-AUDRS-085)
- Dashboard KPIs per type: PSC has Detention count. RS = NOT_ACCEPTED count + Major Discrepancy count? Audit = Major NC count + NC count?
- Excel export — same multi-sheet workbook for all types, or type-specific?
- SQE S 626 monthly export: confirm exact field mapping (D-AUDRS-026) — are all 28 columns derivable from VIMS data alone, or do some require manual entry (Master signs / Tech Supdt last visit etc.)?
- Auto-mail to HSSEQ@kaizenship.net at 7th of month — v1 manual, v1.1 scheduled.

### 16.8 PDF Templates (D-AUDRS-086 to D-AUDRS-090)
- RS PDF: include RISQ Q-text verbatim or just Q-number?
- Audit PDF: SQE F 602 mirror — include audit team signatures, opening/closing attendee names list, 14-area scorecard?
- NC PDF: SQE S 625 mirror — single-page-per-NC format, full signature chain?
- Watermarks / DRAFT badges.
- A4 portrait vs. landscape.

### 16.9 Sync / Offline (D-AUDRS-091 to D-AUDRS-093)
- Master cache size impact of seeding ~1,000 RISQ questions + ~670 checklist rows + ~150 clause rows. Confirm 150MB storage limit headroom.
- Offline finding entry — checklist walk with master cached.
- New conflict types — audit team / attendee list mutation conflicts.

### 16.10 Migration & Backfill (D-AUDRS-094 to D-AUDRS-098)
- Production query to count existing `inspection_type IN ('RS','AUDIT')` rows.
- Backfill policy for those rows.
- Communication plan for vessel masters who already have RS/Audit inspections in flight.
- KSM SMS manuals revision tracking — pull from existing PMS or new master?

### 16.11 Cross-Module / Audit / GDPR (D-AUDRS-099 to D-AUDRS-100)
- Cross-link rules to Safety module incidents (for `triggering_event_id` per D-AUDRS-024) — confirm same manual-cross-ref pattern as PSC ↔ Safety.
- PII handling for lead auditor name, audit team members, attendees, charterer name (commercially sensitive).

---

## 17. Versioning & Document Control

| Field | Value |
|-------|-------|
| Document | VIMS-AUDIT-RS-MODULE-SSOT.md |
| Version | **0.20 · 2026-05-18 PM session 5** — v1.0 frozen at v0.18 (D-001..123); v1.1 R-EXT.0 foundation (D-200..206) + R-EXT.1 Initial+Interim (D-207..209). **133 decisions total** (131 active, 2 superseded retained · D-056, D-100). External audit subtype enum extended from 8 → 16 values. D-087 activated by D-205; D-CERT-025 superseded for v1.1 by D-202. |
| Created | 2026-05-13 |
| Last Updated | 2026-05-18 PM (session 4) |
| Author | LLM (under user direction) |
| Approved By | **v1.0 (D-001..123) frozen 2026-05-18 PM session 3. v1.1 R-EXT.0 foundation (D-200..206) added 2026-05-18 PM session 4 — open for further v1.1 interrogation (R-EXT.1 onwards).** |
| Next Action | **KLOSS Step 2: DocSuite generation.** Produce 11-doc DocSuite (PRD, BACKEND_STRUCTURE, APP_FLOW, DATA_MODEL, RBAC, FIELD_MAP, etc.) + seed CSVs under `VIMS-Audit-Module/` folder following the [[project_vims_safety_module]] pattern. |
| Resume File | This file ▶ CURRENT START HERE → §0 Resume Guidance → §16 Open Questions (all addressed) |
| Latest Snapshot | 119 decisions (117 active + 2 superseded retained for audit trail · D-056, D-100) · 11-phase workflow · 3 branch flows · **13 audit-domain tables** (`audit_*` namespace + `master_hod_assignment` + `notification_delivery_log` + `master_slack_channel` + `master_rca_template`) · `audit_plan` simplified (no PIC columns, runtime-resolved on `audit_detail`) · ~1125 seed rows (added ~25 RCA templates) · **4 PDF outputs at v1.0** (F 601, F 602, KSM-F-NC-001, KSM-F-OBS-001 — S 626 deferred per D-099) · 1 cross-module link (Circular) · online-only · physical-signature-only · PSC/Audit hard namespace separation · **triple-channel notification fanout (in-system + email + Slack)** · **plain-language wizard + RCA templates + office-led drafting** for crew-side NC closure · 12 process gates (AUDIT_P_001..AUDIT_P_012) · all submit-gates/validation/edge-case rules locked · R1.H: scorecard N/A (D-105) + HoD-assignment (D-106) · R1.I: PSC-style open-pool PIC (D-107..110) · R1.J: notifications (D-111..115) · R1.K: NC closure UX (D-116..119) |

### 17.1 Revision History

| Version | Date | Decisions count | Summary |
|---------|------|------------------|---------|
| 0.1 | 2026-05-13 a.m. | 15 (R0) | Round 0 close-out from user interrogation. Architecture + scope locked. |
| 0.2 | 2026-05-13 p.m. | 32 (R0 + R0.5) | KSM SSQE Manual §10 fully ingested + Annex 1 Forms (F 601, F 602, F 604, F 605, F 606, S 625, S 626, F 607) analyzed. Multi-standard audit model, KSM-native NC enum, audit checklist masters, monthly KPI export, NC signature workflow, audit interval enforcement, audit plan register, trigger reasons, 14-area scorecard, named-attendee meeting table all added. |
| 0.3 | 2026-05-13 evening | 38 (R0 + R0.5 + phasing) | Build phasing locked: v1.0 = Internal Audit + RightShip; v1.1 = External Audit; v1.2 = Manning Agent + Security Provider audits (D-AUDRS-033). Clarified DPA = SEQ Manager at KSM per SSQE §1.2.2 (D-AUDRS-034) — no role split needed. Added qualified-auditor master, audit-level signature chain, auditor pre-audit dashboard, 2 new notification types (D-AUDRS-035..038). New §17.2 end-to-end Internal Audit workflow reference table (23 steps). |
| 0.4 | 2026-05-13 late | 48 (R0 + R0.5 + KSM-F-NC/OBS-001) | RightShip removed from v1.0 freeze (phasing corrected). Ingested KSM-F-NC-001 + KSM-F-OBS-001 Rev-01 Jan-2026 forms — these supersede older SQE S 625. Split finding model: `finding_type=NC` (full PSC cycle + DPA Effectiveness Review + Auditor Verification, 7-part KSM-F-NC-001 PDF) vs `finding_type=OBSERVATION` (terminal at Master_Closed, 4-part KSM-F-OBS-001 PDF). New tables `audit_finding_nc` + `audit_finding_obs`. Audit confirmed as office-initiated (D-AUDRS-039): assigned auditor logs in to prepare docs. Closure deadlines split: Minor NC 30d / Major NC 90d / Observation 30d. RCA Method enum + Root Cause Categories + Certificates-at-Risk fields added. |
| 0.5 | 2026-05-13 evening | 53 (R0 + R0.5 + R0.6 + R0.7) | **Audit window enforcement workflow** locked (D-AUDRS-049..053): window computation per vessel (last audit + 8 to 12 months), progressive alerts (T-90 / T-30 / T-0 / T+30 / T+60 / T+90), OPM F 713 extension request flow with DPA approval, Flag notification capture, certificate-at-risk consequences, status enum extended on `master_audit_plan`. Closes the gap user surfaced: "what if audit not carried out in window?" |
| 0.6 | 2026-05-13 night | 54 (+ D-054) | **Office Internal Audit added to v1.0 freeze** (D-AUDRS-054). v1.0 now covers both Vessel + Office Internal tracks per SSQE §10.3.3. F 606 checklist seed added to v1.0 master data. Same module, same forms, same closure flow — only delta is auditee_type=OFFICE_DEPT and the different checklist. |
| 0.7 | 2026-05-13 night | 55 (+ D-055) | F 601 PDF output added (D-AUDRS-055). **v1.0 PDF set finalised:** F 601 (audit plan, pre-audit) + F 602 (audit report, post-audit) + KSM-F-NC-001 (per NC) + KSM-F-OBS-001 (per Observation) + SQE S 626 (monthly KPI). |
| 0.8 | 2026-05-13 late night | 65 (+ D-056..065) | **Closes 8 lifecycle gaps** from completeness review. (056) Audit PIC = Supt (Marine/Tech). (057) Audit NC closure by Lead Auditor (not DPA) — state machine for audit findings: Master → Supt → Lead Auditor. (058) Lead Auditor ≠ PIC constraint; DPA can be Lead Auditor. (059) External audit closure cycle design noted for v1.1. (060) Pre-audit document upload area. (061) Physical signatures only at v1.0 — generate-print-sign-scan workflow. (062) Audit module is ONLINE-ONLY at v1.0 (departs from PSC offline-first). (063) Conductor vs Lead Auditor of record — two distinct fields on audit; conductor locked once audit commences, lead auditor editable until closure. (064) Audit cancellation by DPA with reason + next_planned_date. (065) Fleet-wide NC → Circular cross-module link (FK to msc_data). |
| 0.9 | 2026-05-14 | 70 (+ D-066..070) | **Round 1 R1.A schema-tactical (5 of 6 closed).** (066) No `finding_type` discriminator on `psc_deficiency` — PSC/Audit tracking separated at UX/query layer per user direction. (067) Separate `audit_finding_signature` table (one row per signature event). (068) Polymorphic rule-reference pointer `(rule_book_type, rule_clause_id)` on `audit_finding`. (069) `master_charterer` deferred to v1.2 with RightShip. (070) **Hard namespace separation: PSC and Audit share only the registration entry point + CAR Engine; all other audit tables/masters get a clean `audit_*` / `master_audit_*` namespace.** Mass rename applied across §5 data model, §6 form branching, §17.2 workflow reference, §18 field map (12 child tables + audit-domain masters renamed; CAR engine + generic compliance rule books preserved). Remaining R1.A: cert_impact moved to R1.D. |
| 0.10 | 2026-05-14 | 82 (+ D-071..082) | **R1.B Validation Rules + R1.4 Workflow Edge Cases — all closed.** (071) Audit SUBMIT gates: opening meeting + closing meeting + 14-area scorecard + summary ≥100 chars + equipment-tested ≥1 — all hard-block. (072) Signature absence hard-blocks per-state CAR transitions on audit findings. (073) Overdue NC deadlines are soft (banner + escalation, no block) — keeps closure flowing. (074) Free-text minimum lengths mirror PSC (rework ≥20, RCA ≥50, extension ≥50, cancellation ≥50, eff-review ≥50). (075) All date-order constraints enforced (open ≤ close ≤ today, due ≥ inspection, extended > original, next_planned > today, expiry > qualification, eff-review ∈ [+30, +90]). (076) Upload constraints: PDF/JPG/JPEG/PNG/DOCX, 10 MB cap. (077) `clause_ref_text` free-text validation when rule_book=OTHER: min 5 / max 200 chars, no regex. (078) Lock `audit_classification` + `audit_standards` after first finding exists. (079) Audit soft-delete blocked if any CAR past ALLOTTED — must use CANCELLED. (080) No finding additions after audit SUBMITTED. (081) Office edit-assist on audit = same as PSC (consistent UX). (082) Effectiveness Review (KSM-F-NC-001 Part E) auto-scheduled at T+30 to T+90 with Lead-Auditor task + DPA escalation at T+90 if incomplete. |
| **0.21** | **2026-05-19 (Batch-merge close)** | **~211 D-IDs assigned · ~208 active** (+ D-210..287 v1.1 Batches 1A-1Q + Q-STD-1) | **🔒 v1.1 INTERROGATION CYCLE COMPLETE — 95/95 questions resolved.** Batches 1A (D-210..214 scope boundary + DOC per-flag + DOC_INTERIM addition) · 1B (D-215..219 ISPS_INITIAL + is_cycle_resetting + SLA 7d/30d + attachment versioning + alt evidence paths) · 1C (D-220..224 role-scoped registration + dedup + rework reuses PSC pattern + IACS auditor map + clause_subref) · 1D (D-225..229 OTHER bucket + audit_finding_clause junction + **Q18 REJECTED no dispute mechanism** + alt-evidence DPA attestation + decoupled external_closure_status) · 1E (D-230..234 **Q21 REJECTED no reopen** + **Q22 SUPERSEDES D-204 EffRev portion: tiered EffRev** + finding priority + type-ahead cert linkage + outbox pattern) · 1F (D-235..239 post-closure cert linkage + CAS on cert version + bidirectional SSOT xref + multi-gate cert suspension + cert_change_log) · 1G (D-240..244 **KEY: cert anniversary = Class Status Report sync NOT audit override** + ownership/flag = Certs concern + master_audit_window_rule + Class Status Report cadence + external auditor sign-off via PDF only) · 1H (D-245..247 master_external_auditor + minimal PII + **MAJOR SCOPE LOCK D-247 RightShip→v1.2 + Manning/Security→v1.3**) · 1I (D-248..252 audit_end_date + **D-249 dual-TZ ITC+CMS-WRH** + **D-250 rank-bound signatures via CMS-crew** + **D-251 REJECTED Lead Auditor reassignment = ops policy** + **D-252 REJECTED DPA-on-leave not real**) · 1J (D-253..256 DPA+FM Acting HoD auth + **🔑 D-254 KEY MODEL SHIFT offline-by-design vessel-visit + VESSEL_ACKNOWLEDGED state anchors NC SLA** + 30d Master sig backdate + cross-dept HoD for SEQ CoI) · 1K (D-257 only; **4 rejected NOT APPLICABLE** — CoI declarations not real, vessel-sale handover internal-only, GDPR erasure out of scope; 15y retention soft-delete only) · 1L (D-258..261 no OCR + **🔑 D-259 KEY UNBLOCK Flag State accepts wet-ink+scan-back; HARD BLOCKER removed from D-061** + external stamp in PDF scan + **🔑 D-261 QR/hash PDF replay-prevention OPTION A built**) · 1M (D-262..265; Q74 NOT APPLICABLE notification storm not real; DPA owns Failed Notifications widget; no opt-out for 7 audit types; **🔑 D-264 SUPERSEDES D-112 email-source: CMS API replaces VesselData column**; per-vessel Slack only) · 1N (D-266..271 mechanical re-grep ≥99% + seed _provenance.md + FIELD_MAP cell format + COVERAGE.md 11-doc formula + Certs canonical + **🔑 D-271 CROSS-CUTTING DB TABLE CREATION STANDARD: UNIQUEIDENTIFIER PK + NEWSEQUENTIALID() + `<parent>_id` FK; no INT IDENTITY for new**) · 1O (D-272..276 all "same as VIMS" — tenancy + residency + hosting + **🔑 D-274 Audit is NOT part of offline: software pure online; D-254 is process-only** + backup-from-PSC + auth-from-VIMS) · 1P (D-277..281 SMTP-from-VIMS + Slack-from-VIMS + cross-module version pins + **🔑 D-280 HRM501 vessel-side only + office=users.role + auditor_scope enum** + device matrix) · 1Q (D-282..287 English+CEFR-B1 + supersedes audit + ID convention 124-199 + **🔑 D-285 Prince=final freeze authority** + SSQE Manual Rev 01 Feb 2026 referenced + **🔑 D-287 3 deferred-to-v2 integrations: PMS/SMS-Doc/Training = manual reference; §11 rewritten at this merge**). §11 Cross-Module Dependencies REWRITTEN with 8 active integrations + 3 deferred-to-v2. D-112 marked PARTIALLY SUPERSEDED. §0.4 Reference Document Versions added. §0.5 ID Allocation Convention added. Backup saved as `VIMS-AUDIT-RS-MODULE-SSOT.v0.20.bak`. **Ready for KLOSS Step 2 DocSuite generation at `VIMS-Audit-Module/`.** |
| 0.20 | 2026-05-18 PM session 5 | 133 (+ D-207..209 v1.1 R-EXT.1) | **R-EXT.1 closed — Initial + Interim audit subtypes.** User direction: "what is missed is interim, initial audits." (207) `DOC_INITIAL · SMC_INITIAL · MLC_INITIAL · ISPS_INITIAL` enum values. Initial audits create the cert row in Certs module on close-out + set anniversary date for the first time. No alert ladder; DPA manages manually. (208) `DOC_INTERIM · SMC_INTERIM · MLC_INTERIM · ISPS_INTERIM` enum values. Alert ladder anchored on Interim cert expiry (read from Certs module's vessel_cert.expiry_date) not anniversary. T-90/T-60/T-30/T-0 ladder ending at Interim cert expiry. Close-out converts Interim cert to full cert. (209) Anniversary lifecycle codified: CREATE on Initial audits only; never UPDATE (permanent per D-CERT-074); LEAVE_UNCHANGED for all other subtypes. External audit subtype enum total: 16 values (was 8 in D-200). |
| 0.19 | 2026-05-18 PM session 4 | 130 (+ D-200..206 v1.1 R-EXT.0) | **R-EXT.0 v1.1 EXTERNAL AUDIT FOUNDATION opened.** Same-day continuation after v1.0 freeze (v0.18 sealed). User direction: "so with this we close internal audit and now can move to external audit, which is very simple, vessel registers external audit updates NC issued and closes them in the system. Same for observation. ... DOC Audit is for office side and SMC, MLC and ISPS for vessel side which happens in harmonized manner." Cross-references the Certs module SSOT (D-CERT-011/063/074/110/194/196/197) for anniversary data and external auditor access pattern. (200) New `EXTERNAL` value on audit_classification + `external_audit_subtypes_csv` enum (DOC_ANNUAL/RENEWAL · SMC_INTERMEDIATE/RENEWAL · MLC_INTERMEDIATE/RENEWAL · ISPS_INTERMEDIATE/RENEWAL) + post-facto registration (skip PLANNED→IN_PROGRESS, jump to SUBMITTED). (201) Auditor identity: reuse `vessel.class_society` enum from Certs module for `external_audit_org` + free-text lead auditor name/credential + mandatory external_audit_report_pdf attachment. (202) Cross-module link `linked_cert_ids_csv` on audit_detail; reads anniversary/cadence/window from Certs; writes back last_done + next_due + cert validity refresh on close-out. Harmonized SMC+MLC+ISPS as ONE audit_detail row with multi-cert CSV. **Supersedes D-CERT-025** for v1.1 external audits. (203) Anniversary alerts T-90 / T-0 / window_close / +30 / +90 ladder using Certs window math; triple-channel per D-111. (204) Findings entry by vessel/office staff based on external auditor's report; new `is_external` flag on audit_finding; same wizard + RCA library + office-drafting (D-116..118) work as for internal. Simplified closure: no internal Lead Auditor step; new terminal state `EXTERNAL_AUDITOR_CLOSED` requires Supt PIC review + external close-out letter attachment + DPA confirmation; no Effectiveness Review for external NCs. (205) **D-AUDRS-087 ACTIVATED** — certificate_impact enum (NONE/CERT_VALID/RENEWAL_AT_RISK/SUSPENDED/WITHDRAWN) mandatory at external audit close-out; writeback to Certs module triggers cert state changes. (206) New gates AUDIT_P_013 (register external audit + confirm closure) + AUDIT_P_014 (writeback to Certs); total process gates 14. |
| 0.18 | 2026-05-18 PM session 3 close | 123 (+ D-121..123) | **R1.M closed — Additional Internal Audit support.** Post-freeze unfreeze. User direction: "there are times when additional internal audit is required, may be flag or PSC asks for it or may be due to detention, so should have an option to activate additional internal audit for vessel with a reason to do so, but this shall not affect the audit window of the vessel and should be treated as additional." (121) New `is_additional` BIT flag + `additional_reason` ≥50 char on audit_plan; window-calc excludes is_additional=1 from cadence (D-049 unchanged for routine); DPA-only authority (matches D-064 pattern); no T-90/T-30 alert ladder (reactive not scheduled). (122) D-024 trigger reason enum extended with 5 new values (FLAG_REQUEST, PSC_FOLLOWUP, DETENTION_FOLLOWUP, INCIDENT_FOLLOWUP, MGMT_DIRECTIVE); polymorphic linkage via `trigger_event_type` enum + `trigger_event_ref` (FK to psc_inspection or safety incident for in-VIMS triggers; free text + mandatory attachment for external types). (123) F 601/F 602 PDFs get red "ADDITIONAL AUDIT — DPA AUTHORISED" banner; audit register shows ADDITIONAL badge + filter chip; KPI dashboard splits routine vs additional (cadence-compliance metric counts is_additional=0 only); AUDIT_SCHEDULED notification adds "ADDITIONAL" tag; cross-module back-reference annotated on linked PSC inspection. |
| 0.17 | 2026-05-18 PM end-of-session 2 | 120 (+ D-120) | **R1.L closed — adaptive 2-column desktop layout for NC + Observation wizards.** Same-day follow-up to R1.K. User direction: "what you showed is on the mobile app but the user will use in desktop will it be same?" Locked D-120: viewport ≥1024px renders wizard as 2-column screen (60% wizard content + 40% persistent context panel showing Part A finding, previously answered fields, progress, attachment thumbnails). Below 1024px = mobile-only flow from D-116. Observation gets same treatment at ≥1024px. Keyboard support added (Enter advances, Esc returns, Cmd+S saves). Single React component via Tailwind responsive classes — no separate code path. Mobile-first principle preserved (CLAUDE.md mandate); desktop is the enhancement. Extends D-116; office-led drafting (D-118) continues to use dense-form view. |
| 0.16 | 2026-05-18 PM end-of-session | 119 (+ D-111..119) | **R1.J + R1.K closed — multi-channel notifications + NC closure UX simplification.** Same-day continuation. User directions: (1) "Notification need to be sent to vessel email and also on system as that is an official record, we can also sync with Slack as we are doing for other features." (2) "For NC closure form used presently is very difficult for the crew members to fill as the quality of crew these days is not good we need to make it easier." **R1.J (D-111..115):** triple-channel notification dispatch (in-system source-of-truth + email + Slack via incoming webhook); vessel email = `VesselData.official_email`; new `notification_delivery_log` (7-year retention) + `master_slack_channel` tables; new gate `AUDIT_P_011`; 7 audit notification types covered. **R1.K (D-116..119):** plain-language wizard for KSM-F-NC-001 Parts B+C (mobile-first, single-question-per-screen, inline examples); new `master_rca_template` table seeded ~25 common scenarios at DocSuite Step 2; office-led drafting flow extends D-081 (Supt drafts → Master signs, both names on PDF); new gate `AUDIT_P_012`; photo-first capture deferred to v1.1. Audit-domain table count 10 → 13. Process gates 9 → 12. |
| 0.15 | 2026-05-18 PM | 110 (+ D-107..110, supersedes D-056 + D-100) | **R1.I closed — PIC model simplification (PSC pattern adoption).** Same-day follow-up to R1.H. User direction: "instead [of named PIC selection], can we not have same like PSC inspection open?" + "DPA will have to select the lead auditor rest as per PSC inspection" + "name should be picked from the ID which fills the PIC fields, also Lead Auditor cannot be PIC rule needs to be there." (107) PSC-style open-pool PIC for Audit — drop named PIC at plan time; any scoped office user with `AUDIT_P_004` can pick up the PIC review action; supersedes D-056 + D-100; drops `audit_plan.office_pic_user_id` + `audit_plan.assigned_pic_user_id` columns. (108) DPA selects Lead Auditor at audit_plan creation from `master_audit_qualified_auditor` filtered by standards + active + non-expired; modifies D-039 (was SEQ Manager creates+assigns). (109) F 601/F 602 PIC field runtime-resolved from first-actor user_id; stored in derived `audit_detail.pic_user_id_resolved`; F 601 reissued at DPA_CLOSED with resolved name. (110) Lead Auditor ≠ PIC enforced server-side at action time (HTTP 403); modifies D-058 enforcement-point from plan-time to action-time. |
| 0.14 | 2026-05-18 AM | 106 (+ D-105..106) | **R1.H closed — office scorecard handling + HoD-assignment master.** Resumed after 4-day gap; locked the two remaining R1 candidates flagged at 2026-05-14 EOD. (105) Single `master_audit_area` retained — office audits use N/A status on the ~6 vessel-only rows; no parallel master needed; SUBMIT gate D-071 treats N/A as satisfied. (106) New `master_hod_assignment` table (dept · user_id · is_acting · effective_from · effective_to) with history + acting-HoD support; resolver supersedes D-102's `users.role` lookup; new `AUDIT_P_010` gate extends D-083 family. KLOSS Step 1 (Requirements Interrogation) officially DONE. Spec frozen for KLOSS Step 2 DocSuite generation at `VIMS-Audit-Module/`. |
| 0.13 | 2026-05-14 | 104 (+ D-100..104) | **R1.G Office Internal Audit workflow gap closed.** Until now Office Internal Audit was in v1.0 scope (D-054) but its workflow specifics inherited implicitly from Vessel — user flagged the gap. (100) DPA selects PIC per office audit from any active office user — flexible vs Vessel's fixed OFFICE_SUPT pool. (101) Office audits bypass `master_RoleByVessel` filter (no vessel = filter inapplicable); visible to all office users with AUDIT_P_* read gate. (102) `AUDIT_SCHEDULED` for office targets HoD of audited dept + key staff + DPA + auditor team. (103) `certificates_at_risk` UI restricted to DOC + NONE for office NCs (SMC/ISSC/MLC_DMLC hidden — vessel-specific). (104) §17.3 Office Internal Audit end-to-end workflow reference to be added to SSOT (parallel to §17.2 Vessel workflow). |
| 0.12 | 2026-05-14 | 99 (+ D-099) | **Scope reduction · SQE S 626 deferred from v1.0.** D-AUDRS-099 supersedes D-026 (monthly KPI export removed), the S 626 portion of D-055 (v1.0 PDF set is now 4 PDFs — F 601, F 602, KSM-F-NC-001, KSM-F-OBS-001), and the landscape portion of D-095 (all v1.0 PDFs now A4 portrait). `monthly_kpi_pdf.py` generator removed from v1.0 build; HSSEQ auto-mail removed; `master_ksm_sms_chapter` simplified at v1.0. User direction: "Overview of SSEQ Management will not be a part at the moment." Reports HTML mockup also updated (4 reports). |
| 0.11 | 2026-05-14 | **98 (+ D-083..098)** — **ROUND 1 COMPLETE** | **R1.C RBAC + R1.D Master Data + R1.E PDF + R1.F Migration — all closed. Round 1 interrogation phase officially complete; ready for KLOSS Step 2 (DocSuite generation).** (083) New `AUDIT_P_*` process-gate family — 9 gates mapped to roles (SEQ Manager, Lead Auditor, Master, DPA). (084) Sidebar split into top-level PSC + Audit + RightShip modules (Audit sub-tabs Vessel Internal / Office Internal). (085) PIC pool = any OFFICE_SUPT user. (086) `master_RoleByVessel` applies to audit scoping same as PSC. (087) `audit_detail.certificate_impact` DEFERRED to v1.1 — KSM internal auditors have no suspend/withdraw authority. (088) `master_ism_clause` 3-level depth (X.Y.Z), ~80 rows. (089) `master_isps_clause` Part A only, ~25 rows. (090) `master_mlc_title` Regulation + Standard-A combined, ~30 rows. (091) `master_ksm_sms_chapter` manually seeded from SQE S 626 (13 chapters); future KSM-manuals module ships post-v1.0. (092) Generic compliance masters (SOLAS, STCW, MARPOL, COLREG) at Regulation/Rule level. (093) Rule-book versioning via `code_version` column on each row (new revision = new rows alongside). (094) `master_audit_qualified_auditor` = separate table FK to users with multi-row per user (ISM/ISPS/MLC qualifications can have different expiry dates). (095) PDF orientations match source forms (F 601/602/NC/OBS portrait, S 626 landscape). (096) DRAFT watermark on PDFs until terminal state. (097) Production migration = read-only legacy tagging on existing inspection_type=AUDIT/RS rows; no field-mapping backfill. (098) Master-data seed CSV generation at DocSuite Step 2. |

---

---

## 17.2 Vessel Internal Audit — End-to-End Workflow Reference (v1.0 build target)

Distilled from SSQE Manual §10 + Annex 1 forms. Each step cites the procedure clause and the form involved. This is the canonical workflow the v1.0 build delivers.

| # | Phase | Step | Who | Source clause | Form | VIMS surface |
|---|-------|------|-----|---------------|------|--------------|
| 1 | Planning | SEQ Manager (=DPA) maintains Audit Schedule register; sets up 12-month plan honouring 8–12 month interval rule (D-AUDRS-022) | SEQ Manager | §10.3.2, §10.3.4 | F 601 Plan register | `/inspections/audit-plan` (new) + `master_audit_plan` |
| 2 | Planning | Schedule audit for target vessel; harmonised ISM+ISPS+MLC+EMS by default | SEQ Manager | §10.2.1 | F 601 | audit_classification=INTERNAL, audit_standards=multi |
| 3 | Planning | Assign qualified auditor from `master_qualified_auditor` (D-AUDRS-035) | SEQ Manager | §10.4.1 | — | new master + assignment screen |
| 4 | Planning | Notify auditee — Master + HoDs receive `AUDIT_SCHEDULED` notification (D-AUDRS-038) | System | §10.4.1 | — | `psc_notification` |
| 5 | Pre-audit | Auditor reviews: policies, procedures, plans, previous-audit findings, outstanding NCs | Auditor | §10.4.3 | — | Auditor dashboard widget (D-AUDRS-037) |
| 6 | Pre-audit | Auditor prepares checklist — picks from F 604/605/606 master, may amend/add | Auditor | §10.4.4 | F 604/605/606 | Checklist walk on `/inspections/new` with edit-per-audit overlay |
| 7 | Opening | Opening Meeting — Master + ALL Departmental Heads mandatory | Auditor | §10.5.2 | F 601 Personnel Present | `audit_meeting_attendee` opening_present=1 |
| 8 | Opening | Auditor presents purpose, scope, time-blocked schedule | Auditor | §10.5.1 | F 601 Audit Plan blocks | `audit_schedule_block` (Round 1) |
| 9 | Execution | Interviews conducted at workplace using checklist as guide | Auditor | §10.5.3 | — | Checklist walk UI |
| 10 | Execution | **Objective evidence recorded for every NC/Observation** | Auditor | §10.5.4 | — | `audit_finding.objective_evidence` mandatory at submit |
| 11 | Execution | Auditor may deviate from checklist for emergent issues | Auditor | §10.5.4 | — | "Add finding without checklist link" |
| 12 | Review | Auditor reviews findings with auditee at audit end | Auditor + auditees | §10.5.5 | F 602 draft | Pre-closing review screen |
| 13 | Review | Auditor + auditee plan corrective actions; agree NC + time-frame (≤90 days) | Auditor + auditee | §10.5.6 | F 602 Due Date | `audit_finding.original_due_date`, CAR `psc_corrective_action` rows |
| 14 | Closing | Closing Meeting — NCs explained, **auditees acknowledge + sign** F 602 | Auditor + auditees | §10.5.7 | F 602 acknowledgment | `audit_signature` (D-AUDRS-036) master_sign_at |
| 15 | Closing | Record proposed close-out date in consultation with auditee | Auditor + auditee | §10.5.7 | F 602 | confirmed `original_due_date` |
| 16 | Post-audit | Auditor submits F 602 within 2 weeks | Auditor → SEQ Manager | §10.6.1 | F 602 | audit `status=SUBMITTED` |
| 17 | Post-audit | SEQ Manager records NCs in VIMS for follow-up (already automatic via CAR auto-create trigger) | SEQ Manager | §10.6.1 | — | CARs auto-created when findings inserted |
| 18 | NC closure | Auditee corrects NC within agreed time; submits CAR + evidence in VIMS | Master / HoD / Crew | §10.6.3 | S 625 or VIMS | Existing CAR engine: ALLOTTED → IN_PROGRESS → ... → SUBMITTED_TO_DPA |
| 19 | NC closure | Observation closed via auditor-satisfaction (Excel + evidence) | Master | §10.7.4 | — | Same CAR engine (per D-AUDRS-032) |
| 20 | NC closure | SEQ Manager (DPA) signs F 602 to close audit | SEQ Manager | §10.6.3 | F 602 | audit `status=DPA_CLOSED`; individual CARs already CLOSED |
| 21 | Reporting | Master e-mails monthly SQE S 626 KPI snapshot to HSSEQ@kaizenship.net by 7th | Master | §10.6.4 | S 626 | On-demand export (D-AUDRS-026); v1.1 scheduled |
| 22 | Overdue | If not closed in time, SEQ Manager consults auditee, may extend | SEQ Manager | §10.6.5 | — | `audit_finding.extended_due_date` + reason |
| 23 | Mgmt review | Annual audit outcomes feed Management Review Meeting | All Managers | §10.11.4 | — | Out of this module (Reports module) |

---

## 17.3 Office Internal Audit — End-to-End Workflow Reference (v1.0 build target)

Parallel to §17.2. Same registration form (`/inspections/new`), same CAR engine, same NC/Obs closure forms (KSM-F-NC-001 / KSM-F-OBS-001), same Lead-Auditor closure path (D-AUDRS-057). Deltas highlighted in **bold** where Office differs from Vessel.

| # | Phase | Step | Who | Source clause | Form | VIMS surface |
|---|-------|------|-----|---------------|------|--------------|
| 1 | Planning | SEQ Manager maintains Audit Schedule register; office cadence = **9–15 month** spread between successive audits per department | SEQ Manager | §10.3.3 | F 601 Plan register | `/inspections/audit-plan` + `master_audit_plan` (auditee_type=OFFICE_DEPT) |
| 2 | Planning | Schedule audit for target department; harmonised ISM + ISPS where applicable; **Manning Agent / Security Provider audits deferred to v1.3** per D-AUDRS-033 | SEQ Manager | §10.3.3 | F 601 | `auditee_office_dept` ∈ {CREW, TECH, PURCHASE, IT, MARINE, OTHER} per D-AUDRS-017 |
| 3 | Planning | Assign qualified auditor from `master_audit_qualified_auditor` (D-AUDRS-035/094) — same pool as vessel audits | SEQ Manager | §10.4.1 | — | qualified-auditor dropdown filtered by audit_standards |
| 3a | Planning | **DPA selects PIC for this audit from any active office user** (HoD of peer dept / Supt / SEQ team) per D-AUDRS-100; locked at IN_PROGRESS | DPA | — | — | `audit_plan.office_pic_user_id` dropdown |
| 4 | Planning | Notify auditee — **HoD of audited dept + named key staff + DPA + assigned auditor team** receive `AUDIT_SCHEDULED` (D-AUDRS-102) | System | §10.4.1 | — | `psc_notification` routing branches on auditee_type |
| 5 | Pre-audit | Auditor reviews dept's procedures, prior audit findings, outstanding NCs, applicable KSM-SMS chapters | Auditor | §10.4.3 | — | Auditor dashboard widget · D-AUDRS-037 |
| 6 | Pre-audit | Auditor prepares checklist from **F 606 office** or **F 604 manning** master, may amend/add per §10.4.4 | Auditor | §10.4.4 | F 606 / F 604 | Checklist walk with edit-per-audit overlay |
| 7 | Opening | Opening Meeting — **HoD of audited dept + key staff** (not Master + HoDs) | Auditor | §10.5.2 | F 601 Personnel Present | `audit_meeting_attendee` opening_present=1 |
| 8 | Opening | Auditor presents purpose, scope, time-blocked schedule | Auditor | §10.5.1 | F 601 Audit Plan blocks | `audit_schedule_block` (Round 1) |
| 9 | Execution | Interviews conducted **at the office workplace** using checklist as guide; no shipboard tour | Auditor | §10.5.3 | — | Checklist walk UI |
| 10 | Execution | Objective evidence recorded for every NC/Observation | Auditor | §10.5.4 | — | `audit_finding.objective_evidence` mandatory at submit |
| 11 | Execution | Auditor may deviate from checklist for emergent issues | Auditor | §10.5.4 | — | "Add finding without checklist link" |
| 12 | Review | Auditor reviews findings with HoD + key staff at audit end | Auditor + auditees | §10.5.5 | F 602 draft | Pre-closing review screen |
| 13 | Review | Auditor + auditee plan corrective actions; agree NC + time-frame (≤90 days) | Auditor + auditee | §10.5.6 | F 602 Due Date | `audit_finding.original_due_date`, CAR rows |
| 14 | Closing | Closing Meeting — NCs explained, **HoD + key staff acknowledge + sign** F 602 | Auditor + auditees | §10.5.7 | F 602 acknowledgment | `audit_signature` (D-AUDRS-036) |
| 15 | Closing | Record proposed close-out date in consultation with auditee | Auditor + auditee | §10.5.7 | F 602 | confirmed `original_due_date` |
| 16 | Post-audit | Auditor submits F 602 within 2 weeks | Auditor → SEQ Manager | §10.6.1 | F 602 | audit `status=SUBMITTED` |
| 17 | Post-audit | SEQ Manager records NCs in VIMS (already automatic via CAR auto-create trigger) | SEQ Manager | §10.6.1 | — | CARs auto-created |
| 18 | NC closure | Auditee corrects NC within agreed time; submits CAR + evidence in VIMS. **Master/Responsible Officer in form = HoD of audited dept signing Part B/C/D** per KSM-F-NC-001 template wording | HoD / key staff | §10.6.3 | KSM-F-NC-001 | Existing CAR engine: ALLOTTED → ... → LEAD_AUDITOR_CLOSED |
| 18a | NC closure | **PIC review = DPA-selected office user** (per D-AUDRS-100) — not fixed to OFFICE_SUPT | Selected PIC | — | — | `psc_corrective_action.car_status = PIC_REVIEW` |
| 19 | NC closure | Observation closed via auditor-satisfaction (Excel + evidence) per D-AUDRS-032/040 | HoD | §10.7.4 | KSM-F-OBS-001 | Terminal at MASTER_CLOSED (state name retained; semantically HoD_CLOSED) |
| 20 | NC closure | SEQ Manager (DPA) signs F 602 to close audit | SEQ Manager | §10.6.3 | F 602 | audit `status=DPA_CLOSED` |
| 21 | Cert impact | **`certificates_at_risk` UI restricted to DOC and NONE** (SMC/ISSC/MLC_DMLC hidden — vessel-only certs) per D-AUDRS-103 | Auditor | — | KSM-F-NC-001 §A | conditional UI render based on auditee_type |
| 22 | Visibility | All office users with AUDIT_P_* read gates see this audit; **`master_RoleByVessel` does NOT apply** to office audits per D-AUDRS-101 | All office users | — | — | query layer skips vessel-scope JOIN |
| 23 | Overdue | If not closed in time, SEQ Manager consults auditee, may extend via OPM F 713 | SEQ Manager | §10.6.5 | OPM F 713 | `audit_finding.extended_due_date` + reason |
| 24 | Mgmt review | Annual office-audit outcomes feed Management Review Meeting | All Managers | §10.11.4 | — | Out of this module (Reports module) |

**Triggers applicable to office audits** (per D-AUDRS-024 enum minus inapplicable values):
`SCHEDULED` ✓ · `TAKEOVER_3MONTH` ✗ (no vessel takeover semantics) · `UNSCHEDULED_INCIDENT` ✓ · `UNSCHEDULED_NEAR_MISS` ✓ · `UNSCHEDULED_QUALITY_REVIEW` ✓ · `UNSCHEDULED_COMPLAINT` ✓ · `UNSCHEDULED_ROUTINE` ✓.

**Form-template wording note (per source KSM-F-NC-001 / KSM-F-OBS-001 Rev-01 Jan-2026):** the closure forms use "Master / Responsible Officer" and "Master / HoD" language by design — they were authored to accommodate both vessel and office contexts without separate templates. v1.0 PDF generators (`audit_nc_pdf.py`, `audit_obs_pdf.py`) render whichever label is appropriate based on `auditee_type`.

---

## 18. KSM Form → VIMS Field Map

This section satisfies the [[feedback_field_map_requirement]] memory directive: every DocSuite ships with a FIELD_MAP tracing source paper-form fields → VIMS DB tables/columns → API contracts → UI components. For the Audit & RS extension, the canonical source forms are the KSM Annex 1 forms; this is the v0.2 starter — the full Round-1 spec will produce a stand-alone `FIELD_MAP.md` in the eventual DocSuite folder.

### 18.1 SQE F 601 (Audit Plan) → VIMS
| F 601 field | VIMS table.column | Form widget |
|-------------|-------------------|-------------|
| AUDIT PERFORMED AT | `psc_inspection.port_place` (or `audit_detail.audit_location` for office audits) | text + city autocomplete |
| LOCATION | `psc_inspection.country` (vessel) / office name (office audit) | text |
| AUDIT DATES (From / To) | `psc_inspection.inspection_date` + `audit_detail.opening_meeting_at` / `closing_meeting_at` | date range |
| TYPE OF AUDIT (e.g. "INTERNAL ISM, MLC, ISPS AND EMS AUDIT") | `audit_detail.audit_classification` + `audit_standards[*].standard_code` | classification radio + standards multi-check |
| NAME OF LEAD AUDITOR | `audit_detail.lead_auditor_name` | text |
| DESIGNATION | `audit_detail.lead_auditor_designation` | text |
| NAME OF OTHER AUDITOR(S) | `audit_team_member[*].member_name` | repeatable list |
| AUDIT PLAN (Date / From / To / Activity-Function) | NEW table `audit_schedule_block[*]` (Round 1 confirm) | repeatable rows |
| PERSONNEL PRESENT (Name / Rank / Opening / Closing) | `audit_meeting_attendee[*]` | repeatable rows with two checkboxes |
| REMARKS | `audit_detail.audit_summary` (or separate `remarks` field — R1) | textarea |
| SMS Filing reference | derived; constant `A-2` | hidden |
| SIGNATURE OF LEAD AUDITOR | `audit_finding_signature.issued_by_*` on aggregate; audit-level sign on `psc_inspection.created_by` + signature attachment | signature widget |

### 18.2 SQE F 602 (Internal Audit Report) → VIMS
| F 602 field | VIMS table.column |
|-------------|-------------------|
| Vessel or Department Name | `psc_inspection.vessel_id` or `audit_detail.auditee_office_dept` |
| Location/Port | `psc_inspection.port_place` |
| Terms of Reference | `audit_detail.terms_of_reference` |
| Master or Head of Dept | derived (vessel Master via `VesselData` join, or HoD via department) |
| Auditor(s) | `audit_detail.lead_auditor_name` + `audit_team_member[*]` |
| Date(s) | `psc_inspection.inspection_date` |
| Audit Objectives/Scope | `audit_detail.audit_scope` |
| Corrective Actions from previous Internal Audit verified (Y/N) | `audit_detail.prev_internal_ca_verified` |
| Corrective Actions from previous External Audit verified (Y/N/NA) | `audit_detail.prev_external_ca_verified` |
| Non-Conformities Raised (count) | derived: count of `psc_deficiency` joined to this inspection where category IN (`MAJOR_NC`,`NC`) |
| Observations Raised (count) | derived: count where category=`OBSERVATION` |
| Summary of Audit | `audit_detail.audit_summary` |
| Opening Meeting (From/To/Remarks/List those present) | `audit_detail.opening_meeting_at` + `audit_meeting_attendee[*]` where `opening_present=1` |
| Tour of the Vessel/Office | (R1: capture as schedule block) |
| Closing Meeting (...) | `audit_detail.closing_meeting_at` + attendee list closing_present=1 |
| Inspection Summary 14-area scorecard | `audit_area_summary[*]` |
| Equipment tested successfully | `audit_detail.equipment_tested` |
| Audit Result table (S.No / Category / NC-Obs / Reference / Due Date 90d max) | `psc_deficiency` joined `audit_finding` (one row per finding) |
| Auditor sign | `audit_finding_signature.issued_by_*` |
| Master sign | `audit_finding_signature.master_sign_*` |

### 18.3 SQE F 605 (Vessel Internal Audit Checklist) → VIMS seed
F 605 sheet "Page 2" rows → `master_audit_checklist_item` rows.
| F 605 column | master_audit_checklist_item column |
|--------------|-------------------------------------|
| L. Code | `location_code` |
| Code | `item_code` |
| Check (mark column) | (UI state — not stored in master) |
| Questions | `question` |
| Guideline | `guideline` |
| Related Regulations | `regulation_ref` |
| Reference | `ksm_sms_ref` |
Plus `ship_type` derived from F 605 "Page 1" S Code (10/80/90 → Common / Bulk Carriers / Others).

### 18.4 SQE F 606 (Office Internal Audit Checklist) → VIMS seed
F 606 has multiple sheets per department. Each sheet → checklist scoped by `auditee_type=OFFICE_DEPT` + `auditee_office_dept`.
| F 606 column | master_audit_checklist_item column |
|--------------|-------------------------------------|
| Row no | `sequence_no` |
| Question text | `question` |
| SMS Manual + SMS Chapter + SMS Section | composed → `ksm_sms_ref` |
| Other Ref | `regulation_ref` |

### 18.5 SQE F 604 (Manning Office Audit Checklist) → VIMS seed
46 rows → `master_audit_checklist_item` scoped by `auditee_type=MANNING_AGENT`.
| F 604 column | master_audit_checklist_item column |
|--------------|-------------------------------------|
| Row no | `sequence_no` |
| Question | `question` |
| HRM ref | `ksm_sms_ref` (HRM chapter) |
| Other Ref | `regulation_ref` |

### 18.6 SQE S 625 (Non Conformity) → VIMS
| S 625 field | VIMS table.column |
|-------------|-------------------|
| Non conformity control no. | `psc_car.car_number` (auto-generated) |
| Vessel or Organizational Unit | `psc_inspection.vessel_id` or office dept |
| Date | `audit_finding_signature.issued_at` |
| Report Category (Major NC / NC / Observation / Improvement Proposal) | `audit_finding.finding_category` |
| Non-Conformance Note / Observation | `psc_deficiency.description` |
| Reference | `audit_finding.clause_ref_text` (denormalized) or via `clause_ref_id` lookup |
| Issued By (Rank / Name) | `audit_finding_signature.issued_by_rank` + `issued_by_name` |
| Master sign + date | `audit_finding_signature.master_sign_name` + `master_sign_at` |
| Due Date | `audit_finding.original_due_date` |
| Marine & HSSEQ Supt sign + date | `audit_finding_signature.marine_hsseq_supt_sign_name` + `marine_hsseq_supt_sign_at` |
| Identified Root Cause | `psc_car.root_cause_summary` |
| Immediate CA Taken / Required | computed from `psc_corrective_action` where `action_type=IMMEDIATE` |
| Long-Term CA Taken / Required | computed from `psc_corrective_action` where `action_type=LONG_TERM` |
| Office Notified of CA Completion — Date (Attach E-mail) | `audit_finding_signature.office_notified_at` + `office_notified_email_attach` |
| Office Confirmed Acceptance — Date (Attach E-mail) | `office_confirmed_at` + `office_confirmed_email_attach` |
| Closure Verified by (Name/Rank) | `closure_verified_by_name` + `closure_verified_by_rank` |
| Date | `closure_verified_at` |
| Sign | `closure_signature_path` |
| Filing reference (A-9) | derived constant |

### 18.7 SQE S 626 (Overview of SSEQ Management) → VIMS monthly export
This is a *generated report*, not an input form. The export pulls live VIMS data and produces the workbook. Field-by-field source map:
| S 626 cell / row | VIMS source |
|------------------|-------------|
| Ship Name | `VesselData.vesselName` |
| Name of Master | `HRM501` where rank=Master + active assignment via `Crew_Onboarding_History` |
| Month | report period parameter |
| LSA test dates block (lifeboat, rescue boat, emergency steering, generator, alarms, USCG D&A kits) | from PMS module (out-of-this-module — link only; manual entry fallback for v1) |
| Safety committee meeting last held | from Safety module SCM ledger (existing) |
| Master's review last conducted | (R1: capture in new Master's Review register OR pull from Safety module) |
| Office response on Master's review received | manual entry (v1) |
| Internal audit last conducted | `MAX(psc_inspection.inspection_date)` where `inspection_type=AUDIT` AND `audit_classification=INTERNAL` |
| NC Summary table (Number / Category / Title / Issued / Person Responsible / Due / Extended To / Completed / Closed) | `psc_car` + `psc_deficiency` + `audit_finding` + `audit_finding_signature` join — open NCs per vessel for month |
| PSC last conducted (Date / Place / No. of Deficiencies) | `psc_inspection` last record where `inspection_type=PSC` |
| "PSC entered as NC?" | derived: TRUE if matching CARs exist (always TRUE per D-AUDRS-032) |
| **Last RIGHTSHIP inspection conducted** (Date / Place / Deficiencies / Closed?) | `psc_inspection` last record where `inspection_type=RS` + `rs_detail` + open-CAR count |
| MLC weekly inspection / FW tank / alcohol / FW test | from Safety module + new entries |
| OLP training records / PMS export dates | from HRM + PMS module |
| Incidents during the month / Near miss count | from Safety module (existing) |
| SMS manuals status (Apex/HRM/SSQE/...) | from Document module (or new tracking table) |
| RA counts | from Safety module Risk Assessment register |
| Tech / Marine Supdt last visit | from Superintendent Visit register (v1.1 — until then, manual entry) |
| Master sign + Date | report metadata |
| E-mail target | constant `HSSEQ@kaizenship.net` |

### 18.8 SQE F 607 (Vessel Inspection Report) → out-of-scope v1
Tracked here for v1.1 planning only. Not mapped at v1.

### 18.9 KSM-F-NC-001 (NC Closure Form Rev 01 Jan-2026) → VIMS
| KSM-F-NC-001 field | VIMS table.column |
|--------------------|-------------------|
| NC Reference No. | `psc_car.car_number` (auto: NC-{vessel}-YYYY-NNN) |
| Date of Audit | `psc_inspection.inspection_date` |
| Vessel Name | `psc_inspection.vessel_id` join `VesselData.vesselName` |
| Port / Location | `psc_inspection.port_place` |
| Auditor Name & Organisation | `audit_detail.lead_auditor_name` + `lead_auditor_company` |
| Survey / Report Ref. | `audit_detail.report_reference` (R1 confirm) |
| Code / Regulation Reference | `audit_finding.clause_master_type` + `clause_ref_id` |
| KSM SMS / Procedure Ref. | `audit_finding.clause_ref_text` (when type=KSM_SMS) |
| Objective Evidence (Part A) | `audit_finding.objective_evidence` |
| NC Issued Date | `audit_finding_signature.issued_at` |
| Required Closure Deadline | `audit_finding.original_due_date` (Minor=30d, Major=90d per D-AUDRS-047) |
| Certificate at Risk (DOC/SMC/ISSC/MLC/None) | `audit_finding.certificates_at_risk` |
| NC Classification (Major/Minor) | `audit_finding.nc_category` |
| Part B Immediate Action text | `audit_finding_nc.immediate_action_text` |
| Part B Date Completed | `audit_finding_nc.immediate_action_completed_at` |
| Part B Master Sign | `audit_finding_nc.master_immediate_sign_name` + `master_immediate_sign_at` |
| Part C RCA Method | `audit_finding_nc.rca_method` |
| Part C 5-Why fields | `audit_finding_nc.problem_statement` + `why_1`..`why_5` |
| Part C Root Cause Categories | `audit_finding_nc.root_cause_categories` |
| Part C Root Cause Summary | `audit_finding_nc.root_cause_summary` |
| Part D Corrective Actions | `psc_corrective_action[*]` (existing) + `audit_finding_nc.corrective_action_text` summary |
| Part D Target / Actual Completion Date | `audit_finding_nc.target_completion_date` + `actual_completion_date` |
| Part D Preventive Action (fleet) | `audit_finding_nc.preventive_action_text` |
| Part D SMS Amendment required? | `audit_finding_nc.sms_amendment_required` + `sms_amendment_doc_ref` |
| Part D Evidence checklist (9 options) | `psc_evidence[*]` (existing, with evidence_type tags) |
| Part E Review Date | `audit_finding_nc.effectiveness_review_date` |
| Part E Method | `audit_finding_nc.effectiveness_review_method` |
| Part E Outcome | `audit_finding_nc.effectiveness_outcome` |
| Part E Further Action | `audit_finding_nc.effectiveness_further_action_text` |
| Part E DPA Sign | `audit_finding_nc.effectiveness_dpa_sign_name` + `effectiveness_dpa_sign_at` |
| Part F Reviewed By | `audit_finding_nc.dpa_acceptance_sign_name` |
| Part F Closure Decision | `audit_finding_nc.dpa_closure_decision` (ACCEPTED/RETURNED) |
| Part F Return Reason | `audit_finding_nc.dpa_return_reason` |
| Part F DPA Sign + Date | `audit_finding_nc.dpa_acceptance_sign_at` |
| Part G Verifying Auditor + Org | `audit_finding_nc.verifying_auditor_name` + `verifying_authority_org` |
| Part G Verification Method | `audit_finding_nc.verification_method` |
| Part G Certificate Endorsement | `audit_finding_nc.certificate_endorsement_type` + `certificate_endorsement_ref` |
| Part G Auditor Assessment | `audit_finding_nc.auditor_assessment_text` |
| Part G Final Closure Status | `audit_finding_nc.final_closure_status` (CLOSED/CONDITIONAL/NOT_CLOSED) |
| Part G Resubmit-by Date | `audit_finding_nc.resubmit_by_date` |
| Part G Auditor Sign | `audit_finding_nc.auditor_verification_sign_at` |

### 18.10 KSM-F-OBS-001 (Observation Closure Form Rev 01 Jan-2026) → VIMS
| KSM-F-OBS-001 field | VIMS table.column |
|---------------------|-------------------|
| Observation Ref. No. | `psc_car.car_number` (auto: OBS-{vessel}-YYYY-NNN) |
| Date of Audit · Vessel · Audit Type · Location | (same joins as NC form) |
| Auditor Name & Organisation | `audit_detail.lead_auditor_name` + `lead_auditor_company` |
| SMS / Regulatory Ref. | `audit_finding.clause_master_type` + `clause_ref_id` |
| Observation Category | `audit_finding.observation_category` (OBSERVATION / IMPROVEMENT_SUGGESTION / OFI) |
| Observation Description | `psc_deficiency.description` |
| Date Issued | `audit_finding_signature.issued_at` |
| Part B Responded By Name+Rank | `audit_finding_obs.responded_by_name` + `responded_by_rank` |
| Part B Target Closure Date | `audit_finding_obs.target_closure_date` |
| Part B Immediate Action | `audit_finding_obs.immediate_action_text` |
| Part B Root Cause | `audit_finding_obs.root_cause_text` |
| Part B Corrective Action | `audit_finding_obs.corrective_action_text` |
| Part B Preventive Action | `audit_finding_obs.preventive_action_text` |
| Part B SMS Amendment | `audit_finding_obs.sms_amendment_required` + `sms_amendment_doc_ref` |
| Part B Evidence checklist | `psc_evidence[*]` (existing) |
| Part B Actual Closure Date | `audit_finding_obs.actual_closure_date` |
| Part B Master Sign | `audit_finding_obs.master_sign_name` + `master_sign_at` ← **terminal state per D-AUDRS-040** |
| Part C Reviewed By + Date | `audit_finding_obs.dpa_acceptance_sign_name` + `dpa_review_date` |
| Part C Adequacy Assessment | `audit_finding_obs.dpa_adequacy_text` |
| Part C Closure Decision | `audit_finding_obs.dpa_closure_decision` |
| Part C Return Reason | `audit_finding_obs.dpa_return_reason` |
| Part C DPA Sign | `audit_finding_obs.dpa_acceptance_sign_at` |
| Part D Verifying Auditor + Org | `audit_finding_obs.verifying_auditor_name` + `verifying_authority_org` |
| Part D Verification Method | `audit_finding_obs.verification_method` |
| Part D Auditor Remarks | `audit_finding_obs.auditor_remarks_text` |
| Part D Closure Status | `audit_finding_obs.closure_status` |
| Part D Resubmit-by Date | `audit_finding_obs.resubmit_by_date` |
| Part D Auditor Sign + Date | `audit_finding_obs.auditor_verification_sign_at` |

---

## 19. KSM-Native Terminology Glossary

| KSM term | VIMS internal token | Where used |
|----------|---------------------|------------|
| Non-Conformity (NC) | `finding_category=NC` | KSM-wide for any deviation; v1 enum value |
| Major Non-Conformity | `finding_category=MAJOR_NC` | Severe deviation |
| Observation (audit) | `finding_category=OBSERVATION` | Sign that may lead to NC |
| Improvement Proposal / Suggestion | `finding_category=IMPROVEMENT_PROPOSAL` | KSM equivalent of "OFI" |
| Deficiency | PSC-only display label for `finding_category` mapped to PSC | PSC inspections (in spite of KSM treating it as NC per §10.8.4) |
| Observation (RightShip) | RS-only display label; underlying = NC/Observation in DB | RS inspections |
| Marine & HSSEQ Supt | role title; signature field `marine_hsseq_supt_sign_*` on NC | SQE S 625 |
| SEQ Manager | shore-side role responsible for audit closure + audit schedule | SSQE §10 throughout |
| SQE / SEQ / HSSEQ | KSM department names; equivalent to "Safety, Environment, Quality" | varies |
| SMS | Safety Management System (per ISM Code) | universal |
| SSQE | Safety, Security, Quality & Environmental | KSM's superset of SMS |
| SMS Filing reference (A-2 / A-9 / A-20 / A-28) | KSM physical-filing tag; preserved as field on PDF exports | All forms |
| ISM 6.2 / STCW II/1 / SOLAS III-19.4.1 | clause references — captured via `clause_master_type` + `clause_ref_id` | NC findings |
| OPM F 713 | KSM form for audit-extension DPA approval | D-AUDRS-022 |
| Auditee | the entity being audited (vessel / office dept / manning agent / security provider) | `auditee_type` field |
| Audit Plan | schedule register, distinct from Audit Plan-block-of-time within an audit | `master_audit_plan` (the register) |
| Audit Plan (per F 601) | the time-blocked agenda of activities during a single audit | `audit_schedule_block[*]` (Round 1) |

---

**End of Round 0.5 SSOT.** Version 0.2 — KSM SSQE Manual §10 + Annex 1 Forms fully ingested. 32 decisions locked. Ready for Round 1 (tactical schema, validation rules, dashboard, PDF templates).

---

## 20. SUPPLEMENTAL DECISION BAND — D-AUDRS-288..299 (v1.1 supplemental, append-only)

> **Appended 2026-07-14. The frozen v1.0 (§9, D-001..123) and v1.1 (D-200..287) bodies above are NOT edited** — per §0.5 / D-AUDRS-284, a locked decision changes only by explicit supersession with a new ID in the reserved band. This section is dated and append-only.
>
> **Origin:** Owner ruling (Prince, 2026-07-14) — "AUDIT FORK — RULED: no-legacy-DDL path (zero exceptions)". Rationale (owner): *"removes the contradiction rather than documenting an exception to it."*
>
> **Net effect:** the Audit module ships with an **EMPTY shared-table mutation exception list**. No `ALTER`/`DROP` on `psc_*`, `HRM501`, or `VesselData`. All Audit-specific legacy classification, lifecycle state, and provenance live in **Audit-owned tables**; every relationship to a legacy row is a **loose, application-validated reference** (no DB-level FK).

### 20.1 Live-DB verification performed before this band was banked (2026-07-14)

Queried the restored production snapshot `ksm_cms_live` (`ksm_marine_live_26_March_2026.bak`, Azure SQL Edge 15.0.2000, container `vims-mssql`), the same DB used for `PRESENT_STATE_VERIFICATION.md`:

| # | Query | Result |
|---|-------|--------|
| V-A | `SELECT cc.name, cc.definition FROM sys.check_constraints cc JOIN sys.tables t ON t.object_id=cc.parent_object_id WHERE t.name='psc_car'` | **0 rows — `psc_car` has NO CHECK constraint of any kind.** |
| V-B | `psc_car.status` column definition | `nvarchar(60) NOT NULL`, no CHECK, no default-bound enum. |
| V-C | CHECK constraints across ALL `psc_*` tables | Only 6, all non-negative-integer guards on `psc_opensource_import_run` / `psc_opensource_deficiency_record`. **None on any status column, none on any table Audit touches.** |
| V-D | `SELECT COUNT(*) FROM psc_inspection WHERE inspection_type IN ('AUDIT','RS')` | **0 rows** (total `psc_inspection` = 2, both `PSC`). Confirms the clean-cutover finding in `PRESENT_STATE_VERIFICATION.md`. |
| V-E | `psc_inspection.legacy` column exists? | **No** — and per D-AUDRS-288 it will never be created. |
| V-F | `psc_corrective_action.status` column exists? | **No** (18 columns; no `status`). Confirms PSV V-2 and retires the stale open item — see D-AUDRS-292. |
| V-G | Fingerprint baseline (cols/checks/indexes) for the 9 protected tables | `psc_inspection` 29/0/10 · `psc_car` 28/0/5 · `psc_deficiency` 27/0/12 · `psc_corrective_action` 18/0/6 · `psc_notification` 12/0/5 · `psc_activity_history` 10/0/5 · `psc_audit_log` 13/0/4 · `HRM501` 40/0/1 · `VesselData` 42/0/1. **All 9 carry zero CHECK constraints.** |

**CHECK-constraint verdict: `VERIFIED-none`** — established by live query, not inferred. D-AUDRS-294 nonetheless keeps a build-time assertion, because the snapshot is dated 2026-03-26 and production may drift.

### 20.2 Supplemental decisions

| # | ID | Decision | Source |
|---|----|----------|--------|
| 212 | **D-AUDRS-288** | **🔑 SUPERSEDES THE STORAGE MECHANISM OF D-AUDRS-097 (its substance is preserved verbatim).** **`psc_inspection.legacy` is NEVER created.** No `ALTER TABLE psc_inspection`. Legacy classification moves to the Audit-owned table **`audit_legacy_inspection_tag`** — `id uniqueidentifier PK DEFAULT NEWSEQUENTIALID()` (D-137 compliant), `psc_inspection_id char(32) NOT NULL` (**loose, application-validated reference — no DB FK**; the already-approved legacy-FK form per `MIGRATION.md §4`), `is_legacy bit NOT NULL DEFAULT 1`, `tagged_at datetimeoffset NOT NULL`, `tagged_by nvarchar(100) NOT NULL`, `tag_reason nvarchar(400) NULL`; unique index on `psc_inspection_id`. **D-097's SUBSTANCE IS UNCHANGED:** legacy rows are visible read-only in the Audit/RS lists with the **"Legacy — read only"** banner, cannot be edited, cannot take new findings, cannot transition state, and there is **NO field-mapping backfill**. Only the storage mechanism changes: a row in the Audit-owned tag table, joined at query time on the loose ref, replaces the boolean column on the shared table. Absence of a tag row = not legacy (no per-row write needed for the 0 existing rows). **This RESTORES fidelity to frozen SSOT §15 ("All new fields are in new tables")** — the drafted `legacy` column had violated it. | Owner ruling 2026-07-14 §6.0(2)(3) |
| 213 | **D-AUDRS-289** | **🔑 `psc_car.status` REQUIRES NO DDL — the widening migration is DELETED ENTIRELY.** Live verification (§20.1 V-A/V-B/V-C): `psc_car.status` is `nvarchar(60) NOT NULL` with **zero CHECK constraints**, so it already accepts the Audit-NC values at the storage layer. Adding `SUBMITTED_TO_LEAD_AUDITOR`, `LEAD_AUDITOR_CLOSED`, `OFFICE_DRAFTED`, `AWAITING_EXTERNAL_CLOSE_OUT`, `EXTERNAL_AUDITOR_CLOSED` is therefore a pure **application-layer `CARStatus` choices extension** — a Django `choices` change emits an `AlterField` operation that generates **NO SQL**. **The step-5 "widen" migration is removed from `MIGRATION.md §2`; no DDL replaces it.** D-AUDRS-132 (CAR state lives on `psc_car.status`) and D-003 (state machine unchanged) both still hold; D-057/D-118/D-204 terminal-state behavior is delivered unchanged. **Precedent:** RightShip **D-AUDRS-357** extends `psc_activity_history.entity_type` values under an explicit zero-ALTER/DROP regime — **a value-set extension is not a legacy-table mutation.** Because the CAR state remains on `psc_car.status`, **no Audit-owned CAR projection table is needed**; the ruling's projection fallback (§6.0(5)) is moot and is NOT built. | Owner ruling 2026-07-14 §6.0(1); live DB 2026-07-14 |
| 214 | **D-AUDRS-290** | **🔑 SCHEMA-FINGERPRINT PROBE — approved exception list is EMPTY.** A migration probe + build gate computes a fingerprint over `sys.columns` + `sys.check_constraints` + `sys.indexes` for the 9 protected tables (`psc_inspection`, `psc_car`, `psc_deficiency`, `psc_corrective_action`, `psc_notification`, `psc_activity_history`, `psc_audit_log`, `HRM501`, `VesselData`), captured **pre-migration and post-migration**. The two hashes **MUST be IDENTICAL**; **any diff FAILS the build** — never-waivable (owner brief §2.1(2), §6.0(4)). **`approved_exceptions[] = []` (EMPTY).** There is no module-specific exception and none may be added without a new owner ruling. **Gate-author design note (load-bearing):** the gate MUST assert on the **schema fingerprint**, NOT on the presence/absence of a Django migration operation — a `choices`-only change (D-289) legitimately emits an `AlterField` operation with **no SQL**, so a grep for `AlterField`/`ALTER` in migration files would **false-positive** and block a compliant build. Assert on the database, not on the migration text. Baseline values in §20.1 V-G. | Owner ruling 2026-07-14 §6.0(4) |
| 215 | **D-AUDRS-291** | **PRE-DEPLOY LEGACY-DISCOVERY PROBE (replaces the D-097 `UPDATE` script).** Pre-deploy, run `SELECT COUNT(*) FROM psc_inspection WHERE inspection_type IN ('AUDIT','RS')`. **Verified = 0 on the restored snapshot (§20.1 V-D) — clean cutover.** If the count is **0**, nothing is loaded and the tag table stays empty. If the count is **> 0** at real deploy time, **INSERT one `audit_legacy_inspection_tag` row per discovered `psc_inspection.id`** (`is_legacy=1`, `tagged_at=SYSDATETIMEOFFSET()`, `tagged_by='migration'`, `tag_reason='pre-deploy AUDIT/RS row'`). The loader is idempotent (guarded by the unique index on `psc_inspection_id`). **`psc_inspection` is NEVER updated** — the migration performs **zero writes of any kind** to any `psc_*` table. | Owner ruling 2026-07-14 §6.0(3); live DB 2026-07-14 |
| 216 | **D-AUDRS-292** | **RETIRES the stale open item at `MIGRATION.md §9`** — *"Confirm the `psc_corrective_action` status column is `varchar` (not a CHECK-constrained enum)…"* (attributed to D-057). The item was **mis-aimed**: `psc_corrective_action` **has no `status` column at all** (18 columns — live-verified §20.1 V-F; already proven by `PRESENT_STATE_VERIFICATION.md` V-2). The CAR state lives on **`psc_car.status`** (D-132), whose constraint question is now definitively answered by D-289 (`VERIFIED-none`). The open item is **CLOSED — nothing to confirm**, and is struck from `MIGRATION.md §9` with a dated supersession note. | Live DB 2026-07-14; PSV V-2 |
| 217 | **D-AUDRS-293** | **CORRECTS a stale claim in `DATA_MODEL.md §2`** (table-inventory row **L1**), which read `unchanged + `legacy`, `audit_classification` enum widened`. **Both halves are wrong:** the `legacy` column is never created (D-288), and **no `audit_classification` enum on `psc_inspection` is widened or exists** — the `audit_classification` discriminator lives on **`audit_detail`**, per `DATA_MODEL.md §3.1` and §4. The L1 row becomes **`unchanged (zero DDL)`**. `psc_inspection.inspection_type` already accepts `AUDIT` with no CHECK — no DDL there either. | Live DB 2026-07-14; DATA_MODEL §3.1 |
| 218 | **D-AUDRS-294** | **BUILD-TIME CHECK-CONSTRAINT ASSERTION (P0, fail-closed).** Although D-289 records `VERIFIED-none` from a **live query**, the evidence is a **2026-03-26 snapshot**, and production may have drifted. The migration therefore **asserts at build time** that `psc_car` carries **no CHECK constraint on `status`** (`SELECT COUNT(*) FROM sys.check_constraints cc JOIN sys.tables t ON t.object_id=cc.parent_object_id WHERE t.name='psc_car'` **MUST be 0**). **If a constraint IS found at build time the build FAILS and the owner is consulted — the migration MUST NOT self-authorize an `ALTER`.** State on failure: **`BLOCKED`** (owner brief §6.1 four-state machine: `RESOLVED` · `DEFERRED` · `BLOCKED` · `NOT_APPLICABLE_YET`). Rationale: a verified fact is still asserted, never assumed silently. | Owner ruling 2026-07-14 §6.0(5); coordinator normalization 2026-07-14 |

### 20.3 Band status

| Range | Used | Free |
|-------|------|------|
| D-AUDRS-288..299 | **288, 289, 290, 291, 292, 293, 294** (7 banked 2026-07-14) | 295..299 |

**Shared-table mutation exception list: `[]` (EMPTY).** Audit performs **zero** `ALTER`/`DROP`/`UPDATE` against `psc_*`, `HRM501`, or `VesselData`.

---

## 21. SUPPLEMENTAL DECISION BAND — D-AUDRS-295..299 (Domain 12 Personas + Domain 13 Quality Gates, v4 retrofit)

> **Appended 2026-07-14. The frozen v1.0 (§9, D-001..123) and v1.1 (D-200..287) bodies above are NOT edited** — per §0.5 / D-AUDRS-284, a locked decision changes only by explicit supersession with a new ID in the reserved band. This section is dated and append-only, and continues the band opened at §20 (D-AUDRS-288..294, the no-legacy-DDL fork).
>
> **Origin:** Owner brief *"VIMS v4 — Quality-Gate + Release-Protocol + Personas Retrofit"* (Prince, 2026-07-14) — §1 Personas · §2 Quality · §6.0 Audit fork ruling · §6.1 canonical state enum · §6.2 gate-state for not-yet-existent code.
>
> **Band note (⚠ for the owner):** these five decisions **exhaust** the reserved v1.1 supplemental band `D-AUDRS-288..299`. **Domain 14 (Release) has no free ID left in this band** — a fresh, explicitly-declared range must be authorized before any release decision can be banked for the Audit module.

### 21.1 Supplemental decisions

| # | ID | Decision | Source |
|---|----|----------|--------|
| 219 | **D-AUDRS-295** | **Domain 12 (Personas) — Audit persona set CONFIRMED, all 8 kept.** P1 "SEQ Manager / DPA" · P2 "Lead Auditor" · P3 "Conductor" · P4 "Office Supt / PIC" · P5 "Vessel Master" · P6 "Vessel Crew / Action Owner" · P7 "HoD (office)" · P8 "Fleet Manager" — labels and numbers reused **exactly** as the frozen `JOURNEY_MAP.md` already cites them in its `persona:` fields (verified block-by-block before banking: JOURNEY-1/9/10/11 → P1 · JOURNEY-2 → P3 · JOURNEY-3 → P3 → P5 · JOURNEY-4 → P6 · JOURNEY-5 → P5 · JOURNEY-6 → P4 · JOURNEY-7 → P2 · JOURNEY-8 → P5 with P6 · JOURNEY-12 → P1 with P5 · JOURNEY-13 → P7 with P1 · JOURNEY-14 → P8). The candidate drafts in `scratchpad/sdd/interrogation-battery.md` §A.1 (goal / context / tech_savviness / error_tendency / patience_budget / known_misbehaviors) are accepted **as-is** for all 8 personas per the owner brief §1 ("Drafted … accepted as-is"); the single open `[confirm ≥1 real misbehavior…]` placeholder on **P7 (HoD)** is resolved by dropping the placeholder residue and keeping the one concrete misbehavior the draft already lists — **no new fact is invented**. The framework's "2–5 personas" guidance is deliberately exceeded: the RBAC grid (`docs/RBAC.md` §4/§7) and the hand-authored journeys already assume 8 archetypes, and the journeys are the authority. The `## Personas` companion section below is the canonical home (`journey/bin/check-persona-coverage.sh` re-derives the persona set from its `### P<n>` headings); `docs/PERSONAS.md` mirrors it. | Owner brief §1; `interrogation-battery.md` §A.1; `JOURNEY_MAP.md` `persona:` fields; DPA + Prince, 2026-07-14 |
| 220 | **D-AUDRS-296** | **Domain 13 — quality-tool identities, exact pins, thresholds, coverage tiers, waiver authority.** **Tools (one primary per lens, per the shipped `quality-gate-lib.sh` schema):** hygiene primary = **ruff 0.15.21**; security primary (sole secrets-scanner identity, never replaced/shared) = **gitleaks 8.30.1**; perf primary = **size-limit 12.1.0**. **Supplements:** TS lint = **eslint 10.7.0** + **typescript-eslint 8.64.0** (blocking); TS dead-code = **knip 6.26.0** (blocking on unused files/exports/deps); Python dead-code = **vulture 2.16** (**ADVISORY until a finding is independently confirmed** — Django/DRF dynamic dispatch produces false positives); Python SAST = **bandit 1.9.4** (a *separate* supplement that **never replaces gitleaks**); dependency-vulnerability scanner = **osv-scanner 2.4.0** (offline, see D-AUDRS-298). All nine pins are the ones **live-verified against PyPI/npm registry JSON + GitHub releases/CHANGELOG on 2026-07-14** for the sibling RightShip module (`VIMS-RIGHTSHIP-MODULE-SSOT.md` D-AUDRS-402) — the Audit module runs the **identical** Python/TS stack (`docs/TECH_STACK.md` §1/§3), so the same verified versions are adopted rather than re-guessed; **no version here is a training-data guess**. **Thresholds:** dead-code tolerance **0, on CONFIRMED findings only**; cyclomatic ceiling **10** (ruff `C901` / eslint `complexity`) — waiver-eligible, **Prince only**; duplication = **flag, never block**; dependency-CVE routing **Critical → block, waiver max 30 calendar days · High → block, waiver max 90 calendar days · Medium/Low → flag**; raw `TBD`/`FIXME`/`TODO` placeholder markers **BLOCK** (mechanical closure), while a **structured `BLOCKED:` note carrying its own decision ID** is valid debt and is never flagged. **Coverage tiers (mirrors the RS tier shape, owner brief §2.3):** **100% branch** on the Audit **pure engines** — ① audit-window / cadence math (`audit_window.py`, D-AUDRS-089/205) · ② CAR / NC state machine (D-AUDRS-003/057/132/204) · ③ NC deadline calculation (D-AUDRS-074/082) · ④ PDF render (the 4 generators, `docs/PDF_TEMPLATES.md`) — plus **≥80%** on the audit application package (`inspection/audit/` + `src/**/audit/`), and API tests = **every endpoint × the full `AUDIT_P_*` role grid** (`docs/RBAC.md` §4/§7 — see AUDQ-001, D-AUDRS-299). **Perf:** `PB-AUD-BUNDLE` — production Vite audit-route bundle **≤ 250 KB gz**, `static-budget` via size-limit; **exceeded = FAIL**; route-level code-splitting stays enforced. **Waiver authority = PRINCE ONLY, every lens** — no delegated authority (the engineering-lead / product-owner / IT-security split used by other programs does **not** apply here). Every waiver carries `finding_id` + `decision_id` + `reason` + `created` + `expires` (YYYY-MM-DD); **no auto-renewal** — an extension is a new decision on current evidence. `waivers[]` is **empty at generation**. **Core rule: no optimization without a red budget or a cited finding.** | Owner brief §2.2/§2.3; D-AUDRS-402 (pin verification, sibling module, 2026-07-14); D-AUDRS-089/074/082/132/204 (cited, not re-decided) |
| 221 | **D-AUDRS-297** | **Domain 13 — the Audit API-latency budget is DEFERRED (this is the deferred budget's own decision ID).** The Audit module banked **no numeric performance figure**: D-AUDRS-273 makes performance **inherited / parity-with-existing-VIMS**, and audit screens are online-only (D-AUDRS-062/274). No API p95 number exists for Audit anywhere in the frozen record, and **none is invented here.** Budget **`PB-AUD-API-P95` is therefore banked with `mode: "deferred"`** — it prints **`DEFERRED` on every gate run and never silently passes** (owner brief §6.1: *"reports print DEFERRED"*). It resolves to a `measured-benchmark` budget only when a real baseline is measured against the live VIMS parity target and a numeric figure is banked under a new decision ID. **A bundle-size pass (`PB-AUD-BUNDLE`, D-AUDRS-296) never proves an API p95 budget** (owner brief §2.2). This deferral is a **quality-reporting** deferral, not a build blocker. | Owner brief §2.2 ("API p95 budgets are separate measured budgets and are NOT proven by bundle size") + §6.1 DEFERRED semantics; D-AUDRS-273/062/274 |
| 222 | **D-AUDRS-298** | **Domain 13 — the SOLE gate-time network exception (`network_allowed[]`).** `osv-scanner`'s dependency-vulnerability scan runs **offline** against a **locally-provisioned OSV database**; a **missing or stale-beyond-policy (> 7 calendar days) DB is a FAIL**, never a silent pass. The **OSV-DB refresh is a separate, controlled, network-enabled job** — it is **never** run inside `checks/quality-gate.sh` or any of its three lenses — and it is the **only** entry in `network_allowed[]`, tagged with this decision ID. Every other tool runs **network-free** at gate-execution time: **gitleaks requires no network** (regex + entropy over the local git history and working tree), **size-limit requires no network**, and ruff / eslint / typescript-eslint / knip / vulture / bandit are all fully offline once installed. | Owner brief §2.2 |
| 223 | **D-AUDRS-299** | **Domain 13 — never-waivable custom rules (AUDQ-001..003), the NOT_APPLICABLE_YET gate-state law, and Domain 13 CLOSED.** ① **AUDQ-001 — RBAC grid test** (lens: security): every endpoint × every role per `docs/RBAC.md` §4 (default role → `AUDIT_P_*` gate mapping) and §7 (action-level enforcement matrix) — allowed → documented 2xx; blocked → 403; vessel users cross-vessel → 403/404; forbidden state transitions → 409. Any failure **blocks the build**. **Never waivable.** ② **AUDQ-002 — Audit PK gate** (lens: hygiene; **Audit-owned tables/migrations ONLY**): every Audit-owned table has `id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWSEQUENTIALID()` (D-AUDRS-137/271); **`INT IDENTITY` and any non-compliant PK FAIL**; the sole allowed exception is a **FK column** referencing a legacy `char(32)` `psc_*` table, which is itself `char(32)` (a cross-type FK is impossible) — that exception **never applies to a new table's `id` PK**. **RightShip's `char(32)` + `uuid4().hex` PK rule (D-AUDRS-321/RSQ-002) is NOT applied to Audit** and vice versa. **Never waivable.** ③ **AUDQ-003 — no legacy-table mutation; approved-exception list `[]` (EMPTY)** (lens: hygiene): no `ALTER`/`DROP` against `psc_inspection`, `psc_car`, `psc_deficiency`, `psc_corrective_action`, `psc_notification`, `psc_activity_history`, `psc_audit_log`, `HRM501`, `VesselData` — **zero exceptions**, per D-AUDRS-288/289/290 and owner brief §6.0(4). **The gate asserts on the DB SCHEMA FINGERPRINT** (pre/post hashes over `sys.columns` + `sys.check_constraints` + `sys.indexes` for those 9 tables, baseline at §20.1 V-G) — **NOT on the presence of a Django migration operation**: a `choices`-only change (D-AUDRS-289) legitimately emits an `AlterField` with **no SQL**, so a grep-based gate would **false-positive and block a compliant build** (D-AUDRS-290 design note, restated here as gate law). Its **doc-level half** (no `ALTER`/`DROP` prescribed against a protected table anywhere in the DocSuite) runs today; the authoritative DB half activates with the first migration. **Never waivable.** ④ **Gate-state law (owner brief §6.1/§6.2):** the canonical state enum is exactly **`RESOLVED` · `DEFERRED` · `BLOCKED` · `NOT_APPLICABLE_YET`** — a bare `NOT_APPLICABLE` is **never** emitted. A lens/tool whose input (application code, lockfile, migration, production bundle) does not yet exist reports **`NOT_APPLICABLE_YET`** with a **mandatory** `activation_point` (the first `docs/IMPLEMENTATION_PLAN.md` phase that creates the matching artifact) and a `reason` — **never `PASS` merely because there is nothing to scan.** It does **not** block initial build handover; it does **not** count as a green phase-exit result once its activation point is reached; it **auto-activates** from repository evidence at runtime (`checks/gate-detect-lib.sh` — no flag, env var, or config can retain it after activation); and the quality stamp/verdict must show it as **visibly distinct from both `PASS` and `DEFERRED`**. Per-lens activation table: `docs/QUALITY_GATES.md` §9. ⑤ **Domain 13 CLOSED 2026-07-14** — `docs/QUALITY_GATES.md` (+ `QUALITY-MACHINE-BLOCK`) and `checks/{check-hygiene,check-security,check-perf,quality-gate}.sh` are generated; `sh quality/bin/check-gate-contract.sh .` exits 0. `docs/BLOCKERS.md` **PSB-1 is resolved-by-generation** (the gates exist and are enforceable) — which is **not** a build-phase `QUALITY: PASS` citation; that remains unearned until Step 3 lands code and a real phase exit runs the gates against it. PSB-2/3/4 remain OPEN. | Owner brief §2.1/§2.3/§5/§6.1/§6.2; D-AUDRS-083/137/271/288/289/290 (cited, not re-decided) |

### 21.2 Band status

| Range | Used | Free |
|-------|------|------|
| D-AUDRS-288..299 | **288..294** (7 banked 2026-07-14, §20) + **295, 296, 297, 298, 299** (5 banked 2026-07-14, this section) | **NONE — band EXHAUSTED** |

⚠ **Domain 14 (Release) cannot be banked into this band.** A fresh, explicitly-declared ID range (mirroring how §0.5 declares ranges) must be authorized by Prince before any Audit release decision is recorded.

---

## Personas

**DPA + Prince confirmed 2026-07-14** (D-AUDRS-295). Source: `scratchpad/sdd/interrogation-battery.md` §A.1, accepted as-is per owner brief §1. `journey/bin/check-persona-coverage.sh` re-derives the persona set directly from this section's `### P<n>` headings — the labels/numbers below are **identical** to what the frozen `JOURNEY_MAP.md` `persona:` fields already cite (verified before banking: JOURNEY-1/9/10/11 → P1 · JOURNEY-2 → P3 · JOURNEY-3 → P3 → P5 · JOURNEY-4 → P6 · JOURNEY-5 → P5 · JOURNEY-6 → P4 · JOURNEY-7 → P2 · JOURNEY-8 → P5 with P6 · JOURNEY-12 → P1 with P5 · JOURNEY-13 → P7 with P1 · JOURNEY-14 → P8). `docs/PERSONAS.md` mirrors this section.

### P1 — "SEQ Manager / DPA"
goal:             run the fleet audit programme end-to-end — assign Lead Auditors, approve OPM F 713 extensions, cancel audits, confirm external-audit closure, clear the scan-validation queue, own the operational queues
context:          office desk, all-vessel scope; DPA and SEQ Manager are the same person at KSM (D-AUDRS-034); works across many vessels with heavy context-switching; month-end + audit-cycle surges
tech_savviness:   high
error_tendency:   medium
patience_budget:  3
known_misbehaviors:
  - assigns-lead-auditor-without-checking-scope-standards
  - approves-extension-without-reading-reason
  - clears-scan-queue-item-without-opening-attachment

### P2 — "Lead Auditor"
goal:             conduct an assigned audit and close its NCs (KSM-F-NC-001 Parts E/F/G) as Lead Auditor of record, on time and defensibly
context:          any qualified office user; owns one audit at a time; edits pre-IN_PROGRESS, locked after the first finding; a PIC-review attempt on their own audit is refused 403 (D-AUDRS-110)
tech_savviness:   high
error_tendency:   medium
patience_budget:  2
known_misbehaviors:
  - edits-classification-after-first-finding-locked
  - tries-to-start-pic-review-on-own-audit
  - closes-nc-without-required-signature-scan

### P3 — "Conductor"
goal:             enter audit findings while the audit is IN_PROGRESS (conductor assigned, not the Lead Auditor)
context:          assigned office user; findings entry only; `conductor_user_id` locks at IN_PROGRESS; a post-submit finding attempt is refused 409 (D-AUDRS-080)
tech_savviness:   medium
error_tendency:   medium
patience_budget:  2
known_misbehaviors:
  - adds-finding-after-audit-submitted
  - enters-finding-against-wrong-standard

### P4 — "Office Supt / PIC"
goal:             pick up the open PIC-review pool on a CAR, do office-led NC drafting, issue fleetwide Circulars
context:          Marine/Tech Superintendent; first-to-claim PIC-of-record (D-AUDRS-107); dense-form drafting view (D-AUDRS-118); claiming PIC review while being the Lead Auditor is refused 403
tech_savviness:   high
error_tendency:   medium
patience_budget:  2
known_misbehaviors:
  - claims-pic-review-while-being-lead-auditor
  - issues-circular-without-fleetwide-flag

### P5 — "Vessel Master"
goal:             acknowledge the audit report (D-AUDRS-254), sign the closing-meeting acknowledgment, sign NC Part B, close Observations
context:          onboard; the audit is a vessel-visit event (offline-by-design process, D-AUDRS-254); rank-bound signatures via CMS-crew (D-AUDRS-250); shared ship's-office PC over satellite
tech_savviness:   medium
error_tendency:   high
patience_budget:  2
known_misbehaviors:
  - signs-on-shared-browser-after-session-lock
  - acknowledges-report-without-opening-findings
  - backdates-signature-past-30d-window

### P6 — "Vessel Crew / Action Owner"
goal:             fill NC closure via the plain-language wizard as the action owner on a CAR
context:          onboard; single-question-per-screen wizard (D-AUDRS-116/120); ≥50-char rule (D-AUDRS-074); interrupted by watch / port ops
tech_savviness:   low
error_tendency:   high
patience_budget:  2
known_misbehaviors:
  - submits-wizard-step-under-50-chars
  - attaches-wrong-evidence-scan-first
  - abandons-wizard-mid-closure-after-interruption

### P7 — "HoD (office)"
goal:             as the audited department head, sign the closing-meeting acknowledgment for an office audit
context:          office; auditee side; resolved via `master_hod_assignment` (D-AUDRS-106), acting-HoD supported
tech_savviness:   medium
error_tendency:   low
patience_budget:  2
known_misbehaviors:
  - signs-for-wrong-department-after-context-switch

### P8 — "Fleet Manager"
goal:             authorise Acting-HoD assignments (`AUDIT_P_016`) when a department head is unavailable
context:          oversight designation used only for Acting-HoD authority (D-AUDRS-253); rarely inside audit detail; self-authorisation is forbidden → 403 (D-AUDRS-253)
tech_savviness:   medium
error_tendency:   low
patience_budget:  1
known_misbehaviors:
  - tries-to-self-authorise-acting-hod
  - authorises-acting-hod-past-90-day-cap

## 22. DATED ANNOTATIONS — clarifications of banked rows (2026-07-14, append-only)

> **These are NOT new decisions.** No new ID is minted — the authorized band `D-AUDRS-288..299` is fully used (12/12). Nothing above is edited; every banked row stands exactly as banked. Where an annotation below and an annotated row differ in *wording*, the annotation governs how the row is **read** — never its substance. Recorded here because the frozen/banked bodies are append-only by law (§0.5).

| # | Annotates | Clarification |
|---|-----------|---------------|
| **A-1** | §20.3 band-status table (*"295..299 free"*) | **Point-in-time snapshot, superseded by §21.** D-AUDRS-295..299 were banked later the same day (2026-07-14, Domain 12 + Domain 13). Band `D-AUDRS-288..299` is now **fully used — 12/12**; **0 free**. Any further Audit decision needs a newly owner-authorized band. |
| **A-2** | §20.3 line *"Audit performs zero `ALTER`/`DROP`/`UPDATE` against `psc_*`, `HRM501`, or `VesselData`"*, and the AUDQ-003 rule (D-AUDRS-290 / D-AUDRS-299 ③) | **SCOPE: the never-waivable prohibition is DDL-scoped.** It forbids (a) `ALTER`/`DROP` against any of the 9 protected shared tables and (b) any **migration-time** rewrite of shared legacy rows. It has **never** forbidden **runtime DML through the existing PSC/CAR services**, which is unchanged and *is* the module's core design (D-AUDRS-070/131/132/003): ① the audit finding-create service **INSERTs one `psc_car` row** per finding via the existing Django CAR-creation code (D-AUDRS-008/131); ② audit closure proxies to `POST /api/psc/cars/<id>/workflow/`, which **writes `psc_car.status`** — that write is the **entire point** of D-AUDRS-289 (the values already fit the unconstrained `nvarchar(60)` column, so no DDL is needed to store them); ③ the audit-inspection **soft-delete guard writes its `psc_inspection` row** (D-AUDRS-079, FEAT-AUD-704). **A row write is not a schema mutation.** This is precisely why the gate of record asserts on the **DB schema fingerprint** (`sys.columns` + `sys.check_constraints` + `sys.indexes`, D-AUDRS-290) and never on row-write behaviour. Read the unqualified word *"`UPDATE`"* in §20.3 as *"migration-time `UPDATE`"*. |
| **A-3** | D-AUDRS-292, the words *"The open item is **CLOSED**"* | **State label normalised to the canonical four-state enum** (owner brief §6.1, banked as D-AUDRS-299 ④: `RESOLVED` · `DEFERRED` · `BLOCKED` · `NOT_APPLICABLE_YET`). D-AUDRS-292's state is **`RESOLVED`**; its **reason** is *"retired / mis-aimed — `psc_corrective_action` has no `status` column, so there was nothing to confirm."* `CLOSED` and `RETIRED` are **not** canonical states and are not used as states anywhere in the v4 layer. *(Unaffected: the pre-existing `pdf_hash_validation_status` domain enum, whose `NOT_APPLICABLE` is a legitimate **data value**, not a gate state.)* |
| **A-4** | §21 D-AUDRS-295 (persona → journey mapping list) | **`JOURNEY_MAP.md` `persona:` fields normalised to the gate's single-persona grammar** (`P<n> (<name>)`), per the orchestrator ruling of 2026-07-14: a journey's `persona:` names the **primary actor** — the persona who performs the journey's decisive/misbehavior step — and any second persona stays named in the steps text. Applied to the 4 multi-persona lines: **JOURNEY-3 → P3** (Conductor; the 409 post-submit finding attempt is P3's), **JOURNEY-8 → P5** (Vessel Master; the signature is the decisive step), **JOURNEY-12 → P5** (Vessel Master; the external Part-B signature is the misbehavior step), **JOURNEY-13 → P1** (SEQ Manager / DPA; the 422 SEQ-CoI Lead-Auditor attempt is P1's). **No persona is removed, no behavior changes, and the persona SET (P1..P8) is unchanged.** P7 (HoD) remains a named actor in JOURNEY-13's steps without being its `persona:` of record. |

---

## 23. SUPPLEMENTAL DECISION BAND — D-AUDRS-450..499 (Domain 14 Release & Deployment, v4 retrofit)

> **Appended 2026-07-14. Append-only; nothing above is edited** — per §0.5 / D-AUDRS-284 a locked decision changes only by explicit supersession with a new ID in an authorized band. The frozen v1.0 (§9, D-001..123), v1.1 (D-200..287) and the supplemental bands (§20, §21) stand exactly as banked.
>
> **Why a new band:** band `D-AUDRS-288..299` is **EXHAUSTED (12/12)** — 288..294 (§20, the no-legacy-DDL fork) + 295..299 (§21, Domain 12 + Domain 13). §21.2 and §22 A-1 both flag that **Domain 14 had no free ID**. The owner (Prince) has now **authorized the range `D-AUDRS-450..499`** for Audit Domain 14 and subsequent Audit supplemental decisions. That authorization is itself banked below as **D-AUDRS-450** — the band declaration is a decision, not a footnote.
>
> **Origin:** Owner brief *"VIMS v4 — Quality-Gate + Release-Protocol + Personas Retrofit"* (Prince, 2026-07-14) — **§3 (Release)** · §4.1 (Migration, as **superseded by §6.0**) · §6.0 (zero DDL, EMPTY exception list) · §6.1 (canonical four-state enum) · §6.4/§6.5 (terminal contract, controls).
>
> **Reading note:** the migration facts below are the **post-fork** truth (`docs/MIGRATION.md`, D-AUDRS-288..294) — **not** the pre-fork §4.1 draft text of the owner brief, which §6.0 supersedes.

### 23.1 Band declaration

| Range | Authorized by | Date | Scope | Convention |
|-------|---------------|------|-------|------------|
| **D-AUDRS-450..499** | **Prince (owner / DPA)** | **2026-07-14** | Audit Domain 14 (Release & Deployment) + subsequent Audit supplemental decisions | Dated, append-only, appended AFTER the frozen decision log (§9.5 pattern, §0.5 rule). Frozen bodies are never edited. |

### 23.2 Supplemental decisions

| # | ID | Decision | Source |
|---|----|----------|--------|
| 224 | **D-AUDRS-450** | **🔑 ID-BAND DECLARATION — `D-AUDRS-450..499` is authorized for the Audit module.** Band `D-AUDRS-288..299` is fully used (12/12: 288..294 §20 + 295..299 §21); §21.2 and §22 A-1 record that Domain 14 had **no free ID**. Prince authorizes the fresh range **`D-AUDRS-450..499`**, opened by this decision, for **Domain 14 (Release & Deployment)** and any later Audit supplemental decision. The band follows the existing convention exactly: **dated, append-only, appended after the frozen log; no frozen body is edited; a locked decision changes only by explicit supersession with a new ID** (§0.5, D-AUDRS-284). Ranges already allocated elsewhere are untouched: `D-AUDRS-300+` = v1.2 RightShip · `D-AUDRS-400..449` = RightShip v4 retrofit. **This band does not overlap either.** | Owner authorization 2026-07-14 (VIMS v4 brief §6.3b(3): *"Confirm Audit uses `D-AUDRS-450..499` only after the band declaration is banked"*) |
| 225 | **D-AUDRS-451** | **Domain 14 — versioning & tags.** Scheme = **SemVer**. Tag format = **module-scoped `vims-audit-v<version>`** on the shared `VimsWithSafety` repository (the sibling module uses `vims-rs-v<version>`; the modules advance **independently**). The **first cut is a MINOR (additive) release** — the Audit module adds new tables, endpoints, and screens and changes **no existing PSC/CAR behaviour** (D-AUDRS-001/003); the owner's worked example tag is **`vims-audit-v1.0.0`** (brief §3.3). `VERSION` is the raw version handed to `release/bin/release-preflight.sh`; the **tag is derived from `versioning.tag_format`, never hand-typed**. | Owner brief §3.1/§3.3 |
| 226 | **D-AUDRS-452** | **Domain 14 — deploy target (RESOLVED; the *method* is not — see D-AUDRS-453).** Target = the **existing VIMS production deployment**, extended **in place inside the existing VIMS application** (D-AUDRS-273/001): **no new application server, host, or region**; the **shared `ksm_cms_live`** SQL Server database (D-AUDRS-135); the **existing cron infrastructure** for the audit background jobs (`BACKEND_STRUCTURE.md §12`). **KSM India owns execution.** These are the *known* facts and are banked as known; nothing about *how* the deploy is executed is inferred from them. | Owner brief §3.2; D-AUDRS-273/135/001 |
| 227 | **D-AUDRS-453** | **🔑 Domain 14 — `deploy.method` is DEFERRED (this is the deferral's own decision ID). RELEASE BLOCKER — not a build-handover blocker.** KSM India has **not** supplied the executable deployment procedure, and **none is invented** (owner brief §3.2: *"Do not use generic wording merely to satisfy lint"*). `RELEASE_RUNBOOK.md`'s `deploy.method` therefore carries the **exact sentinel `DEFERRED:D-AUDRS-453`** with a matching `deferred[]` register entry (`field`, `decision_id`, `reason`, `owner`, `closure_data`) — the framework's structured-deferral mechanism, not prose. **Owner = KSM India (execution owner).** **`closure_data` — the seven facts that close it, exactly as the owner enumerated them:** ① exact deployment command or numbered procedure · ② execution environment and identity · ③ required credential/secret references · ④ migration command (the environment-level invocation of `migration.forward`) · ⑤ success signal · ⑥ failure signal · ⑦ previous-tag redeploy/rollback command. **Machine consequences (framework law, verified):** `release/bin/lint-release-runbook.sh` reports **`VERDICT: DEFERRED … reason_codes=DEFERRAL_OPEN` (exit 0)** — the runbook is a **valid document**; `release/bin/release-preflight.sh` reports **`VERDICT: BLOCKED … DEFERRAL_OPEN` (exit 1)** and `release/bin/release-attest.sh` refuses with `result: ABORTED` — the crossing is **impossible, with no override path**. **Closure is a change to release law:** the real value replaces the sentinel **and** the register entry is deleted, **together**, via the Tier-2 CR path — **never inline, never at ceremony time.** The bundle is **BUILD-HANDOVER READY with this open**; it is **release-blocked** until it closes. | Owner brief §3.2 + §6.1b + §6.3 (*"The exact KSM India deployment method is a RELEASE blocker, not a build-handover blocker"*) |
| 228 | **D-AUDRS-454** | **Domain 14 — approval authority.** `approval.authorizer` = **Prince (DPA / final freeze authority, D-AUDRS-285)**. **KSM India executes; only Prince authorizes the crossing.** The authorizer is a **trust root and is NEVER deferrable** (framework `release-lib.sh`: only `deploy.target`, `deploy.method`, `migration.tooling`, `migration.forward`, `migration.reverse`, `rollback.procedure` may be deferred). Preflight output is **evidence presented to the authorizer, never a substitute for the authorizer's judgement**. | Owner brief §3.5; D-AUDRS-285 |
| 229 | **D-AUDRS-455** | **Domain 14 — attestation location, ref, and controls.** `attestation.ref` = **`refs/heads/release-evidence`** (protected, append-only); `attestation.location` = **`release-evidence/<tag>/`** (e.g. `release-evidence/vims-audit-v1.0.0/`). Every published evidence directory contains **at least**: `RELEASE_ATTESTATION.json` · `RELEASE.md` · `REVIEW.md` · `checks/reports/release-preflight.json` · the required-check reports **or their SHA-256 hashes**. **Controls:** only **trusted CI** may publish · **no force-push** · a **published tag directory is immutable** (never modified, never deleted) · corrections are published under **`<tag>/corrections/<n>/`** · **every correction records the SHA-256 hash of the attestation it supersedes** · **an existing tag with NO attestation means the trusted job did not complete and must be re-run** (never that it ran and hid a failure). Attestation location/ref are **trust roots — never deferrable**. | Owner brief §3.3; framework `Release.txt` |
| 230 | **D-AUDRS-456** | **Domain 14 — `required_checks[]` and the whole-repo-tag mandate.** `required_checks[]` = ① **module quality gate** (`sh checks/quality-gate.sh`) · ② **journey gates** (coverage + persona-journeys + journey-map lint + persona coverage, the four delivered `journey/bin` gates with this bundle's exact arguments) · ③ **backend tests** · ④ **frontend tests** · ⑤ **RBAC-grid test** (AUDQ-001, never-waivable, D-AUDRS-299①). **`release-preflight` MUST NOT appear in `required_checks[]`** (recursion — the shipped linter fails the runbook if it does); the preflight **report** (`checks/reports/release-preflight.json`) is nonetheless a **mandatory evidence artifact** (D-AUDRS-455). **Because a module-scoped tag still points at the WHOLE repo commit** (owner brief §3.1), two further checks are **mandatory and are carried IN `required_checks[]`**: ⑥ **shared PSC/CAR regression** (`TEST_PLAN.md §16` Suite M — the PSC lifecycle, CAR state machine, PSC PDF export and `PSC_P_*` RBAC are provably unchanged) and ⑦ **a shared-code diff check** proving that unrelated shared-code changes in the tagged commit are **absent, or deliberately included and reviewed**. Checks ③–⑦ are **code-dependent**: they are declared here as **release law** and shipped as **fail-closed** executables under `checks/release/` — they **exit non-zero until the build wires them to the real suites** (Phase 0). A release **cannot cross on an unrun check**; a check that cannot run **fails, and never passes by absence**. `required_checks[]` is an **evidence source — never deferrable**. | Owner brief §3.1/§3.3; D-AUDRS-299①; `TEST_PLAN.md §11/§16` |
| 231 | **D-AUDRS-457** | **🔑 Domain 14 — the migration command surface (release law; `migration.tooling` / `.forward` / `.reverse` / `.verify_probes`).** **Bound to the POST-FORK truth in `docs/MIGRATION.md` (D-AUDRS-288..294) — NOT the pre-fork owner-brief §4.1 draft, which §6.0 supersedes.** **Tooling:** Django 5.2.7 `managed=True` migrations inside the existing `inspection` app (`TECH_STACK.md §1/§2`; the audit code is the `inspection/audit/` sub-package), **ADDITIVE ONLY**, **zero `ALTER`/`DROP` on any shared legacy table** (`psc_*`, `HRM501`, `VesselData`), **approved shared-table mutation exception list = `[]` (EMPTY)**; seeds load through the idempotent `inspection/audit/seeds/` runner (`BACKEND_STRUCTURE.md §13`). **Forward** is one fail-fast `&&` chain: ⓪ record the last applied `inspection` migration (`PRE_AUDIT_MIGRATION`, the reverse target) → ① capture the **pre-migration schema fingerprint** of the 9 protected tables (`sys.columns` + `sys.check_constraints` + `sys.indexes`, D-AUDRS-290) → ② **D-AUDRS-294's P0 CHECK-constraint assertion** (`psc_car` must carry **0** CHECK constraints; **if one is found the build/crossing FAILS `BLOCKED` and escalates to Prince — the migration MUST NOT self-authorize a schema change**) → ③ the **read-only** pre-deploy legacy-discovery probe (`SELECT COUNT(*) FROM psc_inspection WHERE inspection_type IN ('AUDIT','RS')`, D-AUDRS-291) → ④ `migrate inspection` (creates the 43 Audit-owned tables; the `CARStatus` `choices` extension emits an `AlterField` that generates **no SQL**, D-AUDRS-289) → ⑤ the **PK-standard verification** (D-AUDRS-137/271/299②; **any violation FAILS the build**) → ⑥ the **conditional Audit-owned tag load** into `audit_legacy_inspection_tag` — **never a write of any kind to `psc_inspection`** (D-AUDRS-288/291) → ⑦ the **seed load** → ⑧ the **post-migration fingerprint compare — pre and post MUST be IDENTICAL; any difference FAILS, never-waivable**. **The fingerprint gate asserts on the DATABASE, never on migration-file text** (a `choices`-only change emits a no-SQL `AlterField`, so a grep gate would false-positive on a compliant build — D-AUDRS-290 design note, `MIGRATION.md §10.3`). **Reverse/recovery** (`MIGRATION.md §6`): **data reset precedes any object removal** — never the reverse; **Case A (before production Audit data exists)** = tested reverse of **Audit-owned objects only** (`audit_data_reset` then `migrate inspection <PRE_AUDIT_MIGRATION>`); **Case B (after production Audit data exists)** = **redeploy the previous module tag and LEAVE the additive Audit-owned schema in place** — **production Audit data is NEVER destructively dropped as an automatic application rollback**, corrections go through forward-fix migrations, and a DB restore is a separate human-authorized action. Because the migration performs **no DDL and no writes against any shared legacy table, rollback can never touch `psc_*`, `HRM501`, or `VesselData` in either direction.** **`verify_probes[]` (6):** ① expected Audit-owned tables + constraints/indexes exist · ② module **PK compliance** (`UNIQUEIDENTIFIER` + `NEWSEQUENTIALID()`) · ③ **exactly the approved legacy exceptions — the list is EMPTY, i.e. ZERO shared-table mutation** (fingerprint compare) · ④ **seed/provenance counts** match `SEEDS_PROVENANCE.md` · ⑤ **cutover smoke** — register → submit → DPA-close an internal audit, and its **NC reaches `LEAD_AUDITOR_CLOSED`** · ⑥ **existing PSC and CAR flows healthy** (`TEST_PLAN.md §16`; `/api/psc/health/`). **This decision NAMES the Django management commands the runbook executes (`audit_schema_fingerprint`, `audit_assert_no_car_check_constraint`, `audit_legacy_discovery_probe`, `audit_verify_pk_standard`, `audit_legacy_tag_load`, `load_audit_seeds`, `audit_verify_tables`, `audit_verify_seed_counts`, `audit_cutover_smoke`, `audit_psc_regression_probe`, `audit_data_reset`) — they are RELEASE LAW, and Phase 0 MUST implement them under exactly these names.** They are **specified**, not observed: no existing-code claim is made about them. **The environment-level wrapper** (host, identity, `DJANGO_SETTINGS_MODULE`, DB credentials, the invocation shell) is **owner-dependent and rides D-AUDRS-453** — it is referenced, never invented. | Owner brief §4.1 **as superseded by §6.0** + §4.2's exactness law (*"All runbook migration fields must contain exact executable commands or an explicit blocking DEFERRED decision. Prose alone is insufficient."*); `docs/MIGRATION.md` §1–§10; D-AUDRS-288..294 |
| 232 | **D-AUDRS-458** | **Domain 14 — rollback strategy, triggers, timing.** **Strategy = redeploy the previous module tag.** The **additive, backward-compatible Audit-owned schema REMAINS IN PLACE** during an application rollback, and **schema reversal is NEVER automatically triggered by a deployment rollback**. **Eight triggers (any one fires it):** ① a required post-deploy probe fails · ② `/api/psc/health/` is down or unhealthy past the banked retry window · ③ the module cutover smoke fails · ④ existing PSC/CAR behaviour regresses · ⑤ vessel scoping / authorization / state guards regress · ⑥ data corruption or integrity failure (partial writes, forbidden state transitions, uniqueness violations, broken references, unexpected legacy-data mutation) · ⑦ a newly introduced **unwaived Critical** security defect attributable to the release · ⑧ a newly introduced **High** defect that is remotely exploitable, crosses an authorization/vessel-isolation boundary, exposes secrets/PII, or cannot be immediately contained. **Timing: within 10 minutes of confirmation** — halt further deployment activity, declare rollback, identify the previous tag. **Within 30 minutes** — redeploy the previous tag, verify health, run the shared PSC/CAR smoke, run the affected module smoke, record **`ROLLED_BACK`**. A rollback is **the ceremony working as designed, not a failed ceremony**. The **exact previous-tag redeploy command rides D-AUDRS-453** (`closure_data` ⑦). | Owner brief §3.4 (verbatim) |
| 233 | **D-AUDRS-459** | **🔑 Domain 14 — `handoff.part_a_done: false` and the DRY-crossing law.** Existing VIMS deployments are **historical facts only**: **no tags, no `RELEASE.md`, no attestations are backfilled onto pre-protocol deployments.** The first production attestation must correspond to a **genuinely new module release under this runbook**. **Before KSM India's first production release, a COMPLETE DRY crossing is executed** against a **local bare repo + non-production target**. **A failed DRY crossing BLOCKS the first production crossing.** **DRY scope must prove all 13:** release preflight + stamp verification · module-scoped tag derivation · migration forward command · migration verification probes · reverse / restore-point recovery · human-authorization pause · deployment simulation · post-deploy probes · rollback trigger + previous-tag redeployment · evidence staging · trusted attestation publication · independent attestation verification · append-only correction behaviour. **DRY namespace (NEVER a production release):** tag **`vims-audit-dry-v0.0.1`**, evidence **`release-evidence/dry/<dry-tag>/`**. **One-time handoff semantics:** the DRY crossing may produce DRY evidence and a DRY attestation but **does NOT set `handoff.part_a_done = true`** and **does NOT run Step 5 Part A** as production activation. **The first genuine production crossing** (`RELEASED` or `ROLLED_BACK`, durably attested in the **production** namespace) **runs Step 5 Part A exactly once**. `handoff.part_a_done` changes **only** through the governed release-law change process (Tier-2 CR) — **never by silently editing the runbook**. Later crossings observe `part_a_done = true` and do **not** repeat Part A. | Owner brief §3.5 (verbatim) |
| 234 | **D-AUDRS-460** | **Domain 14 GENERATED; the release remains BLOCKED.** Root **`RELEASE_RUNBOOK.md` is generated from this band** (⛔ stub deleted, machine block `schema_version: 2` with `decisions[]` origin provenance). Verified against the **delivered/vendored** framework scripts (commit `f908204`, stock `/bin/sh`): `sh release/bin/lint-release-runbook.sh .` → **`VERDICT: DEFERRED … deferred_fields=deploy.method reason_codes=DEFERRAL_OPEN` (exit 0)** and `sh release/bin/release-preflight.sh . 1.0.0` → **`VERDICT: BLOCKED … DEFERRAL_OPEN` (exit 1)**. **`docs/BLOCKERS.md` PSB-3 is therefore SPLIT, honestly:** the *runbook-missing* half is **RESOLVED-BY-GENERATION**; the *crossing* half stays **OPEN and BLOCKED** on D-AUDRS-453, and PSB-2 (no `REVIEW.md`) independently blocks the crossing too. **No release may be claimed.** **`NOT_APPLICABLE_YET` is not used anywhere in the runbook** — release-law fields are **owner-dependent, never code-dependent** (framework `release-lib.sh`), so the only honest state for an unsupplied law field is a structured **`DEFERRED`** record. | This generation, 2026-07-14; framework `f908204`; owner brief §6.1/§6.3/§6.4 |

| 235 | **D-AUDRS-461** | **🔑 SUPERSEDES ONE CLAUSE OF D-AUDRS-460 — the machine block ships in the LEGACY form, because the DELIVERED framework linter makes origin-provenance and a structured deferral MUTUALLY EXCLUSIVE.** D-AUDRS-460 stated the block would carry `schema_version: 2` + `decisions[]` origin provenance. **It cannot, and the reason is a framework defect at commit `f908204`, proven — not assumed.** `release/bin/lint-release-runbook.sh`'s **near-miss sentinel scan** flags **any** string outside the `deferred[]` register that begins case-insensitively with `deferred` and is not the exact token `DEFERRED:<id>`. The **canonical origin enum's own value `"origin": "DEFERRED"`** (`USER | PROPOSED | DEFERRED`, per `release/contract/runbook-schema.json` + `Release.txt`) **is exactly such a string.** A **correctly backed** deferral therefore lints **`FAIL … DEFERRAL_MALFORMED`** the instant the runbook also claims provenance. **Minimal reproduction** (schema-conformant 1-decision runbook; `deploy.method: "DEFERRED:D-301"`; complete `deferred[]` record; `decisions: [{"id":"D-301","origin":"DEFERRED"}]`) → `VERDICT: FAIL lint-release-runbook reason_codes=DEFERRAL_MALFORMED`. The framework's own `release/tests/origin-provenance_test.sh` exercises **only the UNBACKED** DEFERRED origin (line 114, expecting `DEFERRED_ORIGIN_UNBACKED`); the **BACKED** case — the case `DEFERRED_ORIGIN_UNBACKED` exists to legitimise, and the only case this module needs — is **never tested and is structurally unreachable.** **Resolution (the only honest one):** the block omits `schema_version`/`decisions[]`, the linter classifies it **`LEGACY`** and prints the **non-blocking** `NOTE: ORIGIN_PROVENANCE_ABSENT`, and the verdict is the honest **`DEFERRED … deferred_fields=deploy.method reason_codes=DEFERRAL_OPEN` (exit 0)**. **Rejected alternatives:** ① patching the vendored linter — **forbidden** (owner brief §6.5 Control 1: vendored gates stay byte-identical to `f908204`; a framework law change needs owner authorization); ② relabelling D-AUDRS-453's origin as `USER` to slip past the scan — **a quiet falsification** (its origin *is* a deferral), i.e. precisely the class of lie the deferral machinery exists to prevent. **Nothing material is lost:** all 11 Domain 14 IDs are listed in `decision_ids[]`, and every origin is recorded in §23.2 — this section is the record of authority. **Same posture as this bundle's `QUALITY-MACHINE-BLOCK`** (also `LEGACY`, deliberately, `progress.txt` 2026-07-14). **⚠ The sibling RightShip runbook will hit this identically.** **Framework fix (upstream, owner-authorized, NEVER here):** exclude `decisions[].origin` from the near-miss path filter — it is a provenance field, not a law field, and must not be scanned as one. Recorded as `docs/BLOCKERS.md` **OQ-2**. | This generation, 2026-07-14 (minimal repro against the delivered `f908204` script); owner brief §6.5 Control 1 |

### 23.3 Band status

| Range | Used | Free |
|-------|------|------|
| **D-AUDRS-450..499** | **450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460** (11 banked 2026-07-14) | **461..499** |

**Release state after this band: `BLOCKED`** (canonical four-state enum, D-AUDRS-299④) — `deploy.method` is an **open DEFERRED decision** (D-AUDRS-453). **Build-handover state is unaffected** (owner brief §6.3).

### 23.4 Band status — UPDATED (supersedes the §23.3 snapshot; append-only, §22 A-1 precedent)

> §23.3 is a **point-in-time snapshot** taken before D-AUDRS-461 was banked. It is **not edited** (§0.5 — banked rows are never rewritten); it is **superseded by this table.**

| Range | Used | Free |
|-------|------|------|
| **D-AUDRS-450..499** | **450..461** (12 banked 2026-07-14 — 450 band declaration · 451..460 Domain 14 · **461** machine-block form correction) | **462..499** |

**Release state: `BLOCKED`** (canonical four-state enum, D-AUDRS-299④) — `deploy.method` is an **open DEFERRED decision** (D-AUDRS-453). **Build-handover state is unaffected** (owner brief §6.3).

### 23.5 Supplemental decision — D-AUDRS-462 (independent-review fix, appended 2026-07-14)

> **Appended 2026-07-14. Append-only; nothing above is edited** — per §0.5 / D-AUDRS-284 a locked decision changes only by explicit supersession with a new ID in the authorized band. D-AUDRS-450..461 stand exactly as banked; this decision supersedes **one clause** of D-AUDRS-456's wording only — the row itself is not rewritten.

| # | ID | Decision | Source |
|---|----|----------|--------|
| 236 | **D-AUDRS-462** | **🔑 SUPERSEDES ONE CLAUSE OF D-AUDRS-456 — `required_checks[]` check ② is FIVE delivered `journey/bin` gates, not four; `check-doc-format.sh` was omitted with no stated rationale and no fact basis for the omission.** D-AUDRS-456 banked check ② as "coverage + persona-journeys + journey-map lint + persona coverage, the four delivered `journey/bin` gates". An independent review found this incomplete: this bundle's own doc-format gate — `sh journey/bin/check-doc-format.sh docs/PRD.md docs/APP_FLOW.md --allow-unlinked` — **exits 0** today, so its omission is not a fact difference from the sibling RightShip module, whose runbook already chains it. **`--allow-unlinked` defers only three reason codes** (`SCREEN_UNTOUCHED`, `UNLINKED_FEAT`, `UNLINKED_AFJ`) to the structured coverage-gap workflow (`JOURNEY_COVERAGE_GAPS.md`, reviewer PENDING-PRINCE) — **every other doc-format structural rule (heading grammar, FEAT/AFJ id format, PRD↔APP_FLOW cross-references) stays enforced.** Omitting the gate from `required_checks[]` would silently discard those structural checks at the release tag, where `release-attest.sh` re-executes every required check in a fresh worktree. **Resolution:** `RELEASE_RUNBOOK.md` §5 check ② and the `RELEASE-MACHINE-BLOCK` `required_checks[1]` command now read **five** gates, ending in `&& sh journey/bin/check-doc-format.sh docs/PRD.md docs/APP_FLOW.md --allow-unlinked`. **D-AUDRS-456's banked row is NOT edited** — this decision supersedes only the "four delivered gates" clause as read; the row stands exactly as originally banked, per §0.5. | Independent review finding A2, 2026-07-14; parity with the sibling RightShip module's `required_checks[]` |

### 23.6 Band status — UPDATED (supersedes the §23.4 snapshot; append-only, §22 A-1 / §23.4 precedent)

> §23.4 is a **point-in-time snapshot** taken before D-AUDRS-462 was banked. It is **not edited** (§0.5 — banked rows are never rewritten); it is **superseded by this table.**

| Range | Used | Free |
|-------|------|------|
| **D-AUDRS-450..499** | **450..462** (13 banked 2026-07-14 — 450 band declaration · 451..460 Domain 14 · 461 machine-block form correction · **462** required_checks[] five-gate correction) | **463..499** |

**Release state: `BLOCKED`** (canonical four-state enum, D-AUDRS-299④) — `deploy.method` is an **open DEFERRED decision** (D-AUDRS-453). **Build-handover state is unaffected** (owner brief §6.3).

### 23.7 Supplemental decision — D-AUDRS-463 (upstream collision defect CLOSED; posture unchanged, appended 2026-07-14)

> **Appended 2026-07-14. Append-only; nothing above is edited** — per §0.5 / D-AUDRS-284 a locked decision changes only by explicit supersession with a new ID in the authorized band. **D-AUDRS-461's banked row is NOT edited, NOT superseded, and stays exactly as originally banked** — this decision records a downstream fact (the upstream defect it described is now fixed) and closes the open question it created; it does not change what D-AUDRS-461 decided or why that decision was correct at the time.

| # | ID | Decision | Source |
|---|----|----------|--------|
| 237 | **D-AUDRS-463** | **🔑 The framework defect D-AUDRS-461 documented (`docs/BLOCKERS.md` OQ-2 — the near-miss sentinel scan making `decisions[].origin` provenance and a correctly-backed deferral MUTUALLY EXCLUSIVE) is FIXED UPSTREAM, at framework commit `aeccc3c`** (the fix itself landed at `68d5afd` — *"fix(release): near-miss sentinel scan is field-scoped — origin provenance no longer collides with a valid deferral"* — with its regression test added at `cdedc72` and the test's own prose corrected at `aeccc3c`; re-vendored into this bundle wholesale, byte-identical, per this session's Control-1 re-vendor). **Verified against the delivered, re-vendored script** (not assumed): `sh release/tests/deferral-origin-collision_test.sh` — **61/61 assertions pass, 0 failures** — proving a runbook that both claims `decisions[].origin` provenance AND carries a correctly-backed deferral now lints the honest `VERDICT: DEFERRED` (never `FAIL`), while **every trust-root and near-miss guard the item-4 hardening (`f908204`) established is provably UNWEAKENED**: a near-miss on `decisions[].id` (oc-6), on `approval.authorizer` (oc-9, trust root), on `attestation.ref` (oc-10, evidence source), inside `required_checks[]` (oc-11) or `rollback.triggers[]` (oc-12), or an out-of-enum/exact-sentinel value in `origin` itself (oc-5, oc-7) is **still REFUSED as `DEFERRAL_MALFORMED`** — the fix is field-scoped exactly to `decisions[].origin`, nothing wider. **What this changes for this bundle: NOTHING, by design.** D-AUDRS-461's resolution — ship `RELEASE_RUNBOOK.md`'s machine block in the **LEGACY form** (no `schema_version`, no `decisions[]`) — **remains valid and non-blocking**, because the gate contract classifies a LEGACY block additively: `sh release/bin/lint-release-runbook.sh .` still reports the same **non-blocking** `NOTE: ORIGIN_PROVENANCE_ABSENT` and the same honest **`VERDICT: DEFERRED … deferred_fields=deploy.method reason_codes=DEFERRAL_OPEN` (exit 0)** it always did — the LEGACY form was never a workaround forced to expire when the upstream bug closed; it was, and remains, a **complete, honest, gate-conformant document**. **Adopting `schema_version: 2` + `decisions[]` origin provenance in this runbook is therefore OPTIONAL and DEFERRED as a future enhancement** — it is now *possible* (the collision that once made it unsafe is gone) but is **required by no gate, and is NOT done by this decision**. **Explicitly out of scope here:** restoring, authoring, or backfilling origin provenance on the runbook now — doing so would assert a substantive per-decision origin claim (an authoring act, not a bookkeeping one) and sits outside this session's scope freeze (owner scope: re-vendor + gate re-run + honest annotation, nothing more). **`docs/BLOCKERS.md` OQ-2 is CLOSED** (upstream defect fixed and proven against the delivered script); the optional provenance adoption is logged there as a **non-blocking future enhancement**, not a residual defect. | This session, 2026-07-14 (re-vendor to framework `aeccc3c`; proof = `release/tests/deferral-origin-collision_test.sh` full pass); owner brief §6.5 Control 1 (annotate, do not author) |

### 23.8 Band status — UPDATED (supersedes the §23.6 snapshot; append-only, §22 A-1 / §23.6 precedent)

> §23.6 is a **point-in-time snapshot** taken before D-AUDRS-463 was banked. It is **not edited** (§0.5 — banked rows are never rewritten); it is **superseded by this table.**

| Range | Used | Free |
|-------|------|------|
| **D-AUDRS-450..499** | **450..463** (14 banked 2026-07-14 — 450 band declaration · 451..460 Domain 14 · 461 machine-block form correction · 462 required_checks[] five-gate correction · **463** upstream collision defect closed, posture unchanged) | **464..499** |

**Release state: `BLOCKED`** (canonical four-state enum, D-AUDRS-299④) — `deploy.method` is an **open DEFERRED decision** (D-AUDRS-453). **Build-handover state is unaffected** (owner brief §6.3).

### 23.9 Supplemental decision — D-AUDRS-464 (Domain 13 — OSV staleness figure retracted; sibling module's owner-ruled 72h/24h policy adopted, appended 2026-07-14)

> **Appended 2026-07-14 (staleness-sweep finding). Append-only; nothing above is edited** — per §0.5 / D-AUDRS-284 a locked decision changes only by explicit supersession with a new ID in the authorized band. **D-AUDRS-298's banked row is NOT edited, NOT superseded, and stays exactly as originally banked** — this decision corrects a factual figure carried in generated artifacts that cited it, not the row's account of the network-exception's existence.

| # | ID | Decision | Source |
|---|----|----------|--------|
| 238 | **D-AUDRS-464** | **🔑 D-AUDRS-298's `> 7 calendar days` OSV-database staleness figure is an INVENTED number with no owner citation, exactly as the sibling RightShip module's identical figure (its D-AUDRS-407) was independently found to be and retracted (D-AUDRS-411⑥) — owner brief §2.2 states no number for Audit either. The Audit module runs the byte-identical tool (`osv-scanner 2.4.0`, D-AUDRS-296/402), so the same reasoning D-AUDRS-296 already used to adopt the sibling module's verified tool pins — "adopted, not re-guessed" — extends here to the freshness/integrity policy: this decision ADOPTS D-AUDRS-411's owner ruling verbatim for the Audit module too — *"refresh every 24 hours; maximum database age 72 hours; trusted refresh manifest is authoritative; cache is transport only; missing, stale, or hash-divergent database fails closed"*. `> 7 calendar days` is retracted and superseded by **72 hours maximum age / 24-hour refresh** in every Audit generated artifact that cited it: `docs/QUALITY_GATES.md` §5 (+ the `QUALITY-MACHINE-BLOCK` `network_allowed[]` entry), `docs/TECH_STACK.md`, and `checks/check-security.sh`. **Unlike D-AUDRS-407, D-AUDRS-298 never carried a false "Payroll exemplar" provenance claim — nothing of that kind is retracted here, because nothing of that kind was ever asserted for Audit.** **Mechanism note (honest, not a claimed build):** this bundle's `checks/check-security.sh` implements a simple mtime-age check, not the sibling module's trusted-refresh-manifest + per-file sha256 verification system; adopting that fuller mechanism is deferred to Phase 0 build activation (the osv-scanner lens is currently `NOT_APPLICABLE_YET` regardless — no lockfile exists yet, D-AUDRS-299④) — what this decision corrects **now** is the policy **number**, wherever it is cited, because the old number is proven invented, not the enforcement mechanism around it. | Staleness-sweep finding, 2026-07-14; parity with the sibling RightShip module's D-AUDRS-411 (owner ruling, verbatim, 2026-07-14) |

### 23.10 Band status — UPDATED (supersedes the §23.8 snapshot; append-only, §22 A-1 / §23.8 precedent)

> §23.8 is a **point-in-time snapshot** taken before D-AUDRS-464 was banked. It is **not edited** (§0.5 — banked rows are never rewritten); it is **superseded by this table.**

| Range | Used | Free |
|-------|------|------|
| **D-AUDRS-450..499** | **450..464** (15 banked 2026-07-14 — 450 band declaration · 451..460 Domain 14 · 461 machine-block form correction · 462 required_checks[] five-gate correction · 463 upstream collision defect closed, posture unchanged · **464** OSV staleness figure retracted, sibling policy adopted) | **465..499** |

**Release state: `BLOCKED`** (canonical four-state enum, D-AUDRS-299④) — `deploy.method` is an **open DEFERRED decision** (D-AUDRS-453). **Build-handover state is unaffected** (owner brief §6.3).
