# Inspection Module

## 1. Scope

The inspection module is the core PSC workflow engine. It owns the business lifecycle that starts with inspection recording and ends with DPA close-out, while also creating the deficiency and CAR chain that powers the rest of the system.

## 2. Features

- inspection create, list, detail, edit, delete
- inspection report upload
- deficiency creation
- automatic CAR creation when a deficiency is added
- inspection submit / PIC review / DPA close
- same-inspection follow-up wizard
- dashboard metrics
- Excel export
- bulk CAR PDF export

## 3. Workflow

### 3.1 Inspection Lifecycle

1. Create draft inspection.
2. Upload report if required.
3. Add deficiencies.
4. Submit for review.
5. PIC reviews and comments.
6. DPA closes after review.

### 3.2 Deficiency Lifecycle

1. Add deficiency to an inspection.
2. Assign owner/reviewer where required.
3. Update action code during follow-up or workflow transitions.
4. Use follow-up wizard to record same-inspection reinspection updates.
5. Deficiency may become cleared when action code reaches the rectified code.

### 3.3 CAR Linkage

Every deficiency creates a linked CAR. That 1:1 relationship is a core design rule and is relied on by the CAR module, reports, and dashboard analytics.

## 4. Backend APIs Used

- `GET /api/psc/inspections/`
- `POST /api/psc/inspections/create/`
- `GET /api/psc/inspections/{id}/`
- `PUT /api/psc/inspections/{id}/update/`
- `DELETE /api/psc/inspections/{id}/delete/`
- `POST /api/psc/inspections/{id}/submit/`
- `POST /api/psc/inspections/{id}/pic-review/`
- `POST /api/psc/inspections/{id}/dpa-close/`
- `POST /api/psc/inspections/{id}/upload-report/`
- `POST /api/psc/inspections/{inspection_id}/deficiencies/`
- `POST /api/psc/inspections/{inspection_id}/deficiencies/bulk-submit/`
- `POST /api/psc/inspections/{inspection_id}/follow-up/`
- `GET /api/psc/inspections/export-excel/`
- `GET /api/psc/inspections/{inspection_id}/cars/export-pdf/`
- master data lookups

## 5. UI Flow

### 5.1 List Page

- filter by status, type, date, detention, and text search
- inspect status badges
- open detail page
- create new draft

### 5.2 Create / Edit Form

- show PSC subtype and MOU only for PSC inspections
- validate future dates and required fields
- upload report before submission

### 5.3 Detail View

- report attachments
- deficiency list
- activity history
- office-only audit trail
- workflow buttons based on role and status

### 5.4 Follow-Up Wizard

- same-inspection update flow
- batch action code update
- optional follow-up PDF upload
- reinspection date required

## 6. Role Behavior

- vessel master can create PSC/RS/AUDIT drafts and submit follow-ups
- vessel crew can view only their assigned scope
- office users can edit and review within assigned vessel scope or global access
- DPA has the final inspection close action

## 7. Error Handling

Common errors to surface in the UI:

- invalid report file type
- future inspection date
- missing MOU on PSC inspection
- no report attached before submit
- deficiencies missing CARs before submit
- permission denied on vessel scope mismatch

