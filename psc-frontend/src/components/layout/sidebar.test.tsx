/**
 * Tests for sidebar role-based navigation rendering.
 *
 * PRD Reference: Docs/PRD.md Section 2.5 - FEAT-AUTH-002
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const sidebarMocks = vi.hoisted(() => ({
  useLocation: vi.fn(),
  useAuth: vi.fn(),
  useUnreadCount: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useLocation: () => sidebarMocks.useLocation(),
  NavLink: ({
    to,
    onClick,
    className,
    children,
  }: {
    to: string;
    onClick?: () => void;
    className?: string;
    children: React.ReactNode;
  }) => (
    <a href={to} onClick={onClick} className={className}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => sidebarMocks.useAuth(),
}));

vi.mock('@/hooks/use-notifications', () => ({
  useUnreadCount: () => sidebarMocks.useUnreadCount(),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
}));

import { Sidebar } from './sidebar';

describe('Sidebar', () => {
  beforeEach(() => {
    sidebarMocks.useLocation.mockReset();
    sidebarMocks.useAuth.mockReset();
    sidebarMocks.useUnreadCount.mockReset();

    sidebarMocks.useLocation.mockReturnValue({ pathname: '/inspections' });
    sidebarMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'vessel',
      },
      isVessel: true,
      isOffice: false,
      isMaster: true,
      canAccessReports: false,
      hasForm: vi.fn((formId: string) => formId !== 'PSC_F_007'),
      hasProcess: vi.fn(() => false),
    });
    sidebarMocks.useUnreadCount.mockReturnValue({ data: 0 });
  });

  it('test_feat_auth_002_vessel_user_sees_sync_and_hides_reports', () => {
    render(<Sidebar isOpen />);

    expect(screen.getByText('Sync')).toBeInTheDocument();
    expect(screen.queryByText('Reports')).not.toBeInTheDocument();
  });

  it('test_feat_auth_002_office_user_sees_reports_and_hides_sync', () => {
    sidebarMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'office',
      },
      isVessel: false,
      isOffice: true,
      isMaster: false,
      canAccessReports: true,
      hasForm: vi.fn((formId: string) => formId !== 'PSC_F_006'),
    });
    render(<Sidebar isOpen />);

    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.queryByText('ORB')).not.toBeInTheDocument();
    expect(screen.queryByText('Sync')).not.toBeInTheDocument();
  });

  it('test_defintel_rbac_vessel_rank_allowed_user_sees_reports', () => {
    sidebarMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'vessel',
      },
      isVessel: true,
      isOffice: false,
      isMaster: false,
      canAccessReports: true,
      hasForm: vi.fn(() => true),
    });
    render(<Sidebar isOpen />);

    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('test_feat_auth_002_mobile_close_button_triggers_onclose', () => {
    const onClose = vi.fn();
    render(<Sidebar isOpen onClose={onClose} />);

    fireEvent.click(screen.getByRole('button', { name: /close menu/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('test_feat_notif_001_sidebar_notifications_shows_unread_badge', () => {
    sidebarMocks.useUnreadCount.mockReturnValue({ data: 7 });
    render(<Sidebar isOpen />);

    expect(screen.getByText('7')).toBeInTheDocument();
  });

  it('hides_help_entry_in_footer_for_authenticated_users', () => {
    render(<Sidebar isOpen />);

    expect(screen.queryByText('Help')).not.toBeInTheDocument();
    expect(screen.queryByText('User guides by module')).not.toBeInTheDocument();
  });

  it('shows_certs_entry_when_user_has_certs_access', () => {
    sidebarMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'office',
      },
      isVessel: false,
      isOffice: true,
      isMaster: false,
      canAccessReports: false,
      vesselId: null,
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
    });

    render(<Sidebar isOpen />);

    expect(screen.getByRole('link', { name: 'Certs' })).toHaveAttribute('href', '/certs');
  });

  it('keeps inspection tree collapsed on circular route until inspection is clicked', () => {
    sidebarMocks.useLocation.mockReturnValue({ pathname: '/circular' });

    render(<Sidebar isOpen />);

    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /inspection/i }));

    expect(screen.getByText('PSC')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
  });

  it('opens psc items only after clicking psc when inspection is manually expanded', () => {
    sidebarMocks.useLocation.mockReturnValue({ pathname: '/orb' });

    render(<Sidebar isOpen />);

    fireEvent.click(screen.getByRole('button', { name: /inspection/i }));
    fireEvent.click(screen.getByRole('button', { name: /psc/i }));

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Inspections')).toBeInTheDocument();
  });

  it('shows_safety_link_when_user_has_any_safety_form_access', () => {
    sidebarMocks.useLocation.mockReturnValue({ pathname: '/safety/scm' });
    sidebarMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'office',
      },
      isVessel: false,
      isOffice: true,
      isMaster: false,
      canAccessReports: false,
      hasForm: vi.fn((formId: string) => formId === 'SAF_F_003'),
    });

    render(<Sidebar isOpen />);

    const safetyButton = screen.getByRole('button', { name: /safety/i });
    const committeeLink = screen.getByRole('link', { name: 'Committee Meetings' });

    expect(safetyButton).toHaveAttribute('aria-expanded', 'true');
    expect(safetyButton.querySelector('svg')).toBeInTheDocument();
    expect(committeeLink).toHaveAttribute('href', '/safety/scm');
    expect(committeeLink.querySelector('svg')).toBeInTheDocument();
  });

  it('renders_audit_parent_and_child_icons_when_user_has_audit_access', () => {
    sidebarMocks.useLocation.mockReturnValue({ pathname: '/audit/plans' });
    sidebarMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'office',
      },
      isVessel: false,
      isOffice: true,
      isMaster: false,
      canAccessReports: false,
      hasForm: vi.fn(() => false),
      hasProcess: vi.fn((processId: string) =>
        ['AUDIT_P_001', 'AUDIT_P_002', 'AUDIT_P_003', 'AUDIT_P_009'].includes(processId),
      ),
    });

    render(<Sidebar isOpen />);

    const auditButton = screen.getByRole('button', { name: /audit/i });
    const auditDashboardLink = screen.getByRole('link', { name: 'Audit Dashboard' });
    const auditPlansLink = screen.getByRole('link', { name: 'Audit Plans' });
    const qualifiedAuditorsLink = screen.getByRole('link', { name: 'Qualified Auditors' });
    const registerAuditLink = screen.getByRole('link', { name: 'Register Audit' });

    expect(auditButton).toHaveAttribute('aria-expanded', 'true');
    expect(auditButton.querySelector('svg')).toBeInTheDocument();
    expect(auditDashboardLink).toHaveAttribute('href', '/audit/dashboard');
    expect(auditDashboardLink.querySelector('svg')).toBeInTheDocument();
    expect(auditPlansLink).toHaveAttribute('href', '/audit/plans');
    expect(auditPlansLink.querySelector('svg')).toBeInTheDocument();
    expect(qualifiedAuditorsLink).toHaveAttribute('href', '/audit/masters/qualified-auditors');
    expect(qualifiedAuditorsLink.querySelector('svg')).toBeInTheDocument();
    expect(registerAuditLink).toHaveAttribute('href', '/inspections/new');
    expect(registerAuditLink.querySelector('svg')).toBeInTheDocument();
  });

  it('hides_broad_safety_admin_link_but_keeps_auditor_export', () => {
    sidebarMocks.useLocation.mockReturnValue({ pathname: '/safety/admin/auditor-export' });
    sidebarMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'office',
      },
      isVessel: false,
      isOffice: true,
      isMaster: false,
      canAccessReports: false,
      hasForm: vi.fn((formId: string) =>
        ['SAF_F_015', 'SAF_F_018', 'SAF_F_020'].includes(formId),
      ),
    });

    render(<Sidebar isOpen />);

    expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument();
    const auditorLink = screen.getByRole('link', { name: 'Auditor Export' });

    expect(auditorLink).toHaveAttribute(
      'href',
      '/safety/admin/auditor-export',
    );
    expect(auditorLink.querySelector('svg')).toBeInTheDocument();
  });

  it('does_not_render_help_entry_on_help_route', () => {
    sidebarMocks.useLocation.mockReturnValue({ pathname: '/help' });

    render(<Sidebar isOpen />);

    expect(screen.queryByRole('link', { name: /help user guides by module/i })).not.toBeInTheDocument();
  });

  it('keeps_sidebar_navigation_scrollable_in_both_directions_and_adds_psc_icon', () => {
    render(<Sidebar isOpen />);

    const sidebar = screen.getByRole('complementary');
    const navigation = screen.getByRole('navigation', { name: /main navigation/i });
    const pscButton = screen.getByRole('button', { name: /psc/i });

    expect(sidebar).toHaveClass('w-80');
    expect(navigation).toHaveClass('overflow-y-auto');
    expect(navigation).toHaveClass('overflow-x-auto');
    expect(pscButton.querySelector('svg')).toBeInTheDocument();
  });
});
