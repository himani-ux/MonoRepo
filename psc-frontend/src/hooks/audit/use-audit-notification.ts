import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auditApi } from '@/lib/api/audit';
import type {
  AuditFailedNotificationList,
  AuditNotificationDelivery,
  AuditNotificationOfflineData,
} from '@/schemas/audit/notification';

export const FAILED_AUDIT_NOTIFICATION_POLL_MS = 60_000;

export const auditNotificationKeys = {
  all: ['audit', 'notifications'] as const,
  failed: () => [...auditNotificationKeys.all, 'failed'] as const,
};

export function useFailedAuditNotifications() {
  return useQuery<AuditFailedNotificationList, Error>({
    queryKey: auditNotificationKeys.failed(),
    queryFn: auditApi.getFailedAuditNotifications,
    refetchInterval: FAILED_AUDIT_NOTIFICATION_POLL_MS,
  });
}

export function useRetryAuditNotification() {
  const queryClient = useQueryClient();

  return useMutation<AuditNotificationDelivery, Error, string>({
    mutationFn: auditApi.retryAuditNotification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditNotificationKeys.failed() });
    },
  });
}

export function useMarkAuditNotificationOffline() {
  const queryClient = useQueryClient();

  return useMutation<AuditNotificationDelivery, Error, { id: string; data: AuditNotificationOfflineData }>({
    mutationFn: ({ id, data }) => auditApi.markAuditNotificationOffline(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditNotificationKeys.failed() });
    },
  });
}
