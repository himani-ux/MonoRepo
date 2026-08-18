# UAT-REPORT
report_date: 2026-08-18
repo_commit: 2063e624035637e263473588c96ff9bb3afd5fb2
app_target: http://localhost:5173
rerun_type: blocked_runtime_preflight
post_sync_update: 2026-08-18
runner_sync_commit: 5ee3062 Sync audit journey test docs

Narrative prose is allowed here and carries no authority.

This report does not mark any Audit journey as passed. The original browser rerun was not executed because, at that time, the local `journey/surface-check` runner package was absent in this checkout and the required journey runtime environment variables were not present in the shell: `JOURNEY_USERNAME`, `JOURNEY_PASSWORD`, `JOURNEY_AUDIT_ID`, `JOURNEY_NC_FINDING_ID`, `JOURNEY_OBS_FINDING_ID`, `JOURNEY_EXTERNAL_AUDIT_ID`, `JOURNEY_ACTING_HOD_ROUTE`, and `APP_BASE_URL`.

Post-sync correction: commit `5ee3062 Sync audit journey test docs` restored `journey/surface-check` and `journey/docs/uat-report-format.md` in the repo. Current browser execution is therefore blocked by runtime setup only: install runner dependencies from `journey/surface-check`, provide credentials through the secret channel, and set the journey env values.

Local runtime preflight found `http://localhost:5173` reachable, but no journey pass is claimed from source inspection, route registration, or database row presence alone.

## Local Test Records Identified

Read-only SQL checks against `HIMANI / ksm_marine_live` confirmed these local records:

- Audit plan: `A1170000-0000-0000-0000-000000000001`, status `CONFIRMED`.
- Audit detail: `A1170000-0000-0000-0000-000000000002`, status `IN_PROGRESS`, conductor `DEMO.CONDUCTOR`, lead auditor `DEMO.LEAD`, PIC `Aman.Oberoi`.
- PSC inspection: `a1170000000000000000000000000003`, status `OPEN`, type `AUDIT`.
- NC finding: `A1170000-0000-0000-0000-000000000007`, linked NC closure row exists, final closure status `OPEN`.
- NC CAR: `a1170000000000000000000000000005`, status `OFFICE_DRAFTED`, last action `OFFICE_DRAFT`.
- Observation finding: `A1170000-0000-0000-0000-000000000012`, linked Observation closure row exists, closure status `OPEN`.
- Observation CAR: `a1170000000000000000000000000010`, status `OPEN`, last action `OBS_CREATED`.
- Acting HoD assignment: `A1170000-0000-0000-0000-000000000030`, department `DECK`, acting assignment for `DEMO.HOD`.
- External audit detail: no local `audit_detail` row was found with `audit_classification = EXTERNAL` or a populated `external_audit_org_id`.

## Journey Rerun Matrix

| Journey | Status | Route / record | Evidence and blocker |
| --- | --- | --- | --- |
| JOURNEY-1 | BLOCKED | `/audit/plans`, plan `A1170000-0000-0000-0000-000000000001` | Browser rerun blocked by missing runtime account/env values. Runner folder is now present after commit `5ee3062`. Expected controls from `tests/journeys/journey-001.spec.ts:5`: `Audit Plans`, `Register Audit`, `Create routine plan entry`, `Register rows`, `OPM F 713`. |
| JOURNEY-2 | BLOCKED | `/inspections/new` | Browser rerun blocked by missing runtime account/env values. Runner folder is now present after commit `5ee3062`. Expected controls from `tests/journeys/journey-002.spec.ts:5`: `Audit Classification`, `Audit Subtype`, `Lead Auditor`, `Register Audit`. |
| JOURNEY-3 | FAILED | `/audit/audits/A1170000-0000-0000-0000-000000000002` | Previous local rerun evidence in `audit_docsuite/AUDIT_GAP_2.md` says the Audit detail page opens, but `Submit`, `Scorecard`, `Vessel Acknowledge`, and `findings` controls were not visible. The route/control source exists at `psc-frontend/src/App.tsx:298` and `psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:259`, `:265`, `:344`, `:371`, but no browser pass evidence exists for this record/actor. |
| JOURNEY-4 | BLOCKED | `/audit/findings/A1170000-0000-0000-0000-000000000007/nc/wizard` | NC finding exists, but browser rerun is blocked by missing runtime account/env values. Runner folder is now present after commit `5ee3062`. Expected controls from `tests/journeys/journey-004.spec.ts:6`: `Root Cause`, `Save and Continue`, `RCA`, `wizard`. |
| JOURNEY-5 | FAILED | `/audit/findings/A1170000-0000-0000-0000-000000000007/nc` | Previous local rerun evidence in `audit_docsuite/AUDIT_GAP_2.md` says the NC Closure page opens but reports `NC closure not found`. Missing journey controls: `Master / HoD Signer`, `signature`, `signed`, `backdate` from `tests/journeys/journey-005.spec.ts:7`. |
| JOURNEY-6 | BLOCKED | `/audit/findings/A1170000-0000-0000-0000-000000000007/nc` | Backend negative guard evidence exists for Lead Auditor denied PIC review on own audit (`psc-backend/tests/audit/test_car_workflow_proxy.py:341`, `:353`, `:354`). Positive browser PIC/Superintendent rerun is blocked here by missing runtime account/env values, so no UAT pass is claimed. |
| JOURNEY-7 | FAILED | `/audit/findings/A1170000-0000-0000-0000-000000000007/nc` | Previous local rerun evidence in `audit_docsuite/AUDIT_GAP_2.md` says the NC Closure page opens but Lead Auditor or effectiveness controls are not visible. Missing journey controls: `Effectiveness`, `Verification`, `Lead Auditor`, `Review Method` from `tests/journeys/journey-007.spec.ts:7`. |
| JOURNEY-8 | FAILED | `/audit/findings/A1170000-0000-0000-0000-000000000012/obs` | Previous local rerun evidence in `audit_docsuite/AUDIT_GAP_2.md` says the Observation Closure page opens but reports `Observation closure not found`. Missing journey controls: `Master Close`, `Action Plan`, `Save and Continue` from `tests/journeys/journey-008.spec.ts:6`. |
| JOURNEY-9 | BLOCKED | `/audit/plans`, plan `A1170000-0000-0000-0000-000000000001` | Browser rerun blocked by missing runtime account/env values. Runner folder is now present after commit `5ee3062`. Expected controls from `tests/journeys/journey-009.spec.ts:5`: `OPM F 713`, `Request extension`, `Cancel`, `Extension`. |
| JOURNEY-10 | BLOCKED | `/audit/plans`, plan `A1170000-0000-0000-0000-000000000001` | Browser rerun blocked by missing runtime account/env values. Runner folder is now present after commit `5ee3062`. Expected controls from `tests/journeys/journey-010.spec.ts:5`: `Create additional audit`, `Additional reason`, `Trigger type`, `Additional`. |
| JOURNEY-11 | BLOCKED | `/dpa/notifications/failed` and `/dpa/scan-validation-queue` | Browser rerun blocked by missing runtime account/env values. Runner folder is now present after commit `5ee3062`. Expected controls from `tests/journeys/journey-011.spec.ts:6` and `:9`: `Retry`, `notified offline`, `Accept`, `rescan`, queue empty states. |
| JOURNEY-12 | BLOCKED | `/audit/external/new`; optional `/audit/external/<external_audit_id>` | Registration route has source evidence at `psc-frontend/src/App.tsx:278`, but browser rerun is blocked by missing runtime account/env values. Optional close-out route is also blocked by missing local external audit detail record; read-only SQL found no external audit row. Expected controls from `tests/journeys/journey-012.spec.ts:6` and `:12`: `External Audit Definition`, `External Audit Org UUID`, `External Lead Auditor`, `Register External Audit`, `External Audit Close-out`, `certificate impact`, `Confirm External Closure`. |
| JOURNEY-13 | BLOCKED | `/inspections/new` | Browser rerun blocked by missing runtime account/env values. Runner folder is now present after commit `5ee3062`. Expected controls from `tests/journeys/journey-013.spec.ts:5`: `Office Department`, `OFFICE_DEPT`, `Department`, `Audit Scope`. |
| JOURNEY-14 | FAILED | no confirmed frontend route | A local Acting HoD assignment row exists (`A1170000-0000-0000-0000-000000000030`), but no `JOURNEY_ACTING_HOD_ROUTE` was available and route search did not find an Audit Acting HoD assignment route in `psc-frontend/src/App.tsx`. Missing screen/control set from `tests/journeys/journey-014.spec.ts:6`: `Acting`, `HoD`, `effective`, `department`. |

## Current Required Rerun Scope

The current required rerun list remains:

`JOURNEY-1, JOURNEY-2, JOURNEY-3, JOURNEY-4, JOURNEY-5, JOURNEY-7, JOURNEY-8, JOURNEY-9, JOURNEY-10, JOURNEY-11, JOURNEY-12, JOURNEY-13`

`JOURNEY-6` has source/backend guard evidence for the Lead Auditor denial case and still needs browser PIC/Superintendent evidence before any UAT pass claim. `JOURNEY-14` remains a failed product/screen gap until Acting HoD assignment is confirmed out of scope or a route is implemented and rerun.

## Required Next Rerun Inputs

- Install dependencies for the synced journey runner expected by `tests/journeys/README.md`: `journey/surface-check`.
- Provide journey credentials through the approved secret channel, not markdown.
- Set the local IDs: `JOURNEY_AUDIT_ID=A1170000-0000-0000-0000-000000000002`, `JOURNEY_NC_FINDING_ID=A1170000-0000-0000-0000-000000000007`, `JOURNEY_OBS_FINDING_ID=A1170000-0000-0000-0000-000000000012`.
- Create or identify a real local external audit detail ID before claiming the optional JOURNEY-12 close-out route.
- Confirm the Acting HoD route or implement it before rerunning JOURNEY-14.
