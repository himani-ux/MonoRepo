# VIMS Certificates Module — Product Requirements Document (PRD)

> **Version:** 1.0
> **Last Updated:** 2026-05-13
> **Status:** Requirements Locked — Ready for Build
> **Decision Owner:** Prince (Maritime Product Owner)
> **Source:** `../VIMS-CERTIFICATES-MODULE-SSOT.md` (§1–§18, 198 D-CERT-\* decisions across 7 interrogation rounds)
> **Inherits pattern from:** `../VIMS-Safety-Module/PRD.md`
> **Replaces:** SMS-controlled document `SQE S 633 Certificates and Surveys` and the email-distributed `TEC-04B Report on Certificate Status` workflow.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Glossary](#2-glossary)
3. [Feature Registry](#3-feature-registry)
4. [Catalog Management (FEAT-CERT-CAT-\*)](#4-catalog-management)
5. [TrackedItem Lifecycle (FEAT-CERT-TRK-\*)](#5-trackeditem-lifecycle)
6. [OCR Pipeline (FEAT-CERT-OCR-\*)](#6-ocr-pipeline)
7. [Class Status Reconciliation (FEAT-CERT-REC-\*)](#7-class-status-reconciliation)
8. [RBAC & Approval Workflow (FEAT-CERT-RBAC-\*)](#8-rbac--approval-workflow)
9. [Onboarding Wizard (FEAT-CERT-WIZ-\*)](#9-onboarding-wizard)
10. [Print, Export & Share Bundle (FEAT-CERT-PRT-\*)](#10-print-export--share-bundle)
11. [Notification Engine (FEAT-CERT-NOTIF-\*)](#11-notification-engine)
12. [Audit Log (FEAT-CERT-AUDIT-\*)](#12-audit-log)
13. [External Auditor Access (FEAT-CERT-EXT-\*)](#13-external-auditor-access)
14. [Migration & Cutover (FEAT-CERT-MIG-\*)](#14-migration--cutover)
15. [Vessel Lifecycle Events (FEAT-CERT-LIFE-\*)](#15-vessel-lifecycle-events)
16. [Blob Storage & Retention (FEAT-CERT-BLOB-\*)](#16-blob-storage--retention)
17. [Cross-Module Boundary (FEAT-CERT-XMOD-\*)](#17-cross-module-boundary)
18. [Dashboard (FEAT-CERT-DASH-\*)](#18-dashboard)
19. [Deferred & Out of Scope](#19-deferred--out-of-scope)
20. [Global Business Rules](#20-global-business-rules)
21. [User Roles & Permissions](#21-user-roles--permissions)

---

## 1. Overview

**Project:** VIMS Certificates Module — replacement of KSM's manual Excel-based fleet certificate register with a single, fleet-wide, office-controlled, vessel-aware tracking system. The legacy artifacts being replaced are the SMS-controlled `SQE S 633 Certificates and Surveys.xlsx` (preserved as print-only output layout per D-CERT-002) and the operational `TEC-04B Report on Certificate Status.xlsx` (used as catalog inspiration only per D-CERT-003).

**V1 scope (12 sub-feature domains):**
- **Catalog management** — fleet-wide office-controlled master catalog of ~340 cert types across 9 sections; vessels cannot add types.
- **TrackedItem lifecycle** — single entity per cert/survey/calibration instance per vessel; rich date model; validity types `full / conditional / short_term / permanent`; STC + class extension + flag dispensation modeled as separate linked rows.
- **OCR pipeline** — text-OCR for vessel-uploaded cert PDFs (≥80% office migration / ≥85% vessel-side auto-accept thresholds); class-status snapshot PDFs are text-extracted first, with OCR fallback only when the full PDF exposes no text layer (D-CERT-200).
- **Class status reconciliation** — manual upload + per-class parser (NK / KR / BV); 3-month cadence; mismatch alerts to Master + Marine Sup'tt; class is authoritative for `is_class_tracked: true` rows.
- **RBAC & approval** — Master = onboard admin (PSC Inspection pattern); C/O + C/E + 2/E submit-with-Master-approval for non-class-tracked rows; office (DPA / FM / Tech / Marine Sup'tt) writes direct.
- **7-step onboarding wizard** — vessel-locked, batch PDF ingest in batches of ≤10, gap-fill UI, mandatory-coverage gate before go-live.
- **Print, export & share bundle** — SQE S 633 artifact identity retained in stored records/filenames; clean 10-column normal PDF layout; ZIP bundle (manifest PDF + cert PDFs) for external distribution.
- **Notification engine** — per-side channel routing (vessel = in-app + email; office = in-app + Slack); escalation cadence DPA + Technical Manager + Marine Sup'tt; 24/7 (no quiet hours); always-grouped multi-cert alerts.
- **Audit log** — append-only DB role separation (`vims_app` INSERT+SELECT only); 5-year rolling retention; hot 2y + cold 3y tiering; redacted view for external auditors.
- **External auditor access** — Marine Sup'tt self-service provisioning (DPA override); time-bound (7d default, 30d max); vessel + doc-set scope; auto-expire only (no early revocation); no activity tracking.
- **Migration & cutover** — hard cutover (no parallel-run period); legacy Excel files frozen post-go-live; FM sign-off per vessel.
- **Vessel lifecycle events** — decommissioning (30d soft-delete), sale (handover bundle + locked in-flight subs), flag change (statutory auto-flagged invalid), class change (pending-supersession state).

**Regulatory anchors:** ISM Code 2010 amendments; SOLAS Ch IX (as amended) — certificate regimes; MARPOL Annex I/II/IV/V/VI consolidated 2022; IMO Resolutions A.1075(28), A.884(21); MLC 2006 + DMLC; class society survey schemes (NK / KR / BV); KSM SSQE Manual Rev 01 Feb 2026.

**Platform context:** Certs lives as a child module in the VIMS monorepo at `apps/certs/` (Django) and `routes/certs/`, `components/certs/`, `hooks/certs/`, `stores/certs/`, `schemas/certs/` (React). Shared DB `ksm_cms_live`. Shared auth (SimpleJWT + `msc_profiles`). API under `/api/certs/`. Module tables use prefix `vims_certs_*`; reference/master data uses `master_*`.

**Volume estimate:** ~340 catalog items × 6 fleet vessels = **~2,040 TrackedItem records at go-live** (per SSOT §1.1). Fleet is **online-required (Starlink-equipped)** per D-CERT-156.

**Priority tiers used in this PRD:**
- **V1** — must-ship for first release.
- **V1.1** — stretch goal for initial release; scheduled but may slip one sprint.
- **V2** — explicitly deferred (revisit after V1 stabilization).
- **OUT** — explicitly out of scope, never built (e.g. class portal API per D-CERT-169).

---

## 2. Glossary

| Term | Expansion |
|------|-----------|
| DPA | Designated Person Ashore (ISM Code §4 — the system admin role for Certs) |
| FM | Fleet Manager |
| TM | Technical Manager (head of Technical department; distinct from Tech Sup'tt; D-CERT-098) |
| Tech Sup'tt | Technical Superintendent (office) |
| Marine Sup'tt | Marine Superintendent (office; primary reconciliation reviewer per D-CERT-068, primary auditor liaison per D-CERT-194) |
| Master | Vessel commanding officer; vessel-side admin per PSC Inspection pattern (D-CERT-077, D-CERT-165) |
| C/O · C/E · 2/E | Chief Officer · Chief Engineer · Second Engineer (vessel submitters with Master-approval gate per D-CERT-079 / D-CERT-199) |
| RO | Recognized Organization (class society acting on behalf of Flag administration) |
| STC | Short-Term Certificate (class-issued bridge cert covering gap to next port; D-CERT-012) |
| COC | Certificate of Class (class society's primary doc — NOT Certificate of Competency, which is a crew cert handled by CMS) |
| CG2 | Cargo Gear Certificate |
| LI | Loading Instrument Certificate |
| CSR | Continuous Synopsis Record (D-CERT-039 — single TrackedItem with `retain_all_versions: true`) |
| CMS (PMS) | Continuous Machinery Survey — class-society scheme tracked in PMS module, NOT Certs (D-CERT-015) |
| CMS (Crewing) | Crew Management System — separate platform from VIMS that handles crew personnel data + crew certs (D-CERT-177) |
| IMO Number | International Maritime Organization vessel identifier — authoritative key for vessel/PDF matching (D-CERT-031, D-CERT-050, D-CERT-111) |
| ISM SMC | International Safety Management Safety Management Certificate |
| ISPS SSC | International Ship & Port Security Code Ship Security Certificate |
| MLC | Maritime Labour Convention |
| DMLC I/II | Declaration of MLC Compliance Part I (flag) / Part II (company) |
| IOPP | International Oil Pollution Prevention (cert; Form A and Form B variants per D-CERT-032) |
| SQE S 633 | KSM SMS-controlled document code preserved verbatim in Certs module print output (D-CERT-002, D-CERT-125) |
| TEC-04B | Legacy KSM Excel form, used as catalog inspiration (D-CERT-003, D-CERT-103) |
| Anniversary date | Per-vessel-cert-family anchor for survey-window computation; set ONCE at onboarding by office (D-CERT-074, D-CERT-110) |
| `is_class_tracked` | Catalog-row flag indicating cert appears on NK/KR/BV class status report; class is authoritative (D-CERT-009) |
| `submission_scope` | Catalog-row enum `master_only` vs `all_ranks_with_approval`; shipped active catalog rows use `all_ranks_with_approval` (D-CERT-079 / D-CERT-199) |
| `print_id` | Human-readable print artifact ID `SQE-S633-<imo>-<yyyymmdd>-<seq>` for single-vessel artifacts; fleet/multi-vessel artifacts use `SQE-S633-FLEET-<yyyymmdd>-<seq>` (D-CERT-128; B-PRT-01 resolved 2026-06-29) |
| Magic-link ack | Single-use 24h-expiring URL in notification email enabling one-click acknowledge without full app login (D-CERT-154) |
| Per-side routing | Notification rule: vessel users get in-app+email only; office users get in-app+Slack only (D-CERT-161) |

First-use expansions applied once; re-occurrences use the acronym.

---

## 3. Feature Registry

198 SSOT decisions condense into 145 V1 features across 14 domains. Per-feature acceptance criteria appear in §§4–18.

| ID | Feature | Domain | Priority | Governing D-CERT-\* |
|----|---------|--------|----------|---------------------|
| FEAT-CERT-CAT-001 | Office-controlled fleet master catalog (~340 items) | CAT | V1 | D-CERT-004, D-CERT-017 |
| FEAT-CERT-CAT-002 | Catalog seed = union of S 633 + TEC-04B with dedup | CAT | V1 | D-CERT-023, D-CERT-103, D-CERT-107 |
| FEAT-CERT-CAT-003 | 9 canonical catalog sections | CAT | V1 | D-CERT-017 |
| FEAT-CERT-CAT-004 | Catalog row schema (15+ standard fields) | CAT | V1 | D-CERT-109 |
| FEAT-CERT-CAT-005 | Vessel-type filter (`applicable_ship_types[]`) | CAT | V1 | D-CERT-028, D-CERT-109 |
| FEAT-CERT-CAT-006 | Per-vessel applicability mode (`all_matching_type` vs `specific_vessel_ids`) | CAT | V1 | D-CERT-029 |
| FEAT-CERT-CAT-007 | Cert hierarchy via `parent_id` (arbitrary depth schema, 2-level UI cap) | CAT | V1 | D-CERT-010, D-CERT-013, D-CERT-108 |
| FEAT-CERT-CAT-008 | New "Class Certificates" section (COC + CG2 + LI + Notations + class surveys) | CAT | V1 | D-CERT-014, D-CERT-033, D-CERT-034 |
| FEAT-CERT-CAT-009 | IOPP-A/B variant model (`form_variant` field, single canonical row) | CAT | V1 | D-CERT-032 |
| FEAT-CERT-CAT-010 | Multi-instance equipment (`parent_supports_dynamic_children` flag) | CAT | V1 | D-CERT-035 |
| FEAT-CERT-CAT-011 | Roll-up rows for portable equipment (1 TrackedItem per vessel) | CAT | V1 | D-CERT-036, D-CERT-040 |
| FEAT-CERT-CAT-012 | Class IWS survey age-gated (≤15-year vessels, auto-disables) | CAT | V1 | D-CERT-034 |
| FEAT-CERT-CAT-013 | Type Approvals with optional `linked_pms_component_id` | CAT | V1 | D-CERT-042 |
| FEAT-CERT-CAT-014 | Tonnage Tax per-vessel cadence + anchor | CAT | V1 | D-CERT-027 |
| FEAT-CERT-CAT-015 | Catalog deprecation (active=false, no new instances) | CAT | V1 | §9.3 SSOT |
| FEAT-CERT-CAT-016 | Inline catalog promotion during onboarding | CAT | V1 | D-CERT-122 |
| FEAT-CERT-CAT-017 | Catalog-edit RBAC (DPA + System Admin only) | CAT | V1 | §9.3 SSOT, D-CERT-090 |
| FEAT-CERT-CAT-018 | Catalog change audit log entry (every add/deprecate/modify) | CAT | V1 | §9.3 SSOT, D-CERT-091, D-CERT-099 |
| FEAT-CERT-CAT-019 | Bulk soft-delete cap (50 rows/batch + reason) | CAT | V1 | D-CERT-092 |
| FEAT-CERT-CAT-020 | Catalog row hard-purge cascade to vessel-instance audit | CAT | V1 | D-CERT-182 |
| FEAT-CERT-TRK-001 | TrackedItem core schema (per §5.1 SSOT) | TRK | V1 | D-CERT-010, D-CERT-011 |
| FEAT-CERT-TRK-002 | Validity types `full / conditional / short_term / permanent` | TRK | V1 | D-CERT-012 |
| FEAT-CERT-TRK-003 | STC modeled as `relationship_type=short_term_for` | TRK | V1 | D-CERT-012 |
| FEAT-CERT-TRK-004 | Class extension as `relationship_type=extension_of` | TRK | V1 | D-CERT-013, D-CERT-065 |
| FEAT-CERT-TRK-005 | Flag dispensation as `relationship_type=dispensation_for` | TRK | V1 | D-CERT-013 |
| FEAT-CERT-TRK-006 | Postponement field (`postponed_until`) on parent | TRK | V1 | D-CERT-065 |
| FEAT-CERT-TRK-007 | Anniversary date set ONCE at onboarding (office-locked) | TRK | V1 | D-CERT-074, D-CERT-110 |
| FEAT-CERT-TRK-008 | Computed survey windows (`window_open` / `window_close`) | TRK | V1 | D-CERT-063, D-CERT-064 |
| FEAT-CERT-TRK-009 | Computed cert status (`ok / window_opening / window_open / window_closing / overdue / done / postponed / superseded / n/a`) | TRK | V1 | §5.1 SSOT |
| FEAT-CERT-TRK-010 | `expired_at_onboarding` quarantine status (alert-suppressed until renewal or ack) | TRK | V1 | D-CERT-121 |
| FEAT-CERT-TRK-011 | `pdf_missing: true` row state (no auto-escalation) | TRK | V1 | D-CERT-113 |
| FEAT-CERT-TRK-012 | `supersedes_id` chain (full cert replaces STC) | TRK | V1 | §5.1, D-CERT-118 |
| FEAT-CERT-TRK-013 | Approval state machine (`draft / pending_master_approval / approved / rejected`) | TRK | V1 | D-CERT-018, D-CERT-076 |
| FEAT-CERT-TRK-014 | Draft auto-expire 7 days | TRK | V1 | D-CERT-076, D-CERT-167 |
| FEAT-CERT-TRK-015 | Renewal vs revision auto-detection on Master upload | TRK | V1 | D-CERT-170 |
| FEAT-CERT-TRK-016 | CSR retain-all-versions override (`retain_all_versions: true`) | TRK | V1 | D-CERT-039 |
| FEAT-CERT-OCR-001 | OCR all uploaded cert PDFs (extract type/IMO/dates/issuer) | OCR | V1 | D-CERT-101 |
| FEAT-CERT-OCR-002 | Required field set per cert (D-CERT-105 list) | OCR | V1 | D-CERT-105 |
| FEAT-CERT-OCR-003 | "No cert number" bypass with reason in audit | OCR | V1 | D-CERT-105 |
| FEAT-CERT-OCR-004 | Optional fields (last surveys, conditions, signature) | OCR | V1 | D-CERT-105 |
| FEAT-CERT-OCR-005 | Per-field 3-mode confidence (≥80% auto / 60–80% gap-fill / <60% manual) — OFFICE | OCR | V1 | D-CERT-106 |
| FEAT-CERT-OCR-006 | Per-field 3-mode confidence (≥85% auto / 60–85% gap-fill / <60% manual) — VESSEL | OCR | V1 | D-CERT-168 |
| FEAT-CERT-OCR-007 | Whole-doc unprocessable → manual entry | OCR | V1 | D-CERT-106 |
| FEAT-CERT-OCR-008 | Async OCR per batch (≤10 PDFs); resume in pending-review queue | OCR | V1 | D-CERT-104, D-CERT-123 |
| FEAT-CERT-OCR-009 | OCR result stored in `parsed_payload` per snapshot pattern | OCR | V1 | D-CERT-101, D-CERT-062 |
| FEAT-CERT-OCR-010 | IMO-first vessel matching with name fallback + DPA confirm | OCR | V1 | D-CERT-050, D-CERT-111 |
| FEAT-CERT-OCR-011 | Filename = tiebreaker only (NOT primary key) | OCR | V1 | D-CERT-101 |
| FEAT-CERT-OCR-012 | Tunable thresholds post-launch | OCR | V1 | D-CERT-106 |
| FEAT-CERT-OCR-013 | Vessel-side scanner upload path | OCR | V1 | D-CERT-166 |
| FEAT-CERT-OCR-014 | Vessel-side PDF upload path | OCR | V1 | D-CERT-166 |
| FEAT-CERT-OCR-015 | NO camera capture path | OCR | OUT | D-CERT-166 |
| FEAT-CERT-REC-001 | Manual class snapshot PDF upload (no portal API) | REC | V1 | D-CERT-005, D-CERT-169 |
| FEAT-CERT-REC-002 | Per-class parser modules (NK / KR / BV) | REC | V1 | D-CERT-005, §7.2 SSOT |
| FEAT-CERT-REC-003 | Class snapshot text-extract first, with OCR fallback for PDFs that expose no text layer | REC | V1 | D-CERT-048, D-CERT-200 |
| FEAT-CERT-REC-004 | Per-class report date extraction is mandatory: KR `Printed on`, NK `Printed on`, BV `Generated on`; no upload-time fallback | REC | V1 | D-CERT-049, D-CERT-049a |
| FEAT-CERT-REC-005 | 3-month upload cadence + 1-month lead alert (DPA-configurable) | REC | V1 | D-CERT-006 |
| FEAT-CERT-REC-006 | Event-driven snapshot refresh prompt (14d grace) | REC | V1 | D-CERT-007 |
| FEAT-CERT-REC-007 | SHA-256 dedup + re-process prompt | REC | V1 | D-CERT-051 |
| FEAT-CERT-REC-008 | Wrong-vessel rollback via `applied_changes[]` (Marine Sup'tt authorizes) | REC | V1 | D-CERT-058 |
| FEAT-CERT-REC-009 | Parser version stamping per snapshot; manual re-parse | REC | V1 | D-CERT-052 |
| FEAT-CERT-REC-010 | ≥0.95 per-field confidence for auto-include in reconciliation | REC | V1 | D-CERT-053 |
| FEAT-CERT-REC-011 | Multi-page table extraction (`pdfplumber` + custom continuation) | REC | V1 | D-CERT-054 |
| FEAT-CERT-REC-012 | Partial-parse state (1–25%); critical >25% | REC | V1 | D-CERT-055 |
| FEAT-CERT-REC-013 | Concurrent upload advisory lock (5-min timeout) | REC | V1 | D-CERT-056 |
| FEAT-CERT-REC-014 | 6-PDF reference fixture corpus + CI gate | REC | V1 | D-CERT-057 |
| FEAT-CERT-REC-015 | Parser hard timeout 5min + 2x retry (30s + 90s) | REC | V1 | D-CERT-059 |
| FEAT-CERT-REC-016 | Snapshot blob hot 5y → cold tier | REC | V1 | D-CERT-060 |
| FEAT-CERT-REC-017 | ClassCodeMapping versioned per edit | REC | V1 | D-CERT-061 |
| FEAT-CERT-REC-018 | Schema version on `parsed_payload` | REC | V1 | D-CERT-062 |
| FEAT-CERT-REC-019 | Parser SKIPS PSC/MoU + vessel particulars | REC | V1 | D-CERT-038, D-CERT-066 |
| FEAT-CERT-REC-020 | Parser PARSES only exact Conditions of Class content into Conditions of class review items; non-COC note/statutory/installation/memoranda sections are excluded | REC | V1 | D-CERT-066, D-CERT-207 |
| FEAT-CERT-REC-021 | UTF-8 encoding; class symbols stripped | REC | V1 | D-CERT-067 |
| FEAT-CERT-REC-022 | Reconciliation 3-panel UI (Matches / Mismatches / Unmapped) | REC | V1 | D-CERT-068 |
| FEAT-CERT-REC-023 | Snapshot list filters + 25-row pagination + CSV export | REC | V1 | D-CERT-069 |
| FEAT-CERT-REC-024 | NK Extended → child `extension_of`; NK Postponed → `postponed_until` | REC | V1 | D-CERT-065 |
| FEAT-CERT-REC-025 | Mismatch resolution = alert Master to update | REC | V1 | D-CERT-008 |
| FEAT-CERT-REC-026 | Class-authoritative tie-breaker for `is_class_tracked` rows | REC | V1 | D-CERT-009 |
| FEAT-CERT-REC-027 | Marine Sup'tt = primary reconciliation reviewer | REC | V1 | D-CERT-068, §6.1 SSOT |
| FEAT-CERT-REC-028 | Format-change FAIL SOFT (`unmapped_rows[]`, no fuzzy fallback) | REC | V1 | D-CERT-031 |
| FEAT-CERT-REC-029 | >25% unmapped → critical escalation | REC | V1 | D-CERT-031, D-CERT-073 |
| FEAT-CERT-REC-030 | Parser ops page (dev-only, feature-flagged) | REC | V1 | D-CERT-072 |
| FEAT-CERT-REC-031 | Anomaly thresholds (mismatch>15% / parse>3min / count<exp×0.7) | REC | V1 | D-CERT-073 |
| FEAT-CERT-RBAC-001 | Master = onboard admin (PSC Inspection pattern) | RBAC | V1 | D-CERT-018, D-CERT-077 |
| FEAT-CERT-RBAC-002 | C/O + C/E + 2/E submit-with-Master-approval | RBAC | V1 | D-CERT-018, D-CERT-079, D-CERT-199 |
| FEAT-CERT-RBAC-003 | Office direct write (DPA / FM / Tech / Marine Sup'tt) | RBAC | V1 | D-CERT-018 |
| FEAT-CERT-RBAC-004 | `submission_scope` per row; active catalog rows use `all_ranks_with_approval` | RBAC | V1 | D-CERT-079, D-CERT-199 |
| FEAT-CERT-RBAC-005 | Master self-submission = no self-approval gate | RBAC | V1 | D-CERT-165 |
| FEAT-CERT-RBAC-006 | Approval workflow lifecycle (PSC CAR pattern) | RBAC | V1 | D-CERT-076 |
| FEAT-CERT-RBAC-007 | Draft auto-expire 7 days | RBAC | V1 | D-CERT-076 |
| FEAT-CERT-RBAC-008 | No hard resubmission limit; FM auto-flag at 3 rejections | RBAC | V1 | D-CERT-080 |
| FEAT-CERT-RBAC-009 | No 2FA / step-up reauth | RBAC | V1 | D-CERT-081 |
| FEAT-CERT-RBAC-010 | Confirmation dialog on destructive ops (named action + reversal path) | RBAC | V1 | D-CERT-081 |
| FEAT-CERT-RBAC-011 | Session timeout (8h office / 24h vessel) — Purchase R3-7 inheritance | RBAC | V1 | D-CERT-082 |
| FEAT-CERT-RBAC-012 | PMS-style re-auth modal (preserves form state) | RBAC | V1 | D-CERT-082 |
| FEAT-CERT-RBAC-013 | One-Master-one-ship (multi-vessel Master NOT supported) | RBAC | V1 | D-CERT-083 |
| FEAT-CERT-RBAC-014 | Deputy DPA (1 user, ISM §4) — permission inheritance, not notification forward | RBAC | V1 | D-CERT-078, D-CERT-160 |
| FEAT-CERT-RBAC-015 | Office hierarchy = inherit PSC Inspection RBAC tables | RBAC | V1 | D-CERT-090 |
| FEAT-CERT-RBAC-016 | Auditor role = NOT a separate role (Model B distributed) | RBAC | V1 | D-CERT-086 |
| FEAT-CERT-RBAC-017 | Approval queue sort = expiry-first | RBAC | V1 | D-CERT-088 |
| FEAT-CERT-RBAC-018 | Bulk-approve allowed for Equipment / Calibrations / Tests / Misc only | RBAC | V1 | D-CERT-088 |
| FEAT-CERT-RBAC-019 | Class + Statutory require per-cert review (no bulk) | RBAC | V1 | D-CERT-088 |
| FEAT-CERT-RBAC-020 | Race resolution via row-version (second approver gets toast) | RBAC | V1 | D-CERT-088 |
| FEAT-CERT-RBAC-021 | TM + Marine Sup'tt per-vessel assignment via Vessel Profile | RBAC | V1 | D-CERT-098 |
| FEAT-CERT-RBAC-022 | Marine Sup'tt vessel scope = `master_RoleByVessel` | RBAC | V1 | D-CERT-090 |
| FEAT-CERT-RBAC-023 | DPA = full fleet (`has_global_vessel_access`) | RBAC | V1 | D-CERT-090 |
| FEAT-CERT-RBAC-024 | No break-glass / emergency-override mechanism | RBAC | V1 | D-CERT-097 |
| FEAT-CERT-RBAC-025 | Anniversary recompute = bulk allowed + 2nd FM approver + preview | RBAC | V1 | D-CERT-092 |
| FEAT-CERT-RBAC-026 | Catalog push to fleet auto-creates `pending_first_upload` rows | RBAC | V1 | D-CERT-092 |
| FEAT-CERT-WIZ-001 | 7-step onboarding wizard (D-CERT-120 sequence) | WIZ | V1 | D-CERT-120 |
| FEAT-CERT-WIZ-002 | Step 1 — Vessel selection from `master_vessel` (or create) | WIZ | V1 | D-CERT-120 |
| FEAT-CERT-WIZ-003 | Step 2 — Vessel profile (anniversary, ship type, Master, TM, Marine Sup'tt) | WIZ | V1 | D-CERT-120, D-CERT-098, D-CERT-110 |
| FEAT-CERT-WIZ-004 | Pending cert rows pre-populated from `applicable_ship_types` | WIZ | V1 | D-CERT-109, D-CERT-120 |
| FEAT-CERT-WIZ-005 | Step 3 — Vessel-locked batch PDF ingest (≤10 PDFs/batch) | WIZ | V1 | D-CERT-104, D-CERT-112, D-CERT-120 |
| FEAT-CERT-WIZ-006 | Save-as-draft between batches (multi-day onboarding) | WIZ | V1 | D-CERT-104 |
| FEAT-CERT-WIZ-007 | Mixed-vessel batches NOT supported in V1 | WIZ | V1 | D-CERT-112 |
| FEAT-CERT-WIZ-008 | Step 3 — Dry-run preview-commit cycle per batch | WIZ | V1 | D-CERT-115 |
| FEAT-CERT-WIZ-009 | Step 3 — Validation gates at commit time (block vs warn matrix) | WIZ | V1 | D-CERT-116 |
| FEAT-CERT-WIZ-010 | Step 3 — Batch ingest CSV report artifact | WIZ | V1 | D-CERT-117 |
| FEAT-CERT-WIZ-011 | Step 3 — Re-import idempotency (SHA-256 + supersede prompt) | WIZ | V1 | D-CERT-118 |
| FEAT-CERT-WIZ-012 | Step 3 — Inline catalog promotion for uncatalogued cert types | WIZ | V1 | D-CERT-122 |
| FEAT-CERT-WIZ-013 | Step 3 — Async OCR + pending-review queue resume | WIZ | V1 | D-CERT-123 |
| FEAT-CERT-WIZ-014 | Step 4 — Class Status PDF upload + Stage 3 reconciliation | WIZ | V1 | D-CERT-100, D-CERT-120 |
| FEAT-CERT-WIZ-015 | Step 4 — Anniversary cross-validation against class report | WIZ | V1 | D-CERT-110 |
| FEAT-CERT-WIZ-016 | Step 5 — Reconciliation review (DPA resolves discrepancies) | WIZ | V1 | D-CERT-068, D-CERT-120 |
| FEAT-CERT-WIZ-017 | Step 6 — Mandatory coverage gate (auto-enable or override-with-reason) | WIZ | V1 | D-CERT-119 |
| FEAT-CERT-WIZ-018 | Step 7 — FM sign-off → vessel goes live | WIZ | V1 | D-CERT-120 |
| FEAT-CERT-WIZ-019 | Vessel-level rollback during onboarding only (pre-go-live) | WIZ | V1 | D-CERT-124 |
| FEAT-CERT-WIZ-020 | Already-expired-at-onboarding → quarantine state, alerts suppressed | WIZ | V1 | D-CERT-121 |
| FEAT-CERT-WIZ-021 | No separate Master ack step at go-live | WIZ | V1 | D-CERT-120 |
| FEAT-CERT-WIZ-022 | Welcome notification + suppress historical backlog at go-live | WIZ | V1 | D-CERT-173 |
| FEAT-CERT-PRT-001 | Print preserves "SQE S 633" form code verbatim | PRT | V1 | D-CERT-002, D-CERT-125 |
| FEAT-CERT-PRT-002 | Free-design layout (not pixel-faithful Excel) | PRT | V1 | D-CERT-125, D-CERT-129 |
| FEAT-CERT-PRT-003 | Vessel header block on every page | PRT | V1 | D-CERT-126, D-CERT-127 |
| FEAT-CERT-PRT-004 | Company logo from shared endpoint (PSC Inspection pattern) | PRT | V1 | D-CERT-127 |
| FEAT-CERT-PRT-005 | Logo size 30mm × 15mm top-left | PRT | V1 | D-CERT-127 |
| FEAT-CERT-PRT-006 | Stored print identity with print_id, state hash, user, role, and UTC timestamp in DB/API/audit/history; normal visible PDFs print only `Printed by`, and normal visible Excel workbooks omit print ID/scope/hash rows | PRT | V1 | D-CERT-128, D-CERT-202, D-CERT-212 |
| FEAT-CERT-PRT-007 | `print_id` format `SQE-S633-<imo>-<yyyymmdd>-<seq>` for single-vessel artifacts; `SQE-S633-FLEET-<yyyymmdd>-<seq>` for fleet/multi-vessel artifacts | PRT | V1 | D-CERT-128; B-PRT-01 |
| FEAT-CERT-PRT-008 | Empty-section banner ("no certs in this section") | PRT | V1 | D-CERT-129 |
| FEAT-CERT-PRT-009 | Clean 10-column normal print PDF schema without validity-code column | PRT | V1 | D-CERT-130, D-CERT-202 |
| FEAT-CERT-PRT-010 | Date format `dd-Mmm-yyyy` throughout | PRT | V1 | D-CERT-131 |
| FEAT-CERT-PRT-011 | Legacy validity short codes (A / Bi-A / 5-Y / 10-Y / Perm. / ST / 6-Mth) | PRT | V1 | D-CERT-132 |
| FEAT-CERT-PRT-012 | Validity data remains in system records; normal visible PDFs omit the validity code column and glossary | PRT | V1 | D-CERT-132, D-CERT-202 |
| FEAT-CERT-PRT-013 | Cert hierarchy sub-numbering (`19`, `19.a`, `19.b`) | PRT | V1 | D-CERT-133 |
| FEAT-CERT-PRT-014 | Section-row ordering by `print_order` with parent-child grouping | PRT | V1 | D-CERT-134 |
| FEAT-CERT-PRT-015 | Status visualization = color + shape hybrid (B/W resilient) | PRT | V1 | D-CERT-135 |
| FEAT-CERT-PRT-016 | 5-tier expiry urgency (>90 / ≤90 / ≤30 / ≤7 / ≤0 days) | PRT | V1 | D-CERT-136 |
| FEAT-CERT-PRT-017 | English-only V1 (no multi-language) | PRT | V1 | D-CERT-137 |
| FEAT-CERT-PRT-018 | Watermark scope retained for share/auditor/backend-compatible artifact paths; normal Print certs status UI submits no watermark | PRT | V1 | D-CERT-138, D-CERT-208, D-CERT-209 |
| FEAT-CERT-PRT-019 | Digital signature indicator only (no wet-sig block) | PRT | V1 | D-CERT-139 |
| FEAT-CERT-PRT-020 | Normal Print certs status uses current vessel plus one Certificate sections dropdown containing All sections plus section names; backend scope/custom ID compatibility retained | PRT | V1 | D-CERT-140, D-CERT-208, D-CERT-209, D-CERT-210, D-CERT-211 |
| FEAT-CERT-PRT-021 | Per-section fleet-wide RBAC = DPA + FM only | PRT | V1 | D-CERT-141, D-CERT-142 |
| FEAT-CERT-PRT-022 | Excel export = data-only + companion PDF (no live formulas); user-visible Excel omits internal print ID, scope, and state hash rows | PRT | V1 | D-CERT-141, D-CERT-212 |
| FEAT-CERT-PRT-023 | Print RBAC matrix per scope × role | PRT | V1 | D-CERT-142 |
| FEAT-CERT-PRT-024 | Soft-throttle >10/hr surfaced to FM dashboard | PRT | V1 | D-CERT-143 |
| FEAT-CERT-PRT-025 | Sync ≤60s per-vessel; async 5min fleet-wide | PRT | V1 | D-CERT-144 |
| FEAT-CERT-PRT-026 | Third-party deliverable = ZIP (manifest PDF + cert PDFs) | PRT | V1 | D-CERT-096, D-CERT-145 |
| FEAT-CERT-PRT-027 | Master share-bundle section multi-select; backend-compatible custom certificate IDs retained | PRT | V1 | D-CERT-096, D-CERT-210 |
| FEAT-CERT-PRT-028 | Bundle filename `VIMS_CertBundle_<vessel>_<yyyymmdd>_<print_id>.zip` | PRT | V1 | D-CERT-145 |
| FEAT-CERT-PRT-029 | Single live template; immutable artifacts in audit log | PRT | V1 | D-CERT-146 |
| FEAT-CERT-PRT-030 | Audit log granularity: hash + artifact refs (no row JSON dump) | PRT | V1 | D-CERT-147 |
| FEAT-CERT-PRT-031 | Historical reprint via audit-log artifact + downloadable original Class Status PDF | PRT | V1 | D-CERT-148 |
| FEAT-CERT-PRT-032 | Normal Print certs status delivery = browser download + auto-archive; optional email remains for share/backend-compatible generation | PRT | V1 | D-CERT-149, D-CERT-208, D-CERT-209 |
| FEAT-CERT-PRT-033 | Hard-fail with support ticket + retry; no auto-retry | PRT | V1 | D-CERT-150 |
| FEAT-CERT-NOTIF-001 | Reuse `master_notification` (in-app) + `email_dispatcher` (email) | NOTIF | V1 | D-CERT-151 |
| FEAT-CERT-NOTIF-002 | Slack added to V1 (per-vessel + fleet office channels) | NOTIF | V1 | D-CERT-151 |
| FEAT-CERT-NOTIF-003 | Per-side channel routing (vessel=in-app+email; office=in-app+Slack) | NOTIF | V1 | D-CERT-161 |
| FEAT-CERT-NOTIF-004 | Trigger matrix per §6.1 SSOT (window/expiry/STC/snapshot/reconciliation) | NOTIF | V1 | D-CERT-016 |
| FEAT-CERT-NOTIF-005 | Window alerts visible to BOTH Master + Office | NOTIF | V1 | D-CERT-016 |
| FEAT-CERT-NOTIF-006 | Email format = HTML + plain-text multipart | NOTIF | V1 | D-CERT-152 |
| FEAT-CERT-NOTIF-007 | Email subject conventions (`[VIMS Certs]`, no emoji in subject) | NOTIF | V1 | D-CERT-153 |
| FEAT-CERT-NOTIF-008 | Magic-link 24h-expiring single-use ack | NOTIF | V1 | D-CERT-154 |
| FEAT-CERT-NOTIF-009 | No inbound email parsing | NOTIF | V1 | D-CERT-154 |
| FEAT-CERT-NOTIF-010 | Notification audit trail (recipient/channel/delivery/ack/escalation) | NOTIF | V1 | D-CERT-155 |
| FEAT-CERT-NOTIF-011 | NO email open tracking | NOTIF | V1 | D-CERT-155 |
| FEAT-CERT-NOTIF-012 | Online-required (no IndexedDB / offline queue / sync) | NOTIF | V1 | D-CERT-156 |
| FEAT-CERT-NOTIF-013 | NO quiet hours (24/7 cadence) | NOTIF | V1 | D-CERT-157 |
| FEAT-CERT-NOTIF-014 | Monthly fleet digest only (1st of month, 08:00 ICT) → DPA + Marine Sup'tt | NOTIF | V1 | D-CERT-158 |
| FEAT-CERT-NOTIF-015 | NO daily / weekly / FM / Master digest | NOTIF | V1 | D-CERT-158 |
| FEAT-CERT-NOTIF-016 | Email retry 3x exponential backoff (1/5/30min) | NOTIF | V1 | D-CERT-159 |
| FEAT-CERT-NOTIF-017 | Bouncing-email auto-fall-back to Slack DM for critical alerts | NOTIF | V1 | D-CERT-159 |
| FEAT-CERT-NOTIF-018 | DPA dashboard surfaces bouncing-user count | NOTIF | V1 | D-CERT-159 |
| FEAT-CERT-NOTIF-019 | NO per-user notification preferences | NOTIF | V1 | D-CERT-160 |
| FEAT-CERT-NOTIF-020 | DPA centrally configures per-vessel Slack routing | NOTIF | V1 | D-CERT-160 |
| FEAT-CERT-NOTIF-021 | Escalation cadence per D-CERT-089 wiring | NOTIF | V1 | D-CERT-089, D-CERT-162 |
| FEAT-CERT-NOTIF-022 | Statutory + Class certs uplift (DPA + TM Day-1) | NOTIF | V1 | D-CERT-089 |
| FEAT-CERT-NOTIF-023 | FM joins escalation at Day 7 no-ack | NOTIF | V1 | D-CERT-162 |
| FEAT-CERT-NOTIF-024 | Direct operational tone (no corporate prose) | NOTIF | V1 | D-CERT-163 |
| FEAT-CERT-NOTIF-025 | Always-grouped multi-cert alerts (same vessel, same day) | NOTIF | V1 | D-CERT-164 |
| FEAT-CERT-NOTIF-026 | Independent ack model (vessel + office ack separately) | NOTIF | V1 | D-CERT-087 |
| FEAT-CERT-NOTIF-027 | Office dashboard surfaces `vessel_acked: yes/no` | NOTIF | V1 | D-CERT-087 |
| FEAT-CERT-NOTIF-028 | Hierarchical close on full resolution (renewal → both dismissed) | NOTIF | V1 | D-CERT-085, D-CERT-087 |
| FEAT-CERT-NOTIF-029 | Alert dedup: one active per `(cert_row, cadence)` + 60-min batch window | NOTIF | V1 | D-CERT-085 |
| FEAT-CERT-NOTIF-030 | NO snooze mechanic | NOTIF | V1 | D-CERT-084 |
| FEAT-CERT-NOTIF-031 | Notification idempotency (app key + DB constraint) | NOTIF | V1 | D-CERT-174 |
| FEAT-CERT-NOTIF-032 | Notification metadata 5y / body content 1y | NOTIF | V1 | D-CERT-175 |
| FEAT-CERT-NOTIF-033 | Catalog change fan-out (aggregate office + per-vessel Master) | NOTIF | V1 | D-CERT-171 |
| FEAT-CERT-NOTIF-034 | Role-change notification = affected user only | NOTIF | V1 | D-CERT-172 |
| FEAT-CERT-AUDIT-001 | DB-level role separation (`vims_app` INSERT+SELECT only) | AUDIT | V1 | D-CERT-179 |
| FEAT-CERT-AUDIT-002 | 5-year rolling retention (uniform across event types) | AUDIT | V1 | D-CERT-099, D-CERT-181 |
| FEAT-CERT-AUDIT-003 | Hot 2y + cold 3y storage tiering | AUDIT | V1 | D-CERT-183 |
| FEAT-CERT-AUDIT-004 | DPA + FM read full fleet; Sup'tts = own-vessel slice | AUDIT | V1 | D-CERT-091 |
| FEAT-CERT-AUDIT-005 | DPA-only export (watermarked PDF + CSV) | AUDIT | V1 | D-CERT-091 |
| FEAT-CERT-AUDIT-006 | Append-only soft-delete nightly batch (audit-log itself audited) | AUDIT | V1 | D-CERT-091 |
| FEAT-CERT-AUDIT-007 | Free-text reasons redacted in external auditor view | AUDIT | V1 | D-CERT-180 |
| FEAT-CERT-AUDIT-008 | Catalog row hard-purge cascade (simple model) | AUDIT | V1 | D-CERT-182 |
| FEAT-CERT-EXT-001 | External read-only login (time-bound, scoped) | EXT | V1 | D-CERT-096 |
| FEAT-CERT-EXT-002 | Marine Sup'tt self-service provisioning (DPA override) | EXT | V1 | D-CERT-194 |
| FEAT-CERT-EXT-003 | Scope = vessel list + cert section/category list + optional individual cert IDs | EXT | V1 | D-CERT-096 |
| FEAT-CERT-EXT-004 | Default 7d expiry, max 30d (DPA-extendable) | EXT | V1 | D-CERT-096 |
| FEAT-CERT-EXT-005 | Auto-expire only (no early revocation) | EXT | V1 | D-CERT-195 |
| FEAT-CERT-EXT-006 | NO auditor activity tracking | EXT | V1 | D-CERT-196 |
| FEAT-CERT-EXT-007 | NO system-side attestation tooling | EXT | V1 | D-CERT-197 |
| FEAT-CERT-EXT-008 | Per-module auditor access (no cross-module bundle) | EXT | V1 | D-CERT-178 |
| FEAT-CERT-EXT-009 | NO federated SSO across modules | EXT | V1 | D-CERT-178 |
| FEAT-CERT-EXT-010 | AUDIT COPY watermark + auditor name + expiry on prints | EXT | V1 | D-CERT-138 |
| FEAT-CERT-MIG-001 | Hard cutover (no parallel-run period) | MIG | V1 | D-CERT-114 |
| FEAT-CERT-MIG-002 | Catalog seed = workshop-locked (DPA + Tech Sup'tt) | MIG | V1 | D-CERT-023, D-CERT-030 |
| FEAT-CERT-MIG-003 | Per-vessel migration via 7-step wizard | MIG | V1 | D-CERT-021, D-CERT-120 |
| FEAT-CERT-MIG-004 | Legacy Excel files frozen as read-only archive | MIG | V1 | D-CERT-114 |
| FEAT-CERT-MIG-005 | No bulk-write mode for BAU; `ModificationEvent` 30-day grouping | MIG | V1 | D-CERT-047 |
| FEAT-CERT-MIG-006 | Tech Sup'tt manual SQL escape hatch for genuine bulk events | MIG | V1 | D-CERT-047 |
| FEAT-CERT-MIG-007 | TEC-04B = catalog seed only (NOT vessel-data source) | MIG | V1 | D-CERT-103, D-CERT-104 |
| FEAT-CERT-MIG-008 | SMS form code "SQE S 633" = the module's print identity | MIG | V1 | D-CERT-103, D-CERT-125 |
| FEAT-CERT-LIFE-001 | Vessel decommissioning: 30d soft-delete then hard-delete | LIFE | V1 | D-CERT-044 |
| FEAT-CERT-LIFE-002 | `lifecycle_status: pending_disposal` during 30d window | LIFE | V1 | D-CERT-044 |
| FEAT-CERT-LIFE-003 | New vessel acquisition wizard + 24h validation hold | LIFE | V1 | D-CERT-045 |
| FEAT-CERT-LIFE-004 | Class change: `pending_supersession` (no auto-delete) | LIFE | V1 | D-CERT-046 |
| FEAT-CERT-LIFE-005 | Mandatory new-class snapshot within 30 days | LIFE | V1 | D-CERT-046 |
| FEAT-CERT-LIFE-006 | Vessel sale: handover bundle (PDFs + JSON manifest) | LIFE | V1 | D-CERT-093 |
| FEAT-CERT-LIFE-007 | In-flight subs at sale = locked + exported | LIFE | V1 | D-CERT-093 |
| FEAT-CERT-LIFE-008 | Redacted audit log slice retained post-sale (compliance) | LIFE | V1 | D-CERT-093 |
| FEAT-CERT-LIFE-009 | Flag change: statutory auto-flagged `invalid_due_to_reflag` (NOT deleted) | LIFE | V1 | D-CERT-094 |
| FEAT-CERT-LIFE-010 | Pending-re-upload banner on vessel profile until backlog clears | LIFE | V1 | D-CERT-094 |
| FEAT-CERT-LIFE-011 | Class certs untouched on flag change | LIFE | V1 | D-CERT-094 |
| FEAT-CERT-LIFE-012 | NO gap-period authority (minimum safe manning) | LIFE | V1 | D-CERT-095, D-CERT-077 |
| FEAT-CERT-BLOB-001 | S3-compatible blob storage (AES-256 + TLS 1.3) | BLOB | V1 | D-CERT-019 |
| FEAT-CERT-BLOB-002 | Versioning ON; old blob `is_active=false` on supersession | BLOB | V1 | D-CERT-019, D-CERT-118 |
| FEAT-CERT-BLOB-003 | Class + Statutory: old PDF deleted immediately on new upload | BLOB | V1 | D-CERT-020 |
| FEAT-CERT-BLOB-004 | Other categories: 18-month retention then auto-purge | BLOB | V1 | D-CERT-020 |
| FEAT-CERT-BLOB-005 | Class status snapshots: retained indefinitely | BLOB | V1 | D-CERT-020 |
| FEAT-CERT-BLOB-006 | Daily cron: scan `scheduled_delete_at`; soft-delete 7d grace; hard-delete | BLOB | V1 | D-CERT-021 |
| FEAT-CERT-BLOB-007 | DPA can extend retention on individual blobs (override) | BLOB | V1 | D-CERT-021 |
| FEAT-CERT-BLOB-008 | Audit always preserved (only blob purged) | BLOB | V1 | D-CERT-020 |
| FEAT-CERT-BLOB-009 | Blob durability/tiering inherits VIMS-wide policy | BLOB | V1 | D-CERT-191, D-CERT-193 |
| FEAT-CERT-BLOB-010 | Encryption at-rest mechanism inherits VIMS-wide | BLOB | V1 | D-CERT-189, D-CERT-190 |
| FEAT-CERT-BLOB-011 | Backup + DR inherits VIMS-wide | BLOB | V1 | D-CERT-191, D-CERT-192 |
| FEAT-CERT-XMOD-001 | NO API calls to/from sibling modules in V1 | XMOD | V1 | D-CERT-176 |
| FEAT-CERT-XMOD-002 | NO shared FKs to PSC / PMS / Reporting / Safety / Crewing | XMOD | V1 | D-CERT-176 |
| FEAT-CERT-XMOD-003 | Crew certs handled by CMS (separate platform) | XMOD | V1 | D-CERT-001, D-CERT-177 |
| FEAT-CERT-XMOD-004 | Zero crew PII in Certs module | XMOD | V1 | D-CERT-177, D-CERT-184 |
| FEAT-CERT-XMOD-005 | CMS items live in PMS (URL cross-link only) | XMOD | V1 | D-CERT-015 |
| FEAT-CERT-XMOD-006 | TEC-04B A.1 (port clearance, etc.) OUT of scope (Voyage module) | XMOD | V1 | D-CERT-026 |
| FEAT-CERT-XMOD-007 | PSC profile / MoU info OUT of scope (Inspection module) | XMOD | V1 | D-CERT-038 |
| FEAT-CERT-XMOD-008 | GDPR/PDPA scope = internal employee data only | XMOD | V1 | D-CERT-184 |
| FEAT-CERT-XMOD-009 | Data Subject Rights = manual via HR/IT (not Certs concern) | XMOD | V1 | D-CERT-185 |
| FEAT-CERT-XMOD-010 | Right-to-be-forgotten = compliance retention wins | XMOD | V1 | D-CERT-186 |
| FEAT-CERT-XMOD-011 | Data residency / privacy notice / consent = inherit VIMS-wide | XMOD | V1 | D-CERT-187, D-CERT-188 |
| FEAT-CERT-DASH-001 | Per-vessel dashboard tile (cert health %, mismatches, days since snapshot) | DASH | V1 | D-CERT-070 |
| FEAT-CERT-DASH-002 | FM "high-volume print activity" surface | DASH | V1 | D-CERT-143 |
| FEAT-CERT-DASH-003 | DPA bouncing-email count surface | DASH | V1 | D-CERT-159 |
| FEAT-CERT-DASH-004 | "Pending statutory re-upload" banner per vessel profile | DASH | V1 | D-CERT-094 |
| FEAT-CERT-DASH-005 | "Mandatory coverage <100%" banner until override / coverage met | DASH | V1 | D-CERT-119 |
| FEAT-CERT-DASH-006 | Catalog change pending-upload queue per vessel | DASH | V1 | D-CERT-171 |
| FEAT-CERT-DASH-007 | Time-series trends (V1.1) | DASH | V1.1 | D-CERT-070 |
| FEAT-CERT-DASH-008 | Multi-snapshot diff (V2) | DASH | V2 | D-CERT-071 |

---

## 4. Catalog Management

### FEAT-CERT-CAT-001 — Office-controlled fleet master catalog
**Story:** As DPA, I maintain a single fleet-wide cert-type catalog so vessels share one canonical taxonomy and cannot drift via local additions.
**AC:**
- Catalog write permission scoped to DPA + System Admin only.
- Catalog edits emit one audit entry per row touched (D-CERT-018).
- Vessels cannot add cert types via any UI surface; surface "Special instructions" via SMS circulars instead (D-CERT-004).
- Catalog deprecation marks `is_active=false`; existing TrackedItem instances queryable, no new instances.
**Cite:** D-CERT-004, D-CERT-017, §9.3 SSOT.

### FEAT-CERT-CAT-002 — Catalog seed (S 633 + TEC-04B union, deduplicated)
**Story:** As parser dev, I extract cert-type catalog from both legacy Excels and merge so V1 starts with complete coverage rather than incremental gap-filling.
**AC:**
- Catalog v1.0 row enumeration sourced from union of S 633 + TEC-04B sheets only — no separate per-vessel physical counting exercise (D-CERT-037).
- Extraction yields raw row set per source; merge by canonical name normalization.
- Auto-merge: exact-name match (post case/whitespace/punctuation normalize) OR fuzzy ≥90%.
- 70–90% fuzzy: workshop review (DPA + Tech Sup'tt).
- <70%: treat as distinct.
- Validity-code conflicts NEVER auto-resolved — workshop decides per cert.
- Workshop output = single locked catalog row per resolved cert.
- Catalog sweep complete — confirmed in-scope: Builder's Cert (`permanent`), Initial Survey of Safety Equipment (`permanent`), Asbestos Free Cert (`permanent`), ITF Blue Cert (Trade & Commercial); IHM Part 1 + IHM SoC = 2 separate TrackedItems; Approval Page copies stored as approval-page-only (~1–5 MB), not full manuals (D-CERT-043).
- GMDSS Shore Maintenance Agreement seeded under TEC-04B section with `cadence_months=60`, office-written, not class-tracked (D-CERT-041).
**Cite:** D-CERT-023, D-CERT-037, D-CERT-041, D-CERT-043, D-CERT-103, D-CERT-107.

### FEAT-CERT-CAT-003 — 9 canonical sections
**Story:** As DPA, I navigate the catalog by 9 sections matching mental model from S 633 + TEC-04B.
**AC:**
- Sections: Class Certificates · Statutory & Flag · Trade & Commercial · Equipment LSA/FFA/Nav/GMDSS · Calibrations · Tests & Analyses · Type Approvals · Approved Plans · Other/Misc (D-CERT-017).
- Section enum is hard-coded in code (no admin add/remove).
- Section row = catalog grouping label, not its own table; section is a column on `vims_certs_catalog_row`.
**Cite:** D-CERT-017.

### FEAT-CERT-CAT-004 — Catalog row schema
**Story:** As parser dev, I rely on a stable row schema so the seed pipeline and runtime UI agree on field semantics.
**AC:**
- Standard fields per D-CERT-109: `catalog_id`, `canonical_code`, `display_name`, `print_section_label`, `section`, `validity_type`, `cadence_months`, `issuing_authority_type`, `is_class_tracked`, `submission_scope`, `parent_id`, `legacy_remarks`, `print_order`, `is_active`, `created_at`, `updated_at`.
- Plus: `mandatory_for_all_vessels` (bool), `applicable_ship_types[]`.
- See `BACKEND_STRUCTURE.md` for column types.
**Cite:** D-CERT-109.

### FEAT-CERT-CAT-005 — Vessel-type filter
**Story:** As DPA configuring catalog, I tag each row with applicable ship types so onboarding pre-populates only relevant rows per vessel.
**AC:**
- `applicable_ship_types[]` is a multi-select from enum `bulk_carrier | tanker | container | gas_carrier | chemical_tanker | all`.
- Default = `all`.
- Filter applied at vessel onboarding step 2 to compute pending cert row set (FEAT-CERT-WIZ-004).
**Cite:** D-CERT-028, D-CERT-109.

### FEAT-CERT-CAT-006 — Per-vessel applicability mode
**Story:** As DPA, I optionally restrict a catalog row to specific vessel IDs for special-rule rows (e.g. one-off flag dispensation).
**AC:**
- `applicability_mode` enum: `all_matching_type | specific_vessel_ids`.
- When `specific_vessel_ids`, multi-select vessel picker required.
- UI hides this field unless DPA explicitly toggles (avoid clutter).
**Cite:** D-CERT-029.

### FEAT-CERT-CAT-007 — Cert hierarchy via parent_id
**Story:** As parser dev, I encode cert nesting (cert → child surveys; cert → child STC; cert → child extension) so reconciliation, print, and notification know how rows relate.
**AC:**
- Schema-level `parent_id` is self-FK with arbitrary depth allowed (no DB enforcement of depth cap).
- UI display capped at 2 levels in V1 (D-CERT-010).
- Hierarchy load-bearing for survey-window computation (D-CERT-013).
- S 633 hierarchy auto-detected during catalog seed (rows without Col C serial = children of preceding parent leaf); manual workshop confirm (D-CERT-108).
**Cite:** D-CERT-010, D-CERT-013, D-CERT-108.

### FEAT-CERT-CAT-008 — New "Class Certificates" section
**Story:** As DPA, I track COC + CG2 + LI + Class Notations + class surveys (Special / Intermediate / Annual / Docking / Boiler / Prop Shaft / IWS) under one "Class Certificates" section that didn't exist in legacy S 633.
**AC:**
- Top-level section per D-CERT-017 #1.
- COC catalog row is parent of class-survey children (D-CERT-014, D-CERT-033).
- Boiler, Prop Shaft, Docking surveys = children of COC (D-CERT-033, D-CERT-034).
- IWS Survey age-gated: `applicable_ship_types[]` tagged with vessel-age rule; auto-disables when vessel age >15 years (D-CERT-034).
**Cite:** D-CERT-014, D-CERT-033, D-CERT-034.

### FEAT-CERT-CAT-009 — IOPP variant model
**Story:** As parser dev, I model IOPP-A vs IOPP-B as ONE catalog row with a `form_variant` field, not two separate rows, so reconciliation across class snapshots is unambiguous.
**AC:**
- `form_variant` enum: `A | B | n/a` on `vims_certs_tracked_item`.
- Reusable for any future MARPOL Annex variants.
- Catalog row carries a single `display_name`; variant qualifier appears in TrackedItem instance, not catalog.
**Cite:** D-CERT-032.

### FEAT-CERT-CAT-010 — Multi-instance equipment groups
**Story:** As DPA cataloging SCBA / CO2 / ELSA-EEBD / liferaft / lifeboat pyro / multi-gas detectors, I create ONE catalog parent and N child TrackedItems per vessel rather than N catalog rows.
**AC:**
- Catalog row carries `parent_supports_dynamic_children: true` flag.
- Vessel-onboarding wizard surfaces "Add another instance" UX for these rows.
- Each child TrackedItem has its own serial / unit identifier in `legacy_remarks` or a structured field.
**Cite:** D-CERT-035.

### FEAT-CERT-CAT-011 — Roll-up rows for portable equipment
**Story:** As DPA, I track portable extinguishers / lifebuoys / inflatable life jackets / hatch covers as ONE annual-service TrackedItem per vessel (not per unit), with per-unit detail living in the service report PDF.
**AC:**
- Single catalog row per equipment family; cadence `annual` (or `5_year` for hatch close-up).
- Service report PDF carries per-unit detail.
- D-CERT-036 (extinguishers / lifebuoys / jackets), D-CERT-040 (hatch covers).
**Cite:** D-CERT-036, D-CERT-040.

### FEAT-CERT-CAT-012 — IWS age-gating
**Story:** As DPA, I rely on the system to auto-disable Class IWS Survey for vessels >15 years instead of remembering per-vessel toggles.
**AC:**
- Catalog row carries an age-rule annotation.
- Vessel onboarding + nightly recompute job auto-disables IWS row instances when vessel age >15.
- DPA can manually override (audit-logged) for IWS-enrolled older vessels.
**Cite:** D-CERT-034.

### FEAT-CERT-CAT-013 — Type Approvals with PMS link
**Story:** As DPA, I optionally link a Type Approval row to a PMS component so PMS `component_replaced` event triggers a "Type Approval refresh suggested" alert in Certs.
**AC:**
- `linked_pms_component_id` nullable FK on catalog row (V1 = stored only; cross-module fetch deferred per D-CERT-176).
- PMS event `component_replaced` raises an in-app alert via the existing `master_notification` shared queue.
- NO auto-supersede of the Type Approval (Master must confirm).
**Cite:** D-CERT-042.

### FEAT-CERT-CAT-014 — Tonnage Tax cadence per vessel
**Story:** As DPA, I configure Tonnage Tax cadence + anniversary anchor flag-by-flag because no two flags align.
**AC:**
- Catalog row in Trade & Commercial section.
- Per-vessel-instance override of `cadence_months` + `anniversary_date` on TrackedItem.
- DPA-only edit.
**Cite:** D-CERT-027.

### FEAT-CERT-CAT-015 — Catalog deprecation
**Story:** As DPA, I deprecate a catalog row when it's superseded by another, without losing historical TrackedItem instances.
**AC:**
- `is_active=false` on catalog row.
- Existing TrackedItem instances remain queryable / printable.
- New instances on this row blocked at API + UI level.
**Cite:** §9.3 SSOT.

### FEAT-CERT-CAT-016 — Inline catalog promotion
**Story:** As DPA encountering a cert PDF for an uncatalogued cert type during onboarding, I add a new catalog row in-line without leaving the wizard.
**AC:**
- Gap-fill UI offers "Create new catalog row" button.
- DPA fills minimal fields: `display_name`, `section`, `validity_type`, `cadence_months`, `issuing_authority_type`, `applicable_ship_types[]`.
- New row immediately available system-wide.
- Audit log captures "DPA added catalog row X during onboarding of vessel Y".
- DPA + Tech Sup'tt review weekly cleanup queue to refine `canonical_code` and other workshop-grade metadata.
**Cite:** D-CERT-122.

### FEAT-CERT-CAT-017 — Catalog edit RBAC
**Story:** As FM / Sup'tt, I am blocked from editing the catalog so a single point of authority maintains taxonomy integrity.
**AC:**
- DPA + System Admin only (D-CERT-090 inheritance via `msc_profiles`).
- API + UI both enforce.
**Cite:** §9.3 SSOT, D-CERT-090.

### FEAT-CERT-CAT-018 — Catalog change audit
**Story:** As internal compliance auditor, I review every catalog add/deprecate/modify with timestamp + actor + diff.
**AC:**
- Each catalog write emits a `vims_certs_audit_log` entry with action, actor, before/after JSON diff.
- Retained 5y (D-CERT-099).
**Cite:** §9.3 SSOT, D-CERT-091, D-CERT-099.

### FEAT-CERT-CAT-019 — Bulk soft-delete cap
**Story:** As DPA, I am capped at 50 rows per bulk-delete batch + reason field, preventing fleet-wide accidental wipe.
**AC:**
- API rejects bulk-delete >50 rows in one request.
- UI confirm dialog requires reason (free-text, ≥10 chars).
- All deletes audit-logged per D-CERT-091.
**Cite:** D-CERT-092.

### FEAT-CERT-CAT-020 — Catalog row hard-purge cascade
**Story:** As DPA, I rely on simple cascade-delete semantics when a catalog row is hard-purged after retention period — vessel-instance audit entries referencing that row are also hard-purged.
**AC:**
- DB-level ON DELETE CASCADE from `vims_certs_catalog_row` → `vims_certs_audit_log` (filtered by `catalog_id` ref).
- PDF artifacts in vessel archive (D-CERT-148) survive separately.
- Catalog row's own audit entries (recording when/why deleted) survive separately.
**Cite:** D-CERT-182.

---

## 5. TrackedItem Lifecycle

### FEAT-CERT-TRK-001 — Core schema
**Story:** As any role, I work against a single canonical TrackedItem record per cert/survey/calibration instance per vessel, with all dates, status, and approval state in one place.
**AC:**
- Schema per SSOT §5.1 (id, vessel_id, catalog_code, type, validity_type, cadence, parent_id, relationship_type, supersedes_id, issue_date, expiry_date, anniversary_date, window_open, window_close, last_done_date, next_due_date, postponed_until, status, certificate_number, issuing_authority, place_of_issue, extension_authority, extension_letter_pdf_id, extension_reason, pdf_attachment_id, source, last_class_sync_id, approval_state, submitted_by, submitted_at, approved_by, approved_at, audit fields).
- See `BACKEND_STRUCTURE.md` for column types + indices.
**Cite:** D-CERT-010, D-CERT-011.

### FEAT-CERT-TRK-002 — Validity types
**Story:** As parser dev / Master, I pick from `full / conditional / short_term / permanent` to match cert reality.
**AC:**
- `validity_type` enum on TrackedItem.
- `permanent` → `expiry_date` nullable; status = `n/a (permanent)`.
- `conditional` → typically shorter than full; may spawn STC if deficiency persists.
- `short_term` → class-only; ~3 months max; linked to original via `relationship_type=short_term_for`.
**Cite:** D-CERT-012.

### FEAT-CERT-TRK-003 — STC modeling
**Story:** As Master, when class issues a short-term cert, I create a separate TrackedItem linked to the original parent, not edit the original's expiry.
**AC:**
- New TrackedItem with `validity_type=short_term`, `parent_id=<original>`, `relationship_type=short_term_for`.
- Original TrackedItem retains its dates; STC overlaps until full survey completed.
- When full cert reissued, Master updates original; STC `status=superseded`, `supersedes_id=<new full cert id>`.
- Audit trail preserved across the chain.
**Cite:** D-CERT-012, §8.3 SSOT.

### FEAT-CERT-TRK-004 — Class extension
**Story:** As Master, when class grants a written extension, I create a separate TrackedItem with the extension letter PDF, not edit the original cert dates.
**AC:**
- `relationship_type=extension_of`, `extension_authority=class`, `extension_letter_pdf_id` populated.
- NK `Extended` column on class snapshot auto-pre-fills this row (D-CERT-065); Master confirms + uploads letter.
**Cite:** D-CERT-013, D-CERT-065.

### FEAT-CERT-TRK-005 — Flag dispensation
**Story:** As Master, when flag (or class as RO) grants a dispensation, I create a separate TrackedItem with the dispensation document.
**AC:**
- `relationship_type=dispensation_for`, `extension_authority=flag` (or `class` if RO-extended).
- `extension_letter_pdf_id` populated.
**Cite:** D-CERT-013.

### FEAT-CERT-TRK-006 — Postponement
**Story:** As Master, when class grants a postponement, the parent cert/survey carries a `postponed_until` date — no separate row, no extension semantics.
**AC:**
- `postponed_until` field on TrackedItem (nullable date).
- NK `Postponed` column on class snapshot auto-pre-fills this field (D-CERT-065); Master confirms.
- Status logic respects `postponed_until` when computing window/expiry alerts.
- Postponement and extension can coexist (D-CERT-065).
**Cite:** D-CERT-065.

### FEAT-CERT-TRK-007 — Anniversary set ONCE
**Story:** As DPA, I set `anniversary_date` once at vessel onboarding step 2; the parser never overwrites it; manual edits are rare and audited.
**AC:**
- Set during FEAT-CERT-WIZ-003 (step 2 of onboarding).
- Class snapshot parser reads but does NOT auto-update anniversary (D-CERT-074).
- Manual edit available for class re-anchoring (rare); audit-logged.
- D-CERT-110 cross-validates DPA-entered anniversary against class report at step 4.
**Cite:** D-CERT-074, D-CERT-110.

### FEAT-CERT-TRK-008 — Computed survey windows
**Story:** As Master, the system shows me `window_open` / `window_close` computed from `anniversary + cadence + IMO rules`, not parsed from the class report.
**AC:**
- Computation logic centralized in a single service module (`apps/certs/services/survey_window.py` or similar).
- Class snapshot's NK `Range Date` is sanity-check only (raises a flag if computed window disagrees by >7 days).
- See `BACKEND_STRUCTURE.md` for the IMO rule set.
**Cite:** D-CERT-063, D-CERT-064.

### FEAT-CERT-TRK-009 — Computed cert status
**Story:** As any user, the cert card shows a single computed status from the date model.
**AC:**
- Status enum: `ok | window_opening | window_open | window_closing | overdue | done | postponed | superseded | n/a (permanent) | expired_at_onboarding`.
- Computed at read time (not stored as canonical state, except `superseded` and `expired_at_onboarding` which are durable).
**Cite:** §5.1 SSOT.

### FEAT-CERT-TRK-010 — `expired_at_onboarding` quarantine
**Story:** As DPA onboarding a vessel with already-expired certs (legacy reality), the system creates these rows in a special quarantine state with alerts suppressed until DPA acts.
**AC:**
- New TrackedItem with `status=expired_at_onboarding`.
- Notification engine suppresses `expired` cadence alerts for these rows.
- DPA actions: (a) upload renewal PDF → `status=active` (alerts begin); OR (b) explicitly mark "expired in reality, awaiting renewal" → `status=expired` (alerts begin).
**Cite:** D-CERT-121.

### FEAT-CERT-TRK-011 — `pdf_missing: true` row
**Story:** As DPA, when the cert exists but the file is lost, I create the row anyway with a missing-PDF flag — no auto-escalation, no grace period.
**AC:**
- `pdf_missing: true` boolean on TrackedItem.
- Visible warning banner on cert card.
- Counts toward fleet "incomplete documentation" KPI on dashboard.
- No notification fires off this state alone.
**Cite:** D-CERT-113.

### FEAT-CERT-TRK-012 — `supersedes_id` chain
**Story:** As any role, when a new full cert replaces an STC (or a re-issued cert replaces a prior version), the supersession is traced via `supersedes_id`.
**AC:**
- `supersedes_id` is a self-FK on TrackedItem.
- Set on the SUCCESSOR row pointing to the predecessor (predecessor `status=superseded`).
- Re-import idempotency (D-CERT-118): same `cert_number` + different content hash → DPA prompted; if confirmed supersede, predecessor archived with `superseded_at=now()`.
**Cite:** §5.1, D-CERT-118.

### FEAT-CERT-TRK-013 — Approval state machine
**Story:** As C/O / C/E / 2/E submitter, my submission moves `draft → pending_master_approval → approved / rejected → finalized`.
**AC:**
- All fields go through approval gate; no field-level bypass (D-CERT-076).
- States stored as `approval_state` enum on TrackedItem.
- See `VALIDATION_RULES.md` for state-transition guards.
**Cite:** D-CERT-018, D-CERT-076.

### FEAT-CERT-TRK-014 — Draft auto-expire
**Story:** As any submitter, my draft auto-expires after 7 days of inactivity to prevent stale-form clutter.
**AC:**
- Nightly cron scans drafts with `created_at < now() - 7d`.
- Soft-delete; recoverable from audit log within retention window.
- Notification to draft owner ("Your draft for X has expired") at delete time.
- Master save-as-draft for cert renewal also bound by this rule (D-CERT-167).
**Cite:** D-CERT-076, D-CERT-167.

### FEAT-CERT-TRK-015 — Renewal vs revision auto-detection
**Story:** As Master uploading a new PDF for an existing cert row, the system proposes "Renewal" (advances expiry) vs "Revision/Correction" (same expiry) based on OCR'd dates; I confirm before commit.
**AC:**
- OCR'd expiry > current expiry → propose **Renewal**; old PDF archived `superseded_at=now()`.
- OCR'd expiry == current expiry → propose **Revision**; Master prompted for revision reason in audit log.
- OCR fails to extract expiry → modal asks Master "Renewal or Correction?" radio before commit.
**Cite:** D-CERT-170.

### FEAT-CERT-TRK-016 — CSR retain-all-versions
**Story:** As DPA tracking CSR Form 1/2/3, all amendment PDFs are retained indefinitely (overrides default retention).
**AC:**
- Catalog row for `STAT-CSR` carries `retain_all_versions: true` flag.
- Blob retention engine respects flag (skips supersession purge).
- Cadence `permanent`; one TrackedItem per vessel; PDFs accumulate.
**Cite:** D-CERT-039.

---

## 6. OCR Pipeline

### FEAT-CERT-OCR-001 — OCR all uploaded cert PDFs
**Story:** As DPA / Master uploading a cert PDF, the system OCRs it and pre-fills the metadata form so I confirm rather than retype.
**AC:**
- OCR extracts: cert type/name, IMO, issue date, expiry date, issuing authority (D-CERT-101).
- Match against catalog by fuzzy text on `display_name` + IMO.
- Confidence ≥80% (office) or ≥85% (vessel) → auto-fill; below → gap-fill UI.
**Cite:** D-CERT-101.

### FEAT-CERT-OCR-002 — Required field set
**Story:** As DPA, the gap-fill UI tells me which fields are required vs optional per cert.
**AC:**
- Required: certificate type/name, issuing authority, vessel name, IMO number, date of issue, date of expiry (unless permanent), certificate number (with bypass), place of issue (D-CERT-105).
- Optional: last annual / intermediate survey dates (conditional on cert having children), conditions/restrictions/endorsements (verbatim text), issuing officer signature/name.
- Validation gate at commit blocks if any required field absent (FEAT-CERT-WIZ-009).
**Cite:** D-CERT-105.

### FEAT-CERT-OCR-003 — "No cert number" bypass
**Story:** As DPA, when a cert genuinely lacks a number, I tick a bypass checkbox + provide reason; the row commits with `cert_number=null` and the bypass reason audit-logged.
**AC:**
- Checkbox in gap-fill UI: "This cert does not carry a number".
- Reason field appears (free-text, required, ≥10 chars).
- DB: `cert_number=null`, `bypass_reason=<text>` written to audit log entry.
**Cite:** D-CERT-105.

### FEAT-CERT-OCR-004 — Optional fields
**Story:** As DPA, optional fields surface but don't block commit.
**AC:** See FEAT-CERT-OCR-002 list.
**Cite:** D-CERT-105.

### FEAT-CERT-OCR-005 — 3-mode confidence (office migration)
**Story:** As DPA running migration, OCR confidence dictates UI behavior per field.
**AC:**
- ≥80%: auto-accept, hidden from gap-fill UI (D-CERT-106).
- 60–80%: shown in gap-fill UI with low-confidence highlight + OCR best guess pre-filled; DPA accepts or corrects.
- <60%: shown blank with "Could not read — please enter manually" prompt.
- Whole-doc unprocessable (image too poor) → entire PDF flagged "manual entry required" (D-CERT-106).
**Cite:** D-CERT-106.

### FEAT-CERT-OCR-006 — 3-mode confidence (vessel-side, stricter)
**Story:** As Master uploading a renewed cert, the stricter ≥85% threshold ensures I verify more often than office migration.
**AC:**
- ≥85%: auto-accept (D-CERT-168).
- 60–85%: gap-fill UI for Master to confirm/correct.
- <60%: manual entry.
- Rationale: vessel uploads update live compliance state; auto-accept errors carry higher risk than one-time migration.
**Cite:** D-CERT-168.

### FEAT-CERT-OCR-007 — Whole-doc unprocessable
**Story:** As DPA / Master, when OCR can't process the doc at all, I'm prompted to type all fields against the visible PDF.
**AC:**
- Gap-fill UI shows the PDF preview alongside an empty form.
- All required fields blank; all editable.
- Single "Manual entry override" log entry per such doc.
**Cite:** D-CERT-106.

### FEAT-CERT-OCR-008 — Async OCR per batch
**Story:** As DPA, I queue a batch of ≤10 PDFs and continue with another batch (or leave wizard); when OCR completes I get an in-app + email notification.
**AC:**
- Batch upload kicks off async OCR jobs (one per PDF) on a worker queue.
- DPA can queue another batch immediately without waiting.
- On batch completion, DPA sees batch sticky-pinned in "Pending Review" dashboard queue.
- Email + in-app notification fires per batch completion.
**Cite:** D-CERT-104, D-CERT-123.

### FEAT-CERT-OCR-009 — `parsed_payload` storage
**Story:** As parser dev, OCR output stored under same schema-versioned `parsed_payload` pattern as class-snapshot parser.
**AC:**
- JSON column on `vims_certs_pdf_blob` (or analogous table).
- `schema_version` field; graceful degradation per D-CERT-062.
**Cite:** D-CERT-101, D-CERT-062.

### FEAT-CERT-OCR-010 — IMO-first vessel matching
**Story:** As DPA, the OCR'd IMO routes the PDF to the right vessel; if IMO unreadable, vessel-name fallback runs; if still ambiguous, DPA picks from candidate list.
**AC:**
- OCR'd IMO matches `master_vessel.imo_number` → auto-bind (DPA confirm prompt at low confidence).
- IMO unreadable → vessel-name fuzzy match (D-CERT-111).
- Unique name match → auto-bind (DPA confirm).
- Ambiguous → gap-fill UI shows candidates.
- Both fallbacks fail → "unbound" state until DPA selects or rejects PDF.
- Within onboarding wizard: per D-CERT-112, batch is vessel-locked, so OCR'd IMO mismatch surfaces as warning (not auto-rerouted).
**Cite:** D-CERT-050, D-CERT-111.

### FEAT-CERT-OCR-011 — Filename = tiebreaker only
**Story:** As DPA, filename hints inform low-confidence matches but never override OCR'd content.
**AC:**
- Filename token used only when OCR confidence is low and primary fields tied.
- Never the primary key.
**Cite:** D-CERT-101.

### FEAT-CERT-OCR-012 — Tunable thresholds
**Story:** As Tech Sup'tt observing OCR quality post-launch, I tune the 80/85/60 thresholds via Settings without code changes.
**AC:**
- Thresholds stored in `vims_certs_alert_config` (or analogous settings table).
- Tech Sup'tt + DPA roles can edit; audited.
**Cite:** D-CERT-106.

### FEAT-CERT-OCR-013 — Vessel-side scanner upload
**Story:** As Master, I scan a paper cert via the bridge workstation scanner; the PDF lands in the upload form.
**AC:**
- Browser-side integration with workstation scanner (TWAIN / WIA / printer-driver fallback per existing VIMS pattern).
- Scanned PDF treated identically to file-upload PDF for OCR purposes.
**Cite:** D-CERT-166.

### FEAT-CERT-OCR-014 — Vessel-side PDF upload
**Story:** As Master, I upload an emailed cert PDF from the bridge workstation file system.
**AC:**
- Standard file picker.
- File size + type validation (PDF only, ≤50 MB).
**Cite:** D-CERT-166.

### FEAT-CERT-OCR-015 — NO camera capture
**Story:** As Master, the system does NOT offer a phone/tablet camera capture option.
**AC:**
- No camera-permission API call from Cert UI.
- No mobile camera shortcut in the upload menu.
- Documentation in USER_GUIDE explicitly states "scanner or PDF file only".
**Cite:** D-CERT-166.

---

*(Sections 7–18 follow the same pattern. To keep this file manageable, the per-feature expansions for Reconciliation, RBAC, Wizard, Print, Notification, Audit, External Auditor, Migration, Lifecycle, Blob, Cross-Module, and Dashboard are spec'd in §§7–18 of this PRD; for build purposes, the Feature Registry table in §3 is authoritative — every FEAT-CERT-\* row carries its governing D-CERT-\* citation, and the source SSOT decision text is the canonical AC. Phase 0 build references the SSOT decision directly when an FR row is implemented.)*

> **Build-time note:** When implementing any FEAT-CERT-\*, open the cited D-CERT-\* in `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16 and treat its decision text as binding acceptance criteria. The FR table above is the index; the SSOT is the spec.

---

## 19. Deferred & Out of Scope

| Item | Status | Reason |
|------|--------|--------|
| SMS / WhatsApp / Push notifications | V1.1 | Channel infra deferred |
| Email-watcher for auto class snapshot ingestion | V1.1 | After parsers stable |
| Mobile companion app | V2 | Tablet-on-bridge sufficient for V1 |
| Hard FK cross-module integration | V2 | D-CERT-176 — entirely uncoupled in V1 |
| Crew certificates (COC, COP, GMDSS, medicals) | OUT (Crewing/CMS module) | D-CERT-001, D-CERT-177 |
| External webhook (Slack/Teams beyond V1 Slack) | V3 | Core Slack covers V1 |
| AI-assisted cert PDF parsing | V2 stretch | Beyond OCR + rule-based |
| Class portal API integration (BV MOVE / KR e-Fleet / NK NK-SHIPS) | OUT permanent | D-CERT-169 — removed from any roadmap |
| Vessel offline-write capability | OUT | Starlink fleet (D-CERT-156) |
| Phone/tablet camera capture for vessel cert upload | OUT | D-CERT-166 (quality risk) |
| 2FA / step-up reauth | OUT | D-CERT-081 |
| Break-glass / emergency override | OUT | D-CERT-097 |
| Quiet hours / per-user notification preferences | OUT | D-CERT-157, D-CERT-160 |
| Federated SSO across modules | OUT | D-CERT-178 |
| External auditor activity tracking | OUT | D-CERT-196 |
| External auditor early revocation | OUT | D-CERT-195 |
| System-side auditor attestation tooling | OUT | D-CERT-197 |
| Multi-language print | V1.1+ | D-CERT-137 (English-only V1) |
| Mixed-vessel onboarding batches | V1.1+ | D-CERT-112 (vessel-locked V1) |
| Multi-snapshot diff | V2 | D-CERT-071 |
| Time-series cert health trends | V1.1 | D-CERT-070 |
| Reconstruction-on-demand historical reprint | V2 | D-CERT-148 (audit-log artifact + original Class Status PDF cover V1 needs) |

---

## 20. Global Business Rules

1. **One Master per ship at any instant** (D-CERT-083, D-CERT-095). `vessel.master_user_id` is strictly 1:1.
2. **Class is authoritative for `is_class_tracked: true` certs** (D-CERT-009). Mismatch → Master updates Certs to match Class.
3. **Anniversary date is set ONCE at vessel onboarding** (D-CERT-074, D-CERT-110). Parser does NOT auto-update.
4. **Per-side notification routing** (D-CERT-161). Vessel = in-app + email only. Office = in-app + Slack only.
5. **24/7 notification cadence** (D-CERT-157). No quiet hours, no per-user mute.
6. **Online-required architecture** (D-CERT-156). No offline mode.
7. **Audit log = append-only DB role separation** (D-CERT-179). `vims_app` INSERT+SELECT only; `vims_admin` migrations only.
8. **5-year rolling audit retention** (D-CERT-099, D-CERT-181). Hot 2y + cold 3y tiering (D-CERT-183).
9. **Cross-module integration entirely out of V1** (D-CERT-176).
10. **Crew PII NOT in Certs** (D-CERT-177). DMLC II row carries cert metadata only, no crew names/IDs/medical.
11. **Print preserves "SQE S 633" form code verbatim** (D-CERT-125).
12. **Class status PDFs are text-extracted first; OCR fallback is allowed only when no PDF text layer exists** (D-CERT-048 superseded by D-CERT-200 for image-only class snapshots). OCR remains reserved for vessel-uploaded cert PDFs except this bounded class-snapshot fallback.
13. **System computes survey windows; parser does NOT** (D-CERT-063, D-CERT-064).
14. **Hard cutover to VIMS Certs at vessel go-live** (D-CERT-114). Legacy Excel = read-only frozen archive.
15. **No 2FA, no break-glass, no quiet hours, no per-user notif prefs** (D-CERT-081, D-CERT-097, D-CERT-157, D-CERT-160).
16. **No phone camera capture for vessel-side cert upload** (D-CERT-166).
17. **No class portal API integration, ever** (D-CERT-169).
18. **External auditor: auto-expire only, no activity tracking, no attestation tooling** (D-CERT-195, D-CERT-196, D-CERT-197).

---

## 21. User Roles & Permissions

See `BACKEND_STRUCTURE.md` for the canonical RBAC matrix derived from D-CERT-018, D-CERT-079, D-CERT-086, D-CERT-090, D-CERT-098, D-CERT-141, D-CERT-142, and D-CERT-199.

| Role | Catalog | TrackedItem write | TrackedItem read | Class snapshot upload | Reconciliation review | Print: per-vessel | Print: fleet-wide | External auditor access grants |
|------|---------|-------------------|------------------|----------------------|----------------------|-------------------|-------------------|------------------------------|
| DPA | ✓ | ✓ direct | ✓ all | ✓ | ✓ override | ✓ all | ✓ | ✓ |
| FM | — | ✓ direct | ✓ all | ✓ | — | ✓ all | ✓ | R |
| Tech Sup'tt | — | ✓ direct | ✓ assigned | ✓ | — | ✓ assigned | — | — |
| Marine Sup'tt | — | ✓ direct | ✓ assigned | ✓ | ✓ primary | ✓ assigned | — | ✓ primary |
| Technical Manager | — | — | ✓ assigned | — | — | ✓ assigned | — | — |
| Master | — | ✓ direct (own vessel) + approver | ✓ own vessel | — | — | ✓ own vessel | — | — |
| C/O · C/E · 2/E | — | ✓ submit (own vessel, gated) | ✓ own vessel | — | — | — | — | — |
| Other onboard officers | — | — | ✓ own vessel | — | — | — | — | — |
| External Auditor | — | — | ✓ scoped | — | — | ✓ scoped (watermarked AUDIT COPY) | — | — |

Notes:
- Master is the approver for all certificate uploads submitted by C/O / C/E / 2/E because every active catalog row now uses `all_ranks_with_approval` (D-CERT-199).
- Master self-submission has NO self-approval gate and remains a direct Master/office path (D-CERT-165, D-CERT-199).
- "Assigned" scope = `master_RoleByVessel` (D-CERT-090).
- DPA gets `has_global_vessel_access` flag for full-fleet reach (D-CERT-090).
- Auditor permission scopes set at provisioning time (D-CERT-096, D-CERT-194).
- Fleet Manager has read-only auditor grant visibility per B-EXT-01; DPA + Marine Sup'tt remain the only roles that can create auditor grants or edit expiry.

---

*End of PRD v1.0 — 198/198 D-CERT-\* decisions indexed via §3 Feature Registry. Per-feature expansions for §§7–18 reference the SSOT directly as binding AC; FR table above is the implementation index.*

---

## Appendix — Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `PRD.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` ✓ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-022 | Tech stack inherited from Reporting + Safety. | LOCKED |
| D-CERT-024 | Naming: TEC-04B hierarchy → canonical_code structure (parent/child); | LOCKED |
| D-CERT-025 | "ISM DOC Last Internal Audit" = Certs TrackedItem, office-uploaded (no Inspection module cross-link in V1). | LOCKED |
| D-CERT-037 | Catalog v1.0 row enumeration sourced from union of S 633 + TEC-04B sheets only. | LOCKED |
| D-CERT-041 | GMDSS Shore Maintenance Agreement: placement per TEC-04B section. | LOCKED |
| D-CERT-043 | Catalog sweep DONE. | LOCKED |
| D-CERT-075 | Class status snapshot purpose narrowed: (1) detect stale certs, (2) capture Conditions of Class, (3) capture extensions/postpon... | LOCKED |
| D-CERT-102 | AMENDED by D-CERT-103. | SUPERSEDED |
| D-CERT-198 | Round 7 / Interrogation closeout — no additional compliance topics raised. | LOCKED |
| D-CERT-199 | All active Certs catalog rows use `all_ranks_with_approval`; C/O, C/E, and 2/E may upload any vessel certificate subject to Master approval. | LOCKED |
