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

- Seed or merge the documented Audit permission IDs into the relevant
  `msc_profiles` rows, especially DPA/SEQ Manager/Lead Auditor/Conductor/
  Office Supt/FM/Master/HoD mappings.
- Do this as an additive permission-data update only. Do not mutate protected
  PSC tables and do not edit the frozen SSOT.

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

- Reordered the affected ORB function-view decorators.
- After that, the next startup blocker was a Safety import drift:
  `ModuleNotFoundError: No module named 'PyPDF2'`, because the backend pins
  `pypdf` instead of `PyPDF2`.

## 3. Additional Development Review Gaps

These are the remaining review-facing gaps observed from the local development
state and the project blocker registers. They are not release approvals and do
not modify the frozen SSOT.

### 3.1 Audit Dashboard Route Mismatch

- `docs/APP_FLOW.md` documents `/audit` / `/audit/dashboard` as the Audit
  dashboard entry.
- The frontend route table currently registers Audit detail, checklist,
  finding, external-audit, DPA queue, and plan routes, but no `/audit` or
  `/audit/dashboard` route.
- Impact: the sidebar should not link an Audit Dashboard until the route is
  implemented or the docs are formally corrected.

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

- Three mockups remain agent-authored `DRAFT` pending Prince approval:
  Audit Dashboard, Finding Detail, and Acting HoD Coverage.
- SCR-AUD-14 reuses the PSC `/deficiencies` screen through a structured mock
  gap record.
- Impact: mock coverage is structurally tracked, but those draft screens are
  not owner-approved UI references yet.

### 3.8 Current Tree Needs Fresh Full Restamp After Runtime Fixes

- Backend startup fixes and sidebar fixes received focused verification.
- The latest Audit permission/profile investigation introduced follow-up code
  and data questions around effective Audit process IDs.
- Impact: the prior `QUALITY: PASS` citation is pre-fix evidence for those
  later edits; a fresh full Domain 13 quality run is needed before formal
  current-tree review claims.

### 3.9 Progress Ledger Has Stale-Looking Status Text

- `progress.txt` contains later Phase 13.4 closeout entries, but the top
  "CURRENT POSITION" section still contains older Phase 11 wording.
- Impact: formal reviewers may see contradictory status unless the ledger is
  normalized before review.
