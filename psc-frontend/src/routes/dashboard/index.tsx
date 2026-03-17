/**
 * Dashboard page — landing page for master + office users.
 *
 * Uses Dashboard API aggregates + recent inspections list to render KPI-driven
 * summary cards and monitoring sections.
 */

import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Anchor,
  Calendar,
  ShieldCheck,
  Ship,
  Target,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import {
  Button,
  Card,
  CardContent,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
} from '@/components/ui';
import { ErrorState, StatusBadge } from '@/components/shared';
import { StatCard, TopDefCodes } from '@/components/dashboard';
import { useAuth } from '@/hooks/use-auth';
import { useCARs } from '@/hooks/use-cars';
import { useDashboard } from '@/hooks/use-dashboard';
import { useInspections } from '@/hooks/use-inspections';
import { ROUTES } from '@/lib/utils/constants';
import type { InspectionStatus } from '@/types';
import type { RepeatDeficiencyGroup as ApiRepeatDeficiencyGroup } from '@/lib/api/dashboard';

function formatDateForQuery(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function daysAgo(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return formatDateForQuery(date);
}

function formatMonthLabel(month: string): string {
  const [year, m] = month.split('-');
  const date = new Date(Number(year), Number(m) - 1);
  return date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' });
}

function getYearFromMonth(month: string): string {
  return month.split('-')[0] || '';
}

const TREND_MONTH_OPTIONS = [1, 3, 6, 12, 24, 36] as const;
const TREND_YEAR_OPTIONS = [1, 2, 3] as const;
const DEF_TARGET_DEFAULT = 2;
const DEF_TARGET_DEFAULT_KEY = 'dashboard:def_target:default';

function normalizeVesselId(vesselId?: string | null): string | undefined {
  if (!vesselId) {
    return undefined;
  }
  const normalized = vesselId.trim();
  return normalized.length > 0 ? normalized : undefined;
}

function getDefTargetStorageKey(vesselId?: string | null): string {
  const normalizedVesselId = normalizeVesselId(vesselId);
  if (!normalizedVesselId) {
    return DEF_TARGET_DEFAULT_KEY;
  }
  return `dashboard:def_target:vessel:${normalizedVesselId}`;
}

function parseStoredDefTarget(value: string | null): number | undefined {
  if (value === null) {
    return undefined;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return undefined;
  }
  return parsed;
}

function readStoredDefTarget(storageKey: string): number | undefined {
  if (typeof window === 'undefined') {
    return undefined;
  }
  try {
    const direct = parseStoredDefTarget(window.localStorage.getItem(storageKey));
    if (direct !== undefined) {
      return direct;
    }
    if (storageKey !== DEF_TARGET_DEFAULT_KEY) {
      return parseStoredDefTarget(window.localStorage.getItem(DEF_TARGET_DEFAULT_KEY));
    }
  } catch {
    return undefined;
  }
  return undefined;
}

interface RepeatDeficiencyVessel {
  vessel_id: string;
  vessel_name: string;
  vessel_code?: string;
}

interface RepeatDeficiencyGroup {
  def_code: string;
  def_title: string;
  repeat_count: number;
  classification?: string;
  vessels: RepeatDeficiencyVessel[];
  range_from?: string;
  range_to?: string;
}

function RepeatDeficienciesSection({
  data,
  hasBackendData,
  onRowClick,
  onVesselClick,
}: {
  data: RepeatDeficiencyGroup[];
  hasBackendData: boolean;
  onRowClick: (group: RepeatDeficiencyGroup) => void;
  onVesselClick: (group: RepeatDeficiencyGroup, vesselId: string) => void;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-4 flex items-center justify-between gap-2">
          <h3 className="text-sm font-medium text-gray-700">Repeat Deficiencies</h3>
          {!hasBackendData ? (
            <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs font-semibold text-neutral-600">
              Not available
            </span>
          ) : (
            <span className="rounded bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700">
              {data.length} found
            </span>
          )}
        </div>

        {!hasBackendData ? (
          <div className="rounded-md border border-dashed border-neutral-200 bg-neutral-50 p-4 text-sm text-neutral-600">
            Repeat deficiency insights are not available yet for this dashboard view.
          </div>
        ) : data.length === 0 ? (
          <div className="rounded-md border border-dashed border-neutral-200 p-4 text-sm text-neutral-500">
            No repeat deficiencies found for the current scope.
          </div>
        ) : (
          <div className="space-y-3">
            {data.map((group) => {
              const vesselCount = new Set((group.vessels || []).map((vessel) => vessel.vessel_id)).size;
              const isSystemic = vesselCount >= 2;
              const classification = isSystemic ? 'Systemic' : 'Recurring';

              return (
                <div key={`${group.def_code}-${classification}`} className="rounded-md border border-neutral-200">
                  <button
                    type="button"
                    className="flex w-full items-center gap-3 p-3 text-left hover:bg-neutral-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
                    onClick={() => onRowClick(group)}
                  >
                    <div
                      className={
                        isSystemic
                          ? 'rounded-md bg-red-50 px-2 py-1 text-xs font-bold text-red-700'
                          : 'rounded-md bg-amber-50 px-2 py-1 text-xs font-bold text-amber-700'
                      }
                    >
                      {group.repeat_count}x
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-neutral-800">{group.def_code}</p>
                      <p className="truncate text-xs text-neutral-600">{group.def_title}</p>
                    </div>

                    <span
                      className={
                        isSystemic
                          ? 'rounded bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700'
                          : 'rounded bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700'
                      }
                    >
                      {classification}
                    </span>
                  </button>

                  {group.vessels?.length > 0 && (
                    <div className="flex flex-wrap gap-2 border-t border-neutral-100 px-3 pb-3 pt-2">
                      {group.vessels.map((vessel) => (
                        <button
                          key={`${group.def_code}-${vessel.vessel_id}`}
                          type="button"
                          className="rounded bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-700 hover:bg-neutral-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
                          onClick={() => onVesselClick(group, vessel.vessel_id)}
                        >
                          {vessel.vessel_name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { isOffice, isDPA, vesselId } = useAuth();
  const [selectedVessel, setSelectedVessel] = useState<string | undefined>();
  const [targetOpen, setTargetOpen] = useState(false);
  const [defTarget, setDefTarget] = useState<number>(DEF_TARGET_DEFAULT);
  const [targetDraft, setTargetDraft] = useState<string>(String(DEF_TARGET_DEFAULT));
  const [trendMode, setTrendMode] = useState<'monthly' | 'yearly'>('monthly');
  const [trendRangeMonths, setTrendRangeMonths] = useState<string>('12');
  const [trendRangeYears, setTrendRangeYears] = useState<string>('1');

  const scopedVesselId = isOffice ? selectedVessel : undefined;
  const targetVesselId = scopedVesselId ?? vesselId ?? undefined;
  const defTargetStorageKey = useMemo(
    () => getDefTargetStorageKey(targetVesselId),
    [targetVesselId]
  );
  const recentInspectionFilters = useMemo(
    () =>
      scopedVesselId
        ? ({ vessel_id: scopedVesselId as unknown as number })
        : {},
    [scopedVesselId]
  );

  const { data, isLoading, isError, error, refetch } = useDashboard(scopedVesselId);
  const { data: recentInspections, isLoading: isRecentInspectionsLoading } = useInspections({
    filters: recentInspectionFilters,
    page: 1,
    pageSize: 5,
  });

  const pvDueFilters = useMemo(
    () => ({
      pv_due: true,
      ...(scopedVesselId ? { vessel_id: scopedVesselId } : {}),
    }),
    [scopedVesselId]
  );
  const { data: pvDueList } = useCARs({
    filters: pvDueFilters,
    page: 1,
    pageSize: 1,
  });

  const pvDueCount = pvDueList?.pagination?.total_count ?? 0;
  const inspections = recentInspections?.data ?? [];
  const allMonthlyTrend = useMemo(() => data?.monthly_def_trend ?? [], [data?.monthly_def_trend]);

  const monthRangeOptions = useMemo(() => {
    const options = TREND_MONTH_OPTIONS
      .filter((months) => months <= 12 || months <= allMonthlyTrend.length)
      .map((months) => ({ value: String(months), label: `${months}m` }));
    return options;
  }, [allMonthlyTrend.length]);

  const yearlyTotals = useMemo(() => {
    const yearlyMap = new Map<string, number>();
    allMonthlyTrend.forEach((month) => {
      const year = getYearFromMonth(month.month);
      if (!year) return;
      yearlyMap.set(year, (yearlyMap.get(year) || 0) + month.count);
    });

    return Array.from(yearlyMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([year, count]) => ({ label: year, count }));
  }, [allMonthlyTrend]);

  const yearRangeOptions = useMemo(() => {
    return TREND_YEAR_OPTIONS
      .filter((years) => years <= yearlyTotals.length)
      .map((years) => ({ value: String(years), label: `${years}y` }));
  }, [yearlyTotals.length]);

  useEffect(() => {
    const storedTarget = readStoredDefTarget(defTargetStorageKey);
    const resolvedTarget = storedTarget ?? DEF_TARGET_DEFAULT;
    setDefTarget(resolvedTarget);
    setTargetDraft(String(resolvedTarget));
  }, [defTargetStorageKey]);

  useEffect(() => {
    if (monthRangeOptions.length === 0) return;
    if (!monthRangeOptions.some((opt) => opt.value === trendRangeMonths)) {
      setTrendRangeMonths(monthRangeOptions[monthRangeOptions.length - 1].value);
    }
  }, [monthRangeOptions, trendRangeMonths]);

  useEffect(() => {
    if (yearRangeOptions.length === 0) return;
    if (!yearRangeOptions.some((opt) => opt.value === trendRangeYears)) {
      setTrendRangeYears(yearRangeOptions[yearRangeOptions.length - 1].value);
    }
  }, [yearRangeOptions, trendRangeYears]);

  const monthlyTrend = useMemo(() => {
    const months = Number(trendRangeMonths);
    if (!Number.isFinite(months) || months <= 0) return allMonthlyTrend;
    return allMonthlyTrend.slice(-months);
  }, [allMonthlyTrend, trendRangeMonths]);

  const yearlyTrend = useMemo(() => {
    const years = Number(trendRangeYears);
    if (!Number.isFinite(years) || years <= 0) return yearlyTotals;
    return yearlyTotals.slice(-years);
  }, [trendRangeYears, yearlyTotals]);

  const activeTrendData = useMemo(() => {
    if (trendMode === 'yearly') {
      return yearlyTrend;
    }
    return monthlyTrend.map((item) => ({
      label: formatMonthLabel(item.month),
      count: item.count,
    }));
  }, [monthlyTrend, trendMode, yearlyTrend]);

  const trendLabel = useMemo(() => {
    if (activeTrendData.length === 0) return 'No data';
    return `${activeTrendData[0].label} — ${activeTrendData[activeTrendData.length - 1].label}`;
  }, [activeTrendData]);

  const trendTotal = activeTrendData.reduce((sum, point) => sum + point.count, 0);
  const defsLast12Months = allMonthlyTrend.slice(-12).reduce((sum, month) => sum + month.count, 0);
  const avgDefsPerInspection =
    data && data.total_inspections_12m > 0 ? defsLast12Months / data.total_inspections_12m : 0;
  const aboveTarget = avgDefsPerInspection > defTarget;

  const repeatDeficiencies = ((data?.repeat_deficiencies || []) as ApiRepeatDeficiencyGroup[])
    .map<RepeatDeficiencyGroup>((group) => ({
      ...group,
      vessels: (group.vessels || []).map((vessel) => ({
        vessel_id: vessel.vessel_id,
        vessel_name:
          (vessel as { vessel_name?: string }).vessel_name ??
          (vessel as { vesselName?: string }).vesselName ??
          '',
        vessel_code:
          (vessel as { vessel_code?: string }).vessel_code ??
          (vessel as { vesselcode?: string }).vesselcode,
      })),
    }))
    .filter((group) => group.repeat_count >= 2);
  const hasRepeatData = Array.isArray(data?.repeat_deficiencies);

  const navigateWithQuery = (
    route: string,
    query: Record<string, string | undefined>
  ) => {
    const params = new URLSearchParams();
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.set(key, value);
      }
    });
    const queryString = params.toString();
    navigate(queryString ? `${route}?${queryString}` : route);
  };

  const carVesselParam = scopedVesselId ? { vessel_id: scopedVesselId } : {};
  const inspectionsVesselParam = scopedVesselId ? { vessel_id: scopedVesselId } : {};

  const handleOpenInspections12m = () => {
    navigateWithQuery(ROUTES.INSPECTIONS, {
      date_from: daysAgo(365),
      ...inspectionsVesselParam,
    });
  };

  const handleOpenOverdueCars = () => {
    navigateWithQuery(ROUTES.CARS, {
      overdue: 'true',
      ...carVesselParam,
    });
  };

  const handleOpenDetentions = () => {
    navigateWithQuery(ROUTES.INSPECTIONS, {
      detention: 'true',
      date_from: daysAgo(365 * 3),
      ...inspectionsVesselParam,
    });
  };

  const handleOpenPVDue = () => {
    navigateWithQuery(ROUTES.CARS, {
      pv_due: 'true',
      ...carVesselParam,
    });
  };

  const handleOpenRepeatDeficiency = (
    group: RepeatDeficiencyGroup,
    vesselId?: string
  ) => {
    navigateWithQuery(ROUTES.DEFICIENCIES, {
      def_code: group.def_code,
      ...(vesselId ? { vessel_id: vesselId } : {}),
      ...(group.range_from ? { date_from: group.range_from } : {}),
      ...(group.range_to ? { date_to: group.range_to } : {}),
      dashboard_source: 'repeat_deficiencies',
      filter_pending: 'repeat_filters',
    });
  };

  const alertItems = (() => {
    const items: Array<{
      key: string;
      count: number;
      label: string;
      tone: 'danger' | 'warning';
      onClick: () => void;
    }> = [];

    if (data?.overdue_cars_count && data.overdue_cars_count > 0) {
      items.push({
        key: 'overdue-cars',
        count: data.overdue_cars_count,
        label: 'Overdue CAR(s)',
        tone: 'danger',
        onClick: handleOpenOverdueCars,
      });
    }

    if (pvDueCount > 0) {
      items.push({
        key: 'pv-due',
        count: pvDueCount,
        label: 'PV Due',
        tone: 'warning',
        onClick: handleOpenPVDue,
      });
    }

    return items;
  })();

  const handleOpenTargetDialog = () => {
    if (!isDPA) return;
    setTargetDraft(String(defTarget));
    setTargetOpen(true);
  };

  const handleSaveTarget = () => {
    const parsed = Number(targetDraft);
    if (!Number.isNaN(parsed) && parsed >= 0) {
      setDefTarget(parsed);
      setTargetDraft(String(parsed));
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(defTargetStorageKey, String(parsed));
        if (defTargetStorageKey !== DEF_TARGET_DEFAULT_KEY) {
          window.localStorage.setItem(DEF_TARGET_DEFAULT_KEY, String(parsed));
        }
      }
      setTargetOpen(false);
    }
  };

  const vesselFilter = isOffice && data?.vessels && data.vessels.length > 0 && (
    <Select
      value={selectedVessel || 'ALL'}
      onValueChange={(v) => setSelectedVessel(v === 'ALL' ? undefined : v)}
    >
      <SelectTrigger className="w-56">
        <SelectValue placeholder="All Vessels" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="ALL">All Vessels</SelectItem>
        {data.vessels.map((v) => (
          <SelectItem key={v.id} value={v.id}>
            {v.vessel_code} — {v.vessel_name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );

  const activeTrendRangeOptions = trendMode === 'monthly' ? monthRangeOptions : yearRangeOptions;
  const activeTrendRangeValue = trendMode === 'monthly' ? trendRangeMonths : trendRangeYears;

  return (
    <RootLayout>
      <PageHeader
        title="Dashboard"
        subtitle="Overview of inspections, CARs, and deficiencies"
        actions={vesselFilter || undefined}
      />

      {isLoading && <DashboardSkeleton />}

      {isError && (
        <ErrorState
          message={error?.message || 'Failed to load dashboard data.'}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && data && (
        <div className="space-y-6">
          {alertItems.length > 0 && (
            <div className="flex flex-col gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 sm:flex-row sm:items-center">
              <AlertTriangle className="h-5 w-5 flex-shrink-0 text-red-600" />
              <div className="flex flex-1 flex-wrap gap-2">
                {alertItems.map((item) => (
                  <Button
                    key={item.key}
                    size="sm"
                    variant="outline"
                    onClick={item.onClick}
                    className={
                      item.tone === 'danger'
                        ? 'border-red-300 bg-white text-red-700 hover:bg-red-100'
                        : 'border-amber-300 bg-white text-amber-800 hover:bg-amber-100'
                    }
                  >
                    <span className="mr-1 font-semibold">{item.count}</span>
                    {item.label}
                  </Button>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard
              icon={Ship}
              label="Inspections (12 mo)"
              value={data.total_inspections_12m}
              onClick={handleOpenInspections12m}
            />
            <StatCard
              icon={AlertTriangle}
              label="Overdue CARs"
              value={data.overdue_cars_count}
              variant={data.overdue_cars_count > 0 ? 'danger' : 'default'}
              onClick={handleOpenOverdueCars}
            />
            <StatCard
              icon={Anchor}
              label="Detentions (3 yr)"
              value={data.detentions_count}
              variant={data.detentions_count > 0 ? 'warning' : 'default'}
              onClick={handleOpenDetentions}
            />
            <StatCard
              icon={ShieldCheck}
              label="PV Due"
              value={pvDueCount}
              variant={pvDueCount > 0 ? 'warning' : 'default'}
              onClick={handleOpenPVDue}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_1.6fr]">
            <Card>
              <CardContent className="space-y-4 p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-700">Avg DEFs / Inspection</h3>
                  {isDPA && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 px-2 text-xs"
                      onClick={handleOpenTargetDialog}
                    >
                      <Target className="mr-1 h-3.5 w-3.5" />
                      Set Target
                    </Button>
                  )}
                </div>

                <div className="text-center">
                  <div
                    className={
                      aboveTarget
                        ? 'text-3xl font-bold text-red-700'
                        : 'text-3xl font-bold text-emerald-700'
                    }
                  >
                    {avgDefsPerInspection.toFixed(1)}
                  </div>
                  <p className="mt-1 text-xs text-neutral-500">DEFs / Inspection</p>
                  <div className="mx-auto mt-3 h-2 w-full max-w-xs rounded-full bg-neutral-100">
                    <div
                      className={aboveTarget ? 'h-2 rounded-full bg-red-500' : 'h-2 rounded-full bg-emerald-500'}
                      style={{
                        width: `${Math.min((avgDefsPerInspection / Math.max(defTarget * 2, 1)) * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-neutral-600">
                    Target: <span className="font-semibold">{defTarget.toFixed(1)}</span>
                  </p>
                  <span
                    className={
                      aboveTarget
                        ? 'mt-2 inline-block rounded bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700'
                        : 'mt-2 inline-block rounded bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700'
                    }
                  >
                    {aboveTarget
                      ? `${(avgDefsPerInspection - defTarget).toFixed(1)} above target`
                      : avgDefsPerInspection === defTarget
                        ? 'On target'
                        : `${(defTarget - avgDefsPerInspection).toFixed(1)} below target`}
                  </span>
                </div>

                <div className="grid grid-cols-3 divide-x rounded-md border border-neutral-200">
                  <div className="p-2 text-center">
                    <p className="text-lg font-semibold text-neutral-800">{data.total_inspections_12m}</p>
                    <p className="text-xs text-neutral-500">Inspections</p>
                  </div>
                  <div className="p-2 text-center">
                    <p className="text-lg font-semibold text-neutral-800">{defsLast12Months}</p>
                    <p className="text-xs text-neutral-500">Total DEFs</p>
                  </div>
                  <div className="p-2 text-center">
                    <p className="text-lg font-semibold text-neutral-800">{defTarget.toFixed(1)}</p>
                    <p className="text-xs text-neutral-500">Target</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                  <h3 className="text-sm font-medium text-gray-700">Deficiency Trend</h3>
                  <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:justify-end">
                    <div className="inline-flex rounded-md border border-neutral-200 bg-white p-0.5">
                      <Button
                        type="button"
                        size="sm"
                        variant={trendMode === 'monthly' ? 'default' : 'ghost'}
                        className="h-7 px-2 text-xs"
                        onClick={() => setTrendMode('monthly')}
                      >
                        Monthly
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant={trendMode === 'yearly' ? 'default' : 'ghost'}
                        className="h-7 px-2 text-xs"
                        onClick={() => setTrendMode('yearly')}
                      >
                        Yearly
                      </Button>
                    </div>

                    <Select
                      value={activeTrendRangeValue}
                      onValueChange={(value) => {
                        if (trendMode === 'monthly') {
                          setTrendRangeMonths(value);
                          return;
                        }
                        setTrendRangeYears(value);
                      }}
                      disabled={activeTrendRangeOptions.length === 0}
                    >
                      <SelectTrigger className="h-8 w-full sm:w-44">
                        <Calendar className="mr-1 h-3.5 w-3.5 text-neutral-500" />
                        <SelectValue placeholder="Select range" />
                      </SelectTrigger>
                      <SelectContent>
                        {activeTrendRangeOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="mb-3 min-h-4 max-w-full truncate text-xs text-neutral-500">{trendLabel}</div>

                {activeTrendData.length === 0 ? (
                  <div className="flex h-64 items-center justify-center rounded-md border border-dashed border-neutral-200 text-sm text-neutral-500">
                    No deficiency trend data available.
                  </div>
                ) : (
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={activeTrendData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis
                          dataKey="label"
                          tick={{ fontSize: 11 }}
                          tickLine={false}
                          axisLine={false}
                        />
                        <YAxis
                          allowDecimals={false}
                          tick={{ fontSize: 11 }}
                          tickLine={false}
                          axisLine={false}
                          width={30}
                        />
                        <Tooltip formatter={(value) => [value ?? 0, 'Deficiencies']} />
                        <Bar
                          dataKey="count"
                          fill="#3b82f6"
                          radius={[4, 4, 0, 0]}
                          maxBarSize={40}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <div className="mt-3 flex items-center justify-between gap-2 border-t border-neutral-200 pt-3">
                  <div className="text-sm text-neutral-600">
                    <span className="text-xl font-semibold text-neutral-800">{trendTotal}</span>
                    <span className="ml-2">
                      Total DEFs ({trendMode === 'monthly' ? `${monthlyTrend.length} mo` : `${yearlyTrend.length} yr`})
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <RepeatDeficienciesSection
              data={repeatDeficiencies}
              hasBackendData={hasRepeatData}
              onRowClick={(group) => handleOpenRepeatDeficiency(group)}
              onVesselClick={(group, vesselId) => handleOpenRepeatDeficiency(group, vesselId)}
            />
            <TopDefCodes data={data.top_def_codes} />
          </div>

          <Card>
            <CardContent className="p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <h3 className="text-sm font-medium text-gray-700">Recent Inspections</h3>
                <Button variant="ghost" size="sm" onClick={() => navigate(ROUTES.INSPECTIONS)}>
                  View All
                </Button>
              </div>

              {isRecentInspectionsLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 rounded-md" />
                  ))}
                </div>
              ) : inspections.length === 0 ? (
                <div className="rounded-md border border-dashed border-neutral-200 p-4 text-sm text-neutral-500">
                  No inspections available.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-[680px] w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-neutral-200">
                        <th className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Vessel</th>
                        <th className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Type</th>
                        <th className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Date</th>
                        <th className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">DEFs</th>
                        <th className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inspections.map((inspection) => (
                        <tr
                          key={inspection.id}
                          className="cursor-pointer border-b border-neutral-100 last:border-b-0 hover:bg-neutral-50 focus-within:bg-neutral-50"
                          onClick={() => navigate(ROUTES.INSPECTION_DETAIL(inspection.id))}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault();
                              navigate(ROUTES.INSPECTION_DETAIL(inspection.id));
                            }
                          }}
                        >
                          <td className="max-w-[240px] truncate px-3 py-2 font-medium text-neutral-800" title={inspection.vessel_name}>
                            {inspection.vessel_name}
                          </td>
                          <td className="px-3 py-2 text-neutral-600">{inspection.inspection_type}</td>
                          <td className="whitespace-nowrap px-3 py-2 text-neutral-600">{inspection.inspection_date}</td>
                          <td className="px-3 py-2 font-semibold text-neutral-800">{inspection.deficiency_count}</td>
                          <td className="px-3 py-2">
                            <StatusBadge status={inspection.operational_status as InspectionStatus} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {isDPA && (
            <Dialog open={targetOpen} onOpenChange={setTargetOpen}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>KPI Target Settings</DialogTitle>
                  <DialogDescription>
                    Set acceptable average deficiencies per inspection.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-2">
                  <label htmlFor="def-target" className="text-sm font-medium text-neutral-700">
                    Target: Avg DEFs per Inspection
                  </label>
                  <Input
                    id="def-target"
                    type="number"
                    min={0}
                    step={0.1}
                    value={targetDraft}
                    onChange={(event) => setTargetDraft(event.target.value)}
                  />
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={() => setTargetOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleSaveTarget}>Save Target</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
        </div>
      )}
    </RootLayout>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-lg" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_1.6fr]">
        <Skeleton className="h-72 rounded-lg" />
        <Skeleton className="h-72 rounded-lg" />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-72 rounded-lg" />
        <Skeleton className="h-72 rounded-lg" />
      </div>
      <Skeleton className="h-80 rounded-lg" />
    </div>
  );
}

export default DashboardPage;
