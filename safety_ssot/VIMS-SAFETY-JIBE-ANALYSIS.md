# JiBe (Anglo-Eastern) — QHSE Module Analysis

> **Source:** 3 PDF user guides from Anglo-Eastern's JiBe platform
> **Purpose:** Design inspiration for VIMS Safety Module
> **Analysed:** 2026-04-09

---

## 1. Incident Reports — Key Design Patterns

### 1.1 Unified Incident + Injury Form
- **Single form** handles both incidents and injuries (not separate modules)
- Selecting "Incident with Injury" as incident type enables injury-specific fields in Crew Involved section
- Rationale: incidents often involve both damage AND injuries simultaneously

### 1.2 Incident Type Taxonomy (Multi-Select, Coded)
| Code | Type |
|------|------|
| — | Incident with Injury |
| T01 | Collision |
| T02 | Grounding |
| T03 | Stranding |
| T04 | Touched bottom at berth / anchorage |
| T05 | Touched bottom in rivers / canals |
| T06 | Allision with Jetty / Berth / Locks |
| T21 | Failure of ship's equipment resulting in loss of propulsion |
| ... | (additional coded types) |

**Note:** Multi-select dropdown — an incident can have multiple types simultaneously.

### 1.3 Sectioned Form with Left Sidebar Navigation
Incident form uses a **scrollable sidebar** with sections:
1. Description (Executive Summary + Immediate Corrective Action)
2. Workflow and Follow-ups (comment thread, both vessel & office)
3. General Details (Incident Type multi-select, Local Time)
4. Investigation & Review Team (Investigated By: Onboard/Office, Lead Investigator)
5. Impact Assessment
6. Attachments (Pictures tab + Attachments tab)
7. Weather Conditions
8. Voyage Details
9. What is Damaged
10. Equipment / Machinery
11. Investigation - Narrative
12. Other Details
13. Cost Evaluation
14. Evidence Review
15. Crew Involved
16. Immediate Cause
17. Root Cause
18. Corrective Action
19. Preventive Action

### 1.4 Status Flow
```
Draft → New → Open → Complete → Closed
```
- **Draft:** Saved but not submitted
- **New:** Just created, not yet worked on
- **Open:** Being worked on (saved = Open, synced to office)
- **Complete:** All CA/PA completed, Master marks Complete
- **Closed:** Vessel Manager (office) closes

### 1.5 Role-Based Access
| Action | Who |
|--------|-----|
| Create report | Any crew member |
| Fill details | Any crew member |
| Mark Complete | Master only |
| Close report | Vessel Manager (office) |
| Delete | Only if Open + no completed CA/PA |

### 1.6 Due Date
- Auto-configured as **30 days** after incident date
- Highlighted in red when overdue

### 1.7 Crew Involved Section
- Pulls **active crew list** from vessel crew module
- Per crew member popup fields:
  - Involved (checkbox)
  - Direct Responsibility (checkbox)
  - Injured (checkbox — only available when "Incident with Injury" type selected)
  - Work Related (checkbox)
  - Nature of Injury (dropdown: Burn heat/cold, etc.)
  - Source of Injury (dropdown: Contact with heat, etc.)
  - Affected Areas of Body (dropdown: R02-Arm(s), etc.)
  - Details of First Aid Administered (free text)
  - Injury Type (dropdown: First Aid Cases, etc.)
  - Off Duty From / To / Hours
  - Rest Hours (Last 24 Hours)
  - Rest Hours HC (Last 24 Hours)
  - Remarks
- Also supports **External** persons (non-crew: Name, Title, Reason on-board)

### 1.8 Four-Category Cause Analysis (Both Immediate & Root)
Used for BOTH Immediate Cause AND Root Cause sections:

| Factor Type | Examples |
|-------------|----------|
| **Human Factors** | Rushing to complete task, Complacency, Fatigue |
| **Vessel Factors** | (N/A checkbox available) |
| **Management Factors** | Lack or inadequate tool box talk, Poor supervision |
| **Other Factors** | Wet/slippery surfaces, Poor lighting |

- Each factor type: dropdown category + **mandatory description field**
- Multiple entries per factor type (dynamic rows)
- "Not Applicable" checkbox per factor type
- View mode shows only selected factors (clean read-only display)

### 1.9 Corrective & Preventive Actions as Tasks
- CA/PA are created as **standalone tasks** (not free text)
- Task types: **Vessel Task** or **Office Task**
- Each task has: Title, Description, Due Date, Status, Completion Date
- Tasks are **linked records** (e.g., `NM-O-47 >> VT-O-48`)
- Vessel Tasks: created by ship, actioned by ship
- Office Tasks: created by ship, actioned and completed by office staff
- Tasks have their own detail page with: Description, Workflow & Follow-ups, Details, Equipment Location, Dates, Attachments, History

---

## 2. Near Miss Reports — Key Design Patterns

### 2.1 Low vs Significant Near Miss (Adaptive Form)
**Key innovation:** Form complexity adapts to risk level.

- Form starts as **short version (Low Risk)** — easy for crew to fill quickly
- Auto-expands to **full version (Significant)** when Impact Assessment records **High or above** residual risk
- Encourages reporting of ALL near misses (low-risk = minimal form burden)

### 2.2 Risk Level Matrix
| | Severity × Likelihood → Risk Level |
|---|---|
| Low severity + Unlikely | Very Low |
| Appreciable + Unlikely | Very Low |
| Major + Almost Certain | High |
| ... | Matrix calculation |

Risk levels: **Very Low → Low → Medium → High → Very High**

### 2.3 Form Sections by Risk Level

**Low Risk (Very Low / Low / Medium):**
- Description (Executive Summary + Immediate Corrective Action)
- Workflow and Follow-ups
- General Details
- Impact Assessment
- Attachments
- Immediate Cause
- Root Cause
- Preventive Action (only — no Corrective Action for low risk)
- Dates
- History

**High Risk / Significant (High / Very High) — adds:**
- Weather Conditions
- Voyage Details
- Equipment / Machinery
- Investigation Narrative
- Corrective Action (in addition to Preventive)
- Human Error Analysis
- Lessons Learned

### 2.4 General Details Fields
| Field | Format |
|-------|--------|
| Near Miss Local Time | HH:MM |
| Near Miss UTC | HH:MM (auto-calculated) |
| Type of Activity | Coded dropdown (T12-In Dry Dock, T17-Overhauling machinery, etc.) |
| Damage/Loss To | People / Property / Environment |
| COSWP Reference | Free text (Code of Safe Working Practices reference) |
| Vessel Location | Coded (B2.1-In Port At berth, B1.1-At Sea Open Sea, etc.) |
| Onboard Location | Coded (C2-Deck, C3-Engine, etc.) |
| Vessel Department | Dropdown |
| Reported By | Auto-populated from logged-in user |

### 2.5 Shared Grid with Incidents
- **Single listing page** for both Incidents and Near Misses
- Columns: Code, Vessel, Title, Type (Incident/Near Miss), Date, Investigated by, Injury (Yes/No), Status, Pending With
- Prefix-based codes: `IN-O-xxx` (Incident-Office), `IN-V-xxx` (Incident-Vessel), `NM-O-xxx` (Near Miss-Office), `NM-V-xxx` (Near Miss-Vessel)
- Filters: Vessel, Type, Status, Incident/Near Miss, Date range
- "Create New" dropdown: Incident | Near Miss

### 2.6 Status Flow (Same as Incidents)
```
Open → Complete (Master) → Closed (Vessel Manager)
```

---

## 3. QHSE Meeting — Key Design Patterns

### 3.1 Meeting Types
- **QHSE Meeting** (monthly routine — currently available)
- **Extra Ordinary Safety Meeting (EOSM)** (planned for future release)

### 3.2 Duplicate Prevention
- System warns if meeting already exists for selected month
- Cannot create 2 meetings for the same date
- ISM Code requires monthly meetings — system enforces this cadence

### 3.3 Create Form
| Field | Notes |
|-------|-------|
| Type | QHSE Meeting / EOSM |
| Date | Meeting date |
| From Time | Start time (HH:MM) |
| To Time | End time (HH:MM) |
| Vessel Location | At Sea (Open Sea Condition), In Port, etc. |

### 3.4 Attendance (Auto-Populated)
- **All crew members auto-listed** from vessel crew module
- Per crew member:
  - Staff ID, Staff Name, Rank (auto-filled)
  - **Committee Role** (dropdown): Chairperson, Safety Officer, Officers' Representative, Crew Representative, Member, Attendee
  - **Attendance** (checkbox)
  - **Reason for Absence** (free text — required if not attended)
- "Add Additional Attendees" button for non-regular attendees
- System ensures all committee roles are assigned

### 3.5 Safety Officer / Safety Committee Findings
- **Auto-pulls** findings from Technical > Defect/Findings list
- Shows findings assigned by safety officer **since last QHSE meeting** or still in **Open state**
- "Display Last Meeting Items" button to carry forward
- Can add new findings: Type, Finding Date, Due Date, Title, Remarks
- Each finding has Status tracking

### 3.6 Incidents and Near Misses Section
- **Auto-displays** all incidents and near misses reported **since previous QHSE meeting**
- Shows: Task Code, Date, Expected Completion Date, Type, Description, Risk Level, Status
- **"Days Since Last Injury"** counter displayed prominently (e.g., "12 Days")
- **Remarks** column for recording discussion notes during meeting
- **Office Remarks** separate field below

### 3.7 Topics of Discussion (Structured Categories)
| Category | Description |
|----------|-------------|
| Incident / Injury / Near Miss occurred on the Vessel | Auto/manual entries |
| Crew Welfare / General Wellbeing / Living and Hygiene Conditions | Manual entries |
| Environment Issues / SEEMP / TEEMP | Manual entries |
| Company QHSE Correspondence / Campaigns | Manual entries (can link to fleet messages) |
| Be Safe+ Observations | Manual entries |

- Each category is an **expandable section** with numbered entries
- Add entries with `+` button, delete with 3-dots menu
- Free text Description per entry

### 3.8 Status Flow
```
New/Pending → Approve → Complete → Close
```
- **New/Pending:** Draft stage, can be deleted
- **Complete:** Senior officer marks complete, triggers "Add Follow Up" confirmation → sends to office
- **Approve:** Office approves
- **Close:** Office closes after review

### 3.9 Attachments
- Pictures tab + Attachments tab (same pattern as Incidents)

### 3.10 KPIs
- Calculated **office-side** from vessel data
- No ship-side KPI input needed

---

## 4. Cross-Cutting Design Patterns (Apply to All Three)

### 4.1 Consistent UI Patterns
- **Left sidebar navigation** for form sections
- **Status badge** with color coding in header bar
- **Due Date highlighting** (red when overdue)
- **Save / Complete** buttons in top-right
- **Workflow and Follow-ups** section for comment threads
- **History** tab for audit trail
- **Attachments** with separate Pictures and Attachments tabs

### 4.2 Consistent Status Model
```
Draft/New → Open → Complete (vessel) → Closed (office)
```
- Clear separation: vessel completes, office closes
- Delete only allowed in draft/open states with no completed child tasks

### 4.3 Task-Based Action System
- CA/PA are NOT free text — they become trackable **tasks**
- Tasks are typed: Vessel Task or Office Task
- Tasks have lifecycle: Open → Complete → Close
- Tasks link back to parent record
- Equipment Location tracking on tasks (Function, System Location, Sub System Location)

### 4.4 Auto-Population Patterns
- Crew list from vessel crew module
- Incidents/near misses since last meeting
- Safety officer findings since last meeting
- Reported By from logged-in user
- UTC time from local time + vessel timezone

---

## 5. Inspiration Points for VIMS Safety Module

### What to adopt:
1. **Unified Incident + Injury form** (not separate modules)
2. **Adaptive near miss form** (Low → Significant based on risk matrix)
3. **4-category cause analysis** (Human/Vessel/Management/Other) with mandatory descriptions
4. **Task-based CA/PA** (not free text) with Vessel Task / Office Task distinction
5. **Shared listing grid** for Incidents + Near Misses
6. **Auto-populated meeting attendance** from crew module
7. **Auto-pull incidents/near misses into meeting** since last meeting date
8. **"Days Since Last Injury" counter** in meeting view
9. **Structured Topics of Discussion** categories in meetings
10. **Duplicate meeting prevention** (one per month per vessel)
11. **30-day auto due date** for incidents
12. **Consistent status flow**: Draft → Open → Complete (vessel) → Closed (office)

### What to improve on:
1. **Better mobile/offline support** (JiBe opens in browser; VIMS is PWA)
2. **Real-time sync** vs JiBe's legacy sync model
3. **Richer analytics/dashboards** (JiBe has basic KPIs)
4. **Integration with PMS** for equipment-related incidents (JiBe has Equipment Location but unclear PMS link)
5. **Regulatory compliance tracking** (ISM Code Ch 9 linkage)
6. **Fleet-wide circular distribution** (our legacy has this; ensure VIMS keeps it)
7. **Safety alert management** (our legacy has 737 alerts; JiBe doesn't show this)
8. **Trouble Report → Incident escalation** (our legacy feature; JiBe doesn't show this)

---

*This analysis is a design reference. Final VIMS requirements will be determined through interrogation with the PO.*
