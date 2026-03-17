/**
 * Tests for FEAT-INS-010 and FEAT-RPT-002 route behavior on Inspection List page.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 * PRD Reference: Docs/PRD.md Section 2.7 - FEAT-RPT-002
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Inspection List)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const inspectionListRouteMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useSearchParams: vi.fn(),
  setSearchParams: vi.fn(),
  exportDeficiencyExcel: vi.fn(),
  toast: vi.fn(),
  filtersProps: null as any,
  listProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => inspectionListRouteMocks.navigate,
  useSearchParams: () => inspectionListRouteMocks.useSearchParams(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: inspectionListRouteMocks.toast }),
}));

vi.mock('@/lib/api/inspections', () => ({
  exportDeficiencyExcel: (...args: unknown[]) =>
    inspectionListRouteMocks.exportDeficiencyExcel(...args),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title, actions }: { title: string; actions?: React.ReactNode }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
}));

vi.mock('@/components/ui', () => ({
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/inspection', () => ({
  InspectionFilters: (props: any) => {
    inspectionListRouteMocks.filtersProps = props;
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            props.onFiltersChange({
              status: 'SUBMITTED',
              inspection_type: 'PSC',
              date_from: '2026-02-01',
              date_to: '2026-02-08',
            })
          }
        >
          Trigger Filter Change
        </button>
      </div>
    );
  },
  InspectionList: (props: any) => {
    inspectionListRouteMocks.listProps = props;
    return (
      <div>
        <button type="button" onClick={props.onClearFilters}>
          Trigger Clear Filters
        </button>
        <button type="button" onClick={() => props.onPageChange(2)}>
          Trigger Page 2
        </button>
      </div>
    );
  },
}));

import InspectionListPage from './index';

describe('InspectionListPage', () => {
  beforeEach(() => {
    inspectionListRouteMocks.navigate.mockReset();
    inspectionListRouteMocks.useSearchParams.mockReset();
    inspectionListRouteMocks.setSearchParams.mockReset();
    inspectionListRouteMocks.exportDeficiencyExcel.mockReset();
    inspectionListRouteMocks.toast.mockReset();
    inspectionListRouteMocks.filtersProps = null;
    inspectionListRouteMocks.listProps = null;

    inspectionListRouteMocks.useSearchParams.mockReturnValue([
      new URLSearchParams('type=PSC&status=SUBMITTED&search=rotterdam'),
      inspectionListRouteMocks.setSearchParams,
    ]);
    inspectionListRouteMocks.exportDeficiencyExcel.mockResolvedValue(new Blob(['ok']));

    Object.defineProperty(globalThis.URL, 'createObjectURL', {
      writable: true,
      value: vi.fn(() => 'blob:mock-url'),
    });
    Object.defineProperty(globalThis.URL, 'revokeObjectURL', {
      writable: true,
      value: vi.fn(() => {}),
    });
  });

  it('test_feat_ins_010_initial_filters_are_parsed_from_query_params', () => {
    render(<InspectionListPage />);

    expect(inspectionListRouteMocks.filtersProps.filters).toEqual({
      inspection_type: 'PSC',
      status: 'SUBMITTED',
      search: 'rotterdam',
    });
    expect(inspectionListRouteMocks.listProps.filters).toEqual({
      inspection_type: 'PSC',
      status: 'SUBMITTED',
      search: 'rotterdam',
    });
    expect(inspectionListRouteMocks.listProps.page).toBe(1);
  });

  it('parses_dashboard_detention_query_filters_and_passes_to_list', () => {
    inspectionListRouteMocks.useSearchParams.mockReturnValue([
      new URLSearchParams('detention=true&date_from=2023-02-12'),
      inspectionListRouteMocks.setSearchParams,
    ]);

    render(<InspectionListPage />);

    expect(inspectionListRouteMocks.filtersProps.filters).toEqual({
      is_detention: true,
      date_from: '2023-02-12',
    });
    expect(inspectionListRouteMocks.listProps.filters).toEqual({
      is_detention: true,
      date_from: '2023-02-12',
    });
  });

  it('test_feat_ins_010_filter_change_updates_url_and_resets_page', async () => {
    const { getByRole } = render(<InspectionListPage />);

    fireEvent.click(getByRole('button', { name: 'Trigger Page 2' }));
    await waitFor(() => {
      expect(inspectionListRouteMocks.listProps.page).toBe(2);
    });

    fireEvent.click(getByRole('button', { name: 'Trigger Filter Change' }));
    await waitFor(() => {
      expect(inspectionListRouteMocks.listProps.page).toBe(1);
    });

    const params = inspectionListRouteMocks.setSearchParams.mock.calls[
      inspectionListRouteMocks.setSearchParams.mock.calls.length - 1
    ]?.[0] as URLSearchParams;
    expect(params.toString()).toBe(
      'type=PSC&status=SUBMITTED&date_from=2026-02-01&date_to=2026-02-08'
    );
  });

  it('test_feat_ins_010_clear_filters_resets_route_state_and_query_string', async () => {
    const { getByRole } = render(<InspectionListPage />);
    fireEvent.click(getByRole('button', { name: 'Trigger Clear Filters' }));

    await waitFor(() => {
      expect(inspectionListRouteMocks.listProps.filters).toEqual({});
      expect(inspectionListRouteMocks.listProps.page).toBe(1);
    });
    const params = inspectionListRouteMocks.setSearchParams.mock.calls[
      inspectionListRouteMocks.setSearchParams.mock.calls.length - 1
    ]?.[0] as URLSearchParams;
    expect(params.toString()).toBe('');
  });

  it('test_feat_ins_010_fab_navigates_to_create_inspection_route', () => {
    render(<InspectionListPage />);

    fireEvent.click(screen.getByRole('button', { name: /create new inspection/i }));

    expect(inspectionListRouteMocks.navigate).toHaveBeenCalledWith('/inspections/new');
  });

  it('test_feat_rpt_002_export_calls_api_with_active_filters', async () => {
    render(<InspectionListPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Export Excel' }));

    await waitFor(() => {
      expect(inspectionListRouteMocks.exportDeficiencyExcel).toHaveBeenCalledWith({
        status: 'SUBMITTED',
        inspection_type: 'PSC',
        date_from: undefined,
        date_to: undefined,
      });
    });
  });

  it('test_feat_rpt_002_export_failure_shows_destructive_toast', async () => {
    inspectionListRouteMocks.exportDeficiencyExcel.mockRejectedValueOnce(
      new Error('network failed')
    );
    render(<InspectionListPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Export Excel' }));

    await waitFor(() => {
      expect(inspectionListRouteMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: 'destructive',
          title: 'Export failed',
        })
      );
    });
  });
});
