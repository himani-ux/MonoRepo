import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { certsApi, type CertSettingsUpdatePayload } from '@/lib/api/certs';

export const certSettingsKeys = {
  all: ['certs', 'settings'] as const,
};

export function useCertSettings(enabled = true) {
  return useQuery({
    queryKey: certSettingsKeys.all,
    queryFn: () => certsApi.getSettings(),
    enabled,
    staleTime: 60 * 1000,
  });
}

export function useUpdateCertSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertSettingsUpdatePayload) => certsApi.updateSettings(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certSettingsKeys.all });
    },
  });
}
