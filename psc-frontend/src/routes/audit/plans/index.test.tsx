import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditPlan, AuditPlanList } from '@/schemas/audit/plan';

const planRouteMocks = vi.hoisted(() => ({
  useAuditPlans: vi.fn(),
  useCancelAuditPlan: vi.fn(),
  useCreateAdditionalAuditPlan: vi.fn(),
  useCreateAuditPlan: vi.fn(),
  useDecideAuditPlanExtension: vi.fn(),
  useAuditQualifiedAuditors: vi.fn(),
  useRecordAuditPlanFlagNotification: vi.fn(),
  useRequestAuditPlanExtension: vi.fn(),
  useUpdateAuditPlan: vi.fn(),
  cancelPlan: vi.fn(),
  createAdditional: vi.fn(),
  createPlan: vi.fn(),
  decideExtension: vi.fn(),
  recordFlag: vi.fn(),
  requestExtension: vi.fn(),
  updatePlan: vi.fn(),
  toast: vi.fn(),
  hasProcess: vi.fn(),
  useAuditVessels: vi.fn(),
  reloadAuditPlanRegisterPage: vi.fn(),
}));

vi.mock('@/hooks/audit/use-audit-plan', () => ({
  useAuditPlans: (isAdditional?: boolean) => planRouteMocks.useAuditPlans(isAdditional),
  useCancelAuditPlan: (id: string | undefined) => planRouteMocks.useCancelAuditPlan(id),
  useCreateAdditionalAuditPlan: () => planRouteMocks.useCreateAdditionalAuditPlan(),
  useCreateAuditPlan: () => planRouteMocks.useCreateAuditPlan(),
  useDecideAuditPlanExtension: (id: string | undefined) => planRouteMocks.useDecideAuditPlanExtension(id),
  useAuditQualifiedAuditors: (standards: string, targetOfficeDept: string) =>
    planRouteMocks.useAuditQualifiedAuditors(standards, targetOfficeDept),
  useRecordAuditPlanFlagNotification: (id: string | undefined) => planRouteMocks.useRecordAuditPlanFlagNotification(id),
  useRequestAuditPlanExtension: (id: string | undefined) => planRouteMocks.useRequestAuditPlanExtension(id),
  useUpdateAuditPlan: (id: string | undefined) => planRouteMocks.useUpdateAuditPlan(id),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    hasProcess: planRouteMocks.hasProcess,
  }),
}));

vi.mock('@/hooks/audit/use-audit-registration', () => ({
  useAuditVessels: () => planRouteMocks.useAuditVessels(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: planRouteMocks.toast }),
}));

vi.mock('@/lib/audit/reload', () => ({
  reloadAuditPlanRegisterPage: () => planRouteMocks.reloadAuditPlanRegisterPage(),
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

import AuditPlanRegisterRoute from './index';

function samplePlan(overrides: Partial<AuditPlan> = {}): AuditPlan {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    target_vessel_id: '22222222-2222-4222-8222-222222222222',
    target_office_dept: null,
    target_label: '22222222-2222-4222-8222-222222222222',
    audit_classification: 'INTERNAL',
    audit_standards_csv: 'ISM,ISPS',
    lead_auditor_user_id: 'lead-1',
    planned_window_start: '2026-05-01',
    planned_window_end: '2026-09-01',
    window_label: '2026-05-01 -> 2026-09-01',
    extended_due_date: null,
    extension_form_ref: null,
    extension_requested_at: null,
    extension_requested_by: null,
    extension_requested_reason: null,
    extension_approved_at: null,
    extension_approved_by: null,
    extension_approved_reason: null,
    flag_notified: false,
    flag_notification_date: null,
    flag_notification_ref: null,
    flag_notification_attachment: null,
    is_additional: false,
    additional_reason: null,
    trigger_event_type: null,
    trigger_event_ref: null,
    cancellation_reason: null,
    next_planned_date: null,
    cancelled_by: null,
    cancelled_at: null,
    status: 'PLANNED',
    created_by: 'seq-1',
    created_date: '2026-08-06T09:00:00+05:30',
    updated_by: null,
    updated_date: null,
    ...overrides,
  };
}

function sampleList(results: AuditPlan[] = [samplePlan()]): AuditPlanList {
  return {
    count: results.length,
    results,
  };
}

function addPlanStandard(formIndex: number, standard: string) {
  fireEvent.click(screen.getAllByLabelText('Standards')[formIndex]);
  fireEvent.click(screen.getByLabelText(standard));
}

describe('AuditPlanRegisterRoute', () => {
  beforeEach(() => {
    planRouteMocks.useAuditPlans.mockReset();
    planRouteMocks.useCancelAuditPlan.mockReset();
    planRouteMocks.useCreateAdditionalAuditPlan.mockReset();
    planRouteMocks.useCreateAuditPlan.mockReset();
    planRouteMocks.useDecideAuditPlanExtension.mockReset();
    planRouteMocks.useAuditQualifiedAuditors.mockReset();
    planRouteMocks.useRecordAuditPlanFlagNotification.mockReset();
    planRouteMocks.useRequestAuditPlanExtension.mockReset();
    planRouteMocks.useUpdateAuditPlan.mockReset();
    planRouteMocks.cancelPlan.mockReset();
    planRouteMocks.createAdditional.mockReset();
    planRouteMocks.createPlan.mockReset();
    planRouteMocks.decideExtension.mockReset();
    planRouteMocks.recordFlag.mockReset();
    planRouteMocks.requestExtension.mockReset();
    planRouteMocks.updatePlan.mockReset();
    planRouteMocks.toast.mockReset();
    planRouteMocks.hasProcess.mockReset();
    planRouteMocks.useAuditVessels.mockReset();
    planRouteMocks.reloadAuditPlanRegisterPage.mockReset();

    planRouteMocks.hasProcess.mockImplementation((processId: string) =>
      ['AUDIT_P_001', 'AUDIT_P_002'].includes(processId)
    );
    planRouteMocks.useAuditVessels.mockReturnValue({
      data: [
        {
          id: '22222222-2222-4222-8222-222222222222',
          vessel_code: 'EAT',
          vessel_name: 'EAST AYUTTHAYA',
        },
      ],
      isLoading: false,
      isError: false,
    });
    planRouteMocks.useAuditQualifiedAuditors.mockReturnValue({
      data: {
        count: 1,
        results: [
          {
            id: 'qualified-auditor-1',
            user_id: 'lead-1',
            display_name: 'Capt. Harman Sandhu',
            designation: 'Marine Auditor',
            company: 'KSM',
            identity_source: 'OFFICE_USER',
            qualification_text: 'ISM Lead Auditor',
            qualification_date: '2026-01-01',
            expiry_date: '2027-01-01',
            scope_standards_csv: 'ISM,ISPS,MLC,EMS',
            qualifying_body: null,
            auditor_scope: 'INTERNAL',
            qualified_for_seq: true,
            is_active: true,
          },
        ],
      },
      isLoading: false,
    });
    planRouteMocks.createPlan.mockResolvedValue(samplePlan());
    planRouteMocks.createAdditional.mockResolvedValue(samplePlan({ is_additional: true }));
    planRouteMocks.cancelPlan.mockResolvedValue(samplePlan({ status: 'CANCELLED' }));
    planRouteMocks.decideExtension.mockResolvedValue(samplePlan({ status: 'EXTENDED' }));
    planRouteMocks.recordFlag.mockResolvedValue(samplePlan({ flag_notified: true }));
    planRouteMocks.requestExtension.mockResolvedValue(samplePlan({ status: 'EXTENSION_REQUESTED' }));
    planRouteMocks.updatePlan.mockResolvedValue(samplePlan({ status: 'CONFIRMED' }));
    planRouteMocks.useCancelAuditPlan.mockReturnValue({
      mutateAsync: planRouteMocks.cancelPlan,
      isPending: false,
    });
    planRouteMocks.useCreateAdditionalAuditPlan.mockReturnValue({
      mutateAsync: planRouteMocks.createAdditional,
      isPending: false,
    });
    planRouteMocks.useCreateAuditPlan.mockReturnValue({
      mutateAsync: planRouteMocks.createPlan,
      isPending: false,
    });
    planRouteMocks.useDecideAuditPlanExtension.mockReturnValue({
      mutateAsync: planRouteMocks.decideExtension,
      isPending: false,
    });
    planRouteMocks.useRecordAuditPlanFlagNotification.mockReturnValue({
      mutateAsync: planRouteMocks.recordFlag,
      isPending: false,
    });
    planRouteMocks.useRequestAuditPlanExtension.mockReturnValue({
      mutateAsync: planRouteMocks.requestExtension,
      isPending: false,
    });
    planRouteMocks.useUpdateAuditPlan.mockReturnValue({
      mutateAsync: planRouteMocks.updatePlan,
      isPending: false,
    });
  });

  it('renders plan rows with window status and additional badge', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([
        samplePlan({ status: 'CONFIRMED' }),
        samplePlan({
          id: '33333333-3333-4333-8333-333333333333',
          target_label: 'Office - SEQ',
          target_vessel_id: null,
          target_office_dept: 'SEQ',
          is_additional: true,
          status: 'EXTENDED',
          extension_form_ref: 'OPM-F-713-2026-003',
        }),
      ]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    expect(await screen.findByRole('heading', { name: 'Audit Plan Register' })).toBeInTheDocument();
    expect(screen.getAllByText('2026-05-01 -> 2026-09-01')).toHaveLength(2);
    expect(screen.getAllByText('Confirmed').length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText('CONFIRMED')).not.toBeInTheDocument();
    expect(screen.getByText('OPM-F-713-2026-003')).toBeInTheDocument();
    expect(screen.getByText('Additional')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('toggles the additional-audit filter query', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /all routine \+ additional/i }));

    await waitFor(() => {
      expect(planRouteMocks.useAuditPlans).toHaveBeenLastCalledWith(true);
    });
  });

  it('creates a routine plan entry from the register form', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    fireEvent.change((await screen.findAllByLabelText('Target vessel'))[0], {
      target: { value: '22222222-2222-4222-8222-222222222222' },
    });
    addPlanStandard(0, 'MLC');
    fireEvent.change(screen.getAllByLabelText('Lead auditor')[0], { target: { value: 'lead-1' } });
    fireEvent.change(screen.getAllByLabelText('Planned window start')[0], { target: { value: '2026-05-01' } });
    fireEvent.change(screen.getAllByLabelText('Planned window end')[0], { target: { value: '2026-09-01' } });
    fireEvent.click(screen.getByRole('button', { name: /new plan entry/i }));

    await waitFor(() => {
      expect(planRouteMocks.createPlan).toHaveBeenCalledWith({
        target_vessel_id: '22222222-2222-4222-8222-222222222222',
        target_office_dept: '',
        audit_classification: 'INTERNAL',
        audit_standards_csv: 'ISM,MLC',
        lead_auditor_user_id: 'lead-1',
        planned_window_start: '2026-05-01',
        planned_window_end: '2026-09-01',
        status: 'PLANNED',
      });
      expect(planRouteMocks.toast).toHaveBeenCalledWith({ title: 'Audit plan created' });
      expect(planRouteMocks.reloadAuditPlanRegisterPage).toHaveBeenCalled();
    });
  });

  it('shows only internal audit standards in the plan standards selector', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    fireEvent.click((await screen.findAllByLabelText('Standards'))[0]);

    expect(screen.getByLabelText('ISM')).toBeInTheDocument();
    expect(screen.getByLabelText('ISPS')).toBeInTheDocument();
    expect(screen.getByLabelText('MLC')).toBeInTheDocument();
    expect(screen.getByLabelText('EMS')).toBeInTheDocument();
    expect(screen.queryByLabelText('DOC')).not.toBeInTheDocument();
  });

  it('renders lead auditor dropdowns in routine and additional plan cards', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    const leadAuditorFields = await screen.findAllByLabelText('Lead auditor');
    expect(leadAuditorFields).toHaveLength(2);
    expect(screen.getAllByText(/Capt\. Harman Sandhu/)).toHaveLength(2);
  });

  it('JOURNEY-1 validates DPA plan creation and confirmation from the plan register', async () => {
    planRouteMocks.hasProcess.mockImplementation((processId: string) =>
      ['AUDIT_P_001', 'AUDIT_P_002', 'AUDIT_P_005', 'AUDIT_P_006'].includes(processId)
    );
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([samplePlan({ status: 'PLANNED' })]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    expect(await screen.findByRole('heading', { name: 'Audit Plan Register' })).toBeInTheDocument();
    expect(screen.getByText('2026-05-01 -> 2026-09-01')).toBeInTheDocument();

    fireEvent.change(screen.getAllByLabelText('Target vessel')[0], {
      target: { value: '22222222-2222-4222-8222-222222222222' },
    });
    addPlanStandard(0, 'ISPS');
    fireEvent.change(screen.getAllByLabelText('Lead auditor')[0], { target: { value: 'lead-1' } });
    fireEvent.change(screen.getAllByLabelText('Planned window start')[0], { target: { value: '2026-05-01' } });
    fireEvent.change(screen.getAllByLabelText('Planned window end')[0], { target: { value: '2026-09-01' } });
    fireEvent.click(screen.getByRole('button', { name: /new plan entry/i }));

    await waitFor(() => {
      expect(planRouteMocks.createPlan).toHaveBeenCalledWith({
        target_vessel_id: '22222222-2222-4222-8222-222222222222',
        target_office_dept: '',
        audit_classification: 'INTERNAL',
        audit_standards_csv: 'ISM,ISPS',
        lead_auditor_user_id: 'lead-1',
        planned_window_start: '2026-05-01',
        planned_window_end: '2026-09-01',
        status: 'PLANNED',
      });
    });

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    fireEvent.change(screen.getAllByLabelText('Status')[0], { target: { value: 'CONFIRMED' } });
    fireEvent.click(screen.getByRole('button', { name: /save plan/i }));

    await waitFor(() => {
      expect(planRouteMocks.useUpdateAuditPlan).toHaveBeenLastCalledWith('11111111-1111-4111-8111-111111111111');
      expect(planRouteMocks.updatePlan).toHaveBeenCalledWith(expect.objectContaining({
        status: 'CONFIRMED',
        audit_standards_csv: 'ISM,ISPS',
      }));
    });
  });

  it('edits a routine plan entry through the plan mutation', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([samplePlan()]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /edit/i }));
    fireEvent.change(screen.getAllByLabelText('Status')[0], { target: { value: 'CONFIRMED' } });
    fireEvent.click(screen.getByRole('button', { name: /save plan/i }));

    await waitFor(() => {
      expect(planRouteMocks.useUpdateAuditPlan).toHaveBeenCalledWith('11111111-1111-4111-8111-111111111111');
      expect(planRouteMocks.updatePlan).toHaveBeenCalledWith(expect.objectContaining({ status: 'CONFIRMED' }));
      expect(planRouteMocks.reloadAuditPlanRegisterPage).toHaveBeenCalled();
    });
  });

  it('requests an OPM F 713 extension from an overdue plan', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([samplePlan({ status: 'OVERDUE' })]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /extension/i }));
    fireEvent.change(screen.getByLabelText('Reason for delay'), {
      target: { value: 'Delay caused by drydock overrun and auditor availability conflict.' },
    });
    fireEvent.change(screen.getByLabelText('Proposed new target date'), { target: { value: '2026-11-30' } });
    fireEvent.click(screen.getByRole('button', { name: /save workflow/i }));

    await waitFor(() => {
      expect(planRouteMocks.useRequestAuditPlanExtension).toHaveBeenLastCalledWith('11111111-1111-4111-8111-111111111111');
      expect(planRouteMocks.requestExtension).toHaveBeenCalledWith({
        extension_requested_reason: 'Delay caused by drydock overrun and auditor availability conflict.',
        proposed_new_target_date: '2026-11-30',
      });
    });
  });

  it('shows DPA decision flag and cancellation workflow controls', async () => {
    planRouteMocks.hasProcess.mockImplementation((processId: string) =>
      ['AUDIT_P_001', 'AUDIT_P_002', 'AUDIT_P_005', 'AUDIT_P_006'].includes(processId)
    );
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([
        samplePlan({ status: 'EXTENSION_REQUESTED' }),
        samplePlan({
          id: '33333333-3333-4333-8333-333333333333',
          status: 'EXTENDED',
          extension_form_ref: 'OPM-F-713-2026-005',
        }),
      ]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /decide/i }));
    fireEvent.change(screen.getByLabelText('DPA reason'), {
      target: { value: 'DPA reviewed the drydock evidence and accepts the proposed date.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save workflow/i }));

    await waitFor(() => {
      expect(planRouteMocks.decideExtension).toHaveBeenCalledWith({
        decision: 'APPROVE',
        extension_approved_reason: 'DPA reviewed the drydock evidence and accepts the proposed date.',
      });
    });

    fireEvent.click(screen.getByRole('button', { name: /flag/i }));
    fireEvent.change(screen.getByLabelText('Flag notification date'), { target: { value: '2026-09-10' } });
    fireEvent.change(screen.getByLabelText('Flag notification ref'), { target: { value: 'FLAG-EXT-2026-09' } });
    fireEvent.change(screen.getByLabelText('Flag attachment ref'), { target: { value: 'attachments/flag-extension.pdf' } });
    fireEvent.click(screen.getByRole('button', { name: /save workflow/i }));

    await waitFor(() => {
      expect(planRouteMocks.recordFlag).toHaveBeenCalledWith({
        flag_notification_date: '2026-09-10',
        flag_notification_ref: 'FLAG-EXT-2026-09',
        flag_notification_attachment: 'attachments/flag-extension.pdf',
      });
    });

    fireEvent.click(screen.getAllByRole('button', { name: /cancel/i })[0]);
    fireEvent.change(screen.getByLabelText('Cancellation reason'), {
      target: { value: 'Vessel entered extended repair and DPA authorised full replanning.' },
    });
    fireEvent.change(screen.getByLabelText('Next planned date'), { target: { value: '2026-12-15' } });
    fireEvent.click(screen.getByRole('button', { name: /save workflow/i }));

    await waitFor(() => {
      expect(planRouteMocks.cancelPlan).toHaveBeenCalledWith({
        cancellation_reason: 'Vessel entered extended repair and DPA authorised full replanning.',
        next_planned_date: '2026-12-15',
      });
    });
  });

  it('creates an additional audit from the register', async () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    fireEvent.change(await screen.findAllByLabelText('Target vessel').then((fields) => fields[1]), {
      target: { value: '22222222-2222-4222-8222-222222222222' },
    });
    fireEvent.change(screen.getAllByLabelText('Lead auditor')[1], { target: { value: 'lead-1' } });
    fireEvent.change(screen.getAllByLabelText('Planned window start')[1], { target: { value: '2026-09-01' } });
    fireEvent.change(screen.getAllByLabelText('Planned window end')[1], { target: { value: '2026-09-10' } });
    fireEvent.change(screen.getByLabelText('Trigger reference'), {
      target: { value: 'FLAG-LETTER-2026-09-10;TRIGGER_EVIDENCE=attachment-123' },
    });
    fireEvent.change(screen.getByLabelText('Trigger type'), { target: { value: 'FLAG_LETTER' } });
    fireEvent.change(screen.getByLabelText('Additional reason'), {
      target: { value: 'DPA authorised additional audit after an external trigger event.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /^additional audit$/i }));

    await waitFor(() => {
      expect(planRouteMocks.createAdditional).toHaveBeenCalledWith(expect.objectContaining({
        target_vessel_id: '22222222-2222-4222-8222-222222222222',
        lead_auditor_user_id: 'lead-1',
        trigger_event_type: 'FLAG_LETTER',
        trigger_event_ref: 'FLAG-LETTER-2026-09-10;TRIGGER_EVIDENCE=attachment-123',
      }));
    });
  });

  it('hides create and edit actions when the user lacks plan gates', async () => {
    planRouteMocks.hasProcess.mockReturnValue(false);
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: sampleList([samplePlan()]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    expect(await screen.findByText('Read only')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /new plan entry/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
  });

  it('shows an error state when the register query fails', () => {
    planRouteMocks.useAuditPlans.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Not found'),
      refetch: vi.fn(),
    });

    render(<AuditPlanRegisterRoute />);

    expect(screen.getByText('Audit plan register not available')).toBeInTheDocument();
  });
});
