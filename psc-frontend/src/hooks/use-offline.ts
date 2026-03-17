/**
 * Hook for detecting online/offline status.
 *
 * Listens to browser online/offline events and updates
 * the sync store. When coming back online after being
 * offline, sets wasOffline flag to trigger auto-sync.
 *
 * Source: FRONTEND_GUIDELINES.md Section 7.2
 * Implements: PRD.md FEAT-SYNC-001
 */

import { useState, useEffect, useCallback } from 'react';
import { useSyncStore } from '@/stores/sync-store';

export interface UseOfflineReturn {
  /** Whether the device currently has internet. */
  isOnline: boolean;

  /** Whether the device was previously offline this session. */
  wasOffline: boolean;

  /** Number of pending changes in the sync queue. */
  pendingChanges: number;

  /** Number of unresolved conflicts. */
  conflicts: number;

  /** Whether a sync is in progress. */
  syncInProgress: boolean;

  /** Last successful sync time (ISO string or null). */
  lastSyncTime: string | null;
}

export function useOffline(): UseOfflineReturn {
  const {
    isOnline,
    setOnline,
    pendingChanges,
    conflicts,
    syncInProgress,
    lastSyncTime,
  } = useSyncStore();

  const [wasOffline, setWasOffline] = useState(false);

  const handleOnline = useCallback(() => {
    setOnline(true);
    // wasOffline stays true so consumers can trigger sync
  }, [setOnline]);

  const handleOffline = useCallback(() => {
    setOnline(false);
    setWasOffline(true);
  }, [setOnline]);

  useEffect(() => {
    // Set initial state
    setOnline(navigator.onLine);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline, setOnline]);

  return {
    isOnline,
    wasOffline,
    pendingChanges,
    conflicts,
    syncInProgress,
    lastSyncTime,
  };
}
