import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  certsApi,
  type CertOnboardingCommitPayload,
  type CertOnboardingBatchPayload,
  type CertOnboardingProfilePayload,
} from '@/lib/api/certs';

export const certOnboardingKeys = {
  all: ['certs', 'onboarding'] as const,
  hub: () => [...certOnboardingKeys.all, 'hub'] as const,
  wizard: (vesselId: string) => [...certOnboardingKeys.all, 'wizard', vesselId] as const,
  batch: (batchId: string) => [...certOnboardingKeys.all, 'batch', batchId] as const,
};

export function useOnboardingHub() {
  return useQuery({
    queryKey: certOnboardingKeys.hub(),
    queryFn: () => certsApi.getOnboardingHub(),
    staleTime: 60 * 1000,
  });
}

export function useOnboardingWizardState(vesselId: string | undefined) {
  return useQuery({
    queryKey: certOnboardingKeys.wizard(vesselId ?? ''),
    queryFn: () => certsApi.getOnboardingWizardState(vesselId!),
    enabled: Boolean(vesselId),
    staleTime: 60 * 1000,
  });
}

export function useOnboardingBatchGapFill(batchId: string | undefined) {
  return useQuery({
    queryKey: certOnboardingKeys.batch(batchId ?? ''),
    queryFn: () => certsApi.getOnboardingBatchGapFill(batchId!),
    enabled: Boolean(batchId),
    staleTime: 60 * 1000,
  });
}

export function usePreviewOnboardingBatch(batchId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => certsApi.previewOnboardingBatch(batchId!),
    onSuccess: () => {
      if (batchId) {
        queryClient.invalidateQueries({ queryKey: certOnboardingKeys.batch(batchId) });
      }
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.hub() });
    },
  });
}

export function useCommitOnboardingBatch(batchId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertOnboardingCommitPayload) => certsApi.commitOnboardingBatch(batchId!, payload),
    onSuccess: () => {
      if (batchId) {
        queryClient.invalidateQueries({ queryKey: certOnboardingKeys.batch(batchId) });
      }
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.hub() });
    },
  });
}

export function useSaveOnboardingProfile(vesselId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertOnboardingProfilePayload) => certsApi.saveOnboardingProfile(vesselId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.hub() });
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.wizard(vesselId) });
    },
  });
}

export function useCreateOnboardingBatch(vesselId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertOnboardingBatchPayload) => certsApi.createOnboardingBatch(vesselId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.hub() });
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.wizard(vesselId) });
    },
  });
}

export function useCoverageOverride(vesselId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) => certsApi.saveCoverageOverride(vesselId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.hub() });
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.wizard(vesselId) });
    },
  });
}

export function useFmSignoff(vesselId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) => certsApi.fmSignoff(vesselId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.hub() });
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.wizard(vesselId) });
    },
  });
}

export function useRollbackOnboarding(vesselId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) => certsApi.rollbackOnboarding(vesselId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.hub() });
      queryClient.invalidateQueries({ queryKey: certOnboardingKeys.wizard(vesselId) });
    },
  });
}
