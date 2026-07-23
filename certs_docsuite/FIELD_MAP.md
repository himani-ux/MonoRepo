# VIMS Certificates Module â€” Field Map (DB â†’ API â†’ UI Trace)

> **Version:** 1.2
> **Last Updated:** 2026-06-24 (v1.2a â€” Phase 0.4 transcribed `vims_certs_settings` field rows after migration implementation. v1.2 â€” B-FM-01..05 RESOLVED: NEWSEQUENTIALID per D-AUDRS-271, ORM auto_now\*/request.user write path, `vims_jobs` retention role, 5y-rolling blanket retention, settings = structured single-row. v1.1 â€” KLOSS Step 2 realignment: naming rule; Â§22 renumber; new Â§23â€“Â§26; 11-check audit. v1.0: 2026-05-13)
> **Status:** ðŸŸ¢ Locked â€” Ready for Build (no open BLOCKED cells; `BLOCKERS.md` is the resolution audit trail)
> **Naming transformation rule (declared once, applied everywhere):** DB `snake_case` â†’ API `camelCase` (DRF serializer layer) â†’ React prop `camelCase` â†’ UI human-readable label. Dates render `dd-Mmm-yyyy` (D-CERT-131). Enum values cross layers verbatim (snake_case strings); UI maps them to display labels per DESIGN_SYSTEM glossary (D-CERT-132). Never improvise a per-file transformation.
> **Purpose:** Trace **every** persistent backend field through to its UI surface. Prevents the failure mode where a column exists, an endpoint serializes it, but no React component renders it â€” leading to wasted debugging time, support tickets asking "where does this show up?", and feature drift.
> **Source:** `BACKEND_STRUCTURE.md` (schema + endpoints) cross-referenced with `APP_FLOW.md` (screens + surfaces).
> **Authority:** This doc is the **acceptance gate for any migration that adds a column**. If a column ships without a FIELD_MAP entry showing its UI surface (or an explicit "internal-only â€” never surfaced" with justification), the merge is blocked per CLAUDE.md completion checklist.

---

## How to Read This Doc

Each `vims_certs_*` table gets one section. Each row in the section is one DB column:

| Column | API key | Component | Screen route | Role visibility | Status | Notes |

**Format note vs KLOSS Step 2 FIELD_MAP spec (declared deviation, 2026-06-12):** the framework's per-field table also carries Type / Required / Validation / Default / Owner FEAT-ID columns. In this docsuite those live in dedicated sibling docs rather than being duplicated here: **Type + Required + Default** â†’ `BACKEND_STRUCTURE.md` Â§3 (column-level schema), **Validation** â†’ `VALIDATION_RULES.md`, **Owner FEAT-ID** â†’ `COVERAGE.md` decision/feature matrix + `PRD.md`. This doc owns the DBâ†’APIâ†’UI seam only. The framework's information requirement is met across the suite; the split avoids drift between duplicated columns. Cross-cutting columns, delete policy, internal-only and computed fields are aggregated in Â§23â€“Â§26 below.

**Status legend:**
- âœ… **Built** â€” column exists in BACKEND, serialized into the API response, rendered by a named React component on a named route, gated to the named role(s).
- ðŸ”§ **Internal** â€” column exists in DB intentionally; never surfaced in UI; justification in Notes (e.g. server-only computation, retention metadata, idempotency key).
- ðŸ”’ **RBAC-redacted** â€” surfaced for some roles, redacted/hidden for others (e.g. external auditor view); redaction rule named in Notes.
- âš ï¸ **Missing UI (build-time flag)** â€” column exists or is planned in BACKEND, but no UI surface exists yet. **MUST be resolved during Phase 0/1 before merge.**

**During Phase 0+ build:** Every PR that adds a column adds a row here. Every PR that adds an API field adds a row here. Every PR that adds a UI binding updates the matching row here. Reviewer rejects the PR if FIELD_MAP isn't updated.

---

## Index

1. [`vims_certs_catalog_section`](#1-vims_certs_catalog_section)
2. [`vims_certs_catalog_row`](#2-vims_certs_catalog_row)
3. [`vims_certs_class_code_mapping`](#3-vims_certs_class_code_mapping)
4. [`vims_certs_tracked_item`](#4-vims_certs_tracked_item)
5. [`vims_certs_pdf_blob`](#5-vims_certs_pdf_blob)
6. [`vims_certs_class_status_snapshot`](#6-vims_certs_class_status_snapshot)
7. [`vims_certs_reconciliation_run`](#7-vims_certs_reconciliation_run)
8. [`vims_certs_reconciliation_flag`](#8-vims_certs_reconciliation_flag)
9. [`vims_certs_audit_log`](#9-vims_certs_audit_log)
10. [`vims_certs_alert_config`](#10-vims_certs_alert_config)
11. [`vims_certs_approval_event`](#11-vims_certs_approval_event)
12. [`vims_certs_notification_meta`](#12-vims_certs_notification_meta)
13. [`vims_certs_print_artifact`](#13-vims_certs_print_artifact)
14. [`vims_certs_external_auditor_access`](#14-vims_certs_external_auditor_access)
15. [`vims_certs_batch_ingest`](#15-vims_certs_batch_ingest)
16. [`vims_certs_vessel_config`](#16-vims_certs_vessel_config)
17. [`vims_certs_modification_event`](#17-vims_certs_modification_event)
18. [`vims_certs_settings`](#18-vims_certs_settings)
19. [Shared `master_*` consumption](#19-shared-master_-consumption)
20. [External Auditor Surface â€” Redaction Map](#20-external-auditor-surface--redaction-map)
21. [Audit Pass Checklist](#21-audit-pass-checklist)
22. [`vims_certs_cert_change_log` + `tracked_item.version` (amendment)](#22-vims_certs_cert_change_log--tracked_itemversion-d-audrs-237239-amendment-2026-06-12)
23. [Cross-Cutting Columns](#23-cross-cutting-columns)
24. [Delete Policy per Table](#24-delete-policy-per-table)
25. [Internal-Only Fields Index](#25-internal-only-fields-index)
26. [Computed / Derived Fields](#26-computed--derived-fields-api-only-no-db-column)

---

## 1. `vims_certs_catalog_section`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| section_id | `id` | `CatalogSidebar` | `/certs/catalog` | All Cert roles | âœ… | URL parameter |
| section_code | `code` | `CatalogSidebar`, `CertVesselDashboard.SectionAccordion` | `/certs/catalog`, `/certs/vessels/<imo>` | All Cert roles | âœ… | Used as accordion key |
| display_name | `displayName` | `CatalogSidebar`, `CertVesselDashboard.SectionAccordion`, `PrintBuilder.ScopeFilters` | `/certs/catalog`, `/certs/vessels/<imo>`, `/certs/print` | All Cert roles | âœ… | Sidebar label, accordion header |
| sort_order | `sortOrder` | (sort param only) | â€” | â€” | ðŸ”§ | Server-side sort key; not displayed |
| created_at, created_by | â€” | â€” | â€” | â€” | ðŸ”§ | Audit trail; reachable via `/certs/audit-log` filtered query, not directly rendered on this entity |

---

## 2. `vims_certs_catalog_row`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| catalog_id | `id` | `CatalogTable.row`, `CatalogRowDetail` | `/certs/catalog`, `/certs/catalog/<id>` | All Cert read; DPA write | âœ… | URL param |
| canonical_code | `canonicalCode` | `CatalogTable.col`, `CatalogRowDetail.header`, `CertCard.codeChip` | `/certs/catalog`, `/certs/catalog/<id>`, `/certs/vessels/<imo>/cert/<id>` | All Cert | âœ… | Immutable post-creation |
| section_id | `sectionId` | `CatalogTable.col` (joined to section name), sidebar grouping | `/certs/catalog` | All Cert | âœ… | Joined to `section.display_name` |
| display_name | `displayName` | `CatalogTable.col`, `CatalogRowDetail`, `CertCard.title`, `GapFillForm.certTypeDropdown`, `PrintBuilder` | most screens | All Cert | âœ… | Primary human label |
| short_name | `shortName` | `CertCard.acronymChip`, `PrintBuilder.compactView` | `/certs/vessels/<imo>`, `/certs/print` | All Cert | âœ… | Optional; hidden if null |
| print_section_label | `printSectionLabel` | `PrintArtifactPdfTemplate` (server-side renderer) | print PDF output | DPA edit | âœ… | Renders into print artifact, not interactive UI |
| validity_type | `validityType` | `CatalogRowDetail.metadata`, `TrackedItemDetail.metadataPanel`, `PrintArtifactPdfTemplate.validityCol` | several | All Cert | âœ… | Enum dropdown in editor |
| cadence_months | `cadenceMonths` | `CatalogRowDetail`, `TrackedItemDetail.metadataPanel` | `/certs/catalog/<id>`, `/certs/vessels/<imo>/cert/<id>` | All Cert | âœ… | Numeric input |
| cadence_custom_days | `cadenceCustomDays` | `CatalogRowDetail` (conditional render when type = custom_days) | `/certs/catalog/<id>` | DPA edit | âœ… | |
| issuing_authority_type | `issuingAuthorityType` | `CatalogRowDetail`, `GapFillForm` | several | DPA edit | âœ… | Enum dropdown |
| is_class_tracked | `isClassTracked` | `CatalogRowDetail`, `CertVesselDashboard.filterChip`, `CertCard.classTrackedBadge`, `ReconciliationEngine` (server logic) | several | All Cert | âœ… | Boolean toggle |
| submission_scope | `submissionScope` | `CatalogRowDetail`, `TrackedItemDetail.workflowPanel` (gates buttons) | `/certs/catalog/<id>`, `/certs/vessels/<imo>/cert/<id>` | All Cert | âœ… | Drives RBAC for submit/approve buttons |
| parent_id | `parentId` | `CatalogTable` (indented child row), `CatalogRowDetail.parentBreadcrumb`, `CertCard.parentBreadcrumb`, `PrintArtifactPdfTemplate.subnumbering` | several | All Cert | âœ… | UI 2-level cap per D-CERT-010 |
| relationship_type_default | `relationshipTypeDefault` | `CatalogRowDetail.metadata` | `/certs/catalog/<id>` | DPA edit | âœ… | |
| applicable_ship_types | `applicableShipTypes` | `CatalogRowDetail.shipTypeMultiselect`, `OnboardingWizard.step2.preview` (count of pre-pop rows) | `/certs/catalog/<id>`, `/certs/onboarding/<imo>` | DPA edit | âœ… | JSON array â†’ multi-select chips |
| mandatory_for_all_vessels | `mandatoryForAllVessels` | `CatalogRowDetail`, `CoverageBanner` (drives D-CERT-119 calculation) | `/certs/catalog/<id>`, `/certs/vessels/<imo>` | All Cert | âœ… | |
| applicability_mode | `applicabilityMode` | `CatalogRowDetail` (toggles specific_vessel_ids picker) | `/certs/catalog/<id>` | DPA edit | âœ… | |
| specific_vessel_ids | `specificVesselIds` | `CatalogRowDetail.vesselPicker` (conditional) | `/certs/catalog/<id>` | DPA edit | âœ… | |
| parent_supports_dynamic_children | `parentSupportsDynamicChildren` | `CatalogRowDetail.flagBadge`, `OnboardingWizard.gapFill.addInstanceButton`, `CertVesselDashboard.addInstanceButton` | several | All Cert | âœ… | Drives "Add another instance" UX |
| age_gate_max_years | `ageGateMaxYears` | `CatalogRowDetail`, nightly recompute job | `/certs/catalog/<id>` | DPA edit | âœ… | E.g. 15 for IWS |
| retain_all_versions | `retainAllVersions` | `CatalogRowDetail`, retention sweeper | `/certs/catalog/<id>` | DPA edit | âœ… | CSR override flag |
| linked_pms_component_id | `linkedPmsComponentId` | `CatalogRowDetail.metadata` | `/certs/catalog/<id>` | DPA edit | âš ï¸ | Stored for V1; cross-module fetch deferred per D-CERT-176. **Phase 0 build: confirm field appears as inert text input + tooltip "Cross-module integration deferred â€” value stored only".** |
| alert_lead_overrides | `alertLeadOverrides` | `CatalogRowDetail.alertOverridesEditor` | `/certs/catalog/<id>` | DPA edit | âœ… | JSON editor; defaults to alert_config table values |
| regulatory_anchor | `regulatoryAnchor` | `CatalogRowDetail`, `CertCard.tooltip` | several | All Cert | âœ… | E.g. "MARPOL Annex I Reg 7" |
| legacy_remarks | `legacyRemarks` | `CatalogRowDetail.history`, `PrintArtifactPdfTemplate.remarksCol` | several | All Cert | âœ… | From S 633 import |
| print_order | `printOrder` | (sort param) | â€” | â€” | ðŸ”§ | Server sort key |
| is_active | `isActive` | `CatalogTable.statusBadge`, `CatalogRowDetail.deprecateButton` | `/certs/catalog`, `/certs/catalog/<id>` | All Cert | âœ… | |
| created_at, created_by, updated_at, updated_by | `createdAt`, `createdBy`, `updatedAt`, `updatedBy` | `CatalogRowDetail.auditChip`, `AuditLogTable` | `/certs/catalog/<id>`, `/certs/audit-log` | DPA + FM full; Sup'tts assigned | âœ… | Joined to user.full_name |

---

## 3. `vims_certs_class_code_mapping`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| mapping_id | `id` | `MappingEditorTable.row` | settings sub-screen / reconciliation flag "Add to Mapping" modal | DPA + Tech Sup'tt | âœ… | |
| class_society | `classSociety` | `MappingEditorTable.col`, `ReconciliationReviewPanel.classChip` | several | All Cert | âœ… | |
| class_code_or_name | `classCodeOrName` | `MappingEditorTable.col`, `ReconciliationReviewPanel.diffPanel` | several | All Cert | âœ… | |
| catalog_id | `catalogId` | `MappingEditorTable.col` (joined to catalog.display_name) | several | All Cert | âœ… | |
| cert_or_survey_kind | `certOrSurveyKind` | `MappingEditorTable.col` | mapping editor | DPA + Tech Sup'tt | âœ… | |
| notes | `notes` | `MappingEditorRow.notesField` | mapping editor | DPA edit | âœ… | |
| version | `version` | `ReconciliationRunCard.mappingVersionBadge`, `MappingEditorTable` | `/certs/reconciliation/<run_id>`, mapping editor | All Cert | âœ… | |
| active | `active` | `MappingEditorTable.statusToggle` | mapping editor | DPA edit | âœ… | |
| created_at, created_by, updated_at, updated_by | `createdAt`, `createdBy`, `updatedAt`, `updatedBy` | `MappingEditorTable`, `AuditLogTable` | mapping editor, `/certs/audit-log` | DPA + FM | âœ… | |

---

## 4. `vims_certs_tracked_item`

This is the largest table; every column matters.

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| tracked_item_id | `id` | `CertCard`, `TrackedItemDetail` | `/certs/vessels/<imo>`, `/certs/vessels/<imo>/cert/<id>` | Per RBAC scope | âœ… | URL param |
| vessel_id | `vesselId`, `vesselName`, `vesselCode`, `vesselImo` | `TrackedItemDetail.header` (joined to vessel name) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | API joins `VesselData`; UI displays vessel name/code/IMO, never raw UUID when a label is available |
| catalog_id | `catalogId` | `CertCard.title` (joined display_name), `TrackedItemDetail.header.canonicalCodeChip` | several | Per RBAC | âœ… | |
| type | `type` | `TrackedItemDetail.typeChip` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| validity_type | `validityType` | `TrackedItemDetail.metadataPanel`, `CertCard.validityShortCode` (mapped via D-CERT-132 table) | several | Per RBAC | âœ… | Maps to A / Bi-A / 5-Y / Perm. / ST short codes |
| form_variant | `formVariant` | `TrackedItemDetail.metadataPanel` (conditional render for IOPP) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | Per D-CERT-032 |
| cadence_months | `cadenceMonths` | `TrackedItemDetail.metadataPanel` (override badge if differs from catalog) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC; DPA edit | âœ… | |
| cadence_custom_days | `cadenceCustomDays` | `TrackedItemDetail.metadataPanel` (conditional) | `/certs/vessels/<imo>/cert/<id>` | DPA edit | âœ… | |
| parent_id | `parentId` | `TrackedItemDetail.hierarchyBreadcrumb`, `CertCard.parentChip` | several | Per RBAC | âœ… | UI 2-level cap |
| relationship_type | `relationshipType` | `TrackedItemDetail.relationshipBadge` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| supersedes_id | `supersedesId` | `TrackedItemDetail.supersedesLink`, `TrackedItemDetail.predecessorChip` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | Clickable to predecessor row |
| issue_date | `issueDate` | `CertCard.issueDate`, `TrackedItemDetail.dates`, `PrintTemplate.issueDateCol` | several | Per RBAC | âœ… | Format `dd-Mmm-yyyy` per D-CERT-131 |
| expiry_date | `expiryDate` | `CertCard.expiryDate`, `TrackedItemDetail.dates`, `PrintTemplate.expiryCol`, `DashboardKpiCards.expiringSoon` | several | Per RBAC | âœ… | "Permanent" rendered when null + validity_type=permanent |
| anniversary_date | `anniversaryDate` | `TrackedItemDetail.metadataPanel` (read-only display + edit-confirm modal), `VesselProfileScreen` | `/certs/vessels/<imo>/cert/<id>`, `/certs/vessels/<imo>/profile` | Per RBAC; DPA edit | âœ… | Rare edit; audit-required confirm dialog (D-CERT-074) |
| window_open | `windowOpen` | `TrackedItemDetail.dates` (with computed-tooltip), `CertCard.statusPill` (drives status state) | several | Per RBAC | âœ… | Server-computed per D-CERT-063 |
| window_close | `windowClose` | `TrackedItemDetail.dates`, `CertCard.statusPill` | several | Per RBAC | âœ… | Server-computed |
| last_done_date | `lastDoneDate` | `TrackedItemDetail.dates`, `PrintTemplate.lastDoneCol` (for surveys) | several | Per RBAC | âœ… | |
| next_due_date | `nextDueDate` | `TrackedItemDetail.dates`, `CertCard.daysToGo` | several | Per RBAC | âœ… | Server-computed |
| postponed_until | `postponedUntil` | `TrackedItemDetail.dates`, `CertCard.postponedBadge` | several | Per RBAC | âœ… | (D-CERT-065) |
| status | `status` | `CertCard.statusPill` (color+shape per D-CERT-135), `TrackedItemDetail.statusPill`, `DashboardKpiCards`, `PrintTemplate.statusCol`, `CertVesselDashboard.filterChip` | most screens | Per RBAC | âœ… | Computed at read time except `superseded`, `expired_at_onboarding`, `pending_first_upload`, `invalid_due_to_reflag`, `pending_supersession` |
| certificate_number | `certificateNumber` | `TrackedItemDetail.metadataPanel`, `CertCard.certNumberChip` (when not bypassed), `PrintTemplate.certNoCol` | several | Per RBAC; nullable when bypassed | âœ… | Bypass UX per D-CERT-105 |
| issuing_authority | `issuingAuthority` | `TrackedItemDetail.metadataPanel`, `CertCard.issuerChip`, `PrintTemplate.issuerCol` | several | Per RBAC | âœ… | |
| place_of_issue | `placeOfIssue` | `TrackedItemDetail.metadataPanel`, `PrintTemplate.placeCol` | several | Per RBAC | âœ… | |
| extension_authority | `extensionAuthority` | `TrackedItemDetail.metadataPanel` (conditional) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| extension_letter_pdf_id | `extensionLetterPdfId` | `TrackedItemDetail.attachmentsList` (extension letter visible) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| extension_reason | `extensionReason` | `TrackedItemDetail.metadataPanel` (conditional) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| pdf_attachment_id | `pdfAttachmentId` | `TrackedItemDetail.pdfPreview`, `CertCard.pdfChip` | several | Per RBAC | âœ… | |
| pdf_missing | `pdfMissing` | `TrackedItemDetail.missingPdfBanner`, `CertCard.missingPdfBadge`, `DashboardKpiCards.incompleteDocsKpi` | several | Per RBAC | âœ… | (D-CERT-113) |
| source | `source` | `TrackedItemDetail.metadataPanel.sourceChip` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | enum: manual / class_snapshot / migration |
| last_class_sync_id | `lastClassSyncId` | `TrackedItemDetail.lastSyncLink` (clickable to snapshot) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| approval_state | `approvalState` | `TrackedItemDetail.workflowPanel.statePill`, `CertCard.approvalBadge` (when != approved), `ApprovalQueueTable` | several | Per RBAC | âœ… | (D-CERT-076) |
| submitted_by | `submittedBy`, `submittedByDisplay` | `TrackedItemDetail.workflowPanel`, `ApprovalQueueTable.submitterCol` | `/certs/vessels/<imo>/cert/<id>`, approval queue | Per RBAC | âœ… | `submittedByDisplay` joins office/crew identity; UI suppresses raw UUID fallback |
| submitted_at | `submittedAt` | same | same | Per RBAC | âœ… | |
| approved_by | `approvedBy`, `approvedByDisplay` | `TrackedItemDetail.workflowPanel.approverChip` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | `approvedByDisplay` joins office/crew identity; UI suppresses raw UUID fallback |
| approved_at | `approvedAt` | same | same | Per RBAC | âœ… | |
| rejection_reason | `rejectionReason` | `TrackedItemDetail.rejectionCallout` (conditional render) | `/certs/vessels/<imo>/cert/<id>` | Per RBAC; ðŸ”’ redacted in external auditor view per D-CERT-180 | ðŸ”’ | Free-text |
| rejection_count | `rejectionCount` | `TrackedItemDetail.rejectionCallout`, FM dashboard auto-flag at 3 (D-CERT-080) | several | Per RBAC | âœ… | |
| draft_expires_at | `draftExpiresAt` | `TrackedItemDetail.workflowPanel.draftExpiryWarning`, draft expirer cron consumer | `/certs/vessels/<imo>/cert/<id>` | Submitter | âœ… | |
| lifecycle_status | `lifecycleStatus` | `TrackedItemDetail.lifecycleBadge`, `CertVesselDashboard.banner` | several | Per RBAC | âœ… | |
| row_version | `rowVersion` | (concurrency token, server-only) | â€” | â€” | ðŸ”§ | D-CERT-088 race resolution; sent in PATCH body but never displayed |
| created_at, created_by, updated_at, updated_by | `createdAt`, `createdBy`, `createdByDisplay`, `updatedAt`, `updatedBy`, `updatedByDisplay` | `TrackedItemDetail.auditChip`, `AuditLogTable` | several | DPA + FM; Sup'tts scope | âœ… | Display fields join office/crew identity; UI must not expose raw UUID as the human label |

---

## 5. `vims_certs_pdf_blob`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| blob_id | `id` | `PdfPreview`, `VersionHistoryTray` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| tracked_item_id, snapshot_id | `trackedItemId`, `snapshotId` | (back-references for navigation) | several | Per RBAC | âœ… | One of these is non-null per blob |
| blob_storage_path | (signed URL only via API) | `PdfPreview.iframe`, `DownloadButton` | several | Per RBAC | ðŸ”’ | Raw S3 path never sent to client; signed download URL minted per request |
| filename | `filename` | `VersionHistoryTray.row`, `DownloadButton.label` | several | Per RBAC | âœ… | Original upload name |
| content_sha256 | (not exposed to UI) | â€” | â€” | â€” | ðŸ”§ | Used for dedup per D-CERT-118; server-only |
| content_size_bytes | `sizeBytes` | `VersionHistoryTray.sizeChip`, `DownloadButton.tooltip` | several | Per RBAC | âœ… | Human-formatted (KB/MB) |
| uploaded_by, uploaded_at | `uploadedBy`, `uploadedByDisplay`, `uploadedAt` | `VersionHistoryTray.row`, `PdfPreview.uploadInfo` | several | Per RBAC | âœ… | `uploadedByDisplay` joins office/crew identity; UI suppresses raw UUID fallback |
| is_active | `isActive` | `VersionHistoryTray.activeBadge` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | Old versions grayed |
| superseded_at | `supersededAt` | `VersionHistoryTray.row` | same | Per RBAC | âœ… | |
| retention_policy | `retentionPolicy` | `VersionHistoryTray.tooltip` | same | Per RBAC | âœ… | Surfaces policy name |
| scheduled_delete_at | `scheduledDeleteAt` | `VersionHistoryTray.deleteCountdown` (for non-active blobs in delete-pending) | same | Per RBAC | âœ… | |
| delete_pending_since | `deletePendingSince` | same | same | Per RBAC | âœ… | 7-day grace banner |
| dpa_retention_override_until | `dpaRetentionOverrideUntil` | `VersionHistoryTray.overrideBadge`, settings extend-retention modal | several | DPA | âœ… | (D-CERT-021) |
| ocr_payload_json | `ocrPayload` | `GapFillForm` (consumes for pre-fill); `TrackedItemDetail.ocrDebugDrawer` (Tech Sup'tt only) | onboarding gap-fill, cert detail | DPA / Master / Tech Sup'tt | âœ… | Drives gap-fill UX |
| ocr_confidence_per_field | `ocrConfidencePerField` | `GapFillForm.fieldHighlight` (drives 80/85/60 banding) | onboarding gap-fill | DPA / Master | âœ… | Color-coded per band |
| ocr_processed_at | `ocrProcessedAt` | `GapFillForm.headerChip`, `BatchIngestRow.ocrCompletedAt` | onboarding | DPA | âœ… | |
| ocr_engine_version | `ocrEngineVersion` | `TrackedItemDetail.ocrDebugDrawer` (Tech Sup'tt only) | cert detail | Tech Sup'tt | âœ… | Diagnostic |
| schema_version | (not displayed) | â€” | â€” | â€” | ðŸ”§ | Migration / parser drift detection |

---

## 6. `vims_certs_class_status_snapshot`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| snapshot_id | `id` | `SnapshotListTable.row`, `ReconciliationRunCard` | `/certs/reconciliation` | Per RBAC | âœ… | |
| vessel_id | `vesselId` | joined to vessel name in `SnapshotListTable.col` | `/certs/reconciliation` | Per RBAC | âœ… | |
| class_society | `classSociety` | `SnapshotListTable.col`, `ReconciliationRunCard.chip` | several | Per RBAC | âœ… | |
| pdf_blob_id | `pdfBlobId` | `SnapshotDetailScreen.openOriginalButton` (per D-CERT-148) | snapshot detail, `/certs/reconciliation/<run_id>` | Per RBAC | âœ… | Always retained per D-CERT-020 |
| printed_on_date | `printedOnDate` | `SnapshotListTable.col` (default sort), `ReconciliationRunCard.dateChip` | several | Per RBAC | âœ… | |
| uploaded_by, uploaded_at | `uploadedBy`, `uploadedAt` | `SnapshotListTable.col` | `/certs/reconciliation` | Per RBAC | âœ… | |
| parser_version | `parserVersion` | `SnapshotDetailScreen.metadata`, `ReconciliationRunCard.parserVersionBadge`, ParserOpsPage | several; ParserOps = Tech Sup'tt only | Per RBAC; Tech Sup'tt | âœ… | |
| parse_status | `parseStatus` | `SnapshotListTable.statusBadge`, `SnapshotDetailScreen.statusBanner` | `/certs/reconciliation` | Per RBAC | âœ… | enum: success / partial / failed / pending |
| parse_started_at, parse_completed_at | `parseStartedAt`, `parseCompletedAt` | `SnapshotDetailScreen.metadata`, ParserOpsPage | snapshot detail | Per RBAC; Tech Sup'tt for ParserOps | âœ… | |
| parser_timeout | `parserTimeout` | `SnapshotDetailScreen.errorBanner` (when true) | snapshot detail | Per RBAC | âœ… | |
| retry_count | `retryCount` | ParserOpsPage | dev-only feature-flagged | Tech Sup'tt | âœ… | |
| parsed_payload_json | `parsedPayload` | `ReconciliationReviewPanel.diffPanel` (consumes for class-side display); ParserOpsPage rawView | reconciliation review | Per RBAC; Tech Sup'tt for raw | âœ… | |
| parsed_payload_schema_version | (not displayed) | â€” | â€” | â€” | ðŸ”§ | |
| reconciliation_run_id | `reconciliationRunId` | `SnapshotDetailScreen.runLink` | snapshot detail | Per RBAC | âœ… | Click to `/certs/reconciliation/<run_id>` |
| upload_sha256 | (not displayed) | â€” | â€” | â€” | ðŸ”§ | Dedup per D-CERT-051 |
| superseded_user_error | `supersededUserError` | `SnapshotListTable.errorBadge` | `/certs/reconciliation` | Per RBAC | âœ… | Wrong-vessel rollback marker |

---

## 7. `vims_certs_reconciliation_run`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| run_id | `id` | `ReconciliationDashboard.row`, `ReconciliationReviewScreen` | `/certs/reconciliation`, `/certs/reconciliation/<run_id>` | Per RBAC | âœ… | |
| snapshot_id | `snapshotId` | `ReconciliationRunCard.snapshotLink` | several | Per RBAC | âœ… | |
| ran_at | `ranAt` | `ReconciliationDashboard.col` | `/certs/reconciliation` | Per RBAC | âœ… | |
| matches_count, mismatches_count, missing_in_catalog_count, missing_in_class_count, conditional_stc_detected_count, extended_postponed_detected_count, unmapped_low_confidence_count | `matchesCount`, `mismatchesCount`, etc. | `ReconciliationDashboard.bucketCounts`, `ReconciliationReviewScreen.tabBadges`, `DashboardKpiCards.mismatchKpi` | several | Per RBAC | âœ… | |
| flags_json | (loaded as separate `vims_certs_reconciliation_flag` rows) | â€” | â€” | â€” | ðŸ”§ | Aggregated for dashboard; per-flag detail via separate endpoint |
| notifications_sent_json | `notificationsSent` | `ReconciliationReviewScreen.notificationHistoryDrawer` | `/certs/reconciliation/<run_id>` | Per RBAC | âœ… | |
| mapping_version_used | `mappingVersionUsed` | `ReconciliationRunCard.mappingVersionBadge` | several | Per RBAC | âœ… | (D-CERT-061) |
| anomaly_breaches_json | `anomalyBreaches` | `ReconciliationReviewScreen.anomalyBanner` (top of screen when non-empty) | `/certs/reconciliation/<run_id>` | Per RBAC | âœ… | (D-CERT-073) |

---

## 8. `vims_certs_reconciliation_flag`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| flag_id | `id` | `ReconciliationReviewScreen.tabRow` | `/certs/reconciliation/<run_id>` | Per RBAC | âœ… | |
| run_id | `runId` | (URL context) | same | Per RBAC | âœ… | |
| bucket | `bucket` | `ReconciliationReviewScreen.tabRoute` | same | Per RBAC | âœ… | Drives which tab the flag appears in |
| catalog_id | `catalogId` | `ReconciliationReviewPanel.diffPanel.catalogSide` | same | Per RBAC | âœ… | Joined to catalog.display_name |
| tracked_item_id | `trackedItemId` | `ReconciliationReviewPanel.diffPanel.trackedItemSide` | same | Per RBAC | âœ… | Click â†’ cert detail |
| class_row_extract_json | `classRowExtract` | `ReconciliationReviewPanel.diffPanel.classSide` | same | Per RBAC | âœ… | |
| diff_json | `diff` | `ReconciliationReviewPanel.diffPanel.diffHighlight` | same | Per RBAC | âœ… | |
| reviewed_by, reviewed_at | `reviewedBy`, `reviewedAt` | `ReconciliationReviewPanel.row.reviewerChip` | same | Per RBAC | âœ… | |
| resolution_action | `resolutionAction` | `ReconciliationReviewPanel.row.actionBadge` | same | Per RBAC | âœ… | enum |
| resolved_at | `resolvedAt` | `ReconciliationReviewPanel.row` | same | Per RBAC | âœ… | |

---

## 9. `vims_certs_audit_log`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| audit_id | `id` | `AuditLogTable.row` | `/certs/audit-log` | DPA + FM full; Sup'tts scoped | âœ… | |
| timestamp_utc | `timestampUtc` | `AuditLogTable.col` (rendered in user's TZ + UTC tooltip) | `/certs/audit-log`, entity audit history drawers | Per RBAC | âœ… | |
| vessel_id | `vesselId` | `AuditLogTable.col` (joined to vessel name) | `/certs/audit-log` | Per RBAC | âœ… | |
| actor_user_id | `actorUserId`, `actorDisplayName` | `AuditLogTable.col`, `TrackedItemDetail.auditTrail` (joined to user.full_name) | `/certs/audit-log`, `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | Display field joins office/crew identity; UI suppresses raw UUID fallback |
| actor_role | `actorRole` | `AuditLogTable.col` | `/certs/audit-log` | Per RBAC | âœ… | Snapshot of role at event time |
| action | `action` | `AuditLogTable.col`, filter dropdown | `/certs/audit-log` | Per RBAC | âœ… | |
| entity_type | `entityType` | `AuditLogTable.col`, filter dropdown | `/certs/audit-log` | Per RBAC | âœ… | |
| entity_id | `entityId` | `AuditLogTable.entityLink` (clickable to entity detail) | `/certs/audit-log` | Per RBAC | âœ… | UUID-backed entity reference. Text-keyed entities such as print artifacts keep this NULL and expose the text reference in `eventMetadata.entityRef`. |
| before_json | `before` | `AuditLogTable.row.expandedDiff` | `/certs/audit-log` | Per RBAC | âœ… | Collapsible JSON viewer |
| after_json | `after` | same | same | Per RBAC | âœ… | |
| reason | `reason` | `AuditLogTable.row.reasonCol` | `/certs/audit-log` | DPA + FM full text; Sup'tts (own-vessel) full text; **ðŸ”’ redacted to `[REDACTED â€” internal note]` for external auditor view** per D-CERT-180 | ðŸ”’ | |
| event_metadata | `eventMetadata` | `AuditLogTable.row.metadataDrawer` | `/certs/audit-log` | Per RBAC | âœ… | Includes `entityRef` for text-keyed entities such as `vims_certs_print_artifact.print_id`. |
| retention_tier | `retentionTier` | `AuditLogTable.tierBadge`, fetch-from-cold prompt | `/certs/audit-log` | Per RBAC | âœ… | |
| archived_at | `archivedAt` | `AuditLogTable.tierBadge.tooltip` | `/certs/audit-log` | Per RBAC | âœ… | |
| schema_version | (not displayed) | â€” | â€” | â€” | ðŸ”§ | |

---

## 10. `vims_certs_alert_config`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| config_id | `id` | `AlertConfigTable.row` | `/certs/settings` (Alert Lead Times tab) | DPA | âœ… | |
| trigger_event | `triggerEvent` | `AlertConfigTable.col` | settings | DPA | âœ… | |
| default_lead_days | `defaultLeadDays` | `AlertConfigTable.col` (immutable display) | settings | DPA | âœ… | |
| dpa_override_lead_days | `dpaOverrideLeadDays` | `AlertConfigTable.col.editable` | settings | DPA edit | âœ… | |
| recipients_default_json | `recipientsDefault` | `AlertConfigTable.recipientsCol` | settings | DPA | âœ… | |
| dpa_override_recipients_json | `dpaOverrideRecipients` | `AlertConfigTable.recipientsCol.editable` | settings | DPA edit | âœ… | |
| escalation_cadence_json | `escalationCadence` | `AlertConfigTable.escalationDrawer` | settings | DPA | âœ… | |
| ocr_threshold_office | `ocrThresholdOffice` | `SettingsScreen.ocrTab.officeThresholdSlider` | `/certs/settings` (OCR Thresholds tab) | DPA edit | âœ… | (D-CERT-106) |
| ocr_threshold_vessel | `ocrThresholdVessel` | `SettingsScreen.ocrTab.vesselThresholdSlider` | settings | DPA edit | âœ… | (D-CERT-168) |
| ocr_threshold_manual_floor | `ocrThresholdManualFloor` | `SettingsScreen.ocrTab.manualFloorSlider` | settings | DPA edit | âœ… | |
| class_snapshot_cadence_months | `classSnapshotCadenceMonths` | `SettingsScreen.snapshotTab.cadenceInput` | settings | DPA edit | âœ… | |
| class_snapshot_lead_months | `classSnapshotLeadMonths` | `SettingsScreen.snapshotTab.leadInput` | settings | DPA edit | âœ… | |
| event_snapshot_grace_days | `eventSnapshotGraceDays` | `SettingsScreen.snapshotTab.graceInput` | settings | DPA edit | âœ… | |
| draft_expire_days | `draftExpireDays` | `SettingsScreen.draftTab.expireDaysInput` | settings | DPA edit | âœ… | |
| created_at, updated_at, updated_by | `createdAt`, `updatedAt`, `updatedBy` | `SettingsScreen.auditChip` | settings | DPA | âœ… | |

---

## 11. `vims_certs_approval_event`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| event_id | `id` | `TrackedItemDetail.workflowPanel.timelineRow` | `/certs/vessels/<imo>/cert/<id>` | Per RBAC | âœ… | |
| tracked_item_id | (URL context) | â€” | â€” | â€” | ðŸ”§ | |
| from_state, to_state | `fromState`, `toState` | `TrackedItemDetail.workflowPanel.timelineRow.transitionBadge` | same | Per RBAC | âœ… | |
| actor_user_id, actor_role | `actorUserId`, `actorDisplayName`, `actorRole` | `TrackedItemDetail.workflowPanel.timelineRow.actorChip` | same | Per RBAC | âœ… | `actorDisplayName` joins office/crew identity; UI suppresses raw UUID fallback |
| reason | `reason` | `TrackedItemDetail.workflowPanel.timelineRow.reasonExpand` | same | Per RBAC; ðŸ”’ redacted in external auditor view | ðŸ”’ | |
| timestamp_utc | `timestampUtc` | `TrackedItemDetail.workflowPanel.timelineRow.timestamp` | same | Per RBAC | âœ… | |

---

## 12. `vims_certs_notification_meta`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| notification_id | `id` | `NotificationInbox.row`, `TrackedItemDetail.notificationsDrawer` | `/notifications`, `/certs/vessels/<imo>/cert/<id>` | Self / Per RBAC | âœ… | |
| master_notification_id | `masterNotificationId` | (joined for body content) | `/notifications` | Self | âœ… | Cross-table join |
| trigger_event | `triggerEvent` | `NotificationInbox.row.eventChip`, `TrackedItemDetail.notificationsDrawer` | several | Self | âœ… | |
| cert_row_id | `certRowId` | `NotificationInbox.row.deepLink` | `/notifications` | Self | âœ… | Click â†’ cert detail |
| vessel_id | `vesselId` | `NotificationInbox.row.vesselChip` | `/notifications` | Self | âœ… | |
| recipients_json | `recipients` | `TrackedItemDetail.notificationsDrawer.recipientsCol`, `AuditLogTable.expandedDiff` | several | Per RBAC | âœ… | |
| channels_json | `channels` | same | same | Per RBAC | âœ… | Per-side routing visible |
| sent_at | `sentAt` | `NotificationInbox.row.sentAt`, `TrackedItemDetail.notificationsDrawer` | several | Self / Per RBAC | âœ… | |
| delivery_status_json | `deliveryStatus` | `TrackedItemDetail.notificationsDrawer.deliveryCol`, DPA dashboard bouncing-email card | several | Per RBAC | âœ… | |
| ack_user_id | `ackUserId` | `TrackedItemDetail.notificationsDrawer.ackChip`, `CertCard.vesselAckedBadge` (office side per D-CERT-087) | several | Per RBAC | âœ… | |
| ack_at | `ackAt` | same | same | Per RBAC | âœ… | |
| ack_channel | `ackChannel` | `TrackedItemDetail.notificationsDrawer.ackChip` | several | Per RBAC | âœ… | |
| escalation_level | `escalationLevel` | `TrackedItemDetail.notificationsDrawer.escalationBadge`, `ApprovalQueueTable.escalationCol` | several | Per RBAC | âœ… | |
| body_content | `body` | `NotificationInbox.row.bodyExpand`, email rendering (server-side) | `/notifications` (within 1y); email client | Self | âœ… | Purged at 1y per D-CERT-175 |
| body_purged_at | `bodyPurgedAt` | `NotificationInbox.row.purgedBadge` (when set) | `/notifications` | Self | âœ… | |
| idempotency_key | (not displayed) | â€” | â€” | â€” | ðŸ”§ | DB UQ enforces D-CERT-174 |

---

## 13. `vims_certs_print_artifact`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| print_id | `id` | `PrintHistoryTable.row`, `PrintArtifactPdfTemplate.footer`, share/email subject | `/certs/print/history`, print PDF, email | Per RBAC | âœ… | (D-CERT-128) single-vessel format `SQE-S633-<imo>-<yyyymmdd>-<seq>`; fleet/multi-vessel format `SQE-S633-FLEET-<yyyymmdd>-<seq>` (B-PRT-01 resolved 2026-06-29) |
| scope | `scope` | `PrintHistoryTable.col`, `PrintBuilder.scopeChip` | several | Per RBAC | âœ… | |
| vessels_json | `vessels` | `PrintHistoryTable.col`, `PrintBuilder.vesselPickerState` | several | Per RBAC | âœ… | |
| sections_json | `sections` | `PrintHistoryTable.col` | `/certs/print/history` | Per RBAC | âœ… | |
| filters_json | `filters` | `PrintHistoryTable.row.filterDrawer` | `/certs/print/history` | Per RBAC | âœ… | |
| custom_cert_ids_json | `customCertIds` | `PrintHistoryTable.row.detailsDrawer` | `/certs/print/history` | Per RBAC | âœ… | |
| user_id, user_role | `userId`, `userRole` | `PrintHistoryTable.col`, `PrintArtifactPdfTemplate.footer` | several | Per RBAC; FM dashboard for high-volume surfacing | âœ… | (D-CERT-128, D-CERT-143) |
| timestamp_utc | `timestampUtc` | `PrintHistoryTable.col`, `PrintArtifactPdfTemplate.footer` | several | Per RBAC | âœ… | |
| system_state_hash | `systemStateHash` | `PrintArtifactPdfTemplate.footer` (printed on every page) | print PDF | Visible on artifact | âœ… | (D-CERT-128) |
| watermark_applied | `watermarkApplied` | `PrintHistoryTable.watermarkBadge`, `PrintArtifactPdfTemplate.watermarkOverlay` | several | Per RBAC | âœ… | |
| watermark_recipient | `watermarkRecipient` | `PrintArtifactPdfTemplate.watermarkOverlay` | print PDF | On artifact | âœ… | |
| pdf_blob_id | `pdfBlobId` â†’ signed download URL | `PrintHistoryTable.downloadPdfButton` | `/certs/print/history`, print result page | Per RBAC | âœ… | |
| excel_blob_id | `excelBlobId` â†’ signed download URL | `PrintHistoryTable.downloadExcelButton` | several | Per RBAC | âœ… | |
| bundle_zip_blob_id | `bundleZipBlobId` â†’ signed URL | `PrintHistoryTable.downloadBundleButton` (when scope=share_bundle) | `/certs/print/history`, share-bundle result | Master / DPA / FM | âœ… | |
| recipient_email | `recipientEmail` | `PrintHistoryTable.recipientCol` | `/certs/print/history` | Per RBAC | âœ… | |
| page_count | `pageCount` | `PrintHistoryTable.col` | `/certs/print/history` | Per RBAC | âœ… | |
| generation_status | `generationStatus` | `PrintHistoryTable.statusBadge` | `/certs/print/history` | Per RBAC | âœ… | |
| failure_message | `failureMessage` | `PrintHistoryTable.errorBanner` (when status=failed) | `/certs/print/history` | Per RBAC | âœ… | (D-CERT-150) |

---

## 14. `vims_certs_external_auditor_access`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| grant_id | `id` | `AuditorAccessTable.row`, `AuditorAccessDetailScreen` | `/certs/auditor-access`, `/certs/auditor-access/<grant_id>` | Marine Sup'tt + DPA | âœ… | |
| auditor_name | `auditorName` | `AuditorAccessTable.col`, `AuditorPortalLanding.welcomeHeader` | several + auditor portal | Marine Sup'tt + DPA + auditor (own) | âœ… | |
| auditor_email | `auditorEmail` | `AuditorAccessTable.col`, signup email recipient | `/certs/auditor-access` | Marine Sup'tt + DPA | âœ… | |
| scope_json | `scope` | `AuditorAccessTable.scopeChips`, `AuditorAccessDetailScreen.scopeEditor`, `AuditorPortalLanding.scopeSummary` | several + auditor portal | Marine Sup'tt + DPA + auditor (own) | âœ… | |
| expiry_at | `expiryAt` | `AuditorAccessTable.expiryCountdown`, `AuditorPortalLanding.expiryBanner`, watermark recipient | several | Marine Sup'tt + DPA + auditor (own) | âœ… | (D-CERT-195 â€” only edit path for effective revoke) |
| granted_by | `grantedBy` | `AuditorAccessTable.col`, `AuditorAccessDetailScreen` | `/certs/auditor-access` | Marine Sup'tt + DPA | âœ… | |
| granted_at | `grantedAt` | same | same | Marine Sup'tt + DPA | âœ… | |
| signup_token_hash | (never displayed) | â€” | â€” | â€” | ðŸ”§ | Server-only; raw token sent in signup email then discarded |
| signup_token_used_at | `signupTokenUsedAt` | `AuditorAccessTable.signupBadge` | `/certs/auditor-access` | Marine Sup'tt + DPA | âœ… | |
| token_secret_hash | (never displayed) | â€” | â€” | â€” | ðŸ”§ | Auditor session token hash |
| last_accessed_at | `lastAccessedAt` | `AuditorAccessTable.col` | `/certs/auditor-access` | Marine Sup'tt + DPA | âœ… | Single timestamp only, NOT per-action (D-CERT-196) |
| revoked_via_expiry_edit | `revokedViaExpiryEdit` | `AuditorAccessTable.statusBadge` | `/certs/auditor-access` | Marine Sup'tt + DPA | âœ… | |

---

## 15. `vims_certs_batch_ingest`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| batch_id | `id` | `OnboardingWizard.step3.batchListRow`, `GapFillScreen` | `/certs/onboarding/<imo>`, `/certs/onboarding/<imo>/batch/<batch_id>/gap-fill` | DPA | âœ… | |
| vessel_id | (URL context) | â€” | â€” | â€” | ðŸ”§ | |
| onboarding_session_id | `onboardingSessionId` | `OnboardingHubTable.col` | `/certs/onboarding` | DPA + FM | âœ… | Groups batches |
| pdf_blob_ids_json | `pdfBlobIds` | `GapFillScreen.pdfCarousel` | gap-fill | DPA | âœ… | |
| pdf_count | `pdfCount` | `OnboardingWizard.step3.batchListRow.countCol` | `/certs/onboarding/<imo>` | DPA | âœ… | |
| status | `status` | `OnboardingWizard.step3.batchListRow.statusBadge`, `GapFillScreen.statusBanner` | several | DPA | âœ… | |
| created_at, created_by | `createdAt`, `createdBy` | `OnboardingWizard.step3.batchListRow` | `/certs/onboarding/<imo>` | DPA | âœ… | |
| ocr_completed_at | `ocrCompletedAt` | same | same | DPA | âœ… | |
| review_started_at | `reviewStartedAt` | same | same | DPA | âœ… | |
| committed_at, committed_by | `committedAt`, `committedBy` | `OnboardingWizard.step3.batchListRow.committedChip`, `BatchIngestReportScreen` | several | DPA | âœ… | |
| cancelled_at, cancelled_by | `cancelledAt`, `cancelledBy` | `OnboardingWizard.step3.batchListRow.cancelledChip` | `/certs/onboarding/<imo>` | DPA | âœ… | |
| validation_blocks_json | `validationBlocks` | `GapFillScreen.commitDialog.blocksList` | gap-fill commit | DPA | âœ… | (D-CERT-116) |
| validation_warns_json | `validationWarns` | `GapFillScreen.commitDialog.warnsList` | gap-fill commit | DPA | âœ… | (D-CERT-116) |
| report_csv_blob_id | `reportCsvBlobId` â†’ signed URL | `OnboardingWizard.step3.batchListRow.downloadReportButton` | `/certs/onboarding/<imo>` | DPA | âœ… | (D-CERT-117) |

---

## 16. `vims_certs_vessel_config`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| vessel_id | (URL context) | â€” | â€” | â€” | ðŸ”§ | |
| anniversary_date | `anniversaryDate` | `VesselProfileScreen.anniversaryField`, `OnboardingWizard.step2`, `TrackedItemDetail` | several | DPA edit (rare) | âœ… | (D-CERT-074) |
| ship_type | `shipType` | `VesselProfileScreen`, `OnboardingWizard.step2` | several | DPA + FM edit | âœ… | |
| marine_supt_user_id | `marineSuptUserId` | `VesselProfileScreen.personnelPicker`, `CertVesselDashboard.header` | several | DPA + FM edit | âœ… | (D-CERT-098) |
| technical_manager_user_id | `technicalManagerUserId` | same | same | DPA + FM edit | âœ… | (D-CERT-098) |
| slack_channel_vessel | `slackChannelVessel` | `VesselProfileScreen.slackRoutingField`, `SettingsScreen.slackTab` | `/certs/vessels/<imo>/profile`, `/certs/settings` | DPA edit | âœ… | (D-CERT-160) |
| slack_channel_office_default | `slackChannelOfficeDefault` | same | same | DPA edit | âœ… | |
| lifecycle_status | `lifecycleStatus` | `CertVesselDashboard.banner`, `VesselProfileScreen.statusBadge`, `OnboardingHubTable.col` | several | Per RBAC | âœ… | |
| pending_disposal_started_at | `pendingDisposalStartedAt` | `CertVesselDashboard.disposalCountdownBanner`, `VesselProfileScreen.statusBadge` | several | Per RBAC | âœ… | (D-CERT-044) |
| sale_handover_bundle_blob_id | `saleHandoverBundleBlobId` â†’ signed URL | `VesselProfileScreen.handoverBundleDownloadButton` | `/certs/vessels/<imo>/profile` | DPA + FM | âœ… | (D-CERT-093) |
| flag_change_pending | `flagChangePending` | `CertVesselDashboard.banner.pendingReupload`, `VesselProfileScreen.flagSection` | several | Per RBAC | âœ… | (D-CERT-094) |
| flag_change_event_json | `flagChangeEvent` | `VesselProfileScreen.flagSection.eventLog` | `/certs/vessels/<imo>/profile` | DPA + FM | âœ… | |
| class_change_pending | `classChangePending` | `VesselProfileScreen.classChangeBanner`, `TrackedItemDetail.statusBadge` (pending_supersession rows) | several | DPA + FM | âœ… | (D-CERT-046) |
| mandatory_coverage_override_reason | `mandatoryCoverageOverrideReason` | `CertVesselDashboard.coverageBanner`, `VesselProfileScreen.coverageSection` | several | Per RBAC | âœ… | (D-CERT-119) |
| mandatory_coverage_override_at | `mandatoryCoverageOverrideAt` | same | same | Per RBAC | âœ… | |
| mandatory_coverage_override_by | `mandatoryCoverageOverrideBy` | same | same | Per RBAC | âœ… | |
| iws_age_gate_disabled | `iwsAgeGateDisabled` | `CertVesselDashboard.iwsDisabledBadge`, `VesselProfileScreen.iwsAgeGateRow.status` | `/certs/vessels/<imo>`, `/certs/vessels/<imo>/profile` | All Cert read | ✅ | FEAT-CERT-CAT-012 / D-CERT-034; computed by onboarding + nightly recompute |
| iws_age_gate_disabled_at | `iwsAgeGateDisabledAt` | `VesselProfileScreen.iwsAgeGateRow.disabledAt` | `/certs/vessels/<imo>/profile` | DPA + FM read | ✅ | First timestamp the cron disabled IWS for this vessel |
| iws_age_gate_disabled_reason | `iwsAgeGateDisabledReason` | `VesselProfileScreen.iwsAgeGateRow.reason` | `/certs/vessels/<imo>/profile` | DPA + FM read | ✅ | System reason, e.g. `vessel_age_exceeds_gate` |
| iws_age_gate_last_age_years | `iwsAgeGateLastAgeYears` | `VesselProfileScreen.iwsAgeGateRow.age` | `/certs/vessels/<imo>/profile` | DPA + FM read | ✅ | Computed from `VesselData.YearBuilt`; `VesselData.Age` fallback only when `YearBuilt` is missing |
| iws_age_gate_last_evaluated_at | `iwsAgeGateLastEvaluatedAt` | `VesselProfileScreen.iwsAgeGateRow.lastChecked` | `/certs/vessels/<imo>/profile` | DPA + FM read | ✅ | Written by onboarding + nightly recompute job |
| iws_manual_override_enabled | `iwsManualOverrideEnabled` | `VesselProfileScreen.iwsOverrideToggle` | `/certs/vessels/<imo>/profile` | DPA write; FM read | ✅ | DPA override for older IWS-enrolled vessels |
| iws_manual_override_reason | `iwsManualOverrideReason` | `VesselProfileScreen.iwsOverrideReason` | `/certs/vessels/<imo>/profile` | DPA write; FM read | ✅ | Required when override is enabled |
| iws_manual_override_by | `iwsManualOverrideBy` | `VesselProfileScreen.iwsOverrideAuditChip`, `AuditLogTable` | `/certs/vessels/<imo>/profile`, `/certs/audit-log` | DPA + FM read | ✅ | Auth user id string per brownfield auth model |
| iws_manual_override_at | `iwsManualOverrideAt` | `VesselProfileScreen.iwsOverrideAuditChip` | `/certs/vessels/<imo>/profile` | DPA + FM read | ✅ | Timestamp of latest DPA override edit |
| created_at, updated_at, updated_by | `createdAt`, `updatedAt`, `updatedBy` | `VesselProfileScreen.auditChip`, `AuditLogTable` | several | DPA + FM | âœ… | |

---

## 17. `vims_certs_modification_event`

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| modification_event_id | `id` | `AuditLogTable.row.eventGroupChip`, `TrackedItemDetail.modEventLink` | `/certs/audit-log`, cert detail | DPA + FM | âœ… | (D-CERT-047) |
| group_started_at, group_window_ends_at | `groupStartedAt`, `groupWindowEndsAt` | `AuditLogTable.row.eventGroupChip.tooltip` | `/certs/audit-log` | DPA + FM | âœ… | |
| description | `description` | `AuditLogTable.row.eventGroupChip.expanded` | `/certs/audit-log` | DPA + FM | âœ… | |
| affected_tracked_item_ids_json | `affectedTrackedItemIds` | `AuditLogTable.row.eventGroupChip.affectedList` | `/certs/audit-log` | DPA + FM | âœ… | |
| created_by | `createdBy` | same | same | DPA + FM | âœ… | |

---

## 18. `vims_certs_settings`

**Structured single-row config table** (âœ… B-FM-05 resolved 2026-06-12 â€” not key-value; mirrors `vims_certs_alert_config` Â§10 pattern, D-AUDRS-271 PK standard). All fields surface on `/certs/settings` (DPA-only), **plus `last_heartbeat_at` (DATETIME2, ðŸ”§ internal)** â€” written hourly by the cadence cron, read by the dead-man check + `/api/certs/health/` + DPA dashboard tile (OBS-CERT-11/12).

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|--------|---------|-----------|--------------|-----------------|--------|-------|
| settings_id | `id` | â€” | â€” | â€” | ðŸ”§ | Internal PK; DB default `NEWSEQUENTIALID()` per B-FM-01 / D-AUDRS-271 |
| singleton_key | â€” | â€” | â€” | â€” | ðŸ”§ | Enforces the single-row shape with `singleton_key='certs'`; not serialized |
| last_heartbeat_at | `lastCadenceHeartbeat` | `HealthEndpoint`, `DpaDashboardHeartbeatTile` | `/api/certs/health/`, `/certs/dashboard` | Public health endpoint / DPA dashboard | ðŸ”§ | OBS-CERT-11/12 heartbeat source; exposed by health endpoint without PII |
| created_at | `createdAt` | `SettingsScreen.auditChip` | `/certs/settings` | DPA | âœ… | Settings row creation timestamp |
| updated_at | `updatedAt` | `SettingsScreen.auditChip` | `/certs/settings` | DPA | âœ… | Settings row update timestamp |
| updated_by | `updatedBy` | `SettingsScreen.auditChip` | `/certs/settings` | DPA | âœ… | Existing auth user id string in the actual monorepo (`AuthenticatedUser.user_id`) |

---

## 19. Shared `master_*` Consumption

These fields are owned by other modules / platform but rendered in Certs UI.

| Source | Fields used by Certs | Component | Screen route | Status |
|--------|---------------------|-----------|--------------|--------|
| `master_vessel` | vessel_id, vessel_name, imo_number, flag_state, class_society, ship_type, master_user_id, build_year, lifecycle_status (also written-to via vessel_config) | `CertVesselDashboard.header`, `VesselProfileScreen`, `FleetDashboard.tile`, `OnboardingWizard.step1` | several | âœ… |
| `master_user` | id, full_name, email, role | joined into all actor / approver / submitter / reviewer chips | every screen surfacing actors | âœ… |
| `master_role` | role_id, role_name | RBAC enforcement (no direct UI) | server-only | ðŸ”§ |
| `master_RoleByVessel` | user_id Ã— vessel_id mapping | RBAC scope filter on every list endpoint | server-only | ðŸ”§ |
| `master_notification` | id, body, created_at, ack_at, etc. | `NotificationInbox` (joined with `vims_certs_notification_meta`) | `/notifications` | âœ… |
| `wrh_ship_time_config` | vessel_id, timezone | `ReauthModal` (D-CERT-082); date display tooltips | several | âœ… |
| `msc_profiles` | form_ids, process_ids | RBAC enforcement | server-only | ðŸ”§ |
| Company logo endpoint `GET /api/auth/company-logo/` | binary image | `PrintArtifactPdfTemplate.headerLogo`, `EmailTemplates.logoHeader` | print PDF, emails | âœ… |
| `Mapping_CrewAssReviewers` + `has_global_vessel_access` | user â†’ vessel | DPA full-fleet override (D-CERT-090) | server-only | ðŸ”§ |

---

## 20. External Auditor Surface â€” Redaction Map

Per **D-CERT-180** (FEAT-CERT-AUDIT-007), **D-CERT-196** (no activity tracking), **D-CERT-178** (per-module only): the auditor portal renders a strict subset.

| Table | Field | External Auditor sees | Redaction reason |
|-------|-------|----------------------|------------------|
| All free-text reason fields | `rejection_reason`, `extension_reason`, `mandatory_coverage_override_reason`, `flag_change_event_json.reason`, `vims_certs_audit_log.reason`, `vims_certs_approval_event.reason` | `[REDACTED â€” internal note]` | Internal context not for external party |
| `vims_certs_audit_log` | (entire screen) | NOT accessible | D-CERT-178 â€” per-module only; no audit log endpoint |
| `vims_certs_external_auditor_access` | (entire table) | NOT accessible | Auditor doesn't see other auditor grants |
| `vims_certs_settings`, `vims_certs_alert_config` | (entire) | NOT accessible | Configuration is internal |
| `vims_certs_notification_meta` | (entire) | NOT accessible | Notification routing is internal |
| `vims_certs_modification_event` | (entire) | NOT accessible | Internal grouping concept |
| `vims_certs_vessel_config.slack_channel_*`, `mandatory_coverage_override_*` | NOT visible | Internal config + override reason | |
| `vims_certs_pdf_blob.dpa_retention_override_until` | NOT visible | Internal retention policy | |
| `vims_certs_print_artifact` | only artifacts auto-generated by auditor's own print actions | Audit COPY watermarked outputs only | |
| `vims_certs_tracked_item.rejection_reason`, `rejection_count` | NOT visible | Internal | |
| `vims_certs_tracked_item.draft_expires_at` | NOT visible | Drafts not in scope | |
| `vims_certs_class_status_snapshot.parsed_payload_json` | only the structured cert info, not parser internals | Filtered serializer | |
| `vims_certs_reconciliation_*` | NOT visible (Phase 0 default) | Reconciliation is operational tooling, not auditor evidence | |

**Implementation:** `serializers/auditor.py` provides redacted versions of all serializers consumed by `/api/auditor/<token>/...` endpoints. Server-side enforcement, not client-side hiding.

---

## 21. Audit Pass Checklist

Run through this every time COVERAGE.md is regenerated:

- [ ] Every column in Â§3 of `BACKEND_STRUCTURE.md` appears as a row here.
- [ ] Every API key returned by an endpoint in Â§5 of `BACKEND_STRUCTURE.md` is named here.
- [ ] Every "Surfaces" line in `APP_FLOW.md` references a column or computed field that has a row here.
- [ ] Every âš ï¸ row has a tracked Phase 0/1 issue.
- [ ] Every ðŸ”§ row's "Notes" justifies why the field never reaches UI.
- [ ] Every ðŸ”’ row's "Notes" names the redaction rule + the role boundary.
- [ ] No ðŸ”’ row leaks the redacted value to the wrong audience (cross-checked against Â§20 redaction map).
- [ ] All `master_*` consumed fields are documented in Â§19.
- [ ] No `apps/<sibling>` import or `/api/<sibling>/*` HTTP call appears in `apps/certs/` (cross-module non-integration per D-CERT-176).
- [ ] Every cross-cutting column on a new table matches the Â§23 table (no ad-hoc audit columns per migration).
- [ ] Every new table has a Â§24 Delete Policy row (soft vs hard declared, not inferred).

When all 11 checks pass, FIELD_MAP is GREEN and the COVERAGE audit can include "FIELD_MAP completeness" as the 5th audit gate.

---

*End of FIELD_MAP v1.0. This is the audit lens that prevents the failure mode "backend done, UI missing" â€” every Phase 0+ PR that adds a column adds a row here, or the merge is blocked.*

---

## Appendix â€” Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `FIELD_MAP.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` âœ“ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` Â§16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-006 | Class snapshot upload cadence: every 3 months, alert 1 month in advance. | LOCKED |
| D-CERT-007 | Event-driven class snapshot refresh prompt when any `is_class_tracked: true` row is updated. | LOCKED |
| D-CERT-011 | Rich date fields: issue/expiry/anniversary/window_open/window_close/last_done/next_due/postponed_until. | LOCKED |
| D-CERT-013 | Extensions: separate row, `relationship_type âˆˆ {extension_of, dispensation_for}`, `extension_authority âˆˆ {class, flag}`. | LOCKED |
| D-CERT-017 | Canonical catalog sections (9): Class Â· Statutory & Flag Â· Trade & Commercial Â· Equipment LSA/FFA/Nav/GMDSS Â· Calibrations Â· Te... | LOCKED |
| D-CERT-027 | Tonnage Tax = TrackedItem (Trade & Commercial section). | LOCKED |
| D-CERT-028 | Catalog row has `vessel_type: bulk_carrier \\| tanker \\| container \\| all` (multi-select). | LOCKED |
| D-CERT-029 | Catalog row has `applicability_mode: all_matching_type \\| specific_vessel_ids` dropdown. | LOCKED |
| D-CERT-034 | `CLASS-PROP-SHAFT-SURVEY`, `CLASS-DOCKING-SURVEY` = Cert children of COC. | LOCKED |
| D-CERT-035 | Multi-instance equipment groups (SCBA / CO2 / ELSA-EEBD / Liferaft / Lifeboat pyrotechnics / Multigas detectors): ONE catalog p... | LOCKED |
| D-CERT-039 | CSR Form 1/2/3: ONE TrackedItem (`STAT-CSR`, cadence `permanent`); | LOCKED |
| D-CERT-042 | Type Approvals: `permanent` cadence + optional `linked_pms_component_id` FK. | LOCKED |
| D-CERT-052 | Parser version stored on each snapshot. | LOCKED |
| D-CERT-062 | `parsed_payload.schema_version` on every snapshot. | LOCKED |
| D-CERT-069 | Snapshot list filters: vessel Â· class_society Â· date_range Â· parse_status Â· has_unresolved_mismatches. | LOCKED |
| D-CERT-072 | Parser ops page (dev-only, feature-flagged) â€” 90-day aggregate stats. | LOCKED |
| D-CERT-091 | Audit log retention = 3 years rolling (AMENDED by D-CERT-099 to 5y). Append-only at DB layer; no UPDATE/DELETE GRANT. | AMENDED |
| D-CERT-096 | External read-only access + Master share-bundle (two distinct features): (a) External read-only login for charterers / vetting ... | LOCKED |
| D-CERT-101 | OCR-based PDF auto-matching to cert rows. | LOCKED |
| D-CERT-104 | Vessel-data migration = iterative batch PDF ingest (no filled-Excel source): DPA uploads actual certificate PDFs in batches of ... | LOCKED |
| D-CERT-109 | Catalog metadata fields per row. | LOCKED |
| D-CERT-115 | Dry-run = preview before commit. | LOCKED |
| D-CERT-145 | Third-party deliverable = ZIP bundle (manifest PDF + cert PDFs). | LOCKED |
| D-CERT-151 | Notification infra = reuse VIMS shared infra + Slack channel added to V1. | LOCKED |
| D-CERT-155 | Email-to-action = magic-link one-click ack; signed short-lived URL marks cert ack without full app login. | LOCKED |
| D-CERT-159 | Failed-delivery / bounce handling = retry 3x exponential backoff + DPA dashboard surface. | LOCKED |
| D-CERT-182 | Audit log cascade on catalog row hard-purge = SIMPLE cascade hard-purge. | LOCKED |
| D-CERT-183 | Audit log storage tiering = hot 2 years + cold 3 years. | LOCKED |
| D-CERT-194 | External auditor access provisioning = Marine Sup'tt self-service (AMENDS D-CERT-096). | LOCKED |


---

## 22. `vims_certs_cert_change_log` + `tracked_item.version` (D-AUDRS-237/239 amendment, 2026-06-12)

> Renumbered from a duplicate "Â§19" on 2026-06-12 (v1.1) â€” Â§19 is Shared `master_*` Consumption.

> Added by cross-module obligation from the Audit module (raised AFTER this docsuite froze; amendment authorized by Prince/DPA 2026-06-12). Build lands these with the Â§3 schema phase.

| Column | API key | Component | Screen route | Role visibility | Status | Notes |
|---|---|---|---|---|---|---|
| vims_certs_tracked_item.version | version | â€” | â€” | â€” | ðŸ”§ Internal | Cross-module CAS counter; serialized to API for writers (Audit) only; never rendered |
| cert_change_log.change_id | â€” | â€” | â€” | â€” | ðŸ”§ Internal | PK |
| cert_change_log.field_name / old_value / new_value | changes[] | CertChangeHistoryDrawer (Phase 0/1 decides placement) | tracked-item detail | DPA, FM | âš  Missing UI (build-time flag) | per-field history incl. WHICH module wrote it |
| cert_change_log.source_module / source_ref | source_module, source_ref | CertChangeHistoryDrawer | tracked-item detail | DPA, FM | âš  Missing UI (build-time flag) | "changed by AUDIT writeback (audit â€¦)" attribution line |
| cert_change_log.changed_by / changed_at | changed_by, changedByDisplay, changed_at | CertChangeHistoryDrawer | tracked-item detail | DPA, FM | âš  Missing UI (build-time flag) | `changedByDisplay` joins office/crew identity; UI suppresses raw UUID fallback |

---

## 23. Cross-Cutting Columns

> Added 2026-06-12 (v1.1) â€” KLOSS Step 2 realignment; sources: BACKEND_STRUCTURE Â§2, Â§3.1â€“3.19, Â§11, Â§12; D-CERT-021/076/088/099/118/174/179/183, D-AUDRS-236/239. BLOCKED cells tracked as `BLOCKERS.md` B-FM-01 (PK generation), B-FM-02 (audit-column write path), B-FM-03 (retention-job role).

| Column | Type | Applies to tables | Default | Written by (app / DB trigger / DB default) |
|--------|------|-------------------|---------|--------------------------------------------|
| `<entity>_id` PK | UNIQUEIDENTIFIER | catalog_row, class_code_mapping, tracked_item, pdf_blob, class_status_snapshot, reconciliation_run, reconciliation_flag, audit_log, alert_config, approval_event, notification_meta, external_auditor_access, batch_ingest, modification_event, cert_change_log. **Exceptions:** catalog_section = INT identity (1..9 seed, D-CERT-017); print_artifact = NVARCHAR(64) human-readable `SQE-S633-<imo>-<yyyymmdd>-<seq>` for single-vessel artifacts and `SQE-S633-FLEET-<yyyymmdd>-<seq>` for fleet/multi-vessel artifacts (D-CERT-128; B-PRT-01 resolved 2026-06-29); vessel_config PK = vessel_id FK â†’ master_vessel; settings = structured single-row table (B-FM-05 resolved) | `NEWSEQUENTIALID()` | âœ… RESOLVED (B-FM-01, 2026-06-12): **DB default `NEWSEQUENTIALID()`** per cross-module law **D-AUDRS-271** â€” confirmed binding for all new Certs tables. Migrations declare it as the column default; app never generates PKs. |
| `created_at` | DATETIME2 | catalog_section (seed-only), catalog_row, class_code_mapping, tracked_item, alert_config, batch_ingest, vessel_config. NOT on: pdf_blob / class_status_snapshot (use `uploaded_at`), audit_log / approval_event / print_artifact (use `timestamp_utc`), notification_meta (`sent_at`), external_auditor_access (`granted_at`), reconciliation_run (`ran_at`), modification_event (`group_started_at`), cert_change_log (`changed_at`) | â€” | âœ… RESOLVED (B-FM-02, 2026-06-12): **Django ORM `auto_now_add=True`** (app-side, platform convention; deployed Safety is plain Django). catalog_section remains migration-seeded. |
| `created_by` | UNIQUEIDENTIFIER FK â†’ master_user | catalog_section, catalog_row, class_code_mapping, tracked_item, batch_ingest (NN), modification_event (NN). NOT on alert_config / vessel_config | â€” | âœ… RESOLVED (B-FM-02): app-supplied from `request.user` at the serializer/service layer â€” the write rule, now stated. |
| `updated_at` | DATETIME2 | catalog_row, class_code_mapping, tracked_item, alert_config, vessel_config. Explicitly absent on catalog_section (seed-only) and all append-only/event tables | â€” | âœ… RESOLVED (B-FM-02): **Django ORM `auto_now=True`** â€” no DB triggers anywhere in the module. |
| `updated_by` | UNIQUEIDENTIFIER FK â†’ master_user | catalog_row, class_code_mapping, tracked_item, alert_config, vessel_config | â€” | âœ… RESOLVED (B-FM-02): app-supplied from `request.user`. |
| `row_version` | ROWVERSION | tracked_item ONLY | engine-stamped | DB engine â€” optimistic in-process concurrency (D-CERT-088); sent in PATCH body, never displayed (Â§4) |
| `version` (CAS counter) | INT | tracked_item ONLY (added 2026-06-12) | 1 | App â€” increments on EVERY write; external writers (Audit writeback) compare-and-swap on it (D-AUDRS-236/239). Distinct from `row_version`. `cert_change_log.version_after` records the post-write value |
| `version` (mapping revision) | INT | class_code_mapping ONLY | 1 | App â€” increments per edit (D-CERT-061); stamped onto reconciliation_run as `mapping_version_used`. **Different semantics** from the CAS counter â€” do not conflate |
| `idempotency_key` | NVARCHAR(128) NN UQ | notification_meta ONLY | â€” | App â€” dispatcher computes `(cert_row_id, cadence, sent_date)`; DB UQ is the belt-and-suspenders enforcement (D-CERT-174) |
| `is_active` / `active` | BIT | catalog_row (`is_active`, deprecation), pdf_blob (`is_active`, supersession), class_code_mapping (`active`) | 1 | App â€” deprecate endpoint / blob supersession / mapping editor toggle |
| `lifecycle_status` | NVARCHAR(24) enum | tracked_item (`active \| pending_disposal \| pending_supersession \| invalid_due_to_reflag \| onboarding_quarantine`), vessel_config (`active \| onboarding_in_progress \| pending_disposal \| sold_pending_handover`) | `'active'` | App â€” lifecycle event endpoints (Â§5.9) |
| `retention_tier` | NVARCHAR(8) | audit_log ONLY | `'hot'` | App â€” `AuditLog.record()` sets 'hot'; flipped 'cold' at 2y by nightly archiver (D-CERT-183). âœ… RESOLVED (B-FM-03, 2026-06-12): executed by new third DB role **`vims_jobs`** â€” UPDATE scoped to retention columns + the 5y-purge DELETE on audit/event tables ONLY; used solely by the scheduled retention tasks (Celery). Provisioned at plan step 0.3 alongside `vims_app`/`vims_admin`. App path stays append-only (D-CERT-179 / SEC-CERT-16). |
| `schema_version` | SMALLINT | pdf_blob, audit_log, class_status_snapshot (`parsed_payload_schema_version`) | 1 | App â€” locked by write helper (audit_log Â§12); payload versioning per D-CERT-062 |

---

## 24. Delete Policy per Table

> Added 2026-06-12 (v1.1); **B-FM-03/04/05 RESOLVED 2026-06-12 (v1.2, Prince/DPA closure session).** Sources: BACKEND_STRUCTURE Â§2, Â§3, Â§5.1, Â§6, Â§11, Â§14; D-CERT-020/021/039/044/051/058/060/076/093/099/175/179/182/183/195/196.
>
> **Blanket retention rule (B-FM-04 resolution / SEC-CERT-17):** every event/evidence table with no stronger LOCKED decision follows the **audit-log 5-year rolling regime (D-CERT-099)** â€” purged by the same nightly batch, executed under the **`vims_jobs`** role (B-FM-03). LOCKED exceptions stand: snapshot metadata indefinite-hot (D-CERT-060), snapshot blobs indefinite (D-CERT-020), notification body 1y (D-CERT-175), vessel decommission 30-day delete (D-CERT-044) + redacted audit slice (D-CERT-093). Live-config tables (alert_config, vessel_config, settings, active mappings) are current state, not history â€” never purged while active.

| Table | Soft-delete mechanism | Hard-delete policy | Cascade / notes |
|-------|----------------------|--------------------|-----------------|
| catalog_section | None â€” 9 fixed seed rows (D-CERT-017); no DELETE endpoint | None â€” no API path exists | Seed-only table |
| catalog_row | `is_active=false` via deprecate (CERT_P_008) and bulk-soft-delete (cap 50 + reason, CERT_P_009, D-CERT-092) | `DELETE /api/certs/catalog/rows/<id>/` hard purge (DPA) | ON DELETE CASCADE â†’ that row's audit_log entries (D-CERT-182). NOT cascaded to tracked_item â€” instances independently retained |
| class_code_mapping | `active=false`; superseded versions retained via `version` increment (D-CERT-061) | âœ… 5y rolling (B-FM-04a) â€” old versions purged at 5y, aligned with reconciliation_run retention so every retained run's `mapping_version_used` stays resolvable | Old versions interpret historical runs within the 5y window |
| tracked_item | State-based, never boolean: `lifecycle_status` enum, `status='superseded'`, `supersedes_id` chain; drafts auto-expire 7d (D-CERT-076, audit `draft_expired`) | âœ… RESOLVED (B-FM-04b): draft expiry = **state flip, row retained** (the `draft_expired` audit action evidences the row's survival); post-decommission = **hard-delete with all vessel data at the 30-day mark (D-CERT-044)**, redacted audit slice retained (D-CERT-093) | NOT cascaded from catalog hard-purge; CSR retains all versions (D-CERT-039) |
| pdf_blob | `is_active=false` + `superseded_at`; `retention_policy` â†’ `scheduled_delete_at`; sweeper moves to delete-pending | YES â€” daily sweeper: soft-delete bucket â†’ hard-delete after 7-day grace (D-CERT-021) | Respects `dpa_retention_override_until` + `retain_all_versions` (CSR D-CERT-039); snapshot blobs retained indefinitely (D-CERT-020) |
| class_status_snapshot | `superseded_user_error=true` wrong-vessel rollback marker (D-CERT-051/058), row retained | None â€” metadata retained indefinitely hot (D-CERT-060); PDF retained indefinitely (D-CERT-020) | No purge job in Â§11 |
| reconciliation_run | None defined | âœ… 5y rolling (B-FM-04c) via nightly `vims_jobs` batch | Run = audit context for flags + `mapping_version_used` |
| reconciliation_flag | `resolved_at` + `resolution_action` close it (row retained) | âœ… 5y rolling (B-FM-04c) â€” purged with its run | FK â†’ run_id |
| audit_log | Nightly purge job soft-deletes past 5y, itself audited (D-CERT-099); hotâ†’cold at 2y (D-CERT-183) | Append-only to app (`vims_app` INSERT+SELECT only, D-CERT-179). âœ… RESOLVED (B-FM-03): retention batch + tier flip run under the new **`vims_jobs`** role (SEC-CERT-16) | EXCEPTION: catalog hard-purge cascades engine-level (D-CERT-182), bypassing GRANT because DELETE targets catalog_row |
| alert_config | None (`dpa_override_*` nulled back, not deleted) | âœ… RESOLVED (B-FM-04d): live config, **never purged** â€” current state, not history | `default_lead_days` immutable display (Â§10) |
| approval_event | None â€” timeline record | âœ… 5y rolling (B-FM-04e) + **joins the INSERT+SELECT-only GRANT regime** (append-only to app; purged only by `vims_jobs`) | FK â†’ tracked_item; vessel-decommission delete (D-CERT-044) overrides |
| notification_meta | Field-level purge: `body_content` NULL'd at 1y + `body_purged_at` (D-CERT-175) | âœ… 5y rolling rows (B-FM-04f) â€” consistent with D-CERT-175's "metadata 5y" | Companion `master_notification` certs rows are INSERT+SELECT-only (D-CERT-179) |
| print_artifact | None defined | âœ… 5y rolling (B-FM-04g) â€” artifact rows AND their PDF/Excel/ZIP blobs (pdf_blob `retention_policy` = 5y class) | Artifact blobs live in pdf_blob |
| external_auditor_access | Auto-expiry hourly job; early revoke ONLY via `expiry_at` edit (`revoked_via_expiry_edit=true`, D-CERT-195) â€” row retained | âœ… 5y rolling for expired grant rows (B-FM-04h) | No per-action activity rows exist (D-CERT-196) |
| batch_ingest | Terminal `status='cancelled'` (+ `cancelled_at/by`), row retained | âœ… 5y rolling (B-FM-04i), incl. `report_csv_blob_id` blob (5y class) | â€” |
| vessel_config | `lifecycle_status='pending_disposal'` + 30-day countdown (D-CERT-044); `sold_pending_handover` + bundle (D-CERT-093) | âœ… RESOLVED (B-FM-04j): at the 30-day mark the vessel's Certs data â€” vessel_config row, tracked_items, blobs â€” is **hard-deleted per D-CERT-044**; deletion event + redacted audit slice retained (D-CERT-093). Active vessels: live config, never purged | Audit enums `sale_completed`/`decommission` mark the deletion event |
| modification_event | None â€” grouping record (D-CERT-047); window self-closes | âœ… 5y rolling (B-FM-04k) | Not visible to external auditor (Â§20) |
| settings | âœ… RESOLVED (B-FM-05, 2026-06-12): **structured single-row table** (mirrors alert_config Â§10 pattern; complies with D-AUDRS-271 PK standard; also hosts `last_heartbeat_at` for OBS-CERT-11). Field rows encoded in Â§18 during step 0.4 | Live config, never purged | One row; columns per Â§18 |
| cert_change_log | None â€” append-only (`vims_app` INSERT+SELECT only, same regime as audit_log) | No app-side delete. âœ… 5y rolling (B-FM-04l) â€” same nightly `vims_jobs` batch as audit_log | Written in SAME transaction as the tracked-item update; vessel-decommission delete overrides |

---

## 25. Internal-Only Fields Index

> Added 2026-06-12 (v1.1) â€” aggregates every ðŸ”§ row in Â§Â§1â€“22 (justifications carried from the inline Notes; inline rows remain authoritative).

| Field (table.col) | Reason (one line) |
|-------------------|-------------------|
| catalog_section.sort_order | Server-side sort key; not displayed |
| catalog_section.created_at / created_by | Audit trail; reachable via `/certs/audit-log` filtered query |
| catalog_row.print_order | Server sort key |
| tracked_item.row_version | D-CERT-088 race resolution; sent in PATCH body, never displayed |
| tracked_item.version | Cross-module CAS counter (D-AUDRS-236/239); serialized for writers (Audit) only |
| pdf_blob.content_sha256 | Dedup per D-CERT-118; server-only |
| pdf_blob.schema_version | Migration / parser drift detection |
| class_status_snapshot.parsed_payload_schema_version | Payload schema versioning (D-CERT-062) |
| class_status_snapshot.upload_sha256 | Dedup per D-CERT-051 |
| reconciliation_run.flags_json | Dashboard aggregate; per-flag detail via separate endpoint |
| audit_log.schema_version | Schema drift versioning (locked by `AuditLog.record()`) |
| approval_event.tracked_item_id | URL context only |
| notification_meta.idempotency_key | DB UQ enforces D-CERT-174 |
| external_auditor_access.signup_token_hash | Server-only; raw token sent once in signup email then discarded |
| external_auditor_access.token_secret_hash | Auditor session token hash; never displayed |
| batch_ingest.vessel_id | URL context only |
| vessel_config.vessel_id | URL context only (PK = FK master_vessel) |
| settings.settings_id | Internal PK; DB default `NEWSEQUENTIALID()` |
| settings.singleton_key | Internal single-row guard; not serialized |
| settings.last_heartbeat_at | Internal heartbeat source exposed only through health/dashboard surfaces |
| cert_change_log.change_id | PK; internal |
| master_role.* / master_RoleByVessel.* / msc_profiles.* | RBAC enforcement; server-only (Â§19) |
| Mapping_CrewAssReviewers + has_global_vessel_access | DPA full-fleet override (D-CERT-090); server-only (Â§19) |

---

## 26. Computed / Derived Fields (API-only, no DB column)

> Added 2026-06-12 (v1.1) â€” sources: BACKEND_STRUCTURE Â§6 services, Â§8â€“Â§11; FIELD_MAP Â§4/Â§5/Â§22; D-CERT-063/064/087/119/128. Rows marked **persisted-derived** DO have a DB column but the value is always machine-computed (never user-entered) â€” listed so nobody hand-writes them.

| API field | Source | Derivation | Recompute trigger |
|-----------|--------|------------|-------------------|
| `windowOpen` / `windowClose` | `services/survey_window.py` â†’ tracked_item (**persisted-derived**) | `compute_window()` from `anniversary_date` + cadence + IMO window rules as data tables (Â±3 mo renewal, Â±2 mo annual). Parser NEVER parses windows (D-CERT-063/064); NK `Range Date` = sanity check only (>7d disagreement â†’ flag) | Create; anniversary edit (audited); catalog cadence change â†’ bulk recompute; hourly cadence cron |
| `nextDueDate` | Same tuple (**persisted-derived**) | Third element of `(window_open, window_close, next_due_date)` | Same + nightly status-flip cron |
| `status` | tracked_item.status (**hybrid**) | Read-time computed EXCEPT sticky stored states: `superseded`, `expired_at_onboarding`, `pending_first_upload`, `invalid_due_to_reflag`, `pending_supersession` (Â§4). Inputs: window/expiry/next_due/postponed vs today | Read time; hourly + nightly crons |
| `classRowExtract` | reconciliation_flag.class_row_extract_json (**persisted-derived**) | Denormalized matching row from snapshot.parsed_payload_json, written by reconciliation engine | New run only â€” immutable per run |
| `diff` | reconciliation_flag.diff_json (**persisted-derived**) | Per-field catalog-vs-class diff computed during bucketing | New run only |
| `changes[]` | cert_change_log rows (**API-only**) | Aggregation of field_name/old_value/new_value/source_module/version_after into per-cert history (Â§22, `CertChangeHistoryDrawer` âš  build-time) | On read; rows appended transactionally per write |
| Signed blob download URLs | pdf_blob.blob_storage_path (**API-only**) | Raw S3 path never sent; signed URL minted per request (Â§5) | Every request |
| Mandatory coverage % | `services/coverage.py` (**API-only**) | `compute_mandatory_coverage(vessel_id)` from `mandatory_for_all_vessels` rows vs tracked items; drives onboarding step-6 gate + `CoverageBanner` (D-CERT-119) | Read time; override stores reason on vessel_config |
| `vessel_acked` | notification_meta ack fields (**API-only**) | Office dashboard derives yes/no from vessel-side copy ack â€” independent ack model (D-CERT-087) | Read time; flips on vessel ack |
| `systemStateHash` | `services/system_state_hash.py` â†’ print_artifact (**persisted-derived**) | 8-char hash of vessel cert state for print identifiability (D-CERT-128); printed in footer | Once at generation; immutable |
| `print_id` | print_artifact PK (**persisted-derived**) | Single-vessel: `SQE-S633-<imo>-<yyyymmdd>-<seq>`; fleet/multi-vessel: `SQE-S633-FLEET-<yyyymmdd>-<seq>` (D-CERT-128; B-PRT-01 resolved 2026-06-29) | Once at generation |
| `scheduledDeleteAt` | pdf_blob (**persisted-derived**) | From retention_policy + supersession (Â§3.5) | Supersession; DPA retention override (D-CERT-021) |
| `idempotency_key` | notification_meta (**persisted-derived**) | `(cert_row_id, cadence, sent_date)` at dispatch (D-CERT-174) | Once per dispatch attempt |
| Dashboard aggregates | `/api/certs/dashboard/*` (**API-only**) | Tile/rollup aggregates over tracked_item status + reconciliation buckets (`DashboardKpiCards`) | Read time |
