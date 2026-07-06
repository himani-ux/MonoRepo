# IMPLEMENTATION_PLAN.md — Master Build Blueprint

## VIMS Safety Module — Incident / Near Miss / SCM / SOI

**Version:** 1.0 | **Date:** 2026-04-17 | **Status:** FROZEN
**Decision Owner:** Prince (Product Owner), DPA (sign-off at Phase 0 kickoff)
**Module home:** `apps/safety/` (Django) + `src/routes/safety/` + `src/components/safety/` + `src/hooks/safety/` + `src/stores/safety/` + `src/schemas/safety/` (React) within the **VIMS monorepo**
**Database:** `ksm_marine_live` (shared with Reporting / Inspection / Platform — **no new DB**)

---

## Document Policy

This plan is **FROZEN** once written. It is never modified during execution. It is the map.

- Step references use the format `{Phase}.{Step}` (e.g., `0.1`, `1.3`, `8.12`).
- Feature IDs reference `FEAT-SAF-<domain>-<seq>` as defined in `PRD.md` (115 IDs total across INC / NM / SCM / SOI / XMOD / PDF / AUDIT / DASH / RBAC).
- Backend file paths are relative to the VIMS monorepo root. Frontend paths are relative to `src/`.
- Test paths live under `tests/safety/` (pytest) and `tests/frontend/safety/` (vitest / Playwright).
- Execution state is tracked in `progress.txt` — this file never changes.
- Decision IDs `D-*` and `D-GAP-*` trace back to `VIMS-SAFETY-MODULE-SSOT.md` §6.

**Stack Reference (pinned — see `TECH_STACK.md`):** Python 3.12.4, Django 5.2.7, DRF 3.14.0, SimpleJWT 5.3.1, mssql-django 1.6, pyodbc 5.1.0, Celery 5.4.0, Redis 7.x, django-celery-beat 2.6.0, ReportLab 4.2.0, PyPDF2 3.0.1, openpyxl 3.1.5, Pillow 10.4.0, qrcode 7.4.2, python-barcode 0.15.1, React 18.3.1, TypeScript 5.4.5, Vite 5.4.0, TanStack Query 5.51.1, Zustand 4.5.4, Zod 3.23.8, react-hook-form 7.52.1, Tailwind 3.4.7, Recharts 3.7.0, Workbox 7.1.0, idb 8.0.0.

**Naming Conventions (law):**
- Module (transactional) tables → `vims_safety_*` prefix (14 tables per BACKEND §4)
- Shared reference tables → `master_*` prefix (8 Safety-owned per BACKEND §5 + 4 platform-owned consumed read-only)
- **Zero bare `safety_*` prefixes.** Any historical drift from the SSOT translates on implementation.
- Permission IDs → `SAF_F_*` (Form) + `SAF_P_*` (Process) — stored in shared `msc_profiles`, not a new table.
- Component prefix → `Safety*` (e.g., `SafetyIncidentPhase3Form.tsx`).
- Backend files → `snake_case.py`. Frontend files → `kebab-case.tsx` / `kebab-case.ts`. Components → `PascalCase` export, `kebab-case` filename.

**Blocked items (Round 20 build-time deferrals surface in Phase 8):**
- FTS engine selection (§2.3 TECH_STACK) — LIKE-based narrow search in V1.
- SOI unique-ID visual encoding (QR vs Code128 vs plain) — library versions pinned; template is one-line change.

**Arbitration order (per master prompt):** `<database_naming_convention>` > `<vims_integration>` > SSOT > BACKEND_STRUCTURE > APP_FLOW > PRD > DESIGN_SYSTEM > VALIDATION_RULES.

---

## Phase Overview

| Phase | Purpose | Steps |
|-------|---------|-------|
| 0 | VIMS monorepo scaffold — apps/safety/ + React routes/components + Django AppConfig + URL include + seed-load masters + migration ordering | 6 |
| 1 | Incident module — 9-phase workflow (Intake → Notifications → Evidence → Sequence → Analysis → Recommendations → Actions → Verification → Closure) + supporting services | 14 |
| 2 | Near Miss module — anonymity-first + triage + fleet alert | 6 |
| 3 | SCM Regular + Ad-Hoc — shared form + RBAC differentiation + WRH attendance + SOI auto-feed | 8 |
| 4 | SOI — paper-first 13-area checklist, 329-item taxonomy, Section 12 quarterly, finding workflow | 12 |
| 5 | Cross-module integrations — Reporting / WRH / CMS / Purchase live joins (PMS DECOUPLED, D-GAP-I1) | 6 |
| 6 | PDF generation — 10-section incident, NM lightweight, SCM, SOI, MSC-MEPC.3/Circ.4, auditor ZIP | 6 |
| 7 | Dashboards / reporting / lessons-learned — Safety Intelligence Dashboard, search, exports, archive opt-in | 8 |
| 8 | Build-time deferral resolutions — 12 steps, one per deferral row in BACKEND §8 | 12 |

Total: **78 numbered steps** mapping **115 FEAT-SAF-* IDs**.

---

## Phase 0 — VIMS Monorepo Scaffold

Purpose: establish the Safety module inside the VIMS monorepo with correct Django registration, URL include, DB router posture, seed-loaded master reference tables, and React route shells. Mirrors Reporting Phase 0 Steps 0.1–0.4 with the Safety addition of `anonymity.py` (D-GAP-J1) and a seed-load step for the four Safety reference CSVs.

---

### Step 0.1 — Django Project Structure for `apps.safety`

**Description:** Create the `apps/safety/` Django app inside the VIMS monorepo, mirroring `apps/reporting/`. Register the AppConfig, create empty sub-packages (`models/`, `repositories/`, `authentication/`, `views/`, `serializers/`, `migrations/`, `services/`), and confirm the `ksm_marine_live` DB router directs Safety ORM traffic correctly. No tables yet — just the skeleton.

**Files to create:**
- `apps/safety/__init__.py`
- `apps/safety/apps.py` — `class SafetyConfig(AppConfig): name = 'apps.safety'`
- `apps/safety/urls.py` — empty router, reserved for Step 0.4 / later phases
- `apps/safety/admin.py` — registration stub
- `apps/safety/models/__init__.py`
- `apps/safety/repositories/__init__.py`
- `apps/safety/authentication/__init__.py`
- `apps/safety/views/__init__.py`
- `apps/safety/serializers/__init__.py`
- `apps/safety/services/__init__.py`
- `apps/safety/migrations/__init__.py`
- `apps/safety/management/__init__.py`
- `apps/safety/management/commands/__init__.py`

**PRD features delivered:** Foundation (no FEAT ID — infrastructure).

**Tests to write:**
- Unit: `tests/safety/test_app_registration.py` — `apps.safety` resolves via `django.apps.apps.get_app_config('safety')`; router sends `apps.safety` models to `ksm_marine_live`; no other DB alias created.
- Integration: `tests/safety/test_db_connection.py` — live connect to `ksm_marine_live` via pyodbc 5.1.0, confirm read of `master_role` + `master_RoleByVessel` + `master_applied_rank` is possible (platform precondition); default DB unchanged.

**Dependencies:**
- Requires VIMS platform (Django 5.2.7, mssql-django 1.6) already provisioned.
- Requires Reporting module `apps/reporting/` and `config/database_router.py` present (pattern source).
- Requires `ksm_marine_live` reachable on port 1433 with ODBC Driver 18.

**Decisions:** `<vims_integration>` folder tree; TECH_STACK §1.1–§1.3; BACKEND §1.1.

---

### Step 0.2 — Base Models, Auth, and Anonymity Layer

**Description:** Create the `BaseSafetyRecord` abstract model that every transactional Safety table inherits from (vessel FK, state, created_by, updated_by, is_deleted, schema_version). Integrate the platform SimpleJWT auth by wiring `HasFormPermission` / `HasProcessPermission` DRF permission classes that check `SAF_F_*` / `SAF_P_*` IDs from `msc_profiles` via the shared auth chain. Implement **`anonymity.py`** — the Near Miss reporter-identity stripping layer (D-GAP-J1) — at the serializer level so any viewer not in {DPA, FM, reporter-self} receives scrubbed output.

**Files to create:**
- `apps/safety/models/base.py` — `class BaseSafetyRecord(models.Model)`: `vessel_id` (FK to `VesselData`), `state` (CharField with choices per module), `created_by`, `created_date`, `updated_by`, `updated_date`, `is_deleted` (BIT default False), `schema_version` (CharField) per D-GAP-I9. `Meta: abstract = True`.
- `apps/safety/authentication/__init__.py` — package init
- `apps/safety/authentication/backends.py` — thin wrapper that imports `SimpleJWTAuthentication` from VIMS platform; no new logic.
- `apps/safety/authentication/permissions.py` — `HasFormPermission(required_form_id=...)` + `HasProcessPermission(required_process_id=...)` DRF classes, reading `form_ids` / `process_ids` from the JWT-populated user object.
- `apps/safety/authentication/vessel_scope.py` — `filter_by_vessel_scope(qs, user)`: office → `master_RoleByVessel`; ship → `Crew_Onboarding_History`; global-access role bypasses.
- `apps/safety/authentication/anonymity.py` — `AnonymityMixin` (serializer mixin) + `can_see_reporter(user, record)` helper; strips `reporter_user_id`, `reporter_name`, `reporter_rank`, `reporter_email`, `created_by`, `updated_by` when `record_type == NEAR_MISS` and viewer role ∉ {DPA, FM, reporter-self}. Enforces D-GAP-J1.

**PRD features delivered:** `FEAT-SAF-RBAC-005` (permission IDs plumbed), `FEAT-SAF-NM-002` (reporter masking enforcement plumbing), `FEAT-SAF-AUDIT-005` (schema_version column plumbed).

**Tests to write:**
- Unit: `tests/safety/test_base_model.py` — abstract inheritance; `is_deleted` default False; `schema_version` required.
- Unit: `tests/safety/test_permissions.py` — `HasFormPermission(SAF_F_001)` passes with matching form_id, rejects otherwise; `HasProcessPermission(SAF_P_003)` same.
- Unit: `tests/safety/test_vessel_scope.py` — office user scoped by `master_RoleByVessel`; ship-side scoped by `Crew_Onboarding_History`; global-access sees all.
- Unit: `tests/safety/test_anonymity.py` — Near Miss serializer output scrubs reporter PII for Master/HOD/CO; full visibility for DPA, FM, self-reporter (D-GAP-J1).
- Integration: `tests/safety/test_auth_jwt.py` — JWT issued via VIMS SimpleJWT carries `SAF_F_*`/`SAF_P_*` IDs; expired token rejected.

**Dependencies:**
- Requires Step 0.1 (app scaffold).
- Requires platform masters `master_role`, `master_RoleByVessel`, `master_applied_rank`, `msc_profiles`, `Crew_Onboarding_History` present (platform precondition).
- Requires Reporting `apps/reporting/authentication/` pattern (clone, don't duplicate DI).

**Decisions:** D-GAP-J1 (anonymity), D-GAP-H1 (auth inheritance), D-GAP-A3/A4/A6 (rank persists), BACKEND §3.

---

### Step 0.3 — SP Wrapper / Repository Base

**Description:** Create `BaseRepository` for Safety by extending the Reporting SP wrapper pattern. Provides `execute_sp(sp_name, params)` with deadlock retry (3 attempts), timeout, parameter validation, structured error mapping. All DB reads for cross-module live joins (WRH, CMS, Purchase, Reporting) go through repositories in later phases — raw cursor calls are forbidden. Supplies Safety-specific exception classes for phase-transition conflicts and anonymity-mask violations.

**Files to create:**
- `apps/safety/repositories/base.py` — `class BaseRepository`: `execute_sp(sp_name, params)`, `execute_query(sql, params)`, `execute_scalar(sql, params)`. Uses `django.db.connections['default']` (which resolves to `ksm_marine_live` via Safety router). Retries on deadlock, structured logging, returns dicts via `cursor.description`.
- `apps/safety/repositories/exceptions.py` — `SPExecutionError`, `SPTimeoutError`, `SPDeadlockError`, `SPParameterError`, `PhaseTransitionError`, `AnonymityMaskError`.

**PRD features delivered:** Foundation.

**Tests to write:**
- Unit: `tests/safety/test_base_repository.py` — mock cursor for SP call, deadlock retry (2 failures then success), timeout mapping, parameter validation, dict result format, connection reuse.

**Dependencies:**
- Requires Step 0.2 (base models, auth).
- Requires Reporting `apps/reporting/repositories/base.py` (pattern clone).

**Decisions:** BACKEND §1.1; TECH_STACK §1.3.

---

### Step 0.4 — React Route + Component + Hook + Store + Schema Scaffolding

**Description:** Wire `/safety/*` routes into the existing VIMS React Router configuration using lazy-loaded route modules. Each route is wrapped in `PermissionGate` checking the required `SAF_F_*` form_id. Create empty `src/components/safety/{shared,incident,near-miss,scm,soi}/`, `src/hooks/safety/`, `src/stores/safety/`, and `src/schemas/safety/` sub-folders. Add the "Safety" sidebar menu group hidden for users with no `SAF_F_*` IDs. Mount the shared `SafetyLayout` chrome (breadcrumbs, vessel dropdown slot).

**Files to create:**
- `src/routes/safety/index.tsx` — lazy-loaded route definitions for `/safety/incidents/*`, `/safety/near-miss/*`, `/safety/scm/*`, `/safety/soi/*`, `/safety/dashboard/*`, `/safety/search/*`, `/safety/admin/*`. Each route wrapped `<PermissionGate formId="SAF_F_00X">`. Placeholder pages for routes implemented in later phases.
- `src/routes/safety/layout.tsx` — `<SafetyLayout>` with breadcrumb + vessel dropdown slot + `<Outlet />`.
- `src/components/safety/shared/permission-gate.tsx` — `<PermissionGate formId=...>` / `<ProcessGate processId=...>`.
- `src/components/safety/shared/safety-sidebar-group.tsx` — hidden when no SAF_F_* IDs; emits badges for open incidents / near-miss / findings.
- `src/hooks/safety/use-auth.ts` — reads auth store, exposes `hasForm(SAF_F_XXX)` / `hasProcess(SAF_P_XXX)` / `role` / `vesselIds` / `isGlobal`.
- `src/stores/safety/incident-draft-store.ts` — Zustand placeholder for incident draft state (populated Phase 1).
- `src/stores/safety/soi-picker-store.ts` — Zustand placeholder for SOI area selection (populated Phase 4).
- `src/stores/safety/scm-draft-store.ts` — Zustand placeholder (populated Phase 3).
- `src/schemas/safety/common.ts` — Zod common schemas (vessel_id, timestamps, attachment refs, schema_version).

**PRD features delivered:** `FEAT-SAF-RBAC-005` (form gating plumbed), `FEAT-SAF-RBAC-006` (cross-vessel visibility respects scope).

**Tests to write:**
- Unit: `tests/frontend/safety/routes.test.tsx` — `/safety/incidents` renders when user has `SAF_F_001`; returns null sidebar entry when user has zero SAF_F_* IDs.
- Unit: `tests/frontend/safety/permission-gate.test.tsx` — renders children when form_id present; renders null when absent; nested `<ProcessGate>` respected.
- Unit: `tests/frontend/safety/use-auth.test.ts` — `hasForm`/`hasProcess` boolean correctness.

**Dependencies:**
- Requires Step 0.2 (permissions plumbed server-side).
- Requires Reporting `src/routes/reporting/` pattern.
- Requires platform auth store already populating `form_ids` / `process_ids`.

**Decisions:** APP_FLOW §3 route map; BACKEND §1.4; FRONTEND_GUIDELINES component prefix.

---

### Step 0.5 — Seed-Load `master_*` Reference Tables from `safety-reference-data/`

**Description:** Create the `0002_seed_master_tables.py` data migration (or equivalent management command + migration) that ingests the four Safety reference CSVs into their `master_*` tables: MSCAT taxonomy (174 rows), immediate causes (52 rows), loss types (7 rows), SOI checklist items (329 rows baseline + 12 cross-cutting). Also seeds `master_soi_area` (13 rows), `master_safety_incident_type` (11 rows per SSOT §2B.5), `master_safety_bias_guard` (8 rows per Round 21 R12), and `master_soi_checklist_version` (first row = v1 pointing to 329-item seed). Migration is idempotent — re-running produces no duplicates.

**Files to create:**
- `apps/safety/management/commands/seed_master_safety.py` — reads the four CSVs from `safety-reference-data/`, upserts rows by natural key. Logs counts + row-diff.
- `apps/safety/migrations/0002_seed_master_tables.py` — data migration invoking the command or performing inline SQL inserts. Depends on `0001_initial`.
- `apps/safety/fixtures/master_soi_area.json` — 13 area rows (12 physical + Section 12 cross-cutting).
- `apps/safety/fixtures/master_safety_incident_type.json` — 11 incident-type rows.
- `apps/safety/fixtures/master_safety_bias_guard.json` — 8 bias-guard rows (5 DNV + 3 organisational traps).
- `apps/safety/fixtures/master_soi_checklist_version.json` — v1 row.

**PRD features delivered:** `FEAT-SAF-SOI-001` (13-area seeded), `FEAT-SAF-SOI-003` (versioned templates seeded v1), `FEAT-SAF-INC-017` (MSCAT picker 174-row backend), `FEAT-SAF-INC-024` (8 bias guards seeded), `FEAT-SAF-RBAC-008` (DPA-only taxonomy maintenance — schema present; CRUD in Phase 7).

**Tests to write:**
- Unit: `tests/safety/test_seed_master_safety.py` — after running seed, `master_mscat_taxonomy` has 174 rows; `master_immediate_causes` has 52; `master_loss_types` has 7; `master_soi_area_item` has 329; `master_soi_area` has 13; `master_safety_incident_type` has 11; `master_safety_bias_guard` has 8. Re-run produces no duplicates (upsert by natural key).
- Integration: `tests/safety/test_master_csv_mapping.py` — CSV column headers match DDL columns exactly (no drift vs BACKEND §5 schema).

**Dependencies:**
- Requires Step 0.1 (app scaffold).
- Requires `0001_initial` migration from Step 0.6 (master table DDL created).
- Requires `safety-reference-data/` CSVs committed at project root (already present per SSQE/Session 5 seed artifacts).

**Decisions:** BACKEND §5.1–§5.8; D-GAP-INC-15 (MSCAT source of truth); D-SOI-16 (13 areas); Round 21 R12 (8 bias guards).

---

### Step 0.6 — Django App Registration + URL Include + `0001_initial` Migration

**Description:** Register `apps.safety` in `INSTALLED_APPS`, mount `path('api/safety/', include('apps.safety.urls'))` under the platform `config/urls.py`, and author the `0001_initial.py` migration containing the DDL for all 14 `vims_safety_*` transactional tables + the 8 `master_*` reference tables (shells — seed data arrives via Step 0.5 `0002_seed_master_tables.py`). Migration explicitly declares dependencies on the platform masters that Safety FKs into.

**Files to create:**
- `config/settings/base.py` (edit) — `INSTALLED_APPS += ['apps.safety']`.
- `config/urls.py` (edit) — `path('api/safety/', include('apps.safety.urls'))`.
- `apps/safety/migrations/0001_initial.py` — DDL for the 14 `vims_safety_*` tables (per BACKEND §4.1–§4.14) and the 8 `master_*` table shells (per BACKEND §5.1–§5.8). `dependencies = [('platform', '0001_bootstrap')]` (or the equivalent platform app label) asserting `master_role`, `master_RoleByVessel`, `master_applied_rank`, `master_notification`, `Crew_Onboarding_History`, `VesselData`, `msc_profiles` are present before Safety migrates.
- `apps/safety/migrations/0003_seed_permission_ids.py` — inserts the `SAF_F_001..004` + `SAF_P_001..0XX` rows into `msc_profiles` per BACKEND §13.4.

**PRD features delivered:** Foundation + `FEAT-SAF-RBAC-005` (permission IDs registered).

**Tests to write:**
- Integration: `tests/safety/test_migration_apply.py` — fresh DB `makemigrations --check` produces no diff; `migrate apps.safety` creates 14 + 8 tables; `master_role` / `master_RoleByVessel` present before Safety migrates (dependency order enforced).
- Integration: `tests/safety/test_url_include.py` — `/api/safety/` resolves to `apps.safety.urls`; 401 response when no JWT (baseline auth check).
- Unit: `tests/safety/test_permission_seed.py` — `SAF_F_001`..`SAF_F_004` + `SAF_P_001`..`SAF_P_004` seeded into `msc_profiles`.

**Dependencies:**
- Requires Steps 0.1, 0.2, 0.3, 0.4 (scaffolding + DDL author inputs).
- Requires Step 0.5 migration file exists (0002 depends on 0001 existing).
- Requires platform migration for `master_role`, `master_RoleByVessel`, `master_applied_rank`, `master_notification`, `Crew_Onboarding_History`, `VesselData`, `msc_profiles` applied first (migration dependency enforces order).

**Decisions:** BACKEND §1.2 (`INSTALLED_APPS`), §1.3 (URL include), §13 (migration ordering); `<vims_integration>` folder tree; D-GAP-I2 (same DB `ksm_marine_live`).

---

## Phase 1 — Incident Module (9-Phase Workflow)

Purpose: Build the full 9-phase incident investigation workflow per SSOT §2A, DNV M-SCAT RCA methodology (Round 21), and KSM SSQE Manual §11. Includes all 41 `FEAT-SAF-INC-*` features plus the supporting audit infrastructure (`vims_safety_incident_phase_log`, `vims_safety_field_history`). Every phase transition is phase-log-logged (append-only); every field edit is field-history-logged. Risk band (GREEN / YELLOW / RED) + IMO SMC/MC/MI classifier (D-GAP-R08 option b) drive routing.

---

### Step 1.1 — `vims_safety_incident` CRUD + Record-Type Discriminator

**Description:** Core `vims_safety_incident` table houses **both Incident and Near Miss** records via `record_type` discriminator column (SSOT §2B.1, BACKEND §4.1). This step creates the base Incident repository / serializer / views. `current_phase` field (1..9) drives the 9-phase state machine. Incident-number auto-assign on creation follows `{VesselCode}/INC/{YYYY}/{NNN}` with a draft-reference series `DRAFT-{uuid4[:8]}` before phase 1 commits (FEAT-SAF-INC-040). Schema-versioned (`schema_version` column) per D-GAP-I9 / FEAT-SAF-AUDIT-005 — historical records always render against their creation-time schema (grandfather rule).

**Files to create:**
- `apps/safety/models/incident.py` — `class Incident(BaseSafetyRecord)`: `record_type` (INCIDENT | NEAR_MISS), `incident_number`, `draft_reference`, `current_phase` (1..9, default 1), `risk_band` (GREEN/YELLOW/RED, D-GAP-R07), `imo_classifier` (SMC/MC/MI/internal-only, D-GAP-R08), `incident_type_id` (FK `master_safety_incident_type`), `loss_type_primary_id` (FK `master_loss_types`), `date_time`, `location_lat/lon`, `port_id`, `narrative_intake`, `scene_control_actions`, plus Phase 2..8 aggregate columns per BACKEND §4.1. Table `vims_safety_incident`.
- `apps/safety/repositories/incident_repo.py` — `IncidentRepository(BaseRepository)`: `create`, `read`, `update`, `list_by_vessel`, `get_by_number`, `assign_number(vessel_code, year) -> str`, `allocate_draft_reference() -> str`. Row-lock for numbering.
- `apps/safety/serializers/incident.py` — `IncidentSerializer` (AnonymityMixin-wrapped), `IncidentListSerializer`, `IncidentCreateSerializer`.
- `apps/safety/views/incident.py` — `IncidentListCreateView` (GET `SAF_F_001` / POST `SAF_P_001`), `IncidentDetailView` (GET/PATCH).
- `apps/safety/urls.py` (append) — `incidents/`, `incidents/<uuid:id>/`.
- `src/routes/safety/incident/index.tsx` — list page (filter by date / vessel / risk_band / state). TanStack Query key `['safety', 'incidents', vesselId, filters]`.
- `src/schemas/safety/incident.ts` — Zod schema (matches Django serializer + schema_version).
- `src/stores/safety/incident-draft-store.ts` (extend) — draft-in-progress persistence.

**PRD features delivered:** `FEAT-SAF-INC-040` (incident number + draft reference), `FEAT-SAF-AUDIT-005` (schema versioning grandfather), `FEAT-SAF-RBAC-002` (creation gate — top-4 officers via `SAF_P_001`).

**Tests to write:**
- Unit: `tests/safety/test_incident_model.py` — BaseSafetyRecord inheritance, defaults, record_type enum, schema_version required.
- Integration: `tests/safety/test_incident_crud.py` — create/read/update/list; scoped by vessel; anonymity mask (only matters for NEAR_MISS record_type, verified Phase 2).
- Unit: `tests/safety/test_incident_numbering.py` — `{VesselCode}/INC/{YYYY}/{NNN}` format, year reset, uniqueness under concurrent creation, draft-reference prefix `DRAFT-` until number assigned.
- E2E: `tests/frontend/safety/incident-list.spec.ts` — `/safety/incidents` renders for SAF_F_001 holders; vessel scope respected.

**Dependencies:** 0.2, 0.3, 0.6.

**Decisions:** D-GAP-INC-01 (9-phase), D-GAP-R07 (risk bands), D-GAP-R08 (IMO classifier alongside band), D-GAP-I9 (schema versioning), FEAT-SAF-INC-040.

---

### Step 1.2 — Phase Log + Field History Infrastructure

**Description:** Create the append-only `vims_safety_incident_phase_log` (state-machine audit) and `vims_safety_field_history` (field-level edit log) tables and service layer. Every phase transition writes a phase_log row; every PATCH on an Incident field writes a field_history row. Phase transitions are enforced via `PhaseStateMachine` — rejects illegal jumps (e.g., Phase 3 → Phase 5) and rejects Phase N→N+1 if prior-phase completion gates fail (e.g., Phase 5 loop-back gate if cause-tree absent). Field-history shape locked to **Option A TEXT** per BACKEND §4.3 interim lock — Phase 8 Step 8.2 revisits per deferral #2.

**Files to create:**
- `apps/safety/models/phase_log.py` — `class IncidentPhaseLog(models.Model)` with `incident_id` FK, `phase_from`, `phase_to`, `transition_reason`, `transitioned_by`, `transitioned_at`. Table `vims_safety_incident_phase_log`. Append-only (no UPDATE / DELETE at ORM level; DB-level trigger in migration).
- `apps/safety/models/field_history.py` — `class SafetyFieldHistory(models.Model)` with `record_id`, `record_type` (INCIDENT/NEAR_MISS/SCM/SOI), `field_name`, `old_value` (TEXT), `new_value` (TEXT), `changed_by`, `changed_at`. Table `vims_safety_field_history`.
- `apps/safety/services/phase_state_machine.py` — `PhaseStateMachine.transition(incident_id, to_phase, user, reason=None) -> dict`. Gate checks per phase (Phase 5 requires ≥1 root cause + bias-guard checklist answered; Phase 6 requires ≥1 Tier-1 rec; etc.).
- `apps/safety/services/field_history_recorder.py` — `record_field_changes(record, old_state, new_state, user)`: diffs dict-on-dict, writes rows.
- `apps/safety/views/phase_log.py` — `PhaseLogView` (read-only, returns chronological log for an incident).
- `apps/safety/views/field_history.py` — `FieldHistoryView` (read-only, paginated by field_name).
- `src/components/safety/shared/phase-log-timeline.tsx` — visual timeline of phase transitions.
- `src/components/safety/shared/field-history-panel.tsx` — expandable panel with per-field diff view.

**PRD features delivered:** `FEAT-SAF-AUDIT-001` (append-only phase log), `FEAT-SAF-AUDIT-002` (field-level history), `FEAT-SAF-INC-016` (partial — Phase 5 loop-back gate enforcement).

**Tests to write:**
- Unit: `tests/safety/test_phase_log_append_only.py` — INSERT allowed; UPDATE/DELETE raises `IntegrityError` (DB trigger + ORM guard).
- Unit: `tests/safety/test_phase_state_machine.py` — Phase 1→2 allowed; Phase 3→5 rejected; Phase 5→6 rejected if no root cause; Phase 7→8 requires DPA acceptance stamp.
- Unit: `tests/safety/test_field_history_recorder.py` — diff captures only changed fields; stores TEXT values; timestamps correct.
- Integration: `tests/safety/test_field_history_patch.py` — PATCH `/api/safety/incidents/{id}/` writes one field_history row per changed field.

**Dependencies:** 1.1.

**Decisions:** D-GAP-D2 (no crypto in field history); D-GAP-INC-09 (append-only phase log); BACKEND §4.2, §4.3; deferrals #2 and #6 (interim lock).

---

### Step 1.3 — Phase 1: Intake + Scene Control

**Description:** Phase 1 form captures initial intake: date/time, location (lat/lon or port), narrative (min-length V-INC-001), initial scene-control actions, reporter identity (always stored, anonymity mask applies only for Near Miss — Phase 2 of this module handles near miss). Sets `current_phase = 1`. Self-report conflict guard (FEAT-SAF-INC-039) — if reporter_rank ∈ {Master, CO, CE, C/O} and is also PIC candidate, warns with acknowledgement gate. Incident-number format assigned at first save post-phase-1 commit.

**Files to create:**
- `apps/safety/serializers/incident_phase1.py` — `IncidentPhase1Serializer` (intake fields only, validates V-INC-001..V-INC-008).
- `apps/safety/views/incident_phase1.py` — `IncidentPhase1CreateView` (POST new incident starting Phase 1), `IncidentPhase1UpdateView` (PATCH intake fields while `current_phase = 1`), `IncidentPhase1SubmitView` (POST transition to Phase 2).
- `apps/safety/services/self_report_guard.py` — `check_self_report_conflict(reporter_id, incident_data) -> (bool, str)`.
- `src/routes/safety/incident/[id]/phase-1.tsx` — Phase 1 intake form.
- `src/components/safety/incident/phase1-form.tsx` — `<SafetyIncidentPhase1Form>` using react-hook-form + Zod.
- `src/components/safety/incident/self-report-guard-modal.tsx` — acknowledgement modal.
- `src/schemas/safety/incident-phase1.ts` — Zod schema (mirrors serializer validation).

**PRD features delivered:** `FEAT-SAF-INC-001` (Phase 1 Intake + Scene Control), `FEAT-SAF-INC-039` (self-report conflict guard), `FEAT-SAF-INC-036` (draft mode at any phase — partial; extends in Step 1.14).

**Tests to write:**
- Unit: `tests/safety/test_incident_phase1_validation.py` — V-INC-001 (narrative min-length), V-INC-002..V-INC-008 from VALIDATION_RULES §2.
- Integration: `tests/safety/test_incident_phase1_submit.py` — POST creates incident in Phase 1; PATCH update allowed; SUBMIT transitions to Phase 2 and writes phase_log row.
- Unit: `tests/safety/test_self_report_conflict.py` — Master-as-reporter triggers modal; acknowledgement proceeds; unacknowledged rejects submit.
- E2E: `tests/frontend/safety/incident-phase-1.spec.ts` — form renders, validation warnings, submit → phase 2 navigation.

**Dependencies:** 1.1, 1.2.

**Decisions:** D-GAP-INC-03/04 (intake requirements), D-GAP-R07 (risk-band plumbed but not decided until Phase 2), FEAT-SAF-INC-039.

---

### Step 1.4 — Phase 2: Notifications, Risk-Band, IMO Classifier, Resource Allocation

**Description:** Phase 2 captures DPA/FM notification timestamps, sets risk_band (GREEN / YELLOW / RED per D-GAP-R07), and sets IMO classifier (SMC / MC / MI / internal-only per D-GAP-R08 option b — classifier is **alongside** internal band, not reconciled). Also allocates PIC (who leads investigation). Band drives closure authority downstream (`FEAT-SAF-RBAC-001`): GREEN = PIC, YELLOW = DPA, RED = FM. RED band triggers additional notification queue writes to `master_notification` (shared platform queue).

**Files to create:**
- `apps/safety/serializers/incident_phase2.py` — `IncidentPhase2Serializer` with risk_band, imo_classifier, pic_user_id, dpa_notified_at, fm_notified_at, office_notified_at.
- `apps/safety/views/incident_phase2.py` — `IncidentPhase2UpdateView`, `IncidentPhase2SubmitView`.
- `apps/safety/services/band_classifier.py` — `classify_band(loss_type, injuries, pollution, damage) -> Band` (advisory helper; final set by investigator).
- `apps/safety/services/notification_writer.py` — `write_notification(record_id, recipients, kind)` — writes to platform `master_notification` queue (D-GAP-F2).
- `src/routes/safety/incident/[id]/phase-2.tsx` — Phase 2 form.
- `src/components/safety/incident/phase2-form.tsx` — includes risk-band picker, IMO classifier dropdown, PIC assignment widget, notification timestamps.
- `src/components/safety/incident/band-helper.tsx` — advisory display of `classify_band` output.
- `src/schemas/safety/incident-phase2.ts`.

**PRD features delivered:** `FEAT-SAF-INC-002` (IMO SMC/MC/MI classifier), `FEAT-SAF-INC-003` (internal risk band), `FEAT-SAF-INC-004` (notifications + resource allocation), `FEAT-SAF-XMOD-006` (shared notification queue via `master_notification`).

**Tests to write:**
- Unit: `tests/safety/test_phase2_risk_band.py` — GREEN/YELLOW/RED enum; no reconciliation with IMO classifier.
- Unit: `tests/safety/test_phase2_imo_classifier.py` — SMC/MC/MI/internal-only; co-exists with band.
- Unit: `tests/safety/test_band_classifier_helper.py` — advisory output matches SSQE §11 mapping.
- Integration: `tests/safety/test_phase2_submit.py` — transition to Phase 3 requires RED band notifications emitted; phase_log entry written.
- Integration: `tests/safety/test_notification_writer.py` — rows added to `master_notification` visible to platform notifier.

**Dependencies:** 1.3.

**Decisions:** D-GAP-R07 (band), D-GAP-R08 (classifier alongside band), D-GAP-F2 (notification best-effort), FEAT-SAF-RBAC-001 (band→closure), FEAT-SAF-XMOD-006.

---

### Step 1.5 — Phase 3: Evidence Workspace (5-Source Tabbed)

**Description:** Phase 3 is the evidence-collection workspace — 5 tabbed sources per DNV M-SCAT evidence framework: People, Position/Places, Parts/Equipment, Paper/Procedures, Photos/Plans. Supports Evidence Matrix (pro/con per finding, FEAT-SAF-INC-006), Chain-of-Custody tab (FEAT-SAF-INC-007), Marine Document Inventory auto-checklist (FEAT-SAF-INC-008, drawn from SSQE §11 doc list), Cargo-Specific Evidence Overlay (FEAT-SAF-INC-009 — contextual fields for bulk/tanker/container), Health/Fatigue sub-section (FEAT-SAF-INC-010 — live join to WRH for fatigue lookback), Evidence-Preservation Deadline Task List (FEAT-SAF-INC-011 — 72h/7d deadlines per Round 21 R04–R07/R10), Structured 4-Phase Interview Module (FEAT-SAF-INC-012), Formal vs Informal Interview flag (FEAT-SAF-INC-013), Witness Read-Back + Sign-Off Protocol (FEAT-SAF-INC-014).

**Files to create:**
- `apps/safety/models/evidence.py` — `IncidentEvidence`, `EvidenceItem`, `ChainOfCustody`, `WitnessInterview`, `EvidenceDeadlineTask` — all FK to incident. Tables under `vims_safety_incident` domain; see BACKEND §4.1 extension columns + Round-21 narrative fields.
- `apps/safety/serializers/incident_phase3.py` — per-tab serializers (5).
- `apps/safety/views/incident_phase3.py` — tab-scoped endpoints.
- `apps/safety/services/evidence_deadline_scheduler.py` — celery-beat task schedules 24h/72h/7d reminders to PIC when evidence task uncompleted (D-GAP-F3 pattern).
- `apps/safety/services/fatigue_live_join.py` — reads `wrh_attendance` and `wrh_daily_rest_hours` via repo for the affected crew in the 7 days preceding the incident (D-GAP-M26 timezone via `wrh_ship_time_config`).
- `src/routes/safety/incident/[id]/phase-3/people.tsx`, `places.tsx`, `parts.tsx`, `paper.tsx`, `photos.tsx` — 5 tabs.
- `src/components/safety/incident/evidence-matrix.tsx` — pro/con matrix UI.
- `src/components/safety/incident/chain-of-custody-table.tsx`.
- `src/components/safety/incident/marine-document-checklist.tsx`.
- `src/components/safety/incident/cargo-specific-overlay.tsx`.
- `src/components/safety/incident/health-fatigue-panel.tsx`.
- `src/components/safety/incident/evidence-deadline-tasks.tsx`.
- `src/components/safety/incident/interview-module.tsx` — 4-phase interview capture.
- `src/components/safety/incident/witness-readback.tsx`.
- `src/schemas/safety/incident-phase3.ts`.

**PRD features delivered:** `FEAT-SAF-INC-005` (5-source tabbed), `FEAT-SAF-INC-006` (evidence matrix), `FEAT-SAF-INC-007` (chain of custody), `FEAT-SAF-INC-008` (marine doc inventory), `FEAT-SAF-INC-009` (cargo overlay), `FEAT-SAF-INC-010` (health/fatigue sub-section), `FEAT-SAF-INC-011` (preservation deadline task list), `FEAT-SAF-INC-012` (4-phase interview), `FEAT-SAF-INC-013` (formal vs informal flag), `FEAT-SAF-INC-014` (witness read-back).

**Tests to write:**
- Unit: `tests/safety/test_phase3_tabs.py` — 5 tabs accept writes independently.
- Unit: `tests/safety/test_chain_of_custody.py` — evidence item transfers audit-logged.
- Unit: `tests/safety/test_evidence_deadline.py` — 24h / 72h / 7d deadline tasks created on Phase 2→3 transition.
- Integration: `tests/safety/test_fatigue_live_join.py` — 7-day WRH lookback returns correct rows; missing data warns (D-GAP-M11 pattern); timezone resolved via `wrh_ship_time_config`.
- Integration: `tests/safety/test_interview_4phase.py` — 4 phases required before interview marks complete; read-back text required for sign-off.
- E2E: `tests/frontend/safety/incident-phase-3.spec.ts` — 5 tabs navigable; evidence matrix save + cargo overlay pick-list renders cargo-type context.

**Dependencies:** 1.4; requires WRH `wrh_attendance` / `wrh_daily_rest_hours` / `wrh_ship_time_config` tables present in `ksm_marine_live` (platform precondition).

**Decisions:** Round 21 R04–R07, R10 (evidence preservation), Round 21 R08 (interview module), D-GAP-M11 + D-GAP-M26 (WRH lookback + timezone), FEAT-SAF-INC-005..014.

---

### Step 1.6 — Phase 4: Facts Systemized (Shared Fact Base)

**Description:** Phase 4 consolidates all evidence into a structured "fact base" — a single canonical list of facts with timestamps, sources, and confidence levels. Supports sequence-of-events editor (drag-reorder), contradiction flagging (two facts incompatible), and multi-vessel incident linking (FEAT-SAF-INC-032 — same incident spans multiple vessels via `related_incident_ids` array) + duplicate detection (FEAT-SAF-INC-032). Near-Miss → Incident supersede path (FEAT-SAF-INC-033) — when a near-miss is reclassified as incident, creates new incident linked back via `supersedes_near_miss_id`.

**Files to create:**
- `apps/safety/models/fact_base.py` — `IncidentFact` (incident_id, sequence_index, fact_text, source_evidence_id, confidence, contradicts_fact_id nullable).
- `apps/safety/serializers/incident_phase4.py`.
- `apps/safety/views/incident_phase4.py` — list/create/update/reorder fact; contradiction-flag endpoint.
- `apps/safety/services/incident_linker.py` — `link_multi_vessel_incidents(incident_ids)`, `detect_duplicates(vessel_id, date_range, narrative_fingerprint)`.
- `apps/safety/services/near_miss_supersede.py` — `supersede_near_miss(nm_id) -> new_incident`.
- `src/routes/safety/incident/[id]/phase-4.tsx`.
- `src/components/safety/incident/fact-base-editor.tsx` — drag-reorderable list.
- `src/components/safety/incident/multi-vessel-linker.tsx`.
- `src/components/safety/incident/duplicate-warning-banner.tsx`.
- `src/schemas/safety/incident-phase4.ts`.

**PRD features delivered:** `FEAT-SAF-INC-015` (Phase 4 Facts Systemized), `FEAT-SAF-INC-032` (multi-vessel linking + duplicate detection), `FEAT-SAF-INC-033` (NM → Incident supersede).

**Tests to write:**
- Unit: `tests/safety/test_fact_base.py` — add/reorder/contradict.
- Unit: `tests/safety/test_multi_vessel_linking.py` — bidirectional link; cycle prevention.
- Unit: `tests/safety/test_duplicate_detection.py` — same-vessel same-day narrative fuzzy match flags candidate.
- Integration: `tests/safety/test_nm_supersede.py` — new incident created, near-miss marked `superseded`, back-link stored.

**Dependencies:** 1.5 (evidence feeds facts); 2.1 (near-miss creation path for supersede).

**Decisions:** D-GAP-INC-11 (fact base shape), FEAT-SAF-INC-015/032/033.

---

### Step 1.7 — Phase 5: Causal Analysis + Loop-Back Gate

**Description:** Phase 5 is the analytical heart — M-SCAT Cause Picker (FEAT-SAF-INC-017, 174-code picker from `master_mscat_taxonomy`), Causal Layering Tag (FEAT-SAF-INC-018 — Immediate / Intermediate / Root per Round 21 R01), Multiple Root Causes with no artificial cap (FEAT-SAF-INC-019 per Round 21 R03), Multi-Tool Analysis Workspace (FEAT-SAF-INC-020 — 5-Whys, Fishbone, Barrier, TapRoot-lite), Investigation-Depth Task Triangle (FEAT-SAF-INC-021), People/Process/Plant Interrogatory (FEAT-SAF-INC-022), Safeguard-Failure Interrogatory (FEAT-SAF-INC-023), 8 Bias Guards (FEAT-SAF-INC-024, seeded Step 0.5 `master_safety_bias_guard`), Blame-Fixation Hard Block + Override (FEAT-SAF-INC-025), Human Factors SHELL + IMO A.884(21) + Risk/Change (FEAT-SAF-INC-026). Phase 5 loop-back gate (from Step 1.2): cannot advance to Phase 6 until ≥1 root cause declared AND all 8 bias guards acknowledged AND (if blame-fixation flagged) override justification written.

**Files to create:**
- `apps/safety/models/causal_analysis.py` — `IncidentCauseTag` (incident_id, mscat_code_id FK, causal_layer {IMMEDIATE|INTERMEDIATE|ROOT}, rationale), `IncidentBiasGuardResponse` (incident_id, bias_guard_id FK, acknowledged, notes), `IncidentBlameOverride` (justification, approved_by).
- `apps/safety/serializers/incident_phase5.py`.
- `apps/safety/views/incident_phase5.py` — M-SCAT picker endpoint with search, causal-layer CRUD, bias-guard checklist, blame override.
- `apps/safety/services/blame_detector.py` — heuristic scanner of causal tags + narrative for blame-fixation language; raises gate.
- `apps/safety/services/mscat_search.py` — LIKE-based v1 search (FTS fallback pre-Phase 8); returns top 20 matches.
- `src/routes/safety/incident/[id]/phase-5.tsx`.
- `src/components/safety/shared/mscat-picker.tsx` — `<SafetyMScatPicker>` — 174-code searchable picker (reusable across Safety).
- `src/components/safety/shared/causal-layer-tabs.tsx` — Immediate / Intermediate / Root tab hierarchy per DESIGN_SYSTEM §4.
- `src/components/safety/shared/bias-guard-checklist.tsx` — `<SafetyBiasGuardChecklist>` 8-item mandatory checklist.
- `src/components/safety/incident/multi-tool-workspace.tsx` — 5-Whys / Fishbone / Barrier / TapRoot-lite tabs.
- `src/components/safety/incident/investigation-depth-triangle.tsx`.
- `src/components/safety/incident/people-process-plant-interrogatory.tsx`.
- `src/components/safety/incident/safeguard-failure-interrogatory.tsx`.
- `src/components/safety/incident/blame-fixation-banner.tsx` — hard block UI with override-with-justification gate.
- `src/components/safety/incident/human-factors-panel.tsx` — SHELL + IMO A.884(21) + Risk/Change framework.
- `src/schemas/safety/incident-phase5.ts`.

**PRD features delivered:** `FEAT-SAF-INC-016` (Phase 5 causal analysis + loop-back gate — gate completed here), `FEAT-SAF-INC-017` (M-SCAT picker), `FEAT-SAF-INC-018` (causal layering), `FEAT-SAF-INC-019` (multiple root causes), `FEAT-SAF-INC-020` (multi-tool analysis), `FEAT-SAF-INC-021` (investigation-depth triangle), `FEAT-SAF-INC-022` (People/Process/Plant), `FEAT-SAF-INC-023` (Safeguard-Failure Interrogatory), `FEAT-SAF-INC-024` (8 bias guards), `FEAT-SAF-INC-025` (blame-fixation hard block + override), `FEAT-SAF-INC-026` (Human Factors), `FEAT-SAF-RBAC-003` (blame-fixation override authority — DPA+).

**Tests to write:**
- Unit: `tests/safety/test_mscat_picker.py` — search "slip" returns subcode hits; 174 rows loaded; 10.15 Design/MOC Governance present (Round 21).
- Unit: `tests/safety/test_causal_layering.py` — Immediate/Intermediate/Root tagging persists; each cause may carry 1 layer.
- Unit: `tests/safety/test_multiple_root_causes.py` — no artificial cap (5, 10, 15 roots allowed).
- Unit: `tests/safety/test_bias_guards.py` — all 8 seeded; checklist gate on Phase 5→6 transition.
- Unit: `tests/safety/test_blame_fixation.py` — narrative containing "negligence"/"fault" raises block; override requires DPA role + justification text.
- Unit: `tests/safety/test_phase5_loopback_gate.py` — advance rejected without ≥1 root cause; rejected if any bias guard unacknowledged.
- E2E: `tests/frontend/safety/incident-phase-5.spec.ts` — picker interaction, layer tagging, bias-guard checklist, blame override dialog.

**Dependencies:** 1.6; seed data from 0.5 (master_mscat_taxonomy + master_safety_bias_guard).

**Decisions:** Round 21 R01 (causal layering), R03 (no cap), R09 (bias guards), R12 (8 bias guards), D-GAP-INC-12 (multi-tool), D-GAP-INC-13 (blame override authority), FEAT-SAF-INC-016..026, FEAT-SAF-RBAC-003.

---

### Step 1.8 — Phase 6: Recommendations (3-Tier + Colour Taxonomy) + ALARP Gate

**Description:** Phase 6 captures recommendations across 3 tiers (Corrective / Preventive / Lessons) with the colour taxonomy set in DESIGN_SYSTEM §5 (Round 21 R13). ALARP (As Low As Reasonably Practicable) cost-benefit gate (FEAT-SAF-INC-028 per Round 21 R02) — system-action recommendations above a cost-benefit threshold must include ALARP justification. Tolerable-Failure Filter (FEAT-SAF-INC-029 — GREEN band only can mark a cause "tolerable-failure" and close without recommendation; YELLOW/RED require ≥1-per-tier per V-INC-064). `vims_safety_recommendation` cardinality (Option A one-row-per-tier lock, per deferral #4) revisited Phase 8.

**Files to create:**
- `apps/safety/models/recommendation.py` — `Recommendation` (incident_id, tier {CORRECTIVE|PREVENTIVE|LESSONS}, text, target_date, assignee, alarp_justification, is_tolerable_failure). Table `vims_safety_recommendation`.
- `apps/safety/serializers/incident_phase6.py`.
- `apps/safety/views/incident_phase6.py`.
- `apps/safety/services/alarp_gate.py` — `require_alarp(recommendation) -> bool`; threshold configurable via env (`SAFETY_ALARP_COST_THRESHOLD`).
- `src/routes/safety/incident/[id]/phase-6.tsx`.
- `src/components/safety/incident/recommendation-editor.tsx` — 3-tier tabbed editor.
- `src/components/safety/incident/alarp-gate-modal.tsx`.
- `src/components/safety/incident/tolerable-failure-marker.tsx` (GREEN-only UI).
- `src/schemas/safety/incident-phase6.ts`.

**PRD features delivered:** `FEAT-SAF-INC-027` (Phase 6 recommendations), `FEAT-SAF-INC-028` (ALARP gate), `FEAT-SAF-INC-029` (tolerable-failure filter GREEN only).

**Tests to write:**
- Unit: `tests/safety/test_recommendation_tiers.py` — 3 tiers enforced; V-INC-064 (≥1-per-tier for YELLOW/RED).
- Unit: `tests/safety/test_alarp_gate.py` — system action above cost threshold requires ALARP text.
- Unit: `tests/safety/test_tolerable_failure.py` — GREEN-only; YELLOW/RED reject flag.
- Integration: `tests/safety/test_phase6_submit.py` — advance to Phase 7 requires valid recommendations per band.

**Dependencies:** 1.7.

**Decisions:** Round 21 R02 (ALARP), R13 (colour taxonomy), V-INC-064, deferral #4 (cardinality interim lock Option A), FEAT-SAF-INC-027..029.

---

### Step 1.9 — Phase 7: DPA Acceptance / Report Issued

**Description:** Phase 7 is DPA acceptance: DPA reviews the complete incident record + recommendations + PDF preview (generated via Phase 6 PDF pipeline but DPA-accepted here), and either **Accepts** (triggers PDF issuance + routing per band — FM for RED full-edit authority D-GAP-RBAC-07) or **Sends Back** (returns to prior phase with reason). Once accepted, the incident enters Phase 8 (Follow-up). RED band requires Master + DPA + FM signatures in sequence (Hybrid Digital Signature Model per FEAT-SAF-AUDIT-003, D-GAP-D1).

**Files to create:**
- `apps/safety/serializers/incident_phase7.py` — DPA acceptance fields; signature collection.
- `apps/safety/views/incident_phase7.py` — `IncidentPhase7AcceptView`, `IncidentPhase7SendBackView`.
- `apps/safety/services/pdf_preview_generator.py` — draft PDF for DPA review (uses pdf_renderer from Phase 6 of overall plan — Step 6.1).
- `apps/safety/services/signature_chain.py` — enforces Reporter → Master → HOD → DPA → FM sequence per band; hybrid digital (typed name + timestamp + device fingerprint) per D-GAP-D1.
- `src/routes/safety/incident/[id]/phase-7.tsx`.
- `src/components/safety/incident/dpa-acceptance-panel.tsx`.
- `src/components/safety/shared/signature-block.tsx` — `<SafetySignatureBlock>` (Reporter / Master / HOD / DPA / FM variants per DESIGN_SYSTEM §6).
- `src/schemas/safety/incident-phase7.ts`.

**PRD features delivered:** `FEAT-SAF-INC-030` (Phase 7 DPA Acceptance), `FEAT-SAF-RBAC-001` (closure authority — DPA accept for YELLOW/GREEN, FM co-accept for RED), `FEAT-SAF-RBAC-007` (FM full edit authority during RED closure), `FEAT-SAF-AUDIT-003` (hybrid digital signature model).

**Tests to write:**
- Unit: `tests/safety/test_signature_chain.py` — sequence enforcement; RED needs FM; YELLOW needs DPA; GREEN needs PIC.
- Integration: `tests/safety/test_phase7_accept.py` — acceptance → Phase 8 transition + PDF issued.
- Integration: `tests/safety/test_phase7_sendback.py` — rejection returns to PIC-selected prior phase with reason; field_history updated.
- Unit: `tests/safety/test_hybrid_digital_signature.py` — typed name + timestamp + device fingerprint stored.

**Dependencies:** 1.8; Step 6.1 (PDF renderer).

**Decisions:** D-GAP-M06 (RED band FM signature), D-GAP-D1 (hybrid signature), FEAT-SAF-INC-030, FEAT-SAF-RBAC-001/007, FEAT-SAF-AUDIT-003.

---

### Step 1.10 — Phase 8: Follow-up / Effectiveness Verification

**Description:** Phase 8 tracks recommendation execution and verifies effectiveness. Each recommendation gets a verification entry — action completed? Effective? Residual risk? If ineffective, the incident loops back to Phase 6 for new recommendation. Corrective Actions link to `vims_safety_corrective_action` (Step 1.11) which carries `purchase_req_id` hard FK to Purchase (D-GAP-M12, FEAT-SAF-XMOD-004). YELLOW-band deadline auto-pause on DPA leave (FEAT-SAF-INC-037) — when DPA marked `on_leave` in HR, YELLOW-band deadlines pause. PIC retains YELLOW ownership after vessel transfer (FEAT-SAF-INC-038).

**Files to create:**
- `apps/safety/models/verification.py` — `RecommendationVerification` (recommendation_id, is_effective, residual_risk, verified_at, verified_by, notes).
- `apps/safety/serializers/incident_phase8.py`.
- `apps/safety/views/incident_phase8.py`.
- `apps/safety/services/deadline_pauser.py` — monitors HR `users.on_leave` flag; pauses YELLOW deadlines.
- `apps/safety/services/pic_retention.py` — on crew rotation event (CMS), checks YELLOW incidents and keeps PIC assignment rather than reassigning to new-rank-holder.
- `src/routes/safety/incident/[id]/phase-8.tsx`.
- `src/components/safety/incident/verification-tracker.tsx`.
- `src/components/safety/incident/deadline-pause-banner.tsx`.
- `src/schemas/safety/incident-phase8.ts`.

**PRD features delivered:** `FEAT-SAF-INC-031` (Phase 8 Follow-up / Effectiveness Verification), `FEAT-SAF-INC-037` (YELLOW deadline auto-pause on DPA leave), `FEAT-SAF-INC-038` (PIC retains YELLOW ownership after vessel transfer).

**Tests to write:**
- Unit: `tests/safety/test_verification.py` — effective / ineffective / loop-back behaviour.
- Unit: `tests/safety/test_deadline_pauser.py` — DPA on_leave pauses; returning resumes.
- Unit: `tests/safety/test_pic_retention.py` — vessel transfer does not reassign PIC on YELLOW incidents.
- Integration: `tests/safety/test_phase8_loopback.py` — ineffective verification loops to Phase 6 for new recommendations.

**Dependencies:** 1.8, 1.9; 1.11 (corrective action linkage); CMS live-join (Step 5.3).

**Decisions:** FEAT-SAF-INC-031/037/038, D-GAP-B2 (timeline extension — reuse), D-GAP-A3/A4 (rank persists).

---

### Step 1.11 — Corrective Action (CA) with Purchase Req Hard FK

**Description:** `vims_safety_corrective_action` table holds Corrective Actions (from Phase 6 recommendations flagged as CA) with `purchase_req_id` hard FK to the Purchase module (D-GAP-M12). CA state machine: `OPEN → IN_PROGRESS → VERIFIED → CLOSED`. Closed CA cannot have its linked Purchase Req archived while the CA remains open (referential integrity). Aging buckets 0-15 / 15-30 / 30-45 / 45+ feed the CA Aging Pipeline dashboard panel (FEAT-SAF-DASH-006).

**Files to create:**
- `apps/safety/models/corrective_action.py` — `CorrectiveAction(incident_id, recommendation_id, purchase_req_id, state, assignee, target_date, closed_date, closure_notes)`. Table `vims_safety_corrective_action`.
- `apps/safety/serializers/corrective_action.py`.
- `apps/safety/views/corrective_action.py` — CRUD + state-transition endpoints.
- `apps/safety/services/ca_aging.py` — `aging_bucket(ca) -> str`.
- `src/routes/safety/incident/[id]/corrective-actions/index.tsx`.
- `src/components/safety/incident/ca-list.tsx`.
- `src/components/safety/incident/purchase-req-linker.tsx`.
- `src/schemas/safety/corrective-action.ts`.

**PRD features delivered:** `FEAT-SAF-XMOD-004` (Safety ↔ Purchase hard FK — defined here, enforced in Step 5.4), `FEAT-SAF-DASH-006` (CA Aging Pipeline — data source; dashboard UI in Step 7.6).

**Tests to write:**
- Unit: `tests/safety/test_corrective_action.py` — state transitions; FK to Purchase enforced.
- Integration: `tests/safety/test_ca_purchase_fk.py` — linked Purchase Req cannot be archived while CA open.
- Unit: `tests/safety/test_ca_aging.py` — buckets 0-15 / 15-30 / 30-45 / 45+.

**Dependencies:** 1.8; requires Purchase module tables present in `ksm_marine_live` (platform precondition).

**Decisions:** D-GAP-M12 (hard FK), FEAT-SAF-XMOD-004, FEAT-SAF-DASH-006.

---

### Step 1.12 — External Party Injury, Re-open, Draft-Mode-at-Any-Phase

**Description:** External-party (non-crew) injury capture (FEAT-SAF-INC-034) — add non-crew injury sub-record with name, party type, severity, no crew-FK requirement. Re-open closed incident, band-gated (FEAT-SAF-INC-035) — GREEN can be re-opened by PIC within 30 days; YELLOW by DPA within 90 days; RED by FM any time. Draft-mode at any phase (FEAT-SAF-INC-036) — Phase 1..6 can be saved as draft (phase stays same, state=`DRAFT`). Auto-save every 30s to IndexedDB (FEAT-SAF-AUDIT-006) on all phase forms using `workbox-background-sync` 7.1.0 + `idb` 8.0.0.

**Files to create:**
- `apps/safety/models/external_party_injury.py` — `ExternalPartyInjury(incident_id, party_name, party_type, severity, notes)`.
- `apps/safety/services/incident_reopen.py` — band-gated reopen authority check + audit write.
- `apps/safety/views/incident_external_party.py`, `apps/safety/views/incident_reopen.py`.
- `src/components/safety/incident/external-party-injury-form.tsx`.
- `src/components/safety/incident/reopen-incident-modal.tsx`.
- `src/hooks/safety/use-draft-autosave.ts` — 30s IndexedDB save.

**PRD features delivered:** `FEAT-SAF-INC-034` (external party), `FEAT-SAF-INC-035` (re-open band-gated), `FEAT-SAF-INC-036` (draft at any phase), `FEAT-SAF-AUDIT-006` (form auto-save every 30s).

**Tests to write:**
- Unit: `tests/safety/test_external_party_injury.py`.
- Unit: `tests/safety/test_incident_reopen_gate.py` — GREEN=30d PIC, YELLOW=90d DPA, RED=FM any time.
- Unit: `tests/frontend/safety/use-draft-autosave.test.ts` — 30s cadence; IndexedDB keyed by incident id + phase.
- Integration: `tests/safety/test_draft_any_phase.py` — Phase 3 draft save; reload picks up draft.

**Dependencies:** 1.3..1.10.

**Decisions:** D-GAP-F1 (30s auto-save), FEAT-SAF-INC-034/035/036, FEAT-SAF-AUDIT-006.

---

### Step 1.13 — MSC-MEPC.3 Position Auto-Fill (±12h Tolerance — Reporting Live Join)

**Description:** When an incident is created with an incident timestamp, auto-fill lat/long from the vessel's Daily Report (Noon Sea) within ±12 hours (D-GAP-M09). If no Daily Report in window (D-GAP-M10), accept manual lat/long and flag `awaiting_daily_report_match` — never blocks submit. Live join on `vims_noon_report` (same DB `ksm_marine_live`, no ETL).

**Files to create:**
- `apps/safety/services/mscmepc3_position_fetcher.py` — `fetch_position(vessel_id, timestamp) -> (lat, lon, source)`; `source` ∈ {AUTO_FROM_NOON, MANUAL, AWAITING_NOON}.
- `apps/safety/repositories/reporting_repo.py` — read-only repo for cross-module joins to `vims_noon_report` + `vims_departure_report` + `vims_arrival_report` (Reporting module tables).
- `src/components/safety/incident/msc-mepc3-position-picker.tsx` — auto-fill UI with "use auto / override manual" toggle.
- `src/hooks/safety/use-msc-mepc3-position.ts`.

**PRD features delivered:** `FEAT-SAF-INC-041` (MSC-MEPC.3 position auto-fill ±12h), `FEAT-SAF-XMOD-001` (Safety ↔ Reporting live join — defined here, verified Step 5.1).

**Tests to write:**
- Unit: `tests/safety/test_mscmepc3_fetch.py` — 12h tolerance; exact 12h boundary; 12h+1m rejected.
- Integration: `tests/safety/test_reporting_live_join.py` — joins `vims_noon_report` without ETL; same-DB assertion.
- Unit: `tests/safety/test_awaiting_noon_flag.py` — manual lat/lon with flag, never blocks submit.

**Dependencies:** 1.3; Reporting module `vims_noon_report` in `ksm_marine_live` (platform precondition).

**Decisions:** D-GAP-M09 (±12h), D-GAP-M10 (manual fallback), D-GAP-I2 (live join same DB), FEAT-SAF-INC-041, FEAT-SAF-XMOD-001.

---

### Step 1.14 — Closure + Audit Trail UI + Cross-Vessel Visibility

**Description:** Phase 9 (terminal) closure view — read-only incident detail, full audit trail panel (phase log + field history), DPA-only taxonomy maintenance gate (FEAT-SAF-RBAC-008 — only DPA may CRUD `master_mscat_taxonomy` / `master_safety_bias_guard`). Cross-Vessel Visibility (FEAT-SAF-RBAC-006): office users see across their `master_RoleByVessel` scope; ship-side users see own vessel only; DPA/FM see all. Incident Creation gate (FEAT-SAF-RBAC-002) — only top-4 officers (Master, CO, CE, 2E) hold `SAF_P_001` in seed profiles. Rank-Persists invariant (FEAT-SAF-RBAC-004) — no Acting-* concepts.

**Files to create:**
- `src/routes/safety/incident/[id]/closure.tsx` — read-only summary.
- `src/routes/safety/incident/[id]/audit.tsx` — phase log + field history combined view.
- `src/components/safety/incident/closure-summary.tsx`.
- `src/components/safety/shared/audit-trail-panel.tsx`.
- `apps/safety/views/incident_closure.py` — closure read-only endpoint.
- `apps/safety/authentication/permissions.py` (extend) — DPA-only guard for master_* taxonomy writes.

**PRD features delivered:** `FEAT-SAF-RBAC-002` (incident creation top-4 officers), `FEAT-SAF-RBAC-004` (rank-persists invariant), `FEAT-SAF-RBAC-006` (cross-vessel visibility), `FEAT-SAF-RBAC-008` (DPA-only taxonomy maintenance).

**Tests to write:**
- Integration: `tests/safety/test_incident_creation_gate.py` — only users with `SAF_P_001` + (Master|CO|CE|2E) can POST incident.
- Unit: `tests/safety/test_rank_persists.py` — no Acting-DPA, no Acting-CO constants anywhere in code.
- Integration: `tests/safety/test_cross_vessel_visibility.py` — office scoped by `master_RoleByVessel`; ship-side scoped by `Crew_Onboarding_History`; DPA/FM global.
- Unit: `tests/safety/test_dpa_taxonomy_guard.py` — non-DPA PATCH on `master_mscat_taxonomy` returns 403.

**Dependencies:** 1.1..1.13.

**Decisions:** D-GAP-A3/A4/A6 (rank persists), D-GAP-RBAC-02 (top-4 officers), FEAT-SAF-RBAC-002/004/006/008.

---

## Phase 2 — Near Miss Module (Anonymity-First)

Purpose: Build Near Miss reporting on top of the shared `vims_safety_incident` table (discriminated by `record_type = NEAR_MISS`) with **reporter anonymity as a first-class constraint** (D-GAP-J1). Any viewer role ∉ {DPA, FM, reporter-self} receives reporter-stripped output — enforced at the serializer layer (`AnonymityMixin` from Step 0.2). Low vs High priority triage drives fleet-alert issuance.

---

### Step 2.1 — Near Miss Creation + Reporter Anonymity Enforcement

**Description:** Near Miss is created by **any rank** (FEAT-SAF-NM-001 — contrast with Incident's top-4-officers gate). Creation uses the `vims_safety_incident` table with `record_type = NEAR_MISS`. Reporter identity is **always stored** in the DB (for DPA + FM visibility) but **always stripped** in serialization for other viewers. `AnonymityMixin` (Step 0.2) is applied to every serializer touching near-miss rows. Minimum-description length enforced at submit (V-NM-001 from VALIDATION_RULES §3).

**Files to create:**
- `apps/safety/serializers/near_miss.py` — `NearMissSerializer(AnonymityMixin, ...)`, `NearMissListSerializer(AnonymityMixin, ...)`, `NearMissCreateSerializer`.
- `apps/safety/views/near_miss.py` — `NearMissListCreateView` (POST gates on `SAF_P_001` + `SAF_F_002`; GET filtered by anonymity rules), `NearMissDetailView`.
- `apps/safety/urls.py` (append) — `near-miss/`, `near-miss/<uuid:id>/`.
- `apps/safety/services/nm_rate_limiter.py` — (continues in 2.5).
- `src/routes/safety/near-miss/index.tsx` — list page; AnonymityBadge shown on every row.
- `src/routes/safety/near-miss/create.tsx` — creation form.
- `src/components/safety/shared/anonymity-badge.tsx` — `<SafetyAnonymityBadge>` with eye-off icon per DESIGN_SYSTEM §6.
- `src/components/safety/near-miss/near-miss-form.tsx` — `<SafetyNearMissForm>`.
- `src/schemas/safety/near-miss.ts`.

**PRD features delivered:** `FEAT-SAF-NM-001` (Near Miss creation any rank), `FEAT-SAF-NM-002` (reporter identity masking for non-DPA/FM).

**Tests to write:**
- Unit: `tests/safety/test_near_miss_create_any_rank.py` — Wiper/Oiler can create; no rank gate on SAF_P_001 for NEAR_MISS record_type.
- Integration: `tests/safety/test_near_miss_anonymity_serializer.py` — Master/HOD receives reporter fields stripped; DPA/FM receive full; reporter-self receives full.
- Unit: `tests/safety/test_anonymity_badge.test.tsx` — badge visible on all near-miss rows for non-DPA/FM viewers.

**Dependencies:** 0.2 (`anonymity.py`), 1.1 (shared table), 1.2 (field history captures edits).

**Decisions:** D-GAP-J1 (anonymity boundary), SSOT §2B-Near-Miss, FEAT-SAF-NM-001/002.

---

### Step 2.2 — Low vs High Priority Triage

**Description:** After creation, near-miss enters triage queue. DPA (or delegate) triages as **Low** (log, no investigation) or **High** (full investigation path — supersedes to Incident via Step 1.6 `supersede_near_miss`). Priority field on `vims_safety_incident` (nullable for INCIDENT rows, required on NEAR_MISS before closure). Triage action writes to phase_log.

**Files to create:**
- `apps/safety/serializers/near_miss_triage.py`.
- `apps/safety/views/near_miss_triage.py` — `NearMissTriageView` (PATCH priority; DPA-only via `SAF_P_002`).
- `src/routes/safety/near-miss/[id]/triage.tsx`.
- `src/components/safety/near-miss/triage-modal.tsx`.

**PRD features delivered:** `FEAT-SAF-NM-003` (Low vs High priority triage).

**Tests to write:**
- Unit: `tests/safety/test_nm_triage.py` — DPA triages; non-DPA rejected; priority persists; phase_log written.
- Unit: `tests/safety/test_nm_triage_high_supersede.py` — High priority triage suggests supersede-to-incident; user confirms; new incident created via Step 1.6 path.

**Dependencies:** 2.1, 1.6.

**Decisions:** D-GAP-NM-02 (priority model), FEAT-SAF-NM-003.

---

### Step 2.3 — Lightweight Fact-Tree Analysis

**Description:** High-priority near-miss that is NOT superseded to incident gets a lightweight analysis workspace — fact tree only (no 9-phase workflow). Builds on Phase 4 fact-base model (Step 1.6) but without causal layering requirement. Keeps near-miss record_type intact.

**Files to create:**
- `apps/safety/serializers/near_miss_analysis.py`.
- `apps/safety/views/near_miss_analysis.py`.
- `src/routes/safety/near-miss/[id]/analysis.tsx`.
- `src/components/safety/near-miss/fact-tree-editor.tsx`.

**PRD features delivered:** `FEAT-SAF-NM-004` (Near Miss Lightweight Analysis — Fact Tree only).

**Tests to write:**
- Unit: `tests/safety/test_nm_fact_tree.py` — add/edit/delete facts; no causal layering required.

**Dependencies:** 2.2, 1.6.

**Decisions:** D-GAP-NM-03 (lightweight), FEAT-SAF-NM-004.

---

### Step 2.4 — Near Miss Rate-Limit + Minimum-Detail Enforcement

**Description:** Anti-spam guard: rate-limit near-miss submissions per user (configurable, default 5 per vessel per hour per user). Minimum-detail enforcement at server (V-NM-001 narrative ≥ 50 chars — confirmed VALIDATION_RULES §3). Both enforced at submit; warning-only on save-draft.

**Files to create:**
- `apps/safety/services/nm_rate_limiter.py` — sliding window per user+vessel; returns 429 with retry-after.
- `apps/safety/middleware/rate_limit_middleware.py` (if DRF throttle insufficient).

**PRD features delivered:** `FEAT-SAF-NM-005` (Near Miss rate-limit + minimum-detail).

**Tests to write:**
- Unit: `tests/safety/test_nm_rate_limit.py` — 6th submission in 1h rejected; 1h elapsed allows again.
- Unit: `tests/safety/test_nm_min_detail.py` — narrative < 50 chars 422.

**Dependencies:** 2.1.

**Decisions:** V-NM-001 (VALIDATION_RULES), FEAT-SAF-NM-005.

---

### Step 2.5 — Fleet Alert Issuance for High-Priority Near Miss

**Description:** High-priority near-miss requires a fleet alert issued within 1 week (FEAT-SAF-NM-006). Fleet alert is a notification row to all vessels in the company's scope via `master_notification`. Celery-beat monitors high-priority near-miss records with no fleet alert issued and is approaching 7-day mark; nudges DPA at day 5, day 6, and auto-escalates to FM at day 8.

**Files to create:**
- `apps/safety/services/fleet_alert_issuer.py` — `issue_fleet_alert(nm_id, alert_text, user)`.
- `apps/safety/tasks/fleet_alert_monitor.py` — celery-beat task; monitors and nudges.
- `apps/safety/views/fleet_alert.py` — `FleetAlertIssueView`.
- `src/routes/safety/near-miss/[id]/fleet-alert.tsx`.
- `src/components/safety/near-miss/fleet-alert-composer.tsx`.

**PRD features delivered:** `FEAT-SAF-NM-006` (Fleet Alert within 1 week for high-priority near miss).

**Tests to write:**
- Unit: `tests/safety/test_fleet_alert_issue.py` — rows written to `master_notification` for each vessel in company scope.
- Unit: `tests/safety/test_fleet_alert_nudge_schedule.py` — day 5/6/8 nudges fire on schedule.
- Integration: `tests/safety/test_fleet_alert_end_to_end.py` — high-priority NM → DPA issues alert → all vessels see notification.

**Dependencies:** 2.2, 1.4 (notification writer).

**Decisions:** D-GAP-NM-04 (1 week SLA), FEAT-SAF-NM-006.

---

### Step 2.6 — Near Miss Closure + Anonymity Boundary Verification

**Description:** Near miss closure (triaged Low → closed; triaged High with lightweight analysis complete → closed). Read-only summary respects AnonymityMixin. Self-report conflict guard (from Step 1.3, FEAT-SAF-INC-039 reused for near-miss). Verify anonymity boundary end-to-end across all exit points: list, detail, PDF (Step 6.3), search (Step 7.3), audit panel.

**Files to create:**
- `apps/safety/views/near_miss_closure.py`.
- `src/routes/safety/near-miss/[id]/closure.tsx`.
- `src/components/safety/near-miss/closure-summary.tsx`.

**PRD features delivered:** (consolidation step — no new FEAT IDs; hardens FEAT-SAF-NM-002 across all exits).

**Tests to write:**
- Integration: `tests/safety/test_nm_anonymity_all_exits.py` — sweep across list, detail, PDF render path (mocked), search, audit panel — reporter fields stripped in every exit for non-DPA/FM.

**Dependencies:** 2.1..2.5.

**Decisions:** D-GAP-J1 (full coverage verified).

---

## Phase 3 — SCM Regular + Ad-Hoc

Purpose: Safety Committee Meeting module — both Regular monthly and Ad-Hoc meetings can be hosted by Master or CO. Office Comment closes the meeting. Shared form shape (FEAT-SAF-SCM-003 — legacy `vw_GetSCM_Master` structure preserved); `meeting_type` differentiates the record. WRH attendance live join is warn-don't-block (D-GAP-M11). Overdue SOI is warning/visibility only in SCM. Aligns with KSM SSQE Manual Rev 01 Feb 2026 §9.

---

### Step 3.1 — `vims_safety_scm_meeting` CRUD + Regular SCM

**Description:** Core SCM table. `record_type` ∈ {REGULAR, AD_HOC}. Regular SCM must run monthly (cadence enforcement warn-only, not block). Master or CO hosts and can edit until Office Comment closes the record. 10-section form structure frozen to match legacy `vw_GetSCM_Master` view (FEAT-SAF-SCM-003).

**Files to create:**
- `apps/safety/models/scm.py` — `SCMMeeting` (vessel_id, record_type, meeting_date, scheduled_date, state, created_by, office_comment, office_comment_by, office_comment_at, ten_section_fields...). Table `vims_safety_scm_meeting`.
- `apps/safety/repositories/scm_repo.py`.
- `apps/safety/serializers/scm.py`.
- `apps/safety/views/scm.py` — `SCMListCreateView` (POST gates on `SAF_P_001` + `SAF_F_003`), `SCMDetailView`, `SCMCreateRegularView`.
- `apps/safety/urls.py` (append) — `scm/`, `scm/<uuid:id>/`, `scm/create-regular/`.
- `src/routes/safety/scm/index.tsx` — list page (Regular + Ad-Hoc tabs).
- `src/routes/safety/scm/create-regular.tsx`.
- `src/routes/safety/scm/[id]/index.tsx` — detail view.
- `src/components/safety/scm/scm-10-section-form.tsx` — 10-section form.
- `src/schemas/safety/scm.ts`.

**PRD features delivered:** `FEAT-SAF-SCM-001` (SCM Regular monthly cadence), `FEAT-SAF-SCM-003` (legacy structure), `FEAT-SAF-SCM-004` (creation/edit by Master/CO, Office Comment closure).

**Tests to write:**
- Unit: `tests/safety/test_scm_model.py`.
- Integration: `tests/safety/test_scm_regular_crud.py` — Master/CO can create; non-host roles with SAF_P_001 are rejected.
- Unit: `tests/safety/test_scm_10_sections.py` — legacy `vw_GetSCM_Master` field parity.
- Unit: `tests/safety/test_scm_cadence_warn.py` — > 30 days since last Regular SCM warns but does not block creation.

**Dependencies:** 0.6.

**Decisions:** D-GAP-SCM-01 (monthly cadence warn), SSOT §2C-SCM, FEAT-SAF-SCM-001/003/004.

---

### Step 3.2 — Ad-Hoc SCM (Master/CO Host-Triggered)

**Description:** Ad-Hoc SCM is hosted by Master or CO outside the monthly schedule. Same 10-section form as Regular; differs in `record_type = AD_HOC` and mandatory trigger reason. Typical trigger: RED-band incident, fleet alert follow-up, PSC finding.

**Files to create:**
- `apps/safety/views/scm_adhoc.py` — `SCMCreateAdHocView` (Master/CO host gate).
- `src/routes/safety/scm/create-adhoc.tsx`.
- `src/components/safety/scm/adhoc-trigger-reason.tsx` — mandatory reason text.

**PRD features delivered:** `FEAT-SAF-SCM-002` (SCM Ad-Hoc host-triggered).

**Tests to write:**
- Integration: `tests/safety/test_scm_adhoc_create.py` — Master/CO can create Ad-Hoc; non-host roles cannot.
- Unit: `tests/safety/test_scm_adhoc_reason_required.py`.

**Dependencies:** 3.1.

**Decisions:** FEAT-SAF-SCM-002.

---

### Step 3.3 — WRH Attendance Join (Warn-Don't-Block)

**Description:** `vims_safety_scm_attendance` joins live to `wrh_attendance` via user_id + meeting_date+window (24h + 7d snapshot on save per BACKEND deferral #7 interim lock option a). Missing WRH data warns — never blocks submit (D-GAP-M11). Timezone resolved via `wrh_ship_time_config` (D-GAP-M26). Per attendee: WRH fatigue status indicator (Green / Yellow / Red based on 24h + 7d rest hour thresholds).

**Files to create:**
- `apps/safety/models/scm_attendance.py` — `SCMAttendance(scm_id, user_id, rank_at_meeting, attended, wrh_24h_snapshot, wrh_7d_snapshot, wrh_flag)`.
- `apps/safety/repositories/wrh_repo.py` — live join to `wrh_attendance`, `wrh_daily_rest_hours`, `wrh_ship_time_config`.
- `apps/safety/serializers/scm_attendance.py`.
- `apps/safety/views/scm_attendance.py`.
- `apps/safety/services/wrh_snapshot_fetcher.py` — `fetch_24h_and_7d(user_id, meeting_dt)`; 10-second timeout; missing data → row flagged.
- `src/routes/safety/scm/[id]/attendance.tsx`.
- `src/components/safety/scm/attendance-table.tsx` — with WRH fatigue indicator.
- `src/components/safety/scm/wrh-unavailable-warning.tsx`.

**PRD features delivered:** `FEAT-SAF-SCM-005` (WRH attendance warn-don't-block), `FEAT-SAF-XMOD-002` (Safety ↔ WRH live join — defined here, verified Step 5.2).

**Tests to write:**
- Integration: `tests/safety/test_scm_wrh_join.py` — live SQL join against `wrh_attendance`; no ETL.
- Unit: `tests/safety/test_wrh_missing_warn.py` — WRH empty → row flagged, submit proceeds.
- Unit: `tests/safety/test_wrh_timezone.py` — timezone from `wrh_ship_time_config`; not UTC, not server time.

**Dependencies:** 3.1; WRH tables present in `ksm_marine_live` (platform precondition).

**Decisions:** D-GAP-M11 (warn-don't-block), D-GAP-M26 (timezone), deferral #7 interim lock, FEAT-SAF-SCM-005, FEAT-SAF-XMOD-002.

---

### Step 3.4 — Closed-Since-Last-SCM Summary Block

**Description:** Auto-populated summary block on each SCM showing items closed since the previous SCM on the same vessel: incidents closed, near-miss triaged, SOI findings closed, corrective actions completed. Read from `vims_safety_incident` (state=closed since last SCM date), `vims_safety_soi_finding` (state=closed), `vims_safety_corrective_action` (state=closed). Rendered in SCM form section 4.

**Files to create:**
- `apps/safety/services/closed_since_last_scm.py` — `fetch_closed_items(vessel_id, since_date) -> dict`.
- `apps/safety/views/scm_closed_since.py`.
- `src/components/safety/scm/closed-since-last-block.tsx`.

**PRD features delivered:** `FEAT-SAF-SCM-006` (Closed-since-last-SCM summary).

**Tests to write:**
- Unit: `tests/safety/test_closed_since_last.py` — correct cross-module aggregation.

**Dependencies:** 3.1, 1.10 (incident closure), 1.11 (CA closure), 4.9 (SOI finding closure).

**Decisions:** FEAT-SAF-SCM-006.

---

### Step 3.5 — SCM Agenda + Action-Item Tracking

**Description:** `vims_safety_scm_agenda` captures agenda items and Suggestions / Recommendations. Action items from SCM flow into `vims_safety_corrective_action` if flagged as such (reuse Step 1.11 model). Each item: owner, target date, status. Outcome logged at next SCM (Closed-Since-Last-SCM block picks up).

**Files to create:**
- `apps/safety/models/scm_agenda.py` — `SCMAgendaItem(scm_id, section, text, decision, owner, target_date, status)` where the legacy `decision` field is labelled Suggestions / Recommendations in the UI and PDF.
- `apps/safety/serializers/scm_agenda.py`.
- `apps/safety/views/scm_agenda.py`.
- `src/routes/safety/scm/[id]/agenda.tsx`.
- `src/components/safety/scm/agenda-editor.tsx`.

**PRD features delivered:** `FEAT-SAF-SCM-008` (agenda + action-item tracking).

**Tests to write:**
- Unit: `tests/safety/test_scm_agenda.py` — CRUD; action-item flag promotes to CA.

**Dependencies:** 3.1, 1.11.

**Decisions:** FEAT-SAF-SCM-008.

---

### Step 3.6 — SCM Overdue SOI Visibility (Warning Only)

**Description:** SCM can be **created, edited, exported to PDF, and closed by Office Comment** with overdue SOI. If any SOI on the vessel is past the 90-day ceiling (D-GAP-SOI-05, FEAT-SAF-SCM-007), SCM shows the overdue areas as warning/visibility only. It does not block the SCM workflow.

**Files to create:**
- `apps/safety/services/overdue_soi_blocker.py` — `check_overdue_soi(vessel_id) -> list[overdue_inspections]`.
- `apps/safety/services/overdue_soi_blocker.py` — `check_overdue_soi(vessel_id) -> list[overdue_inspections]`.
- SCM detail warning block / SOI link.

**PRD features delivered:** `FEAT-SAF-SCM-007` (SCM overdue SOI visibility).

**Tests to write:**
- Integration: SCM warning test — overdue SOI appears but does not block Office Comment closure.
- Unit: `tests/safety/test_overdue_soi_detector.py`.

**Dependencies:** 3.1, 4.4 (SOI 90-day ceiling + overdue detection).

**Decisions:** D-GAP-SOI-05 (90-day ceiling), FEAT-SAF-SCM-007.

---

### Step 3.7 — SCM Office Comment Closure

**Description:** Office Comment transitions SCM from `DRAFT` to `CLOSED`. DPA, FM, Shore HOD, and Marine Superintendent profile `407EF017-0F1C-EF11-A9F1-F348983BAE6B` can save Office Comment. Once Office Comment is saved, vessel-side meeting, attendance, and agenda edits are read-only. SCM does not capture digital signatures.

**Files to create:**
- `apps/safety/services/scm_state_machine.py`.
- `apps/safety/views/scm_office_comment.py`.
- SCM detail Office Comment block.

**PRD features delivered:** `FEAT-SAF-SCM-004` (Office Comment closure — completes this feature started in 3.1).

**Tests to write:**
- Integration: `tests/safety/test_scm_office_comment.py` — authorized office reviewer saves Office Comment → state=CLOSED.
- Unit: `tests/safety/test_scm_state_immutable.py` — closed SCM cannot be PATCHed by vessel users.

**Dependencies:** 3.6; 6.4 (SCM PDF).

**Decisions:** FEAT-SAF-SCM-004, D-RBAC-06.

---

### Step 3.8 — SOI → SCM Auto-Feed (Split Model)

**Description:** When a new SCM is created on a vessel, the form auto-populates a "New SOI findings since last SCM" block and a "Carried-Forward SOI findings" block (split model per D-GAP-SOI-14). Findings marked `CARRIED_FORWARD` in SOI state ENUM (deferral #5 interim lock option a) appear in the latter block. Outcome of each finding at SCM is captured and may close the finding (writes back to `vims_safety_soi_finding`).

**Files to create:**
- `apps/safety/services/soi_to_scm_feeder.py` — `fetch_new_and_carried(vessel_id, since_last_scm)`.
- `apps/safety/views/scm_soi_feed.py`.
- `src/components/safety/scm/soi-findings-auto-feed.tsx` — split-model display.

**PRD features delivered:** `FEAT-SAF-SOI-020` (SOI → SCM auto-feed split model).

**Tests to write:**
- Unit: `tests/safety/test_soi_scm_auto_feed.py` — new vs carried-forward split; outcome updates finding state.

**Dependencies:** 3.1, 4.9 (SOI finding closure).

**Decisions:** D-GAP-SOI-14 (split model), deferral #5 (Carried-Forward state interim), FEAT-SAF-SOI-020.

---

## Phase 4 — SOI (Safety Officer Inspection)

Purpose: Paper-first 13-area SOI workflow per D-GAP-E4, using the 329-item master checklist seeded in Step 0.5. Section 12 (Cross-cutting Safety & Culture) runs once per 3-month cycle (FEAT-SAF-SOI-014). NO scan upload — paper is authoritative, filed in ship SMS; only findings captured digitally. 90-day hard ceiling + 80-day amber warning. State pill label renamed to "SOI Compliance %" per D-GAP-DESIGN-01.

---

### Step 4.1 — `vims_safety_soi_inspection` + Area Map + Vessel Applicability

**Description:** Core SOI inspection event model. `vims_safety_soi_vessel_area_map` stores per-vessel per-area applicability flags + `last_inspected_at` timestamps (drives 90-day counter). `vims_safety_soi_applicability_log` audits `applicable=false` decisions (D-GAP-M19).

**Files to create:**
- `apps/safety/models/soi.py` — `SOIInspection(vessel_id, inspection_date, so_user_id, assistant_user_id, state, checklist_version_id, checklist_generated_at, unique_checklist_id, notes)`. Table `vims_safety_soi_inspection`.
- `apps/safety/models/soi_area_map.py` — `SOIVesselAreaMap(vessel_id, area_id, applicable, last_inspected_at, due_by_date)`. Table `vims_safety_soi_vessel_area_map`.
- `apps/safety/models/soi_applicability_log.py` — audit (D-GAP-M19). Table `vims_safety_soi_applicability_log`.
- `apps/safety/repositories/soi_repo.py`.
- `apps/safety/serializers/soi.py`.
- `apps/safety/urls.py` (append) — `soi/`, `soi/<uuid:id>/`, `soi/applicability/`.

**PRD features delivered:** `FEAT-SAF-SOI-001` (13-area taxonomy — model plumbed; seeded Step 0.5), `FEAT-SAF-SOI-002` (area-applicability toggle + audit log).

**Tests to write:**
- Unit: `tests/safety/test_soi_model.py`.
- Unit: `tests/safety/test_soi_area_map.py` — per-vessel applicability default True; toggle-false writes to log.
- Unit: `tests/safety/test_soi_applicability_log.py` — D-GAP-M19 audit entries persist.

**Dependencies:** 0.5, 0.6.

**Decisions:** D-SOI-16 (13 areas), D-GAP-M19 (applicability audit), FEAT-SAF-SOI-001/002.

---

### Step 4.2 — SOI Create + Pick Areas + SO/Assistant Assignment

**Description:** SO creates an SOI inspection, picks which areas to cover this event, and assigns an Assistant (cross-functional enforcement — FEAT-SAF-SOI-009). Up to 3 trainees (FEAT-SAF-SOI-010) via `vims_safety_soi_trainee`. SO/Assistant assignment uses live join to CMS (`Crew_Onboarding_History`) to verify rank at assignment time. Inherit CO-role on rotation (FEAT-SAF-SOI-024) — if CO rotates off vessel, their SOI ownership carries with the rank.

**Files to create:**
- `apps/safety/models/soi_trainee.py` — `SOITrainee(inspection_id, trainee_user_id, slot {1|2|3})`. Table `vims_safety_soi_trainee`.
- `apps/safety/services/soi_assistant_validator.py` — cross-functional enforcement: Assistant must be different department than SO.
- `apps/safety/repositories/cms_repo.py` — live join to `Crew_Onboarding_History` / `HRM501` for rank lookup.
- `apps/safety/views/soi_create.py`.
- `apps/safety/views/soi_pick_areas.py`.
- `apps/safety/views/soi_trainees.py`.
- `src/routes/safety/soi/create.tsx`.
- `src/routes/safety/soi/[id]/pick-areas.tsx`.
- `src/components/safety/soi/area-picker.tsx` — 13-area multi-select.
- `src/components/safety/soi/assistant-picker.tsx`.
- `src/components/safety/soi/trainee-assigner.tsx` — up to 3.
- `src/schemas/safety/soi.ts`.

**PRD features delivered:** `FEAT-SAF-SOI-004` (SO + Alternate assignment), `FEAT-SAF-SOI-009` (cross-functional assistant hard enforcement), `FEAT-SAF-SOI-010` (up to 3 trainees), `FEAT-SAF-SOI-024` (CO-role inheritance on rotation), `FEAT-SAF-XMOD-003` (Safety ↔ CMS live join — defined here).

**Tests to write:**
- Unit: `tests/safety/test_soi_create.py`.
- Unit: `tests/safety/test_soi_cross_functional.py` — same-department Assistant rejected.
- Unit: `tests/safety/test_soi_trainees_max3.py`.
- Integration: `tests/safety/test_cms_live_join.py` — rank read from `Crew_Onboarding_History`; no ETL.

**Dependencies:** 4.1; CMS tables (platform precondition).

**Decisions:** D-GAP-SOI-09 (cross-functional), D-GAP-A3/A4 (rank persists), D-GAP-I2 (live join), FEAT-SAF-SOI-004/009/010/024, FEAT-SAF-XMOD-003.

---

### Step 4.3 — Versioned Checklist Templates + `master_soi_checklist_version`

**Description:** DPA-maintained versioned checklist templates. Each SOI captures `checklist_version_id` at creation — historical inspections always render against their creation-time template (grandfather rule per FEAT-SAF-AUDIT-005). v1 seeded Step 0.5; subsequent versions created via DPA admin UI (Step 7.7).

**Files to create:**
- `apps/safety/models/soi_checklist_version.py` — (table already seeded Step 0.5; ORM wrapper here for read access). Table `master_soi_checklist_version`.
- `apps/safety/services/checklist_version_resolver.py` — resolves active version at create time; freezes into inspection row.

**PRD features delivered:** `FEAT-SAF-SOI-003` (versioned checklist templates).

**Tests to write:**
- Unit: `tests/safety/test_checklist_version_resolver.py` — active version at SOI create time is frozen.
- Unit: `tests/safety/test_historical_version_render.py` — old SOI renders against v1 even when v2 active.

**Dependencies:** 0.5, 4.1.

**Decisions:** FEAT-SAF-SOI-003, FEAT-SAF-AUDIT-005.

---

### Step 4.4 — 90-Day Hard Ceiling + 80-Day Amber + SOI Compliance %

**Description:** Per area per vessel, compute `due_by_date = last_inspected_at + 90 days`. At 80 days (or 10 days before due) surface an **amber** warning per D-GAP-SOI-05 / FEAT-SAF-SOI-005. At 90 days **hard ceiling** — overdue flag is shown in SCM as warning-only visibility (Step 3.6) and does not block meeting creation, PDF download, or Office Comment closure. Dashboard pill labelled **"SOI Compliance %"** per D-GAP-DESIGN-01 (NEVER "Inspection Compliance %"). Celery-beat nightly rollup.

**Files to create:**
- `apps/safety/services/soi_compliance_calculator.py` — `compliance_percent(vessel_id, at_date)`; 90/80 day logic.
- `apps/safety/tasks/soi_compliance_rollup.py` — nightly celery-beat.
- `src/components/safety/shared/soi-compliance-pill.tsx` — label literal "SOI Compliance %".

**PRD features delivered:** `FEAT-SAF-SOI-005` (90-day hard ceiling + 80-day amber), `FEAT-SAF-DASH-005` (SOI Compliance % renamed metric — data source; dashboard panel in Step 7.5).

**Tests to write:**
- Unit: `tests/safety/test_soi_compliance_calc.py` — 79d, 80d (amber), 89d, 90d (hard ceiling).
- Unit: `tests/safety/test_soi_compliance_label.py` — string is literally "SOI Compliance %".

**Dependencies:** 4.1, 4.3.

**Decisions:** D-GAP-SOI-05 (90/80-day), D-GAP-DESIGN-01 (renamed metric), FEAT-SAF-SOI-005, FEAT-SAF-DASH-005.

---

### Step 4.5 — Paper-First Checklist Generation (PDF or Excel) + Unique ID + Idempotent Download

**Description:** Core paper-first engine. On SO request, render the checklist as **PDF (reportlab)** or **Excel (openpyxl)** with a **unique checklist ID** (FEAT-SAF-SOI-008) printed as QR / Code128 / plain (resolved Phase 8 deferral #10; default `VITE_SAFETY_QR_FORMAT=qr`). Stamp `checklist_generated_at`. Idempotent re-download (FEAT-SAF-SOI-007, D-GAP-E3) — same unique ID re-served. **No scan upload endpoint** (D-GAP-E4). Paper is filed in ship SMS filing system; only findings captured digitally.

**Files to create:**
- `apps/safety/services/soi_checklist_generator.py` — renders PDF/Excel; embeds unique ID (QR via `qrcode` 7.4.2 or Code128 via `python-barcode` 0.15.1).
- `apps/safety/services/unique_id_allocator.py` — `allocate(inspection_id) -> str` (format: `{VesselCode}-SOI-{YYYY}-{NNN}-{random4}`).
- `apps/safety/views/soi_download.py` — `SOIDownloadView` (GET with format query param).
- `src/routes/safety/soi/[id]/download.tsx` — paper-first download page with 4-step guidance panel (download → field work on paper → file in SMS → register findings digitally).
- `src/components/safety/soi/download-panel.tsx`.
- `src/components/safety/soi/paper-first-guidance.tsx` — the 4-step explainer.

**PRD features delivered:** `FEAT-SAF-SOI-006` (paper-first PDF/Excel), `FEAT-SAF-SOI-007` (idempotent download + reprint), `FEAT-SAF-SOI-008` (unique checklist ID linkage).

**Tests to write:**
- Unit: `tests/safety/test_soi_checklist_pdf_gen.py` — reportlab PDF produced; QR embeds unique ID.
- Unit: `tests/safety/test_soi_checklist_excel_gen.py` — openpyxl workbook with QR image embedded.
- Unit: `tests/safety/test_unique_id_allocator.py` — format + uniqueness.
- Integration: `tests/safety/test_soi_idempotent_download.py` — 2 downloads = same unique ID.
- Unit: `tests/safety/test_no_scan_endpoint.py` — assert no URL matches `soi/<id>/scan/upload`.

**Dependencies:** 4.1, 4.2, 4.3.

**Decisions:** D-GAP-E1/E3/E4 (paper-first, idempotent, no scan), deferral #10 (QR vs Code128 vs plain — default QR; Phase 8 resolution), FEAT-SAF-SOI-006/007/008.

---

### Step 4.6 — Lost / Damaged Paper Recovery

**Description:** Lost/damaged paper may be re-downloaded (FEAT-SAF-SOI-013, D-GAP-E3). Loss event logged as `soi_notes` entry with timestamp + reason. Unique ID is re-used (not re-allocated) — paper→digital linkage preserved.

**Files to create:**
- `apps/safety/views/soi_reprint.py` — `SOIReprintView` with mandatory reason.
- `src/components/safety/soi/reprint-modal.tsx`.

**PRD features delivered:** `FEAT-SAF-SOI-013` (lost/damaged paper recovery).

**Tests to write:**
- Unit: `tests/safety/test_soi_reprint.py` — reason required; unique ID unchanged; log entry written.

**Dependencies:** 4.5.

**Decisions:** D-GAP-E3, FEAT-SAF-SOI-013.

---

### Step 4.7 — Finding Registration + Per-Area Stamping (Partial Submission)

**Description:** `vims_safety_soi_finding` holds findings registered **after** paper fieldwork. Per-item Yes/No/NA responses live on paper only (BACKEND §11.2); DB holds findings (deviations) only. Partial submission (FEAT-SAF-SOI-012) — SO may submit findings for a subset of areas; each area stamped separately (`last_inspected_at` updates per area). HIGH severity finding requires photo (FEAT-SAF-SOI-016, D-GAP-M24). Default assignee = SO (FEAT-SAF-SOI-021).

**Files to create:**
- `apps/safety/models/soi_finding.py` — `SOIFinding(inspection_id, area_id, area_item_id, severity {HIGH|MED|LOW}, title, description, assignee_user_id, state {OPEN|IN_PROGRESS|CLOSED|CARRIED_FORWARD|REOPENED}, photo_ids[], target_date)`. Table `vims_safety_soi_finding`.
- `apps/safety/models/soi_inspection_area.py` — `SOIInspectionArea(inspection_id, area_id, stamped_at, stamped_by)`. Table `vims_safety_soi_inspection_area`.
- `apps/safety/repositories/finding_repo.py`.
- `apps/safety/serializers/soi_finding.py`.
- `apps/safety/views/soi_finding.py`.
- `apps/safety/services/high_severity_photo_validator.py`.
- `src/routes/safety/soi/[id]/findings/index.tsx`.
- `src/routes/safety/soi/[id]/findings/create.tsx`.
- `src/components/safety/shared/soi-finding-row.tsx` — `<SafetySoiFindingRow>`.
- `src/components/safety/soi/high-severity-photo-upload.tsx` — Pillow 10.4.0-processed upload.
- `src/components/safety/soi/partial-submission-indicator.tsx`.
- `src/schemas/safety/soi-finding.ts`.

**PRD features delivered:** `FEAT-SAF-SOI-011` (finding registration — no per-item DB responses), `FEAT-SAF-SOI-012` (partial submission per-area stamping), `FEAT-SAF-SOI-016` (HIGH severity photo required), `FEAT-SAF-SOI-021` (default assignee = SO).

**Tests to write:**
- Unit: `tests/safety/test_soi_finding_crud.py`.
- Unit: `tests/safety/test_soi_no_per_item_in_db.py` — no `vims_safety_soi_item_response` table exists.
- Unit: `tests/safety/test_soi_partial_submission.py` — 3 of 5 areas stamped; 2 remain "Downloaded".
- Unit: `tests/safety/test_high_severity_photo.py` — HIGH without photo rejected.
- Unit: `tests/safety/test_default_assignee.py` — assignee defaults to SO when not specified.

**Dependencies:** 4.2, 4.5.

**Decisions:** D-GAP-E4 (no per-item DB), D-GAP-E2 (partial submission), D-GAP-M24 (HIGH photo), FEAT-SAF-SOI-011/012/016/021.

---

### Step 4.8 — HIGH Severity Nudge + Life-Threat Escalation

**Description:** When a HIGH severity finding is registered, system nudges SO with "Is this incident-worthy?" modal (FEAT-SAF-SOI-017). If SO confirms, creates Incident via Phase 1 intake flow auto-linked back. Life-threat escalation path (FEAT-SAF-SOI-018) — if severity field or description contains life-threat keywords, forces escalation via Incident or Near Miss before save can proceed.

**Files to create:**
- `apps/safety/services/high_severity_nudge.py`.
- `apps/safety/services/life_threat_detector.py` — keyword scanner.
- `src/components/safety/soi/incident-worthy-nudge-modal.tsx`.
- `src/components/safety/soi/life-threat-escalation-banner.tsx`.

**PRD features delivered:** `FEAT-SAF-SOI-017` (HIGH severity system nudge), `FEAT-SAF-SOI-018` (life-threat escalation via Incident/Near Miss).

**Tests to write:**
- Unit: `tests/safety/test_high_severity_nudge.py` — HIGH triggers modal; SO confirms → incident prefilled.
- Unit: `tests/safety/test_life_threat_detector.py` — keyword list triggers escalation block.

**Dependencies:** 4.7, 1.3 (incident intake).

**Decisions:** FEAT-SAF-SOI-017/018.

---

### Step 4.9 — Finding Closure (SO → Master) + Repeat-Finding Badge

**Description:** SO closes a finding (state → CLOSED or CARRIED_FORWARD); Master counter-signs on closure (D-GAP-M15). Repeat-finding detection (FEAT-SAF-SOI-019, D-GAP-M17) — same `area_item_id` on same vessel closed within last 180 days flags as "Repeat" (badge in UI + dashboard metric). V1 uses LIKE-based narrow search; Phase 8 FTS may upgrade matching.

**Files to create:**
- `apps/safety/services/finding_closure.py`.
- `apps/safety/services/repeat_finding_detector.py`.
- `apps/safety/views/finding_closure.py` — SO close + Master countersign endpoints.
- `src/routes/safety/soi/[id]/findings/[findId].tsx`.
- `src/components/safety/soi/repeat-finding-badge.tsx`.
- `src/components/safety/soi/master-countersign-block.tsx`.

**PRD features delivered:** `FEAT-SAF-SOI-015` (Finding Closure SO → Master), `FEAT-SAF-SOI-019` (repeat-finding badge + dashboard metric), `FEAT-SAF-SOI-023` (paper-signature capture — SO + Assistant mandatory — model here; digital signature per D-GAP-D1 hybrid).

**Tests to write:**
- Unit: `tests/safety/test_finding_closure.py` — SO close → Master countersign → CLOSED.
- Unit: `tests/safety/test_repeat_detection.py` — same area_item_id on same vessel within 180 days flags repeat.
- Unit: `tests/safety/test_signature_soi.py` — SO + Assistant digital signatures stored at save; Master at closure.

**Dependencies:** 4.7.

**Decisions:** D-GAP-M15 (Master countersign), D-GAP-M17 (repeat detection), D-GAP-D1 (hybrid signature), FEAT-SAF-SOI-015/019/023.

---

### Step 4.10 — Section 12 Cross-Cutting — Once Per 3-Month Cycle

**Description:** Section 12 (Cross-cutting Safety & Culture, 12 items, master_soi_area.id = 13) runs **once per 3-month cycle** (FEAT-SAF-SOI-014). Enforcement: cannot pick Section 12 if it has been inspected within the current 3-month cycle on this vessel. Cycle defined as calendar quarters (Jan-Mar / Apr-Jun / Jul-Sep / Oct-Dec) per D-GAP-SOI-18.

**Files to create:**
- `apps/safety/services/section12_cycle_enforcer.py` — `can_pick_section_12(vessel_id, at_date) -> (bool, next_allowed_date)`.

**PRD features delivered:** `FEAT-SAF-SOI-014` (Section 12 once per 3-month cycle).

**Tests to write:**
- Unit: `tests/safety/test_section12_cycle.py` — Feb 1 inspection → picking in Feb/Mar/April/May rejected until July 1 (next cycle); boundary at quarter edge.

**Dependencies:** 4.2.

**Decisions:** D-GAP-SOI-18 (3-month calendar cycle), FEAT-SAF-SOI-014.

---

### Step 4.11 — Area-Applicability Request/Approve Workflow

**Description:** Vessel requests to toggle an area `applicable=false` (e.g., no cranes on a tanker). Request routes to DPA for approval. Approved requests write to `vims_safety_soi_applicability_log` (D-GAP-M19 audit) and update `vims_safety_soi_vessel_area_map.applicable = false`. Re-enable path available if fleet ops change.

**Files to create:**
- `apps/safety/views/soi_applicability_request.py` — vessel-side request.
- `apps/safety/views/soi_applicability_approve.py` — DPA-side approve/reject.
- `src/routes/safety/soi/[id]/applicability/request.tsx`.
- `src/routes/safety/soi/[id]/applicability/approve.tsx`.

**PRD features delivered:** `FEAT-SAF-SOI-002` (area-applicability toggle + audit log — completes the workflow started in Step 4.1).

**Tests to write:**
- Integration: `tests/safety/test_applicability_workflow.py` — request → approve → map updated → log written.

**Dependencies:** 4.1.

**Decisions:** D-GAP-M19, FEAT-SAF-SOI-002.

---

### Step 4.12 — SOI Close Event + Crew Rotation Coverage % Metric

**Description:** SO closes the full SOI event after partial submissions / findings registered. Master final approval (D-GAP-M15). At close, update `vims_safety_soi_vessel_area_map.last_inspected_at` for each stamped area (resets 90-day counter per deferral #12 interim lock option a). Crew Rotation Coverage % metric (FEAT-SAF-SOI-022) — computes % of distinct crew who participated in ≥1 SOI in last 12 months (formula is deferral #11 — interim lock option a: strict `(distinct crew ≥1 inspection / total crew on vessel)`).

**Files to create:**
- `apps/safety/services/soi_close_service.py`.
- `apps/safety/services/crew_rotation_coverage.py` — interim strict formula.
- `apps/safety/views/soi_close.py`.
- `src/routes/safety/soi/[id]/close.tsx`.
- `src/components/safety/soi/close-confirm-panel.tsx`.

**PRD features delivered:** `FEAT-SAF-SOI-022` (crew rotation coverage % metric).

**Tests to write:**
- Unit: `tests/safety/test_soi_close.py` — close updates last_inspected_at per area; 90-day counter resets.
- Unit: `tests/safety/test_crew_rotation_coverage.py` — strict formula; deferred until Phase 8 Step 8.11.

**Dependencies:** 4.4, 4.7, 4.9, 4.11.

**Decisions:** D-GAP-M15 (Master close), deferrals #11 (formula interim) and #12 (reset timing interim), FEAT-SAF-SOI-022.

---

## Phase 5 — Cross-Module Integrations

Purpose: Harden the live-join contracts to Reporting / WRH / CMS / Purchase. **PMS is explicitly DECOUPLED (D-GAP-I1)** — no FK, no live join, no table reference; M-SCAT cause 12 "Inadequate Maintenance" is cross-referenced by the investigator manually. Every integration here is a **same-DB live SQL join** (D-GAP-I2) — no ETL, no sync, no message broker. Notification writes flow through `master_notification` (FEAT-SAF-XMOD-006).

---

### Step 5.1 — Reporting Live Join (MSC-MEPC.3 Position + Daily Report Missing)

**Description:** Harden the live join to `vims_noon_report` / `vims_departure_report` / `vims_arrival_report` for MSC-MEPC.3 position auto-fill (Step 1.13). Cover the missing-Daily-Report path (D-GAP-M10) — manual lat/long accepted with `awaiting_daily_report_match` flag; never blocks submit. Performance: query scoped by vessel + ±12h time range + indexed `vims_noon_report(vessel_id, date_time)` (BACKEND §7).

**Files to create:**
- `apps/safety/repositories/reporting_repo.py` (extend from Step 1.13) — hardened query planner; read-only Django queryset against Reporting models via same-DB join.
- `apps/safety/tasks/awaiting_daily_report_matcher.py` — celery-beat nightly task: retries match for any incident with `awaiting_daily_report_match=True`.

**PRD features delivered:** `FEAT-SAF-XMOD-001` (Safety ↔ Reporting MSC-MEPC.3 live join — hardened end-to-end here).

**Tests to write:**
- Integration: `tests/safety/test_reporting_live_join_hardened.py` — query performance < 200ms for vessel + ±12h.
- Unit: `tests/safety/test_awaiting_match_retry.py` — new Daily Report arriving later resolves the flag.

**Dependencies:** 1.13.

**Decisions:** D-GAP-M09 (±12h), D-GAP-M10 (manual fallback), D-GAP-I2 (live join), FEAT-SAF-XMOD-001.

---

### Step 5.2 — WRH Live Join (SCM Attendance + Fatigue Lookback)

**Description:** Harden WRH join used in Step 3.3 (SCM attendance) and Step 1.5 (Phase 3 fatigue lookback). Warn-don't-block (D-GAP-M11). Timezone via `wrh_ship_time_config` (D-GAP-M26). Configurable timeout via env (`SAFETY_WRH_QUERY_TIMEOUT_MS`) per deferral #7 interim lock option a (24h + 7d snapshot on save).

**Files to create:**
- `apps/safety/repositories/wrh_repo.py` (extend from Step 3.3) — hardened error handling; timeout → row flagged; missing data → warn-banner at UI.
- `apps/safety/services/wrh_snapshot_fetcher.py` (extend).

**PRD features delivered:** `FEAT-SAF-XMOD-002` (Safety ↔ WRH live join — hardened).

**Tests to write:**
- Integration: `tests/safety/test_wrh_timeout.py` — simulate WRH slow query → flag set, submit proceeds.
- Integration: `tests/safety/test_wrh_fatigue_7d.py` — 7-day fatigue lookback on Phase 3 returns aligned data.

**Dependencies:** 1.5, 3.3.

**Decisions:** D-GAP-M11, D-GAP-M26, deferral #7, FEAT-SAF-XMOD-002.

---

### Step 5.3 — CMS Live Join (SOI Assistant Lookup + Crew Assignment)

**Description:** Harden CMS join used in Step 4.2 (SO/Assistant rank lookup) and for incident crew assignment (Phase 3 evidence People tab). Uses live join to `Crew_Onboarding_History` + `HRM501` (same DB, D-GAP-I2). No staleness handling required.

**Files to create:**
- `apps/safety/repositories/cms_repo.py` (extend from Step 4.2) — hardened lookup by user_id / vessel_id / as-of-date.
- `apps/safety/services/crew_rank_resolver.py` — resolves rank at a given timestamp (handles crew rotation boundaries).

**PRD features delivered:** `FEAT-SAF-XMOD-003` (Safety ↔ CMS live join — hardened).

**Tests to write:**
- Integration: `tests/safety/test_cms_rank_at_date.py` — rank as-of correct across rotation boundary.

**Dependencies:** 1.5, 4.2.

**Decisions:** D-GAP-I2, FEAT-SAF-XMOD-003.

---

### Step 5.4 — Purchase Live Join + CA Hard FK Enforcement

**Description:** Enforce the hard FK `vims_safety_corrective_action.purchase_req_id` at the DB level. Referential integrity rule: Purchase Req cannot be archived while a linked open CA exists (D-GAP-M12). Live join for CA status display on the CA list.

**Files to create:**
- `apps/safety/repositories/purchase_repo.py` — live join to Purchase Req table.
- `apps/safety/services/purchase_fk_enforcer.py` — Purchase archive-request interceptor.
- Migration `0004_add_purchase_fk_constraint.py` — DB-level FK constraint on `vims_safety_corrective_action.purchase_req_id`.

**PRD features delivered:** `FEAT-SAF-XMOD-004` (Safety ↔ Purchase CA hard FK — hardened).

**Tests to write:**
- Integration: `tests/safety/test_purchase_fk.py` — linked Purchase Req archive blocked while CA open; unblocks on CA close.
- Integration: `tests/safety/test_ca_status_live.py` — CA list shows live Purchase Req status.

**Dependencies:** 1.11; Purchase tables (platform precondition).

**Decisions:** D-GAP-M12, FEAT-SAF-XMOD-004.

---

### Step 5.5 — PMS Decoupling Verification

**Description:** PMS integration is **NOT** built. Verification step: assert no code references PMS tables; no Python import of PMS ORM modules; no FK from Safety to PMS. M-SCAT cause 12 "Inadequate Maintenance" is a free-text cross-reference by investigator only. This step exists to explicitly document the non-integration.

**Files to create:**
- `tests/safety/test_pms_decoupled.py` — assertions only (no new app code).

**PRD features delivered:** `FEAT-SAF-XMOD-005` (Safety ↔ PMS decoupled — verified).

**Tests to write:**
- Unit: `tests/safety/test_pms_decoupled.py` — grep source tree for `pms_` table references (must be zero); grep imports for `apps.pms` (must be zero); assert no FK column name contains `pms_`.

**Dependencies:** None — verification only.

**Decisions:** D-GAP-I1 (PMS decoupled), FEAT-SAF-XMOD-005.

---

### Step 5.6 — Shared Notification Queue + Circular Module Write

**Description:** All Safety notifications write to `master_notification` (the platform queue — FEAT-SAF-XMOD-006). Recipients specified per band / per record type. Additionally, on incident closure, Safety writes a Fleet Circular draft into the VIMS Circular module table (lessons learned surfacing; per APP_FLOW §9.6). Best-effort Slack webhook (D-GAP-F2) fires alongside — in-app notification is authoritative.

**Files to create:**
- `apps/safety/services/notification_writer.py` (extend from Step 1.4).
- `apps/safety/services/circular_writer.py` — `draft_circular_from_incident(incident_id) -> circular_id`.
- `apps/safety/tasks/slack_dispatcher.py` — best-effort celery task.

**PRD features delivered:** `FEAT-SAF-XMOD-006` (shared notification queue via `master_notification` — hardened end-to-end; Circular integration completes APP_FLOW §9.6).

**Tests to write:**
- Integration: `tests/safety/test_notification_end_to_end.py` — RED incident accepted → rows in `master_notification` → platform notifier picks up.
- Unit: `tests/safety/test_circular_draft.py` — incident closure creates draft Circular entry auto-linked.
- Unit: `tests/safety/test_slack_best_effort.py` — Slack webhook failure does not break primary notification.

**Dependencies:** 1.9 (incident closure), 1.4 (notification writer).

**Decisions:** D-GAP-F2 (Slack best-effort), FEAT-SAF-XMOD-006.

---

## Phase 6 — PDF Generation

Purpose: Render the authoritative PDFs per D-PDF-01 / D-PDF-02 / D-PDF-03a / D-PDF-03b. All rendering via **ReportLab 4.2.0** (platform-installed; WeasyPrint banned per Reporting TECH_STACK §13). Post-processing (page numbering, headers/footers, ZIP assembly) via **PyPDF2 3.0.1**. All templates honour anonymity mask (D-GAP-J1 — reporter stripped for non-DPA/FM).

---

### Step 6.1 — 10-Section Incident PDF (Formal Report)

**Description:** Primary D-PDF-01 template. 10 sections: (1) cover, (2) executive summary (auto from Lessons), (3) intake, (4) sequence, (5) causes, (6) recommendations, (7) actions, (8) verification, (9) annexes (evidence / interview transcripts), (10) signatures. Signature block shows Master / DPA / FM per band (RED gets FM row per D-GAP-M06). Page numbering + confidentiality header/footer via PyPDF2 post-process. Anonymity enforced via serializer-level scrub before template interpolation (not applicable for Incident record_type; plumbed for reuse in 6.3).

**Files to create:**
- `apps/safety/services/pdf_renderer.py` — `render_incident_pdf(incident_id, viewer_user) -> bytes`.
- `apps/safety/services/pdf_templates/incident_10_section.py` — ReportLab template.
- `apps/safety/services/pdf_post_process.py` — PyPDF2 page numbering + confidentiality header/footer.
- `apps/safety/views/incident_pdf.py` — `IncidentPDFDownloadView`.
- `apps/safety/tasks/pdf_generation_task.py` — celery async for large reports.
- `src/routes/safety/incident/[id]/pdf/index.tsx`.
- `src/components/safety/incident/pdf-download-panel.tsx`.

**PRD features delivered:** `FEAT-SAF-PDF-001` (10-section incident PDF formal report).

**Tests to write:**
- Unit: `tests/safety/test_pdf_10_sections.py` — all 10 sections render with placeholder fixtures.
- Unit: `tests/safety/test_pdf_signature_block_by_band.py` — GREEN = Master+PIC; YELLOW = +DPA; RED = +FM.
- Integration: `tests/safety/test_pdf_end_to_end.py` — accept Phase 7 → PDF generated + stored under `/var/www/ksm_uploads/safety/{vessel_id}/exports/`.

**Dependencies:** 1.9 (Phase 7 accept triggers PDF); ReportLab 4.2.0 installed (platform precondition).

**Decisions:** D-PDF-01 (template), D-GAP-M06 (RED FM signature), FEAT-SAF-PDF-001.

---

### Step 6.2 — MSC-MEPC.3/Circ.4 Regulatory Export PDF

**Description:** Secondary regulatory PDF (D-DNV-12) for IMO flag-state reporting. Distinct template from D-PDF-01 — minimal fields per Circular 4 structure. Generated on demand by DPA; supports out-of-band flag-state notification (D-GAP-G1 — no deadline tracking in V1).

**Files to create:**
- `apps/safety/services/pdf_templates/msc_mepc3_circ4.py`.
- `apps/safety/views/msc_mepc3_export.py`.

**PRD features delivered:** `FEAT-SAF-PDF-002` (MSC-MEPC.3/Circ.4 regulatory export PDF).

**Tests to write:**
- Unit: `tests/safety/test_msc_mepc3_pdf.py` — field mapping matches IMO Circular 4 structure.

**Dependencies:** 6.1.

**Decisions:** D-DNV-12, D-GAP-G1 (no deadline tracking), FEAT-SAF-PDF-002.

---

### Step 6.3 — Near Miss Lightweight PDF

**Description:** D-PDF-03a lightweight 1–2 page NM template. "What happened" + "immediate action" + "suggestion"; no investigation / cause-tree sections. **Anonymity mask applied at serializer before PDF template interpolation** (D-GAP-J1) — non-DPA/FM viewers get a stripped reporter identity in the PDF output.

**Files to create:**
- `apps/safety/services/pdf_templates/near_miss_lightweight.py`.
- `apps/safety/views/near_miss_pdf.py`.
- `src/routes/safety/near-miss/[id]/pdf/index.tsx`.

**PRD features delivered:** `FEAT-SAF-PDF-003` (Near Miss lightweight PDF).

**Tests to write:**
- Unit: `tests/safety/test_near_miss_pdf_layout.py` — 1–2 pages; no cause-tree section.
- Integration: `tests/safety/test_near_miss_pdf_anonymity.py` — Master-viewer PDF has reporter stripped; DPA-viewer PDF has reporter visible.

**Dependencies:** 2.1, 6.1.

**Decisions:** D-PDF-03a, D-GAP-J1, FEAT-SAF-PDF-003.

---

### Step 6.4 — SCM PDF (10-Section Legacy Structure)

**Description:** D-PDF-03b legacy `vw_GetSCM_Master` 10-section template preserved in the active 9-section display. Available immediately after meeting creation. Includes Attendance + WRH snapshot, Closed-Since-Last, SOI summary without duplicate finding details, Section 7 findings/corrective measures, Office Comment, and plain Master Signature / Chief Officer Signature lines. SCM does not capture digital signatures.

**Files to create:**
- `apps/safety/services/pdf_templates/scm_10_section_legacy.py`.
- `apps/safety/views/scm_pdf.py`.
- `src/routes/safety/scm/[id]/pdf/index.tsx`.

**PRD features delivered:** `FEAT-SAF-PDF-004` (SCM PDF 10-section legacy).

**Tests to write:**
- Unit: `tests/safety/test_scm_pdf_legacy.py` — 10 sections match `vw_GetSCM_Master` column order.

**Dependencies:** 3.7.

**Decisions:** D-PDF-03b, FEAT-SAF-PDF-004.

---

### Step 6.5 — SOI Summary PDF (Post-Submission)

**Description:** SOI summary PDF generated after finding registration — lists stamped areas, findings (title + severity + assignee + state), trainees, signatures. Not the paper-first checklist (that's Step 4.5); this is the post-submission record for audit trail.

**Files to create:**
- `apps/safety/services/pdf_templates/soi_summary.py`.
- `apps/safety/views/soi_pdf.py`.
- `src/routes/safety/soi/[id]/pdf/index.tsx`.

**PRD features delivered:** `FEAT-SAF-PDF-005` (SOI summary PDF post-submission).

**Tests to write:**
- Unit: `tests/safety/test_soi_summary_pdf.py`.

**Dependencies:** 4.7, 4.9.

**Decisions:** FEAT-SAF-PDF-005.

---

### Step 6.6 — Auditor Leave-Behind ZIP Package

**Description:** D-PDF-02 auditor ZIP — bundles selected record-type PDFs within a date range plus their attachments in an `attachments/` subfolder. PyPDF2 assembly. No crew-name redaction (D-GAP-M37). Configurable at export (record types + date range). DPA-only via `SAF_P_004` + DPA role.

**Files to create:**
- `apps/safety/services/auditor_zip_builder.py`.
- `apps/safety/views/auditor_export.py` — DPA-only endpoint.
- `src/routes/safety/admin/auditor-export.tsx`.
- `src/components/safety/admin/auditor-export-configurator.tsx`.

**PRD features delivered:** `FEAT-SAF-PDF-006` (auditor leave-behind ZIP package).

**Tests to write:**
- Integration: `tests/safety/test_auditor_zip.py` — zip contains selected PDFs + attachments/ subfolder; non-DPA rejected.

**Dependencies:** 6.1, 6.3, 6.4, 6.5.

**Decisions:** D-PDF-02, D-GAP-M37 (no redaction), FEAT-SAF-PDF-006.

---

## Phase 7 — Dashboards, Reporting, Lessons-Learned

Purpose: Safety Intelligence Dashboard (composite score, Heinrich ratio, repeat-root-cause radar, Pareto screening, SOI Compliance %, CA aging pipeline) + cross-record search + archive search opt-in + taxonomy admin + case-study library seed + retention / attachment orphan cleanup + 3-year retention job.

---

### Step 7.1 — Safety Intelligence Dashboard — Composite Score + Core Rollup Pipeline

**Description:** Safety Intelligence Dashboard (SID) composite score (FEAT-SAF-DASH-001). Celery-beat 6-hourly rollup (per TECH_STACK §4.5 env `SAFETY_DASHBOARD_ROLLUP_CRON=0 */6 * * *`) aggregates open incidents, open near-miss, open findings, overdue CAs, SOI Compliance %. Recharts 3.7.0 visuals. Period persistence is deferral #9 interim — Zustand in-memory for V1; resolved Phase 8.

**Files to create:**
- `apps/safety/models/dashboard_rollup.py` — materialized rollup tables per vessel + fleet.
- `apps/safety/services/composite_score.py`.
- `apps/safety/tasks/dashboard_rollup.py` — 6-hourly celery-beat.
- `apps/safety/views/dashboard.py`.
- `src/routes/safety/dashboard/index.tsx`.
- `src/components/safety/dashboard/composite-score-card.tsx`.

**PRD features delivered:** `FEAT-SAF-DASH-001` (Safety Intelligence Dashboard composite score).

**Tests to write:**
- Unit: `tests/safety/test_composite_score.py`.
- Integration: `tests/safety/test_dashboard_rollup_cadence.py` — 6-hourly cadence; rollup tables populated.

**Dependencies:** 1.10, 1.11, 2.5, 4.12.

**Decisions:** FEAT-SAF-DASH-001, deferral #9 (period persistence interim).

---

### Step 7.2 — Heinrich Ratio Panel + Repeat-Root-Cause Radar + Pareto Screening

**Description:** Three analytical panels:
- Heinrich Ratio (FEAT-SAF-DASH-002) — ratio of Incidents : Near-Miss : Findings with confidence indicator (D-GAP-M27).
- Repeat-Root-Cause Radar (FEAT-SAF-DASH-003) — fleet + vessel views of top 10 repeat M-SCAT roots (D-GAP-H2).
- Pareto Screening Panel (FEAT-SAF-DASH-004) — 80/20 distribution of cause categories.

**Files to create:**
- `apps/safety/services/heinrich_ratio.py`.
- `apps/safety/services/repeat_root_radar.py`.
- `apps/safety/services/pareto_screener.py`.
- `src/components/safety/dashboard/heinrich-ratio-panel.tsx`.
- `src/components/safety/dashboard/repeat-root-radar.tsx` (Recharts).
- `src/components/safety/dashboard/pareto-panel.tsx` (Recharts).

**PRD features delivered:** `FEAT-SAF-DASH-002` (Heinrich ratio + confidence), `FEAT-SAF-DASH-003` (repeat root cause radar), `FEAT-SAF-DASH-004` (Pareto screening).

**Tests to write:**
- Unit: `tests/safety/test_heinrich_ratio.py`.
- Unit: `tests/safety/test_repeat_root_radar.py`.
- Unit: `tests/safety/test_pareto_screener.py`.

**Dependencies:** 7.1.

**Decisions:** D-GAP-M27, D-GAP-H2, FEAT-SAF-DASH-002/003/004.

---

### Step 7.3 — Cross-Record Search (LIKE-Based V1 Fallback)

**Description:** Cross-record search across Incident / Near Miss / SCM / SOI Finding. V1 uses **LIKE-based narrow search** (pending Phase 8 FTS engine resolution — BLOCKED §2.3 TECH_STACK). Respects anonymity mask (D-GAP-J1) — Near Miss rows return reporter-stripped unless DPA/FM.

**Files to create:**
- `apps/safety/services/cross_record_search.py` — LIKE queries against `narrative`, `title`, `description` columns.
- `apps/safety/views/search.py`.
- `src/routes/safety/search/index.tsx`.
- `src/components/safety/search/cross-record-results.tsx`.

**PRD features delivered:** `FEAT-SAF-DASH-007` (dashboard + cross-record search — data source; full FTS in Phase 8).

**Tests to write:**
- Unit: `tests/safety/test_cross_record_search_like.py`.
- Integration: `tests/safety/test_search_anonymity.py` — Near Miss hit returns reporter-stripped for non-DPA/FM.

**Dependencies:** 1.1, 2.1, 3.1, 4.7.

**Decisions:** BLOCKED §2.3 TECH_STACK / deferral #8, D-GAP-J1, FEAT-SAF-DASH-007.

---

### Step 7.4 — Archive Search Opt-In Toggle

**Description:** Default search scope excludes archived records (>3-year retention mark). Opt-in toggle (FEAT-SAF-DASH-008) pulls archived records until hard-delete by retention job. Applies to all search surfaces.

**Files to create:**
- `src/components/safety/search/archive-opt-in-toggle.tsx`.
- `apps/safety/services/cross_record_search.py` (extend with `include_archived` param).

**PRD features delivered:** `FEAT-SAF-DASH-008` (archive search opt-in toggle).

**Tests to write:**
- Unit: `tests/safety/test_archive_opt_in.py`.

**Dependencies:** 7.3.

**Decisions:** FEAT-SAF-DASH-008.

---

### Step 7.5 — SOI Compliance % Dashboard Panel

**Description:** Dashboard panel rendering SOI Compliance % per vessel + fleet average. Label literal **"SOI Compliance %"** (D-GAP-DESIGN-01; never "Inspection Compliance %"). Data source = Step 4.4 rollup.

**Files to create:**
- `src/components/safety/dashboard/soi-compliance-panel.tsx`.

**PRD features delivered:** `FEAT-SAF-DASH-005` (SOI Compliance % — completes the feature; calc in 4.4).

**Tests to write:**
- Unit: `tests/safety/test_soi_compliance_panel.test.tsx` — literal label "SOI Compliance %".

**Dependencies:** 4.4, 7.1.

**Decisions:** D-GAP-DESIGN-01, FEAT-SAF-DASH-005.

---

### Step 7.6 — CA Aging Pipeline Panel + Dashboard Export

**Description:** CA Aging Pipeline panel (FEAT-SAF-DASH-006 — 0-15 / 15-30 / 30-45 / 45+ buckets, data source Step 1.11) + Dashboard Export (PDF + Excel, DPA-only per FEAT-SAF-DASH-007). Export uses ReportLab + openpyxl.

**Files to create:**
- `src/components/safety/dashboard/ca-aging-pipeline.tsx`.
- `apps/safety/services/dashboard_export.py`.
- `apps/safety/views/dashboard_export.py` (DPA-only).

**PRD features delivered:** `FEAT-SAF-DASH-006` (CA Aging Pipeline — completes feature started Step 1.11), `FEAT-SAF-DASH-007` (dashboard export PDF+Excel DPA-only — completes feature).

**Tests to write:**
- Unit: `tests/safety/test_ca_aging_panel.test.tsx`.
- Integration: `tests/safety/test_dashboard_export_dpa_only.py` — non-DPA 403.

**Dependencies:** 1.11, 7.1.

**Decisions:** FEAT-SAF-DASH-006/007.

---

### Step 7.7 — Taxonomy Admin (DPA-Only) + Case-Study Library Seed

**Description:** DPA admin UI for `master_mscat_taxonomy`, `master_immediate_causes`, `master_loss_types`, `master_safety_bias_guard`, `master_soi_checklist_version`, `master_soi_area`, `master_soi_area_item`. Non-DPA blocked (FEAT-SAF-RBAC-008). Seed Case-Study Library (FEAT-SAF-DASH-009) — two historical cases (Navigator + Sinkfast) inserted for investigator training reference.

**Files to create:**
- `apps/safety/views/taxonomy_admin.py` — CRUD for 7 master tables, DPA-only.
- `apps/safety/models/case_study.py` — `SafetyCaseStudy` table.
- `apps/safety/fixtures/case_studies_seed.json` — Navigator + Sinkfast entries.
- `src/routes/safety/admin/index.tsx`.
- `src/routes/safety/admin/taxonomy.tsx`.
- `src/routes/safety/admin/case-studies.tsx`.

**PRD features delivered:** `FEAT-SAF-RBAC-008` (DPA-only taxonomy maintenance — completes feature), `FEAT-SAF-DASH-009` (seed case-study library Navigator + Sinkfast).

**Tests to write:**
- Integration: `tests/safety/test_taxonomy_admin_dpa.py` — non-DPA 403; DPA write succeeds.
- Unit: `tests/safety/test_case_study_seed.py` — 2 seeded cases present.

**Dependencies:** 0.5, 0.6.

**Decisions:** FEAT-SAF-RBAC-008, FEAT-SAF-DASH-009.

---

### Step 7.8 — 3-Year Retention Job + Attachment Orphan Cleanup

**Description:** Celery-beat daily retention job enforces 3-year hard-delete on Safety records (D-GAP-G2, FEAT-SAF-AUDIT-004). Attachments orphan cleanup (FEAT-SAF-AUDIT-007) — attachments without a parent record (from draft abandonment or hard-delete) removed from `/var/www/ksm_uploads/safety/`. Same-filename re-upload replaces in place (D-GAP-M02) with audit entry.

**Files to create:**
- `apps/safety/tasks/retention_job.py` — daily celery-beat, hard-delete records > 1095 days old (`SAFETY_RETENTION_DAYS`).
- `apps/safety/tasks/orphan_attachment_cleanup.py`.
- `apps/safety/services/attachment_replace_handler.py` — same-filename replace with audit.

**PRD features delivered:** `FEAT-SAF-AUDIT-004` (3-year retention + hard-delete attachments), `FEAT-SAF-AUDIT-007` (attachment orphan cleanup).

**Tests to write:**
- Integration: `tests/safety/test_retention_job.py` — records > 1095 days hard-deleted; audit entry written.
- Unit: `tests/safety/test_orphan_cleanup.py`.
- Unit: `tests/safety/test_same_filename_replace.py` — audit captured.

**Dependencies:** 1.1, 2.1, 3.1, 4.1.

**Decisions:** D-GAP-G2 (3-year hard-delete), D-GAP-M01/M02 (orphan cleanup + same-filename replace), FEAT-SAF-AUDIT-004/007.

---

## Phase 8 — Build-Time Deferral Resolutions

Purpose: Resolve the 12 build-time deferrals from BACKEND_STRUCTURE §8. Each deferral gets one numbered step here. These steps run when the DOMAIN owner resolves the option (Backend lead / Product / Design / Platform lead) — they are **ordered** per deferral number for traceability but may execute at their `Required by phase` deadline. Resolution writes a DECISION log entry in `progress.txt` and an ADR under `docs/adr/safety/` (not a code file — governance artifact).

---

### Step 8.1 — Deferral #1: `vims_safety_incident` ENUMs and Nullability

**Description:** Backend lead locks final ENUM CHECK constraints vs VARCHAR + lookup vs hybrid for state / phase / band / classifier columns (interim lock: hybrid). Migration tightens ENUM constraints where appropriate; schema_version bumped; historical records grandfather.

**Files to create:**
- `apps/safety/migrations/0005_tighten_incident_enums.py`.
- `docs/adr/safety/adr-001-incident-enums.md` (governance).

**PRD features delivered:** (resolution only — hardens plumbing in Step 1.1).

**Tests to write:**
- Unit: `tests/safety/test_incident_enum_tightening.py` — invalid enum rejected at DB level.
- Regression: `tests/safety/test_schema_version_grandfather_enum.py` — pre-0005 records still render.

**Dependencies:** 1.1.

**Decisions:** BACKEND §8 deferral #1, D-GAP-I9 (schema versioning).

---

### Step 8.2 — Deferral #2: `vims_safety_field_history` Column Shape

**Description:** Backend lead finalizes TEXT vs JSON vs typed + non-crypto rolling hash (crypto forbidden per D-GAP-D2). Interim lock Option A TEXT (Step 1.2). Resolution may migrate to JSON for typing preservation. No content hash chain (D-GAP-G2).

**Files to create:**
- `apps/safety/migrations/0006_field_history_shape.py`.
- `docs/adr/safety/adr-002-field-history-shape.md`.

**PRD features delivered:** (resolution — hardens `FEAT-SAF-AUDIT-002`).

**Tests to write:**
- Unit: `tests/safety/test_field_history_shape_final.py`.
- Unit: `tests/safety/test_no_crypto_hash.py` — no hashlib usage in field_history.

**Dependencies:** 1.2.

**Decisions:** BACKEND §8 deferral #2, D-GAP-D2/G2 (no crypto).

---

### Step 8.3 — Deferral #3: Soft-Archive Implementation

**Description:** Backend lead locks `archived_at NULL` sentinel (interim) vs `is_archived BIT + archived_at DATETIME2` vs partition strategy. Impacts retention job (Step 7.8) + search default filters.

**Files to create:**
- `apps/safety/migrations/0007_soft_archive_final.py`.
- `docs/adr/safety/adr-003-soft-archive.md`.

**PRD features delivered:** (resolution — hardens `FEAT-SAF-AUDIT-004`).

**Tests to write:**
- Unit: `tests/safety/test_soft_archive_final.py`.
- Integration: `tests/safety/test_retention_with_final_archive.py`.

**Dependencies:** 7.8.

**Decisions:** BACKEND §8 deferral #3.

---

### Step 8.4 — Deferral #4: `vims_safety_recommendation` Cardinality

**Description:** Backend lead locks one-row-per-tier (interim Option A) vs single-row-3-cols vs parent+children. Impacts V-INC-064 (≥1-per-tier enforcement on YELLOW/RED).

**Files to create:**
- `apps/safety/migrations/0008_recommendation_cardinality.py`.
- `docs/adr/safety/adr-004-recommendation-cardinality.md`.

**PRD features delivered:** (hardens `FEAT-SAF-INC-027`).

**Tests to write:**
- Unit: `tests/safety/test_recommendation_cardinality_final.py`.

**Dependencies:** 1.8.

**Decisions:** BACKEND §8 deferral #4, V-INC-064.

---

### Step 8.5 — Deferral #5: `vims_safety_soi_finding` State ENUM + Carried-Forward Semantics

**Description:** Backend lead finalizes 5-state ENUM with CARRIED_FORWARD (interim) vs 4-state ENUM + derived carried-forward. Impacts SCM auto-feed (Step 3.8, D-SOI-14).

**Files to create:**
- `apps/safety/migrations/0009_soi_finding_state_final.py`.
- `docs/adr/safety/adr-005-soi-finding-state.md`.

**PRD features delivered:** (hardens `FEAT-SAF-SOI-020`, FEAT-SAF-SOI-015).

**Tests to write:**
- Unit: `tests/safety/test_soi_finding_state_final.py`.
- Integration: `tests/safety/test_scm_auto_feed_final.py`.

**Dependencies:** 3.8, 4.9.

**Decisions:** BACKEND §8 deferral #5, D-SOI-14.

---

### Step 8.6 — Deferral #6: `vims_safety_incident_phase_log` Table Shape

**Description:** Backend lead finalizes typed phase_from/phase_to (interim) vs free-form JSON vs key-value pairs. Impacts phase-timeline UI query shape.

**Files to create:**
- `apps/safety/migrations/0010_phase_log_shape_final.py`.
- `docs/adr/safety/adr-006-phase-log-shape.md`.

**PRD features delivered:** (hardens `FEAT-SAF-AUDIT-001`).

**Tests to write:**
- Unit: `tests/safety/test_phase_log_shape_final.py`.

**Dependencies:** 1.2.

**Decisions:** BACKEND §8 deferral #6.

---

### Step 8.7 — Deferral #7: WRH Lookback Window / Query Timeout

**Description:** Backend + WRH lead finalizes 24h + 7d snapshot on save (interim Option A) vs streaming query at render vs env-configurable. Impacts SCM attendance save/display latency (D-GAP-M11 warn-don't-block).

**Files to create:**
- `apps/safety/services/wrh_snapshot_fetcher.py` (update with final policy).
- `docs/adr/safety/adr-007-wrh-lookback.md`.

**PRD features delivered:** (hardens `FEAT-SAF-SCM-005`, `FEAT-SAF-XMOD-002`).

**Tests to write:**
- Integration: `tests/safety/test_wrh_timeout_final.py`.

**Dependencies:** 3.3, 5.2.

**Decisions:** BACKEND §8 deferral #7, D-GAP-M11.

---

### Step 8.8 — Deferral #8: FTS Engine Selection (BLOCKED stub resolution)

**Description:** Platform lead chooses FTS engine — SQL Server native CONTAINS/FREETEXT vs Elasticsearch vs PG-FTS. This resolves BLOCKED §2.3 TECH_STACK. Upgrades LIKE-based search (Step 7.3) to full FTS. Impacts FEAT-SAF-DASH-007, FEAT-SAF-INC-009 (search by M-SCAT code), FEAT-SAF-SOI-019 (repeat-finding detection).

**Files to create:**
- `apps/safety/services/cross_record_search.py` (replace LIKE with FTS).
- `apps/safety/services/fts_engine.py` — new wrapper.
- If Elasticsearch chosen: `apps/safety/repositories/es_indexer.py` + celery task for re-index.
- If SQL Server FTS: `apps/safety/migrations/0011_enable_sql_server_fts.py`.
- `docs/adr/safety/adr-008-fts-engine.md`.

**PRD features delivered:** `FEAT-SAF-DASH-007` (full FTS), `FEAT-SAF-INC-009` (M-SCAT search final), `FEAT-SAF-SOI-019` (repeat-finding detection final).

**Tests to write:**
- Integration: `tests/safety/test_fts_engine.py` — full-text match across records.
- Regression: `tests/safety/test_search_after_fts.py` — search surface unchanged from user perspective.

**Dependencies:** 7.3, 1.5 (FEAT-SAF-INC-009 search surface exists).

**Decisions:** BLOCKED §2.3 TECH_STACK, BACKEND §8 deferral #8.

---

### Step 8.9 — Deferral #9: Dashboard Period Persistence per User Session

**Description:** Frontend lead chooses in-memory Zustand (interim) vs localStorage vs server-side `users.dashboard_period_pref`. Impacts SID UX.

**Files to create:**
- `src/stores/safety/dashboard-period-store.ts` (update persistence mode).
- If server-side: `apps/safety/models/user_dashboard_pref.py` + migration.
- `docs/adr/safety/adr-009-dashboard-period-persistence.md`.

**PRD features delivered:** (hardens `FEAT-SAF-DASH-001`).

**Tests to write:**
- Unit: `tests/frontend/safety/dashboard-period-persistence.test.ts`.

**Dependencies:** 7.1.

**Decisions:** BACKEND §8 deferral #9.

---

### Step 8.10 — Deferral #10: SOI Unique-ID Flag Format (BLOCKED stub resolution)

**Description:** Product + Design choose QR (interim default `VITE_SAFETY_QR_FORMAT=qr`) vs Code128 barcode vs plain alphanumeric only. Resolves BLOCKED §2.2 TECH_STACK. Library versions pinned in advance (qrcode 7.4.2, python-barcode 0.15.1) — one-line template change.

**Files to create:**
- `apps/safety/services/soi_checklist_generator.py` (update embed call per chosen format).
- `docs/adr/safety/adr-010-soi-unique-id-format.md`.

**PRD features delivered:** `FEAT-SAF-SOI-008` (unique checklist ID linkage — final format).

**Tests to write:**
- Unit: `tests/safety/test_soi_unique_id_format_final.py`.

**Dependencies:** 4.5.

**Decisions:** BLOCKED §2.2 TECH_STACK, BACKEND §8 deferral #10.

---

### Step 8.11 — Deferral #11: Trainee Rotation Coverage % Formula

**Description:** Product chooses strict `(distinct crew ≥1 inspection / total crew)` (interim) vs slot-weighted vs deck-engine-only scope. Impacts SID Crew Rotation panel (FEAT-SAF-SOI-022).

**Files to create:**
- `apps/safety/services/crew_rotation_coverage.py` (update formula).
- `docs/adr/safety/adr-011-rotation-coverage-formula.md`.

**PRD features delivered:** (hardens `FEAT-SAF-SOI-022`).

**Tests to write:**
- Unit: `tests/safety/test_crew_rotation_formula_final.py`.

**Dependencies:** 4.12.

**Decisions:** BACKEND §8 deferral #11.

---

### Step 8.12 — Deferral #12: 90-Day Counter Reset Timing

**Description:** Backend lead chooses reset at finding-registration (interim), Master approval, or overnight cron after Master approval. Impacts SOI Compliance % precision.

**Files to create:**
- `apps/safety/services/soi_compliance_calculator.py` (update reset-timing hook).
- `apps/safety/tasks/soi_cycle_counter_reset.py` (if cron chosen).
- `docs/adr/safety/adr-012-90-day-reset-timing.md`.

**PRD features delivered:** (hardens `FEAT-SAF-SOI-005`, `FEAT-SAF-DASH-005`).

**Tests to write:**
- Unit: `tests/safety/test_90_day_reset_final.py`.

**Dependencies:** 4.4, 4.12.

**Decisions:** BACKEND §8 deferral #12.

---

## Appendix A — FEAT-SAF-* → Step Coverage Matrix

Every PRD `FEAT-SAF-*` ID must appear in ≥1 step's "PRD features delivered". Compiled here for rubric compliance.

### Incident (41 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-INC-001 | 1.3 |
| FEAT-SAF-INC-002 | 1.4 |
| FEAT-SAF-INC-003 | 1.4 |
| FEAT-SAF-INC-004 | 1.4 |
| FEAT-SAF-INC-005 | 1.5 |
| FEAT-SAF-INC-006 | 1.5 |
| FEAT-SAF-INC-007 | 1.5 |
| FEAT-SAF-INC-008 | 1.5 |
| FEAT-SAF-INC-009 | 1.5, 8.8 |
| FEAT-SAF-INC-010 | 1.5 |
| FEAT-SAF-INC-011 | 1.5 |
| FEAT-SAF-INC-012 | 1.5 |
| FEAT-SAF-INC-013 | 1.5 |
| FEAT-SAF-INC-014 | 1.5 |
| FEAT-SAF-INC-015 | 1.6 |
| FEAT-SAF-INC-016 | 1.2, 1.7 |
| FEAT-SAF-INC-017 | 0.5, 1.7 |
| FEAT-SAF-INC-018 | 1.7 |
| FEAT-SAF-INC-019 | 1.7 |
| FEAT-SAF-INC-020 | 1.7 |
| FEAT-SAF-INC-021 | 1.7 |
| FEAT-SAF-INC-022 | 1.7 |
| FEAT-SAF-INC-023 | 1.7 |
| FEAT-SAF-INC-024 | 0.5, 1.7 |
| FEAT-SAF-INC-025 | 1.7 |
| FEAT-SAF-INC-026 | 1.7 |
| FEAT-SAF-INC-027 | 1.8, 8.4 |
| FEAT-SAF-INC-028 | 1.8 |
| FEAT-SAF-INC-029 | 1.8 |
| FEAT-SAF-INC-030 | 1.9 |
| FEAT-SAF-INC-031 | 1.10 |
| FEAT-SAF-INC-032 | 1.6 |
| FEAT-SAF-INC-033 | 1.6 |
| FEAT-SAF-INC-034 | 1.12 |
| FEAT-SAF-INC-035 | 1.12 |
| FEAT-SAF-INC-036 | 1.3, 1.12 |
| FEAT-SAF-INC-037 | 1.10 |
| FEAT-SAF-INC-038 | 1.10 |
| FEAT-SAF-INC-039 | 1.3 |
| FEAT-SAF-INC-040 | 1.1 |
| FEAT-SAF-INC-041 | 1.13 |

### Near Miss (6 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-NM-001 | 2.1 |
| FEAT-SAF-NM-002 | 0.2, 2.1, 2.6 |
| FEAT-SAF-NM-003 | 2.2 |
| FEAT-SAF-NM-004 | 2.3 |
| FEAT-SAF-NM-005 | 2.4 |
| FEAT-SAF-NM-006 | 2.5 |

### SCM (8 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-SCM-001 | 3.1 |
| FEAT-SAF-SCM-002 | 3.2 |
| FEAT-SAF-SCM-003 | 3.1 |
| FEAT-SAF-SCM-004 | 3.1, 3.7 |
| FEAT-SAF-SCM-005 | 3.3, 8.7 |
| FEAT-SAF-SCM-006 | 3.4 |
| FEAT-SAF-SCM-007 | 3.6 |
| FEAT-SAF-SCM-008 | 3.5 |

### SOI (24 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-SOI-001 | 0.5, 4.1 |
| FEAT-SAF-SOI-002 | 4.1, 4.11 |
| FEAT-SAF-SOI-003 | 0.5, 4.3 |
| FEAT-SAF-SOI-004 | 4.2 |
| FEAT-SAF-SOI-005 | 4.4, 8.12 |
| FEAT-SAF-SOI-006 | 4.5 |
| FEAT-SAF-SOI-007 | 4.5 |
| FEAT-SAF-SOI-008 | 4.5, 8.10 |
| FEAT-SAF-SOI-009 | 4.2 |
| FEAT-SAF-SOI-010 | 4.2 |
| FEAT-SAF-SOI-011 | 4.7 |
| FEAT-SAF-SOI-012 | 4.7 |
| FEAT-SAF-SOI-013 | 4.6 |
| FEAT-SAF-SOI-014 | 4.10 |
| FEAT-SAF-SOI-015 | 4.9, 8.5 |
| FEAT-SAF-SOI-016 | 4.7 |
| FEAT-SAF-SOI-017 | 4.8 |
| FEAT-SAF-SOI-018 | 4.8 |
| FEAT-SAF-SOI-019 | 4.9, 8.8 |
| FEAT-SAF-SOI-020 | 3.8, 8.5 |
| FEAT-SAF-SOI-021 | 4.7 |
| FEAT-SAF-SOI-022 | 4.12, 8.11 |
| FEAT-SAF-SOI-023 | 4.9 |
| FEAT-SAF-SOI-024 | 4.2 |

### Cross-Module (6 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-XMOD-001 | 1.13, 5.1 |
| FEAT-SAF-XMOD-002 | 3.3, 5.2, 8.7 |
| FEAT-SAF-XMOD-003 | 4.2, 5.3 |
| FEAT-SAF-XMOD-004 | 1.11, 5.4 |
| FEAT-SAF-XMOD-005 | 5.5 |
| FEAT-SAF-XMOD-006 | 1.4, 5.6 |

### PDF (6 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-PDF-001 | 6.1 |
| FEAT-SAF-PDF-002 | 6.2 |
| FEAT-SAF-PDF-003 | 6.3 |
| FEAT-SAF-PDF-004 | 6.4 |
| FEAT-SAF-PDF-005 | 6.5 |
| FEAT-SAF-PDF-006 | 6.6 |

### Audit (7 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-AUDIT-001 | 1.2, 8.6 |
| FEAT-SAF-AUDIT-002 | 1.2, 8.2 |
| FEAT-SAF-AUDIT-003 | 1.9, 3.7 |
| FEAT-SAF-AUDIT-004 | 7.8, 8.3 |
| FEAT-SAF-AUDIT-005 | 0.2, 1.1, 4.3 |
| FEAT-SAF-AUDIT-006 | 1.12 |
| FEAT-SAF-AUDIT-007 | 7.8 |

### Dashboard (9 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-DASH-001 | 7.1, 8.9 |
| FEAT-SAF-DASH-002 | 7.2 |
| FEAT-SAF-DASH-003 | 7.2 |
| FEAT-SAF-DASH-004 | 7.2 |
| FEAT-SAF-DASH-005 | 4.4, 7.5 |
| FEAT-SAF-DASH-006 | 1.11, 7.6 |
| FEAT-SAF-DASH-007 | 7.3, 7.6, 8.8 |
| FEAT-SAF-DASH-008 | 7.4 |
| FEAT-SAF-DASH-009 | 7.7 |

### RBAC (8 features)

| Feature ID | Step(s) |
|------------|---------|
| FEAT-SAF-RBAC-001 | 1.4, 1.9 |
| FEAT-SAF-RBAC-002 | 1.14 |
| FEAT-SAF-RBAC-003 | 1.7 |
| FEAT-SAF-RBAC-004 | 1.14 |
| FEAT-SAF-RBAC-005 | 0.2, 0.4, 0.6 |
| FEAT-SAF-RBAC-006 | 0.4, 1.14 |
| FEAT-SAF-RBAC-007 | 1.9 |
| FEAT-SAF-RBAC-008 | 0.5, 1.14, 7.7 |

**Total coverage: 115 / 115 FEAT-SAF-* IDs mapped (100%).**

---

## Appendix B — Build-Time Deferral Coverage

All 12 BACKEND_STRUCTURE §8 deferrals are owned by a Phase 8 step:

| Deferral # | Phase 8 Step |
|------------|--------------|
| 1 | 8.1 |
| 2 | 8.2 |
| 3 | 8.3 |
| 4 | 8.4 |
| 5 | 8.5 |
| 6 | 8.6 |
| 7 | 8.7 |
| 8 | 8.8 |
| 9 | 8.9 |
| 10 | 8.10 |
| 11 | 8.11 |
| 12 | 8.12 |

**Total: 12 / 12 deferrals resolved (100%).**

---

## Appendix C — Dependency Graph Summary (No Forward References)

Every step depends only on prior steps + platform preconditions. No forward references. Sample verification:

- Phase 0 depends on VIMS platform preconditions only.
- Phase 1 Steps 1.1..1.14 depend on Phase 0 + prior Phase 1 steps (no step depends on a higher-numbered step in the same phase).
- Phase 2 depends on Phase 0 + Phase 1 foundations (anonymity, base model, field history).
- Phase 3 depends on Phase 0 + Phase 1 (corrective actions for agenda promotion) + platform WRH tables.
- Phase 4 depends on Phase 0 + platform CMS tables.
- Phase 5 depends on Phases 1, 3, 4 (hardens their cross-module contracts) + platform Purchase.
- Phase 6 depends on Phases 1, 2, 3, 4 (records must exist before PDFs render).
- Phase 7 depends on Phases 1, 2, 3, 4, 6 (dashboards read cross-module rollups; exports reuse PDF pipeline).
- Phase 8 depends on the interim-locked steps it resolves (Phases 1–7).

No step in any phase depends on a higher phase. **Forward-reference rubric: PASS.**

---

## Appendix D — Rubric Self-Check

| Rubric Criterion | Status | Evidence |
|------------------|--------|----------|
| Every PRD FEAT-SAF-* ID mapped to ≥1 step | PASS | Appendix A: 115/115 |
| Every step has files + features + tests + dependencies | PASS | Standard block template applied uniformly |
| Build-time deferrals all 12 appear as Phase 8 steps | PASS | Appendix B: 12/12 |
| No forward references | PASS | Appendix C verification |
| Phase 0 includes Django app reg + URL include + seed-load | PASS | Steps 0.1–0.6 (6 sub-steps) |
| Phase 5 explicitly excludes PMS (D-GAP-I1) | PASS | Step 5.5 is a verification-only step asserting zero PMS imports / table refs |
| Phase 6 uses pinned ReportLab version from TECH_STACK | PASS | All PDF steps cite ReportLab 4.2.0 (TECH_STACK §1.4) |
| Zero bare `safety_*` prefixes | PASS | Every table named `vims_safety_*` or `master_*` throughout |
| DB connection `ksm_marine_live` referenced, not a new DB | PASS | Header + Step 0.1 + Step 5.x all cite `ksm_marine_live` |
| Migration order: Safety `0001_initial` depends on platform masters | PASS | Step 0.6 declares explicit migration dependency on `master_role` / `master_RoleByVessel` / `master_applied_rank` / `Crew_Onboarding_History` / `VesselData` / `msc_profiles` |
| Anonymity layer (D-GAP-J1) plumbed early (Phase 0) | PASS | Step 0.2 `anonymity.py` |
| SOI paper-first has NO scan upload | PASS | Step 4.5 explicit + Step 4.7 no per-item DB table + Step 4.5 test `tests/safety/test_no_scan_endpoint.py` |
| "SOI Compliance %" label (D-GAP-DESIGN-01), never "Inspection Compliance %" | PASS | Step 4.4 + Step 7.5 literal label assertions |

---

## Appendix E — BLOCKED Stubs Register

Two BLOCKED items carried forward from TECH_STACK §2.2 and §2.3 (Round 20 deferrals). Both resolve in Phase 8.

> **BLOCKED: FTS engine selection (Round 20 build-time deferral #8)**
> **Question:** Elasticsearch, SQL Server native CONTAINS/FREETEXT, PostgreSQL FTS, or platform default?
> **Gap:** No D-* decision locks this; Round 20 deferred to build-time.
> **Impact:** `FEAT-SAF-DASH-007` (incident search), `FEAT-SAF-INC-009` (search by M-SCAT code), `FEAT-SAF-SOI-019` (repeat-finding detection) render against V1 LIKE-based fallback until Step 8.8 resolves.

> **BLOCKED: SOI unique-ID flag format (Round 20 build-time deferral #10)**
> **Question:** QR code, Code128 barcode, or plain alphanumeric on the SOI paper checklist?
> **Gap:** D-SOI-10 revised + D-GAP-E1/E3/E4 mandate unique ID; visual encoding deferred.
> **Impact:** `FEAT-SAF-SOI-008` (unique checklist ID linkage) renders default QR until Step 8.10 resolves; library versions already pinned in TECH_STACK §2.2 so change is template-only.

---

## Document References

| Document | Reference |
|----------|-----------|
| `VIMS-Safety-Module/PRD.md` | 115 FEAT-SAF-* IDs mapped in Appendix A |
| `VIMS-Safety-Module/APP_FLOW.md` | Route paths used throughout Phase 1..7 steps |
| `VIMS-Safety-Module/TECH_STACK.md` | Version-locked dependencies cited per step |
| `VIMS-Safety-Module/DESIGN_SYSTEM.md` | Token names (risk-band palette, causal-layer hierarchy, anonymity badge, SOI Compliance % pill) cited per UI step |
| `VIMS-Safety-Module/FRONTEND_GUIDELINES.md` | Component prefix `Safety*`, 9-phase stepper pattern, paper-first download flow cited per frontend step |
| `VIMS-Safety-Module/BACKEND_STRUCTURE.md` | Table DDLs, API endpoints, live-join contracts, 12 build-time deferrals — authoritative for all data + API steps |
| `VIMS-Safety-Module/VALIDATION_RULES.md` | V-INC-* / V-NM-* / V-SCM-* / V-SOI-* test-spec references per step |
| `VIMS-Reporting-Module/IMPLEMENTATION_PLAN.md` | Phase-numbering pattern + Phase 0 Steps 0.1–0.4 template (cloned) |
| `VIMS-SAFETY-MODULE-SSOT.md` | 159 locked decisions — authority on every D-* cited |
| KSM SSQE Manual Rev 01 Feb 2026 §9, §11 | Regulatory authority for SCM and Incident procedures |
| ISM Code 2010 amendments §10 | Audit non-repudiation satisfied via `vims_safety_field_history` per D-GAP-D2 |
| IMO Casualty Investigation Code (Resolution MSC.255(84)) | SMC/MC/MI classifier per D-GAP-R08 |

---

## Amendment 1 - 2026-06-22

Incident Phase 1 injury capture now supports both crew and non-crew injuries under CR-002. The original Step 1.12 external-party injury scope is superseded for injury capture only: the physical table and compatibility endpoint remain, but the functional record now branches by `injured_person_type`.

Triggering discovery: post-build requirements expanded injury capture from non-crew-only to crew injuries with rank, age, vessel/activity details, investigation narrative, OCIMF reporting flags, and estimated cost fields.

Superseded steps or statements:

- Step 1.12 references the Phase 1 injury form as an external-party-only sub-form. That UI contract is superseded by the crew/non-crew injury section.
- FEAT-SAF-INC-034 references non-crew-only injury capture. That feature now means crew/non-crew injury capture while preserving the original non-crew fields.

Implementation record:

- Migration `0046_enhance_injury_record_for_crew` expands `vims_safety_external_party_injury`.
- `ExternalPartyInjurySerializer` and Phase 1 nested payload accept the expanded injury record.
- `SafetyExternalPartyInjuryForm` displays the crew/non-crew branch and loads crew rank options from the selected vessel's crew list.

## Amendment 2 - 2026-06-23

Incident Phase 1 crew injury dropdowns are now DB-backed under CR-004. The temporary CR-003 frontend-list approach is superseded for `Nature of Injury`, `Source of Injury`, and `Affected Areas of the Body`.

Triggering discovery: the injury dropdown values need to be maintained as master data with UUID primary keys instead of hardcoded frontend lists.

Superseded steps or statements:

- CR-003 stated no DB migration was required. That is superseded by migration `0047_injury_dropdown_options_master`.
- Any frontend-only injury dropdown source is superseded by `vims_safety_injury_dropdown_option`.

Implementation record:

- Migration `0047_injury_dropdown_options_master` creates and seeds `vims_safety_injury_dropdown_option`.
- `GET /api/safety/reference/injury-dropdown-options/` exposes active master options.
- `SafetyExternalPartyInjuryForm` loads injury dropdown options from the reference API and keeps `Other (specify)` behavior by storing typed text in the existing injury record fields.

## Amendment 3 - 2026-06-24

Incident evidence capture is simplified under CR-012. The original Step 1.5 five-source tabbed evidence UI is superseded for the current user-facing workflow: users now capture evidence in one Documents section, with each row containing Attachment, Title, and Description. Users can add as many document attachments as required.

Triggering discovery: post-shipment use found the People / Place / Equipment / Documents / Photos category screen too chaotic for evidence entry. The requested operating model is a repeatable document attachment list instead of category selection.

Superseded steps or statements:

- Step 1.5 references a required five-source tabbed user interface. That UI contract is superseded by the Documents-only evidence capture screen.
- Step 1.5 references the marine document inventory, cargo overlay, health/fatigue subsection, and category-specific evidence cards as primary user-facing controls. Those controls are no longer primary capture fields in the current UI.
- D-DNV-07, D-GAP-R05, D-GAP-R10, and D-GAP-R23 remain historical decisions, but their user-facing evidence-category requirements are superseded by SSOT decision `D-MAINT-CR012`.

Implementation record:

- `SafetyIncidentPhase3` now exposes only the Documents evidence section for the Phase 4 evidence workspace.
- Legacy category routes for People, Place, Equipment, and Photos redirect to `/phase-4/paper/`.
- Evidence uploads include `title` and `description` metadata; the backend stores them in both attachment metadata and the created `EvidenceItem`.
- The Phase 4 to Phase 5 evidence gate is documented as requiring at least one recorded evidence item, not completion of all five legacy categories.

## Amendment 4 - 2026-06-24

Incident evidence capture is made available earlier under CR-013. The original reached-phase edit gate for Phase 4 evidence documents is superseded: authorized users can open Phase 4 Documents and save attachments before Phase 4 is formally reached, including while Phase 2 or Phase 3 are still incomplete.

Triggering discovery: post-shipment testing showed the evidence screen returned a warning that investigation evidence could be edited only after Phase 4 was reached. This blocked legitimate early evidence capture when proof was available before root-cause or next-action work was complete.

Superseded behavior:
- Any statement that evidence document editing requires `current_phase >= 4` is superseded for the Documents evidence endpoints.
- Ordered phase submit/transition requirements are not superseded; users still submit Phase 2 and Phase 3 in sequence for workflow advancement.
- Office approval, closure, superseded-state, role, and vessel-scope locks are not superseded.

Implementation impact:
- The backend evidence workspace and attachment endpoints now enforce the normal edit lock only, not the Phase 4 reached check.
- The frontend keeps the Phase 4 Documents route accessible and no longer redirects users away when early evidence access is attempted.
- No schema or data migration is required.

## Amendment 5 - 2026-06-26

SCM meeting hosting is WRH-gated under CR-014. The original D-GAP-M11 warn-don't-block behavior is superseded for SCM Regular and Ad-Hoc meeting creation only: users may host an SCM meeting only when ship-time configuration exists for the vessel/date and all roster crew included in SCM readiness have available, compliant WRH data.

Triggering discovery: post-shipment use found that allowing users to host SCM while the same flow showed WRH warnings was operationally confusing. The requested operating model is "no WRH warning means hosting allowed; any WRH warning means hosting blocked."

Superseded behavior:
- D-GAP-M11 remains historical and still applies to already-created meeting detail/PDF/Office Comment warning visibility, but it no longer allows SCM meeting creation when WRH readiness is missing or non-compliant.
- Any APP_FLOW, BACKEND_STRUCTURE, VALIDATION_RULES, USER_GUIDE, or SSOT statement that says WRH data unavailable does not block SCM meeting creation is superseded by `D-MAINT-CR014`.
- No SCM database schema change is required; the gate uses existing WRH ship-time configuration and WRH snapshot lookup surfaces.

Implementation impact:
- SCM Regular and Ad-Hoc create endpoints run WRH readiness before creating the meeting record.
- The SCM create UI surfaces WRH readiness blockers near the host action and disables submit when readiness is not clear.
- Regression tests must cover blocked creation when ship-time or WRH crew data is missing and allowed creation when all WRH readiness checks are clear.

## Amendment 6 - 2026-06-29

Incident Phase 4 Evidence Check is removed from the current user-facing workflow under CR-015. The original Evidence Matrix / Pro-Con supporting tool remains historical and backend-compatible only; it is no longer a Phase 4 frontend route, optional card, or Phase 5/6 user-facing gate.

Triggering discovery: post-shipment use found the Safety evidence workflow still exposed too much investigation tooling after the Documents-only simplification. Users now need only the Documents attachment flow plus Witness Notes where needed.

Superseded behavior:
- D-DNV-07 remains historical, but its current user-facing Evidence Matrix surface is superseded by `D-MAINT-CR015`.
- D-DNV-11 #4 remains historical, but the current UI no longer asks users to satisfy a Con-row Evidence Matrix guard before continuing.
- Any APP_FLOW, PRD, VALIDATION_RULES, USER_GUIDE, FRONTEND_GUIDELINES, or SSOT statement that describes `/phase-4/evidence-matrix/` as a current Phase 4 route is superseded by `D-MAINT-CR015`.
- No backend table or endpoint deletion is required in this change; compatibility surfaces remain for older records and existing API clients.

Implementation impact:
- The Phase 4 frontend route tree no longer registers `/safety/incidents/:id/phase-4/evidence-matrix/`.
- The Phase 4 Documents workspace no longer renders the Evidence Check optional card and no longer calls the evidence-matrix endpoint.
- Regression tests must assert that Phase 4 Documents hides Evidence Check and does not load evidence-matrix data.

## Amendment 7 - 2026-06-29

Incident Phase 4 Witness Notes are simplified under CR-016. The original user-facing 4-phase interview form, formal/informal selector, and witness read-back/sign-off controls are superseded in the current Phase 4 UI. Users now record only Witness name, What the witness said, and Closing note.

Triggering discovery: post-shipment use found the Witness Notes form still exposed too much investigation protocol detail after the Evidence UI cleanup. The requested operating model is a short witness-note capture form that does not ask users to choose formal/informal mode or complete signature/read-back controls.

Superseded behavior:
- D-DNV-08 remains historical, but its current user-facing 4-phase interview form is superseded by `D-MAINT-CR016`.
- D-GAP-R19 and D-GAP-R20 remain backend/API compatibility rules for formal/informal interview payloads, but the current Phase 4 Witness Notes UI does not expose those controls.
- Any APP_FLOW, PRD, VALIDATION_RULES, USER_GUIDE, FRONTEND_GUIDELINES, or SSOT statement that describes formal/informal selection, read-back, witness signature, copy-to-witness, or 4-phase fields as current Phase 4 Witness Notes UI is superseded by `D-MAINT-CR016`.

Implementation impact:
- The Phase 4 Witness Notes form renders only Witness name, What the witness said, and Closing note.
- The frontend submits the simplified note as an informal compatibility payload with a system reason so existing backend validation and stored-data contracts remain intact.
- Regression tests must assert the three-field UI and compatibility payload.

## Amendment 8 - 2026-06-29

Incident Phase 1 First Checks are removed from the current user-facing workflow under CR-018. The original first-hour scene-protection checklist decision remains historical, but the current Incident Phase 1 UI, frontend schema, frontend payloads, incident serializers, and PDF output do not expose the checklist.

Triggering discovery: post-shipment use found the first-check checklist unnecessary and confusing for users. The requested operating model is a direct Phase 1 intake form that captures the incident details, reporter data, risk, office communication, weather/position, and injury details without a separate checklist.

Superseded behavior:
- `D-GAP-R07` remains historical, but its current user-facing checklist UI and submit gate are superseded by `D-MAINT-CR018`.
- Any APP_FLOW, PRD, VALIDATION_RULES, FRONTEND_GUIDELINES, BACKEND_STRUCTURE, USER_GUIDE, or SSOT statement that describes the first-check checklist as current UI, a required gate, an API serializer field, or a PDF field is superseded by `D-MAINT-CR018`.
- The existing `first_hour_checklist_done` database column remains legacy storage only; no data migration is required in this change.

Implementation impact:
- The Phase 1 form no longer renders the First Checks card, checklist toggle, checklist checkboxes, or hidden checklist value.
- The frontend Phase 1 schema and create/update payload builders no longer include `first_hour_checklist_done`.
- Incident serializers and incident PDF field summaries no longer expose or print the first-check field.
- Regression tests must assert the Phase 1 UI is absent, payloads omit the field, and current validation does not require the old gate.

## Amendment 9 - 2026-06-29

Incident Final Record history presentation is simplified under CR-019. The original terminal closure view described a full audit trail panel with phase log and field history. The current user-facing Final Record page now shows a clear final summary, simplified Phase History, approvals, reports, and reopen action. It does not show the Change History card or the History Rows metric.

Triggering discovery: post-shipment use found the Final Record page still surfaced technical audit concepts and raw enum values that confused users. The requested operating model is a readable final page where users understand the workflow path without seeing raw field-history rows or `NOT_APPLICABLE`.

Superseded behavior:
- Any statement that the routine Final Record UI exposes field/change history as a visible card is superseded by `D-MAINT-CR019`.
- Backend audit APIs and stored field-history rows are not removed. They remain available for authorized audit/export use.
- The Final Record risk summary formats `imo_classifier = NOT_APPLICABLE` as `No IMO class` in the UI.

Implementation impact:
- `SafetyIncidentPhase9` no longer renders the Change History card, Show/Hide Changes toggle, or History Rows card.
- Phase History renders as a numbered, plain-language timeline with transition status and actor/date context.
- Regression tests must assert the removed cards are absent and raw `NOT_APPLICABLE` is not shown.

## Amendment 10 - 2026-06-29

The Incident Type master data is simplified under CR-021. The original 11-row incident-type seed and picklist is superseded for current behavior: `IMO_MISSING_VESSEL` / Missing vessel is removed from seed data, removed from existing databases by migration, and defensively hidden from the Phase 1 dropdown.

Triggering discovery: post-shipment use found that Missing vessel should not be offered as an incident type in routine incident reporting.

Superseded behavior:
- D-DNV-04 remains historical, but the current Incident Type dropdown and master seed data contain 10 options, not 11.
- Any APP_FLOW, BACKEND_STRUCTURE, PRD, USER_GUIDE, or SSOT statement that says `master_safety_incident_type` has 11 current rows is superseded by `D-MAINT-CR021`.
- Existing incident records are not rewritten by this change.

Implementation impact:
- `master_safety_incident_type.json` no longer includes `IMO_MISSING_VESSEL`.
- Migration `0049_remove_missing_vessel_incident_type` deletes the existing master row.
- The frontend Incident Type picker defensively filters `IMO_MISSING_VESSEL` / Missing vessel if returned by an older API.
- Regression tests must assert the seed payload count is 10 and the Phase 1 dropdown does not show Missing vessel.

## Amendment 11 - 2026-06-30

Phase 1 reporting context fields are moved to the incident record under CR-024. Shore Assistance Required, Location of Vessel, Location on Board, Last Port, Departure Date, and Vessel Condition are now incident-level fields rendered in the main Phase 1 Incident Report section.

Triggering discovery: post-shipment UI review showed these fields were not visible in the main Incident Report screen. Repository discovery confirmed the fields existed only on `vims_safety_external_party_injury`, so they could not be saved for incidents without an injury row.

Superseded behavior:
- CR-023's temporary placement of these six fields inside a shared Injury Reporting subsection is superseded.
- The legacy injury-table copies remain backward-compatible for old injury records and PDF fallback, but current create/edit forms source these values from `vims_safety_incident`.
- No separate injury latitude/longitude columns are introduced; existing incident coordinates remain the shared coordinate source.

Implementation impact:
- Migration `0050_incident_reporting_context_fields` adds six nullable columns to `vims_safety_incident`.
- Phase 1 create/edit serializers and frontend payloads include the six incident-level fields.
- The Phase 1 UI renders the fields before Weather Condition and removes their duplicate injury-subsection rendering.
- Incident PDFs print the incident-level reporting context and fall back to legacy injury-row values only for older records.

## Amendment 12 - 2026-07-03

The Incident Type master data is replaced under CR-031. The current Incident Phase 1 dropdown and `master_safety_incident_type` seed data now expose 32 active options in the user-provided order. Earlier incident-type rows that are not part of the new list are retired for new selection while remaining available for historical lookup.

Triggering discovery: post-shipment classification review found the 10-option incident-type list too broad. Users need more specific options for bottom-touch events, allisions, foundering, flooding, fire/explosion split, cargo damage, equipment failures, crew injury, pollution, local-regulation breach, stowaway, security, cyber security, and Other.

Superseded behavior:
- `D-MAINT-CR021` remains historical for removing Missing vessel, but its 10-option current list is superseded by `D-MAINT-CR031`.
- D-DNV-04 remains historical background only; current master data is the 32-option CR-031 list.
- Any APP_FLOW, BACKEND_STRUCTURE, PRD, USER_GUIDE, or SSOT statement that says `master_safety_incident_type` has 10 or 11 current rows is superseded by `D-MAINT-CR031`.
- Existing incident records are not rewritten by this change.

Implementation impact:
- `master_safety_incident_type.json` now contains 32 active rows with `INC_*` type codes.
- Migration `0051_replace_incident_type_master_list` deactivates retired rows and upserts the 32 active rows for existing databases.
- The reference Incident Type endpoint orders rows by the CR-031 business sequence.
- The frontend Incident Type picker still filters retired `Missing vessel` if returned by an older API, and regression tests assert the new 32-option dropdown order.

## Amendment 13 - 2026-07-03

Incident Phase 1 field presentation is simplified under CR-032. The current form uses "Was office informed?" and "How was office informed?", hides WhatsApp from the communication-mode dropdown, places Latitude and Longitude together on one row, shifts Shore Assistance Required below the coordinate row, hides Last Port, and hides Weather ice-condition fields.

Triggering discovery: post-shipment UI review showed the office wording was less professional, WhatsApp should not be offered as a current office communication mode, Latitude and Longitude were split across rows, and Last Port plus ice-condition weather fields added unnecessary clutter.

Superseded behavior:
- `D-MAINT-CR024` remains valid for moving incident reporting context onto the incident record, but its current visible-field list is superseded for Last Port. Last Port remains a nullable compatibility column and historical/PDF fallback field, but it is no longer shown or sent by the current Phase 1 frontend.
- Any APP_FLOW, PRD, USER_GUIDE, VALIDATION_RULES, or SSOT statement that says Last Port is a current visible Phase 1 field is superseded by `D-MAINT-CR032`.
- The backend `office_notification_mode` storage may retain legacy `WHATSAPP` values, but the current Phase 1 dropdown only offers `ON_CALL` and `EMAIL`.
- Weather ice-condition columns remain compatibility storage, but the current Weather Condition UI no longer shows or sends them.

Implementation impact:
- `SafetyIncidentPhase1Form` updates the office labels, removes the WhatsApp option, removes Last Port and ice-condition controls, and nests Latitude/Longitude in a two-column row.
- Current Phase 1 save/submit payloads omit Last Port and weather ice-condition fields and normalize legacy `WHATSAPP` to null so users select a current mode when needed.
- Regression tests must assert the new labels/options, hidden fields, coordinate grouping, and payload omission.

## Amendment 14 - 2026-07-03

Incident Phase 1 field placement is adjusted under CR-034. The current form places Shore Assistance Required beside Report time while Latitude and Longitude remain together on their own row.

Triggering discovery: post-change UI review requested Shore Assistance Required beside Report time instead of below the coordinate row.

Supersedes:
- Amendment 13 and `D-MAINT-CR032` only for Shore Assistance Required placement.

Implementation impact:
- `SafetyIncidentPhase1Form` renders Report time and Shore Assistance Required in the same two-column row.
- Latitude and Longitude remain grouped in a separate two-column row.
- No backend, API, or database contract changes are required.

## Amendment 15 - 2026-07-03

Incident weather-condition migration compatibility is hardened under CR-035. Migration `0043_incident_weather_condition_fields` now separates Django migration state from database DDL so existing SQL Server databases can continue when `vims_safety_incident_weather_option` or incident weather columns already exist.

Triggering discovery: a deployment migration failed because SQL Server already contained `vims_safety_incident_weather_option` before Django had recorded `safety.0043` as applied.

Supersedes:
- The original assumption that `0043_incident_weather_condition_fields` always owns first creation of `vims_safety_incident_weather_option`.
- Any manual workaround requiring operators to drop the existing weather option table before rerunning migrations.

Implementation impact:
- The migration records the `IncidentWeatherOption` model and incident weather fields in Django state while running idempotent database operations.
- SQL Server DDL conditionally creates `vims_safety_incident_weather_option`, adds missing weather columns, and converts existing weather UUID-compatible columns to the current `CHAR(32)` storage shape when needed.
- Later weather seed migrations can run without requiring the pre-existing weather option table to be dropped.

## Amendment 16 - 2026-07-03

Incident RCA and Next Actions capture are simplified under CR-033. Current Incident RCA uses only Immediate Cause and Root Cause in the user-facing workflow, and Current Next Actions no longer shows or submits the "Why is this needed?" rationale field for corrective, preventive, or lessons entries.

Triggering discovery: post-shipment UI review found the Intermediate Cause layer and the why-needed action rationale field added clutter and confusion to the incident investigation flow.

Supersedes:
- Original Step 1.7 and D-GAP-R01 current-flow wording only where they require a current user-facing Immediate / Intermediate / Root RCA ladder.
- D-GAP-R09 current PDF wording only where it requires printing Immediate / Intermediate / Root labels.
- D-MAINT-CR028 only where it kept corrective/preventive rationale available in the current UI.

Implementation impact:
- Phase 2 RCA UI, counts, and phase-gate validation require at least one Immediate Cause and one Root Cause.
- The API rejects new `INTERMEDIATE` cause submissions with a user-facing validation message.
- The database enum and historical migrations remain compatible with legacy `INTERMEDIATE` rows; current UI/PDF display those rows under Root Cause instead of printing Intermediate Cause.
- Phase 3 Next Actions no longer renders or sends recommendation `rationale`; the nullable backend column remains for old records and compatibility.

## Amendment 17 - 2026-07-03

Incident Phase 4 Witness Statement capture is simplified under CR-036, and duplicate in-page incident phase headers are removed under CR-037. Current Phase 4 labels the supporting witness tool as Witness Statement, opens `/phase-4/interviews/` directly, loads the incident vessel crew list for witness-name selection, provides an Other typed-name option, captures What the witness said, Remark, and an optional signature image. Incident phase tabs remain the single phase number/name indicator; phase workspace content does not repeat separate Phase X/phase-title header cards.

Triggering discovery: post-shipment UI review found that the "Optional" witness card and "Closing note" wording were unclear, witness names should come from the vessel crew list where possible, and repeated phase headers duplicated the already-visible phase tabs.

Supersedes:
- `D-MAINT-CR016` only for the current user-facing label and field list: Witness Notes / Closing note becomes Witness Statement / Remark, and optional signature image upload is added.
- Existing APP_FLOW, PRD, USER_GUIDE, and SSOT wording that says current Phase 4 witness capture has only Witness name, What the witness said, and Closing note.
- Existing UI presentation assumptions that each phase workspace repeats its phase number/name inside the content area.

Implementation impact:
- Phase 4 Documents shows a collapsed Witness Statement support card that links directly to the witness statement page.
- The witness statement form fetches the incident vessel crew list, lets the user choose a crew member or Other, stores Other as typed text, reads image files as data URLs for `witness_signature`, and submits the existing informal witness-interview compatibility payload.
- Saved witness statements display Witness name, What the witness said, Remark, and signature status/image.
- Incident PDF evidence witness output uses the Witness Statement heading and Remark label.
- Phase workspace header cards that only repeated the phase number/name are removed; functional section headings and phase tabs remain.

## Amendment 18 - 2026-07-03

Incident action capture is split under CR-038. Current visible workflow separates Corrective Action, Preventive Action, and Lessons Learned into separate phase tabs, moves Evidence to visible Phase 6, Office Check to visible Phase 7, Check Actions to visible Phase 8, and removes the read-only Final Record from the visible workflow tabs.

Triggering discovery: post-shipment UI review found that combining corrective action, preventive action, and lessons learned inside one screen made the workflow harder to understand, and that Final Record is read-only so it should not appear as a normal editable phase.

Supersedes:
- The current-flow wording that treats Phase 3 as one combined Next Actions screen.
- The visible workflow assumption that Final Record is a normal phase tab.
- Current action-entry wording that requires a visible owner/checker card, Remaining risk field, or risk-confirmation checkbox.

Implementation impact:
- Phase tabs now show Phase 1 Report Incident, Phase 2 RCA, Phase 3 Corrective Action, Phase 4 Preventive Action, Phase 5 Lessons Learned, Phase 6 Add Evidence, Phase 7 Office Check, and Phase 8 Check Actions.
- Corrective Action uses the existing action storage contract but shows Description and Due date only; the owner/checker card is removed.
- Preventive Action hides Remaining risk and the risk-confirmation checkbox while maintaining backend compatibility values.
- Lessons Learned is captured on its own screen.
- Direct Final Record routes remain available for legacy/audit access but are hidden from the visible workflow.
- No database migration or backend endpoint change is required.

## Amendment 19 - 2026-07-03

Incident workflow is shortened under CR-042. The visible Phase 5 Lessons Learned screen is removed, Preventive Action now continues directly to Office Review, Office Check is renamed Office Review, and Office Review captures unrestricted Office Comments.

Triggering discovery: post-shipment workflow review found that the added Lessons Learned phase created unnecessary work, while the office decision screen lacked the important office comment field needed by reviewers.

Supersedes:
- Amendment 18 only where it made Lessons Learned a current visible phase and used the Office Check label.
- D-MAINT-CR038 only for the current visible Lessons Learned screen. Corrective Action and Preventive Action remain separate visible screens.
- Any APP_FLOW, PRD, USER_GUIDE, VALIDATION_RULES, BACKEND_STRUCTURE, or SSOT statement that says `/safety/incidents/:id/phase-5/` is a current Lessons Learned or analysis workspace is superseded by `D-MAINT-CR042`.

Implementation impact:
- Incident phase tabs now show Phase 1 Report Incident, Phase 2 RCA, Phase 3 Corrective Action, Phase 4 Preventive Action, Phase 6 Add Evidence, Phase 7 Office Review, and Phase 8 Check Actions.
- `/safety/incidents/:id/phase-3/lessons/` remains as a legacy route but redirects to Office Review.
- Preventive Action uses the existing continue control to route directly to Office Review.
- Migration `0052_incident_office_comment` adds nullable `vims_safety_incident.office_comment`.
- Phase 7 preflight and accept/approve-red payloads expose/save `office_comment`; the field has no word or character limit.
- Incident PDFs print Office Review comments and closure reason before Signature when present. Current PDF section selectors do not show Lessons Learned by default; legacy lesson export support remains compatibility-only.

## Amendment 20 - 2026-07-03

Incident visible phase numbering is made sequential under CR-043. After Lessons Learned was removed, the current visible workflow must no longer skip from Phase 4 to Phase 6.

Triggering discovery: post-shipment UI review found the phase tabs showed Phase 4 and then Phase 6, which looked broken to users even though the backend compatibility route paths still worked.

Supersedes:
- Amendment 19 only where it listed visible Add Evidence as Phase 6, Office Review as Phase 7, and Check Actions as Phase 8.
- Any APP_FLOW, PRD, USER_GUIDE, VALIDATION_RULES, BACKEND_STRUCTURE, or SSOT statement that uses the old visible Phase 6/7/8 labels for Add Evidence, Office Review, or Check Actions.

Implementation impact:
- Visible incident phase tabs now show Phase 1 Report Incident, Phase 2 RCA, Phase 3 Corrective Action, Phase 4 Preventive Action, Phase 5 Add Evidence, Phase 6 Office Review, and Phase 7 Check Actions.
- Shared frontend phase-label helpers map legacy backend `current_phase` values to the sequential visible labels.
- Backend `current_phase` values, route paths, API names, component names, and migrations remain unchanged for compatibility.
- No database migration or backend endpoint change is required.

## Amendment 21 - 2026-07-06

Incident Office Review authority is simplified under CR-044. Current Office Review decisions are not risk-band specific: PIC and DPA can accept, close, or send an incident back for rework for GREEN, YELLOW, and RED risk bands.

Triggering discovery: post-shipment permission review found users need PIC and DPA to perform the same Office Review decision actions regardless of risk band, instead of being blocked by the old GREEN/PIC, YELLOW/DPA, RED/FM closer mapping.

Supersedes:
- D-RBAC-01 and D-RBAC-05 only for current Incident Office Review accept/close/send-back authority.
- Amendment 19 and Amendment 20 only where their Office Review wording inherited the old risk-band closer model.
- Any APP_FLOW, PRD, USER_GUIDE, VALIDATION_RULES, BACKEND_STRUCTURE, or SSOT statement that says current Office Review acceptance, closure, or rework is limited by GREEN/PIC, YELLOW/DPA, or RED/FM.

Implementation impact:
- Phase 6 Office Review preflight advertises PIC and DPA as allowed decision roles for every risk band.
- Phase 6 accept and send-back endpoints allow PIC or DPA with the relevant process permission for every risk band.
- The legacy RED approval endpoint remains for route compatibility but no longer requires FM in the current implemented flow.
- Phase 7 Check Actions verification/close allows PIC or DPA for every risk band after action checks are complete or validly deferred.
- Incident PDF signature output prints the Office Review signature as PIC / DPA office signature rather than a risk-band-specific FM/PIC/DPA closer slot.
- No database migration is required.

## Amendment 22 - 2026-07-06

Incident visible Phase 7 is replaced under CR-047. The current user-facing Phase 7 is Loss Evaluation, not Check Actions. The compatibility route and backend phase number remain `/safety/incidents/:id/phase-6` and backend `current_phase` 8, but the screen now captures risk assessment, report-specific other details, cost evaluation, and estimated costs before closure.

Triggering discovery: post-shipment workflow review found the old Check Actions phase no longer matched the requested final review content. The final visible phase needs to evaluate operational loss and cost for Incident Report records and injury-specific loss/cost details for Injury Report records.

Supersedes:
- Amendment 20 only where it names visible Phase 7 as Check Actions.
- Amendment 21 only where it says Phase 7 Check Actions verification/close is the current closure step after Office Review.
- Any APP_FLOW, PRD, USER_GUIDE, VALIDATION_RULES, BACKEND_STRUCTURE, or SSOT statement that describes current visible Phase 7 as action checks/effectiveness verification.

Implementation impact:
- Visible incident phase tabs now show Phase 1 Report Incident, Phase 2 RCA, Phase 3 Corrective Action, Phase 4 Preventive Action, Phase 5 Add Evidence, Phase 6 Office Review, and Phase 7 Loss Evaluation.
- Migration `0053_incident_loss_evaluation` adds `vims_safety_incident_loss_evaluation`, one editable Loss Evaluation row per incident.
- Migration `0054_alter_injurydropdownoption_field_key` adds the `SAFE_WORKING_PRACTICE` dropdown category for future Injury Report safe-working-practice options.
- `GET /api/safety/incidents/{id}/phase-6/` returns the Loss Evaluation workspace; `PATCH /api/safety/incidents/{id}/phase-6/` saves it.
- `POST /api/safety/incidents/{id}/phase-6/close/` closes only after a Loss Evaluation row has been saved and a closure note is supplied.
- The old `/phase-6/verify/` effectiveness-verification endpoint remains registered as a compatibility endpoint but is not the current visible Phase 7 UI.
- The Incident PDF Estimated Cost selection prints Loss Evaluation blocks when a Loss Evaluation record exists.

## Amendment 23 - 2026-07-06

The Phase 7 Injury Report Loss Evaluation Safe Working Practice dropdown is seeded under CR-048. The field already existed from CR-047; this amendment supplies the requested Code of Safe Working Practices master data.

Triggering discovery: post-shipment field configuration review provided the actual dropdown list for `Code of Safe Working Practices to which the Incident relates`.

Supersedes:
- Amendment 22 only where it says `SAFE_WORKING_PRACTICE` options are future options.
- Any APP_FLOW, PRD, USER_GUIDE, VALIDATION_RULES, BACKEND_STRUCTURE, or SSOT statement that says the Safe Working Practice dropdown is unseeded or options are unavailable.

Implementation impact:
- Migration `0055_seed_safe_working_practice_options` seeds the user-provided Code of Safe Working Practices list into `vims_safety_injury_dropdown_option` with `field_key = SAFE_WORKING_PRACTICE`.
- Exact duplicate labels from the provided list are stored once to honor the master table unique key and keep the dropdown clean.
- Existing active `SAFE_WORKING_PRACTICE` choices outside the new list are deactivated so the dropdown reflects the approved list.

## Amendment 24 - 2026-07-06

Incident action, witness, and Office Review UI are simplified under CR-049. The current screens remove redundant technical wording while keeping the existing workflow and compatibility storage.

Triggering discovery: post-shipment UI review found that users were still seeing unnecessary preventive-action headings/fields, witness statement text fields, Office Review counters, approval-role explanations, and send-back target choices that confused the current ship/office workflow.

Supersedes:
- D-MAINT-CR036 only where it says current Witness Statement captures "What the witness said" and optional signature image.
- D-MAINT-CR038 only where it says current Preventive Action keeps compatibility theme/effort fields visible or lacks a preventive due date.
- D-MAINT-CR042 and D-MAINT-CR044 only where Office Review UI descriptions imply root/action counters, pre-approval summary cards, approval-role wording, or a user-selected send-back target are current visible controls.
- Any APP_FLOW, PRD, USER_GUIDE, VALIDATION_RULES, BACKEND_STRUCTURE, or SSOT statement that describes those superseded visible controls as current behavior.

Implementation impact:
- Preventive Action now shows Description, Due date, and How much will this reduce risk? only. It sends risk reduction and a linked due-date action; theme/effort/rationale remain nullable legacy compatibility storage.
- Witness Statement now shows Witness name, Other typed name when selected, Remark, and Upload witness statement. The old text statement field is not current UI.
- Office Review removes root/action counters, pre-approval summary cards, approval-role wording, and the send-back target picker. Office-side users see Accept / Close and Send for rework cards; ship-side users see Office Comments/lesson learnt only when a comment exists.
- Send for rework submits the comment with the fixed action-rework target phase through the existing endpoint. No database migration or new endpoint is required.

**Document Control:**
- Created: 2026-04-17
- Author: Wave 3 docsuite generation agent (Implementation Plan)
- Status: FROZEN — `progress.txt` is the execution-state tracker; this plan is the immutable blueprint.
- Next document in Wave 3: `USER_GUIDE.md`
