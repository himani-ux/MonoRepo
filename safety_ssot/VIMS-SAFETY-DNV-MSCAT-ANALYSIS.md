# VIMS Safety Module — DNV / M-SCAT Reference Wiki

> **Source pack:** `2023_DNV Practical Incident Investigation and Root Cause Analysis/` (4 sub-folders, 27 files: 12 PDFs + 14 DOCX/PPTX worked exercises + 1 spreadsheet matrix)
> **Compiled:** 2026-04-16
> **Purpose:** Distilled, build-ready guidance from the DNV Practical Incident Investigation & Root Cause Analysis course (2023). This wiki is the **canonical reference** the Safety Module SSOT draws from for: M-SCAT cause taxonomy, investigation workflow, evidence framework, interview protocol, fact-tree/STEP method, IMO regulatory fields, and recommendation-writing rubric.
> **Status:** Reference wiki — feeds the SSOT but does not replace it. Raw PDFs/DOCX remain untouched in the source folder.
> **Adoption status (2026-04-16):** All 14 §14 diff items adopted by user. SSOT now contains 45 binding decisions (D-DNV-01..14 + D-RBAC-01..11 + D-CFG-01..04 + D-EDGE-01..12 + D-PDF-01..03b). See `VIMS-SAFETY-MODULE-SSOT.md` §6 Decisions Log for the full list.

---

## 1. What This Pack Adds to the Safety Module

Until now the Safety SSOT specified "M-SCAT investigation for incidents (all 4 levels)" but treated M-SCAT as a black box. This DNV pack supplies:

1. **The full M-SCAT cause taxonomy** — 17 Basic Cause categories with ~170 numbered sub-codes, plus the Immediate Cause set (Substandard Acts/Conditions) and the Lack-of-Control layer. **This is the dropdown content for the cause-classification UI.**
2. **The DNV-prescribed investigation workflow** — 8 phases from scene control to follow-up, with an explicit "need more info?" loop-back gate.
3. **The 5-source evidence framework** (Position / People / Parts / Paper / Electronic) — what every investigation must collect before analysis.
4. **The 4-phase interview protocol** with question-type guidance (Open / Closed / Analysing / Clarifying / Probing — Avoid Leading & Biased).
5. **The SHELL human-factors model** + IMO Resolution A.884(21) 7-domain human-element checklist.
6. **STEP, Fact Tree, Event-and-Causal-Factor (ECF), Barrier Analysis, Change Analysis** — five complementary analysis tools, each with field-level template.
7. **IMO casualty definitions and MSC-MEPC.3/Circ.4 mandatory reporting fields** (5 appendices, 30 coded option lists) — the regulatory floor for what the incident form must capture.
8. **Three-tier safety-recommendation format** — Lessons Learned → Immediate Actions → System Actions (with worked examples from Navigator grounding and Sinkfast pump-room explosion).
9. **Investigator-bias safeguards** — 5 named biases with system-level guards.

---

## 2. The Loss Causation Model (DNV Core Diagram)

```
┌───────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────┐   ┌──────┐
│ LACK OF       │──▶│ BASIC        │──▶│ IMMEDIATE     │──▶│ INCIDENT │──▶│ LOSS │
│ CONTROL       │   │ CAUSES       │   │ CAUSES        │   │ (event)  │   │      │
│               │   │              │   │               │   │          │   │      │
│ Inadequate:   │   │ Personal     │   │ Substandard   │   │          │   │ Above
│ • System      │   │ Factors (1-4)│   │ Acts /        │   │          │   │ Threshold
│ • Standards   │   │ Job/System   │   │ Practices     │   │          │   │ Limit
│ • Compliance  │   │ Factors (5-17│   │ Substandard   │   │          │   │ = Loss
│               │   │              │   │ Conditions    │   │          │   │ Below =
│               │   │              │   │               │   │          │   │ Near Miss
└───────────────┘   └──────────────┘   └───────────────┘   └──────────┘   └──────┘
```

**Threshold Limit principle:** the same incident-event chain produces a **loss** (accident) or a **near miss** depending only on whether outcomes cross a damage/injury threshold. This justifies treating both in one investigation flow with shared cause taxonomy.

**Heinrich/Bird Accident Ratio** (built into M-SCAT teaching):

| Layer | Ratio |
|-------|-------|
| Fatality / Major Injury | 1 |
| Minor Injury | 10 |
| Property Damage | 30 |
| Near Miss | 600 |
| Hazards (immediate causes, no incident) | 600+ |

> **Application in VIMS:** the Safety Health Score and "reporting culture" panel on the dashboard should monitor the *ratio* — not just absolute counts. A vessel reporting 1 incident and 0 near-misses is a worse signal than 1 incident and 30 near-misses.

---

## 3. M-SCAT Cause Taxonomy (Complete Coding for UI Dropdowns)

### 3.1 Layer 3 — IMMEDIATE CAUSES

Two branches. Codes seen in the worked exercises (Navigator + Sinkfast cases):

**Substandard Acts / Practices**
- 2. Failure to Follow Procedure / Instruction
- 4. Failure to Use PPE / Personal Detection Equipment Properly
- 5. Failure to Inform / Warn
- 8. Improper Placing
- 10. Incorrect Navigation
- 15. Inadequate Servicing of Equipment / Machinery in Operation
- 16. Using Defective Tool / Equipment / Machinery / Device
- 17. Improper Operation of Equipment / Tools

**Substandard Conditions**
- 25. Defective Tool / Equipment
- 33. Presence of Flammable / Explosive Atmosphere
- 38. Inadequate Ventilation
- 39. Inadequate Warning System
- 40. Incorrect / Inadequate Tool / Equipment

> **Note:** the full Substandard Acts list (numbered 1–24) and Substandard Conditions list (25–48) are in `MSCAT 8.2 - Basic causes explained.pdf`. The codes above are the ones explicitly used in the DNV worked solutions; the full set must be loaded into the dropdown table from the chart PDF before go-live.

### 3.2 Layer 2 — BASIC CAUSES (Root Causes)

**Personal Factors**

| # | Category | Sub-codes |
|---|----------|-----------|
| 1 | Inadequate Physical / Physiological Capability | 1.1–1.11 (height/weight/strength, range of movement, body positions, substance sensitivity, sensory extremes, vision, hearing, other sensory, respiratory, permanent disability, temporary disability) |
| 2 | Inadequate Mental / Psychological Capability | 2.1–2.10 (fears/phobias, emotional disturbance, mental illness, intelligence, comprehension, coordination, reaction time, mechanical aptitude, learning aptitude, memory) |
| 3 | Physical / Physiological Stress | 3.1–3.10 |
| 4 | Mental / Psychological Stress | 4.1–4.11 (emotional overload, fatigue, judgment demands, monotony, perception demands, meaningless activity, conflicting directions, conflicting interests, **4.9 Procrastination/Preoccupation**, frustration, mental illness) |

**Job / System Factors**

| # | Category | Notable sub-codes |
|---|----------|-----------|
| 5 | Lack of Competence | 5.1 Inadequate experience · 5.2 Inadequate orientation/induction · 5.3 Inadequate initial training · 5.4 Inadequate refresher training · 5.6 Lack of situational awareness/risk perception · 5.7 Inadequate skill training · 5.8 Inadequate practice · 5.10 Inadequate coaching |
| 6 | Improper Motivation | 6.1–6.17 (reward/punishment misalignment, incentive conflicts, frustration, peer pressure, leadership example, feedback) |
| 7 | Unclear Organizational Structure | 7.1 Reporting · 7.2 Function/role · 7.3 Accountability |
| 8 | Inadequate Leadership | 8.1 HSE strategy · 8.5 Inadequate communication of policy/procedure · **8.7 Inadequate work/process planning** · 8.8 Condone deviation · 8.11 Inadequate management info · 8.12 Inadequate audit-action closure |
| 9 | Inadequate Supervision / Coaching | 9.1 Inadequate instruction · 9.4 Mismatch qualifications↔job · 9.5 Performance measurement · 9.6 Performance feedback |
| 10 | Inadequate Management of Change | 10.1 Hazard ID in design · 10.5 Human/ergonomic factors · 10.11 Operational readiness · 10.12 Commissioning/handover · 10.14 MoC process |
| 11 | Inadequate Supply Chain Management | 11.1 Specs on PO · 11.5 Receiving inspection · 11.6 Hazard communication · 11.13 Contractor selection |
| 12 | Inadequate Maintenance / Inspection | 12.1 Preventive needs · 12.6 Scheduling · **12.7 Inadequate assessment of repair needs** · 12.9 Inspection method/interval |
| 13 | Excessive Wear / Tear | 13.1 Use planning · 13.2 Service-life extension · 13.4 Improper loading |
| 14 | Inadequate Tool / Equipment / Machinery | 14.1 Needs and risk assessment · 14.4 Measurement/detection · 14.6 Inspection/maintenance · 14.7 Calibration |
| 15 | Inadequate Product / Service Design | 15.1 Need/risk assessment · 15.5 Design validation · 15.6 Design verification |
| 16 | Inadequate Work / Production Standards | 16.1 Regulatory ID · 16.4 Coordination with process design · 16.7 Publication · 16.8 Distribution · 16.11 Training of standard · 16.13 Compliance monitoring |
| 17 | Inadequate Communication / Information | 17.1 Information handling · 17.2 Unclear info · 17.3 Internal transfer · 17.4 Client transfer · 17.5 Authority transfer · 17.7 Communication structure · 17.8 Databases |

### 3.3 Layer 1 — LACK OF CONTROL (Management System)

Three areas; each finding must map to at least one:
- **System** — process design, implementation, monitoring, verification, review
- **Standards** — policies, procedures, instructions, specifications
- **Compliance** — adherence to and enforcement of standards

> **UI rule:** every M-SCAT investigation must end with at least one Lack-of-Control entry. If the investigator's only root causes are Personal Factors (1–4) without any Job/System Factor (5–17) and without a System/Standards/Compliance failure, the system flags a *blame-fixation warning* (see §10).

### 3.4 Type-of-Loss Categories (7)

From the M-SCAT chart header — every incident is classified under one or more:

1. **People** (Safety / Health)
2. **Asset** (Damage)
3. **Environmental**
4. **Financial** (Fines, Claims, Insurance)
5. **Non-Conformity** (Product / Service)
6. **Reputation / Complaint**
7. **Process / Business**

> **VIMS mapping:** these become the *Impact Category* multi-select on the incident form (currently labelled "Impact Category" in the SSOT). The DNV list is more granular than what we had — recommend adopting verbatim.

### 3.5 Type-of-Event Codes (Confirmed)

From worked exercises (full list in MSCAT chart):
- 14. Ship grounding
- 16. Fire
- 17. Explosion

Combined with IMO's 11 reportable types (§7) → final dropdown.

---

## 4. M-SCAT Investigation Workflow (8 Phases)

| Phase | Activity | Key deliverable | UI artefact |
|-------|----------|-----------------|-------------|
| 1 | **Control the Scene** | Stop further losses, first aid, preserve evidence, notify | Scene-control checklist |
| 2 | **Allocate Resources** | Team appointed with right qualifications | Team-assignment screen |
| 3 | **Evidence Collection** | 5-source data (Position/People/Parts/Paper/Electronic) | Evidence workspace (5 tabs) |
| 4 | **Systemize Facts** | Sequence events, identify gaps | STEP timeline + Fact Tree builder |
| 5 | **Analyse Causes** | Immediate → Basic → Lack-of-Control | M-SCAT cause picker |
| 6 | **Need More Info?** | Decision gate | Loop back to Phase 3 / proceed |
| 7 | **Findings & Report** | Causal narrative + recommendations | Report generator |
| 8 | **Follow-up** | Verify CA effectiveness | Effectiveness review screen |

> **Critical change vs current SSOT:** today the Safety SSOT runs Draft → In Progress → Pending Review → … → Closed. DNV's loop-back gate at Phase 6 means "In Progress" must support **re-opening evidence collection after analysis starts**, not just linear forward progression. UI implication: the investigator stage must allow returning to the evidence tab without resetting analysis already entered.

---

## 5. Evidence Framework — The 5 Sources

Every investigation must populate all 5 categories (gaps allowed but flagged):

| Source | What | Maritime examples |
|--------|------|-------------------|
| **Position** | Where things were | Lat/lon, vessel position, equipment location, photos (long/medium/short range from 4 angles), sketches, deck plans |
| **People** | Who saw / did what | Witness list, interviews, crew condition at time, fitness/fatigue, qualifications |
| **Parts** | Physical objects | Damaged equipment, samples, wear/tear, labels, signs, safeguards, previous-damage history |
| **Paper** | Documents | SMS procedures, standing orders, voyage plan, charts, logs, work permits, training records, certificates, minutes |
| **Electronic** | Digital traces | VDR, ECDIS, GPS, UMS, VTS, fire/ballast control logs, CCTV, email, AIS |

**DNV evidence-management worksheets to digitise:**
- **Evidence Checklist** — `No. | Item | Where | Why | Comments`
- **Evidence Matrix** — `Finding | Pro Evidence | Con Evidence | Source | Comments` (forces investigator to log *contradicting* evidence — confirmation-bias guard)

> **Rule of thumb (DNV):** quality of evidence deteriorates with time. The system should auto-prompt for "perishable evidence" (witness statements, equipment readings, weather observations) within 24 hours of incident notification.

---

## 6. Interview Protocol (4-Phase, with Question-Type Guard)

### Phase structure

1. **Make Acquaintance** — handshake, name, function, find a quiet spot
2. **Introduction** — purpose, structure, timeframe, recording, confidentiality
3. **The Meeting** — open questions first, minimal note-taking, ask follow-ups
4. **Conclusion** — invite queries, offer follow-up, thank

### Question types (UI guidance)

| Type | Use | Example |
|------|-----|---------|
| Open | Encourage narrative | "Walk me through what you saw." |
| Closed | Verify a fact | "Was the permit issued?" |
| Analysing | Compare procedure vs action | "The procedure says X — is that what happened?" |
| Clarifying | Remove ambiguity | "Correct me if wrong, you said …?" |
| Probing | Deeper thought | "What do you think caused this?" |
| **AVOID — Leading** | Plants the answer | ~~"That's not allowed, is it?"~~ |
| **AVOID — Biased** | Implies blame | ~~"How could that happen?"~~ |
| Use instead — Unbiased | Neutral framing | "How did that happen?" |

> **UI implication:** the interview screen should have a question-bank dropdown labelled by type. A free-text question field can run a simple keyword check ("could that", "shouldn't you", "isn't it") and surface a soft warning suggesting an unbiased rephrase.

### Interviewer behaviour checklist (optional self-audit)

Body language · Gestures · Facial expression · Note-taking discipline · Voice volume · Voice tone · Word choice — all rated open vs closed.

---

## 7. IMO / EMSA Regulatory Floor

### 7.1 Casualty severity definitions (IMO MSC.255(84))

| Class | Threshold |
|-------|-----------|
| **Very Serious Casualty** | Loss of life · Loss of ship · Pollution > 400 t · Mitigation > $2M |
| **Serious Casualty** | Hospitalisation injury · Property damage > $2M · Pollution 100–400 t · Significant operational impact |
| **Less Serious Casualty** | Below "Serious" threshold but still a casualty |
| **Marine Incident** | Hazardous occurrence not rising to casualty class |

### 7.2 Reportable event types (11 IMO categories)

1. Collision
2. Stranding / Grounding
3. Contact (with fixed/floating object)
4. Fire / Explosion
5. Hull failure
6. Machinery damage
7. Damage to ship / equipment
8. Capsizing / listing
9. Missing vessel
10. Accidents with life-saving appliances
11. Other

> **UI mapping:** these become the *Incident Type* multi-select. Combined with the M-SCAT type-of-event codes (§3.5) it gives a unified picklist that satisfies both regulatory reporting and M-SCAT classification.

### 7.3 MSC-MEPC.3/Circ.4 reporting form (5 appendices)

| Appendix | Content | VIMS form section |
|----------|---------|-------------------|
| 1 | Generic info — date, location, reporter, investigating authority | Header |
| 2 | Ship particulars — IMO, flag, class, GT, crew, cargo | Auto-populate from vessel particulars |
| 3 | Casualty analysis — sequence, hazards, contributing factors | Investigation tabs |
| 4 | Supplementary — weather, sea state, environment | Auto-populate from Daily Reporting position-time match |
| 5 | Field value tables — 30 standardised picklists | Reference data tables |

> **Auto-population win:** Appendix 2 fields are already in VIMS vessel particulars; Appendix 4 weather/sea fields can be pulled from the matching Daily Report (using same-DB join already specified for safety↔reporting integration). Estimated **~40 % of MSC-MEPC.3 fields auto-fill** with no investigator input.

### 7.4 IMO Res. A.884(21) — 7 human-element domains

Investigator must consider all seven:

1. **People** — qualifications, experience, fatigue, health
2. **Organization on board** — task division, manning, comms, workload, hours/rest
3. **Working & living conditions** — ergonomics, recreation, food, motion/noise
4. **Ship factors** — design, maintenance, equipment, cargo
5. **Shore-side management** — recruitment, scheduling, contracts, ship-shore comms
6. **External influences & environment** — weather, traffic, regulations, inspections
7. **Sequence of events** — timeline, immediate conditions

> **UI mapping:** these become a **7-tab "Human Factors" sub-section** inside the M-SCAT investigation form. Each tab is optional; investigator ticks "considered — n/a" or fills narrative.

---

## 8. SHELL Human-Factors Model

DNV uses Hawkins (1987) SHELL as the structural lens for human-factors analysis:

```
            Software
               │
   Liveware ──┼── Hardware
   (peripheral) │
            Liveware ←── (central — the person)
               │
           Environment
```

| Element | Examples |
|---------|----------|
| **S — Software** | Procedures, manuals, checklists, computer programs, charts |
| **H — Hardware** | Workstations, controls, displays, seats, equipment design |
| **E — Environment** | Weather, visibility, vibration, noise, fatigue, regulatory climate |
| **L — Liveware (central)** | The person — capabilities, limits, physical/mental state |
| **L — Liveware (peripheral)** | Other humans — supervision, teamwork, communication, management |

> **UI rule:** every human-factor finding the investigator logs is **tagged with one of S/H/E/L-central/L-peripheral**. This produces dashboard analytics ("our cluster of incidents tags to L-peripheral / S = supervisor-procedure mismatch").

---

## 9. Analysis Tools — Five Templates to Digitise

### 9.1 STEP (Sequentially Timed Events Plotting)

Card-based timeline. Columns = time slots. Rows = actors. Each cell = an action.

| Field | Value |
|-------|-------|
| Event ID | E-001 |
| Actor | Fitter / Pumpman / CO / CE / Master / Fire-brigade … |
| Action | One noun + one verb |
| Time began | YYYY-MM-DD HH:MM |
| Duration | minutes |
| Data source | Interview / log / VDR / photo |
| Location | "Pump room, frame 25" |
| Description | Free narrative |

> **VIMS UI:** swimlane diagram with date columns and actor rows — draggable event cards. Auto-populates the Fact Tree and ECF Chart.

### 9.2 Fact Tree

End-fact at top, build downward by repeatedly asking:
1. **What is needed?** (causal precondition)
2. **Is that enough?** (sufficiency check — if no, add AND-branch)

Example (from DNV course):
```
              [Cannot stop in time, car hits wall]
                          ▲
                          │
              [Brakes work insufficiently]
                          ▲
              ┌───────────┴───────────┐
   [Brakes not maintained]   [Driving 100 km/h]
```

> **UI:** drag-to-add boxes; AND-gate visualisation; tree validation = every leaf must trace to evidence.

### 9.3 Event & Causal Factor (ECF) Chart

Visual symbol set:
- **Diamond** = the incident
- **Box** = event (active, one noun + verb, dated, quantified)
- **Oval** = condition (passive, state-descriptive)
- **Dashed shape** = presumptive (unconfirmed) fact
- **Arrow** = causal link

> **UI:** node-edge graph editor. Acts as the visual glue between STEP timeline and M-SCAT cause classification.

### 9.4 Barrier Analysis

| Hazard / Target | Barriers that existed | How did the barrier perform? | Why did it fail? | Effect on incident? |
|-----------------|----------------------|------------------------------|-----------------|---------------------|

Forces investigator to enumerate the *defences-in-depth* and locate the broken layer (Reason's Swiss-cheese applied).

### 9.5 Change Analysis

Compare incident-state vs ideal/baseline state across 6 factors:

| Factor | Incident situation | Prior / ideal situation | Difference (change) | Effect |
|--------|-------------------|-------------------------|---------------------|--------|
| WHAT | | | | |
| WHEN | | | | |
| WHERE | | | | |
| WHO | | | | |
| HOW | | | | |
| OTHER | | | | |

> **Bias guard:** Change Analysis specifically counters confirmation bias by anchoring against a known incident-free baseline rather than a hypothesis.

---

## 10. Investigator-Bias Safeguards (System-Level Guards)

| Bias | Risk | VIMS guard |
|------|------|------------|
| **Recency** | Tunnel vision on final moments | Block "submit analysis" until all 5 evidence categories have ≥1 entry or "n/a — justified" |
| **Assumption** | Filling gaps with guesses | Every fact box requires an evidence link (interview ID / document ID / photo ID) |
| **Hindsight** | Judging past with present knowledge | Decision/action records timestamped; cannot reference info dated after the event |
| **Confirmation** | Ignoring contradictory evidence | Evidence Matrix requires at least one *Con* row for any major finding |
| **Blame fixation** | Stops at the individual error | If all root causes are Personal Factors (cat 1–4) AND no Lack-of-Control entry → flag for senior review |

---

## 11. Worked Examples (DNV Course Solutions)

### 11.1 Navigator — Container vessel grounding, Verne Bank, Dover Strait, 18 Sept 2013

**Type of loss:** Asset (Damage), Reputation/Complaint, Process/Business
**Type of event:** 14. Ship grounding
**Immediate causes:**
- 10. Incorrect Navigation — position only monitored against ECDIS track; OOW took 19 min to realise grounding
- 10. Incorrect Navigation — route leg crossed Verne Bank
- 5. Failure to inform — lookout missed Verne Bank cardinal buoy
- 5. Failure to warn — CNIS did not alert
- 17. Improper operation of equipment — wrong ECDIS chart scale
- 39. Inadequate warning system — wrong safety parameters
- 16. Using defective equipment — ECDIS audible alarm unserviceable

**Root causes (Basic):**
- 5. Lack of competence — passage planned by inexperienced unsupervised junior officer; not checked by Master or OOW
- 8. Inadequate leadership — dysfunctional onboard management; insufficient leadership for safety culture
- 12. Inadequate maintenance — defective ECDIS audible alarm not reported

**Recommendations** (3-tier):
- **Lessons learned:** navigation is critical; Master must brief bridge team; promotion/handover/familiarisation inadequate
- **Immediate actions:** safety bulletin to fleet · ECDIS trainer to vessel for type-specific refresher · Master-led risk assessment for Dover Strait · extraordinary internal audits on nav-safety, defect reporting, leadership
- **System actions:**
  - *Training & competence* — defect-reporting training in-house; replace CBT with in-house ECDIS trainer; Competency Management System as promotion prerequisite
  - *Contractor management* — formal evaluation program for training providers
  - *Compliance assurance* — third-party navigational safety audits

### 11.2 Sinkfast — Tanker pump-room explosion, Esso Fawley, 19 Sept 2015 (1 fatality)

**Type of loss:** People (Safety/Health), Asset, Environmental
**Type of event:** 17. Explosion / 16. Fire
**Immediate causes:**
- 2. Failure to follow procedures — inadequate cold work permit; hazards not all evaluated
- 4. Failure to use personal gas detection equipment properly — Fitter had no personal detector
- 8. Improper placing — newly-joined Fitter assigned high-risk task
- 33. Presence of flammable atmosphere — vapour condensation
- 25. Defective equipment — fixed gas detector failed
- 17. Improper operation of tools — steel hammer/spanner used (ignition source)

**Root causes (Basic):**
- 4.9 Preoccupation with problem — crew constantly fighting equipment problems; expected pump failure
- 5. Lack of competence — Fitter never worked tanker before
- 9. Lack of supervision — high-risk job not senior-supervised
- 16. Inadequate work standard — shipboard procedures didn't suit vessel type; no controlled-entry permit; safety-critical equipment not maintained
- 12.7 Inadequate assessment of repair needs — shore organisation ignored urgent repair requests

**Recommendations** (3-tier):
- **Lessons learned:** inadequate Management of Change when company took new vessel type into management in 2014; SMS, equipment classification, maintenance, shore competency gaps not identified
- **Immediate actions:** safety bulletin · third-party SMS revision · all cargo pumps overhauled, pump-room fan repaired, gas detection calibrated, all outstanding orders delivered before sailing
- **System actions:**
  - *Training & competence* — tanker operations training for line management; competence matrix revised
  - *Human resources* — crew retention KPI; tanker-experienced vessel manager hired

> **Use of these examples in VIMS:** load both as the seed Case Study Library entries in the Knowledge Base. Investigators see them when starting their first M-SCAT analysis.

---

## 12. Recommendation-Writing Rubric (3-Tier Output Format)

Every investigation must close with three sections:

### 12.1 Lessons Learned
A short narrative of *what the company / fleet should know*. Generalised — not vessel-specific. This is the content that goes into the **Fleet Circular** (already specified in SSOT — connects to existing VIMS Circular module).

### 12.2 Immediate (Corrective) Actions — within 30–90 days
- Equipment repairs / calibration
- Crew coaching / refresher
- Procedure update
- Safety bulletin
- Fleet-wide awareness

### 12.3 System Actions — preventing recurrence (long-term)
Organised under standard themes:
- **Training & Competence**
- **Contractor / Supplier Management**
- **Compliance Assurance** (audits, third-party verification)
- **Human Resources** (retention, hiring profile, KPIs)
- **Management of Change**
- **Procedures & Standards**
- **Equipment Management**

> **UI rule:** the recommendation editor must enforce a **non-empty Lessons Learned + ≥1 Immediate Action + ≥1 System Action** before allowing investigation closure. System Actions auto-tag against the 7 themes for fleet-wide trend analysis.

---

## 13. Severity / Investigation-Scope Matrix (Risk-Based Investigation Depth)

DNV ties investigation depth to risk level (severity × probability):

| Risk Level | Reporter | Investigator | Initial Time | Closure Time | Verification |
|-----------|----------|--------------|--------------|--------------|--------------|
| **GREEN — Negligible** | Master | Master | 28 days | 30 days | HSE register |
| **YELLOW — Intermediate** | Master | DPA | 14 days | ~30 days | Internal audit |
| **RED — Urgent / Critical** | Master | Managing Director + external expert | 7 days | Per-case | Extraordinary management review |

> **VIMS mapping:** today the SSOT specifies a single 45-day deadline for all incidents. DNV's risk-tiered model is more sophisticated. **Recommendation:** keep 45 days as default, but:
> - **RED-band incidents** (fatality / major injury / total loss / pollution) auto-shorten to **7-day initial findings + DPA-led investigation**
> - **GREEN-band** (near miss / minor) remain 30-day Master-led
> See §14.

---

## 14. Mapping DNV → Existing Safety SSOT (Diff Proposal)

| Existing SSOT decision | DNV-informed change | Effort |
|------------------------|---------------------|--------|
| "M-SCAT investigation for incidents (all 4 levels)" — opaque | **Load full 17-cat × ~170-code M-SCAT taxonomy as reference table** with hierarchical picker UI | Medium — one-time data load + picker component |
| Single 45-day deadline | **Risk-tiered deadlines:** RED 7d initial, YELLOW 14d, GREEN 30d (all close ≤45d default) | Small — workflow rule change |
| 3-layer classification: Type / Severity / Impact Category | **Replace Impact Category with DNV 7 Type-of-Loss list** (People/Asset/Environmental/Financial/NC/Reputation/Process) | Small — picklist swap |
| Incident Type — multi-select | **Adopt IMO 11 reportable types** + M-SCAT type-of-event extension | Small — picklist swap |
| Investigator workflow — Draft → In Progress → Pending Review … | **Add Phase-6 loop-back gate**: from analysis-stage, allow re-opening evidence collection without losing partial analysis | Medium — state-machine update |
| CA/PA inside incident form | **Restructure recommendations** as 3-tier: Lessons Learned + Immediate Actions + System Actions (themed) | Medium — form refactor |
| Free-text root cause notes | **M-SCAT cause picker** (taxonomy dropdown) + free-text rationale per code | Medium — new form section |
| Evidence as attachments only | **5-source Evidence Workspace** (Position/People/Parts/Paper/Electronic tabs) + Evidence Matrix (Pro/Con) | Large — new module |
| Interview = free text | **Structured Interview screen** (4 phases, question-type guidance, behaviour self-audit) | Medium — new form |
| Human factors not modelled | **SHELL tags + IMO A.884(21) 7-domain checklist** | Small — tagging + checklist |
| Single fact narrative | **STEP timeline + Fact Tree + ECF Chart** as parallel views | Large — multi-tool analysis workspace |
| No bias guard | **5 named bias guards** (recency, assumption, hindsight, confirmation, blame fixation) as form-level validations | Medium |
| MSC-MEPC.3 fields not addressed | **Auto-map** Appendix 2 from vessel particulars + Appendix 4 from Daily Report position-time match | Small — DB joins |
| Safety Health Score on dashboard | **Add Heinrich ratio panel** (1:10:30:600) — flag vessels with skewed ratios | Small — new chart |

---

## 15. Source Pack Catalogue (for INDEX.md)

```
2023_DNV Practical Incident Investigation and Root Cause Analysis/
├── 01_Presentation/
│   ├── DNV Pract_Inc_Investigation.pdf                       (78 pp main presentation)
│   └── Introduction to DNV MSCAT 2023.pdf                    (9 pp MSCAT intro)
├── 02_Documentation/
│   └── Docu_Practical_Inc_Inv_RCA_2021.pdf                   (33 pp full course book)
├── 03_Tools_Materials/
│   ├── Annual Overview of Marine Casualties and Incidents 2023.pdf  (EMSA stats)
│   ├── CASUALTY ANALYSIS PROCEDURE.pdf                       (DNV procedure)
│   ├── EMSAFE_Report_2022.pdf                                (EMSA framework)
│   ├── IMO_In-the-field aide memoire.pdf                     (40 pp scene checklist)
│   ├── Introduction to DNV MSCAT 2023.pdf                    (duplicate of 01)
│   ├── LiteratureSources_2021.pdf                            (bibliography)
│   ├── MSC-MEPC3_Circ4 Rev 1  Revised harmonized reporting.pdf (IMO mandatory fields)
│   ├── MSCAT 8.2 - Basic causes explained.pdf                (18 pp full taxonomy)
│   ├── Resolution A1075_28_Impl of CIC.pdf                   (Casualty Investigation Code)
│   └── Resolution_A884_21.pdf                                (7 human-element domains)
└── Course material/
    ├── 1.pdf                                                 (extra handout)
    ├── Ac_01_Principles of Investigation.pdf                 (5 pp)
    ├── Ac_02_NAVIGATOR_Ship_Details.pdf                      (case)
    ├── Ac_02_NAVIGATOR_Statement_Facts.pdf                   (case)
    ├── Ac_02_SINKFAST_Ship_Details.pdf                       (case)
    ├── Ac_02_SINKFAST_Statement_Facts.pdf                    (case)
    ├── Ac_02_Worksheet_Matrix.docx                           (evidence matrix template)
    ├── Ac_04_Human Factors.pdf                               (4 pp SHELL)
    ├── Ac_05_The_Interview.pdf                               (3 pp protocol)
    ├── Ac_06_Grounding_summary.pdf                           (Navigator summary)
    ├── Ac_06_Pumproom explosion_summary.pdf                  (Sinkfast summary)
    ├── Ac_06_STEP blank.docx                                 (STEP template)
    ├── Ac_07_Creating_FactTree.docx                          (fact tree exercise)
    ├── Ac_09_MSCAT_RCA.docx                                  (blank RCA template)
    ├── Ac_09_MSCAT_RCA_Navigator_Solution.docx               (worked solution)
    ├── Ac_09_MSCAT_RCA_Sinkfast_Solution.docx                (worked solution)
    ├── Ac_09_MSCAT_Training_Tool*.pdf                        (3 versions)
    ├── Ac_10_Safety recommendations.docx                     (blank template)
    ├── Ac_10_Safety recommendations_Navigator_solution.docx  (worked solution)
    ├── Ac_10_Safety recommendations_Sinkfast_solution.docx   (worked solution)
    ├── human-factors-approach.pdf
    └── OCIMF-Human-Factors-Management-and-Self-Assessment.pdf
```

---

## 16. Adoption Trail (what happened on 2026-04-16)

1. **INDEX.md** — DNV folder catalogue (raw sources) + this wiki entry added. ✅
2. **VIMS-SAFETY-MODULE-SSOT.md** — all 14 §14 diff items adopted by user ("all Y"). New §2B "M-SCAT Investigation Framework" section added with binding spec content for each diff item. §3 (Incident Reporting) and §4 (Near Miss) refreshed from stubs to bound spec. §6 Decisions Log gained D-DNV-01..14. ✅
3. **VIMS-SAFETY-REQUIREMENTS-INTERROGATION.md** — Q47 (RBAC) reopened with DNV risk-tiered lens. Rounds 13 + 14 + 15 then completed in same session. ✅
4. **45 decisions locked total** spanning the DNV framework, RBAC, admin/config, edge cases, and PDF export. See SSOT §6 for canonical list. ✅
5. **Module status** advanced from "Interrogation IN PROGRESS" → "REQUIREMENTS COMPLETE — ready for docsuite generation". ✅

---

## 17. Reference-Data Loads Still Needed at Build Time

When the build phase begins, these CSVs must be prepared from the source PDFs and seeded into the backend:

| Reference table | Rows | Source |
|-----------------|------|--------|
| `safety_immediate_cause_act` | 24 (codes 1–24) | `MSCAT 8.2 - Basic causes explained.pdf` |
| `safety_immediate_cause_condition` | 24 (codes 25–48) | same |
| `safety_basic_cause` | ~170 (17 cats × sub-codes) | same + DNV wiki §3.2 |
| `safety_lack_of_control` | 3 (System / Standards / Compliance) | DNV wiki §3.3 |
| `safety_loss_type` | 7 (DNV verbatim) | wiki §3.4 |
| `safety_incident_type` | 11 (IMO MSC.255(84) verbatim) | wiki §7.2 |
| `safety_event_type` | (M-SCAT type-of-event codes) | MSCAT chart |
| `safety_recommendation_theme` | 7 themes | wiki §12.3 |
| `safety_external_party_type` | 7 (Pilot/Shipyard/Stevedore/Contractor/Passenger/Port Agent/Other) | D-EDGE-02 |
| `safety_case_study` | 2 seed (Navigator + Sinkfast) | DNV course solutions |
| MSC-MEPC.3 Appendix 5 picklists | 30 | `MSC-MEPC3_Circ4 Rev 1.pdf` |

---

*This wiki is the LLM-compiled summary of the DNV pack. The raw PDFs/DOCX in `2023_DNV Practical Incident Investigation and Root Cause Analysis/` remain authoritative — refer back when implementing any rule cited here.*

---

## §18 — Extraction + Session 5 updates (2026-04-17)

**Seed CSVs extracted to `safety-reference-data/`:**
- `mscat_taxonomy.csv` — 174 rows. 17 basic-cause categories × full sub-codes. Category 3 (Physical/Physiological Stress) **editorially corrected** from the DNV Ac_09 Training Tool because the original `MSCAT 8.2 - Basic causes explained.pdf` (page 4) has a copy-paste defect where the Cat 3 label text duplicates Cat 2's entries. Full verbatim Cat 3 list now 3.1 Injury or illness · 3.2 Fatigue due to task load or duration · 3.3 Fatigue due to lack of rest · 3.4 Fatigue due to sensory overload · 3.5 Exposure to health hazard · 3.6 Exposure to temperature extreme · 3.7 Oxygen deficiency · 3.8 Atmospheric pressure variation · 3.9 Constrained movement · 3.10 Blood sugar insufficiency · 3.11 Alcohol/Drugs/Other Self-Imposed Stress. New sub-code `10.15 Design/MOC Governance — Independent Review Absent` added per D-GAP-R15 (TapRoot MOC-NI influence).
- `immediate_causes.csv` — 52 rows. 28 Substandard Acts (main 1–22 + sub-codes 19.1–19.6 for External Party) + 24 Substandard Conditions (23–46). Extracted from `Ac_09_MSCAT_Training_Tool 2.pdf` p.4 Section E.
- `loss_types.csv` — 7 rows (verbatim DNV 7-category Type-of-Loss).

**Framework enhancements layered in Session 5 Round 21** (from additional reference pack at `Incident investigation/`): causal layering on top of M-SCAT (ABS), ALARP gate on recommendations, multiple-root-causes default rule, Chain of Custody + marine document inventory + evidence preservation deadlines + scene protection + cargo overlay + health/fatigue evidence all expanding the 5-source Evidence Workspace, Tolerable Failure filter, Organisational defence-traps added to bias guards (5 → 8), Corrective/Preventive/Lessons visual taxonomy, Task Triangle depth scoping, People/Process/Plant interrogatory at Phase 5 gate, Pareto pre-screening panel, Safeguard-failure interrogatory deepening Barrier tool, witness read-back + sign-off, formal/informal interview flag, Risk & Change Management HF domain, near-miss Low vs High priority triage, IMO SMC/MC/MI classifier as separate field (band deadlines stay). See SSOT §6 decisions D-GAP-R01..R23 for the binding spec.
