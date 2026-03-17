/**
 * Hook for reading inspections with offline fallback.
 *
 * When online: uses TanStack Query (server data).
 * When offline: reads from IndexedDB cache.
 * Mutations while offline are queued to the sync queue.
 *
 * Source: FRONTEND_GUIDELINES.md Section 7.2
 * Implements: PRD.md FEAT-SYNC-001
 */

import { useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSyncStore } from '@/stores/sync-store';
import {
  getAllInspections,
  getAllDeficiencies,
  getInspectionById,
} from '@/lib/db/inspections';
import { addToSyncQueue } from '@/lib/db/sync-queue';
import { countPendingSyncQueue } from '@/lib/db/sync-queue';
import type { Inspection, Deficiency } from '@/types';

// ============================================================================
// Offline Inspection Queries
// ============================================================================

/**
 * Fetch inspections from IndexedDB when offline.
 * Returns cached inspection list for the given vessel.
 */
export function useOfflineInspections(vesselId?: number) {
  const isOnline = useSyncStore((s) => s.isOnline);

  return useQuery({
    queryKey: ['offline', 'inspections', vesselId],
    queryFn: () => getAllInspections(vesselId),
    // Only enable when offline — online uses the regular useInspections hook
    enabled: !isOnline,
    staleTime: Infinity, // IndexedDB data doesn't go stale
    gcTime: Infinity,
  });
}

/**
 * Fetch deficiencies from IndexedDB when offline.
 * Optionally filtered by inspection ID.
 */
export function useOfflineDeficiencies(inspectionId?: number) {
  const isOnline = useSyncStore((s) => s.isOnline);

  return useQuery({
    queryKey: ['offline', 'deficiencies', inspectionId],
    queryFn: () => getAllDeficiencies(inspectionId),
    enabled: !isOnline,
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

/**
 * Fetch a single inspection from IndexedDB when offline.
 */
export function useOfflineInspection(id: number) {
  const isOnline = useSyncStore((s) => s.isOnline);

  return useQuery({
    queryKey: ['offline', 'inspection', id],
    queryFn: () => getInspectionById(id),
    enabled: !isOnline && id > 0,
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

// ============================================================================
// Offline Mutation Helpers
// ============================================================================

/**
 * Queue an inspection mutation for later sync.
 * Returns a function that queues the operation and updates pending count.
 */
export function useQueueInspectionMutation() {
  const { incrementPendingChanges } = useSyncStore();

  const queueCreate = useCallback(
    async (data: Partial<Inspection>) => {
      await addToSyncQueue({
        entity_type: 'INSPECTION',
        entity_id: data.id ?? `temp_${Date.now()}`,
        operation: 'CREATE',
        data: data as Record<string, unknown>,
      });
      incrementPendingChanges();
      await _refreshPendingCount();
    },
    [incrementPendingChanges]
  );

  const queueUpdate = useCallback(
    async (id: number, data: Partial<Inspection>) => {
      await addToSyncQueue({
        entity_type: 'INSPECTION',
        entity_id: id,
        operation: 'UPDATE',
        data: data as Record<string, unknown>,
      });
      incrementPendingChanges();
      await _refreshPendingCount();
    },
    [incrementPendingChanges]
  );

  const queueDeficiencyCreate = useCallback(
    async (data: Partial<Deficiency>) => {
      await addToSyncQueue({
        entity_type: 'DEFICIENCY',
        entity_id: data.id ?? `temp_${Date.now()}`,
        operation: 'CREATE',
        data: data as Record<string, unknown>,
      });
      incrementPendingChanges();
      await _refreshPendingCount();
    },
    [incrementPendingChanges]
  );

  return { queueCreate, queueUpdate, queueDeficiencyCreate };
}

// ============================================================================
// Internal Helpers
// ============================================================================

/** Refresh the pending changes count from IndexedDB. */
async function _refreshPendingCount(): Promise<void> {
  const count = await countPendingSyncQueue();
  useSyncStore.getState().setPendingChanges(count);
}
