# Frontend CAR Workflow

## Path

- `psc-frontend/src/routes/cars/`
- `psc-frontend/src/routes/notifications/`
- `psc-frontend/src/components/car/`
- `psc-frontend/src/components/notification/`
- `psc-frontend/src/hooks/use-cars.ts`
- `psc-frontend/src/hooks/use-notifications.ts`
- `psc-frontend/src/lib/api/cars.ts`
- `psc-frontend/src/lib/api/notifications.ts`

## Purpose

This module renders the corrective action workflow and notification inbox in the modern UI.

## Owns

- CAR list filters and pagination
- CAR detail screen with workflow actions
- CAR edit form for vessel-side and office-assist updates
- Evidence upload modals
- Physical verification create/close flows
- Notification center and read-state actions

## Workflow

1. `/cars` lists CARs with filters for status, overdue state, and PV due state.
2. `/cars/:id` renders the full CAR: deficiency context, root cause, actions, evidence, activity, audit, and workflow actions.
3. `/cars/:id/edit` lets authorized users save draft content or perform the next forward workflow action.
4. Evidence and PV actions are handled through dedicated modal components backed by CAR hooks.
5. `/notifications` loads paginated notifications and supports mark-read and mark-all-read.

## Dependencies

- Auth route guards and process IDs
- `apps/car` backend endpoints
- Notification backend endpoints

## Notes

- The frontend does not create CARs directly; it assumes inspection deficiency creation already created them.
- CAR workflow is driven by backend available-actions, not a frontend-only state machine.
