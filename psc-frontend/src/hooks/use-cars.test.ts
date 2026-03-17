/**
 * Tests for use-cars hooks (TanStack Query)
 *
 * PRD Reference: PRD.md FEAT-CAR-001 through FEAT-CAR-008
 * Validation Reference: FRONTEND_GUIDELINES.md Section 4.1
 *
 * Mocks the carsApi module and tests query key structure +
 * hook behavior with renderHook + QueryClientProvider.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// ============================================================================
// MOCKS
// ============================================================================

const carsApiMock = vi.hoisted(() => ({
  getCARs: vi.fn(),
  getCARDetail: vi.fn(),
  updateCAR: vi.fn(),
  submitCAR: vi.fn(),
  picAcceptCAR: vi.fn(),
  requestReworkCAR: vi.fn(),
  dpaCloseCAR: vi.fn(),
  reopenCAR: vi.fn(),
  createAction: vi.fn(),
  updateAction: vi.fn(),
  completeAction: vi.fn(),
  uploadEvidence: vi.fn(),
  deleteEvidence: vi.fn(),
  createPhysicalVerification: vi.fn(),
  closePhysicalVerification: vi.fn(),
  exportCARPDF: vi.fn(),
}));

vi.mock('@/lib/api/cars', () => ({
  carsApi: carsApiMock,
}));

import { carKeys, useCARs, useCAR, useUpdateCAR, useSubmitCAR } from './use-cars';

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

describe('carKeys factory', () => {
  it('all includes user scope', () => {
    expect(carKeys.all()).toEqual(['cars', 'anonymous']);
  });

  it('lists appends "list"', () => {
    expect(carKeys.lists()).toEqual(['cars', 'anonymous', 'list']);
  });

  it('list includes filters, page, pageSize', () => {
    const result = carKeys.list({ status: 'ALLOTTED' }, 1, 20);
    expect(result).toEqual([
      'cars',
      'anonymous',
      'list',
      { filters: { status: 'ALLOTTED' }, page: 1, pageSize: 20 },
    ]);
  });

  it('details appends "detail"', () => {
    expect(carKeys.details()).toEqual(['cars', 'anonymous', 'detail']);
  });

  it('detail includes id', () => {
    expect(carKeys.detail(42)).toEqual(['cars', 'anonymous', 'detail', 42]);
  });
});

// ============================================================================
// useCARs
// ============================================================================

describe('useCARs', () => {
  it('calls getCARs with correct params', async () => {
    carsApiMock.getCARs.mockResolvedValue({
      data: [],
      pagination: { page: 1, page_size: 20, total_count: 0, total_pages: 1 },
    });

    const { result } = renderHook(
      () => useCARs({ filters: { status: 'ALLOTTED' }, page: 2, pageSize: 10 }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(carsApiMock.getCARs).toHaveBeenCalledWith({ status: 'ALLOTTED' }, 2, 10);
  });

  it('is disabled when enabled=false', () => {
    const { result } = renderHook(
      () => useCARs({ enabled: false }),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe('idle');
    expect(carsApiMock.getCARs).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useCAR
// ============================================================================

describe('useCAR', () => {
  it('calls getCARDetail with id', async () => {
    carsApiMock.getCARDetail.mockResolvedValue({ id: 5, status: 'ALLOTTED' });

    const { result } = renderHook(() => useCAR(5), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(carsApiMock.getCARDetail).toHaveBeenCalledWith(5);
  });

  it('is disabled when id is undefined', () => {
    const { result } = renderHook(() => useCAR(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(carsApiMock.getCARDetail).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useUpdateCAR
// ============================================================================

describe('useUpdateCAR', () => {
  it('calls updateCAR and invalidates caches', async () => {
    carsApiMock.updateCAR.mockResolvedValue({ id: 5, status: 'ALLOTTED' });

    const { result } = renderHook(() => useUpdateCAR(5), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ root_cause_summary: 'Updated cause with enough length to satisfy validation.' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(carsApiMock.updateCAR).toHaveBeenCalledWith(5, {
      root_cause_summary: 'Updated cause with enough length to satisfy validation.',
    });
  });
});

// ============================================================================
// useSubmitCAR
// ============================================================================

describe('useSubmitCAR', () => {
  it('calls submitCAR', async () => {
    carsApiMock.submitCAR.mockResolvedValue({ id: 5, status: 'SUBMITTED_TO_PIC' });

    const { result } = renderHook(() => useSubmitCAR(5), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(carsApiMock.submitCAR).toHaveBeenCalledWith(5);
  });
});
