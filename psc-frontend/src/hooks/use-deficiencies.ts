/**
 * Deficiency workflow hooks using TanStack Query.
 *
 * Provides hooks for the vessel-side DEF workflow:
 * - useDeficiencies: Paginated list with filters
 * - useTransitionDeficiency: Workflow state transition mutation
 * - useAllocateDeficiency: Master crew allocation mutation
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  deficienciesApi,
  type DeficiencyFilters,
} from '@/lib/api/deficiencies';
import type { DeficiencyDetail, DefStatus, PaginatedResponse } from '@/types';
import { STALE_TIME, DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';
import { inspectionKeys } from './use-inspections';
import { useAuthStore } from '@/stores/auth-store';

// ============================================================================
// Query Key Factory
// ============================================================================

export const deficiencyKeys = {
  all: () => ['deficiencies', getDeficiencyUserScope()] as const,
  lists: () => [...deficiencyKeys.all(), 'list'] as const,
  list: (filters: DeficiencyFilters, page: number, pageSize: number) =>
    [...deficiencyKeys.lists(), { filters, page, pageSize }] as const,
};

function getDeficiencyUserScope(): string {
  const user = useAuthStore.getState().user;
  if (!user) return 'anonymous';
  return `${user.user_type}:${user.id}:${user.crew_id ?? ''}:${user.employee_id ?? ''}`;
}

// ============================================================================
// List Hook
// ============================================================================

export interface UseDeficienciesOptions {
  filters?: DeficiencyFilters;
  page?: number;
  pageSize?: number;
  enabled?: boolean;
}

/**
 * Hook to fetch paginated deficiencies with filters.
 * Results are scoped to the user's vessel on the backend.
 */
export function useDeficiencies(options: UseDeficienciesOptions = {}) {
  const {
    filters = {},
    page = 1,
    pageSize = DEFAULT_PAGE_SIZE,
    enabled = true,
  } = options;

  return useQuery<PaginatedResponse<DeficiencyDetail>>({
    queryKey: deficiencyKeys.list(filters, page, pageSize),
    queryFn: () => deficienciesApi.getDeficiencies(filters, page, pageSize),
    staleTime: STALE_TIME.INSPECTIONS,
    enabled,
  });
}

// ============================================================================
// Transition Mutation
// ============================================================================

/**
 * Hook to transition a deficiency through the workflow.
 * Invalidates both deficiency and inspection caches on success.
 */
export function useTransitionDeficiency() {
  const queryClient = useQueryClient();

  return useMutation<
    DeficiencyDetail,
    Error,
    { id: number | string; targetStatus: DefStatus; comment?: string }
  >({
    mutationFn: ({ id, targetStatus, comment }) =>
      deficienciesApi.transitionDeficiency(id, targetStatus, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deficiencyKeys.all() });
      queryClient.invalidateQueries({ queryKey: inspectionKeys.all });
    },
  });
}

// ============================================================================
// Allocate Mutation
// ============================================================================

/**
 * Hook for Master to allocate a deficiency to a crew member.
 * Auto-computes reviewer on the backend.
 */
export function useAllocateDeficiency() {
  const queryClient = useQueryClient();

  return useMutation<
    DeficiencyDetail,
    Error,
    { id: number | string; assignedCrewId: string; reviewerCrewId?: string }
  >({
    mutationFn: ({ id, assignedCrewId, reviewerCrewId }) =>
      deficienciesApi.allocateDeficiency(id, assignedCrewId, reviewerCrewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deficiencyKeys.all() });
      queryClient.invalidateQueries({ queryKey: inspectionKeys.all });
    },
  });
}

// ============================================================================
// Bulk Submit Mutation
// ============================================================================

/**
 * Hook for Master to bulk-submit multiple APPROVED deficiencies to the office.
 */
export function useBulkSubmitDeficiencies() {
  const queryClient = useQueryClient();

  return useMutation<
    { data: DeficiencyDetail[]; message: string },
    Error,
    { inspectionId: string; deficiencyIds: Array<number | string>; comment?: string }
  >({
    mutationFn: ({ inspectionId, deficiencyIds, comment }) =>
      deficienciesApi.bulkSubmitDeficiencies(inspectionId, deficiencyIds, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deficiencyKeys.all() });
      queryClient.invalidateQueries({ queryKey: inspectionKeys.all });
    },
  });
}
