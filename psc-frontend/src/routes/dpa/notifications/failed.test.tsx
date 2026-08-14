import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type {
  AuditFailedNotificationList,
  AuditNotificationDelivery,
} from '@/schemas/audit/notification';

const failedNotificationMocks = vi.hoisted(() => ({
  useFailedAuditNotifications: vi.fn(),
  useRetryAuditNotification: vi.fn(),
  useMarkAuditNotificationOffline: vi.fn(),
  retryNotification: vi.fn(),
  markOffline: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('@/hooks/audit/use-audit-notification', () => ({
  useFailedAuditNotifications: () => failedNotificationMocks.useFailedAuditNotifications(),
  useRetryAuditNotification: () => failedNotificationMocks.useRetryAuditNotification(),
  useMarkAuditNotificationOffline: () => failedNotificationMocks.useMarkAuditNotificationOffline(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: failedNotificationMocks.toast }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => (
    <header>
      <h1>{title}</h1>
    </header>
  ),
}));

vi.mock('@/components/shared', () => ({
  ErrorState: ({ title, onRetry }: { title: string; onRetry: () => void }) => (
    <div>
      <div>{title}</div>
      <button type="button" onClick={onRetry}>Retry load</button>
    </div>
  ),
}));

vi.mock('@/components/shared/loading-skeleton', () => ({
  SectionSkeleton: () => <div>Section Skeleton</div>,
}));

import AuditFailedNotificationQueueRoute from './failed';

function sampleDelivery(overrides: Partial<AuditNotificationDelivery> = {}): AuditNotificationDelivery {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    psc_notification_id: '22222222222242228222222222222222',
    notification_type: 'AUDIT_OVERDUE',
    title: 'Audit overdue',
    message: 'Internal audit is overdue.',
    entity_type: 'AUDIT_PLAN',
    entity_id: '33333333-3333-4333-8333-333333333333',
    vessel_id: '44444444-4444-4444-8444-444444444444',
    recipient_type: 'CREW',
    recipient_id: 'MASTER001',
    channel: 'EMAIL',
    recipient_address: 'master@example.test',
    status: 'FAILED_PERMANENT',
    attempt_count: 3,
    first_attempted_at: '2026-08-06T09:00:00+05:30',
    last_attempted_at: '2026-08-06T09:03:00+05:30',
    last_error: 'CMS_NO_EMAIL_ON_FILE',
    sent_at: null,
    resolved_offline_reason: null,
    created_date: '2026-08-06T09:00:00+05:30',
    ...overrides,
  };
}

function sampleList(results: AuditNotificationDelivery[] = [sampleDelivery()]): AuditFailedNotificationList {
  return {
    count: results.length,
    results,
  };
}

describe('AuditFailedNotificationQueueRoute', () => {
  beforeEach(() => {
    failedNotificationMocks.useFailedAuditNotifications.mockReset();
    failedNotificationMocks.useRetryAuditNotification.mockReset();
    failedNotificationMocks.useMarkAuditNotificationOffline.mockReset();
    failedNotificationMocks.retryNotification.mockReset();
    failedNotificationMocks.markOffline.mockReset();
    failedNotificationMocks.toast.mockReset();

    failedNotificationMocks.retryNotification.mockResolvedValue(sampleDelivery({ status: 'QUEUED' }));
    failedNotificationMocks.markOffline.mockResolvedValue(sampleDelivery({ status: 'RESOLVED_OFFLINE' }));
    failedNotificationMocks.useRetryAuditNotification.mockReturnValue({
      mutateAsync: failedNotificationMocks.retryNotification,
      isPending: false,
    });
    failedNotificationMocks.useMarkAuditNotificationOffline.mockReturnValue({
      mutateAsync: failedNotificationMocks.markOffline,
      isPending: false,
    });
  });

  it('renders failed notification rows with actions', async () => {
    failedNotificationMocks.useFailedAuditNotifications.mockReturnValue({
      data: sampleList([
        sampleDelivery(),
        sampleDelivery({
          id: '55555555-5555-4555-8555-555555555555',
          notification_type: 'AUDIT_NC_RAISED',
          channel: 'SLACK',
          recipient_address: '#audit-mvt',
          last_error: 'SLACK_WEBHOOK_HTTP_404',
        }),
      ]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditFailedNotificationQueueRoute />);

    expect(await screen.findByRole('heading', { name: 'Failed Notifications' })).toBeInTheDocument();
    expect(screen.getByText('AUDIT_OVERDUE')).toBeInTheDocument();
    expect(screen.getByText('AUDIT_NC_RAISED')).toBeInTheDocument();
    expect(screen.getByText('CMS_NO_EMAIL_ON_FILE')).toBeInTheDocument();
    expect(screen.getByText('SLACK_WEBHOOK_HTTP_404')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /retry/i })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: /mark notified offline/i })).toHaveLength(2);
  });

  it('queues manual retry for a failed row', async () => {
    failedNotificationMocks.useFailedAuditNotifications.mockReturnValue({
      data: sampleList(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditFailedNotificationQueueRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /^retry$/i }));

    await waitFor(() => {
      expect(failedNotificationMocks.retryNotification).toHaveBeenCalledWith('11111111-1111-4111-8111-111111111111');
      expect(failedNotificationMocks.toast).toHaveBeenCalledWith({ title: 'Notification queued for retry' });
    });
  });

  it('validates the offline reason minimum before submitting', async () => {
    failedNotificationMocks.useFailedAuditNotifications.mockReturnValue({
      data: sampleList(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditFailedNotificationQueueRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /mark notified offline/i }));
    fireEvent.change(screen.getByLabelText('Offline resolution reason'), { target: { value: 'too short' } });
    fireEvent.click(screen.getByRole('button', { name: /save offline resolution/i }));

    expect(await screen.findByText('Reason must be at least 30 characters.')).toBeInTheDocument();
    expect(failedNotificationMocks.markOffline).not.toHaveBeenCalled();
  });

  it('marks a failed notification row notified offline', async () => {
    failedNotificationMocks.useFailedAuditNotifications.mockReturnValue({
      data: sampleList(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditFailedNotificationQueueRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /mark notified offline/i }));
    fireEvent.change(screen.getByLabelText('Offline resolution reason'), {
      target: { value: 'DPA confirmed the Master was notified by direct phone and email.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save offline resolution/i }));

    await waitFor(() => {
      expect(failedNotificationMocks.markOffline).toHaveBeenCalledWith({
        id: '11111111-1111-4111-8111-111111111111',
        data: { reason: 'DPA confirmed the Master was notified by direct phone and email.' },
      });
      expect(failedNotificationMocks.toast).toHaveBeenCalledWith({
        title: 'Notification marked notified offline',
      });
    });
  });

  it('shows an error state when the queue query fails', () => {
    const refetch = vi.fn();
    failedNotificationMocks.useFailedAuditNotifications.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Forbidden'),
      refetch,
    });

    render(<AuditFailedNotificationQueueRoute />);

    expect(screen.getByText('Failed notifications not available')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /retry load/i }));
    expect(refetch).toHaveBeenCalled();
  });
});
