import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { certVesselDashboardKeys } from '@/hooks/certs/use-vessel-dashboard';
import {
  certsApi,
  type CertTrackedItemFilters,
  type CertTrackedItemMetadataUpdatePayload,
  type CertTrackedItemReparsePdfPayload,
  type CertTrackedItemRemovePdfPayload,
  type CertTrackedItemUploadPdfPayload,
  type CertTrackedItemTransitionPayload,
} from '@/lib/api/certs';

export const certTrackedItemKeys = {
  all: ['certs', 'tracked-items'] as const,
  list: (filters: CertTrackedItemFilters) => [...certTrackedItemKeys.all, 'list', filters] as const,
  detail: (id: string) => [...certTrackedItemKeys.all, 'detail', id] as const,
};

export function useTrackedItems(filters: CertTrackedItemFilters = {}, enabled = true) {
  return useQuery({
    queryKey: certTrackedItemKeys.list(filters),
    queryFn: () => certsApi.getTrackedItems(filters),
    enabled,
    staleTime: 60 * 1000,
  });
}

export function useTrackedItemDetail(id: string | undefined) {
  return useQuery({
    queryKey: certTrackedItemKeys.detail(id ?? ''),
    queryFn: () => certsApi.getTrackedItemDetail(id!),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

function useTrackedItemTransition(
  id: string,
  imo: string,
  mutationFn: (payload: CertTrackedItemTransitionPayload) => Promise<unknown>
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certTrackedItemKeys.all });
      queryClient.invalidateQueries({ queryKey: certTrackedItemKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.vessel(imo) });
    },
  });
}

export function useSubmitTrackedItem(id: string, imo: string) {
  return useTrackedItemTransition(id, imo, (payload) => certsApi.submitTrackedItem(id, payload));
}

export function useApproveTrackedItem(id: string, imo: string) {
  return useTrackedItemTransition(id, imo, (payload) => certsApi.approveTrackedItem(id, payload));
}

export function useRejectTrackedItem(id: string, imo: string) {
  return useTrackedItemTransition(id, imo, (payload) => certsApi.rejectTrackedItem(id, payload));
}

export function useUpdateTrackedItemMetadata(id: string, imo: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertTrackedItemMetadataUpdatePayload) => certsApi.updateTrackedItemMetadata(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certTrackedItemKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.vessel(imo) });
    },
  });
}

export function useUploadTrackedItemPdf(id: string, imo: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertTrackedItemUploadPdfPayload) => certsApi.uploadTrackedItemPdf(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certTrackedItemKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.vessel(imo) });
    },
  });
}

export function useReparseTrackedItemPdf(id: string, imo: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertTrackedItemReparsePdfPayload = {}) => certsApi.reparseTrackedItemPdf(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certTrackedItemKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.vessel(imo) });
    },
  });
}

export function useRemoveTrackedItemPdf(id: string, imo: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertTrackedItemRemovePdfPayload) => certsApi.removeTrackedItemPdf(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certTrackedItemKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.vessel(imo) });
    },
  });
}
