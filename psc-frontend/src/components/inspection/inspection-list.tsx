import { type FC, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui';
import {
  ListSkeleton,
  EmptyStateInspections,
  EmptyStateFilterResults,
  ErrorState,
} from '@/components/shared';
import { InspectionCard } from './inspection-card';
import { useInspections } from '@/hooks/use-inspections';
import { useAuth } from '@/hooks/use-auth';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/utils/constants';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import type { InspectionFilters, InspectionStatus } from '@/types';

/**
 * Inspection list component per APP_FLOW.md Section 2.2
 *
 * Handles:
 * - Data fetching with useInspections hook
 * - Loading state (skeleton cards)
 * - Empty state (no inspections or no filter results)
 * - Error state with retry
 * - Pagination (Load More)
 */

export interface InspectionListProps {
  /** Current filter values */
  filters: InspectionFilters;
  /** Called when filters should be cleared */
  onClearFilters: () => void;
  /** Current page number */
  page: number;
  /** Called when page changes (for pagination) */
  onPageChange: (page: number) => void;
  /** Additional class names */
  className?: string;
}

export const InspectionList: FC<InspectionListProps> = ({
  filters,
  onClearFilters,
  page,
  onPageChange,
  className,
}) => {
  const navigate = useNavigate();
  const { hasProcess } = useAuth();

  const {
    data,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useInspections({ filters, page });

  const handleCreateFirst = useCallback(() => {
    navigate(ROUTES.INSPECTION_NEW);
  }, [navigate]);

  const handleLoadMore = useCallback(() => {
    onPageChange(page + 1);
  }, [page, onPageChange]);

  const handleRetry = useCallback(() => {
    refetch();
  }, [refetch]);

  // Check if any filters are active
  const hasActiveFilters =
    filters.inspection_type ||
    filters.status ||
    filters.search ||
    filters.is_detention !== undefined ||
    filters.date_from ||
    filters.date_to;

  // Loading state - show skeleton
  if (isLoading) {
    return <ListSkeleton count={5} variant="card" className={className} />;
  }

  // Error state
  if (isError) {
    return (
      <ErrorState
        title="Failed to load inspections"
        message={error?.message || 'An error occurred while loading inspections.'}
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
        />
      );
    }
    return (
      <EmptyStateInspections
        onCreateFirst={hasProcess(PROCESS_IDS.CREATE_INSPECTION) ? handleCreateFirst : undefined}
      />
    );
  }

  const hasMore = page < data.pagination.total_pages;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Inspection cards */}
      <div className="space-y-3">
        {data.data.map((inspection) => (
          <InspectionCard
            key={inspection.id}
            id={inspection.id}
            vesselName={inspection.vessel_name}
            inspectionType={inspection.inspection_type}
            pscSubtype={inspection.psc_subtype}
            inspectionDate={inspection.inspection_date}
            port={inspection.port}
            portState={inspection.port_state}
            mouCode={inspection.mou_code}
            isDetention={inspection.is_detention}
            status={inspection.operational_status as InspectionStatus}
            deficiencyCount={inspection.deficiency_count}
            openDeficiencyCount={inspection.open_deficiency_count}
          />
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
        Showing {data.data.length} of {data.pagination.total_count} inspections
      </div>
    </div>
  );
};
