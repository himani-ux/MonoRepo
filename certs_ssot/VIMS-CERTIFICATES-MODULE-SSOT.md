# VIMS Certificates Module — Single Source of Truth (SSOT)

> **Module Status:** **INTERROGATION COMPLETE 2026-05-07** — All 7 rounds done · **199 decisions LOCKED** (D-CERT-001 → D-CERT-199) · KLOSS Step 2 DONE · Module ready for KLOSS Step 3 (DocSuite generation)
> **Owner:** Prince (Maritime PO) · **Methodology:** KLOSS Framework (Step 2 — Interrogation, paused)
> **Sister Modules:** Reporting (DocSuite COMPLETE 2026-04-06) · Safety (DocSuite COMPLETE 2026-04-17) · PMS · Purchase · WRH · Inspection
> **Project Path:** `/Users/prince/Documents/Project reserch/`
> **Resume Point (Next Session):** **KLOSS Step 3 — DocSuite generation.** Same pattern as VIMS-Safety-Module DocSuite (11 canonical docs + COVERAGE.md). Convert SSOT's 198 decisions into a build-ready spec set: PRD, DataModel, APIs, AppFlow, BackendStructure, FrontendGuidelines, ValidationRules, DesignSystem, ImplementationPlan, TestPlan, AuditChecklist. Audit each generated doc against SSOT for 100% decision coverage.

---

## §0 Document Control

| Field | Value |
|---|---|
| Document | VIMS-CERTIFICATES-MODULE-SSOT.md |
| Version | 0.2 (Round 1 + Round 2 + Round 3 Batches 1–2 LOCKED) |
| Date | 2026-05-06 (paused EOD) |
| Status | INTERROGATION IN PROGRESS — Round 3 Batch 3/5 starts tomorrow |
| Decisions Locked | **80** (D-CERT-001 → D-CERT-080) |
| Predecessor Forms | `Certificates/SQE S 633 Certificates and Surveys.xlsx` · `Certificates/TEC-04B Report on Certificate Status.xlsx` |
| Class Reference Reports | 6 PDFs (one per fleet vessel, 6th May 2026 snapshot) — NK / KR / BV |
| Replaces | Manual Excel-based cert tracking + email-distributed registers |

---

## §1 Scope

### §1.1 In Scope (V1)

| Category | Description | Source Forms |
|---|---|---|
| **Class Certificates** | COC, Cargo Gear (CG2), Loading Instrument (LI), Class Notations + Class surveys (Special, Intermediate, Annual, Docking, Boiler, Prop Shaft) as children | NEW (gap in existing forms) |
| **Statutory & Flag** | CSS Construction/Equipment/Radio, ILL, IOPP, ISPP, IAPP/EIAPP, IEEC, BWM, IMSBC, IHM/IHM-EU, ISM SMC, ISPS SSC, MLC, DMLC I/II, Safe Manning, CSR | S 633 §3-§7, TEC-04B A.2/A.3/A.4 |
| **Trade & Commercial** | P&I, H&M, Bunker Convention, Wreck Removal, ITF Bluecard, Civil Liability, Tonnage Tax | TEC-04B A.6, S 633 commercial section |
| **Equipment — LSA / FFA / Nav / GMDSS** | Lifeboats, davits, liferafts, SCBA/ELSA/EEBD, fixed FFA (CO2/foam/water-mist/DCP/galley), portable extinguishers, pyrotechnics, immersion suits | TEC-04B B.1–B.6 |
| **Calibrations** | Multigas detectors, fixed gas detection, OWS/15ppm OCM, pressure / temp calibrators, alcohol meter, BWTS TRO, torque wrench, dynamometer | TEC-04B C.6 |
| **Tests & Analyses** | Fresh water, bunker line pressure (12-mth + 2.5-yr), ballast discharge, noise survey | TEC-04B C.7 |
| **Type Approvals** | OWS, STP, BWTS, Incinerator, LSA aids, SCBA/ELSA/EEBD | TEC-04B C.4 + S 633 distributed |
| **Approved Plans** | SOPEP / SMPEP / PCSOPEP / VRP / NTVRP / California VRP / Coating Tech File / Stability Booklet / Ship Structure Access Manual / Emergency Towing Booklet | TEC-04B C.9 |
| **Other / Misc** | Flag dispensations, ITF blue cert, SCAC code, US CBP customs bond, Japanese customs approvals, ECO Notation, EU MRV, DCS SoC | TEC-04B C.1–C.4 |

**Volume estimate:** ~340 catalog items × 6 vessels = **~2,040 TrackedItem records at go-live**.

### §1.2 Out of Scope (V1)

| Item | Reason | Future home |
|---|---|---|
| Crew certificates (COC competency, COP, GMDSS, medicals, STCW endorsements, vaccinations) | Crewing module | Separate VIMS Crewing Module |
| CMS items (Continuous Machinery Survey ~80–90 items per vessel) | PMS-aligned data | VIMS PMS Module — cross-link only |
| ~~Class portal API integration (BV MOVE, KR e-Fleet, NK NK-SHIPS)~~ — **REMOVED FROM ROADMAP entirely per D-CERT-169 (2026-05-07)** | — | OUT OF SCOPE (not V1, V2, or any future version) |
| Email-watcher for class snapshots | Mailbox infra | V1.1 (after parsers stable) |
| SMS / WhatsApp / Push notifications | Channel infra | V1.1 |
| Vessel offline-write capability | Cert work happens at port (online) | Likely never — read-only cached view sufficient |

### §1.3 Pain Points Driving the Build

| # | Gap | V1 mitigation |
|---|---|---|
| 1 | Excel registers **not timely updated** | Mandatory write-on-issue; Master submission + approval workflow; office direct write; class snapshot reconciliation auto-flags drift |
| 2 | Surveys/services **missed** because windows invisible in current Excel | Window dates parsed from class status; per-survey alerts (window-open / window-closing / overdue) visible to Master + Office |
| 3 | **Duplicate registers** — Master / Tech / Marine / FM each maintain own copy via email | Office-controlled fleet master catalog (D-CERT-004); single canonical TrackedItem store; Excel templates retired (S 633 layout retained as **print-only output**) |

---

## §2 Source Materials Analyzed

### §2.1 KSM Internal Forms

| File | Lines/Items | Role | Disposition |
|---|---|---|---|
| `Certificates/SQE S 633 Certificates and Surveys.xlsx` | 1026 rows / ~340 items | Master register — KSM legacy template | **Retained as print-only export layout** (D-CERT-002) |
| `Certificates/TEC-04B Report on Certificate Status.xlsx` | 3 sheets, 343 rows total | Status report doubling as folder index (file refs 1MA_01, 1MA_02). Hierarchical A/B/C taxonomy. | **Reference inspiration only** — internal taxonomy is free design (D-CERT-003) |

### §2.2 Class Status Reports (6th May 2026 snapshot)

| Vessel | Class Society | Format | Pages | Distinguishing features |
|---|---|---|---|---|
| YC FORTITUDE | **BV** (Bureau Veritas) | "MOVE Fleet in Service Survey Status" | ~14 | ToC-driven, narrative; Conditions of Class section + 1-Year Survey Planner + Continuous Survey List |
| SF CHALISA | **KR** (Korean Register) | "Vessel Status for Ship's Owner" | 19 | Two-table cert layout (Class + Statutory); code abbreviations (SC/SE/SR/IOPP-A); `Type ∈ Full/Permanence/Conditional`; UTN unique tracking number; e-Fleet portal `https://e-Fleet.krs.co.kr` |
| SF DARIKA | **KR** | Same as Chalisa | 19 | Includes VGP (US-trading) |
| EAST AYUTTHAYA | **KR** | Same | 19 | Includes USCG cert + VGP |
| EAST BANGKOK | **NK** (ClassNK / Nippon Kaiji Kyokai) | "NK-SHIPS Survey and/or Audit Status" | 38 | Most granular surveys; explicit `Range Date` (window) + `Extended` + `Postponed` columns; abbreviated names (Load Line, Safety Construction, OPP, SPP, APP) |
| SFYC ARAYA | **NK** | Same as Bangkok | 30 | Includes EIAPP + Grain Loading + IHM separately |

**Fleet–class distribution:** BV 1 · KR 3 · NK 2 · Total 6.

### §2.3 Cross-References

| File | Relevance |
|---|---|
| `INDEX.md` | Master research index — Certificates entry to be appended |
| `VIMS-SAFETY-MODULE-SSOT.md` | Sister module — share auth, JWT, master_notification, RBAC patterns |
| `VIMS-REPORTING-MODULE-SSOT.md` | Sister module — share tech stack version locks |
| `ssot_auth_specific.md` | Canonical auth — JWT payload, msc_profiles, form_ids/process_ids |
| `VIMS DOCS/CAR_Database_Schema_v4.sql` | Inspection PSC pattern — approval workflow shape (D-CERT-018) |

---

## §3 Module Architecture

### §3.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                  VIMS Certificates Module                    │
│                                                              │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Catalog Mgmt   │  │ Cert Tracking    │  │ Class Status │ │
│  │ (office only)  │  │ (per vessel)     │  │ Reconciler   │ │
│  └────────┬───────┘  └─────────┬────────┘  └──────┬───────┘ │
│           │                    │                  │          │
│           └────────────┬───────┴──────────────────┘          │
│                        │                                     │
│           ┌────────────▼─────────────┐                       │
│           │     TrackedItem Store    │                       │
│           │     + PDF Blob Store     │                       │
│           │     + Audit Trail        │                       │
│           └────────────┬─────────────┘                       │
│                        │                                     │
│       ┌────────────────┼─────────────────┐                   │
│       ▼                ▼                 ▼                   │
│  ┌──────────┐   ┌────────────┐    ┌─────────────┐           │
│  │ Alert    │   │ Print/PDF  │    │ Fleet       │           │
│  │ Engine   │   │ Export     │    │ Dashboard   │           │
│  └──────────┘   └────────────┘    └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
        │                                       │
        ▼                                       ▼
   master_notification                     Cross-module links
   (in-app + email V1)                     (PMS / Safety / Reporting)
```

### §3.2 Boundary Definitions

- **Catalog** (fleet-wide) ≠ **TrackedItem instances** (per vessel). Catalog defines what types of certs exist; instances are vessel-specific records.
- **Class Status Snapshot** is a separate immutable artifact (PDF + parsed JSON), kept indefinitely. TrackedItems reference the snapshot via `last_class_sync_id`.
- **PDF blob storage** is separate from TrackedItem — items hold blob references, not blobs.

---

## §4 Canonical Catalog Structure (D-CERT-017)

### §4.1 Top-Level Sections (9)

| # | Section | Approx items | `is_class_tracked` default | Notes |
|---|---|---|---|---|
| 1 | **Class Certificates** | ~5 + class surveys | ✓ true | NEW. COC + CG2 + LI + Class Notations + 6 class surveys |
| 2 | **Statutory & Flag** | ~50 | ✓ true (mostly) | CSS, ILL, IOPP, ISPP, IAPP, BWM, MLC, ISM, ISPS, IMSBC, IHM, etc. |
| 3 | **Trade & Commercial** | ~12 | ✗ false | P&I, H&M, Bluecard, Civil Liability, Bunker Convention |
| 4 | **Equipment — LSA/FFA/Nav/GMDSS** | ~140 | ✗ false | Former TEC-04B B.1–B.6 |
| 5 | **Calibrations** | ~12 | ✗ false | Gas detectors, OWS/15ppm, pressure/temp, alcohol meter, BWTS TRO, torque, dynamometer |
| 6 | **Tests & Analyses** | ~8 | ✗ false | Fresh water, bunker line pressure, ballast, noise |
| 7 | **Type Approvals** | ~10 | ✗ false | OWS, STP, BWTS, Incinerator + LSA + SCBA |
| 8 | **Approved Plans** | ~12 | ✗ false | SOPEP, SMPEP, VRP, Stability Booklet, Coating Tech File |
| 9 | **Other / Misc** | ~10 | ✗ false | Flag dispensations, customs bonds, ECO Notation, MRV, DCS SoC |

**Total catalog items:** ~340.

### §4.2 Catalog Row Schema (Template)

```yaml
catalog_row:
  catalog_code:        # canonical fleet-wide code, e.g., "STAT-IOPP-A"
  section_id:          # 1..9 from §4.1
  display_name:        # human-readable, e.g., "International Oil Pollution Prevention Certificate (Form A)"
  short_name:          # e.g., "IOPP"
  type:                # certificate | endorsement_survey | service | calibration | test | type_approval | plan_approval
  cadence:             # permanent | annual | intermediate | 5_year | 6_month | 3_month | custom_days(N)
  is_class_tracked:    # bool — appears on NK/KR/BV class status report
  default_owner:       # office | vessel — hint, not enforcement (per Q3 b model)
  parent_catalog_code: # nullable — for survey/STC/extension nesting
  required_for_vessel_types: # bulk_carrier | tanker | container | all (filters which vessels get this row)
  alert_lead_overrides:    # nullable — override default §6 lead times for this row
  print_section_label:     # mapping back to SQE S 633 section for export
  regulatory_anchor:       # e.g., "MARPOL Annex I Reg 7 / SOLAS II-1"
  audit fields (created_by, modified_by, etc.)
```

---

## §5 Data Model — TrackedItem (D-CERT-010 → D-CERT-013)

### §5.1 Core Schema

```yaml
TrackedItem:
  id:                       # UUID
  vessel_id:                # FK to vessel (6 fleet vessels)
  catalog_code:             # FK to catalog row in §4.2

  type:                     # certificate | endorsement_survey | service | calibration |
                            # test | type_approval | plan_approval
  validity_type:            # full | conditional | short_term | permanent
  cadence:                  # permanent | annual | intermediate | 5_year | 6_month |
                            # 3_month | custom_days(N)

  # Relationships (D-CERT-010, D-CERT-013)
  parent_id:                # nullable, self-FK; arbitrary depth in schema, 2-level cap in UI V1
  relationship_type:        # nullable enum (when parent_id set):
                            #   survey_of           — endorsement survey under parent cert
                            #   short_term_for      — STC bridging to parent
                            #   extension_of        — class extension granted on parent
                            #   dispensation_for    — flag dispensation granted on parent
  supersedes_id:            # nullable — when full cert replaces an STC

  # Date fields (D-CERT-011)
  issue_date:               # date issued
  expiry_date:              # nullable for permanent
  anniversary_date:         # anchor for annual/intermediate cycles
  window_open:              # survey window start (parsed from class snapshot)
  window_close:             # survey window end
  last_done_date:           # last execution of this survey/service
  next_due_date:            # computed: anniversary + cadence
  postponed_until:          # nullable — class-granted postponement

  # Status (computed)
  status:                   # ok | window_opening | window_open | window_closing |
                            # overdue | done | postponed | superseded | n/a (permanent)

  # Cert identity
  certificate_number:       # cert number from issuer
  issuing_authority:        # "DNV" | "KR" | "NK" | "BV" | "Panama Flag" | etc.
  place_of_issue:

  # Extension fields (D-CERT-013)
  extension_authority:      # nullable: class | flag | n/a
  extension_letter_pdf_id:  # nullable FK to PDF blob
  extension_reason:         # nullable short text

  # PDF + sync
  pdf_attachment_id:        # current active PDF
  source:                   # manual | class_snapshot | migration
  last_class_sync_id:       # FK to ClassStatusSnapshot

  # Approval workflow (D-CERT-018)
  approval_state:           # draft | pending_master_approval | approved | rejected
  submitted_by:             # user_id
  submitted_at:
  approved_by:              # user_id (Master if onboard submission, n/a if office direct)
  approved_at:

  # Audit
  created_at, created_by, modified_at, modified_by, version
```

### §5.2 PDF Blob Schema

```yaml
PdfBlob:
  id:
  tracked_item_id:          # FK
  blob_storage_path:        # S3-compatible
  filename:                 # original upload name
  uploaded_by, uploaded_at:
  is_active:                # bool — false once superseded
  superseded_at:            # nullable
  retention_policy:         # immediate_delete_on_supersede (Class+Statutory)
                            # | retain_18_months_then_purge (all others)
                            # (D-CERT-021)
  scheduled_delete_at:      # nullable; computed for retain_18_months
```

### §5.3 ClassStatusSnapshot Schema

```yaml
ClassStatusSnapshot:
  id:
  vessel_id:
  class_society:            # NK | KR | BV
  pdf_blob_id:              # original uploaded PDF (kept indefinitely)
  printed_on_date:          # extracted from PDF cover
  uploaded_by, uploaded_at:
  parser_version:           # for tracking parser changes
  parse_status:             # success | partial | failed
  parsed_payload_json:      # extracted structured data
  reconciliation_run_id:    # FK to reconciliation run record
```

### §5.4 ReconciliationRun Schema

```yaml
ReconciliationRun:
  id:
  snapshot_id:              # FK
  ran_at:
  matches_count:            # cert in catalog AND class status, all dates equal
  mismatches_count:         # cert in both, dates differ
  missing_in_catalog_count: # on class status, not in catalog (catalog gap)
  missing_in_class_count:   # in catalog, not on class status (expected for non-class-tracked)
  flags:                    # JSON array of per-row issues
  notifications_sent:       # JSON array of (recipient, channel, sent_at)
```

---

## §6 Alert & Notification Engine (D-CERT-016)

### §6.1 Trigger Matrix (V1)

| Trigger | Default Lead | Recipients | DPA-configurable |
|---|---|---|---|
| Window opening soon | 30 days before `window_open` | Master + Office (Tech Sup'tt) | ✓ lead time |
| Window open — entered | At `window_open` | Master + Office | — |
| Window closing soon | 30 days before `window_close` | Master + Office + DPA | ✓ lead time |
| Window overdue | 1 day after `window_close` | Master + Office + DPA + FM | — |
| Cert expiring (ladder) | 90 / 60 / 30 / 7 days before `expiry_date` | Master + Office | ✓ ladder values |
| Cert expired | At `expiry_date + 1` | Master + Office + DPA + FM | — |
| Conditional / STC closing | 14 days before `expiry_date` of STC | Master + Office + DPA | ✓ lead |
| Class snapshot stale | 60 days after last upload (= 1 month before next 3-monthly upload) | Office (DPA + Tech Sup'tt) | ✓ N + lead |
| Class snapshot refresh suggested | Immediate, after `is_class_tracked: true` row updated | Office (DPA + Tech Sup'tt) | — |
| Reconciliation mismatch found | At reconciliation completion | Master (primary) + Office | — |

### §6.2 Channels (V1) — Updated 2026-05-07 per D-CERT-151 + D-CERT-161

**Per-side routing (D-CERT-161):**

| Audience | In-app | Email | Slack |
|---|---|---|---|
| **Vessel-side** (Master, C/O, C/E, 2/E) | ✓ | ✓ | ✗ |
| **Office-side** (DPA, FM, Marine Sup'tt, Technical Manager, Tech Sup'tt) | ✓ | ✗ | ✓ |

**Channel availability roadmap:**

| Channel | V1 | V1.1 | V2 |
|---|---|---|---|
| In-app dashboard banner (shared `master_notification`) | ✓ | | |
| Email (HTML+plain-text multipart, magic-link ack) — *vessel-side only* | ✓ | | |
| Slack (per-vessel + fleet-wide channels) — *office-side only, elevated from V2* | ✓ | | |
| SMS / WhatsApp | | ✓ | |
| Push notification (mobile companion app) | | ✓ | |
| External webhook (Teams + others) | | | ✓ |

### §6.3 Survey Window Visibility (D-CERT-016 special)

Per Q6: surveys are arranged by office. Window-open / window-closing / overdue alerts are **visible to BOTH** Master AND Office regardless of who initiates the survey. Master cannot disable office's view; office cannot disable Master's view.

---

## §7 Class Status Reconciliation (D-CERT-005 → D-CERT-009)

### §7.1 Upload Cadence

- **Time-based:** Every **3 months** per vessel. **DPA-configurable** in Settings.
- **Lead alert:** **1 month** before next upload due. DPA-configurable.
- **Event-based:** When any `is_class_tracked: true` TrackedItem is updated by Master or Office, a "Class snapshot refresh suggested" flag is raised on the office dashboard for that vessel. **Grace = 14 days**, then escalates. Auto-clears on next snapshot upload.

### §7.2 Per-Class Parser Strategy

Three independent parser modules. Each ingests the class PDF, normalizes to a common intermediate schema, then maps to canonical `catalog_code`.

| Class | Parser key fields | Mapping table |
|---|---|---|
| **KR** | Class Cert table (Code: CC/CG2/LI), Statutory Cert table (Code: SC/SE/SR/ILL/IOPP-A/ISPP/IGPP/IAPP/IAFS/BWM/IMSBC/CDG/IIHM/IHM(EU)/IEE/USCG/VGP), `Type ∈ {Full, Permanence, Conditional}`, Issue/Expiry/UTN/Exemption | `(KR, code) → catalog_code` |
| **NK** | "Current Statutory Certificates" (name-based: Load Line, Safety Construction, Safety Equipment, Safety Radio, OPP, SPP, APP, EE, AFS, BWM, IHM, IMSBC, etc.), "Survey Status: Class" with Range Date, "Survey Status: Statutory" with Renewal/Intermediate/Annual rows | `(NK, name_normalized) → catalog_code` |
| **BV** | "Conditions of Class / Statutory / ISM / ISPS / MLC Status" section, "1-Year Survey Planner", "Continuous Survey List" | `(BV, item_label_normalized) → catalog_code` |

### §7.3 Canonical Mapping Table

```yaml
ClassCodeMapping:
  id:
  class_society:    # NK | KR | BV
  class_code_or_name: # raw value from class report
  catalog_code:     # FK to canonical catalog row
  cert_or_survey_kind: # "renewal" | "intermediate" | "annual" | "periodic" | "n/a"
  notes:            # editorial notes
  active:           # bool
```

Maintained by office (DPA + Tech Sup'tt). Initial seed extracted by parser developer from the 6 reference PDFs. Updates over time as class society reformats.

### §7.4 Reconciliation Output

For each vessel post-upload:

| Bucket | Meaning | Action |
|---|---|---|
| Match | Class status row maps to catalog row, all dates equal | None — log only |
| **Mismatch** | Class status row maps to catalog row, dates differ | **Alert Master** to update; class is authoritative; Master uploads new cert PDF + corrects dates |
| Missing in catalog | Class status row has no canonical mapping | **Alert DPA** to extend ClassCodeMapping (or extend catalog itself) |
| Missing in class | Catalog row exists with `is_class_tracked: true` but absent from snapshot | **Alert Office**; could mean cert was withdrawn, or new cert pending issuance |
| Conditional / STC detected | Class shows `Type = Conditional` or short validity window | **Flag to Master**; system pre-fills an STC TrackedItem form (`relationship_type = short_term_for`, linked to parent) — Master confirms + uploads PDF. Consistent with D-CERT-008 (no auto-write). |
| Extended / Postponed detected | Class shows `Extended` or `Postponed` column populated | **Flag to Master**; system pre-fills an extension TrackedItem form (`relationship_type = extension_of`, `extension_authority = class`) — Master confirms + uploads extension letter. |

### §7.5 Source-of-Truth Tie-Breaker

**Class is always authoritative** for `is_class_tracked: true` certs (D-CERT-009). Mismatch resolution always means Master updates catalog to match class.

---

## §8 Cert Lifecycle States (D-CERT-012 → D-CERT-013)

### §8.1 Validity Types

| `validity_type` | Meaning | Issued by | Typical duration | Linked records |
|---|---|---|---|---|
| `full` | Standard cert with full validity | Class or Flag | Cert-specific (5y / 1y / etc.) | — |
| `conditional` | Cert issued with deficiency to clear | Class or Flag | Shorter than full (e.g., 2 months) | May spawn STC if deficiency persists |
| `short_term` | Bridge cert covering gap to next port for full survey | **Class only** (incl. acting as RO for Flag certs) | ~3 months max | `relationship_type = short_term_for` linking to original |
| `permanent` | No expiry (Builder's Cert, IEEC, EIAPP, Class Notations record) | Class / Flag / Builder | Lifetime | — |

### §8.2 Extension Pathways

| Extension origin | Authority | Mechanism | Linked TrackedItem |
|---|---|---|---|
| **Class certs need extension** | Class | Class issues extension letter (max ~3 months typical) | `relationship_type = extension_of`, `extension_authority = class`, `extension_letter_pdf` attached |
| **Statutory certs need extension** | Flag (or Class as RO) | Flag dispensation document required (or Class can extend on Flag's behalf as Recognized Organization) | `relationship_type = dispensation_for`, `extension_authority = flag` (or `class` if RO-extended), `extension_letter_pdf` attached |

### §8.3 STC Workflow Example

```
T0:  IOPP cert due renewal at port X. Surveyor unavailable.
T1:  Class issues STC with 2-month validity (until next port).
     → Spawn TrackedItem:
        - type: certificate
        - validity_type: short_term
        - parent_id: original IOPP TrackedItem
        - relationship_type: short_term_for
        - issue_date: T1, expiry_date: T1+60d
        - pdf_attachment: STC PDF
T2:  Vessel reaches next port. Full survey completed.
     New full IOPP cert issued.
T3:  Master updates IOPP TrackedItem with new dates + new PDF.
     STC TrackedItem set to status: superseded.
     STC's supersedes_id = new full cert's id.
     Audit trail preserved.
```

---

## §9 RBAC & Approval Workflow (D-CERT-018)

### §9.1 Role Matrix

| Role | Catalog mgmt | TrackedItem write | TrackedItem read | Class status upload | Alert config | Fleet view |
|---|---|---|---|---|---|---|
| DPA / Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FM (Fleet Manager) | — | ✓ direct | ✓ all | ✓ | — | ✓ |
| Tech Sup'tt | — | ✓ direct | ✓ all | ✓ | — | ✓ |
| Marine Sup'tt | — | ✓ direct | ✓ all | ✓ | — | ✓ |
| **Master** (onboard) | — | ✓ direct (own vessel) + approver of subordinate submissions | ✓ own vessel | — | — | own vessel |
| **C/O** (Chief Officer) | — | ✓ submit (own vessel) | ✓ own vessel | — | — | own vessel |
| **C/E** (Chief Engineer) | — | ✓ submit (own vessel) | ✓ own vessel | — | — | own vessel |
| **2/E** (Second Engineer) | — | ✓ submit (own vessel) | ✓ own vessel | — | — | own vessel |
| Other onboard officers | — | — | ✓ own vessel | — | — | own vessel |
| Auditor (read-only) | — | — | ✓ all | — | — | ✓ |

### §9.2 Approval Workflow (PSC Inspection Pattern)

Subordinate submissions (C/O, C/E, 2/E) follow the existing **PSC Inspection approval pattern** from `VIMS DOCS/CAR_Database_Schema_v4.sql`:

```
[ C/O / C/E / 2/E creates submission ]
        ↓
   approval_state = pending_master_approval
        ↓
   Master notified (in-app + email)
        ↓
   ┌─────────────────────────────┐
   │ Master reviews submission   │
   └─────────────────────────────┘
        ↓                     ↓
   [Approve]             [Reject + reason]
        ↓                     ↓
   approval_state =      approval_state =
       approved              rejected
        ↓                     ↓
   Live on dashboard     Returned to submitter
   Audit captures          for correction
   submitter + approver    Audit captures rejection
```

- **Master's own writes**: direct, no approval gate (Master IS the approver onboard).
- **Office writes** (DPA / FM / Tech / Marine Sup'tt): direct, no approval gate.
- Audit trail captures both **submitter** and **approver** with timestamps + state transitions.

### §9.3 Catalog Management

- Catalog editable only by **DPA + System Admin** roles.
- Every catalog change (add/deprecate/modify) audit-logged.
- Catalog deprecation does NOT delete TrackedItem instances — instances remain queryable but their catalog row is marked `active = false` (no new instances allowed).

---

## §10 PDF Document Storage & Retention (D-CERT-019 → D-CERT-021)

### §10.1 Storage

- **Backend:** S3-compatible blob storage (matches Reporting + Safety pattern).
- **Versioning:** ON. Every PDF replacement creates a new blob; old blob marked `is_active: false` and `superseded_at = now()`.
- **Encryption:** At-rest (AES-256) + in-transit (TLS 1.3).

### §10.2 Retention Rules

| Category | Active version | Old versions on supersession |
|---|---|---|
| Class Certificates (COC, CG2, LI, Notations) | Always retained | **Deleted immediately** on new upload |
| Statutory & Flag certs | Always retained | **Deleted immediately** on new upload |
| Trade & Commercial / Equipment / Calibrations / Tests / Type Approvals / Approved Plans / Misc | Always retained | Retained **18 months** from supersession, then auto-purged |
| Class Status Snapshots (the uploaded class PDF itself) | Retained **indefinitely** | — |

### §10.3 Audit Always Preserved

Regardless of PDF retention, the audit trail (who uploaded, when, dates entered, approval flow) is **never deleted**. Only the PDF blob is purged.

### §10.4 Deletion Mechanism

- Daily cron job scans `PdfBlob.scheduled_delete_at <= now()` and `is_active = false`.
- Soft-delete first (move to delete-pending bucket, 7-day grace).
- Hard-delete after 7 days (irreversible).
- DPA can extend retention on individual blobs (override).

---

## §11 Print/Export — SQE S 633 Layout (D-CERT-002)

### §11.1 Output Format

- **Per-vessel print summary** in SQE S 633 layout (preserves muscle memory + auditor expectations).
- Generated as **PDF** (primary) + **Excel** (secondary, retains formula compatibility for legacy users).
- Generated **on-demand** by office or Master from the dashboard.

### §11.2 Mapping Catalog → S 633 Layout

Each catalog row carries `print_section_label` referencing the S 633 section. Print engine groups TrackedItem instances by this label, sorts by S 633 row number, renders columns: `No / CERTIFICATE / Issued by / Place of issue / Date of Issue / Expiry date / Days to go / Cadence (Perm. | A | Bi-A | 5-Y | 6-Mth) / Remarks`.

### §11.3 Print Coverage

The print includes ALL catalog instances for the vessel — not just `is_class_tracked`. The `Days to go` column is computed from `expiry_date` (or `next_due_date` for surveys).

---

## §12 Cross-Module Integrations (D-CERT-022)

### §12.1 V1 Cross-Links (Manual cross-reference, no FK)

| From | To | Purpose | Mechanism |
|---|---|---|---|
| Certs UI | PMS | Surface CMS items per vessel; component-equipment cert linkage | URL link with vessel + component_id parameter |
| Certs UI | Safety module | Approved Plans (SOPEP/SMPEP/VRP) referenced from incident response | URL link |
| Certs UI | Reporting module | ISM/ISPS/MLC certs surfaced in inspection contexts | URL link |
| Reporting (MARPOL Annex I) | Certs (IOPP) | IOPP validity check before fuel ROB calc | Read-only API call |
| Inspection (PSC) | Certs | Show all certs at PSC inspection start | Read-only API call |

### §12.2 V2 Hard FK Integrations

Deferred — establishing schema-level FK relationships requires cross-module migration coordination. V1 stays loose-coupled via APIs.

---

## §13 Migration Strategy (D-CERT-020)

### §13.1 Per-Vessel Onboarding Wizard

```
Phase 1 — Catalog seed (office, one-time)
  Office runs catalog seed import:
    - Parse SQE S 633 + TEC-04B → canonical catalog rows
    - Office reviews + approves catalog (manual quality pass)
    - Catalog locks for fleet

Phase 2 — Per-vessel migration (office-led, vessel-by-vessel)
  For each of 6 vessels:
    Step 1: Upload current vessel's S 633 Excel + most recent class status PDF + bulk PDF zip of all current cert files
    Step 2: System pre-populates TrackedItem rows
    Step 3: Class status parser runs; reconciliation report generated
    Step 4: Office reviews mismatches with Master (joint session)
    Step 5: Master uploads any missing PDFs from onboard files
    Step 6: Vessel goes "live" — alerts begin firing

Phase 3 — Cutover
  Excel registers retired (read-only archive kept)
  Email distribution lists discontinued
  Office + vessels operate from VIMS Certs only
```

### §13.2 Time Estimate

| Phase | Effort |
|---|---|
| Catalog seed | 8–12 hours (one-time) |
| Per-vessel migration | 2–4 hours per vessel × 6 = 12–24 hours total |
| Cutover communication + training | 4 hours |

---

## §14 Tech Stack (D-CERT-022)

### §14.1 Inherited from Reporting + Safety (Locked Versions)

| Layer | Component | Version |
|---|---|---|
| Frontend | React | 18.3.1 |
| Frontend | TypeScript | 5.4.5 |
| Frontend | TanStack Query | (per Reporting lock) |
| Frontend | Zustand | (per Reporting lock) |
| Backend | Django | 5.2.7 |
| Backend | DRF | 3.14.0 |
| Database | SQL Server `ksm_cms_live` | (shared) |
| Auth | JWT | (per `ssot_auth_specific.md`) |
| PDF generation | ReportLab | 4.2.0 |
| Notifications | `master_notification` table | (per Safety pattern) |

### §14.2 New for Certs Module

| Component | Purpose | Version target |
|---|---|---|
| `pdfplumber` | Class status PDF text extraction | latest stable |
| `tabula-py` (optional) | Table extraction fallback | latest stable |
| Per-class parser modules | NK / KR / BV format parsers (Python) | own |
| S3-compatible blob client | PDF storage | matches existing Safety pattern |

### §14.3 Database Tables (new prefix `vims_certs_*`)

- `vims_certs_catalog_section`
- `vims_certs_catalog_row`
- `vims_certs_class_code_mapping`
- `vims_certs_tracked_item`
- `vims_certs_pdf_blob`
- `vims_certs_class_status_snapshot`
- `vims_certs_reconciliation_run`
- `vims_certs_reconciliation_flag`
- `vims_certs_audit_log`
- `vims_certs_alert_config`
- `vims_certs_approval_event`

### §14.4 API Surface (DRF)

- `/api/certs/catalog/...` — catalog mgmt (DPA only)
- `/api/certs/tracked-items/...` — TrackedItem CRUD per vessel
- `/api/certs/class-snapshots/...` — upload, list, parse
- `/api/certs/reconciliation/...` — run history, mismatches
- `/api/certs/print/...` — S 633 PDF/Excel export
- `/api/certs/dashboard/...` — fleet rollup
- `/api/certs/alerts/...` — alert config

---

## §15 Module Governance (KLOSS Step 1 → Step 3)

### §15.1 Pipeline (matching Reporting + Safety)

```
Step 1: SSOT (this doc)              ← CURRENT
Step 2: Interrogation                  ← NEXT
   Round 1: Catalog completeness (full 340-item enumeration vs. SQE S 633 + TEC-04B + class reports)
   Round 2: Class parser specifications (test cases per class society, format edge cases)
   Round 3: RBAC + approval workflow precision
   Round 4: Migration mechanics + bulk import format
   Round 5: Print layout fidelity + edge cases
   ... (iterate until decision coverage = 100% GREEN)
Step 3: DocSuite (11 canonical docs in /VIMS-Certificates-Module/)
   PRD.md
   APP_FLOW.md
   TECH_STACK.md
   DESIGN_SYSTEM.md
   FRONTEND_GUIDELINES.md
   BACKEND_STRUCTURE.md
   IMPLEMENTATION_PLAN.md
   VALIDATION_RULES.md
   USER_GUIDE.md
   CLAUDE.md
   LESSONS.md
   COVERAGE.md (decisions audit)
Step 4: Handover (/VIMS-CERTIFICATES-HANDOVER/)
Step 5: Phase 0 build (per IMPLEMENTATION_PLAN.md)
```

---

## §16 Decisions Log (D-CERT-001 → D-CERT-022)

| # | Decision | Driver | Status |
|---|---|---|---|
| D-CERT-001 | V1 scope = vessel certs + surveys; crew COCs out of scope (separate Crewing module) | Q1 confirmation | LOCKED |
| D-CERT-002 | Print/export retains SQE S 633 layout. Internal UI/UX is free design. | Q1 user reply | LOCKED |
| D-CERT-003 | Internal data model + UI taxonomy: free design (TEC-04B = reference inspiration). | Q1 user reply | LOCKED |
| D-CERT-004 | Fleet-wide office-controlled master catalog. Vessels cannot add cert types. Special instructions handled via circulars. | Q2 user reply (option A) | LOCKED |
| D-CERT-005 | Class status reconciliation V1: manual PDF upload + per-class parser (NK / KR / BV). Email/API integration deferred. | Q4 user reply (option A) | LOCKED |
| D-CERT-006 | Class snapshot upload cadence: every 3 months, alert 1 month in advance. DPA-configurable. | Q4a user reply | LOCKED |
| D-CERT-007 | Event-driven class snapshot refresh prompt when any `is_class_tracked: true` row is updated. Grace = 14 days. | User addendum after Q5 | LOCKED |
| D-CERT-008 | Mismatch handling: alert + Master prompted to update. No auto-write. | Q4b user reply | LOCKED |
| D-CERT-009 | Source-of-truth tie-breaker: Class is always authoritative for class-tracked certs. | Q4c user reply (option i) | LOCKED |
| D-CERT-010 | Single `TrackedItem` entity with `type` enum + `parent_id`. Schema: arbitrary depth via `parent_id`. UI: 2-level cap V1. | Q5 / Q5b | LOCKED |
| D-CERT-011 | Rich date fields: issue/expiry/anniversary/window_open/window_close/last_done/next_due/postponed_until. | Q5 user clarification on survey windows | LOCKED |
| D-CERT-012 | Validity types: full / conditional / short_term / permanent. STC modeled as separate row with `relationship_type = short_term_for`. | User STC clarification | LOCKED |
| D-CERT-013 | Extensions: separate row, `relationship_type ∈ {extension_of, dispensation_for}`, `extension_authority ∈ {class, flag}`. | User Flag dispensation vs Class extension distinction | LOCKED |
| D-CERT-014 | New section "Class Certificates" (COC, CG2, LI, Class Notations). Class surveys (Special / Intermediate / Annual / Docking / Boiler / Prop Shaft) as children of COC. | User addendum: COC missing from existing forms | LOCKED |
| D-CERT-015 | CMS items belong to PMS module. Certs cross-links only — no duplication. | User reply confirming CMS in PMS | LOCKED |
| D-CERT-016 | Per-cert alert rules per §6.1: window-open / window-closing / expiring / expired / STC closing / snapshot stale / refresh suggested. Channels V1: in-app + email. SMS/Push V1.1. **Window alerts visible to BOTH Master + Office** (surveys arranged by office). | Q6 user reply | LOCKED |
| D-CERT-017 | Canonical catalog sections (9): Class · Statutory & Flag · Trade & Commercial · Equipment LSA/FFA/Nav/GMDSS · Calibrations · Tests & Analyses · Type Approvals · Approved Plans · Misc. | Q7 default accepted | LOCKED |
| D-CERT-018 | RBAC: Master = onboard admin. C/O + C/E + 2/E = submit-with-Master-approval (PSC pattern). Others onboard = read-only. Office (DPA / FM / Tech / Marine Sup'tt) = direct write, no approval gate. | Q8 user reply | LOCKED |
| D-CERT-019 | PDF blob storage: S3-compatible, AES-256 at rest, TLS 1.3 in transit, versioned. | Q9 default accepted | LOCKED |
| D-CERT-020 | PDF retention: Class + Statutory certs → old deleted immediately on new upload. All other categories → old retained 18 months from supersession, then auto-purged. Class status snapshots → retained indefinitely. Audit trail always preserved. | Q9 user reply | LOCKED |
| D-CERT-021 | Migration: per-vessel onboarding wizard (catalog seed → upload S633 + class PDF + bulk PDFs → review with Master → vessel live). 6 vessels × 2–4h. | Q10 default accepted | LOCKED |
| D-CERT-022 | Tech stack inherited from Reporting + Safety. New tables `vims_certs_*`. Per-class parser in Python. KLOSS pipeline: SSOT → Interrogation → DocSuite → Handover → Phase 0 build. | Q14–Q17 defaults accepted | LOCKED |

### Interrogation Round 1 (Catalog Completeness, 25 questions, 2026-05-06)

| # | Decision | Status |
|---|---|---|
| D-CERT-023 | Catalog v1.0 = union of S 633 + TEC-04B with dedup. Parser dev extracts → DPA + Tech Sup'tt review workshop → locked. | LOCKED |
| D-CERT-024 | Naming: TEC-04B hierarchy → canonical_code structure (parent/child); S 633 names → display_name + print_section_label. | LOCKED |
| D-CERT-025 | "ISM DOC Last Internal Audit" = Certs TrackedItem, office-uploaded (no Inspection module cross-link in V1). Same pattern for ISM External Audit, MLC Audit, ISPS audits. | LOCKED |
| D-CERT-026 | TEC-04B A.1 (Last port clearance, Free Pratique, Lighthouse dues, DG manifest, Fumigation) = OUT of V1 Certs scope. Defer to future Voyage/Port Call module. | LOCKED |
| D-CERT-027 | Tonnage Tax = TrackedItem (Trade & Commercial section). Cadence + anniversary anchor configurable per vessel (flag-by-flag basis). DPA-only edit. | LOCKED |
| D-CERT-028 | Catalog row has `vessel_type: bulk_carrier \| tanker \| container \| all` (multi-select). V1 ships with this functionality. Default = `all`. DPA-editable. | LOCKED |
| D-CERT-029 | Catalog row has `applicability_mode: all_matching_type \| specific_vessel_ids` dropdown. When `specific_vessel_ids`, multi-select vessel picker appears. DPA-editable. | LOCKED |
| D-CERT-030 | Class code mapping seed extracted by parser dev from 6 reference PDFs; validated by DPA + Tech Sup'tt in same workshop as Catalog v1.0. | LOCKED |
| D-CERT-031 | Class format-change recovery: FAIL SOFT. `unmapped_rows[]`; reconciliation continues for mapped rows; DPA notified. NO fuzzy fallback. >25% unmapped → critical escalation. | LOCKED |
| D-CERT-032 | IOPP variant-bearing certs use ONE canonical row + `form_variant: A \| B \| n/a`. Pattern reusable for any future MARPOL Annex variants. | LOCKED |
| D-CERT-033 | `CLASS-BOILER-SURVEY` = Cert child of COC (statutory class survey, NOT CMS). | LOCKED |
| D-CERT-034 | `CLASS-PROP-SHAFT-SURVEY`, `CLASS-DOCKING-SURVEY` = Cert children of COC. `CLASS-IWS-SURVEY` age-gated: vessels ≤15 years only. Auto-disables when age crosses 15. | LOCKED |
| D-CERT-035 | Multi-instance equipment groups (SCBA / CO2 / ELSA-EEBD / Liferaft / Lifeboat pyrotechnics / Multigas detectors): ONE catalog parent + N child TrackedItems per vessel via `parent_supports_dynamic_children: true` flag. | LOCKED |
| D-CERT-036 | Portable extinguishers / lifebuoys / inflatable life jackets = ONE TrackedItem per vessel for annual service. Per-unit detail in service report PDF. NOT individually tracked in Certs V1. | LOCKED |
| D-CERT-037 | Catalog v1.0 row enumeration sourced from union of S 633 + TEC-04B sheets only. NO separate per-vessel physical counting exercise. | LOCKED |
| D-CERT-038 | PSC profile / MoU info OUT of Certs scope. Owned by PSC Inspection module. Class snapshot parser SKIPS this section. | LOCKED |
| D-CERT-039 | CSR Form 1/2/3: ONE TrackedItem (`STAT-CSR`, cadence `permanent`); all amendment PDFs retained indefinitely. Override flag `retain_all_versions: true`. | LOCKED |
| D-CERT-040 | Hatch Cover surveys: ONE rolled-up `EQ-HATCH-COVER-ANNUAL` + ONE `EQ-HATCH-COVER-CLOSE-UP-5Y` per vessel. Per-cover detail in service report PDF. | LOCKED |
| D-CERT-041 | GMDSS Shore Maintenance Agreement: placement per TEC-04B section. Cadence `5_year`. Office-written, not class-tracked. | LOCKED |
| D-CERT-042 | Type Approvals: `permanent` cadence + optional `linked_pms_component_id` FK. PMS `component_replaced` event triggers alert; NO auto-supersede. | LOCKED |
| D-CERT-043 | Catalog sweep DONE. Confirmed in scope: Builder's Cert (`permanent`), Initial Survey of Safety Equipment (`permanent`), Asbestos Free Cert (`permanent`), ITF Blue Cert (Trade & Commercial). IHM Part 1 + IHM SoC = 2 separate TrackedItems. Approval Page copies stored as approval-page-only (~1–5 MB), not full manuals. | LOCKED |
| D-CERT-044 | Vessel decommissioning: data deleted 30 days from handover or scrap date. Audit log of deletion event retained indefinitely. Days 0–29: `lifecycle_status: pending_disposal`. | LOCKED |
| D-CERT-045 | New vessel acquisition: Acquisition Wizard with mandatory 24-hour validation hold. DPA + Tech Sup'tt + new Master joint sign-off. | LOCKED |
| D-CERT-046 | Class change workflow: manual `vessel.class_society` update by DPA → old class certs `pending_supersession` (NOT auto-deleted) → mandatory new-class snapshot within 30 days → DPA reviews each pending row. | LOCKED |
| D-CERT-047 | NO bulk-write mode for BAU. `ModificationEvent` record groups subsequent cert updates within 30 days for audit traceability. Tech Sup'tt manual SQL escape hatch for genuinely massive bulk events. | LOCKED |

### Interrogation Round 2 (Parser Edge Cases, 25 questions, 2026-05-06)

| # | Decision | Status |
|---|---|---|
| D-CERT-048 | Class status PDFs (NK/KR/BV) ALWAYS text-extractable — no OCR for class snapshot parser. Vessel-side cert PDF uploads may include scans — OCR design for cert upload deferred. | LOCKED |
| D-CERT-049 | Per-class date format whitelist: KR = `YYYY-MM-DD` (ISO 8601); NK + BV = `DD Mon YYYY`. Failed parse → `unmapped_rows[]`. | LOCKED |
| D-CERT-049a | KR uses ISO 8601 consistently across ALL KR-classed vessels. No format variability per vessel. | LOCKED |
| D-CERT-050 | Vessel-to-PDF matching: IMO Number is authoritative. Office UI auto-detects + pre-selects vessel + allows override. Vessel name fuzzy match as secondary check. | LOCKED |
| D-CERT-051 | PDF dedup via SHA-256 hash. Duplicate hash for same vessel → user prompt "Re-process anyway?". Wrong-vessel upload → `superseded: user_error` flag + reverse-apply rollback. | LOCKED |
| D-CERT-052 | Parser version stored on each snapshot. NO automatic re-parse on parser update. Manual re-parse trigger from snapshot detail page. | LOCKED |
| D-CERT-053 | Per-field confidence threshold ≥ 0.95 for auto-inclusion in reconciliation. Below → `flagged_low_confidence[]` for **Marine Sup'tt review**. | LOCKED |
| D-CERT-054 | Multi-page table extraction: `pdfplumber` + custom continuation logic. Test fixtures must include cross-page table samples. | LOCKED |
| D-CERT-055 | Partial parse: `partial_parse` state when 1–25% rows fail. Two banners on dashboard. Marine Sup'tt notified ≤1 hour. >25% = critical escalation. | LOCKED |
| D-CERT-056 | Concurrent uploads: advisory lock on `(vessel_id, snapshot_upload_in_progress)`. Wait OR Override paths. Lock auto-released after 5-min timeout. | LOCKED |
| D-CERT-057 | Test fixture corpus: 6 reference PDFs as permanent regression fixtures + expected JSON. Parser PRs must pass full corpus. CI runs on every PR. | LOCKED |
| D-CERT-058 | Wrong-vessel rollback: conditional reverse-apply via `applied_changes[]`. Intervening writes preserved; conflicts logged. **Marine Sup'tt authorizes rollback**. | LOCKED |
| D-CERT-059 | Parser hard timeout = 5 min. Auto-retry x2 (30s + 90s backoff). Final failure → `parse_failed` state; raw PDF retained; admin notification. | LOCKED |
| D-CERT-060 | Snapshot blob: metadata indefinite (hot); PDF blob hot 5y, then cold archive (S3 Glacier-equivalent, 12h retrieval). UI seamless fetch. | LOCKED |
| D-CERT-061 | ClassCodeMapping versioned per edit. Each ReconciliationRun stamps mapping version. Historical runs NOT auto-recomputed. Manual "Re-reconcile with current mapping" available. | LOCKED |
| D-CERT-062 | `parsed_payload.schema_version` on every snapshot. Graceful degradation for absent fields. Major migrations explicit + reversible. | LOCKED |
| D-CERT-063 | **Replaces window-parsing logic.** Parser extracts only: anniversary, last_done, cadence, postponed, extension info, cert dates. System computes window_open / window_close from anniversary + cadence + IMO rules. NK Range Date = sanity check only. | LOCKED |
| D-CERT-064 | **General principle:** When data follows deterministic rules, system computes rather than parses per-class. Parsers extract minimal facts; computation centralized. | LOCKED |
| D-CERT-065 | NK `Extended` column → child `extension_of` TrackedItem (Master uploads letter). NK `Postponed` column → parent's `postponed_until` field. Both can coexist. | LOCKED |
| D-CERT-066 | Parser SKIPS: vessel particulars, company info, MoU/PSC. Parser PARSES: Conditions of Class → populates `vessel.conditions_of_class[]`; new conditions raise critical alert. | LOCKED |
| D-CERT-067 | All parsed text in UTF-8. Class symbols stripped from `display_name`, preserved in raw payload. Foreign-language fields not parsed. Encoding errors → `unmapped_rows[]` + DPA notification. | LOCKED |
| D-CERT-068 | Reconciliation UI = three-panel view: header (status + counts) → tabs (Matches / Mismatches / Unmapped) → side-by-side per-row diff with `[Notify Master]` + `[Mark as Reviewed]`. Marine Sup'tt is primary reviewer. | LOCKED |
| D-CERT-069 | Snapshot list filters: vessel · class_society · date_range · parse_status · has_unresolved_mismatches. Default sort `printed_on_date DESC`. Pagination 25. CSV export. | LOCKED |
| D-CERT-070 | V1 dashboard tile per vessel: current cert health (% expiring 30/60/90, # mismatches, days since last snapshot). Time-series trends = V1.1. | LOCKED |
| D-CERT-071 | Multi-snapshot diff = V2. V1 ships per-snapshot `applied_changes[]` log only. | LOCKED |
| D-CERT-072 | Parser ops page (dev-only, feature-flagged) — 90-day aggregate stats. Visible to Tech Sup'tt + parser dev mailing list. | LOCKED |
| D-CERT-073 | Anomaly thresholds: mismatch_rate >15% → critical; parse_time >3min → warning; cert_count <expected×0.7 → warning. Threshold-based, no ML in V1. | LOCKED |
| D-CERT-074 | **Anniversary date is permanent per vessel-cert-family.** Office sets ONCE at vessel onboarding. Parser does NOT auto-update. Manual edit only for class re-anchoring (rare, audited). | LOCKED |
| D-CERT-075 | **Class status snapshot purpose narrowed:** (1) detect stale certs, (2) capture Conditions of Class, (3) capture extensions/postponements. Does NOT source: anniversary, window dates, vessel particulars, company info. | LOCKED |

### Interrogation Round 3 (RBAC & Approval Workflow, in progress)

| # | Decision | Status |
|---|---|---|
| D-CERT-076 | Approval workflow follows PSC CAR pattern (`VIMS DOCS/CAR_Database_Schema_v4.sql`). All fields go through approval gate (no field-level bypass). Lifecycle: `draft → pending_master_approval → approved/rejected → finalized`. Drafts auto-expire 7 days. | LOCKED |
| D-CERT-077 | **No "Acting Master" concept.** Master role always staffed onboard; person changes via sign-on/sign-off events but rank is continuous. `vessel.master_user_id` always populated. | LOCKED |
| D-CERT-078 | Deputy DPA designation: ONE user (senior Marine/Tech Sup'tt) per ISM Code paragraph 4. Inherits DPA permissions when substantive DPA flagged unavailable. Time-bound; both can act simultaneously in transition. | LOCKED |
| D-CERT-079 | **Submission scope by catalog row:** new field `submission_scope`. Class Certificates + Statutory & Flag + `is_class_tracked: true` rows = `master_only`. Equipment / Calibrations / Tests / Type Approvals / Plans / Trade & Commercial / Misc = `all_ranks_with_approval` (C/O + C/E + 2/E submit; Master approves). | LOCKED |
| D-CERT-080 | No hard resubmission limit. Each rejection captures reason. After 3 rejections on same submission, auto-flag to FM for review. | LOCKED |

### Interrogation Round 3 — Batch 3/5 (Security & Alert Hygiene, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-081 | **No 2FA / step-up reauth** for high-risk operations (rollback, catalog edit, vessel decommissioning, anniversary date change, deputy DPA activation). A confirmation dialog ("Are you sure?") is sufficient — all destructive operations are soft-delete with audit trail and recoverable within retention window. Confirm dialog text shall name the action and the reversal path. | LOCKED |
| D-CERT-082 | **Session timeout inherits Purchase Module R3-7 + PMS modal pattern.** Office users (DPA, FM, Sup'tts) = 8h idle; Vessel users (Master, C/O, C/E, 2/E) = 24h idle. Re-auth UX = PMS-style modal overlay (not redirect), preserves form state; identifier pre-filled (CrewID for vessel, Employee ID for office); 15-min and 5-min toast warnings; offline = no interruption until next sync. Time reference = server-issued timestamps based on vessel local time from `wrh_ship_time_config`. | LOCKED |
| D-CERT-083 | **Multi-vessel Master = NOT supported.** KSM operates one-Master-one-ship (Pattern X). `vessel.master_user_id` is strictly 1:1 with vessel at any instant. Same human can rotate across different vessels across contracts (Pattern Y, allowed implicitly), but never holds Master role on 2 vessels simultaneously. | LOCKED |
| D-CERT-084 | **No snooze mechanic** for alert cadences. Alerts fire on the 90/60/30/14/7/1 day schedule plus daily post-expiry. User can acknowledge but not defer. Snooze tends to bury real risk; explicit ack-only keeps the system honest. | LOCKED |
| D-CERT-085 | **Alert deduplication rules:** (a) one active alert per `(cert_row, cadence)` pair — re-computation does not re-fire if already-acknowledged at that cadence; (b) successful renewal (new expiry > today + cadence days) auto-dismisses all open alerts on that row; (c) 60-min batch window for in-app/email notifications across same vessel/section. | LOCKED |
| D-CERT-086 | **Internal compliance auditor staffing = Model B (Distributed).** No dedicated auditor role at KSM. Audits conducted by DPA / FM / Tech Sup'tt / Marine Sup'tt as a side responsibility, rotating who audits what. **System does NOT need a separate `auditor` role** — existing DPA / FM / Sup'tt roles already cover audit-time read access. | LOCKED |
| D-CERT-087 | **Read-receipts: independent ack model.** Alerts fire dual-channel (vessel + office simultaneously). Master ack on vessel side does NOT auto-dismiss the office-side alert, and vice versa. Each side acknowledges its own copy. Office dashboard surfaces `vessel_acked: yes/no` as a status flag — visible indicator of vessel awareness, actionable for follow-up calls. Hierarchical close on full resolution: cert renewed → both copies dismissed (per D-CERT-085). | LOCKED |

### Interrogation Round 3 — Batch 4/5 (Approval Queue, Escalation, Office Hierarchy, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-088 | **Approval queue sort = expiry-first.** Master's pending-approvals inbox sorts by closest-expiring cert at top (compliance risk drives priority). Filter scope = current vessel only (audit access via separate Audit Log screen, not queue). No reviewer-lock in V1; race conflicts resolved at DB layer via row version (second approver gets "already actioned by X at HH:MM" toast). Bulk-approve allowed for Equipment / Calibrations / Tests / Misc only; Class Certificates and Statutory & Flag require per-cert review. | LOCKED |
| D-CERT-089 | **Notification escalation targets = DPA + Technical Manager** (head of Technical department, distinct from Tech Sup'tt). Escalation cadence: 30-day alert → Master + Marine Sup'tt + Technical Manager (initial); 14-day no-ack → also DPA; 7-day no-ack → daily reminder to all four; post-expiry → daily to all four until resolved. FM not on the chain (corrected from earlier proposal). Statutory & Class certs include DPA + Technical Manager from day-1 cadence (severity uplift). | LOCKED · ⚠ Confirm "Technical Manager" role exists distinct from Tech Sup'tt — see resume notes |
| D-CERT-090 | **Office hierarchy = inherit PSC Inspection RBAC pattern (`VIMS DOCS/BACKEND_STRUCTURE.md §11`).** Reuse existing tables: `master_RoleByVessel` (office user → vessel-scope mapping), `msc_profiles.form_ids` (sidebar/nav visibility), `msc_profiles.process_ids` (action-level permissions), `mapping_role_user` (user → profile mapping). Global reviewer override via `Mapping_CrewAssReviewers` + `has_global_vessel_access` flag for DPA / fleet-wide reviewers. **No new vessel-assignment tables for Certs module** — reuse existing assignment infra. Marine Sup'tt and Tech Sup'tt vessel scope = whatever `master_RoleByVessel` says today; DPA = full fleet. | LOCKED |
| D-CERT-091 | **Audit log retention = 3 years rolling.** Append-only at DB layer (no UPDATE/DELETE GRANTs to app role on `vims_certs_audit_log`). Read access = DPA + FM (full fleet); Marine/Tech Sup'tt = own assigned-vessel audit slice via filtered view. Export = DPA only, watermarked PDF + CSV for ISM external audit. **Note:** 3y is shorter than common 5–10y ISM retention; user-decision per Maritime PO. Older rows soft-deleted nightly batch (audit_log retention is itself audited). | LOCKED · ⚠ Note: 3y vs IMO ISM common 5y — confirmed by PO 2026-05-07 |
| D-CERT-092 | **Bulk-action permissions:** (a) **Catalog push** of new cert type by DPA = auto-creates `pending_first_upload` row on every active vessel (no opt-in friction); (b) **Anniversary recompute** = bulk allowed but requires 2nd approver from FM, confirmation modal shows affected vessel count + cert count + sample preview before commit; (c) **Bulk soft-delete of catalog rows** = single confirm dialog + reason field, capped at 50 rows per batch to prevent fleet-wide accidental wipe. All three operations are themselves audited per D-CERT-091. | LOCKED |

### Interrogation Round 3 — Batch 5/5 (Edge Cases & Continuity, 2026-05-07) — ROUND 3 COMPLETE

| # | Decision | Status |
|---|---|---|
| D-CERT-093 | **Vessel sale: 30-day soft-delete window, then hard-delete** (same path as decommissioning per D-CERT-038). Pre-delete handover bundle generated automatically: PDFs + structured JSON manifest (cert metadata + an index listing contents). In-flight submissions at sale time = **locked and exported as-is** in handover bundle (no auto-reject; preserves intent for new owner). KSM retains a redacted audit log slice (cert events only, no personnel data) post-delete for compliance history. | LOCKED |
| D-CERT-094 | **Flag-change event:** recorded by DPA in vessel profile (effective date, old flag, new flag, reason free-text). On commit: statutory certs auto-flagged `invalid_due_to_reflag` but NOT deleted (audit trail preserved); Master prompted to upload replacement statutory certs from new flag. Class certs untouched (class society survives flag change). Vessel profile UI surfaces a "pending statutory re-upload" banner until backlog clears. | LOCKED |
| D-CERT-095 | **No gap-period authority needed.** KSM enforces **minimum safe manning** — Master sign-off and reliever sign-on must overlap (handover overlap mandated). Vessel never sails without a Master onboard. Therefore: `vessel.master_user_id` always populated, no acting/bridge/auto-promotion mechanism required. Reinforces D-CERT-077. | LOCKED |
| D-CERT-096 | **External read-only access + Master share-bundle** (two distinct features): (a) **External read-only login** for charterers / vetting / external auditors: time-bound (7-day default, DPA-extendable to 30), scoped granularly to **specific vessel(s) AND specific document set(s)** (not just whole-vessel). DPA defines scope at login creation: vessel list + cert section/category list + optional individual cert IDs. (b) **Master share-bundle:** Master can bulk-select OR single-select certificates from their vessel and download as a single zipped bundle with an auto-generated **index/manifest PDF** listing all contents (cert title, issue date, expiry, file count). Used to send to port agents, charterers, vetting inspectors. Both features logged in audit log. | LOCKED |
| D-CERT-097 | **No break-glass / emergency-override mechanism.** Not needed given D-CERT-095 (minimum safe manning ensures Master is always onboard). DPA-emergency-approve and incapacitation flag NOT in V1. | LOCKED |
| D-CERT-098 | **Technical Manager (TM) is a distinct role** at KSM — head of Technical department, separate from Tech Sup'tt. **Per-vessel assignment:** DPA configures `vessel.technical_manager_user_id` AND `vessel.marine_supt_user_id` per vessel via Vessel Profile screen. These mappings drive notification routing per D-CERT-089 (TM gets escalation pings on cert expiries; Marine Sup'tt is reconciliation reviewer per D-CERT-039). One TM may cover multiple vessels (allowed). Stored as FK to `master_user`. | LOCKED |
| D-CERT-099 | **AMENDS D-CERT-091:** Audit log retention revised to **5 years rolling** (matches IMO ISM common policy). All other terms unchanged: append-only DB GRANTs, DPA+FM read full fleet, Marine/Tech Sup'tt = own-vessel slice, DPA-only export. Earlier 3y note in D-CERT-091 is superseded. | LOCKED |

### Interrogation Round 4 — Batch 1/5 (Source Format & File Ingest, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-100 | **AMENDED by D-CERT-104.** ~~Migration ingest pipeline (3-stage onboarding wizard): Stage 1 — DPA bulk-uploads filled-in SQE S 633 file per vessel + PDF folder/ZIP in single drop; system parses both in parallel.~~ Stages 2 & 3 unchanged: Stage 2 = System auto-populates and surfaces gap-fill UI; Stage 3 = Class Status Report cross-validation. Stage 1 superseded — see D-CERT-104. | PARTIALLY SUPERSEDED |
| D-CERT-101 | **OCR-based PDF auto-matching to cert rows.** System OCRs each uploaded cert PDF and extracts: cert type/name, IMO (authoritative per D-CERT-031), issue date, expiry date, issuing authority. Match against cert rows by fuzzy text on `display_name` + IMO. Confidence ≥80% → auto-attach; <80% → surface in gap-fill UI for DPA manual confirm. **Filename is NOT primary key** — used only as tiebreaker if OCR confidence is low. OCR result stored in `parsed_payload` per snapshot pattern (D-CERT-062). | LOCKED |
| D-CERT-102 | **AMENDED by D-CERT-103.** ~~TEC-04B is REFERENCE ONLY, not part of SMS, NOT a vessel-data migration source. It is provided solely to inherit cert categories and types into the new catalog (already consumed by D-CERT-023 / D-CERT-024 / D-CERT-037 during catalog design). Vessel-level cert instance data is migrated exclusively from the filled-in SQE S 633 file per vessel (R3-R4 header carries vessel name + date; rows carry per-cert issue/expiry/remarks). No TEC-04B per-vessel ingest occurs at runtime.~~ | SUPERSEDED |
| D-CERT-103 | **Catalog seed + SMS document identity (SUPERSEDES D-CERT-102):** **Catalog construction = union of cert types from BOTH SQE S 633 + TEC-04B, deduplicated.** TEC-04B's section taxonomy (Trading / LSA-FFA-Nav-GMDSS / Misc + Serial/Type/Cert#/Issue/Expiry/Survey/Next-Annual/Remarks columns) is the **structural model** for catalog sections and per-cert metadata fields. TEC-04B is not itself in the SMS document register, but its taxonomy is cleaner. **The new VIMS Certificates module IS the digital replacement for the SMS-controlled document "SQE S 633"** — that's the form code the company SMS uses, so the module's print/export carries the "SQE S 633" header and document identifier (already covered by D-CERT-002, restated for clarity). All cert types from both legacy files are seeded; duplicates merged at catalog build time (DPA + Tech Sup'tt review workshop per D-CERT-023). | LOCKED |
| D-CERT-104 | **Vessel-data migration = iterative batch PDF ingest (no filled-Excel source):** DPA uploads actual certificate PDFs in **batches of ≤10 docs per batch** (or whatever batch size yields best OCR throughput; system may auto-cap if needed). Loop per batch: (1) system OCRs each PDF per D-CERT-101 (extracts cert type, IMO, issue date, expiry, issuer); (2) auto-populates target cert rows in catalog and creates new vessel-cert instances; (3) gap-fill UI surfaces unresolved fields and low-confidence matches for DPA confirm/correct; (4) DPA confirms batch → batch committed → next batch. **Save-as-draft between batches** for multi-day onboarding. Filled-in legacy Excel files (SQE S 633 / TEC-04B per vessel) are **NOT** required as input — Excel files were only used to seed the catalog (D-CERT-103). Class Status Report PDF cross-verification (per D-CERT-100 Stage 3) runs after all cert PDF batches are ingested. | LOCKED |

### Interrogation Round 4 — Batch 2/5 (OCR Field Extraction & Catalog Dedup, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-105 | **OCR field extraction targets per cert PDF.** REQUIRED fields: certificate type/name, issuing authority, vessel name, IMO number, date of issue, date of expiry (unless permanent), **certificate number** (with explicit "no cert number on document" bypass checkbox in gap-fill UI when cert genuinely lacks one), **place of issue**. OPTIONAL fields: last annual / intermediate survey date (conditional on cert having child surveys), conditions/restrictions/endorsements (verbatim text), issuing officer signature/name. Bypass-cert-number flow logs reason and writes `cert_number = null, bypass_reason = '<DPA reason>'` to audit. | LOCKED |
| D-CERT-106 | **OCR confidence handling — three-mode fallback.** Per-field auto-accept threshold ≥80%. Per-field 60–80% confidence → field shown in gap-fill UI with low-confidence highlight + OCR best guess pre-filled; DPA accepts or corrects. Per-field <60% → field shown blank with "Could not read — please enter manually" prompt. Whole-doc unprocessable (image too poor) → entire PDF flagged "manual entry required" and DPA types all fields against the visible PDF. All thresholds tunable post-launch based on observed OCR quality. | LOCKED |
| D-CERT-107 | **Catalog dedup rules (S 633 + TEC-04B merge).** Detection: exact-name match after normalization (case, whitespace, punctuation) = auto-merge; fuzzy match ≥90% confidence = auto-merge; 70–90% = surface for DPA + Tech Sup'tt workshop review (per D-CERT-023); <70% = treat as distinct. Validity-code conflicts (same cert name, different validity in two files) = workshop decides per cert; **never auto-resolve** validity conflicts (compliance risk). Workshop output = single locked catalog row per resolved cert. | LOCKED |
| D-CERT-108 | **Cert hierarchy preservation = auto-detect + workshop review.** S 633 row patterns (rows without Col C serial = children of immediately preceding parent leaf) auto-parsed into proposed `parent_id` links during catalog seed. Proposed tree shown in workshop UI; DPA + Tech Sup'tt confirm or re-parent before catalog locks. Hierarchy is load-bearing for survey window computation (D-CERT-013), so manual confirmation prevents auto-detection errors from propagating. UI display capped at 2 levels per D-CERT-009. | LOCKED |
| D-CERT-109 | **Catalog metadata fields per row.** Standard set: `catalog_id` (UUID), `canonical_code` (workshop-assigned, e.g. `ISM_SMC`), `display_name`, `print_section_label`, `section` (one of 9 enums per D-CERT-008), `validity_type` (full/conditional/short_term/permanent per D-CERT-013), `cadence_months`, `issuing_authority_type` (flag/class/RO/manufacturer/company), `is_class_tracked`, `submission_scope` (master_only/all_ranks_with_approval per D-CERT-079), `parent_id`, `legacy_remarks`, `print_order`, `is_active`, `created_at`, `updated_at`. **PLUS:** `mandatory_for_all_vessels` (bool) AND `applicable_ship_types` (array of ship_type enums, e.g. `['oil_tanker', 'chemical_tanker', 'gas_carrier']`). At vessel onboarding, system pre-populates pending cert rows based on vessel's ship type — DPA does not pick from full catalog manually. | LOCKED |

### Interrogation Round 4 — Batch 3/5 (Anniversary, IMO, Missing-Data Handling, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-110 | **Anniversary date discovery = manual DPA entry + Class Status Report cross-validation.** DPA enters anniversary date manually as part of vessel-profile setup (before cert-PDF batches start). When DPA later uploads the Class Status Report PDF (Stage 3 per D-CERT-100), system cross-validates DPA-entered anniversary against the date implied by the class report's next-due-dates; any discrepancy surfaced in reconciliation panel for DPA to confirm or correct before cutover. Anniversary is set ONCE at onboarding (per D-CERT-035) and never auto-updated by parser. | LOCKED |
| D-CERT-111 | **IMO sourcing & vessel-cert binding.** OCR'd IMO that doesn't match any KSM vessel → **vessel-name fallback** match against `master_vessel.vessel_name`; if unique match, auto-bind with DPA confirm prompt; if ambiguous, gap-fill UI shows candidates for DPA selection. OCR can't read IMO at all → system suggests IMO from vessel name + filename hint + the wizard's currently-selected vessel context (per D-CERT-112), DPA confirms. PDFs that resolve to no vessel after both fallbacks = held in gap-fill UI as "unbound" until DPA either selects a vessel or rejects the PDF. | LOCKED |
| D-CERT-112 | **Onboarding wizard = vessel-locked, one vessel at a time.** DPA selects target vessel first, then uploads cert PDFs for that vessel only. System assumes every PDF in the active batch belongs to the selected vessel; OCR'd IMO mismatch surfaces as warning (not auto-rerouted to another vessel). Mixed-vessel batches NOT supported in V1 (deferred to V1.1+ if office workflow demands it). Simpler mental model, fewer auto-routing errors. | LOCKED |
| D-CERT-113 | **Missing-PDF cert rows allowed at onboarding.** DPA may manually create a cert row without an attached PDF when the cert is known to exist but the file is lost. Row marked `pdf_missing: true`; visible warning banner on cert card; counts toward fleet "incomplete documentation" KPI. **No auto-escalation, no grace period** — the data state is acknowledged-incomplete, not an active compliance risk; DPA requests PDF copy when convenient (request workflow not in V1, just a flag). | LOCKED |
| D-CERT-114 | **Migration cutover = HARD CUTOVER.** When DPA completes vessel onboarding and FM signs off, legacy SQE S 633 + TEC-04B Excel files **stop being maintained on go-live day**. All cert updates flow exclusively through VIMS Certs module; print export from VIMS replaces the Excel artifacts. Legacy files retained as **read-only frozen archive** for historical reference; never updated post-cutover. No parallel-run safety period. Confidence is built during onboarding (per-vessel DPA confirmation per batch) — by the time a vessel is fully onboarded, its data is trusted. | LOCKED |

### Interrogation Round 4 — Batch 4/5 (Dry-Run, Validation Gates, Error Reporting, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-115 | **Dry-run = preview before commit.** After OCR + auto-population, system shows DPA a summary screen ("This batch will create N cert rows + M PDF attachments to existing rows") with full row-level breakdown. DPA clicks Commit (writes to DB) or Cancel (full batch rollback, no DB writes). One extra click per batch in exchange for safer onboarding. | LOCKED |
| D-CERT-116 | **Validation gates at commit time:** **BLOCKS commit:** required field missing on any row · cert-number bypass without reason · OCR'd IMO unresolved against any vessel · validity type undetermined (`unknown`) · cert issue date in the future · cert duplicate within batch (same cert_number on two PDFs). **WARNS but allows:** `pdf_missing: true` row · issuer type undetermined · cert expiry date in past (already-expired cert at onboarding) · two cert rows for same catalog_id on same vessel (legitimate cases like dispensation + original). | LOCKED |
| D-CERT-117 | **Error report = in-app UI + downloadable CSV artifact.** Live gap-fill UI for active session. On commit, system generates `batch_ingest_<vessel_imo>_<yyyymmddhhmm>.csv` listing every row with status (committed / blocked / warned / corrected) + reason. CSV saved in audit log as `batch_ingest_report` artifact (retrievable per D-CERT-091/099 retention rules) and downloadable by DPA for vessel follow-up or sharing. | LOCKED |
| D-CERT-118 | **Re-import idempotency = content-hash dedup + supersede prompt.** Each uploaded PDF hashed (SHA-256) at upload. If same hash already attached to a vessel's cert row → silently skip re-attach, log "already imported" in batch report. If a PDF arrives with same `cert_number` on same vessel but DIFFERENT content hash (re-issued/corrected cert) → prompt DPA: "A cert with this number already exists, does this PDF supersede it?" If yes → old PDF archived with `superseded_at = now()`, new PDF attached as current. | LOCKED |
| D-CERT-119 | **Per-vessel onboarding completion = hybrid auto-enable / override.** System computes coverage of `mandatory_for_all_vessels=true` cert types for the vessel. **100% mandatory coverage** (no gap-fill items, anniversary date set) → auto-enables alerts and notification engine for that vessel. **<100%** → DPA must explicitly override with a written reason (e.g., "X cert being re-issued, expected by date Y") to enable. Override reason logged in audit log; surfaced on vessel dashboard until coverage reaches 100%. | LOCKED |

### Interrogation Round 4 — Batch 5/5 (Onboarding Wizard UX, Edge Cases, Compute Budget, 2026-05-07) — ROUND 4 COMPLETE

| # | Decision | Status |
|---|---|---|
| D-CERT-120 | **Per-vessel onboarding wizard sequence (7 steps, no Master acknowledgment step):** (1) Vessel selection from `master_vessel` (or create new vessel record); (2) Vessel profile setup — anniversary date, ship type, current Master, Marine Sup'tt, Technical Manager (per D-CERT-098); pending cert rows pre-populated from `applicable_ship_types` (per D-CERT-109); (3) Cert PDF batch ingest in batches of ≤10 (per D-CERT-104); preview-commit cycle (per D-CERT-115); loop until DPA marks "all PDFs uploaded"; (4) Class Status Report PDF upload + Stage 3 reconciliation (per D-CERT-100) + anniversary cross-validation (per D-CERT-110); (5) Reconciliation review — DPA resolves discrepancies; (6) Completion gate — mandatory coverage check (per D-CERT-119), auto-enable or override-with-reason; (7) FM sign-off → vessel goes live and alerts begin firing. **No separate Master notification / acknowledgment step** — alerts route to Master at go-live without explicit ack handshake. | LOCKED |
| D-CERT-121 | **Already-expired certs at onboarding = quarantine state.** Cert rows where OCR'd expiry date is in the past at commit time created with `status = expired_at_onboarding` (special state distinct from `expired`). Alert engine **suppresses** post-expiry notifications for these rows until DPA either (a) uploads a renewal PDF (status flips to `active` with new expiry) OR (b) explicitly marks "expired in reality, awaiting renewal" (status flips to `expired`, alerts begin firing). Prevents alarm-spam at go-live for known-state legacy certs. | LOCKED |
| D-CERT-122 | **Uncatalogued cert types = inline catalog promotion.** When DPA encounters a cert PDF for a cert type not in the catalog during onboarding, gap-fill UI offers "Create new catalog row" inline (no leaving the wizard). DPA fills minimal fields: display_name, section, validity_type, cadence, issuing_authority_type, applicable_ship_types. New catalog row immediately available system-wide; DPA + Tech Sup'tt review weekly cleanup queue to refine `canonical_code` and other workshop-grade metadata. Audit log captures "DPA added catalog row X during onboarding of vessel Y". | LOCKED |
| D-CERT-123 | **OCR processing = async per batch.** DPA uploads a batch (≤10 PDFs); system queues OCR jobs; DPA can immediately queue another batch OR leave wizard. When OCR completes for a batch, DPA gets in-app notification + email; batch's gap-fill UI sticky-pinned in "Pending Review" dashboard queue. DPA returns when convenient to confirm/correct/commit each ready batch. Aligns with D-CERT-104 multi-day onboarding pattern. | LOCKED |
| D-CERT-124 | **Onboarding rollback = vessel-level, pre-go-live only.** During the onboarding wizard (before step 7 FM sign-off), DPA can click "Reset onboarding for vessel X" — soft-deletes all cert rows + PDFs created during the active onboarding session for that vessel; vessel returns to wizard step 1; audit log captures full rollback with DPA reason. **Post-go-live**, this control is unavailable; corrections proceed via normal cert lifecycle (rollback per D-CERT-076). Avoids accidental fleet-state corruption after live operations begin. | LOCKED |

### Interrogation Round 5 — Batch 1/5 (Page Layout & Header Block, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-125 | **Print export — form code preserved, layout free.** SMS form identifier **"SQE S 633"** is preserved verbatim in print output (this is the SMS-controlled document code; auditor expectation). Beyond that, layout is **free design for best UI/UX**. Not pixel-faithful to the legacy Excel; modernized for readability while keeping the form code, section structure (D-CERT-008 sections), and SMS document identity. Paper size + orientation chosen by designer to suit content density. | LOCKED |
| D-CERT-126 | **Vessel header block (every page):** Top of page 1 carries: vessel name (large), IMO, flag, class society, ship type, current Master at print time (per `vessel.master_user_id`, D-CERT-077/095), print date. Pages 2+ carry compact one-line header (vessel name + IMO + page X of Y + section banner). Vessel metadata (IMO/flag/class/ship-type) appears in a **footer-extended block** on page 1 to avoid overcrowding the visual header. | LOCKED |
| D-CERT-127 | **Repeating page elements + company logo:** Every printed page repeats: (a) compact vessel header (vessel name + IMO + page X of Y), (b) column headers, (c) **current section banner** (so a page picked up mid-stack is identifiable). **Company logo sourced from database via shared endpoint pattern from PSC Inspection module**: `GET /api/auth/company-logo/` (reused; no separate Certs-module endpoint). Logo size **30mm × 15mm top-left** per `VIMS DOCS/DESIGN_SYSTEM.md` line 481 — consistent with PSC Inspection PDF reports. | LOCKED |
| D-CERT-128 | **Print identifiability — full audit trail in footer:** Each printed page footer contains: (a) print date + time UTC, (b) print user name + role (e.g., "DPA John Smith"), (c) **system-state hash** (8-char hash of vessel cert state at print time — detects post-print data drift), (d) **unique `print_id`** (human-readable code: `SQE-S633-<imo>-<yyyymmdd>-<seq>`, e.g. `SQE-S633-9876543-20260507-001`). Every print event writes a row to audit log with `print_id` as cross-reference key. | LOCKED |
| D-CERT-129 | **Margins & blank-space — best UX/UI:** Designer-led margins; not bound to legacy 0.38"/0.31" specs. Optimize for binder hole-punching (≥0.6" left bind-edge) and readability. **Empty sections preserved with banner** showing "— no certs in this section for this vessel —" (auditor expectation: visible confirmation that section was checked, not omitted). Empty rows within a section: collapse to keep density high, but section heading always shown. | LOCKED |

### Interrogation Round 5 — Batch 2/5 (Column Schema, Date Formats, Validity Codes, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-130 | **Print column schema (11 columns):** S/No (resets per section) · Certificate name (`display_name`, wraps to 2 lines if needed) · Cert number (empty if bypassed per D-CERT-105) · Issued by (`issuing_authority`) · Place of issue (per D-CERT-105) · Date of issue · Date of expiry ("Permanent" if applicable) · Validity (legacy short codes per D-CERT-132) · Days to go (negative for expired, e.g. `-23`) · Status (small colored dot + 1-letter G/Y/R; B/W-printer-friendly) · Remarks (`legacy_remarks` + manual notes). Drops legacy serial sub-numbers and section column (replaced by section banner per D-CERT-127). | LOCKED |
| D-CERT-131 | **Date format throughout print = `dd-Mmm-yyyy`** (e.g., `15-Mar-2027`). Header dates and table dates use the same format. Unambiguous (no US/EU collision), maritime industry standard on most flag certs, recognizable to KSM Bangkok office staff and Thai/international auditors. | LOCKED |
| D-CERT-132 | **Validity codes printed as legacy short forms:** `A` · `Bi-A` · `5-Y` · `10-Y` · `Perm.` · `ST` · `6-Mth`. One-line glossary printed in **page 1 footer only** ("Validity codes: A=Annual, Bi-A=Biennial, 5-Y=5-Yearly, 10-Y=10-Yearly, Perm.=Permanent, ST=Short-Term, 6-Mth=6-Monthly"). Subsequent pages omit the glossary to preserve density. Auditor recognition is the print's primary purpose. | LOCKED |
| D-CERT-133 | **Cert hierarchy print = sub-numbering.** Parent cert gets a section-relative serial number (e.g., `19`); children get sub-letters (e.g., `19.a Last Annual Survey`, `19.b Last Intermediate Survey`). Stable identifier per row enables auditor referencing ("show me supporting evidence for line 19.a"). No font-size shifts or indentation tricks; flat row format with the sub-numbering carrying hierarchy semantics. | LOCKED |
| D-CERT-134 | **Section row ordering = catalog `print_order` with parent-child grouping enforced.** Within each section, rows ordered by `catalog.print_order` (DPA/Tech Sup'tt-set canonical sequence at catalog seed time). Children **always immediately follow their parent** regardless of `print_order` of children themselves. Stable across reprints (auditor can find the same row in the same place across two prints of the same vessel state). | LOCKED |

### Interrogation Round 5 — Batch 3/5 (Status Visualization, Color, B/W Print, Multi-Language, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-135 | **Status visualization = color + shape hybrid (B/W-photocopy-resilient).** Every cert row's status indicator carries BOTH color AND shape: green ● (Current), amber ◐ shades for expiring tiers (per D-CERT-136), red ◯ or hatched bar (Expired). Color print preferred but B/W reproduction (photocopy, fax) remains readable via shape. No DPA toggle for color/B/W mode — output is always hybrid. | LOCKED |
| D-CERT-136 | **Expiry urgency = 5 tiers, granular alignment with notification cadence.** Status bands: (1) Current (>90 days to expiry) — green ● ; (2) Expiring ≤90 days — amber-light ◐ ; (3) Expiring ≤30 days — amber-medium ◐ ; (4) Expiring ≤7 days — amber-dark ◐ ; (5) Expired (≤0 days) — red ◯. Mirrors notification cadences (90/30/14/7/1 day per D-CERT-084). Auditor sees exactly which tier any cert is in. Days-to-go column shows precise number alongside the band. | LOCKED |
| D-CERT-137 | **Print language = English only for V1.** Maritime industry default; Thai officials handle cert matters in English; translating 340+ cert names to Thai would be heavy translation+maintenance burden. Multi-language print deferred to V1.1+ if Thai DMA inspector explicitly requires Thai-language certs in the future. | LOCKED |
| D-CERT-138 | **Watermarks = conditional, scope-driven.** Watermark applied per print context: (a) DPA fleet-wide internal print → `INTERNAL`; (b) external auditor export per D-CERT-096 → `AUDIT COPY — <VESSEL>` + auditor name + expiry date of access; (c) Master share-bundle per D-CERT-096 → `MASTER COPY` + recipient name (port agent / charterer); (d) pre-go-live during onboarding → `DRAFT — NOT FINAL`; (e) post-go-live default = no watermark. Watermark color = light gray, diagonal, ~30% opacity, doesn't obscure data. | LOCKED |
| D-CERT-139 | **Signature block = digital signature indicator only (no wet-sig block).** End-of-print shows: "Approved by Master <name> on <date> at <time> via VIMS — print_id <reference>", "Reviewed by Marine Sup'tt <name> on <date> via VIMS — <reference>", "DPA acknowledgment <name> on <date> via VIMS — <reference>". Digital approval is the source of truth for compliance. No empty wet-signature lines printed. Saves paper, reinforces digital-first model, and prevents confusion about which signature is authoritative. | LOCKED |

### Interrogation Round 5 — Batch 4/5 (Print Scope, Excel Export, RBAC, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-140 | **Print scope = 4 variants, all available.** (a) **Per-vessel full** — single vessel, all 9 sections, all rows (default; the classic SQE S 633); (b) **Per-vessel partial** — single vessel filtered by section / status / cadence (e.g., only Statutory, only ≤30-day expiring); (c) **Per-section fleet-wide** — single section across all vessels in fleet (DPA/FM only, per D-CERT-141 RBAC); (d) **Custom selection** — multi-select individual cert rows from any in-scope vessel(s) (Master share-bundle for outbound to agents/charterers per D-CERT-096). All scopes render identical column schema (D-CERT-130) + header/footer (D-CERT-126/127/128); only the row set differs. | LOCKED |
| D-CERT-141 | **Excel export model = data-only + companion PDF.** Each print action generates BOTH (a) a `print_id`-stamped PDF (legal/audit artifact, hash-stamped per D-CERT-128) and (b) a data-only Excel file (no formulas; computed-and-frozen values). PDF is the source of truth for compliance. Excel is for analysis (auditor sorts/filters/pivots). No live formulas in Excel — prevents stale-data illusion when an old file is reopened months later. Both files share the same `print_id` for cross-reference. | LOCKED |
| D-CERT-142 | **Print RBAC matrix:** | LOCKED |
| | **Per-vessel full / partial:** VESSEL_MASTER (own vessel only), OFFICE_PIC/SSQE/SUPT (vessels per `master_RoleByVessel`, per D-CERT-090), DPA (all), FM (all), External Auditor (scoped per D-CERT-096). | |
| | **Per-section fleet-wide:** DPA + FM only; everyone else blocked. | |
| | **Custom selection (Master share-bundle):** VESSEL_MASTER (own vessel only), DPA + FM (all). | |
| | Master cannot print other vessels' state. Print actions logged in audit log per D-CERT-128. | |
| D-CERT-143 | **Print throttling = soft limit + audit-log surface.** No hard blocking. If a user prints >10 reports per hour, audit log entry tagged "high-volume print activity by user X" surfaces in FM dashboard for governance review. Legitimate burst scenarios (fleet review, audit prep) not blocked. Pattern-based abuse handled via office governance, not system enforcement. | LOCKED |
| D-CERT-144 | **Print performance budget:** Per-vessel scope (default, ~4-6 pages, ~40 certs) = synchronous generation with progress bar UI ("Generating PDF (page X of Y)..."). Hard cap **60 seconds sync**; over → error with retry. Fleet-wide scope (all vessels, ~30+ pages) = async generation per D-CERT-123 pattern (queue + email/in-app notification + download link); async timeout **5 minutes**. PDF library: HTML-to-PDF (WeasyPrint or ReportLab — final pick deferred to Phase 0 build). | LOCKED |

### Interrogation Round 5 — Batch 5/5 (Custom Templates, Audit Logging, Third-Party Distribution, 2026-05-07) — ROUND 5 COMPLETE

| # | Decision | Status |
|---|---|---|
| D-CERT-145 | **Third-party deliverable = ZIP bundle (manifest PDF + cert PDFs).** When sharing cert state with external parties (auditors, charterers, port agents, P&I, vetting), the deliverable is **NOT** the printed SQE S 633 alone — it's a **ZIP archive** containing: (a) a **manifest PDF** auto-generated, listing every cert in the bundle (cert title, issuer, issue date, expiry, file reference) — same index style as D-CERT-096 Master share-bundle; (b) the **actual cert PDFs** (the underlying source documents). The recipient sees the list and can open each cert directly. Bundle filename: `VIMS_CertBundle_<vessel_name>_<yyyymmdd>_<print_id>.zip`. Watermark per D-CERT-138 applies to manifest PDF. Generalizes the share-bundle pattern from D-CERT-096 to ALL external distribution scenarios (charterers, auditors, P&I, port agents). | LOCKED |
| D-CERT-146 | **Print template versioning = single live template + immutable artifact archive.** Template is editable by DPA at any time (column tweaks, glossary updates, layout refinements). Generated PDFs/Excels in audit log are **immutable artifacts** preserving exactly what was rendered at print time (per append-only audit log per D-CERT-091/099). No template version history needed — the PDF artifact IS the historical snapshot. | LOCKED |
| D-CERT-147 | **Print audit log granularity = system-state hash + artifact references, no full-row JSON dump.** Per print event: `print_id`, user (id/name/role), timestamp UTC, vessel(s) in scope, print scope variant (D-CERT-140), system-state hash, PDF blob URL, Excel blob URL, watermark applied, page count, recipient (if external). **No full row-by-row JSON serialization** — duplicative since audit log already tracks every cert change individually; system-state hash + reconstruction query is the lean sufficient model. | LOCKED |
| D-CERT-148 | **Historical reprint = audit-log artifact preferred; original Class Status downloadable.** When auditor requests "show me state as-of <date>", system returns the PDF/Excel artifact closest to that date from audit log (immutable, auditor-verifiable). **Additionally**, vessel staff and office staff can download the **original uploaded Class Status Report PDF** for any vessel at any point in time directly from system archive (vessel-scoped per RBAC; preserves the source-of-truth class document for audit cross-reference). Reconstruction-on-demand reprints are NOT in V1 (deferred); audit-log artifact + original Class Status PDFs are sufficient evidence. | LOCKED |
| D-CERT-149 | **Print delivery = browser download + auto-archive + optional email.** Every print action: (a) immediate browser download of PDF + Excel pair; (b) auto-archived in vessel-scoped "Archived Reports" folder for office re-fetch without re-printing; (c) optional checkbox at print time: "Email this report to <recipient>" — uses existing email infra; recipient + subject + attachment + audit log entry. Default = (a) + (b); (c) is opt-in per print. | LOCKED |
| D-CERT-150 | **Print failure handling = HARD FAIL with error surfacing for support team.** PDF/Excel generation failures NOT auto-retried (no silent recovery — could mask underlying bugs). User sees clear error message with `print_id`-prefixed error code; retry option in UI. **Failure event automatically logged to support ticket queue** (or email to support team) with stack trace and `print_id` reference so support can investigate and patch. No partial-success outputs (dangerous — auditor might mistake partial for complete). | LOCKED |

### Interrogation Round 6 — Batch 1/5 (Channels, Templates, Delivery Infrastructure, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-151 | **Notification infra = reuse VIMS shared infra + Slack channel added to V1.** In-app notifications via shared `master_notification` table (single bell-icon inbox across all VIMS modules — Reporting, Safety, PMS, Purchase, Certs); email via existing `email_dispatcher` service. **Slack integration added to V1** (was V2 in original §6.2 — user-elevated 2026-05-07). Per-vessel Slack channel for high-priority alerts (cert expiring ≤30d, cert expired, approval-needed); fleet-wide channel for DPA/FM digests. Module-specific cert metadata in `vims_certs_notification_meta` table linked to `master_notification.id`. Updates §6.2 channel matrix accordingly. | LOCKED |
| D-CERT-152 | **Email format = HTML primary + plain-text fallback (multipart).** KSM-branded HTML with company logo header (per D-CERT-127 logo source), color+shape status indicators per D-CERT-135, action buttons ("View in VIMS / Acknowledge"), footer with `notification_id` reference. Plain-text alternative auto-generated for legacy/filtered clients. Action buttons use 24h-expiring magic links per D-CERT-154. | LOCKED |
| D-CERT-153 | **Email subject conventions:** Prefix `[VIMS Certs]`; vessel name (not IMO) in subject for human mental-model match; **NO emoji in subject** (SMTP relay strip risk + spam filter false-positives) — emoji used in HTML body only. Templates: expiring 90/60d → `[VIMS Certs] Cert expiring in N days — <Vessel> — <Cert Name>`; expiring 30/14/7/1d → `[VIMS Certs] URGENT — <Cert> expires in N days — <Vessel>`; expired → `[VIMS Certs] EXPIRED — <Cert> — <Vessel> — Action required`; approval-needed → `[VIMS Certs] Approval needed — <Cert> renewal — <Vessel>`; daily fleet digest → `[VIMS Certs] Daily fleet digest — <date> — N items`. | LOCKED |
| D-CERT-154 | **Email-to-action = magic-link one-click ack.** Email body includes "Acknowledge" button → unique short-lived signed URL → click marks ack on cert without requiring full app login. URL is **single-use** and **24h-expiring**; click-through tracked in audit log per D-CERT-155. No inbound email parsing (avoids spoofing surface, fragile parsers, infra requirement). Plain in-app ack remains primary path; magic-link is the convenience channel for Masters at sea. | LOCKED |
| D-CERT-155 | **Notification audit trail.** Per notification event, audit log captures: `notification_id` (UUID), trigger event (`cert_expiring_30d` / `cert_expired` / etc.), cert row id + vessel id, recipient(s) (user_ids + roles), channels delivered to (in-app/email/Slack), sent timestamp, delivery status per channel (queued/sent/bounced/failed), ack status (who, when, channel — in-app/magic-link/Slack), escalation level (initial / 14d-no-ack / 7d daily-reminder). **No email open tracking** (privacy concerns + Apple Mail Privacy Protection blocks pixel reads anyway; signal unreliable). Magic-link click-through is the engagement signal alongside explicit ack. ⚠ User did not explicitly answer Q5 in 2026-05-07 session — recommendation applied as default; revisit if needed. | LOCKED · ⚠ Default-applied (Q5 unanswered) |

### Interrogation Round 6 — Batch 2/5 (Vessel Online Architecture, Quiet Hours, Digests, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-156 | **Vessel architecture = ONLINE-REQUIRED (Starlink-equipped fleet).** All KSM vessels have Starlink onboard providing reliable always-on broadband. The Certs module assumes online connectivity for vessel users; **no IndexedDB cert caching, no offline queue, no offline-mode UX, no sync logic** in the Certs module. Standard server-side `master_notification` queue handles transient connectivity drops; client pulls on reconnect via standard polling/websocket. Significantly simplifies vessel-side architecture vs. PMS/Purchase modules (which were designed pre-Starlink). Note: D-CERT-082 session re-auth modal still applies for transient drops; that's HTTP-level resilience, not full offline-mode design. | LOCKED |
| D-CERT-157 | **Quiet hours = NONE. 24/7 notification cadence.** Shipping operations are 24/7 — cert expiries don't sleep, compliance risk doesn't pause for office hours. No per-user quiet windows in V1 (or later). Critical alerts (≤7d / expired), regular cadence alerts (90/60/30/14/7/1d), and approval requests all fire on schedule regardless of recipient time-of-day. Users mute via device-level OS controls if needed. Simplifies notification engine (no scheduling/deferred-delivery logic) and aligns with maritime operational reality. | LOCKED |
| D-CERT-158 | **Digest schedule = MONTHLY only, DPA + Marine Sup'tt recipients.** Single monthly fleet compliance digest emailed on **1st of every month at 08:00 ICT** to DPA and Marine Sup'tt only. Contents: expiring-this-month roll-up, overdue acks, approval queue depth, exception report. **No daily digest** (would be noise). **No weekly digest** (still too noisy per PO). **FM not on digest list** (FM consumes ad-hoc reports/dashboard, no scheduled push). **No Master digest** (Master receives per-event cadence alerts as primary mechanism — additional digest would compete for attention with critical alerts). | LOCKED |
| D-CERT-159 | **Failed-delivery / bounce handling = retry 3x exponential backoff + DPA dashboard surface.** Email bounce → automatic retry at 1min / 5min / 30min intervals. Persistent failure (3 retries exhausted) → user's email flagged `delivery_status: bouncing` in user profile; aggregated count surfaced to DPA dashboard ("N users have failing email delivery — review"). **Critical alerts (≤7d expiry / expired) auto-fall-back to Slack DM** if email is in bouncing state — does not wait for DPA to fix. All retry attempts and final outcome captured in audit log per D-CERT-155. | LOCKED |
| D-CERT-160 | **NO per-user notification preferences. Routing is centrally configured by DPA at vessel level.** Users (Master, DPA, Marine Sup'tt, Tech Manager, etc.) cannot personally tune channel preference, mute non-critical, vacation auto-forward, per-vessel mute, per-section mute, or custom escalation thresholds. Instead: **Slack channel routing is set system-wide by DPA — each vessel has its own Slack channel; notifications for that vessel auto-route to the vessel's channel based on cert context.** Office-side notifications go to fleet-wide office channels per role. Per-user inbox tuning is intentionally absent (avoids fragmented notification policy + alert-fatigue gaming). Deputy DPA inheritance (per D-CERT-078) is login/permission-level only — does NOT auto-forward notifications. | LOCKED |

### Interrogation Round 6 — Batch 3/5 (Channel Routing Per-Side, Escalation, Templates, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-161 | **Channel routing = per-side split, clean separation:** **Vessel-side users** (Master, C/O, C/E, 2/E) receive notifications on **in-app (system) + email** ONLY. NO Slack delivery to vessel staff. **Office-side users** (DPA, FM, Marine Sup'tt, Technical Manager, Tech Sup'tt) receive notifications on **in-app (system) + Slack** ONLY. NO email delivery to office staff (Slack replaces email for office). Per-vessel Slack channels (`#certs-vessel-<vessel-name>`) for vessel-context alerts; fleet-wide office channels for fleet/digest content. AMENDS §6.2 channel matrix — email is vessel-only; Slack is office-only. | LOCKED |
| D-CERT-162 | **Escalation cadence = D-CERT-089 wiring with minimal channel-noise principle.** Per-cadence escalation just adds **recipients** (not extra channels per step) on the per-side routing per D-CERT-161. Day 30 → Master + Marine Sup'tt + Technical Manager (vessel side via in-app+email; office side via in-app+Slack). Day 22 no-ack → DPA added. Day 14 no-ack → daily reminders all four. Day 7 no-ack → FM added; critical-only Slack channel ping. Post-expiry → daily until renewed. Statutory/Class certs: DPA + Technical Manager from Day 30 (severity uplift per D-CERT-089). Goal: no excessive channel noise — additional escalation = additional recipients on existing channels, not new channels. | LOCKED |
| D-CERT-163 | **Alert template tone = direct operational for ALL recipients.** Body format: `Cert expiring: <cert name> · Vessel: <vessel> · Expires: <dd-Mmm-yyyy> (in N days) · Action: [Renew] [Acknowledge]`. No formal corporate prose. Maritime professionals — vessel staff and office alike — prefer signal-dense messages. Subject conveys urgency (per D-CERT-153); body delivers data; action buttons (per D-CERT-154 magic links) execute. Same tone across email, Slack, and in-app. | LOCKED |
| D-CERT-164 | **Multi-cert grouping = ALWAYS group, no threshold.** When 2+ certs on the same vessel hit a cadence on the same day, system delivers a **single grouped alert** clearly listing all affected certificates (cert name, expiry date, days-to-go for each). One Slack message, one email, one in-app card. No threshold logic — grouping is always-on for same-vessel-same-day. Reduces inbox volume; gives recipient a complete day-summary in one read. Group title: `<N> certs on <vessel> hit <cadence> mark today`; body lists each cert with action buttons. | LOCKED |
| D-CERT-165 | **Master = vessel-side admin (PSC Inspection pattern); no Master-self-approval gate.** When Master submits a cert renewal for a `master_only` row (per D-CERT-079: Class / Statutory / is_class_tracked rows), Master IS the approver — no `pending_master_approval` state for Master's own submissions. Master submission goes directly to **office reconciliation review** (Marine Sup'tt) and finalizes thereafter. Same UX pattern as PSC Inspection's Master-submitted inspections (`VIMS DOCS/BACKEND_STRUCTURE.md §11.1`). For `all_ranks_with_approval` rows (Equipment, Calibrations, etc.), C/O / C/E / 2/E submissions still gate through Master approval per existing D-CERT-079. **Other state-change notifications (rollback, class snapshot, anniversary change, catalog edit, reconciliation discrepancy) stand as proposed in Q15;** anniversary-date-change notifications include diff (old vs new + list of affected certs whose windows shifted). | LOCKED |

### Interrogation Round 6 — Batch 4/5 (Vessel-Side Cert PDF OCR Pipeline, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-166 | **Vessel-side cert upload sources = PDF + bridge scanner only. NO camera path.** Master uploads renewed certs via two channels: (a) **PDF file** — class society / RO emails the cert as PDF; Master uploads from local file (primary path, modern issuers); (b) **Bridge workstation scanner** — paper certs scanned via the workstation-connected scanner that produces a PDF directly into the upload form. **No phone/tablet camera path** — quality unreliable, glare/angle issues create data-quality risk. If Master has only paper and no working scanner, ops must request electronic copy from issuer. | LOCKED |
| D-CERT-167 | **Master upload UX flow:** (1) Master clicks "Upload renewed cert" on cert card; (2) picks source — PDF file or scanner; (3) system OCRs in real-time, extracts metadata per D-CERT-101 + D-CERT-105; (4) Master sees pre-filled form with extracted values + low-confidence highlights; (5) Master corrects, **save-as-draft supported** (auto-expires after 7 days per D-CERT-076 alignment) so Master can interrupt for nav/ops and resume; (6) submit → for `master_only` rows goes direct to Marine Sup'tt reconciliation per D-CERT-165; for `all_ranks_with_approval` rows from C/O/C/E/2/E submitters, gates through Master per D-CERT-079; (7) old PDF archived per D-CERT-118 supersede pattern; cert row updated; status flips to Current with new expiry. | LOCKED |
| D-CERT-168 | **Vessel-side OCR confidence threshold = STRICTER (≥85% auto-accept).** All vessel uploads (PDF or scanner) use the stricter threshold than office migration ingest (which is ≥80% per D-CERT-106). Rationale: vessel-side uploads update live compliance state — incorrect auto-acceptance carries higher risk than during one-time migration. 60–85% confidence → field shown in gap-fill UI for Master to confirm or correct; <60% → field blank, Master enters manually. Better to make Master verify than auto-accept and discover errors at next class survey. | LOCKED |
| D-CERT-169 | **Class society API integration = OUT OF SCOPE entirely (not V1, not V2, not later).** No class portal API integration with BV MOVE / KR e-Fleet / NK NK-SHIPS / ABS Eagle / RINA / etc. Pure manual upload in perpetuity. Removed from V2 deferrals in §17 (was previously listed). Email-watcher remains V1.1 (already in deferral list — auto-ingest from designated `certs@ksm` inbox is acceptable; that's an inbound-email feature, not class-portal API integration). | LOCKED |
| D-CERT-170 | **Renewal vs. revision auto-detection.** When Master uploads a new PDF for an existing cert row, system compares OCR-extracted expiry date against current cert row expiry: (a) **expiry > current expiry** → propose classification as **Renewal** (advances validity period; old PDF archived as `superseded_at = now()` per D-CERT-118); (b) **expiry == current expiry** → propose classification as **Revision/Correction** (same validity, content corrected — typo, wrong date, scope corrected); Master prompted for revision reason in audit log. Auto-detection shown in gap-fill UI; Master confirms classification before commit. **Fallback:** if OCR fails to extract expiry clearly, modal asks Master "Renewal or Correction?" radio before commit. | LOCKED |

### Interrogation Round 6 — Batch 5/5 (Notification Engine Edge Cases, 2026-05-07) — ROUND 6 COMPLETE

| # | Decision | Status |
|---|---|---|
| D-CERT-171 | **Catalog change fan-out = aggregate office + per-vessel Master.** When DPA adds/removes a cert type affecting fleet: (a) **Aggregate notification** to fleet-office Slack channel — "DPA added/removed cert type X — affects N vessels — review pending uploads in queue"; (b) **Per-vessel ping** — each affected vessel's Master gets email + in-app notification ("New cert type X is required on your vessel; pending upload row created"); office side sees same per-vessel context on Slack + in-app per D-CERT-161 routing. Both fire on the same DPA action. | LOCKED |
| D-CERT-172 | **User role-change notifications = affected user only.** When a user's role/assignment changes (DPA reassigns Marine Sup'tt, Technical Manager, Master rotation, Deputy DPA designation, etc.), system notifies **only the affected user** ("You've been assigned as <role> for vessel X effective <date>"). No fleet-wide noise; no DPA receipt notification (DPA performed the action — they already know). Office dashboards reflect change for ambient awareness. | LOCKED |
| D-CERT-173 | **Vessel go-live = single Master welcome + suppress historical backlog.** On vessel onboarding completion (D-CERT-119/120 step 7 FM sign-off), Master receives a single welcome notification: "Vessel <name> is now live in VIMS Certs. You'll start receiving alerts from now. Tap here for orientation." **Pre-go-live cadence states are NOT replayed** — if a cert already passed its 30-day mark before VIMS knew about it, no retroactive 30-day alert fires; the next forward-looking cadence (14d / 7d / 1d / expired) catches it from go-live onward. Avoids backlog-spam UX disaster at go-live. | LOCKED |
| D-CERT-174 | **Notification idempotency = belt-and-suspenders (app-level key + DB constraint).** Every notification carries an idempotency key `(cert_row_id, cadence, sent_date)`. App layer checks for duplicate dispatch within 24h before sending. DB-level unique constraint on `master_notification(module='certs', cert_row_id, cadence, sent_date)` rejects duplicate inserts silently. Both layers active simultaneously. Protects against server restart, scheduled job re-run, DB recovery scenarios. | LOCKED |
| D-CERT-175 | **Notification audit retention = hybrid 5y metadata + 1y body content.** Notification **metadata** (notification_id, trigger event, recipients, channels, sent timestamp, delivery status, ack status, escalation level — per D-CERT-155) retained for **5 years rolling** matching audit log per D-CERT-099. **Full email body content / Slack message text** retained for **1 year rolling** (after which body is purged but metadata row preserved). Storage savings without compromising compliance evidence (metadata proves delivery + ack; body rarely needed historically). | LOCKED |

### Interrogation Round 7 — Batch 1/5 (Cross-Module Integration — OUT OF SCOPE, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-176 | **Cross-module integration ENTIRELY OUT OF SCOPE for V1.** Certs module operates independently with **no API calls, no shared FKs, and no automated cross-references** to PSC Inspection, CMS (Continuous Machinery Survey, part of PMS module), Reporting (MARPOL/incidents), or Safety modules. Each VIMS module has its own UI, audit log, and export. Workflow integrations like "check IOPP validity from Reporting" are out of scope — users navigate to Certs module manually if they need cert state. **AMENDS D-CERT-022** — V1 is not just loose-coupled, it's NOT coupled at all. Hard-FK V2 design (per §12.2) is deferred indefinitely until a concrete business case emerges; no time-based or feature-driven trigger pre-defined. | LOCKED |
| D-CERT-177 | **Crew certificates (COC, COP, GMDSS, medicals, STCW endorsements, vaccinations) handled by CMS (Crew Management System — a separate platform from VIMS), not VIMS Certs module.** The Certs module has **zero crew personal identifiable information (PII)**. DMLC II row stores the PDF + cert-level metadata (issuer, issue date, expiry) only; does NOT contain crew names, ID numbers, medical info, or any personal data. Crew compliance verification flows through CMS, separate from VIMS. **Significantly narrows GDPR/PDPA scope** for VIMS Certs (Round 7 Batch 3 questions on crew personal data are largely moot). | LOCKED |
| D-CERT-178 | **External auditor access = per-module only (no cross-module bundle, no federated SSO).** Auditor wanting "everything about Vessel X" visits Certs module (login per D-CERT-096), then Reporting, then Safety, etc., separately — each with its own scoped read-only login. No unified "Vessel X Compliance Bundle" tool that aggregates across VIMS modules in V1. Federated SSO across modules is out of scope (would require shared identity infra and is beyond Certs module remit). Auditor compiles complete picture by visiting modules independently. | LOCKED |

### Interrogation Round 7 — Batch 2/5 (Audit Log Governance & Retention, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-179 | **Audit log immutability = DB-level role separation.** PostgreSQL role `vims_app` (used by Django runtime) has only **INSERT + SELECT** GRANTs on `vims_certs_audit_log` and `master_notification` notification rows. Separate `vims_admin` role has full GRANTs but is used **only for migrations** — never at runtime. Belt-and-suspenders against accidental code paths or future direct-DB connections. No additional triggers (D-CERT-176 simplification spirit — no extra complexity unless required). | LOCKED |
| D-CERT-180 | **Audit log redaction for external auditor view.** Free-text reason fields (DPA bulk-delete reason, Master rejection reason, reconciliation discrepancy notes, override reasons) are **redacted to `[REDACTED — internal note]`** when accessed via external-auditor read-only login (per D-CERT-096). DPA + FM see full unredacted content always; Marine/Tech Sup'tt see full for own-vessel scope. Redaction is automatic at the view layer based on viewing-user's role; no manual DPA curation needed. Structured fields (timestamps, user IDs, cert IDs, state transitions) always visible to auditor. | LOCKED |
| D-CERT-181 | **ISM/ISPS/MLC retention overlay = uniform 5y per D-CERT-099 (REAFFIRMED, no per-event overrides).** Audit log retention stays at 5 years rolling for all event types — no special tagging for class-survey events or PSC-related cert events. PDF artifacts in vessel-scoped archive (per D-CERT-148) cover the vessel-lifetime / decadal-class-survey-history need; the audit log is for change-tracking governance, not the canonical historical document store. Same retention rule applies across cert types and event types. | LOCKED |
| D-CERT-182 | **Audit log cascade on catalog row hard-purge = SIMPLE cascade hard-purge.** When a catalog row is hard-purged after retention period, all vessel-instance audit entries referencing that `catalog_id` are **also hard-purged** (cascade delete). Simplest possible model. Trade-off accepted: loses traceability of vessel-instance history beyond catalog row's own retention; mitigated because PDF artifacts (in vessel archive per D-CERT-148) and the catalog row's own audit entries (recording when/why it was deleted) survive separately. No snapshot-embed or orphan-reference complexity. | LOCKED |
| D-CERT-183 | **Audit log storage tiering = hot 2 years + cold 3 years.** Audit entries newer than 2 years live in primary DB (`vims_certs_audit_log`, `master_notification`) for fast query. Entries older than 2 years auto-archive to compressed cold storage (S3 Glacier or equivalent, decision deferred to Phase 0 build). DPA export tool transparently fetches from both tiers (warns user if cold-tier fetch is slow). After 5 years total, entries hard-purge from both tiers per D-CERT-099. Storage costs negligible at fleet scale, but tiering keeps hot DB lean for query performance. | LOCKED |

### Interrogation Round 7 — Batch 3/5 (GDPR/PDPA & Personal Data — narrow scope, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-184 | **Personal data scope = INTERNAL KSM EMPLOYEE DATA ONLY; not shared externally.** Combined with D-CERT-177 (no crew PII — CMS handles that), the personal data footprint of VIMS Certs is limited to: (a) VIMS user accounts (DPA, FM, Marine/Tech Sup'tt, Tech Manager, Master, C/O, C/E, 2/E names + emails — ~30-50 employees); (b) audit log actor names; (c) print user identity in artifact footers; (d) approval/rejection actor logs; (e) notification recipient logs. **Not shared with third parties** — vessel sale handover bundle (D-CERT-093) contains cert PDFs but new owner issues their own new certs post-handover; KSM does not track new-owner personal contact data as ongoing personal data. Issuer signature names on cert PDFs are third-party content incidental to compliance, not VIMS-managed personal data. | LOCKED |
| D-CERT-185 | **GDPR/PDPA Data Subject Rights = NOT APPLICABLE as a formal Certs-module concern.** Internal employment-data context is governed by KSM employment terms + Thai labor law, not formal GDPR DSR procedures. **No self-service DSR UI; no formal DSR SOP** in Certs module. Standard KSM HR/IT processes (account deactivation on departure, etc.) cover the practical needs. If a formal DSR request ever arrives, it's handled at the corporate level via existing HR + Legal channels, not via Certs module tooling. | LOCKED |
| D-CERT-186 | **Right-to-be-forgotten vs. compliance retention conflict = NOT APPLICABLE.** Audit retention (5y per D-CERT-099) is governed by ISM Code + maritime employment context, not by GDPR territorial scope. Departing employees: VIMS account deactivated per existing KSM IT policy; audit log entries retained per maritime compliance regulations (which override any deletion request as a matter of law). No special pseudonymization mechanism in V1. | LOCKED |
| D-CERT-187 | **Data residency = inherits existing VIMS-wide hosting/region policy; NOT a Certs-module decision.** Whatever region/jurisdiction VIMS currently runs in (Thailand or Singapore or wherever existing modules deploy) is inherited by Certs module. Out of Certs module remit to specify. Cross-border-data-transfer compliance handled at corporate IT level for the entire VIMS platform. | LOCKED |
| D-CERT-188 | **Privacy notice & consent = inherits existing VIMS-wide policy.** No Certs-specific privacy notice, no Certs-specific first-login consent acknowledgment. If existing VIMS has corporate-wide privacy notice and consent flow, that covers Certs module by default. If not, Certs module does not introduce a new one. Issuer signature names on cert PDFs handled per D-CERT-184 (third-party compliance content, no consent required). | LOCKED |

### Interrogation Round 7 — Batch 4/5 (Encryption, Keys, Backup, DR — all inherit VIMS-wide policy, 2026-05-07)

| # | Decision | Status |
|---|---|---|
| D-CERT-189 | **Encryption at-rest mechanism = inherits existing VIMS-wide policy.** Whatever current VIMS modules use (full-disk encryption, S3 SSE, RDS encryption, etc.) is inherited by Certs module. §10 already locked AES-256 at-rest and TLS 1.3 in-transit at the policy level; specific implementation (full-disk vs. field-level vs. per-blob) follows VIMS-wide standard. No Certs-module-specific encryption design. | LOCKED |
| D-CERT-190 | **Key management = inherits existing VIMS-wide policy.** Whether VIMS uses AWS-managed keys, customer-managed keys (CMK), or BYOK is determined at the corporate IT level for the entire VIMS platform. Certs module reuses whatever KMS/key infrastructure is already provisioned. No Certs-specific key provisioning, rotation policy, or escrow. | LOCKED |
| D-CERT-191 | **Backup strategy = inherits existing VIMS-wide policy.** DB snapshot frequency, retention duration (daily / weekly / monthly), and offsite-replica targets are all determined at the corporate IT level. Certs module's `vims_certs_*` tables and PDF blob storage are included in the existing VIMS backup scope by default. No Certs-module-specific backup configuration. | LOCKED |
| D-CERT-192 | **Disaster recovery RTO/RPO = inherits existing VIMS-wide policy.** Whatever DR target VIMS-wide currently honors applies to Certs. Operational note: a cert system being down for several hours is manageable (vessels don't lose cert state from local outage, just convenience of querying); Certs does not require a stricter DR target than the rest of VIMS. No Certs-specific hot-standby, regional failover, or DR drill schedule. | LOCKED |
| D-CERT-193 | **PDF blob storage durability + tiering = inherits existing VIMS-wide policy.** Storage class (S3 Standard / Glacier / multi-region) chosen at corporate IT level. Audit log tiering per D-CERT-183 (hot 2y + cold 3y) is the only Certs-specific storage decision; PDF cert blobs follow VIMS-wide blob storage policy. Active cert PDFs and archived/superseded PDFs use whatever durability/tiering pattern other VIMS modules use. | LOCKED |

### Interrogation Round 7 — Batch 5/5 (External Auditor Workflow & Final Compliance, 2026-05-07) — ROUND 7 COMPLETE · INTERROGATION COMPLETE

| # | Decision | Status |
|---|---|---|
| D-CERT-194 | **External auditor access provisioning = Marine Sup'tt self-service (AMENDS D-CERT-096).** Marine Sup'tt — being the primary reconciliation reviewer per D-CERT-039 and typical auditor's main contact — controls external auditor access provisioning via Settings UI: enters auditor name + email + scope (vessel list + doc sections per D-CERT-096) + expiry → system emails auditor a one-time-use signup link. **DPA retains override authority** (can also provision or revoke), but the typical operational path is Marine Sup'tt-driven. Audit log captures every grant action with provisioning user identity per D-CERT-179. | LOCKED |
| D-CERT-195 | **External auditor access revocation = AUTO-EXPIRE ONLY (no early revocation).** Once granted, auditor access runs through to its expiry timestamp without an early-revocation control. Simpler logic; no token-revocation-list (TRL) needed. If a compromise scenario ever materializes (extremely rare given short-grant + scoped pattern), Marine Sup'tt or DPA can shorten the expiry by editing the access record (effectively revoking). Default: no anytime-revoke button. | LOCKED |
| D-CERT-196 | **External auditor activity audit trail = NOT TRACKED.** No per-action logging of what an auditor reads / downloads / prints during their session. Read access is just credentialed access — page views, PDF downloads, search queries, and ZIP exports are NOT individually audit-logged. Information has no operational use; tracking adds storage volume and complexity without value. The grant event itself (who provisioned, scope, expiry) is logged per D-CERT-194; everything within the grant window is opaque. | LOCKED |
| D-CERT-197 | **Auditor attestation tooling = NOT BUILT.** No "Auditor Attestation Form" generator, no read-only auditor note-taking inside VIMS, no system-side attestation export. External auditors produce their own reports per their professional standards using whatever data they accessed via the read-only login (per D-CERT-096 + D-CERT-194). VIMS provides data; auditor produces attestation. Avoids ambiguity about authorship of compliance documents. | LOCKED |
| D-CERT-198 | **Round 7 / Interrogation closeout — no additional compliance topics raised.** Quick-scan checklist confirmed: ISM Code retention (D-CERT-099/181), ISPS/MLC/SOLAS retention (D-CERT-181), audit log integrity (D-CERT-179), cross-module scope (D-CERT-176), crew PII (D-CERT-177), GDPR/PDPA (D-CERT-184–188), encryption / keys / backup / DR (D-CERT-189–193), external auditor workflow (D-CERT-096, D-CERT-194–197), vessel sale handover (D-CERT-093, D-CERT-145), class society APIs out-of-scope (D-CERT-169) — all covered. **Interrogation complete (KLOSS Step 2).** Module proceeds to DocSuite (KLOSS Step 3). | LOCKED |
| D-CERT-199 | **AMENDS D-CERT-079 and D-CERT-165: all active Certs catalog rows use `submission_scope = all_ranks_with_approval`.** Chief Officer, Chief Engineer, and Second Engineer may upload certificate PDFs for any certificate on their own vessel when they hold Certs tracked-item write permission; their uploads enter `pending_master_approval` and require Master approval. Master and office direct uploads still finalize without a Master self-approval gate. Other ship ranks remain upload-blocked unless code-level sub-officer recognition is expanded. | LOCKED |

---

## §16a Resume Point (For Next Session)

**Status:** **INTERROGATION COMPLETE 2026-05-07.** Rounds 1–7 ALL DONE. **199 decisions locked** (D-CERT-001 → D-CERT-199). KLOSS Step 2 finished.

**Next session — KLOSS Step 3: DocSuite generation.**

Same pattern as VIMS-Safety-Module's DocSuite completion (`/Users/prince/Documents/Project reserch/VIMS-Safety-Module/`). Generate the 11-canonical build-ready document suite + COVERAGE.md from this SSOT:

1. **PRD.md** — Feature requirements with FEAT-CERT-* IDs
2. **DATA_MODEL.md** — DB schema (`vims_certs_*` tables) + ER diagram + indexes + constraints
3. **API_CONTRACTS.md** — DRF endpoints, request/response shapes, error codes, RBAC scopes
4. **APP_FLOW.md** — Screen layouts, navigation, user journeys per role (Master / DPA / FM / Marine Sup'tt / Tech Manager / external auditor)
5. **BACKEND_STRUCTURE.md** — Django apps, services, jobs, RBAC matrix, OCR pipeline
6. **FRONTEND_GUIDELINES.md** — React component architecture, hooks, stores, styling
7. **DESIGN_SYSTEM.md** — Tokens, color palette (with status tier colors per D-CERT-136), components, print layout per D-CERT-125–139
8. **VALIDATION_RULES.md** — Field validation, gap-fill UI rules, validation gates per D-CERT-116
9. **IMPLEMENTATION_PLAN.md** — Phase 0 → Phase N build sequence with milestones
10. **TEST_PLAN.md** — Unit / integration / E2E coverage; OCR test fixtures using existing Class Status PDFs
11. **AUDIT_CHECKLIST.md** — Pre-launch ISM/ISPS readiness checklist
12. **COVERAGE.md** — Decision coverage report: every D-CERT-* mapped to which doc(s) cover it

After DocSuite locks GREEN (analogous to Safety's "159/159 100% GREEN" gate), module proceeds to **KLOSS Step 4 — Phase 0 build kickoff**.

**Pre-DocSuite TODO at session start:**
- Reload SSOT into context
- Reload Safety Module DocSuite as reference template
- Reload Reporting Module DocSuite as second reference template
- Decide DocSuite naming convention: `VIMS-Certs-Module/<11 docs>/` directory under project root

**Subsequent Rounds (4–7):**
- Round 4: Migration mechanics (bulk import format, filename conventions, missing-PDF handling)
- Round 5: Print/export fidelity (SQE S 633 column widths, page breaks, header)
- Round 6: Notification engine + cert PDF upload UX (incl. OCR for vessel-side scans deferred from R2 Q1)
- Round 7: Cross-module FK + audit/compliance + GDPR

**Subsequent Rounds (4–7):**
- Round 4: Migration mechanics (bulk import format, filename conventions, missing-PDF handling)
- Round 5: Print/export fidelity (SQE S 633 column widths, page breaks, header)
- Round 6: Notification engine + cert PDF upload UX (incl. OCR for vessel-side scans deferred from R2 Q1)
- Round 7: Cross-module FK + audit/compliance + GDPR

---

## §17 Open Items / V1.1+ Deferrals

| Item | V1.1 / V2 / Later |
|---|---|
| SMS / WhatsApp / Push notifications | V1.1 |
| Email-watcher for auto class snapshot ingestion | V1.1 (after parsers stable) |
| ~~Class portal API integration (BV MOVE / KR e-Fleet / NK NK-SHIPS)~~ — **REMOVED 2026-05-07 per D-CERT-169** | OUT OF SCOPE permanently |
| Mobile companion app | V2 |
| Hard FK cross-module integration | V2 |
| Crew certificates (COC competency, COP, GMDSS, medicals) | Separate Crewing Module |
| External webhook (Slack/Teams) | V3 |
| AI-assisted cert PDF parsing (auto-extract issue/expiry from any uploaded cert) | V2 stretch |

---

## §18 Glossary

| Term | Meaning |
|---|---|
| COC | **Certificate of Class** (the primary class society document confirming vessel is in class). NOT Certificate of Competency (crew). |
| CG2 | Cargo Gear Certificate (5-yearly load test + annual thorough exam) |
| LI | Loading Instrument Certificate |
| RO | Recognized Organization — Class society acting on behalf of Flag administration |
| STC | Short-Term Certificate (bridge cert covering gap to next port) |
| DPA | Designated Person Ashore (ISM Code role; here = system admin for Certs config) |
| FM | Fleet Manager |
| Tech Sup'tt | Technical Superintendent (office) |
| Marine Sup'tt | Marine Superintendent (office) |
| C/O · C/E · 2/E | Chief Officer · Chief Engineer · Second Engineer |
| ESP | Enhanced Survey Programme |
| CSR | Continuous Synopsis Record (NOT Continuous Survey, despite the abbreviation collision) |
| CSR (other) | Continuous Survey Regime — a class-society survey scheme; context disambiguates |
| CMS | **Two distinct meanings — context disambiguates:** (1) **Continuous Machinery Survey** — class-society survey scheme tracked in VIMS PMS module (not VIMS Certs); (2) **Crew Management System** — separate platform from VIMS that handles crew personnel data and crew certificates (COC, COP, GMDSS, medicals, STCW endorsements, vaccinations) per D-CERT-177. VIMS Certs module does NOT integrate with either. |
| ISM SMC | International Safety Management Safety Management Certificate |
| ISPS SSC | International Ship & Port Security Code Ship Security Certificate |
| MLC | Maritime Labour Convention |
| DMLC I/II | Declaration of MLC Compliance Part I (flag) / Part II (company) |
| IOPP | International Oil Pollution Prevention (cert) |
| ISPP | International Sewage Pollution Prevention |
| IAPP / EIAPP | International / Engine Air Pollution Prevention |
| BWM | Ballast Water Management |
| IHM | Inventory of Hazardous Materials |
| IMSBC | International Maritime Solid Bulk Cargoes Code |
| UTN | Unique Tracking Number (KR e-cert identifier) |
| MoU | Memorandum of Understanding (PSC regimes — USCG, Paris MoU, Tokyo MoU) |

---

*End of SSOT v0.1 — awaiting user review before progressing to Step 2 (Interrogation).*
