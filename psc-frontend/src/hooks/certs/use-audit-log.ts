import { useMutation, useQuery } from '@tanstack/react-query';

import { certsApi, type CertAuditLogExportPayload, type CertAuditLogFilters } from '@/lib/api/certs';

export const certAuditLogKeys = {
  all: ['certs', 'audit-log'] as const,
  list: (filters: CertAuditLogFilters = {}) => [...certAuditLogKeys.all, 'list', filters] as const,
  detail: (id: string) => [...certAuditLogKeys.all, 'detail', id] as const,
};

export function useAuditLog(filters: CertAuditLogFilters = {}, enabled = true) {
  return useQuery({
    queryKey: certAuditLogKeys.list(filters),
    queryFn: () => certsApi.getAuditLog(filters),
    enabled,
    staleTime: 30 * 1000,
  });
}

export function useAuditLogEntry(id: string | undefined) {
  return useQuery({
    queryKey: certAuditLogKeys.detail(id ?? ''),
    queryFn: () => certsApi.getAuditLogEntry(id!),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useExportAuditLog() {
  return useMutation({
    mutationFn: (payload: CertAuditLogExportPayload) => certsApi.exportAuditLog(payload),
  });
}
