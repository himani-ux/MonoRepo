import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditDetail } from '@/schemas/audit/detail';

const externalCloseoutMocks = vi.hoisted(() => ({
  useAuditDetail: vi.fn(),
  useConfirmExternalAuditCloseout: vi.fn(),
  useEditExternalAuditCertLinks: vi.fn(),
  closeout: vi.fn(),
  editLinks: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('@/hooks/audit/use-audit-registration', () => ({
  useAuditDetail: (id: string | undefined) => externalCloseoutMocks.useAuditDetail(id),
  useConfirmExternalAuditCloseout: (id: string | undefined) => externalCloseoutMocks.useConfirmExternalAuditCloseout(id),
  useEditExternalAuditCertLinks: (id: string | undefined) => externalCloseoutMocks.useEditExternalAuditCertLinks(id),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: externalCloseoutMocks.toast }),
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

vi.mock('@/components/shared', () => ({
  ErrorState: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock('@/components/shared/loading-skeleton', () => ({
  SectionSkeleton: () => <div>Section Skeleton</div>,
}));

import { ExternalAuditCloseoutPage } from './[auditId]';

function sampleExternalAudit(overrides: Partial<AuditDetail> = {}): AuditDetail {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    inspection_id: '22222222-2222-4222-8222-222222222222',
    inspection: {
      id: '22222222-2222-4222-8222-222222222222',
      vessel_id: 'VESSEL-001',
      inspection_date: '2026-07-30',
      port_place: 'Singapore',
      country: 'Singapore',
      authority: '',
      inspector_name: 'External Lead',
      report_reference: 'DNV-SMC-2026-001',
    },
    audit_classification: 'EXTERNAL',
    auditee_type: 'VESSEL',
    auditee_office_dept: null,
    audit_subtype: 'EXTERNAL',
    lead_auditor_name: 'External Lead',
    lead_auditor_designation: null,
    lead_auditor_company: 'DNV',
    lead_auditor_qual: 'ISM Lead Auditor',
    trigger_reason: 'EXTERNAL_AUDIT',
    audit_start_date: '2026-07-29',
    audit_end_date: '2026-07-30',
    opening_meeting_at: null,
    closing_meeting_at: null,
    audit_scope: '',
    terms_of_reference: '',
    audit_summary: '',
    equipment_tested: '',
    prev_internal_ca_verified: '',
    prev_external_ca_verified: '',
    status: 'VESSEL_ACKNOWLEDGED',
    external_audit_subtypes: ['SMC_RENEWAL'],
    external_audit_org_id: '33333333-3333-4333-8333-333333333333',
    external_audit_org_type: 'CLASS_SOCIETY',
    external_lead_auditor_name: 'L. Bergstrom',
    external_lead_auditor_credential: 'IMO ISM Auditor',
    flag_state_code: 'SG',
    cycle_year: 2026,
    linked_cert_ids: ['44444444-4444-4444-8444-444444444444'],
    certificate_impact: '',
    external_closure_status: 'PENDING_EXTERNAL_CLOSE',
    is_cycle_resetting: false,
    cycle_reset_reason: '',
    standards: ['ISM'],
    team_members: [],
    attendees: [],
    counts: {
      nc: 1,
      observations: 0,
      total_findings: 1,
    },
    scorecard: [],
    findings: [],
    ...overrides,
  };
}

describe('ExternalAuditCloseoutPage', () => {
  beforeEach(() => {
    externalCloseoutMocks.useAuditDetail.mockReset();
    externalCloseoutMocks.useConfirmExternalAuditCloseout.mockReset();
    externalCloseoutMocks.useEditExternalAuditCertLinks.mockReset();
    externalCloseoutMocks.closeout.mockReset();
    externalCloseoutMocks.editLinks.mockReset();
    externalCloseoutMocks.toast.mockReset();

    externalCloseoutMocks.closeout.mockResolvedValue(sampleExternalAudit({ status: 'DPA_CLOSED' }));
    externalCloseoutMocks.editLinks.mockResolvedValue(sampleExternalAudit());
    externalCloseoutMocks.useConfirmExternalAuditCloseout.mockReturnValue({
      mutateAsync: externalCloseoutMocks.closeout,
      isPending: false,
    });
    externalCloseoutMocks.useEditExternalAuditCertLinks.mockReturnValue({
      mutateAsync: externalCloseoutMocks.editLinks,
      isPending: false,
    });
    externalCloseoutMocks.useAuditDetail.mockReturnValue({
      data: sampleExternalAudit(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it('confirms SUSPENDED external close-out with flag notification evidence', async () => {
    render(<ExternalAuditCloseoutPage auditId="11111111-1111-4111-8111-111111111111" />);

    expect(screen.getByRole('heading', { name: 'External Audit' })).toBeInTheDocument();
    expect(screen.getByText(/Class Society - SMC Renewal/i)).toBeInTheDocument();
    expect(screen.queryByText(/CLASS_SOCIETY - SMC_RENEWAL/i)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/certificate impact/i), { target: { value: 'SUSPENDED' } });
    fireEvent.change(screen.getByLabelText(/typed certificate number/i), { target: { value: 'SMC-2026-001' } });
    fireEvent.change(screen.getByLabelText(/flag notified to/i), { target: { value: 'Flag administration' } });
    fireEvent.change(screen.getByLabelText(/flag notification ref/i), { target: { value: 'FLAG-REF-001' } });
    fireEvent.click(screen.getByText(/cycle-resetting external event/i));
    fireEvent.change(screen.getByLabelText(/cycle reset reason/i), {
      target: {
        value:
          'External renewal audit closed with full certificate cycle reset evidence accepted by the external body.',
      },
    });

    fireEvent.click(screen.getByRole('button', { name: /confirm external closure/i }));

    await waitFor(() => {
      expect(externalCloseoutMocks.closeout).toHaveBeenCalledWith({
        certificate_impact: 'SUSPENDED',
        typed_cert_number: 'SMC-2026-001',
        flag_notified_to: 'Flag administration',
        flag_notification_ref: 'FLAG-REF-001',
        is_cycle_resetting: true,
        cycle_reset_reason:
          'External renewal audit closed with full certificate cycle reset evidence accepted by the external body.',
      });
      expect(externalCloseoutMocks.toast).toHaveBeenCalledWith({ title: 'External closure confirmed' });
    });
  });

  it('saves post-closure certificate link edits with an edit reason', async () => {
    render(<ExternalAuditCloseoutPage auditId="11111111-1111-4111-8111-111111111111" />);

    fireEvent.change(screen.getByLabelText(/linked certificate uuids/i), {
      target: { value: '55555555-5555-4555-8555-555555555555' },
    });
    fireEvent.change(screen.getByLabelText(/edit reason/i), {
      target: { value: 'Correcting linked Certs item after external body supplied amended certificate reference.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save certs link edit/i }));

    await waitFor(() => {
      expect(externalCloseoutMocks.editLinks).toHaveBeenCalledWith({
        linked_cert_ids: ['55555555-5555-4555-8555-555555555555'],
        reason: 'Correcting linked Certs item after external body supplied amended certificate reference.',
      });
      expect(externalCloseoutMocks.toast).toHaveBeenCalledWith({ title: 'Certificate links updated' });
    });
  });
});
