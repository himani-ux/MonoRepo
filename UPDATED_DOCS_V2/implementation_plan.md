# Implementation Plan

This plan is written so the system can be rebuilt in a deterministic order without guessing dependencies.

## 1. Environment Prerequisites

### Backend

- Python 3.12.x
- SQL Server 2019 or later
- ODBC Driver 17 or 18 for SQL Server
- A writable media/uploads directory

### Frontend

- Node.js 22.x LTS
- npm 10+ or a compatible package manager

### Shared

- Existing SQL Server database access
- Access to the shared unmanaged tables used by the system

## 2. Repository Layout To Create First

Create the project structure before writing feature code:

```text
psc-backend/
  core/
  apps/
    accounts/
    masters/
    inspection/
    car/
    notifications/
    sync/
  modules/
    circular/
    orb/

psc-frontend/
  src/
    components/
    hooks/
    lib/
    routes/
    stores/
    legacy/
```

## 3. Database Setup

### Important Constraint

Do not alter existing shared tables directly. The codebase reads from a mixture of:

- unmanaged legacy tables
- PSC-owned tables
- legacy module tables

### Database Initialization Order

1. Connect Django to the target SQL Server instance.
2. Verify the shared tables referenced by authentication and vessel access exist.
3. Verify the PSC master tables exist.
4. Verify the PSC transaction tables exist.
5. Verify the legacy Circular and ORB tables exist.
6. Only after the schema is present, seed reference data if the environment is empty.

### Required Table Groups

- Authentication and vessel mapping tables
- PSC master lookup tables
- Inspection and deficiency tables
- CAR and workflow tables
- Notification tables
- Sync tables
- Circular tables
- ORB tables

## 4. Backend Setup

### Step 4.1: Create Virtual Environment

```bash
cd psc-backend
python -m venv venv
source venv/bin/activate
```

### Step 4.2: Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4.3: Configure Environment

Create `psc-backend/.env` from `.env.example` and set:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`
- `JWT_ACCESS_TOKEN_LIFETIME`
- `JWT_REFRESH_TOKEN_LIFETIME`
- `UPLOAD_BASE_PATH`
- `MAX_FILE_SIZE_MB`
- `CORS_ALLOWED_ORIGINS`

### Step 4.4: Validate Connectivity

Run the following checks in order:

```bash
python manage.py check
python manage.py test
```

If the project is being built against a fresh database copy, run migrations only after verifying the unmanaged/shared tables are already present.

### Step 4.5: Start Backend

```bash
python manage.py runserver 0.0.0.0:8000
```

## 5. Frontend Setup

### Step 5.1: Install Dependencies

```bash
cd psc-frontend
npm install
```

### Step 5.2: Configure Environment

Create `psc-frontend/.env` from `.env.example` and set:

- `VITE_API_BASE_URL`
- `VITE_APP_ENV`

### Step 5.3: Start Frontend

```bash
npm run dev
```

## 6. Module Implementation Order

Implement in the following order to avoid circular dependencies:

### 1. Authentication

Build first because every other feature depends on identity, roles, and vessel scope.

Deliverables:

- custom authentication backend
- JWT issuance and refresh
- user-profile endpoint
- company logo endpoint
- frontend auth store and route guard

### 2. Inspection Module

Build the inspection lifecycle next, because it creates the base entity for deficiencies and CARs.

Deliverables:

- inspection master/detail/create/update/delete
- inspection report upload
- deficiency create and workflow
- follow-up flow
- dashboard metrics

### 3. Circular Module

Integrate the legacy circular shell after auth and core inspection flows are stable.

Deliverables:

- circular navigation shell
- office-side notification management
- ship-side acknowledgment flows
- PDF/report viewer flows

### 4. ORB Module

Add ORB last because it reuses the same auth shell but has a separate legacy workflow and UI.

Deliverables:

- vessel selector and approved entries
- operation entry create/update flows
- PDF archive and metadata support

## 7. API Creation Order

Follow this backend order:

1. `POST /api/psc/auth/login/`
2. `POST /api/psc/auth/refresh/`
3. `POST /api/psc/auth/logout/`
4. `GET /api/psc/auth/me/`
5. `GET /api/psc/auth/crew/`
6. `GET|POST /api/psc/auth/company-logo/`
7. `GET /api/psc/masters/*`
8. `GET|POST /api/psc/inspections/` and `POST /api/psc/inspections/create/`
9. `GET|PUT|DELETE /api/psc/inspections/{id}/*`
10. `POST /api/psc/inspections/{id}/submit/`
11. `POST /api/psc/inspections/{id}/pic-review/`
12. `POST /api/psc/inspections/{id}/dpa-close/`
13. `POST /api/psc/inspections/{id}/upload-report/`
14. `POST /api/psc/inspections/{inspection_id}/deficiencies/`
15. `PUT /api/psc/deficiencies/{id}/action-code/`
16. `POST /api/psc/deficiencies/{id}/workflow/`
17. `POST /api/psc/deficiencies/{id}/allocate/`
18. `GET|PUT|POST /api/psc/cars/*`
19. `POST /api/psc/cars/{car_id}/evidence/`
20. `POST /api/psc/cars/{car_id}/actions/`
21. `POST /api/psc/cars/{car_id}/physical-verification/`
22. `POST /api/psc/sync/pull/`
23. `POST /api/psc/sync/push/`
24. `GET /api/psc/sync/conflicts/`
25. `POST /api/psc/sync/resolve-conflict/`
26. `GET /api/psc/notifications/*`
27. `POST /api/psc/reports/*`
28. Legacy `/api/circular/*`
29. Legacy `/api/orb/*`

## 8. UI Development Order

Follow the same order on the frontend:

1. Auth screens and route protection
2. Root layout, header, sidebar, bottom nav
3. Dashboard
4. Inspection list/create/detail/edit/follow-up
5. Deficiency dashboard
6. CAR list/detail/edit
7. Notifications center
8. Sync status screen
9. Reports workspace
10. Settings page
11. Circular module shell
12. ORB module shell

## 9. Integration Steps

### Backend to Frontend

- Configure the API base URL in the frontend environment.
- Ensure JWT tokens are attached by the Axios interceptor.
- Use query invalidation after every mutation.
- Keep role and process IDs aligned with backend claims.

### Auth Integration

- Login returns access token, refresh token, and the normalized user payload.
- Frontend persists tokens locally.
- Interceptor retries on 401 by refreshing the token once.

### Offline Integration

- Persist local sync state.
- Queue vessel-side changes.
- Sync attachments after server accepts the metadata.
- Resolve conflicts only in office/DPA mode.

### Legacy Module Integration

- Load the legacy provider only after the modern auth store is initialized.
- Bridge modern tokens and user claims into the legacy Redux store.
- Keep the legacy modules inside their own wrappers so they do not leak assumptions into PSC screens.

## 10. Deployment Steps

### Local Dev

1. Start SQL Server.
2. Start the backend server.
3. Start the frontend dev server.
4. Confirm auth, inspection list, and dashboard load before testing deeper flows.

### Production

1. Build the frontend bundle.
2. Serve the frontend through Nginx or a static file host.
3. Run the backend through Gunicorn.
4. Ensure media/uploads are persisted outside the container image.
5. Set CORS and allowed hosts correctly.
6. Confirm JWT refresh works in the deployed domain.

## 11. Common Pitfalls

- Mixing `user_type` and `role` logic. The role claim is the primary RBAC source.
- Editing unmanaged shared tables with migrations. Treat them as read-only.
- Forgetting that office visibility is vessel-scoped unless the user has global access.
- Uploading files larger than the configured limits.
- Using the wrong endpoint shape for inspections and CARs. The codebase uses `/create/`, `/update/`, and `/workflow/` actions.
- Breaking the legacy module bridge by bypassing the auth store.

## 12. Best Practices

- Keep request validation in serializers, not views.
- Keep access control in permission classes and vessel-access helpers.
- Treat sync metadata as first-class data, not an afterthought.
- Use explicit transition endpoints for workflow state changes.
- Never rely on the frontend alone for role enforcement.
- Preserve legacy route compatibility when touching Circular or ORB.

