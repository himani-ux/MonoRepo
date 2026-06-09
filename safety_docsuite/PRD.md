# VIMS Safety Module — Product Requirements Document (PRD)

> **Version:** 1.0
> **Last Updated:** 2026-06-09
> **Status:** Requirements Locked — Ready for Build
> **Decision Owner:** Prince (Product Owner)
> **Source:** `VIMS-SAFETY-MODULE-SSOT.md` (§2B M-SCAT, §2C SOI, §3 Incident, §4 Near Miss, §5 SCM, §6 Decisions Log) + `VIMS-SAFETY-GAP-ANALYSIS.md` (Session 5 A–M + DESIGN + R01–R23)
> **Inherits pattern from:** `VIMS-Reporting-Module/PRD.md`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Glossary](#2-glossary)
3. [Feature Registry](#3-feature-registry)
4. [Incident Module — 9 Phases (FEAT-SAF-INC-*)](#4-incident-module)
5. [Near Miss Module (FEAT-SAF-NM-*)](#5-near-miss-module)
6. [Safety Committee Meeting — Regular + Ad-Hoc (FEAT-SAF-SCM-*)](#6-safety-committee-meeting)
7. [Safety Officer Inspection — 13 Areas, Paper-First (FEAT-SAF-SOI-*)](#7-safety-officer-inspection)
8. [Cross-Module Contracts (FEAT-SAF-XMOD-*)](#8-cross-module-contracts)
9. [PDF Generation (FEAT-SAF-PDF-*)](#9-pdf-generation)
10. [Audit, Signatures, Field History (FEAT-SAF-AUDIT-*)](#10-audit-signatures-field-history)
11. [Dashboards & Analytics (FEAT-SAF-DASH-*)](#11-dashboards--analytics)
12. [RBAC Specifics (FEAT-SAF-RBAC-*)](#12-rbac-specifics)
13. [Deferred & Out of Scope (V2)](#13-deferred--out-of-scope-v2)
14. [Global Business Rules](#14-global-business-rules)
15. [User Roles & Permissions](#15-user-roles--permissions)

---

## 1. Overview

**Project:** VIMS Safety Module — migration of the legacy eMarineSoft safety management surface (incidents, near misses, safety meetings) to the VIMS platform, expanded with Safety Officer Inspection (SOI) as the 4th V1 sub-feature and the DNV M-SCAT investigation framework as the canonical RCA taxonomy.

**V1 scope (4 sub-features):**
- **Incident Reporting** — 9-phase workflow (Intake → Notifications → Evidence → Sequence → Analysis → Recommendations → Actions → Verification → Closure), IMO SMC/MC/MI classifier + internal risk band GREEN/YELLOW/RED, ALARP gate, causal layering Immediate/Intermediate/Root over M-SCAT, 8 bias guards, Chain-of-Custody, 10-section PDF.
- **Near Miss Reporting** — reporter details visible to Master and authorized users (D-GAP-J1 revised), Office Comments priority decision (LOW/MEDIUM by PIC, HIGH by DPA), no anonymous reporting concept.
- **Safety Committee Meeting (SCM)** — Regular monthly + Ad-Hoc meetings, same form, Master/CO host authority with `meeting_type` selection, aligned with KSM SSQE Manual Rev 01 Feb 2026 §9.
- **Safety Officer Inspection (SOI)** — 13 areas × 329 items (12 physical + Section 12 Cross-cutting Safety & Culture + Compressor House), paper-first no-scan (D-GAP-E4), unique-ID linkage, state pill "SOI Compliance %" (D-GAP-DESIGN-01).

**Regulatory anchors:** ISM Code (2010 amendments); SOLAS Ch IX (as amended); IMO Casualty Investigation Code — Resolution MSC.255(84); MARPOL Annex I (consolidated 2022); IMO Resolution A.884(21); IMO Res A.1075(28); MLC 2006; COSWP 2026 Ch 13; KSM SSQE Manual Rev 01 Feb 2026 §4.5, §9, §11.

**Platform context:** Safety lives as a child module in the VIMS monorepo at `apps/safety/` (Django) and `routes/safety/`, `components/safety/`, `hooks/safety/`, `stores/safety/`, `schemas/safety/` (React). Shared DB `ksm_marine_live`. Shared auth (SimpleJWT + `msc_profiles`). API under `/api/safety/`. Module tables use prefix `vims_safety_*`; reference/master data uses `master_*`.

**Identifier strategy:** Safety-owned managed records use UUID `id` as the actual database primary key and as the public API/navigation identifier. The transitional `public_id` field is not part of the final design. This does not change business reference numbers such as incident numbers, SCM numbers, SOI inspection references, checklist unique IDs, or report numbers.

**Priority tiers used in this PRD:**
- **V1** — must-ship for first release
- **V1.1** — stretch goal for initial release; scheduled but may slip one sprint
- **V2** — explicitly deferred (revisit after V1 stabilisation)

---

## 2. Glossary

| Term | Expansion |
|------|-----------|
| DPA | Designated Person Ashore (ISM Code §4) |
| FM | Fleet Manager |
| TD | Technical Director |
| HOD | Head of Department (onboard: CO, CE, or senior officer of department) |
| CO | Chief Officer |
| CE | Chief Engineer |
| SO | Safety Officer (onboard, SSQE §4.5.1 — CO by default, 2/E alternate) |
| PIC | Person-in-Charge (Vessel Superintendent, office-side owner of a vessel) |
| SCM | Safety Committee Meeting |
| SOI | Safety Officer Inspection |
| MoC | Management of Change |
| RCA | Root Cause Analysis |
| CA / PA | Corrective Action / Preventive Action |
| ALARP | As Low As Reasonably Practicable |
| SMC / MC / MI | Serious Marine Casualty / Marine Casualty / Marine Incident (IMO Casualty Investigation Code) |
| WRH | Work & Rest Hours module |
| CMS | Crew Management System module |
| PMS | Planned Maintenance System module (**decoupled from VIMS — D-GAP-I1**) |
| SSQE | Safety, Security, Quality & Environment (KSM Manual). Note: SSQE is the team label for the DPA function — no separate RBAC entry exists (D-RBAC-03). |

First-use expansions applied once; re-occurrences use the acronym.

---

## 3. Feature Registry

| ID | Feature | Domain | Priority | SSOT/Gap ref |
|----|---------|--------|----------|--------------|
| FEAT-SAF-INC-001 | Incident Phase 1 Intake + Scene Control | INC | V1 | §2B.6, D-GAP-R07, D-GAP-C1 |
| FEAT-SAF-INC-002 | IMO SMC/MC/MI Regulatory Classifier | INC | V1 | D-GAP-R08 |
| FEAT-SAF-INC-003 | Internal Risk Band GREEN/YELLOW/RED | INC | V1 | §2B.3, D-DNV-02 |
| FEAT-SAF-INC-004 | Phase 2 Notifications + Resource Allocation | INC | V1 | D-EDGE-09, D-GAP-F2 |
| FEAT-SAF-INC-005 | Phase 3 Evidence Workspace (5-Source) | INC | V1 | §2B.8, D-DNV-07 |
| FEAT-SAF-INC-006 | Evidence Matrix (Pro/Con, Confirmation-Bias Guard) | INC | V1 | §2B.8, §2B.12 |
| FEAT-SAF-INC-007 | Chain-of-Custody Tab | INC | V1 | D-GAP-R04 |
| FEAT-SAF-INC-008 | Marine Document Inventory Auto-Checklist | INC | V1 | D-GAP-R05 |
| FEAT-SAF-INC-009 | Cargo-Specific Evidence Overlay | INC | V1 | D-GAP-R10 |
| FEAT-SAF-INC-010 | Health / Fatigue Evidence Sub-Section | INC | V1 | D-GAP-R23 |
| FEAT-SAF-INC-011 | Evidence-Preservation Deadline Task List | INC | V1 | D-GAP-R06 |
| FEAT-SAF-INC-012 | Structured 4-Phase Interview Module | INC | V1 | §2B.9, D-DNV-08 |
| FEAT-SAF-INC-013 | Formal vs Informal Interview Flag | INC | V1 | D-GAP-R20 |
| FEAT-SAF-INC-014 | Witness Read-Back + Sign-Off Protocol | INC | V1 | D-GAP-R19 |
| FEAT-SAF-INC-015 | Phase 4 Facts Systemized (Multi-Tool Fact Base) | INC | V1 | §2B.11 |
| FEAT-SAF-INC-016 | Phase 5 Causal Analysis + Loop-Back Gate | INC | V1 | §2B.6, D-DNV-05, D-GAP-B3 |
| FEAT-SAF-INC-017 | M-SCAT Cause Picker (174 codes) | INC | V1 | §2B.2, D-DNV-01, D-GAP-C2 |
| FEAT-SAF-INC-018 | Causal Layering Tag (Immediate/Intermediate/Root) | INC | V1 | D-GAP-R01 |
| FEAT-SAF-INC-019 | Multiple Root Causes (no cap) | INC | V1 | D-GAP-R03 |
| FEAT-SAF-INC-020 | Multi-Tool Analysis Workspace (STEP/Fact Tree/ECF/Barrier/Change) | INC | V1 | §2B.11, D-DNV-10 |
| FEAT-SAF-INC-021 | Investigation-Depth Task Triangle | INC | V1 | D-GAP-R14 |
| FEAT-SAF-INC-022 | People/Process/Plant Interrogatory Checklist | INC | V1 | D-GAP-R16 |
| FEAT-SAF-INC-023 | Safeguard-Failure Interrogatory (6-dimension) | INC | V1 | D-GAP-R18 |
| FEAT-SAF-INC-024 | 8 Bias Guards (5 DNV + 3 Organisational Traps) | INC | V1 | §2B.12, D-DNV-11, D-GAP-R12 |
| FEAT-SAF-INC-025 | Blame-Fixation Hard Block + Override | INC | V1 | D-DNV-11 #5, D-RBAC-07 |
| FEAT-SAF-INC-026 | Human Factors — SHELL + IMO A.884(21) + Risk/Change Domain | INC | V1 | §2B.10, D-DNV-09, D-GAP-R21 |
| FEAT-SAF-INC-027 | Phase 6 Recommendations (3-Tier: Lessons/Immediate/System) | INC | V1 | §2B.7, D-DNV-06, D-GAP-R13 |
| FEAT-SAF-INC-028 | ALARP Cost-Benefit Gate on System Actions | INC | V1 | D-GAP-R02 |
| FEAT-SAF-INC-029 | Tolerable-Failure Filter (GREEN only) | INC | V1.1 | D-GAP-R11 |
| FEAT-SAF-INC-030 | Phase 7 DPA Acceptance / Report Issued | INC | V1 | §2B.6, D-PDF-01 |
| FEAT-SAF-INC-031 | Phase 8 Follow-up / Effectiveness Verification | INC | V1 | D-EDGE-06 |
| FEAT-SAF-INC-032 | Multi-Vessel Incident Linking + Duplicate Detection | INC | V1 | D-EDGE-01, D-GAP-M25, D-GAP-M07 |
| FEAT-SAF-INC-033 | Near-Miss ↔ Incident Supersede-and-Create-New | INC | V1 | D-EDGE-07 |
| FEAT-SAF-INC-034 | External-Party (Non-Crew) Injury Capture | INC | V1 | D-EDGE-02 |
| FEAT-SAF-INC-035 | Re-open Closed Incident (Band-Gated) | INC | V1 | D-EDGE-03 |
| FEAT-SAF-INC-036 | Draft Mode at Any Phase (Partial Data) | INC | V1 | D-EDGE-08 |
| FEAT-SAF-INC-037 | YELLOW-Band Deadline Auto-Pause on DPA Leave | INC | V1 | D-GAP-A1 |
| FEAT-SAF-INC-038 | PIC Retains YELLOW Ownership After Transfer | INC | V1 | D-GAP-A2 |
| FEAT-SAF-INC-039 | Self-Report Conflict Guard | INC | V1 | D-GAP-A5 |
| FEAT-SAF-INC-040 | Incident Number `{VslCode}/{YYYY}/{NNN}` with Draft Series | INC | V1 | D-GAP-C1 |
| FEAT-SAF-INC-041 | MSC-MEPC.3 Position Auto-Fill (±12h tolerance) | INC | V1 | D-DNV-12, D-GAP-M09, D-GAP-M10 |
| FEAT-SAF-NM-001 | Near Miss Creation (Any Rank) | NM | V1 | D-RBAC-11 |
| FEAT-SAF-NM-002 | Reporter Identity Masking (DPA/FM-only view) | NM | V1 | D-GAP-J1 |
| FEAT-SAF-NM-003 | Near Miss Office Comments + Priority Decision | NM | V1 | D-GAP-R22 |
| FEAT-SAF-NM-004 | Near Miss Lightweight Record Review | NM | V1 | §4.3 SSOT |
| FEAT-SAF-NM-005 | Near Miss Rate-Limit + Minimum-Detail | NM | V1 | D-GAP-M38 |
| FEAT-SAF-NM-006 | Fleet Alert within 1 Week for High-Priority Near Miss | NM | V1 | D-GAP-R22 |
| FEAT-SAF-SCM-001 | SCM Regular — Monthly Cadence | SCM | V1 | §5, D-GAP-M-ADHOC |
| FEAT-SAF-SCM-002 | SCM Ad-Hoc — Host-Triggered | SCM | V1 | D-GAP-M-ADHOC |
| FEAT-SAF-SCM-003 | 10-Section SCM Form (legacy `vw_GetSCM_Master` structure) | SCM | V1 | D-PDF-03b |
| FEAT-SAF-SCM-004 | SCM Host Creation by Master/CO, Office Comment Closure | SCM | V1 | D-RBAC-06 |
| FEAT-SAF-SCM-005 | WRH Attendance Warn-Don't-Block | SCM | V1 | D-GAP-M11, D-GAP-M26 |
| FEAT-SAF-SCM-006 | Closed-Since-Last-SCM Summary Block | SCM | V1 | D-SOI-14, D-GAP-M22 |
| FEAT-SAF-SCM-007 | SCM SOI Overdue Visibility (Warning Only) | SCM | V1 | D-GAP-M20 |
| FEAT-SAF-SCM-008 | Agenda + Action-Item Tracking | SCM | V1 | §5.4 |
| FEAT-SAF-SOI-001 | 13-Area Inspection Taxonomy | SOI | V1 | §2C.5, D-SOI-13, D-SOI-16 |
| FEAT-SAF-SOI-002 | Area-Applicability Toggle + Audit Log | SOI | V1 | D-SOI-12, D-GAP-M19 |
| FEAT-SAF-SOI-003 | Versioned Checklist Templates | SOI | V1 | D-SOI-05, D-GAP-M05 |
| FEAT-SAF-SOI-004 | Safety Officer + Alternate Assignment | SOI | V1 | D-SOI-02 |
| FEAT-SAF-SOI-005 | 90-Day Hard Ceiling + 80-Day Amber | SOI | V1 | D-SOI-04 |
| FEAT-SAF-SOI-006 | Paper-First Checklist Generation (PDF/Excel) | SOI | V1 | D-SOI-10, D-GAP-E4 |
| FEAT-SAF-SOI-007 | Idempotent Download + Reprint | SOI | V1 | D-GAP-E1 |
| FEAT-SAF-SOI-008 | Unique Checklist ID Linkage | SOI | V1 | D-GAP-E4, D-SOI-10 |
| FEAT-SAF-SOI-009 | Cross-Functional Assistant Hard Enforcement | SOI | V1 | D-SOI-08, D-GAP-I2, D-GAP-M18 |
| FEAT-SAF-SOI-010 | Up to 3 Crew Trainees per Inspection | SOI | V1 | D-SOI-09 |
| FEAT-SAF-SOI-011 | Finding Registration (No Per-Item Responses in DB) | SOI | V1 | D-SOI-10, D-GAP-E4 |
| FEAT-SAF-SOI-012 | Partial Submission (Per-Area Stamping) | SOI | V1 | D-GAP-E2 |
| FEAT-SAF-SOI-013 | Lost/Damaged Paper Recovery | SOI | V1 | D-GAP-E3 |
| FEAT-SAF-SOI-014 | Section 12 Once Per 3-Month Cycle | SOI | V1 | D-GAP-M23, D-SOI-16 |
| FEAT-SAF-SOI-015 | Finding Closure (SO → Master) | SOI | V1 | D-SOI-07, D-GAP-M21 |
| FEAT-SAF-SOI-016 | HIGH Severity Finding — Photo Required | SOI | V1 | D-GAP-M24 |
| FEAT-SAF-SOI-017 | HIGH Severity System Nudge ("Incident-Worthy?") | SOI | V1 | D-GAP-M16 |
| FEAT-SAF-SOI-018 | Life-Threat Escalation via Incident/Near Miss | SOI | V1 | D-GAP-E6 |
| FEAT-SAF-SOI-019 | Repeat-Finding Badge + Dashboard Metric | SOI | V1 | D-GAP-M17 |
| FEAT-SAF-SOI-020 | SOI → SCM Auto-Feed (Split Model) | SOI | V1 | D-SOI-14 |
| FEAT-SAF-SOI-021 | Default Finding Assignee = SO | SOI | V1 | D-GAP-E7 |
| FEAT-SAF-SOI-022 | Crew Rotation Coverage % Metric | SOI | V1 | D-SOI-09 |
| FEAT-SAF-SOI-023 | Paper-Signature Capture (SO + Assistant mandatory) | SOI | V1 | D-GAP-M15 |
| FEAT-SAF-SOI-024 | Inherit CO-Role on Rotation | SOI | V1 | D-GAP-A4 |
| FEAT-SAF-XMOD-001 | Safety ↔ Reporting — MSC-MEPC.3 Position Live Join | XMOD | V1 | D-GAP-M09, D-GAP-M10, D-DNV-12 |
| FEAT-SAF-XMOD-002 | Safety ↔ WRH — SCM Attendance Compliance | XMOD | V1 | D-GAP-M11, D-GAP-M26 |
| FEAT-SAF-XMOD-003 | Safety ↔ CMS — Live Join for SOI Assistant + Crew | XMOD | V1 | D-GAP-I2 |
| FEAT-SAF-XMOD-004 | Safety ↔ Purchase — CA → Purchase Req Hard FK | XMOD | V1 | D-GAP-M12 |
| FEAT-SAF-XMOD-005 | Safety ↔ PMS — Decoupled (no FK) | XMOD | V1 | D-GAP-I1 |
| FEAT-SAF-XMOD-006 | Shared Notification Queue via `master_notification` | XMOD | V1 | D-GAP-F2, D-GAP-M28 |
| FEAT-SAF-PDF-001 | 10-Section Incident PDF (formal report) | PDF | V1 | D-PDF-01, D-GAP-R09 |
| FEAT-SAF-PDF-002 | MSC-MEPC.3/Circ.4 Regulatory Export PDF | PDF | V1 | D-DNV-12, D-GAP-R08 |
| FEAT-SAF-PDF-003 | Near Miss Lightweight PDF | PDF | V1 | D-PDF-03a |
| FEAT-SAF-PDF-004 | SCM PDF (legacy structure) | PDF | V1 | D-PDF-03b |
| FEAT-SAF-PDF-005 | SOI Summary PDF (post-submission) | PDF | V1 | §2C.19, D-SOI-10 |
| FEAT-SAF-PDF-006 | Auditor Leave-Behind ZIP Package | PDF | V1 | D-PDF-02, D-GAP-M37 |
| FEAT-SAF-AUDIT-001 | Append-Only `vims_safety_incident_phase_log` | AUDIT | V1 | D-EDGE-10, §3.3 SSOT |
| FEAT-SAF-AUDIT-002 | Field-Level History (`vims_safety_field_history`) | AUDIT | V1 | D-EDGE-10, D-GAP-M33 |
| FEAT-SAF-AUDIT-003 | Hybrid Digital Signature Model | AUDIT | V1 | D-GAP-D1 |
| FEAT-SAF-AUDIT-004 | 3-Year Retention + Hard-Delete Attachments | AUDIT | V1 | D-SOI-11, D-GAP-G2 |
| FEAT-SAF-AUDIT-005 | Schema Versioning Grandfather | AUDIT | V1 | D-EDGE-11, D-GAP-C4 |
| FEAT-SAF-AUDIT-006 | Form Auto-Save Every 30s (IndexedDB) | AUDIT | V1 | D-GAP-F1 |
| FEAT-SAF-AUDIT-007 | Attachment Orphan Cleanup | AUDIT | V1 | D-GAP-M01 |
| FEAT-SAF-DASH-001 | Safety Intelligence Dashboard — Composite Score | DASH | V1 | §2B.14 |
| FEAT-SAF-DASH-002 | Heinrich Ratio Panel + Confidence Indicator | DASH | V1 | D-DNV-13, D-GAP-M27 |
| FEAT-SAF-DASH-003 | Repeat-Root-Cause Radar (Fleet + Vessel) | DASH | V1 | D-GAP-H2 |
| FEAT-SAF-DASH-004 | Pareto Screening Panel | DASH | V1 | D-GAP-R17 |
| FEAT-SAF-DASH-005 | SOI Compliance % (renamed) | DASH | V1 | D-GAP-DESIGN-01, D-GAP-M30 |
| FEAT-SAF-DASH-006 | CA Aging Pipeline (0-15/15-30/30-45/45+) | DASH | V1 | D-GAP-M29 |
| FEAT-SAF-DASH-007 | Dashboard Export (PDF + Excel, DPA-only) | DASH | V1 | D-GAP-M31 |
| FEAT-SAF-DASH-008 | Archive Search Opt-In Toggle | DASH | V1 | D-GAP-M32 |
| FEAT-SAF-DASH-009 | Seed Case-Study Library (Navigator + Sinkfast) | DASH | V1 | D-DNV-14 |
| FEAT-SAF-RBAC-001 | Closure Authority by Band (PIC/DPA/FM) | RBAC | V1 | D-RBAC-01, D-RBAC-05 |
| FEAT-SAF-RBAC-002 | Incident Creation — Top-4 Officers | RBAC | V1 | §3.4 SSOT |
| FEAT-SAF-RBAC-003 | Blame-Fixation Override Authority | RBAC | V1 | D-RBAC-07, D-GAP-B1 |
| FEAT-SAF-RBAC-004 | Rank-Persists / No Acting-* Invariant | RBAC | V1 | D-GAP-A3, D-GAP-A4 |
| FEAT-SAF-RBAC-005 | Permission IDs `SAF_F_*` / `SAF_P_*` in `msc_profiles` | RBAC | V1 | `<vims_integration>` |
| FEAT-SAF-RBAC-006 | Cross-Vessel Visibility (PIC borrow-lessons, Master read-closed) | RBAC | V1 | D-RBAC-08, D-RBAC-09, D-GAP-M08 |
| FEAT-SAF-RBAC-007 | FM Full Edit Authority During RED Closure | RBAC | V1 | D-GAP-M06 |
| FEAT-SAF-RBAC-008 | DPA-Only Taxonomy Maintenance | RBAC | V1 | D-CFG-01, D-CFG-03 |

**Total feature count: 94 features across 9 domains (41 INC, 6 NM, 8 SCM, 24 SOI, 6 XMOD, 6 PDF, 7 AUDIT, 9 DASH, 8 RBAC).**

---

## 4. Incident Module

The incident module is the largest V1 surface. 41 features cover the DNV-aligned 9-phase workflow (UI phases derived from the underlying 8-phase DNV state machine in §2B.6 of the SSOT — note: UI exposes "Intake" as a pre-Phase-1 scene-control step, giving the 9-phase nomenclature used in this PRD). The regulatory and investigation baseline is ISM Code (2010 amendments) Ch.9; IMO Casualty Investigation Code — Resolution MSC.255(84); IMO Resolution A.884(21); IMO Res A.1075(28); MARPOL Annex I (consolidated 2022); SOLAS Ch IX (as amended); KSM SSQE Manual Rev 01 Feb 2026 §11.

### Phase map (UI → DNV state machine)

| UI Phase | UI Label | Underlying DNV state (§2B.6) |
|---------|----------|------------------------------|
| 1 | Intake (Scene Control) | Phase 1 Scene Control |
| 2 | Notifications + Resource Allocation | Phase 2 Resources Allocated |
| 3 | Evidence | Phase 3 Evidence Collection |
| 4 | Sequence (Facts Systemized) | Phase 4 Facts Systemized |
| 5 | Analysis (Causes Analysed) | Phase 5 Causes Analysed |
| 6 | Recommendations (Findings Submitted) | Phase 6 Findings Submitted |
| 7 | Actions (DPA Accepted / Report Issued) | Phase 7 DPA Accepted |
| 8 | Verification (Follow-up / Effectiveness) | Phase 8 Follow-up |
| 9 | Closure | terminal state within Phase 8 |

### FEAT-SAF-INC-001 — Phase 1 Intake + Scene Control

**Priority:** V1
**User story:** As a reporter (any rank onboard), I need a fast intake form that captures what happened, when, where, initial risk impression, and a first-hour scene-protection checklist so the scene is preserved and the draft record exists before details fade.
**Acceptance criteria:**
- First-hour scene-protection checklist (freeze/mark alarms · note damage extent · secure scene · photograph + sketch · record witnesses present) rendered as an opening block; all 5 ticks required before Phase 1 Submit.
- Auto-save to IndexedDB every 30s; reconnect resumes from last saved state.
- Draft reference series issued on first save (`DRAFT-{VslCode}/{YYYY}/T{nnn}`); formal number assigned only at Phase 2 submit-to-office.
- Position fields editable; if incident occurs within ±12h of a Daily Report, system offers auto-fill from `vims_daily_report` live join.
- Incident type (IMO 11-category picklist, `master_safety_incident_type`, D-DNV-04) mandatory; multi-select permitted.
- Free-text narrative minimum 150 characters (configurable per validation layer).
**Dependencies:** FEAT-SAF-AUDIT-006 (auto-save), FEAT-SAF-XMOD-001 (position auto-fill), FEAT-SAF-INC-040 (numbering), FEAT-SAF-AUDIT-002 (field history).
**Decisions:** D-GAP-R07, D-GAP-C1, D-GAP-F1, D-GAP-M09.
**SSOT refs:** see SSOT §2B.6 Phase 1; §3.1.

### FEAT-SAF-INC-002 — IMO SMC/MC/MI Regulatory Classifier

**Priority:** V1
**User story:** As DPA, I need to classify every incident against the IMO Casualty Investigation Code categories (SMC / MC / MI) so the correct regulatory export template and auditor-bundle treatment apply.
**Acceptance criteria:**
- Three-value picklist: **SMC** (Serious Marine Casualty) / **MC** (Marine Casualty) / **MI** (Marine Incident) per IMO Res A.1075(28).
- Field is **separate from and in addition to** internal risk band (FEAT-SAF-INC-003) — no collapse.
- Investigation deadlines remain risk-band deadlines (NOT 60/30/30 SMC windows) — explicit reconciliation per D-GAP-R08 option (b).
- Classifier drives template selection for MSC-MEPC.3 export (FEAT-SAF-PDF-002) and auditor bundle (FEAT-SAF-PDF-006).
- Changes logged in `vims_safety_field_history` with reason.
**Dependencies:** FEAT-SAF-INC-003, FEAT-SAF-PDF-002, FEAT-SAF-AUDIT-002.
**Decisions:** D-GAP-R08.
**SSOT refs:** see SSOT §2B.5; §6 D-GAP-R08.

### FEAT-SAF-INC-003 — Internal Risk Band GREEN/YELLOW/RED

**Priority:** V1
**User story:** As an investigator, I need the system to compute and display a GREEN/YELLOW/RED band from severity × probability so investigation depth, closer authority and deadline auto-align.
**Acceptance criteria:**
- Risk band computed on Phase 1 submit from incident type + type-of-loss + probability assessment; editable by DPA at any review stage with reason logged.
- GREEN → 30-day closure, Master investigator, PIC closer.
- YELLOW → 30–45 day closure (per DPA), joint Master + PIC investigation, DPA closer.
- RED → per-case closure (no automatic close), DPA + external expert investigation, FM closer.
- Dashboard overdue flag at 80% of band deadline and again at deadline.
- Re-classification does not reset deadline clock; original submit-timestamp governs.
**Dependencies:** FEAT-SAF-RBAC-001, FEAT-SAF-AUDIT-002.
**Decisions:** D-DNV-02, D-GAP-F3.
**SSOT refs:** see SSOT §2B.3; §3.4.

### FEAT-SAF-INC-004 — Phase 2 Notifications + Resource Allocation

**Priority:** V1
**User story:** As DPA, I need Phase 2 to fire notifications to the investigation chain the moment an incident is formally submitted and to allocate the lead investigator based on band.
**Acceptance criteria:**
- On Phase 2 submit: notifications to PIC + DPA + safety channel via `master_notification` (shared VIMS queue); Slack best-effort (D-GAP-F2) with in-app notification as authoritative.
- RED-band also notifies Managing Director and fires external-expert engagement prompt.
- No notification digest — every safety event is an independent notification (D-GAP-M28).
- No auto-fallback to email on Slack webhook failure (D-GAP-F2); webhook failure on RED notifications raises a platform-level alert (D-GAP-F4).
- Formal incident number assigned at this gate: `{VslCode}/{YYYY}/{NNN}`, gap-free per-vessel-per-year.
**Dependencies:** FEAT-SAF-XMOD-006, FEAT-SAF-INC-040.
**Decisions:** D-EDGE-09, D-GAP-F2, D-GAP-F4, D-GAP-M28.
**SSOT refs:** see SSOT §3.5.

### FEAT-SAF-INC-005 — Phase 3 Evidence Workspace (5-Source Tabbed)

**Priority:** V1
**User story:** As the lead investigator, I need a tabbed evidence workspace covering Position / People / Parts / Paper / Electronic so I capture the full DNV 5-source picture without free-text fragmentation.
**Acceptance criteria:**
- Five tabs, each with its own checklist (§2B.8 table reproduced in-app).
- Position: lat/lon editable, photos from 4 angles, sketches, deck-plan overlay upload.
- People: witness list, structured interview links (FEAT-SAF-INC-012), qualifications snapshot at event time.
- Parts: damaged equipment ID, samples, wear/tear notes; equipment history reference is **manual** (PMS decoupled per D-GAP-I1).
- Paper: SMS procedure ref, voyage plan, log entries, permits, training records, certs; auto-checklist per D-GAP-R05.
- Electronic: VDR / ECDIS / GPS / UMS / VTS / fire-system / CCTV / email / AIS fields.
- Perishable-evidence prompt on YELLOW/RED if Phase 3 has no People or Electronic entries within 24h of Phase 2 submit.
**Dependencies:** FEAT-SAF-INC-008, FEAT-SAF-INC-011, FEAT-SAF-INC-012, FEAT-SAF-XMOD-005.
**Decisions:** D-DNV-07, D-GAP-I1, D-GAP-R05, D-GAP-R06.
**SSOT refs:** see SSOT §2B.8.

### FEAT-SAF-INC-006 — Evidence Matrix (Pro/Con)

**Priority:** V1
**User story:** As the lead investigator, I need a Pro/Con evidence matrix per major finding so I visibly surface contradicting evidence and mitigate confirmation bias.
**Acceptance criteria:**
- Matrix columns: `Finding | Pro evidence | Con evidence | Source | Comments`.
- DPA may flag any finding as "major"; matrix then requires ≥1 Con row before Phase 5 → 6 transition (bias guard #4).
- Soft warning override permitted with justification text.
**Dependencies:** FEAT-SAF-INC-024.
**Decisions:** D-DNV-07, D-DNV-11 #4.
**SSOT refs:** see SSOT §2B.8; §2B.12.

### FEAT-SAF-INC-007 — Chain-of-Custody Tab

**Priority:** V1
**User story:** As DPA, I need every physical evidence item's custody history captured so any future legal-discovery or P&I claim is defensible.
**Acceptance criteria:**
- Per-item fields: description, collection date/time, collector name + signature, storage location (sealed-bag ID if applicable), witness signature, handover log (who-got-it-when).
- Handover log is append-only; every transfer logged with timestamp.
- Mandatory for RED; recommended for YELLOW; optional for GREEN.
- Rendered as dedicated tab inside Phase 3 Evidence Workspace.
**Dependencies:** FEAT-SAF-INC-005, FEAT-SAF-AUDIT-003.
**Decisions:** D-GAP-R04.
**SSOT refs:** see SSOT §6 D-GAP-R04.

### FEAT-SAF-INC-008 — Marine Document Inventory Auto-Checklist

**Priority:** V1
**User story:** As an investigator, I need an auto-populated checklist of maritime documents (logs, certificates, maintenance records) so nothing perishable or frequently-overwritten is missed.
**Acceptance criteria:**
- Pre-populated list: Deck Log (rough + smooth), Engine Log, Radio Log, ECDIS track, AIS record (shore-requested), VDR data, Noon/Bunker records, ISM certs, Stability booklet, Class certs, Maintenance records.
- Each item = tick + timestamp when captured; photos/scan attachments linked.
- Cargo-incident overlay loads additional items via FEAT-SAF-INC-009.
**Dependencies:** FEAT-SAF-INC-009, FEAT-SAF-INC-011.
**Decisions:** D-GAP-R05.
**SSOT refs:** see SSOT §6 D-GAP-R05.

### FEAT-SAF-INC-009 — Cargo-Specific Evidence Overlay

**Priority:** V1
**User story:** As an investigator on a cargo incident, I need domain-specific evidence prompts so cargo-related evidence (ullage, sampling, stability, manifest) is reliably captured.
**Acceptance criteria:**
- Triggered when incident type in {Cargo-related categories}.
- Adds prompts: tank ullage record, sounding log, cargo-hold bilge, cargo sampling, hatch-cover certs, cargo-hold temp/humidity, stability calc, manifest, shipper instructions, cargo inspection reports.
- Overlay applies inside Paper tab of Evidence Workspace.
**Dependencies:** FEAT-SAF-INC-005, FEAT-SAF-INC-008.
**Decisions:** D-GAP-R10.
**SSOT refs:** see SSOT §6 D-GAP-R10.

### FEAT-SAF-INC-010 — Health / Fatigue Evidence Sub-Section

**Priority:** V1
**User story:** As an investigator on personal-injury / illness / fitness-for-duty incidents, I need a health & fatigue sub-section prompting ship + shore medical records, medication, WRH 96-hour lookback, sleep, fitness-for-duty status, vaccinations, pre-existing conditions.
**Acceptance criteria:**
- Triggered on incident type = Personal Injury / Illness / Fitness-for-Duty.
- Sub-section embedded in People tab of Evidence Workspace.
- WRH lookback pulled via live join to `vims_wrh_*` tables (D-GAP-M26 timezone model).
- MLC 2006 flag (MLC-reportable = Yes/No) surfaced; DPA-visible.
**Dependencies:** FEAT-SAF-INC-005, FEAT-SAF-XMOD-002, FEAT-SAF-AUDIT-002.
**Decisions:** D-GAP-R23, D-GAP-M14, D-GAP-M26.
**SSOT refs:** see SSOT §6 D-GAP-R23.

### FEAT-SAF-INC-011 — Evidence-Preservation Deadline Task List

**Priority:** V1
**User story:** As DPA, I need auto-generated deadline tasks on every new incident so VDR, ECDIS, AIS and witness statement evidence is captured before it's overwritten or forgotten.
**Acceptance criteria:**
- On incident creation: system schedules prompts — VDR capture within 12h (RED hard alarm), ECDIS track snapshot within 24h, AIS shore-request within 24h, photo walk-around within 48h, full formal statements within 7 days.
- Overdue items appear on incident dashboard tile + notification.
- RED-band VDR-overdue fires a hard alarm (dashboard + Slack + in-app).
**Dependencies:** FEAT-SAF-INC-004, FEAT-SAF-DASH-001.
**Decisions:** D-GAP-R06.
**SSOT refs:** see SSOT §6 D-GAP-R06.

### FEAT-SAF-INC-012 — Structured 4-Phase Interview Module

**Priority:** V1
**User story:** As an investigator, I need a structured interview form that follows the DNV 4-phase protocol so interviews are consistent and defensible.
**Acceptance criteria:**
- Four phases: Make Acquaintance · Introduction · The Meeting · Conclusion.
- Q&A array; each row has a `type` dropdown (Open / Closed / Analysing / Clarifying / Probing / Leading / Biased).
- Leading / Biased selections fire soft warnings with suggested rephrasing; keyword checks for "isn't it", "shouldn't you", "could that", "wouldn't it".
- Recording-consent toggle; behaviour self-audit checklist post-interview (optional).
- Each interview is its own record under the People tab.
**Dependencies:** FEAT-SAF-INC-005, FEAT-SAF-INC-013, FEAT-SAF-INC-014.
**Decisions:** D-DNV-08.
**SSOT refs:** see SSOT §2B.9.

### FEAT-SAF-INC-013 — Formal vs Informal Interview Flag

**Priority:** V1
**User story:** As DPA, I need to know whether each interview was a formal protocol interview or an informal on-scene conversation so auditors and defence counsel can evaluate weight.
**Acceptance criteria:**
- Picklist at interview start: **FORMAL** or **INFORMAL**.
- FORMAL interviews enforce witness read-back + sign-off (FEAT-SAF-INC-014).
- INFORMAL interviews require a mandatory reason field ("why formal was impossible").
- Flag visible on interview record and on auditor export.
**Dependencies:** FEAT-SAF-INC-012, FEAT-SAF-INC-014.
**Decisions:** D-GAP-R20.
**SSOT refs:** see SSOT §6 D-GAP-R20.

### FEAT-SAF-INC-014 — Witness Read-Back + Sign-Off Protocol

**Priority:** V1
**User story:** As an investigator, I need the system to enforce a read-back → sign → copy-to-witness flow on every formal interview statement so statements are not "final" without witness confirmation.
**Acceptance criteria:**
- Three ticks required: (a) read-back to witness, (b) witness signature on paper (wet-sign scan upload OR digital signature per D-GAP-D1), (c) copy to witness recorded.
- Statement is locked as "final" only after all three.
- Applies to FORMAL interviews only; INFORMAL interviews show the checklist but do not hard-block.
**Dependencies:** FEAT-SAF-INC-012, FEAT-SAF-INC-013, FEAT-SAF-AUDIT-003.
**Decisions:** D-GAP-R19, D-GAP-M15.
**SSOT refs:** see SSOT §6 D-GAP-R19.

### FEAT-SAF-INC-015 — Phase 4 Facts Systemized (Shared Fact Base)

**Priority:** V1
**User story:** As the lead investigator, I need a single fact base that all analysis tools draw from so adding a fact in STEP also makes it available in Fact Tree, ECF, Barrier, and Change analyses.
**Acceptance criteria:**
- Shared `vims_safety_fact` table underpins every analysis tool (FEAT-SAF-INC-020).
- Each fact requires an evidence link (interview ID / document ID / photo ID) — bias guard #2 (Assumption).
- Hindsight guard: facts referencing post-event information are blocked from being used in "decision at time" analysis (bias guard #3).
**Dependencies:** FEAT-SAF-INC-005, FEAT-SAF-INC-020, FEAT-SAF-INC-024.
**Decisions:** D-DNV-10, D-DNV-11 #2, D-DNV-11 #3.
**SSOT refs:** see SSOT §2B.11; §2B.12.

### FEAT-SAF-INC-016 — Phase 5 Causal Analysis + Loop-Back Gate

**Priority:** V1
**User story:** As the lead investigator, I need to be able to loop back from Phase 5 (or 4) to Phase 3 without losing partial data when more evidence is required, so the DNV "need more info?" gate is honoured.
**Acceptance criteria:**
- Loop-back from Phase 5 → Phase 3 (also Phase 4 → 3, Phase 6 → 3) permitted at any time.
- No cap on loop-back count per incident (D-GAP-B3).
- Every loop-back logged in `vims_safety_incident_phase_log` with mandatory reason.
- Excessive looping surfaces as a dashboard metric (no hard block).
- All evidence/cause data preserved across loop-back (state machine permits in-place re-opening).
**Dependencies:** FEAT-SAF-INC-015, FEAT-SAF-AUDIT-001.
**Decisions:** D-DNV-05, D-GAP-B3.
**SSOT refs:** see SSOT §2B.6.

### FEAT-SAF-INC-017 — M-SCAT Cause Picker (174 codes)

**Priority:** V1
**User story:** As the lead investigator, I need a hierarchical cause picker over the 174-row M-SCAT taxonomy with prefix search so cause coding is fast and consistent across the fleet.
**Acceptance criteria:**
- Source: `master_mscat_taxonomy` seeded from `safety-reference-data/mscat_taxonomy.csv` (174 rows, columns `category_id, category_name, subcode_id, subcode_description, cause_type`).
- Includes new subcode **10.15 Design/MOC Governance — Independent Review Absent** (D-GAP-R15).
- Hierarchical tree UI with prefix search (e.g., "5.2" → "Inadequate orientation/induction").
- Every selected code requires a free-text rationale + evidence link (bias guard #2).
- In-app Help drawer shows Navigator + Sinkfast case-study examples (FEAT-SAF-DASH-009).
- Taxonomy edit rights = DPA only (D-CFG-01, FEAT-SAF-RBAC-008).
**Dependencies:** FEAT-SAF-INC-015, FEAT-SAF-DASH-009, FEAT-SAF-RBAC-008.
**Decisions:** D-DNV-01, D-GAP-C2, D-GAP-R15, D-CFG-01.
**SSOT refs:** see SSOT §2B.2; §6 D-GAP-C2, D-GAP-R15.

### FEAT-SAF-INC-018 — Causal Layering Tag (Immediate / Intermediate / Root)

**Priority:** V1
**User story:** As DPA, I need every cause tagged Immediate / Intermediate / Root so investigations don't prematurely close at the intermediate level and the ABS scaffolding is visibly applied.
**Acceptance criteria:**
- Each cause entered on an incident MUST carry an additional tag `layer ∈ {Immediate, Intermediate, Root}`.
- Phase 5 → Phase 6 transition blocked unless at least one Root-level cause exists.
- Visual hierarchy: causal-layer tabs (FEAT-SAF-INC-020) render Immediate → Intermediate → Root columns with colour tokens from DESIGN_SYSTEM.
- Soft warning when >5 Immediate-only causes exist with zero Root — nudges investigator to deepen.
**Dependencies:** FEAT-SAF-INC-017, FEAT-SAF-INC-019.
**Decisions:** D-GAP-R01.
**SSOT refs:** see SSOT §6 D-GAP-R01.

### FEAT-SAF-INC-019 — Multiple Root Causes (no cap)

**Priority:** V1
**User story:** As an investigator, I need the system to accept multiple root causes as the default so genuinely multi-causal events are not artificially reduced to one root.
**Acceptance criteria:**
- At least one root cause mandatory.
- No upper cap on root causes.
- Single-root-cause closure requires a written monocausal justification in the closure note (free text, min 80 characters).
- Multiple causal paths can each be coded separately against M-SCAT; each carries its own evidence link.
**Dependencies:** FEAT-SAF-INC-017, FEAT-SAF-INC-018.
**Decisions:** D-GAP-R03.
**SSOT refs:** see SSOT §6 D-GAP-R03.

### FEAT-SAF-INC-020 — Multi-Tool Analysis Workspace

**Priority:** V1
**User story:** As the lead investigator, I need parallel analysis views (STEP, Fact Tree, ECF, Barrier, Change) over the same fact set so I can cross-method triangulate and mitigate investigator bias.
**Acceptance criteria:**
- Five tools backed by shared fact base (FEAT-SAF-INC-015): STEP timeline (swimlane), Fact Tree (AND-gated), ECF Chart, Barrier Analysis, Change Analysis.
- Minimum tools required per band: SHALLOW=2, MEDIUM=3, DEEP=5 (FEAT-SAF-INC-021).
- RED-band always DEEP → all 5 mandatory.
- Adding a fact in one tool populates it in all others.
**Dependencies:** FEAT-SAF-INC-015, FEAT-SAF-INC-021.
**Decisions:** D-DNV-10, D-GAP-R14.
**SSOT refs:** see SSOT §2B.11.

### FEAT-SAF-INC-021 — Investigation-Depth Task Triangle

**Priority:** V1
**User story:** As DPA, I need the system to recommend investigation depth (SHALLOW / MEDIUM / DEEP) based on severity × systemic-risk × learning-value × resources so investigation rigour is proportionate.
**Acceptance criteria:**
- Auto-recommendation based on risk band (GREEN→SHALLOW, YELLOW→MEDIUM, RED→DEEP).
- DPA may override with reason logged.
- Depth drives minimum analysis tools (FEAT-SAF-INC-020).
- Depth is editable until Phase 5 submit; locked thereafter.
**Dependencies:** FEAT-SAF-INC-003, FEAT-SAF-INC-020.
**Decisions:** D-GAP-R14.
**SSOT refs:** see SSOT §6 D-GAP-R14.

### FEAT-SAF-INC-022 — People / Process / Plant Interrogatory Checklist

**Priority:** V1
**User story:** As an investigator, I need three mandatory interrogatory questions (People / Process / Plant) at the Phase 5 gate so investigations are not one-dimensional.
**Acceptance criteria:**
- Three mandatory narrative answers before Phase 5 Submit:
  1. How did actions of people contribute?
  2. What gaps in procedures?
  3. What machinery / equipment failures?
- Each answer min 50 characters.
- Answers appear on 10-section PDF in the causal-factor enumeration section.
**Dependencies:** FEAT-SAF-INC-016.
**Decisions:** D-GAP-R16.
**SSOT refs:** see SSOT §6 D-GAP-R16.

### FEAT-SAF-INC-023 — Safeguard-Failure Interrogatory

**Priority:** V1
**User story:** As an investigator, I need a 6-dimension safeguard-failure interrogatory on every failed barrier so Design / Installation / Maintenance / Operation / Testing / Override gaps are systematically coded.
**Acceptance criteria:**
- For every failed safeguard in Barrier Analysis, investigator codes 6 dimensions: Design (spec) / Installation (QC) / Maintenance (PM effectiveness) / Operation (procedure adherence) / Testing (validation) / Override (authorisation + training).
- Each dimension maps back to an M-SCAT code (via FEAT-SAF-INC-017).
- Extends Barrier tool in FEAT-SAF-INC-020.
**Dependencies:** FEAT-SAF-INC-020, FEAT-SAF-INC-017.
**Decisions:** D-GAP-R18.
**SSOT refs:** see SSOT §6 D-GAP-R18.

### FEAT-SAF-INC-024 — 8 Bias Guards (5 DNV + 3 Organisational Traps)

**Priority:** V1
**User story:** As DPA, I need 8 named bias guards firing at phase-transition gates so investigator and institutional biases are surfaced and mitigated.
**Acceptance criteria:**
- Seed `master_safety_bias_guard` table with 8 rows:
  1. Recency (Phase 4 → 5) — all 5 evidence categories have ≥1 entry OR explicit "n/a — justified".
  2. Assumption (Add-fact) — every fact requires an evidence link.
  3. Hindsight (Add-finding) — decision/action records timestamped; cannot cite post-event info.
  4. Confirmation (Phase 5 → 6) — Evidence Matrix requires ≥1 Con per major finding.
  5. Blame Fixation (Phase 6 → 7) — hard block if all roots in Personal Factors cat 1–4 AND no Lack-of-Control entry.
  6. Plant-Problem Trap (organisational) — soft warning if causes cluster in hardware-only categories.
  7. Personnel-Problem Trap (organisational) — soft warning if causes cluster in person-only categories.
  8. External-Event Trap (organisational) — soft warning if causes cluster in external-event-only categories.
- Soft warnings (1, 4, 6, 7, 8) over-ridable with justification.
- Hard block (5) overridable by DPA for GREEN/YELLOW, FM for RED (FEAT-SAF-RBAC-003).
**Dependencies:** FEAT-SAF-INC-025, FEAT-SAF-RBAC-003.
**Decisions:** D-DNV-11, D-GAP-R12.
**SSOT refs:** see SSOT §2B.12; §6 D-GAP-R12.

### FEAT-SAF-INC-025 — Blame-Fixation Hard Block + Override

**Priority:** V1
**User story:** As DPA (GREEN/YELLOW) or FM (RED), I need a hard override authority when blame-fixation bias guard fires so unavoidable personal-factor-only closures are still possible with senior acknowledgement.
**Acceptance criteria:**
- Block fires at Phase 6 → 7 transition when all root causes are in M-SCAT Personal Factors categories 1–4 AND no Lack-of-Control entry exists.
- Override action requires: justification text (≥200 chars) + digital signature (FEAT-SAF-AUDIT-003) + timestamp.
- GREEN/YELLOW override = DPA; RED override = FM.
- If both DPA and FM refuse RED override → investigation sent back to Phase 3 (rework); no MD escalation (D-GAP-B1).
**Dependencies:** FEAT-SAF-INC-024, FEAT-SAF-RBAC-003, FEAT-SAF-AUDIT-003.
**Decisions:** D-DNV-11 #5, D-RBAC-07, D-GAP-B1.
**SSOT refs:** see SSOT §6 D-RBAC-07; D-GAP-B1.

### FEAT-SAF-INC-026 — Human Factors (SHELL + IMO A.884(21) + Risk/Change)

**Priority:** V1
**User story:** As an investigator, I need SHELL element tagging + IMO A.884(21) 7-domain checklist + a new marine-specific Risk & Change domain so human-factor analysis is regulatory-compliant and SMS-aware.
**Acceptance criteria:**
- SHELL tagging optional per cause: S / H / E / L-central / L-peripheral.
- 7-domain checklist (People / Organisation / Working conditions / Ship factors / Shore-side / External / Sequence) rendered as tabs; each has free-text + "considered — n/a" toggle.
- Additional 8th domain added per D-GAP-R21: **Risk & Change Management** (Risk control inadequacy · Monitoring gaps · Change-management effectiveness · Regulatory-compliance failures).
- Near miss variant uses category tag and immediate-cause selection only; no 7/8-domain expansion (§2B.10).
**Dependencies:** FEAT-SAF-INC-017.
**Decisions:** D-DNV-09, D-GAP-R21.
**SSOT refs:** see SSOT §2B.10; §6 D-GAP-R21.

### FEAT-SAF-INC-027 — Phase 6 Recommendations (3-Tier + Colour Taxonomy)

**Priority:** V1
**User story:** As DPA, I need Phase 6 closure to require three recommendation tiers (Lessons Learned + Immediate + System) and a visible Corrective / Preventive / Lessons taxonomy so recommendations are actionable and auditable.
**Acceptance criteria:**
- Three mandatory sections at Phase 6:
  1. **Lessons Learned** — ≥1 narrative paragraph; drafts Fleet Circular auto-linked to VIMS Circular module.
  2. **Immediate (Corrective) Actions** — ≥1; vessel-specific; 30–90 day; auto-creates CA records with verifier + due date (FEAT-SAF-XMOD-004).
  3. **System Actions** — ≥1; office/fleet-wide; themed against 7 themes: Training & Competence · Contractor/Supplier Management · Compliance Assurance · Human Resources · Management of Change · Procedures & Standards · Equipment Management.
- Each item colour-coded as Corrective / Preventive / Lessons per D-GAP-R13 visual taxonomy.
- Closure check for YELLOW/RED: at least one of each tier must exist.
- ALARP gate on System Actions per FEAT-SAF-INC-028.
**Dependencies:** FEAT-SAF-INC-028, FEAT-SAF-XMOD-004.
**Decisions:** D-DNV-06, D-GAP-R13.
**SSOT refs:** see SSOT §2B.7; §6 D-GAP-R13.

### FEAT-SAF-INC-028 — ALARP Cost-Benefit Gate on System Actions

**Priority:** V1
**User story:** As DPA, I need every System Action to carry ALARP fields (effort, likelihood reduction, residual-risk acceptability) so recommendations are defensible under regulatory scrutiny.
**Acceptance criteria:**
- Each System Action requires three fields:
  - Estimated effort (cost or labour).
  - Estimated likelihood reduction.
  - Residual-risk acceptability statement (free text).
- Mandatory for RED and YELLOW bands; optional-but-prompted for GREEN.
- ALARP fields surfaced on 10-section PDF and auditor export.
**Dependencies:** FEAT-SAF-INC-027.
**Decisions:** D-GAP-R02.
**SSOT refs:** see SSOT §6 D-GAP-R02.

### FEAT-SAF-INC-029 — Tolerable-Failure Filter (GREEN only)

**Priority:** V1.1
**User story:** As DPA, I need a pre-investigation "tolerable failure" gate at Phase 1 so GREEN-band repeat low-consequence events already trended in Pareto can be closed without full RCA.
**Acceptance criteria:**
- GREEN-band only; YELLOW/RED always proceed to full RCA.
- Decision tile at Phase 1: "Is this a preventive-maintenance / repeat low-consequence failure already trended?"
- If yes → closure path "Tolerable — referenced to trend analysis" with DPA acknowledgment.
- Auto-linked to Pareto dashboard record (FEAT-SAF-DASH-004).
**Dependencies:** FEAT-SAF-INC-001, FEAT-SAF-DASH-004, FEAT-SAF-INC-003.
**Decisions:** D-GAP-R11.
**SSOT refs:** see SSOT §6 D-GAP-R11.

### FEAT-SAF-INC-030 — Phase 7 DPA Acceptance / Report Issued

**Priority:** V1
**User story:** As DPA, I need a Phase 7 acceptance gate that validates the 3-tier recommendations, bias guards, and causal-layer completeness before issuing the formal report.
**Acceptance criteria:**
- Pre-flight validations: bias guards resolved, ≥1 Root cause coded, all three recommendation tiers filled (for YELLOW/RED), ALARP fields populated.
- On accept: generates the 10-section PDF (FEAT-SAF-PDF-001); state transitions to Phase 8.
- Closer authority by band: PIC=GREEN, DPA=YELLOW, FM=RED.
- Re-open authority mirrors closer authority (D-EDGE-03).
**Dependencies:** FEAT-SAF-INC-027, FEAT-SAF-PDF-001, FEAT-SAF-RBAC-001.
**Decisions:** D-PDF-01, D-RBAC-01, D-EDGE-03.
**SSOT refs:** see SSOT §2B.6; §6 D-PDF-01.

### FEAT-SAF-INC-031 — Phase 8 Follow-up / Effectiveness Verification

**Priority:** V1
**User story:** As PIC (GREEN) or DPA (YELLOW/RED), I need Phase 8 to reuse the existing `psc_physical_verification` pattern so corrective-action effectiveness is confirmed without bespoke re-review cycles.
**Acceptance criteria:**
- Reuse `psc_physical_verification` pattern (same-DB live join) — no separate 90/180/365-day re-review (D-EDGE-06).
- Incident closes to CLOSED once all CAs are verified (or explicitly deferred with reason).
- CA closure does not block on Physical Verification — PV runs on its own track (D-GAP-M03).
**Dependencies:** FEAT-SAF-INC-030, FEAT-SAF-XMOD-004.
**Decisions:** D-EDGE-06, D-GAP-M03.
**SSOT refs:** see SSOT §6 D-EDGE-06; D-GAP-M03.

### FEAT-SAF-INC-032 — Multi-Vessel Incident Linking + Duplicate Detection

**Priority:** V1
**User story:** As a reporter submitting a multi-vessel event, I need the system to auto-detect potential duplicates within 24h and prompt me to link or create separately so each vessel retains flag-state reporting integrity.
**Acceptance criteria:**
- Auto-detect rule: same incident type + position within 10 nm + overlapping time window, ≤24h.
- Prompt: "Link to existing incident? [Yes / No — separate events]".
- On link: two records created, each vessel owns its investigation, cross-link preserved in `vims_safety_incident.linked_incident_id`.
- Each vessel's PIC/DPA closes their own half independently (D-GAP-M07).
**Dependencies:** FEAT-SAF-INC-001.
**Decisions:** D-EDGE-01, D-GAP-M25, D-GAP-M07.
**SSOT refs:** see SSOT §6 D-EDGE-01; D-GAP-M07; D-GAP-M25.

### FEAT-SAF-INC-033 — Near-Miss ↔ Incident Supersede-and-Create-New

**Priority:** V1
**User story:** As DPA, when I reclassify a near miss as an incident (or vice versa) I need the original to close as "Superseded" with a link to the new record so analytics remain pure.
**Acceptance criteria:**
- Option C (supersede-and-create-new) is the only reclassification path.
- Original record status → `Superseded`; new record created; bidirectional link stored.
- Superseded records excluded from dashboard metrics (D-GAP-H2) — no inflation.
**Dependencies:** FEAT-SAF-NM-001.
**Decisions:** D-EDGE-07, D-GAP-H2.
**SSOT refs:** see SSOT §6 D-EDGE-07.

### FEAT-SAF-INC-034 — External-Party (Non-Crew) Injury Capture

**Priority:** V1
**User story:** As an investigator, I need to record non-crew injuries (pilot, stevedore, contractor etc.) with the right party type so the event is reportable correctly.
**Acceptance criteria:**
- "External Party" picklist: Pilot / Shipyard / Stevedore / Contractor / Passenger / Port Agent / Other.
- Free-text name + company fields.
- Appears in Phase 1 People section and on 10-section PDF.
**Dependencies:** FEAT-SAF-INC-001.
**Decisions:** D-EDGE-02.
**SSOT refs:** see SSOT §6 D-EDGE-02.

### FEAT-SAF-INC-035 — Re-open Closed Incident (Band-Gated)

**Priority:** V1
**User story:** As DPA (GREEN/YELLOW) or FM (RED), I need to re-open a closed incident when new evidence emerges so investigation integrity is maintained.
**Acceptance criteria:**
- Re-open authority mirrors closure authority (D-EDGE-03).
- Returns to Phase 5 (Analysis).
- Mandatory reason logged in `vims_safety_incident_phase_log`.
- All prior data preserved; new loop-back counter increments.
**Dependencies:** FEAT-SAF-INC-016, FEAT-SAF-AUDIT-001.
**Decisions:** D-EDGE-03.
**SSOT refs:** see SSOT §6 D-EDGE-03.

### FEAT-SAF-INC-036 — Draft Mode at Any Phase

**Priority:** V1
**User story:** As an investigator, I need to save partial data at any phase so I can pause and resume without forcing full-form validation at every save.
**Acceptance criteria:**
- Any phase allows partial data save.
- Phase-level Submit enforces full validation for that phase's required fields (D-EDGE-08 hybrid A+D).
- No partial phase advance — cannot jump Phase 3 → 5 without Phase 4 Submit passing.
**Dependencies:** FEAT-SAF-AUDIT-006.
**Decisions:** D-EDGE-08.
**SSOT refs:** see SSOT §6 D-EDGE-08.

### FEAT-SAF-INC-037 — YELLOW-Band Deadline Auto-Pause on DPA Leave

**Priority:** V1
**User story:** As DPA, when I'm on approved leave the YELLOW-band closure deadline should auto-pause and resume on my return so the clock doesn't run against sole-closer authority.
**Acceptance criteria:**
- Pause triggered when DPA leave record is active in the HRM system (live join).
- Resume on DPA return date.
- No "Acting-DPA" concept (D-GAP-A3).
- Audit log records pause/resume events.
**Dependencies:** FEAT-SAF-RBAC-004, FEAT-SAF-AUDIT-002.
**Decisions:** D-GAP-A1, D-GAP-A3.
**SSOT refs:** see SSOT §6 D-GAP-A1; D-GAP-A3.

### FEAT-SAF-INC-038 — PIC Retains YELLOW Ownership After Vessel Transfer

**Priority:** V1
**User story:** As the original PIC on a YELLOW investigation, I retain ownership remotely until closure even if I transfer vessels mid-investigation so continuity is preserved.
**Acceptance criteria:**
- `investigator_crew_id` field locks at Phase 2 submit; does not update on vessel transfer.
- PIC can access and edit the record from any vessel while role persists.
- Replacement PIC on original vessel has read-only access until original closes out.
**Dependencies:** FEAT-SAF-RBAC-004.
**Decisions:** D-GAP-A2.
**SSOT refs:** see SSOT §6 D-GAP-A2.

### FEAT-SAF-INC-039 — Self-Report Conflict Guard

**Priority:** V1
**User story:** As DPA, when the reporter is also the injured party, PIC or person-in-charge, I need the system to flag the conflict and require a different approver so separation-of-duties is enforced.
**Acceptance criteria:**
- On submit, check: reporter's CrewId == injured-party CrewId OR == PIC CrewId OR == person-in-charge CrewId.
- If match: form shows warning "Conflict detected — different approver required".
- Approver routing: Master for vessel-side submissions; DPA for office-side.
- Does not block submission; enforces approver assignment only.
**Dependencies:** FEAT-SAF-INC-001, FEAT-SAF-RBAC-001.
**Decisions:** D-GAP-A5.
**SSOT refs:** see SSOT §6 D-GAP-A5.

### FEAT-SAF-INC-040 — Incident Number with Draft Reference Series

**Priority:** V1
**User story:** As a reporter, I need a temporary `DRAFT-{VslCode}/{YYYY}/T{nnn}` reference while the record is a draft, and a gap-free `{VslCode}/{YYYY}/{NNN}` formal number assigned only at submit-to-office so draft editing doesn't pollute the sequence.
**Acceptance criteria:**
- Draft series: `DRAFT-{VslCode}/{YYYY}/T{nnn}` issued on first save.
- Formal: `{VslCode}/{YYYY}/{NNN}` assigned at Phase 2 submit-to-office; per-vessel-per-year, gap-free sequence.
- Once assigned, formal number never changes.
- Schema version stamped on record at formal-number assignment (D-EDGE-11 grandfather; D-GAP-C4).
**Dependencies:** FEAT-SAF-INC-004, FEAT-SAF-AUDIT-005.
**Decisions:** D-GAP-C1, D-EDGE-11, D-GAP-C4.
**SSOT refs:** see SSOT §6 D-GAP-C1; D-EDGE-11; D-GAP-C4.

### FEAT-SAF-INC-041 — MSC-MEPC.3 Position Auto-Fill (±12h tolerance)

**Priority:** V1
**User story:** As an investigator preparing the MSC-MEPC.3/Circ.4 export, I need the incident position auto-filled from a Daily Report within ±12h so ~40% of the IMO appendix pre-populates.
**Acceptance criteria:**
- Live join to `vims_daily_report` via Reporting module (D-GAP-I2 same-DB).
- Window: incident timestamp ± 12 hours.
- User can always edit the auto-fill or enter a more recent position (D-GAP-M09).
- Daily Report missing: accept manual lat/long + time; flag `awaiting_daily_report_match`; do NOT block (D-GAP-M10).
**Dependencies:** FEAT-SAF-XMOD-001, FEAT-SAF-PDF-002.
**Decisions:** D-DNV-12, D-GAP-M09, D-GAP-M10.
**SSOT refs:** see SSOT §2B.13; §6 D-GAP-M09; D-GAP-M10.

---

## 5. Near Miss Module

Near miss is the reporting-culture pillar. The module uses the same underlying `vims_safety_incident` table via a `record_type='near_miss'` discriminator — schema and cause taxonomy inherit from Incident, but the workflow, visibility, and PDF output diverge.

### FEAT-SAF-NM-001 — Near Miss Creation (Any Rank)

**Priority:** V1
**User story:** As any crew member, I can create a near miss record so the reporting-culture principle (Heinrich pyramid base) is fed.
**Acceptance criteria:**
- Any rank may create a near miss (not top-4 limited) per D-RBAC-11.
- `record_type='near_miss'` set at creation.
- The form captures place (`At Anchor`, `At Sea`, `At Port`), a single user-facing Category field that combines the previous Category and Possible Loss Type dropdown options, and Immediate Cause. Near Miss Type is not used.
- Category allows up to 3 selections and supports `Other - Specify`. Immediate Cause supports `Other - Specify` inside the dropdown at the bottom.
- Form is lighter than Incident (no Phase 7 DPA acceptance, no separate analysis page, no 7-domain IMO A.884(21) expansion, no mandatory CA/PA - Lessons Learned + Immediate Action only).
- Submission controls per FEAT-SAF-NM-005.
**Dependencies:** FEAT-SAF-NM-002, FEAT-SAF-NM-003, FEAT-SAF-NM-005.
**Decisions:** D-RBAC-11.
**SSOT refs:** see SSOT §4.1; §4.3; §6 D-RBAC-11.

### FEAT-SAF-NM-002 — Reporter Identity Visibility

**Priority:** V1
**User story:** As a Master or authorized Safety user, I can see who reported a near miss so follow-up and rework can be handled clearly.
**Acceptance criteria:**
- Stored: reporter's CrewId + name (full audit data).
- Master and authorized users within vessel scope can see reporter name, rank, and user reference.
- The UI and PDF must not show `Anonymous Reporter`, `identity withheld`, or "Reporter identity is masked" wording.
- Reporter details remain in field history/audit trail.
**Dependencies:** FEAT-SAF-NM-001, FEAT-SAF-RBAC-005.
**Decisions:** D-GAP-J1.
**SSOT refs:** see SSOT §6 D-GAP-J1.

### FEAT-SAF-NM-003 — Near Miss Office Comments + Priority Decision

**Priority:** V1
**User story:** As the office reviewer, I need one Office Comments page to confirm priority, correct category/immediate cause if needed, accept the report, or send it back to the vessel for rework.
**Acceptance criteria:**
- Auto-classifier at submission suggests LOW or HIGH based on Category, immediate-cause hints, description, and severity.
- PIC accepts LOW and MEDIUM cases; DPA accepts HIGH cases.
- `Accept` saves priority, category tag, immediate cause, and office comment.
- `Send to Rework` sends the item back to the vessel side with a required reason.
- LOW → close with explanatory note.
- HIGH → preventive measures with timeline and fleet alert within 1 week (FEAT-SAF-NM-006).
- Priority field stored on `vims_safety_incident.near_miss_priority`.
**Dependencies:** FEAT-SAF-NM-001, FEAT-SAF-NM-006.
**Decisions:** D-GAP-R22.
**SSOT refs:** see SSOT §6 D-GAP-R22.

### FEAT-SAF-NM-004 — Near Miss Lightweight Record Review

**Priority:** V1
**User story:** As the near-miss handler, I need a reduced review surface with category tag and immediate-cause selection, no mandatory incident-style analysis workspace, so submission is frictionless.
**Acceptance criteria:**
- Category tag and immediate-cause selection only; no IMO A.884(21) 7/8-domain checklist.
- No mandatory System Action — Lessons Learned + Immediate Action only; System Action optional.
- Bias guards 1, 2, 3 still apply; bias guards 4, 5, 6, 7, 8 skipped for LOW; applied for HIGH.
- No mandatory physical verification.
- PIC (not DPA) closes.
**Dependencies:** FEAT-SAF-NM-003, FEAT-SAF-INC-020.
**Decisions:** §4.3 SSOT.
**SSOT refs:** see SSOT §4.3; §4.4.

### FEAT-SAF-NM-005 — Near Miss Minimum Detail

**Priority:** V1
**User story:** As the system, I enforce minimum detail on near miss submissions so records are useful without limiting how many valid reports a user can submit in a day.
**Acceptance criteria:**
- Each submission requires description ≥ 100 characters + severity selected.
- No daily near-miss submission cap.
**Dependencies:** FEAT-SAF-NM-001, FEAT-SAF-XMOD-002.
**Decisions:** D-GAP-M38, D-GAP-M26.
**SSOT refs:** see SSOT §6 D-GAP-M38; D-GAP-M26.

### FEAT-SAF-NM-006 — Fleet Alert within 1 Week for High-Priority Near Miss

**Priority:** V1
**User story:** As DPA, I need HIGH-priority near misses to generate a fleet alert within 1 week so sister vessels learn before the next parallel event.
**Acceptance criteria:**
- On HIGH classification: auto-drafts an anonymised fleet-alert title/body from the Near Miss record.
- DPA can use `[Issue Circular/Alert]` to open the existing VIMS Circular create page with only title/body prefilled.
- DPA completes all remaining Circular fields manually and publishes through the existing Circular module workflow; Safety does not direct-create or direct-publish the Circular record.
- Dashboard counter: "High-priority near-miss alerts due this week".
- If not issued within 7 days: flag on DPA dashboard (no hard block; PIC borrows lessons per D-RBAC-08).
- Vessel + crew names anonymised per D-GAP-M08 before inclusion in circular.
**Dependencies:** FEAT-SAF-NM-003, FEAT-SAF-RBAC-006.
**Decisions:** D-GAP-R22, D-CFG-04, D-GAP-M08.
**SSOT refs:** see SSOT §6 D-GAP-R22; D-CFG-04.

---

## 6. Safety Committee Meeting

SCM aligns with KSM SSQE Manual Rev 01 Feb 2026 §9. V1 supports Regular monthly cadence and Ad-Hoc meetings; same form, same PDF template, Master/CO host authority via `meeting_type`.

### FEAT-SAF-SCM-001 — SCM Regular (Monthly Cadence)

**Priority:** V1
**User story:** As Master or CO, I create a Regular monthly SCM record per SSQE §9 cadence so compliance obligations are met.
**Acceptance criteria:**
- Cadence counter: next meeting due 30 days from prior SCM closure timestamp (D-GAP-M22).
- `meeting_type='REGULAR'`.
- One Regular meeting expected per calendar month per vessel.
- Overdue flag at 28 days; hard overdue at 30+ days.
**Dependencies:** FEAT-SAF-SCM-003, FEAT-SAF-SCM-004.
**Decisions:** §5, D-GAP-M-ADHOC, D-GAP-M22.
**SSOT refs:** see SSOT §5; §6 D-GAP-M-ADHOC.

### FEAT-SAF-SCM-002 — SCM Ad-Hoc (Host-Triggered)

**Priority:** V1
**User story:** As Master or CO, I can call an Ad-Hoc SCM for major incidents or important information so significant events can be discussed outside the monthly cycle.
**Acceptance criteria:**
- `meeting_type='AD_HOC'`.
- Does NOT replace the monthly Regular meeting.
- Cadence counter + Closed-Since-Last snapshot anchor on last SCM closure timestamp **regardless of type** (D-GAP-M22).
- Same form, PDF, RBAC as Regular.
- Master or CO creates directly using the SCM host meeting-type selector.
**Dependencies:** FEAT-SAF-SCM-003, FEAT-SAF-SCM-004, FEAT-SAF-SCM-006.
**Decisions:** D-GAP-M-ADHOC, D-GAP-M22.
**SSOT refs:** see SSOT §6 D-GAP-M-ADHOC; D-GAP-M22.

### FEAT-SAF-SCM-003 — SCM Form (Legacy Structure)

**Priority:** V1
**User story:** As CO preparing minutes, I need the SCM form to match the legacy `vw_GetSCM_Master` structure so historical-new consistency is preserved.
**Acceptance criteria:**
- Old reserved Section 2 is removed; former Sections 3-10 are renumbered to Sections 2-9.
- Section 7 "PSC Findings & Corrective Measures" is the single place where finding/corrective-measure rows are printed.
- SOI feed summary shows count + coverage-% figures when SOI data exists; it must not print the old "Section 7 auto-answer NO" line when no SOI inspections exist.
- Open SOI finding details are not duplicated in the SOI feed; Section 7 remains authoritative for findings and corrective measures.
- Free-text fields min 20 chars each.
- PDF signature block: plain Master Signature and Chief Officer Signature lines only. SCM does not capture attendee digital signatures.
**Dependencies:** FEAT-SAF-SOI-020, FEAT-SAF-AUDIT-003.
**Decisions:** D-PDF-03b, D-SOI-14.
**SSOT refs:** see SSOT §5.3; §6 D-PDF-03b.

### FEAT-SAF-SCM-004 — SCM Host Creation by Master/CO, Office Comment Closure

**Priority:** V1
**User story:** As Master or CO, I can host and prepare SCM minutes; as office reviewer, I add the Office Comment and close the meeting so final shore review is clear.
**Acceptance criteria:**
- `SAF_F_003` + `SAF_P_*` IDs: Master and CO have Create + Edit host authority until office comment closes the meeting.
- Ad-Hoc meetings allow Master or CO to create directly with a mandatory trigger reason.
- PDF is downloadable after meeting creation; it does not wait for Master sign-off.
- Office Comment is the closure event. DPA, FM, Shore HOD, and Marine Superintendent profile `407EF017-0F1C-EF11-A9F1-F348983BAE6B` can save Office Comment.
- Saving Office Comment sets state to Closed and prevents further vessel-side edits.
- Closed-Since-Last snapshot cutoff = office comment closure timestamp for new SCM records; legacy Master sign-off timestamps remain valid for historical records (D-GAP-M22).
**Dependencies:** FEAT-SAF-RBAC-005.
**Decisions:** D-RBAC-06, D-GAP-M22.
**SSOT refs:** see SSOT §3.4; §6 D-RBAC-06.

### FEAT-SAF-SCM-005 — WRH Attendance Warn-Don't-Block

**Priority:** V1
**User story:** As Master, CO, or office reviewer, when an SCM attendee has missing or non-compliant WRH data I want a warning (not a block) so meeting recording and office closure are never prevented by roster sync timing.
**Acceptance criteria:**
- On attendance save/display: live join to `vims_wrh_*` for each listed attendee.
- If WRH data missing for attendee: row flagged "WRH data unavailable"; warning shown; do NOT block.
- If WRH indicates non-compliance (insufficient rest): row flagged with amber badge; warning shown; do NOT block.
- Timezone from `wrh_ship_time_config` per D-GAP-M26.
- `vims_safety_scm_attendance` row stores WRH snapshot values for audit and PDF.
- Office users can view the Attendance + WRH snapshot. Only Master/CO can edit attendance before closure.
**Dependencies:** FEAT-SAF-XMOD-002.
**Decisions:** D-GAP-M11, D-GAP-M26.
**SSOT refs:** see SSOT §6 D-GAP-M11; D-GAP-M26.

### FEAT-SAF-SCM-006 — Closed-Since-Last-SCM Summary Block

**Priority:** V1
**User story:** As DPA, I need a "Closed-Since-Last-SCM" summary block at the top of every SCM so closed findings get for-record visibility without cluttering main discussion.
**Acceptance criteria:**
- Summary block placed between Attendance and Section 8 of SCM.
- Lists findings closed by SO + Master since prior closed SCM timestamp (D-GAP-M22).
- For-record only; no discussion required unless DPA flags.
- Each row links to source SOI finding (unique-ID linkage via FEAT-SAF-SOI-008).
- Snapshot cutoff is unambiguous through reschedules and Ad-Hoc meetings. New records anchor on office comment closure; legacy records may anchor on Master sign-off timestamp (D-GAP-M22).
**Dependencies:** FEAT-SAF-SOI-020, FEAT-SAF-SCM-003.
**Decisions:** D-SOI-14, D-GAP-M22.
**SSOT refs:** see SSOT §2C.14; §6 D-GAP-M22.

### FEAT-SAF-SCM-007 — SCM SOI Overdue Visibility (Warning Only)

**Priority:** V1
**User story:** As Master, CO, or office reviewer, I want overdue SOI areas visible in SCM so the committee can discuss them without blocking meeting creation, PDF export, or office closure.
**Acceptance criteria:**
- SCM displays specific overdue areas per D-SOI-04 where available.
- Overdue SOI areas do not block meeting creation, meeting editing, PDF download, or Office Comment closure.
- Once overdue areas are cleared, warning badges disappear from new SCM snapshots.
- Surfaces on dashboard before the meeting so Master is forewarned.
**Dependencies:** FEAT-SAF-SOI-005, FEAT-SAF-SCM-004.
**Decisions:** D-GAP-M20, D-SOI-04.
**SSOT refs:** see SSOT §6 D-GAP-M20.

### FEAT-SAF-SCM-008 — Agenda + Action-Item Tracking

**Priority:** V1
**User story:** As Master, I track agenda items and action items with owners and due dates so accountability persists to the next SCM.
**Acceptance criteria:**
- `vims_safety_scm_agenda` table stores agenda items + suggestions / recommendations.
- Action items carry owner (CrewId), due date, status (Open / In Progress / Closed / Carried Forward).
- Open items auto-carry-forward to next SCM (matches SSQE §4.5.2 closing paragraph).
- Overdue action items flagged on DPA dashboard.
- Agenda editing is restricted to Master or Chief Officer and stops after Office Comment closure.
**Dependencies:** FEAT-SAF-SCM-003.
**Decisions:** §5.4 SSOT.
**SSOT refs:** see SSOT §5.4.

---

## 7. Safety Officer Inspection

SOI is the 4th V1 sub-feature per D-SOI-01. Paper-first, no-scan (D-GAP-E4). 13 areas × 329 items (12 physical areas incl. new Compressor House sub-area + Section 12 Cross-cutting Safety & Culture).

### The 13 inspection areas

| # | Area | Items | Source |
|---|------|-------|--------|
| 1 | External Deck Structure | 26 | SQE S 608 |
| 2 | Accommodation | 17 | SQE S 608 |
| 3 | Navigating Bridge & Monkey Island | 16 | SQE S 608 |
| 4 | Electrical Safety | 16 | SQE S 608 |
| 5 | Engine Room & Work Shop | 37 | SQE S 608 |
| 6 | Other Machinery Spaces (Steering Gear + Emergency Generator Room + Battery Room + CO₂ Room sub-areas) | ~30 | SQE S 608 |
| 7 | All Stores (Chemical Locker etc.) | ~35 | SQE S 608 |
| 8 | Galley / Cold Rooms | ~30 | SQE S 608 |
| 9 | All Lifting Equipment (Cranes) | ~25 | SQE S 608 |
| 10 | Mooring & Access Equipment | ~40 | SQE S 608 |
| 11 | CO₂ Room & Fixed Smothering Systems | ~10 | SQE S 608 |
| 12 | Compressor House (added per seed CSV) | derived | Seed data `soi_checklist_v1.csv` |
| 13 | **Cross-cutting Safety & Culture** (Section 12 in form, 13th area in DB) | 12 | COSWP Ch 13 + D-38 + QEOHS-VSL-HSSE-10 |

Seed CSV at `safety-reference-data/soi_checklist_v1.csv` (329 rows — 317 baseline + 12 cross-cutting) loaded into `master_soi_area` (13 rows) + `master_soi_area_item` (329 rows) at install per D-GAP-C3.

### FEAT-SAF-SOI-001 — 13-Area Inspection Taxonomy

**Priority:** V1
**User story:** As DPA, I maintain the 13-area taxonomy so every vessel inspects the same regulatory coverage.
**Acceptance criteria:**
- `master_soi_area` seeded with 13 rows (12 physical + Section 12 Cross-cutting Safety & Culture).
- `master_soi_area_item` seeded with 329 rows from `safety-reference-data/soi_checklist_v1.csv` (columns: `area_id, area_name, subsection_id, subsection_name, item_number, description, tier`).
- Tier ∈ {High, Med, Low}.
- DPA-only edit rights (D-CFG-01 pattern).
**Dependencies:** FEAT-SAF-SOI-003, FEAT-SAF-RBAC-008.
**Decisions:** D-SOI-13, D-SOI-16, D-GAP-C3.
**SSOT refs:** see SSOT §2C.5; §6 D-GAP-C3.

### FEAT-SAF-SOI-002 — Area-Applicability Toggle + Audit Log

**Priority:** V1
**User story:** As Master, I request `applicable=false` for an area that doesn't apply to my vessel (e.g., CO₂ room on non-CO₂ vessel); as DPA, I approve with reason captured.
**Acceptance criteria:**
- `vims_safety_soi_vessel_area_map` stores `applicable` flag per vessel × area.
- Toggle from true → false requires Master request + DPA approval.
- `vims_safety_soi_applicability_log` captures: vessel, area, decision, Master signature, DPA signature, reason text, timestamp.
- Non-applicable areas do NOT count toward 90-day compliance counter (D-SOI-12).
**Dependencies:** FEAT-SAF-SOI-001, FEAT-SAF-AUDIT-003.
**Decisions:** D-SOI-12, D-GAP-M19.
**SSOT refs:** see SSOT §2C.7; §6 D-GAP-M19.

### FEAT-SAF-SOI-003 — Versioned Checklist Templates

**Priority:** V1
**User story:** As DPA, I maintain versioned checklist templates so historical inspections stay on their original schema and new versions apply only forward.
**Acceptance criteria:**
- `master_soi_checklist_version` stores version (semver), effective date, DPA approver.
- Vessel-assignable at onboarding; reassignable with DPA approval.
- Historical inspections grandfather on their original version (D-EDGE-11 pattern).
- Checklist template reassign mid-inspection: in-flight inspection freezes on OLD version; new version applies only to NEXT cycle (D-GAP-M05).
**Dependencies:** FEAT-SAF-SOI-001, FEAT-SAF-AUDIT-005.
**Decisions:** D-SOI-05, D-GAP-M05, D-EDGE-11.
**SSOT refs:** see SSOT §2C.6; §6 D-GAP-M05.

### FEAT-SAF-SOI-004 — Safety Officer + Alternate Assignment

**Priority:** V1
**User story:** As Master, I confirm CO as Safety Officer (default per SSQE §4.5.1) or toggle 2/E as alternate so role assignment matches vessel reality.
**Acceptance criteria:**
- CO is default Safety Officer; Master may toggle 2/E as alternate per D-SOI-02.
- Safety Officer must NOT be Master (COSWP 13.3.2.3).
- Role persists; new CO on rotation inherits open SOI findings / in-flight inspection (D-GAP-A4 — no Acting-*).
- Stop-work authority (D-SOI-03) explicitly deferred to V2; use Incident/Near Miss flow for urgent cases (D-GAP-E6).
**Dependencies:** FEAT-SAF-RBAC-004, FEAT-SAF-SOI-018.
**Decisions:** D-SOI-02, D-SOI-03, D-GAP-A4, D-GAP-E6.
**SSOT refs:** see SSOT §2C.3; §6 D-GAP-A4.

### FEAT-SAF-SOI-005 — 90-Day Hard Ceiling + 80-Day Amber

**Priority:** V1
**User story:** As DPA, I enforce a 90-day hard ceiling per applicable inspection area so the regulatory ceiling (COSWP 13.4.4.1) is never breached.
**Acceptance criteria:**
- Hard ceiling: 90 days per applicable area without inspection = overdue (dashboard red flag).
- Soft warning: 80 days = amber flag, email to CO + Master.
- Target: 1/3 of applicable areas per month (SSQE §4.5.2), but SO chooses which specific areas each cycle.
- No strict per-month segmentation; any 3-consecutive-months span must cover all applicable areas.
- Overdue SOI areas surface in SCM as warning/visibility only (FEAT-SAF-SCM-007).
**Dependencies:** FEAT-SAF-SCM-007, FEAT-SAF-DASH-005.
**Decisions:** D-SOI-04.
**SSOT refs:** see SSOT §2C.8.

### FEAT-SAF-SOI-006 — Paper-First Checklist Generation (PDF or Excel)

**Priority:** V1
**User story:** As Safety Officer, I select areas for this cycle; system generates a dynamic PDF or Excel checklist with a unique checklist ID; I download it; fieldwork runs on paper — no scan upload required (D-GAP-E4).
**Acceptance criteria:**
- SO chooses output format: PDF or Excel.
- Header: vessel, cycle, planned date, SO, Assistant, trainees, areas covered.
- Body: each selected area's items + Yes/No/NA columns + Section 12 (if included this cycle).
- Footer: signature lines for SO, Assistant, Master (paper signatures; wet-signed).
- Unique checklist ID printed on every page (format TBD at build per D-GAP-E3).
- Download flips state to `Downloaded`; idempotent (D-GAP-E1).
- **No scan upload column in schema** — paper permanently filed in ship's SMS filing system (D-GAP-E4).
**Dependencies:** FEAT-SAF-SOI-007, FEAT-SAF-SOI-008, FEAT-SAF-SOI-014.
**Decisions:** D-SOI-10, D-GAP-E4, D-GAP-E1.
**SSOT refs:** see SSOT §2C.9; §2C.19; §6 D-GAP-E4.

### FEAT-SAF-SOI-007 — Idempotent Download + Reprint

**Priority:** V1
**User story:** As Safety Officer, I can re-download the checklist freely (e.g., to reprint after a coffee spill) without the state flipping or audit noise.
**Acceptance criteria:**
- Second and subsequent downloads are no-ops on state (still `Downloaded`).
- Each download re-issues same PDF/Excel with same unique checklist ID.
- Reprint count logged in `vims_safety_soi_inspection.reprint_count` for audit.
**Dependencies:** FEAT-SAF-SOI-006.
**Decisions:** D-GAP-E1.
**SSOT refs:** see SSOT §6 D-GAP-E1.

### FEAT-SAF-SOI-008 — Unique Checklist ID Linkage

**Priority:** V1
**User story:** As PSC / auditor, I can trace any registered finding back to the exact paper checklist in the ship's SMS filing system via a unique checklist ID so paper-first traceability is preserved.
**Acceptance criteria:**
- Unique checklist ID generated at State 2 (Downloaded); printed on every page of PDF/Excel.
- SO enters the same ID on finding registration (State 4) to link digital → paper.
- ID format to be specified at build (D-GAP-E3 notes either reuse or new-on-recovery).
- Paper in ship SMS filing system = authoritative per-item record; digital = findings + link.
**Dependencies:** FEAT-SAF-SOI-006, FEAT-SAF-SOI-011.
**Decisions:** D-GAP-E4, D-SOI-10.
**SSOT refs:** see SSOT §2C.9; §6 D-GAP-E4.

### FEAT-SAF-SOI-009 — Cross-Functional Assistant Hard Enforcement

**Priority:** V1
**User story:** As Safety Officer, I must pick an Assistant from a different department (SSQE §4.5.2 bias-reduction) — hard-enforced, no override.
**Acceptance criteria:**
- Assistant name + department pulled from CMS via live join (D-GAP-I2 same-DB, no staleness).
- Rule: Assistant's department ≠ Safety Officer's department (if CO is SO → Assistant from engine side; if 2/E is alt SO → Assistant from deck).
- Cannot submit inspection without valid cross-functional pairing.
- No override mechanism (D-GAP-M18 — single-department exception not required; vessels always have Deck + Engine).
- New joiner onboard but not yet in CMS roster: Master defers inspection or selects a different assistant (no manual override per D-GAP-I2).
**Dependencies:** FEAT-SAF-XMOD-003.
**Decisions:** D-SOI-08, D-GAP-I2, D-GAP-M18.
**SSOT refs:** see SSOT §2C.10; §6 D-GAP-I2; D-GAP-M18.

### FEAT-SAF-SOI-010 — Up to 3 Crew Trainees per Inspection

**Priority:** V1
**User story:** As Safety Officer, I can add up to 3 crew trainees by CrewId so training-through-participation is formally tracked.
**Acceptance criteria:**
- `vims_safety_soi_trainee` child table holds up to 3 trainee CrewId FKs per inspection.
- System computes per-crew "inspections accompanied" counter + per-vessel "crew rotation coverage %" over rolling 12 months.
- Surfaced on Crew dashboard (FEAT-SAF-SOI-022) and in SCM analytics.
- Trainees do not sign the paper (D-GAP-M15 — only SO + Assistant sign paper; Master signs digitally at approval).
**Dependencies:** FEAT-SAF-SOI-022, FEAT-SAF-XMOD-003.
**Decisions:** D-SOI-09, D-GAP-M15.
**SSOT refs:** see SSOT §2C.11; §6 D-GAP-M15.

### FEAT-SAF-SOI-011 — Finding Registration (No Per-Item Responses in DB)

**Priority:** V1
**User story:** As Safety Officer returning to VIMS after fieldwork, I register ONLY findings digitally and enter the unique checklist ID so per-item Yes/No responses stay on paper (D-GAP-E4).
**Acceptance criteria:**
- Finding fields: `finding_id · area_id · item_id · description · evidence_photo_id · mscat_cause_codes (optional) · priority (High/Med/Low) · proposed_action · assigned_to · due_date · status`.
- Per-item Yes/No responses live ONLY on paper in ship SMS filing — never in DB, never as scan upload (D-GAP-E4).
- On submit, all selected areas stamp "Last Inspected = today" (resets 90-day counter).
- No auto-escalation to Near Miss / Incident / PMS Defect (D-SOI-06). HIGH severity findings trigger nudge per FEAT-SAF-SOI-017.
- Submit-with-no-findings path: SO can close inspection with zero findings; areas still stamp as inspected.
**Dependencies:** FEAT-SAF-SOI-008, FEAT-SAF-SOI-016, FEAT-SAF-SOI-017.
**Decisions:** D-SOI-10, D-SOI-06, D-GAP-E4.
**SSOT refs:** see SSOT §2C.9; §2C.12; §6 D-GAP-E4.

### FEAT-SAF-SOI-012 — Partial Submission (Per-Area Stamping)

**Priority:** V1
**User story:** As Safety Officer, if I completed 3 out of 5 selected areas this cycle, I can submit findings for just those 3 and come back later for the remaining 2 under the same unique checklist ID.
**Acceptance criteria:**
- Inspection supports partial submission: submitted areas stamp as inspected (90-day counter reset per area); remaining areas stay in `Downloaded` state.
- Same unique checklist ID remains valid for remaining areas.
- Dashboard shows "2 of 5 areas pending" until all areas submitted or cancelled.
- Per-area counter already defined in D-SOI-04.
**Dependencies:** FEAT-SAF-SOI-006, FEAT-SAF-SOI-011.
**Decisions:** D-GAP-E2, D-SOI-04.
**SSOT refs:** see SSOT §6 D-GAP-E2.

### FEAT-SAF-SOI-013 — Lost / Damaged Paper Recovery

**Priority:** V1
**User story:** As Safety Officer, if my paper checklist is lost or damaged I can re-download the same area selection (reuses existing unique checklist ID or issues a new one — per build decision) and re-conduct fieldwork on fresh paper.
**Acceptance criteria:**
- Re-download path available pre-submission.
- Loss event logged in inspection notes (mandatory reason).
- Build-time decision: reuse ID or issue new (D-GAP-E3 defers to implementation).
- Recovery is pragmatic, not punitive — no approval required.
**Dependencies:** FEAT-SAF-SOI-006.
**Decisions:** D-GAP-E3.
**SSOT refs:** see SSOT §6 D-GAP-E3.

### FEAT-SAF-SOI-014 — Section 12 Once Per 3-Month Cycle

**Priority:** V1
**User story:** As Safety Officer, I evaluate Section 12 "Cross-cutting Safety & Culture" once per 3-month cycle (not every individual SOI event) so duplicate responses are avoided.
**Acceptance criteria:**
- Section 12 (12 items) applied once per 3-month cycle; SO decides which SOI event in the cycle carries it.
- System prompts if no SOI event in current quarter has included Section 12.
- Items 12.10 and 12.11 are text-response prompts; others are Yes/No/NA.
- Rendered as distinct section in generated checklist (PDF/Excel) regardless of which physical areas were selected.
**Dependencies:** FEAT-SAF-SOI-001, FEAT-SAF-SOI-006.
**Decisions:** D-GAP-M23, D-SOI-16.
**SSOT refs:** see SSOT §2C.5; §6 D-GAP-M23.

### FEAT-SAF-SOI-015 — Finding Closure (SO → Master)

**Priority:** V1
**User story:** As Safety Officer, I mark a finding `pending_closure`; as Master, I approve to move it to `closed` — or reject with a mandatory written reason.
**Acceptance criteria:**
- Status lifecycle: Open → Pending Closure → Master-Approved → Closed. Carried Forward possible at each SCM.
- Master rejection: mandatory written reason; finding returns to Open; reason appended to finding notes (D-GAP-M21).
- DPA safety net: DPA may re-open closed findings.
- Closed-since-last-SCM snapshot populates per FEAT-SAF-SCM-006.
- Field edit history per D-EDGE-10 applies.
**Dependencies:** FEAT-SAF-SOI-011, FEAT-SAF-SCM-006, FEAT-SAF-AUDIT-002.
**Decisions:** D-SOI-07, D-GAP-M21.
**SSOT refs:** see SSOT §2C.13; §6 D-GAP-M21.

### FEAT-SAF-SOI-016 — HIGH Severity Finding — Photo Required

**Priority:** V1
**User story:** As DPA, I require at least one photo on every HIGH-severity SOI finding so evidence chain is defensible at audit.
**Acceptance criteria:**
- On finding save: if `priority='High'`, system enforces ≥1 photo attachment.
- MED / LOW = optional photos.
- Enforcement at serializer validation (server-side).
**Dependencies:** FEAT-SAF-SOI-011.
**Decisions:** D-GAP-M24.
**SSOT refs:** see SSOT §6 D-GAP-M24.

### FEAT-SAF-SOI-017 — HIGH Severity System Nudge ("Incident-Worthy?")

**Priority:** V1
**User story:** As Safety Officer saving a HIGH-severity finding, I see a system nudge "This looks incident-worthy. Create one now? [Yes / No + reason]" so buried HIGH findings are caught without violating no-auto-escalation.
**Acceptance criteria:**
- Nudge fires on save when `priority='High'`.
- User choice: Yes → creates linked Incident (pre-fills from finding); No → mandatory reason field, recorded in finding notes.
- Does NOT auto-create an Incident (SO judgement retained per D-SOI-06).
- No auto-escalation to PMS Defect (D-GAP-I1).
**Dependencies:** FEAT-SAF-SOI-016, FEAT-SAF-INC-001.
**Decisions:** D-GAP-M16, D-SOI-06.
**SSOT refs:** see SSOT §6 D-GAP-M16.

### FEAT-SAF-SOI-018 — Life-Threat Escalation via Incident/Near Miss

**Priority:** V1
**User story:** As Safety Officer, if I discover a life-threat hazard mid-inspection I create a parallel Incident or Near Miss which triggers RED-band notifications while the SOI continues once the hazard is controlled.
**Acceptance criteria:**
- No new "Urgent SOI" schema — reuses Incident/Near Miss flow.
- Slack to DPA/FM fires per RED-band notification rules.
- SOI inspection state does not change; resumes once hazard controlled.
- Stop-work authority remains deferred (D-SOI-03 V2).
**Dependencies:** FEAT-SAF-INC-001, FEAT-SAF-NM-001.
**Decisions:** D-GAP-E6, D-SOI-03.
**SSOT refs:** see SSOT §6 D-GAP-E6.

### FEAT-SAF-SOI-019 — Repeat-Finding Badge + Dashboard Metric

**Priority:** V1
**User story:** As Master / DPA, I see a visual badge on any finding that repeats a prior finding and a dashboard tile of top-5 repeat findings per vessel so systemic issues surface.
**Acceptance criteria:**
- Badge on record: "Repeat — Nth occurrence".
- Dashboard tile: "Top 5 repeat findings per vessel" — rolling 12 months.
- Repeat match = same area + same item_id + similar description (fuzzy match per FTS engine — build-time deferral).
- Surfaced at both discovery (badge) and review (dashboard) layers.
**Dependencies:** FEAT-SAF-DASH-003.
**Decisions:** D-GAP-M17.
**SSOT refs:** see SSOT §6 D-GAP-M17.

### FEAT-SAF-SOI-020 — SOI → SCM Auto-Feed (Split Model)

**Priority:** V1
**User story:** As DPA, I need SOI open findings to populate the SCM "Safety Observations for the Month" table, and closed findings to appear in the "Closed-Since-Last-SCM" summary block — per the split model.
**Acceptance criteria:**
- Open findings since last SCM → populate "Safety Observations for the Month" table.
- Closed findings since last SCM closure timestamp → populate new "Closed Items" summary block at top of SCM (D-GAP-M22 cutoff).
- Both blocks carry SOI inspection reference number (format `SOI/{VesselCode}/{YY}/{NN}`) and hyperlink to source record.
- Section 7 SCM question auto-answers Yes if any inspection occurred in period, with count + coverage-% figures.
**Dependencies:** FEAT-SAF-SCM-006, FEAT-SAF-SCM-003.
**Decisions:** D-SOI-14, D-GAP-M22.
**SSOT refs:** see SSOT §2C.14; §6 D-GAP-M22.

### FEAT-SAF-SOI-021 — Default Finding Assignee = SO

**Priority:** V1
**User story:** As Safety Officer, if I leave the finding assignee blank the system defaults to me so ownership is always clear; Master can re-assign at approval time.
**Acceptance criteria:**
- `assigned_to` defaults to SO's CrewId when left blank.
- Master may re-assign to any crew member at approval time.
- Re-assignment logged in `vims_safety_field_history`.
**Dependencies:** FEAT-SAF-SOI-011, FEAT-SAF-SOI-015.
**Decisions:** D-GAP-E7.
**SSOT refs:** see SSOT §6 D-GAP-E7.

### FEAT-SAF-SOI-022 — Crew Rotation Coverage % Metric

**Priority:** V1
**User story:** As DPA, I see per-vessel crew rotation coverage % (crew who have accompanied ≥1 inspection in rolling 12 months) so training-through-participation is evidenced at audit.
**Acceptance criteria:**
- Metric: `count(distinct crew with ≥1 SOI accompaniment in 12m) / total active crew × 100`.
- Surfaced on vessel dashboard and in SCM analytics.
- Supports SSQE training-through-participation intent at flag-state audits.
**Dependencies:** FEAT-SAF-SOI-010, FEAT-SAF-DASH-001.
**Decisions:** D-SOI-09.
**SSOT refs:** see SSOT §2C.11; §2C.17.

### FEAT-SAF-SOI-023 — Paper-Signature Capture (SO + Assistant mandatory)

**Priority:** V1
**User story:** As the custody-of-findings rule, SO and Assistant sign the paper checklist wet-ink; Master counter-signs digitally at approval stage.
**Acceptance criteria:**
- SO + Assistant paper-signature is mandatory (printed on checklist footer).
- Master counter-signs digitally at approval stage (not on paper) per D-GAP-M15.
- Trainees do NOT sign.
- Digital Master signature uses hybrid model per D-GAP-D1 (typed name + timestamp + device fingerprint).
**Dependencies:** FEAT-SAF-SOI-015, FEAT-SAF-AUDIT-003.
**Decisions:** D-GAP-M15, D-GAP-D1.
**SSOT refs:** see SSOT §6 D-GAP-M15; D-GAP-D1.

### FEAT-SAF-SOI-024 — Inherit CO-Role on Rotation

**Priority:** V1
**User story:** As incoming CO on rotation, I inherit any open SOI findings and in-flight inspections from the previous CO so continuity is preserved without handover chains.
**Acceptance criteria:**
- SOI `safety_officer_crew_id` lookup resolves via CO-role assignment, not static CrewId at creation.
- No 2/E alternate succession except by explicit Master toggle per D-SOI-02.
- No Acting-CO concept (D-GAP-A4).
- Open findings / in-flight inspection become the incoming CO's responsibility automatically.
**Dependencies:** FEAT-SAF-SOI-004, FEAT-SAF-RBAC-004.
**Decisions:** D-GAP-A4, D-SOI-02.
**SSOT refs:** see SSOT §6 D-GAP-A4.

---

## 8. Cross-Module Contracts

Same-DB (`ksm_marine_live`) live joins per D-GAP-I2 — no ETL, no staleness. All integrations are backed by direct FK / live-join; none use sync pipelines.

### FEAT-SAF-XMOD-001 — Safety ↔ Reporting (MSC-MEPC.3 Position Live Join)

**Priority:** V1
**User story:** As an investigator, the MSC-MEPC.3/Circ.4 export pulls position from the nearest Daily Report via a same-DB live join so no sync staleness exists.
**Acceptance criteria:**
- Live join to `vims_daily_report` table; no ETL.
- Window: ±12h from incident timestamp (D-GAP-M09).
- Daily Report missing: manual entry accepted; record flagged `awaiting_daily_report_match` (D-GAP-M10); submission not blocked.
- User may edit auto-fill (more recent position available).
**Dependencies:** FEAT-SAF-PDF-002, FEAT-SAF-INC-041.
**Decisions:** D-GAP-I2, D-GAP-M09, D-GAP-M10, D-DNV-12.
**SSOT refs:** see SSOT §6 D-GAP-I2; D-GAP-M09.

### FEAT-SAF-XMOD-002 — Safety ↔ WRH (SCM Attendance + Fatigue Lookback)

**Priority:** V1
**User story:** As Master, CO, or office reviewer viewing an SCM, WRH rest-hour compliance per attendee is surfaced (warn-don't-block); as an investigator on a personal-injury incident, WRH 96-hour lookback per FEAT-SAF-INC-010 uses same live join.
**Acceptance criteria:**
- Live join to `vims_wrh_*` tables; no ETL.
- SCM attendance: warn-don't-block on missing / non-compliant WRH (D-GAP-M11).
- Timezone: UTC in DB; vessel-local resolved via `wrh_ship_time_config` (D-GAP-M26).
- Build-time deferral: WRH lookback window / query timeout settings.
**Dependencies:** FEAT-SAF-SCM-005, FEAT-SAF-INC-010.
**Decisions:** D-GAP-M11, D-GAP-M26.
**SSOT refs:** see SSOT §6 D-GAP-M11; D-GAP-M26.

### FEAT-SAF-XMOD-003 — Safety ↔ CMS (Live Join for SOI Assistant + Crew)

**Priority:** V1
**User story:** As Safety Officer, the Assistant picker and trainee picker pull from CMS via live join; as an investigator, crew assignment / qualifications pull from the same join.
**Acceptance criteria:**
- Live join to `Crew_Onboarding_History` + `Final_crew_list` (platform CMS tables).
- No staleness (D-GAP-I2 same-DB).
- Department field canonical from CMS (not free text) for FEAT-SAF-SOI-009 cross-functional rule.
- New joiner onboard but not in CMS: Master defers or picks different assistant (no manual override).
**Dependencies:** FEAT-SAF-SOI-009, FEAT-SAF-SOI-010.
**Decisions:** D-GAP-I2, D-GAP-M18.
**SSOT refs:** see SSOT §6 D-GAP-I2.

### FEAT-SAF-XMOD-004 — Safety ↔ Purchase (CA → Purchase Req Hard FK)

**Priority:** V1
**User story:** As DPA authorising a CA that requires parts, I link to a Purchase Requisition via hard FK so lifecycle integrity is preserved.
**Acceptance criteria:**
- `vims_safety_corrective_action.purchase_req_id` is a hard FK to `vims_purchase_requisition.id`.
- Purchase Requisition cannot be archived / deleted while linked to an open CA.
- Live status syncs (requisition state visible on CA detail).
- CA may close with its Physical Verification still Open (D-GAP-M03).
**Dependencies:** FEAT-SAF-INC-027, FEAT-SAF-INC-031.
**Decisions:** D-GAP-M12, D-GAP-M03.
**SSOT refs:** see SSOT §6 D-GAP-M12; D-GAP-M03.

### FEAT-SAF-XMOD-005 — Safety ↔ PMS (Decoupled)

**Priority:** V1
**User story:** As an investigator on an M-SCAT cause 12 "Inadequate Maintenance" finding, I cross-reference PMS manually — there is NO in-VIMS PMS integration (PMS is standalone).
**Acceptance criteria:**
- No FK from `vims_safety_*` to PMS tables.
- Investigator manually cross-references PMS via separate login (PMS is an independent system per D-GAP-I1).
- Equipment defect linkage from SOI findings to PMS: also manual (no FK).
- Removes the Safety ↔ PMS dependency previously noted in SSOT §2.
**Dependencies:** — (negative contract).
**Decisions:** D-GAP-I1.
**SSOT refs:** see SSOT §6 D-GAP-I1.

### FEAT-SAF-XMOD-006 — Shared Notification Queue via `master_notification`

**Priority:** V1
**User story:** As the Safety module, I write all notifications to the shared `master_notification` table so VIMS platform's notifier consumes them uniformly.
**Acceptance criteria:**
- All Slack / in-app notifications write to `master_notification` (existing VIMS master).
- Safety does NOT maintain its own notification queue.
- Slack is best-effort (D-GAP-F2); in-app is authoritative.
- No notification digest — every event is independent (D-GAP-M28).
- RED-band Slack webhook failure raises a platform-level alert (D-GAP-F4).
**Dependencies:** FEAT-SAF-INC-004.
**Decisions:** D-GAP-F2, D-GAP-M28, D-GAP-F4.
**SSOT refs:** see SSOT §6 D-GAP-F2; D-GAP-M28; D-GAP-F4.

---

## 9. PDF Generation

### FEAT-SAF-PDF-001 — 10-Section Incident PDF (Formal Report)

**Priority:** V1
**User story:** As DPA, at Phase 7 acceptance the system generates the formal 10-section incident report PDF with the standard template so DPA filing, management review, and flag-state hand-off have a single document.
**Acceptance criteria:**
Ten sections per D-GAP-R09 refinement of D-PDF-01:
1. Cover + classification (SMC/MC/MI per FEAT-SAF-INC-002) + risk band (GREEN/YELLOW/RED).
2. Investigator / team credentials.
3. Evidence collected (summary table, cross-ref Chain-of-Custody per FEAT-SAF-INC-007).
4. Root-cause analysis (with Immediate/Intermediate/Root labels per FEAT-SAF-INC-018).
5. 7-point causal-factor enumeration (per KAIZEN §11.5.6.1).
6. Corrective + Preventive actions with timeline (Corrective/Preventive/Lessons taxonomy per D-GAP-R13).
7. Lessons Learnt (auto-feeds Fleet Circular).
8. Fleet notification plan.
9. Signatures per D-PDF-01: Master + DPA + [FM for RED] + page numbering + confidentiality header/footer.
10. Appendices — attachments list.
- Executive summary auto-generated from Lessons Learned.
- Cover classification aligns with IMO Casualty Investigation Code (Resolution MSC.255(84)).
**Dependencies:** FEAT-SAF-INC-002, FEAT-SAF-INC-007, FEAT-SAF-INC-018, FEAT-SAF-INC-027, FEAT-SAF-AUDIT-003.
**Decisions:** D-PDF-01, D-GAP-R09.
**SSOT refs:** see SSOT §6 D-PDF-01; D-GAP-R09.

### FEAT-SAF-PDF-002 — MSC-MEPC.3/Circ.4 Regulatory Export PDF

**Priority:** V1
**User story:** As DPA preparing flag-state hand-off, I export the MSC-MEPC.3/Circ.4 PDF with ~40% auto-filled fields so manual entry is minimised.
**Acceptance criteria:**
- "Export to MSC-MEPC.3/Circ.4 PDF" button on closed (Phase 7+) incidents.
- 5 appendices auto-populate per §2B.13:
  - App 1: investigator-entered (Phase 1–2).
  - App 2: auto from `vims_vessel_particulars`.
  - App 3: auto from STEP timeline + M-SCAT cause tree.
  - App 4: auto from Daily Report position-time match via FEAT-SAF-XMOD-001.
  - App 5: 30 standardised picklists from backend reference data.
- Manual flag-state notification deadline tracking is OUT of V1 (D-GAP-G1); DPA handles deadlines out-of-band.
**Dependencies:** FEAT-SAF-XMOD-001, FEAT-SAF-INC-041.
**Decisions:** D-DNV-12, D-GAP-G1.
**SSOT refs:** see SSOT §2B.13; §6 D-GAP-G1.

### FEAT-SAF-PDF-003 — Near Miss Lightweight PDF

**Priority:** V1
**User story:** As DPA, near miss records export as a distinct 1-2 page lightweight PDF (what-happened + suggestion + immediate action) — no investigation/cause-tree details.
**Acceptance criteria:**
- 1–2 page template; sections: Header + What Happened + Suggestion + Immediate Action + Signatures.
- No investigation / cause tree.
- Reporter identity is visible to authorized users. PDF output must not print anonymous or masked-reporter wording.
**Dependencies:** FEAT-SAF-NM-002.
**Decisions:** D-PDF-03a.
**SSOT refs:** see SSOT §6 D-PDF-03a.

### FEAT-SAF-PDF-004 — SCM PDF (Legacy Structure)

**Priority:** V1
**User story:** As CO/Master producing the SCM PDF, the layout matches the legacy `vw_GetSCM_Master` structure so historical-new consistency is preserved.
**Acceptance criteria:**
- Old reserved Section 2 is removed; former Sections 3-10 are renumbered to Sections 2-9.
- Closed-since-last summary block appears at top (per FEAT-SAF-SCM-006).
- Attendance block + WRH flags inline.
- Signature box: plain Master Signature and Chief Officer Signature lines. No attendee digital signature status and no device fingerprint text.
- Regular and Ad-Hoc use same template; meeting type printed on cover.
**Dependencies:** FEAT-SAF-SCM-003, FEAT-SAF-SCM-006.
**Decisions:** D-PDF-03b, D-GAP-M-ADHOC.
**SSOT refs:** see SSOT §6 D-PDF-03b; D-GAP-M-ADHOC.

### FEAT-SAF-PDF-005 — SOI Summary PDF (Post-Submission)

**Priority:** V1
**User story:** As Master reviewing completed SOI, the summary PDF shows areas inspected + findings table + flow-to-SCM indicator — but does NOT reproduce per-item Yes/No data (paper is authoritative).
**Acceptance criteria:**
- Auto-generated at submission.
- Cover: vessel, cycle, inspection reference, state, closure chain.
- Areas inspected with Last Inspected date stamps.
- Findings table: M-SCAT + SHELL + priority + assignee + status.
- Paper reference note: "Paper checklist: unique-ID {id}, filed in ship SMS filing system" (D-GAP-E4 — no scan).
- Does NOT reproduce per-item checklist (paper is authoritative).
- Signature block: SO + Assistant + Master (digital).
- Audit-trail footer (record ID, schema version, timestamps).
**Dependencies:** FEAT-SAF-SOI-011, FEAT-SAF-AUDIT-003.
**Decisions:** D-SOI-10, D-GAP-E4.
**SSOT refs:** see SSOT §2C.19; §6 D-GAP-E4.

### FEAT-SAF-PDF-006 — Auditor Leave-Behind ZIP Package

**Priority:** V1
**User story:** As Master preparing for vetting / PSC inspection, I configure an export scope (record types + date range) and download a ZIP with PDFs + attachments for leave-behind.
**Acceptance criteria:**
- Export scope: record types (Incidents / Near Misses / Safety Meetings / SOI) + date range.
- ZIP contents: PDFs + `attachments/` subfolder with all linked attachments.
- No crew-name redaction — full context preserved (D-GAP-M37).
- Vetting access: Master drives on-screen + PDF export for auditor (D-RBAC-10).
- DPA-owns dashboard export rights; FM read-only (D-GAP-M31 — FM dashboards yes, export no).
**Dependencies:** FEAT-SAF-PDF-001, FEAT-SAF-PDF-003, FEAT-SAF-PDF-004, FEAT-SAF-PDF-005.
**Decisions:** D-PDF-02, D-GAP-M37, D-RBAC-10, D-GAP-M31.
**SSOT refs:** see SSOT §6 D-PDF-02; D-GAP-M37.

---

## 10. Audit, Signatures, Field History

### FEAT-SAF-AUDIT-001 — Append-Only Phase Log

**Priority:** V1
**User story:** As DPA, every state change and phase transition on every incident / near miss / SOI / SCM is captured in an append-only log so ISM non-repudiation is satisfied.
**Acceptance criteria:**
- `vims_safety_incident_phase_log` append-only; no UPDATE / DELETE permitted at DB level.
- Fields: parent_id, from_state, to_state, reason, actor_crew_id, timestamp, loop_back_flag.
- Phase-log build-time deferral noted in BACKEND_STRUCTURE (shape TBD).
- Same pattern applied to SOI event state, SCM state, Near Miss state — one log table per domain or unified table (build-time decision).
**Dependencies:** FEAT-SAF-AUDIT-002.
**Decisions:** §3.3 SSOT, D-EDGE-10.
**SSOT refs:** see SSOT §3.3; §6 D-EDGE-10.

### FEAT-SAF-AUDIT-002 — Field-Level History

**Priority:** V1
**User story:** As DPA, every field edit on a safety record is captured so ISM tamper-evidence + legal-discovery are friendly.
**Acceptance criteria:**
- `vims_safety_field_history` captures old_value, new_value, field_name, editor, timestamp.
- Diff view on incident detail screen.
- Schema shape is build-time deferral (TEXT vs JSON vs typed + content_hash).
- Retention tied to parent: deleted when parent is hard-deleted (D-GAP-M33).
- No point-in-time snapshot / revert UI in V1 (D-GAP-M04).
- No column-level encryption (D-GAP-C5).
- Access log on `vims_safety_field_history` itself for tamper visibility (D-GAP-F4).
**Dependencies:** —
**Decisions:** D-EDGE-10, D-GAP-M33, D-GAP-M04, D-GAP-C5, D-GAP-F4.
**SSOT refs:** see SSOT §6 D-EDGE-10; D-GAP-M33.

### FEAT-SAF-AUDIT-003 — Hybrid Digital Signature Model

**Priority:** V1
**User story:** As Master / DPA / FM / SO, I sign via typed name + timestamp + device fingerprint in the VIMS UI; for formal PDFs intended for flag-state / auditor hand-off, a wet-signed scan is also accepted as attachment.
**Acceptance criteria:**
- Digital signature fields: typed_name, timestamp, device_fingerprint.
- Wet-signed scan upload accepted as attachment for formal PDFs.
- **No PKI / UETA compliance required in V1.**
- **No cryptographic tamper-evidence in V1** (D-GAP-D2) — no hash chains, no legal-hold.
- Non-repudiation satisfied via audit trail + backups (inherited from platform per D-GAP-G3).
**Dependencies:** FEAT-SAF-AUDIT-001.
**Decisions:** D-GAP-D1, D-GAP-D2, D-GAP-G3.
**SSOT refs:** see SSOT §6 D-GAP-D1; D-GAP-D2.

### FEAT-SAF-AUDIT-004 — 3-Year Retention + Hard-Delete Attachments

**Priority:** V1
**User story:** As DPA, safety records soft-archive at 3 years and attachments hard-delete at 3 years so storage is bounded.
**Acceptance criteria:**
- 3-year soft archive (searchable by all office users, opt-in via archive toggle per D-GAP-M32).
- Cloud-stored attachments hard-delete at 3-year mark.
- DB link reference persists; file returns 404 after purge.
- No legal-hold feature in V1 (D-GAP-G2) — DPA exports externally before cutoff when a case is open.
- Orphaned attachments hard-delete immediately when parent draft/record is deleted (D-GAP-M01).
**Dependencies:** FEAT-SAF-AUDIT-007, FEAT-SAF-DASH-008.
**Decisions:** D-SOI-11, D-GAP-G2, D-GAP-M01, D-GAP-M32.
**SSOT refs:** see SSOT §2C.15; §6 D-GAP-G2.

### FEAT-SAF-AUDIT-005 — Schema Versioning Grandfather

**Priority:** V1
**User story:** As DPA adding new M-SCAT codes in Year 2, only new records use them — old records stay on their original taxonomy version (true grandfather).
**Acceptance criteria:**
- `vims_safety_incident.schema_version` stamps record at formal-number assignment.
- Taxonomy reference data filtered by record's `schema_version` at lookup.
- No retroactive remapping of closed records.
- Legacy eMarineSoft data stays separate read-only system (D-EDGE-05).
**Dependencies:** FEAT-SAF-INC-040, FEAT-SAF-SOI-003.
**Decisions:** D-EDGE-11, D-GAP-C4, D-EDGE-05.
**SSOT refs:** see SSOT §6 D-EDGE-11; D-GAP-C4.

### FEAT-SAF-AUDIT-006 — Form Auto-Save Every 30s (IndexedDB)

**Priority:** V1
**User story:** As a reporter on a shaky satcomm link, my form auto-saves every 30 seconds to IndexedDB so I don't lose work on reconnect.
**Acceptance criteria:**
- Auto-save every 30s to browser IndexedDB.
- On reconnect / reload, form resumes from last saved state.
- Applies to all Safety module forms (Incident, Near Miss, SCM, SOI finding registration).
- Re-upload with same filename = replace in place (`vims_safety_field_history` captures old→new) per D-GAP-M02.
**Dependencies:** —
**Decisions:** D-GAP-F1, D-GAP-M02.
**SSOT refs:** see SSOT §6 D-GAP-F1; D-GAP-M02.

### FEAT-SAF-AUDIT-007 — Attachment Orphan Cleanup

**Priority:** V1
**User story:** As the platform, orphaned attachments hard-delete immediately when their parent draft or record is deleted so cloud storage doesn't bloat.
**Acceptance criteria:**
- Hard-delete from cloud storage on parent deletion — no grace period.
- `vims_safety_field_history` logs the delink event.
- Re-upload with same filename = replace in place (no auto-versioned copies per D-GAP-M02).
**Dependencies:** FEAT-SAF-AUDIT-004, FEAT-SAF-AUDIT-002.
**Decisions:** D-GAP-M01, D-GAP-M02.
**SSOT refs:** see SSOT §6 D-GAP-M01; D-GAP-M02.

---

## 11. Dashboards & Analytics

### FEAT-SAF-DASH-001 — Safety Intelligence Dashboard (Composite Score)

**Priority:** V1
**User story:** As DPA / FM, I see a composite Safety Health Score + drill-down panels (Heinrich ratio, Pareto, repeat-root-cause, SOI compliance %) on a single fleet dashboard.
**Acceptance criteria:**
- Single landing page at `/safety/dashboard`.
- Panels: Heinrich ratio (FEAT-SAF-DASH-002), repeat-root-cause radar (FEAT-SAF-DASH-003), Pareto screening (FEAT-SAF-DASH-004), SOI compliance % (FEAT-SAF-DASH-005), CA aging (FEAT-SAF-DASH-006).
- Period persistence per user session (build-time deferral).
- DPA-only export rights (FEAT-SAF-DASH-007).
**Dependencies:** FEAT-SAF-DASH-002, FEAT-SAF-DASH-003, FEAT-SAF-DASH-004, FEAT-SAF-DASH-005, FEAT-SAF-DASH-006, FEAT-SAF-DASH-007.
**Decisions:** §2B.14, D-GAP-H1.
**SSOT refs:** see SSOT §2B.14.

### FEAT-SAF-DASH-002 — Heinrich Ratio Panel + Confidence Indicator

**Priority:** V1
**User story:** As DPA, I see the per-vessel reporting-culture pyramid (fatality / minor injury / property damage / near miss / hazards) with DNV benchmark overlay and a green/amber/red confidence indicator.
**Acceptance criteria:**
- 3-year rolling window per vessel.
- Benchmark overlay: 1 / 10 / 30 / 600 / 600+ pyramid.
- "Reporting Culture Gap" warning if any layer above near-miss is missing the layers below it.
- Confidence indicator: green (≥5 incidents + ≥20 near misses in 12m) / amber (below) / red ("Insufficient data" tooltip).
- Superseded / reclassified incidents do NOT count (D-GAP-H2).
**Dependencies:** FEAT-SAF-DASH-001.
**Decisions:** D-DNV-13, D-GAP-M27, D-GAP-H2.
**SSOT refs:** see SSOT §2B.14; §6 D-GAP-M27.

### FEAT-SAF-DASH-003 — Repeat-Root-Cause Radar (Fleet + Vessel)

**Priority:** V1
**User story:** As DPA, I see two repeat-root-cause radars: fleet-level (same M-SCAT leaf 3+ times across fleet in rolling 6m) + vessel-level (same leaf 3+ times on same vessel in rolling 6m).
**Acceptance criteria:**
- Two independent radars, same panel.
- Superseded / reclassified incidents excluded (D-GAP-H2).
- Leaf-code granularity (M-SCAT subcode, not category).
**Dependencies:** FEAT-SAF-DASH-001.
**Decisions:** D-GAP-H2.
**SSOT refs:** see SSOT §6 D-GAP-H2.

### FEAT-SAF-DASH-004 — Pareto Screening Panel

**Priority:** V1
**User story:** As DPA, I see a Pareto-style top-N panel of repeat failures by M-SCAT leaf + vessel + rolling 12 months so the Tolerable-Failure Filter and chronic-incident flagging are data-driven.
**Acceptance criteria:**
- Top-N configurable (default 10).
- Feeds FEAT-SAF-INC-029 Tolerable-Failure Filter.
- Reinforces chronic-incident surfacing alongside Heinrich panel.
**Dependencies:** FEAT-SAF-DASH-001, FEAT-SAF-INC-029.
**Decisions:** D-GAP-R17.
**SSOT refs:** see SSOT §6 D-GAP-R17.

### FEAT-SAF-DASH-005 — SOI Compliance % (Renamed Metric)

**Priority:** V1
**User story:** As DPA, I see "SOI Compliance %" (NOT "Inspection Compliance %") on the Safety dashboard so there is no clash with the existing PSC Inspection-module metric.
**Acceptance criteria:**
- Label is **"SOI Compliance %"** in all UI + exports.
- Formula: (applicable areas inspected within last 90 days) / (total applicable areas) × 100.
- Edge cases:
  - New vessel (zero cycles completed): display "N/A — awaiting first cycle" (NOT 0% red) per D-GAP-M30.
  - `pending_closure` findings' areas count as inspected (fieldwork is done) per D-GAP-M30.
- Additional SOI metrics: Areas Overdue · Open Findings by Priority · Crew Rotation Coverage · Inspection → Meeting Closure Rate.
**Dependencies:** FEAT-SAF-SOI-005, FEAT-SAF-SOI-015.
**Decisions:** D-GAP-DESIGN-01, D-GAP-M30.
**SSOT refs:** see SSOT §2C.17; §6 D-GAP-DESIGN-01.

### FEAT-SAF-DASH-006 — CA Aging Pipeline (0-15 / 15-30 / 30-45 / 45+)

**Priority:** V1
**User story:** As DPA, I see CA aging buckets calculated from CA creation date (not reopen date) so aging reflects true organisational response time.
**Acceptance criteria:**
- Buckets: 0-15 / 15-30 / 30-45 / 45+ days.
- Clock starts at CA creation.
- Reopen does NOT reset clock (D-GAP-M29).
- Panel on Safety Intelligence Dashboard.
**Dependencies:** FEAT-SAF-DASH-001, FEAT-SAF-XMOD-004.
**Decisions:** D-GAP-M29.
**SSOT refs:** see SSOT §6 D-GAP-M29.

### FEAT-SAF-DASH-007 — Dashboard Export (PDF + Excel, DPA-Only)

**Priority:** V1
**User story:** As DPA, I export the Safety Intelligence Dashboard to PDF or Excel; FM has read-only dashboard access but NOT export rights in V1.
**Acceptance criteria:**
- Both PDF and Excel formats.
- Export includes timestamp + period + exporter name.
- DPA-owned export access; FM dashboard-read-only.
- No DPA export rate-limiting in V1.
**Dependencies:** FEAT-SAF-DASH-001.
**Decisions:** D-GAP-M31.
**SSOT refs:** see SSOT §6 D-GAP-M31.

### FEAT-SAF-DASH-008 — Archive Search Opt-In Toggle

**Priority:** V1
**User story:** As a search user, by default archived records are excluded; I tick "Include archived records" to include them so the default UI stays clean.
**Acceptance criteria:**
- Default search excludes archived (> 3y soft-archived) records.
- Opt-in checkbox on search bar: "Include archived records".
- Applies to all Safety record searches (Incident / Near Miss / SCM / SOI).
- FTS engine choice is build-time deferral (Round 20 / Phase 7).
**Dependencies:** FEAT-SAF-AUDIT-004.
**Decisions:** D-GAP-M32.
**SSOT refs:** see SSOT §6 D-GAP-M32.

### FEAT-SAF-DASH-009 — Seed Case-Study Library (Navigator + Sinkfast)

**Priority:** V1
**User story:** As a first-time investigator, I see DNV's Navigator (grounding) and Sinkfast (explosion) worked cases in the cause-picker Help drawer so I learn from published precedent.
**Acceptance criteria:**
- `master_safety_case_study` seeded with Navigator + Sinkfast.
- Full narrative + recommendations stored; renders in Help drawer.
- Also appear as worked examples inside Knowledge Base landing.
- Maintenance rights: DPA only (D-CFG-02).
**Dependencies:** FEAT-SAF-INC-017.
**Decisions:** D-DNV-14, D-CFG-02.
**SSOT refs:** see SSOT §2B.15; §6 D-CFG-02.

---

## 12. RBAC Specifics

### FEAT-SAF-RBAC-001 — Closure Authority by Band (PIC / DPA / FM)

**Priority:** V1
**User story:** As the system, closure authority tiers to the band: PIC closes GREEN, DPA closes YELLOW, FM closes RED.
**Acceptance criteria:**
- GREEN → PIC (Vessel Superintendent) closes.
- YELLOW → DPA closes.
- RED → FM closes + owns blame-fixation override for RED (D-RBAC-05).
- Re-open authority mirrors closure authority (D-EDGE-03).
- YELLOW-band joint investigation = Master + PIC (D-RBAC-02); DPA is closer not co-investigator (except RED per D-GAP-M06).
**Dependencies:** FEAT-SAF-INC-003, FEAT-SAF-RBAC-003.
**Decisions:** D-RBAC-01, D-RBAC-02, D-RBAC-05, D-EDGE-03.
**SSOT refs:** see SSOT §3.4; §6 D-RBAC-01.

### FEAT-SAF-RBAC-002 — Incident Creation (Top-4 Officers)

**Priority:** V1
**User story:** As the system, incident creation is limited to Top-4 officers (Master, CO, CE, 2/E); near miss creation is any rank.
**Acceptance criteria:**
- Incident creation: Master, CO, CE, 2/E only.
- Near miss creation: any rank (D-RBAC-11).
- Enforced via `SAF_P_001` process permission in `msc_profiles`.
**Dependencies:** FEAT-SAF-RBAC-005.
**Decisions:** §3.4 SSOT, D-RBAC-11.
**SSOT refs:** see SSOT §3.4.

### FEAT-SAF-RBAC-003 — Blame-Fixation Override Authority

**Priority:** V1
**User story:** As DPA (GREEN/YELLOW) or FM (RED), I have the exclusive authority to override the blame-fixation hard block.
**Acceptance criteria:**
- GREEN / YELLOW override → DPA.
- RED override → FM.
- If both DPA and FM refuse RED override → investigation returns to Phase 3 (no MD escalation per D-GAP-B1).
- Override action logged in `vims_safety_incident_phase_log` + `vims_safety_field_history`.
**Dependencies:** FEAT-SAF-INC-024, FEAT-SAF-INC-025.
**Decisions:** D-RBAC-07, D-GAP-B1.
**SSOT refs:** see SSOT §6 D-RBAC-07; D-GAP-B1.

### FEAT-SAF-RBAC-004 — Rank-Persists / No Acting-* Invariant

**Priority:** V1
**User story:** As the system, rank persists and the person in the role changes via normal crew rotation — no Acting-Master, no Acting-DPA, no deputy chains, no MD-escalation logic.
**Acceptance criteria:**
- All role-based permissions resolve to the current holder of the rank (via CMS live join for shipboard, HRM for office).
- No "Acting-*" UI or code paths anywhere (D-GAP-A3, D-GAP-A4).
- No deputy / MD-escalation logic.
- Timeline-extension procedure (D-GAP-B2) is the universal escape valve when a role-holder is unavailable.
- New Master on rotation inherits SCM chair + GREEN closure + SOI approval; new CO inherits open SOI findings + in-flight inspection.
- Role stays as-is even when incumbent is subject of the incident (D-GAP-A6) — integrity via DPA oversight + audit trail.
**Dependencies:** FEAT-SAF-INC-037, FEAT-SAF-INC-038, FEAT-SAF-SOI-024.
**Decisions:** D-GAP-A3, D-GAP-A4, D-GAP-A6, D-GAP-B2.
**SSOT refs:** see SSOT §6 D-GAP-A3; D-GAP-A4; D-GAP-A6.

### FEAT-SAF-RBAC-005 — Permission IDs `SAF_F_*` / `SAF_P_*` in `msc_profiles`

**Priority:** V1
**User story:** As the auth layer, Safety form IDs (`SAF_F_*`) and process IDs (`SAF_P_*`) are stored in the shared `msc_profiles` table — not a new permission table.
**Acceptance criteria:**
- Safety mirrors Reporting's `RPT_F_*` / `RPT_P_*` pattern.
- `SAF_F_001` = Incident form, `SAF_F_002` = Near Miss, `SAF_F_003` = SCM, `SAF_F_004` = SOI. SOI uses the same `SAF_F_*` / `SAF_P_*` pattern as the other Safety modules — no bespoke permission scheme (D-SOI-15).
- `SAF_P_001` = Create, `SAF_P_002` = Submit to office, `SAF_P_003` = Send back, `SAF_P_004` = Approve/Close, etc. (expand per BACKEND_STRUCTURE).
- Permission checks at `apps/safety/authentication/permissions.py` (HasFormPermission / HasProcessPermission).
- Sidebar: Safety group wrapped in `PermissionGate(SAF_F_*)`; hidden for users without any Safety form_ids.
**Dependencies:** —
**Decisions:** `<vims_integration>` mandate.
**SSOT refs:** see SSOT §3.4; cross-ref `<vims_integration>` in master prompt.

### FEAT-SAF-RBAC-006 — Cross-Vessel Visibility

**Priority:** V1
**User story:** As PIC, I can borrow lessons from non-managed vessels into my own vessel circulars; as Master, I can read closed incidents fleet-wide for in-crew learning.
**Acceptance criteria:**
- PIC: read-only on non-managed vessels + can borrow lessons-learned into own vessel circulars (D-RBAC-08).
- PIC borrow-lessons: anonymise vessel + crew names before pasting (D-GAP-M08); cause analysis and lesson text preserved verbatim.
- Master: read-only on closed incidents fleet-wide (D-RBAC-09).
- Vetting access: Master-driven on-screen + PDF export (D-RBAC-10).
**Dependencies:** FEAT-SAF-NM-006, FEAT-SAF-PDF-006.
**Decisions:** D-RBAC-08, D-RBAC-09, D-RBAC-10, D-GAP-M08.
**SSOT refs:** see SSOT §6 D-RBAC-08; D-RBAC-09; D-GAP-M08.

### FEAT-SAF-RBAC-007 — FM Full Edit Authority During RED Closure

**Priority:** V1
**User story:** As FM during RED closure, I can rewrite any investigation content — effectively co-investigator for RED band.
**Acceptance criteria:**
- FM has full edit authority on RED-band investigations (not just approve/reject).
- All FM edits captured in `vims_safety_field_history`.
- Does NOT apply to GREEN/YELLOW (FM baseline read + flag + comment only — D-RBAC-04).
**Dependencies:** FEAT-SAF-INC-003, FEAT-SAF-AUDIT-002.
**Decisions:** D-GAP-M06, D-RBAC-04.
**SSOT refs:** see SSOT §6 D-GAP-M06; D-RBAC-04.

### FEAT-SAF-RBAC-008 — DPA-Only Taxonomy Maintenance

**Priority:** V1
**User story:** As DPA, I exclusively maintain M-SCAT cause taxonomy, Recommendation Themes, Case Study Library, SOI 13-area template and checklist templates so analytics stability and taxonomy-churn control are preserved.
**Acceptance criteria:**
- DPA-only: M-SCAT taxonomy (D-CFG-01), Recommendation Themes (D-CFG-03), Case Study Library (D-CFG-02), SOI 11+2-area template, SOI checklist versions (D-SOI-05).
- DPA + PIC: Guidance Library (D-CFG-02 split).
- Fleet Circular approval reuses VIMS Circular module (D-CFG-04) — no Safety-specific workflow.
- Config-change log entry for every taxonomy modification.
**Dependencies:** FEAT-SAF-INC-017, FEAT-SAF-SOI-001, FEAT-SAF-SOI-003, FEAT-SAF-DASH-009.
**Decisions:** D-CFG-01, D-CFG-02, D-CFG-03, D-CFG-04.
**SSOT refs:** see SSOT §3.4; §6 D-CFG-01..04.

---

## 13. Deferred & Out of Scope (V2)

| Item | Reason | Decision |
|------|--------|----------|
| Stop-work authority workflow | Verbal informal escalation to Master retained; revisit when utilisation data justifies dedicated flow | D-SOI-03 |
| Anonymous near-miss submission | V1 uses reporter-identity masking instead (D-GAP-J1) | §4.4 SSOT |
| Column-level PII / medical encryption | Standard role permissions sufficient for V1; GDPR risk flagged for non-EU/UK/SG contexts | D-GAP-C5, D-EDGE-04 |
| Cryptographic tamper-evidence (hash chains, PKI signatures, UETA compliance) | V1 uses append-only audit + platform backups | D-GAP-D2 |
| Legal-hold feature | DPA exports externally before 3-year cutoff when case is open | D-GAP-G2 |
| In-module flag-state notification deadlines / class society toggle | DPA handles out-of-band | D-GAP-G1, D-GAP-M13 |
| Point-in-time snapshot / revert UI | Field-level diff per D-EDGE-10 is sufficient | D-GAP-M04 |
| User-configurable notification digest preferences | V1 every safety event is independent notification | D-GAP-M28 |
| Multilingual UI + translated M-SCAT codes | V1 English-only, DD-MMM-YYYY dates, metric units | D-GAP-M36 |
| Phone (≤480px) CRUD | V1 phone = read-only dashboards; tablet (768px+) is primary SOI device; desktop (1280px+) primary overall | D-GAP-M34 |
| In-VIMS PMS integration | PMS is standalone; manual cross-reference only | D-GAP-I1 |
| P&I / insurance claim data modelling | Commercial/finance system owns it | D-EDGE-12 |
| Deputy-FM / MD-escalation / Acting-* concepts | Rank persists; timeline-extension procedure is universal escape valve | D-GAP-A3, D-GAP-A4, D-GAP-B1, D-GAP-B2 |
| FEAT-SAF-INC-029 Tolerable-Failure Filter | Tagged V1.1 — stretch goal; depends on Pareto panel maturity | D-GAP-R11 |

---

## 14. Global Business Rules

### Causal reasoning
- Every incident uses the DNV Loss Causation Model (5-layer chain): LACK OF CONTROL → BASIC CAUSES → IMMEDIATE CAUSES → INCIDENT → LOSS (§2B.1).
- Near miss shares the full chain — only the loss threshold differs.
- Every investigation must produce at least one Lack-of-Control entry (bias guard #5).
- Every cause carries: M-SCAT code + causal layer (Immediate/Intermediate/Root) + evidence link + free-text rationale.

### Investigation
- Risk band (GREEN/YELLOW/RED) computed at Phase 1 submit; DPA may re-classify at any review stage with reason logged.
- IMO classifier (SMC/MC/MI) separate from risk band — drives regulatory export template.
- Loop-back from Phase 5 → Phase 3 always allowed; no cap; all logged.
- Investigation depth (SHALLOW/MEDIUM/DEEP) drives minimum analysis tools (2/3/5).
- Multiple root causes are the default; monocausal closure requires written justification.

### Recommendations
- Phase 6 requires three tiers: Lessons Learned + Immediate Action + System Action.
- Each System Action carries ALARP fields (effort, likelihood reduction, residual-risk acceptability) — mandatory for RED/YELLOW.
- Visual taxonomy: Corrective / Preventive / Lessons colour badges.
- YELLOW/RED closure check: at least one of each tier exists.

### Paper-first SOI
- No per-item responses in DB (paper is authoritative).
- No scan upload — paper filed in ship SMS filing system (D-GAP-E4).
- Unique checklist ID prints on PDF/Excel and on paper; entered at finding registration to link digital → paper.
- Section 12 once per 3-month cycle (not every SOI event).
- HIGH severity findings require ≥1 photo.

### SCM
- Regular monthly cadence + Ad-Hoc meetings hosted by Master or CO.
- Cadence counter + Closed-Since-Last snapshot anchor on last SCM closure timestamp **regardless of meeting type**.
- SCM form matches legacy `vw_GetSCM_Master` structure with the reserved section removed and later sections renumbered.
- Office Comment closes SCM and stops editing.
- PDF is downloadable after meeting creation and includes plain Master/CO signature lines only.
- Overdue SOI areas are warning/visibility only; they do not block meeting creation/running/office closure.
- WRH attendance warn-don't-block.

### Near Miss
- Reporter identity stored and visible to Master and authorized users within scope.
- LOW, MEDIUM, or HIGH priority is finalized in Office Comments.
- No daily submission cap; min 100 chars description.
- HIGH priority triggers fleet alert within 1 week.

### Timezone, dates, units
- All timestamps stored UTC in DB.
- Vessel local time resolved via `wrh_ship_time_config` (D-GAP-M26).
- Date rendering: DD-MMM-YYYY (e.g., 17-Apr-2026) to avoid US/EU ambiguity.
- Units: metric always.

### Naming
- Module tables: `vims_safety_*` (NEVER bare `safety_*`).
- Reference / seed data: `master_*`.
- Feature IDs: `FEAT-SAF-<INC|NM|SCM|SOI|XMOD|PDF|AUDIT|DASH|RBAC>-NNN`.
- Permission IDs: `SAF_F_*` (forms) / `SAF_P_*` (processes) in shared `msc_profiles`.
- Component prefix: `Safety*` (e.g., `SafetyIncidentPhase3.tsx`).
- Dashboard metric: **"SOI Compliance %"** (NOT "Inspection Compliance %") per D-GAP-DESIGN-01.

### Accessibility & mobile
- WCAG 2.1 Level AA baseline (D-GAP-M35).
- Mobile-first mandate; tablet (768px+) primary SOI device; phone (≤480px) read-only dashboards; desktop (1280px+) primary overall (D-GAP-M34).

### Data integrity
- Append-only phase log + field-level history on all safety records.
- 3-year soft archive + attachment hard-delete.
- No cryptographic tamper-evidence in V1.
- Same-DB live joins — no ETL / no staleness.

---

## 15. User Roles & Permissions

Expansions on first use: **DPA** (Designated Person Ashore, ISM Code §4); **FM** (Fleet Manager); **TD** (Technical Director); **HOD** (Head of Department onboard — CO or CE); **CO** (Chief Officer); **CE** (Chief Engineer); **SO** (Safety Officer — CO by default, 2/E alternate); **PIC** (Person-in-Charge / Vessel Superintendent).

### 15.1 Incident module

| Action | Reporter (any rank) | Master | CO | CE | 2/E | PIC | DPA | FM |
|--------|---------------------|--------|-----|-----|-----|-----|-----|-----|
| Create incident | — | Yes | Yes | Yes | Yes | — | — | — |
| Phase 1 submit (formal) | — | Yes | Yes | Yes | Yes | — | — | — |
| Phase 3–5 investigation — GREEN | — | Yes (lead) | — | — | — | — | — | — |
| Phase 3–5 investigation — YELLOW | — | Yes (joint) | — | — | — | Yes (joint) | — | — |
| Phase 3–5 investigation — RED | — | — | — | — | — | — | Yes (lead + external) | Edit (D-GAP-M06) |
| Phase 7 acceptance — GREEN | — | — | — | — | — | **Yes (closer)** | — | — |
| Phase 7 acceptance — YELLOW | — | — | — | — | — | — | **Yes (closer)** | — |
| Phase 7 acceptance — RED | — | — | — | — | — | — | — | **Yes (closer)** |
| Blame-fixation override — GREEN/YELLOW | — | — | — | — | — | — | **Yes** | — |
| Blame-fixation override — RED | — | — | — | — | — | — | — | **Yes** |
| Re-open (band-gated) | — | — | — | — | — | — | GREEN/YELLOW | RED |
| Cross-vessel read-only (closed) | — | Fleet-wide | — | — | — | Non-managed | All | All |
| Borrow lessons into own circulars | — | — | — | — | — | **Yes (anonymised)** | — | — |
| Flag / comment outside formal record | — | — | — | — | — | — | — | **Yes** |

### 15.2 Near Miss module

| Action | Any crew | Master | HOD | DPA | FM |
|--------|----------|--------|-----|-----|-----|
| Create near miss | **Yes** | Yes | Yes | — | — |
| See reporter identity | Self | **Yes** | **Yes** | **Yes** | **Yes** |
| Office Comments priority decision | — | — | PIC for LOW/MEDIUM | HIGH only | — |
| Close (PIC) | — | — | — | — | — |
| Fleet-alert generate (HIGH) | — | — | — | Yes | — |

### 15.3 SCM module

| Action | CO | Master | DPA | FM |
|--------|-----|--------|-----|-----|
| Create Regular SCM | **Yes** | **Yes** | — | — |
| Create Ad-Hoc SCM | **Yes** | **Yes** | — | — |
| Edit before Office Comment | **Yes** | **Yes** | — | — |
| Office Comment + Close | — | — | **Yes** | **Yes** |
| Attendance / WRH edit | **Yes** | **Yes** | Read | Read |
| Read fleet-wide | — | Closed records | All | All |

### 15.4 SOI module

| Action | CO (SO) | 2/E (alt SO) | Master | Assistant (cross-dept) | Trainees | PIC | DPA | FM |
|--------|---------|--------------|--------|-------------------------|----------|-----|-----|-----|
| Schedule inspection | Yes | Yes (if alt) | Override | — | — | Flag | Yes | Flag |
| Create inspection record | Yes | Yes | — | — | — | — | — | — |
| Edit during Draft | Yes | Yes | — | — | — | — | — | — |
| Enter findings | Yes | Yes | — | Advisory | Advisory | — | — | — |
| Submit inspection | Yes | Yes | — | — | — | — | — | — |
| Mark finding `pending_closure` | Yes | Yes | — | — | — | — | — | — |
| Approve closure | — | — | **Yes** | — | — | — | — | — |
| View inspection records | Own vessel | Own vessel | Own vessel | If named | If named | Assigned | All | Fleet (read) |
| Maintain checklist taxonomy | — | — | Propose | — | — | Propose | **Yes (exclusive)** | — |
| Maintain 13-area template | — | — | — | — | — | — | **Yes (exclusive)** | — |
| Re-open closed finding | — | — | Yes | — | — | — | Yes (safety net) | — |
| Area-applicability toggle → false | — | — | Request | — | — | — | **Approve** | — |
| Paper signature | Yes | Yes | Digital at approval | **Yes** | No | — | — | — |

### 15.5 Admin / config

| Area | Maintainer |
|------|------------|
| M-SCAT cause taxonomy | DPA only (D-CFG-01) |
| Recommendation Themes | DPA only (D-CFG-03) |
| Case Study Library | DPA only (D-CFG-02) |
| Guidance Library | DPA + PIC (D-CFG-02) |
| SOI 13-area template | DPA only |
| SOI checklist versions | DPA only (D-SOI-05) |
| Bias-guard set | DPA only (seeded) |
| Fleet Circular approval | Reuses VIMS Circular module (D-CFG-04) |

---

## Appendix A — Mapping: SSOT `safety_*` names → VIMS naming

Per `<database_naming_convention>`, the SSOT's historical `safety_*` prefix is translated on output:

| SSOT name | This PRD's name |
|-----------|-----------------|
| `safety_incident` | `vims_safety_incident` |
| `safety_incident_phase_log` | `vims_safety_incident_phase_log` |
| `safety_field_history` | `vims_safety_field_history` |
| `safety_soi_inspection` | `vims_safety_soi_inspection` |
| `safety_soi_inspection_area` | `vims_safety_soi_inspection_area` |
| `safety_soi_finding` | `vims_safety_soi_finding` |
| `safety_soi_vessel_area_map` | `vims_safety_soi_vessel_area_map` |
| `safety_soi_applicability_log` | `vims_safety_soi_applicability_log` |
| `safety_soi_trainee` | `vims_safety_soi_trainee` |
| `safety_scm_meeting` | `vims_safety_scm_meeting` |
| `safety_scm_attendance` | `vims_safety_scm_attendance` |
| `safety_scm_agenda` | `vims_safety_scm_agenda` |
| `safety_corrective_action` | `vims_safety_corrective_action` |
| `safety_recommendation` | `vims_safety_recommendation` |
| MSCAT taxonomy | `master_mscat_taxonomy` (seeded from `mscat_taxonomy.csv`, 174 rows) |
| Immediate causes | `master_immediate_causes` (52 rows) |
| Loss types | `master_loss_types` (7 rows, D-DNV-03 — DNV 7-category taxonomy) |
| `safety_soi_area` | `master_soi_area` (13 rows) |
| `safety_soi_area_item` | `master_soi_area_item` (329 rows) |
| `safety_soi_checklist_version` | `master_soi_checklist_version` |
| `safety_incident_type` (11 rows) | `master_safety_incident_type` |
| 8 bias guards | `master_safety_bias_guard` |

Consumed existing VIMS masters (not duplicated): `master_role`, `master_RoleByVessel`, `master_applied_rank`, `master_notification`.

---

## Appendix B — Priority breakdown

| Tier | Count |
|------|-------|
| V1 (must-ship) | 93 |
| V1.1 (stretch) | 1 (FEAT-SAF-INC-029) |
| V2 (deferred) | see §13 |

All V1 features carry ≥1 D-* or D-GAP-* decision citation in the feature block above.

---

**End of PRD.**
