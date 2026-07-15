# VIMS Certificates Module — Design System

> **Version:** 1.1
> **Last Updated:** 2026-07-15
> **Status:** Locked
> **Source:** D-CERT-125 → D-CERT-150 (Print/Export round) + D-CERT-127 (logo reuse from `VIMS DOCS/DESIGN_SYSTEM.md` line 481) + Reporting/Safety inherited tokens.
> **Inheritance:** Reuses platform Tailwind config, shadcn/ui primitives, color palette. Adds Certs-specific tokens for status tiers, watermark scopes, print layout.

---

## 1. Inherited Tokens (Platform)

Pulled from `../VIMS-Safety-Module/DESIGN_SYSTEM.md` and platform Tailwind config. Do NOT redefine.

- **Typography:** `Inter` (system stack fallback). Sizes per Tailwind defaults (`text-xs` 12px / `text-sm` 14px / `text-base` 16px / `text-lg` 18px / `text-xl` 20px / `text-2xl` 24px).
- **Spacing scale:** Tailwind defaults (0.25rem unit).
- **Border radius:** `rounded-md` (6px) default, `rounded-lg` (8px) for cards.
- **Shadow:** Tailwind `shadow-sm` (subtle), `shadow-md` (raised), `shadow-lg` (modal).
- **Base color palette:** slate (neutral), white background, black text.
- **Brand accent:** KSM corporate blue (existing platform token — do not redefine).
- **Focus ring:** Tailwind `ring-2 ring-offset-2 ring-blue-500` (accessibility-compliant).

### 1.1 Screen Surface Treatment

The interactive Certs workspace uses a module-scoped light treatment. The page canvas is a soft mist (`#f4f8f8`), cards remain white, borders use quiet blue-gray/green-gray tones, and primary actions use a restrained teal (`#36747c`). Shadows are shallow and low-opacity; tables, filters, and vessel rows use subtle surface changes for hover and focus. This treatment is scoped under `.certs-theme` and does not change shared VIMS screens.

The status-tier colors and shape encoding in Section 2 remain unchanged. Their stronger contrast is intentional because expiry and renewal urgency must remain immediately visible and understandable without relying on the surrounding surface colors.

---

## 2. Status Tier Palette (D-CERT-135 / D-CERT-136)

**5 tiers** — color + shape hybrid for B/W-photocopy resilience. Every status indicator MUST render both color AND shape.

| Tier | Definition | Color (hex) | Tailwind class | Shape | Component |
|------|------------|-------------|----------------|-------|-----------|
| Current | days_to_go > 90 | `#16a34a` (green-600) | `bg-green-600 text-white` | ● filled circle | `CertStatusBadge.variant="current"` |
| Expiring-90 | days_to_go ≤ 90 | `#fde047` (yellow-300) | `bg-yellow-300 text-black` | ◐ half-filled circle (light amber) | `CertStatusBadge.variant="expiring-90"` |
| Expiring-30 | days_to_go ≤ 30 | `#f59e0b` (amber-500) | `bg-amber-500 text-black` | ◐ half-filled circle (medium amber) | `CertStatusBadge.variant="expiring-30"` |
| Expiring-7 | days_to_go ≤ 7 | `#ea580c` (orange-600) | `bg-orange-600 text-white` | ◐ half-filled circle (dark amber) | `CertStatusBadge.variant="expiring-7"` |
| Expired | days_to_go ≤ 0 | `#dc2626` (red-600) | `bg-red-600 text-white` | ◯ hollow circle with hatched bar overlay | `CertStatusBadge.variant="expired"` |

**Aligned with notification cadence:** 90/30/14/7/1d alerts per D-CERT-084 + post-expiry.

**Bands matter on B/W output:** shape alone disambiguates. Test print on grayscale before merge.

**Special states (additional badges, not status tiers):**
| State | Color | Tailwind | Badge |
|-------|-------|----------|-------|
| `n/a` (permanent) | slate-500 | `bg-slate-500 text-white` | "PERM" pill |
| `postponed` | violet-500 | `bg-violet-500 text-white` | "POSTPONED" pill |
| `superseded` | slate-400 | `bg-slate-400 text-white` (strikethrough) | "SUPERSEDED" pill |
| `expired_at_onboarding` | slate-700 with red border | `bg-slate-700 text-white border-red-500 border-2` | "QUARANTINE" pill |
| `pending_first_upload` | slate-300 | `bg-slate-300 text-black` | "PENDING UPLOAD" pill |
| `invalid_due_to_reflag` | red-300 | `bg-red-300 text-black` | "RE-FLAG PENDING" pill |
| `pending_supersession` | yellow-200 | `bg-yellow-200 text-black` | "CLASS-CHANGE PENDING" pill |
| `pdf_missing: true` | red-600 outline | `border-2 border-red-600 text-red-600 bg-white` | "PDF MISSING" pill |

---

## 3. Approval State Palette

| State | Color | Tailwind | Visible context |
|-------|-------|----------|-----------------|
| `draft` | slate-300 | `bg-slate-300 text-slate-700` | TrackedItem detail (submitter), approval queue (off) |
| `pending_master_approval` | yellow-400 | `bg-yellow-400 text-black` | Master's approval queue, cert card |
| `approved` | green-600 | `bg-green-600 text-white` | All approved certs (default, often hidden when default) |
| `rejected` | red-600 | `bg-red-600 text-white` | Returned to submitter with reason callout |

---

## 4. Watermark Scope (D-CERT-138)

Diagonal text overlay, ~30% opacity, light gray (`#a3a3a3`, `text-neutral-400/30`). Font-size large enough to read across page (~96pt on letter/A4). Never obscures data.

| Watermark | Scope | Color | Text format |
|-----------|-------|-------|-------------|
| (none) | Post-go-live default per-vessel | — | — |
| `INTERNAL` | DPA fleet-wide internal print | neutral-400 | `INTERNAL` |
| `AUDIT COPY` | External auditor export (D-CERT-096) | neutral-400 | `AUDIT COPY — <VESSEL NAME>\n<auditor name>\nAccess expires <dd-Mmm-yyyy>` |
| `MASTER COPY` | Master share-bundle (D-CERT-096) | neutral-400 | `MASTER COPY — <recipient name>` |
| `DRAFT` | Pre-go-live during onboarding | neutral-400 | `DRAFT — NOT FINAL` |

---

## 5. Print Layout (D-CERT-125 → D-CERT-135)

**Form code on every print:** `SQE S 633` preserved verbatim (D-CERT-125). Free design beyond that.

### 5.1 Paper / Margins
- **Paper size:** A4 (default) or US Letter (DPA-configurable). Detected from print job.
- **Orientation:** Landscape (11-column schema fits better landscape; portrait acceptable for partial scopes with fewer columns).
- **Margins:** ≥0.6" left binding edge (D-CERT-129); 0.4" right/top/bottom.

### 5.2 Header (page 1)
- **Top-left logo:** 30mm × 15mm sourced from `GET /api/auth/company-logo/` (D-CERT-127, matches PSC Inspection pattern).
- **Top-right vessel block (large):**
  - Vessel name — `text-2xl font-bold`
  - IMO — `text-base`
  - Flag — `text-base`
  - Class society — `text-base`
  - Ship type — `text-base`
  - Current Master at print time — `text-base`
  - Print date — `text-sm`
- **Form code identifier:** `SQE S 633 — Certificates and Surveys` in `text-lg font-semibold` below header.

### 5.3 Header (pages 2+)
Compact one-line: `<Vessel Name> · IMO <num> · Page X of Y · <Current Section Banner>`. Font: `text-xs`.

### 5.4 Section Banner
Each section repeats on its first page: full-width strip, KSM brand color, `text-base font-semibold text-white`. Section code + display name (e.g. "STATUTORY & FLAG").

### 5.5 11-Column Schema (D-CERT-130)

| # | Column | Width (relative) | Source |
|---|--------|------------------|--------|
| 1 | S/No | 4% | resets per section |
| 2 | Certificate name | 24% | `display_name` (wraps 2 lines if needed) |
| 3 | Cert number | 8% | `certificate_number` (empty if bypassed) |
| 4 | Issued by | 11% | `issuing_authority` |
| 5 | Place of issue | 8% | `place_of_issue` |
| 6 | Date of issue | 9% | `issue_date` formatted `dd-Mmm-yyyy` |
| 7 | Date of expiry | 9% | `expiry_date` ("Permanent" if applicable) |
| 8 | Validity | 6% | short code per §6 |
| 9 | Days to go | 6% | computed; negative when expired |
| 10 | Status | 5% | small color dot + 1-letter G/Y/R (B/W-printer-friendly) |
| 11 | Remarks | 10% | `legacy_remarks` + manual notes |

### 5.6 Sub-numbering (D-CERT-133)
Parent: section-relative serial (e.g. `19`). Children: sub-letters (e.g. `19.a Last Annual Survey`, `19.b Last Intermediate Survey`). Flat row format; no indentation tricks; sub-numbering carries hierarchy semantics.

### 5.7 Row Ordering (D-CERT-134)
Within each section: rows by `catalog.print_order`. Children always immediately follow their parent regardless of children's own `print_order`. Stable across reprints.

### 5.8 Empty Sections (D-CERT-129)
Section banner always printed even if empty. Body shows: `— no certs in this section for this vessel —` in italic gray text. Auditor sees that the section was checked, not omitted.

### 5.9 Footer (every page)
- Left: `print_id` (full string per D-CERT-128, e.g. single-vessel `SQE-S633-9876543-20260507-001`; fleet/multi-vessel `SQE-S633-FLEET-20260507-001`)
- Center: print user name + role (e.g. "DPA John Smith")
- Right: print date/time UTC + system-state hash (8-char per D-CERT-128)
- All footer text `text-xs text-neutral-600`.

### 5.10 Page-1 Validity Glossary (D-CERT-132)
At bottom of page 1 only (not subsequent pages): `Validity codes: A=Annual, Bi-A=Biennial, 5-Y=5-Yearly, 10-Y=10-Yearly, Perm.=Permanent, ST=Short-Term, 6-Mth=6-Monthly`. Font `text-xs italic`.

### 5.11 Digital Signature Block (D-CERT-139)
End-of-print: three lines
```
Approved by Master <name> on <date> at <time> via VIMS — print_id <reference>
Reviewed by Marine Sup'tt <name> on <date> via VIMS — <reference>
DPA acknowledgment <name> on <date> via VIMS — <reference>
```
No wet-signature lines.

---

## 6. Validity Short Codes (D-CERT-132)

| Long form | Print short code |
|-----------|------------------|
| Annual | `A` |
| Biennial | `Bi-A` |
| 5-Yearly | `5-Y` |
| 10-Yearly | `10-Y` |
| Permanent | `Perm.` |
| Short-Term | `ST` |
| 6-Monthly | `6-Mth` |

Glossary on page 1 footer only (D-CERT-132).

---

## 7. Date Format

`dd-Mmm-yyyy` throughout (D-CERT-131). Examples: `15-Mar-2027`, `01-Jan-2026`. Header dates, table dates, footer dates all use this format. No US/EU collision.

---

## 8. OCR Confidence Badge

Used in `GapFillForm` per-field display.

| Confidence band | Color | Tailwind | Icon |
|----------------|-------|----------|------|
| ≥ threshold (auto-accept) | (no badge) — value displayed in normal text | — | — |
| Gap-fill band (60% to threshold) | yellow-300 | `bg-yellow-300 text-black border-yellow-500` | "?" icon |
| Below 60% | red-300 | `bg-red-300 text-black border-red-500` | "✗" icon, field starts blank |
| Whole-doc unprocessable | orange-500 (full-form banner) | `bg-orange-500 text-white` | "!" icon, banner at top of form |

Thresholds: office = 80% (D-CERT-106), vessel = 85% (D-CERT-168). DPA-tunable per FEAT-CERT-OCR-012.

---

## 9. Component Library

All Certs-specific components live under `src/components/certs/shared/` and follow shadcn/ui primitives:

| Component | Variants | Used in |
|-----------|----------|---------|
| `CertStatusBadge` | current / expiring-90 / expiring-30 / expiring-7 / expired / permanent / postponed / superseded / quarantine / pending-upload / re-flag-pending / class-change-pending / pdf-missing | CertCard, TrackedItemDetail, PrintTemplate, Dashboard |
| `OcrConfidenceBadge` | high / gap / low / unprocessable | GapFillForm |
| `ClassSocietyChip` | NK / KR / BV | SnapshotList, ReconciliationReview |
| `WatermarkOverlay` | INTERNAL / AUDIT-COPY / MASTER-COPY / DRAFT | PrintArtifactPdfTemplate |
| `PrintIdFooter` | with print_id, user, role, UTC timestamp, state hash | PrintArtifactPdfTemplate |
| `BatchProgressBar` | OCR running / ready / committed / cancelled | Onboarding step 3 |
| `ApprovalStateChip` | draft / pending_master_approval / approved / rejected | TrackedItemDetail, ApprovalQueueTable |
| `CertExpiryTier` | (composed of CertStatusBadge + days_to_go text) | CertCard, Dashboard |
| `CoverageBanner` | active (<100%) / dismissed | CertVesselDashboard, OnboardingWizard step 6 |
| `LifecycleStatusBanner` | onboarding / pending_disposal / pending_supersession / flag_change_pending | CertVesselDashboard, VesselProfileScreen |
| `MagicLinkAckButton` | (in email HTML template) | EmailTemplates |
| `RedactedReasonText` | text / `[REDACTED — internal note]` | AuditLogTable (external auditor view) |

---

## 10. Accessibility

- WCAG AA: every status indicator carries shape + color + text (not color alone).
- Keyboard nav: full tab order through every interactive element.
- Focus ring: platform default (`ring-2 ring-offset-2 ring-blue-500`).
- ARIA: `aria-label` on icon-only buttons; `role="status"` on banner regions; `aria-live="polite"` for OCR completion notifications.
- Color-blind friendly: amber tiers differ in shape (light/medium/dark half-circle), not solely in hue.
- B/W print: status indicators retain shape encoding (D-CERT-135 explicit requirement).

---

## 11. Mobile / Tablet Tokens

- Breakpoints: Tailwind defaults (`sm` 640 / `md` 768 / `lg` 1024 / `xl` 1280).
- Bridge tablet primary: tested at 1024×768 (iPad classic) and 1280×800 (modern Android tablets).
- Touch target minimum: 44×44 px per platform accessibility standard.
- PDF preview: pinch-zoom enabled; falls back to native viewer on iOS Safari.

---

*End of DESIGN_SYSTEM v1.0. Status tier palette + watermark scope are the load-bearing visual contracts — never drift these.*

---

## Appendix — Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `DESIGN_SYSTEM.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` ✓ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-002 | Print/export retains SQE S 633 layout. | LOCKED |
| D-CERT-113 | Missing-PDF cert rows allowed at onboarding. | LOCKED |
| D-CERT-119 | Per-vessel onboarding completion = hybrid auto-enable / override. | LOCKED |
| D-CERT-121 | Already-expired certs at onboarding = quarantine state. | LOCKED |
| D-CERT-126 | Vessel header block (every page): Top of page 1 carries: vessel name (large), IMO, flag, class society, ship type, current Mast... | LOCKED |
