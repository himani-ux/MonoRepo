import { type FC, useCallback } from 'react';
import { X } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Button,
} from '@/components/ui';
import { SearchInput } from '@/components/shared';
import { cn } from '@/lib/utils';
import { CAR_STATUS } from '@/lib/utils/constants';
import type { CARFilters as FilterType, CARStatus } from '@/types';

/**
 * CAR filters component per APP_FLOW.md Section 2.3
 *
 * Provides filtering controls for:
 * - Status (unified workflow: ALLOTTED → CLOSED)
 * - Search (CAR number, vessel name)
 * - Clear filters button
 */

export interface CARFiltersProps {
  /** Current filter values */
  filters: FilterType;
  /** Called when filters change */
  onFiltersChange: (filters: FilterType) => void;
  /** Additional class names */
  className?: string;
}

/** Status options for dropdown (unified workflow) */
const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: CAR_STATUS.ALLOTTED, label: 'Allotted' },
  { value: CAR_STATUS.IN_PROGRESS, label: 'In Progress' },
  { value: CAR_STATUS.PENDING_CE_REVIEW, label: 'Pending CE Review' },
  { value: CAR_STATUS.PENDING_MASTER_REVIEW, label: 'Pending Master Review' },
  { value: CAR_STATUS.SUBMITTED_TO_PIC, label: 'Submitted to PIC' },
  { value: CAR_STATUS.PIC_REVIEW, label: 'PIC Review' },
  { value: CAR_STATUS.SUBMITTED_TO_DPA, label: 'Submitted to DPA' },
  { value: CAR_STATUS.CLOSED, label: 'Closed' },
  { value: CAR_STATUS.RETURNED_FOR_REWORK, label: 'Returned for Rework' },
];

export const CARFilters: FC<CARFiltersProps> = ({
  filters,
  onFiltersChange,
  className,
}) => {
  const handleStatusChange = useCallback(
    (value: string) => {
      onFiltersChange({
        ...filters,
        status: (value === 'all' ? undefined : value) as CARStatus | undefined,
      });
    },
    [filters, onFiltersChange]
  );

  const handleSearchChange = useCallback(
    (value: string) => {
      onFiltersChange({
        ...filters,
        search: value || undefined,
      });
    },
    [filters, onFiltersChange]
  );

  const handleClearFilters = useCallback(() => {
    onFiltersChange({});
  }, [onFiltersChange]);

  const handlePVDueToggle = useCallback(() => {
    onFiltersChange({
      ...filters,
      pv_due: filters.pv_due ? undefined : true,
    });
  }, [filters, onFiltersChange]);

  const handleOverdueToggle = useCallback(() => {
    onFiltersChange({
      ...filters,
      is_overdue: filters.is_overdue ? undefined : true,
    });
  }, [filters, onFiltersChange]);

  // Check if any filters are active
  const hasActiveFilters =
    filters.status ||
    filters.pv_due !== undefined ||
    filters.search ||
    filters.is_overdue !== undefined ||
    filters.has_missing_evidence !== undefined;

  return (
    <div className={cn('space-y-3', className)}>
      {/* Filter row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        {/* Status filter */}
        <Select
          value={filters.status || 'all'}
          onValueChange={handleStatusChange}
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value || 'all'} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Search input */}
        <div className="flex-1">
          <SearchInput
            value={filters.search || ''}
            onChange={handleSearchChange}
            placeholder="Search CAR number, vessel..."
            className="w-full"
          />
        </div>

        <Button
          type="button"
          variant={filters.pv_due ? 'default' : 'outline'}
          size="sm"
          onClick={handlePVDueToggle}
          className="flex-shrink-0"
        >
          PV Due
        </Button>

        <Button
          type="button"
          variant={filters.is_overdue ? 'default' : 'outline'}
          size="sm"
          onClick={handleOverdueToggle}
          className="flex-shrink-0"
        >
          Overdue
        </Button>

        {/* Clear filters button */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="flex-shrink-0"
          >
            <X className="mr-1 h-4 w-4" />
            Clear
          </Button>
        )}
      </div>

      {(filters.is_overdue || filters.pv_due) && (
        <div className="flex flex-wrap gap-2">
          {filters.is_overdue && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
              Overdue active
            </span>
          )}
          {filters.pv_due && (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
              PV Due active
            </span>
          )}
        </div>
      )}
    </div>
  );
};
