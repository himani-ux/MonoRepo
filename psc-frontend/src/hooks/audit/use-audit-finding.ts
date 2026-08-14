import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auditApi } from '@/lib/api/audit';
import type {
  AuditClauseMaster,
  AuditFindingCreateFormData,
  AuditFindingCreateResponse,
  AuditIssueCircularResponse,
} from '@/schemas/audit/finding';
import type {
  AuditNcClosure,
  AuditNcDraftPayload,
  AuditNcPartName,
  AuditNcPartPayload,
  AuditNcWorkflowAction,
  AuditNcWorkflowResponse,
  AuditRcaTemplateMaster,
} from '@/schemas/audit/nc-closure';
import type { AuditObsClosure, AuditObsPartName, AuditObsPartPayload } from '@/schemas/audit/obs-closure';
import { auditChecklistKeys } from './use-audit-checklist';
import { auditKeys } from './use-audit-registration';

export const auditClauseKeys = {
  all: () => [...auditKeys.all, 'clauses'] as const,
  book: (book: string | undefined) => [...auditClauseKeys.all(), book || 'unknown'] as const,
};

export const auditNcClosureKeys = {
  all: () => [...auditKeys.all, 'nc-closure'] as const,
  detail: (findingId: string | undefined) => [...auditNcClosureKeys.all(), findingId || 'unknown'] as const,
};

export const auditObsClosureKeys = {
  all: () => [...auditKeys.all, 'obs-closure'] as const,
  detail: (findingId: string | undefined) => [...auditObsClosureKeys.all(), findingId || 'unknown'] as const,
};

export const auditRcaTemplateKeys = {
  all: () => [...auditKeys.all, 'rca-templates'] as const,
  category: (category: string | undefined) => [...auditRcaTemplateKeys.all(), category || 'all'] as const,
};

export function useAuditClauseMaster(book: string | undefined) {
  return useQuery<AuditClauseMaster, Error>({
    queryKey: auditClauseKeys.book(book),
    queryFn: () => auditApi.getAuditClauseMaster(book!),
    enabled: Boolean(book && book !== 'OTHER' && book !== 'FLAG'),
  });
}

export function useCreateAuditFinding(auditId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditFindingCreateResponse, Error, AuditFindingCreateFormData>({
    mutationFn: (data) => auditApi.createAuditFinding(auditId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(auditId) });
      queryClient.invalidateQueries({ queryKey: auditChecklistKeys.checklist(auditId) });
    },
  });
}

export function useAuditNcClosure(findingId: string | undefined) {
  return useQuery<AuditNcClosure, Error>({
    queryKey: auditNcClosureKeys.detail(findingId),
    queryFn: () => auditApi.getAuditNcClosure(findingId!),
    enabled: Boolean(findingId),
  });
}

export function useAuditRcaTemplates(category?: string) {
  return useQuery<AuditRcaTemplateMaster, Error>({
    queryKey: auditRcaTemplateKeys.category(category),
    queryFn: () => auditApi.getAuditRcaTemplates(category),
  });
}

export function useUpdateAuditNcPart(findingId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditNcClosure, Error, { part: AuditNcPartName; data: AuditNcPartPayload }>({
    mutationFn: ({ part, data }) => auditApi.updateAuditNcPart(findingId!, part, data),
    onSuccess: (closure) => {
      queryClient.invalidateQueries({ queryKey: auditNcClosureKeys.detail(findingId) });
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(closure.audit_detail_id) });
    },
  });
}

export function useAuditObsClosure(findingId: string | undefined) {
  return useQuery<AuditObsClosure, Error>({
    queryKey: auditObsClosureKeys.detail(findingId),
    queryFn: () => auditApi.getAuditObsClosure(findingId!),
    enabled: Boolean(findingId),
  });
}

export function useUpdateAuditObsPart(findingId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditObsClosure, Error, { part: AuditObsPartName; data: AuditObsPartPayload }>({
    mutationFn: ({ part, data }) => auditApi.updateAuditObsPart(findingId!, part, data),
    onSuccess: (closure) => {
      queryClient.invalidateQueries({ queryKey: auditObsClosureKeys.detail(findingId) });
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(closure.audit_detail_id) });
    },
  });
}

export function useDraftAuditNcForVessel(findingId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditNcClosure, Error, AuditNcDraftPayload>({
    mutationFn: (data) => auditApi.draftAuditNcForVessel(findingId!, data),
    onSuccess: (closure) => {
      queryClient.invalidateQueries({ queryKey: auditNcClosureKeys.detail(findingId) });
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(closure.audit_detail_id) });
    },
  });
}

export function useAuditFindingCarWorkflow(findingId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditNcWorkflowResponse, Error, { action: AuditNcWorkflowAction; comment?: string }>({
    mutationFn: ({ action, comment }) => auditApi.transitionAuditFindingCar(findingId!, action, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditNcClosureKeys.detail(findingId) });
    },
  });
}

export function useIssueAuditCircular(auditId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<AuditIssueCircularResponse, Error, string>({
    mutationFn: (findingId) => auditApi.issueAuditFindingCircular(findingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(auditId) });
    },
  });
}
