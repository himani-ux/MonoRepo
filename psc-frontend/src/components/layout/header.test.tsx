/**
 * Tests for header actions and user menu behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.7 - FEAT-NOTIF-001
 * PRD Reference: Docs/PRD.md Section 2.5 - FEAT-AUTH-001
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const headerMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useLocation: vi.fn(),
  useAuth: vi.fn(),
  useUnreadCount: vi.fn(),
  logout: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => headerMocks.navigate,
  useLocation: () => headerMocks.useLocation(),
  Link: ({
    to,
    children,
    ...rest
  }: {
    to: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={to} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => headerMocks.useAuth(),
}));

vi.mock('@/hooks/use-notifications', () => ({
  useUnreadCount: () => headerMocks.useUnreadCount(),
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

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({
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
  DropdownMenuSeparator: () => <hr />,
}));

import { Header } from './header';

describe('Header', () => {
  beforeEach(() => {
    headerMocks.navigate.mockReset();
    headerMocks.useLocation.mockReset();
    headerMocks.useAuth.mockReset();
    headerMocks.useUnreadCount.mockReset();
    headerMocks.logout.mockReset();

    headerMocks.useLocation.mockReturnValue({ pathname: '/inspections' });
    headerMocks.logout.mockResolvedValue(undefined);
    headerMocks.useAuth.mockReturnValue({
      fullName: 'Captain Nemo',
      role: 'VESSEL_MASTER',
      logout: headerMocks.logout,
      isVessel: true,
      hasProcess: vi.fn(() => true),
    });
    headerMocks.useUnreadCount.mockReturnValue({ data: 3 });
  });

  it('renders_polished_header_surface_and_controls', () => {
    render(<Header />);

    expect(screen.getByRole('banner')).toHaveClass('shadow-sm');
    expect(screen.getByLabelText('VIMS Home')).toHaveClass('rounded-xl');
    expect(screen.getByLabelText('VIMS Home').querySelector('img[src="/icons/ksm-icon-192x192.png"]')).toBeTruthy();
    expect(screen.getByText('Vessel Inspection Management System')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /notifications/i })).toHaveClass('rounded-full');
  });

  it('test_feat_notif_001_notifications_button_navigates_to_notifications_page', () => {
    render(<Header />);
    fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
    expect(headerMocks.navigate).toHaveBeenCalledWith('/notifications');
  });

  it('test_feat_notif_001_unread_badge_caps_at_99_plus', () => {
    headerMocks.useUnreadCount.mockReturnValue({ data: 120 });
    render(<Header />);
    expect(screen.getByText('99+')).toBeInTheDocument();
  });

  it('test_feat_auth_001_logout_success_redirects_to_login', async () => {
    render(<Header />);
    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));

    await waitFor(() => {
      expect(headerMocks.logout).toHaveBeenCalledTimes(1);
      expect(headerMocks.navigate).toHaveBeenCalledWith('/login', { replace: true });
    });
  });

  it('test_feat_auth_001_logout_error_still_redirects_to_login', async () => {
    headerMocks.logout.mockRejectedValueOnce(new Error('server error'));
    render(<Header />);
    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));

    await waitFor(() => {
      expect(headerMocks.navigate).toHaveBeenCalledWith('/login', { replace: true });
    });
  });
});

