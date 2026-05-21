# VIMS Safety Module — Requirements Interrogation

> **Status:** IN PROGRESS — Session 3 paused 2026-04-10
> **Started:** 2026-04-09
> **Progress:** Q1-Q46 answered (Rounds 1-12 complete), Round 13+ pending
> **Method:** Systematic Q&A — 3 questions at a time
> **Purpose:** Eliminate all assumptions before documentation phase
> **Questions answered:** 46 + sub-questions
> **Pending rounds:** 13-15 (RBAC, PDF Export, Edge Cases)
> **Resume at:** Round 13 Q47 — Permissions & RBAC (question already drafted, awaiting answer)

---

## Round 1 — Scope & Boundaries

### Q1. Sub-Feature Scope for V1
Your legacy system has 6 distinct sub-features: Incident Reporting, Near Miss Reporting, Safety Committee Meeting, Trouble Report, Observation Notification, and Safety Alerts. Which of these are **in scope for V1** of the VIMS Safety Module, and which are deferred to later phases?

**Answer:** V1 scope: **Incident Reporting, Near Miss Reporting, Safety Committee Meeting**. Trouble Report and Safety Alerts are deferred. Observation is folded into Near Miss Reporting (not a standalone feature).

---

### Q2. Unified vs Separate Listing
JiBe combines Incidents and Near Misses into a **single unified listing page** with a shared grid and a "Create New" dropdown that splits into Incident or Near Miss. Your legacy keeps them as completely separate modules. Which approach do you want for VIMS?

**Answer:** **Unified listing page** (PO asked for recommendation — rationale: single entry point for all safety events, less navigation, filterable by type, codes distinguish records (IN-xxx / NM-xxx), consistent with JiBe pattern, better UX for office users monitoring fleet-wide safety). PO confirmed.

---

### Q3. Unified Incident + Injury Form
JiBe uses a **unified Incident + Injury form** — injuries are just an incident with "Incident with Injury" selected as a type, which unlocks injury-specific fields. Your legacy treats injuries as part of the incident severity matrix (Injury is one of 7 criteria). Do you want a unified form like JiBe, or do you want injuries handled differently?

**Answer:** Yes — **unified form like JiBe**. "Incident with Injury" type unlocks injury-specific fields (crew involved, nature of injury, body areas, first aid, off-duty hours).

---

### Q4. Trouble Report → Incident Escalation
Your legacy has a **Trouble Report → Incident escalation** path (`Proc_CovertTroubleToIncident`). If Trouble Reports are in scope, does this escalation path remain? If Trouble Reports are deferred, does anything replace that equipment-focused reporting path?

**Answer:** Trouble Reports deferred (per Q1). Equipment-focused trouble reports will be handled through **PMS module** (defect/work order path), not Safety Module. No gap to fill in V1.

---

### Q5. Safety Alerts Scope
Your legacy has **Safety Alerts** (737 records) — these are external alerts from IMO, flag state, P&I clubs, class societies pushed to vessels. Is this in scope for V1, or is it handled outside the Safety Module (e.g., via Fleet Messages)?

**Answer:** Deferred — not in V1 scope (per Q1).

---

### Q6. Observation Notifications Scope
Your legacy has **Observation Notifications** (312 records) — office sends observation findings to vessels. JiBe has "Be Safe+ Observations" as a topic in meetings. Is Observation a standalone feature in V1, or folded into meetings/findings?

**Answer:** Folded into Near Miss Reporting — not a standalone feature (per Q1).

---

## Round 2 — Incident Reporting Specifics

### Q7. Classification Model
Your legacy severity matrix has **4 levels** (Minor/Significant/Severe/Major) across **7 categories** (Injury, Pollution, Business Loss, Navigational, PSC Detention, Security, Other). JiBe uses **coded incident types** (T01-Collision, T02-Grounding, etc.) as a multi-select with a separate Impact Assessment section. Which classification model do you want — the legacy severity×category matrix, JiBe's coded types, or a different approach entirely?

**Answer:** PO wants a model **better than JiBe**, not a copy. **Hybrid 3-layer model confirmed:**

**Layer 1 — Incident Type (multi-select, admin-configurable master list):**
Collision, Grounding/Stranding, Contact/Allision, Fire/Explosion, Equipment Failure, Cargo Damage/Loss, Pollution/Spill, Security Breach, Incident with Injury (unlocks injury fields), Other. **Master table — office admin can add new types as needed.**

**Layer 2 — Severity (single-select):**
Minor / Significant / Severe / Major

**Layer 3 — Impact Category (multi-select, what was affected):**
People (injury/fatality), Environment (pollution), Asset (vessel/equipment damage), Operations (delay/off-hire), Regulatory (PSC detention, flag state)

---

### Q8. Crew Involved Detail Level
JiBe has a rich **Crew Involved** section that pulls the active crew list and lets you mark each person as Involved / Directly Responsible / Injured / Work Related, with detailed injury fields (Nature of Injury, Source of Injury, Affected Body Areas, First Aid details, Off-Duty hours, Rest Hours last 24h). Your legacy stores this as simple free-text fields (ReportedByFirstName, InjuryDefination). Do you want the JiBe-style detailed crew involvement tracking?

**Answer:** Yes — crew list is available in VIMS DB. **Simplified model confirmed:**

**Per crew member:** Involved (checkbox), Injured (checkbox — only when "Incident with Injury" type).

**When Injured = Yes, expand:** Nature of Injury (dropdown), Body Part Affected (dropdown), First Aid Given (free text), Off-Duty Days (number), Remarks (free text).

**Dropped vs JiBe:** Direct Responsibility, Work Related, Source of Injury, Injury Type, Rest Hours, Rest Hours HC (over-engineering).

**Kept:** External persons section (Name, Role, Company — for port workers, pilots, surveyors).

---

### Q9. Cause Analysis Model
For **cause analysis**, your legacy uses a flat model: CSV of ImmediateCause IDs + CSV of RootCause IDs from lookup tables (11 root cause categories, 40 sub-causes). JiBe uses a **4-factor structured model** (Human Factors, Vessel Factors, Management Factors, Other Factors) with dropdown category + mandatory free-text description per factor, used for BOTH Immediate and Root Cause separately. Which model do you want?

**Answer:** PO wants better than both. Must follow **M-SCAT (Marine Systematic Cause Analysis Technique)** methodology. Both vessel AND office must investigate — vessel can't be excluded from investigation or they won't learn. Office has their own side of investigation but vessel also needs to do root cause analysis. See Q9b/Q9c for detailed discussion.

---

### Q10. Ship vs Office Cause Analysis
Your legacy office-side investigation adds up to **5 root causes + 5 sub-causes** separately from the ship-side report. JiBe doesn't appear to separate ship vs office cause analysis — it's one set of causes per report. Do you want ship and office to have **separate cause analysis fields**, or a single shared cause analysis that both can edit?

**Answer:** Both ship and office investigate. **M-SCAT all 4 levels — vessel fills all 4 levels.** Office uses **Option C (Layered):** office can add to / amend the same M-SCAT chain (with edit history showing who changed what), plus add office-specific remarks. Ship's original entries preserved in audit trail.

**M-SCAT Chain in VIMS:**
- Level 1 — Loss Event (incident description)
- Level 2 — Immediate Causes: Substandard Acts + Substandard Conditions (dropdown from master + description)
- Level 3 — Basic/Root Causes: Personal Factors + Job/System Factors (dropdown from master + description)
- Level 4 — Lack of Control: Inadequate Programs, Inadequate Standards, Inadequate Compliance (dropdown from master + description)

**Vessel fills all 4 levels. Office can amend/add with full edit history.**

---

### Q11. Cost Tracking on Incidents
JiBe has a **Cost Evaluation** section in the incident form. Your legacy Trouble Report tracks costs (LossTime, Estimated, Fixed, CostRepair, MakersGuarantee, ClaimRecoverable, FinalRepair) but the incident form does not. Do you want cost tracking on incidents?

**Answer:** **Option A confirmed** — Office-only cost section, invisible to vessel. Fields: Estimated Cost (USD), Repair Cost, Off-Hire Days, Off-Hire Cost, Insurance Claim (Y/N), Claim Amount, Remarks. Optional, office fills when available.

---

### Q12. Preliminary Notification
Your legacy has a **Preliminary Notification** step — a quick alert sent before the full incident report. JiBe doesn't show this. Do you want to keep a preliminary notification mechanism, or is the initial save/draft sufficient?

**Answer:** **No — not needed.** Initial notification happens via email (outside VIMS). The incident form in VIMS is for the full report and investigation, not the first alert.

---

### Q13. Auto Due Dates
JiBe auto-sets a **30-day due date** from incident date. Your legacy has no due date concept on incidents. Do you want auto-calculated due dates? If so, what's the default period, and is it configurable per severity level?

**Answer:** Yes. **45 days from date of vessel submission** for office-side investigation to be closed. DPA can grant **one extension of 30 days** (max total: 75 days), must provide reasoning. "Due" = office investigation complete and closed, not just vessel side.

---

## Round 3 — Near Miss Specifics

### Q14. Adaptive Form (Low vs Significant)
JiBe's key innovation is the **adaptive form**: Low-risk near misses get a short form (description + immediate cause + preventive action only), High-risk near misses auto-expand to a full investigation form matching the incident form. Your legacy uses the same full form for every near miss. Do you want the adaptive Low/Significant approach?

**Answer:** Yes — **adaptive form confirmed.** Additional rule: **if a near miss is repeated (same/similar event reported before), it should automatically be treated as High risk** regardless of the Severity × Likelihood score.

**Repeat detection:** Option A — same Incident Type on **same vessel** within **last 3 months** = auto-flagged as repeated = auto High risk.

**Quality control concern:** Vessel crew may always mark as minor to avoid extra work.

**Anti-gaming mechanism:** Certain categories **auto-force High risk** regardless of crew's severity/likelihood selection. List is **admin-configurable by DPA** with a built-in starter list:

**Auto-High starter list:**
- Oil Pollution / Spill
- Fire / Explosion
- Fall from height
- Confined space event
- Man overboard situation
- Contact with hazardous substance
- Mooring line snap/failure

**Crew-selectable (matrix applies normally):**
- Slip/Trip (no fall from height), Housekeeping, Minor equipment issue, PPE non-compliance, Procedural shortcut (no injury risk)

DPA can add/remove/adjust categories from the auto-High list at any time.

**Rework mechanism confirmed:** Office can send substandard near miss reports back to vessel for rework (same pattern as VIMS PSC Inspection module). See Q16/Q18b for details.

**Submission flow:** Any crew member can raise a near miss. **HOD reviews and submits to office** (crew member does NOT submit directly to office).

---

### Q15. Near Miss Cause Analysis Model
Should the near miss investigation also follow **M-SCAT** (same as incidents) when the risk level is High/Very High? Or simpler cause analysis?

**Answer:** **Simpler cause analysis for near misses** — M-SCAT is only for incidents. Near misses use a lighter model even at high risk (it's a near miss, not an incident).

**Low risk form:** Description, Immediate Corrective Action, Immediate Cause (simple dropdown + description), Preventive Action.

**High risk form (NOT M-SCAT):** Everything in low risk + Root Cause (simple dropdown + description), Corrective Action, Weather/Voyage details, Equipment details, Lessons Learned.

---

### Q16. Accept/Reject Workflow
Your legacy has an **Accept/Reject workflow** for near misses — office reviews and explicitly accepts or rejects each near miss (615 accepted, 68 rejected, 216 pending). JiBe doesn't show this — it goes straight to Complete → Closed. Do you want the accept/reject step, or is the simpler Complete → Closed flow sufficient?

**Answer:** **Rework mechanism** — not accept/reject but **rework**. If vessel submits a substandard near miss report (low effort, insufficient detail), office can send it back to vessel for rework with comments explaining what's missing. Same pattern as VIMS PSC Inspection module. Purpose: prevent crew from submitting low-quality reports just to meet KPI targets.

**Status flow confirmed:**
```
Open → Submitted (HOD reviews & submits) → Rework (office sends back) → Resubmitted → Accepted → Closed
```
- **No limit** on rework cycles
- **Rework shows as visible status** on grid so everyone sees which reports are sent back
- **Any crew member** can create a near miss
- **HOD reviews and submits** to office (crew doesn't submit directly)
- Office accepts or sends for rework

---

### Q17. Near Miss KPI Targets
Your legacy tracks **monthly near-miss KPI targets** per vessel (via `tbl_KPI`). Is this a feature you want to carry forward — i.e., each vessel has a target number of near misses per month, and the system tracks actual vs target?

**Answer:** Yes — from KSM Management Review 2025: 223 near misses reported fleet-wide (92% accepted), 5/6 vessels met target (East Ayutthaya failed). Incident target: ≤2 per vessel per year.

**Near miss target:** Same for all vessels. **Configurable by DPA yearly** — DPA sets target number for the year, system tracks actual vs target per vessel per month. Dashboard shows compliance.

---

### Q18. Category Reclassification with Audit
Your legacy allows office to **reclassify near miss categories** with an audit trail (`FR_NearMissCatUpdate`, 385 records). Do you want this category-reclassification-with-audit capability?

**Answer:** **Both options (C)** — Office can reclassify themselves OR send back for rework so vessel corrects it. Both actions logged with full audit trail (who changed what, when, why).

**Q18c — HOD Review Logic (same as VIMS PSC CAR workflow):**
- **Rank-based routing:** Crew member creates → routes to HOD based on rank hierarchy
  - Engine room near miss → **Chief Engineer** reviews → **Master** reviews → Office
  - Deck near miss → **Chief Officer** reviews → **Master** reviews → Office
  - General/cross-department → **Master** reviews → Office
- **HOD can rework** back to crew member before submitting to office (vessel-internal quality gate)
- **Office can also rework** back after submission (office quality gate)
- Two rework gates: HOD (internal) + Office (external)

---

## Round 4 — Safety Committee Meeting Specifics

### Q19. Meeting Form Structure
Your legacy meeting form has **10 hardcoded structured sections** (Structured Review, Outstanding Items, Safety Practice, Security, Environment, Health, Crew, Findings×10, Miscellaneous, Office Comments). JiBe has a **different structure**: Attendance, Safety Officer Findings, Incidents & Near Misses (auto-pulled), Topics of Discussion (5 categories), Attachments. Which structure do you prefer, or do you want a hybrid?

**Answer:** PO said topic categories should be **HSSEQ** (Health, Safety, Security, Environment, Quality). Rest of proposed structure accepted. See Q19b for final confirmed structure.

**SSQE Manual Section 9.4 requirements incorporated:**
- Monthly routine + Extraordinary meetings (within 48hrs of injury/casualty, after PSC detention, or office request)
- Agenda per 9.4.3: previous minutes, NCs/incidents/near misses, inspection findings, PSC/audit results, improvements, legislation changes, lessons learnt, crew welfare/MLC/rest hours, SEEMP/cyber/garbage
- Recorded by Safety Officer or on VIMS
- Copy forwarded to DPA, SEQ reviews and sends written response to Master
- Entire complement encouraged to attend (except duty personnel)

---

### Q20. Auto-Pull Incidents/Near Misses into Meeting
JiBe **auto-pulls all incidents and near misses since the last meeting** into the meeting form and shows a **"Days Since Last Injury" counter**. Your legacy doesn't do this. Do you want this auto-population feature?

**Answer:** **Yes** — auto-pull incidents and near misses since last meeting. Show both **"Days Since Last Injury"** counter AND **"Days Since Last Pollution Incident"** counter (environment tracking is a key KSM KPI per management review).

---

### Q21. Dynamic Findings (Child Table)
Your legacy hardcodes **10 findings + 10 corrective measures** as column pairs (findings1-10, correctivemeasure1-10). You already flagged this as a design flaw. Do you want unlimited dynamic findings using a child table, similar to JiBe's approach?

**Answer:** **Yes** — unlimited dynamic entries via child table. No cap on findings or action items per meeting.

---

### Q22. Committee Role Tracking
JiBe has **Committee Role assignment** per crew member (Chairperson, Safety Officer, Officers' Representative, Crew Representative, Member, Attendee). Your legacy just tracks Rank + Name + Present/Absent. Do you want committee role tracking?

**Answer:** Yes — **per SSQE Manual Section 9.4.7**, the safety committee has defined roles:

| Role | Who |
|------|-----|
| **Chairperson** | Master |
| **Safety Officer** | Chief Officer (or 2nd Engineer if nominated) |
| **Member** | Chief Engineer & 2nd Engineer |
| **Officer Representative** | At least 1 Junior Officer |
| **Crew Representative** | Bosun + at least 1 crew member |
| **Attendee** | All other attending crew |

Per 9.4.8: Officers and crew representatives are **elected by ship staff**. Roles should be **pre-configured per vessel** (system remembers who is Safety Officer, who is Crew Rep) and auto-assigns each meeting. Master can update role assignments when crew changes.

---

### Q23. One Meeting Per Month Enforcement
JiBe enforces **one routine meeting per month per vessel** (duplicate prevention). Your legacy allows multiple meetings. Do you want this one-per-month enforcement for routine meetings, with the ability to create Extra Ordinary meetings without limit?

**Answer:** Per SSQE Manual 9.4.2 — **two meeting types:**

**1. Monthly Routine (HSSEQ Meeting):** One per month per vessel, duplicate prevention with warning.

**2. Extraordinary/Additional Safety Meeting:** No limit. **Must be created within 48 hours** when triggered by:
- Any onboard injury or casualty
- Vessel detention after PSC inspection
- Office request in case of serious incident
- Superintendent visit (in conjunction with Master)
- Before undertaking an unusual operation

---

## Round 5 — Workflow & Status

### Q24. Status Lifecycle
JiBe uses a clean **Draft → Open → Complete → Closed** status model across all three modules. Your legacy infers status from field population (no explicit status field on incidents). What is the exact status lifecycle you want for each module? Are they all identical or do some differ?

**Answer:** Incidents follow the **same PSC CAR unified workflow pattern** — including rework and HOD review chain. Corrected name: "Safety Committee Meeting" (not HSSEQ Meeting).

**Incident (mirrors PSC CAR workflow):**
```
Draft → In Progress → Pending CE Review (engine-related) / Pending Master Review (deck-related)
→ Submitted to PIC → PIC Review → Submitted to DPA → Closed
       ↑                                         |
       └──────────── Rework (at any stage) ──────┘
```
- Office (PIC/SSQE/Supt) or DPA can request rework — sends back to vessel for re-editing
- Rework reason mandatory
- Same HOD chain as PSC CAR: 2E → CE → Master (engine) / CO → Master (deck)

**Near Miss:**
```
Open → Submitted (HOD chain) → Rework ↔ Resubmitted → Accepted → Closed
```

**Safety Committee Meeting** (formal SSQE name: "On-Board Safety, Security & Environmental Protection Meeting", per §9.4; briefly called "Safety Committee Meeting" — using brief name as VIMS feature label, matching form SQE S 623 A):
```
Draft → Completed (Master/Safety Officer) → Reviewed (SEQ/DPA) → Closed
```

---

### Q25. Role-Based Status Transitions
Who exactly can transition between each status? Spell out every role and every transition. For example: Can a Chief Officer mark an incident Complete, or only the Master?

**Answer:** Incident reports can only be prepared by the **top 4 officers**: Master, CO, CE, 2E. Regular crew cannot create incident reports (unlike near misses where any crew member can raise one).

**Incident HOD chain (same as PSC CAR):**
- Engine-related incident: **2E** creates → **CE** reviews → **Master** reviews → Office
- Deck-related incident: **CO** creates → **Master** reviews → Office
- Master can create and submit directly to office (no HOD above)
- CE can create engine incidents → **Master** reviews → Office

**Office-side transitions (same as PSC CAR):**
- PIC reviews → can accept or rework back to vessel
- PIC submits to DPA → DPA closes or reworks
- DPA can reopen closed incidents

**Near miss HOD chain (per Q18c):**
- Any crew member creates → HOD based on department (CO for deck, CE for engine) → Master → Office

---

### Q26. Fleet-Wide Circular Distribution
Your legacy has **fleet-wide circular distribution** — office can circulate incident lessons and near-miss lessons to selected vessels as a PDF. JiBe doesn't show this feature. Do you want fleet circulars?

**Answer:** Yes — **connect to existing VIMS Circular module** (already live with office authoring, ship inbox, acknowledgment tracking, reminders, PDF reports). Do NOT build a separate circular system.

**Integration approach:**
- After incident investigation is **Closed by DPA**, office gets a **"Generate Fleet Circular"** action
- This creates a new circular in the existing VIMS Circular module, pre-linked to the incident
- Office writes: what happened, root cause, lessons learned, preventive measures
- Leverages existing Circular infrastructure: vessel targeting, delivery tracking, acknowledgment, PDF export
- Circular auto-pulled into next **Safety Committee Meeting** agenda (per SSQE Manual §9.4.3 requirement)
- Legacy data: 32 incident circulars sent via `Tbl_AccidentCircular`; near miss circulars (`Tbl_NearMissCircular`) never used (0 records)

---

### Q27. Archiving Model
Your legacy has **archiving** — closed incidents can be moved to an archive table. Do you want hard archiving (moved to separate table) or soft archiving (status = Archived, stays in same table with filter)?

**Answer:** **Soft archiving with 3-year retention.** All vessel safety records remain visible in the system for 3 years from closure date. After 3 years, records auto-flagged as "Archived" — hidden from default grid views but accessible via "Show archived" toggle. Nothing is ever deleted. No separate archive table — everything stays in the same table with status-based filtering.

---

## Round 6 — Corrective & Preventive Actions

### Q28. CA/PA Tracking Model
For incidents, are corrective/preventive actions tracked within the incident form itself (embedded fields), or as separate linked records with their own status lifecycle? Do near misses also get formal CA/PA tracking?

**Answer:**
- **Incidents:** CA/PA **within the incident report form** — embedded in the M-SCAT investigation section. Corrective and preventive actions are the natural output of the cause analysis chain. Not separate records like PSC CARs.
- **Near misses:** **No formal CA/PA tracking** within the near miss form. Low-risk has "Immediate Corrective Action" + "Preventive Action" free-text fields (per Q15). High-risk adds "Corrective Action" + "Lessons Learned". These are sufficient.

---

### Q28b. Near Miss Guidance Library (Quality Improvement)
Legacy pain point: 68 rejected near misses (7.2%), 385 category reclassifications by office, crew gaming severity to avoid longer forms. How can VIMS help vessels submit better near misses at the point of entry?

**Answer:** **Guidance prompt library** — admin-configurable library of contextual prompts that appear when crew selects a near miss type. Crew picks from the library (pick-and-choose), and prompts guide what information to include.

**How it works:**
- DPA/admin maintains a **library of guidance prompts** per incident type
- When crew selects a type (e.g., "Slip/Trip"), relevant prompts appear: *"Describe: Where did it happen? What was the surface condition? What footwear was being used? What immediate action was taken?"*
- Prompts are **pick-and-choose from the library** — not mandatory fill-in, but visible coaching
- Admin can **add, remove, and edit** prompts at any time
- Initial setup: system ships with a **starter library** of prompts per incident type (seeded from common near miss patterns)
- Purpose: reduce rework cycles by coaching crew at point of entry, not after rejection

---

## Round 7 — Notifications & Alerts

### Q29. Notification Triggers
What events should trigger automatic notifications, and to whom?

**Answer:** Notify **PIC + DPA + Slack channel** on safety events. Specific triggers:
- New incident submitted by vessel → PIC + DPA + Slack
- New near miss submitted by vessel → PIC + DPA + Slack
- Rework sent back to vessel → vessel Master (Slack + in-app)
- Investigation deadline approaching (45 days) → PIC + DPA + Slack
- Safety Committee Meeting completed → SEQ/DPA + Slack
- Fleet circular generated from incident → target vessels + Slack

---

### Q30. Notification Channels
Do you need email notifications for safety events, or in-app only? Should safety events feed into the same alerting pattern as reporting module?

**Answer:** **Slack notifications** — same pattern as reporting module alerts. No separate email channel for safety events. Slack is the primary notification channel for office-side safety alerts.

---

### Q31. Escalation Rules
If an incident investigation is approaching its 45-day deadline with no action, should the system auto-escalate?

**Answer:** **Flag as overdue on dashboard** — no auto-escalation to higher authority. Dashboard shows overdue investigations prominently (color-coded or flagged). PIC and DPA already receive deadline-approaching notifications via Q29. Visual dashboard flag is sufficient — no automated escalation chain beyond that.

---

## Round 8 — Offline / PWA Behavior

### Q32. Offline Capability
Should incident and near miss forms be available offline (draft while disconnected, auto-sync when connectivity returns)?

**Answer:** **Online only.** No offline capability for safety module V1. All incident reports, near miss reports, and safety committee meetings require active connectivity. Same PWA shell as existing VIMS but no offline form storage or background sync for safety module.

---

### Q33. Offline Conflict Resolution
How should the system handle sync conflicts if crew drafts offline?

**Answer:** **N/A — online only** (per Q32). No conflict resolution needed.

---

### Q34. Safety Committee Meeting Offline
Should the meeting form work offline?

**Answer:** **No — online only** (per Q32). Connectivity is available during scheduled meetings.

---

## Round 9 — Data Migration

### Q35. Migration Scope
Do you want to migrate historical data from legacy eMarineSoft (1,063 incidents, 943 near misses, 677 meetings) into VIMS, or start fresh?

**Answer:** **No migration — system starts fresh.** Clean database. Legacy eMarineSoft remains as read-only archive for historical reference. No data carried over to VIMS.

---

### Q36. Migration Cutoff
**Answer:** **N/A — no migration** (per Q35).

---

### Q37. Open Records at Migration
**Answer:** **N/A — no migration** (per Q35). All open records in legacy must be closed out in legacy before VIMS safety module goes live.

---

## Round 10 — Dashboards & Analytics

### Q38. Office Dashboard — Safety Intelligence Platform
What should the shore-side safety dashboard show beyond basic counts and trends?

**Answer:** Dashboard should be a **decision-making tool** that surfaces patterns before they become accidents. Approved tiered approach:

**Tier 1 — Safety Health Score (V1):**
Composite score per vessel (0-100) combining:
- Near-miss reporting rate (are crew actually reporting?)
- Action item closure rate (are fixes happening on time?)
- Time-to-investigate (how fast are incidents being worked?)
- Repeat root cause count (are the same problems recurring?)
- Safety meeting compliance (are meetings happening with proper content?)
- **KPI tracking** (monthly near-miss targets per vessel — carried from legacy `tbl_KPI` concept)
- **Days without incident** per vessel (preferred over LTIFR)

> **Decision:** KSM prefers KPI targets + days-without-incident over LTIFR/TRCF. No exposure hours tracking needed.

**Tier 2 — Leading Indicators (V1):**
1. **Reporting Culture Monitor** — Heinrich's Triangle ratio (near-misses vs incidents). Drop in ratio = red flag (crew stopped reporting, not safer). Alert when vessel ratio drops significantly vs prior quarter.
2. **Repeat Root Cause Radar** — Same root cause appearing 3+ times across fleet in rolling 6 months = systemic issue flagged for fleet-wide action.

**Tier 3 — Action Effectiveness (V1):**
3. **Corrective Action Aging Pipeline** — Actions at 0-15 / 15-30 / 30-45 / 45+ days. Shows process flow health.

**Tier 4 — Deferred to V2:**
- Fatigue & watch pattern correlation (time-of-occurrence vs watch schedules)
- New joiner risk window (incidents by crew tenure — **crew joining dates available from Crew List module**)
- Port vs sea risk profile
- Fix-vs-recurrence tracker (did same root cause reappear within 6 months after CA closed?)
- Fleet learning score (did circulars actually prevent recurrence on other vessels?)
- Vessel comparison heatmap (vessels × incident types, color = frequency)
- Regulatory readiness (PSC window + open safety items)

**Filters & Drill-down (V1):** Date range, vessel group, vessel, incident type, severity, root cause category. Click any metric to drill into underlying records.

> **Key integration:** Crew tenure data available from existing VIMS Crew List module — no additional input needed on incident form for V2 new-joiner analysis.

---

### Q39. Vessel Dashboard — What does the Master/onboard team see?

**Answer:** Vessel dashboard is **officer-only** (top 4: Master, CO, CE, 2E). Focused on their vessel's safety posture, not fleet-wide data.

**Header Bar:**
- **Days Without Incident** — prominent counter, resets on any recordable incident
- **Near-Miss KPI** — progress ring showing "X of Y target this month"
- **Open Action Items** — count with oldest item age

**Dashboard Widgets:**
1. **My Open Items** — all incidents/near-misses in Draft or In Progress state for this vessel, with age indicator (green <15 days, amber 15-30, red 30+)
2. **Pending My Review** — role-filtered queue: each officer sees only items awaiting their sign-off in the HOD chain (e.g., Master sees items pending Master review, CE sees engine-related items pending CE review)
3. **Recent Fleet Circulars** — latest safety circulars from office. Acknowledgement handling already covered by existing VIMS Circular module (not rebuilt here)
4. **Next Safety Meeting** — countdown to next scheduled monthly meeting + checklist: agenda prepared? previous action items closed?
5. **My Vessel's Trend** — 6-month sparkline: incidents vs near-misses (crew trajectory at a glance)

> **Decision:** Vessel dashboard restricted to top 4 officers only. No crew-level dashboard in V1.
> **Decision:** "Pending My Review" is role-filtered — each officer sees only items relevant to their position in the HOD chain.
> **Decision:** Fleet circular acknowledgement uses existing VIMS Circular module — no duplication in safety module.

---

### Q40. Dashboard Time Periods & Refresh

**Answer:**

**A. Default Time Windows:**
- Safety Health Score — calculated on **rolling 3-year** window
- Near-miss KPI — **monthly per vessel** (carried from legacy concept)
- Days Without Incident — **live counter** from last incident date (no window, resets on new incident)
- Trend charts — default **last 12 months**, expandable to **24 months**

**B. Data Freshness:** **Real-time** — dashboard queries live data, updates as soon as records are saved/submitted. No batch processing or periodic refresh.

**C. Dashboard Access Matrix (confirmed):**

| Role | Office Dashboard | Vessel Dashboard |
|------|-----------------|-----------------|
| DPA | Full fleet | N/A |
| PIC (Superintendent) | Assigned vessel group | N/A |
| Fleet Manager | Full fleet (read-only) | N/A |
| Master | N/A | Own vessel |
| CO / CE / 2E | N/A | Own vessel |

> **Decision:** PIC/DPA can drill into vessel-level data from the office dashboard but do not access the vessel dashboard UI directly — they see the same data through the office drill-down.
> **Decision:** 3-year rolling window for Safety Health Score aligns with the 3-year soft archive policy.

---

## Round 11 — Integration with Other VIMS Modules

### Q41. Integration with Existing VIMS Modules
Which other VIMS modules should the safety module integrate with, and how?

**Answer:**

| Integration | Decision | Detail |
|-------------|----------|--------|
| **PMS / Trouble Reports** | **No integration** | Completely independent records. Incident root cause "equipment failure" does not link to PMS work orders. |
| **Crew List** | **Yes — auto-populate** | Incident/near-miss form auto-populates reporter details (name, rank, department) from active crew list when crew member is selected. Ensures data consistency, avoids manual entry. |
| **Daily Reporting (Voyage)** | **Yes — auto-populate** | Vessel position (lat/long) and port/sea status pulled from daily reporting module. No manual entry of position data. |
| **Purchasing / Stores** | **Yes — link Requisition No.** | Corrective actions can link to a Purchase Requisition number from the Purchase module, enabling follow-up on procurement status for required spares/PPE. |
| **Circulars** | **Yes — existing module** | Fleet circulars use existing VIMS Circular module (confirmed earlier). |
| **Drill / Training** | **No integration** | Not part of current scope. No auto-triggered drills from incidents. |

> **Decision:** No PMS integration — safety and maintenance are independent record streams.
> **Decision:** Crew List + Daily Reporting provide auto-population of reporter details and vessel position — reduces manual entry and improves data quality.
> **Decision:** Purchase module linked via Requisition No. on corrective actions — lightweight reference, not deep integration.

---

### Q42. Integration Data Flow Direction
For each integration, what is the data flow direction and linking mechanism?

**Answer:**

| Integration | Direction | Mechanism |
|-------------|-----------|-----------|
| **Crew List** | **Read-only pull** | Safety module reads crew data (name, rank, department) — never writes back to Crew List |
| **Daily Reporting** | **Read-only pull** | Safety module reads latest vessel position (lat/long) and port/sea status — never writes back |
| **Purchasing** | **Searchable dropdown** | Corrective action form shows searchable dropdown of open requisitions from Purchase module. User selects to create a linked reference. Without the actual record link, follow-up is impossible. |

> **Decision:** Purchasing link must be a searchable dropdown pulling open requisitions — not a free-text Req No. field. Free text cannot create a navigable link to the Purchase record.
> **Decision:** All integrations are read-only from the safety module's perspective — safety consumes data from other modules but never writes to them.

---

### Q43. Integration Failure Handling

**Answer:** **N/A — not applicable.** All VIMS modules (Crew List, Daily Reporting, Purchasing, Circulars) share the same database. Integrations are direct table joins/queries, not external API calls. No failure handling needed — if the database is available, all module data is available.

---

## Round 12 — Regulatory Compliance

### Q44. Regulatory Framework & Flag State Reporting
Which regulations govern this module and how should flag state reporting be handled?

**Answer:**

**Applicable regulations:**
- **ISM Code** §9 (non-conformities, accidents, hazardous occurrences) and §11 (documentation) — primary regulatory driver
- **MLC 2006** — occupational safety/injury reporting obligations
- **RightShip vetting** — applies to bulk carriers; vetting inspectors review safety records
- **No specific classification society requirements** for safety record-keeping identified

**Flag state:**
- Flag varies ship-to-ship — pulled from **vessel particulars** in VIMS (set when vessel is registered in the system). Legacy data already captures `VesselFlag` on incident reports.
- **Flag state casualty reports are done manually outside VIMS** — not auto-generated
- **New fields on incident form:**
  - "Flag State Informed?" — Yes/No toggle
  - If Yes: text box for details + attachment pin for supporting documents
  - If No: text box for reason/notes

> **Decision:** No auto-generated flag state casualty forms. VIMS captures whether flag was informed + supporting docs, but the actual report is prepared manually outside the system.
> **Decision:** RightShip vetting relevant for bulk carriers — safety records must be presentable for vetting inspection. Format/data expectations to be confirmed.

---

### Q45. ISM Code Audit Trail — What must be provable?
What audit trail and verification mechanisms does the module need for ISM compliance and RightShip vetting?

**Answer:**

**1. Timestamp trail:** Standard — every status change logged with who/when. (Implicit in VIMS platform.)

**2. Investigation timeliness:** Covered by the 45-day deadline and overdue dashboard flags (Q38).

**3. Management review:** **Deferred to next phase.** DPA fleet-level review sign-off is not part of V1 safety module.

**4. Corrective action physical verification:** **Same pattern as PSC CAR.** Reuse the existing `psc_physical_verification` model structure:
- Scheduled date
- Visit date
- Visit port
- Verifier (office user ID or crew ID)
- Comments
- Status: OPEN → CLOSED
- Linked to the incident record (instead of CAR)

Physical verification confirms that corrective actions were actually implemented onboard — not just paperwork-closed. This satisfies ISM Code requirement for verification of corrective action effectiveness.

> **Decision:** Management review sign-off deferred to next phase.
> **Decision:** Physical verification for safety incidents mirrors PSC CAR physical verification — same data model, same workflow. Reuse existing pattern.

---

### Q46. Retention & Archival Compliance
How long are records and attachments retained, and how do audits work?

**Answer:**

**1. Record retention:** 3-year soft archive (confirmed earlier). Archived records remain searchable by all office users — no restricted access.

**2. Attachment retention:**
- Database stores **link only** (URL/path reference), not the file itself
- Files stored on **cloud storage**
- **Hard delete after 3 years** — files are permanently removed from cloud storage after 3-year retention period
- DB link remains but file will return 404 after purge

**3. Audit access:**
- ISM/RightShip audits happen **onboard with top 4 officers** (Master, CO, CE, 2E) — **not with DPA at office**
- Officers must be able to pull up and present safety records on the vessel dashboard during audit
- No bulk PDF export needed for auditors — they review records on-screen with the Master
- Vessel dashboard must support this use case: filter by date range, show full incident/near-miss/meeting records with attachments

> **Decision:** Cloud file storage with hard delete at 3 years — DB retains link reference only.
> **Decision:** Audits are onboard, officer-facing. Vessel dashboard is the audit presentation tool — must be able to show filtered records with full detail on demand.
> **Decision:** No batch PDF export for auditors in V1 — on-screen review is sufficient.

---

## Round 13 — Permissions & RBAC (pending — resume here)

### Q47. Role-Based Access Control — Who can do what?
*(Question redrafted 2026-04-16 to incorporate DNV risk-tiered investigator model from SSOT §2B.3 — `VIMS-SAFETY-DNV-MSCAT-ANALYSIS.md` §13. The risk band changes which role *leads* the investigation and consequently who can advance phases. The original 4 sub-questions still need your answers but several are now constrained by the risk band.)*

**Risk-tiered investigator authority (locked at D-DNV-02):**

| Risk Band | Lead Investigator | Initial findings | Closure |
|-----------|------------------|-----------------|---------|
| GREEN — Negligible (near miss / minor) | **Master** | Day 28 | Day 30 |
| YELLOW — Intermediate (hospitalisation / pollution contained / Cat-2 damage) | **DPA (with PIC support)** | Day 14 | Day 30–45 |
| RED — Urgent / Critical (fatality / loss of ship / >100t pollution / IMO Very Serious) | **Managing Director + external expert** | Day 7 | Per-case |

The four open RBAC sub-questions become risk-band aware. Drafted answers below — **please confirm or override each**.

---

#### **Sub-Q1 — Who closes incidents?**

**DNV-informed proposal (please confirm):**
- **GREEN**: PIC may close (Master is lead investigator, PIC accepts at Phase 7)
- **YELLOW**: DPA closes (DPA is lead investigator)
- **RED**: Managing Director closes after extraordinary management review

This means **PIC closes only GREEN incidents** (the lightest band — equivalent to current near-miss closure pattern). DPA always closes YELLOW and above. RED requires MD sign-off.

> **Confirm? Override?** (e.g., "DPA closes everything regardless of band" is also defensible.)

---

#### **Sub-Q2 — SSQE role: separate from PIC/DPA, or same?**

**Three plausible models — pick one:**

**(A) SSQE = DPA team (no separate role)** — SSQE Manager *is* the DPA in the matrix; "SSQE" is a label, not a permission set. Simplest.

**(B) SSQE = independent third reviewer** — SSQE can review/comment on incidents from any vessel, can override classification, but cannot close. Acts as the system-wide quality gate. **Adds a dedicated phase between Phase 6 and 7.**

**(C) SSQE = subject-matter expert pool, no workflow authority** — SSQE users tagged on incidents matching their expertise (e.g., "tanker safety specialist"); can comment, propose root causes, but PIC/DPA still own decisions.

> **DNV bias guard #5 (blame-fixation hard block)** requires senior review when an investigation has only Personal Factor causes. Whoever performs that override is functionally the SSQE role. Model (B) makes this explicit; (A) folds it into DPA.

> **Which model?**

---

#### **Sub-Q3 — Fleet Manager: read-only, or can they comment/flag?**

**DNV-informed proposal (please confirm):**
- Read-only on incident *content*
- Can **flag** an incident for DPA attention (one-click, no edit)
- Can **add a "Fleet Manager Remark" comment** visible to PIC/DPA but separate from the formal investigation record (does not become part of audit trail for ISM purposes)

This keeps the ISM audit chain pure (investigator → DPA → MD) while letting Fleet Manager surface concerns operationally.

> **Confirm? Override?**

---

#### **Sub-Q4 — Who can host safety meetings?**

**DNV-neutral question** — DNV doesn't address this. Final operational rule revised 2026-05-18: Master and CO can both host SCM. The create screen exposes a `meeting_type` dropdown so either role may create Regular or Ad-Hoc SCM. Master remains the final SCM sign-off authority.

---

### Q47 — Updated Permission Matrix (DNV-informed)

**Ship-Side Roles** (no change from prior draft except meeting-creation row):

| Action | Master | CO | CE | 2E |
|--------|--------|----|----|-----|
| Create incident report | Yes | Yes (deck) | Yes (engine) | Yes (engine) |
| Create near-miss report | Yes | Yes | Yes | Yes |
| Edit own draft | Yes | Yes | Yes | Yes |
| Submit (start HOD chain) | Yes | Yes | Yes | Yes |
| Review/approve in HOD chain | Yes (final) | Yes (deck HOD) | Yes (engine HOD) | Yes (engine initiator) |
| **Lead investigation (GREEN-band)** | Yes | — | — | — |
| Lead investigation (YELLOW/RED) | — | — | — | — |
| Create safety meeting | Yes | **Sub-Q4** | No | No |
| View all vessel records | Yes | Yes | Yes | Yes |
| View vessel dashboard | Yes | Yes | Yes | Yes |

**Office-Side Roles** (DNV risk-tiered):

| Action | PIC (Superintendent) | DPA | Fleet Manager | SSQE | Managing Director |
|--------|---------------------|-----|---------------|------|------|
| View records | Assigned vessels | All | All (read-only) | **Sub-Q2** | All |
| Comment / flag for attention | Assigned vessels | All | **Sub-Q3** | **Sub-Q2** | All |
| **Lead investigation (YELLOW)** | Support DPA | Yes | No | **Sub-Q2** | No |
| **Lead investigation (RED)** | Support MD | Support MD | No | **Sub-Q2** | Yes |
| Review/accept/reject incident | Yes | Yes | No | **Sub-Q2** | Yes (RED) |
| Rework incident (loop-back to Phase 3) | Yes | Yes | No | **Sub-Q2** | Yes (RED) |
| **Close GREEN incident** | **Sub-Q1: Yes (proposed)** | Yes | No | No | Yes |
| **Close YELLOW incident** | No | Yes | No | No | Yes |
| **Close RED incident** | No | No | No | No | **Sub-Q1: Yes (proposed)** |
| Add M-SCAT root-cause classification | Yes | Yes | No | **Sub-Q2** | Yes (RED) |
| Override blame-fixation guard | No | Yes | No | **Sub-Q2 model B: Yes** | Yes |
| Send fleet circular | Yes | Yes | No | **Sub-Q2** | Yes |
| Physical verification scheduling | Yes | Yes | No | No | No |
| Maintain M-SCAT taxonomy / guidance library | No | No | No | **Sub-Q2 (typically yes)** | No |
| MSC-MEPC.3 PDF export | Yes | Yes | View only | View only | Yes |
| View office dashboard | Assigned vessels | Full fleet | Full fleet (RO) | Full fleet | Full fleet |
| View Heinrich Ratio fleet panel | Assigned vessels | Full fleet | Full fleet | Full fleet | Full fleet |

> **Action requested:** answer Sub-Q1 / Sub-Q2 / Sub-Q3 / Sub-Q4 above. Once locked, I'll redraw the matrix as final and proceed to Q48 (admin/config permissions: who maintains M-SCAT taxonomy, recommendation themes, guidance library, case studies).

---

### Q47 — User Answers (2026-04-16, Session 4)

**Q47.1 — Closure authority by band:**
- GREEN: Master investigates, **PIC (Vessel Supt) closes**
- YELLOW: **Master + PIC jointly investigate, DPA closes**
- RED: **DPA + External expert investigate, Fleet Manager closes**

> **Decision:** Closure authority escalates with risk band — PIC/DPA/FM. FM holds the highest closure authority for RED incidents (not MD as originally proposed). YELLOW is a joint ship-office investigation (Master + PIC), DPA is the closer.

**Q47.2 — SSQE role: Option A** — SSQE = DPA team label, no separate permissions in the matrix. "SSQE Manager" is a job title for DPA-team members; RBAC treats them as DPA.

> **Decision:** SSQE folds into DPA for permission purposes. No separate SSQE column in the final matrix.

**Q47.3 — Fleet Manager baseline scope: Option C** — Read + flag + comment (comments visible to PIC/DPA but **kept separate from the formal investigation record** so ISM audit trail stays pure).

> **Decision:** FM baseline is advisory (read + flag + comment outside formal record). FM gets elevated authority only for RED-band: closure + blame-fixation override.

**Q47.4 — SCM host authority: revised 2026-05-18** — CO or Master can create/host the meeting record and choose `meeting_type` (`REGULAR` or `AD_HOC`). Master remains the final signer at Phase "Completed".

> **Decision:** Master and CO can create safety committee meeting records. Master remains the final closure/sign-off authority.

**Q47.5 — Blame-fixation hard-block override: Option B** — DPA overrides for GREEN and YELLOW; Fleet Manager overrides for RED. Consistent with the band-tiered closure model.

> **Decision:** Override authority for the Personal-Factors-only hard block escalates with band: DPA (GREEN/YELLOW), FM (RED).

**Q47.6 — Cross-vessel / cross-fleet visibility:**
- 1 (PIC cross-vessel): **Option C** — PIC gets read-only on non-managed vessels and **can borrow lessons-learned into their own vessel circulars**
- 2 (Master cross-fleet): **Option B** — Master gets read-only view of closed incidents fleet-wide for learning
- 3 (Vetting/inspector access): **Options A + C** — Master drives on-screen presentation **AND** can generate a date-filtered PDF export for the auditor's records. *(This updates Q46 decision: Q46 said "no batch PDF export for auditors in V1, on-screen sufficient" — now expanded to "on-screen + PDF export for auditors".)*

> **Decision Q47.6.1:** PIC read-only + borrow-lessons on non-managed vessels.
> **Decision Q47.6.2:** Master read-only on closed incidents fleet-wide.
> **Decision Q47.6.3:** Vetting/inspector access = Master-driven on-screen + PDF export (updates Q46 — adds PDF export capability).

---

### Q47 — FINAL Permission Matrix (locked 2026-04-16)

**Ship-Side Roles:**

| Action | Master | CO | CE | 2E | Other ranks |
|--------|--------|----|----|-----|-------------|
| Create incident report | Yes | Yes (deck) | Yes (engine) | Yes (engine) | No |
| Create near-miss report | Yes | Yes | Yes | Yes | **Yes (any rank — Q48.4)** |
| Create safety meeting | Yes | **Yes (prepares minutes)** | No | No | No |
| Chair safety meeting (sign off) | Yes | No | No | No | No |
| Edit own draft | Yes | Yes | Yes | Yes | Yes (own near miss) |
| Submit (start HOD chain) | Yes | Yes | Yes | Yes | Yes (own near miss, Master reviews) |
| Review/approve in HOD chain | Yes (final) | Yes (deck HOD) | Yes (engine HOD) | Yes (engine initiator) | — |
| **Lead investigation GREEN-band** | Yes | — | — | — | — |
| **Joint investigation YELLOW-band** (with PIC) | Yes | — | — | — | — |
| View own vessel records | Yes | Yes | Yes | Yes | Own reports only |
| **View closed incidents fleet-wide (read-only for learning)** | **Yes** | No | No | No | No |
| View vessel dashboard | Yes | Yes | Yes | Yes | Limited |

**Office-Side Roles:** (SSQE folded into DPA per Q47.2 Option A)

| Action | PIC (Vessel Supt) | DPA | Fleet Manager |
|--------|------------------|-----|---------------|
| View records — assigned vessels | Full | — | — |
| View records — non-assigned vessels | **Read-only (Q47.6.1)** | Full (all fleet) | Full (all fleet, read-only baseline) |
| View records — cross-fleet | Read-only (Q47.6.1) | Full | Full |
| Comment on assigned vessels | Yes | Yes | Flag + comment outside formal record (Q47.3) |
| Flag for DPA attention | Yes | — | Yes (any vessel, Q47.3) |
| **Close GREEN incident** | **Yes** | Yes | Yes (oversight) |
| **Close YELLOW incident** | No | **Yes** | Yes (oversight) |
| **Close RED incident** | No | No | **Yes (Q47.1)** |
| Joint investigation YELLOW-band (with Master) | **Yes (Q47.1)** | — (DPA closes after Master + PIC investigate) | — |
| Lead investigation RED-band (with External expert) | — | **Yes** | — |
| Review/accept/reject incident | Yes | Yes | No (flag only) |
| Rework incident (loop-back Phase 6→3) | Yes | Yes | No |
| Add M-SCAT root-cause classification | Yes | Yes | No |
| **Override blame-fixation hard block (GREEN/YELLOW)** | No | **Yes (Q47.5)** | No |
| **Override blame-fixation hard block (RED)** | No | No | **Yes (Q47.5)** |
| Send fleet circular (Lessons Learned auto-draft) | Uses existing VIMS Circular module (Q48.5) | Uses existing VIMS Circular module | — |
| **Borrow lessons from non-managed vessels into own circulars** | **Yes (Q47.6.1)** | — (already sees all) | — |
| Physical verification scheduling | Yes | Yes | No |
| MSC-MEPC.3 PDF export | Yes | Yes | View only |
| **Auditor PDF export (vetting/PSC/class/flag state)** | Master drives, generates from vessel dashboard (Q47.6.3) | Yes | View only |
| View office dashboard | Assigned vessels | Full fleet | Full fleet (read-only baseline) |
| View Heinrich Ratio fleet panel | Assigned vessels | Full fleet | Full fleet |

**Admin/Config Permissions (Q48 — answered 2026-04-16):**

| Action | PIC | DPA | Fleet Manager |
|--------|-----|-----|---------------|
| **Maintain M-SCAT cause taxonomy** (Q48.1) | No | **Yes (exclusive)** | No |
| **Maintain Guidance Library** (near-miss prompts, Q48.2 D) | **Yes** | Yes | No |
| **Maintain Case Study Library** (Q48.2 D — stricter) | No | **Yes (exclusive)** | No |
| **Maintain Recommendation Themes** (Q48.3) | No | **Yes (exclusive)** | No |
| **Fleet Circular approval chain** (Q48.5) | Reuses existing VIMS Circular module approval chain — no new Safety-specific rules | | |

---

### Round 15 — Edge Cases (CLOSED 2026-04-16, Session 4)

**Q49.1 — Multi-vessel incidents: Option B** — Two independent records, linked by "related incident" field. Each vessel owns its own investigation, cross-linked for visibility. Each closes independently.
> **D-EDGE-01:** Multi-vessel incidents = 2 linked records, not 1 shared.

**Q49.2 — Non-crew injuries (pilot/contractor/stevedore): Option B** — Structured "External Party" picklist (Pilot / Shipyard Worker / Stevedore / Contractor / Passenger / Port Agent / Other) + free-text name/company. Linked to incident, not crew table.
> **D-EDGE-02:** External Party picklist for non-crew injured persons.

**Q49.3 — Re-opening closed incidents: Option B** — DPA re-opens GREEN/YELLOW; Fleet Manager re-opens RED. Returns to Phase 5 with audit-log entry capturing reason. Band-tiered, consistent with closure authority.
> **D-EDGE-03:** Re-open authority follows closure authority by band.

**Q49.4 — Medical/fitness-for-duty data sensitivity: Option A** — Same as rest of incident; no separate medical-data permission. *(Flagged: GDPR/UK DPA/Singapore PDPA exposure; user accepts risk for V1.)*
> **D-EDGE-04:** Medical/D&A data uses standard incident permissions; no field-level restriction in V1.

**Q49.5 — GDPR-style deletion requests: Option A** — Request denied; ISM compliance over-rides personal-data rights. Crew informed at hiring of statutory retention. *(Defensible but PR-risky in EU jurisdictions.)*
> **D-EDGE-05:** GDPR/right-to-be-forgotten denied; ISM regulatory obligation prevails.

**Q49.6 — Phase 8 effectiveness verification:** Use the existing PSC PV pattern — `psc_physical_verification` model (Scheduled date / Visit date / Visit port / Verifier / Comments / OPEN→CLOSED). Collapses Phase 7+8 into single physical-verification act; no separate 90/180/365-day effectiveness review.
> **D-EDGE-06:** Phase 8 = PSC PV pattern reuse. No separate time-windowed effectiveness re-review in V1.

**Q49.7 — Near miss ↔ Incident reclassification: Option C** — Close + create new with reference. Original closes as "Superseded"; new record manually created with link to old. Keeps each record-type pure.
> **D-EDGE-07:** Reclassification = supersede-and-create-new, not in-place mutation.

**Q49.8 — Mandatory fields & Draft mode: A + D hybrid** — Draft mode allowed at any phase with partial data; **at each phase Submit, all fields required for that phase must be complete** (full validation per gate). No partial submissions.
> **D-EDGE-08:** Draft mode = always saveable with partial data. Submit = full per-phase validation.

**Q49.9 — Notifications beyond creation: Option B** — Three triggers:
- Creation → PIC + DPA + Slack channel (already locked)
- Overdue at 80% of risk-band deadline → PIC + DPA email
- Rework requested → reporter + HOD chain
> **D-EDGE-09:** Notifications = Creation + Overdue (80% threshold) + Rework. No per-phase-transition pings.

**Q49.10 — Audit trail & edit rights: Option B** — Edits allowed with full history. Every change creates a `safety_field_history` row (`field_name | old_value | new_value | changed_by | changed_at | reason`). Viewable as a diff on the incident detail screen.
> **D-EDGE-10:** Full field-level edit history, viewable as diff. No append-only restriction.

**Q49.11 — Form schema versioning: Option A** — Grandfathered. Old incidents keep their original schema until closed. `schema_version` stored per incident. New incidents use new schema.
> **D-EDGE-11:** Schema versioning grandfathered per `safety_incident.schema_version`.

**Q49.12 — P&I / insurance claim linkage: Option C** — Out of scope. Claim handling lives in finance/commercial systems; Safety module stays purely operational. May reference "See company claims register" in comments.
> **D-EDGE-12:** Insurance claim data not modelled in Safety; commercial system owns it.

---

### Round 14 — PDF Export & Reporting (CLOSED 2026-04-16, Session 4)

Already locked: MSC-MEPC.3/Circ.4 auto-export at D-DNV-12; Fleet Circular reuses existing VIMS Circular module per D-CFG-04.

**Q50.1 — Internal Incident Report PDF: Option B** — Formal report template:
- Cover page (logo, vessel name, incident no, severity, date)
- Executive summary auto-populated from Lessons Learned
- Full sections (Incident Details / Investigation / Causes / Recommendations / CA tracking / Verification)
- Signature block at end: Master + DPA + (FM for RED-band)
- Page numbering, header/footer with confidentiality marking
> **D-PDF-01:** Internal incident PDF = formal company template (cover + summary + sections + signatures).

**Q50.2 — Auditor leave-behind PDF package: Option D + (iii)** — Configurable at export time. Master ticks record types (Incidents / Near Misses / Safety Meetings) and date range; system generates ZIP with PDF (text/tables only) + `attachments/` subfolder containing all referenced files.
> **D-PDF-02:** Auditor PDF package = configurable scope at export, attachments in separate `attachments/` folder inside the ZIP.

**Q50.3 — Near Miss + Safety Meeting PDF formats:**
- Near Miss: **Option B** — Distinct lighter template. 1–2 page format: what-happened + suggestion + immediate action. No investigation phases, no cause-tree details.
- Safety Meeting: **Option D** — Same as legacy `vw_GetSCM_Master` 10-section structure verbatim, so historical and new minutes look consistent.
> **D-PDF-03a:** Near miss PDF = lighter purpose-built 1–2 page template.
> **D-PDF-03b:** Safety meeting PDF = legacy 10-section layout preserved.

---

## Round 16 — Safety Officer Inspection (added 2026-04-16, 4th V1 sub-feature)

**Context:** User added a new sub-feature late in Session 4 based on the existing KSM SQE S 608 Safety Officer Inspection Checklist, SSQE Manual §4.5, and COSWP 2026 Ch 13 (Safety Officials). Goal: digitise and modernise the Safety Officer Inspection process, tightly coupled to the Safety Committee Meeting.

**Q-SOI-1 — Scope: Option A** — Add SOI as a distinct 4th V1 sub-feature (own data model, own UI, own permission set, own PDF output). SCM auto-pulls findings.
> **D-SOI-01**

**Q-SOI-2 — Safety Officer role assignment: Option A** — Chief Officer is the designated Safety Officer; Master may toggle 2nd Engineer as alternate at the vessel-settings level. Locked to CO/2E pattern only (no other-rank variants).
> **D-SOI-02**

**Q-SOI-3 — Stop-work authority: Option C** — Out of V1 scope. Informal verbal escalation to Master continues; revisit as V2 feature.
> **D-SOI-03**

**Q-SOI-4 — Inspection cadence: Option B + D-38 zone-tracked model.** Target-based cadence with 90-day hard ceiling per applicable area (SCM hard-block on overdue). 80-day amber warning. Target 1/3 per month per SSQE §4.5.2 but Safety Officer chooses which specific areas each cycle. User pointed to D-38 (Anglo-Eastern SOI form) showing per-zone last-inspected / due-inspected tracking matrix.
> **D-SOI-04**

**Q-SOI-5 — Checklist taxonomy:** User answer — "versions with a provision to select vessel it is applicable to". Interpretation: DPA maintains versioned checklist templates; each vessel assigned an applicable version at onboarding; reassignable with DPA approval. Historical inspections grandfathered on their schema version.
> **D-SOI-05**

**Q-SOI-6 — Finding escalation rules: Option D** — No auto-escalation to Near Miss / Incident / PMS Defect. All findings stay within SOI and are followed up via the SCM. If escalation is needed, Safety Officer files the separate record manually with cross-reference.
> **D-SOI-06**

**Q-SOI-7 — Finding closure authority:** User answer — "Can close within the inspection report and same is picked and reflected in SMC, before any finding is closed Master needs to review and approve". Interpretation: Safety Officer marks `pending_closure` inside the inspection report; Master review + approval mandatory before `closed`; closure auto-reflects into next SCM under Closed Items block.
> **D-SOI-07**

**Q-SOI-8 — Cross-functional assistant: Option A + CMS integration.** Hard-enforced; both name and department pulled from Crew Management System (not free text); system blocks submit if assistant's department = Safety Officer's department.
> **D-SOI-08**

**Q-SOI-9 — Training mode / crew rotation tracking: Option A** — Formal tracking of up to 3 crew trainees per inspection by CrewId; system computes per-crew "inspections accompanied" counter + per-vessel "crew rotation coverage %" over last 12 months; surfaced on Crew dashboard and SCM analytics.
> **D-SOI-09**

**Q-SOI-10 — PDF output format:** User answer — "CO can download the checklist, but finding needs to be updated in the system to make the inspection close. [QEOHS-VSL-HSSE-10] is our present format which we can improve". Reference image: First Oil & Gas Services QEOHS-VSL-HSSE-10 2-page layout (Schedule table + Section 2 Inspection with 4 thematic categories + Section 3 Observations + Signatures). User later clarified the canonical present format is KSM's own SQE S 608 Excel (11 detailed sections).
> Interpretation: hybrid digital-first workflow — downloadable blank checklist PDF for field use + mandatory digital findings entry to close + auto-generated completed PDF. Layout improves on the present format with M-SCAT cause tags on findings and audit-trail footer.
> **D-SOI-10**

**Q-SOI-11 — Retention: Option A** — Same as other safety records (3-year soft archive; hard-delete attachments at 3 years).
> **D-SOI-11**

**Q-SOI-12 — Zone template: Option C** — Fleet-wide standard, same coding on every vessel. Non-applicable areas flagged `applicable=false` at onboarding.
> **D-SOI-12**

**Q-SOI-13 — V1 inspection area scope:** User clarified by pointing to SQE S 608 as the present canonical KSM format → **Option C implicitly confirmed** (11 inspection areas matching SQE S 608 sections baseline).
> **D-SOI-13**

**Q-SOI-14 — SCM auto-feed rules: Option C** — Split model. Open findings populate Safety Observations for the Month table (for discussion at the meeting). Closed-Since-Last-SCM findings appear in a new "Closed Items" summary block at the top of the SCM (for record, no discussion needed).
> **D-SOI-14**

**Q-SOI-15 — SOI RBAC: Option A** — Inherits standard Safety module pattern. No new permission patterns invented. CO/2/E create & edit; Master approves closure; DPA maintains reference data.
> **D-SOI-15**

**Q-SOI-16 — Checklist content finalisation: Option B** — Keep SQE S 608's 11 area-based sections unchanged + add a 12th cross-cutting section with ~12 industry-standard items (PPE matrix, LOTO, IMO signs, PTW, enclosed-space, hot-work, work-at-height, heat-stress, supervision adequacy, two open prompts for improvements + suggestions, previous-findings rectification check). Sourced from COSWP Ch 13 + D-38 + QEOHS-VSL-HSSE-10.
> **D-SOI-16**

> **Note:** D-SOI-10 (revised 2026-04-16) — user clarified the paper-first workflow. System generates dynamic checklist (PDF or Excel) from selected areas + Section 12; download flips inspection to "In Progress"; Safety Officer registers only findings + uploads scan; submission stamps areas as inspected (resets 90-day counter) + feeds SCM. No per-item response table in the DB.

---

## Round 17 — Gap-Analysis Resolution Sweep — Clusters A, B, C (CLOSED 2026-04-17, Session 5)

*Triggered by `VIMS-SAFETY-GAP-ANALYSIS.md` (2026-04-17). 5 parallel gap-hunter agents surfaced 125 raw gaps → 85 deduped (27 HIGH, 44 MED, 14 LOW). Clusters A–C closed in this round; 14 new decisions locked.*

### Cluster A — People / Role Continuity

**Q-GAP-A1.** Acting DPA for YELLOW closure when DPA on leave? → **Option C — deadline auto-pauses.** No Acting-DPA concept. **D-GAP-A1**
**Q-GAP-A2.** PIC transfer mid-YELLOW — who owns? → **Option B — original PIC retains remotely.** **D-GAP-A2**
**Q-GAP-A3.** Master rotation mid-cycle (SCM chair, GREEN closer, SOI approver)? → **Rank persists, person may change.** VIMS-wide invariant. New Master on rotation inherits all pending duties. **D-GAP-A3**
**Q-GAP-A4.** CO medevac mid-SOI? → **Same rule — CO rank always onboard; new CO inherits.** **D-GAP-A4**
**Q-GAP-A5.** Self-report conflict (reporter = injured / PIC)? → **Option A — system flags + mandates different approver. Vessel side: Master. Office side: DPA.** **D-GAP-A5**
**Q-GAP-A6.** Master / CO is subject of incident? → **Role stays as-is. No stand-in.** Relies on DPA oversight + audit trail per D-EDGE-10. **D-GAP-A6**

### Cluster B — Authority Dead-Ends

**Q-GAP-B1.** Both DPA and FM refuse blame-fixation override on RED? → **Option B — rework. Investigation goes back to Phase 3.** No MD escalation. Loop until override granted or framing changes. **D-GAP-B1**
**Q-GAP-B2.** FM unavailable for RED closure — max wait / deputy? → **No deputy FM.** RED closure runs within designed timeline; existing VIMS timeline-extension procedure is the only extension path. **D-GAP-B2**
**Q-GAP-B3.** Phase 5 → Phase 3 loop-back max iterations? → **Option B — no cap.** DPA judgement; every loop-back logged with reason; excessive looping surfaces via dashboard metric (no hard block). **D-GAP-B3**

### Cluster C — Data Foundations

**Q-GAP-C1.** Incident number format + assignment timing? → **Option A.** Format = `{VslCode}/{YYYY}/{NNN}` per-vessel-per-year. **Temp draft series** (e.g. `DRAFT-EBK/2026/T042`) during WIP; **final number assigned at submit-to-office.** Gap-free final sequence. **D-GAP-C1**
**Q-GAP-C2.** M-SCAT taxonomy seed source? → **Option B — extract NOW from DNV MSCAT 8.2 PDF** and commit structured CSV to repo at `safety-reference-data/mscat_taxonomy.csv`. Seeded at install. **D-GAP-C2**
**Q-GAP-C3.** SOI 292-item seed source? → **Option A — extract NOW from SQE S 608 Excel** to `safety-reference-data/soi_checklist_v1.csv`. Columns: area_id, area_name, item_number, description, tier. Seeded at install. **D-GAP-C3**
**Q-GAP-C4.** Schema / taxonomy drift within VIMS over time? → **Option A — old records locked on original taxonomy version** (true grandfather). New codes only apply forward. No retroactive remapping. Legacy eMarineSoft stays separate read-only. **D-GAP-C4**
**Q-GAP-C5.** PII / medical / D&A protection in DB? → **Option D — no extra protection.** Standard role permissions per D-EDGE-04 are sufficient. GDPR risk remains flagged. **D-GAP-C5**

---

## Round 18 — Gap-Analysis Resolution Sweep — Clusters D, E, F (CLOSED 2026-04-17, Session 5)

*Batch 2 of the gap-analysis sweep. User confirmed all options (mix of explicit choices and "recommend best stable" — recommendations accepted). E4 revision supersedes scan-upload step in D-SOI-10.*

### Cluster D — Digital Signatures & Audit Tamper-Evidence

**Q-GAP-D1.** E-sig mechanism on PDFs and records? → **Option D — hybrid.** Typed name + timestamp + device fingerprint in UI; wet-signed scan of PDF accepted as attachment for flag-state / auditor hand-off. No PKI / UETA required in V1. **D-GAP-D1**
**Q-GAP-D2.** Audit-trail tamper-evidence? → **Option C — no crypto in V1.** Rely on DB/table access control + `safety_field_history` append-only + backups + access log on audit table. Hash chains revisitable in V2. **D-GAP-D2**

### Cluster E — SOI Paper-First Operational Gaps

**Q-GAP-E1.** Checklist download idempotency? → **Option A — no-op on repeat download.** SO reprints freely. **D-GAP-E1**
**Q-GAP-E2.** Partial submission? → **Option A — allowed.** Per-area 90-day reset; remaining areas stay "Downloaded". **D-GAP-E2**
**Q-GAP-E3.** Lost/damaged paper? → **Option A — re-download + re-conduct.** Loss logged in inspection notes. **D-GAP-E3**
**Q-GAP-E4.** Scan upload strategy? → **User override: NO scan upload required.** Paper permanently filed in ship's onboard SMS filing system; digital record linked to paper via **unique checklist ID** printed on the generated document. Revises D-SOI-10. **D-GAP-E4**
**Q-GAP-E5.** Paper ↔ digital count mismatch audit? → **Option A — no mechanism.** SO judgment; ship filing available for PSC/auditor on-demand review. **D-GAP-E5**
**Q-GAP-E6.** Life-threat escalation during V1 inspection? → **Option A — SO creates parallel Incident / Near Miss via existing flow.** SOI continues after hazard controlled. **D-GAP-E6**
**Q-GAP-E7.** Default finding assignee? → **Option B — SO themselves.** Master re-assigns at approval. **D-GAP-E7**

### Cluster F — Online-Only Fragility & Notifications

**Q-GAP-F1.** Connectivity drop mid-entry? → **Auto-save every 30 seconds** to browser local storage. On reconnect / reload, resume from last saved state. **D-GAP-F1**
**Q-GAP-F2.** Slack webhook failure? → **Option C — in-app only.** Slack best-effort, no email fallback. **D-GAP-F2**
**Q-GAP-F3.** Escalation on 80% overdue? → **Option D — dashboard flag only.** No auto-escalation. Timeline-extension procedure from D-GAP-B2 handles approved overruns. **D-GAP-F3**
**Q-GAP-F4.** Monitoring / SLA / observability? → **Option C — inherit from VIMS platform.** Module supplements if platform lacks: Slack failure alert (RED-band) / CMS-PMS integration failure alert / `safety_field_history` access log. **D-GAP-F4**

---

## Round 19 — Gap-Analysis Resolution Sweep — Clusters G, H, I, J (CLOSED 2026-04-17, Session 5)

*Batch 3 of the gap-analysis sweep. Two user corrections invalidated assumed gaps: I1 removed the Safety↔PMS auto-integration, I2 removed CMS staleness concern. 8 decisions locked.*

### Cluster G — Regulatory & Retention

**Q-GAP-G1.** IMO flag-state deadline auto-calc? → **Option C — no tracking.** DPA handles manually out-of-band; MSC-MEPC.3 PDF auto-fill already supports them via D-DNV-12. **D-GAP-G1**
**Q-GAP-G2.** Legal hold vs 3-year hard-delete? → **Option B — no legal-hold feature.** 3-year hard-delete runs on schedule. DPA exports records externally before cutoff when case open. **D-GAP-G2**
**Q-GAP-G3.** Backup / DR? → **Inherit from VIMS platform.** No module-specific backup. Verify platform covers Safety tables at deploy time. **D-GAP-G3**

### Cluster H — Performance

**Q-GAP-H1.** Concurrent user load target? → **Option C — inherit VIMS platform baseline.** No module-level target. **D-GAP-H1**
**Q-GAP-H2.** Repeat root-cause definition? → **Option C — both fleet-level and vessel-level radars.** Superseded / reclassified incidents do NOT count. **D-GAP-H2**

### Cluster I — Cross-Module Hard-Blocks

**Q-GAP-I1.** PMS lookup offline fallback? → **User clarification: PMS is independent, separate login.** No in-VIMS PMS lookup for M-SCAT cause 12. Investigator cross-references manually. **Removes Safety↔PMS integration for V1.** **D-GAP-I1**
**Q-GAP-I2.** CMS crew-data staleness? → **User clarification: same DB, no sync.** SOI assistant lookup is a live table join on `ksm_cms_live`. No staleness possible. Residual case (new joiner not yet in CMS) = HR process issue, handled via D-SOI-08 hard-enforce — Master selects different assistant or defers inspection. **D-GAP-I2**

### Cluster J — Near-Miss Reporter Anonymity

**Q-GAP-J1.** Reporter identity visibility? → **Option B — hidden from Master/HOD; visible only to DPA + FM** (and reporter themselves). Name stored in DB, UI-masked outside DPA/FM view. Reporting-culture-protective. **D-GAP-J1**

---

## Round 20 — Gap-Analysis Resolution Sweep — MED-severity items (CLOSED 2026-04-17, Session 5)

*Batch 4 of the gap-analysis sweep. 44 MED-severity gaps triaged: **11 auto-resolved** by locked principles (A3/A4 rank-persists, F3 dashboard-flag-only, E4 no-scan-upload, I1 PMS-decoupled, H1 platform-inherited, D-RBAC-04 baseline, D-EDGE-07, C4 no-legacy-migration), **11 deferred** to docsuite/BACKEND_STRUCTURE as build-time specs, **38 genuine decisions** presented to user + confirmed, plus **2 bonus decisions** (Ad-Hoc SCM provision, SOI Compliance % rename). Total new locked this round: **40**.*

### Sub-batch 4a — Workflow / Policy (M1–M15)

- **M1** Attachment orphan cleanup → Hard-delete on delink. `safety_field_history` logs the delink. **D-GAP-M01**
- **M2** Re-upload same filename → Replace in place + audit log. **D-GAP-M02**
- **M3** CA closure vs PV → CA may close with PV open (PSC CAR pattern). **D-GAP-M03**
- **M4** Snapshot / revert → Field-level diff per D-EDGE-10 is sufficient. **D-GAP-M04**
- **M5** Template reassign mid-inspection → Freeze in-flight on old version. **D-GAP-M05**
- **M6** FM RED closure authority → Full edit (user override of recommendation). **D-GAP-M06**
- **M7** Multi-vessel linked closure → Each vessel closes independently. **D-GAP-M07**
- **M8** PIC borrow-lessons → Anonymize vessel + crew names. **D-GAP-M08**
- **M9** Position-time tolerance → ±12h, user may edit with newer position. **D-GAP-M09**
- **M10** Daily Report missing → Accept manual entry + DPA-review flag. **D-GAP-M10**
- **M11** WRH missing for SCM attendee → Warn don't block. **D-GAP-M11**
- **M12** CA ↔ Purchase Req → Hard FK. **D-GAP-M12**
- **M13** Class society notification → No toggle; DPA out-of-band. **D-GAP-M13**
- **M14** MLC injury auto-flag → Flag on incident; no cross-module notification. **D-GAP-M14**
- **M15** Paper checklist signatures → SO + Assistant on paper; Master digital. **D-GAP-M15**

### Sub-batch 4b — SOI / SCM operational (M16–M24 + bonus)

- **M16** HIGH finding → Prompt SO to create incident (nudge, no auto). **D-GAP-M16**
- **M17** Repeat finding → Badge + dashboard metric both. **D-GAP-M17**
- **M18** Single-dept vessel exception → **Not needed** (Deck + Engine always present). **D-GAP-M18**
- **M19** `applicable=false` → Master requests, DPA approves, dedicated audit log. **D-GAP-M19**
- **M20** SCM hard-block on overdue → Block Master sign-off (not meeting creation). **D-GAP-M20**
- **M21** Master rejection of SO closure → Mandatory reason + back to Open. **D-GAP-M21**
- **M22** Closed-Since-Last-SCM cutoff → Prior SCM CLOSURE timestamp. **D-GAP-M22**
- **M23** Section 12 scope → Once per 3-month cycle, not per inspection event. **D-GAP-M23**
- **(bonus)** **Ad-Hoc / Additional SCM** provision per SSQE §9 — Master or CO triggers for major incidents / important info; same form + shared SCM host RBAC; tagged `meeting_type = 'AD_HOC'`. **D-GAP-M-ADHOC**
- **M24** Photo evidence → HIGH mandatory; MED/LOW optional. **D-GAP-M24**

### Sub-batch 4c — Dashboards / NFR / UX (M25–M38 + rename)

- **M25** Multi-vessel duplicate detection → Auto-detect 24h/10nm, prompt creator. **D-GAP-M25**
- **M26** Timezone model → Reuse WRH `wrh_ship_time_config`. **D-GAP-M26**
- **M27** Heinrich Ratio → Always display + RAG confidence indicator. **D-GAP-M27**
- **M28** Notification fatigue → No digest; every event independent. **D-GAP-M28**
- **M29** CA aging → Days since CREATION; reopen does NOT reset. **D-GAP-M29**
- **M30** Inspection Compliance % → New vessel "N/A"; `pending_closure` counts. **D-GAP-M30**
- **M31** Dashboard export → PDF + Excel; **DPA owns export rights**; FM read-only. **D-GAP-M31**
- **M32** Archive search → Opt-in checkbox "Include archived records". **D-GAP-M32**
- **M33** Audit-log retention → Tied to parent; deleted on parent hard-delete. **D-GAP-M33**
- **M34** Mobile responsiveness → Tablet full CRUD; phone read-only dashboards. **D-GAP-M34**
- **M35** Accessibility → WCAG 2.1 Level AA. **D-GAP-M35**
- **M36** Localization → English-only V1; DD-MMM-YYYY; metric; multilingual is V2. **D-GAP-M36**
- **M37** Auditor export redaction → None; full context preserved. **D-GAP-M37**
- **M38** Near-miss spam controls → Rate limit (5/day/crew) + min-detail (≥100 chars + severity). **D-GAP-M38**
- **(rename)** Dashboard metric **"Inspection Compliance %" → "SOI Compliance %"** to avoid PSC-Inspection name clash. **D-GAP-DESIGN-01**

### Build-time specs deferred to docsuite (not locked as D-GAP; IMPLEMENTATION_PLAN / BACKEND_STRUCTURE phase)

- `safety_incident` field ENUMs and nullability
- `safety_field_history` column schema (TEXT vs JSON)
- Soft-archive physical implementation (`archived_at NULL` vs `is_archived BIT` vs partition)
- `safety_recommendation` cardinality enforcement
- `safety_soi_finding` state ENUM
- `safety_incident_phase_log` shape
- WRH lookback window / query timeout
- FTS engine choice
- Dashboard period persistence per user
- Paper-format PDF vs Excel layout details
- Trainee rotation coverage % formula
- 90-day counter reset exact timing

---

## Round 21 — References-Borrowed Sweep (CLOSED 2026-04-17, Session 5)

*Triggered by user contribution of additional reference pack at `Incident investigation/` (26 files incl. TapRoot, ABS RCA map, VMTC-RAII, IMO/TC RCA guidance, RightShip Lessons Learned, KAIZEN Manual, Nautical Institute 2019 evidence supplement). Two parallel review agents screened against locked SSOT. 28 borrow candidates surfaced (12 methodology + 16 evidence/procedure). User adopted **all 10 HIGH + all 13 MED = 23 new decisions**; 5 LOW items deferred; 4 items explicitly ignored.*

### Adopted — HIGH impact (10)

- **R01** Causal layering (Immediate/Intermediate/Root) on top of M-SCAT → extends D-DNV-01. Source: ABS 2005 §6 + RightShip 2023. **D-GAP-R01**
- **R02** ALARP cost-benefit gate on System-Action recommendations → new gate on D-DNV-06. Source: VMTC-RAII Veritas + IMO/ISM. **D-GAP-R02**
- **R03** Multiple root causes per incident is default; monocausal needs justification → guidance on D-DNV-01. Source: ABS §6.1. **D-GAP-R03**
- **R04** Chain-of-Custody tab added to D-DNV-07. Source: KAIZEN §11.4.5 + Nautical Institute 2019. **D-GAP-R04**
- **R05** Marine document inventory auto-checklist on D-DNV-07 Paper tab. Source: NI 2019 List 1. **D-GAP-R05**
- **R06** Evidence-preservation deadline task list (VDR 12h hard alarm etc.). Source: KAIZEN §11.4.2. **D-GAP-R06**
- **R07** First-hour scene-protection checklist pre-Phase-1. Source: KAIZEN §11.4.2–3. **D-GAP-R07**
- **R08** IMO classifier SMC/MC/MI as a field (separate from risk band); band deadlines remain per D-DNV-02. Reconciliation option (b). Source: KAIZEN §11.5.6 + OCIMF + IMO A.1075(28). **D-GAP-R08**
- **R09** Refined D-PDF-01 template with 10 standard sections. Source: KAIZEN §11.5.6 + Good Closure Report exemplar. **D-GAP-R09**
- **R10** Cargo-specific evidence overlay on D-DNV-07 (by incident type). Source: NI 2019 Lists 9/10/11. **D-GAP-R10**

### Adopted — MED impact (13)

- **R11** Tolerable-Failure filter at Phase 1 gate (GREEN only). Source: TapRoot + IMO RCA §9.6. **D-GAP-R11**
- **R12** Organisational defence-traps (Plant/Personnel/External) added to bias-guard set. Source: RightShip 2023. **D-GAP-R12**
- **R13** Corrective / Preventive / Lessons Learnt visual taxonomy on D-DNV-06. Source: RightShip 2023. **D-GAP-R13**
- **R14** Investigation-depth Task Triangle (Shallow/Medium/Deep) at Phase 1. Source: IMO RCA Feb 2014 §2.1. **D-GAP-R14**
- **R15** New M-SCAT sub-code `10.15 Design/MOC Governance — Independent Review Absent`; add to seed CSV. Source: TapRoot MOC-NI. **D-GAP-R15**
- **R16** People/Process/Plant interrogatory checklist at Phase 5 gate. Source: RightShip 2023. **D-GAP-R16**
- **R17** Pareto screening panel on Safety Intelligence Dashboard. Source: IMO RCA §9.6. **D-GAP-R17**
- **R18** Safeguard-failure interrogatory extending D-DNV-10 Barrier tool. Source: ABS 2005 App. 2. **D-GAP-R18**
- **R19** Witness statement read-back + sign-off protocol in D-DNV-08. Source: KAIZEN §11.4.4. **D-GAP-R19**
- **R20** Formal vs Informal interview distinction flag in D-DNV-08. Source: KAIZEN §11.4.4 + NI 2019 List 5. **D-GAP-R20**
- **R21** Marine-specific "Risk & Change Management" domain added to D-DNV-09 HF set. Source: KAIZEN §11.5.6.1. **D-GAP-R21**
- **R22** Near-miss Low vs High priority triage at creation. Source: KAIZEN §11.6. **D-GAP-R22**
- **R23** Health/fatigue evidence sub-section on D-DNV-07 People tab (personal-injury / illness incidents). Source: NI 2019 Lists 2/3. **D-GAP-R23**

### Deferred — LOW (5)

M-10 Near-miss parity (redundant with D-DNV-13) · E-06 Fully-anonymous near-miss (conflicts with D-GAP-J1 partial-anonymity; no additional change) · E-13 Diversion evidence overlay · E-15 Stowaway evidence overlay · E-16 Crew dispute / industrial-action evidence overlay. May revisit in V2.

### Ignored (4)

Full ABS MarCAT methodology swap · TapRoot SnapCharT pedagogical tool · VMTC-RAII full risk-mgmt curriculum · RightShip trend dashboard. All outside scope or duplicate existing decisions.

### Follow-up work triggered

- **Seed CSV update:** `safety-reference-data/mscat_taxonomy.csv` must gain row `10.15 Design/MOC Governance — Independent Review Absent` before seeding (per R15)
- **D-DNV-07 spec will expand** in BACKEND_STRUCTURE.md during docsuite — 5-source Evidence Workspace now includes Chain-of-Custody tab, marine doc inventory, preservation deadlines, scene-protection checklist, cargo overlay, health/fatigue sub-section
- **D-DNV-08 spec will expand** — Interview module now includes read-back + sign-off, Formal/Informal flag
- **D-DNV-09 spec will expand** — HF set now includes Risk & Change Management domain
- **D-DNV-10 spec will expand** — Barrier tool deepened with Safeguard-failure interrogatory; People/Process/Plant checklist at Phase-5 gate
- **D-DNV-11 spec will expand** — Bias guard set grows from 5 to 8 (+Plant/Personnel/External organisational traps)
- **D-DNV-13 spec will expand** — Dashboard gains Pareto panel
- **D-PDF-01 template redrawn** per R09 10-section spec

---

## INTERROGATION STATUS — **COMPLETE 2026-04-17, Session 5**

| Round | Topic | Status |
|-------|-------|--------|
| 1–12 | Sessions 1–3 (M-SCAT scope, classification, workflow, dashboard, integrations, regulatory) | CLOSED (prior sessions) |
| 13 | RBAC + Admin/Config Permissions (Q47, Q48) | CLOSED 2026-04-16 |
| 14 | PDF Export & Reporting (Q50) | CLOSED 2026-04-16 |
| 15 | Edge Cases & Validation (Q49) | CLOSED 2026-04-16 |
| 16 | Safety Officer Inspection (Q-SOI-1..15) | CLOSED 2026-04-16 |
| 17 | Gap-analysis sweep — Clusters A, B, C (14 decisions) | CLOSED 2026-04-17 |
| 18 | Gap-analysis sweep — Clusters D, E, F (13 decisions) | CLOSED 2026-04-17 |
| 19 | Gap-analysis sweep — Clusters G, H, I, J (8 decisions) | CLOSED 2026-04-17 |
| 20 | Gap-analysis sweep — MED-severity batch (40 decisions) | CLOSED 2026-04-17 |
| 21 | References-borrowed sweep (23 decisions from new reference pack) | CLOSED 2026-04-17 |

**Total decisions locked: 159** (D-DNV-01..14 [14] · D-RBAC-01..11 [11] · D-CFG-01..04 [4] · D-EDGE-01..12 [12] · D-PDF-01..03b [4] · D-SOI-01..16 [16] · D-GAP-A/B/C [14] · D-GAP-D/E/F [13] · D-GAP-G/H/I/J [8] · **D-GAP-M01..M38 [38] + D-GAP-M-ADHOC + D-GAP-DESIGN-01 [2]**)

**V1 Scope (final, locked):** Incident Reporting · Near Miss Reporting · Safety Committee Meeting (Regular + Ad-Hoc) · Safety Officer Inspection (13 areas / 329 items, paper-first, no scan upload)

**Module status:** REQUIREMENTS COMPLETE → **ready for docsuite generation** (11-doc handover folder pattern from `VIMS-Reporting-Module/`) + seed CSVs already extracted at `safety-reference-data/`:
- `mscat_taxonomy.csv` (173 rows, 17 basic-cause categories, 3.1–3.11 complete)
- `immediate_causes.csv` (52 rows, 28 acts + 24 conditions)
- `loss_types.csv` (7 rows)
- `soi_checklist_v1.csv` (329 rows, 13 areas including Compressor House, subsection_id schema)
**Total Q&A: ~89** across 4 sessions (3 prior + 2026-04-16 current).
**V1 Scope (final):** Incident Reporting · Near Miss Reporting · Safety Committee Meeting · **Safety Officer Inspection** (12 inspection areas, ~292 items)

**Module status:** REQUIREMENTS COMPLETE → ready for docsuite generation (11-doc handover folder pattern from `VIMS-Reporting-Module/`):
1. PRD.md
2. APP_FLOW.md
3. TECH_STACK.md
4. DESIGN_SYSTEM.md
5. FRONTEND_GUIDELINES.md
6. BACKEND_STRUCTURE.md
7. IMPLEMENTATION_PLAN.md
8. VALIDATION_RULES.md
9. USER_GUIDE.md
10. LESSONS.md
11. CLAUDE.md

Plus seed data files: M-SCAT taxonomy CSVs (170+ basic causes, 48 immediate causes, 7 themes, 3 lack-of-control areas), 2 case-study seed records (Navigator + Sinkfast).

---

## Pending Rounds (to be added as interrogation progresses)

- Round 14 — PDF Export & Reporting
- Round 15 — Edge Cases & Validation Rules

---

*Interrogation in progress. Answers will be merged into VIMS-SAFETY-MODULE-SSOT.md upon completion.*
