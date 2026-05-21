# VIMS Safety Module — Single Source of Truth

> **Status:** REQUIREMENTS COMPLETE — ready for docsuite generation
> **Created:** 2026-04-08
> **Last Updated:** 2026-04-16
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
| 2 | **Near Miss Reporting** | Capturing near-miss events to build a proactive safety culture — M-SCAT-lite framework | Requirements COMPLETE |
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

### 2B.5 [Diff #4] Incident Type Picklist (IMO 11 Reportable Types)

Multi-select. Adopt IMO categories verbatim. Combined with M-SCAT type-of-event codes for trend analytics.

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

### 2B.6 [Diff #5] Investigation Workflow with Loop-Back Gate

DNV 8-phase workflow becomes the canonical incident lifecycle (replaces linear Draft → In Progress → Review):

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

### 2B.8 [Diff #7] 5-Source Evidence Workspace

Tabbed UI inside the investigation. Each tab has a checklist + evidence matrix.

| Tab | Captures | Required artefacts |
|-----|----------|-------------------|
| **Position** | Where things were | Lat/lon (auto from VDR if available), photos (long/medium/short range from 4 angles), sketches, deck-plan overlay |
| **People** | Who saw / did | Witness list, interview links (see §2B.9), qualifications & fitness at time of event |
| **Parts** | Physical objects | Damaged equipment ID, samples, wear/tear notes, previous-damage history (auto-pull from PMS) |
| **Paper** | Documents | SMS procedure ref, voyage plan, log entries, work permits, training records, certs |
| **Electronic** | Digital traces | VDR / ECDIS / GPS / UMS / VTS / fire-system / CCTV / email / AIS extracts |

**Evidence Matrix** (separate sub-tool inside each finding): `Finding | Pro evidence | Con evidence | Source | Comments` — enforces that contradicting evidence be logged (confirmation-bias guard).

**Perishable evidence prompt:** if a YELLOW or RED incident's Phase 3 has no entries in *People* or *Electronic* within 24 hours of submission, the system pings the lead investigator (perishable-evidence reminder).

### 2B.9 [Diff #8] Structured Interview Module

Replaces free-text interview notes. Each interview is its own record under the People tab.

**4-phase form:**
1. **Make Acquaintance** — checkbox + room/location field
2. **Introduction** — script template + recording-consent toggle
3. **The Meeting** — Q&A field array (each row = question + answer)
4. **Conclusion** — close-out notes + follow-up needed (Y/N)

**Question-type guidance:** each question has a `type` dropdown — *Open / Closed / Analysing / Clarifying / Probing*. Two types are flagged on entry: *Leading* and *Biased* — soft warning ("This phrasing may bias the witness — consider rephrasing as: '<unbiased version>'"). Keyword check looks for: "isn't it", "shouldn't you", "could that", "how could that", "wouldn't it".

**Behaviour self-audit (optional):** post-interview checklist — body language / tone / note-taking / word choice (open vs closed self-rating).

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
| 1 | **Recency** | All 5 evidence categories must have ≥1 entry OR explicit "n/a — justified" | Phase 4 → 5 |
| 2 | **Assumption** | Every fact box requires an evidence link (interview ID / document ID / photo ID) | Adding a fact |
| 3 | **Hindsight** | Decision/action records timestamped; cannot reference info dated after the event | Adding a finding |
| 4 | **Confirmation** | Evidence Matrix requires ≥1 *Con* row for each "major finding" (DPA-flagged) | Phase 5 → 6 |
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

> **Status:** Spec partially locked. Investigation framework adopted from §2B (DNV M-SCAT). RBAC (Q47) and edge-case validation (Round 15) outstanding.

### 3.1 Scope & Definitions
- **Incident:** any event whose outcome crosses the loss threshold (injury · damage · environmental release · reputational impact). Per DNV Loss Causation Model (§2B.1) — same chain as a near miss, only the threshold differs.
- **Severity classification:** computed from Type-of-Loss (§2B.4) × probability → Risk Band (RED/YELLOW/GREEN per §2B.3) → drives investigator level and deadline.
- **Incident Type picklist:** IMO 11 reportable types (§2B.5).
- **Regulatory anchors:**
  - ISM Code Ch.9 (incident reporting, investigation, corrective action)
  - IMO Casualty Investigation Code (Resolution A.1075(28)) — 5 principles in §2B
  - IMO Resolution A.884(21) — 7 human-element domains (§2B.10)
  - IMO MSC-MEPC.3/Circ.4 — mandatory reporting fields (auto-export per §2B.13)
  - MLC 2006 — work/rest hours linkage when fatigue is a finding
  - Flag-state casualty reporting — manual outside VIMS; "Flag State Informed?" toggle on form (decision Q44)

### 3.2 Workflow
Per §2B.6 — DNV 8-phase workflow with explicit Phase-5 → Phase-3 loop-back gate. State machine permits in-place re-opening without losing partial data. Audit log records every loop-back with reason.

State summary (replaces the prior linear "Draft → In Progress → Pending Review → Submitted to PIC → Closed"):

```
Phase 1 Scene Control      → Phase 2 Resources Allocated
                          → Phase 3 Evidence Collection ──┐
                          → Phase 4 Facts Systemized   ◄──┤ (loop-back)
                          → Phase 5 Causes Analysed    ◄──┘
                          → Phase 6 Findings Submitted
                          → Phase 7 DPA Accepted / Report Issued
                          → Phase 8 Follow-up / Effectiveness Verified → CLOSED
```

Rework remains possible at Phase 6 → Phase 3 (DPA-requested rework — replaces the legacy "rework at any stage" pattern).

### 3.3 Data Model
Core tables (DNV-aligned):
- `safety_incident` — the master record (1 row per incident; status = current Phase 1–8)
- `safety_incident_phase_log` — append-only state-change audit (every phase transition + every loop-back with reason)
- `safety_evidence` — child of incident, FK to one of 5 categories (Position/People/Parts/Paper/Electronic) per §2B.8
- `safety_evidence_matrix` — Pro/Con rows per major finding (confirmation-bias guard)
- `safety_interview` — child of evidence/People; structured 4-phase form per §2B.9
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
- `safety_incident_type` (11 rows per §2B.5)
- `safety_event_type` (M-SCAT type-of-event codes)
- `safety_recommendation_theme` (7 themes per §2B.7)
- `safety_case_study` (seeded with Navigator + Sinkfast per §2B.15)

### 3.4 Roles & Permissions (locked 2026-04-16, Round 13 Q47 + Q48)

Risk-tiered investigation/closure chain (user-locked, diverges from initial DNV proposal):

| Band | Investigator | Closer |
|------|--------------|--------|
| **GREEN** | Master | **PIC (Vessel Supt)** |
| **YELLOW** | Master + PIC (joint) | **DPA** |
| **RED** | DPA + External expert | **Fleet Manager** |

**Creation:** Top-4 officers (Master, CO, CE, 2E) create incidents. **Any rank** creates near misses (Q48.4 — reporting-culture best practice).

**SSQE:** folded into DPA role (no separate permission set) — Q47.2 Option A.

**Fleet Manager baseline:** read + flag + comment (comment kept **outside formal investigation record** to keep ISM audit trail pure — Q47.3 Option C). FM gains elevated authority only for **RED closure** and **RED-band blame-fixation override**.

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

> **Status:** Spec partially locked. Uses lightweight version of §2B framework.

### 4.1 Scope & Definitions
A **near miss** is the incident chain (§2B.1) where the outcome did **not** cross the loss threshold. Same M-SCAT taxonomy, same evidence concepts, but lighter capture and shorter workflow. Observations are folded into Near Miss (decision prior).

### 4.2 Workflow
Per Round 12 decision, the lifecycle remains:

```
Open → Submitted (HOD chain) → Rework ↔ Resubmitted → Accepted → Closed
```

Structurally equivalent to a GREEN-band incident: Master leads, 30-day default closure, no Phase-7 DPA acceptance required (PIC accepts).

### 4.3 Data Model
Reuses the incident schema with a `record_type` discriminator on `safety_incident` (`type IN ('incident','near_miss')`) — same tables, near-miss-specific fields nullable for incidents and vice versa. Cause picker uses the **same** M-SCAT lookup tables (§2B.2).

Near-miss-specific:
- No Phase-7 DPA acceptance requirement (PIC closes)
- No mandatory 5-tool analysis — Fact Tree alone is sufficient
- No 7-domain IMO A.884(21) checklist — SHELL tag only (per §2B.10)
- No formal CA/PA — Lessons Learned + Immediate Action only (System Action optional)
- No physical verification mandatory

### 4.4 Anonymity & Reporting Culture
- Submission is **named** by default (CrewId tracked) — anonymous submission deferred to V2
- No-blame policy enforced via bias-fixation guard #5 (§2B.12) — investigations stopping at "individual error" without a Lack-of-Control entry are blocked
- Guidance library (decision prior) — admin-configurable pick-and-choose prompts per incident type — surfaces during creation to lower friction

### 4.5 Trend Analysis & KPIs
- Per-vessel near-miss target tracked monthly (legacy KPI continues)
- Heinrich Ratio panel (§2B.14) is the primary near-miss-vs-incident health indicator
- Repeat root-cause radar (3+ in 6 months = systemic) — decision prior — uses M-SCAT basic-cause codes for matching

---

## 5. Safety Committee Meeting Minutes

> **Status:** Research Pending
> _This section will be populated through interrogation_

### 5.1 Scope & Frequency
<!-- Monthly meetings as per ISM Code, attendees, agenda structure -->

### 5.2 Workflow
<!-- Agenda creation → meeting → minutes capture → action items → follow-up -->

### 5.3 Data Model
<!-- Fields, tables, relationships -->

### 5.4 Action Item Tracking
<!-- Assignment, deadlines, status tracking, overdue alerts -->

### 5.5 Shore-Side Visibility
<!-- DPA review, fleet-wide action item dashboard -->

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
| D-RBAC-06 | CO and Master can host either Regular or Ad-Hoc SCM; user selects `meeting_type` at creation; Master remains final sign-off authority | 2026-04-16; revised 2026-05-18 | Operational update: both senior shipboard roles may host either SCM type while preserving Master closure/sign-off accountability |
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
| D-EDGE-02 | Non-crew injuries captured via "External Party" picklist (Pilot/Shipyard/Stevedore/Contractor/Passenger/Port Agent/Other) + free-text name/company | 2026-04-16 | Q49.2 — covers legacy pattern of pilot/shipyard/stevedore injuries |
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
| D-PDF-01 | Internal incident PDF = formal company report template (cover + executive summary auto-from Lessons Learned + full sections + signature block Master/DPA/[FM for RED] + page numbering + confidentiality header/footer) | 2026-04-16 | Q50.1 Option B — DPA filing / management review / flag-state hand-off |
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
| D-GAP-J1 | **Near-miss reporter identity hidden from Master and HOD** on the incident screen and in PDFs. Visible only to DPA and FM (and reporter themselves). System stores the name; UI masks it outside the DPA/FM view. Reporting-culture-protective | 2026-04-17 | Session 5 Round 19 Cluster J — resolves fear-of-retaliation concern without losing audit trail |
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
| D-GAP-M20 | **SCM hard-block on overdue SOI** = block Master's SIGN-OFF only (not meeting creation / running). Meeting happens; the compliance artefact cannot be signed until the overdue area(s) cleared | 2026-04-17 | Session 5 Round 20 — preserves regulatory force without preventing discussion |
| D-GAP-M21 | **Master rejection of SO's `pending_closure`:** mandatory written reason; finding returns to "Open" state; reason appended to finding notes | 2026-04-17 | Session 5 Round 20 — audit trail for ISM/class |
| D-GAP-M22 | **Closed-Since-Last-SCM snapshot cutoff = prior SCM's CLOSURE timestamp** (Master sign-off moment). Unambiguous through reschedules and Ad-Hoc meetings | 2026-04-17 | Session 5 Round 20 — crisp temporal anchor |
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
| D-GAP-M38 | **Near-miss submission controls: rate-limit + minimum-detail combined.** Max 5 near-miss submissions per crew member per 24 hours; each submission requires description ≥ 100 characters + severity selected | 2026-04-17 | Session 5 Round 20 — light friction against spam, preserves honest reporting |
| D-GAP-DESIGN-01 | **Dashboard metric rename: "Inspection Compliance %" (on Safety dashboard) is renamed to "SOI Compliance %"** to avoid clash with the existing PSC Inspection-module metric of the same name. Applies to all UI labels and exports | 2026-04-17 | Session 5 Round 20 — DESIGN clarity; no name collision across modules |
| D-GAP-R01 | **Causal-layer tagging on top of M-SCAT (ABS scaffolding).** Every cause entered on an incident must also be tagged as Immediate / Intermediate / Root. Investigator cannot close Phase 5 with Immediate-only codes — at least one Root-level cause required. Extends D-DNV-01 | 2026-04-17 | Session 5 Round 21 — ABS Guidance Notes 2005 §6 + RightShip 2023; prevents premature closure at intermediate level |
| D-GAP-R02 | **ALARP cost-benefit gate on System-Action recommendations.** Each System Action (per D-DNV-06 tier 3) must include: estimated effort, estimated likelihood reduction, residual-risk acceptability statement. Mandatory for RED and YELLOW bands; optional-but-prompted for GREEN | 2026-04-17 | Session 5 Round 21 — VMTC-RAII (Veritas) + IMO/ISM baseline; adds regulatory defensibility |
| D-GAP-R03 | **Multiple root causes per incident is the default.** Investigator must identify ≥1 root cause; where multiple causal paths are credible, each must be coded separately against M-SCAT. Monocausal conclusion requires a written justification in closure note. Guidance on D-DNV-01 | 2026-04-17 | Session 5 Round 21 — ABS §6.1 (Multiple Coding Approach); prevents premature closure |
| D-GAP-R04 | **Chain-of-Custody tab added to D-DNV-07 Evidence Workspace.** Every physical evidence item captured: description, collection date/time, collector name + signature, storage location (sealed-bag ID if applicable), witness signature, handover log (who-got-it-when) until closed. Extends D-DNV-07 | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.5 + Nautical Institute 2019 guidelines; legal-discovery defensibility |
| D-GAP-R05 | **Marine document inventory auto-checklist** embedded in D-DNV-07 Paper evidence tab. Pre-populated list: Deck Log (rough + smooth), Engine Log, Radio Log, ECDIS track, AIS record (shore-requested), VDR data, Noon/Bunker records, ISM certificates, Stability booklet, Class certificates, Maintenance records. Each item tick = captured-with-timestamp. Cargo incidents load additional overlay per D-GAP-R10 | 2026-04-17 | Session 5 Round 21 — Nautical Institute 2019 List 1; prevents evidence loss |
| D-GAP-R06 | **Evidence-preservation deadline task list auto-generated on incident creation.** System creates scheduled prompts: VDR capture within 12h (RED hard alarm), ECDIS track snapshot within 24h, AIS shore-request within 24h, photo walk-around within 48h, full formal statements within 7 days. Overdue items surface on incident dashboard | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.2; VDR overwrites every 12h on standard units |
| D-GAP-R07 | **First-hour scene-protection checklist** (Master / CO responsibility) shown as the opening block of a new incident record: freeze/mark alarm logs · note extent of damage (initial assessment) · secure scene (no repairs / movements) · photograph + sketch before detailed examination · record witnesses present. Tick-completed before Phase 1 Submit | 2026-04-17 | Session 5 Round 21 — KAIZEN §11.4.2–3; evidence integrity |
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
