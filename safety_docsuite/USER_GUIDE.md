# VIMS Safety Module — User Guide

> **Version:** 1.0
> **Last Updated:** 2026-04-17
> **Status:** End-user procedural documentation — ready for V1 rollout
> **Authority:** `APP_FLOW.md` (routes, screen states) · `PRD.md` (FEAT-SAF-* features) · `VALIDATION_RULES.md` (V-* error codes) · `VIMS-SAFETY-MODULE-SSOT.md` §6 (D-* / D-GAP-* decisions)
> **Audience:** Shipboard crew (Master, CO, CE, SO, HOD, any reporter) and shore staff (DPA, FM, TD, HOD)

This guide tells each role exactly what to do, screen by screen. Every step names the route (`/safety/...`) that `APP_FLOW.md` documents so you can cross-check. Every rule cites the decision (D-GAP-*, D-*) that locks it. Nothing here contradicts the locked spec — if it does, the SSOT wins.

---

## Table of Contents

1. [Glossary of Roles & Terms](#1-glossary-of-roles--terms)
2. [First-Time Login Walkthrough](#2-first-time-login-walkthrough)
3. [Reporter — Any Crew Member](#3-reporter--any-crew-member)
4. [Shipboard HOD — Chief Officer / Chief Engineer / Department Senior](#4-shipboard-hod)
5. [Safety Officer — The SOI Procedure](#5-safety-officer--the-soi-procedure)
6. [Master — Captain](#6-master--captain)
7. [Shore DPA — Designated Person Ashore](#7-shore-dpa--designated-person-ashore)
8. [Shore FM — Fleet Manager](#8-shore-fm--fleet-manager)
9. [Mobile & Tablet Tips](#9-mobile--tablet-tips)
10. [Common Error Messages](#10-common-error-messages)
11. [Escalation Paths & Timeline Extensions](#11-escalation-paths--timeline-extensions)
12. [Appendix A — Route-to-Role Index](#12-appendix-a--route-to-role-index)

---

## 1. Glossary of Roles & Terms

Expanded on first use per the VIMS Safety docsuite glossary. Subsequent occurrences use the acronym only.

| Term | Expansion |
|------|-----------|
| **DPA** | Designated Person Ashore (ISM Code 2010 amendments §4) — shore-based owner of the investigation lifecycle. |
| **FM** | Fleet Manager — shore-based commercial + budget authority; RED-band incident closer. |
| **TD** | Technical Director — shore executive; read-only on V1 Safety screens. |
| **HOD** | Head of Department — on the vessel, this is the CO (deck) or CE (engine); onshore, it is the shore-side department head (e.g., HSE Manager). |
| **CO** | Chief Officer — default SO per KSM SSQE Manual Rev 01 Feb 2026 §4.5.1. |
| **CE** | Chief Engineer. |
| **SO** | Safety Officer (SOLAS Reg VI, COSWP 2026 Ch 13). In V1, CO is SO by default; Master may toggle 2/E as alternate SO (D-SOI-02). |
| **PIC** | Person-in-Charge (Vessel Superintendent) — shore side, default closer for GREEN incidents + PIC on Near Miss (LOW). |
| **SCM** | Safety Committee Meeting — Regular (monthly) and Ad-Hoc (host-triggered by Master or CO). Office Comment closes the meeting. |
| **SOI** | Safety Officer Inspection — 13-area paper-first quarterly-cycle inspection. |
| **MoC** | Management of Change. |
| **RCA** | Root Cause Analysis — VIMS uses the DNV M-SCAT taxonomy. |
| **CA / PA** | Corrective Action / Preventive Action. |
| **ALARP** | As Low As Reasonably Practicable — gate on every RED/YELLOW System-Action recommendation (Round 21 R02). |
| **SMC / MC / MI** | Serious Marine Casualty / Marine Casualty / Marine Incident — IMO Casualty Investigation Code Resolution MSC.255(84). |
| **SSQE** | Safety, Security, Quality & Environment — KSM Manual Rev 01 Feb 2026. |
| **WRH / CMS / PMS** | Work & Rest Hours module / Crew Management System / Planned Maintenance System (decoupled — D-GAP-I1). |

Never used in this system: "Acting-DPA", "Acting-CO", "Deputy FM", "MD escalation" — these concepts **do not exist**. Role persists, the person filling it changes via normal crew rotation (D-GAP-A3 / A4). Where absence is an issue, the VIMS timeline-extension procedure is the only escape valve (D-GAP-B2). See [§11](#11-escalation-paths--timeline-extensions).

---

## 2. First-Time Login Walkthrough

### 2.1 Access the Safety Module

1. Log in to VIMS at your normal entry point (same JWT / SimpleJWT session as Reporting, WRH, and Purchase).
2. Look for the **Safety** group in the left sidebar. The group appears only if your VIMS profile has any `SAF_F_*` form permission (form IDs live in `msc_profiles`; the sidebar uses `PermissionGate`). If you do not see it, ask your DPA to grant the appropriate permission.
3. The Safety landing opens at `/safety/dashboard/` by default. Shore roles (DPA / FM / TD / HOD-shore) see fleet-wide tiles; ship roles see their assigned vessel only.

### 2.2 Set Notification Preferences

Safety uses the shared `master_notification` channel. You do not maintain a separate preference table for Safety.

1. Open your user profile (top-right avatar).
2. Select **Notifications**.
3. Under **Safety**, confirm the channels you want for each event category:
   - Incident assignment / state change
   - Near Miss triage needed (DPA only)
   - SCM meeting created / Office Comment required
   - SOI 80-day / 90-day compliance alerts
   - CA due / overdue
4. Save. Changes apply immediately.

### 2.3 Vessel Scope

- **Shore users** — your vessel scope comes from `master_RoleByVessel`. You see only vessels assigned to your role profile. Fleet roles (DPA, TD) typically see all.
- **Ship users** — your scope comes from `Crew_Onboarding_History`. You see only the vessel you are currently assigned to. When you sign off, the scope drops automatically on next login.

---

## 3. Reporter — Any Crew Member

> **Who this is:** Any rated or unrated crew member. Any rank can create a Near Miss (D-RBAC-11 / `SAF_P_001` on `SAF_F_002`). Only Master / CO / CE / 2/E may create a formal Incident; all others contribute witness statements inside an Incident created by the top-4.

### 3.1 Day in the Life — Reporter

You see a near miss during routine cargo watch. Before the end of the watch you want it on record. You open VIMS on the mess-room tablet, tap **Safety → Near Miss → New Near Miss**, type 80+ characters of description, attach a photo, submit. You receive a confirmation toast with the Near Miss reference number. Your Master does **not** see your name on the report. The DPA will triage it within 48 hours. If it is HIGH priority, the DPA issues a fleet alert within the week; if LOW, the PIC closes it after review. You receive a notification when your report is triaged.

### 3.2 Reporting an Incident (when you are in the top-4 rank)

**Entry point:** Safety sidebar → **Incidents** → **New Incident** button (`/safety/incidents/create/`). Available only to Master, CO, CE, 2/E.

Step-by-step:

1. On `/safety/incidents/create/` (Phase 1 — Intake + Scene Control), fill:
   - **What happened** — free-text narrative (minimum 200 characters; enforced by `V-INC-001`).
   - **When and position** — date, time, Latitude, and Longitude. Report time appears beside Shore Assistance Required. Latitude and Longitude appear together on their own row.
   - **Office communication** — answer **Was office informed?**. If Yes, select how it was informed: On call or On email.
   - **Reporting context** — Shore Assistance Required, Location of Vessel, Location on Board, Departure Date, and Vessel Condition. Shore Assistance Required is beside Report time; the remaining reporting-context fields appear below the coordinates. These are stored on the incident report and are used for both incident and injury reporting. Last Port is not shown in the current form.
   - **Weather Condition** — record weather and sea details. Ice condition on-board and Ice condition at sea are not shown in the current form.
   - **Incident type** — picked from `master_safety_incident_type` (32 active options; retired earlier options such as `Missing vessel` are not offered).
   - **Injury Details** — optional. Select `Crew` for crew injury and fill rank, age, and `Type of Activity`. Select `Non-crew` for pilot/contractor/shipyard/passenger injuries and fill the existing person/company/type/injury-level fields. In crew injury, choose `Type of Activity`, nature of injury, source of injury, and affected body area from the dropdowns; select `Others(Specify)` when the required value is not listed. Estimated cost details are optional: select Yes to open the cost fields, or No to continue without them.
   - **Scene control** — confirm the area is secured per SSQE §11.
2. Tap **Save Draft**. System issues a draft reference `DRAFT-{VslCode}/{YYYY}/T{nnn}` (D-GAP-C1).
3. Attach evidence under **Phase 4 → Documents** if photos, logs, VDR exports, or other proof are immediately available. You do not need to finish Phase 2 or Phase 3 before saving these documents.
4. When ready, tap **Continue to Phase 2** — `/safety/incidents/:id/phase-2/`.
5. Phase 2 is **Notifications + Resource Allocation**. You:
   - Select **IMO classification** (SMC / MC / MI) per the IMO Casualty Investigation Code MSC.255(84) picklist — this is a regulatory field (FEAT-SAF-INC-002).
   - Select **Internal risk band** (GREEN / YELLOW / RED) per D-DNV-02 — this is a company field separate from the IMO classifier.
   - Confirm notification list (PIC + DPA + safety-channel — auto-populated).
6. Tap **Submit to office**. The system assigns the formal reference `{VslCode}/{YYYY}/{NNN}` (gap-free), routes to `/safety/incidents/:id/phase-3/`, and fires notifications to PIC + DPA via `master_notification` (FEAT-SAF-XMOD-006, D-GAP-F2).
7. After Phase 2 submission, the investigation workspace is driven by the Master (lead for GREEN / YELLOW) or the shore team (RED). You continue contributing witness statements and evidence when asked.

Until office approval, authorized users can return to saved incident details and correct them. User-facing investigation phases are flexible: RCA, Corrective Action, Preventive Action, Evidence Documents, and Witness Statements can be opened and saved even when the formal workflow has not yet moved to that legacy backend phase number. Moving from one phase to the next does not make earlier phases read-only. Phase 2 saved Immediate Cause and Root Cause cards include **Edit**, which loads the existing cause into the form and updates that same saved cause. Phase 3 Corrective Action, Phase 4 Preventive Action, and Phase 5 Add Evidence saved cards also include **Edit** and update the existing saved row instead of adding a duplicate. The former Lessons Learned screen is removed from the current workflow; its old URL redirects to Office Review. The Phase 1 edit page loads the saved report and **Save changes** writes back to the incident; leaving the injury section unchanged does not remove a saved injury record. Once office approves, closes, or supersedes the incident, the record is locked for normal phase edits.

### 3.3 Reporting a Near Miss

**Entry point:** Safety sidebar → **Near Miss** → **New Near Miss** (`/safety/near-miss/create/`). Any crew member can use this (`SAF_P_001` scoped to `SAF_F_002`).

Step-by-step:

1. On `/safety/near-miss/create/`:
   - **What happened** — free-text description (minimum 100 characters; enforced by `V-NM-001`).
   - **Where** — location picklist.
   - **Photo** — mandatory for HIGH severity; optional otherwise.
   - **Category** — one user-facing dropdown that combines the old Category and Possible Loss Type options.
   - **Factor causes** — select Immediate Cause and Root Cause for Human Factors, Vessel Factors, Management Factors, and Other Factors. Use `Not Applicable` where a factor does not apply. Use `Other` only when no dropdown option fits, then type the custom text.
2. There is no daily Near Miss submission cap. While submission is running, the button shows **Processing** so users do not click multiple times and create duplicates.
3. Tap **Submit**. System routes to `/safety/near-miss/:id/` with confirmation and the Near Miss reference number.

### 3.4 Reporter Identity (D-GAP-J1 revised)

When you file a Near Miss, the system stores your name, rank, and user reference for follow-up and audit. Anonymous reporting is removed from V1.

| Who is looking at your report | Sees your name? |
|-------------------------------|-----------------|
| You (yourself) | Yes — full name |
| **DPA (shore)** | **Yes — full name** |
| **FM (shore)** | **Yes — full name** |
| Master | Yes — full name within vessel scope |
| HOD / CO / CE | Yes — full name within vessel scope |
| SO | Yes — full name within vessel scope |
| TD / authorized shore user | Yes, where vessel scope and Safety permission allow |
| PDF exports | Prints reporter details for authorized viewers; no anonymous/masked wording |

The UI and PDF must not display `Anonymous Reporter`, `identity withheld`, or `Reporter identity is masked`.

### 3.5 What Happens After You Submit?

| Record type | Who reviews next | Expected timeline | Where to track |
|-------------|-------------------|-------------------|----------------|
| Incident (Phase 1 + 2 submitted) | Master leads GREEN/YELLOW investigation; FM leads RED (D-GAP-M06) | Phase 3 within 24 h of Phase 2 submit | `/safety/incidents/:id/` — your phase indicator moves right |
| Near Miss LOW | PIC closes after review | Usually within 7 days | `/safety/near-miss/:id/` |
| Near Miss HIGH | DPA triage → fleet alert if appropriate | Triage within 48 h; fleet alert 5–7 days | `/safety/near-miss/:id/` + fleet circular |
| Witness statement | Investigation lead assembles facts (Phase 4) | Depends on band | Referenced inside Incident Phase 3 |

You will receive a `master_notification` when state changes materially (triage complete, closed, re-opened).

### 3.6 Reporter Routes at a Glance

| Route | Purpose |
|-------|---------|
| `/safety/dashboard/` | Vessel-scoped dashboard (read). |
| `/safety/incidents/` | Incident list — read-only for non-top-4. |
| `/safety/incidents/create/` | Create new Incident (top-4 only). |
| `/safety/incidents/:id/` | Incident detail landing. |
| `/safety/near-miss/` | Near Miss list. |
| `/safety/near-miss/create/` | Create new Near Miss. |
| `/safety/near-miss/:id/` | Near Miss detail — your identity visible only to DPA/FM/yourself. |

---

## 4. Shipboard HOD

> **Who this is:** Chief Officer (deck HOD), Chief Engineer (engine HOD), or other department senior acting in the HOD slot. The CO defaults to Safety Officer (SSQE §4.5.1). This section covers the HOD's investigation and signature responsibilities; see [§5](#5-safety-officer--the-soi-procedure) for CO's SO-specific duties.

### 4.1 Day in the Life — HOD (Chief Officer)

You see a draft incident notification at 07:10. The Master opened it at 06:40 after a crane-wire pre-tension parted on #3 cargo hold. By 08:00 you are at your workstation reviewing evidence documents and witness statements. The Master records Corrective Action and Preventive Action on separate action screens; you counter-sign the HOD signature block once the Master has signed and before the DPA closes. Your name + timestamp + device fingerprint lock the HOD signature (D-GAP-D1).

Current Witness Statement update: the Phase 4 Witness Statement screen no longer asks users to flag statements as FORMAL, type a separate witness-statement text field, or complete read-back/copy-to-witness controls. Choose a crew witness from the vessel list or select Other and type the name, enter a Remark, and use Upload witness statement when a statement file/image is available.

### 4.2 Reviewing Incoming Incident Reports

Entry point: Safety sidebar → **Incidents** (`/safety/incidents/`).

1. The list shows columns `Ref No | Vessel | Date | Type | SMC/MC/MI | Band | Phase | Closer | Updated`. Filter by band, classification, or phase.
2. Click a row to open `/safety/incidents/:id/`. The landing tab shows the current phase + bias-guard status.
3. Read the Phase 1 intake narrative, Phase 2 classifier + band rationale, and the evidence gathered so far.
4. If a correction is needed before office approval, open the relevant earlier phase and edit it directly. A formal send-back is not required just because the incident has moved forward.

### 4.3 Contributing to Investigation Phases

**Phase 2 - RCA (Root Cause Analysis)** (`/safety/incidents/:id/phase-2/`):

1. Add at least one Immediate Cause and one Root Cause using the visible cause dropdowns.
2. After a cause saves, the page shows a success message and moves to the Saved causes area so you can immediately review the saved cause.
3. To correct a saved cause, use **Edit** on that cause card. The form is filled with the saved values; **Update** changes the existing card instead of adding a duplicate.

**Current action phases (CR-038, superseded by CR-042 for Lessons Learned):**

1. **Phase 3 - Corrective Action** (`/safety/incidents/:id/phase-3/`) captures the corrective action description and due date. The old owner/checker card is not shown.
2. **Phase 4 - Preventive Action** (`/safety/incidents/:id/phase-3/preventive/`) captures Description, Due date, and one shared **How much will this reduce risk?** answer for the screen. It does not ask for Remaining risk, the "I confirm this will reduce risk" checkbox, theme, effort, or "Prevent It Happening Again" wording, and saved preventive cards do not repeat risk reduction per row.
3. The former **Lessons Learned** screen is removed from current navigation. Its old URL redirects to Office Review.
4. Each save shows a success message and moves to the saved item so users can review what was saved.
5. To correct a saved corrective or preventive action, use **Edit** on that saved card. The form is filled with the saved values; **Update** changes that existing item instead of adding a duplicate. The preventive risk-reduction answer remains a shared screen-level field.

**Phase 4 — Evidence Workspace** (`/safety/incidents/:id/phase-4/`):

1. Open **Documents** (`/safety/incidents/:id/phase-4/paper/`) whenever evidence is available. Documents can be added before Phase 2 or Phase 3 are completed; official phase submit steps still move in order.
2. Add one evidence entry with **Attachment**, **Title**, and **Description**. Repeat the same form for as many attachments as needed.
3. Use the title to name what the attachment is, and use the description to explain why it matters.
4. After a document or witness statement saves, the page shows a success message and moves to the saved-content area so you can immediately review the saved entry.
5. Click **Witness Statement** when a statement needs to be recorded; it opens the witness statement page directly with no extra **Open Witness Statement** step. Choose a crew witness from the incident vessel list or select **Other** and type the name, add a Remark, and upload the witness statement when available. Evidence Check is not part of the current Phase 4 screen.
6. To correct a saved document title/description or saved Witness Statement, use **Edit** on that saved card. Document Edit keeps the original file and updates only the metadata; Witness Statement Edit updates the same witness row.
7. Every fact you record must link to ≥1 evidence row (assumption-bias guard `V-INC-041` / D-DNV-11 #2).

**Legacy combined action screen (superseded by CR-038)** (`/safety/incidents/:id/phase-3/`):

1. This older combined view is superseded by the current separate Corrective Action and Preventive Action screens above.
2. Do not use this legacy wording as current user guidance for owner/checker fields or remaining-risk confirmation.

**Legacy analysis tools**:

1. Older DNV analysis tools remain background/compatibility material only.
2. Current users complete RCA on Phase 2, Corrective Action on Phase 3, Preventive Action on Phase 4, and then continue to Office Review.
3. The current `/safety/incidents/:id/phase-5/` route is **Office Review**, not an analysis workspace.

### 4.4 Recommending Corrective / Preventive / Lessons

**Legacy recommendations screen (superseded by CR-038)** (`/safety/incidents/:id/phase-6/`):

1. Three tiers are **mandatory** for YELLOW / RED closure (`V-INC-064` / D-GAP-R13):
   - ≥1 **Corrective Action** (fix this incident's root cause)
   - ≥1 **Preventive Action** (prevent recurrence on the same or sister vessel)
   - ≥1 **Lessons Learnt** (knowledge-capture item, surfaces in SCM + dashboards)
2. Each System-Action recommendation needs ALARP attestation (Round 21 R02 / `V-INC-065`).
3. For each Corrective Action that requires a purchase, click **[Link Purchase Req]** — this opens Purchase in a new tab with the `linked_safety_ca` parameter (see [§8.2](#82-budget-approval-on-corrective-action)). The CA→Purchase Req link is a hard FK; the requisition cannot be archived while an open CA is linked (D-GAP-M12).

### 4.5 Signature in the Chain

Signature sequence is **Reporter → Master → HOD → DPA → FM** (as applicable by band). Enforcement:

- You cannot sign until the Master has signed (`V-INC-071`).
- Your signature is typed name + ISO-8601 timestamp + device fingerprint (D-GAP-D1 hybrid model).
- For flag-state hand-off PDFs, a wet-signed scan may be attached separately (not a replacement).

| Band | Signature chain | HOD slot |
|------|------------------|----------|
| GREEN Incident | Reporter → Master → HOD → PIC | Phase 6 closure review |
| YELLOW Incident | Reporter → Master → HOD → DPA | Phase 6 closure review |
| RED Incident | Reporter → Master → HOD → DPA → FM | Phase 6 closure review |

### 4.6 HOD Routes at a Glance

| Route | Purpose |
|-------|---------|
| `/safety/incidents/` | Incident list |
| `/safety/incidents/:id/phase-4/people/` | Interview input |
| `/api/safety/incidents/:id/phase-4/chain-of-custody/` | Chain-of-custody ledger |
| `/safety/incidents/:id/phase-3/` | Corrective Action |
| `/safety/incidents/:id/phase-3/preventive/` | Preventive Action |
| `/safety/incidents/:id/phase-3/lessons/` | Legacy redirect to Office Review |
| `/safety/incidents/:id/phase-5/analysis/*` | Analysis tools + Human Factors |
| `/safety/incidents/:id/phase-6/` | Loss Evaluation |
| `/safety/scm/:id/` | SCM read + HOD department input |

---

## 5. Safety Officer — The SOI Procedure

> **Who this is:** The onboard Safety Officer, per SOLAS Reg VI and COSWP 2026 Ch 13. In V1, CO is SO by default (SSQE §4.5.1); Master may toggle 2/E as alternate SO via the `CO_ON_LEAVE` flag (D-SOI-02). There is no separate rank and no "Acting-SO" concept (D-GAP-A3 / A4).

### 5.1 Day in the Life — SO (Chief Officer in the default configuration)

It is the second Tuesday of the month. You have two SOI areas due per the 3-monthly cycle. You open VIMS on your tablet, tap **Safety → SOI → New SOI**, pick Area 3 (Mooring Deck) and Area 7 (Galley), add a cross-departmental assistant from CMS (the 3/E), and assign the Deck Cadet as a trainee. You hit **Save & Continue to Download**, pick PDF, the paper is generated with a unique checklist ID on every page. You print two copies, file one in the SMS pending-inspection tray, and take the other out on deck for the Mooring area. You walk the mooring deck with the 3/E, tick Yes/No on paper for all 23 items under Area 3, note four findings in the margins. After the walk you return to your cabin, open VIMS, go to `/safety/soi/:id/findings/create/`, enter the unique checklist ID, register each of the four findings digitally (one with a photo, marked HIGH severity). You file the signed paper in the ship's SMS filing cabinet. You do **not** scan or upload anything (D-GAP-E4 / D-GAP-E5). The Master approves closure at month-end.

### 5.2 Paper-First SOI Walkthrough — The 4 Steps (D-GAP-E4)

Paper-first means: the system generates the checklist → you download and work on paper → paper is filed in the ship SMS filing system → you register digital findings linked by unique ID. **There is no scan upload step. There is no digital per-item Yes/No tick.** The paper record is authoritative and PSC/auditor-available on demand (D-GAP-E5).

| Step | What you do | Route | System state transition |
|------|-------------|-------|-------------------------|
| **1. Pick areas + generate unique-ID checklist** | Select the areas to inspect, assign cross-departmental assistant, assign up to 3 trainees. System issues a unique checklist ID. | `/safety/soi/create/` → `/safety/soi/:id/pick-areas/` | `Draft` → `Ready-to-Download` |
| **2. Download paper (PDF or Excel)** | Choose PDF or Excel format. The unique checklist ID prints on every page. Print the document. | `/safety/soi/:id/download/` | `Ready-to-Download` → `Downloaded` |
| **3. Fieldwork on paper** | Walk the area with your assistant. Tick Yes/No on the printed checklist. Note observations + photos in the margin. **File the completed paper in the ship SMS filing system.** No upload. No scan. | Offline (paper) | `Downloaded` (unchanged) |
| **4. Register findings digitally — linked by unique ID** | Return to VIMS. Enter the unique checklist ID. Register each formal finding as a structured row. HIGH severity findings require photo attachment. | `/safety/soi/:id/findings/` + `/safety/soi/:id/findings/create/` | `Downloaded` → `Submitted` (per area) |

### 5.3 Detailed Step-by-Step

#### Step 1 — Pick areas + assistant + trainees

1. Safety sidebar → **SOI** → **New SOI** (`/safety/soi/create/`). Available to SO only (enforced by `SAF_P_001` on `SAF_F_004`).
2. Land on `/safety/soi/:id/pick-areas/`. The screen lists 13 areas filtered by `vims_safety_soi_vessel_area_map.applicable=true` (D-SOI-12):
   - 12 physical areas (including Compressor House — the 12th area added Session 5 Round 21)
   - 1 Section 12 Cross-cutting Safety & Culture area
3. Tick the areas you want to inspect this session. If Section 12 has not been covered in the current 3-month quarter, a banner prompts you to include it (FEAT-SAF-SOI-014). Section 12 runs **once per 3-month cycle**, not monthly.
4. **Assistant picker** — pick one assistant from a different department than yours (SSQE §4.5.2 cross-department rule). The picker enforces this server-side via live CMS join (D-GAP-I2 / D-GAP-M18) — there is no manual override.
5. **Trainees** — assign up to 3 (stored in `vims_safety_soi_trainee`). Trainees shadow the inspection; they do **not** sign anything (D-GAP-M15).
6. Tap **Save & Continue to Download**. State flips to `Ready-to-Download`; unique checklist ID is generated on the server and locked to this SOI event.

#### Step 2 — Download paper (PDF or Excel)

1. Land on `/safety/soi/:id/download/`.
2. Choose format: **PDF** (recommended for print) or **Excel** (recommended if you prefer writing with the laptop). The format choice is a build-time deferral item (#10) — both are supported at launch. The unique checklist ID prints on every page.
3. Tap **Download**. File downloads to your device.
4. Print the document. The printed page is now the authoritative record.
5. State flips to `Downloaded`.

> **Offline-friendly.** Once downloaded, the paper works without internet — the whole point of paper-first. Bring it on deck, into the engine room, into the galley freezer — wherever.

#### Step 3 — Fieldwork on paper

1. Walk the area with your assistant.
2. Tick Yes / No for each item on paper. The standard template carries 329 items across the 13 areas (from `safety-reference-data/soi_checklist_v1.csv` — `master_soi_area_item`, 317 baseline + 12 cross-cutting).
3. Note any observation / photo / measurement in the margins — this is your field notebook.
4. At the end, **sign the paper** (SO signature). Your assistant signs next to yours (D-GAP-M15). Trainees **do not** sign.
5. **File the completed paper in the ship's SMS filing cabinet** per your vessel's SMS index. PSC, class, and auditors have on-demand access to this paper on request (D-GAP-E5).

> **Do not scan and upload the paper.** There is no upload endpoint (D-GAP-E4). If you try to circumvent by sending a scan via email, you create a second source of truth that contradicts the SMS filing system — do not do it.

#### Step 4 — Register findings digitally

1. Return to VIMS → `/safety/soi/:id/findings/` → **[+ Add Finding]** → `/safety/soi/:id/findings/create/`.
2. On the finding create form:
   - **Unique checklist ID** — enter the ID printed on your paper. The system validates it against the SOI event record. Mismatch → rejection.
   - **Area** — picklist of the areas covered in this event.
   - **Item reference** — optional; pick a specific item from the checklist.
   - **Description** — free text of the finding (minimum length enforced client + server).
   - **Severity** — LOW / MEDIUM / HIGH.
   - **Photo** — **mandatory for HIGH severity**. Optional otherwise.
   - **M-SCAT tag** — optional; pick from `master_mscat_taxonomy` (174 rows).
3. Save. The finding is added to `vims_safety_soi_finding`. Each finding is a structured row — there is no per-item Yes/No column because that data lives on the paper.
4. Repeat for each finding.
5. When all findings are logged for an area, mark the area **Submitted**. State: `Downloaded` → `Submitted`.
6. When all picked areas are `Submitted`, the event state becomes **Pending Closure**; the Master receives a notification to approve closure (see [§6.4](#64-approving-soi-closure-findings)).

### 5.4 Section 12 — Cross-cutting Safety & Culture

Section 12 is the 13th area — cross-cutting Safety & Culture observations that do not belong to a single physical area. It runs **once per 3-month cycle**, not monthly (FEAT-SAF-SOI-014). The create screen prompts you if the quarter's Section 12 has not been covered yet. Section 12 feeds the SOI Compliance % dashboard (see next subsection) distinctly from the 12 physical areas.

### 5.5 SOI Compliance % — The Metric

The dashboard tile and the SOI list state pill read **"SOI Compliance %"** — never "Inspection Compliance %" (D-GAP-DESIGN-01). This naming avoids clash with the existing PSC Inspection-module metric of the same name.

- **GREEN** — area last inspected within the 3-monthly cadence.
- **AMBER** — area overdue by ≥80 days since last inspection (FEAT-SAF-SOI-005).
- **RED** — area overdue by ≥90 days.

Amber / red do not auto-escalate to FM or MD — they surface as dashboard flags; DPA judgement governs, and the VIMS timeline-extension procedure handles approved overruns (D-GAP-F3 / D-GAP-B2).

### 5.6 Trainee Assignment (up to 3)

Trainees are stored in `vims_safety_soi_trainee` per event. Pick their names in Step 1 from the CMS crew roster (live join via `Crew_Onboarding_History`). Up to 3 per SOI event. Trainees shadow — they do not sign paper, do not register findings, do not approve. The trainee-rotation coverage % formula is a build-time deferral (#11) — final definition lands at Phase 4 build.

### 5.7 SO Routes at a Glance

| Route | Purpose |
|-------|---------|
| `/safety/soi/` | SOI list + "SOI Compliance %" tiles |
| `/safety/soi/create/` | Step 1 — pick areas + assistant + trainees |
| `/safety/soi/:id/pick-areas/` | Area selection + Section 12 prompt |
| `/safety/soi/:id/download/` | Step 2 — download paper (PDF or Excel) |
| `/safety/soi/:id/findings/` | Step 4 — findings list |
| `/safety/soi/:id/findings/create/` | Register a finding (unique-ID gated) |
| `/safety/soi/:id/findings/:findId/` | Finding detail + SO→Master closure flow |
| `/safety/soi/:id/close/` | SOI event close (after Master approval) |
| `/safety/soi/:id/pdf/` | SOI Summary PDF |

---

## 6. Master — Captain

> **Who this is:** The vessel Master. Top of the shipboard RBAC tree. Signs off on every formal safety record. Only the Master can call an Ad-Hoc SCM.

### 6.1 Day in the Life — Master

Your day begins with the dashboard tile on `/safety/dashboard/`. You have one YELLOW incident awaiting Office Review, one SCM due in 3 days, two SOI areas in `Pending Closure`, and zero open Near Misses on your vessel. You tap the YELLOW incident, review the saved RCA/actions/evidence, sign where required, then route the record to the DPA. You call the CO to review the SOI closure items, approve both. You glance at the fleet-wide closed incidents tab (your cross-vessel read access per D-RBAC-09) to see what sister vessels have closed this month. By 11:00 you have cleared your Safety queue.

### 6.2 Signature Authority in Every Flow

| Record type | Master's signature point | Chain position | Validation rule |
|-------------|--------------------------|----------------|-----------------|
| Incident (GREEN) | Phase 6 (before PIC closure) | After Reporter, before HOD | `V-INC-070` (cannot sign before Reporter) |
| Incident (YELLOW) | Phase 6 (before DPA closure) | After Reporter, before HOD | `V-INC-070` / `V-INC-071` |
| Incident (RED) | Phase 6 (before DPA + FM closure) | After Reporter, before HOD | `V-INC-070` / `V-INC-071` |
| Near Miss (LOW) | — (PIC closes) | Reporter only below | n/a |
| Near Miss (HIGH) | After Reporter, before HOD → DPA | Fleet-alert chain | D-GAP-J1 (reporter identity masked to you) |
| SCM Regular | Host/preparer is Master or CO; office adds Office Comment to close | No digital SCM signature | `SAF_F_003` |
| SCM Ad-Hoc | Host/preparer is Master or CO; office adds Office Comment to close | No digital SCM signature | D-GAP-M-ADHOC |
| SOI event | Digital counter-signature at approval (not on paper) | After SO + Assistant paper | D-GAP-M15 |
| SOI finding closure | Approve per D-SOI-07 | After SO | `SAF_P_004` on `SAF_F_004` |
| SOI area-applicability false | Request (DPA approves) | Two-party | D-GAP-M19 |

Incident and SOI signature type: typed name + ISO-8601 timestamp + device fingerprint (D-GAP-D1). SCM does not capture digital signatures; its PDF prints blank Master and CO signature lines for record copy.

### 6.3 Triggering an Ad-Hoc SCM (D-GAP-M-ADHOC)

**What it is:** An additional Safety Committee Meeting beyond the monthly cadence, called by Master or CO for major incidents or important safety information. Same form and PDF as a Regular SCM, but tagged `meeting_type = 'AD_HOC'`. Aligns with SSQE Manual Rev 01 Feb 2026 §9 provisions.

**When to call one:**

- A RED-band incident has occurred and you need to brief the crew before the monthly SCM.
- A fleet alert from the DPA requires an immediate onboard discussion.
- A significant Near Miss indicates a systemic condition on your vessel.
- Any other significant safety information you judge material enough to not wait.

**How to trigger — step by step:**

1. Safety sidebar → **SCM** → choose **Ad-Hoc SCM** in the **Meeting to host** dropdown → **Host meeting** (`/safety/scm/create-adhoc/`). Available to Master and CO (enforced by `SAF_P_001` on `SAF_F_003` with `meeting_type = 'AD_HOC'`).
2. Enter:
   - **Trigger reason** — free text (e.g., "RED-band fall-from-height incident 2026-04-17 — crew brief before full investigation completes").
   - **Scheduled date/time** — when the meeting will run.
   - **Agenda** — draft items (you can edit until office adds Office Comment).
   - **Attendee picklist** — pre-populated from CMS crew roster, WRH-checked.
3. Check the **WRH readiness** card. The SCM can be hosted only when ship time is configured and every roster crew member has available, compliant WRH data.
4. Save Draft. System creates the SCM record with `meeting_type = 'AD_HOC'`. If WRH readiness is not clear, the host action is disabled and the backend rejects creation until the warning is fixed.
5. At meeting time, go to `/safety/scm/:id/`, run through agenda, record Suggestions / Recommendations in `/safety/scm/:id/agenda/`.
6. Office adds Office Comment on the SCM detail page. Saving Office Comment closes the meeting. WRH badges and overdue SOI items are warnings only and do not block closure after the meeting exists.

> **An Ad-Hoc SCM does NOT replace the monthly Regular SCM.** The cadence counter + Closed-Since-Last-SCM snapshot anchors on **last SCM closure timestamp regardless of type** (D-GAP-M-ADHOC). If the Ad-Hoc happens on the 15th, your Regular is still due 30 days after that.

### 6.4 Regular SCM Chairing (SSQE §9)

1. Master or CO prepares the draft at `/safety/scm/create-regular/` using the **Meeting type** selector (D-RBAC-06). Confirm the **WRH readiness** card is clear before hosting; missing ship time, missing WRH rows, or non-compliant crew blocks SCM creation.
2. You attend the scheduled meeting. The system auto-assembles on `/safety/scm/:id/` after the meeting is created:
   - **Closed-Since-Last-SCM** block — SOI findings + Near Miss + Incident records closed since prior SCM closure timestamp (`/safety/scm/:id/closed-since-last/`, D-GAP-M22).
   - **Safety Observations** — auto-filled from open SOI findings (FEAT-SAF-SOI-020 / `/api/safety/soi/open-findings/`).
   - **Attendance** — WRH join; per-row badges + tooltip (D-GAP-M11 / D-GAP-M26).
   - **Agenda** — 10-section template derived from legacy `vw_GetSCM_Master`.
3. Chair the discussion. Record Suggestions / Recommendations under `/safety/scm/:id/agenda/`.
4. Use **Edit Meeting** if any correction is needed. Editing is allowed only until office saves Office Comment.
5. Download the SCM PDF from `/safety/scm/:id/pdf/`. The PDF is available after meeting creation and includes the 10-section layout, attendance + WRH badges inline, and blank Master/CO signature lines.
6. Office saves **Office Comment** on the SCM detail page. This closes the meeting and stops further vessel edits.

### 6.5 Approving SOI Closure & Findings

When all picked areas on an SOI event reach `Submitted`, the event moves to `Pending Closure` and you receive a notification.

1. Open `/safety/soi/:id/`. Review findings at `/safety/soi/:id/findings/`.
2. For each finding, drill into `/safety/soi/:id/findings/:findId/` and approve closure (`SAF_P_004` on `SAF_F_004`, per D-SOI-07).
3. If you believe an SOI area does not apply to your vessel (e.g., no Compressor House on a bulk carrier variant), navigate to `/safety/soi/:id/applicability/request/` and file a request — the DPA approves at `/safety/soi/:id/applicability/approve/` (D-GAP-M19). Both signatures + reason land in `vims_safety_soi_applicability_log`.
4. Once all findings are approved, close the event at `/safety/soi/:id/close/`. SOI Summary PDF generates at `/safety/soi/:id/pdf/`.

### 6.6 Approving Incident Findings Before Shore Escalation

At the action-check stage you review the saved corrective/preventive action entries, causal layering, and the 8 bias guards. Before you sign the Master block:

1. Check that action recommendations are recorded before Office Review (`V-INC-064`).
2. Check ALARP attestation on every System-Action (`V-INC-065` / Round 21 R02).
3. Check the 8 bias guards are attested (5 DNV + 3 organisational defence-traps per D-GAP-R12 / `V-INC-055`).
4. Sign. The record routes to the DPA for Office Review (`/safety/incidents/:id/phase-5/`). RED records route to DPA then FM (D-GAP-M06).

### 6.7 Fleet-Wide Read Access

You have fleet-wide read-only access to **closed** incidents on sister vessels (D-RBAC-09). Use this to learn from fleet-wide events. Open `/safety/incidents/` and remove the vessel filter; closed records on other vessels are visible read-only.

### 6.8 Master Routes at a Glance

| Route | Purpose |
|-------|---------|
| `/safety/dashboard/` | Fleet dashboard (your vessel default; cross-vessel read) |
| `/safety/incidents/:id/phase-6/` | Loss Evaluation |
| `/safety/scm/create-adhoc/` | Host Ad-Hoc SCM (D-GAP-M-ADHOC) |
| `/safety/scm/:id/` | SCM detail, Edit Meeting, Office Comment, PDF download |
| `/safety/soi/:id/findings/:findId/` | Approve SOI finding closure |
| `/safety/soi/:id/applicability/request/` | Request area non-applicability |
| `/safety/soi/:id/close/` | Close SOI event |

---

## 7. Shore DPA — Designated Person Ashore

> **Who this is:** The Designated Person Ashore per ISM Code 2010 amendments §4. Owns the investigation lifecycle from shore. One of only two roles (along with FM) that can see Near Miss reporter identity.

### 7.1 Day in the Life — DPA

You arrive at your desk at 07:30. One incident closed overnight on MV Alpha — you do the Office Review acceptance. Two Near Misses were filed in the last 24 hours — you triage both, mark one HIGH (a mooring rope tension reading + crew fatigue signal), prepare the Circular/Alert handoff from `/safety/near-miss/:id/fleet-alert/`, complete the remaining Circular fields in the Circular module, then record the Near Miss fleet-alert step as issued. You open the Safety Intelligence Dashboard at `/safety/dashboard/`, check the Pareto of root causes across the fleet, notice the 10.15 Design/MOC Governance category creeping up. You open the taxonomy admin at `/safety/admin/mscat/` and check the case-study repository. Before lunch you approve two SOI area-applicability requests from Masters. Afternoon is a cross-vessel lessons-learned digest export from the dashboard.

### 7.2 Owning the Investigation Lifecycle

The DPA is a lead authority at every Incident investigation phase. Under the current CR-044 authority model, PIC and DPA can accept, close, or send rework for every risk band:

| Phase | DPA role |
|-------|----------|
| Phase 1 — Intake | Monitor; receive notifications via `master_notification` |
| Phase 2 — Classification + band | Review IMO classifier + internal band |
| Phase 4 — Evidence | Comment; request more evidence; enforce chain-of-custody (D-GAP-R04) |
| Phase 3 — Corrective Action | Review corrective action |
| Phase 4 — Preventive Action | Review preventive action |
| Legacy Lessons route | Redirects to Office Review; not a current DPA work step |
| Legacy analysis tools | Background compatibility only; not a current visible phase |
| Phase 7 — Loss Evaluation | Ship-side or office-side users save final risk, loss, repair/injury, and cost evaluation before office closure |
| **Phase 6 — Office Review** | **Enter Office Comments/lesson learnt, accept, or send for rework** at `/safety/incidents/:id/phase-5/` |
| Legacy follow-up verification | Compatibility route only; current visible Phase 7 is Loss Evaluation |
| Closure | YELLOW band — sign and close. RED band — hand to FM. |

### 7.3 Near Miss Triage — DPA Only

Entry point: Safety sidebar → **Near Miss** → click a LOW-triage item → `/safety/near-miss/:id/triage/`.

1. Review the reporter's description, attached photo, category, and factor causes.
2. Read the reporter's identity where vessel scope and Safety permission allow.
3. Set priority LOW or HIGH (D-GAP-R22). If HIGH, proceed to fleet alert at `/safety/near-miss/:id/fleet-alert/`.
4. Fleet alert payload auto-drafts with vessel + crew names anonymised per D-GAP-M08. Review and edit the alert text and fleet-learning text.
5. Use **Issue Circular/Alert** when you want the same alert prepared in the Circular module. The Circular page opens with only the title and body prefilled; complete recipients, category, priority, attachments, and publish there as normal (FEAT-SAF-NM-006 / D-CFG-04).
6. Use **Issue fleet alert** in Near Miss to record that the HIGH-priority fleet-alert requirement is complete. This is separate from the Circular module publish action.

### 7.4 Reporter Identity View (D-GAP-J1 revised)

Near Miss reporter identity is visible to authorized users within vessel scope. The anonymous/masked reporter concept is removed from V1.

**What this means for your work:**

- You can talk to the reporter directly if follow-up is needed.
- Master and authorized vessel/office users can see reporter details where their vessel scope allows it.
- PDFs must not print `Anonymous Reporter` or any masked-reporter wording.

### 7.5 Closing Incidents — ALARP Attestation

Office Review runs the required readiness checks in the background. The visible page does not show root/action counters, pre-approval summary cards, approval-role wording, or a send-back phase picker. Before you tap **Accept / Close**:

1. Confirm all 8 bias guards are attested (5 DNV + 3 organisational defence-traps per Round 21 R12).
2. Confirm ≥1 **Root** layer cause (no artificial cap — Round 21 R03).
3. Confirm at least one action recommendation is recorded.
4. Confirm ALARP attestation on every RED/YELLOW System-Action (Round 21 R02).
5. Enter **Office Comments/lesson learnt** if the office review needs a note. There is no word limit.
6. Before previewing or downloading the PDF, review the **Select PDF content** checklist. All items are selected by default: Summary, Reporter Details, Injury Details, Estimated Cost, Root Cause, Evidence (Documents), Corrective / Preventive Actions, and Signature. PDF preview/download is available for incident records before Phase 7 acceptance; the page should not show a Phase 7 acceptance-only PDF warning.
7. Tap **Accept**. System fires PDF generation (FEAT-SAF-PDF-001) with the selected sections, keeps the record compatible with visible Phase 7 Loss Evaluation, and writes the event to `vims_safety_incident_phase_log`.
8. Open `/safety/incidents/:id/phase-6/`, choose **Incident Report** or **Injury Report** in **Loss Evaluation type**, complete **Loss Evaluation**, and save it. Ship-side and office-side users with incident access can save this evaluation without waiting for Office Review approval. Incident Report shows repair/loss/cost fields; Injury Report shows safe-working-practice/rest/repatriation/hospitalization/evacuation/injury-cost fields. Closure is enabled only after the Loss Evaluation save succeeds and remains an office close action.

To issue an Incident Fleet Alert from Office Review, tap **Fleet Alert** below **Accept / Close**, select one or more ships, and tap **Send Fleet Alert**. The system sends in-app and email alerts only to the selected ships; vessel email addresses come from `VesselData.email`.

If **Record injury** was saved on Phase 1, the PDF prints the title `Injury Report`. If no injury was recorded, it prints `Incident Report`. The PDF Loss Evaluation cost/details block follows the saved Phase 7 Loss Evaluation type; older saved evaluations without a type use the injury-record fallback. Office Comments and closure reason appear near the end of the PDF before Signature, not in Summary. Evidence documents appear as separate document blocks with Description and File rows instead of numbered attachment rows; internal evidence notes are not printed. Action descriptions appear once inside their detail box without recommendation rationale / "Why is this needed?" text. Required signature rows remain visible in the PDF even when unsigned; unsigned rows show as `Pending`.

Under the current CR-044 authority model, PIC or DPA can complete Office Review and later closure for any risk band.
When sending the incident back, enter only the rework comment and tap **Send for rework**. The current UI sends the incident back to the action rework target; it does not ask the office user to choose a phase. Ship-side users do not see Accept / Close or Send for rework cards on Office Review; they see the Office Comments/lesson learnt card. If office has not added a note yet, the card says **Office comment is not added yet.**

### 7.6 Overseeing M-SCAT Root-Cause Analysis

You are the **sole maintainer** of the M-SCAT taxonomy, case-study library, and SOI template (`/safety/admin/*`, exclusive per D-CFG-01 / 02 / 03). The investigation teams pick from the 174-row `master_mscat_taxonomy` — you add new rows, edit subcode descriptions, and deprecate obsolete codes. The 10.15 Design / MoC Governance category was added Round 21 (D-GAP-R15); further additions happen here.

### 7.7 Managing Bias Guards (Round 21 R12)

The 8 bias-guard catalogue lives at `/safety/admin/bias-guards/` (read-only for V1 — maintained centrally as `master_safety_bias_guard`). The 8 are:

1. Recency (DNV) — at least one evidence item is recorded before leaving evidence capture (D-MAINT-CR012 / `V-INC-040`).
2. Assumption (DNV) — every fact linked to evidence (D-DNV-11 #2 / `V-INC-041`).
3. Hindsight (DNV) — no info dated after `occurred_at` without justification (D-DNV-11 #3 / `V-INC-042`).
4. Confirmation (DNV) — current users document contradictory evidence in Documents, Witness Statement, and analysis notes; the Evidence Matrix Con-row gate is compatibility-only after D-MAINT-CR015.
5. Blame-fixation (DNV) — roots not all in Personal Factors (cat 1–4) unless DPA override (D-DNV-11 #5 / `V-INC-044`).
6. Defence-trap: Plant (organisational) — D-GAP-R12.
7. Defence-trap: Personnel (organisational) — D-GAP-R12.
8. Defence-trap: External-event (organisational) — D-GAP-R12.

You are the override authority for guard #5 (blame-fixation) via `SAF_P_006`. Use sparingly; document reason; record lands in `vims_safety_field_history`.

### 7.8 DPA Routes at a Glance

| Route | Purpose |
|-------|---------|
| `/safety/dashboard/` | Fleet-wide Safety Intelligence Dashboard |
| `/safety/incidents/:id/phase-5/` | Office Review acceptance or rework for any risk band |
| `/safety/incidents/:id/fleet-alert/` | Incident Fleet Alert selected-ship in-app/email dispatch |
| `/safety/near-miss/:id/triage/` | LOW / HIGH triage |
| `/safety/near-miss/:id/fleet-alert/` | Prepare Circular/Alert handoff and issue Near Miss fleet-alert step (HIGH) |
| `/safety/soi/:id/applicability/approve/` | Approve Master's area-applicability request |
| `/safety/admin/mscat/` | M-SCAT taxonomy edit (exclusive) |
| `/safety/admin/soi-template/` | 13-area × 329-item template edit (exclusive) |
| `/safety/admin/case-studies/` | Navigator + Sinkfast case-study library |
| `/safety/search/` | Cross-record FTS search (archive toggle) |

---

## 8. Shore FM — Fleet Manager

> **Who this is:** The shore Fleet Manager. Commercial + budget authority. RED-band incident closer (D-GAP-M06). One of only two roles (along with DPA) that can see Near Miss reporter identity. Last signature in the chain.

### 8.1 Day in the Life — FM

You start the day reviewing the RED-band incident MV Bravo filed yesterday. The DPA has signed during Office Review; the record is now on your desk at `/safety/incidents/:id/phase-5/` awaiting FM closure. You scrutinise the commercial impact, confirm the ALARP attestation on each System-Action, review the linked purchase requisitions on each Corrective Action, and sign to close. You then open `/safety/dashboard/` (read-only for you per D-GAP-M31) to check fleet-wide trends. Two Corrective Actions need budget approval — both flow from the Corrective Action → Purchase Requisition hard-FK link (D-GAP-M12). You approve the larger one in the Purchase module and leave the second for tomorrow pending quote clarification.

### 8.2 Budget Approval on Corrective Action (D-GAP-M12)

Every Corrective Action on an Incident can be linked to a Purchase Requisition. The link is a **hard foreign key** from `vims_safety_corrective_action.purchase_req_id` to the Purchase module. This means:

- A Purchase Requisition **cannot be archived or deleted** while an open CA is linked.
- Live status syncs — when the requisition advances (PO raised, goods received, closed), the CA row in `/safety/incidents/:id/phase-6/` reflects it.
- Same-DB live join — no sync staleness (D-GAP-I2).

**Step-by-step — approving a CA's purchase:**

1. From your dashboard or notifications, open the Incident at `/safety/incidents/:id/phase-6/`.
2. Find the Corrective Action row showing `[Purchase Req: PR-2026-0123 — Awaiting Approval]`.
3. Click **[Open PR]** — opens the Purchase module at `/purchase/requisitions/PR-2026-0123` in a new tab.
4. Review the requisition (items, quantities, quote, vendor, delivery terms).
5. In the Purchase module, follow the standard approval flow.
6. On approval, the CA row in Safety auto-updates status. No manual sync.

> **If a requisition is rejected or amended,** the CA row reflects it live. The CA cannot be closed until the linked requisition reaches a terminal state (closed or cancelled with a new CA created).

**Creating a new CA → Purchase Req link** (done by HOD/Master at Phase 6):

1. HOD taps **[Link Purchase Req]** on a CA row.
2. Navigates to `/purchase/requisitions/create?linked_safety_ca={caId}`.
3. Creates the requisition — the `linked_safety_ca` parameter forms the hard FK.
4. Requisition routes for approval through standard Purchase flow, ending at your desk for sign-off.

### 8.3 Reporter Identity View

Same as the DPA (see §7.4). Near Miss reporter identity is visible where vessel scope and Safety permission allow it; the masked reporter concept is removed from V1.

### 8.4 RED-Band Incident Closure

For RED-band incidents only, you are the closer (D-GAP-M06):

1. DPA signs during Office Review.
2. Record routes to you at `/safety/incidents/:id/phase-5/`.
3. Review the full investigation record; read-access to RCA, actions, evidence, and Office Review is full edit for RED (D-GAP-M06 gives you full-edit authority on RED — unusual among shore roles).
4. Tap **Accept**. Record stays compatible with visible Phase 7 Loss Evaluation and PDF generation (FEAT-SAF-PDF-001). Closure event logs to `vims_safety_incident_phase_log`.
5. Complete and save Loss Evaluation at `/safety/incidents/:id/phase-6/` if it has not already been saved by a ship-side or office-side user; then close with a closure note.
5. Your signature is the terminal node in the Reporter → Master → HOD → DPA → FM chain (`V-INC-073` / `V-INC-074`).

### 8.5 FM Routes at a Glance

| Route | Purpose |
|-------|---------|
| `/safety/dashboard/` | Fleet-wide read-only (D-GAP-M31) |
| `/safety/incidents/:id/phase-6/` | Loss Evaluation |
| `/safety/incidents/:id/phase-5/` | RED-band Office Review closure signature |
| `/safety/near-miss/:id/` | Near Miss detail — full reporter identity visible |
| `/purchase/requisitions/:reqId` | Linked Purchase Req approval (cross-module) |

---

## 9. Mobile & Tablet Tips

V1 breakpoints per D-GAP-M34 / DESIGN_SYSTEM §9 / APP_FLOW §11:

| Breakpoint | Device | Primary use |
|------------|--------|-------------|
| **≥1280px** | Desktop | Shore roles (DPA / FM / TD / HOD-shore); office analytics |
| **≥768px** | **Tablet — primary SOI device** | Ship SO / Master — SOI pick-areas, download, findings |
| **≤480px** | Phone | **Read-only dashboards in V1** — CRUD deferred to V2 |

### 9.1 Vessel-Tablet Workflow

- Mobile-first is the mandate — every Safety screen starts mobile and scales up (`FRONTEND_GUIDELINES.md`).
- The SOI pick-areas screen is single-column at 768px portrait.
- The Evidence Workspace uses a single Documents form on tablet: Attachment, Title, and Description.
- Hit-target for all buttons is ≥44px to satisfy WCAG AA (Round 20).

### 9.2 Offline — Paper-First SOI Download

SOI is designed for offline use via paper. Once you download the PDF or Excel at `/safety/soi/:id/download/` (Step 2), the paper works anywhere — no internet needed.

- **On the vessel network** — download before going on deck.
- **Off the network** — the paper is the record. Register findings when you return to VIMS coverage.
- **No scan, no upload** (D-GAP-E4 / D-GAP-E5). The paper is filed in the ship SMS filing system as the authoritative physical record.

### 9.3 Other Offline Considerations

- Incident Phase 1 intake can be drafted offline via local browser storage; Phase 2 submission requires connectivity (to fire notifications and assign the formal reference).
- Near Miss submission requires connectivity to issue the reference.
- SCM hosting requires ship-time configuration and clear WRH readiness for all roster crew. SCM Office Comment closure requires connectivity; WRH live join warnings do not block closure after the meeting exists.

### 9.4 Phone-Specific Limitations

- **Phone CRUD is not supported in V1.** Phone users see read-only dashboards. Reporting / SOI / Incident creation is tablet-or-larger.
- This is deliberate — small-screen CRUD on a safety-critical form has legibility risk.

---

## 10. Common Error Messages

When a screen blocks your action, the error message names the validation rule ID (V-*). These cross-reference `VALIDATION_RULES.md`.

| Error shown | Rule ID | What it means | What to do |
|-------------|---------|----------------|------------|
| "Incident narrative must be at least 200 characters." | `V-INC-001` | Phase 1 narrative too short | Expand the narrative — cover what / when / where / who / how |
| "Risk band must be GREEN, YELLOW, or RED." | `V-INC-009` | Invalid band value | Re-select the band from the picklist |
| "Chain-of-custody entry requires description, collection date-time, collector signature, and storage location." | `V-INC-020` | Missing fields on a physical evidence row | Fill all four required fields (D-GAP-R04) |
| "Physical evidence requires witness signature per chain-of-custody protocol." | `V-INC-021` | Witness signature missing | Add witness signature (paper or digital) |
| "Formal interview requires: read-back to witness, witness signature, copy to witness." | `V-INC-032` | Legacy/API formal interview payload missing the protocol fields | Use the current simplified Witness Statement screen unless maintaining an older formal interview integration |
| "Phase 4 evidence is incomplete: add at least one evidence note, file, interview, or N/A reason." | `V-INC-040` | Phase 4 transition blocked | Add at least one document attachment with title and description, or record another valid evidence item |
| "Assumption bias guard: every fact requires a linked evidence reference." | `V-INC-041` | Unlinked fact row | Link an evidence ID to each fact |
| "Hindsight bias guard: cannot reference information dated after the incident." | `V-INC-042` | Post-incident date on a finding | Remove or justify the reference |
| "Blame-fixation bias guard: add a Lack-of-Control cause or request DPA override." | `V-INC-044` | All roots in Personal Factors | Add a Lack-of-Control cause or request DPA override |
| "All 8 bias guards must be attested (5 DNV + 3 organisational defence-traps per Round 21 R12) before Phase 6 → 7 transition." | `V-INC-055` | Guard attestations incomplete | Attest remaining guards |
| "Investigation depth '{depth}' requires {N} analysis tools (D-GAP-R14)." | `V-INC-056` | Too few Phase 5 tools | Add tools (DEEP=5, MEDIUM=3, SHALLOW=2) |
| "YELLOW/RED closure requires ≥1 Corrective + ≥1 Preventive + ≥1 Lessons-Learnt recommendation." | `V-INC-064` | Missing recommendation tier | Add missing tier(s) at Phase 6 |
| "Each closure requires Lessons Learned + ≥1 Immediate Action + ≥1 System Action." | `V-INC-065` | Missing System-Action tier | Add System-Action per D-DNV-06 |
| "Master cannot sign before Reporter submits." | `V-INC-070` | Out-of-order signature | Reporter signs first |
| "HOD cannot sign before Master." | `V-INC-071` | Out-of-order signature | Master signs first |
| "DPA cannot sign before HOD." | `V-INC-072` | Out-of-order signature | HOD signs first |
| "FM cannot sign before DPA." | `V-INC-073` | Out-of-order signature | DPA signs first |
| "RED-band closure requires FM signature (D-GAP-M06)." | `V-INC-074` | FM signature missing on RED | FM signs to close |
| "Digital signature requires typed name, timestamp, and device fingerprint." | `V-INC-075` | Hybrid-signature payload incomplete | Sign again via the UI block |
| "Safety Officer + Assistant paper signatures are mandatory. Trainees do not sign." | `V-SOI-031` / `V-SOI-032` | Paper checklist missing SO/Assistant sig; trainee-name present | Sign paper correctly (D-GAP-M15) |
| "Master counter-signs digitally at approval stage, not on paper." | `V-SOI-033` | Master sig attempted on paper | Master signs digitally at `/safety/soi/:id/findings/:findId/` approval |
| "You do not have access to Safety incidents." | 403 | Permission missing | Request `SAF_F_001` permission from DPA |

See `VALIDATION_RULES.md` for the full 100+ rule catalogue.

---

## 11. Escalation Paths & Timeline Extensions

### 11.1 No "Acting-*", No Deputy Chains (D-GAP-A3 / A4)

Rank persists. The person filling a rank changes via normal crew rotation, but the rank itself is continuous. The system has **no "Acting-DPA", "Acting-CO", "Acting-Master", or "Deputy-FM" concepts**. If the DPA is on leave, the person assigned the DPA rank on the crew roster performs the DPA's actions; the same access and same audit trail apply. There is no parallel "temporary DPA" sub-identity.

### 11.2 The Only Escalation — Timeline Extension (D-GAP-B2)

When a signature chain stalls because the assigned signatory is unavailable beyond the designed timeline, the **VIMS timeline-extension procedure** is the only escape valve (D-GAP-B2). This is a platform-level flow shared with other modules (not Safety-specific).

**How to request a timeline extension:**

1. Use the VIMS platform extension request form (shared with Reporting / WRH etc.).
2. Cite the Safety record reference and the blocked signature step.
3. Extension-approval authority is the platform flow — Safety does not maintain a separate authority table.
4. Approved extension shifts the 80-day / 90-day counters on the dashboard (D-GAP-F3).

**What does NOT exist:**

- Auto-escalation to MD / Head Office.
- Deputy-FM / Deputy-DPA fallbacks.
- Acting-role assignments inside the Safety module.
- FM → CEO automatic escalation on overdue RED.

### 11.3 Master Unavailable — What Happens

If the Master is unavailable beyond a signature's designed timeline:

1. The next-in-rank assigned to the Master slot on the current crew roster performs the action. This is standard ISM practice — the CO may step up if the Master is incapacitated; the assignment is driven by the vessel's Crew_Onboarding_History + CMS.
2. If no next-in-rank is assigned (roster gap), file a timeline extension (D-GAP-B2) via the platform flow.
3. Never create a record under an "Acting-Master" sub-identity — this would fracture the audit trail.

### 11.4 DPA Unavailable

Same pattern — whoever holds the DPA rank on the shore org roster performs DPA actions. V1 has no Deputy-DPA. Timeline extension handles genuine gaps.

### 11.5 FM Unavailable (RED Closure)

Same pattern, specifically called out in D-GAP-B2 — no Deputy-FM. RED closure runs within the designed timeline; timeline extension is the only path when FM is unavailable.

### 11.6 Dashboard-Flagged Overrun

On the dashboard, overdue records surface at 80% of the timeline as an amber flag (D-GAP-F3). This is a metric — not an auto-escalation trigger. DPA judgement decides whether to request a timeline extension or press for immediate action.

---

## 12. Appendix A — Route-to-Role Index

This index cross-references every route from `APP_FLOW.md` against the roles that use it in this guide.

| Route | Primary actor(s) | Section in this guide |
|-------|-------------------|------------------------|
| `/safety/dashboard/` | All roles (read-scoped) | §2.1, §6.1, §7.1, §8.1 |
| `/safety/search/` | DPA, FM, Master, HOD (read) | §7.8 |
| `/safety/incidents/` | All top-4 ship roles + Shore | §3.6, §4.2, §6.7 |
| `/safety/incidents/create/` | Master, CO, CE, 2/E | §3.2 |
| `/safety/incidents/:id/` | All roles (scoped) | §4.2, §6.6 |
| `/safety/incidents/:id/phase-1/` | Top-4 reporters | §3.2 |
| `/safety/incidents/:id/phase-2/` | Top-4 (band + classifier) | §3.2 |
| `/safety/incidents/:id/phase-3/` | Master lead, HOD contribute | §4.3 |
| `/safety/incidents/:id/phase-4/places/` | HOD, Reporter (witness) | §4.3 |
| `/safety/incidents/:id/phase-4/people/` | HOD (interviews) | §4.3 |
| `/safety/incidents/:id/phase-4/parts/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-4/paper/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-4/photos/` | HOD | §4.3 |
| `/api/safety/incidents/:id/phase-4/chain-of-custody/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-4/interviews/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-4/` | HOD, Master | §4.3 |
| `/safety/incidents/:id/phase-5/` | HOD, Master, DPA (review) | §4.3, §7.2 |
| `/safety/incidents/:id/phase-5/analysis/step/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-5/analysis/fact-tree/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-5/analysis/ecf/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-5/analysis/barrier/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-5/analysis/change/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-5/causal-layering/` | HOD, Master | §4.3 |
| `/safety/incidents/:id/phase-5/human-factors/` | HOD | §4.3 |
| `/safety/incidents/:id/phase-6/` | Master, HOD, FM (RED edit) | §4.4, §6.6, §8.2 |
| `/safety/incidents/:id/phase-5/` | DPA (YELLOW), FM (RED) Office Review | §7.2, §7.5, §8.4 |
| `/safety/incidents/:id/phase-7/verification/` | Legacy verification compatibility | §7.2 |
| `/safety/incidents/:id/phase-8/` | DPA | §7.2 |
| `/safety/incidents/:id/closure/` | Terminal read; all | §7.2 |
| `/safety/incidents/:id/audit/` | DPA, FM, auditors | §7.2 |
| `/safety/incidents/:id/pdf/incident/` | All (scoped PDF with selectable content checklist) | §7.5 |
| `/safety/incidents/:id/pdf/mscmepc3/` | DPA | §7.8 |
| `/safety/incidents/:id/pdf/auditor-zip/` | DPA | §7.8 |
| `/safety/incidents/:id/reopen/` | DPA (GREEN/YELLOW), FM (RED) | §7.5 |
| `/safety/near-miss/` | All | §3.6, §7.3 |
| `/safety/near-miss/create/` | Any crew | §3.3 |
| `/safety/near-miss/:id/` | Authorized users see reporter within vessel scope | §3.4, §7.4, §8.3 |
| `/safety/near-miss/:id/triage/` | DPA | §7.3 |
| `/safety/near-miss/:id/fleet-alert/` | DPA | §7.3 |
| `/safety/near-miss/:id/pdf/` | Authorized users; no masked-reporter wording | §7.3 |
| `/safety/scm/` | All | §6.4 |
| `/safety/scm/create-regular/` | Master or CO | §6.4 |
| `/safety/scm/create-adhoc/` | Master or CO | §6.3 |
| `/safety/scm/:id/` | Master, CO, attendees | §6.3, §6.4 |
| `/safety/scm/:id/attendance/` | Master, CO | §6.4 |
| `/safety/scm/:id/agenda/` | Master, CO | §6.3, §6.4 |
| `/safety/scm/:id/closed-since-last/` | Master, CO (auto) | §6.4 |
| `/safety/scm/:id/pdf/` | All (read) | §6.4 |
| `/safety/soi/` | All | §5.7 |
| `/safety/soi/create/` | SO | §5.2 |
| `/safety/soi/:id/` | All (read) | §5.7 |
| `/safety/soi/:id/pick-areas/` | SO | §5.3 |
| `/safety/soi/:id/download/` | SO | §5.3 |
| `/safety/soi/:id/findings/` | SO | §5.3 |
| `/safety/soi/:id/findings/create/` | SO | §5.3 |
| `/safety/soi/:id/findings/:findId/` | SO → Master | §5.3, §6.5 |
| `/safety/soi/:id/applicability/request/` | Master | §6.5 |
| `/safety/soi/:id/applicability/approve/` | DPA | §7.8 |
| `/safety/soi/:id/close/` | Master | §6.5 |
| `/safety/soi/:id/pdf/` | All (read) | §5.7 |
| `/safety/admin/mscat/` | DPA only | §7.6, §7.8 |
| `/safety/admin/soi-template/` | DPA only | §7.8 |
| `/safety/admin/bias-guards/` | DPA (read V1) | §7.7 |
| `/safety/admin/case-studies/` | DPA | §7.8 |

Total APP_FLOW routes referenced in this guide: **63 of 63 (100%)**.

---

## Appendix B — Regulatory Citations Used

| Citation | Edition / Year |
|----------|----------------|
| ISM Code | 2010 amendments |
| SOLAS | Chapter IX as amended |
| MARPOL | Annex I consolidated 2022 |
| IMO Casualty Investigation Code | Resolution MSC.255(84) |
| IMO Human Factors Analysis | Resolution A.884(21), 1999 |
| IMO Near-Miss Guidance | Resolution A.1075(28) |
| MLC | 2006 |
| COSWP | 2026, Chapter 13 |
| KSM SSQE Manual | Rev 01 Feb 2026 — §4.5 (SO designation), §9 (meetings), §11 (incidents) |
| DNV Practical Incident Investigation & RCA | 2023 |

---

## Appendix C — What This Guide Does NOT Cover

These are deliberate omissions — either out of V1 scope or governed by other documents:

- **PMS integration** — decoupled per D-GAP-I1. No Safety screen links to PMS.
- **Cryptographic / PKI signatures** — no crypto in V1 (D-GAP-D2 / G2). Hybrid model only (D-GAP-D1).
- **Hash chains / legal-hold** — deferred to V2 (D-GAP-G2).
- **Scan upload of SOI paper** — explicitly removed per D-GAP-E4 / D-GAP-E5.
- **"Inspection Compliance %" label** — renamed to "SOI Compliance %" per D-GAP-DESIGN-01. If you see the old label anywhere, it is a bug.
- **"Acting-*" concepts** — do not exist (D-GAP-A3 / A4).
- **Auto-escalation to MD / Head Office** — does not exist (D-GAP-B2 / F3).
- **Phone-based CRUD** — deferred to V2 (D-GAP-M34).

For anything in this list, consult `VIMS-SAFETY-MODULE-SSOT.md` §6 (Decisions Log) or raise a scope change through the Product Owner.

---

*End of USER_GUIDE.md.*
