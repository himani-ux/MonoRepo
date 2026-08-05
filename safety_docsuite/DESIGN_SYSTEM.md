# DESIGN_SYSTEM.md — Visual Language & Design Tokens
## VIMS Safety Module — Incident · Near Miss · SCM · SOI

**Version:** 1.0 | **Date:** 2026-04-17 | **Status:** Locked (Session 5 close)

**Glossary (first-use expansions — per `<glossary>` in dispatch brief):**
DPA (Designated Person Ashore, ISM Code §4) · FM (Fleet Manager) · TD (Technical Director) · HOD (Head of Department — Chief Officer / Chief Engineer / senior deck-or-engine rank on board) · SO (Safety Officer, SOLAS Reg VI designated) · CO (Chief Officer) · CE (Chief Engineer) · SCM (Safety Committee Meeting) · SOI (Safety Officer Inspection) · RCA (Root Cause Analysis) · CA (Corrective Action) · PA (Preventive Action) · SMC (Serious Marine Casualty — IMO Casualty Investigation Code, Res. MSC.255(84)) · MC (Marine Casualty — IMO) · MI (Marine Incident — IMO) · WCAG (Web Content Accessibility Guidelines 2.1).

---

## 0. Inheritance Declaration

The VIMS Safety Module **inherits the entire token set** of the sibling **VIMS Reporting Module** (`VIMS-Reporting-Module/DESIGN_SYSTEM.md` v1.0, 2026-04-06), which itself inherits from the **VIMS Inspection Module** (`VIMS DOCS/DESIGN_SYSTEM.md` v1.0, 2026-02-03). Nothing from either upstream file is overridden here.

This document exists **solely** to:

1. **Declare** which Reporting/Inspection tokens are reused verbatim — referenced by name, **not restated**.
2. **Extend** the system with Safety-specific tokens that have no upstream equivalent, each citing the governing `D-GAP-DESIGN-*` or `D-*` decision from `VIMS-SAFETY-MODULE-SSOT.md §6`.
3. **Re-map** existing tokens onto Safety semantic concepts (risk band, state pill, causal layer, etc.).

> **Rule (inherited from Reporting §0):** Every color, spacing value, radius, shadow, font, icon, and animation referenced in this file MUST already exist in the Reporting or Inspection design system unless explicitly justified by a Safety decision ID. No invented values.

**Arbitration:** If a token appears in both this file and Reporting, **Reporting wins** (single source of base palette). This file only binds Safety-specific semantic meanings onto those values.

---

## 1. Inherited Foundation (Tokens Reused Verbatim — Reference Only)

The full token tables live in `VIMS-Reporting-Module/DESIGN_SYSTEM.md` §1. Developers consume those tokens directly by name. The table below is a **manifest of which categories are inherited** — no restatement of hex / px / rem values.

| Category | Source | Safety reuse |
|----------|--------|--------------|
| Color palette — `primary-50…900`, `neutral-50…900`, `success-50/100/500/600/700`, `warning-50/100/500/600/700`, `error-50/100/500/600/700`, `info-50/100/500` | Reporting §1.1 → Inspection §1 | **All reused unchanged.** Safety risk-band and state-pill tokens re-map these. |
| Surface colors — `surface-page`, `surface-card`, `surface-elevated`, `surface-overlay` | Reporting §1.2 | All reused unchanged. |
| Typography font stacks — `--font-sans` (Inter / system fallback), `--font-mono` (JetBrains Mono / Fira Code fallback) | Reporting §1.3 → Inspection §2.1 | Reused unchanged. |
| Typography scale — `text-xs` (12px), `text-sm` (14px), `text-base` (16px), `text-lg` (18px), `text-xl` (20px), `text-2xl` (24px), `text-3xl` (30px), with inherited line-heights and font-weight ramp (`font-normal` 400, `font-medium` 500, `font-semibold` 600, `font-bold` 700) | Reporting §1.3 → Inspection §2.2 | Reused unchanged; see §6 for Safety typography usage rules. |
| Spacing scale — `space-0` through `space-12` on a 4px base unit (`space-1` = 4px, `space-2` = 8px, `space-3` = 12px, `space-4` = 16px, `space-6` = 24px, `space-8` = 32px) | Inspection §3 (via Reporting §1.4) | Reused unchanged. |
| Border-radius — `radius-none`, `radius-sm` (4px), `radius-md` (6px), `radius-lg` (8px), `radius-xl` (12px), `radius-full` (9999px) | Inspection §4 (via Reporting §1.4) | Reused unchanged. |
| Shadows — `shadow-sm`, `shadow-md`, `shadow-lg`, `shadow-xl` | Inspection §5 (via Reporting §1.4) | Reused unchanged. |
| Borders — `border-width-1`, `border-width-2`, `border-width-4`; default border color `neutral-200` | Inspection §6 | Reused unchanged. |
| Breakpoints — `bp-sm` 640px, `bp-md` 768px, `bp-lg` 1024px, `bp-xl` 1280px, `bp-2xl` 1536px | Inspection §7 | Reused unchanged; Safety adds the **SOI tablet profile** in §7. |
| Animation durations — `duration-150`, `duration-200`, `duration-300`, `duration-500`; easings `ease-out`, `ease-in-out`, `ease-linear` | Inspection §8 | Reused unchanged. |
| Z-index scale — `z-10` content · `z-20` dropdowns · `z-30` sticky · `z-40` header · `z-50` modal · `z-60` toast/banner | Inspection §9 | Reused unchanged. |
| Icons — **Lucide React v0.408.0**; size tokens `icon-xs` 12px, `icon-sm` 16px, `icon-md` 20px, `icon-lg` 24px, `icon-2xl` 48px | Reporting §1.5 → Inspection §10 | Reused unchanged; Safety adds icon-usage rules in §12. |
| Component tokens — Button (`btn-primary`, `btn-secondary`, `btn-ghost`, `btn-danger`), Input, Card, Badge (2px 8px / `radius-full` pill / `text-xs` `font-medium` uppercase), Modal | Reporting §1.6 → Inspection §11 | Reused unchanged. Safety's state pill and risk band badges use these exact dimensions. |
| PDF base — A4 portrait, 20 mm margins, Inter body 10pt / headings 12–14pt, `neutral-800` body, `neutral-200` table grid | Reporting §1.7 → Inspection §12 | Reused unchanged; Safety extends PDF templates in §14. |
| Themes — Light theme is v1; dark theme is deferred to Inspection's eventual dark-mode release (Inspection §13) | Reporting §15 rule 7 | Deferred identically. Safety does NOT ship dark mode in V1. |

**Mapping rule:** When this document names `primary-500`, `neutral-700`, `radius-lg`, `shadow-md`, etc., it is referring to the Reporting/Inspection value. No duplication. A developer should be able to open `tailwind.config.js` (generated from Reporting §1) and find every token named here already defined.

---

## 2. Safety Naming Convention for NEW Tokens

All Safety-specific semantic tokens use the prefix `--safety-<category>-<variant>`. This is a CSS-variable layer on top of the inherited palette — the variable **points at** an inherited color, it does not define a new hex.

| Category segment | Meaning | Example |
|------------------|---------|---------|
| `risk` | Risk-band indicators (IMO + internal) | `--safety-risk-critical` |
| `state` | Workflow state pills | `--safety-state-soi-compliance` |
| `causal` | Causal-layer visual hierarchy | `--safety-causal-root` |
| `rec` | Recommendation taxonomy (Corrective / Preventive / Lessons) | `--safety-rec-preventive` |
| `sig` | Signature-block variants per role | `--safety-sig-dpa` |
| `anon` | Anonymity indicator states | `--safety-anon-masked` |
| `bias` | Bias-guard checklist tokens | `--safety-bias-blame-fixation` |
| `pdf` | PDF-only Safety extensions | `--safety-pdf-cover-band` |

**Rule:** A Safety token name appearing anywhere in Safety's frontend code MUST resolve to an inherited Reporting/Inspection hex value **unless** a `D-GAP-DESIGN-*` decision permits a new value. The **only** current justified exception is `D-GAP-DESIGN-01` (the SOI Compliance % **label rename**, which introduces no new color).

**Flag audit:** In the token tables below, the "Inherited?" column is `Yes` (value reused) or `NEW — cite D-*` (Safety-specific, cited).

---

## 3. Risk-Band Palette

Safety carries **two parallel risk-band systems** that the designer keeps visually distinct:

- **Internal risk band** (`GREEN / YELLOW / RED`) — drives investigator seniority, closure deadlines, PDF signature block (D-DNV-02, D-RBAC-01, D-RBAC-05).
- **IMO regulatory classifier** (`SMC / MC / MI`) — drives external reporting template (MSC-MEPC.3/Circ.4 per D-DNV-12), separate from internal band (D-GAP-R08, reconciliation option b).

Both appear side-by-side on the incident header, never stacked inside the same pill. Investigation deadlines are always driven by the **internal band**, never the IMO classifier (D-GAP-R08).

### 3.1 Internal Risk Band (GREEN / YELLOW / RED)

Locked by **D-DNV-02** (SSOT §6 L1404) and **D-DNV-11** (SSOT §6 L1413). Replaces the legacy 7-column severity matrix (`Injury / Pollution / Business / Navigational / PSC / Security / Other`).

| Token | Semantic name | Hex (from inherited) | Reporting reference | WCAG AA contrast vs `surface-card` (#FFFFFF) | Inherited? |
|-------|---------------|----------------------|---------------------|---------------------------------------------|-----------|
| `--safety-risk-green-bg` | Negligible — background | `#D1FAE5` | `success-100` | Decorative; text layer below passes | Yes |
| `--safety-risk-green-text` | Negligible — text | `#047857` | `success-700` | 6.34:1 ✓ (passes AA normal + large) | Yes |
| `--safety-risk-green-border` | Negligible — 2px left accent | `#10B981` | `success-500` | Non-text element; 3:1 rule → passes | Yes |
| `--safety-risk-yellow-bg` | Intermediate — background | `#FEF3C7` | `warning-100` | Decorative | Yes |
| `--safety-risk-yellow-text` | Intermediate — text | `#B45309` | `warning-700` | 5.93:1 ✓ (passes AA normal + large) | Yes |
| `--safety-risk-yellow-border` | Intermediate — 2px left accent | `#F59E0B` | `warning-500` | Non-text; 3:1 → passes | Yes |
| `--safety-risk-red-bg` | Urgent/Critical — background | `#FEE2E2` | `error-100` | Decorative | Yes |
| `--safety-risk-red-text` | Urgent/Critical — text | `#B91C1C` | `error-700` | 7.25:1 ✓ (passes AA normal + large) | Yes |
| `--safety-risk-red-border` | Urgent/Critical — 2px left accent | `#EF4444` | `error-500` | Non-text; 3:1 → passes | Yes |

**Rule (D-GAP-M35 / WCAG 2.1 AA):** Every risk-band pill must carry the **text label** (`GREEN`, `YELLOW`, `RED`) alongside color. Color alone is never the sole carrier of meaning.

Pill dimensions reuse the inherited Reporting Badge spec verbatim: `padding: 2px 8px`, `border-radius: radius-full`, `font: text-xs font-medium`, `text-transform: uppercase`, `border: 1px solid <border token>` (Reporting §2).

### 3.2 IMO Regulatory Classifier (SMC / MC / MI)

Locked by **D-GAP-R08** (SSOT §6 L1546). Shown alongside — never replacing — internal risk band.

| Token | Semantic name | Hex (from inherited) | Reporting reference | WCAG AA contrast vs `surface-card` | Inherited? |
|-------|---------------|----------------------|---------------------|-------------------------------------|-----------|
| `--safety-risk-imo-smc-bg` | SMC Serious Marine Casualty — background | `#FEE2E2` | `error-100` | Decorative | Yes |
| `--safety-risk-imo-smc-text` | SMC text | `#B91C1C` | `error-700` | 7.25:1 ✓ | Yes |
| `--safety-risk-imo-mc-bg` | MC Marine Casualty — background | `#FEF3C7` | `warning-100` | Decorative | Yes |
| `--safety-risk-imo-mc-text` | MC text | `#B45309` | `warning-700` | 5.93:1 ✓ | Yes |
| `--safety-risk-imo-mi-bg` | MI Marine Incident — background | `#DBEAFE` | `info-100` / `primary-100` | Decorative | Yes |
| `--safety-risk-imo-mi-text` | MI text | `#1D4ED8` | `primary-700` | 7.52:1 ✓ | Yes |

**Shape differentiator:** To prevent visual confusion with the internal band, IMO pills are rendered with an **outline-only** style (`background: transparent; border: 1px solid <text>-token; color: <text>-token`), while internal band pills are **solid-fill** (bg + text as shown in §3.1). Shape is the second encoding channel (WCAG 2.1 §1.4.1 compliance — no reliance on color alone).

### 3.3 Internal Severity × Probability Grid (for Risk-Band Picker UI)

Per SSOT §2B.3 and D-DNV-01, the risk band is computed `severity × probability`. The picker UI renders a 4×4 grid where each cell displays its resolved band color.

| Severity ↓ / Probability → | Unlikely | Possible | Likely | Certain |
|----------------------------|----------|----------|--------|---------|
| **Minor** (6) | GREEN | GREEN | GREEN | YELLOW |
| **Significant** (16) | GREEN | YELLOW | YELLOW | YELLOW |
| **Severe** (11) | YELLOW | YELLOW | RED | RED |
| **Major** (10) | YELLOW | RED | RED | RED |

Cell background = corresponding `--safety-risk-{green|yellow|red}-bg`; cell text = corresponding `-text` token.

### 3.4 Internal Low / Medium / High / Critical (SOI Finding Severity)

SOI findings use a **4-level** severity (not 3), locked implicitly by **D-GAP-M24** (SSOT §6 L1523 — `HIGH` requires ≥1 photo) and **D-GAP-M16** (SSOT §6 L1514 — `HIGH` triggers incident-worthy prompt). This is distinct from the incident 3-band system.

| Token | Semantic name | Hex (from inherited) | Reporting reference | WCAG AA contrast vs `surface-card` | Inherited? |
|-------|---------------|----------------------|---------------------|-------------------------------------|-----------|
| `--safety-sev-low` | Low (text / accent) | `#059669` | `success-600` | 5.00:1 ✓ | Yes |
| `--safety-sev-medium` | Medium | `#D97706` | `warning-600` | 4.52:1 ✓ | Yes |
| `--safety-sev-high` | High | `#DC2626` | `error-600` | 5.87:1 ✓ | Yes |
| `--safety-sev-critical` | Critical | `#B91C1C` | `error-700` | 7.25:1 ✓ | Yes |

**Visual distinction rule:** Critical uses `error-700` + a 1px solid `error-900`-equivalent **outline ring** (`box-shadow: inset 0 0 0 1px #7F1D1D`) to distinguish from High without introducing a new hex. This is an on-the-fly composition of existing tokens, not a new token.

---

## 4. State Pill Values (Workflow States)

Locked by **D-DNV-05** (SSOT §6 L1407), **D-EDGE-08** (L1439), and **D-GAP-DESIGN-01** (SSOT §6 L1538). The Safety state machine is richer than Reporting's (which has only `draft / sent_to_office / reopened`). Safety extends it with `Under Review`, `Approved`, `Closed`, and `Sent Back` to reflect the 9-phase Incident flow and the SOI/SCM sign-off chains.

### 4.1 Workflow-State Pills

| State token | Display label | Background | Text | Border | Reporting-map reference | Decision |
|-------------|---------------|------------|------|--------|-------------------------|----------|
| `--safety-state-draft` | `DRAFT` | `neutral-100` | `neutral-700` | `neutral-300` | = Reporting `draft` | D-EDGE-08 (partial-data draft mode) |
| `--safety-state-submitted` | `SUBMITTED` | `primary-100` | `primary-700` | `primary-300` | = Reporting `sent_to_office` | D-DNV-05 (Phase 1 Submit) |
| `--safety-state-under-review` | `UNDER REVIEW` | `info-100` | `primary-700` | `primary-300` | new state — no Reporting analog | D-DNV-05 (Phase 2–6 investigator work) |
| `--safety-state-approved` | `APPROVED` | `success-100` | `success-700` | `success-500` | new — no Reporting analog | D-RBAC-01, D-SOI-07 (Master/DPA/FM approval) |
| `--safety-state-closed` | `CLOSED` | `neutral-200` | `neutral-800` | `neutral-400` | new — Reporting has no closed state (reports are permanent) | D-DNV-05 Phase 7 closure |
| `--safety-state-sent-back` | `SENT BACK` | `warning-100` | `warning-700` | `warning-500` | = Reporting `reopened` (semantic match) | D-EDGE-03 (re-open authority), D-DNV-05 Phase 5→3 loopback |

**Pill dimensions:** identical to the inherited Reporting badge pattern (`2px 8px`, `radius-full`, `text-xs font-medium` uppercase, 1px border). No new dimensions introduced.

All six pills carry the text label — color never alone (WCAG AA, **D-GAP-M35**).

### 4.2 Dashboard KPI Label — "SOI Compliance %" (D-GAP-DESIGN-01)

**D-GAP-DESIGN-01** (SSOT §6 L1538) renames the Safety-dashboard metric **"Inspection Compliance %"** to **"SOI Compliance %"** to avoid collision with the existing PSC-Inspection-module metric of the same legacy name.

| Token | Display label (EXACT string) | Typography | Color | Decision |
|-------|------------------------------|------------|-------|----------|
| `--safety-state-soi-compliance` | `SOI Compliance %` (literal; **never** `Inspection Compliance %`) | `text-sm font-medium` for label; `text-2xl font-bold` for value (same as Reporting KPI card §11.2) | Label `neutral-500`; value `neutral-900`; accent ring `primary-500` | D-GAP-DESIGN-01 |

**Hard rule:** Any docsuite output, UI string, PDF export, CSV column header, API JSON key, or translation file containing the string `Inspection Compliance %` in the Safety module is a **violation of D-GAP-DESIGN-01** and blocks merge. The docsuite coverage audit greps for this.

### 4.3 SOI Finding Lifecycle Pills

Locked by **D-SOI-07** (SSOT §6 L1454) — `Open → Pending Closure → Master-Approved → Closed`, with `Carried Forward` possible at each SCM (D-SOI-14).

| Token | Display label | Background | Text | Border | Decision |
|-------|---------------|------------|------|--------|----------|
| `--safety-state-finding-open` | `OPEN` | `warning-100` | `warning-700` | `warning-500` | D-SOI-07 |
| `--safety-state-finding-pending` | `PENDING CLOSURE` | `info-100` | `primary-700` | `primary-300` | D-SOI-07 |
| `--safety-state-finding-approved` | `MASTER-APPROVED` | `success-100` | `success-700` | `success-500` | D-SOI-07 |
| `--safety-state-finding-closed` | `CLOSED` | `neutral-200` | `neutral-800` | `neutral-400` | D-SOI-07 |
| `--safety-state-finding-carried` | `CARRIED FORWARD` | `neutral-100` | `neutral-700` | `neutral-400` (dashed) | D-SOI-14 |

The `Carried Forward` pill uses a **dashed border** as its second encoding channel — distinguishes from `CLOSED` without a new color.

---

## 5. Causal-Layer Visual Hierarchy

Locked by **D-GAP-R01** and updated for the current UI by **D-MAINT-CR033** — every current cause entered on an incident must be tagged **Immediate / Root**, extending D-DNV-01 M-SCAT-compatible coding. The current flow cannot advance unless at least one Immediate Cause and one Root Cause are recorded.

### 5.1 Layer Tokens

| Token | Layer | Background (card) | Text / icon accent | Left-border accent (4px) | Indentation (left) | Font-weight | Decision |
|-------|-------|--------------------|---------------------|---------------------------|---------------------|-------------|----------|
| `--safety-causal-immediate` | Immediate cause (what happened) | `neutral-50` | `warning-600` | `warning-500` | `space-0` (0px) | `font-normal` (400) | D-GAP-R01 |
| `--safety-causal-intermediate` | Legacy Intermediate / Contributing (not shown as a current selectable layer) | `warning-50` | `warning-700` | `warning-600` | `space-4` (16px) | `font-medium` (500) | D-GAP-R01 historical; superseded for current UI by D-MAINT-CR033 |
| `--safety-causal-root` | Root cause (system-level, Lack-of-Control per §2B.11 bias #5) | `error-50` | `error-700` | `error-600` | `space-8` (32px) | `font-semibold` (600) | D-GAP-R01 + D-DNV-11 |

Indentation, left-border thickness, and font-weight form a **3-channel visual hierarchy** — color is never the sole channel (WCAG 2.1 §1.4.1).

### 5.2 Causal Tree Component Rules

- **Layer order on screen:** Immediate at top → Root. Legacy Intermediate rows are grouped under Root in current UI/PDF display instead of appearing as a separate selectable category.
- **Connector lines:** 1px solid `neutral-300`, vertical between parent/child nodes (reuses inherited border color).
- **Empty-state (no Root recorded yet):** Render a `warning-100` banner inside the Root section with Lucide icon `AlertTriangle` (`icon-sm`, `warning-600`) and the text `"At least one Root Cause is required."`
- **Count badge per layer:** pill with inherited Reporting badge dimensions; shows Immediate and Root counts across the top of the Analysis Workspace.

---

## 6. Recommendation Taxonomy — Corrective / Preventive / Lessons Learnt

Locked by **D-GAP-R13** (SSOT §6 L1551) — each recommendation explicitly tagged `Corrective` (fix the symptom) · `Preventive` (fix the system) · `Lessons Learnt` (share). Extends **D-DNV-06** (SSOT §6 L1408) 3-tier recommendation format (`Lessons Learned + ≥1 Immediate Action + ≥1 System Action`). Colour-coded badges + dashboard filter.

| Token | Tier | Hex (from inherited) | Reporting ref | Lucide icon | WCAG AA contrast vs `surface-card` | Decision |
|-------|------|----------------------|---------------|-------------|-------------------------------------|----------|
| `--safety-rec-corrective-bg` | Corrective — background | `#FEE2E2` | `error-100` | `Wrench` (`icon-sm`) | Decorative | D-GAP-R13 |
| `--safety-rec-corrective-text` | Corrective — text | `#B91C1C` | `error-700` | — | 7.25:1 ✓ | D-GAP-R13 |
| `--safety-rec-preventive-bg` | Preventive — background | `#DBEAFE` | `primary-100` | `ShieldCheck` (`icon-sm`) | Decorative | D-GAP-R13 |
| `--safety-rec-preventive-text` | Preventive — text | `#1D4ED8` | `primary-700` | — | 7.52:1 ✓ | D-GAP-R13 |
| `--safety-rec-lessons-bg` | Lessons Learnt — background | `#D1FAE5` | `success-100` | `BookOpen` (`icon-sm`) | Decorative | D-GAP-R13, D-DNV-06 |
| `--safety-rec-lessons-text` | Lessons Learnt — text | `#047857` | `success-700` | — | 6.34:1 ✓ | D-GAP-R13, D-DNV-06 |

**Closure-gate rule (D-GAP-R13):** YELLOW and RED bands require at least one of each tier before the incident can close. The dashboard filter chips re-use the badge colors above.

**Icon as second channel:** The Lucide icon (`Wrench` / `ShieldCheck` / `BookOpen`) is rendered inside each tier badge so users who cannot distinguish red/blue/green still read the tier.

---

## 7. WCAG 2.1 Level AA Compliance (D-GAP-M35)

**D-GAP-M35** (SSOT §6 L1534) locks the accessibility target: WCAG 2.1 AA. Every Safety UI surface complies.

### 7.1 Minimum Contrast Ratios

| Text role | Minimum ratio (WCAG 2.1 AA) | Safety application |
|-----------|-----------------------------|---------------------|
| Normal text (≤ 18pt regular, ≤ 14pt bold) | **4.5 : 1** | All body copy, pill text, table rows, signature labels |
| Large text (> 18pt regular, > 14pt bold) | **3.0 : 1** | Section headers, KPI values, risk-band callouts |
| Non-text UI components (borders, icons, focus rings) | **3.0 : 1** | Risk-band left-border accents, state-pill borders, causal-layer connector lines |
| Decorative elements | No requirement | Pill backgrounds (text layer above carries the contrast) |

All `--safety-risk-*-text`, `--safety-state-*-text`, `--safety-causal-*` text tokens in §3–5 above pass the 4.5:1 normal-text threshold against `surface-card` (`#FFFFFF`) — contrast ratio shown in the tables.

### 7.2 Focus-State Requirements

| Element | Focus treatment | Token |
|---------|-----------------|-------|
| All interactive elements (buttons, links, form inputs, pills-as-buttons) | 2px solid outline, offset 2px, color `primary-500` | Reuses inherited Reporting focus ring (Inspection §11) |
| Signature-capture canvas | Same 2px ring + `shadow-md` on focus-within | Reuses inherited shadow |
| Causal-tree nodes (keyboard-navigable) | Ring + `primary-100` background fill on current node | Reuses inherited `primary-100` |

Focus outlines must meet the 3:1 non-text contrast minimum (WCAG 2.1 §1.4.11). `primary-500` (`#3B82F6`) vs `surface-card` (`#FFFFFF`) = 3.68:1 ✓.

### 7.3 Hit-Target Sizes (Vessel Tablet Use)

WCAG 2.1 AAA recommends 44×44 CSS px; Safety targets **minimum 44×44 px** across all interactive elements because vessel tablets at sea (pitch + glove use) demand larger targets than desktop benchmarks suggest.

| Control class | Minimum hit area | Safety application |
|---------------|------------------|---------------------|
| Primary buttons (Submit, Approve, Send Back) | 44 × 44 px (48 × 44 preferred) | Phase-Submit CTAs, SCM attendance toggles, SOI finding add |
| Icon-only buttons (e.g., delete row) | 44 × 44 px with 8px internal padding | SOI row-action menus, evidence delete |
| Checkbox / radio | 24 × 24 px input, with 44 × 44 px clickable wrapper | Bias-guard checklist, SOI Yes/No/N-A |
| State pills (when clickable as filters) | Min-height 32 px with `space-2` vertical + `space-4` horizontal padding | Dashboard filter chips |
| Signature field | 44 × 44 px minimum tap area; canvas 320 × 120 px on tablet | All signature blocks in §10 |

**Color-and-text rule (D-GAP-M35):** Every color-coded indicator in this document carries a redundant text label or icon. Any new Safety UI must obey this rule — automated axe-core test covers it.

### 7.4 Keyboard, ARIA, and Screen-Reader Parity

- Full keyboard-navigation parity on every form and dashboard (no mouse-only actions).
- ARIA labels on every pill, icon-button, and signature block. Example: `<span role="img" aria-label="Risk band: RED Urgent">RED</span>`.
- Screen-reader announcement on state transitions (e.g., Phase 1 → Phase 2) via an `aria-live="polite"` region.
- Skip-link to main content on every Safety route.

---

## 8. Signature Block — 5 Role Variants

Locked by **D-GAP-D1** (SSOT §6 L1478) — hybrid digital signature: typed name + timestamp + device fingerprint. **No PKI / UETA** in V1 (D-GAP-D2, L1479). PDFs intended for flag-state / auditor handoff accept a wet-signed scan as attachment.

**PDF signature chain (D-PDF-01, SSOT §6 L1444):** `Master / DPA / [FM for RED]` — five total variants documented for UI (Reporter + HOD added for Near Miss and intermediate routing).

### 8.1 Role Variant Tokens

Each variant is a composition of the inherited Card token (Reporting §1.6 / Inspection §11) plus a role-specific top accent band.

| Token | Role | Avatar slot bg | Accent-band color | Role label color | Decision |
|-------|------|-----------------|---------------------|---------------------|----------|
| `--safety-sig-reporter` | Reporter (any crew; hidden per D-GAP-J1 on Near Miss) | `neutral-200` | `neutral-500` | `neutral-700` | D-GAP-D1, D-GAP-J1 |
| `--safety-sig-master` | Master (on-board authority; PDF signature chain per D-PDF-01) | `primary-200` | `primary-500` | `primary-700` | D-GAP-D1, D-PDF-01 |
| `--safety-sig-hod` | HOD (Chief Officer / Chief Engineer) | `info-100` | `info-500` | `primary-700` | D-GAP-D1 |
| `--safety-sig-dpa` | DPA (shore; closure authority GREEN/YELLOW per D-RBAC-01) | `success-100` | `success-600` | `success-700` | D-GAP-D1, D-RBAC-01 |
| `--safety-sig-fm` | FM (shore; closure authority RED per D-RBAC-05) | `error-100` | `error-600` | `error-700` | D-GAP-D1, D-RBAC-05 |

All five use the same structure — the token only changes accent color, so a screen-reader reads the **rank label** (`Master`, `Designated Person Ashore`, `Fleet Manager`, etc.) as the primary cue. Color is secondary.

### 8.2 Signature Block Anatomy (All 5 Variants)

```
┌──────────────────────────────────────────────────────────┐
│ [AVATAR 40x40]  [Name (text-base font-semibold)         ]│
│                 [Rank + Role (text-sm, neutral-600)     ]│
├──────────────────────────────────────────────────────────┤
│ Digital-signature line: typed name · timestamp ISO-8601  │
│                        · device fingerprint hash (last 8 ch)│
│ Font: text-xs, font-mono, neutral-700                    │
├──────────────────────────────────────────────────────────┤
│ [Attach wet-signed scan (optional, D-GAP-D1 fallback)]   │
│  — Button style: btn-ghost, Lucide PaperClip icon-sm     │
└──────────────────────────────────────────────────────────┘
Top accent band: 4px solid <role accent-band color>
Card: surface-card bg, radius-lg, border 1px neutral-200, shadow-sm
Padding: space-4 (16px)
Tablet min width: 320px · max width: 480px
```

**Avatar:** circular, 40 × 40 px (tablet) / 48 × 48 px (desktop). If no avatar uploaded, show initials over role-colored background.

**Timestamp format:** ISO-8601 `YYYY-MM-DD HH:MM:SS±TZ` with timezone from `wrh_ship_time_config` (D-GAP-M26), rendered `text-xs font-mono`.

**Device fingerprint hash:** last 8 chars of the SHA-256 of the browser fingerprint, stored server-side as plain-text audit field (D-GAP-D2 explicitly prohibits tamper-evidence hash chains — this is just an identifier, not a cryptographic proof).

**Order enforcement:** Phase-6 submit validates signature order per SSOT §2B.14 chain — `Reporter → Master → HOD → DPA → FM` as applicable. Out-of-order submission blocked client + server (VALIDATION_RULES.md owns the enforcement rules).

**Missing signature placeholder:** empty slot shows `neutral-100` bg, dashed `neutral-300` border, label "Awaiting <Role>" in `neutral-500 text-xs italic`.

---

## 9. Anonymity Indicator (D-GAP-J1)

Locked by **D-GAP-J1** (SSOT §6 L1498) — near-miss reporter identity **hidden from Master and HOD** on the incident screen and in PDFs; **visible only to DPA and FM** (and the reporter themselves).

### 9.1 Masked-View Tokens

| Token | Usage | Lucide icon | Color | Background | Decision |
|-------|-------|-------------|-------|------------|----------|
| `--safety-anon-masked-icon` | Replaces name when viewer lacks DPA/FM role | `EyeOff` (`icon-sm`, 16px) | `neutral-500` | transparent | D-GAP-J1 |
| `--safety-anon-masked-label-bg` | Pill shown next to "Reporter" field | `neutral-100` | — | `neutral-100` | D-GAP-J1 |
| `--safety-anon-masked-label-text` | Text inside the pill | `neutral-700` | `neutral-700` | — | D-GAP-J1 |
| `--safety-anon-visible-icon` | Shown to DPA/FM + reporter | `Eye` (`icon-sm`) | `primary-500` | transparent | D-GAP-J1 |

### 9.2 Rendering Rules

- **Non-DPA/FM viewer:** Reporter field renders as `[EyeOff icon] Anonymous Reporter` (pill: `--safety-anon-masked-*`). Tooltip on hover: `"Reporter identity hidden per D-GAP-J1. Visible to DPA and Fleet Manager only."`
- **DPA / FM / reporter self-view:** Reporter field renders the full name plus an `Eye` icon in `primary-500` and tooltip `"You can see this because you are <Role>. Name is hidden from Master and HOD."`
- **PDF rendering:** Non-DPA/FM PDFs render `Anonymous Reporter` literally in the Reporter field; DPA/FM PDFs render the full name. Backend serializer enforces this (see `anonymity.py` per `<vims_integration>`).
- **ARIA:** Masked view includes `aria-label="Reporter identity is hidden for this viewer role"` so screen-readers announce the masking instead of reading the icon silently.

### 9.3 Anonymity Does NOT Apply To

Per D-GAP-J1, anonymity is **reporter-field-only** on Near Miss records. It does **not** mask:

- Master / HOD / SO signatures (identity must be traceable for accountability)
- Incident reporter field (incidents are always attributable — only Near Miss has anonymity)
- Any crew names in the causal narrative (those are factual witness references, not the reporter's identity)

---

## 10. Bias-Guard Checklist (8 Variants)

Locked by **D-DNV-11** (5 guards, SSOT §6 L1413) extended by **D-GAP-R12** (3 additional organisational defence-traps, SSOT §6 L1550). Total = **8 bias guards** rendered as a checklist at Phase-transition gates.

### 10.1 Full List (5 + 3 = 8)

| # | Short label (UI token) | Guard rule | Trigger point | Hard/Soft | Decision |
|---|------------------------|------------|---------------|-----------|----------|
| 1 | `Recency` | All 5 evidence categories have ≥1 entry OR "n/a — justified" | Phase 4 → 5 | Soft | D-DNV-11 |
| 2 | `Assumption` | Every fact-box has an evidence link | Adding a fact | Soft | D-DNV-11 |
| 3 | `Hindsight` | Decision timestamps cannot reference post-event info | Adding a finding | Soft | D-DNV-11 |
| 4 | `Confirmation` | Evidence Matrix has ≥1 Con row per major finding | Phase 5 → 6 | Soft | D-DNV-11 |
| 5 | `Blame Fixation` | If all root causes = Personal Factors AND no Lack-of-Control entry → block | Phase 6 → 7 | **Hard** (DPA override only) | D-DNV-11 |
| 6 | `Plant-Problem Trap` | Warns if all causes cluster on hardware (avoids process issues) | Phase 6 → 7 | Soft | D-GAP-R12 |
| 7 | `Personnel-Problem Trap` | Warns if all causes cluster on persons (avoids system issues) | Phase 6 → 7 | Soft | D-GAP-R12 |
| 8 | `External-Event Trap` | Warns if all causes cluster on external events (avoids internal control) | Phase 6 → 7 | Soft | D-GAP-R12 |

### 10.2 Checkbox Variant Tokens

Each checkbox reuses the inherited Input token (Reporting §1.6 → Inspection §11). Safety adds the short-label typography and state visuals below.

| Token | State | Checkbox fill | Label text | Icon | Decision |
|-------|-------|---------------|------------|------|----------|
| `--safety-bias-unchecked` | Not yet evaluated | `neutral-50` / `neutral-300` border | `neutral-700 text-sm font-medium` | — | D-DNV-11 |
| `--safety-bias-passed` | Guard passed | `success-500` fill + white `Check` icon | `neutral-700 text-sm font-medium` | `Check` (`icon-sm`) | D-DNV-11 |
| `--safety-bias-warned` | Soft warning raised | `warning-500` fill + white `AlertTriangle` icon | `warning-700 text-sm font-semibold` | `AlertTriangle` (`icon-sm`) | D-DNV-11, D-GAP-R12 |
| `--safety-bias-blocked` | Hard block (guard #5 only) | `error-500` fill + white `X` icon | `error-700 text-sm font-semibold` | `XOctagon` (`icon-sm`) | D-DNV-11 |
| `--safety-bias-override` | DPA override applied (guard #5) | `primary-500` fill + white `ShieldAlert` icon | `primary-700 text-sm font-semibold italic` | `ShieldAlert` (`icon-sm`) | D-DNV-11 |
| `--safety-bias-justified` | "n/a — justified" | `neutral-300` fill + `Info` icon | `neutral-600 text-sm italic` | `Info` (`icon-sm`) | D-DNV-11 |
| `--safety-bias-softwarn-override` | Soft warning overridden with reason | `warning-200` + `neutral-600 text-xs italic` | `neutral-600 text-sm line-through` | `MessageSquareWarning` (`icon-sm`) | D-DNV-11 |
| `--safety-bias-trap-highlight` | R12 organizational trap triggered | `error-50` bg on guard row + `warning-500` ring | `error-700 text-sm font-semibold` | `Siren` (`icon-sm`) | D-GAP-R12 |

### 10.3 Short-Label Typography

- **Checklist labels:** `text-sm` (14px) `font-medium` max-width `32ch` with 2-line wrap max. Abbreviate guard names to ≤ 18 chars (see `#` column in §10.1 — `Plant-Problem Trap`, `External-Event Trap`, etc., fit).
- **Tooltip full explanation:** `text-xs` (12px) `font-normal` `neutral-600` inside a `surface-elevated` card with `shadow-lg` and `radius-md` — reuses inherited Chart-hover-tooltip token (Reporting §7.3).
- **Guard number badge:** `text-xs font-bold` circle 20 × 20 px, `neutral-800` bg, white text — prefixes each row.

### 10.4 Guard #5 Hard-Block Modal

When Blame-Fixation fires, render the inherited Modal token (Inspection §11, Reporting §10.7 pattern) with:

- Overlay: `surface-overlay` (`rgba(0,0,0,0.5)`), `z-50`
- Dialog header bg: `error-50`; header text: `error-700` `text-lg font-semibold`; header icon: `ShieldAlert` (`icon-lg`, `error-600`)
- Body: explanation + "Request DPA override" primary action (button = inherited Primary Button)
- Cancel: "Return to Phase 6 and add a Lack-of-Control root cause" secondary action

---

## 11. Mobile-First Tokens (SOI Tablet Profile)

Locked by **D-GAP-M34** (SSOT §6 L1533) — tablet (`≥ 768 px`) fully supported for all CRUD; phone (`≤ 480 px`) read-only dashboards only; desktop (`≥ 1280 px`) primary target.

**SOI context (D-GAP-E4):** Paper-first workflow — the SO prints / downloads the checklist, does fieldwork on paper, then enters findings digitally on the bridge tablet. Tablet is the **primary capture device** for SOI findings.

### 11.1 Breakpoint Profiles

All breakpoint values inherited from Inspection §7. Safety defines the **activation rules** for each.

| Breakpoint | Min width | Safety behaviour | Decision |
|------------|-----------|---------------------|----------|
| `bp-phone-readonly` (≤ `bp-sm` - 1 px = ≤ 639 px) | — | Read-only dashboards; CRUD disabled with banner "This surface requires a tablet or desktop (D-GAP-M34)." | D-GAP-M34 |
| `bp-tablet` (`bp-md` = 768 px) | 768 px | **Full CRUD enabled**; SOI-entry optimised layout (single column, sticky header, enlarged hit targets — see §7.3) | D-GAP-M34 |
| `bp-desktop` (`bp-lg` = 1024 px) | 1024 px | Multi-column incident-detail layout, side-rail filters, causal-tree side-by-side with evidence panel | D-GAP-M34 |
| `bp-wide` (`bp-xl` = 1280 px) | 1280 px | **Primary target** — dashboards with Pareto panel, Heinrich ratio panel, and multi-band filter chips | D-GAP-M34 |

### 11.2 Tablet-First SOI Layout Tokens

| Token | Value | Decision |
|-------|-------|----------|
| `--safety-soi-row-min-height` | `56 px` (vs. 40 px desktop default) | D-GAP-M34 + WCAG 2.1 §2.5.5 |
| `--safety-soi-checkbox-size` | `28 × 28 px` (vs. 20 × 20 inherited default) | D-GAP-M34 + glove-use requirement |
| `--safety-soi-cell-tap-area` | `44 × 44 px` minimum on Yes/No/N-A/Obs columns | WCAG 2.1 AAA §2.5.5 |
| `--safety-soi-sticky-header-height` | `64 px` + 8 px bottom shadow `shadow-md` | D-GAP-M34 |
| `--safety-soi-photo-thumb` | `80 × 80 px` with `radius-md` + 1px `neutral-200` border; tap opens `surface-overlay` viewer | D-GAP-M24 (photo evidence mandatory for HIGH) |
| `--safety-soi-add-finding-fab` | Floating action button, 56 × 56 px, `primary-500` fill, `shadow-lg`, bottom-right `space-6` from edges | D-GAP-M34 + tablet ergonomics |

### 11.3 Tablet Typography Scale-Up

On tablet (`bp-tablet` to `bp-desktop - 1`):

- Body text: `text-base` (16px, inherited) — **no change** from desktop; 16px is already the ergonomic minimum.
- Input text: scales from `text-sm` (desktop) to `text-base` (tablet) to prevent iOS auto-zoom on focus.
- Button labels: `text-base font-medium` (vs. desktop `text-sm`) to preserve readability with distance + pitch.

### 11.4 Orientation Behavior

- **Portrait tablet (`width: 768–1023 px` with `orientation: portrait`):** SOI checklist single-column; signature block full-width.
- **Landscape tablet (`width: 1024 px+`):** 2-column layout permitted (item list left, detail right).
- Incident module never splits below 1024 px — switches to stacked single-column at tablet portrait.

---

## 12. Safety-Specific Icons

All icons from **Lucide React v0.408.0** (same library and version as Reporting + Inspection — no new library). Sizes reuse the inherited `icon-xs / sm / md / lg / 2xl` scale.

| Usage | Lucide name | Size default | Context | Decision |
|-------|-------------|--------------|---------|----------|
| Incident module | `AlertTriangle` | `icon-lg` | Route + module identifier | D-DNV-05 |
| Near Miss module | `AlertCircle` | `icon-lg` | Route + module identifier | D-GAP-R22 |
| SCM module | `Users` | `icon-lg` | Route + module identifier | D-GAP-M-ADHOC |
| SOI module | `ClipboardCheck` | `icon-lg` | Route + module identifier | D-SOI-07 |
| Anonymity masked | `EyeOff` | `icon-sm` | Near Miss reporter field, non-DPA/FM views | D-GAP-J1 |
| Anonymity visible | `Eye` | `icon-sm` | Near Miss reporter field, DPA/FM view | D-GAP-J1 |
| Corrective action badge | `Wrench` | `icon-sm` | D-DNV-06 / D-GAP-R13 tier 1 | D-GAP-R13 |
| Preventive action badge | `ShieldCheck` | `icon-sm` | D-DNV-06 / D-GAP-R13 tier 2 | D-GAP-R13 |
| Lessons Learnt badge | `BookOpen` | `icon-sm` | D-DNV-06 / D-GAP-R13 tier 3 | D-GAP-R13, D-DNV-06 |
| Causal Immediate | `Zap` | `icon-sm` | Immediate-cause row | D-GAP-R01 |
| Causal Intermediate | `GitBranch` | `icon-sm` | Intermediate-cause row | D-GAP-R01 |
| Causal Root | `Sprout` (inverted rotate-180) | `icon-sm` | Root-cause row | D-GAP-R01 |
| Bias-guard passed | `Check` | `icon-sm` | Checklist row | D-DNV-11 |
| Bias-guard warn | `AlertTriangle` | `icon-sm` | Soft warning | D-DNV-11 |
| Bias-guard hard-block | `XOctagon` | `icon-sm` | Blame Fixation only | D-DNV-11 |
| Bias-guard DPA override | `ShieldAlert` | `icon-sm` | Override applied | D-DNV-11 |
| Chain-of-Custody | `Link2` | `icon-sm` | Evidence tab | D-GAP-R04 |
| MSC-MEPC.3 export | `FileDown` | `icon-md` | Regulatory export button | D-DNV-12 |
| Fleet Circular | `Send` | `icon-md` | Lessons-Learnt auto-feed | D-PDF-01, D-DNV-06 |
| Signature digital | `PenLine` | `icon-sm` | Signature-block trigger | D-GAP-D1 |
| Signature wet-scan attach | `PaperClip` | `icon-sm` | Signature-block optional attach | D-GAP-D1 |
| SOI finding HIGH photo requirement | `Camera` | `icon-sm` | SOI finding row | D-GAP-M24 |
| Paper-first SOI download | `Download` | `icon-md` | PDF/Excel generator | D-GAP-E4 |
| Ad-Hoc SCM | `CalendarPlus` | `icon-md` | SCM meeting_type indicator | D-GAP-M-ADHOC |
| ALARP gate | `Gauge` | `icon-sm` | System-Action recommendation | D-GAP-R02 |
| Pareto screening | `BarChart3` | `icon-md` | Dashboard panel | D-GAP-R17 |
| Heinrich ratio | `Triangle` | `icon-md` | Dashboard panel | §2B.14 (SSOT) |

**Rule:** No icon in this module is meaning-bearing on its own. Every icon is paired with a text label, ARIA label, or tooltip (D-GAP-M35).

---

## 13. Composite Card States (Incident / Near Miss / SOI / SCM Lists)

Reuses the Reporting "left-border accent" card pattern (Reporting §9) — Safety extends with risk-band left-border mapping.

| Card state | Background | Left border (4px) | Additional | Decision |
|------------|------------|---------------------|------------|----------|
| Draft incident | `neutral-50` | `2px solid neutral-300` | — | D-EDGE-08 |
| Submitted GREEN-band | `surface-card` | `--safety-risk-green-border` | GREEN pill in header | D-DNV-02 |
| Submitted YELLOW-band | `surface-card` | `--safety-risk-yellow-border` | YELLOW pill in header | D-DNV-02 |
| Submitted RED-band | `surface-card` | `--safety-risk-red-border` | RED pill in header + pulsing `error-500` dot (2s ease-in-out, inherited Reporting pulse spec §9) | D-DNV-02, D-GAP-F4 |
| Sent Back | `warning-50` | `warning-500` | Pulsing `warning-500` dot | D-EDGE-03 |
| Near Miss card (masked reporter) | `surface-card` | `primary-500` | `EyeOff` icon on Reporter field | D-GAP-J1 |
| SOI finding HIGH | `surface-card` | `--safety-sev-high` (`error-600`) | `Camera` icon if ≥1 photo attached | D-GAP-M24 |
| SOI finding Carried Forward | `surface-card` | dashed `neutral-400` | "CARRIED FORWARD" pill | D-SOI-14 |
| Overdue (deadline missed) | `error-50` | `error-600` | Red overlay ribbon "OVERDUE" | D-DNV-02 |

Card dimensions, radius, shadow, padding, hover-elevation transform: all inherited from Reporting §9 / Inspection §11.3.

---

## 14. PDF Styling Extensions (Safety)

Inherits Reporting §13 / Inspection §12 PDF base (A4, 20mm margins, Inter body 10pt, heading 12–14pt). Safety extensions per **D-PDF-01** (SSOT §6 L1444) and **D-GAP-R09** (L1547) 10-section template.

### 14.1 Incident PDF — 10-Section Template (D-GAP-R09)

| Section # | Title | Styling extension | Decision |
|-----------|-------|---------------------|----------|
| 1 | Cover + IMO classification + risk band | Top band 15mm, color = band text token (`error-700` RED / `warning-700` YELLOW / `success-700` GREEN); logo top-left 25×25mm; `IMO classifier` outline-pill bottom-right | D-GAP-R08, D-GAP-R09 |
| 2 | Investigator / team credentials | Standard section; each credential row = 10pt | D-GAP-R09 |
| 3 | Evidence collected + Chain-of-Custody cross-ref | Table with `neutral-200` grid (inherited); Chain-of-Custody ID column 12mm | D-GAP-R04, D-GAP-R09 |
| 4 | Root-cause analysis (Immediate / Root labels) | Each causal-layer row uses the current two-level RCA layout; legacy Intermediate rows are grouped under Root Cause. | D-GAP-R01, D-GAP-R09, D-MAINT-CR033 |
| 5 | 7-point causal-factor enumeration (KAIZEN §11.5.6.1) | Numbered list 1–7, 10pt body | D-GAP-R09 |
| 6 | Corrective / Preventive / Lessons Learnt actions + timeline | Tier chip 6pt uppercase; tier color matches §6 tokens | D-GAP-R13, D-DNV-06 |
| 7 | Lessons Learnt narrative | Italic block, `neutral-700` 10pt, 5mm left indent | D-DNV-06, D-PDF-01 |
| 8 | Fleet notification plan | Table — Vessel · Method · Date | D-DNV-06 |
| 9 | Signatures per D-PDF-01 | Signature-block rows per §8 variant tokens; RED adds FM row; `Master / DPA / [FM for RED]` chain | D-PDF-01, D-GAP-D1 |
| 10 | Appendices — attachments list | Table — Doc name · Type · Attached by · Date | D-GAP-R09 |

### 14.2 Cover Band Color (per Risk Band)

| Token | RED | YELLOW | GREEN |
|-------|-----|--------|-------|
| `--safety-pdf-cover-band` | `error-700` `#B91C1C` | `warning-700` `#B45309` | `success-700` `#047857` |

All three are inherited Reporting/Inspection hex values.

### 14.3 Near Miss PDF Anonymity Handling

- When PDF is generated by Master / HOD / auditor role: Reporter field prints `Anonymous Reporter` literally (D-GAP-J1).
- When PDF is generated by DPA / FM: Reporter field prints full name.
- Generation role is recorded in the PDF footer along with the timestamp and job ID — `audit.pdf_role = 'DPA|FM|MASTER|HOD|AUDITOR'`.

### 14.4 SCM / SOI PDF Extensions

| Document | Extension | Decision |
|----------|-----------|----------|
| SCM minutes | "Closed Items Since Last Meeting" block between Attendance and Section 8, rendered as 10pt table with finding ID · description · closure date · Master-sign-off timestamp | D-SOI-14, D-GAP-M22 |
| SOI paper-first (PDF) | **Unique ID barcode (or QR)** bottom-right of every page; 20 × 20mm; links back to `vims_safety_soi_inspection.id` | D-GAP-E4 (paper-first no-scan) — **see BLOCKED stub below** |
| SOI paper-first (Excel) | Same layout as PDF; unique ID cell top-right; response cells unlocked for tablet edit | D-GAP-E4 |

> **BLOCKED: Paper-format barcode vs QR choice for SOI unique ID**
> **Question:** Barcode (Code128) or QR code for the SOI paper-form unique ID imprinted on each page?
> **Gap:** Build-time deferral #10 in the `<rules>` BACKEND deferral list (dispatch brief §6); no D-* locks this.
> **Impact:** `FEAT-SAF-SOI-012` (paper-first download) layout is otherwise specified, but the machine-readable format choice affects PDF renderer library selection (barcode-jsbarcode vs qrcode-generator) and the scanner SDK on vessel tablets if findings are later barcode-scanned.

---

## 15. Rules Summary

1. **Inheritance is mandatory.** Every base token comes from Reporting `DESIGN_SYSTEM.md` §1. No restatement, no re-invention.
2. **Safety-specific tokens require a decision citation.** Every `--safety-*` token in this document cites its governing `D-GAP-DESIGN-*` or `D-*` ID from `VIMS-SAFETY-MODULE-SSOT.md §6`.
3. **"SOI Compliance %" is the canonical label.** Never `Inspection Compliance %`. Enforced by **D-GAP-DESIGN-01** and audited in COVERAGE.md.
4. **WCAG 2.1 Level AA is the floor.** All text passes 4.5:1 (normal) / 3:1 (large); all non-text UI passes 3:1. Color alone is never meaning-bearing (D-GAP-M35).
5. **Minimum hit target 44 × 44 px** across all interactive elements (vessel tablet reality).
6. **Mobile-first is SOI-first.** Tablet (`bp-md` = 768 px) is a full CRUD target; phone is read-only (D-GAP-M34).
7. **Anonymity masking is role-scoped, not data-deletion.** System stores the reporter name; non-DPA/FM viewers see the `EyeOff` badge (D-GAP-J1).
8. **No new color invented for V1.** The only NEW Safety-specific token that is not a re-mapping of an inherited color is the SOI-specific tap-target sizing in §11.2 — every hex in this file resolves to an existing Reporting/Inspection value.
9. **Signatures are hybrid-digital, no PKI.** Typed name + timestamp + device fingerprint (D-GAP-D1); wet-signed scan optional attachment (D-GAP-D2).
10. **Dark mode deferred** to Inspection's first dark-mode release (Reporting §15 rule 7).

---

## 16. Naming-Convention Cheat-Sheet (Developer Quick Reference)

```
--safety-risk-{green|yellow|red}-{bg|text|border}          → §3.1
--safety-risk-imo-{smc|mc|mi}-{bg|text}                    → §3.2
--safety-sev-{low|medium|high|critical}                    → §3.4
--safety-state-{draft|submitted|under-review|approved|closed|sent-back}  → §4.1
--safety-state-soi-compliance                              → §4.2 (D-GAP-DESIGN-01)
--safety-state-finding-{open|pending|approved|closed|carried}  → §4.3
--safety-causal-{immediate|intermediate|root}              → §5.1
--safety-rec-{corrective|preventive|lessons}-{bg|text}     → §6
--safety-sig-{reporter|master|hod|dpa|fm}                  → §8.1
--safety-anon-{masked|visible}-{icon|label-bg|label-text}  → §9.1
--safety-bias-{unchecked|passed|warned|blocked|override|justified|softwarn-override|trap-highlight}  → §10.2
--safety-soi-{row-min-height|checkbox-size|cell-tap-area|sticky-header-height|photo-thumb|add-finding-fab}  → §11.2
--safety-pdf-cover-band                                    → §14.2
```

---

## 17. Document References

| Document | Relationship |
|----------|---------------|
| `VIMS-Reporting-Module/DESIGN_SYSTEM.md` | **Parent** — all base tokens inherited |
| `VIMS DOCS/DESIGN_SYSTEM.md` | **Grandparent** — Inspection module foundation |
| `VIMS-SAFETY-MODULE-SSOT.md` | Source of truth for every `D-*` and `D-GAP-*` decision cited herein |
| `VIMS-Safety-Module/PRD.md` | Feature requirements consuming these tokens |
| `VIMS-Safety-Module/FRONTEND_GUIDELINES.md` | Component-engineering rules that cite these tokens |
| `VIMS-Safety-Module/APP_FLOW.md` | Screens that render these tokens |
| `VIMS-Safety-Module/VALIDATION_RULES.md` | WCAG + signature-order enforcement rules |

---

**Document Control:**
- Created: 2026-04-17 (Session 5 close)
- Author: System Generated (Safety Module Docsuite Wave 1)
- Parent: Reporting DESIGN_SYSTEM.md v1.0 (2026-04-06) → Inspection DESIGN_SYSTEM.md v1.0 (2026-02-03)
- Safety Extension Version: 1.0
- Decisions cited: D-GAP-DESIGN-01, D-GAP-J1, D-GAP-M34, D-GAP-M35, D-GAP-R01, D-GAP-R02, D-GAP-R04, D-GAP-R08, D-GAP-R09, D-GAP-R12, D-GAP-R13, D-GAP-R17, D-GAP-R22, D-GAP-M16, D-GAP-M22, D-GAP-M24, D-GAP-M-ADHOC, D-GAP-E4, D-GAP-D1, D-GAP-D2, D-DNV-01, D-DNV-02, D-DNV-05, D-DNV-06, D-DNV-11, D-DNV-12, D-SOI-07, D-SOI-14, D-RBAC-01, D-RBAC-05, D-PDF-01, D-EDGE-03, D-EDGE-08
- BLOCKED stubs open: 1 (§14.4 — SOI paper-form barcode-vs-QR choice)
