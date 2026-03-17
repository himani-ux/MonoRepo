import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const reportsPageMocks = vi.hoisted(() => ({
  useOffline: vi.fn(),
  useAuth: vi.fn(),
  useDashboard: vi.fn(),
  toast: vi.fn(),
  importOpenSourceExcel: vi.fn(),
  previewVesselPreparationChecklist: vi.fn(),
  exportVesselPreparationChecklist: vi.fn(),
  predictDefCodes: vi.fn(),
}));

vi.mock('@/hooks/use-offline', () => ({
  useOffline: () => reportsPageMocks.useOffline(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => reportsPageMocks.useAuth(),
}));

vi.mock('@/hooks/use-dashboard', () => ({
  useDashboard: (...args: unknown[]) => reportsPageMocks.useDashboard(...args),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: reportsPageMocks.toast }),
}));

vi.mock('@/lib/api/reports', () => ({
  reportsApi: {
    importOpenSourceExcel: (...args: unknown[]) =>
      reportsPageMocks.importOpenSourceExcel(...args),
    previewVesselPreparationChecklist: (...args: unknown[]) =>
      reportsPageMocks.previewVesselPreparationChecklist(...args),
    exportVesselPreparationChecklist: (...args: unknown[]) =>
      reportsPageMocks.exportVesselPreparationChecklist(...args),
    predictDefCodes: (...args: unknown[]) => reportsPageMocks.predictDefCodes(...args),
  },
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/components/ui', () => ({
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
  Card: ({
    children,
    className,
  }: {
    children: ReactNode;
    className?: string;
  }) => <section className={className}>{children}</section>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  CardDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value: string;
    onValueChange?: (value: string) => void;
    children: ReactNode;
  }) => (
    <select value={value} onChange={(event) => onValueChange?.(event.target.value)}>
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectValue: () => null,
  SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectItem: ({
    value,
    children,
  }: {
    value: string;
    children: ReactNode;
  }) => <option value={value}>{children}</option>,
}));

import ReportsPage from './page';

describe('ReportsPage', () => {
  beforeEach(() => {
    reportsPageMocks.useOffline.mockReset();
    reportsPageMocks.useAuth.mockReset();
    reportsPageMocks.useDashboard.mockReset();
    reportsPageMocks.toast.mockReset();
    reportsPageMocks.importOpenSourceExcel.mockReset();
    reportsPageMocks.previewVesselPreparationChecklist.mockReset();
    reportsPageMocks.exportVesselPreparationChecklist.mockReset();
    reportsPageMocks.predictDefCodes.mockReset();

    reportsPageMocks.useOffline.mockReturnValue({ isOnline: true });
    reportsPageMocks.useAuth.mockReturnValue({
      isOffice: true,
      vesselId: null,
      canImportOpenSource: true,
    });
    reportsPageMocks.useDashboard.mockReturnValue({
      data: {
        vessels: [{ id: 'v-1', vessel_code: 'MV01', vessel_name: 'Atlas' }],
      },
      isError: false,
      error: null,
    });

    reportsPageMocks.importOpenSourceExcel.mockResolvedValue({
      import_run_id: 'run-1',
      total_rows: 5,
      valid_rows: 5,
      inserted_rows: 3,
      duplicate_rows: 2,
      invalid_rows: 0,
      invalid_rows_sample: [],
      duplicate_rows_sample: [],
    });
    reportsPageMocks.previewVesselPreparationChecklist.mockResolvedValue({
      scope_mode: 'VESSEL',
      date_from: null,
      date_to: null,
      filters: {},
      dedup: true,
      rows: [
        {
          def_code: '01101',
          action_code: '30',
          mou: 'TOKYO',
          port: 'SINGAPORE',
          country: 'SINGAPORE',
          occurrence_count_total: 4,
          occurrence_count_internal: 3,
          occurrence_count_opensource: 1,
          last_seen_date: '2026-02-01',
          example_description: 'Sample',
        },
      ],
      summary: {
        row_count: 1,
        occurrence_count_total: 4,
        occurrence_count_internal: 3,
        occurrence_count_opensource: 1,
        internal_invalid_rows: 0,
        input_internal_rows: 3,
        input_opensource_rows: 1,
        dedup_stats: {
          dedup_enabled: true,
          input_rows: 4,
          removed_rows: 0,
          output_rows: 4,
        },
        last_seen_rule: 'test',
      },
    });
    reportsPageMocks.exportVesselPreparationChecklist.mockResolvedValue(new Blob(['xlsx']));
    reportsPageMocks.predictDefCodes.mockResolvedValue({
      context: 'PORT',
      context_value: 'SINGAPORE',
      window: 'LAST_24_MONTHS',
      alpha: 100,
      top_n: 20,
      rows: [
        {
          def_code: '01101',
          probability: 0.5,
          count_context: 2,
          count_global: 4,
          last_seen_date: '2026-02-01',
        },
      ],
      invalid_rows_skipped: 0,
    });

    Object.defineProperty(globalThis.URL, 'createObjectURL', {
      writable: true,
      value: vi.fn(() => 'blob:reports'),
    });
    Object.defineProperty(globalThis.URL, 'revokeObjectURL', {
      writable: true,
      value: vi.fn(() => {}),
    });
  });

  it('test_phase5_reports_route_renders_real_defintel_sections_not_placeholder', () => {
    render(<ReportsPage />);

    expect(screen.getByText('A) Import OpenSource Excel (monthly)')).toBeInTheDocument();
    expect(screen.getByText('B) Checklist Builder (scope modes + preview + export)')).toBeInTheDocument();
    expect(screen.getByText('C) Prediction (PORT/MOU + window + top_n)')).toBeInTheDocument();
    expect(screen.queryByText(/Coming in/i)).not.toBeInTheDocument();
  });

  it('test_phase5_offline_guard_shows_online_required_message', () => {
    reportsPageMocks.useOffline.mockReturnValue({ isOnline: false });

    render(<ReportsPage />);
    expect(screen.getByText('Online required')).toBeInTheDocument();
  });

  it('test_phase5_import_flow_calls_api_and_displays_summary_counts', async () => {
    render(<ReportsPage />);

    const file = new File(['sample'], 'monthly.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    fireEvent.change(screen.getByLabelText('OpenSource Excel file'), {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole('button', { name: /Import OpenSource/i }));

    await waitFor(() => {
      expect(reportsPageMocks.importOpenSourceExcel).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByText('Inserted rows')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('test_defintel_rbac_import_403_shows_office_only_message', async () => {
    reportsPageMocks.importOpenSourceExcel.mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        status: 403,
        data: {
          message: 'Office only: OpenSource import is restricted to office users.',
        },
      },
    });
    render(<ReportsPage />);

    const file = new File(['sample'], 'monthly.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    fireEvent.change(screen.getByLabelText('OpenSource Excel file'), {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole('button', { name: /Import OpenSource/i }));

    await waitFor(() => {
      expect(reportsPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Office only',
        })
      );
    });
  });

  it('test_defintel_rbac_vessel_user_hides_import_section', () => {
    reportsPageMocks.useAuth.mockReturnValue({
      isOffice: false,
      vesselId: 'v-1',
      canImportOpenSource: false,
    });

    render(<ReportsPage />);
    expect(screen.queryByText('A) Import OpenSource Excel (monthly)')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Import OpenSource/i })).not.toBeInTheDocument();
  });

  it('test_phase5_checklist_preview_and_export_call_endpoints_and_render_table', async () => {
    render(<ReportsPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Preview' }));
    await waitFor(() => {
      expect(reportsPageMocks.previewVesselPreparationChecklist).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByText('01101')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Export Checklist' }));
    await waitFor(() => {
      expect(reportsPageMocks.exportVesselPreparationChecklist).toHaveBeenCalledTimes(1);
    });
  });

  it('test_phase5_checklist_preview_export_payload_parity_includes_dates_scope_and_filters', async () => {
    render(<ReportsPage />);

    fireEvent.change(screen.getAllByRole('combobox')[0], {
      target: { value: 'FILTER_COMBINED' },
    });

    const dateInputs = Array.from(
      document.querySelectorAll('input[type="date"]')
    ) as HTMLInputElement[];
    fireEvent.change(dateInputs[0], { target: { value: '2026-02-01' } });
    fireEvent.change(dateInputs[1], { target: { value: '2026-02-12' } });

    fireEvent.change(screen.getByPlaceholderText('Port value(s), comma-separated'), {
      target: { value: 'singapore' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Preview' }));
    await waitFor(() => {
      expect(reportsPageMocks.previewVesselPreparationChecklist).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByRole('button', { name: 'Export Checklist' }));
    await waitFor(() => {
      expect(reportsPageMocks.exportVesselPreparationChecklist).toHaveBeenCalledTimes(1);
    });

    const previewPayload = reportsPageMocks.previewVesselPreparationChecklist.mock.calls[0][0];
    const exportPayload = reportsPageMocks.exportVesselPreparationChecklist.mock.calls[0][0];

    expect(previewPayload).toMatchObject({
      scope_mode: 'FILTER_COMBINED',
      date_from: '2026-02-01',
      date_to: '2026-02-12',
      filters: {
        port: ['singapore'],
      },
    });
    expect(exportPayload).toEqual(previewPayload);
  });

  it('test_phase5_filter_combined_shows_import_required_when_backend_requires_import', async () => {
    reportsPageMocks.previewVesselPreparationChecklist.mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        data: {
          error: 'IMPORT_REQUIRED',
        },
      },
    });

    render(<ReportsPage />);

    fireEvent.change(screen.getAllByRole('combobox')[0], {
      target: { value: 'FILTER_COMBINED' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Preview' }));

    await waitFor(() => {
      expect(screen.getByText('Import required')).toBeInTheDocument();
    });
  });

  it('test_phase5_prediction_flow_renders_results_table', async () => {
    render(<ReportsPage />);

    fireEvent.change(screen.getByPlaceholderText('e.g. Singapore'), {
      target: { value: 'Singapore' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Run Prediction' }));

    await waitFor(() => {
      expect(reportsPageMocks.predictDefCodes).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByText('0.500000')).toBeInTheDocument();
  });
});
