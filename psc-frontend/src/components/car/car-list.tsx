import { type FC, useCallback } from 'react';
import { Button } from '@/components/ui';
import {
  ListSkeleton,
  EmptyStateCARs,
  EmptyStateFilterResults,
  ErrorState,
} from '@/components/shared';
import { CARCard } from './car-card';
import { useCARs } from '@/hooks/use-cars';
import { cn } from '@/lib/utils';
import type { CARFilters, CARStatus } from '@/types';

/**
 * CAR list component per APP_FLOW.md Section 2.3
 *
 * Handles:
 * - Data fetching with useCARs hook
 * - Loading state (skeleton cards)
 * - Empty state (no CARs or no filter results)
 * - Error state with retry
 * - Pagination (Load More)
 * - Overdue and missing evidence computation
 */

export interface CARListProps {
  /** Current filter values */
  filters: CARFilters;
  /** Called when filters should be cleared */
  onClearFilters: () => void;
  /** Current page number */
  page: number;
  /** Called when page changes (for pagination) */
  onPageChange: (page: number) => void;
  /** Whether the quick-close action should be shown for PV due rows */
  canQuickClosePV?: boolean;
  /** Quick-close handler (used by PV Due operational flow) */
  onQuickClosePV?: (carId: number) => void;
  /** Additional class names */
  className?: string;
}

/** Compute whether a CAR is overdue based on target_date and status */
function isOverdue(targetDate: string | null, status: string): boolean {
  if (!targetDate || status === 'DPA_CLOSED') return false;
  return new Date(targetDate) < new Date();
}

/** Compute whether a CAR has missing evidence */
function hasMissingEvidence(
  beforeCount: number,
  afterCount: number
): boolean {
  return beforeCount === 0 || afterCount === 0;
}

export const CARList: FC<CARListProps> = ({
  filters,
  onClearFilters,
  page,
  onPageChange,
  canQuickClosePV = false,
  onQuickClosePV,
  className,
}) => {
  const {
    data,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useCARs({ filters, page });

  const handleLoadMore = useCallback(() => {
    onPageChange(page + 1);
  }, [page, onPageChange]);

  const handleRetry = useCallback(() => {
    refetch();
  }, [refetch]);

  // Check if any filters are active
  const hasActiveFilters =
    filters.status ||
    filters.pv_due !== undefined ||
    filters.search ||
    filters.is_overdue !== undefined ||
    filters.has_missing_evidence !== undefined;

  // Loading state - show skeleton
  if (isLoading) {
    return <ListSkeleton count={5} variant="card" className={className} />;
  }

  // Error state
  if (isError) {
    return (
      <ErrorState
        title="Failed to load CARs"
        message={error?.message || 'An error occurred while loading CARs.'}
        onRetry={handleRetry}
        className={className}
      />
    );
  }

  // Empty state - no data
  if (!data?.data?.length) {
    if (hasActiveFilters) {
      return (
        <EmptyStateFilterResults
          onClearFilters={onClearFilters}
          title="No CARs found"
          description="No CARs match your current filter criteria."
        />
      );
    }
    return <EmptyStateCARs />;
  }

  const cars = data.data;
  const { total_count, page: currentPage, total_pages } = data.pagination;
  const hasMore = currentPage < total_pages;

  return (
    <div className={cn('space-y-4', className)}>
      {/* CAR cards */}
      <div className="space-y-3">
        {cars.map((car) => (
          <div key={car.id} className="space-y-2">
            <CARCard
              id={car.id}
              carNumber={car.car_number}
              defCode={car.def_code}
              deficiencyDescription={car.deficiency_description}
              vesselName={car.vessel_name}
              status={car.status as CARStatus}
              targetDate={car.target_date}
              isOverdue={isOverdue(car.target_date, car.status)}
              hasMissingEvidence={hasMissingEvidence(
                car.before_evidence_count,
                car.after_evidence_count
              )}
              pvDue={Boolean(car.pv_due)}
              inspectionType={car.inspection_type}
            />
            {canQuickClosePV && car.pv_due && onQuickClosePV && (
              <div className="flex justify-end">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => onQuickClosePV(car.id)}
                >
                  Close Verification
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Load more / Pagination */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <Button
            variant="outline"
            onClick={handleLoadMore}
            disabled={isFetching}
          >
            {isFetching ? 'Loading...' : 'Load More'}
          </Button>
        </div>
      )}

      {/* Results count */}
      <div className="text-center text-sm text-neutral-500">
        Showing {cars.length} of {total_count} CARs
      </div>
    </div>
  );
};
