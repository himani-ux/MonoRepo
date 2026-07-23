import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  certsApi,
  type CertAddClassMappingPayload,
  type CertClassSnapshotFilters,
  type CertClassSnapshotUploadPayload,
  type CertMasterReconciliationMessageFilters,
  type CertReconciliationRunFilters,
} from '@/lib/api/certs';

export const certReconciliationKeys = {
  all: ['certs', 'reconciliation'] as const,
  snapshots: (filters: CertClassSnapshotFilters = {}) => [...certReconciliationKeys.all, 'snapshots', filters] as const,
  snapshot: (id: string) => [...certReconciliationKeys.all, 'snapshot', id] as const,
  runs: (filters: CertReconciliationRunFilters = {}) => [...certReconciliationKeys.all, 'runs', filters] as const,
  run: (id: string) => [...certReconciliationKeys.all, 'run', id] as const,
  masterMessages: (filters: CertMasterReconciliationMessageFilters = {}) =>
    [...certReconciliationKeys.all, 'master-messages', filters] as const,
};

export function useClassSnapshots(filters: CertClassSnapshotFilters = {}) {
  return useQuery({
    queryKey: certReconciliationKeys.snapshots(filters),
    queryFn: () => certsApi.getClassSnapshots(filters),
    staleTime: 60 * 1000,
  });
}

export function useClassSnapshot(id: string | undefined) {
  return useQuery({
    queryKey: certReconciliationKeys.snapshot(id ?? ''),
    queryFn: () => certsApi.getClassSnapshot(id!),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useReconciliationRuns(filters: CertReconciliationRunFilters = {}) {
  return useQuery({
    queryKey: certReconciliationKeys.runs(filters),
    queryFn: () => certsApi.getReconciliationRuns(filters),
    staleTime: 60 * 1000,
  });
}

export function useReconciliationRun(id: string | undefined) {
  return useQuery({
    queryKey: certReconciliationKeys.run(id ?? ''),
    queryFn: () => certsApi.getReconciliationRun(id!),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useMasterReconciliationMessages(
  filters: CertMasterReconciliationMessageFilters = {},
  enabled = true
) {
  return useQuery({
    queryKey: certReconciliationKeys.masterMessages(filters),
    queryFn: () => certsApi.getMasterReconciliationMessages(filters),
    enabled,
    staleTime: 60 * 1000,
  });
}

export function useUploadClassSnapshot() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertClassSnapshotUploadPayload) => certsApi.uploadClassSnapshot(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certReconciliationKeys.all });
    },
  });
}

export function useReparseClassSnapshot(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => certsApi.reparseClassSnapshot(id!),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: certReconciliationKeys.all });
      if (id) {
        queryClient.invalidateQueries({ queryKey: certReconciliationKeys.snapshot(id) });
      }
      if (data.reconciliationRun?.id) {
        queryClient.invalidateQueries({ queryKey: certReconciliationKeys.run(data.reconciliationRun.id) });
      }
    },
  });
}

export function useMarkReconciliationFlagReviewed(runId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ flagId, reason }: { flagId: string; reason: string }) => certsApi.markReconciliationFlagReviewed(flagId, reason),
    onSuccess: () => {
      if (runId) {
        queryClient.invalidateQueries({ queryKey: certReconciliationKeys.run(runId) });
      }
      queryClient.invalidateQueries({ queryKey: certReconciliationKeys.all });
    },
  });
}

export function useNotifyMasterForReconciliationFlag(runId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ flagId, reason }: { flagId: string; reason: string }) => certsApi.notifyMasterForReconciliationFlag(flagId, reason),
    onSuccess: () => {
      if (runId) {
        queryClient.invalidateQueries({ queryKey: certReconciliationKeys.run(runId) });
      }
      queryClient.invalidateQueries({ queryKey: certReconciliationKeys.all });
    },
  });
}

export function useAcknowledgeMasterReconciliationMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ messageId, note }: { messageId: string; note: string }) =>
      certsApi.acknowledgeMasterReconciliationMessage(messageId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certReconciliationKeys.all });
    },
  });
}

export function useAddClassCodeMappingForFlag(runId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ flagId, payload }: { flagId: string; payload: CertAddClassMappingPayload }) =>
      certsApi.addClassCodeMappingForFlag(flagId, payload),
    onSuccess: (data) => {
      if (runId) {
        queryClient.invalidateQueries({ queryKey: certReconciliationKeys.run(runId) });
      }
      if (data.reconciliationRun?.id) {
        queryClient.invalidateQueries({ queryKey: certReconciliationKeys.run(data.reconciliationRun.id) });
      }
      queryClient.invalidateQueries({ queryKey: certReconciliationKeys.runs() });
    },
  });
}
