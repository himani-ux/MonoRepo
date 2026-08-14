import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auditApi } from '@/lib/api/audit';
import type {
  AuditScanValidationActionData,
  AuditScanValidationAttachment,
  AuditScanValidationQueue,
} from '@/schemas/audit/scan-validation';

export const auditScanValidationKeys = {
  all: ['audit', 'scan-validation'] as const,
  queue: () => [...auditScanValidationKeys.all, 'queue'] as const,
};

export function useAuditScanValidationQueue() {
  return useQuery<AuditScanValidationQueue, Error>({
    queryKey: auditScanValidationKeys.queue(),
    queryFn: auditApi.getAuditScanValidationQueue,
  });
}

export function useAuditScanValidationAction() {
  const queryClient = useQueryClient();

  return useMutation<AuditScanValidationAttachment, Error, { id: string; data: AuditScanValidationActionData }>({
    mutationFn: ({ id, data }) => auditApi.validateAuditScanAction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditScanValidationKeys.queue() });
    },
  });
}
