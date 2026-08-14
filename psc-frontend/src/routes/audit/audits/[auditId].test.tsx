import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditDetail } from '@/schemas/audit/detail';

const auditDetailMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  useAuditDetail: vi.fn(),
  useSubmitAuditReport: vi.fn(),
  useAcknowledgeAuditReport: vi.fn(),
  useUpdateAuditDetail: vi.fn(),
  useUpdateAuditScorecard: vi.fn(),
  useIssueAuditCircular: vi.fn(),
  submitAudit: vi.fn(),
  acknowledgeAudit: vi.fn(),
  updateDetail: vi.fn(),
  updateScorecard: vi.fn(),
  issueCircular: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => auditDetailMocks.useParams(),
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => <a href={to}>{children}</a>,
}));

vi.mock('@/hooks/audit/use-audit-registration', () => ({
  useAuditDetail: (id: string | undefined) => auditDetailMocks.useAuditDetail(id),
  useSubmitAuditReport: (id: string | undefined) => auditDetailMocks.useSubmitAuditReport(id),
  useAcknowledgeAuditReport: (id: string | undefined) => auditDetailMocks.useAcknowledgeAuditReport(id),
  useUpdateAuditDetail: (id: string | undefined) => auditDetailMocks.useUpdateAuditDetail(id),
  useUpdateAuditScorecard: (id: string | undefined) => auditDetailMocks.useUpdateAuditScorecard(id),
}));

vi.mock('@/hooks/audit/use-audit-finding', () => ({
  useIssueAuditCircular: (id: string | undefined) => auditDetailMocks.useIssueAuditCircular(id),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: auditDetailMocks.toast }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title, actions }: { title: string; actions?: React.ReactNode }) => (
    <header>
      <h1>{title}</h1>
      {actions}
    </header>
  ),
}));

vi.mock('@/components/shared', () => ({
  ErrorState: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock('@/components/shared/loading-skeleton', () => ({
  SectionSkeleton: () => <div>Section Skeleton</div>,
}));

import AuditDetailRoute from './[auditId]';

function sampleAudit(overrides: Partial<AuditDetail> = {}): AuditDetail {
  return {
    id: 'audit-1',
    inspection_id: 'inspection-1',
    inspection: {
      id: 'inspection-1',
      vessel_id: 'vessel-1',
      inspection_date: '2026-07-29',
      port_place: 'Singapore',
      country: 'Singapore',
      authority: '',
      inspector_name: 'Lead Auditor',
      report_reference: 'F602-2026-001',
    },
    audit_classification: 'INTERNAL',
    auditee_type: 'VESSEL',
    auditee_office_dept: null,
    audit_subtype: 'ANNUAL_INTERNAL',
    lead_auditor_name: 'Lead Auditor',
    lead_auditor_designation: 'Marine Auditor',
    lead_auditor_company: 'KSM',
    lead_auditor_qual: 'ISM Lead Auditor',
    trigger_reason: 'SCHEDULED',
    audit_start_date: '2026-07-29',
    audit_end_date: '2026-07-30',
    opening_meeting_at: '2026-07-29T09:00:00+05:30',
    closing_meeting_at: null,
    audit_scope: 'Initial scope',
    terms_of_reference: 'Initial terms',
    audit_summary: '',
    equipment_tested: '',
    prev_internal_ca_verified: '',
    prev_external_ca_verified: '',
    status: 'IN_PROGRESS',
    standards: ['ISM', 'ISPS', 'MLC', 'EMS'],
    team_members: [
      {
        id: 'team-1',
        member_name: 'Co Auditor',
        member_designation: 'Supt',
        member_company: 'KSM',
        member_role: 'CO_AUDITOR',
        sequence_no: 1,
      },
    ],
    attendees: [],
    counts: {
      nc: 1,
      observations: 1,
      total_findings: 2,
    },
    scorecard: [
      {
        area_code: 'AREA_01',
        display_name: 'Documentation',
        is_vessel_only: false,
        sequence_no: 1,
        status: null,
        remarks: '',
      },
    ],
    findings: [
      {
        id: 'finding-1',
        finding_type: 'NC',
        nc_category: 'MINOR_NC',
        observation_category: null,
        standard_code: 'ISM',
        clause_ref_text: 'ISM 10',
        description: 'Fire door issue',
        objective_evidence: 'Observed',
        priority: 'MEDIUM',
        is_fleetwide_relevance: false,
        linked_circular_id: null,
        psc_deficiency_id: 'def-1',
        car_id: 'car-1',
        car_number: 'AUDIT-2026-001',
        car_status: 'ALLOTTED',
      },
      {
        id: 'finding-2',
        finding_type: 'OBSERVATION',
        nc_category: null,
        observation_category: 'OFI',
        standard_code: 'ISM',
        clause_ref_text: 'ISM 12',
        description: 'Checklist ownership observation',
        objective_evidence: 'Observed',
        priority: 'MEDIUM',
        is_fleetwide_relevance: false,
        linked_circular_id: null,
        psc_deficiency_id: 'def-2',
        car_id: 'car-2',
        car_number: 'AUDIT-2026-002',
        car_status: 'ALLOTTED',
      },
    ],
    ...overrides,
  };
}

describe('AuditDetailRoute', () => {
  beforeEach(() => {
    auditDetailMocks.useParams.mockReset();
    auditDetailMocks.useAuditDetail.mockReset();
    auditDetailMocks.useSubmitAuditReport.mockReset();
    auditDetailMocks.useAcknowledgeAuditReport.mockReset();
    auditDetailMocks.useUpdateAuditDetail.mockReset();
    auditDetailMocks.useUpdateAuditScorecard.mockReset();
    auditDetailMocks.useIssueAuditCircular.mockReset();
    auditDetailMocks.submitAudit.mockReset();
    auditDetailMocks.acknowledgeAudit.mockReset();
    auditDetailMocks.updateDetail.mockReset();
    auditDetailMocks.updateScorecard.mockReset();
    auditDetailMocks.issueCircular.mockReset();
    auditDetailMocks.toast.mockReset();

    auditDetailMocks.useParams.mockReturnValue({ auditId: 'audit-1' });
    auditDetailMocks.submitAudit.mockResolvedValue(sampleAudit({ status: 'REPORT_FINALIZED' }));
    auditDetailMocks.acknowledgeAudit.mockResolvedValue(sampleAudit({ status: 'VESSEL_ACKNOWLEDGED' }));
    auditDetailMocks.updateDetail.mockResolvedValue(sampleAudit());
    auditDetailMocks.updateScorecard.mockResolvedValue(sampleAudit());
    auditDetailMocks.issueCircular.mockResolvedValue({
      status: 'DRAFT_CREATED',
      circular_id: '55555555-5555-4555-8555-555555555555',
      detail_url: '',
      payload: {},
    });
    auditDetailMocks.useSubmitAuditReport.mockReturnValue({
      mutateAsync: auditDetailMocks.submitAudit,
      isPending: false,
    });
    auditDetailMocks.useAcknowledgeAuditReport.mockReturnValue({
      mutateAsync: auditDetailMocks.acknowledgeAudit,
      isPending: false,
    });
    auditDetailMocks.useUpdateAuditDetail.mockReturnValue({
      mutateAsync: auditDetailMocks.updateDetail,
      isPending: false,
    });
    auditDetailMocks.useUpdateAuditScorecard.mockReturnValue({
      mutateAsync: auditDetailMocks.updateScorecard,
      isPending: false,
    });
    auditDetailMocks.useIssueAuditCircular.mockReturnValue({
      mutateAsync: auditDetailMocks.issueCircular,
      isPending: false,
    });
  });

  it('renders the audit detail shell with header counts scorecard and findings', async () => {
    auditDetailMocks.useAuditDetail.mockReturnValue({
      data: sampleAudit(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditDetailRoute />);

    expect(await screen.findByText('vessel-1')).toBeInTheDocument();
    expect(screen.getByText('Singapore')).toBeInTheDocument();
    expect(screen.getByText('14-Area Inspection Summary')).toBeInTheDocument();
    expect(screen.getByText('0/14 populated')).toBeInTheDocument();
    expect(screen.getByText('AUDIT-2026-001')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /dense/i })).toHaveAttribute(
      'href',
      '/audit/findings/finding-1/nc'
    );
    expect(screen.getByRole('link', { name: /wizard/i })).toHaveAttribute(
      'href',
      '/audit/findings/finding-1/nc/wizard'
    );
    expect(screen.getByRole('link', { name: /observation/i })).toHaveAttribute(
      'href',
      '/audit/findings/finding-2/obs'
    );
    expect(screen.getByText('NCs Raised')).toBeInTheDocument();
    expect(screen.getByText('Observations Raised')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /walk checklist/i })).toHaveAttribute(
      'href',
      '/audit/audits/audit-1/checklist'
    );
    expect(screen.getByRole('button', { name: /submit report/i })).toBeInTheDocument();
  });

  it('saves edited summary and equipment fields through the detail mutation', async () => {
    auditDetailMocks.useAuditDetail.mockReturnValue({
      data: sampleAudit(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditDetailRoute />);

    fireEvent.change(await screen.findByLabelText('Summary of Audit'), {
      target: { value: 'A'.repeat(120) },
    });
    fireEvent.change(screen.getByLabelText('Equipment Tested Successfully'), {
      target: { value: 'Emergency generator' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save summary/i }));

    await waitFor(() => {
      expect(auditDetailMocks.updateDetail).toHaveBeenCalledWith(
        expect.objectContaining({
          audit_summary: 'A'.repeat(120),
          equipment_tested: 'Emergency generator',
        })
      );
    });
  });

  it('saves populated scorecard rows through the scorecard mutation', async () => {
    auditDetailMocks.useAuditDetail.mockReturnValue({
      data: sampleAudit(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditDetailRoute />);

    fireEvent.change(await screen.findByLabelText('Documentation status'), {
      target: { value: 'SATISFACTORY' },
    });
    fireEvent.change(screen.getByLabelText('Documentation remarks'), {
      target: { value: 'Checked' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save scorecard/i }));

    await waitFor(() => {
      expect(auditDetailMocks.updateScorecard).toHaveBeenCalledWith([
        {
          area_code: 'AREA_01',
          status: 'SATISFACTORY',
          remarks: 'Checked',
        },
      ]);
    });
  });

  it('shows structured submit gate failures returned by the backend', async () => {
    auditDetailMocks.submitAudit.mockRejectedValue({
      response: {
        data: {
          message: 'Audit cannot be submitted until all D-071 gates pass.',
          gates: {
            scorecard: {
              missing_rows: 'Populate all 14 scorecard rows before submit: AREA_14.',
            },
          },
        },
      },
    });
    auditDetailMocks.useAuditDetail.mockReturnValue({
      data: sampleAudit(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditDetailRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /submit report/i }));

    await waitFor(() => {
      expect(auditDetailMocks.submitAudit).toHaveBeenCalled();
      expect(screen.getByText('Submit gates blocked finalization')).toBeInTheDocument();
      expect(screen.getByText(/AREA_14/)).toBeInTheDocument();
    });
  });

  it('acknowledges a finalized report through the acknowledgement mutation', async () => {
    auditDetailMocks.useAuditDetail.mockReturnValue({
      data: sampleAudit({ status: 'REPORT_FINALIZED' }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditDetailRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /vessel acknowledge audit report/i }));

    await waitFor(() => {
      expect(auditDetailMocks.acknowledgeAudit).toHaveBeenCalled();
    });
  });

  it('issues a Circular from a fleet-wide NC finding', async () => {
    auditDetailMocks.useAuditDetail.mockReturnValue({
      data: sampleAudit({
        findings: [
          {
            id: 'finding-1',
            finding_type: 'NC',
            nc_category: 'MAJOR_NC',
            observation_category: null,
            standard_code: 'ISM',
            clause_ref_text: 'ISM 10',
            description: 'Fleetwide NC',
            objective_evidence: 'Observed',
            priority: 'HIGH',
            is_fleetwide_relevance: true,
            linked_circular_id: null,
            psc_deficiency_id: 'def-1',
            car_id: 'car-1',
            car_number: 'AUDIT-2026-001',
            car_status: 'ALLOTTED',
          },
        ],
      }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditDetailRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /issue circular/i }));

    await waitFor(() => {
      expect(auditDetailMocks.issueCircular).toHaveBeenCalledWith('finding-1');
      expect(auditDetailMocks.toast).toHaveBeenCalledWith({ title: 'Circular draft created' });
    });
  });
});
