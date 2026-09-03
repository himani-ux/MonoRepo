import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditChecklist } from '@/schemas/audit/checklist';
import { useChecklistWalkStore } from '@/stores/audit/use-checklist-walk-store';

const checklistRouteMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  useAuditChecklist: vi.fn(),
  useAuditDetail: vi.fn(),
  useAuditClauseMaster: vi.fn(),
  useCreateAuditFinding: vi.fn(),
  createFinding: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => checklistRouteMocks.useParams(),
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => <a href={to}>{children}</a>,
}));

vi.mock('@/hooks/audit/use-audit-checklist', () => ({
  useAuditChecklist: (id: string | undefined) => checklistRouteMocks.useAuditChecklist(id),
}));

vi.mock('@/hooks/audit/use-audit-registration', () => ({
  useAuditDetail: (id: string | undefined) => checklistRouteMocks.useAuditDetail(id),
}));

vi.mock('@/hooks/audit/use-audit-finding', () => ({
  useAuditClauseMaster: (book: string | undefined) => checklistRouteMocks.useAuditClauseMaster(book),
  useCreateAuditFinding: (id: string | undefined) => checklistRouteMocks.useCreateAuditFinding(id),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: checklistRouteMocks.toast }),
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

import AuditChecklistRoute from './[auditId].checklist';

function sampleChecklist(overrides: Partial<AuditChecklist> = {}): AuditChecklist {
  return {
    audit_id: 'audit-1',
    selected: true,
    ship_type_filter: null,
    item_filter_applied: false,
    checklist: {
      id: 'checklist-1',
      checklist_code: 'F605',
      name: 'Vessel Internal Audit Checklist',
      auditee_type: 'VESSEL',
      scope_dept: null,
      ship_type_scope: 'Common',
      source_form_ref: 'F 605',
      code_version: 'SSQE Rev 01 Feb 2026',
    },
    items: [
      {
        id: '22222222-2222-4222-8222-222222222222',
        location_code: 'BRIDGE',
        item_code: '001',
        question: 'Bridge procedures verified?',
        guideline: 'Check the bridge log and procedures.',
        regulation_ref: 'ISM 7',
        ksm_sms_ref: 'SPM 1.1',
        ship_type: 'Common',
        sequence_no: 1,
      },
      {
        id: '33333333-3333-4333-8333-333333333333',
        location_code: 'CARGO',
        item_code: '002',
        question: 'Cargo procedure verified?',
        guideline: '',
        regulation_ref: '',
        ksm_sms_ref: '',
        ship_type: 'Bulk Carrier',
        sequence_no: 2,
      },
    ],
    ...overrides,
  };
}

describe('AuditChecklistRoute', () => {
  beforeEach(() => {
    checklistRouteMocks.useParams.mockReset();
    checklistRouteMocks.useAuditChecklist.mockReset();
    checklistRouteMocks.useAuditDetail.mockReset();
    checklistRouteMocks.useAuditClauseMaster.mockReset();
    checklistRouteMocks.useCreateAuditFinding.mockReset();
    checklistRouteMocks.createFinding.mockReset();
    checklistRouteMocks.toast.mockReset();
    checklistRouteMocks.useParams.mockReturnValue({ auditId: 'audit-1' });
    checklistRouteMocks.useAuditDetail.mockReturnValue({
      data: { status: 'IN_PROGRESS' },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    checklistRouteMocks.useAuditClauseMaster.mockReturnValue({
      data: {
        rule_book_type: 'ISM',
        clauses: [{ id: '11111111-1111-4111-8111-111111111111', code: '10.2', title: 'NC control', code_version: 'ISM 2018' }],
      },
      isLoading: false,
      error: null,
    });
    checklistRouteMocks.createFinding.mockResolvedValue({ car_number: 'AUDIT-2026-001' });
    checklistRouteMocks.useCreateAuditFinding.mockReturnValue({
      mutateAsync: checklistRouteMocks.createFinding,
      isPending: false,
    });
    useChecklistWalkStore.setState({ auditId: null, items: {} });
  });

  it('renders a loading state while checklist rows are loading', () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    expect(screen.getAllByText('Section Skeleton')).toHaveLength(2);
  });

  it('renders an error state when the checklist query fails', () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('failed'),
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    expect(screen.getByText('Checklist not available')).toBeInTheDocument();
  });

  it('renders checklist rows and stores local walk status and remarks', async () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: sampleChecklist(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    expect(await screen.findByText('Vessel Internal Audit Checklist')).toBeInTheDocument();
    expect(screen.getByText('0/2 reviewed')).toBeInTheDocument();
    expect(screen.getByText('Bridge procedures verified?')).toBeInTheDocument();
    expect(screen.getByText('ISM 7')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /audit detail/i })).toHaveAttribute(
      'href',
      '/audit/audits/audit-1'
    );
    expect(screen.getAllByRole('radiogroup', { name: /status/i })[0]).toHaveAccessibleName('001 status');
    expect(screen.getByLabelText('001 Not reviewed')).toBeChecked();
    expect(screen.getByLabelText('001 Compliant')).toBeInTheDocument();
    expect(screen.getByLabelText('001 Findings')).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('001 Compliant'));
    fireEvent.change(screen.getByLabelText('001 remarks'), {
      target: { value: 'Checked during bridge round.' },
    });

    expect(screen.getByText('1/2 reviewed')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Checked during bridge round.')).toBeInTheDocument();
  });

  it('shows an empty success state when no checklist matches', async () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: sampleChecklist({ selected: false, checklist: null, items: [] }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    expect(await screen.findByText('Checklist not selected')).toBeInTheDocument();
    expect(screen.getByText('No active checklist matched this audit classification.')).toBeInTheDocument();
    expect(screen.getByText('No checklist rows available.')).toBeInTheDocument();
  });

  it('enables the row Add Finding affordance only after the row is marked for finding capture', async () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: sampleChecklist(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    const addFindingButtons = await screen.findAllByRole('button', { name: /^add finding$/i });
    expect(addFindingButtons[0]).toBeDisabled();

    fireEvent.click(screen.getByLabelText('001 Findings'));

    expect(addFindingButtons[0]).not.toBeDisabled();
  });

  it('opens the finding modal from a checklist row and submits a typed NC with a primary clause', async () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: sampleChecklist(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    fireEvent.click(await screen.findByLabelText('001 Findings'));
    fireEvent.click(screen.getAllByRole('button', { name: /^add finding$/i })[0]);

    expect(await screen.findByRole('heading', { name: 'Create Audit Finding' })).toBeInTheDocument();
    expect(screen.getByText('001 - Bridge procedures verified?')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Seeded Clause'), {
      target: { value: '11111111-1111-4111-8111-111111111111' },
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Fire door self-closing device was not functioning.' },
    });
    fireEvent.change(screen.getByLabelText('Objective Evidence'), {
      target: { value: 'Observed during accommodation walk.' },
    });
    fireEvent.change(screen.getByLabelText('Target Closure Date'), {
      target: { value: '2026-08-30' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save finding/i }));

    expect(checklistRouteMocks.createFinding).toHaveBeenCalledWith(
      expect.objectContaining({
        finding_type: 'NC',
        nc_category: 'MINOR_NC',
        priority: 'MEDIUM',
        checklist_item_id: '22222222-2222-4222-8222-222222222222',
        description: 'Fire door self-closing device was not functioning.',
        objective_evidence: 'Observed during accommodation walk.',
        original_due_date: '2026-08-30',
        clauses: [
          expect.objectContaining({
            rule_book_type: 'ISM',
            rule_clause_id: '11111111-1111-4111-8111-111111111111',
            is_primary: true,
          }),
        ],
      })
    );
  });

  it('submits priority certificate scope and fleet-wide relevance from the modal', async () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: sampleChecklist(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /add emergent finding/i }));
    fireEvent.change(screen.getByLabelText('NC Category'), {
      target: { value: 'MAJOR_NC' },
    });
    fireEvent.change(screen.getByLabelText('Priority'), {
      target: { value: 'LOW' },
    });
    fireEvent.change(screen.getByLabelText('Certificates at Risk'), {
      target: { value: 'DOC' },
    });
    fireEvent.click(screen.getByLabelText('Fleet-wide relevance'));
    fireEvent.change(screen.getByLabelText('Seeded Clause'), {
      target: { value: '11111111-1111-4111-8111-111111111111' },
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Fleetwide NC from audit sample.' },
    });
    fireEvent.change(screen.getByLabelText('Objective Evidence'), {
      target: { value: 'Same finding sampled on sister vessels.' },
    });
    fireEvent.change(screen.getByLabelText('Target Closure Date'), {
      target: { value: '2026-08-30' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save finding/i }));

    expect(checklistRouteMocks.createFinding).toHaveBeenCalledWith(
      expect.objectContaining({
        finding_type: 'NC',
        nc_category: 'MAJOR_NC',
        priority: 'LOW',
        certificates_at_risk: 'DOC',
        original_due_date: '2026-08-30',
        is_fleetwide_relevance: true,
      })
    );
  });

  it('hides Add Finding actions when the audit is finalized', async () => {
    checklistRouteMocks.useAuditDetail.mockReturnValue({
      data: { status: 'REPORT_FINALIZED' },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: sampleChecklist(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    expect(await screen.findByText(/Findings are frozen/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /add emergent finding/i })).not.toBeInTheDocument();
    const addFindingButtons = screen.getAllByRole('button', { name: /^add finding$/i });
    expect(addFindingButtons[0]).toBeDisabled();
  });

  it('validates OTHER clause free text before submitting the modal', async () => {
    checklistRouteMocks.useAuditChecklist.mockReturnValue({
      data: sampleChecklist(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditChecklistRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /add emergent finding/i }));
    fireEvent.change(screen.getByLabelText('Primary Book'), {
      target: { value: 'OTHER' },
    });
    fireEvent.change(screen.getByLabelText('Clause Text'), {
      target: { value: 'bad' },
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Emergent finding.' },
    });
    fireEvent.change(screen.getByLabelText('Objective Evidence'), {
      target: { value: 'Observed during audit walkdown.' },
    });
    fireEvent.change(screen.getByLabelText('Target Closure Date'), {
      target: { value: '2026-08-30' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save finding/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Select a seeded clause');
    expect(checklistRouteMocks.createFinding).not.toHaveBeenCalled();
  });
});
