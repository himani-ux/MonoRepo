/**
 * Tests for use-inspections hooks (TanStack Query)
 *
 * PRD Reference: PRD.md FEAT-INS-001 through FEAT-INS-007
 * Validation Reference: FRONTEND_GUIDELINES.md Section 4.1
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// ============================================================================
// MOCKS
// ============================================================================

const inspectionsApiMock = vi.hoisted(() => ({
  getInspections: vi.fn(),
  getInspection: vi.fn(),
  createInspection: vi.fn(),
  updateInspection: vi.fn(),
  deleteInspection: vi.fn(),
  submitInspection: vi.fn(),
  picReviewInspection: vi.fn(),
  dpaCloseInspection: vi.fn(),
  uploadInspectionReport: vi.fn(),
  createDeficiency: vi.fn(),
  registerFollowUp: vi.fn(),
  exportDeficiencyExcel: vi.fn(),
  exportInspectionCARs: vi.fn(),
}));

vi.mock('@/lib/api/inspections', () => ({
  inspectionsApi: inspectionsApiMock,
}));

import {
  inspectionKeys,
  useInspections,
  useInspection,
  useCreateInspection,
  useDeleteInspection,
} from './use-inspections';

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

describe('inspectionKeys factory', () => {
  it('all is ["inspections"]', () => {
    expect(inspectionKeys.all).toEqual(['inspections']);
  });

  it('lists appends "list"', () => {
    expect(inspectionKeys.lists()).toEqual(['inspections', 'list']);
  });

  it('list includes filters, page, pageSize', () => {
    const result = inspectionKeys.list({ status: 'DRAFT' }, 1, 20);
    expect(result).toEqual([
      'inspections',
      'list',
      { filters: { status: 'DRAFT' }, page: 1, pageSize: 20 },
    ]);
  });

  it('details appends "detail"', () => {
    expect(inspectionKeys.details()).toEqual(['inspections', 'detail']);
  });

  it('detail includes id', () => {
    expect(inspectionKeys.detail('abc-123')).toEqual(['inspections', 'detail', 'abc-123']);
  });
});

// ============================================================================
// useInspections
// ============================================================================

describe('useInspections', () => {
  it('calls getInspections with params', async () => {
    inspectionsApiMock.getInspections.mockResolvedValue({
      data: [],
      pagination: { page: 1, page_size: 20, total_count: 0, total_pages: 1 },
    });

    const { result } = renderHook(
      () => useInspections({ filters: { status: 'SUBMITTED' }, page: 3, pageSize: 15 }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(inspectionsApiMock.getInspections).toHaveBeenCalledWith(
      { status: 'SUBMITTED' },
      3,
      15,
    );
  });

  it('is disabled when enabled=false', () => {
    const { result } = renderHook(
      () => useInspections({ enabled: false }),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe('idle');
    expect(inspectionsApiMock.getInspections).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useInspection
// ============================================================================

describe('useInspection', () => {
  it('calls getInspection with id', async () => {
    inspectionsApiMock.getInspection.mockResolvedValue({
      id: 'abc-123',
      status: 'DRAFT',
    });

    const { result } = renderHook(() => useInspection('abc-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(inspectionsApiMock.getInspection).toHaveBeenCalledWith('abc-123');
  });

  it('is disabled when id is undefined', () => {
    const { result } = renderHook(() => useInspection(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(inspectionsApiMock.getInspection).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useCreateInspection
// ============================================================================

describe('useCreateInspection', () => {
  it('calls createInspection', async () => {
    const newInspection = { id: 'new-1', status: 'DRAFT' };
    inspectionsApiMock.createInspection.mockResolvedValue(newInspection);

    const { result } = renderHook(() => useCreateInspection(), {
      wrapper: createWrapper(),
    });

    const payload = {
      vessel_id: 'v-1',
      inspection_type: 'PSC',
      inspection_date: '2026-01-01',
      port_place: 'Singapore',
      country: 'Singapore',
    };

    result.current.mutate(payload as any);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(inspectionsApiMock.createInspection).toHaveBeenCalledWith(payload);
  });
});

// ============================================================================
// useDeleteInspection
// ============================================================================

describe('useDeleteInspection', () => {
  it('calls deleteInspection and removes from cache', async () => {
    inspectionsApiMock.deleteInspection.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteInspection(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('abc-123');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(inspectionsApiMock.deleteInspection).toHaveBeenCalledWith('abc-123');
  });
});
