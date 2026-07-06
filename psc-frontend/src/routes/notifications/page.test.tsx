/**
 * Tests for FEAT-NOTIF-001 route behavior on Notification Center page.
 *
 * PRD Reference: Docs/PRD.md Section 2.7 - FEAT-NOTIF-001
 * Flow Reference: Docs/APP_FLOW.md Section 2.6 (Notification Center)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

const notificationsPageMocks = vi.hoisted(() => ({
  useNotifications: vi.fn(),
  useMarkRead: vi.fn(),
  useMarkAllRead: vi.fn(),
  markReadMutate: vi.fn(),
  markAllReadMutate: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  notificationListProps: null as any,
}));

vi.mock('@/hooks/use-notifications', () => ({
  useNotifications: (opts: unknown) => notificationsPageMocks.useNotifications(opts),
  useMarkRead: () => notificationsPageMocks.useMarkRead(),
  useMarkAllRead: () => notificationsPageMocks.useMarkAllRead(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: {
      success: notificationsPageMocks.toastSuccess,
      error: notificationsPageMocks.toastError,
    },
  }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({
    title,
    actions,
  }: {
    title: string;
    actions?: React.ReactNode;
  }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
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

vi.mock('@/components/notification/notification-list', () => ({
  NotificationList: (props: any) => {
    notificationsPageMocks.notificationListProps = props;
    return (
      <div>
        <button type="button" onClick={() => props.onMarkRead?.('n-1')}>
          Trigger Mark Read
        </button>
        <button type="button" onClick={props.onLoadMore}>
          Trigger Load More
        </button>
      </div>
    );
  },
}));

import NotificationsPage from './page';

function buildNotification(id: string, isRead = false) {
  return {
    id,
    recipient_type: 'OFFICE',
    recipient_id: 'EMP001',
    vessel_id: null,
    notification_type: 'CAR_SUBMITTED',
    title: 'Notice',
    message: 'Message',
    entity_type: 'CAR',
    entity_id: 'car-1',
    is_read: isRead,
    read_at: null,
    created_date: new Date().toISOString(),
  } as any;
}

describe('NotificationsPage', () => {
  beforeEach(() => {
    notificationsPageMocks.useNotifications.mockReset();
    notificationsPageMocks.useMarkRead.mockReset();
    notificationsPageMocks.useMarkAllRead.mockReset();
    notificationsPageMocks.markReadMutate.mockReset();
    notificationsPageMocks.markAllReadMutate.mockReset();
    notificationsPageMocks.toastSuccess.mockReset();
    notificationsPageMocks.toastError.mockReset();
    notificationsPageMocks.notificationListProps = null;

    notificationsPageMocks.useNotifications.mockReturnValue({
      data: {
        data: [buildNotification('n-1', false), buildNotification('n-2', true)],
        pagination: { total_pages: 2 },
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    notificationsPageMocks.useMarkRead.mockReturnValue({
      mutate: notificationsPageMocks.markReadMutate,
    });
    notificationsPageMocks.useMarkAllRead.mockReturnValue({
      mutate: notificationsPageMocks.markAllReadMutate,
      isPending: false,
    });
  });

  it('test_feat_notif_001_mark_all_read_calls_mutation_and_shows_success_toast', async () => {
    notificationsPageMocks.markAllReadMutate.mockImplementation(
      (_arg: unknown, opts: { onSuccess?: (r: any) => void }) => {
        opts?.onSuccess?.({ data: { marked_count: 1 } });
      }
    );

    render(<NotificationsPage />, { wrapper: MemoryRouter });
    fireEvent.click(screen.getByRole('button', { name: 'Mark All Read' }));

    await waitFor(() => {
      expect(notificationsPageMocks.markAllReadMutate).toHaveBeenCalledTimes(1);
      expect(notificationsPageMocks.toastSuccess).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'All read',
        })
      );
    });
  });

  it('test_feat_notif_001_mark_read_passes_selected_notification_id', () => {
    render(<NotificationsPage />, { wrapper: MemoryRouter });

    fireEvent.click(screen.getByRole('button', { name: 'Trigger Mark Read' }));

    expect(notificationsPageMocks.markReadMutate).toHaveBeenCalledWith(['n-1']);
  });

  it('test_feat_notif_001_load_more_requests_next_page', async () => {
    render(<NotificationsPage />, { wrapper: MemoryRouter });
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Load More' }));

    await waitFor(() => {
      expect(notificationsPageMocks.useNotifications).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2, pageSize: 20 })
      );
    });
  });

  it('test_feat_notif_001_hides_mark_all_read_when_all_notifications_are_read', () => {
    notificationsPageMocks.useNotifications.mockReturnValue({
      data: {
        data: [buildNotification('n-1', true), buildNotification('n-2', true)],
        pagination: { total_pages: 1 },
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<NotificationsPage />, { wrapper: MemoryRouter });

    expect(screen.queryByRole('button', { name: 'Mark All Read' })).not.toBeInTheDocument();
  });

  it('passes the Certs module filter from the shared inbox URL', () => {
    render(
      <MemoryRouter initialEntries={['/notifications?module=certs']}>
        <NotificationsPage />
      </MemoryRouter>
    );

    expect(notificationsPageMocks.useNotifications).toHaveBeenCalledWith(
      expect.objectContaining({ module: 'certs' })
    );
  });
});
