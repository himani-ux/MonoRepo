# VALIDATION_RULES.md — VIMS Safety Module Input & Compliance Rules

> **Canonical rule-set for validation, compliance, rate-limiting, and phase-gate enforcement across the four V1 sub-features: Incident, Near Miss, Safety Committee Meeting (SCM), Safety Officer Inspection (SOI).**
>
> **Authority order** (per `CLAUDE.md` arbitration rule): SSOT (`VIMS-SAFETY-MODULE-SSOT.md`) > `BACKEND_STRUCTURE.md` > `APP_FLOW.md` > `PRD.md` > `DESIGN_SYSTEM.md` > `VALIDATION_RULES.md`. Within this doc, naming convention `<database_naming_convention>` overrides SSOT table names.
>
> **Every rule below is either a D-* decision or a Round 20/21 directive.** No speculative validations. No crypto in V1 (D-GAP-D2 / D-GAP-G2).

**Glossary** (first-use expansions per master prompt): DPA = Designated Person Ashore (ISM Code 2010 amendments §4); FM = Fleet Manager; TD = Technical Director; HOD = Head of Department; CO = Chief Officer; CE = Chief Engineer; SO = Safety Officer (SOLAS Reg VI); SCM = Safety Committee Meeting; SOI = Safety Officer Inspection; MoC = Management of Change; RCA = Root Cause Analysis; CA = Corrective Action; PA = Preventive Action; ALARP = As Low As Reasonably Practicable; SMC = Serious Marine Casualty (IMO Casualty Investigation Code); MC = Marine Casualty; MI = Marine Incident; WRH = Work & Rest Hours module; CMS = Crew Management System module; PMS = Planned Maintenance System module; SSQE = Safety, Security, Quality & Environment.

**Identifier validation note:** Path identifiers on Safety-owned managed endpoints are UUID `id` primary keys. Validation must resolve the record first, then apply the same state, role, vessel-scope, signature, rate-limit, and phase-gate rules. User-facing reference numbers are not identifiers for route resolution unless a dedicated lookup endpoint explicitly says so.

**Reference validation note:** Safety-owned child rows store UUID-compatible references to Safety-owned parent rows. Polymorphic references must include the record/source type discriminator plus UUID value. External/shared VIMS identifiers remain in their original format and are not converted by Safety validation.

**Master/reference validation note:** Safety-owned master/reference rows use UUID `id` as the actual database primary key. Stable natural keys remain authoritative for their domains, for example M-SCAT `subcode_id`, loss `loss_type_id`, SOI `area_id`, bias guard `guard_code`, Near Miss cause option `option_code`, and the injury dropdown `field_key` values used for `TYPE_OF_ACTIVITY`, `NATURE_OF_INJURY`, `SOURCE_OF_INJURY`, and `AFFECTED_BODY_AREA`.

**Incident simplification validation update (2026-07-07):** For incident records, current validation follows the simplified flow in `safety_ssot/VIMS-SAFETY-MODULE-SSOT.md` section 3.0. Binding rules are: narrative minimum still applies; occurred/reported timestamps cannot be in the future or reversed; vessel scope is enforced; reporter identity is required; risk band is required; investigation depth is derived from risk band; office communication is required as yes/no using "Was office informed?", and mode is required only when yes using "How was office informed?"; the current mode dropdown offers On call and On email only; Report time and Shore Assistance Required are visible together on one Phase 1 row; latitude and longitude are visible together on their own Phase 1 row and stored on the incident record; Shore Assistance Required, Location of Vessel, Location on Board, Departure Date, and Vessel Condition are nullable visible Phase 1 incident-reporting context fields; Last Port remains legacy storage only and is not shown or sent by the current frontend; Weather ice-condition fields remain legacy storage only and are not shown or sent by the current Weather Condition UI; up to three loss types are allowed including `Other`; `Other` requires text. Corrective Action and Preventive Action are separate visible screens; Corrective Action validates user-visible Description and Due date, not owner/checker fields; Preventive Action validates Description, Due date, and one shared How much will this reduce risk? answer for the screen, and does not validate a user-visible Remaining risk field, risk-confirmation checkbox, theme, or effort. Office Review send-back validates only the rework comment in the current UI and sends the fixed action-rework target. Ship-side Office Review shows a pending message when no office comment exists. Loss Evaluation save is available to authorized ship-side and office-side users with incident form access and vessel scope without waiting for Office Review approval; the current UI requires the user to select Incident Report or Injury Report first and persists that selection as nullable `report_type`; closure still requires a saved Loss Evaluation row and office close authority. Incident PDF preview/download and MSC-MEPC.3/Circ.4 export are not blocked solely by pending Phase 7 acceptance; record-type and regulatory applicability checks still apply. The former Lessons Learned screen is removed from current navigation and its old route redirects to Office Review. The former Phase 1 first-check gate is removed from the current UI/API/PDF flow under `D-MAINT-CR018`. User-entered IMO classifier, resource handoff, link-to-existing-finding, and mandatory bias-filter gates are superseded for the simplified V1 UI.

**Incident Phase 2-6 editability update (2026-07-03):** RCA, facts/evidence helpers, Corrective Action, Preventive Action, Evidence Documents, and Witness Statements save endpoints remain editable for authorized users until office approval, closure, or supersession, regardless of legacy backend `current_phase` numbering. Saved RCA causes, action cards, evidence document metadata, and Witness Statement cards expose Edit controls that update the existing row instead of adding duplicates. Submit/continue endpoints still enforce ordered workflow movement. Office Review captures optional Office Comments with no word or character limit.

---

## 1. Global Rules

### 1.1 Accessibility (WCAG 2.1 Level AA — D-GAP-M35)

All validator output must work for screen readers + keyboard-only navigation. Applies to every Safety form, dashboard, and PDF generator.

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-GBL-001 | Color-only indicator (risk band, state pill, causal layer) without paired text label | client (linter) + manual QA | "Indicator must pair colour with text label (e.g., 'RED — Serious')." | D-GAP-M35 |
| V-GBL-002 | Form control missing ARIA label / associated `<label>` | client (ESLint a11y plugin + Axe CI gate) | "Form control requires ARIA label for screen reader parity." | D-GAP-M35 |
| V-GBL-003 | Colour-contrast ratio < 4.5:1 (normal text) or < 3:1 (large text / UI components) | CI (Axe/Pa11y gate on DESIGN_SYSTEM tokens) | "Contrast ratio below WCAG AA; adjust foreground or use higher-contrast token." | D-GAP-M35 |
| V-GBL-004 | Focus state not visible (outline removed without replacement) | CI (visual regression + Axe) | "Every interactive element must have a visible focus state (≥2px outline or equivalent)." | D-GAP-M35 |
| V-GBL-005 | Keyboard trap (Tab cycle cannot exit modal / drawer) | manual QA on each new overlay | "Keyboard navigation must complete full cycle — escape key or Tab-wrap required." | D-GAP-M35 |
| V-GBL-006 | Tabbable order not logical (DOM order differs from visual order without `tabindex` fix) | manual QA | "Tabbable order must match visual reading order." | D-GAP-M35 |
| V-GBL-007 | Image / icon-only button missing alt/`aria-label` | client (ESLint jsx-a11y) | "Non-text content requires text alternative." | D-GAP-M35 |
| V-GBL-008 | Dashboard chart / data viz missing text-table fallback | client (component contract) | "Charts must expose tabular equivalent via keyboard-triggered 'View as table' affordance." | D-GAP-M35 |

### 1.2 Rate Limits (per crew member unless stated)

Per `master_role` identity from the SimpleJWT `sub` claim. Enforced at DRF `throttle_classes`. Applies to HTTP `/api/safety/*` endpoints (see `<vims_integration>` URL routing).

| Rule ID | Endpoint | Method | Limit | Scope | Error message | Decision ref |
|---------|----------|--------|-------|-------|---------------|--------------|
| V-GBL-010 | `/api/safety/near-miss/` | POST | No daily cap | per crew user | n/a | D-GAP-M38 revised 2026-06-09 |
| V-GBL-011 | `/api/safety/incidents/` | POST | 10 per 24h | per crew user | "Incident creation limit reached (10 in 24h)." | D-GAP-M38 (analogous extension) |
| V-GBL-012 | `/api/safety/incidents/{id}/phase-transition/` | POST | 20 per 10 min | per user | "Too many phase transitions on this incident; wait 10 minutes." | Round 20 anti-thrash |
| V-GBL-013 | `/api/safety/incidents/{id}/attachments/` | POST | 30 per hour | per incident | "Attachment upload limit reached for this incident (30/hour)." | Round 20 anti-thrash |
| V-GBL-014 | `/api/safety/scm/` | POST | 3 per day per vessel | per vessel | "SCM creation limit: 3 per vessel per day." | Round 20 sanity |
| V-GBL-015 | `/api/safety/soi/download-checklist/` | POST | 60 per day per vessel | per vessel | "Checklist re-download limit: 60/day. Re-downloads idempotent per D-GAP-E1." | D-GAP-E1 |
| V-GBL-016 | Any `/api/safety/*` | any | 1000 req/min | per user | "Rate limit exceeded. Slow down." | Platform inheritance (D-GAP-F4) |
| V-GBL-017 | Dashboard export (`/api/safety/dashboard/export/`) | POST | 5 per hour | per user | "Export limit reached (5/hour). DPA-owned export per D-GAP-M31." | D-GAP-M31 |

### 1.3 Mobile-first Input Patterns (D-GAP-M34 — tablet 768px+)

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-GBL-020 | Input field whose touch target < 44×44 CSS px on viewport ≤1024px | client (CI visual regression) | "Touch target below 44px; enlarge for tablet/phone viewports." | D-GAP-M34 |
| V-GBL-021 | Form wider than 100% viewport (horizontal scroll) on 768px breakpoint | CI visual regression | "Safety forms must fit 768px viewport without horizontal scroll." | D-GAP-M34 |
| V-GBL-022 | `type="number"` / `type="date"` / `type="time"` fields not using native tablet picker | manual QA | "Use native mobile inputs for number/date/time on tablets." | D-GAP-M34 |
| V-GBL-023 | CRUD attempted on phone (≤480px) viewport | client (route guard) | "Phone viewport is read-only per D-GAP-M34. Open on a tablet or desktop to edit." | D-GAP-M34 |
| V-GBL-024 | SOI finding entry form requires >2 taps to reach first input | client (usability contract) | "SOI finding entry must be reachable within 2 taps from inspection overview." | D-GAP-M34 + D-SOI-10 revised |

### 1.4 Regulatory Citations (version-locked)

| Citation | Edition | Scope |
|----------|---------|-------|
| ISM Code | 2010 amendments (IMO Res MSC.273(85), in force 2010-07-01) §4, §9.2 | DPA role, non-conformity / incident reporting |
| SOLAS | Ch IX (as amended, consolidated SOLAS 2020 Edition), Reg VI | ISM applicability, Safety Officer duties |
| MARPOL | Annex I (consolidated 2022) | Pollution incident reporting |
| IMO Casualty Investigation Code | Resolution MSC.255(84) (adopted 2008-05-16, in force 2010-01-01) | SMC / MC / MI classification |
| MSC-MEPC.3/Circ.4 | as amended (current rev) | Casualty external report template |
| COSWP | 2026 Edition, Chapter 13 | Safety Officer onboard procedure |

---

## 2. Incident Validation

Every Incident record is a row in `vims_safety_incident` with `record_type='INCIDENT'`. Phase state lives in `vims_safety_incident.current_phase` and is append-only logged in `vims_safety_incident_phase_log`.

### 2.1 Intake (Phase 1 — Scene Control)

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-INC-001 | `narrative` < 200 characters at Phase 1 submit | client + server | "Incident narrative must be at least 200 characters." | D-DNV-02 + Round 20 minimum-detail |
| V-INC-002 | `occurred_at` > `reported_at` | client + server | "Incident occurred time cannot be after reported time." | Round 20 timestamp sanity |
| V-INC-003 | `reported_at` > NOW() (server clock, UTC) | server | "Reported time cannot be in the future." | Round 20 timestamp sanity |
| V-INC-004 | `occurred_at` > NOW() | client + server | "Occurred time cannot be in the future." | Round 20 timestamp sanity |
| V-INC-005 | `vessel_id` not in user's `master_RoleByVessel` scope (office) or `Crew_Onboarding_History` (ship) | server | "You are not assigned to this vessel." | D-GAP-A3 + platform auth |
| V-INC-007 | `imo_classifier` not in {`SMC`, `MC`, `MI`, `NOT_APPLICABLE`} | server | "IMO classifier must be SMC, MC, MI, or NOT_APPLICABLE." | D-GAP-R08 |
| V-INC-008 | `imo_classifier` missing for incident with `loss_type` in {People-Fatality, People-Major-Injury, Environmental-Major} | client + server | "IMO casualty classifier (SMC/MC/MI) is mandatory for this incident type. This is independent of internal risk band (D-GAP-R08 reconciliation option b)." | D-GAP-R08 |
| V-INC-009 | `risk_band` not in {`GREEN`, `YELLOW`, `RED`} | server | "Risk band must be GREEN, YELLOW, or RED." | D-DNV-02 |
| V-INC-010 | `investigation_depth` not in {`SHALLOW`, `MEDIUM`, `DEEP`}; depth not set at Phase 1 submit | client + server | "Select an investigation depth (SHALLOW / MEDIUM / DEEP) per D-GAP-R14 Task Triangle." | D-GAP-R14 |
| V-INC-011 | `record_type='INCIDENT'` with `investigation_depth='DEEP'` but `risk_band='GREEN'` without DPA override reason | server | "DEEP investigation on GREEN band requires DPA override reason." | D-GAP-R14 |
| V-INC-012 | Position (`latitude`, `longitude`) missing for `imo_classifier IN ('SMC','MC','MI')` | client + server | "Position is mandatory for IMO-classified casualties. Auto-fill from Daily Report within ±12h or enter manually." | D-GAP-M09 |
| V-INC-013 | Tolerable-Failure Filter used on YELLOW or RED band | server | "Tolerable-Failure fast-close is GREEN-band only." | D-GAP-R11 |
| V-INC-014 | Tolerable-Failure closure without DPA acknowledgment | server | "Tolerable-Failure closure requires DPA acknowledgment." | D-GAP-R11 |
| V-INC-015 | `external_party_injury.injured_person_type='NON_CREW'` and any original non-crew field is blank (`party_name`, `party_type`, `company_name`, `severity`) | client + server | "Required for non-crew injury." | D-EDGE-02 |
| V-INC-016 | `external_party_injury.injured_person_type='CREW'` with optional crew detail fields blank | none until final submission policy is defined | Crew injury details are nullable draft fields; rank options are loaded from current vessel crew. | CR-002 |
| V-INC-017 | Crew injury `crew_activity_type`, `nature_of_injury`, `source_of_injury`, or `affected_body_areas` is outside `vims_safety_injury_dropdown_option` because `Others(Specify)` was used | none | The typed value is stored in the same injury record text field. | CR-004 |
| V-INC-018 | Injury estimated cost choice is No or no cost fields are provided | none | Estimated cost details are optional; the UI hides the cost fields unless the user chooses Yes and continuation is allowed without cost values. | CR-025 |

### 2.2 Evidence (Phase 3) — Chain of Custody & Preservation

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-INC-020 | Chain-of-custody entry missing any of: description / collection timestamp / collector signature / storage location | client + server | "Chain-of-custody entry requires description, collection date-time, collector signature, and storage location." | D-GAP-R04 |
| V-INC-021 | Witness signature absent on a physical evidence item | client + server | "Physical evidence requires witness signature per chain-of-custody protocol." | D-GAP-R04 |
| V-INC-022 | Handover log gap (evidence not traced from collection to current custody) | server | "Chain-of-custody handover log must be continuous from collection to current custody." | D-GAP-R04 |
| V-INC-023 | VDR capture overdue — `risk_band='RED'` and >12h from `occurred_at` without VDR evidence row or explicit "not-fitted / unavailable" justification | server (cron) | "VDR capture overdue (12h) on RED incident. VDR typically overwrites; log capture or justify unavailability." | D-GAP-R06 |
| V-INC-024 | ECDIS track snapshot overdue at 24h from `occurred_at` | server (cron) | "ECDIS track snapshot overdue (24h)." | D-GAP-R06 |
| V-INC-025 | AIS shore-request overdue at 24h from `occurred_at` | server (cron) | "AIS shore-request overdue (24h)." | D-GAP-R06 |
| V-INC-026 | Photo walk-around overdue at 48h from `occurred_at` | server (cron) | "Photo walk-around overdue (48h)." | D-GAP-R06 |
| V-INC-027 | Formal statements overdue at 7 days from `occurred_at` | server (cron) | "Formal statements overdue (7 days)." | D-GAP-R06 |
| V-INC-028 | Legacy marine-document checklist data is absent | none in current simplified UI | Not a blocking validation in the Documents-only evidence screen. Capture the relevant document as an attachment with title and description. | D-MAINT-CR012 supersedes D-GAP-R05 user-facing enforcement |
| V-INC-029 | Cargo-type incident has no cargo-specific overlay data | none in current simplified UI | Not a blocking validation in the Documents-only evidence screen. Capture cargo evidence as document attachments with title and description. | D-MAINT-CR012 supersedes D-GAP-R10 user-facing enforcement |
| V-INC-030 | Personal-injury incident has no health / fatigue sub-section data | none in current simplified UI | Not a blocking validation in the Documents-only evidence screen. Capture health/fatigue evidence as document attachments with title and description where applicable. | D-MAINT-CR012 supersedes D-GAP-R23 user-facing enforcement |
| V-INC-031 | Interview record missing `interview_type IN ('FORMAL','INFORMAL')` | server compatibility | "Interview must be flagged FORMAL or INFORMAL." Current UI supplies `INFORMAL` automatically for simplified Witness Statement records. | D-GAP-R20; D-MAINT-CR016; D-MAINT-CR036 |
| V-INC-032 | `interview_type='FORMAL'` missing read-back tick, witness signature, or copy-to-witness record | server compatibility | "Formal interview requires: read-back to witness, witness signature, copy to witness (D-GAP-R19)." Formal read-back/copy controls and the old text statement field are not exposed in the current Witness Statement UI; the simplified UI can upload a witness statement file/image. | D-GAP-R19; D-MAINT-CR016; D-MAINT-CR036; D-MAINT-CR049 |
| V-INC-033 | `interview_type='INFORMAL'` missing `reason` (why formal was impossible) | server compatibility | "Informal interview requires a reason explaining why formal interview was not possible." Current UI supplies a system reason for simplified Witness Statement records. | D-GAP-R20; D-MAINT-CR016; D-MAINT-CR036 |

### 2.3 Legacy Analysis (former Phase 5) — Causal Layering, Bias Guards, ALARP

The current simplified incident workflow does not expose a visible Phase 5 analysis screen. Rules in this section remain historical/backend compatibility references only unless a current workflow section above explicitly carries the same rule forward.

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-INC-040 | Phase 4 → 5 transition attempted with no evidence recorded | client + server | "Phase 4 evidence is incomplete: add at least one evidence note, file, interview, or N/A reason." | D-MAINT-CR012; D-DNV-11 #1 |
| V-INC-041 | Fact entry saved without linked evidence ID (interview / document / photo) | client + server | "Assumption bias guard: every fact requires a linked evidence reference." | D-DNV-11 #2 |
| V-INC-042 | Finding/decision row references info dated after `occurred_at` without justification | server | "Hindsight bias guard: cannot reference information dated after the incident." | D-DNV-11 #3 |
| V-INC-043 | Legacy Evidence Matrix Con-row check | none in current Documents-only UI | Not enforced in the current user-facing workflow; Evidence Check / Evidence Matrix is compatibility-only after D-MAINT-CR015. | D-MAINT-CR015 supersedes D-DNV-11 #4 for current UI |
| V-INC-044 | Phase 6 → 7 transition: root causes all in Personal Factors (cat 1–4) AND no Lack-of-Control entry | server (hard block; DPA override only) | "Blame-fixation bias guard: add a Lack-of-Control cause or request DPA override." | D-DNV-11 #5 |
| V-INC-045 | Investigation-coded causes cluster into "Plant" (hardware only) | client + server (soft warn) | "Plant-Problem trap: review whether process / organisational factors are under-coded (D-GAP-R12)." | D-GAP-R12 |
| V-INC-046 | Investigation-coded causes cluster into "Personnel" (person only) | client + server (soft warn) | "Personnel-Problem trap: review whether system / process factors are under-coded (D-GAP-R12)." | D-GAP-R12 |
| V-INC-047 | Investigation-coded causes cluster into "External event" (weather / port only) | client + server (soft warn) | "External-Event trap: review whether internal control factors contributed (D-GAP-R12)." | D-GAP-R12 |
| V-INC-048 | Phase 5 → 6: People / Process / Plant interrogatory trio not all answered | client + server | "People / Process / Plant interrogatory: answer all three questions before leaving Phase 5 (D-GAP-R16)." | D-GAP-R16 |
| V-INC-049 | Current RCA advance attempted without both an Immediate Cause and a Root Cause | client + server | "Add at least one Immediate Cause and one Root Cause." | D-MAINT-CR033 supersedes D-GAP-R01 for current UI |
| V-INC-049A | New cause submitted with `causal_layer='INTERMEDIATE'` | server | "Use Immediate Cause or Root Cause." | D-MAINT-CR033 |
| V-INC-049B | Saved RCA cause edited with missing selected cause option, invalid option, missing Other text where Other is selected, or missing reason | client; server rejects invalid option, missing Other text, missing reason, Intermediate layer, and root-limit violations | "Complete the selected cause and reason before saving." | D-MAINT-CR040 |
| V-INC-050 | Phase 5 close with zero root causes identified | client + server | "At least one root cause must be identified (D-GAP-R03 — multiple root causes is the default)." | D-GAP-R03 |
| V-INC-051 | Single root cause saved at Phase 5 close without monocausal justification in closure note | client + server | "Monocausal conclusion requires a written justification in the closure note (D-GAP-R03)." | D-GAP-R03 |
| V-INC-052 | Artificial cap attempted on number of root-cause rows | server (rejected by design) | "No cap on root causes — multiple root causes are the default (D-GAP-R03)." | D-GAP-R03 |
| V-INC-053 | Safeguard-failure not coded across 6 dimensions (Design / Installation / Maintenance / Operation / Testing / Override) | client + server | "Failed safeguards require coding across all 6 dimensions: Design · Installation · Maintenance · Operation · Testing · Override (D-GAP-R18)." | D-GAP-R18 |
| V-INC-054 | Human-factors analysis missing Marine-specific Risk & Change Management domain prompts | client + server | "Complete the marine Risk & Change Management domain (D-GAP-R21) alongside SHELL + IMO A.884(21)." | D-GAP-R21 |
| V-INC-055 | 8 bias-guard attestation set not all confirmed before Phase 6 → 7 transition. The 8 guards = 5 DNV (Recency, Assumption, Hindsight, Confirmation, Blame-fixation) + 3 organisational defence-traps (Plant / Personnel / External-event) from D-GAP-R12 | client + server | "All 8 bias guards must be attested (5 DNV + 3 organisational defence-traps per Round 21 R12) before Phase 6 → 7 transition." | D-DNV-11 + D-GAP-R12 |
| V-INC-056 | Analysis tool coverage below depth rule: DEEP requires all 5 D-DNV-10 tools, MEDIUM requires ≥3, SHALLOW requires ≥2 | server | "Investigation depth '{depth}' requires {N} analysis tools (D-GAP-R14)." | D-GAP-R14 |

### 2.4 Action Phases and Compatibility Risk Fields

Current user-facing action validation is split by screen:

| Screen | Current user-visible validation | Compatibility note |
|--------|--------------------------------|--------------------|
| Corrective Action | Description and Due date are required before the user continues. | Owner/checker fields are not user-facing; frontend supplies compatibility values where the existing backend contract requires them. |
| Preventive Action | Description, Due date, and one shared How much will this reduce risk? answer for the screen are required. | Remaining risk, risk-confirmation checkbox, theme, effort, and "Prevent It Happening Again" wording are not user-facing under D-MAINT-CR049/CR-052; the shared risk-reduction answer is sent as the compatibility `estimated_likelihood_reduction` value for preventive saves. |
| Legacy Lessons Learned | Not a current user-facing validation gate. | Legacy `LESSONS_LEARNT` rows remain readable for old records/API compatibility only. |

Editing a saved Corrective Action or Preventive Action card reuses the same visible-field validation and PATCHes the existing recommendation/action row. Editing must not create a second row for the same phase category.

Legacy recommendation and ALARP rules below remain backend compatibility rules where older clients or stored rows still use those fields.

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-INC-060 | Preventive Action missing the shared risk-reduction answer or linked action due date | client + server | "Select how much the action will reduce risk and enter a due date." | D-GAP-R02; D-MAINT-CR049; D-MAINT-CR052 |
| V-INC-061 | Closure attempt on RED/YELLOW without ALARP attestation flag `true` on every System-Action | server (hard block) | "Cannot close — ALARP attestation missing on one or more System-Actions (D-GAP-R02)." | D-GAP-R02 |
| V-INC-062 | GREEN band Preventive Action saved without theme, effort, or residual-risk wording | none | Theme, effort, and residual-risk wording are not current user-facing fields; risk reduction and due date are still required. | D-GAP-R02; D-MAINT-CR049 |
| V-INC-063 | Recommendation row without tier tag `IN ('CORRECTIVE','PREVENTIVE','LESSONS_LEARNT')` | client + server | "Recommendations must be tagged Corrective, Preventive, or legacy Lessons Learnt (D-GAP-R13)." | D-GAP-R13; D-MAINT-CR042 |
| V-INC-064 | Office Review attempted with no active recommendation/action row | client + server | "At least one action recommendation is required before Office Review." | D-DNV-06 / D-GAP-R13; D-MAINT-CR042 |
| V-INC-065 | Legacy System-Action recommendation missing per D-DNV-06 3-tier rubric | legacy compatibility | Current UI does not require a visible Lessons Learned or System-Action tier; ALARP checks on current Preventive rows are covered by V-INC-060 and V-INC-061. | D-DNV-06; D-MAINT-CR042 |

### 2.5 Chain of Signatures (Phase-Gate Progression)

Sequencing is **Reporter → Master → HOD → DPA → FM**. Each next signature requires the prior one to be present in `vims_safety_incident_phase_log` with `signature_valid=true`. No "Acting-*" / deputy shortcuts (D-GAP-A3 / A4).

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-INC-070 | Master signature attempted before Reporter signature | server | "Master cannot sign before Reporter submits." | Round 20 signature sequencing |
| V-INC-071 | HOD signature attempted before Master | server | "HOD cannot sign before Master." | Round 20 signature sequencing |
| V-INC-072 | DPA signature attempted before HOD | server | "DPA cannot sign before HOD." | Round 20 signature sequencing |
| V-INC-073 | FM signature attempted before DPA | server | "FM cannot sign before DPA." | Round 20 signature sequencing |
| V-INC-074 | FM signature required (RED band closure) and missing | server | "RED-band closure requires FM signature (D-GAP-M06)." | D-GAP-M06 |
| V-INC-075 | Signature payload missing typed name, timestamp, or device fingerprint | server | "Digital signature requires typed name, timestamp, and device fingerprint (D-GAP-D1)." | D-GAP-D1 |
| V-INC-076 | Role persistence: phase action attempted with `rank` not equal to the required rank on `master_RoleByVessel` / `Crew_Onboarding_History` at the time of action | server | "This action is rank-based (D-GAP-A3). The currently-ranked person-in-role must perform it." | D-GAP-A3 / A4 |
| V-INC-077 | Any form field named `acting_master`, `acting_dpa`, `deputy_*`, or `alternate_*` present in request body | server (reject 400) | "Acting-role / deputy-chain concepts not supported (D-GAP-A3 / A4). Route through rank-holder or use VIMS timeline-extension procedure (D-GAP-B2)." | D-GAP-A3 / A4 / B2 |

### 2.6 Phase Gate Summary (completeness checks required to advance)

| From → To | Must be complete | Decision ref |
|-----------|------------------|--------------|
| 0 → 1 | Draft created with vessel scope and reporter context | D-GAP-C1, D-EDGE-08 |
| 1 → 2 | Intake narrative ≥200 chars; `risk_band`; office communication yes/no; communication mode when office was told; Reporter signature | V-INC-001..005, V-INC-009, V-INC-070, D-MAINT-CR018 |
| 2 → 3 | Investigator team + resources allocated | D-DNV baseline |
| Visible Phase 2-6 saves | RCA create/update, facts/evidence helpers, Corrective Action, Preventive Action, Evidence Documents, and Witness Statements can be saved or edited by authorized users before office approval even when legacy backend `current_phase` has not reached the old phase number. Edits update existing rows rather than adding duplicates. | D-MAINT-CR039, D-MAINT-CR040, D-MAINT-CR041, D-MAINT-CR042 |
| Visible Phase 3 → 4 | Corrective Action saved with Description and Due date | D-MAINT-CR038 |
| Visible Phase 4 → 6 | Preventive Action saved with Description, Due date, and the shared screen-level risk reduction; frontend continues directly to Office Review | D-MAINT-CR038, D-MAINT-CR042, D-MAINT-CR043, D-MAINT-CR049, D-MAINT-CR052 |
| Visible Phase 5 Evidence | Evidence Documents can be opened early by authorized users; document Edit requires a title and updates title/description metadata without replacing the file. Witness Statement Edit reuses the simplified witness required fields and updates the existing witness row. Official submit/order still follows backend workflow gates | D-MAINT-CR012, D-MAINT-CR013, D-MAINT-CR039, D-MAINT-CR041, D-MAINT-CR043 |
| Visible Phase 6 → 7 | Office Review accepted by PIC or DPA for any risk band; optional Office Comments/lesson learnt saved without a word limit; ship-side pending message displays when no comment exists; PDF preview/download is not blocked solely by pending Phase 7 acceptance. Send for rework uses a comment plus the fixed action-rework target. | D-PDF-01, D-MAINT-CR042, D-MAINT-CR043, D-MAINT-CR044, D-MAINT-CR049, D-MAINT-CR050 |
| Visible Phase 6 Fleet Alert | At least one active `VesselData` ship is selected; in-app and email dispatch is scoped only to selected ships | D-MAINT-CR051 |
| Visible Phase 7 save | Authorized ship-side and office-side users with incident form access and vessel scope can save the Loss Evaluation row in `vims_safety_incident_loss_evaluation` before Office Review approval/backend `current_phase` 8 after choosing Incident Report or Injury Report | D-MAINT-CR052, D-MAINT-CR053 |
| Visible Phase 7 → CLOSED | Loss Evaluation row saved in `vims_safety_incident_loss_evaluation` and closure note supplied by an office close actor | D-MAINT-CR047, D-MAINT-CR052 |

### 2.6.1 Phase 7 Loss Evaluation Validation

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-INC-090 | User opens or saves Loss Evaluation without incident form access or vessel scope | server/UI | form-permission or vessel-scope error | D-MAINT-CR052 |
| V-INC-091 | User closes an incident from Phase 7 before saving Loss Evaluation | server | "Save Loss Evaluation before closing the incident." | D-MAINT-CR047 |
| V-INC-092 | User closes an incident without a closure note | server | `closure_reason` required | D-MAINT-CR047 |
| V-INC-093 | Consequence, Likelihood, Risk level, or Type of Repairs submitted outside the configured fixed dropdown values | server serializer | field-level choice validation | D-MAINT-CR047 |
| V-INC-094 | Code of Safe Working Practices dropdown loads | UI/API | active options are loaded from `vims_safety_injury_dropdown_option` where `field_key = SAFE_WORKING_PRACTICE`; CR-048 seeds the requested list and deactivates stale choices outside it | D-MAINT-CR048 |
| V-INC-095 | Incident Fleet Alert submitted with no selected ship, an unknown ship, or an inactive/deleted `VesselData` row | server | "Select at least one ship." or field-level selected-ship error | D-MAINT-CR051 |
| V-INC-096 | User saves Loss Evaluation without selecting Incident Report or Injury Report, or submits an unknown report type | UI/server serializer | select Incident Report or Injury Report / field-level choice validation | D-MAINT-CR053 |

### 2.7 Timeline-Extension (D-GAP-B2)

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-INC-080 | Incident deadline breach attempted without VIMS timeline-extension request | server | "Timeline overrun requires the standard VIMS extension procedure (D-GAP-B2). No deputy / MD escalation path exists." | D-GAP-B2 |
| V-INC-081 | Request body contains `deputy_fm`, `acting_dpa`, `md_escalation`, or equivalent | server (reject 400) | "Deputy / Acting / MD-escalation concepts not supported. Use VIMS extension workflow (D-GAP-B2)." | D-GAP-B2 / A3 / A4 |
| V-INC-082 | Extension request missing justification text | server | "Extension request requires written justification." | D-GAP-B2 inherits VIMS extension form |
| V-INC-083 | Extension approver rank ≠ DPA (GREEN/YELLOW) or FM (RED) | server | "Extension approval authority matches closure authority by band (D-EDGE-03)." | D-EDGE-03 |

---

## 3. Near Miss Validation

Near-miss records share `vims_safety_incident` with `record_type='NEAR_MISS'`. Anonymous reporting is removed from V1; reporter details are stored and visible to Master and authorized users within vessel scope. Near Miss cause analysis uses `vims_safety_near_miss_cause_option` and stores selections in `vims_safety_incident.near_miss_factor_causes`; old M-SCAT near-miss fields are compatibility-only for historical rows.

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-NM-001 | `description` < 100 characters at submit | client + server | "Near-miss description must be at least 100 characters (D-GAP-M38)." | D-GAP-M38 |
| V-NM-002 | `severity` not selected | client + server | "Select a severity level before submitting." | D-GAP-M38 |
| V-NM-002A | `place` outside {`AT_ANCHOR`, `AT_SEA`, `AT_PORT`} | client + server | "Select a valid place." | FEAT-SAF-NM-001 |
| V-NM-002B | Missing factor-cause selection for any required factor/stage pair (`HUMAN`, `VESSEL`, `MANAGEMENT`, `OTHER` × `IMMEDIATE`, `ROOT`) | client + server | "Select immediate and root causes for every factor, or choose Not Applicable." | FEAT-SAF-NM-001 |
| V-NM-002C | Category value outside the approved combined Category/Possible Loss list and not saved through `Other - Specify` | client + server | "Select a valid category." | FEAT-SAF-NM-001 |
| V-NM-003 | Near Miss Type submitted from the UI | client + server | "Near Miss Type is not used. Select Category instead." | D-GAP-M38 revised 2026-06-09 |
| V-NM-004 | Office Comments priority not in {`LOW`, `MEDIUM`, `HIGH`} on Accept | server | "Near-miss priority must be LOW, MEDIUM, or HIGH." | D-GAP-R22 |
| V-NM-005 | Office reviewer changes priority without `priority_change_reason`, changes category tag without `category_tag_change_reason`, or sends to rework without reason text | client + server | "Please enter the reason before saving this office decision." | D-GAP-R22 |
| V-NM-006 | `priority='HIGH'`: fleet-alert target date > 7 days from submission | server | "HIGH-priority near-miss requires fleet alert within 1 week (D-GAP-R22)." | D-GAP-R22 |
| V-NM-007 | Reporter identity missing from a submitted near-miss record | client + server | "Reporter details are required from login/session." | D-GAP-J1 revised 2026-06-09 |
| V-NM-008 | PDF output prints "Reporter identity is masked" or `Anonymous Reporter` text | server (PDF renderer) | "Near-miss PDF must show reporter details for authorized users and must not print masking text." | D-GAP-J1 revised 2026-06-09 |
| V-NM-009 | Reporter identity absent from audit log (`vims_safety_field_history`) | server | N/A — audit retention is mandatory | D-GAP-J1 revised 2026-06-09 |
| V-NM-010 | Master attempts rework on a near miss originally reported by another authorized user | server | Allowed; no error | D-GAP-J1 revised 2026-06-09 |
| V-NM-011 | `priority='LOW'` or `priority='MEDIUM'` close without closure note | server | "LOW/MEDIUM-priority near-miss closure requires a closure note." | D-GAP-R22 |
| V-NM-012 | `priority='HIGH'` close without preventive measures + fleet learning + fleet alert | server | "HIGH-priority near miss can be closed only after preventive measures, fleet learning, and the fleet alert are completed." | D-GAP-R22 |
| V-NM-013 | Factor cause option is `Other` and the matching custom text is blank | client + server | "Specify the cause when Other is selected." | FEAT-SAF-NM-001 |
| V-NM-014 | Factor cause option UUID is inactive, belongs to another factor/stage, or does not exist | server | "Select valid near-miss cause options." | FEAT-SAF-NM-001 |

---

## 4. SCM Validation

SCM records live in `vims_safety_scm_meeting` with `meeting_type IN ('REGULAR','AD_HOC')`. Meeting creation is WRH-gated: ship-time configuration must exist and all roster crew WRH data must be available and compliant before hosting (D-MAINT-CR014). Created-meeting attendance still joins to WRH via `wrh_ship_time_config` (D-GAP-M26).

Active SCM state display:
- `DRAFT` displays as `Draft`.
- `SUBMITTED` displays as `Submitted to Office`.
- `CLOSED` displays as `Closed`.

### 4.1 Cadence and Type

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SCM-001 | Days since vessel's last `meeting_type='REGULAR'` CLOSURE timestamp > 35 days, and new Regular not yet scheduled | server (dashboard warn) | "Regular SCM overdue: >35 days since last monthly meeting. Schedule immediately (SSQE Manual Rev 01 Feb 2026 §9)." | D-GAP-M-ADHOC cadence counter anchors on last SCM closure regardless of type |
| V-SCM-002 | SCM create/edit attempted by role outside `{Master, CO}` | server | "Only Chief Officer or Master can create or edit this SCM meeting." | D-RBAC-06, D-GAP-M-ADHOC |
| V-SCM-003 | `meeting_type='AD_HOC'` missing `trigger_reason` text | client + server | "Ad-Hoc SCM requires a trigger reason." | D-GAP-M-ADHOC |
| V-SCM-004 | Ad-Hoc SCM attempt to replace / skip monthly Regular cadence | server | "Ad-Hoc meetings do NOT replace the monthly Regular meeting (D-GAP-M-ADHOC)." | D-GAP-M-ADHOC |
| V-SCM-005 | Vessel has overdue SOI area during SCM creation, edit, PDF export, or Office Comment closure | server (warn only) | "Warning: vessel has overdue SOI area(s). Meeting may continue and may be closed with Office Comment." | D-GAP-M20 |
| V-SCM-006 | Office Comment save attempted by a user outside DPA, FM, Shore HOD, or Marine Superintendent profile `407EF017-0F1C-EF11-A9F1-F348983BAE6B` | server | "Only authorized office reviewers can save Office Comment." | D-RBAC-06 |
| V-SCM-007 | Office Comment save attempted with blank comment | client + server | "Office Comment is required before closing the SCM meeting." | D-RBAC-06 |
| V-SCM-008 | Vessel-side edit attempted after `office_comment_at` is set or state is `CLOSED` | server | "SCM meeting is closed after Office Comment. Editing is stopped." | D-GAP-M22 |
| V-SCM-009 | Submit to Office clicked but meeting remains `DRAFT` after save | client + server | "SCM meeting must be submitted to office." | D-RBAC-06 revised 2026-06-09 |
| V-SCM-014 | SCM Regular or Ad-Hoc creation attempted while ship-time config is missing, roster WRH data is unavailable, WRH lookup fails, or any roster crew is non-compliant | client + server | "SCM meeting cannot be hosted until all WRH warnings are cleared." | D-MAINT-CR014, D-GAP-M26 |

### 4.2 Attendance (WRH Join)

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SCM-010 | Attendee row WRH rest-hour non-compliant in trailing 24h window | server (blocks create; warning-only after meeting exists) | "SCM meeting cannot be hosted until all WRH warnings are cleared." at create; after creation: "Warning: attendee '{name}' had WRH non-compliance in the trailing 24h." | D-MAINT-CR014, D-GAP-M11 |
| V-SCM-011 | WRH data unavailable for attendee at meeting timestamp | server (blocks create; warning-only after meeting exists) | "SCM meeting cannot be hosted until all WRH warnings are cleared." at create; after creation: "Warning: WRH data unavailable for '{name}'." | D-MAINT-CR014, D-GAP-M11 |
| V-SCM-012 | Timestamp resolution for attendee attempts direct local-time input | server (reject) | "Attendance timestamps are stored UTC and resolved via `wrh_ship_time_config` (D-GAP-M26)." | D-GAP-M26 |
| V-SCM-013 | Dateline event (vessel crosses IDL during meeting) without Master override in `wrh_ship_time_config` | server | "Dateline event requires Master-set time configuration in `wrh_ship_time_config` (D-GAP-M26)." | D-GAP-M26 |

### 4.3 Agenda & Closure

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SCM-020 | Agenda item close attempted with `suggestions_recommendations` empty where action is needed | client + server | "Agenda items that need action require Suggestions / Recommendations." | SSQE §9 |
| V-SCM-021 | Closed-Since-Last snapshot cutoff requested from a non-SCM-closure timestamp | server | "Cutoff must anchor on prior closed SCM timestamp. New SCM uses Office Comment closure; legacy records may use Master sign-off timestamp (D-GAP-M22)." | D-GAP-M22 |
| V-SCM-022 | SCM PDF attempts to print attendee digital signature status, device fingerprint, or capture status | server/PDF renderer | "SCM PDF must use plain Master Signature and Chief Officer Signature lines only." | D-PDF-03b |

---

## 5. SOI Validation

SOI events live in `vims_safety_soi_inspection`. Checklist items load from `master_soi_area_item` (329 rows, seeded from `safety-reference-data/soi_checklist_v1.csv`). Paper-first flow per D-GAP-E4.

### 5.1 Checklist Version & Applicability

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SOI-001 | Checklist version selected for download not active at `generation_time` | server | "Checklist version is not active at event timestamp (D-SOI-05)." | D-SOI-05 |
| V-SOI-002 | Vessel assigned to checklist version ≠ requested version without DPA override | server | "Vessel is on a different checklist version. DPA approval required to reassign (D-SOI-05)." | D-SOI-05 |
| V-SOI-003 | Checklist template reassigned mid-inspection — engine attempts to apply new version to in-flight | server | "In-flight inspection frozen on prior version; new version applies to next cycle only (D-GAP-M05)." | D-GAP-M05 |
| V-SOI-004 | `applicable=false` decision on an SOI area without both Master request + DPA approval + reason in `vims_safety_soi_applicability_log` | server | "Area applicability toggle requires Master request + DPA approval + reason (D-GAP-M19)." | D-GAP-M19 |

### 5.2 Unique ID & Paper-First Flow

Unique checklist ID format: `SOI-{VESSEL_IMO:7}-{YYYYMMDD}-{SEQ:04}` (e.g., `SOI-9123456-20260417-0001`). Regex: `^SOI-\d{7}-\d{8}-\d{4}$`. Encoded as barcode/QR on the generated PDF/Excel (barcode format is a build-time deferral — see BACKEND_STRUCTURE §Deferrals).

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SOI-010 | Unique checklist ID not matching regex `^SOI-\d{7}-\d{8}-\d{4}$` | server | "Unique checklist ID must match format SOI-IMO-YYYYMMDD-SEQ." | D-SOI-10 revised + D-GAP-E4 |
| V-SOI-011 | Duplicate unique checklist ID at creation | server (DB unique constraint) | "Checklist ID already issued. SO may re-download same ID (D-GAP-E1)." | D-GAP-E1 |
| V-SOI-012 | **Any HTTP request to a scan-upload endpoint or any `scanned_checklist_file` / `paper_scan_url` field in request body** | server (reject 400) | "Paper-first SOI: no scan-upload endpoint exists (D-GAP-E4). Paper is filed in the ship SMS filing system; digital record links via unique checklist ID only." | D-GAP-E4 |
| V-SOI-013 | Finding row submitted without matching unique checklist ID reference | server | "Findings must cite the unique checklist ID (D-GAP-E4 linkage)." | D-GAP-E4 |
| V-SOI-014 | Second download attempt for same area selection — treated as idempotent re-print | server | (no error; re-issues same unique ID) | D-GAP-E1 |
| V-SOI-015 | Partial submission (subset of downloaded areas) attempted | server | (allowed; per-area 90-day counter resets only for submitted areas) | D-GAP-E2 |
| V-SOI-016 | Re-download after loss/damage without inspection-notes loss event | server | "Record loss-of-paper event in inspection notes before re-downloading (D-GAP-E3)." | D-GAP-E3 |

### 5.3 Section 12 Cross-Cutting Safety & Culture

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SOI-020 | Section 12 attempted on an event in a 3-month cycle where Section 12 has already been carried by an earlier event | server | "Section 12 'Cross-cutting Safety & Culture' evaluated once per 3-month cycle (D-GAP-M23). This cycle already covered." | D-GAP-M23 |
| V-SOI-021 | 3-month cycle ending without any event carrying Section 12 | server (dashboard warn + block next-cycle close) | "Section 12 not completed this 3-month cycle. SO must select one SOI event to carry it (D-GAP-M23)." | D-GAP-M23 |
| V-SOI-022 | Section 12 items 12.10 / 12.11 submitted as Yes/No/NA instead of text | client + server | "Items 12.10 and 12.11 are narrative prompts, not Yes/No/NA (D-SOI-16)." | D-SOI-16 / §2C.5 |

### 5.4 Findings

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SOI-030 | `severity='HIGH'` finding saved with zero photos attached | client + server | "HIGH-severity SOI findings require ≥1 photo (D-GAP-M24)." | D-GAP-M24 |
| V-SOI-031 | Paper checklist signatures: Safety Officer or Assistant signature missing on submission | client + server | "Safety Officer + Assistant paper signatures are mandatory (D-GAP-M15). Trainees do not sign." | D-GAP-M15 |
| V-SOI-032 | Trainee name present in signature fields | server (reject) | "Trainees do not sign the checklist (D-GAP-M15)." | D-GAP-M15 |
| V-SOI-033 | Master digital counter-signature attempted on paper instead of at approval stage | server | "Master counter-signs digitally at approval stage, not on paper (D-GAP-M15)." | D-GAP-M15 |
| V-SOI-034 | Master rejection of `pending_closure` without written reason | client + server | "Master rejection requires a written reason; finding returns to Open (D-GAP-M21)." | D-GAP-M21 |
| V-SOI-035 | Repeat finding (same area + item + vessel within trailing N cycles) — auto-badge `Repeat — Nth` | server (computed) | (badge applied; no block) | D-GAP-M17 |
| V-SOI-036 | HIGH-severity finding saved without in-form prompt to create incident | client | "Prompt SO: 'This looks incident-worthy. Create one now?' (D-GAP-M16). Nudge only; SO judgement retained." | D-GAP-M16 |

### 5.5 "SOI Compliance %" Calculation (D-GAP-DESIGN-01)

Renamed from "Inspection Compliance %" to disambiguate from the PSC Inspection module metric of the same name. **Always use the label "SOI Compliance %" — never "Inspection Compliance %".**

**Formula (canonical):**

```
SOI Compliance % = ( areas_inspected_in_current_3_month_cycle
                     / areas_applicable_to_vessel )
                   × 100
```

Where:
- `areas_inspected_in_current_3_month_cycle` = count of distinct `master_soi_area` rows with `applicable=true` for the vessel, where `vims_safety_soi_vessel_area_map.last_inspected_at` falls inside the current 3-month window OR the area has a finding in `state='pending_closure'` (D-GAP-M30 — pending_closure counts as inspected).
- `areas_applicable_to_vessel` = count of `master_soi_area` rows with `applicable=true` for the vessel per `vims_safety_soi_vessel_area_map` (excludes areas toggled applicable=false per D-GAP-M19).

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-SOI-040 | Dashboard / PDF label reads "Inspection Compliance %" anywhere in Safety UI | CI lint + manual QA | "Use 'SOI Compliance %' (D-GAP-DESIGN-01). Never 'Inspection Compliance %'." | D-GAP-DESIGN-01 |
| V-SOI-041 | New-vessel edge case: `areas_applicable_to_vessel > 0` but zero cycles completed | server | Display "N/A — awaiting first cycle" (not 0% red) | D-GAP-M30 |
| V-SOI-042 | 90-day per-area counter attempts to reset on upload event | server | Reset timing is a build-time deferral — pending D-GAP resolution on upload vs approval vs cron | See BACKEND_STRUCTURE Deferral #12 |

---

## 6. Cross-Module Validation

Safety lives in `ksm_marine_live` alongside Reporting, WRH, CMS, Purchase. Cross-module calls are **live joins**, not ETL (D-GAP-I2).

### 6.1 Reporting (Daily Report) — MSC-MEPC.3 Position Auto-Fill

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-XMOD-001 | Auto-fill position request: no Daily Report within ±12h of `occurred_at` | server | "No Daily Report within ±12h window; enter position manually. Record flagged `awaiting_daily_report_match` for DPA review (D-GAP-M09/M10)." | D-GAP-M09 / M10 |
| V-XMOD-002 | Auto-fill position applied with timestamp delta > 12h | server (reject) | "Position auto-fill tolerance is ±12h (D-GAP-M09). Enter manually or wait for Daily Report." | D-GAP-M09 |
| V-XMOD-003 | User edits auto-filled position with more-recent coordinates — allowed; audit-logged | server | (no error; `vims_safety_field_history` logs override) | D-GAP-M09 |
| V-XMOD-004 | Missing Daily Report blocks incident submission | server (reject) | "Submission must NOT be blocked on Reporting-module gap (D-GAP-M10)." | D-GAP-M10 |

### 6.2 WRH Attendance (SCM)

See §4.2 above. SCM creation is blocked by WRH host readiness per D-MAINT-CR014; after a meeting exists, attendance warnings remain warning-only per D-GAP-M11. Timezone via `wrh_ship_time_config` per D-GAP-M26.

### 6.3 Purchase Requisition (Corrective Action)

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-XMOD-010 | `vims_safety_corrective_action.purchase_req_id` references non-existent requisition | server (DB FK violation) | "Corrective Action → Purchase Requisition link must reference an existing requisition (hard FK per D-GAP-M12)." | D-GAP-M12 |
| V-XMOD-011 | Requisition archive/delete attempted while linked to an open CA | server (DB trigger / pre-delete guard) | "Requisition cannot be archived while linked to an open Corrective Action (D-GAP-M12)." | D-GAP-M12 |
| V-XMOD-012 | Requisition status change polled via integration endpoint | server (live DB join, no sync) | (no error; live status) | D-GAP-I2 |
| V-XMOD-013 | CA close attempt with Physical Verification still Open | server | (allowed — CA may close while PV tracks independently per D-GAP-M03) | D-GAP-M03 |

### 6.4 PMS — Decoupled (D-GAP-I1)

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-XMOD-020 | **Any** field, FK, or request path referencing PMS from a Safety endpoint — e.g. `pms_workorder_id`, `pms_job_code`, `/api/safety/pms-link/` | server (reject 400 at serializer + URL conf) | "PMS integration is decoupled in V1 (D-GAP-I1). No FK or in-VIMS integration permitted; manual cross-reference only." | D-GAP-I1 |
| V-XMOD-021 | Database migration introducing FK to any `pms_*` table from `vims_safety_*` | CI lint on migrations | "PMS FK forbidden (D-GAP-I1)." | D-GAP-I1 |
| V-XMOD-022 | Corrective Action narrative containing a PMS job-code pattern — allowed as free text | (no enforcement) | (no error — text reference acceptable; structured FK forbidden) | D-GAP-I1 |

### 6.5 CMS (Crew Master)

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-XMOD-030 | SOI assistant lookup or incident-crew assignment: stale / cached CMS record served | server | "Use live join to CMS — no sync / staleness (D-GAP-I2)." | D-GAP-I2 |

### 6.6 Flag-State / Class Society / MLC

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-XMOD-040 | UI exposes a class-society notification toggle | CI lint + manual QA | "No in-module class-society toggle (D-GAP-M13). DPA handles externally." | D-GAP-M13 |
| V-XMOD-041 | MLC-reportable injury — field `mlc_reportable=true` without DPA visibility | server | "MLC-reportable flag must be visible to DPA (D-GAP-M14)." | D-GAP-M14 |

---

## 7. Timeline-Extension Procedure (D-GAP-B2)

The **one and only** escape valve when a deadline cannot be met is the existing VIMS platform timeline-extension flow — shared with Reporting, Inspection, and other modules. Safety does not introduce a parallel flow.

### 7.1 Allowed

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-EXT-001 | Extension request submitted via VIMS shared extension endpoint with parent `incident_id` / `soi_id` / `scm_id` / `ca_id` | server | (accepted if approver rank matches closure band) | D-GAP-B2 |
| V-EXT-002 | Extension approver rank = DPA (GREEN/YELLOW), FM (RED) | server | (per D-EDGE-03 closure-authority mapping) | D-EDGE-03 / B2 |
| V-EXT-003 | 80%-of-deadline mark reached — dashboard flag fires; no auto-escalation | server (cron) | (dashboard metric only; no FM/MD ping) | D-GAP-F3 |

### 7.2 Explicitly Rejected

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-EXT-010 | Request body includes `acting_fm`, `acting_dpa`, `acting_master`, `acting_co`, `acting_ce`, `acting_so`, `acting_hod` | server (reject 400 at serializer) | "Acting-role concepts not supported (D-GAP-A3 / A4). Role persists; person may change via normal rotation." | D-GAP-A3 / A4 |
| V-EXT-011 | Request body includes `deputy_*` fields (`deputy_fm`, `deputy_dpa`, etc.) | server (reject 400) | "No deputy chains. RED closure runs within designed timeline; use VIMS extension (D-GAP-B2)." | D-GAP-B2 |
| V-EXT-012 | Request body includes `md_escalation`, `md_approval`, `escalated_to_md` | server (reject 400) | "No MD-escalation logic in Safety (D-GAP-F3)." | D-GAP-F3 |
| V-EXT-013 | Request body includes `alternate_*`, `stand_in_*`, `covering_*` (e.g., `alternate_master`, `stand_in_dpa`) | server (reject 400) | "No stand-in / alternate role concepts. Use timeline-extension (D-GAP-B2)." | D-GAP-A3 / B2 |
| V-EXT-014 | Frontend form renders an `Acting-*` or `Deputy-*` field | CI lint (forbidden string test) | "Forbidden field name. See VALIDATION_RULES §7.2." | D-GAP-A3 / A4 / B2 |

---

## 8. Role Persistence (D-GAP-A3 / A4 / A6)

Rank-based routing, never person-based. The person in the role may change mid-flow (crew rotation), but the role / rank is continuous and duties pass automatically to the next holder.

| Rule ID | Trigger condition | Enforcement point | Error message | Decision ref |
|---------|-------------------|-------------------|---------------|--------------|
| V-ROLE-001 | Pending action assigned to a specific `user_id` rather than a `rank` | server | "Assignments must reference rank, not person. Person-rotation should not require re-assignment (D-GAP-A3)." | D-GAP-A3 |
| V-ROLE-002 | New Master on rotation — inherited duties (SCM chair, GREEN closure, SOI approval) not visible in inbox | server (routing recompute at sign-in) | (recompute required; no handover-to-CO fallback) | D-GAP-A3 |
| V-ROLE-003 | New CO on rotation — open SOI findings not inherited | server (routing recompute) | (recompute required; no 2/E alternate succession except Master toggle per D-SOI-02) | D-GAP-A4 |
| V-ROLE-004 | Role-holder is the subject of an incident — system attempts to re-assign their own duties | server (reject) | "Role stays as-is when incumbent is subject of incident. DPA oversight + audit trail provide integrity (D-GAP-A6)." | D-GAP-A6 |

---

## 9. Regulatory Compliance Summary

Every regulatory-driven validation cites its code edition on first use. Re-verify editions on each minor release.

| Rule ID | Regulation | Citation | Enforcement point | Validation reference |
|---------|-----------|----------|-------------------|----------------------|
| V-REG-001 | ISM Code §4 (DPA) | ISM Code 2010 amendments (IMO Res MSC.273(85)) | server (RBAC) | V-INC-072, V-NM-010 |
| V-REG-002 | ISM Code §9.2 (Non-conformity reporting) | ISM Code 2010 amendments | server export | V-INC-008 / MSC-MEPC.3 integration |
| V-REG-003 | SOLAS Ch IX | SOLAS consolidated 2020 Edition | server (ISM applicability) | platform inherited |
| V-REG-004 | SOLAS Reg VI (Safety Officer) | SOLAS consolidated 2020 Edition | server (SOI RBAC) | V-SOI-031..033 |
| V-REG-005 | MARPOL Annex I | MARPOL consolidated 2022 | server (pollution incident classifier) | V-INC-007 |
| V-REG-006 | IMO Casualty Investigation Code (SMC/MC/MI) | Resolution MSC.255(84), in force 2010-01-01 | server | V-INC-007, V-INC-008 |
| V-REG-007 | MSC-MEPC.3/Circ.4 casualty report template | current revision (as amended) | server export | §2B.13 SSOT mapping |
| V-REG-008 | COSWP Ch 13 (Safety Officials) | COSWP 2026 Edition | server (SOI RBAC) | V-SOI-031 |
| V-REG-009 | Merchant Shipping Safety Officials and Safety Committees | SI 1997/2962 (UK flag-state reference) | server (flag-state export hook) | V-SOI baseline |
| V-REG-010 | IMO A.884(21) Human-Factors domains | IMO A.884(21), 1999 | server (D-DNV-09 analysis) | V-INC-054 |

---

## 10. Self-Check Rubric Report

| Rubric item | Status |
|-------------|--------|
| Every validation cites a D-* or Round 20/21 decision | PASS — every rule row has Decision ref column |
| Every validation has trigger / enforcement point / error message | PASS — all three columns present |
| Regulatory validations cite code edition | PASS — §1.4 + §9 |
| ALARP gate present on System-Actions | PASS — V-INC-060..062 |
| No artificial cap on root causes | PASS — V-INC-052 explicitly rejects caps |
| Reporter identity visibility rules present | PASS — V-NM-007..010 |
| No "Acting-*" / deputy concepts anywhere | PASS — V-INC-077, V-EXT-010..014, V-ROLE-001..004 |
| Paper-first SOI: scan-upload rejection rule present | PASS — V-SOI-012 |
| "SOI Compliance %" label used (never "Inspection Compliance %") | PASS — §5.5 + V-SOI-040 |
| PMS integration rejection rule present | PASS — V-XMOD-020..022 |
| Zero bare `safety_*` prefixes (without `vims_` / `master_`) | PASS — every table reference is `vims_safety_*` or `master_*` |
| Signature sequencing Reporter → Master → HOD → DPA → FM | PASS — V-INC-070..073; FM gated on RED per V-INC-074 |

**No BLOCKED stubs required.** All rule specifications resolved from 159 locked decisions + Round 20/21 directives.
