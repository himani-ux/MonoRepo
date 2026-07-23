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

Normal Print Builder PDFs print the selected watermark as a small bottom-right label on each page. The label is red, does not include the recipient name, and must not obscure table data (D-CERT-202). External auditor exports may keep the separate auditor watermark pattern where required by grant policy.

| Watermark | Scope | Color | Text format |
|-----------|-------|-------|-------------|
| (none) | Post-go-live default per-vessel | — | — |
| `INTERNAL` | DPA fleet-wide internal print | neutral-400 | `INTERNAL` |
| `AUDIT COPY` | External auditor export (D-CERT-096) | neutral-400 | `AUDIT COPY — <VESSEL NAME>\n<auditor name>\nAccess expires <dd-Mmm-yyyy>` |
| `MASTER COPY` | Master share-bundle / selected print watermark (D-CERT-096, D-CERT-202) | red-700 for normal print PDF | `MASTER COPY` |
| `DRAFT` | Pre-go-live during onboarding | neutral-400 | `DRAFT — NOT FINAL` |

---

## 5. Print Layout (D-CERT-125 → D-CERT-135)

**Stored form identity:** `SQE S 633` remains in stored print IDs, filenames, audit/history records, and API responses. Normal visible PDFs do not print the form-code title/header per D-CERT-202.

### 5.1 Paper / Margins
- **Paper size:** A4 (default) or US Letter (DPA-configurable). Detected from print job.
- **Orientation:** Landscape for the normal 10-column certificate table; portrait acceptable for partial scopes with fewer columns.
- **Margins:** ≥0.6" left binding edge (D-CERT-129); 0.4" right/top/bottom.

### 5.2 Visible Start (page 1)
- Vessel context line: vessel name, IMO, flag, and class society when available.
- Printed-by line: `Printed by: <user> (<role>)`.
- No company-logo header, report title, scope label, print ID, hash, recipient name, or generation-footer page in the normal visible PDF.

### 5.3 Continuing Pages
No repeating report header. The table header repeats as needed, and the selected watermark label appears bottom-right on each page.

### 5.4 Section Banner
Each section repeats on its first page: full-width strip, KSM brand color, `text-base font-semibold text-white`. Section code + display name (e.g. "STATUTORY & FLAG").

### 5.5 10-Column Schema (D-CERT-130, D-CERT-202)

| # | Column | Width (relative) | Source |
|---|--------|------------------|--------|
| 1 | Section | 10% | catalog section name/code |
| 2 | Sub No. | 5% | row number in the printed set |
| 3 | Certificate / Survey | 21% | `display_name` or catalog code |
| 4 | Cert No. | 10% | `certificate_number` |
| 5 | Issued By | 10% | `issuing_authority` |
| 6 | Issue | 8% | `issue_date` |
| 7 | Expiry | 8% | `expiry_date` or `PERM` |
| 8 | Last Done | 8% | `last_done_date` |
| 9 | Next Due | 8% | `next_due_date` |
| 10 | Status | 12% | text status |

### 5.6 Sub-numbering (D-CERT-133)
Parent: section-relative serial (e.g. `19`). Children: sub-letters (e.g. `19.a Last Annual Survey`, `19.b Last Intermediate Survey`). Flat row format; no indentation tricks; sub-numbering carries hierarchy semantics.

### 5.7 Row Ordering (D-CERT-134)
Within each section: rows by `catalog.print_order`. Children always immediately follow their parent regardless of children's own `print_order`. Stable across reprints.

### 5.8 Empty Sections (D-CERT-129)
Section banner always printed even if empty. Body shows: `— no certs in this section for this vessel —` in italic gray text. Auditor sees that the section was checked, not omitted.

### 5.9 Visible Print Metadata (D-CERT-202)
Normal Print Builder PDFs do not print an internal header/title, scope label, `print_id`, system-state hash, recipient name, or generation-footer page. The only generator line in the visible PDF is `Printed by: <user> (<role>)`. The stored artifact still carries `print_id`, hash, timestamp, role, and audit metadata in DB/API/history.

### 5.10 Validity Glossary (D-CERT-132, D-CERT-202)
Validity data remains in system records, but normal visible PDFs do not print the validity code column or page-1 glossary.

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

Normal visible PDFs omit the validity code column and glossary per D-CERT-202.

---

## 7. Date Format

`dd-Mmm-yyyy` throughout where dates are printed (D-CERT-131). Examples: `15-Mar-2027`, `01-Jan-2026`. No US/EU collision.

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
| `BottomRightWatermark` | INTERNAL / AUDIT-COPY / MASTER-COPY / DRAFT label without recipient name | PrintArtifactPdfTemplate |
| `PrintedByLine` | `Printed by: <user> (<role>)` | PrintArtifactPdfTemplate |
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
| D-CERT-002 | Print/export retains SQE S 633 artifact identity; visible normal PDF form-code header is superseded by D-CERT-202. | LOCKED |
| D-CERT-113 | Missing-PDF cert rows allowed at onboarding. | LOCKED |
| D-CERT-119 | Per-vessel onboarding completion = hybrid auto-enable / override. | LOCKED |
| D-CERT-121 | Already-expired certs at onboarding = quarantine state. | LOCKED |
| D-CERT-126 | Vessel context remains visible on normal PDFs; full header block/every-page header is superseded by D-CERT-202. | LOCKED |
