/**
 * Tests for FEAT-SYNC-001/006 sync status surface (SyncStatus component).
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-001, FEAT-SYNC-006
 * Flow Reference: Docs/APP_FLOW.md Section 2.5 (Sync Status screen)
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SyncStatus } from './sync-status';

describe('SyncStatus', () => {
  it('test_feat_sync_001_online_syncing_state_renders_online_connection_and_syncing_message', () => {
    render(
      <SyncStatus
        isOnline
        lastSyncTime="2026-02-08T12:15:00Z"
        syncInProgress
        lastSyncError={null}
      />
    );

    expect(screen.getByText('Connection: Online')).toBeInTheDocument();
    expect(screen.getByText('Syncing...')).toBeInTheDocument();
  });

  it('test_feat_sync_001_offline_without_last_sync_shows_never_synced_message', () => {
    render(
      <SyncStatus
        isOnline={false}
        lastSyncTime={null}
        syncInProgress={false}
        lastSyncError={null}
      />
    );

    expect(screen.getByText('Connection: Offline')).toBeInTheDocument();
    expect(screen.getByText('Last Sync: Never synced')).toBeInTheDocument();
  });

  it('test_feat_sync_006_sync_error_renders_error_banner', () => {
    render(
      <SyncStatus
        isOnline
        lastSyncTime="2026-02-08T12:15:00Z"
        syncInProgress={false}
        lastSyncError="Network timeout while uploading attachments"
      />
    );

    expect(
      screen.getByText('Network timeout while uploading attachments')
    ).toBeInTheDocument();
  });
});
