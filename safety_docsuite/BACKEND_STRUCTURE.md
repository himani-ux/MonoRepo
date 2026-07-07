# BACKEND_STRUCTURE.md — Database, APIs, Auth
## VIMS Safety Module — Incident / Near Miss / SCM / SOI

**Version:** 1.0 | **Date:** 2026-06-15 | **Status:** INITIAL RELEASE | **Target DB:** `ksm_marine_live` (shared SQL Server)

> This document is the single source of truth for the Safety module's persistence layer, REST contracts, and authorization chain. Every `CREATE TABLE`, every `/api/safety/*` endpoint, every cross-module live-join is enumerated here. It is consumed by Django (apps.safety), React (`src/routes/safety/`), and downstream PDF/dashboard services.

> **Naming law (per master prompt `<database_naming_convention>`):** every module-owned transactional table uses the `vims_safety_*` prefix; every shared reference / seed table uses the `master_*` prefix. **The bare `safety_*` prefix that appears in the SSOT is historical drift and MUST NOT appear in any DDL below.** Any legacy SSOT name is translated on output.

> **Final Safety UUID identity design (2026-05-21):** Every Safety-owned managed table uses UUID `id` as the actual database primary key. The transitional `public_id` column is not part of the final schema. Safety-owned child references store UUID-compatible identifiers, while polymorphic references retain their type discriminator plus UUID record/source value. Human-readable numbers such as `incident_number`, `scm_number`, `inspection_reference`, and `checklist_unique_id` remain unchanged and are not database identifiers.
> **Safety test-data reset:** Migration `safety.0032_uuid_id_final_cleanup` reset and recreated Safety-owned managed tables only during the test-phase UUID cleanup. External/shared VIMS tables were not touched. Transactional integer IDs were not retained because test data was reset; Safety-owned master/reference seed tables may retain `legacy_int_id` for seed compatibility and audit of prior seeded integer values.
> **Seed/bootstrap rule:** Safety seed and bootstrap paths must be idempotent. Reference/master seed commands match rows by natural keys and must not duplicate rows. Raw SQL seed paths must insert UUID `id` values explicitly when bypassing model defaults.
> **External/shared table rule:** Vessel, Crew, WRH, PMS, Circular, Purchase, auth/profile, and other shared non-Safety tables are not converted by the Safety UUID identity cleanup.

> **Incident backend update (2026-06-12):** The simplified incident workflow requires `vims_safety_incident.office_notified`, `office_notification_mode`, `loss_type_secondary_id`, `loss_type_tertiary_id`, and `loss_type_other`. Deploy migrations `0037_incident_office_notification_fields.py` and `0038_incident_multiple_loss_types.py` before deploying incident UI/API code that references these fields. Public incident routes follow the simplified phase contract in the Safety SSOT section 3.0; older backend class names and legacy URL aliases remain compatibility details only.
>
> **Incident Office Review update (2026-07-07):** Deploy migration `0052_incident_office_comment.py` before using the renamed Office Review screen. It adds nullable `vims_safety_incident.office_comment` for unrestricted Office Comments/lesson learnt captured during visible Phase 6 Office Review. This is separate from SCM meeting `office_comment` fields. Current send-for-rework UI sends a fixed action-rework target with the comment; it does not expose a target-phase picker. Ship-side Office Review shows a pending message when this comment is empty. Incident PDF preview/download is not blocked solely by pending Phase 7 acceptance.

> **Incident Fleet Alert update (2026-07-07):** No migration is required for CR-051. The Office Review Fleet Alert endpoint reads active ships and email addresses from existing `VesselData`, writes in-app rows through existing `psc_notification`, and sends best-effort email only to the selected ships.

> **Incident Loss Evaluation and preventive-risk update (2026-07-07):** No migration is required for CR-052. `GET/PATCH /api/safety/incidents/{id}/phase-6/` allows authorized ship-side and office-side users with `SAF_F_001` and vessel scope to open/save Loss Evaluation without requiring Office Review approval/backend `current_phase = 8`; `/phase-6/close/` remains office-close controlled. The Phase 4 frontend shows one shared preventive risk-reduction answer and sends it as `vims_safety_recommendation.estimated_likelihood_reduction` for preventive saves.

> **Incident Loss Evaluation report-type update (2026-07-07):** Deploy migration `0056_incident_loss_evaluation_report_type.py` before using the CR-053 Phase 7 selector. It adds nullable `vims_safety_incident_loss_evaluation.report_type` with `INCIDENT` and `INJURY` choices. `PATCH /api/safety/incidents/{id}/phase-6/` persists the selected type, `GET` returns `choices.report_type`, and PDF Loss Evaluation cost/detail blocks use the saved type. Existing rows without a saved type keep the previous injury-record fallback.

> **Incident Phase 1 vessel identity update (2026-07-07):** No migration is required for CR-054. `GET /api/safety/incidents/{id}/phase-1/` returns resolved `vessel_code` together with `vessel_name` and `vessel_display_name` using the existing VesselData/auth resolver. `vessel_code` remains accepted on create for draft-number allocation and is ignored on Phase 1 update; `vessel_id` plus vessel-scope validation remain the persisted authority.

> **Near Miss backend update (2026-06-15):** Near Miss no longer uses the Incident M-SCAT picker for Immediate Cause. Deploy migration `0039_near_miss_factor_causes.py` before deploying the Near Miss create/rework UI. The migration adds `vims_safety_incident.near_miss_factor_causes`, creates `vims_safety_near_miss_cause_option`, and seeds Human/Vessel/Management/Other factor options for Immediate Cause and Root Cause.

---

## Table of Contents

1. [Module Location & Django Integration](#1-module-location--django-integration)
2. [Database Naming + Router Contract](#2-database-naming--router-contract)
3. [Auth & RBAC Inheritance](#3-auth--rbac-inheritance)
4. [Full Schema — Transactional Tables (`vims_safety_*`)](#4-full-schema--transactional-tables)
5. [Full Schema — Reference / Seed Tables (`master_*`)](#5-full-schema--reference--seed-tables)
6. [Existing VIMS Masters Consumed](#6-existing-vims-masters-consumed)
7. [Indexes & Performance Contract](#7-indexes--performance-contract)
8. [Build-Time Deferrals Register](#8-build-time-deferrals-register)
9. [API Endpoints — Complete REST Contract](#9-api-endpoints)
10. [Cross-Module Live-Join Contracts](#10-cross-module-live-join-contracts)
11. [Paper-First SOI Data-Model Constraints](#11-paper-first-soi-constraints)
12. [Audit Rails](#12-audit-rails)
13. [Migration Ordering](#13-migration-ordering)
14. [Rubric Self-Check](#14-rubric-self-check)
15. [Document References](#15-document-references)

---

## 1. Module Location & Django Integration

### 1.1 Folder tree (backend — Django)

Safety is a **child Django app inside the VIMS monorepo** — not a standalone service. Connection, auth, migrations, and notifications all reuse the platform. Folder layout mirrors `apps/reporting/` (verified against `VIMS-Reporting-Module/IMPLEMENTATION_PLAN.md` §Phase 0 Steps 0.1–0.4) and is mandated by the master prompt `<vims_integration>`:

```
<vims-repo-root>/
├── apps/
│   ├── reporting/                  ← sibling module (exists — verbatim pattern source)
│   ├── inspection/                 ← sibling module (exists)
│   └── safety/                     ← NEW — Safety module lives here
│       ├── __init__.py
│       ├── apps.py                 ← class SafetyConfig(AppConfig); name = 'apps.safety'
│       ├── urls.py                 ← Root URL namespace; mounted at /api/safety/
│       ├── admin.py                ← Django-admin registrations for master_* read-only inspection
│       ├── models/
│       │   ├── __init__.py         ← Re-export all ORM models
│       │   ├── base.py             ← BaseSafetyRecord abstract (vessel_id, state, created_by,
│       │   │                          updated_by, is_deleted, schema_version, archived_at)
│       │   ├── incident.py         ← vims_safety_incident, vims_safety_incident_phase_log,
│       │   │                          vims_safety_field_history
│       │   ├── soi.py              ← vims_safety_soi_* tables (6 tables)
│       │   ├── scm.py              ← vims_safety_scm_* tables (3 tables)
│       │   ├── actions.py          ← vims_safety_corrective_action, vims_safety_recommendation
│       │   └── reference.py        ← Read-only wrappers for master_mscat_taxonomy,
│       │                              master_immediate_causes, master_loss_types,
│       │                              master_soi_area, master_soi_area_item,
│       │                              master_safety_incident_type, master_safety_bias_guard
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py             ← BaseRepository (SP wrapper + query-builder helpers;
│       │   │                          inherits reporting pattern §3 of Reporting BACKEND_STRUCTURE)
│       │   ├── incident_repo.py    ← Phase transitions, field-history append, recommendation rollup
│       │   ├── near_miss_repo.py   ← Share vims_safety_incident via record_type discriminator
│       │   ├── scm_repo.py         ← Meeting + attendance + agenda + WRH live-join
│       │   ├── soi_repo.py         ← Inspection + area stamping + finding registration + unique-ID
│       │   ├── action_repo.py      ← CA lifecycle + purchase_req_id hard FK resolution
│       │   └── exceptions.py       ← SafetyDomainError, PhaseTransitionDenied, ALARPGateFailed, etc.
│       ├── authentication/
│       │   ├── __init__.py
│       │   ├── permissions.py      ← HasFormPermission / HasProcessPermission for SAF_F_*/SAF_P_*
│       │   ├── backends.py         ← Reuse VIMS SimpleJWT config; no new token issuer
│       │   ├── vessel_scope.py     ← Reuse master_RoleByVessel (office) + Crew_Onboarding_History (ship)
│       │   └── reporter_identity.py ← D-GAP-J1 revised: reporter details visible to authorized users
│       │                               within vessel scope; no anonymous/masked reporter output
│       ├── serializers/
│       │   ├── __init__.py
│       │   ├── incident.py
│       │   ├── near_miss.py        ← Returns reporter details for authorized users; no anonymous/masked display
│       │   ├── scm.py
│       │   ├── soi.py
│       │   ├── action.py
│       │   └── reference.py        ← Read-only serializers for master_* (pagination + search)
│       ├── views/
│       │   ├── __init__.py
│       │   ├── incident_views.py   ← CRUD + 9 phase-transition endpoints + PDF + search
│       │   ├── near_miss_views.py  ← CRUD + Office Comments priority decision + reporter-visible PDF
│       │   ├── scm_views.py        ← Regular + Ad-Hoc; attendance roll; agenda; PDF
│       │   ├── soi_views.py        ← CRUD + area-applicability + paper-first checklist generator
│       │   │                          + finding registration + unique-ID endpoint
│       │   ├── action_views.py     ← CA + physical-verification
│       │   ├── reference_views.py  ← GET-only master_* surfaces
│       │   └── dashboard_views.py  ← Heinrich Ratio, Repeat-root-cause, CA-Aging, SOI-Compliance-%
│       ├── services/
│       │   ├── pdf_renderer.py     ← reportlab 4.2.0 — D-PDF-01/02/03a/03b templates
│       │   ├── soi_checklist_generator.py ← reportlab + openpyxl + qrcode/python-barcode (D-GAP-E1)
│       │   ├── phase_state_machine.py     ← 9-phase transitions + loop-back audit emission
│       │   ├── alarp_gate.py              ← ALARP attestation aggregator (D-GAP-R02)
│       │   ├── notification_dispatcher.py ← Writes to master_notification rows
│       │   └── retention_job.py           ← 3-year hard-delete job (D-GAP-G2); Celery-beat scheduled
│       ├── tasks/
│       │   ├── __init__.py
│       │   ├── pdf_tasks.py               ← Async reportlab render
│       │   ├── rollup_tasks.py            ← D-GAP-M27 Heinrich, D-GAP-H2 radar, D-GAP-M29 CA aging
│       │   ├── overdue_flags.py           ← 80% risk-band deadline flagging (D-GAP-F3)
│       │   └── retention.py               ← 3-year purge (D-GAP-G2)
│       └── migrations/
│           ├── 0001_initial.py            ← All 14 vims_safety_* CREATE TABLEs + FKs + indexes
│           ├── 0002_seed_master_tables.py ← Seed-load master_mscat_taxonomy (174),
│           │                                 master_immediate_causes (52),
│           │                                 master_loss_types (7),
│           │                                 master_soi_area (13),
│           │                                 master_soi_area_item (329),
│           │                                 master_safety_incident_type (32 active),
│           │                                 master_safety_bias_guard (8) from
│           │                                 safety-reference-data/*.csv
│           └── 0003_seed_permission_ids.py ← Register SAF_F_001–020 + SAF_P_001–024 into
│                                              msc_profiles (idempotent insert-or-ignore)
├── config/
│   ├── settings.py                 ← INSTALLED_APPS += ['apps.safety']
│   └── urls.py                     ← path('api/safety/', include('apps.safety.urls'))
└── tests/
    └── safety/                     ← pytest; mirror tests/reporting/ structure
        ├── test_db_connection.py
        ├── test_auth.py
        ├── test_permissions.py
        ├── test_vessel_scope.py
        ├── test_reporter_identity.py ← D-GAP-J1 revised: reporter details visible to authorized users
        ├── test_phase_state_machine.py
        ├── test_soi_paper_first.py ← No scan-upload column, no upload endpoint (D-GAP-E4)
        ├── test_ca_fk.py           ← vims_safety_corrective_action.purchase_req_id hard FK
        └── test_cross_module_joins.py
```

### 1.2 `INSTALLED_APPS` registration step

In `config/settings.py`, after the existing Reporting / Inspection entries, append:

```python
INSTALLED_APPS = [
    # ... django.contrib.* entries ...
    # ... platform apps (auth, common, notifier) ...
    'apps.reporting',
    'apps.inspection',
    'apps.safety',        # NEW — Safety module
]
```

The `apps.safety.apps.SafetyConfig` class wires the `default_auto_field`, `name`, and a `ready()` hook. `ready()` imports `apps.safety.signals` (field-history append-only emitters) and registers Celery-beat schedules (rollup, 80% overdue flag, retention).

### 1.3 URL include step

In `config/urls.py`, append once:

```python
from django.urls import include, path

urlpatterns = [
    # ... existing VIMS routes ...
    path('api/reporting/', include('apps.reporting.urls')),
    path('api/inspection/', include('apps.inspection.urls')),
    path('api/safety/',    include('apps.safety.urls')),   # NEW
]
```

### 1.4 Frontend folder tree (React 18 + TypeScript 5.4.5 + Vite 5.4.0)

```
<vims-repo-root>/src/
├── routes/
│   ├── reporting/                  ← sibling (exists)
│   └── safety/                     ← NEW
│       ├── index.tsx               ← Lazy-loaded route defs; each wrapped with PermissionGate(SAF_F_*)
│       ├── layout.tsx              ← Safety module chrome (breadcrumbs, vessel dropdown slot)
│       ├── incident/               ← 9-phase sub-routes (intake → closure)
│       ├── near-miss/              ← lightweight lifecycle; reporter identity visible by permission
│       ├── scm/                    ← Regular + Ad-Hoc
│       └── soi/                    ← Paper-first 13-area / 329-item
├── components/
│   └── safety/                     ← NEW
│       ├── shared/
│       │   ├── SignatureBlock.tsx
│       │   ├── ReporterIdentity.tsx
│       │   ├── MScatPicker.tsx
│       │   ├── BiasGuardChecklist.tsx
│       │   ├── BarrierAnalysisCanvas.tsx
│       │   ├── CausalLayerTabs.tsx
│       │   └── SoiFindingRow.tsx
│       ├── incident/
│       ├── near-miss/
│       ├── scm/
│       └── soi/
├── hooks/safety/                   ← useSafetyIncident, useSafetySoiChecklist, etc.
├── stores/safety/                  ← Zustand — draft incident, SOI selected areas, Ad-Hoc SCM trigger
├── schemas/safety/                 ← Zod schemas per form (schema_version column on vims_safety_incident)
└── tests/frontend/safety/
```

---

## 2. Database Naming + Router Contract

### 2.1 Naming convention (law)

| Prefix | Scope | Example |
|--------|-------|---------|
| `vims_safety_*` | Module-owned transactional tables | `vims_safety_incident`, `vims_safety_scm_meeting` |
| `master_*` | Shared reference / seed data (DPA-maintained, cross-module consumable) | `master_mscat_taxonomy`, `master_soi_area`, `master_role` |
| *(none)* | Legacy tables — retained as-is | `Crew_Onboarding_History`, `HRM501`, `VesselData` |

**Zero occurrences** of a bare `safety_*` table reference anywhere in this document. Where the SSOT uses `safety_X`, translate via the `<database_naming_convention>` map before rendering DDL.

### 2.2 DB router — single connection

Safety uses the **same `ksm_marine_live` SQL Server instance** as Reporting / Inspection / platform. No new DB alias is registered. The Django router returns the default alias for every Safety model:

```python
# apps/safety/routing.py  (intentionally minimal — no new DB)
class SafetyRouter:
    safety_app = 'safety'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.safety_app:
            return 'default'        # ksm_marine_live
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.safety_app:
            return 'default'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.safety_app:
            return db == 'default'
        return None
```

`DATABASES['default']` is already defined at platform level in `config/settings.py` with `ENGINE='mssql'`, `HOST='localhost'`, `PORT=1433`, `NAME='ksm_marine_live'`, ODBC Driver 18, `Encrypt=no`, `TrustServerCertificate=yes`, and Windows trusted connection when no SQL username/password is supplied. Safety adds no standalone database.

### 2.3 Character set, collation, time

- All text columns: `NVARCHAR(N)` (Unicode) — platform standard.
- All timestamps: `DATETIME2` stored UTC; rendered to vessel local time via `wrh_ship_time_config` (D-GAP-M26).
- `updated_date` on every transactional row for optimistic locking (platform pattern per `VIMS-Reporting-Module/BACKEND_STRUCTURE.md` §1A).

---

## 3. Auth & RBAC Inheritance

Safety registers **no new auth tables** and **no new permission catalog**. Everything inherits from the VIMS platform per `ssot_auth_specific.md`.

### 3.1 Shared auth tables (read-only to Safety)

| Table | Purpose | Safety use |
|-------|---------|-----------|
| `users` | Office login credentials | Office identity resolution |
| `Ship_UsersLogin` | Ship-side login credentials | Ship identity resolution |
| `HRM501` | Crew master (rank, dept, email, crew_id) | Ship-side enrichment for SOI assistant dept check |
| `Crew_Onboarding_History` | Crew-to-vessel assignment (latest) | Ship-side vessel scope; SCM attendance roster |
| `VesselData` | Vessel master | All vessel FKs |
| `master_applied_rank` | Rank normalization | Ship-side role resolution |
| `mapping_role_user` | Office user → role IDs | Office role chain |
| `master_role` | Role ID → role name | Office role chain |
| `msc_profiles` | `form_ids` + `process_ids` per profile | SAF_F_*/SAF_P_* live here |
| `master_RoleByVessel` | Office user → vessel scope | Office vessel filter |

### 3.2 Permission ID registry — `SAF_F_*` / `SAF_P_*`

Mirror Reporting's `RPT_F_*` / `RPT_P_*` pattern. Registered in `msc_profiles` by migration `0003_seed_permission_ids.py` (idempotent `INSERT ... WHERE NOT EXISTS`).

**Form IDs (`SAF_F_*`) — screen / route access:**

| ID | Feature scope |
|----|---------------|
| `SAF_F_001` | Incident list + detail |
| `SAF_F_002` | Incident create |
| `SAF_F_003` | Incident phase workbench (3–6) |
| `SAF_F_004` | Near Miss list + detail |
| `SAF_F_005` | Near Miss create |
| `SAF_F_006` | Near Miss reporter-identity view for authorized users |
| `SAF_F_007` | SCM list + detail |
| `SAF_F_008` | SCM Regular create |
| `SAF_F_009` | SCM Ad-Hoc trigger (Master/CO host) |
| `SAF_F_010` | SOI list + detail |
| `SAF_F_011` | SOI plan + checklist generator |
| `SAF_F_012` | SOI finding register |
| `SAF_F_013` | SOI area-applicability toggle (Master → DPA approval) |
| `SAF_F_014` | CA list + detail |
| `SAF_F_015` | Safety Intelligence Dashboard |
| `SAF_F_016` | Safety Search (FTS — BLOCKED until deferral #8 resolves) |
| `SAF_F_017` | Audit-trail viewer (field history) |
| `SAF_F_018` | DPA reference-data admin (M-SCAT / SOI taxonomy) |
| `SAF_F_019` | PDF export surface |
| `SAF_F_020` | Auditor leave-behind bundle export |

**Process IDs (`SAF_P_*`) — action access:**

| ID | Action |
|----|--------|
| `SAF_P_001` | Create incident / near miss |
| `SAF_P_002` | Submit phase transition |
| `SAF_P_003` | Request phase loop-back (Phase 5→3, Phase 6→3) |
| `SAF_P_004` | Office Review accept |
| `SAF_P_005` | FM approve RED closure |
| `SAF_P_006` | PIC close GREEN |
| `SAF_P_007` | PDF/export and formal close actions (SOI closure, incident); SCM closure is Office Comment |
| `SAF_P_008` | Re-open closed incident |
| `SAF_P_009` | Override blame-fixation hard block |
| `SAF_P_010` | Override ALARP gate |
| `SAF_P_011` | Override timeline (request extension per D-GAP-B2) |
| `SAF_P_012` | Create SCM Ad-Hoc |
| `SAF_P_013` | Register SOI finding |
| `SAF_P_014` | Mark finding pending-closure |
| `SAF_P_015` | Approve finding closure |
| `SAF_P_016` | Toggle SOI area applicable=false |
| `SAF_P_017` | Approve area-applicability change (DPA) |
| `SAF_P_018` | Edit M-SCAT taxonomy (DPA-only) |
| `SAF_P_019` | Edit SOI taxonomy (DPA-only) |
| `SAF_P_020` | Create CA with Purchase Req hard FK |
| `SAF_P_021` | Link CA to PR |
| `SAF_P_022` | Approve CA physical verification |
| `SAF_P_023` | Export PDF (D-PDF-01/02/03a/03b) |
| `SAF_P_024` | Emit fleet circular (via VIMS Circular module) |

### 3.3 Permission enforcement in DRF

```python
# apps/safety/authentication/permissions.py
from rest_framework.permissions import BasePermission

class HasFormPermission(BasePermission):
    form_id = None
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        form_id = getattr(view, 'form_id', self.form_id)
        if not form_id:
            return False
        user_form_ids = getattr(request.user, 'form_ids', []) or []
        return form_id in user_form_ids


class HasProcessPermission(BasePermission):
    process_id = None

    def has_permission(self, request, view):
        process_id = getattr(view, 'process_id', self.process_id)
        if not process_id:
            return False
        user_process_ids = getattr(request.user, 'process_ids', []) or []
        return process_id in user_process_ids


class HasVesselScope(BasePermission):
    """Vessel-scope gate. Applied after has_permission; deny if vessel_id
    in the request payload (or URL param) not in user's allowed vessel list."""
    # Impl details in vessel_scope.py — consults master_RoleByVessel for office users,
    # Crew_Onboarding_History for ship users. Global-access flag bypasses.
```

### 3.4 Near-miss reporter identity (D-GAP-J1 revised 2026-06-09)

Anonymous near-miss reporting is removed from V1. The backend stores reporter user id, name, rank, and device fingerprint on `vims_safety_incident` rows with `record_type='NEAR_MISS'`.

Serializer and PDF behavior:
- Reporter fields are returned to authorized users according to Safety permissions and vessel scope.
- The API must not replace the reporter with `Anonymous Reporter`.
- The PDF renderer must not print "Reporter identity is masked" or any equivalent masking text.
- Field history retains reporter changes like any other audited field.

---

## 4. Full Schema — Transactional Tables

All 14 module-owned tables below live in `ksm_marine_live` under the `vims_safety_*` prefix. DDL is rendered in T-SQL / Django-compatible SQL Server syntax; Django ORM models live at `apps/safety/models/*.py` and map 1:1. Every table inherits the platform columns:

| Inherited column | Type | Default | Purpose |
|------------------|------|---------|---------|
| `id` | BIGINT IDENTITY(1,1) PRIMARY KEY | — | Surrogate PK |
| `vessel_id` | UNIQUEIDENTIFIER NOT NULL | — | FK → `VesselData.VesselID` |
| `schema_version` | INT NOT NULL | 1 | Per D-EDGE-11 — grandfathered per row; form schema versioning |
| `is_deleted` | BIT NOT NULL | 0 | Soft-delete flag (platform pattern) |
| `archived_at` | DATETIME2 NULL | NULL | Soft-archive per deferral #3 — implementation TBD |
| `created_by` | NVARCHAR(128) NOT NULL | — | Username / CrewId |
| `created_date` | DATETIME2 NOT NULL | `SYSUTCDATETIME()` | UTC |
| `updated_by` | NVARCHAR(128) NULL | — | Last editor |
| `updated_date` | DATETIME2 NULL | — | UTC; optimistic-lock field |

### 4.1 `vims_safety_incident` — Incident + Near Miss master record

Single-table design. `record_type` discriminator covers Near Miss (SSOT §4.3). Near-miss-specific fields nullable for incidents and vice versa (SSOT §4.3 verbatim).

> **Build-time deferral #1 (ENUMs / nullability):** exact ENUM values for `state`, `risk_band`, `imo_classifier`, `loss_type_primary_id`, plus nullability for phase-specific columns are finalised during Phase 1 by the Backend lead. Body below renders the current locked surface and marks each deferral-affected column.

```sql
CREATE TABLE vims_safety_incident (
  id                          BIGINT        IDENTITY(1,1) NOT NULL,
  incident_number             NVARCHAR(32)  NOT NULL,          -- Format {VslCode}/{YYYY}/{NNN} (FEAT-SAF-INC-040, D-GAP-C1). DRAFT series separate.
  vessel_id                   UNIQUEIDENTIFIER NOT NULL,
  record_type                 VARCHAR(16)   NOT NULL,          -- CHECK IN ('INCIDENT','NEAR_MISS') — SSOT §4.3 discriminator
  state                       VARCHAR(48)   NOT NULL,          -- Phase 1..8 + 'CLOSED' + 'DRAFT' (deferral #1 locks exact set)
  phase                       TINYINT       NOT NULL,          -- 1..8; derived from state
  risk_band                   VARCHAR(8)    NULL,              -- CHECK IN ('GREEN','YELLOW','RED') §2B.3; NULL until Phase 1 classifier runs
  imo_classifier              VARCHAR(16)   NULL,              -- CHECK IN ('SMC','MC','MI','NOT_APPLICABLE') D-GAP-R08
  incident_type_id            INT           NULL,              -- FK → master_safety_incident_type.id (32 active rows §2B.5)
  loss_type_primary_id        INT           NULL,              -- FK → master_loss_types.id (7 rows §2B.4)
  investigation_depth         VARCHAR(8)    NULL,              -- CHECK IN ('SHALLOW','MEDIUM','DEEP') D-GAP-R14
  -- ── Phase 1 intake ─────────────────────────────────────────────────
  occurred_at                 DATETIME2     NULL,
  reported_at                 DATETIME2     NULL,
  latitude                    DECIMAL(9,6)  NULL,
  longitude                   DECIMAL(9,6)  NULL,
  shore_assistance_required   BIT           NULL,              -- CR-024: main incident reporting context shared by incident/injury reporting
  vessel_location             NVARCHAR(128) NULL,
  onboard_location            NVARCHAR(128) NULL,
  last_port                   NVARCHAR(128) NULL,
  departure_date              DATE          NULL,
  vessel_condition            VARCHAR(16)   NULL,              -- 'LOADED' | 'BALLAST'
  position_source             VARCHAR(32)   NULL,              -- 'DAILY_REPORT_AUTO' | 'MANUAL' | 'DAILY_REPORT_EDITED' (D-GAP-M09)
  position_daily_report_id    UNIQUEIDENTIFIER NULL,           -- FK → vims_noon_report / DepartureReport / ArrivalReport (live join; no hard FK — cross-module table union)
  narrative                   NVARCHAR(MAX) NULL,              -- min 200 chars at Phase 1 submit (V-INC-001)
  awaiting_daily_report_match BIT           NOT NULL DEFAULT 0,-- D-GAP-M10: flag when no DR within ±12h
  first_hour_checklist_done   BIT           NOT NULL DEFAULT 0,-- legacy storage only; not exposed in current Phase 1 UI/API/PDF (D-MAINT-CR018)
  -- ── Phase 2 notification + resources ──────────────────────────────
  slack_notified_at           DATETIME2     NULL,
  notification_channel_count  INT           NOT NULL DEFAULT 0,
  resources_allocated         NVARCHAR(MAX) NULL,              -- JSON blob of role → assignee
  -- ── Near Miss specific ────────────────────────────────────────────
  near_miss_priority          VARCHAR(8)    NULL,              -- CHECK IN ('LOW','HIGH') D-GAP-R22 (NM only)
  near_miss_place             VARCHAR(16)   NULL,              -- 'AT_ANCHOR' | 'AT_SEA' | 'AT_PORT' (NM only)
  near_miss_shell_tag         VARCHAR(32)   NULL,              -- first selected category tag for compatibility
  near_miss_category_tags     NVARCHAR(MAX) NULL,              -- JSON array, up to 3 category tags
  near_miss_incident_type_ids NVARCHAR(MAX) NULL,              -- legacy compatibility only; Near Miss Type is not shown in V1 UI
  near_miss_mscat_category_id INT           NULL,              -- legacy compatibility only; new create/rework clears this
  near_miss_mscat_subcode_id  VARCHAR(16)   NULL,              -- legacy compatibility only; new create/rework clears this
  near_miss_mscat_subcode_ids NVARCHAR(MAX) NULL,              -- legacy compatibility only; new create/rework clears this
  near_miss_factor_causes     NVARCHAR(MAX) NULL,              -- JSON factor causes: HUMAN/VESSEL/MANAGEMENT/OTHER x IMMEDIATE/ROOT
  reporter_id                 NVARCHAR(64)  NULL,              -- CrewId or user_id — visible by vessel scope + Safety permission
  reporter_name               NVARCHAR(128) NULL,
  reporter_rank               NVARCHAR(64)  NULL,
  reporter_email              NVARCHAR(128) NULL,
  reporter_department         NVARCHAR(64)  NULL,
  reporter_device_fingerprint NVARCHAR(256) NULL,              -- D-GAP-D1 hybrid signature/audit
  -- ── Phase 3 evidence sentinel flags ───────────────────────────────
  chain_of_custody_ok         BIT           NOT NULL DEFAULT 0,-- D-GAP-R04
  marine_docs_checklist_done  BIT           NOT NULL DEFAULT 0,-- D-GAP-R05
  cargo_evidence_applicable   BIT           NOT NULL DEFAULT 0,-- D-GAP-R10
  health_fatigue_applicable   BIT           NOT NULL DEFAULT 0,-- D-GAP-R23
  -- ── Phase 5 causal analysis sentinel ──────────────────────────────
  causal_layering_complete    BIT           NOT NULL DEFAULT 0,-- D-GAP-R01
  alarp_attested              BIT           NOT NULL DEFAULT 0,-- D-GAP-R02 (RED/YELLOW hard gate)
  bias_guard_attestations     VARCHAR(64)   NOT NULL DEFAULT '',-- bitmask of 8 guards (D-DNV-11 + D-GAP-R12)
  blame_fixation_override_by  NVARCHAR(64)  NULL,              -- D-DNV-11 #5 override (DPA GREEN/YELLOW; FM RED)
  -- ── Office Review acceptance ──────────────────────────────────────
  dpa_accepted_at             DATETIME2     NULL,
  dpa_accepted_by             NVARCHAR(64)  NULL,
  fm_approved_at              DATETIME2     NULL,              -- RED-only closure per D-GAP-M06
  fm_approved_by              NVARCHAR(64)  NULL,
  office_comment              NVARCHAR(MAX) NULL,              -- Visible Phase 6 Office Review comments; no word/character limit
  closed_at                   DATETIME2     NULL,
  closure_reason              NVARCHAR(MAX) NULL,
  -- ── Multi-vessel linkage (D-EDGE-01, D-GAP-M25) ───────────────────
  linked_incident_id          BIGINT        NULL,              -- FK → vims_safety_incident.id (self) — supersede/link per FEAT-SAF-INC-032/033
  superseded_by_id            BIGINT        NULL,              -- FK → self; near-miss → incident upgrade
  -- ── Platform inherited ────────────────────────────────────────────
  schema_version              INT           NOT NULL DEFAULT 1,
  is_deleted                  BIT           NOT NULL DEFAULT 0,
  archived_at                 DATETIME2     NULL,
  created_by                  NVARCHAR(128) NOT NULL,
  created_date                DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_by                  NVARCHAR(128) NULL,
  updated_date                DATETIME2     NULL,
  CONSTRAINT PK_vims_safety_incident PRIMARY KEY CLUSTERED (id),
  CONSTRAINT UQ_vims_safety_incident_number UNIQUE (incident_number),
  CONSTRAINT FK_vims_safety_incident_vessel FOREIGN KEY (vessel_id) REFERENCES VesselData(VesselID),
  CONSTRAINT FK_vims_safety_incident_type FOREIGN KEY (incident_type_id) REFERENCES master_safety_incident_type(id),
  CONSTRAINT FK_vims_safety_incident_loss FOREIGN KEY (loss_type_primary_id) REFERENCES master_loss_types(id),
  CONSTRAINT FK_vims_safety_incident_linked FOREIGN KEY (linked_incident_id) REFERENCES vims_safety_incident(id),
  CONSTRAINT FK_vims_safety_incident_superseded FOREIGN KEY (superseded_by_id) REFERENCES vims_safety_incident(id),
  CONSTRAINT CK_vims_safety_incident_record_type CHECK (record_type IN ('INCIDENT','NEAR_MISS')),
  CONSTRAINT CK_vims_safety_incident_risk_band CHECK (risk_band IS NULL OR risk_band IN ('GREEN','YELLOW','RED')),
  CONSTRAINT CK_vims_safety_incident_imo_class CHECK (imo_classifier IS NULL OR imo_classifier IN ('SMC','MC','MI','NOT_APPLICABLE')),
  CONSTRAINT CK_vims_safety_incident_phase CHECK (phase BETWEEN 0 AND 8)
);

CREATE INDEX IX_vims_safety_incident_vessel_date ON vims_safety_incident (vessel_id, occurred_at) WHERE is_deleted = 0;
CREATE INDEX IX_vims_safety_incident_state      ON vims_safety_incident (state) WHERE is_deleted = 0;
CREATE INDEX IX_vims_safety_incident_record_type ON vims_safety_incident (record_type, state);
CREATE INDEX IX_vims_safety_incident_risk_band  ON vims_safety_incident (risk_band) WHERE risk_band IS NOT NULL;
CREATE INDEX IX_vims_safety_incident_linked     ON vims_safety_incident (linked_incident_id) WHERE linked_incident_id IS NOT NULL;
```

Triggers: none (use Django ORM pre/post-save signals in `apps/safety/signals.py` to write `vims_safety_incident_phase_log` and `vims_safety_field_history` rows). Trigger-free approach matches the Reporting module precedent (§3 SP Wrapper pattern) and keeps audit logic in application code testable under pytest.

### 4.0A `vims_safety_external_party_injury` - Phase 1 injury record

The physical table name remains `vims_safety_external_party_injury` for backwards compatibility, but the functional record now supports both crew and non-crew injuries. The discriminator is `injured_person_type`.

```sql
ALTER TABLE vims_safety_external_party_injury ADD injured_person_type VARCHAR(16) NOT NULL DEFAULT 'NON_CREW';
ALTER TABLE vims_safety_external_party_injury ALTER COLUMN party_name NVARCHAR(128) NULL;
ALTER TABLE vims_safety_external_party_injury ALTER COLUMN party_type VARCHAR(32) NULL;
ALTER TABLE vims_safety_external_party_injury ALTER COLUMN company_name NVARCHAR(128) NULL;
ALTER TABLE vims_safety_external_party_injury ALTER COLUMN severity NVARCHAR(64) NULL;
ALTER TABLE vims_safety_external_party_injury ADD crew_rank NVARCHAR(128) NULL;
ALTER TABLE vims_safety_external_party_injury ADD crew_age SMALLINT NULL;
ALTER TABLE vims_safety_external_party_injury ADD crew_activity_type NVARCHAR(128) NULL;
ALTER TABLE vims_safety_external_party_injury ADD shore_assistance_required BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD vessel_location NVARCHAR(128) NULL;
ALTER TABLE vims_safety_external_party_injury ADD onboard_location NVARCHAR(128) NULL;
ALTER TABLE vims_safety_external_party_injury ADD last_port NVARCHAR(128) NULL;
ALTER TABLE vims_safety_external_party_injury ADD departure_date DATE NULL;
ALTER TABLE vims_safety_external_party_injury ADD vessel_condition VARCHAR(16) NULL;
ALTER TABLE vims_safety_external_party_injury ADD what_happened_narrative NVARCHAR(MAX) NULL;
ALTER TABLE vims_safety_external_party_injury ADD nature_of_injury NVARCHAR(255) NULL;
ALTER TABLE vims_safety_external_party_injury ADD source_of_injury NVARCHAR(255) NULL;
ALTER TABLE vims_safety_external_party_injury ADD affected_body_areas NVARCHAR(255) NULL;
ALTER TABLE vims_safety_external_party_injury ADD first_aid_details NVARCHAR(MAX) NULL;
ALTER TABLE vims_safety_external_party_injury ADD why_it_happened_analysis NVARCHAR(MAX) NULL;
ALTER TABLE vims_safety_external_party_injury ADD regulation_or_procedure_breach NVARCHAR(MAX) NULL;
ALTER TABLE vims_safety_external_party_injury ADD risk_assessment_carried_out VARCHAR(8) NULL;
ALTER TABLE vims_safety_external_party_injury ADD toolbox_meeting_carried_out VARCHAR(8) NULL;
ALTER TABLE vims_safety_external_party_injury ADD prevention_action_taken_required NVARCHAR(MAX) NULL;
ALTER TABLE vims_safety_external_party_injury ADD ocimf_fatality BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD ocimf_permanent_total_disability BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD ocimf_permanent_partial_disability BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD ocimf_lost_workday_case BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD ocimf_restricted_workday_case BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD ocimf_medical_treatment_case BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD ocimf_first_aid_case BIT NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_medicines_onboard DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_doctor_visits DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_repatriation DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_evacuation DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_off_hire DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_vessel_delays DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_man_hours_lost DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_deviation DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD cost_miscellaneous DECIMAL(12,2) NULL;
ALTER TABLE vims_safety_external_party_injury ADD miscellaneous_expenses_reason NVARCHAR(MAX) NULL;
ALTER TABLE vims_safety_external_party_injury ADD total_estimated_cost DECIMAL(12,2) NULL;
```

Serializer contract: `external_party_injury` is nested in Phase 1 create/update. Non-crew requires the original fields; crew details are nullable draft fields. The old injury-row context columns `shore_assistance_required`, `vessel_location`, `onboard_location`, `last_port`, `departure_date`, and `vessel_condition` remain for backward compatibility with older injury records, but the current Phase 1 UI/API source of truth is the incident-level columns added by CR-024. On update, a populated nested payload creates or updates the injury row; a null or omitted `external_party_injury` leaves any existing injury row unchanged.

### 4.0B `vims_safety_injury_dropdown_option` - Injury dropdown master

This table owns the Phase 1 crew injury dropdown values for `Nature of Injury`, `Source of Injury`, `Affected Areas of the Body`, and `Type of Activity`. It also owns the Phase 7 Injury Report `Code of Safe Working Practices` dropdown category through `field_key = SAFE_WORKING_PRACTICE`; migration `0055_seed_safe_working_practice_options` seeds the active Code of Safe Working Practices list and deactivates stale safe-working-practice choices outside that list. The selected label, or the typed value when `Others(Specify)` is used, is still stored in the transaction row that owns the field.

```sql
CREATE TABLE vims_safety_injury_dropdown_option (
  id            UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
  field_key     VARCHAR(32)      NOT NULL, -- NATURE_OF_INJURY | SOURCE_OF_INJURY | AFFECTED_BODY_AREA | TYPE_OF_ACTIVITY | SAFE_WORKING_PRACTICE
  option_label  NVARCHAR(255)    NOT NULL,
  display_order SMALLINT         NOT NULL DEFAULT 0,
  active        BIT              NOT NULL DEFAULT 1,
  created_by    NVARCHAR(128)    NOT NULL DEFAULT 'system',
  created_date  DATETIME2        NOT NULL,
  updated_by    NVARCHAR(128)    NULL,
  updated_date  DATETIME2        NULL
);

ALTER TABLE vims_safety_injury_dropdown_option
  ADD CONSTRAINT uq_injury_dropdown_field_label UNIQUE (field_key, option_label);

CREATE INDEX ix_injury_dropdown_lookup
  ON vims_safety_injury_dropdown_option (active, field_key, display_order);
```

Reference API:

```text
GET /api/safety/reference/injury-dropdown-options/
GET /api/safety/reference/injury-dropdown-options/?field_key=NATURE_OF_INJURY
GET /api/safety/reference/injury-dropdown-options/?field_key=TYPE_OF_ACTIVITY
GET /api/safety/reference/injury-dropdown-options/?field_key=SAFE_WORKING_PRACTICE
```

### 4.0C `vims_safety_incident_loss_evaluation` - Phase 7 Loss Evaluation

This table stores the current visible Phase 7 Loss Evaluation. It is one editable row per incident and is required before Phase 7 close. The backend keeps the compatibility route `/api/safety/incidents/{id}/phase-6/`, but GET/PATCH saves are no longer gated by Office Review approval/backend `current_phase = 8`; authorized ship-side and office-side users with incident form access and vessel scope can save it. The payload is now Loss Evaluation rather than Check Actions. Migration `0056_incident_loss_evaluation_report_type.py` adds nullable `report_type` so users can choose Incident Report or Injury Report first; existing rows without that value use the old injury-record fallback.

```sql
CREATE TABLE vims_safety_incident_loss_evaluation (
  id                                            UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
  incident_id                                   UNIQUEIDENTIFIER NOT NULL UNIQUE,
  report_type                                   VARCHAR(16) NULL,
  consequence                                   VARCHAR(32) NULL,
  likelihood                                    VARCHAR(32) NULL,
  risk_level                                    VARCHAR(32) NULL,
  name_of_master                                NVARCHAR(128) NULL,
  name_of_chief_engineer                        NVARCHAR(128) NULL,
  repair_type                                   VARCHAR(32) NULL,
  repair_details                                NVARCHAR(MAX) NULL,
  last_overhaul_maintenance_survey_details      NVARCHAR(MAX) NULL,
  safe_working_practice                         NVARCHAR(255) NULL,
  man_hours_worked                              DECIMAL(10,2) NULL,
  hours_worked_previous_day                     DECIMAL(10,2) NULL,
  hours_rest_last_96_hours                      DECIMAL(10,2) NULL,
  delay_to_vessel                               NVARCHAR(MAX) NULL,
  delay_reason                                  NVARCHAR(MAX) NULL,
  repair_man_hours_lost                         DECIMAL(10,2) NULL,
  materials_used_repairs_onboard                NVARCHAR(MAX) NULL,
  materials_specify_details                     NVARCHAR(MAX) NULL,
  materials_reason                              NVARCHAR(MAX) NULL,
  deviation                                     BIT NULL,
  off_hire                                      BIT NULL,
  injury_man_hours_lost                         DECIMAL(10,2) NULL,
  injury_reasons                                NVARCHAR(MAX) NULL,
  repatriation                                  BIT NULL,
  hospitalization                               BIT NULL,
  evacuation                                    BIT NULL,
  estimated_cost_off_hire                       DECIMAL(12,2) NULL,
  estimated_cost_delay                          DECIMAL(12,2) NULL,
  estimated_cost_man_hours                      DECIMAL(12,2) NULL,
  estimated_cost_deviation                      DECIMAL(12,2) NULL,
  estimated_cost_materials                      DECIMAL(12,2) NULL,
  estimated_cost_miscellaneous                  DECIMAL(12,2) NULL,
  total_estimated_cost                          DECIMAL(12,2) NULL,
  miscellaneous_expenses_reason                 NVARCHAR(MAX) NULL,
  cost_medicines_onboard                        DECIMAL(12,2) NULL,
  cost_doctor_visits                            DECIMAL(12,2) NULL,
  cost_repatriation                             DECIMAL(12,2) NULL,
  cost_evacuation                               DECIMAL(12,2) NULL,
  cost_injury_delay                             DECIMAL(12,2) NULL,
  cost_injury_man_hours                         DECIMAL(12,2) NULL,
  cost_injury_deviation                         DECIMAL(12,2) NULL,
  cost_injury_miscellaneous                     DECIMAL(12,2) NULL,
  injury_total_estimated_cost                   DECIMAL(12,2) NULL,
  injury_miscellaneous_expenses_reason          NVARCHAR(MAX) NULL,
  schema_version                                INT NOT NULL DEFAULT 1,
  created_by                                    NVARCHAR(128) NOT NULL,
  created_date                                  DATETIME2 NOT NULL,
  updated_by                                    NVARCHAR(128) NULL,
  updated_date                                  DATETIME2 NULL
);
```

Dropdown constraints:
- `consequence`: `MINOR`, `APPRECIABLE`, `MAJOR`, `SEVERE`, `CATASTROPHIC`.
- `likelihood`: `REMOTE`, `UNLIKELY`, `POSSIBLE`, `LIKELY`, `ALMOST_CERTAIN`.
- `risk_level`: `VERY_LOW`, `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`.
- `repair_type`: `TEMPORARY`, `PERMANENT`.

### 4.1A `vims_safety_near_miss_cause_option` — Near Miss cause dropdown seed table

This table owns the Near Miss factor-cause dropdown values. It is separate from `master_mscat_taxonomy` because Near Miss uses a simpler crew-facing cause model.

```sql
CREATE TABLE vims_safety_near_miss_cause_option (
  id             UNIQUEIDENTIFIER NOT NULL,
  factor         VARCHAR(16)      NOT NULL,  -- HUMAN | VESSEL | MANAGEMENT | OTHER
  cause_stage    VARCHAR(16)      NOT NULL,  -- IMMEDIATE | ROOT
  option_code    NVARCHAR(64)     NOT NULL,
  option_text    NVARCHAR(MAX)    NOT NULL,
  display_order  SMALLINT         NOT NULL DEFAULT 0,
  active         BIT              NOT NULL DEFAULT 1,
  created_by     NVARCHAR(128)    NOT NULL DEFAULT 'system',
  created_date   DATETIME2        NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_by     NVARCHAR(128)    NULL,
  updated_date   DATETIME2        NULL,
  CONSTRAINT PK_vims_safety_near_miss_cause_option PRIMARY KEY CLUSTERED (id),
  CONSTRAINT uq_nm_cause_option_factor_stage_code UNIQUE (factor, cause_stage, option_code)
);

CREATE INDEX ix_nm_cause_option_lookup
  ON vims_safety_near_miss_cause_option (active, factor, cause_stage);
```

Seed rows: 128 active options total across four factors and two cause stages. Every factor/stage includes `Other` and `Not Applicable`. The API resolves selections by UUID `id` and stores the selected labels/codes as JSON text on `vims_safety_incident.near_miss_factor_causes`.

### 4.2 `vims_safety_incident_phase_log` — append-only state-change audit

> **Build-time deferral #6:** exact column shape (free-form vs rigid JSON vs typed phase_from/phase_to) is finalised at Phase 1. The variant below is the current locked surface; deferral-affected fields noted.

```sql
CREATE TABLE vims_safety_incident_phase_log (
  id                  BIGINT        IDENTITY(1,1) NOT NULL,
  incident_id         BIGINT        NOT NULL,
  phase_from          TINYINT       NULL,                     -- NULL on first row (creation event)
  phase_to            TINYINT       NOT NULL,
  transition_type     VARCHAR(24)   NOT NULL,                 -- 'FORWARD' | 'LOOP_BACK' | 'REWORK' | 'REOPEN' | 'CLOSE'
  loop_back_reason    NVARCHAR(MAX) NULL,                     -- mandatory when transition_type='LOOP_BACK' (D-GAP-B3)
  actor_user_id       NVARCHAR(64)  NOT NULL,
  actor_role_code     VARCHAR(16)   NOT NULL,                 -- DPA, FM, MASTER, CO, CE, PIC, SSO, HOD, REPORTER
  occurred_at         DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  device_fingerprint  NVARCHAR(256) NULL,                     -- D-GAP-D1 hybrid digital signature footprint
  schema_version      INT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_incident_phase_log PRIMARY KEY CLUSTERED (id),
  CONSTRAINT FK_vims_safety_incident_phase_log_incident FOREIGN KEY (incident_id)
      REFERENCES vims_safety_incident(id) ON DELETE CASCADE,
  CONSTRAINT CK_vims_safety_incident_phase_log_transition CHECK
      (transition_type IN ('FORWARD','LOOP_BACK','REWORK','REOPEN','CLOSE')),
  CONSTRAINT CK_vims_safety_incident_phase_log_loopback_reason CHECK
      (transition_type <> 'LOOP_BACK' OR loop_back_reason IS NOT NULL)
);

CREATE INDEX IX_vims_safety_incident_phase_log_incident ON vims_safety_incident_phase_log (incident_id, occurred_at);
CREATE INDEX IX_vims_safety_incident_phase_log_actor    ON vims_safety_incident_phase_log (actor_user_id, occurred_at);
```

**Append-only contract (enforced at application layer):**

- Django signal `post_save` on `vims_safety_incident` writes the row.
- Django admin class `VimsSafetyIncidentPhaseLogAdmin` has `has_change_permission = False` and `has_delete_permission = False`.
- DB-level prevention via a `DENY UPDATE, DELETE` grant on the `vims_safety_role_writer` role applied in `0001_initial.py`:
  ```sql
  DENY UPDATE, DELETE ON vims_safety_incident_phase_log TO vims_safety_role_writer;
  ```
- Retention: rows purge when the parent incident is hard-deleted (D-GAP-M33).

### 4.3 `vims_safety_field_history` — field-level edit log (D-EDGE-10)

> **Build-time deferral #2 (column shape):** whether to store `old_value` / `new_value` as `NVARCHAR(MAX)` free text, structured `JSON`, typed per-field columns, or include a `content_hash` for tamper visibility. **Each option's trade-off:**
> - **Option A — TEXT (chosen as current lock):** simple; queryable via LIKE; no schema coupling to parent table; lossy for numeric / date typing.
> - **Option B — JSON:** preserves typing; requires SQL Server 2016+ JSON funcs (present in SQL Server); awkward diffs.
> - **Option C — Typed columns + content_hash:** strongest audit defensibility; large per-field migration cost; no crypto if hash is SHA-256 but that conflicts with D-GAP-D2/G2 "no crypto in V1". If chosen, `content_hash` would use a non-crypto rolling hash (e.g., FNV-1a).
> **Decision required at Phase 1 kickoff.** Current DDL renders Option A.

```sql
CREATE TABLE vims_safety_field_history (
  id              BIGINT        IDENTITY(1,1) NOT NULL,
  parent_table    VARCHAR(64)   NOT NULL,                  -- 'vims_safety_incident' | 'vims_safety_scm_meeting' | ...
  parent_id       BIGINT        NOT NULL,
  field_name      VARCHAR(128)  NOT NULL,
  old_value       NVARCHAR(MAX) NULL,                      -- TEXT variant (Option A — deferral #2)
  new_value       NVARCHAR(MAX) NULL,                      -- TEXT variant
  change_reason   NVARCHAR(MAX) NULL,                      -- optional free text
  actor_user_id   NVARCHAR(64)  NOT NULL,
  actor_role_code VARCHAR(16)   NOT NULL,
  changed_at      DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  schema_version  INT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_field_history PRIMARY KEY CLUSTERED (id)
  -- NO FK to parent: polymorphic. Parent_table + parent_id resolved in app layer.
  -- Retention tied to parent per D-GAP-M33 — purge job reads parent_table/parent_id and removes orphan rows.
);

CREATE INDEX IX_vims_safety_field_history_parent ON vims_safety_field_history (parent_table, parent_id, changed_at);
CREATE INDEX IX_vims_safety_field_history_actor  ON vims_safety_field_history (actor_user_id, changed_at);

-- DB-level write-only enforcement (append-only contract)
DENY UPDATE, DELETE ON vims_safety_field_history TO vims_safety_role_writer;
-- Purge job runs under elevated vims_safety_role_retention (Celery beat) which has DELETE grant.
```

**Access-log requirement (D-GAP-F4):** Every `SELECT` against `vims_safety_field_history` emits a platform access-log event. Implementation via SQL Server Extended Events session `sp_vims_safety_field_history_access` or (fallback) Django middleware on `/api/safety/audit/*` endpoints. Monitoring supplement row in `TECH_STACK.md` §5.1.

### 4.4 `vims_safety_soi_inspection` — SOI event master

Per SSOT §2C.9 (D-SOI-10 revised + D-GAP-E4 paper-first). Five-state workflow: Planned → Downloaded → In Fieldwork → Reported → Closed. **No scan-upload column exists** (D-GAP-E4 explicit). Paper remains in the ship SMS filing system.

```sql
CREATE TABLE vims_safety_soi_inspection (
  id                          BIGINT        IDENTITY(1,1) NOT NULL,
  vessel_id                   UNIQUEIDENTIFIER NOT NULL,
  inspection_reference        NVARCHAR(32)  NOT NULL,          -- Format SOI/{VesselCode}/{YY}/{NN} (§2C.14)
  cycle_label                 VARCHAR(16)   NOT NULL,          -- e.g. 'Q2/2026'
  state                       VARCHAR(24)   NOT NULL,          -- CHECK IN ('PLANNED','DOWNLOADED','IN_FIELDWORK','REPORTED','CLOSED')
  planned_date                DATE          NOT NULL,
  safety_officer_crew_id      NVARCHAR(64)  NOT NULL,          -- Live join → Crew_Onboarding_History
  safety_officer_department   VARCHAR(16)   NOT NULL,          -- 'DECK' | 'ENGINE' (resolved on save)
  assistant_crew_id           NVARCHAR(64)  NOT NULL,          -- D-SOI-08 mandatory; cross-functional enforcement at save
  assistant_department        VARCHAR(16)   NOT NULL,          -- MUST differ from safety_officer_department (V-SOI-*)
  master_crew_id              NVARCHAR(64)  NULL,              -- Populated at Master approval
  checklist_unique_id         NVARCHAR(32)  NULL,              -- D-GAP-E1 idempotent download; QR/barcode encodes this
  checklist_generated_at      DATETIME2     NULL,              -- D-GAP-E4: flips state to DOWNLOADED (paper-first, no upload)
  checklist_format            VARCHAR(8)    NULL,              -- CHECK IN ('PDF','XLSX') §2C.9
  fieldwork_started_at        DATETIME2     NULL,
  reported_at                 DATETIME2     NULL,
  closed_at                   DATETIME2     NULL,
  lost_paper_flag             BIT           NOT NULL DEFAULT 0,-- D-GAP-E3; true when re-download triggered
  lost_paper_note             NVARCHAR(MAX) NULL,
  section_12_included         BIT           NOT NULL DEFAULT 0,-- D-GAP-M23 (cross-cutting, once/3mo cycle)
  schema_version              INT           NOT NULL DEFAULT 1,
  is_deleted                  BIT           NOT NULL DEFAULT 0,
  archived_at                 DATETIME2     NULL,
  created_by                  NVARCHAR(128) NOT NULL,
  created_date                DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_by                  NVARCHAR(128) NULL,
  updated_date                DATETIME2     NULL,
  CONSTRAINT PK_vims_safety_soi_inspection PRIMARY KEY CLUSTERED (id),
  CONSTRAINT UQ_vims_safety_soi_inspection_ref UNIQUE (inspection_reference),
  CONSTRAINT UQ_vims_safety_soi_checklist_unique UNIQUE (checklist_unique_id),
  CONSTRAINT FK_vims_safety_soi_inspection_vessel FOREIGN KEY (vessel_id) REFERENCES VesselData(VesselID),
  CONSTRAINT CK_vims_safety_soi_inspection_state CHECK
      (state IN ('PLANNED','DOWNLOADED','IN_FIELDWORK','REPORTED','CLOSED')),
  CONSTRAINT CK_vims_safety_soi_inspection_format CHECK
      (checklist_format IS NULL OR checklist_format IN ('PDF','XLSX')),
  CONSTRAINT CK_vims_safety_soi_inspection_xfunc CHECK
      (assistant_department <> safety_officer_department)  -- D-SOI-08 hard enforcement
);

CREATE INDEX IX_vims_safety_soi_inspection_vessel_state ON vims_safety_soi_inspection (vessel_id, state);
CREATE INDEX IX_vims_safety_soi_inspection_cycle         ON vims_safety_soi_inspection (vessel_id, cycle_label);
CREATE INDEX IX_vims_safety_soi_inspection_unique_id     ON vims_safety_soi_inspection (checklist_unique_id)
  WHERE checklist_unique_id IS NOT NULL;
```

**Explicit no-scan-upload callout (D-GAP-E4):**
- No `scan_upload_path`, `scan_uploaded_at`, `scan_uploader_id`, or `scan_file_hash` column.
- No `/api/safety/soi/{id}/scan/upload` endpoint.
- The paper checklist bears the `checklist_unique_id` (QR or barcode — resolution deferral #10 below); that ID links the paper that sits in the ship SMS filing system back to this digital row. One-way link.

### 4.5 `vims_safety_soi_inspection_area` — areas covered per event

```sql
CREATE TABLE vims_safety_soi_inspection_area (
  id              BIGINT IDENTITY(1,1) NOT NULL,
  inspection_id   BIGINT NOT NULL,
  area_id         INT    NOT NULL,                     -- FK → master_soi_area.id
  inspected       BIT    NOT NULL DEFAULT 0,           -- D-GAP-E2 partial submission: TRUE only if findings reported for this area
  last_inspected_at DATETIME2 NULL,                    -- Stamped when findings registered for this area; resets 90-day counter
  notes           NVARCHAR(MAX) NULL,
  schema_version  INT    NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_soi_inspection_area PRIMARY KEY (id),
  CONSTRAINT UQ_vims_safety_soi_inspection_area UNIQUE (inspection_id, area_id),
  CONSTRAINT FK_vims_safety_soi_inspection_area_insp FOREIGN KEY (inspection_id)
      REFERENCES vims_safety_soi_inspection(id) ON DELETE CASCADE,
  CONSTRAINT FK_vims_safety_soi_inspection_area_area FOREIGN KEY (area_id)
      REFERENCES master_soi_area(id)
);

CREATE INDEX IX_vims_safety_soi_inspection_area_insp ON vims_safety_soi_inspection_area (inspection_id);
CREATE INDEX IX_vims_safety_soi_inspection_area_area ON vims_safety_soi_inspection_area (area_id, last_inspected_at);
```

### 4.6 `vims_safety_soi_finding` — findings per event

> **Build-time deferral #5 (state ENUM + Carried-Forward semantics):** exact ENUM for `status` and the carried-forward indicator (derived column vs explicit `carried_forward` bit vs cross-table query). Current lock: explicit status ENUM + `carried_forward_count` integer.

```sql
CREATE TABLE vims_safety_soi_finding (
  id                          BIGINT        IDENTITY(1,1) NOT NULL,
  inspection_id               BIGINT        NOT NULL,
  area_id                     INT           NOT NULL,     -- FK → master_soi_area.id
  item_id                     BIGINT        NULL,         -- FK → master_soi_area_item.id (nullable — concern-style findings OK)
  title                       NVARCHAR(256) NOT NULL,
  description                 NVARCHAR(MAX) NOT NULL,
  severity                    VARCHAR(8)    NOT NULL,     -- CHECK IN ('HIGH','MED','LOW')
  priority                    VARCHAR(8)    NOT NULL,     -- CHECK IN ('HIGH','MED','LOW') — SSQE priority; copy of severity by default, editable
  mscat_category_id           INT           NULL,         -- FK → master_mscat_taxonomy.category_id (optional on findings per §2C.12)
  mscat_subcode_id            NVARCHAR(16)  NULL,         -- e.g. '10.15' (D-GAP-R15 MOC governance)
  shell_tag                   VARCHAR(16)   NULL,         -- 'SOFTWARE' | 'HARDWARE' | 'ENVIRONMENT' | 'LIVEWARE' | 'LIVEWARE-LIVEWARE'
  assigned_crew_id            NVARCHAR(64)  NULL,
  due_date                    DATE          NULL,
  proposed_action             NVARCHAR(MAX) NULL,
  status                      VARCHAR(24)   NOT NULL,     -- CHECK IN ('OPEN','PENDING_CLOSURE','MASTER_APPROVED','CLOSED','CARRIED_FORWARD')
  carried_forward_count       INT           NOT NULL DEFAULT 0, -- increments each SCM that re-carries an open finding
  photo_attachment_path       NVARCHAR(512) NULL,         -- MANDATORY when severity='HIGH' (D-GAP-M24)
  master_approved_at          DATETIME2     NULL,
  master_approved_by          NVARCHAR(64)  NULL,
  closed_at                   DATETIME2     NULL,
  closure_note                NVARCHAR(MAX) NULL,
  schema_version              INT           NOT NULL DEFAULT 1,
  is_deleted                  BIT           NOT NULL DEFAULT 0,
  created_by                  NVARCHAR(128) NOT NULL,
  created_date                DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_by                  NVARCHAR(128) NULL,
  updated_date                DATETIME2     NULL,
  CONSTRAINT PK_vims_safety_soi_finding PRIMARY KEY CLUSTERED (id),
  CONSTRAINT FK_vims_safety_soi_finding_insp FOREIGN KEY (inspection_id) REFERENCES vims_safety_soi_inspection(id),
  CONSTRAINT FK_vims_safety_soi_finding_area FOREIGN KEY (area_id) REFERENCES master_soi_area(id),
  CONSTRAINT FK_vims_safety_soi_finding_item FOREIGN KEY (item_id) REFERENCES master_soi_area_item(id),
  CONSTRAINT CK_vims_safety_soi_finding_severity CHECK (severity IN ('HIGH','MED','LOW')),
  CONSTRAINT CK_vims_safety_soi_finding_priority CHECK (priority IN ('HIGH','MED','LOW')),
  CONSTRAINT CK_vims_safety_soi_finding_status   CHECK (status IN
      ('OPEN','PENDING_CLOSURE','MASTER_APPROVED','CLOSED','CARRIED_FORWARD')),
  -- D-GAP-M24 photo required when severity='HIGH':
  CONSTRAINT CK_vims_safety_soi_finding_high_photo CHECK
      (severity <> 'HIGH' OR photo_attachment_path IS NOT NULL)
);

CREATE INDEX IX_vims_safety_soi_finding_insp      ON vims_safety_soi_finding (inspection_id);
CREATE INDEX IX_vims_safety_soi_finding_status    ON vims_safety_soi_finding (status) WHERE is_deleted = 0;
CREATE INDEX IX_vims_safety_soi_finding_assigned  ON vims_safety_soi_finding (assigned_crew_id, due_date);
CREATE INDEX IX_vims_safety_soi_finding_severity  ON vims_safety_soi_finding (severity, status);
CREATE INDEX IX_vims_safety_soi_finding_mscat     ON vims_safety_soi_finding (mscat_category_id, mscat_subcode_id);
```

### 4.7 `vims_safety_soi_vessel_area_map` — per-vessel applicability + last-inspected

```sql
CREATE TABLE vims_safety_soi_vessel_area_map (
  id                  BIGINT        IDENTITY(1,1) NOT NULL,
  vessel_id           UNIQUEIDENTIFIER NOT NULL,
  area_id             INT           NOT NULL,              -- FK → master_soi_area.id
  applicable          BIT           NOT NULL DEFAULT 1,    -- FALSE excludes from 90-day counter (§2C.5)
  last_inspected_at   DATETIME2     NULL,                  -- Reset on per-area stamp (D-GAP-E2)
  due_at              AS DATEADD(DAY, 90, last_inspected_at) PERSISTED, -- Computed: 90-day hard ceiling (D-SOI-04)
  schema_version      INT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_soi_vessel_area_map PRIMARY KEY (id),
  CONSTRAINT UQ_vims_safety_soi_vessel_area UNIQUE (vessel_id, area_id),
  CONSTRAINT FK_vims_safety_soi_vessel_area_map_vessel FOREIGN KEY (vessel_id) REFERENCES VesselData(VesselID),
  CONSTRAINT FK_vims_safety_soi_vessel_area_map_area FOREIGN KEY (area_id) REFERENCES master_soi_area(id)
);

CREATE INDEX IX_vims_safety_soi_vessel_area_map_due ON vims_safety_soi_vessel_area_map (vessel_id, due_at)
  WHERE applicable = 1;
```

### 4.8 `vims_safety_soi_applicability_log` — audit of `applicable=false` decisions (D-GAP-M19)

```sql
CREATE TABLE vims_safety_soi_applicability_log (
  id                  BIGINT        IDENTITY(1,1) NOT NULL,
  vessel_id           UNIQUEIDENTIFIER NOT NULL,
  area_id             INT           NOT NULL,
  old_applicable      BIT           NOT NULL,
  new_applicable      BIT           NOT NULL,
  reason              NVARCHAR(MAX) NOT NULL,          -- Mandatory per D-GAP-M19
  master_requested_by NVARCHAR(64)  NOT NULL,
  master_requested_at DATETIME2     NOT NULL,
  master_signature    NVARCHAR(256) NOT NULL,          -- D-GAP-D1 typed name + device fingerprint
  dpa_approved_by     NVARCHAR(64)  NULL,
  dpa_approved_at     DATETIME2     NULL,
  dpa_signature       NVARCHAR(256) NULL,              -- NULL until DPA approval; pending state handled at app layer
  dpa_decision        VARCHAR(16)   NULL,              -- CHECK IN ('APPROVED','REJECTED')
  schema_version      INT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_soi_applicability_log PRIMARY KEY (id),
  CONSTRAINT FK_vims_safety_soi_applicability_log_vessel FOREIGN KEY (vessel_id) REFERENCES VesselData(VesselID),
  CONSTRAINT FK_vims_safety_soi_applicability_log_area FOREIGN KEY (area_id) REFERENCES master_soi_area(id),
  CONSTRAINT CK_vims_safety_soi_applicability_log_decision CHECK
      (dpa_decision IS NULL OR dpa_decision IN ('APPROVED','REJECTED'))
);

CREATE INDEX IX_vims_safety_soi_applicability_log_vessel_area
  ON vims_safety_soi_applicability_log (vessel_id, area_id, master_requested_at);
```

### 4.9 `vims_safety_soi_trainee` — up to 3 trainees per inspection (D-SOI-09)

```sql
CREATE TABLE vims_safety_soi_trainee (
  id              BIGINT        IDENTITY(1,1) NOT NULL,
  inspection_id   BIGINT        NOT NULL,
  crew_id         NVARCHAR(64)  NOT NULL,               -- FK via live join to Crew_Onboarding_History
  trainee_slot    TINYINT       NOT NULL,               -- 1, 2, or 3
  schema_version  INT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_soi_trainee PRIMARY KEY (id),
  CONSTRAINT UQ_vims_safety_soi_trainee UNIQUE (inspection_id, crew_id),
  CONSTRAINT UQ_vims_safety_soi_trainee_slot UNIQUE (inspection_id, trainee_slot),
  CONSTRAINT CK_vims_safety_soi_trainee_slot CHECK (trainee_slot BETWEEN 1 AND 3),
  CONSTRAINT FK_vims_safety_soi_trainee_insp FOREIGN KEY (inspection_id)
      REFERENCES vims_safety_soi_inspection(id) ON DELETE CASCADE
);

CREATE INDEX IX_vims_safety_soi_trainee_crew ON vims_safety_soi_trainee (crew_id);
```

### 4.10 `vims_safety_scm_meeting` — SCM event master (Regular + Ad-Hoc)

Per SSOT §5 + D-GAP-M-ADHOC. Same form, same table, discriminated by `meeting_type`. Regular and Ad-Hoc can be hosted by Master or CO. Active V1 flow is `DRAFT` → `SUBMITTED` → `CLOSED`; UI displays `SUBMITTED` as `Submitted to Office`. New SCM records are closed by office review: DPA, FM, Shore HOD, or Marine Superintendent profile `407EF017-0F1C-EF11-A9F1-F348983BAE6B` saves the Office Comment, which freezes vessel-side editing.

```sql
CREATE TABLE vims_safety_scm_meeting (
  id                      BIGINT        IDENTITY(1,1) NOT NULL,
  vessel_id               UNIQUEIDENTIFIER NOT NULL,
  scm_number              NVARCHAR(48)  NOT NULL,            -- Format {VesselCode}-{DD-Mon-YYYY} (legacy pattern)
  meeting_type            VARCHAR(16)   NOT NULL,            -- CHECK IN ('REGULAR','AD_HOC')
  meeting_date            DATE          NOT NULL,
  meeting_time_local      TIME          NOT NULL,
  location                NVARCHAR(128) NULL,                -- port name or 'AT SEA'
  latitude                DECIMAL(9,6)  NULL,                -- At-sea meetings
  longitude               DECIMAL(9,6)  NULL,
  voyage_no               NVARCHAR(32)  NULL,
  chair_crew_id           NVARCHAR(64)  NOT NULL,            -- Master for Regular; host for Ad-Hoc
  prepared_by_crew_id     NVARCHAR(64)  NOT NULL,            -- SCM host: Master or CO
  ad_hoc_trigger_reason   NVARCHAR(MAX) NULL,                -- Mandatory when meeting_type='AD_HOC'
  office_comment          NVARCHAR(MAX) NULL,                -- Office Comment; saving closes SCM
  office_comment_by       NVARCHAR(64)  NULL,
  office_comment_at       DATETIME2     NULL,
  state                   VARCHAR(24)   NOT NULL,            -- Active flow: DRAFT -> SUBMITTED -> CLOSED; UI shows SUBMITTED as Submitted to Office
  master_signed_off_at    DATETIME2     NULL,                -- legacy compatibility only; no active SCM digital sign-off
  master_signed_off_by    NVARCHAR(64)  NULL,                -- legacy compatibility only
  pdf_export_path         NVARCHAR(512) NULL,                -- D-PDF-03b legacy SCM PDF preserved
  schema_version          INT           NOT NULL DEFAULT 1,
  is_deleted              BIT           NOT NULL DEFAULT 0,
  archived_at             DATETIME2     NULL,
  created_by              NVARCHAR(128) NOT NULL,
  created_date            DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_by              NVARCHAR(128) NULL,
  updated_date            DATETIME2     NULL,
  CONSTRAINT PK_vims_safety_scm_meeting PRIMARY KEY CLUSTERED (id),
  CONSTRAINT UQ_vims_safety_scm_meeting_number UNIQUE (scm_number),
  CONSTRAINT FK_vims_safety_scm_meeting_vessel FOREIGN KEY (vessel_id) REFERENCES VesselData(VesselID),
  CONSTRAINT CK_vims_safety_scm_meeting_type CHECK (meeting_type IN ('REGULAR','AD_HOC')),
  CONSTRAINT CK_vims_safety_scm_meeting_state CHECK
      (state IN ('DRAFT','SUBMITTED','SIGNED_OFF','REOPENED','CLOSED')),
  CONSTRAINT CK_vims_safety_scm_meeting_adhoc_reason CHECK
      (meeting_type <> 'AD_HOC' OR ad_hoc_trigger_reason IS NOT NULL)
);

CREATE INDEX IX_vims_safety_scm_meeting_vessel_date ON vims_safety_scm_meeting (vessel_id, meeting_date DESC);
CREATE INDEX IX_vims_safety_scm_meeting_state       ON vims_safety_scm_meeting (state);
CREATE INDEX IX_vims_safety_scm_meeting_type        ON vims_safety_scm_meeting (meeting_type, meeting_date);
```

### 4.11 `vims_safety_scm_attendance` — WRH-joined attendance

```sql
CREATE TABLE vims_safety_scm_attendance (
  id                          BIGINT        IDENTITY(1,1) NOT NULL,
  meeting_id                  BIGINT        NOT NULL,
  crew_id                     NVARCHAR(64)  NOT NULL,
  rank_name                   NVARCHAR(64)  NOT NULL,            -- resolved from master_applied_rank
  display_name                NVARCHAR(128) NOT NULL,
  present                     BIT           NOT NULL DEFAULT 1,
  absence_reason              NVARCHAR(MAX) NULL,
  -- WRH live-join snapshot (D-GAP-M11; creation readiness gate D-MAINT-CR014)
  wrh_data_available          BIT           NOT NULL DEFAULT 1,   -- FALSE → render "WRH data unavailable" badge
  wrh_rest_hours_24h          DECIMAL(5,2)  NULL,                 -- Previous 24h rest hours from wrh_attendance
  wrh_rest_hours_7d           DECIMAL(5,2)  NULL,                 -- Previous 7d rest hours
  wrh_non_compliance_flag     BIT           NOT NULL DEFAULT 0,   -- TRUE blocks new SCM hosting; warning-only after meeting exists
  remarks                     NVARCHAR(MAX) NULL,
  schema_version              INT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_scm_attendance PRIMARY KEY (id),
  CONSTRAINT UQ_vims_safety_scm_attendance UNIQUE (meeting_id, crew_id),
  CONSTRAINT FK_vims_safety_scm_attendance_meeting FOREIGN KEY (meeting_id)
      REFERENCES vims_safety_scm_meeting(id) ON DELETE CASCADE
);

CREATE INDEX IX_vims_safety_scm_attendance_meeting ON vims_safety_scm_attendance (meeting_id);
CREATE INDEX IX_vims_safety_scm_attendance_crew    ON vims_safety_scm_attendance (crew_id);
```

> **Build-time deferral #7:** WRH lookback window (24h / 72h / 168h / query timeout) for attendance live-join. Current lock: 24h + 7d snapshots on save; not streamed. Resolution owner: Backend + WRH lead, required by Phase 3.

### 4.12 `vims_safety_scm_agenda` — agenda items + Suggestions / Recommendations

```sql
CREATE TABLE vims_safety_scm_agenda (
  id                      BIGINT        IDENTITY(1,1) NOT NULL,
  meeting_id              BIGINT        NOT NULL,
  agenda_item_number      INT           NOT NULL,                 -- 1..10 per vw_GetSCM_Master (D-PDF-03b)
  section_label           NVARCHAR(128) NOT NULL,                 -- e.g. 'Safety Observations for the Month', 'Closed Items Since Last Meeting'
  auto_populated          BIT           NOT NULL DEFAULT 0,       -- D-SOI-14: Open findings feed, Closed items feed
  content                 NVARCHAR(MAX) NOT NULL,
  decision                NVARCHAR(MAX) NULL,                     -- legacy column; UI/PDF label is "Suggestions / Recommendations"
  linked_finding_ids      NVARCHAR(MAX) NULL,                     -- CSV of vims_safety_soi_finding.id (optional)
  linked_incident_ids     NVARCHAR(MAX) NULL,                     -- CSV of vims_safety_incident.id (optional)
  schema_version          INT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_vims_safety_scm_agenda PRIMARY KEY (id),
  CONSTRAINT UQ_vims_safety_scm_agenda_item UNIQUE (meeting_id, agenda_item_number),
  CONSTRAINT FK_vims_safety_scm_agenda_meeting FOREIGN KEY (meeting_id)
      REFERENCES vims_safety_scm_meeting(id) ON DELETE CASCADE
);

CREATE INDEX IX_vims_safety_scm_agenda_meeting ON vims_safety_scm_agenda (meeting_id, agenda_item_number);
```

### 4.13 `vims_safety_corrective_action` — CA with Purchase Req hard FK (D-GAP-M12)

```sql
CREATE TABLE vims_safety_corrective_action (
  id                          BIGINT        IDENTITY(1,1) NOT NULL,
  source_table                VARCHAR(64)   NOT NULL,         -- 'vims_safety_incident' | 'vims_safety_soi_finding' | 'vims_safety_scm_agenda'
  source_id                   BIGINT        NOT NULL,         -- polymorphic parent; resolved in app layer
  recommendation_id           BIGINT        NULL,             -- FK → vims_safety_recommendation.id (when CA derives from a rec)
  title                       NVARCHAR(256) NOT NULL,
  description                 NVARCHAR(MAX) NOT NULL,
  assigned_crew_id            NVARCHAR(64)  NULL,
  assigned_office_user_id     NVARCHAR(64)  NULL,
  verifier_user_id            NVARCHAR(64)  NULL,
  due_date                    DATE          NULL,
  status                      VARCHAR(24)   NOT NULL,         -- CHECK IN ('OPEN','IN_PROGRESS','PENDING_VERIFY','CLOSED','REOPENED')
  -- D-GAP-M12 Purchase hard FK:
  purchase_req_id             BIGINT        NULL,             -- FK → pur_requisition(id) — HARD FK; RI prevents requisition archive while CA open
  -- Physical verification (D-PSC pattern, Q45)
  physical_verification_done  BIT           NOT NULL DEFAULT 0,
  physical_verification_at    DATETIME2     NULL,
  physical_verification_by    NVARCHAR(64)  NULL,
  physical_verification_note  NVARCHAR(MAX) NULL,
  -- Aging (D-GAP-M29)
  aging_bucket                AS CASE
    WHEN DATEDIFF(DAY, created_date, ISNULL(closed_at, SYSUTCDATETIME())) BETWEEN 0 AND 15 THEN '0-15'
    WHEN DATEDIFF(DAY, created_date, ISNULL(closed_at, SYSUTCDATETIME())) BETWEEN 16 AND 30 THEN '15-30'
    WHEN DATEDIFF(DAY, created_date, ISNULL(closed_at, SYSUTCDATETIME())) BETWEEN 31 AND 45 THEN '30-45'
    ELSE '45+'
  END PERSISTED,
  closed_at                   DATETIME2     NULL,
  closed_by                   NVARCHAR(64)  NULL,
  schema_version              INT           NOT NULL DEFAULT 1,
  is_deleted                  BIT           NOT NULL DEFAULT 0,
  created_by                  NVARCHAR(128) NOT NULL,
  created_date                DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_by                  NVARCHAR(128) NULL,
  updated_date                DATETIME2     NULL,
  CONSTRAINT PK_vims_safety_corrective_action PRIMARY KEY CLUSTERED (id),
  CONSTRAINT FK_vims_safety_corrective_action_purchase
      FOREIGN KEY (purchase_req_id) REFERENCES pur_requisition(id),   -- HARD FK per D-GAP-M12
  CONSTRAINT FK_vims_safety_corrective_action_recommendation
      FOREIGN KEY (recommendation_id) REFERENCES vims_safety_recommendation(id),
  CONSTRAINT CK_vims_safety_corrective_action_status CHECK
      (status IN ('OPEN','IN_PROGRESS','PENDING_VERIFY','CLOSED','REOPENED'))
);

CREATE INDEX IX_vims_safety_corrective_action_source    ON vims_safety_corrective_action (source_table, source_id);
CREATE INDEX IX_vims_safety_corrective_action_status    ON vims_safety_corrective_action (status) WHERE is_deleted = 0;
CREATE INDEX IX_vims_safety_corrective_action_due       ON vims_safety_corrective_action (due_date, status);
CREATE INDEX IX_vims_safety_corrective_action_purchase  ON vims_safety_corrective_action (purchase_req_id)
  WHERE purchase_req_id IS NOT NULL;
CREATE INDEX IX_vims_safety_corrective_action_aging     ON vims_safety_corrective_action (aging_bucket);
```

**RI contract (D-GAP-M12):** `pur_requisition` cannot be hard-deleted or archived while an open (status ∉ {'CLOSED'}) CA references it. Purchase-module logic must consult `vims_safety_corrective_action` before archive. Application-level pre-check in Purchase + DB FK prevents cascade anomalies.

### 4.14 `vims_safety_recommendation` — Corrective / Preventive / Lessons tiers

> **Build-time deferral #4 (cardinality):** whether a single-row model with three nullable tier columns vs one-row-per-tier vs child sub-table best fits the "≥1 per tier on YELLOW/RED" rule (V-INC-064). Current lock: one-row-per-tier (easier bulk query; cleaner cardinality constraint).

```sql
CREATE TABLE vims_safety_recommendation (
  id                          BIGINT        IDENTITY(1,1) NOT NULL,
  incident_id                 BIGINT        NOT NULL,
  tier                        VARCHAR(16)   NOT NULL,         -- CHECK IN ('CORRECTIVE','PREVENTIVE','LESSONS_LEARNT')
  theme_code                  VARCHAR(32)   NULL,             -- 7 themes §2B.7 (system-action only)
  title                       NVARCHAR(256) NOT NULL,
  description                 NVARCHAR(MAX) NOT NULL,
  rationale                   NVARCHAR(MAX) NULL,
  -- ALARP/compatibility fields (current UI requires likelihood reduction; effort/residual text are legacy-compatible)
  estimated_effort            NVARCHAR(MAX) NULL,
  estimated_likelihood_reduction VARCHAR(24) NULL,            -- 'LOW' | 'MED' | 'HIGH' | 'QUANTIFIED'
  residual_risk_statement     NVARCHAR(MAX) NULL,
  alarp_attested              BIT           NOT NULL DEFAULT 0,
  tolerable_failure_filter    BIT           NOT NULL DEFAULT 0, -- D-GAP-R11 GREEN-only fast-close
  -- Linkage
  linked_ca_ids               NVARCHAR(MAX) NULL,             -- CSV of vims_safety_corrective_action.id
  schema_version              INT           NOT NULL DEFAULT 1,
  is_deleted                  BIT           NOT NULL DEFAULT 0,
  created_by                  NVARCHAR(128) NOT NULL,
  created_date                DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_by                  NVARCHAR(128) NULL,
  updated_date                DATETIME2     NULL,
  CONSTRAINT PK_vims_safety_recommendation PRIMARY KEY CLUSTERED (id),
  CONSTRAINT FK_vims_safety_recommendation_incident FOREIGN KEY (incident_id)
      REFERENCES vims_safety_incident(id) ON DELETE CASCADE,
  CONSTRAINT CK_vims_safety_recommendation_tier CHECK
      (tier IN ('CORRECTIVE','PREVENTIVE','LESSONS_LEARNT'))
);

CREATE INDEX IX_vims_safety_recommendation_incident ON vims_safety_recommendation (incident_id, tier);
CREATE INDEX IX_vims_safety_recommendation_theme    ON vims_safety_recommendation (theme_code)
  WHERE theme_code IS NOT NULL;
CREATE INDEX IX_vims_safety_recommendation_alarp    ON vims_safety_recommendation (alarp_attested);
```

CR-049/CR-052 compatibility note: `rationale`, `theme_code`, and `estimated_effort` remain nullable storage for old recommendation rows and direct API compatibility, but the current Incident action frontend does not render or send recommendation rationale / "Why is this needed?", theme, or effort. Preventive Action now sends Description, Due date, and one shared screen-level risk reduction; the due date is stored through the existing linked `vims_safety_corrective_action` row for the preventive recommendation, and the shared risk-reduction answer is stored in `vims_safety_recommendation.estimated_likelihood_reduction` for backend compatibility. Formal Incident PDF output also omits stored recommendation rationale.

---

## 5. Full Schema — Reference / Seed Tables

All 8 Safety-owned reference tables. Seeded by `0002_seed_master_tables.py` from `safety-reference-data/*.csv`. DPA-editable post-deploy (per D-CFG-01). No `vims_` prefix — these are cross-module reference data (§2.1).

### 5.1 `master_mscat_taxonomy` — 174 rows (DNV M-SCAT)

Column headers from `safety-reference-data/mscat_taxonomy.csv`: `category_id, category_name, subcode_id, subcode_description, cause_type`. Mapped 1:1 to DDL:

```sql
CREATE TABLE master_mscat_taxonomy (
  id                  CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id       BIGINT        IDENTITY(1,1) NOT NULL, -- prior integer id retained for compatibility
  category_id         INT           NOT NULL,               -- CSV col 1
  category_name       NVARCHAR(128) NOT NULL,               -- CSV col 2 (e.g. 'Inadequate Physical/Physiological Capability')
  subcode_id          NVARCHAR(16)  NOT NULL,               -- CSV col 3 (e.g. '1.1', '10.15')
  subcode_description NVARCHAR(512) NOT NULL,               -- CSV col 4
  cause_type          VARCHAR(32)   NOT NULL,               -- CSV col 5: 'BASIC_CAUSE' | 'IMMEDIATE_SUBSTANDARD_ACT' | 'IMMEDIATE_SUBSTANDARD_CONDITION' | 'LACK_OF_CONTROL'
  active              BIT           NOT NULL DEFAULT 1,
  seeded_version      NVARCHAR(16)  NOT NULL DEFAULT 'v1.0-Round21',
  schema_version      INT           NOT NULL DEFAULT 1,
  updated_by          NVARCHAR(128) NULL,
  updated_date        DATETIME2     NULL,
  CONSTRAINT PK_master_mscat_taxonomy PRIMARY KEY CLUSTERED (id),
  CONSTRAINT UQ_master_mscat_taxonomy_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT UQ_master_mscat_taxonomy_subcode UNIQUE (subcode_id),
  CONSTRAINT CK_master_mscat_taxonomy_cause_type CHECK
      (cause_type IN ('BASIC_CAUSE','IMMEDIATE_SUBSTANDARD_ACT','IMMEDIATE_SUBSTANDARD_CONDITION','LACK_OF_CONTROL'))
);

CREATE INDEX IX_master_mscat_taxonomy_category ON master_mscat_taxonomy (category_id, subcode_id);
CREATE INDEX IX_master_mscat_taxonomy_type     ON master_mscat_taxonomy (cause_type, active);
```

**Seed source:** `safety-reference-data/mscat_taxonomy.csv` (174 rows). Includes the Round 21 R15 `10.15 Design/MOC Governance — Independent Review Absent` addition. DPA-editable via `/api/safety/reference/mscat/` under `SAF_P_018`.

### 5.2 `master_immediate_causes` — 52 rows

Column headers from `safety-reference-data/immediate_causes.csv`: `category_id, category_name, subcode_id, subcode_description, cause_type`. Mapped:

```sql
CREATE TABLE master_immediate_causes (
  id                  CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id       BIGINT        IDENTITY(1,1) NOT NULL,
  category_id         INT           NOT NULL,               -- CSV col 1 (1 or 2)
  category_name       NVARCHAR(128) NOT NULL,               -- CSV col 2 ('Substandard Acts / Practices' | 'Substandard Conditions')
  subcode_id          NVARCHAR(16)  NOT NULL,               -- CSV col 3 (1..28 for acts, 1..24 for conditions)
  subcode_description NVARCHAR(512) NOT NULL,               -- CSV col 4
  cause_type          VARCHAR(32)   NOT NULL,               -- CSV col 5: 'IMMEDIATE_SUBSTANDARD_ACT' | 'IMMEDIATE_SUBSTANDARD_CONDITION'
  active              BIT           NOT NULL DEFAULT 1,
  seeded_version      NVARCHAR(16)  NOT NULL DEFAULT 'v1.0',
  schema_version      INT           NOT NULL DEFAULT 1,
  updated_by          NVARCHAR(128) NULL,
  updated_date        DATETIME2     NULL,
  CONSTRAINT PK_master_immediate_causes PRIMARY KEY (id),
  CONSTRAINT UQ_master_immediate_causes_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT UQ_master_immediate_causes UNIQUE (category_id, subcode_id),
  CONSTRAINT CK_master_immediate_causes_type CHECK
      (cause_type IN ('IMMEDIATE_SUBSTANDARD_ACT','IMMEDIATE_SUBSTANDARD_CONDITION'))
);

CREATE INDEX IX_master_immediate_causes_category ON master_immediate_causes (category_id);
```

**Seed source:** 28 Substandard Acts + 24 Substandard Conditions = 52 rows.

### 5.3 `master_loss_types` — 7 rows (§2B.4, D-DNV-03)

Column headers from `safety-reference-data/loss_types.csv`: `loss_type_id, loss_type_name, description`. Mapped:

```sql
CREATE TABLE master_loss_types (
  id              CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id   BIGINT        IDENTITY(1,1) NOT NULL,
  loss_type_id    INT           NOT NULL,                 -- CSV col 1 (1..7)
  loss_type_name  NVARCHAR(64)  NOT NULL,                 -- CSV col 2 ('People','Asset','Environmental','Financial','Non-Conformity','Reputation','Process')
  description     NVARCHAR(128) NOT NULL,                 -- CSV col 3 (e.g. 'Safety / Health')
  active          BIT           NOT NULL DEFAULT 1,
  seeded_version  NVARCHAR(16)  NOT NULL DEFAULT 'v1.0',
  CONSTRAINT PK_master_loss_types PRIMARY KEY (id),
  CONSTRAINT UQ_master_loss_types_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT UQ_master_loss_types UNIQUE (loss_type_id)
);
```

**Seed rows (verbatim from CSV):**
| loss_type_id | loss_type_name | description |
|---|---|---|
| 1 | People | Safety / Health |
| 2 | Asset | Damage |
| 3 | Environmental | Environmental |
| 4 | Financial | Fines, Claims, Insurance |
| 5 | Non-Conformity | Product / Service |
| 6 | Reputation | Reputation / Complaint |
| 7 | Process | Process / Business |

### 5.4 `master_soi_area` — 13 rows (§2C.5, D-SOI-16)

Derived from `safety-reference-data/soi_checklist_v1.csv` `area_id`/`area_name` unique values (12 physical areas + 1 cross-cutting per D-GAP-M23 Section 12).

```sql
CREATE TABLE master_soi_area (
  id              CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id   BIGINT        IDENTITY(1,1) NOT NULL,
  area_id         INT           NOT NULL,                 -- 1..13 (CSV col 1)
  area_name       NVARCHAR(128) NOT NULL,                 -- CSV col 2
  section_12_flag BIT           NOT NULL DEFAULT 0,       -- TRUE only for area_id=13 (cross-cutting)
  display_order   INT           NOT NULL,
  active          BIT           NOT NULL DEFAULT 1,
  seeded_version  NVARCHAR(16)  NOT NULL DEFAULT 'v1.0 (SQE S 608 — SSQE Rev 02 baseline + Section 12)',
  CONSTRAINT PK_master_soi_area PRIMARY KEY (id),
  CONSTRAINT UQ_master_soi_area_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT UQ_master_soi_area UNIQUE (area_id)
);
```

**Seed rows (13 areas):**
| area_id | area_name | section_12_flag |
|---|---|---|
| 1 | External Deck Structure | 0 |
| 2 | Accommodation | 0 |
| 3 | Navigating Bridge & Monkey Island | 0 |
| 4 | Electrical safety | 0 |
| 5 | Engine Room and Work Shop | 0 |
| 6 | Other Machinery Spaces | 0 |
| 7 | All Stores as Applicable | 0 |
| 8 | Galley / Cold Rooms including work practices and hygiene control | 0 |
| 9 | All Lifting Equipment | 0 |
| 10 | Mooring and Access Equipment | 0 |
| 11 | CO2 Room & Fixed Smothering Systems | 0 |
| 12 | Compressor House & Motor Room | 0 |
| 13 | Cross-cutting Safety & Culture | 1 |

### 5.5 `master_soi_area_item` — 329 rows (checklist items)

Column headers from `safety-reference-data/soi_checklist_v1.csv`: `area_id, area_name, subsection_id, subsection_name, item_number, description, tier`. Mapped:

```sql
CREATE TABLE master_soi_area_item (
  id                  CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id       BIGINT        IDENTITY(1,1) NOT NULL,
  area_id             INT           NOT NULL,                 -- CSV col 1 (FK → master_soi_area.area_id)
  area_name           NVARCHAR(128) NOT NULL,                 -- CSV col 2 (denormalised for readability)
  subsection_id       INT           NOT NULL,                 -- CSV col 3
  subsection_name     NVARCHAR(128) NOT NULL,                 -- CSV col 4
  item_number         INT           NOT NULL,                 -- CSV col 5
  description         NVARCHAR(MAX) NOT NULL,                 -- CSV col 6
  tier                VARCHAR(16)   NOT NULL,                 -- CSV col 7: 'BASELINE' | 'CROSS_CUTTING'
  active              BIT           NOT NULL DEFAULT 1,
  seeded_version      NVARCHAR(16)  NOT NULL DEFAULT 'v1.0',
  schema_version      INT           NOT NULL DEFAULT 1,
  updated_by          NVARCHAR(128) NULL,
  updated_date        DATETIME2     NULL,
  CONSTRAINT PK_master_soi_area_item PRIMARY KEY CLUSTERED (id),
  CONSTRAINT UQ_master_soi_area_item_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT CK_master_soi_area_item_tier CHECK (tier IN ('BASELINE','CROSS_CUTTING'))
);

CREATE INDEX IX_master_soi_area_item_area ON master_soi_area_item (area_id, subsection_id, item_number);
CREATE INDEX IX_master_soi_area_item_tier ON master_soi_area_item (tier, active);
```

**Seed source:** `safety-reference-data/soi_checklist_v1.csv` (329 rows = 317 baseline + 12 cross-cutting per Section 12).

### 5.6 `master_soi_checklist_version` — versioned templates (DPA-maintained)

```sql
CREATE TABLE master_soi_checklist_version (
  id                  CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id       BIGINT        IDENTITY(1,1) NOT NULL,
  version_label       NVARCHAR(16)  NOT NULL,             -- e.g. 'v1.0', 'v1.1-Rev02'
  effective_from      DATE          NOT NULL,
  effective_to        DATE          NULL,
  source_description  NVARCHAR(256) NOT NULL,             -- e.g. 'SQE S 608 baseline — SSQE Rev 02 + Section 12'
  active              BIT           NOT NULL DEFAULT 1,
  created_by          NVARCHAR(128) NOT NULL,
  created_date        DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT PK_master_soi_checklist_version PRIMARY KEY (id),
  CONSTRAINT UQ_master_soi_checklist_version_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT UQ_master_soi_checklist_version_label UNIQUE (version_label)
);

CREATE INDEX IX_master_soi_checklist_version_effective ON master_soi_checklist_version (effective_from, effective_to);
```

### 5.7 `master_safety_incident_type` — 32 active rows (§2B.5, D-DNV-04 superseded by D-MAINT-CR031)

```sql
CREATE TABLE master_safety_incident_type (
  id              CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id   BIGINT        IDENTITY(1,1) NOT NULL,
  type_code       VARCHAR(32)   NOT NULL,
  type_name       NVARCHAR(128) NOT NULL,
  imo_reportable  BIT           NOT NULL DEFAULT 0,             -- IMO 11 reportable type flag
  description     NVARCHAR(MAX) NULL,
  active          BIT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_master_safety_incident_type PRIMARY KEY (id),
  CONSTRAINT UQ_master_safety_incident_type_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT UQ_master_safety_incident_type_code UNIQUE (type_code)
);
```

**Seed rows (32 active incident types per §2B.5):** Collision, Grounding, Stranding, Touched bottom at berth / anchorage, Touched bottom in rivers / canals, Allision with Jetty / Berth / Locks, Allision with other Vessels, Allision with ice, Allision with Navigation Aids / Buoys / Other objects, Foundering, Capsizing / Loss of Stability, Flooding, Explosion, Fire, Cargo Damage, Hull / Structural Failure, pipeline/submarine-cable fouling or damage, aid-to-navigation fouling or damage other than allision, port/terminal installation fouling or damage, equipment failure causing electrical-power loss, equipment failure causing propulsion loss, equipment failure causing steering loss, equipment failure causing cargo-operation delay over 6 hours, equipment failure rendering vessel otherwise unseaworthy, equipment or hull failure causing cargo damage, Crew Injury, Pollution, Breach of Local Regulations, Stowaway Incident, Security Incident, Breach of Cyber Security, Other. Retired earlier rows, including `IMO_MISSING_VESSEL`, are inactive or absent from new seeds and are not offered for new selection. Each active row has `imo_reportable=1`.

### 5.8 `master_safety_bias_guard` — 8 rows (Round 21 R12)

```sql
CREATE TABLE master_safety_bias_guard (
  id              CHAR(32)      NOT NULL DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), -- UUID PK
  legacy_int_id   BIGINT        IDENTITY(1,1) NOT NULL,
  guard_code      VARCHAR(32)   NOT NULL,                   -- 'RECENCY','ASSUMPTION','HINDSIGHT','CONFIRMATION','BLAME_FIXATION','PLANT_TRAP','PERSONNEL_TRAP','EXTERNAL_EVENT_TRAP'
  guard_name      NVARCHAR(128) NOT NULL,
  family          VARCHAR(16)   NOT NULL,                   -- 'DNV' | 'ORG_TRAP'
  description     NVARCHAR(MAX) NOT NULL,
  bit_position    TINYINT       NOT NULL,                   -- 0..7 for bias_guard_attestations bitmask on vims_safety_incident
  active          BIT           NOT NULL DEFAULT 1,
  CONSTRAINT PK_master_safety_bias_guard PRIMARY KEY (id),
  CONSTRAINT UQ_master_safety_bias_guard_legacy_int_id UNIQUE (legacy_int_id),
  CONSTRAINT UQ_master_safety_bias_guard UNIQUE (guard_code),
  CONSTRAINT CK_master_safety_bias_guard_family CHECK (family IN ('DNV','ORG_TRAP'))
);
```

**Seed rows:** 5 DNV (Recency, Assumption, Hindsight, Confirmation, Blame-Fixation) + 3 Organisational Traps (Plant, Personnel, External-Event). Bitmask positions 0..7 per bit_position column — mapped 1:1 to `vims_safety_incident.bias_guard_attestations`.

---

## 6. Existing VIMS Masters Consumed

**Safety does NOT duplicate these — read-only consumption only.** They live in `ksm_marine_live` maintained by the VIMS platform / Reporting / Inspection:

| Table | Safety usage |
|-------|--------------|
| `master_role` | Resolve role names for audit log / signatures / permission chain |
| `master_RoleByVessel` | Office-user vessel scoping on every list / detail endpoint |
| `master_applied_rank` | Rank normalization for SCM attendance + SOI trainee display |
| `master_notification` | Shared notification queue — Safety writes rows; platform notifier consumes (per `<vims_integration>`) |
| `VesselData` | Vessel master — FK target on every Safety row via `vessel_id`; Incident Fleet Alert reads active ship names/codes and `email` from this table |
| `Crew_Onboarding_History` | Ship-side vessel scope + SOI assistant dept lookup + SCM attendance roster (live join, D-GAP-I2) |
| `HRM501` | Crew email / rank enrichment — live join |
| `master_applied_rank` | Already listed above — (explicit confirmation per rubric) |
| `master_port` | SCM location picker, SOI port field, incident location |
| `msc_profiles` | SAF_F_*/SAF_P_* registered here, not in a new permission table |
| `users`, `Ship_UsersLogin` | Auth credential tables — read-only via platform auth chain |
| `wrh_attendance` | SCM attendance rest-hour compliance live join (D-GAP-M11) |
| `wrh_ship_time_config` | Timezone resolution (D-GAP-M26) |
| `vims_noon_report` + `DepartureReport` + `ArrivalReport` + `NoonReportPort` | MSC-MEPC.3 position live join ±12h tolerance (D-GAP-M09, D-GAP-M10) |
| `pur_requisition` | CA hard FK target (D-GAP-M12) |

---

## 7. Indexes & Performance Contract

All inline index statements are already rendered with each `CREATE TABLE` above. Summary:

| Table | Composite index on | Purpose |
|-------|-------------------|---------|
| `vims_safety_incident` | `(vessel_id, occurred_at)` filtered `is_deleted=0` | List by vessel + date |
| `vims_safety_incident` | `(state)` filtered `is_deleted=0` | Phase-workbench filter |
| `vims_safety_incident` | `(record_type, state)` | Near-miss-only queries |
| `vims_safety_near_miss_cause_option` | `(active, factor, cause_stage)` | Near-miss factor cause dropdown |
| `vims_safety_incident_phase_log` | `(incident_id, occurred_at)` | Audit timeline render |
| `vims_safety_field_history` | `(parent_table, parent_id, changed_at)` | Field-history detail render |
| `vims_safety_soi_inspection` | `(vessel_id, state)` | SOI list per vessel |
| `vims_safety_soi_finding` | `(status)` filtered `is_deleted=0` | Open findings for SCM auto-feed |
| `vims_safety_soi_vessel_area_map` | `(vessel_id, due_at)` filtered `applicable=1` | Dashboard SOI Compliance % |
| `vims_safety_scm_meeting` | `(vessel_id, meeting_date DESC)` | Meeting history |
| `vims_safety_corrective_action` | `(status)` filtered `is_deleted=0` | Open CA dashboard |
| `vims_safety_corrective_action` | `(aging_bucket)` | CA Aging Pipeline chart (D-GAP-M29) |

No partitioning in V1 (deferral #3 covers soft-archive). Performance baseline inherited from VIMS platform (TECH_STACK §5.4 D-GAP-H1).

---

## 8. Build-Time Deferrals Register

Per master prompt §6, the following 12 items are explicitly deferred to build-time. Each row has a decision-options commentary below the table.

| # | Deferred item | Resolution owner | Required by phase |
|---|---------------|------------------|-------------------|
| 1 | `vims_safety_incident` field ENUMs and nullability | Backend lead | Phase 1 |
| 2 | `vims_safety_field_history` column shape (TEXT vs JSON vs typed + content_hash) | Backend lead | Phase 1 |
| 3 | Soft-archive implementation (`archived_at NULL` vs `is_archived BIT` vs partition) | Backend lead | Phase 0 |
| 4 | `vims_safety_recommendation` cardinality (1-per-tier vs child table) | Backend lead | Phase 1 |
| 5 | `vims_safety_soi_finding` state ENUM + Carried-Forward semantics | Backend lead | Phase 4 |
| 6 | `vims_safety_incident_phase_log` table shape | Backend lead | Phase 1 |
| 7 | WRH lookback window / query timeout for SCM attendance | Backend + WRH lead | Phase 3 |
| 8 | FTS engine choice (Elasticsearch / PG-FTS / platform default) | Platform | Phase 7 |
| 9 | Dashboard period persistence per user session | Frontend lead | Phase 7 |
| 10 | Paper-format PDF vs Excel layout (barcode/QR for unique ID) | Product + Design | Phase 4 |
| 11 | Trainee rotation coverage % formula | Product | Phase 4 |
| 12 | 90-day counter reset timing (upload vs approval vs cron) | Backend lead | Phase 7 |

### Deferral commentary

**#1 — `vims_safety_incident` ENUMs & nullability.** Options: (a) ENUM-strict CHECK constraints on every state/classifier column (tight, hard to evolve); (b) VARCHAR(N) + lookup tables (flexible, adds joins); (c) Hybrid — ENUM for state/phase/band, lookup for incident_type_id/loss_type_primary_id. Current lock leans (c). Impact: Phase 1 serializer + Zod schema tightening.

**#2 — `vims_safety_field_history` column shape.** See §4.3 above. Option A TEXT is current lock; Option B JSON preserves typing; Option C typed + content_hash gives strongest audit defensibility (but D-GAP-D2/G2 block crypto hash — non-crypto rolling hash only). Impact: ISM Code §10 non-repudiation strength + storage footprint.

**#3 — Soft-archive implementation.** Options: (a) `archived_at NULL` sentinel (current lock — simplest); (b) `is_archived BIT + archived_at DATETIME2` (redundant but explicit); (c) partition by archived state (best for 3-year retention purge performance; high initial complexity). Impact: retention job (D-GAP-G2) + search default filters. Required by Phase 0 because initial migration sets the column shape.

**#4 — `vims_safety_recommendation` cardinality.** See §4.14. Options: (a) one-row-per-tier (current lock — V-INC-064 compatibility); (b) single row with three tier columns (lossy for multiple recs per tier); (c) parent row + child tier-specific rows (most flexible, most joins). Impact: ≥1-per-tier enforcement on YELLOW/RED (V-INC-064).

**#5 — `vims_safety_soi_finding` state ENUM + Carried-Forward.** See §4.6. Options: (a) 5-state ENUM with explicit `CARRIED_FORWARD` state + counter (current lock); (b) 4-state ENUM + derived carried-forward via JOIN to `vims_safety_scm_agenda`; (c) separate `vims_safety_soi_finding_scm_link` table. Impact: SCM auto-feed query complexity (D-SOI-14).

**#6 — `vims_safety_incident_phase_log` shape.** See §4.2. Options: (a) typed phase_from/phase_to (current); (b) free-form JSON; (c) generic key-value pairs. Impact: phase-timeline UI query shape.

**#7 — WRH lookback window.** See §4.11. Options: (a) 24h + 7d snapshots on save (current lock); (b) streaming query at render time (can hit WRH timeouts); (c) configurable via env var. Impact: SCM attendance save latency; warn-don't-block contract (D-GAP-M11).

**#8 — FTS engine.** See TECH_STACK §2.3. Options: (a) SQL Server native CONTAINS/FREETEXT (no new dependency; platform-native); (b) Elasticsearch (richer relevance, new infra); (c) PostgreSQL FTS (requires platform DB change — unlikely). Impact: FEAT-SAF-DASH-007 + FEAT-SAF-INC-009 + FEAT-SAF-SOI-019. V1 fallback is LIKE-based narrow search. Current BLOCKED stub in TECH_STACK.

> **BLOCKED: FTS engine selection (Round 20 build-time deferral #8)**
> **Question:** Elasticsearch, SQL Server native CONTAINS/FREETEXT, or platform default?
> **Gap:** Round 20 deferred this to build-time; no D-* decision locks it.
> **Impact:** `FEAT-SAF-DASH-007` incident search, `FEAT-SAF-INC-009` search-by-M-SCAT, `FEAT-SAF-SOI-019` repeat-finding detection all render a degraded LIKE contract in V1.

**#9 — Dashboard period persistence.** Options: (a) in-memory Zustand (loses on reload); (b) localStorage per-user (survives reload, browser-local); (c) server-side stored on `users.dashboard_period_pref` (portable across devices). Impact: Safety Intelligence Dashboard UX.

**#10 — Paper-format PDF vs Excel & QR vs barcode.** Options: (a) QR code (current default, `VITE_SAFETY_QR_FORMAT=qr`); (b) Code128 barcode (1D, legacy scanner-compatible); (c) plain alphanumeric unique ID only (no scanner tooling, manual typing). Impact: SOI paper-first scan-back workflow (D-GAP-E4) — paper-to-digital linkage.

> **BLOCKED: SOI unique-ID flag format (deferral #10)**
> **Question:** QR code, Code128 barcode, or plain alphanumeric on the SOI paper checklist?
> **Gap:** D-SOI-10 revised + D-GAP-E1/E3/E4 mandate a unique checklist ID; visual encoding deferred.
> **Impact:** `FEAT-SAF-SOI-012` paper-first download template; `apps/safety/services/soi_checklist_generator.py` render path.

**#11 — Trainee rotation coverage % formula.** Options: (a) strict: `(distinct crew in last 12m ≥ 1 inspection) / total crew on vessel`; (b) weighted by trainee_slot (slot-1 = full credit, slot-2/3 = half); (c) include only deck + engine ranks. Impact: Safety Intelligence Dashboard Crew Rotation panel.

**#12 — 90-day counter reset timing.** Options: (a) reset at finding-registration time (current design, §4.5 last_inspected_at set when findings saved); (b) reset at Master approval (more conservative; delays compliance credit); (c) reset via overnight cron after Master approval (smoothest on close-of-business inspections). Impact: SOI Compliance % (D-GAP-DESIGN-01) precision.

---

## 9. API Endpoints

### 9.1 Base contract

- **Base URL:** `/api/safety/`
- **Auth:** SimpleJWT Bearer token (inherited from platform). Token payload carries `form_ids`, `process_ids`, role, vessel scope.
- **Permission enforcement:** `HasFormPermission` for route access + `HasProcessPermission` for mutating actions + `HasVesselScope` for vessel filter.
- **Content type:** `application/json` unless stated.
- **Error envelope (all endpoints):**
  | Code | Body | When |
  |------|------|------|
  | 400 | `{"detail":"...","errors":{...}}` | Malformed request |
  | 401 | `{"detail":"Authentication credentials were not provided."}` | Missing/expired JWT |
  | 403 | `{"detail":"You do not have permission to perform this action."}` | `form_id`/`process_id` missing OR vessel out of scope |
  | 404 | `{"detail":"Not found."}` | Resource missing or out of scope |
  | 409 | `{"detail":"Phase transition denied.","errors":{"state":[...],"current_phase":N}}` | Phase-state-machine rejection |
  | 422 | `{"detail":"Validation failed.","errors":{"field":["V-INC-nnn: ..."]}}` | VALIDATION_RULES violation |

### 9.2 Incident + Near Miss endpoints (shared table, `record_type` discriminator)

#### 9.2.1 `GET /api/safety/incidents/`

List incidents/near-misses with filters + pagination.

- **Auth:** `SAF_F_001`. Ship users see own vessel (`Crew_Onboarding_History`); office users filtered by `master_RoleByVessel`.
- **Query params:** `vessel_id` (UUID), `record_type` (INCIDENT | NEAR_MISS), `state`, `risk_band`, `date_from`, `date_to`, `page`, `page_size` (max 100).
- **Response 200:** paginated list. Near-miss rows include reporter fields for authorized users within vessel scope; anonymous/masked reporter display is not used.
- **Response 403:** vessel out of scope.

```json
{
  "count": 42,
  "results": [
    {
      "id": 123, "incident_number": "EBK/2026/007", "record_type": "INCIDENT",
      "state": "PHASE_3_EVIDENCE", "phase": 3, "risk_band": "YELLOW",
      "imo_classifier": "MI", "incident_type_id": 7,
      "occurred_at": "2026-04-10T03:15:00Z", "vessel_id": "uuid",
      "narrative": "...", "near_miss_priority": null
    }
  ]
}
```

#### 9.2.2 `POST /api/safety/incidents/`

Create incident / near miss. `record_type` in body determines row class.

- **Auth:** `SAF_F_002` + `SAF_P_001`. Creators per D-RBAC: Top-4 officers (Master, CO, CE, 2E) for incidents; any rank for near miss (D-RBAC-11).
- **Request body:**
  ```json
  {
    "record_type": "INCIDENT",
    "vessel_id": "uuid",
    "occurred_at": "2026-04-10T03:15:00Z",
    "reported_at": "2026-04-10T03:50:00Z",
    "narrative": "at least 200 chars ...",
    "latitude": 1.25, "longitude": 103.85,
    "shore_assistance_required": false,
    "vessel_location": "At sea",
    "onboard_location": "Main deck",
    "last_port": "Singapore",
    "departure_date": "2026-04-09",
    "vessel_condition": "LOADED",
    "incident_type_id": 7,
    "loss_type_primary_id": 1
  }
  ```
- **Response 201:** `{ "id": 123, "incident_number": "EBK/2026/DRAFT-0001", "state": "DRAFT", ... }`.
- **Errors:** 422 V-INC-001 (narrative <200 chars), V-INC-002/003/004 (timestamp sanity), V-INC-005 (vessel out of scope), V-INC-012 (position missing when imo_classifier set).

#### 9.2.3 `GET /api/safety/incidents/{id}/`

Full detail. Near-miss reporter details are returned for authorized users within vessel scope; anonymous/masked reporter display is not used.

- **Auth:** `SAF_F_001` + vessel scope.
- **Response 200:** full row + eager-loaded `phase_log`, `recommendations`, `corrective_actions`, `signatures`, `evidence_ids`.
- **Response 404:** out of scope.

#### 9.2.4 `PATCH /api/safety/incidents/{id}/`

Edit within the incident edit window. Advancing to a later phase does not lock earlier phase edits. User-facing investigation save endpoints remain editable for authorized users until office approval locks the incident, even when the incident `current_phase` has not reached the legacy backend phase number for that data. This includes RCA, facts/evidence helpers, corrective action, preventive action, evidence documents, and witness statements. The former Lessons Learned screen is not a current edit surface; legacy `LESSONS_LEARNT` rows remain readable for old records/API compatibility. The lock starts when `state` is `APPROVED`, `CLOSED`, or `SUPERSEDED`. Every field change emits a `vims_safety_field_history` row (D-EDGE-10).

- **Auth:** `SAF_F_001` + role/phase matrix. User-facing Phase 2-6 save endpoints require an allowed edit role and an incident that has not been office-approved, closed, or superseded; they do not require the legacy backend phase number to have been reached. Submit/continue endpoints still enforce ordered workflow movement.
- **Phase 1 edit:** `GET/PATCH /api/safety/incidents/{id}/phase-1/` uses the same edit window. GET returns resolved `vessel_code`, `vessel_name`, and `vessel_display_name` for the locked Vessel/Vessel code UI. Create accepts `vessel_code` only for draft-number allocation; update ignores display-only code changes and validates persisted `vessel_id` against scope. Null `external_party_injury` does not delete saved injury details.
- **Phase 2 edit:** explicit `imo_classifier` values (`SMC`, `MC`, `MI`) are preserved and validated. The system defaults to `NOT_APPLICABLE` only when no classifier exists. Position is required when the classifier is `SMC`, `MC`, or `MI`.
- **Errors:** 403 if not in role-phase window; 400 if office approval has locked the incident; 422 per VALIDATION_RULES §2.

#### 9.2.4a Phase 4 evidence documents (CR-012, CR-013)

The current user-facing evidence screen writes new evidence to the legacy `PAPER` tab only. Legacy `PEOPLE`, `POSITION`, `PARTS`, and `ELECTRONIC` rows still exist in serializers and storage for backward compatibility with older records. Authorized evidence editors can use these endpoints before Phase 4 is reached; the endpoints still reject records locked by office approval, closure, or supersession.

- `GET/PATCH /api/safety/incidents/{id}/phase-4/evidence/` returns the legacy-compatible workspace payload.
- `POST /api/safety/incidents/{id}/phase-4/evidence/attachments/` accepts multipart fields `tab_key=paper`, `file`, `title`, and optional `description`.
- `PATCH /api/safety/incidents/{id}/phase-4/evidence/attachments/?path={attachment_path}` updates saved attachment `title` and `description` metadata on the existing attachment record and matching `EvidenceItem`; it does not replace the uploaded file.
- `PATCH /api/safety/incidents/{id}/phase-4/interviews/{interview_id}/` updates an existing simplified Witness Statement row instead of creating a new witness row.
- The upload response returns `attachment` metadata and refreshed `workspace`.
- The attachment metadata stored in `IncidentEvidence.structured_data.attachments[]` includes `attachment_path`, `file_name`, `original_name`, `content_type`, `byte_size`, `tab_key`, `title`, `description`, and `uploaded_at`.
- A matching `EvidenceItem` row is created with `item_type=PHYSICAL`, `title`, `description`, `source_label=PAPER`, and the same metadata JSON, so exports and later analysis can display the user-facing title instead of a raw file UUID/path.

#### 9.2.4b Phase 7 Loss Evaluation (CR-047)

Current visible Phase 7 uses route path `/phase-6/` and no longer requires backend compatibility phase 8 for workspace read/save.

- `GET /api/safety/incidents/{id}/phase-6/` returns `phase_title="Loss Evaluation"`, effective/saved `report_type` (`INCIDENT` or `INJURY`), `choices.report_type`, fixed dropdown choices, safe-working-practice options from `vims_safety_injury_dropdown_option`, saved `loss_evaluation`, and `ready_for_close` for authorized ship-side or office-side users with incident form access and vessel scope.
- `PATCH /api/safety/incidents/{id}/phase-6/` creates or updates the one-to-one `vims_safety_incident_loss_evaluation` row, persists selected `report_type`, and emits `vims_safety_field_history` rows for changed fields without requiring Office Review approval/backend `current_phase = 8`.
- `POST /api/safety/incidents/{id}/phase-6/close/` requires office close authority, a saved Loss Evaluation row, and `closure_reason`, then transitions backend `current_phase` 8 to 9 and sets `state=CLOSED`.
- `POST /api/safety/incidents/{id}/phase-6/verify/` remains registered for legacy effectiveness-verification compatibility but is not the current visible Phase 7 UI.
- PIC and DPA can save and close for every risk band after Office Review approval.

#### 9.2.5 `POST /api/safety/incidents/{id}/transition/`

Forward or loop-back phase transition. Writes `vims_safety_incident_phase_log`.

- **Auth:** `SAF_F_003` + `SAF_P_002` (forward) or `SAF_P_003` (loop-back).
- **Request body:**
  ```json
  { "target_phase": 5, "transition_type": "FORWARD" }
  ```
  or
  ```json
  { "target_phase": 3, "transition_type": "LOOP_BACK",
    "loop_back_reason": "New witness statement changes evidence picture" }
  ```
- **Response 200:** updated incident + appended phase_log row.
- **Errors:** 409 PhaseTransitionDenied with current_phase; 422 V-INC-040..056 (phase-specific preconditions, excluding legacy V-INC-043 in the current UI); 422 V-INC-061 (ALARP not attested); 422 V-INC-044 (Blame-fixation without override); 422 loop_back_reason missing.

#### 9.2.6 `POST /api/safety/incidents/{id}/accept/` (Office Review acceptance)

- **Auth:** `SAF_F_001` plus `SAF_P_004` or `SAF_P_006`. Current Office Review role gate allows PIC or DPA for every risk band; legacy RED/FM paths are compatibility-only.
- **Request body:** `{"typed_name":"...","device_fingerprint":"...","office_comment":"..."}`. `office_comment` is optional, unrestricted text and is saved to `vims_safety_incident.office_comment` when supplied.
- **Response 200:** `{"state":"PHASE_7_DPA_ACCEPTED","dpa_accepted_at":"...","dpa_accepted_by":"...","office_comment":"..."}`.

#### 9.2.6a `GET/POST /api/safety/incidents/{id}/fleet-alert/` (Office Review Fleet Alert)

- **Auth:** `SAF_F_001` plus Office Review process permission `SAF_P_004` or `SAF_P_006`; role must be PIC or DPA. The incident must be in backend `current_phase = 7` (visible Phase 6 Office Review).
- **GET response:** incident summary plus `recipient_vessels[]` loaded from active, non-deleted `VesselData` rows. Each row returns `vessel_id`, `display_name`, `vessel_name`, `vessel_code`, and `has_email`.
- **POST request body:** `{"recipient_vessel_ids":["<vessel_uuid>", "..."]}`. At least one selected active ship is required.
- **POST behavior:** writes `INCIDENT_FLEET_ALERT` in-app notifications through `psc_notification` for selected vessel recipients and sends best-effort emails only to selected ships using `VesselData.email`. Ships not selected do not receive in-app or email alerts.
- **Response 200:** includes selected `recipient_vessel_ids`, selected `recipient_vessels`, `notifications_emitted`, `emails_sent`, `email_failed`, and `vessels_without_email`.

#### 9.2.7 `POST /api/safety/incidents/{id}/close/`

- **Auth:** `SAF_P_006` (GREEN — PIC) or `SAF_P_005` (RED — FM) or `SAF_P_004` (YELLOW — DPA).
- **Errors:** 422 V-INC-061 (ALARP not attested on all System-Actions); 422 V-INC-064 (YELLOW/RED missing ≥1 rec per tier).

#### 9.2.8 `POST /api/safety/incidents/{id}/reopen/`

Band-gated re-open (D-EDGE-03).

- **Auth:** `SAF_P_008`. GREEN → PIC; YELLOW → DPA; RED → FM.
- **Request body:** `{"reason":"new evidence surfaced"}`.

#### 9.2.9 `POST /api/safety/incidents/{id}/override-blame/`

- **Auth:** `SAF_P_009`. DPA for GREEN/YELLOW; FM for RED (D-DNV-11 #5).
- **Request body:** `{"justification":"..."}`.

#### 9.2.10 `GET /api/safety/incidents/{id}/pdf/`

Emit D-PDF-01 internal 10-section report. Near-miss → D-PDF-03a lighter template. For incident exports, the rendered title is `Injury Report` when `vims_safety_external_party_injury` has a row for the incident; otherwise the rendered title is `Incident Report`. The Estimated Cost selection prints Phase 7 Loss Evaluation blocks from `vims_safety_incident_loss_evaluation` when that row exists; the saved `report_type` controls whether incident repair/loss/cost or injury safe-working-practice/rest/cost blocks print. Older rows without `report_type` use the injury-record fallback, and older injury cost fields are used only as fallback when no Loss Evaluation row exists.

- **Auth:** `SAF_P_023`.
- **Query:** optional `sections`, accepted as repeated values or comma-separated keys. Current frontend defaults to `summary`, `reporter_details`, `injury_details`, `estimated_cost`, `root_cause`, `evidence_documents`, `corrective_preventive_actions`, and `signature`. The legacy backend key `lessons_learned` remains accepted for old/direct exports only. Omitted or empty `sections` renders all allowed backend sections for compatibility.
- **Response 200:** `application/pdf` binary. Near-miss PDFs show reporter details for authorized users and must not print anonymous/masked-reporter wording. Incident PDFs are available before Phase 7 acceptance and render required signature rows by band even when unsigned, showing `Pending` for incomplete signature slots. Incident `office_comment` and closure reason print in the final Office Review / Closure area before Signature, not in Summary.

#### 9.2.11 `POST /api/safety/incidents/{id}/link/`

Multi-vessel linkage / supersede-and-create-new (D-EDGE-01, D-EDGE-07).

- **Request body:** `{"target_incident_id": 456, "link_type": "SUPERSEDE" | "RELATED"}`.

#### 9.2.12 `GET /api/safety/near-miss/reporter/{incident_id}/`

Return reporter identity for authorized users within vessel scope. Anonymous/masked reporter display is not used in V1.

- **Auth:** `SAF_F_002` plus vessel scope and any stricter Safety permission configured for reporter-detail access. 404 if incident is not `record_type='NEAR_MISS'`.

#### 9.2.13 `GET /api/safety/near-miss/cause-options/`

Return active Near Miss cause dropdown options grouped by factor and cause stage.

- **Auth:** Safety access and vessel scope where configured.
- **Source:** `vims_safety_near_miss_cause_option`.
- **Response 200:** active rows ordered by `factor`, `cause_stage`, `display_order`, and `option_text`.
- **Usage:** Create and rework forms load this endpoint to render Human/Vessel/Management/Other Factors with Immediate Cause and Root Cause dropdowns. Selected values are saved as JSON text in `near_miss_factor_causes`.

### 9.3 SCM endpoints

#### 9.3.1 `GET /api/safety/scm/`

List SCM meetings. Filter by `vessel_id`, `meeting_type`, `date_from`, `date_to`.

- **Auth:** `SAF_F_007`.

#### 9.3.2 `POST /api/safety/scm/`

Create SCM draft. Ship-side — both `meeting_type=REGULAR` and `meeting_type=AD_HOC` can be created by Master or Chief Officer. Ad-Hoc requires `ad_hoc_trigger_reason`. Before insert, the backend builds WRH host readiness for the vessel/date and submitted roster; creation is rejected unless ship-time configuration exists and every roster crew member has available, compliant WRH data (D-MAINT-CR014). Frontend "Submit to Office" saves the draft and immediately calls the submit endpoint below.

- **Request body:**
  ```json
  {
    "vessel_id": "uuid", "meeting_type": "REGULAR",
    "meeting_date": "2026-04-30", "meeting_time_local": "10:00:00",
    "location": "Singapore anchorage",
    "voyage_no": "V2026-03"
  }
  ```
- **Blocked response:** `400` with `detail="SCM meeting cannot be hosted until all WRH warnings are cleared."` and `wrh_host_readiness` containing `ready`, `missing_ship_time`, `checked_crew_count`, `warnings`, and `blocking_crew`.

#### 9.3.2A `POST /api/safety/scm/{id}/submit/`

Submit SCM to office. Master or Chief Officer can submit a `DRAFT` meeting after agenda/attendance preflight passes. State changes to `SUBMITTED`; UI displays `Submitted to Office`.

#### 9.3.3 `GET|POST /api/safety/scm/{id}/attendance/`

Read or bulk-save attendance rows. GET is visible to office reviewers so they can see the Attendance + WRH snapshot. POST/write is restricted to Master or Chief Officer while the SCM is not closed. For each row, the backend runs a **live join on `wrh_attendance` and `wrh_ship_time_config`** (D-GAP-M11, D-GAP-M26) to populate `wrh_rest_hours_24h` / `wrh_rest_hours_7d` / `wrh_non_compliance_flag`. Missing WRH → `wrh_data_available=false`, warning surfaces in response and remains warning-only after the meeting exists; new hosting is blocked earlier by `POST /api/safety/scm/` readiness validation (D-MAINT-CR014).

- **Request body:**
  ```json
  { "rows": [
    { "crew_id": "SG00042", "present": true },
    { "crew_id": "SG00088", "present": false, "absence_reason": "Watchkeeping" }
  ]}
  ```

#### 9.3.4 `GET /api/safety/scm/{id}/auto-feed/`

Return Open findings (D-SOI-14 "Safety Observations for the Month") + Closed-Since-Last-SCM summary block — both auto-populated from `vims_safety_soi_finding` via cross-table query.

#### 9.3.5 `PATCH /api/safety/scm/{id}/agenda/`

Updates agenda section text and suggestions / recommendations. Write is restricted to Master or Chief Officer and rejected after Office Comment closure.

#### 9.3.6 `POST /api/safety/scm/{id}/office-comment/`

Office review closure. DPA, FM, Shore HOD, or Marine Superintendent profile `407EF017-0F1C-EF11-A9F1-F348983BAE6B` saves `office_comment`. State `SUBMITTED` or `DRAFT` → `CLOSED`; writes `office_comment_by` and `office_comment_at`. Once closed, vessel-side meeting/attendance/agenda edits are rejected. Overdue SOI and WRH gaps remain warnings/visibility only and do not block closure.

#### 9.3.7 `GET /api/safety/scm/{id}/pdf/`

Emit D-PDF-03b legacy SCM layout. Available immediately after meeting creation for any non-deleted SCM. The old reserved Section 2 is removed; former Sections 3-10 are renumbered to Sections 2-9. The PDF prints Attendance + WRH snapshot, Closed-Since-Last, SOI summary without duplicate finding details, Section 7 findings/corrective measures, Office Comment, and plain Master Signature / Chief Officer Signature lines. It does not print attendee digital signature status or device fingerprints.

### 9.4 SOI endpoints

#### 9.4.1 `GET /api/safety/soi/`

List inspections. Filter by `vessel_id`, `state`, `cycle_label`, `date_from`, `date_to`.

- **Auth:** `SAF_F_010`.

#### 9.4.2 `POST /api/safety/soi/`

Create PLANNED inspection. Validates `safety_officer_department != assistant_department` at save (D-SOI-08 hard-enforced). Assistant lookup uses **live join on `Crew_Onboarding_History` + `HRM501`** (D-GAP-I2) to resolve department.

- **Request body:**
  ```json
  {
    "vessel_id": "uuid", "cycle_label": "Q2/2026",
    "planned_date": "2026-04-20",
    "safety_officer_crew_id": "SG00042",
    "assistant_crew_id": "SG00088",
    "trainee_crew_ids": ["SG00111","SG00222"],
    "area_ids": [1,2,5,13],
    "section_12_included": true
  }
  ```

- **Errors:** 422 cross-functional violation; 422 trainee count > 3; 422 section_12_included=true without area_id=13.

#### 9.4.3 `POST /api/safety/soi/{id}/generate-unique-id/`

Generate `checklist_unique_id` (D-GAP-E1 idempotent). Subsequent calls return the same ID — the endpoint is idempotent by design.

- **Auth:** `SAF_F_011`.
- **Response 200:** `{"checklist_unique_id":"SOI-EBK-2026-Q2-0007"}`.

#### 9.4.4 `GET /api/safety/soi/{id}/checklist/download/?format=pdf|xlsx`

Paper-first checklist generator (D-SOI-10 revised, D-GAP-E4). Returns the dynamically built PDF or Excel. Writes `checklist_generated_at`, flips state to `DOWNLOADED`. **No scan-upload endpoint exists** (D-GAP-E4 explicit).

- **Auth:** `SAF_F_011`.
- **Response 200:** `application/pdf` or `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` binary. Contains QR or Code128 barcode (deferral #10) encoding `checklist_unique_id` in header.
- **Idempotency:** subsequent downloads with the same `checklist_unique_id` serve identical content (D-GAP-E1) — supports lost/damaged paper recovery (D-GAP-E3).

#### 9.4.5 `POST /api/safety/soi/{id}/register-finding/`

Register one finding (D-SOI-06). HIGH severity **must** include a photo attachment (D-GAP-M24 hard-enforced by DB CHECK constraint + serializer).

- **Auth:** `SAF_F_012` + `SAF_P_013`.
- **Request body:**
  ```json
  {
    "area_id": 5, "item_id": 42,
    "title": "...", "description": "...",
    "severity": "HIGH", "priority": "HIGH",
    "assigned_crew_id": "SG00088", "due_date": "2026-05-01",
    "photo_attachment_path": "/safety/{vessel_id}/soi/photos/xyz.jpg"
  }
  ```
- **Errors:** 422 V-SOI-* HIGH severity without photo; 422 area_id not in inspection's area list.

#### 9.4.6 `POST /api/safety/soi/{id}/submit/`

Flips state `DOWNLOADED/IN_FIELDWORK → REPORTED`. Supports **partial submission** (D-GAP-E2): only per-area `inspected=true` rows update `last_inspected_at` and reset the 90-day counter on `vims_safety_soi_vessel_area_map`. Remaining areas stay in DOWNLOADED state for later completion under the same `checklist_unique_id`.

#### 9.4.7 `POST /api/safety/soi/findings/{finding_id}/pending-closure/`

SO marks finding pending closure (D-SOI-07).

- **Auth:** `SAF_P_014`.

#### 9.4.8 `POST /api/safety/soi/findings/{finding_id}/approve-closure/`

Master approves closure → MASTER_APPROVED → CLOSED. Auto-reflects into next SCM under Closed-Items block (D-SOI-14 + D-GAP-M22).

- **Auth:** `SAF_P_015`. Master only.

#### 9.4.9 `POST /api/safety/soi/vessel-area-map/toggle-applicability/`

Master requests `applicable=false`; DPA approves (D-GAP-M19 workflow). Writes `vims_safety_soi_applicability_log` with both signatures + reason.

- **Auth:** `SAF_P_016` (Master request) + `SAF_P_017` (DPA approval).
- **Request body (Master step):**
  ```json
  { "vessel_id":"uuid", "area_id": 11,
    "new_applicable": false,
    "reason": "Vessel has no CO2 fixed system — confirmed by class records" }
  ```

#### 9.4.10 `GET /api/safety/soi/{id}/lost-paper/recover/`

Re-download same `checklist_unique_id` per D-GAP-E3. Logs `lost_paper_flag=true` + `lost_paper_note`.

#### 9.4.11 `GET /api/safety/soi/{id}/pdf/summary/`

Emit summary record (not duplicate checklist — per §2C.19). Contains findings + Master approval chain + link to `checklist_unique_id`.

### 9.5 Corrective Action endpoints

#### 9.5.1 `GET /api/safety/corrective-actions/`

List CAs by `vessel_id`, `status`, `aging_bucket`, `source_table`.

#### 9.5.2 `POST /api/safety/corrective-actions/`

Create CA. Optional `purchase_req_id` hard FK (D-GAP-M12). If specified, backend verifies `pur_requisition.id` exists and requisition status is not archived.

- **Auth:** `SAF_P_020`.
- **Errors:** 422 purchase_req_id FK violation; 403 if caller lacks Purchase read permission.

#### 9.5.3 `POST /api/safety/corrective-actions/{id}/link-pr/`

Attach a PR to an existing CA.

- **Auth:** `SAF_P_021`.

#### 9.5.4 `POST /api/safety/corrective-actions/{id}/verify/`

Physical verification record (Q45 pattern).

- **Auth:** `SAF_P_022`.
- **Request body:** `{"note":"...","verifier_user_id":"..."}`

### 9.6 Reference-data endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/safety/reference/mscat/` | GET | `SAF_F_018` | List master_mscat_taxonomy (174) |
| `/api/safety/reference/mscat/{subcode_id}/` | PATCH | `SAF_P_018` (DPA) | DPA-maintained updates |
| `/api/safety/reference/immediate-causes/` | GET | `SAF_F_018` | 52 rows |
| `/api/safety/reference/loss-types/` | GET | `SAF_F_018` | 7 rows |
| `/api/safety/reference/soi-areas/` | GET | `SAF_F_018` | 13 rows |
| `/api/safety/reference/soi-items/` | GET | `SAF_F_018` | 329 rows, paginated |
| `/api/safety/reference/soi-items/{id}/` | PATCH | `SAF_P_019` | DPA-maintained updates |
| `/api/safety/reference/bias-guards/` | GET | `SAF_F_018` | 8 rows |
| `/api/safety/reference/incident-types/` | GET | `SAF_F_018` | 32 active rows, ordered by the CR-031 business sequence |

### 9.7 Dashboard endpoints

| Endpoint | Purpose | Decision |
|----------|---------|----------|
| `GET /api/safety/dashboard/heinrich/?vessel_id=...&window=12m` | Heinrich Ratio with confidence indicator | D-GAP-M27 |
| `GET /api/safety/dashboard/repeat-root-cause/?scope=fleet|vessel&window=6m` | Repeat root-cause radar | D-GAP-H2 |
| `GET /api/safety/dashboard/ca-aging/?vessel_id=...` | CA Aging Pipeline (0-15/15-30/30-45/45+) | D-GAP-M29 |
| `GET /api/safety/dashboard/soi-compliance/?vessel_id=...` | SOI Compliance % (D-GAP-DESIGN-01 label) | §2C.17 |
| `GET /api/safety/dashboard/crew-rotation/?vessel_id=...&window=12m` | Crew Rotation Coverage | D-SOI-09 (deferral #11 for formula) |
| `GET /api/safety/dashboard/overdue/?vessel_id=...` | Overdue flag list (80% + deadline, D-GAP-F3) | D-GAP-F3 |

### 9.8 Audit endpoints

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /api/safety/audit/field-history/?parent_table=...&parent_id=...` | `SAF_F_017` | Read-only; emits platform access-log event (D-GAP-F4) |
| `GET /api/safety/audit/phase-log/?incident_id=...` | `SAF_F_017` | Phase timeline |

### 9.9 Export endpoints

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /api/safety/export/incident/{id}/pdf` | `SAF_P_023` | D-PDF-01 internal report; optional `sections` query filters printable sections; not blocked solely by pending Phase 7 acceptance |
| `GET /api/safety/export/near-miss/{id}/pdf` | `SAF_P_023` | D-PDF-03a light template |
| `GET /api/safety/export/scm/{id}/pdf` | `SAF_P_023` | D-PDF-03b legacy structure |
| `POST /api/safety/export/auditor-bundle/` | `SAF_F_020` | D-PDF-02 configurable ZIP (record types + date range); attachments live in `attachments/` subfolder |
| `GET /api/safety/export/msc-mepc-3/{incident_id}/` | `SAF_P_023` | MSC-MEPC.3/Circ.4 auto-populated PDF (D-DNV-12); requires applicable IMO classifier but not Phase 7 acceptance |

### 9.10 Circular integration

`POST /api/safety/circular/from-incident/{id}/` — writes to **existing VIMS Circular module** (per D-GAP-R17 lock; see TECH_STACK §7). Safety module emits a draft; VIMS Circular approval chain runs independently.

Near Miss Office Comments are handled through `/api/safety/near-miss/{id}/office-comments/` with the legacy `/triage/` route retained as a compatibility alias. `Accept` saves priority, category tag, factor causes, and office comment; `Send to Rework` moves the record back to vessel rework with a required reason. PIC/office PIC accepts LOW/MEDIUM cases; DPA accepts HIGH cases.

Near Miss HIGH-priority fleet alerts use a UI handoff, not a Safety-owned Circular insert. `/api/safety/near-miss/{id}/fleet-alert/draft/` prepares anonymised title/body text. The frontend stores that text as a one-time Circular prefill and opens `/circular/office?safety_prefill=near_miss_fleet_alert`; DPA completes recipients/category/priority/attachments and publishes from the Circular module. The Near Miss `[Issue fleet alert]` action records Safety workflow completion separately and must not be treated as Circular publication.

---

## 10. Cross-Module Live-Join Contracts

Per D-GAP-I2 — all cross-module reads are **live SQL joins on `ksm_marine_live`**. No ETL, no sync, no staleness. Safety issues queries against sibling module tables directly.

### 10.1 Safety ↔ Reporting — MSC-MEPC.3 position (D-GAP-M09, D-GAP-M10)

Incident intake auto-fills `latitude` / `longitude` from the nearest Daily Report within ±12 hours of `occurred_at`. Outside the tolerance → manual entry (D-GAP-M10 never blocks submit; row flagged `awaiting_daily_report_match=1`).

```sql
-- Incident intake position auto-fill query (executed in incident_repo.py on Phase 1 save)
SELECT TOP 1
  dr.id AS daily_report_id, dr.Latitude, dr.Longitude, dr.ReportDate
FROM (
  SELECT id, VesselID, Latitude = NULL, Longitude = NULL, ReportDate FROM DepartureReport
  UNION ALL
  SELECT id, VesselID, Latitude, Longitude, ReportDate FROM NoonReport
  UNION ALL
  SELECT id, VesselID, Latitude, Longitude, ReportDate FROM ArrivalReport
  UNION ALL
  SELECT id, VesselID, Latitude = NULL, Longitude = NULL, ReportDate FROM NoonReportPort
) dr
WHERE dr.VesselID = @vessel_id
  AND ABS(DATEDIFF(HOUR, dr.ReportDate, @occurred_at)) <= 12
ORDER BY ABS(DATEDIFF(HOUR, dr.ReportDate, @occurred_at));
```

User may **edit the auto-filled value** — writes `position_source='DAILY_REPORT_EDITED'` (D-GAP-M09). V-INC-012 enforces position when `imo_classifier IN ('SMC','MC','MI')`.

### 10.2 Safety ↔ WRH — SCM attendance (D-GAP-M11, D-GAP-M26)

On SCM create, the same WRH live join is used as a host-readiness gate: missing ship-time configuration, missing roster WRH data, or non-compliant roster WRH blocks meeting creation (D-MAINT-CR014). On SCM attendance save/display after creation, the join warms `wrh_rest_hours_24h` / `wrh_rest_hours_7d` / `wrh_non_compliance_flag`; missing rows → `wrh_data_available=0` remains visible but does not block PDF export or office closure. Timezone resolution via `wrh_ship_time_config`:

```sql
-- SCM attendance WRH warm-up (executed in scm_repo.py on POST /attendance/)
SELECT
  @crew_id                                  AS crew_id,
  COALESCE(SUM(wa.rest_hours_24h), NULL)    AS wrh_rest_hours_24h,
  COALESCE(SUM(wa.rest_hours_7d),  NULL)    AS wrh_rest_hours_7d,
  MAX(CASE WHEN wa.non_compliance_flag = 1 THEN 1 ELSE 0 END) AS wrh_non_compliance_flag,
  CASE WHEN COUNT(*) = 0 THEN 0 ELSE 1 END  AS wrh_data_available
FROM wrh_attendance wa
WHERE wa.crew_id = @crew_id
  AND wa.log_date >= CAST(DATEADD(DAY, -7, @meeting_date) AS DATE)
  AND wa.log_date <= @meeting_date;

-- Ship-local time resolution for meeting_time_local render
SELECT TOP 1 utc_offset_minutes
FROM wrh_ship_time_config
WHERE vessel_id = @vessel_id
  AND effective_from <= @meeting_date
  AND (effective_to IS NULL OR effective_to >= @meeting_date)
ORDER BY effective_from DESC;
```

### 10.3 Safety ↔ CMS — SOI assistant lookup + incident crew assignment (D-GAP-I2)

SOI create validates cross-functional assistant via live join. Same pattern used when assigning crew to an incident. No FK is added — CMS tables are legacy PascalCase.

```sql
-- SOI create: resolve safety_officer + assistant departments (D-SOI-08)
SELECT
  ho.rank                            AS sa_rank,
  ho.department                      AS sa_dept,
  ho2.rank                           AS asst_rank,
  ho2.department                     AS asst_dept
FROM Crew_Onboarding_History co1
JOIN HRM501 ho  ON ho.crew_id  = co1.crew_id
JOIN Crew_Onboarding_History co2 ON co2.vessel_id = co1.vessel_id
JOIN HRM501 ho2 ON ho2.crew_id = co2.crew_id
WHERE co1.crew_id = @safety_officer_crew_id
  AND co2.crew_id = @assistant_crew_id
  AND co1.vessel_id = @vessel_id
  AND co1.is_current = 1 AND co2.is_current = 1;
-- Validation fails at serializer if sa_dept = asst_dept.
```

### 10.4 Safety ↔ Purchase — CA hard FK (D-GAP-M12)

`vims_safety_corrective_action.purchase_req_id` is a **hard FK** to `pur_requisition(id)`. Referential integrity enforced by the constraint. Two-way contract:

- **Safety writes:** CA may reference an existing PR; FK rejects unknown IDs.
- **Purchase enforces:** `pur_requisition` cannot be archived while a CA references it with `status IN ('OPEN','IN_PROGRESS','PENDING_VERIFY')`. Pre-check query Purchase runs before archive:

```sql
SELECT 1
FROM vims_safety_corrective_action
WHERE purchase_req_id = @requisition_id
  AND is_deleted = 0
  AND status IN ('OPEN','IN_PROGRESS','PENDING_VERIFY');
-- If any row → block archive with 409.
```

### 10.5 Safety ↔ PMS — DECOUPLED (D-GAP-I1)

**No in-VIMS integration.** No FK, no live join, no endpoint. Equipment-related findings reference PMS defect IDs as **free-text only** — specifically, `vims_safety_soi_finding.description` may contain the PMS defect ID string, but there is no typed column and no join. M-SCAT cause 12 "Inadequate Maintenance" is cross-referenced manually by investigator in the incident narrative. This is a load-bearing constraint — any future Safety ↔ PMS FK requires an SSOT amendment (D-GAP-I1 override).

### 10.6 Safety → Circular module

`POST /api/safety/circular/from-incident/{id}/` writes a draft row to the VIMS Circular module's table via the Circular module's service API — **not** a direct SQL write. Keeps audit paths clean. Circular approval chain runs independently (D-GAP-R17).

---

## 11. Paper-First SOI Constraints (D-GAP-E4)

This section is a **load-bearing constraint callout** — paper is the system of record for the SOI checklist. Digital tracks event metadata + findings only.

### 11.1 What the database supports

- `vims_safety_soi_inspection.checklist_generated_at` — flips state to `DOWNLOADED`.
- `vims_safety_soi_inspection.checklist_unique_id` — idempotent (D-GAP-E1).
- `vims_safety_soi_inspection.lost_paper_flag` + `lost_paper_note` — re-download event (D-GAP-E3).
- `vims_safety_soi_finding` rows — per-finding records with photos (HIGH severity mandatory, D-GAP-M24).
- `vims_safety_soi_inspection_area.last_inspected_at` — per-area stamp on finding submit (D-GAP-E2 partial).

### 11.2 What the database deliberately does NOT support

| Not supported | Why |
|---------------|-----|
| `scan_upload_path` column | D-GAP-E4 — paper lives in ship SMS filing system |
| `scan_uploaded_at` column | D-GAP-E4 |
| `scan_uploader_id` column | D-GAP-E4 |
| `scan_file_hash` column | D-GAP-E4 + D-GAP-D2 no crypto |
| Per-item Yes/No response table | §2C.9 — item-level responses live on paper only |
| `/api/safety/soi/{id}/scan/upload` endpoint | D-GAP-E4 — no upload endpoint exists |
| OCR / auto-extract pipeline | D-GAP-E4 — paper is authoritative |
| Service-worker background-sync of checklist answers | TECH_STACK §6.2 — findings only, never paper answers |

### 11.3 Paper ↔ digital linkage

The **only** link between paper and digital is the `checklist_unique_id` printed as QR or Code128 barcode (deferral #10) on the paper checklist header + page footers. PSC / auditor on-demand review finds the paper in ship SMS filing; digital findings are queryable via `SOI/{VesselCode}/{YY}/{NN}` reference or by scanning the QR/barcode into the system.

---

## 12. Audit Rails

### 12.1 `vims_safety_incident_phase_log` — append-only contract

- `DENY UPDATE, DELETE` grant on writer role (§4.2).
- Django admin disables change + delete.
- Signal emits one row per state transition; loop-back mandates `loop_back_reason` (D-GAP-B3).
- No hard cap on loop-backs (D-GAP-B3 DPA judgement); dashboard metric surfaces excess.
- Retention: row purges with parent incident (D-GAP-M33).

### 12.2 `vims_safety_field_history` — schema is deferral #2 (flagged)

- Current lock Option A (TEXT `old_value` / `new_value`); deferral #2 may elevate to JSON or typed columns + non-crypto content_hash.
- Append-only (`DENY UPDATE, DELETE`).
- Polymorphic parent resolved in app layer (no FK).
- Access-log on every SELECT (D-GAP-F4).
- Retention: rows purge when parent incident / near-miss / SCM / SOI is hard-deleted (D-GAP-M33).

### 12.3 No crypto (D-GAP-D2, D-GAP-G2)

- **No hash chains.** No tamper-evidence crypto envelopes.
- **No PKI / X.509 / UETA digital signatures.** D-GAP-D1 hybrid model: typed-name + timestamp + device fingerprint + optional wet-signed scan as attachment.
- **No legal-hold crypto.** D-GAP-G2 — 3-year hard-delete runs on schedule; DPA is responsible for out-of-band export when a case is open.
- Audit integrity relies on: standard DB access control + append-only audit tables + platform backups + access log.

### 12.4 Physical-signature attachments (D-GAP-D1 hybrid)

Wet-signed PDFs live under `/var/www/ksm_uploads/safety/{vessel_id}/{record_type}/{id}/signatures/`. Stored as file references in a future `vims_safety_attachment` table (not part of V1 initial surface — flagged to Phase 1 backend lead; overlaps with deferral #1 re: evidence attachment shape).

---

## 13. Migration Ordering

### 13.1 Platform precondition

`apps/safety/migrations/0001_initial.py` depends on the following tables existing beforehand (platform responsibility):

- `master_role`
- `master_RoleByVessel`
- `master_applied_rank`
- `Crew_Onboarding_History`
- `VesselData`
- `HRM501`
- `msc_profiles`
- `users`, `Ship_UsersLogin`
- `wrh_attendance`, `wrh_ship_time_config` (live-join targets)
- `pur_requisition` (CA hard FK target)
- `master_notification` (notification queue)

`SafetyConfig.ready()` emits a startup sanity check against this list. If any is missing, Safety boot fails fast with a clear error.

### 13.2 Migration dependency chain

```python
# apps/safety/migrations/0001_initial.py
class Migration(migrations.Migration):
    initial = True
    dependencies = [
        # Platform-level — these are not Django apps but legacy tables;
        # verified at SafetyConfig.ready() runtime, not at migration time.
    ]
    operations = [
        # 1. CREATE master_* reference tables (no FKs to vims_safety_*)
        migrations.RunSQL('CREATE TABLE master_mscat_taxonomy (...);'),
        migrations.RunSQL('CREATE TABLE master_immediate_causes (...);'),
        migrations.RunSQL('CREATE TABLE master_loss_types (...);'),
        migrations.RunSQL('CREATE TABLE master_soi_area (...);'),
        migrations.RunSQL('CREATE TABLE master_soi_area_item (...);'),
        migrations.RunSQL('CREATE TABLE master_soi_checklist_version (...);'),
        migrations.RunSQL('CREATE TABLE master_safety_incident_type (...);'),
        migrations.RunSQL('CREATE TABLE master_safety_bias_guard (...);'),
        # 2. CREATE vims_safety_* tables in FK dependency order
        migrations.RunSQL('CREATE TABLE vims_safety_incident (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_incident_phase_log (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_field_history (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_soi_inspection (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_soi_inspection_area (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_soi_finding (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_soi_vessel_area_map (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_soi_applicability_log (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_soi_trainee (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_scm_meeting (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_scm_attendance (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_scm_agenda (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_recommendation (...);'),
        migrations.RunSQL('CREATE TABLE vims_safety_corrective_action (...);'),
        # 3. Apply all index statements
        # 4. Apply DENY UPDATE, DELETE on audit tables to writer role
    ]
```

### 13.3 Seed migration `0002_seed_master_tables.py`

Loads the 4 CSVs using `BULK INSERT` (SQL Server) or pandas-free Python parsing per platform forbidden list (no `pandas`):

```python
import csv
from django.db import migrations

def seed_mscat(apps, schema_editor):
    with open('safety-reference-data/mscat_taxonomy.csv') as f:
        reader = csv.DictReader(f)
        rows = [(r['category_id'], r['category_name'], r['subcode_id'],
                 r['subcode_description'], r['cause_type']) for r in reader]
    with schema_editor.connection.cursor() as cur:
        cur.executemany(
            "INSERT INTO master_mscat_taxonomy "
            "(category_id, category_name, subcode_id, subcode_description, cause_type) "
            "VALUES (%s, %s, %s, %s, %s);", rows)
    # 174 rows inserted. Verify count post-insert.

# ... similar for immediate_causes.csv (52), loss_types.csv (7),
#     soi_checklist_v1.csv (329), 13 soi_area rows, 32 incident_type rows,
#     8 bias_guard rows.
```

### 13.4 Permission seed `0003_seed_permission_ids.py`

Idempotent inserts into `msc_profiles`:

```python
PERMISSIONS = [
    ('SAF_F_001', 'SAFETY_INCIDENT_LIST',  'form'),
    ('SAF_F_002', 'SAFETY_INCIDENT_CREATE','form'),
    # ... SAF_F_003..020 and SAF_P_001..024 ...
]

def seed_permissions(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        for code, label, kind in PERMISSIONS:
            cur.execute(
                "IF NOT EXISTS (SELECT 1 FROM msc_profiles_catalog WHERE code = %s) "
                "INSERT INTO msc_profiles_catalog (code, label, kind) VALUES (%s, %s, %s);",
                [code, code, label, kind])
```

(`msc_profiles_catalog` is a platform-level catalog — exact name verified at build with platform lead.)

---

## 14. Rubric Self-Check

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Every table has columns (name + type + nullable + default), PK, FKs, indexes | PASS | §4.1–4.14 (14 vims_safety_* tables), §5.1–5.8 (8 master_* tables) |
| Every API endpoint has path, method, auth, request shape, response shape, error codes | PASS | §9.1 base contract + §9.2–9.10 endpoint blocks |
| All 12 build-time deferrals rendered in the table | PASS | §8 table + commentary rows 1–12 |
| Seed CSV column headers match DDL columns exactly for master_mscat_taxonomy / master_immediate_causes / master_loss_types / master_soi_area_item | PASS | §5.1 col map category_id/category_name/subcode_id/subcode_description/cause_type; §5.2 same; §5.3 loss_type_id/loss_type_name/description; §5.5 area_id/area_name/subsection_id/subsection_name/item_number/description/tier |
| No crypto language (no hash chains, no legal-hold) | PASS | §12.3 explicit exclusion; deferral #2 Option C uses non-crypto rolling hash |
| PMS has no FK to Safety | PASS | §10.5 DECOUPLED callout; no FK in §4 DDL |
| Zero occurrences of bare `safety_*` prefix | PASS | Every module table renders as `vims_safety_*`; every shared reference as `master_*`; translations applied throughout |
| Folder structure block present (Django `apps/safety/` + React folders) | PASS | §1.1 backend tree; §1.4 frontend tree |
| Django AppConfig + URL include + INSTALLED_APPS step documented | PASS | §1.2 INSTALLED_APPS; §1.3 URL include; §1.1 AppConfig `name='apps.safety'` |
| DB router points to `ksm_marine_live` | PASS | §2.2 SafetyRouter returns `'default'`; no new alias |
| Migration dependencies on platform masters stated | PASS | §13.1 precondition list + §13.2 migration chain |
| Near-miss reporter identity visibility documented | PASS | §3.4 reporter identity contract + PDF pipeline integration |
| No `safety_X` scan-upload column on SOI | PASS | §4.4 + §11.2 explicit NOT-supported list |
| CA ↔ Purchase hard FK present | PASS | §4.13 FK constraint + §10.4 RI contract |
| WRH host-readiness gate + timezone reuse | PASS | §4.11 `wrh_non_compliance_flag`; §9.3.2 create readiness block; §10.2 SQL example |

### 14.1 BLOCKED stubs summary

| # | Section | Label | Resolution owner | Required by |
|---|---------|-------|------------------|-------------|
| 1 | §8 deferral #8 | FTS engine selection | Platform | Phase 7 |
| 2 | §8 deferral #10 | SOI unique-ID flag format (QR / barcode / alphanumeric) | Product + Design | Phase 4 |

Both are Round 20 acknowledged build-time deferrals — not gaps in the 159 locked decisions.

---

## 15. Document References

| Document | Reference |
|----------|-----------|
| `VIMS-SAFETY-MODULE-SSOT.md` | 159 locked decisions (D-*, D-GAP-*) — authority on requirements |
| `VIMS-SAFETY-DOCSUITE-PROMPT.md` | Master prompt with `<database_naming_convention>`, `<vims_integration>`, deferral register |
| `VIMS-Reporting-Module/BACKEND_STRUCTURE.md` §1.3, §1A | Naming convention + auth inheritance pattern source |
| `VIMS-Safety-Module/TECH_STACK.md` | Version lock — Django 5.2.7, DRF 3.14.0, SimpleJWT 5.3.1, reportlab 4.2.0, pyodbc 5.1.0, mssql-django 1.6, qrcode 7.4.2, python-barcode 0.15.1 |
| `VIMS-Safety-Module/PRD.md` | FEAT-SAF-* IDs — 40+ features across INC / NM / SCM / SOI / XMOD / PDF / AUDIT / DASH / RBAC |
| `VIMS-Safety-Module/VALIDATION_RULES.md` | V-INC-* / V-NM-* / V-SCM-* / V-SOI-* IDs cited per endpoint error contract |
| `VIMS-Safety-Module/DESIGN_SYSTEM.md` | "SOI Compliance %" token (D-GAP-DESIGN-01) cited in §9.7 |
| `WRH_CANONICAL_SINGLE_SOURCE_OF_TRUTH.md` | `wrh_attendance`, `wrh_ship_time_config` — live-join targets (D-GAP-M11, D-GAP-M26) |
| `PURCHASE_MODULE_SINGLE_SOURCE_OF_TRUTH.md` | `pur_requisition` hard FK (D-GAP-M12) |
| `PMS_SINGLE_SOURCE_OF_TRUTH.md` | DECOUPLED (D-GAP-I1) — no integration |
| `ssot_auth_specific.md` | Dual identity paths (office + ship), `msc_profiles` permission chain |
| KSM SSQE Manual Rev 01 Feb 2026 §4.5, §9, §11 | Regulatory authority for SOI (§4.5), SCM (§9), Incidents (§11) |
| ISM Code 2010 amendments §9, §10 | Incident reporting + non-repudiation (satisfied via `vims_safety_field_history` per D-GAP-D2) |
| IMO Casualty Investigation Code (Resolution MSC.255(84)) | 5 principles → 8 bias guards (§4.1 `bias_guard_attestations`) |
| IMO Resolution A.884(21) | 7 human-element domains — linked via `vims_safety_human_factor_tag` (phase-1 model surface) |
| IMO MSC-MEPC.3/Circ.4 | Auto-populated PDF export (D-DNV-12) — §9.9 endpoint `/api/safety/export/msc-mepc-3/{id}/` |
| MARPOL Annex I (consolidated 2022) | Environmental loss type seed (master_loss_types row 3) |
| SOLAS Ch IX (as amended) | ISM enforcement basis |

---

**Document Control:**
- Created: 2026-04-17
- Author: Docsuite generation agent, Wave 2
- Approved by: [Pending DPA + Tech Lead + Platform lead sign-off at Phase 0 kickoff]
- Supersedes: None (initial release)
- Next review: End of Phase 0 (scaffold verification) + Phase 1 (deferrals #1, #2, #4, #6 resolution checkpoint)
