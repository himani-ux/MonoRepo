/**
 * CAR API functions
 *
 * Handles all CAR-related API calls per BACKEND_STRUCTURE.md contracts.
 */

import { apiClient } from './client';
import type {
  CARFilters,
  CARListItem,
  CARDetail,
  CARStatus,
  UpdateCARInput,
  CreateCorrectiveActionInput,
  UpdateCorrectiveActionInput,
  CorrectiveAction,
  Evidence,
  EvidenceType,
  PhysicalVerification,
} from '@/types';
import { DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';

// ============================================================================
// Response Types (matching actual backend format)
// ============================================================================

/** Paginated response format from CAR backend views */
export interface CARPaginatedResponse {
  data: CARListItem[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get paginated list of CARs with optional filters.
 *
 * @param filters - Optional filter parameters
 * @param page - Page number (1-indexed)
 * @param pageSize - Number of items per page
 */
export async function getCARs(
  filters?: CARFilters,
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE
): Promise<CARPaginatedResponse> {
  const params = new URLSearchParams();

  // Pagination
  params.set('page', page.toString());
  params.set('page_size', pageSize.toString());

  // Apply filters
  if (filters?.vessel_id) {
    params.set('vessel_id', filters.vessel_id.toString());
  }
  if (filters?.status) {
    params.set('status', filters.status);
  }
  if (filters?.pv_due !== undefined) {
    params.set('pv_due', String(filters.pv_due));
  }
  if (filters?.is_overdue !== undefined) {
    params.set('overdue', String(filters.is_overdue));
  }
  if (filters?.search) {
    params.set('car_number', filters.search);
  }

  const response = await apiClient.get<CARPaginatedResponse>(
    `/cars/?${params.toString()}`
  );
  return response.data;
}

// ============================================================================
// API Object (for consistency with other modules)
// ============================================================================

/** Single CAR detail response */
export interface CARDetailResponse {
  data: CARDetail;
}

/**
 * Get CAR detail by ID.
 */
export async function getCARDetail(id: string | number): Promise<CARDetail> {
  const response = await apiClient.get<CARDetailResponse>(`/cars/${id}/`);
  return response.data.data;
}

/**
 * Update CAR (root cause, CLC codes, target date).
 */
export async function updateCAR(
  id: string | number,
  data: UpdateCARInput
): Promise<CARDetail> {
  const response = await apiClient.put<CARDetailResponse>(`/cars/${id}/update/`, data);
  return response.data.data;
}

/**
 * Submit CAR for PIC review.
 */
export async function submitCAR(id: string | number): Promise<CARDetail> {
  const response = await apiClient.post<CARDetailResponse>(
    `/cars/${id}/submit/`
  );
  return response.data.data;
}

// ============================================================================
// Unified Workflow API Functions
// ============================================================================

export interface WorkflowTransitionInput {
  action: string;
  comment?: string;
}

interface WorkflowTransitionResponse {
  data: { id: string; status: CARStatus; action: string };
  message: string;
}

/**
 * Execute a named workflow transition on a CAR.
 * POST /api/psc/cars/{id}/workflow/
 */
export async function transitionCAR(
  id: string | number,
  data: WorkflowTransitionInput
): Promise<{ id: string; status: CARStatus; action: string }> {
  const response = await apiClient.post<WorkflowTransitionResponse>(
    `/cars/${id}/workflow/`,
    data
  );
  return response.data.data;
}

export interface AvailableActionResponse {
  data: Array<{ action: string; label: string; comment_required: boolean; role?: string }>;
}

/**
 * Get available workflow actions for the current user on a CAR.
 * GET /api/psc/cars/{id}/available-actions/
 */
export async function getCARAvailableActions(
  id: string | number
): Promise<Array<{ action: string; label: string; comment_required: boolean; role?: string }>> {
  const response = await apiClient.get<AvailableActionResponse>(
    `/cars/${id}/available-actions/`
  );
  return response.data.data;
}

// ============================================================================
// Corrective Action API Functions
// ============================================================================

/** Single corrective action response */
interface ActionResponse {
  data: CorrectiveAction;
}

/**
 * Create a new corrective action on a CAR.
 * POST /api/psc/cars/{car_id}/actions/
 */
export async function createAction(
  carId: string | number,
  data: CreateCorrectiveActionInput
): Promise<CorrectiveAction> {
  const response = await apiClient.post<ActionResponse>(
    `/cars/${carId}/actions/`,
    data
  );
  return response.data.data;
}

/**
 * Update an existing corrective action.
 * PUT /api/psc/actions/{id}/
 */
export async function updateAction(
  actionId: string | number,
  data: UpdateCorrectiveActionInput
): Promise<CorrectiveAction> {
  const response = await apiClient.put<ActionResponse>(
    `/actions/${actionId}/`,
    data
  );
  return response.data.data;
}

/**
 * Delete (soft-delete) a corrective action.
 * DELETE /api/psc/actions/{id}/delete/
 */
export async function deleteAction(
  actionId: string | number
): Promise<void> {
  await apiClient.delete(`/actions/${actionId}/delete/`);
}

/**
 * Mark a corrective action as completed.
 * POST /api/psc/actions/{id}/complete/
 */
export async function completeAction(
  actionId: string | number,
  data?: { completion_remarks?: string }
): Promise<CorrectiveAction> {
  const response = await apiClient.post<ActionResponse>(
    `/actions/${actionId}/complete/`,
    data
  );
  return response.data.data;
}

// ============================================================================
// Evidence API Functions
// ============================================================================

/** Upload evidence payload */
export interface UploadEvidenceInput {
  carId: string | number;
  file: File;
  evidence_type: EvidenceType;
  description: string;
}

/**
 * Upload evidence attachment for a CAR.
 * POST /api/psc/cars/{car_id}/evidence/
 *
 * Uses multipart/form-data per BACKEND_STRUCTURE.md.
 */
export async function uploadEvidence(
  input: UploadEvidenceInput
): Promise<Evidence> {
  const formData = new FormData();
  formData.append('file', input.file);
  formData.append('evidence_type', input.evidence_type);
  formData.append('description', input.description);

  const response = await apiClient.post<{ data: Evidence }>(
    `/cars/${input.carId}/evidence/`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  );
  return response.data.data;
}

/**
 * Delete (soft-delete) an evidence attachment.
 * DELETE /api/psc/evidence/{id}/
 */
export async function deleteEvidence(
  evidenceId: string | number
): Promise<void> {
  await apiClient.delete(`/evidence/${evidenceId}/`);
}

// ============================================================================
// State Transition API Functions
// ============================================================================

/**
 * PIC accept a submitted CAR.
 * POST /api/psc/cars/{id}/pic-accept/
 *
 * Implements: FEAT-CAR-005
 * Per BACKEND_STRUCTURE.md — CARPICAcceptSerializer expects { comment: string }
 */
export async function picAcceptCAR(
  id: string | number,
  data: { comment: string }
): Promise<CARDetail> {
  const response = await apiClient.post<CARDetailResponse>(
    `/cars/${id}/pic-accept/`,
    data
  );
  return response.data.data;
}

/**
 * Request rework on a CAR.
 * POST /api/psc/cars/{id}/rework/
 *
 * Implements: FEAT-CAR-006
 * Per BACKEND_STRUCTURE.md — CARReworkSerializer expects { reason: string } (min 20 chars)
 */
export async function requestReworkCAR(
  id: string | number,
  data: { reason: string }
): Promise<CARDetail> {
  const response = await apiClient.post<CARDetailResponse>(
    `/cars/${id}/rework/`,
    data
  );
  return response.data.data;
}

/**
 * DPA close a CAR.
 * POST /api/psc/cars/{id}/dpa-close/
 *
 * Implements: FEAT-CAR-007
 * Per BACKEND_STRUCTURE.md — CARDPACloseSerializer expects { comment: string }
 */
export async function dpaCloseCAR(
  id: string | number,
  data: { comment: string }
): Promise<CARDetail> {
  const response = await apiClient.post<CARDetailResponse>(
    `/cars/${id}/dpa-close/`,
    data
  );
  return response.data.data;
}

/**
 * Reopen a DPA-closed CAR.
 * POST /api/psc/cars/{id}/reopen/
 *
 * Implements: FEAT-CAR-008
 * Per BACKEND_STRUCTURE.md — CARReopenSerializer expects { reason: string } (min 10 chars)
 */
export async function reopenCAR(
  id: string | number,
  data: { reason: string }
): Promise<CARDetail> {
  const response = await apiClient.post<CARDetailResponse>(
    `/cars/${id}/reopen/`,
    data
  );
  return response.data.data;
}

// ============================================================================
// Physical Verification — FEAT-PV-001, FEAT-PV-002
// ============================================================================

export interface CreatePVInput {
  scheduled_date?: string | null;
  visit_port?: string;
  verifier_user_id?: string;
}

export interface ClosePVInput {
  visit_date: string;
  comments: string;
}

export async function createPhysicalVerification(
  carId: string | number,
  data: CreatePVInput
): Promise<PhysicalVerification> {
  const response = await apiClient.post<{ data: PhysicalVerification }>(
    `/cars/${carId}/physical-verification/`,
    data
  );
  return response.data.data;
}

export async function closePhysicalVerification(
  pvId: string | number,
  data: ClosePVInput
): Promise<PhysicalVerification> {
  const response = await apiClient.post<{ data: PhysicalVerification }>(
    `/physical-verifications/${pvId}/close/`,
    data
  );
  return response.data.data;
}

// ============================================================================
// Reports — FEAT-RPT-001
// ============================================================================

export type CARPDFAudience = 'internal' | 'external';

export async function exportCARPDF(
  id: string | number,
  audience: CARPDFAudience = 'internal'
): Promise<Blob> {
  const response = await apiClient.get(`/cars/${id}/export-pdf/`, {
    params: { audience },
    responseType: 'blob',
  });
  return response.data;
}

// ============================================================================
// API Object (for consistency with other modules)
// ============================================================================

export const carsApi = {
  getCARs,
  getCARDetail,
  updateCAR,
  submitCAR,
  transitionCAR,
  getCARAvailableActions,
  // Legacy (deprecated)
  picAcceptCAR,
  requestReworkCAR,
  dpaCloseCAR,
  reopenCAR,
  // Actions & Evidence
  createAction,
  updateAction,
  deleteAction,
  completeAction,
  uploadEvidence,
  deleteEvidence,
  createPhysicalVerification,
  closePhysicalVerification,
  exportCARPDF,
};
