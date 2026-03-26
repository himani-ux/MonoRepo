# Shared Utilities and Services

## 1. Shared Frontend Utilities

### 1.1 Constants

The frontend centralizes system constants in `lib/utils/constants.ts`.

Important groups:

- API base URL and prefix
- token storage keys
- file upload limits
- validation limits
- pagination limits
- inspection and CAR status enums
- route constants
- role constants
- process IDs and form IDs

### 1.2 Permission IDs

`lib/utils/permission-ids.ts` provides the canonical form IDs and process IDs used by the frontend permission guards.

### 1.3 Formatting Helpers

Common helpers include:

- date formatting
- status badge formatting
- utility class merging
- general string normalization

## 2. Shared Frontend Components

### 2.1 Layout Components

- `RootLayout`
- `Header`
- `Sidebar`
- `BottomNav`
- `PageHeader`

These components provide the global app shell, responsive navigation, offline banner, and user menu.

### 2.2 Shared Feedback Components

- `EmptyState`
- `ErrorState`
- `LoadingSkeleton`
- `ConfirmDialog`
- `StatusBadge`
- `FileUpload`
- `SearchInput`
- `DatePicker`

### 2.3 UI Primitives

The UI layer is built from reusable primitives such as:

- button
- card
- input
- textarea
- select
- checkbox
- dialog
- dropdown menu
- toast
- skeleton

## 3. Feature Components

### 3.1 Inspection Components

- inspection list cards
- inspection detail view
- inspection form
- filters
- deficiency list and detail dialog
- workflow action controls
- follow-up wizard

### 3.2 CAR Components

- CAR list and detail cards
- CAR form
- corrective action list/item
- root-cause section
- evidence section
- evidence upload modal
- physical verification section
- PV create and close modals
- PIC accept, rework, DPA close, and reopen modals
- activity history and audit log views

### 3.3 Sync Components

- sync status card
- storage indicator
- pending changes panel
- conflict list
- conflict resolution modal
- offline banner

### 3.4 Notification Components

- notification list
- notification item
- notification badge

## 4. Shared Hooks and Services

### 4.1 Auth Hooks

- `useAuth`
- `useAuthInitializer`
- `useRequireAuth`

Responsibilities:

- initialize auth state
- expose role and process helpers
- bridge tokens into the request client

### 4.2 Inspection Hooks

- `useInspections`
- `useInspection`
- `useCreateInspection`
- `useUpdateInspection`
- `useDeleteInspection`
- `useSubmitInspection`
- `usePICReviewInspection`
- `useDPACloseInspection`

### 4.3 CAR Hooks

- `useCARs`
- `useCAR`
- `useUpdateCAR`
- `useSubmitCAR`
- `useTransitionCAR`
- `useCARAvailableActions`
- legacy workflow hooks for accept/rework/close/reopen

### 4.4 Sync Hooks

- `useConflicts`
- `useInvalidateConflicts`

### 4.5 Notification Hooks

- `useNotifications`
- `useUnreadCount`
- `useMarkRead`
- `useMarkAllRead`

### 4.6 Dashboard and Master Hooks

- `useDashboard`
- `useMasters`
- `useVesselCrew`

## 5. API Client Services

### 5.1 Shared Axios Client

The primary `apiClient`:

- injects the JWT access token
- auto-refreshes on 401
- retries once after refresh
- logs out and redirects when refresh fails

### 5.2 Auth API

Handles:

- login
- refresh
- logout
- me

### 5.3 Inspection API

Handles:

- inspection CRUD
- inspection workflow
- report upload
- deficiency create
- follow-up
- export actions

### 5.4 CAR API

Handles:

- CAR CRUD
- workflow transitions
- evidence
- corrective actions
- physical verification

### 5.5 Sync API

Handles:

- pull
- push
- upload
- conflict resolution

### 5.6 Reports API

Handles:

- OpenSource import
- checklist preview/export
- deficiency prediction

### 5.7 Settings API

Handles:

- company logo status
- company logo upload

## 6. IndexedDB and Offline Storage

The offline store is used for vessel-side persistence and sync queueing.

Primary responsibilities:

- store pending inspections and CAR mutations
- keep an upload queue for evidence files
- maintain local sync metadata
- support conflict resolution after reconnect

## 7. Legacy Module Services

Legacy Circular and ORB maintain their own older service layers under `legacy/vims-basic`.

Key integration behavior:

- Redux auth bridge receives the modern token/user state
- legacy components continue to call legacy APIs
- the modern shell only supplies the authenticated context and navigation frame

