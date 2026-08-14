import { useQuery } from '@tanstack/react-query';
import { auditApi } from '@/lib/api/audit';
import type { AuditChecklist } from '@/schemas/audit/checklist';
import { auditKeys } from './use-audit-registration';

export const auditChecklistKeys = {
  checklist: (id: string | undefined) => [...auditKeys.detail(id), 'checklist'] as const,
};

export function useAuditChecklist(id: string | undefined) {
  return useQuery<AuditChecklist, Error>({
    queryKey: auditChecklistKeys.checklist(id),
    queryFn: () => auditApi.getAuditChecklist(id!),
    enabled: Boolean(id),
  });
}
