import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditNcClosure, AuditRcaTemplateMaster } from '@/schemas/audit/nc-closure';
import { useNcWizardStore } from '@/stores/audit/use-nc-wizard-store';

const wizardMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  useAuditNcClosure: vi.fn(),
  useAuditRcaTemplates: vi.fn(),
  useUpdateAuditNcPart: vi.fn(),
  updatePart: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => wizardMocks.useParams(),
}));

vi.mock('@/hooks/audit/use-audit-finding', () => ({
  useAuditNcClosure: (id: string | undefined) => wizardMocks.useAuditNcClosure(id),
  useAuditRcaTemplates: (category?: string) => wizardMocks.useAuditRcaTemplates(category),
  useUpdateAuditNcPart: (id: string | undefined) => wizardMocks.useUpdateAuditNcPart(id),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: wizardMocks.toast }),
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

import AuditNcWizardRoute from './[findingId].nc.wizard';

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

function sampleTemplates(): AuditRcaTemplateMaster {
  return {
    category: '',
    templates: [
      {
        id: 'template-1',
        category: 'TRAINING_GAP',
        title: 'Permit refresher missed',
        template_text: 'The assigned team had not completed the latest permit refresher before the task and the gap was not visible in routine supervision.',
        example_evidence_hint: 'Training matrix and toolbox meeting record.',
        applicable_def_categories: 'MINOR_NC,MAJOR_NC',
        code_version: 'Rev 01 Jan-2026',
      },
    ],
  };
}

describe('AuditNcWizardRoute', () => {
  beforeEach(() => {
    wizardMocks.useParams.mockReset();
    wizardMocks.useAuditNcClosure.mockReset();
    wizardMocks.useAuditRcaTemplates.mockReset();
    wizardMocks.useUpdateAuditNcPart.mockReset();
    wizardMocks.updatePart.mockReset();
    wizardMocks.toast.mockReset();

    useNcWizardStore.setState({ findingId: null, stepIndex: 0 });
    wizardMocks.useParams.mockReturnValue({ findingId: 'finding-1' });
    wizardMocks.updatePart.mockResolvedValue(sampleClosure());
    wizardMocks.useUpdateAuditNcPart.mockReturnValue({
      mutateAsync: wizardMocks.updatePart,
      isPending: false,
    });
    wizardMocks.useAuditRcaTemplates.mockReturnValue({
      data: sampleTemplates(),
      isLoading: false,
      error: null,
    });
  });

  it('saves Part B on advance and moves through the mobile wizard steps', async () => {
    wizardMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcWizardRoute />);

    fireEvent.change(await screen.findByLabelText('Immediate action'), {
      target: { value: 'Door was secured and the watchkeeper was briefed.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save and continue/i }));

    await waitFor(() => {
      expect(wizardMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-b',
        data: expect.objectContaining({
          immediate_action_text: 'Door was secured and the watchkeeper was briefed.',
        }),
      });
      expect(screen.getByText('Completed')).toBeInTheDocument();
    });
  });

  it('resumes from server-saved Part C state and pre-fills from an RCA template', async () => {
    wizardMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure({
        part_b: {
          immediate_action_text: 'Door secured.',
          immediate_action_completed_at: '2026-07-30',
          master_immediate_sign_name: '',
          master_immediate_sign_at: null,
          drafted_by_user_id: '',
        },
        part_c: {
          rca_method: 'FIVE_WHY',
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
        },
      }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcWizardRoute />);

    expect(await screen.findByText('Starting Point')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /permit refresher missed/i }));
    fireEvent.click(screen.getByRole('button', { name: /save and continue/i }));

    await waitFor(() => {
      expect(wizardMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-c',
        data: expect.objectContaining({
          rca_template_id: 'template-1',
          root_cause_summary: expect.stringContaining('permit refresher'),
        }),
      });
    });
  });

  it('saves the current step with Ctrl+S and shows backend validation errors', async () => {
    wizardMocks.updatePart.mockRejectedValue({
      isAxiosError: true,
      response: {
        data: {
          message: 'root_cause_summary must be at least 50 characters.',
        },
      },
    });
    wizardMocks.useAuditNcClosure.mockReturnValue({
      data: sampleClosure({
        part_b: {
          immediate_action_text: 'Door secured.',
          immediate_action_completed_at: '2026-07-30',
          master_immediate_sign_name: '',
          master_immediate_sign_at: null,
          drafted_by_user_id: '',
        },
        part_c: {
          rca_method: 'FIVE_WHY',
          rca_method_other: '',
          rca_template_id: 'template-1',
          problem_statement: 'Permit refresher missed',
          why_1: 'Crew had not completed refresher.',
          why_2: '',
          why_3: '',
          why_4: '',
          why_5: '',
          root_cause_categories: ['TRAINING_GAP'],
          root_cause_summary: 'Too short.',
        },
      }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditNcWizardRoute />);

    expect(await screen.findByRole('textbox', { name: /root cause summary/i })).toBeInTheDocument();
    fireEvent.keyDown(screen.getByRole('textbox', { name: /root cause summary/i }), { key: 's', ctrlKey: true });

    await waitFor(() => {
      expect(wizardMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-c',
        data: expect.objectContaining({
          root_cause_summary: 'Too short.',
        }),
      });
      expect(screen.getByText('root_cause_summary must be at least 50 characters.')).toBeInTheDocument();
    });
  });
});
