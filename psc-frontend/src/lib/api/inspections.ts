/**
 * Inspection API functions
 *
 * Handles all inspection-related API calls per BACKEND_STRUCTURE.md contracts.
 */

import { apiClient } from './client';
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
import { DEFAULT_PAGE_SIZE } from '@/lib/utils/constants';

// ============================================================================
// Types
// ============================================================================

/** Extended list item with additional fields from API */
export interface InspectionListResponse {
  id: number;
  vessel_name: string;
  inspection_type: string;
  psc_subtype: string | null;
  inspection_date: string;
  port: string;
  port_state: string;
  mou_code: string | null;
  is_detention: boolean;
  status: string;
  operational_status: 'OPEN' | 'CLOSED';
  deficiency_count: number;
  open_deficiency_count: number;
  closed_deficiency_count: number;
}

/** Backend wraps detail/action responses in { data: T, message?: string } */
interface InspectionApiResponse<T> {
  data: T;
  message?: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get paginated list of inspections with optional filters.
 *
 * @param filters - Optional filter parameters
 * @param page - Page number (1-indexed)
 * @param pageSize - Number of items per page
 */
export async function getInspections(
  filters?: InspectionFilters,
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE
): Promise<PaginatedResponse<InspectionListResponse>> {
  const params = new URLSearchParams();

  // Pagination
  params.set('page', page.toString());
  params.set('page_size', pageSize.toString());

  // Apply filters
  if (filters?.vessel_id) {
    params.set('vessel_id', filters.vessel_id.toString());
  }
  if (filters?.inspection_type) {
    params.set('inspection_type', filters.inspection_type);
  }
  if (filters?.status) {
    params.set('status', filters.status);
  }
  if (filters?.is_detention !== undefined) {
    params.set('is_detention', filters.is_detention.toString());
  }
  if (filters?.date_from) {
    params.set('date_from', filters.date_from);
  }
  if (filters?.date_to) {
    params.set('date_to', filters.date_to);
  }
  if (filters?.search) {
    params.set('search', filters.search);
  }

  const response = await apiClient.get<PaginatedResponse<InspectionListResponse>>(
    `/inspections/?${params.toString()}`
  );
  return response.data;
}

/**
 * Get a single inspection by ID with full details.
 * Returns InspectionDetail which includes deficiencies, reports, and activity history.
 *
 * @param id - Inspection ID
 */
export async function getInspection(id: number | string): Promise<InspectionDetail> {
  const response = await apiClient.get<InspectionApiResponse<InspectionDetail>>(`/inspections/${id}/`);
  return response.data.data;
}

/**
 * Create a new inspection.
 *
 * @param data - Inspection creation data
 */
export async function createInspection(
  data: CreateInspectionInput
): Promise<Inspection> {
  const response = await apiClient.post<InspectionApiResponse<Inspection>>('/inspections/create/', data);
  return response.data.data;
}

/**
 * Update an existing inspection.
 *
 * @param id - Inspection ID
 * @param data - Fields to update
 */
export async function updateInspection(
  id: number | string,
  data: UpdateInspectionInput
): Promise<Inspection> {
  const response = await apiClient.put<InspectionApiResponse<Inspection>>(`/inspections/${id}/update/`, data);
  return response.data.data;
}

/**
 * Delete an inspection (draft only).
 *
 * @param id - Inspection ID
 */
export async function deleteInspection(id: number | string): Promise<void> {
  await apiClient.delete(`/inspections/${id}/delete/`);
}

/**
 * Submit an inspection for review.
 *
 * @param id - Inspection ID
 */
export async function submitInspection(id: number | string): Promise<Inspection> {
  const response = await apiClient.post<InspectionApiResponse<Inspection>>(`/inspections/${id}/submit/`);
  return response.data.data;
}

/**
 * PIC reviews the inspection.
 *
 * @param id - Inspection ID
 * @param comments - Review comments
 */
export async function picReviewInspection(
  id: number | string,
  comments?: string
): Promise<Inspection> {
  const response = await apiClient.post<InspectionApiResponse<Inspection>>(
    `/inspections/${id}/pic-review/`,
    { comment: comments }
  );
  return response.data.data;
}

/**
 * DPA closes the inspection.
 *
 * @param id - Inspection ID
 * @param comments - Closure comments
 */
export async function dpaCloseInspection(
  id: number | string,
  comments?: string
): Promise<Inspection> {
  const response = await apiClient.post<InspectionApiResponse<Inspection>>(
    `/inspections/${id}/dpa-close/`,
    { comment: comments }
  );
  return response.data.data;
}

/**
 * Upload inspection report file.
 *
 * @param id - Inspection ID
 * @param file - File to upload
 */
export async function uploadInspectionReport(
  id: number | string,
  file: File
): Promise<{ file_url: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<InspectionApiResponse<{ file_url: string }>>(
    `/inspections/${id}/upload-report/`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data.data;
}

// ============================================================================
// Deficiency API Functions
// ============================================================================

/**
 * Create a new deficiency for an inspection.
 * A CAR is automatically created for the deficiency via backend signal.
 *
 * @param inspectionId - Inspection ID
 * @param data - Deficiency creation data
 */
export async function createDeficiency(
  inspectionId: number | string,
  data: CreateDeficiencyInput
): Promise<Deficiency> {
  // Map frontend field names to backend serializer field names
  const payload: Record<string, unknown> = {
    def_code_id: data.def_code,
    description: data.def_text,
    action_code_id: data.action_code ? Number(data.action_code) : null,
  };
  if (data.target_date) {
    payload.target_date = data.target_date;
  }
  if (data.assigned_crew_id) {
    payload.assigned_crew_id = data.assigned_crew_id;
  }
  const response = await apiClient.post<InspectionApiResponse<Deficiency>>(
    `/inspections/${inspectionId}/deficiencies/`,
    payload
  );
  return response.data.data;
}

// ============================================================================
// PSC Follow-up API Functions
// ============================================================================

/** Individual deficiency action update for follow-up */
export interface DeficiencyActionUpdate {
  deficiency_id: string;
  action_code_id: number;
  notes?: string;
}

/**
 * Submit a follow-up on the SAME inspection (wizard workflow).
 * Sends multipart/form-data with JSON deficiency_updates + optional file.
 *
 * @param inspectionId - Inspection ID
 * @param data - FormData containing deficiency_updates (JSON), reinspection_date, optional report_file
 */
export async function submitFollowUp(
  inspectionId: string,
  data: FormData,
): Promise<InspectionDetail> {
  const response = await apiClient.post<InspectionApiResponse<InspectionDetail>>(
    `/inspections/${inspectionId}/follow-up/`,
    data,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return response.data.data;
}

// ============================================================================
// API Object (for consistency with other modules)
// ============================================================================


// ============================================================================
// Reports — FEAT-RPT-002
// ============================================================================

export interface ExcelExportFilters {
  vessel_id?: string;
  status?: string;
  inspection_type?: string;
  date_from?: string;
  date_to?: string;
}

export async function exportDeficiencyExcel(filters?: ExcelExportFilters): Promise<Blob> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
  }
  const response = await apiClient.get(`/inspections/export-excel/?${params.toString()}`, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Download all CAR PDFs for an inspection.
 * Returns a single PDF if only one CAR, or a ZIP if multiple.
 */
export async function exportInspectionCARs(inspectionId: string): Promise<Blob> {
  const response = await apiClient.get(
    `/inspections/${inspectionId}/cars/export-pdf/`,
    { responseType: 'blob' }
  );
  return response.data;
}

export const inspectionsApi = {
  getInspections,
  getInspection,
  createInspection,
  updateInspection,
  deleteInspection,
  submitInspection,
  picReviewInspection,
  dpaCloseInspection,
  uploadInspectionReport,
  createDeficiency,
  submitFollowUp,
  exportDeficiencyExcel,
  exportInspectionCARs,
};
