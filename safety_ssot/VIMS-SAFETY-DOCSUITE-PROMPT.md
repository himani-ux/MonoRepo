# VIMS Safety Module — Docsuite Generation Prompt (v2)

**Use this prompt to dispatch parallel documentation agents after Session 5 close (2026-04-17). Feed it verbatim to each Agent call, specifying which doc to produce.**

---

<role>
You are a technical documentation architect for the **VIMS Safety Module** — a migration of the safety management system from the legacy **eMarineSoft** platform to the new **VIMS** (Vessel Information Management System) platform. Your output becomes the canonical knowledge base that AI coding tools execute against with zero ambiguity. Every document you create is a constraint that prevents hallucination. You work within maritime safety management conventions (IMO ISM Code 2010 amendments, SOLAS Ch IX, MARPOL Annex I, flag-state reporting, DNV M-SCAT RCA, KSM SSQE Manual Rev 01 Feb 2026).
</role>

<glossary>
Expand these role/term abbreviations on first use in any document you produce. Do not re-define after first use.

| Term | Expansion |
|------|-----------|
| DPA  | Designated Person Ashore (ISM Code §4) |
| FM   | Fleet Manager |
| TD   | Technical Director |
| HOD  | Head of Department (onboard: Chief Officer, Chief Engineer, or deck/engine senior) |
| CO   | Chief Officer |
| CE   | Chief Engineer |
| SO   | Safety Officer (onboard designated per SOLAS Reg VI) |
| SCM  | Safety Committee Meeting |
| SOI  | Safety Officer Inspection |
| MoC  | Management of Change |
| RCA  | Root Cause Analysis |
| CA   | Corrective Action |
| PA   | Preventive Action |
| ALARP | As Low As Reasonably Practicable |
| SMC  | Serious Marine Casualty (IMO Casualty Investigation Code) |
| MC   | Marine Casualty (IMO) |
| MI   | Marine Incident (IMO) |
| WRH  | Work & Rest Hours module |
| CMS  | Crew Management System module |
| PMS  | Planned Maintenance System module |
| SSQE | Safety, Security, Quality & Environment (KSM Manual) |
</glossary>

<mission>
The interrogation phase is **COMPLETE**. Across 5 sessions and 21 rounds, **159 requirements decisions have been locked** covering:

- **Incident Reporting** — 9-phase workflow with IMO SMC/MC/MI classification + internal risk band, ALARP gate, causal layering Immediate/Intermediate/Root over M-SCAT, multiple root causes by default, Chain of Custody, 10-section PDF template, 8 bias guards
- **Near Miss Reporting** — reporter anonymity, Low vs High priority triage, reporter visible only to DPA + FM
- **Safety Committee Meetings** (SCM) — Regular monthly + Ad-Hoc meetings hosted by Master or CO, same form + `meeting_type` differentiation, aligns with SSQE §9
- **Safety Officer Inspections** (SOI) — 13 areas × 329 items, paper-first no-scan flow with unique-ID checklist, Section 12 Cross-cutting Safety & Culture once per 3-month cycle, state pill label "SOI Compliance %"

Your job: take the locked specification (see `<inputs>`) and produce the **11-document canonical docsuite** under `VIMS-Safety-Module/`. These documents become the single source of truth. Nothing gets built without a corresponding document. The docsuite must interlock — PRD feature IDs must be referenced by IMPLEMENTATION_PLAN steps, BACKEND_STRUCTURE tables must match APP_FLOW data contracts, DESIGN_SYSTEM tokens must be cited by FRONTEND_GUIDELINES.
</mission>

<reading_budget>
**SSOT is 134KB — reading it fully will exhaust agent context.** Use targeted retrieval:

1. **Grep first, Read second.** Grep the SSOT by decision ID (`D-XXX-NN`, `D-GAP-[A-M]\d+`) and section anchor (`## §6`, `## Round 20`) rather than full-file reads.
2. **Read only sections ≤3KB at a time** when you need body content. Use `offset` + `limit` on the Read tool.
3. **Do NOT re-read source PDFs** (DNV pack, SSQE Manual, DUMMY-SAFETY-PDFS) — use the derived wikis (`VIMS-SAFETY-DNV-MSCAT-ANALYSIS.md`, `VIMS-SAFETY-JIBE-ANALYSIS.md`) or the SSOT's decision log.
4. **For CSV seed data,** read column headers via `head -1` then sample-read 5–10 rows for structure. Do not read full CSVs unless producing the full seed-load migration.
5. **For the Reporting sibling module,** read only the specific section you are inheriting from — not the whole file.
</reading_budget>

<inputs>
All canonical inputs exist at `/Users/prince/Documents/Project reserch/`. Do not invent facts — cite by file path.

**Primary spec (authoritative — 159 decisions live here):**
- `VIMS-SAFETY-MODULE-SSOT.md` (~1600+ lines, 134KB). §6 contains every D-* decision ID. Grep before reading.
- `VIMS-SAFETY-REQUIREMENTS-INTERROGATION.md` (86KB) — 21-round Q&A audit trail; consult only when D-* context is ambiguous.
- `VIMS-SAFETY-GAP-ANALYSIS.md` (16KB) — Session 5 artifact; maps 85 deduped gaps → D-GAP-A/B/C/D/E/F/G/H/I/J/M/DESIGN decisions.

**Reference wikis (use instead of re-reading source PDFs):**
- `VIMS-SAFETY-DNV-MSCAT-ANALYSIS.md` — DNV Practical Incident Investigation & RCA pack (27 files condensed).
- `VIMS-SAFETY-JIBE-ANALYSIS.md` — JiBe platform UI-pattern analysis for parity benchmarking.

**Seed data (already extracted — ready for import, do NOT re-derive):**

| File | Rows | Columns |
|------|------|---------|
| `safety-reference-data/mscat_taxonomy.csv` | 174 | `category_id, category_name, subcode_id, subcode_description, cause_type` — includes new **10.15 Design/MOC Governance** (Round 21) |
| `safety-reference-data/immediate_causes.csv` | 52 | `category_id, category_name, subcode_id, subcode_description, cause_type` — 28 Substandard Acts + 24 Conditions |
| `safety-reference-data/loss_types.csv` | 7 | `loss_type_id, loss_type_name, description` |
| `safety-reference-data/soi_checklist_v1.csv` | 329 | `area_id, area_name, subsection_id, subsection_name, item_number, description, tier` — 317 baseline (12 physical areas incl. Compressor House) + 12 cross-cutting |

**Regulatory & organizational reference:**
- `SSQE Manual- Rev 01 Feb 2026/` (297 pages). §9 = meetings, §11 = incidents, committee roles, signature authorities. Cite as: *"KSM SSQE Manual Rev 01 Feb 2026 §X.Y"*.
- `2023_DNV Practical Incident Investigation and Root Cause Analysis/` — DO NOT re-analyze; use the wiki.
- `Safety Officer Inspection/` — SQE S 608 xlsx + supporting docs.
- `Incident investigation/` — Round 21 reference pack (TapRoot, ABS RCA, VMTC-RAII, IMO/TC RCA guidance, RightShip Lessons Learned, KAIZEN Manual, Nautical Institute 2019).

**Dummy PDFs (visual validation complete Session 4):**
- `DUMMY-SAFETY-PDFS/01_INCIDENT_REPORT_DUMMY.pdf`
- `DUMMY-SAFETY-PDFS/02_NEAR_MISS_REPORT_DUMMY.pdf`
- `DUMMY-SAFETY-PDFS/03_SAFETY_COMMITTEE_MEETING_DUMMY.pdf`
- `DUMMY-SAFETY-PDFS/04_SAFETY_OFFICER_INSPECTION_DUMMY.pdf`

**Proven docsuite pattern (clone structure, NOT content):**

| Sibling file | Size | Inherit what? |
|--------------|------|---------------|
| `VIMS-Reporting-Module/TECH_STACK.md` | 25KB | **Inherit verbatim:** framework versions, Node/React/DB/ORM versions, hosting, CI/CD choices. **Author fresh:** Safety-specific libraries (PDF renderer, FTS engine stub, barcode lib for SOI unique ID). |
| `VIMS-Reporting-Module/DESIGN_SYSTEM.md` | 31KB | **Inherit verbatim:** color palette (all hex), typography scale, spacing base-unit + multipliers, border-radius values, shadow definitions, breakpoints, animation durations, themes. **Author fresh:** risk band palette, causal-layer hierarchy tokens, anonymity indicator, signature block variants. |
| `VIMS-Reporting-Module/FRONTEND_GUIDELINES.md` | 36KB | **Inherit verbatim:** component architecture rules, state management approach, naming conventions. **Author fresh:** Safety component prefix rules, 9-phase stepper pattern, SOI paper-first download flow. |
| `VIMS-Reporting-Module/BACKEND_STRUCTURE.md` | 106KB | **Inherit verbatim:** auth model, RBAC patterns, API contract conventions, migration patterns. **Author fresh:** every `safety_*` table, cross-module live-join contracts. |
| `VIMS-Reporting-Module/APP_FLOW.md` | 55KB | **Clone layout pattern only** — author all Safety screens/routes fresh. |
| `VIMS-Reporting-Module/IMPLEMENTATION_PLAN.md` | 121KB | **Clone phase-numbering pattern only** — author all Safety phases fresh. |
| `VIMS-Reporting-Module/CLAUDE.md` | 22KB | **Clone section structure** — author all Safety-specific rules fresh. |
| `VIMS-Reporting-Module/PRD.md` | 72KB | **Clone user-story + acceptance-criteria format** — author all Safety features fresh. |
| `VIMS-Reporting-Module/LESSONS.md` | 2KB | **Clone entry format** — author Safety-specific lessons fresh. |

- `VIMS-REPORTING-MODULE-SSOT.md` — for cross-module contract verification.

**Cross-module contracts (same-DB live joins, no sync staleness):**
- `WRH_CANONICAL_SINGLE_SOURCE_OF_TRUTH.md` — timezone reuse via `wrh_ship_time_config` (D-GAP-M26); SCM attendance warn-don't-block (D-GAP-M11).
- `PMS_SINGLE_SOURCE_OF_TRUTH.md` — **DECOUPLED** per D-GAP-I1, no in-VIMS integration.
- `PURCHASE_MODULE_SINGLE_SOURCE_OF_TRUTH.md` — CA → Purchase Req hard FK (D-GAP-M12).
- `ssot_auth_specific.md` — platform auth + RBAC inheritance.

**Target output folder:** `VIMS-Safety-Module/` (exists, currently empty).
</inputs>

<database_naming_convention>
**This is non-negotiable and overrides any contradictory usage in the SSOT.**

The VIMS platform (verified against `VIMS-Reporting-Module/BACKEND_STRUCTURE.md` §line 983–984 and all 23 `CREATE TABLE` statements in that file) uses two table prefixes:

| Prefix | Purpose | Examples in existing DB |
|--------|---------|--------------------------|
| `vims_*` | **Module-specific transactional tables** (owned by one module) | `vims_form_config`, `vims_off_hire_event`, `vims_port`, `vims_audit_trail`, `vims_ets_leg`, `vims_fuel_type`, `vims_marpol_sounding` |
| `master_*` | **Shared cross-module reference/master data** (maintained centrally, consumed by many modules) | `master_role`, `master_RoleByVessel`, `master_applied_rank`, `master_notification`, `master_Lube_oil` |

**⚠ The SSOT (`VIMS-SAFETY-MODULE-SSOT.md`) currently uses the bare `safety_*` prefix.** This is historical drift from Session 1–4 when the naming convention had not yet been reconciled with VIMS. **Every docsuite agent must translate on output** per this mapping:

### Safety module table translation map

**Module tables (transactional, Safety-owned) → `vims_safety_*`**

| SSOT name | Docsuite name | Purpose |
|-----------|---------------|---------|
| `safety_incident` | `vims_safety_incident` | Master record; `record_type` discriminator covers both incident and near-miss (SSOT §2B-Near-Miss) |
| `safety_incident_phase_log` | `vims_safety_incident_phase_log` | Append-only state-change audit |
| `safety_field_history` | `vims_safety_field_history` | Field-level edit log (D-EDGE-10) |
| `safety_soi_inspection` | `vims_safety_soi_inspection` | SOI event master |
| `safety_soi_inspection_area` | `vims_safety_soi_inspection_area` | Which areas each event covered |
| `safety_soi_finding` | `vims_safety_soi_finding` | Structured findings per event |
| `safety_soi_vessel_area_map` | `vims_safety_soi_vessel_area_map` | Per-vessel applicable flag + last-inspected timestamps |
| `safety_soi_applicability_log` | `vims_safety_soi_applicability_log` | D-GAP-M19 audit of `applicable=false` decisions |
| `safety_soi_trainee` | `vims_safety_soi_trainee` | Trainee FKs per inspection (up to 3) |
| `safety_scm_meeting` | `vims_safety_scm_meeting` | SCM event master (Regular + Ad-Hoc) |
| `safety_scm_attendance` | `vims_safety_scm_attendance` | WRH-joined attendance log |
| `safety_scm_agenda` | `vims_safety_scm_agenda` | Agenda items + decisions |
| `safety_corrective_action` | `vims_safety_corrective_action` | CA with `purchase_req_id` hard FK (D-GAP-M12) |
| `safety_recommendation` | `vims_safety_recommendation` | Corrective / Preventive / Lessons tiers |

**Reference/master data tables (seeded, DPA-maintained, cross-module consumable) → `master_*`**

| SSOT name | Docsuite name | Source | Rows |
|-----------|---------------|--------|------|
| MSCAT taxonomy lookup | `master_mscat_taxonomy` | `safety-reference-data/mscat_taxonomy.csv` | 174 |
| Immediate causes lookup | `master_immediate_causes` | `safety-reference-data/immediate_causes.csv` | 52 |
| Loss type lookup | `master_loss_types` | `safety-reference-data/loss_types.csv` | 7 |
| `safety_soi_area` | `master_soi_area` | SOI §12 derivation | 13 |
| `safety_soi_area_item` / `safety_soi_item` | `master_soi_area_item` | `safety-reference-data/soi_checklist_v1.csv` | 329 |
| `safety_soi_checklist_version` | `master_soi_checklist_version` | Versioned templates, DPA-maintained | varies |
| `safety_incident_type` (11 rows per SSOT §2B.5) | `master_safety_incident_type` | Enum table | 11 |
| 8 bias guards (Round 21 R12) | `master_safety_bias_guard` | Enum table | 8 |

**Existing VIMS masters Safety consumes (do NOT duplicate):**
- `master_role` — RBAC role definitions
- `master_RoleByVessel` — office-user vessel scoping
- `master_applied_rank` — rank normalization
- `master_notification` — shared notification channel

**Rule:** If an agent sees `safety_X` in the SSOT, classify it:
- **Is it transactional / owned by Safety?** → `vims_safety_X`
- **Is it reference data consumed by >1 module, or DPA-maintained seed data?** → `master_X` (drop the `safety_` infix if the domain is clear from table name; keep it if disambiguation needed, e.g., `master_safety_incident_type` is fine)

**Coverage check must verify no `safety_*` (without `vims_` or `master_` prefix) appears in any docsuite output.**
</database_naming_convention>

<vims_integration>
The Safety module is a **child module within the VIMS monorepo** — it does not live as a standalone app. Folder structure mirrors the Reporting module (verified from `VIMS-Reporting-Module/IMPLEMENTATION_PLAN.md` §Phase 0 Steps 0.1–0.4).

### Backend location (Django, shared DB `ksm_cms_live`)

```
<vims-repo-root>/
├── apps/
│   ├── reporting/          ← sibling module (exists)
│   ├── inspection/         ← sibling module (exists)
│   └── safety/             ← NEW — Safety module lives here
│       ├── __init__.py
│       ├── apps.py         ← Django AppConfig (name = 'apps.safety')
│       ├── urls.py         ← Root URL namespace, mounted at /api/safety/
│       ├── admin.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py     ← BaseSafetyRecord abstract (vessel_id, state, created_by, updated_by, is_deleted, schema_version)
│       │   ├── incident.py ← vims_safety_incident + vims_safety_incident_phase_log + vims_safety_field_history
│       │   ├── soi.py      ← vims_safety_soi_* tables
│       │   ├── scm.py      ← vims_safety_scm_* tables
│       │   ├── actions.py  ← vims_safety_corrective_action + vims_safety_recommendation
│       │   └── reference.py ← Read-only ORM wrappers for master_mscat_taxonomy, master_immediate_causes, master_loss_types, master_soi_area, master_soi_area_item, master_safety_incident_type, master_safety_bias_guard
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py     ← Inherit BaseRepository from reporting (SP wrapper pattern)
│       │   ├── incident_repo.py
│       │   ├── soi_repo.py
│       │   ├── scm_repo.py
│       │   └── exceptions.py
│       ├── authentication/
│       │   ├── __init__.py
│       │   ├── permissions.py  ← HasFormPermission / HasProcessPermission for SAF_F_* / SAF_P_* IDs (mirror RPT_F_* / RPT_P_* pattern)
│       │   ├── backends.py     ← Reuse VIMS SimpleJWT config
│       │   ├── vessel_scope.py ← Reuse master_RoleByVessel scoping + Crew_Onboarding_History for ship-side
│       │   └── anonymity.py    ← D-GAP-J1 enforcement: strip reporter identity from serializers for non-DPA/FM roles
│       ├── views/
│       ├── serializers/
│       └── migrations/
│           └── 0001_initial.py ← All vims_safety_* CREATE TABLEs + seed-load for master_* from safety-reference-data/
├── config/
│   └── urls.py             ← Add include('apps.safety.urls') under /api/safety/
└── tests/
    └── safety/             ← pytest tests mirror tests/reporting/ structure
        ├── test_db_connection.py
        ├── test_auth.py
        ├── test_permissions.py
        ├── test_vessel_scope.py
        ├── test_anonymity.py  ← Near-miss reporter hidden from Master/HOD, visible to DPA/FM
        └── test_*.py per feature
```

### Frontend location (React 18 + TypeScript + Vite)

```
<vims-repo-root>/src/
├── routes/
│   ├── reporting/      ← sibling (exists)
│   └── safety/         ← NEW
│       ├── index.tsx   ← Lazy-loaded route defs for all /safety/* paths; each wrapped with PermissionGate(SAF_F_*)
│       ├── layout.tsx  ← Safety module chrome (breadcrumbs, vessel dropdown slot)
│       ├── incident/   ← per-phase sub-routes
│       ├── near-miss/
│       ├── scm/
│       └── soi/
├── components/
│   ├── reporting/      ← sibling (exists)
│   └── safety/         ← NEW
│       ├── shared/
│       │   ├── signature-block.tsx
│       │   ├── anonymity-badge.tsx
│       │   ├── mscat-picker.tsx
│       │   ├── bias-guard-checklist.tsx
│       │   ├── barrier-analysis-canvas.tsx
│       │   ├── causal-layer-tabs.tsx
│       │   └── soi-finding-row.tsx
│       ├── incident/
│       ├── near-miss/
│       ├── scm/
│       └── soi/
├── hooks/
│   └── safety/         ← NEW — useAuth, use<Feature> hooks per SAF_F_*/SAF_P_* IDs
├── stores/
│   └── safety/         ← NEW — Zustand stores for draft incident state, SOI selected areas, etc.
├── schemas/
│   └── safety/         ← NEW — Zod schemas per phase per form (schema_version column on vims_safety_incident)
└── tests/frontend/safety/
```

### Permission ID namespace

Mirror Reporting's `RPT_F_*` / `RPT_P_*` pattern:
- `SAF_F_*` — Form IDs (e.g., `SAF_F_001` = Incident form, `SAF_F_002` = Near Miss, `SAF_F_003` = SCM, `SAF_F_004` = SOI)
- `SAF_P_*` — Process IDs (e.g., `SAF_P_001` = Create, `SAF_P_002` = Submit to office, `SAF_P_003` = Send back, `SAF_P_004` = Approve/Close)

Permission IDs go into the shared `msc_profiles` auth chain — Safety does not maintain its own permission table.

### URL routing

- Backend API: `/api/safety/incidents/`, `/api/safety/near-miss/`, `/api/safety/scm/`, `/api/safety/soi/`
- Frontend: `/safety/incidents/`, `/safety/near-miss/`, `/safety/scm/`, `/safety/soi/`

### Integration touchpoints (already in parent VIMS)
- **DB connection:** `ksm_cms_live` (shared; Safety models register in `apps/safety/models/` and use the existing router)
- **Auth:** reuse `SimpleJWT` config from VIMS platform; no new auth layer
- **Notifications:** write to `master_notification` table — shared queue consumed by VIMS platform notifier
- **Vessel scoping:** reuse `master_RoleByVessel` (office) + `Crew_Onboarding_History` (ship) — no duplication
- **Sidebar:** Safety group wrapped in `PermissionGate(SAF_F_*)`; hidden for users without any Safety form_ids

### BACKEND_STRUCTURE.md must document
- The full folder tree above
- Django app registration step (`INSTALLED_APPS += ['apps.safety']`)
- URL include step (`path('api/safety/', include('apps.safety.urls'))`)
- DB router confirmation — Safety uses the same `ksm_cms_live` connection, not a separate DB
- Migration ordering: Safety's `0001_initial.py` depends on `master_role`, `master_RoleByVessel`, `master_applied_rank`, `Crew_Onboarding_History` being present (platform precondition)

### IMPLEMENTATION_PLAN.md Phase 0 must include
- Step 0.1 Django project structure: `apps/safety/` scaffolding (mirror Reporting Step 0.1)
- Step 0.2 Base models + auth (mirror Reporting Step 0.2, add `anonymity.py`)
- Step 0.3 SP Wrapper base (mirror Reporting Step 0.3)
- Step 0.4 React route structure (mirror Reporting Step 0.4)
- Step 0.5 Seed-load `master_*` from `safety-reference-data/` CSVs
</vims_integration>

<feature_id_taxonomy>
All feature IDs use prefix `FEAT-SAF-<domain>-<seq>` where `<seq>` is 3-digit zero-padded:

| Domain | Scope |
|--------|-------|
| `INC`   | Incident Reporting (9-phase workflow) |
| `NM`    | Near Miss Reporting |
| `SCM`   | Safety Committee Meeting (Regular + Ad-Hoc) |
| `SOI`   | Safety Officer Inspection |
| `XMOD`  | Cross-module contracts (Reporting / WRH / CMS / Purchase / PMS) |
| `PDF`   | PDF generation (10-section template per D-PDF-01) |
| `AUDIT` | Audit trail, signatures, field history |
| `DASH`  | Dashboards, reporting, lessons-learned surfacing |
| `RBAC`  | Role-based access control specifics |

Examples: `FEAT-SAF-INC-001` = Incident Phase 1 intake; `FEAT-SAF-SOI-012` = SOI paper-first download; `FEAT-SAF-XMOD-004` = WRH attendance join.
</feature_id_taxonomy>

<documents>
Generate these in order. Each document must cross-reference others by exact decision IDs (D-*, D-GAP-*), feature IDs (FEAT-SAF-*), table names, and file paths. No placeholder content. No "TBD" sections. If blocked, use the BLOCKED stub format (see `<blocked_stub>`).

All documentation files are `.md` format. Progress is `.txt` format.

### Markdown style conventions (all docs)
- **H1** = doc title only (once per file)
- **H2** = major sections
- **H3** = sub-sections
- **Tables over bullets** for schemas, API contracts, role matrices, seed data, state transitions
- **Fenced code blocks** for SQL, API examples, file paths
- Cite decision IDs inline: `(D-GAP-I2)`, `(D-PDF-01)`
- Cite feature IDs inline: `(FEAT-SAF-INC-001)`
- Cite SSOT sections: `(see SSOT §6.3)`

## The 9 canonical docs:

### 1. `PRD.md` — Product Requirements
**Target length:** ~70–90 KB (benchmark: Reporting PRD is 72KB).

Every feature with acceptance criteria, user stories, priority. Use `FEAT-SAF-<domain>-<seq>` taxonomy above. Cover:
- **Incident module** — all 9 phases (Intake → Notifications → Evidence → Sequence → Analysis → Recommendations → Actions → Verification → Closure)
- **Near Miss module** — reporter anonymity, Low/High triage
- **SCM Regular + SCM Ad-Hoc** — same form, RBAC diff
- **SOI** — 13 areas, 329 items, paper-first, Section 12 quarterly

Each feature cites the governing D-* decision(s). Priority tiers: **V1 (must-ship), V1.1 (stretch), V2 (deferred)**.

**Self-check rubric** (verify before returning):
- ≥40 `FEAT-SAF-*` IDs total
- Every V1 feature cites ≥1 D-* or D-GAP-* decision
- Every V1 feature has: user story, acceptance criteria (≥3 bullets), priority, dependencies
- All 9 Incident phases covered
- All 13 SOI areas referenced
- SCM Regular and SCM Ad-Hoc both present

### 2. `APP_FLOW.md` — User Journeys & Screen Contracts
**Target length:** ~50–65 KB.

Every screen, every route, every user journey. Roles: **Shore (DPA, FM, TD, HOD), Ship (Master, CO, CE, SO, HOD, Reporter)**. Per screen document:
- Route path (e.g., `/safety/incident/:id/phase-3`)
- Data loaded on mount (SQL source, live joins)
- Empty state
- Error state (validation / network / auth)
- Navigation logic
- Signature/approval transitions per SSQE §11

Include the Near Miss anonymity boundary (reporter hidden from Master/HOD, visible to DPA + FM only — D-GAP-J1).

**Self-check rubric:**
- Every `FEAT-SAF-*` from PRD maps to ≥1 screen or route
- Every screen documents all 4 states (loaded / empty / error / loading)
- Role-permission matrix present
- Cross-module navigation paths explicit (e.g., Incident → Daily Report for MSC-MEPC.3 position)

### 3. `TECH_STACK.md` — Frameworks, Versions, Hosting
**Target length:** ~20–30 KB.

Version-lock everything. Inherit from Reporting `TECH_STACK.md` — do not re-invent platform choices. Document:
- Same-DB live joins (D-GAP-I2): no ETL / sync to CMS / Reporting / WRH / Purchase
- Platform inheritance (D-GAP-F4/G3/H1): monitoring, backup, performance
- **No crypto in V1** (D-GAP-D2/G2): no hash chains, no legal-hold
- FTS engine = build-time deferral (Round 20) — mark as decision pending
- PDF library for 10-section template
- Offline behavior for paper-first SOI (download only, no scan upload)

**Self-check rubric:**
- Every dependency has exact semver
- Hosting + region specified
- Every integration documented with API version
- Cost estimate per service
- No "latest" / "TBD" / "recommended"

### 4. `DESIGN_SYSTEM.md` — Visual Language
**Target length:** ~28–38 KB.

Inherit all base tokens verbatim from Reporting `DESIGN_SYSTEM.md`. Add Safety-specific tokens only where D-GAP-DESIGN-* demands. Document:
- Risk band color mapping (IMO SMC/MC/MI + internal Low/Med/High/Critical)
- State pill values — including the renamed **"SOI Compliance %"** (D-GAP-DESIGN-01, NOT "Inspection Compliance %")
- Causal layer visual hierarchy (Immediate / Intermediate / Root)
- Corrective / Preventive / Lessons taxonomy (Round 21 R13)
- Signature block variants (Reporter / Master / HOD / DPA / FM)
- Anonymity indicator (eye-off icon)
- WCAG AA compliance per Round 20

**Self-check rubric:**
- Every color has hex + semantic name
- Every typography level has exact size/weight/line-height
- Spacing scale present
- Breakpoints present
- All inherited Reporting tokens cited by name (don't restate, reference)
- Safety-specific tokens cite their D-GAP-DESIGN-* decision

### 5. `FRONTEND_GUIDELINES.md` — Engineering Rules
**Target length:** ~30–45 KB.

Inherit architecture rules from Reporting. Component prefix: `Safety*` (e.g., `SafetyIncidentPhase3.tsx`). Document:
- Mobile-first mandate (vessel tablets are primary SOI device)
- Responsive breakpoints from DESIGN_SYSTEM
- 9-phase stepper pattern
- Form state for incident draft (local persistence + server reconciliation)
- Reusable Safety sub-components: `MScatPicker`, `BiasGuardChecklist`, `BarrierAnalysisCanvas`, `SoiFindingRow`, `SignatureBlock`, `CausalLayerTabs`, `AnonymityBadge`

**Self-check rubric:**
- Component hierarchy diagram or tree
- Naming convention rule stated once
- File structure example
- State management approach cited
- Mobile-first test mental model present

### 6. `BACKEND_STRUCTURE.md` — Database, APIs, Auth
**Target length:** ~90–120 KB.

Every table, column, type, relationship. **Follow the VIMS naming convention exactly (see `<database_naming_convention>` above):**
- Transactional, Safety-owned → `vims_safety_*`
- Reference/seed data → `master_*`
- Consumed existing masters (`master_role`, `master_RoleByVessel`, `master_applied_rank`, `master_notification`) — do NOT duplicate

Document:
- Folder location per `<vims_integration>` — `apps/safety/` in the VIMS monorepo, not a standalone app
- Full schema for Incident / Near Miss (same table via `record_type` discriminator) / SCM / SOI using `vims_safety_*` prefix
- `master_*` lookup tables seeded from `safety-reference-data/` (174 / 52 / 7 / 329 rows — map CSV column headers to DDL columns exactly)
- `vims_safety_field_history` audit table (schema is Round 20 build-time deferral — flag it)
- Django app registration (`INSTALLED_APPS`), URL include (`/api/safety/`), DB connection reuse (`ksm_cms_live`)
- Migration ordering: Safety `0001_initial.py` depends on platform masters existing first
- **Build-time deferrals list — render as a table:**

| # | Deferred item | Resolution owner | Required by phase |
|---|---------------|------------------|-------------------|
| 1 | `safety_incident` field ENUMs and nullability | Backend lead | Phase 1 |
| 2 | `safety_field_history` column shape (TEXT vs JSON vs typed + content_hash) | Backend lead | Phase 1 |
| 3 | Soft-archive implementation (`archived_at NULL` vs `is_archived BIT` vs partition) | Backend lead | Phase 0 |
| 4 | `safety_recommendation` cardinality (1-per-tier vs child table) | Backend lead | Phase 1 |
| 5 | `safety_soi_finding` state ENUM + Carried-Forward semantics | Backend lead | Phase 4 |
| 6 | `safety_incident_phase_log` table shape | Backend lead | Phase 1 |
| 7 | WRH lookback window / query timeout for SCM attendance | Backend + WRH lead | Phase 3 |
| 8 | FTS engine choice (Elasticsearch / PG-FTS / platform default) | Platform | Phase 7 |
| 9 | Dashboard period persistence per user session | Frontend lead | Phase 7 |
| 10 | Paper-format PDF vs Excel layout (barcode/QR for unique ID) | Product + Design | Phase 4 |
| 11 | Trainee rotation coverage % formula | Product | Phase 4 |
| 12 | 90-day counter reset timing (upload vs approval vs cron) | Backend lead | Phase 7 |

- Cross-module FK / live-join contracts:
  - Safety ↔ Reporting: MSC-MEPC.3 position from Daily Report, ±12h tolerance (D-GAP-M09)
  - Safety ↔ WRH: attendance rest-hour compliance warn-don't-block (D-GAP-M11), timezone via `wrh_ship_time_config` (D-GAP-M26)
  - Safety ↔ CMS: live join for SOI assistant lookup + incident crew assignment (D-GAP-I2)
  - Safety ↔ Purchase: `safety_corrective_action.purchase_req_id` hard FK (D-GAP-M12)
  - Safety ↔ PMS: **DECOUPLED** (D-GAP-I1), no FK, manual cross-reference only
- Paper-first SOI (D-GAP-E4): `safety_soi_event.checklist_generated_at` flips state; **no scan upload column**

**Self-check rubric:**
- Every table has: columns (name + type + nullable + default), PK, FKs, indexes
- Every API endpoint has: path (`/api/safety/...`), method, auth, request shape, response shape, error codes
- All 12 build-time deferrals rendered in the table
- Seed CSV column headers match `master_mscat_taxonomy` / `master_soi_area_item` / `master_loss_types` / `master_immediate_causes` DDL exactly
- No crypto language (no hash chains, no legal-hold)
- PMS nowhere has an FK to Safety tables
- **Zero occurrences of bare `safety_*` prefix.** Every module table uses `vims_safety_*`; every shared reference uses `master_*`
- Folder structure block present (Django `apps/safety/` + React `routes/safety/`, `components/safety/`, `hooks/safety/`, `stores/safety/`)
- Django AppConfig, URL include, and `INSTALLED_APPS` step documented
- DB router points to `ksm_cms_live` (not a new DB)
- Migration dependencies on platform masters stated

### 7. `IMPLEMENTATION_PLAN.md` — Master Blueprint
**Target length:** ~100–130 KB.

Numbered phases and steps. Each step lists:
- Exact files to create (full path under app repo)
- PRD feature IDs (`FEAT-SAF-*`)
- Tests to write (unit / integration / E2E — call out which)
- Dependencies on prior steps
- Dependency on sibling modules

Phases:
- **Phase 0** — VIMS monorepo scaffold: create `apps/safety/` (Django) + `routes/safety/`, `components/safety/`, `hooks/safety/`, `stores/safety/`, `schemas/safety/` (React), register `apps.safety` in `INSTALLED_APPS`, mount `/api/safety/` URL include, create `0001_initial.py` migration with all `vims_safety_*` tables, seed-load `master_*` tables from `safety-reference-data/` CSVs. Mirror Reporting Phase 0 Steps 0.1–0.5.
- **Phase 1** — Incident module (9 sub-phases → UI phases)
- **Phase 2** — Near Miss module (anonymity-first)
- **Phase 3** — SCM Regular + Ad-Hoc
- **Phase 4** — SOI (paper-first, 13-area checklist, Section 12 quarterly)
- **Phase 5** — Cross-module integrations (Reporting / WRH / CMS / Purchase)
- **Phase 6** — PDF generation (10-section template per D-PDF-01)
- **Phase 7** — Dashboards, reporting, lessons-learned
- **Phase 8** — Build-time deferral resolutions (one step per deferral row)

**This file is written once. It does not get modified during execution.**

**Self-check rubric:**
- Every PRD `FEAT-SAF-*` ID mapped to ≥1 step
- Every step has files + features + tests + dependencies
- Build-time deferrals all appear as Phase 8 steps
- No forward references (step N cannot depend on step > N)

### 8. `VALIDATION_RULES.md` — Input & Compliance Rules
**Target length:** ~15–25 KB.

Per Round 20 decisions:
- WCAG AA rules
- Rate limits per endpoint
- Minimum-detail rules (Incident narrative min-length, near-miss description min-length)
- Signature sequencing (Reporter → Master → HOD → DPA → FM)
- Timeline extension procedure (D-GAP-B2) — reuse VIMS extension flow, no deputy chains
- IMO SMC/MC/MI classifier validation — field alongside internal risk band (D-GAP-R08, reconciliation option b)
- ALARP gate on System-Actions (Round 21 R02)
- Multiple root causes — no artificial cap (Round 21 R03)
- Chain-of-custody + evidence preservation deadlines (Round 21 R04–R07, R10)
- Anonymity enforcement for Near Miss reporter (D-GAP-J1)

**Self-check rubric:**
- Every validation cites a D-* or Round 20/21 decision
- Every validation has: trigger condition, enforcement point (client / server / both), error message
- Regulatory validations cite the code edition (e.g., "ISM Code 2010 amendments §9.2")

### 9. `USER_GUIDE.md` — End-User Documentation
**Target length:** ~25–40 KB.

Role-scoped sections:
- Reporter (any crew)
- Shipboard HOD
- Safety Officer (SOI workflow)
- Master (signatures, Ad-Hoc SCM trigger)
- Shore DPA (owns investigation, anonymity visibility)
- Shore FM (budget approval on CA)

Cover paper-first SOI procedure explicitly: download PDF/Excel with unique ID → fieldwork on paper → file in ship SMS filing system → register findings digitally linked via unique ID.

**Self-check rubric:**
- Every role has a "day in the life" flow
- Every APP_FLOW route appears in at least one role's procedure
- Paper-first SOI procedure present with all 4 steps
- Near Miss anonymity explained to the Reporter role

## The session + governance files:

### 10. `CLAUDE.md` — AI Agent Governance
**Target length:** ~20–28 KB.

Read automatically at every session start. Contains project rules, constraints, Safety-specific conventions:
- **Module tables:** `vims_safety_*` prefix (NEVER bare `safety_*`)
- **Shared reference tables:** `master_*` prefix (seed from `safety-reference-data/`)
- **Feature IDs:** `FEAT-SAF-<INC/NM/SCM/SOI/XMOD/PDF/AUDIT/DASH/RBAC>-NNN`
- **Permission IDs:** `SAF_F_*` (forms) and `SAF_P_*` (processes)
- **Component prefix:** `Safety*` (e.g., `SafetyIncidentPhase3.tsx`)
- **Django app:** `apps.safety` registered in VIMS monorepo; API under `/api/safety/`
- **DB connection:** `ksm_cms_live` (shared with Reporting / Inspection / platform)

Plus these mandatory sections verbatim:

#### Workflow Orchestration
1. **Plan Mode Default** — Enter plan mode for any non-trivial Safety work (phase transitions, cross-module joins, regulatory classification, multi-signature flows). If something goes sideways, STOP and re-plan.
2. **Subagent Strategy** — Use subagents liberally. Offload research, exploration, parallel analysis. One task per subagent.
3. **Self-Improvement Loop** — After any user correction, update `LESSONS.md`. Write rules preventing recurrence. Review at session start.
4. **Verification Before Done** — Never mark complete without proof. Run tests, check logs, demo the 9-phase flow, demo paper-first SOI, demo anonymity boundary.
5. **Demand Elegance (Balanced)** — For non-trivial changes, pause and ask "is there a more elegant way?" Skip for simple fixes.
6. **Autonomous Bug Fixing** — Given a bug report, fix it. Point at logs, errors, failing tests — then resolve.

#### Protection Rules
- **No Regressions** — Safety touches Reporting / WRH / CMS / Purchase via live joins. Diff each sibling contract before merging.
- **No File Overwrites** — Never overwrite existing docs under `VIMS-Safety-Module/`. Create timestamped versions using suffix `-YYYYMMDD-HHMM` (e.g., `PRD-20260420-1430.md`). The un-suffixed file is always the current.
- **No Assumptions** — If it's not in the SSOT or one of the 159 D-* decisions, STOP and ask. Silence is not permission.
- **Design System Enforcement** — Check `DESIGN_SYSTEM.md` first. No invented colors/spacing/radii. Always "SOI Compliance %", never "Inspection Compliance %".
- **Mobile-First Mandate** — SOI runs on vessel tablets. Every component starts mobile.

#### Task Management
1. Plan → `tasks/todo.md` with checkboxes
2. Verify plan with user
3. Track progress inline
4. Explain changes at each step
5. Document results in `tasks/todo.md` review section
6. Capture lessons in `LESSONS.md`

#### Core Principles
- Simplicity First — minimal code impact per change
- No Laziness — root causes only, no temp fixes
- Minimal Impact — touch only what's necessary

#### Session Startup Sequence
1. Read `CLAUDE.md` (this file)
2. Read `progress.txt`
3. Read `IMPLEMENTATION_PLAN.md`
4. Read `LESSONS.md`
5. Write `tasks/todo.md`
6. Verify plan with user before executing

#### Arbitration Rule for Conflicts
When two documents conflict, the authority order is:
1. **SSOT** (`../VIMS-SAFETY-MODULE-SSOT.md`) — wins over all docsuite output
2. **BACKEND_STRUCTURE.md** — wins on data/schema disputes
3. **APP_FLOW.md** — wins on UI/navigation disputes
4. **PRD.md** — wins on scope/feature disputes
5. **DESIGN_SYSTEM.md** — wins on visual token disputes
6. **VALIDATION_RULES.md** — wins on input/compliance disputes

Reference every canonical doc as source of truth. SSOT is the spec ceiling — nothing outside its 159 decisions ships in V1.

### 11. `LESSONS.md` — The Learning File
**Target length:** starts ~3–5 KB; grows with corrections.

Seed with these Session 5 starter entries:

```markdown
## L-001 — External reference packs can reshape locked specs
**What happened:** Round 21 reference pack (TapRoot, ABS RCA, IMO RCA guidance) surfaced 23 enhancements after Session 4 had already "closed" the V1 spec. Causal layering (Immediate/Intermediate/Root) was added on top of M-SCAT as a result.
**Why:** "Interrogation complete" is a state-in-time, not permanence. External references introduce patterns the original interrogation didn't probe.
**Rule:** Before docsuite generation, always run a final gap-analysis pass against any new reference material the user contributes. Do not treat spec close as immutable.

## L-002 — Paper-first means no scan upload
**What happened:** Initial SOI design assumed scanned-PDF upload after paper fieldwork.
**Why:** User clarified (D-GAP-E4) that paper is filed in ship SMS filing system — scan upload is duplicative and creates a second source of truth.
**Rule:** When a workflow is "paper-first," the system generates → user downloads → paper becomes authoritative → findings registered digitally via unique ID only. No upload column, no scan endpoint.

## L-003 — Role persists, person may change
**What happened:** Early drafts had "Acting-DPA" and "Acting-CO" concepts.
**Why:** D-GAP-A3/A4 locked that ranks are always staffed; the person in the role changes via normal crew rotation but the role itself is continuous.
**Rule:** No "Acting-*" concepts anywhere. No deputy chains. No MD-escalation logic. Use the timeline-extension procedure (D-GAP-B2) as the universal escape valve.
```

Every future correction gets a new `L-###` entry: what went wrong, why, the rule that prevents recurrence.

## Session-bridge files (live in `VIMS-Safety-Module/`):

### `progress.txt`
Cross-session bridge. `.txt` not `.md`. Tracks built / in-progress / blocked / next. References `IMPLEMENTATION_PLAN.md` phase numbers. Initial content:

```
PROJECT: VIMS Safety Module
DOCSUITE GENERATED: 2026-MM-DD
CURRENT PHASE: Phase 0 — not started
STATUS: Awaiting build kickoff
NEXT STEP: Phase 0.1 — Platform scaffold per IMPLEMENTATION_PLAN.md
BLOCKED: none
LAST UPDATED: 2026-MM-DD HH:MM
```

### `tasks/todo.md`
In-session work plan. Created per-session, checkable items, disposable. Path: `VIMS-Safety-Module/tasks/todo.md`.
</documents>

<blocked_stub>
If you cannot complete a section from the 159 decisions + inputs, insert this exact stub format inline and continue:

```markdown
> **BLOCKED: <short label>**
> **Question:** <the specific question the user must answer>
> **Gap:** <which decision is missing, or which D-GAP-* doesn't cover this>
> **Impact:** <what downstream doc/feature depends on this>
```

Example:
```markdown
> **BLOCKED: FTS engine selection**
> **Question:** Elasticsearch, PostgreSQL FTS, or platform default?
> **Gap:** Round 20 deferred this to build-time; no D-* locks it.
> **Impact:** `FEAT-SAF-DASH-007` (incident search) cannot be fully specified in BACKEND_STRUCTURE §API.
```

Do NOT invent. Do NOT silently fail. Every blocker is surfaced.
</blocked_stub>

<cross_referencing>
Cascade:
- **PRD** defines features (FEAT-SAF-*) → cited by APP_FLOW screens + IMPLEMENTATION_PLAN steps
- **APP_FLOW** defines user experience → cites PRD features + BACKEND data contracts
- **TECH_STACK** defines what builds it → inherits Reporting, adds Safety libs
- **DESIGN_SYSTEM** defines how it looks → cites D-GAP-DESIGN-* decisions
- **FRONTEND_GUIDELINES** defines how it's engineered → cites DESIGN_SYSTEM tokens
- **BACKEND_STRUCTURE** defines how data works → cites cross-module FKs + live joins
- **VALIDATION_RULES** defines input/compliance → cites Round 20/21 decisions
- **USER_GUIDE** defines human procedure → cites APP_FLOW routes
- **IMPLEMENTATION_PLAN** is the master blueprint → references every PRD `FEAT-SAF-*` + BACKEND table + TECH_STACK dep

`CLAUDE.md` references all 9 canonical docs as law plus the SSOT as spec ceiling. `progress.txt` tracks position against IMPLEMENTATION_PLAN phases. `tasks/todo.md` breaks the current phase into session checkboxes. `LESSONS.md` prevents repeat mistakes.

Three levels of execution tracking: IMPLEMENTATION_PLAN is the map. `progress.txt` is the GPS pin. `tasks/todo.md` is the turn-by-turn directions.
</cross_referencing>

<coverage_check>
After all waves complete, produce `VIMS-Safety-Module/COVERAGE.md` — a matrix proving every D-* decision appears in the docsuite.

**Format:**

| Decision ID | PRD | APP_FLOW | TECH_STACK | DESIGN_SYSTEM | FRONTEND_GUIDELINES | BACKEND_STRUCTURE | IMPLEMENTATION_PLAN | VALIDATION_RULES | USER_GUIDE |
|-------------|-----|----------|------------|---------------|---------------------|-------------------|---------------------|------------------|------------|
| D-GAP-A3    | ✓   | ✓        | —          | —             | —                   | ✓                 | —                   | ✓                | ✓          |
| D-GAP-I2    | —   | ✓        | ✓          | —             | —                   | ✓                 | ✓                   | —                | —          |
| ... (all 159)

**Method:**
1. Grep SSOT §6 for every `D-*` and `D-GAP-*` ID — gives the denominator
2. For each ID, grep the 9 canonical docs
3. Mark ✓ if present, — if absent
4. **Any decision row with zero ✓ = BLOCKER.** Escalate before build.
5. Include footer: total decisions / coverage % / blockers.

This file is generated last and does not count toward the 11-doc target.

**Additional audits (run alongside the decision matrix):**

1. **Naming convention audit.** Grep every docsuite output for:
   - Bare `safety_[a-z]` (no `vims_` or `master_` prefix) → should be ZERO hits. Any hit = translation missed; blocker.
   - `vims_safety_*` count — should match the translation map's 14+ module tables
   - `master_*` references — confirm the 8 Safety-owned master tables present, plus the 4 existing VIMS masters consumed (`master_role`, `master_RoleByVessel`, `master_applied_rank`, `master_notification`)

2. **Folder structure audit.** Confirm `BACKEND_STRUCTURE.md` and `IMPLEMENTATION_PLAN.md` both document `apps/safety/` + React folders. Confirm no doc suggests a standalone app.

3. **DB connection audit.** Every SQL/migration/DDL example cites `ksm_cms_live` (not `eMarineSoft_live`, not a new DB name).

4. **Permission ID audit.** Every RBAC reference uses `SAF_F_*` / `SAF_P_*` (not `RPT_*`, not freeform names).

Report all four audits + the decision matrix in `COVERAGE.md`. Any audit failure = blocker for build kickoff.
</coverage_check>

<rules>
- **No generic advice.** Every statement specific to VIMS Safety (maritime ISM/SOLAS, KSM SSQE §9/§11, DNV M-SCAT, IMO SMC/MC/MI).
- **Version-lock everything.** Inherit exact versions from Reporting. Cite version string verbatim.
- **Regulatory citations are version-locked.** ISM Code 2010 amendments; MARPOL Annex I (consolidated 2022); SOLAS Ch IX (as amended); IMO Casualty Investigation Code (Resolution MSC.255(84)). Cite edition/year on first use.
- **DESIGN_SYSTEM and FRONTEND_GUIDELINES are two separate docs.**
- **IMPLEMENTATION_PLAN is the blueprint.** It does not get modified during execution — only `progress.txt` does.
- **progress is `.txt`, not `.md`.**
- **tasks/todo.md is disposable.**
- **No existing documentation files overwritten.** Timestamped suffix `-YYYYMMDD-HHMM.md` for revisions; un-suffixed file is always current.
- **No assumptions.** Outside the 159 decisions / SSOT / wikis → BLOCKED stub. Do not infer from DNV PDF or SSQE Manual directly — use the wikis.
- **No regressions.** Cross-module contracts (Reporting / WRH / CMS / Purchase) preserved exactly.
- **Mobile-first. Always.** SOI runs on vessel tablets.
- **Design system is law.** Tokens inherit from Reporting; only D-GAP-DESIGN-* justifies additions.
- **Role persists, person may change** (D-GAP-A3/A4). No Acting-* concepts.
- **Same-DB = live joins** (D-GAP-I2). No ETL/sync language.
- **No crypto in V1** (D-GAP-D2/G2). No hash chains, no legal-hold.
- **PMS is decoupled** (D-GAP-I1). No in-VIMS PMS integration.
- **Paper-first SOI has NO scan upload** (D-GAP-E4).
- **"SOI Compliance %"** (D-GAP-DESIGN-01) — never "Inspection Compliance %".
- **Near-miss reporter anonymity** (D-GAP-J1) — reporter hidden from Master/HOD.
- **Database naming is law.** `vims_safety_*` for module tables, `master_*` for shared reference. **Never bare `safety_*`** — that prefix in the SSOT is historical drift and MUST be translated on every docsuite output.
- **Module lives inside VIMS monorepo** at `apps/safety/` (Django) + `routes/safety/`, `components/safety/`, `hooks/safety/`, `stores/safety/`, `schemas/safety/` (React). Not a standalone app. Shared DB (`ksm_cms_live`), shared auth (SimpleJWT), shared notification queue (`master_notification`), shared vessel scoping (`master_RoleByVessel`).
- **Permission IDs** follow Reporting's pattern: `SAF_F_*` (forms) + `SAF_P_*` (processes) — stored in `msc_profiles`, not a new permission table.
- **SSOT wins on spec decisions. Naming convention wins on table names.** Arbitration order: `<database_naming_convention>` > `<vims_integration>` > SSOT > BACKEND > APP_FLOW > PRD > DESIGN_SYSTEM > VALIDATION_RULES.
- These documents are law. No AI coding tool deviates without explicit approval + SSOT amendment.
</rules>

<dispatch_instructions>
Launch one Agent per doc in parallel within each wave. Each agent receives:
1. This full prompt
2. The specific doc to produce (e.g., "Produce `VIMS-Safety-Module/PRD.md`")
3. Explicit read list — targeted, not full files
4. Instruction to write directly to target path
5. Instruction to run its **Self-check rubric** before returning and report pass/fail in its summary

**Dispatch waves:**

**Wave 1 (foundation, fully parallel):**
- `PRD.md`
- `TECH_STACK.md`
- `DESIGN_SYSTEM.md`
- `VALIDATION_RULES.md`

**Wave 2 (depend on Wave 1, parallel within wave):**
- `APP_FLOW.md` (needs PRD feature IDs)
- `FRONTEND_GUIDELINES.md` (needs DESIGN_SYSTEM tokens)
- `BACKEND_STRUCTURE.md` (needs TECH_STACK + VALIDATION_RULES)

**Wave 3 (depends on Wave 2):**
- `USER_GUIDE.md` (needs APP_FLOW routes)
- `IMPLEMENTATION_PLAN.md` (needs all Wave 1+2 outputs)

**Wave 4 (governance, last):**
- `CLAUDE.md` (references all 10 above)
- `LESSONS.md` (seed with L-001/002/003)
- `progress.txt` + `tasks/` scaffold

**Wave 5 (verification, single agent):**
- `COVERAGE.md` — generate the decision-coverage matrix. Report blockers.

Agents that cannot complete a section must emit a BLOCKED stub inline and continue — never fabricate.
</dispatch_instructions>
