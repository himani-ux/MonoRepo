import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  certsApi,
  type CertClassChangePayload,
  type CertDecommissionPayload,
  type CertFlagChangePayload,
  type CertSaleHandoverPayload,
} from '@/lib/api/certs';

export const certVesselDashboardKeys = {
  all: ['certs', 'dashboard'] as const,
  fleet: () => [...certVesselDashboardKeys.all, 'fleet'] as const,
  vessel: (imo: string) => [...certVesselDashboardKeys.all, 'vessel', imo] as const,
  profile: (imo: string) => [...certVesselDashboardKeys.all, 'vessel-profile', imo] as const,
};

export function useFleetDashboard(enabled = true) {
  return useQuery({
    queryKey: certVesselDashboardKeys.fleet(),
    queryFn: () => certsApi.getFleetDashboard(),
    enabled,
    staleTime: 60 * 1000,
  });
}

export function useVesselDashboard(imo: string | undefined) {
  return useQuery({
    queryKey: certVesselDashboardKeys.vessel(imo ?? ''),
    queryFn: () => certsApi.getVesselDashboard(imo!),
    enabled: Boolean(imo),
    staleTime: 60 * 1000,
  });
}

export function useVesselProfile(imo: string | undefined) {
  return useQuery({
    queryKey: certVesselDashboardKeys.profile(imo ?? ''),
    queryFn: () => certsApi.getVesselProfile(imo!),
    enabled: Boolean(imo),
    staleTime: 60 * 1000,
  });
}

function useLifecycleMutation<TPayload>(imo: string, mutationFn: (payload: TPayload) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.vessel(imo) });
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.profile(imo) });
      queryClient.invalidateQueries({ queryKey: certVesselDashboardKeys.fleet() });
    },
  });
}

export function useRecordFlagChange(imo: string) {
  return useLifecycleMutation<CertFlagChangePayload>(imo, (payload) => certsApi.recordFlagChange(imo, payload));
}

export function useRecordClassChange(imo: string) {
  return useLifecycleMutation<CertClassChangePayload>(imo, (payload) => certsApi.recordClassChange(imo, payload));
}

export function useInitiateSaleHandover(imo: string) {
  return useLifecycleMutation<CertSaleHandoverPayload>(imo, (payload) => certsApi.initiateSaleHandover(imo, payload));
}

export function useDecommissionVessel(imo: string) {
  return useLifecycleMutation<CertDecommissionPayload>(imo, (payload) => certsApi.decommissionVessel(imo, payload));
}
