# VIMS Safety Module — Application Flow (APP_FLOW)

> **Version:** 1.0
> **Last Updated:** 2026-06-15
> **Status:** Locked — ready for build
> **Authority:** PRD.md (FEAT-SAF-* IDs) · VIMS-SAFETY-MODULE-SSOT.md §6 (D-* / D-GAP-* decisions) · DESIGN_SYSTEM.md (state pills, signature blocks, reporter identity display) · VALIDATION_RULES.md (state-transition enforcement)
> **Pattern inherited from:** `VIMS-Reporting-Module/APP_FLOW.md` (layout / state / navigation contract only; every Safety screen authored fresh)

This document is the **screen contract** for every route the Safety Module exposes. It is the only place where route paths, role gates, on-mount data loads, and loaded / loading / empty / error states are specified together. BACKEND_STRUCTURE.md owns table DDL; FRONTEND_GUIDELINES.md owns component code; this file owns **which screen does what for whom**.

> **Incident workflow update (2026-07-06):** The implemented incident user flow is now simplified and sequentially numbered: Phase 1 Report Incident -> Phase 2 RCA (Root Cause Analysis) -> Phase 3 Corrective Action -> Phase 4 Preventive Action -> Phase 5 Add Evidence -> Phase 6 Office Review -> Phase 7 Loss Evaluation. Lessons Learned is removed from the visible workflow; its legacy URL redirects to Office Review. Backend `current_phase` values and route paths still keep older compatibility numbers. The read-only Final Record is removed from the visible workflow tabs and remains a direct/read-only legacy route only where needed for audit or old links. Older references in this document to a 9-phase catalog, a combined Next Actions phase, visible Final Record phase, resource handoff, user-entered IMO classifier, user-entered position block, mandatory bias-filter screens, Office Check wording, Check Actions wording, and a visible Lessons Learned phase are superseded by `safety_ssot/VIMS-SAFETY-MODULE-SSOT.md` section 3.0.

> **Incident edit-window update (2026-07-03):** Advancing an incident to a later phase does not lock earlier phase edits. User-facing RCA, Corrective Action, Preventive Action, and Add Evidence remain editable by authorized roles until office approval locks the record, and their save endpoints can be used even before the legacy backend `current_phase` reaches that old phase number. This covers RCA, facts/evidence helpers, Corrective Action, Preventive Action, and Evidence Documents. The edit lock starts when the incident state becomes `APPROVED`, `CLOSED`, or `SUPERSEDED`; submit/transition endpoints still enforce the ordered workflow.

> **Incident save-feedback update (2026-07-03):** Phase 2 RCA cause saves, Corrective Action / Preventive Action saves, and Phase 5 Evidence document/witness saves show an inline success message and automatically scroll to the saved-content area. This is a frontend acknowledgement/focus rule only; API payloads, validation, persistence, and workflow transitions are unchanged.

> **Incident RCA/action simplification update (2026-07-07):** Current Phase 2 RCA exposes Immediate Cause and Root Cause only. New Intermediate Cause submissions are rejected, and legacy Intermediate rows are displayed under Root Cause instead of as a separate current category. Current action capture is split into Corrective Action and Preventive Action screens. Corrective Action shows Description and Due date only, without the owner/checker card. Preventive Action shows Description, Due date, and one shared **How much will this reduce risk?** answer for the screen; it does not show Remaining risk, the "I confirm this will reduce risk" checkbox, theme, effort, or "Prevent It Happening Again" wording, and saved preventive cards do not repeat risk reduction per row. The action screens do not show or send the "Why is this needed?" recommendation-rationale field.

> **Incident phase-header and witness statement update (2026-07-06):** Incident phase tabs are the single visible phase number/name indicator; phase content areas do not repeat separate Phase X/phase-title header cards. Phase 4 supporting witness capture is labelled **Witness Statement**, opens `/phase-4/interviews/` directly, loads the incident vessel crew list with an **Other** typed-name option, captures **Remark**, and offers **Upload witness statement**.

> **Incident RCA edit update (2026-07-03):** Phase 2 saved Immediate Cause and Root Cause cards include an **Edit** action. Edit loads the saved cause into the RCA form and saves back to that existing cause row; users should not add a duplicate cause just to correct factor, cause, Other text, or reason.

> **Incident action/evidence edit update (2026-07-03):** Phase 3 Corrective Action, Phase 4 Preventive Action, and Phase 5 Add Evidence saved cards include **Edit**. Edit loads the saved action, document metadata, or Witness Statement into the same form and saves back to the existing row; users should not add duplicate rows just to correct saved content.

> **Incident Office Review update (2026-07-07):** Office Check is renamed **Office Review**. The Office Review screen includes an unrestricted **Office Comments/lesson learnt** textarea saved to `vims_safety_incident.office_comment` through migration `0052_incident_office_comment`. The comment is separate from the later closure reason and prints near the signature area in the incident PDF when present. Under D-MAINT-CR044, D-MAINT-CR049, D-MAINT-CR050, and D-MAINT-CR051, PIC and DPA can accept, close, send rework, or issue a selected-ship Fleet Alert for every incident risk band; the old RED/FM closer gate is legacy-only. Office-side users see Accept / Close, Fleet Alert, and Send for rework controls; ship-side users see the Office Comments/lesson learnt card, with "Office comment is not added yet." when no note exists. Office-side Phase 6 does not show Phase 7 acceptance-only PDF warning text.

> **Incident Loss Evaluation update (2026-07-07):** Visible Phase 7 is **Loss Evaluation**, served on the existing compatibility route `/safety/incidents/:id/phase-6/`. Authorized ship-side and office-side users with incident form access and vessel scope can open and save one editable `vims_safety_incident_loss_evaluation` row through `PATCH /api/safety/incidents/:id/phase-6/` without waiting for Office Review approval. Incident Report and Injury Report records show different Other Details, Cost Evaluation, and Estimated Costs fields. Closure through `/phase-6/close/` remains an office close action and requires a saved Loss Evaluation row plus a closure note.

**Glossary (first-use, per `<glossary>`):** **DPA** = Designated Person Ashore (ISM Code §4); **FM** = Fleet Manager; **TD** = Technical Director; **HOD** = Head of Department (onboard: CO or CE); **CO** = Chief Officer; **CE** = Chief Engineer; **SO** = Safety Officer (SOLAS Reg VI, COSWP 13.3.2); **SCM** = Safety Committee Meeting; **SOI** = Safety Officer Inspection; **MoC** = Management of Change; **RCA** = Root Cause Analysis; **CA / PA** = Corrective Action / Preventive Action; **ALARP** = As Low As Reasonably Practicable; **SMC / MC / MI** = Serious Marine Casualty / Marine Casualty / Marine Incident (IMO Casualty Investigation Code MSC.255(84)); **WRH** = Work & Rest Hours module; **CMS** = Crew Management System module; **PMS** = Planned Maintenance System module (**decoupled from VIMS — D-GAP-I1**); **SSQE** = Safety, Security, Quality & Environment (KSM Manual Rev 01 Feb 2026).

**Safety UUID identifier rule:** Route examples use `:id` as the path variable name, and for Safety-owned managed records that value is the UUID `id` primary key. The transitional `public_id` field is not part of the final Safety design. This identifier rule does not change any workflow state, role gate, validation, signature sequence, dashboard, export, PDF, or user-facing document number.

**Safety master/reference identifiers:** Safety-owned seeded master/reference endpoints return UUID `id` as the actual database primary key. Stable business keys remain unchanged and continue to drive workflow selections where already developed: `type_code`, `loss_type_id`, `subcode_id`, `area_id`, `version_label`, `guard_code`, and checklist item reference codes. External/shared VIMS master data is not converted.

---

## Table of Contents

1. [Role × Module Permission Matrix](#1-role--module-permission-matrix)
2. [Permission Model (SAF_F_* / SAF_P_*) & Sidebar Group](#2-permission-model)
3. [Route Map Summary](#3-route-map-summary)
4. [Incident Module — Current Screen Catalog](#4-incident-module--9-phase-screen-catalog)
5. [Near Miss Module — Screens & Reporter Identity](#5-near-miss-module)
6. [SCM Module — Regular + Ad-Hoc Screens](#6-scm-module)
7. [SOI Module — Paper-First 4-Step Journey](#7-soi-module)
8. [Dashboards, Search, Exports](#8-dashboards-search-exports)
9. [Cross-Module Navigation Paths](#9-cross-module-navigation-paths)
10. [Signature Sequencing (SSQE §11)](#10-signature-sequencing)
11. [Mobile / Tablet Breakpoints per Screen](#11-mobile--tablet-breakpoints)
12. [Appendix — FEAT-SAF-* → Screen Coverage Matrix](#12-appendix--feat-saf---screen-coverage-matrix)

---

## 1. Role × Module Permission Matrix

This is the canonical permission matrix for V1. "Y" = screen and primary actions are accessible; "R" = read-only; "—" = no access. Actions gated by band / state add finer constraints in each module section. Rank persists — no Acting-* concepts (D-GAP-A3 / A4 / FEAT-SAF-RBAC-004). The roles below are the eight defined in `<role>` of the dispatch brief (Shore: DPA · FM · TD · HOD-shore; Ship: Master · CO · CE · SO · HOD-onboard · Reporter).

> **Note.** *TD* does not own any Safety workflow action in V1 — TD reads dashboards and closed records. *HOD (shore)* = shore-side department head (e.g., Shore HSE Manager, Marine Superintendent) with read access + ability to flag/comment outside the formal record (same pattern as D-RBAC-04 for FM). *HOD (onboard)* = CO or CE acting as department head on the vessel. *Reporter* = any crew member initiating a Near Miss (`D-RBAC-11`), or providing a witness statement / minor incident intake on behalf of the ship.

> **CR-044 current authority override.** For Incident Office Review acceptance, closure, and send-back/rework, PIC and DPA can act for every risk band. Any older matrix wording that maps GREEN to PIC, YELLOW to DPA, or RED to FM is legacy-only for current Office Review.

### 1.1 Shore roles — module access

| Module / Surface | DPA | FM | TD | HOD (shore) |
|------------------|-----|----|----|-------------|
| Incident — create | — | — | — | — |
| Incident — investigate (GREEN / YELLOW) | R + comment | R + comment (D-RBAC-04) | R | R + comment |
| Incident — investigate RED (edit) | Lead | **Full edit (D-GAP-M06)** | R | R |
| Incident — Phase-7 acceptance | YELLOW closer | RED closer | — | — |
| Incident — re-open | GREEN/YELLOW | RED | — | — |
| Blame-fixation override | GREEN/YELLOW | RED | — | — |
| Near Miss — reporter identity visible | **Y** | **Y** | **Y** | **Y** |
| Near Miss — close (PIC role = VSU) | — | — | — | — |
| SCM — read fleet-wide | All | All | R | R (own vessels) |
| SCM — office comment + close | **Y** | **Y** | R | **Y (Marine Superintendent profile)** |
| SOI — read fleet-wide | All | R (fleet) | R | R |
| SOI — approve area-applicability false | **Y (D-GAP-M19)** | — | — | — |
| SOI — maintain 13-area template | **Y (exclusive)** | — | — | — |
| Dashboards (Safety Intelligence) | Y (+export) | Y (read only — D-GAP-M31) | Y | Y |
| Audit / taxonomy maintenance | **Y (exclusive, D-CFG-01/02/03)** | — | — | — |
| PDF export — auditor ZIP (D-PDF-02) | Y | R | R | R |

### 1.2 Ship roles — module access

| Module / Surface | Master | CO (default SO) | CE | SO* | HOD (onboard) | Reporter (any crew) |
|------------------|--------|------|----|-----|--------|----------|
| Incident — create (top-4) | Y | Y | Y | (inherits via CO/2E) | — (unless in top-4) | — |
| Incident — Phase 1 intake + scene control | Y | Y | Y | via CO | R | Witness-statement only |
| Incident — investigation lead GREEN | **Y** | assist | assist | — | assist | — |
| Incident — joint investigation YELLOW | **Y** (+ PIC) | assist | assist | — | assist | — |
| Near Miss — create | Y | Y | Y | Y | Y | **Y (any rank, D-RBAC-11)** |
| Near Miss — see reporter identity | **Y** | **Y** | **Y** | **Y** | **Y** | **Y** |
| SCM — create Regular | **Y (host)** | **Y (host)** | — | — | — | — |
| SCM — create Ad-Hoc | **Y (host)** | **Y (host)** | — | — | — | — |
| SCM — edit before office comment | **Y** | **Y** | — | — | — | — |
| SOI — safety-officer lead | — | **Y (default, SSQE §4.5.1)** | — | Y (if CO on leave toggle → 2/E via D-SOI-02) | — | — |
| SOI — area-applicability toggle → false (request) | **Y (Master requests; DPA approves)** | — | — | — | — | — |
| SOI — finding creation | — | Y (as SO) | — | Y | — | — |
| SOI — finding closure approve | **Y (D-SOI-07)** | — | — | — | — | — |
| SOI — paper-signature on checklist | Digital at approval (D-GAP-M15) | **Y (paper)** | — | **Y (paper)** | — | — |
| Dashboards (own vessel) | Y | Y | Y | Y | Y | R |
| Cross-vessel read-only (closed incidents) | **Fleet-wide (D-RBAC-09)** | — | — | — | — | — |

\* The **SO** row represents the Safety Officer assignment. In V1 CO is SO by default (SSQE §4.5.1); Master may toggle 2/E as alternate SO via D-SOI-02; no separate rank.

### 1.3 Summary — action-column authority (V1)

| Action | Authority |
|--------|-----------|
| Create Incident | Master, CO, CE, 2/E (top-4 per SSOT §3.4, enforced by `SAF_P_001`) |
| Create Near Miss | Any crew (D-RBAC-11, `SAF_P_001` scoped to `SAF_F_002`) |
| Create SCM Regular | Master or CO (`SAF_P_001` on `SAF_F_003` + role in `{MASTER, CO}`) |
| Create SCM Ad-Hoc | Master or CO (`SAF_P_001` on `SAF_F_003` + role in `{MASTER, CO}` + `meeting_type = 'AD_HOC'`) |
| Edit SCM before office comment | Master or CO |
| Add SCM Office Comment and close meeting | DPA, FM, Shore HOD, or Marine Superintendent profile `407EF017-0F1C-EF11-A9F1-F348983BAE6B` |
| Create SOI record | SO (CO or 2/E alternate, `SAF_P_001` on `SAF_F_004`) |
| Approve SOI finding closure | Master (`SAF_P_004` on `SAF_F_004`) |
| Approve area-applicability false | DPA (`SAF_P_010` on `SAF_F_004`) |
| Phase-6 Incident Office Review acceptance/rework | PIC or DPA for every risk band (`SAF_P_004` or `SAF_P_006` on `SAF_F_001`; send-back also accepts `SAF_P_003`) |
| Re-open closed Incident | Band-gated, mirrors closer (D-EDGE-03) |

---

## 2. Permission Model

Safety permissions follow the Reporting sibling pattern: `form_ids` (`SAF_F_*`) gate screens; `process_ids` (`SAF_P_*`) gate individual actions. Both live in the shared `msc_profiles` table and arrive in the JWT payload (`<vims_integration>` + FEAT-SAF-RBAC-005). Frontend wraps every route in `<PermissionGate form_id="SAF_F_xxx">`; action buttons wrap in `<ActionGate process_id="SAF_P_xxx">`.

### 2.1 Permission Map by Screen Group

```
Safety (sidebar group — hidden if user has no SAF_F_* IDs)
├── Incident ....................... form_ids: SAF_F_001
│   ├── Create incident ............ process_ids: SAF_P_001
│   ├── Submit Phase 1 / 2 / ... 6 . process_ids: SAF_P_002
│   ├── Send back (DPA → vessel) ... process_ids: SAF_P_003
│   ├── Phase-7 acceptance (close) . process_ids: SAF_P_004
│   ├── Re-open closed ............. process_ids: SAF_P_005
│   ├── Blame-fixation override .... process_ids: SAF_P_006
│   └── Export PDF / regulatory .... process_ids: SAF_P_007
├── Near Miss ...................... form_ids: SAF_F_002
│   ├── Create near miss ........... process_ids: SAF_P_001
│   ├── Office Comments priority decision (LOW↔HIGH) . process_ids: SAF_P_002 / SAF_P_006
│   ├── Issue fleet alert (HIGH) ... process_ids: SAF_P_024
│   └── Close (PIC) ................ process_ids: SAF_P_004
├── SCM ............................ form_ids: SAF_F_003
│   ├── Create Regular ............. process_ids: SAF_P_001
│   ├── Create Ad-Hoc ............. process_ids: SAF_P_001
│   ├── Edit agenda / suggestions .. process_ids: SAF_P_002
│   ├── Office Comment (close) ..... process_ids: SAF_P_004
│   └── Export PDF ................. process_ids: SAF_P_007
├── SOI ............................ form_ids: SAF_F_004 (inherits standard Safety RBAC, D-SOI-15)
│   ├── Schedule + generate paper .. process_ids: SAF_P_001
│   ├── Register findings .......... process_ids: SAF_P_002
│   ├── Mark `pending_closure` ..... process_ids: SAF_P_002
│   ├── Master approve closure ..... process_ids: SAF_P_004
│   ├── Area-applicability request . process_ids: SAF_P_011 (Master)
│   └── Area-applicability approve . process_ids: SAF_P_010 (DPA)
├── Dashboards ..................... form_ids: SAF_F_005
│   ├── Composite fleet score ...... (read)
│   └── Export (DPA only) .......... process_ids: SAF_P_007
└── Taxonomy admin ................. form_ids: SAF_F_006 (DPA only)
    ├── M-SCAT edit ................ process_ids: SAF_P_012
    ├── Case-study edit ............ process_ids: SAF_P_012
    └── SOI template edit .......... process_ids: SAF_P_012
```

### 2.2 Reporter Identity

Anonymous near-miss reporting is removed from V1. Reporter name, rank, and user reference are stored and shown to Master and authorized users according to vessel scope and Safety permissions. The frontend displays the reporter details returned by the API. PDF exports must not print any wording that says reporter identity is masked.

---

## 3. Route Map Summary

```
/safety/
  dashboard/                                 # Safety Intelligence Dashboard (FEAT-SAF-DASH-001)
  search/                                    # Cross-record FTS search + archive toggle (FEAT-SAF-DASH-008)
  incidents/                                 # Incident list (FEAT-SAF-INC-001 list)
    create/                                  # Create new — Phase 1 Intake
    :id/                                     # Incident detail — landing tab = current phase
    :id/phase-1/                             # Intake + Scene Control
    :id/phase-2/                             # Notifications + Resource Allocation
    :id/phase-3/                             # Corrective Action
      preventive/                            # Preventive Action
      lessons/                               # Legacy redirect to Office Review
    :id/phase-4/                             # Evidence Documents compatibility landing
      paper/                                 # Documents evidence capture
      people/ places/ parts/ photos/         # Legacy routes redirect to paper/
      interviews/                            # Witness Statement, opened only when needed
    :id/phase-5/                             # Office Review
    :id/fleet-alert/                         # Office Review Incident Fleet Alert selected-ship notification/email
      analysis/step/                         # STEP swimlane
      analysis/fact-tree/                    # Fact Tree
      analysis/ecf/                          # ECF Chart
      analysis/barrier/                      # Barrier Analysis + safeguard interrogatory
      analysis/change/                       # Change Analysis
      causal-layering/                       # Immediate/Root tagger
      human-factors/                         # SHELL + IMO A.884(21) 7+1 domain
    :id/phase-6/                             # Loss Evaluation
    :id/phase-7/                             # Legacy read-only final record route, hidden from workflow tabs
      verification/                          # Legacy backend effectiveness verification
    :id/phase-8/                             # Compatibility follow-up
    :id/closure/                             # Closure view (terminal)
    :id/audit/                               # Phase log + field history diff
    :id/pdf/incident/                        # 10-section PDF generation
    :id/pdf/mscmepc3/                        # MSC-MEPC.3 regulatory export
    :id/pdf/auditor-zip/                     # Auditor leave-behind ZIP
    :id/reopen/                              # Re-open flow
  near-miss/                                 # Near Miss list
    create/                                  # Create — one-screen form
    :id/                                     # Near Miss detail (authorized users see reporter identity)
    :id/triage/                              # Office Comments: LOW/MEDIUM by PIC, HIGH by DPA
    :id/fleet-alert/                         # Issue fleet alert (HIGH)
    :id/pdf/                                 # 1-2 page lightweight PDF
  scm/                                       # Safety Committee Meeting list
    create-regular/                          # Master/CO hosts Regular SCM
    create-adhoc/                            # Master/CO hosts Ad-Hoc SCM
    :id/                                     # SCM detail — landing = Overview
    :id/attendance/                          # Attendance + WRH join
    :id/agenda/                              # Agenda + decisions
    :id/closed-since-last/                   # Closed-Since-Last-SCM block
    :id/pdf/                                 # SCM PDF
  soi/                                       # SOI list + compliance tiles
    create/                                  # Step 1 — pick areas, SO + Assistant
    :id/                                     # SOI detail — landing = current state
    :id/pick-areas/                          # Area selector + Section 12 inclusion prompt
    :id/download/                            # Step 2 — generate & download paper (PDF or Excel)
    :id/findings/                            # Step 4 — register findings (link by unique-ID)
    :id/findings/create/                     # Add finding
    :id/findings/:findId/                    # Finding detail + SO → Master closure
    :id/applicability/request/               # Master requests `applicable=false`
    :id/applicability/approve/               # DPA approves / rejects
    :id/close/                               # Close SOI event
    :id/pdf/                                 # SOI Summary PDF
  admin/                                     # Taxonomy admin (DPA only)
    mscat/                                   # M-SCAT 174-row taxonomy editor
    soi-template/                            # 13-area × 329-item template editor
    bias-guards/                             # Bias-guard catalogue (read-only, 8 rows)
    case-studies/                            # Navigator + Sinkfast + user-added
```

Total unique routes: **65** (incident = 28 · near-miss = 6 · scm = 8 · soi = 11 · dashboards/search = 2 · admin = 4 · list + landing = 6).

---

## 4. Incident Module — Current Screen Catalog

Incident flow follows the simplified current workflow recorded in SSOT section 3.0. The visible phase tabs are sequential: Report Incident, RCA, Corrective Action, Preventive Action, Add Evidence, Office Review, and Loss Evaluation. Lessons Learned is removed from the current workflow; its legacy route redirects to Office Review. The read-only Final Record route remains available only for direct audit/legacy access and is not shown as a workflow tab. Older DNV-heavy phase details below are retained as compatibility/background only where they do not conflict with this current binding.

| Visible phase | Screen | Primary route |
|---------------|--------|---------------|
| Phase 1 | Report Incident | `/safety/incidents/:id/phase-1/` |
| Phase 2 | RCA (Root Cause Analysis) | `/safety/incidents/:id/phase-2/` |
| Phase 3 | Corrective Action | `/safety/incidents/:id/phase-3/` |
| Phase 4 | Preventive Action | `/safety/incidents/:id/phase-3/preventive/` |
| Phase 5 | Add Evidence | `/safety/incidents/:id/phase-4/paper/` |
| Phase 6 | Office Review | `/safety/incidents/:id/phase-5/` |
| Phase 7 | Loss Evaluation | `/safety/incidents/:id/phase-6/` |
| Legacy redirect | Removed Lessons Learned path | `/safety/incidents/:id/phase-3/lessons/` redirects to Office Review |

Current action screens use the existing recommendation/corrective-action backend contract for compatibility. Corrective Action shows Description and Due date only. Preventive Action shows Description, Due date, and **How much will this reduce risk?** only. The owner/checker card, theme, effort, Remaining risk, risk-confirmation checkbox, and "Prevent It Happening Again" wording are removed from the current action UI. Saved action cards show **Edit**, load the existing row into the form, and update that row instead of adding a duplicate.

### 4.0 Incident List — `/safety/incidents/`

**FEAT refs:** FEAT-SAF-INC-001 (list), FEAT-SAF-INC-036 (draft mode), FEAT-SAF-DASH-005, FEAT-SAF-INC-032.

**Route:** `/safety/incidents/`
**Role gate:** `PermissionGate(SAF_F_001)` — any user with Safety form access.
**Data loaded on mount:**
- `GET /api/safety/incidents/?vessel_id={id}&status={filter}&band={filter}&classification={filter}` — query key `['safety','incidents', vesselId, filters]`
- Vessel-scope filter uses `master_RoleByVessel` (office) or `Crew_Onboarding_History` (ship) per platform pattern.
- Risk-band pill colours from DESIGN_SYSTEM §3 (`--safety-risk-green / yellow / red`).
**States:**
- **Loaded:** Table with columns `Ref No | Vessel | Date | Type | SMC/MC/MI | Band | Phase | Closer | Updated`. Rows click through to `/safety/incidents/:id/`.
- **Loading:** Skeleton rows × 8 (DESIGN_SYSTEM §5.2 skeleton pattern inherited from Reporting).
- **Empty:** `"No incidents recorded for this vessel. Click New Incident to begin a Phase 1 intake."` + `[New Incident]` CTA (visible only if `SAF_P_001`).
- **Error — validation:** not applicable on list screen.
- **Error — network:** Retry banner + stale-cache rows displayed in grey.
- **Error — auth:** 403 → redirect to `/safety/` with toast `"You do not have access to Safety incidents."`
**Signature transition:** n/a (list view).
**Navigation:**
- `[New Incident]` → `/safety/incidents/create/` (Phase 1).
- Row click → `/safety/incidents/:id/` (detail landing).
- Sidebar → Near Miss / SCM / SOI / Dashboard / Search.
**Decisions:** D-EDGE-01 (multi-vessel linking), D-GAP-M07 (dup detection), D-EDGE-08 (draft mode).

### 4.1 Phase 1 — Intake — `FEAT-SAF-INC-001` / `FEAT-SAF-INC-040`

**Route:** `/safety/incidents/create/` (new) · `/safety/incidents/:id/phase-1/` (resume)
**Role gate:** `PermissionGate(SAF_F_001) + ActionGate(SAF_P_001) + role ∈ {Master, CO, CE, 2/E}` (top-4 per D-RBAC-11 enforcement via `SAF_P_001`).
**Data loaded on mount:**
- `GET /api/safety/incidents/form-config/latest/` — Zod schema version + incident-type picklist.
- `GET /api/safety/reference/incident-types/` — 32 active rows from `master_safety_incident_type`; retired earlier rows, including `Missing vessel`, are not offered for new selection.
- `GET /api/safety/master/loss-types/` — 7 rows from `master_loss_types`.
- On first save: `POST /api/safety/incidents/` → issues `DRAFT-{VslCode}/{YYYY}/T{nnn}` per D-GAP-C1.
- On resume/edit: `GET /api/safety/incidents/:id/phase-1/` loads the saved Phase 1 record and `PATCH /api/safety/incidents/:id/phase-1/` persists changes while the incident remains before office approval.
- Live join (position auto-fill): `GET /api/safety/incidents/position-prefill/?vessel_id={id}&timestamp={ts}` → joins `vims_reporting_daily_report` for ±12h window (D-GAP-M09, FEAT-SAF-XMOD-001).
**Signature transition:** None on Phase 1. Draft state; no sign-off until Phase 2 submit.
**States:**
- **Loaded:** Form renders with:
  - Incident type picker (32 active options in the CR-031 business order; retired earlier options are hidden).
  - Narrative free-text (≥150 chars — enforced in VALIDATION_RULES §4).
  - Office communication fields labelled **Was office informed?** and **How was office informed?**. The current communication-mode dropdown offers On call and On email; WhatsApp is not offered.
  - Report time and Shore Assistance Required together on one incident-report row.
  - Latitude and Longitude fields together on their own incident-report row.
  - Incident reporting context fields on the main report form: Shore Assistance Required, Location of Vessel, Location on Board, Departure Date, and Vessel Condition. These use incident-level columns added by CR-024 and are shared by incident and injury reporting. Last Port remains legacy storage only and is not shown by the current Phase 1 UI.
  - Weather Condition fields exclude Ice condition on-board and Ice condition at sea in the current UI.
  - Injury details section (FEAT-SAF-INC-034) optional; asks `Crew` or `Non-crew`.
  - Non-crew injury shows the existing person/company/party type/injury level/notes fields.
  - Crew injury shows ship-crew rank dropdown, age, and `Type of Activity`.
  - Crew injury also captures investigation narrative and OCIMF yes/no flags; estimated cost fields are optional and are shown only when the user answers Yes to adding estimated cost details.
  - `Type of Activity` is loaded from the injury dropdown master using field key `TYPE_OF_ACTIVITY`.
  - In the crew investigation section, `Nature of Injury`, `Source of Injury`, and `Affected Areas of the Body` are dropdowns loaded from the injury dropdown master. Choosing `Others(Specify)` opens a blank text field and saves the typed value.
  - During edit, a null or omitted `external_party_injury` payload leaves any existing injury record unchanged; populated injury payloads create or update the injury row.
  - Auto-save every 30s to IndexedDB per FEAT-SAF-AUDIT-006 (D-GAP-F1).
- **Loading:** Skeleton form; "Loading form config…" tag top-right.
- **Empty:** On new incident, form pre-fills vessel + reporter + timestamp; narrative/incident-type blank.
- **Error — validation:** Narrative below the current minimum shows a field-level warning; future or reversed occurrence/report times and missing required reporter/risk/office fields show inline errors.
- **Error — network:** Auto-save falls back to IndexedDB; banner `"Offline — changes saved locally."` Sync on reconnect.
- **Error — auth:** 403 → redirect to incident list.
**Navigation:**
- `[Save Draft]` → stays on screen; amber "Draft saved 14:32 LT" chip.
- `[Continue to Phase 2]` → enforces all Phase 1 mandatory fields, transitions state, routes to `/safety/incidents/:id/phase-2/`.
- `[Cancel]` → confirm modal; discards new record.
**Decisions:** D-MAINT-CR018 (first-check removal), D-MAINT-CR024 (incident-level reporting context fields), D-GAP-C1 (draft series), D-GAP-F1 (auto-save), D-GAP-M09 (position), D-EDGE-08 (partial save).
**Cross-module join:** **Reporting** (Daily Report position, FEAT-SAF-XMOD-001); **CMS** (reporter name / rank via live join, FEAT-SAF-XMOD-003).

### 4.2 Phase 2 — Notifications + Resource Allocation — `FEAT-SAF-INC-004`, `FEAT-SAF-INC-002`, `FEAT-SAF-INC-003`

**Route:** `/safety/incidents/:id/phase-2/`
**Role gate:** `PermissionGate(SAF_F_001) + ActionGate(SAF_P_002) + role ∈ {Master, CO, CE, DPA, FM}`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/` — full record including Phase 1 data.
- `GET /api/safety/master/classifications/` — IMO SMC/MC/MI picklist.
- On Submit: `POST /api/safety/incidents/:id/phase-2/submit/` → assigns formal `{VslCode}/{YYYY}/{NNN}` number (gap-free per-vessel-per-year), fires notifications to PIC + DPA + safety-channel via `master_notification` (FEAT-SAF-XMOD-006, D-GAP-F2), computes risk band (GREEN / YELLOW / RED per D-DNV-02), stamps `schema_version`, transitions state to Phase 3.
**Signature transition:**
- **Phase 1 → 2** captures the **Reporter (Master / CO / CE / 2E)** digital signature block (typed name + timestamp + device fingerprint per D-GAP-D1, DESIGN_SYSTEM §8.2 `--safety-sig-reporter`). This is the first signature in the Reporter → Master → HOD → DPA → FM chain (SSQE §11.2).
- RED-band also triggers `"External expert engagement prompt"` modal.
**States:**
- **Loaded:** Two-column layout — left = Phase 1 data read-only summary; right = Phase 2 inputs (SMC/MC/MI, Type-of-Loss, Probability, computed band). `[Submit to office]` CTA bottom-right.
- **Loading:** Summary skeleton + classifier picklist spinner.
- **Empty:** Not applicable (Phase 1 data always present; if missing → redirect to Phase 1).
- **Error — validation:** Classifier unselected → red border + inline message. Probability missing → blocked submit.
- **Error — network:** `"Submission failed — retry in 10s"` with retry button; state stays Phase 1 draft.
- **Error — auth:** 403 with role mismatch → read-only view + tooltip `"Only top-4 officers may submit Phase 2"`.
**Navigation:**
- `[← Back to Phase 1]` → `/safety/incidents/:id/phase-1/` (editable until office approval locks the incident).
- `[Submit to office]` → `/safety/incidents/:id/phase-3/` on success + confirmation toast with formal ref no.
**Decisions:** D-EDGE-09, D-GAP-F2, D-GAP-M28 (no digest), D-GAP-F4 (RED alert), D-GAP-R08 (classifier), D-DNV-02 (band).
**Cross-module join:** **master_notification** writes (shared queue). **HRM / CMS** for DPA on-leave detection (FEAT-SAF-INC-037 deadline auto-pause).

### 4.3 Phase 4 — Evidence Documents — `FEAT-SAF-INC-005` through `FEAT-SAF-INC-014`

**Route:** `/safety/incidents/:id/phase-4/paper/`
**Role gate:** `PermissionGate(SAF_F_001) + role ∈ {Master, CO, CE, HOD (onboard), DPA, FM (RED-edit)}`.
**Availability:** Authorized users can open the current Phase 5 Add Evidence documents screen and add attachments before the legacy evidence phase is formally reached. This early evidence capture does not skip submit/continue requirements and remains locked after office approval, closure, or supersession.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/phase-4/evidence/` — legacy-compatible evidence payload; the current UI writes to the Documents/PAPER tab.
- `GET /api/safety/incidents/:id/chain-of-custody/` — physical evidence custody list.
- `GET /api/safety/incidents/:id/interviews/` — interview index (FEAT-SAF-INC-012).
**Signature transition:**
- Current Office Review captures a PIC or DPA office decision signature for every risk band. FM-specific RED signature is no longer required by the current implemented Office Review path.
- Chain-of-Custody items capture **collector + witness** paper signatures (wet-sign or digital per D-GAP-D1, FEAT-SAF-INC-007).
- The current Witness Statement UI captures a witness-statement upload but does not expose the old text statement, read-back/copy-to-witness controls, or formal/informal selector; legacy formal interview API validation remains compatible for older clients (D-MAINT-CR016, D-MAINT-CR036, D-MAINT-CR049).

**Sub-routes:**
| Route | Content |
|-------|---------|
| `/phase-4/paper/` | Documents evidence capture. Each entry has Attachment, Title, and Description. Users can add as many attachments as required. |
| `/phase-4/people/`, `/phase-4/places/`, `/phase-4/parts/`, `/phase-4/photos/` | Legacy routes retained for bookmarks and redirected to `/phase-4/paper/`. |
| `/phase-4/interviews/` | Witness Statement, opened only when needed. The form has vessel crew/Other witness selection, Remark, and Upload witness statement. |

**Current UI simplification (CR-012):**
- The screen shows one **Documents** evidence section, not People / Place / Equipment / Photos category cards.
- The document form has only `Attachment`, `Title`, and `Description`; the user repeats the form for additional attachments.
- Saved document cards show **Edit** for `Title` and `Description`. Editing metadata does not require reuploading or replacing the original attachment file.
- Existing backend tab codes (`PEOPLE`, `POSITION`, `PARTS`, `PAPER`, `ELECTRONIC`) are kept for compatibility, but the current user-facing capture writes new attachments to `PAPER`.
- Evidence Check / Evidence Matrix is removed from the current Phase 4 UI under CR-015; legacy matrix data remains backend-compatible only.
- Witness Statement is simplified under CR-016, CR-036, and CR-049; formal/informal selection, read-back, copy-to-witness, old statement textarea, and 4-phase interview fields are legacy compatibility only. Upload witness statement writes to the existing witness-signature storage field. Saved Witness Statement cards show **Edit**, load the existing statement into the form, and update the same witness row.

**States (Documents section):**
- **Loaded:** Documents renders with the add-document form and saved attachment list first. Saved documents and Witness Statements include Edit actions. Supporting tools stay collapsed until opened. The phase tabs show phase number/name, and the content area does not repeat a separate Phase X title card.
- **Loading:** Skeleton list items.
- **Empty:** `"No attachments added yet."`
- **Error — validation:** Missing title or missing attachment is shown inline before upload.
- **Error — network:** Cache-fallback for read; uploads queue in IndexedDB.
- **Error — auth:** RED investigation lock — non-DPA/FM see read-only view.

**Navigation:**
- Current rework action: PIC or DPA can send the incident back with a required reason, regardless of risk band.
- Tab bar preserves state across tabs.
- `[Schedule deadline tasks]` button (FEAT-SAF-INC-011) → modal to spawn VDR-12h, ECDIS-24h, AIS-24h, photo-48h, statements-7d tasks.
- Evidence document uploads and metadata edits save in place even when Phase 4 has not been reached; workflow submit buttons still follow ordered phase transitions.
- **Witness Statement** card opens `/phase-4/interviews/` directly on the first click; there is no intermediate **Open Witness Statement** button.
- Loop-back from future phase returns to this screen with `loop_back_from_phase` set in URL query string.

**Decisions:** D-MAINT-CR012 (Documents-only evidence UI), D-MAINT-CR013 (early evidence capture before Phase 4 reached), D-MAINT-CR016 (simplified witness baseline), D-MAINT-CR036 (Witness Statement crew/Other/signature/Remark), D-MAINT-CR037 (duplicate phase headers removed), D-MAINT-CR041 (saved document/witness edit controls), D-MAINT-CR045 (Witness Statement card opens directly), D-DNV-07 (legacy Evidence Workspace compatibility), D-GAP-R04 (CoC), D-GAP-R06 (deadlines), D-GAP-I1 (PMS manual), D-DNV-11 #4 (Pro/Con), D-DNV-08 / D-GAP-R19 / D-GAP-R20 (legacy interview compatibility).

### 4.4 Phase 4 — Sequence (Facts Systemized) — `FEAT-SAF-INC-015`

**Route:** `/safety/incidents/:id/phase-4/`
**Role gate:** `PermissionGate(SAF_F_001) + role ∈ {Master, CO, CE, HOD, DPA, FM (RED-edit)}`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/facts/` — list from shared `vims_safety_fact` table.
- `GET /api/safety/incidents/:id/evidence/` — for evidence-link picker.
**Signature transition:** None. Phase 4 is analytical; no signature captured.
**States:**
- **Loaded:** Fact grid (`Fact | Evidence link | Layer | Timestamp | Added by`); `[+ Add Fact]` CTA; facts flagged `hindsight_guard_triggered=true` show amber badge (bias guard #3).
- **Loading:** Skeleton rows.
- **Empty:** `"No facts systemized yet. Add your first fact — each must cite evidence (bias guard #2)."`.
- **Error — validation:** Fact without evidence link → red block on save. Fact citing post-event info → amber warning with override reason (hindsight guard).
- **Error — network:** Save queues; retry banner.
- **Error — auth:** Read-only for non-investigators.
**Navigation:**
- Legacy analytical navigation is superseded by the current simplified workflow. The current `/safety/incidents/:id/phase-5/` route opens Office Review.
- Loop-back → Phase 3 via `[← Loop back — need more evidence]` (reason required; logged in `vims_safety_incident_phase_log` per D-GAP-B3).
**Decisions:** D-DNV-10, D-DNV-11 #2 (assumption), D-DNV-11 #3 (hindsight).

### 4.5 Legacy Analysis Tools — compatibility background — `FEAT-SAF-INC-016` … `FEAT-SAF-INC-026`

**Route:** Legacy/background only. Current `/safety/incidents/:id/phase-5/` is Office Review under D-MAINT-CR042.
**Role gate:** `PermissionGate(SAF_F_001) + role ∈ {Master, CO, CE, HOD, DPA, FM (RED-edit)}`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/analysis/` — tool-specific payload (STEP / Fact Tree / ECF / Barrier / Change) over shared fact base.
- `GET /api/safety/master/mscat/` — 174 rows from `master_mscat_taxonomy` (incl. 10.15 Design/MOC Governance — D-GAP-R15).
- `GET /api/safety/master/immediate-causes/` — 52 rows from `master_immediate_causes`.
- `GET /api/safety/master/bias-guards/` — 8 rows from `master_safety_bias_guard`.
- `GET /api/safety/master/case-studies/` — Navigator + Sinkfast Help-drawer content (FEAT-SAF-DASH-009).
**Signature transition:** Legacy only. The current visible workflow does not expose a Phase 5 analysis step.

**Sub-routes (tabs):**
| Tab | Route | Content |
|-----|-------|---------|
| Multi-tool | `/phase-5/analysis/step/` etc. | 5 tools over shared fact base |
| Causal layering | `/phase-5/causal-layering/` | Immediate / Root tagger (FEAT-SAF-INC-018, superseded for current UI by D-MAINT-CR033) |
| Human Factors | `/phase-5/human-factors/` | SHELL + IMO A.884(21) 7-domain + Risk/Change 8th |
| People / Process / Plant | embedded in summary | 3 mandatory narrative answers ≥50 chars each (FEAT-SAF-INC-022) |
| Investigation depth | top panel | SHALLOW / MEDIUM / DEEP indicator (FEAT-SAF-INC-021) |

**States:**
- **Loaded:** Depth triangle top-left; cause tree centre; bias-guard rail right. Current causes show Immediate or Root. Saved cause cards show Edit and update the existing cause row when corrected. Legacy Intermediate rows, when present, display under Root rather than as a separate category.
- **Loading:** Skeleton + "Loading M-SCAT (174)".
- **Empty:** `"No causes coded yet. Start from the M-SCAT picker or Fact Tree."`.
- **Error — validation:** Phase 5 → 6 transition fires the current bias-guard set (DESIGN_SYSTEM §8 state pill "Under Review"): Recency, Assumption, Hindsight, Confirmation review, Blame-Fixation; the legacy evidence-matrix Con-row gate is not user-facing after D-MAINT-CR015; Blame-Fixation hard-block per D-RBAC-07 → GREEN/YELLOW override DPA, RED override FM.
- **Error — network:** Save queues.
- **Error — auth:** RED → only DPA/FM edit.

**Navigation:**
- Legacy only. Current users move from Preventive Action directly to Office Review and may open Add Evidence separately.
- `[← Loop back to Phase 3]` with reason.
- Help drawer link → case studies.

**Decisions:** D-DNV-05 (loop-back), D-GAP-B3 (no cap), D-DNV-01 (M-SCAT), D-GAP-C2 (hierarchical picker), D-GAP-R01 (layer tag), D-GAP-R03 (multi-root), D-GAP-R14 (depth), D-GAP-R16 (P/P/P), D-GAP-R18 (6-dim safeguard), D-DNV-09 (SHELL), D-GAP-R21 (Risk/Change), D-DNV-11 (bias guards), D-GAP-R12 (8 guards), D-RBAC-07 (override).

### 4.6 Phase 6 — Recommendations — `FEAT-SAF-INC-027`, `FEAT-SAF-INC-028`, `FEAT-SAF-INC-029`

**Route:** `/safety/incidents/:id/phase-6/`
**Role gate:** `PermissionGate(SAF_F_001) + role ∈ {Master, DPA, FM (RED-edit)}`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/recommendations/` — three tiers (Lessons / Immediate / System).
- `GET /api/safety/master/recommendation-themes/` — 7 themes (Training / Contractor / Compliance / HR / MoC / Procedures / Equipment).
**Signature transition:**
- **Phase 6 Submit** captures the **Master** signature (DESIGN_SYSTEM §8.2 `--safety-sig-master`) — second in the Reporter → Master → HOD → DPA → FM chain.
**States:**
- **Loaded:** Three columns = Lessons / Immediate / System. ALARP fields visible on System rows (effort, likelihood reduction, residual-risk statement). Each recommendation carries colour badge Corrective / Preventive / Lessons (D-GAP-R13). Tolerable-Failure tile shown for GREEN (V1.1 — FEAT-SAF-INC-029).
- **Loading:** Skeleton columns.
- **Empty:** `"No recommendations yet. YELLOW/RED closure requires ≥1 of each tier."`.
- **Error — validation:** YELLOW/RED Phase 6 Submit without all three tiers → red banner. System Action without ALARP fields (RED/YELLOW) → red banner (VALIDATION_RULES §5.4).
- **Error — network:** Auto-save.
- **Error — auth:** Master-rank bypass for RED (edit).
**Navigation:**
- `[Continue to Phase 7 (DPA acceptance)]` → `/safety/incidents/:id/phase-7/`.
- `[Link to Purchase Req]` on an Immediate CA → opens Purchase module `/purchase/requisitions/create?linked_safety_ca={caId}` — **hard FK via D-GAP-M12 / FEAT-SAF-XMOD-004**.
- `[← Loop back to Phase 3 or 4]` allowed.
**Decisions:** D-DNV-06, D-GAP-R13, D-GAP-R02 (ALARP), D-GAP-R11 (tolerable-failure), D-GAP-M12 (CA/Purchase).

### 4.7 Phase 7 — DPA Acceptance / Report Issued — `FEAT-SAF-INC-030`

**Route:** `/safety/incidents/:id/phase-7/`
**Current CR-044 role gate:** PIC or DPA with Office Review process permission can accept, close, or send rework for every risk band. Legacy text in this section that maps acceptance to PIC/GREEN, DPA/YELLOW, or FM/RED is superseded for the current implemented Office Review path.
**Role gate:** `PermissionGate(SAF_F_001) + ActionGate(SAF_P_004) + role ∈ {PIC (GREEN closer), DPA (YELLOW closer), FM (RED closer)}`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/phase-7/preflight/` — returns `{bias_guards_resolved, root_count, recommendation_tier_count, alarp_complete, signature_chain_status}`.
- On Accept: `POST /api/safety/incidents/:id/phase-7/accept/` → triggers PDF generation (FEAT-SAF-PDF-001), transitions to user-facing Phase 7 Loss Evaluation using backend compatibility phase 8, writes closure event to `vims_safety_incident_phase_log`. Manual PDF preview/download is also available before Phase 7 acceptance when the record is an incident.
**Signature transition:**
- **DPA** signature (YELLOW) or **FM** signature (RED) captured here — fourth / fifth in the Reporter → Master → HOD → DPA → FM chain (SSQE §11.2). For GREEN, PIC signature is terminal.
- HOD signature (third) is captured when the HOD completes department-level review at an earlier Phase-6 sub-routing step (same screen, department-locked rows) — see DESIGN_SYSTEM §8.2 `--safety-sig-hod`.
**States:**
- **Loaded:** Preflight card — green ticks + any red blockers listed; PDF preview tile with the default-selected content checklist; `[Accept & Issue Report]` CTA.
- **Loading:** Preflight spinner.
- **Empty:** not applicable (always has Phase 6 data).
- **Error — validation:** Any preflight check failed → CTA disabled with reason listed.
- **Error — network:** Retry; state unchanged.
- **Error — auth:** Wrong closer-band → read-only preview with tooltip.
**Navigation:**
- `[Accept]` → `/safety/incidents/:id/phase-8/` + download 10-section PDF.
- `[Send back to Phase 3]` (DPA safety-net) → reason required.
- `[View draft PDF]` → opens `/safety/incidents/:id/pdf/incident/` using the selected PDF section checklist.
**Decisions:** D-PDF-01 (10-section), D-MAINT-CR044 (PIC/DPA all-band Office Review), D-EDGE-03 (legacy re-open).

### 4.8 Phase 7 / backend Phase 8 — Loss Evaluation — `FEAT-SAF-INC-031`

**Route:** `/safety/incidents/:id/phase-6/` (frontend compatibility path; legacy `/phase-8/` component aliases may still exist internally).
**Current CR-047 role gate:** PIC or DPA can save Loss Evaluation and close for every risk band after Office Review approval.
**Role gate:** `PermissionGate(SAF_F_001) + role ∈ {PIC, DPA}`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/phase-6/` — Loss Evaluation workspace with `report_type`, dropdown choices, saved `loss_evaluation`, and close readiness.
- `PATCH /api/safety/incidents/:id/phase-6/` — saves one editable Loss Evaluation row in `vims_safety_incident_loss_evaluation`.
- `POST /api/safety/incidents/:id/phase-6/close/` — closes after Loss Evaluation is saved and closure note is supplied.
**Signature transition:** no formal re-signing of the incident report; closure note and Office Review signature remain in the final PDF signature/closure area.
**States:**
- **Loaded:** Risk Assessment, Other Details, Cost Evaluation, Estimated Costs, and Close Incident card. Incident Report records show repair/loss/cost fields; Injury Report records show safe-working-practice/rest/repatriation/hospitalization/evacuation/injury-cost fields.
- **Loading:** `"Loading Loss Evaluation..."`
- **Empty:** saved status shows `Not saved`; Close Incident is disabled until Loss Evaluation is saved.
- **Error — validation:** Attempt-close without saved Loss Evaluation → red/amber validation message.
- **Error — network:** Retry.
- **Error — auth:** PIC or DPA role required.
**Navigation:**
- `[Close Incident]` → `/safety/incidents/:id/closure/` (terminal state).
- `[Back to Office Review]` → `/safety/incidents/:id/phase-5/`.
**Decisions:** D-MAINT-CR047.

### 4.9 Closure / Read-only — `/safety/incidents/:id/closure/`

**Role gate:** Any with `SAF_F_001`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/` — full record with derived `is_closed=true`.
- `GET /api/safety/incidents/:id/audit/` — phase log + field history diff.
**Signature transition:** None (read-only).
**States:**
- **Loaded:** Two-panel — left = all phases' data read-only; right = signature chain summary with 5 blocks (Reporter / Master / HOD / DPA / FM) per DESIGN_SYSTEM §8.2 each showing typed name + timestamp + device fingerprint.
- **Loading:** Skeleton.
- **Empty:** n/a.
- **Error — network / auth:** standard.
**Navigation:**
- `[Re-open Incident]` (band-gated per D-EDGE-03) → `/safety/incidents/:id/reopen/` (DPA for GREEN/YELLOW; FM for RED).
- `[Auditor ZIP]` → `/safety/incidents/:id/pdf/auditor-zip/` (FEAT-SAF-PDF-006).
- `[MSC-MEPC.3 Export]` → `/safety/incidents/:id/pdf/mscmepc3/` (FEAT-SAF-PDF-002).
**Decisions:** D-EDGE-03, D-PDF-02, D-DNV-12.

### 4.10 Audit Trail — `/safety/incidents/:id/audit/`

**Role gate:** `PermissionGate(SAF_F_001) + role ∈ {DPA, FM, Master (own vessel)}`.
**Data loaded on mount:**
- `GET /api/safety/incidents/:id/phase-log/` — `vims_safety_incident_phase_log` append-only rows.
- `GET /api/safety/incidents/:id/field-history/` — `vims_safety_field_history` rows.
**Signature transition:** None.
**States:**
- **Loaded:** Timeline of phase transitions (from → to, reason, actor, ts, loop_back flag) + expandable field-history diff panel per record.
- **Loading:** Skeleton.
- **Empty:** n/a (every incident has ≥1 log entry).
- **Error — network / auth:** standard.
**Navigation:** Back to incident detail; link to diff viewer.
**Decisions:** D-EDGE-10 (append-only), D-GAP-M04 (no revert UI in V1), D-GAP-F4 (access log on audit itself).

### 4.11 PDF Generation Routes — `/safety/incidents/:id/pdf/*`

| Sub-route | Feature | Role gate | States |
|-----------|---------|-----------|--------|
| `/pdf/incident/` | FEAT-SAF-PDF-001 selectable-section PDF | Closer-band roles; any `SAF_F_001` for view | Loaded: default-selected section checklist + inline PDF viewer. Loading: spinner + "Generating PDF…". Error: "Generation failed — retry" |
| `/pdf/mscmepc3/` | FEAT-SAF-PDF-002 MSC-MEPC.3/Circ.4 | DPA | Loaded: 5-appendix regulatory PDF; position auto-filled from Daily Report live-join (D-GAP-M09) |
| `/pdf/auditor-zip/` | FEAT-SAF-PDF-006 ZIP | Master (vessel vetting) + DPA (fleet) | Loaded: scope selector → ZIP download. Error: "Scope empty" |

The FEAT-SAF-PDF-001 visible title is `Injury Report` when the incident has a saved Phase 1 injury record from `Record injury`; otherwise it is `Incident Report`.

Before incident PDF preview or download, the user chooses the content to include. The current checklist defaults all items to selected and includes: Summary, Reporter Details, Injury Details, Estimated Cost, Root Cause, Evidence (Documents), Corrective / Preventive Actions, and Signature. The frontend sends selected keys in the `sections` query parameter; omitted or empty `sections` means print all allowed backend sections for backward compatibility, including the legacy `lessons_learned` key for old/direct exports.

Incident PDF preview/download and MSC-MEPC.3/Circ.4 export are not blocked only because Phase 7 acceptance is pending. Record-type checks and MSC-MEPC.3/Circ.4 classifier applicability checks still apply.

In FEAT-SAF-PDF-001 output, Office Review comments and closure reason are not part of the Summary table. When present, they print in the final Office Review / Closure area immediately before Signature. Current action detail boxes print each saved description once and do not repeat the same description as a separate paragraph above the box. Recommendation rationale / "Why is this needed?" text is not captured by the current action screens and is not printed in the PDF.

Evidence (Documents) PDF output prints each saved attachment as its own document block. The block uses the saved title when available and separates Description and File rows; it does not use numbered labels such as `Attachment 1` or `Attachment 2`. Legacy evidence-note-only rows are not printed in the PDF; saved Witness Statements remain printable with Remark wording.

---

## 5. Near Miss Module

Near Miss uses the same `vims_safety_incident` table via `record_type='near_miss'` discriminator; UI surface is **lightweight** per FEAT-SAF-NM-004. Anonymous reporting is removed from V1; reporter details are visible to Master and authorized users.

### 5.1 Near Miss List — `/safety/near-miss/`

**FEAT refs:** FEAT-SAF-NM-001.
**Role gate:** `PermissionGate(SAF_F_002)` — all crew + shore office.
**Data loaded on mount:**
- `GET /api/safety/near-miss/?vessel_id={id}` — query key `['safety','nearMiss', vesselId]`.
**Signature transition:** n/a.
**States:**
- **Loaded:** Table `Ref | Vessel | Date | Priority (LOW/MEDIUM/HIGH) | Reporter | State`. Reporter cell shows the reporter name/rank where available.
- **Loading:** Skeleton rows.
- **Empty:** `"No near miss records. Any crew member may create one — click New Near Miss."`
- **Error — network / auth:** standard.
**Navigation:**
- `[New Near Miss]` → `/safety/near-miss/create/`.
- Row click → `/safety/near-miss/:id/`.
**Decisions:** D-RBAC-11, D-GAP-J1 revised 2026-06-09.

### 5.2 Create Near Miss — `/safety/near-miss/create/`

**FEAT refs:** FEAT-SAF-NM-001, FEAT-SAF-NM-005.
**Role gate:** `PermissionGate(SAF_F_002) + ActionGate(SAF_P_001) + role = any crew` (D-RBAC-11).
**Data loaded on mount:**
- `GET /api/safety/master/loss-types/` for the combined Category dropdown.
- `GET /api/safety/near-miss/cause-options/` for Human/Vessel/Management/Other factor cause dropdowns.
**Signature transition:**
- On submit, **Reporter** identity and device fingerprint are stored on record.
**Field controls:** place is one of `At Anchor`, `At Sea`, `At Port`; Category combines the previous Category and Possible Loss Type dropdown options into a single flat dropdown; Near Miss Type is removed; Category allows up to 3 selections and has one custom option `Other - Specify`. Cause analysis is four cards: Human Factors, Vessel Factors, Management Factors, and Other Factors. Each card has Immediate Cause and Root Cause dropdowns. Every dropdown includes `Other` and `Not Applicable`; selecting `Other` opens a required text field.
**States:**
- **Loaded:** Single-page form — what happened (≥100 chars, D-GAP-M38) · severity · place · category · factor causes · Immediate Action · suggestion/preventive action.
- **Loading:** Skeleton.
- **Empty:** n/a.
- **Error — validation:** `<100 chars` → red block. There is no per-day near-miss submission cap in V1.
- **Error — network:** Auto-save to IndexedDB; submit queues.
- **Error — auth:** 403 (no `SAF_F_002`).
**Navigation:**
- `[Submit]` → `/safety/near-miss/:id/` with confirmation.
**Decisions:** D-RBAC-11, D-GAP-M38 revised 2026-06-09, D-GAP-F1 (auto-save).

### 5.3 Near Miss Detail — `/safety/near-miss/:id/`

**FEAT refs:** FEAT-SAF-NM-002, FEAT-SAF-NM-003, FEAT-SAF-NM-004.
**Role gate:** `PermissionGate(SAF_F_002)` — all authorized Safety users within vessel scope.

**Reporter identity:** reporter name, rank, and user reference are visible to Master and authorized users. The old `Anonymous Reporter` display and anonymous badge are not used.

**Data loaded on mount:**
- `GET /api/safety/near-miss/:id/`.
- `GET /api/safety/near-miss/:id/audit/` — field history visible per Safety permissions and vessel scope.
**Signature transition:**
- Reporter identity/signature data captured at submit.
- LOW → PIC review → closure signature (DESIGN_SYSTEM §8.2 role-varied signature block).
- HIGH → Master / HOD vessel-side review signature captured with typed name + device fingerprint before Office Comments / fleet-alert approval.
**States:**
- **Loaded:** Card layout — What happened · Suggestion · Immediate action · Priority pill (LOW amber / HIGH red per DESIGN_SYSTEM §3).
- **Loading:** Skeleton card.
- **Empty:** n/a.
- **Error — network / auth:** standard.
**Navigation:**
- `[Office Comments]` → `/safety/near-miss/:id/triage/` (PIC accepts LOW/MEDIUM; DPA accepts HIGH; either can send back for rework when authorized; Master can submit rework regardless of original reporter).
- `[Issue Fleet Alert]` → `/safety/near-miss/:id/fleet-alert/` (DPA if HIGH).
- `[Close]` → PIC action.
**Decisions:** D-GAP-J1 revised 2026-06-09, D-GAP-R22 (Office Comments), §4.3 SSOT (lightweight).

### 5.4 Near Miss Office Comments — `/safety/near-miss/:id/triage/`

**Role gate:** `PermissionGate(SAF_F_002)` plus office action permission. PIC/office PIC accepts LOW and MEDIUM cases; DPA accepts HIGH cases.
**Data loaded on mount:** Existing record + suggested priority + current category tag and factor causes.
**Actions:** `Accept` saves priority, category tag, factor causes, and office comment. `Send to Rework` moves the record back to vessel rework with a required reason.
**States:** Standard loaded/loading; error if priority override or rework send-back is missing a reason.
**Navigation:** Back to detail.
**Decisions:** D-GAP-R22.

### 5.5 Fleet Alert Issuance — `/safety/near-miss/:id/fleet-alert/`

**FEAT refs:** FEAT-SAF-NM-006.
**Role gate:** `PermissionGate(SAF_F_002) + ActionGate(SAF_P_024) + role = DPA`.
**Data loaded on mount:**
- `GET /api/safety/near-miss/:id/fleet-alert/draft/` — auto-draft with vessel + crew names anonymised per D-GAP-M08.
- `[Issue Circular/Alert]` stores a one-time prefill handoff and opens `/circular/office?safety_prefill=near_miss_fleet_alert`.
- The handoff pre-fills only Circular title and body from the anonymised Near Miss fleet-alert draft. DPA completes document type, department, scope, sub-categories, priority, recipients, attachments, and publish from the Circular module.
- The Safety module does **not** directly create or publish the Circular record from this screen.
**Signature transition:** DPA fleet-alert issue signature stays in Near Miss; Circular publish signature stays in the Circular module.
**States:** Loaded / Loading / Empty (new draft) / Error if Near Miss fleet-alert issue fails.
**Navigation:** `[Issue Circular/Alert]` opens the Circular create page with title/body prefilled; `[Issue fleet alert]` records the Near Miss HIGH-alert requirement as issued.
**Decisions:** D-GAP-R22, D-CFG-04, D-GAP-M08.

### 5.6 Near Miss PDF — `/safety/near-miss/:id/pdf/`

**FEAT refs:** FEAT-SAF-PDF-003.
**Role gate:** `PermissionGate(SAF_F_002) + ActionGate(SAF_P_007)`.
**Data loaded on mount:** `GET /api/safety/near-miss/:id/pdf/`.
**Signature transition:** n/a (rendering).
**States:** Loading spinner → Loaded inline viewer → Error "Generation failed — retry".
**Navigation:** Download link.
**Decisions:** D-PDF-03a, D-GAP-J1 revised 2026-06-09.

---

## 6. SCM Module

SCM aligns with KSM SSQE Manual Rev 01 Feb 2026 §9. Regular monthly + Ad-Hoc meetings share the same form + PDF template. Master and CO both have SCM host authority; the user selects `meeting_type` at creation.

### 6.1 SCM List — `/safety/scm/`

**FEAT refs:** FEAT-SAF-SCM-001, FEAT-SAF-SCM-002.
**Role gate:** `PermissionGate(SAF_F_003)`.
**Data loaded on mount:**
- `GET /api/safety/scm/?vessel_id={id}` — list both types; cadence indicator (next due 30 days from last closure, D-GAP-M22).
**Signature transition:** n/a.
**States:**
- **Loaded:** Rows `Meeting type (pill) | Date | Chair | State | Overdue flag`. State labels are user-friendly: `DRAFT` = Draft, `SUBMITTED` = Submitted to Office, `CLOSED` = Closed. Cadence card shows `"Next Regular SCM due: 12-May-2026 (25 days)"`.
- **Loading:** Skeleton.
- **Empty:** `"No SCM records. Master or CO can host the first SCM."`
- **Error:** standard.
**Navigation:**
- `[Host meeting]` with meeting-type dropdown → `/safety/scm/create-regular/` or `/safety/scm/create-adhoc/` (Master or CO).
- Row → `/safety/scm/:id/`.
**Decisions:** D-GAP-M-ADHOC, D-GAP-M22.

### 6.2 Create Regular SCM — `/safety/scm/create-regular/`

**FEAT refs:** FEAT-SAF-SCM-001, FEAT-SAF-SCM-003, FEAT-SAF-SCM-004.
**Role gate:** `PermissionGate(SAF_F_003) + ActionGate(SAF_P_001) + role ∈ {Master, CO}` (D-RBAC-06).
**Data loaded on mount:**
- `GET /api/safety/scm/form-config/` — SCM section template derived from legacy `vw_GetSCM_Master`, with the old reserved Section 2 removed and later sections renumbered.
- `wrh_host_readiness` in form-config — host-readiness result for the selected vessel/date. Hosting is allowed only when ship-time configuration exists and all SCM roster crew have available, compliant WRH data (D-MAINT-CR014).
- `GET /api/safety/scm/closed-since-last/?vessel_id={id}` — for auto-fill block (FEAT-SAF-SCM-006).
- `GET /api/safety/soi/open-findings/?vessel_id={id}` — for Safety Observations auto-fill (FEAT-SAF-SOI-020).
**Signature transition:** None. SCM no longer captures digital signatures.
**States:**
- **Loaded:** SCM form with WRH readiness card and Section 7 SOI summary count + coverage % where SOI data exists. If no SOI inspections exist, the form does not print the old "Section 7 auto-answer NO" text.
- **Loading:** Skeleton.
- **Empty:** New draft — pre-filled vessel + date; free-text sections blank (≥20 chars each).
- **Error — validation:** Section free-text < 20 chars → red block on Submit (VALIDATION_RULES §6). WRH readiness not clear → host action disabled and backend returns `400` with `wrh_host_readiness` (D-MAINT-CR014).
- **Error — network:** Auto-save + queue.
- **Error — auth:** non-Master/non-CO → read-only.
**Navigation:** `[Submit to Office]` saves the meeting and submits it to office only when WRH host readiness is clear. Backend stores `state='SUBMITTED'`; UI displays `Submitted to Office`. PDF download is available immediately after creation/submission. `[Edit Meeting]` remains available to Master/CO until office comment is saved.
**Decisions:** D-RBAC-06, D-PDF-03b, D-SOI-14, D-MAINT-CR014.

### 6.3 Create Ad-Hoc SCM — `/safety/scm/create-adhoc/`

**FEAT refs:** FEAT-SAF-SCM-002.
**Role gate:** `PermissionGate(SAF_F_003) + ActionGate(SAF_P_001) + role ∈ {Master, CO}` (D-GAP-M-ADHOC).
Same form as Regular except `meeting_type='AD_HOC'` and mandatory trigger reason. Cadence counter still anchors on last SCM closure regardless of type (D-GAP-M22). The same WRH host-readiness gate applies before the meeting can be hosted (D-MAINT-CR014).
**States / Navigation:** identical to 6.2 with meeting-type pill shown amber. Ad-Hoc SCM can be edited until office comment closes the meeting.
**Decisions:** D-GAP-M-ADHOC, D-GAP-M22, D-MAINT-CR014.

### 6.4 SCM Detail — `/safety/scm/:id/`

**FEAT refs:** FEAT-SAF-SCM-003, FEAT-SAF-SCM-006, FEAT-SAF-SCM-008.
**Role gate:** `PermissionGate(SAF_F_003)`.
**Data loaded on mount:** `GET /api/safety/scm/:id/`, including agenda + suggestions / recommendations, attendance + WRH snapshot, office comment, and PDF download state.
**Signature transition:** None on read view.
**States:**
- **Loaded:** Meeting-type pill + date + chair + state; `SUBMITTED` is displayed as `Submitted to Office`; SCM sections as horizontal section tabs; Closed-Since-Last block top; Attendance + WRH snapshot visible to ship and office users.
- **Loading:** Skeleton.
- **Empty:** n/a.
- **Error:** standard.
**Navigation:** Sub-tab links listed below. `[Edit Meeting]` is shown only while the meeting is still editable. Editing a Draft meeting and clicking `[Submit to Office]` saves changes and submits it. Once office comment is saved, the meeting state is Closed and edit is stopped.
**Decisions:** D-PDF-03b, D-SOI-14, D-GAP-M22.

### 6.5 SCM Attendance (WRH Join) — `/safety/scm/:id/attendance/`

**FEAT refs:** FEAT-SAF-SCM-005, FEAT-SAF-XMOD-002.
**Role gate:** `PermissionGate(SAF_F_003)` for read. Attendance write/edit is restricted to Master or Chief Officer while the meeting is not closed.
**Data loaded on mount:**
- `GET /api/safety/scm/:id/attendance/` — attendee list from `vims_safety_scm_attendance`; office users can read this WRH snapshot.
- Live join: `GET /api/wrh/rest-hours/?crew_id={id}&window=prior-96h&timezone=via-wrh-ship-time-config` — per attendee (D-GAP-M11, D-GAP-M26).
**Signature transition:** None.
**States:**
- **Loaded:** Table `Name | Rank | Present | WRH flag | Rest 24h | Rest 7d` with badge per row — green (compliant) / amber "WRH data unavailable" / red "Non-compliant".
- **Loading:** Skeleton.
- **Empty:** `"No attendees recorded yet. Add attendees before closing the meeting."`
- **Error — validation:** Created-meeting attendance warnings do not block PDF export or Office Comment closure (D-GAP-M11). New SCM hosting is blocked earlier by WRH host readiness until ship time and all roster crew WRH data are clear (D-MAINT-CR014).
- **Error — network:** WRH unavailable → defaults to "WRH data unavailable" badge on all rows; meeting closure remains possible.
- **Error — auth:** standard.
**Navigation:** `[Back to SCM]`.
**Cross-module join:** **WRH** module via `wrh_ship_time_config` (D-GAP-M26); **CMS** for attendee identity (D-GAP-I2).
**Decisions:** D-GAP-M11, D-GAP-M26, D-GAP-I2.

### 6.6 SCM Agenda / Suggestions and Recommendations — `/safety/scm/:id/agenda/`

**FEAT refs:** FEAT-SAF-SCM-008.
**Role gate:** `PermissionGate(SAF_F_003) + ActionGate(SAF_P_002) + role ∈ {CO, Master}`.
**Data loaded on mount:** `GET /api/safety/scm/:id/agenda/` — rows from `vims_safety_scm_agenda`.
**Signature transition:** None.
**States:** Loaded table `Agenda | Suggestions / Recommendations | Owner | Due | State`. Auto-carry-forward on open items per SSQE §4.5.2. Agenda editing is restricted to Master or Chief Officer until office comment closes the meeting.
**Navigation:** `[+ Add agenda item]`; row click → detail sub-drawer.
**Decisions:** §5.4 SSOT.

### 6.7 Closed-Since-Last-SCM — `/safety/scm/:id/closed-since-last/`

**FEAT refs:** FEAT-SAF-SCM-006, FEAT-SAF-SOI-020.
**Role gate:** `PermissionGate(SAF_F_003)`.
**Data loaded on mount:** `GET /api/safety/scm/:id/closed-since-last/` — SOI findings + Near Miss + Incident records closed since the prior closed SCM timestamp. Closure is anchored by office comment closure for new records, with legacy Master sign-off timestamps used only for old records (D-GAP-M22 cutoff).
**Signature transition:** None.
**States:** Loaded table linking each item to source record via unique-ID (FEAT-SAF-SOI-008). Empty = `"Nothing closed since last SCM."`
**Navigation:** Row click → source record (incident / near miss / SOI detail).
**Decisions:** D-SOI-14, D-GAP-M22.

### 6.8 SCM Office Comment and Closure — SCM detail Office Comment section

**FEAT refs:** FEAT-SAF-SCM-004, FEAT-SAF-SCM-007.
**Role gate:** `PermissionGate(SAF_F_003)` plus office reviewer authority. DPA, FM, Shore HOD, and Marine Superintendent profile `407EF017-0F1C-EF11-A9F1-F348983BAE6B` can save Office Comment.
**Data loaded on mount:**
- `GET /api/safety/scm/:id/` — includes `office_comment`, `office_comment_by`, `office_comment_at`, and `state`.
**Signature transition:** None. SCM does not capture digital signatures in the UI.
**States:**
- **Loaded:** Office Comment text area for permitted office reviewers. The label is `Office Comment`.
- **Closed:** Saving Office Comment sets `state='CLOSED'`, displays `Closed`, and stops further vessel-side editing.
- **Error — validation:** Blank Office Comment cannot close the meeting.
- **Error — network / auth:** standard.
**Navigation:**
- Office saves comment on SCM detail. No `/signoff/` route is used.
- PDF remains downloadable before and after office closure.
**Cross-module join:** SOI overdue and WRH data are shown as information/warnings only; they do not block office closure.
**Decisions:** D-RBAC-06, D-GAP-M20, D-SOI-04, D-GAP-M22.

### 6.9 SCM PDF — `/safety/scm/:id/pdf/`

**FEAT refs:** FEAT-SAF-PDF-004.
**Role gate:** `PermissionGate(SAF_F_003) + ActionGate(SAF_P_007)`.
**Data loaded on mount:** `GET /api/safety/scm/:id/pdf/` — SCM layout with Closed-Since-Last summary block at top, attendance + WRH badges inline, Section 7 PSC findings retained once, and a plain signature box for Master Signature and Chief Officer Signature. No attendee digital signature status is printed.
**States:** Loading → Loaded viewer → Error "Generation failed".
**Decisions:** D-PDF-03b, D-GAP-M-ADHOC.

---

## 7. SOI Module

SOI is **paper-first, no-scan** (D-GAP-E4). 13 areas × 329 items. Section 12 Cross-cutting once per 3-month cycle. Follows this 4-step journey:

### 7.0 Paper-First SOI Journey — 4 Steps (D-GAP-E4)

| # | Step | Screen | User action | State flip |
|---|------|--------|-------------|-----------|
| **1** | **Pick areas + generate unique-ID checklist** | `/safety/soi/create/` → `/safety/soi/:id/pick-areas/` | SO selects areas, Assistant (cross-dept), up to 3 trainees; system issues unique checklist ID | `Draft` → `Ready-to-Download` |
| **2** | **Download paper (PDF or Excel)** | `/safety/soi/:id/download/` | SO chooses PDF/Excel; file is printed; unique checklist ID on every page | `Ready-to-Download` → `Downloaded` |
| **3** | **Fieldwork on paper (offline)** | *no VIMS screen* | SO + Assistant walk the vessel, tick Yes/No/NA on paper, write notes, photograph findings; paper permanently filed in ship SMS filing system — **no scan upload** (D-GAP-E4) | (no state change) |
| **4** | **Register findings digitally via unique-ID link** | `/safety/soi/:id/findings/` + `/findings/create/` | SO returns to VIMS, enters the same unique ID, registers structured findings only (no per-item Yes/No); each finding carries photo for HIGH severity | `Downloaded` → `Submitted` (per area) |

Per D-GAP-E4, the paper is authoritative for per-item responses; the digital record holds **findings only**. The unique-ID prints on every paper page (FEAT-SAF-SOI-008) and is entered when registering findings — this is the sole link between digital and paper. Section 12 (Cross-cutting Safety & Culture) is evaluated once per 3-month cycle regardless of which physical areas are selected (FEAT-SAF-SOI-014, D-GAP-M23).

### 7.1 SOI List — `/safety/soi/`

**FEAT refs:** FEAT-SAF-SOI-001, FEAT-SAF-SOI-005, FEAT-SAF-DASH-005.
**Role gate:** `PermissionGate(SAF_F_004)`.
**Data loaded on mount:**
- `GET /api/safety/soi/?vessel_id={id}&status=all`
- `GET /api/safety/soi/compliance/?vessel_id={id}` — **"SOI Compliance %"** per D-GAP-DESIGN-01 (never "Inspection Compliance %"); amber 80-day, red 90-day per FEAT-SAF-SOI-005.
**Signature transition:** n/a.
**States:**
- **Loaded:** Compliance tile top-left (`SOI Compliance % = X%`), areas-overdue tile, open-findings tile. Table of past SOI events with state pills `Draft / Ready-to-Download / Downloaded / Submitted / Closed`.
- **Loading:** Skeleton tiles + rows.
- **Empty:** New vessel → `"N/A — awaiting first cycle"` on compliance tile (D-GAP-M30); list empty with CTA.
- **Error:** standard.
**Navigation:**
- `[New SOI]` → `/safety/soi/create/`.
- Overdue filter chip → `/safety/soi/?filter=overdue-areas`.
**Decisions:** D-SOI-04, D-SOI-13, D-GAP-DESIGN-01, D-GAP-M30.

### 7.2 Step 1 — Create / Pick Areas — `/safety/soi/create/` + `/safety/soi/:id/pick-areas/`

**FEAT refs:** FEAT-SAF-SOI-001, FEAT-SAF-SOI-003, FEAT-SAF-SOI-004, FEAT-SAF-SOI-009, FEAT-SAF-SOI-010, FEAT-SAF-SOI-014.
**Role gate:** `PermissionGate(SAF_F_004) + ActionGate(SAF_P_001) + role = SO` (CO by default per SSQE §4.5.1; 2/E alternate via D-SOI-02 toggle).
**Data loaded on mount:**
- `GET /api/safety/master/soi-area/?vessel_id={id}` — 13 rows from `master_soi_area` filtered by `vims_safety_soi_vessel_area_map.applicable=true` (D-SOI-12).
- `GET /api/safety/master/soi-checklist-version/active/` — current version (D-SOI-05).
- Live join: `GET /api/cms/crew/?vessel_id={id}&department_ne={soDept}` — for cross-functional Assistant picker (D-GAP-I2, D-SOI-08).
- `GET /api/safety/soi/section-12-status/?vessel_id={id}` — returns whether Section 12 has been covered in current quarter (FEAT-SAF-SOI-014).
**Signature transition:** None — paper signatures captured Step 4.
**States:**
- **Loaded:** Area grid (13 checkboxes) with last-inspected timestamps + tier badges. SO + Assistant pickers; 0–3 Trainee slots. Section 12 banner `"Cross-cutting Safety & Culture not yet covered this quarter — include now?"` (D-GAP-M23).
- **Loading:** Skeleton grid.
- **Empty:** n/a (areas always seeded).
- **Error — validation:** Assistant dept == SO dept → **hard block** banner `"Assistant must be from a different department (SSQE §4.5.2)"` (FEAT-SAF-SOI-009, D-GAP-M18); trainees > 3 → blocked.
- **Error — network:** CMS live join unavailable → CTA greyed `"Crew data temporarily unavailable — retry or defer inspection"` (no manual override per D-GAP-I2).
- **Error — auth:** non-SO → read-only.
**Navigation:**
- `[Save & Continue to Download]` → `/safety/soi/:id/download/` (state flips to `Ready-to-Download`; unique checklist ID generated).
**Decisions:** D-SOI-02 (CO default, 2/E alt), D-SOI-05 (versioned), D-SOI-08/D-GAP-I2/D-GAP-M18 (cross-functional), D-SOI-09 (3 trainees), D-GAP-M23 (Section 12), D-GAP-A4 (no Acting-*).

### 7.3 Step 2 — Download Paper — `/safety/soi/:id/download/`

**FEAT refs:** FEAT-SAF-SOI-006, FEAT-SAF-SOI-007, FEAT-SAF-SOI-008, FEAT-SAF-SOI-023.
**Role gate:** `PermissionGate(SAF_F_004) + ActionGate(SAF_P_001) + role = SO`.
**Data loaded on mount:** `GET /api/safety/soi/:id/` — current selection; pre-computed unique checklist ID.
**Signature transition:**
- **Paper signatures** (SO + Assistant) will be captured on the printed paper during Step 3 fieldwork; the PDF/Excel **includes printed signature lines** (DESIGN_SYSTEM §8.2 / FEAT-SAF-SOI-023, D-GAP-M15). Master signature stays digital, captured at Step 5 approval.
**States:**
- **Loaded:** Format picker (PDF / Excel radio), preview tile, `[Download]` CTA. Reprint counter visible (idempotent per D-GAP-E1).
- **Loading:** `"Generating paper checklist…"` spinner.
- **Empty:** n/a.
- **Error — validation:** No areas selected → red block (should have been caught at Step 1).
- **Error — network:** Retry.
- **Error — auth:** standard.
**Navigation:**
- `[Download PDF]` → file download + state flips to `Downloaded` on first call.
- `[Download Excel]` → same.
- `[Back]`, `[Go to Findings]` → `/safety/soi/:id/findings/`.

**Fieldwork (Step 3)** occurs offline on paper — no VIMS screen. Paper is filed in ship SMS filing system on completion (D-GAP-E4). **No scan upload path.**

**Decisions:** D-SOI-10, D-GAP-E4 (no scan), D-GAP-E1 (idempotent), D-GAP-M15 (paper sigs SO+Assistant; Master digital).

### 7.4 Step 4 — Register Findings — `/safety/soi/:id/findings/`

**FEAT refs:** FEAT-SAF-SOI-011, FEAT-SAF-SOI-012, FEAT-SAF-SOI-013, FEAT-SAF-SOI-016, FEAT-SAF-SOI-017, FEAT-SAF-SOI-018.
**Role gate:** `PermissionGate(SAF_F_004) + ActionGate(SAF_P_002) + role = SO`.
**Data loaded on mount:**
- `GET /api/safety/soi/:id/findings/`
- `GET /api/safety/master/mscat/` — optional M-SCAT tagging.
**Signature transition:**
- Each finding save captures SO digital signature (implicit via `created_by` + device fingerprint).
**States:**
- **Loaded:** Findings table + `[+ Add Finding]`. Top banner reminds SO to enter the unique checklist ID (must match the one on paper); partial-submission indicator `"2 of 5 areas complete"` (FEAT-SAF-SOI-012).
- **Loading:** Skeleton.
- **Empty:** `"No findings registered. Select an area and add findings — or submit with zero findings (areas still stamp as inspected)."`
- **Error — validation:** HIGH severity without ≥1 photo → red block (D-GAP-M24). Unique-ID mismatch → amber warning.
- **Error — network:** Queue + retry.
- **Error — auth:** non-SO → read-only.
**Navigation:**
- `[+ Add Finding]` → `/safety/soi/:id/findings/create/`.
- `[Submit Area N]` → per-area submit (D-GAP-E2 partial submission).
- `[Lost paper? Re-download]` → opens recovery modal (FEAT-SAF-SOI-013, D-GAP-E3).
**Decisions:** D-SOI-10, D-GAP-E2, D-GAP-E3, D-GAP-E4, D-GAP-M24, D-GAP-M16 ("Incident-worthy?" nudge).

### 7.5 Finding Create — `/safety/soi/:id/findings/create/`

Form: `area_id · item_id · description · priority (High/Med/Low) · photo (mandatory if High) · proposed_action · assigned_to (default SO per D-GAP-E7) · due_date · MSCat code optional`.
**HIGH-severity nudge modal** fires on save (D-GAP-M16): `"This looks incident-worthy. Create an Incident now? [Yes / No + reason]"` — No path captures mandatory reason into finding notes. No auto-escalation (D-SOI-06).
**Decisions:** D-GAP-M16, D-GAP-M24, D-GAP-E7, D-SOI-06.

### 7.6 Finding Closure (SO → Master) — `/safety/soi/:id/findings/:findId/`

**FEAT refs:** FEAT-SAF-SOI-015.
**Role gate:** `PermissionGate(SAF_F_004)`; SO can mark `pending_closure`; Master approves closure.
**Data loaded on mount:** `GET /api/safety/soi/:id/findings/:findId/`.
**Signature transition:**
- SO signature on `pending_closure` mark.
- **Master** digital signature on approval (DESIGN_SYSTEM §8.2) — captured here as Master counter-signature per D-GAP-M15.
- DPA safety-net re-open signature (if applicable).
**States:**
- **Loaded:** Finding detail + status lifecycle panel (`Open → Pending Closure → Master-Approved → Closed`, `Carried Forward` possible).
- **Loading:** Skeleton.
- **Empty:** n/a.
- **Error — validation:** Master rejection without reason → red block (D-GAP-M21); reason appended to finding notes, status returns to Open.
- **Error — network / auth:** standard.
**Navigation:** Back to findings list; link to SCM if Closed-Since-Last feeds FEAT-SAF-SCM-006.
**Decisions:** D-SOI-07, D-GAP-M21.

### 7.7 Area-Applicability Workflow — `/safety/soi/:id/applicability/request/` + `/applicability/approve/`

**FEAT refs:** FEAT-SAF-SOI-002.
**Role gate:** Request = `role = Master` (`SAF_P_011`); Approve = `role = DPA` (`SAF_P_010`).
**Data loaded on mount:** area list + current `applicable` flag from `vims_safety_soi_vessel_area_map`.
**Signature transition:** Master signature on request, DPA signature on approval; both logged to `vims_safety_soi_applicability_log` (D-GAP-M19).
**States:**
- **Loaded:** Request form (area · reason ≥100 chars); DPA approval panel with reject/approve + reason.
- **Loading:** Skeleton.
- **Empty:** n/a.
- **Error — validation:** reason < 100 chars → red block.
- **Error — network / auth:** standard.
**Navigation:** On DPA approve → area flag flipped; does not count toward 90-day compliance counter (D-SOI-12).
**Decisions:** D-SOI-12, D-GAP-M19.

### 7.8 SOI Close Event — `/safety/soi/:id/close/`

**FEAT refs:** FEAT-SAF-SOI-011 (submit-with-no-findings path).
**Role gate:** `PermissionGate(SAF_F_004) + ActionGate(SAF_P_004) + role = Master`.
**Signature transition:** Master final digital signature.
**States:** Standard. Close flips state to `Closed`; all selected areas stamp `last_inspected_at = now()` (D-SOI-04 90-day counter reset).
**Navigation:** Back to SOI list; link to SCM Closed-Since-Last feed.
**Decisions:** D-SOI-04, D-SOI-10, D-GAP-M15.

### 7.9 SOI Summary PDF — `/safety/soi/:id/pdf/`

**FEAT refs:** FEAT-SAF-PDF-005.
**Role gate:** `PermissionGate(SAF_F_004) + ActionGate(SAF_P_007)`.
**Data loaded on mount:** `GET /api/safety/soi/:id/pdf/`.
Standard loaded/loading/error.
**Note:** Per D-GAP-E4, PDF does **not** reproduce per-item Yes/No checklist data — paper is authoritative. Paper-reference footer reads `"Paper checklist: unique-ID {id}, filed in ship SMS filing system"`.

---

## 8. Dashboards, Search, Exports

### 8.1 Safety Intelligence Dashboard — `/safety/dashboard/`

**FEAT refs:** FEAT-SAF-DASH-001 through FEAT-SAF-DASH-009.
**Role gate:** `PermissionGate(SAF_F_005) + role ∈ {DPA, FM, TD, HOD (shore), Master (own vessel view)}`.
**Data loaded on mount:**
- `GET /api/safety/dashboard/composite/?period={p}` — composite Safety Health Score.
- Panels loaded in parallel: Heinrich (FEAT-SAF-DASH-002), Repeat-root-cause (DASH-003), Pareto (DASH-004), SOI Compliance % (DASH-005, label per D-GAP-DESIGN-01), CA Aging (DASH-006).
**Signature transition:** n/a.
**States:**
- **Loaded:** Grid of panels; period selector; export button (DPA-only `SAF_P_007`).
- **Loading:** Skeleton panel grid.
- **Empty per panel:** e.g., Heinrich `"Reporting Culture Gap — insufficient data"` (D-GAP-M27). SOI compliance on new vessel → `"N/A — awaiting first cycle"` (D-GAP-M30).
- **Error — network:** per-panel error badges; other panels continue.
- **Error — auth:** FM sees dashboards but **no export** (D-GAP-M31).
**Navigation:**
- Panel click → drill-down screens (e.g., Pareto → Incident list filtered; CA Aging → CA list).
- `[Export PDF / Excel]` — DPA only.
**Decisions:** D-GAP-DESIGN-01 (label), D-GAP-M30 (edge case), D-GAP-M31 (export), D-DNV-13/D-GAP-M27/D-GAP-H2, D-GAP-R17 (Pareto), D-GAP-M29 (CA aging).

### 8.2 Cross-record Search — `/safety/search/`

**FEAT refs:** FEAT-SAF-DASH-008.
**Role gate:** `PermissionGate(SAF_F_005)`.
**Data loaded on mount:**
- `GET /api/safety/search/?q={q}&include_archived={bool}&record_type={filter}`.
- FTS engine is a **build-time deferral** (Round 20 / Phase 7) — BLOCKED stub below.

> **BLOCKED: FTS engine selection**
> **Question:** Elasticsearch, PostgreSQL FTS, or platform-default (SQL Server FTS)?
> **Gap:** Round 20 deferred this to build-time; no D-* locks it.
> **Impact:** Search ranking, highlighting, and fuzzy-match behaviour for FEAT-SAF-DASH-008 cannot be fully specified in APP_FLOW pending build-time choice.

**Signature transition:** n/a.
**States:**
- **Loaded:** Search bar + `[ ] Include archived records` opt-in checkbox (default off, D-GAP-M32). Result groups by record type (Incident / Near Miss / SCM / SOI).
- **Loading:** Skeleton.
- **Empty:** `"No matches. Try including archived records?"`
- **Error — validation:** < 3 chars query → soft block.
- **Error — network / auth:** standard.
**Navigation:** Result click → record detail.
**Decisions:** D-GAP-M32.

### 8.3 Taxonomy Admin — `/safety/admin/*` (DPA only)

**FEAT refs:** FEAT-SAF-RBAC-008, FEAT-SAF-DASH-009.
**Role gate:** `PermissionGate(SAF_F_006) + role = DPA`.
**Sub-routes:**
- `/admin/mscat/` — edit `master_mscat_taxonomy` (174 rows). Config-change log row per modification (D-CFG-01).
- `/admin/soi-template/` — edit `master_soi_area` (13) and `master_soi_area_item` (329); versioned via `master_soi_checklist_version` (D-SOI-05, D-GAP-M05).
- `/admin/bias-guards/` — read-only list of 8 rows (D-GAP-R12).
- `/admin/case-studies/` — Navigator + Sinkfast + user-added (D-CFG-02).
**Signature transition:** DPA digital signature on every save (typed name + timestamp + device fingerprint per D-GAP-D1).
**States:** Standard.
**Decisions:** D-CFG-01/02/03, D-GAP-R15 (10.15 subcode), D-SOI-05, D-GAP-R12.

---

## 9. Cross-Module Navigation Paths

All cross-module joins use **same-DB live queries** — no ETL, no sync staleness (D-GAP-I2). `ksm_marine_live` is the single shared connection.

| Path | From (Safety screen) | To (sibling module) | Navigation affordance | Decision |
|------|----------------------|--------------------|------------------------|----------|
| **Incident → Reporting Daily Report (position auto-fill)** | `/safety/incidents/:id/phase-1/` banner | `/reporting/noon-reports/:ref/` | Amber "Position auto-filled from Daily Report {ref}. Click to view source." Clicking opens Reporting detail in new tab | **D-GAP-M09** · **D-GAP-M10** · **D-DNV-12** · FEAT-SAF-XMOD-001 |
| **Incident → Reporting Daily Report (MSC-MEPC.3 PDF export)** | `/safety/incidents/:id/pdf/mscmepc3/` generator | `vims_reporting_daily_report` live join | Internal — user doesn't navigate; PDF pre-fills App 4 directly | **D-GAP-M09** · **D-DNV-12** · FEAT-SAF-PDF-002 |
| **Incident → CMS crew roster (crew assignment / witness picker)** | `/safety/incidents/:id/phase-4/people/` | `Crew_Onboarding_History` + `Final_crew_list` live join | In-line picker dropdown returns crew; click opens CMS crew card in slide-over | **D-GAP-I2** · FEAT-SAF-XMOD-003 |
| **Incident → CMS (qualifications snapshot at event time)** | Phase-3 People tab record display | Same live join, historical filter `active_on={incidentDate}` | Snapshot captured at Phase 1 submit; read-only thereafter | **D-GAP-I2** |
| **SCM → WRH host readiness and attendance** | `/safety/scm/create-*` readiness card and `/safety/scm/:id/attendance/` table badges | `vims_wrh_rest_hours` + `wrh_ship_time_config` live join | SCM hosting is blocked until ship time and all roster crew WRH readiness are clear; after creation, per-row badges remain visible and do not block PDF export or Office Comment closure | **D-MAINT-CR014** · **D-GAP-M11** · **D-GAP-M26** · FEAT-SAF-XMOD-002 |
| **Corrective Action → Purchase Requisition (hard FK)** | Corrective Action row from `/safety/incidents/:id/phase-3/` | `/purchase/requisitions/create?linked_safety_ca={caId}` or `/purchase/requisitions/:reqId` | Hard FK = Purchase Req cannot be archived while open CA linked; CA detail shows live Req status | **D-GAP-M12** · FEAT-SAF-XMOD-004 |
| **SOI assistant picker → CMS** | `/safety/soi/create/` | `Crew_Onboarding_History` live join with cross-department filter | Picker enforces cross-dept (SSQE §4.5.2); no manual override | **D-GAP-I2** · **D-GAP-M18** · FEAT-SAF-XMOD-003 |
| **Near Miss fleet alert → Circular module** | `/safety/near-miss/:id/fleet-alert/` `[Issue Circular/Alert]` | `/circular/office?safety_prefill=near_miss_fleet_alert` | Opens existing Circular create flow with title/body prefilled from the anonymised Near Miss alert; DPA completes all remaining Circular fields and publishes there. Safety does not direct-create the circular. | **D-CFG-04** · **D-GAP-M08** · FEAT-SAF-NM-006 |
| **Legacy backend verification → PSC Physical Verification (Inspection module)** | `/safety/incidents/:id/phase-8/` | `vims_psc_physical_verification` live join | Status shown inline; CA close independent of PV close (separate tracks) | **D-EDGE-06** · **D-GAP-M03** · FEAT-SAF-INC-031 |
| **Safety → PMS (DECOUPLED)** | Phase-3 Parts tab text note | *No link* | Note: `"PMS equipment history: cross-reference manually — PMS is standalone (D-GAP-I1)."` **No navigation path. No FK. No live join.** | **D-GAP-I1** · FEAT-SAF-XMOD-005 |
| **Safety → master_notification** | All screens that send notifications | Shared notification queue | Internal write; user doesn't navigate. Slack best-effort + in-app authoritative | **D-GAP-F2** · **D-GAP-M28** · **D-GAP-F4** · FEAT-SAF-XMOD-006 |

### 9.1 Explicit exclusion — PMS

Per **D-GAP-I1**, the Safety module has **no navigation to PMS**. There is no link, no FK, no live join, no API call. Investigators on M-SCAT cause 12 "Inadequate Maintenance" findings must cross-reference PMS manually via a separate PMS login (PMS is standalone). Equipment defects surfaced in SOI findings also do not link to PMS. Every PMS-adjacent UI location shows the note `"PMS equipment history: cross-reference manually — PMS is standalone (D-GAP-I1)."` — and nothing else. This is the negative contract enforced at every build-time review.

---

## 10. Signature Sequencing

Per SSQE Manual Rev 01 Feb 2026 §11 and DESIGN_SYSTEM §8.2, the canonical signature chain is **Reporter → Master → HOD → DPA → FM** (as applicable by band / module). The frontend renders each slot via the `<SignatureBlock role={…} state={awaiting|signed}>` component (DESIGN_SYSTEM §8.2). Out-of-order submission blocked client + server (VALIDATION_RULES §3).

Current Incident PDFs render the Office Review decision slot as PIC / DPA office signature for every risk band. Older per-band signature rows in this section are legacy background and are superseded by D-MAINT-CR044 for the current Incident Office Review path.

### 10.1 Signature chain per module

| Module | Signature order | Notes |
|--------|-----------------|-------|
| **Incident (GREEN)** | Reporter → Master → HOD → PIC | HOD signs department-level review at Phase 6; PIC is closer at Phase 7 (D-RBAC-01). PIC signature functionally occupies the "closer" slot. |
| **Incident (YELLOW)** | Reporter → Master → HOD → DPA | DPA closer at Phase 7. |
| **Incident (RED)** | Reporter → Master → HOD → DPA → FM | FM closer at Phase 7 with full-edit authority (D-GAP-M06). External expert signature stored as attachment, not in formal chain. |
| **Near Miss (LOW)** | Reporter → PIC (closer) | Reporter details are visible to Master and authorized users within vessel scope. |
| **Near Miss (HIGH)** | Reporter → Master → HOD → DPA (fleet alert issuer) | Reporter details remain visible to authorized users. |
| **SCM Regular** | No digital signature capture | Master or CO creates/edits; office saves Office Comment to close. PDF has blank Master/CO signature lines only. |
| **SCM Ad-Hoc** | No digital signature capture | Same host authority; `meeting_type='AD_HOC'` requires trigger reason. Office Comment closes the record. |
| **SOI event** | SO (paper) + Assistant (paper) → Master (digital approval at closure) | Trainees do not sign (D-GAP-M15). Master's digital counter-signature is what closes the SOI event. |
| **SOI finding** | SO → Master (approval) → DPA (safety-net re-open if needed) | Per D-SOI-07 / D-GAP-M21. |
| **SOI area-applicability toggle** | Master (request) → DPA (approval) | D-GAP-M19. |

### 10.2 Signature block visual states

Per DESIGN_SYSTEM §8.2:
- **Awaiting** — `neutral-100` bg, dashed `neutral-300` border, label `"Awaiting <Role>"`.
- **Signed** — role-specific solid token (`--safety-sig-reporter / master / hod / dpa / fm`), typed name + ISO-8601 timestamp + device fingerprint on a single line.
- **Rejected / Sent back** — amber border + reason panel.

### 10.3 Hybrid model (D-GAP-D1)

All digital signatures are captured as **typed name + timestamp + device fingerprint** — no PKI / UETA in V1 (D-GAP-D2). For formal PDFs intended for flag-state / auditor hand-off, a wet-signed scan is accepted as an **additional attachment** on the same record. The APP_FLOW never surfaces a cryptographic-signature UI surface — VALIDATION_RULES §7 enforces the "no crypto in V1" rule.

---

## 11. Mobile / Tablet Breakpoints

Per D-GAP-M34:
- **Desktop (≥1280px)** — primary for Shore roles (DPA/FM/TD/HOD-shore) and office analytics.
- **Tablet (≥768px)** — **primary SOI device** per mobile-first mandate. SOI pick-areas screen is single-column at 768px portrait; Incident Evidence uses one Documents form rather than a horizontal category tab bar.
- **Phone (≤480px)** — **read-only dashboards in V1**; CRUD deferred to V2.

Every screen in this APP_FLOW follows the DESIGN_SYSTEM §9 breakpoint rules; no screen-specific overrides.

---

## 12. Appendix — FEAT-SAF-* → Screen Coverage Matrix

Every PRD V1 feature must map to ≥1 screen or route. `R` = referenced on screen; `P` = primary screen for this feature.

| FEAT ID | Primary screen(s) | Referenced-on screens |
|---------|-------------------|------------------------|
| FEAT-SAF-INC-001 | P: `/safety/incidents/create/` + phase-1 | R: list, audit |
| FEAT-SAF-INC-002 | P: `/phase-2/` (classifier) | R: closure, PDF |
| FEAT-SAF-INC-003 | P: `/phase-2/` (band) | R: list, dashboard |
| FEAT-SAF-INC-004 | P: `/phase-2/` | R: notifications (system-level) |
| FEAT-SAF-INC-005 | P: `/phase-4/*` | R: Phase 4 facts |
| FEAT-SAF-INC-006 | Legacy compatibility only; no current Phase 4 route | R: Historical DNV confirmation-bias reference |
| FEAT-SAF-INC-007 | P: `/phase-3/chain-of-custody/` | R: PDF section 3 |
| FEAT-SAF-INC-008 | P: `/phase-4/paper/` auto-checklist | R: PDF |
| FEAT-SAF-INC-009 | R: overlay inside `/phase-4/paper/` | — |
| FEAT-SAF-INC-010 | R: sub-section in `/phase-4/people/` | WRH live join |
| FEAT-SAF-INC-011 | P: Phase-3 `[Schedule deadline tasks]` modal | R: dashboard |
| FEAT-SAF-INC-012 | P: `/phase-3/interview/:intId/` | R: People tab |
| FEAT-SAF-INC-013 | R: interview detail picklist | — |
| FEAT-SAF-INC-014 | R: interview detail checklist | — |
Note: FEAT-SAF-INC-012 through FEAT-SAF-INC-014 are superseded for the current user-facing Phase 4 Witness Statement route by D-MAINT-CR016, D-MAINT-CR036, and D-MAINT-CR049. Current users open `/phase-4/interviews/`, choose a crew witness or Other typed name, enter Remark, and may upload a witness statement; formal/informal, text statement, and read-back/copy-to-witness controls remain legacy API compatibility.

| FEAT-SAF-INC-015 | P: `/phase-4/` | R: Phase 5 analyses |
| FEAT-SAF-INC-016 | P: `/phase-5/` (loop-back CTA) | R: Phase 4/6 |
| FEAT-SAF-INC-017 | P: `/phase-5/analysis/*` + `/admin/mscat/` | R: Phase 6 |
| FEAT-SAF-INC-018 | P: `/phase-5/causal-layering/` | R: PDF |
| FEAT-SAF-INC-019 | R: Phase 5 validation | — |
| FEAT-SAF-INC-020 | P: `/phase-5/analysis/*` | R: Phase 4 |
| FEAT-SAF-INC-021 | R: top-panel depth triangle at Phase 5 | — |
| FEAT-SAF-INC-022 | R: Phase 5 summary narrative section | — |
| FEAT-SAF-INC-023 | R: Barrier Analysis tool | — |
| FEAT-SAF-INC-024 | R: Phase 4→5 and 5→6 transitions | `/admin/bias-guards/` |
| FEAT-SAF-INC-025 | R: Phase 6→7 transition modal | — |
| FEAT-SAF-INC-026 | P: `/phase-5/human-factors/` | — |
| FEAT-SAF-INC-027 | P: `/phase-6/` | R: PDF |
| FEAT-SAF-INC-028 | R: Phase 6 System Action rows | — |
| FEAT-SAF-INC-029 | R: Phase 1 tile (GREEN only, V1.1) | R: Pareto dashboard |
| FEAT-SAF-INC-030 | P: `/phase-7/` | — |
| FEAT-SAF-INC-031 | P: `/phase-8/` | R: verification sub-route |
| FEAT-SAF-INC-032 | R: create-incident duplicate modal | R: list filter |
| FEAT-SAF-INC-033 | R: detail `[Supersede as {other_type}]` | — |
| FEAT-SAF-INC-034 | R: Phase 1 crew/non-crew injury section | — |
| FEAT-SAF-INC-035 | P: `/safety/incidents/:id/reopen/` | — |
| FEAT-SAF-INC-036 | R: every phase allows draft save | — |
| FEAT-SAF-INC-037 | System-level; surfaced on dashboard | — |
| FEAT-SAF-INC-038 | System-level; surfaced on list row badge | — |
| FEAT-SAF-INC-039 | R: Phase 1 submit validation | — |
| FEAT-SAF-INC-040 | R: header on every incident screen | — |
| FEAT-SAF-INC-041 | R: Phase 1 position block + MSC-MEPC.3 PDF | — |
| FEAT-SAF-NM-001 | P: `/safety/near-miss/create/` | R: list |
| FEAT-SAF-NM-002 | P: detail (every near-miss screen) | R: PDF, list |
| FEAT-SAF-NM-003 | P: `/safety/near-miss/:id/triage/` (Office Comments) | R: detail |
| FEAT-SAF-NM-004 | P: `/safety/near-miss/:id/` | — |
| FEAT-SAF-NM-005 | R: create screen minimum-detail validation | — |
| FEAT-SAF-NM-006 | P: `/safety/near-miss/:id/fleet-alert/` | R: Circular module |
| FEAT-SAF-SCM-001 | P: `/safety/scm/create-regular/` | R: list cadence |
| FEAT-SAF-SCM-002 | P: `/safety/scm/create-adhoc/` | — |
| FEAT-SAF-SCM-003 | P: create + detail | R: PDF |
| FEAT-SAF-SCM-004 | P: SCM detail Office Comment | R: closed state/edit lock |
| FEAT-SAF-SCM-005 | P: `/attendance/` | R: SCM detail WRH snapshot |
| FEAT-SAF-SCM-006 | P: `/closed-since-last/` | R: detail top |
| FEAT-SAF-SCM-007 | R: SCM detail warning | SOI list link |
| FEAT-SAF-SCM-008 | P: `/agenda/` | — |
| FEAT-SAF-SOI-001 | P: `/safety/soi/create/` + `/admin/soi-template/` | — |
| FEAT-SAF-SOI-002 | P: `/applicability/request/` + `/approve/` | — |
| FEAT-SAF-SOI-003 | R: every create screen | `/admin/soi-template/` |
| FEAT-SAF-SOI-004 | R: create Step 1 | — |
| FEAT-SAF-SOI-005 | R: list compliance tile | — |
| FEAT-SAF-SOI-006 | P: `/:id/download/` | — |
| FEAT-SAF-SOI-007 | R: reprint counter on download | — |
| FEAT-SAF-SOI-008 | R: download + findings screens | — |
| FEAT-SAF-SOI-009 | R: Step 1 assistant picker | — |
| FEAT-SAF-SOI-010 | R: Step 1 trainee picker | R: crew coverage dashboard |
| FEAT-SAF-SOI-011 | P: `/findings/` + `/findings/create/` | — |
| FEAT-SAF-SOI-012 | R: findings screen partial submit | — |
| FEAT-SAF-SOI-013 | R: findings `[Lost paper?]` modal | — |
| FEAT-SAF-SOI-014 | R: Step 1 Section 12 banner | — |
| FEAT-SAF-SOI-015 | P: `/findings/:findId/` | — |
| FEAT-SAF-SOI-016 | R: finding create validation | — |
| FEAT-SAF-SOI-017 | R: finding save nudge modal | — |
| FEAT-SAF-SOI-018 | R: finding → Incident/Near Miss CTA | — |
| FEAT-SAF-SOI-019 | R: finding badge + dashboard tile | — |
| FEAT-SAF-SOI-020 | R: SCM `/closed-since-last/` + Section 7 auto-fill | — |
| FEAT-SAF-SOI-021 | R: finding create `assigned_to` default | — |
| FEAT-SAF-SOI-022 | R: dashboard + SCM analytics | — |
| FEAT-SAF-SOI-023 | R: download paper signature lines | — |
| FEAT-SAF-SOI-024 | System-level; SO-role resolution | — |
| FEAT-SAF-XMOD-001 | R: Phase 1 + MSC-MEPC.3 PDF | — |
| FEAT-SAF-XMOD-002 | R: `/safety/scm/:id/attendance/` | — |
| FEAT-SAF-XMOD-003 | R: SOI Step 1 + Incident Phase 3 People | — |
| FEAT-SAF-XMOD-004 | R: Phase 6 CA row + CA aging dashboard | — |
| FEAT-SAF-XMOD-005 | R: note on Phase 3 Parts tab (decoupled) | — |
| FEAT-SAF-XMOD-006 | System-level; no UI surface | — |
| FEAT-SAF-PDF-001 | P: `/safety/incidents/:id/pdf/incident/` | — |
| FEAT-SAF-PDF-002 | P: `/safety/incidents/:id/pdf/mscmepc3/` | — |
| FEAT-SAF-PDF-003 | P: `/safety/near-miss/:id/pdf/` | — |
| FEAT-SAF-PDF-004 | P: `/safety/scm/:id/pdf/` | — |
| FEAT-SAF-PDF-005 | P: `/safety/soi/:id/pdf/` | — |
| FEAT-SAF-PDF-006 | P: `/safety/incidents/:id/pdf/auditor-zip/` | — |
| FEAT-SAF-AUDIT-001 | P: `/safety/incidents/:id/audit/` | — |
| FEAT-SAF-AUDIT-002 | P: audit screen diff panel | — |
| FEAT-SAF-AUDIT-003 | R: signature blocks across all screens | — |
| FEAT-SAF-AUDIT-004 | R: archive toggle on search | — |
| FEAT-SAF-AUDIT-005 | R: schema version stamp on create screens | — |
| FEAT-SAF-AUDIT-006 | R: auto-save draft persistence across forms; Phase 1 keeps the header free of internal incident-id and auto-save badges | CR-026 |
| FEAT-SAF-AUDIT-007 | System-level; no UI surface | — |
| FEAT-SAF-DASH-001 | P: `/safety/dashboard/` | — |
| FEAT-SAF-DASH-002 | R: Heinrich panel | — |
| FEAT-SAF-DASH-003 | R: repeat-root radar panel | — |
| FEAT-SAF-DASH-004 | R: Pareto panel | — |
| FEAT-SAF-DASH-005 | R: SOI Compliance % panel + SOI list tile | **Label per D-GAP-DESIGN-01** |
| FEAT-SAF-DASH-006 | R: CA Aging panel | — |
| FEAT-SAF-DASH-007 | R: dashboard export button | — |
| FEAT-SAF-DASH-008 | P: `/safety/search/` | — |
| FEAT-SAF-DASH-009 | R: M-SCAT help drawer + `/admin/case-studies/` | — |
| FEAT-SAF-RBAC-001 | R: Phase-7 closer role | — |
| FEAT-SAF-RBAC-002 | R: create-incident action gate | — |
| FEAT-SAF-RBAC-003 | R: Blame-Fixation override modal (Phase 6→7) | — |
| FEAT-SAF-RBAC-004 | System-level; applied at all role gates | — |
| FEAT-SAF-RBAC-005 | System-level; applied at all routes | — |
| FEAT-SAF-RBAC-006 | R: list cross-vessel filter + NM fleet-alert | — |
| FEAT-SAF-RBAC-007 | R: Phase-3/4/5/6 edit gate RED-band | — |
| FEAT-SAF-RBAC-008 | R: `/admin/*` gate | — |

---

## Self-Check (authoring compliance)

- [x] Every `FEAT-SAF-*` V1 feature from PRD maps to ≥1 screen or route (§12 matrix).
- [x] Every screen documents loaded / loading / empty / error states (§§4–8).
- [x] Role-permission matrix present (§1) — 10 roles × module actions.
- [x] Cross-module navigation paths explicit (§9) — Reporting / WRH / CMS / Purchase covered; PMS **explicitly excluded** with inline note.
- [x] Near-miss reporter identity visibility subsection present (§5.3 table).
- [x] Paper-first SOI 4-step journey present (§7.0 table).
- [x] Signature sequencing Reporter → Master → HOD → DPA → FM referenced (§10.1 table).
- [x] Zero bare `safety_*` prefixes — all use `vims_safety_*` (module) or `master_*` (reference).
- [x] No "Acting-*" concepts anywhere (§1 note, §10, FEAT-SAF-RBAC-004 reference).
- [x] "SOI Compliance %" label used throughout — never "Inspection Compliance %" (§7.1, §8.1, §12 note).

**Open BLOCKED stubs:**
- §8.2 — FTS engine selection (build-time deferral, Round 20).

**End of APP_FLOW.**
