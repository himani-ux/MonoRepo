# VIMS Inspection Module - User Guide

## Overview

The VIMS Inspection Module manages maritime vessel inspections (PSC, RightShip, Audit) from initial recording through deficiency tracking, corrective actions, and final closure. It works offline on vessels and syncs when connected.

---

## Later Updates

The items below were added or changed later on after the original guide baseline:

- dashboard landing page and separate deficiency workflow page were added
- reports now include DefIntel/OpenSource tools, not only exports
- settings now includes company logo management for PDF reports
- office reviewer mapping can be vessel-scoped or global depending on the external mapping tables
- CAR workflow now uses the unified operational statuses shown in the status section at the end of this guide
- Audit plan and registration forms show vessel dropdowns; users select the vessel name/code and the system saves the correct vessel ID behind the scenes
- Audit plan Standards are selected from fixed options, so users no longer type comma-separated standard codes
- Register Audit shows a Selected Audit Plan picker. Choose the exact plan by `PLAN-XXXXXXXX`, target vessel/department, standards, status, audit window, and planned lead auditor before saving the audit.
- After a selected audit plan is registered, that plan becomes `IN_PROGRESS` and cannot be selected again for another audit registration.
- Qualified Auditors maintenance uses dropdowns for Employee/User ID and Qualifying Body. Qualifying Body choices come from active master rows in `aud_master_qual_body`, and the screen does not ask users to manually enter attachment UUIDs.

---

## 1. Login

1. Open the application URL
2. Enter your username and password
3. Click **Login**

Your role determines what you can see and do:

| Role | Access |
|------|--------|
| **Vessel Master** | Create inspections, submit CARs, register follow-ups |
| **Crew** | View assigned actions, upload evidence |
| **Office (PIC/SSQE/Supt)** | Review, start PIC review, submit to DPA, edit-assist, request rework |
| **DPA** | Final closure, rework, reopen, and global reviewer access when mapped |

---

## 1A. Dashboard and Navigation

- Users with dashboard permission land on **Dashboard** after login; others land on **CARs**
- **Dashboard** shows KPI cards, vessel drill-down, detention counts, CAR status charts, and top deficiency codes
- **Deficiencies** is a separate workflow page for allocation and review actions
- **Reports** is a working screen for OpenSource import, checklist preview/export, and prediction
- **Settings** now includes company logo upload/status for PDF reports

Reports access:

- Office users can access the reports workspace
- Vessel users in Master, CO, CE, and 2/E categories can access reports
- OpenSource import is office-only

---

## 2. Inspections

### View Inspection List

- Navigate to **Inspections** from the bottom nav (mobile) or sidebar (desktop)
- Filter by inspection type (PSC, RS, Audit, Internal) or status
- Search by port, vessel, or reference number
- Detention inspections are highlighted with a red border

### Create an Inspection

1. Tap the **+** button (bottom-right FAB)
2. Fill in required fields:
   - **Inspection Type** (PSC, RS, Audit, Internal)
   - **Inspection Date** (cannot be in the future)
   - **Port/Place**
3. For PSC inspections, also select:
   - **PSC Subtype** (Initial, Expanded, CIC, Follow-up)
   - **MOU** (Memorandum of Understanding region)
4. Optionally add inspector name, authority, report reference
5. Upload the inspection report (PDF, JPG, or JPEG, max 3MB)
6. Click **Save** to create in DRAFT status

### Register an Internal Audit

Office users register internal audits from **Register Audit**.

1. Select the exact audit plan first.
2. Check the plan reference, target, standards, status, and audit window shown on screen.
3. If two plans are for the same vessel, use the plan reference and window to choose the correct one.
4. Complete the common header, team, attendees, dates, scope, and plan blocks. The Lead Auditor fields are filled from the selected audit plan and cannot be edited during planned audit registration.
5. Click **Register Audit**.

When registerable audit plans exist, the screen requires a selected plan before saving.
The server also checks the plan status and previous usage, so a stale browser session cannot reuse or submit the wrong plan.

### Add Deficiencies

1. Open an inspection detail
2. Click **Add Deficiency**
3. Select a **Deficiency Code** (DefCode) - this is mandatory and always visible
4. Enter deficiency description (10-4000 characters)
5. Optionally set a target date and action code
6. Click **Save**

A **Corrective Action Report (CAR)** is automatically created for each deficiency.

### Submit an Inspection

1. Open a DRAFT inspection
2. Ensure an inspection report is attached
3. Click **Submit**
4. Status changes to SUBMITTED

### Review (Office/PIC)

1. Open a SUBMITTED inspection
2. Review the details and deficiencies
3. Click **Mark Reviewed**
4. Status changes to PIC_REVIEWED

### Close (DPA)

1. Open a PIC_REVIEWED inspection
2. Click **DPA Close**
3. Status changes to DPA_CLOSED

### Register Follow-up (PSC Only)

1. Open a PSC inspection
2. Click **Register Follow-up**
3. Enter follow-up date, port, and authority
4. Select deficiencies to include
5. Set action codes for each (default: 10 = Rectified)
6. Click **Submit**

---

## 3. Corrective Action Reports (CARs)

### View CAR List

- Navigate to **CARs** from the bottom nav or sidebar
- Filter by status: Allotted, In Progress, Pending CE Review, Pending Master Review, Submitted to PIC, PIC Review, Submitted to DPA, Closed
- Overdue CARs are highlighted with a red border
- CARs missing evidence show a warning indicator

### Edit a CAR

1. Open a CAR detail and click **Edit**
2. **Root Cause Section:**
   - Select one or more CLC (Classification of Loss Causation) codes
   - Write a root cause summary (minimum 50 characters for submission)
3. **Corrective Actions:**
   - Add Immediate and/or Long-term actions
   - Set due dates and assign owners
   - Mark actions as complete when done
4. **Target Dates:**
   - Set the overall target completion date
5. Click **Save**

### Upload Evidence

1. Open a CAR detail or edit page
2. Click **Upload Evidence** in the evidence section
3. Select evidence type: **BEFORE** or **AFTER**
4. Choose a file (PDF, JPG, JPEG - max 3MB)
5. Add an optional description
6. Click **Upload**

Submission requires at least 1 BEFORE evidence and 1 AFTER evidence.

### Submit a CAR

1. Ensure all requirements are met:
   - Root cause summary (50+ characters)
   - At least 1 CLC code or custom cause
   - At least 1 BEFORE evidence
   - At least 1 AFTER evidence
2. Click **Submit**
3. Status changes to **SUBMITTED_TO_PIC**

### PIC Review (Office)

1. Open a **SUBMITTED_TO_PIC** CAR
2. Review the root cause analysis, corrective actions, and evidence
3. Click **Start Review** and add the required comment
4. When review is complete, click **Submit to DPA**
5. Status changes to **SUBMITTED_TO_DPA**

### Request Rework (Office)

1. If a CAR needs corrections, click **Request Rework**
2. Enter a reason (minimum 20 characters)
3. Status moves back into the vessel-side rework path for revision

### DPA Close

1. Open a **SUBMITTED_TO_DPA** CAR
2. Click **DPA Close** and add a comment (minimum 10 characters)
3. Optionally check "Schedule Physical Verification"
4. Status changes to **CLOSED**

### Physical Verification

After DPA closure, a physical verification visit can be scheduled:

1. In the CAR detail, the PV section appears
2. Click **Create PV** to schedule a visit
3. Enter visit date, port, and verifier details
4. After the on-board visit, click **Close PV** with findings

---

## 4. Notifications

- The **bell icon** in the header shows unread notification count
- Navigate to **Notifications** to see all notifications
- Notifications are grouped by date (Today, Yesterday, Earlier)
- Click a notification to navigate to the related inspection or CAR
- Click **Mark All Read** to clear unread indicators

Notification types include:
- CAR created, submitted, accepted, rework requested, closed
- Corrective action overdue warnings
- PSC follow-up recorded
- Sync conflicts detected/resolved
- Physical verification created

---

## 5. Offline Mode and Sync

The application works offline on vessels with limited connectivity.

### When Offline

- A yellow **"Offline - Showing cached data"** banner appears at the top
- You can still view cached inspections and CARs
- Changes you make are queued for sync
- The sync page shows pending changes count

### Syncing

1. Navigate to **Sync** from the bottom nav
2. The status indicator shows Online/Offline
3. Click **Sync Now** to manually trigger sync
4. View pending changes and any failed uploads
5. Storage usage is shown (150MB limit)

### Conflict Resolution (Office/DPA Only)

When the same record is modified on vessel and server:

1. A conflict notification appears
2. Office/DPA users can open the conflict resolution modal
3. Compare vessel vs. server values side-by-side
4. Choose a resolution:
   - **Keep Server Version** - discard vessel changes
   - **Keep Vessel Version** - override server with vessel data
   - **Reopen for Merge** - send back to vessel for manual reconciliation
5. Click **Apply Resolution**

---

## 6. Reports and Settings

### Reports Workspace

1. Open **Reports** from the sidebar
2. Use the page for:
   - OpenSource monthly Excel import
   - vessel preparation checklist preview
   - vessel preparation checklist export
   - deficiency code prediction by port or MOU
3. If you are a vessel user with report access, you can use the report tools but not the OpenSource import
4. If OpenSource data has not been imported yet, combined checklist features will show the missing-data state

### Settings - Company Logo

1. Open **Settings**
2. Office users can upload or replace the company logo used in PDF reports
3. Accepted formats are PNG and JPG, up to 2MB
4. Vessel users can see the current logo status but cannot upload

---

## 7. Exports

### CAR PDF Export

1. Open a CAR detail page
2. Click the dropdown menu (three dots)
3. Select **Export PDF**
4. The PDF downloads with full CAR details

### Deficiency Excel Export

1. Go to the Inspection list page
2. Click **Export Excel** in the header
3. An Excel file downloads with all deficiency data

---

## Status Flow Reference

### Inspection States

```
DRAFT --> SUBMITTED --> PIC_REVIEWED --> DPA_CLOSED
```

### CAR States

```
ALLOTTED --> IN_PROGRESS --> PENDING_CE_REVIEW --> PENDING_MASTER_REVIEW
PENDING_MASTER_REVIEW --> SUBMITTED_TO_PIC --> PIC_REVIEW --> SUBMITTED_TO_DPA --> CLOSED
```

Common rework paths:

- `PENDING_CE_REVIEW -> IN_PROGRESS`
- `PENDING_MASTER_REVIEW -> IN_PROGRESS`
- `SUBMITTED_TO_PIC -> PENDING_MASTER_REVIEW`
- `PIC_REVIEW -> PENDING_MASTER_REVIEW`
- `SUBMITTED_TO_DPA -> PENDING_MASTER_REVIEW`
- `CLOSED -> PENDING_MASTER_REVIEW` (reopen)

### Who Can Do What

| Action | Vessel Master | Crew | Office (PIC) | DPA |
|--------|:---:|:---:|:---:|:---:|
| Create Inspection | X | | | |
| Submit Inspection | X | | | |
| Review Inspection | | | X | |
| Close Inspection | | | | X |
| Edit CAR (Draft) | X | | X | |
| Upload Evidence | X | X | X | |
| Submit CAR | X | | | |
| Start PIC Review / Submit to DPA | | | X | |
| Request Rework | | | X | X |
| Close CAR | | | | X |
| Reopen Closed CAR | | | | X |
| Resolve Conflicts | | | X | X |
