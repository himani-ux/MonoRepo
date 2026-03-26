# Frontend Dashboard and Reports

## Path

- `psc-frontend/src/routes/dashboard/`
- `psc-frontend/src/routes/reports/`
- `psc-frontend/src/components/dashboard/`
- `psc-frontend/src/hooks/use-dashboard.ts`
- `psc-frontend/src/lib/api/dashboard.ts`
- `psc-frontend/src/lib/api/reports.ts`

## Purpose

This module provides the management and analytics surfaces: KPI dashboard, repeat-deficiency visibility, and DefIntel reporting tools.

## Owns

- Landing dashboard with KPI cards and charts
- Vessel drill-down for office users
- Repeat deficiency presentation
- OpenSource import UI
- Vessel preparation checklist preview/export
- Deficiency-code prediction UI

## Workflow

1. `/dashboard` requests a single aggregate payload from the dashboard endpoint.
2. Office users can switch vessel context for drill-down.
3. Cards link users into inspections or CAR lists with prefiltered query params.
4. `/reports` gates online-only features for import, preview, export, and prediction.
5. Report actions call the backend and then either render preview payloads or download files.

## Dependencies

- Dashboard API from `apps/inspection/dashboard_views.py`
- Report APIs from `apps/inspection/urls_reports.py`
- Auth capability checks for office-only import actions

## Notes

- Reports are tightly coupled to backend DefIntel endpoints.
- The reports page also reflects connectivity state and backend reachability before enabling actions.
