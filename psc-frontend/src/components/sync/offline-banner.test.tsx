/**
 * Tests for FEAT-SYNC-001 offline banner behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-001
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { OfflineBanner } from './offline-banner';

describe('OfflineBanner', () => {
  it('test_feat_sync_001_online_state_hides_offline_banner', () => {
    const { container } = render(
      <OfflineBanner isOnline lastSyncTime="2026-02-08T12:15:00Z" />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('test_feat_sync_001_offline_banner_shows_cached_data_message_and_last_sync_when_available', () => {
    render(<OfflineBanner isOnline={false} lastSyncTime="2026-02-08T12:15:00Z" />);

    expect(screen.getByText(/Offline — Showing cached data/)).toBeInTheDocument();
    expect(screen.getByText(/\(Last sync:/)).toBeInTheDocument();
  });

  it('test_feat_sync_001_offline_banner_without_last_sync_omits_last_sync_suffix', () => {
    render(<OfflineBanner isOnline={false} lastSyncTime={null} />);

    expect(screen.getByText(/Offline — Showing cached data/)).toBeInTheDocument();
    expect(screen.queryByText(/\(Last sync:/)).not.toBeInTheDocument();
  });
});
