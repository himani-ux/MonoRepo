# Journey Runtime Run - 2026-08-17

## Scope

Runtime smoke run for the authored audit journey specs in `tests/journeys/` against:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

Credentials were supplied interactively for DPA, Master, Superintendent/PIC, and Fleet Manager. Passwords are intentionally not recorded here.

## DPA Result

User: DPA account supplied in chat.

Command group: full authored journey suite, 14 specs.

Result:

- Passed: 6
  - JOURNEY-1: audit plan register and planning controls
  - JOURNEY-2: register-audit/sidebar branch and checklist-entry route reachability
  - JOURNEY-9: OPM F 713 extension/cancellation controls
  - JOURNEY-10: additional audit creation surface
  - JOURNEY-11: failed-notification and scan-validation queues
  - JOURNEY-12: external audit registration/close-out route reachability
- Skipped: 7
  - JOURNEY-3 through JOURNEY-8 require concrete sample audit/finding/closure IDs.
  - JOURNEY-14 requires the acting-HoD assignment route or implementation path.
- Failed: 1
  - JOURNEY-13: `/inspections/new` does not expose the audit registration field `#auditee_type`.

## Other Supplied Roles

Master:

- DPA/office planning journeys are not valid for this account and failed when run as a full group.
- The targeted office-department audit registration journey also failed because `/inspections/new` did not expose `#auditee_type`.

Superintendent/PIC:

- DPA/office audit planning, external audit, failed-notification, and scan-validation surfaces were not visible for this account.
- `Register Audit` was not visible in the sidebar for the targeted conductor/register journey.
- `/inspections/new` still did not expose `#auditee_type`.

Fleet Manager:

- DPA/office audit planning, external audit, failed-notification, and scan-validation surfaces were not visible for this account.
- `Register Audit` was not visible in the sidebar for the targeted conductor/register journey.
- `/inspections/new` still did not expose `#auditee_type`.

## Confirmed Runtime Gap

The DPA account can see these audit sidebar tabs:

- Audit Plans
- Register Audit
- External Audit
- Failed Notifications
- Scan Validation Queue

However, the `Register Audit` link points to `/inspections/new`, and the current page renders the PSC-style `New Inspection` form instead of the audit registration form. The expected audit-specific field `#auditee_type` is absent, so office-department audit registration cannot be completed from the current UI.

## Remaining Inputs Needed

To run the skipped journeys end to end, provide real test records from the audit module:

- One draft/submittable audit ID for submit and acknowledgement flow.
- One NC/finding ID assigned to a crew action owner.
- One NC/finding ID waiting for master closure/signature.
- One NC/finding ID waiting for office/PIC review.
- One NC/finding ID waiting for lead-auditor verification/effectiveness review.
- One observation finding ID waiting for master close.
- Acting-HoD assignment route or confirmation that the feature is not implemented yet.

## Files Touched In This Runtime Pass

- `tests/journeys/helpers.ts`: sidebar helper now expands collapsed menus only when needed.
- `tests/journeys/journey-013.spec.ts`: checks for office-department audit registration controls on `/inspections/new`.
- `docs/JOURNEY_RUNTIME_RUN_2026-08-17.md`: this run note.

## Follow-Up Runtime Run With Local Audit Data

Run input supplied on 2026-08-17:

- Audit ID: `87226e6c-0cef-4c97-9a07-abd5f5cc11e7`
- NC finding ID: `c68d6233-1dec-482e-9c73-192b357e3774`
- OBS finding ID: `7666c138-e984-4d26-84ed-226530a66771`
- Vessel: SF DARIKA / SFD
- Inspection ID: `427185c77313443682d27a6a50957f94`
- NC CAR: `SFD-PSC-2026-003`
- OBS CAR: `SFD-PSC-2026-004`

DPA full-suite result:

- Passed: 8
  - JOURNEY-1, JOURNEY-2, JOURNEY-4, JOURNEY-9, JOURNEY-10, JOURNEY-11, JOURNEY-12, JOURNEY-13
- Failed: 5
  - JOURNEY-3: `/audit/audits/{auditId}` opens `Audit Detail`, but submit/scorecard/vessel-acknowledgement/findings controls are not visible.
  - JOURNEY-5: `/audit/findings/{ncFindingId}/nc` opens `NC Closure`, but the page says `NC closure not found`.
  - JOURNEY-6: failed under DPA, but passed when rerun with the Superintendent/PIC account.
  - JOURNEY-7: `/audit/findings/{ncFindingId}/nc` opens `NC Closure`, but effectiveness/lead-auditor verification controls are not visible.
  - JOURNEY-8: `/audit/findings/{obsFindingId}/obs` opens `Observation Closure`, but the page says `Observation closure not found`.
- Skipped: 1
  - JOURNEY-14: acting-HoD assignment route/page is absent and remains a development gap.

Role-targeted reruns:

- Superintendent/PIC account passed JOURNEY-6 with the supplied NC finding ID.
- Master account failed JOURNEY-5 and JOURNEY-8 with the supplied finding IDs.
- Fleet Manager and Superintendent/PIC accounts also failed JOURNEY-3 against the supplied audit ID; the detail page shell loads, but the expected controls do not appear.

Additional JOURNEY-6 clarification:

- Retested `JOURNEY-6` under the Superintendent/PIC account on 2026-08-17: passed.
- The current `tests/journeys/journey-006.spec.ts` checks only that the office/PIC NC closure surface is reachable for the correct PIC actor.
- The Journey Map step that requires a second Superintendent/Lead Auditor attempting to claim PIC review on their own audit has not been exercised by the current spec or available credentials.
- To test that negative case, a second Superintendent/PIC-capable account is required, and that account must be configured as the Lead Auditor of record on the same audit/finding. Expected result: server/UI refuses PIC claim for Lead Auditor of own audit, typically HTTP 403 or equivalent access denial.
- A second Superintendent/PIC-capable account was later supplied and `JOURNEY-6` positive surface access passed with the same NC finding ID.
- Read-only DB evidence showed the supplied NC finding belongs to audit `87226e6c-0cef-4c97-9a07-abd5f5cc11e7`, whose `audit_detail.lead_auditor_user_id` is `Harman.S`; the second Superintendent account is not the Lead Auditor of that audit.
- Therefore the browser/live journey still has not exercised the negative "Lead Auditor refused PIC on own audit" sub-case. It needs a fixture where the second Superintendent is assigned as `lead_auditor_user_id` for the same audit/finding and the CAR is in `SUBMITTED_TO_PIC`.
- Backend regression evidence exists for the negative rule: `tests.audit.test_car_workflow_proxy.AuditCarWorkflowProxyTests.test_lead_auditor_cannot_claim_pic_review_on_own_audit` passed on 2026-08-17 and asserts HTTP 403 with `LEAD_AUDITOR_PIC_DENIED`.

Current interpretation:

- `Register Audit` blocker is fixed.
- `JOURNEY-6` is not a development failure for the supplied data; it requires the correct PIC actor.
- `JOURNEY-3` needs investigation in the audit detail page/data binding because the route loads but the expected journey controls are missing.
- `JOURNEY-5`, `JOURNEY-7`, and `JOURNEY-8` need either records in the exact closure/verification states or a backend/frontend fix for closure lookup/access.
- `JOURNEY-14` is a confirmed development gap because the acting-HoD page/route is absent.
