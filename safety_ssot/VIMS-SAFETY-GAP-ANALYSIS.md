# VIMS Safety Module — Gap & Edge-Case Analysis

> **Generated:** 2026-04-17 (Session 5 opening review)
> **Purpose:** Surface unresolved decisions, ambiguities, and edge cases BEFORE docsuite generation.
> **Method:** 5 parallel gap-hunter agents, one per domain. Raw output: 125 gaps. Deduped + consolidated below.
> **Input:** `VIMS-SAFETY-MODULE-SSOT.md` (1481 lines, 61 decisions locked) + `VIMS-SAFETY-REQUIREMENTS-INTERROGATION.md` (1035 lines, 16 rounds)

---

## Executive Summary

| Severity | Raw | Deduped | Must-close before build? |
|----------|-----|---------|--------------------------|
| **HIGH** | 40 | **27** | YES — will block or misbuild |
| **MED** | 62 | **44** | Preferred — prevents rework |
| **LOW** | 23 | **14** | Nice-to-have |
| **Total** | 125 | **85** | |

**Top 10 themes by risk weight:**

1. Absence / delegation chain (no Acting DPA, PIC, Master, CO)
2. Self-reporting & dual-hat conflicts (reporter = victim, Master = subject, CO = subject)
3. Digital signature & non-repudiation chain (legal weight, ISM, crypto proof)
4. Paper-first SOI robustness (download, partial submit, lost paper, upload failure, count mismatch)
5. Online-only fragility (connectivity drop during incident entry / scan upload)
6. Notification reliability (Slack failure, escalation dead-ends, no observability)
7. Legal hold & data retention (3-yr hard-delete vs open claims / subpoena)
8. Regulatory deadlines (IMO flag-state window, class society, MARPOL)
9. Reference-data seeding (170 M-SCAT codes, 292 SOI items — no canonical CSV)
10. Audit trail integrity (field history schema, tamper-evidence, snapshot semantics)

---

## HIGH-Severity Gaps (27) — must resolve before docsuite

### Cluster A. People/role continuity (6)

| ID | Gap | Question to lock |
|----|-----|------------------|
| H-01 | No Acting DPA when DPA on leave during YELLOW closure deadline | "If DPA is on leave when YELLOW-band deadline hits, does an Acting DPA close, does FM close down-band, or does deadline pause?" |
| H-02 | No handling when PIC transfers vessels mid-incident | "If assigned PIC moves vessels mid-YELLOW investigation, does replacement assume ownership, or does original PIC see it through remotely?" |
| H-03 | No Master-rotation handling mid-SOI / mid-incident | "When Master rotates ashore mid-cycle, does Chief Officer act (SCM chair, GREEN closer, SOI approver), or does original Master finish remotely?" |
| H-04 | No CO (Safety Officer) continuity mid-SOI | "If CO is medically repatriated mid-inspection, does 2/E alternate finish and submit, or must original CO validate remotely?" |
| H-05 | No conflict-of-interest guard when reporter IS the injured/PIC | "When the incident reporter is also the injured party or PIC, does system flag conflict and mandate a different approver?" |
| H-06 | No handling when Master/CO is subject of incident | "If Master (or CO) is implicated in the incident, who chairs SCM / approves SOI / closes GREEN incident?" |

### Cluster B. Authority dead-ends (3)

| ID | Gap | Question |
|----|-----|----------|
| H-07 | RED bias override — what if both DPA and FM refuse? | "If blame-fixation hard-block is triggered RED and FM refuses override, does escalation go to MD, or is closure blocked indefinitely?" |
| H-08 | No FM-unavailable timeout for RED closure | "Max wait for FM RED closure decision? Designated deputy FM when unavailable?" |
| H-09 | No max-iteration cap on Phase 5→3 loop-back | "Max loop-back cycles before mandatory escalation? What prevents infinite rework?" |

### Cluster C. Data model foundations (5)

| ID | Gap | Question |
|----|-----|----------|
| H-10 | Incident-number generation formula undefined | "Format — per-vessel-per-year counter (EBK-2026-001), global fleet sequence, or UUID with prefix? Assigned at draft-save or at submit?" |
| H-11 | M-SCAT taxonomy seed — no canonical CSV | "Do we extract from DNV PDF (OCR risk), compile structured CSV in repo, or seed `TBD — populate by DPA` placeholder?" |
| H-12 | SOI 292-item seed — no structured source | "Extract from SQE S 608 Excel (column-map discovery), accept structured CSV, or placeholder per item?" |
| H-13 | Schema versioning mechanism undefined (grandfathering HOW) | "Per-incident snapshot of taxonomy version (immutable), versioned reference table with FK, or translation map at query time?" |
| H-14 | Medical/D&A PII protection not specified | "Column-encrypt at rest + read-audit, soft-mask by default behind 'view sensitive' perm, or separate `safety_incident_sensitive` table?" |

### Cluster D. Digital signature / non-repudiation (2)

| ID | Gap | Question |
|----|-----|----------|
| H-15 | Digital signature mechanism absent | "Typed name + timestamp (wet-ink look), PKI (DocuSign/Adobe Sign/UETA-compliant), or print-and-wet-sign?" |
| H-16 | Audit trail tamper-evidence not addressed | "Hash chain / cryptographic sig on milestone records (submission, Phase 7, closure)? Required for ISM/legal non-repudiation?" |

### Cluster E. SOI paper-first operational gaps (5)

| ID | Gap | Question |
|----|-----|----------|
| H-17 | Checklist-download idempotency undefined | "Does second download re-toggle 'In Progress', or is it no-op? Reprint workflow?" |
| H-18 | Partial-inspection submission not defined | "Can SO submit 3 of 5 downloaded areas and reset 90-day counter for those 3 only?" |
| H-19 | Lost / damaged paper recovery path missing | "If paper lost/damaged, restart completely or allow re-download + re-conduct with new paper?" |
| H-20 | Scan upload failure (satcomm drop) has no queue/resume | "Findings registered but scan upload interrupted — resume from last byte, retry queue, or re-register after reconnect?" |
| H-21 | Paper ↔ digital count mismatch has no audit mechanism | "How does Master cross-check 8 paper ticks vs 5 digital findings if no per-item DB table exists?" |
| H-22 | Stop-work deferred to V2 — no escalation path for life-threat mid-inspection | "If SO finds life-threat (structural/fire) during inspection, is there expedited incident creation or pure out-of-system informal?" |
| H-23 | Default finding assignee undefined | "If SO leaves assignee blank, who owns the finding (Master / SO / unassigned queue)?" |

### Cluster F. Online-only fragility & notifications (4)

| ID | Gap | Question |
|----|-----|----------|
| H-24 | Online-only degradation unspecified (hard block vs local draft) | "If connectivity drops mid-RED incident entry, auto-save locally and sync on reconnect, or fail hard?" |
| H-25 | Slack webhook failure has no fallback | "If Slack webhook down / rate-limited / account deleted, fall back to email, queue retries, or silent fail?" |
| H-26 | Escalation chain dead-ends at 80% overdue | "If DPA ignores overdue RED notification 24h+, auto-escalate to FM/MD/flag-state, or no further action?" |
| H-27 | No monitoring / observability / SLA | "Uptime SLA? Alerting on Slack/DB/upload-service failures? Tamper detection on audit log? APM/tracing?" |

### Cluster G. Regulatory & legal retention (3)

| ID | Gap | Question |
|----|-----|----------|
| H-28 | IMO flag-state deadline — no auto-calc or escalation | "Should system auto-calculate flag-state notification window on RED incidents with 80% overdue alert, or is PDF export sufficient reminder?" |
| H-29 | No legal hold on 3-year hard-delete | "Legal-hold flag to block file deletion while P&I claim / litigation / flag-state case is open — who triggers, who lifts?" |
| H-30 | Backup / DR not defined | "RPO / RTO for safety data? Geo-replication? Retention of backups (3 / 7 years)?" |

### Cluster H. Performance & concurrent load (2)

| ID | Gap | Question |
|----|-----|----------|
| H-31 | Concurrent-user load during incident response | "Peak concurrent target (10 viewers + 2 editors)? Concurrent-edit conflict resolution or single-editor lock?" |
| H-32 | Repeat root-cause definition ambiguous (vessel vs fleet, reclassified count) | "Repeat = 3+ on SAME vessel or ACROSS fleet in 6 months? Reclassified/superseded records count?" |

### Cluster I. Cross-module hard-blocks (2)

| ID | Gap | Question |
|----|-----|----------|
| H-33 | PMS work-order lookup has no offline fallback (M-SCAT cause 12) | "If PMS unavailable during incident investigation, cache last 3 months on vessel or defer cause-12 assignment to office?" |
| H-34 | CMS crew-data staleness hard-blocks SOI submit | "Max staleness tolerance for CMS department lookup? 'Refresh crew list' button before submit, or hourly sync mandate?" |

### Cluster J. Near-miss reporting culture (1)

| ID | Gap | Question |
|----|-----|----------|
| H-35 | Reporter anonymity unspecified — tension with "any rank creates" | "Is near-miss reporter identity hidden from Master/HOD (anonymized to investigators only), or visible to all with access?" |

> Note: numbering goes to H-35 because Cluster A spans 6 (H-01..H-06); actual count after dedup = 27 (some mapped to same question). Use the question text as the canonical identity.

---

## MED-Severity Gaps (44) — group-batched summary

### Group 1. Data model precision (11)
- `safety_incident` field types / nullability / ENUMs (phase_current, risk_band, schema_version)
- `safety_field_history` column schema (TEXT vs JSON vs type-specific; content_hash)
- Whole-record snapshot / revert semantics (UI, ISM-discovery)
- Attachment orphan cleanup (delink → soft-delete grace, or forever)
- Attachment re-upload versioning (replace / append v2 / reject)
- Signature chain of custody when signer leaves (both shown, replace, acceptance-only)
- Soft-archive schema (`archived_at NULL` vs `is_archived BIT` vs partition)
- CA ↔ PV state-machine (can CA close with PV open; PV blocks incident closure?)
- `safety_recommendation` cardinality (one-per-tier vs child-items table; post-closure mutability)
- `safety_soi_finding` state machine (Open ↔ Pending Closure ↔ Closed; carry-forward; Master-approve timeout)
- `safety_incident_phase_log` shape (one row per transition vs aggregated loops; required columns)

### Group 2. RBAC secondary cases (8)
- Template re-assignment mid-inspection (freeze vs force-upgrade)
- FM edit capability in RED closure (full edit vs decision toggle only)
- FM cross-vessel read during RED review (precedent search?)
- Multi-vessel linked-incident closure authority (single PIC both, or each vessel independent)
- PIC borrow-lessons: copy-paste identifiable vs anonymize/summarize
- Auditor access when Master absent (time-bound guest vs Master-mandatory)
- SCM chair substitution (Chief Officer stands in, or reschedule)
- Rework escalation (vessel ignores rework — days to PIC escalate)

### Group 3. Integration & regulatory edges (9)
- Position-time match tolerance window for MSC-MEPC.3 (hours-old OK?)
- Daily Report missing for incident date (block, accept manual, flag)
- WRH lookback window & query timeout (7d / 30d / lifetime)
- WRH incompleteness in SCM (warn / skip / block)
- Purchase Req FK vs soft-link (survive PO archive?)
- Flag-state reporting threshold variations (same-flag fleet? flag-specific overlays?)
- Class society notification toggle on damage incidents
- MLC injury auto-flag to HR/Crew List module
- COSWP Ch 13 V1 minimum viability without stop-work

### Group 4. SOI operational edges (8)
- Scan minimum resolution / legibility validation
- Paper checklist signatures required (SO, assistant, Master counter-sign?)
- Finding severity threshold for incident creation
- Repeat finding flag/color/metric without auto-escalation
- SOI finding ↔ PMS defect linkage (FK both ways?)
- Cross-functional "different dept" exception for single-dept vessels
- Trainee rotation coverage % formula
- `applicable=false` audit trail + class-dispute handling
- Checklist template versioning (DPA v2 published mid-flight)
- SCM hard-block exact point (schedule / sign / advance) & override
- Closed-Since-Last-SCM snapshot cutoff (close date / schedule date / start date)
- 90-day counter reset timing (upload / approval / cron)
- Master rejection workflow for disputed SO closures
- Paper format PDF-vs-Excel layout consistency + lock-cells
- Photo evidence mandatory by severity tier
- Section 12 per-inspection vs per-cycle scope

### Group 5. Non-functional & UX (8)
- Notification fatigue: digest / quiet hours / per-user preference
- Shore-side time-zone aware notifications
- Email fallback vs replacement for Slack
- Heinrich Ratio zero-division display
- Heinrich Ratio small-sample validity (minimum-N rule)
- CA aging definition (creation / due / last-change; reopen reset)
- Inspection Compliance % formula edges (pending_closure credit, new-vessel N/A)
- Dashboard real-time vs cached (5-min TTL, 1h cron aggregate)
- Dashboard period selection persistence
- Dashboard export (PDF/Excel for management review)
- Archive search surfacing (include-archived checkbox, separate mode)
- Full-text search performance (FTS engine, filter indexing)
- Historical-query latency target (<5s / <30s)
- Audit-log retention vs incident retention (3 vs 7 yr; partition)
- Mobile / iPad responsiveness (signature capture, attachment upload on 7")
- WCAG target & color-only indicators
- Localization (DD-MM-YYYY ambiguity across locales)

*(Note: Group 5 lists ~17 lines but after dedup-to-theme resolves to 8 canonical MED items; consolidated in final questionnaire.)*

### Group 6. Classification & cross-entity (4)
- Incident ↔ near-miss reclassification (mutate single record vs unidirectional escalate vs supersede-create)
- Multi-vessel incident duplicate detection (24h auto-detect + merge prompt)
- SOI finding → incident promotion linkage (FK, join table, or free-text)
- Legacy cause-map many-to-many mappings

### Group 7. Sensitive operational (4)
- PSC auditor privacy redaction (other-crew data in bundle export)
- Rate-limit / spam on near-miss (max/day, min-detail)
- Incident-form language / M-SCAT translations
- Time-zone semantics (UTC vs vessel-local vs shore-local)
- Inspection Compliance % dashboard name-clash (Safety SOI vs PSC Inspection)

---

## LOW-Severity Gaps (14) — defer / V2 candidates

1. Indexes/perf hints called out explicitly in SSOT (vs left to build phase)
2. Legacy archive UI / discoverability within VIMS
3. Reference-data editability (add/edit/delete vs add-only vs deploy-time locked)
4. Near-miss anonymous submission channel (V1 vs V2)
5. M-SCAT taxonomy drift auto-remap (Year 2 additions reconcile Year 1 data)
6. Area-coded item drift across SQE S 608 revisions (2026→2028)
7. Zone vs Area terminology normalization
8. MARPOL pollution reporting (separate track or auto-trigger from Safety?)
9. Heinrich Ratio per-vessel validity on small fleet
10. Browser support baseline (IE11 or modern-only)
11. Purchase Req auto-create vs manual-link trigger
12. `safety_soi_finding.status` explicit ENUM definition
13. Incident demotion (currently only escalation exists)
14. Offline legacy data migration scope (43 incidents — migrate vs read-only archive link)

---

## Recommended Next Steps

1. **Review HIGH cluster** (27 gaps in 10 clusters A–J). Each cluster should be one interrogation round; user answers + I lock D-GAP-xx decisions into SSOT.
2. **Sweep MED gaps in batches** grouped as above (7 groups) — faster because many are spec-precision questions with short answers.
3. **Defer LOW gaps** to SSOT §7 "Open Questions V2" or resolve as build-time judgement.
4. **After sweeps close:** re-increment decision count from 61 → ~88-95, re-export SSOT, THEN proceed to docsuite generation.

---

*Generated from parallel gap-hunter agents 2026-04-17. Raw agent transcripts retained in session log. Update this file in place as gaps are resolved.*

---

## RESOLUTION STATUS (closed 2026-04-17, Session 5)

All HIGH clusters and the MED batch closed via interrogation Rounds 17–20. References-borrowed sweep (Round 21) added 23 further enhancements from a user-contributed reference pack. Breakdown:

| Severity | Count | Status |
|----------|-------|--------|
| HIGH | 27 | ✓ Closed via Rounds 17–19 (Clusters A–J, 35 decisions) |
| MED | 44 | ✓ Closed via Round 20 (38 decisions + Ad-Hoc SCM bonus + DESIGN rename); 11 auto-resolved by locked principles; 11 deferred to docsuite build-time |
| LOW | 14 | Deferred — tracked in SSOT §7 Open Questions V2 |
| Reference-borrow additions | 23 | ✓ Adopted via Round 21 (D-GAP-R01..R23) |

**Total Session 5 contribution:** 136 new decisions added (96 HIGH clusters + 40 MED + bonuses, then 23 from borrow sweep → +98 decisions, with 23 stretching into Round 21). Pre-session lock: 61. Post-session lock: **159**.

The SSOT decisions log (`VIMS-SAFETY-MODULE-SSOT.md` §6) and interrogation trail (`VIMS-SAFETY-REQUIREMENTS-INTERROGATION.md` Rounds 17–21) are now authoritative for all resolved items. This file is retained as a pre-resolution audit artifact.
