import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const sessionReauthMocks = vi.hoisted(() => ({
  toastWarning: vi.fn(),
}));

vi.mock('@/hooks/use-toast', () => ({
  toast: {
    warning: sessionReauthMocks.toastWarning,
  },
}));

import { useSessionReauth } from './use-session-reauth';
import {
  OFFICE_IDLE_TIMEOUT_MS,
  SESSION_WARNING_THRESHOLDS_MS,
  useAuthStore,
} from '@/stores/auth-store';

function officeUser() {
  return {
    id: 'office-1',
    user_type: 'office' as const,
    full_name: 'DPA User',
    role: 'DPA',
    vessel_id: null,
    vessel_code: null,
    email: 'dpa@example.com',
    employee_id: 'EMP-44',
    crew_id: null,
    rank: null,
    form_ids: [],
    process_ids: [],
  };
}

function Harness() {
  const session = useSessionReauth();
  return (
    <div>
      <span>{session.isReauthRequired ? 'reauth-required' : 'session-active'}</span>
      <span>{session.identifier.label}</span>
      <span>{session.identifier.value}</span>
    </div>
  );
}

function resetStore(now: number) {
  useAuthStore.setState({
    tokens: { access: 'access', refresh: 'refresh' },
    user: officeUser(),
    isAuthenticated: true,
    isLoading: false,
    isInitialized: true,
    isReauthRequired: false,
    sessionLastActivityAt: now,
  });
}

describe('useSessionReauth', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-30T08:00:00Z'));
    sessionReauthMocks.toastWarning.mockReset();
    resetStore(Date.now());
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('test_feat_cert_rbac_011_emits_15_min_and_5_min_idle_warnings', () => {
    const now = Date.now();
    resetStore(now - (OFFICE_IDLE_TIMEOUT_MS - SESSION_WARNING_THRESHOLDS_MS[0] + 1000));

    render(<Harness />);
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(sessionReauthMocks.toastWarning).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Session expires in 15 minutes',
      })
    );

    act(() => {
      useAuthStore
        .getState()
        .markSessionActivity(now - (OFFICE_IDLE_TIMEOUT_MS - SESSION_WARNING_THRESHOLDS_MS[1] + 1000));
      vi.advanceTimersByTime(1000);
    });

    expect(sessionReauthMocks.toastWarning).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Session expires in 5 minutes',
      })
    );
  });

  it('test_feat_cert_rbac_012_requires_modal_reauth_after_idle_timeout_without_unmounting_content', () => {
    const now = Date.now();
    resetStore(now - OFFICE_IDLE_TIMEOUT_MS - 1000);

    render(<Harness />);
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(screen.getByText('reauth-required')).toBeInTheDocument();
    expect(screen.getByText('Employee ID')).toBeInTheDocument();
    expect(screen.getByText('EMP-44')).toBeInTheDocument();
  });
});
