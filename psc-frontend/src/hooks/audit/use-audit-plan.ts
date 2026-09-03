import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  auditApi,
  type AuditHodAssignment,
  type AuditHodAssignmentPayload,
  type AuditMasterList,
  type AuditOfficeUserOption,
  type AuditQualifyingBody,
  type AuditQualifiedAuditor,
  type AuditQualifiedAuditorPayload,
} from '@/lib/api/audit';
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
  qualifiedAuditors: (standards: string, targetOfficeDept: string) =>
    ['audit', 'masters', 'qualified-auditors', standards || 'none', targetOfficeDept || 'none'] as const,
  qualifiedAuditorMaster: () => ['audit', 'masters', 'qualified-auditors', 'all'] as const,
  qualifyingBodies: () => ['audit', 'masters', 'qualifying-bodies'] as const,
  officeUsers: () => ['audit', 'masters', 'office-users'] as const,
  hodCoverage: () => ['audit', 'admin', 'hod-coverage'] as const,
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

export function useAuditQualifiedAuditors(standards: string, targetOfficeDept: string) {
  return useQuery<AuditMasterList<AuditQualifiedAuditor>, Error>({
    queryKey: auditPlanKeys.qualifiedAuditors(standards, targetOfficeDept),
    queryFn: () =>
      auditApi.getAuditQualifiedAuditors({
        standards,
        target_office_dept: targetOfficeDept || undefined,
        eligible: true,
      }),
    enabled: Boolean(standards),
  });
}

export function useAuditQualifiedAuditorMaster() {
  return useQuery<AuditMasterList<AuditQualifiedAuditor>, Error>({
    queryKey: auditPlanKeys.qualifiedAuditorMaster(),
    queryFn: () => auditApi.getAuditQualifiedAuditors({ include_inactive: true }),
  });
}

export function useAuditOfficeUsers() {
  return useQuery<AuditMasterList<AuditOfficeUserOption>, Error>({
    queryKey: auditPlanKeys.officeUsers(),
    queryFn: auditApi.getAuditOfficeUsers,
  });
}

export function useAuditQualifyingBodies() {
  return useQuery<AuditMasterList<AuditQualifyingBody>, Error>({
    queryKey: auditPlanKeys.qualifyingBodies(),
    queryFn: () => auditApi.getAuditQualifyingBodies(),
  });
}

export function useCreateAuditQualifiedAuditor() {
  const queryClient = useQueryClient();

  return useMutation<AuditQualifiedAuditor, Error, AuditQualifiedAuditorPayload>({
    mutationFn: auditApi.createAuditQualifiedAuditor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.qualifiedAuditorMaster() });
      queryClient.invalidateQueries({ queryKey: ['audit', 'masters', 'qualified-auditors'] });
    },
  });
}

export function useUpdateAuditQualifiedAuditor() {
  const queryClient = useQueryClient();

  return useMutation<
    AuditQualifiedAuditor,
    Error,
    { id: string; data: Partial<AuditQualifiedAuditorPayload> }
  >({
    mutationFn: ({ id, data }) => auditApi.updateAuditQualifiedAuditor(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.qualifiedAuditorMaster() });
      queryClient.invalidateQueries({ queryKey: ['audit', 'masters', 'qualified-auditors'] });
    },
  });
}

export function useAuditHodCoverage() {
  return useQuery<AuditMasterList<AuditHodAssignment>, Error>({
    queryKey: auditPlanKeys.hodCoverage(),
    queryFn: auditApi.getAuditHodCoverage,
  });
}

export function useCreateAuditHodAssignment() {
  const queryClient = useQueryClient();

  return useMutation<AuditHodAssignment, Error, AuditHodAssignmentPayload>({
    mutationFn: auditApi.createAuditHodAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.hodCoverage() });
    },
  });
}

export function useExpireAuditHodAssignment() {
  const queryClient = useQueryClient();

  return useMutation<AuditHodAssignment, Error, string>({
    mutationFn: auditApi.expireAuditHodAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditPlanKeys.hodCoverage() });
    },
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
