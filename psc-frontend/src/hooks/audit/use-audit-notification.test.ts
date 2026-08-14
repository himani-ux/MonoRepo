import { describe, expect, it, vi } from 'vitest';

const queryMocks = vi.hoisted(() => ({
  invalidateQueries: vi.fn(),
  useMutation: vi.fn(),
  useQuery: vi.fn(),
}));

vi.mock('@tanstack/react-query', () => ({
  useMutation: (options: unknown) => queryMocks.useMutation(options),
  useQuery: (options: unknown) => queryMocks.useQuery(options),
  useQueryClient: () => ({ invalidateQueries: queryMocks.invalidateQueries }),
}));

import {
  FAILED_AUDIT_NOTIFICATION_POLL_MS,
  auditNotificationKeys,
  useFailedAuditNotifications,
  useMarkAuditNotificationOffline,
  useRetryAuditNotification,
} from './use-audit-notification';

describe('use-audit-notification hooks', () => {
  it('configures failed notifications to poll every 60 seconds', () => {
    queryMocks.useQuery.mockReturnValue({ data: undefined });

    useFailedAuditNotifications();

    expect(queryMocks.useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: auditNotificationKeys.failed(),
        refetchInterval: FAILED_AUDIT_NOTIFICATION_POLL_MS,
      })
    );
    expect(FAILED_AUDIT_NOTIFICATION_POLL_MS).toBe(60000);
  });

  it('invalidates the failed queue after retry or offline mutation success', () => {
    queryMocks.useMutation.mockReturnValue({ mutateAsync: vi.fn() });

    useRetryAuditNotification();
    const retryOptions = queryMocks.useMutation.mock.calls[0][0];
    retryOptions.onSuccess();

    useMarkAuditNotificationOffline();
    const offlineOptions = queryMocks.useMutation.mock.calls[1][0];
    offlineOptions.onSuccess();

    expect(queryMocks.invalidateQueries).toHaveBeenCalledTimes(2);
    expect(queryMocks.invalidateQueries).toHaveBeenCalledWith({
      queryKey: auditNotificationKeys.failed(),
    });
  });
});
