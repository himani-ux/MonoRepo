/**
 * Master data hooks using TanStack Query.
 *
 * Per FRONTEND_GUIDELINES.md Section 4.1 and LESSONS.md query key pattern.
 *
 * These hooks provide cached access to master data with a 24-hour stale time
 * since master data rarely changes.
 */

import { useQuery } from '@tanstack/react-query';
import {
  mastersApi,
  type PICFilters,
  type PSCDefCodeFilters,
  type CLCFilters,
} from '@/lib/api/masters';
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
// Cache Configuration
// ============================================================================

/** 24 hours in milliseconds - master data rarely changes */
const MASTER_DATA_STALE_TIME = 24 * 60 * 60 * 1000;
const MASTER_DATA_GC_TIME = 24 * 60 * 60 * 1000;

// ============================================================================
// Query Key Factory
// ============================================================================

/**
 * Query key factory for master data.
 * Per LESSONS.md pattern for consistent cache management.
 */
export const mastersKeys = {
  all: ['masters'] as const,

  // MOU
  mou: () => [...mastersKeys.all, 'mou'] as const,

  // PSC Action Codes
  pscActionCodes: () => [...mastersKeys.all, 'psc-action-codes'] as const,

  // PIC Codes
  pic: () => [...mastersKeys.all, 'pic'] as const,
  picFiltered: (filters: PICFilters) =>
    [...mastersKeys.pic(), filters] as const,

  // PSC Deficiency Categories
  pscDefCategories: () => [...mastersKeys.all, 'psc-def-categories'] as const,

  // PSC Deficiency Codes
  pscDefCodes: () => [...mastersKeys.all, 'psc-def-codes'] as const,
  pscDefCodesFiltered: (filters: PSCDefCodeFilters) =>
    [...mastersKeys.pscDefCodes(), filters] as const,

  // CLC Categories
  clcCategories: () => [...mastersKeys.all, 'clc-categories'] as const,

  // CLC Items
  clcItems: () => [...mastersKeys.all, 'clc'] as const,
  clcItemsFiltered: (filters: CLCFilters) =>
    [...mastersKeys.clcItems(), filters] as const,

  // CLC Hierarchy
  clcHierarchy: () => [...mastersKeys.all, 'clc-hierarchy'] as const,

  // Vessel Crew
  vesselCrew: (vesselId: string) => [...mastersKeys.all, 'crew', vesselId] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Hook to fetch MOU (Memorandum of Understanding) region codes.
 *
 * Usage:
 * ```tsx
 * const { data: mouCodes, isLoading, error } = useMOUCodes();
 * ```
 */
export function useMOUCodes() {
  return useQuery<MOUCode[], Error>({
    queryKey: mastersKeys.mou(),
    queryFn: mastersApi.getMOUCodes,
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch PSC action codes.
 * These define what action was taken on a deficiency.
 *
 * Usage:
 * ```tsx
 * const { data: actionCodes, isLoading, error } = usePSCActionCodes();
 * ```
 */
export function usePSCActionCodes() {
  return useQuery<PSCActionCode[], Error>({
    queryKey: mastersKeys.pscActionCodes(),
    queryFn: mastersApi.getPSCActionCodes,
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch PIC (Person In Charge) codes.
 *
 * @param filters - Optional department filter (Deck or Engine)
 *
 * Usage:
 * ```tsx
 * const { data: picCodes } = usePICCodes();
 * const { data: deckPIC } = usePICCodes({ department: 'Deck' });
 * ```
 */
export function usePICCodes(filters?: PICFilters) {
  return useQuery<PICCode[], Error>({
    queryKey: filters ? mastersKeys.picFiltered(filters) : mastersKeys.pic(),
    queryFn: () => mastersApi.getPICCodes(filters),
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch PSC deficiency categories.
 *
 * Usage:
 * ```tsx
 * const { data: categories } = usePSCDefCategories();
 * ```
 */
export function usePSCDefCategories() {
  return useQuery<PSCDefCategory[], Error>({
    queryKey: mastersKeys.pscDefCategories(),
    queryFn: mastersApi.getPSCDefCategories,
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch PSC deficiency codes with optional search/filter.
 *
 * @param filters - Optional search text and category code filter
 *
 * Usage:
 * ```tsx
 * // Get all def codes
 * const { data: defCodes } = usePSCDefCodes();
 *
 * // Search def codes
 * const { data: results } = usePSCDefCodes({ search: 'fire' });
 *
 * // Filter by category
 * const { data: catCodes } = usePSCDefCodes({ category: '07' });
 * ```
 */
export function usePSCDefCodes(filters?: PSCDefCodeFilters) {
  return useQuery<PSCDefCode[], Error>({
    queryKey: filters
      ? mastersKeys.pscDefCodesFiltered(filters)
      : mastersKeys.pscDefCodes(),
    queryFn: () => mastersApi.getPSCDefCodes(filters),
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch CLC (Comprehensive List of Causes) categories.
 *
 * Usage:
 * ```tsx
 * const { data: categories } = useCLCCategories();
 * ```
 */
export function useCLCCategories() {
  return useQuery<CLCCategory[], Error>({
    queryKey: mastersKeys.clcCategories(),
    queryFn: mastersApi.getCLCCategories,
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch CLC items with optional search/filter.
 *
 * @param filters - Optional search text, type (IMMEDIATE/ROOT), and category_id filter
 *
 * Usage:
 * ```tsx
 * // Get all CLC items
 * const { data: items } = useCLCItems();
 *
 * // Get immediate causes only
 * const { data: immediate } = useCLCItems({ type: 'IMMEDIATE' });
 *
 * // Search CLC items
 * const { data: results } = useCLCItems({ search: 'training' });
 * ```
 */
export function useCLCItems(filters?: CLCFilters) {
  return useQuery<CLCItem[], Error>({
    queryKey: filters
      ? mastersKeys.clcItemsFiltered(filters)
      : mastersKeys.clcItems(),
    queryFn: () => mastersApi.getCLCItems(filters),
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch CLC data in hierarchical format.
 * Useful for tree/accordion display of root causes.
 *
 * Usage:
 * ```tsx
 * const { data: hierarchy, isLoading } = useCLCHierarchy();
 * if (hierarchy) {
 *   // hierarchy.immediate_causes - nested immediate causes
 *   // hierarchy.root_causes - nested root causes
 * }
 * ```
 */
export function useCLCHierarchy() {
  return useQuery<CLCHierarchy, Error>({
    queryKey: mastersKeys.clcHierarchy(),
    queryFn: mastersApi.getCLCHierarchy,
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

/**
 * Hook to fetch active crew members for a vessel.
 * Used for corrective action owner assignment.
 */



export function useVesselCrew(vesselId: string | undefined) {
  return useQuery<CrewMember[], Error>({
    queryKey: mastersKeys.vesselCrew(vesselId!),
    queryFn: () => mastersApi.getVesselCrew(vesselId!),
    enabled: !!vesselId,
    staleTime: MASTER_DATA_STALE_TIME,
    gcTime: MASTER_DATA_GC_TIME,
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Hook to get a specific deficiency code by its code.
 * Searches the cached def codes list.
 *
 * @param defCode - The deficiency code to find
 *
 * Usage:
 * ```tsx
 * const { defCode, isLoading } = useDefCodeByCode('07115');
 * ```
 */
export function useDefCodeByCode(defCode: string | undefined) {
  const { data: defCodes, isLoading, error } = usePSCDefCodes();

  const foundDefCode = defCode
    ? defCodes?.find((d) => d.def_code === defCode)
    : undefined;

  return {
    defCode: foundDefCode,
    isLoading,
    error,
  };
}

/**
 * Hook to get a specific action code by its code.
 * Searches the cached action codes list.
 *
 * @param actionCode - The action code to find
 *
 * Usage:
 * ```tsx
 * const { actionCode, isLoading } = useActionCodeByCode('10');
 * ```
 */
export function useActionCodeByCode(actionCode: string | undefined) {
  const { data: actionCodes, isLoading, error } = usePSCActionCodes();

  const foundActionCode = actionCode
    ? actionCodes?.find((a) => String(a.action_code) === actionCode)
    : undefined;

  return {
    actionCode: foundActionCode,
    isLoading,
    error,
  };
}

/**
 * Hook to get a specific MOU by its code.
 * Searches the cached MOU codes list.
 *
 * @param mouCode - The MOU code to find
 *
 * Usage:
 * ```tsx
 * const { mou, isLoading } = useMOUByCode('TOKYO');
 * ```
 */
export function useMOUByCode(mouCode: string | undefined) {
  const { data: mouCodes, isLoading, error } = useMOUCodes();

  const foundMOU = mouCode
    ? mouCodes?.find((m) => m.mou_code === mouCode)
    : undefined;

  return {
    mou: foundMOU,
    isLoading,
    error,
  };
}
