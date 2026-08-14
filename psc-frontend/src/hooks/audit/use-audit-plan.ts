import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auditApi } from '@/lib/api/audit';
import type {
  AuditPlan,
  AuditPlanAdditionalData,
  AuditPlanCancelData,
  AuditPlanExtensionDecisionData,
  AuditPlanExtensionRequestData,
  AuditPlanFlagNotificationData,
  AuditPlanFormData,
  AuditPlanList,
} from '@/schemas/audit/plan';

export const auditPlanKeys = {
  all: ['audit', 'plans'] as const,
  list: (isAdditional?: boolean) => [...auditPlanKeys.all, 'list', isAdditional ?? 'all'] as const,
  detail: (id: string | undefined) => [...auditPlanKeys.all, id || 'unknown'] as const,
};

export function useAuditPlans(isAdditional?: boolean) {
  return useQuery<AuditPlanList, Error>({
    queryKey: auditPlanKeys.list(isAdditional),
    queryFn: () => auditApi.getAuditPlans(isAdditional),
  });
}

export function useAuditPlan(id: string | undefined) {
  return useQuery<AuditPlan, Error>({
    queryKey: auditPlanKeys.detail(id),
    queryFn: () => auditApi.getAuditPlan(id!),
    enabled: Boolean(id),
  });
}

export function useCreateAuditPlan() {
  const queryClient = useQueryClient();

  return useMutation<AuditPlan, Error, AuditPlanFormData>({
    mutationFn: auditApi.createAuditPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.all });
    },
  });
}

export function useUpdateAuditPlan(id: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditPlan, Error, AuditPlanFormData>({
    mutationFn: (data) => auditApi.updateAuditPlan(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.all });
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.detail(id) });
    },
  });
}

function usePlanWorkflowMutation<TPayload>(
  id: string | undefined,
  mutationFn: (id: string, data: TPayload) => Promise<AuditPlan>
) {
  const queryClient = useQueryClient();

  return useMutation<AuditPlan, Error, TPayload>({
    mutationFn: (data) => mutationFn(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.all });
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.detail(id) });
    },
  });
}

export function useRequestAuditPlanExtension(id: string | undefined) {
  return usePlanWorkflowMutation<AuditPlanExtensionRequestData>(id, auditApi.requestAuditPlanExtension);
}

export function useDecideAuditPlanExtension(id: string | undefined) {
  return usePlanWorkflowMutation<AuditPlanExtensionDecisionData>(id, auditApi.decideAuditPlanExtension);
}

export function useRecordAuditPlanFlagNotification(id: string | undefined) {
  return usePlanWorkflowMutation<AuditPlanFlagNotificationData>(id, auditApi.recordAuditPlanFlagNotification);
}

export function useCancelAuditPlan(id: string | undefined) {
  return usePlanWorkflowMutation<AuditPlanCancelData>(id, auditApi.cancelAuditPlan);
}

export function useCreateAdditionalAuditPlan() {
  const queryClient = useQueryClient();

  return useMutation<AuditPlan, Error, AuditPlanAdditionalData>({
    mutationFn: auditApi.createAdditionalAuditPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.all });
    },
  });
}
