# Frontend Circular Workflow

## Path

- `psc-frontend/src/routes/circular/page.tsx`
- `psc-frontend/src/components/layout/circular-header-actions.tsx`
- `psc-frontend/src/legacy/vims-basic/routes/circular/CircularRoutes.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/circular/`
- `psc-frontend/src/legacy/vims-basic/components/circular/`
- `psc-frontend/src/legacy/vims-basic/utils/circular/permissionUtils.js`

## Purpose

This module renders the legacy circular system inside the modern React shell. It decides which office or ship screen to show, fetches legacy `/api/circular/` endpoints directly from the browser, and coordinates multi-step authoring and approval flows through component state plus `localStorage`.

## Owns

- Circular route mounting under `/circular`
- Office create, draft, pending-review, approval, vessel selection, and rank selection UI
- Creator history and draft management UI
- Approved library and crew-delivery status UI
- Ship dashboard filters, list, detail, PDF viewer, acknowledgement, and crew reminder UI
- Permission-gated button visibility for the legacy circular pages

## Main Files

- `page.tsx`: mounts the legacy circular app inside `RootLayout` and `LegacyBasicProvider`
- `CircularRoutes.jsx`: route map and role guards
- `Officeuser.jsx`: main office/admin workbench; this is the dominant file in the module
- `MainDashboard.jsx`: office landing wrapper around approved library and nav
- `ApprovedNotificationsLibrary.jsx`: approved office library, delete/supersede/reminder/status tools
- `UserNotifications.jsx`: creator-facing approved/rejected history
- `DraftNotifications.jsx`: creator-facing drafts list and draft edit launcher
- `Dashboard.jsx`: ship dashboard state container
- `FilterBar.jsx`: ship filter controls and report download trigger
- `KsmLibrary.jsx`: ship circular card list, crew status modal, and reminder UI
- `PdfViewer.jsx`: PDF rendering, scroll-to-bottom gating, and acknowledgement
- `permissionUtils.js`: parses `form_ids` and `process_ids` from auth state and exposes permission helpers

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

`Officeuser.jsx` is a single large stateful page that handles:

- lookup loading for type, department, priority, sub-category, second sub-category, vessels, and ranks
- circular form state
- pending queue display
- direct-publish admin flow
- office submit-for-approval flow
- draft save
- pending edit and draft edit prefill
- vessel popup and rank popup
- approval and rejection comment modal

The file mixes create, review, publish, and edit behavior instead of splitting them into focused screens or hooks.

### Draft and pending edit handoff

The draft and pending screens do not navigate with typed state. They write prefill data into `localStorage`, then redirect back into `Officeuser.jsx`.

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

1. fetch notification details
2. store approval context in `localStorage`
3. open vessel popup
4. open comment modal
5. call status update endpoint
6. call vessel email endpoint
7. open rank popup
8. call rank-link endpoint

Approval context keys:

- `approvingNotificationSrNo`
- `approvingNotificationId`
- `approvingNotificationDept`
- `selectedVesselIdsForNotification`

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

`PdfViewer.jsx` fetches the attachment URL, renders the PDF with PDF.js, and only exposes the acknowledge button once the viewer is scrolled to the bottom.

## Permission Model In The Frontend

The ship dashboard uses form/process IDs from auth state. `permissionUtils.js` normalizes mixed `F_` and `PSC_F_` style values and mixed JSON-string or comma-separated storage formats.

The important consequence is that the frontend, not the backend, decides whether most circular actions are visible. Because the backend routes are largely open, this is a presentation guard, not a security boundary.

## API Contract Expectations

The frontend expects several inconsistent response shapes and works around them manually.

- document types, departments, and priorities arrive as tuple arrays such as `[id, name]`
- sub-categories and second sub-categories arrive as objects
- some screens expect `dept` to behave like an integer flag
- other screens expect department UUIDs or department names

This is why many pages build their own name-to-id and id-to-name maps locally.

## Current Risks And Breakpoints

### 1. `Officeuser.jsx` is the module's single point of failure

It is a very large component responsible for almost every office-side state transition. Authoring, review, approval, publish, edit, vessel selection, rank selection, and local storage restoration are all interleaved in one file.

### 2. The frontend still has endpoint mismatches

- Draft submit-after-edit currently posts to `/api/circular/api/drafts/{id}/update/`, but the backend exposes `/api/circular/api/draft/<sr_no>/update/`.
- Approved library has a `send-reminder` button wired to `/api/notifications/{srNo}/send-reminder/`, but the backend only exposes `/send-individual-reminder/`.

Those actions are not just awkward; they are currently wired to routes that do not exist in the backend URL map.

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

### 7. New shell integration is only partial

The circular module lives inside the modern shell, but most of the logic still uses legacy hooks, legacy routes, hard-coded URLs, and ad hoc state transfer.

`circular-header-actions.tsx` also checks `user_type === 'vessel'`, while the legacy circular routes expect `user_type === 'ship'`, so header affordances for ship users can diverge from the route guard model.

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
- Prefer consolidating API calls behind a shared client before changing endpoint contracts.
- Any real refactor should split the office page into at least create, review, and publish/routing concerns before adding new features.
