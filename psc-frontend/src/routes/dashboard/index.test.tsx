import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const dashboardRouteMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useDashboard: vi.fn(),
  useCARs: vi.fn(),
  useInspections: vi.fn(),
  useAuth: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => dashboardRouteMocks.navigate,
  };
});

vi.mock('@/hooks/use-dashboard', () => ({
  useDashboard: (...args: unknown[]) => dashboardRouteMocks.useDashboard(...args),
}));

vi.mock('@/hooks/use-cars', () => ({
  useCARs: (...args: unknown[]) => dashboardRouteMocks.useCARs(...args),
}));

vi.mock('@/hooks/use-inspections', () => ({
  useInspections: (...args: unknown[]) => dashboardRouteMocks.useInspections(...args),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => dashboardRouteMocks.useAuth(),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/components/dashboard', async () => {
  const actual = await vi.importActual<typeof import('@/components/dashboard')>('@/components/dashboard');
  return {
    ...actual,
    DeficiencyTrendChart: () => <div data-testid="deficiency-trend-chart" />,
    TopDefCodes: () => <div data-testid="top-def-codes" />,
  };
});

import DashboardPage from './index';

function formatDateForQuery(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function daysAgo(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return formatDateForQuery(date);
}

function expectTargetText(value: string) {
  expect(
    screen.queryAllByText((_, node) => (node?.textContent?.trim() ?? '') === `Target: ${value}`)
      .length
  ).toBeGreaterThan(0);
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-12T12:00:00.000Z'));
    window.localStorage.clear();

    dashboardRouteMocks.navigate.mockReset();
    dashboardRouteMocks.useAuth.mockReset();
    dashboardRouteMocks.useDashboard.mockReset();
    dashboardRouteMocks.useCARs.mockReset();
    dashboardRouteMocks.useInspections.mockReset();

    dashboardRouteMocks.useAuth.mockReturnValue({ isOffice: false, isDPA: false });
    dashboardRouteMocks.useDashboard.mockReturnValue({
      data: {
        inspections_by_type: [],
        total_inspections_12m: 12,
        open_cars_count: 8,
        overdue_cars_count: 3,
        detentions_count: 2,
        top_def_codes: [],
        pending_defs_count: 4,
        missing_evidence_count: 5,
        overdue_actions_count: 0,
        car_status_distribution: [],
        monthly_def_trend: [],
        repeat_deficiencies: undefined,
        vessels: [],
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    dashboardRouteMocks.useCARs.mockReturnValue({
      data: {
        data: [],
        pagination: {
          page: 1,
          page_size: 1,
          total_count: 0,
          total_pages: 1,
        },
      },
    });
    dashboardRouteMocks.useInspections.mockReturnValue({
      data: {
        data: [
          {
            id: 10,
            vessel_name: 'MV Pacific Star',
            inspection_type: 'PSC',
            psc_subtype: null,
            inspection_date: '2026-02-11',
            port: 'Rotterdam',
            port_state: 'NL',
            mou_code: null,
            is_detention: false,
            status: 'SUBMITTED',
            operational_status: 'OPEN',
            deficiency_count: 3,
            open_deficiency_count: 2,
            closed_deficiency_count: 1,
          },
        ],
        pagination: {
          page: 1,
          page_size: 5,
          total_count: 1,
          total_pages: 1,
        },
      },
      isLoading: false,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('removes deprecated KPI labels from dashboard', () => {
    render(<DashboardPage />);

    expect(screen.queryByText('Open CARs')).not.toBeInTheDocument();
    expect(screen.queryByText('Pending DEFs')).not.toBeInTheDocument();
    expect(screen.queryByText('CARs Missing Evidence')).not.toBeInTheDocument();
    expect(screen.queryByText('Overdue Actions')).not.toBeInTheDocument();
  });

  it('navigates for remaining KPI cards via mouse clicks', () => {
    render(<DashboardPage />);

    fireEvent.click(screen.getByRole('button', { name: /Inspections \(12 mo\)/i }));
    fireEvent.click(screen.getByRole('button', { name: /Overdue CARs/i }));
    fireEvent.click(screen.getByRole('button', { name: /Detentions \(3 yr\)/i }));
    fireEvent.click(screen.getByRole('button', { name: /^0 PV Due$/i }));

    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(
      1,
      `/inspections?date_from=${daysAgo(365)}`
    );
    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(2, '/cars?overdue=true');
    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(
      3,
      `/inspections?detention=true&date_from=${daysAgo(365 * 3)}`
    );
    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(4, '/cars?pv_due=true');
  });

  it('supports keyboard activation with Enter and Space', () => {
    render(<DashboardPage />);

    const detentionsCard = screen.getByRole('button', { name: /Detentions \(3 yr\)/i });

    fireEvent.keyDown(detentionsCard, { key: 'Enter' });
    fireEvent.keyDown(detentionsCard, { key: ' ' });

    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(
      1,
      `/inspections?detention=true&date_from=${daysAgo(365 * 3)}`
    );
    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(
      2,
      `/inspections?detention=true&date_from=${daysAgo(365 * 3)}`
    );
  });

  it('keeps remaining KPI cards actionable even when values are zero', () => {
    dashboardRouteMocks.useDashboard.mockReturnValueOnce({
      data: {
        inspections_by_type: [],
        total_inspections_12m: 0,
        open_cars_count: 0,
        overdue_cars_count: 0,
        detentions_count: 0,
        top_def_codes: [],
        pending_defs_count: 0,
        missing_evidence_count: 0,
        overdue_actions_count: 0,
        car_status_distribution: [],
        monthly_def_trend: [],
        repeat_deficiencies: undefined,
        vessels: [],
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<DashboardPage />);

    fireEvent.click(screen.getByRole('button', { name: /^0 Overdue CARs$/i }));
    fireEvent.click(screen.getByRole('button', { name: /^0 Detentions \(3 yr\)$/i }));
    fireEvent.click(screen.getByRole('button', { name: /^0 PV Due$/i }));

    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(1, '/cars?overdue=true');
    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(
      2,
      `/inspections?detention=true&date_from=${daysAgo(365 * 3)}`
    );
    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(3, '/cars?pv_due=true');
  });

  it('shows Set Target control only for DPA', () => {
    const { rerender } = render(<DashboardPage />);
    expect(screen.queryByRole('button', { name: /set target/i })).not.toBeInTheDocument();

    dashboardRouteMocks.useAuth.mockReturnValue({ isOffice: false, isDPA: true });
    rerender(<DashboardPage />);

    expect(screen.getByRole('button', { name: /set target/i })).toBeInTheDocument();
  });

  it('persists avg defs target for same vessel when switching from dpa to master context', () => {
    dashboardRouteMocks.useAuth.mockReturnValue({ isOffice: false, isDPA: true, vesselId: 'v-1' });

    const { unmount } = render(<DashboardPage />);

    fireEvent.click(screen.getByRole('button', { name: /set target/i }));
    fireEvent.change(screen.getByLabelText(/target: avg defs per inspection/i), {
      target: { value: '3' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save target/i }));

    expect(window.localStorage.getItem('dashboard:def_target:vessel:v-1')).toBe('3');
    expect(window.localStorage.getItem('dashboard:def_target:default')).toBe('3');

    unmount();
    dashboardRouteMocks.useAuth.mockReturnValue({ isOffice: false, isDPA: false, vesselId: 'v-1' });
    render(<DashboardPage />);

    expect(screen.queryByRole('button', { name: /set target/i })).not.toBeInTheDocument();
    expectTargetText('3.0');
  });

  it('keeps avg defs target across dashboard remounts', () => {
    dashboardRouteMocks.useAuth.mockReturnValue({ isOffice: false, isDPA: true, vesselId: 'v-8' });

    const { unmount } = render(<DashboardPage />);

    fireEvent.click(screen.getByRole('button', { name: /set target/i }));
    fireEvent.change(screen.getByLabelText(/target: avg defs per inspection/i), {
      target: { value: '4.5' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save target/i }));
    expectTargetText('4.5');

    unmount();
    render(<DashboardPage />);

    expectTargetText('4.5');
    expect(window.localStorage.getItem('dashboard:def_target:vessel:v-8')).toBe('4.5');
  });

  it('navigates repeat deficiency row and vessel chip click-through', () => {
    dashboardRouteMocks.useDashboard.mockReturnValueOnce({
      data: {
        inspections_by_type: [],
        total_inspections_12m: 12,
        open_cars_count: 8,
        overdue_cars_count: 3,
        detentions_count: 2,
        top_def_codes: [],
        pending_defs_count: 4,
        missing_evidence_count: 5,
        overdue_actions_count: 0,
        car_status_distribution: [],
        monthly_def_trend: [],
        repeat_deficiencies: [
          {
            def_code: '01315',
            def_title: 'Fire doors not self-closing',
            repeat_count: 3,
            classification: 'Systemic',
            vessels: [
              { vessel_id: 'v-1', vessel_name: 'MV Pacific Star' },
              { vessel_id: 'v-2', vessel_name: 'MV Ocean Breeze' },
            ],
          },
        ],
        vessels: [],
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<DashboardPage />);

    fireEvent.click(screen.getByRole('button', { name: /01315/i }));
    fireEvent.click(screen.getAllByRole('button', { name: /MV Pacific Star/i })[0]);

    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(
      1,
      '/deficiencies?def_code=01315&dashboard_source=repeat_deficiencies&filter_pending=repeat_filters'
    );
    expect(dashboardRouteMocks.navigate).toHaveBeenNthCalledWith(
      2,
      '/deficiencies?def_code=01315&vessel_id=v-1&dashboard_source=repeat_deficiencies&filter_pending=repeat_filters'
    );
  });

  it('shows_repeat_deficiencies_not_available_state_as_non_error_copy', () => {
    render(<DashboardPage />);

    expect(
      screen.getByText('Repeat deficiency insights are not available yet for this dashboard view.')
    ).toBeInTheDocument();
  });
});
