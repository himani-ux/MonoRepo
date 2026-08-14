import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const externalRouteMocks = vi.hoisted(() => ({
  createAuditRegistration: vi.fn(),
  navigate: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => externalRouteMocks.navigate,
  };
});

vi.mock('@/hooks/audit/use-audit-registration', () => ({
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
    externalRouteMocks.createAuditRegistration.mockResolvedValue({
      id: '11111111-1111-4111-8111-111111111111',
      inspection_id: '22222222-2222-4222-8222-222222222222',
      status: 'SUBMITTED',
      audit_classification: 'EXTERNAL',
      auditee_type: 'VESSEL',
    });
  });

  it('registers an external audit at the Phase 11 route', async () => {
    render(
      <MemoryRouter>
        <ExternalAuditRegistrationRoute />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'External Audit' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/vessel uuid/i), {
      target: { value: '33333333-3333-4333-8333-333333333333' },
    });
    fireEvent.change(screen.getByLabelText(/completion date/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/audit start/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/audit end/i), { target: { value: '2026-08-01' } });
    fireEvent.change(screen.getByLabelText(/port\/place/i), { target: { value: 'Singapore' } });
    fireEvent.change(screen.getByLabelText(/report reference/i), { target: { value: 'DNV-SMC-2026-001' } });
    fireEvent.change(screen.getByLabelText(/external audit org uuid/i), {
      target: { value: '44444444-4444-4444-8444-444444444444' },
    });
    fireEvent.change(screen.getByLabelText(/external lead auditor/i), { target: { value: 'L. Bergstrom' } });
    fireEvent.change(screen.getByLabelText(/auditor credential/i), {
      target: { value: 'IMO ISM/ISPS/MLC Auditor' },
    });
    fireEvent.change(screen.getByLabelText(/external audit report pdf/i), {
      target: { value: 'DNV-audit-report-2026.pdf' },
    });
    fireEvent.change(screen.getByLabelText(/report file path/i), {
      target: { value: '/audit/external/DNV-audit-report-2026.pdf' },
    });

    fireEvent.click(screen.getByRole('button', { name: /register external audit/i }));

    await waitFor(() => {
      expect(externalRouteMocks.createAuditRegistration).toHaveBeenCalledWith(
        expect.objectContaining({
          audit_classification: 'EXTERNAL',
          vessel_id: '33333333-3333-4333-8333-333333333333',
          external_audit_subtypes: ['SMC_RENEWAL'],
          external_audit_org_type: 'CLASS_SOCIETY',
          external_report_file_name: 'DNV-audit-report-2026.pdf',
        })
      );
      expect(externalRouteMocks.navigate).toHaveBeenCalledWith('/audit/external/11111111-1111-4111-8111-111111111111');
    });
  });
});
