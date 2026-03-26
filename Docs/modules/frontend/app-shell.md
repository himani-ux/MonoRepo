# Frontend App Shell

## Path

- `psc-frontend/src/App.tsx`
- `psc-frontend/src/components/layout/`
- `psc-frontend/src/hooks/use-auth.ts`
- `psc-frontend/src/stores/auth-store.ts`
- `psc-frontend/src/lib/api/client.ts`

## Purpose

This module is the modern frontend shell. It bootstraps auth, mounts the route tree, enforces process-based route guards, and provides the shared page layout used by modern PSC screens.

## Owns

- Browser router and route registration
- Auth initialization and protected-route behavior
- Process permission checks per page
- Header, sidebar, bottom navigation, and offline banner
- Axios token injection and refresh logic
- Persisted auth state in Zustand

## Workflow

1. `main.tsx` creates the React Query client and mounts `App`.
2. `AppShell` runs `useAuthInitializer()` once.
3. Stored tokens are validated and refreshed if needed.
4. `AuthGuard` and `PermissionGuard` decide which route can render.
5. `RootLayout` wraps authenticated pages with navigation and offline indicators.

## Dependencies

- `lib/api/auth.ts` and `lib/api/client.ts`
- `stores/auth-store.ts`
- `hooks/use-auth.ts`
- All route modules under `src/routes/`

## Notes

- The modern app shell is also responsible for mounting the embedded legacy modules under `/orb/*` and `/circular/*`.
- Process IDs, not just roles, drive page visibility in the modern UI.
