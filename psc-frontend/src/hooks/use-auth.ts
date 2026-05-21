/**
 * Authentication hook for components.
 *
 * Provides convenient access to auth state and actions.
 * Wraps the auth store with additional computed values and utilities.
 *
 * Per FRONTEND_GUIDELINES.md Section 4.2
 */

import { useCallback, useEffect, useMemo } from 'react';
import { useAuthStore, migrateLegacyTokens } from '@/stores/auth-store';
import { USER_ROLES } from '@/lib/utils/constants';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import type { UserRole, AuthTokens } from '@/types';
import type { AuthUser, LoginRequest } from '@/lib/api/auth';

function normalizePermissionId(id: string, type: 'form' | 'process'): string {
  const normalized = String(id).trim().toUpperCase();
  if (!normalized) {
    return '';
  }

  if (type === 'form') {
    if (normalized.startsWith('PSC_F_')) return normalized;
    if (normalized.startsWith('F_')) return `PSC_${normalized}`;
    return normalized;
  }

  if (normalized.startsWith('PSC_P_')) return normalized;
  if (normalized.startsWith('P_')) return `PSC_${normalized}`;
  return normalized;
}

/**
 * Check if a role is a vessel role.
 */
export function isVesselRole(role: string | undefined): boolean {
  return role === USER_ROLES.VESSEL_MASTER || role === USER_ROLES.VESSEL_CREW;
}

/**
 * Check if a role is an office role.
 */
export function isOfficeRole(role: string | undefined): boolean {
  return (
    role === 'PIC' ||
    role === 'VESSEL SUPERINTENDENT' ||
    role === USER_ROLES.OFFICE_PIC ||
    role === USER_ROLES.OFFICE_SSQE ||
    role === USER_ROLES.OFFICE_SUPT ||
    role === USER_ROLES.DPA ||
    role === USER_ROLES.PHYSICAL_VERIFIER
  );
}

/**
 * Check if a role can perform PIC actions.
 */
export function canPerformPICActions(role: string | undefined): boolean {
  return (
    role === 'PIC' ||
    role === 'VESSEL SUPERINTENDENT' ||
    role === USER_ROLES.OFFICE_PIC ||
    role === USER_ROLES.OFFICE_SSQE ||
    role === USER_ROLES.OFFICE_SUPT ||
    role === USER_ROLES.DPA
  );
}

/**
 * Check if a role can perform DPA actions.
 */
export function canPerformDPAActions(role: string | undefined): boolean {
  return role === USER_ROLES.DPA;
}

export type VesselRankCategory = 'MASTER' | 'CO' | 'CE' | '2E' | 'OTHER';

/**
 * Classify vessel rank string into DefIntel access categories.
 */
export function classifyVesselRank(rank: string | null | undefined): VesselRankCategory {
  const normalized = (rank || '').toLowerCase().trim();
  if (!normalized) {
    return 'OTHER';
  }

  if (normalized.includes('master') || normalized.includes('captain')) {
    return 'MASTER';
  }

  if (normalized.includes('chief officer') || normalized.includes('chief mate') || normalized.includes('c/o')) {
    return 'CO';
  }

  if (normalized.includes('chief engineer') || normalized.includes('c/e')) {
    return 'CE';
  }

  if (normalized.includes('second engineer') || normalized.includes('2nd engineer') || normalized.includes('2/e')) {
    return '2E';
  }

  return 'OTHER';
}

/**
 * DefIntel reports access rule:
 * - Any office user
 * - Vessel users in Master/CO/CE/2E ranks
 */
export function canAccessReportsFeature(
  userType: string | undefined,
  role: string | undefined,
  rank: string | null | undefined
): boolean {
  const normalizedUserType = (userType || '').toLowerCase();
  if (normalizedUserType === 'office') {
    return true;
  }
  if (normalizedUserType !== 'vessel') {
    return false;
  }

  if (role === USER_ROLES.VESSEL_MASTER) {
    return true;
  }

  return ['MASTER', 'CO', 'CE', '2E'].includes(classifyVesselRank(rank));
}

/**
 * OpenSource import is restricted to office users.
 */
export function canImportOpenSourceFeature(userType: string | undefined): boolean {
  return (userType || '').toLowerCase() === 'office';
}

/**
 * Hook return type.
 */
export interface UseAuthReturn {
  // State
  user: AuthUser | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;

  // Computed
  isVessel: boolean;
  isOffice: boolean;
  isMaster: boolean;
  isCrew: boolean;
  isPIC: boolean;
  isDPA: boolean;
  canAccessReports: boolean;
  canImportOpenSource: boolean;
  role: UserRole | undefined;
  vesselId: string | null;
  fullName: string;
  formIds: string[];
  processIds: string[];
  hasForm: (formId: string) => boolean;
  hasProcess: (processId: string) => boolean;

  // Actions
  login: (credentials: LoginRequest) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<AuthTokens | null>;
}

/**
 * Main authentication hook.
 *
 * Usage:
 * ```tsx
 * const { user, isAuthenticated, login, logout } = useAuth();
 * ```
 */
export function useAuth(): UseAuthReturn {
  const {
    user,
    tokens,
    isAuthenticated,
    isLoading,
    isInitialized,
    login,
    logout,
    refreshTokens,
  } = useAuthStore();

  // Computed values
  const role = user?.role as UserRole | undefined;
  const isVessel = isVesselRole(role);
  const isOffice = isOfficeRole(role);
  const isMaster = role === USER_ROLES.VESSEL_MASTER;
  const isCrew = role === USER_ROLES.VESSEL_CREW;
  const isPIC = canPerformPICActions(role);
  const isDPA = canPerformDPAActions(role);
  const formIds = user?.form_ids ?? [];
  const processIds = user?.process_ids ?? [];
  const formIdSet = useMemo(
    () => new Set(formIds.map((id) => normalizePermissionId(id, 'form')).filter(Boolean)),
    [formIds.join('|')]
  );
  const processIdSet = useMemo(
    () => new Set(processIds.map((id) => normalizePermissionId(id, 'process')).filter(Boolean)),
    [processIds.join('|')]
  );
  const canAccessReports = processIdSet.has(normalizePermissionId(PROCESS_IDS.VIEW_REPORTS, 'process'));
  const canImportOpenSource = canImportOpenSourceFeature(user?.user_type);
  const vesselId = user?.vessel_id ?? null;
  const fullName = user?.full_name ?? '';
  const hasForm = useCallback(
    (formId: string) => formIdSet.has(normalizePermissionId(formId, 'form')),
    [formIdSet]
  );
  const hasProcess = useCallback(
    (processId: string) => processIdSet.has(normalizePermissionId(processId, 'process')),
    [processIdSet]
  );

  return {
    // State
    user,
    tokens,
    isAuthenticated,
    isLoading,
    isInitialized,

    // Computed
    isVessel,
    isOffice,
    isMaster,
    isCrew,
    isPIC,
    isDPA,
    canAccessReports,
    canImportOpenSource,
    role,
    vesselId,
    fullName,
    formIds,
    processIds,
    hasForm,
    hasProcess,

    // Actions
    login,
    logout,
    refreshTokens,
  };
}

/**
 * Hook to initialize auth on app startup.
 * Should be called once in the root component.
 *
 * Usage:
 * ```tsx
 * function App() {
 *   useAuthInitializer();
 *   // ...
 * }
 * ```
 */
export function useAuthInitializer(): void {
  const initialize = useAuthStore((state) => state.initialize);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  useEffect(() => {
    if (!isInitialized) {
      // Migrate any legacy tokens first
      migrateLegacyTokens();
      // Then initialize
      initialize();
    }
  }, [initialize, isInitialized]);
}

/**
 * Hook that requires authentication.
 * Redirects to login if not authenticated after initialization.
 *
 * Usage:
 * ```tsx
 * function ProtectedPage() {
 *   const { isLoading } = useRequireAuth();
 *   if (isLoading) return <Loading />;
 *   // ...
 * }
 * ```
 */
export function useRequireAuth(): {
  isLoading: boolean;
  isAuthenticated: boolean;
} {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  useEffect(() => {
    if (isInitialized && !isAuthenticated && !isLoading) {
      window.location.href = '/login';
    }
  }, [isAuthenticated, isLoading, isInitialized]);

  return {
    isLoading: !isInitialized || isLoading,
    isAuthenticated,
  };
}

/**
 * Hook that checks for specific role(s).
 * Useful for conditional rendering based on permissions.
 *
 * Usage:
 * ```tsx
 * const { hasRole, hasAnyRole } = useRoleCheck();
 * if (hasRole('DPA')) { ... }
 * if (hasAnyRole(['OFFICE_PIC', 'OFFICE_SSQE'])) { ... }
 * ```
 */
export function useRoleCheck(): {
  hasRole: (requiredRole: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
} {
  const { role } = useAuth();

  const hasRole = useCallback(
    (requiredRole: UserRole): boolean => {
      return role === requiredRole;
    },
    [role]
  );

  const hasAnyRole = useCallback(
    (roles: UserRole[]): boolean => {
      return role !== undefined && roles.includes(role);
    },
    [role]
  );

  return { hasRole, hasAnyRole };
}

export default useAuth;
