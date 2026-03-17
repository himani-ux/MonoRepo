/**
 * Dashboard data hook using TanStack Query.
 */

import { useQuery } from '@tanstack/react-query';
import { fetchDashboard, type DashboardData } from '@/lib/api/dashboard';
import { STALE_TIME } from '@/lib/utils/constants';

export const dashboardKeys = {
  all: ['dashboard'] as const,
  data: (vesselId?: string) => [...dashboardKeys.all, { vesselId }] as const,
};

export interface UseDashboardOptions {
  enabled?: boolean;
}

export function useDashboard(vesselId?: string, options: UseDashboardOptions = {}) {
  const { enabled = true } = options;

  return useQuery<DashboardData>({
    queryKey: dashboardKeys.data(vesselId),
    queryFn: () => fetchDashboard(vesselId),
    staleTime: STALE_TIME.DASHBOARD,
    enabled,
  });
}
