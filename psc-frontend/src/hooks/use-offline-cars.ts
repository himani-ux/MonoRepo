/**
 * Hook for reading CARs with offline fallback.
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
import { getAllCARs, getCARById } from '@/lib/db/cars';
import { addToSyncQueue, countPendingSyncQueue } from '@/lib/db/sync-queue';
import { registerFileForUpload } from '@/lib/sync/attachment-uploader';
import type { UpdateCARInput } from '@/types';

// ============================================================================
// Offline CAR Queries
// ============================================================================

/**
 * Fetch CARs from IndexedDB when offline.
 * Returns cached CAR list for the given vessel.
 */
export function useOfflineCARs(vesselId?: number) {
  const isOnline = useSyncStore((s) => s.isOnline);

  return useQuery({
    queryKey: ['offline', 'cars', vesselId],
    queryFn: () => getAllCARs(vesselId),
    // Only enable when offline — online uses the regular useCARs hook
    enabled: !isOnline,
    staleTime: Infinity, // IndexedDB data doesn't go stale
    gcTime: Infinity,
  });
}

/**
 * Fetch a single CAR from IndexedDB when offline.
 */
export function useOfflineCAR(id: number) {
  const isOnline = useSyncStore((s) => s.isOnline);

  return useQuery({
    queryKey: ['offline', 'car', id],
    queryFn: () => getCARById(id),
    enabled: !isOnline && id > 0,
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

// ============================================================================
// Offline Mutation Helpers
// ============================================================================

/**
 * Queue a CAR mutation for later sync.
 * Returns functions that queue operations and update pending count.
 */
export function useQueueCARMutation() {
  const { incrementPendingChanges } = useSyncStore();

  const queueUpdate = useCallback(
    async (id: number, data: Partial<UpdateCARInput>) => {
      await addToSyncQueue({
        entity_type: 'CAR',
        entity_id: id,
        operation: 'UPDATE',
        data: data as Record<string, unknown>,
      });
      incrementPendingChanges();
      await _refreshPendingCount();
    },
    [incrementPendingChanges]
  );

  const queueEvidenceUpload = useCallback(
    async (carId: number, evidenceData: Record<string, unknown>) => {
      const clientId = `temp_${Date.now()}`;
      const fileCandidate =
        evidenceData.file ??
        evidenceData.blob ??
        evidenceData.__upload_blob;
      if (typeof Blob !== 'undefined' && fileCandidate instanceof Blob) {
        registerFileForUpload(clientId, fileCandidate);
      }

      await addToSyncQueue({
        entity_type: 'EVIDENCE',
        entity_id: clientId,
        operation: 'CREATE',
        data: { car_id: carId, ...evidenceData },
      });
      incrementPendingChanges();
      await _refreshPendingCount();
    },
    [incrementPendingChanges]
  );

  return { queueUpdate, queueEvidenceUpload };
}

// ============================================================================
// Internal Helpers
// ============================================================================

/** Refresh the pending changes count from IndexedDB. */
async function _refreshPendingCount(): Promise<void> {
  const count = await countPendingSyncQueue();
  useSyncStore.getState().setPendingChanges(count);
}
