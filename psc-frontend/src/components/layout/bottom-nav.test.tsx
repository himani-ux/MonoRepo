/**
 * Tests for mobile bottom navigation role filtering and active route behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.5 - FEAT-AUTH-002
 */

import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const bottomNavMocks = vi.hoisted(() => ({
  useLocation: vi.fn(),
  useAuth: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useLocation: () => bottomNavMocks.useLocation(),
  NavLink: ({
    to,
    className,
    children,
  }: {
    to: string;
    className?: string;
    children: React.ReactNode;
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => bottomNavMocks.useAuth(),
}));

import { BottomNav } from './bottom-nav';

describe('BottomNav', () => {
  beforeEach(() => {
    bottomNavMocks.useLocation.mockReset();
    bottomNavMocks.useAuth.mockReset();

    bottomNavMocks.useLocation.mockReturnValue({ pathname: '/inspections' });
    bottomNavMocks.useAuth.mockReturnValue({
      isVessel: true,
      isOffice: false,
      isMaster: true,
      hasForm: vi.fn(() => true),
    });
  });

  it('test_feat_auth_002_vessel_user_sees_sync_navigation_item', () => {
    render(<BottomNav />);
    expect(screen.getByText('Sync')).toBeInTheDocument();
  });

  it('shows_certs_navigation_when_user_has_certs_access', () => {
    render(<BottomNav />);

    expect(screen.getByRole('link', { name: /certs/i })).toHaveAttribute('href', '/certs');
  });

  it('test_feat_auth_002_office_user_does_not_see_sync_navigation_item', () => {
    bottomNavMocks.useAuth.mockReturnValue({
      isVessel: false,
      isOffice: true,
      isMaster: false,
      hasForm: vi.fn((formId: string) => formId !== 'PSC_F_006'),
    });
    render(<BottomNav />);

    expect(screen.queryByText('Sync')).not.toBeInTheDocument();
  });

  it('test_feat_auth_002_inspection_route_is_marked_active_for_root_path', () => {
    bottomNavMocks.useLocation.mockReturnValue({ pathname: '/' });
    render(<BottomNav />);

    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboardLink.className).toContain('text-primary-600');
  });
});
