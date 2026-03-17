/**
 * Master data API functions.
 *
 * Endpoints per BACKEND_STRUCTURE.md Section 10.10 and apps/masters/views.py:
 * - GET /api/psc/masters/mou/
 * - GET /api/psc/masters/psc-action-codes/
 * - GET /api/psc/masters/pic/
 * - GET /api/psc/masters/psc-def-categories/
 * - GET /api/psc/masters/psc-def-codes/
 * - GET /api/psc/masters/clc-categories/
 * - GET /api/psc/masters/clc/
 * - GET /api/psc/masters/clc/hierarchy/
 */

import { apiClient } from './client';
import type {
  MOUCode,
  PSCActionCode,
  PICCode,
  PSCDefCategory,
  PSCDefCode,
  CLCCategory,
  CLCItem,
  CLCHierarchy,
  CrewMember,
} from '@/types';

// ============================================================================
// Filter Types
// ============================================================================

/** Filters for PIC codes endpoint */
export interface PICFilters {
  department?: 'Deck' | 'Engine';
}

/** Filters for PSC deficiency codes endpoint */
export interface PSCDefCodeFilters {
  search?: string;
  category?: string;
}

/** Filters for CLC items endpoint */
export interface CLCFilters {
  search?: string;
  type?: 'IMMEDIATE' | 'ROOT';
  category_id?: number;
}

// ============================================================================
// API Functions
// ============================================================================

/** Backend wraps master data responses in { data: T[], message: string } */
interface MasterResponse<T> {
  data: T;
  message: string;
  count?: number;
}

/**
 * Master data API functions.
 * All endpoints are public (no auth required) since master data is reference data.
 * Backend returns { data: T[], message: string } — we unwrap .data here.
 */
export const mastersApi = {
  /**
   * Get all MOU (Memorandum of Understanding) region codes.
   */
  getMOUCodes: async (): Promise<MOUCode[]> => {
    const { data } = await apiClient.get<MasterResponse<MOUCode[]>>('/masters/mou/');
    return data.data;
  },

  /**
   * Get all PSC action codes.
   * These define what action was taken on a deficiency (e.g., "10 - Deficiency rectified").
   */
  getPSCActionCodes: async (): Promise<PSCActionCode[]> => {
    const { data } = await apiClient.get<MasterResponse<PSCActionCode[]>>(
      '/masters/psc-action-codes/'
    );
    return data.data;
  },

  /**
   * Get PIC (Person In Charge) codes.
   * @param filters - Optional department filter (Deck or Engine)
   */
  getPICCodes: async (filters?: PICFilters): Promise<PICCode[]> => {
    const params = new URLSearchParams();
    if (filters?.department) {
      params.append('department', filters.department);
    }
    const queryString = params.toString();
    const url = queryString ? `/masters/pic/?${queryString}` : '/masters/pic/';
    const { data } = await apiClient.get<MasterResponse<PICCode[]>>(url);
    return data.data;
  },

  /**
   * Get all PSC deficiency categories.
   */
  getPSCDefCategories: async (): Promise<PSCDefCategory[]> => {
    const { data } = await apiClient.get<MasterResponse<PSCDefCategory[]>>(
      '/masters/psc-def-categories/'
    );
    return data.data;
  },

  /**
   * Get PSC deficiency codes with optional search and category filter.
   * @param filters - Optional search text and category code filter
   */
  getPSCDefCodes: async (filters?: PSCDefCodeFilters): Promise<PSCDefCode[]> => {
    const params = new URLSearchParams();
    if (filters?.search) {
      params.append('search', filters.search);
    }
    if (filters?.category) {
      params.append('category', filters.category);
    }
    const queryString = params.toString();
    const url = queryString
      ? `/masters/psc-def-codes/?${queryString}`
      : '/masters/psc-def-codes/';
    const { data } = await apiClient.get<MasterResponse<PSCDefCode[]>>(url);
    return data.data;
  },

  /**
   * Get all CLC (Comprehensive List of Causes) categories.
   */
  getCLCCategories: async (): Promise<CLCCategory[]> => {
    const { data } = await apiClient.get<MasterResponse<CLCCategory[]>>(
      '/masters/clc-categories/'
    );
    return data.data;
  },

  /**
   * Get CLC items with optional search, type, and category filter.
   * @param filters - Optional search text, type (IMMEDIATE/ROOT), and category_id filter
   */
  getCLCItems: async (filters?: CLCFilters): Promise<CLCItem[]> => {
    const params = new URLSearchParams();
    if (filters?.search) {
      params.append('search', filters.search);
    }
    if (filters?.type) {
      params.append('type', filters.type);
    }
    if (filters?.category_id !== undefined) {
      params.append('category_id', String(filters.category_id));
    }
    const queryString = params.toString();
    const url = queryString ? `/masters/clc/?${queryString}` : '/masters/clc/';
    const { data } = await apiClient.get<MasterResponse<CLCItem[]>>(url);
    return data.data;
  },

  /**
   * Get CLC data in hierarchical format for tree/accordion display.
   * Returns immediate_causes and root_causes organized by category.
   */
  getCLCHierarchy: async (): Promise<CLCHierarchy> => {
    const { data } = await apiClient.get<MasterResponse<CLCHierarchy>>(
      '/masters/clc/hierarchy/'
    );
    return data.data;
  },

  /**
   * Get active crew members for a vessel.
   * Used for corrective action owner assignment.
   */
  getVesselCrew: async (vesselId: string): Promise<CrewMember[]> => {
    const { data } = await apiClient.get<MasterResponse<CrewMember[]>>(
      `/auth/crew/?vessel_id=${vesselId}`
    );
    return data.data;
  },
};
