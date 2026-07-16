import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  certsApi,
  type CertCatalogBulkSoftDeletePayload,
  type CertCatalogRowFilters,
  type CertCatalogRowInput,
} from '@/lib/api/certs';

export const certCatalogKeys = {
  all: ['certs', 'catalog'] as const,
  sections: () => [...certCatalogKeys.all, 'sections'] as const,
  rows: (filters: CertCatalogRowFilters) => [...certCatalogKeys.all, 'rows', filters] as const,
  rowsLazy: (filters: CertCatalogRowFilters, pageSize: number) => [...certCatalogKeys.all, 'rows-lazy', filters, pageSize] as const,
  detail: (id: string) => [...certCatalogKeys.all, 'row', id] as const,
  auditHistory: (id: string) => [...certCatalogKeys.all, 'row', id, 'audit'] as const,
};

export function useCatalogSections() {
  return useQuery({
    queryKey: certCatalogKeys.sections(),
    queryFn: certsApi.getCatalogSections,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCatalogRows(filters: CertCatalogRowFilters = {}) {
  return useQuery({
    queryKey: certCatalogKeys.rows(filters),
    queryFn: () => certsApi.getCatalogRows(filters),
    staleTime: 60 * 1000,
  });
}

export function useCatalogRowsLazy(filters: CertCatalogRowFilters = {}, pageSize = 50) {
  return useInfiniteQuery({
    queryKey: certCatalogKeys.rowsLazy(filters, pageSize),
    initialPageParam: 1,
    queryFn: ({ pageParam }) => certsApi.getCatalogRows({ ...filters, page: Number(pageParam), pageSize }),
    getNextPageParam: (lastPage) => {
      const currentPage = lastPage.page ?? 1;
      const currentPageSize = lastPage.pageSize ?? pageSize;
      return currentPage * currentPageSize < lastPage.count ? currentPage + 1 : undefined;
    },
    staleTime: 60 * 1000,
  });
}

export function useCatalogRow(id: string | undefined) {
  return useQuery({
    queryKey: certCatalogKeys.detail(id ?? ''),
    queryFn: () => certsApi.getCatalogRow(id!),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useCatalogRowAuditHistory(id: string | undefined) {
  return useQuery({
    queryKey: certCatalogKeys.auditHistory(id ?? ''),
    queryFn: () => certsApi.getCatalogRowAuditHistory(id!),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useCreateCatalogRow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertCatalogRowInput) => certsApi.createCatalogRow(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.all });
    },
  });
}

export function useUpdateCatalogRow(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertCatalogRowInput) => certsApi.updateCatalogRow(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.all });
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.auditHistory(id) });
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.detail(id) });
    },
  });
}

export function useDeprecateCatalogRow(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { reason: string }) => certsApi.deprecateCatalogRow(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.all });
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.auditHistory(id) });
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.detail(id) });
    },
  });
}

export function useBulkSoftDeleteCatalogRows() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertCatalogBulkSoftDeletePayload) => certsApi.bulkSoftDeleteCatalogRows(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.all });
    },
  });
}

export function useHardPurgeCatalogRow(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { reason: string }) => certsApi.hardPurgeCatalogRow(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certCatalogKeys.all });
      queryClient.removeQueries({ queryKey: certCatalogKeys.detail(id) });
      queryClient.removeQueries({ queryKey: certCatalogKeys.auditHistory(id) });
    },
  });
}
