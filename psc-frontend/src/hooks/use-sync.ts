/**
 * Sync hooks using TanStack Query.
 *
 * Per FRONTEND_GUIDELINES.md Section 4.1
 * Implements: PRD.md FEAT-SYNC-004
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getConflicts } from '@/lib/api/sync';

// ============================================================================
// Query Key Factory
// ============================================================================

export const syncKeys = {
  all: ['sync'] as const,
  conflicts: () => [...syncKeys.all, 'conflicts'] as const,
};

// ============================================================================
// Conflicts Hook
// ============================================================================

/**
 * Fetch unresolved sync conflicts from the backend.
 *
 * Only fetches when `enabled` is true (typically when conflict count > 0
 * and user is online). Refetches after each sync cycle.
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: FEAT-SYNC-004
 */
export function useConflicts(enabled: boolean = true) {
  return useQuery({
    queryKey: syncKeys.conflicts(),
    queryFn: getConflicts,
    enabled,
    staleTime: 30_000, // 30 seconds — conflicts change infrequently
  });
}

/**
 * Invalidate the conflicts query to trigger a refetch.
 * Call after resolving a conflict or completing a sync.
 */
export function useInvalidateConflicts() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: syncKeys.conflicts() });
}
