/**
 * CAR hooks using TanStack Query.
 *
 * Per FRONTEND_GUIDELINES.md Section 4.1 and LESSONS.md query key pattern.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  carsApi,
  type CARPaginatedResponse,
  type UploadEvidenceInput,
  type CreatePVInput,
  type ClosePVInput,
  type WorkflowTransitionInput,
} from '@/lib/api/cars';
import type {
  CARFilters,
  CARDetail,
  Evidence,
  UpdateCARInput,
  CreateCorrectiveActionInput,
  UpdateCorrectiveActionInput,
  CorrectiveAction,
  PhysicalVerification,
} from '@/types';
import { STALE_TIME, DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';
import { useAuthStore } from '@/stores/auth-store';

// ============================================================================
// Query Key Factory
// ============================================================================

function getCarUserScope(): string {
  const user = useAuthStore.getState().user;
  if (!user) return 'anonymous';
  return `${user.user_type}:${user.id}:${user.crew_id ?? ''}:${user.employee_id ?? ''}`;
}

/**
 * Query key factory for CARs.
 * Per LESSONS.md pattern for consistent cache management.
 */
export const carKeys = {
  all: () => ['cars', getCarUserScope()] as const,

  // List queries
  lists: () => [...carKeys.all(), 'list'] as const,
  list: (filters: CARFilters, page: number, pageSize: number) =>
    [...carKeys.lists(), { filters, page, pageSize }] as const,

  // Detail queries
  details: () => [...carKeys.all(), 'detail'] as const,
  detail: (id: number | string) => [...carKeys.details(), id] as const,

  // Available actions
  availableActions: (id: number | string) =>
    [...carKeys.all(), 'available-actions', id] as const,
};

// ============================================================================
// List Hook
// ============================================================================

export interface UseCARsOptions {
  /** Filter parameters */
  filters?: CARFilters;
  /** Page number (1-indexed) */
  page?: number;
  /** Items per page */
  pageSize?: number;
  /** Whether the query is enabled */
  enabled?: boolean;
}

/**
 * Hook to fetch paginated list of CARs with filters.
 *
 * @param options - Query options including filters, pagination
 *
 * Usage:
 * ```tsx
 * const { data, isLoading, error } = useCARs({
 *   filters: { status: 'DRAFT' },
 *   page: 1,
 * });
 * ```
 */
export function useCARs(options: UseCARsOptions = {}) {
  const {
    filters = {},
    page = 1,
    pageSize = DEFAULT_PAGE_SIZE,
    enabled = true,
  } = options;

  return useQuery<CARPaginatedResponse, Error>({
    queryKey: carKeys.list(filters, page, pageSize),
    queryFn: () => carsApi.getCARs(filters, page, pageSize),
    staleTime: STALE_TIME.CARS,
    enabled,
    placeholderData: (previousData) => previousData,
  });
}

// ============================================================================
// Detail Hook
// ============================================================================

/**
 * Hook to fetch a single CAR detail by ID.
 */
export function useCAR(id: string | number | undefined) {
  return useQuery<CARDetail, Error>({
    queryKey: carKeys.detail(id!),
    queryFn: () => carsApi.getCARDetail(id!),
    staleTime: STALE_TIME.CARS,
    enabled: !!id,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook to update a CAR (root cause, CLC codes, target date).
 */
export function useUpdateCAR(id: string | number) {
  const queryClient = useQueryClient();

  return useMutation<CARDetail, Error, UpdateCARInput>({
    mutationFn: (data) => carsApi.updateCAR(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

/**
 * Hook to submit a CAR for PIC review.
 */
export function useSubmitCAR(id: string | number) {
  const queryClient = useQueryClient();

  return useMutation<CARDetail, Error, void>({
    mutationFn: () => carsApi.submitCAR(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

// ============================================================================
// Unified Workflow Hooks
// ============================================================================

/**
 * Hook to execute a named workflow transition on a CAR.
 */
export function useTransitionCAR(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<
    { id: string; status: CARDetail['status']; action: string },
    Error,
    WorkflowTransitionInput
  >({
    mutationFn: (data) => carsApi.transitionCAR(carId, data),
    onSuccess: (result) => {
      // Apply immediate status update so UI reflects workflow transition
      // before network refetch completes.
      queryClient.setQueryData<CARDetail | undefined>(
        carKeys.detail(carId),
        (existing) => {
          if (!existing) return existing;
          return {
            ...existing,
            status: result.status,
            last_action: result.action,
          };
        },
      );
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
      queryClient.invalidateQueries({ queryKey: carKeys.availableActions(carId) });
    },
  });
}

/**
 * Hook to fetch available workflow actions for a CAR.
 */
export function useCARAvailableActions(carId: string | number | undefined) {
  return useQuery({
    queryKey: carKeys.availableActions(carId!),
    queryFn: () => carsApi.getCARAvailableActions(carId!),
    enabled: !!carId,
    staleTime: STALE_TIME.CARS,
  });
}

// ============================================================================
// Legacy State Transition Mutation Hooks (deprecated)
// ============================================================================

/**
 * Hook for PIC to accept a submitted CAR.
 * Implements: FEAT-CAR-005
 */
export function usePICAccept(id: string | number) {
  const queryClient = useQueryClient();

  return useMutation<CARDetail, Error, { comment: string }>({
    mutationFn: (data) => carsApi.picAcceptCAR(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

/**
 * Hook to request rework on a CAR.
 * Implements: FEAT-CAR-006
 */
export function useRequestRework(id: string | number) {
  const queryClient = useQueryClient();

  return useMutation<CARDetail, Error, { reason: string }>({
    mutationFn: (data) => carsApi.requestReworkCAR(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

/**
 * Hook for DPA to close a CAR.
 * Implements: FEAT-CAR-007
 */
export function useDPAClose(id: string | number) {
  const queryClient = useQueryClient();

  return useMutation<CARDetail, Error, { comment: string }>({
    mutationFn: (data) => carsApi.dpaCloseCAR(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

/**
 * Hook to reopen a DPA-closed CAR.
 * Implements: FEAT-CAR-008
 */
export function useReopenCAR(id: string | number) {
  const queryClient = useQueryClient();

  return useMutation<CARDetail, Error, { reason: string }>({
    mutationFn: (data) => carsApi.reopenCAR(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

// ============================================================================
// Corrective Action Mutation Hooks
// ============================================================================

/**
 * Hook to create a corrective action on a CAR.
 */
export function useCreateAction(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<CorrectiveAction, Error, CreateCorrectiveActionInput>({
    mutationFn: (data) => carsApi.createAction(carId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

/**
 * Hook to update an existing corrective action.
 */
export function useUpdateAction(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<
    CorrectiveAction,
    Error,
    { actionId: string | number; data: UpdateCorrectiveActionInput }
  >({
    mutationFn: ({ actionId, data }) => carsApi.updateAction(actionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
    },
  });
}

/**
 * Hook to delete (soft-delete) a corrective action.
 */
export function useDeleteAction(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string | number>({
    mutationFn: (actionId) => carsApi.deleteAction(actionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}

/**
 * Hook to mark a corrective action as completed.
 */
export function useCompleteAction(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<
    CorrectiveAction,
    Error,
    { actionId: string | number; completion_remarks?: string }
  >({
    mutationFn: ({ actionId, completion_remarks }) =>
      carsApi.completeAction(actionId, { completion_remarks }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
    },
  });
}

// ============================================================================
// Evidence Mutation Hooks
// ============================================================================

/**
 * Hook to upload evidence for a CAR.
 * Sends multipart/form-data and invalidates the CAR detail cache on success.
 */
export function useUploadEvidence(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<Evidence, Error, Omit<UploadEvidenceInput, 'carId'>>({
    mutationFn: (input) => carsApi.uploadEvidence({ ...input, carId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
    },
  });
}

/**
 * Hook to delete (soft-delete) an evidence attachment.
 */
export function useDeleteEvidence(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string | number>({
    mutationFn: (evidenceId) => carsApi.deleteEvidence(evidenceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
    },
  });
}

// ============================================================================
// Physical Verification Mutation Hooks — FEAT-PV-001, FEAT-PV-002
// ============================================================================

/**
 * Hook to create a physical verification for a CAR.
 * Only for DPA_CLOSED CARs.
 */
export function useCreatePV(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<PhysicalVerification, Error, CreatePVInput>({
    mutationFn: (data) => carsApi.createPhysicalVerification(carId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
    },
  });
}

/**
 * Hook to close a physical verification.
 * Requires visit_date and comments.
 */
export function useClosePV(carId: string | number) {
  const queryClient = useQueryClient();

  return useMutation<PhysicalVerification, Error, { pvId: string | number } & ClosePVInput>({
    mutationFn: ({ pvId, ...data }) => carsApi.closePhysicalVerification(pvId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: carKeys.detail(carId) });
      queryClient.invalidateQueries({ queryKey: carKeys.lists() });
    },
  });
}
