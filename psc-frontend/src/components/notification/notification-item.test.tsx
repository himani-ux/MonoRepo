/**
 * Tests for FEAT-NOTIF-001: Notification item interactions and deep linking
 *
 * PRD Reference: Docs/PRD.md Section 2.7 - FEAT-NOTIF-001
 * Flow Reference: Docs/APP_FLOW.md Section 2.6 (Notification Center)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const notificationItemMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  onMarkRead: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => notificationItemMocks.navigate,
}));

import { NotificationItem } from './notification-item';

function buildNotification(overrides: Record<string, unknown> = {}) {
  return {
    id: 'n1',
    recipient_type: 'OFFICE',
    recipient_id: 'EMP001',
    vessel_id: null,
    notification_type: 'CAR_SUBMITTED',
    title: 'CAR submitted',
    message: 'CAR submitted',
    entity_type: 'CAR',
    entity_id: '321',
    is_read: false,
    read_at: null,
    created_date: '2026-02-08T12:00:00Z',
    ...overrides,
  } as any;
}

describe('NotificationItem', () => {
  beforeEach(() => {
    notificationItemMocks.navigate.mockReset();
    notificationItemMocks.onMarkRead.mockReset();
  });

  it('test_feat_notif_001_unread_notification_click_marks_read_and_navigates_to_car', () => {
    render(
      <NotificationItem
        notification={buildNotification()}
        onMarkRead={notificationItemMocks.onMarkRead}
      />
    );

    fireEvent.click(
      screen.getByRole('button', { name: /Unread: CAR submitted/i })
    );

    expect(notificationItemMocks.onMarkRead).toHaveBeenCalledWith('n1');
    expect(notificationItemMocks.navigate).toHaveBeenCalledWith('/cars/321');
  });

  it('test_feat_notif_001_read_notification_click_navigates_without_mark_read', () => {
    render(
      <NotificationItem
        notification={buildNotification({ is_read: true })}
        onMarkRead={notificationItemMocks.onMarkRead}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /CAR submitted/i }));
    expect(notificationItemMocks.onMarkRead).not.toHaveBeenCalled();
    expect(notificationItemMocks.navigate).toHaveBeenCalledWith('/cars/321');
  });

  it('test_feat_notif_001_inspection_entity_notification_navigates_to_inspection_detail', () => {
    render(
      <NotificationItem
        notification={buildNotification({
          entity_type: 'INSPECTION',
          entity_id: '555',
        })}
        onMarkRead={notificationItemMocks.onMarkRead}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /CAR submitted/i }));
    expect(notificationItemMocks.navigate).toHaveBeenCalledWith('/inspections/555');
  });

  it('test_feat_notif_001_unknown_or_missing_entity_does_not_navigate', () => {
    render(
      <NotificationItem
        notification={buildNotification({
          entity_type: 'SYNC',
          entity_id: 'x-1',
        })}
        onMarkRead={notificationItemMocks.onMarkRead}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Unread: CAR submitted/i }));
    expect(notificationItemMocks.navigate).not.toHaveBeenCalled();
  });

  it('test_feat_notif_001_message_line_hidden_when_message_equals_title_and_shown_when_different', () => {
    const { rerender } = render(
      <NotificationItem
        notification={buildNotification({ title: 'Same', message: 'Same' })}
      />
    );

    expect(screen.queryByText('Same', { selector: 'p.text-xs.text-neutral-500' })).not.toBeInTheDocument();

    rerender(
      <NotificationItem
        notification={buildNotification({
          title: 'Title',
          message: 'Detailed message',
        })}
      />
    );

    expect(screen.getByText('Detailed message')).toBeInTheDocument();
  });

  it('test_feat_notif_001_invalid_created_date_falls_back_to_raw_string', () => {
    render(
      <NotificationItem
        notification={buildNotification({
          created_date: 'invalid-date-value',
        })}
      />
    );

    expect(screen.getByText('invalid-date-value')).toBeInTheDocument();
  });
});

