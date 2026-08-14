# VIMS Present-State Discovery - Customized Evidence Report

Date: 2026-08-13
Source template: `C:\Users\himan\Downloads\DEV_TEAM_PRESENT_STATE_QUESTIONS_v1.md`
Repository scope: VIMS only

## Executive Summary

Complete VIMS is evidenced in this repository as a Django/DRF + React/TypeScript system backed by SQL Server, with PSC, Safety, Certs, Circular, ORB, accounts/auth, masters, sync, notifications and help surfaces mounted in the backend (`psc-backend/core/urls.py:39-134`). The current backend configuration targets SQL Server database `ksm_marine_live` through `mssql` and ODBC Driver 18 (`psc-backend/core/settings.py:111-116`, `psc-backend/core/settings.py:128-133`). A read-only SQL snapshot taken on 2026-08-13 connected to `server_name = HIMANI` and `database_name = ksm_marine_live`; those database observations are useful local/current evidence, but they must not be treated as production proof unless operations confirms the target.

Production performance is not established. No APM/RUM export, Nginx/Gunicorn timing log, browser navigation dataset, vessel satellite timing, or production host survey was supplied. The only checked-in timing evidence found is Certs local/API timing, where `tracked-items page 100` and `catalog/rows page 100` are the slowest measured Certs calls in `certs-api-timing-results-final-clean.json`. Those numbers are not production p95, not browser render timing, and not full VIMS timing.

Usage is also not established from telemetry. The repository proves module surfaces and vessel/office-capable workflows, while the 2026-08-13 database snapshot gives only account and catalog facts: 6 active vessels, 209 active ship-login accounts, 136 active onboard ship-login users matched to latest active onboarding rows, and 42 active office users. The highest current per-vessel onboard ship-login count in that snapshot is 23. These are enabled/onboard-account proxies, not concurrent users or actual workflow usage.

Poor-connectivity behavior is partially implemented and PSC-focused. The frontend includes PWA/Workbox dependencies, a service worker, IndexedDB queueing, sync status, offline hooks for inspections/CARs, and attachment/conflict handling. The backend exposes PSC sync pull, push, upload, conflict list and conflict resolution endpoints. However, the `psc_sync_*` tables were empty in the 2026-08-13 database snapshot, so live PSC sync usage is not demonstrated. Non-PSC offline coverage, vessel outage frequency, crew workarounds, replay rework, and business consequences remain evidence gaps.

Database reality is shared and not yet fully owned. The current catalog contains 552 `dbo` tables, including `master`, `pur`, `vims`, `psc`, `pms`, `audit`, `django`, `wrh`, `msc`, `auth`, `sync`, temp/tmp/tbl and many smaller families. The repo maps PSC, Safety and Certs families clearly, but external writers, table ownership, migration practice, replication/ETL/log shipping, and per-vessel local data volume are not fully proven. The same snapshot reports SQL Server 2019 RTM Developer Edition, `SIMPLE` recovery, `SQL_Latin1_General_CP1_CI_AS` collation, compatibility level 120 and Query Store off for the connector target; production DBA confirmation is still required.

The immediate baseline work is therefore measurement and ownership, not architecture design. Before using this document as a basis for onboard/offline architecture decisions, collect production p50/p95/p99 timings, shore-versus-vessel network measurements, 90-day module usage telemetry, outage/support evidence, database writer ownership, table scope/retention matrices, backup/restore proof, and production infrastructure sizing.

## A. Current performance

Evidence scope for A-D:

- Repository evidence comes from checked-in Django/DRF backend code, React frontend code, module docs, tests, and checked-in timing artifacts.
- Database observations are from a read-only SQL Server snapshot taken on 2026-08-13. The connector returned `server_name = HIMANI` and `database_name = ksm_marine_live`; treat these as local/current database observations unless operations confirms this is production.
- No production APM/RUM export, Nginx/Gunicorn request-time log, browser navigation dataset, vessel satellite timing, or production host survey was supplied for this VIMS document.

### A1. What are the current response times for login, list pages, record open, save, search, and report generation?

Status: **Unknown for production p95. Partial local artifact evidence exists for Certs only.**

Direct answer:

- There is no evidence-backed current production p95 for login, list pages, record open, save, search, report generation, PDF generation, or sync.
- The checked-in Certs timing artifact records local three-run averages/min/max, not production p95. Its heaviest measured calls are `tracked-items page 100` at 25,603 ms average, `catalog/rows page 100` at 25,140 ms average, and one `tracked-item detail` at 8,676 ms average with a 25,858 ms max (`certs-api-timing-results-final-clean.json`).
- These numbers must not be relabeled as production, vessel, browser-render, or full VIMS p95 timings.

Repository evidence:

- VIMS exposes PSC auth, inspections, deficiencies, CARs, sync, dashboard, reports, notifications, Safety, Certs, Circular, ORB, masters and help routes (`psc-backend/core/urls.py:39-134`).
- The backend uses DRF with authenticated access and page-number pagination (`psc-backend/core/settings.py:210-221`).
- Certs has parser-duration anomaly handling above 180 seconds (`psc-backend/apps/certs/services/reconciliation.py:22`, `psc-backend/apps/certs/services/reconciliation.py:213-221`).

Evidence gap:

- Capture 7-30 days of route-normalized production server timings and browser RUM.
- Calculate p50/p95/p99 by route, method, status, role type, vessel/office context, payload band and app build.
- Correlate slow request IDs with SQL duration/query count, SQL Server waits, app host metrics and network path.

Owner to confirm: Dev team, Operations/SRE and DBA.

### A2. Are these times measured from shore office or from a vessel over satellite?

Status: **Unknown.**

Direct answer:

- No checked-in artifact separates shore-office timing from vessel-over-satellite timing.
- The existing Certs timing artifact is local/API evidence only and does not identify shore, vessel, browser, satellite provider, bandwidth, packet loss or latency.

Repository evidence:

- PSC docs and frontend code include PWA/offline dependencies and service-worker code (`Docs/TECH_STACK.md:93-104`, `psc-frontend/package.json:33`, `psc-frontend/package.json:49-54`, `psc-frontend/package.json:80`, `psc-frontend/src/sw.ts:7-13`).
- PSC sync endpoints are exposed under `/api/psc/sync/` (`psc-backend/core/urls.py:104-111`, `psc-backend/apps/sync/urls.py:24-31`).

Evidence gap:

- Run the same timing route set from at least one shore office and at least two vessels.
- Record server processing time separately from browser total time and network path time.

Owner to confirm: Dev team, vessel IT/communications provider and operations/support.

### A3. What is the slowest screen in each module today, and why?

Status: **Not answered for production. Partially answered by local/code evidence.**

Direct answer:

- No production screen can be truthfully named as the slowest VIMS screen from the current evidence.
- The strongest local evidence is Certs: `tracked-items page 100` and `catalog/rows page 100` are the slowest measured Certs API calls in `certs-api-timing-results-final-clean.json`.
- PSC and Safety have code-level heavy candidates, but no measured p95/query matrix was supplied.

Likely heavy areas, bounded by evidence:

| Module | Evidence-backed heavy candidate | Why this is only a candidate |
|---|---|---|
| Certs | Tracked-item list/detail, catalog rows, fleet dashboard, class snapshot/reconciliation and print/share paths | Local timing artifact covers some API calls, but not production, browser render or vessel network. |
| PSC | CAR list/detail, dashboard/reporting, deficiency/CAR follow-up and evidence paths | PSC routes expose list/detail/action/report surfaces (`psc-backend/core/urls.py:57-117`); CAR tests mention a slow vessel-assignment branch regression (`psc-backend/apps/car/tests.py:2258`). |
| Safety | Dashboard, incident phase workspaces, SCM attendance, WRH checks, SOI dashboards/downloads | Safety routes are mounted at `/api/safety/` (`psc-backend/core/urls.py:129-130`); WRH lookups have explicit timeout handling (`psc-backend/apps/safety/repositories/wrh_repo.py:12-23`). |
| Circular/ORB | PDF/file delivery, acknowledgement and vessel-facing pages | Routes exist (`psc-backend/core/urls.py:42-44`), but no timing artifact was found. |

Evidence gap:

- Build a screen-open request graph for PSC, Certs, Safety, Circular and ORB.
- Capture HTTP p50/p95/max, SQL statement count, slowest SQL shape, payload size, browser timing, role and vessel scope.

Owner to confirm: Dev team and QA/performance owner.

### A4. Are there known performance complaints from vessel users today?

Status: **Anecdotal only; not evidenced as a support dataset.**

Evidence gap:

- Pull 90 days of support tickets, direct support messages, release notes and incident logs.
- Classify complaints as application latency, SQL/database latency, vessel connectivity, file/PDF latency, authentication, data correctness, permissions or training/usability.


### A5. What is the current query count and slowest query per heavy screen?

Repository evidence:

- PSC tests include a regression note that a global PIC list should avoid a slow vessel-assignment branch (`psc-backend/apps/car/tests.py:2258`).
- CAR serializers include denormalized deficiency information for performance (`psc-backend/apps/car/serializers.py:563`).
- Safety repositories enforce cursor timeouts and convert DB timeout errors into application exceptions (`psc-backend/apps/safety/repositories/base.py:62-111`, `psc-backend/apps/safety/repositories/base.py:188-190`).

Evidence gap:

- Add request-scoped SQL capture for each heavy screen in a read-only local benchmark.
- Repeat in production using Query Store or equivalent DBA tooling.
- Store endpoint, role, vessel scope, HTTP p50/p95/max, SQL statement count, average DB time, slowest SQL shape and payload bytes.

Owner to confirm: Dev team and DBA.

### A6. What hardware does production run on today?

- The repo confirms the backend is configured for SQL Server via `mssql-django`, database default `ksm_marine_live`, host default `localhost`, port `1433`, and ODBC Driver 18 (`psc-backend/core/settings.py:111-116`, `psc-backend/core/settings.py:128-133`).
- The repo does not prove production app-server CPU, RAM, disk, OS, virtualization, Gunicorn worker count, Nginx config, SQL Server host sizing, NAS/storage sizing, backup target or network layout.
- The 2026-08-13 read-only SQL snapshot identifies the connector target as SQL Server 2019 version `15.0.2000.5`, RTM, Developer Edition. This is not production sizing or licensing proof without infrastructure confirmation.

Evidence gap:

- Collect app host specs, DB host specs, storage/NAS specs, process inventory, Gunicorn/Nginx/systemd configuration, SQL Server memory/tempdb/file layout and sustained CPU/memory/disk/network metrics.

Owner to confirm: Infrastructure/opeStatus: **Unknown for actual usage proportions.**

Direct answer:

- The repo proves module surfaces and vessel/office-capable code paetry that can calculate vessel-side versus shore-side usage by module.
- The read-only database snapshot proves configured users and current table rows, not actual click frequency, completed workflow volume by role, or concurrency.

Repository evidence:

- The backend routes include PSC, Safety, Certs, Circular, ORB, accounts/auth, masters, sync, notifications and help (`psc-backend/core/urls.py:39-134`).
- PSC backend docs describe shared identity/vessel tables and role/vessel access (`Docs/BACKEND_STRUCTURE.md:29-30`, `Docs/BACKEND_STRUCTURE.md:140-151`, `Docs/BACKEND_STRUCTURE.md:179-180`).

Evidence gap:

- Extract 90 days of aggregate sessions, API calls and write transactions by module, route, role type, vessel ID, client, status and action outcome.
- Keep enabled account counts separate from actual usage counts.

Owner to confirm: Product Owner, dev telemetry owner and module owners.

### B2. How many concurrent users are there on a single vessel at peak?

Status: **Unknown for actual concurrency. Local/current database gives an enabled/onboard upper-bound proxy only.**

Direct answer:

--login accounts and 136 active onboard ship-login users matched to the latest active, non-signed-off onboarding row across 6 active vessels.
- The highest current per-vessel onboard ship-login count in that snapshot is 23, not a measured concurrency number.

Read-only database snapshot:

| Vessel code | Active onboard ship-login users |
|---|---:|
| ARY | 23 |
| EBK | 23 |
| SFC | 23 |
| SFD | 23 |
| YCF | 23 |
| EAT | 21 |

Do not over-interpret:

- Enabled/onboard login count is not simultaneous use.
- It does not prove browser sessions, active devices, shift overlap, offline usage or peak API concurrency.

Evidence gap:

- Measure authenticated sessions and API activity per vessel over at least one operational month.
- Report max, p95 and typical shift-overlap concurrency per vessel and module.

Owner to confirm: Operations/support and dev telemetry owner.

### B3. How many distinct users per vessel in total?

Status: **Partially answered for active onboard ship-login accounts in the local/current database snapshot. Full distinct user popula to latest active, non-signed-off `Crew_Onboarding_History` rows and active `VesselData`.
- The same snapshot shows 42 active office users.

Evidence boundaries:

- No names, usernames, emails, passwords, phone numbers or personal crew records were extracted into this report.
- This does not count inactive users, historical rotated crew, shared devices, duplicate credentials or real monthly active users.

Evidence gap:

- Confirm the intended definition: active credentials, currently onboard crew, monthly active users, or all historical users.
- Add rotation joins/leavers by vessel and rank without exposing personal identifiers.

Owner to confirm: Crewing/HR, DBA and Product Owner.

### B4. Which specific workflows do crew perform onboard today?

Status: **Implemented/entitled workflow surfaces are partially known; actual onboard frequency is unknown.**

Direct answer:

- Code and docs show vessel-relevant workflows for PSC inspection/CAR follow-up, PSC sync, Circular ship routes, Safety incidents/near misses/SCM/SOI, and Certs vessel-scoped certificate tracking.
- The repo does not prove how often crew perform each workflow onboard.

Repository evidence:

- PSC inspection, deficiency, follow-up, CAR, evidence, corrective-action and physical-verification endpoints are mounted under `/api/psc/` (`psc-backend/core/urls.py:57-102`).
- PSC sync exposes pull, push, attachment upload, conflict list and conflict resolution (`psc-backend/core/urls.py:104-111`, `psc-backend/apps/sync/urls.py:24-31`).
- Circular ship routes are mounted with Circular office routes (`psc-backend/core/urls.py:42-44`).
- Safety routes are mounted at `/api/safety/` (`psc-backend/core/urls.py:129-130`).
- Certs routes are mounted at `/api/certs/` and `/api/auditor/` (`psc-backend/core/urls.py:133-134`).

Evidence gap:

- Pull route-level usage by role/vessel for create, update, submit, review, acknowledge, upload, download, report and PDF actions.
- Classify each workflow as vessel-originated, shore-originated, shared workflow, or office-only with evidence.

Owner to confirm: Product Owner and operations/support.

### B5. Which workflows are shore-only and will never need to work offline?

Status: **Not safely answerable as "never" from repo evidence.**

Direct answer:

- Several workflows appear office-heavy, including Safety office review/reporting/admin paths, and Circular publishing/recipient targeting.
- The word "never" requires Product Owner confirmation and usage evidence. The repo alone cannot prove a shore-only workflow will never be needed during onboard visits, audits, emergency support or poor-connectivity workarounds.

Evidence gap:

- For each candidate shore-only workflow, confirm owner, role, onboard exception cases, regulatory/audit constraints and whether vessel staff ever perform it by phone/WhatsApp/email on behalf of office.

Owner to confirm: Product Owner, module owners and operations.

### B6. Are there workflows where vessel and shore genuinely edit the same record today?

Status: **Design supports shared-edit risk; actual collision frequency is unknown.**

Direct answer:

- PSC clearly has shared-edit riflict resolution are implemented.
- Safety and Certs also contain vessel-scoped records plus office review/reporting/configuration surfaces, but actual same-record concurrent edit frequency is unmeasured.

Repository evidence:

- PSC inspection and CAR models include vessel identifiers and shared workflow status fields (`psc-backend/apps/inspection/models.py:48-133`, `psc-backend/apps/inspection/deficiency_models.py:28-121`, `psc-backend/apps/car/models.py:86-114`).
- PSC sync has conflict status/resolution models and per-vessel sync tokens (`psc-backend/apps/sync/models.py:161-236`).
- Safety base records include `vessel_id`, and Safety incident states include `PENDING_VESSEL_REVIEW` (`psc-backend/apps/safety/models/base.py:15-35`, `psc-backend/apps/safety/models/incident.py:43-52`).
- Certs tracked items carry `vessel_id` (`psc-backend/apps/certs/models/tracked_item.py:8-71`).

Evidence gap:

- Query audit/history tables for records edited by both vessel and office roles within defined windows.
- Distinguish normal sequential workflow transitions from same-field collisions and stale offline overwrites.

Owner to confirm: Dev team, DBA and Product Owner.
d office-side states. The sync module includes conflict detection, which confirms thtual frequency of same-record concurrent edits still needs usage evidence.

## C. Poor connectivity behavior today

#
- The current offline implementation is PSC-focused. The frontend has Workbox/PWA support, IndexedDB-backed sync queue behavior, offline status tracking and offline hooks for inspections and CARs. The backend exposes PSC sync pull, push, attachment upload, conflict list and conflict resolution.
- API requests are service-worker `NetworkOnly`; offline business data is handled by IndexedDB and sync code, not by the service worker returning cached API responses.
- The read-only database snapshot shows the PSC-specific sync tables exist but are empty: `psc_sync_log`, `psc_sync_log_detail`, `psc_sync_conflict` and `psc_sync_token` all had zero rows on 2026-08-13. That means the database snapshot does not prove live PSC sync usage.

Repository evidence:

- PWA/offline dependencies are declared (`psc-frontend/package.json:33`, `psc-frontend/package.json:49-54`, `psc-frontend/package.json:80`).
- The service worker precaches the app shell, uses navigation/static caches, and treats API requests as NetworkOnly (`psc-frontend/src/sw.ts:7-13`, `psc-frontend/src/sw.ts:25-49`).
- The frontend queue stores offline mutations in IndexedDB and tracks pending/failed/completed states (`psc-frontend/src/lib/db/sync-queue.ts:2-16`, `psc-frontend/src/lib/db/sync-queue.ts:34-168`).
- The sync service pulls server changes, merges them into IndexedDB, pushes queued changes, handles id mappings/conflicts and attachment uploads (`psc-frontend/src/lib/sync/sync-service.ts:131-257`).
- Offline hooks read inspections/deficiencies/CARs from IndexedDB and queue offline mutations (`psc-frontend/src/hooks/use-offline-inspections.ts:2-21`, `psc-frontend/src/hooks/use-offline-inspections.ts:29-129`, `psc-frontend/src/hooks/use-offline-cars.ts:29-104`).
- Backend sync routes are mounted for pull, push, upload, resolve-conflict and conflicts (`psc-backend/apps/sync/urls.py:24-31`).

Current behavior matrix:

| Interruption point | Present implemented behavior | Limitation |
|---|---|---|
| App shell/static files already cached | Workbox can serve app shell/navigation/static assets from cache. | First-time launch or uncached assets still need connectivity. |
| API request while offline | Service worker keeps API as NetworkOnly; business fallback depends on the calling screen's IndexedDB logic. | Screens without offline hooks fail or wait for connectivity. |
| PSC inspection/CAR list while offline | Offline hooks can read cached PSC inspection/deficiency/CAR data from IndexedDB. | Cache completeness depends on prior successful pull. |
| PSC mutation while offline | Mutation is queued in IndexedDB for later push. | Queue durability is browser/device-local. |
| Attachment/evidence sync | Sync code has attachment upload registration and backend upload endpoint. | Real outage replay success and production usage are not proven by the empty PSC sync tables. |
| Conflict | Backend and frontend conflict list/resolution surfaces exist. | The local/current DB snapshot has no PSC sync conflicts, so conflict frequency is unknown. |

Evidence gap:

- Instrument client offline transitions, queue depth, failed intents, replay attempts, sync duration and conflict outcomes.
- Confirm whether PSC sync is enabled in production and which vessels have successfully used it.
- Audit non-PSC modules for offline behavior before telling crew that VIMS is broadly offline-capable.



### C2. Do crew currently work around outages?


- The repo shows system-supported PSC sync and UI components for offline/pending/conflict/storage status, but it does not prove actual crew workarounds such as paper, Excel, WhatsApp, email, phone calls or delayed entry.

Repository evidence:

- Offline banner, pending changes, sync status, storage indicator and conflict components exist in the frontend (`psc-frontend/src/components/sync/offline-banner.tsx`, `psc-frontend/src/components/sync/pending-changes.tsx`, `psc-frontend/src/components/sync/sync-status.tsx`, `psc-frontend/src/components/sync/storage-indicator.tsx`, `psc-frontend/src/components/sync/conflict-list.tsx`).

Evidence gap:

- Interview Master, Chief Engineer, Chief Officer, junior creators, office reviewers and support for at least one outage per vessel.
- Record actual fallback channel, document used, who re-keyed, duplicate check, final record ID and time lost.

Owner to confirm: Product Owner, vessel operations and support.

### C3. How long are typical outages today, and how frequent?

- The repository and database snapshot do not contain vessel connectivity telemetry, router/satellite logs, client offline transition logs or server reachability probes by vessel.
- Business timestamps in VIMS tables cannot be interpreted as outage duration without client/network telemetry.

Minimum measurement matrix:

| Metric | Required source |
|---|---|
| Offline transition count and duration | PWA heartbeat plus browser online/offline events and API health checks |
| Satellite/router outage duration | Vessel router, Starlink/VSAT or communications-provider logs |
| Queue depth and oldest pending age | Privacy-safe client sync telemetry sent on reconnect |
| Replay attempts and failure cause | Server-side sync event ID plus client event ID |
| Server availability and latency | Nginx/Gunicorn/APM/system metrics |
| Business impact overlap | Join outage windows to aggregate workflow timestamps |


### C4. How much rework does an outage cause today?

- Rework volume cannot be calculated from the current evidence.
- Potential rework exists when local queue entries fail, browser storage is lost, attachments do not upload, conflicts require manual resolution, or crew uses an external/manual channel and later duplicates a synced record.

Current safeguard and risk matrix:

| Cause | Current safeguard | Residual risk |
|---|---|---|
| Offline PSC mutation | IndexedDB sync queue and later push (`psc-frontend/src/lib/db/sync-queue.ts:34-168`, `psc-frontend/src/lib/sync/sync-service.ts:245-257`) | Queue is local to the browser/device. |
| Conflict | Conflict model, conflict list endpoint and resolve-conflict endpoint (`psc-backend/apps/sync/models.py:161-203`, `psc-backend/apps/sync/urls.py:29-31`) | Frequency and crew support process are unknown. |
| Attachment upload | Attachment upload endpoint and frontend upload helper are present (`psc-backend/apps/sync/urls.py:29`, `psc-frontend/src/lib/sync/attachment-uploader.ts`) | Actual replay under poor links is unmeasured. |
| Non-PSC workflow during outage | No evidence of broad offline coverage | Crew may delay, communicate outside VIMS or re-key later. |

Evidence gap:

- Add privacy-safe client mutation IDs and server replay markers.
- Measure duplicate creates, failed queue items, attachment retry failures, manual re-entry events, conflict resolutions and person-minutes of rework.


### C5. What is the actual business consequence of an outage?

- The current evidence does not link outages to missed inspections, late CAR closure, delayed Safety incident reporting, delayed certificate updates, failed Circular acknowledgement, audit findings, off-hire, expedited cost or safety risk.
- Exposure exists because vessel-facing workflows include PSC inspection/CAR evidence, Safety reporting/review, Circular acknowledgement and Certs vessel data. If connectivity prevents submission, upload, acknowledgement or sync replay, shore visibility and audit trail timing can be delayed.

Evidence gap:

- For each future outage incident, capture vessel, workflow, priority, outage start/end, local event ID, final server record ID, replay outcome, duplicate/manual record, delay minutes, audit/safety/commercial consequence and resolution owner.


### C6. Have crew asked for offline capability, or is this a shore-side initiative?

- The repo proves PSC offline/sync work was built or planned, but it does not prove whether the request originated from crew, shore management, audit/compliance, engineering, or product planning.
- Crew demand, satisfaction and priority order for offline coverage remain unverified.

Repository evidence:

- PSC docs define PWA/offline stack requirements (`Docs/TECH_STACK.md:93-104`, `Docs/TECH_STACK.md:239-242`).
- PSC backend docs define sync tables and idempotency/conflict concepts (`Docs/BACKEND_STRUCTURE.md:681-782`).
- Frontend and backend sync code exists as listed in C1.

Evidence gap:

- Locate original CR/design note/stakeholder request for offline work.
- Interview vessel users to rank needed offline capabilities: inspection create/update, CAR evidence, Safety incident/near miss, Circular acknowledgement, Certs view/download, attachments, comments, reports and conflict repair.

line capability, or is this a shore-side initiative?

**Answer:** Unknown
- The VIMS backend defaults to SQL Server database `ksm_marine_live` using `DB_ENGINE=mssql`, host `localhost`, port `1433`, and ODBC Driver 18 (`psc-backend/core/settings.py:111-116`, `psc-backend/core/settings.py:128-133`).
- The read-only connector on 2026-08-13 returned `DB_NAME() = ksm_marine_live` on server `HIMANI`.
- The live/current catalog has 552 `dbo` tables.
- This does not prove whether VIMS, CMS, PMS, SMS and Purchase all use one database in production, nor whether other databases such as `ksm_cms_live` exist in production.

### D2. What else writes to this database besides the five applications?

- The repo and read-only catalog prove a shared, multi-family database, but they do not enumerate all external writers.
- Because the database includes Purchase (`pur_`), PMS (`pms_`), Django/auth, legacy master/crew/vessel, WRH, audit, sync and VIMS-specific families, external writers are plausible but not proven.

Read-only catalog evidence:

- Prefix counts include `master` 98 tables, `pur` 72, `vims` 57, no-underscore 49, `psc` 22, `pms` 20, `audit` 19, `django` 13, `wrh` 13, `msc` 12, plus other smaller families.

Evidence gap:

- Inventory every writer: Django apps, legacy VIMS/CMS/PMS/SMS services, Purchase, SQL Agent jobs, SSRS/Crystal, ETL/import tools, Excel/Access tools, vendor integrations, manual scripts and DBA maintenance scripts.
- For each writer, capture table list, write frequency, identity/security context, owner and sync/outbox relevance.

Owner to confirm: DBA and operations. Treat this as a blocker for any server-side sync/outbox design.

### D3. Who owns the tables outside the main naming families?

- The local/current catalog shows many table families. The repo maps some clearly to modules, but ownership outside those mappings requires DBA/module-owner confirmation.

Current evidence-backed family map:

| Family/table pattern | Evidence-backed interpretation |
|---|---|
| `psc_*` / `PSC_*` | PSC inspections, deficiencies, CARs, evidence, notifications, audit and sync (`psc-backend/apps/inspection/models.py:129-207`, `psc-backend/apps/inspection/deficiency_models.py:120-341`, `psc-backend/apps/car/models.py:48-331`, `psc-backend/apps/sync/models.py:100-236`). |
| `vims_certs_*` | Certs catalog, tracked items, PDFs, snapshots, reconciliation, audit, alerts and print artifacts (`psc-backend/apps/certs/models/catalog.py:14-55`, `psc-backend/apps/certs/models/tracked_item.py:69-98`). |
| `vims_safety_*` | Safety incident, evidence, SCM, SOI, dashboard, phase, recommendation and related records (`psc-backend/apps/safety/models/base.py:15-35`, `psc-backend/apps/safety/models/incident.py:221-222`, `psc-backend/apps/safety/models/scm.py:65-92`). |
| `master_*`, `mapping_*`, `VesselData`, `HRM501`, `Crew_Onboarding_History`, `Final_crew_list`, `Ship_UsersLogin`, `users` | Shared/legacy identity, vessel, crew, role/profile and reference data (`Docs/BACKEND_STRUCTURE.md:29-30`, `Docs/BACKEND_STRUCTURE.md:86-180`). |
| `pur_*`, `pms_*`, `wrh_*`, `msc_*`, `audit_*`, `django_*`, `auth_*`, `sync_*` | Present in catalog; ownership and write paths must be confirmed with module owners/DBA. |

Evidence gap:

- Build a table ownership matrix with columns: table, owner app, writer services, read-only consumers, vessel scope, retention, attachment dependency, sync relevance and deletion policy.

Owner to confirm: DBA and module owners.

### D4. Do Django migrations run directly against the shared production database?

Status: **Unknown for production process. Framework and app migration artifacts exist.**

Direct answer:

- The previous answer "Yes" is under-evidenced. The repo contains Django migration files and the live/current database contains `django` and `auth` table families, but that does not prove the production deployment process runs `manage.py migrate` directly against the shared production database.
- Certs and Safety include models with `managed = False` for selected existing/reference tables, while many other app models are normal Django models or migration-backed.

Repository/database evidence:

- Backend settings install Django/DRF/auth/token apps (`psc-backend/core/settings.py:47-58`).
- The live/current catalog includes 13 `django_*` tables, 6 `auth_*` tables and 1 `authtoken_*` table.
- Certs catalog/tracked models explicitly mark some tables unmanaged (`psc-backend/apps/certs/models/catalog.py:14-55`, `psc-backend/apps/certs/models/tracked_item.py:69-98`).
- Safety reference models mark master reference tables unmanaged (`psc-backend/apps/safety/models/reference.py:22-131`).

Evidence gap:

- Review deployment scripts/runbooks for `manage.py migrate`.
- Capture the production `django_migrations` table and deployment history.
- Confirm which apps are migration-controlled versus manually DBA-controlled.

Owner to confirm: Release/deployment owner and DBA.

### D5. Are `temp_`, `tmp_`, and `tbl_` tables active, abandoned, or temporary?

Status: **Existence verified in local/current database; status unknown.**

Direct answer:

- The 2026-08-13 read-only catalog contains four matching tables: `tbl_Crew_Vessels`, `temp_fuel_summary`, `temp_Lube_Budget` and `tmp_Lube_Periodic`.
- The repo does not prove whether these tables are active, abandoned, staging-only, temporary-by-name, or used by external jobs.

Evidence gap:

- For each table, capture owner, row count, last write, dependencies, indexes, job references, application references and sync relevance.

Owner to confirm: DBA and operations.

### D6. What are row counts and growth rates for the twenty largest tables?

Status: **Current row counts partially known; growth rates unknown.**

Direct answer:

- The read-only snapshot can list current row counts, but it cannot establish growth rate without historical samples or warehouse/backup history.

Top current tables by row count from the 2026-08-13 read-only snapshot:

| Table | Rows |
|---|---:|
| `city` | 103,645 |
| `master_item_master` | 79,752 |
| `inv_vessel_inventory` | 46,558 |
| `master_component_spare_link` | 30,461 |
| `token_blacklist_outstandingtoken` | 29,753 |
| `token_blacklist_blacklistedtoken` | 29,752 |
| `wrh_audit_trail` | 15,918 |
| `pms_class_spare_applicability_rule` | 13,934 |
| `psc_notification` | 13,675 |
| `wrh_condition_tags` | 10,871 |
| `msc_notification` | 10,809 |
| `audit_event` | 9,637 |
| `psc_opensource_deficiency_record` | 8,089 |
| `wrh_s520_day_entry` | 7,801 |
| `pms_equipment_instance` | 7,514 |
| `pms_system_membership` | 7,514 |
| `stock_count_item` | 7,262 |
| `pms_functional_location` | 5,996 |
| `state` | 5,078 |
| `defect_event` | 4,799 |

VIMS-family row totals from the same snapshot:

| Family | Tables | Rows |
|---|---:|---:|
| `psc` / `PSC` | 22 | 23,767 |
| `vims_certs` | 19 | 3,332 |
| `vims_safety` | 38 | 1,910 |
| identity/reference sample | 6 | 2,162 |
| generic `sync_*` | 3 | 5 |

Evidence gap:

- Capture the same row-count and size query monthly, or derive growth from backups/warehouse history for at least 6-12 months.
- Include table size, index size and attachment/blob storage separately.

Owner to confirm: DBA and infrastructure.

### D7. Which tables are vessel-scoped versus fleet-wide reference data?

Status: **Partial. Clear examples exist; a complete table-by-table scope matrix is missing.**

Direct answer:

- PSC, Certs and Safety each have vessel-scoped records, while master/reference/identity tables are shared or fleet-wide. The repo does not provide a complete sync-scope matrix for all 552 tables.

Evidence-backed vessel-scoped examples:

- PSC inspections and activity history have `vessel_id` fields/indexes (`psc-backend/apps/inspection/models.py:48-133`, `psc-backend/apps/car/models.py:258-295`).
- PSC sync logs, conflicts and tokens are vessel-scoped (`psc-backend/apps/sync/models.py:67-104`, `psc-backend/apps/sync/models.py:171-206`, `psc-backend/apps/sync/models.py:215-236`).
- Certs tracked items carry `vessel_id` (`psc-backend/apps/certs/models/tracked_item.py:8-71`).
- Safety base records, SCM and near-miss KPI targets carry `vessel_id` (`psc-backend/apps/safety/models/base.py:15-35`, `psc-backend/apps/safety/models/scm.py:21-92`, `psc-backend/apps/safety/models/near_miss_config.py:46-67`).

Evidence-backed shared/reference examples:

- `VesselData`, `Crew_Onboarding_History`, `Ship_UsersLogin`, role/profile and master/reference tables are shared inputs (`Docs/BACKEND_STRUCTURE.md:86-180`).
- Safety master reference models are unmanaged shared/reference tables (`psc-backend/apps/safety/models/reference.py:22-131`).

Evidence gap:

- Build a complete matrix for every table: table, module owner, vessel-scoped/fleet-wide/global/user-specific, retention window, attachment dependency, sync direction, conflict policy and external writer.

Owner to confirm: Dev team plus DBA.

### D8. Which tables have no primary key?

Status: **Partially answered from current catalog. Full ownership classification still required.**

Direct answer:

- The 2026-08-13 read-only `ksm_marine_live` catalog shows 28 tables without a primary key.
- In the reviewed filter for `psc_%`, `vims_%`, `sync_%`, and core identity/reference tables (`Ship_UsersLogin`, `Crew_Onboarding_History`, `Final_crew_list`, `VesselData`, `HRM501`, `users`), zero matching tables lacked a primary key.
- This does not prove the 28 PK-less tables are irrelevant; their owners and sync relevance are unknown.

Evidence gap:

- List all 28 PK-less tables with owner, row count, last write, use path and whether any are in offline/sync or reporting scope.

Owner to confirm: DBA and module owners.

### D9. What is the current SQL Server edition, update level, recovery model, and collation?

Status: **Answered for the current connector target; production confirmation still required.**

Direct answer:

- The 2026-08-13 read-only connector target reported:
  - Database: `ksm_marine_live`
  - Server: `HIMANI`
  - Product version: `15.0.2000.5`
  - Product level: `RTM`
  - Edition: `Developer Edition (64-bit)`
  - Recovery model: `SIMPLE`
  - Collation: `SQL_Latin1_General_CP1_CI_AS`
  - Compatibility level: `120`
  - Query Store: off
- This answers the local/current connector target only. It must be confirmed against production before making licensing, HA, backup, restore or performance decisions.

Repository evidence:

- Docs state SQL Server 2019 and database `ksm_marine_live` (`Docs/TECH_STACK.md:173-175`).
- Backend settings use SQL Server through `mssql` and ODBC Driver 18 (`psc-backend/core/settings.py:111-116`, `psc-backend/core/settings.py:128-133`).

Evidence gap:

- Capture production `SERVERPROPERTY`, database properties, recovery model, compatibility level, Query Store, max memory, tempdb configuration, file layout, backup history and HA/DR configuration.

Owner to confirm: DBA.

### D10. Is there any existing replication, ETL, log shipping, or sync?

Status: **App-level PSC sync exists. Database-level replication/ETL/log shipping is unknown.**

Direct answer:

- The repo implements PSC application-level sync: frontend IndexedDB queue/pull/push and backend sync endpoints/tables.
- The current database snapshot shows `psc_sync_*` tables exist but contain zero rows, so live PSC sync usage is not demonstrated by this snapshot.
- No repo evidence proves SQL Server replication, Change Data Capture, Change Tracking, log shipping, ETL, SSIS, SQL Agent jobs or reporting replicas.

Repository evidence:

- Frontend sync queue and sync service exist (`psc-frontend/src/lib/db/sync-queue.ts:2-168`, `psc-frontend/src/lib/sync/sync-service.ts:131-257`).
- Backend sync models define `psc_sync_log`, `psc_sync_log_detail`, `psc_sync_conflict` and `psc_sync_token` (`psc-backend/apps/sync/models.py:58-236`).
- Backend sync routes expose pull, push, upload, resolve-conflict and conflicts (`psc-backend/apps/sync/urls.py:24-31`).
- PSC backend docs define sync tables and idempotency/conflict concepts (`Docs/BACKEND_STRUCTURE.md:681-782`).

Evidence gap:

- DBA to confirm SQL Server replication, CDC, Change Tracking, SQL Agent ETL, SSIS, linked servers, log shipping, backups/restores and reporting replicas.

Owner to confirm: DBA and operations.

### D11. How much data would a single vessel actually need locally?

Status: **Unknown.**

Direct answer:

- The repo proves that PSC has vessel-scoped offline/sync-capable entities, but it does not calculate the data volume a single vessel needs locally for PSC, Safety, Certs, Circular, ORB or shared reference data.
- The current database row counts show total system scale, not per-vessel offline storage requirements.

Evidence gap:

- For each active vessel, calculate current row counts and serialized payload/blob sizes for candidate local datasets: PSC inspections/CARs/evidence/activity, Safety incidents/SCM/SOI/evidence, Certs tracked items/PDF metadata/class snapshots, Circular ship notifications/acknowledgements/PDFs and shared reference data.
- Compare 30-day, 90-day, current-open-workflow, current-year and full-history retention windows.
- Include attachment/PDF/blob storage separately from relational JSON/cache storage.

Owner to confirm: DBA, dev team, Product Owner and vessel IT.
ch data would a single vessel actually need locally?

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
ere flag-state, classification-society, or ISM cyber requirements?

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
