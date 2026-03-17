/**
 * Tests for FEAT-SYNC-001 and FEAT-SYNC-006 sync orchestration.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-001, FEAT-SYNC-006
 * Validation Reference: Docs/VALIDATION_RULES.md Sections 11.3, 11.4
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';

const syncServiceMocks = vi.hoisted(() => {
  const syncState = {
    syncInProgress: false,
    setLastSyncTime: vi.fn(),
    setPendingChanges: vi.fn(),
    setConflicts: vi.fn(),
    setSyncInProgress: vi.fn(),
    setLastSyncError: vi.fn(),
  };

  const authState = {
    user: { vessel_id: '11111111-1111-1111-1111-111111111111' },
  };

  return {
    syncState,
    authState,
    pullChanges: vi.fn(),
    pushChanges: vi.fn(),
    bulkPutInspections: vi.fn(),
    removeInspection: vi.fn(),
    bulkPutDeficiencies: vi.fn(),
    removeDeficiency: vi.fn(),
    bulkPutCARs: vi.fn(),
    removeCAR: vi.fn(),
    getRetryableSyncQueue: vi.fn(),
    updateSyncQueueItem: vi.fn(),
    clearCompletedFromQueue: vi.fn(),
    countPendingSyncQueue: vi.fn(),
    isStorageNearlyFull: vi.fn(),
    uploadAttachments: vi.fn(),
    registerFileForUpload: vi.fn(),
    bulkPutMasterData: vi.fn(),
  };
});

vi.mock('@/stores/sync-store', () => ({
  useSyncStore: {
    getState: () => syncServiceMocks.syncState,
  },
}));

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: {
    getState: () => syncServiceMocks.authState,
  },
}));

vi.mock('@/lib/api/sync', () => ({
  pullChanges: syncServiceMocks.pullChanges,
  pushChanges: syncServiceMocks.pushChanges,
}));

vi.mock('@/lib/db/inspections', () => ({
  bulkPutInspections: syncServiceMocks.bulkPutInspections,
  removeInspection: syncServiceMocks.removeInspection,
  bulkPutDeficiencies: syncServiceMocks.bulkPutDeficiencies,
  removeDeficiency: syncServiceMocks.removeDeficiency,
}));

vi.mock('@/lib/db/cars', () => ({
  bulkPutCARs: syncServiceMocks.bulkPutCARs,
  removeCAR: syncServiceMocks.removeCAR,
}));

vi.mock('@/lib/db/sync-queue', () => ({
  getRetryableSyncQueue: syncServiceMocks.getRetryableSyncQueue,
  updateSyncQueueItem: syncServiceMocks.updateSyncQueueItem,
  clearCompletedFromQueue: syncServiceMocks.clearCompletedFromQueue,
  countPendingSyncQueue: syncServiceMocks.countPendingSyncQueue,
}));

vi.mock('@/lib/db', () => ({
  isStorageNearlyFull: syncServiceMocks.isStorageNearlyFull,
}));

vi.mock('@/lib/db/masters', () => ({
  bulkPutMasterData: syncServiceMocks.bulkPutMasterData,
}));

vi.mock('./attachment-uploader', () => ({
  uploadAttachments: syncServiceMocks.uploadAttachments,
  registerFileForUpload: syncServiceMocks.registerFileForUpload,
}));

import { pullFromServer, pushToServer } from './sync-service';

describe('sync-service', () => {
  beforeEach(() => {
    localStorage.clear();
    syncServiceMocks.pullChanges.mockReset();
    syncServiceMocks.pushChanges.mockReset();
    syncServiceMocks.bulkPutInspections.mockReset();
    syncServiceMocks.removeInspection.mockReset();
    syncServiceMocks.bulkPutDeficiencies.mockReset();
    syncServiceMocks.removeDeficiency.mockReset();
    syncServiceMocks.bulkPutCARs.mockReset();
    syncServiceMocks.removeCAR.mockReset();
    syncServiceMocks.getRetryableSyncQueue.mockReset();
    syncServiceMocks.updateSyncQueueItem.mockReset();
    syncServiceMocks.clearCompletedFromQueue.mockReset();
    syncServiceMocks.countPendingSyncQueue.mockReset();
    syncServiceMocks.isStorageNearlyFull.mockReset();
    syncServiceMocks.uploadAttachments.mockReset();
    syncServiceMocks.registerFileForUpload.mockReset();
    syncServiceMocks.bulkPutMasterData.mockReset();

    syncServiceMocks.syncState.syncInProgress = false;
    syncServiceMocks.syncState.setLastSyncTime.mockReset();
    syncServiceMocks.syncState.setPendingChanges.mockReset();
    syncServiceMocks.syncState.setConflicts.mockReset();
    syncServiceMocks.syncState.setSyncInProgress.mockReset();
    syncServiceMocks.syncState.setLastSyncError.mockReset();

    syncServiceMocks.authState.user = {
      vessel_id: '11111111-1111-1111-1111-111111111111',
    };
  });

  it('test_feat_sync_001_validation_blocks_pull_when_offline_storage_is_nearly_full', async () => {
    syncServiceMocks.isStorageNearlyFull.mockResolvedValue(true);

    await expect(pullFromServer()).rejects.toThrow(
      'Storage nearly full (<10MB remaining). Free space before syncing.'
    );
    expect(syncServiceMocks.pullChanges).not.toHaveBeenCalled();
  });

  it('test_feat_sync_001_happy_path_pull_merges_active_records_and_removes_deleted_records', async () => {
    syncServiceMocks.isStorageNearlyFull.mockResolvedValue(false);
    syncServiceMocks.pullChanges.mockResolvedValue({
      data: {
        inspections: [
          { id: 1, is_deleted: false },
          { id: 2, is_deleted: true },
        ],
        inspection_reports: [],
        deficiencies: [
          { id: 10, is_deleted: false },
          { id: 11, is_deleted: true },
        ],
        cars: [
          { id: 100, is_deleted: false },
          { id: 101, is_deleted: true },
        ],
        corrective_actions: [{ id: 1000 }],
        evidence_metadata: [{ id: 2000 }],
        activity_history: [{ id: 3000 }],
      },
      sync_token: 'sync-token-1',
      server_version: 42,
    });

    const result = await pullFromServer();

    expect(syncServiceMocks.bulkPutInspections).toHaveBeenCalledWith([{ id: 1, is_deleted: false }]);
    expect(syncServiceMocks.removeInspection).toHaveBeenCalledWith(2);
    expect(syncServiceMocks.bulkPutDeficiencies).toHaveBeenCalledWith([{ id: 10, is_deleted: false }]);
    expect(syncServiceMocks.removeDeficiency).toHaveBeenCalledWith(11);
    expect(syncServiceMocks.bulkPutCARs).toHaveBeenCalledWith([{ id: 100, is_deleted: false }]);
    expect(syncServiceMocks.removeCAR).toHaveBeenCalledWith(101);
    expect(syncServiceMocks.syncState.setLastSyncTime).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('sync-token')).toBe('sync-token-1');
    expect(localStorage.getItem('sync-server-version')).toBe('42');
    expect(result.recordCount).toBe(9);
  });

  it('test_feat_sync_001_gap_pull_should_persist_master_data_bucket_to_indexeddb', async () => {
    syncServiceMocks.isStorageNearlyFull.mockResolvedValue(false);
    syncServiceMocks.pullChanges.mockResolvedValue({
      data: {
        inspections: [],
        inspection_reports: [],
        deficiencies: [],
        cars: [],
        corrective_actions: [],
        evidence_metadata: [],
        activity_history: [],
        masters: {
          def_codes: [{ code: '001' }],
          action_codes: [{ code: '10' }],
          mou: [{ id: 'mou-1' }],
          clc_items: [{ id: 'clc-1' }],
        },
      },
      sync_token: 'sync-token-2',
      server_version: 50,
    });

    await pullFromServer();

    expect(syncServiceMocks.bulkPutMasterData).toHaveBeenCalledWith({
      def_codes: [{ code: '001' }],
      action_codes: [{ code: '10' }],
      mou: [{ id: 'mou-1' }],
      clc_items: [{ id: 'clc-1' }],
    });
  });

  it('test_feat_sync_006_gap_failed_attachment_uploads_should_mark_queue_items_failed_for_retry', async () => {
    syncServiceMocks.getRetryableSyncQueue.mockResolvedValue([
      {
        id: 1,
        entity_type: 'EVIDENCE',
        entity_id: 'temp_1',
        operation: 'CREATE',
        data: {
          car_id: 'car-1',
          evidence_type: 'BEFORE',
          file_name: 'evidence.jpg',
          file_size: 128000,
          sync_version: 1,
        },
        status: 'PENDING',
        attempts: 0,
        last_attempt_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
      },
    ]);
    syncServiceMocks.pushChanges.mockResolvedValue({
      data: {
        sync_id: 'sync-push-1',
        processed: 1,
        failed: 0,
        conflicts: [],
        id_mappings: {},
        attachment_upload_urls: [
          {
            client_id: 'temp_1',
            upload_url: '/api/psc/sync/upload/token/',
            expires_at: new Date(Date.now() + 60_000).toISOString(),
          },
        ],
      },
    });
    syncServiceMocks.uploadAttachments.mockResolvedValue({
      total: 1,
      succeeded: 0,
      failed: 1,
      results: [
        {
          client_id: 'temp_1',
          success: false,
          attempts: 3,
          error: 'Upload failed with status 500',
        },
      ],
    });
    syncServiceMocks.countPendingSyncQueue.mockResolvedValue(1);

    await pushToServer();
    await Promise.resolve();

    expect(syncServiceMocks.updateSyncQueueItem).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ status: 'FAILED' })
    );
  });
});
