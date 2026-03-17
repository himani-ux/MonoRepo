/**
 * Tests for FEAT-CAR-009 route behavior on CAR list page.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-009
 * Flow Reference: Docs/APP_FLOW.md Section 2.3 (CAR List)
 */

import { fireEvent, render, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const carListRouteMocks = vi.hoisted(() => ({
  useSearchParams: vi.fn(),
  setSearchParams: vi.fn(),
  filtersProps: null as any,
  listProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useSearchParams: () => carListRouteMocks.useSearchParams(),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/components/car', () => ({
  CARFilters: (props: any) => {
    carListRouteMocks.filtersProps = props;
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            props.onFiltersChange({ status: 'SUBMITTED', search: 'PSC-2026-001' })
          }
        >
          Trigger Filter Change
        </button>
      </div>
    );
  },
  CARList: (props: any) => {
    carListRouteMocks.listProps = props;
    return (
      <div>
        <button type="button" onClick={props.onClearFilters}>
          Trigger Clear Filters
        </button>
        <button type="button" onClick={() => props.onPageChange(3)}>
          Trigger Page 3
        </button>
      </div>
    );
  },
}));

import CARListPage from './index';

describe('CARListPage', () => {
  beforeEach(() => {
    carListRouteMocks.useSearchParams.mockReset();
    carListRouteMocks.setSearchParams.mockReset();
    carListRouteMocks.filtersProps = null;
    carListRouteMocks.listProps = null;

    carListRouteMocks.useSearchParams.mockReturnValue([
      new URLSearchParams('status=DRAFT&search=abc'),
      carListRouteMocks.setSearchParams,
    ]);
  });

  it('test_feat_car_009_initial_filters_are_parsed_from_query_params', () => {
    render(<CARListPage />);

    expect(carListRouteMocks.filtersProps.filters).toEqual({
      status: 'DRAFT',
      search: 'abc',
    });
    expect(carListRouteMocks.listProps.filters).toEqual({
      status: 'DRAFT',
      search: 'abc',
    });
    expect(carListRouteMocks.listProps.page).toBe(1);
  });

  it('test_feat_car_009_filter_change_updates_url_and_resets_page_to_one', async () => {
    const { getByRole } = render(<CARListPage />);

    fireEvent.click(getByRole('button', { name: 'Trigger Page 3' }));
    await waitFor(() => {
      expect(carListRouteMocks.listProps.page).toBe(3);
    });

    fireEvent.click(getByRole('button', { name: 'Trigger Filter Change' }));

    await waitFor(() => {
      expect(carListRouteMocks.listProps.page).toBe(1);
    });
    expect(carListRouteMocks.setSearchParams).toHaveBeenCalledWith(
      expect.any(URLSearchParams),
      { replace: true }
    );
    const params = carListRouteMocks.setSearchParams.mock.calls[
      carListRouteMocks.setSearchParams.mock.calls.length - 1
    ]?.[0] as URLSearchParams;
    expect(params.toString()).toBe('status=SUBMITTED&search=PSC-2026-001');
  });

  it('test_feat_car_009_clear_filters_clears_query_and_resets_page', async () => {
    const { getByRole } = render(<CARListPage />);

    fireEvent.click(getByRole('button', { name: 'Trigger Page 3' }));
    await waitFor(() => {
      expect(carListRouteMocks.listProps.page).toBe(3);
    });

    fireEvent.click(getByRole('button', { name: 'Trigger Clear Filters' }));

    await waitFor(() => {
      expect(carListRouteMocks.listProps.page).toBe(1);
      expect(carListRouteMocks.listProps.filters).toEqual({});
    });
    const params = carListRouteMocks.setSearchParams.mock.calls[
      carListRouteMocks.setSearchParams.mock.calls.length - 1
    ]?.[0] as URLSearchParams;
    expect(params.toString()).toBe('');
  });

  it('test_feat_car_009_page_change_updates_current_page_for_list', async () => {
    const { getByRole } = render(<CARListPage />);

    fireEvent.click(getByRole('button', { name: 'Trigger Page 3' }));

    await waitFor(() => {
      expect(carListRouteMocks.listProps.page).toBe(3);
    });
  });

  it('parses_overdue_flag_from_query_params_for_dashboard_navigation', () => {
    carListRouteMocks.useSearchParams.mockReturnValue([
      new URLSearchParams('overdue=true'),
      carListRouteMocks.setSearchParams,
    ]);

    render(<CARListPage />);

    expect(carListRouteMocks.filtersProps.filters).toEqual({
      is_overdue: true,
    });
    expect(carListRouteMocks.listProps.filters).toEqual({
      is_overdue: true,
    });
  });
});
