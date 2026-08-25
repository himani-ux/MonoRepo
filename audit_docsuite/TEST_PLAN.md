# VIMS Inspection Extension — Audit Module — Test Plan

**Input:** `VIMS-AUDIT-RS-MODULE-SSOT.md` v0.21 (🔒 FROZEN). **DocSuite doc 11 of 11** per D-AUDRS-269.
**Companion:** `APP_FLOW.md` (flows under test) · `RBAC.md` (gate matrix) · `DATA_MODEL.md §12` (constraints).

---

## Table of Contents

1. Scope & Strategy
2. Test Levels
3. Device / Browser Matrix
4. Suite A — Registration & Submit Gates
5. Suite B — Finding Capture
6. Suite C — NC Closure
7. Suite D — Observation Closure
8. Suite E — Planning, Window & Extension
9. Suite F — External Audit
10. Suite G — Notifications
11. Suite H — RBAC & CoI
12. Suite I — PDF & QR/Hash
13. Suite J — Cross-Module Integration
14. Suite K — Validation & Edge Cases
15. Suite L — Readability & Accessibility
16. Regression — PSC Untouched
17. Exit Criteria

---

## 1. Scope & Strategy

Covers v1.0 Internal Audit (Vessel + Office) + v1.1 External Audit. RS / RightShip (v1.2) and Manning/Security (v1.3) are out of scope. The over-arching invariant under test: **the PSC workflow, CAR engine, evidence rules, sync, and existing RBAC are unchanged** (D-001/003) — Suite M regression proves it.

Every test case traces to a decision and to an `APP_FLOW.md` flow or a `DATA_MODEL.md §12` constraint.

---

## 2. Test Levels

| Level | Coverage |
|-------|----------|
| Unit | Service-layer rules — submit gates, date-order constraints, free-text minimums, window math, HoD resolver, CAS guard. |
| Integration | API endpoints + DB; CAR engine handoff; cross-module clients (CMS, HRM501, Certs) against pinned versions (D-279). |
| End-to-end | The 9 `APP_FLOW.md` flows, browser-driven. |
| Regression | PSC inspection workflow unchanged. |

---

## 3. Device / Browser Matrix (D-AUDRS-281)

Desktop: Chrome 120+, Edge 120+, Safari 17+, Firefox 121+. Mobile: iOS 16+ Safari, Android 13+ Chrome. Reference test devices: iPad 12.9" + iPhone 6.7". Wizard adaptive breakpoint verified at 1024px (D-120). **Not supported / not tested:** IE11, Android <13 tablets, in-app browsers (LinkedIn/WeChat).

---

## 4. Suite A — Registration & Submit Gates

| ID | Case | Expect | D- |
|----|------|--------|----|
| A-01 | Office user registers an internal vessel audit via `/inspections/new` (AUDIT branch). | Audit created at `IN_PROGRESS`; F 605 checklist auto-picked by ship_type. | D-001/020/039 |
| A-02 | Vessel user attempts to register an audit. | Blocked — AUDIT branch restricted to office users with `AUDIT_P_001/003`. | D-039 |
| A-03 | Harmonised standards multi-select ISM+ISPS+MLC+EMS. | All persisted to `audit_standards`. | D-016 |
| A-04 | Submit with opening meeting unset. | Hard-block, inline error on the opening-meeting field. | D-071 |
| A-05 | Submit with a 14-area scorecard row blank. | Hard-block; office audit with N/A on the 6 vessel-only rows passes. | D-071/105 |
| A-06 | Submit with `audit_summary` < 100 chars. | Hard-block. | D-071 |
| A-07 | Submit with empty `equipment_tested`. | Hard-block. | D-071 |
| A-08 | All 4 gates satisfied → Submit. | Status → `REPORT_FINALIZED`; findings list freezes. | D-071/080 |
| A-09 | Master clicks "Vessel Acknowledge Audit Report". | Status → `VESSEL_ACKNOWLEDGED`; NC SLA clocks start. | D-254 |
| A-10 | Register Audit with a selected plan in `PLANNED` or already-used state. | Backend rejects with `audit_plan_id` validation error and no audit is created. | D-108 |
| A-11 | Register Audit with a valid selected plan. | Audit is created and source `master_audit_plan.status` becomes `IN_PROGRESS`. | D-108 |
| A-12 | First successful NC `START_PIC_REVIEW` after vessel acknowledgement. | `audit_detail.pic_user_id_resolved` is set and audit status becomes `CLOSURE_IN_PROGRESS`. | D-109/254 |
| A-13 | First successful Observation closure save after vessel acknowledgement. | Audit status becomes `CLOSURE_IN_PROGRESS`. | D-254 |
| A-14 | Audit detail contains NC and OBS findings created at the same timestamp. | API returns findings in deterministic NC/OBS order, not UUID-dependent order. | D-080 |
| A-15 | Edit `audit_classification` after a finding exists. | Read-only; banner shown. | D-078 |
| A-16 | Select a registerable audit plan during Register Audit. | Lead Auditor fields are populated from the selected plan and rendered read-only; submitted payload keeps the plan auditor snapshot. | D-108 |

---

## 5. Suite B — Finding Capture

| ID | Case | Expect | D- |
|----|------|--------|----|
| B-01 | Add an NC finding. | One CAR auto-created (`AUDIT-YYYY-NNN`), CAR at `ALLOTTED`. | D-002/008 |
| B-02 | Add a finding with `objective_evidence` blank, then submit. | Submit blocked — objective evidence mandatory. | D-007 |
| B-03 | Polymorphic clause ref — pick ISM clause; pick `OTHER` + free text. | OTHER requires 5–200 char `clause_ref_text`. | D-068/077 |
| B-04 | Multi-clause: add 2 clauses, mark one `is_primary`. | Exactly one `is_primary=1`; mirror columns on `audit_finding` match. | D-226 |
| B-05 | Add a finding to a `SUBMITTED` audit. | HTTP 409. | D-080 |
| B-06 | Major NC + `certificate_impact=SUSPENDED`. | `priority` auto-escalates to CRITICAL. | D-232 |
| B-07 | Office NC — `certificates_at_risk` UI. | Only DOC + NONE offered; SMC/ISSC/MLC_DMLC rejected (HTTP 400). | D-103 |

---

## 6. Suite C — NC Closure (KSM-F-NC-001)

| ID | Case | Expect | D- |
|----|------|--------|----|
| C-01 | Crew fills Part B/C via the mobile wizard. | Single-question-per-screen; draft saved each advance; resume from last screen. | D-116 |
| C-02 | Wizard on desktop ≥1024px. | 2-column layout with persistent context panel. | D-120 |
| C-03 | RCA wizard — pick an `master_rca_template`. | RCA field pre-filled; editable; ≥50-char rule applies after edit. | D-074/117 |
| C-04 | Office-led drafting — Supt drafts B+C. | CAR → `OFFICE_DRAFTED`; Master notified; both names on PDF Part B footer. | D-118 |
| C-05 | Transition without a signature scan. | Hard-block "Signature missing for {phase}". | D-072 |
| C-06 | PIC review pickup by first scoped office user. | That user becomes PIC of record; `pic_user_id_resolved` set. | D-107/109 |
| C-07 | Lead Auditor clicks "Start PIC Review" on own audit. | HTTP 403. | D-110 |
| C-08 | Lead Auditor closes Parts E/F/G; CAR → `LEAD_AUDITOR_CLOSED`. | EffRev task scheduled, due T+30, expiry T+90. | D-057/082 |
| C-09 | EffRev outcome `NOT_EFFECTIVE`. | Finding re-opens via `REWORK_REQUESTED`. | D-044 |
| C-10 | EffRev incomplete at T+90. | `effectiveness_overdue=1`; DPA/SEQ escalation. | D-082 |
| C-11 | NC overdue past due date. | Soft — banner + escalation; transitions still work. | D-073 |
| C-12 | Master signature backdated 25 days with reason. | Accepted; `audit_finding_sign_event` records claimed vs actual. Backdate >30d hard-blocks. | D-255 |

---

## 7. Suite D — Observation Closure (KSM-F-OBS-001)

| ID | Case | Expect | D- |
|----|------|--------|----|
| D-01 | Master fills Part B and signs. | State → `MASTER_CLOSED` (terminal). | D-040/043 |
| D-02 | DPA Part C / Auditor Part D entered. | Recorded as timestamps; state stays `MASTER_CLOSED` (not gated). | D-040 |
| D-03 | Observation wizard (3 questions) on mobile + desktop. | Adaptive layout per D-120. | D-116/120 |

---

## 8. Suite E — Planning, Window & Extension

| ID | Case | Expect | D- |
|----|------|--------|----|
| E-01 | Window computed for a vessel. | `window_start = last + 8mo`, `window_end = last + 12mo` from `master_audit_window_rule`. | D-049/242 |
| E-02 | T-90 tick. | SEQ Manager notified; draft PLANNED entry auto-created. | D-050 |
| E-03 | T-0 / T+90 ticks. | `OVERDUE` / `CRITICAL_OVERDUE`; cert-at-risk flag at T+90. | D-050 |
| E-04 | OPM F 713 extension — reason < 50 chars. | Rejected. Valid request → `EXTENSION_REQUESTED`. | D-051 |
| E-05 | DPA approves extension. | `extended_due_date` set; auto-numbered `OPM-F-713-YYYY-NNN`; status `EXTENDED`. | D-051 |
| E-06 | DPA cancels audit. | `cancellation_reason` ≥50 + future `next_planned_date` enforced; new PLANNED entry auto-created at −90d. | D-064 |
| E-07 | Create an additional audit. | `is_additional=1`; excluded from cadence math; no alert ladder. | D-121 |
| E-08 | Additional audit trigger = PSC_INSPECTION. | FK picker resolves; PSC inspection gets the back-reference annotation. | D-122/123 |
| E-09 | Additional audit trigger = FLAG_LETTER. | Free text + mandatory `TRIGGER_EVIDENCE` attachment enforced. | D-122 |

---

## 9. Suite F — External Audit (v1.1)

| ID | Case | Expect | D- |
|----|------|--------|----|
| F-01 | Master registers an external SMC audit post-facto. | Created at `status=SUBMITTED`; no PLANNED lifecycle. | D-200 |
| F-02 | Register with a missing mandatory field. | HTTP 400. | D-201 |
| F-03 | Register >30 days after completion. | Hard-block unless DPA override with `late_registration_reason` ≥50. | D-217 |
| F-04 | DOC audit without `flag_state_code`. | Rejected — flag mandatory for DOC subtypes. | D-213 |
| F-05 | Two DOC audits, same flag + cycle year. | Second blocked by the per-flag unique constraint. | D-213 |
| F-06 | Duplicate external audit (same vessel/org/subtype/month). | Soft-warn; DB UNIQUE blocks an exact dup; DPA merge available. | D-221 |
| F-07 | Link a `vessel_cert`; close out with `certificate_impact=CERT_VALID`. | `cert_writeback_outbox` row enqueued; worker drains to Certs. | D-202/234 |
| F-08 | Certs version changed before writeback drains. | CAS conflict; `CONFLICT` row in DPA queue with ACCEPT/FORCE. | D-236 |
| F-09 | `certificate_impact=SUSPENDED` at close-out. | Requires close-out letter + two-step DPA confirm + `flag_state_notification_log` row. | D-238 |
| F-10 | Close external NC. | `EXTERNAL_AUDITOR_CLOSED` requires close-out letter + DPA confirm; no Lead Auditor step. | D-204 |
| F-11 | External Major / Minor / Observation EffRev. | Major mandatory, Minor optional, Observation none. | D-231 |
| F-12 | `DOC_INITIAL` close-out. | Certs writeback CREATES the cert row + sets anniversary. | D-207/209 |
| F-13 | `SMC_INTERIM` close-out. | Certs writeback CONVERTS the Interim cert to full (same `vessel_cert.id`). | D-208 |
| F-14 | `DOC_INITIAL` close-out where cert already exists. | HTTP 409; DPA reconciles. | D-209 |

---

## 10. Suite G — Notifications

| ID | Case | Expect | D- |
|----|------|--------|----|
| G-01 | `AUDIT_SCHEDULED` fires. | In-system insert in the same transaction; email + Slack async. | D-111 |
| G-02 | Email/Slack fail after 3 retries. | Audit action NOT rolled back; `notification_delivery_log` `FAILED_PERMANENT`. | D-111 |
| G-03 | CMS returns no vessel email. | `FAILED_PERMANENT` + `CMS_NO_EMAIL_ON_FILE`; surfaces in DPA failed-widget. | D-264 |
| G-04 | Office audit notification. | Routes to HoD (via `master_hod_assignment`) + staff + DPA + team; Slack skipped. | D-102/106/265 |
| G-05 | DPA "Mark Notified Offline". | Reason ≥30 chars; status `RESOLVED_OFFLINE`; logged. | D-262 |

---

## 11. Suite H — RBAC & CoI

| ID | Case | Expect | D- |
|----|------|--------|----|
| H-01 | Each `AUDIT_P_*` gate against each role per `RBAC.md §4/§7`. | Mapping holds; ungated calls 403. | D-083/206 |
| H-02 | Office-audit visibility. | All office users with read gates see it; `master_RoleByVessel` bypassed. | D-101 |
| H-03 | Vessel-audit visibility. | Filtered by `master_RoleByVessel`. | D-086 |
| H-04 | SEQ-dept audit, Lead Auditor = DPA. | HTTP 422. | D-256 |
| H-05 | Self-acting HoD authorisation. | Forbidden; only FM/DPA via `AUDIT_P_016`. | D-253 |
| H-06 | Acting-HoD beyond 90 days. | Auto-expiry job flips `is_acting=0` at 00:01 ITC. | D-253 |

---

## 12. Suite I — PDF & QR/Hash

| ID | Case | Expect | D- |
|----|------|--------|----|
| I-01 | Generate F 601/F 602/NC/OBS PDFs. | A4 portrait; correct layout per `PDF_TEMPLATES.md`. | D-042/043/095 |
| I-02 | PDF while audit not terminal. | DRAFT watermark present; removed at terminal state. | D-096 |
| I-03 | Additional audit PDF. | Red "ADDITIONAL AUDIT — DPA AUTHORISED" banner. | D-123 |
| I-04 | Upload a signed scan; QR matches. | `pdf_hash_validation_status=MATCHED`. | D-261 |
| I-05 | Upload a scan from a different finding. | `MISMATCH_FINDING`; appears in `/dpa/scan-validation-queue`; upload not blocked. | D-261 |
| I-06 | External-audit attachment. | `NOT_APPLICABLE`. | D-261 |
| I-07 | TZ rendering. | Office PDF `(ITC)`; vessel sign block `(LT UTC±HH:MM)`. | D-249 |

---

## 13. Suite J — Cross-Module Integration

CMS/HRM501/PSC/Circular are same-DB reads (D-135) — exercised by ordinary integration tests. Certs + Safety are the two pinned external modules (`CROSS_MODULE_DEPS.md §5`); a pin failure blocks Phase 0 *(pins recorded 2026-06-12 — owner ruling 2026-07-14, importing DPA_SIGNOFF 2026-06-12 (RightShip bundle): baseline `VimsWithSafety @ 11993891a27cc2cc1d17496513a508d72bfadb73`; runtime `cert_change_log` gated to Phase 11 only)*.

| ID | Case | Expect | D- |
|----|------|--------|----|
| J-01 | Vessel local time read (CMS-WRH + `master_time_zone`). | Vessel local time + UTC offset returned. | D-249, D-135 |
| J-02 | Active crew by rank (`Crew_Onboarding_History` ⨝ `HRM501`). | Correct `user_id` for the rank at the instant. | D-250, D-135 |
| J-03 | Vessel email read of `VesselData.Email`. | Email returned; null/empty path → `FAILED_PERMANENT`. | D-136 |
| J-04 | Vessel-side rank `SELECT rank_name FROM HRM501 WHERE user_id=?`. | Rank returned; office users use `users.employee_role`. | D-280, D-135 |
| J-05 | "Issue Circular" from an NC. | Pre-filled Circular entry; `linked_circular_id` stored. | D-065 |
| J-06 | Safety incident → `INCIDENT_FOLLOWUP` additional audit. | Polymorphic link resolves. | D-122 |
| J-07 | Certs writeback / Safety incident lookup against the pinned external modules. | Verified versions; pin mismatch blocks Phase 0 *(pins recorded 2026-06-12 — owner ruling 2026-07-14, importing DPA_SIGNOFF 2026-06-12 (RightShip bundle); Certs runtime dep gated to Phase 11)*. | D-279 |

---

## 14. Suite K — Validation & Edge Cases

| ID | Case | Expect | D- |
|----|------|--------|----|
| K-01 | Date-order: `opening > closing`, `closing > today`, `extended ≤ original`, `next_planned ≤ today`, `expiry ≤ qualification`. | Each hard-blocked with an inline error. | D-075 |
| K-02 | EffRev date outside [+30,+90]. | Rejected. | D-075 |
| K-03 | Free-text minimums (RCA 50, rework 20, extension 50, cancellation 50, cycle_reset 100). | Each enforced. | D-074/216 |
| K-04 | Soft-delete an audit with a CAR past `ALLOTTED`. | Blocked — must use `CANCELLED`. | D-079 |
| K-05 | Attachment >10 MB or disallowed mime. | Rejected with inline error. | D-076 |
| K-06 | Attachment versioning. | Re-upload of FINAL marks the prior `SUPERSEDED`. | D-218 |
| K-07 | DB Table Creation Standard verification grep. | Zero violations across all 43 new tables. | D-271 |
| K-08 | Legacy AUDIT/RS rows post-deploy — **tag resolved via `audit_legacy_inspection_tag`** (re-pointed 2026-07-14; formerly asserted the `psc_inspection.legacy` column). | An inspection with a tag row (`is_legacy=1`) renders read-only with the "Legacy — read only" banner; edit / add-finding / state-transition are all blocked. **`psc_inspection` has NO `legacy` column.** | D-097 (substance) · **D-288** |
| K-09 | **Absence of a tag row.** | Inspection is treated as **not legacy** — fully editable, no banner. (Absence = not legacy; no per-row write needed for the 0 existing rows.) | D-288 |
| K-10 | **Pre-deploy discovery probe** on a DB with **0** AUDIT/RS rows (the live-verified case). | Probe returns 0; **no tag rows written; `psc_inspection` untouched (zero writes)**. | D-291 |
| K-11 | **Pre-deploy discovery probe** on a seeded DB with **N > 0** AUDIT/RS rows. | Exactly N tag rows inserted into `audit_legacy_inspection_tag`; **`psc_inspection` still byte-identical (zero `UPDATE`s)**; re-running the loader is **idempotent** (still N rows, guarded by the unique index). | D-291 |
| K-12 | **🔒 SCHEMA-FINGERPRINT GATE (never-waivable).** Capture the fingerprint (`sys.columns` + `sys.check_constraints` + `sys.indexes`) of the 9 protected tables — `psc_inspection`, `psc_car`, `psc_deficiency`, `psc_corrective_action`, `psc_notification`, `psc_activity_history`, `psc_audit_log`, `HRM501`, `VesselData` — **before and after** the full migration. | **Pre and post fingerprints are IDENTICAL. Any diff FAILS the build.** Approved exception list = **EMPTY**. **Assert on the DB fingerprint, NOT on migration-file text** — a `choices`-only change emits a no-SQL `AlterField` and would false-positive a grep-based check. | **D-290** |
| K-13 | **🔒 NEGATIVE / fail-closed:** inject a deliberate `ALTER TABLE psc_inspection ADD junk bit` into a scratch migration and run the gate. | Gate **FAILS** (fingerprint diff detected). Proves the gate actually catches a legacy mutation rather than passing vacuously. | D-290 |
| K-14 | **🔒 P0 CHECK-CONSTRAINT ASSERTION (fail-closed):** run the build-time probe against a DB where a CHECK constraint **has** been added to `psc_car.status`. | Build **FAILS** with state **`BLOCKED`**; owner is consulted. The migration **does NOT self-authorize an `ALTER`**. Against the real (verified) DB the probe returns **0** and the build proceeds. | **D-294** |
| K-15 | **Module isolation:** run the full Audit migration, then diff every non-Audit table in the DB. | **Only `audit_*` / `master_audit_*` / whitelisted master tables are created.** No object outside the Audit namespace is created, altered, or dropped. Existing PSC + CAR flows remain green (Suite M regression). | D-070 · D-290 |
| K-16 | **CAR status extension needs no DDL.** Apply the `CARStatus` `choices` extension and inspect the generated migration + the DB. | The migration emits an `AlterField` with **no SQL**; `psc_car` schema is **unchanged**; an audit NC nevertheless reaches `LEAD_AUDITOR_CLOSED` and an external NC reaches `EXTERNAL_AUDITOR_CLOSED`. | **D-289** · D-057/118/204 |

---

## 15. Suite L — Readability & Accessibility

| ID | Case | Expect | D- |
|----|------|--------|----|
| L-01 | Wizard prompt readability. | Flesch-Kincaid grade ≤ 8 (CEFR B1). | D-282 |
| L-02 | Wizard keyboard support (desktop). | Enter advances, Esc returns, Cmd/Ctrl+S saves. | D-120 |
| L-03 | English-only UI. | No translation surface present at v1.0. | D-282 |

---

## 16. Regression — PSC Untouched

| ID | Case | Expect | D- |
|----|------|--------|----|
| M-01 | Full PSC inspection lifecycle. | Unchanged — DRAFT → SUBMITTED → PIC_REVIEWED → DPA_CLOSED. | D-001 |
| M-02 | PSC CAR state machine + evidence rules. | Unchanged. | D-003/009 |
| M-03 | PSC PDF export. | `psc_car_pdf.py` output unchanged. | D-013 §13 |
| M-04 | Existing PSC RBAC gates. | `PSC_P_*` behaviour unchanged. | D-083 |

---

## 17. Exit Criteria

1. All Suite A–M cases pass on the §3 device/browser matrix.
2. PSC regression (Suite M) is 100% green — the CAR engine and PSC workflow are provably unchanged.
3. The DB Table Creation Standard verification grep (K-07) reports zero violations.
4. Cross-module integration tests (Suite J) pass against the pinned sibling versions (D-279). **Pins locked 2026-06-12** (owner ruling 2026-07-14, importing DPA_SIGNOFF 2026-06-12 — RightShip bundle): baseline `VimsWithSafety @ 11993891a27cc2cc1d17496513a508d72bfadb73`; the runtime `cert_change_log` dependency is gated to Phase 11 only (`CROSS_MODULE_DEPS.md §5`), so it does not block Phase 0 cutover.
5. The DocSuite mechanical re-grep (`COVERAGE.md`) reports ≥99% coverage (D-266).
6. All `MIGRATION.md §8` cutover-checklist items are ticked.
