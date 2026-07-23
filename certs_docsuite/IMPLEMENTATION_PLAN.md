# VIMS Certificates Module — Implementation Plan (FROZEN)

> **Version:** 1.2
> **Last Updated:** 2026-06-12 (v1.2 — closure session: step 0.3 gains `vims_jobs` role; NEW steps 6.7 heartbeat dead-man alert + 8.5 security-review/maintenance-page exit gates; resolved-blocker references inlined. v1.1 — per-step **Traceability** blocks per KLOSS Step 2 framework rev 2026-05-27; step 0.4 corrected 18→19 tables (D-AUDRS-237/239). Build has NOT started; the freeze rule applies from Phase 0 kickoff. v1.0: 2026-05-13)
> **Status:** Locked — FROZEN. State lives in `progress.txt`. Do NOT modify this doc post-lock.
> **Source:** All other DocSuite docs.
> **Pattern:** Mirrors VIMS-Safety-Module/IMPLEMENTATION_PLAN.md phasing.
> **Traceability convention:** every step carries a Traceability line across 8 layers — PRD / APP_FLOW / FIELD_MAP / BACKEND / DESIGN_SYSTEM / FRONTEND_GUIDELINES / SECURITY (SEC-CERT-\* via `SECURITY.md` §14, cited by D-CERT) / OBSERVABILITY (OBS-CERT-\* via `OBSERVABILITY.md` §9, cited by audit action). "—" = layer genuinely untouched. Audit action names follow BACKEND_STRUCTURE §3.9; where a cited action is not yet in the §3.9 enum, adding it (with FIELD_MAP cascade) is part of that step's scope. A step whose Traceability line no longer resolves = stale plan → STOP (CLAUDE.md Traceability Enforcement).

---

## Phase 0 — Scaffold (Week 1)

**Goal:** apps/certs Django app exists, runs, no business logic.

| Step | Output | Tests | Dependencies |
|------|--------|-------|--------------|
| 0.1 | `apps/certs/` skeleton (apps.py, urls.py, models/__init__.py, empty admin.py) | App registers without error | — |
| 0.2 | `INSTALLED_APPS` += `apps.certs`; URL mount `/api/certs/` | smoke endpoint `/api/certs/health/` returns 200 — this IS the module health contract (OBS-CERT-12): later returns `{status, last_cadence_heartbeat}` once 6.7 lands | 0.1 |
| 0.3 | DB role separation provisioned — THREE roles (B-FM-03 resolution): `vims_app` (INSERT+SELECT only on audit/event tables), `vims_admin` (migrations only), **`vims_jobs`** (UPDATE on retention columns + 5y-purge DELETE, scheduled tasks only — SEC-CERT-16) | Manual GRANT verification incl. vims_jobs scope | 0.1 |
| 0.4 | Migration `0001_initial.py` — all 19 `vims_certs_*` tables per BACKEND_STRUCTURE §3 (incl. `cert_change_log` §3.19, D-AUDRS-237/239) | Migration runs forward + backward cleanly on dev DB | 0.3 |
| 0.5 | Seed mgmt commands: `seed_catalog_sections`, `seed_certs_permissions` | `manage.py seed_catalog_sections` writes 9 rows; `seed_certs_permissions` writes CERT_F_* + CERT_P_* into msc_profiles | 0.4 |
| 0.6 | Frontend route `/certs/` stub renders "Certs module coming soon" | Renders without console errors; permission check works | 0.2 |
| 0.7 | OCR engine pick + wrapper interface in `services/ocr_pipeline.py` (per TECH_STACK §15.1) | Mock + real engine both pass interface test | 0.4 |
| 0.8 | HTML-to-PDF renderer pick (WeasyPrint or ReportLab) per TECH_STACK §15.2 | Renders sample HTML to PDF | 0.4 |
| 0.9 | Slack workspace + channel naming convention confirmed with DPA | DPA sign-off note | — |

### Phase 0 Traceability
- **0.1** — PRD: — (infrastructure scaffold); APP_FLOW: —; FIELD_MAP: —; BACKEND: §1 Django App Structure; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: — (no regulated surface); OBSERVABILITY: no events — scaffold only
- **0.2** — PRD: —; APP_FLOW: — (`/api/certs/` mount root for all §5 endpoints); FIELD_MAP: —; BACKEND: §1 (INSTALLED_APPS + URL mount), smoke `/api/certs/health/`; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: — (smoke endpoint only); OBSERVABILITY: no events — smoke endpoint
- **0.3** — PRD: FEAT-CERT-AUDIT-001; APP_FLOW: —; FIELD_MAP: §9 audit_log (GRANT note), §23 retention_tier row; BACKEND: §2 DB Role Separation; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: SEC-CERT-01 / D-CERT-179 (append-only GRANT) + SEC-CERT-16 (`vims_jobs` retention role); OBSERVABILITY: no events — enables audit writes for all later phases
- **0.4** — PRD: schema substrate for all 15 domains (FEAT-CERT-CAT-004, TRK-001, OCR-009, REC-017, AUDIT-001, NOTIF-031, PRT-029, EXT-001, LIFE-002, BLOB-002 et al.); APP_FLOW: —; FIELD_MAP: §1–§18 + §22 cert_change_log + §23 cross-cutting columns (PK = `NEWSEQUENTIALID()` DB default per B-FM-01/D-AUDRS-271; settings = structured single-row incl. `last_heartbeat_at` per B-FM-05); BACKEND: §3.1–§3.19, §4 Indexes & Constraints; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: SEC-CERT-01 (audit table created append-only), SEC-CERT-04 / D-CERT-019 (pdf_blob assumes encrypted store); OBSERVABILITY: no events — DDL only
- **0.5** — PRD: FEAT-CERT-CAT-003 (9 canonical sections); APP_FLOW: — (sections later surface §3.2 sidebar); FIELD_MAP: §1 catalog_section; BACKEND: §3.1 + `msc_profiles` seeds (CERT_F_001–008 / CERT_P_001–010); DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: — (seeds; permission IDs consumed by later RBAC gates); OBSERVABILITY: no events — migration identity
- **0.6** — PRD: — (route stub); APP_FLOW: §3.1 Fleet Dashboard `/certs` (stub); FIELD_MAP: —; BACKEND: —; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §1 File Layout, §2 `Cert*` naming, §7 RBAC Gating (stub permission check); SECURITY: —; OBSERVABILITY: no events — static stub
- **0.7** — PRD: FEAT-CERT-OCR-001 (foundation); APP_FLOW: —; FIELD_MAP: —; BACKEND: §6 `services/ocr_pipeline.py`, §7 OCR Pipeline interface; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — interface + mock only (resolves BLOCKERS B-TECH-01)
- **0.8** — PRD: FEAT-CERT-PRT-002 (foundation); APP_FLOW: —; FIELD_MAP: —; BACKEND: §6 `services/pdf_renderer.py`; DESIGN_SYSTEM: §5 Print Layout is the target spec (not implemented this step); FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — renderer selection spike (resolves BLOCKERS B-TECH-02)
- **0.9** — PRD: FEAT-CERT-NOTIF-002/020 (preparation); APP_FLOW: —; FIELD_MAP: —; BACKEND: §6 `services/slack_relay.py` (future consumer); DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — DPA sign-off note is the artifact

**Phase 0 exit gate:** every cell above checked; no business logic yet; CI green; the 0.7/0.8 picks (OCR engine, PDF renderer) encoded back into TECH_STACK.md §2 + BACKEND_STRUCTURE.md; settings field rows transcribed into FIELD_MAP.md §18.

---

## Phase 1 — Catalog (Week 2)

**Goal:** DPA can build the catalog before any vessel onboards.

| Step | Feature(s) | Notes |
|------|-----------|-------|
| 1.1 | FEAT-CERT-CAT-001/002/003/004 — `vims_certs_catalog_row` CRUD endpoints + admin UI | DPA write-only |
| 1.2 | FEAT-CERT-CAT-005/006 — vessel-type filter + applicability mode | |
| 1.3 | FEAT-CERT-CAT-007 — `parent_id` hierarchy + UI 2-level cap | |
| 1.4 | FEAT-CERT-CAT-008 — Class Certificates section + COC + class surveys as children | |
| 1.5 | FEAT-CERT-CAT-009 — IOPP variant model | |
| 1.6 | FEAT-CERT-CAT-010/011 — multi-instance equipment + roll-up rows | |
| 1.7 | FEAT-CERT-CAT-012 — IWS age-gate cron | |
| 1.8 | FEAT-CERT-CAT-013/014 — Type Approvals link + Tonnage Tax cadence | |
| 1.9 | FEAT-CERT-CAT-015/016 — deprecation + inline promotion | |
| 1.10 | FEAT-CERT-CAT-017/018 — RBAC + audit | |
| 1.11 | FEAT-CERT-CAT-019/020 — bulk soft-delete + cascade purge | |
| 1.12 | Catalog seed workshop — DPA + Tech Sup'tt produce v1.0 catalog from S 633 + TEC-04B union (D-CERT-023, D-CERT-103, D-CERT-107) | One-time data event |

### Phase 1 Traceability
- **1.1** — PRD: FEAT-CERT-CAT-001/002/003/004; APP_FLOW: §3.2 Catalog Admin, §3.3 Catalog Row Detail; FIELD_MAP: §1, §2; BACKEND: §3.1/§3.2, §5.1 sections + rows CRUD; DESIGN_SYSTEM: uses existing tokens only (+§9 Component Library); FRONTEND_GUIDELINES: §5 state contract, §6.1 forms, §7 RBAC (DPA write-only); SECURITY: SEC-CERT-01 (writes produce append-only audit rows); OBSERVABILITY: `create_catalog_row`, `update_catalog_row`
- **1.2** — PRD: FEAT-CERT-CAT-005/006; APP_FLOW: §3.2 filter toolbar, §3.3 Metadata tab; FIELD_MAP: §2 (`applicable_ship_types`, `applicability_mode`); BACKEND: §3.2, §5.1 GET filters; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: `update_catalog_row`
- **1.3** — PRD: FEAT-CERT-CAT-007; APP_FLOW: §3.2 indented child rows (2-level cap), §3.3 `parent_id` picker; FIELD_MAP: §2 (`parent_id`); BACKEND: §3.2, §4 self-FK; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: `update_catalog_row`
- **1.4** — PRD: FEAT-CERT-CAT-008; APP_FLOW: §3.2 Class Certificates section; FIELD_MAP: §1, §2; BACKEND: §3.1/§3.2, §5.1; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: `create_catalog_row` (COC + class-survey child seeds)
- **1.5** — PRD: FEAT-CERT-CAT-009; APP_FLOW: §3.3 Metadata tab, §3.5 `form_variant` surface; FIELD_MAP: §2 + §4 (`form_variant`); BACKEND: §3.2/§3.4; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: `update_catalog_row`
- **1.6** — PRD: FEAT-CERT-CAT-010/011; APP_FLOW: §3.2 (`parent_supports_dynamic_children` indicator); FIELD_MAP: §2; BACKEND: §3.2; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: `update_catalog_row`
- **1.7** — PRD: FEAT-CERT-CAT-012; APP_FLOW: — (cron; IWS flag visible §3.2); FIELD_MAP: §2 (IWS age-gate flag); BACKEND: §3.2, §11 age-gate cron; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: `update_catalog_row` (system actor on auto-disable)
- **1.8** — PRD: FEAT-CERT-CAT-013/014; APP_FLOW: §3.3 Metadata tab (`linked_pms_component_id` URL cross-link, no FK per D-CERT-176); FIELD_MAP: §2; BACKEND: §3.2, §13 (deliberately no cross-module surface); DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: `update_catalog_row`
- **1.9** — PRD: FEAT-CERT-CAT-015/016; APP_FLOW: §3.3 "Deprecate row", §3.8 inline promotion entry; FIELD_MAP: §2 (`is_active`); BACKEND: §5.1 deprecate + create; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.4 confirmation dialogs; SECURITY: —; OBSERVABILITY: `deprecate_catalog_row`, `create_catalog_row`
- **1.10** — PRD: FEAT-CERT-CAT-017/018; APP_FLOW: §3.2 role gate, §3.3 Audit history tab; FIELD_MAP: §2, §9; BACKEND: §3.9, §5.1 (CERT_P_008/009), §12 Audit Enforcement; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §7 RBAC Gating; SECURITY: SEC-CERT-01 / D-CERT-179; OBSERVABILITY: catalog write actions visible in audit history tab
- **1.11** — PRD: FEAT-CERT-CAT-019/020; APP_FLOW: §3.2 bulk soft-delete toolbar, §3.3 hard purge footer; FIELD_MAP: §2, §9 (cascade rows), §24 delete policy; BACKEND: §5.1 bulk-soft-delete (cap 50 + reason) + DELETE cascade; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.4 confirmation dialogs (D-CERT-081); SECURITY: SEC-CERT-11 / D-CERT-092 (cap 50 + reason); OBSERVABILITY: `bulk_soft_delete`, `hard_purge_catalog_row`
- **1.12** — PRD: FEAT-CERT-CAT-002, FEAT-CERT-MIG-002/007; APP_FLOW: §3.2 (one-time data event); FIELD_MAP: §1, §2; BACKEND: §5.1 POST rows + export-csv; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: ~340 `create_catalog_row` audit entries (exit-gate evidence)

**Phase 1 exit gate:** ~340 catalog rows seeded; DPA can edit; audit log entries visible.

---

## Phase 2 — TrackedItem core + RBAC (Week 3)

| Step | Feature(s) |
|------|-----------|
| 2.1 | FEAT-CERT-TRK-001 → 016 — full TrackedItem schema + lifecycle + status computation |
| 2.2 | FEAT-CERT-RBAC-001 → 026 — full RBAC matrix + approval state machine |
| 2.3 | Survey-window computation service per BACKEND_STRUCTURE §10 |
| 2.4 | Approval state-transition guards per VALIDATION_RULES §7 |
| 2.5 | Vessel Cert Dashboard `/certs/vessels/<imo>` (`CertVesselDashboard` per APP_FLOW §3.4) |
| 2.6 | TrackedItem Detail `/certs/vessels/<imo>/cert/<id>` (per APP_FLOW §3.5) |

### Phase 2 Traceability
- **2.1** — PRD: FEAT-CERT-TRK-001 → 016; APP_FLOW: §3.4, §3.5 (schema surfaces); FIELD_MAP: §4 tracked_item, §5 pdf_blob; BACKEND: §3.4, §5.2 tracked-items CRUD + upload-pdf + quarantine-resolve; DESIGN_SYSTEM: §2 Status Tier Palette (D-CERT-135/136), §6 Validity Codes, §7 Date Format; FRONTEND_GUIDELINES: §5 state contract, §4 Data Fetching; SECURITY: SEC-CERT-04 / D-CERT-019 (PDFs land in encrypted store); OBSERVABILITY: `create_tracked_item`, `update_tracked_item`, `upload_pdf`, `draft_expired`
- **2.2** — PRD: FEAT-CERT-RBAC-001 → 026; APP_FLOW: §2 role-permission matrix, §3.5 approval action buttons; FIELD_MAP: §11 approval_event, §4 (`approval_state`, `submission_scope`); BACKEND: §3.11, §5.2 submit/approve/reject, §5.1 push-to-fleet + anniversary-recompute; DESIGN_SYSTEM: §3 Approval State Palette; FRONTEND_GUIDELINES: §7 RBAC Gating, §6.4 confirmation dialogs; SECURITY: SEC-CERT-03 / D-CERT-082 (session), SEC-CERT-12 / D-CERT-081 (no 2FA — confirmation dialogs on destructive transitions); OBSERVABILITY: `submit_tracked_item`, `approve_tracked_item`, `reject_tracked_item`, `catalog_push_to_fleet`, `anniversary_recompute`
- **2.3** — PRD: FEAT-CERT-TRK-008; APP_FLOW: — (computed values surface §3.4/§3.5); FIELD_MAP: §4 + §26 (`windowOpen`/`windowClose` persisted-derived); BACKEND: §10 Survey-Window Computation, §6 `services/survey_window.py`; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — pure computation
- **2.4** — PRD: FEAT-CERT-TRK-013/014, FEAT-CERT-RBAC-005/006/007/020; APP_FLOW: §3.5 state-gated buttons + rejected callout; FIELD_MAP: §11; BACKEND: §3.11, §5.2 transitions (VALIDATION_RULES §7 guards); DESIGN_SYSTEM: §3 Approval State Palette; FRONTEND_GUIDELINES: §6.3 validation gates, §14 row-version race toast; SECURITY: —; OBSERVABILITY: transition events (guard rejections in `event_metadata`)
- **2.5** — PRD: FEAT-CERT-TRK-009, FEAT-CERT-DASH-001/004/005; APP_FLOW: §3.4 Vessel Cert Dashboard; FIELD_MAP: §4, §19 master_vessel join; BACKEND: §5.9 vessel dashboard, §5.2 GET; DESIGN_SYSTEM: §2, §6, §9 (`CertStatusBadge`, `CertExpiryTier`); FRONTEND_GUIDELINES: §5, §7, §4.4 Polling; SECURITY: — (read surface under standard RBAC); OBSERVABILITY: no events — read-only screen
- **2.6** — PRD: FEAT-CERT-TRK-010/011/012/015/016, FEAT-CERT-RBAC-001/002/003; APP_FLOW: §3.5 (3-column layout + special states); FIELD_MAP: §4, §5 version tray, §11 timeline; BACKEND: §5.2 detail/pdfs/audit/upload-pdf; DESIGN_SYSTEM: §2, §3, §7; FRONTEND_GUIDELINES: §11 PDF Preview, §6.4, §5; SECURITY: SEC-CERT-04 (blob preview/download from encrypted store); OBSERVABILITY: `update_tracked_item`, `upload_pdf`, `supersede_pdf`

---

## Phase 3 — OCR pipeline + onboarding wizard (Weeks 4–5)

| Step | Feature(s) |
|------|-----------|
| 3.1 | FEAT-CERT-OCR-001 → 014 — OCR pipeline incl. confidence routing |
| 3.2 | FEAT-CERT-WIZ-001 → 022 — 7-step wizard incl. gap-fill UI |
| 3.3 | Validation gates at commit (D-CERT-116) |
| 3.4 | SHA-256 dedup + supersede prompt (D-CERT-118) |
| 3.5 | Mandatory coverage gate (D-CERT-119) |
| 3.6 | Vessel-level rollback (D-CERT-124) |

### Phase 3 Traceability
- **3.1** — PRD: FEAT-CERT-OCR-001 → 014; APP_FLOW: §3.8 Gap-Fill (confidence-band highlighting), §3.7 Step 3 async batch states; FIELD_MAP: §4 OCR-fed fields, §5, §15 batch_ingest; BACKEND: §7 OCR Pipeline, §6, §3.15, §5.4 batch endpoints; DESIGN_SYSTEM: §8 OCR Confidence Badge; FRONTEND_GUIDELINES: §6.2 gap-fill form pattern; SECURITY: SEC-CERT-04 / D-CERT-019/189; OBSERVABILITY: `ocr_processed`, `upload_pdf`; OBS-CERT-08 thresholds (≥80/≥85)
- **3.2** — PRD: FEAT-CERT-WIZ-001 → 022 (+CAT-016, RBAC-021 at steps 2–3); APP_FLOW: §3.6 Hub, §3.7 7-step Wizard, §3.8 Gap-Fill; FIELD_MAP: §15, §16 vessel_config, §6 (step 4), §19 master_vessel; BACKEND: §5.4 full onboarding set; DESIGN_SYSTEM: §8, §9 (`BatchProgressBar`), §11 Mobile/Tablet; FRONTEND_GUIDELINES: §6.1/§6.2, §5, §13 Performance; SECURITY: — (DPA/FM gates = standard RBAC via CERT_F_005); OBSERVABILITY: `onboarding_step_complete`, `fm_signoff`, `ocr_processed`, `create_tracked_item`; SESSION_EXPIRED mid-wizard preserves step state (APP_FLOW §5.1 — explicit test target)
- **3.3** — PRD: FEAT-CERT-WIZ-008/009/010; APP_FLOW: §3.8 commit (block-vs-warn matrix, dry-run, CSV artifact); FIELD_MAP: §15 (`report_csv_blob_id`); BACKEND: §5.4 preview + commit (D-CERT-116 gates); DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.3 validation gates; SECURITY: —; OBSERVABILITY: `validation_block` per blocked commit + commit audit entries
- **3.4** — PRD: FEAT-CERT-WIZ-011, FEAT-CERT-TRK-012, FEAT-CERT-BLOB-002; APP_FLOW: §3.8 silent-skip + supersede prompt; FIELD_MAP: §5 (sha256, `is_active`); BACKEND: §3.5, §5.4 idempotency path; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.4 supersede prompt; SECURITY: SEC-CERT-04; OBSERVABILITY: `upload_pdf` (skip in `event_metadata`), `supersede_pdf`
- **3.5** — PRD: FEAT-CERT-WIZ-017, FEAT-CERT-DASH-005; APP_FLOW: §3.7 Step 6 coverage gate; §3.1/§3.4 banner; FIELD_MAP: §16 (override) + §26 coverage computed metric; BACKEND: §6 `services/coverage.py`, §5.4 coverage-override; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.1 (mandatory reason textarea); SECURITY: — (override audited, not gated); OBSERVABILITY: coverage-override audit entry; banner persists until 100% (D-CERT-119)
- **3.6** — PRD: FEAT-CERT-WIZ-019; APP_FLOW: §3.7 reset button, §3.5 DPA reset pre-go-live; FIELD_MAP: §15, §16, §9 rollback trail; BACKEND: §5.4 rollback (CERT_P_010); DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.4 destructive confirmation; SECURITY: SEC-CERT-12 / D-CERT-081 (soft-delete + audit, no 2FA); OBSERVABILITY: `onboarding_rollback`

**Phase 3 exit gate:** one fleet vessel onboarded successfully end-to-end on staging.

---

## Phase 4 — Class snapshot reconciliation (Week 6)

| Step | Feature(s) |
|------|-----------|
| 4.1 | FEAT-CERT-REC-001 → 031 |
| 4.2 | NK / KR / BV parsers + 6-PDF fixture corpus (D-CERT-057) |
| 4.3 | Reconciliation 3-panel UI |
| 4.4 | ClassCodeMapping versioned editor |
| 4.5 | Anomaly thresholds (D-CERT-073) |

### Phase 4 Traceability
- **4.1** — PRD: FEAT-CERT-REC-001 → 031; APP_FLOW: §3.9 Reconciliation Dashboard, §3.10 Review; FIELD_MAP: §6, §7, §8; BACKEND: §3.6–§3.8, §5.3 full set, §8 Reconciliation Engine; DESIGN_SYSTEM: §9 (`ClassSocietyChip`); FRONTEND_GUIDELINES: §5, §4; SECURITY: — (standard RBAC; Marine Sup'tt primary reviewer); OBSERVABILITY: `upload_class_snapshot`, `reconciliation_review`, `reparse_snapshot`
- **4.2** — PRD: FEAT-CERT-REC-002/003/004/011/014/015/019/020/021; APP_FLOW: — (results surface §3.10); FIELD_MAP: §6 (`parsed_payload_json`, parser_version); BACKEND: §6 `services/parsers/` (NK/KR/BV), §8; CI = 6-PDF corpus (D-CERT-057); DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: — (text-extract only, never OCR per D-CERT-048); OBSERVABILITY: `reparse_snapshot`; timeout/retry outcomes in `event_metadata` (D-CERT-059)
- **4.3** — PRD: FEAT-CERT-REC-022/024/025/027; APP_FLOW: §3.10 tabs + diff + actions; FIELD_MAP: §8, §4 pre-fill targets; BACKEND: §5.3 notify-master + mark-reviewed; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §5, §9 Notification UX; SECURITY: —; OBSERVABILITY: `reconciliation_review`, `notify_master`
- **4.4** — PRD: FEAT-CERT-REC-017/028; APP_FLOW: §3.10 `[Add to ClassCodeMapping]` (DPA-only), §3.9 re-parse; FIELD_MAP: §3; BACKEND: §3.3, §5.3 add-mapping + reparse; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.1, §7 (DPA-only); SECURITY: —; OBSERVABILITY: `add_class_mapping`, `edit_class_mapping`
- **4.5** — PRD: FEAT-CERT-REC-029/030/031; APP_FLOW: §3.10 anomaly banner; parser ops page (dev-only, feature-flagged); FIELD_MAP: §7 anomaly fields; BACKEND: §8 threshold evaluation, §3.7; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: OBS-CERT-04 / D-CERT-073 anomaly alerts (>15% unmapped / >3min / <0.7× count)

**Phase 4 exit gate:** all 6 reference snapshots parsed + reconciled with expected output.

---

## Phase 5 — Print + Share Bundle (Week 7)

| Step | Feature(s) |
|------|-----------|
| 5.1 | FEAT-CERT-PRT-001 → 033 — full print pipeline + 4 scopes + Excel companion + ZIP bundle |
| 5.2 | print_id derivation, system_state_hash, watermark scope mapping |
| 5.3 | Soft-throttle surface (D-CERT-143) |
| 5.4 | Hard-fail with support ticket (D-CERT-150) |

### Phase 5 Traceability
- **5.1** — PRD: FEAT-CERT-PRT-001 → 033 (+MIG-008 form code); APP_FLOW: §3.11 Print Builder, §3.12 History, §3.13 Share-Bundle; FIELD_MAP: §13 print_artifact; BACKEND: §3.13, §5.5 print/jobs/artifacts/share-bundle, §6 renderers + zip; DESIGN_SYSTEM: §4 Watermark Scope (D-CERT-138), §5 Print Layout (incl. 11-column schema, footer, glossary), §6, §7; FRONTEND_GUIDELINES: §10 Print/Share-Bundle UX, §7 scope×role matrix; SECURITY: SEC-CERT-05 / D-CERT-096 (outbound distribution scope); OBSERVABILITY: `print`, `share_bundle` (hash + artifact refs); OBS-CERT-06 budget ≤60s/≤5min
- **5.2** — PRD: FEAT-CERT-PRT-006/007/018/029/030/031; APP_FLOW: §3.11 Step 3 preview, §3.12 re-fetch; FIELD_MAP: §13 (`print_id`, `system_state_hash`, `watermark_applied`) + §26; BACKEND: §6 `services/system_state_hash.py`, §3.13; DESIGN_SYSTEM: §5.9 footer, §4 watermark map; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: SEC-CERT-09 / D-CERT-128 (identifiability footer); OBSERVABILITY: `print` entry carrying print_id + hash (immutable artifacts)
- **5.3** — PRD: FEAT-CERT-PRT-024, FEAT-CERT-DASH-002; APP_FLOW: §3.11 throttle note, §3.1 FM-only high-volume card; FIELD_MAP: §13, §9; BACKEND: §5.5 counter, §5.9 fleet aggregate; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: SEC-CERT-10 / D-CERT-143 (soft-throttle, surfaced not blocked); OBSERVABILITY: OBS-CERT-07 "high-volume print activity" → FM dashboard
- **5.4** — PRD: FEAT-CERT-PRT-033; APP_FLOW: §3.11 generation failure (support ticket + manual retry); FIELD_MAP: §13 job status; BACKEND: §5.5 job failure states; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §14 Error Handling; SECURITY: —; OBSERVABILITY: print-failure audit entry + ticket reference

---

## Phase 6 — Notification engine (Week 8)

| Step | Feature(s) |
|------|-----------|
| 6.1 | FEAT-CERT-NOTIF-001 → 034 — full per-side routing + escalation cadence |
| 6.2 | Magic-link ack flow (D-CERT-154) |
| 6.3 | Slack relay integration |
| 6.4 | Monthly digest cron (D-CERT-158) |
| 6.5 | Bouncing-email handling + Slack DM fallback (D-CERT-159) |
| 6.6 | Notification idempotency (D-CERT-174 — both layers) |
| 6.7 | Cadence heartbeat + dead-man alert (OBS-CERT-11, added at closure 2026-06-12): hourly cron stamps `settings.last_heartbeat_at`; independent 30-min beat task alerts office Slack + DPA dashboard red tile if stale >2h; `/api/certs/health/` exposes heartbeat age |

### Phase 6 Traceability
- **6.1** — PRD: FEAT-CERT-NOTIF-001 → 034 (excl. 6.2–6.6 items); APP_FLOW: §3.14 Notification Inbox; FIELD_MAP: §12 notification_meta, §10 alert_config, §19 master_notification; BACKEND: §3.10/§3.12, §5.6, §9 Dispatcher; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §9 per-side routing UX (Hard Rule 7); SECURITY: — (D-CERT-161 routing enforced server-side); OBSERVABILITY: OBS-CERT-02 dispatch trail (D-CERT-155), OBS-CERT-03 escalation ladder (D-CERT-089), dedup 60-min window
- **6.2** — PRD: FEAT-CERT-NOTIF-008/009; APP_FLOW: §3.14 [Acknowledge] (magic-link backed); FIELD_MAP: §12 ack metadata; BACKEND: §6 `services/magic_link.py`, §5.6 ack token endpoint; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: SEC-CERT-08 / D-CERT-154 (single-use 24h link, no inbound email parsing); OBSERVABILITY: ack state in dispatch trail (D-CERT-155)
- **6.3** — PRD: FEAT-CERT-NOTIF-002/003/020; APP_FLOW: — (config surfaces §3.18/§3.19); FIELD_MAP: §12, §16 per-vessel Slack routing; BACKEND: §6 `services/slack_relay.py`, §9 (office-side only); DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: §12 Slack Routing UX; SECURITY: —; OBSERVABILITY: Slack delivery status in notification_meta
- **6.4** — PRD: FEAT-CERT-NOTIF-014/015; APP_FLOW: —; FIELD_MAP: §12; BACKEND: §11 monthly digest (1st 08:00 ICT → DPA + Marine Sup'tt, D-CERT-158); DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: digest dispatch rows; no per-cert alerts
- **6.5** — PRD: FEAT-CERT-NOTIF-016/017/018, FEAT-CERT-DASH-003; APP_FLOW: §3.1 DPA bouncing-email card; FIELD_MAP: §12 delivery status, §9; BACKEND: §9 retry ×3 (1/5/30min) via shared `email_dispatcher`; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: OBS-CERT-05 / D-CERT-159 bounce fallback (Slack-DM) + DPA counter
- **6.6** — PRD: FEAT-CERT-NOTIF-031; APP_FLOW: —; FIELD_MAP: §12 idempotency_key (§23 cross-cutting); BACKEND: §3.12 (app-layer + DB UQ, D-CERT-174), §4; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no new events — dedup guard
- **6.7** — PRD: — (closure-scope reliability control, OBS-CERT-11/12); APP_FLOW: §3.1 Fleet Dashboard (DPA red tile); FIELD_MAP: §18 settings (`last_heartbeat_at`); BACKEND: §11 jobs (cadence cron + new beat task), `/api/certs/health/`; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: — (no PII in heartbeat); OBSERVABILITY: OBS-CERT-11 dead-man alert (office Slack per D-CERT-161 routing) + OBS-CERT-12 health payload

---

## Phase 7 — Audit log + External Auditor portal (Week 9)

| Step | Feature(s) |
|------|-----------|
| 7.1 | FEAT-CERT-AUDIT-001 → 008 |
| 7.2 | FEAT-CERT-EXT-001 → 010 — provisioning, scoped portal, redaction, watermark |
| 7.3 | Hot/cold tiering job |
| 7.4 | DPA-only export (watermarked) |

### Phase 7 Traceability
- **7.1** — PRD: FEAT-CERT-AUDIT-001 → 008; APP_FLOW: §3.17 Audit Log Read; FIELD_MAP: §9; BACKEND: §3.9 full enums, §5.8, §12 Audit Enforcement; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §5, §7 (DPA+FM full / Sup'tt slice); SECURITY: SEC-CERT-01 / D-CERT-179, SEC-CERT-07 / D-CERT-180; OBSERVABILITY: OBS-CERT-01 — this step ships the observability substrate itself (full action enum browsable; nightly retention batch itself audited)
- **7.2** — PRD: FEAT-CERT-EXT-001 → 010; APP_FLOW: §3.15 Provisioning, §3.16 Grant Detail, §3.20 External Portal; FIELD_MAP: §14, §20 Redaction Map; BACKEND: §3.14, §5.7 (grants + `/api/auditor/` token tree), §14, §6 `services/auditor_token.py`; DESIGN_SYSTEM: §4 Watermark (AUDIT COPY + name + expiry); FRONTEND_GUIDELINES: §7, §11 read-only portal; SECURITY: SEC-CERT-05 / D-CERT-096+195, SEC-CERT-06 / D-CERT-196, SEC-CERT-07 / D-CERT-180, SEC-CERT-14 (token hashing); OBSERVABILITY: `grant_auditor_access`, `edit_auditor_access`, signup-token-used; deliberately NO per-action session events (D-CERT-196)
- **7.3** — PRD: FEAT-CERT-AUDIT-003, FEAT-CERT-REC-016; APP_FLOW: §3.17 cold-tier fetch prompt; FIELD_MAP: §9 (`retention_tier`, `archived_at`), §23; BACKEND: §3.9, §11 tiering job; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: §14 long-fetch handling; SECURITY: SEC-CERT-02 / D-CERT-183, executed under `vims_jobs` (SEC-CERT-16, B-FM-03 resolved — D-CERT-179 app-path append-only preserved); OBSERVABILITY: tier flip recorded via `archived_at`
- **7.4** — PRD: FEAT-CERT-AUDIT-005; APP_FLOW: §3.17 export (DPA-only); FIELD_MAP: §9, §13 export artifact; BACKEND: §5.8 export (CERT_F_008 + CERT_P_005); DESIGN_SYSTEM: §4 watermarked export; FRONTEND_GUIDELINES: §7 DPA-only button; SECURITY: SEC-CERT-01 (read-only path) / D-CERT-091 export rule; OBSERVABILITY: export logged as `print` entry (watermarked artifact ref)

---

## Phase 8 — Vessel lifecycle events + Blob retention + Settings (Week 10)

| Step | Feature(s) |
|------|-----------|
| 8.1 | FEAT-CERT-LIFE-001 → 012 — decommission / sale / flag-change / class-change |
| 8.2 | FEAT-CERT-BLOB-001 → 011 — retention sweeper, DPA override, encryption inheritance |
| 8.3 | Settings screen (alert config, OCR thresholds, Slack routing) |
| 8.4 | Re-auth modal (D-CERT-082) |
| 8.5 | Phase-8 exit gates (added at closure 2026-06-12): (a) internal adversarial security review per SECURITY.md §13 / SEC-CERT-18 — auditor-portal token attacks, magic-link replay, RBAC bypass, GRANT-regime probes; results logged in progress.txt; (b) verify platform static maintenance page exists (APP_FLOW §5 MAINTENANCE) before Phase 9 cutover |

### Phase 8 Traceability
- **8.1** — PRD: FEAT-CERT-LIFE-001 → 012 (+DASH-004 banner); APP_FLOW: §3.18 Vessel Profile (lifecycle triggers + banners), §3.1 pending-re-upload banner; FIELD_MAP: §16 (flag-change/sale events), §4 (`invalid_due_to_reflag`, `pending_supersession`), §24 (vessel end-state resolved: 30-day hard-delete per D-CERT-044 + redacted slice D-CERT-093); BACKEND: §5.9 flag-change/class-change/sale-handover/decommission, §11 30-day jobs; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §6.4 destructive confirmations, §7 DPA-only; SECURITY: D-CERT-044 (30-day deletion) + D-CERT-093 (redacted audit slice retained post-sale); OBSERVABILITY: `flag_change_event`, `class_change_event`, `sale_initiated`, `sale_completed`, `decommission`
- **8.2** — PRD: FEAT-CERT-BLOB-001 → 011; APP_FLOW: §3.5 version tray (delete-pending grayed, 7-day grace); FIELD_MAP: §5 (`scheduled_delete_at`, `is_active`), §24 pdf_blob row; BACKEND: §3.5, §6 `services/retention.py`, §11 daily sweeper; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: SEC-CERT-04 / D-CERT-019/189 (encryption inheritance); OBSERVABILITY: `retention_purge` (audit always preserved — only blob purged)
- **8.3** — PRD: FEAT-CERT-OCR-012, FEAT-CERT-REC-005/009, FEAT-CERT-BLOB-007, FEAT-CERT-NOTIF-020; APP_FLOW: §3.19 Settings (5 tabs); FIELD_MAP: §10 alert_config, §18 settings (structured single-row, B-FM-05 resolved); BACKEND: §3.10/§3.18, §5.10, §5.6; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §12 Slack Routing UX, §7 DPA-only; SECURITY: — (CERT_F_006 standard RBAC); OBSERVABILITY: `settings_change` per tunable edit
- **8.4** — PRD: FEAT-CERT-RBAC-011/012; APP_FLOW: cross-screen modal (no dedicated route; APP_FLOW §5 SESSION_EXPIRED row); FIELD_MAP: — (session layer; consumes `wrh_ship_time_config` §19); BACKEND: shared JWT/`msc_profiles` chain; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §8 Online-Required UX; SECURITY: SEC-CERT-03 / D-CERT-082 (8h/24h + modal re-auth), SEC-CERT-12 (no 2FA); OBSERVABILITY: no events — re-auth is not an audited domain action
- **8.5** — PRD: — (quality gate, no feature); APP_FLOW: §5 MAINTENANCE row (page existence check); FIELD_MAP: —; BACKEND: attack surface = §5.7 auditor tree, §5.6 ack token, §2 GRANT regime; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: SEC-CERT-18 (adversarial review gate), SEC-CERT-05/06/07/08/14 (the controls under test); OBSERVABILITY: results logged in progress.txt; no runtime events

---

## Phase 9 — Cutover (Week 11)

| Step | Activity |
|------|----------|
| 9.1 | Per-vessel onboarding × 6 vessels with DPA + FM + each Master |
| 9.2 | FM sign-off per vessel → vessel goes live |
| 9.3 | Hard cutover — Excel registers retired, frozen as read-only archive |
| 9.4 | Email distribution lists discontinued |
| 9.5 | Training session for office + sea staff |

### Phase 9 Traceability
- **9.1** — PRD: FEAT-CERT-MIG-003 (+WIZ-001 → 022 exercised, not built); APP_FLOW: §3.6, §3.7 ×6 vessels; FIELD_MAP: §15, §16 (live rows); BACKEND: §5.4 (production use); DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: — (operational execution under existing controls); OBSERVABILITY: onboarding + OCR + create events per vessel — audit trail is the cutover evidence
- **9.2** — PRD: FEAT-CERT-WIZ-018, FEAT-CERT-MIG-003; APP_FLOW: §3.7 Step 7 FM sign-off; FIELD_MAP: §16 (`lifecycle_status`→active), §9 sign-off row; BACKEND: §5.4 fm-signoff; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: — (FM authority via CERT_P_002); OBSERVABILITY: `fm_signoff` per vessel; historical-backlog notification suppression (D-CERT-173)
- **9.3** — PRD: FEAT-CERT-MIG-001/004; APP_FLOW: — (organizational activity); FIELD_MAP: —; BACKEND: — (Excel archive outside the system); DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — ops/file-share action, not a system transaction
- **9.4** — PRD: FEAT-CERT-MIG-001 (cutover consequence); APP_FLOW: — (replaced by §3.14 inbox); FIELD_MAP: —; BACKEND: — (engine live since Phase 6); DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — distribution-list retirement happens in the mail system
- **9.5** — PRD: — (enablement; content = USER_GUIDE.md); APP_FLOW: all screens §3.1–§3.20 (walkthrough scope); FIELD_MAP: —; BACKEND: —; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — training only

---

## Phase 10 — Post-launch hardening (Week 12+)

- Monitor parser anomalies (D-CERT-073 thresholds).
- Tune OCR thresholds based on observed quality (D-CERT-106 / D-CERT-168).
- Refine Slack channel routing based on noise feedback.
- Address LESSONS.md entries accumulated during build.

### Phase 10 Traceability
- **10.1 (parser monitoring)** — PRD: FEAT-CERT-REC-029/030/031; APP_FLOW: §3.9/§3.10 anomaly banner + dev-only ops page; FIELD_MAP: §7; BACKEND: §8 thresholds; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: OBS-CERT-04 / D-CERT-073 alerts are the monitored signal
- **10.2 (OCR tuning)** — PRD: FEAT-CERT-OCR-012 (+OCR-005/006 thresholds); APP_FLOW: §3.19 OCR thresholds tab; FIELD_MAP: §18; BACKEND: §5.10, §7 threshold consumption; DESIGN_SYSTEM: §8 badge bands follow tuned values; FRONTEND_GUIDELINES: uses existing patterns only; SECURITY: —; OBSERVABILITY: `settings_change` per edit; `ocr_processed` confidence distribution is the tuning input (OBS-CERT-08)
- **10.3 (Slack routing refinement)** — PRD: FEAT-CERT-NOTIF-020 (+NOTIF-002/003); APP_FLOW: §3.18 per-vessel routing, §3.19 tab; FIELD_MAP: §16, §18; BACKEND: §6 `services/slack_relay.py`, §5.9/§5.10; DESIGN_SYSTEM: uses existing tokens only; FRONTEND_GUIDELINES: §12; SECURITY: — (D-CERT-161 law unchanged by tuning); OBSERVABILITY: `settings_change`; noise measured via dispatch/ack rates (OBS-CERT-02)
- **10.4 (LESSONS loop)** — PRD: —; APP_FLOW: —; FIELD_MAP: —; BACKEND: —; DESIGN_SYSTEM: —; FRONTEND_GUIDELINES: —; SECURITY: —; OBSERVABILITY: no events — `L-NNN` entries are the artifact; fixes carry their own traceability

---

## Hard Rules During Build

1. Read CLAUDE.md + progress.txt + LESSONS.md at every session start.
2. Every PR adds/updates FIELD_MAP.md row for any column or API field changed.
3. No isolated dep bumps in `TECH_STACK.md §1` — coordinate across modules.
4. Parser CI gate: all 6 reference PDFs must pass on every PR (D-CERT-057).
5. Cross-module non-integration enforced via static analysis (D-CERT-176).
6. Every destructive op gets a confirmation dialog with named action + reversal path (D-CERT-081); NO 2FA.
7. Per-side notification routing enforced server-side (D-CERT-161); never cross-route.
8. Before starting any step: its Traceability line must resolve through every cited layer (CLAUDE.md → Traceability Enforcement), and any 🔴 BLOCKED item it references (`BLOCKERS.md`) must be resolved first.
9. SECURITY.md controls (SEC-CERT-\*) and OBSERVABILITY.md events/budgets (OBS-CERT-\*) are verified per change via the CLAUDE.md Completion Checklist.

---

## Deferrals (V1.1 / V2)

See PRD §19. Build-time deferrals (Phase 0 picks) listed in BACKEND_STRUCTURE §15.

---

*FROZEN. State carries forward via `progress.txt`. Do NOT modify this doc.*

---

## Amendment 1 - 2026-07-17

**What changed:** CR-091 changed the live Certs catalog policy so every active catalog row uses `submission_scope = all_ranks_with_approval`.

**Triggering discovery:** Local DB verification showed all 459 rows were still `master_only`, preventing Chief Officer, Chief Engineer, and Second Engineer from uploading any certificate despite backend support for vessel sub-officer upload.

**Supersedes:** D-CERT-079 and D-CERT-165 only where they assigned Class, Statutory/Flag, or class-tracked rows to `master_only`. The current shipped behavior is D-CERT-199: C/O, C/E, and 2/E may upload any certificate on their own vessel, and those uploads require Master approval.

---

## Appendix — Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `IMPLEMENTATION_PLAN.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` ✓ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-017 | Canonical catalog sections (9): Class · Statutory & Flag · Trade & Commercial · Equipment LSA/FFA/Nav/GMDSS · Calibrations · Te... | LOCKED |
| D-CERT-030 | Class code mapping seed extracted by parser dev from 6 reference PDFs; | LOCKED |

---

## Amendment 2 - 2026-07-21

**What changed:** CR-102 adds bounded OCR fallback for class-status snapshot PDFs when the uploaded PDF exposes no text layer. The primary path remains `pdfplumber` text extraction, and OCR fallback feeds the same NK/KR/BV parser modules and reconciliation schema.

**Triggering discovery:** The real uploaded KR `class_Ayuthya.pdf` showed visible data from page 3 onward, but `pdfplumber` and `pypdf` extracted zero text characters across all 19 pages because each page is embedded as images. Tesseract OCR against the page image read the KR vessel-status content, proving that image-only class-status PDFs require OCR fallback to parse.

**Supersedes:** D-CERT-048 and Phase 4.2 only where they prohibited OCR fallback for image-only class-status snapshot PDFs. The current behavior is D-CERT-200: class snapshots are text-extracted first; if the full PDF has no text layer, existing Tesseract/pytesseract OCR may be used as a fallback before the same NK/KR/BV parsers and reconciliation flow run.

---

## Amendment 3 - 2026-07-22

**What changed:** CR-103 replaces the Certs OCR runtime from Tesseract/pytesseract to PaddleOCR. PaddleOCR is now the default engine for vessel-uploaded certificate PDF OCR and the bounded fallback engine for image-only class-status snapshot PDFs.

**Triggering discovery:** Users need better OCR accuracy for class-status snapshot and certificate document extraction, while preserving the shipped parser payloads, confidence routing, upload responses, and reconciliation contract.

**Supersedes:** Amendment 2 and TECH_STACK Phase 0.7 only where they name Tesseract/pytesseract as the OCR engine. D-CERT-200 remains unchanged: class snapshots are text-extracted first, and OCR fallback runs only when the full PDF has no text layer before the same NK/KR/BV parsers and reconciliation flow run.

---

## Amendment 4 - 2026-07-23

**What changed:** CR-108 makes generated Certs print/share artifacts directly accessible and deliverable. Print Builder exposes authenticated downloads for generated PDF and Excel artifacts and emails both files when a recipient email is provided. Share Bundle exposes an authenticated ZIP download and emails the ZIP when a recipient email is provided.

**Triggering discovery:** The shipped print/share UI showed "PDF ready", "Excel ready", or "ZIP ready" after generation, but users could not access the generated file from that screen. The recipient email field was persisted on the artifact record but did not send mail, making the field misleading.

**Supersedes:** Phase 5 print/export behavior only where readiness status was sufficient as the user-facing result. The current behavior is D-CERT-201: a successful print/share generation must provide direct authenticated artifact access, and a non-empty recipient email triggers delivery through the existing platform email configuration.
