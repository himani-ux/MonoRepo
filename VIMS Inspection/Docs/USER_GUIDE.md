# VIMS Inspection Module - User Guide

## Overview

The VIMS Inspection Module manages maritime vessel inspections (PSC, RightShip, Audit) from initial recording through deficiency tracking, corrective actions, and final closure. It works offline on vessels and syncs when connected.

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
| **Office (PIC/SSQE/Supt)** | Review, accept, edit-assist, request rework |
| **DPA** | Final closure authority for inspections and CARs |

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
- Filter by status: Draft, Submitted, PIC Accepted, DPA Closed, Rework Requested
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
3. Status changes to SUBMITTED

### PIC Accept (Office)

1. Open a SUBMITTED CAR
2. Review the root cause analysis, corrective actions, and evidence
3. Click **Accept** and add a comment (minimum 10 characters)
4. Status changes to PIC_ACCEPTED

### Request Rework (Office)

1. If a CAR needs corrections, click **Request Rework**
2. Enter a reason (minimum 20 characters)
3. Status returns to DRAFT for the vessel to revise

### DPA Close

1. Open a PIC_ACCEPTED CAR
2. Click **DPA Close** and add a comment (minimum 10 characters)
3. Optionally check "Schedule Physical Verification"
4. Status changes to DPA_CLOSED

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

## 6. Exports

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
DRAFT --> SUBMITTED --> PIC_ACCEPTED --> DPA_CLOSED
  ^                        |
  |    REWORK_REQUESTED <--+
  +------------------------+
```

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
| Accept CAR | | | X | |
| Request Rework | | | X | X |
| Close CAR | | | | X |
| Resolve Conflicts | | | X | X |
