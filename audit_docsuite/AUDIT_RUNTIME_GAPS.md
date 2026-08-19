# Audit Runtime Gaps

Date: 2026-08-14

This file records runtime/setup gaps found while trying to run the completed
Audit build locally. It is an operational note, not a release claim and not a
change to the frozen SSOT or `docs/IMPLEMENTATION_PLAN.md`.

## 1. `msc_profiles` Audit Permission Seeding Gap

Observed issue:

- DPA login succeeds, but Audit tabs are not visible in the sidebar.
- `msc_profiles` does not currently contain the Audit module permission IDs
  needed by the frontend/backend permission checks.
- The missing values include Audit process IDs such as `AUDIT_P_001`,
  `AUDIT_P_005`, `AUDIT_P_006`, `AUDIT_P_013`, `AUDIT_P_014`,
  `AUDIT_P_016`, and `AUDIT_P_018` for DPA.
- Audit is process-gated through `AUDIT_P_*`; it is not enough to rely on
  existing PSC/Safety/Certs form IDs.

Impact:

- A DPA user can authenticate but may not see Audit navigation.
- Audit route guards that call `hasProcess(...)` may also deny access if the
  login payload has no Audit process IDs.

Code mitigation applied:

- Frontend auth now derives effective Audit `AUDIT_P_*` process IDs from the
  documented role/designation mapping when `msc_profiles.process_ids` does not
  include Audit grants.
- Backend Audit permission helpers now merge explicit process IDs with the
  same documented role/designation defaults, so API guards use the same
  effective-gate model as the sidebar.
- Verification: focused frontend auth/sidebar tests passed, frontend
  type-check passed, Django startup check passed, backend permission tests
  passed, and the full Audit backend suite passed.

Required follow-up:

- Do not blindly seed by the documented designation labels. The earlier
  shorthand "DPA/SEQ Manager/Lead Auditor/Conductor/Office Supt/FM/Master/HoD"
  is not a valid `msc_profiles` seed plan by itself because the live profile
  table may not contain literal rows named `Lead Auditor` or `Conductor`.
- `Lead Auditor` and `Conductor` are audit assignment/designation concepts;
  they may be selected per audit or derived from qualified-auditor / team
  assignment data, not from standalone auth-profile rows.
- First inspect the actual `msc_profiles` rows and the real login/profile
  tokens used by office and vessel users. Then produce an explicit additive
  merge map from real profile row -> Audit `AUDIT_P_*` process IDs.
- Seed or merge the documented Audit permission IDs only into confirmed
  existing profiles/users. Preserve all existing PSC/Safety/Certs `form_ids`
  and `process_ids`; append Audit IDs only where the real profile/user mapping
  proves that role should have Audit inputs.
- Do this as an additive permission-data update only. Do not mutate protected
  PSC tables and do not edit the frozen SSOT.

Why the previous seed logic is wrong:

- It assumes `msc_profiles` has one row per Audit workflow label.
- In reality, labels such as `Lead Auditor` and `Conductor` are not guaranteed
  to be profile rows. They are contextual Audit responsibilities assigned to
  existing office users.
- Lead Auditor is selected per audit from qualified-auditor / audit-team data;
  it can change from audit to audit. Therefore a fixed `msc_profiles` row
  cannot safely represent "the Lead Auditor" for all audits unless KSM's real
  auth model already has a broader office profile intended to hold those gates.
- This creates a real model mismatch: some Audit permissions are stable
  profile-level authorities, while other Audit actions must be checked against
  per-audit assignment data. Treating both as permanent profile grants can
  over-grant access.
- A safe seed cannot be generated from the RBAC role table alone. It must be
  generated from the actual production profile rows and the way KSM identifies
  DPA, SEQ, office superintendent, vessel master, HoD, and audit-team users at
  login/runtime.

New required investigation before any seed:

- Learn the actual `msc_profiles` table format and data pattern first:
  column meanings, row naming conventions, how `form_ids` and `process_ids`
  are stored, how rows relate to `users`, `employee_role`, vessel users, and
  office profiles, and whether there are generic office profiles rather than
  per-audit labels.
- Produce a read-only profile inventory before writing anything:
  profile id/name, role/work-side fields, current `form_ids`, current
  `process_ids`, sample linked users, and whether the row is shared by many
  users.
- After that inventory, separate permanent profile grants from contextual
  assignment checks. DPA/SEQ/FM/Master/HoD may be profile-derived if real rows
  support that; Lead Auditor and Conductor should likely remain per-audit
  assignment-derived unless the live auth data proves otherwise.

Resolution package finding reviewed 2026-08-16:

- `C:\Users\himan\Downloads\AUDIT-GAPS-RESOLUTION` includes a proposed
  response based on a real but stale `msc_profiles_export.sql` from
  2026-02-27. That export reportedly has 41 profile rows and confirms there
  are no literal profile rows named `Lead Auditor`, `Conductor`, `DPA`, or
  `HoD`.
- The draft static seed map in that package is limited to stable
  profile-level rows such as `SEQ Manager`, `Fleet Manager`, and `MASTER`,
  with explicit caveats around `AUDIT_P_013`, `AUDIT_P_004`, and
  `AUDIT_P_007`.
- This does not close the seed gap. The export is stale and must be re-pulled
  from the current live DB before any update. The safe seed cannot include
  per-audit roles such as Lead Auditor/Conductor as fixed profile grants.

Live DB additive update applied 2026-08-16:

- Connected to `ksm_marine_live` on SQL Server `HIMANI` and inspected the live
  `dbo.msc_profiles` table: 52 profile rows, columns
  `id`, `profile_id`, `profile_name`, `work_side`, `form_ids`,
  `process_ids`, `created_on`, `is_active`, `is_deleted`.
- Backed up the eight affected rows before update to:
  `tmp/db-backups/msc_profiles_audit_permissions_backup_20260816_204059.json`.
- Updated only `process_ids`. No `form_ids` were changed. No rows were added.
  No fake `Lead Auditor`, `Conductor`, `DPA`, or `HoD` profile rows were
  created.
- Additive Audit IDs inserted:
  - `SEQ Manager`: `AUDIT_P_001`, `005`, `006`, `007`, `009`, `010`, `011`,
    `012`, `013`, `014`, `016`, `018`
  - `Fleet Manager`: `AUDIT_P_016`
  - `MASTER`: `AUDIT_P_008`, `017`
  - `Marine Superintendent`: `AUDIT_P_004`, `007`
  - `Technical Superintendent`: `AUDIT_P_004`, `007`
  - `Senior Technical Superintendent`: `AUDIT_P_004`, `007`
  - `admin`: full Audit gate set `AUDIT_P_001..014`, `016`, `017`, `018`
  - `Super Admin`: full Audit gate set `AUDIT_P_001..014`, `016`, `017`,
    `018`
- Verification after update confirmed all old `process_ids` remained present
  and all `form_ids` were unchanged for those eight rows.

Assignment-scoped permission resolution applied 2026-08-17:

- Lead Auditor, Conductor, and office HoD are no longer treated as static
  fallback profile grants.
- Backend Audit permission helpers now derive audit-specific gates from the
  current audit record:
  - `AuditDetail.lead_auditor_user_id` grants Lead Auditor gates for that
    audit only.
  - `AuditDetail.conductor_user_id` grants Conduct gates for that audit only.
  - active `MasterHodAssignment` for `AuditDetail.auditee_office_dept` grants
    HoD signing gates for that office audit only.
- Record-level Audit endpoints now load the audit/finding first, then evaluate
  the user's effective permissions for that audit. Stable global profile gates
  from `msc_profiles` still apply for DPA, SEQ, Fleet Manager, Master, and
  office superintendent actions.
- Audit-linked CAR workflow actions are checked inside the Audit proxy and
  again inside the shared CAR workflow engine so direct PSC-CAR calls cannot
  bypass the audit-specific permission model.
- Frontend Audit record routes no longer rely only on global Audit process IDs;
  the backend remains the source of truth for access to a specific audit
  record.

Remaining boundary after assignment fix:

- If KSM wants `ACTING MASTER` to receive the same Audit gates as `MASTER`, or
  wants `AUDIT_P_013` granted to vessel-side Master for external registration,
  that still needs an explicit product/security ruling before another
  additive update.

## 2. First Backend Startup Error Previously Seen

Command:

```powershell
python manage.py runserver
```

Location:

```text
Complete_VIMS_audit_dev/psc-backend/modules/orb/orb/views.py
```

First error:

```text
TypeError: @permission_classes must come after (below) the @api_view decorator.
```

Traceback pointed first to:

```text
modules/orb/orb/views.py line 824
@permission_classes([AllowAny])
@api_view(['GET'])
def get_operations(request):
```

Cause:

- The active DRF version enforces decorator order for function-based API views.
- `@api_view(...)` must be the top source decorator, with
  `@permission_classes(...)` below it.

Fix applied during debugging:

- Reordered the affected ORB function-view decorators during initial
  debugging. Later review of
  `C:\Users\himan\Downloads\AUDIT-GAPS-RESOLUTION` identified this as
  security-sensitive: once the decorator order is valid, `AllowAny` becomes
  active on those endpoints.
- Corrected on 2026-08-16 in the active tree by deleting the stray
  `@permission_classes([AllowAny])` decorator from the four affected ORB
  endpoints instead of keeping it reordered:
  `get_operations`, `list_for_chief`,
  `get_all_crew_onboarding_history`, and
  `get_vessel_id_for_current_user`.
- After that, the next startup blocker was a Safety import drift:
  `ModuleNotFoundError: No module named 'PyPDF2'`, because the backend pins
  `pypdf` instead of `PyPDF2`.
- The resolution package recommends restoring `PyPDF2==3.0.1` for an older
  baseline tree. That recommendation does not apply to this active tree:
  `Complete_VIMS_audit_dev/psc-backend/requirements.txt` pins
  `pypdf==6.15.0`, and current production imports now match that pin.

Current verification on 2026-08-17:

- Checked local commit `a2f308127f1e9b03137408deb08c5fe1a7e6ad52`.
- Project default DRF permission is `IsAuthenticated`
  (`psc-backend/core/settings.py`).
- Direct unauthenticated DRF `APIRequestFactory` calls returned `401` for all
  four affected ORB functions:
  `get_operations`, `list_for_chief`,
  `get_all_crew_onboarding_history`, and
  `get_vessel_id_for_current_user`.
- `get_vessel_id_for_current_user` is URL-wired locally. The other three
  functions are not URL-wired locally, so they were verified by direct DRF
  view invocation rather than route-level HTTP requests.
- Follow-up hardening item: add committed regression coverage so any future
  route wiring for these functions still proves unauthenticated access returns
  `401` or `403`.

## 3. Additional Development Review Gaps

These are the remaining review-facing gaps observed from the local development
state and the project blocker registers. They are not release approvals and do
not modify the frozen SSOT.

### 3.1 Audit Dashboard Route Mismatch

- Resolved locally on 2026-08-19 under `CR-149`.
- `psc-frontend/src/App.tsx` now registers `/audit` and `/audit/dashboard`.
- `/audit` redirects to `/audit/dashboard`.
- `/audit/dashboard` renders a read-only Audit dashboard backed by the existing
  audit-plan list query; no backend route, schema, or permission-ID change was
  introduced.
- The existing Audit sidebar group now exposes an `Audit Dashboard` child link
  for users with Audit process access.
- Remaining review note: route-level browser evidence should be included in the
  next UAT report if this screen is part of the formal journey ledger.

### 3.2 Pre-Ship Review Not Executed

- No `REVIEW.md` approval artifact is present.
- Per `docs/BLOCKERS.md` PSB-2, no `APPROVE` or `APPROVE-WITH-MINORS` claim
  may be made until `Review.txt` is executed in a fresh verifier session.
- Impact: this blocks release crossing claims, not local build handover.

### 3.3 Release Crossing Still Blocked

- `RELEASE_RUNBOOK.md` exists and is generated, but the release crossing is
  still blocked by `deploy.method = DEFERRED:D-AUDRS-453`.
- KSM India still owes the seven closure facts: exact deployment command or
  procedure, execution environment and identity, credential/secret references,
  migration command, success signal, failure signal, and rollback command.
- Impact: no production release or release-crossing claim can be made.

### 3.4 Release Checks Are Fail-Closed

- The release check scripts exist under `checks/release/`, including backend
  tests, frontend tests, RBAC grid, PSC CAR regression, and shared-code diff.
- The runbook records these as fail-closed until they are wired to the real
  release suites and executed.
- Impact: release preflight cannot be treated as passing by absence.

### 3.5 Step 5 / Tier-R Not Executed

- Step 5 Part A and Tier-R / quality-trend maintenance drift review have not
  been executed for ship day.
- Per `docs/BLOCKERS.md` PSB-4, no Tier-R or code-rot-trend claim may be made.

### 3.6 Audit API Performance Baseline Deferred

- `PB-AUD-API-P95` remains a structured `DEFERRED` budget.
- No numeric Audit API p95 baseline is banked yet.
- Impact: not a build blocker, but review should record that performance
  budget evidence is deferred rather than measured.

### 3.7 Mock Approval Gaps

- Resolved for SCR-AUD-11/12/13 by the external resolution package reviewed
  2026-08-16.
- `docs/MOCK_APPROVAL.md` records Prince approval dated 2026-08-14 for
  Audit Dashboard, Finding Detail, and Acting HoD Coverage.
- The approved copies were folded into `docs/mockups/` with
  `status: reference`.
- SCR-AUD-14 reuses the PSC `/deficiencies` screen through a structured mock
  gap record and remains outside this approval.
- Impact: the previous draft-mock approval gap is closed for SCR-AUD-11/12/13;
  only the SCR-AUD-14 structured reuse gap remains.

### 3.8 Current Tree Needs Fresh Full Restamp After Runtime Fixes

- Backend startup fixes and sidebar fixes received focused verification.
- The latest Audit permission/profile investigation introduced follow-up code
  and data questions around effective Audit process IDs.
- The ORB `AllowAny` security correction and mock approval updates were applied
  after the previous quality stamp.
- Impact: the prior `QUALITY: PASS` citation is pre-fix evidence for those
  later edits; a fresh full Domain 13 quality run is needed before formal
  current-tree review claims.

### 3.9 Progress Ledger Has Stale-Looking Status Text

- `progress.txt` contains later Phase 13.4 closeout entries, but the top
  "CURRENT POSITION" section still contains older Phase 11 wording.
- Impact: formal reviewers may see contradictory status unless the ledger is
  normalized before review.
