/**
 * Notification hooks using TanStack Query.
 *
 * Per FRONTEND_GUIDELINES.md Section 4.1
 * Implements: PRD.md FEAT-NOTIF-001
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getNotifications,
  getUnreadCount,
  markNotificationsRead,
  markAllNotificationsRead,
  type NotificationPaginatedResponse,
} from '@/lib/api/notifications';
import { STALE_TIME, DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';
import { useAuth } from '@/hooks/use-auth';

// ============================================================================
// Query Key Factory
// ============================================================================

export const notificationKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationKeys.all, 'list'] as const,
  list: (scopeKey: string, page: number, pageSize: number, isRead?: boolean, module?: 'certs') =>
    [...notificationKeys.lists(), scopeKey, { page, pageSize, isRead, module }] as const,
  unreadCount: (scopeKey: string) => [...notificationKeys.all, 'unread-count', scopeKey] as const,
};

function getNotificationScopeKey(user: {
  user_type?: string | null;
  employee_id?: string | null;
  crew_id?: string | null;
} | null): string | null {
  if (!user) return null;
  const userType = (user.user_type || '').toLowerCase();
  if (userType === 'office') {
    const employeeId = user.employee_id?.trim();
    return employeeId ? `office:${employeeId}` : null;
  }
  if (userType === 'vessel') {
    const crewId = user.crew_id?.trim();
    return crewId ? `crew:${crewId}` : null;
  }
  return null;
}

// ============================================================================
// List Hook
// ============================================================================

export interface UseNotificationsOptions {
  page?: number;
  pageSize?: number;
  isRead?: boolean;
  module?: 'certs';
  enabled?: boolean;
}

/**
 * Hook to fetch paginated list of notifications.
 */
export function useNotifications(options: UseNotificationsOptions = {}) {
  const { user, isAuthenticated, isInitialized } = useAuth();
  const {
    page = 1,
    pageSize = DEFAULT_PAGE_SIZE,
    isRead,
    module,
    enabled = true,
  } = options;
  const scopeKey = getNotificationScopeKey(user);
  const queryEnabled = enabled && isInitialized && isAuthenticated && Boolean(scopeKey);

  return useQuery<NotificationPaginatedResponse>({
    queryKey: notificationKeys.list(scopeKey ?? 'anonymous', page, pageSize, isRead, module),
    queryFn: () => getNotifications(page, pageSize, isRead, module),
    staleTime: STALE_TIME.NOTIFICATIONS,
    refetchOnMount: 'always',
    enabled: queryEnabled,
  });
}

// ============================================================================
// Unread Count Hook
// ============================================================================

/**
 * Hook to fetch unread notification count.
 * Polls every 60 seconds for fresh data.
 */
export function useUnreadCount(enabled = true) {
  const { user, isAuthenticated, isInitialized } = useAuth();
  const scopeKey = getNotificationScopeKey(user);
  const queryEnabled = enabled && isInitialized && isAuthenticated && Boolean(scopeKey);

  return useQuery<number>({
    queryKey: notificationKeys.unreadCount(scopeKey ?? 'anonymous'),
    queryFn: getUnreadCount,
    staleTime: STALE_TIME.NOTIFICATIONS,
    refetchInterval: 60 * 1000, // Poll every 60s
    refetchOnMount: 'always',
    enabled: queryEnabled,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook to mark specific notifications as read.
 */
export function useMarkRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationIds: string[]) =>
      markNotificationsRead(notificationIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

/**
 * Hook to mark all notifications as read.
 */
export function useMarkAllRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}
