import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditNcClosure } from '@/schemas/audit/nc-closure';

const ncRouteMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  useAuditNcClosure: vi.fn(),
  useUpdateAuditNcPart: vi.fn(),
  useDraftAuditNcForVessel: vi.fn(),
  useAuditFindingCarWorkflow: vi.fn(),
  updatePart: vi.fn(),
  draftForVessel: vi.fn(),
  carWorkflow: vi.fn(),
  toast: vi.fn(),
  useCLCHierarchy: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => ncRouteMocks.useParams(),
}));

vi.mock('@/hooks/audit/use-audit-finding', () => ({
  useAuditFindingCarWorkflow: (id: string | undefined) => ncRouteMocks.useAuditFindingCarWorkflow(id),
  useAuditNcClosure: (id: string | undefined) => ncRouteMocks.useAuditNcClosure(id),
  useDraftAuditNcForVessel: (id: string | undefined) => ncRouteMocks.useDraftAuditNcForVessel(id),
  useUpdateAuditNcPart: (id: string | undefined) => ncRouteMocks.useUpdateAuditNcPart(id),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: ncRouteMocks.toast }),
}));

vi.mock('@/hooks/use-masters', () => ({
  useCLCHierarchy: () => ncRouteMocks.useCLCHierarchy(),
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

import AuditNcClosureRoute from './[findingId].nc';

function sampleClosure(overrides: Partial<AuditNcClosure> = {}): AuditNcClosure {
  return {
    id: 'nc-1',
    finding_id: 'finding-1',
    audit_detail_id: 'audit-1',
    car: {
      id: 'car-1',
      car_number: 'AUDIT-2026-001',
      status: 'ALLOTTED',
      target_date: '2026-08-30',
    },
    part_a: {
      nc_reference_no: 'AUDIT-2026-001',
      audit_date: '2026-07-29',
      vessel_id: 'vessel-1',
      port_place: 'Singapore',
      auditor_name: 'Lead Auditor',
      auditor_organisation: 'KSM',
      rule_book_type: 'ISM',
      clause_ref_text: 'ISM 10.2',
      objective_evidence: 'Observed during accommodation walk.',
      nc_issued_date: '2026-07-29',
      required_closure_deadline: '2026-08-30',
      certificates_at_risk: 'DOC',
      nc_classification: 'MINOR_NC',
      description: 'Fire door self-closing device failed.',
    },
    part_b: {
      immediate_action_text: '',
      immediate_action_completed_at: null,
      master_immediate_sign_name: '',
      master_immediate_sign_at: null,
      drafted_by_user_id: '',
    },
    part_c: {
      rca_method: '',
      rca_method_other: '',
      rca_template_id: null,
      problem_statement: '',
      why_1: '',
      why_2: '',
      why_3: '',
      why_4: '',
      why_5: '',
      root_cause_categories: [],
      root_cause_summary: '',
      clc_item_ids: [],
      custom_cause_text: '',
    },
    part_d: {
      corrective_action_text: '',
      target_completion_date: null,
      actual_completion_date: null,
      preventive_action_text: '',
      sms_amendment_required: false,
      sms_amendment_doc_ref: '',
    },
    part_e: {
      effectiveness_review_date: null,
      effectiveness_review_method: '',
      effectiveness_assessment_text: '',
      effectiveness_outcome: '',
      effectiveness_further_action_text: '',
      effectiveness_signer_name: '',
      effectiveness_signer_at: null,
      effectiveness_overdue: false,
    },
    part_f: {
      acceptance_review_date: null,
      acceptance_rca_adequacy_text: '',
      acceptance_decision: '',
      acceptance_return_reason: '',
      acceptance_signer_name: '',
      acceptance_signer_at: null,
    },
    part_g: {
      verifying_auditor_name: '',
      verifying_authority_org: '',
      verification_method: '',
      certificate_endorsement_type: '',
      certificate_endorsement_ref: '',
      auditor_assessment_text: '',
      final_closure_status: '',
      resubmit_by_date: null,
      auditor_verification_sign_at: null,
    },
    ...overrides,
  };
}

describe('AuditNcClosureRoute', () => {
  beforeEach(() => {
    ncRouteMocks.useParams.mockReset();
    ncRouteMocks.useAuditNcClosure.mockReset();
    ncRouteMocks.useUpdateAuditNcPart.mockReset();
    ncRouteMocks.useDraftAuditNcForVessel.mockReset();
    ncRouteMocks.useAuditFindingCarWorkflow.mockReset();
    ncRouteMocks.updatePart.mockReset();
    ncRouteMocks.draftForVessel.mockReset();
    ncRouteMocks.carWorkflow.mockReset();
    ncRouteMocks.toast.mockReset();
    ncRouteMocks.useCLCHierarchy.mockReset();

    ncRouteMocks.useParams.mockReturnValue({ findingId: 'finding-1' });
    ncRouteMocks.useCLCHierarchy.mockReturnValue({
      data: {
        immediate_causes: {
          actions: {},
          conditions: {},
        },
        root_causes: {
          personal_factors: {
            P1: { name: 'Personal Readiness', items: { P1: 'Training Gap' } },
          },
          job_factors: {
            J7: { name: 'Job Planning', items: { J7: 'Procedure Gap' } },
          },
        },
      },
      isLoading: false,
    });
    ncRouteMocks.updatePart.mockResolvedValue(sampleClosure());
    ncRouteMocks.draftForVessel.mockResolvedValue(sampleClosure({ car: { id: 'car-1', car_number: 'AUDIT-2026-001', status: 'OFFICE_DRAFTED', target_date: '2026-08-30' } }));
    ncRouteMocks.carWorkflow.mockResolvedValue({ id: 'car-1', status: 'SUBMITTED_TO_PIC', action: 'SUBMIT_TO_PIC' });
    ncRouteMocks.useUpdateAuditNcPart.mockReturnValue({
      mutateAsync: ncRouteMocks.updatePart,
      isPending: false,
    });
    ncRouteMocks.useDraftAuditNcForVessel.mockReturnValue({
      mutateAsync: ncRouteMocks.draftForVessel,
      isPending: false,
    });
    ncRouteMocks.useAuditFindingCarWorkflow.mockReturnValue({
      mutateAsync: ncRouteMocks.carWorkflow,
      isPending: false,
    });
  });

  it('renders the NC closure dense form with Part A and all save sections', async () => {
    ncRouteMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcClosureRoute />);

    expect(await screen.findByText('AUDIT-2026-001')).toBeInTheDocument();
    expect(screen.getByText('Part A - Auditor Issuance')).toBeInTheDocument();
    expect(screen.getByText('Part B - Immediate / Containment Action')).toBeInTheDocument();
    expect(screen.getByText('Part G - Auditor Verification')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /save section/i })).toHaveLength(6);
  });

  it('saves Part C with CLC root-cause codes and root-cause summary', async () => {
    ncRouteMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcClosureRoute />);

    fireEvent.click(await screen.findByLabelText(/Training Gap/));
    fireEvent.click(screen.getByLabelText(/Procedure Gap/));
    fireEvent.change(screen.getByLabelText('Root Cause Summary'), {
      target: {
        value: 'The closer arm inspection was missed during weekly checks and the loose part remained undetected.',
      },
    });
    fireEvent.click(screen.getAllByRole('button', { name: /save section/i })[1]);

    await waitFor(() => {
      expect(ncRouteMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-c',
        data: expect.objectContaining({
          clc_item_ids: ['P1', 'J7'],
          root_cause_summary: expect.stringContaining('closer arm inspection'),
        }),
      });
    });
  });

  it('shows an error state when the NC closure query fails', () => {
    ncRouteMocks.useAuditNcClosure.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Not found'),
      refetch: vi.fn(),
    });

    render(<AuditNcClosureRoute />);

    expect(screen.getByText('NC closure not found')).toBeInTheDocument();
  });

  it('drafts Part B and Part C for vessel review', async () => {
    ncRouteMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcClosureRoute />);

    fireEvent.change(await screen.findByLabelText('Immediate Action'), {
      target: { value: 'Office drafted immediate containment for Master review.' },
    });
    fireEvent.click(screen.getByLabelText(/Training Gap/));
    fireEvent.change(screen.getByLabelText('Root Cause Summary'), {
      target: {
        value: 'Office drafted the RCA narrative because the vessel team needed a clear starting point.',
      },
    });
    fireEvent.click(screen.getByRole('button', { name: /draft for vessel/i }));

    await waitFor(() => {
      expect(ncRouteMocks.draftForVessel).toHaveBeenCalledWith(expect.objectContaining({
        immediate_action_text: 'Office drafted immediate containment for Master review.',
        clc_item_ids: ['P1'],
        root_cause_summary: expect.stringContaining('vessel team needed'),
      }));
    });
  });

  it('shows backend signature-gate errors when a transition is blocked', async () => {
    ncRouteMocks.carWorkflow.mockRejectedValueOnce(new Error('Signature missing for Part B/C.'));
    ncRouteMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure({
        car: {
          id: 'car-1',
          car_number: 'AUDIT-2026-001',
          status: 'OFFICE_DRAFTED',
          target_date: '2026-08-30',
        },
      }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcClosureRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /submit to pic/i }));

    await waitFor(() => {
      expect(ncRouteMocks.toast).toHaveBeenCalledWith(expect.objectContaining({
        variant: 'destructive',
        title: 'CAR transition blocked',
        description: 'Signature missing for Part B/C.',
      }));
    });
  });

  it('shows the scheduled Effectiveness Review date and overdue state', async () => {
    ncRouteMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure({
        car: {
          id: 'car-1',
          car_number: 'AUDIT-2026-001',
          status: 'LEAD_AUDITOR_CLOSED',
          target_date: '2026-08-30',
        },
        part_e: {
          effectiveness_review_date: '2026-09-30',
          effectiveness_review_method: '',
          effectiveness_assessment_text: '',
          effectiveness_outcome: '',
          effectiveness_further_action_text: '',
          effectiveness_signer_name: '',
          effectiveness_signer_at: null,
          effectiveness_overdue: true,
        },
      }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcClosureRoute />);

    expect(await screen.findByText('EffRev due 2026-09-30')).toBeInTheDocument();
    expect(screen.getByLabelText('Further Action, If any')).toBeInTheDocument();
  });
});
