# PRD.md — Product Requirements Document
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.1 | **Date:** 2026-02-05 | **Status:** DRAFT — PENDING APPROVAL

---

## 1. Product Overview

### 1.1 Purpose
A comprehensive inspection management system for maritime vessels that handles Port State Control (PSC), RightShip (RS), and Audit inspections. The system manages the complete lifecycle from inspection recording through deficiency tracking, Corrective Action Reports (CAR), and final DPA closure.

### 1.2 Target Users
| Role | Description | Primary Actions |
|------|-------------|-----------------|
| Vessel Master | Ship's Master or designated vessel admin | Create inspections, submit CARs, register follow-ups |
| Crew (Action Owner) | Crew member assigned to corrective actions | View assigned actions, upload evidence |
| Office (PIC/SSQE/Supt) | Shore-based inspectors and superintendents | Review, accept, edit-assist, request rework |
| DPA | Designated Person Ashore per ISM Code | Final closure authority |
| Physical Verifier | Person conducting on-board verification | Record physical verification visits |

### 1.3 Success Criteria
- 100% of deficiencies have auto-generated CARs (1:1 enforcement)
- Zero inspections submitted without report attachment
- All CARs require BEFORE + AFTER evidence before submission
- Offline capability for vessel operations with conflict resolution
- Complete audit trail for regulatory compliance

---

## 2. Feature Inventory

### 2.1 Inspection Management

#### FEAT-INS-001: Create Inspection
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to create a new inspection record so that I can document PSC/RS/Audit findings.
**Acceptance Criteria:**
- [ ] User can select inspection type: PSC, RS, AUDIT, INTERNAL
- [ ] PSC inspections require subtype: INITIAL, EXPANDED, CIC, FOLLOW_UP
- [ ] Inspection date cannot be in the future
- [ ] Port/Place is mandatory
- [ ] MOU selection available for PSC inspections
- [ ] System creates inspection in DRAFT status
- [ ] Works offline with sync queue

#### FEAT-INS-002: Upload Inspection Report
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to upload the official inspection report so that it's attached to the record.
**Acceptance Criteria:**
- [ ] Accepted formats: PDF, JPG, JPEG
- [ ] Maximum file size: 3MB
- [ ] Description field mandatory
- [ ] Report required before inspection submission
- [ ] Uploads queue when offline

#### FEAT-INS-003: Add Deficiency to Inspection
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to add deficiencies found during inspection so that each can be tracked and resolved.
**Acceptance Criteria:**
- [ ] DefCode (deficiency code) is MANDATORY — visible on all screens
- [ ] DefCode selected from masters.psc_def_codes lookup
- [ ] Description field required
- [ ] Action Code selected from masters.psc_action_codes
- [ ] Target date can be set
- [ ] Adding deficiency auto-creates CAR (FEAT-CAR-001)

#### FEAT-INS-004: Submit Inspection
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to submit the inspection for office review once complete.
**Acceptance Criteria:**
- [ ] Inspection report must be attached (PDF, JPG, or JPEG)
- [ ] All deficiencies must have associated CARs
- [ ] Status changes: DRAFT → SUBMITTED
- [ ] Creates activity event for history
- [ ] Office can submit on vessel's behalf (override, no comment required)

#### FEAT-INS-005: PIC Review Inspection
**Priority:** P0 (Critical)
**User Story:** As an Office PIC, I want to review and acknowledge the inspection submission.
**Acceptance Criteria:**
- [ ] Only Office (PIC/SSQE/Supt) can perform
- [ ] PIC comment is MANDATORY
- [ ] Status changes: SUBMITTED → PIC_REVIEWED
- [ ] Creates activity event

#### FEAT-INS-006: DPA Close Inspection
**Priority:** P0 (Critical)
**User Story:** As DPA, I want to close the inspection once all CARs are satisfactorily resolved.
**Acceptance Criteria:**
- [ ] Only DPA can perform
- [ ] DPA comment is MANDATORY
- [ ] Status changes: PIC_REVIEWED → DPA_CLOSED
- [ ] Creates activity event
- [ ] Sends notification to Vessel Master

#### FEAT-INS-007: Edit Inspection (Draft)
**Priority:** P1 (High)
**User Story:** As a Vessel Master, I want to edit inspection details before submission.
**Acceptance Criteria:**
- [ ] Only available when status = DRAFT
- [ ] Vessel Master has full edit access
- [ ] Office can edit-assist (logged separately)

#### FEAT-INS-008: Edit Inspection (Post-Submit)
**Priority:** P1 (High)
**User Story:** As Office/DPA, I want to amend inspection details after submission when corrections are needed.
**Acceptance Criteria:**
- [ ] Available for SUBMITTED, PIC_REVIEWED statuses
- [ ] Only Office and DPA can edit
- [ ] Increments revision_no
- [ ] Full audit log of changes

#### FEAT-INS-009: Delete Draft Inspection
**Priority:** P2 (Medium)
**User Story:** As a Vessel Master, I want to delete a draft inspection that was created in error.
**Acceptance Criteria:**
- [ ] Only available when status = DRAFT
- [ ] Only Vessel Master can delete
- [ ] Soft delete (is_deleted = 1)
- [ ] Associated deficiencies and CARs also soft deleted

#### FEAT-INS-010: View Inspection List
**Priority:** P0 (Critical)
**User Story:** As a user, I want to see all inspections for my vessel(s) with filtering options.
**Acceptance Criteria:**
- [ ] Vessel users see only their vessel's inspections
- [ ] Office users can filter by vessel
- [ ] Filter by: status, inspection_type, date range
- [ ] Pagination (default 20, max 100)
- [ ] Shows deficiency count and open count
- [ ] Detention inspections highlighted

#### FEAT-INS-011: View Inspection Detail
**Priority:** P0 (Critical)
**User Story:** As a user, I want to see complete inspection details including all deficiencies and CARs.
**Acceptance Criteria:**
- [ ] Shows all inspection fields
- [ ] Lists all deficiencies with DefCode prominently displayed
- [ ] Shows CAR status for each deficiency
- [ ] Shows activity history
- [ ] Office/DPA can see full audit log

---

### 2.2 Deficiency Management

#### FEAT-DEF-001: Update Action Code
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to update a deficiency's action code when PSC follow-up occurs.
**Acceptance Criteria:**
- [ ] Only Vessel Master can update
- [ ] Action code selected from masters.psc_action_codes
- [ ] Code 30 can transition to any code including 10
- [ ] Creates history record in deficiency_actioncode_history
- [ ] Linked to follow-up inspection if applicable

#### FEAT-DEF-002: Register PSC Follow-up
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to record a PSC follow-up inspection that clears deficiencies.
**Acceptance Criteria:**
- [ ] Creates new inspection with type=PSC, subtype=FOLLOW_UP
- [ ] Links to original inspection via parent_inspection_id
- [ ] Records follow-up date, port, authority
- [ ] Allows batch update of deficiency action codes
- [ ] Typically sets cleared deficiencies to action_code=10
- [ ] Creates psc_follow_up_events record
- [ ] Sends notification to Office + Vessel

#### FEAT-DEF-003: Mark Deficiency Cleared
**Priority:** P1 (High)
**User Story:** As a system, I want to mark deficiencies as cleared when action code indicates resolution.
**Acceptance Criteria:**
- [ ] Automatically set is_cleared=1 when action_code=10
- [ ] Record cleared_date and cleared_by_follow_up_id
- [ ] Update deficiency status in lists and reports

---

### 2.3 CAR (Corrective Action Report) Management

#### FEAT-CAR-001: Auto-Create CAR from Deficiency
**Priority:** P0 (Critical)
**User Story:** As a system, I want to automatically create a CAR when a deficiency is added so that 1:1 relationship is enforced.
**Acceptance Criteria:**
- [ ] Triggered automatically on deficiency INSERT
- [ ] CAR number format: SOURCE-YYYY-NNN (e.g., PSC-2026-001)
- [ ] CAR created in DRAFT status
- [ ] Target date defaults to deficiency target or +7 days
- [ ] No manual CAR creation allowed

#### FEAT-CAR-002: Edit CAR (Draft)
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to complete the CAR form with root cause analysis and corrective actions.
**Acceptance Criteria:**
- [ ] Root cause summary field (min 50 chars for submission)
- [ ] CLC code selection from masters.clc_items (multi-select)
- [ ] Custom cause text allowed if not in CLC
- [ ] Immediate corrective actions (at least 1 required)
- [ ] Long-term preventive actions (at least 1 required)
- [ ] Each action has: description, owner, due date
- [ ] Office can edit-assist (no notification to vessel)

#### FEAT-CAR-003: Upload CAR Evidence
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master or Crew, I want to upload evidence photos/documents for the CAR.
**Acceptance Criteria:**
- [ ] Evidence types: BEFORE, AFTER, EVIDENCE, OTHER
- [ ] File formats: PDF, JPG, JPEG only
- [ ] Maximum file size: 3MB per file
- [ ] Description is MANDATORY
- [ ] At least 1 BEFORE evidence required for submission
- [ ] At least 1 AFTER evidence required for submission
- [ ] Crew can upload for their assigned actions only
- [ ] Works offline with upload queue

#### FEAT-CAR-004: Submit CAR
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to submit the CAR for office review once complete.
**Acceptance Criteria:**
- [ ] Validation: root_cause_summary min 50 chars
- [ ] Validation: at least 1 CLC code or custom cause
- [ ] Validation: at least 1 immediate action with owner and due date
- [ ] Validation: at least 1 long-term action with owner and due date
- [ ] Validation: at least 1 BEFORE evidence
- [ ] Validation: at least 1 AFTER evidence
- [ ] Status changes: DRAFT → SUBMITTED
- [ ] Office can submit on behalf (override, no comment required)
- [ ] Creates activity event
- [ ] Sends notification to Office PIC/SSQE

#### FEAT-CAR-005: PIC Accept CAR
**Priority:** P0 (Critical)
**User Story:** As an Office PIC, I want to accept a submitted CAR after review.
**Acceptance Criteria:**
- [ ] Only Office (PIC/SSQE/Supt) can perform
- [ ] PIC comment is MANDATORY
- [ ] Status changes: SUBMITTED → PIC_ACCEPTED
- [ ] Creates activity event
- [ ] Sends notification to Vessel Master

#### FEAT-CAR-006: Request CAR Rework
**Priority:** P0 (Critical)
**User Story:** As an Office PIC or DPA, I want to request rework when the CAR is insufficient.
**Acceptance Criteria:**
- [ ] Office can request from SUBMITTED status
- [ ] DPA can request from SUBMITTED or PIC_ACCEPTED status
- [ ] Rework reason is MANDATORY (min 20 chars)
- [ ] Status changes: → REWORK_REQUESTED → auto to DRAFT
- [ ] Vessel can edit again after rework requested
- [ ] Creates activity event
- [ ] Sends notification to Vessel Master + Action Owners

#### FEAT-CAR-007: DPA Close CAR
**Priority:** P0 (Critical)
**User Story:** As DPA, I want to close a CAR once satisfactorily completed.
**Acceptance Criteria:**
- [ ] Only DPA can perform
- [ ] DPA comment is MANDATORY
- [ ] Status changes: PIC_ACCEPTED → DPA_CLOSED
- [ ] Creates activity event
- [ ] Sends notification to Vessel Master
- [ ] CAR closure is independent of physical verification

#### FEAT-CAR-008: Reopen Closed CAR
**Priority:** P2 (Medium)
**User Story:** As DPA, I want to reopen a closed CAR if issues are discovered later.
**Acceptance Criteria:**
- [ ] Only DPA can perform
- [ ] Reopen reason is MANDATORY
- [ ] Status changes: DPA_CLOSED → REWORK_REQUESTED
- [ ] Creates audit log entry

#### FEAT-CAR-009: View CAR List
**Priority:** P0 (Critical)
**User Story:** As a user, I want to see all CARs with filtering and status tracking.
**Acceptance Criteria:**
- [ ] Filter by: vessel, status, source, date range, overdue
- [ ] Shows: CAR number, DefCode, vessel, target date, status
- [ ] Overdue CARs highlighted in red
- [ ] Pagination support

#### FEAT-CAR-010: View CAR Detail
**Priority:** P0 (Critical)
**User Story:** As a user, I want to see complete CAR details including all evidence and history.
**Acceptance Criteria:**
- [ ] Shows deficiency details with DefCode
- [ ] Shows root cause analysis and CLC codes
- [ ] Lists all corrective actions with status
- [ ] Shows all evidence attachments with previews
- [ ] Shows activity history (all users)
- [ ] Shows audit log (Office/DPA only)

#### FEAT-CAR-011: Add Corrective Action
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to add corrective actions to a CAR.
**Acceptance Criteria:**
- [ ] Action type: IMMEDIATE or LONGTERM
- [ ] Description required
- [ ] Assigned owner (user or role)
- [ ] Due date required
- [ ] Multiple actions allowed per CAR

#### FEAT-CAR-012: Complete Corrective Action
**Priority:** P1 (High)
**User Story:** As an Action Owner, I want to mark my assigned action as complete.
**Acceptance Criteria:**
- [ ] Only assigned owner can complete (or Vessel Master)
- [ ] Completion remarks optional
- [ ] Sets is_completed=1 and completed_at timestamp
- [ ] Creates activity event

---

### 2.4 Physical Verification

#### FEAT-PV-001: Create Physical Verification
**Priority:** P1 (High)
**User Story:** As Office/DPA/Verifier, I want to schedule a physical verification visit for a closed CAR.
**Acceptance Criteria:**
- [ ] Can only be created for DPA_CLOSED CARs
- [ ] Created in OPEN status
- [ ] Visit date and port optional at creation
- [ ] Verifier assignment optional at creation
- [ ] Sends notification to Vessel Master

#### FEAT-PV-002: Close Physical Verification
**Priority:** P1 (High)
**User Story:** As a Verifier, I want to record the verification visit results.
**Acceptance Criteria:**
- [ ] Visit date is MANDATORY to close
- [ ] Comments are MANDATORY to close
- [ ] Status changes: OPEN → CLOSED
- [ ] No evidence upload for physical verification
- [ ] Separate from CAR closure (CAR already closed)

---

### 2.5 Authentication & Authorization

#### FEAT-AUTH-001: User Authentication
**Priority:** P0 (Critical)
**User Story:** As any user, I want to log in securely so the system knows my identity and role.
**Acceptance Criteria:**
- [ ] JWT authentication with access + refresh tokens
- [ ] Login via existing user tables (core.office_users_v, core.vessel_users_v)
- [ ] Token refresh without re-login
- [ ] Logout invalidates refresh token
- [ ] Protected endpoints reject unauthenticated requests

#### FEAT-AUTH-002: Role-Based Access Control
**Priority:** P0 (Critical)
**User Story:** As a system, I want to enforce permissions so each role can only perform allowed actions.
**Acceptance Criteria:**
- [ ] RBAC middleware enforces permission matrix per BACKEND_STRUCTURE.md §11.1
- [ ] Vessel roles see own vessel data only
- [ ] Office roles see vessels assigned via master_RoleByVessel
- [ ] DPA role sees all vessels
- [ ] Unauthorized actions return 403 with clear message

---

### 2.6 Offline & Sync

#### FEAT-SYNC-001: Offline Data Caching
**Priority:** P0 (Critical)
**User Story:** As a Vessel Master, I want to work offline when internet is unavailable.
**Acceptance Criteria:**
- [ ] Cache 1 year of inspection history
- [ ] Cache all deficiencies, CARs, corrective actions
- [ ] Cache all activity events
- [ ] Cache master data (codes, CLC items)
- [ ] Cache attachments up to 150MB total limit
- [ ] Storage warning at <10MB remaining

#### FEAT-SYNC-002: Sync Pull (Server → Vessel)
**Priority:** P0 (Critical)
**User Story:** As a Vessel, I want to receive updates from the server when online.
**Acceptance Criteria:**
- [ ] Delta sync using last_sync_token
- [ ] Receive inspection/deficiency/CAR updates
- [ ] Receive activity events (not audit logs)
- [ ] Receive master data updates
- [ ] Handle deleted records

#### FEAT-SYNC-003: Sync Push (Vessel → Server)
**Priority:** P0 (Critical)
**User Story:** As a Vessel, I want to send my offline changes to the server.
**Acceptance Criteria:**
- [ ] Send queued events in order
- [ ] Upload queued attachments
- [ ] Receive presigned URLs for attachment upload
- [ ] Handle partial failures with retry

#### FEAT-SYNC-004: Conflict Detection
**Priority:** P0 (Critical)
**User Story:** As a system, I want to detect when vessel and office have edited the same record.
**Acceptance Criteria:**
- [ ] Compare client_version (from sync push payload) vs sync_version (server column)
- [ ] Identify conflicting fields
- [ ] Queue conflict for resolution
- [ ] Notify Vessel Master of conflict

#### FEAT-SYNC-005: Conflict Resolution
**Priority:** P0 (Critical)
**User Story:** As an Office user, I want to resolve sync conflicts.
**Acceptance Criteria:**
- [ ] Only Office/DPA can resolve
- [ ] Options: KEEP_SERVER, KEEP_VESSEL, REOPEN_FOR_MERGE
- [ ] KEEP_SERVER: discard vessel changes, notify vessel
- [ ] KEEP_VESSEL: apply vessel changes, audit log
- [ ] REOPEN_FOR_MERGE: set CAR to REWORK_REQUESTED
- [ ] Creates audit log entry

#### FEAT-SYNC-006: Attachment Upload Retry
**Priority:** P1 (High)
**User Story:** As a system, I want to retry failed attachment uploads.
**Acceptance Criteria:**
- [ ] Max 3 retries with exponential backoff
- [ ] Delays: 1s, 2s, 4s
- [ ] After 3 failures: mark as Failed, queue for next sync
- [ ] Show ⚠️ icon for failed uploads
- [ ] Manual retry button available

---

### 2.7 Notifications

#### FEAT-NOTIF-001: In-App Notifications
**Priority:** P1 (High)
**User Story:** As a user, I want to receive notifications for important events.
**Acceptance Criteria:**
- [ ] CAR Created → Vessel Master
- [ ] CAR Submitted → Office PIC/SSQE
- [ ] PIC Accepted → Vessel Master
- [ ] Rework Requested → Vessel Master + Action Owners
- [ ] DPA Closed → Vessel Master
- [ ] Overdue Action (T-3 days) → Action Owner + Master
- [ ] Overdue Action (past due) → Action Owner + Master + Office
- [ ] PSC Follow-up Recorded → Office + Vessel
- [ ] Conflict Detected → Vessel Master
- [ ] Conflict Resolved → Vessel Master
- [ ] Physical Verification Created → Vessel Master

---

### 2.8 Reports & Exports

#### FEAT-RPT-001: CAR PDF Export
**Priority:** P1 (High)
**User Story:** As a user, I want to generate a PDF report of a CAR.
**Acceptance Criteria:**
- [ ] A4 portrait format
- [ ] Company logo header
- [ ] All CAR sections included
- [ ] Evidence list (not embedded images)
- [ ] Review/approval history
- [ ] Physical verification if exists

#### FEAT-RPT-002: Deficiency Excel Export
**Priority:** P1 (High)
**User Story:** As an Office user, I want to export deficiency data to Excel for analysis.
**Acceptance Criteria:**
- [ ] Multi-sheet workbook
- [ ] Sheet 1: Deficiency Summary
- [ ] Sheet 2: CAR Status
- [ ] Sheet 3: Applied Filters
- [ ] Styling: header formatting, alternating rows
- [ ] Detention rows highlighted
- [ ] Auto-filter enabled

---

### 2.9 History & Audit

#### FEAT-HIST-001: Activity History
**Priority:** P0 (Critical)
**User Story:** As any user, I want to see the activity history of an inspection or CAR.
**Acceptance Criteria:**
- [ ] Shows: status changes, submissions, approvals, rework
- [ ] Shows: evidence uploads, action completions
- [ ] Visible to all users including vessel/crew
- [ ] Synced to vessel for offline viewing

#### FEAT-HIST-002: Full Audit Log
**Priority:** P0 (Critical)
**User Story:** As Office/DPA, I want to see detailed audit logs including field-level changes.
**Acceptance Criteria:**
- [ ] Shows: field changes with old/new values
- [ ] Shows: office edit-assist actions
- [ ] Shows: conflict resolutions
- [ ] Records: user_id, role, IP, user_agent
- [ ] NOT synced to vessel (server-only)

---

## 3. Non-Functional Requirements

### 3.1 Performance
- Page load: <2 seconds on 3G connection
- Offline sync: handle 1 year of data within 150MB
- Attachment upload: resume support for files >1MB

### 3.2 Security
- JWT authentication with refresh tokens
- Role-based access control (RBAC) per matrix
- Audit logging for compliance
- No sensitive data in client-side storage

### 3.3 Compatibility
- Browsers: Chrome 90+, Safari 14+, Edge 90+
- Mobile: PWA with offline support
- Responsive: mobile-first design

---

## 4. Out of Scope (v1.0)

- Email notifications (future phase)
- Integration with external PSC databases
- Multi-language support
- Bulk import of historical inspections
- Custom report builder
- Dashboard analytics

---

## 5. Document References

| Document | Purpose |
|----------|---------|
| APP_FLOW.md | Screen inventory and navigation paths |
| TECH_STACK.md | Locked technology versions |
| DESIGN_SYSTEM.md | Visual language and tokens |
| FRONTEND_GUIDELINES.md | Component architecture |
| BACKEND_STRUCTURE.md | Database schema and API contracts |
| VALIDATION_RULES.md | Field validation rules |
| IMPLEMENTATION_PLAN.md | Phased build sequence |

---

**Document Control:**
- Created: 2026-02-03
- Updated: 2026-02-05
- Author: System Generated
- Approved By: [Pending]
- Change Log v1.1: Added FEAT-AUTH-001/002; fixed conflict versioning terms to match BACKEND_STRUCTURE schema (client_version/sync_version); fixed section numbering; corrected status to DRAFT until approval
