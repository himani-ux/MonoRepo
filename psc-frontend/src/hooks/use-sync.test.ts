/**
 * Tests for use-sync hooks (TanStack Query)
 *
 * PRD Reference: PRD.md FEAT-SYNC-004
 * Validation Reference: FRONTEND_GUIDELINES.md Section 4.1
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// ============================================================================
// MOCKS
// ============================================================================

const syncApiMock = vi.hoisted(() => ({
  getConflicts: vi.fn(),
}));

vi.mock('@/lib/api/sync', () => ({
  getConflicts: syncApiMock.getConflicts,
}));

import { syncKeys, useConflicts, useInvalidateConflicts } from './use-sync';

// ============================================================================
// HELPERS
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

// ============================================================================
// SETUP
// ============================================================================

beforeEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Query Key Factory
// ============================================================================

describe('syncKeys factory', () => {
  it('all is ["sync"]', () => {
    expect(syncKeys.all).toEqual(['sync']);
  });

  it('conflicts appends "conflicts"', () => {
    expect(syncKeys.conflicts()).toEqual(['sync', 'conflicts']);
  });
});

// ============================================================================
// useConflicts
// ============================================================================

describe('useConflicts', () => {
  it('calls getConflicts', async () => {
    syncApiMock.getConflicts.mockResolvedValue([
      { id: 'c-1', entity_type: 'INSPECTION' },
    ]);

    const { result } = renderHook(() => useConflicts(true), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(syncApiMock.getConflicts).toHaveBeenCalled();
  });

  it('is disabled when enabled=false', () => {
    const { result } = renderHook(() => useConflicts(false), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(syncApiMock.getConflicts).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useInvalidateConflicts
// ============================================================================

describe('useInvalidateConflicts', () => {
  it('returns a callable function', () => {
    const { result } = renderHook(() => useInvalidateConflicts(), {
      wrapper: createWrapper(),
    });

    expect(typeof result.current).toBe('function');
  });
});
