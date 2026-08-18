# Audit Gap 2 - Journey Test Data And Acting HoD Assignment

Date: 2026-08-17

## Current Journey Result

After fixing the Register Audit route and rerunning with the local Audit test dataset, the previous local run reported:

- 8 journeys passed.
- 5 journeys failed.
- 1 journey skipped.

Passed:

- JOURNEY-1.
- JOURNEY-2.
- JOURNEY-4.
- JOURNEY-9.
- JOURNEY-10.
- JOURNEY-11.
- JOURNEY-12.
- JOURNEY-13.

Failed:

- JOURNEY-3: Audit detail page opens, but submit, scorecard, acknowledgement, and findings controls are not visible.
- JOURNEY-5: NC Closure page opens, but says NC closure not found.
- JOURNEY-6: Failed under DPA, but passed when rerun with Superintendent/PIC. This points to actor-specific access or workflow-state data, not a general code failure.
- JOURNEY-7: NC Closure page opens, but Lead Auditor or effectiveness controls are not visible.
- JOURNEY-8: Observation Closure page opens, but says Observation closure not found.

Skipped:

- JOURNEY-14: Acting HoD page is absent.

Evidence correction on 2026-08-17:

- The previous pass list should not be treated as formally verified until each
  journey has the agreed evidence package: commit SHA, account/persona, route,
  record IDs, command, raw output/log, and screenshot for manual checks.
- `JOURNEY-1`, `JOURNEY-2`, `JOURNEY-4`, `JOURNEY-9`, `JOURNEY-10`, and `JOURNEY-11` especially need rerun evidence
  because their actor usage and dependent screens were not fully recorded.
- `JOURNEY-12` is added to the rerun list because the external-audit record
  view still needs explicit verification evidence.
- `JOURNEY-6` is not a DPA failure. The backend negative guard now has a
  passing regression test for Lead Auditor denied PIC review on own audit, but
  the browser/manual positive PIC case still needs a complete evidence package.

Current unified rerun list:

- JOURNEY-2.
- JOURNEY-3.
- JOURNEY-4.
- JOURNEY-5.
- JOURNEY-7.
- JOURNEY-8.
- JOURNEY-9.
- JOURNEY-10.
- JOURNEY-11.
- JOURNEY-12.
- JOURNEY-13.

The previous Register Audit blocker is resolved. The Register Audit screen now opens the Audit Registration form and exposes the auditee type field.

One-line gap summary: Acting HoD assignment screen/route is not available, and the remaining failures are now around Audit detail action controls, NC/Observation closure records not being found, workflow state, and actor-specific access.

## Permission Model Status - msc_profiles And Per-Record Roles

This is not an open permission-model decision.

`msc_profiles` works for fixed profile-wide Audit permissions such as `SEQ Manager`, `MASTER`, `Marine Superintendent`, `Technical Superintendent`, `admin`, and `Super Admin`.

Audit also has roles that come from the audit record itself. These roles are not solved by adding rows into `msc_profiles`.

Confirmed access sources:

Current position:

- `audit_detail.lead_auditor_user_id` grants Lead Auditor access for that audit.
- `audit_detail.conductor_user_id` grants Conductor access for that audit.
- `master_hod_assignment` grants HoD / Acting HoD access where the assignment is active.
- Backend permission logic merges static `AUDIT_P_*` grants with these per-record assignment grants.
- Audit Detail frontend reads the API `effective_permissions` value for action visibility.

Remaining validation:

- The failed journeys must be rerun with real test users deliberately written into the matching audit/finding assignment fields.
- A run against arbitrary existing IDs is only a data-state check, not proof that assigned-role controls are missing.

## What Is Not A Development Bug

JOURNEY-6 is not a general development failure because it passed with the correct Superintendent/PIC user.

This means the DPA failure is most likely caused by one of these:

- the journey was run with the wrong actor for that workflow step,
- the test record is not assigned to the DPA user being used,
- the finding is not in the exact state where DPA can act.

The test data still needs to be prepared per journey step, not just as a generic audit and finding record.

## Remaining Failure Areas

### Audit Detail Controls

JOURNEY-3 reaches the Audit detail page, but the expected submit, scorecard, acknowledgement, and findings controls are not visible.

This needs verification against the expected workflow state and role permissions for the audit detail page.

### NC Closure Records

JOURNEY-5 and JOURNEY-7 reach the NC Closure page, but either the NC closure record is not found or the expected Lead Auditor/effectiveness controls are not visible.

This means the NC finding data exists, but it is not yet confirmed to be in the correct closure stage for those journeys.

### Observation Closure Record

JOURNEY-8 reaches the Observation Closure page, but says Observation closure not found.

This means the Observation finding data exists, but the closure child record or expected workflow state is missing for that journey.

## Actual Development Gap

JOURNEY-14 is different from the other skipped journeys.

JOURNEY-14 checks Acting HoD assignment. This is currently a development gap if the business expects this feature in the current Audit scope.

## Why This Is A Gap

The backend has partial support for Acting HoD logic:

- `master_hod_assignment` table exists.
- Audit permission logic can resolve active HoD assignments.
- Acting HoD permission helper exists.

However, the user-facing workflow is not fully wired:

- There is no visible frontend window for Acting HoD assignment.
- There is no confirmed frontend route for this function.
- There is no clearly exposed Audit API endpoint for creating or updating Acting HoD assignment from the UI.

Because of this, a user cannot assign an Acting HoD from the Audit module today.

## User Impact

If Acting HoD assignment is required, users cannot complete that workflow from the application.

The journey test must remain skipped until either:

- the Acting HoD assignment screen/API is implemented, or
- the business confirms Acting HoD assignment is out of current scope.

## How To Resolve

### Test Data Gap

Create controlled audit test data for each journey validation stage.

The cleanest option is to create a backend seed command that prepares records in the exact workflow state needed by each journey and prints the environment variables needed by the journey runner.

Expected output example:

```text
JOURNEY_AUDIT_ID=<audit_id>
JOURNEY_NC_FINDING_ID=<nc_finding_id>
JOURNEY_OBS_FINDING_ID=<observation_finding_id>
```

The seed data must also include any required NC and Observation closure child records, with the right assigned user and status for the journey being tested.

### Acting HoD Gap

If Acting HoD assignment is required, implement a small Audit module screen and API.

Expected fields:

- Department.
- HoD user.
- Acting HoD user.
- Effective from date.
- Effective to date.
- Acting or permanent assignment flag.
- Reason or remarks.

Expected permission:

- Restrict assignment to authorized users, likely through `AUDIT_P_016`.

Expected result:

- User can create or update Acting HoD assignment from the Audit module.
- Journey-14 can run against the confirmed route instead of being skipped.

## Ownership

Test data gap:

- Functional/testing team or development team with database seed access.

Acting HoD development gap:

- Development team, after business confirms the feature is required in current scope.

## Simple Status

Register Audit is fixed.

PIC review works when the correct PIC/Superintendent user is used.

The remaining failed journeys now need workflow-state-specific audit, NC, and Observation closure data, plus verification of the Audit detail controls for the expected role.

Acting HoD assignment remains a development gap because the user-facing page or route is still absent.
