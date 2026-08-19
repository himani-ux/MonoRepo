import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { AuditPlan, AuditPlanList } from '@/schemas/audit/plan';

const dashboardMocks = vi.hoisted(() => ({
  useAuditPlans: vi.fn(),
  hasProcess: vi.fn(),
}));

vi.mock('@/hooks/audit/use-audit-plan', () => ({
  useAuditPlans: () => dashboardMocks.useAuditPlans(),
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

describe('AuditDashboardRoute', () => {
  beforeEach(() => {
    dashboardMocks.useAuditPlans.mockReset();
    dashboardMocks.hasProcess.mockReset();
    dashboardMocks.hasProcess.mockReturnValue(true);
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

    render(
      <MemoryRouter>
        <AuditDashboardRoute />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Audit Dashboard' })).toBeInTheDocument();
    expect(screen.getByText('EAST AYUTTHAYA')).toBeInTheDocument();
    expect(screen.getByText('Office - SEQ')).toBeInTheDocument();
    expect(screen.getByText('Need Attention')).toBeInTheDocument();
    expect(screen.getAllByText('1')).toHaveLength(3);
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
