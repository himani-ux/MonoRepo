# VIMS Safety Module — Single Source of Truth

> **Status:** REQUIREMENTS COMPLETE — ready for docsuite generation
> **Created:** 2026-04-08
> **Last Updated:** 2026-07-07
> **Module Owner:** Prince (PO)
> **Reference wikis:** `VIMS-SAFETY-JIBE-ANALYSIS.md` (UI patterns) · `VIMS-SAFETY-DNV-MSCAT-ANALYSIS.md` (M-SCAT taxonomy + DNV methodology — added 2026-04-16, all 14 diff items adopted)
> **Interrogation:** COMPLETE — ~89 Q&A across 16 rounds, **61 decisions locked**:
> · D-DNV-01..14 (DNV/M-SCAT framework — 14)
> · D-RBAC-01..11 (Role-based access — 11)
> · D-CFG-01..04 (Admin/config — 4)
> · D-EDGE-01..12 (Edge cases — 12)
> · D-PDF-01..03b (PDF export — 4)
> · D-SOI-01..16 (Safety Officer Inspection — 16, added 2026-04-16)

---

## 1. Module Overview

The VIMS Safety Module covers **four** sub-features for vessel safety management:

| # | Sub-Feature | Description | Status |
|---|-------------|-------------|--------|
| 1 | **Incident Reporting** | Logging, investigating, and tracking maritime incidents (injuries, collisions, groundings, equipment damage, pollution events) — full M-SCAT framework | Requirements COMPLETE |
| 2 | **Near Miss Reporting** | Capturing near-miss events to build a proactive safety culture — lightweight Category + factor-based cause framework | Requirements COMPLETE |
| 3 | **Safety Committee Meeting Minutes** | Monthly safety committee meetings — production layout + enhancements (Safety Health Panel, auto-populated compliance, bias-awareness, Closed Items summary) | Requirements COMPLETE |
| 4 | **Safety Officer Inspection (SOI)** | 3-monthly inspection cycle per area (12 areas = SQE S 608 × 11 + cross-cutting Section 12 × 1 → ~292 items). Chief Officer leads with cross-functional assistant; paper-first workflow (PDF/Excel checklist download → findings registered digitally + signed scan uploaded); Master reviews & approves closure; findings auto-feed SCM | Requirements COMPLETE (2026-04-16) |

---

## 2. Cross-Module Dependencies (Preliminary)

```
Safety ←→ PMS  (DECOUPLED per D-GAP-I1)
  - PMS is an independent system with its own login; no in-VIMS integration for Safety V1
  - Investigator cross-references PMS manually when M-SCAT cause 12 (Inadequate Maintenance) is selected
  - Equipment / defect linkage from SOI findings or incidents to PMS remains manual (no FK, no auto-pull)

Safety ←→ Reporting
  - Incident timestamps correlate with noon report data
  - MSC-MEPC.3 Appendix 4 (weather/sea/environment) auto-populated from matched Daily Report
  - Vessel position auto-populated from Daily Report position-time match

Safety ←→ Inspection (Live)
  - PSC/RS findings may relate to safety incidents
  - Corrective actions may overlap
  - Physical-verification model for safety mirrors PSC CAR pattern

Safety ←→ Crew Management System (CMS)
  - SOI Safety Officer / Assistant / Trainee names + departments pulled from CMS (D-SOI-08 cross-functional rule enforced automatically)
  - SCM attendance roster auto-populated from CMS; rest-hour compliance joined from WRH

Safety ←→ WRH
  - Work/Rest Hours non-compliance may be a contributing factor
  - Fatigue analysis linkage — IMO A.884(21) Domain 2 "Organization on board" surfaces WRH summary
  - M-SCAT Personal Factor 4.2 (fatigue) cross-references WRH non-compliance flags

All Modules
  - Shared database: ksm_cms_live (SQL Server)
  - Shared auth: JWT (single permission matrix)
  - Shared notifications: master_notification table
  - Shared platform: VIMS shell (React SPA, Django backend)
```

---

## 2A. Legacy System Analysis (eMarineSoft — Database Exploration 2026-04-08)

> **Source:** `eMarineSoft_live_08_Apr_2026.bak` (8GB, 800 tables, 2057 SPs)
> **Target:** `ksm_cms_live` (VIMS) — zero safety tables exist, only menu stubs in `master_menu_ship`

### Legacy Safety Module — Table Inventory

| # | Table | Records | Purpose |
|---|-------|---------|---------|
| **INCIDENT REPORTING** | | | |
| 1 | `FR_Accident` | 43 | **Office-side** incident reports — full investigation data |
| 2 | `Vsl_FR_Accident` | 0 | **Vessel-side** mirror (dual-environment sync) |
| 3 | `FR_Accident_Archive` | 0 | Archived/closed incidents |
| 4 | `FR_AccidentPreliminaryNotification` | 0 | Preliminary notification before full report |
| 5 | `Tbl_Accident_Attachments` | 97 | Photos, docs attached to incidents (image blob + path) |
| 6 | `VSL_Accident_Attachments` | — | Vessel-side attachment mirror |
| 7 | `Tbl_AccidentCircular` | 32 | Circulate incident lessons to fleet |
| 8 | `Tbl_DefinationOfIncident` | 27 | **Severity × Category matrix** (Minor/Significant/Severe/Major × 7 categories) |
| **NEAR MISS REPORTING** | | | |
| 9 | `FR_NearMiss` | 943 | **Office-side** near miss reports |
| 10 | `Vsl_FR_NearMiss` | 0 | **Vessel-side** mirror |
| 11 | `FR_NearMiss_OfficeLink` | 958 | Office accept/reject workflow per near miss |
| 12 | `FR_NearMiss_VesselLink` | 1028 | Master review/sign-off per near miss |
| 13 | `FR_NearMissCatUpdate` | 385 | Category update audit trail |
| 14 | `VSL_NearMissCause` | 0 | Vessel-side root cause assignment |
| 15 | `Tbl_NearMissCircular` | 0 | Fleet-wide near miss lessons distribution |
| 16 | `TMP_NEARMISS` | — | Temp staging table |
| **SAFETY COMMITTEE MEETING** | | | |
| 17 | `SCM_MASTER` | 257 | **Main meeting record** — date, position, sections, office comments |
| 18 | `SCM_RANKDETAILS` | 4927 | **Attendance** — rank, name, present/absent per meeting |
| 19 | `SCM_SAFETY` | 0 | Safety alert references in meeting |
| 20 | `SCM_INCIDENTDETAILS` | 0 | Incident references in meeting |
| 21 | `SCM_NCRDETAILS` | 0 | NCR references in meeting |
| 22 | `SCM_NOTIFICATIONDETAILS` | 0 | Notification references in meeting |
| **TROUBLE REPORT** | | | |
| 23 | `Tbl_TroubleReport` | 52 | Equipment trouble reports (may escalate to incident) |
| 24 | `Vsl_Tbl_TroubleReport` | — | Vessel-side mirror |
| 25 | `Tbl_TroubleReportAttachments` | — | Trouble report attachments |
| 26 | `Tbl_CirculateTroubleReport` | — | Fleet distribution |
| **OBSERVATION** | | | |
| 27 | `Tbl_ObservationNotification` | 312 | Observation notifications to vessels |
| 28 | `Vsl_Tbl_ObservationNotification` | — | Vessel-side mirror |
| 29 | `t_ObservationsNew` | 178 | Observation findings with corrective actions |
| **SAFETY ALERTS** | | | |
| 30 | `SA_SafetyAlert` | 737 | Safety alerts (source, topic, details, attachment) |
| **LOOKUP/REFERENCE TABLES** | | | |
| 31 | `Mst_tbl_NearMissRootCause` | 11 | Root cause categories (Materials, ManPower, Machine-Equip, etc.) |
| 32 | `Mst_tbl_NearMissSubRootCause` | 40 | Sub-root causes (2 levels deep) |
| 33 | `Tbl_UnsafeActs` | 18 | Unsafe act classifications |
| 34 | `Tbl_UnsafeCondition` | 28 | Unsafe condition classifications |
| 35 | `Tbl_PersonalFactors` | 10 | Personal contributing factors |
| 36 | `Tbl_JobFactor` | 15 | Job/organizational contributing factors |
| 37 | `Mst_tbl_KindofTrouble` | 3 | Hull / Machinery / Other |

### Incident Severity × Category Matrix (from `Tbl_DefinationOfIncident`)

| Severity | INJURY | POLLUTION | BUSINESS LOSS | NAVIGATIONAL | PSC DETENTION | SECURITY | OTHER |
|----------|--------|-----------|---------------|--------------|---------------|----------|-------|
| **Minor** | First aid only, no time off | <400L contained onboard | Downtime ≤6hrs | Collision/grounding ≤$5K | ≤6hrs | Unauthorized access | Fire/flood, no loss |
| **Significant** | Medical treatment, 1-3 days off | >400L but contained onboard | Downtime 6-24hrs | $5K-$15K | 6-24hrs | Pilferage/theft/stowaways | Fire/flood 6-24hrs |
| **Severe** | Fracture, hospitalization, >3 days off | 1-100L overboard | Off-hire 1-3 days | $15K-$50K | 1-3 days | Attempted pirate boarding | Off-hire 1-3 days |
| **Major** | Multiple fractures/fatal/disability | >100L overboard | Off-hire >3 days | >$50K | >3 days | Boarded by pirates | Off-hire >3 days |

### Near Miss — Root Cause Taxonomy (11 categories, 40 sub-causes)

1. **Materials** → Defective material, Wear & tear, Poor procurement
2. **ManPower** → Inadequate competency, Language, Health, Stress, Inattention, Oversight, Intoxication
3. **Machine-Equip** → Incorrect tool, Poor design, Poor placement, Defective equipment
4. **WorkEnvironment** → Disordered workplace, Poor job layout, Physical demands, Forces of nature
5. **Management** → Lack of monitoring, Poor supervision, Unclear instructions, Bad planning
6. **Methods** → Inadequate procedures, Practice ≠ procedure, Poor communication
7. **Training** → Lack of knowledge, Lack of skill, No assessment, Ineffective training
8. **Maintenance** → Insufficient supervision, No feedback, Insufficient planning, Not per maker's manual
9. **Risk Assessment** → Not carried out, Inadequately done, Hazards ignored
10. **SMS** → Procedures inadequate, Missing, New regulation
11. **Others** → Specify

### Near Miss — 4-Factor Analysis (per report)

| Factor | # Options | Examples |
|--------|-----------|---------|
| **Unsafe Acts** | 18 | Non-compliance with rules, Failure to use PPE, Operating without authority, Incorrect navigation |
| **Unsafe Conditions** | 28 | Inadequate guarding, Defective tools, Slippery surface, Poor housekeeping, Electrical fault |
| **Personal Factors** | 10 | Lack of knowledge/skill, Fatigue, Stress, Confusion, Inadequate experience |
| **Job Factors** | 15 | Inadequate supervision, Poor planning, Inadequate maintenance, Wear & tear |

### Safety Committee Meeting Structure (from `SCM_MASTER`)

The meeting form has **8 structured sections**:

1. **Meeting Header** — vessel, date, position (Sea/Port), occasion (Monthly), start/end time
2. **Structured Review** (bit flags) — Previous minutes reviewed? Topics recommended? Deficiencies? All near misses? Major incidents? Emergency drills?
3. **Outstanding Items** — pending items, closed items (free text)
4. **Safety Practice** — Permit to work, Checklist system, 5-min safety meeting compliance, Risk assessment, Alcohol policy, Rest hours
5. **Security** — Immediate security review, Best practices, Cyber security
6. **Environment** — KPI review, Best practices
7. **Health** — Health review, Rest hours, Medical certificates, Weekly inspection by Master, Mess committee
8. **Crew** — Complaints received? Matter resolved? Complaint form submitted to office?
9. **Findings & Corrective Measures** — 10 pairs of findings + corrective measures (hardcoded columns: findings1-10, correctivemeasure1-10)
10. **Office Comments** — Shore-side review, IsReviewed flag

**Attendance** tracked in `SCM_RANKDETAILS`: rank, name, present/absent per meeting (avg ~19 crew per meeting based on 4927 records / 257 meetings).

### Live Data Statistics

| Metric | Value |
|--------|-------|
| Total incidents | 43 (across all vessels, 2016-2026) |
| Incident severity split | Minor: 6, Significant: 16, Severe: 11, Major: 10 |
| Top incident criteria | Other: 17, Business loss: 9, Injury: 6, Navigational: 4, Pollution: 4 |
| Total near misses | 943 (2018-2026) |
| Near miss by vessel | EBK: 374, EAT: 272, SFD: 119, SFC: 104, ARY: 52, YCF: 22 |
| Safety committee meetings | 257 (monthly per vessel) |
| Meeting attendees tracked | 4,927 records |
| Trouble reports | 52 |
| Safety alerts | 737 |
| Observations sent | 312 |
| Incident attachments | 97 |
| Incident circulars sent | 32 |

### Legacy Architecture Patterns

**Dual-Environment (Ship ↔ Office):**
- Every core table has a `Vsl_` mirror (e.g., `FR_Accident` ↔ `Vsl_FR_Accident`)
- Ship creates report → synced to office via packet system (`PacketSent`, `PacketRecd`)
- Office adds comments/review → synced back to ship
- VIMS replaces this with real-time API (no packet sync needed)

**Report Numbering:**
- Incident: `{VesselCode}/ACC/{YY}/{Counter}` (e.g., `EBK/ACC/26/28`)
- Near Miss: `{VesselCode}/NMS/{YY}/{Counter}` (e.g., `EBK/NMS/26/390`)
- Trouble: `{VesselCode}{NN}/{YY}` (e.g., `EBK01/23`)

**Workflow:**
- Near Miss: Ship creates → Master reviews/signs → Office accept/reject → Office comments → Circulate to fleet
- Incident: Ship creates → Office investigation (root cause, sub-cause) → Office review (QD reviewed, DPA accepted, entire fleet) → Corrective actions → Circulate
- Safety Meeting: Ship creates monthly → All crew attendance → Office reviews → Office comments

### Key Stored Procedures (Safety Module)

| SP | Purpose |
|----|---------|
| `Proc_Insert_Fr_Accident` / `_Vessel` | Create incident report (office/ship) |
| `Proc_Update_Accident` / `_Vessel` | Update incident |
| `PR_FR_GetAccidentDetailById` | Get single incident |
| `PR_FR_Search_Accident` | Search/filter incidents |
| `PR_FR_BindAccidentGrid` | Grid listing |
| `Proc_Insert_NearMIss` / `_Vessel` | Create near miss (office/ship) |
| `Proc_Update_NearMIss` / `_Vessel` | Update near miss |
| `PR_FR_GetNearMissDetailById` | Get single near miss |
| `PR_FR_Search_NearMiss` / `All` | Search/filter near misses |
| `PR_FR_NearMiss_OfficeLink` | Office accept/reject workflow |
| `Proc_AccecptReject_FR_NearMiss` | Accept/reject action |
| `Proc_Insert_Update_Office_SCM_Master` | Create/update safety meeting |
| `Proc_Select_SCM_Master` | Get meeting details |
| `Proc_Select_All_SCM_Reports` | List all meetings |
| `SP_INSERT_SCM_RANKDETAILS` | Add attendees |
| `Proc_Insert_TroubleReport` / `_Vessel` | Create trouble report |
| `Proc_CovertTroubleToIncident` | Escalate trouble → incident |
| `Pro_UpdateIncidentCorrectiveAction` | Update corrective actions |
| `Proc_InsertAccidentCircular` | Circulate incident to fleet |
| `sp_InsertSA_SafetyAlert` | Create safety alert |
| `PR_RPT_NearMiss` / `RootCause` / `Sub` | Near miss analytics/reports |

### Legacy Report Formats

#### 1. Incident Report Format (`Vw_AccidentReport` / `Vw_AccidentOfficeReport`)

**Ship-Side Report (created by vessel):**
| Section | Fields |
|---------|--------|
| **Header** | ReportNo (`EBK/ACC/26/28`), VesselName, VesselIMO, VesselFlag, VesselGroup, ReportDate |
| **Reporter** | ReportedByFirstName + FamilyName, Rank (lookup), CrewNumber |
| **Classification** | AccidentSeverity (Minor/Significant/Severe/Major), IncidentCriteria (Injury/Pollution/Business/Navigational/PSC/Security/Other), AccidentCategory |
| **Compliance** | CompanyPolicy (Y/N), DandATest (Drug & Alcohol test Y/N) |
| **Notification** | InformedToOffice, InformedTo, InformedBy, InformedDate, InformedTime |
| **Occurrence** | DateofOccurrence, LocalTimeofEvent, VslPosLat, VslPosLong, Place |
| **Narrative** | WhatHappened (free text, unlimited), Description, ImmediateCause (CSV of cause IDs), RootCause (CSV of cause IDs) |
| **Actions** | ImmediateCorrectiveAction, PreventiveAction, CorrectiveActions, Recommendations |
| **Injury Detail** | InjuryDefination (linked to severity matrix text) |
| **Attachments** | Photos/docs via `Tbl_Accident_Attachments` (image blob + file path) |

**Office-Side Additions (added by shore staff):**
| Section | Fields |
|---------|--------|
| **Office Root Cause** | Up to 5 root causes + 5 sub-causes (OfficeRootCause1-5, OfficeSubCause1-5) — resolves to `Mst_tbl_NearMissRootCause` names |
| **Office Review** | OfficeRDReviewedQD (reviewed by QD), OfficeRDAcceptedDPA (accepted by DPA), OfficeRDEntireFleet (circulated to fleet) |
| **Office Remarks** | OfficeRemarks, OfficeCategory, VesselSafetyRating |
| **Verification** | VerifiedBy (user lookup), VerifiedOn |
| **Fleet Circular** | Via `Tbl_AccidentCircular` — sent to selected vessels with PDF attachment |

**Count Report:** `Vw_FR_Accident_CountReport` — same fields, used for aggregated dashboards (by vessel, severity, criteria, date range)

---

#### 2. Near Miss Report Format (`VW_GetFr_NearMiss`)

**Ship-Side Report:**
| Section | Fields |
|---------|--------|
| **Header** | NearMissNo (`EBK/NMS/26/390`), VesselCode, DateOfOccurrence, NearMissPlace |
| **Reporter** | IdentifiedByFirstName + FamilyName, Rank (lookup), CrewId |
| **Category** | InjuryCategory, PollutionCategory, ProDamageCategory (can be multiple) |
| **Narrative** | WhatHappened (free text), Suggestions |
| **4-Factor Analysis** | UnsafeAct (ID→name + free text comment), UnsafeCondition (ID→name + comment), PersonalFactor (ID→name + comment), JobFactor (ID→name + comment) |
| **Master Review** | MasterReview, MasterComments, SignMasterFirstName + FamilyName, SignMasterCrewId |
| **KPI** | KPI value (monthly near-miss target tracking) |
| **File** | FileName (single attachment) |

**Office-Side Additions:**
| Section | Fields |
|---------|--------|
| **Root Cause** | ImmediateCause (CSV of IDs from `tbl_ImmediateCause`), RootCause (CSV of IDs from `tbl_RootCause`), SubRootCause |
| **Office Review** | OfficeComments, CommentType, AccecptRejectFlag (A/R) |
| **Office Link** | Via `FR_NearMiss_OfficeLink` — AcceptReject, Remarks per vessel link |
| **Vessel Link** | Via `FR_NearMiss_VesselLink` — Master review/sign-off record |
| **Verification** | VerifiedBy, VerifiedOn |
| **Status** | Status (char: 0=open, etc.) |
| **Fleet Circular** | Via `Tbl_NearMissCircular` (unused in current data) |

**Analytics Reports:**
- `Proc_NearMissReport` — Filter by vessel, month, year → joins root cause + sub-root cause names
- `PR_RPT_NearMissRootCause` — Root cause breakdown for single near miss
- `PR_RPT_NearMissSub` — Immediate cause breakdown for single near miss
- `PR_FR_Search_NearMiss` — Search grid with date range, vessel, injury type filters

---

#### 3. Safety Committee Meeting Format (`vw_GetSCM_Master`)

**Meeting Header:**
| Field | Format/Example |
|-------|---------------|
| SCMNo | `EBK-31-Mar-2026` (auto-generated: VesselCode + date) |
| VesselName | Lookup from Vessel table |
| SDate | Meeting date |
| Ocassion | M=Monthly (standard) |
| ShipPosition | S=Sea / P=Port |
| ShipPosFrom / ShipPosTo | Voyage from/to (if at sea) or port name (if in port) |
| CommTime / CompTime | Start/end time (HH:MM) |

**Section 1 — Structured Review (all Yes/No):**
- Minutes of previous safety committee reviewed?
- Date absent from previous meeting
- Topics recommended by company discussed?
- Deficiencies discussed?
- All near misses discussed?
- Immediate actions discussed?
- Major incidents discussed?
- Emergency drills discussed?

**Section 2 — Outstanding Items:**
- OUTSTANDINGITEMS (free text — pending items)
- pendingitems, closeditems (separate tracking)

**Section 3 — Safety Practice (Yes/No + free text):**
- Permit to Work compliance
- Checklist System compliance
- 5-Minute Safety Meeting compliance
- Risk Assessment Management
- Alcohol Policy
- Rest Hours
- Best practice recommendations (free text)
- Quality & Safety topics 1-3 (free text)

**Section 4 — Security:**
- Review of immediate security concerns (free text)
- Best practices (free text)
- Cyber security notes
- Latest circular received? Safety alert?
- Message from SEQ?

**Section 5 — Environment:**
- KPI review (free text)
- Best practices (free text)

**Section 6 — Health:**
- Health review (free text)
- Rest hours compliance (Y/N)
- Medical certificates healthy (Y/N)
- Weekly inspection by Master (Y/N)
- Mess committee meeting for quality (Y/N)
- Best practices (free text)

**Section 7 — Crew:**
- Any complaints received from crew? (Y/N)
- Matter status resolved (int)
- Scan copy of complaint form submitted to office (int)
- Best practices (free text)

**Section 8 — Findings & Corrective Measures:**
- 10 pairs: findings1-10 + correctivemeasure1-10 (hardcoded columns — **design flaw to fix in VIMS: use child table**)

**Section 9 — Miscellaneous:**
- Miscellaneous comments (free text)

**Section 10 — Office Review:**
- OFFICECOMMENTS (free text, added by shore SEQ/DPA)
- IsReviewed (bit)

**Attendance** (`SCM_RANKDETAILS`):
- One row per crew member: SCMId, VesselCode, RankName, Name, Absent (0/1), Remarks, CrewNumber

---

#### 4. Trouble Report Format (`Vw_Tbl_TroubleReport`)

| Section | Fields |
|---------|--------|
| **Header** | SerialNo, ShipCode, TitleofTrouble, VoyageNo, DateofIssue, ServiceLine |
| **Classification** | Department, ShipCondition, KindofTrouble (Hull/Machinery/Other), Equipment, EquipmentCode, EquipmentCategory, Manufacturer, Model |
| **Discovery** | ModeOfDiscovery, DateofTrouble, PlaceofTrouble |
| **Effect** | ddlEffect (dropdown) |
| **Narrative** | ChronologicalOrder, Phenomenon |
| **Actions** | EmergencyOrTemporary, FinalOrSubsequent, DateCompletion |
| **Spares** | DeliveryofSpares, EmergencyTemporary, FinalSubsequent |
| **Class** | ClassStatus, DueDate |
| **Root Cause** | RootCauseID, SubrootCauseID, DirectCause, RootCauseDescription |
| **Prevention** | ImmediateActions, RecurrencePrevention |
| **Cost** | LossTime, Estimated, Fixed, CostRepair, MakersGuarantee, FinalSpare, ClaimRecoverable, FinalRepair |
| **Status** | ExpectedDateClosure, ReportRequired |
| **Escalation** | `Proc_CovertTroubleToIncident` — converts trouble report into full incident |

---

#### 5. Safety Alert Format (`SA_SafetyAlert` — 737 records)

| Field | Description |
|-------|-------------|
| SANumber | Alert serial number |
| Source | Origin of alert (IMO, flag state, P&I club, class, internal) |
| Date | Alert date |
| Topic | Subject line |
| Details | Full alert text |
| FileName | Attached document |
| CreatedBy / NotifiedBy | User tracking |

---

### Legacy Report Views Summary

| View | Purpose | Key Joins |
|------|---------|-----------|
| `Vw_AccidentReport` | Full incident report with resolved names | Rank lookup, root cause names, verified-by name |
| `Vw_AccidentOfficeReport` | Office version with resolved office root causes | + CorrectiveActionCategory, CorrectiveActionRootCause lookups |
| `Vw_FR_Accident_CountReport` | Count/dashboard aggregation | Same as AccidentReport |
| `VW_GetFr_NearMiss` | Full near miss with 4-factor names resolved | UnsafeActs, UnsafeCondition, PersonalFactors, JobFactor JOINs |
| `vw_GetSCM_Master` | Safety meeting with all Yes/No resolved to text | Vessel name lookup, formatted dates/times |
| `vw_SCM_RankDetails` | Meeting attendance | Direct from SCM_RANKDETAILS |
| `Vw_Tbl_TroubleReport` | Trouble report with resolved lookups | Department, ShipCondition, KindofTrouble, Equipment lookups |
| `Vw_Tbl_TroubleReport_CountReport` | Trouble report dashboard aggregation | Same with raw IDs for grouping |
| `Vw_AccidentAttachment` | Attachment listing for incidents | — |
| `vw_GetInternalSafetyInspectionReport` | Internal safety inspection | — |
| `vw_ObservationsAll` | All observations | — |

### Legacy Workflow Analysis

#### Workflow 1: Incident Report (FR_Accident)

```
SHIP SIDE                                          OFFICE SIDE
─────────                                          ───────────
                                                   
1. Any crew member reports                         
   incident to Master                              
        │                                          
        ▼                                          
2. Master creates report                           
   Proc_Insert_FR_Accident_Vessel                  
   → Vsl_FR_Accident                               
   Fields: severity, criteria, what happened,      
   immediate cause, root cause, corrective         
   actions, D&A test, company policy,              
   lat/long, place                                 
        │                                          
        ▼                                          
3. (Optional) Preliminary Notification             
   PR_FR_InsertAccidentPreliminaryNotification     
   Quick alert: accident happened? CAPA taken?     
   Comments. Sent before full report.              
        │                                          
        ▼                                          
4. XML Packet Sync ──────────────────────────────► 5. Office receives
   (offline ship → office when connected)             PR_FR_ImportAccident
                                                      Parses XML, inserts into FR_Accident
                                                      Auto-generates report number:
                                                      {VslCode}/ACC/{YY}/{Counter}
                                                           │
                                                           ▼
                                                   6. Office Investigation
                                                      Proc_Update_Accident
                                                      • Add up to 5 Office Root Causes
                                                        + 5 Sub-Causes (from lookup)
                                                      • OfficeRemarks (free text)
                                                      • OfficeCategory
                                                      • VesselSafetyRating
                                                           │
                                                           ▼
                                                   7. QD Review
                                                      OfficeRDReviewedQD = true
                                                           │
                                                           ▼
                                                   8. DPA Acceptance
                                                      OfficeRDAcceptedDPA = true
                                                           │
                                                           ▼
                                                   9. Verification
                                                      VerifiedBy (user), VerifiedOn (date)
                                                           │
                                                           ▼
                                                   10. (Optional) Circulate to Fleet
                                                       OfficeRDEntireFleet = true
                                                       Proc_InsertAccidentCircular
                                                       → Tbl_AccidentCircular
                                                       PDF sent to selected vessels
                                                           │
                                                           ▼
                                                   11. (Optional) Archive
                                                       PR_FR_Accident_Archive
                                                       Moves record from FR_Accident
                                                       → FR_Accident_Archive + DELETE
```

**No explicit status field** — workflow state is inferred from:
- Report exists but no OfficeRootCause → "Pending Office Review"
- OfficeRDReviewedQD = true → "QD Reviewed"
- OfficeRDAcceptedDPA = true → "DPA Accepted"
- VerifiedBy populated → "Verified/Closed"
- OfficeRDEntireFleet = true → "Circulated to Fleet"

**Attachments:** `Proc_InsertAccidentReportAttachment` / `_Vessel` — image blob or file path per incident

---

#### Workflow 2: Near Miss Report (FR_NearMiss)

```
SHIP SIDE                                          OFFICE SIDE
─────────                                          ───────────

1. Any crew member identifies                      
   near miss event                                 
        │                                          
        ▼                                          
2. Crew fills Near Miss form                       
   Proc_Insert_NearMiss_Vessel                     
   → Vsl_FR_NearMiss                               
   Fields: date, place, category (Injury/          
   Pollution/Property Damage), what happened,      
   suggestions, identified-by details              
        │                                          
        ▼                                          
3. 4-Factor Analysis (on ship)                     
   • Unsafe Act (dropdown, 18 options + comment)   
   • Unsafe Condition (dropdown, 28 options)       
   • Personal Factor (dropdown, 10 options)        
   • Job Factor (dropdown, 15 options)             
   Each with free-text comment field               
        │                                          
        ▼                                          
4. Master Review & Sign-off                        
   Proc_InsertUpdate_FR_NearMissHistory            
   → FR_NearMiss_VesselLink                        
   MasterReview, MasterComments,                   
   SignMasterName, SignMasterCrewId                 
        │                                          
        ▼                                          
5. XML Packet Sync ──────────────────────────────► 6. Office receives
   Status = '0' (Open)                                PR_FR_ImportNearMiss
                                                      Auto-generates: {VslCode}/NMS/{YY}/{Counter}
                                                           │
                                                           ▼
                                                   7. Office Review
                                                      PR_FR_NearMiss_OfficeLink (Insert)
                                                      → FR_NearMiss_OfficeLink
                                                      AcceptReject = true/false
                                                      Remarks (free text)
                                                      (History kept — multiple reviews possible)
                                                           │
                                                           ▼
                                                   8. Accept / Reject Decision
                                                      Proc_AccecptReject_FR_NearMiss
                                                      AccecptRejectFlag = 'A' or 'R'
                                                           │
                                                   ┌──────┴──────┐
                                                   ▼             ▼
                                              ACCEPTED       REJECTED
                                              Flag='A'       Flag='R'
                                              (615 records)  (68 records)
                                                   │
                                                   ▼
                                                   9. Office Comments & Verification
                                                      PR_FR_UpdateOffComments
                                                      • OfficeComments
                                                      • ImmediateCause (assigned by office)
                                                      • VerifiedBy, VerifiedOn
                                                      • Status → 'C' (Closed)
                                                           │
                                                           ▼
                                                   10. (Optional) Category Update by Office
                                                       PR_FR_UpdateOffNmCategory
                                                       Office can reclassify Injury/Pollution/
                                                       PropertyDamage with audit trail
                                                       → FR_NearMissCatUpdate
```

**Status values (from data):**
| Status | Meaning | Count |
|--------|---------|-------|
| `0` | Open / New | 41 |
| `C` | Closed (office verified) | 902 |

**AcceptReject flags (from data):**
| Flag | Meaning | Count |
|------|---------|-------|
| `None` | Not yet reviewed | 216 |
| `A` | Accepted | 615 |
| `R` | Rejected | 68 |
| `O` | Open (legacy?) | 32 |
| `E` | Escalated? | 12 |

**KPI tracking:** Monthly near-miss target per vessel tracked via `tbl_KPI` (VesselId, Month, Year, KPIValue)

---

#### Workflow 3: Safety Committee Meeting (SCM_MASTER)

```
SHIP SIDE                                          OFFICE SIDE
─────────                                          ───────────

1. Master schedules monthly meeting                
   (ISM Code requirement)                          
        │                                          
        ▼                                          
2. Meeting conducted onboard                       
   Occasion: M=Monthly or S=Superintendent Visit   
   Position: S=Sea or P=Port                       
   Start/End time recorded                         
        │                                          
        ▼                                          
3. Master fills SCM form                           
   Proc_InsertUpdate_SCM_MASTER                    
   → SCM_MASTER                                    
   10 structured sections:                         
   • Structured Review (6 Yes/No flags)            
   • Outstanding Items (pending/closed)            
   • Safety Practice (6 checkboxes + notes)        
   • Security (free text + cyber security)         
   • Environment (KPI + best practices)            
   • Health (4 checkboxes + notes)                 
   • Crew (complaints, resolution)                 
   • Findings × 10 (findings + corrective measure) 
   • Miscellaneous                                 
        │                                          
        ▼                                          
4. Attendance recorded                             
   SP_INSERT_SCM_RANKDETAILS                       
   → SCM_RANKDETAILS                               
   Every crew member: Rank, Name, Present/Absent   
   (~19 crew per meeting average)                  
        │                                          
        ▼                                          
5. XML Packet Sync ──────────────────────────────► 6. Office receives
                                                      (or office creates directly via
                                                      Proc_Insert_Update_Office_SCM_Master)
                                                           │
                                                           ▼
                                                   7. SEQ/DPA Reviews
                                                      Proc_Update_OfficeComment_SCM_MASTER
                                                      • OFFICECOMMENTS (free text)
                                                      • IsReviewed = true
                                                      
                                                      Monthly review cycle — office confirms
                                                      all topics were adequately covered.
```

**No status field** — workflow state inferred from:
- `IsReviewed = false` → Pending office review
- `IsReviewed = true` + `OFFICECOMMENTS` populated → Reviewed
- SCMNo auto-generated: `{VesselCode}-{DD-Mon-YYYY}`

---

#### Workflow 4: Trouble Report → Incident Escalation

```
SHIP SIDE                                          OFFICE SIDE
─────────                                          ───────────

1. Engineer/Officer creates                        
   Proc_Insert_TroubleReport_Vessel                
   → Vsl_Tbl_TroubleReport                         
   Equipment-focused: manufacturer, model,         
   kind of trouble (Hull/Machinery/Other),         
   chronological order, phenomenon                 
        │                                          
        ▼                                          
2. Sync to office ───────────────────────────────► 3. Office receives
                                                      → Tbl_TroubleReport
                                                           │
                                                           ▼
                                                   4. Office reviews
                                                      Proc_Update_TroubleReport
                                                      • Root cause + sub-cause
                                                      • Direct cause description
                                                      • Immediate actions
                                                      • Recurrence prevention
                                                      • Cost tracking (estimated/fixed/
                                                        repair cost/claim recoverable)
                                                           │
                                                   ┌──────┴──────┐
                                                   ▼             ▼
                                              RESOLVED     ESCALATE TO INCIDENT
                                              (normal       Proc_CovertTroubleToIncident
                                              closure)      Pre-fills incident form
                                                            from trouble report data
                                                            → Creates FR_Accident entry
                                                           │
                                                           ▼
                                                   5. (Optional) Fleet distribution
                                                      Proc_Insert_CirculateTroubleReport
                                                      Proc_EmailTroubleReport
```

---

#### Ship ↔ Office Sync Architecture (Legacy)

```
┌─────────────┐                        ┌─────────────┐
│  SHIP APP   │                        │ OFFICE APP  │
│ (eMarineSoft│                        │(eMarineSoft │
│  Ship-side) │                        │ Shore-side) │
│             │     XML Packets        │             │
│ Vsl_FR_*    │ ──────────────────►    │ FR_*        │
│ Vsl_Tbl_*   │  (when connectivity   │ Tbl_*       │
│ Vsl_SCM_*   │   available, via      │ SCM_*       │
│             │   PacketSent/Recd)     │             │
│             │ ◄──────────────────    │             │
│             │  (office updates       │             │
│             │   synced back)         │             │
└─────────────┘                        └─────────────┘

VIMS REPLACEMENT:
┌─────────────┐     Real-time API      ┌─────────────┐
│  VIMS PWA   │ ◄──────────────────►   │ VIMS Django │
│ (Ship/Shore │   REST + WebSocket     │  Backend    │
│  same app)  │   (online)             │  + DRF API  │
│             │   + Offline queue      │             │
│             │   (PWA service worker) │  Single DB  │
│             │                        │ ksm_cms_live│
└─────────────┘                        └─────────────┘

Key differences:
• No mirror tables (Vsl_*) needed — single database
• No XML packet sync — real-time API calls
• Offline: PWA service worker queues requests
• Same UI for ship and office (role-based views)
```

### VIMS Target State (ksm_cms_live)

**What exists in VIMS:**
- Menu stubs in `master_menu_ship` under "Web Forms": Incident Report, Near Miss, Safety Committee Meeting, Observation Notification, Trouble Report + 5 more SMS forms (all `ctrl=#` placeholders)
- `SMS` top-level menu (sr_no: 8, no children)
- `HRM506` familiarization checklist references near-miss and safety meeting topics
- `CorrectiveAction` table pattern (from Inspection module) — reusable for safety CARs
- `msc_profiles` RBAC pattern — extend with safety form_ids/process_ids

**What does NOT exist in VIMS:**
- Zero safety/incident/near-miss data tables
- Zero safety stored procedures
- No reference/lookup data for severity, root causes, unsafe acts, etc.

### Existing Roles (Relevant to Safety)

**Shore-side (from ksm_cms_live):**
| Role | Relevance |
|------|-----------|
| SEQ Manager | Primary safety oversight — DPA role |
| Marine Superintendent | Vessel technical oversight |
| Fleet Manager | Fleet-wide safety dashboard viewer |
| Technical Superintendent | Equipment-related incidents |

**Ship-side:**
| Rank | Access Level |
|------|-------------|
| MASTER | Full — create, investigate, approve, close, chair safety meetings |
| CHIEF OFFICER | Senior — create, investigate, attend meetings |
| CHIEF ENGINEER | Senior — create, investigate (engine room), attend meetings |
| All other ranks | Can submit near miss reports, attend safety meetings |

---

## 2B. M-SCAT Investigation Framework (DNV — adopted 2026-04-16)

> **Source:** `VIMS-SAFETY-DNV-MSCAT-ANALYSIS.md` (full reference wiki) compiled from `2023_DNV Practical Incident Investigation and Root Cause Analysis/` (27 files: course materials, IMO resolutions, EMSA reports, MSCAT chart).
> **User decision (2026-04-16):** All 14 diff items adopted ("all Y").
> **Binding scope:** This framework applies to **incident reporting** (primary), **near miss reporting** (lighter version using same taxonomy), and feeds the **Safety Intelligence Dashboard**. The Safety Committee Meeting module is unaffected.

### 2B.1 Loss Causation Model (canonical mental model)

Every incident in VIMS is reasoned about via DNV's 5-layer chain:

```
LACK OF CONTROL  →  BASIC CAUSES  →  IMMEDIATE CAUSES  →  INCIDENT  →  LOSS
(Mgmt System)      (Personal /         (Substandard          (event)    (above
                    Job-System          Acts +                           threshold)
                    Factors)            Conditions)
```

**Threshold Limit principle:** a loss is just an incident whose outcome crossed a damage/injury threshold. **Near misses share the full investigation taxonomy** — only the closure depth differs (see §2B.10).

### 2B.2 [Diff #1] M-SCAT Cause Taxonomy — Reference Tables

Three lookup tables seed the cause-classification picker. Sources referenced for full code lists.

| Table | Categories | Codes | Source for full list |
|-------|-----------|-------|---------------------|
| `safety_immediate_cause_act` | Substandard Acts/Practices | 1–24 (e.g., 2 Failure to Follow Procedure, 5 Failure to Inform/Warn, 10 Incorrect Navigation, 16 Using Defective Equipment, 17 Improper Operation) | `MSCAT 8.2 - Basic causes explained.pdf` |
| `safety_immediate_cause_condition` | Substandard Conditions | 25–48 (e.g., 25 Defective Tool, 33 Flammable Atmosphere, 38 Inadequate Ventilation, 39 Inadequate Warning System) | same |
| `safety_basic_cause` | Basic Causes (Personal + Job/System Factors) | 17 categories with ~170 sub-codes (cat 1–4 = Personal, cat 5–17 = Job/System) | DNV wiki §3.2 + MSCAT chart |
| `safety_lack_of_control` | Mgmt System failures | 3 areas: System / Standards / Compliance | DNV wiki §3.3 |

**Picker UI:** hierarchical tree with code prefix search (e.g., user types "5.2" → "Inadequate orientation/induction"). Free-text rationale field is **mandatory** per code selected (cannot pick a code without explaining how the evidence supports it).

**Validation:** every M-SCAT investigation must produce **at least one Lack-of-Control entry** before closure. (See bias guard #5 in §2B.11.)

### 2B.3 [Diff #2] Risk-Tiered Investigation Deadlines

Replaces the prior single 45-day deadline. The risk band is computed from severity × probability at submission and may be re-classified by the office at any review stage.

| Risk Band | Trigger | Initial Findings Due | Closure Due | Lead Investigator | Verification |
|-----------|---------|---------------------|-------------|-------------------|--------------|
| **GREEN — Negligible** | Near miss / minor / no injury & no measurable loss | Day 28 of submission | Day 30 | **Master** | HSE register entry |
| **YELLOW — Intermediate** | Hospitalisation injury · property damage · pollution contained · operational impact | Day 14 | Day 30–45 (per DPA) | **DPA (with PIC support)** | Internal audit |
| **RED — Urgent / Critical** | Fatality · loss of ship · pollution >100 t · multi-vessel · IMO Very Serious Casualty | Day 7 | Per-case (no automatic close) | **Managing Director + external expert** | Extraordinary management review |

**Default for V1:** any incident not auto-classified retains the legacy 45-day cap. Risk band determines deadline countdown shown on dashboard overdue flag.

### 2B.4 [Diff #3] Type-of-Loss Categories (replaces "Impact Category")

Multi-select. Adopt DNV's 7 verbatim — replaces the legacy 7-column severity matrix (Injury/Pollution/Business/Navigational/PSC/Security/Other).

1. **People** (Safety / Health)
2. **Asset** (Damage)
3. **Environmental**
4. **Financial** (Fines, Claims, Insurance)
5. **Non-Conformity** (Product / Service)
6. **Reputation / Complaint**
7. **Process / Business**

Legacy 7-column matrix is **migration-mapped**, not preserved (Injury → People; Pollution → Environmental; Business loss → Process/Business; Navigational → Asset+Process; PSC Detention → Non-Conformity; Security → Reputation; Other → free choice).

### 2B.5 [Diff #4] Incident Type Picklist (Current 32 Options)

Current binding behavior: the Phase 1 Incident Type picklist uses the 32 active master rows defined by `D-MAINT-CR031`. `D-MAINT-CR031` supersedes the earlier `D-MAINT-CR021` 10-option list for current dropdown/master-data behavior. Retired earlier rows, including **Missing vessel**, are not offered for new selection; historical records remain readable.

1. Collision
2. Grounding
3. Stranding
4. Touched bottom at berth / anchorage
5. Touched bottom in rivers / canals
6. Allision with Jetty / Berth / Locks
7. Allision with other Vessels
8. Allision with ice
9. Allision with Navigation Aids / Buoys / Other objects
10. Foundering
11. Capsizing / Loss of Stability
12. Flooding
13. Explosion
14. Fire
15. Cargo Damage
16. Hull / Structural Failure
17. The fouling or damaging by a vessel of a pipeline or submarine cable
18. The fouling or damaging by a vessel of an aid to navigation other than allision
19. The fouling or damaging by a vessel of a port/terminal installation
20. Failure of ship's equipment resulting in loss of vessel's electrical power
21. Failure of ship's equipment resulting in loss of propulsion
22. Failure of ship's equipment resulting in loss of steering capabilities
23. Failure of ship's equipment resulting in a delay of cargo operation of more than 6 hours
24. Failure of ship's equipment rendering the vessel in any other way unseaworthy
25. Failure of ship's equipment or hull resulting in cargo damage
26. Crew Injury
27. Pollution
28. Breach of Local Regulations
29. Stowaway Incident
30. Security Incident
31. Breach of Cyber Security
32. Other

### 2B.6 [Diff #5] Incident Workflow Background

**Current binding note:** The developed application no longer uses the old DNV phase names as user-facing phase names. Training, UI labels, meeting material, and new development must follow the current VIMS flow in Sections 3.0 and 3.2. The older DNV table in this subsection is retained only as historical investigation-framework background.

Historical DNV reference workflow, retained for investigation-framework context only:

| Phase | State | Who can advance | Loop-back allowed? |
|-------|-------|-----------------|--------------------|
| 1 | **Scene Control** | Reporter (any rank) | — |
| 2 | **Resources Allocated** | Master / DPA (per risk band) | — |
| 3 | **Evidence Collection** | Lead investigator | from Phase 5 |
| 4 | **Facts Systemized** | Lead investigator | back to Phase 3 |
| 5 | **Causes Analysed** | Lead investigator | **back to Phase 3** (the DNV "need more info?" gate) |
| 6 | **Findings Submitted** | Lead investigator | back to Phase 3 (DPA-requested rework) |
| 7 | **DPA Accepted / Report Issued** | DPA | — |
| 8 | **Follow-up / Effectiveness Verified** | DPA + PIC | — |

**Critical rule:** going back to Phase 3 from Phase 5 (or 4) **does not lose** evidence/cause data already entered. The state machine permits in-place re-opening of any earlier phase tab; the audit log records each loop-back with reason.

### 2B.7 [Diff #6] Three-Tier Recommendation Format (replaces free-text CA/PA)

Investigation closure requires three filled sections; DPA cannot accept Phase 7 if any are empty.

| Tier | Min entries | Audience | Auto-feed |
|------|-------------|----------|-----------|
| **Lessons Learned** | 1 narrative paragraph | Fleet (via Circular) | Drafts a Fleet Circular auto-linked to existing VIMS Circular module |
| **Immediate (Corrective) Actions** | ≥ 1 | Vessel-specific, 30–90 day | Auto-create CA records with verifier + due date |
| **System Actions** | ≥ 1 | Office / fleet-wide, themed | Themes: *Training & Competence · Contractor/Supplier Management · Compliance Assurance · Human Resources · Management of Change · Procedures & Standards · Equipment Management* |

Each System Action tags one of 7 themes (used for fleet trend analytics).

### 2B.8 [Diff #7] Evidence Documents Workspace

The current user-facing evidence capture is simplified by D-MAINT-CR012. Investigators use one **Documents** section instead of selecting People, Position, Parts, Paper, or Electronic categories. Each new evidence entry has:

| Field | Purpose |
|-------|---------|
| **Attachment** | JPG, JPEG, PNG, or PDF evidence file |
| **Title** | Plain-language name shown in the workspace, PDF, and later analysis |
| **Description** | Short explanation of why the attachment matters |

Users can add as many document attachments as needed. Legacy evidence tab codes (`PEOPLE`, `POSITION`, `PARTS`, `PAPER`, `ELECTRONIC`) remain in the backend serializer and database for older records, but the current UI stores new attachment entries under `PAPER`.

**Evidence Check / Evidence Matrix is no longer exposed in the current Phase 4 UI** per D-MAINT-CR015. Legacy matrix rows and backend compatibility surfaces may still exist for older records, but current users capture evidence through Documents and do not open an Evidence Check form.

**Perishable evidence prompt:** evidence deadline tasks remain available as supporting reminders, but the main evidence completion gate is now "at least one recorded evidence item" rather than five source-category completion.

### 2B.9 [Diff #8] Witness Statement and Legacy Interview Compatibility

Current Phase 4 Witness Statement capture is intentionally simple. The user-facing form has:

1. **Witness name** from the incident vessel crew list, or **Other** with a typed witness name
2. **Upload witness statement**
3. **Remark**

The legacy `vims_safety_witness_interview` table and formal/informal API validation remain available for older records and integrations. The current UI stores simplified witness statements as informal compatibility records with a system reason and stores the uploaded witness statement in the existing `witness_signature` field. It does not expose the old witness-statement text field, formal/informal selector, read-back tick, copy-to-witness control, or 4-phase interview fields.

### 2B.10 [Diff #9] Human Factors — SHELL Tags + IMO A.884(21) Domains

Every M-SCAT finding can be tagged with one SHELL element:

- **S — Software** (procedures, manuals, charts, computer programs)
- **H — Hardware** (equipment, controls, displays, ergonomics)
- **E — Environment** (weather, fatigue, noise, climate)
- **L (central) — Liveware** (the person — capability, state)
- **L (peripheral) — Liveware** (other humans — supervision, teamwork, ship-shore comms)

**7-domain checklist** (IMO Resolution A.884(21)) appears as a sub-section of the M-SCAT analysis tab. Each domain is a tab with free-text + "considered — n/a" toggle:

1. People (qualifications, experience, fatigue, health)
2. Organization on board (task division, manning, comms, workload, hours/rest)
3. Working & living conditions (ergonomics, recreation, food, motion/noise)
4. Ship factors (design, maintenance, equipment, cargo)
5. Shore-side management (recruitment, scheduling, contracts, ship-shore comms)
6. External influences & environment (weather, traffic, regulations, inspections)
7. Sequence of events (timeline, immediate conditions)

**Near miss** uses a lighter version: SHELL tag only, no 7-domain expansion.

### 2B.11 [Diff #10] Multi-Tool Analysis Workspace

Five parallel views over the same fact set. Investigator must complete **at least 2** before submitting Phase 5. RED-band incidents must complete **all 5**.

| Tool | Use | Output |
|------|-----|--------|
| **STEP timeline** | Sequential events plotting (actor × time grid) | Swimlane diagram with draggable event cards |
| **Fact Tree** | Backward-chained "what is needed?" + "is that enough?" | AND-gated tree; every leaf must trace to evidence |
| **ECF Chart** | Event-and-Causal-Factor visual | Diamond=incident · Box=event · Oval=condition · Dashed=presumptive · Arrow=causal link |
| **Barrier Analysis** | Defences-in-depth assessment | `Hazard \| Barriers existed \| Performed how \| Why failed \| Effect on incident` |
| **Change Analysis** | Compare incident-state vs ideal | 6-factor table: WHAT/WHEN/WHERE/WHO/HOW/OTHER × Incident / Prior / Difference / Effect |

Tools share underlying fact records — adding a fact in STEP makes it available to Fact Tree, ECF, etc.

### 2B.12 [Diff #11] Investigator Bias Guards (form-level validations)

Five named guards, fired at Phase-transition gates:

| # | Bias | Guard rule | Trigger point |
|---|------|------------|---------------|
| 1 | **Recency** | At least one evidence item must be recorded before leaving evidence capture; the current UI captures Documents entries with attachment, title, and description | Phase 4 → 5 |
| 2 | **Assumption** | Every fact box requires an evidence link (interview ID / document ID / photo ID) | Adding a fact |
| 3 | **Hindsight** | Decision/action records timestamped; cannot reference info dated after the event | Adding a finding |
| 4 | **Confirmation** | Current UI no longer exposes the Evidence Matrix Con-row gate; investigators document contradictory evidence in Documents, Witness Statement, and analysis notes | Phase 5 review |
| 5 | **Blame fixation** | If all root causes fall within Personal Factors (cat 1–4) AND no Lack-of-Control entry exists → block submission, require senior review | Phase 6 → 7 |

Soft warnings (1, 4) can be over-ridden with justification. Hard blocks (5) require DPA override.

### 2B.13 [Diff #12] MSC-MEPC.3/Circ.4 Auto-Population (Regulatory Export)

The IMO mandatory casualty-report fields (5 appendices) auto-populate where possible:

| Appendix | Content | Source |
|----------|---------|--------|
| 1 | Generic — date, location, reporter, investigating authority | Investigator-entered (Phase 1–2) |
| 2 | Ship particulars — IMO, flag, class, GT, crew, cargo | **Auto from VIMS vessel-particulars table** |
| 3 | Casualty analysis — sequence, hazards, contributing factors | Auto from STEP timeline + M-SCAT cause tree (Phase 5) |
| 4 | Supplementary — weather, sea state, environment | **Auto from Daily Report position-time match** (uses existing same-DB integration) |
| 5 | Field value tables (30 standardised picklists) | Backend reference data, loaded at seed time |

**Output:** "Export to MSC-MEPC.3/Circ.4 PDF" button on closed (Phase 7+) incidents. Estimated **~40 % of fields auto-fill** with no investigator typing.

### 2B.14 [Diff #13] Heinrich Ratio Panel on Safety Intelligence Dashboard

Adds a panel alongside the composite Safety Health Score. Shows the per-vessel **reporting-culture pyramid** over the rolling 3-year window, with the Heinrich/Bird benchmark overlay:

```
Benchmark    Vessel actual    Diagnosis
   1            1              1 fatality / major injury
  10            8              minor injuries (under-counted?)
  30           12              property damage events (under-counted)
 600           42              near misses (severely under-reporting)
 600+          —               hazards/observations (none captured)
```

**Flag rule:** if any layer above near-miss is missing the layers *below* it (i.e., no near misses but multiple incidents), surface a **"Reporting Culture Gap"** warning on the vessel dashboard. This is the diagnostic for under-reporting — far more actionable than headline counts.

### 2B.15 [Diff #14] Seed Case-Study Library

The Knowledge Base loads with two DNV-published worked solutions on day 1 — investigators see them when starting their first M-SCAT analysis (in-app tutorial mode):

| Case | Type | Cause coding shown |
|------|------|---------------------|
| **Navigator** (container vessel grounding, Verne Bank, Dover Strait, 2013) | Type 14 Grounding · Loss = Asset + Reputation + Process | Immediate: 5, 10×2, 16, 17, 39 · Basic: 5, 8, 12 |
| **Sinkfast** (tanker pump-room explosion + fatality, Esso Fawley, 2015) | Type 16/17 Fire/Explosion · Loss = People + Asset + Environmental | Immediate: 2, 4, 8, 17, 25, 33 · Basic: 4.9, 5, 9, 12.7, 16 |

Full narrative + recommendations stored in `safety_case_study` reference table. Both also appear as worked examples inside the Help drawer of the cause-picker UI.

### 2B.16 Mapping to Legacy (eMarineSoft) Reference Data

The legacy module already had a thinner version of M-SCAT (`Tbl_UnsafeActs` 18, `Tbl_UnsafeCondition` 28, `Tbl_PersonalFactors` 10, `Tbl_JobFactor` 15, `Mst_tbl_NearMissRootCause` 11 with 40 sub-causes). These are **superseded** by the full DNV M-SCAT taxonomy — not migrated as-is. A one-shot mapping table (`safety_legacy_cause_map`) lets read-only legacy archive views show their original codes alongside the equivalent M-SCAT code.

---

## 2C. Safety Officer Inspection (SOI) Framework (added 2026-04-16)

> **Source:** KSM SSQE Manual §4.5 ("SAFETY OFFICER"), §9.4 (SCM agenda), SQE S 608 Safety Officer Inspection Checklist, COSWP 2026 Ch 13 (Safety Officials), Regulations SI 1997/2962 (Merchant Shipping Safety Officials and Safety Committees).
> **Binding scope:** Defines the 4th V1 sub-feature — Safety Officer Inspection — and its tight coupling to the Safety Committee Meeting.
> **Interrogation:** 15 Q&A (Q-SOI-1..15), all CLOSED 2026-04-16 — see D-SOI-01..15 in Decisions Log.

### 2C.1 Overview and Regulatory Anchor

Safety Officer Inspection (SOI) is a regulated routine activity on every KSM vessel. Governing text:

- **COSWP 2026 Ch 13.4.4.1:** *"The safety officer must ensure that each accessible part of the ship has a health and safety inspection at least once every three months."*
- **SSQE Manual §4.5.2:** *"The Safety Officer must plan an inspection schedule for the entire vessel within a 3-month period, covering 1/3rd of the accessible spaces each month."*
- **SSQE Manual §4.5.2 (closing):** *"Result of such inspection shall be recorded in SQE S Form No. 608 Safety officer inspection checklist, SCM report in VIMS and the findings of inspections to be discussed in Safety, Security Environment Management meeting. Any findings which are not closed satisfactorily by the time of the SCM, the same shall be carried forward as 'Open items' in next months SCM."*

### 2C.2 [D-SOI-01] Scope — 4th V1 Sub-Feature

SOI is a **distinct V1 sub-feature** with its own data model, UI, permission set, and PDF export. It is **tightly coupled to the SCM**: inspection findings auto-feed the SCM's Item 8 and the Safety Observations for the Month table. V1 scope becomes Incident · Near Miss · SCM · **SOI**.

### 2C.3 [D-SOI-02] Safety Officer Role Assignment

- **Chief Officer is the designated Safety Officer** (SSQE §4.5.1)
- **Master may appoint 2nd Engineer to act as alternate** via a vessel-level toggle
- **Must not be Master** (COSWP 13.3.2.3)
- Stop-work authority (COSWP 13.4.6 / SSQE §4.5.1) is **NOT modelled in V1** (per D-SOI-03) — handled informally via verbal escalation to Master

### 2C.4 [D-SOI-03] Stop-Work Authority — Deferred

Stop-work authority (Safety Officer may halt any unsafe work and inform Master) is **out of V1 scope**. Captured informally via Incident/Near Miss escalation if required. Revisit as a V2 feature when utilisation data supports dedicated workflow.

### 2C.5 [D-SOI-13 + D-SOI-16] Inspection-Area Taxonomy (12 Areas — SQE S 608 baseline + Section 12)

V1 ships with **12 inspection areas**: the existing 11 from KSM SQE S 608 plus a new **Section 12 "Cross-cutting Safety & Culture"** (D-SOI-16) covering industry-standard items SQE S 608 did not previously capture. Fleet-wide standard coding (D-SOI-12):

| # | Inspection Area | Item count (approx) | Source |
|---|----------------|---------------------|--------|
| 1 | External Deck Structure | 26 | SQE S 608 |
| 2 | Accommodation | 17 | SQE S 608 |
| 3 | Navigating Bridge & Monkey Island | 16 | SQE S 608 |
| 4 | Electrical Safety | 16 | SQE S 608 |
| 5 | Engine Room and Work Shop | 37 | SQE S 608 |
| 6 | Other Machinery Spaces (Steering Gear + Emergency Generator Room + Battery Room + CO₂ Room sub-areas) | ~30 | SQE S 608 |
| 7 | All Stores (Chemical Locker, etc.) | ~35 | SQE S 608 |
| 8 | Galley / Cold Rooms | ~30 | SQE S 608 |
| 9 | All Lifting Equipment (Cranes, etc.) | ~25 | SQE S 608 |
| 10 | Mooring and Access Equipment | ~40 | SQE S 608 |
| 11 | CO₂ Room & Fixed Smothering Systems | ~10 | SQE S 608 |
| 12 | **Cross-cutting Safety & Culture** *(new, D-SOI-16)* | **12** | COSWP Ch 13 + D-38 + QEOHS-VSL-HSSE-10 |

**Total items: ~292** across 12 areas.

Each area carries its own checklist items as reference data (`safety_soi_area` + `safety_soi_item` tables). DPA maintains the master taxonomy (per D-CFG-01 pattern).

**Section 12 content (12 items, applied once per inspection regardless of physical areas covered this cycle):**

| # | Item | Rationale |
|---|------|-----------|
| 12.1 | PPE Matrix compliance — all crew observed using correct PPE per posted matrix | RightShip + OCIMF explicit check |
| 12.2 | LOTO (Lockout/Tagout) in active use for energy isolation where required | MLC + COSWP compliance |
| 12.3 | IMO signs correct, legible, not worn or torn | PSC-detainable category |
| 12.4 | Permit-to-Work system — observations during active jobs show compliance | ISM hot-work + enclosed-space coverage |
| 12.5 | Enclosed-space entry checklist completed + records evident before each entry | Top-3 PSC deficiency fleet-wide |
| 12.6 | Hot-work area — fire-watch + gas-free monitoring + stand-by arrangements visible | Tanker/bulker hot-work ignition prevention; matches DNV SA-2026-027 case learning |
| 12.7 | Working-at-height / overside — harness, tagline, stand-by person, permit in order | MLC fatality-risk area; COSWP §14 |
| 12.8 | Heat-stress / climate awareness on crew — hydration, rest rotations during tropical ops | Recent PSC + IMO emphasis for tropical operations |
| 12.9 | Supervision adequate for inexperienced crew / new joiners | Key cultural factor in Sinkfast-pattern incidents |
| 12.10 | Practicable occupational safety improvements observed (open prompt, narrative) | Safety-culture capture matches DNV M-SCAT bias-awareness (D-DNV-11) |
| 12.11 | Crew raising safety concerns / suggestions (open prompt, narrative) | MLC representation requirement |
| 12.12 | Previous SOI/SCM findings rectified since last inspection | ISM improvement-culture check — closed-loop verification |

**UI note:** Section 12 appears as a distinct section in the generated checklist (PDF/Excel) regardless of which physical areas were selected. It's always part of every inspection event (D-SOI-16 binding rule). Items 12.10 and 12.11 are text-response prompts; all others are Yes/No/NA.

### 2C.6 [D-SOI-05] Checklist Versioning and Per-Vessel Assignment

DPA maintains **versioned checklist templates**. Each version published with an effective date; historical inspections remain on the schema version they were created under (consistent with D-EDGE-11 grandfathering). Each vessel is assigned an applicable version at onboarding (Master / DPA jointly); may be re-assigned with DPA approval.

### 2C.7 [D-SOI-12] Zone Template — Fleet-Wide Standard

Same 11-area coding on every vessel. Sections that don't apply to a particular vessel (e.g., CO₂ Room on a non-CO₂-system vessel) flagged with `applicable=false` at onboarding; do not enter the 90-day compliance counter.

### 2C.8 [D-SOI-04] Inspection Cadence — 90-Day Ceiling, 80-Day Warning

- **Hard ceiling:** 90 days per applicable inspection area without inspection = overdue (dashboard red flag, SCM hard-block until resolved)
- **Soft warning:** 80 days = amber flag on dashboard, email to CO + Master
- **Target:** 1/3 of applicable areas per month (SSQE §4.5.2 rule), but Safety Officer chooses which specific areas to inspect each cycle — operational reality allowed (weather, cargo ops, etc.)

No strict per-month segmentation; any 3-consecutive-months span must cover all applicable areas.

### 2C.9 [D-SOI-10 — revised 2026-04-16] Paper-First Workflow with System-Generated Checklist

The inspection flow is **paper-first; only findings are captured digitally**. The system of record is: inspection event metadata + selected areas + findings (structured) + signed-scan attachment. Per-item Yes/No responses live on paper, not in the database.

**Workflow (5 states):**

| State | Trigger | System behaviour |
|-------|---------|------------------|
| 1. **Planned** | Safety Officer selects areas to cover this cycle; dashboard suggests ones due by 90-day rule | Record created with `area_ids[]` + `cycle_label` (e.g., Q2/2026) |
| 2. **Downloaded** | Safety Officer downloads the checklist (**PDF or Excel**, their choice) | Inspection flagged "in progress"; checklist generated dynamically from `safety_soi_area_item` reference data for the selected areas only |
| 3. **In Fieldwork** | Paper walk-through on board (or XLSX on tablet); Safety Officer + Assistant + trainees sign the paper | System idle — expects findings to be returned |
| 4. **Reported** | Safety Officer registers findings in VIMS + uploads signed scan | All selected areas stamped "Last Inspected = today" (resets 90-day counter); `safety_soi_finding` rows created with M-SCAT + priority + assignee |
| 5. **Closed** | All findings reach Master-approved closure (or acknowledged open) | Inspection event closes; findings continue their own lifecycle (feed SCM per D-SOI-14) |

**Checklist generation (State 2):**
- Dynamically built from selected areas only (not a static template)
- Header: vessel, cycle, planned date, Safety Officer, Assistant, trainees, areas covered
- Body: each area's checklist items with Yes/No/NA columns
- Footer: signature lines for SO, Assistant, Master (paper signatures; wet-signed)
- **Two formats offered**: PDF (print-ready) or Excel (tablet-friendly / editable on board)

**"Submit with no findings" path:** Safety Officer may close an inspection by reporting zero findings; system still requires the signed scan and still stamps the areas as inspected.

**Completed inspection record (digital):** inspection event + selected areas + findings (if any) + scan attachment + Master approval chain. The only PDF VIMS auto-generates post-completion is a **summary record** (not a duplicate of the checklist) — shows areas covered, findings raised, closure status, and links to the scan attachment. The paper checklist itself is the SQE S 608 / XLSX scan — no duplicate digital reconstruction.

### 2C.10 [D-SOI-08] Cross-Functional Assistant — Hard-Enforced

Per SSQE §4.5.2 ("Safety Officer should carry out the inspection assisted by an Officer from another department… to limit individual bias"):

- **Mandatory field:** every inspection record must name an Assistant Officer.
- **Both name and department pulled from Crew Management System** (no free-text — the department rule is automatically enforceable).
- **Hard rule:** Assistant's department ≠ Safety Officer's department. If the CO is Safety Officer (deck), Assistant must be from engine side (C/E, 2/E, 3/E, 4/E, Electrical Officer). If 2/E is alternate Safety Officer (engine), Assistant must be from deck (C/O, 2/O, 3/O).
- No over-ride — inspection cannot be submitted without a valid cross-functional pairing.

### 2C.11 [D-SOI-09] Crew Trainee Participation — Formal Tracking

Per SSQE §4.5.2 ("2-3 Crew members can accompany… In rotation the crew members should then be replaced every month so all the crew can be involved"):

- Each inspection record captures up to **3 crew trainees** by CrewId (optional but structured).
- System tracks a **per-crew "inspections accompanied" counter** and a **per-vessel "crew rotation coverage %"** metric over the last 12 months.
- Surfaces on the Crew dashboard and in the SCM under a new analytic line.
- Supports the SSQE training-through-participation intent at flag-state audits.

### 2C.12 [D-SOI-06] Finding Model — No Auto-Escalation

Every "No" answer on the checklist becomes a structured finding:

- Finding fields: `finding_id · area_id · item_id · description · evidence_photo_id · mscat_cause_codes (optional) · priority (High/Med/Low) · proposed_action · assigned_to · due_date · status`
- **No auto-escalation to Near Miss / Incident / PMS Defect records.** All findings stay within SOI and are followed up via the SCM.
- If Safety Officer believes a finding warrants a separate Near Miss or Incident, they file that record manually with a free-text cross-reference to the SOI finding ID.
- Exception — PMS cross-reference recommended but not auto-created: equipment-related findings may reference a PMS defect ID when known.

### 2C.13 [D-SOI-07] Finding Closure — Safety Officer + Master Approval

- Safety Officer marks a finding `pending_closure` inside the inspection report (between inspections and between SCMs — closure is not gated on the next meeting).
- **Master review + approval is mandatory** before the finding moves to `closed`. Master's approval timestamped and logged.
- Closed status is **auto-reflected into the next SCM** under the new "Closed Items" summary block (per D-SOI-14 Option C).
- Open findings **auto-carry-forward into each subsequent SCM** until closed (matches SSQE §4.5.2 closing paragraph verbatim).
- Field edit history per D-EDGE-10 applies — every finding state change logged.

### 2C.14 [D-SOI-14] SCM Auto-Feed Rules (Split Model)

- **Section "Safety Observations for the Month" (existing table)** — auto-populates with **all currently Open findings** from SOI inspections since the last SCM. Master discusses each at the meeting. Columns already include M-SCAT cause + SHELL tag (per D-DNV-01 / D-DNV-09) — these propagate from the SOI finding record.
- **New section "Closed Items Since Last Meeting" (summary block at top of SCM, between the Attendance block and Section 8)** — lists findings closed by Safety Officer + Master since the prior SCM. For-record only; no discussion required unless DPA flags.
- Both blocks carry the SOI inspection reference number (format `SOI/{VesselCode}/{YY}/{NN}`) and hyperlink to the source record.
- Item 8 numbered question ("Findings of Safety and environmental inspection conducted by Safety officer and Safety observer") in the SCM form auto-answers **Yes** if any inspection occurred in the period, with count and coverage-% figures surfaced.

### 2C.15 [D-SOI-11] Retention Alignment

Same as the rest of the Safety module (Q46 decisions):
- 3-year soft archive of inspection records (searchable by all office users)
- Cloud-stored attachments (photos, signed scans) hard-deleted at 3-year mark
- DB link reference persists; file returns 404 after purge

### 2C.16 [D-SOI-15] RBAC — Inherits Standard Safety Module Pattern

| Action | CO (SO) | 2/E (alt SO) | Master | Assistant Officer (any dept) | Crew trainees | PIC | DPA | FM |
|--------|---------|--------------|--------|------------------------------|----------------|-----|-----|-----|
| Schedule inspection | Yes | Yes (if designated) | Yes (override) | — | — | Flag only | Yes | Flag only |
| Create inspection record | Yes | Yes | No | No (signs as assistant) | No (named in record) | No | No | No |
| Edit during Draft | Yes | Yes | No | No | No | No | No | No |
| Enter findings | Yes | Yes | No | Advisory | Advisory | No | No | No |
| Submit inspection | Yes | Yes | No | No | No | No | No | No |
| Mark finding `pending_closure` | Yes | Yes | No | No | No | No | No | No |
| **Approve closure** | No | No | **Yes** | No | No | No | No | No |
| View inspection records | Yes (own vessel) | Yes (own vessel) | Yes (own vessel) | Yes (if named) | View only if named | Assigned vessels | All fleet | Fleet-wide (read-only) |
| Maintain checklist taxonomy | No | No | Propose only | No | No | Propose only | **Yes (exclusive)** | No |
| Maintain 11-area template | No | No | No | No | No | No | **Yes (exclusive)** | No |
| Override / re-open closed finding | No | No | Yes (Master) | No | No | No | Yes (DPA — safety net) | No |

### 2C.17 Integration with Safety Intelligence Dashboard

New metrics added to the vessel and fleet dashboards:

- **Inspection Compliance %** — (applicable-areas inspected within last 90 days) / (total applicable areas) × 100
- **Areas Overdue** — count of applicable areas > 90 days since last inspection
- **Open Findings by Priority** — High / Medium / Low breakdown
- **Crew Rotation Coverage** — % of crew who have accompanied ≥ 1 inspection in the last 12 months
- **Inspection → Meeting Closure Rate** — % of findings closed by the meeting after they were raised

### 2C.18 Data Model

New tables (scoped to `safety_soi_*` prefix):

- `safety_soi_area` — 11 inspection areas (reference data, DPA-maintained)
- `safety_soi_area_item` — checklist items per area with priority tier (High / Med / Low)
- `safety_soi_checklist_version` — versioned templates; vessel-assignable
- `safety_soi_vessel_area_map` — per-vessel applicable flag + last-inspected / due-inspected timestamps
- `safety_soi_inspection` — the master record (one per inspection event, covering ≥ 1 area). State: Planned / Downloaded / Reported / Closed
- `safety_soi_inspection_area` — which areas an inspection event covered
- `safety_soi_attachment` — signed-scan PDF(s) uploaded at Report time (per D-SOI-10 paper-first)
- `safety_soi_finding` — each "No" or concern → structured finding with status lifecycle (Open → Pending Closure → Master-Approved → Closed; Carried Forward possible at each SCM)
- (No `safety_soi_response` per-item table — item-level responses live on the paper scan, not in the DB)
- `safety_soi_trainee` — crew-trainee FKs per inspection (up to 3)
- `safety_soi_field_history` — appended edit log (per D-EDGE-10)

Reference data seeding:
- Load all 11 areas + items from SQE S 608 at install time
- Seed version = "v1.0 (SQE S 608 — SSQE Rev 02 baseline)" dated 2026-04-16

### 2C.19 PDF / Excel Output (per D-SOI-10 revised)

**Two distinct outputs, different purposes:**

1. **Generated checklist (before fieldwork)** — PDF or Excel, Safety Officer's choice
   - Built dynamically from the areas selected for this cycle only
   - SQE S 608 layout reproduced exactly — section-by-section Yes/No items
   - Header pre-filled (vessel, cycle, SO, Assistant, trainees, planned date)
   - All response cells left blank for wet-signed paper use (PDF) or tablet edit (Excel)
   - Download event transitions inspection to "In Progress"

2. **Summary record (after report)** — PDF only, auto-generated at submission
   - Cover: vessel, cycle, inspection reference, state, closure chain
   - Areas inspected (with Last Inspected date stamps)
   - Findings table with M-SCAT cause + SHELL + priority + assignee + status (Open / Pending Closure / Master-Approved Closed)
   - Scan-attachment reference ("Paper checklist: soi-EBK-26-0003-scan.pdf, 2.1 MB, uploaded 12-Apr 17:50 LT")
   - Flow-to-SCM indicator
   - Signature block (digital — SO + Assistant + Master)
   - Audit-trail footer (record ID, schema version, timestamps)
   - **Does NOT reproduce the per-item checklist** — the paper scan is the authoritative item-level record

Auditor leave-behind package (per D-PDF-02 configurable export) includes both the SOI summary records AND their scan attachments in the date-filtered bundle.

---

## 3. Incident Reporting

> **Current binding update (2026-06-18):** Incident Reporting now follows the developed user-facing incident flow in the frontend/backend. This subsection is the implemented SSOT for workflow, user inputs, APIs, roles, injury handling, and database tables. Older DNV-heavy phase descriptions below this update are retained as background only where they do not conflict with this binding update.

### 3.0 Implemented Workflow, API, and DB Contract

#### Current User Workflow

```
Phase 1 Intake + Scene Control
  -> Phase 2 RCA (Root Cause Analysis)
  -> Phase 3 Corrective Action
  -> Phase 4 Preventive Action
  -> Phase 5 Add Evidence
  -> Phase 6 Office Review
  -> Phase 7 Loss Evaluation
```

Internal backend class names still contain older phase numbers. User-facing labels and frontend routes are the source of truth for training and meeting material. Backend API paths are documented separately below because several compatibility endpoints intentionally keep older names. The office-communication screen is a Phase 1 handoff/compatibility screen, not a separate user-facing phase. The separate Lessons Learned screen is removed from current navigation; its old URL redirects to Office Review for compatibility. The read-only Final Record route remains available for direct audit/legacy access but is no longer shown as a visible workflow phase tab.

#### Developed Frontend Route Mapping

| User step | Current screen | Frontend route |
|-----------|----------------|----------------|
| Phase 1 | Report Incident | `/safety/incidents/:id/phase-1` |
| Phase 2 | RCA (Root Cause Analysis) | `/safety/incidents/:id/phase-2` |
| Phase 3 | Corrective Action | `/safety/incidents/:id/phase-3` |
| Phase 4 | Preventive Action | `/safety/incidents/:id/phase-3/preventive` |
| Phase 5 | Add Evidence | `/safety/incidents/:id/phase-4/paper` and legacy `/phase-4/*` evidence routes that redirect to Documents |
| Phase 6 | Office Review | `/safety/incidents/:id/phase-5` |
| Phase 7 | Loss Evaluation | `/safety/incidents/:id/phase-6` |
| Direct read-only | Legacy Final Record | `/safety/incidents/:id/phase-7` |
| Legacy redirect | Removed Lessons Learned path | `/safety/incidents/:id/phase-3/lessons` redirects to `/safety/incidents/:id/phase-5` |

#### Backend Phase Number Compatibility

`vims_safety_incident.current_phase` and several API/component names still carry older backend numbers. The shared frontend helper maps them to the current user-facing steps:

| Backend `current_phase` | User-facing step |
|-------------------------|------------------|
| 1 | Phase 1 - Report Incident |
| 2 | Phase 1 - Report Incident |
| 3 or 5 | Phase 2 - RCA (Root Cause Analysis) |
| 6 | Phase 3 - Corrective Action, with Preventive Action as a split frontend action route |
| 4 | Phase 5 - Add Evidence |
| 7 | Phase 6 - Office Review |
| 8 | Phase 7 - Loss Evaluation |
| 9 or higher | Closed / direct read-only record |

#### Phase Purpose and Inputs

| Step | Purpose | Main user input | System behaviour |
|------|---------|-----------------|------------------|
| Phase 1 Intake | Record what happened and capture first details | Vessel and Vessel code are derived from the user's vessel context or saved incident and are not manually editable after autofill/save; reporter name/rank/user, occurred/reported time, latitude, longitude, shore assistance required, location of vessel, location on board, last port, departure date, vessel condition, incident type, up to 3 loss types plus Other, risk band, narrative, weather condition, office informed yes/no, communication mode if yes, PIC/person-in-charge candidate, crew/non-crew injury if any | Creates a draft incident, validates vessel scope, stores reporter identity, captures office-notification flag/mode, handles the office-communication handoff, and prepares the Phase 2 cause-selection step |
| Phase 2 RCA (Root Cause Analysis) | Capture root cause analysis before evidence upload is treated as complete | At least one Immediate cause and one Root cause; selected cause factor (Human, Management, Vessel, Other); selected cause option; Other text when applicable; reason; safety controls; people/work process/equipment notes; human factors; final checks | Saves cause tags using the shared Near Miss factor-cause master; stores the selected option snapshot on `vims_safety_cause_tag`; shows a success message after save and scrolls to Saved causes; saved Immediate and Root cause cards expose Edit so users can update the existing cause instead of adding a duplicate; blocks advance until Immediate and Root causes are present; can send user into evidence capture. Intermediate Cause is legacy compatibility only and is not shown or accepted for new current RCA entries. |
| Phase 3 Corrective Action | Record what must be corrected for this incident | Description plus optional Due Date. Status/open-close, owner/checker, and verification fields are not shown. | Saves a corrective recommendation row and any Due Date through the linked corrective-action payload; multiple Corrective rows are allowed for the same incident; shows a success message and scrolls to saved actions; saved corrective cards expose Edit and update that existing recommendation row including Due Date; continues to Preventive Action |
| Phase 4 Preventive Action | Record what will prevent recurrence | Preventive action Description plus optional Due Date. Status/open-close, risk reduction, Remaining risk, risk-confirmation checkbox, theme, effort, and "Prevent It Happening Again" wording are not shown in the current UI. | Saves a preventive recommendation row and any Due Date through the linked corrective-action payload; multiple Preventive rows are allowed for the same incident; shows a success message and scrolls to saved actions; saved preventive cards expose Edit and update that existing recommendation row including Due Date; continues directly to Office Review |
| Phase 5 Add Evidence | Collect and describe proof before it disappears | One Documents evidence section with Attachment, Title, and Description. The user repeats the form for as many attachments as needed. Witness Statement remains available with vessel crew/Other witness selection, Upload witness statement, and Remark below the upload. Evidence Check is not shown in the current Evidence UI. | Saves new attachments under the legacy PAPER evidence tab; shows a success message after document/witness save and scrolls to saved content; saved document cards expose Edit for title/description metadata without replacing the file, and saved Witness Statement cards expose Edit to update the existing witness row; keeps legacy evidence rows for older records, and can still load simplified witness statements, interviews, and deadline-task updates |
| Phase 6 Office Review | Office reviews the incident and either closes it, sends it back, marks rework done, or issues a targeted fleet alert | Office-side users see Office Comments/lesson learnt, typed-name Accept / Close approval, a Fleet Alert action that opens a vessel-selection popup, and a send-for-rework Comment box. When an incident is currently sent back, the screen shows the latest office-typed Rework summary highlighted in red with a Rework Done button. Ship-side users see Office Comments/lesson learnt; when no note exists, the screen shows "Office comment is not added yet." Root/action counters, pre-approval summary cards, approval-role wording, send-back target selection, and Phase 7 PDF availability warning text are not shown. | Saves Office Comments on `vims_safety_incident.office_comment`, runs checks, captures signs, closes the incident for PIC or DPA on any risk band, supports PDF preview/download for office-side users without waiting for Phase 7 acceptance, can send in-app plus email Fleet Alert notifications only to selected `VesselData` ships after popup Confirm from Office Review even after Accept / Close has moved the record to its final phase, attaches the Incident PDF to the email with a short prevention-focused body, sends back to action rework with a fixed backend target phase even when the incident has not yet reached internal phase 7 and stores the typed rework instruction in the incident phase log, or lets ship/office users mark Rework Done so `state` changes from `SENT_BACK` to `UNDER_REVIEW` at backend Office Review phase 7 |
| Phase 7 Loss Evaluation | Evaluate consequence, likelihood, operational loss, repair/injury details, and estimated costs as an additional data-entry phase | First choose Loss Evaluation type: Incident Report or Injury Report; then Risk Assessment; Other Details; Cost Evaluation; Estimated Costs. Other Details auto-fills Name of master and Name of Chief Engineer from the incident vessel's current active onboard crew when saved values are blank. | Authorized ship-side and office-side users with incident form access and vessel scope can open and save one editable Loss Evaluation record per incident in `vims_safety_incident_loss_evaluation` without waiting for Office Review approval; the saved `report_type` controls whether Incident Report or Injury Report fields are shown on reload and in PDF cost blocks; existing rows without `report_type` keep the old injury-record fallback; the current UI has no closing note or Close Incident action |
| Direct read-only Final Record | Preserve the final closed record and audit trail for direct access only | No normal editing; authorized users can still access final summary data where direct legacy/audit links require it | Keeps terminal closed state, incident PDF, IMO export, auditor bundle, and band-gated reopen available without showing Final Record as a workflow tab. Field/change-history data remains available through audit APIs for authorized audit use. |

#### Current User-Facing Field Contract

| Area | Current fields / sections | Notes |
|------|---------------------------|-------|
| Incident identity | `incident_number`, `draft_reference`, `vessel_id`, `vessel_code`, `state`, `current_phase`, `schema_version` | Draft and formal numbering coexist; formal numbering is used after submit/office communication. `vessel_id` is the saved identity and `vessel_code` is resolved from auth/VesselData for display and draft numbering; Phase 1 disables Vessel and Vessel code once they are auto-filled or the incident exists, so users cannot manually alter the vessel identity. Internal UUID/auto-save status chips are not shown in the current Phase 1 or Phase 4 user headers. |
| Phase 1 timing and story | `occurred_at`, `reported_at`, `narrative` | The current UI label is **Describe What happened?** and the narrative is required with meaningful detail. The former first-check field is not exposed by the current UI/API/PDF flow and remains only as a legacy database column. |
| Phase 1 classification | `incident_type_id`, `incident_type_other`, `loss_type_primary_id`, `loss_type_secondary_id`, `loss_type_tertiary_id`, `loss_type_other`, `risk_band` | Up to three standard loss types plus Other text where selected; duplicates are blocked. Incident Type Other detail is stored when the selected incident type is Other. |
| Phase 1/2 communication | `office_notified`, `office_notification_mode`, `office_notified_at`, `dpa_notified_at`, `fm_notified_at` | Current UI labels are "Was office informed?" and "How was office informed?". The current dropdown offers `ON_CALL` and `EMAIL`; legacy stored `WHATSAPP` values remain readable but are not offered for new selection. |
| Phase 1/2 position | `latitude`, `longitude`, `position_source`, `position_daily_report_id`, `awaiting_daily_report_match` | Latitude and longitude are visible together on one Phase 1 row and stored on the incident record. They support both incident and injury reporting. Position data also supports MSC-MEPC.3 export. |
| Phase 1 reporting context | `shore_assistance_required`, `vessel_location`, `vessel_location_detail`, `onboard_location`, `risk_assessment_carried_out`, `toolbox_meeting_carried_out`, `permit_issued`, `activity_type`, `departure_date`, `vessel_condition` | These nullable incident-level fields are visible in the main Incident Report section and are shared by incident and injury reporting. Shore Assistance Required is placed beside Report time. Location of Vessel is selected from At Sea (Open sea condition), At Sea (Coastal passage), In Port, or At Anchorage; detail is retained for In Port / At Anchorage. Risk Assessment carried out, Toolbox Meeting carried out, Permit Issue, and Type of Activity are placed below Location on Board and above Departure Date / Vessel Condition. Last Port remains a legacy database/API compatibility field but is not shown, sent by the current Phase 1 frontend, or printed in the current Incident PDF. |
| Phase 1 weather condition | `weather_visibility_id`, `weather_precipitation_id`, `weather_sea_state_id`, `weather_wind_scale_id`, `weather_wind_direction_id`, `weather_lighting_source_id`, `weather_current_direction_id`, `weather_current_strength_knots`, `weather_ambient_temperature_c`, `weather_light_condition_id` | Dropdown fields use `vims_safety_incident_weather_option`; current strength and ambient temperature are text areas. Ice condition on-board and ice condition at sea remain legacy storage fields but are not shown or sent by the current Weather Condition UI. Migration `0043_incident_weather_condition_fields` is idempotent for databases where the weather option table or weather columns already exist outside Django migration state. |
| Reporter and responsibility | `reporter_name`, `reporter_rank`, `reporter_user_id`, `reporter_department`, `reporter_device_fingerprint`, `person_in_charge_id`, `pic_candidate_id`, `pic_user_id` | Reporter data starts the signature/audit chain; PIC/user owner drives later responsibility. |
| Injury handling | `external_party_injury` object now functions as the Phase 1 injury record with `injured_person_type` = `CREW` or `NON_CREW` | Non-crew keeps person/company/party type/injury level/notes. Crew captures rank from active vessel crew ranks, age, Type of Activity, and OCIMF flags. The current injury form does not show a separate **Describe What Happened** field inside Investigation - Narrative; the incident-level **Describe What happened?** narrative is authoritative for both incident and injury reports. Legacy `what_happened_narrative` storage remains readable but is not printed in the current Incident PDF. Phase 1 does not show or submit injury estimated-cost fields; current estimated-cost entry belongs to Phase 7 Loss Evaluation. Nature/source/body-area dropdowns and Type of Activity are loaded from `vims_safety_injury_dropdown_option` using field keys `NATURE_OF_INJURY`, `SOURCE_OF_INJURY`, `AFFECTED_BODY_AREA`, and `TYPE_OF_ACTIVITY`. |
| Phase 2 classification | `imo_classifier`, `investigation_depth`, `risk_band` | `imo_classifier` values are `SMC`, `MC`, `MI`, `NOT_APPLICABLE`; `investigation_depth` values are `SHALLOW`, `MEDIUM`, `DEEP`. |
| Root-cause analysis | cause `source_fact_id`, `mscat_subcode_id`, `mscat_category_id`, `mscat_description`, `causal_layer`, `analysis_tool`, `rationale` | Current flow requires at least one Immediate and one Root cause before moving onward. Saved cause cards can be edited before office approval; the edit form reuses the same fields and updates the existing cause row. `INTERMEDIATE` remains readable only as legacy stored data; current UI/API rejects new Intermediate causes and formal PDF groups legacy Intermediate rows under Root Cause. |
| Cause factors | `vims_safety_cause_tag.cause_factor`, `cause_option_id`, `cause_option_text`, `cause_other_text` | Phase 2 uses the same factor-based master as Near Miss: Human Factors, Management Factors, Vessel Factors, Other Factors. `mscat_subcode_id` remains for historical compatibility and is set to `OTHER` for new factor-based causes. |
| Safeguards and bias | safeguard name plus design/installation/maintenance/operation/testing/override M-SCAT codes; bias guards with acknowledgement/evaluation/justification | Used to avoid blame-only or single-cause closure. Safeguard technical analysis still keeps its existing M-SCAT fields. |
| Phase 4 evidence UI | Documents only | The current UI has one Documents section. Each row is Attachment, Title, and Description. Legacy People, Place, Equipment, and Photos routes redirect to Documents. |
| Phase 4 supporting tools | Witness Statement and optional Checklist | Supporting tools are collapsed by default and opened only when needed. Witness Statement opens the witness page directly and shows vessel crew/Other witness selection, Upload witness statement, and Remark below the upload. Checklist task cards show the item, status, and action controls without due-date wording or due-date values. Evidence Check / Evidence Matrix is legacy compatibility only and is not shown as a current Phase 4 tool. |
| Supporting facts | fact sequence, fact text, timestamp, evidence source, confidence, contradiction, hindsight override | Facts are currently supporting APIs/workspace data. The main simplified user flow does not stop users at a separate visible "Facts" phase. |
| Action phases | recommendation tier/theme/title/description/rationale storage; corrective action verifier/due date/status; ALARP likelihood reduction, residual risk, attestation; purchase requisition link | Current UI exposes only Corrective Action and Preventive Action. Multiple active recommendation rows are allowed for the same incident and tier. The legacy `LESSONS_LEARNT` tier remains readable for old records/API compatibility but is not a current screen, tab, dropdown option, or PDF-selector default. Current UI does not expose a separate title field; title is derived from the entered description. Corrective Action and Preventive Action show Description and optional Due Date only. Status/open-close, owner/checker, risk reduction, recommendation rationale / "Why is this needed?", theme, effort, Remaining risk, and risk-confirmation checkbox are not current user-facing action fields; incident PDF renders each saved action as a full-width bordered row/box with no left-side `Description` label column, prints the description first, prints any saved linked due date second as `Due Date: YYYY-MM-DD`, and omits status/open-close, verification, closed-at, rationale, and recommendation verification fields. |
| Phase 6 Office Review | approvals, HOD sign where required, PIC/DPA Office Review decision, send-for-rework comment, latest Rework summary, Rework Done action, `office_comment`, Fleet Alert selected vessel IDs | PIC or DPA can accept/close, send to rework, or issue an Incident Fleet Alert for every risk band. Office Comments/lesson learnt is free text with no word/character limit and is used as the Office Review closure reason when present. Send for rework requires only the rework comment plus permission and can create the `SENT_BACK` state even if the incident is still at an earlier internal phase. Fleet Alert opens a popup of active, non-deleted `VesselData` ships, requires at least one selected ship, and sends in-app plus email alerts only to those selected ships after Confirm, using `VesselData.email` for email delivery. The email attaches the Incident PDF and uses a short prevention-focused body. Fleet Alert remains available from the Office Review screen after Accept / Close moves the incident to the final backend phase; early investigation phases remain blocked. Ship-side users always see the Office Comments/lesson learnt card; if no note exists, it shows "Office comment is not added yet." If the incident is sent back, users also see the latest Rework summary from the office textbox highlighted in red, and ship or office users can click Rework Done to return the incident to Office Review/`UNDER_REVIEW`. |
| Phase 7 Loss Evaluation | `report_type`, consequence, likelihood, risk level, master/chief engineer names, incident repair/loss/cost fields, injury safe-working-practice/rest/repatriation/hospitalization/evacuation/cost fields | Stored in `vims_safety_incident_loss_evaluation`. The current UI requires the user to choose Incident Report or Injury Report first; the selected nullable `report_type` is persisted by migration `0056_incident_loss_evaluation_report_type` and controls visible fields on reload and Loss Evaluation PDF cost blocks. Existing rows without `report_type` keep the old fallback that infers Injury Report when an injury row exists. Authorized ship-side and office-side users with `SAF_F_001` access and vessel scope can open and save Loss Evaluation before Office Review approval or after Office Review closure when permission scope allows; it has no closing note, no Close Incident control, and no closure gate. Name of master and Name of Chief Engineer are auto-filled from current active onboard `Crew_Onboarding_History`/`HRM501`/`master_applied_rank` records for the incident vessel only when the saved Loss Evaluation values are blank. Safe Working Practice uses the existing `vims_safety_injury_dropdown_option` master with field key `SAFE_WORKING_PRACTICE`; CR-048 seeds the active Code of Safe Working Practices options and deactivates stale placeholder choices. |
| Direct read-only final record | closing reason, closed date/by, simplified phase history, approvals, incident PDF, IMO export, auditor bundle, reopen | Read-only except authorized reopen and hidden from the visible phase tabs. Routine user-facing final record access does not show a Change History card or History Rows metric. |

#### Current Simplifications and Compatibility Notes

- User-facing flow is Phase 1 through Phase 7. Supporting DNV concepts still exist in code: M-SCAT, cause layers, safeguards, bias guards, chain of custody, interviews, ALARP, and verification. Evidence Matrix remains compatibility-only for older records and is no longer a current Evidence user tool.
- There is no standalone user-facing "Facts Systemized" phase in the current main flow. Fact APIs and a fact workspace exist as support for evidence/cause/action quality.
- The incident register no longer shows the implementation-facing Current Scope card. It shows Vessel, `risk_band`, and Status filters; global office users can choose from all active ships, and selecting a ship sends the existing `vessel_id` incident-list filter. The register table labels the risk band column as `risk_band` and the lifecycle column as Status. Routine incident pages also avoid duplicate module breadcrumbs/page headings and internal incident UUID/status chips. The phase tabs are the single phase number/name indicator; phase content does not repeat separate Phase X/phase-title header cards.
- Some frontend route names and component names still use older backend phase numbers. Example: the Office Review UI is user-facing Phase 6 but calls `/phase-5/*` APIs implemented by `IncidentPhase7*` backend views.
- `office-communication` and `resource-handoff` API/route names are retained for Phase 1 handoff compatibility.
- The Final Record UI is not part of the visible workflow tabs. Direct final-record/closure routes remain compatibility/audit surfaces even though some component/schema names still refer to Phase 9/closure summary.
- Older aliases remain registered for compatibility; new development should prefer the current API table below.

#### Current Incident PDF Output

- In Phase 6 Office Review, the current user-facing PDF option is one checkbox: **Print Loss Evaluation**. Summary, Reporter Details, Injury Details, Root Cause Analysis, Corrective and Preventive Actions, Evidence (Documents), and Signature are compulsory in the download request. Checking Print Loss Evaluation adds the existing `estimated_cost` PDF section key, which now prints the Phase 7 Loss Evaluation blocks. The legacy backend `lessons_learned` section key remains supported only for old/direct export compatibility.
- The PDF title prints `Injury Report` when a Phase 1 injury row exists; otherwise it prints `Incident Report`.
- Summary prints the incident classification and context rows. **Describe What happened?** is not printed at the top of Summary. For standard **Incident Report** output it prints below the intake/detail sections and immediately before **Root Cause Analysis**. For **Injury Report** output it prints after **Reporter Details** and before **Injury Details**. Legacy injury-row `what_happened_narrative` text is not printed. Odd trailing summary rows leave the unused cells blank; filler cells do not print `Not recorded`.
- Office Review comments are excluded from Summary and print in the final Closure area as one undivided full-width **Office comments/ lesson learnt** block immediately before Signature when present. The stored `office_comment` text is passed through as one comment block, preserving typed line breaks and repeated spaces and avoiding artificial chunk splits. The stored `closure_reason`, a separate Comment row, and filler labels are not printed in the current Incident PDF.
- Evidence (Documents) prints after Corrective Actions and Preventive Actions. It prints each saved attachment as a separate document block using the saved title when available, with Description and File rows. It does not print generic numbered labels such as `Attachment 1` / `Attachment 2`, and it does not print legacy evidence-note-only rows. Saved Witness Statements print as separate witness blocks named `Witness Statement - <witness display>` where a witness display exists, then print a clickable witness-statement attachment link when the stored upload is downloadable and Remark rows inside the block. The old free-text `What the witness said` value is not printed even when legacy rows contain it.
- Immediate Cause and Root Cause each print once as their own blocks with cause factor on the left and cause/reason on the right. Location of Vessel prints once; any In Port / At Anchorage detail is appended in the same value, such as `In Port - Singapore`, and no separate Specific vessel location row is printed.
- Current action PDF output separates saved actions into **Corrective Actions** and **Preventive Actions** blocks. Each action prints as a full-width bordered row/box with no left-side `Description` label column; the first line is the description and any saved linked due date appears on the second line as `Due Date: YYYY-MM-DD`. It does not print a separate due-date row, recommendation rationale / "Why is this needed?", action status, physical verification note, closed-at, or recommendation verification rows. Legacy Lessons Learned PDF output remains supported only when the legacy section is explicitly requested or reached through older direct export defaults.
- Current Incident PDF signature output prints Reporter signature and PIC / DPA office signature rows only. Master signature and HOD signature rows are not printed.
- Incident PDF preview/download and MSC-MEPC.3/Circ.4 export are not blocked only because Office Review, Phase 7 acceptance, or closure is pending. Record-type and regulatory applicability checks still apply.

#### Database Changes Required on Server

The incident flow uses these current `vims_safety_incident` columns added/confirmed by the developed implementation:

- `office_notified` nullable boolean/bit
- `office_notification_mode` nullable text, allowed values `ON_CALL`, `WHATSAPP`, `EMAIL`
- `office_notified_at` nullable datetime
- `dpa_notified_at` nullable datetime
- `fm_notified_at` nullable datetime
- `office_comment` nullable text for Office Review comments, with no word/character limit
- `loss_type_secondary_id` nullable integer
- `loss_type_tertiary_id` nullable integer
- `loss_type_other` nullable text, max 256 characters
- `weather_visibility_id` nullable UUID
- `weather_precipitation_id` nullable UUID
- `weather_sea_state_id` nullable UUID
- `weather_wind_scale_id` nullable UUID
- `weather_wind_direction_id` nullable UUID
- `weather_lighting_source_id` nullable UUID
- `weather_current_direction_id` nullable UUID
- `weather_current_strength_knots` nullable text
- `weather_ambient_temperature_c` nullable text
- `weather_ice_condition_onboard_id` nullable UUID
- `weather_ice_condition_at_sea_id` nullable UUID
- `weather_light_condition_id` nullable UUID
- `imo_classifier` nullable text, allowed values `SMC`, `MC`, `MI`, `NOT_APPLICABLE`
- `investigation_depth` nullable text, allowed values `SHALLOW`, `MEDIUM`, `DEEP`
- position-related fields including latitude/longitude and Daily Report matching metadata where available
- `external_party_injury` JSON/object payload where crew and non-crew injury is captured; `injured_person_type` controls which fields are shown and validated

Required Django migrations:

- `psc-backend/apps/safety/migrations/0037_incident_office_notification_fields.py`
- `psc-backend/apps/safety/migrations/0038_incident_multiple_loss_types.py`
- `psc-backend/apps/safety/migrations/0043_incident_weather_condition_fields.py`
- `psc-backend/apps/safety/migrations/0044_seed_incident_weather_options.py`
- `psc-backend/apps/safety/migrations/0052_incident_office_comment.py`

Important related tables used by the implemented incident workflow:

- `vims_safety_incident`
- `vims_safety_incident_weather_option`
- `vims_safety_incident_phase_log`
- `vims_safety_incident_evidence`
- `vims_safety_evidence_item`
- `vims_safety_chain_of_custody`
- `vims_safety_witness_interview`
- `vims_safety_incident_fact`
- `vims_safety_incident_cause_tag`
- `vims_safety_incident_safeguard_failure`
- `vims_safety_recommendation`
- `vims_safety_corrective_action`
- `vims_safety_field_history`

#### Primary API Paths

| API | Method | Purpose |
|-----|--------|---------|
| `/api/safety/incidents/` | GET | List incidents |
| `/api/safety/incidents/` | POST | Create incident draft |
| `/api/safety/incidents/{id}/` | GET/PATCH | Retrieve or edit incident master row |
| `/api/safety/incidents/position-prefill/` | GET | Position lookup from Daily Report tolerance window |
| `/api/safety/incidents/{id}/phase-1/` | GET/PATCH | Phase 1 intake |
| `/api/safety/incidents/{id}/phase-1/submit/` | POST | Submit Phase 1 |
| `/api/safety/incidents/{id}/resource-handoff/` | GET/PATCH | Office Communication / resource handoff compatibility endpoint |
| `/api/safety/incidents/{id}/resource-handoff/submit/` | POST | Confirm Office Communication and move to root-cause investigation |
| `/api/safety/incidents/{id}/phase-2/` | GET/PATCH | Alias for Office Communication update |
| `/api/safety/incidents/{id}/phase-2/submit/` | POST | Alias for Office Communication submit |
| `/api/safety/incidents/{id}/phase-2/analysis/` | GET/PATCH | User-facing Phase 2 RCA (Root Cause Analysis) workspace |
| `/api/safety/incidents/{id}/phase-2/analysis/mscat/` | GET | Legacy/search support for M-SCAT-backed compatibility fields |
| `/api/safety/incidents/{id}/phase-2/analysis/causes/` | GET/POST | Add cause |
| `/api/safety/incidents/{id}/phase-2/analysis/causes/{cause_id}/` | PATCH | Edit cause |
| `/api/safety/incidents/{id}/phase-2/analysis/safeguards/` | GET/POST | Add safeguard failure |
| `/api/safety/incidents/{id}/phase-2/analysis/safeguards/{safeguard_id}/` | PATCH | Edit safeguard failure |
| `/api/safety/incidents/{id}/phase-2/bias-guards/` | GET/POST | Read/submit bias guard checklist |
| `/api/safety/incidents/{id}/phase-2/override-blame/` | POST | Blame-fixation override |
| `/api/safety/incidents/{id}/phase-3/` | GET | User-facing action workspace backing Phase 3 Corrective Action and Phase 4 Preventive Action routes |
| `/api/safety/incidents/{id}/phase-3/recommendations/` | GET/POST | Add corrective/preventive recommendation/action |
| `/api/safety/incidents/{id}/phase-3/recommendations/{recommendation_id}/` | PATCH | Edit existing corrective/preventive recommendation/action row |
| `/api/safety/incidents/{id}/phase-4/evidence/` | GET/PATCH | User-facing Phase 4 evidence workspace |
| `/api/safety/incidents/{id}/phase-4/evidence/attachments/` | POST/GET/PATCH/DELETE | Upload, preview, edit title/description metadata, or delete evidence attachment |
| `/api/safety/incidents/{id}/phase-4/chain-of-custody/` | GET/POST | Chain-of-custody rows |
| `/api/safety/incidents/{id}/phase-4/evidence-matrix/` | GET/POST | Legacy Evidence Matrix compatibility rows; not linked by the current Phase 4 UI |
| `/api/safety/incidents/{id}/phase-4/interviews/` | GET/POST | Witness interview rows |
| `/api/safety/incidents/{id}/phase-4/interviews/{interview_id}/` | PATCH | Edit existing Witness Statement row |
| `/api/safety/incidents/{id}/phase-4/interviews/{interview_id}/statement-attachment/` | GET | Download the stored Witness Statement attachment for PDF links |
| `/api/safety/incidents/vessels/` | GET | Vessel dropdown options for the Incident register, using active `VesselData` rows within the user's vessel scope |
| `/api/safety/incidents/{id}/phase-4/evidence/deadline-tasks/{task_id}/` | PATCH | Complete/justify evidence-preservation deadline task |
| `/api/safety/incidents/{id}/phase-4/facts/` | GET/POST | Supporting facts |
| `/api/safety/incidents/{id}/phase-4/facts/sources/` | GET | Evidence sources for facts |
| `/api/safety/incidents/{id}/phase-4/facts/gate/` | GET | Fact/evidence gate |
| `/api/safety/incidents/{id}/phase-4/facts/{fact_id}/` | PATCH | Edit supporting fact |
| `/api/safety/incidents/{id}/phase-4/facts/reorder/` | POST | Reorder facts |
| `/api/safety/incidents/{id}/phase-4/facts/contradictions/` | POST | Record contradiction |
| `/api/safety/corrective-actions/` | GET/POST | List/create linked corrective actions |
| `/api/safety/corrective-actions/{id}/transition/` | POST | Advance corrective action status |
| `/api/safety/corrective-actions/{id}/verify/` | POST | Record physical verification |
| `/api/safety/corrective-actions/{id}/link-pr/` | POST | Link corrective action to Purchase requisition |
| `/api/safety/incidents/{id}/phase-5/preflight/` | GET | User-facing Phase 6 Office Review/PDF preview info, including `rework_summary` from the latest active send-back phase log when the incident is currently sent back |
| `/api/safety/incidents/{id}/phase-5/hod-signature/` | POST | Capture HOD signature |
| `/api/safety/incidents/{id}/phase-5/accept/` | POST | PIC or DPA accepts/closes any risk band and can save Office Comments |
| `/api/safety/incidents/{id}/phase-5/approve-red/` | POST | Legacy RED compatibility alias; current Office Review still accepts PIC or DPA and does not require FM |
| `/api/safety/incidents/{id}/phase-5/send-back/` | POST | PIC or DPA sends incident back for rework with one free-text comment; the current UI sends a fixed action-rework target and does not expose a phase picker |
| `/api/safety/incidents/{id}/fleet-alert/` | GET/POST | Office Review Incident Fleet Alert. GET returns active ships from `VesselData`; POST requires selected vessel IDs and sends in-app plus email only to those selected ships, with the Incident PDF attached to the email |
| `/api/safety/near-miss/{id}/fleet-alert/` | GET/POST | HIGH-priority Near Miss Fleet Alert. GET returns anonymised draft and selected-vessel scope; POST records issue, writes in-app notifications, sends one selected-vessel email batch using `VesselData.Email` with the Near Miss PDF attached, and returns notification/email counts |
| `/api/safety/incidents/{id}/phase-6/` | GET | User-facing Phase 7 Loss Evaluation workspace for authorized ship-side or office-side users with incident form access and vessel scope; returns `choices.report_type`, the saved/effective report type, and officer-name defaults for blank master/chief engineer fields |
| `/api/safety/incidents/{id}/phase-6/` | PATCH | Save editable Phase 7 Loss Evaluation fields, including selected `report_type`, without requiring Office Review approval/backend `current_phase` 8 |
| `/api/safety/incidents/{id}/phase-6/verify/` | POST | Legacy effectiveness verification compatibility endpoint; not the current visible Phase 7 UI |
| `/api/safety/incidents/{id}/phase-6/close/` | POST | Compatibility endpoint that rejects closure because incident close is handled in Phase 6 Office Review |
| `/api/safety/incidents/{id}/phase-7/closure/` | GET/PATCH | Direct read-only final-record/closure summary for legacy/audit access |
| `/api/safety/incidents/{id}/reopen/` | POST | Reopen closed incident by band authority |
| `/api/safety/export/incident/{id}/pdf/` | GET | Authenticated incident PDF download |
| `/api/safety/export/msc-mepc-3/{id}/` | GET | MSC-MEPC.3/Circ.4 export |
| `/api/safety/export/auditor-bundle/` | POST | Auditor bundle export |
| `/api/safety/incidents/{id}/audit/` | GET | Combined audit payload |
| `/api/safety/incidents/{id}/audit/phase-log/` | GET | Phase timeline |
| `/api/safety/incidents/{id}/audit/field-history/` | GET | Field history |

Legacy aliases remain for compatibility, including `/api/safety/incidents/{id}/evidence/`, `/api/safety/incidents/{id}/analysis/`, `/api/safety/incidents/{id}/recommendations/`, and public compatibility paths under `/phase-3/analysis/` or `/phase-2/evidence/`.

#### Roles and Permissions

- Create incident: Master, CO, CE, 2/E.
- User-facing RCA, action, and evidence edit: authorized users can open and save RCA, corrective action, preventive action, facts, and evidence while the incident remains before office approval/closure/supersession, even when `current_phase` has not reached the legacy backend phase number for that saved data. Saved RCA causes, action cards, evidence documents, and Witness Statements expose Edit controls that update the existing row instead of creating duplicates. Ordered submit/continue transitions still enforce workflow movement.
- Phase 1 edit: top-4 vessel officers can edit while the record remains before office approval; saving Phase 1 edits preserves existing injury rows unless the injury payload is explicitly changed.
- Office Communication edit/submit: Master, CO, CE, DPA, FM.
- Root cause edit: Master, CO, CE, HOD, DPA, FM, with RED edit authority controlled for office/fleet authority.
- Evidence edit: Master, CO, CE, HOD, DPA, FM; RED investigations are read-only to users without RED edit authority. Current Phase 5 Add Evidence document saves use the legacy Phase 4 evidence endpoints and can be edited while the incident remains before office approval/closure.
- Action phases: Master, DPA, FM for RED edit; HOD review/signature where applicable.
- Office Review: PIC or DPA with process permission can accept/close or send to rework for every risk band. FM-specific RED Office Review is legacy-only and is not required in the current implemented flow. Office Comments are saved on the incident and provide the Office Review closure reason when present.
- Loss Evaluation save: authorized ship-side and office-side users with `SAF_F_001` access and vessel scope can save Loss Evaluation without waiting for Office Review approval. Loss Evaluation is additional data entry and has no current close action.
- Reopen authority remains the legacy band-gated path unless changed by a separate CR.


> **Status:** Current implemented SSOT locked to developed Incident flow as of 2026-07-03. Investigation framework still uses DNV/M-SCAT concepts from section 2B where implemented, but the binding user-facing flow is Phase 1 through Phase 7 as documented above; Final Record is direct/read-only rather than a visible workflow phase.

### 3.1 Scope & Definitions
- **Incident:** any event whose outcome crosses the loss threshold (injury · damage · environmental release · reputational impact). Per DNV Loss Causation Model (§2B.1) — same chain as a near miss, only the threshold differs.
- **Severity classification:** computed from Type-of-Loss (§2B.4) × probability → Risk Band (RED/YELLOW/GREEN per §2B.3) → drives investigator level and deadline.
- **Incident Type picklist:** 32 active reportable-type options (§2B.5); retired earlier options, including Missing vessel, are not offered for new selection under `D-MAINT-CR031`.
- **Regulatory anchors:**
  - ISM Code Ch.9 (incident reporting, investigation, corrective action)
  - IMO Casualty Investigation Code (Resolution A.1075(28)) — 5 principles in §2B
  - IMO Resolution A.884(21) — 7 human-element domains (§2B.10)
  - IMO MSC-MEPC.3/Circ.4 — mandatory reporting fields (auto-export per §2B.13)
  - MLC 2006 — work/rest hours linkage when fatigue is a finding
  - Flag-state casualty reporting — manual outside VIMS; "Flag State Informed?" toggle on form (decision Q44)

### 3.2 Workflow

Current developed user flow:

```
Phase 1 Report Incident
  -> Phase 2 RCA (Root Cause Analysis)
  -> Phase 3 Corrective Action
  -> Phase 4 Preventive Action
  -> Phase 5 Add Evidence
  -> Phase 6 Office Review
  -> Phase 7 Loss Evaluation
```

This is the UI and training flow. Final Record is direct/read-only legacy/audit access, not a visible workflow phase tab. The older DNV state summary below is retained only as historical background and must not be used for UI labels or route naming.
Historical note: older DNV 8-phase material below is superseded by the developed user flow above.

Historical DNV state names are retained only in the background model sections. They are not current UI phases.

Current rework behaviour: Office Review can send the incident back with a reason, and closed incidents can be reopened only by authorized roles/processes.

### 3.3 Data Model
Core tables (DNV-aligned):
- `safety_incident` — the master record (1 row per incident; stores internal backend `current_phase`, mapped to the current user-facing flow in Section 3.0)
- `safety_incident_phase_log` — append-only state-change audit (every phase transition + every loop-back with reason)
- `safety_evidence` — child of incident, FK to one of 5 categories (Position/People/Parts/Paper/Electronic) per §2B.8
- `safety_evidence_matrix` — Pro/Con rows per major finding (confirmation-bias guard)
- `safety_interview` — legacy-compatible child of evidence/People; current UI stores simplified Witness Statement records per §2B.9
- `safety_interview_qa` — child Q&A rows with type tag
- `safety_cause_finding` — child of incident; FK to one of `safety_immediate_cause_act` / `safety_immediate_cause_condition` / `safety_basic_cause` / `safety_lack_of_control`; required `evidence_link_id` and `rationale_text`
- `safety_human_factor_tag` — SHELL element + IMO A.884(21) domain notes
- `safety_analysis_step` / `safety_analysis_facttree` / `safety_analysis_ecf` / `safety_analysis_barrier` / `safety_analysis_change` — per-tool node tables (share `safety_fact` parent)
- `safety_recommendation` — 3-tier output (tier = Lessons / Immediate / System; system-action carries theme tag)
- `safety_corrective_action` — child of recommendation; verifier, due date, physical-verification record (mirrors PSC CAR pattern)
- `safety_physical_verification` — mirrors `psc_physical_verification` (decision Q45)
- `safety_attachment` — cloud-link only, hard-delete after 3 years (decision Q46)
- `safety_legacy_cause_map` — one-shot read-only mapping for legacy archive views (§2B.16)

Reference tables seeded at install:
- `safety_immediate_cause_act` (24 rows — codes 1–24)
- `safety_immediate_cause_condition` (24 rows — codes 25–48)
- `safety_basic_cause` (~170 rows across 17 categories)
- `safety_lack_of_control` (3 rows)
- `safety_loss_type` (7 rows per §2B.4)
- `safety_incident_type` (32 active rows per §2B.5; retired earlier options are inactive under `D-MAINT-CR031`)
- `safety_event_type` (M-SCAT type-of-event codes)
- `safety_recommendation_theme` (7 themes per §2B.7)
- `safety_case_study` (seeded with Navigator + Sinkfast per §2B.15)

### 3.4 Roles & Permissions (locked 2026-04-16, Round 13 Q47 + Q48)

Risk-tiered investigation chain with current Office Review authority (D-MAINT-CR044 supersedes the old closer-by-band rule for Office Review decisions):

| Band | Investigator | Current Office Review closer |
|------|--------------|--------|
| **GREEN** | Master | **PIC or DPA** |
| **YELLOW** | Master + PIC (joint) | **PIC or DPA** |
| **RED** | DPA + External expert | **PIC or DPA** |

**Creation:** Top-4 officers (Master, CO, CE, 2E) create incidents. **Any rank** creates near misses (Q48.4 — reporting-culture best practice).

**SSQE:** folded into DPA role (no separate permission set) — Q47.2 Option A.

**Fleet Manager baseline:** read + flag + comment (comment kept **outside formal investigation record** to keep ISM audit trail pure — Q47.3 Option C). FM gains elevated authority only for **RED closure** and **RED-band blame-fixation override**.

**Current Office Review authority supersession:** D-MAINT-CR044 supersedes the old FM RED-closure rule for the implemented Office Review path. PIC or DPA can accept, close, or send rework for GREEN, YELLOW, and RED incidents.

**Blame-fixation hard-block override (D-DNV-11 #5):**
- GREEN / YELLOW → DPA
- RED → Fleet Manager

**Cross-vessel visibility:**
- PIC: read-only on non-managed vessels + can borrow lessons-learned into own vessel circulars (Q47.6.1)
- Master: read-only on closed incidents fleet-wide for learning (Q47.6.2)
- Vetting access: Master drives on-screen + generates PDF export for auditor leave-behind (Q47.6.3 — **updates Q46** which previously said "no PDF export for auditors")

**Meeting creation:** Master or CO can host and prepare either Regular or Ad-Hoc SCM using the `meeting_type` selector. Master remains the final sign-off authority.

**Admin/config maintenance:**
- M-SCAT cause taxonomy → **DPA only** (Q48.1)
- Guidance Library → **DPA + PIC** (Q48.2 split)
- Case Study Library → **DPA only** (Q48.2 split)
- Recommendation Themes → **DPA only** (Q48.3)
- Fleet Circular approval → **reuses existing VIMS Circular module** (`/api/circular/`, office+ship endpoints already deployed) — no Safety-specific approval chain (Q48.5)

Full permission matrix is in `VIMS-SAFETY-REQUIREMENTS-INTERROGATION.md` Round 13 (Q47 FINAL).

### 3.5 Notifications & Escalation
- All incidents → Slack notification to PIC + DPA + safety channel (decision prior)
- RED-band auto-pages Managing Director and triggers external-expert engagement workflow
- Overdue dashboard flag at 80% of risk-band deadline + at deadline (per §2B.3)
- No auto-escalation between bands — DPA may re-classify at any review stage with reason logged

### 3.6 Regulatory Compliance
- **ISM Ch.9** — satisfied by Phases 6–8 audit trail
- **IMO Casualty Investigation Code** — 5 principles encoded as bias guards (§2B.12) + report-content checklist on Phase 7 export
- **IMO MSC-MEPC.3/Circ.4** — auto-populated PDF export per §2B.13
- **Flag State** — manual report outside VIMS; "Flag State Informed?" toggle + supporting attachment on form
- **RightShip vetting** — vessel dashboard is the audit-presentation tool (decision Q46)

---

## 4. Near Miss Reporting

> **Status:** Implemented V1 behavior, revised 2026-06-15.

### 4.1 Scope & Definitions
A **near miss** is the incident chain (§2B.1) where the outcome did **not** cross the loss threshold. It uses a lightweight capture flow and the shared Safety M-SCAT reference data.

Implementation update: Near Miss no longer uses the Incident M-SCAT picker for Immediate Cause. The current V1 form uses the dedicated factor-based cause framework documented in 4.3 and 4.5.

### 4.2 Workflow

```
Submitted by vessel → Office Comments / Rework → Accepted → Closed
```

- Any authorized vessel user can submit a near miss.
- If Office sends a near miss back for rework, the **Master can perform the rework regardless of who originally reported it**.
- HIGH priority requires the stronger office/fleet-learning path before closure; LOW/MEDIUM follow the lighter closure path.
- Current HIGH-priority Near Miss Fleet Alert issue writes in-app `NEAR_MISS_FLEET_ALERT` notifications and sends one BCC email batch to selected vessel `VesselData.Email` recipients, with `HSSEQ@kaizenship.net` in CC, the Near Miss PDF attached, and a short prevention-focused body. The Circular module handoff remains separate.

### 4.3 Create Form Rules
- **Near Miss Type is removed** from the create form.
- **Category** is the single user-facing field. It combines the old Category options and Possible Loss Type options into one dropdown. This is a UI merge only; existing DB fields remain for compatibility.
- Category supports up to 3 selected values.
- Category dropdown has one custom option only: **Other - Specify**.
- Cause analysis is split into four factor cards: **Human Factors**, **Vessel Factors**, **Management Factors**, and **Other Factors**.
- Each factor card has two dropdowns: **Immediate Cause** and **Root Cause**.
- Every factor/stage dropdown includes **Other** and **Not Applicable**.
- If **Other** is selected, the user must type the custom cause text for that factor and stage.
- Place is one of `At Anchor`, `At Sea`, `At Port`.
- Description must be at least 100 characters.
- Severity must be selected.
- If severity is **High**, image upload is mandatory before submission.
- While submit is in progress, the UI must show **Processing** and prevent duplicate clicks.
- The previous 5-per-day near-miss submission cap is removed; users may submit as many near misses as required.

### 4.4 Reporter Identity
- The anonymous reporting concept is removed.
- Reporter name, rank, and user reference are stored and shown to Master and authorized office users according to vessel scope and safety permissions.
- PDFs do not print any "Reporter identity is masked" wording.

### 4.5 Data Model
Reuses the incident schema with `record_type='NEAR_MISS'` on `vims_safety_incident`.

Current Near Miss cause data:
- `vims_safety_incident.near_miss_factor_causes` stores the selected factor causes as JSON text.
- `vims_safety_near_miss_cause_option` stores the active dropdown values for each `(factor, cause_stage)` pair.
- Factors are `HUMAN`, `VESSEL`, `MANAGEMENT`, and `OTHER`.
- Cause stages are `IMMEDIATE` and `ROOT`.
- Old M-SCAT compatibility fields (`near_miss_mscat_category_id`, `near_miss_mscat_subcode_id`, `near_miss_mscat_subcode_ids`) remain in the table for historical records only. New create/rework saves clear those fields and use `near_miss_factor_causes`.

### 4.6 PDF Rules
- Near miss PDF is a lightweight report: event, category, factor causes, immediate action, suggestion/preventive action, reporter details, office comments/rework history, and closure where available.
- High-risk / learning sections are printed only when recorded.
- Duplicate Office Comment blocks must not be printed.

### 4.7 Trend Analysis & KPIs
- Heinrich Ratio panel (§2B.14) remains the primary near-miss-vs-incident health indicator.
- Repeat cause analysis uses selected Category plus the factor cause JSON where available. Historical rows may still fall back to old M-SCAT compatibility fields.

---

## 5. Safety Committee Meeting Minutes

> **Status:** Implemented V1 behavior, revised 2026-06-09.

### 5.1 Scope & Frequency
SCM covers Regular monthly meetings and Ad-Hoc meetings. Master and Chief Officer can host either meeting type. Ad-Hoc meetings do not replace the monthly Regular SCM cadence.

### 5.2 Workflow

```
Draft → Submitted to Office → Closed
```

- Master/CO completes the meeting form and clicks **Submit to Office**.
- Database state is stored as `SUBMITTED`; UI displays this as **Submitted to Office**.
- Authorized office users enter **Office Comment**.
- Saving Office Comment changes the meeting to `CLOSED` and stops vessel-side editing.

### 5.3 Data Model
- Main table: `vims_safety_scm_meeting`.
- Child tables: attendance, agenda, signatures/legacy compatibility, and legacy fields where applicable.
- Active state values used by V1 are `DRAFT`, `SUBMITTED`, and `CLOSED`. `SIGNED_OFF` / `REOPENED` may remain for legacy compatibility.

### 5.4 Auto-Fetch Inputs
SCM must continue to fetch:
- WRH attendance/rest-hour status,
- latest circulars / safety alerts / work instructions,
- recent near misses,
- PSC/SOI findings and closed-since-last items.

These feeds must be optimized by query batching and bounded result sets. SCM meeting creation is blocked by `D-MAINT-CR014` until WRH readiness is clear; after a meeting exists, WRH gaps remain visible warnings for detail, PDF, and Office Comment closure.

### 5.5 Action Item Tracking
SCM agenda sections record discussion, decisions, suggestions/recommendations, and carried-forward findings. Open SOI/PSC items continue to carry forward until closed.

### 5.6 Shore-Side Visibility and Closure
DPA, FM, Shore HOD, and Marine Superintendent profile users can enter Office Comment. Office Comment is restricted to office users only. Once saved, the meeting is closed.

### 5.7 PDF Rules
- SCM PDF follows the 10-section legacy-aligned format, with current simplified wording.
- The removed explanatory lines about Regular/Ad-Hoc cadence, WRH warnings, and near-miss reporter masking must not be printed.
- PDF includes attendance + WRH snapshot, circular/near-miss/PSC/SOI discussion, Office Comment, and plain Master/Chief Officer signature lines.

---

## 6. Decisions Log

> Pre-DNV decisions (Sessions 1–3, Rounds 1–12) are captured in the interrogation file `VIMS-SAFETY-REQUIREMENTS-INTERROGATION.md`. Below: DNV-driven decisions adopted 2026-04-16.

| # | Decision | Date | Rationale |
|---|----------|------|-----------|
| D-DNV-01 | Adopt full M-SCAT taxonomy (24+24 immediate codes, 17 basic-cause cats with ~170 sub-codes, 3-area Lack-of-Control) as canonical cause picker | 2026-04-16 | Provides codified taxonomy for trend analytics, replaces opaque "M-SCAT" label; sourced from DNV course pack |
| D-DNV-02 | Risk-tiered investigation deadlines: GREEN 30d/Master · YELLOW 14d→30–45d/DPA · RED 7d→per-case/MD+external | 2026-04-16 | Aligns investigation depth to risk; replaces single 45-day cap |
| D-DNV-03 | Adopt DNV's 7 Type-of-Loss categories verbatim (People/Asset/Environmental/Financial/Non-Conformity/Reputation/Process) | 2026-04-16 | Standard DNV nomenclature; legacy 7-column matrix migration-mapped |
| D-DNV-04 | Adopt IMO 11 reportable types as Incident Type picklist | 2026-04-16 | Regulatory alignment with MSC.255(84) and MSC-MEPC.3/Circ.4 |
| D-DNV-05 | DNV 8-phase investigation workflow with explicit Phase-5 → Phase-3 loop-back gate (no data loss) | 2026-04-16 | DNV "need more info?" decision gate; replaces linear Draft → Closed flow |
| D-DNV-06 | 3-tier recommendation format mandatory at closure: Lessons Learned + ≥1 Immediate Action + ≥1 System Action (themed) | 2026-04-16 | DNV course rubric; Lessons Learned auto-feeds Fleet Circular |
| D-DNV-07 | 5-source Evidence Workspace: Position/People/Parts/Paper/Electronic tabs + Evidence Matrix (Pro/Con) | 2026-04-16 | DNV evidence framework; perishable-evidence prompt at 24h for YELLOW/RED |
| D-DNV-08 | Structured 4-phase Interview module with question-type guidance + leading/biased keyword warning | 2026-04-16 | DNV interview protocol (Ac_05); replaces free-text notes |
| D-DNV-09 | SHELL tags + IMO A.884(21) 7-domain human-factors checklist on incidents (SHELL only on near miss) | 2026-04-16 | DNV human-factors model + IMO regulatory floor |
| D-DNV-10 | Multi-tool Analysis Workspace: STEP / Fact Tree / ECF / Barrier / Change. Min 2 tools required, all 5 for RED-band | 2026-04-16 | DNV bias-mitigation through cross-method triangulation |
| D-DNV-11 | 5 named bias guards as form validations: Recency · Assumption · Hindsight · Confirmation · Blame fixation (hard block) | 2026-04-16 | DNV ICC §16 principles; blame-fixation guard requires Lack-of-Control entry to close |
| D-DNV-12 | MSC-MEPC.3/Circ.4 PDF auto-export — App.2 from vessel particulars, App.4 from Daily Report position-time match (~40% auto-fill) | 2026-04-16 | Uses existing same-DB integrations specified in Reporting/Vessel modules |
| D-DNV-13 | Heinrich Ratio panel on Safety Intelligence Dashboard with under-reporting "Reporting Culture Gap" warning | 2026-04-16 | Heinrich/Bird ratio is the diagnostic for under-reporting; more actionable than headline counts |
| D-DNV-14 | Seed Case Study Library with Navigator (grounding) + Sinkfast (explosion) DNV worked solutions | 2026-04-16 | First-time investigator tutorial; both shown in cause-picker Help drawer |
| D-RBAC-01 | Closure authority: PIC→GREEN, DPA→YELLOW, FM→RED | 2026-04-16 | Q47.1 — matches investigator seniority |
| D-RBAC-02 | YELLOW-band uses joint Master+PIC investigation (not DPA-led) | 2026-04-16 | Q47.1 — ship+office collaboration preserves operational context |
| D-RBAC-03 | SSQE = DPA team label, no separate RBAC entry | 2026-04-16 | Q47.2 Option A — simplifies matrix |
| D-RBAC-04 | Fleet Manager baseline = read+flag+comment outside formal record | 2026-04-16 | Q47.3 Option C — keeps ISM audit trail pure |
| D-RBAC-05 | FM sole authority for RED closure + RED blame-fixation override | 2026-04-16 | Q47.1 + Q47.5 — highest-band elevation |
| D-RBAC-06 | CO and Master can host either Regular or Ad-Hoc SCM; user selects `meeting_type` at creation; submitting moves the meeting to Office; Office Comment closes it | 2026-04-16; revised 2026-06-09 | Operational update: both senior shipboard roles may host either SCM type; active closure is by authorized office comment |
| D-RBAC-07 | Blame-fixation override: DPA for GREEN/YELLOW, FM for RED | 2026-04-16 | Q47.5 Option B — band-tiered |
| D-RBAC-08 | PIC read-only non-managed + can borrow lessons into own circulars | 2026-04-16 | Q47.6.1 Option C — supports cross-fleet learning |
| D-RBAC-09 | Master read-only on closed incidents fleet-wide | 2026-04-16 | Q47.6.2 Option B — supports in-crew learning culture |
| D-RBAC-10 | Vetting access: Master-driven on-screen + PDF export for auditor (updates D-PRIOR-Q46) | 2026-04-16 | Q47.6.3 A+C — Q46 previously excluded PDF; now includes |
| D-RBAC-11 | Any rank can create near misses (not top-4 limited) | 2026-04-16 | Q48.4 Option A — matches legacy + Heinrich reporting-culture principle |
| D-CFG-01 | M-SCAT cause taxonomy maintenance: DPA only | 2026-04-16 | Q48.1 — prevents taxonomy churn (trend-analytics stability) |
| D-CFG-02 | Guidance Library: DPA + PIC maintain · Case Study Library: DPA only | 2026-04-16 | Q48.2 Option D — split based on document formality |
| D-CFG-03 | Recommendation Themes: DPA only | 2026-04-16 | Q48.3 Option A — aligned with taxonomy policy |
| D-CFG-04 | Fleet Circular reuses existing VIMS Circular module `/api/circular/` approval chain | 2026-04-16 | Q48.5 — no Safety-specific circular workflow |
| D-EDGE-01 | Multi-vessel incidents = 2 linked records (each vessel owns its investigation; cross-linked) | 2026-04-16 | Q49.1 — independent flag-state reporting per vessel |
| D-EDGE-02 | Injury capture supports `Crew` and `Non-crew`. Non-crew keeps the External Party picklist and free-text name/company; crew adds rank, age, Type of Activity dropdown, vessel/location details, investigation narrative, and OCIMF flags. Estimated costs are optional and only shown when the user chooses to add them. | 2026-04-16; expanded 2026-06-23; refined 2026-06-30 | Q49.2 plus CR-002 and CR-025 - covers legacy pilot/shipyard/stevedore injuries, crew injury details, and optional estimated cost entry |
| D-EDGE-03 | Re-open authority follows closure authority by band: DPA for GREEN/YELLOW, FM for RED. Returns to Phase 5 with audit-log reason | 2026-04-16 | Q49.3 — consistent with closure RBAC |
| D-EDGE-04 | Medical / D&A / fitness-for-duty data uses standard incident permissions (no field-level restriction) | 2026-04-16 | Q49.4 — V1 simplification; **flagged as GDPR risk for non-EU/UK/SG operating context** |
| D-EDGE-05 | GDPR-style deletion requests denied; ISM regulatory obligation prevails. Crew informed at hiring | 2026-04-16 | Q49.5 — legitimate-interest legal basis |
| D-EDGE-06 | Phase 8 effectiveness verification = reuse `psc_physical_verification` pattern. No separate 90/180/365-day re-review | 2026-04-16 | Q49.6 — collapses Phase 7+8, consistent with Q45 CA verification |
| D-EDGE-07 | Near-miss ↔ Incident reclassification = supersede-and-create-new (Option C). Original closes as "Superseded" with link | 2026-04-16 | Q49.7 — preserves record-type purity for analytics |
| D-EDGE-08 | Draft mode at any phase with partial data; per-phase Submit enforces full validation for that phase's required fields | 2026-04-16 | Q49.8 — A+D hybrid. No partial phase advance |
| D-EDGE-09 | Notifications = Creation + Overdue at 80% of risk-band deadline + Rework requested. No per-phase-transition notifications | 2026-04-16 | Q49.9 — pragmatic noise floor |
| D-EDGE-10 | Edits allowed at all times with full field-level history (`safety_field_history`); diff view on incident detail screen | 2026-04-16 | Q49.10 — Option B; ISM tamper-evidence + legal-discovery friendly |
| D-EDGE-11 | Form schema versioning grandfathered per `safety_incident.schema_version` — old incidents keep their schema until closed | 2026-04-16 | Q49.11 — Option A; engineering-safe default |
| D-EDGE-12 | P&I / insurance claim data NOT modelled in Safety module — commercial/finance system owns it | 2026-04-16 | Q49.12 — keeps Safety module operational |
| D-PDF-01 | Internal incident PDF = formal company report template (cover + executive summary auto-from Lessons Learned + full sections + signature block Master/DPA/[FM for RED] + page numbering + confidentiality header/footer). Title prints as `Injury Report` when a Phase 1 injury record exists, otherwise `Incident Report`. | 2026-04-16; title clarified 2026-06-23 | Q50.1 Option B — DPA filing / management review / flag-state hand-off |
| D-PDF-02 | Auditor leave-behind PDF package = configurable scope at export. Master selects record types (Incidents / Near Misses / Safety Meetings) + date range. **Attachments delivered as separate folder inside the ZIP** (PDF references file names; attachments live in `attachments/` subfolder) | 2026-04-16 | Q50.2 Option D + (iii) — flexibility + portability |
| D-PDF-03a | Near miss PDF = distinct lighter template (1–2 page: what-happened + suggestion + immediate action). No investigation/cause-tree details | 2026-04-16 | Q50.3 Near Miss = Option B — matches near-miss data simplicity |
| D-PDF-03b | Safety Meeting PDF = legacy `vw_GetSCM_Master` 10-section structure preserved verbatim | 2026-04-16 | Q50.3 Safety Meeting = Option D — historical-new consistency |
| D-SOI-01 | Safety Officer Inspection added as 4th V1 sub-feature (own module, own PDF, own RBAC; tightly coupled to SCM via auto-feed) | 2026-04-16 | Q-SOI-1 Option A — matches SSQE §4.5 separation and COSWP Ch 13 governance |
| D-SOI-02 | Chief Officer is the designated Safety Officer; 2/E is alternate (Master toggle per vessel) | 2026-04-16 | Q-SOI-2 Option A — locked per SSQE §4.5.1 verbatim |
| D-SOI-03 | Stop-work authority (COSWP 13.4.6 / SSQE §4.5.1) is **out of V1 scope**. Verbal informal escalation to Master retained; revisit as V2 feature | 2026-04-16 | Q-SOI-3 Option C — prioritise core workflow in V1 |
| D-SOI-04 | Cadence = 90-day hard ceiling per applicable inspection area (SCM hard-block on any overdue area). 80-day amber warning to CO + Master. Target 1/3 per month per SSQE §4.5.2, but Safety Officer chooses which specific areas each cycle | 2026-04-16 | Q-SOI-4 Option B + D-38 zone-tracked model — enforces the regulatory ceiling while respecting operational reality |
| D-SOI-05 | DPA maintains **versioned checklist templates**. Each vessel assigned an applicable version at onboarding; reassignable with DPA approval. Historical inspections grandfathered on their schema version | 2026-04-16 | Q-SOI-5 — versions with per-vessel assignment; aligns with D-EDGE-11 |
| D-SOI-06 | **No auto-escalation** from SOI findings to Near Miss / Incident / PMS Defect. All findings stay in SOI and are followed up via the SCM. Manual separate-record filing if escalation needed | 2026-04-16 | Q-SOI-6 Option D — keeps the audit chain pure, SCM is the single meeting venue |
| D-SOI-07 | Safety Officer marks finding `pending_closure` inside the inspection record; **Master review + approval required** before it moves to `closed`. Auto-reflected into next SCM under new Closed Items block | 2026-04-16 | Q-SOI-7 — hybrid closure: Master is the approver, SCM is the audit venue |
| D-SOI-08 | Cross-functional assistant **hard-enforced**: Name + Department pulled from CMS (not free text). Assistant's department must differ from Safety Officer's. No submit without valid cross-functional pairing | 2026-04-16 | Q-SOI-8 Option A + CMS integration — supports SSQE §4.5.2 bias-reduction intent automatically |
| D-SOI-09 | Up to 3 crew trainees per inspection tracked by CrewId. System computes per-crew "inspections accompanied" counter + per-vessel "crew rotation coverage %" over rolling 12 months. Surfaced on Crew dashboard and SCM analytics | 2026-04-16 | Q-SOI-9 Option A — formal tracking to evidence training-through-participation at flag-state audits |
| D-SOI-10 | **Paper-first workflow with system-generated checklist** (revised 2026-04-17 via D-GAP-E4 — no scan upload): (1) Safety Officer selects areas → (2) system generates dynamic checklist PDF **or Excel** (SO choice) with a **unique checklist ID** printed on it → download flips state to "In Progress" → (3) fieldwork on paper → (4) **physical document filed in ship's onboard SMS filing system permanently** (unique ID = the cross-reference key) → (5) Safety Officer returns to VIMS, registers ONLY findings digitally and enters the unique checklist ID to link → (6) submission stamps all selected areas as inspected (90-day counter reset). Per-item Yes/No responses live **only** on the paper in ship filing, never in DB or as scan upload. Findings feed SCM. Auto-generated summary PDF of findings available post-submission | 2026-04-17 | Q-SOI-10 re-revised — user: "no need to scan and upload, physical document is maintained onboard filing system; tracked via unique ID on checklist which links it" |
| D-SOI-11 | SOI retention aligns with the rest of the Safety module — 3-year soft archive; hard-delete attachments at 3 years | 2026-04-16 | Q-SOI-11 Option A — single retention policy module-wide |
| D-SOI-12 | Fleet-wide standard zone/area template — same 11-area coding on every vessel. Non-applicable areas flagged `applicable=false` at onboarding (don't enter compliance counter) | 2026-04-16 | Q-SOI-12 Option C — simpler analytics, per-vessel applicability toggle |
| D-SOI-13 | 11 inspection areas per SQE S 608 baseline, seeded at install | 2026-04-16 | Q-SOI-13 Option C — matches KSM's present form; ~280 items total |
| D-SOI-14 | **SCM auto-feed split**: Open findings populate Safety Observations for the Month table (for discussion); Closed-Since-Last-SCM findings appear in a new "Closed Items" summary block at the top of the SCM (for record) | 2026-04-16 | Q-SOI-14 Option C — preserves closure visibility without cluttering main discussion |
| D-SOI-15 | SOI RBAC **inherits standard Safety module pattern** — no new permission patterns. CO/2/E create & edit; Master approves closure; DPA maintains reference data; PIC read-only assigned vessels + flag; DPA read-all; FM read-only fleet baseline | 2026-04-16 | Q-SOI-15 Option A — simplifies the locked Q47 matrix extension |
| D-SOI-16 | Add 12th inspection area **"Cross-cutting Safety & Culture"** to SQE S 608 baseline — 12 items covering PPE matrix, LOTO, IMO signs, PTW, enclosed-space entry, hot-work, work-at-height, heat-stress, supervision adequacy, open improvement prompts, crew suggestions, previous-findings rectification. Applied once per inspection regardless of physical areas covered | 2026-04-16 | User chose Option B — plugs vetting-gap items without disrupting familiarity with the existing 11 sections. Sourced from COSWP Ch 13 + D-38 + QEOHS-VSL-HSSE-10 |
| D-GAP-A1 | YELLOW-band closure deadline **auto-pauses** while DPA is on approved leave and resumes on return. No Acting-DPA concept | 2026-04-17 | Session 5 Round 17 — keeps deadline clock integrity tied to sole closer authority |
| D-GAP-A2 | Original PIC retains YELLOW ownership **remotely until closure** even if they transfer vessels mid-investigation | 2026-04-17 | Session 5 Round 17 — continuity of investigator prevents handover gaps |
| D-GAP-A3 | **VIMS-wide invariant: rank persists, person may change.** For Safety, new Master on rotation inherits all pending Master duties (SCM chair, GREEN closure, SOI approval). No handover-to-CO or deputy fallback | 2026-04-17 | Session 5 Round 17 — mirrors established VIMS pattern across modules |
| D-GAP-A4 | Same rank-persistence rule applied to Chief Officer / Safety Officer. New CO on rotation inherits any open SOI findings / in-flight inspection. No 2/E alternate succession except by Master toggle per D-SOI-02 | 2026-04-17 | Session 5 Round 17 — consistent with D-GAP-A3 |
| D-GAP-A5 | Self-report conflict guard: when reporter = injured / PIC / person-in-charge, system flags conflict and mandates a **different approver — Master for vessel-side submissions, DPA for office-side** | 2026-04-17 | Session 5 Round 17 — separation-of-duties guard without blocking submission |
| D-GAP-A6 | **Role stays as-is even when incumbent is subject of incident** (Master still chairs SCM, CO still approves SOI, PIC still closes GREEN). No automatic stand-in. Integrity relies on DPA oversight + full audit trail per D-EDGE-10 | 2026-04-17 | Session 5 Round 17 — role-based accountability model; consistent with D-GAP-A3 |
| D-GAP-B1 | If DPA and FM both refuse blame-fixation override on RED, investigation is **sent back to Phase 3 (rework)** — no MD escalation. Loop continues until override granted or investigation reframes | 2026-04-17 | Session 5 Round 17 — self-correcting mechanism; prevents blame-based closure |
| D-GAP-B2 | No Deputy-FM concept. RED closure runs within designed timeline; **existing VIMS timeline-extension procedure is the only extension path** when FM unavailable | 2026-04-17 | Session 5 Round 17 — reuses cross-module extension workflow |
| D-GAP-B3 | **No cap on Phase 5 → Phase 3 loop-backs.** Every loop-back logged in `safety_incident_phase_log` with reason; DPA judgement governs. Excessive looping surfaces via dashboard metric (no hard block) | 2026-04-17 | Session 5 Round 17 — DPA authority + audit visibility, no rigid iteration limit |
| D-GAP-C1 | Incident number format = `{VslCode}/{YYYY}/{NNN}` per-vessel-per-year. **Temp reference series during draft** (e.g. `DRAFT-EBK/2026/T042`); **final number assigned at submit-to-office** (first formal phase gate). Gap-free sequence guaranteed | 2026-04-17 | Session 5 Round 17 — preserves draft editability while keeping sequence pure |
| D-GAP-C2 | **M-SCAT taxonomy CSV extracted now from DNV MSCAT 8.2 PDF** and committed to repo at `safety-reference-data/mscat_taxonomy.csv`. Seeded at install. DPA-editable post-deploy per D-CFG-01 | 2026-04-17 | Session 5 Round 17 — removes build-time OCR risk; canonical source locked |
| D-GAP-C3 | **SOI 292-item checklist extracted now from SQE S 608 Excel** and committed to repo at `safety-reference-data/soi_checklist_v1.csv`. Structured columns: area_id, area_name, item_number, description, tier. Seeded at install per D-SOI-13 + D-SOI-16 | 2026-04-17 | Session 5 Round 17 — removes column-discovery risk at build time |
| D-GAP-C4 | Schema / taxonomy drift within VIMS: **old incidents locked on their original taxonomy version (true grandfather).** When DPA adds new M-SCAT codes in Year 2, only records created post-change can use them. No retroactive remapping. Legacy eMarineSoft data stays separate read-only system (D-EDGE-05 already notes migration out of scope) | 2026-04-17 | Session 5 Round 17 — trend-analytics purity, matches D-EDGE-11 engineering-safe default |
| D-GAP-C5 | **No column-level encryption or separate-table isolation for PII / medical / D&A data.** Standard role permissions per D-EDGE-04 are sufficient. GDPR risk remains flagged for non-EU/UK/SG operating context | 2026-04-17 | Session 5 Round 17 — user override of earlier PII-protection suggestion; deliberate simplification |
| D-GAP-D1 | **Hybrid digital signature model:** Master / DPA / FM / SO sign via typed name + timestamp + device fingerprint in the VIMS UI (digital). For formal PDFs intended for flag-state / auditor hand-off, a wet-signed scan of the PDF is also accepted as attachment. No PKI / UETA compliance required in V1 | 2026-04-17 | Session 5 Round 18 Cluster D — user chose D; balances usability with audit defensibility |
| D-GAP-D2 | **No cryptographic tamper-evidence in V1.** Audit integrity relies on: standard DB/table access control · `safety_field_history` append-only audit · platform backups · access log on audit table itself. ISM non-repudiation satisfied via audit trail + backups. Hash chains / digital PKI signatures revisitable in V2 if insurance / legal forces the issue | 2026-04-17 | Session 5 Round 18 Cluster D — consistent with D-GAP-C5; proportionate for V1 |
| D-GAP-E1 | **Checklist download is idempotent** — second download is a no-op (state flipped once). SO may reprint freely. Each download re-issues same PDF/Excel with same unique checklist ID; state stays "In Progress" | 2026-04-17 | Session 5 Round 18 Cluster E — paper is source of truth; digital state flips once |
| D-GAP-E2 | **Partial submission allowed.** SO downloaded 5 areas, can submit findings for only 3 — those 3 stamp as inspected (90-day counter reset per-area); remaining 2 stay in "Downloaded" state for later completion under same unique checklist ID | 2026-04-17 | Session 5 Round 18 Cluster E — real-world ops continuity; per-area counter already in D-SOI-04 |
| D-GAP-E3 | **Lost / damaged paper recovery:** SO may re-download same area selection (reuses existing unique checklist ID or issues a new one — to be specified at build) and re-conduct fieldwork on fresh paper. Loss event logged in inspection notes | 2026-04-17 | Session 5 Round 18 Cluster E — pragmatic; not punitive |
| D-GAP-E4 | **No scan upload required.** Paper checklist permanently filed in ship's onboard SMS filing system. Digital record linked to paper via unique checklist ID. This revises D-SOI-10 (scan upload requirement removed). PSC/auditor on-demand review of the physical paper | 2026-04-17 | Session 5 Round 18 Cluster E — user clarification; simplifies data model and reduces storage |
| D-GAP-E5 | **No paper-vs-digital count reconciliation mechanism.** SO's digital findings reflect professional judgment on what's worth formal filing. Paper in ship SMS filing is always available for PSC/auditor review on demand | 2026-04-17 | Session 5 Round 18 Cluster E — follows from D-GAP-E4; trust-based + audit-available |
| D-GAP-E6 | **Life-threat escalation during V1 inspection:** SO creates a parallel Incident or Near Miss via the existing incident flow (which triggers Slack to DPA/FM). SOI continues once hazard is controlled. No new "Urgent SOI" schema. Stop-work authority remains deferred to V2 per D-SOI-03 | 2026-04-17 | Session 5 Round 18 Cluster E — reuses existing escalation; clean schema |
| D-GAP-E7 | **Default finding assignee = Safety Officer themselves** when SO leaves assignee blank. Master can re-assign at approval time | 2026-04-17 | Session 5 Round 18 Cluster E — clear ownership by default |
| D-GAP-F1 | **Form auto-save every 30 seconds** to browser local storage (IndexedDB). On reconnect or page reload, form resumes from last saved state. Applies to all Safety module forms (Incident, Near Miss, SCM, SOI finding registration) | 2026-04-17 | Session 5 Round 18 Cluster F — preserves work across satcomm drops |
| D-GAP-F2 | **Slack is best-effort.** In-app notification is the authoritative channel. No auto-fallback to email on Slack failure. Users see overdue flags on dashboard regardless | 2026-04-17 | Session 5 Round 18 Cluster F — simplifies notification reliability surface |
| D-GAP-F3 | **Dashboard flag only on 80% overdue — no auto-escalation to FM/MD.** Existing VIMS timeline-extension procedure (referenced in D-GAP-B2) handles approved overruns. Breaches surface as dashboard metric; DPA judgement governs | 2026-04-17 | Session 5 Round 18 Cluster F — consistent with D-GAP-B2/B3 |
| D-GAP-F4 | **Monitoring inherited from VIMS platform.** Safety module does not build its own observability stack. Module-specific supplements if platform lacks them: (a) alert on Slack webhook failure for RED-band notifications, (b) alert on CMS/PMS integration failure blocking submit, (c) access log on `safety_field_history` for tamper visibility | 2026-04-17 | Session 5 Round 18 Cluster F — platform-first; minimum viable module supplements |
| D-GAP-G1 | **No in-module tracking of IMO flag-state notification deadlines.** DPA handles manually out-of-band. System supports DPA via MSC-MEPC.3 PDF auto-export per D-DNV-12 (pre-filled fields); no deadline countdown or overdue alert in V1 | 2026-04-17 | Session 5 Round 19 Cluster G — keeps V1 scope focused; DPA regulatory duty remains human-owned |
| D-GAP-G2 | **No legal-hold feature in V1.** 3-year hard-delete runs on schedule regardless. When a case (P&I claim, flag-state investigation, litigation) is open at the 3-year mark, DPA is responsible for exporting the incident record + attachments externally before the cutoff date. Retention extension revisitable in V2 | 2026-04-17 | Session 5 Round 19 Cluster G — simplifies V1 retention model |
| D-GAP-G3 | **Backup / DR strategy inherited from VIMS platform.** Safety module stores no separate backup. Module assumes platform-level RPO/RTO covers safety data at the same cadence as `ksm_cms_live`. Verification: confirm platform backup policy covers all Safety tables at deploy time | 2026-04-17 | Session 5 Round 19 Cluster G — consistent with D-GAP-F4 platform-first principle |
| D-GAP-H1 | **No formal concurrent-user load target at module level.** Inherit VIMS platform baseline. No single-editor lock vs optimistic-locking decision taken at module level; follows whatever the platform provides | 2026-04-17 | Session 5 Round 19 Cluster H — platform-inherited performance posture |
| D-GAP-H2 | **Two repeat-root-cause radars on Safety Intelligence Dashboard:** (a) fleet-level — same M-SCAT leaf code appearing 3+ times across the fleet in rolling 6 months; (b) vessel-level — same leaf 3+ times on same vessel in rolling 6 months. Both flagged independently. **Superseded / reclassified incidents do NOT count** toward the total (no inflation) | 2026-04-17 | Session 5 Round 19 Cluster H — dual-axis radar preserves both fleet and vessel insight |
| D-GAP-I1 | **PMS is an independent system accessed by separate login.** M-SCAT cause 12 "Inadequate Maintenance" does NOT trigger any in-VIMS PMS work-order lookup. Investigator cross-references PMS manually. **Removes the Safety↔PMS cross-module dependency previously noted in §2 for M-SCAT cause 12.** Equipment defect linkage from SOI findings to PMS also remains manual (no FK) | 2026-04-17 | Session 5 Round 19 Cluster I — user clarification: PMS is standalone; simplifies integration surface |
| D-GAP-I2 | **No CMS staleness concern.** Crew Management System and Safety module share the same database (`ksm_cms_live`); cross-functional assistant lookup for SOI is a live table join with no sync lag. Residual operational case (new joiner physically onboard but not yet entered in CMS roster by HR) is an HR process issue; V1 handles via D-SOI-08's hard-enforcement — Master may defer inspection or select a different assistant. No manual override added | 2026-04-17 | Session 5 Round 19 Cluster I — user clarification: same-DB = no staleness |
| D-GAP-J1 | **Near-miss reporter identity is visible to authorized users.** Anonymous reporting and reporter masking are removed from V1. Reporter name/rank/user reference are stored and shown according to vessel scope and safety permissions | 2026-04-17; revised 2026-06-09 | User priority: Master and authorized users must see reporter details; no anonymous concept |
| D-GAP-M01 | **Orphaned attachment cleanup:** hard-delete immediately from cloud storage when its parent draft/record is deleted. No grace period. `safety_field_history` logs the delink | 2026-04-17 | Session 5 Round 20 — simplicity; no cloud-bloat |
| D-GAP-M02 | **Re-upload with same filename = replace in place.** `safety_field_history` captures old→new filename, uploader, timestamp. No auto-versioned copies | 2026-04-17 | Session 5 Round 20 — single source of truth per file |
| D-GAP-M03 | **CA may close with its Physical Verification still Open.** PV runs on its own track; incident closure also allowed. Matches PSC CAR pattern already in use | 2026-04-17 | Session 5 Round 20 — operational reality (drydock slots); consistent with cross-module precedent |
| D-GAP-M04 | **No dedicated point-in-time snapshot/revert UI in V1.** Field-level diff per D-EDGE-10 is sufficient for ISM discovery and dispute resolution | 2026-04-17 | Session 5 Round 20 — V1 simplification |
| D-GAP-M05 | **Checklist template reassign mid-inspection: freeze in-flight on old version.** New version applies only to the next cycle. Consistent with D-SOI-05 versioning and D-GAP-C4 grandfather principle | 2026-04-17 | Session 5 Round 20 — preserves in-flight validity |
| D-GAP-M06 | **FM has full edit authority during RED closure** — can rewrite any investigation content, not just approve/reject. Effectively co-investigator for RED band. Supersedes my recommendation; user override | 2026-04-17 | Session 5 Round 20 — strong FM authority on highest-risk band |
| D-GAP-M07 | **Multi-vessel linked incidents close independently.** Each vessel's PIC/DPA closes their own half; cross-link (D-EDGE-01) remains intact for analytics | 2026-04-17 | Session 5 Round 20 — preserves per-vessel flag-state reporting |
| D-GAP-M08 | **PIC borrow-lessons: anonymize vessel + crew names before pasting into own circular.** Cause analysis and lesson text preserved verbatim | 2026-04-17 | Session 5 Round 20 — protects privacy; preserves learning value |
| D-GAP-M09 | **MSC-MEPC.3 position auto-fill tolerance: ±12 hours from incident timestamp.** Outside window → manual entry. **User may also edit the auto-fill and enter a more recent position if available** | 2026-04-17 | Session 5 Round 20 — matches Daily Report cadence; always editable |
| D-GAP-M10 | **Daily Report missing for incident date:** accept manual lat/long + time entry; flag record `awaiting_daily_report_match` for DPA review; do NOT block submission | 2026-04-17 | Session 5 Round 20 — submission never blocked on Reporting-module gap |
| D-GAP-M11 | **WRH data missing for SCM attendee:** warn Master on submit; row flagged "WRH data unavailable"; do NOT block | 2026-04-17 | Session 5 Round 20 — pragmatic handling of roster sync timing |
| D-GAP-M12 | **CA ↔ Purchase Requisition link uses hard FK** (referential integrity). Requisition cannot be archived/deleted while linked to an open CA. Live status syncs | 2026-04-17 | Session 5 Round 20 — same-DB makes FK cheap; strict traceability |
| D-GAP-M13 | **Class society notification: no in-module toggle.** DPA handles out-of-band (same pattern as G1 flag-state) | 2026-04-17 | Session 5 Round 20 — consistent external-regulatory handling |
| D-GAP-M14 | **MLC injury flag = "MLC-reportable = Yes" on incident**, visible to DPA. No cross-module notification to HR. External follow-up by DPA | 2026-04-17 | Session 5 Round 20 — simplified V1 handling |
| D-GAP-M15 | **Paper SOI checklist signatures:** Safety Officer + Assistant mandatory on paper. Master counter-signs digitally at approval stage (not on paper). Trainees do not sign | 2026-04-17 | Session 5 Round 20 — COSWP custody-of-findings + digital accountability |
| D-GAP-M16 | **HIGH severity SOI finding triggers a system prompt** to SO: "This looks incident-worthy. Create one now? [Yes / No + reason]". Nudge-only; does NOT auto-create. SO judgement retained per D-SOI-06 | 2026-04-17 | Session 5 Round 20 — catches buried HIGH findings without violating no-auto-escalation |
| D-GAP-M17 | **Repeat findings: both visual badge + dashboard metric.** Badge on record ("Repeat — Nth occurrence") + dashboard tile ("Top 5 repeat findings per vessel") | 2026-04-17 | Session 5 Round 20 — dual visibility at discovery + review layers |
| D-GAP-M18 | **No single-department exception required.** Vessels always have Deck and Engine departments — D-SOI-08 cross-functional rule is always satisfiable. No override mechanism added | 2026-04-17 | Session 5 Round 20 — user clarified operational assumption |
| D-GAP-M19 | **`applicable=false` workflow for an SOI area:** Master requests, DPA approves; both signatures + reason captured in dedicated `safety_soi_applicability_log` | 2026-04-17 | Session 5 Round 20 — strong audit defence for vetting / class queries |
| D-GAP-M20 | **SCM overdue SOI handling** = warning only during SCM creation, edit, PDF export, and Office Comment closure. Meeting and closure may continue while the warning remains visible | 2026-04-17; revised 2026-06-09 | Operational update: SCM must not become slow or blocked by SOI checks; overdue items remain visible for office/vessel action |
| D-GAP-M21 | **Master rejection of SO's `pending_closure`:** mandatory written reason; finding returns to "Open" state; reason appended to finding notes | 2026-04-17 | Session 5 Round 20 — audit trail for ISM/class |
| D-GAP-M22 | **Closed-Since-Last-SCM snapshot cutoff = prior SCM closure timestamp.** New SCM records close when Office Comment is saved; legacy records may use Master sign-off timestamp | 2026-04-17; revised 2026-06-09 | Aligns with active Draft to Submitted to Office to Closed workflow |
| D-GAP-M23 | **Section 12 "Cross-cutting Safety & Culture" evaluated once per 3-month cycle** (not every individual SOI event). Safety Officer decides which SOI event in the cycle carries Section 12 | 2026-04-17 | Session 5 Round 20 — avoids duplicate cross-cutting responses |
| D-GAP-M-ADHOC | **SCM supports Ad-Hoc / Additional meetings** (beyond monthly cadence) called by Master or CO for major incidents or important information. Same form, PDF, and shared SCM host RBAC; tagged `meeting_type = 'AD_HOC'`. Does NOT replace the monthly Regular meeting. Cadence counter + Closed-Since-Last snapshot anchor on last SCM closure timestamp regardless of type. Aligns with SSQE Manual §9 provisions | 2026-04-17; revised 2026-05-18 | Session 5 Round 20 plus operational update: Master and CO both have SCM host authority |
| D-GAP-M24 | **Photo evidence on SOI findings: HIGH severity requires ≥1 photo** (mandatory). MED / LOW = optional. Enforced at finding-save | 2026-04-17 | Session 5 Round 20 — evidence-chain defensible at audit |
| D-GAP-M25 | **Multi-vessel incident duplicate detection:** system auto-detects potential duplicates within 24h (same incident type + position within 10 nm + overlapping time window) and prompts creator: "Link to existing incident? [Yes / No — separate events]". Creator decides | 2026-04-17 | Session 5 Round 20 — cheap detection; human in the loop |
| D-GAP-M26 | **Timezone model reuses WRH module:** timestamps stored UTC in DB; vessel local time resolved via `dbo.wrh_ship_time_config` (Master-set, supports dateline events). Same pattern as Reporting module — consistency across VIMS | 2026-04-17 | Session 5 Round 20 — cross-module reuse; no parallel infrastructure |
| D-GAP-M27 | **Heinrich Ratio display: always shown with confidence indicator** (green/amber/red) based on rolling sample size (e.g. ≥5 incidents + ≥20 near-misses in 12-month = green; below = amber; zero = red with "Insufficient data" tooltip). No hiding | 2026-04-17 | Session 5 Round 20 — matches DNV teaching that pyramid is indicative |
| D-GAP-M28 | **No notification digest; every safety event is an independent notification.** RED + Overdue + Rework all fire immediately. User preferences to tune cadence are V2 | 2026-04-17 | Session 5 Round 20 — safety signals not bucketed |
| D-GAP-M29 | **CA Aging Pipeline buckets (0-15 / 15-30 / 30-45 / 45+) calculated from CA CREATION date.** Reopen does NOT reset the clock — aging reflects total time the problem has been in the system | 2026-04-17 | Session 5 Round 20 — reflects true organizational response time |
| D-GAP-M30 | **Inspection Compliance % edge cases:** new vessel (zero cycles completed) displays "N/A — awaiting first cycle" (not 0% red). `pending_closure` findings' areas COUNT as inspected (fieldwork is done) | 2026-04-17 | Session 5 Round 20 — avoids punishing new vessels and closure queue |
| D-GAP-M31 | **Safety Intelligence Dashboard export: PDF + Excel formats.** Both include timestamp + period + exporter name. **DPA owns export access** (domain owner); FM has read-only dashboard access but NOT export rights in V1 | 2026-04-17 | Session 5 Round 20 — user explicit: DPA is dashboard domain owner |
| D-GAP-M32 | **Archive search surfacing:** default search excludes archived records; user ticks "Include archived records" checkbox on search bar to include them | 2026-04-17 | Session 5 Round 20 — keeps default UI clean; opt-in when needed |
| D-GAP-M33 | **`safety_field_history` retention tied to parent:** audit log rows are deleted when their parent incident / near-miss / SCM / SOI is hard-deleted. No orphan retention | 2026-04-17 | Session 5 Round 20 — storage-efficient; audit log is context-only |
| D-GAP-M34 | **Mobile responsiveness target:** tablet (768px+) fully supported with all CRUD features; phone (≤480px) read-only dashboards only. Desktop (1280px+) is primary target | 2026-04-17 | Session 5 Round 20 — realistic V1; bridge-iPad scenario covered |
| D-GAP-M35 | **Accessibility target: WCAG 2.1 Level AA.** All color-coded indicators include text labels; forms have ARIA labels; full keyboard navigation parity; screen-reader support on dashboard + forms | 2026-04-17 | Session 5 Round 20 — maritime SaaS baseline; protects against vetting failures |
| D-GAP-M36 | **Localization V1: English-only UI.** Date rendering = DD-MMM-YYYY (e.g. 17-Apr-2026) to avoid US/EU ambiguity. Units = metric always. Timestamps per D-GAP-M26. Multilingual and translated M-SCAT codes are V2 | 2026-04-17 | Session 5 Round 20 — ambiguity-free dates; V2 scope for translation |
| D-GAP-M37 | **No crew-name redaction in auditor export bundle** (D-PDF-02). Full context preserved; auditor sees names as recorded | 2026-04-17 | Session 5 Round 20 — full context serves auditor better than partial privacy |
| D-GAP-M38 | **Near-miss submission controls:** no daily submission cap; each submission requires description >= 100 characters and severity selected | 2026-04-17; revised 2026-06-09 | User priority: crew must be able to report as many near misses as needed in a day |
| D-GAP-DESIGN-01 | **Dashboard metric rename: "Inspection Compliance %" (on Safety dashboard) is renamed to "SOI Compliance %"** to avoid clash with the existing PSC Inspection-module metric of the same name. Applies to all UI labels and exports | 2026-04-17 | Session 5 Round 20 — DESIGN clarity; no name collision across modules |
| D-GAP-R01 | **Causal-layer tagging on top of M-SCAT (ABS scaffolding).** Every cause entered on an incident must also be tagged as Immediate / Intermediate / Root. Investigator cannot close Phase 5 with Immediate-only codes — at least one Root-level cause required. Extends D-DNV-01 | 2026-04-17 | Session 5 Round 21 — ABS Guidance Notes 2005 §6 + RightShip 2023; prevents premature closure at intermediate level |
| D-GAP-R02 | **ALARP cost-benefit gate on System-Action recommendations.** Each System Action (per D-DNV-06 tier 3) must include: estimated effort, estimated likelihood reduction, residual-risk acceptability statement. Mandatory for RED and YELLOW bands; optional-but-prompted for GREEN | 2026-04-17 | Session 5 Round 21 — VMTC-RAII (Veritas) + IMO/ISM baseline; adds regulatory defensibility |
| D-GAP-R03 | **Multiple root causes per incident is the default.** Investigator must identify ≥1 root cause; where multiple causal paths are credible, each must be coded separately against M-SCAT. Monocausal conclusion requires a written justification in closure note. Guidance on D-DNV-01 | 2026-04-17 | Session 5 Round 21 — ABS §6.1 (Multiple Coding Approach); prevents premature closure |
| D-GAP-R04 | **Chain-of-Custody tab added to D-DNV-07 Evidence Workspace.** Every physical evidence item captured: description, collection date/time, collector name + signature, storage location (sealed-bag ID if applicable), witness signature, handover log (who-got-it-when) until closed. Extends D-DNV-07 | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.5 + Nautical Institute 2019 guidelines; legal-discovery defensibility |
| D-GAP-R05 | **Marine document inventory auto-checklist** embedded in D-DNV-07 Paper evidence tab. Pre-populated list: Deck Log (rough + smooth), Engine Log, Radio Log, ECDIS track, AIS record (shore-requested), VDR data, Noon/Bunker records, ISM certificates, Stability booklet, Class certificates, Maintenance records. Each item tick = captured-with-timestamp. Cargo incidents load additional overlay per D-GAP-R10 | 2026-04-17 | Session 5 Round 21 — Nautical Institute 2019 List 1; prevents evidence loss |
| D-GAP-R06 | **Evidence-preservation deadline task list auto-generated on incident creation.** System creates scheduled prompts: VDR capture within 12h (RED hard alarm), ECDIS track snapshot within 24h, AIS shore-request within 24h, photo walk-around within 48h, full formal statements within 7 days. Overdue items surface on incident dashboard | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.2; VDR overwrites every 12h on standard units |
| D-GAP-R07 | **First-hour scene-protection checklist** (Master / CO responsibility) shown as the opening block of a new incident record: freeze/mark alarm logs · note extent of damage (initial assessment) · secure scene (no repairs / movements) · photograph + sketch before detailed examination · record witnesses present. Tick-completed before Phase 1 Submit. Superseded for the current user-facing incident flow by `D-MAINT-CR018`. | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.2–3; evidence integrity |
| D-GAP-R08 | **Add IMO regulatory classifier field on incidents: SMC (Serious Marine Casualty) / MC (Marine Casualty) / MI (Marine Incident).** This field is separate from and in addition to existing risk band (GREEN/YELLOW/RED per D-DNV-02). Classifier drives external reporting template (MSC-MEPC.3 per D-DNV-12) and is used in auditor exports. **Investigation deadlines remain the risk-band deadlines locked in D-DNV-02** (not 60/30/30 SMC/MC/MI windows) | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.5.6 + OCIMF + IMO Res A.1075(28); reconciliation choice option (b) |
| D-GAP-R09 | **Refine D-PDF-01 formal incident report template with standard sections:** (1) Cover + classification (R08) + risk band · (2) Investigator/team credentials · (3) Evidence collected (summary table, cross-ref Chain-of-Custody) · (4) Root-cause analysis (with Immediate/Intermediate/Root labels per R01) · (5) 7-point causal-factor enumeration (per KAIZEN §11.5.6.1) · (6) Corrective + Preventive actions with timeline (R13 taxonomy) · (7) Lessons Learnt · (8) Fleet notification plan · (9) Signatures per D-PDF-01 · (10) Appendices — attachments list | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.5.6 + "Good Closure Report" exemplar; standardises the internal report |
| D-GAP-R10 | **Cargo-specific evidence overlay in D-DNV-07.** When incident type = Cargo, load additional evidence prompts: tank ullage record, sounding log, cargo-hold bilge record, cargo sampling, hatch-cover certificates, cargo-hold temperature/humidity, stability calculations, manifest, shipper instructions, cargo inspection reports. Driven by incident-type value | 2026-04-17 | Session 5 Round 21 — Nautical Institute 2019 Lists 9/10/11; cargo incidents = largest category |
| D-GAP-R11 | **Tolerable-Failure Filter at Phase 1.** New pre-investigation decision gate: investigator assesses whether the event is a preventive-maintenance / repeat low-consequence failure already trended in the Pareto dashboard (per R17) — if yes, close as "Tolerable — referenced to trend analysis" without full RCA. Requires DPA acknowledgment. GREEN-band only; YELLOW/RED always proceed | 2026-04-17 | Session 5 Round 21 — TapRoot Dictionary 7th ed. + IMO RCA Guidance §9.6; cost-discipline |
| D-GAP-R12 | **Organisational defence-traps added to bias-guard set (D-DNV-11).** Adds 3 guards beyond the existing 5: "Plant-Problem Trap" (blames hardware to avoid process issues) · "Personnel-Problem Trap" (blames person to avoid system issues) · "External-Event Trap" (blames outside event to avoid internal control issues). Each fires as a soft warning if the investigation's coded causes cluster in that category | 2026-04-17 | Session 5 Round 21 — RightShip Lessons Learned 2023; targets institutional culture not investigator psychology |
| D-GAP-R13 | **Visual taxonomy on D-DNV-06 recommendations:** each item tagged explicitly as Corrective (fix the symptom) · Preventive (fix the system) · Lessons Learnt (share). Colour-coded badges + filter in dashboard. Closure checks that at least one of each tier exists for YELLOW/RED (per D-DNV-06) | 2026-04-17 | Session 5 Round 21 — RightShip 2023; reduces symptom/system confusion at closeout |
| D-GAP-R14 | **Investigation-depth Task Triangle** added to Phase 1 scoping. Investigator chooses SHALLOW · MEDIUM · DEEP based on severity × systemic-risk × learning-value × resources. Auto-recommends based on risk band but DPA can override. Depth drives which D-DNV-10 analysis tools are mandatory (DEEP = all 5; MEDIUM = 3; SHALLOW = 2) | 2026-04-17 | Session 5 Round 21 — IMO/TC RCA Guidance Feb 2014 §2.1; risk-proportionate rigour |
| D-GAP-R15 | **Management-of-Change governance sub-code added to M-SCAT taxonomy** under Category 10 "Inadequate Management of Change": new code `10.15 Design/MOC Governance — Independent Review Absent` (to be inserted into `safety-reference-data/mscat_taxonomy.csv` at seed time; DPA may refine description post-deploy) | 2026-04-17 | Session 5 Round 21 — TapRoot Dictionary "MOC-NI"; closes a common maritime gap (equipment swaps, crew changes without safety review) |
| D-GAP-R16 | **People / Process / Plant interrogatory checklist** enforced at Phase 5 gate (before loop-back decision). Three mandatory questions: (1) How did actions of people contribute? (2) What gaps in procedures? (3) What machinery / equipment failures? Each answered before Phase 5 Submit. Extends D-DNV-10 | 2026-04-17 | Session 5 Round 21 — RightShip 2023; prevents one-dimensional investigations |
| D-GAP-R17 | **Pareto screening panel on Safety Intelligence Dashboard** — top-N repeat failures (by M-SCAT leaf + vessel + rolling 12 months). Feeds R11 Tolerable-Failure decision and R19 chronic-incident flagging. Extends D-DNV-13 dashboard set | 2026-04-17 | Session 5 Round 21 — IMO/TC RCA Guidance §9.6 Pareto analysis |
| D-GAP-R18 | **Safeguard-failure interrogatory extending D-DNV-10 Barrier tool.** For every failed safeguard identified, investigator systematically codes: Design (spec) / Installation (QC) / Maintenance (PM effectiveness) / Operation (procedure adherence) / Testing (validation) / Override (authorisation + training). Each dimension mapped back to an M-SCAT code | 2026-04-17 | Session 5 Round 21 — ABS Guidance Notes 2005 App. 2; strengthens barrier analysis depth |
| D-GAP-R19 | **Witness statement read-back + sign-off protocol** enforced on D-DNV-08 Interview module. After investigator prepares statement from interview notes, system requires: (a) read-back to witness (tick), (b) witness signature on paper (scan or wet-sign), (c) copy to witness recorded. No statement considered "final" without these three. Aligns with D-GAP-M15 paper-signature pattern | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.4; legal defensibility of statements |
| D-GAP-R20 | **Formal vs Informal interview distinction** in D-DNV-08. Interview flagged at start: FORMAL (enforces R19 read-back + sign) or INFORMAL (accepted as evidence if formal interview was impossible — reason field mandatory). Visible on the interview record and on auditor export | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.4 + Nautical Institute 2019 List 5; flexibility with traceability |
| D-GAP-R21 | **Marine-specific Risk & Change Management domain** added to D-DNV-09 human-factors set (alongside SHELL + IMO A.884(21) 7 domains). New domain prompts: Risk control inadequacy · Monitoring gaps (reactive vs proactive) · Change-management effectiveness · Regulatory-compliance failures | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.5.6.1; deepens causal analysis for SMS-linked incidents |
| D-GAP-R22 | **Near-miss Low vs High priority triage** at creation time. Auto-classifier suggests Low (Master/DPA correspondence — close with explanatory note if not classified as near miss) vs High (full investigation · onboard + ashore causal analysis · preventive measures with timeline · fleet alert within 1 week). Safety Officer may override the auto-classification. Replaces ad-hoc handling | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.6; resource efficiency + fast fleet-alert on significant near misses |
| D-GAP-R23 | **Health / fatigue evidence sub-section** added to D-DNV-07 People tab, activated when incident type = Personal Injury / Illness / Fitness-for-Duty. Prompts: ship + ashore medical records · medication record · hours-on-duty (96 h lookback) · sleep hours · fitness-for-duty status pre-incident · vaccination record · pre-existing conditions · medical advice received | 2026-04-17 | Session 5 Round 21 — Nautical Institute 2019 Lists 2/3; completes personal-injury investigations |
| D-MAINT-CR009 | **Incident PDF selectable content:** Incident PDF preview/download lets the user choose included sections, all sections are selected by default, and omitted/empty section selection prints all supported sections for backward compatibility. | 2026-06-24 | Maintain-mode enhancement CR-009: users need control over which report sections are printed. |
| D-MAINT-CR058 | **Phase 6 PDF compulsory content with optional Loss Evaluation:** Phase 6 Office Review no longer exposes the multi-section PDF checklist. All normal incident report sections are compulsory; the only visible PDF option is **Print Loss Evaluation**, mapped to the existing `estimated_cost` backend section key. Supersedes CR-009 for the current Phase 6 user-facing selector while retaining backend section-filter compatibility for old/direct exports. | 2026-07-07 | Maintain-mode correction CR-058: routine users should not choose core report content, only whether the additional Loss Evaluation prints. |
| D-MAINT-CR059 | **Incident PDF final-report grouping:** Current Incident PDFs render each Witness Statement as its own block, split Corrective Actions and Preventive Actions, print only **Office comments/ lesson learnt** in the closure area, and show only Reporter plus PIC / DPA office signature rows. Supersedes D-PDF-01/D-GAP-R09 only for current PDF signature-row composition and supersedes CR-027 where closure reason was printed. | 2026-07-07 | Maintain-mode PDF correction CR-059: users needed the generated report to match the current simplified workflow and avoid duplicated closure wording. |
| D-MAINT-CR060 | **Incident PDF action and witness row simplification:** Current Incident PDFs keep witness identity in each Witness Statement block heading and do not repeat a Witness name row. Corrective and Preventive action blocks print only Description and Due date; action status, physical verification note, closed-at, and recommendation verification rows are not printed. Supersedes D-MAINT-CR059 only where it described a separate Witness name PDF row. | 2026-07-08 | Maintain-mode PDF refinement CR-060: users wanted the final PDF to show only the action information currently recorded in the simplified action workflow and avoid repeated witness identity. |
| D-MAINT-CR010 | **Incident edit window until office approval:** Reached incident phases remain editable by authorized users until office approval/closure/supersession locks the record. Advancing phases does not by itself make earlier phases read-only. | 2026-06-24 | Maintain-mode correction CR-010: vessel/office users must be able to correct investigation details before approval. |
| D-MAINT-CR011 | **Phase 1 edit persistence and PDF pending signatures:** Phase 1 edit saves update the incident without deleting existing injury rows when injury payload is omitted, and formal PDFs show required signature rows even when unsigned. | 2026-06-24 | Maintain-mode correction CR-011: saved injury data and required sign-off rows must remain visible. |
| D-MAINT-CR012 | **Simplified incident evidence capture:** user-facing Phase 4 evidence now uses one Documents section. Each evidence entry is Attachment + Title + Description. Legacy People / Position / Parts / Electronic category routes redirect to Documents, and legacy tab codes remain API/database compatibility only. Supersedes the user-facing portions of D-DNV-07, D-GAP-R05, D-GAP-R10, and D-GAP-R23. | 2026-06-24 | Maintain-mode correction CR-012: the category evidence screen was too chaotic for users; preserving backend compatibility avoids risky data migration. |
| D-MAINT-CR013 | **Early evidence capture before Phase 4 reached:** authorized users may open Phase 4 Documents and add evidence attachments before Phase 2/Phase 3 are complete or before `current_phase` reaches 4. Ordered submit transitions still run in sequence, and approval/closure/superseded locks still stop editing. Supersedes reached-phase gating for the Documents evidence endpoints only. | 2026-06-24 | Maintain-mode correction CR-013: available evidence should be captured immediately instead of blocked by investigation phase sequencing. |
| D-MAINT-CR014 | **SCM WRH readiness gate for hosting:** Regular and Ad-Hoc SCM meeting creation is allowed only when ship-time configuration exists for the vessel/date and all SCM roster crew have available, compliant WRH data. Supersedes D-GAP-M11 for SCM meeting creation only; existing created-meeting detail, PDF, and Office Comment closure continue to show WRH gaps as warnings unless changed separately. | 2026-06-26 | Maintain-mode correction CR-014: users should not host an SCM while the create flow still shows WRH warnings. |
| D-MAINT-CR015 | **Phase 4 Evidence Check removal:** The current Phase 4 user interface no longer exposes Evidence Check / Evidence Matrix as a route, optional card, form, or transition gate. Legacy evidence-matrix APIs and stored rows remain compatibility-only. Supersedes D-DNV-07 and D-DNV-11 #4 for current user-facing Evidence Matrix enforcement only. | 2026-06-29 | Maintain-mode simplification CR-015: users should not see the confusing Evidence Check tool in Phase 4. |
| D-MAINT-CR016 | **Phase 4 simplified Witness Notes:** The current Phase 4 Witness Notes UI exposes only Witness name, What the witness said, and Closing note. The frontend submits these notes as informal compatibility records with a system reason; legacy formal/informal interview APIs and stored data remain compatible. Supersedes D-DNV-08, D-GAP-R19, and D-GAP-R20 for current user-facing Witness Notes only. | 2026-06-29 | Maintain-mode simplification CR-016: users should not see formal interview protocol fields in routine Witness Notes capture. |
| D-MAINT-CR017 | **Phase 4 save acknowledgement:** Phase 4 document, witness-note, and checklist saves show an inline success acknowledgement and move focus/scroll to the saved content area. | 2026-06-29 | Maintain-mode UX correction CR-017: users need immediate confirmation that saved evidence is visible. |
| D-MAINT-CR018 | **Phase 1 first-check removal:** The current user-facing Incident Phase 1 flow does not render, require, accept from the frontend, expose through incident serializers, or print the first-hour/First Checks checklist. The existing `first_hour_checklist_done` database column remains historical storage only. Supersedes `D-GAP-R07` for current Incident Phase 1 UI/API/PDF behavior. | 2026-06-29 | Maintain-mode simplification CR-018: users do not need a separate first-check checklist in the incident flow. |
| D-MAINT-CR019 | **Final Record history simplification:** The current Incident Final Record UI shows final summary cards, simplified Phase History, approvals, reports, and reopen action. It does not show the Change History card or History Rows metric, and it formats `NOT_APPLICABLE` IMO classifier values as `No IMO class`. Field/change-history data remains available through audit APIs for authorized audit/export use. | 2026-06-29 | Maintain-mode simplification CR-019: routine users need a clear final record, not raw audit counters or enum values. |
| D-MAINT-CR020 | **Incident UI technical-card cleanup:** The current Phase 2 RCA page does not show an Evidence Notes summary card, and the incident register does not show the Current Scope card. | 2026-06-29 | Maintain-mode simplification CR-020: these cards exposed implementation detail and confused routine users. |
| D-MAINT-CR021 | **Missing vessel incident type removed:** The current Incident Type picklist and `master_safety_incident_type` seed/master data do not include `IMO_MISSING_VESSEL` / Missing vessel. Existing incident records are not rewritten by this change. Supersedes `D-DNV-04` only for the removed option in current UI/master-data behavior. | 2026-06-29 | Maintain-mode simplification CR-021: users should not be offered Missing vessel as an incident type. |
| D-MAINT-CR022 | **Incident save acknowledgements:** Phase 2 RCA cause saves, action-screen saves, and Evidence document/witness saves show success messages and scroll/focus to the saved-content area. | 2026-06-30; wording current as of CR-038 | Maintain-mode UX correction CR-022: users need to see that their investigation input was saved. |
| D-MAINT-CR024 | **Phase 1 reporting context fields moved to incident:** Shore Assistance Required, Location of Vessel, Location on Board, Last Port, Departure Date, and Vessel Condition are current incident-level fields shown in the main Phase 1 Incident Report section. Legacy injury-row copies remain compatibility-only for older injury records and PDF fallback. Supersedes CR-023's temporary UI placement of these fields inside a shared injury subsection. | 2026-06-30 | Maintain-mode correction CR-024: users need these fields visible for normal incident reporting even when no injury row exists. |
| D-MAINT-CR025 | **Optional injury estimated cost:** Injury estimated-cost fields are hidden until the user chooses to add estimated cost details; selecting No keeps the section hidden and does not block continuation. | 2026-06-30 | Maintain-mode simplification CR-025: estimated cost entry is optional and should not force injury reporting. |
| D-MAINT-CR026 | **Incident header technical badges removed:** Current Phase 1 headers do not show the internal incident UUID or auto-save status chip; auto-save behavior remains active where implemented. | 2026-06-30 | Maintain-mode UI cleanup CR-026: technical identifiers and autosave state should not clutter the user form header. |
| D-MAINT-CR027 | **Incident PDF closure and Lessons layout:** closure reason is excluded from the Summary table and prints in a Closure block immediately before Signature when present. Lessons Learned descriptions print once inside their detail box and are not repeated as a separate paragraph above the box. | 2026-07-01 | Maintain-mode PDF layout correction CR-027: closure rationale belongs at final sign-off context, and duplicated lesson text made the PDF harder to read. |
| D-MAINT-CR028 | **Lessons Learned rationale hidden:** Current incident Next Actions UI does not show "Why is this needed?" for `LESSONS_LEARNT`, does not send lesson rationale from the frontend, and the incident PDF Lessons Learned block does not print stored lesson rationale. Corrective and preventive action rationale remains available. | 2026-07-01 | Maintain-mode simplification CR-028: lesson entries should stay simple and avoid confusing rationale text in the UI and PDF. |
| D-MAINT-CR029 | **Incident PDF evidence document blocks:** Evidence (Documents) PDF output prints each saved attachment as its own document block using the saved title when available, with separate Description and File rows. It does not print generic numbered labels such as `Attachment 1` or `Attachment 2`. | 2026-07-01 | Maintain-mode PDF layout correction CR-029: numbered attachment labels made multi-document evidence hard to read. |
| D-MAINT-CR030 | **Incident PDF evidence notes hidden:** Evidence (Documents) PDF output prints attachment document blocks and saved Witness Notes, but does not print legacy evidence-note-only rows such as root-cause placeholder notes. | 2026-07-01 | Maintain-mode PDF layout correction CR-030: internal evidence notes were confusing in the formal PDF and duplicated investigation context. |
| D-MAINT-CR031 | **Incident Type master list replaced:** Current Incident Phase 1 dropdown and `master_safety_incident_type` seed/master data expose 32 active incident-type options in the user-provided order. Retired earlier rows, including `IMO_MISSING_VESSEL`, remain unavailable for new selection; historical records remain readable. Supersedes `D-MAINT-CR021` for current active option count/list. | 2026-07-03 | Maintain-mode master-data replacement CR-031: users need a more precise incident-type list covering allisions, bottom-touch events, equipment failures, injury, pollution, local regulation, stowaway, security, cyber security, and Other. |
| D-MAINT-CR032 | **Incident Phase 1 field cleanup:** Current Phase 1 labels say "Was office informed?" and "How was office informed?"; WhatsApp is not offered in the current communication-mode dropdown; Latitude and Longitude are grouped in one row; Shore Assistance follows the coordinate row; Last Port and Weather ice-condition fields are hidden and omitted from current frontend save/submit payloads. Legacy columns and old values remain readable. Supersedes `D-MAINT-CR024` only for Last Port current visibility/payload behavior. | 2026-07-03 | Maintain-mode UI simplification CR-032: reduce Phase 1 clutter and improve wording/layout without dropping compatibility storage. |
| D-MAINT-CR033 | **Incident RCA and action simplification:** Current Incident RCA exposes and accepts only Immediate Cause and Root Cause. Intermediate Cause is legacy storage compatibility only and is not shown as a current category in UI/PDF. Current action capture does not show or send "Why is this needed?" for corrective, preventive, or lesson entries. Supersedes `D-GAP-R01` and `D-GAP-R09` only for current user-facing Intermediate Cause labels, and supersedes `D-MAINT-CR028` for corrective/preventive rationale availability. | 2026-07-03; wording current as of CR-038 | Maintain-mode simplification CR-033: users asked to remove Intermediate Cause completely from the current flow and remove the why-needed field from corrective action capture. |
| D-MAINT-CR034 | **Incident Phase 1 Shore Assistance placement:** Current Phase 1 places Shore Assistance Required beside Report time while Latitude and Longitude remain grouped on their own row. Supersedes `D-MAINT-CR032` only for Shore Assistance field placement. | 2026-07-03 | Maintain-mode layout correction CR-034: users asked for Shore Assistance Required beside Report time. |
| D-MAINT-CR035 | **Incident weather migration compatibility:** `safety.0043_incident_weather_condition_fields` must be safe when `vims_safety_incident_weather_option` or incident weather columns already exist before Django records the migration. It registers Django state and runs conditional SQL Server DDL instead of requiring manual table drops. | 2026-07-03 | Maintain-mode migration failure CR-035: SQL Server deployment failed because the weather option table already existed. |
| D-MAINT-CR036 | **Incident Witness Statement simplification:** Current Phase 4 labels the witness tool as Witness Statement, opens `/phase-4/interviews/` directly, loads the incident vessel crew list for witness-name selection, provides Other with typed name, captures What the witness said, Remark, and optional signature image upload, and stores the statement through the legacy informal witness-interview payload. | 2026-07-03 | Maintain-mode simplification CR-036: users need a clearer witness statement flow without formal interview fields. |
| D-MAINT-CR037 | **Incident duplicate phase headers removed:** Current incident phase tabs are the only phase number/name indicator; phase workspace content no longer repeats separate Phase X/phase-title header cards. | 2026-07-03 | Maintain-mode UI cleanup CR-037: phase cards already tell users which phase they are on. |
| D-MAINT-CR038 | **Incident action phases split:** CR-038 originally split Corrective Action, Preventive Action, and Lessons Learned into separate visible phases. CR-042 supersedes this for Lessons Learned: current workflow keeps Corrective Action and Preventive Action separate, removes the visible Lessons Learned phase, removes Final Record from the visible workflow tabs, removes the owner/checker card from action entry, keeps Due date on Corrective Action, hides Remaining risk and the risk-confirmation checkbox on Preventive Action, and reuses existing backend recommendation/corrective-action storage for compatibility. | 2026-07-03; superseded in part by CR-042 | Maintain-mode workflow simplification CR-038 with CR-042 correction: users should complete action categories without an extra lesson phase, and read-only final records should not appear as an editable workflow phase. |
| D-MAINT-CR039 | **Incident Phase 2-6 editable save window:** Current user-facing phases 2 through 6 remain editable for authorized users until office approval, closure, or supersession. RCA, fact/evidence helper rows, corrective action, preventive action, and evidence document saves no longer require the incident `current_phase` to have reached the legacy backend phase number; submit/continue and office approval gates still enforce ordered workflow movement. | 2026-07-03; wording current as of CR-042 | Maintain-mode behavior correction CR-039: users must be able to work across investigation phases and correct saved details without being blocked by legacy backend phase numbering. |
| D-MAINT-CR040 | **Incident RCA saved-cause edit controls:** Current Phase 2 saved Immediate Cause and Root Cause cards show an Edit action. Editing loads the existing cause into the RCA form, saves through the existing cause update endpoint, and updates the saved cause instead of creating a duplicate. | 2026-07-03 | Maintain-mode usability correction CR-040: backend editability was not sufficient without a visible way for users to edit saved RCA causes. |
| D-MAINT-CR041 | **Incident action/evidence saved-entry edit controls:** Current Phase 3 Corrective Action, Phase 4 Preventive Action, and Phase 5 Add Evidence saved cards show Edit actions. Editing loads the saved action, document metadata, or Witness Statement into its form and saves back to the existing row without creating a duplicate. The previous Lessons Learned edit surface is removed by CR-042. | 2026-07-03; wording current as of CR-043 | Maintain-mode usability correction CR-041: the same visible edit affordance required for RCA must exist for later saved investigation entries. |
| D-MAINT-CR042 | **Incident Lessons phase removed and Office Review comments added:** Current incident workflow removes the visible Lessons Learned screen. Preventive Action continues directly to Office Review. Office Check is renamed Office Review, and Office Review exposes an unrestricted Office Comments textbox saved to `vims_safety_incident.office_comment` through migration `0052_incident_office_comment`. Current PDF selectors do not show Lessons Learned by default; legacy lesson data/API/PDF support remains compatibility-only for old/direct exports. | 2026-07-03; wording current as of CR-043 | Maintain-mode structural correction CR-042: users asked to remove the lesson phase and capture the key office comment directly on the office decision screen. |
| D-MAINT-CR043 | **Incident visible phase numbering is sequential:** Current phase tabs and shared phase labels read Phase 1 Report Incident, Phase 2 RCA, Phase 3 Corrective Action, Phase 4 Preventive Action, Phase 5 Add Evidence, Phase 6 Office Review, and Phase 7 Check Actions. Backend `current_phase` values, route paths, and legacy component/API names remain unchanged for compatibility. | 2026-07-03 | Maintain-mode structural correction CR-043: after removing Lessons Learned, the visible workflow must not skip from Phase 4 to Phase 6. |
| D-MAINT-CR047 | **Incident visible Phase 7 is Loss Evaluation:** CR-047 supersedes CR-043 only where visible Phase 7 was named Check Actions. Backend `current_phase` 8 and compatibility route `/safety/incidents/:id/phase-6` remain unchanged, but the workspace now saves `vims_safety_incident_loss_evaluation`. Superseded by D-MAINT-CR056 where CR-047 made Phase 7 the close owner. | 2026-07-06 | Maintain-mode structural change CR-047: Phase 7 now captures risk, loss, repair/injury, and cost evaluation for Incident Report and Injury Report records. |
| D-MAINT-CR048 | **Safe Working Practice dropdown is seeded:** Phase 7 Injury Report Loss Evaluation uses `vims_safety_injury_dropdown_option` rows where `field_key = SAFE_WORKING_PRACTICE`; migration `0055_seed_safe_working_practice_options` seeds the user-provided Code of Safe Working Practices list, stores exact duplicate labels once, and deactivates stale choices outside the list. | 2026-07-06 | Maintain-mode master-data change CR-048: the previously dropdown-ready safe-working-practice field now has the requested active choices. |
| D-MAINT-CR044 | **Incident Office Review decisions are not risk-band specific:** PIC and DPA can accept, close, or send an incident back for rework for GREEN, YELLOW, and RED risk bands. FM-specific RED Office Review closure is no longer required by the current implemented flow; legacy route names remain compatibility-only. | 2026-07-06 | Maintain-mode structural correction CR-044: user required PIC and DPA authority for Office Review decisions regardless of risk band. |
| D-MAINT-CR045 | **Incident Witness Statement entry opens directly:** Current Phase 5 Add Evidence shows Witness Statement as a direct navigation card to `/phase-4/interviews/`. The intermediate **Open Witness Statement** step is not shown. | 2026-07-06 | Maintain-mode UI correction CR-045: users asked for the Witness Statement click to open the witness page immediately. |
| D-MAINT-CR049 | **Incident action, witness, and Office Review UI simplification:** Current Preventive Action shows only Description, Due date, and How much will this reduce risk? Current Witness Statement shows Witness name, optional Other typed name, Upload witness statement, and Remark below the upload. Current Office Review removes root/action counters, pre-approval summary cards, approval-role wording, and send-back target selection; office-side users see Accept / Close and Send for rework cards, while ship-side users see only Office Comments/lesson learnt when present. Supersedes D-MAINT-CR036 for current Witness Statement fields and D-MAINT-CR038/D-MAINT-CR042/D-MAINT-CR044 only for the current visible fields and ship/office visibility. | 2026-07-06 | Maintain-mode UI/workflow simplification CR-049: users asked to remove technical and redundant wording while keeping workflow behavior intact. |
| D-MAINT-CR074 | **Incident Office Review rework summary:** Current Incident Office Review keeps only one Send for rework comment textbox and does not expose a target-phase picker. The typed comment is stored on the existing `vims_safety_incident_phase_log` REWORK row and is returned as `rework_summary` while the incident remains sent back so users can read the requested changes from the Office Review screen. | 2026-07-13 | Maintain-mode correction CR-074: users needed the office rework instructions visible after send-back without reintroducing target selection. |
| D-MAINT-CR075 | **Incident Rework Done action:** While an incident is `SENT_BACK`, Phase 6 Office Review highlights the Rework summary in red and shows a Rework Done button to both ship-side and office-side users. Clicking it transitions backend phase `6 -> 7` and changes state from `SENT_BACK` to `UNDER_REVIEW`. | 2026-07-13 | Maintain-mode correction CR-075: users needed a shared explicit way to acknowledge that requested rework is complete before Office Review continues. |
| D-MAINT-CR076 | **Incident PDF narrative placement and RCA heading:** Current Incident PDF Summary no longer prints **Describe What happened?** at the top. The incident narrative prints below the intake/detail sections immediately before the cause-analysis section, and that section heading is **Root Cause Analysis**. | 2026-07-13 | Maintain-mode PDF correction CR-076: users required the narrative to appear before cause analysis and the root-cause section title to use the fuller Root Cause Analysis wording. |
| D-MAINT-CR077 | **Safety Dashboard simplified default view:** Current `/safety/dashboard/` defaults to a simplified office view with plain Safety Dashboard/Safety score wording, repeat issues, top repeat causes, corrective-action age, and export controls. Heinrich Ratio and SOI Compliance % remain available but are hidden by default behind **Show more dashboard cards**. The SOI metric keeps the literal **SOI Compliance %** label wherever shown. Supersedes D-GAP-M27 and D-GAP-DESIGN-01 only where those decisions required Heinrich Ratio or SOI Compliance % to be immediately visible on the default dashboard. | 2026-07-13 | Maintain-mode dashboard simplification CR-077: users found the office dashboard too chaotic and asked for advanced cards to display only on request with simpler wording. |
| D-MAINT-CR078 | **Injury duplicate narrative removed:** Current Phase 1 injury Investigation - Narrative does not show a separate **Describe What Happened** field, and current Incident PDFs do not print legacy `what_happened_narrative` from the injury row. The incident-level **Describe What happened?** narrative is the only current user-facing narrative for incident and injury reports. | 2026-07-13 | Maintain-mode correction CR-078: user still saw the duplicate injury narrative field and required it removed from Phase 1. |
| D-MAINT-CR079 | **Office Review send-back phase guard relaxed:** Current Incident Office Review send-back no longer fails solely because the incident has not reached internal `current_phase = 7`. PIC/DPA with send-back permission can enter one rework comment and send the incident to the fixed action-rework phase; the incident becomes `SENT_BACK`, with Rework Done returning it to Office Review/`UNDER_REVIEW`. | 2026-07-13 | Maintain-mode correction CR-079: users hit `Office review actions require current_phase = 7.` when clicking Send for rework from the visible Office Review screen. |
| D-MAINT-CR080 | **Incident register vessel/status filters:** Current Safety Incidents register shows Vessel, `risk_band`, and Status filters. Global office users can select from all active ships, and selected ships are sent through the existing `vessel_id` incident-list filter. Visible label `State` is replaced by Status, and old Band/Risk band wording is replaced by `risk_band`. | 2026-07-13 | Maintain-mode UI correction CR-080: user required a vessel dropdown on the incident register and clearer filter/table labels shown in `Error_Images/saf22.png`. |
| D-MAINT-CR081 | **Incident action Due Date restored:** Current Phase 3 Corrective Action and Phase 4 Preventive Action collect Description and optional Due Date only. Due Date is saved through the existing linked corrective-action payload and displayed on saved action cards. Status/open-close, verification, owner/checker, risk-reduction, theme, effort, and remaining-risk controls remain hidden. Supersedes D-MAINT-CR065 and D-MAINT-CR066 only for current action due-date capture/display. | 2026-07-13 | Maintain-mode correction CR-081: user clarified that removing action status/closure controls must not remove Due Date from Phase 3 and Phase 4 action capture. |
| D-MAINT-CR082 | **Injury Report narrative placement:** Current Injury Report PDFs render **Describe What happened?** immediately after **Reporter Details** and before **Injury Details**. Standard Incident Report PDFs keep the narrative below intake/detail content and immediately before **Root Cause Analysis**. Legacy injury-row `what_happened_narrative` remains suppressed. Supersedes D-MAINT-CR076 only for Injury Report narrative placement. | 2026-07-13 | Maintain-mode PDF correction CR-082: user required the Injury Report narrative to appear after Reporter's Details. |
| D-MAINT-CR083 | **Near Miss Fleet Alert email delivery:** Current HIGH-priority Near Miss Fleet Alert issue sends in-app `NEAR_MISS_FLEET_ALERT` notifications plus one batched email to selected vessel `VesselData.Email` recipients using BCC, with `HSSEQ@kaizenship.net` in CC. Missing selected-vessel email or missing SMTP sender credentials blocks issue before completion history is written. The Circular module handoff remains separate and Safety still does not direct-create Circular records. | 2026-07-13 | Maintain-mode integration correction CR-083: users required Near Miss Fleet Alert to match Incident Fleet Alert delivery with in-app notification plus email. |
| D-MAINT-CR086 | **Fleet Alert PDF email attachment:** Current Incident and Near Miss Fleet Alert email dispatch attaches the matching Incident/Near Miss PDF and uses a short prevention-focused body that tells selected vessels the event happened, to review the PDF, and to take preventive action. In-app notification behavior, selected-vessel scoping, BCC batching, and `HSSEQ@kaizenship.net` CC remain unchanged. | 2026-07-14 | Maintain-mode behavior change CR-086: users required Fleet Alert email to carry the PDF and avoid long duplicated email body text. |
| D-MAINT-CR084 | **Safety Dashboard quieter default and Auditor Export vessel dropdown:** Current `/safety/dashboard/` defaults to Safety score, Current view, period/vessel controls, and export controls. Repeat issues, top repeat causes, corrective-action age, Heinrich Ratio, and SOI Compliance % are hidden until the user opens **Show dashboard details**. `/safety/admin/auditor-export/` uses an active-vessel dropdown for Vessel filter instead of a free-text field. Supersedes D-MAINT-CR077 only where CR-077 kept repeat issues, top causes, and corrective-action age visible by default or named the old **Show more dashboard cards** control. | 2026-07-13 | Maintain-mode dashboard/export simplification CR-084: users asked to simplify the Safety Dashboard even more and make Auditor Export's Vessel filter contain vessel dropdown options. |
| D-MAINT-CR085 | **Safety sidebar removes broad Admin shortcut:** Current Safety sidebar does not show a broad **Admin** link. **Auditor Export** remains a direct sidebar link for users with `SAF_F_020`. Existing admin/config routes remain permission-gated for direct access but are not advertised as a sidebar Admin section. | 2026-07-13 | Maintain-mode navigation simplification CR-085: user asked to remove the Admin section from the sidebar and keep only Auditor Export because it is the useful admin-facing shortcut. |
| D-MAINT-CR055 | **Phase 1 estimated costs removed and Witness Statement order clarified:** Current Phase 1 injury capture does not show or submit injury estimated-cost fields; users record current estimated-cost data in Phase 7 Loss Evaluation. Legacy injury cost columns remain readable for old records and fallback export behavior. Current Witness Statement field order is Witness name, optional Other typed name, Upload witness statement, then Remark below the upload. Supersedes D-EDGE-02 and D-MAINT-CR025 only where they made Phase 1 estimated-cost entry a current visible UI behavior. | 2026-07-07 | Maintain-mode UI ownership correction CR-055: cost entry belongs in the dedicated Loss Evaluation phase, and the witness upload should appear above the remark field. |
| D-MAINT-CR050 | **Office Review pending comment and PDF availability:** Ship-side Office Review always shows the Office Comments/lesson learnt card; if office has not added a note, it displays "Office comment is not added yet." Office-side Phase 6 does not show Phase 7 acceptance-only PDF warning text, and incident PDF preview/download plus MSC-MEPC.3/Circ.4 export are not blocked solely by pending Phase 7 acceptance. | 2026-07-07 | Maintain-mode correction CR-050: users needed a visible pending state for missing office comments and PDF export without the Phase 7 acceptance-only guard. |
| D-MAINT-CR051 | **Incident Fleet Alert from Office Review:** Office-side Phase 6 Office Review shows a Fleet Alert action below Accept / Close. PIC or DPA opens the ship selector, selects one or more active `VesselData` ships, and the system sends in-app `INCIDENT_FLEET_ALERT` notifications plus emails only to the selected ships using `VesselData.email`. No new Safety table or migration is introduced. Wording current as of D-MAINT-CR061. | 2026-07-07 | Maintain-mode feature CR-051: users needed the Near Miss fleet-alert concept available for Incidents with explicit selected-ship targeting. |
| D-MAINT-CR061 | **Incident Fleet Alert remains available after Office Review close:** PIC/DPA can send the selected-ship Incident Fleet Alert from the Office Review screen after Accept / Close has advanced the incident to the final backend phase. The backend blocks early investigation phases but accepts Office Review and later phases for this notification action. Wording current as of D-MAINT-CR062. | 2026-07-08 | Maintain-mode availability correction CR-061: DPA users hit the old "Incident Fleet Alert is available from Office Review." guard after closing from Office Review. |
| D-MAINT-CR062 | **Incident Fleet Alert popup and SMTP configuration:** Clicking Fleet Alert opens a vessel-selection popup populated from active, non-deleted `VesselData` rows. Confirm sends in-app notifications plus email only to selected vessels using `VesselData.email`. SMTP sender settings come from environment variables such as `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL`; no email password is stored in tracked source. | 2026-07-08 | Maintain-mode UI/config correction CR-062: users expected a vessel popup and selected-vessel email delivery from the configured sender account. |
| D-MAINT-CR064 | **Incident Phase 1 operational fields and PDF/Fleet Alert refinements:** Current Phase 1 stores Risk Assessment carried out, Toolbox Meeting carried out, Permit Issue, Type of Activity, Incident Type Other details, Location of Vessel, and Location of Vessel detail for In Port / At Anchorage. Phase 6 PDF download is available to ship-side users with only the optional Print Loss Evaluation checkbox; Fleet Alert popup has Select all vessels and emails CC `HSSEQ@kaizenship.net`. Incident PDF prints sections in visible phase order, starts Loss Evaluation on a new page when selected, labels onboard location as Location on Board, and prints root causes/actions as unnumbered detail boxes. | 2026-07-08 | Maintain-mode behavior change CR-064: user required richer Phase 1 intake, ship-side PDF download, selected-all fleet alert support, fixed email CC, and cleaner final PDF layout. |
| D-MAINT-CR065 | **Description-only incident actions and final PDF layout:** Current Incident Corrective Action and Preventive Action screens record Description only; due date, status/open-close, owner/checker, risk-reduction, and verification/closure fields are not current user-facing action capture. Phase 1 places Risk Assessment carried out, Toolbox Meeting carried out, Permit Issue, and Type of Activity above Departure Date and Vessel Condition. Incident PDF prints Location of Vessel and Specific vessel location separately, groups Immediate Cause and Root Cause once each with cause factor left and cause/reason right, prints witness-statement attachment presence, groups Corrective Actions and Preventive Actions independently with Description only, and renders Office comments/ lesson learnt as one full-width comment box. Supersedes D-MAINT-CR052, D-MAINT-CR060, and D-MAINT-CR064 only for current action required fields and these PDF layout details. | 2026-07-09 | Maintain-mode behavior/layout correction CR-065: users required action rows to record only descriptions and the final PDF to match the visible phase structure without repeated labels or closure/comment splits. |
| D-MAINT-CR066 | **Incident PDF due dates, witness attachment links, and undivided closure:** Current action screens still collect Description only, but Incident PDF Corrective Actions and Preventive Actions print any saved linked Due date beside the Description. Witness Statement attachment rows render a clickable link to the stored statement attachment instead of printing plain attachment presence. Office comments/ lesson learnt renders as one undivided full-width closure comment box with no filler label. Supersedes D-MAINT-CR065 only for action due-date PDF output and witness attachment PDF wording. | 2026-07-10 | Maintain-mode PDF correction CR-066: users required due dates in the PDF, direct witness attachment links, and removal of the closure table split shown in `Error_Images/saf20.png`. |
| D-MAINT-CR072 | **Incident PDF witness text suppression:** Current Incident PDFs do not print the old free-text `What the witness said` value from Witness Statement rows. Witness blocks keep the witness display in the heading, show downloadable attachment links when present, and print Remark. Supersedes D-MAINT-CR036/D-MAINT-CR059/D-MAINT-CR066 only where they described printing witness statement text in the PDF. | 2026-07-10 | Maintain-mode PDF correction CR-072: users repeatedly clarified that the witness free-text value is not part of the current saved/printed PDF output and must not appear even when legacy database rows contain it. |
| D-MAINT-CR073 | **Incident PDF action-before-evidence order:** Current Incident PDFs render Corrective Actions and Preventive Actions before Evidence (Documents). Evidence remains before Office Review/Closure and Signature output. Supersedes D-MAINT-CR064 only where it described Evidence before actions in the PDF section order. | 2026-07-10 | Maintain-mode PDF sequence correction CR-073: users required Evidence (Documents) to appear after both action sections. |
| D-MAINT-CR067 | **Incident PDF action due-date placement:** Incident PDF Corrective Actions and Preventive Actions keep each action as one Description row. Any saved linked Due date is appended inside that Description value and is not rendered as a separate Due date row. Supersedes D-MAINT-CR066 only for due-date placement. | 2026-07-10 | Maintain-mode PDF correction CR-067: users wanted due dates visible but not as separate action rows. |
| D-MAINT-CR068 | **Incident PDF office comment text preservation:** The Closure **Office comments/ lesson learnt** block renders the stored `office_comment` as one full-width comment block without artificial chunking. Typed line breaks are preserved; normal PDF line wrapping may still occur to fit the page width. Supersedes D-MAINT-CR066 only for closure-comment text rendering. | 2026-07-10 | Maintain-mode PDF correction CR-068: users required the PDF to display the office comment as typed instead of splitting it into template chunks. |
| D-MAINT-CR069 | **Incident PDF action boxes:** Incident PDF Corrective Actions and Preventive Actions keep their category headings, then render every saved action as a full-width bordered row/box without a repeated left-side `Description` label column. The action description is the first line and any saved linked due date is the second line as `Due Date: YYYY-MM-DD`. Supersedes D-MAINT-CR067 only for current action-row layout and due-date capitalization. | 2026-07-10 | Maintain-mode PDF layout correction CR-069: users required a cleaner full-width action layout instead of a two-column Description/value split for each action. |
| D-MAINT-CR070 | **Incident PDF omits Last Port:** Last Port remains legacy database/API compatibility storage, but the current Incident PDF does not print Last port from either the incident row or legacy injury-row fallback because current Phase 1 no longer shows or saves that field. Supersedes D-MAINT-CR032 only where it preserved Last Port as a PDF-fallback field. | 2026-07-10 | Maintain-mode PDF correction CR-070: users should not see stale legacy Last Port data in reports when the current incident form does not maintain it. |
| D-MAINT-CR071 | **Incident PDF combines vessel location detail:** Incident PDF prints one Vessel location row. If `vessel_location_detail` is stored for In Port or At Anchorage, the detail is appended to the selected location in the same value, such as `In Port - Singapore`; At Sea selections with no detail do not print a separate `Not recorded` detail row. Supersedes D-MAINT-CR065 only where current PDFs printed Location of Vessel and Specific vessel location separately. | 2026-07-10 | Maintain-mode PDF correction CR-071: users wanted port/anchorage detail readable beside the selected vessel location instead of as a separate row. |
| D-MAINT-CR052 | **Loss Evaluation save is not approval-gated and preventive risk reduction is shared:** Authorized ship-side and office-side users with incident form access and vessel scope can open and save Phase 7 Loss Evaluation without Office Review approval/backend `current_phase` 8. Phase 4 Preventive Action shows one shared How much will this reduce risk? answer for the screen, sends that value with preventive saves for backend compatibility, and does not repeat risk reduction on each saved preventive card. | 2026-07-07 | Maintain-mode behavior change CR-052: users required both ship and office users to fill Loss Evaluation and a single common risk-reduction answer for preventive actions. |
| D-MAINT-CR053 | **Loss Evaluation report type is user-selected:** Phase 7 asks the user to choose Incident Report or Injury Report before showing the Loss Evaluation fields. The choice is stored as nullable `vims_safety_incident_loss_evaluation.report_type`, controls the visible field group on reload, and controls the PDF Loss Evaluation cost/detail block; existing rows without a saved type keep the previous injury-record fallback. | 2026-07-07 | Maintain-mode behavior change CR-053: users must decide which Loss Evaluation form they are recording instead of being forced into the automatic injury-detection layout. |
| D-MAINT-CR056 | **Incident close belongs to Phase 6 Office Review:** Current Office Review Accept / Close moves the incident to terminal closed state. Phase 7 Loss Evaluation is an additional save-only phase for risk/loss/cost details and does not show closing note, Close Incident, or closure readiness controls. The compatibility `/phase-6/close/` endpoint rejects close attempts with guidance to use Phase 6 Office Review. Fixed-tier Corrective and Preventive screens allow saving additional visible action rows when required fields are complete. | 2026-07-07 | Maintain-mode structural correction CR-056: user required closure at Phase 6 and Phase 7 to remain only an addition. |
| D-MAINT-CR057 | **Incident action rows are repeatable by tier:** Corrective and Preventive recommendation rows are no longer limited to one active row per incident/tier. The database unique constraint and API duplicate-tier validation are removed. Save creates another row when visible required fields are complete; Edit updates the selected existing row. | 2026-07-07 | Maintain-mode behavior correction CR-057: user required multiple Corrective and Preventive rows instead of a one-row cap. |
| D-MAINT-CR054 | **Phase 1 vessel identity is system-derived and locked:** Phase 1 auto-fills Vessel and Vessel code from the authenticated vessel context, single-vessel scope, or saved incident. The UI disables those fields after autofill/save, Phase 1 GET returns resolved `vessel_code`, and backend vessel-scope validation remains the authority. | 2026-07-07 | Maintain-mode behavior correction CR-054: users reported missing vessel code and required Vessel/Vessel code to be auto-filled and non-editable. |
| D-MAINT-CR063 | **Loss Evaluation officer names auto-fill from vessel crew:** Phase 7 Other Details defaults Name of master and Name of Chief Engineer from active, non-deleted current onboard crew for the incident vessel using `Crew_Onboarding_History`, `HRM501`, and `master_applied_rank`. Saved user-entered Loss Evaluation values remain authoritative and are not overwritten. | 2026-07-08 | Maintain-mode behavior change CR-063: user required Phase 7 officer names to auto-fill like vessel identity. |

---

## 7. Open Questions

| # | Question | Round | Notes |
|---|----------|-------|-------|
| ~~Q47~~ | ~~RBAC permission matrix~~ | 13 | **CLOSED 2026-04-16** — see D-RBAC-01..11 |
| ~~Q48~~ | ~~Admin/config permissions~~ | 13 | **CLOSED 2026-04-16** — see D-CFG-01..04 |
| ~~Q49 / R15~~ | ~~Edge cases (12 questions)~~ | 15 | **CLOSED 2026-04-16** — see D-EDGE-01..12 |
| ~~R14~~ | ~~PDF Export & Reporting~~ | 14 | **CLOSED 2026-04-16** — see D-PDF-01..03b |
| ~~R16~~ | ~~Safety Officer Inspection (4th V1 sub-feature)~~ | 16 | **CLOSED 2026-04-16** — see D-SOI-01..15 |

---

*This SSOT follows the KLOSS Framework pattern: research → documentation → execution.*
*Interrogation findings will be merged here as the single source of truth.*
