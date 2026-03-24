# Frontend Offline and Legacy Bridge

## Path

- `psc-frontend/src/lib/db/`
- `psc-frontend/src/lib/sync/`
- `psc-frontend/src/lib/pwa/`
- `psc-frontend/src/stores/sync-store.ts`
- `psc-frontend/src/routes/sync/page.tsx`
- `psc-frontend/src/routes/orb/page.tsx`
- `psc-frontend/src/routes/circular/page.tsx`
- `psc-frontend/src/legacy/vims-basic/`

## Purpose

This module covers two infrastructure concerns:

- Offline cache, queue, and sync UX for the modern PSC app
- The bridge that mounts the legacy ORB and Circular frontend inside the modern shell

## Owns

- IndexedDB stores for inspections, deficiencies, CARs, sync queue, and master data
- Full sync orchestration and attachment upload coordination
- Persisted sync status and conflict counts
- Sync status page and conflict resolution modal
- Redux provider bridge for legacy pages
- ORB and Circular route mounting inside the React Router tree

## Workflow

1. Modern pages queue mutations into IndexedDB-backed sync queues when needed.
2. `fullSync()` performs push then pull and updates sync state.
3. `/sync` exposes connectivity, queue, storage, and conflict resolution controls.
4. `/orb/*` and `/circular/*` route into the legacy app via `LegacyBasicProvider`.
5. `module-provider.tsx` mirrors modern auth tokens and user metadata into the legacy Redux store.

## Dependencies

- Backend sync APIs
- Zustand sync store
- Legacy Redux store and legacy route trees
- PWA service worker registration

## Notes

- The legacy bridge is an important compatibility layer: the old UI still expects different auth field names and user-type values.
- Offline data lives in IndexedDB, but auth and sync summary state live in localStorage-backed Zustand stores.
