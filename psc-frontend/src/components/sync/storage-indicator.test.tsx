/**
 * Tests for FEAT-SYNC-001 storage usage warning behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-001
 */

import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const storageIndicatorMocks = vi.hoisted(() => ({
  getStorageEstimate: vi.fn(),
}));

vi.mock('@/lib/db', async () => {
  const actual = await vi.importActual<typeof import('@/lib/db')>('@/lib/db');
  return {
    ...actual,
    getStorageEstimate: storageIndicatorMocks.getStorageEstimate,
  };
});

import { STORAGE_LIMIT_BYTES, STORAGE_WARNING_BYTES } from '@/lib/db';
import { StorageIndicator } from './storage-indicator';

describe('StorageIndicator', () => {
  beforeEach(() => {
    storageIndicatorMocks.getStorageEstimate.mockReset();
  });

  it('test_feat_sync_001_warning_shows_when_remaining_storage_below_threshold', async () => {
    storageIndicatorMocks.getStorageEstimate.mockResolvedValue({
      usage: STORAGE_LIMIT_BYTES - STORAGE_WARNING_BYTES + 1024,
      quota: STORAGE_LIMIT_BYTES,
    });

    render(<StorageIndicator />);

    expect(await screen.findByText(/Storage nearly full/i)).toBeInTheDocument();
    expect(
      screen.getByText('Please connect to internet and sync to free up space.')
    ).toBeInTheDocument();
  });

  it('test_feat_sync_001_no_warning_when_storage_has_sufficient_remaining_capacity', async () => {
    storageIndicatorMocks.getStorageEstimate.mockResolvedValue({
      usage: 25 * 1024 * 1024,
      quota: STORAGE_LIMIT_BYTES,
    });

    render(<StorageIndicator />);

    await waitFor(() => {
      expect(screen.getByText(/25\.0 MB \/ 150\.0 MB/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Storage nearly full/i)).not.toBeInTheDocument();
  });
});
