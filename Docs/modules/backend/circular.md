# Circular Module

## Path

- `psc-backend/modules/circular/circular/`
- `psc-backend/modules/circular/circular_office/`
- `psc-backend/modules/circular/circular_ship/`
- `psc-backend/core/urls.py` mounts both office and ship APIs under `/api/circular/`

## Purpose

This is a legacy circular distribution system embedded inside the PSC backend. It covers office-side circular authoring and approval, vessel-level email delivery, crew-level rank assignment, ship-side inbox and acknowledgement tracking, reminder flows, report exports, and workflow event emission into the shared in-app notification system.

The module is split into three Django apps:

- `circular`: shared unmanaged table models and cross-cutting data access.
- `circular_office`: office and admin APIs for authoring, review, publishing, lookup, reporting, and delivery setup.
- `circular_ship`: ship APIs for master and crew inboxes, PDF access, acknowledgement, reminders, and ship-side reporting.

## Owns

- Circular creation, draft save, draft edit, and pending edit
- Serial number generation and PDF cover generation
- Approval and rejection workflow
- Vessel email dispatch and vessel-level delivery tracking
- Rank-to-crew expansion and crew-level delivery tracking
- Circular workflow notification triggers into `psc_notification`
- Ship inbox list, acknowledgement, unread/reminder state, and crew status views
- Approved library export/report generation
- Supersede and soft-delete behavior

## Main Files

- `circular/models.py`: unmanaged SQL Server tables used by both office and ship flows
- `circular_office/views.py`: the main office workflow surface and most business logic
- `circular_office/urls.py`: office route inventory
- `circular_ship/views.py`: ship inbox, acknowledgement, reminder, and PDF/report logic
- `circular_ship/urls.py`: ship route inventory
- `circular_office/models.py`: unmanaged support tables such as `department`, `master_role`, `mapping_role_user`, `users`, and `final_crew_list`
- `circular_ship/models.py`: unmanaged ship auth and acknowledgement history tables
- `apps/notifications/models.py`: shared `psc_notification` types now extended for circular workflow events
- `apps/notifications/signals.py`: helper functions that fan circular events out to office users and crew

## Core Data Model

The system depends on external SQL Server tables. Almost every model is `managed = False`, so the schema is treated as existing infrastructure rather than Django-owned state.

- `MscData`: the main circular header table. Stores SR number, type, department, category, body, creator, approval fields, attachment metadata, priority, and vessel CSV.
- `MscNotification`: crew-level delivery table keyed by `msc_sr_no` and `crew_id`. Tracks delivered, seen, reminder timestamp, and `reminder_count`.
- `MscShipNotification`: vessel-level delivery table keyed by `msc_sr_no_` and vessel. Used for master inbox and vessel delivery state.
- `MscRankAssigned`: selected rank links for a published notification.
- `MscAcknowledgeHistory`: crew acknowledgement history keyed by `msc_sr_no` and `read_by`, with its own `reminder_count`.
- `HRM501`: crew master table used for rank, department, email, and crew mapping.
- `FinalCrewList`: bridge from `HRM501.id` to ship-facing `CrewID`.
- `CrewOnboardingHistory` and `VesselData` from ORB: vessel placement and vessel contact information.
- Lookup tables: `MscType`, `MscPriority`, `MscSubCat`, `Msc2ndSubCat`, `Department`, `MasterAppliedRank`, `MasterRole`, `MappingRoleUser`, `User`.

## Status Model

- `publish_status = 0`: draft
- `publish_status = 1`: pending approval
- `publish_status = 2`: approved/published
- `publish_status = 3`: rejected

Delivery state is not driven by `publish_status` alone.

- Vessel delivery exists only after `send_emails_to_vessels` inserts `msc_ship_notification`.
- Crew delivery exists only after `link_notification_to_ranks` inserts `msc_notification`.
- Crew acknowledgement status is derived by comparing `msc_notification.reminder_count` with `msc_acknowledge_history.reminder_count`.

## Backend Route Map

### Office lookup and setup APIs

- `get_document_types`, `get_departments`, `get_priorities`
- `get_sub_categories`, `get_second_sub_categories`
- `get_vessels`
- `get_master_applied_ranks`, `get_all_ranks`
- `get_master_roles`, `get_mapping_role_users`, `get_users`
- `get_crews_by_department`, `get_crews_by_department_and_vessel`

### Office authoring and review APIs

- `create_notification`: create draft, pending, or directly published circular rows and generate attachment PDF cover
- `get_notifications`: admin/office list for pending, approved, and rejected items; now also emits `dept_name` to stabilize frontend department resolution
- `get_notification_details` and `get_notification_details_by_sr_no`: fetch one circular by SR number
- `get_user_notifications`: creator-facing approved/rejected history
- `update_notification_status`: approve or reject a pending circular and regenerate the PDF cover with approval footer
- `delete_notification`: soft-delete by SR number
- `supersede_notification`: mark an older circular as superseded
- `edit_pending_notification`: update a pending circular in place

### Draft APIs

- `get_notifications_draft`: all drafts
- `get_user_drafts`: current creator's drafts
- `get_draft_by_sr_no`: draft prefill for editing
- `delete_draft_by_sr_no`: soft-delete draft
- `update_draft_by_sr_no` and `update_draft_by_id`: alternate draft update paths

### Delivery and reporting APIs

- `send_emails_to_vessels`: send vessel emails and insert vessel delivery rows
- `create_delivery_records`: manual crew delivery row insertion helper
- `link_notification_to_ranks`: expand selected ranks into crew deliveries and rank assignment rows
- `get_crew_ids_and_status_by_notification_sr_no`: office-side crew delivery status list
- `send_individual_notification_reminder`: update one crew delivery reminder timestamp
- `get_approved_notifications`: approved library list
- `get_approved_notifications_csv`: PDF export of approved library results

### Ship APIs

- `get_master_notifications`: master inbox derived from `msc_ship_notification`
- `get_non_master_notifications`: crew inbox derived from `msc_rank_assigned` and `msc_notification`
- `get_crew_list` and `get_crew_status`: master view of crew acknowledgement state for a circular
- `send_reminder`: master reminder to one crew member
- `crew_acknowledge_notification`: crew acknowledgement write path
- `get_notification_pdf_url`: resolve a circular attachment URL
- `download_filtered_report`: PDF report export for ship dashboard filters

## Actual Workflow

### 1. Draft or pending creation

`create_notification` accepts multipart form data from the legacy office UI. It:

- normalizes UUID-like inputs for type, priority, sub-category, second sub-category, and vessels
- generates the next SR number as `KSM/{type}/{department}/{year}-{serial}`
- generates a new circular PDF artifact even when no attachment is uploaded
- merges the generated cover with the uploaded PDF only when an attachment is provided
- inserts directly into `msc_data` using raw SQL
- optionally records supersede metadata on the previous circular
- emits shared circular notifications on commit:
  - draft save -> `CIRCULAR_CREATED`
  - pending approval submission -> `CIRCULAR_PENDING_APPROVAL`
  - direct publish -> `CIRCULAR_APPROVED`

For office users the frontend usually sends `publish_status = 1`, so the record becomes pending approval. For admin direct-publish flows the frontend sends `publish_status = 2`.

### 2. Draft storage and draft editing

Drafts are just `msc_data` rows with `publish_status = 0`.

- `get_user_drafts` lists them.
- `get_draft_by_sr_no` returns raw UUID values for prefill.
- `update_draft_by_id` is the real database-id update path used by the current frontend.
- `delete_draft_by_sr_no` soft-deletes the draft.

### 3. Approval or rejection

`update_notification_status` is the status transition point for pending rows.

- Rejection writes `publish_status = 3` and the review comment.
- Approval writes `publish_status = 2`, `published_by`, and `published_on`.
- On approval it also regenerates the first PDF pages so the published cover includes approval metadata.
- It now also sends shared circular notifications back to the creator:
  - approval -> `CIRCULAR_APPROVED`
  - rejection -> `CIRCULAR_REJECTED`

This endpoint does not create crew delivery rows. That happens later.

### 4. Vessel delivery

After approval, the office UI calls `send_emails_to_vessels`.

- It loads `VesselData` for each selected vessel.
- It sends an email to the vessel contact.
- It inserts one `msc_ship_notification` row per vessel.

That vessel-level row is what drives the master inbox.

### 5. Rank assignment and crew delivery

After vessel selection, the office UI calls `link_notification_to_ranks`.

- Selected rank UUIDs are validated.
- `HRM501` is filtered by those rank UUIDs.
- Matching `FinalCrewList` rows are expanded to ship-facing `CrewID` values.
- One `msc_notification` row is inserted per crew with `reminder_count = 1`.
- One `msc_rank_assigned` row is inserted per chosen rank.
- Unique crew recipients also receive shared in-app notifications through `psc_notification`.

That crew-level row is what drives non-master inbox entries and acknowledgement state.

### 6. Ship consumption

Master flow:

- `get_master_notifications` uses the logged-in crew member's active vessel from `Crew_Onboarding_History`.
- It resolves published circulars from `msc_ship_notification`.
- It joins into `msc_data` for titles, types, priorities, attachment paths, and delivery metadata.
- It computes unread counts by comparing `msc_notification` and `msc_acknowledge_history` for crew on the same vessel.

Non-master flow:

- `get_non_master_notifications` uses the crew member's rank from `HRM501`.
- It resolves matching circular SR numbers from `msc_rank_assigned`.
- It joins into `msc_data` and crew delivery state in `msc_notification`.

### 7. PDF access and acknowledgement

- `get_notification_pdf_url` converts the stored absolute attachment path into a media URL.
- `crew_acknowledge_notification` updates `msc_notification.seen_at` and inserts or updates `msc_acknowledge_history`.
- If the acknowledging user is a master, `master_acknowledge_ship_notification` also updates `msc_ship_notification.seen_at`.

### 8. Reminders and reporting

- `send_reminder` updates `msc_notification.reminder_sent_at`, increments `reminder_count`, and emails the specific crew member.
- `send_individual_notification_reminder` only updates the reminder timestamp for a single crew delivery row.
- `download_filtered_report` builds a ship-side PDF report from the currently visible inbox filters.
- `get_approved_notifications_csv` actually generates a PDF, not CSV, for the approved office library.

## Shared Notification Integration

Circular workflow events now reuse the shared notifications module instead of introducing any circular-specific notification tables.

- Storage remains the existing `psc_notification` table.
- No new circular notification migration was added.
- Circular events are emitted from `circular_office/views.py` into helper functions in `apps/notifications/signals.py`.
- The current circular notification types are:
  - `CIRCULAR_CREATED`
  - `CIRCULAR_PENDING_APPROVAL`
  - `CIRCULAR_APPROVED`
  - `CIRCULAR_REJECTED`

Current trigger points:

- `create_notification`
  - draft save -> creator notified
  - submit for approval -> creator and reviewer roles notified
  - direct publish -> creator notified
- `update_notification_status`
  - approval/rejection -> creator notified
- `link_notification_to_ranks`
  - final crew distribution -> unique crew recipients notified

## PDF and Attachment Flow

- Uploaded PDFs are stored under `MEDIA_ROOT/circular/attachments/`.
- `attachment_path` stores the filesystem path.
- Most APIs derive `attachment_url` from `attachment_name` and `MEDIA_URL`.
- Cover pages are created with ReportLab.
- Existing PDFs are merged or rewritten with `PyPDF2`.
- Attachment upload is now optional for circular creation and draft update.
- When the user skips the upload, the backend still generates a valid circular PDF from form content and stores that generated PDF as the attachment artifact.
- The preserved `original_...` copy only exists when the user actually uploaded a source PDF.

There are two separate cover-generation paths:

- initial creation in `create_notification`
- approval or pending-edit regeneration in `update_notification_status` and `edit_pending_notification`

## Cross-Module Dependencies

- ORB models: `VesselData`, `MasterAppliedRank`, `CrewOnboardingHistory`
- shared auth user data: `users`, `master_role`, `mapping_role_user`
- frontend legacy circular module under `psc-frontend/src/legacy/vims-basic/pages/circular/`
- Django email configuration and media storage
- SQL Server-specific behavior and raw SQL casts to `UNIQUEIDENTIFIER`

## Current Risks And Breakpoints

### 1. Department handling is still partially inconsistent

The module migrated `dept` toward UUID or master-driven lookup, but some legacy branches still treat it as `0` or `1`.

- `create_notification` inserts the department UUID into `msc_data`.
- `get_notifications` and detail APIs now emit `dept_name`, which reduces frontend guesswork.
- Some status-update and ship-scope paths still branch on integer `0` and `1`.
- Result: department-dependent behavior is improved in pending-request UI flows, but some legacy paths can still degrade to `Unknown`.

### 2. Approval status handling still contains legacy datetime code

- `update_notification_status` still references `django_timezone_utc` in a legacy published-date parsing branch.
- The current frontend approval flow usually sends an ISO timestamp and avoids the slower failing details fetch, but this code path is still present and should be cleaned up before deeper refactors.

### 3. Route and API shapes do not match cleanly

- The frontend uses both SR-number and database-id update semantics for drafts.
- Lookup endpoints return mixed response shapes: some return `[id, name]` tuples, others return objects.
- `get_approved_notifications_csv` returns a PDF even though the endpoint name and frontend label say CSV.

### 4. Delivery is split across multiple side effects

Approval alone does not make a circular visible to crew.

- vessel visibility depends on `send_emails_to_vessels`
- crew visibility depends on `link_notification_to_ranks`

If the second step fails or is skipped, the circular can be approved and emailed to vessels while still missing from crew inboxes.

### 5. Security is weak

- Every office and ship endpoint uses `AllowAny`.
- `get_users` returns raw password fields from the `users` table.

This module should be treated as publicly reachable unless an external gateway blocks it.

### 6. The code is hard to change safely

- `circular_office/views.py` is a very large function-heavy file with multiple overlapping implementations of the same workflow.
- The ship and office modules mix ORM and raw SQL heavily.
- The apps have effectively no real tests.

## What To Read First Before Changing It

If you need to modify behavior safely, read in this order:

1. `circular_office/urls.py` and `circular_ship/urls.py`
2. `circular/models.py`, `circular_office/models.py`, `circular_ship/models.py`
3. `create_notification`, `update_notification_status`, `send_emails_to_vessels`, `link_notification_to_ranks`
4. `get_master_notifications`, `get_non_master_notifications`, `crew_acknowledge_notification`
5. the legacy frontend files that call those endpoints

## Maintenance Notes

- Treat `sr_no` as the business identifier, but remember many code paths still rely on database `id` for editing.
- Be careful with department and rank values: some code expects UUID strings, some expects display names, and some still assumes integers.
- If you change delivery logic, verify both `msc_ship_notification` and `msc_notification`.
- Any change to acknowledgement or reminder logic should preserve the `reminder_count` comparison contract.
- Add integration tests before refactoring any approval, rank-link, or acknowledgement path.
