# APP_FLOW.md - End-to-End Runtime Flow (Detailed)
## VIMS Inspection Module
**Version:** 3.0  
**Date:** 2026-02-23  
**Purpose:** Detailed functional flow from login screen design through complete defect/CAR lifecycle.

---

## 1. Entry, Auth, and Login Screen Design

### 1.1 Public Entry Behavior
- Public route: `/login`.
- If user is already authenticated and auth initialization is complete, `/login` redirects immediately to prior route (`location.state.from`) or `/dashboard`.
- While auth state initializes, login route shows full-page spinner.

### 1.2 Login Page Visual Design (Implemented)
- Page background:
  - Full-screen muted blue-gray surface (`#c3c9d0`) with radial overlay.
- Top-left label:
  - `Our Values` uppercase micro heading.
- Hero zone:
  - Large centered image card (cargo vessel image).
  - Overlayed horizontal line across hero.
  - Foreground value panel with:
    - Heading: `Innovation`
    - Supporting value statement text
    - Decorative `D` marker.
  - Secondary blurred value panel on very wide screens (`Care` panel).
- Side controls:
  - Circular left/right arrow buttons on desktop (`Previous value`, `Next value`).
  - Presentational only in current implementation (no value carousel logic wired).
- Login card:
  - Separate card below hero with heading `Sign in to your account`.
  - Contains reusable `LoginForm`.
- Footer:
  - `(c) {year} KSM. All rights reserved.`

### 1.3 Login Form UX and Validation
- Fields:
  - `username` (required)
  - `password` (required)
  - Password show/hide toggle.
- Validation:
  - Zod + react-hook-form.
  - Empty username => `Username is required`.
  - Empty password => `Password is required`.
- Error mapping logic:
  - Invalid credentials text from API => `Invalid email or password`.
  - Locked account text => `Account locked. Contact administrator.`
  - Network/connect issues => `Unable to connect. Check your connection.`
  - All others => pass-through API error message.
- Submit state:
  - Button text switches to `Signing in...` with spinner.
- Forgot password:
  - UI link present.
  - Current behavior is placeholder alert: `Password reset functionality coming soon.`

### 1.4 Auth Redirect Contract
- Protected pages use `AuthGuard`.
- Unauthenticated access to protected route:
  - Redirect to `/login`
  - Store attempted route in `state.from`.
- Post-login:
  - Return to `from` route if provided.
  - Else default to `/dashboard`.

---

## 2. Route Map, Guards, and Access Rules

| Route | Guard | Allowed Users | Notes |
|---|---|---|---|
| `/login` | Public | All | Authenticated users auto-redirect away. |
| `/` | `AuthGuard` + default redirect | Authenticated | Crew -> `/cars`; others -> `/dashboard`. |
| `/dashboard` | `AuthGuard` + `MasterOnlyGuard` | Master + Office | Crew redirected to `/cars`. |
| `/inspections` | `AuthGuard` + `MasterOnlyGuard` | Master + Office | Crew redirected to `/cars`. |
| `/inspections/new` | `AuthGuard` + `MasterOnlyGuard` | Master + Office | Create form has additional type/vessel constraints. |
| `/inspections/:id` | `AuthGuard` + `MasterOnlyGuard` | Master + Office | Detail page + deficiency add entry. |
| `/inspections/:id/edit` | `AuthGuard` + `MasterOnlyGuard` | Master + Office | Runtime status/role checks also applied. |
| `/inspections/:id/follow-up` | `AuthGuard` + `MasterOnlyGuard` | Master + Office route pass | Page logic + backend enforce Vessel Master for submit. |
| `/deficiencies` | `AuthGuard` + `MasterOnlyGuard` | Master + Office | Crew redirected to `/cars`. |
| `/cars` | `AuthGuard` | All authenticated | Main work page for crew. |
| `/cars/:id` | `AuthGuard` | All authenticated | Dynamic action buttons from backend available-actions. |
| `/cars/:id/edit` | `AuthGuard` | All authenticated | Object-level CAR edit permission enforced. |
| `/notifications` | `AuthGuard` | All authenticated | Accumulated pagination + mark read/all read. |
| `/sync` | `AuthGuard` + `MasterOnlyGuard` | Master + Office route pass | Sidebar hides for office, but direct URL works. |
| `/reports` | `AuthGuard` + `ReportsAccessGuard` | Office + eligible vessel ranks | Access via rank classification rules. |
| `/settings` | `AuthGuard` | All authenticated | Logo upload action restricted to office. |
| `*` | none | All | 404 fallback page. |

---

## 3. Navigation Model by Role

### 3.1 Sidebar and Bottom Nav Visibility
- Shared across authenticated pages through `RootLayout`.
- Desktop sidebar contains:
  - Dashboard, Inspections, Deficiencies, CARs, Notifications, Sync, Reports, Settings.
- Mobile bottom nav contains:
  - Dashboard, Inspections, Deficiencies, CARs, Notifications, Sync, Settings.
  - `Reports` is sidebar-only in current implementation.

### 3.2 Role Filters (Current)
- Vessel Master:
  - Dashboard, Inspections, Deficiencies, CARs, Notifications, Sync, Settings, Reports.
- Vessel Crew:
  - CARs, Notifications, Settings.
  - Reports appears only if `canAccessReports` rank logic passes.
- Office roles:
  - Dashboard, Inspections, CARs, Notifications, Reports, Settings.
  - Deficiencies route is accessible (guard allows), but sidebar item is configured vessel-only and may not appear.
  - Sync route is accessible by URL, but sidebar item is vessel-only and does not appear.

---

## 4. Core Data and State Model

### 4.1 Inspection Lifecycle (Stored)
`DRAFT -> SUBMITTED -> PIC_REVIEWED -> DPA_CLOSED`

### 4.2 Inspection Operational Status (Computed Open/Closed)
List filter/status chips use computed operational status:
- `CLOSED` when:
  - `def_reported = NO`, or
  - `def_reported = YES` and all deficiencies are action code `10`.
- `OPEN` when:
  - `def_reported = YES` and no deficiencies yet, or
  - at least one deficiency has action code null or not `10`.

### 4.3 Deficiency-CAR Coupling
- Deficiency creation auto-creates one CAR (1:1 relation).
- Legacy deficiency status (`def_status`) still exists, but CAR status is the primary workflow source.

### 4.4 Unified CAR Statuses
- `ALLOTTED`
- `IN_PROGRESS`
- `PENDING_CE_REVIEW`
- `PENDING_MASTER_REVIEW`
- `SUBMITTED_TO_PIC`
- `PIC_REVIEW`
- `SUBMITTED_TO_DPA`
- `CLOSED`
- `RETURNED_FOR_REWORK`

### 4.5 CAR Transition Matrix (Source of Truth)

| From | Action | To | Actor(s) | Comment Required |
|---|---|---|---|---|
| ALLOTTED | START_WORK | IN_PROGRESS | owner, master | No |
| IN_PROGRESS | MARK_COMPLETED | PENDING_CE_REVIEW | owner, master | No |
| PENDING_CE_REVIEW | APPROVE_AND_FORWARD | PENDING_MASTER_REVIEW | reviewer, master | No |
| PENDING_CE_REVIEW | RETURN_FOR_REWORK | IN_PROGRESS | reviewer, master | Yes |
| PENDING_MASTER_REVIEW | SUBMIT_TO_PIC | SUBMITTED_TO_PIC | master | No |
| PENDING_MASTER_REVIEW | RETURN_FOR_REWORK | IN_PROGRESS | master | Yes |
| SUBMITTED_TO_PIC | START_PIC_REVIEW | PIC_REVIEW | pic | No |
| SUBMITTED_TO_PIC | REQUEST_REWORK | PENDING_MASTER_REVIEW | pic, dpa | Yes |
| PIC_REVIEW | SUBMIT_TO_DPA | SUBMITTED_TO_DPA | pic | No |
| PIC_REVIEW | REQUEST_REWORK | PENDING_MASTER_REVIEW | pic, dpa | Yes |
| SUBMITTED_TO_DPA | CLOSE_CAR | CLOSED | dpa | Yes |
| SUBMITTED_TO_DPA | REQUEST_REWORK | PENDING_MASTER_REVIEW | dpa | Yes |
| CLOSED | REOPEN_CAR | PENDING_MASTER_REVIEW | dpa | Yes |

### 4.6 Physical Verification (PV) State
- Created after CAR is `CLOSED`.
- PV statuses: `OPEN`, `CLOSED`.
- Can close PV:
  - DPA, or
  - assigned verifier (office user matching verifier ID).

---

## 5. Detailed Screen Flows

### 5.1 Dashboard (`/dashboard`)
- Audience: master + office.
- Features:
  - KPI cards: inspections, overdue CARs, detentions, PV due.
  - Alerts with deep-link buttons.
  - Deficiency trend chart (monthly/yearly modes).
  - Avg DEFs/inspection KPI with DPA target setting dialog.
  - Repeat deficiencies panel with deep-links.
  - Top deficiency codes.
  - Recent inspections table with click-through to detail.
- Office can filter dashboard by vessel.

### 5.2 Inspection List (`/inspections`)
- Filters:
  - Inspection type (`PSC`, `RS`, `AUDIT`)
  - Operational status (`OPEN`, `CLOSED`)
  - Search
  - Detention toggle.
- Actions:
  - `Export Excel` (hidden for crew).
  - Floating `New Inspection` button (hidden for crew).
- Result cards show deficiency counts and operational status.

### 5.3 Create Inspection (`/inspections/new`)
- Form sections:
  - Inspection details
  - Inspection report upload
  - Deficiency placeholder (defects added after create).
- Core fields:
  - Type, PSC subtype (PSC only), date, port, country, MOU (PSC only), authority, inspector, detention + reason, `def_reported`.
- Type restrictions:
  - Vessel Master: can choose `PSC`, `RS`, `AUDIT`.
  - Others in current UI: `AUDIT` only.
- Report:
  - UI requires report on create.
  - File types: PDF/JPG/JPEG, max 3MB.
- Submit:
  - Creates draft inspection, then uploads report file.
  - On success -> inspection detail.
- Current constraint:
  - UI expects `user.vessel_id`; office vessel selection is not implemented here.

### 5.4 Inspection Detail (`/inspections/:id`)
- Displays:
  - Header metadata and operational status.
  - Report groups: Original and Follow-up.
  - Deficiencies list.
  - Activity history.
- Menu actions:
  - Edit inspection (vessel) and office assist edit.
  - Download all CARs (if linked CARs exist).
  - Register follow-up (PSC + vessel user path).
  - Delete inspection (vessel, only when no deficiencies).
- Deficiency add rules:
  - If `def_reported = NO`, add action is blocked and info banner shown.
  - If allowed, opens `DeficiencyModal`.

### 5.5 Edit Inspection (`/inspections/:id/edit`)
- Status/role edit matrix:
  - `DRAFT`: vessel master and office edit-assist.
  - `SUBMITTED`, `PIC_REVIEWED`: office edit-assist only.
  - `DPA_CLOSED`: read-only.
- Can replace report during edit.

### 5.6 Add Deficiency Modal
- Triggered from inspection detail.
- Required:
  - DefCode
  - Description
  - Action code.
- Optional:
  - Target date
  - Assigned crew.
- Auto-reviewer preview:
  - Derived from assigned crew rank and vessel crew list.
- On submit:
  - Creates deficiency.
  - Auto-creates linked CAR.

### 5.7 Deficiency Workflow Board (`/deficiencies`)
- Filters:
  - CAR status
  - `Awaiting Review` toggle.
- Card click opens detail dialog:
  - Def code details
  - Owner/reviewer
  - Linked CAR quick link
  - Workflow buttons in footer.
- Workflow actions in this dialog call unified CAR workflow transitions.

### 5.8 CAR List (`/cars`)
- Filters:
  - CAR status
  - Search
  - `PV Due`
  - `Overdue`
  - Optional vessel filter (URL-driven).
- Supports quick PV close flow when:
  - `PV Due` filter active and
  - user is DPA or assigned verifier.

### 5.9 CAR Detail (`/cars/:id`)
- Displays:
  - Deficiency summary
  - Root cause/CLC
  - Corrective actions
  - Evidence
  - Activity history
  - Audit (office context)
  - Physical verification section.
- Header menu:
  - Edit CAR (if editable)
  - Download External PDF
  - Download Internal PDF.
- Action area:
  - `CARWorkflowActions` from backend `/available-actions`.
  - Comment dialogs auto-open when transition requires comments.

### 5.10 CAR Edit (`/cars/:id/edit`)
- Editable sections:
  - Deficiency (read-only context)
  - Root cause analysis
  - CLC hierarchy multi-select
  - Immediate actions
  - Long-term actions
  - Target date
  - Evidence buckets (`BEFORE`, `AFTER`, `OTHER`).
- Sticky bottom actions:
  - Cancel
  - Save Draft
  - Submit (label is current forward workflow action).
- Submission checks (client + server for `SUBMIT_TO_PIC`):
  - Root cause >= 50 chars.
  - At least one CLC or custom cause.
  - At least one immediate action.
  - At least one long-term action.
  - At least one immediate action description >= 50 chars.
  - At least one long-term action description >= 50 chars.
  - At least one `BEFORE` evidence.
  - At least one `AFTER` evidence.

### 5.11 Follow-up Wizard (`/inspections/:id/follow-up`)
- Same-inspection follow-up (does not create a new inspection).
- Steps:
  1. Confirm context.
  2. Select open deficiencies.
  3. Update action codes + reinspection date.
  4. Optional follow-up report upload (PDF, max 5MB, description required if file selected).
  5. Confirm and submit.
- Submission behavior:
  - Writes `DeficiencyActionHistory` entries.
  - Updates deficiency action codes.
  - Optionally uploads follow-up report (`report_type = FOLLOW_UP`).
  - Does not auto-change CAR status.
  - Does not auto-set deficiency `is_cleared`.

### 5.12 Notifications (`/notifications`)
- Paginated feed with load-more accumulation.
- Grouped presentation by date in list component.
- Actions:
  - Per-item mark read.
  - Mark all read.

### 5.13 Sync (`/sync`)
- Blocks:
  - Connection and last-sync status.
  - Storage usage.
  - Pending changes/failed uploads.
  - Conflict list.
- Actions:
  - `Sync Now`
  - Conflict resolve (`KEEP_SERVER`, `KEEP_VESSEL`, `REOPEN_FOR_MERGE`)
  - `Clear Old Data`.

### 5.14 Reports / DefIntel (`/reports`)
- Access:
  - Office users.
  - Vessel users in rank categories `MASTER`, `CHIEF OFFICER`, `CHIEF ENGINEER`, `SECOND ENGINEER`.
- Sections:
  - A) OpenSource import (office import action only).
  - B) Checklist builder:
    - Scope modes: `VESSEL`, `FLEET`, `INSPECTOR`, `FILTER_COMBINED`.
    - Preview + export.
    - `FILTER_COMBINED` requires prior import.
  - C) Prediction:
    - Context: `PORT` or `MOU`.
    - Window: `LAST_24_MONTHS` or `ALL_TIME`.
    - Top-N output rows.
- Online/API reachability required.

### 5.15 Settings (`/settings`)
- Company logo panel for report branding.
- Upload:
  - Office-only action.
  - PNG/JPG, max 2MB.
- Non-office users get read-only display.

---

## 6. Complete Defect Cycle (Login to Closure)

### 6.1 Happy Path
1. User logs in on `/login`.
2. Master goes to inspections flow (`/inspections` -> `/inspections/new`).
3. Create draft inspection with `def_reported = YES` and upload report.
4. Open inspection detail and add deficiencies.
5. Each added deficiency auto-creates a CAR in `ALLOTTED`.
6. Owner/master executes vessel-side workflow:
   - `START_WORK` -> `IN_PROGRESS`
   - `MARK_COMPLETED` -> `PENDING_CE_REVIEW`
7. Reviewer/master performs review:
   - `APPROVE_AND_FORWARD` -> `PENDING_MASTER_REVIEW`.
8. Master sends to office:
   - `SUBMIT_TO_PIC` -> `SUBMITTED_TO_PIC` (after submission validation passes).
9. PIC flow:
   - `START_PIC_REVIEW` -> `PIC_REVIEW`
   - `SUBMIT_TO_DPA` -> `SUBMITTED_TO_DPA`.
10. DPA closes:
    - `CLOSE_CAR` -> `CLOSED` (comment required).
11. System auto-creates OPEN physical verification if none exists.
12. Assigned verifier or DPA closes PV in PV flow.

### 6.2 Rework Loop
- Rework can happen from:
  - `PENDING_CE_REVIEW` via `RETURN_FOR_REWORK`.
  - `PENDING_MASTER_REVIEW` via `RETURN_FOR_REWORK`.
  - `SUBMITTED_TO_PIC`, `PIC_REVIEW`, `SUBMITTED_TO_DPA` via `REQUEST_REWORK`.
- Rework target is vessel-side status (`IN_PROGRESS` or `PENDING_MASTER_REVIEW` based on source), then cycle continues to PIC/DPA again.

### 6.3 Reopen Loop
- DPA can reopen from `CLOSED`:
  - `REOPEN_CAR` -> `PENDING_MASTER_REVIEW` (comment required).
- Vessel and office complete corrections and re-submit through same pipeline.

### 6.4 Follow-up Path (Post Inspection)
- Vessel Master can run follow-up wizard for PSC inspections.
- Action code updates and follow-up report are stored on same inspection context.
- This is corrective follow-up documentation and action-code history; CAR closure remains controlled by CAR workflow.

### 6.5 No-Deficiency Path
- Inspection can be created with `def_reported = NO`.
- Operational status is `CLOSED`.
- Add-deficiency action is intentionally blocked until inspection is edited and `def_reported` is changed to `YES`.

---

## 7. Key Validation and Guardrails

### 7.1 Inspection
- Create PSC/RS: Vessel Master only.
- Submit inspection:
  - Inspection must be `DRAFT`.
  - Report must exist.

### 7.2 Deficiency
- Cannot add deficiency when inspection `def_reported = NO`.
- Deficiency create requires def code, text, action code.

### 7.3 CAR Workflow
- Available actions are role + status resolved by backend.
- Mandatory comment actions are enforced in backend (and prompted in UI).
- `SUBMIT_TO_PIC` blocked if content/evidence validation fails.

### 7.4 Follow-up
- Vessel Master only.
- PSC inspection only.
- Reinspection date cannot be future and cannot predate inspection date.
- Follow-up upload:
  - PDF only
  - max 5MB
  - description required when file attached.

---

## 8. API Surface Used by This Flow

| Domain | Main Endpoints |
|---|---|
| Auth | `/api/psc/auth/login/`, `/api/psc/auth/refresh/`, `/api/psc/auth/logout/`, `/api/psc/auth/me/` |
| Dashboard | `/api/psc/dashboard/` |
| Inspections | `/api/psc/inspections/`, `/api/psc/inspections/{id}/`, `/api/psc/inspections/{id}/update/`, `/api/psc/inspections/{id}/submit/`, `/api/psc/inspections/{id}/pic-review/`, `/api/psc/inspections/{id}/dpa-close/`, `/api/psc/inspections/{id}/upload-report/` |
| Deficiencies | `/api/psc/inspections/{inspection_id}/deficiencies/`, `/api/psc/deficiencies/`, `/api/psc/deficiencies/{id}/action-code/`, `/api/psc/deficiencies/{id}/workflow/`, `/api/psc/deficiencies/{id}/allocate/`, `/api/psc/inspections/{inspection_id}/deficiencies/bulk-submit/` |
| Follow-up | `/api/psc/inspections/{inspection_id}/follow-up/`, `/api/psc/psc-follow-up/register/` |
| CAR | `/api/psc/cars/`, `/api/psc/cars/{id}/`, `/api/psc/cars/{id}/update/`, `/api/psc/cars/{id}/workflow/`, `/api/psc/cars/{id}/available-actions/` |
| CAR Content | `/api/psc/cars/{car_id}/evidence/`, `/api/psc/evidence/{id}/`, `/api/psc/cars/{car_id}/actions/`, `/api/psc/actions/{id}/`, `/api/psc/actions/{id}/complete/`, `/api/psc/actions/{id}/delete/` |
| Physical Verification | `/api/psc/cars/{car_id}/physical-verification/`, `/api/psc/physical-verifications/{id}/`, `/api/psc/physical-verifications/{id}/close/` |
| Reports | `/api/psc/reports/opensource/import/`, `/api/psc/reports/vessel-prep/preview/`, `/api/psc/reports/vessel-prep/export/`, `/api/psc/reports/defintel/predict-defcodes/` |
| Sync | `/api/psc/sync/*` |
| Notifications | `/api/psc/notifications/*` |
| Masters | `/api/psc/masters/*` |

---

## 9. Current Implementation Notes

- Sync route access:
  - Route guard allows office users, but navigation item is vessel-only.
- Reports navigation:
  - Present in desktop sidebar; not in mobile bottom nav.
- Deficiency and CAR dual-state:
  - Legacy `def_status` still exists for compatibility and some bulk logic.
  - Operational workflow is CAR status transitions.
- CAR close action:
  - Closing CAR marks `verification_pending` and auto-creates an OPEN PV when none exists.

---

## Document Control

- Previous version: `2.0` (condensed runtime map)
- Current version: `3.0` (detailed login design through full defect cycle)
- Updated by: Codex
