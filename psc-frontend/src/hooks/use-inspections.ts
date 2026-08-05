/**
 * Inspection hooks using TanStack Query.
 *
 * Per FRONTEND_GUIDELINES.md Section 4.1 and LESSONS.md query key pattern.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  inspectionsApi,
  type InspectionListResponse,
} from '@/lib/api/inspections';
import type {
  Inspection,
  InspectionDetail,
  InspectionFilters,
  PaginatedResponse,
  CreateInspectionInput,
  UpdateInspectionInput,
  Deficiency,
  CreateDeficiencyInput,
} from '@/types';
import { STALE_TIME, DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';

// ============================================================================
// Query Key Factory
// ============================================================================

/**
 * Query key factory for inspections.
 * Per LESSONS.md pattern for consistent cache management.
 */
export const inspectionKeys = {
  all: ['inspections'] as const,

  // List queries
  lists: () => [...inspectionKeys.all, 'list'] as const,
  list: (filters: InspectionFilters, page: number, pageSize: number) =>
    [...inspectionKeys.lists(), { filters, page, pageSize }] as const,

  // Detail queries
  details: () => [...inspectionKeys.all, 'detail'] as const,
  detail: (id: number | string) => [...inspectionKeys.details(), id] as const,
};

// ============================================================================
// List Hook
// ============================================================================

export interface UseInspectionsOptions {
  /** Filter parameters */
  filters?: InspectionFilters;
  /** Page number (1-indexed) */
  page?: number;
  /** Items per page */
  pageSize?: number;
  /** Whether the query is enabled */
  enabled?: boolean;
}

/**
 * Hook to fetch paginated list of inspections with filters.
 *
 * @param options - Query options including filters, pagination
 *
 * Usage:
 * ```tsx
 * const { data, isLoading, error } = useInspections({
 *   filters: { inspection_type: 'PSC', status: 'DRAFT' },
 *   page: 1,
 * });
 * ```
 */
export function useInspections(options: UseInspectionsOptions = {}) {
  const {
    filters = {},
    page = 1,
    pageSize = DEFAULT_PAGE_SIZE,
    enabled = true,
  } = options;

  return useQuery<PaginatedResponse<InspectionListResponse>, Error>({
    queryKey: inspectionKeys.list(filters, page, pageSize),
    queryFn: () => inspectionsApi.getInspections(filters, page, pageSize),
    staleTime: STALE_TIME.INSPECTIONS,
    enabled,
    placeholderData: (previousData) => previousData, // Keep previous data while fetching
  });
}

// ============================================================================
// Detail Hook
// ============================================================================

export interface UseInspectionOptions {
  /** Whether the query is enabled */
  enabled?: boolean;
}

/**
 * Hook to fetch a single inspection with full details.
 *
 * @param id - Inspection ID
 * @param options - Query options
 *
 * Usage:
 * ```tsx
 * const { data: inspection, isLoading } = useInspection(123);
 * ```
 */
export function useInspection(
  id: number | string | undefined,
  options: UseInspectionOptions = {}
) {
  const { enabled = true } = options;

  return useQuery<InspectionDetail, Error>({
    queryKey: inspectionKeys.detail(id!),
    queryFn: () => inspectionsApi.getInspection(id!),
    staleTime: STALE_TIME.INSPECTIONS,
    enabled: enabled && id !== undefined,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook to create a new inspection.
 *
 * Usage:
 * ```tsx
 * const createMutation = useCreateInspection();
 * createMutation.mutate(inspectionData);
 * ```
 */
export function useCreateInspection() {
  const queryClient = useQueryClient();

  return useMutation<Inspection, Error, CreateInspectionInput>({
    mutationFn: inspectionsApi.createInspection,
    onSuccess: () => {
      // Invalidate list queries to refetch
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}

/**
 * Hook to update an existing inspection.
 *
 * Usage:
 * ```tsx
 * const updateMutation = useUpdateInspection(inspectionId);
 * updateMutation.mutate(updateData);
 * ```
 */
export function useUpdateInspection(id: number | string) {
  const queryClient = useQueryClient();

  return useMutation<Inspection, Error, UpdateInspectionInput>({
    mutationFn: (data) => inspectionsApi.updateInspection(id, data),
    onSuccess: (updatedInspection) => {
      // Update the detail cache
      queryClient.setQueryData(
        inspectionKeys.detail(id),
        updatedInspection
      );
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}

/**
 * Hook to delete an inspection.
 *
 * Usage:
 * ```tsx
 * const deleteMutation = useDeleteInspection();
 * deleteMutation.mutate(inspectionId);
 * ```
 */
export function useDeleteInspection() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number | string>({
    mutationFn: inspectionsApi.deleteInspection,
    onSuccess: (_, deletedId) => {
      // Remove from detail cache
      queryClient.removeQueries({ queryKey: inspectionKeys.detail(deletedId) });
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}

/**
 * Hook to submit an inspection for review.
 *
 * Usage:
 * ```tsx
 * const submitMutation = useSubmitInspection(inspectionId);
 * submitMutation.mutate();
 * ```
 */
export function useSubmitInspection(id: number | string) {
  const queryClient = useQueryClient();

  return useMutation<Inspection, Error, void>({
    mutationFn: () => inspectionsApi.submitInspection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inspectionKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}

/**
 * Hook for PIC to review an inspection.
 *
 * Usage:
 * ```tsx
 * const reviewMutation = usePICReviewInspection(inspectionId);
 * reviewMutation.mutate({ comments: 'Approved' });
 * ```
 */
export function usePICReviewInspection(id: number | string) {
  const queryClient = useQueryClient();

  return useMutation<Inspection, Error, { comments?: string }>({
    mutationFn: ({ comments }) => inspectionsApi.picReviewInspection(id, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inspectionKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}

/**
 * Hook for DPA to close an inspection.
 *
 * Usage:
 * ```tsx
 * const closeMutation = useDPACloseInspection(inspectionId);
 * closeMutation.mutate({ comments: 'Final review complete' });
 * ```
 */
export function useDPACloseInspection(id: number | string) {
  const queryClient = useQueryClient();

  return useMutation<Inspection, Error, { comments?: string }>({
    mutationFn: ({ comments }) => inspectionsApi.dpaCloseInspection(id, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inspectionKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}

/**
 * Hook to upload inspection report.
 *
 * Usage:
 * ```tsx
 * const uploadMutation = useUploadInspectionReport(inspectionId);
 * uploadMutation.mutate(file);
 * ```
 */
export function useUploadInspectionReport(id: number | string) {
  const queryClient = useQueryClient();

  return useMutation<{ file_url: string }, Error, File>({
    mutationFn: (file) => inspectionsApi.uploadInspectionReport(id, file),
    onSuccess: () => {
      // Invalidate detail to get updated file URL
      queryClient.invalidateQueries({ queryKey: inspectionKeys.detail(id) });
    },
  });
}

// ============================================================================
// Deficiency Mutation Hooks
// ============================================================================

/**
 * Hook to create a new deficiency for an inspection.
 * A CAR is automatically created via backend signal.
 *
 * Usage:
 * ```tsx
 * const createDeficiencyMutation = useCreateDeficiency(inspectionId);
 * createDeficiencyMutation.mutate({ def_code: '10101', def_text: '...' });
 * ```
 */
export function useCreateDeficiency(inspectionId: number | string) {
  const queryClient = useQueryClient();

  return useMutation<Deficiency, Error, CreateDeficiencyInput>({
    mutationFn: (data) => inspectionsApi.createDeficiency(inspectionId, data),
    onSuccess: () => {
      // Invalidate inspection detail to update deficiency count
      queryClient.invalidateQueries({
        queryKey: inspectionKeys.detail(inspectionId),
      });
      // Invalidate list queries in case deficiency count is shown
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}

// ============================================================================
// PSC Follow-up Mutation Hook
// ============================================================================

/**
 * Hook to submit a follow-up on the same inspection (wizard workflow).
 *
 * Usage:
 * ```tsx
 * const followUpMutation = useSubmitFollowUp(inspectionId);
 * const formData = new FormData();
 * formData.append('deficiency_updates', JSON.stringify(updates));
 * formData.append('reinspection_date', '2026-01-20');
 * formData.append('report_files', pdfFile);
 * followUpMutation.mutate(formData);
 * ```
 */
export function useSubmitFollowUp(inspectionId: string) {
  const queryClient = useQueryClient();

  return useMutation<InspectionDetail, Error, FormData>({
    mutationFn: (formData) => inspectionsApi.submitFollowUp(inspectionId, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: inspectionKeys.detail(inspectionId),
      });
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}
