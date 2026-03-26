# Frontend Overview

## 1. Frontend Architecture

The frontend is a React 18 single-page application built with Vite and TypeScript. It uses a modern PSC shell for the inspection platform and wraps legacy Circular and ORB functionality inside dedicated module routes.

Primary frontend responsibilities:

- route protection and role-aware navigation
- form validation and submission
- dashboard and workflow screens
- offline sync status and conflict management
- legacy module bridging

## 2. Project Structure

```text
psc-frontend/
  src/
    App.tsx
    main.tsx
    routes/
    components/
    hooks/
    lib/
    stores/
    legacy/
```

## 3. App Boot Flow

1. `main.tsx` creates the TanStack Query client.
2. The app is wrapped in `QueryClientProvider`.
3. `App.tsx` initializes auth on load.
4. Auth-protected routes render inside `RootLayout`.
5. The service worker is registered for PWA support.

## 4. Routing Strategy

The application uses React Router with:

- public login route
- authenticated default redirect
- route-based permission guard using process IDs
- lazy-loaded feature routes

Important behavior:

- `/` redirects to `/dashboard` for users with dashboard permission
- otherwise `/` redirects to `/cars`
- legacy modules are only loaded after auth is available

## 5. State Management

### 5.1 TanStack Query

Used for:

- inspections
- CARs
- masters
- notifications
- sync conflicts
- dashboard data
- reports workspace
- settings/company logo

### 5.2 Zustand Stores

Used for:

- auth state
- sync/offline state

### 5.3 Legacy Redux Bridge

Circular and ORB depend on a legacy Redux store. The modern auth store bridges current claims into that legacy store through `LegacyBasicProvider`.

## 6. Authentication and Route Guards

The frontend exposes these auth-related abstractions:

- `useAuth`
- `AuthGuard`
- `PermissionGuard`
- `useRequireAuth`

Permission checks are based on process IDs from the JWT payload, not just on visual navigation state.

## 7. Folder Responsibilities

### 7.1 `components/`

- layout components
- feature cards, lists, forms, and modals
- shared UI primitives
- sync widgets
- notification widgets

### 7.2 `hooks/`

- query hooks and mutations
- auth helpers
- offline helpers
- toast helpers

### 7.3 `lib/`

- API wrappers
- IndexedDB helpers
- validation utilities
- constants
- formatting utilities
- PWA helpers

### 7.4 `legacy/`

- preserved Circular and ORB app shell
- Redux bridge
- legacy components, routes, and utilities

## 8. Frontend Runtime Rules

- Always read auth state before rendering protected screens.
- Always invalidate TanStack Query caches after mutations.
- Never assume a vessel user can see another vessel by navigating directly.
- Preserve the legacy provider wrapper for Circular and ORB routes.
- Keep file upload constraints aligned with backend validation.

