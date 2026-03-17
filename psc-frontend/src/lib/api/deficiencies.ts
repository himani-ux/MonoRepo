/**
 * Deficiency API functions for vessel-side workflow.
 *
 * Endpoints at /api/psc/deficiencies/
 */

import { apiClient } from './client';
import type { CARStatus, DeficiencyDetail, DefStatus, PaginatedResponse } from '@/types';
import { DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';

/** Backend wraps responses in { data: T, message?: string } */
interface DeficiencyApiResponse<T> {
  data: T;
  message?: string;
}

// ============================================================================
// Filter types
// ============================================================================

export interface DeficiencyFilters {
  status?: DefStatus;
  car_status?: CARStatus;
  owner?: string;
  awaiting_review?: boolean;
  def_code?: string;
  vessel_id?: string;
  date_from?: string;
  date_to?: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get paginated list of deficiencies with optional filters.
 * Scoped to user's vessel on the backend.
 */
export async function getDeficiencies(
  filters?: DeficiencyFilters,
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE
): Promise<PaginatedResponse<DeficiencyDetail>> {
  const params = new URLSearchParams();
  params.set('page', page.toString());
  params.set('page_size', pageSize.toString());

  if (filters?.status) {
    params.set('status', filters.status);
  }
  if (filters?.car_status) {
    params.set('car_status', filters.car_status);
  }
  if (filters?.owner) {
    params.set('owner', filters.owner);
  }
  if (filters?.awaiting_review) {
    params.set('awaiting_review', 'true');
  }
  if (filters?.def_code) {
    params.set('def_code', filters.def_code);
  }
  if (filters?.vessel_id) {
    params.set('vessel_id', filters.vessel_id);
  }
  if (filters?.date_from) {
    params.set('date_from', filters.date_from);
  }
  if (filters?.date_to) {
    params.set('date_to', filters.date_to);
  }

  const response = await apiClient.get<PaginatedResponse<DeficiencyDetail>>(
    `/deficiencies/?${params.toString()}`
  );
  return response.data;
}

/**
 * Transition a deficiency through the workflow.
 */
export async function transitionDeficiency(
  id: number | string,
  targetStatus: DefStatus,
  comment?: string
): Promise<DeficiencyDetail> {
  const response = await apiClient.post<DeficiencyApiResponse<DeficiencyDetail>>(
    `/deficiencies/${id}/workflow/`,
    { target_status: targetStatus, comment: comment || '' }
  );
  return response.data.data;
}

/**
 * Allocate a deficiency to a crew member (Master only).
 */
export async function allocateDeficiency(
  id: number | string,
  assignedCrewId: string,
  reviewerCrewId?: string
): Promise<DeficiencyDetail> {
  const response = await apiClient.post<DeficiencyApiResponse<DeficiencyDetail>>(
    `/deficiencies/${id}/allocate/`,
    {
      assigned_crew_id: assignedCrewId,
      ...(reviewerCrewId ? { reviewer_crew_id: reviewerCrewId } : {}),
    }
  );
  return response.data.data;
}

/**
 * Bulk-submit multiple APPROVED deficiencies to the office.
 */
export async function bulkSubmitDeficiencies(
  inspectionId: string,
  deficiencyIds: Array<number | string>,
  comment?: string
): Promise<{ data: DeficiencyDetail[]; message: string }> {
  const response = await apiClient.post<{ data: DeficiencyDetail[]; message: string }>(
    `/inspections/${inspectionId}/deficiencies/bulk-submit/`,
    { deficiency_ids: deficiencyIds, ...(comment ? { comment } : {}) }
  );
  return response.data;
}

export const deficienciesApi = {
  getDeficiencies,
  transitionDeficiency,
  allocateDeficiency,
  bulkSubmitDeficiencies,
};