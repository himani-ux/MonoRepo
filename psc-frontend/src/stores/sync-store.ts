/**
 * Zustand store for sync and offline state management.
 *
 * Tracks online/offline status, pending changes count,
 * sync conflicts, and last sync time.
 *
 * Source: FRONTEND_GUIDELINES.md Section 4.2
 * Implements: PRD.md FEAT-SYNC-001
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================================================
// Types
// ============================================================================

interface SyncState {
  /** Whether the device currently has internet connectivity. */
  isOnline: boolean;

  /** Whether a sync operation is currently in progress. */
  syncInProgress: boolean;

  /** Timestamp of the last successful sync. */
  lastSyncTime: string | null;

  /** Number of pending mutations in the sync queue. */
  pendingChanges: number;

  /** Number of unresolved sync conflicts. */
  conflicts: number;

  /** Last sync error message, if any. */
  lastSyncError: string | null;

  // Actions
  setOnline: (isOnline: boolean) => void;
  setSyncInProgress: (inProgress: boolean) => void;
  setLastSyncTime: (time: string) => void;
  setPendingChanges: (count: number) => void;
  incrementPendingChanges: () => void;
  decrementPendingChanges: () => void;
  setConflicts: (count: number) => void;
  setLastSyncError: (error: string | null) => void;
  resetSyncState: () => void;
}

// ============================================================================
// Store
// ============================================================================

export const useSyncStore = create<SyncState>()(
  persist(
    (set) => ({
      // Initial state
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
      syncInProgress: false,
      lastSyncTime: null,
      pendingChanges: 0,
      conflicts: 0,
      lastSyncError: null,

      // Actions
      setOnline: (isOnline) => set({ isOnline }),

      setSyncInProgress: (inProgress) =>
        set({ syncInProgress: inProgress }),

      setLastSyncTime: (time) =>
        set({ lastSyncTime: time, lastSyncError: null }),

      setPendingChanges: (count) => set({ pendingChanges: count }),

      incrementPendingChanges: () =>
        set((state) => ({ pendingChanges: state.pendingChanges + 1 })),

      decrementPendingChanges: () =>
        set((state) => ({
          pendingChanges: Math.max(0, state.pendingChanges - 1),
        })),

      setConflicts: (count) => set({ conflicts: count }),

      setLastSyncError: (error) => set({ lastSyncError: error }),

      resetSyncState: () =>
        set({
          syncInProgress: false,
          lastSyncTime: null,
          pendingChanges: 0,
          conflicts: 0,
          lastSyncError: null,
        }),
    }),
    {
      name: 'sync-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist these across sessions
        lastSyncTime: state.lastSyncTime,
        pendingChanges: state.pendingChanges,
        conflicts: state.conflicts,
      }),
    }
  )
);
