/**
 * Tests for FEAT-CAR-009: View CAR List (CARList component behavior)
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-009
 * Flow Reference: Docs/APP_FLOW.md Section 2.3 (CAR List)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const carListMocks = vi.hoisted(() => ({
  onClearFilters: vi.fn(),
  onPageChange: vi.fn(),
  onQuickClosePV: vi.fn(),
  useCARs: vi.fn(),
  refetch: vi.fn(),
  hookState: {
    data: undefined as any,
    isLoading: false,
    isFetching: false,
    isError: false,
    error: null as Error | null,
    refetch: vi.fn(),
  },
}));

vi.mock('@/hooks/use-cars', () => ({
  useCARs: (...args: unknown[]) => carListMocks.useCARs(...args),
}));

vi.mock('./car-card', () => ({
  CARCard: (props: any) => (
    <div data-testid={`car-card-${props.id}`}>
      {props.carNumber}|overdue:{String(props.isOverdue)}|missing:{String(props.hasMissingEvidence)}
    </div>
  ),
}));

import { CARList } from './car-list';

describe('CARList', () => {
  beforeEach(() => {
    carListMocks.onClearFilters.mockReset();
    carListMocks.onPageChange.mockReset();
    carListMocks.onQuickClosePV.mockReset();
    carListMocks.useCARs.mockReset();
    carListMocks.refetch.mockReset();
    carListMocks.hookState = {
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      refetch: carListMocks.refetch,
    };
    carListMocks.useCARs.mockImplementation(() => carListMocks.hookState);
  });

  it('test_feat_car_009_loading_state_shows_skeleton_cards', () => {
    carListMocks.hookState.isLoading = true;

    const { container } = render(
      <CARList
        filters={{}}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
      />
    );

    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
  });

  it('test_feat_car_009_error_state_shows_retry_and_calls_refetch', () => {
    carListMocks.hookState.isError = true;
    carListMocks.hookState.error = new Error('CAR endpoint failed');

    render(
      <CARList
        filters={{}}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
      />
    );

    expect(screen.getByText('Failed to load CARs')).toBeInTheDocument();
    expect(screen.getByText('CAR endpoint failed')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(carListMocks.refetch).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_009_empty_state_without_filters_shows_no_cars_message', () => {
    carListMocks.hookState.data = {
      data: [],
      pagination: { page: 1, total_pages: 1, total_count: 0, page_size: 20 },
    };

    render(
      <CARList
        filters={{}}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
      />
    );

    expect(screen.getByText('No CARs found')).toBeInTheDocument();
  });

  it('test_feat_car_009_empty_state_with_filters_shows_clear_filters_action', () => {
    carListMocks.hookState.data = {
      data: [],
      pagination: { page: 1, total_pages: 1, total_count: 0, page_size: 20 },
    };

    render(
      <CARList
        filters={{ status: 'SUBMITTED' as any }}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
      />
    );

    expect(screen.getByText('No CARs found')).toBeInTheDocument();
    expect(screen.getByText('No CARs match your current filter criteria.')).toBeInTheDocument();
    expect(screen.queryByText('No inspections found')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Clear Filters' }));
    expect(carListMocks.onClearFilters).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_009_happy_path_renders_cards_results_count_and_load_more', () => {
    carListMocks.hookState.data = {
      data: [
        {
          id: 1,
          car_number: 'PSC-2026-001',
          def_code: '10101',
          deficiency_description: 'Expired cert',
          vessel_name: 'MV Atlas',
          status: 'SUBMITTED',
          target_date: '2099-01-01',
          before_evidence_count: 1,
          after_evidence_count: 1,
          inspection_type: 'PSC',
        },
      ],
      pagination: { page: 1, total_pages: 2, total_count: 10, page_size: 20 },
    };

    render(
      <CARList
        filters={{}}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
      />
    );

    expect(screen.getByTestId('car-card-1')).toHaveTextContent('PSC-2026-001');
    expect(screen.getByText('Showing 1 of 10 CARs')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Load More' }));
    expect(carListMocks.onPageChange).toHaveBeenCalledWith(2);
  });

  it('test_feat_car_009_computes_overdue_and_missing_evidence_flags_per_row', () => {
    carListMocks.hookState.data = {
      data: [
        {
          id: 10,
          car_number: 'PSC-2026-010',
          def_code: '10101',
          deficiency_description: 'A',
          vessel_name: 'MV One',
          status: 'SUBMITTED',
          target_date: '2000-01-01',
          before_evidence_count: 0,
          after_evidence_count: 1,
          inspection_type: 'PSC',
        },
        {
          id: 11,
          car_number: 'PSC-2026-011',
          def_code: '10102',
          deficiency_description: 'B',
          vessel_name: 'MV Two',
          status: 'DPA_CLOSED',
          target_date: '2000-01-01',
          before_evidence_count: 1,
          after_evidence_count: 1,
          inspection_type: 'PSC',
        },
      ],
      pagination: { page: 1, total_pages: 1, total_count: 2, page_size: 20 },
    };

    render(
      <CARList
        filters={{}}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
      />
    );

    expect(screen.getByTestId('car-card-10')).toHaveTextContent('overdue:true');
    expect(screen.getByTestId('car-card-10')).toHaveTextContent('missing:true');
    expect(screen.getByTestId('car-card-11')).toHaveTextContent('overdue:false');
    expect(screen.getByTestId('car-card-11')).toHaveTextContent('missing:false');
  });

  it('passes_overdue_filter_to_car_query_hook', () => {
    carListMocks.hookState.data = {
      data: [],
      pagination: { page: 1, total_pages: 1, total_count: 0, page_size: 20 },
    };

    render(
      <CARList
        filters={{ is_overdue: true }}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
      />
    );

    expect(carListMocks.useCARs).toHaveBeenCalledWith(
      expect.objectContaining({
        filters: { is_overdue: true },
        page: 1,
      })
    );
  });

  it('test_feat_car_009_pv_due_row_shows_quick_close_action_when_enabled', () => {
    carListMocks.hookState.data = {
      data: [
        {
          id: 21,
          car_number: 'PSC-2026-021',
          def_code: '11001',
          deficiency_description: 'PV pending',
          vessel_name: 'MV Due',
          status: 'CLOSED',
          target_date: '2099-01-01',
          before_evidence_count: 1,
          after_evidence_count: 1,
          pv_due: true,
          inspection_type: 'PSC',
        },
      ],
      pagination: { page: 1, total_pages: 1, total_count: 1, page_size: 20 },
    };

    render(
      <CARList
        filters={{ pv_due: true }}
        onClearFilters={carListMocks.onClearFilters}
        page={1}
        onPageChange={carListMocks.onPageChange}
        canQuickClosePV
        onQuickClosePV={carListMocks.onQuickClosePV}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Close Verification' }));
    expect(carListMocks.onQuickClosePV).toHaveBeenCalledWith(21);
  });
});
