/**
 * Tests for FEAT-INS-010: View Inspection List
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Inspection List)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const inspectionListMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  onClearFilters: vi.fn(),
  onPageChange: vi.fn(),
  useInspections: vi.fn(),
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

vi.mock('react-router-dom', () => ({
  useNavigate: () => inspectionListMocks.navigate,
}));

vi.mock('@/hooks/use-inspections', () => ({
  useInspections: (...args: unknown[]) => inspectionListMocks.useInspections(...args),
}));

vi.mock('./inspection-card', () => ({
  InspectionCard: (props: any) => (
    <div data-testid="inspection-card">
      {props.vesselName} | {props.deficiencyCount}/{props.openDeficiencyCount}
    </div>
  ),
}));

import { InspectionList } from './inspection-list';

describe('InspectionList', () => {
  beforeEach(() => {
    inspectionListMocks.navigate.mockReset();
    inspectionListMocks.onClearFilters.mockReset();
    inspectionListMocks.onPageChange.mockReset();
    inspectionListMocks.useInspections.mockReset();
    inspectionListMocks.refetch.mockReset();

    inspectionListMocks.hookState = {
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      refetch: inspectionListMocks.refetch,
    };
    inspectionListMocks.useInspections.mockImplementation(() => inspectionListMocks.hookState);
  });

  it('test_feat_ins_010_loading_state_shows_skeleton_cards', () => {
    inspectionListMocks.hookState.isLoading = true;

    const { container } = render(
      <InspectionList
        filters={{}}
        onClearFilters={inspectionListMocks.onClearFilters}
        page={1}
        onPageChange={inspectionListMocks.onPageChange}
      />
    );

    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
    expect(screen.queryByTestId('inspection-card')).not.toBeInTheDocument();
  });

  it('test_feat_ins_010_error_state_shows_retry_and_calls_refetch', () => {
    inspectionListMocks.hookState.isError = true;
    inspectionListMocks.hookState.error = new Error('Server unavailable');

    render(
      <InspectionList
        filters={{}}
        onClearFilters={inspectionListMocks.onClearFilters}
        page={1}
        onPageChange={inspectionListMocks.onPageChange}
      />
    );

    expect(screen.getByText('Failed to load inspections')).toBeInTheDocument();
    expect(screen.getByText('Server unavailable')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(inspectionListMocks.refetch).toHaveBeenCalledTimes(1);
  });

  it('test_feat_ins_010_empty_state_without_filters_allows_create_first_inspection', () => {
    inspectionListMocks.hookState.data = {
      data: [],
      pagination: { page: 1, total_pages: 1, total_count: 0, page_size: 20 },
    };

    render(
      <InspectionList
        filters={{}}
        onClearFilters={inspectionListMocks.onClearFilters}
        page={1}
        onPageChange={inspectionListMocks.onPageChange}
      />
    );

    expect(screen.getByText('No inspections recorded yet')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Create First Inspection' }));
    expect(inspectionListMocks.navigate).toHaveBeenCalledWith('/inspections/new');
  });

  it('test_feat_ins_010_empty_state_with_active_filters_allows_clear_filters', () => {
    inspectionListMocks.hookState.data = {
      data: [],
      pagination: { page: 1, total_pages: 1, total_count: 0, page_size: 20 },
    };

    render(
      <InspectionList
        filters={{ status: 'DRAFT' as any }}
        onClearFilters={inspectionListMocks.onClearFilters}
        page={1}
        onPageChange={inspectionListMocks.onPageChange}
      />
    );

    expect(screen.getByText('No inspections found')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Clear Filters' }));
    expect(inspectionListMocks.onClearFilters).toHaveBeenCalledTimes(1);
  });

  it('test_feat_ins_010_happy_path_renders_cards_results_count_and_load_more', () => {
    inspectionListMocks.hookState.data = {
      data: [
        {
          id: 101,
          vessel_name: 'MV Test Vessel',
          inspection_type: 'PSC',
          psc_subtype: 'INITIAL',
          inspection_date: '2026-02-01',
          port: 'Singapore',
          port_state: 'SG',
          mou_code: 'TOKYO',
          is_detention: false,
          status: 'SUBMITTED',
          deficiency_count: 3,
          open_deficiency_count: 2,
        },
      ],
      pagination: { page: 1, total_pages: 2, total_count: 5, page_size: 20 },
    };

    render(
      <InspectionList
        filters={{}}
        onClearFilters={inspectionListMocks.onClearFilters}
        page={1}
        onPageChange={inspectionListMocks.onPageChange}
      />
    );

    expect(screen.getByTestId('inspection-card')).toHaveTextContent('MV Test Vessel');
    expect(screen.getByText('Showing 1 of 5 inspections')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Load More' }));
    expect(inspectionListMocks.onPageChange).toHaveBeenCalledWith(2);
  });

  it('test_feat_ins_010_fetching_state_disables_load_more_button', () => {
    inspectionListMocks.hookState.isFetching = true;
    inspectionListMocks.hookState.data = {
      data: [
        {
          id: 102,
          vessel_name: 'MV Fetching',
          inspection_type: 'RS',
          psc_subtype: null,
          inspection_date: '2026-02-02',
          port: 'Rotterdam',
          port_state: 'NL',
          mou_code: null,
          is_detention: false,
          status: 'DRAFT',
          deficiency_count: 1,
          open_deficiency_count: 1,
        },
      ],
      pagination: { page: 1, total_pages: 3, total_count: 25, page_size: 20 },
    };

    render(
      <InspectionList
        filters={{}}
        onClearFilters={inspectionListMocks.onClearFilters}
        page={1}
        onPageChange={inspectionListMocks.onPageChange}
      />
    );

    const button = screen.getByRole('button', { name: 'Loading...' });
    expect(button).toBeDisabled();
  });

  it('passes_detention_and_date_filters_to_inspection_query_hook', () => {
    inspectionListMocks.hookState.data = {
      data: [],
      pagination: { page: 1, total_pages: 1, total_count: 0, page_size: 20 },
    };

    render(
      <InspectionList
        filters={{ is_detention: true, date_from: '2023-02-12' }}
        onClearFilters={inspectionListMocks.onClearFilters}
        page={1}
        onPageChange={inspectionListMocks.onPageChange}
      />
    );

    expect(inspectionListMocks.useInspections).toHaveBeenCalledWith(
      expect.objectContaining({
        filters: { is_detention: true, date_from: '2023-02-12' },
        page: 1,
      })
    );
  });
});
