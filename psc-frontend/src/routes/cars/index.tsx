/**
 * CAR List page route.
 *
 * Screen: CAR List (`/cars`) per APP_FLOW.md Section 2.3
 *
 * Features:
 * - List of CARs with filters
 * - Loading/empty/error states
 * - Pagination
 * - Overdue and missing evidence indicators
 * - Mobile-first responsive design
 * - No FAB (CARs are auto-created when deficiencies are added)
 *
 * PRD Reference: FEAT-CAR-009
 */

import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { CARList, CARFilters, PVCloseModal } from '@/components/car';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { carsApi } from '@/lib/api/cars';
import type { CARFilters as FilterType, CARStatus } from '@/types';

/**
 * Parse filters from URL search params
 */
function parseFiltersFromParams(params: URLSearchParams): FilterType {
  const filters: FilterType = {};

  const status = params.get('status');
  if (status) {
    filters.status = status as CARStatus;
  }

  const search = params.get('search');
  if (search) {
    filters.search = search;
  }

  const pvDue = params.get('pv_due');
  if (pvDue && ['1', 'true', 'yes'].includes(pvDue.toLowerCase())) {
    filters.pv_due = true;
  }

  const overdue = params.get('overdue');
  if (overdue && ['1', 'true', 'yes'].includes(overdue.toLowerCase())) {
    filters.is_overdue = true;
  }

  const vesselId = params.get('vessel_id');
  if (vesselId) {
    filters.vessel_id = vesselId;
  }

  return filters;
}

/**
 * Convert filters to URL search params
 */
function filtersToParams(filters: FilterType): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.status) {
    params.set('status', filters.status);
  }
  if (filters.search) {
    params.set('search', filters.search);
  }
  if (filters.pv_due !== undefined) {
    params.set('pv_due', String(filters.pv_due));
  }
  if (filters.is_overdue !== undefined) {
    params.set('overdue', String(filters.is_overdue));
  }
  if (filters.vessel_id) {
    params.set('vessel_id', String(filters.vessel_id));
  }

  return params;
}

export function CARListPage() {
  const { isOffice, isDPA, isPIC, user } = useAuth();
  const { toast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse initial filters from URL
  const [filters, setFilters] = useState<FilterType>(() =>
    parseFiltersFromParams(searchParams)
  );
  const searchParamsKey = searchParams.toString();

  // Current page (1-indexed)
  const [page, setPage] = useState(1);
  const [isResolvingPV, setIsResolvingPV] = useState(false);
  const [showPVClose, setShowPVClose] = useState(false);
  const [selectedCarId, setSelectedCarId] = useState<string | null>(null);
  const [selectedPvId, setSelectedPvId] = useState<string | null>(null);

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

  const handleQuickClosePV = useCallback(async (carId: number) => {
    setIsResolvingPV(true);
    try {
      const car = await carsApi.getCARDetail(carId);
      const pv = car.physical_verification;

      if (!pv || pv.status !== 'OPEN') {
        toast({
          variant: 'destructive',
          title: 'Verification not available',
          description: 'This CAR does not have an open physical verification.',
        });
        return;
      }

      const verifierUserId = pv.verifier_user_id?.trim().toLowerCase();
      const currentUserIds = [user?.employee_id, user?.id]
        .filter((value): value is string => Boolean(value))
        .map((value) => value.trim().toLowerCase());
      const isAssignedVerifier = Boolean(
        verifierUserId && currentUserIds.includes(verifierUserId)
      );

      const canQuickClose = isPIC || (isOffice && isAssignedVerifier);
      if (!canQuickClose) {
        toast({
          variant: 'destructive',
          title: 'Permission denied',
          description:
            'Only the assigned verifier, PIC reviewer, or DPA can close this verification.',
        });
        return;
      }

      setSelectedCarId(String(carId));
      setSelectedPvId(String(pv.id));
      setShowPVClose(true);
    } catch {
      toast({
        variant: 'destructive',
        title: 'Failed to load verification',
        description: 'Unable to load CAR verification details. Please try again.',
      });
    } finally {
      setIsResolvingPV(false);
    }
  }, [isDPA, isOffice, toast, user?.employee_id, user?.id]);

  return (
    <RootLayout>
      {/* Page header */}
      <PageHeader
        title="Corrective Action Reports"
        subtitle="Track and manage CARs for inspection deficiencies"
      />

      {/* Filters */}
      <CARFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        className="mb-4"
      />

      {/* CAR list */}
      <CARList
        filters={filters}
        onClearFilters={handleClearFilters}
        page={page}
        onPageChange={handlePageChange}
        canQuickClosePV={Boolean(filters.pv_due && (isOffice || isDPA) && !isResolvingPV)}
        onQuickClosePV={handleQuickClosePV}
      />

      {selectedCarId && selectedPvId && (
        <PVCloseModal
          open={showPVClose}
          onOpenChange={(open) => {
            setShowPVClose(open);
            if (!open) {
              setSelectedCarId(null);
              setSelectedPvId(null);
            }
          }}
          carId={selectedCarId}
          pvId={selectedPvId}
          onSuccess={() => {
            toast({
              title: 'Verification closed',
              description: 'Physical verification has been closed successfully.',
            });
            setShowPVClose(false);
            setSelectedCarId(null);
            setSelectedPvId(null);
          }}
        />
      )}
    </RootLayout>
  );
}

export default CARListPage;