import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auditApi, type AuditRegistrationResponse } from '@/lib/api/audit';
import type { ExternalAuditCloseoutPayload, ExternalCertLinkPayload } from '@/lib/api/audit';
import type { AuditDetail, AuditDetailEditableFields, AuditScorecardRow } from '@/schemas/audit/detail';
import type { AuditRegistrationPayload } from '@/schemas/audit/registration';

export const auditKeys = {
  all: ['audit'] as const,
  audits: () => [...auditKeys.all, 'audits'] as const,
  detail: (id: string | undefined) => [...auditKeys.audits(), id || 'unknown'] as const,
};

export function useCreateAuditRegistration() {
  const queryClient = useQueryClient();

  return useMutation<AuditRegistrationResponse, Error, AuditRegistrationPayload>({
    mutationFn: auditApi.createAuditRegistration,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.audits() });
      queryClient.invalidateQueries({ queryKey: ['inspections', 'list'] });
    },
  });
}

export function useAuditDetail(id: string | undefined) {
  return useQuery<AuditDetail, Error>({
    queryKey: auditKeys.detail(id),
    queryFn: () => auditApi.getAuditDetail(id!),
    enabled: Boolean(id),
  });
}

export function useUpdateAuditDetail(id: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditDetail, Error, AuditDetailEditableFields>({
    mutationFn: (data) => auditApi.updateAuditDetail(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(id) });
    },
  });
}

export function useUpdateAuditScorecard(id: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditDetail, Error, Pick<AuditScorecardRow, 'area_code' | 'status' | 'remarks'>[]>({
    mutationFn: (rows) => auditApi.updateAuditScorecard(id!, rows),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(id) });
    },
  });
}

export function useSubmitAuditReport(id: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditDetail, Error, void>({
    mutationFn: () => auditApi.submitAuditReport(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: auditKeys.audits() });
    },
  });
}

export function useAcknowledgeAuditReport(id: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditDetail, Error, void>({
    mutationFn: () => auditApi.acknowledgeAuditReport(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: auditKeys.audits() });
    },
  });
}

export function useConfirmExternalAuditCloseout(id: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditDetail, Error, ExternalAuditCloseoutPayload>({
    mutationFn: (data) => auditApi.confirmExternalAuditCloseout(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: auditKeys.audits() });
    },
  });
}

export function useEditExternalAuditCertLinks(id: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditDetail, Error, ExternalCertLinkPayload>({
    mutationFn: (data) => auditApi.editExternalAuditCertLinks(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: auditKeys.audits() });
    },
  });
}
