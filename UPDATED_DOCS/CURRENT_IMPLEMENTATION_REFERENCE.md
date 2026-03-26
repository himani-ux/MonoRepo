# CURRENT_IMPLEMENTATION_REFERENCE.md
## VIMS Inspection Current Snapshot
**Date:** 2026-03-26

This document was added in `UPDATED_DOCS` to capture the current implementation snapshot without changing the original `Docs` baseline files.

---

## 1. Frontend Route Snapshot

| Route | Current Behavior | Source |
|------|------------------|--------|
| `/` | Redirects authenticated users to `/dashboard` when they have dashboard permission, otherwise `/cars` | `psc-frontend/src/App.tsx` |
| `/login` | Public login route | `psc-frontend/src/routes/login.tsx` |
| `/dashboard` | KPI dashboard with vessel drill-down for office users | `psc-frontend/src/routes/dashboard/index.tsx` |
| `/inspections` | Inspection list with filters and Excel export | `psc-frontend/src/routes/inspections/index.tsx` |
| `/inspections/new` | Create inspection | `psc-frontend/src/routes/inspections/new.tsx` |
| `/inspections/:id` | Inspection detail | `psc-frontend/src/routes/inspections/[id].tsx` |
| `/inspections/:id/edit` | Edit inspection | `psc-frontend/src/routes/inspections/[id].edit.tsx` |
| `/inspections/:id/follow-up` | Follow-up workflow | `psc-frontend/src/routes/inspections/[id].follow-up.tsx` |
| `/deficiencies` | Deficiency workflow dashboard | `psc-frontend/src/routes/deficiencies/index.tsx` |
| `/cars` | CAR list | `psc-frontend/src/routes/cars/index.tsx` |
| `/cars/:id` | CAR detail | `psc-frontend/src/routes/cars/[id].tsx` |
| `/cars/:id/edit` | Edit CAR | `psc-frontend/src/routes/cars/[id].edit.tsx` |
| `/notifications` | Notification center | `psc-frontend/src/routes/notifications/page.tsx` |
| `/reports` | DefIntel/OpenSource workspace | `psc-frontend/src/routes/reports/page.tsx` |
| `/settings` | Company logo settings page | `psc-frontend/src/routes/settings/page.tsx` |
| `/circular/*` | Integrated Circular module inside the shared VIMS shell. Office users see the Circular office/admin/user workflow; ship users see the ship dashboard. | `psc-frontend/src/routes/circular/page.tsx`, `psc-frontend/src/legacy/vims-basic/routes/circular/CircularRoutes.jsx` |
| `/orb/*` | Integrated ORB module. Vessel users use the legacy ORB route tree, including dashboard, all entries, approved/rejected/deleted entries, PDF archive, and guidelines; office users see the native approved-entries page. | `psc-frontend/src/routes/orb/page.tsx`, `psc-frontend/src/legacy/vims-basic/routes/orb/OrbRoutes.jsx`, `psc-frontend/src/routes/orb/office-approved-entries.tsx` |
| `/sync` | Offline/sync status page | `psc-frontend/src/routes/sync/page.tsx` |

---

## 2. Backend Route Snapshot

All backend APIs are rooted under `/api/psc/`.

| Prefix | Key Current Endpoints |
|------|------------------------|
| `/auth/` | `login/`, `refresh/`, `logout/`, `me/`, `crew/`, `company-logo/` |
| `/masters/` | `mou/`, `psc-action-codes/`, `pic/`, `psc-def-categories/`, `psc-def-codes/`, `clc-categories/`, `clc/`, `clc/hierarchy/` |
| `/inspections/` | list/create, detail/update/delete, `submit/`, `pic-review/`, `dpa-close/`, `upload-report/`, `deficiencies/`, `deficiencies/bulk-submit/`, `follow-up/`, `cars/export-pdf/`, `export-excel/` |
| `/deficiencies/` | list, `action-code/`, `workflow/`, `allocate/` |
| `/cars/` | list/detail/update, `workflow/`, `available-actions/`, legacy transition endpoints, evidence/action/PV create, `export-pdf/` |
| `/evidence/` | `GET <id>/view/`, `DELETE <id>/` |
| `/actions/` | update, complete, soft-delete |
| `/physical-verifications/` | update, close |
| `/sync/` | pull, push, upload, resolve-conflict, conflicts |
| `/dashboard/` | aggregate dashboard response |
| `/reports/` | OpenSource import, vessel prep preview/export, DefIntel prediction |
| `/notifications/` | list, mark-read, mark-all-read |
| `/api/circular/` | Circular office and ship backend endpoints, including document lookup, authoring, delivery tracking, acknowledgments, and PDF reporting | `psc-backend/modules/circular/circular_office/urls.py`, `psc-backend/modules/circular/circular_ship/urls.py` |
| `/api/orb/` | ORB backend endpoints for vessel lookup, entry lifecycle, approval/rejection, archive listing, and PDF metadata | `psc-backend/modules/orb/orb/urls.py` |

---

## 3. Role and Permission Snapshot

Current role codes used in frontend/backend:

- `VESSEL_MASTER`
- `VESSEL_CREW`
- `OFFICE_PIC`
- `OFFICE_SSQE`
- `OFFICE_SUPT`
- `DPA`
- `PHYSICAL_VERIFIER`

Current frontend process guards:

- `PSC_P_001` View dashboard
- `PSC_P_002` View inspections
- `PSC_P_003` Create inspection
- `PSC_P_004` View inspection detail
- `PSC_P_005` Edit inspection
- `PSC_P_006` Submit follow-up
- `PSC_P_007` View deficiencies
- `PSC_P_008` Allocate deficiency
- `PSC_P_009` View CARs
- `PSC_P_010` Edit CAR
- `PSC_P_011` CAR workflow
- `PSC_P_012` View notifications
- `PSC_P_013` Manage notifications
- `PSC_P_014` View sync
- `PSC_P_015` View reports
- `PSC_P_016` View settings

Current frontend form guards:

- `PSC_F_001` Dashboard
- `PSC_F_002` Inspections
- `PSC_F_003` Deficiencies
- `PSC_F_004` CARs
- `PSC_F_005` Notifications
- `PSC_F_006` Sync
- `PSC_F_007` Reports
- `PSC_F_008` Settings

Module access rules:

- Inspection uses `form_ids` for sidebar and bottom-nav visibility, while `process_ids` gate the screen actions within each inspection workflow
- `msc_profiles` is the database source that carries the `form_ids` and `process_ids` consumed by the frontend guards
- Circular legacy permission gates are organized per screen as follows:

  | Circular Screen / Area | `form_ids` | `process_ids` |
  |---|---|---|
  | Office / admin workspace | `PSC_F_009` | `PSC_P_017`, `PSC_P_018`, `PSC_P_019`, `PSC_P_024` |
  | Overlay / modal workspace | `PSC_F_010` | - |
  | Follow-up / approval panel | `PSC_F_011` | `PSC_P_025`, `PSC_P_026`, `PSC_P_027` |
  | Dashboard filters | `PSC_F_012` | `PSC_P_028`, `PSC_P_029` |
  | Notifications workspace | `PSC_F_013` | `PSC_P_030`, `PSC_P_031`, `PSC_P_032`, `PSC_P_033`, `PSC_P_034`, `PSC_P_035`, `PSC_P_036` |
  | Approved notifications library actions | - | `PSC_P_020`, `PSC_P_021`, `PSC_P_022`, `PSC_P_023` |
- ORB legacy permission gates are organized per screen as follows:

  | ORB Screen / Area | `form_ids` | `process_ids` |
  |---|---|---|
  | Entry form | `PSC_F_014` | `PSC_P_043` |
  | Draft / table workspace | `PSC_F_015` | `PSC_P_037`, `PSC_P_038` |
  | Pending entries view | `PSC_F_016` | `PSC_P_040`, `PSC_P_041` |
  | Approved entries view | `PSC_F_017` | `PSC_P_042` |
  | Report filter | `PSC_F_018` | `PSC_P_039` |
  | Report view | `PSC_F_019` | - |
- Circular access is split by legacy `user_type`: office users see the office routes and ship users see the ship dashboard and document viewer flows
- ORB access is split by legacy `user_type`: vessel users see the legacy ORB route tree and office users see the native approved-entries page

Access notes:

- office users are filtered by `master_RoleByVessel` unless they resolve as global PIC/DPA reviewers
- global reviewer mapping is derived from `mapping_role_user`, `msc_profiles`, and `Mapping_CrewAssReviewers`
- DefIntel report access is broader than OpenSource import access:
  - reports: office users + vessel Master/CO/CE/2E categories
  - OpenSource import: office users only

---

## 4. Live Table Snapshot

Live PSC tables confirmed in `ksm_inspection`:

- `psc_inspection`
- `psc_inspection_report`
- `psc_deficiency`
- `psc_deficiency_action_history`
- `psc_car`
- `psc_car_clc_mapping`
- `psc_corrective_action`
- `psc_evidence`
- `psc_physical_verification`
- `psc_activity_history`
- `psc_audit_log`
- `psc_notification`
- `psc_sync_log`
- `psc_sync_log_detail`
- `psc_sync_conflict`
- `psc_sync_token`
- `psc_opensource_import_run`
- `psc_opensource_deficiency_record`

Shared/reference tables actively used by the current code:

- `VesselData`
- `HRM501`
- `users`
- `master_RoleByVessel`
- `mapping_role_user`
- `master_role`
- `msc_profiles`
- `Mapping_CrewAssReviewers`
- `Crew_Onboarding_History`
- `MOU_Master`
- `PSC_Action_Codes`
- `PIC_Master`
- `PSC_Def_Category`
- `PSC_Def_Subcategory`
- `PSC_Def_Code`
- `CLC_Category`
- `CLC_Item`

## 5. Module Integration Snapshot

- the merged frontend is still a single authenticated VIMS shell, with Inspection as the base module and Circular/ORB mounted as nested route trees
- `Header` now renders module-specific actions for `/circular` and `/orb` paths without changing the global notifications or user menu
- `LegacyBasicProvider` bridges modern auth into the legacy stores and maps modern vessel users to legacy `ship` users so the embedded Circular and ORB routes continue to work
- the backend module packages live under `psc-backend/modules/circular/` and `psc-backend/modules/orb/`, and they continue to use the same `ksm_inspection` database as the base Inspection module
