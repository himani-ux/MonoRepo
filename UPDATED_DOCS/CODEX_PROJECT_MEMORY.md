# CODEX Project Memory

Last updated: 2026-03-09 (IST)
Workspace: `C:\Users\himan\Downloads\VIMS_Inspection_deployed\VIMS_Inspection`

## Session Guardrails

- User instruction captured: do not modify database or code unless explicitly requested.
- Database connection reference reviewed from `psc-backend/core/settings.py`.
- No database write operations were performed in this review.

## What Was Reviewed

### 1) Database configuration reference

- File: `psc-backend/core/settings.py`
- Lines:
  - `100-116`: SQL Server database config block (`DATABASES`).
  - `106`: engine `mssql`
  - `107`: database name `ksm_marine_live`
  - `112-113`: ODBC Driver 18 + trusted connection parameters

### 2) Role model and mapping tables

- File: `psc-backend/apps/accounts/models.py`
- Lines:
  - `100-116`: `MasterRoleByVessel` (db table `master_RoleByVessel`)
  - `144-161`: `MappingRoleUser` (db table `mapping_role_user`)
  - `220-238`: `RoleCodes` and reviewer groups
    - `PIC_REVIEWERS = [OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT]`

### 3) Office authentication and role assignment

- File: `psc-backend/apps/accounts/backends.py`
- Lines:
  - `319-348`: `_authenticate_office_user(...)`
    - Office user loaded by username/employee_id from users table.
    - Role is set to:
      - `DPA` if `_is_dpa_role_assignment(...)` is true
      - else default `OFFICE_PIC`
  - `378-406`: `_is_dpa_role_assignment(...)`
    - checks `mapping_role_user` joined with `Mapping_CrewAssReviewers.DPA_RoleId`

- File: `psc-backend/apps/accounts/utils.py`
- Lines:
  - `185-213`: `get_office_permissions_by_mapping(...)`
    - permissions resolved via `mapping_role_user -> master_role -> msc_profiles`

### 4) Vessel-wise access for office users

- File: `psc-backend/core/vessel_access.py`
- Lines:
  - `55-95`: `apply_office_vessel_filter(...)`
    - office + `DPA`: no vessel filter
    - other office roles: filtered by vessel assignments from `master_RoleByVessel`
    - no assignments: empty queryset (safety)

- File: `psc-backend/apps/inspection/permissions.py`
- Lines:
  - `298-307`: office object-level vessel access check through `get_office_user_vessel_ids(...)`

- `apply_office_vessel_filter(...)` usage found in:
  - `psc-backend/apps/inspection/views.py:149`
  - `psc-backend/apps/inspection/deficiency_views.py:765,778`
  - `psc-backend/apps/inspection/report_views.py:72`
  - `psc-backend/apps/inspection/dashboard_views.py:76,77,80,83`
  - `psc-backend/apps/inspection/defintel_checklist.py:206`
  - `psc-backend/apps/car/views.py:278,293`

### 5) CAR PIC visibility and workflow behavior

- File: `psc-backend/apps/car/views.py`
- Lines:
  - `275-287`: PIC list query behavior
    - for office PIC reviewers, queryset = `vessel-scoped cars` UNION `PIC inbox statuses`
    - PIC inbox statuses included: `SUBMITTED_TO_PIC`, `PIC_REVIEW`
  - `438-476`: `CARDetailView.get(...)`
    - explicit vessel mismatch guard exists for vessel users
    - no equivalent explicit office vessel guard in this method
  - `877-912`: `CARWorkflowView.post(...)`
    - transition eligibility delegated to `validate_workflow_transition(...)`

- File: `psc-backend/apps/car/permissions.py`
- Lines:
  - `38-44`: `CanEditCAR` allows all office users at object-level
  - `107-126`: `CanPICAcceptCAR` is role/status based (`OFFICE_PIC/OFFICE_SSQE/OFFICE_SUPT`)

- File: `psc-backend/apps/inspection/workflow.py`
- Lines:
  - `257-274`: `_get_user_workflow_roles(...)`
    - office `OFFICE_PIC/OFFICE_SSQE/OFFICE_SUPT` -> workflow role `pic`
    - office `DPA` -> workflow role `dpa`
  - `365-384`: `get_available_actions(...)` returns `comment_required` per action
  - `339-340`: transition fails if required comment missing

## Answer Captured: PIC mapping vessel-wise?

Current understanding from code:

- PIC mapping is primarily role-based at auth/workflow level.
- Vessel-wise access is a separate layer via `master_RoleByVessel` filters.
- For CAR list specifically, PIC reviewers intentionally get inbox statuses even if outside normal vessel-scoped subset due to union logic in `CARListView`.

## Change Record (Done on Request)

Requested behavior:
- When PIC clicks "SUBMIT TO DPA", comment box should always be shown/required.

Change made:
- File: `psc-backend/apps/inspection/workflow.py`
- Exact lines: `221-224`
- Transition:
  - `(CARStatus.PIC_REVIEW, WorkflowAction.SUBMIT_TO_DPA)`
  - `comment_required` is set to `True`

Why this enforces UI behavior:
- `get_available_actions(...)` exposes `comment_required` (`365-384`).
- `validate_workflow_transition(...)` hard-validates comment presence (`339-340`).

## Pending Topic at Time of This Note

- User asked: "how does the PIC is being mapped, is it vessel wise?"
- This document includes the traced answer and source references.

## Update: Global PIC/DPA Mapping (2026-03-09)

User request implemented:
- Remove PIC/DPA dependence on `master_RoleByVessel`.
- Map global PIC/DPA using:
  - `mapping_role_user.role_id`
  - `msc_profiles.profile_id`
  - `Mapping_CrewAssReviewers.PIC_RoleId` / `Mapping_CrewAssReviewers.DPA_RoleId`

Implemented behavior:
- If user profile is in `DPA_RoleId` -> role `DPA` and global vessel access.
- If user profile is in `PIC_RoleId` -> role `OFFICE_PIC` and global vessel access.
- Otherwise office role remains default `OFFICE_PIC` but stays vessel-scoped (legacy behavior).
- Global reviewer access now bypasses vessel filters consistently (list/object/dashboard).

Files changed:
- `psc-backend/apps/accounts/utils.py`
  - Added `get_office_global_reviewer_role(...)` helper (profile-based PIC/DPA mapping).
- `psc-backend/apps/accounts/backends.py`
  - Office auth now resolves global reviewer role via mapping helper.
  - Added `has_global_vessel_access` on `AuthenticatedUser`.
- `psc-backend/apps/accounts/serializers.py`
  - Added JWT claim support for `has_global_vessel_access`.
- `psc-backend/apps/accounts/views.py`
  - `GET /auth/me` now includes `has_global_vessel_access`.
- `psc-backend/core/vessel_access.py`
  - Added `get_office_user_identifiers(...)`.
  - Added `has_global_office_vessel_access(...)`.
  - `apply_office_vessel_filter(...)` now bypasses for global PIC/DPA.
- `psc-backend/apps/inspection/permissions.py`
  - `HasVesselAccess` updated to allow global PIC/DPA object access.
- `psc-backend/apps/inspection/dashboard_views.py`
  - Vessel dropdown now returns all active vessels for global PIC/DPA.
- `psc-backend/core/test_vessel_access.py`
  - Reworked tests for new global access + filtering behavior.

Validation run:
- `manage.py test core.test_vessel_access --settings=core.settings_test` -> passed.
- `manage.py test apps.accounts.tests --settings=core.settings_test` -> passed.
