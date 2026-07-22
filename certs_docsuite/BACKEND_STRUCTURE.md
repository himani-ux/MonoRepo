# VIMS Certificates Module â€” Backend Structure

> **Version:** 1.0
> **Last Updated:** 2026-05-13
> **Status:** Locked â€” Ready for Build
> **Source:** SSOT Â§Â§3, 5, 7, 10, 14 + APP_FLOW.md "Surfaces" trace lines + PRD Feature Registry.
> **Inheritance:** Reuses Reporting + Safety platform conventions for app structure, JWT auth, `master_*` tables, `email_dispatcher`, `master_notification`, blob storage, RBAC via `msc_profiles`. Certs introduces the `vims_certs_*` schema family + parser/OCR/notification subsystems.
> **Authority order:** This doc wins on schema, FKs, columns, indexes, API contract shape (per CLAUDE.md arbitration rule Â§3).

---

## Table of Contents

1. [Django App Structure](#1-django-app-structure)
2. [Database Role Separation](#2-database-role-separation)
3. [Schema â€” `vims_certs_*` Tables](#3-schema)
4. [Indexes & Constraints](#4-indexes--constraints)
5. [API Endpoint Catalog](#5-api-endpoint-catalog)
6. [Service Layer Modules](#6-service-layer-modules)
7. [OCR Pipeline](#7-ocr-pipeline)
8. [Reconciliation Engine](#8-reconciliation-engine)
9. [Notification Dispatcher](#9-notification-dispatcher)
10. [Survey-Window Computation](#10-survey-window-computation)
11. [Background Jobs](#11-background-jobs)
12. [Audit Log Enforcement](#12-audit-log-enforcement)
13. [Cross-Module Surface (DELIBERATELY NONE)](#13-cross-module-surface)
14. [External Auditor Subsystem](#14-external-auditor-subsystem)
15. [Build-Time Deferrals (Phase 0 Picks)](#15-build-time-deferrals)

---

## 1. Django App Structure

```
apps/certs/
â”œâ”€â”€ __init__.py
â”œâ”€â”€ apps.py                       # AppConfig name = "apps.certs"
â”œâ”€â”€ urls.py                       # Mounted at /api/certs/
â”œâ”€â”€ admin.py                      # Django admin (DPA-only access via msc_profiles)
â”œâ”€â”€ models/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ catalog.py                # CatalogSection, CatalogRow, ClassCodeMapping
â”‚   â”œâ”€â”€ tracked_item.py           # TrackedItem, ApprovalEvent
â”‚   â”œâ”€â”€ blob.py                   # PdfBlob, PrintArtifact
â”‚   â”œâ”€â”€ snapshot.py               # ClassStatusSnapshot, ReconciliationRun, ReconciliationFlag
â”‚   â”œâ”€â”€ ingest.py                 # BatchIngest, ModificationEvent
â”‚   â”œâ”€â”€ notification.py           # NotificationMeta
â”‚   â”œâ”€â”€ auditor.py                # ExternalAuditorAccess
â”‚   â”œâ”€â”€ audit.py                  # AuditLog (write helper + manager)
â”‚   â”œâ”€â”€ config.py                 # AlertConfig, VesselConfig, Settings
â”‚   â””â”€â”€ enums.py                  # All enum choices in one module
â”œâ”€â”€ serializers/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ catalog.py
â”‚   â”œâ”€â”€ tracked_item.py
â”‚   â”œâ”€â”€ snapshot.py
â”‚   â”œâ”€â”€ ingest.py
â”‚   â”œâ”€â”€ print.py
â”‚   â”œâ”€â”€ notification.py
â”‚   â”œâ”€â”€ auditor.py
â”‚   â””â”€â”€ audit.py
â”œâ”€â”€ views/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ catalog_views.py          # /api/certs/catalog/
â”‚   â”œâ”€â”€ tracked_item_views.py     # /api/certs/tracked-items/
â”‚   â”œâ”€â”€ snapshot_views.py         # /api/certs/class-snapshots/
â”‚   â”œâ”€â”€ reconciliation_views.py   # /api/certs/reconciliation/
â”‚   â”œâ”€â”€ onboarding_views.py       # /api/certs/onboarding/
â”‚   â”œâ”€â”€ print_views.py            # /api/certs/print/
â”‚   â”œâ”€â”€ dashboard_views.py        # /api/certs/dashboard/
â”‚   â”œâ”€â”€ alert_views.py            # /api/certs/alerts/ (config)
â”‚   â”œâ”€â”€ notification_views.py     # /api/certs/notifications/ (ack endpoints incl. magic-link)
â”‚   â”œâ”€â”€ auditor_views.py          # /api/certs/auditor-access/
â”‚   â””â”€â”€ audit_views.py            # /api/certs/audit-log/
â”œâ”€â”€ services/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ ocr_pipeline.py           # OCR engine wrapper + confidence routing
â”‚   â”œâ”€â”€ parsers/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ base.py               # BaseClassParser (interface)
â”‚   â”‚   â”œâ”€â”€ nk.py                 # NK parser (NK-SHIPS format)
â”‚   â”‚   â”œâ”€â”€ kr.py                 # KR parser (Vessel Status for Ship's Owner)
â”‚   â”‚   â”œâ”€â”€ bv.py                 # BV parser (MOVE Fleet in Service Survey Status)
â”‚   â”‚   â””â”€â”€ normalizer.py         # Common intermediate schema normalization
â”‚   â”œâ”€â”€ reconciliation.py         # Reconciliation engine
â”‚   â”œâ”€â”€ survey_window.py          # window_open / window_close computation
â”‚   â”œâ”€â”€ notification_dispatcher.py
â”‚   â”œâ”€â”€ slack_relay.py            # Slack SDK wrapper
â”‚   â”œâ”€â”€ magic_link.py             # Signed 24h-expiring URLs
â”‚   â”œâ”€â”€ pdf_renderer.py           # Print PDF generation
â”‚   â”œâ”€â”€ excel_renderer.py         # Companion Excel data-only export
â”‚   â”œâ”€â”€ zip_bundler.py            # Manifest PDF + cert PDFs ZIP
â”‚   â”œâ”€â”€ system_state_hash.py      # 8-char hash for print identifiability
â”‚   â”œâ”€â”€ coverage.py               # Mandatory-coverage % computation
â”‚   â”œâ”€â”€ auditor_token.py          # External auditor token signing + verification
â”‚   â””â”€â”€ retention.py              # Daily blob retention sweeper
â”œâ”€â”€ jobs/                         # Async / scheduled
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ ocr_worker.py             # Per-PDF OCR job
â”‚   â”œâ”€â”€ parser_worker.py          # Per-class snapshot parse job
â”‚   â”œâ”€â”€ notification_worker.py    # Notification dispatch worker
â”‚   â”œâ”€â”€ retention_sweeper.py      # Daily cron for PdfBlob retention
â”‚   â”œâ”€â”€ digest_monthly.py         # 1st of month 08:00 ICT digest
â”‚   â”œâ”€â”€ draft_expirer.py          # Nightly draft auto-expire (7d)
â”‚   â”œâ”€â”€ audit_archiver.py         # Hot â†’ cold tiering for audit log
â”‚   â””â”€â”€ reauth_warning.py         # Session-timeout warning emitter
â”œâ”€â”€ permissions/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ certs_perms.py            # CERT_F_* + CERT_P_* check helpers
â”‚   â””â”€â”€ auditor_perms.py          # External auditor scope enforcement
â”œâ”€â”€ management/
â”‚   â””â”€â”€ commands/
â”‚       â”œâ”€â”€ seed_catalog_sections.py   # Seed 9 sections per D-CERT-017
â”‚       â”œâ”€â”€ seed_certs_permissions.py  # Seed CERT_F_* / CERT_P_* into msc_profiles
â”‚       â”œâ”€â”€ reparse_snapshot.py        # Manual re-parse trigger
â”‚       â””â”€â”€ grant_auditor_access.py    # CLI fallback for grant creation
â”œâ”€â”€ migrations/
â”‚   â””â”€â”€ 0001_initial.py           # All vims_certs_* tables
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ parsers/
â”‚   â”‚   â””â”€â”€ fixtures/             # 6 reference class-status PDFs + expected JSON (D-CERT-057)
â”‚   â”œâ”€â”€ test_ocr_pipeline.py
â”‚   â”œâ”€â”€ test_reconciliation.py
â”‚   â”œâ”€â”€ test_notification_routing.py  # Per-side routing per D-CERT-161
â”‚   â”œâ”€â”€ test_approval_workflow.py     # State machine per D-CERT-076
â”‚   â”œâ”€â”€ test_print_artifacts.py
â”‚   â”œâ”€â”€ test_auditor_access.py
â”‚   â”œâ”€â”€ test_audit_log_role_separation.py
â”‚   â”œâ”€â”€ test_survey_window.py
â”‚   â”œâ”€â”€ test_idempotency.py           # D-CERT-118, D-CERT-174
â”‚   â””â”€â”€ test_validation_gates.py      # D-CERT-116
â””â”€â”€ conftest.py
```

Frontend mirrors this in:
```
src/
â”œâ”€â”€ routes/certs/                 # Per APP_FLOW.md routes
â”œâ”€â”€ components/certs/
â”‚   â”œâ”€â”€ shared/                   # CertStatusBadge, CertExpiryTier, OcrConfidenceBadge, ...
â”‚   â”œâ”€â”€ catalog/
â”‚   â”œâ”€â”€ onboarding/
â”‚   â”œâ”€â”€ tracked-item/
â”‚   â”œâ”€â”€ reconciliation/
â”‚   â”œâ”€â”€ print/
â”‚   â”œâ”€â”€ notifications/
â”‚   â”œâ”€â”€ auditor-access/
â”‚   â””â”€â”€ audit-log/
â”œâ”€â”€ hooks/certs/                  # TanStack Query hooks per endpoint
â”œâ”€â”€ stores/certs/                 # Zustand stores per sub-domain
â””â”€â”€ schemas/certs/                # Zod schemas matching API + form validation
```

---

## 2. Database Role Separation

Per **D-CERT-179** (FEAT-CERT-AUDIT-001):

| Role | GRANTs |
|------|--------|
| `vims_app` | `INSERT, SELECT` on `vims_certs_audit_log`. `SELECT, INSERT, UPDATE, DELETE` on all other `vims_certs_*` and `master_notification`. NO `UPDATE` or `DELETE` on `vims_certs_audit_log` ever. |
| `vims_admin` | Full GRANTs on all `vims_certs_*` tables. **Used only for migrations** â€” never at runtime. Migration runner authenticates as this role; runtime Django ORM authenticates as `vims_app`. |

**Belt-and-suspenders:** Even if a code path attempted to update an audit row, the DB rejects it. Application code MUST use `AuditLog.objects.create(...)` only â€” there is no `update()` or `delete()` interface in the manager.

**Notification immutability:** Same INSERT+SELECT-only GRANT applies to `master_notification` rows where `module='certs'` (per D-CERT-179). Cross-module rows in `master_notification` follow whatever the owning module's policy is.

**Migration execution:** During platform deploys, the migration runner uses `DATABASES['default']['USER'] = 'vims_admin'` (env-overridden); runtime uses `vims_app`. Phase 0 IMPLEMENTATION_PLAN encodes the env-flip mechanism.

---

## 3. Schema

Notation: PK = Primary Key; FK â†’ table.col = Foreign Key; UQ = Unique; NN = Not Null; NULL = Nullable.
Types use SQL Server compatible expressions; Django field types in parens.

### 3.1 `vims_certs_catalog_section`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| section_id | INT | PK, identity | 1..9 hard-coded per D-CERT-017 |
| section_code | NVARCHAR(32) | NN, UQ | E.g. `CLASS`, `STATUTORY`, `TRADE`, `EQUIPMENT`, `CALIBRATIONS`, `TESTS`, `TYPE_APPROVAL`, `APPROVED_PLANS`, `MISC` |
| display_name | NVARCHAR(128) | NN | Sidebar label |
| sort_order | SMALLINT | NN | 1..9 print order |
| created_at, created_by | (audit fields) | NN | Seeded by migration; no updated_* on this seed-only table |

**Seed:** `seed_catalog_sections` mgmt command writes 9 rows (D-CERT-017) at Phase 0.

### 3.2 `vims_certs_catalog_row` (FEAT-CERT-CAT-004 / D-CERT-109)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| catalog_id | UNIQUEIDENTIFIER | PK | UUID |
| canonical_code | NVARCHAR(64) | NN, UQ | Workshop-assigned, e.g. `STAT-IOPP`, `CLASS-COC`, `EQ-SCBA` |
| section_id | INT | NN, FK â†’ vims_certs_catalog_section.section_id | |
| display_name | NVARCHAR(256) | NN | Human-readable |
| short_name | NVARCHAR(64) | NULL | Acronym |
| print_section_label | NVARCHAR(128) | NN | Mapping back to S 633 section for print export |
| validity_type | NVARCHAR(16) | NN | enum: `full \| conditional \| short_term \| permanent` per D-CERT-012 |
| cadence_months | SMALLINT | NULL | NULL for permanent |
| cadence_custom_days | INT | NULL | For `custom_days(N)` cadence |
| issuing_authority_type | NVARCHAR(16) | NN | enum: `flag \| class \| RO \| manufacturer \| company \| ko_other` |
| is_class_tracked | BIT | NN, default 0 | D-CERT-009 |
| submission_scope | NVARCHAR(32) | NN | enum: `master_only \| all_ranks_with_approval`; shipped active catalog rows use `all_ranks_with_approval` per D-CERT-199 |
| parent_id | UNIQUEIDENTIFIER | NULL, FK â†’ self.catalog_id | Nullable; arbitrary depth schema (D-CERT-010); UI 2-level cap |
| relationship_type_default | NVARCHAR(32) | NULL | Default `relationship_type` for child instances |
| applicable_ship_types | NVARCHAR(256) | NN, default '["all"]' | JSON array per D-CERT-028 / D-CERT-109 |
| mandatory_for_all_vessels | BIT | NN, default 1 | D-CERT-109 |
| applicability_mode | NVARCHAR(24) | NN, default 'all_matching_type' | enum: `all_matching_type \| specific_vessel_ids` per D-CERT-029 |
| specific_vessel_ids | NVARCHAR(MAX) | NULL | JSON array of vessel IDs when mode=specific |
| parent_supports_dynamic_children | BIT | NN, default 0 | D-CERT-035 |
| age_gate_max_years | SMALLINT | NULL | E.g. 15 for IWS (D-CERT-034) |
| retain_all_versions | BIT | NN, default 0 | CSR override (D-CERT-039) |
| linked_pms_component_id | NVARCHAR(64) | NULL | D-CERT-042 (V1 stored only; cross-module fetch deferred) |
| alert_lead_overrides | NVARCHAR(MAX) | NULL | JSON override of default Â§6.1 lead times for this row |
| regulatory_anchor | NVARCHAR(256) | NULL | E.g. "MARPOL Annex I Reg 7" |
| legacy_remarks | NVARCHAR(MAX) | NULL | From S 633 import |
| print_order | INT | NN, default 0 | Within section |
| is_active | BIT | NN, default 1 | Deprecation flag (FEAT-CERT-CAT-015) |
| created_at, created_by, updated_at, updated_by | (audit fields) | NN | |

**Cascade on hard-purge:** ON DELETE CASCADE â†’ `vims_certs_audit_log` rows where `entity_type='catalog_row' AND entity_id=catalog_id` (D-CERT-182 / FEAT-CERT-CAT-020). NOT cascade to `vims_certs_tracked_item` â€” those are independently retained.

### 3.3 `vims_certs_class_code_mapping`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| mapping_id | UNIQUEIDENTIFIER | PK | |
| class_society | NVARCHAR(8) | NN | enum: `NK \| KR \| BV` |
| class_code_or_name | NVARCHAR(128) | NN | Raw value from class report |
| catalog_id | UNIQUEIDENTIFIER | NN, FK â†’ vims_certs_catalog_row.catalog_id | |
| cert_or_survey_kind | NVARCHAR(16) | NN | enum: `renewal \| intermediate \| annual \| periodic \| n/a` |
| notes | NVARCHAR(MAX) | NULL | |
| version | INT | NN, default 1 | Increments on each edit (D-CERT-061) |
| active | BIT | NN, default 1 | |
| created_at, created_by, updated_at, updated_by | (same as 3.2) |

**Indexes:** UQ on `(class_society, class_code_or_name, version)`.

### 3.4 `vims_certs_tracked_item` (FEAT-CERT-TRK-001 / D-CERT-010, D-CERT-011)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| tracked_item_id | UNIQUEIDENTIFIER | PK | |
| vessel_id | UNIQUEIDENTIFIER | NN, FK â†’ master_vessel.vessel_id | |
| catalog_id | UNIQUEIDENTIFIER | NN, FK â†’ vims_certs_catalog_row.catalog_id | |
| type | NVARCHAR(24) | NN | enum: `certificate \| endorsement_survey \| service \| calibration \| test \| type_approval \| plan_approval` |
| validity_type | NVARCHAR(16) | NN | enum per D-CERT-012 |
| form_variant | NVARCHAR(8) | NULL | `A \| B \| n/a` for IOPP-style (D-CERT-032) |
| cadence_months | SMALLINT | NULL | Per-instance override of catalog cadence (D-CERT-027) |
| cadence_custom_days | INT | NULL | |
| parent_id | UNIQUEIDENTIFIER | NULL, FK â†’ self.tracked_item_id | |
| relationship_type | NVARCHAR(32) | NULL | enum: `survey_of \| short_term_for \| extension_of \| dispensation_for` |
| supersedes_id | UNIQUEIDENTIFIER | NULL, FK â†’ self.tracked_item_id | When full cert replaces an STC |
| issue_date | DATE | NULL | |
| expiry_date | DATE | NULL | NULL for permanent |
| anniversary_date | DATE | NULL | Set ONCE at onboarding (D-CERT-074) |
| window_open | DATE | NULL | Computed (D-CERT-063) |
| window_close | DATE | NULL | Computed |
| last_done_date | DATE | NULL | |
| next_due_date | DATE | NULL | Computed |
| postponed_until | DATE | NULL | (D-CERT-065) |
| status | NVARCHAR(32) | NN, default 'ok' | enum: `ok \| window_opening \| window_open \| window_closing \| overdue \| done \| postponed \| superseded \| permanent \| expired_at_onboarding \| expired \| pending_first_upload \| invalid_due_to_reflag \| pending_supersession` |
| certificate_number | NVARCHAR(128) | NULL | NULL when bypassed (D-CERT-105) |
| issuing_authority | NVARCHAR(128) | NN | |
| place_of_issue | NVARCHAR(128) | NULL | |
| extension_authority | NVARCHAR(8) | NULL | enum: `class \| flag \| n/a` (D-CERT-013) |
| extension_letter_pdf_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_pdf_blob.blob_id | |
| extension_reason | NVARCHAR(512) | NULL | |
| pdf_attachment_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_pdf_blob.blob_id | Current active PDF |
| pdf_missing | BIT | NN, default 0 | (D-CERT-113 / FEAT-CERT-TRK-011) |
| source | NVARCHAR(16) | NN, default 'manual' | enum: `manual \| class_snapshot \| migration` |
| last_class_sync_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_class_status_snapshot.snapshot_id | |
| approval_state | NVARCHAR(24) | NN, default 'approved' | enum: `draft \| pending_master_approval \| approved \| rejected` (D-CERT-076) |
| submitted_by | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | |
| submitted_at | DATETIME2 | NULL | |
| approved_by | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | |
| approved_at | DATETIME2 | NULL | |
| rejection_reason | NVARCHAR(MAX) | NULL | |
| rejection_count | SMALLINT | NN, default 0 | Auto-flag to FM at 3 (D-CERT-080) |
| draft_expires_at | DATETIME2 | NULL | NN when approval_state='draft'; nightly expirer (D-CERT-076) |
| lifecycle_status | NVARCHAR(24) | NN, default 'active' | enum: `active \| pending_disposal \| pending_supersession \| invalid_due_to_reflag \| onboarding_quarantine` |
| row_version | TIMESTAMP / ROWVERSION | NN | Optimistic concurrency (D-CERT-088 race resolution) |
| version | INT | NN, default 1 | **Cross-module CAS counter (D-AUDRS-236/239 obligation, added 2026-06-12):** increments on EVERY write to this row; external writers (Audit module writeback of last_done/next_due/validity per D-AUDRS-202) must compare-and-swap on it. Distinct from row_version (in-process concurrency). |
| created_at, created_by, updated_at, updated_by | (audit fields) |

### 3.5 `vims_certs_pdf_blob`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| blob_id | UNIQUEIDENTIFIER | PK | |
| tracked_item_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_tracked_item.tracked_item_id | NULL for snapshot blobs |
| snapshot_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_class_status_snapshot.snapshot_id | NULL for tracked-item blobs |
| blob_storage_path | NVARCHAR(512) | NN | S3-compatible URI |
| filename | NVARCHAR(256) | NN | Original upload name |
| content_sha256 | CHAR(64) | NN | (D-CERT-051 / D-CERT-118) |
| content_size_bytes | BIGINT | NN | |
| uploaded_by | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |
| uploaded_at | DATETIME2 | NN | |
| is_active | BIT | NN, default 1 | False once superseded |
| superseded_at | DATETIME2 | NULL | |
| retention_policy | NVARCHAR(32) | NN | enum: `immediate_delete_on_supersede \| retain_18_months_then_purge \| retain_indefinite \| retain_all_versions` (D-CERT-020 / D-CERT-039) |
| scheduled_delete_at | DATETIME2 | NULL | Computed from retention_policy + supersession |
| delete_pending_since | DATETIME2 | NULL | 7-day soft-delete grace (D-CERT-021) |
| dpa_retention_override_until | DATETIME2 | NULL | DPA can extend (D-CERT-021 / FEAT-CERT-BLOB-007) |
| ocr_payload_json | NVARCHAR(MAX) | NULL | OCR result for cert PDFs (D-CERT-101 / FEAT-CERT-OCR-009) |
| ocr_confidence_per_field | NVARCHAR(MAX) | NULL | JSON map of field â†’ confidence float |
| ocr_processed_at | DATETIME2 | NULL | |
| ocr_engine_version | NVARCHAR(32) | NULL | |
| schema_version | SMALLINT | NN, default 1 | (D-CERT-062) |

**Indexes:** UQ on `(tracked_item_id, content_sha256)` for dedup; index on `(scheduled_delete_at, is_active)` for retention sweeper.

### 3.6 `vims_certs_class_status_snapshot`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| snapshot_id | UNIQUEIDENTIFIER | PK | |
| vessel_id | UNIQUEIDENTIFIER | NN, FK â†’ master_vessel.vessel_id | |
| class_society | NVARCHAR(8) | NN | enum: `NK \| KR \| BV` |
| pdf_blob_id | UNIQUEIDENTIFIER | NN, FK â†’ vims_certs_pdf_blob.blob_id | Original (retained indefinitely per D-CERT-020) |
| printed_on_date | DATE | NULL | Extracted from PDF cover |
| uploaded_by | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |
| uploaded_at | DATETIME2 | NN | |
| parser_version | NVARCHAR(32) | NN | |
| parse_status | NVARCHAR(16) | NN | enum: `success \| partial \| failed \| pending` |
| parse_started_at | DATETIME2 | NULL | |
| parse_completed_at | DATETIME2 | NULL | |
| parser_timeout | BIT | NN, default 0 | True when 5-min hard timeout hit (D-CERT-059) |
| retry_count | SMALLINT | NN, default 0 | |
| parsed_payload_json | NVARCHAR(MAX) | NULL | Common intermediate schema |
| parsed_payload_schema_version | SMALLINT | NN, default 1 | (D-CERT-062) |
| reconciliation_run_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_reconciliation_run.run_id | |
| upload_sha256 | CHAR(64) | NN | (D-CERT-051) |
| superseded_user_error | BIT | NN, default 0 | Wrong-vessel rollback flag (D-CERT-051) |

### 3.7 `vims_certs_reconciliation_run`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| run_id | UNIQUEIDENTIFIER | PK | |
| snapshot_id | UNIQUEIDENTIFIER | NN, FK â†’ vims_certs_class_status_snapshot.snapshot_id | |
| ran_at | DATETIME2 | NN | |
| matches_count | INT | NN, default 0 | |
| mismatches_count | INT | NN, default 0 | |
| missing_in_catalog_count | INT | NN, default 0 | |
| missing_in_class_count | INT | NN, default 0 | |
| conditional_stc_detected_count | INT | NN, default 0 | |
| extended_postponed_detected_count | INT | NN, default 0 | |
| unmapped_low_confidence_count | INT | NN, default 0 | |
| flags_json | NVARCHAR(MAX) | NULL | Aggregate JSON for dashboard |
| notifications_sent_json | NVARCHAR(MAX) | NULL | (recipient, channel, sent_at) array |
| mapping_version_used | INT | NN | (D-CERT-061) |
| anomaly_breaches_json | NVARCHAR(MAX) | NULL | Per D-CERT-073 |

### 3.8 `vims_certs_reconciliation_flag`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| flag_id | UNIQUEIDENTIFIER | PK | |
| run_id | UNIQUEIDENTIFIER | NN, FK â†’ vims_certs_reconciliation_run.run_id | |
| bucket | NVARCHAR(32) | NN | enum: `match \| mismatch \| missing_in_catalog \| missing_in_class \| conditional_stc \| extended_postponed \| unmapped_low_confidence` |
| catalog_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_catalog_row.catalog_id | NULL for unmapped/missing-in-catalog |
| tracked_item_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_tracked_item.tracked_item_id | NULL when no instance exists |
| class_row_extract_json | NVARCHAR(MAX) | NULL | Raw class snapshot row data |
| diff_json | NVARCHAR(MAX) | NULL | Per-field diff |
| reviewed_by | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | |
| reviewed_at | DATETIME2 | NULL | |
| resolution_action | NVARCHAR(32) | NULL | enum: `notified_master \| marked_reviewed \| pending_master_upload \| added_to_mapping \| dismissed` |
| resolved_at | DATETIME2 | NULL | NULL when open |

### 3.9 `vims_certs_audit_log` (FEAT-CERT-AUDIT-001)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| audit_id | UNIQUEIDENTIFIER | PK | |
| timestamp_utc | DATETIME2 | NN | |
| vessel_id | UNIQUEIDENTIFIER | NULL, FK â†’ master_vessel.vessel_id | NULL for fleet-wide events |
| actor_user_id | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |
| actor_role | NVARCHAR(32) | NN | Snapshot of actor's role at event time |
| action | NVARCHAR(64) | NN | enum: `create_catalog_row \| update_catalog_row \| deprecate_catalog_row \| hard_purge_catalog_row \| create_tracked_item \| update_tracked_item \| submit_tracked_item \| approve_tracked_item \| reject_tracked_item \| upload_pdf \| supersede_pdf \| upload_class_snapshot \| reparse_snapshot \| reconciliation_review \| notify_master \| add_class_mapping \| edit_class_mapping \| print \| share_bundle \| grant_auditor_access \| edit_auditor_access \| onboarding_step_complete \| fm_signoff \| onboarding_rollback \| flag_change_event \| class_change_event \| sale_initiated \| sale_completed \| decommission \| catalog_push_to_fleet \| anniversary_recompute \| bulk_soft_delete \| ocr_processed \| validation_block \| settings_change \| draft_expired \| retention_purge` |
| entity_type | NVARCHAR(32) | NN | enum: `catalog_row \| tracked_item \| pdf_blob \| class_status_snapshot \| reconciliation_flag \| auditor_access \| print_artifact \| batch_ingest \| approval_event \| vessel_config \| settings \| notification` |
| entity_id | UNIQUEIDENTIFIER | NULL | NULL when action is fleet-wide |
| before_json | NVARCHAR(MAX) | NULL | |
| after_json | NVARCHAR(MAX) | NULL | |
| reason | NVARCHAR(MAX) | NULL | DPA reason / Master rejection / etc. |
| event_metadata | NVARCHAR(MAX) | NULL | Extra context JSON |
| retention_tier | NVARCHAR(8) | NN, default 'hot' | enum: `hot \| cold` (D-CERT-183) |
| archived_at | DATETIME2 | NULL | When tier flipped to cold |
| schema_version | SMALLINT | NN, default 1 | |

**GRANT enforcement:** `vims_app` role has only `INSERT, SELECT` on this table (D-CERT-179).

### 3.10 `vims_certs_alert_config`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| config_id | UNIQUEIDENTIFIER | PK | |
| trigger_event | NVARCHAR(64) | NN | enum per Â§6.1 SSOT |
| default_lead_days | INT | NN | |
| dpa_override_lead_days | INT | NULL | |
| recipients_default_json | NVARCHAR(MAX) | NN | Default recipient role list |
| dpa_override_recipients_json | NVARCHAR(MAX) | NULL | |
| escalation_cadence_json | NVARCHAR(MAX) | NN | Per D-CERT-089 / D-CERT-162 |
| ocr_threshold_office | DECIMAL(4,3) | NN, default 0.800 | Tunable (D-CERT-106) |
| ocr_threshold_vessel | DECIMAL(4,3) | NN, default 0.850 | (D-CERT-168) |
| ocr_threshold_manual_floor | DECIMAL(4,3) | NN, default 0.600 | |
| class_snapshot_cadence_months | SMALLINT | NN, default 3 | (D-CERT-006) |
| class_snapshot_lead_months | SMALLINT | NN, default 1 | |
| event_snapshot_grace_days | SMALLINT | NN, default 14 | (D-CERT-007) |
| draft_expire_days | SMALLINT | NN, default 7 | (D-CERT-076) |

### 3.11 `vims_certs_approval_event`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| event_id | UNIQUEIDENTIFIER | PK | |
| tracked_item_id | UNIQUEIDENTIFIER | NN, FK â†’ vims_certs_tracked_item.tracked_item_id | |
| from_state | NVARCHAR(24) | NN | |
| to_state | NVARCHAR(24) | NN | |
| actor_user_id | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |
| actor_role | NVARCHAR(32) | NN | |
| reason | NVARCHAR(MAX) | NULL | |
| timestamp_utc | DATETIME2 | NN | |

### 3.12 `vims_certs_notification_meta` (D-CERT-151, D-CERT-155, D-CERT-174, D-CERT-175)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| notification_id | UNIQUEIDENTIFIER | PK | |
| master_notification_id | UNIQUEIDENTIFIER | NN, FK â†’ master_notification.id | |
| trigger_event | NVARCHAR(64) | NN | E.g. `cert_expiring_30d`, `reconciliation_mismatch` |
| cert_row_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_tracked_item.tracked_item_id | |
| vessel_id | UNIQUEIDENTIFIER | NULL, FK â†’ master_vessel.vessel_id | |
| recipients_json | NVARCHAR(MAX) | NN | (user_id + role) array |
| channels_json | NVARCHAR(MAX) | NN | per-recipient (in_app/email/slack) |
| sent_at | DATETIME2 | NN | |
| delivery_status_json | NVARCHAR(MAX) | NULL | per-channel (queued/sent/bounced/failed) |
| ack_user_id | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | |
| ack_at | DATETIME2 | NULL | |
| ack_channel | NVARCHAR(16) | NULL | enum: `in_app \| magic_link \| slack` |
| escalation_level | SMALLINT | NN, default 0 | 0=initial, 1=14d-no-ack, 2=7d-daily, 3=post-expiry |
| body_content | NVARCHAR(MAX) | NULL | 1y retention then NULL'd (D-CERT-175) |
| body_purged_at | DATETIME2 | NULL | |
| idempotency_key | NVARCHAR(128) | NN, UQ | `(cert_row_id, cadence, sent_date)` (D-CERT-174) |

**UQ constraint** on `idempotency_key` enforces D-CERT-174 belt-and-suspenders.

### 3.13 `vims_certs_print_artifact` (D-CERT-128, D-CERT-145, D-CERT-147)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| print_id | NVARCHAR(64) | PK | Human-readable. Single-vessel: `SQE-S633-<imo>-<yyyymmdd>-<seq>`; fleet/multi-vessel: `SQE-S633-FLEET-<yyyymmdd>-<seq>` (B-PRT-01 resolved 2026-06-29) |
| scope | NVARCHAR(32) | NN | enum: `per_vessel_full \| per_vessel_partial \| per_section_fleetwide \| custom_selection \| share_bundle` |
| vessels_json | NVARCHAR(MAX) | NN | Array of vessel_ids in scope |
| sections_json | NVARCHAR(MAX) | NULL | Array of section_codes when applicable |
| filters_json | NVARCHAR(MAX) | NULL | Per-vessel partial filter set |
| custom_cert_ids_json | NVARCHAR(MAX) | NULL | For custom_selection / share_bundle |
| user_id | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |
| user_role | NVARCHAR(32) | NN | |
| timestamp_utc | DATETIME2 | NN | |
| system_state_hash | CHAR(8) | NN | (D-CERT-128) |
| watermark_applied | NVARCHAR(32) | NN | enum: `none \| INTERNAL \| AUDIT_COPY \| MASTER_COPY \| DRAFT` |
| watermark_recipient | NVARCHAR(128) | NULL | For MASTER_COPY / AUDIT_COPY |
| pdf_blob_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_pdf_blob.blob_id | |
| excel_blob_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_pdf_blob.blob_id | |
| bundle_zip_blob_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_pdf_blob.blob_id | For share-bundle |
| recipient_email | NVARCHAR(256) | NULL | Opt-in email (D-CERT-149) |
| page_count | INT | NULL | |
| generation_status | NVARCHAR(16) | NN, default 'success' | enum: `success \| failed` |
| failure_message | NVARCHAR(MAX) | NULL | (D-CERT-150) |

### 3.14 `vims_certs_external_auditor_access` (D-CERT-096, D-CERT-194, D-CERT-195, D-CERT-196)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| grant_id | UNIQUEIDENTIFIER | PK | |
| auditor_name | NVARCHAR(128) | NN | |
| auditor_email | NVARCHAR(256) | NN | |
| scope_json | NVARCHAR(MAX) | NN | `{vessels: [imo,...], sections: [...], cert_ids: [...]}` |
| expiry_at | DATETIME2 | NN | |
| granted_by | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |
| granted_at | DATETIME2 | NN | |
| signup_token_hash | CHAR(64) | NN | SHA-256 of one-time signup token |
| signup_token_used_at | DATETIME2 | NULL | |
| token_secret_hash | CHAR(64) | NULL | Auditor's session token hash post-signup |
| last_accessed_at | DATETIME2 | NULL | (D-CERT-196 prevents activity logging â€” last_accessed_at is allowed as a single grant-level signal, not per-action) |
| revoked_via_expiry_edit | BIT | NN, default 0 | (D-CERT-195) |

### 3.15 `vims_certs_batch_ingest` (D-CERT-104, D-CERT-115, D-CERT-117)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| batch_id | UNIQUEIDENTIFIER | PK | |
| vessel_id | UNIQUEIDENTIFIER | NN, FK â†’ master_vessel.vessel_id | |
| onboarding_session_id | UNIQUEIDENTIFIER | NULL | Groups batches per onboarding instance |
| pdf_blob_ids_json | NVARCHAR(MAX) | NN | Array of blob_ids in batch |
| pdf_count | SMALLINT | NN | â‰¤10 (D-CERT-104) |
| status | NVARCHAR(24) | NN | enum: `queued \| ocr_running \| ready_for_review \| commit_pending \| committed \| cancelled` |
| created_at | DATETIME2 | NN | |
| created_by | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |
| ocr_completed_at | DATETIME2 | NULL | |
| review_started_at | DATETIME2 | NULL | |
| committed_at | DATETIME2 | NULL | |
| committed_by | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | |
| cancelled_at | DATETIME2 | NULL | |
| cancelled_by | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | |
| validation_blocks_json | NVARCHAR(MAX) | NULL | Per D-CERT-116 block list at last preview |
| validation_warns_json | NVARCHAR(MAX) | NULL | Per D-CERT-116 warn list |
| report_csv_blob_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_pdf_blob.blob_id | (D-CERT-117) |

### 3.16 `vims_certs_vessel_config`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| vessel_id | UNIQUEIDENTIFIER | PK, FK â†’ master_vessel.vessel_id | One row per vessel |
| anniversary_date | DATE | NULL | Source of truth for survey-window computation |
| ship_type | NVARCHAR(32) | NN | (used by catalog `applicable_ship_types`) |
| marine_supt_user_id | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | (D-CERT-098) |
| technical_manager_user_id | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | (D-CERT-098) |
| slack_channel_vessel | NVARCHAR(64) | NULL | E.g. `#certs-vessel-yc-fortitude` (D-CERT-160) |
| slack_channel_office_default | NVARCHAR(64) | NULL | Vessel-specific override of default office channel |
| lifecycle_status | NVARCHAR(24) | NN, default 'active' | enum: `active \| onboarding_in_progress \| pending_disposal \| sold_pending_handover` |
| pending_disposal_started_at | DATETIME2 | NULL | (D-CERT-044 â€” 30-day countdown) |
| sale_handover_bundle_blob_id | UNIQUEIDENTIFIER | NULL, FK â†’ vims_certs_pdf_blob.blob_id | (D-CERT-093) |
| flag_change_pending | BIT | NN, default 0 | (D-CERT-094) |
| flag_change_event_json | NVARCHAR(MAX) | NULL | Most recent event |
| class_change_pending | BIT | NN, default 0 | (D-CERT-046) |
| mandatory_coverage_override_reason | NVARCHAR(MAX) | NULL | (D-CERT-119) |
| mandatory_coverage_override_at | DATETIME2 | NULL | |
| mandatory_coverage_override_by | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | |
| iws_age_gate_disabled | BIT | NN, default 0 | Computed disabled state for FEAT-CERT-CAT-012 / D-CERT-034 |
| iws_age_gate_disabled_at | DATETIME2(7) | NULL | First time the cron disabled IWS for this vessel |
| iws_age_gate_disabled_reason | NVARCHAR(256) | NULL | System reason, e.g. `vessel_age_exceeds_gate` |
| iws_age_gate_last_age_years | SMALLINT | NULL | Computed from `VesselData.YearBuilt`; `VesselData.Age` fallback only if YearBuilt is unavailable |
| iws_age_gate_last_evaluated_at | DATETIME2(7) | NULL | Written by onboarding + nightly recompute |
| iws_manual_override_enabled | BIT | NN, default 0 | DPA override for older IWS-enrolled vessels |
| iws_manual_override_reason | NVARCHAR(MAX) | NULL | Required by service validation when override is enabled |
| iws_manual_override_by | NVARCHAR(64) | NULL | Auth user id string |
| iws_manual_override_at | DATETIME2(7) | NULL | Latest override edit |
| created_at, updated_at, updated_by | (audit fields) | |

### 3.17 `vims_certs_modification_event` (D-CERT-047)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| modification_event_id | UNIQUEIDENTIFIER | PK | |
| group_started_at | DATETIME2 | NN | |
| group_window_ends_at | DATETIME2 | NN | (start + 30 days) |
| description | NVARCHAR(MAX) | NN | DPA-provided context |
| affected_tracked_item_ids_json | NVARCHAR(MAX) | NN | |
| created_by | UNIQUEIDENTIFIER | NN, FK â†’ master_user.id | |

### 3.18 `vims_certs_settings`

Single-row config table (or key-value pattern). Holds module-wide tunables not on `vims_certs_alert_config` (which is alert-specific).

### 3.19 `vims_certs_cert_change_log` (D-AUDRS-237/239 cross-module obligation â€” added 2026-06-12)

Append-only, per-field change log with **source-module attribution**. Required by the Audit module before its v1.1 External Audit phase: when Audit (or any other module) writes back `last_done_date` / `next_due_date` / validity to a tracked item, Certs must be able to show WHICH module changed WHAT. The RightShip module reads certs via loose `certificate_id` links only (never writes) â€” no rows from RS.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| change_id | UNIQUEIDENTIFIER | PK | |
| tracked_item_id | UNIQUEIDENTIFIER | NN, FK â†’ vims_certs_tracked_item.tracked_item_id | |
| field_name | NVARCHAR(64) | NN | column changed |
| old_value | NVARCHAR(MAX) | NULL | |
| new_value | NVARCHAR(MAX) | NULL | |
| version_after | INT | NN | tracked_item.version AFTER this write (CAS audit trail) |
| source_module | NVARCHAR(16) | NN | enum: `CERTS \| AUDIT \| SYSTEM` (extend per integrating module) |
| source_ref | NVARCHAR(64) | NULL | originating record id (e.g. audit_detail id) |
| changed_by | UNIQUEIDENTIFIER | NULL, FK â†’ master_user.id | NULL for system writes |
| changed_at | DATETIME2 | NN | |

**GRANT enforcement:** `vims_app` role has only `INSERT, SELECT` on this table (append-only â€” same regime as `vims_certs_audit_log`, D-CERT-179). Written in the SAME transaction as the tracked-item update.

---

## 4. Indexes & Constraints

| Table | Index | Purpose |
|-------|-------|---------|
| `vims_certs_catalog_row` | idx on `(section_id, is_active, print_order)` | Catalog UI render |
| `vims_certs_catalog_row` | UQ `canonical_code` | Identity |
| `vims_certs_tracked_item` | idx on `(vessel_id, status, expiry_date)` | Vessel dashboard + expiry alerts |
| `vims_certs_tracked_item` | idx on `(catalog_id)` | Catalog row "instances" tab |
| `vims_certs_tracked_item` | idx on `(approval_state, draft_expires_at)` | Draft expirer cron |
| `vims_certs_tracked_item` | idx on `(vessel_id, lifecycle_status)` | Lifecycle event scans |
| `vims_certs_pdf_blob` | UQ `(tracked_item_id, content_sha256)` | Per-row dedup (D-CERT-118) |
| `vims_certs_pdf_blob` | idx on `(scheduled_delete_at, is_active)` | Retention sweeper (D-CERT-021) |
| `vims_certs_class_status_snapshot` | idx on `(vessel_id, printed_on_date DESC)` | Snapshot list default sort (D-CERT-069) |
| `vims_certs_class_status_snapshot` | idx on `(parse_status)` | Failed/partial filter |
| `vims_certs_reconciliation_flag` | idx on `(run_id, bucket, resolved_at)` | Three-panel review filtering |
| `vims_certs_audit_log` | idx on `(timestamp_utc DESC, vessel_id)` | Hot-tier read |
| `vims_certs_audit_log` | idx on `(actor_user_id, timestamp_utc DESC)` | Per-actor audit |
| `vims_certs_audit_log` | idx on `(retention_tier, timestamp_utc)` | Tier-flip cron |
| `vims_certs_notification_meta` | UQ `idempotency_key` | (D-CERT-174) |
| `vims_certs_notification_meta` | idx on `(cert_row_id, escalation_level)` | Escalation worker |
| `vims_certs_print_artifact` | idx on `(timestamp_utc DESC)` | Print history |
| `vims_certs_print_artifact` | idx on `(user_id, timestamp_utc DESC)` | Soft-throttle volume check |
| `vims_certs_external_auditor_access` | idx on `(expiry_at)` | Auto-expire worker |
| `vims_certs_batch_ingest` | idx on `(vessel_id, status)` | Onboarding hub |

---

## 5. API Endpoint Catalog

All under `/api/certs/`. Auth: JWT (SimpleJWT) for primary users; signed token for `/auditor/<grant_token>/...` separate routing tree (defined under `/api/auditor/`). RBAC enforced via `permissions/certs_perms.py` checking `CERT_F_*` form ID + `CERT_P_*` process ID per endpoint.

### 5.1 Catalog
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| GET | `/api/certs/catalog/sections/` | (read-any-Cert) | All Certs roles | List 9 sections |
| GET | `/api/certs/catalog/rows/` | (read-any-Cert) | All Certs roles | Supports `sectionId`, `isActive`, `q`, `applicableShipType`, `page`, `pageSize`; `pageSize` is capped at 100 and implemented with SQL `OFFSET/FETCH` |
| GET | `/api/certs/catalog/rows/<catalog_id>/` | (read-any-Cert) | All Certs roles | Detail |
| POST | `/api/certs/catalog/rows/` | CERT_P_001 + CERT_P_008 | DPA + System Admin | Create row; rejects `submission_scope = master_only` per D-CERT-199 |
| PATCH | `/api/certs/catalog/rows/<catalog_id>/` | CERT_P_008 | DPA + System Admin | Update; rejects `submission_scope = master_only` per D-CERT-199 |
| POST | `/api/certs/catalog/rows/<catalog_id>/deprecate/` | CERT_P_008 | DPA | Soft-delete (is_active=false) |
| DELETE | `/api/certs/catalog/rows/<catalog_id>/` | CERT_P_008 + CERT_P_009 | DPA | Hard purge with cascade |
| POST | `/api/certs/catalog/rows/bulk-soft-delete/` | CERT_P_009 | DPA | Cap 50, reason required |
| POST | `/api/certs/catalog/push-to-fleet/<catalog_id>/` | CERT_P_009 | DPA | Auto-create pending_first_upload rows |
| POST | `/api/certs/catalog/anniversary-recompute/` | CERT_P_009 | DPA + FM 2nd approver | Bulk recompute with preview gate |
| GET | `/api/certs/catalog/export-csv/` | CERT_P_005 | DPA | CSV export of full catalog |

### 5.2 TrackedItems
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| GET | `/api/certs/tracked-items/?vessel_id=<imo>` | (read-vessel) | Per RBAC scope | List per vessel |
| GET | `/api/certs/tracked-items/<id>/` | (read-vessel) | Per RBAC scope | Detail |
| POST | `/api/certs/tracked-items/` | CERT_P_001 / CERT_P_002 | Per submission_scope rule | Create (direct or draft) |
| PATCH | `/api/certs/tracked-items/<id>/` | CERT_P_001 / CERT_P_002 | Per role + state | Edit |
| POST | `/api/certs/tracked-items/<id>/submit/` | CERT_P_002 | C/O / C/E / 2/E (own vessel) | draft â†’ pending_master_approval |
| POST | `/api/certs/tracked-items/<id>/approve/` | CERT_P_003 | Master (own vessel), DPA, PIC | pending_master_approval â†’ approved |
| POST | `/api/certs/tracked-items/<id>/reject/` | CERT_P_004 | Master (own vessel), DPA, PIC | pending_master_approval â†’ rejected; reason required |
| POST | `/api/certs/tracked-items/<id>/upload-pdf/` | CERT_P_001 | Master direct / DPA / FM / Sup'tts | Renewal vs revision auto-detect |
| GET | `/api/certs/tracked-items/<id>/pdfs/<blob_id>/view/` | (read-vessel) | Per RBAC scope | Authenticated PDF view stream |
| GET | `/api/certs/tracked-items/<id>/pdfs/` | (read-vessel) | Per RBAC | Active + superseded + pending-delete |
| POST | `/api/certs/tracked-items/<id>/anniversary/` | CERT_P_008 | DPA | Rare; confirmation flow |
| POST | `/api/certs/tracked-items/<id>/quarantine-resolve/` | CERT_P_001 | DPA | expired_at_onboarding â†’ expired or active |
| GET | `/api/certs/tracked-items/<id>/audit/` | CERT_F_008 read | Per audit-log RBAC | Per-entity audit history |

### 5.3 Class Snapshots & Reconciliation
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| POST | `/api/certs/class-snapshots/` | CERT_P_001 | DPA / FM / Sup'tts | Upload + invoke parser/reconciliation worker path immediately |
| GET | `/api/certs/class-snapshots/` | (read-vessel) | Per RBAC | Filter list |
| GET | `/api/certs/class-snapshots/<id>/` | (read-vessel) | Per RBAC | Detail |
| POST | `/api/certs/class-snapshots/<id>/reparse/` | CERT_P_001 | DPA + Tech Sup'tt | Manual re-parse trigger |
| POST | `/api/certs/class-snapshots/<id>/rollback/` | CERT_P_010 | Marine Sup'tt + DPA | Wrong-vessel rollback (D-CERT-058) |
| GET | `/api/certs/reconciliation/runs/` | (read-vessel) | Per RBAC | List runs |
| GET | `/api/certs/reconciliation/runs/<run_id>/` | (read-vessel) | Per RBAC | Detail + flags |
| POST | `/api/certs/reconciliation/flags/<flag_id>/notify-master/` | CERT_P_002 | Marine Sup'tt + DPA | Fire alert |
| POST | `/api/certs/reconciliation/flags/<flag_id>/mark-reviewed/` | CERT_P_002 | Marine Sup'tt + DPA | Resolve |
| POST | `/api/certs/reconciliation/flags/<flag_id>/add-mapping/` | CERT_P_008 | DPA | Update ClassCodeMapping |

### 5.4 Onboarding
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| POST | `/api/certs/onboarding/` | CERT_P_001 | DPA | Start session for vessel |
| GET | `/api/certs/onboarding/<vessel_id>/` | (read) | DPA + FM | Wizard state |
| POST | `/api/certs/onboarding/<vessel_id>/profile/` | CERT_P_001 | DPA | Step 2 |
| POST | `/api/certs/onboarding/<vessel_id>/batch/` | CERT_P_001 | DPA | Create batch with PDFs |
| GET | `/api/certs/onboarding/batch/<batch_id>/` | (read) | DPA | Gap-fill state |
| POST | `/api/certs/onboarding/batch/<batch_id>/preview/` | CERT_P_001 | DPA | Dry-run validation |
| POST | `/api/certs/onboarding/batch/<batch_id>/commit/` | CERT_P_002 | DPA | Commit + emit CSV |
| POST | `/api/certs/onboarding/batch/<batch_id>/cancel/` | CERT_P_010 | DPA | Cancel batch |
| POST | `/api/certs/onboarding/<vessel_id>/coverage-override/` | CERT_P_001 | DPA | Step 6 override + reason |
| POST | `/api/certs/onboarding/<vessel_id>/fm-signoff/` | CERT_P_002 | FM | Step 7 â†’ vessel goes live |
| POST | `/api/certs/onboarding/<vessel_id>/rollback/` | CERT_P_010 | DPA | Reset onboarding (pre-go-live) |

### 5.5 Print / Export
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| POST | `/api/certs/print/` | CERT_P_005 | Per scope RBAC | Generate (sync per-vessel; async fleet-wide) |
| GET | `/api/certs/print/jobs/<job_id>/` | (read) | Per scope | Async status |
| GET | `/api/certs/print/artifacts/` | (read) | Per scope | History |
| GET | `/api/certs/print/artifacts/<print_id>/` | (read) | Per scope | Detail + download links |
| POST | `/api/certs/print/share-bundle/` | CERT_P_006 | Master / DPA / FM | ZIP bundle |

### 5.6 Notifications
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| GET | `/api/certs/notifications/?module=certs` | (own inbox) | Self | Filter shared bell |
| POST | `/api/certs/notifications/<id>/ack/` | (self) | Self | In-app ack |
| GET | `/api/certs/notifications/ack/<token>/` | (token-bound) | Anyone with valid token | Magic-link landing |
| GET | `/api/certs/alerts/config/` | CERT_F_006 read | DPA | Settings |
| PATCH | `/api/certs/alerts/config/` | CERT_F_006 + CERT_P_008 | DPA | Update lead times / thresholds |

### 5.7 Auditor Access
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| GET | `/api/certs/auditor-access/` | CERT_F_007 read | Fleet Manager + Marine Sup'tt + DPA | List grants |
| POST | `/api/certs/auditor-access/` | CERT_P_007 | Marine Sup'tt + DPA | Create grant + email signup link |
| GET | `/api/certs/auditor-access/<grant_id>/` | CERT_F_007 read | Fleet Manager + Marine Sup'tt + DPA | Detail |
| PATCH | `/api/certs/auditor-access/<grant_id>/` | CERT_P_007 | Marine Sup'tt + DPA | Edit expiry only (effective revoke) |
| POST | `/api/auditor/signup/<token>/` | (token-bound) | Auditor | One-time signup |
| GET | `/api/auditor/<grant_token>/vessels/` | (token-bound) | Auditor | Scoped list |
| GET | `/api/auditor/<grant_token>/vessels/<imo>/certs/` | (token-bound) | Auditor | Scoped certs |
| GET | `/api/auditor/<grant_token>/cert/<id>/` | (token-bound) | Auditor | Read-only detail |
| POST | `/api/auditor/<grant_token>/print/` | (token-bound) | Auditor | AUDIT COPY watermarked |

### 5.8 Audit Log
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| GET | `/api/certs/audit-log/` | CERT_F_008 read | DPA + FM (full) / Sup'tts (own-vessel slice) | Filterable |
| GET | `/api/certs/audit-log/<id>/` | CERT_F_008 read | Per scope | Detail |
| POST | `/api/certs/audit-log/export/` | CERT_F_008 + CERT_P_005 | DPA only | Watermarked PDF + CSV |

### 5.9 Dashboard / Vessel Profile
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| GET | `/api/certs/dashboard/fleet/` | (read-vessel) | Per RBAC | Tile aggregates |
| GET | `/api/certs/dashboard/vessel/<imo>/` | (read-vessel) | Per RBAC | Per-vessel rollup |
| GET | `/api/certs/vessel/<imo>/profile/` | (read-vessel) | Per RBAC | Certs config |
| PATCH | `/api/certs/vessel/<imo>/profile/` | CERT_P_008 | DPA + FM | Update Certs-specific fields |
| POST | `/api/certs/vessel/<imo>/flag-change/` | CERT_P_008 | DPA | Record flag change event (D-CERT-094) |
| POST | `/api/certs/vessel/<imo>/class-change/` | CERT_P_008 | DPA | Record class change (D-CERT-046) |
| POST | `/api/certs/vessel/<imo>/sale-handover/` | CERT_P_008 | DPA | Initiate 30-day handover (D-CERT-093) |
| POST | `/api/certs/vessel/<imo>/decommission/` | CERT_P_008 | DPA | Initiate 30-day disposal (D-CERT-044) |

### 5.10 Settings
| Method | Path | Process ID | Roles | Notes |
|--------|------|------------|-------|-------|
| GET | `/api/certs/settings/` | (DPA-only) | DPA | All tunables |
| PATCH | `/api/certs/settings/` | (DPA-only) | DPA | Update + audit |

---

## 6. Service Layer Modules

### `services/ocr_pipeline.py`
- `process_cert_pdf(blob_id, vessel_context, threshold_band='office')` â†’ returns OCR result (per-field value + confidence + 80/85/60 banding); writes to `vims_certs_pdf_blob.ocr_payload_json`.
- Default engine is PaddleOCR through `PaddleOcrEngine`; wrapper interface remains stable.

### `services/parsers/`
- `BaseClassParser` interface: `parse(pdf_path) â†’ ParsedSnapshot`.
- One concrete parser per class society (NK / KR / BV) per D-CERT-005.
- Output normalized to common intermediate schema â†’ reconciliation engine.
- Class snapshot PDFs are text-extracted first per D-CERT-048. If the full PDF exposes no text layer, D-CERT-200 allows PaddleOCR fallback against rendered page images before the same NK/KR/BV parser modules run.
- Test fixtures = 6 reference PDFs (D-CERT-057); CI runs full corpus on every parser PR.

### `services/reconciliation.py`
- `reconcile(snapshot_id) â†’ ReconciliationRun` â€” applies ClassCodeMapping (versioned per D-CERT-061), buckets into Match / Mismatch / Missing-in-catalog / Missing-in-class / Conditional-STC / Extended-Postponed / Unmapped-low-conf.
- Anomaly detection per D-CERT-073; raises critical events when thresholds breached.

### `services/survey_window.py`
- `compute_window(tracked_item) â†’ (window_open, window_close, next_due_date)` â€” central source of truth per D-CERT-063 / D-CERT-064.
- IMO rules encoded as data tables; no per-class branching.

### `services/notification_dispatcher.py`
- `dispatch(trigger, cert_row, recipients_per_side)` â€” applies per-side routing (D-CERT-161), grouping (D-CERT-164), idempotency (D-CERT-174), retry (D-CERT-159), fallback to Slack DM if email bouncing.
- Writes to `master_notification` (in-app) + emits to `email_dispatcher` + Slack relay; logs to `vims_certs_notification_meta`.

### `services/slack_relay.py`
- Wrapper around `slack-sdk`; per-vessel + fleet-wide channel routing (D-CERT-160).

### `services/magic_link.py`
- `mint(notification_id, action='ack', ttl_h=24)` â†’ signed token URL.
- `verify(token)` â†’ notification_id or invalid; single-use enforced via DB nonce table (or by marking the notification ack with the token-binding).

### `services/pdf_renderer.py` / `services/excel_renderer.py` / `services/zip_bundler.py`
- Per FEAT-CERT-PRT-* features. Free-design layout; preserves SQE S 633 form code (D-CERT-125).
- Phase 0.8 renderer pick: `services/pdf_renderer.py` uses the ReportLab 4.2.0 fallback. WeasyPrint 68.1 was attempted with MSYS2/Pango runtime remediation on Windows, but failed real render verification; do not depend on WeasyPrint for V1 unless a later runtime smoke test passes.

### `services/system_state_hash.py`
- `compute_hash(vessel_id, scope) â†’ 8-char hash` for print identifiability (D-CERT-128).

### `services/coverage.py`
- `compute_mandatory_coverage(vessel_id) â†’ percent` for onboarding step 6 + dashboard banner (D-CERT-119).

### `services/auditor_token.py`
- Signed token issuance + verification for external auditor portal; bound to `vims_certs_external_auditor_access.grant_id`.

### `services/retention.py`
- Daily sweep: `vims_certs_pdf_blob.scheduled_delete_at <= now()` AND `is_active=false` â†’ soft-delete (move to delete-pending bucket); after 7d grace â†’ hard-delete (D-CERT-021).
- Respects `dpa_retention_override_until` and `retain_all_versions: true` flag.

---

## 7. OCR Pipeline

```
DPA / Master uploads PDF â†’ /api/certs/onboarding/<vessel>/batch/  OR
                          /api/certs/tracked-items/<id>/upload-pdf/
        â”‚
        â–¼
   PdfBlob inserted (content_sha256 dedup check first)
        â”‚
        â–¼
   OCR worker job enqueued (jobs/ocr_worker.py)
        â”‚
        â–¼
   services/ocr_pipeline.process_cert_pdf(blob_id)
        â”‚  - extract: cert type, IMO, dates, issuer, place, cert_number, optionals (D-CERT-105)
        â”‚  - per-field confidence
        â”‚  - threshold band: office (â‰¥80) or vessel (â‰¥85)
        â–¼
   PdfBlob.ocr_payload_json + ocr_confidence_per_field + ocr_processed_at written
        â”‚
        â–¼
   Notify DPA (in-app + email if office) / Master (in-app + email) â€” batch ready for review
        â”‚
        â–¼
   Gap-fill UI consumes ocr_payload_json + confidence map
        â”‚
        â–¼
   On commit: Validation gates per D-CERT-116 â†’ block / warn / pass
        â”‚
        â–¼
   TrackedItem inserts/updates within transaction; AuditLog writes
```

**OCR engine pluggability:** PaddleOCR is the current default engine (TECH_STACK Â§2). Interface in `services/ocr_pipeline.py` remains stable; concrete impl remains swappable.

**Concurrency:** Worker queue concurrency controlled at platform level. Per-vessel advisory lock (`vims_certs_class_status_snapshot.snapshot_upload_in_progress` or analogous) for class snapshot uploads (D-CERT-056) â€” does NOT apply to per-cert PDF uploads.

---

## 8. Reconciliation Engine

```
Class snapshot uploaded â†’ ClassStatusSnapshot inserted
        â”‚
        â–¼
   Parser worker job (jobs/parser_worker.py)
        â”‚  - invoked synchronously by upload and manual Reparse endpoints in this deployment
        â”‚  - parser_version stamped on success
        â”‚  - no-text-layer PDFs run bounded PaddleOCR fallback before parser failure is recorded
        â–¼
   Class society parser â†’ common intermediate schema
        â”‚
        â–¼
   services/reconciliation.reconcile(snapshot_id)
        â”‚  - Apply ClassCodeMapping (current version stamp on run)
        â”‚  - Per row: bucket (Match / Mismatch / Missing-in-catalog / Missing-in-class /
        â”‚    Conditional-STC / Extended-Postponed / Unmapped-low-conf)
        â”‚  - For Conditional-STC: pre-fill STC TrackedItem (relationship_type=short_term_for)
        â”‚  - For Extended: pre-fill child extension_of TrackedItem
        â”‚  - For Postponed: pre-fill parent's postponed_until
        â”‚  - For Conditions of Class section: write to vessel.conditions_of_class[] (D-CERT-066)
        â”‚  - Anomaly thresholds checked (D-CERT-073)
        â–¼
   ReconciliationRun + ReconciliationFlag rows inserted
        â”‚
        â–¼
   Marine Sup'tt notified (per-side: in-app + Slack)
        â”‚
        â–¼
   Three-panel UI (Â§3.10) renders flags by bucket
        â”‚
        â–¼
   Per-flag resolution: notify_master / mark_reviewed / add_mapping / dismiss
```

**Format-change FAIL SOFT:** Unparseable rows â†’ `unmapped_rows[]` in parsed_payload; reconciliation continues for mapped rows; DPA notified; >25% unmapped â†’ critical escalation (D-CERT-031).
**Whole-PDF text failure:** if `pdfplumber` extracts no text from the snapshot, PaddleOCR fallback runs against rendered page images. If OCR also reads no usable text, the snapshot remains stored with `parse_status=failed`, no reconciliation run is created, and the UI reports that the parser could not read the PDF.

**No fuzzy fallback:** Per D-CERT-031, parser does NOT attempt fuzzy mapping when class format changes. Workshop expansion of ClassCodeMapping is the human-in-loop path.

---

## 9. Notification Dispatcher

```
Trigger (cron / state change / mismatch / etc.)
        â”‚
        â–¼
   services/notification_dispatcher.dispatch(trigger, cert_row, ...)
        â”‚  1. Compute recipients per cadence + escalation level (D-CERT-089 / D-CERT-162)
        â”‚  2. Per-side route: vessel users â†’ in-app + email; office users â†’ in-app + Slack (D-CERT-161)
        â”‚  3. Group multi-cert same-vessel-same-day (D-CERT-164)
        â”‚  4. Compute idempotency_key = (cert_row_id, cadence, sent_date) (D-CERT-174)
        â”‚  5. Check existing notification_meta with this key (app-level dedup)
        â”‚  6. Write notification_meta + master_notification (DB UQ enforces (D-CERT-174))
        â”‚  7. Per channel: enqueue email (with magic-link button) / Slack message / no-op for in-app (already in DB)
        â–¼
   Email: 3x retry exponential backoff (1/5/30 min); on 3-fail flag user delivery_status=bouncing;
   if cert_row severity = critical (â‰¤7d expiry / expired), auto-fall-back to Slack DM (D-CERT-159)
        â”‚
        â–¼
   Magic-link click â†’ /api/certs/notifications/ack/<token>/ â†’ verify token â†’ ack written â†’
   notification_meta.ack_at + ack_user_id + ack_channel='magic_link'
        â”‚
        â–¼
   Hierarchical close on full resolution: cert renewed â†’ both vessel + office copies dismissed (D-CERT-085, D-CERT-087)
```

**Parser-anomaly notification resilience:** reconciliation run creation is authoritative. Parser-anomaly notification dispatch is best-effort when the shared `master_notification` table does not expose the Certs notification columns; schema errors are logged and must not roll back snapshot parsing or reconciliation run creation.

**Independent ack model (D-CERT-087):** Office and vessel each ack their own copy. Office dashboard surfaces `vessel_acked: yes/no` as a status flag.

**Catalog change fan-out (D-CERT-171):**
- Aggregate office Slack message: "DPA added/removed cert type X â€” N vessels affected â€” review pending uploads"
- Per-vessel Master email + in-app: "New cert type X required on your vessel; pending upload row created"

**Vessel go-live welcome (D-CERT-173):** Single welcome notification to Master at FM sign-off; pre-go-live cadence states NOT replayed.

**Monthly digest (D-CERT-158):** `jobs/digest_monthly.py` cron fires 1st of month 08:00 ICT; recipients = DPA + Marine Sup'tt only.

---

## 10. Survey-Window Computation

`services/survey_window.py` is the single source of truth. Inputs: `anniversary_date`, `cadence_months` (or `cadence_custom_days`), IMO survey window rules (e.g. Â±3 months for Renewal Survey, Â±2 months for Annual). Output: `(window_open, window_close, next_due_date)`.

**No per-class parsing of windows** (D-CERT-063, D-CERT-064). Class snapshot's NK `Range Date` column is read for sanity check only â€” if computed window disagrees by >7 days, raise a flag in reconciliation.

Recompute triggered:
- On TrackedItem create.
- On `anniversary_date` edit (rare, audited).
- On `cadence_months` change (catalog-level â†’ bulk recompute via FEAT-CERT-RBAC-025).
- Nightly cron for "next_due_date crossed" status flips.

---

## 11. Background Jobs

| Job | Schedule | Module | Notes |
|-----|----------|--------|-------|
| OCR worker | event-driven (queue) | `jobs/ocr_worker.py` | Per-PDF |
| Parser worker | event-driven | `jobs/parser_worker.py` | Per-snapshot, 5min timeout + 2x retry |
| Notification worker | event-driven | `jobs/notification_worker.py` | Drains dispatch queue |
| Retention sweeper | daily 02:00 UTC | `jobs/retention_sweeper.py` | PdfBlob purge per D-CERT-021 |
| Monthly digest | 1st of month 08:00 ICT | `jobs/digest_monthly.py` | DPA + Marine Sup'tt only (D-CERT-158) |
| Draft expirer | daily 03:00 UTC | `jobs/draft_expirer.py` | 7d auto-expire (D-CERT-076) |
| Audit archiver | nightly 04:00 UTC | `jobs/audit_archiver.py` | Hot â†’ cold tiering at 2y boundary (D-CERT-183) |
| Cadence cron | hourly | `jobs/cadence_cron.py` | Computes next_due / window flips; fires per-cadence alerts (90/60/30/14/7/1d + post-expiry) |
| Snapshot stale alert | daily | `jobs/snapshot_stale.py` | Per D-CERT-006 / D-CERT-007 |
| Auditor expirer | hourly | `jobs/auditor_expirer.py` | Auto-expire grants past expiry_at |
| Retention purge â€” audit log | nightly 05:00 UTC | `jobs/audit_purge.py` | Soft-delete past 5y; itself audited (D-CERT-091) |
| Bouncing-email metric | hourly | `jobs/bouncing_email_metric.py` | Updates DPA dashboard surface |
| Re-auth warning emitter | every 5 min | `jobs/reauth_warning.py` | 15-min + 5-min toast warnings per D-CERT-082 |

---

## 12. Audit Log Enforcement

**Single write path:** All Cert mutations go through `apps/certs/models/audit.py`'s helper:
```python
AuditLog.record(
    action='update_tracked_item',
    entity_type='tracked_item',
    entity_id=tracked_item.id,
    actor=request.user,
    vessel=tracked_item.vessel,
    before=before_dict,
    after=after_dict,
    reason=request.data.get('reason'),
    metadata={'submission_scope': catalog.submission_scope},
)
```
Helper enforces:
- Always records actor's role at event time (snapshot, not FK to mutable role).
- Always sets `retention_tier='hot'`.
- Always sets `timestamp_utc=now()` server-side (never client-supplied).
- Schema version locked.

**Read scope enforcement:** `views/audit_views.py` filters by RBAC scope:
- DPA + FM: full fleet.
- Marine / Tech Sup'tt: `WHERE vessel_id IN <master_RoleByVessel for current user>`.
- Other roles: 403.

**External auditor:** No access to audit log endpoints (D-CERT-196). Free-text reason redaction at view layer (`SerializerMethodField` redacts when `request.user.kind == 'external_auditor'`) per D-CERT-180.

---

## 13. Cross-Module Surface (DELIBERATELY NONE)

Per **D-CERT-176** (FEAT-CERT-XMOD-001 / FEAT-CERT-XMOD-002):

- Certs exposes **NO** API endpoints for sibling modules to call.
- Certs makes **NO** API calls to sibling modules.
- Certs holds **NO** FKs to sibling-module tables (besides shared `master_*` and `wrh_ship_time_config`).
- External auditor access is **per-module only** (D-CERT-178).
- Crew certs handled by **CMS â€” separate platform from VIMS** (D-CERT-177); Certs holds **zero crew PII** (FEAT-CERT-XMOD-004).

**Allowed shared platform consumption:**
- `master_user`, `master_vessel`, `master_role`, `master_RoleByVessel`, `Mapping_CrewAssReviewers` â€” shared identity + RBAC tables.
- `master_notification` â€” shared in-app inbox.
- `email_dispatcher` â€” shared email service.
- `wrh_ship_time_config` â€” vessel local time for re-auth (D-CERT-082).
- Company logo endpoint `GET /api/auth/company-logo/` â€” shared platform endpoint (D-CERT-127).
- `msc_profiles` â€” shared auth chain (CERT_F_* + CERT_P_*).

**Build-time guard:** Code review checklist (CLAUDE.md) blocks any `from apps.<sibling> import ...` line in `apps/certs/`. Same for HTTP calls to `/api/<sibling>/*` from Certs services.

---

## 14. External Auditor Subsystem

Separate routing tree at `/api/auditor/<grant_token>/...`. Backed by `services/auditor_token.py` token signing + `vims_certs_external_auditor_access` table.

**Provisioning flow (D-CERT-194):**
1. Marine Sup'tt (or DPA override) calls `POST /api/certs/auditor-access/` with auditor name, email, scope, expiry. Fleet Manager may read grant metadata/list/detail only, with no create/edit permission (B-EXT-01).
2. Server creates `vims_certs_external_auditor_access` row with `signup_token_hash` (SHA-256 of one-time signup token).
3. Server emails auditor a one-time-use signup link containing the raw token.
4. Auditor clicks link â†’ `POST /api/auditor/signup/<token>/` â†’ token verified, marked used, server issues a session token (also signed, bound to grant_id) â†’ auditor can now hit `/api/auditor/<session_token>/...`.

**Read enforcement:** Every `/api/auditor/<token>/...` view validates token â†’ loads grant â†’ checks scope (vessels list, sections, cert IDs) before serializing.

**Watermark application:** Print views called via auditor token always emit `watermark_applied='AUDIT_COPY'` with auditor name + grant expiry (D-CERT-138 / FEAT-CERT-EXT-010).

**No activity log (D-CERT-196):** Per-action audit logging suppressed for auditor sessions. Only `last_accessed_at` field on the grant row updated (one timestamp, not per-request).

**No early revoke (D-CERT-195):** Only path to terminate access early is editing `expiry_at` to a past timestamp (sets `revoked_via_expiry_edit=true` in audit log).

---

## 15. Build-Time Deferrals

Phase 0 picks (encoded in IMPLEMENTATION_PLAN.md):

1. **OCR engine** â€” **RESOLVED 2026-07-22: PaddleOCR.** Certs uses PaddleOCR for certificate PDF OCR and for bounded class-snapshot fallback. Wrapper interface stable; concrete impl swappable.
2. **HTML-to-PDF renderer for print** â€” **RESOLVED 2026-06-24:** ReportLab 4.2.0 fallback encoded in `apps.certs.services.pdf_renderer.ReportLabPdfRenderer`; WeasyPrint rejected after failed Windows native-runtime smoke test.
3. **Worker queue runtime** â€” match platform default (Celery / RQ / custom). Already inherited; no Certs-specific decision.
4. **Cold storage** â€” S3 Glacier vs equivalent for audit log + snapshot blob 5y+. Match platform default (D-CERT-183, D-CERT-191, D-CERT-193).
5. **Slack workspace + channel naming convention** â€” confirm with DPA; default `#certs-vessel-<slug>` per FEAT-CERT-NOTIF-020.

---

*End of BACKEND_STRUCTURE v1.0. Every column above must appear in `FIELD_MAP.md` showing its UI surface (or explicit "internal-only â€” never surfaced" with justification).*

---

## Appendix â€” Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `BACKEND_STRUCTURE.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` âœ“ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` Â§16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-004 | Fleet-wide office-controlled master catalog. | LOCKED |
| D-CERT-008 | Mismatch handling: alert + Master prompted to update. | LOCKED |
| D-CERT-016 | Per-cert alert rules per Â§6.1: window-open / window-closing / expiring / expired / STC closing / snapshot stale / refresh sugge... | LOCKED |
| D-CERT-018 | RBAC: Master = onboard admin. | LOCKED |
| D-CERT-019 | PDF blob storage: S3-compatible, AES-256 at rest, TLS 1.3 in transit, versioned. | LOCKED |
| D-CERT-022 | Tech stack inherited from Reporting + Safety. | LOCKED |
| D-CERT-038 | PSC profile / MoU info OUT of Certs scope. | LOCKED |
| D-CERT-050 | Vessel-to-PDF matching: IMO Number is authoritative. | LOCKED |
| D-CERT-052 | Parser version stored on each snapshot. | LOCKED |
| D-CERT-060 | Snapshot blob: metadata indefinite (hot); | LOCKED |
| D-CERT-090 | Office hierarchy = inherit PSC Inspection RBAC pattern (`VIMS DOCS/BACKEND_STRUCTURE.md Â§11`). | LOCKED |
| D-CERT-092 | Bulk-action permissions: (a) Catalog push of new cert type by DPA = auto-creates `pending_first_upload` row on every active ves... | LOCKED |
| D-CERT-099 | AMENDS D-CERT-091: Audit log retention revised to 5 years rolling (matches IMO ISM common policy). | LOCKED |
| D-CERT-108 | Cert hierarchy preservation = auto-detect + workshop review. | LOCKED |
| D-CERT-110 | Anniversary date discovery = manual DPA entry + Class Status Report cross-validation. | LOCKED |
| D-CERT-111 | IMO sourcing & vessel-cert binding. | LOCKED |
| D-CERT-123 | OCR processing = async per batch. | LOCKED |
| D-CERT-144 | Print performance budget: Per-vessel scope (default, ~4-6 pages, ~40 certs) = synchronous generation with progress bar UI ("Gen... | LOCKED |
| D-CERT-154 | Email-to-action = magic-link one-click ack. | LOCKED |
| D-CERT-166 | Vessel-side cert upload sources = PDF + bridge scanner only. | LOCKED |
| D-CERT-170 | Renewal vs. | LOCKED |
| D-CERT-189 | Encryption at-rest mechanism = inherits existing VIMS-wide policy. | LOCKED |
| D-CERT-190 | Key management = inherits existing VIMS-wide policy. | LOCKED |
