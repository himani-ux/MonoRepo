import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { INSPECTION_TYPES, USER_ROLES } from '@/lib/utils/constants';

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  useCreateInspection: vi.fn(),
  useCreateAuditRegistration: vi.fn(),
  useAuditVessels: vi.fn(),
  useAuditPlans: vi.fn(),
  createMutateAsync: vi.fn(),
  createAuditMutateAsync: vi.fn(),
  uploadInspectionReport: vi.fn(),
  inspectionFormProps: null as any,
  auditRegistrationFormProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => mocks.navigate,
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => mocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mocks.toast }),
}));

vi.mock('@/hooks/use-inspections', () => ({
  useCreateInspection: () => mocks.useCreateInspection(),
}));

vi.mock('@/hooks/audit/use-audit-registration', () => ({
  useCreateAuditRegistration: () => mocks.useCreateAuditRegistration(),
  useAuditVessels: () => mocks.useAuditVessels(),
}));

vi.mock('@/hooks/audit/use-audit-plan', () => ({
  useAuditPlans: () => mocks.useAuditPlans(),
}));

vi.mock('@/lib/api/inspections', () => ({
  inspectionsApi: {
    uploadInspectionReport: (...args: unknown[]) => mocks.uploadInspectionReport(...args),
  },
}));

vi.mock('@/lib/api/client', () => ({
  getErrorMessage: () => 'Request failed',
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/components/shared', () => ({
  ConfirmDialog: () => null,
}));

vi.mock('@/components/inspection/inspection-form', () => ({
  InspectionForm: (props: any) => {
    mocks.inspectionFormProps = props;
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            props.onSubmit(
              {
                inspection_type: INSPECTION_TYPES.PSC,
                psc_subtype: 'INITIAL',
                inspection_date: '2026-02-08',
                port: 'Singapore',
                port_state: 'SG',
                mou_code: 'TOKYO',
                authority: 'Authority',
                inspector_name: 'Inspector',
                is_detention: false,
                detention_reason: null,
                def_reported: 'NO',
              },
              null
            )
          }
        >
          Submit PSC
        </button>
        <button
          type="button"
          onClick={() =>
            props.onSubmit(
              {
                inspection_type: INSPECTION_TYPES.AUDIT,
                psc_subtype: null,
                inspection_date: '2026-02-08',
                port: 'Singapore',
                port_state: 'SG',
                mou_code: null,
                authority: 'Authority',
                inspector_name: 'Inspector',
                is_detention: false,
                detention_reason: null,
                def_reported: 'NO',
              },
              null
            )
          }
        >
          Submit Audit
        </button>
      </div>
    );
  },
}));

vi.mock('@/components/audit/registration/audit-registration-form', () => ({
  AuditRegistrationForm: (props: any) => {
    mocks.auditRegistrationFormProps = props;
    return (
      <div>
        <label htmlFor="auditee_type">Auditee Type</label>
        <select id="auditee_type" defaultValue="VESSEL">
          <option value="VESSEL">Vessel</option>
          <option value="OFFICE_DEPT">Office Department</option>
        </select>
        <button
          type="button"
          onClick={() =>
            props.onSubmit({
              vessel_id: '11111111-1111-4111-8111-111111111111',
              inspection_date: '2026-02-08',
              port_place: 'Singapore',
              country: 'SG',
              authority: 'Authority',
              inspector_name: 'Lead Auditor',
              report_reference: 'AUD-001',
              audit_classification: 'INTERNAL',
              auditee_type: 'OFFICE_DEPT',
              auditee_office_dept: 'SEQ',
              audit_subtype: 'ANNUAL_INTERNAL',
              lead_auditor_name: 'Lead Auditor',
              lead_auditor_designation: 'Auditor',
              lead_auditor_company: 'KSM',
              lead_auditor_qual: 'ISM',
              lead_auditor_user_id: 'auditor-1',
              trigger_reason: 'SCHEDULED',
              audit_plan_id: '',
              parent_audit_id: '',
              audit_start_date: '2026-02-08',
              audit_end_date: '',
              opening_meeting_at: '',
              closing_meeting_at: '',
              audit_scope: 'Office audit',
              terms_of_reference: '',
              prev_internal_ca_verified: '',
              prev_external_ca_verified: '',
              standards: ['ISM'],
              team_members: [],
              attendees: [],
              schedule_blocks: [],
            })
          }
        >
          Submit Audit Registration
        </button>
      </div>
    );
  },
}));

import CreateInspectionPage from './new';

describe('CreateInspectionPage RBAC type restrictions', () => {
  beforeEach(() => {
    mocks.navigate.mockReset();
    mocks.useAuth.mockReset();
    mocks.toast.mockReset();
    mocks.useCreateInspection.mockReset();
    mocks.useCreateAuditRegistration.mockReset();
    mocks.useAuditVessels.mockReset();
    mocks.useAuditPlans.mockReset();
    mocks.createMutateAsync.mockReset();
    mocks.createAuditMutateAsync.mockReset();
    mocks.uploadInspectionReport.mockReset();
    mocks.inspectionFormProps = null;
    mocks.auditRegistrationFormProps = null;

    mocks.createMutateAsync.mockResolvedValue({ id: 'ins-100' });
    mocks.createAuditMutateAsync.mockResolvedValue({ id: 'audit-100', inspection_id: 'ins-100', status: 'IN_PROGRESS' });
    mocks.useCreateInspection.mockReturnValue({
      mutateAsync: mocks.createMutateAsync,
      isPending: false,
    });
    mocks.useCreateAuditRegistration.mockReturnValue({
      mutateAsync: mocks.createAuditMutateAsync,
      isPending: false,
    });
    mocks.useAuditVessels.mockReturnValue({
      data: [
        {
          id: '11111111-1111-4111-8111-111111111111',
          vessel_code: 'EAT',
          vessel_name: 'EAST AYUTTHAYA',
        },
      ],
      isLoading: false,
    });
    mocks.useAuditPlans.mockReturnValue({
      data: {
        count: 0,
        results: [],
      },
      isLoading: false,
    });
  });

  it('office user sees the audit registration form with auditee type controls', async () => {
    mocks.useAuth.mockReturnValue({
      user: {
        role: USER_ROLES.OFFICE_PIC,
        vessel_id: 'vessel-1',
        full_name: 'Office Auditor',
      },
    });

    render(<CreateInspectionPage />);

    expect(screen.getByRole('heading', { name: 'Register Audit' })).toBeInTheDocument();
    expect(screen.getByLabelText('Auditee Type')).toBeInTheDocument();
    expect(mocks.inspectionFormProps).toBeNull();
    expect(mocks.auditRegistrationFormProps.vesselOptions).toHaveLength(1);
    expect(mocks.auditRegistrationFormProps.auditPlanOptions).toEqual([]);
    expect(mocks.auditRegistrationFormProps.defaultLeadAuditorName).toBe('Office Auditor');
  });

  it('passes distinct registerable audit plans to prevent same-vessel registration confusion', () => {
    mocks.useAuth.mockReturnValue({
      user: {
        role: USER_ROLES.OFFICE_PIC,
        vessel_id: 'vessel-1',
        full_name: 'Office Auditor',
      },
    });
    mocks.useAuditPlans.mockReturnValue({
      data: {
        count: 4,
        results: [
          auditPlan({
            id: 'aaaaaaaa-1111-4111-8111-111111111111',
            target_label: 'SFC - SF CHALISA',
            planned_window_start: '2026-08-22',
            planned_window_end: '2026-08-31',
            window_label: '2026-08-22 -> 2026-08-31',
            status: 'CONFIRMED',
          }),
          auditPlan({
            id: 'bbbbbbbb-2222-4222-8222-222222222222',
            target_label: 'SFC - SF CHALISA',
            planned_window_start: '2026-09-15',
            planned_window_end: '2026-09-20',
            window_label: '2026-09-15 -> 2026-09-20',
            status: 'EXTENDED',
          }),
          auditPlan({
            id: 'cccccccc-3333-4333-8333-333333333333',
            target_label: 'SFC - SF CHALISA',
            planned_window_start: '2026-10-01',
            planned_window_end: '2026-10-05',
            window_label: '2026-10-01 -> 2026-10-05',
            status: 'PLANNED',
          }),
          auditPlan({
            id: 'dddddddd-4444-4444-8444-444444444444',
            lead_auditor_user_id: '',
            target_label: 'Office - TECH',
            status: 'CRITICAL_OVERDUE',
          }),
        ],
      },
      isLoading: false,
    });

    render(<CreateInspectionPage />);

    expect(mocks.auditRegistrationFormProps.auditPlanOptions).toEqual([
      expect.objectContaining({
        id: 'aaaaaaaa-1111-4111-8111-111111111111',
        target_label: 'SFC - SF CHALISA',
        window_label: '2026-08-22 -> 2026-08-31',
      }),
      expect.objectContaining({
        id: 'bbbbbbbb-2222-4222-8222-222222222222',
        target_label: 'SFC - SF CHALISA',
        window_label: '2026-09-15 -> 2026-09-20',
      }),
    ]);
  });

  it('office user submits through the audit registration endpoint', async () => {
    mocks.useAuth.mockReturnValue({
      user: {
        role: USER_ROLES.OFFICE_PIC,
        vessel_id: 'vessel-1',
      },
    });

    render(<CreateInspectionPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Submit Audit Registration' }));

    await waitFor(() => {
      expect(mocks.createAuditMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          audit_classification: 'INTERNAL',
          auditee_type: 'OFFICE_DEPT',
          lead_auditor_user_id: 'auditor-1',
        })
      );
      expect(mocks.createMutateAsync).not.toHaveBeenCalled();
      expect(mocks.navigate).toHaveBeenCalledWith('/audit/audits/audit-100', {
        replace: true,
      });
    });
  });

  it('vessel master can submit PSC and gets all type options', async () => {
    mocks.useAuth.mockReturnValue({
      user: {
        role: USER_ROLES.VESSEL_MASTER,
        vessel_id: 'vessel-1',
      },
    });

    render(<CreateInspectionPage />);

    expect(mocks.inspectionFormProps.allowedInspectionTypes).toEqual([
      INSPECTION_TYPES.PSC,
      INSPECTION_TYPES.RS,
      INSPECTION_TYPES.AUDIT,
    ]);

    fireEvent.click(screen.getByRole('button', { name: 'Submit PSC' }));

    await waitFor(() => {
      expect(mocks.createMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          inspection_type: INSPECTION_TYPES.PSC,
          vessel_id: 'vessel-1',
        })
      );
      expect(mocks.navigate).toHaveBeenCalledWith('/inspections', {
        replace: true,
      });
    });
  });
});

function auditPlan(overrides: Record<string, unknown> = {}) {
  return {
    id: 'aaaaaaaa-1111-4111-8111-111111111111',
    target_vessel_id: '11111111-1111-4111-8111-111111111111',
    target_office_dept: null,
    target_label: 'EAT - EAST AYUTTHAYA',
    audit_classification: 'INTERNAL',
    audit_standards_csv: 'ISM,ISPS',
    lead_auditor_user_id: 'auditor-1',
    planned_window_start: '2026-08-01',
    planned_window_end: '2026-08-31',
    window_label: '2026-08-01 -> 2026-08-31',
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
    status: 'CONFIRMED',
    created_by: null,
    created_date: null,
    updated_by: null,
    updated_date: null,
    ...overrides,
  };
}
