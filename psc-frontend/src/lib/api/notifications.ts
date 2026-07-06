/**
 * Notification API functions
 *
 * Handles all notification-related API calls per BACKEND_STRUCTURE.md Section 10.11.
 * Implements: PRD.md FEAT-NOTIF-001
 */

import { apiClient } from './client';
import type { Notification } from '@/types';
import { DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';

// ============================================================================
// Response Types (matching actual backend format)
// ============================================================================

/** Paginated response format from notification backend views */
export interface NotificationPaginatedResponse {
  data: Notification[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}

/** Response for mark-read and mark-all-read */
export interface MarkReadResponse {
  data: { marked_count: number };
  message: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get paginated list of notifications for the authenticated user.
 *
 * GET /api/psc/notifications/?is_read=false&page=1&page_size=20
 */
export async function getNotifications(
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE,
  isRead?: boolean,
  module?: 'certs'
): Promise<NotificationPaginatedResponse> {
  const params = new URLSearchParams();
  params.set('page', page.toString());
  params.set('page_size', pageSize.toString());

  if (isRead !== undefined) {
    params.set('is_read', isRead.toString());
  }
  if (module) {
    params.set('module', module);
  }

  const path = module === 'certs' ? '/certs/notifications/' : '/notifications/';
  const response = await apiClient.get<NotificationPaginatedResponse>(
    `${path}?${params.toString()}`
  );
  return response.data;
}

/**
 * Get unread notification count.
 * Uses page_size=1 to minimize data transfer.
 */
export async function getUnreadCount(): Promise<number> {
  const response = await apiClient.get<NotificationPaginatedResponse>(
    '/notifications/?is_read=false&page=1&page_size=1'
  );
  return response.data.pagination.total_count;
}

/**
 * Mark specific notifications as read.
 *
 * POST /api/psc/notifications/mark-read/
 */
export async function markNotificationsRead(
  notificationIds: string[]
): Promise<MarkReadResponse> {
  const response = await apiClient.post<MarkReadResponse>(
    '/notifications/mark-read/',
    { notification_ids: notificationIds }
  );
  return response.data;
}

/**
 * Mark all notifications as read.
 *
 * POST /api/psc/notifications/mark-all-read/
 */
export async function markAllNotificationsRead(): Promise<MarkReadResponse> {
  const response = await apiClient.post<MarkReadResponse>(
    '/notifications/mark-all-read/'
  );
  return response.data;
}
