# Later Changes Record

Last updated: 2026-03-26

This file records implementation changes that were made later on after the initial v1.0 documentation baseline in `docs/APP_FLOW.md` (2026-02-03) and `docs/BACKEND_STRUCTURE.md` (2026-02-04).

Where older baseline sections differ from the current code, the later changes in this file and the updated summary sections in the canonical docs take precedence.

## 1. Backend Functions and Endpoints Added Later

- Dashboard aggregation endpoint added:
  - `GET /api/psc/dashboard/`
  - backend file: `psc-backend/apps/inspection/dashboard_views.py`
- DefIntel/OpenSource reporting endpoints added:
  - `POST /api/psc/reports/opensource/import/`
  - `POST /api/psc/reports/vessel-prep/preview/`
  - `POST /api/psc/reports/vessel-prep/export/`
  - `GET /api/psc/reports/defintel/predict-defcodes/`
  - backend files: `psc-backend/apps/inspection/defintel_views.py`, `psc-backend/apps/inspection/defintel_checklist.py`, `psc-backend/apps/inspection/defintel_prediction.py`, `psc-backend/apps/inspection/urls_reports.py`
- Auth support endpoints added:
  - `GET /api/psc/auth/crew/?vessel_id=<uuid>`
  - `GET /api/psc/auth/company-logo/`
  - `POST /api/psc/auth/company-logo/`
  - `GET /api/psc/auth/me/` now returns `has_global_vessel_access`
- Additional implemented workflow/export endpoints now confirmed in the live code:
  - `POST /api/psc/inspections/<inspection_id>/deficiencies/bulk-submit/`
  - `POST /api/psc/inspections/<inspection_id>/follow-up/`
  - `GET /api/psc/inspections/<inspection_id>/cars/export-pdf/`
  - `GET /api/psc/inspections/export-excel/`
  - `GET /api/psc/deficiencies/`
  - `POST /api/psc/deficiencies/<id>/workflow/`
  - `POST /api/psc/deficiencies/<id>/allocate/`
  - `POST /api/psc/cars/<id>/workflow/`
  - `GET /api/psc/cars/<id>/available-actions/`
  - `GET /api/psc/cars/<id>/export-pdf/`
  - `GET /api/psc/evidence/<id>/view/`

## 2. Tables and Mapping Added or Used Later

### Existing shared tables now used by auth, permissions, and mapping

- `master_role`
- `mapping_role_user`
- `msc_profiles`
- `Mapping_CrewAssReviewers`
- `Crew_Onboarding_History`
- `Ship_UsersLogin`

### PSC tables added later for DefIntel/OpenSource data

- `psc_opensource_import_run`
- `psc_opensource_deficiency_record`

### Later-added office reviewer mapping logic

Office global reviewer resolution now uses:

`mapping_role_user.role_id -> msc_profiles.profile_id -> Mapping_CrewAssReviewers.PIC_RoleId / DPA_RoleId`

Implemented effect:

- global PIC users resolve to `OFFICE_PIC`
- global DPA users resolve to `DPA`
- mapped global reviewers get `has_global_vessel_access = true`
- non-global office users continue to use vessel-scoped filtering through `master_RoleByVessel`

## 3. Frontend Screens and Files Added Later

### New route screens

- `psc-frontend/src/routes/dashboard/index.tsx`
- `psc-frontend/src/routes/deficiencies/index.tsx`
- `psc-frontend/src/routes/reports/page.tsx`
- `psc-frontend/src/routes/settings/page.tsx`

### Supporting frontend modules added later

- `psc-frontend/src/lib/api/dashboard.ts`
- `psc-frontend/src/lib/api/reports.ts`
- `psc-frontend/src/lib/api/settings.ts`
- `psc-frontend/src/hooks/use-dashboard.ts`
- `psc-frontend/src/components/dashboard/*`

## 4. Workflow and Access Changes Added Later

- Default landing route changed later:
  - users with dashboard permission land on `/dashboard`
  - users without dashboard permission land on `/cars`
- A dedicated deficiency workflow screen was added later at `/deficiencies`
- Reports access was expanded later:
  - all office users can access reports
  - vessel users in Master, CO, CE, and 2/E categories can access reports
  - OpenSource import remains office-only
- Company logo upload is currently enforced for office users generally in backend code; vessel users remain read-only
- CAR workflow was changed later to the unified status model:
  - `ALLOTTED -> IN_PROGRESS -> PENDING_CE_REVIEW -> PENDING_MASTER_REVIEW -> SUBMITTED_TO_PIC -> PIC_REVIEW -> SUBMITTED_TO_DPA -> CLOSED`

## 5. Related Working Files Added Later

These files are part of the later implementation context and data/mapping review work:

- `new_tables.md`
- `mapping_role_user.json`
- `master_role.json`
- `msc_profiles.json`
- `psc-backend/master_role_export.sql`
- `psc-backend/mapping_role_user_export.sql`
- `psc-backend/msc_profiles_export.sql`

## 6. Circular and ORB Module Integration

- `psc-frontend/src/App.tsx` now mounts `/circular/*` and `/orb/*` as authenticated module roots inside the existing VIMS shell
- `psc-frontend/src/components/layout/header.tsx` now renders `CircularHeaderActions` and `OrbHeaderActions` when the current pathname belongs to those modules
- `psc-frontend/src/legacy/vims-basic/module-provider.tsx` bridges modern auth into the legacy stores and maps modern vessel users to legacy `ship` users
- `psc-frontend/src/routes/circular/page.tsx` keeps Circular inside `LegacyBasicProvider` + `RootLayout` for both office and ship users
- `psc-frontend/src/routes/orb/page.tsx` keeps vessel ORB users on the legacy route tree and sends office users to the native approved-entries page
- no new backend API family was introduced for the merged modules; the integration is primarily frontend routing, shared shell composition, and legacy auth bridging
- the backend module packages are live under `psc-backend/modules/circular/` and `psc-backend/modules/orb/`, and both continue to use the shared `ksm_inspection` database
