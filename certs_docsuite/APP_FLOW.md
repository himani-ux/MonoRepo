# VIMS Certificates Module — Application Flow

> **Version:** 1.2
> **Last Updated:** 2026-06-12 (v1.2 — B-FLOW-01..03 RESOLVED: 403 page, maintenance page, route-guard return-to all specified; RATE_LIMITED N/A confirmed via B-SEC-11. v1.1 — KLOSS Step 2 realignment: §5 upgraded from 4-state to 11-state contract + §5.1 per-screen deviations. v1.0: 2026-05-13)
> **Status:** 🟢 Locked — Ready for Build (all 11 states specified or sourced-N/A on every screen)
> **Source:** SSOT §§3, 6, 7, 9, 11, 13 + PRD Feature Registry + Safety APP_FLOW.md pattern.
> **Relation to FIELD_MAP.md:** Every "Surfaces" line in this doc names DB columns / API keys that MUST appear in `FIELD_MAP.md`. If a screen surfaces a field that has no FIELD_MAP entry, the merge is blocked.

---

## Table of Contents

1. [Navigation Architecture](#1-navigation-architecture)
2. [Role-Permission Matrix per Screen](#2-role-permission-matrix-per-screen)
3. [Screen Catalog](#3-screen-catalog)
   - 3.1 Fleet Dashboard `/certs`
   - 3.2 Catalog Admin `/certs/catalog`
   - 3.3 Catalog Row Detail `/certs/catalog/<catalog_id>`
   - 3.4 Vessel Cert Dashboard `/certs/vessels/<imo>`
   - 3.5 TrackedItem Detail `/certs/vessels/<imo>/cert/<tracked_item_id>`
   - 3.6 Onboarding Hub `/certs/onboarding`
   - 3.7 Onboarding Wizard `/certs/onboarding/<imo>` (7 steps)
   - 3.8 Gap-Fill UI `/certs/onboarding/<imo>/batch/<batch_id>/gap-fill`
   - 3.9 Reconciliation Dashboard `/certs/reconciliation`
   - 3.10 Reconciliation Review (3-panel) `/certs/reconciliation/<run_id>`
   - 3.11 Print Builder `/certs/print`
   - 3.12 Print History `/certs/print/history`
   - 3.13 Master Share-Bundle `/certs/share-bundle`
   - 3.14 Notification Inbox (shared bell + Certs filter)
   - 3.15 External Auditor Provisioning `/certs/auditor-access`
   - 3.16 Auditor Access Detail `/certs/auditor-access/<grant_id>`
   - 3.17 Audit Log Read `/certs/audit-log`
   - 3.18 Vessel Profile (Certs context) `/certs/vessels/<imo>/profile`
   - 3.19 Settings `/certs/settings`
   - 3.20 External Auditor Portal `/auditor/<grant_token>/...`
4. [Cross-Screen Navigation Map](#4-cross-screen-navigation-map)
5. [4-State Contract per Screen](#5-4-state-contract-per-screen)
6. [Mobile / Tablet Adaptation](#6-mobile--tablet-adaptation)

---

## 1. Navigation Architecture

```
Top-level VIMS nav (existing)
└─ Certs (CERT_F_* form-id gate; visible to roles holding any CERT_F_*)
   ├─ Dashboard               → /certs
   ├─ Vessels                 → /certs/vessels (list) → /certs/vessels/<imo>
   │   ├─ Profile             → /certs/vessels/<imo>/profile
   │   └─ Cert detail         → /certs/vessels/<imo>/cert/<tracked_item_id>
   ├─ Catalog                 → /certs/catalog (DPA + System Admin only)
   │   └─ Row detail          → /certs/catalog/<catalog_id>
   ├─ Onboarding              → /certs/onboarding (DPA + FM only)
   │   └─ Wizard              → /certs/onboarding/<imo>
   │       └─ Gap-fill        → /certs/onboarding/<imo>/batch/<batch_id>/gap-fill
   ├─ Reconciliation          → /certs/reconciliation
   │   └─ Run review          → /certs/reconciliation/<run_id>
   ├─ Print                   → /certs/print
   │   └─ History             → /certs/print/history
   ├─ Share Bundle            → /certs/share-bundle (Master + DPA + FM)
   ├─ Auditor Access          → /certs/auditor-access (Marine Sup'tt primary, DPA override)
   │   └─ Grant detail        → /certs/auditor-access/<grant_id>
   ├─ Audit Log               → /certs/audit-log (DPA + FM full; Sup'tts own-vessel)
   └─ Settings                → /certs/settings (DPA only)

Notification Inbox (shared platform bell)
   - Filter: "Module = Certs" surfaces vims_certs_notification_meta-tagged rows from master_notification

External Auditor Portal (separate root)
   /auditor/<grant_token>/                    → landing
   /auditor/<grant_token>/vessels/<imo>       → scoped vessel view
   /auditor/<grant_token>/cert/<tracked_id>   → scoped cert detail (read-only)
   /auditor/<grant_token>/print               → scoped print (AUDIT COPY watermark)
```

---

## 2. Role-Permission Matrix per Screen

Permission gating uses `msc_profiles.form_ids` (CERT_F_\*) and `msc_profiles.process_ids` (CERT_P_\*) per the platform RBAC pattern (D-CERT-090). Role labels here: DPA, FM, TS (Tech Sup'tt), MS (Marine Sup'tt), TM (Technical Manager), M (Master), CO/CE/2E (vessel sub-officers), Other (other onboard officers, read-only own-vessel), EXT (external auditor, scoped).

| Screen | DPA | FM | TS | MS | TM | M | CO/CE/2E | Other | EXT |
|--------|-----|----|----|----|----|---|----------|-------|-----|
| 3.1 Fleet Dashboard | full fleet | full fleet | assigned | assigned | assigned | own vessel | own vessel | own vessel | scoped |
| 3.2 Catalog Admin | RW | R | R | R | R | — | — | — | — |
| 3.3 Catalog Row Detail | RW | R | R | R | R | — | — | — | — |
| 3.4 Vessel Cert Dashboard | full fleet | full fleet | assigned | assigned | assigned | own vessel | own vessel | own vessel | scoped |
| 3.5 TrackedItem Detail | RW any | RW any | RW assigned | RW assigned | R assigned | RW own + approver | submit own + Master gate | R own | R scoped |
| 3.6 Onboarding Hub | RW | R | — | — | — | — | — | — | — |
| 3.7 Onboarding Wizard | RW | R + sign-off step 7 | — | — | — | — | — | — | — |
| 3.8 Gap-Fill UI | RW | R | — | — | — | — | — | — | — |
| 3.9 Reconciliation Dashboard | RW | R | R | RW (primary reviewer) | R | R own (read-only) | — | — | — |
| 3.10 Reconciliation Review | RW | R | R | RW | R | notified-only (alert link) | — | — | — |
| 3.11 Print Builder | per-vessel + fleet-wide | per-vessel + fleet-wide | per-vessel assigned | per-vessel assigned | per-vessel assigned | per-vessel own | — | — | scoped per-vessel |
| 3.12 Print History | full fleet | full fleet | assigned | assigned | assigned | own vessel | — | — | scoped |
| 3.13 Master Share-Bundle | full fleet | full fleet | — | — | — | own vessel | — | — | — |
| 3.14 Notification Inbox | own | own | own | own | own | own | own | own | — (auditor portal has no inbox) |
| 3.15 Auditor Access Provisioning | RW | R | — | RW (primary) | — | — | — | — | — |
| 3.16 Auditor Access Detail | RW | R | — | RW | — | — | — | — | — |
| 3.17 Audit Log Read | full fleet | full fleet | own-vessel filtered view | own-vessel filtered view | own-vessel filtered view | — | — | — | — |
| 3.18 Vessel Profile | RW | RW | R | R | R | R own | R own | R own | R scoped |
| 3.19 Settings | RW | — | — | — | — | — | — | — | — |
| 3.20 External Auditor Portal | — (uses portal as themselves only via test grant) | — | — | — | — | — | — | — | RW within scope |

**Notation:** `RW` = read+write; `R` = read-only; `assigned` = vessels per `master_RoleByVessel`; `own vessel` = `vessel.master_user_id = current_user OR vessel.<role>_user_id = current_user`; `scoped` = per `vims_certs_external_auditor_access.scope_json`.

---

## 3. Screen Catalog

### 3.1 Fleet Dashboard `/certs`

**Route:** `/certs`
**Form ID:** `CERT_F_dashboard` (sidebar)
**Primary user:** All Certs roles; default landing.
**Purpose:** Fleet-wide compliance health snapshot per vessel.

**Layout:**
- Top bar: 6 vessel tiles (D-CERT-070): name, IMO, current Master, days since last class snapshot, cert count, % expiring 30/60/90d, # mismatches outstanding.
- Below tiles: 4 KPI cards — fleet expiring ≤30d, fleet overdue, pending Marine Sup'tt review (mismatches), DPA actionable items (catalog gaps, bouncing emails, override-required vessels).
- Bottom: recent activity feed (last 20 audit events, RBAC-filtered).

**Surfaces (must be in FIELD_MAP):**
- `master_vessel.vessel_name`, `master_vessel.imo_number`, `master_vessel.master_user_id` → joined `master_user.full_name`.
- Computed aggregates from `vims_certs_tracked_item`: `count_by_status_band` per D-CERT-136.
- `vims_certs_class_status_snapshot.uploaded_at` → "days since last snapshot".
- `vims_certs_reconciliation_flag` count where `resolved_at IS NULL`.
- D-CERT-119 mandatory-coverage banner if vessel has `<100%` coverage AND override not set.
- D-CERT-094 "pending statutory re-upload" banner if vessel has `flag_change_event` open.
- D-CERT-159 bouncing-email count (DPA-only card).
- D-CERT-143 high-volume print activity surface (FM-only card).

**4 states:** see §5.

**Navigation out:**
- Vessel tile → `/certs/vessels/<imo>`
- KPI card → filtered list or `/certs/reconciliation`
- Activity row → relevant entity detail

---

### 3.2 Catalog Admin `/certs/catalog`

**Route:** `/certs/catalog`
**Form ID:** `CERT_F_001` (Catalog Mgmt)
**Process IDs:** `CERT_P_008` (Catalog Edit), `CERT_P_009` (Bulk Action)
**Primary user:** DPA + System Admin only (D-CERT-090, FEAT-CERT-CAT-017).
**Purpose:** Maintain the fleet-wide cert-type catalog (~340 rows across 9 sections).

**Layout:**
- Section sidebar (9 sections, D-CERT-017): each shows count of active rows.
- Main area: filterable table of catalog rows. Visible columns are Code, Name, Validity, Ship types, and Status. Select is shown only when bulk actions are available. The first 50 rows load immediately, then later pages append in the background so the screen does not block on the full catalog. Cadence and submission scope remain available on catalog row detail/edit surfaces but are not repeated in the list table.
- Toolbar: "Add row" (DPA), "Bulk soft-delete" (DPA, capped at 50 rows + reason per D-CERT-092 / FEAT-CERT-CAT-019), "Bulk push to fleet" (DPA, auto-creates `pending_first_upload` rows on every active vessel per D-CERT-092 / FEAT-CERT-RBAC-026), "Anniversary recompute" (DPA + FM 2nd approver per D-CERT-092 / FEAT-CERT-RBAC-025), "Export catalog CSV" (DPA).
- Inline indicators: `parent_id` shown as indented child rows (UI 2-level cap per D-CERT-010); `parent_supports_dynamic_children: true` flag visible (D-CERT-035); IWS age-gate flag visible (D-CERT-034); `retain_all_versions: true` flag visible (D-CERT-039).

**Surfaces (FIELD_MAP):**
- All `vims_certs_catalog_row.*` columns per FEAT-CERT-CAT-004 / D-CERT-109.
- Joined `vims_certs_catalog_section.section_name` for sidebar grouping.

**4 states:**
- **Loading:** skeleton table + section sidebar shimmer.
- **Loaded:** populated table; sticky header.
- **Empty (only on filter):** "No catalog rows match your filter." Reset button.
- **Error:** "Could not load catalog. <retry>". Audit log captures fetch failure for ops.

**Navigation out:**
- Row click → `/certs/catalog/<catalog_id>`.
- "Add row" → `/certs/catalog/new`.
- "Bulk push to fleet" → confirm dialog with affected vessel + cert count preview (D-CERT-092).

---

### 3.3 Catalog Row Detail `/certs/catalog/<catalog_id>`

**Route:** `/certs/catalog/<catalog_id>`
**Form ID:** `CERT_F_001`
**Process ID:** `CERT_P_008`
**Primary user:** DPA edit; FM/TS/MS/TM read.
**Purpose:** Edit a single catalog row's metadata; view dependent TrackedItem instances across fleet.

**Layout:**
- Header: `canonical_code` (immutable post-creation), `display_name` (editable), `section` (immutable post-creation), Active/Inactive toggle, Audit chip ("created by X on Y, last edited by Z on W").
- Tabs:
  - **Metadata** — full row schema editable; validity_type, cadence_months, is_class_tracked, submission_scope, mandatory_for_all_vessels, applicable_ship_types[], parent_id picker, applicability_mode, alert_lead_overrides, regulatory_anchor, legacy_remarks, print_section_label, print_order.
  - **Instances** — table of all TrackedItem rows referencing this catalog row, grouped by vessel; status counts per band.
  - **Audit history** — full timeline of edits (5-year retention per D-CERT-099); filterable by actor.
- Footer: "Save changes" (DPA), "Deprecate row" (DPA, sets is_active=false, audit reason required), "Hard purge" (DPA, gated; cascades per D-CERT-182 / FEAT-CERT-CAT-020).

**Surfaces (FIELD_MAP):** All `vims_certs_catalog_row.*` + joined `vims_certs_tracked_item` aggregates per vessel.

**4 states:** standard.

**Navigation:** Instance row → `/certs/vessels/<imo>/cert/<tracked_item_id>`.

---

### 3.4 Vessel Cert Dashboard `/certs/vessels/<imo>`

**Route:** `/certs/vessels/<imo>`
**Form ID:** `CERT_F_002` (Tracked Items)
**Primary user:** Per role (full/own-vessel/scoped).
**Purpose:** All certs for a single vessel grouped by section, with status-tier visualization.

**Layout:**
- Header card: vessel name + IMO + flag + class society + ship type + current Master at top. "Last class snapshot uploaded N days ago" with link to `/certs/reconciliation` filtered to this vessel. Mandatory-coverage % (D-CERT-119) with override banner if applicable.
- Section accordion (9 sections, D-CERT-017): each section header shows section_name + active TrackedItem count + status-band breakdown badges (per D-CERT-136).
- Per-section table: expanded by default for sections with action items (overdue / window_open / window_closing); collapsed for healthy sections.
- Per-row columns: `display_name`, `certificate_number`, `issuing_authority`, `issue_date`, `expiry_date` ("Permanent" if applicable), `days_to_go` (computed), status pill (color+shape per D-CERT-135), validity short code (D-CERT-132), action button (Renew / Acknowledge / Upload).
- Toolbar: "Print this vessel" (D-CERT-140 per-vessel scope), "Share bundle" (Master self / DPA / FM only per D-CERT-142), "Upload class snapshot" (DPA / FM / Sup'tts), filter chips (status / section / `is_class_tracked` / `pdf_missing`).

**Surfaces (FIELD_MAP):**
- `vims_certs_tracked_item.*` rendered: id, catalog_code (joined to display_name), certificate_number, issuing_authority, place_of_issue, issue_date, expiry_date, anniversary_date (read-only display), status (computed), days_to_go (computed), validity_type → short code, parent_id grouping, pdf_attachment_id presence indicator.
- Hidden but available via row expansion: window_open, window_close, last_done_date, next_due_date, postponed_until, supersedes_id, extension_authority, extension_letter_pdf_id, extension_reason, source, last_class_sync_id.
- Approval state badge (`approval_state`) on rows where != `approved`.
- D-CERT-087 `vessel_acked` indicator on alert-bearing rows (office-side view).

**4 states:** standard. Empty for a brand-new vessel (pre-onboarding) shows "Vessel not yet onboarded — start wizard" CTA → `/certs/onboarding/<imo>`.

**Navigation:**
- Row click → `/certs/vessels/<imo>/cert/<tracked_item_id>`.
- "Profile" tab → `/certs/vessels/<imo>/profile`.

---

### 3.5 TrackedItem Detail `/certs/vessels/<imo>/cert/<tracked_item_id>`

**Route:** `/certs/vessels/<imo>/cert/<tracked_item_id>`
**Form ID:** `CERT_F_002`
**Process IDs:** `CERT_P_001` (Create), `CERT_P_002` (Submit), `CERT_P_003` (Approve), `CERT_P_004` (Reject)
**Primary user:** Master (own vessel) RW; C/O/C/E/2/E submit; DPA/FM/MS/TS direct write; TM read-only.
**Purpose:** Full per-cert editor with approval gate, PDF preview, hierarchy view, audit history.

**Layout (3-column desktop / stacked tablet):**
- **Left col — Cert metadata:**
  - Identity: catalog_code (display_name + canonical_code), certificate_number (with bypass per D-CERT-105 / FEAT-CERT-OCR-003), issuing_authority, place_of_issue, validity_type, form_variant (if IOPP-style per D-CERT-032). Users with TrackedItem write permission can use **Edit** in the Metadata card to manually correct OCR-filled certificate number, issuing authority, place of issue, issue date, and expiry date with an audit reason.
  - Dates: issue_date, expiry_date (or "Permanent"), anniversary_date (read-only; DPA-edit only via separate confirm flow), window_open/close (computed, read-only with tooltip "Computed from anniversary + cadence per D-CERT-063"), last_done_date, next_due_date, postponed_until.
  - Status pill (D-CERT-135/136 color+shape) + days_to_go.
  - Hierarchy: parent breadcrumb (D-CERT-010 2-level UI cap); child rows list (STC, extensions, dispensations, sub-surveys).
- **Middle col — PDF preview:**
  - Active PDF embedded (with download button).
  - Version history tray (D-CERT-019/020): previous PDFs with `superseded_at` timestamps; deleted-pending blobs grayed out (7-day grace per D-CERT-021).
  - Upload new PDF button (renewal / revision auto-detect per D-CERT-170 / FEAT-CERT-TRK-015).
- **Right col — Workflow + audit:**
  - Approval state pill (`draft / pending_master_approval / approved / rejected`).
  - Submitted_by + submitted_at + approved_by + approved_at (when applicable).
  - Action buttons gated by role + state:
    - Master: Approve / Reject (with reason) when state = `pending_master_approval`; Edit + Save direct (Master own write).
    - CO/CE/2E: Save as draft / Submit for approval (when own submission).
    - DPA / FM / MS / TS: Edit + Save direct (no approval gate).
  - Approval event timeline (D-CERT-018 / D-CERT-076): full state transitions with timestamps + reasons.
  - Notification thread: alerts fired for this row (D-CERT-155 metadata).
  - Field history: per-field change log (audit-driven; respects D-CERT-091/099 retention).
  - "Reset onboarding" button (DPA, only visible if vessel `lifecycle_status = onboarding_in_progress` per D-CERT-124 / FEAT-CERT-WIZ-019).

**Surfaces (FIELD_MAP):** Every column on `vims_certs_tracked_item`, all `vims_certs_pdf_blob` rows for this tracked_item (active + superseded + delete-pending), `vims_certs_approval_event` rows, `vims_certs_audit_log` filtered to this entity, `vims_certs_notification_meta` joined.

**Special states:**
- `expired_at_onboarding` → quarantine banner: "This cert was already expired at onboarding. Alerts suppressed. Either upload renewal or explicitly mark 'expired in reality' to begin alerts." (D-CERT-121 / FEAT-CERT-TRK-010)
- `pdf_missing: true` → red banner: "PDF not on file. Request copy from issuer." (D-CERT-113 / FEAT-CERT-TRK-011)
- `approval_state = rejected` → callout with rejection reason from approver, "Resubmit" button.
- `supersedes_id != null` → "This cert supersedes [link]." Linked predecessor row.

---

### 3.6 Onboarding Hub `/certs/onboarding`

**Route:** `/certs/onboarding`
**Form ID:** `CERT_F_005` (Onboarding Wizard)
**Primary user:** DPA RW; FM read + step 7 sign-off authority.
**Purpose:** List vessels currently in onboarding + entry to start a new onboarding.

**Layout:**
- Header: "New vessel onboarding" CTA (DPA only) → `/certs/onboarding/new`.
- Table: vessels with `lifecycle_status = onboarding_in_progress`. Columns: vessel name, IMO, current step (1–7), batches uploaded, mandatory coverage %, pending FM sign-off (yes/no), last activity, started_at, started_by.
- Toolbar: filter by step; sort by mandatory-coverage %.

**Surfaces (FIELD_MAP):** `master_vessel.lifecycle_status`, `vims_certs_batch_ingest.*` aggregates, mandatory-coverage computed metric.

**4 states:** standard. Empty = "No onboardings in progress."

**Navigation:** Row click → `/certs/onboarding/<imo>`.

---

### 3.7 Onboarding Wizard `/certs/onboarding/<imo>` (7 steps)

**Route:** `/certs/onboarding/<imo>` (with `?step=N` query param for direct step entry; defaults to first incomplete step)
**Form ID:** `CERT_F_005`
**Process IDs:** `CERT_P_001` (Create), `CERT_P_002` (Submit), `CERT_P_010` (Rollback)
**Primary user:** DPA throughout; FM signs off at step 7.
**Purpose:** Per-vessel onboarding per D-CERT-120 (FEAT-CERT-WIZ-001).

**Stepper bar (top):** 7 steps, current highlighted, completed checkmarked, locked (greyed) until prerequisites met.

**Step 1 — Vessel selection** (D-CERT-120, FEAT-CERT-WIZ-002)
- Pick from `master_vessel` OR "Create new vessel" form (mini-flow that writes a new `master_vessel` row).
- Surfaces: `master_vessel.vessel_name`, `imo_number`, `flag_state`, `class_society`, `ship_type`.

**Step 2 — Vessel profile setup** (D-CERT-120, FEAT-CERT-WIZ-003)
- Form fields: `anniversary_date` (mandatory; this is the load-bearing anchor per D-CERT-074 / FEAT-CERT-TRK-007), `ship_type` (multi-select), current `master_user_id`, `marine_supt_user_id`, `technical_manager_user_id` (D-CERT-098 / FEAT-CERT-RBAC-021).
- Pending cert rows pre-populated from `applicable_ship_types[]` filter on catalog (D-CERT-109 / FEAT-CERT-WIZ-004); shown as a count: "N mandatory cert types match this ship type — these will be pre-created for you."
- "Save and continue" advances to step 3.

**Step 3 — Cert PDF batch ingest** (D-CERT-104, D-CERT-112, D-CERT-115, D-CERT-116, D-CERT-117, D-CERT-118, D-CERT-122, D-CERT-123, FEAT-CERT-WIZ-005 → FEAT-CERT-WIZ-013)
- Layout:
  - Drop zone for ≤10 PDFs at a time (D-CERT-104). Vessel-locked context shown ("Uploading for: <vessel name>"); PDFs landing here will be assumed to belong to this vessel (D-CERT-112).
  - Active batches list: each batch shows status (queued / OCR running / ready for review / committed / cancelled), PDF count, last activity.
  - "Save & resume later" (multi-day onboarding per D-CERT-104).
- Per-batch action row:
  - **Ready for review** → "Review batch" button → opens Gap-Fill UI (§3.8).
  - **Committed** → "View summary" button (loads CSV report per D-CERT-117).
  - **Cancelled** → audit trail kept; rollback occurred per D-CERT-115.
- "Mark all PDFs uploaded" advances to step 4.

**Step 4 — Class Status Report upload + reconciliation** (D-CERT-100, D-CERT-110, D-CERT-120, FEAT-CERT-WIZ-014, FEAT-CERT-WIZ-015)
- Upload class status PDF (NK / KR / BV — auto-detected from format).
- Parser runs per FEAT-CERT-REC-002; results land in reconciliation panel.
- Anniversary cross-validation: if DPA-entered anniversary disagrees with class report's implied dates, surface in panel (FEAT-CERT-WIZ-015 / D-CERT-110).

**Step 5 — Reconciliation review** (D-CERT-068, D-CERT-120, FEAT-CERT-WIZ-016)
- Embedded three-panel reconciliation UI (mirrors §3.10) scoped to this onboarding's snapshot.
- DPA resolves Mismatches / Unmapped / Missing-in-Catalog / Missing-in-Class buckets.
- "All resolved" advances to step 6.

**Step 6 — Coverage gate** (D-CERT-119, FEAT-CERT-WIZ-017)
- Compute coverage of `mandatory_for_all_vessels=true` cert types vs vessel's onboarded TrackedItems.
- ≥100%: "Ready to enable. Click to auto-enable alerts." button.
- <100%: list missing certs; require DPA written reason in textarea (e.g. "X cert being re-issued, expected by date Y") to override; override audit-logged + visible on vessel dashboard until coverage = 100%.

**Step 7 — FM sign-off** (D-CERT-120, FEAT-CERT-WIZ-018)
- Summary screen: vessel name, IMO, total certs onboarded, coverage %, override reason (if any), batches committed, in-flight items, anniversary date, key personnel.
- FM clicks "Sign off — vessel goes live" button (FM `CERT_P_002` on this screen).
- On commit: `master_vessel.lifecycle_status = active`; alerts begin firing forward-looking only (D-CERT-173 / FEAT-CERT-WIZ-022); welcome notification dispatched to Master.

**Cross-step:**
- "Reset onboarding for this vessel" button (DPA only, visible all steps until step 7 commit) → soft-deletes wizard-created rows + PDFs + batches; vessel returns to step 1; full audit trail (D-CERT-124 / FEAT-CERT-WIZ-019).

**Surfaces (FIELD_MAP):** `vims_certs_batch_ingest.*`, `vims_certs_class_status_snapshot.*`, `vims_certs_reconciliation_run.*`, anniversary cross-validation diff structure, coverage computation result, FM sign-off event row in `vims_certs_audit_log`.

---

### 3.8 Gap-Fill UI `/certs/onboarding/<imo>/batch/<batch_id>/gap-fill`

**Route:** `/certs/onboarding/<imo>/batch/<batch_id>/gap-fill`
**Form ID:** `CERT_F_005`
**Primary user:** DPA.
**Purpose:** Per-batch PDF-by-PDF metadata correction; commits the batch.

**Layout:**
- Header: batch ID, vessel name, PDF count, "Cancel batch" + "Commit batch" buttons.
- PDF carousel: navigable list of PDFs in batch; current selection highlighted.
- Two-pane main:
  - **Left:** PDF preview (zoomable, scrollable).
  - **Right:** auto-filled form per FEAT-CERT-OCR-002 fields — required fields enforced per D-CERT-105:
    - `certificate_type` (dropdown bound to catalog `display_name`; "Create new catalog row" inline button per D-CERT-122 / FEAT-CERT-CAT-016 / FEAT-CERT-WIZ-012)
    - `issuing_authority` (dropdown + free text)
    - `vessel_name` (auto-filled from selected vessel)
    - `imo_number` (auto-filled from selected vessel; OCR mismatch surfaces warning per D-CERT-112 — does NOT auto-reroute)
    - `issue_date`, `expiry_date` (or "Permanent" toggle)
    - `certificate_number` (with "No cert number on document" bypass + reason per D-CERT-105 / FEAT-CERT-OCR-003)
    - `place_of_issue`
    - Optional: last surveys, conditions/restrictions, signature/issuing officer.
  - Per-field highlight by confidence band (FEAT-CERT-OCR-005):
    - ≥80% (auto-filled, low-key — black text on white)
    - 60–80% (yellow background, "Verify" hint, OCR best-guess pre-filled)
    - <60% (red border, blank, "Could not read — please enter manually")
  - Whole-doc unprocessable flag → orange banner top of right pane: "OCR could not process this PDF. Please enter all fields manually." All fields blank.
- Top-right of right pane: per-PDF status — "Ready" (all required filled) / "Incomplete" (required missing) / "Bypassed" (cert_number bypass active).
- "Save & next" within carousel.
- "Commit batch" button — runs validation gates per D-CERT-116:
  - **Blocks** if any: required field missing on any PDF; cert_number bypass without reason; OCR'd IMO unresolved against any vessel; validity type undetermined; cert issue date in future; cert duplicate within batch (same cert_number on two PDFs).
  - **Warns but allows** if any: pdf_missing rows; issuer type undetermined; expiry in past (already-expired at onboarding → quarantine per D-CERT-121); two cert rows for same catalog_id on same vessel (legitimate cases).
  - On commit: dry-run preview (D-CERT-115 / FEAT-CERT-WIZ-008) — "This batch will create N rows + M PDF attachments. Review and confirm." Cancel = full rollback (no DB writes). Commit = writes + generates `batch_ingest_<imo>_<yyyymmddhhmm>.csv` (D-CERT-117 / FEAT-CERT-WIZ-010).
- Re-import idempotency: SHA-256 dedup on PDF (D-CERT-118 / FEAT-CERT-WIZ-011); silent skip with audit if already attached; supersede prompt if same cert_number + different content.

**Surfaces (FIELD_MAP):** Every field above maps to `vims_certs_tracked_item` columns + `vims_certs_pdf_blob` insert + `vims_certs_batch_ingest.report_csv_blob_id` ref + `vims_certs_audit_log` entries.

---

### 3.9 Reconciliation Dashboard `/certs/reconciliation`

**Route:** `/certs/reconciliation`
**Form ID:** `CERT_F_003` (Reconciliation)
**Primary user:** Marine Sup'tt (primary reviewer per D-CERT-068); DPA / FM / TS / TM read.
**Purpose:** All reconciliation runs across fleet, filterable; entry to per-run review.

**Layout:**
- Filter bar (D-CERT-069 / FEAT-CERT-REC-023): vessel, class society, date range, parse_status, has_unresolved_mismatches.
- Table (default sort `printed_on_date DESC`, pagination 25):
  - Columns: vessel, class society, snapshot date, parse status, parser version, matches count, mismatches count, missing-in-catalog count, missing-in-class count, conditional/STC detected, extended/postponed detected, unresolved flags, last reviewed by + when.
- Per-row action: "Review" → §3.10. "Re-parse with current mapping" (manual, D-CERT-061).
- "Export filtered list as CSV" button.

**Surfaces (FIELD_MAP):** `vims_certs_reconciliation_run.*` columns, joined `vims_certs_class_status_snapshot`, joined `vims_certs_class_code_mapping.version`.

---

### 3.10 Reconciliation Review (3-panel) `/certs/reconciliation/<run_id>`

**Route:** `/certs/reconciliation/<run_id>`
**Form ID:** `CERT_F_003`
**Primary user:** Marine Sup'tt.
**Purpose:** Per-run review of class snapshot reconciliation; resolve mismatches / unmapped (per D-CERT-068 / FEAT-CERT-REC-022).

**Layout:**
- Header: vessel, class society, snapshot date, parser version, status counts, "Open original Class Status PDF" button (D-CERT-148 / FEAT-CERT-PRT-031).
- Tabs: **Matches** (audit only, no action) / **Mismatches** / **Missing in Catalog** / **Missing in Class** / **Conditional/STC detected** / **Extended/Postponed detected** / **Unmapped (low confidence)**.
- Per-tab: side-by-side per-row diff panel:
  - Left: catalog/TrackedItem state.
  - Right: class snapshot extracted state.
  - Highlighted diff fields.
  - Action buttons: `[Notify Master to update]` (sends per-side routed alert per D-CERT-161; vessel side gets in-app+email, office side gets in-app+Slack), `[Mark as reviewed]` (records reviewer + timestamp; for matches/audit rows), `[Resolve via Master upload]` (creates a pending TrackedItem update awaiting Master per D-CERT-008), `[Add to ClassCodeMapping]` (DPA only, opens mapping editor per D-CERT-061).
- Anomaly banner at top if D-CERT-073 / FEAT-CERT-REC-031 thresholds breached (mismatch_rate > 15%, parse_time > 3min, count < expected×0.7).

**Special handling:**
- `Conditional/STC detected` → pre-fills an STC TrackedItem form (`relationship_type=short_term_for`, linked to parent) per D-CERT-008 / D-CERT-012; Master confirms + uploads PDF.
- `Extended/Postponed detected` → for NK Extended → child `extension_of` row pre-fill; for NK Postponed → parent's `postponed_until` field pre-fill (D-CERT-065 / FEAT-CERT-REC-024).

**Surfaces (FIELD_MAP):** `vims_certs_reconciliation_flag.*`, joined `vims_certs_tracked_item`, parsed_payload field paths from `vims_certs_class_status_snapshot.parsed_payload_json`.

---

### 3.11 Print Builder `/certs/print`

**Route:** `/certs/print`
**Form ID:** `CERT_F_004` (Print/Export)
**Process ID:** `CERT_P_005` (Print)
**Primary user:** Master own vessel; DPA + FM full fleet; Sup'tts assigned vessels (D-CERT-142 / FEAT-CERT-PRT-023).
**Purpose:** Configure + generate print artifacts (PDF + Excel companion) per FEAT-CERT-PRT-001 → FEAT-CERT-PRT-033.

**Layout:**
- Step 1 — **Choose scope** (D-CERT-140 / FEAT-CERT-PRT-020):
  - Per-vessel full (single vessel, all 9 sections, all rows — default)
  - Per-vessel partial (single vessel, filtered by section / status / cadence)
  - Per-section fleet-wide (single section, all vessels — DPA + FM only per D-CERT-141 / FEAT-CERT-PRT-021)
  - Custom selection (multi-select cert rows from in-scope vessels)
- Step 2 — **Filters & options:** sections, status bands, cadence, vessel pickers (depending on scope); watermark toggle (DPA can override default scope-driven watermark per D-CERT-138 / FEAT-CERT-PRT-018); recipient field (optional, opt-in email per D-CERT-149 / FEAT-CERT-PRT-032).
- Step 3 — **Preview & generate:** sample first page rendering with `print_id` placeholder; "Generate" button.
- During generation: progress bar for sync per-vessel scope ("Generating PDF (page X of Y)…", hard cap 60s per D-CERT-144 / FEAT-CERT-PRT-025); for fleet-wide async, "Submitted — you'll be notified when ready" + queue position.
- On success: download buttons (PDF + Excel companion); confirmation that artifact is auto-archived in vessel-scoped "Archived Reports" folder; if recipient email entered, "Email sent to <addr>".

**Throttling:** Soft-throttle surface at >10/hour per user → audit log entry "high-volume print activity by user X" surfaces in FM dashboard for governance review (D-CERT-143 / FEAT-CERT-PRT-024); no hard block.

**Surfaces (FIELD_MAP):** `vims_certs_print_artifact.*` — print_id, scope, vessels[], sections[], system_state_hash, user_id, role, timestamp_utc, watermark_applied, page_count, pdf_blob_id, excel_blob_id, recipient_email (nullable).

---

### 3.12 Print History `/certs/print/history`

**Route:** `/certs/print/history`
**Form ID:** `CERT_F_004`
**Primary user:** Per role; "Archived Reports" per vessel scope.
**Purpose:** Re-fetch past print artifacts without re-printing.

**Layout:**
- Filter bar: vessel, scope, date range, watermark, recipient, user.
- Table: print_id, generated_at, scope, vessels, watermark, user, page count, recipient (if any), download buttons (PDF + Excel).
- Per-row: "View audit entry" link.

**Surfaces (FIELD_MAP):** `vims_certs_print_artifact.*` plus joined `vims_certs_audit_log`.

---

### 3.13 Master Share-Bundle `/certs/share-bundle`

**Route:** `/certs/share-bundle`
**Form ID:** `CERT_F_004`
**Process ID:** `CERT_P_006` (Export Bundle)
**Primary user:** Master own vessel; DPA + FM full fleet (D-CERT-142).
**Purpose:** Generate ZIP bundle (manifest PDF + cert PDFs) for outbound distribution to charterers / port agents / vetting / P&I (D-CERT-145 / FEAT-CERT-PRT-026).

**Layout:**
- Vessel picker (own vessel for Master; any for DPA/FM).
- Cert selection table: bulk + single multi-select (D-CERT-096 / FEAT-CERT-PRT-027) with section grouping, expiry status visible.
- Recipient name field (optional; populates `MASTER COPY` watermark recipient per D-CERT-138).
- "Generate ZIP" button → `VIMS_CertBundle_<vessel_name>_<yyyymmdd>_<print_id>.zip` (D-CERT-145 / FEAT-CERT-PRT-028).
- Inside ZIP: manifest PDF (cert title, issuer, issue date, expiry, file reference) + cert PDFs.

**Surfaces (FIELD_MAP):** Same `vims_certs_print_artifact` table with `bundle_zip_blob_id` extension; `vims_certs_audit_log` entry per generation.

---

### 3.14 Notification Inbox (shared bell + Certs filter)

**Route:** Shared platform `/notifications` (existing); Certs filter via `module=certs` query.
**Primary user:** All Certs roles see their own inbox.
**Purpose:** Single bell-icon inbox across VIMS modules per D-CERT-151; Certs entries surfaced via `vims_certs_notification_meta` joined to `master_notification.id`.

**Layout (Certs-relevant rows):**
- Row format: trigger event (e.g. "Cert expiring in 14 days"), vessel, cert name, days_to_go, action buttons ([Renew] / [Acknowledge] — magic-link backed for email per D-CERT-154 / FEAT-CERT-NOTIF-008).
- Grouped multi-cert alerts (D-CERT-164 / FEAT-CERT-NOTIF-025) collapse a single card listing N affected certs.
- Per-side routing visible: vessel users see no Slack rows; office users see no email rows (D-CERT-161 / FEAT-CERT-NOTIF-003).
- Filters: vessel, cert section, severity, ack status, date range.

**Surfaces (FIELD_MAP):** `master_notification.*` + `vims_certs_notification_meta.*` + ack metadata.

---

### 3.15 External Auditor Provisioning `/certs/auditor-access`

**Route:** `/certs/auditor-access`
**Form ID:** `CERT_F_007` (External Auditor Provisioning)
**Process ID:** `CERT_P_007` (Provision Auditor)
**Primary user:** Marine Sup'tt primary (D-CERT-194 / FEAT-CERT-EXT-002); DPA override.
**Purpose:** Grant time-bound, scoped read-only access to external auditors (D-CERT-096 / FEAT-CERT-EXT-001).

**Layout:**
- Active grants table: auditor name, auditor email, vessel scope (chips), section/category scope, expiry, granted_by, granted_at, last_accessed_at, status (active / expired).
- "New grant" button → modal:
  - Fields: auditor name, auditor email, vessels (multi-select), cert section/category scope (multi-select), optional individual cert IDs, expiry (default 7 days; max 30 days, DPA-extendable per D-CERT-096 / FEAT-CERT-EXT-004).
  - On submit: system emails auditor a one-time-use signup link (D-CERT-194); audit log captures grant event with provisioner identity.
- No "Revoke" button — auto-expire only per D-CERT-195 / FEAT-CERT-EXT-005. To effectively revoke: edit expiry to past timestamp (audit-logged).

**Surfaces (FIELD_MAP):** `vims_certs_external_auditor_access.*` — grant_id, auditor_name, auditor_email, scope_json, expiry_at, granted_by, granted_at, last_accessed_at, signup_token_used (bool), revoked_via_expiry_edit (bool).

---

### 3.16 Auditor Access Detail `/certs/auditor-access/<grant_id>`

**Route:** `/certs/auditor-access/<grant_id>`
**Form ID:** `CERT_F_007`
**Primary user:** Marine Sup'tt + DPA.
**Purpose:** View / extend / shorten a specific grant.

**Layout:**
- Grant metadata as per §3.15 row.
- Edit form (Marine Sup'tt + DPA only): expiry editable; everything else immutable post-creation (revoke a grant → create a new one).
- **NO activity log** per D-CERT-196 / FEAT-CERT-EXT-006: read sessions are opaque.
- Audit log shows: grant creation, expiry edits, signup token usage event (used: yes/no).

**Surfaces (FIELD_MAP):** Same as §3.15.

---

### 3.17 Audit Log Read `/certs/audit-log`

**Route:** `/certs/audit-log`
**Form ID:** `CERT_F_008` (Audit Log)
**Primary user:** DPA + FM full fleet; Sup'tts own-vessel slice (D-CERT-091 / FEAT-CERT-AUDIT-004).
**Purpose:** Read-only browse of audit entries; export by DPA only.

**Layout:**
- Filter bar: vessel, actor (user), entity type (catalog row / TrackedItem / class snapshot / approval event / print artifact / auditor grant), action (create/update/delete/approve/reject/print/grant), date range, RBAC-scoped automatically.
- Table: timestamp UTC, vessel, actor (name + role), action, entity ref (clickable to entity detail), before/after diff (expandable JSON), event_metadata.
- Hot tier (<2y) loads instantly; cold tier (2–5y) prompts "This range includes archived entries (cold storage). Fetch may take ~30s — Continue?" per D-CERT-183 / FEAT-CERT-AUDIT-003.
- "Export filtered as PDF" / "Export filtered as CSV" — DPA only, watermarked (D-CERT-091 / FEAT-CERT-AUDIT-005).

**Surfaces (FIELD_MAP):** `vims_certs_audit_log.*` — timestamp_utc, vessel_id, actor_user_id, actor_role, action, entity_type, entity_id, before_json, after_json, event_metadata, retention_tier (hot/cold).

**Special:** Free-text reason fields shown verbatim to DPA + FM + scope-matching Sup'tts; redacted to `[REDACTED — internal note]` for any external auditor view (D-CERT-180 / FEAT-CERT-AUDIT-007). External auditors do NOT see this screen at all (out of scope per portal §3.20).

---

### 3.18 Vessel Profile (Certs context) `/certs/vessels/<imo>/profile`

**Route:** `/certs/vessels/<imo>/profile`
**Form ID:** `CERT_F_002`
**Primary user:** DPA + FM RW; Sup'tts R; Master R own.
**Purpose:** View / edit vessel-level Certs config.

**Layout:**
- Identity (read-only from `master_vessel`): name, IMO, flag, class society, ship type, build year.
- Certs-specific config (RW for DPA + FM):
  - `anniversary_date` (rare-edit; audit-required confirm dialog per D-CERT-074)
  - `master_user_id`, `marine_supt_user_id`, `technical_manager_user_id` (D-CERT-098 / FEAT-CERT-RBAC-021)
  - Per-vessel Slack channel routing (DPA only per D-CERT-160 / FEAT-CERT-NOTIF-020)
  - `lifecycle_status` indicator (active / onboarding_in_progress / pending_disposal per D-CERT-044)
  - Class change workflow trigger (DPA per D-CERT-046 / FEAT-CERT-LIFE-004)
  - Flag change event log (DPA records per D-CERT-094 / FEAT-CERT-LIFE-009)
  - "Initiate sale handover" button (DPA only, opens 30-day handover flow per D-CERT-093 / FEAT-CERT-LIFE-006)
- Banners (per state):
  - "Pending statutory re-upload after flag change" (D-CERT-094)
  - "Mandatory coverage <100% — override active. Reason: X" (D-CERT-119)
  - "Pending disposal — N days remaining" (D-CERT-044)

**Surfaces (FIELD_MAP):** `master_vessel.*` (Certs-relevant subset), `vims_certs_vessel_config.*` (per-vessel Slack routing, anniversary-edit history, flag-change events, sale-handover events).

---

### 3.19 Settings `/certs/settings`

**Route:** `/certs/settings`
**Form ID:** `CERT_F_006` (Notification Config) + system admin overlay.
**Primary user:** DPA only.
**Purpose:** Module-wide config (alert lead times, OCR thresholds, parser version, retention overrides).

**Layout (tabs):**
- **Alert lead times** — DPA-configurable per cadence (D-CERT-006, D-CERT-016).
- **OCR thresholds** — tunable office (default 80) + vessel (default 85) per D-CERT-106 / D-CERT-168 / FEAT-CERT-OCR-012.
- **Parser version** — current per class, manual re-parse trigger (D-CERT-052 / FEAT-CERT-REC-009).
- **Retention overrides** — per-blob extension (D-CERT-021 / FEAT-CERT-BLOB-007).
- **Class snapshot upload cadence** — default 3 months, lead 1 month (D-CERT-006).
- **Slack channel routing per vessel** — central per D-CERT-160 (also surfaced on vessel profile §3.18).

**Surfaces (FIELD_MAP):** `vims_certs_alert_config.*`, `vims_certs_settings.*` (or analogous structured config table; deferred to BACKEND_STRUCTURE).

---

### 3.20 External Auditor Portal `/auditor/<grant_token>/...`

**Routes:**
- `/auditor/<grant_token>/` — landing, scope summary, vessel list within scope.
- `/auditor/<grant_token>/vessels/<imo>` — vessel cert dashboard (filtered to scope; mirrors §3.4 with redactions).
- `/auditor/<grant_token>/cert/<tracked_item_id>` — TrackedItem detail (read-only; mirrors §3.5 with redactions; PDF preview + download enabled).
- `/auditor/<grant_token>/print` — generate AUDIT COPY watermarked print (D-CERT-138 / FEAT-CERT-EXT-010).

**Auth:** Token-based (signed, expiry-bound per `vims_certs_external_auditor_access.expiry_at`); separate from main JWT auth. No federated SSO across modules (D-CERT-178 / FEAT-CERT-EXT-009).

**Restrictions:**
- Read-only everywhere.
- Free-text reason fields redacted to `[REDACTED — internal note]` per D-CERT-180.
- No audit-log screen.
- No cross-module navigation (per-module only per D-CERT-178).
- No activity tracking (D-CERT-196 / FEAT-CERT-EXT-006) — but the grant event itself was logged at provisioning.
- Print outputs always carry `AUDIT COPY` watermark + auditor name + access-expiry per D-CERT-138.

**Surfaces (FIELD_MAP):** Same as §3.4, §3.5 minus redacted columns. Tracked separately in FIELD_MAP "External Auditor Surface" section to make redaction obligations explicit.

---

## 4. Cross-Screen Navigation Map

```
Fleet Dashboard ──┬─→ Vessel Cert Dashboard ──┬─→ TrackedItem Detail
                  │                            ├─→ Vessel Profile
                  │                            └─→ Reconciliation Dashboard (filtered)
                  ├─→ Reconciliation Dashboard ──→ Reconciliation Review
                  ├─→ Onboarding Hub ──→ Onboarding Wizard ──→ Gap-Fill UI
                  │                                          ↘ embeds Reconciliation Review (step 5)
                  ├─→ Catalog Admin ──→ Catalog Row Detail ──→ TrackedItem Detail (per instance)
                  ├─→ Print Builder ──→ Print History
                  ├─→ Master Share-Bundle ──→ Print History (bundle entries)
                  ├─→ Auditor Access ──→ Auditor Access Detail
                  ├─→ Audit Log Read
                  ├─→ Settings
                  └─→ Notification Inbox (shared bell)

Notification deep-link → directly into TrackedItem Detail OR Reconciliation Review (per trigger event).
Magic-link email → /certs/notifications/ack/<token> → backend ack → redirect to TrackedItem Detail.

External Auditor Portal is a separate root tree; never navigates back into main /certs/* routes.
```

---

## 5. 11-State Contract per Screen

> **Amended 2026-06-12 (v1.1 — KLOSS Step 2 realignment):** the framework's base state set grew from 4 to 11 (adds PERMISSION_DENIED, OFFLINE, PARTIAL_DATA, RATE_LIMITED, SESSION_EXPIRED, MAINTENANCE, ROUTE_GUARD). The original 4 states below are unchanged. Inline "**4 states:** standard" references in §3 screen sections now resolve to THIS 11-state contract — the 7 added states apply module-wide via this table; per-screen deviations are listed in §5.1. The 5 mobile-only states (BACKGROUND, DEEP_LINK, PERMISSION_PROMPT, PERMISSION_DENIED_OS, OFFLINE_FIRST) are **N/A — Platform: WEB** (TECH_STACK.md).

Every screen MUST implement all 11 states (or inherit the module-wide N/A). Standard pattern:

| State | UI behavior |
|-------|------------|
| **LOADING** | Skeleton placeholder matching final layout; no spinner-on-blank-page. Use shadcn `Skeleton` primitive. |
| **SUCCESS (Loaded)** | Final content rendered. Empty filtered subsets fall under "Empty (filtered)" sub-state — show "No results — reset filters" CTA. |
| **EMPTY (true zero state)** | Encouraging copy + primary CTA. Examples: "Vessel not yet onboarded — start wizard", "No certs in this section yet — add the first one", "No reconciliation runs yet — upload a class snapshot to begin." |
| **ERROR** | Inline error banner at top of content area: "Could not load <X>. <Retry>". Audit log captures fetch failure for ops surfacing on DPA dashboard. NEVER blank page; NEVER silent fail. |
| **PERMISSION_DENIED** | Authenticated but role lacks the screen's `CERT_F_*`/`CERT_P_*` permission (§2 matrix): action surfaces (buttons, tabs, nav entries) are **hidden, not disabled-with-tooltip**, per the role-permission matrix. Field-level redaction follows D-CERT-180 (external auditor sees `[REDACTED — internal note]`). Direct API access without permission returns 403. ✅ **RESOLVED (B-FLOW-01, 2026-06-12):** URL-navigation to an unauthorized route renders a full-screen 403 page — "You don't have access to this page." + primary CTA **[Back to Fleet Dashboard]** (`/certs`). No request-access flow in V1. |
| **OFFLINE** | **N/A — online-required architecture (D-CERT-156, Starlink fleet).** Network failure renders the ERROR state; transient drops ride the `master_notification` server-side queue and the D-CERT-082 re-auth modal's HTTP-level resilience. No offline UI exists by locked decision. |
| **PARTIAL_DATA** | Module-wide policy: screens render **per-panel**, not all-or-nothing — a failed panel shows its own inline ERROR banner (+retry) while sibling panels render (e.g. §3.5 metadata loads, PDF preview fails → preview-pane error only). No silent omission of failed panels — every failed fetch is visible per the ERROR contract. |
| **RATE_LIMITED** | **N/A — no hard rate limiting exists in V1** (✅ confirmed by B-SEC-11 resolution, 2026-06-12: no DRF throttling). Print throttle is a soft audit-log signal, never a user-facing block (D-CERT-143); batch caps (≤10 ingest D-CERT-104, ≤50 bulk-delete D-CERT-092) surface as **validation errors**, not 429s. |
| **SESSION_EXPIRED** | **Fully specified by D-CERT-082:** PMS-style modal overlay (NOT redirect); form state preserved; identifier pre-filled (CrewID vessel / Employee ID office); 15-min and 5-min toast warnings precede idle expiry (8h office / 24h vessel). External Auditor Portal (§3.20) differs — see §5.1. |
| **MAINTENANCE** | ✅ **RESOLVED (B-FLOW-02, 2026-06-12):** platform-level static maintenance page (served at the Nginx layer so it works with Django down): "VIMS is under scheduled maintenance." + ETA line when known. **DPA-triggered** (coordinated with corporate IT); not module code — Certs inherits whatever VIMS-wide static page exists, and one MUST exist before Phase 9 cutover (Phase 8 checklist item). Unplanned outages still render the ERROR state. |
| **ROUTE_GUARD** | ✅ **RESOLVED (B-FLOW-03, 2026-06-12):** logged-out user hitting any `/certs/*` route → **redirect to platform login preserving the full target URL as return-to; restore navigation to it after successful login** (extends the `ssot_auth_specific.md` §10 session-rehydration pattern). Wrong-role users on a valid session fall under PERMISSION_DENIED above. External Auditor Portal routes (`/auditor/<grant_token>/...`) are token-guarded, render the terminal expired/invalid screen (§5.1), and never link back into `/certs/*` (§4). |

### 5.1 Per-Screen State Deviations

Screens not listed here implement the standard 11-state contract exactly.

| Screen | Deviation |
|--------|-----------|
| §3.5 TrackedItem Detail | Adds domain banners ON TOP of the contract (see "Special states" below); PARTIAL_DATA per-panel split = metadata / PDF preview / workflow+audit panes. |
| §3.11 Print Builder | Generation progress bar with ETA (≤60s sync, ≤5min fleet async per D-CERT-144); generation failure = ERROR with retry; soft print-throttle is invisible to user (D-CERT-143). |
| §3.17 Audit Log Read | Cold-tier (2–5y) rows load on explicit prompt (D-CERT-183) — that prompt is a SUCCESS-state affordance, not LOADING. External-auditor view applies D-CERT-180 redaction (PERMISSION_DENIED at field level). |
| §3.20 External Auditor Portal | SESSION_EXPIRED ≠ D-CERT-082 modal: grant token is signed + expiry-bound; an expired/exhausted grant shows a terminal "Access expired — contact the DPA" screen (no re-auth path, no early revocation per D-CERT-195). ROUTE_GUARD: invalid/expired token = same terminal screen; portal never redirects into `/certs/*`. |
| §3.7 Onboarding Wizard / §3.8 Gap-Fill | SESSION_EXPIRED mid-wizard relies on D-CERT-082 form-state preservation — wizard step state MUST survive the re-auth modal (explicit test target). |

**Special states:**
- `expired_at_onboarding` quarantine banner on TrackedItem Detail (§3.5).
- `pdf_missing: true` red banner on TrackedItem Detail (§3.5).
- `lifecycle_status = pending_disposal` countdown banner on Vessel Profile + Vessel Cert Dashboard.
- `onboarding_in_progress` "Resume wizard" CTA on Vessel Cert Dashboard.
- `mandatory_coverage < 100%` override banner on Vessel Cert Dashboard until coverage reaches 100% (D-CERT-119).
- `flag_change_event` open → "pending statutory re-upload" banner on Vessel Profile + Vessel Cert Dashboard (D-CERT-094).

---

## 6. Mobile / Tablet Adaptation

**Primary devices:**
- Office: desktop (DPA / FM / Sup'tts / TM workflow).
- Vessel: bridge tablet (Master flows for cert renewal upload, approval, share-bundle creation).

**Tablet layout adjustments:**
- TrackedItem Detail (§3.5) — 3-column desktop collapses to stacked vertical sections (Metadata → PDF preview → Workflow + audit). PDF preview stays full-width; pinch-zoom enabled.
- Vessel Cert Dashboard (§3.4) — section accordion; per-section table becomes per-row card on narrow screens.
- Onboarding Wizard (§3.7) — DPA primarily desktop; not optimized for mobile (acceptable scope).
- Master upload flow (§3.5 PDF upload + §3.13 Share Bundle) — fully tablet-optimized; bridge-scanner integration via standard browser file API (D-CERT-166 / FEAT-CERT-OCR-013).
- Notification inbox (§3.14) — mobile-responsive (Master may receive in-app + email per D-CERT-161 routing).
- External Auditor Portal — desktop primary; tablet acceptable; mobile read-only acceptable.

**Phone form factor:** acknowledge-via-magic-link (email tap) is the only intentional mobile UX path. Full app on phone is not a target.

---

*End of APP_FLOW v1.0. Cross-references: every "Surfaces" line above maps into FIELD_MAP.md (synthesis doc). Field bindings are authoritative there; this doc is the screen contract.*

---

## Appendix — Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `APP_FLOW.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` ✓ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-004 | Fleet-wide office-controlled master catalog. | LOCKED |
| D-CERT-007 | Event-driven class snapshot refresh prompt when any `is_class_tracked: true` row is updated. | LOCKED |
| D-CERT-009 | Source-of-truth tie-breaker: Class is always authoritative for class-tracked certs. | LOCKED |
| D-CERT-011 | Rich date fields: issue/expiry/anniversary/window_open/window_close/last_done/next_due/postponed_until. | LOCKED |
| D-CERT-013 | Extensions: separate row, `relationship_type ∈ {extension_of, dispensation_for}`, `extension_authority ∈ {class, flag}`. | LOCKED |
| D-CERT-079 | Submission scope by catalog row: new field `submission_scope`. | LOCKED |
| D-CERT-101 | OCR-based PDF auto-matching to cert rows. | LOCKED |
| D-CERT-111 | IMO sourcing & vessel-cert binding. | LOCKED |
| D-CERT-128 | Print identifiability — full audit trail in footer: Each printed page footer contains: (a) print date + time UTC, (b) print use... | LOCKED |
| D-CERT-171 | Catalog change fan-out = aggregate office + per-vessel Master. | LOCKED |
