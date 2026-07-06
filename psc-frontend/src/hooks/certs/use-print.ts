import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  certsApi,
  type CertPrintArtifactFilters,
  type CertPrintPayload,
  type CertShareBundlePayload,
} from '@/lib/api/certs';

export const certPrintKeys = {
  all: ['certs', 'print'] as const,
  artifacts: (filters: CertPrintArtifactFilters = {}) => [...certPrintKeys.all, 'artifacts', filters] as const,
  artifact: (printId: string) => [...certPrintKeys.all, 'artifact', printId] as const,
};

export function usePrintArtifacts(filters: CertPrintArtifactFilters = {}) {
  return useQuery({
    queryKey: certPrintKeys.artifacts(filters),
    queryFn: () => certsApi.getPrintArtifacts(filters),
    staleTime: 60 * 1000,
  });
}

export function usePrintArtifact(printId: string | undefined) {
  return useQuery({
    queryKey: certPrintKeys.artifact(printId ?? ''),
    queryFn: () => certsApi.getPrintArtifact(printId!),
    enabled: Boolean(printId),
    staleTime: 60 * 1000,
  });
}

export function useGeneratePrintArtifact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertPrintPayload) => certsApi.generatePrintArtifact(payload),
    onSuccess: (artifact) => {
      queryClient.invalidateQueries({ queryKey: certPrintKeys.all });
      queryClient.setQueryData(certPrintKeys.artifact(artifact.printId), artifact);
    },
  });
}

export function useGenerateShareBundle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertShareBundlePayload) => certsApi.generateShareBundle(payload),
    onSuccess: (artifact) => {
      queryClient.invalidateQueries({ queryKey: certPrintKeys.all });
      queryClient.setQueryData(certPrintKeys.artifact(artifact.printId), artifact);
    },
  });
}
