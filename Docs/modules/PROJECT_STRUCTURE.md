# Project Structure

## Active Top-Level Layout

```text
Complete_VIMS/
  Docs/                  Primary documentation set
  psc-backend/           Django + DRF backend
  psc-frontend/          React + Vite frontend
  tasks/                 Working notes and handoff docs
  uploads/               Runtime upload data
  UPDATED_DOCS/          Historical duplicate docs
  VIMS Inspection/       Historical duplicate project snapshot
  README.md              High-level bootstrap instructions
  docker-compose.yml     Local multi-service orchestration
```

## Backend Layout

```text
psc-backend/
  core/                  Django settings, root urls, WSGI
  apps/
    accounts/           Auth, role mapping, vessel access, crew lookup
    masters/            Reference data APIs
    inspection/         Inspection, deficiency, dashboard, reports
    car/                CAR detail, actions, evidence, PV, exports
    notifications/      In-app notifications and overdue command
    sync/               Offline pull/push and conflict handling
  modules/
    orb/                Legacy oil record book module
    circular/           Legacy circular / notification module
  tests/                 Shared test helpers
  uploads/               Backend-side upload storage
  media/                 Logo and media storage
```

## Frontend Layout

```text
psc-frontend/
  src/
    components/         Reusable UI by feature
    hooks/              React Query hooks and auth helpers
    legacy/             Embedded VIMS Basic ORB/Circular app
    lib/                API client, IndexedDB, sync, validation, utils
    routes/             Page-level route components
    stores/             Zustand stores for auth and sync
    types/              Shared TypeScript models
  public/                Static assets
  tests/                 Frontend test support
```

## Ownership Boundaries

### Backend

- `apps/accounts`: user identity, JWT reconstruction, role/process resolution
- `apps/masters`: read-only master data lookup layer
- `apps/inspection`: inspection lifecycle and deficiency lifecycle
- `apps/car`: corrective action lifecycle after auto-created CAR exists
- `apps/notifications`: notification records and dispatch helpers
- `apps/sync`: vessel offline synchronization contract
- `modules/orb`: separate legacy product surface for ORB operations
- `modules/circular`: separate legacy product surface for circular distribution

### Frontend

- `routes/` and `components/`: modern PSC UI
- `lib/api/`: transport contract for backend modules
- `lib/db/` and `lib/sync/`: offline cache and queue orchestration
- `legacy/vims-basic/`: Redux-based legacy UI mounted inside the modern shell

## Important Non-Code Folders

- `Docs/`: use as canonical docs
- `tasks/`: useful for recent implementation context, not architecture source of truth
- `uploads/` and `psc-backend/uploads/`: runtime data, not source
- `node_modules/` and `psc-backend/backend.env/`: vendored/runtime dependencies

## Structural Observations

- The repository currently contains both a modern PSC application and two embedded legacy modules.
- Documentation is duplicated across `Docs/`, `UPDATED_DOCS/`, and `VIMS Inspection/Docs/`.
- The main architectural seam is not frontend vs backend; it is modern PSC workflow vs legacy ORB/Circular workflow.
