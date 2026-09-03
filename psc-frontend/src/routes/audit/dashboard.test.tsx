import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { RegisteredAudit, RegisteredAuditList } from '@/lib/api/audit';
import type { AuditPlan, AuditPlanList } from '@/schemas/audit/plan';

const dashboardMocks = vi.hoisted(() => ({
  useAuditPlans: vi.fn(),
  useRegisteredAudits: vi.fn(),
  hasProcess: vi.fn(),
}));

vi.mock('@/hooks/audit/use-audit-plan', () => ({
  useAuditPlans: () => dashboardMocks.useAuditPlans(),
}));

vi.mock('@/hooks/audit/use-audit-registration', () => ({
  useRegisteredAudits: () => dashboardMocks.useRegisteredAudits(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    hasProcess: dashboardMocks.hasProcess,
  }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import AuditHomeRoute from './index';
import AuditDashboardRoute from './dashboard';

function samplePlan(overrides: Partial<AuditPlan> = {}): AuditPlan {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    target_vessel_id: '22222222-2222-4222-8222-222222222222',
    target_office_dept: null,
    target_label: 'EAST AYUTTHAYA',
    audit_classification: 'INTERNAL',
    audit_standards_csv: 'ISM,ISPS',
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
    created_by: 'seq-1',
    created_date: '2026-08-01T09:00:00+05:30',
    updated_by: null,
    updated_date: null,
    ...overrides,
  };
}

function sampleList(results: AuditPlan[]): AuditPlanList {
  return {
    count: results.length,
    results,
  };
}

function sampleRegisteredAudit(overrides: Partial<RegisteredAudit> = {}): RegisteredAudit {
  return {
    id: '34cfabc1-01c3-49ad-9516-5de5bdd7073d',
    audit_plan_id: '11111111-1111-4111-8111-111111111111',
    target_label: 'SFC - SF CHALISA',
    vessel_id: '22222222222242228222222222222222',
    audit_classification: 'INTERNAL',
    auditee_type: 'VESSEL',
    auditee_office_dept: null,
    audit_subtype: 'ANNUAL_INTERNAL',
    lead_auditor_name: 'Capt. Harman Sandhu',
    lead_auditor_designation: 'SEQ Manager',
    audit_start_date: '2026-08-25',
    audit_end_date: '2026-08-26',
    status: 'IN_PROGRESS',
    created_date: '2026-08-25T10:00:00+05:30',
    ...overrides,
  };
}

function sampleRegisteredAuditList(results: RegisteredAudit[]): RegisteredAuditList {
  return {
    count: results.length,
    results,
  };
}

describe('AuditDashboardRoute', () => {
  beforeEach(() => {
    dashboardMocks.useAuditPlans.mockReset();
    dashboardMocks.useRegisteredAudits.mockReset();
    dashboardMocks.hasProcess.mockReset();
    dashboardMocks.hasProcess.mockReturnValue(true);
    dashboardMocks.useRegisteredAudits.mockReturnValue({
      data: sampleRegisteredAuditList([]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it('renders audit dashboard summary from audit plans', () => {
    dashboardMocks.useAuditPlans.mockReturnValue({
      data: sampleList([
        samplePlan(),
        samplePlan({
          id: '33333333-3333-4333-8333-333333333333',
          target_label: 'Office - SEQ',
          status: 'OVERDUE',
          is_additional: true,
        }),
      ]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    dashboardMocks.useRegisteredAudits.mockReturnValue({
      data: sampleRegisteredAuditList([sampleRegisteredAudit()]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter>
        <AuditDashboardRoute />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Audit Dashboard' })).toBeInTheDocument();
    expect(screen.getByText('EAST AYUTTHAYA')).toBeInTheDocument();
    expect(screen.getByText('Office - SEQ')).toBeInTheDocument();
    expect(screen.getByText('Registered Audits')).toBeInTheDocument();
    expect(screen.getByText('SFC - SF CHALISA')).toBeInTheDocument();
    expect(screen.getByText('Capt. Harman Sandhu')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.queryByText('IN_PROGRESS')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^open$/i })).toHaveAttribute(
      'href',
      '/audit/audits/34cfabc1-01c3-49ad-9516-5de5bdd7073d'
    );
    expect(screen.getByText('Need Attention')).toBeInTheDocument();
    expect(screen.getAllByText('1')).toHaveLength(3);
  });

  it('opens external registered audits on the external close-out route', () => {
    dashboardMocks.useAuditPlans.mockReturnValue({
      data: sampleList([]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    dashboardMocks.useRegisteredAudits.mockReturnValue({
      data: sampleRegisteredAuditList([
        sampleRegisteredAudit({
          id: '982df453-4aa8-411c-9330-b6ff357fb897',
          audit_plan_id: null,
          target_label: 'YCF - YC FORTITUDE',
          audit_classification: 'EXTERNAL',
          audit_subtype: 'SMC_RENEWAL',
          status: 'SUBMITTED',
        }),
      ]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter>
        <AuditDashboardRoute />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: /^open$/i })).toHaveAttribute(
      'href',
      '/audit/external/982df453-4aa8-411c-9330-b6ff357fb897'
    );
  });

  it('redirects /audit to /audit/dashboard', () => {
    dashboardMocks.useAuditPlans.mockReturnValue({
      data: sampleList([]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/audit']}>
        <Routes>
          <Route path="/audit" element={<AuditHomeRoute />} />
          <Route path="/audit/dashboard" element={<div>Dashboard route reached</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Dashboard route reached')).toBeInTheDocument();
  });
});
