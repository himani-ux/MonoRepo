# VIMS Inspection Module

Maritime vessel inspection management system for Port State Control (PSC), RightShip (RS), and Audit inspections. Manages the complete lifecycle from inspection recording through deficiency tracking, Corrective Action Reports (CAR), and DPA closure.

## Documentation Status

The original v1.0 documents were expanded later as the implementation grew. Post-baseline additions for routes, files, tables, mappings, and reporting are captured in `docs/LATER_CHANGES.md`.

## Architecture

| Layer | Technology | Directory |
|-------|-----------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS | `psc-frontend/` |
| Backend | Django 5.2.7 + Django REST Framework | `psc-backend/` |
| Database | SQL Server 2019+ | Configured via `.env` |
| PWA | Workbox 7.1.0 (service worker, offline support) | `psc-frontend/src/sw.ts` |

## Prerequisites

- **Node.js** 22.x (LTS)
- **Python** 3.12.x
- **SQL Server** 2019 or later
- **ODBC Driver** 17+ for SQL Server

## Quick Start

### 1. Clone and set up environment files

```bash
# Copy environment templates
cp psc-backend/.env.example psc-backend/.env
cp psc-frontend/.env.example psc-frontend/.env
```

Edit each `.env` file with your local values (see Environment Variables below).

### 2. Backend Setup

```bash
cd psc-backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

Backend runs at `http://localhost:8000`.

### 3. Frontend Setup

```bash
cd psc-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Environment Variables

### Backend (`psc-backend/.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Django debug mode | `True` |
| `SECRET_KEY` | Django secret key | (generate a secure key) |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DB_HOST` | SQL Server hostname | `localhost` |
| `DB_NAME` | Database name | `ksm_marine_live` |
| `DB_USER` | Database user | `sa` |
| `DB_PASSWORD` | Database password | (your password) |
| `DB_PORT` | Database port | `1433` |
| `JWT_ACCESS_TOKEN_LIFETIME` | Access token lifetime (minutes) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME` | Refresh token lifetime (minutes) | `43200` |
| `UPLOAD_BASE_PATH` | File upload directory | `/var/www/ksm_uploads` |
| `MAX_FILE_SIZE_MB` | Max upload size (MB) | `3` |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

### Frontend (`psc-frontend/.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend host URL (API prefix is appended by the client) | `http://localhost:8000` |
| `VITE_APP_ENV` | Environment name | `development` |

## Available Scripts

### Frontend

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server (HMR) |
| `npm run build` | Production build (type-check + bundle) |
| `npm run type-check` | TypeScript type checking only |
| `npm run lint` | ESLint check |
| `npm run format` | Prettier formatting |
| `npm run preview` | Preview production build locally |

### Backend

| Script | Description |
|--------|-------------|
| `python manage.py runserver` | Start development server |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Generate new migrations |
| `python manage.py check` | Verify Django configuration |
| `python manage.py check_overdue_actions` | Check for overdue corrective actions |

## Project Structure

```
psc-frontend/
  src/
    components/       # UI components (ui/, shared/, layout/, inspection/, car/, etc.)
    hooks/            # Custom React hooks
    lib/              # Utilities, API layer, validation, sync, PWA
    routes/           # Page components (file-based routing)
    stores/           # Zustand state stores
    types/            # TypeScript type definitions

psc-backend/
  core/               # Django project settings, root URLs
  apps/
    accounts/         # Authentication, role mapping, company logo, crew lookup
    masters/          # Master data (MOU, PSC codes, CLC, PIC)
    inspection/       # Inspections, deficiencies, dashboard, reports/DefIntel
    car/              # Corrective Action Reports
    notifications/    # Notification system
    sync/             # Offline sync protocol
```

## API Endpoints

All API endpoints are under `/api/psc/`:

| Prefix | App | Key Endpoints |
|--------|-----|---------------|
| `/api/psc/auth/` | accounts | login, refresh, me, crew, company-logo |
| `/api/psc/inspections/` | inspection | CRUD, submit, review, close |
| `/api/psc/deficiencies/` | inspection | list, allocate, workflow, action-code update |
| `/api/psc/cars/` | car | CRUD, workflow, available-actions, evidence, PV |
| `/api/psc/dashboard/` | inspection | aggregate KPIs, vessel drill-down |
| `/api/psc/reports/` | inspection | OpenSource import, checklist preview/export, prediction |
| `/api/psc/notifications/` | notifications | list, mark-read, unread-count |
| `/api/psc/sync/` | sync | pull, push, resolve-conflict |
| `/api/psc/masters/` | masters | MOU, PSC codes, CLC, PIC |

## Key Features

- **Inspection lifecycle:** DRAFT > SUBMITTED > PIC_REVIEWED > DPA_CLOSED
- **CAR unified workflow:** ALLOTTED > IN_PROGRESS > PENDING_CE_REVIEW > PENDING_MASTER_REVIEW > SUBMITTED_TO_PIC > PIC_REVIEW > SUBMITTED_TO_DPA > CLOSED
- **1:1 Deficiency-CAR:** Every deficiency auto-creates a CAR
- **Dashboard landing:** KPI dashboard with office vessel drill-down
- **Deficiency workflow page:** Dedicated `/deficiencies` route for allocation and review flows
- **Evidence management:** Before/After photo evidence for CARs
- **Physical verification:** On-board verification visits tracking
- **Offline-first PWA:** IndexedDB storage, sync queue, conflict resolution
- **Role-based access:** Vessel Master, Crew, Office (PIC/SSQE/Supt), DPA
- **Global reviewer mapping:** `mapping_role_user -> msc_profiles -> Mapping_CrewAssReviewers`
- **Notification system:** 11 notification types with real-time unread badge
- **DefIntel reports:** OpenSource import, checklist builder, def-code prediction
- **Export:** CAR PDF, Deficiency Excel, vessel preparation checklist
- **Company branding:** Office logo upload for PDF reports

## Documentation

All canonical documentation is in the `docs/` folder:

| File | Purpose |
|------|---------|
| `PRD.md` | Product requirements (FEAT-* IDs) |
| `APP_FLOW.md` | Screen layouts and user journeys |
| `BACKEND_STRUCTURE.md` | Database schema and API contracts |
| `LATER_CHANGES.md` | Later-added routes, files, tables, mappings, and workflow notes |
| `FRONTEND_GUIDELINES.md` | Component architecture and patterns |
| `DESIGN_SYSTEM.md` | Design tokens (colors, spacing, typography) |
| `VALIDATION_RULES.md` | Field validation rules |
| `TECH_STACK.md` | Locked dependency versions |
| `IMPLEMENTATION_PLAN.md` | Build sequence (8 phases) |
