# Review Notes

This file captures the highest-signal issues found during a static repository review.

## Critical

### 1. Secrets are committed in backend settings

- `psc-backend/core/settings.py` contains a real SMTP username and password instead of loading them from environment variables.
- Impact: credential exposure, email account compromise, and unsafe promotion of local settings into shared environments.
- Expected fix: move all mail and database secrets to `.env`, rotate the leaked credentials, and fail fast when secrets are missing.

### 2. Legacy ORB and Circular APIs are publicly exposed

- The legacy modules define many endpoints with `AllowAny` on viewsets and function views.
- Impact: unauthenticated users can reach business workflows that should be vessel or office scoped.
- Expected fix: place legacy routes behind the same JWT/authz layer used by PSC modules or isolate them behind a separate gateway.

## High

### 3. Sync push path is not safe for offline evidence creation

- `apps/sync/sync_service.py` always injects `created_by` during create operations, but the `Evidence` model does not accept that field.
- Impact: offline evidence uploads can fail during push, leaving queue items stuck or retried indefinitely.
- Expected fix: make create-field injection model-aware and map evidence ownership to `uploaded_by`.

## Medium

### 4. Overdue action notifications ignore most active CAR states

- `apps/notifications/management/commands/check_overdue_actions.py` only scans a narrow subset of CAR statuses.
- Impact: overdue warnings can be skipped while a CAR is still actively moving through vessel-side review states.
- Expected fix: filter on "not closed" or explicitly include all actionable workflow states.

### 5. DPA quick-close flow is inconsistent between CAR list and detail pages

- `psc-frontend/src/routes/cars/index.tsx` shows quick-close affordance to DPA users but its click handler only authorizes PIC or assigned verifier paths.
- Impact: DPA sees an action they are then blocked from executing.
- Expected fix: keep the permission rule aligned with the CAR detail page and backend policy.

## Maintainability Risks

- The repo mixes active source, runtime folders, duplicate documentation, and historical project copies in one tree.
- Legacy ORB/Circular code is large, mostly function-based, and weakly isolated from the modern app shell.
- PSC modules have meaningful tests; the legacy modules appear much less covered and should be treated as higher-risk when changed.
