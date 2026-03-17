/**
 * Deficiency Dashboard page route.
 *
 * Screen: Deficiency List (`/deficiencies`) — Master workflow dashboard
 *
 * Features:
 * - List of deficiencies scoped to user's vessel
 * - Filter by status, awaiting review toggle
 * - Click card to open detail dialog with workflow actions
 * - Pagination
 */

import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { Button } from '@/components/ui';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { Skeleton } from '@/components/ui';
import { ErrorState } from '@/components/shared';
import { DeficiencyCard } from '@/components/inspection/deficiency-card';
import { DeficiencyDetailDialog } from '@/components/inspection/deficiency-detail-dialog';
import { useDeficiencies } from '@/hooks/use-deficiencies';
import type { DeficiencyFilters } from '@/lib/api/deficiencies';
import type { DeficiencyDetail, CARStatus } from '@/types';

const CAR_STATUS_OPTIONS: { label: string; value: string }[] = [
  { label: 'All Statuses', value: 'ALL' },
  { label: 'Allotted', value: 'ALLOTTED' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'Pending CE Review', value: 'PENDING_CE_REVIEW' },
  { label: 'Pending Master Review', value: 'PENDING_MASTER_REVIEW' },
  { label: 'Submitted to PIC', value: 'SUBMITTED_TO_PIC' },
  { label: 'PIC Review', value: 'PIC_REVIEW' },
  { label: 'Submitted to DPA', value: 'SUBMITTED_TO_DPA' },
  { label: 'Closed', value: 'CLOSED' },
  { label: 'Returned for Rework', value: 'RETURNED_FOR_REWORK' },
];

function parseFiltersFromParams(params: URLSearchParams): DeficiencyFilters {
  const filters: DeficiencyFilters = {};
  const carStatus = params.get('car_status');
  if (carStatus) filters.car_status = carStatus as CARStatus;
  if (params.get('awaiting_review') === 'true') filters.awaiting_review = true;
  const defCode = params.get('def_code');
  if (defCode) filters.def_code = defCode;
  const vesselId = params.get('vessel_id');
  if (vesselId) filters.vessel_id = vesselId;
  return filters;
}

function filtersToParams(filters: DeficiencyFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.car_status) params.set('car_status', filters.car_status);
  if (filters.awaiting_review) params.set('awaiting_review', 'true');
  if (filters.def_code) params.set('def_code', filters.def_code);
  if (filters.vessel_id) params.set('vessel_id', filters.vessel_id);
  return params;
}

export function DeficiencyDashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [selectedDef, setSelectedDef] = useState<DeficiencyDetail | null>(null);

  const filters = parseFiltersFromParams(searchParams);
  const showDashboardFilterPendingBanner =
    searchParams.get('dashboard_source') === 'repeat_deficiencies' &&
    searchParams.get('filter_pending') === 'repeat_filters';

  const { data, isLoading, isError, error, refetch } = useDeficiencies({
    filters,
    page,
  });

  const handleFilterChange = useCallback(
    (newFilters: DeficiencyFilters) => {
      setSearchParams(filtersToParams(newFilters));
      setPage(1);
    },
    [setSearchParams]
  );

  const handleStatusFilter = useCallback(
    (value: string) => {
      handleFilterChange({
        ...filters,
        car_status: value && value !== 'ALL' ? (value as CARStatus) : undefined,
      });
    },
    [filters, handleFilterChange]
  );

  const handleAwaitingReviewToggle = useCallback(() => {
    handleFilterChange({
      ...filters,
      awaiting_review: filters.awaiting_review ? undefined : true,
      car_status: filters.awaiting_review ? filters.car_status : undefined,
    });
  }, [filters, handleFilterChange]);

  const deficiencies = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <RootLayout>
      <PageHeader title="Deficiency Workflow" subtitle="Manage vessel deficiency assignments and approvals" />

      {showDashboardFilterPendingBanner && (
        <div className="mb-4 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            Dashboard repeat-deficiency filters are not supported by the current API yet.
            Showing the base deficiency list.
          </p>
        </div>
      )}

      {/* Filter bar */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Select value={filters.car_status || 'ALL'} onValueChange={handleStatusFilter}>
          <SelectTrigger className="w-52">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            {CAR_STATUS_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button
          variant={filters.awaiting_review ? 'default' : 'outline'}
          size="sm"
          onClick={handleAwaitingReviewToggle}
        >
          Awaiting Review
        </Button>
      </div>

      {/* Content */}
      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <ErrorState
          message={error?.message || 'Failed to load deficiencies.'}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && deficiencies.length === 0 && (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-gray-500">
          No deficiencies found matching the current filters.
        </div>
      )}

      {!isLoading && !isError && deficiencies.length > 0 && (
        <>
          <div className="space-y-3">
            {deficiencies.map((def) => (
              <DeficiencyCard
                key={String(def.id)}
                deficiency={def}
                onClick={() => setSelectedDef(def)}
              />
            ))}
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <span className="text-sm text-gray-500">
                Page {pagination.page} of {pagination.total_pages} ({pagination.total_count} total)
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= pagination.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Deficiency Detail Dialog */}
      <DeficiencyDetailDialog
        deficiency={selectedDef}
        open={!!selectedDef}
        onOpenChange={(open) => {
          if (!open) setSelectedDef(null);
        }}
      />
    </RootLayout>
  );
}

export default DeficiencyDashboardPage;
