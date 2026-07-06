import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { certVesselDashboardKeys } from '@/hooks/certs/use-vessel-dashboard';
import {
  certsApi,
  type CertTrackedItemUploadPdfPayload,
  type CertTrackedItemTransitionPayload,
} from '@/lib/api/certs';

export const certTrackedItemKeys = {
  all: ['certs', 'tracked-items'] as const,
  detail: (id: string) => [...certTrackedItemKeys.all, 'detail', id] as const,
};

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
