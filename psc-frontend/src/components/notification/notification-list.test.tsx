/**
 * Tests for FEAT-NOTIF-001: In-App Notifications (Notification Center list behavior)
 *
 * PRD Reference: Docs/PRD.md Section 2.7 - FEAT-NOTIF-001
 * Flow Reference: Docs/APP_FLOW.md Section 2.6 (Notification Center)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const notificationListMocks = vi.hoisted(() => ({
  onRetry: vi.fn(),
  onMarkRead: vi.fn(),
  onLoadMore: vi.fn(),
}));

vi.mock('./notification-item', () => ({
  NotificationItem: ({ notification, onMarkRead }: any) => (
    <button
      type="button"
      data-testid={`notification-item-${notification.id}`}
      onClick={() => onMarkRead?.(notification.id)}
    >
      {notification.title}
    </button>
  ),
}));

import { NotificationList } from './notification-list';

function isoDaysOffset(days: number): string {
  return new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString();
}

function buildNotification(id: string, createdDate: string, title = 'Notice') {
  return {
    id,
    recipient_type: 'OFFICE',
    recipient_id: 'EMP001',
    vessel_id: null,
    notification_type: 'CAR_SUBMITTED',
    title,
    message: title,
    entity_type: 'CAR',
    entity_id: 'car-1',
    is_read: false,
    read_at: null,
    created_date: createdDate,
  } as any;
}

describe('NotificationList', () => {
  it('test_feat_notif_001_loading_state_shows_skeleton_items', () => {
    const { container } = render(
      <NotificationList
        notifications={[]}
        isLoading
        isError={false}
      />
    );

    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThanOrEqual(5);
  });

  it('test_feat_notif_001_error_state_shows_retry_and_calls_on_retry', () => {
    render(
      <NotificationList
        notifications={[]}
        isLoading={false}
        isError
        error={new Error('Network timeout')}
        onRetry={notificationListMocks.onRetry}
      />
    );

    expect(screen.getByText('Failed to load notifications')).toBeInTheDocument();
    expect(screen.getByText('Network timeout')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(notificationListMocks.onRetry).toHaveBeenCalledTimes(1);
  });

  it('test_feat_notif_001_empty_state_shows_no_notifications_message', () => {
    render(
      <NotificationList
        notifications={[]}
        isLoading={false}
        isError={false}
      />
    );

    expect(screen.getByText('No notifications')).toBeInTheDocument();
  });

  it('test_feat_notif_001_groups_notifications_by_today_yesterday_and_earlier', () => {
    const notifications = [
      buildNotification('n1', isoDaysOffset(0), 'Today notice'),
      buildNotification('n2', isoDaysOffset(-1), 'Yesterday notice'),
      buildNotification('n3', isoDaysOffset(-3), 'Earlier notice'),
    ];

    render(
      <NotificationList
        notifications={notifications}
        isLoading={false}
        isError={false}
      />
    );

    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Yesterday')).toBeInTheDocument();
    expect(screen.getByText('Earlier')).toBeInTheDocument();
    expect(screen.getByText('Today notice')).toBeInTheDocument();
    expect(screen.getByText('Yesterday notice')).toBeInTheDocument();
    expect(screen.getByText('Earlier notice')).toBeInTheDocument();
  });

  it('test_feat_notif_001_happy_path_item_click_calls_on_mark_read', () => {
    render(
      <NotificationList
        notifications={[buildNotification('n1', isoDaysOffset(0), 'Mark Me')]}
        isLoading={false}
        isError={false}
        onMarkRead={notificationListMocks.onMarkRead}
      />
    );

    fireEvent.click(screen.getByTestId('notification-item-n1'));
    expect(notificationListMocks.onMarkRead).toHaveBeenCalledWith('n1');
  });

  it('test_feat_notif_001_pagination_renders_load_more_and_calls_handler', () => {
    render(
      <NotificationList
        notifications={[buildNotification('n1', isoDaysOffset(0), 'Paged')]}
        isLoading={false}
        isError={false}
        hasMore
        onLoadMore={notificationListMocks.onLoadMore}
        isLoadingMore={false}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load more' }));
    expect(notificationListMocks.onLoadMore).toHaveBeenCalledTimes(1);
  });
});

