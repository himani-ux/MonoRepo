import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditObsClosure } from '@/schemas/audit/obs-closure';
import { useObsWizardStore } from '@/stores/audit/use-obs-wizard-store';

const obsRouteMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  useAuditObsClosure: vi.fn(),
  useUpdateAuditObsPart: vi.fn(),
  updatePart: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => obsRouteMocks.useParams(),
}));

vi.mock('@/hooks/audit/use-audit-finding', () => ({
  useAuditObsClosure: (id: string | undefined) => obsRouteMocks.useAuditObsClosure(id),
  useUpdateAuditObsPart: (id: string | undefined) => obsRouteMocks.useUpdateAuditObsPart(id),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: obsRouteMocks.toast }),
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

import AuditObsClosureRoute from './[findingId].obs';

function sampleClosure(overrides: Partial<AuditObsClosure> = {}): AuditObsClosure {
  return {
    id: 'obs-1',
    finding_id: 'finding-1',
    audit_detail_id: 'audit-1',
    state: 'IN_PROGRESS',
    car: {
      id: 'car-1',
      car_number: 'AUDIT-2026-002',
      status: 'ALLOTTED',
      target_date: '2026-08-30',
    },
    part_a: {
      observation_reference_no: 'AUDIT-2026-002',
      audit_date: '2026-07-29',
      vessel_id: 'vessel-1',
      port_place: 'Singapore',
      auditor_name: 'Lead Auditor',
      auditor_organisation: 'KSM',
      rule_book_type: 'ISM',
      clause_ref_text: 'ISM 12.1',
      objective_evidence: 'Observation raised during accommodation walk.',
      observation_issued_date: '2026-07-29',
      required_closure_deadline: '2026-08-30',
      observation_category: 'OFI',
      description: 'Checklist ownership was unclear.',
    },
    part_b: {
      responded_by_name: '',
      responded_by_rank: '',
      target_closure_date: null,
      immediate_action_text: '',
      root_cause_text: '',
      corrective_action_text: '',
      preventive_action_text: '',
      sms_amendment_required: false,
      sms_amendment_doc_ref: '',
      actual_closure_date: null,
      master_sign_name: '',
      master_sign_at: null,
    },
    part_c: {
      acceptance_review_date: null,
      acceptance_adequacy_text: '',
      acceptance_decision: '',
      acceptance_return_reason: '',
      acceptance_signer_name: '',
      acceptance_signer_at: null,
    },
    part_d: {
      verifying_auditor_name: '',
      verifying_authority_org: '',
      verification_method: '',
      auditor_remarks_text: '',
      closure_status: '',
      resubmit_by_date: null,
      auditor_verification_sign_at: null,
    },
    ...overrides,
  };
}

describe('AuditObsClosureRoute', () => {
  beforeEach(() => {
    obsRouteMocks.useParams.mockReset();
    obsRouteMocks.useAuditObsClosure.mockReset();
    obsRouteMocks.useUpdateAuditObsPart.mockReset();
    obsRouteMocks.updatePart.mockReset();
    obsRouteMocks.toast.mockReset();

    useObsWizardStore.setState({ findingId: null, stepIndex: 0 });
    obsRouteMocks.useParams.mockReturnValue({ findingId: 'finding-1' });
    obsRouteMocks.updatePart.mockResolvedValue(sampleClosure({ state: 'MASTER_CLOSED' }));
    obsRouteMocks.useUpdateAuditObsPart.mockReturnValue({
      mutateAsync: obsRouteMocks.updatePart,
      isPending: false,
    });
  });

  it('renders the Observation closure record with all four parts', async () => {
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    expect(await screen.findAllByText('AUDIT-2026-002')).not.toHaveLength(0);
    expect(screen.getByText('Part A - Auditor Issuance')).toBeInTheDocument();
    expect(screen.getByText('Part B - Master / HOD Response')).toBeInTheDocument();
    expect(screen.getByText('Part C - DPA Review')).toBeInTheDocument();
    expect(screen.getByText('Part D - Auditor Verification')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /save section/i })).toHaveLength(3);
  });

  it('saves wizard drafts on advance through the three Observation questions', async () => {
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    expect(await screen.findByRole('heading', { name: 'Responder' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Responder name'), { target: { value: 'R. Okafor' } });
    fireEvent.change(screen.getByLabelText('Responder rank'), { target: { value: 'Master' } });
    fireEvent.change(screen.getByLabelText('Target closure date'), { target: { value: '2026-08-12' } });
    fireEvent.click(screen.getByRole('button', { name: /save and continue/i }));

    await waitFor(() => {
      expect(obsRouteMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-b',
        data: expect.objectContaining({
          responded_by_name: 'R. Okafor',
          responded_by_rank: 'Master',
          target_closure_date: '2026-08-12',
        }),
      });
      expect(screen.getByRole('heading', { name: 'Action Plan' })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Immediate action'), {
      target: { value: 'Records corrected and the watch team briefed.' },
    });
    fireEvent.change(screen.getByLabelText('Root cause'), {
      target: { value: 'The rating used an old work-rest-hour format.' },
    });
    fireEvent.change(screen.getByLabelText('Corrective action'), {
      target: { value: 'The current format was issued to the department.' },
    });
    fireEvent.change(screen.getByLabelText('Preventive action'), {
      target: { value: 'A sample completed form was posted near the records file.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save and continue/i }));

    await waitFor(() => {
      expect(obsRouteMocks.updatePart).toHaveBeenLastCalledWith({
        part: 'part-b',
        data: expect.objectContaining({
          immediate_action_text: expect.stringContaining('watch team'),
          root_cause_text: expect.stringContaining('old work-rest-hour'),
          corrective_action_text: expect.stringContaining('current format'),
          preventive_action_text: expect.stringContaining('sample completed form'),
        }),
      });
      expect(screen.getByRole('heading', { name: 'Master Close' })).toBeInTheDocument();
    });
  });

  it('resumes the wizard from server-saved Observation answers and keeps the D-120 layout', async () => {
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure({
        part_b: {
          responded_by_name: 'R. Okafor',
          responded_by_rank: 'Master',
          target_closure_date: '2026-08-12',
          immediate_action_text: 'Records corrected.',
          root_cause_text: 'Old form used.',
          corrective_action_text: 'Current format issued.',
          preventive_action_text: 'Sample posted.',
          sms_amendment_required: false,
          sms_amendment_doc_ref: '',
          actual_closure_date: null,
          master_sign_name: '',
          master_sign_at: null,
        },
      }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    expect(await screen.findByRole('heading', { name: 'Master Close' })).toBeInTheDocument();
    expect(screen.getByText('Observation Context')).toBeInTheDocument();
    expect(screen.getByTestId('obs-wizard-layout')).toHaveClass('lg:grid-cols-[3fr_2fr]');
  });

  it('saves the current wizard step with Ctrl+S and shows online-only API denial', async () => {
    obsRouteMocks.updatePart.mockRejectedValue({
      isAxiosError: true,
      response: {
        data: {
          message: 'Connection lost. Save was not queued offline.',
        },
      },
    });
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    fireEvent.change(await screen.findByLabelText('Responder name'), { target: { value: 'R. Okafor' } });
    fireEvent.keyDown(screen.getByLabelText('Responder name'), { key: 's', ctrlKey: true });

    await waitFor(() => {
      expect(obsRouteMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-b',
        data: expect.objectContaining({
          responded_by_name: 'R. Okafor',
        }),
      });
      expect(screen.getByText('Connection lost. Save was not queued offline.')).toBeInTheDocument();
    });
  });

  it('uses the wizard Master close step to save terminal signature fields', async () => {
    useObsWizardStore.setState({ findingId: 'finding-1', stepIndex: 2 });
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure({
        part_b: {
          responded_by_name: 'R. Okafor',
          responded_by_rank: 'Master',
          target_closure_date: '2026-08-12',
          immediate_action_text: 'Records corrected.',
          root_cause_text: 'Old form used.',
          corrective_action_text: 'Current format issued.',
          preventive_action_text: 'Sample posted.',
          sms_amendment_required: false,
          sms_amendment_doc_ref: '',
          actual_closure_date: null,
          master_sign_name: '',
          master_sign_at: null,
        },
      }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    fireEvent.change(await screen.findByLabelText('Wizard actual closure date'), {
      target: { value: '2026-08-15' },
    });
    fireEvent.change(screen.getByLabelText('Wizard master signer'), {
      target: { value: 'R. Okafor' },
    });
    fireEvent.change(screen.getByLabelText('Wizard master signature time'), {
      target: { value: '2026-08-15T09:30' },
    });
    fireEvent.click(screen.getByRole('button', { name: /^master close$/i }));

    await waitFor(() => {
      expect(obsRouteMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-b',
        data: expect.objectContaining({
          actual_closure_date: '2026-08-15',
          master_sign_name: 'R. Okafor',
          master_sign_at: '2026-08-15T09:30',
        }),
      });
    });
  });

  it('saves Part B with Master signature to terminal closure', async () => {
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    fireEvent.change(await screen.findByLabelText('Responded By Name'), { target: { value: 'Chief Officer' } });
    fireEvent.change(screen.getByLabelText('Immediate Action'), {
      target: { value: 'Crew briefed and checklist owner assigned.' },
    });
    fireEvent.change(screen.getByLabelText('Actual Closure Date'), { target: { value: '2026-08-10' } });
    fireEvent.change(screen.getByLabelText('Master Signer'), { target: { value: 'Vessel Master' } });
    fireEvent.change(screen.getByLabelText('Master Signature Time'), { target: { value: '2026-08-10T10:00' } });
    fireEvent.click(screen.getAllByRole('button', { name: /save section/i })[0]);

    await waitFor(() => {
      expect(obsRouteMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-b',
        data: expect.objectContaining({
          responded_by_name: 'Chief Officer',
          immediate_action_text: 'Crew briefed and checklist owner assigned.',
          actual_closure_date: '2026-08-10',
          master_sign_name: 'Vessel Master',
          master_sign_at: '2026-08-10T10:00',
        }),
      });
    });
  });

  it('saves Part C and keeps the terminal state visible', async () => {
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure({ state: 'MASTER_CLOSED' }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    expect(await screen.findAllByText('MASTER_CLOSED')).not.toHaveLength(0);
    fireEvent.change(screen.getByLabelText('Decision'), { target: { value: 'ACCEPTED' } });
    fireEvent.change(screen.getByLabelText('Adequacy Review'), {
      target: { value: 'DPA reviewed the closure evidence after Master signature.' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: /save section/i })[0]);

    await waitFor(() => {
      expect(obsRouteMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-c',
        data: expect.objectContaining({
          acceptance_decision: 'ACCEPTED',
          acceptance_adequacy_text: expect.stringContaining('closure evidence'),
        }),
      });
    });
  });

  it('saves Part D verification as audit-trail data', async () => {
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: sampleClosure({ state: 'MASTER_CLOSED' }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    fireEvent.change(await screen.findByLabelText('Verifying Auditor'), { target: { value: 'Lead Auditor' } });
    fireEvent.change(screen.getByLabelText('Verification Method'), { target: { value: 'DOCUMENT_REVIEW' } });
    fireEvent.change(screen.getByLabelText('Closure Status'), { target: { value: 'CLOSED' } });
    fireEvent.click(screen.getAllByRole('button', { name: /save section/i })[1]);

    await waitFor(() => {
      expect(obsRouteMocks.updatePart).toHaveBeenCalledWith({
        part: 'part-d',
        data: expect.objectContaining({
          verifying_auditor_name: 'Lead Auditor',
          verification_method: 'DOCUMENT_REVIEW',
          closure_status: 'CLOSED',
        }),
      });
    });
  });

  it('shows an error state when the Observation query fails', () => {
    obsRouteMocks.useAuditObsClosure.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Not found'),
      refetch: vi.fn(),
    });

    render(<AuditObsClosureRoute />);

    expect(screen.getByText('Observation closure not found')).toBeInTheDocument();
  });
});
