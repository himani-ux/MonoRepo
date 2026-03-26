# Backend API Documentation

This document covers the live PSC API surface, the shared auth/utility endpoints, the inspection/CAR workflows, sync, reporting, and the legacy Circular/ORB integration routes.

## 1. Response Format Standard

The API generally uses one of these patterns:

### Success envelope

```json
{
  "data": {},
  "message": "Success"
}
```

### Error envelope

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Human readable error",
  "details": {}
}
```

Some list endpoints return pagination metadata:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 0,
    "total_pages": 0
  }
}
```

## 2. Authentication APIs

### 2.0 `GET /api/psc/health/`

- Module: Operations
- Access: public

Purpose:

- simple liveness probe for monitoring and deployment checks

Response:

```json
{
  "status": "healthy",
  "service": "psc-backend",
  "version": "1.0.0"
}
```

### 2.1 `POST /api/psc/auth/login/`

- Module: Authentication
- Access: public

Request:

```json
{
  "username": "KSM0001",
  "password": "secret"
}
```

Validation:

- `username` required
- `password` required

Response:

```json
{
  "data": {
    "access": "<jwt>",
    "refresh": "<jwt>",
    "user": {
      "id": "...",
      "user_type": "vessel",
      "role": "VESSEL_MASTER",
      "full_name": "..."
    }
  },
  "message": "Login successful"
}
```

Role behavior:

- vessel users authenticate through `Ship_UsersLogin` and `HRM501`
- office users authenticate through `users`

### 2.2 `POST /api/psc/auth/refresh/`

- Module: Authentication
- Access: public

Request:

```json
{
  "refresh": "<refresh-token>"
}
```

Validation:

- refresh token required
- token must be valid and unexpired

Response:

```json
{
  "data": {
    "access": "<new-access-token>",
    "refresh": "<new-refresh-token>"
  },
  "message": "Token refreshed successfully"
}
```

### 2.3 `POST /api/psc/auth/logout/`

- Module: Authentication
- Access: authenticated

Request:

```json
{
  "refresh": "<refresh-token>"
}
```

Behavior:

- best-effort refresh token blacklist
- frontend must always clear local auth state

Response:

```json
{
  "data": {},
  "message": "Logout successful"
}
```

### 2.4 `GET /api/psc/auth/me/`

- Module: Authentication
- Access: authenticated

Returns the current user claims as stored in the JWT.

Response fields include:

- user identity
- role
- vessel identity
- office profile IDs
- permission arrays
- legacy compatibility fields

### 2.5 `GET /api/psc/auth/crew/?vessel_id=<uuid>`

- Module: Authentication / Master lookup
- Access: authenticated
- Purpose: returns active onboard crew for a vessel

Validation:

- `vessel_id` query parameter is required
- must be a valid UUID

Response:

```json
{
  "data": [
    {
      "id": "...",
      "crew_id": "KSM0001",
      "first_name": "John",
      "surname": "Doe",
      "rank_name": "Master",
      "department_name": "Deck",
      "display_name": "Master - John Doe"
    }
  ],
  "message": "Success"
}
```

### 2.6 `GET|POST /api/psc/auth/company-logo/`

- Module: Settings / Reporting
- Access: authenticated

GET response:

```json
{
  "data": {
    "has_logo": true,
    "logo_url": "/media/company/logo.png"
  }
}
```

POST request:

```multipart/form-data
logo=<png-or-jpg-file>
```

Validation:

- office users only
- PNG/JPG/JPEG only
- max 2MB

## 3. Dashboard API

### `GET /api/psc/dashboard/?vessel_id=<uuid>`

- Module: Dashboard
- Access: authenticated

Purpose:

- returns aggregate KPI data for the dashboard screen

Key response groups:

- inspections by type
- inspections in last 12 months
- open and overdue CAR counts
- detention counts
- top deficiency codes
- pending deficiencies
- missing evidence count
- overdue actions count
- CAR status distribution
- monthly deficiency trend
- repeat deficiencies
- vessel list for office drill-down

Role behavior:

- vessel users see only their own vessel
- office users see assigned vessels
- office users can pass `vessel_id` for drill-down

## 4. Master Data APIs

### `GET /api/psc/masters/mou/`

- Returns MOU codes and names

### `GET /api/psc/masters/psc-action-codes/`

- Returns action codes used for deficiency action updates

### `GET /api/psc/masters/pic/`

- Returns PIC lookup data
- Optional department filter

### `GET /api/psc/masters/psc-def-categories/`

- Returns top-level deficiency categories

### `GET /api/psc/masters/psc-def-codes/`

- Returns PSC deficiency codes
- Supports search and category filters in the frontend wrapper

### `GET /api/psc/masters/clc-categories/`

- Returns CLC categories

### `GET /api/psc/masters/clc/`

- Returns CLC items

### `GET /api/psc/masters/clc/hierarchy/`

- Returns hierarchical CLC structure for tree/accordion UIs

## 5. Inspection APIs

### 5.1 `GET /api/psc/inspections/`

- Module: Inspection
- Access: authenticated

Purpose:

- paginated inspection list

Note:

- list-only route on the current URL map
- create uses `POST /api/psc/inspections/create/`

Query parameters:

- `page`
- `page_size`
- `vessel_id`
- `status`
- `inspection_type`
- `date_from`
- `date_to`
- `search` in frontend, filtered by list hook logic

Role behavior:

- vessel users see only their vessel
- vessel crew are further restricted to assigned deficiencies
- office users are filtered by vessel assignment unless global access applies

### 5.2 `POST /api/psc/inspections/create/`

- Module: Inspection
- Access: vessel master and office roles allowed by permission logic

Request fields:

- `vessel_id`
- `inspection_type`
- `psc_subtype`
- `inspection_date`
- `port_place`
- `country`
- `mou_id`
- `authority`
- `inspector_name`
- `is_detention`
- `def_reported`
- `client_id`

Validation:

- inspection date cannot be in the future
- port/place must be at least 2 characters
- PSC inspections require `psc_subtype` and `mou_id`
- non-PSC inspections must not carry `psc_subtype`
- `def_reported` must be `YES` or `NO`

### 5.3 `GET /api/psc/inspections/{id}/`

- Returns full inspection detail

Response includes:

- report list
- deficiency list
- activity history
- audit log for office/DPA users
- parent inspection info
- follow-up count

### 5.4 `PUT /api/psc/inspections/{id}/update/`

- Module: Inspection
- Access: object-level permission

Validation:

- same rules as create
- `def_reported=NO` is blocked if deficiencies already exist

### 5.5 `DELETE /api/psc/inspections/{id}/delete/`

- Soft-deletes draft inspections only

### 5.6 `POST /api/psc/inspections/{id}/submit/`

- Submits a draft inspection for review

Validation:

- inspection must be `DRAFT`
- at least one non-deleted report must exist
- every non-deleted deficiency must have a CAR

### 5.7 `POST /api/psc/inspections/{id}/pic-review/`

- PIC review action
- Request body: `comment`

Validation:

- comment minimum 10 characters
- inspection must be `SUBMITTED`

### 5.8 `POST /api/psc/inspections/{id}/dpa-close/`

- DPA close action
- Request body: `comment`

Validation:

- comment minimum 10 characters
- inspection must be `PIC_REVIEWED`

### 5.9 `POST /api/psc/inspections/{id}/upload-report/`

- Upload inspection report file
- multipart/form-data

Fields:

- `file`
- `description` optional

Validation:

- PDF/JPG/JPEG only
- max 3MB

### 5.10 `POST /api/psc/inspections/{inspection_id}/deficiencies/`

- Add a deficiency to an inspection
- Auto-creates CAR through signal

Request fields:

- `def_code_id`
- `description`
- `action_code_id`
- `assigned_crew_id`
- `target_date`
- `client_id`

Validation:

- deficiency code must exist
- action code, if present, must exist
- description minimum 10 characters
- assigned crew must be valid and onboard this vessel
- target date cannot be in the past

### 5.11 `POST /api/psc/inspections/{inspection_id}/deficiencies/bulk-submit/`

- Bulk submission of multiple approved deficiencies
- Used by the master workflow

### 5.12 `POST /api/psc/inspections/{inspection_id}/follow-up/`

- Same-inspection follow-up wizard
- Vessel master only

Request is multipart/form-data and may contain:

- `deficiency_updates` JSON string
- `reinspection_date`
- `notes`
- `report_file`
- `report_description`

Validation:

- every deficiency must belong to the inspection
- `reinspection_date` cannot be before the original inspection date
- `reinspection_date` cannot be in the future
- if `report_file` is present, description is required
- report file must be PDF and under 5MB

Legacy alias:

- `POST /api/psc/psc-follow-up/register/`

### 5.13 `GET /api/psc/inspections/export-excel/`

- Exports deficiency data as Excel
- honors the same vessel scoping and filters as inspection list

### 5.14 `GET /api/psc/inspections/{inspection_id}/cars/export-pdf/`

- Exports CAR PDFs for all CARs in an inspection
- returns a single PDF when there is one CAR
- returns a ZIP when there are multiple CARs

## 6. Deficiency APIs

### 6.1 `GET /api/psc/deficiencies/`

- Lists deficiencies with filters
- Vessel crew visibility is restricted to assigned items

### 6.2 `PUT /api/psc/deficiencies/{id}/action-code/`

- Updates action code with history tracking

Request:

```json
{
  "action_code_id": 10,
  "follow_up_inspection_id": "uuid",
  "change_reason": "Updated after verification"
}
```

Validation:

- action code must exist
- follow-up inspection, if present, must be a PSC follow-up inspection

### 6.3 `POST /api/psc/deficiencies/{id}/workflow/`

- Transitions vessel-side deficiency workflow state

Request:

```json
{
  "target_status": "APPROVED",
  "comment": "Reviewed and approved"
}
```

### 6.4 `POST /api/psc/deficiencies/{id}/allocate/`

- Assigns deficiency responsibility to a crew member

Request:

```json
{
  "assigned_crew_id": "KSM0001",
  "reviewer_crew_id": "uuid"
}
```

Validation:

- assigned crew must exist in `Ship_UsersLogin`

## 7. CAR APIs

### 7.1 `GET /api/psc/cars/`

- Paginated CAR list
- Supports status, vessel, overdue, and PV filters

### 7.2 `GET /api/psc/cars/{id}/`

- Returns full CAR detail

Response includes:

- deficiency summary
- root cause
- CLC mappings
- corrective actions
- evidence
- activity history
- audit log
- physical verification

### 7.3 `PUT /api/psc/cars/{id}/update/`

- Updates CAR root cause, target date, and CLC selections

### 7.4 `POST /api/psc/cars/{id}/workflow/`

- Executes named CAR workflow transitions

Request:

```json
{
  "action": "SUBMIT_TO_PIC",
  "comment": "Ready for review"
}
```

### 7.5 `GET /api/psc/cars/{id}/available-actions/`

- Returns the actions available to the current user for that CAR

### 7.6 Legacy workflow endpoints

- `POST /api/psc/cars/{id}/submit/`
- `POST /api/psc/cars/{id}/pic-accept/`
- `POST /api/psc/cars/{id}/rework/`
- `POST /api/psc/cars/{id}/dpa-close/`
- `POST /api/psc/cars/{id}/reopen/`

### 7.6.1 `GET /api/psc/cars/{id}/export-pdf/`

- Generates a CAR PDF for one CAR
- accepts optional `audience=internal|external`
- vessel roles can only export their own vessel's CAR

These are kept for backward compatibility and map to the unified workflow model.

### 7.7 `POST /api/psc/cars/{car_id}/evidence/`

- Upload evidence to a CAR
- multipart/form-data

Fields:

- `file`
- `evidence_type`
- `description`
- `client_id` optional

Validation:

- file max size is driven by backend limits
- file type must be PDF/JPG/JPEG
- description is required and must be at least 5 characters

### 7.8 `GET /api/psc/evidence/{id}/view/`

- Returns the evidence file for preview/download

### 7.9 `DELETE /api/psc/evidence/{id}/`

- Soft-deletes evidence

### 7.10 `POST /api/psc/cars/{car_id}/actions/`

- Creates a corrective action

Request fields:

- `action_type`
- `description`
- `owner_crew_id`
- `owner_user_id`
- `due_date`
- `client_id`

Validation:

- description minimum 10 characters
- due date cannot be in the past
- internal workflow text is blocked

### 7.11 `PUT /api/psc/actions/{id}/`

- Updates a corrective action

### 7.12 `POST /api/psc/actions/{id}/complete/`

- Marks a corrective action complete

Request:

```json
{
  "completion_remarks": "Completed on board"
}
```

### 7.13 `DELETE /api/psc/actions/{id}/delete/`

- Soft-deletes a corrective action

### 7.14 `POST /api/psc/cars/{car_id}/physical-verification/`

- Creates a physical verification record

### 7.15 `PUT /api/psc/physical-verifications/{id}/`

- Updates a physical verification record

### 7.16 `POST /api/psc/physical-verifications/{id}/close/`

- Closes a physical verification record

## 8. Notification APIs

### 8.1 `GET /api/psc/notifications/`

- Lists notifications for the authenticated recipient

Query parameters:

- `is_read`
- `page`
- `page_size`

Role behavior:

- vessel users read by `crew_id`
- office users read by `employee_id`

### 8.2 `POST /api/psc/notifications/mark-read/`

- Marks selected notifications as read

Request:

```json
{
  "notification_ids": ["uuid1", "uuid2"]
}
```

### 8.3 `POST /api/psc/notifications/mark-all-read/`

- Marks every notification belonging to the current user as read

## 9. Sync APIs

### 9.1 `POST /api/psc/sync/pull/`

- Returns server deltas for a vessel

Request:

```json
{
  "vessel_id": "uuid",
  "last_sync_token": "uuid",
  "last_server_version": 12345
}
```

Validation:

- vessel user only
- vessel ID must match the authenticated user scope

### 9.2 `POST /api/psc/sync/push/`

- Pushes client-side batched events to the server

Request shape:

```json
{
  "sync_id": "uuid",
  "vessel_id": "uuid",
  "checksum": "sha256",
  "events": [],
  "attachments": []
}
```

Validation:

- max 100 events
- unique event IDs
- checksum must match the serialized events payload or conform to the legacy allowed pattern
- vessel user only

### 9.3 `PUT|POST /api/psc/sync/upload/{token}/`

- Uploads attachment bytes for a tokenized sync attachment

Behavior:

- token is signed
- payload is raw request body
- attachment metadata must already exist as a CAR evidence record

### 9.4 `POST /api/psc/sync/resolve-conflict/`

- Resolves one sync conflict
- office/DPA only

Request:

```json
{
  "conflict_id": "uuid",
  "resolution": "KEEP_SERVER",
  "notes": "Accepted office version"
}
```

### 9.5 `GET /api/psc/sync/conflicts/`

- Lists unresolved conflicts
- vessel users see only their vessel

## 10. Reporting APIs

### 10.1 `POST /api/psc/reports/opensource/import/`

- Office-only OpenSource Excel import
- multipart/form-data with `file`

Validation:

- `.xlsx` only
- file cannot be empty
- import is office-restricted

### 10.2 `POST /api/psc/reports/vessel-prep/preview/`

- Builds a preview of the vessel preparation checklist

Request fields:

- `scope_mode`
- `vessel_id`
- `vessel_name`
- `inspector_name`
- `filters`
- `date_from`
- `date_to`
- `dedup`

### 10.3 `POST /api/psc/reports/vessel-prep/export/`

- Exports the vessel preparation checklist as a file

### 10.4 `GET /api/psc/reports/defintel/predict-defcodes/`

- Predicts likely deficiency codes for a port or MOU context

Query parameters:

- `context=PORT|MOU`
- `port`
- `mou`
- `window=LAST_24_MONTHS|ALL_TIME`
- `top_n`

Validation:

- `port` required when context is PORT
- `mou` required when context is MOU
- office users and qualified vessel ranks only

## 11. Legacy Circular APIs

The legacy Circular module is mounted under `/api/circular/` and is split into office and ship routes.

### 11.1 Office-side routes

Base prefix: `/api/circular/`

Examples from the current URL map:

- `/api/roles/`
- `/api/mapping-role-users/`
- `/api/users/`
- `/api/document-types/`
- `/api/departments/`
- `/api/priorities/`
- `/api/sub-categories/`
- `/api/second-sub-categories/`
- `/api/vessels/`
- `/api/master-applied-ranks/`
- `/api/ranks/`
- `/api/notifications/`
- `/api/submitted/`
- `/api/draft/...`
- `/api/approved-notifications/`
- `/api/user-notifications/`
- `/api/crews-by-department/`
- `/api/crews-by-department-and-vessel/`

### 11.2 Ship-side routes

Base prefix: `/api/circular/`

Examples from the current URL map:

- `/api/ship/notifications/`
- `/api/crew/notifications/`
- `/api/msc/pdf-url/`
- `/api/msc/read-ack/`
- `/api/msc/remind-crew/`
- `/api/crew/list/`
- `/api/crew/status/`
- `/api/reports/download-pdf/`

These are legacy routes retained for the integrated Circular experience and are consumed by the legacy frontend shell.

## 12. Legacy ORB APIs

The legacy ORB module is mounted under `/api/orb/` and `/api/orb/api/` with additional helper routes.

Primary route families:

- `/api/vessels/`
- `/api/tanks/`
- `/api/codes/`
- `/api/operations/`
- `/api/operations/{id}/approve/`
- `/api/operations/{id}/reject/`
- `/api/operations/{pk}/soft_delete/`
- `/api/non-deleted-entries/`
- `/api/deleted-entries/`
- `/api/rejected-entries/`
- `/api/approved-entries/`
- `/api/update-print-status/`
- `/api/save-pdf-metadata/`
- `/api/list-pdfs/`
- `/api/download-pdf/{pdf_id}/`
- `/api/get-current-user-vessel/`
- `/api/latest-entry-date/`

These routes support the legacy ORB workflow and are surfaced in the frontend through the ORB module shell.
