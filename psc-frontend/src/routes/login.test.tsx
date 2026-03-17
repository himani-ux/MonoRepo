/**
 * Tests for FEAT-AUTH-001 route behavior on Login page.
 *
 * PRD Reference: Docs/PRD.md Section 2.5 - FEAT-AUTH-001
 * Flow Reference: Docs/APP_FLOW.md Section 2.1 (Login)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const loginPageMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useLocation: vi.fn(),
  useAuth: vi.fn(),
  loginFormOnSuccess: null as null | (() => void),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => loginPageMocks.navigate,
  useLocation: () => loginPageMocks.useLocation(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => loginPageMocks.useAuth(),
}));

vi.mock('@/components/auth/login-form', () => ({
  LoginForm: ({ onSuccess }: { onSuccess: () => void }) => {
    loginPageMocks.loginFormOnSuccess = onSuccess;
    return <button onClick={onSuccess}>Trigger Login Success</button>;
  },
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import LoginPage from './login';

describe('LoginPage', () => {
  beforeEach(() => {
    loginPageMocks.navigate.mockReset();
    loginPageMocks.useLocation.mockReset();
    loginPageMocks.useAuth.mockReset();
    loginPageMocks.loginFormOnSuccess = null;

    loginPageMocks.useLocation.mockReturnValue({ state: undefined });
  });

  it('test_feat_auth_001_loading_state_when_auth_not_initialized_shows_spinner_and_hides_form', () => {
    loginPageMocks.useAuth.mockReturnValue({
      isAuthenticated: false,
      isInitialized: false,
    });

    const { container } = render(<LoginPage />);

    expect(container.querySelector('.animate-spin')).not.toBeNull();
    expect(screen.queryByText('Sign in to your account')).not.toBeInTheDocument();
  });

  it('test_feat_auth_001_redirects_authenticated_user_to_state_from_route', async () => {
    loginPageMocks.useLocation.mockReturnValue({
      state: { from: '/cars' },
    });
    loginPageMocks.useAuth.mockReturnValue({
      isAuthenticated: true,
      isInitialized: true,
    });

    render(<LoginPage />);

    await waitFor(() => {
      expect(loginPageMocks.navigate).toHaveBeenCalledWith('/cars', { replace: true });
    });
  });

  it('test_feat_auth_001_renders_login_form_when_unauthenticated_and_initialized', () => {
    loginPageMocks.useAuth.mockReturnValue({
      isAuthenticated: false,
      isInitialized: true,
    });

    render(<LoginPage />);

    expect(screen.getByText('Sign in to your account')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Trigger Login Success' })).toBeInTheDocument();
  });

  it('test_feat_auth_001_login_success_navigates_to_default_dashboard_route', () => {
    loginPageMocks.useAuth.mockReturnValue({
      isAuthenticated: false,
      isInitialized: true,
    });

    render(<LoginPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Login Success' }));

    expect(loginPageMocks.navigate).toHaveBeenCalledWith('/dashboard', { replace: true });
  });
});
