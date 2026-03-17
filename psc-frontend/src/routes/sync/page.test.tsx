/**
 * Tests for FEAT-SYNC-001/004/005 route behavior on Sync Status page.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-001, FEAT-SYNC-004, FEAT-SYNC-005
 * Flow Reference: Docs/APP_FLOW.md Section 2.5 (Sync Status)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const syncPageMocks = vi.hoisted(() => {
  const syncStoreState = {
    resetSyncState: vi.fn(),
    setConflicts: vi.fn(),
  };

  const useSyncStore = Object.assign(vi.fn(), {
    getState: vi.fn(() => syncStoreState),
  });

  return {
    useOffline: vi.fn(),
    useAuth: vi.fn(),
    useConflicts: vi.fn(),
    useInvalidateConflicts: vi.fn(),
    useSyncStore,
    syncStoreState,
    fullSync: vi.fn(),
    clearAllStores: vi.fn(),
    resolveConflictAPI: vi.fn(),
    toast: vi.fn(),
  };
});

vi.mock('@/hooks/use-offline', () => ({
  useOffline: () => syncPageMocks.useOffline(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => syncPageMocks.useAuth(),
}));

vi.mock('@/hooks/use-sync', () => ({
  useConflicts: (enabled: boolean) => syncPageMocks.useConflicts(enabled),
  useInvalidateConflicts: () => syncPageMocks.useInvalidateConflicts(),
}));

vi.mock('@/stores/sync-store', () => ({
  useSyncStore: syncPageMocks.useSyncStore,
}));

vi.mock('@/lib/sync/sync-service', () => ({
  fullSync: () => syncPageMocks.fullSync(),
}));

vi.mock('@/lib/db', () => ({
  clearAllStores: () => syncPageMocks.clearAllStores(),
}));

vi.mock('@/lib/api/sync', () => ({
  resolveConflict: (payload: unknown) => syncPageMocks.resolveConflictAPI(payload),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: syncPageMocks.toast }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/components/ui', () => ({
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/shared', () => ({
  ConfirmDialog: ({
    open,
    onConfirm,
  }: {
    open: boolean;
    onConfirm: () => void;
  }) => (open ? <button onClick={onConfirm}>Confirm Clear Data</button> : null),
}));

vi.mock('@/components/sync', () => ({
  SyncStatus: () => <div>Sync Status Card</div>,
  StorageIndicator: () => <div>Storage Indicator</div>,
  PendingChanges: ({ onRetryFailed }: { onRetryFailed?: () => void }) => (
    <button onClick={onRetryFailed}>Trigger Retry Failed</button>
  ),
  ConflictList: ({
    conflicts,
    onResolve,
  }: {
    conflicts: any[];
    onResolve?: (c: any) => void;
  }) => (
    <button onClick={() => onResolve?.(conflicts?.[0])}>Resolve First Conflict</button>
  ),
  ConflictResolutionModal: ({
    open,
    conflict,
    onResolve,
  }: {
    open: boolean;
    conflict: any;
    onResolve?: (
      conflictId: string,
      resolution: 'KEEP_SERVER' | 'KEEP_VESSEL' | 'REOPEN_FOR_MERGE',
      notes?: string
    ) => void;
  }) =>
    open ? (
      <button onClick={() => onResolve?.(conflict?.id, 'KEEP_SERVER', 'resolved')}>
        Submit Resolution
      </button>
    ) : null,
}));

import SyncStatusPage from './page';

describe('SyncStatusPage', () => {
  beforeEach(() => {
    syncPageMocks.useOffline.mockReset();
    syncPageMocks.useAuth.mockReset();
    syncPageMocks.useConflicts.mockReset();
    syncPageMocks.useInvalidateConflicts.mockReset();
    syncPageMocks.useSyncStore.mockReset();
    syncPageMocks.useSyncStore.getState.mockReset();
    syncPageMocks.syncStoreState.resetSyncState.mockReset();
    syncPageMocks.syncStoreState.setConflicts.mockReset();
    syncPageMocks.fullSync.mockReset();
    syncPageMocks.clearAllStores.mockReset();
    syncPageMocks.resolveConflictAPI.mockReset();
    syncPageMocks.toast.mockReset();

    syncPageMocks.useOffline.mockReturnValue({
      isOnline: true,
      lastSyncTime: null,
      syncInProgress: false,
      pendingChanges: 0,
      conflicts: 1,
    });
    syncPageMocks.useAuth.mockReturnValue({
      isOffice: true,
      isDPA: false,
    });
    syncPageMocks.useConflicts.mockReturnValue({
      data: [
        {
          id: 'conf-1',
          entity_type: 'INSPECTION',
          entity_id: 'ins-1',
        },
      ],
    });
    syncPageMocks.useInvalidateConflicts.mockReturnValue(vi.fn());
    syncPageMocks.useSyncStore.mockReturnValue({ lastSyncError: null });
    syncPageMocks.useSyncStore.getState.mockReturnValue(syncPageMocks.syncStoreState);
    syncPageMocks.fullSync.mockResolvedValue({
      pullRecords: 3,
      pushProcessed: 2,
      conflicts: 0,
    });
    syncPageMocks.clearAllStores.mockResolvedValue(undefined);
    syncPageMocks.resolveConflictAPI.mockResolvedValue({});
  });

  it('test_feat_sync_001_offline_sync_now_shows_error_and_skips_sync_call', async () => {
    syncPageMocks.useOffline.mockReturnValue({
      isOnline: false,
      lastSyncTime: null,
      syncInProgress: false,
      pendingChanges: 0,
      conflicts: 0,
    });

    render(<SyncStatusPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Retry Failed' }));

    await waitFor(() => {
      expect(syncPageMocks.fullSync).not.toHaveBeenCalled();
      expect(syncPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Offline',
          variant: 'destructive',
        })
      );
    });
  });

  it('test_feat_sync_001_online_sync_now_calls_full_sync_and_shows_success_toast', async () => {
    const invalidateConflicts = vi.fn();
    syncPageMocks.useInvalidateConflicts.mockReturnValue(invalidateConflicts);

    render(<SyncStatusPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Sync Now' }));

    await waitFor(() => {
      expect(syncPageMocks.fullSync).toHaveBeenCalledTimes(1);
      expect(invalidateConflicts).toHaveBeenCalledTimes(1);
      expect(syncPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Sync Complete',
        })
      );
    });
  });

  it('test_feat_sync_001_clear_data_resets_store_and_shows_confirmation_toast', async () => {
    render(<SyncStatusPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Clear Old Data' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Clear Data' }));

    await waitFor(() => {
      expect(syncPageMocks.clearAllStores).toHaveBeenCalledTimes(1);
      expect(syncPageMocks.syncStoreState.resetSyncState).toHaveBeenCalledTimes(1);
      expect(syncPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Data Cleared',
        })
      );
    });
  });

  it('test_feat_sync_005_conflict_resolution_calls_api_and_updates_conflict_count', async () => {
    const invalidateConflicts = vi.fn();
    syncPageMocks.useInvalidateConflicts.mockReturnValue(invalidateConflicts);
    syncPageMocks.useOffline.mockReturnValue({
      isOnline: true,
      lastSyncTime: null,
      syncInProgress: false,
      pendingChanges: 0,
      conflicts: 1,
    });

    render(<SyncStatusPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Resolve First Conflict' }));
    fireEvent.click(screen.getByRole('button', { name: 'Submit Resolution' }));

    await waitFor(() => {
      expect(syncPageMocks.resolveConflictAPI).toHaveBeenCalledWith({
        conflict_id: 'conf-1',
        resolution: 'KEEP_SERVER',
        notes: 'resolved',
      });
      expect(syncPageMocks.syncStoreState.setConflicts).toHaveBeenCalledWith(0);
      expect(invalidateConflicts).toHaveBeenCalledTimes(1);
      expect(syncPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Conflict Resolved',
        })
      );
    });
  });
});
