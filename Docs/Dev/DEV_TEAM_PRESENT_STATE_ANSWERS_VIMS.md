# Present-State Discovery - Answers


## A. Current performance

### A1. What are the current response times for login, list pages, record open, save, search, and report generation?

**Answer:** Unknown

### A2. Are these times measured from shore office or from a vessel over satellite?

**Answer:** Unknown

### A3. What is the slowest screen in each module today, and why?

**Answer:** The code shows likely heavy areas, but they have not been measured yet.

Likely heavy screens from local code:
- PSC: CAR list and dashboard, because they join CARs, deficiencies, inspections, vessel metadata, action counts, evidence counts, and physical verification counts.
- Certs: tracked items, class reconciliation, OCR/PDF parsing, print/share bundle generation.
- Safety: incident dashboard, incident phase workspaces, SCM attendance, WRH checks, SOI dashboards.
- Circular: PDF viewing and attachment delivery.

**What to do next:** Time these locally with server logs and SQL query timing enabled.

### A4. Are there known performance complaints from vessel users today?

**Answer:** sometimes system slow down

### A5. What is the current query count and slowest query per heavy screen?

**Answer:** Unknown.

### A6. What hardware does production run on today?

**Answer:** The repo confirms Django + SQL Server configuration, but not production cores, RAM, disk type, SQL Server edition, or app-server sizing.

## B. Who uses what, and where

### B1. For each module, what proportion of usage is vessel-side versus shore-side?

**Answer:** The repo has modules for PSC, Certs, Safety, Circular, ORB, accounts, masters, sync, and notifications. It does not contain session or transaction analytics showing vessel-side versus shore-side usage.

### B2. How many concurrent users are there on a single vessel at peak?

**Answer:** Based on onboard crew mapped to active ship login accounts, the highest possible vessel-side user count in local DB is 24 on SF DARIKA. Use 24 possible vessel-side users per vessel as the current local upper bound, but treat actual simultaneous concurrency as unmeasured until server access logs or session history are reviewed.

### B3. How many distinct users per vessel in total?

**Answer:** Local DB shows 136 onboard vessel-side users with ship login accounts across 6 vessels.

Per-vessel onboard ship-login users:
- SF DARIKA: 24
- EAST BANGKOK: 23
- SF CHALISA: 23
- SFYC ARAYA: 23
- YC FORTITUDE: 23
- EAST AYUTTHAYA: 21

### B4. Which specific workflows do crew perform onboard today?

**Answer:** Vessel-side workflows appear to include:
- PSC inspection and CAR follow-up.
- Circular viewing, PDF access, and acknowledgement.
- Safety incident and near miss reporting/review.
- SCM meetings, attendance, signatures, and WRH checks.
- SOI inspection and findings.
- Certs vessel/master view of certificate status, messages, and class status PDF.



### B5. Which workflows are shore-only and will never need to work offline?

**Answer:**  Likely shore-heavy or office-only areas include:
- Certs catalog, fleet dashboard, class status upload, reconciliation review, notifications, audit log, print/share bundle.
- Circular creation/publishing and recipient targeting.
- Safety reference/master data and office review stages.
- PSC PIC/DPA review and closure stages.


### B6. Are there workflows where vessel and shore genuinely edit the same record today?

**Answer:**  PSC inspections/CARs, Safety incidents/near misses/SCM/SOI, and Certs class review messages all have vessel-side and office-side states. The sync module includes conflict detection, which confirms the design expects some shared editing risk.

The actual frequency of same-record concurrent edits still needs usage evidence.

## C. Poor connectivity behavior today

### C1. What actually happens today when a vessel loses internet mid-task?

**Answer:**  for PSC sync-capable screens only. The frontend has IndexedDB stores and a sync queue for inspections, deficiencies, CARs, master data, and offline mutations. The backend has pull, push, attachment upload, conflict list, and conflict resolution endpoints.



### C2. Do crew currently work around outages?

**Answer:** Unknown

### C3. How long are typical outages today, and how frequent?

**Answer:** Unknown

### C4. How much rework does an outage cause today?

**Answer:** Unknown

### C5. What is the actual business consequence of an outage?

**Answer:** Unknown

### C6. Have crew asked for offline capability, or is this a shore-side initiative?

**Answer:** Unknown

## D. Database reality

### D1. How many databases are there, actually?

**Answer:**  `psc-backend/core/settings.py` configures the Django backend to use SQL Server through environment variables, defaulting to:
- `DB_ENGINE=mssql`
- `DB_NAME=ksm_marine_live`
- `DB_HOST=localhost`
- `DB_PORT=1433`
- ODBC Driver 18 for SQL Server

The question document mentions possible evidence of `ksm_cms_live` elsewhere, but this was not confirmed from the local backend settings file.

### D2. What else writes to this database besides the five applications?

**Answer:** Needs DBA/dev-owner confirmation. The code uses many unmanaged existing tables, which means other applications or legacy systems probably own some data, but the repo cannot prove every writer.

**What to do next:** Ask DBA/dev owners for scheduled jobs, SSRS/Crystal reports, ETL jobs, imports, manual scripts, and third-party integrations that write to the same databases.

### D3. Who owns the tables outside the main naming families?

**Answer:** Local models show these families:
- `psc_*`: PSC inspections, deficiencies, CARs, evidence, sync, notifications, audit.
- `vims_certs_*`: Certs catalog, tracked items, PDFs, snapshots, reconciliation, alerts, print artifacts.
- `vims_safety_*`: Safety incidents, evidence, SCM, SOI, findings, dashboard rollups, phase logs.
- `msc_*`: Circular/profile/notification related existing tables.
- `master_*`, `mapping_*`, `VesselData`, `HRM501`, `Crew_Onboarding_History`, `Final_crew_list`, `Ship_UsersLogin`, `users`: shared/legacy identity, vessel, crew, circular, or reference data.



### D4. Do Django migrations run directly against the shared production database?

**Answer:** Yes

### D5. Are `temp_`, `tmp_`, and `tbl_` tables active, abandoned, or temporary?

**Answer:** A live database inventory is required to know whether these tables exist, are active, or are abandoned.

### D6. What are row counts and growth rates for the twenty largest tables?

**Answer:**= Unknown

### D7. Which tables are vessel-scoped versus fleet-wide reference data?

**Answer:**
 vessel-scoped:
- PSC inspections, deficiencies, CARs, corrective actions, evidence, physical verification, activity history.
- Safety incidents, near misses, SCM, SOI, findings, recommendations.
- Certs tracked items, class snapshots, reconciliation runs/messages, print artifacts.
- Circular ship notifications and acknowledgements.

 fleet-wide/reference:
- Master/reference tables, code tables, catalog tables, rank/role/profile tables, vessel master data.



### D8. Which tables have no primary key?

**Answer:** Some unmanaged models map to existing tables and may not fully represent physical primary keys. A database schema scan is required.

### D9. What is the current SQL Server edition, update level, recovery model, and collation?

**Answer:** Needs DBA confirmation. The app uses SQL Server through `mssql-django` and ODBC Driver 18, but server edition and database settings are not in the repo.

### D10. Is there any existing replication, ETL, log shipping, or sync?

**Answer:**  for app-level PSC sync only. The repo contains:
- Frontend IndexedDB stores and queue.
- Backend `/api/psc/sync/pull/`, `/api/psc/sync/push/`, `/api/psc/sync/upload/`, `/api/psc/sync/conflicts/`, and `/api/psc/sync/resolve-conflict/`.
- Backend tables `psc_sync_log`, `psc_sync_log_detail`, `psc_sync_conflict`, and `psc_sync_token`.


### D11. How much data would a single vessel actually need locally?

**Answer:** Unknown

## E. Current operations

### E1. How are the applications deployed and updated today?

**Answer:** The frontend has Vite scripts for dev/build/test. The backend has Django/gunicorn dependencies. The main workflow is such that, entire folder is being copied from local to server. later settings.py, urls.py, uploads and media files are being replaced.

### E2. What is the current backup practice?

**Answer:** Before every new release/deployment, backup is taken on server's root folder

### E3. What monitoring exists today?

**Answer:** Certs has Slack/email notification code and PSC/Safety have notifications/audit-related code. Actual production monitoring, alert routing, and on-call behavior still need confirmation.

### E4. What breaks most often in production today?

**Answer:** Recent local testing found issues in PDF/OCR, localhost API hosts, CAR list SQL queries, and SQL Server UUID conversions, but this is not a production incident history.

### E5. What is the current support model?

**Answer:** Unknown

### E6. How do you currently support a vessel user with a problem?

**Answer:** via direct contact on whatsapp

### E7. Have you ever deployed anything to a vessel before?

**Answer:** Yes

## F. Existing vessel-side infrastructure

### F1. What IT infrastructure is already on a typical vessel?

**Answer:** unknown

### F2. Is there an existing vessel LAN the mini PC would join?

**Answer:** unknown

### F3. What devices will crew actually use?

**Answer:** unknown

### F4. What is the current satellite setup?

**Answer:** unknown

### F5. Is there already a vessel-side file share or NAS?

**Answer:** unknown

### F6. What power quality and UPS exist today?

**Answer:** unknown

### F7. Who physically has access to the space where the mini PC would live?

**Answer:** unknown
## G. Offline and sync already built

### G1. What is the current status of the React vessel PWA offline layer?

**Answer:**  The frontend uses `vite-plugin-pwa`, Workbox packages, service-worker registration code, IndexedDB, offline hooks, sync status UI, pending changes UI, conflict UI, and storage indicator UI. The setup already exist in folder but not completely configured yet.

### G2. If it is live, how many vessels and users are using it?

**Answer:** NA

### G3. Has anyone observed duplicate records created by the replay path?

**Answer:** Unknown

### G4. What drove that work originally, and why was it built client-side?

**Answer:** unknown

### G5. What did you learn from it?

**Answer:** The implementation contains offline banners, storage warnings, pending changes, conflict resolution, attachment retry handling, and sync status screens. This suggests known concerns around stranded local changes, storage limits, and conflict visibility.

### G6. Is there similar offline work in VIMS, CMS, PMS, or SMS?

**Answer:** Unknown.

a## H. People and change

### H1. Who onboard is the most technical person on a typical vessel?

**Answer:** Master

### H2. What is crew rotation frequency?

**Answer:** Unknown

### H3. What languages must crew-facing procedures and error messages be in?

**Answer:** UI text appears in English.

### H4. Who trains crew on these systems today, and how?

**Answer:** Userguides are being shared while releasing any feature/module.

### H5. Are there vessels that would be poor pilots, and one that would be a good pilot?

**Answer:** unknown

## I. Unknown constraints

### I1. Are there flag-state, classification-society, or ISM cyber requirements?

**Answer:** unknown

### I2. Are there charterer, owner, or client contractual constraints?

**Answer:**  unknown

### I3. Are there data-residency, privacy, or crew-data rules?

**Answer:**  Local code references crew/user tables and authentication models. Any onboard replication of users, crew details, passwords, tokens, attachments, or audit logs needs privacy and security review.

### I4. Are any applications subject to external audit?

**Answer:** PSC, Safety, and Certs all include audit logs, PDF exports, generated reports, signatures, and history-style records. The external audit requirement itself still needs confirmation.

### I5. Is there anything else about the present system that would materially change this design?

**Answer:** Risk areas visible in the folder:
- UUID handling has caused local SQL Server conversion errors in recent testing.
- Some heavy endpoints have needed query cleanup to avoid local timeouts.
- PSC offline/sync exists but appears scoped mainly to PSC entities.
- Safety has a complex workflow surface with many phase endpoints, SCM, SOI, WRH checks, and signatures.
- Certs has OCR/PDF parsing, generated artifacts, Slack/email alerts, and class-status reconciliation, which are integration-heavy and need repeatable test PDFs.
