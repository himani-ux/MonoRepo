/**
 * Tests for FEAT-SYNC-006 and FEAT-SYNC-001 sync status UI sections.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-001, FEAT-SYNC-006
 * Flow Reference: Docs/APP_FLOW.md Section 2.5 (Sync Status screen)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { PendingChanges } from './pending-changes';

const syncQueueMocks = vi.hoisted(() => ({
  getPendingSyncQueue: vi.fn(),
  getFailedSyncQueue: vi.fn(),
}));

vi.mock('@/lib/db/sync-queue', () => ({
  getPendingSyncQueue: syncQueueMocks.getPendingSyncQueue,
  getFailedSyncQueue: syncQueueMocks.getFailedSyncQueue,
}));

describe('PendingChanges', () => {
  beforeEach(() => {
    syncQueueMocks.getPendingSyncQueue.mockReset();
    syncQueueMocks.getFailedSyncQueue.mockReset();
  });

  it('test_feat_sync_006_happy_path_failed_uploads_section_renders_retry_button_and_error_details', async () => {
    syncQueueMocks.getPendingSyncQueue.mockResolvedValue([]);
    syncQueueMocks.getFailedSyncQueue.mockResolvedValue([
      {
        id: '1',
        entity_type: 'EVIDENCE',
        entity_id: 'temp_1',
        operation: 'CREATE',
        data: {},
        status: 'FAILED',
        attempts: 3,
        last_attempt_at: new Date().toISOString(),
        error_message: 'Network error',
        created_at: new Date().toISOString(),
      },
    ]);
    const onRetryFailed = vi.fn();

    render(
      <PendingChanges
        pendingCount={1}
        onRetryFailed={onRetryFailed}
        retryInProgress={false}
      />
    );

    expect(await screen.findByText('Failed Uploads')).toBeInTheDocument();
    expect(await screen.findByText('1 upload failed')).toBeInTheDocument();
    expect(screen.getByText(/Network error/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetryFailed).toHaveBeenCalledTimes(1);
  });

  it('test_feat_sync_001_happy_path_when_no_pending_or_failed_items_shows_all_changes_synced_state', async () => {
    syncQueueMocks.getPendingSyncQueue.mockResolvedValue([]);
    syncQueueMocks.getFailedSyncQueue.mockResolvedValue([]);

    render(<PendingChanges pendingCount={0} retryInProgress={false} />);

    expect(await screen.findByText('All changes synced')).toBeInTheDocument();
    expect(screen.queryByText('Failed Uploads')).not.toBeInTheDocument();
  });
});

