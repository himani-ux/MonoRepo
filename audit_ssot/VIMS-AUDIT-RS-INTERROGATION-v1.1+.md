# VIMS Audit & RightShip — Post-Freeze Interrogation Register
**Companion to:** `VIMS-AUDIT-RS-MODULE-SSOT.md` (v0.20, 133 locked decisions)
**Started:** 2026-05-18 PM (post-v1.0-freeze, mid-v1.1 interrogation)
**Purpose:** Drive remaining decisions before KLOSS Step 2 (DocSuite generation). Five questions per batch; user picks/redirects/overrides per Q. Closed Q's become new `D-AUDRS-###` entries appended to SSOT §9 + §4 by the LLM after batch close.

---

## ▶ RESUME HERE — Next session (2026-05-19+)

**🔒 v1.1 INTERROGATION CYCLE COMPLETE 2026-05-19**

**State of play:**
- **Cumulative locked:** D-AUDRS-210..287 (78 v1.1 decisions; 17 batches closed: 1A through 1Q).
- **All 95 interrogation questions resolved** (closed / deferred to v1.2-v1.3 / rejected as not-applicable).
- **Q95 closure:** Internal Audit integration coverage explicitly locked — 8 active integrations + 3 deferred-to-v2 (PMS / SMS Doc Control / Training records) via D-AUDRS-287.
- D-AUDRS-271 cross-module DB-standard sweep RESOLVED externally (dev team handling Safety + Certs).
- D-274 software-offline ambiguity closed.
- D-280 vessel/office rank-source split locked.
- D-285 freeze authority = Prince (no separate DPA/SEQ written sign-off).
- **Scope confirmed at Batch 1H:** This interrogation cycle covers **v1.0 Internal Audit (frozen) + v1.1 External Audit (closing)** only. RightShip (Q38–Q45) deferred to v1.2 build cycle. Manning/Security (Q46–Q50) deferred to v1.3 build cycle.
- **Batch 1J closed** — Q56 acting HoD = DPA+FM; Q57 **REFRAMED** (offline-by-design vessel-visit; new VESSEL_ACKNOWLEDGED gate AUDIT_P_017; D-062 stays); Q58 subsumed; Q59 ok; Q60 ok (cross-dept HoD path).
- **Batch 1K closed** — Q61/Q62/Q64/Q65 **ALL REJECTED as not-applicable** (CoI declarations not real at KSM; vessel-sale handover pack not built — internal-only; GDPR erasure out of scope). Only Q63 locked (15-yr retention, soft-delete only, D-AUDRS-257). Saves: 1 column, 2 gates, 1 background job, 4 UI screens, multiple OPM/privacy-notice drafts.
- **MODEL SHIFT still load-bearing (D-AUDRS-254):** Audit lifecycle now `REPORT_FINALIZED → VESSEL_ACKNOWLEDGED → CLOSURE_IN_PROGRESS`. NC SLA clocks anchor on VESSEL_ACKNOWLEDGED.

**Next action — SSOT §9 BATCH-MERGE (no more interrogation questions):**
1. Append D-AUDRS-210..287 entries to SSOT §9 Decisions Log (78 new rows).
2. Rewrite §11 Cross-Module Dependencies table per D-AUDRS-287 (8 active + 3 deferred-to-v2).
3. Strip "HARD BLOCKER — Flag State confirmation required" from D-AUDRS-061 per D-AUDRS-259.
4. Mark D-AUDRS-112 email-source portion SUPERSEDED per D-AUDRS-264.
5. Add §0.4 Reference Document Versions per D-AUDRS-286 (SSQE Manual Rev 01 Feb 2026).
6. Add §0.5 ID Allocation Convention per D-AUDRS-284.
7. Add v0.21 entry to version history table with all v1.1 R-EXT.2..R-EXT.X groupings.
8. Update §0 Resume Guidance to "v1.1 FROZEN — handoff to KLOSS Step 2".
9. Save backup as `VIMS-AUDIT-RS-MODULE-SSOT.v0.20.bak` before merge.
10. After merge: project memory + MEMORY.md updated to "v1.1 FROZEN at v0.21"; hand off to KLOSS Step 2 DocSuite generation at `VIMS-Audit-Module/` using Certs canonical pattern per D-AUDRS-270.

**Outstanding cross-module action items (deferred to KLOSS Step 2 prep):**
- Certs SSOT update for D-AUDRS-202/213/235/236/238/239/240/241/243 cross-references.
- New `cert_change_log` table to be added to Certs module (D-AUDRS-239).
- Confirm Certs API exposes `version` field for CAS (D-AUDRS-236 Q27 dependency).
- Confirm Class Status Report sync cadence + reconciliation rule in Certs SSOT (D-AUDRS-240 / 243).
- Bidirectional SSOT cross-reference table at the head of both Audit + Certs SSOTs (D-AUDRS-237).

**SSOT §9 batch-merge pending:** all 38 v1.1 decisions to be appended to `VIMS-AUDIT-RS-MODULE-SSOT.md` §9 + §4 + version-history table when interrogation cycle completes (or at any user-requested checkpoint).

**Approximate progress:** ~44 of 95 questions closed/deferred (38 locked + ~6 deferred). Remaining: ~51 questions across cross-cutting v1.0 gaps (Q51–Q79), deployment/legal/integration (Q80–Q90), meta (Q91–Q95).

---

## Working protocol
1. LLM fires 5 questions with a recommended action per question.
2. User responds Q-by-Q (accept / modify / override / "defer to v1.2 / out of scope").
3. LLM writes back the closure into this file (status + final decision + rationale).
4. After each batch, LLM updates SSOT §9 with new `D-AUDRS-###` IDs.
5. Repeat until all 95 closed (or new Qs surface mid-flight).

## Conventions
- **Status** = OPEN | CLOSED | DEFERRED | OUT-OF-SCOPE | SUPERSEDED
- **Recommended Action** = LLM's pre-recommendation. User free to override.
- **Decision** = final wording once user confirms (locked).
- **New SSOT ID** = D-AUDRS-### assigned on closure.

---

## BATCH 1 — v1.1 EXTERNAL AUDIT (Q1–Q37)

### 1.1 Scope boundary

#### Q1 — Class society statutory surveys
> Where do Class society statutory surveys (SOLAS, MARPOL, Loadline, etc.) live? "External audit" in VIMS, or Certificate-module survey events, or both?
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Treat Class statutory surveys as **Certificate-module events** (already covered by Certs SSOT). VIMS Audit v1.1 = ISM/ISPS/MLC system audits only. Cross-link via `linked_cert_ids_csv` per D-202. Rationale: scope creep risk; statutory surveys have very different field sets (loadline marks, hull thickness gauging, etc.).
- **Decision:** Audit and Survey are TWO DISTINCT workflows maintained separately. Statutory class surveys live exclusively in the Certificates module. VIMS Audit v1.1 = ISM / ISPS / MLC / EMS / DOC **system audits only**. Cross-link via `audit_detail.linked_cert_ids_csv` per D-202. No survey fields enter the audit module data model.
- **New SSOT ID:** D-AUDRS-210

#### Q2 — Flag State direct audits
> Flag State direct audits (flag-led, not RO-delegated) — same `audit_classification=EXTERNAL` or new sibling enum?
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Keep `audit_classification=EXTERNAL`; differentiate by `external_audit_org` taxonomy (CLASS_SOCIETY | FLAG_STATE | RO | OTHER) on `audit_detail`. Avoids enum proliferation.
- **Decision:** `audit_classification=EXTERNAL` remains the sole external-audit classification. Differentiation handled by new column `external_audit_org_type` on `audit_detail` with enum {`CLASS_SOCIETY`, `FLAG_STATE`, `RO`, `OTHER`}. Closure flow, finding shape, and cert writeback are identical regardless of issuing organisation. UI may filter / label by org_type but does not branch logic.
- **New SSOT ID:** D-AUDRS-211

#### Q3 — RO ≠ Class society
> Today `external_audit_org` reuses `vessel.class_society`. Vessel can be classed with one society, ISM/ISPS delegated to another, MLC to a third. Does this hold?
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Replace reuse with new `master_external_audit_org` table (id, name, type, country, FK optional to class_society master). Vessel can have N delegations stored on `vessel_audit_delegation` join. Default at audit registration = vessel's class_society but override allowed.
- **Decision:** **Audit RO is a first-class concept distinct from Vessel Class.** Reuse of `vessel.class_society` for audit org is REPLACED. New tables:
  1. `master_external_audit_org` — id, name, `org_type` (per D-211 enum CLASS_SOCIETY/FLAG_STATE/RO/OTHER), country, optional `linked_class_society_ref` (FK to class_society master where applicable).
  2. `vessel_audit_ro_delegation` — vessel_id, `standard_code` (ISM/ISPS/MLC/EMS/DOC), `delegated_org_id` (FK master_external_audit_org), effective_from, effective_to, audit-trail cols.
  
  On external audit registration: `external_audit_org_id` defaults to the delegated RO matching (vessel_id + standard) for the audit_subtype's standard; the field is **overridable** (rare but supported per user — Vessel Class and Audit RO can diverge). Supersedes the `vessel.class_society` reuse portion of D-201.
- **New SSOT ID:** D-AUDRS-212 (supersedes the org-identity portion of D-201)

#### Q4 — Combined DOC audits (multi-vessel)
> Combined DOC audit covers DOC + multiple vessels in one event. `audit_detail` is 1:1 with `psc_inspection`. Does that fit?
- **Status:** ✅ CLOSED 2026-05-18 (with critical refinement: DOC is per-flag)
- **Recommended Action:** **DOC audit = office-side audit** (single audit on the company's DOC); vessel-side SMC audits are separate inspections. Model the combined event as: one DOC audit_detail (auditee=OFFICE_DEPT) + N vessel SMC audit_details (auditee=VESSEL), linked by new `parent_audit_event_id` self-FK. Reuse v1.0 office-internal audit shape for DOC side.
- **Decision:** **DOC is scoped per Flag State, not per company.** KSM holds one separate DOC per flag administration (e.g., Thai-flag DOC + Panama-flag DOC are independent certificates with independent anniversaries and audit cycles). Modeling:
  1. **DOC audit_detail** carries new MANDATORY column `flag_state_code` (FK to flag master) when `audit_subtype` ∈ {DOC_*}. Uniqueness: at most one open DOC audit per (flag_state_code + audit_cycle_year).
  2. **Combined-event model retained:** new self-FK `parent_audit_event_id` on `audit_detail`. One parent DOC audit (auditee=OFFICE_DEPT) + N child vessel SMC audit_details (auditee=VESSEL, only vessels under that flag), linked via the parent FK.
  3. Multi-flag fleet → one DOC audit cycle PER FLAG. SMC audits scoped to vessels under the matching flag.
  4. Cert writeback (D-202) applies per-flag — DOC cert in Certs module is per-flag.
- **New SSOT ID:** D-AUDRS-213

#### Q5 — Interim DOC for new-build / transfer
> Interim DOC for newly built/transferred vessels — is Interim DOC issuance audit-driven? Captured?
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Yes — add `DOC_INTERIM` to D-200 enum (currently D-208 only mentions SMC/MLC/ISPS_INTERIM). Cert anniversary = NOT_SET on Interim; Certs module records "interim until full audit done within 12 months". Captured but no alert ladder (matches Initial pattern per D-209).
- **Decision:** **Both DOC_INTERIM and DOC_INITIAL are first-class audit subtypes.** Confirms D-207's `DOC_INITIAL` and adds `DOC_INTERIM` to the external_audit_subtypes_csv enum. Behaviour:
  - **DOC_INITIAL** (per D-207): creates DOC cert in Certs module on close-out; sets first anniversary; per-flag (per D-213).
  - **DOC_INTERIM**: issued when company first applies for DOC for a new flag, new ship type, or major change. Cert anniversary = NOT_SET; no alert ladder (matches Initial pattern from D-209); superseded by next full DOC audit close-out within 12 months. Per-flag (per D-213).
  - Both subtypes obey the per-flag rule from D-213.
  - External audit subtype enum total now: **18 values** (was 16 after D-208/D-200; +DOC_INTERIM = 17; +affirmation of DOC_INITIAL already counted; with D-208's SMC/MLC/ISPS Interims and Initials already included, recounting: DOC[INITIAL, INTERIM, ANNUAL, RENEWAL] + SMC[INITIAL, INTERIM, INTERMEDIATE, RENEWAL] + MLC[INITIAL, INTERIM, INTERMEDIATE, RENEWAL] + ISPS[INITIAL, INTERIM, INTERMEDIATE, RENEWAL] + ADDITIONAL = **17 + 1 ADDITIONAL = 18** if ADDITIONAL retained; confirm at SSOT merge).
- **New SSOT ID:** D-AUDRS-214

#### Q6 — ISPS Initial Verification on first SSP approval
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Treat as `ISPS_INITIAL` per D-207. Same flow as DOC_INITIAL — create cert in Certs module + set first anniversary.
- **Decision:** ISPS Initial Verification = `ISPS_INITIAL` per D-207. No new subtype. Workflow identical to DOC_INITIAL: creates ISSC cert in Certs module on close-out + sets first anniversary. Single audit subtype handles SSP-approval-driven verification.
- **New SSOT ID:** D-AUDRS-215

#### Q7 — Additional ISM audits resetting cycle
> Additional ISM audit triggered by operator transfer / major change. D-209 says anniversary LEAVE_UNCHANGED for non-Initial. But what if the additional audit IS the audit that legally resets the cycle?
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Add explicit `is_cycle_resetting` BIT on audit_detail, defaulting OFF. Set ON manually by DPA when the additional audit is, in fact, a re-Initial event (e.g., operator transfer). When ON, cert anniversary is recomputed in Certs module via writeback. Audit trail captures who flipped it.
- **Decision:** New column `audit_detail.is_cycle_resetting` BIT NOT NULL DEFAULT 0. DPA-only authority to flip ON (new server-side enforcement via existing `AUDIT_P_*` gate set, gate TBD at SSOT merge). When ON at close-out, the cert writeback (D-202) **overrides** D-209's default LEAVE_UNCHANGED and recomputes cert anniversary in Certs module. Mandatory companion fields: `cycle_reset_reason` ≥100 chars, `cycle_reset_authorised_by` (user_id), `cycle_reset_authorised_at` (datetime). All events logged to `psc_audit_log` with a dedicated event_type.
- **New SSOT ID:** D-AUDRS-216

### 1.2 Post-facto registration

#### Q8 — SLA for entering external audit
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Soft target 7 days, hard cap 30 days from audit completion date. Beyond 30 days requires DPA override with reason ≥50 chars. Captured in `late_registration_reason`.
- **Decision:** Registration SLA = **7 days soft target / 30 days hard cap** from audit completion date. Between 7 and 30 days: in-system warning banner + email/Slack reminder to DPA. Beyond 30 days: hard block on save UNLESS DPA-authorised override with `late_registration_reason` ≥50 chars. New columns on `audit_detail`: `late_registration_reason` (nvarchar max nullable), `late_registered_by` (varchar 100), `late_registered_at` (datetime). Every override = audit-trail entry.
- **New SSOT ID:** D-AUDRS-217

#### Q9 — Audit report received in pieces (draft → final)
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Allow `external_audit_report_pdf` to be replaced until status=CLOSED. Versioned in `audit_attachment` with `category=AUDIT_REPORT_DRAFT` vs `AUDIT_REPORT_FINAL`. Close-out requires FINAL.
- **Decision:** External audit report attachments are **versionable** via `audit_attachment` table (D-060). Two new attachment categories added to D-060 enum:
  - `AUDIT_REPORT_DRAFT` — replaceable; can have multiple versions; all retained
  - `AUDIT_REPORT_FINAL` — close-out gate; ≥1 required for status=CLOSED transition
  
  Drafts retained for audit trail (never deleted, only soft-deleted via is_deleted=1). Final report can also be replaced (new version) but only by DPA with reason ≥50 chars. UI shows version history per audit.
- **New SSOT ID:** D-AUDRS-218

#### Q10 — No PDF report (letter/email only)
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Make PDF optional but require *some* attachment (PDF / DOCX / scanned letter / forwarded email export). Mandatory rule: ≥1 attachment of `category=AUDIT_REPORT_*` before close-out.
- **Decision:** PDF report not strictly mandatory at close-out. Close-out gate: **≥1 attachment with category ∈ {`AUDIT_REPORT_FINAL`, `AUDIT_REPORT_LETTER`, `AUDIT_REPORT_EMAIL_EXPORT`}**. Two new categories added to D-060 enum (in addition to those from D-218):
  - `AUDIT_REPORT_LETTER` — scanned official letter (PDF / JPG / PNG)
  - `AUDIT_REPORT_EMAIL_EXPORT` — exported email (EML / PDF / DOCX)
  
  When close-out attachment is LETTER or EMAIL_EXPORT (not FINAL), DPA must enter `evidence_completeness_attestation_text` ≥100 chars at close-out describing why no formal report exists. Stored on `audit_detail.evidence_completeness_attestation_text` + `_attested_by` + `_attested_at`. Mime type whitelist for attachments: PDF / DOCX / EML / JPG / PNG (matches D-076 with EML added).
- **New SSOT ID:** D-AUDRS-219

#### Q11 — Who registers external audits?
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Both Master and Office (any user with `AUDIT_P_013`). De-dup via uniqueness on (vessel_id, audit_subtype, external_audit_org_id, audit_date) with conflict resolution = first-write-wins + system flag.
- **Decision:** **Registration authority is role-scoped by `auditee_type`** (no cross-confirmation handshake):
  - **`auditee_type=VESSEL`** → registered by **Vessel Master only** (VESSEL_MASTER role + AUDIT_P_013 gate)
  - **`auditee_type=OFFICE_DEPT`** → registered by **DPA or Marine Supt** (DPA role OR OFFICE_SUPT role with marine sub-scope + AUDIT_P_013 gate)
  
  Server-side enforcement on save (HTTP 403 if registrant role ≠ allowed roles for the chosen auditee_type). Captured on `audit_detail.registered_by_user_id` + `registered_by_role`. No cross-confirmation step at registration (subsequent review/rework loop per D-AUDRS-222 [Q13] provides the second-eye check). Open question for SSOT merge: define how "Marine Supt" vs other Supt sub-scopes is distinguished — likely via a new `users.supt_scope` enum (MARINE / TECH / OTHER) or via `master_hod_assignment` dept filter. Flag for batch close-out review.
- **New SSOT ID:** D-AUDRS-220

#### Q12 — Duplicate external audit registration
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Background dedup checker surfaces "possible duplicate" banner on save; explicit "Yes, separate audit" confirm required to bypass.
- **Decision:** Soft de-dup with conflict resolution UI:
  1. **De-dup candidate-match key (composite, used in query on save):** `(vessel_id OR flag_state_code-for-DOC, audit_subtype, external_audit_org_id, audit_start_date ±7 days)`.
  2. On save, system runs candidate-match query; if any match found, UI shows "**Possible duplicate**" banner linking to existing record.
  3. User must explicitly choose:
     - **"Yes, this is a separate audit"** + reason ≥50 chars → proceeds with new record; reason stored on `audit_detail.dedup_override_reason`.
     - **"Merge into existing"** → current entry's data merged into the matched record (new attachments preserved; conflicting field values audit-trailed). Merge gated to DPA only.
  4. DB-level UNIQUE constraint (vessel_id_or_flag_code, audit_subtype, external_audit_org_id, audit_start_date) with override allowance via the soft-dedup workflow.
- **New SSOT ID:** D-AUDRS-221

### 1.3 Findings entry and dispute

#### Q13 — Vessel/office disagree on NC vs Observation
- **Status:** ✅ CLOSED 2026-05-18 (refined — rework loop replaces DPA arbiter)
- **Recommended Action:** External auditor's classification is **authoritative** — vessel/office enters what the report says, no internal reclassification permitted. If report is ambiguous, DPA decides + records decision rationale ≥50 chars on `audit_finding.classification_rationale`.
- **Decision:** **Reuse existing PSC CAR rework-loop pattern** for external audit findings. Workflow:
  1. **Registrant enters initial classification** (NC vs Observation, severity) based on the external auditor's report verbatim. For vessel audit → Master enters. For office audit → DPA/Marine Supt enters (per D-AUDRS-220).
  2. **Office review step** (matches existing PSC PIC review): Office Supt (or DPA for office-audit findings) reviews each finding. Can:
     - **ACCEPT** → finding proceeds to closure workflow (NC or Observation flow per D-040)
     - **RESEND FOR REWORK** → returns to registrant with reason ≥20 chars (matches D-074 rework min length); reuses existing `REWORK_REQUESTED` CAR state semantics
  3. **Re-classification** happens implicitly on rework — registrant updates finding_type / category / severity per office feedback, resubmits.
  4. Rework history captured on existing `psc_deficiency_action_history` table (no new table). Reason stored on action_history row.
  5. No new "DPA arbiter" concept; existing rework loop is the arbitration mechanism.
  6. **Hard rule:** classification on FINAL closed finding must match the external auditor's report verbatim where unambiguous. Ambiguity resolved through the rework loop until office accepts.
- **New SSOT ID:** D-AUDRS-222

#### Q14 — Non-standard auditor categories
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** New per-org mapping table `master_external_auditor_category_map` (org_id, raw_label, mapped_finding_type, mapped_subcategory). Seed for DNV/ABS/LR/BV/CCS/NK/KR/RINA common labels. Free-text bucket if no mapping.
- **Decision:** New master table `master_external_auditor_category_map` with columns:
  - `id` uniqueidentifier PK
  - `org_id` FK `master_external_audit_org.id` (per D-AUDRS-212)
  - `raw_label` nvarchar(200) — the auditor's verbatim label (e.g., "Memorandum", "Condition", "Finding-Major")
  - `mapped_finding_type` varchar(20) — NC | OBSERVATION (per D-040 enum)
  - `mapped_subcategory` varchar(40) — MAJOR_NC | MINOR_NC | OBSERVATION | IMPROVEMENT_SUGGESTION | OFI (per D-041)
  - `effective_from`, `effective_to`, audit-trail cols
  
  **Seed at KLOSS Step 2** with top IACS class society mappings (DNV, ABS, LR, BV, CCS, NK, KR, RINA) + common Flag State patterns. At finding entry, system auto-suggests mapping based on (`external_audit_org_id` + raw_label entered); user accepts or overrides. Mappings missing from master → DPA reviews and adds (audit-trailed). Mapping suggestions are advisory; registrant's chosen classification is what proceeds into the D-AUDRS-222 rework loop.
- **New SSOT ID:** D-AUDRS-223

#### Q15 — Sub-paragraph ISM references
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Allow 4-level depth via optional `clause_subref_text` column (e.g., master row ISM 7.1, subref ".2"). UI displays "7.1.2". Avoids restructuring master.
- **Decision:** Add optional column `audit_finding.clause_subref_text` (nvarchar(50) nullable). Master tables retain their currently-locked depths (D-088 ISM at 3-level X.Y.Z, D-089 ISPS Part A only, D-090 MLC at Regulation+Standard-A combined). When auditor cites a deeper reference:
  - Pick the closest matching master row (e.g., ISM "7.2")
  - Enter the trailing portion in `clause_subref_text` (e.g., ".3", "(a)", "(b)(ii)")
  - UI displays concatenated form: "ISM 7.2.3" or "ISM 7.2(a)"
  
  Validation pattern: `^[\.\(\)a-zA-Z0-9\s]{1,50}$` when non-null. Applies to all clause masters (ISM, ISPS, MLC, SOLAS, STCW, MARPOL, COLREG, KSM SMS). PDF rendering concatenates clause_ref_text + clause_subref_text. No master restructuring required.
- **New SSOT ID:** D-AUDRS-224

#### Q16 — No clause cited
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Use `rule_book_type=OTHER` + `clause_ref_text="General — no clause cited"` (or auditor's verbatim phrase). 5–200 char rule applies.
- **Decision:** Reuse existing `rule_book_type=OTHER` bucket (D-077). Populate `clause_ref_text` with the auditor's verbatim phrase OR "General — no clause cited" when truly absent. D-077's 5–200 char validation applies. `clause_ref_id` and `clause_subref_text` (D-AUDRS-224) left NULL. Dashboards add a counter widget "Findings without specific clause reference" for QA monitoring; sustained high counts signal poor audit-report quality or lazy data entry — DPA reviews quarterly.
- **New SSOT ID:** D-AUDRS-225

#### Q17 — Finding cites multiple clauses
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Add `audit_finding_clause` join table (deficiency_id, rule_book_type, rule_clause_id, sequence_no, is_primary BIT). Primary clause shown in lists; others on detail.
- **Decision:** New junction table `audit_finding_clause`:
  ```
  id              uniqueidentifier PK
  deficiency_id   uniqueidentifier FK psc_deficiency.id (NOT NULL)
  rule_book_type  varchar(20) NOT NULL  -- ISM | ISPS | MLC | SOLAS | STCW | MARPOL | COLREG | FLAG | KSM_SMS | OTHER
  rule_clause_id  uniqueidentifier NULL  -- polymorphic FK to clause master per rule_book_type
  clause_ref_text nvarchar(200) NOT NULL  -- denormalised display string
  clause_subref_text nvarchar(50) NULL    -- sub-paragraph per D-AUDRS-224
  sequence_no     int NOT NULL DEFAULT 1
  is_primary      BIT NOT NULL DEFAULT 0
  created_by, created_date, is_deleted
  CHECK: exactly one row per deficiency_id has is_primary=1 (app-layer enforcement)
  ```
  Existing `audit_finding.clause_ref_id` / `clause_master_type` / `clause_ref_text` retained as **denormalised mirror of the is_primary=1 junction row** for list-page performance (continues D-066's separation philosophy). Application layer keeps them in sync on every junction write. Dashboards filter on primary; finding detail page shows all junction rows in sequence_no order.
- **New SSOT ID:** D-AUDRS-226

#### Q18 — Vessel disputes finding post-acceptance
- **Status:** ✅ CLOSED 2026-05-18 — **RECOMMENDATION REJECTED**
- **Recommended Action:** Add `dispute_status` (NONE | RAISED | RESOLVED_UPHELD | RESOLVED_OVERTURNED) + `dispute_text` + `dispute_resolution_text` + audit trail of dispute events. Dispute does NOT halt closure clock; closure must proceed unless auditor agrees to overturn externally.
- **Decision:** **No dispute mechanism in VIMS.** Per ISM audit practice, disagreements between vessel/office and external auditor are resolved during the audit's **closing meeting** BEFORE the report is finalised and issued. Once the auditor's report is issued, its findings are **immutable inputs to VIMS**. If vessel/office disagrees post-issuance, that conversation happens off-system with the auditor; only an amended report (if the auditor agrees to revise) is registered in VIMS via the attachment replacement path (D-AUDRS-218) and findings updated accordingly. No `dispute_*` columns, no dispute gate, no dispute audit-trail event. **Rationale:** The proposed dispute mechanism would invite gaming (vessels disputing findings to delay closure or contest severity); the closing-meeting checkpoint already provides the legitimate dispute window.
- **New SSOT ID:** D-AUDRS-227

### 1.4 Closure (EXTERNAL_AUDITOR_CLOSED state)

#### Q19 — No formal close-out letter from auditor
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Make close-out letter attachment "preferred but not mandatory". If absent, DPA must enter `closure_evidence_text` ≥100 chars describing what evidence was received (email, verbal, etc.) + attach correspondence export. Audit trail.
- **Decision:** D-204's "external close-out letter attachment" requirement softened. Close-out gate now permits **either**:
  - Formal close-out letter (new attachment category `EXTERNAL_AUDITOR_CLOSEOUT_LETTER`), OR
  - **`closure_evidence_text` ≥100 chars** on `audit_finding` describing alternative evidence + at least one attachment with category `CLOSURE_ALTERNATIVE_EVIDENCE` (new category). Acceptable forms: emails / call notes / next-audit confirmation memos.
  
  DPA performs the attestation by entering closure_evidence_text + selecting the corresponding attachment. Audit-trail event `EXTERNAL_CLOSURE_VIA_ALT_EVIDENCE` raised on each such close-out. Dashboard widget flags alternative-evidence closures for quarterly DPA QA review.
- **New SSOT ID:** D-AUDRS-228

#### Q20 — Auditor closes externally but vessel hasn't completed action
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Allow VIMS to close on auditor's authority (mark `closed_by_auditor_only=1`); ISM-style internal action plan continues until vessel-actual completion captured. Risk surfaced on dashboard as "Closed externally, internal action ongoing".
- **Decision:** Decouple external closure from internal action completion. New columns on `audit_finding`:
  - `external_closure_status` enum {`NOT_CLOSED_EXTERNALLY` (default), `CLOSED_EXTERNALLY_BY_AUDITOR`, `CLOSED_VESSEL_COMPLETE`, `CLOSED_BOTH`}
  - `internal_action_completion_target_date` date NULL
  - `internal_action_completion_actual_date` date NULL
  
  Auditor authority is final for **cert state**: when external_closure_status moves to `CLOSED_EXTERNALLY_BY_AUDITOR`, finding's CAR state can transition to CLOSED and cert writeback (D-202) proceeds. Internal action completion is tracked **separately for KSM SMS effectiveness records** — does NOT block cert validity. Dashboard widget "Closed externally, internal action ongoing" flags such findings until `CLOSED_BOTH`. Lead Auditor (or DPA for external NCs per D-204) confirms internal action completion as a separate event.
- **New SSOT ID:** D-AUDRS-229

#### Q21 — Auditor reopens at next verification
- **Status:** ✅ CLOSED 2026-05-18 — **RECOMMENDATION REJECTED**
- **Recommended Action:** New action "Reopen externally-closed NC" (gate AUDIT_P_015 new). Creates linked finding under the new audit with `parent_finding_id` pointer; old finding stays CLOSED but flagged "REOPENED-AT (date)" on detail.
- **Decision:** **External auditors do not reopen previously-closed findings.** Per audit practice, if the same issue is observed at the next periodic audit, the auditor raises a **NEW** finding (with a fresh NC reference) under the new audit. The previously-closed finding remains closed and untouched. **No `parent_finding_id` column, no reopen gate, no finding-chain UI.** Recurrence/trend analysis is performed downstream (post-v1.1 reporting concern) by content/clause matching on the unfiltered finding population, not by explicit reopen linkage. Rationale: closed audit records are statutory immutable; reopens would corrupt the historic record.
- **New SSOT ID:** D-AUDRS-230

#### Q22 — Effectiveness review for external NCs
> ISM 12.2 requires effectiveness review for ALL NCs. D-204 says no EffRev for external NCs.
- **Status:** ✅ CLOSED 2026-05-18 — **SUPERSEDES EffRev portion of D-AUDRS-204**
- **Recommended Action:** Re-open D-204 portion: make EffRev MANDATORY for external Major NC; OPTIONAL for external Minor NC + Observation. Lead Auditor of internal audit (next periodic) inherits the review duty. Alternative: shift EffRev duty to DPA for external NCs.
- **Decision:** Tiered Effectiveness Review for external findings:
  - **External Major NC** → EffRev **MANDATORY**
  - **External Minor NC** → EffRev **OPTIONAL** (recorded if performed; not a state gate)
  - **External Observation** → no EffRev (matches D-040)
  
  Performer = **DPA** (no internal Lead Auditor exists for external audits per D-204). Stored on existing `audit_finding_nc` Part E columns (already defined for internal). Method enum extended with new value `EXTERNAL_AUDIT_VERIFICATION` (i.e., next periodic external audit confirms effectiveness, recorded retroactively). New column `audit_finding_nc.effectiveness_review_required` BIT NOT NULL — defaulted at finding creation based on (is_external + nc_category):
  - is_external=1 + MAJOR_NC → 1
  - is_external=1 + MINOR_NC → 0 (DPA may toggle ON manually)
  - is_external=0 → 1 (internal NC unchanged from D-AUDRS-044)
  
  When required=1, finding cannot reach `EXTERNAL_AUDITOR_CLOSED` until EffRev is completed (extends D-204 state machine).
  
  **ISM 12.2 compliance rationale:** ISM Code 12.2 mandates effectiveness review for all corrective actions. Internal Minor NCs are exempted by KSM practice (low risk, high volume) — same exemption logic extends to external Minor NCs. External Major NCs are too consequential to skip; mandatory EffRev protects KSM's own SMS audit posture when KSM is audited by Class/Flag on its NC handling.
- **New SSOT ID:** D-AUDRS-231 (supersedes EffRev portion of D-204)

#### Q23 — Major external NC hot-path
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Add `priority` enum (NORMAL | URGENT | CRITICAL) on external NCs. CRITICAL = certificate suspended/withdrawn → triggers immediate DPA + Marine Director notification + 24h response SLA. Normal = standard flow.
- **Decision:** New columns on `audit_finding`:
  - `priority` enum {`NORMAL` (default), `URGENT`, `CRITICAL`}
  - `priority_set_at` datetime
  - `priority_set_by` user_id
  - `priority_set_reason` nvarchar(max) — ≥50 chars when manually escalated to URGENT/CRITICAL
  
  **Auto-escalation rules** (server-side at save):
  - external NC + nc_category=MAJOR_NC + certificate_impact ∈ {SUSPENDED, WITHDRAWN} → auto-set `priority=CRITICAL`
  - external NC + nc_category=MAJOR_NC + certificate_impact=RENEWAL_AT_RISK → auto-set `priority=URGENT`
  - all other findings → `priority=NORMAL` (DPA may manually escalate)
  
  **CRITICAL behaviour:**
  1. Immediate triple-channel notification (D-111) to DPA + Marine Director + Tech Director on save. New notification type `AUDIT_NC_CRITICAL`.
  2. **24-hour SLA** for initial containment action (overrides KSM-F-NC-001's 72-hour Major NC rule for this priority tier).
  3. Master CA plan submission target: **7 days** (overrides D-AUDRS-047's 30/90 default for CRITICAL).
  4. Dashboard tile with red banner: "Critical Cert-Suspended Findings — Open" with count + drill-through.
  5. Daily-digest cc to DPA + Marine Director until closed.
  
  **URGENT behaviour:** notification fanout only; SLAs follow Major NC defaults from D-AUDRS-047.
- **New SSOT ID:** D-AUDRS-232

### 1.5 Certs module writeback

#### Q24 — `linked_cert_ids_csv` UX
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Type-ahead list pre-filtered to (vessel_id + cert_type matching audit_subtype). Multi-select. Display cert number + expiry + status inline.
- **Decision:** Cert linkage UI at external audit registration:
  - **Type-ahead multi-select widget**, pre-filtered by:
    - `vessel_id` matches audit's vessel (when auditee_type=VESSEL)
    - OR `flag_state_code` matches DOC audit's flag (when auditee_type=OFFICE_DEPT + audit_subtype ∈ DOC_*)
    - AND `cert_type` matches the audit_subtype's standard (e.g., SMC_RENEWAL → SMC certs; DOC_INITIAL → DOC certs for the relevant flag)
    - AND `is_active=1` in default suggestion list (DPA can toggle "show withdrawn/expired" filter)
  - **Display per item:** cert number · issue date · expiry date · status · class society / Audit RO (per D-AUDRS-212)
  - **Multi-select.** Required **≥1 selection** when audit_classification=EXTERNAL (hard SUBMIT gate).
  - **Validation on save:** each selected cert's vessel_id (or flag) must match the audit's scope; HTTP 422 with clear error on mismatch.
  - **Data API:** read-only call to Certs module's cert-search endpoint; results cached client-side for the registration session.
- **New SSOT ID:** D-AUDRS-233

#### Q25 — Forgotten cert linkage
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Allow add until status=CLOSED. After close-out, edit requires DPA with audit-trailed reason ≥50 chars.
- **Decision:** Cert linkage mutable until status=CLOSED without restriction (any user with `AUDIT_P_013` per D-AUDRS-220 can edit). Post-close-out: **DPA-only** with `cert_linkage_amendment_reason` ≥50 chars + audit-trail event `CERT_LINKAGE_AMENDED_POST_CLOSURE`. New columns on `audit_detail`:
  - `cert_linkage_last_amended_at` datetime NULL
  - `cert_linkage_last_amended_by` varchar(100) NULL
  - `cert_linkage_amendment_reason` nvarchar(max) NULL (latest only — full history on `psc_audit_log`)
  
  Each post-closure amendment that **adds** a cert triggers a fresh `audit_cert_writeback_outbox` row (per D-AUDRS-234) for the newly linked cert. Removals from the linkage do NOT reverse prior writebacks (those already affected cert state; reversal would require explicit cert-side amendment with its own paper trail per D-AUDRS-239).
- **New SSOT ID:** D-AUDRS-235

#### Q26 — Transactional writeback
- **Status:** ✅ CLOSED 2026-05-18 (presented as "Q25" in Batch 1E — register Q25 [forgotten cert linkage] remains OPEN and queued for Batch 1F)
- **Recommended Action:** Two-phase: (1) audit close-out commits; (2) writeback queued via outbox pattern with retry. If writeback fails after 3 retries, surfaced on DPA dashboard for manual intervention. Audit never blocked by Certs failure.
- **Decision:** **Outbox pattern** for cert writeback:
  1. Audit close-out transaction writes to audit-module tables only. In the same DB transaction, insert one row into new table `audit_cert_writeback_outbox` (id, audit_id, cert_id, writeback_payload_json, status enum {PENDING/IN_FLIGHT/DELIVERED/FAILED}, attempt_count int, last_attempt_at, last_error_text, created_at, delivered_at, audit-trail cols).
  2. Background worker polls outbox (every 60s) for PENDING/FAILED rows with attempt_count<3, writes to Certs module API.
  3. Success → status=DELIVERED + audit-trail event `CERT_WRITEBACK_DELIVERED` on `psc_audit_log`.
  4. Failure → exponential backoff (60s / 5m / 30m), attempt_count++ ; after 3 retries → status=FAILED.
  5. Failed outbox rows surfaced on **DPA dashboard widget "Failed Cert Writebacks"** with: audit ref · cert ref · error text · retry button (manual retry resets attempt_count). DPA may alternatively reconcile manually in Certs module.
  6. Audit close-out **never blocked** by Certs availability — eventual consistency guarantee.
- **New SSOT ID:** D-AUDRS-234

#### Q27 — Cert state conflict
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Audit writeback uses **CAS (compare-and-set)** on cert state version. If Certs module state changed since audit started, writeback fails → DPA shown both states + manual reconcile.
- **Decision:** Compare-and-Set (CAS) on cert state version:
  1. Cert rows in Certs module carry a `version` int (auto-incremented on every state-affecting update — existing pattern; confirm at Certs SSOT cross-ref).
  2. On audit close-out, outbox payload (D-AUDRS-234) captures the cert version observed at registration time (`cert_version_at_registration` column on `audit_cert_writeback_outbox`).
  3. Worker writeback sends version in the update API call; Certs module rejects with HTTP 409 Conflict if current cert version ≠ payload version.
  4. **On 409 → outbox row status=CONFLICT** (new outbox status). Row surfaced on DPA "Conflicted Cert Writebacks" dashboard widget showing: current Certs state · proposed writeback · diff.
  5. DPA chooses:
     - **"Accept current state — discard writeback"** → outbox row status=DISCARDED with reason ≥50 chars; cert state unchanged.
     - **"Force writeback — overrides current state"** → outbox row status=FORCE_DELIVERED with reason ≥100 chars; cert state updated to audit's value; `cert_change_log` (per D-AUDRS-239) entry annotated `FORCE_DELIVERED_BY_DPA`.
  6. Non-conflict failures (network, schema, etc.) follow standard retry per D-AUDRS-234.
  
  **Dependency:** Confirm Certs module API exposes `version` field and accepts it in update calls. Flag for cross-module integration spec.
- **New SSOT ID:** D-AUDRS-236

#### Q28 — Certs SSOT drift
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Update Certs SSOT with explicit "D-AUDRS-202 supersedes D-CERT-025 for v1.1 external-audit-triggered cert state changes". Maintain bidirectional cross-reference at top of each SSOT.
- **Decision:** Bidirectional SSOT cross-reference required:
  1. **Certs SSOT update** (at next Certs SSOT revision): add entry "D-AUDRS-202 + D-AUDRS-213 + D-AUDRS-235 + D-AUDRS-236 + D-AUDRS-238 + D-AUDRS-239 supersede or extend D-CERT-025 for v1.1 external-audit-triggered cert state changes. See Audit SSOT §X." Plus pointers for each subsequent v1.1+ decision that affects Certs.
  2. **Top-level cross-reference table** at the head of both SSOTs listing all cross-module supersessions/extensions. Format: source_decision · target_decision · effective_from · summary.
  3. **Doc-review checklist item** added to KLOSS Step 2 DocSuite generation: any future change to a cross-module decision triggers verification + update of the counterpart SSOT.
  4. **Mechanical re-grep check** at KLOSS Step 2: grep both SSOTs for "supersedes D-CERT-*" and "supersedes D-AUDRS-*" cross-mentions; cross-validate counterparts exist. Fail DocSuite if mismatch.
  5. **Action owner:** LLM/user (this session or next) updates Certs SSOT in a dedicated session before KLOSS Step 2 begins.
- **New SSOT ID:** D-AUDRS-237

#### Q29 — Cert suspension trigger
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** SUSPENDED/WITHDRAWN states require: (a) external auditor's close-out letter attached AND (b) DPA two-step confirm AND (c) automatic Flag State notification record (just a flag, actual notification is out-of-band). UI dialog warns of consequences.
- **Decision:** Multi-gate sequence required when audit close-out drives cert state → SUSPENDED or WITHDRAWN:
  1. **Attachment gate:** auditor's final report (D-AUDRS-218) OR alt-evidence path (D-AUDRS-219 / D-AUDRS-228) MUST be present.
  2. **DPA two-step confirm:**
     - Step 1 (warning dialog): "This will SUSPEND/WITHDRAW certificate [number]. Vessel cannot trade against this cert. Continue?" → Cancel/Continue.
     - Step 2 (typed confirmation): DPA must **type the cert number** to confirm intent (anti-misclick).
  3. **Flag State notification capture:** new columns on `audit_detail`:
     - `flag_state_notification_required` BIT NOT NULL DEFAULT 0 (auto-set 1 when cert state → SUSPENDED/WITHDRAWN)
     - `flag_notification_scheduled_at` date NULL
     - `flag_notification_completed_at` date NULL
     - `flag_notification_attachment_id` FK to `audit_attachment` NULL (the formal letter sent to Flag State Administration)
     - `flag_notification_reason_text` nvarchar(max) NULL (≥100 chars when scheduled)
     
     Actual notification is OUT-OF-BAND (KSM sends formal letter via existing channels per ISM Code 13.5); VIMS tracks the obligation and its completion. Reminder notifications fire if `flag_notification_scheduled_at` passes without `flag_notification_completed_at`.
  4. **Triple-channel notification** (per D-AUDRS-111) on save: DPA + Marine Director + Tech Director + Commercial Director. New notification type `AUDIT_CERT_SUSPENDED_OR_WITHDRAWN`.
  5. Outbox writeback (D-AUDRS-234) proceeds with the cert state change after all gates pass.
- **New SSOT ID:** D-AUDRS-238

#### Q30 — Certs module audit-originated change log
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Certs module gets new `cert_change_log.source_type=AUDIT` + `source_ref=audit_id` field. Audit_detail link is *display*; cert_change_log is *immutable history*.
- **Decision:** New table in **Certs module** (cross-module obligation): `cert_change_log`:
  ```
  id              uniqueidentifier PK
  cert_id         uniqueidentifier FK vessel_cert.id NOT NULL
  change_type     varchar(40) NOT NULL  -- STATE_CHANGE | ANNIVERSARY_SET | EXPIRY_AMENDED | LINKAGE | OTHER
  from_state      varchar(60) NULL      -- snapshot before change
  to_state        varchar(60) NULL      -- snapshot after change
  source_type     varchar(20) NOT NULL  -- MANUAL | AUDIT | SYSTEM | MIGRATION
  source_ref_id   uniqueidentifier NULL -- polymorphic FK; when source_type=AUDIT → audit_detail.inspection_id
  source_ref_type varchar(40) NULL      -- e.g., 'AUDIT_DETAIL' when source_type=AUDIT
  changed_by_user_id  varchar(100) NOT NULL
  changed_at      datetime NOT NULL DEFAULT GETDATE()
  change_reason_text  nvarchar(max) NULL
  -- append-only: no UPDATE allowed; no DELETE allowed (enforce via trigger + RBAC)
  ```
  
  **Pattern:** `audit_detail.linked_cert_ids_csv` (D-202) = forward link (audit → cert, for navigation). `cert_change_log` = backward audit trail (cert → originating events, immutable history). Both required.
  
  **Cross-module action item:** add this table to Certs module SSOT + DocSuite. Coordinate with D-AUDRS-237 (Certs SSOT update obligation).
  
  **Read pattern on cert detail page:** "Recent changes" panel queries `cert_change_log` ordered by changed_at DESC. AUDIT-source rows link back to the originating audit detail page.
- **New SSOT ID:** D-AUDRS-239

### 1.6 Anniversary lifecycle

#### Q31 — Cert anniversary ≠ audit completion date
- **Status:** ✅ CLOSED 2026-05-18 (**refined — defer to Class Status Report**)
- **Recommended Action:** Initial audit close-out form has separate field `cert_anniversary_date_override` defaulting to audit completion date but editable. Stored on Certs module's cert row, not on audit_detail.
- **Decision:** **Cert anniversary date is sourced from the Class Status Report sync** (existing Certs-module pattern), not from audit-side override. Logic:
  1. At audit close-out for INITIAL subtypes, the writeback (D-AUDRS-234) sends audit completion date as the **proposed anniversary** to Certs module.
  2. Certs module accepts the proposed value as a working anchor.
  3. On next Class Status Report sync (KSM's existing periodic sync from Class society reports), the cert's authoritative anniversary is reconciled against the Class Status Report value. If divergence detected, **Class Status Report value wins** (matches Certs-module reconciliation rule).
  4. The reconciliation event is captured in `cert_change_log` (D-AUDRS-239) with `change_type=ANNIVERSARY_SET`, `source_type=SYSTEM`, `source_ref_type=CLASS_STATUS_REPORT_SYNC`. The pre-sync (audit-derived) and post-sync (class-derived) values are both preserved in the log.
  5. **No `cert_anniversary_date_override` column on audit_detail.** Audit module records only `audit_completion_date`; anniversary truth lives in Certs module + Class Status Report.
  
  **Cross-module dependency:** Class Status Report sync mechanism is owned by Certs module (verify in Certs SSOT). Audit SSOT cross-references this dependency.
  
  **Open follow-up for SSOT merge:** confirm Class Status Report sync cadence + reconciliation rule documented in Certs SSOT.
- **New SSOT ID:** D-AUDRS-240

#### Q32 — Change of ownership / flag
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Out of audit module scope; handled by Certs module (cert reissue event resets anniversary). Audit module reads new anniversary on next external audit registration. Document this in cross-module dependency section.
- **Decision:** Change of ownership / change of flag is **out of audit module scope**. Owned entirely by Certs module:
  - Certs module owns the "cert reissue" event (per Certs SSOT; verify exact mechanism).
  - Reissue creates a new cert row with new anniversary; old cert row marked REISSUED with pointer to new.
  - Future audits register against the new cert via D-AUDRS-233 cert picker (active certs only by default).
  
  **Audit module behaviour:**
  - Read-only consumption of cert state via D-AUDRS-233 type-ahead picker.
  - No reissue-handling logic, no anniversary reset, no flag-change UI.
  - Old REISSUED certs filtered out of suggestion list (DPA can include via "show inactive" toggle for historic audit registration).
  
  **Documented in §11 Cross-Module Dependencies** of audit SSOT (at next SSOT merge): "Change of ownership / change of flag = Certs-module event. Audit module consumes via D-AUDRS-233; no direct audit-module involvement."
- **New SSOT ID:** D-AUDRS-241

#### Q33 — `window_close` definition
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Cite IMO ISM Code 13.4 — annual audit "within three months before or after each anniversary date". `window_close` = anniversary + 90 days. SMC = same. DOC = same. MLC follows MLC 2006 Standard A5.1.3 (5-year cert, intermediate between 2nd and 3rd anniversary). ISPS follows ISPS Part A 19.1.1 (5-year cert, intermediate between 2nd and 3rd anniversary).
- **Decision:** Window rules data-driven via new master table `master_audit_window_rule`:
  ```
  audit_subtype                    varchar(40) PK    -- e.g., SMC_ANNUAL, DOC_ANNUAL, SMC_INTERMEDIATE, MLC_INTERMEDIATE
  window_open_offset_days          int               -- negative = before anchor (e.g., -90)
  window_close_offset_days         int               -- positive = after anchor (e.g., +90)
  anchor                           varchar(40)       -- ANNIVERSARY | CERT_EXPIRY | INTERMEDIATE_2ND_TO_3RD_YEAR
  regulatory_ref                   nvarchar(200)     -- citation
  effective_from, effective_to, created_by, created_date
  ```
  **Seed at KLOSS Step 2** with explicit IMO/ILO clauses:
  - `SMC_ANNUAL` / `DOC_ANNUAL` → anchor=ANNIVERSARY, [-90, +90], ref="IMO ISM Code 13.4 — within 3 months before or after anniversary date"
  - `SMC_INTERMEDIATE` / `DOC_INTERMEDIATE` → anchor=INTERMEDIATE_2ND_TO_3RD_YEAR, [0, +365], ref="IMO ISM Code 13.6"
  - `MLC_INTERMEDIATE` → anchor=INTERMEDIATE_2ND_TO_3RD_YEAR, [0, +365], ref="MLC 2006 Standard A5.1.3"
  - `ISPS_INTERMEDIATE` → anchor=INTERMEDIATE_2ND_TO_3RD_YEAR, [0, +365], ref="ISPS Code Part A 19.1.1"
  - `SMC_RENEWAL` / `DOC_RENEWAL` → anchor=CERT_EXPIRY, [-90, 0], ref="IMO ISM Code 13.7"
  - `MLC_RENEWAL` → anchor=CERT_EXPIRY, [-90, 0], ref="MLC 2006 Standard A5.1.3"
  - `ISPS_RENEWAL` → anchor=CERT_EXPIRY, [-90, 0], ref="ISPS Code Part A 19.1.1"
  - `*_INITIAL` / `*_INTERIM` → no window enforcement (no alert ladder per D-209)
  
  Window math applied to each audit_plan row using the cert's anniversary (from Class Status Report per D-AUDRS-240) as the anchor. Code reads from master, never hard-codes offsets.
- **New SSOT ID:** D-AUDRS-242

#### Q34 — Harmonized certs with different anniversaries
- **Status:** ✅ CLOSED 2026-05-18 (**anniversary source = Class Status Report**)
- **Recommended Action:** Earliest anniversary drives alert ladder; UI shows all anchored cert anniversaries on the audit_plan detail. Triggers fire when ANY cert window opens.
- **Decision:** Harmonization logic for multi-cert audits:
  1. **Anniversary source = Class Status Report** for every linked cert (per D-AUDRS-240). Audit module reads cert anniversaries from Certs module's reconciled values; never sets them.
  2. **Earliest upcoming anniversary** (computed from Class-sourced anniversaries) drives the alert ladder. At audit_plan creation:
     ```
     next_audit_due_date = min(
       compute_window_open(linked_cert[i].anniversary, audit_subtype rule per D-AUDRS-242)
       for each cert in linked_cert_ids_csv
     )
     ```
  3. Alerts (T-90 / T-30 / T-0 / window_close / +30 / +90 per D-203) fire from `next_audit_due_date`.
  4. **audit_plan UI** displays ALL anchored cert anniversaries with their individual windows, sourced from Certs module read API. DPA sees each cert's window status alongside the harmonized planning window.
  5. **Harmonization validation:** a single harmonized audit covering N certs is valid when the windows overlap (i.e., max(window_open) ≤ min(window_close)). If no overlap, system flags `harmonization_blocked=1` and forbids the multi-cert linkage; requires separate audits per cert with windows resolved independently.
  6. When Class Status Report sync updates cert anniversaries (per D-AUDRS-240 reconciliation), audit_plan's `next_audit_due_date` is recomputed automatically; alerts re-evaluated.
- **New SSOT ID:** D-AUDRS-243

### 1.7 External auditor identity

#### Q35 — Auditor sign-off without system access
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** Wet signature on the external auditor's own report PDF (received from them) is the source of truth. VIMS does not capture auditor's signature separately. Close-out letter attachment = the signed artefact.
- **Decision:** External auditors are **not VIMS users at v1.1** (reconfirms D-AUDRS-015). Auditor sign-off mechanism:
  1. **Auditor's own report PDF** (and close-out letter, if any), signed wet by the auditor and received by KSM via existing channels, is the **sole source of truth** for auditor sign-off.
  2. Artefact attached to audit via `audit_attachment` with appropriate category (`AUDIT_REPORT_FINAL` per D-AUDRS-218 / `EXTERNAL_AUDITOR_CLOSEOUT_LETTER` per D-AUDRS-228).
  3. VIMS does NOT capture auditor signature image separately, does NOT generate auditor-signing PDFs, does NOT require auditor system access.
  4. **KSM-side signatures** (Master acknowledgment, Office Supt/DPA confirm of close-out) ARE captured via VIMS sign-and-scan workflow per D-AUDRS-061 (physical signatures at v1.0/v1.1).
  
  **Asymmetry documented:** external party signatures live in attached PDFs; KSM-internal signatures live in VIMS sign-and-scan flow.
  
  External auditor portal deferred to v2+ if commercial demand emerges.
- **New SSOT ID:** D-AUDRS-244

#### Q36 — Repeat auditor — master record or free-text
- **Status:** ✅ CLOSED 2026-05-18
- **Recommended Action:** New `master_external_auditor` (org_id FK, name, credential_number, last_seen_date). Auto-suggest on registration. Free-text fallback creates new row pending DPA confirm.
- **Decision:** New master table `master_external_auditor` (with simplified PII surface per Q37 closure):
  ```
  id                  uniqueidentifier PK
  org_id              uniqueidentifier FK master_external_audit_org.id  (per D-AUDRS-212)
  auditor_name        nvarchar(200) NOT NULL
  last_seen_date      date NULL  (auto-updated on each linked audit)
  is_active           BIT NOT NULL DEFAULT 1
  is_pending_review   BIT NOT NULL DEFAULT 0  (1 when created via free-text fallback awaiting DPA confirm)
  created_by, created_date, updated_by, updated_date, is_deleted
  ```
  Auto-suggest at audit registration based on (org_id + name prefix). Free-text fallback creates a new row with `is_pending_review=1`; DPA confirms or merges via curation UI. Free-text entry never bypasses the master.
- **New SSOT ID:** D-AUDRS-245

#### Q37 — PII concerns for external auditor records
- **Status:** ✅ CLOSED 2026-05-18 (**simplified — name + org only**)
- **Recommended Action:** Treat as commercial-contact data (business-purpose lawful basis), retain 10 years post last audit. Document in GDPR register. No special consent required for business contacts; redaction on subject request handled per GDPR procedure.
- **Decision:** **Minimal PII surface:** capture **only `auditor_name` + `org_id`** (Class society or company they belong to, via FK to `master_external_audit_org`). Specifically EXCLUDED from v1.1:
  - No `credential_number` column
  - No `qualifications_text` column
  - No `consent_basis` enum
  - No signature image stored separately (signatures live inside attached PDFs per D-AUDRS-244, treated as inseparable from the regulatory record)
  
  GDPR treatment:
  - **Lawful basis:** GDPR Art 6(1)(f) legitimate interests + Art 6(1)(c) legal obligation under ISM Code 13.
  - **Retention:** matches audit record retention (15+ years per D-AUDRS-pending Q63).
  - **Subject rights:** on GDPR access request, KSM discloses (auditor_name, org name, audits attended). On erasure request, refuse under Art 17(3)(b/e) exemptions (legal obligation + defence of legal claims). Document in privacy notice + Article 30 register.
  - Auditor signatures inside attached PDFs not separately erasable.
  
  Aligns Q36's master schema (auditor_name + org_id only — no credential/qual fields).
- **New SSOT ID:** D-AUDRS-246

---

## BATCH 2 — v1.2 RIGHTSHIP & v1.3 MANNING/SECURITY (Q38–Q50)

### 2.1 RightShip (v1.2)

#### Q38 — RISQ 3.0 IP / redistribution
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (out of this interrogation scope)
- **Recommended Action:** **HARD BLOCKER — must confirm with RightShip before any seed work.** Likely paths: (a) license agreement; (b) reference Q-numbers only without verbatim Q-text (text shown only when vessel is registered RightShip user). Default plan = (b) until license confirmed.
- **Decision:** **User scope decision 2026-05-18:** "RightShip is not part of this build, RightShip will be covered in next build. This build is only for Internal and External audit and its related workflow." Therefore this question and all subsequent RightShip questions (Q38–Q45) are formally deferred to the v1.2 build cycle's own interrogation round. **This interrogation cycle ends RightShip scope here.** Re-open when v1.2 build cycle starts. Captured as a meta-scope decision (no D-AUDRS ID consumed — scope deferral does not create a v1.1 SSOT lock; instead it's recorded in §8 Out of Scope of the audit SSOT at next merge).
- **New SSOT ID:** D-AUDRS-247 (scope-deferral lock — formalises §8 entry)

#### Q39 — Manual entry vs auto-import
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (per Q38 scope decision)
- **Recommended Action:** Manual entry only at v1.2. Auto-import deferred to v2 (would need RightShip API/portal scraping — both have legal/contractual constraints).
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.2 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q40 — Ship-type variants of RISQ
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (per Q38 scope decision)
- **Recommended Action:** RISQ 3.0 (dry bulk + general); SIRE = separate product (tankers). v1.2 = RISQ 3.0 only matching D-005. Tanker fleet = v1.3+ via SIRE 2.0.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.2 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q41 — RISQ scoring algorithm
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (per Q38 scope decision)
- **Recommended Action:** Score is inspector-supplied integer only; VIMS does not compute. Stored on `rs_detail.overall_risk_score`.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.2 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q42 — Charterer portal access
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (per Q38 scope decision)
- **Recommended Action:** No charterer access in v1.2. Charterer name captured for record only. Charterer portal = v3+ if commercial demand.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.2 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q43 — RISQ Recommendations vs Findings
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (per Q38 scope decision)
- **Recommended Action:** Both captured. RISQ "Findings" → `rs_observation.finding_category=MD` (Major Discrepancy). RISQ "Observations/Recommendations" → `rs_observation.finding_category=NO` (Negative Observation). Both create CAR per D-008.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.2 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q44 — Commercial impact notification
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (per Q38 scope decision)
- **Recommended Action:** Add notification type `RS_VETTING_OUTCOME_NEGATIVE` → fanout to Commercial team Slack channel + DPA email. New gate `AUDIT_P_016`.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.2 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q45 — RightShip Crew Vetting
- **Status:** ⏸️ DEFERRED to v1.2 build cycle (per Q38 scope decision)
- **Recommended Action:** Out of scope this module. Belongs in HRM module if KSM adopts it.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.2 build cycle.
- **New SSOT ID:** *(none — deferred)*

### 2.2 Manning Agent & Security Provider (v1.3)

#### Q46 — Manning agent user / login
- **Status:** ⏸️ DEFERRED to v1.3 build cycle (per Q38 scope decision — extended to Manning/Security)
- **Recommended Action:** KSM Crew Dept enters responses on behalf of agent (no agent login at v1.3, matching no-external-portal pattern). Agent's wet-signed response sheet scanned + attached.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.3 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q47 — Multiple manning agents per vessel
- **Status:** ⏸️ DEFERRED to v1.3 build cycle
- **Recommended Action:** Audit scoped per agent — one `audit_detail` per agent per audit cycle. Roll-up = office-side reporting view.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.3 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q48 — F 604 seed CSV provenance
- **Status:** ⏸️ DEFERRED to v1.3 build cycle (F 604 is the Manning Office Audit Checklist — Manning scope)
- **Recommended Action:** Extract from KSM SSQE Annex 1 PDF at KLOSS Step 2; commit as `seeds/master_audit_checklist_item_F604.csv`. User reviews before lock.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.3 build cycle. Note: F 605 (Vessel Internal Audit Checklist) and F 606 (Office Internal Audit Checklist) seeds remain in v1.0 scope per D-AUDRS-020 and will be generated at KLOSS Step 2 of the current build.
- **New SSOT ID:** *(none — deferred)*

#### Q49 — Security Provider regulation framework
- **Status:** ⏸️ DEFERRED to v1.3 build cycle
- **Recommended Action:** ISPS Part A (primary) + Flag State notices + KSM Ship Security Plan checklist. New checklist seed extracted from KSM SSP at v1.3 spec time.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.3 build cycle.
- **New SSOT ID:** *(none — deferred)*

#### Q50 — PCASP (armed guards) audits
- **Status:** ⏸️ DEFERRED to v1.3 build cycle
- **Recommended Action:** Sub-category under SECURITY_PROVIDER_AUDIT; new `audit_subtype=PCASP_AUDIT`. ISO 28007 referenced. Deferred to v1.3+.
- **Decision:** Out of v1.1 interrogation scope. Re-open in v1.3 build cycle.
- **New SSOT ID:** *(none — deferred)*

---

## BATCH 3 — V1.0 CROSS-CUTTING GAPS (Q51–Q79)

### 3.1 Real-world ops scenarios

#### Q51 — Audit spans multiple days
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Add `audit_end_date` column on audit_detail; `inspection_date` becomes audit_start_date. Both dates editable until status=CLOSED. SLA clocks count from `audit_end_date`.
- **Decision:** **OK as recommended.** New column `audit_detail.audit_end_date` (date, NULL until first save). Existing `inspection_date` retained as `audit_start_date` semantically (column name unchanged for legacy compatibility per D-AUDRS-066 namespace-separation policy). Validation: `audit_end_date >= audit_start_date` server-side. Both dates editable until status=CLOSED. **All NC closure SLAs (D-AUDRS-073: 30d Minor / 90d Major / 30d Obs) count from `audit_end_date`** — not start_date, not finding_raised_date. PDF F 601 footer renders "Audit Period: {start} – {end}". Single-day audits: end_date defaults equal to start_date.
- **New SSOT ID:** D-AUDRS-248

#### Q52 — Time zone handling
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Storage = UTC. Display = user's tenant TZ (KSM HQ = SGT). NC closure clock = wall-clock days computed at office TZ (not per-vessel local TZ — too volatile during voyage). Document explicitly to avoid drift.
- **Decision:** **OVERRIDE: Dual-TZ display with CMS integration.** 
  1. **Storage = UTC** (all datetime columns server-side; ISO 8601 with offset on API boundaries).
  2. **Office-side display TZ = ITC** (Office TZ value configurable in `app_settings.office_display_tz`; default ITC per user direction). Applies to all office-user screens, office PDFs, and SLA clock computation.
  3. **Vessel-side display TZ = vessel local time pulled from CMS WRH module.** Same integration pattern that PSC inspection already uses for vessel-local timestamps. New service contract: `CmsWrhClient.getVesselLocalTime(vessel_id, datetime_utc)` returns vessel local time + UTC offset valid at that instant.
  4. **NC closure SLA clock = computed at OFFICE TZ (ITC)** — wall-clock days. Vessel local TZ is display-only; never used for deadline math (vessel TZ shifts mid-voyage and would produce non-deterministic SLAs).
  5. **PDF rendering:** office-issued PDFs show ITC timestamps with `(ITC)` suffix; vessel-issued PDF parts (Master signature blocks B + D) show vessel local time with `(LT UTC±HH:MM)` suffix derived from WRH at sign time, frozen onto the PDF.
  6. **Audit trail (`psc_audit_log`)** stores UTC plus the captured display TZ for forensic clarity.
- **New SSOT ID:** D-AUDRS-249

#### Q53 — Crew change mid-NC closure
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** PDF shows whichever Master is the signer of EACH part (Part B Master A, Part D Master B). Audit trail captures full sign history with role + timestamp.
- **Decision:** **OVERRIDE: Rank-bound, not person-bound; CMS live crew list is source of truth.**
  1. NC signature fields (Part B Master immediate-action, Part D Master effectiveness-review) bind to **RANK = Master**, not to a specific user_id. Whichever person holds the Master rank at sign time is the valid signer.
  2. **Live crew list pulled from CMS** — same integration the PSC inspection module already uses (no new code path). Lookup: `CmsCrewClient.getActiveCrewByRank(vessel_id, rank, datetime_utc)` returns the user_id currently mustered to that rank at that instant.
  3. PDF F 601 Part B + Part D footer renders: rank label, signer name (frozen from CMS at sign time), sign date in vessel local time (per D-AUDRS-249).
  4. If signer of Part B ≠ signer of Part D (crew change between signings): both names render on the PDF — Part B shows Master A, Part D shows Master B. **No special "handover" workflow needed** — signatures are independent per part. UI surfaces a small badge ("Signed by previous Master / signed by current Master") for context only.
  5. `psc_audit_log` captures every signature event: user_id + rank_at_signing + datetime_utc + vessel_local_time + part_label. Full sign history is queryable for audit defence.
  6. Same rule extends to **Chief Officer / Chief Engineer / Safety Officer** ranks where they sign on Audit forms (e.g., F 605 checklist rows). Rank-bound everywhere.
- **New SSOT ID:** D-AUDRS-250

#### Q54 — Lead Auditor leaves during NC closure
- **Status:** ✅ CLOSED 2026-05-19 (OPERATIONAL POLICY — no software change)
- **Recommended Action:** DPA reassigns Lead Auditor on open findings via new action "Reassign Lead Auditor" (gate AUDIT_P_017). Reassignment captured in audit trail; reason ≥50 chars. Original Lead Auditor's prior signatures remain valid (he signed Parts A-D); new Lead Auditor takes over Parts E-G.
- **Decision:** **REJECTED — operational policy, not a software feature.** KSM policy: Lead Auditor must complete all open audits and close all assigned NCs (including effectiveness review per D-AUDRS-082) **before departure from the company**. HR offboarding checklist enforces this gate operationally. No "Reassign Lead Auditor" action, no new gate, no new column. If a Lead Auditor genuinely cannot complete (death, medical incapacity, contract dispute), DPA handles as a one-off ticket — out of system. **AUDIT_P_015 NOT created.**
  - Rationale: Reassignment feature would create an exception path that could be misused to bypass auditor accountability. KSM SSQE Manual §10.6 puts personal responsibility on the Lead Auditor for the audits they conducted. Making this a software-easy action erodes that.
  - Implication: SSOT must add an HR-offboarding callout in §16 Operational Procedures (new sub-section) referencing "Lead Auditor open-findings clearance".
- **New SSOT ID:** D-AUDRS-251

#### Q55 — DPA on leave during close-out
- **Status:** ✅ CLOSED 2026-05-19 (NO ACTING DPA MECHANISM)
- **Recommended Action:** Acting DPA via existing `master_hod_assignment` (extend dept enum to include 'DPA'). All DPA actions during acting period stamped with `acted_as_DPA_for=<original_DPA_id>` for audit clarity.
- **Decision:** **REJECTED — DPA-on-leave is not a real KSM scenario.** Per user direction: "DPA is never on leave; can log in and complete." DPA role at KSM is structured such that the appointed DPA retains login access and personally completes all DPA actions regardless of physical absence (vacation, travel, illness short of incapacity). No acting-DPA mechanism, no `dept='DPA'` extension to `master_hod_assignment` table.
  - **D-AUDRS-106 NOT re-opened.** `master_hod_assignment` table scope remains limited to operational HoD coverage (Marine, Technical, HSSEQ, Crewing) — NOT DPA.
  - Edge case (DPA medically incapacitated for extended period): handled by Flag State notification of DPA succession per ISM Code 4.2 — appoint new permanent DPA, not an acting one. Out of v1.0 scope.
  - **Simplification gain:** removes ~2 columns + 1 audit-trail event_type + 1 gate that the recommendation would have introduced.
- **New SSOT ID:** D-AUDRS-252

#### Q56 — Acting HoD authorisation
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Only DPA + HR Director can set acting flag. Audit trail event on each assignment. Auto-expiry on `effective_to`.
- **Decision:** **OK with role override: DPA + Fleet Manager (FM)** can flip `is_acting=1` and set `effective_from/to` on `master_hod_assignment` rows. New gate **AUDIT_P_016** scoped to these two roles only (HR Director NOT in scope at v1.0 — FM owns operational HoD coverage at KSM). Constraints:
  1. Self-acting forbidden — DPA can't acting-promote DPA (consistent with D-AUDRS-252 — DPA role is structurally not delegable); FM can't acting-promote FM.
  2. Auto-expiry server job (daily 00:01 ITC per D-AUDRS-249) flips `is_acting=0` on rows where `effective_to < today`. Acting period max = 90 days (re-issue required beyond).
  3. Every flip (set / extend / revoke) writes a `psc_audit_log` event with both DPA's and FM's user_ids (whichever performed action) plus the affected user_id + dept.
  4. UI: FM-only screen at `/admin/hod-coverage` lists active acting assignments + history; DPA gets same screen read-write.
  5. Premise confirmed by user proceeding without rejection — acting-HoD IS a real scenario at KSM (separates from DPA case in D-AUDRS-252).
- **New SSOT ID:** D-AUDRS-253

#### Q57 — Internet failure during audit (online-only)
- **Status:** ✅ CLOSED 2026-05-19 (NO SOFTWARE CHANGE — operating model already handles it)
- **Recommended Action:** Re-validate D-AUDRS-062 (ONLINE-ONLY at v1.0). Recommended override: keep online-only but add **draft-on-paper + key-in-later** workflow with backdating allowed up to 14 days (audit-trailed). Or: re-open D-062 and implement offline cache for audit forms specifically. Pick one explicitly.
- **Decision:** **REJECTED — premise was wrong. The audit operating model is offline-by-design for the vessel-visit portion; data entry happens ashore where connectivity is fine.** D-AUDRS-062 online-only stays as-is. New decision codifies the operating model:
  1. **Pre-boarding (ashore, online):** Auditor prepares audit plan, checklist (F 605), pre-fills audit_detail header (vessel, scope, standards, dates). System produces a printable "Audit Workbook" PDF the auditor takes onboard.
  2. **Onboard (vessel, offline-by-design):** Auditor conducts checklist walk on paper / personal notes. No VIMS access required. No data entry expectation during the visit.
  3. **Post-disembark (ashore, online):** Auditor enters all checklist results, findings, evidence, and NCs into VIMS within standard SLA (existing D-AUDRS-066 timestamps apply; entries are stamped at actual server-time, not backdated).
  4. **Vessel acknowledgement:** Master receives in-system notification when auditor finalizes the report (status moves to `REPORT_FINALIZED`). New action **"Vessel Acknowledge Audit Report"** by Master before NC closure clocks start. New state on `audit_detail.status` chain: `REPORT_FINALIZED → VESSEL_ACKNOWLEDGED → CLOSURE_IN_PROGRESS`. Acknowledgement = Master confirms audit happened + findings accurately reflect observations. Disputes raised verbally at auditor's closing meeting per D-AUDRS-229 — no in-system dispute mechanism.
  5. **NC SLA clocks (D-AUDRS-073) start at `VESSEL_ACKNOWLEDGED` timestamp**, not at finding_raised_at. Master gets full Part B window from his acknowledgement.
  6. New gate **AUDIT_P_017** = vessel-side acknowledgement (Master rank-bound per D-AUDRS-250).
  7. Dropped from recommendation: 14-day backdate window, `offline_capture_reason` column, scanned-paper attachment requirement, sat-link assumption — none needed under this model.
- **New SSOT ID:** D-AUDRS-254

#### Q58 — Audit in port without internet
- **Status:** ✅ CLOSED 2026-05-19 (covered by D-AUDRS-254)
- **Recommended Action:** Same as Q57. KSM should confirm coverage assumption holds at typical bunker / drydock locations.
- **Decision:** **Subsumed by D-AUDRS-254.** Offline-by-design vessel-visit model means port connectivity is not on the critical path — auditor enters data ashore post-disembark from any KSM office or remote-work location with normal connectivity. No port-specific connectivity dependency to validate. Drydock auditors follow the same workflow (prep ashore → conduct → report ashore from a local hotel / yard office).
- **New SSOT ID:** *(none — folded into D-AUDRS-254)*

#### Q59 — NC raised at port, Master signs later
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Backdating of `master_immediate_sign_at` allowed up to 30 days from finding issuance with reason ≥50 chars. Audit trail records both actual entry time and backdated time.
- **Decision:** **OK as recommended.** Backdate of `master_immediate_sign_at` up to **30 days** from `finding_raised_at` allowed with mandatory `backdate_reason` ≥50 chars on `audit_finding_sign_event` (new audit-trail child table) plus the server-clock entry timestamp `actual_entered_at` (UTC). PDF F 601 Part B renders the claimed sign date in vessel local TZ per D-AUDRS-249/250; audit log retains both clocks for forensic clarity. No new gate — uses existing PIC gate **AUDIT_P_004**. Beyond 30 days: hard block on save; Master must explain via separate Office Memo escalation outside system (rare exception).
  - Coherence note: Under D-AUDRS-254 (Q57), NC closure SLA clocks anchor on `VESSEL_ACKNOWLEDGED` timestamp anyway, so the 30-day Master-signature backdate is bounded by the vessel-acknowledgement gate (in practice ≤30 days).
- **New SSOT ID:** D-AUDRS-255

### 3.2 Conflict of interest

#### Q60 — Office audit on DPA's own dept
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Hard rule: when `auditee_office_dept=SEQ`, Lead Auditor MUST NOT be DPA. Server-side validation. Audit conducted by an independent external auditor (out-of-cycle external) OR by another department's HoD with appropriate qualification.
- **Decision:** **OK with primary-path lock to cross-dept HoD.** Server-side validation: when `auditee_office_dept='SEQ'`, Lead Auditor `user_id` MUST NOT equal DPA's `user_id` (HTTP 422 on save). **Primary resolution path:** assign a Lead Auditor who is an HoD of another department (Marine / Technical / HSSEQ ≠ SEQ / Crewing) holding an active row in `master_audit_qualified_auditor` with `qualified_for_seq=1`. This codifies KSM's stated practice ("HoD of other department will audit DPA's department"). External auditor fallback (out-of-cycle EXTERNAL classification per D-AUDRS-200) remains available but is NOT the default — only used when no qualified cross-dept HoD is on-roster. UI hint at audit_plan creation: when auditee_office_dept=SEQ is selected, picker for Lead Auditor pre-filters to cross-dept HoDs with `qualified_for_seq=1`. New flag on `master_audit_qualified_auditor`: `qualified_for_seq` BIT NOT NULL DEFAULT 0 (DPA designates qualified cross-dept HoDs at master-data setup).
- **New SSOT ID:** D-AUDRS-256

#### Q61 — Lead Auditor auditing former employer
- **Status:** ✅ CLOSED 2026-05-19 (NOT APPLICABLE — no software change)
- **Recommended Action:** Add `lead_auditor_conflict_declaration_text` (optional) on audit_detail; DPA reviews on assignment. No automated enforcement at v1.0 — honor system.
- **Decision:** **NOT APPLICABLE at KSM.** Premise rejected by user. Internal Lead Auditors are all KSM staff (no prior-employer overlap with KSM-managed vessels). External auditors arrive via RO/Flag — KSM does not select them. No `lead_auditor_independence_declaration` column added; no UI; no PDF cover-sheet field; no DPA review gate. If a CoI ever surfaces operationally, DPA handles as a one-off ticket per Q60's existing reassignment picker (D-AUDRS-256). **Saves: 1 column, 0 gates, ~6 PDF rendering lines.**
- **New SSOT ID:** *(none — not applicable)*

#### Q62 — Auditor's relative on vessel
- **Status:** ✅ CLOSED 2026-05-19 (NOT APPLICABLE — no software change)
- **Recommended Action:** Same mechanism as Q61; combine into single "Independence Declaration" field on audit_detail.
- **Decision:** **NOT APPLICABLE at KSM.** Premise rejected by user. Kinship-based CoI is not a real scenario in KSM's auditor roster vs crew rosters. No column, no UI, no PDF. Folded into Q61's rejection — no shared "Independence Declaration" field exists. Operational discretion via DPA reassignment (D-AUDRS-256 mechanism) covers exotic edge cases without code.
- **New SSOT ID:** *(none — not applicable)*

### 3.3 Data lifecycle

#### Q63 — Audit record retention
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Audit_detail + linked findings = retained indefinitely (or minimum 15 years to cover 3 ISM cycles). Soft-delete via is_deleted; never hard-deleted at v1.0. Hard-delete policy v2+.
- **Decision:** **OK as recommended. 15-year retention** for the full audit graph: `audit_detail` + `audit_finding` + `audit_finding_clause` + `audit_attachment` (incl. PDF/scan blobs) + `notification_delivery_log` + `psc_audit_log` rows linked to audits + `audit_finding_sign_event` (D-AUDRS-255) rows. Retention clock starts at `audit_detail.created_at`. **Soft-delete only at v1.0** via existing `is_deleted` BIT + `deleted_at` + `deleted_by` on every audit-domain table (consistent with D-AUDRS-066 legacy-pattern reuse). **No hard-delete at v1.0** — DPA-only `is_deleted` flip with reason ≥50 chars + audit log entry. Hard-delete + archival storage tier (cold-storage move) policy is v2+ work, NOT a v1.0 obligation. Aligns with KSM SMS doc retention rule (D-AUDRS-114 specified 7y for general SMS docs; audit graph gets 15y because Flag/RO defence horizon is wider — 3 ISM cycles).
- **New SSOT ID:** D-AUDRS-257

#### Q64 — Vessel sold / changes management
- **Status:** ✅ CLOSED 2026-05-19 (NO HANDOVER EXPORT — internal-only)
- **Recommended Action:** Export bundle ("vessel handover pack") generated on request: all audits + findings + PDFs + attachments as ZIP. KSM retains a copy for its own ISM history. Document data ownership in commercial contract.
- **Decision:** **REJECTED outbound handover pack — audit records are internal to KSM and NOT shared with the new manager on divestment.** Per user direction: "not shared as that's internal." 
  - **No "Vessel Handover Pack" export feature** at v1.0. No AUDIT_P_018 gate. No ZIP-builder job. No 72h-TTL download URL infra.
  - **Inbound (acquisition) also out of scope.** No bulk historical-audit ingest at v1.0. If KSM acquires a vessel with prior ISM history, the prior history stays with the prior manager; KSM starts the audit clock on takeover (additional/initial audit per D-AUDRS-121 + D-AUDRS-207).
  - **Retention behaviour on divestment:** vessel_id row + all linked audit graph retained internally per D-AUDRS-257 (15-year retention). `vessel_status='DIVESTED'` flag read from CMS (no VIMS-side mirror). Audit records remain queryable for KSM's own legal defence / Flag-State enquiry history.
  - **Saves:** 1 background job, 1 gate, 1 download-URL service, ~4 UI screens (DPA export config + status tracker), commercial-contract clause negotiation effort.
- **New SSOT ID:** *(none — feature dropped)*

#### Q65 — GDPR right to erasure on crew names
- **Status:** ✅ CLOSED 2026-05-19 (NOT APPLICABLE — no software/policy change)
- **Recommended Action:** Audit records are ISM-mandated legal documents — GDPR Art 17(3)(b) "compliance with legal obligation" + Art 17(3)(e) "establishment, exercise or defence of legal claims" exemptions apply. Refuse erasure on those grounds; document policy in privacy notice.
- **Decision:** **NOT APPLICABLE at v1.0.** Premise rejected by user. GDPR erasure on crew names is not a live operational concern at KSM (likely due to jurisdiction — KSM operates under non-EU privacy regimes; PDPA/DPDPA-class frameworks don't have equivalent erasure rights for ISM-mandated records). No canned response template, no privacy-notice text bundled with v1.0, no `gdpr_erasure_response_template` documentation. If an erasure request ever arrives, KSM legal handles ad-hoc — out of system, out of SSOT.
  - Note: D-AUDRS-246 (Q37 external auditor PII) handles GDPR for external auditors specifically because RO/Flag inspectors may be EU-based. That decision stands — narrowly scoped to that role. Crew + Master + internal auditors not covered at v1.0.
  - **Saves:** privacy-notice drafting, legal-template review, §16 OPM addendum.
- **New SSOT ID:** *(none — not applicable)*

### 3.4 Signatures and audit-trail integrity

#### Q66 — PDF signature replay prevention
- **Status:** ✅ CLOSED 2026-05-19 (after re-fire with concrete scenarios A/B/C)
- **Recommended Action:** Each generated PDF has unique hash + sequence_no embedded in QR/barcode. Scanned-back PDF validated against stored hash; mismatch flagged. Reuses pattern from PSC module if present.
- **Decision:** **OPTION A SELECTED — build QR/hash replay-prevention.** Closes scenarios A (same-scan reuse against different finding), B (outdated-scan reuse after office RCA edit per D-AUDRS-081), C (cross-vessel scan reuse on crew transfer). Implementation:
  1. **New table `audit_pdf_generation`** — `id` (uuid PK) · `finding_id` FK (nullable for whole-audit PDFs) · `audit_detail_id` FK · `pdf_kind` enum (F_601 / F_605 / EXTERNAL_REPORT / EXTERNAL_CLOSEOUT_LETTER / OTHER) · `pdf_version` int (increments on each regeneration triggered by office-edit per D-AUDRS-081 or audit re-finalize) · `content_hash` (SHA-256 over canonical text payload at generation time) · `qr_payload` (compact JSON: `{pdf_id, pdf_version, content_hash, finding_id, vessel_id}`) · `generated_at` UTC · `generated_by` FK to users · `is_superseded` BIT (set when a newer pdf_version replaces it).
  2. **QR embedded on every page footer** of VIMS-generated audit PDFs (F 601, F 605, NC PDFs). Excludes external-auditor-supplied scans (D-AUDRS-201/204) — those are inherently non-VIMS-generated.
  3. **New columns on `audit_attachment`:** `linked_pdf_generation_id` (uuid, nullable — null for non-VIMS-PDF attachments) · `pdf_hash_validation_status` enum {`MATCHED`, `MISMATCH_FINDING`, `MISMATCH_VESSEL`, `MISMATCH_VERSION`, `UNREADABLE`, `NOT_APPLICABLE`} · `validated_at` UTC · `validator_message` nvarchar max.
  4. **Upload-time validation pipeline:** on `audit_attachment` POST, server runs QR-decode via image-processing lib on every page → if QR present, parse → look up `audit_pdf_generation` by `pdf_id` → compare against target `finding_id` / `vessel_id` / `pdf_version`. Result writes the `pdf_hash_validation_status`. Upload NEVER blocked outright (scan-quality glitches happen); MISMATCH/UNREADABLE statuses surface in DPA queue.
  5. **DPA review widget** at `/dpa/scan-validation-queue` shows MISMATCH/UNREADABLE uploads. DPA decisions: `ACCEPT_WITH_REASON` (reason ≥50 chars; audit-trailed) or `REJECT_AND_REQUEST_RESCAN` (notifies uploader). New gate **AUDIT_P_018** (DPA-only).
  6. **Audit trail (`psc_audit_log`):** every PDF generation, every upload validation, every DPA decision logged with full context.
  7. **External-audit attachments** (D-AUDRS-201/204): `linked_pdf_generation_id = NULL`, `pdf_hash_validation_status='NOT_APPLICABLE'` — no validation, no review. External auditor's report has its own integrity (auditor's stamp per D-AUDRS-260).
  8. **Re-generation triggers:** office-edit-assist save (D-AUDRS-081), audit re-finalize, manual DPA-initiated regen. Previous pdf_version row is marked `is_superseded=1` but retained for 15y per D-AUDRS-257.
  9. **PDF kinds OUT OF SCOPE for QR/hash at v1.0:** S 625, S 626 (KPI exports — read-only reports, no signature workflow); audit cover sheets without sign blocks.
  10. **Estimated effort:** ~2 dev-days backend + ~1 day DPA queue widget + QR library evaluation. Acceptable trade for closing three named threat vectors.
- **New SSOT ID:** D-AUDRS-261

#### Q67 — Signature image OCR/verification
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** No OCR / signature verification at v1.0. Documented limitation; risk = forged signatures. Mitigation = audit-trail of who uploaded the scan + their VIMS account login.
- **Decision:** **OK as recommended.** No biometric/handwriting verification, no signature-image stored as a separate column, no third-party signature-verification SaaS. Forged-signature risk is accepted at v1.0; mitigated by (a) audit-trail of `audit_attachment.uploaded_by_user_id` + `uploaded_at` UTC, (b) wet-ink + scanned-back attestation, (c) F 601 PDF retained under SMS document control per D-AUDRS-114 retention rules. §16 OPM documents this as a known limitation. Revisit v2+ only if forgery incident actually occurs operationally.
- **New SSOT ID:** D-AUDRS-258

#### Q68 — eIDAS / 21 CFR / MSC.1/Circ.1593 compliance
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** **HARD BLOCKER — must confirm with Flag State(s) before v1.0 production cutover.** KSM SSQE Manager confirms that physical-signature-only meets Flag State acceptance. Otherwise re-open D-061.
- **Decision:** **CLOSED — Flag State acceptance confirmed by user.** Per user direction: "Flag accepts it so no need." All Flags in KSM's portfolio (per D-AUDRS-213 per-flag DOC model) accept the VIMS workflow: system-generated PDF → printed → wet-ink signed → scanned back as SMS objective-evidence record. No eIDAS-class qualified e-signature required. No 21 CFR Part 11 conformity required. No MSC.1/Circ.1593 declaration required. **D-AUDRS-061 wet-ink-physical-signature-only model stands without modification.** No §16 OPM addendum needed; the "hard blocker" annotation on the spec is REMOVED.
  - SSOT merge action: when §9 batch-merge runs, strip any "HARD BLOCKER — Flag State confirmation required" callout on D-AUDRS-061 / D-AUDRS-256-class entries.
  - If KSM acquires a vessel under a new Flag in future, that Flag's acceptance is presumed unless KSM SSQE flags otherwise; no per-Flag attestation table needed.
- **New SSOT ID:** D-AUDRS-259

#### Q69 — Auditor's official stamp
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Captured as part of the close-out letter / report PDF scan (not a separate field). Documented in user guide.
- **Decision:** **OK as recommended.** External audits: auditor's official stamp/chop is captured as part of the scanned `external_audit_report_pdf` attachment (D-AUDRS-201) and/or `external_audit_closeout_letter_pdf` (D-AUDRS-204) — i.e., the stamped page IS the scan. No separate `auditor_stamp_image` column on `audit_detail`; no stamp-image upload widget; no PDF render overlay. Internal audits: no stamp involved; Lead Auditor signature on F 601/F 605 suffices per D-AUDRS-061 wet-ink rule. §16 OPM documents instruction: "External-audit registrar must ensure the auditor's stamped page is included in the scanned report PDF." **Saves:** 1 column, 1 image-upload widget, ~3 PDF rendering lines.
- **New SSOT ID:** D-AUDRS-260

### 3.5 Notifications

#### Q70 — Email/Slack failure after 3× retry
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Surface on Office DPA dashboard widget "Failed Notifications" with retry button. In-system notification still present as source of truth; failed-delivery flag visible on notification detail.
- **Decision:** **OK as recommended — DPA owns this (not FM/IT admin).** New DPA dashboard widget at `/dpa/notifications/failed` listing rows from `notification_delivery_log` (D-AUDRS-114) with `status='FAILED_PERMANENT'`. Columns: notification_id, notification_type, recipient_address, channel (EMAIL/SLACK), last_error, attempt_count, original send_at. Two DPA actions on each row:
  1. **"Manual Retry"** — queues a fresh delivery attempt; resets `attempt_count=0` and `status='QUEUED'`. Logged as `event_type='NOTIFICATION_MANUAL_RETRY'` in `psc_audit_log` with DPA user_id.
  2. **"Mark as Notified Offline"** — records DPA-confirmed out-of-band delivery (phone/in-person); reason ≥30 chars; sets `status='RESOLVED_OFFLINE'`. Logged with DPA user_id.
  Widget polls every 60s. In-system notification remains source-of-truth (D-AUDRS-111 unchanged — never "fails" since same-DB-transaction). No automatic escalation chain to FM/IT — DPA owns notification health as part of compliance oversight role.
- **New SSOT ID:** D-AUDRS-262

#### Q71 — Notification opt-out per user
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** No opt-out at v1.0 for audit-related notifications (regulatory). User preferences screen lists them as "mandatory". Opt-out for non-audit types (informational) v1.1+.
- **Decision:** **No opt-out at v1.0.** Confirmed by user. All 7 audit notification types from D-AUDRS-115 (AUDIT_SCHEDULED · AUDIT_NC_RAISED · AUDIT_CANCELLED · AUDIT_OVERDUE · AUDIT_CRITICAL_OVERDUE · AUDIT_EXTENSION_APPROVED · NC_EFFECTIVENESS_REVIEW_DUE) are **mandatory** for every targeted recipient. User Preferences screen displays them as read-only ("Audit notifications are mandatory and cannot be disabled — regulatory requirement"). No `notification_preference` table at v1.0; no opt-out gate. Future v1.1+ may introduce per-user opt-out only for non-regulatory notification types if any are added (none planned at v1.0).
- **New SSOT ID:** D-AUDRS-263

#### Q72 — Single vessel email mailbox responsibility
- **Status:** ✅ CLOSED 2026-05-19 (SUPERSEDES D-AUDRS-112 email-source portion)
- **Recommended Action:** Vessel Master is accountable; standing instruction is mailbox monitored daily. Document in user guide. Future v1.1: per-officer distribution list.
- **Decision:** **OVERRIDE — vessel email pulled from CMS, NOT from a new VIMS-side VesselData column. Supersedes D-AUDRS-112 (email source portion).** Per user direction: "in PSC no email is sent, but Audit requires a trail so email is needed. CMS uses email for vessel and you can find from the database."
  1. **PSC inspection module does NOT send email** today — Audit module is the first VIMS feature requiring vessel-email delivery as part of regulatory trail. Don't extrapolate PSC's behaviour.
  2. **Email source = CMS database.** New service contract: `CmsVesselClient.getOfficialEmail(vessel_id)` → returns the vessel's official mailbox. Same integration pattern family as D-AUDRS-249 (CMS-WRH time) and D-AUDRS-250 (CMS live crew). **No new column on `VesselData` in VIMS — D-AUDRS-112's `VesselData.official_email` provisioning is RESCINDED.** Email is read-through from CMS at notification dispatch time; cached for 15 min only.
  3. **Master remains accountable** for monitoring vessel mailbox daily — standing instruction documented in §16 OPM + Fleet Standing Orders.
  4. **Failure mode:** if CMS returns null/empty email for a vessel, notification dispatch logs `status='FAILED_PERMANENT'` with `last_error='CMS_NO_EMAIL_ON_FILE'` and surfaces in DPA queue per D-AUDRS-262. DPA escalates to CMS data-fix workflow (out of VIMS).
  5. **Per-officer distribution lists** = v1.1+ candidate (keyed off CMS rank assignments). Not built at v1.0.
  6. **Cross-module dependency:** Add CMS API endpoint requirement to §11 cross-module deps in SSOT — `GET /cms/vessels/{vessel_id}/official_email`. Confirm with CMS team that endpoint exists or needs to be added.
- **New SSOT ID:** D-AUDRS-264 (supersedes email-source portion of D-AUDRS-112; D-AUDRS-112's "single official mailbox" principle retained)

#### Q73 — Slack channel mapping
- **Status:** ✅ CLOSED 2026-05-19 (SIMPLIFIED — per-vessel only)
- **Recommended Action:** Per-vessel Slack channel + per-event-type override at master_slack_channel level. Default fleet-wide channel for non-vessel-specific events (e.g., S 626 monthly export reminders if ever added).
- **Decision:** **SIMPLIFIED — per-vessel Slack channel only.** Per user direction: "Per Vessel Slack channel."
  1. **`master_slack_channel` row per vessel:** `scope_type='VESSEL'`, `scope_value=vessel_id`, `notification_types_csv` = all 7 audit notification types (D-AUDRS-115). One channel per vessel; created at vessel onboarding alongside the existing CMS-side Slack channel KSM already maintains per vessel.
  2. **No fleet-wide DPA Slack channel** at v1.0. DPA monitors via in-system dashboard + email; no Slack aggregator channel.
  3. **No per-notification-type override** at v1.0. Every audit notification type for a given vessel goes to that vessel's channel uniformly.
  4. **Office-internal audits (D-AUDRS-102) skip Slack entirely at v1.0.** No vessel scope means no per-vessel channel; office audits notify via in-system + email only (HoD + key staff + DPA + auditor team all on email per D-AUDRS-264 office-side users.email). v1.1 may add per-department office Slack channel if KSM requests.
  5. **Webhook URL** stored encrypted in `master_slack_channel.webhook_url` per D-AUDRS-113. Posted in Block Kit format.
  6. **Cross-module premise confirmed:** KSM already maintains per-vessel Slack channels (for other features per memory of [[project_vims_safety_module]]). Audit module reuses the existing per-vessel channel rather than introducing a parallel audit-only channel.
  7. **Saves:** fleet-wide-aggregator config, per-notification-type override table, office-dept channel scaffolding at v1.0.
- **New SSOT ID:** D-AUDRS-265

#### Q74 — Notification storm
- **Status:** ✅ CLOSED 2026-05-19 (NOT APPLICABLE — premise rejected)
- **Recommended Action:** Rate-limit by recipient: max 10 audit-notifications per recipient per hour. Excess batched into digest. In-system events not rate-limited.
- **Decision:** **NOT APPLICABLE — notification storm is not a real KSM operational concern at v1.0.** Per user direction: "DOC Audit is for office, not vessel, but it's rare to have multiple audits at one time due to window period."
  1. **Premise clarification:** my recommendation framed "multi-vessel DOC audit" — this was wrong. Per D-AUDRS-213, DOC audit is office-side (one DOC per flag); combined-event SMC audits across vessels are bounded by audit-window cadence rules (D-AUDRS-049) preventing simultaneous fleet-wide events.
  2. **Real KSM cadence:** audit windows per vessel are spaced; AUDIT_OVERDUE midnight batch jobs across vessels rarely exceed a handful of notifications per recipient per day. Recipients are bounded (DPA + HoD + Master) — no fan-out across hundreds.
  3. **No rate limiting at v1.0.** No `notification_rate_limit_window` table. No hourly digest formatter. No bypass enum for critical events. Accept occasional brief notification bursts (e.g., year-end DOC audit cycle) as harmless — recipients can ignore individual emails; in-system queue handles volume natively.
  4. Revisit only if operational incident report flags notification volume as a complaint (none on record).
  5. **Saves:** 1 new table, 1 background job, 1 digest template, ~2 dev-days.
- **New SSOT ID:** *(none — not applicable)*

### 3.6 KLOSS Step 2 execution

#### Q75 — DocSuite acceptance criteria
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Mechanical re-grep coverage like Certs module 199/199 pattern. N = sum of (locked decisions × required mention count). Pre-define N before generation starts. Target ≥99% mechanical coverage.
- **Decision:** **OK as recommended.** Mechanical re-grep coverage matching Certs module 199/199 pattern. Each locked D-AUDRS-### tagged with `required_in:[doc_list]` listing 1–5 canonical docs where mention is mandatory (defaults by decision category — schema → DATA_MODEL+PRD; RBAC → RBAC+APP_FLOW+PRD; etc.). Required-mention matrix pre-defined in COVERAGE.md before generation kicks off. **Target ≥99% mechanical coverage** with ≤1% misses tolerated only with documented reason. Audit script = same Python re-grep tool that produced Certs 199/199.
- **New SSOT ID:** D-AUDRS-266

#### Q76 — Seed CSV provenance
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Each seed CSV gets a `_provenance.md` sibling file: source document, page range, extraction date, extractor (LLM or human), reviewer, review date.
- **Decision:** **OK as recommended.** Every seed CSV in `VIMS-Audit-Module/seeds/` (incl. but not limited to: `master_audit_area.csv` 14 rows · `master_audit_qualified_auditor.csv` · `master_rca_template.csv` ~25 rows per D-AUDRS-117 · `master_external_audit_org.csv` per D-AUDRS-212 · `master_audit_window_rule.csv` per D-AUDRS-242 · `master_external_auditor.csv` per D-AUDRS-245 · `master_audit_clause_ref.csv` SOLAS/STCW/MARPOL/COLREG/KSM-SMS) gets a sibling `<file_name>_provenance.md` capturing: **source document** (KSM SSQE Manual §/IMO publication/Class society circular/customer-supplied list) · **page range or URL** · **extraction date** · **extractor** (LLM model ID or human name) · **reviewer** (always human — KSM SSQE Manager or DPA) · **review date** · **change log** for any subsequent edits. Provides auditable chain from regulatory source to running database.
- **New SSOT ID:** D-AUDRS-267

#### Q77 — FIELD_MAP for unbuilt UI
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** UI column = mockup screen IDs from existing HTML artefacts (VIMS-Audit-Module-Mockups.html etc.). Each cell references screen + element. Flag screens not yet mocked as "MOCKUP-PENDING".
- **Decision:** **OK as recommended.** Per [[feedback_field_map_requirement]], `FIELD_MAP.md` in DocSuite traces DB column → API field → UI element. UI cells reference existing HTML mockups by screen ID format `<mockup_id>:<element_id>` (e.g., `MOCKUP-VESSEL-04:nc_wizard_step3.rca_input` for the NC-wizard step in `VIMS-NC-Observation-UX.html`; `MOCKUP-EXT-02:registration_form.lead_auditor_name` for external-audit registration in `VIMS-External-Audit-UX.html`). For features locked in SSOT but not yet wireframed (e.g., DPA scan-validation queue from D-AUDRS-261, "Failed Notifications" widget from D-AUDRS-262), cell marked `MOCKUP-PENDING-KLOSS-STEP-2` — DocSuite Step 2 produces the mockup alongside the doc. **Never leave a UI cell blank** — every API field terminates at either a real screen reference or a PENDING placeholder.
- **New SSOT ID:** D-AUDRS-268

#### Q78 — COVERAGE.md N value
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** N = 133 (locked decisions) × 7 (canonical doc types: PRD, BACKEND_STRUCTURE, APP_FLOW, DATA_MODEL, RBAC, FIELD_MAP, PDF_TEMPLATES) = 931 cells. Each cell = "decision referenced in this doc Y/N". Cells where N/A (e.g., RBAC for a non-RBAC decision) marked N/A. Confirm formula before generation.
- **Decision:** **OK with updated formula. Canonical doc set = 11 docs per Safety/Certs pattern:** `PRD.md` · `BACKEND_STRUCTURE.md` · `APP_FLOW.md` · `DATA_MODEL.md` · `RBAC.md` · `FIELD_MAP.md` · `PDF_TEMPLATES.md` · `SEEDS_PROVENANCE.md` · `CROSS_MODULE_DEPS.md` · `MIGRATION.md` · `TEST_PLAN.md`. **Decision count at v1.1 close ≈ 189** (123 v1.0 + 66 v1.1 incl. D-AUDRS-271 standard; minus 3 superseded retained for audit trail). **N = sum of `required_in:[]` lengths across all decisions** (NOT 189×11 — most decisions only require mention in 1–5 docs). Estimated N ≈ 700–900 for v1.1 Audit DocSuite (vs Certs' 199 — Audit is larger scope). Re-grep tool produces COVERAGE.md showing each decision × required-doc mention status + final percentage. Confirm exact N at DocSuite Step 2 kickoff.
- **New SSOT ID:** D-AUDRS-269

#### Q79 — Pattern: Safety vs Certs
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Use **Certs module pattern** as canonical (more recent, larger scope, 199/199 mechanical re-grep proven). Safety as secondary reference for any aspects Certs doesn't cover. Document the chosen pattern's structure explicitly in COVERAGE.md.
- **Decision:** **OK — Certs as canonical, Safety as secondary.** Rationale: Certs DocSuite (2026-05-13, 199/199 GREEN) is more recent and incorporates Safety DocSuite handover lessons; closer in size to Audit's projected 700–900 mention count; cross-module patterns (D-AUDRS-202 / 235–239 cert linkages, D-AUDRS-264 CMS API contract) directly load-bearing for Audit; re-grep methodology proven. Safety module ([[project_vims_safety_module]]) referenced ONLY for aspects Certs doesn't cover — crew-side wizard patterns from D-AUDRS-116 reference Safety's incident-form simplification work. COVERAGE.md opening section explicitly cites both reference modules with the chosen-pattern declaration.
- **New SSOT ID:** D-AUDRS-270

---

### 3.7 Cross-cutting schema governance (user-supplied 2026-05-19)

#### Q-STD-1 — Database Table Creation Standard (production gap)
- **Status:** ✅ CLOSED 2026-05-19 (user-supplied; not in original 95-question register)
- **Source:** User-supplied 2026-05-19 — "found to be a gap in early production." Cross-cutting governance rule that applies to ALL unbuilt tables in v1.0 + v1.1 + all future modules.
- **Decision:** **Database Table Creation Standard is hereby load-bearing for the Audit DocSuite DATA_MODEL.md and for every prior + future schema decision that has not yet shipped to production.**
  1. **Every newly created table MUST contain an `id` column.**
  2. **The `id` column MUST:**
     - Use the `UNIQUEIDENTIFIER` datatype (SQL Server) / `uuid` (cross-DB equivalent if ever portable).
     - Be defined as the `PRIMARY KEY`.
     - Use `NEWSEQUENTIALID()` as the default value generator unless a specific exception is documented and approved by DPA + lead engineer.
  3. **`INT IDENTITY` is FORBIDDEN** for primary keys in any new development at v1.0 + v1.1+.
  4. **All foreign key references** to parent tables MUST use the **same `UNIQUEIDENTIFIER` datatype** (no type coercion at FK boundary).
  5. **Naming convention (mandatory):**
     - Primary key column name: **`id`** (always, no exceptions — not `audit_id`, not `pk`, not `uuid`)
     - Foreign key column format: **`<parent_table_name>_id`** (e.g., `audit_detail_id`, `vessel_id`, `finding_id`)
  6. **UUID-based keys MUST remain immutable** after record creation. Any update touching `id` is rejected at trigger level.
  7. **Retrospective application to all unbuilt v1.0 + v1.1 tables** — DATA_MODEL.md generated at KLOSS Step 2 MUST follow this standard for every NEW table specified by D-AUDRS-001 through D-AUDRS-270. Tables introduced:
     - v1.0 NEW tables: `audit_detail` extension columns (parent psc_inspection is legacy INT IDENTITY — read-only per D-AUDRS-066, OK to retain), `audit_finding`, `audit_finding_clause` (D-225/227), `master_audit_area`, `master_audit_qualified_auditor`, `master_audit_plan`, `master_audit_clause_ref`, `master_audit_checklist_F604/605/606`, `master_audit_window_rule` (D-242), `master_hod_assignment` (D-106), `master_rca_template` (D-117), `notification_delivery_log` (D-114), `master_slack_channel` (D-113), `audit_finding_sign_event` (D-255).
     - v1.1 NEW tables: `master_external_audit_org` (D-212), `vessel_audit_ro_delegation` (D-212), `master_external_auditor` (D-245), `cert_change_log` (D-239), `audit_pdf_generation` (D-261).
     - **ALL of the above** = UNIQUEIDENTIFIER `id` PK + NEWSEQUENTIALID() default + `<parent>_id` FK convention.
  8. **Exception path:** legacy `psc_inspection` + `psc_corrective_action` + `psc_activity_history` retain their existing INT IDENTITY PKs (locked by live data per D-AUDRS-066). FK references FROM new audit tables INTO these legacy tables use INT (one-direction type bridge). Documented as the ONLY exception.
  9. **DocSuite MIGRATION.md** must include a verification script that grep's `CREATE TABLE` statements for compliance with the standard. Failures block KLOSS Step 2 sign-off.
  10. **Cross-module callout — RESOLVED 2026-05-19:** Safety module is where this gap was discovered in early production; dev team is already remediating Safety + by extension Certs. **No retroactive sweep required from interrogation side.** Audit DocSuite only needs to be born-compliant with the standard; prior modules are owned by the dev team's existing fix-up workstream. This decision confirms compliance for Audit going forward and closes the cross-module callout.
- **New SSOT ID:** D-AUDRS-271

---

## BATCH 4 — DEPLOYMENT, LEGAL, INTEGRATION (Q80–Q90)

#### Q80 — Multi-tenancy
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Confirm KSM-only at v1.0; defer multi-tenant config to v2. Document KSM-specific seeds (14-area scorecard, KSM SMS chapter list, F 604/605/606) as tenant-configurable in v2 design.
- **Decision:** **Same tenancy posture as existing VIMS — single-tenant for KSM at v1.0.** No `tenant_id` column on audit-domain tables. All KSM-specific seeds (14-area scorecard from D-AUDRS-105, KSM SMS chapter list, F 604/605/606 templates, KSM-native NC enum from D-AUDRS-018, per-flag DOC scoping from D-AUDRS-213) hardcoded as part of seed CSVs. Multi-tenant retrofit = v2+ work — would require adding `tenant_id` UNIQUEIDENTIFIER (per D-AUDRS-271 standard) + tenant-scoped masters + tenant-isolated RBAC. v2 design surface documented in `BACKEND_STRUCTURE.md` future-work appendix only; not built at v1.0.
- **New SSOT ID:** D-AUDRS-272

#### Q81 — Data residency
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Confirm hosting region with KSM IT. GDPR applies if any EU-flag vessel or EU crew. Document in privacy / compliance register.
- **Decision:** **Inherit data residency from existing VIMS deployment — same region as the live VIMS Inspection + Safety + Certs modules.** No new regional split for the audit module; database lives alongside existing VIMS tables in the same SQL Server instance (or whatever physical topology KSM IT operates today). GDPR + per-flag residency constraints (if any EU-flag vessel ever enters KSM portfolio) inherit the same posture as existing VIMS — not an audit-module concern. `CROSS_MODULE_DEPS.md` at DocSuite Step 2 records: "Audit module data residency = same as parent VIMS deployment. Confirm regional placement with KSM IT at deployment-config phase, not as audit-spec concern."
- **New SSOT ID:** D-AUDRS-273

#### Q82 — Hosting + offline cache
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Cloud (Azure/AWS — KSM IT decides). Audit module online-only at v1.0 per D-062 — no vessel-side cache except checklist masters read-only. Re-confirm or change D-062 per Q57/Q58 answers.
- **Decision:** **Audit module is NOT part of any offline capability.** Per user direction: "Audit is not part of offline." Software is **pure online** end-to-end. Whatever offline modules VIMS may grow elsewhere (PMS, future safety-form caching, etc.) — Audit is NOT in scope for them at v1.0 or v1.1.
  1. **D-AUDRS-062 (online-only) STANDS UNMODIFIED.** No vessel-side offline cache, no checklist-master pre-fetch, no service-worker IndexedDB, no progressive-web-app offline shell.
  2. **D-AUDRS-254 (vessel-visit offline-by-design) is a PROCESS model, not a software model.** Auditor works on paper notes during the onboard visit and enters data into VIMS ashore where connectivity is normal. No software component runs offline. This decision re-emphasises the distinction for the build team.
  3. **Hosting target:** inherit existing VIMS hosting (per D-AUDRS-273). Audit-module API endpoints live on the same backend, same DB instance, same load-balancer.
  4. **Build implication:** developers building audit-module UI MUST NOT add service-worker offline shells or local-storage caching of audit data. Per-screen "are you online?" checks are unnecessary — assume online; let normal HTTP error handling cover transient disconnects.
- **New SSOT ID:** D-AUDRS-274

#### Q83 — Backup / DR / RTO
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** RPO ≤1h, RTO ≤4h for audit data. Daily off-site backup. Quarterly restore drill documented in IT runbook.
- **Decision:** **Inherit RPO/RTO from existing PSC inspection module configuration.** Per user direction: "same as PSC inspection." Audit-domain tables join the existing VIMS Inspection module's backup/DR scope unchanged — no audit-specific override of RPO, RTO, snapshot cadence, off-site replication interval, or restore-drill frequency. `CROSS_MODULE_DEPS.md` records: "Audit module RPO/RTO = inherited from PSC inspection module deployment; confirm exact values with KSM IT during DocSuite Step 2 if not already documented in VIMS infra spec." Retention horizon for audit-graph specifically remains 15y per D-AUDRS-257 (independent of backup retention — backup is operational DR, 15y retention is record-keeping). If PSC inspection module backup retention is shorter than 15y, the gap is covered by D-AUDRS-257's soft-delete retention in primary DB (no special archive tier required at v1.0).
- **New SSOT ID:** D-AUDRS-275

#### Q84 — Auth + MFA
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Reuse existing VIMS JWT. MFA mandatory for DPA + Lead Auditor + SEQ Manager roles. SSO/AD integration v1.1 if KSM IT supports.
- **Decision:** **Inherit auth + MFA configuration from existing VIMS.** Per user direction: "Yes same as VIMS." 
  1. **JWT:** same token issuer, same lifetime, same refresh policy, same logout behaviour as existing VIMS endpoints. Audit-module endpoints accept the standard VIMS JWT — no audit-specific token class.
  2. **MFA:** inherit current VIMS MFA policy (whatever roles VIMS already enforces MFA for today). No audit-module-specific override of MFA matrix. If KSM IT later strengthens MFA for compliance-sensitive roles (DPA, FM, Lead Auditor, Master signing NC closures), that change applies VIMS-wide — not as an audit-module patch.
  3. **SSO/AD:** if/when VIMS adopts SSO/AD integration, audit module inherits it without code change (JWT issuance abstraction at platform layer, not feature layer).
  4. **Premise note for KLOSS Step 2:** DocSuite RBAC.md references VIMS auth spec by link, doesn't redefine it. If VIMS auth spec is undocumented, raise as a prerequisite to KSM IT — out of audit-module scope.
- **New SSOT ID:** D-AUDRS-276

#### Q85 — Email provider
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Reuse existing VIMS SMTP. Bounce handling = bounce → mark `notification_delivery_log.delivery_status=BOUNCED` + retry up to 3× over 24h. Vessel satellite email reliability is KSM's responsibility, not VIMS.
- **Decision:** **OK as recommended — inherit existing VIMS SMTP.** Same provider, same connection config, same bounce-handling pipeline as existing VIMS notification-emitting features. Audit module emits to the existing platform send queue; no audit-specific SMTP client. Bounce-handling: events feed back into `notification_delivery_log` (D-AUDRS-114) with `delivery_status='BOUNCED'`; 3× retry over 24h per D-AUDRS-111 exponential backoff; permanent failures surface in DPA "Failed Notifications" widget per D-AUDRS-262. Vessel sat-link reliability is KSM ops responsibility (not VIMS-side concern). Note for build: even though PSC inspection doesn't currently emit email (per D-AUDRS-264), the underlying VIMS SMTP infrastructure is presumed to exist and serve other VIMS features; Audit reuses without reinvention. If VIMS SMTP infra turns out to be undocumented at DocSuite Step 2, escalate as a VIMS-platform prerequisite, NOT as an audit-module build task.
- **New SSOT ID:** D-AUDRS-277

#### Q86 — Slack workspace scope
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** KSM-specific workspace at v1.0. master_slack_channel is KSM-only. Multi-tenant Slack support v2.
- **Decision:** **OK as recommended — single KSM Slack workspace at v1.0.** Matches Q80 single-tenancy posture (D-AUDRS-272). `master_slack_channel` (D-AUDRS-113 / D-AUDRS-265) stores per-vessel webhook URLs all pointing into the one KSM Slack workspace — same workspace KSM uses today for safety + PSC + other VIMS Slack integrations per [[project_vims_safety_module]] pattern. Audit module adds new channel rows to existing per-vessel channel infra; zero new workspace config. Multi-tenant Slack support = v2+; would need `workspace_id` column + per-tenant webhook routing layer.
- **New SSOT ID:** D-AUDRS-278

#### Q87 — Cross-module version compatibility
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Pin minimum compatible versions of Safety / Circular / Certs / HRM / PMS in cross-module dependency section of SSOT. Integration tests at KLOSS Step 3 verify.
- **Decision:** **OK as recommended.** `CROSS_MODULE_DEPS.md` in DocSuite Step 2 pins minimum-compatible versions of:
  1. **Safety module** ([[project_vims_safety_module]]) — min version exposing incident lookup endpoints for `INCIDENT_FOLLOWUP` trigger (D-AUDRS-122).
  2. **Certs module** ([[project_vims_certificates_module]]) — min version with `cert_change_log` table (D-AUDRS-239) + `vessel_cert.version` field for CAS (D-AUDRS-236) + the cross-module anniversary read pattern (D-AUDRS-240/243). Bidirectional SSOT cross-ref table per D-AUDRS-237.
  3. **CMS** — min version exposing `getVesselLocalTime` (D-AUDRS-249), `getActiveCrewByRank` (D-AUDRS-250), `getOfficialEmail` (D-AUDRS-264) endpoints.
  4. **HRM** (HRM501) — min version exposing vessel-side rank/qualification API per Q88 / D-AUDRS-280.
  5. **Live PSC Inspection module** ([[vims_inspection_live_truth]]) — min schema version of `psc_inspection` / `psc_corrective_action` / `psc_activity_history` supporting `audit_classification` enum (EXTERNAL added per D-AUDRS-200).
  
  Integration tests at KLOSS Step 3 (build phase) verify each cross-module call against the pinned min version. Failures block Phase 0 cutover. Pin format: semver-like `vMAJOR.MINOR.PATCH` matching whatever module-versioning convention KSM IT publishes (or git tag / build number if no formal versioning).
- **New SSOT ID:** D-AUDRS-279

#### Q88 — HRM501 rank auto-suggest
- **Status:** ✅ CLOSED 2026-05-19 (with critical scope split: vessel-side ONLY)
- **Recommended Action:** Live FK to HRM501 read-only API. Cached in client for performance. Stale-while-revalidate strategy.
- **Decision:** **HRM501 = VESSEL-SIDE ONLY. Office-side follows VIMS standard (same as existing VIMS).** Per user direction: "HRM501 for vessel side only not office side follow same as VIMS."
  1. **Vessel-side users** (Master, Chief Officer, Chief Engineer, Safety Officer, ratings — anyone mustered on a ship): rank source = HRM501 live read-only API. Same integration pattern family as D-AUDRS-250 (CMS live crew). New service contract: `Hrm501Client.getCurrentRank(user_id)` returns active rank at lookup time. Client-side cache: 15-min TTL stale-while-revalidate (matches D-AUDRS-264 CMS email cache TTL).
  2. **Office-side users** (DPA, FM, Marine Sup'tt, HoD, SEQ Manager, auditor): rank/role source = VIMS `users.role` column or whatever existing VIMS-standard mechanism handles office-staff role assignment today. NO HRM501 lookup for office users. `master_audit_qualified_auditor` (D-AUDRS-039) joins office-side rows via `users.user_id` + `users.role`; vessel-side rows join via `users.user_id` + HRM501-resolved rank.
  3. **`master_audit_qualified_auditor` schema clarification:** carries `auditor_scope` enum {`VESSEL_SIDE`, `OFFICE_SIDE`} so the resolver picks the right lookup at runtime. No rank stored on the qualified-auditor row (would go stale on promotion); rank is always resolved live. `qualified_for_seq` BIT (D-AUDRS-256) is office-side only — vessel-side auditors don't audit office depts.
  4. **No mirror tables in VIMS.** Single source of truth = HRM501 for vessel ranks, VIMS users table for office roles. Both kept canonical in their owning systems.
  5. **Premise check resolved:** if HRM501 lacks a `/users/{id}/current_rank` endpoint, raise as integration prerequisite (consistent with D-AUDRS-279 pinning).
- **New SSOT ID:** D-AUDRS-280

#### Q89 — Device / browser matrix
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Desktop = Chrome 120+ / Edge 120+ / Safari 17+. Mobile = iOS 16+ Safari, Android 13+ Chrome. Document. Wizard tested on iPad (12.9") + iPhone (6.7").
- **Decision:** **OK as recommended.** Audit module supports the same device/browser matrix as the broader VIMS platform — if a formal VIMS matrix exists, audit module references it; if not, audit module's matrix becomes the new VIMS-wide default. Concrete targets:
  - **Desktop:** Chrome 120+ / Edge 120+ / Safari 17+ / Firefox 121+ (added — internal users may use Firefox).
  - **Mobile:** iOS 16+ Safari, Android 13+ Chrome. Wizard adaptive layout per D-AUDRS-120 (≥1024px = 2-column; <1024px = mobile-first).
  - **Test devices:** iPad (12.9") + iPhone (6.7") for mobile QA per D-AUDRS-116; Chrome desktop for primary office UX per D-AUDRS-120.
  - **Not supported at v1.0:** IE11 (deprecated industry-wide), tablet-Android <13, in-app browsers (LinkedIn / WeChat) — documented in §16 OPM "Known Limitations".
  - DocSuite Step 2 records exact list in `TEST_PLAN.md`.
- **New SSOT ID:** D-AUDRS-281

#### Q90 — Language / literacy
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** English-only UI at v1.0. Plain-language wizard targets CEFR B1 reading level. Translation v2 if user demand emerges. Document literacy assumption.
- **Decision:** **OK as recommended.** English-only UI at v1.0; plain-language wizard (D-AUDRS-116) targets CEFR B1 reading level — short sentences, common vocabulary, jargon replaced ("What did you do right away?" not "Master immediate corrective action"). Inline examples + help text on every wizard step. Translation = v2+ if KSM expands to non-English-proficient crew (none currently). §16 OPM documents literacy assumption: "Crew expected to operate at CEFR B1 English minimum, aligned with STCW Reg. VI/1 working-English requirement for all officers + ratings." TEST_PLAN.md at DocSuite Step 2 must include readability check on wizard copy (target Flesch-Kincaid grade ≤8).
- **New SSOT ID:** D-AUDRS-282

---

## BATCH 5 — META (Q91–Q95)

#### Q91 — Hidden supersedes
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** LLM audits all 133 decisions for "supersedes" mentions; produces list. Cross-check against §9 Decisions Log column "Source / Supersedes". Any inline-superseded-but-not-flagged decisions get explicit `SUPERSEDED` status retroactively.
- **Decision:** **OK as recommended.** Before SSOT §9 batch-merge, run full-text scan over all ~189 active decisions (123 v1.0 + 66 v1.1 incl. D-AUDRS-271 standard) for inline `supersedes` / `rescinds` / `replaces` mentions. Cross-check against §9 Decisions Log "Source / Supersedes" column. Catalog known supersedes from this cycle:
  - D-AUDRS-107..110 supersede D-AUDRS-056 + D-AUDRS-100 (PSC-style PIC, R1.I)
  - D-AUDRS-212 supersedes D-AUDRS-201 (org-identity portion, Q3)
  - D-AUDRS-202 supersedes D-CERT-025 for v1.1 (cross-module)
  - D-AUDRS-216 modifies D-AUDRS-049 (cycle-reset case; not strict supersede)
  - D-AUDRS-264 supersedes D-AUDRS-112 email-source portion (Q72)
  - D-AUDRS-254 anchors NC SLA clocks on `VESSEL_ACKNOWLEDGED` — modifies D-AUDRS-073 deadline math (not supersedes; refines anchor)
  - D-AUDRS-274 RE-EMPHASISES D-AUDRS-062 (online-only) + clarifies D-AUDRS-254 is process-only (not software supersede)
  - D-AUDRS-256 introduces `qualified_for_seq` BIT — extends D-AUDRS-039 (master_audit_qualified_auditor) but does NOT supersede
  - D-AUDRS-280 splits master_audit_qualified_auditor by auditor_scope — extends D-AUDRS-039 (no supersede)
  - Final grep at SSOT merge catches anything missed. Inline-superseded-but-not-flagged decisions get explicit `SUPERSEDED` status retroactively + cross-link in both directions.
- **New SSOT ID:** D-AUDRS-283

#### Q92 — Decision ID gap (124–199)
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Reserve 124–199 for v1.0 supplemental decisions that may emerge during DocSuite generation (e.g., minor schema fixes, validation gaps surfaced by writing PRD). v1.1 sits at 200+, v1.2 at 300+, v1.3 at 400+.
- **Decision:** **OK as recommended.** ID allocation convention locked:
  - **D-AUDRS-001..123:** v1.0 Internal Audit (FROZEN at v0.18).
  - **D-AUDRS-124..199:** RESERVED for v1.0 supplemental decisions that may emerge during DocSuite Step 2 generation (minor schema fixes, validation gaps surfaced while writing DATA_MODEL / TEST_PLAN / FIELD_MAP, seed-row corrections from SEEDS_PROVENANCE.md drafting). New decisions in this range require DPA + Prince re-confirmation.
  - **D-AUDRS-200..283:** v1.1 External Audit + cross-cutting standards (incl. D-271 DB Table Creation Standard).
  - **D-AUDRS-284..299:** RESERVED for v1.1 supplemental.
  - **D-AUDRS-300+:** v1.2 RightShip (deferred per D-247).
  - **D-AUDRS-400+:** v1.3 Manning/Security (deferred per D-247).
  - Convention published in SSOT §0 + §9 header.
- **New SSOT ID:** D-AUDRS-284

#### Q93 — Sign-off process
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Three-step sign-off: (1) LLM marks "freeze candidate"; (2) user confirms; (3) named KSM DPA / SEQ Manager confirms in writing (email captured as attachment to SSOT). v1.0 is currently at step (2). Step (3) pending.
- **Decision:** **OVERRIDE — Prince is the final freeze authority.** Per user direction: "Prince is final freeze." Simplified two-step protocol:
  1. **LLM marks "freeze candidate"** — interrogation closes, SSOT §9 batch-merge complete.
  2. **Prince (user) confirms freeze** — terminal authority; no separate DPA/SEQ Manager written sign-off required. Prince's verbal/written confirmation in this interrogation cycle IS the freeze authority for both v1.0 and v1.1.
  - This explicitly drops the "named KSM DPA / SEQ Manager confirms in writing" third step from the prior recommendation.
  - Rationale: Prince acts as the customer-side product owner for VIMS modules; DPA/SEQ Manager will be involved at operational rollout (training, sign-off-by-use) but not as a documentation gate.
  - **v1.0 status:** FROZEN at v0.18 per Prince confirmation 2026-05-18 (no pending external sign-off).
  - **v1.1 status:** FROZEN at end of this batch (this Q95 closure marks completion of interrogation cycle); SSOT batch-merge then runs.
- **New SSOT ID:** D-AUDRS-285

#### Q94 — Mid-build SSQE Manual revision
- **Status:** ✅ CLOSED 2026-05-19
- **Recommended Action:** Document version of SSQE Manual referenced (Rev 01 Feb 2026). If KSM revises mid-build, change-impact analysis via diff; minor revisions absorbed in next sprint, major revisions trigger SSOT re-interrogation round.
- **Decision:** **OK as recommended.** Reference version locked: **KSM SSQE Manual Rev 01 Feb 2026** (per [[reference_ssqe_manual]] memory). All SSOT + DocSuite citations reference this version explicitly with chapter + sub-section + page where applicable. Mid-build revision handling:
  - **Minor revision** (typo, formatting, clarification of existing rule): change-impact diff produced by LLM; absorbed in next dev sprint as documentation update; no SSOT change unless rule changes.
  - **Major revision** (new requirement, process restructure, §10 chapter overhaul, new audit-area added, NC severity threshold change): triggers SSOT re-interrogation round R-AUD-vN.0; affected decisions get `REVIEW-PENDING-MANUAL-REV-<rev_number>` status; build paused on affected modules until reviewed.
  - **Trigger detection:** quarterly grep of `KSM SSQE Manual` references in SSOT against the live manual file at project root — version-stamp mismatch surfaces a flag. Quarterly cadence sufficient for KSM's typical revision cycle.
  - At SSOT merge, add new §0.4 sub-section "Reference Document Versions" listing SSQE Manual Rev 01 Feb 2026 + all other authoritative references with their versions.
- **New SSOT ID:** D-AUDRS-286

#### Q95 — Internal Audit integration coverage check
- **Status:** ✅ CLOSED 2026-05-19 (re-framed by user; OPTION A locked)
- **Re-framed scope:** Verify all integration points for Internal Audit v1.0 are explicitly locked before freeze. User picked OPTION A — lock the 3 implicit integrations as "manual reference at v1.0; live API = v2+".
- **Decision (D-AUDRS-287):** **Internal Audit integration coverage explicitly locked.** Three implicit-integration ambiguities removed from build risk:
  1. **PMS module integration — MANUAL REFERENCE ONLY at v1.0.** Auditor enters PMS task ID / title / overdue context as free text in `audit_finding.description` and `audit_finding_nc.root_cause_summary`. No `pms_task_id` FK on audit tables. No live API call from audit module to PMS. D-AUDRS-105's "PMS" scorecard area is a label only (not an integration). D-AUDRS-117's `PMS_OVERDUE` RCA template references PMS contextually, not via FK. **Live PMS API integration deferred to v2+.** Document in `CROSS_MODULE_DEPS.md` and `§11`.
  2. **SMS Document Control integration — STATIC CONSTANTS ONLY at v1.0.** "SMS Filing reference" tags (A-2 / A-9 / A-20 / A-28) on F 601 / F 602 / KSM-F-NC-001 PDFs are **rendered as static derived constants** at PDF generation time. No lookup to an SMS Document Control system. Auditor cites SMS document IDs (chapter / section / revision number) as free text in finding description. No `sms_doc_id` FK on audit tables. **Live SMS Doc Control API integration deferred to v2+.** Document in `CROSS_MODULE_DEPS.md` and `§11`.
  3. **Crew Training / Competency module integration — MANUAL REFERENCE ONLY at v1.0.** D-AUDRS-117's `TRAINING_GAP` RCA template doesn't FK to a training records system. Auditor enters crew member name / rank / training gap as free text. No `training_record_id` FK on audit tables. **Live HRM training-records API integration deferred to v2+.** Document in `CROSS_MODULE_DEPS.md` and `§11`.
  4. **SSOT §11 Cross-Module Dependencies table rewrite at batch-merge.** Current §11 is stale (says "Circular: No linkage" but D-AUDRS-065 added that linkage in R0.8). At SSOT §9 batch-merge, rewrite §11 to reflect the **8 active integrations** (CAR engine · PSC Inspection · Circular module · Safety module · CMS-WRH · CMS-crew · CMS-email · HRM501) + **3 explicit deferred integrations** (PMS / SMS Doc Control / Training records — all "v2+").
  5. **Build-team posture lock:** every cross-module call appearing in DocSuite DATA_MODEL.md or APP_FLOW.md MUST trace to one of the 8 active integration entries; anything not listed is rejected at code review. This closes the ambiguity that prompted the user's question and removes the risk that the build team assumes an integration exists where none does.
- **New SSOT ID:** D-AUDRS-287

---

## Closure log

| Batch | Q range | Closed at | New D-IDs assigned | Notes |
|-------|---------|-----------|---------------------|-------|
| 1A | Q1–Q5 | 2026-05-18 | D-AUDRS-210..214 | v1.1 scope boundary. Q3 supersedes D-201 org-identity portion. Q4 added critical "DOC per-flag" refinement (new mandatory `flag_state_code` column on DOC audits). Q5 confirmed both DOC_INITIAL + DOC_INTERIM; enum now ~18 values. SSOT §9 batch-merge pending end-of-round. |
| 1B | Q6–Q10 | 2026-05-18 | D-AUDRS-215..219 | ISPS_INITIAL handled by D-207 (no new subtype). New `is_cycle_resetting` BIT for additional-audits-that-reset-anniversary (DPA authority). Registration SLA 7d soft / 30d hard. Attachment versioning (DRAFT/FINAL) + non-PDF paths (LETTER/EMAIL_EXPORT) with DPA attestation. D-060 enum gains 4 new categories. D-076 mime whitelist extended with EML. |
| 1C | Q11–Q15 | 2026-05-18 | D-AUDRS-220..224 | Q11: role-scoped registration (Master for vessel audit, DPA/Marine Supt for office audit — open: define Marine Supt sub-scope). Q12: soft-dedup + DB UNIQUE + DPA-only merge. **Q13 (key refinement): rework loop reuses PSC CAR REWORK_REQUESTED pattern — no new DPA-arbiter concept; office-review→rework→registrant-resubmit until office accepts.** Q14: new `master_external_auditor_category_map` seeded with IACS labels at KLOSS Step 2. Q15: optional `clause_subref_text` column avoids master restructure. |
| 1D | Q16–Q20 | 2026-05-18 | D-AUDRS-225..229 | Q16: OTHER bucket + QA counter. Q17: new `audit_finding_clause` junction table with is_primary; denormalised mirror on audit_finding retained. **Q18 REJECTED: no VIMS dispute mechanism — disputes resolved at auditor's closing meeting pre-issue; report immutable post-issue. Drops 6 columns + 1 gate from proposed model.** Q19: alt evidence path with DPA attestation + new attachment categories. Q20: decoupled `external_closure_status` from internal action completion — cert state follows auditor; SMS rigour tracked separately. |
| 1E | Q21–Q24 + Q26 (off-by-one — register Q25 skipped, requeued) | 2026-05-18 | D-AUDRS-230..234 | **Q21 REJECTED: no reopen mechanism — recurrence at next audit = new finding, original stays closed. No parent_finding_id.** **Q22 SUPERSEDES D-204 EffRev portion: tiered EffRev (External Major=mandatory, Minor=optional, Obs=none), DPA performs.** Q23: priority enum + auto-CRITICAL escalation for cert-suspended Major NCs (24h SLA, 7d CA plan, daily DPA digest). Q24: type-ahead cert linkage with vessel/flag/cert_type scoping. Q26: outbox pattern for cert writeback (audit never blocked by Certs availability). **Register Q25 [forgotten cert linkage] OPEN — moved to Batch 1F head.** |
| 1F | Q25 + Q27..Q30 | 2026-05-18 | D-AUDRS-235..239 | Q25: post-closure cert linkage edits DPA-gated with audit-trail; new outbox row on add. Q27: CAS on cert version; CONFLICT outbox status; DPA accept/force resolution. **Q28 + Q30: cross-module obligations on Certs SSOT/DocSuite — new `cert_change_log` table (append-only), bidirectional SSOT cross-ref table, mechanical re-grep check at KLOSS Step 2.** Q29: multi-gate suspension (attachment + DPA two-step incl. typed cert# + Flag notification tracking + quad-recipient notification). Cross-module action items captured for Certs SSOT update session before KLOSS Step 2. |
| 1G | Q31..Q35 | 2026-05-18 | D-AUDRS-240..244 | **Q31 + Q34 KEY REFINEMENT: cert anniversary = Class Status Report (existing Certs-module sync pattern), not audit-side override. Audit module reads anniversaries; Class Status Report sync owns reconciliation; cert_change_log captures sync events. Drops `cert_anniversary_date_override` column.** Q32: change of ownership/flag entirely Certs-module concern; documented in §11 cross-module deps. Q33: data-driven window rules via new `master_audit_window_rule` seeded with IMO/MLC/ISPS citations. Q35: external auditor sign-off via attached signed PDF only; no auditor system access at v1.1. |
| 1H | Q36–Q37 closed; Q38–Q50 deferred | 2026-05-18 | D-AUDRS-245..247 | Q36: `master_external_auditor` master with auto-suggest + pending-review on free-text fallback. **Q37: minimal PII surface — name + org only; no credential/qual/signature fields. GDPR Art 6(1)(f)+(c) basis; Art 17(3)(b/e) exemptions on erasure.** **Q38 MAJOR SCOPE LOCK (D-AUDRS-247): RightShip (Q38–Q45) deferred entirely to v1.2 build cycle. Manning + Security (Q46–Q50) deferred to v1.3 build cycle. THIS INTERROGATION CYCLE = Internal + External Audit only. From here forward, batches focus on Q51+ (cross-cutting v1.0 gaps + deployment/legal/integration + meta).** |
| 1I | Q51–Q55 | 2026-05-19 | D-AUDRS-248..252 | Q51: `audit_end_date` added; SLAs anchor on end_date. **Q52 OVERRIDE: dual-TZ — storage UTC; office display ITC; vessel display from CMS WRH module (same integration as PSC). SLA clock = ITC (office TZ).** **Q53 OVERRIDE: signatures bind to RANK (Master/CO/CE), not person. CMS live-crew lookup at sign time (reuses PSC pattern). PDF shows whichever Master signed each part — no handover workflow.** **Q54 REJECTED: Lead Auditor must clear open audits/NCs before company departure — operational policy via HR offboarding, NOT a software feature. No reassign action, no AUDIT_P_015.** **Q55 REJECTED: DPA-on-leave is not a real KSM scenario (DPA logs in and completes regardless). `master_hod_assignment` (D-AUDRS-106) NOT extended to DPA dept.** |
| 1J | Q56–Q60 | 2026-05-19 | D-AUDRS-253..256 (4 IDs; Q58 folded into Q57) | Q56: Acting HoD auth = **DPA + Fleet Manager (FM)** only; new gate AUDIT_P_016; self-acting forbidden; 90-day max acting period. **Q57 + Q58 REFRAMED — KEY MODEL SHIFT: audit vessel-visit is offline-by-design.** Workflow = pre-board prep (ashore online) → conduct onboard offline → enter report ashore online → vessel acknowledges. New audit_detail status chain: `REPORT_FINALIZED → VESSEL_ACKNOWLEDGED → CLOSURE_IN_PROGRESS`. New gate **AUDIT_P_017** (Master rank-bound vessel acknowledgement). **NC SLA clocks anchor on VESSEL_ACKNOWLEDGED, not finding_raised_at** — updates D-AUDRS-073. D-AUDRS-062 online-only stays. No paper-attachment workflow, no backdate-with-reason for offline period. Q59 ok: 30-day Master-sig backdate w/ reason ≥50 chars. Q60: primary CoI path = cross-dept HoD with new `qualified_for_seq` BIT on master_audit_qualified_auditor; external auditor is fallback. |
| 1K | Q61–Q65 | 2026-05-19 | D-AUDRS-257 (1 ID only; Q61/Q62/Q64/Q65 all rejected as not-applicable) | **Q61 + Q62 REJECTED (NOT APPLICABLE):** CoI/independence declarations are not real KSM scenarios — internal auditors are all KSM staff; external auditors come via RO/Flag (KSM doesn't pick them). No declaration column, no PDF cover-sheet field, no DPA review gate. **Q63 OK: 15-year retention** across full audit graph (audit_detail + finding + clause + attachment blobs + notification_delivery_log + psc_audit_log + sign events). Soft-delete only at v1.0 via existing is_deleted family; hard-delete + archival = v2+. **Q64 REJECTED (handover-pack feature dropped):** audit records are KSM-internal and NOT shared with new manager on divestment; no ZIP-builder, no gate, no inbound-acquisition ingest. Vessel retained internally w/ `vessel_status='DIVESTED'` read from CMS. **Q65 REJECTED (NOT APPLICABLE):** GDPR erasure not a live concern at KSM jurisdictionally; no canned response, no privacy-notice text bundled. D-AUDRS-246 (external auditor PII) stands narrowly for that role only. Cumulative simplification: 1 column, 2 gates, 1 background job, 4 UI screens, multiple legal/OPM drafts all dropped. |
| 1L | Q66–Q69 (Q66 closed on re-fire) | 2026-05-19 | D-AUDRS-258..261 | Q67 ok: no OCR/biometric sig verification at v1.0. **Q68 KEY UNBLOCK: KSM SSQE confirms all Flag States accept wet-ink + scan-back.** D-AUDRS-061 stays unmodified; HARD BLOCKER annotation REMOVED at SSOT merge. No eIDAS / 21 CFR / MSC.1/Circ.1593 e-sig required. Q69 ok: external auditor stamp captured as part of scanned report PDF. **Q66 (re-fired with scenarios A/B/C) → user chose OPTION A: build QR/hash replay-prevention.** New `audit_pdf_generation` table with content_hash + qr_payload + pdf_version (increments on regen per D-081 office-edit). New `pdf_hash_validation_status` enum on audit_attachment (MATCHED/MISMATCH_FINDING/MISMATCH_VESSEL/MISMATCH_VERSION/UNREADABLE/NOT_APPLICABLE). DPA review queue at `/dpa/scan-validation-queue` w/ ACCEPT_WITH_REASON or REJECT_AND_REQUEST_RESCAN. New gate AUDIT_P_018 (DPA-only). Upload NEVER blocked outright — mismatch flagged for review. External-audit attachments (D-201/204) get NOT_APPLICABLE. |
| 1M | Q70–Q74 | 2026-05-19 | D-AUDRS-262..265 (4 IDs; Q74 rejected NOT APPLICABLE) | Q70 ok: DPA owns "Failed Notifications" widget at `/dpa/notifications/failed`; Manual Retry + Mark as Notified Offline actions; logged to psc_audit_log. Q71 ok: no opt-out for 7 audit notification types — mandatory regulatory. **Q72 OVERRIDE (SUPERSEDES D-AUDRS-112 email-source portion): vessel email pulled from CMS via `CmsVesselClient.getOfficialEmail(vessel_id)` (same integration family as D-249 WRH + D-250 crew); no new `VesselData.official_email` column in VIMS. PSC inspection does NOT send email — Audit is first VIMS feature needing email regulatory trail. CMS API requirement added to §11 cross-module deps.** Q73 simplified: per-vessel Slack channel only (reuses KSM's existing per-vessel channels); no fleet-wide DPA channel; no per-event-type overrides; office audits skip Slack at v1.0 (in-system + email only). **Q74 NOT APPLICABLE: notification storm not real at KSM due to D-049 cadence spacing + bounded recipient set (DPA + HoD + Master). No rate-limit table, no digest formatter.** Saves: 1 column on VesselData (Q72), 1 rate-limit table + digest job (Q74). |
| 1N | Q75–Q79 + Q-STD-1 (user-supplied) | 2026-05-19 | D-AUDRS-266..271 (6 IDs incl. user-supplied DB standard) | Q75 ok: mechanical re-grep ≥99% coverage matching Certs 199/199 pattern; required_in:[] tag per decision. Q76 ok: `<seed>_provenance.md` sibling for every seed CSV. Q77 ok: FIELD_MAP UI cell format `<mockup_id>:<element_id>` with `MOCKUP-PENDING-KLOSS-STEP-2` placeholder when not yet wireframed. Q78 ok with updated 11-doc canonical set (PRD · BACKEND_STRUCTURE · APP_FLOW · DATA_MODEL · RBAC · FIELD_MAP · PDF_TEMPLATES · SEEDS_PROVENANCE · CROSS_MODULE_DEPS · MIGRATION · TEST_PLAN); estimated N≈700-900 for Audit DocSuite. Q79 ok: Certs canonical, Safety secondary. **Q-STD-1 USER-SUPPLIED CROSS-CUTTING STANDARD (D-AUDRS-271): DB Table Creation Standard — every new table uses UNIQUEIDENTIFIER `id` PK with NEWSEQUENTIALID() default; NO INT IDENTITY for new tables; FK = `<parent>_id` matching UNIQUEIDENTIFIER datatype; immutable post-create. Retroactive to all unbuilt v1.0 + v1.1 tables (legacy psc_inspection family is sole exception). MIGRATION.md gets verification grep script.** Cross-module retro-sweep callout RESOLVED at Batch 1O — Safety is where gap was discovered, dev team already remediating Safety + Certs. |
| 1O | Q80–Q84 | 2026-05-19 | D-AUDRS-272..276 (5 IDs) | All five answers = **"same as VIMS / PSC inspection"** — inherit existing deployment posture without audit-module override. Q80: single-tenant for KSM; multi-tenant=v2; no `tenant_id` columns. Q81: data residency inherits existing VIMS region; no audit-specific override; `CROSS_MODULE_DEPS.md` records inheritance. **Q82 CRITICAL CLARIFICATION:** "Audit is not part of offline." Software is pure online end-to-end. D-AUDRS-062 stands unmodified. D-AUDRS-254's "offline-by-design" is the PROCESS model only (paper notes onboard); not a software offline mode. Build team MUST NOT add service workers / IndexedDB / PWA offline shells for audit screens. Q83: RPO/RTO/backup cadence inherit PSC inspection module; 15y audit-graph retention (D-257) sits atop normal backup. Q84: JWT + MFA + SSO inherit VIMS — no audit-module-specific token class or MFA override. |
| 1P | Q85–Q89 | 2026-05-19 | D-AUDRS-277..281 (5 IDs) | Q85 ok: inherit VIMS SMTP; audit reuses existing platform send queue + bounce pipeline; if VIMS SMTP infra undocumented at DocSuite Step 2, escalate as VIMS-platform prerequisite. Q86 ok: single KSM Slack workspace (matches Q80); audit module adds per-vessel channel rows into existing workspace KSM uses for safety/PSC. Q87 ok: `CROSS_MODULE_DEPS.md` pins min compatible versions of Safety/Certs/CMS/HRM/PSC; integration tests at KLOSS Step 3 verify. **Q88 KEY SCOPE SPLIT (D-280): HRM501 = VESSEL-SIDE ranks only. Office-side users = VIMS users.role standard. `master_audit_qualified_auditor` gets `auditor_scope` enum {VESSEL_SIDE, OFFICE_SIDE} to pick right lookup at runtime. No rank mirror in VIMS; live-resolved from HRM501 / users.role. 15-min stale-while-revalidate cache.** Q89 ok: Chrome 120+ / Edge 120+ / Safari 17+ / Firefox 121+ desktop; iOS 16+ / Android 13+ mobile; IE11 + tablet-Android<13 + in-app browsers explicitly unsupported at v1.0. |
| 1Q | Q90–Q95 (FINAL — interrogation closure) | 2026-05-19 | D-AUDRS-282..287 (6 IDs) | Q90 ok: English-only UI; CEFR B1 plain-language wizard target; readability check in TEST_PLAN.md. Q91 ok: pre-merge supersedes audit run on all ~189 active decisions; cataloged: D-107..110 supersede D-056+D-100, D-212 supersedes D-201 org portion, D-202 supersedes D-CERT-025, D-264 supersedes D-112 email-source, D-254 modifies D-073 SLA anchor. Q92 ok: ID allocation locked (v1.0 124-199 reserved, v1.1 200-299, v1.2 300+, v1.3 400+). **Q93 OVERRIDE (D-285): Prince is final freeze authority — drops the "named DPA/SEQ Manager written sign-off" third step.** Q94 ok: SSQE Manual Rev 01 Feb 2026 referenced; mid-build minor revision = diff & absorb; major revision = re-interrogation round. **Q95 RE-FRAMED by user as integration audit; OPTION A locked (D-287): 3 implicit integrations explicitly deferred to v2 — PMS, SMS Document Control, Crew Training/Competency are MANUAL FREE-TEXT REFERENCE ONLY at v1.0; live API integration = v2+. §11 Cross-Module Dependencies table rewritten at SSOT merge to reflect 8 active integrations (CAR engine, PSC Inspection, Circular, Safety, CMS-WRH, CMS-crew, CMS-email, HRM501) + 3 deferred-to-v2.** **Interrogation cycle complete: 95/95 questions resolved (78 closed + 13 deferred to v1.2-v1.3 + 4 rejected NOT APPLICABLE).** |
