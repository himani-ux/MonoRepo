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
import { INSPECTION_TYPES } from '@/lib/utils/constants';
import type { InspectionFilters as FilterType, InspectionType, InspectionStatus } from '@/types';

/**
 * Inspection filters component per APP_FLOW.md Section 2.2
 *
 * Provides filtering controls for:
 * - Inspection type (PSC, RS, AUDIT)
 * - Status (DRAFT, SUBMITTED, PIC_REVIEWED, DPA_CLOSED)
 * - Search (vessel name, port)
 * - Clear filters button
 */

export interface InspectionFiltersProps {
  /** Current filter values */
  filters: FilterType;
  /** Called when filters change */
  onFiltersChange: (filters: FilterType) => void;
  /** Additional class names */
  className?: string;
}

/** Type options for dropdown */
const typeOptions = [
  { value: 'all', label: 'All Types' },
  { value: INSPECTION_TYPES.PSC, label: 'PSC' },
  { value: INSPECTION_TYPES.RS, label: 'RightShip' },
  { value: INSPECTION_TYPES.AUDIT, label: 'Audit' },
];

/** Status options for dropdown (computed operational status) */
const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'OPEN', label: 'Open' },
  { value: 'CLOSED', label: 'Closed' },
];

export const InspectionFilters: FC<InspectionFiltersProps> = ({
  filters,
  onFiltersChange,
  className,
}) => {
  const handleTypeChange = useCallback(
    (value: string) => {
      onFiltersChange({
        ...filters,
        inspection_type: (value === 'all' ? undefined : value) as InspectionType | undefined,
      });
    },
    [filters, onFiltersChange]
  );

  const handleStatusChange = useCallback(
    (value: string) => {
      onFiltersChange({
        ...filters,
        status: (value === 'all' ? undefined : value) as InspectionStatus | undefined,
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

  const handleDetentionToggle = useCallback(() => {
    onFiltersChange({
      ...filters,
      is_detention: filters.is_detention ? undefined : true,
    });
  }, [filters, onFiltersChange]);

  // Check if any filters are active
  const hasActiveFilters =
    filters.inspection_type ||
    filters.status ||
    filters.search ||
    filters.is_detention !== undefined ||
    filters.date_from ||
    filters.date_to;

  return (
    <div className={cn('space-y-3', className)}>
      {/* Filter row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        {/* Type filter */}
        <Select
          value={filters.inspection_type || 'all'}
          onValueChange={handleTypeChange}
        >
          <SelectTrigger className="w-full sm:w-[140px]">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            {typeOptions.map((option) => (
              <SelectItem key={option.value || 'all'} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Status filter */}
        <Select
          value={filters.status || 'all'}
          onValueChange={handleStatusChange}
        >
          <SelectTrigger className="w-full sm:w-[160px]">
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
            placeholder="Search vessel, port..."
            className="w-full"
          />
        </div>

        <Button
          type="button"
          variant={filters.is_detention ? 'default' : 'outline'}
          size="sm"
          onClick={handleDetentionToggle}
          className="flex-shrink-0"
        >
          Detentions
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

      {(filters.is_detention || filters.date_from) && (
        <div className="flex flex-wrap gap-2">
          {filters.is_detention && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
              Detention active
            </span>
          )}
          {filters.date_from && (
            <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-700">
              From {filters.date_from}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
