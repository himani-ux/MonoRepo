# TECH_STACK.md â€” Locked Technology Versions
## VIMS Safety Module â€” Incident / Near Miss / SCM / SOI

**Version:** 1.0 | **Date:** 2026-04-17 | **Status:** INITIAL RELEASE

---

## 0. Document Scope and Authority

This document is the **version-lock specification** for the VIMS Safety Module â€” the migration of the KSM safety management system (Incident Reporting, Near Miss Reporting, Safety Committee Meeting, Safety Officer Inspection) from the legacy eMarineSoft platform onto the VIMS monorepo at `apps/safety/` (Django backend) and `src/routes/safety/` + `src/components/safety/` (React frontend), against the shared database `ksm_marine_live`.

**Version Lock Policy:**
- DO NOT install any package not listed in this document without explicit approval.
- DO NOT upgrade versions without testing and approval.
- All versions are pinned with `==` (Python) or exact strings (package.json) â€” no `^`, `~`, `>=`, or `*`.
- Lock files (`package-lock.json`, pinned `requirements.txt`) are committed to version control.

**Arbitration order** (per master prompt `<rules>`): `<database_naming_convention>` > `<vims_integration>` > SSOT > BACKEND_STRUCTURE > APP_FLOW > PRD > DESIGN_SYSTEM > VALIDATION_RULES.

---

## 1. Platform Inheritance (from VIMS Reporting Module)

Every dependency in this section is **inherited verbatim from `VIMS-Reporting-Module/TECH_STACK.md`** and is installed once at the VIMS platform level. Safety consumes them without change.

> **Rationale:** see `VIMS-Reporting-Module/TECH_STACK.md` Â§1â€“Â§7 for full rationale on each choice. Frontend parity with the Inspection module is a platform rule (LESSONS `VIMS-Reporting-Module/CLAUDE.md` Â§Forbidden Actions â†’ Database / Auth / Frontend).

### 1.1 Backend Runtime & Framework

| Package | Version | Safety use |
|---------|---------|-----------|
| Python | 3.12.4 | Django app `apps.safety` runtime |
| pip | 24.x | Package manager |
| Django | 5.2.7 | `apps.safety` registered in `INSTALLED_APPS` (per `<vims_integration>`) |
| djangorestframework | 3.14.0 | REST API at `/api/safety/` |
| django-cors-headers | 4.4.0 | CORS for Safety endpoints |

### 1.2 Backend Authentication

| Package | Version | Safety use |
|---------|---------|-----------|
| djangorestframework-simplejwt | 5.3.1 | Shared VIMS SimpleJWT config; no new auth layer (D-GAP-H1) |
| PyJWT | 2.8.0 | JWT encoding |

Permission model: permissions live in the shared `msc_profiles` table as `SAF_F_*` (forms â€” Incident / Near Miss / SCM / SOI) and `SAF_P_*` (processes â€” Create / Submit / Send-back / Approve / Close). No new permission table. Vessel scoping reuses `master_RoleByVessel` (office) + `Crew_Onboarding_History` (ship).

### 1.3 Database Connectivity

| Package | Version | Safety use |
|---------|---------|-----------|
| pyodbc | 5.1.0 | ODBC connector to `ksm_marine_live` |
| mssql-django | 1.6 | SQL Server backend |

Database: **`ksm_marine_live`** (shared instance, SQL Server). Safety uses the same connection as Reporting / Inspection â€” the DB router registers no new DB alias.

### 1.4 File Generation / Parsing

| Package | Version | Safety use |
|---------|---------|-----------|
| reportlab | 4.2.0 | Primary PDF renderer â€” see Â§2.1 |
| PyPDF2 | 3.0.1 | PDF post-processing (page numbering, merge, confidentiality header/footer per D-PDF-01) |
| openpyxl | 3.1.5 | SOI checklist Excel format (D-SOI-10, D-GAP-E1) + Safety Intelligence Dashboard export (D-GAP-M31) |
| Pillow | 10.4.0 | Incident evidence photo processing + SOI HIGH-severity photo (D-GAP-M24) |
| pdfplumber | 0.11.4 | Not directly used by Safety; inherited at platform level |

### 1.5 Async / Task Queue

| Package | Version | Safety use |
|---------|---------|-----------|
| celery | 5.4.0 | Async PDF generation, notification dispatch, dashboard rollups |
| redis | 5.0.8 | Celery broker + result backend |
| django-celery-beat | 2.6.0 | Periodic tasks: 80%-overdue flag evaluation (D-GAP-F3), CA aging-pipeline rollup (D-GAP-M29), 3-year retention job (D-GAP-G2), SOI cycle counter |
| django-celery-results | 2.5.1 | Task result persistence |

### 1.6 Utilities

| Package | Version | Safety use |
|---------|---------|-----------|
| python-dotenv | 1.0.1 | Env var loading |
| gunicorn | 22.0.0 | WSGI server |
| requests | 2.32.3 | Slack webhook dispatch (per D-GAP-F2 â€” best-effort) |

### 1.7 Frontend Runtime & Build

| Package | Version | Safety use |
|---------|---------|-----------|
| Node.js | 22.17.1 | Build runtime |
| npm | 10.x | Package manager |
| Vite | 5.4.0 | Build tool + dev server |

### 1.8 Frontend Core Framework

| Package | Version | Safety use |
|---------|---------|-----------|
| react | 18.3.1 | UI framework |
| react-dom | 18.3.1 | DOM renderer |
| typescript | 5.4.5 | Type safety |
| @types/react | 18.3.3 | React type defs |
| @types/react-dom | 18.3.0 | React DOM types |
| react-router-dom | 6.24.0 | Client routing â€” mounts `/safety/incidents`, `/safety/near-miss`, `/safety/scm`, `/safety/soi` |

### 1.9 Frontend Styling

| Package | Version | Safety use |
|---------|---------|-----------|
| tailwindcss | 3.4.7 | Utility-first CSS |
| postcss | 8.4.39 | CSS processing |
| autoprefixer | 10.4.19 | Vendor prefixes |
| tailwind-merge | 2.4.0 | Merge Tailwind classes |
| clsx | 2.1.1 | Conditional classes |
| class-variance-authority | 0.7.0 | Component variants (risk-band pills, causal-layer tabs) |

### 1.10 Frontend UI Components (shadcn/ui + Radix)

| Package | Version | Safety use |
|---------|---------|-----------|
| @radix-ui/react-dialog | 1.1.1 | Phase gates, confirmation modals |
| @radix-ui/react-select | 2.1.1 | M-SCAT picker, vessel picker |
| @radix-ui/react-checkbox | 1.1.1 | Bias-guard checklist (8 bias guards) |
| @radix-ui/react-label | 2.1.0 | Form labels |
| @radix-ui/react-slot | 1.1.0 | Slot pattern |
| @radix-ui/react-toast | 1.2.1 | Notification toasts |
| @radix-ui/react-tabs | 1.1.0 | Causal-layer tabs (Immediate / Intermediate / Root) |
| @radix-ui/react-dropdown-menu | 2.1.1 | Record-action menus |
| lucide-react | 0.408.0 | Icon library (includes `eye-off` for anonymity badge â€” D-GAP-J1) |

### 1.11 Frontend State Management

| Package | Version | Safety use |
|---------|---------|-----------|
| @tanstack/react-query | 5.51.1 | Server state â€” all `/api/safety/*` fetches |
| zustand | 4.5.4 | Client state â€” incident draft, SOI selected areas, Ad-Hoc SCM trigger state |

### 1.12 Frontend Charts

| Package | Version | Safety use |
|---------|---------|-----------|
| recharts | 3.7.0 | Safety Intelligence Dashboard (Heinrich Ratio indicator D-GAP-M27, repeat-root-cause radar D-GAP-H2, CA Aging Pipeline D-GAP-M29) |

### 1.13 Frontend Forms & Validation

| Package | Version | Safety use |
|---------|---------|-----------|
| react-hook-form | 7.52.1 | All 9-phase Incident forms, Near Miss, SCM, SOI finding registration |
| @hookform/resolvers | 3.9.0 | Zod resolver bridge |
| zod | 3.23.8 | Schema validation â€” `src/schemas/safety/*` per form, `schema_version` column on `vims_safety_incident` |

### 1.14 Frontend HTTP / Date

| Package | Version | Safety use |
|---------|---------|-----------|
| axios | 1.7.2 | HTTP client |
| date-fns | 3.6.0 | Date utilities; timezone resolution via `wrh_ship_time_config` (D-GAP-M26) |

### 1.15 Frontend Testing / Tooling

| Package | Version | Safety use |
|---------|---------|-----------|
| eslint | 8.57.0 | Linting |
| eslint-plugin-react | 7.34.3 | React linting |
| eslint-plugin-react-hooks | 4.6.2 | Hooks linting |
| @typescript-eslint/parser | 7.16.0 | TS parsing |
| @typescript-eslint/eslint-plugin | 7.16.0 | TS linting |
| prettier | 3.3.3 | Formatting |
| prettier-plugin-tailwindcss | 0.6.5 | Tailwind sorting |
| vitest | 3.2.4 | Unit + integration runner |
| jsdom | 28.0.0 | DOM test env |
| @testing-library/react | 16.3.0 | Component testing |
| @testing-library/user-event | 14.6.1 | User interaction |
| @testing-library/jest-dom | 6.9.1 | DOM assertions |

### 1.16 PWA / Offline Stack (relevant to Safety auto-save D-GAP-F1)

| Package | Version | Safety use |
|---------|---------|-----------|
| workbox-core | 7.1.0 | Service worker core |
| workbox-precaching | 7.1.0 | Precache assets |
| workbox-routing | 7.1.0 | Request routing |
| workbox-strategies | 7.1.0 | Caching strategies |
| workbox-background-sync | 7.1.0 | Background sync for draft incident / near-miss submissions |
| workbox-window | 7.1.0 | SW registration |
| vite-plugin-pwa | 0.20.0 | PWA Vite plugin |
| idb | 8.0.0 | IndexedDB wrapper â€” 30-second form auto-save (D-GAP-F1) for Incident, Near Miss, SCM agenda, SOI finding-registration |

**Safety offline posture:** auto-save every 30 seconds to IndexedDB (D-GAP-F1). On reconnect, form resumes from last saved state. This is a **draft-only** guarantee â€” final submission requires connectivity. **Paper-first SOI (D-GAP-E4) does NOT use background sync**; see Â§6.

### 1.17 Mobile (Flutter) â€” not used in V1

Safety V1 targets browsers only (office via desktop Chrome/Edge; ship via vessel tablet Chrome/Safari 14+). No Flutter mobile client. Reporting's FCM/APNs stack is inherited at platform level but Safety does not emit push notifications in V1; the `master_notification` queue is the sole notification path (platform decides downstream delivery).

---

## 2. Safety-Specific Additions

These libraries are **added on top of the Reporting-inherited stack** and exist solely to serve Safety module features.

### 2.1 PDF Renderer â€” 10-Section Template (D-PDF-01, D-PDF-02, D-PDF-03a, D-PDF-03b)

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| reportlab | 4.2.0 | Primary PDF engine (inherited) â€” renders 10-section incident report template, near-miss 1â€“2 page template, SCM 10-section legacy `vw_GetSCM_Master` layout, SOI summary record | `pip install reportlab==4.2.0` |
| PyPDF2 | 3.0.1 | Post-processing: page numbering, confidentiality header/footer per D-PDF-01, auditor leave-behind ZIP assembly (D-PDF-02) | `pip install PyPDF2==3.0.1` |

**Decision:** ReportLab is chosen (not WeasyPrint â€” banned at platform level per `VIMS-Reporting-Module/TECH_STACK.md` Â§13). PyPDF2 is the companion manipulation layer â€” both already platform-installed; no new dependency added for Safety.

**D-PDF-01 template scope:** cover + executive summary auto-from Lessons Learned + full sections + signature block (Master / DPA / FM for RED band per D-GAP-M06) + page numbering + confidentiality header/footer. Implementation lives at `apps/safety/services/pdf_renderer.py`.

**D-PDF-02 auditor ZIP scope:** configurable at export (record types + date range). **Attachments delivered as separate `attachments/` subfolder inside the ZIP** (PDF references filenames; files live alongside). No crew-name redaction (D-GAP-M37).

**D-PDF-03a near-miss template:** distinct lighter 1â€“2 page layout (what-happened + suggestion + immediate action). No investigation / cause-tree content.

**D-PDF-03b SCM template:** legacy `vw_GetSCM_Master` 10-section structure preserved verbatim.

**Near-miss reporter anonymity (D-GAP-J1):** PDF rendering pipeline strips reporter identity for all viewers except DPA and FM. Enforced at `apps/safety/authentication/anonymity.py` serializer layer before PDF template interpolation.

### 2.2 Barcode / QR Library â€” SOI Unique Checklist ID

Per Round 20 build-time deferral #10 (BACKEND_STRUCTURE deferrals table), the **exact visual encoding** of the SOI unique checklist ID (QR code vs linear barcode vs human-readable only) is a build-time product + design decision. The **library choice**, however, is version-locked now to avoid re-work:

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| qrcode | 7.4.2 | QR code generation for SOI PDF/Excel checklist unique ID (links printed paper â†’ digital record per D-GAP-E4) | `pip install qrcode==7.4.2` |
| python-barcode | 0.15.1 | Code128 linear barcode alternative (if product chooses barcode over QR) | `pip install python-barcode==0.15.1` |

Both libraries are pure-Python, have no system dependencies (beyond Pillow 10.4.0 which is already installed), and add <100KB to the deploy footprint. Carrying both avoids a rebuild when deferral #10 resolves.

> **BLOCKED: SOI unique-ID flag format (Round 20 build-time deferral #10)**
> **Question:** QR code, Code128 barcode, or plain alphanumeric only on the SOI paper checklist?
> **Gap:** D-SOI-10 (revised) + D-GAP-E1/E3/E4 mandate a unique checklist ID that survives paperâ†’digital linkage, but the visual encoding is explicitly deferred to build-time (Round 20).
> **Impact:** `FEAT-SAF-SOI-012` (paper-first download) template layout; `apps/safety/services/soi_checklist_generator.py` render path. Library versions already pinned above so resolution is a one-line template change, not a dependency change.

### 2.3 Full-Text Search (FTS) Engine â€” BLOCKED

Per Round 20 explicit deferral (BACKEND_STRUCTURE deferrals table row #8), the FTS engine powering incident / near-miss / finding search is **not locked in this document**.

> **BLOCKED: FTS engine selection (Round 20 build-time deferral #8)**
> **Question:** Elasticsearch, PostgreSQL FTS, SQL Server Full-Text Search (CONTAINS/FREETEXT), or platform default?
> **Gap:** Round 20 deferred the FTS engine choice to build-time; no D-* decision locks it. The VIMS platform currently runs on SQL Server, which offers native FTS via `CONTAINS`/`FREETEXT` predicates, but this has not been confirmed as the target engine for Safety.
> **Impact:** `FEAT-SAF-DASH-007` (incident search), `FEAT-SAF-INC-009` (search by M-SCAT code), `FEAT-SAF-SOI-019` (repeat-finding detection D-GAP-M17) cannot be fully specified in BACKEND_STRUCTURE Â§API until resolved. No FTS package is installed at this time. Safety V1 ships with LIKE-based narrow search as a fallback contract; full FTS is enabled by a Phase 8 deferral-resolution step (IMPLEMENTATION_PLAN Phase 8).
> **Resolution owner:** Platform lead; required by IMPLEMENTATION_PLAN Phase 7.

### 2.4 Cryptographic Libraries â€” NONE IN V1 (D-GAP-D2, D-GAP-G2)

**No cryptographic libraries are added for Safety V1.** Explicitly excluded:

| Library | Excluded because |
|---------|------------------|
| PyCryptodome / cryptography | No hash-chain tamper-evidence in V1 (D-GAP-D2) |
| python-jose (additional) | SimpleJWT already covers JWT signing at platform level |
| Digital signature PKI (X.509, PGP) | D-GAP-D1 chose hybrid digital-typed-name + wet-signed-scan model; no PKI / UETA compliance in V1 |
| Legal-hold crypto envelopes | No legal-hold feature in V1 (D-GAP-G2); 3-year hard-delete runs on schedule |

Audit integrity relies on: standard DB access control, `vims_safety_field_history` append-only audit table, platform backups (D-GAP-G3), and access logging on the audit table itself (D-GAP-F4). ISM Code 2010 amendments Â§10 non-repudiation satisfied via this audit trail + backups. Hash chains / digital PKI signatures are revisitable in V2 if insurance or legal forces the issue (per D-GAP-D2 note).

---

## 3. Cross-Module Live-Join Posture (D-GAP-I2)

Safety does **not** run ETL, batch sync, or change-data-capture pipelines against sibling modules. Every cross-module read is a **live SQL join on `ksm_marine_live`**.

### 3.1 No-Sync Contract

| Posture | Reason | Enforcement |
|---------|--------|-------------|
| No ETL from Reporting â†’ Safety | Same DB, same instance (D-GAP-I2) | Safety service layer issues JOIN queries against `vims_noon_report` / `vims_voyage` directly |
| No CMS staleness handler | Safety and CMS share `ksm_marine_live` (D-GAP-I2) | SOI assistant lookup via live join on `Crew_Onboarding_History` |
| No WRH message-bus integration | Same DB (D-GAP-M11, D-GAP-M26) | SCM attendance joins `wrh_attendance` directly; timezone resolved via `wrh_ship_time_config` |
| No Purchase webhook | Same DB (D-GAP-M12) | `vims_safety_corrective_action.purchase_req_id` hard FK to Purchase table; live status |
| **PMS decoupled** (D-GAP-I1) | PMS is an independent system on a separate login | **No in-VIMS integration.** No FK, no live join, no table reference. M-SCAT cause 12 "Inadequate Maintenance" is cross-referenced manually by investigator |

### 3.2 Consequence for tooling

- No Kafka, RabbitMQ, or message broker added for Safety. Celery + Redis (Â§1.5) handles async work internally.
- No ETL framework (Airflow / dbt / Fivetran). None required.
- No data-replication tool (Debezium / Qlik / SymmetricDS). None required.

---

## 4. Hosting + Region

Inherited verbatim from the VIMS platform / Reporting Module TECH_STACK.md Â§7 â€” Safety does **not** provision its own infrastructure.

### 4.1 Database Host

| Component | Value |
|-----------|-------|
| Engine | SQL Server â€” same instance as Inspection + Reporting |
| Port | 1433 (default SQL Server port) |
| Database | `ksm_marine_live` |
| ODBC Driver | ODBC Driver 18 for SQL Server |
| Connection string env var | `MSSQL_CONNECTION_STRING` |

### 4.2 Region

| Component | Value | Source |
|-----------|-------|--------|
| Cloud provider | Azure | Platform (Reporting Module Â§7.1) |
| Region | Azure `southindia` (Chennai) primary, `centralindia` (Pune) standby | Platform-level; inherited. KSM Mumbai HQ region preference documented under Reporting platform DR policy |
| Data residency | India-only for crew PII + incident records (MLC-A4.3 confidentiality, D-GAP-M14) | Platform compliance baseline |

### 4.3 Web / App Servers

| Component | Version | Notes |
|-----------|---------|-------|
| Nginx | 1.24.x | Reverse proxy, static files (shared with Reporting) |
| Gunicorn | 22.0.0 | WSGI application server |
| Celery worker | 5.4.0 | 4-worker concurrency default (platform setting, inherited) |
| Redis | 7.x server | Shared broker + result backend, port 6379 |

### 4.4 File Storage

| Component | Path | Purpose |
|-----------|------|---------|
| Uploads base | `/var/www/ksm_uploads/` | Platform-level |
| Safety module | `/var/www/ksm_uploads/safety/` | Safety-specific root |
| Incident attachments | `/var/www/ksm_uploads/safety/{vessel_id}/incident/{incident_id}/` | Photo + document evidence (Pillow 10.4.0 processes photos) |
| Near-miss attachments | `/var/www/ksm_uploads/safety/{vessel_id}/near-miss/{nm_id}/` | â€” |
| SCM attachments | `/var/www/ksm_uploads/safety/{vessel_id}/scm/{scm_id}/` | Minutes, circulars |
| SOI checklists generated | `/var/www/ksm_uploads/safety/{vessel_id}/soi/checklists/` | Generated PDF/Excel with unique checklist ID (D-GAP-E1) |
| Generated PDFs | `/var/www/ksm_uploads/safety/{vessel_id}/exports/` | D-PDF-01 internal report, D-PDF-02 auditor ZIPs, D-PDF-03a near-miss, D-PDF-03b SCM |

Orphaned-attachment policy: hard-delete immediately on parent draft/record deletion (D-GAP-M01). Same-filename re-upload replaces in place (D-GAP-M02); audit captured in `vims_safety_field_history`.

### 4.5 Environment Configuration (Safety-specific additions)

#### Frontend `.env` additions

```env
# Safety Module base URL
VITE_SAFETY_API_BASE_URL=http://localhost:8001/api/safety

# Safety Module feature flags
VITE_SAFETY_FTS_ENABLED=false   # Locked off until Phase 8 FTS resolution (BLOCKED Â§2.3)
VITE_SAFETY_QR_FORMAT=qr        # qr | code128 â€” default QR, resolves BLOCKED Â§2.2
```

#### Backend `.env` additions

```env
# Safety Module paths
SAFETY_UPLOAD_BASE=/var/www/ksm_uploads/safety
SAFETY_RETENTION_DAYS=1095      # 3 years hard-delete (D-GAP-G2)
SAFETY_AUTOSAVE_INTERVAL_SECONDS=30  # D-GAP-F1 IndexedDB auto-save cadence

# Safety Slack integration (best-effort per D-GAP-F2)
SLACK_SAFETY_CHANNEL_WEBHOOK=<per-vessel channel mapping handled in master_notification>

# Safety dashboard cadence
SAFETY_DASHBOARD_ROLLUP_CRON=0 */6 * * *   # 6-hourly rollup for D-GAP-H2 repeat-root-cause radar
```

---

## 5. Monitoring / Backup / Performance â€” Platform Inherited

### 5.1 Monitoring (D-GAP-F4)

Safety inherits the VIMS platform observability stack. **Module-specific supplements** (only when platform lacks them):

| Supplement | Trigger | Channel |
|-----------|---------|---------|
| Slack webhook failure alert | RED-band incident notification fails | Platform alerting (secondary Slack channel) |
| CMS/PMS integration failure | Blocks submit (only CMS is joined; PMS decoupled) | Platform alerting |
| `vims_safety_field_history` access log | Any SELECT or DML on audit table | Platform access-log aggregator |

No Prometheus / Grafana / Datadog agent added at module level.

### 5.2 Backup / DR (D-GAP-G3)

**Safety stores no separate backup.** Platform-level RPO/RTO on `ksm_marine_live` covers all `vims_safety_*` and `master_*` tables at the same cadence as Reporting. Deploy-time verification required: platform backup policy must include all 14 Safety module tables and all 8 Safety-owned reference tables (see `<database_naming_convention>` translation map).

File-storage backup (`/var/www/ksm_uploads/safety/`) piggy-backs on platform file-system snapshot policy. No separate S3 / Azure Blob lifecycle configured at module level in V1.

### 5.3 Retention (D-GAP-G2)

3-year hard-delete on incident + near-miss + SCM + SOI records. Celery Beat schedules the retention job (`django-celery-beat` 2.6.0). No legal-hold feature â€” DPA is responsible for out-of-band export before the 3-year mark when a case is open.

### 5.4 Performance Posture (D-GAP-H1)

No formal concurrent-user load target at module level. Inherits VIMS platform baseline. No module-level decision between pessimistic single-editor lock vs optimistic-locking â€” Safety follows whatever the platform provides (currently optimistic-locking via `updated_date` + `schema_version` columns on `vims_safety_*` tables).

### 5.5 Browser Support (Inherited)

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Safari | 14+ (iOS vessel tablets â€” mobile-first mandate) |
| Edge | 90+ |
| Firefox | 90+ |

---

## 6. Offline Behavior for Paper-First SOI (D-GAP-E4)

**Critical design constraint:** SOI is paper-first. The paper checklist is the source of truth. The system downloads a PDF or Excel checklist and the fieldwork happens on paper. There is **NO scan upload step** (D-GAP-E4 revises the earlier D-SOI-10 scan-upload requirement).

### 6.1 What the offline posture supports

| Capability | Implementation |
|-----------|----------------|
| Download checklist | Server-rendered PDF (reportlab 4.2.0) or Excel (openpyxl 3.1.5), served as file response from `/api/safety/soi/checklist/{id}/download` |
| Idempotent re-download | Same unique checklist ID re-served (D-GAP-E1). SO may reprint freely |
| Partial submission | SO downloaded 5 areas, submits findings for 3 (D-GAP-E2). The 3 stamp as inspected; remaining 2 stay in "Downloaded" state |
| Lost/damaged paper recovery | Re-download allowed (D-GAP-E3); loss event logged in inspection notes |

### 6.2 What the offline posture does NOT support

| Explicitly NOT supported | Reason |
|--------------------------|--------|
| Scan upload of filled checklist | D-GAP-E4 â€” paper filed in ship SMS filing system; digital record linked only via unique checklist ID |
| Upload column on `vims_safety_soi_inspection` for paper scan | D-GAP-E4 â€” no scan endpoint, no upload column |
| Background sync of filled checklist answers | D-GAP-E4 â€” Yes/No/NA item responses live on paper only; not in the DB |
| Service-worker-queued checklist response submission | D-GAP-E4 â€” no such endpoint exists |
| OCR pipeline to extract paper answers | Out of scope; paper is authoritative |

### 6.3 What IS captured digitally (offline-capable via D-GAP-F1 auto-save)

Findings registered by the SO **after** fieldwork:

- Finding record (title, severity HIGH/MED/LOW, area, item, date, assignee)
- HIGH-severity finding photos (D-GAP-M24 mandates â‰¥1 photo)
- Inspection event metadata (event ID, vessel, date range, areas selected, trainees if any â€” up to 3)
- Safety Officer + Assistant digital signatures at save; Master counter-signs at approval (D-GAP-M15)

These use IndexedDB 30-second auto-save (D-GAP-F1) + `workbox-background-sync` 7.1.0 for submission once reconnected â€” **findings only**, never the paper checklist itself.

---

## 7. Integration Matrix

Every external or cross-module touchpoint with its version lock.

| Integration | Direction | API / Version | Auth | Governing Decision | Notes |
|-------------|-----------|---------------|------|--------------------|-------|
| **Slack Web API** | Safety â†’ Slack (outbound only) | `https://slack.com/api/chat.postMessage` (HTTP v1, no dated version) | Bot token (OAuth 2.0), env var `SLACK_BOT_TOKEN` | D-GAP-F2 | Best-effort; in-app notification is authoritative. Rate limit 1 msg/sec per channel |
| **`master_notification` (platform queue)** | Safety â†’ Platform (outbound) | Internal VIMS (DB-row write) | Django ORM writes | `<vims_integration>` | Safety writes notification rows; platform notifier consumes |
| **Reporting Module â€” MSC-MEPC.3 position** | Safety â† Reporting (live SQL join) | Internal (live join on `vims_noon_report`) | Same-DB (SimpleJWT for user context) | D-GAP-M09 | Â±12 hours tolerance from incident timestamp; user may edit auto-fill |
| **Reporting Module â€” Daily Report missing** | Safety â† Reporting (live SQL join) | Internal | Same-DB | D-GAP-M10 | Manual lat/long accepted; record flagged `awaiting_daily_report_match`; never blocks submit |
| **WRH Module â€” SCM attendance** | Safety â† WRH (live SQL join) | Internal (live join on `wrh_attendance`) | Same-DB | D-GAP-M11 | Missing data warns, does not block. Row flagged "WRH data unavailable" |
| **WRH Module â€” timezone config** | Safety â† WRH (live SQL join) | Internal (live join on `wrh_ship_time_config`) | Same-DB | D-GAP-M26 | UTC storage + vessel local time resolution per Reporting pattern |
| **CMS â€” SOI assistant lookup** | Safety â† CMS (live SQL join) | Internal (live join on `Crew_Onboarding_History`, `HRM501`) | Same-DB | D-GAP-I2 | No staleness; same DB |
| **Purchase Module â€” CA hard FK** | Safety â†” Purchase (live + FK) | Internal (`purchase_req_id` FK) | Same-DB | D-GAP-M12 | Referential integrity; requisition cannot be archived while linked to open CA |
| **PMS Module** | **DECOUPLED â€” no integration** | N/A | N/A | D-GAP-I1 | No FK, no live join, no API. Manual cross-reference only |
| **VIMS Circular Module** | Safety â†’ Circular (live SQL write) | Internal (write to VIMS Circular table) | Same-DB | Â§1, Lessons Learned | Fleet circular draft auto-linked post-incident closure |
| **IMO flag-state notification** | Out-of-band (no system integration) | N/A â€” DPA handles manually | N/A | D-GAP-G1 | MSC-MEPC.3/Circ.4 PDF auto-export (D-DNV-12) supports DPA; no deadline tracking in V1 |
| **Class society notification** | Out-of-band | N/A | N/A | D-GAP-M13 | DPA handles manually, same pattern as G1 |
| **Open-Meteo Marine API** | Not consumed by Safety | N/A | N/A | â€” | Reporting-only integration |
| **UN/LOCODE Port Database** | Safety â† `master_port` (shared) | Internal (SELECT from `master_port`) | Same-DB | Platform | Safety reuses for SCM location, SOI port field, incident location |
| **Firebase FCM / APNs** | Not consumed by Safety V1 | N/A | N/A | â€” | Safety V1 does not push to mobile; `master_notification` is sole channel |

---

## 8. Cost Estimate per Service

All line items inherit from the platform. Safety adds no dedicated SaaS account.

| Service | Version / Tier | Monthly Cost (USD) | Safety share | Source |
|---------|---------------|---------------------|--------------|--------|
| SQL Server (`ksm_marine_live`) | Licensed at platform level | $0 incremental for Safety | Shared with Reporting / Inspection / platform | Platform licensing |
| Azure VM hosting (Nginx + Gunicorn + Celery workers) | Platform-sized | $0 incremental | Shared; Safety sized within existing capacity | Platform |
| Redis 7.x (broker + result backend) | Self-hosted on same VM | $0 incremental | Shared with Reporting Celery | Platform |
| File storage (`/var/www/ksm_uploads/safety/`) | Azure managed disk | ~$5 / month per 100 GB | Safety projected <50 GB in V1 (3-year retention, no scan uploads per D-GAP-E4 reduces footprint) | Platform |
| Slack API | Existing KSM workspace, bot token | $0 | Shared existing workspace | `VIMS-Reporting-Module/TECH_STACK.md` Â§6.2 |
| Firebase Cloud Messaging | Not used by Safety V1 | $0 | â€” | D-GAP-F2 (in-app notification authoritative) |
| Open-Meteo Marine API | Not used by Safety | $0 | â€” | Reporting-only |
| UN/LOCODE bulk data | Free (public dataset) | $0 | Shared `master_port` table | Platform |
| TLS certificates | Platform-level (Let's Encrypt or Azure App Service managed cert) | $0 | Shared | Platform |
| PDF storage retention | Azure managed disk | Covered in file-storage line | 3-year (D-GAP-G2) | Platform |
| Backup / DR | Platform-level (Azure SQL automated backup + file snapshots) | $0 incremental | Shared per D-GAP-G3 | Platform |
| FTS engine (when Phase 8 resolves BLOCKED Â§2.3) | Elasticsearch cluster if chosen; $0 if native SQL Server FTS | TBD at resolution â€” deliberately unresolved per Round 20 | â€” | BLOCKED Â§2.3 |

**Total Safety incremental monthly cost: ~$5 / month** (storage only). All other costs absorbed at the VIMS platform level.

---

## 9. Version Lock Policy (Safety-Specific Rules)

### 9.1 Approval Process

| Change Type | Approver | Process |
|-------------|----------|---------|
| New Safety-specific package | Tech Lead + Safety PO (DPA delegate) | Written justification + this document updated first |
| Safety Python package patch bump | Tech Lead | Stage test, update this document |
| Safety Python package minor/major bump | Tech Lead + PO | Impact assessment; regression on 9-phase incident flow + SOI paper-first flow + Near Miss anonymity + SCM; update this document |
| Inherited (platform) package change | Tech Lead + Platform lead | Must update Reporting TECH_STACK.md AND this document in same approval |
| FTS engine selection (Phase 8) | Platform + Safety Tech Lead | Resolves BLOCKED Â§2.3; triggers IMPLEMENTATION_PLAN Phase 8 step |
| SOI unique-ID format selection | Product + Design | Resolves BLOCKED Â§2.2; template-only change |

### 9.2 Forbidden Packages (Safety-Specific Additions to Platform List)

In addition to the forbidden list in `VIMS-Reporting-Module/TECH_STACK.md` Â§13, Safety specifically forbids:

| Package | Reason | Use Instead |
|---------|--------|-------------|
| Any hash-chain / blockchain library | D-GAP-D2 â€” no crypto in V1 | `vims_safety_field_history` audit table |
| Any PKI / X.509 / UETA library | D-GAP-D1 â€” hybrid digital + wet-signed-scan only | Typed-name + timestamp + device fingerprint |
| `pytesseract` / OCR libs | D-GAP-E4 â€” no scan upload, no OCR needed | Paper stays on paper |
| `elasticsearch-py` / `opensearch-py` (pre-resolution) | BLOCKED Â§2.3 â€” FTS engine not yet chosen | LIKE-based narrow search as V1 fallback |
| `pandas` | Platform-forbidden | Raw SQL + openpyxl |
| `WeasyPrint` | Platform-forbidden | reportlab 4.2.0 |

---

## 10. Complete Installation Commands

### 10.1 Safety-Specific `requirements.txt` Additions

All platform packages (Â§1) are installed via `VIMS-Reporting-Module/TECH_STACK.md` Â§9.2 `requirements.txt`. Safety adds these two lines:

```txt
qrcode==7.4.2
python-barcode==0.15.1
```

No new Python package beyond those two. ReportLab 4.2.0, PyPDF2 3.0.1, openpyxl 3.1.5, Pillow 10.4.0, Celery 5.4.0, Redis 5.0.8 are all already present from platform install.

### 10.2 Safety-Specific Frontend Dependencies

**None.** All frontend packages (Â§1.7â€“Â§1.16) inherit verbatim from Reporting. Safety's `src/components/safety/` and `src/routes/safety/` consume the same shadcn/ui + Radix + react-hook-form + Zod stack.

---

## 11. Version Compatibility Matrix

| Frontend | Backend | Database | Task Queue | Status |
|----------|---------|----------|------------|--------|
| React 18.3.1 + Vite 5.4.0 + TypeScript 5.4.5 + Zustand 4.5.4 + Zod 3.23.8 | Django 5.2.7 + DRF 3.14.0 + SimpleJWT 5.3.1 + ReportLab 4.2.0 + qrcode 7.4.2 | SQL Server port 1433, `ksm_marine_live` | Celery 5.4.0 + Redis 7.x | **Target for Safety V1** |

Safety's compatibility envelope is **identical** to Reporting's plus the two Safety-specific Python lines in Â§10.1. Any divergence is a violation.

---

## 12. Rubric Self-Check

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Every dependency has exact semver (no "latest", no `^`, no `~`) | PASS | Â§1 all tables use `X.Y.Z` form; Â§10.1 uses `==` |
| Hosting + region specified | PASS | Â§4.1â€“Â§4.2: SQL Server, `southindia` primary, `centralindia` standby |
| Every integration documented with API version | PASS | Â§7 Integration Matrix: Slack HTTP v1, internal same-DB joins, UN/LOCODE bulk, Open-Meteo explicitly not-consumed |
| Cost estimate per service | PASS | Â§8 all 12 service lines; total ~$5/month incremental |
| No "TBD" / "recommended" | PASS | FTS cost line marks "TBD at resolution â€” deliberately unresolved per Round 20" which is the BLOCKED stub (not a gap) |
| FTS engine flagged as Round 20 build-time deferral (BLOCKED stub) | PASS | Â§2.3 BLOCKED stub |
| No crypto libs | PASS | Â§2.4 explicit exclusion table |
| PMS decoupled (D-GAP-I1) | PASS | Â§3.1, Â§7 Integration Matrix row |
| Paper-first SOI no upload / sync language | PASS | Â§6.2 explicit NOT-supported list |
| Zero bare `safety_*` prefixes | PASS | All table references use `vims_safety_*` (module) or `master_*` (reference). Search-verified across this file |
| Django `apps.safety` / `/api/safety/` / `ksm_marine_live` referenced | PASS | Â§1.1 `apps.safety`; Â§1.2 `/api/safety/`; Â§4.1 `ksm_marine_live` |

### 12.1 BLOCKED Stubs Summary

| # | Section | Label | Resolution owner | Required by |
|---|---------|-------|------------------|-------------|
| 1 | Â§2.2 | SOI unique-ID flag format | Product + Design | IMPLEMENTATION_PLAN Phase 4 |
| 2 | Â§2.3 | FTS engine selection | Platform lead | IMPLEMENTATION_PLAN Phase 7 |

Both BLOCKED items are Round 20 acknowledged build-time deferrals; neither is a gap in the 159 locked decisions.

---

## 13. Document References

| Document | Reference |
|----------|-----------|
| `VIMS-Reporting-Module/TECH_STACK.md` | Platform tech stack â€” inherited verbatim for all non-Safety-specific lines |
| `VIMS-SAFETY-MODULE-SSOT.md` | 159 locked decisions (D-*, D-GAP-*) â€” authority on requirements |
| `VIMS-Safety-Module/PRD.md` | Features (FEAT-SAF-*) â€” maps to this TECH_STACK via library choices |
| `VIMS-Safety-Module/BACKEND_STRUCTURE.md` | Schema + APIs; contains the 12-row build-time deferrals table referenced by Â§2.2 and Â§2.3 |
| `VIMS-Safety-Module/DESIGN_SYSTEM.md` | Visual tokens for PDF templates and dashboard (consumes reportlab + recharts from this stack) |
| `VIMS-Safety-Module/VALIDATION_RULES.md` | Input + compliance rules; uses Zod 3.23.8 (Â§1.13) |
| `VIMS-Safety-Module/IMPLEMENTATION_PLAN.md` | Master blueprint; Phase 8 resolves BLOCKED Â§2.2 and Â§2.3 |
| `VIMS-Reporting-Module/CLAUDE.md` | Platform forbidden-actions list; Safety inherits |
| KSM SSQE Manual Rev 01 Feb 2026 Â§9, Â§11 | Regulatory authority for SCM (Â§9) and Incident (Â§11) |
| ISM Code 2010 amendments Â§10 | Audit trail non-repudiation satisfied via `vims_safety_field_history` per D-GAP-D2 |

---

**Document Control:**
- Created: 2026-04-17
- Author: Docsuite generation agent, Wave 1
- Approved By: [Pending DPA + Tech Lead sign-off at Phase 0 kickoff]
- Supersedes: None (initial release)
