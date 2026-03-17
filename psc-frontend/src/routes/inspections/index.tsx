/**
 * Inspection List page route.
 *
 * Screen: Inspection List (`/inspections`) per APP_FLOW.md Section 2.2
 *
 * Features:
 * - List of inspections with filters
 * - FAB for creating new inspection
 * - Loading/empty/error states
 * - Pagination
 * - Mobile-first responsive design
 *
 * PRD Reference: FEAT-INS-010
 */

import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Plus, Download } from 'lucide-react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { Button } from '@/components/ui';
import { InspectionList, InspectionFilters } from '@/components/inspection';
import { ROUTES } from '@/lib/utils/constants';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import { exportDeficiencyExcel } from '@/lib/api/inspections';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/use-auth';
import type { InspectionFilters as FilterType, InspectionType, InspectionStatus } from '@/types';

/**
 * Parse filters from URL search params
 */
function parseFiltersFromParams(params: URLSearchParams): FilterType {
  const filters: FilterType = {};

  const type = params.get('type');
  if (type) {
    filters.inspection_type = type as InspectionType;
  }

  const status = params.get('status');
  if (status) {
    filters.status = status as InspectionStatus;
  }

  const search = params.get('search');
  if (search) {
    filters.search = search;
  }

  const dateFrom = params.get('date_from');
  if (dateFrom) {
    filters.date_from = dateFrom;
  }

  const dateTo = params.get('date_to');
  if (dateTo) {
    filters.date_to = dateTo;
  }

  const detention = params.get('detention');
  if (detention === 'true') {
    filters.is_detention = true;
  }

  return filters;
}

/**
 * Convert filters to URL search params
 */
function filtersToParams(filters: FilterType): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.inspection_type) {
    params.set('type', filters.inspection_type);
  }
  if (filters.status) {
    params.set('status', filters.status);
  }
  if (filters.search) {
    params.set('search', filters.search);
  }
  if (filters.date_from) {
    params.set('date_from', filters.date_from);
  }
  if (filters.date_to) {
    params.set('date_to', filters.date_to);
  }
  if (filters.is_detention) {
    params.set('detention', 'true');
  }

  return params;
}

export function InspectionListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const { hasProcess } = useAuth();
  const [isExporting, setIsExporting] = useState(false);

  // Parse initial filters from URL
  const [filters, setFilters] = useState<FilterType>(() =>
    parseFiltersFromParams(searchParams)
  );
  const searchParamsKey = searchParams.toString();

  // Current page (1-indexed)
  const [page, setPage] = useState(1);

  useEffect(() => {
    setFilters(parseFiltersFromParams(new URLSearchParams(searchParamsKey)));
    setPage(1);
  }, [searchParamsKey]);

  // Handle filter changes - update URL and reset page
  const handleFiltersChange = useCallback(
    (newFilters: FilterType) => {
      setFilters(newFilters);
      setPage(1); // Reset to first page on filter change

      // Update URL params
      const params = filtersToParams(newFilters);
      setSearchParams(params, { replace: true });
    },
    [setSearchParams]
  );

  // Handle clear filters
  const handleClearFilters = useCallback(() => {
    setFilters({});
    setPage(1);
    setSearchParams(new URLSearchParams(), { replace: true });
  }, [setSearchParams]);

  // Handle page change for pagination
  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  // Navigate to create new inspection
  const handleCreateNew = useCallback(() => {
    navigate(ROUTES.INSPECTION_NEW);
  }, [navigate]);

  // Excel export handler — FEAT-RPT-002
  const handleExportExcel = useCallback(async () => {
    setIsExporting(true);
    try {
      const blob = await exportDeficiencyExcel({
        status: filters.status,
        inspection_type: filters.inspection_type,
        date_from: filters.date_from,
        date_to: filters.date_to,
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Deficiency_Export_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      toast({
        variant: 'destructive',
        title: 'Export failed',
        description: 'Failed to generate Excel export. Please try again.',
      });
    } finally {
      setIsExporting(false);
    }
  }, [filters, toast]);

  return (
    <RootLayout>
      {/* Page header */}
      <PageHeader
        title="Inspections"
        subtitle="PSC, RightShip, and Audit inspections"
        actions={
          hasProcess(PROCESS_IDS.VIEW_INSPECTIONS) ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportExcel}
              disabled={isExporting}
            >
              <Download className="mr-2 h-4 w-4" />
              {isExporting ? 'Exporting...' : 'Export Excel'}
            </Button>
          ) : undefined
        }
      />

      {/* Filters */}
      <InspectionFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        className="mb-4"
      />

      {/* Inspection list */}
      <InspectionList
        filters={filters}
        onClearFilters={handleClearFilters}
        page={page}
        onPageChange={handlePageChange}
      />

      {/* FAB - Create new inspection (hidden from crew) */}
      {hasProcess(PROCESS_IDS.CREATE_INSPECTION) && (
        <Button
          onClick={handleCreateNew}
          size="lg"
          className="fixed bottom-20 right-4 z-40 h-14 w-14 rounded-full shadow-lg md:bottom-6 md:right-6 md:h-auto md:w-auto md:rounded-lg md:px-4"
          aria-label="Create new inspection"
        >
          <Plus className="h-6 w-6 md:mr-2 md:h-5 md:w-5" />
          <span className="hidden md:inline">New Inspection</span>
        </Button>
      )}
    </RootLayout>
  );
}

export default InspectionListPage;
