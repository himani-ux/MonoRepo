/**
 * Tests for FEAT-AUTH-001 login form behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.5 - FEAT-AUTH-001
 * Flow Reference: Docs/APP_FLOW.md Section 2.1 (Login)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const loginFormMocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  login: vi.fn(),
  getErrorMessage: vi.fn(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => loginFormMocks.useAuth(),
}));

vi.mock('@/lib/api/client', () => ({
  getErrorMessage: (err: unknown) => loginFormMocks.getErrorMessage(err),
}));

import { LoginForm } from './login-form';

describe('LoginForm', () => {
  beforeEach(() => {
    loginFormMocks.useAuth.mockReset();
    loginFormMocks.login.mockReset();
    loginFormMocks.getErrorMessage.mockReset();

    loginFormMocks.useAuth.mockReturnValue({
      login: loginFormMocks.login,
      isLoading: false,
    });
    loginFormMocks.getErrorMessage.mockImplementation((err: any) => err?.message ?? 'unknown');
  });

  it('test_feat_auth_001_required_field_validation_blocks_submit_when_empty', async () => {
    render(<LoginForm />);

    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    expect(await screen.findByText('Username is required')).toBeInTheDocument();
    expect(await screen.findByText('Password is required')).toBeInTheDocument();
    expect(loginFormMocks.login).not.toHaveBeenCalled();
  });

  it('test_feat_auth_001_successful_login_calls_auth_and_onsuccess', async () => {
    const onSuccess = vi.fn();
    loginFormMocks.login.mockResolvedValue({});

    render(<LoginForm onSuccess={onSuccess} />);

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'master1' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'secret' } });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(loginFormMocks.login).toHaveBeenCalledWith({
        username: 'master1',
        password: 'secret',
      });
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it('test_feat_auth_001_invalid_credentials_error_is_mapped_to_user_friendly_message', async () => {
    loginFormMocks.login.mockRejectedValue(new Error('401 invalid credentials'));
    loginFormMocks.getErrorMessage.mockReturnValue('invalid credentials');

    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'bad' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument();
  });

  it('test_feat_auth_001_password_visibility_toggle_switches_input_type', () => {
    render(<LoginForm />);

    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');

    fireEvent.click(screen.getByRole('button', { name: /show password/i }));
    expect(passwordInput.type).toBe('text');

    fireEvent.click(screen.getByRole('button', { name: /hide password/i }));
    expect(passwordInput.type).toBe('password');
  });
});

