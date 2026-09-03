# OCR Plan

## Status

This is a proposed implementation plan. It is not implemented yet.

If this plan is implemented, treat it as a maintain-mode structural change because it changes OCR behavior, adds database fields, changes upload response timing, and introduces a separate background worker service. Open a CR before coding.

## Goal

Certificate PDF upload should work smoothly on the current 6 GB RAM server without reducing the original PDF quality or blocking users while OCR is running.

The target behavior is:

```text
Upload PDF -> save original PDF -> return upload success -> run OCR in background -> update extracted fields later
```

Upload validation:

```text
Certificate PDF size must not exceed 20 MB.
```

## Current Problem

Currently, certificate upload and OCR processing happen inside the same API request. For large or scanned PDFs, OCR can consume high RAM while the browser is waiting. This can cause request timeout, 500 errors, or Gunicorn worker termination.

The stored PDF file itself is not the main RAM problem. The RAM pressure happens when OCR actively renders/reads PDF pages and loads OCR models.

## Recommended Approach

Use this combined approach:

1. Upload first.
2. OCR later in background.
3. Run only one OCR job at a time.
4. Try selectable-text extraction before OCR.
5. Keep original PDF unchanged.
6. If OCR cannot safely read the PDF, mark it for manual verification instead of failing the upload.

## User-Facing Workflow

Current workflow:

```text
User uploads PDF -> user waits for OCR -> success or failure
```

Proposed workflow:

```text
User uploads PDF -> upload succeeds -> OCR status shows pending/processing -> extracted data appears after OCR
```

After a successful upload, show a user-facing information line with an estimated OCR processing time based on the PDF size:

```text
Your PDF has been uploaded successfully. It will take approximately <n> minutes to update the details. Please check again in a while.
```

Suggested estimate bands:

| PDF size | Message estimate |
|---|---|
| Up to 5 MB | 1-2 minutes |
| More than 5 MB and up to 10 MB | 2-4 minutes |
| More than 10 MB and up to 20 MB | 4-8 minutes |

The estimate should be treated as guidance only because scanned-image quality, page count, and OCR queue length can change actual processing time.

If OCR fails:

```text
PDF remains uploaded -> status becomes Manual Verification Required -> user checks/enters fields manually
```

## OCR Status Flow

```text
PENDING
PROCESSING
COMPLETED
MANUAL_REVIEW_REQUIRED
FAILED
```

Suggested display labels:

```text
OCR pending
OCR processing
OCR completed
Manual verification required
OCR failed
```

## Files To Change

| Area | File | Required change | Effect |
|---|---|---|---|
| Backend model | `psc-backend/apps/certs/models/tracked_item.py` | Add OCR status fields to `PdfBlob` model after DB migration fields exist. | Python model matches database columns. No workflow change by itself. |
| Backend repository | `psc-backend/apps/certs/services/pdf_blob_repository.py` | Read/write `ocr_status`, `ocr_attempt_count`, `ocr_last_error`, `ocr_locked_at`, `ocr_locked_by`, and optional retry timestamp. Add methods to mark pending, claim job, complete job, fail job. | Upload and worker can share DB-safe OCR status logic. |
| Backend OCR pipeline | `psc-backend/apps/certs/services/ocr_pipeline.py` | Add text-extraction-first path before PaddleOCR. Keep PaddleOCR fallback for scanned PDFs. Keep manual-entry payload fallback. | Reduces RAM for digital PDFs without reducing OCR quality. |
| Backend upload API | `psc-backend/apps/certs/views/tracked_item_views.py` | Stop running `process_cert_pdf()` inside `TrackedItemUploadPdfView` and `TrackedItemReparsePdfView`. Save PDF, mark OCR `PENDING`, return success. | Upload becomes fast and stable. OCR fields are no longer immediately available in the upload response. |
| Backend upload validation | `psc-backend/apps/certs/views/tracked_item_views.py` and related serializers | Enforce a 20 MB maximum PDF upload size before saving/queuing OCR. | Oversized PDFs are rejected with a clear validation error instead of entering the OCR queue. |
| Backend serializers | `psc-backend/apps/certs/serializers/tracked_item.py` | Include OCR status/error fields in `serialize_pdf_blob()` and tracked-item detail payload where needed. | UI can show pending/processing/manual-review state. |
| Backend tracked item updates | `psc-backend/apps/certs/services/tracked_item_repository.py` | Move OCR auto-fill update logic into a reusable method, so the background worker can update certificate number, issuer, place, issue date, and expiry date after OCR. | Auto-filled certificate metadata becomes asynchronous. |
| Backend queue service | `psc-backend/apps/certs/services/ocr_queue.py` | New service for queue operations: mark pending, claim next job, complete, manual-review, fail/retry. | Keeps concurrency and status transitions centralized. |
| Backend worker command | `psc-backend/apps/certs/management/commands/process_certs_ocr_queue.py` | New command that continuously or repeatedly processes one pending OCR job at a time. | Enables a separate server OCR service. |
| Backend class snapshots | `psc-backend/apps/certs/views/snapshot_views.py` | Stop parsing class snapshots inside upload request. Save file, create snapshot, mark parsing/OCR pending, process later. | Prevents class snapshot OCR from causing RAM pressure during upload. |
| Backend snapshot repository | `psc-backend/apps/certs/services/snapshot_repository.py` | Add/update methods to mark snapshot parse pending/processing/success/failed when processed by worker. | Class snapshot UI can show delayed parse result. |
| Backend parser worker | `psc-backend/apps/certs/jobs/parser_worker.py` | Reuse from background worker instead of request path, or split certificate OCR and class snapshot parsing into separate worker functions. | Keeps heavy parser work outside Gunicorn. |
| Backend URLs | `psc-backend/apps/certs/urls.py` | Usually no new endpoint is required if existing detail responses expose OCR status. Add status/retry endpoint only if UI needs a manual retry button. | API surface can remain mostly stable. |
| Backend tests | `psc-backend/apps/certs/tests.py` or `psc-backend/tests/certs/*` | Add regression tests for async upload, pending OCR state, worker completion, failure/manual fallback, and reparse. | Prevents upload from accidentally becoming synchronous again. |
| Frontend API types | `psc-frontend/src/lib/api/certs.ts` | Add OCR status/error fields to PDF blob types. Make upload response not depend on immediate `ocrPayload`. | TypeScript matches async backend behavior. |
| Frontend hook | `psc-frontend/src/hooks/certs/use-tracked-item.ts` | After upload/reparse, refresh tracked item detail and optionally poll while OCR status is pending/processing. | UI updates when OCR finishes. |
| Frontend Certs page | `psc-frontend/src/routes/certs/index.tsx` | Show OCR pending/processing/completed/manual verification states. Do not expect extracted OCR fields immediately after upload. | Users understand upload succeeded even while OCR is pending. |
| Frontend tests | `psc-frontend/src/lib/api/certs.test.ts` and Certs route tests if present | Update mocks/assertions for asynchronous OCR response and status display. | Frontend behavior is protected. |
| Server service | `/etc/systemd/system/InspectionOCR.service` on server | New systemd service running the OCR worker command separately from Gunicorn. | OCR memory pressure is isolated from the web service. |
| Deployment docs/scripts | Existing deployment notes or runbook if used | Add copy/restart steps for worker service and migration. | Server deployment becomes repeatable. |

## Database Impact

Primary table affected:

```text
dbo.vims_certs_pdf_blob
```

Suggested new columns:

```sql
ocr_status NVARCHAR(32) NOT NULL DEFAULT 'PENDING'
ocr_attempt_count INT NOT NULL DEFAULT 0
ocr_last_error NVARCHAR(MAX) NULL
ocr_locked_at DATETIME2 NULL
ocr_locked_by NVARCHAR(128) NULL
ocr_next_attempt_at DATETIME2 NULL
```

Existing columns still used:

```text
ocr_payload_json
ocr_confidence_per_field
ocr_processed_at
ocr_engine_version
```

Recommended index:

```text
IX_vims_certs_pdf_blob_ocr_queue
```

Purpose of index:

```text
Find pending OCR jobs quickly without scanning all PDF blob rows.
```

Suggested indexed fields:

```text
ocr_status
ocr_next_attempt_at
uploaded_at
is_active
```

### Existing Data Backfill

Existing PDF rows should be backfilled carefully:

```text
If ocr_processed_at is not null -> COMPLETED
If ocr_payload_json contains manual-entry result -> MANUAL_REVIEW_REQUIRED
If active PDF has no OCR result -> PENDING, only if business wants old PDFs reprocessed
Otherwise -> COMPLETED or leave as not queued based on migration decision
```

Do not change:

```text
blob_id
tracked_item_id
snapshot_id
blob_storage_path
filename
content_sha256
content_size_bytes
uploaded_by
uploaded_at
is_active
```

### Tracked Item Field Impact

The worker may update these existing `dbo.vims_certs_tracked_item` fields after OCR completes:

```text
certificate_number
issuing_authority
place_of_issue
issue_date
expiry_date
pdf_attachment_id
pdf_missing
updated_at
updated_by
version
```

Main behavior change:

```text
These fields may update after upload, not during upload.
```

This means UI must show pending OCR instead of assuming the fields are instantly available.

## API Impact

Upload endpoint behavior changes from synchronous to asynchronous.

Affected endpoint:

```text
POST /api/certs/tracked-items/{id}/upload-pdf/
```

Current response behavior:

```text
Returns uploaded PDF plus OCR payload after OCR finishes.
```

Proposed response behavior:

```text
Returns uploaded PDF immediately with OCR status PENDING.
OCR payload may be null until background processing finishes.
```

The upload response should include enough metadata for the frontend to show the size-based processing estimate:

```text
content_size_bytes
ocr_status = PENDING
estimated_ocr_minutes or estimated_ocr_message
```

Reparse endpoint behavior also changes:

```text
POST /api/certs/tracked-items/{id}/reparse-pdf/
```

Current:

```text
Runs OCR immediately.
```

Proposed:

```text
Marks active PDF OCR status as PENDING and returns success.
```

No permission change is required.

## Frontend Impact

The frontend must stop assuming OCR output is available immediately after upload.

UI should show:

```text
Upload successful
OCR pending
OCR processing
OCR completed
Manual verification required
```

After upload, the success state should include the estimated timing message:

```text
Your PDF has been uploaded successfully. It will take approximately <n> minutes to update the details. Please check again in a while.
```

The certificate detail screen should allow the user to continue viewing the uploaded PDF even if OCR is still pending or failed.

If OCR fails, the UI should guide the user to verify or manually enter certificate fields.

## Server Impact

Gunicorn should remain for web/API only.

New worker service should run OCR separately:

```text
Inspection.service     -> Django/Gunicorn web API
InspectionOCR.service  -> OCR worker only
```

Recommended worker behavior for current 6 GB RAM server:

```text
one OCR process only
one OCR job at a time
restart on failure
optional recycle after each heavy job
separate logs in journalctl
```

This does not remove OCR RAM usage, but it prevents OCR from killing the main web service.

## OCR Quality Impact

This plan should not reduce OCR quality because:

- The original PDF is stored unchanged.
- Users are not forced to compress PDFs.
- Pages are not rejected only because the PDF has many pages.
- Selectable text is tried before OCR.
- OCR still uses the original document when needed.

Possible tradeoff:

```text
OCR result may take longer to appear if multiple PDFs are waiting.
```

## Things To Avoid

- Do not reduce PDF quality before OCR.
- Do not force heavy compression.
- Do not skip pages as a business rule.
- Do not run multiple OCR jobs together on a 6 GB server.
- Do not rely only on increasing request timeout.

## Docs To Update When Implemented

When this plan is implemented, update these docs in the same commit:

| Doc | Required update |
|---|---|
| `crs/CR-###.md` | Required CR because implementation changes DB fields, endpoint behavior, and server processing. |
| `certs_docsuite/IMPLEMENTATION_PLAN.md` | Add append-only amendment for asynchronous OCR/background worker behavior. |
| `certs_ssot/VIMS-CERTIFICATES-MODULE-SSOT.md` | Add/supersede decision for upload-first OCR-later lifecycle and manual fallback. |
| `certs_docsuite/APP_FLOW.md` | Change certificate upload flow from synchronous OCR to async OCR status lifecycle. |
| `certs_docsuite/BACKEND_STRUCTURE.md` | Document new OCR queue service, worker command, repository methods, and DB columns. |
| `certs_docsuite/FIELD_MAP.md` | Add OCR status/error fields and explain delayed updates to tracked-item OCR-derived fields. |
| `certs_docsuite/PRD.md` | Document user-facing behavior: upload succeeds first, OCR result may appear later. |
| `certs_docsuite/USER_GUIDE.md` | Explain OCR pending/processing/manual verification states for Certs users. |
| `certs_docsuite/VALIDATION_RULES.md` | Explain upload size validation remains separate from OCR processing outcome. |
| `certs_docsuite/OBSERVABILITY.md` | Add OCR worker logs, queue monitoring, failure count, and manual-review metrics. |
| `certs_docsuite/TECH_STACK.md` | Document separate OCR worker service and runtime dependency on PaddleOCR/PDF tooling. |
| `Docs/OFFICE_CERTS_USER_GUIDE.md` | Update office user instructions for upload success and delayed OCR/manual verification. |
| `Docs/SHIP_CERTS_USER_GUIDE.md` | Update ship user instructions if vessel users can upload certificate PDFs. |
| `Docs/progress.txt` | Append maintain-mode progress entry. |

Docs likely unchanged unless implementation touches them:

```text
certs_docsuite/SECURITY.md
certs_docsuite/DESIGN_SYSTEM.md
certs_docsuite/FRONTEND_GUIDELINES.md
```

Update them only if the implementation changes file access permissions, visible design patterns, or frontend design rules.

## Test Plan

Backend tests:

```text
PDF upload saves file and returns success without calling OCR directly
PDF blob is marked PENDING after upload
reparse marks active PDF PENDING
worker claims only one pending job
worker stores OCR payload and marks COMPLETED
worker stores manual payload and marks MANUAL_REVIEW_REQUIRED on OCR failure
worker does not process inactive/superseded PDFs
same-PDF upload behavior remains compatible
class snapshot upload no longer parses inside request
```

Frontend tests:

```text
upload success can render with OCR payload null
OCR pending/processing/completed labels display correctly
manual verification required state displays clearly
tracked-item detail refresh/polling updates completed OCR fields
```

Server verification:

```text
Inspection.service handles API requests without OCR running inside Gunicorn
InspectionOCR.service processes one OCR job at a time
journalctl logs show worker failures separately from web service failures
large PDF upload returns success before OCR finishes
```

## Rollout Plan

1. Create CR and doc amendment.
2. Add DB migration and backfill strategy.
3. Add repository/service status methods.
4. Change upload/reparse endpoints to mark OCR pending.
5. Add worker command.
6. Add text-extraction-first pipeline.
7. Update frontend status display.
8. Add tests.
9. Deploy backend and frontend.
10. Run migration.
11. Create and start `InspectionOCR.service`.
12. Upload one known good PDF and one difficult scanned PDF for verification.

## Rollback Plan

If the worker causes issues:

```text
Stop InspectionOCR.service
Keep uploaded PDFs stored
Manual verification can continue
Web/API service remains available
```

If async OCR must be rolled back:

```text
Restore previous upload/reparse view behavior
Leave new DB columns in place unused
Disable OCR worker service
```

## Best Short Explanation

We will separate PDF upload from OCR. The PDF uploads first and remains saved. OCR runs separately in the background, one file at a time, using the original PDF. If OCR cannot read the document safely, the system keeps the PDF and asks for manual verification instead of failing the upload.
