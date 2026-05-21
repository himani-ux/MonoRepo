# FRONTEND_GUIDELINES.md — Engineering Rules & Component Architecture
## VIMS Safety Module — Incident · Near Miss · SCM · SOI

**Version:** 1.0 | **Date:** 2026-04-17 | **Status:** Locked (Session 5 close)

**Glossary (first-use expansions):**
DPA (Designated Person Ashore, ISM Code §4) · FM (Fleet Manager) · TD (Technical Director) · HOD (Head of Department — Chief Officer / Chief Engineer / senior rank onboard) · CO (Chief Officer) · CE (Chief Engineer) · SO (Safety Officer, SOLAS Reg VI) · SCM (Safety Committee Meeting) · SOI (Safety Officer Inspection) · RCA (Root Cause Analysis) · CA (Corrective Action) · PA (Preventive Action) · SMC/MC/MI (IMO Serious Marine Casualty / Marine Casualty / Marine Incident — IMO Casualty Investigation Code Res. MSC.255(84)) · WCAG (Web Content Accessibility Guidelines 2.1).

---

## 0. Platform Inheritance Declaration

The VIMS Safety Module **extends** the sibling **VIMS Reporting Module** frontend guidelines (`VIMS-Reporting-Module/FRONTEND_GUIDELINES.md` v1.0, 2026-04-06), which itself extends the **VIMS Inspection Module** guidelines (`VIMS DOCS/FRONTEND_GUIDELINES.md` v1.1, 2026-03-26). Every pattern in those two upstream files applies to Safety unless explicitly overridden in this document (nothing is overridden).

**Inherited verbatim — do NOT restate in Safety code or reviews:**

| Pattern | Source | Safety reuse |
|---------|--------|--------------|
| React 18.3.1 + TypeScript 5.4.5 + Vite project structure | Inspection §1 (via Reporting §0) | Used unchanged |
| Naming conventions — kebab-case files, PascalCase components, camelCase hooks | Inspection §2 | Used unchanged |
| Component patterns — props interface, named exports, `FC` typing | Inspection §3 | Used unchanged |
| **State management** — TanStack Query v5 for server state; Zustand v4 for client/draft state | Inspection §4 (via Reporting §0) | Used unchanged — Safety adds module-scoped stores (§7) |
| Axios v1.7 client with JWT refresh interceptor | Inspection §5 | Used unchanged — Safety endpoints mount at `/api/safety/*` |
| Zod v3 validation schemas + `react-hook-form` v7 integration | Inspection §6 | Used unchanged — Safety schemas per-phase (§8) |
| IndexedDB via `idb` v8 for offline / draft persistence | Inspection §7 | Used unchanged — Safety uses it for 30-second draft auto-save (§4, §7) |
| Mobile-first Tailwind v3.4.7 responsive patterns | Inspection §8 | Used unchanged — Safety hardens for tablet-primary SOI (§3) |
| Error boundary + API error envelope handling | Inspection §9 | Used unchanged |
| Testing patterns — React Testing Library v14 + Vitest v1.6 + Playwright v1.45 for E2E | Inspection §10 | Used unchanged — Safety adds anonymity + phase-transition tests (§10) |
| Auth store + `PermissionGate` / `ProcessGate` components | Reporting §0A (from `ssot_auth_specific.md`) | Used unchanged — Safety registers `SAF_F_*` / `SAF_P_*` IDs (§9) |
| `@/` path alias; no relative paths > 1 level | Reporting §10.2 | Used unchanged |
| Config-versioned form rendering (schema_version pinned at creation) | Reporting §9 | Pattern reused — Safety pins `schema_version` on `vims_safety_incident` (§8) |
| Auto-save hook (`useAutoSave`, IndexedDB, never API) | Reporting §4.2 | Reused with 30s interval per **D-GAP-F1** (SSOT §6 L1487) |

**Rule (inherited from Reporting §0):** If a pattern exists upstream, use it. This file adds only Safety-specific patterns that have no upstream equivalent.

**Arbitration:** When a pattern is defined upstream, upstream wins. This file only binds Safety-specific semantics (9-phase stepper, anonymity, M-SCAT picker, paper-first download) onto those inherited primitives.

---

## 1. Safety Naming Conventions

Everything that is Safety-module-owned carries a `Safety*` / `safety/` / `SAF_*` marker. This lets static analysis, lint rules, and coverage audits distinguish Safety code from sibling-module code in the same monorepo.

### 1.1 Component Prefix — `Safety*`

Every React component file authored for this module exports a PascalCase component whose name begins with `Safety`:

| Category | Component example | File |
|----------|-------------------|------|
| Module route | `SafetyIncidentListPage` | `src/routes/safety/incident/index.tsx` |
| Phase screen | `SafetyIncidentPhase3` | `src/routes/safety/incident/[id]/phase-3.tsx` |
| Shared block | `SafetySignatureBlock` | `src/components/safety/shared/signature-block.tsx` |
| Picker | `SafetyMScatPicker` | `src/components/safety/shared/mscat-picker.tsx` |
| Finding row | `SafetySoiFindingRow` | `src/components/safety/shared/soi-finding-row.tsx` |
| Dashboard tile | `SafetySoiComplianceTile` | `src/components/safety/shared/soi-compliance-tile.tsx` |

**Rule:** Any component referenced from `src/routes/safety/**` or `src/components/safety/**` **must** have a `Safety`-prefixed exported name. ESLint rule `naming-convention` enforces this (config in `.eslintrc.cjs`). Violations block CI.

**Exception:** The generic `PermissionGate` and `ProcessGate` components are shared across modules (live under `src/components/shared/`); they are used as-is without renaming.

### 1.2 Folder Layout (per `<vims_integration>`)

Safety slots cleanly into the existing VIMS monorepo — it is not a standalone app. All paths are relative to the repo root.

```
src/
├── routes/
│   └── safety/                                         ← NEW Safety module
│       ├── index.tsx                                   ← Module landing + role-scoped tiles
│       ├── layout.tsx                                  ← SafetyModuleLayout (breadcrumbs, vessel dropdown slot)
│       ├── incident/
│       │   ├── index.tsx                               ← SafetyIncidentListPage
│       │   ├── new.tsx                                 ← SafetyIncidentCreatePage (first-hour checklist)
│       │   └── [id]/
│       │       ├── index.tsx                           ← SafetyIncidentDetail (stepper shell)
│       │       ├── phase-1.tsx                         ← Scene Control + intake
│       │       ├── phase-2.tsx                         ← Resources Allocated
│       │       ├── phase-3.tsx                         ← Evidence Collection
│       │       ├── phase-4.tsx                         ← Facts Systemized (STEP timeline)
│       │       ├── phase-5.tsx                         ← Causes Analysed (M-SCAT + causal layers)
│       │       ├── phase-6.tsx                         ← Findings Submitted (bias-guard gate)
│       │       ├── phase-7.tsx                         ← DPA Accepted / Report Issued
│       │       └── phase-8.tsx                         ← Follow-up / Effectiveness Verified
│       ├── near-miss/
│       │   ├── index.tsx                               ← SafetyNearMissListPage
│       │   ├── new.tsx                                 ← SafetyNearMissCreatePage (anonymity notice)
│       │   └── [id].tsx                                ← SafetyNearMissDetail (single-screen)
│       ├── scm/
│       │   ├── index.tsx                               ← SafetyScmListPage (Regular + Ad-Hoc)
│       │   ├── new.tsx                                 ← SafetyScmCreatePage
│       │   └── [id].tsx                                ← SafetyScmDetail (agenda + attendance)
│       └── soi/
│           ├── index.tsx                               ← SafetySoiListPage
│           ├── new.tsx                                 ← SafetySoiPlannerPage (13-area picker)
│           └── [id]/
│               ├── index.tsx                           ← SafetySoiDetail (event + findings)
│               ├── download.tsx                        ← SafetySoiDownloadPage (paper-first — §6)
│               └── findings.tsx                        ← SafetySoiFindingsRegister
├── components/
│   └── safety/                                         ← NEW
│       ├── shared/                                     ← cross-feature primitives
│       │   ├── signature-block.tsx                     ← SafetySignatureBlock (5 variants, §5.1)
│       │   ├── anonymity-badge.tsx                     ← SafetyAnonymityBadge (§5.2)
│       │   ├── mscat-picker.tsx                        ← SafetyMScatPicker (174-row, §5.3)
│       │   ├── mscat-subcode-display.tsx               ← SafetyMscatSubcodeDisplay (read-only, §5.8)
│       │   ├── bias-guard-checklist.tsx                ← SafetyBiasGuardChecklist (8 guards, §5.4)
│       │   ├── barrier-analysis-canvas.tsx             ← SafetyBarrierAnalysisCanvas (§5.5)
│       │   ├── causal-layer-tabs.tsx                   ← SafetyCausalLayerTabs (Imm/Int/Root, §5.6)
│       │   ├── soi-finding-row.tsx                     ← SafetySoiFindingRow (tablet-compact, §5.7)
│       │   ├── risk-band-pill.tsx                      ← SafetyRiskBandPill (GREEN/YELLOW/RED)
│       │   ├── imo-classifier-pill.tsx                 ← SafetyImoClassifierPill (SMC/MC/MI)
│       │   ├── state-pill.tsx                          ← SafetyStatePill (workflow states)
│       │   ├── alarp-gauge.tsx                         ← SafetyAlarpGauge (Round 21 R02)
│       │   ├── chain-of-custody-tab.tsx                ← SafetyChainOfCustodyTab
│       │   └── stepper.tsx                             ← SafetyPhaseStepper (9-phase, §4)
│       ├── incident/
│       │   ├── first-hour-checklist.tsx                ← SafetyFirstHourChecklist (D-GAP-R07)
│       │   ├── step-timeline.tsx                       ← SafetyStepTimeline (Phase 4)
│       │   ├── evidence-matrix.tsx                     ← SafetyEvidenceMatrix (Phase 3/5)
│       │   ├── recommendation-form.tsx                 ← SafetyRecommendationForm (C/P/L tiers)
│       │   └── fleet-circular-preview.tsx              ← SafetyFleetCircularPreview
│       ├── near-miss/
│       │   ├── triage-toggle.tsx                       ← SafetyNmTriageToggle (Low/High)
│       │   └── anonymity-notice.tsx                    ← SafetyNmAnonymityNotice
│       ├── scm/
│       │   ├── agenda-editor.tsx                       ← SafetyScmAgendaEditor (SSQE §9)
│       │   ├── attendance-roster.tsx                   ← SafetyScmAttendanceRoster (WRH join)
│       │   └── ad-hoc-banner.tsx                       ← SafetyScmAdHocBanner
│       └── soi/
│           ├── area-picker.tsx                         ← SafetySoiAreaPicker (13 areas)
│           ├── findings-register.tsx                   ← SafetySoiFindingsRegister
│           └── download-button.tsx                     ← SafetySoiDownloadButton (paper-first, §6)
├── hooks/
│   └── safety/                                         ← NEW — prefix useSafety*
│       ├── query-keys.ts                               ← safetyKeys factory (§7.2)
│       ├── use-safety-auth.ts                          ← permission helpers (SAF_F_*/SAF_P_*)
│       ├── use-safety-incident.ts                      ← incident CRUD + draft hydration
│       ├── use-safety-phase-transition.ts              ← gate validation + stepper advance
│       ├── use-safety-draft.ts                         ← 30s auto-save (D-GAP-F1)
│       ├── use-safety-near-miss.ts
│       ├── use-safety-scm.ts
│       ├── use-safety-scm-attendance.ts                ← WRH attendance live join
│       ├── use-safety-soi.ts
│       ├── use-safety-soi-download.ts                  ← paper-first PDF/Excel
│       ├── use-safety-mscat.ts                         ← master_mscat_taxonomy
│       ├── use-safety-anonymity.ts                     ← viewer-role → mask/unmask
│       └── use-safety-bias-guards.ts                   ← checklist evaluation
├── stores/
│   └── safety/                                         ← NEW — suffix safety*Store
│       ├── safety-incident-draft-store.ts              ← per-phase draft working set
│       ├── safety-soi-planner-store.ts                 ← selected areas + trainee rotation
│       ├── safety-scm-agenda-store.ts                  ← in-session agenda edits
│       ├── safety-filter-store.ts                      ← dashboard filter chips (band, period)
│       └── safety-navigation-store.ts                  ← stepper state, last-visited phase
├── schemas/
│   └── safety/                                         ← NEW — one Zod schema per form
│       ├── incident-phase-1.ts                         ← intake + first-hour
│       ├── incident-phase-2.ts                         ← resources
│       ├── incident-phase-3.ts                         ← evidence
│       ├── incident-phase-4.ts                         ← STEP / facts
│       ├── incident-phase-5.ts                         ← M-SCAT + causal layers
│       ├── incident-phase-6.ts                         ← findings submitted
│       ├── incident-phase-7.ts                         ← DPA accept
│       ├── incident-phase-8.ts                         ← effectiveness verify
│       ├── near-miss.ts                                ← anonymity + triage
│       ├── scm-regular.ts                              ← SSQE §9.x agenda
│       ├── scm-ad-hoc.ts                               ← Master/CO-hosted agenda
│       ├── soi-event.ts                                ← event planner
│       ├── soi-finding.ts                              ← finding registration
│       └── common.ts                                   ← shared refinements (e.g. narrative min-length)
├── api/
│   └── safety/                                         ← Axios endpoint wrappers
│       ├── incidents.ts
│       ├── near-miss.ts
│       ├── scm.ts
│       ├── soi.ts
│       ├── actions.ts
│       └── reference.ts                                ← master_* lookups
└── types/
    └── safety/
        ├── incident.ts                                 ← IncidentRecord, PhaseNumber, SchemaVersion
        ├── near-miss.ts                                ← NearMissRecord, AnonymityView
        ├── scm.ts                                      ← ScmMeeting, MeetingType
        ├── soi.ts                                      ← SoiEvent, SoiFinding, FindingSeverity
        └── common.ts                                   ← RiskBand, ImoClassifier, CausalLayer
```

**Rule:** The folder names `safety/` under `routes`, `components`, `hooks`, `stores`, `schemas`, `api`, `types` are reserved for this module. Sibling modules do NOT write into `safety/` folders, and Safety does NOT write into `reporting/`, `inspection/`, or `shared/` folders.

### 1.3 Hook Prefix — `useSafety*`

Every hook file in `src/hooks/safety/` exports a camelCase hook whose name begins with `useSafety`:

```ts
// hooks/safety/use-safety-incident.ts
export function useSafetyIncident(incidentId: string) { /* ... */ }

// hooks/safety/use-safety-phase-transition.ts
export function useSafetyPhaseTransition(incidentId: string, from: PhaseNumber, to: PhaseNumber) { /* ... */ }

// hooks/safety/use-safety-mscat.ts
export function useSafetyMscat(search: string) { /* ... */ }
```

**Exception:** The shared `useAuth()` helper (from `src/hooks/shared/`) is re-exported via `useSafetyAuth()` thin wrapper that additionally exposes `hasSafForm('SAF_F_001')` / `hasSafProcess('SAF_P_002')` convenience predicates.

### 1.4 Store Suffix — `safety*Store`

Zustand stores live under `src/stores/safety/`. Each store's default export is the hook `useSafety<Name>Store`. The **module constant** used for devtools naming is `safety<Name>Store`:

```ts
// stores/safety/safety-incident-draft-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SafetyIncidentDraftState {
  draftsByPhase: Record<number, Record<string, unknown>>;
  setField: (phase: number, key: string, value: unknown) => void;
  clearPhase: (phase: number) => void;
  hydrateFromIndexedDb: (incidentId: string) => Promise<void>;
}

export const useSafetyIncidentDraftStore = create<SafetyIncidentDraftState>()(
  persist(
    (set) => ({ /* ... */ }),
    { name: 'safetyIncidentDraftStore' }   // ← devtools + persistence key
  )
);
```

**Rule:** Stores do not persist PII or signatures — only draft field values. Signatures always round-trip through the server (see §7.4, "Optimistic update rules").

### 1.5 Schema Location + Column Contract

Zod schemas live under `src/schemas/safety/`. Each schema carries a `schema_version` literal that the server stamps onto `vims_safety_incident.schema_version` on create (**D-EDGE-11**, SSOT §6 L1442). Historical records render with their creation-time schema — the frontend never forces a migration.

```ts
// schemas/safety/incident-phase-1.ts
import { z } from 'zod';

export const SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION = 1 as const;

export const safetyIncidentPhase1Schema = z.object({
  schema_version: z.literal(SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION),
  occurred_at: z.string().datetime(),       // ISO-8601, vessel local time via wrh_ship_time_config
  vessel_id: z.string().uuid(),
  location_onboard: z.string().min(3),
  reporter_rank_code: z.string().min(1),
  first_hour_checklist: z.object({
    alarm_logs_frozen: z.boolean(),
    damage_assessed: z.boolean(),
    scene_secured: z.boolean(),
    photographs_sketch_done: z.boolean(),
    witnesses_recorded: z.boolean(),
  }),                                       // D-GAP-R07
  narrative: z.string().min(120),           // VALIDATION_RULES §narrative_min_length
});

export type SafetyIncidentPhase1Values = z.infer<typeof safetyIncidentPhase1Schema>;
```

**Rule:** Every Safety Zod schema file exports both the schema and a `SCHEMA_VERSION` constant. The value flows into the API body verbatim — the server stores it on `vims_safety_incident.schema_version`. See BACKEND_STRUCTURE.md §incident schema for column contract.

### 1.6 Permission IDs

Form IDs (`SAF_F_*`) and Process IDs (`SAF_P_*`) mirror Reporting's `RPT_F_*` / `RPT_P_*` pattern. They are stored in `msc_profiles` and read from the JWT payload into the shared auth store. See §9 for gating rules.

---

## 2. Component Hierarchy (Text Tree)

The top-level shape of Safety UI — each node maps to a folder in §1.2.

```
<VimsAppShell>                                          ← inherited (src/routes/_layout.tsx)
└── <SafetyModuleLayout>                                ← src/routes/safety/layout.tsx
    ├── <SafetyBreadcrumbs>                             ← inherited breadcrumb + Safety crumbs
    ├── <VesselDropdown>                                ← inherited; scoped by master_RoleByVessel
    └── <Outlet />                                      ← per-feature route
        │
        ├── ── INCIDENT ────────────────────────────────
        │   <SafetyIncidentListPage>
        │   └── <SafetyIncidentDetail>                   ← stepper shell
        │       ├── <SafetyPhaseStepper phases=9 />      ← §4 — horizontal on desktop, vertical on tablet
        │       ├── <SafetyRiskBandPill />               ← GREEN/YELLOW/RED (DESIGN_SYSTEM §3.1)
        │       ├── <SafetyImoClassifierPill />          ← SMC/MC/MI (DESIGN_SYSTEM §3.2)
        │       ├── <SafetyStatePill />                  ← DRAFT/SUBMITTED/UNDER REVIEW/... (DESIGN_SYSTEM §4.1)
        │       └── per-phase screen:
        │           ├── phase-1  → <SafetyFirstHourChecklist /> + intake form
        │           ├── phase-2  → Resources Allocated form
        │           ├── phase-3  → <SafetyChainOfCustodyTab /> + <SafetyEvidenceMatrix />
        │           ├── phase-4  → <SafetyStepTimeline />
        │           ├── phase-5  → <SafetyCausalLayerTabs />
        │           │              ├── <SafetyMScatPicker />          ← 174-row picker
        │           │              ├── <SafetyMscatSubcodeDisplay />  ← read-only chips
        │           │              └── <SafetyBarrierAnalysisCanvas />
        │           ├── phase-6  → <SafetyBiasGuardChecklist guards=8 /> + <SafetyRecommendationForm />
        │           ├── phase-7  → DPA accept: <SafetySignatureBlock role="DPA" />
        │           └── phase-8  → Effectiveness verify + closure signatures
        │
        ├── ── NEAR MISS ───────────────────────────────
        │   <SafetyNearMissListPage>
        │   └── <SafetyNearMissDetail>
        │       ├── <SafetyNmAnonymityNotice />          ← banner explaining D-GAP-J1
        │       ├── <SafetyAnonymityBadge view="viewer-role" />  ← §5.2
        │       ├── <SafetyNmTriageToggle />             ← Low / High
        │       └── <SafetySignatureBlock role="Master" />
        │
        ├── ── SCM ─────────────────────────────────────
        │   <SafetyScmListPage>
        │   └── <SafetyScmDetail>
        │       ├── <SafetyScmAdHocBanner />             ← visible if meeting_type=ad_hoc
        │       ├── <SafetyScmAgendaEditor />            ← SSQE §9.x agenda items
        │       ├── <SafetyScmAttendanceRoster />        ← WRH join; warn-don't-block (D-GAP-M11)
        │       └── <SafetySignatureBlock role="Master" />
        │
        └── ── SOI ─────────────────────────────────────
            <SafetySoiListPage>
            └── <SafetySoiDetail>
                ├── <SafetySoiAreaPicker areas=13 />     ← incl. §12 Cross-cutting (D-SOI-16)
                ├── <SafetySoiDownloadButton />          ← paper-first (§6)
                ├── <SafetySoiFindingsRegister>
                │   └── <SafetySoiFindingRow />          ← tablet-compact (§5.7) — repeats per finding
                └── <SafetySignatureBlock role="Master" /> ← D-SOI-07 closure
```

---

## 3. Mobile-First Mandate

### 3.1 The Rule

SOI runs on vessel tablets. Every new Safety component begins its CSS at the smallest supported breakpoint, then scales up. Desktop styles are **additive** overrides, never the default.

- **Tailwind breakpoints** are inherited from Inspection §7 / DESIGN_SYSTEM §11.1:
  - `sm` = 640px
  - `md` = 768px (Safety's minimum for CRUD — `bp-tablet`, **D-GAP-M34**)
  - `lg` = 1024px (Safety's landscape tablet threshold)
  - `xl` = 1280px (Safety's primary desktop target)
  - `2xl` = 1536px

- **Tablet is the CRUD minimum.** Per **D-GAP-M34** (SSOT §6 L1533) — phone (≤ 480px) is **read-only dashboards only**; every create/edit surface disables itself below `md` and shows the banner: *"This surface requires a tablet or desktop (D-GAP-M34)."*

- **Desktop is the primary target** — but we **start** at tablet for every component. Test order: phone-readonly → tablet-CRUD → desktop-full. Any component that visually collapses when widened was built correctly; any that only works on desktop and breaks on tablet failed the mandate.

### 3.2 44×44 Hit Targets (Glove Use)

Locked by **DESIGN_SYSTEM §7.3** (WCAG 2.1 AAA §2.5.5 + D-GAP-M35):

- Primary buttons (Submit, Approve, Send Back): **44 × 44 px minimum** (48 × 44 preferred).
- Icon-only buttons (delete row, attach photo): **44 × 44 px** with 8px internal padding.
- Checkbox / radio: 24 × 24 px input inside a **44 × 44 px** clickable wrapper.
- Signature canvas field: 320 × 120 px minimum; the containing tap area ≥ 44 × 44 px.

**Engineering rule:** Use the Tailwind token `min-h-[44px] min-w-[44px]` on every interactive element. Wrapping smaller icons in a `<button>` with explicit `p-3` (12px padding around a 20px icon = 44px total) is the preferred pattern.

### 3.3 Glove-Use Considerations

- **Accidental drag suppression** — SOI finding rows use `touch-action: pan-y` to prevent horizontal drag gestures triggering the rubber-band on iPad Safari while the Chief Officer is scrolling through 100+ items.
- **No hover-only states** — every `hover:` Tailwind utility has a matching `focus-visible:` or `active:` equivalent. Touch devices never fire hover reliably.
- **No long-press** — context menus open on explicit tap-to-open toggles, not long-press (unlearnable with gloves).
- **Double-tap-to-zoom disabled** on form surfaces via the viewport meta (`user-scalable=no` is **not** used; we use CSS `touch-action: manipulation` on form wrappers only — readers retain pinch-zoom).
- **Large input fonts** — `text-base` (16px) minimum on every `<input>` to prevent iOS auto-zoom-on-focus (DESIGN_SYSTEM §11.3).

### 3.4 Mobile-First Test Mental Model

> "Start at tablet portrait 768×1024. If it works there, widen; never narrow."

Every Safety component in `components/safety/**` has at least one Vitest + RTL test that mounts inside a `ResizeObserver` mock at `width=768`. Desktop-specific assertions live in separate tests guarded by `resizeTo(1280)`. See §10.

---

## 4. 9-Phase Stepper Pattern (Incident)

### 4.1 Phase Contract

The Incident module's state machine — locked by **D-DNV-05** (SSOT §6 L1407) and elaborated in SSOT §2B.6 — drives a 9-phase stepper. Phase 0 is the informal "draft" state (record exists locally, no server number assigned). Phases 1–8 are the DNV canonical 8-phase flow plus the pre-submit draft:

| # | Phase | UI route segment | State pill on entry | Gate before advance |
|---|-------|------------------|---------------------|---------------------|
| 0 | Draft | `/safety/incident/new` | `DRAFT` (neutral) | None — save to local + IndexedDB |
| 1 | Scene Control | `phase-1` | `SUBMITTED` | First-hour checklist (D-GAP-R07) + narrative ≥120 chars |
| 2 | Resources Allocated | `phase-2` | `UNDER REVIEW` | Investigator assigned + investigation-depth chosen (D-GAP-R14) |
| 3 | Evidence Collection | `phase-3` | `UNDER REVIEW` | ≥1 evidence entry OR "n/a — justified" per category (bias guard #1 Recency) |
| 4 | Facts Systemized | `phase-4` | `UNDER REVIEW` | STEP timeline has ≥1 row |
| 5 | Causes Analysed | `phase-5` | `UNDER REVIEW` | ≥1 Immediate + ≥1 Root cause tagged (D-GAP-R01); ≥2 RCA tools (SHALLOW) / 3 (MEDIUM) / 5 (DEEP) |
| 6 | Findings Submitted | `phase-6` | `UNDER REVIEW` | 8 bias guards evaluated; ≥1 each of Corrective/Preventive/Lessons for YELLOW+RED (D-GAP-R13) |
| 7 | DPA Accepted / Report Issued | `phase-7` | `APPROVED` | DPA signature (GREEN/YELLOW) or FM signature (RED) per D-RBAC-05 |
| 8 | Follow-up / Effectiveness Verified | `phase-8` | `CLOSED` | Every CA shows verified-effective status |

The **Phase 5 → Phase 3 loop-back gate** (DNV "need more info?" per D-DNV-05) is a special transition: the stepper component permits in-place re-opening without data loss and logs the loop-back to `vims_safety_incident_phase_log` with a mandatory reason.

### 4.2 Stepper Component Contract

```tsx
// components/safety/shared/stepper.tsx

interface SafetyPhaseStepperProps {
  incidentId: string;
  currentPhase: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
  highestReachedPhase: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
  orientation?: 'horizontal' | 'vertical';   // default: auto — horizontal ≥ lg, vertical below
  onNavigate: (target: PhaseNumber) => void; // throws if target > highestReachedPhase + 1
  canLoopBack: boolean;                      // true once currentPhase ≥ 4; gates Phase 5→3 arrow
  permissions: {
    canSubmitPhase1: boolean;                // hasSafProcess('SAF_P_001')
    canAdvanceToPhase7: boolean;             // hasSafProcess('SAF_P_004') — DPA
    canFinalizePhase8: boolean;              // hasSafProcess('SAF_P_005') — DPA/FM
  };
}

export const SafetyPhaseStepper: FC<SafetyPhaseStepperProps> = ({ /* ... */ }) => { /* ... */ };
```

**Rules:**

1. **Non-linear navigation allowed backwards only.** A user may click any phase `≤ highestReachedPhase`; clicking `highestReachedPhase + 1` triggers the gate validator (§4.4); clicks further forward are no-ops (visually dim).
2. **Loop-back Phase 5 → Phase 3** requires a reason modal before the transition. The reason goes into the `vims_safety_incident_phase_log` POST body as `loopback_reason`.
3. **Orientation auto-flips to vertical below `lg`.** Horizontal stepper on desktop; vertical rail on tablet portrait — the label and completion icon stack instead of shrink.
4. **Current phase** has `primary-500` fill + `text-primary-700` label; reached phases have `success-500` check; unreached are `neutral-200` outline.
5. **ARIA:** `role="progressbar" aria-valuenow={currentPhase} aria-valuemin={0} aria-valuemax={8}` on the stepper container; each phase is an `<li>` with `aria-current="step"` on the active one.

### 4.3 Per-Phase Route Mapping

Routes use a **nested** layout so the stepper persists across phase navigation:

```
/safety/incident/:id                        → SafetyIncidentDetail (stepper shell + outlet)
/safety/incident/:id/phase-1                → SafetyIncidentPhase1 (Scene Control)
/safety/incident/:id/phase-2                → SafetyIncidentPhase2 (Resources Allocated)
/safety/incident/:id/phase-3                → SafetyIncidentPhase3 (Evidence Collection)
/safety/incident/:id/phase-4                → SafetyIncidentPhase4 (Facts Systemized)
/safety/incident/:id/phase-5                → SafetyIncidentPhase5 (Causes Analysed)
/safety/incident/:id/phase-6                → SafetyIncidentPhase6 (Findings Submitted)
/safety/incident/:id/phase-7                → SafetyIncidentPhase7 (DPA Accepted)
/safety/incident/:id/phase-8                → SafetyIncidentPhase8 (Effectiveness Verified)
```

Every phase route is wrapped by `<PermissionGate formId="SAF_F_001">` (the Incident form). Per-phase advance buttons are wrapped by `<ProcessGate processId="SAF_P_00N">` (§9).

### 4.4 Draft State — Local Persistence + Server Reconciliation

Per **D-GAP-F1** (SSOT §6 L1487), every Safety form auto-saves every 30 seconds to the browser's IndexedDB. This preserves work across satcomm drops.

**Architecture:**

```
┌───────────────────────┐        30s         ┌─────────────────────┐
│ Zustand working set   │ ─── writeDb() ───► │ IndexedDB           │
│ safetyIncidentDraft-  │                    │ table "safety-      │
│ Store (in memory)     │                    │  incident-drafts"   │
└───────────────────────┘                    └─────────────────────┘
        │                                             ▲
        │ on Phase N Submit                           │ on mount or
        ▼                                             │ reconnect
┌───────────────────────┐    POST/PATCH    ┌──────────┴──────────┐
│ /api/safety/          │ ◄─────────────── │ reconcile() helper   │
│ incidents/:id/phase-N │                  │ (use-safety-draft.ts)│
└───────────────────────┘                  └──────────────────────┘
```

**Rules:**

1. **IndexedDB key:** `safety-incident-draft::<incidentId>::phase-<N>::<schema_version>`. Keying on schema_version guarantees a post-migration client never overwrites a pre-migration draft with a stale shape.
2. **Auto-save interval:** 30 seconds (D-GAP-F1). Jitter ±2 seconds to avoid thundering-herd when a fleet of tablets reconnects to satcomm simultaneously.
3. **Server is authoritative on submit.** When the user clicks Submit on a phase, the stepper hook fires the phase-transition mutation; on 2xx, the IndexedDB record is **deleted** (not kept as a zombie draft).
4. **Reconciliation on mount:** If both a server record (from GET `/api/safety/incidents/:id`) and a local draft exist, `reconcile()` compares `updated_at` timestamps. If local > server, prompt: *"A newer local draft was found. Restore it?"* (inherited from Reporting §4.2). Never silently overwrite.
5. **No cross-device sync** — the draft lives on the device that created it. Another device opening the same incident sees only the server state. This aligns with D-GAP-F1 (browser local storage, not a cloud draft service).
6. **30-day drift cleanup:** Drafts older than 30 days are evicted on app start. The Safety module shares the IndexedDB cleanup hook with Reporting (`useSyncQueue` + garbage collector).

### 4.5 Gate Validation Before Advance

Each phase advance triggers a **gate validator** before firing the mutation. Validators live in `src/hooks/safety/use-safety-phase-transition.ts` and reference rules documented in **VALIDATION_RULES.md**.

```ts
// hooks/safety/use-safety-phase-transition.ts

export function useSafetyPhaseTransition(incidentId: string) {
  const validateGate = async (from: PhaseNumber, to: PhaseNumber): Promise<GateResult> => {
    // 1. Zod structural validation on the Phase <from> schema
    // 2. Cross-field validators (see VALIDATION_RULES §phase-gates)
    // 3. Bias-guard evaluation (§5.4 — hard blocks Phase 6→7 if guard #5 fails)
    // 4. Signature order check (Reporter → Master → HOD → DPA → FM)
    //    see VALIDATION_RULES §signature_sequencing
    return { ok: true }; // or { ok: false, errors: [...] }
  };

  const advance = useMutation({ /* ... */ });

  return { validateGate, advance };
}
```

**Rule:** No gate validator is client-only. Every client rule is duplicated on the server (`apps/safety/views/*.py`). The client copy exists to give instant UX feedback; the server copy is authoritative.

---

## 5. Reusable Safety Sub-Components

Eight components listed in `<vims_integration>` + the stepper (§4) form the Safety component library. Every one is tablet-first and ARIA-complete.

### 5.1 `SafetySignatureBlock` — 5 Role Variants

**Purpose:** Capture + display a digitally-attested signature per role. Enforces the DESIGN_SYSTEM §8 signature anatomy.

**Props:**

```ts
interface SafetySignatureBlockProps {
  role: 'reporter' | 'master' | 'hod' | 'dpa' | 'fm';
  mode: 'capture' | 'display';                     // capture = typing required; display = read-only
  existingSignature?: {
    signer_user_id: string;
    signer_rank_code: string;                      // from master_applied_rank
    signer_display_name: string;
    signed_at: string;                             // ISO-8601 with TZ from wrh_ship_time_config
    device_fingerprint_last8: string;
    wet_scan_attachment_id?: string;
  };
  onSign?: (typedName: string) => Promise<void>;   // capture mode only
  onAttachScan?: (file: File) => Promise<void>;    // capture mode only
  awaitingLabel?: string;                          // used when mode=display but no signature yet
}
```

**State requirements:** Component is **server-authoritative** (see §7.4). Signature round-trips must not be optimistic — the ink does not render until the server returns 201.

**Accessibility:** Role label read as primary cue; color is secondary (DESIGN_SYSTEM §7 WCAG AA). `aria-label` on the capture input reads the role full name (e.g., "Designated Person Ashore — type full name to sign").

**Mobile-first notes:** On tablet portrait the card uses `max-w-[480px]` and the signature canvas scales to 100% width; on desktop it sits inside a 2-column layout next to metadata.

**Decision:** D-GAP-D1 (hybrid signature), D-PDF-01 (Master/DPA/FM chain), D-GAP-D2 (no PKI in V1 — device fingerprint is an audit identifier, not a cryptographic proof).

### 5.2 `SafetyAnonymityBadge` — D-GAP-J1

**Purpose:** Render the reporter-identity field with masking rules for Near Miss records. Replaces the name with `[EyeOff] Anonymous Reporter` for non-DPA/FM viewers; shows full name with `[Eye]` for DPA, FM, and self-view.

**Props:**

```ts
interface SafetyAnonymityBadgeProps {
  reporter: {
    user_id: string;
    display_name: string;   // always present in props; masking decision is view-side
    rank_code: string;
  };
  viewerRole: 'reporter-self' | 'master' | 'hod' | 'so' | 'dpa' | 'fm' | 'other';
  context: 'card' | 'detail-header' | 'signature-block' | 'pdf-fallback';
}
```

**State requirements:** Stateless — depends on the viewer role from `useSafetyAuth()`. Never persists.

**Accessibility:** Masked rendering includes `aria-label="Reporter identity is hidden for this viewer role"`; unmasked includes `aria-label="Reporter: <name>. You see this because you are DPA/FM/self."`.

**Mobile-first notes:** Icon-size `icon-sm` (16px) matches typography-line-height on tablet; never collapses.

**Decision:** D-GAP-J1 (SSOT §6 L1498). Anonymity applies to **Near Miss reporter field only** — does NOT mask Master/HOD/SO signatures or crew names in causal narratives (DESIGN_SYSTEM §9.3).

### 5.3 `SafetyMScatPicker` — 174-Row Searchable

**Purpose:** Pick one (or more) M-SCAT subcodes from the 174-row `master_mscat_taxonomy` table during Phase 5 Causes Analysed. Extended by **Round 21** with the new `10.15 Design/MOC Governance` category (SSOT §6).

**Props:**

```ts
interface SafetyMScatPickerProps {
  selected: MscatSubcodeRef[];   // each = { category_id, subcode_id, cause_type }
  onChange: (next: MscatSubcodeRef[]) => void;
  maxSelections?: number;        // default: undefined (Round 21 R03 = no artificial cap)
  filterCauseType?: 'basic-cause' | 'lack-of-control' | 'all';   // default: 'all'
  causalLayer: 'immediate' | 'intermediate' | 'root';            // forwarded to store for D-GAP-R01 tagging
  disabled?: boolean;
}

interface MscatSubcodeRef {
  category_id: string;     // e.g., "10.15"
  subcode_id: string;      // e.g., "10.15.3"
  cause_type: 'basic' | 'lack-of-control';
  // display fields (category_name, subcode_description) resolved via useSafetyMscat()
}
```

**State requirements:** Uses `useSafetyMscat(search)` which fetches `master_mscat_taxonomy` via `/api/safety/reference/mscat?q=...`. Cached via `safetyKeys.mscat()` with `staleTime: Infinity` (the taxonomy only changes via DPA admin console — infrequent).

**Accessibility:** Keyboard-navigable combobox, `role="combobox"` on the search input, `role="listbox"` on the results. Each row exposes `aria-label` including category ID + full description (not just the 4-letter subcode).

**Mobile-first notes:** Full-screen sheet pattern on tablet portrait (rather than a floating dropdown, which is hard to target with gloves); inline popover on desktop. `max-h-[60vh]` with internal scroll.

**Decision:** D-DNV-01 (M-SCAT as canonical), D-GAP-R01 (causal-layer tagging), Round 21 R03 (no cap), Round 21 addition of 10.15.

### 5.4 `SafetyBiasGuardChecklist` — 8 Guards

**Purpose:** Render the 8 bias guards (5 DNV + 3 R12 organisational-defence) as a checklist at each phase-transition gate. Shows pass / soft-warn / hard-block / DPA-override states per DESIGN_SYSTEM §10.2.

**Props:**

```ts
interface SafetyBiasGuardChecklistProps {
  incidentId: string;
  triggerPoint: 'phase-4-to-5' | 'phase-5-to-6' | 'phase-6-to-7';
  evaluatedGuards: Record<BiasGuardId, GuardEvaluation>;   // from useSafetyBiasGuards()
  onJustify: (guardId: BiasGuardId, reason: string) => void;
  onDpaOverride: (guardId: BiasGuardId, reason: string) => void;
  readOnly?: boolean;
}

type BiasGuardId = 'recency' | 'assumption' | 'hindsight' | 'confirmation' | 'blame-fixation'
                 | 'plant-problem-trap' | 'personnel-problem-trap' | 'external-event-trap';

interface GuardEvaluation {
  state: 'unchecked' | 'passed' | 'warned' | 'blocked' | 'override' | 'justified' | 'softwarn-override';
  rationale?: string;
  evaluated_by: string;
  evaluated_at: string;
}
```

**State requirements:** Backed by server evaluation returned from `/api/safety/incidents/:id/bias-guards`. Guard #5 (Blame Fixation) is **hard-blocking** — it opens the DESIGN_SYSTEM §10.4 Guard-5 modal and cannot be soft-bypassed.

**Accessibility:** Each guard row is a `<fieldset>` with its guard number and short label as the `<legend>`; full description lives in the `aria-describedby` tooltip (DESIGN_SYSTEM §10.3).

**Mobile-first notes:** Single-column stack on tablet; two-column on desktop. Each row's clickable area is 44 × 44 px minimum (§3.2).

**Decision:** D-DNV-11 (5 guards), D-GAP-R12 (3 additional), SSOT §6 L1550.

### 5.5 `SafetyBarrierAnalysisCanvas` — Causal Layer Visualization

**Purpose:** Render the **Immediate → Intermediate → Root** causal tree as a barrier-analysis diagram for Phase 5. Uses inherited connector lines (1px `neutral-300`) and DESIGN_SYSTEM §5.1 layer tokens.

**Props:**

```ts
interface SafetyBarrierAnalysisCanvasProps {
  incidentId: string;
  causes: CauseNode[];
  onAddCause: (layer: CausalLayer, parentId?: string) => void;
  onEditCause: (causeId: string) => void;
  onReparent: (causeId: string, newParentId: string) => void;
  readOnly?: boolean;
}

interface CauseNode {
  id: string;
  layer: 'immediate' | 'intermediate' | 'root';
  parent_cause_id: string | null;
  mscat_subcode: MscatSubcodeRef;
  narrative: string;
}
```

**State requirements:** Tree operations write through `useSafetyIncident` mutations; no local-only tree state (so loop-backs from Phase 5 → 3 do not lose tree structure).

**Accessibility:** Canvas is SVG-based; each node also exposes a DOM `<button>` overlay so keyboard + screen-reader users can navigate (`tabindex=0`, `aria-label="Intermediate cause 2 of 4 — communication breakdown. Press Enter to edit."`).

**Mobile-first notes:** On tablet portrait (< 1024px), the canvas collapses to a vertical list view (reusing `SafetyCausalLayerTabs`, §5.6) so a Chief Officer on a tablet at sea can still operate it. Full canvas renders only on `lg+`.

**Decision:** D-GAP-R01 (causal-layer mandatory), D-DNV-01 (M-SCAT scaffolding), D-GAP-R14 (DEEP investigation requires all 5 RCA tools).

### 5.6 `SafetyCausalLayerTabs` — Immediate / Intermediate / Root

**Purpose:** Alternative to the canvas on small screens; tabs let a user drill into each layer one at a time.

**Props:**

```ts
interface SafetyCausalLayerTabsProps {
  incidentId: string;
  activeLayer: 'immediate' | 'intermediate' | 'root';
  onChangeLayer: (layer: CausalLayer) => void;
  counts: { immediate: number; intermediate: number; root: number };
}
```

**State requirements:** Active layer is a URL search param (`?layer=root`) so deep-linking works; also mirrored in `safetyNavigationStore` so back/forward within the same incident restores the last-visited layer.

**Accessibility:** `role="tablist"` with three `role="tab"` children; each tab's `aria-controls` points at the matching panel. Empty-state for the Root tab reads *"At least one Root-level cause is required before closing Phase 5 (D-GAP-R01)."*

**Mobile-first notes:** Tabs are the **default** rendering on tablet portrait; canvas takes over on `lg+`. The same store powers both.

**Decision:** D-GAP-R01, DESIGN_SYSTEM §5.2.

### 5.7 `SafetySoiFindingRow` — Tablet-Compact Finding Row

**Purpose:** Represent a single SOI finding in the findings register. Tuned for a Chief Officer to fill out on a tablet at sea, standing near a piece of equipment.

**Props:**

```ts
interface SafetySoiFindingRowProps {
  finding: SoiFinding;
  onChange: (patch: Partial<SoiFinding>) => void;
  onAttachPhoto: (file: File) => void;
  onDelete: () => void;
  readOnly?: boolean;
}

interface SoiFinding {
  id: string;
  area_id: string;                 // FK → master_soi_area
  item_number: string | null;      // nullable — D-SOI-10 paper-first, item-level responses live on paper
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  photo_attachments: AttachmentRef[];
  state: 'open' | 'pending' | 'master-approved' | 'closed' | 'carried-forward';
  incident_linked_id?: string;     // D-GAP-M16 — HIGH severity prompts incident creation
}
```

**State requirements:** Row-local draft saves optimistically to `safetySoiPlannerStore` then flushes to the server on blur-of-last-field. Photo attachments use the platform attachment upload service (no optimistic URL — display the `neutral-100` skeleton thumbnail until server confirms).

**Accessibility:** Row is a `<li>` with `aria-label` summarising area + severity + state. Severity pill uses DESIGN_SYSTEM §3.4 tokens with the color + text + icon triple-encoding.

**Mobile-first notes:** Row height = `--safety-soi-row-min-height` (56px on tablet; DESIGN_SYSTEM §11.2). Yes/No/N-A columns use `--safety-soi-cell-tap-area` (44 × 44 px). HIGH severity triggers an inline `Camera` icon that opens the device camera on tablet via `<input type="file" capture="environment">`.

**Decision:** D-SOI-07 (finding lifecycle), D-SOI-10 (paper-first — no per-item scan), D-GAP-M24 (HIGH requires photo), D-GAP-M16 (HIGH prompts incident creation), D-SOI-14 (Carried Forward).

### 5.8 `SafetyMscatSubcodeDisplay` — Read-Only Representation

**Purpose:** Show a previously-picked M-SCAT subcode as a read-only chip outside the picker (e.g., in the causal-tree canvas, the incident card, PDF preview pane).

**Props:**

```ts
interface SafetyMscatSubcodeDisplayProps {
  subcode: MscatSubcodeRef;
  variant?: 'chip' | 'inline-text' | 'table-row';
  showCategoryName?: boolean;   // default: true — helpful when subcode alone is ambiguous
}
```

**State requirements:** Stateless. Resolves the `category_name` / `subcode_description` via `useSafetyMscat()` cache (`staleTime: Infinity`) — no network call if the taxonomy is already warm.

**Accessibility:** `aria-label` reads the full description (`"M-SCAT 10.15.3: Design change not reviewed by MOC committee"`), not just the ID.

**Mobile-first notes:** `chip` variant max-width `20ch` with ellipsis overflow; `inline-text` variant truncates at `28ch` on tablet.

**Decision:** D-DNV-01, Round 21 addition of 10.15.

---

## 6. SOI Paper-First Download Flow (D-GAP-E4)

### 6.1 The Rule

Per **D-GAP-E4** (SSOT §6 L1483), SOI is paper-first with **no scan upload**. Revises D-SOI-10. The fieldwork happens on paper; the paper is filed in the ship's onboard SMS filing system; the digital record is linked to the paper by a **unique checklist ID**. PSC / auditors review the paper on demand.

### 6.2 UI Flow

```
┌────────────────────────┐
│ SafetySoiPlannerPage   │  Step 1 — SO / CO picks inspection scope
│ (new.tsx)              │           • Select physical areas (1..12 of 13)
│                        │           • §12 Cross-cutting auto-included if 3 months elapsed
│                        │           • Pick assistant (CMS cross-functional enforced, D-SOI-08)
│                        │           • Pick up to 3 trainees
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ POST /api/safety/soi/  │  Step 2 — Server creates vims_safety_soi_inspection
│        plan            │           • Assigns unique_checklist_id (barcode-encodable)
│                        │           • Freezes selected areas in vims_safety_soi_inspection_area
│                        │           • Flips checklist_generated_at = now()
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ SafetySoiDownloadPage  │  Step 3 — User clicks "Download Checklist"
│ (/safety/soi/:id/      │           • Choice of PDF or Excel (format = build-time deferral #10)
│  download)             │           • File contains unique_checklist_id barcode (deferral #10)
└───────────┬────────────┘
            ▼
        [ PAPER ]          Step 4 — Fieldwork on paper
            │
            ▼
┌────────────────────────┐
│ SafetySoiFindingsPage  │  Step 5 — Back on the bridge tablet, SO/CO types findings
│ (/safety/soi/:id/      │           into SafetySoiFindingRow × N. Finding references
│  findings)             │           the paper by unique_checklist_id only.
└────────────────────────┘           NO SCAN UPLOAD (D-GAP-E4).
```

### 6.3 Component Contract

`SafetySoiDownloadButton` (`components/safety/soi/download-button.tsx`):

```tsx
interface SafetySoiDownloadButtonProps {
  inspectionId: string;
  uniqueChecklistId: string;          // displayed on screen + embedded in file
  format: 'pdf' | 'excel';            // see BLOCKED stub below
  onDownloaded?: () => void;          // optimistic UI — mark "downloaded" state
  disabled?: boolean;
}
```

**Download handler:** Calls `GET /api/safety/soi/:id/checklist?format=<pdf|excel>`, streams the binary to a `Blob`, and triggers a programmatic `<a download>` click. No client-side PDF rendering — the server authority generates the document with the exact `unique_checklist_id`.

### 6.4 No Upload Component Exists

**Hard rule:** There is **no** `SafetySoiScanUpload` component in this module. No `/api/safety/soi/:id/scan` endpoint. No `scan_url` column on `vims_safety_soi_inspection`. If a future feature request asks for scan upload, the answer is "paper stays in the SMS filing system; the digital side links by unique ID" — and update the SSOT before reopening the decision.

### 6.5 Digital Finding Registration Links via Unique ID

`SafetySoiFindingsPage` displays the `unique_checklist_id` prominently in the header (read-only, `text-lg font-mono`). Every finding row created under that inspection inherits the ID via FK on `vims_safety_soi_finding.inspection_id`. There is no free-text ID entry (which would risk typos).

> **BLOCKED: SOI checklist file format (PDF vs Excel)**
> **Question:** Should the generated checklist be PDF only, Excel only, or user-choice per download?
> **Gap:** Build-time deferral #10 (see BACKEND_STRUCTURE.md build-time deferrals table). Round 20 left this open; D-GAP-E4 does not specify.
> **Impact:** `SafetySoiDownloadButton.format` prop signature is wider than it needs to be; `/api/safety/soi/:id/checklist?format=...` query param cannot be validated client-side until Product + Design lock.

> **BLOCKED: Barcode / QR format for unique checklist ID**
> **Question:** Code128 barcode, QR code, or human-readable-only?
> **Gap:** Build-time deferral #10 also encompasses the machine-readable encoding for the ID on the paper.
> **Impact:** Finding registration could eventually scan the paper's barcode to pre-fill `inspection_id`; blocked until decision.

---

## 7. State Management

Safety inherits TanStack Query v5 for server state and Zustand v4 for client state from Reporting §0 / Inspection §4. This section defines **what lives in which store** for Safety specifically.

### 7.1 Zustand Store Inventory

| Store | Scope | Persistence | Primary consumers |
|-------|-------|-------------|-------------------|
| `safetyIncidentDraftStore` | Draft phase values for the *currently-open* incident | IndexedDB (30s auto-save, D-GAP-F1) | Phase 1–8 forms |
| `safetySoiPlannerStore` | Selected areas, chosen assistant, trainee list | IndexedDB — purged on plan submit | `SafetySoiPlannerPage` |
| `safetyScmAgendaStore` | In-session agenda edits before SCM Regular/Ad-Hoc submit | IndexedDB — purged on meeting submit | `SafetyScmAgendaEditor` |
| `safetyFilterStore` | Dashboard filter chips (risk band, period, vessel) | `localStorage` | Dashboards (Phase 7 deliverable) |
| `safetyNavigationStore` | Last-visited phase per incident, last-visited causal layer | Session only (no persistence) | `SafetyPhaseStepper`, `SafetyCausalLayerTabs` |

**Rule:** Stores contain **working-set data only**. They do NOT mirror server state. When both a cached server query and a store draft exist for the same field, the Zustand draft wins *until* submit — at which point the mutation's `onSuccess` invalidates the relevant TanStack Query key and clears the draft.

### 7.2 TanStack Query Keys — `safetyKeys` Factory

```ts
// hooks/safety/query-keys.ts

export const safetyKeys = {
  all: ['safety'] as const,

  incidents: (vesselId: string) =>
    ['safety', 'incidents', vesselId] as const,
  incident: (incidentId: string) =>
    ['safety', 'incidents', 'by-id', incidentId] as const,
  incidentPhaseLog: (incidentId: string) =>
    ['safety', 'incidents', 'by-id', incidentId, 'phase-log'] as const,
  incidentFieldHistory: (incidentId: string) =>
    ['safety', 'incidents', 'by-id', incidentId, 'field-history'] as const,

  nearMiss: (vesselId: string) =>
    ['safety', 'near-miss', vesselId] as const,
  nearMissById: (id: string) =>
    ['safety', 'near-miss', 'by-id', id] as const,

  scm: (vesselId: string) =>
    ['safety', 'scm', vesselId] as const,
  scmMeeting: (id: string) =>
    ['safety', 'scm', 'by-id', id] as const,
  scmAttendanceWrh: (meetingId: string) =>
    ['safety', 'scm', 'by-id', meetingId, 'wrh-attendance'] as const,

  soiInspections: (vesselId: string) =>
    ['safety', 'soi', vesselId] as const,
  soiInspection: (id: string) =>
    ['safety', 'soi', 'by-id', id] as const,
  soiFindings: (inspectionId: string) =>
    ['safety', 'soi', 'by-id', inspectionId, 'findings'] as const,
  soiAreaMap: (vesselId: string) =>
    ['safety', 'soi', 'area-map', vesselId] as const,

  // Master reference data (static, staleTime: Infinity)
  mscat: (search?: string) =>
    ['safety', 'reference', 'mscat', search ?? ''] as const,
  immediateCauses: (search?: string) =>
    ['safety', 'reference', 'immediate-causes', search ?? ''] as const,
  lossTypes: () =>
    ['safety', 'reference', 'loss-types'] as const,
  soiAreas: () =>
    ['safety', 'reference', 'soi-areas'] as const,
  soiAreaItems: (areaId: string) =>
    ['safety', 'reference', 'soi-area-items', areaId] as const,
  biasGuards: () =>
    ['safety', 'reference', 'bias-guards'] as const,

  // Dashboards
  dashboard: (vesselId: string, period: string) =>
    ['safety', 'dashboard', vesselId, period] as const,
  soiCompliance: (vesselId: string, period: string) =>
    ['safety', 'dashboard', 'soi-compliance', vesselId, period] as const,
};
```

### 7.3 Stale Time Defaults (Safety Overrides)

| Data category | `staleTime` | Rationale |
|---------------|-------------|-----------|
| Incident detail | `2 * 60 * 1000` (2 min) | Phase transitions are frequent during active investigation |
| Near Miss detail | `5 * 60 * 1000` | Less editing pressure |
| SCM meeting | `5 * 60 * 1000` | — |
| SOI inspection list | `2 * 60 * 1000` | New findings common |
| Master reference tables (`mscat`, `loss-types`, `immediate-causes`, `soi-areas`, `bias-guards`) | `Infinity` | DPA-maintained, infrequent changes; refetch on explicit admin event |
| Dashboard aggregates | `5 * 60 * 1000` | Match Reporting analytics default |

### 7.4 Optimistic Update Rules

**Default:** Optimistic updates are **allowed** for low-risk state (SOI finding text, incident narrative, SCM agenda rearrangement) — pattern inherited from Reporting §4 (TanStack Query `onMutate` + rollback on error).

**Hard exceptions — NEVER optimistic:**

1. **Signatures (all 5 variants, §5.1).** A signature is a legal attestation. The ink does not render until the server returns 201 Created. Rollback UX on a signature is unacceptable.
2. **Phase transitions.** The stepper cannot advance to Phase N+1 until the server confirms the phase-log row. Reason: if the server rejects the transition (bias-guard server-side re-evaluation, permission re-check), an optimistic advance would show an APPROVED state that doesn't exist.
3. **Closure events.** Incident closure (Phase 7 DPA accept), SOI Master-approve, SCM finalize — all server-authoritative. The state pill flips only after the mutation succeeds.
4. **Permission-gated actions.** Any `onClick` wrapped by `<ProcessGate>` writes to the server first; the UI reflects the success after.
5. **Near Miss anonymity field changes.** Reporter identity masking is authoritative on the server; optimistic UI would risk leaking a name to a non-DPA/FM viewer during the round-trip window.

### 7.5 Server Reconciliation Strategy

On app load and on every network reconnect:

1. `useSafetyDraft` scans IndexedDB for drafts older than `server.updated_at`.
2. For each stale draft, prompt (inherited pattern, Reporting §4.2): *"A newer server version exists. Discard local draft?"*
3. For drafts newer than server, prompt: *"A newer local draft exists. Restore it?"*
4. Never auto-merge. Never silently discard.

**Cross-module live joins** (D-GAP-I2 — same DB, no sync):

- `vims_safety_scm_attendance` does **not** cache WRH rest-hour data — it queries `wrh_daily_rest_summary` live via SQL JOIN in the view layer, cached with `staleTime: 60 * 1000`. Warn-don't-block surfaced as a `warning` chip next to each attendee's name (D-GAP-M11).
- `vims_safety_incident` Phase 1 vessel-position field: live-joins `vims_daily_report` within ±12h (D-GAP-M09).
- `vims_safety_corrective_action.purchase_req_id`: hard FK (D-GAP-M12); the frontend renders the linked purchase-req state via `useQuery` against the Purchase module's API.

---

## 8. Form Patterns

### 8.1 React Hook Form + Zod — Inherited

Every Safety form uses `react-hook-form` + `zodResolver`, per Reporting §8 / Inspection §6. No custom form library.

```tsx
// routes/safety/incident/[id]/phase-1.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { safetyIncidentPhase1Schema, SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION } from '@/schemas/safety/incident-phase-1';

export const SafetyIncidentPhase1: FC<{ incidentId: string }> = ({ incidentId }) => {
  const form = useForm<SafetyIncidentPhase1Values>({
    resolver: zodResolver(safetyIncidentPhase1Schema),
    defaultValues: {
      schema_version: SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION,
      // ... hydrated from server + IndexedDB draft (see §7.5)
    },
  });
  // ...
};
```

### 8.2 Per-Phase Schema Versioning

Per **D-EDGE-11** (SSOT §6 L1442), each Safety form carries a `schema_version` that the server stamps onto `vims_safety_incident.schema_version` at create time. Historical records render with their creation-time schema.

**Rule:** Bumping a Phase schema is a breaking change — create a *new* schema file `incident-phase-5-v2.ts` alongside the existing `incident-phase-5.ts`. The UI dispatches schema based on `record.schema_version`:

```tsx
const PhaseFive = ({ record }: { record: IncidentRecord }) => {
  switch (record.schema_version) {
    case 1: return <SafetyIncidentPhase5V1 record={record} />;
    case 2: return <SafetyIncidentPhase5V2 record={record} />;
    default: throw new Error(`Unknown schema_version ${record.schema_version}`);
  }
};
```

No in-place migration. Grandfathering wins — see Reporting §9 for the proven pattern.

### 8.3 Narrative Min-Length Validators

Per VALIDATION_RULES.md (narrative rules):

| Form | Field | Min chars | Source |
|------|-------|-----------|--------|
| Incident Phase 1 | `narrative` | **120** | D-GAP-R05 / VALIDATION_RULES §incident_narrative_min |
| Near Miss | `description` | **80** | VALIDATION_RULES §near_miss_min_length |
| SOI Finding (HIGH) | `description` | **60** | D-GAP-M16 + VALIDATION_RULES §soi_high_severity |
| SCM Agenda Item | `decision` | **40** | VALIDATION_RULES §scm_decision_min |

These live as Zod `.min()` refinements inside the per-form schemas. The client shows an inline character counter below the textarea (turning amber at < 30% remaining, red at 0).

### 8.4 Warning vs Error Semantics

Unlike Reporting (where *all* validation is warning-only — Reporting §8.2), Safety has **both** modes:

- **Hard errors (block submit):** Zod structural errors, signature-order violations, bias guard #5 (Blame Fixation), missing Root-level cause at Phase 5 close, missing photo on a HIGH SOI finding.
- **Warnings (advise, don't block):** Bias guards #1–4, #6–8 (soft), WRH rest-hour non-compliance for SCM attendance (D-GAP-M11 — warn don't block), plausibility checks on incident severity × probability picker.

Warning styling reuses the Reporting warning-50 + warning-500 border (Reporting §8.3).

### 8.5 Warning-Only Fallback for Reporting-Like Fields

Any Safety form field that mirrors a Reporting field (e.g., vessel position MSC-MEPC.3 entry in the incident flow) inherits Reporting's warning-only rule for that specific field — the Safety form wraps it rather than duplicating the validator.

---

## 9. Permission-Gated Routing

### 9.1 Route Guards — `PermissionGate(SAF_F_*)`

Every top-level Safety route is wrapped in a `<PermissionGate>` keyed on the corresponding form ID. The sidebar also gates the parent Safety group — if the user has zero `SAF_F_*` IDs, the whole Safety group is hidden.

```tsx
// routes/safety/index.tsx

import { PermissionGate } from '@/components/shared/permission-gate';

export const safetyRoutes: RouteObject[] = [
  {
    path: '/safety',
    element: <SafetyModuleLayout />,
    children: [
      {
        path: 'incident',
        element: (
          <PermissionGate formId="SAF_F_001">
            <Outlet />
          </PermissionGate>
        ),
        children: [
          { index: true, element: <SafetyIncidentListPage /> },
          { path: 'new', element: <SafetyIncidentCreatePage /> },
          {
            path: ':id',
            element: <SafetyIncidentDetail />,
            children: [
              { path: 'phase-1', element: <SafetyIncidentPhase1 /> },
              { path: 'phase-2', element: <SafetyIncidentPhase2 /> },
              // ... phase-3 through phase-8
            ],
          },
        ],
      },
      {
        path: 'near-miss',
        element: (
          <PermissionGate formId="SAF_F_002">
            <Outlet />
          </PermissionGate>
        ),
        children: [ /* ... */ ],
      },
      {
        path: 'scm',
        element: (
          <PermissionGate formId="SAF_F_003">
            <Outlet />
          </PermissionGate>
        ),
        children: [ /* ... */ ],
      },
      {
        path: 'soi',
        element: (
          <PermissionGate formId="SAF_F_004">
            <Outlet />
          </PermissionGate>
        ),
        children: [ /* ... */ ],
      },
    ],
  },
];
```

### 9.2 Action Buttons — `ProcessGate(SAF_P_*)`

Every action button (Submit, Approve, Send Back, Attach Scan, Delete, Advance Phase, DPA Accept, FM Close-Red, Ad-Hoc Trigger) is wrapped in `<ProcessGate processId="SAF_P_...">`.

```tsx
// routes/safety/incident/[id]/phase-1.tsx

<ProcessGate processId="SAF_P_001">
  <Button onClick={handlePhase1Submit} className="min-h-[44px]">
    Submit Phase 1 — Scene Control
  </Button>
</ProcessGate>

<ProcessGate processId="SAF_P_004">
  <Button variant="primary" onClick={handleDpaAccept} className="min-h-[44px]">
    DPA Accept — Phase 7
  </Button>
</ProcessGate>
```

### 9.3 Permission ID Registry (Initial)

BACKEND_STRUCTURE.md §RBAC owns the full matrix. The frontend cites these IDs as string literals:

| ID | Meaning |
|----|---------|
| `SAF_F_001` | Incident form (list + detail + phases) |
| `SAF_F_002` | Near Miss form |
| `SAF_F_003` | SCM form (Regular + Ad-Hoc) |
| `SAF_F_004` | SOI form |
| `SAF_P_001` | Create draft / Submit Phase 1 |
| `SAF_P_002` | Phase 2–6 investigator work (Resources, Evidence, Facts, Causes, Findings) |
| `SAF_P_003` | Send back / loop-back Phase 5 → 3 |
| `SAF_P_004` | Phase 7 DPA Accept (GREEN / YELLOW) |
| `SAF_P_005` | Phase 7 FM Accept (RED) / Phase 8 closure |
| `SAF_P_006` | SOI approve closure (Master) |
| `SAF_P_007` | SCM finalize (Master) |
| `SAF_P_008` | Ad-Hoc SCM trigger (Master/CO host) |
| `SAF_P_009` | Near Miss triage Low/High |
| `SAF_P_010` | Lessons Learnt publish to Fleet Circular |

**Rule:** Never use a raw role string (`'DPA'`, `'MASTER'`) for gating. Use the permission ID. The role is available for *display* (breadcrumb, signature label) only — `useSafetyAuth().user?.role_name`.

### 9.4 Sidebar Group

```tsx
// within VimsSidebar (shared shell)

{useSafetyAuth().hasAnySafetyAccess() && (
  <SidebarGroup label="Safety">
    <PermissionGate formId="SAF_F_001"><SidebarItem to="/safety/incident" label="Incidents" /></PermissionGate>
    <PermissionGate formId="SAF_F_002"><SidebarItem to="/safety/near-miss" label="Near Miss" /></PermissionGate>
    <PermissionGate formId="SAF_F_003"><SidebarItem to="/safety/scm" label="Committee Meetings" /></PermissionGate>
    <PermissionGate formId="SAF_F_004"><SidebarItem to="/safety/soi" label="Officer Inspections" /></PermissionGate>
  </SidebarGroup>
)}
```

---

## 10. Testing

### 10.1 Inherited Conventions

Vitest v1.6 for unit/integration + React Testing Library v14 + Playwright v1.45 for E2E, per Reporting §10 / Inspection §10.

### 10.2 Mobile-First Test Mental Model

**Tablet portrait 768 × 1024 is the default test viewport for every Safety component.** Each Vitest suite opens with:

```ts
// tests/frontend/safety/setup.ts

import { beforeEach } from 'vitest';

beforeEach(() => {
  Object.defineProperty(window, 'innerWidth',  { writable: true, configurable: true, value: 768 });
  Object.defineProperty(window, 'innerHeight', { writable: true, configurable: true, value: 1024 });
  window.dispatchEvent(new Event('resize'));
});
```

A test that needs desktop dimensions calls `resizeTo(1280, 800)` explicitly and asserts the desktop-specific behavior. The *default* is tablet.

**Matching Playwright projects:**

```ts
// playwright.config.ts (safety subset)
projects: [
  { name: 'safety-tablet-portrait',  use: { viewport: { width: 768,  height: 1024 }, hasTouch: true } },
  { name: 'safety-tablet-landscape', use: { viewport: { width: 1024, height: 768  }, hasTouch: true } },
  { name: 'safety-desktop',          use: { viewport: { width: 1280, height: 800  }                  } },
  { name: 'safety-phone-readonly',   use: { viewport: { width: 390,  height: 844  }, hasTouch: true } },
];
```

### 10.3 Required Test Categories per Component

Every component in `components/safety/**` needs at least:

- **Render test** — renders without crashing at tablet portrait.
- **Accessibility test** — `axe-core` v4.9 passes; no WCAG 2.1 AA violations (D-GAP-M35).
- **Permission test** — renders correctly when required `SAF_F_*` / `SAF_P_*` ID is absent (should be empty or disabled).
- **State transition test** — if the component drives a phase transition, test happy-path + gate-failure + loop-back.

### 10.4 Anonymity Boundary Test Cases

Per **D-GAP-J1**, `SafetyAnonymityBadge` and `SafetyNearMissDetail` have mandatory test cases:

```ts
// tests/frontend/safety/near-miss/anonymity.test.tsx

describe('Near Miss reporter anonymity (D-GAP-J1)', () => {
  it('masks reporter name for Master viewer', () => { /* assert EyeOff + "Anonymous Reporter" */ });
  it('masks reporter name for HOD viewer',    () => { /* assert EyeOff */ });
  it('masks reporter name for SO viewer',     () => { /* SO != DPA/FM */ });
  it('reveals reporter name for DPA viewer',  () => { /* assert Eye + full name */ });
  it('reveals reporter name for FM viewer',   () => { /* assert Eye + full name */ });
  it('reveals reporter name for self-view',   () => { /* reporter viewing own report */ });
  it('renders Anonymous Reporter literally in PDF fallback for non-DPA/FM', () => { /* ... */ });
  it('masks aria-label so screen readers announce masking, not the name', () => { /* ... */ });
  it('does NOT mask Master signature even in masked view', () => { /* §9.3 scope rule */ });
  it('does NOT mask crew names in causal narrative text', () => { /* §9.3 scope rule */ });
});
```

A failing anonymity test blocks merge. An `@anonymity-boundary` tag on the Vitest suite routes it to the required-checks pipeline.

### 10.5 Phase-Transition E2E Tests

Each phase transition (1→2, 2→3, 3→4, 4→5, 5→6, 5↔3 loop-back, 6→7, 7→8) has a Playwright scenario that:

1. Seeds the database with a fixture incident at phase N.
2. Logs in as the role with `SAF_P_00X` required to advance.
3. Asserts the gate validator fails → fixes the gap → asserts advance succeeds → asserts `vims_safety_incident_phase_log` row created.

### 10.6 Bias-Guard Hard-Block Tests

`SafetyBiasGuardChecklist` has a dedicated test for guard #5 Blame-Fixation hard-block behavior:

- Pre-condition: all root causes = Personal Factors, no Lack-of-Control entry.
- Action: click Submit Phase 6.
- Assertion: Modal opens (DESIGN_SYSTEM §10.4), Phase transition does NOT fire, mutation is NOT called.
- Follow-up: DPA override with reason → modal closes, mutation fires with `dpa_override_reason` in body.

---

## 11. Rules Summary (Developer Checklist)

When writing any component, hook, or screen in `src/{routes,components,hooks,stores,schemas,api,types}/safety/**`:

1. **Naming:** PascalCase `Safety*` export; file kebab-case; hook `useSafety*`; store `safety*Store` (devtools name).
2. **Location:** Under the correct `safety/` subfolder (§1.2). No cross-module writes.
3. **Inheritance:** No new design tokens (DESIGN_SYSTEM rule); no new state management libraries; no new form libraries.
4. **Tablet first:** Start CSS at `md` (768px); desktop overrides are additive. Read-only on phone.
5. **44 × 44 px hit targets** on every interactive element.
6. **Permission-gate** every route (`SAF_F_*`) and every action button (`SAF_P_*`). Never gate by raw role string.
7. **Schema version** stamped on every Incident phase form; historical records grandfathered.
8. **30-second auto-save** to IndexedDB on every Safety form (D-GAP-F1).
9. **No optimistic update** on signatures, phase transitions, closures, or anonymity changes.
10. **No scan upload** anywhere in SOI. Paper stays in the SMS filing system (D-GAP-E4).
11. **Anonymity mask for Near Miss reporter** wherever the reporter field renders for a non-DPA/FM viewer (D-GAP-J1).
12. **WCAG 2.1 AA** — axe-core passes; color is never the only channel (D-GAP-M35).
13. **Test at tablet portrait by default**; desktop tests are explicit opt-in (§10.2).
14. **Bare `safety_*` table names never appear in frontend code** — backend API paths are under `/api/safety/*`, table names are a server concern.
15. **"SOI Compliance %"** (D-GAP-DESIGN-01) — literal string, never "Inspection Compliance %".
16. **Role persists, person may change** (D-GAP-A3/A4). No `Acting-*` concepts in the UI, no deputy-chain logic.

---

## 12. Document References

| Document | Relationship |
|----------|--------------|
| `VIMS-Reporting-Module/FRONTEND_GUIDELINES.md` v1.0 | **Parent** — architecture, state management, naming inherited verbatim |
| `VIMS DOCS/FRONTEND_GUIDELINES.md` v1.1 | **Grandparent** — React/TypeScript project structure, offline patterns |
| `VIMS-Safety-Module/DESIGN_SYSTEM.md` v1.0 | Safety visual tokens — cited throughout this doc by section (§3, §5, §7, §10, §11) |
| `VIMS-Safety-Module/PRD.md` | Feature requirements — `FEAT-SAF-*` IDs each component implements |
| `VIMS-Safety-Module/BACKEND_STRUCTURE.md` | API contracts (`/api/safety/*`) that these hooks call |
| `VIMS-Safety-Module/VALIDATION_RULES.md` | Hard-error vs warning matrix — referenced in §8.3–§8.4 |
| `VIMS-Safety-Module/APP_FLOW.md` | Route-level journeys + role permission matrix |
| `VIMS-SAFETY-MODULE-SSOT.md` §6 | Source of decision IDs cited throughout (D-DNV-*, D-GAP-*, D-SOI-*, D-EDGE-*, D-PDF-*) |
| `ssot_auth_specific.md` | Dual identity + `form_ids` / `process_ids` — origin of §9 gating pattern |

---

**Document Control:**
- Created: 2026-04-17
- Author: System Generated (Safety Module Docsuite — Wave 2)
- Parent Guidelines Version: Reporting v1.0 (2026-04-06) → Inspection v1.1 (2026-03-26)
- Safety Extension Version: 1.0
- Session 5 Close: 2026-04-17 (159 decisions locked)
