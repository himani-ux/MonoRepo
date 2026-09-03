import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditQualifyingBody, AuditQualifiedAuditor } from '@/lib/api/audit';

const qualifiedAuditorMocks = vi.hoisted(() => ({
  useAuditOfficeUsers: vi.fn(),
  useAuditQualifyingBodies: vi.fn(),
  useAuditQualifiedAuditorMaster: vi.fn(),
  useCreateAuditQualifiedAuditor: vi.fn(),
  useUpdateAuditQualifiedAuditor: vi.fn(),
  createAuditor: vi.fn(),
  updateAuditor: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('@/hooks/audit/use-audit-plan', () => ({
  useAuditOfficeUsers: () => qualifiedAuditorMocks.useAuditOfficeUsers(),
  useAuditQualifyingBodies: () => qualifiedAuditorMocks.useAuditQualifyingBodies(),
  useAuditQualifiedAuditorMaster: () => qualifiedAuditorMocks.useAuditQualifiedAuditorMaster(),
  useCreateAuditQualifiedAuditor: () => qualifiedAuditorMocks.useCreateAuditQualifiedAuditor(),
  useUpdateAuditQualifiedAuditor: () => qualifiedAuditorMocks.useUpdateAuditQualifiedAuditor(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: qualifiedAuditorMocks.toast }),
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

import AuditQualifiedAuditorsRoute from './qualified-auditors';

function sampleAuditor(overrides: Partial<AuditQualifiedAuditor> = {}): AuditQualifiedAuditor {
  return {
    id: 'qualified-auditor-1',
    user_id: 'EMP001',
    display_name: 'Capt. Harman Sandhu',
    designation: 'Marine Superintendent',
    company: 'KSM',
    identity_source: 'OFFICE',
    qualification_text: 'ISM Lead Auditor',
    qualification_date: '2026-01-01',
    expiry_date: '2028-01-01',
    scope_standards_csv: 'ISM,ISPS',
    qualifying_body: 'KSM Academy',
    certificate_attachment_id: null,
    auditor_scope: 'OFFICE_SIDE',
    qualified_for_seq: true,
    is_active: true,
    ...overrides,
  };
}

function sampleQualifyingBody(overrides: Partial<AuditQualifyingBody> = {}): AuditQualifyingBody {
  return {
    id: 'qualifying-body-1',
    body_name: 'KSM Academy',
    is_active: true,
    is_deleted: false,
    ...overrides,
  };
}

describe('AuditQualifiedAuditorsRoute', () => {
  beforeEach(() => {
    qualifiedAuditorMocks.createAuditor.mockReset();
    qualifiedAuditorMocks.updateAuditor.mockReset();
    qualifiedAuditorMocks.toast.mockReset();
    qualifiedAuditorMocks.createAuditor.mockResolvedValue(sampleAuditor());
    qualifiedAuditorMocks.updateAuditor.mockResolvedValue(sampleAuditor());
    qualifiedAuditorMocks.useAuditQualifiedAuditorMaster.mockReturnValue({
      data: { count: 1, results: [sampleAuditor()] },
      isError: false,
      isLoading: false,
    });
    qualifiedAuditorMocks.useAuditOfficeUsers.mockReturnValue({
      data: {
        count: 2,
        results: [
          {
            employee_id: 'EMP001',
            display_name: 'Capt. Harman Sandhu',
            employee_name: 'Harman Sandhu',
            username: 'Harman.S',
            employee_role: 'Internal',
            department: 'Marine',
            role_name: 'SEQ Manager',
          },
          {
            employee_id: 'EMP123',
            display_name: 'Karan Tikare',
            employee_name: 'Karan Tikare',
            username: 'Karan.Tikare',
            employee_role: 'Internal',
            department: 'Operations',
            role_name: 'Technical Superintendent',
          },
        ],
      },
      isError: false,
      isLoading: false,
    });
    qualifiedAuditorMocks.useAuditQualifyingBodies.mockReturnValue({
      data: {
        count: 2,
        results: [
          sampleQualifyingBody(),
          sampleQualifyingBody({ id: 'qualifying-body-2', body_name: 'Bureau Veritas' }),
        ],
      },
      isError: false,
      isLoading: false,
    });
    qualifiedAuditorMocks.useCreateAuditQualifiedAuditor.mockReturnValue({
      isPending: false,
      mutateAsync: qualifiedAuditorMocks.createAuditor,
    });
    qualifiedAuditorMocks.useUpdateAuditQualifiedAuditor.mockReturnValue({
      isPending: false,
      mutateAsync: qualifiedAuditorMocks.updateAuditor,
    });
  });

  it('renders_existing_qualified_auditors', () => {
    render(<AuditQualifiedAuditorsRoute />);

    expect(screen.getByRole('heading', { name: 'Qualified Auditors' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Karan Tikare - Technical Superintendent' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Bureau Veritas' })).toBeInTheDocument();
    expect(screen.getByLabelText('Qualifying Body')).toHaveValue('');
    expect(screen.queryByLabelText('Certificate Attachment ID')).not.toBeInTheDocument();
    expect(screen.getByText('Capt. Harman Sandhu')).toBeInTheDocument();
    expect(screen.getByText('ISM,ISPS')).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('creates_qualified_auditor_record', async () => {
    render(<AuditQualifiedAuditorsRoute />);

    fireEvent.change(screen.getByLabelText('Employee/User ID'), { target: { value: 'EMP123' } });
    fireEvent.change(screen.getByLabelText('Qualification Date'), { target: { value: '2026-08-20' } });
    fireEvent.change(screen.getByLabelText('Expiry Date'), { target: { value: '2028-08-20' } });
    fireEvent.change(screen.getByLabelText('Qualification'), { target: { value: 'MLC Lead Auditor' } });
    fireEvent.change(screen.getByLabelText('Qualifying Body'), { target: { value: 'KSM Academy' } });
    fireEvent.click(screen.getByRole('checkbox', { name: 'MLC' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'SEQ qualified' }));
    fireEvent.click(screen.getByRole('button', { name: /^Save$/ }));

    await waitFor(() => {
      expect(qualifiedAuditorMocks.createAuditor).toHaveBeenCalledWith({
        user_id: 'EMP123',
        qualification_text: 'MLC Lead Auditor',
        qualification_date: '2026-08-20',
        expiry_date: '2028-08-20',
        scope_standards_csv: 'ISM,MLC',
        qualifying_body: 'KSM Academy',
        certificate_attachment_id: null,
        auditor_scope: 'OFFICE_SIDE',
        qualified_for_seq: true,
        is_active: true,
      });
    });
  });

  it('edits_existing_qualified_auditor_record', async () => {
    render(<AuditQualifiedAuditorsRoute />);

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.change(screen.getByLabelText('Qualification'), { target: { value: 'ISM/ISPS Lead Auditor' } });
    fireEvent.click(screen.getByRole('button', { name: /^Save$/ }));

    await waitFor(() => {
      expect(qualifiedAuditorMocks.updateAuditor).toHaveBeenCalledWith({
        id: 'qualified-auditor-1',
        data: expect.objectContaining({
          user_id: 'EMP001',
          qualification_text: 'ISM/ISPS Lead Auditor',
          scope_standards_csv: 'ISM,ISPS',
        }),
      });
    });
  });

  it('toggles_active_state', async () => {
    render(<AuditQualifiedAuditorsRoute />);

    fireEvent.click(screen.getByRole('button', { name: 'Deactivate' }));

    await waitFor(() => {
      expect(qualifiedAuditorMocks.updateAuditor).toHaveBeenCalledWith({
        id: 'qualified-auditor-1',
        data: { is_active: false },
      });
    });
  });
});
