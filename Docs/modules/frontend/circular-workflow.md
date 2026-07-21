# Frontend Circular Workflow

## Path

- `psc-frontend/src/routes/circular/page.tsx`
- `psc-frontend/src/components/layout/circular-header-actions.tsx`
- `psc-frontend/src/components/notification/notification-item.tsx`
- `psc-frontend/src/legacy/vims-basic/routes/circular/CircularRoutes.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/circular/`
- `psc-frontend/src/legacy/vims-basic/components/circular/`
- `psc-frontend/src/legacy/vims-basic/utils/circular/permissionUtils.js`

## Purpose

This module renders the legacy circular system inside the modern React shell. It decides which office or ship screen to show, fetches legacy `/api/circular/` endpoints directly from the browser, coordinates multi-step authoring and approval flows through component state plus `localStorage`, and now deep-links circular entries from the shared notification center into the correct legacy screen.

## Owns

- Circular route mounting under `/circular`
- Office create, draft, pending-review, approval, vessel selection, and rank selection UI
- Creator history and draft management UI
- Approved library and crew-delivery status UI
- Ship dashboard filters, list, detail, PDF viewer, acknowledgement, and crew reminder UI
- Permission-gated button visibility for the legacy circular pages
- Shared notification click routing for circular workflow events
- Header create shortcut icon inside the modern shell

## Main Files

- `page.tsx`: mounts the legacy circular app inside `RootLayout` and `LegacyBasicProvider`
- `CircularRoutes.jsx`: route map and role guards
- `Officeuser.jsx`: main office workbench; owns create, draft, pending review, approval, vessel selection, and rank selection flows
- `Admin.jsx`: admin workbench mirroring the office flow with direct-publish and pending-approval actions
- `MainDashboard.jsx`: office landing wrapper around approved library and nav
- `ApprovedNotificationsLibrary.jsx`: approved office library, delete/supersede/reminder/status tools
- `UserNotifications.jsx`: creator-facing approved/rejected history
- `DraftNotifications.jsx`: creator-facing drafts list and draft edit launcher
- `Dashboard.jsx`: ship dashboard state container
- `FilterBar.jsx`: ship filter controls and report download trigger
- `KsmLibrary.jsx`: ship circular card list, crew status modal, and reminder UI
- `PdfViewer.jsx`: PDF rendering with a bundled PDF.js worker, scroll-to-bottom gating, and acknowledgement
- `permissionUtils.js`: parses `form_ids` and `process_ids` from auth state and exposes permission helpers
- `circular-header-actions.tsx`: shell-level create/history/drafts shortcuts; the create affordance now uses a custom inline SVG file-plus style icon without visible text
- `notification-item.tsx`: shared notification-center click handling for `entity_type === 'CIRCULAR'`

## Route Map

- `/circular`: default entry, redirects by role
- `/circular/role-landing`: fallback landing page
- `/circular/dashboard`: office landing page
- `/circular/office`: office/admin authoring workbench
- `/circular/admin`: admin authoring workbench
- `/circular/admin/all-notifications`: admin review list
- `/circular/user/notifications`: creator history
- `/circular/user/drafts`: creator drafts
- `/circular/approved-library`: approved circular library
- `/circular/ship-dashboard`: ship inbox dashboard
- `/circular/pdf-viewer`: shared PDF view screen

## UI Workflow

### Entry and shell

`page.tsx` checks modern auth first. If the user is authenticated, it mounts the legacy module provider and renders `CircularRoutes` inside the app shell.

`CircularRoutes.jsx` then does a second role split:

- office users go to office routes
- ship users go to ship routes
- everything else falls back to `role-landing`

### Office authoring

`Officeuser.jsx` and `Admin.jsx` are large stateful pages that handle:

- lookup loading for type, department, priority, sub-category, second sub-category, vessels, and ranks
- circular form state
- pending queue display
- direct-publish admin flow
- office submit-for-approval flow
- draft save
- pending edit and draft edit prefill
- vessel popup and rank popup
- approval and rejection comment modal
- optional attachment upload with generated-PDF fallback messaging

Both files still mix create, review, publish, and edit behavior instead of splitting them into focused screens or hooks.

### Draft and pending edit handoff

The draft and pending screens do not navigate with typed state. They write prefill data into `localStorage`, then redirect back into the active legacy authoring page (`Officeuser.jsx` or `Admin.jsx`).

Important handoff keys:

- `editingDraftData`
- `editingDraftId`
- `editingPendingNotificationData`
- `editingPendingNotificationSrNo`
- `editingPendingNotificationId`

### Supersede handoff

Supersede also relies on `localStorage`.

Keys used for the supersede prefill:

- `supersedingNotificationId`
- `oldNotificationType`
- `oldNotificationDept`
- `oldNotificationCategory`
- `oldNotificationPriority`
- `oldNotificationSubCatNames`
- `oldNotificationSecondSubCatNames`

### Approval handoff

Approval is staged across multiple UI steps:

1. use the selected pending-row data directly
2. store approval context in `localStorage`
3. open vessel popup
4. open comment modal
5. call status update endpoint
6. open rank popup immediately after approval succeeds
7. call vessel email endpoint in the background
8. call rank-link endpoint

Approval context keys:

- `approvingNotificationSrNo`
- `approvingNotificationDept`
- `selectedVesselIdsForNotification`

This is an intentional change from the older flow. The current pages no longer block approval on an extra `get_notification_details` fetch before opening the vessel popup, which removed the slower failing path that previously surfaced `500` errors during approval.

### Notification center integration

Circular workflow notifications are rendered inside the same shared notification tab used by inspections.

- `notification-item.tsx` recognizes `entity_type === 'CIRCULAR'`.
- office admin users are routed to `/circular/admin?panel=pending-requests`
- other office users are routed to `/circular/office?panel=pending-requests`
- vessel users are routed to `/circular/ship-dashboard`
- `Officeuser.jsx` and `Admin.jsx` read `panel=pending-requests`, auto-open the pending-request section, and scroll it into view once the list is available

### Ship flow

`Dashboard.jsx` owns ship view state only:

- search term
- scope/type/criticality filters
- unread toggle
- selected circular
- list vs PDF mode

`KsmLibrary.jsx` does the actual ship-side data fetch:

- masters call `/api/ship/notifications/`
- non-masters call `/api/crew/notifications/`
- masters can open crew list and send reminders

`PdfViewer.jsx` fetches the attachment URL, renders the PDF with PDF.js, and only exposes the acknowledge button once the viewer is scrolled to the bottom. Both circular PDF viewer entry points use a Vite-bundled PDF.js worker instance so production does not depend on the server MIME type for a separate `.mjs` worker asset.

## Permission Model In The Frontend

The ship dashboard uses form/process IDs from auth state. `permissionUtils.js` normalizes mixed `F_` and `PSC_F_` style values and mixed JSON-string or comma-separated storage formats.

The important consequence is that the frontend, not the backend, decides whether most circular actions are visible. Because the backend routes are largely open, this is a presentation guard, not a security boundary.

## API Contract Expectations

The frontend expects several inconsistent response shapes and works around them manually.

- document types, departments, and priorities arrive as tuple arrays such as `[id, name]`
- sub-categories and second sub-categories arrive as objects
- some screens expect `dept` to behave like an integer flag
- other screens expect department UUIDs or department names
- pending-request lists now also consume backend-provided `dept_name` to reduce local fallback mapping

This is why many pages build their own name-to-id and id-to-name maps locally.

## Current Risks And Breakpoints

### 1. The legacy office workbenches are still the module's main failure points

`Officeuser.jsx` and `Admin.jsx` are still very large components responsible for almost every office-side state transition. Authoring, review, approval, publish, edit, vessel selection, rank selection, and local storage restoration are interleaved instead of being split into focused units.

### 2. Approval and delivery are still split across multiple requests

- status update
- vessel email dispatch
- rank-link delivery

The UI now moves faster by opening the rank popup immediately after approval succeeds, but these side effects are still not wrapped in a single transactional frontend flow. Partial success is still possible.

### 3. Department semantics are inconsistent across screens

Some code maps department by UUID and some code still expects `dept === 0` or `dept === 1`.

That affects:

- office approval vessel-selection context
- rank popup department lookup
- supersede prefill
- ship scope labeling

### 4. The workflow depends heavily on `localStorage`

Draft edit, pending edit, supersede, and approval all persist ephemeral state into `localStorage`. That makes flows brittle across tabs, reloads, and stale-session scenarios.

### 5. Hard-coded backend URLs are everywhere

Most requests point directly at `http://localhost:8000/api/circular/...` instead of using a shared API client. This makes environment changes and testing harder.

### 6. There are duplicate approval implementations

`Officeuser.jsx` contains overlapping approval logic:

- `handleConfirmPublish`
- `handleConfirmApprovalWithComment`
- `submitApprovalOrRejection`

They do similar work but are not cleanly consolidated, so behavior can drift.

### 7. New shell integration is still only partial

The circular module lives inside the modern shell, but most of the logic still uses legacy hooks, legacy routes, hard-coded URLs, ad hoc state transfer, and direct `fetch` calls to `http://localhost:8000`.

The newer pieces added around it are shell wrappers, not a full modernization:

- the header action icon is modern-shell UI around a legacy route
- notification center deep-links land inside legacy pages and still depend on query params plus `localStorage`

## Dependencies

- modern auth shell: `useAuth`, `RootLayout`, and the app route wrapper
- legacy module provider and legacy auth hook
- backend circular office and ship APIs
- auth-store user state for logout and permission IDs
- PDF.js for ship-side attachment rendering

## Maintenance Notes

- If you touch office flows, start with `Officeuser.jsx` and trace every `localStorage` key it reads and writes.
- If you touch draft edit or supersede behavior, verify the redirect target and storage cleanup path.
- If you touch ship flows, verify both `KsmLibrary.jsx` and `PdfViewer.jsx`; the list and detail flows each send writes.
- If you touch approval flows, verify all three stages together: `update-status`, `send-emails`, and `link-ranks`.
- If you touch notification behavior, verify both `notification-item.tsx` deep-link routing and the `panel=pending-requests` handling in `Officeuser.jsx` and `Admin.jsx`.
- Prefer consolidating API calls behind a shared client before changing endpoint contracts.
- Any real refactor should split the office page into at least create, review, and publish/routing concerns before adding new features.
