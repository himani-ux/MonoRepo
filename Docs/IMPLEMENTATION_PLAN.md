# IMPLEMENTATION_PLAN.md — Master Build Sequence
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.0 | **Date:** 2026-02-03

---

## Overview

This document is the **master blueprint** for implementation. It does not get modified during execution. Progress is tracked in `progress.txt`. Session tasks are tracked in `tasks/todo.md`.

**Total Phases:** 8  
**Estimated Duration:** 12-16 weeks  
**Team Size:** 2-3 developers

---

## Phase 1: Project Foundation
**Duration:** 1 week  
**Dependencies:** None  
**Deliverable:** Working development environment with CI/CD

### Step 1.1: Initialize Frontend Project
**Files to create:**
- `package.json`
- `tsconfig.json`
- `vite.config.ts`
- `tailwind.config.js`
- `postcss.config.js`
- `.eslintrc.js`
- `.prettierrc`
- `.gitignore`

**Actions:**
1. Initialize Vite + React + TypeScript project
2. Install dependencies from TECH_STACK.md exactly:
   - React 18.3.1
   - TypeScript 5.4.5
   - Tailwind CSS 3.4.7
   - @tanstack/react-query 5.51.0
   - zustand 4.5.4
   - react-hook-form 7.52.1
   - zod 3.23.8
   - axios 1.7.2
   - lucide-react 0.408.0
   - idb 8.0.0
3. Configure Tailwind with tokens from DESIGN_SYSTEM.md
4. Set up ESLint + Prettier

**Verification:**
- [ ] `npm run dev` starts without errors
- [ ] Tailwind classes compile correctly
- [ ] TypeScript strict mode enabled

### Step 1.2: Initialize Backend Project
**Files to create:**
- `requirements.txt`
- `pyproject.toml`
- `manage.py`
- `core/settings.py`
- `core/urls.py`
- `.env.example`

**Actions:**
1. Create Django 5.2.7 project
2. Install dependencies from TECH_STACK.md:
   - Django 5.2.7
   - djangorestframework 3.14.0
   - djangorestframework-simplejwt 5.3.1
   - django-cors-headers 4.4.0
   - pyodbc 5.1.0
   - mssql-django 1.4
   - reportlab 4.2.0
   - openpyxl 3.1.5
3. Configure SQL Server connection
4. Set up JWT authentication

**Verification:**
- [ ] `python manage.py runserver` starts
- [ ] Database connection verified
- [ ] JWT token generation works

### Step 1.3: Set Up Project Structure
**Files to create:**
- Full folder structure per FRONTEND_GUIDELINES.md Section 1
- `src/lib/utils/cn.ts`
- `src/lib/utils/constants.ts`
- `src/types/index.ts`

**Actions:**
1. Create all folders as specified in FRONTEND_GUIDELINES.md
2. Set up path aliases (@/components, @/lib, etc.)
3. Create utility functions

**Verification:**
- [ ] All folders exist
- [ ] Path aliases resolve correctly
- [ ] No TypeScript errors

### Step 1.4: Install & Configure shadcn/ui
**Files to create:**
- `components.json`
- `src/components/ui/button.tsx`
- `src/components/ui/input.tsx`
- `src/components/ui/card.tsx`
- `src/components/ui/badge.tsx`
- `src/components/ui/dialog.tsx`
- `src/components/ui/select.tsx`
- `src/components/ui/toast.tsx`
- `src/components/ui/skeleton.tsx`

**Actions:**
1. Run `npx shadcn@latest init`
2. Install required components
3. Customize theme to match DESIGN_SYSTEM.md tokens

**Verification:**
- [ ] All UI components render correctly
- [ ] Colors match DESIGN_SYSTEM.md
- [ ] Components are accessible

### Step 1.5: Set Up CI/CD
**Files to create:**
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `Dockerfile` (frontend)
- `Dockerfile` (backend)
- `docker-compose.yml`

**Actions:**
1. Configure GitHub Actions for linting/testing
2. Set up deployment pipeline
3. Configure Docker for local development

**Verification:**
- [ ] CI runs on push/PR
- [ ] Docker containers build successfully
- [ ] Local development works via Docker

---

## Phase 2: Authentication & Core Layout
**Duration:** 1 week  
**Dependencies:** Phase 1 complete  
**Deliverable:** Working auth flow and app shell

### Step 2.1: Implement Authentication Backend
**Files to create:**
- `apps/accounts/models.py`
- `apps/accounts/serializers.py`
- `apps/accounts/views.py`
- `apps/accounts/urls.py`

**Features:** FEAT-AUTH-001, FEAT-AUTH-002

**Actions:**
1. Create User model extending existing core.office_users_v, core.vessel_users_v
2. Implement JWT token endpoints per BACKEND_STRUCTURE.md
3. Set up RBAC middleware
4. Create login/logout/refresh endpoints

**API Endpoints:**
- `POST /api/psc/auth/login/`
- `POST /api/psc/auth/refresh/`
- `POST /api/psc/auth/logout/`
- `GET /api/psc/auth/me/`

**Verification:**
- [ ] Login returns access + refresh tokens
- [ ] Protected endpoints require valid token
- [ ] User roles correctly determined

### Step 2.2: Implement Auth Store & Hooks
**Files to create:**
- `src/stores/auth-store.ts`
- `src/hooks/use-auth.ts`
- `src/lib/api/client.ts`
- `src/lib/api/auth.ts`

**Actions:**
1. Create Zustand auth store with token management
2. Set up Axios interceptors for auth headers
3. Handle token refresh logic
4. Implement auth hooks

**Verification:**
- [ ] Token persists across page refresh
- [ ] Automatic token refresh works
- [ ] Logout clears all auth state

### Step 2.3: Build Login Page
**Files to create:**
- `src/routes/login.tsx`
- `src/components/auth/login-form.tsx`

**Screen:** Login (`/login`) per APP_FLOW.md Section 2.1

**Actions:**
1. Build login form with email/password
2. Implement validation
3. Handle error states per APP_FLOW.md
4. Redirect to /inspections on success

**Verification:**
- [ ] Form validates correctly
- [ ] Error messages display properly
- [ ] Successful login redirects

### Step 2.4: Build App Shell & Navigation
**Files to create:**
- `src/routes/layout.tsx`
- `src/components/layout/header.tsx`
- `src/components/layout/sidebar.tsx`
- `src/components/layout/bottom-nav.tsx`
- `src/components/layout/page-header.tsx`

**Screen:** Main navigation per APP_FLOW.md Section 3.1

**Actions:**
1. Create responsive layout (bottom nav mobile, sidebar desktop)
2. Implement navigation items per user role
3. Add notification badge component
4. Style per DESIGN_SYSTEM.md

**Verification:**
- [ ] Navigation responsive at all breakpoints
- [ ] Correct items shown per role
- [ ] Active state highlights correctly

### Step 2.5: Implement Route Protection
**Files to create:**
- `src/components/auth/auth-guard.tsx`
- `src/components/auth/role-guard.tsx`

**Actions:**
1. Create auth guard that redirects to login
2. Create role-based access guard
3. Apply to protected routes

**Verification:**
- [ ] Unauthenticated users redirected to login
- [ ] Role restrictions enforced
- [ ] Loading states during auth check

---

## Phase 3: Master Data & Core Components
**Duration:** 1 week  
**Dependencies:** Phase 2 complete  
**Deliverable:** All master data loaded, shared components built

### Step 3.1: Implement Master Data API
**Files to create:**
- `apps/masters/models.py`
- `apps/masters/serializers.py`
- `apps/masters/views.py`
- `apps/masters/urls.py`

**Actions:**
1. Create read-only endpoints for master data:
   - MOU codes
   - PSC action codes
   - PSC deficiency codes
   - CLC items
   - PIC codes
2. Implement caching (Redis or in-memory)

**API Endpoints:**
- `GET /api/psc/masters/mou/`
- `GET /api/psc/masters/psc-action-codes/`
- `GET /api/psc/masters/psc-def-codes/`
- `GET /api/psc/masters/clc/`
- `GET /api/psc/masters/pic/`

**Verification:**
- [ ] All endpoints return correct data
- [ ] Caching reduces DB load
- [ ] Search/filter works

### Step 3.2: Implement Masters Hooks & Caching
**Files to create:**
- `src/hooks/use-masters.ts`
- `src/lib/api/masters.ts`

**Actions:**
1. Create TanStack Query hooks for master data
2. Set staleTime to 24 hours (rarely changes)
3. Prefetch on app load

**Verification:**
- [ ] Master data cached correctly
- [ ] No unnecessary refetches
- [ ] Available offline (Phase 7)

### Step 3.3: Build Shared Components
**Files to create:**
- `src/components/shared/status-badge.tsx`
- `src/components/shared/date-picker.tsx`
- `src/components/shared/file-upload.tsx`
- `src/components/shared/search-input.tsx`
- `src/components/shared/empty-state.tsx`
- `src/components/shared/error-state.tsx`
- `src/components/shared/loading-skeleton.tsx`
- `src/components/shared/confirm-dialog.tsx`
- `src/components/shared/def-code-select.tsx`

**Actions:**
1. Build each component per DESIGN_SYSTEM.md tokens
2. Make DefCode select searchable with code + description
3. Create reusable empty/error/loading states per APP_FLOW.md

**Verification:**
- [ ] All components match design system
- [ ] DefCode select shows code prominently
- [ ] File upload accepts PDF/JPG/JPEG only, 3MB max

---

## Phase 4: Inspection Module
**Duration:** 2 weeks  
**Dependencies:** Phase 3 complete  
**Deliverable:** Complete inspection CRUD with deficiency management

### Step 4.1: Implement Inspection Backend
**Files to create:**
- `apps/inspection/models.py` (per BACKEND_STRUCTURE.md Part 2)
- `apps/inspection/serializers.py`
- `apps/inspection/views.py`
- `apps/inspection/urls.py`
- `apps/inspection/permissions.py`

**Features:** FEAT-INS-001 through FEAT-INS-011

**Actions:**
1. Create Inspection model per schema
2. Implement CRUD endpoints per API contracts
3. Add RBAC per permission matrix
4. Implement submit workflow

**API Endpoints:**
- `GET /api/psc/inspections/`
- `POST /api/psc/inspections/`
- `GET /api/psc/inspections/{id}/`
- `PUT /api/psc/inspections/{id}/`
- `DELETE /api/psc/inspections/{id}/`
- `POST /api/psc/inspections/{id}/submit/`
- `POST /api/psc/inspections/{id}/pic-review/`
- `POST /api/psc/inspections/{id}/dpa-close/`
- `POST /api/psc/inspections/{id}/upload-report/`

**Verification:**
- [ ] All endpoints match API contracts
- [ ] RBAC enforced correctly
- [ ] State transitions work

### Step 4.2: Implement Deficiency Backend
**Files to create:**
- `apps/inspection/deficiency_models.py`
- `apps/inspection/deficiency_serializers.py`
- `apps/inspection/deficiency_views.py`

**Features:** FEAT-DEF-001 through FEAT-DEF-003, FEAT-INS-003

**Actions:**
1. Create Deficiency model per schema
2. Create auto-CAR trigger (database-level)
3. Implement action code update with history

**API Endpoints:**
- `GET /api/psc/deficiencies/`
- `POST /api/psc/inspections/{inspection_id}/deficiencies/`
- `GET /api/psc/deficiencies/{id}/`
- `PUT /api/psc/deficiencies/{id}/`
- `PUT /api/psc/deficiencies/{id}/action-code/`

**Verification:**
- [ ] Adding deficiency auto-creates CAR
- [ ] Action code history recorded
- [ ] DefCode validation works

### Step 4.3: Implement PSC Follow-up Backend
**Files to create:**
- `apps/inspection/followup_views.py`

**Features:** FEAT-DEF-002

**Actions:**
1. Implement follow-up registration endpoint
2. Create follow-up inspection linked to parent
3. Batch update deficiency action codes

**API Endpoints:**
- `POST /api/psc/psc-follow-up/register/`

**Verification:**
- [ ] Follow-up creates new inspection with parent link
- [ ] Deficiency action codes updated
- [ ] Activity events created

### Step 4.4: Build Inspection List Page
**Files to create:**
- `src/routes/inspections/index.tsx`
- `src/components/inspection/inspection-list.tsx`
- `src/components/inspection/inspection-card.tsx`
- `src/components/inspection/inspection-filters.tsx`
- `src/hooks/use-inspections.ts`
- `src/lib/api/inspections.ts`

**Screen:** Inspection List (`/inspections`) per APP_FLOW.md Section 2.2

**Features:** FEAT-INS-010

**Actions:**
1. Implement list with filters
2. Build inspection card with all states
3. Add detention highlighting
4. Implement empty states
5. Add FAB for create

**Verification:**
- [ ] List loads with pagination
- [ ] Filters work correctly
- [ ] Detention rows highlighted
- [ ] Empty state shows when no data

### Step 4.5: Build Create Inspection Page
**Files to create:**
- `src/routes/inspections/new.tsx`
- `src/components/inspection/inspection-form.tsx`
- `src/lib/validations/inspection.ts`

**Screen:** Create Inspection (`/inspections/new`) per APP_FLOW.md Section 2.2

**Features:** FEAT-INS-001, FEAT-INS-002

**Actions:**
1. Build form with conditional PSC fields
2. Implement validation per PRD
3. Add report upload
4. Create draft and navigate

**Verification:**
- [ ] Form validates correctly
- [ ] PSC subtype required for PSC type
- [ ] Report upload works
- [ ] Creates inspection in DRAFT status

### Step 4.6: Build Add Deficiency Modal
**Files to create:**
- `src/components/inspection/deficiency-modal.tsx`
- `src/lib/validations/deficiency.ts`

**Screen:** Add Deficiency Modal per APP_FLOW.md Section 2.2

**Features:** FEAT-INS-003

**Actions:**
1. Build modal with DefCode search select
2. Show CAR auto-creation notice
3. Validate required fields

**Verification:**
- [ ] DefCode shows code prominently
- [ ] CAR created automatically
- [ ] Validation works

### Step 4.7: Build Inspection Detail Page
**Files to create:**
- `src/routes/inspections/[id].tsx`
- `src/components/inspection/inspection-detail.tsx`
- `src/components/inspection/deficiency-list.tsx`
- `src/components/inspection/deficiency-card.tsx`
- `src/hooks/use-inspection.ts`

**Screen:** Inspection Detail (`/inspections/:id`) per APP_FLOW.md Section 2.2

**Features:** FEAT-INS-011

**Actions:**
1. Build detail view with all sections
2. List deficiencies with CAR status
3. Show activity history
4. Conditional action buttons by status/role

**Verification:**
- [ ] All details display correctly
- [ ] DefCode prominent on deficiency cards
- [ ] Correct actions per status/role

### Step 4.8: Build Edit Inspection & Follow-up Pages
**Files to create:**
- `src/routes/inspections/[id].edit.tsx`
- `src/routes/inspections/[id].follow-up.tsx`
- `src/components/inspection/follow-up-form.tsx`

**Screens:** Edit Inspection, Register Follow-up per APP_FLOW.md

**Features:** FEAT-INS-007, FEAT-INS-008, FEAT-DEF-002

**Actions:**
1. Build edit form (reuse inspection-form)
2. Build follow-up form with deficiency selection
3. Implement batch action code updates

**Verification:**
- [ ] Edit works for allowed statuses
- [ ] Follow-up updates deficiencies
- [ ] Notifications triggered

---

## Phase 5: CAR Module
**Duration:** 2 weeks  
**Dependencies:** Phase 4 complete  
**Deliverable:** Complete CAR lifecycle management

### Step 5.1: Implement CAR Backend
**Files to create:**
- `apps/car/models.py` (per BACKEND_STRUCTURE.md Part 2)
- `apps/car/serializers.py`
- `apps/car/views.py`
- `apps/car/urls.py`
- `apps/car/permissions.py`

**Features:** FEAT-CAR-001 through FEAT-CAR-012

**Actions:**
1. Create CAR model per schema
2. Create Corrective Action model
3. Create Attachment model
4. Implement all state transitions
5. Add activity events and audit logs

**API Endpoints:**
- `GET /api/psc/cars/`
- `GET /api/psc/cars/{id}/`
- `PUT /api/psc/cars/{id}/`
- `POST /api/psc/cars/{id}/submit/`
- `POST /api/psc/cars/{id}/pic-accept/`
- `POST /api/psc/cars/{id}/request-rework/`
- `POST /api/psc/cars/{id}/dpa-close/`
- `POST /api/psc/cars/{id}/reopen/`
- `POST /api/psc/cars/{car_id}/evidence/`
- `DELETE /api/psc/evidence/{id}/`
- `POST /api/psc/cars/{car_id}/actions/`
- `PUT /api/psc/actions/{id}/`
- `POST /api/psc/actions/{id}/complete/`

**Verification:**
- [ ] All endpoints match API contracts
- [ ] State transitions enforce rules
- [ ] Evidence validation works
- [ ] Activity events created

### Step 5.2: Build CAR List Page
**Files to create:**
- `src/routes/cars/index.tsx`
- `src/components/car/car-list.tsx`
- `src/components/car/car-card.tsx`
- `src/components/car/car-filters.tsx`
- `src/hooks/use-cars.ts`
- `src/lib/api/cars.ts`

**Screen:** CAR List (`/cars`) per APP_FLOW.md Section 2.3

**Features:** FEAT-CAR-009

**Actions:**
1. Build list with filters
2. Show overdue highlighting
3. Show missing evidence indicator

**Verification:**
- [ ] List loads with pagination
- [ ] Overdue CARs highlighted red
- [ ] Filters work correctly

### Step 5.3: Build CAR Detail Page
**Files to create:**
- `src/routes/cars/[id].tsx`
- `src/components/car/car-detail.tsx`
- `src/components/car/root-cause-section.tsx`
- `src/components/car/corrective-action-list.tsx`
- `src/components/car/corrective-action-item.tsx`
- `src/components/car/evidence-section.tsx`
- `src/components/car/activity-history.tsx`
- `src/components/car/audit-log.tsx`
- `src/hooks/use-car.ts`

**Screen:** CAR Detail (`/cars/:id`) per APP_FLOW.md Section 2.3

**Features:** FEAT-CAR-010

**Actions:**
1. Build all sections per APP_FLOW.md layout
2. Show DefCode prominently
3. Evidence thumbnails with lightbox
4. Activity history for all users
5. Audit log for Office/DPA only

**Verification:**
- [ ] All sections display correctly
- [ ] DefCode visible on deficiency section
- [ ] Audit log only visible to Office/DPA

### Step 5.4: Build Edit CAR Page
**Files to create:**
- `src/routes/cars/[id].edit.tsx`
- `src/components/car/car-form.tsx`
- `src/lib/validations/car.ts`

**Screen:** Edit CAR (`/cars/:id/edit`) per APP_FLOW.md Section 2.3

**Features:** FEAT-CAR-002, FEAT-CAR-011

**Actions:**
1. Build form with all sections
2. CLC code multi-select with search
3. Corrective action management
4. Validation per submission rules

**Verification:**
- [ ] Form validates on submit
- [ ] Root cause min 50 chars enforced
- [ ] At least 1 immediate + 1 long-term action

### Step 5.5: Build Evidence Upload Modal
**Files to create:**
- `src/components/car/evidence-upload-modal.tsx`
- `src/lib/validations/evidence.ts`

**Screen:** Upload Evidence Modal per APP_FLOW.md Section 2.3

**Features:** FEAT-CAR-003

**Actions:**
1. Build modal with type selection
2. File validation (PDF/JPG/JPEG, 3MB)
3. Required description field

**Verification:**
- [ ] File type validation works
- [ ] Size limit enforced
- [ ] Description required

### Step 5.6: Build Office Review Modals
**Files to create:**
- `src/components/car/pic-accept-modal.tsx`
- `src/components/car/rework-modal.tsx`
- `src/components/car/dpa-close-modal.tsx`

**Screens:** PIC Accept/Rework/DPA Close per APP_FLOW.md Section 2.4

**Features:** FEAT-CAR-005, FEAT-CAR-006, FEAT-CAR-007

**Actions:**
1. Build accept modal with mandatory comment
2. Build rework modal with min 20 char reason
3. Build DPA close modal with optional PV scheduling

**Verification:**
- [ ] Comments/reasons enforced
- [ ] State transitions work
- [ ] Notifications triggered

---

## Phase 6: Reports & Physical Verification
**Duration:** 1 week  
**Dependencies:** Phase 5 complete  
**Deliverable:** PDF/Excel exports, PV management

### Step 6.1: Implement CAR PDF Export
**Files to create:**
- `apps/car/reports.py`
- `apps/car/templates/car_report.html`

**Features:** FEAT-RPT-001

**Actions:**
1. Create HTML template per DESIGN_SYSTEM.md Section 12
2. Generate PDF with WeasyPrint
3. Include all CAR sections

**Verification:**
- [ ] PDF generates correctly
- [ ] Styling matches spec
- [ ] All data included

### Step 6.2: Implement Deficiency Excel Export
**Files to create:**
- `apps/inspection/reports.py`

**Features:** FEAT-RPT-002

**Actions:**
1. Create multi-sheet Excel with openpyxl
2. Apply styling per spec
3. Add filters and detention highlighting

**Verification:**
- [ ] Excel generates with all sheets
- [ ] Styling applied correctly
- [ ] Auto-filter enabled

### Step 6.3: Implement Physical Verification Backend
**Files to create:**
- `apps/car/pv_views.py`

**Features:** FEAT-PV-001, FEAT-PV-002

**Actions:**
1. Create Physical Verification model (already in schema)
2. Implement create/close endpoints
3. Add to CAR detail response

**API Endpoints:**
- `POST /api/psc/cars/{car_id}/physical-verification/`
- `PUT /api/psc/physical-verifications/{id}/`
- `POST /api/psc/physical-verifications/{id}/close/`

**Verification:**
- [ ] PV only creatable for DPA_CLOSED CARs
- [ ] Close requires visit_date and comments

### Step 6.4: Build Physical Verification UI
**Files to create:**
- `src/components/car/physical-verification-section.tsx`
- `src/components/car/pv-create-modal.tsx`
- `src/components/car/pv-close-modal.tsx`

**Actions:**
1. Add PV section to CAR detail
2. Build create/close modals

**Verification:**
- [ ] PV section shows on closed CARs
- [ ] Create/close work correctly

---

## Phase 7: Offline & Sync
**Duration:** 2 weeks  
**Dependencies:** Phase 6 complete  
**Deliverable:** Full offline capability with conflict resolution

### Step 7.1: Implement Sync Backend
**Files to create:**
- `apps/sync/views.py`
- `apps/sync/serializers.py`
- `apps/sync/conflict_resolver.py`

**Features:** FEAT-SYNC-002 through FEAT-SYNC-005

**Actions:**
1. Implement pull endpoint with delta sync
2. Implement push endpoint with presigned URLs
3. Implement conflict detection and resolution

**API Endpoints:**
- `POST /api/psc/sync/pull/`
- `POST /api/psc/sync/push/`
- `POST /api/psc/sync/resolve-conflict/`

**Verification:**
- [ ] Delta sync returns only changes
- [ ] Push handles partial failures
- [ ] Conflict resolution works

### Step 7.2: Set Up IndexedDB
**Files to create:**
- `src/lib/db/index.ts`
- `src/lib/db/inspections.ts`
- `src/lib/db/cars.ts`
- `src/lib/db/sync-queue.ts`
- `src/lib/db/masters.ts`

**Features:** FEAT-SYNC-001

**Actions:**
1. Create IndexedDB schema per FRONTEND_GUIDELINES.md
2. Implement CRUD operations for each store
3. Create sync queue management

**Verification:**
- [ ] All stores created correctly
- [ ] CRUD operations work
- [ ] Data persists across sessions

### Step 7.3: Implement Offline Data Layer
**Files to create:**
- `src/hooks/use-offline.ts`
- `src/hooks/use-offline-inspections.ts`
- `src/hooks/use-offline-cars.ts`
- `src/stores/sync-store.ts`

**Actions:**
1. Create hooks that read from IndexedDB when offline
2. Queue mutations when offline
3. Track pending changes count

**Verification:**
- [ ] Data reads from cache when offline
- [ ] Mutations queue correctly
- [ ] Pending count updates

### Step 7.4: Implement Sync Service
**Files to create:**
- `src/lib/sync/sync-service.ts`
- `src/lib/sync/attachment-uploader.ts`

**Features:** FEAT-SYNC-003, FEAT-SYNC-006

**Actions:**
1. Implement pull/push logic
2. Handle attachment uploads with retry
3. Implement exponential backoff (1s, 2s, 4s)

**Verification:**
- [ ] Sync completes successfully
- [ ] Retry logic works
- [ ] Failed uploads marked and retryable

### Step 7.5: Build Sync Status Page
**Files to create:**
- `src/routes/sync/page.tsx`
- `src/components/sync/sync-status.tsx`
- `src/components/sync/storage-indicator.tsx`
- `src/components/sync/pending-changes.tsx`
- `src/components/sync/conflict-list.tsx`
- `src/components/sync/offline-banner.tsx`

**Screen:** Sync Status (`/sync`) per APP_FLOW.md Section 2.5

**Actions:**
1. Build all sections per APP_FLOW.md layout
2. Show storage usage (150MB limit)
3. Show pending changes and failed uploads
4. Show conflicts awaiting resolution

**Verification:**
- [ ] Storage meter accurate
- [ ] Pending changes listed
- [ ] Sync Now button triggers sync

### Step 7.6: Implement Conflict Resolution UI
**Files to create:**
- `src/components/sync/conflict-resolution-modal.tsx`

**Features:** FEAT-SYNC-005

**Actions:**
1. Build modal showing vessel vs server changes
2. Implement resolution options (KEEP_SERVER, KEEP_VESSEL, REOPEN)
3. Only available to Office users

**Verification:**
- [ ] Conflicts displayed clearly
- [ ] Resolution options work
- [ ] Vessel notified of resolution

---

## Phase 8: Notifications & Polish
**Duration:** 1 week  
**Dependencies:** Phase 7 complete  
**Deliverable:** Production-ready application

### Step 8.1: Implement Notification System
**Files to create:**
- `apps/notifications/models.py`
- `apps/notifications/views.py`
- `apps/notifications/signals.py`

**Features:** FEAT-NOTIF-001

**Actions:**
1. Create Notification model
2. Implement notification triggers via signals
3. Create list/mark-read endpoints

**API Endpoints:**
- `GET /api/psc/notifications/`
- `POST /api/psc/notifications/mark-read/`
- `POST /api/psc/notifications/mark-all-read/`

**Verification:**
- [ ] Notifications created on triggers
- [ ] Correct recipients per PRD

### Step 8.2: Build Notification UI
**Files to create:**
- `src/routes/notifications/page.tsx`
- `src/components/notification/notification-list.tsx`
- `src/components/notification/notification-item.tsx`
- `src/components/notification/notification-badge.tsx`
- `src/hooks/use-notifications.ts`
- `src/stores/notification-store.ts`

**Screen:** Notification Center (`/notifications`) per APP_FLOW.md Section 2.6

**Actions:**
1. Build notification list with grouping
2. Add badge to header/nav
3. Implement mark-read functionality

**Verification:**
- [ ] Notifications display correctly
- [ ] Badge shows unread count
- [ ] Mark read works

### Step 8.3: Implement Service Worker (PWA)
**Files to create:**
- `public/sw.js`
- `src/lib/pwa/register-sw.ts`
- `public/manifest.json`

**Actions:**
1. Configure Workbox for caching
2. Cache app shell and static assets
3. Handle offline fallback

**Verification:**
- [ ] App installable as PWA
- [ ] Works offline
- [ ] Updates detected

### Step 8.4: Performance Optimization
**Actions:**
1. Implement code splitting
2. Optimize bundle size
3. Add image lazy loading
4. Implement virtualized lists for large data

**Verification:**
- [ ] Lighthouse score > 90
- [ ] Initial load < 2s on 3G
- [ ] No unnecessary re-renders

### Step 8.5: Accessibility Audit
**Actions:**
1. Run aXe audit
2. Fix any WCAG 2.1 AA violations
3. Test with screen reader
4. Verify keyboard navigation

**Verification:**
- [ ] No critical accessibility issues
- [ ] All forms keyboard accessible
- [ ] Focus management correct

### Step 8.6: Final Testing & Documentation
**Actions:**
1. Write E2E tests for critical paths
2. Update README with setup instructions
3. Create user guide
4. Final QA pass

**Verification:**
- [ ] E2E tests pass
- [ ] Documentation complete
- [ ] No critical bugs

---

## Phase Dependencies Diagram

```
Phase 1: Foundation
    ↓
Phase 2: Auth & Layout
    ↓
Phase 3: Masters & Components
    ↓
Phase 4: Inspections ←──────┐
    ↓                       │
Phase 5: CARs ──────────────┘
    ↓
Phase 6: Reports & PV
    ↓
Phase 7: Offline & Sync
    ↓
Phase 8: Notifications & Polish
```

---

## Document References

| Document | Usage |
|----------|-------|
| PRD.md | Feature IDs (FEAT-*) for each step |
| APP_FLOW.md | Screen specifications |
| DESIGN_SYSTEM.md | Visual tokens |
| FRONTEND_GUIDELINES.md | Component patterns |
| BACKEND_STRUCTURE.md | API contracts, database schema |
| VALIDATION_RULES.md | Field validation rules |
| TECH_STACK.md | Exact versions to install |
| BACKEND_STRUCTURE.md Part 2 | Shared database tables (VesselData, HRM501, etc.) |

---

**Document Control:**
- Created: 2026-02-03
- Updated: 2026-02-04
- Author: System Generated
- This document does not change during execution

## Amendment 29 - 2026-08-14

The Audit module is synced into the maintained Complete VIMS repository from the Audit handover workspace as a separate maintained module. This amendment supersedes the original PSC-only scope wherever it omitted Audit runtime support.

Triggering discovery: the handover includes Audit-specific backend code under `apps/inspection/audit`, frontend code under `src/routes/audit`, `src/components/audit`, `src/hooks/audit`, `src/schemas/audit`, and `src/stores/audit`, plus new inspection migrations for Audit domain/master tables and Audit workflow support.

Implementation boundary: only Audit-related code and docs are imported. Existing non-Audit PSC, Safety, Certs, Circular, ORB, and shared module files are not overwritten from the handover. Shared files receive only isolated Audit route/navigation/permission additions required to wire the module.

Migration note: the current maintained repo already contains `inspection` migration `0017_alter_inspectionreport_description.py`. Audit handover migrations are renumbered after that migration chain so existing migration history is preserved.

## Amendment 30 - 2026-08-17

The post-sync Audit gap-resolution package was reviewed and safely folded into the maintained repo. The current repo imports the revised Audit runtime gap evidence, approved mock references, the Audit create-page route permission allowance, and the ORB decorator correction that removes unsafe `AllowAny` activation from four function views. Broad source-workspace dependency updates and unrelated PSC/Safety changes are intentionally excluded. No database changes are executed by this amendment; the `msc_profiles` live update noted in the handover remains an operational record pending environment-specific deployment handling.
