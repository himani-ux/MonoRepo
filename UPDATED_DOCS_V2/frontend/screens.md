# Frontend Screens

This document lists the main screens and key modals in the current VIMS frontend.

## 1. Login Screen

- Module: Authentication
- Route: `/login`
- Purpose: authenticate the user and redirect to the correct landing page
- Components:
  - `LoginForm`
  - centered shell card
  - company logo icon
- API integrations:
  - `POST /api/psc/auth/login/`

Wireframe:

```text
--------------------------------------------------
|                 VIMS Logo                       |
|             PSC / RS / Audit                    |
|                                                |
|   +----------------------------------------+   |
|   | Username                               |   |
|   +----------------------------------------+   |
|   +----------------------------------------+   |
|   | Password                               |   |
|   +----------------------------------------+   |
|                [ Sign In ]                     |
|                                                |
|          Footer copyright / status              |
--------------------------------------------------
```

## 2. Dashboard

- Module: Inspection
- Route: `/dashboard`
- Purpose: show KPI summary, trends, repeat deficiencies, and vessel drill-down
- Components:
  - `StatCard`
  - `TopDefCodes`
  - charts
  - repeated deficiency panel
  - vessel selector modal
- API integrations:
  - `GET /api/psc/dashboard/`
  - `GET /api/psc/inspections/`
  - `GET /api/psc/cars/`

Wireframe:

```text
--------------------------------------------------------------
| Header: logo | notifications | user menu                   |
--------------------------------------------------------------
| Sidebar | Dashboard Title                                  |
|         |--------------------------------------------------|
|         | [Inspections] [Open CARs] [Overdue] [Detentions]  |
|         |--------------------------------------------------|
|         | Trend Chart            | Top Deficiency Codes      |
|         |--------------------------------------------------|
|         | Repeat Deficiencies Table / Cards                  |
--------------------------------------------------------------
```

## 3. Inspection List

- Module: Inspection
- Route: `/inspections`
- Purpose: browse inspections with filtering and pagination
- Components:
  - `InspectionFilters`
  - `InspectionList`
  - floating create button
- API integrations:
  - `GET /api/psc/inspections/`
  - `GET /api/psc/inspections/export-excel/`

Wireframe:

```text
--------------------------------------------------------------
| Inspections  [Export Excel]                                |
|------------------------------------------------------------|
| Filters: Type | Status | Date | Search | Detention         |
|------------------------------------------------------------|
| [Inspection Card]                                          |
| [Inspection Card]                                          |
| [Inspection Card]                                          |
|                                                            |
|                                (+) New Inspection          |
--------------------------------------------------------------
```

## 4. Create Inspection

- Module: Inspection
- Route: `/inspections/new`
- Purpose: create a draft inspection and optionally upload a report
- Components:
  - `InspectionForm`
  - cancel confirmation dialog
- API integrations:
  - `POST /api/psc/inspections/create/`
  - `POST /api/psc/inspections/{id}/upload-report/`
  - master lookups

Wireframe:

```text
--------------------------------------------------------------
| New Inspection   [Back]                                    |
|------------------------------------------------------------|
| Inspection Details                                         |
|  Type  [PSC v]  Subtype [INITIAL v]  Date [dd/mm/yyyy]     |
|  Port  [.................]  Country [...............]      |
|  MOU   [TOKYO v]  Authority [..........]                   |
|------------------------------------------------------------|
| Report Upload                                              |
|  [ Choose File ]                                           |
|------------------------------------------------------------|
| Deficiencies                                               |
|  [ Add Deficiency ]                                        |
|------------------------------------------------------------|
| [Cancel]                               [Create Draft]      |
--------------------------------------------------------------
```

## 5. Inspection Detail

- Module: Inspection
- Route: `/inspections/:id`
- Purpose: display the complete inspection lifecycle and linked data
- Components:
  - `InspectionDetail`
  - `DeficiencyList`
  - activity history
  - audit log
  - workflow actions
  - evidence/report modals
- API integrations:
  - `GET /api/psc/inspections/{id}/`
  - `POST /api/psc/inspections/{id}/submit/`
  - `POST /api/psc/inspections/{id}/pic-review/`
  - `POST /api/psc/inspections/{id}/dpa-close/`
  - `POST /api/psc/inspections/{id}/upload-report/`

Wireframe:

```text
--------------------------------------------------------------
| Inspection Detail | status badge | actions menu            |
|------------------------------------------------------------|
| Inspection Summary                                        |
| Reports                                                   |
| Deficiencies                                              |
| Activity History                                          |
| Audit Log                                                 |
--------------------------------------------------------------
```

## 6. Edit Inspection

- Module: Inspection
- Route: `/inspections/:id/edit`
- Purpose: update draft or office-editable inspection data
- Components:
  - `InspectionForm`
  - evidence/report upload modal if needed
- API integrations:
  - `PUT /api/psc/inspections/{id}/update/`

Wireframe:

```text
--------------------------------------------------------------
| Edit Inspection                                            |
|------------------------------------------------------------|
| Same structure as create form, prefilled                   |
| [Save Draft] [Cancel]                                      |
--------------------------------------------------------------
```

## 7. Follow-up Screen

- Module: Inspection
- Route: `/inspections/:id/follow-up`
- Purpose: record same-inspection follow-up updates
- Components:
  - follow-up wizard form
  - deficiency selection/update list
  - optional report upload
- API integrations:
  - `POST /api/psc/inspections/{id}/follow-up/`

Wireframe:

```text
--------------------------------------------------------------
| Follow Up                                                 |
|------------------------------------------------------------|
| Deficiency Update Rows                                     |
|  [ Deficiency | Action Code | Notes ]                      |
|  [ Deficiency | Action Code | Notes ]                      |
|------------------------------------------------------------|
| Reinspection Date | Notes | Optional PDF report           |
|------------------------------------------------------------|
| [Cancel]                               [Submit Follow-up]  |
--------------------------------------------------------------
```

## 8. Deficiency Dashboard

- Module: Inspection
- Route: `/deficiencies`
- Purpose: master workflow dashboard for deficiency allocation and review
- Components:
  - `DeficiencyCard`
  - `DeficiencyDetailDialog`
  - status filters
- API integrations:
  - `GET /api/psc/deficiencies/`
  - `PUT /api/psc/deficiencies/{id}/action-code/`
  - `POST /api/psc/deficiencies/{id}/workflow/`
  - `POST /api/psc/deficiencies/{id}/allocate/`

Wireframe:

```text
--------------------------------------------------------------
| Deficiency Workflow                                        |
|------------------------------------------------------------|
| Filters: CAR Status v | Awaiting Review                    |
|------------------------------------------------------------|
| [Deficiency Card]                                          |
| [Deficiency Card]                                          |
| [Deficiency Card]                                          |
|------------------------------------------------------------|
| Detail Dialog opens on click                               |
--------------------------------------------------------------
```

## 9. CAR List

- Module: CAR
- Route: `/cars`
- Purpose: browse CARs, filter by status, and close physical verification when permitted
- Components:
  - `CARFilters`
  - `CARList`
  - `PVCloseModal`
- API integrations:
  - `GET /api/psc/cars/`
  - `GET /api/psc/cars/{id}/`
  - `POST /api/psc/physical-verifications/{id}/close/`

Wireframe:

```text
--------------------------------------------------------------
| CARs                                                      |
|------------------------------------------------------------|
| Filters: Status | Search | PV Due | Overdue               |
|------------------------------------------------------------|
| [CAR Card]                                                |
| [CAR Card]                                                |
| [CAR Card]                                                |
|------------------------------------------------------------|
| Quick close PV modal from list when allowed               |
--------------------------------------------------------------
```

## 10. CAR Detail

- Module: CAR
- Route: `/cars/:id`
- Purpose: detailed CAR workflow page
- Components:
  - `CARDetail`
  - `CARWorkflowActions`
  - evidence section
  - physical verification section
  - evidence upload modal
  - PIC accept / rework / DPA close modals
  - PV create / PV close modals
- API integrations:
  - `GET /api/psc/cars/{id}/`
  - `POST /api/psc/cars/{id}/workflow/`
  - `POST /api/psc/cars/{id}/evidence/`
  - `POST /api/psc/cars/{id}/actions/`
  - `POST /api/psc/cars/{id}/physical-verification/`
  - `GET /api/psc/cars/{id}/export-pdf/`

Wireframe:

```text
--------------------------------------------------------------
| CAR Detail | status | export | edit                        |
|------------------------------------------------------------|
| Deficiency Summary                                         |
| Root Cause + CLC                                           |
| Corrective Actions                                         |
| Evidence                                                   |
| Physical Verification                                      |
| Activity History / Audit Log                               |
--------------------------------------------------------------
```

## 11. CAR Edit

- Module: CAR
- Route: `/cars/:id/edit`
- Purpose: update root cause, CLC items, and CAR target date
- Components:
  - `CARForm`
  - `EvidenceUploadModal`
- API integrations:
  - `PUT /api/psc/cars/{id}/update/`
  - `POST /api/psc/cars/{id}/workflow/`

Wireframe:

```text
--------------------------------------------------------------
| Edit CAR                                                   |
|------------------------------------------------------------|
| Root Cause Summary                                         |
| CLC Selection                                              |
| Target Date                                                |
| Evidence Upload                                            |
| [Cancel]                               [Save Draft]       |
--------------------------------------------------------------
```

## 12. Notifications

- Module: Notifications
- Route: `/notifications`
- Purpose: list and mark user notifications as read
- Components:
  - `NotificationList`
  - `NotificationItem`
  - `NotificationBadge`
- API integrations:
  - `GET /api/psc/notifications/`
  - `POST /api/psc/notifications/mark-read/`
  - `POST /api/psc/notifications/mark-all-read/`

Wireframe:

```text
--------------------------------------------------------------
| Notifications [Mark All Read]                              |
|------------------------------------------------------------|
| Today                                                      |
|  [Notification Item]                                       |
| Yesterday                                                  |
|  [Notification Item]                                       |
| Earlier                                                    |
|  [Notification Item]                                       |
--------------------------------------------------------------
```

## 13. Sync Status

- Module: Sync
- Route: `/sync`
- Purpose: display offline status, pending changes, and conflicts
- Components:
  - `SyncStatus`
  - `StorageIndicator`
  - `PendingChanges`
  - `ConflictList`
  - `ConflictResolutionModal`
- API integrations:
  - `POST /api/psc/sync/pull/`
  - `POST /api/psc/sync/push/`
  - `GET /api/psc/sync/conflicts/`
  - `POST /api/psc/sync/resolve-conflict/`

Wireframe:

```text
--------------------------------------------------------------
| Sync Status                                                |
|------------------------------------------------------------|
| Connection status / last sync                               |
| Storage usage                                              |
| Pending changes                                            |
| Conflict list                                              |
| [Sync Now] [Clear Data]                                    |
--------------------------------------------------------------
```

## 14. Reports Workspace

- Module: Inspection / Reporting
- Route: `/reports`
- Purpose: DefIntel and OpenSource reporting workspace
- Components:
  - import panel
  - checklist preview/export controls
  - prediction controls
  - summary cards
- API integrations:
  - `POST /api/psc/reports/opensource/import/`
  - `POST /api/psc/reports/vessel-prep/preview/`
  - `POST /api/psc/reports/vessel-prep/export/`
  - `GET /api/psc/reports/defintel/predict-defcodes/`

Wireframe:

```text
--------------------------------------------------------------
| Reports / DefIntel Workspace                               |
|------------------------------------------------------------|
| OpenSource Import Panel                                    |
| Vessel Prep Checklist Preview / Export                     |
| DefCode Prediction Panel                                   |
| Dashboard summary cards                                    |
--------------------------------------------------------------
```

## 15. Settings

- Module: Settings
- Route: `/settings`
- Purpose: manage company logo used in report generation
- Components:
  - file input
  - logo preview
  - upload button
- API integrations:
  - `GET /api/psc/auth/company-logo/`
  - `POST /api/psc/auth/company-logo/`

Wireframe:

```text
--------------------------------------------------------------
| Settings                                                   |
|------------------------------------------------------------|
| Company Logo                                               |
| [Preview Box]   [Upload Logo / Replace Logo]               |
| Notes: PNG/JPG, max 2MB                                    |
--------------------------------------------------------------
```

## 16. Circular Module Shell

- Module: Circular
- Route: `/circular/*`
- Purpose: mount the legacy Circular UI within the modern app shell
- Components:
  - `LegacyBasicProvider`
  - legacy Circular routes
- API integrations:
  - `/api/circular/*`

Wireframe:

```text
--------------------------------------------------------------
| Modern Header / Sidebar                                    |
|------------------------------------------------------------|
| Legacy Circular content area                               |
|   - notifications                                           |
|   - drafts                                                  |
|   - approved library                                        |
|   - pdf viewer                                              |
--------------------------------------------------------------
```

## 17. ORB Module Shell

- Module: ORB
- Route: `/orb/*`
- Purpose: mount the legacy ORB UI or office-approved entries screen
- Components:
  - `LegacyBasicProvider`
  - legacy ORB routes
  - office-approved entries page
- API integrations:
  - `/api/orb/api/*`
  - `/api/orb/*`

Wireframe:

```text
--------------------------------------------------------------
| Modern Header / Sidebar                                    |
|------------------------------------------------------------|
| ORB module content                                          |
|  - vessel dashboard                                         |
|  - approved/rejected entries                                |
|  - operation form                                           |
|  - PDF archive                                              |
--------------------------------------------------------------
```

## 18. Key Modals

### 18.1 Inspection Cancel Confirm

- Appears on create/edit inspection forms
- Prevents accidental loss of draft input

### 18.2 Evidence Upload Modal

- Used in CAR detail and CAR edit flows
- Accepts file, evidence type, and description

### 18.3 PIC Accept / Rework / DPA Close Modals

- Used for explicit CAR workflow transitions
- Carry the required comment fields

### 18.4 PV Create / PV Close Modals

- Manage physical verification lifecycle

### 18.5 Conflict Resolution Modal

- Used on the sync screen for office/DPA users

### 18.6 Deficiency Detail Dialog

- Shows deficiency metadata and workflow actions

