# Module Documentation Index

This folder documents the current codebase by active module, not by historical planning document.

## Canonical Scope

- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md): top-level folder map and ownership boundaries
- [`REVIEW_NOTES.md`](REVIEW_NOTES.md): code review findings and maintainability risks found during the repository audit

## Backend Modules

- [`backend/accounts.md`](backend/accounts.md)
- [`backend/masters.md`](backend/masters.md)
- [`backend/inspection.md`](backend/inspection.md)
- [`backend/car.md`](backend/car.md)
- [`backend/notifications.md`](backend/notifications.md)
- [`backend/sync.md`](backend/sync.md)
- [`backend/orb.md`](backend/orb.md)
- [`backend/circular.md`](backend/circular.md)

## Frontend Modules

- [`frontend/app-shell.md`](frontend/app-shell.md)
- [`frontend/circular-workflow.md`](frontend/circular-workflow.md)
- [`frontend/inspection-workflow.md`](frontend/inspection-workflow.md)
- [`frontend/car-workflow.md`](frontend/car-workflow.md)
- [`frontend/dashboard-reports.md`](frontend/dashboard-reports.md)
- [`frontend/offline-legacy.md`](frontend/offline-legacy.md)

## How To Read These Docs

Each module document answers the same questions:

- What folders and files define the module
- What the module owns
- Which other modules it depends on
- The request or UI workflow through the module
- Where the main extension points and risks are

## Repository Notes

- `Docs/` should be treated as the primary documentation location.
- `UPDATED_DOCS/` and `VIMS Inspection/Docs/` appear to be historical or duplicated copies.
- Runtime and generated directories such as `node_modules/`, `psc-backend/backend.env/`, `uploads/`, and `media/` should not be used as architecture references.
