/**
 * Tests for use-notifications hooks (TanStack Query)
 *
 * PRD Reference: PRD.md FEAT-NOTIF-001
 * Validation Reference: FRONTEND_GUIDELINES.md Section 4.1
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// ============================================================================
// MOCKS
// ============================================================================

const notifApiMock = vi.hoisted(() => ({
  getNotifications: vi.fn(),
  getUnreadCount: vi.fn(),
  markNotificationsRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}));
const authHookMock = vi.hoisted(() => ({
  useAuth: vi.fn(),
}));

vi.mock('@/lib/api/notifications', () => ({
  getNotifications: notifApiMock.getNotifications,
  getUnreadCount: notifApiMock.getUnreadCount,
  markNotificationsRead: notifApiMock.markNotificationsRead,
  markAllNotificationsRead: notifApiMock.markAllNotificationsRead,
}));
vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => authHookMock.useAuth(),
}));

import {
  notificationKeys,
  useNotifications,
  useUnreadCount,
  useMarkRead,
  useMarkAllRead,
} from './use-notifications';

// ============================================================================
// HELPERS
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

// ============================================================================
// SETUP
// ============================================================================

beforeEach(() => {
  vi.clearAllMocks();
  authHookMock.useAuth.mockReturnValue({
    user: {
      user_type: 'office',
      employee_id: 'EMP001',
      crew_id: null,
    },
    isAuthenticated: true,
    isInitialized: true,
  });
});

// ============================================================================
// Query Key Factory
// ============================================================================

describe('notificationKeys factory', () => {
  it('all is ["notifications"]', () => {
    expect(notificationKeys.all).toEqual(['notifications']);
  });

  it('lists appends "list"', () => {
    expect(notificationKeys.lists()).toEqual(['notifications', 'list']);
  });

  it('list includes scopeKey, page, pageSize, isRead', () => {
    expect(notificationKeys.list('office:EMP001', 1, 20, true)).toEqual([
      'notifications',
      'list',
      'office:EMP001',
      { page: 1, pageSize: 20, isRead: true },
    ]);
  });

  it('unreadCount key', () => {
    expect(notificationKeys.unreadCount('office:EMP001')).toEqual([
      'notifications',
      'unread-count',
      'office:EMP001',
    ]);
  });
});

// ============================================================================
// useNotifications
// ============================================================================

describe('useNotifications', () => {
  it('calls getNotifications with params', async () => {
    notifApiMock.getNotifications.mockResolvedValue({
      data: [],
      pagination: { page: 1, page_size: 20, total_count: 0, total_pages: 1 },
    });

    const { result } = renderHook(
      () => useNotifications({ page: 2, pageSize: 10, isRead: false }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(notifApiMock.getNotifications).toHaveBeenCalledWith(2, 10, false);
  });

  it('is disabled when enabled=false', () => {
    const { result } = renderHook(
      () => useNotifications({ enabled: false }),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe('idle');
    expect(notifApiMock.getNotifications).not.toHaveBeenCalled();
  });

  it('is disabled when auth is not initialized/authenticated', () => {
    authHookMock.useAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isInitialized: false,
    });
    const { result } = renderHook(
      () => useNotifications({}),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe('idle');
    expect(notifApiMock.getNotifications).not.toHaveBeenCalled();
  });

  it('is disabled when user scope key cannot be resolved', () => {
    authHookMock.useAuth.mockReturnValue({
      user: {
        user_type: 'office',
        employee_id: null,
        crew_id: null,
      },
      isAuthenticated: true,
      isInitialized: true,
    });
    const { result } = renderHook(
      () => useNotifications({}),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe('idle');
    expect(notifApiMock.getNotifications).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useUnreadCount
// ============================================================================

describe('useUnreadCount', () => {
  it('calls getUnreadCount', async () => {
    notifApiMock.getUnreadCount.mockResolvedValue(5);

    const { result } = renderHook(() => useUnreadCount(true), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe(5);
  });

  it('is disabled when enabled=false', () => {
    const { result } = renderHook(() => useUnreadCount(false), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(notifApiMock.getUnreadCount).not.toHaveBeenCalled();
  });

  it('is disabled when auth is not initialized/authenticated', () => {
    authHookMock.useAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isInitialized: false,
    });
    const { result } = renderHook(() => useUnreadCount(true), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(notifApiMock.getUnreadCount).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useMarkRead
// ============================================================================

describe('useMarkRead', () => {
  it('calls markNotificationsRead with ids', async () => {
    notifApiMock.markNotificationsRead.mockResolvedValue({ updated: 2 });

    const { result } = renderHook(() => useMarkRead(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(['n-1', 'n-2']);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(notifApiMock.markNotificationsRead).toHaveBeenCalledWith(['n-1', 'n-2']);
  });
});

// ============================================================================
// useMarkAllRead
// ============================================================================

describe('useMarkAllRead', () => {
  it('calls markAllNotificationsRead', async () => {
    notifApiMock.markAllNotificationsRead.mockResolvedValue({ updated: 10 });

    const { result } = renderHook(() => useMarkAllRead(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(notifApiMock.markAllNotificationsRead).toHaveBeenCalled();
  });
});
