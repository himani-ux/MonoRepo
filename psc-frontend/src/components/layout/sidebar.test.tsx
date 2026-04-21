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

  it('shows_help_entry_in_footer_for_authenticated_users', () => {
    render(<Sidebar isOpen />);

    expect(screen.getByText('Help')).toBeInTheDocument();
    expect(screen.getByText('User guides by module')).toBeInTheDocument();
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

  it('marks_help_entry_as_active_on_help_route', () => {
    sidebarMocks.useLocation.mockReturnValue({ pathname: '/help' });

    render(<Sidebar isOpen />);

    expect(screen.getByRole('link', { name: /help user guides by module/i })).toHaveAttribute('href', '/help');
  });
});
