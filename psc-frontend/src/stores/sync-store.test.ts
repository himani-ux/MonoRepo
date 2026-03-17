/**
 * Tests for Sync Store (Zustand)
 *
 * PRD Reference: PRD.md FEAT-SYNC-001
 * Validation Reference: FRONTEND_GUIDELINES.md Section 4.2
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useSyncStore } from './sync-store';

// ============================================================================
// HELPERS
// ============================================================================

function resetStore() {
  useSyncStore.setState({
    isOnline: true,
    syncInProgress: false,
    lastSyncTime: null,
    pendingChanges: 0,
    conflicts: 0,
    lastSyncError: null,
  });
}

// ============================================================================
// SETUP
// ============================================================================

beforeEach(() => {
  resetStore();
  localStorage.clear();
});

// ============================================================================
// INITIAL STATE
// ============================================================================

describe('sync-store — initial state', () => {
  it('has correct defaults', () => {
    const state = useSyncStore.getState();
    expect(state.isOnline).toBe(true);
    expect(state.syncInProgress).toBe(false);
    expect(state.lastSyncTime).toBeNull();
    expect(state.pendingChanges).toBe(0);
    expect(state.conflicts).toBe(0);
    expect(state.lastSyncError).toBeNull();
  });
});

// ============================================================================
// ACTIONS
// ============================================================================

describe('sync-store — setOnline', () => {
  it('sets online to false', () => {
    useSyncStore.getState().setOnline(false);
    expect(useSyncStore.getState().isOnline).toBe(false);
  });

  it('sets online to true', () => {
    useSyncStore.getState().setOnline(false);
    useSyncStore.getState().setOnline(true);
    expect(useSyncStore.getState().isOnline).toBe(true);
  });
});

describe('sync-store — setSyncInProgress', () => {
  it('sets syncInProgress', () => {
    useSyncStore.getState().setSyncInProgress(true);
    expect(useSyncStore.getState().syncInProgress).toBe(true);
  });
});

describe('sync-store — setLastSyncTime', () => {
  it('sets time and clears error', () => {
    useSyncStore.setState({ lastSyncError: 'old error' });
    useSyncStore.getState().setLastSyncTime('2026-01-01T00:00:00Z');

    const state = useSyncStore.getState();
    expect(state.lastSyncTime).toBe('2026-01-01T00:00:00Z');
    expect(state.lastSyncError).toBeNull();
  });
});

describe('sync-store — pendingChanges', () => {
  it('setPendingChanges sets exact count', () => {
    useSyncStore.getState().setPendingChanges(5);
    expect(useSyncStore.getState().pendingChanges).toBe(5);
  });

  it('incrementPendingChanges adds 1', () => {
    useSyncStore.getState().setPendingChanges(3);
    useSyncStore.getState().incrementPendingChanges();
    expect(useSyncStore.getState().pendingChanges).toBe(4);
  });

  it('decrementPendingChanges subtracts 1', () => {
    useSyncStore.getState().setPendingChanges(3);
    useSyncStore.getState().decrementPendingChanges();
    expect(useSyncStore.getState().pendingChanges).toBe(2);
  });

  it('decrementPendingChanges never goes below 0', () => {
    useSyncStore.getState().setPendingChanges(0);
    useSyncStore.getState().decrementPendingChanges();
    expect(useSyncStore.getState().pendingChanges).toBe(0);
  });
});

describe('sync-store — setConflicts', () => {
  it('sets conflict count', () => {
    useSyncStore.getState().setConflicts(3);
    expect(useSyncStore.getState().conflicts).toBe(3);
  });
});

describe('sync-store — setLastSyncError', () => {
  it('sets error message', () => {
    useSyncStore.getState().setLastSyncError('Connection failed');
    expect(useSyncStore.getState().lastSyncError).toBe('Connection failed');
  });

  it('clears error with null', () => {
    useSyncStore.getState().setLastSyncError('err');
    useSyncStore.getState().setLastSyncError(null);
    expect(useSyncStore.getState().lastSyncError).toBeNull();
  });
});

describe('sync-store — resetSyncState', () => {
  it('clears all sync fields', () => {
    useSyncStore.setState({
      syncInProgress: true,
      lastSyncTime: '2026-01-01',
      pendingChanges: 5,
      conflicts: 2,
      lastSyncError: 'some error',
    });

    useSyncStore.getState().resetSyncState();

    const state = useSyncStore.getState();
    expect(state.syncInProgress).toBe(false);
    expect(state.lastSyncTime).toBeNull();
    expect(state.pendingChanges).toBe(0);
    expect(state.conflicts).toBe(0);
    expect(state.lastSyncError).toBeNull();
  });

  it('preserves isOnline', () => {
    useSyncStore.setState({ isOnline: false });
    useSyncStore.getState().resetSyncState();
    expect(useSyncStore.getState().isOnline).toBe(false);
  });
});
