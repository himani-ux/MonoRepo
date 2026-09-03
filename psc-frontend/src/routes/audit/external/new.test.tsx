import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

if (!HTMLElement.prototype.hasPointerCapture) {
  Object.defineProperty(HTMLElement.prototype, 'hasPointerCapture', {
    configurable: true,
    value: () => false,
  });
}

if (!HTMLElement.prototype.setPointerCapture) {
  Object.defineProperty(HTMLElement.prototype, 'setPointerCapture', {
    configurable: true,
    value: () => undefined,
  });
}

if (!HTMLElement.prototype.releasePointerCapture) {
  Object.defineProperty(HTMLElement.prototype, 'releasePointerCapture', {
    configurable: true,
    value: () => undefined,
  });
}

if (!HTMLElement.prototype.scrollIntoView) {
  Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
    configurable: true,
    value: () => undefined,
  });
}

const externalRouteMocks = vi.hoisted(() => ({
  createAuditRegistration: vi.fn(),
  navigate: vi.fn(),
  toast: vi.fn(),
  useAuditVessels: vi.fn(),
  useAuditExternalAuditOrgs: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => externalRouteMocks.navigate,
  };
});

vi.mock('@/hooks/audit/use-audit-registration', () => ({
  useAuditVessels: () => externalRouteMocks.useAuditVessels(),
  useAuditExternalAuditOrgs: () => externalRouteMocks.useAuditExternalAuditOrgs(),
  useCreateAuditRegistration: () => ({
    mutateAsync: externalRouteMocks.createAuditRegistration,
    isPending: false,
  }),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: externalRouteMocks.toast }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => (
    <header>
      <h1>{title}</h1>
    </header>
  ),
}));

import ExternalAuditRegistrationRoute from './new';

describe('ExternalAuditRegistrationRoute', () => {
  beforeEach(() => {
    externalRouteMocks.createAuditRegistration.mockReset();
    externalRouteMocks.navigate.mockReset();
    externalRouteMocks.toast.mockReset();
    externalRouteMocks.useAuditVessels.mockReset();
    externalRouteMocks.useAuditExternalAuditOrgs.mockReset();
    externalRouteMocks.useAuditVessels.mockReturnValue({
      data: [
        {
          id: '33333333-3333-4333-8333-333333333333',
          vessel_code: 'EAT',
          vessel_name: 'EAST AYUTTHAYA',
        },
      ],
      isLoading: false,
      isError: false,
    });
    externalRouteMocks.useAuditExternalAuditOrgs.mockReturnValue({
      data: {
        results: [
          {
            id: '44444444-4444-4444-8444-444444444444',
            name: 'DNV',
            org_type: 'CLASS_SOCIETY',
            country: 'Norway',
            linked_class_society_ref: null,
            is_active: true,
          },
        ],
      },
      isLoading: false,
      isError: false,
    });
    externalRouteMocks.createAuditRegistration.mockResolvedValue({
      id: '11111111-1111-4111-8111-111111111111',
      inspection_id: '22222222-2222-4222-8222-222222222222',
      status: 'SUBMITTED',
      audit_classification: 'EXTERNAL',
      auditee_type: 'VESSEL',
    });
  });

  it('registers an external audit at the Phase 11 route', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ExternalAuditRegistrationRoute />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'External Audit' })).toBeInTheDocument();
    expect(screen.queryByLabelText(/linked certificate uuids/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/linked certificates/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/report file path/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/report file size/i)).not.toBeInTheDocument();

    const reportPdf = new File(['%PDF-1.4 external audit report'], 'DNV-audit-report-2026.pdf', {
      type: 'application/pdf',
    });
    fireEvent.change(screen.getByLabelText(/^vessel/i), {
      target: { value: '33333333-3333-4333-8333-333333333333' },
    });
    fireEvent.change(screen.getByLabelText(/completion date/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/audit start/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/audit end/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/port\/place/i), { target: { value: 'Singapore' } });
    await user.click(screen.getByRole('combobox', { name: /external audit organisation/i }));
    await user.click(await screen.findByRole('option', { name: /DNV - Class Society/i }));
    expect(screen.getByText('SMC Renewal')).toBeInTheDocument();
    expect(screen.queryByText('SMC_RENEWAL')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/external lead auditor/i), { target: { value: 'L. Bergstrom' } });
    fireEvent.change(screen.getByLabelText(/auditor credential/i), {
      target: { value: 'IMO ISM/ISPS/MLC Auditor' },
    });
    await user.upload(screen.getByLabelText(/attach external audit report pdf/i), reportPdf);

    await user.click(await screen.findByRole('button', { name: /register external audit/i }));

    await waitFor(() => {
      expect(externalRouteMocks.createAuditRegistration).toHaveBeenCalledWith(
        expect.objectContaining({
          audit_classification: 'EXTERNAL',
          vessel_id: '33333333-3333-4333-8333-333333333333',
          report_reference: '',
          external_audit_subtypes: ['SMC_RENEWAL'],
          external_audit_org_type: 'CLASS_SOCIETY',
          external_report_file_name: 'DNV-audit-report-2026.pdf',
          external_report_file_path: 'DNV-audit-report-2026.pdf',
          external_report_mime_type: 'application/pdf',
          external_report_file_size: reportPdf.size,
          external_report_file: reportPdf,
        })
      );
      expect(externalRouteMocks.createAuditRegistration.mock.calls[0]?.[0]).not.toHaveProperty('linked_cert_ids');
      expect(externalRouteMocks.navigate).toHaveBeenCalledWith('/audit/external/11111111-1111-4111-8111-111111111111');
    });
  });

  it('rejects a non-PDF report before submit', async () => {
    render(
      <MemoryRouter>
        <ExternalAuditRegistrationRoute />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/attach external audit report pdf/i), {
      target: {
        files: [new File(['plain text'], 'external-report.txt', { type: 'text/plain' })],
      },
    });

    expect(await screen.findByText('Attach a PDF file.')).toBeInTheDocument();
    expect(externalRouteMocks.createAuditRegistration).not.toHaveBeenCalled();
  });

  it('allows registration without external audit organisation when none are configured', async () => {
    const user = userEvent.setup();

    externalRouteMocks.useAuditExternalAuditOrgs.mockReturnValue({
      data: {
        count: 0,
        results: [],
      },
      isLoading: false,
      isError: false,
    });

    render(
      <MemoryRouter>
        <ExternalAuditRegistrationRoute />
      </MemoryRouter>
    );

    expect(screen.getByRole('combobox', { name: /external audit organisation/i })).toBeDisabled();
    expect(
      screen.getByText('No active external audit organisations are configured. You can register without selecting one.')
    ).toBeInTheDocument();

    const reportPdf = new File(['%PDF-1.4 external audit report'], 'DNV-audit-report-2026.pdf', {
      type: 'application/pdf',
    });
    fireEvent.change(screen.getByLabelText(/completion date/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/audit start/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/audit end/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/port\/place/i), { target: { value: 'Singapore' } });
    fireEvent.change(screen.getByLabelText(/external lead auditor/i), { target: { value: 'L. Bergstrom' } });
    fireEvent.change(screen.getByLabelText(/auditor credential/i), {
      target: { value: 'IMO ISM/ISPS/MLC Auditor' },
    });
    await user.upload(screen.getByLabelText(/attach external audit report pdf/i), reportPdf);

    await user.click(screen.getByRole('button', { name: /register external audit/i }));

    await waitFor(() => {
      expect(externalRouteMocks.createAuditRegistration).toHaveBeenCalledWith(
        expect.objectContaining({
          external_audit_org_id: '',
          external_audit_org_type: 'CLASS_SOCIETY',
        })
      );
    });
    expect(screen.queryByText('External audit organisation is required')).not.toBeInTheDocument();
  });
});
