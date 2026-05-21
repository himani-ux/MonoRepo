import { useEffect, useMemo, useState } from "react";

import SafetyCaAgingPipeline from "../../../components/safety/dashboard/ca-aging-pipeline";
import SafetyCompositeScoreCard from "../../../components/safety/dashboard/composite-score-card";
import SafetyHeinrichRatioPanel from "../../../components/safety/dashboard/heinrich-ratio-panel";
import SafetyParetoPanel from "../../../components/safety/dashboard/pareto-panel";
import SafetyRepeatRootRadar from "../../../components/safety/dashboard/repeat-root-radar";
import SafetySoiCompliancePanel from "../../../components/safety/dashboard/soi-compliance-panel";
import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import {
  useSafetyDashboardCaAging,
  useSafetyDashboardComposite,
  useSafetyDashboardHeinrich,
  useSafetyDashboardPareto,
  useSafetyDashboardRepeatRoot,
  useSafetyDashboardSoiCompliance,
} from "../../../hooks/use-safety";
import {
  safetyApi,
  type SafetyDashboardPeriodCode,
  type SafetyDashboardVesselOption,
} from "../../../lib/api/safety";
import {
  buildSafetyDashboardPeriodScopeKey,
  useSafetyDashboardPeriodStore,
} from "../../../stores/safety/dashboard-period-store";

const periodOptions: Array<{
  description: string;
  id: SafetyDashboardPeriodCode;
  label: string;
}> = [
  { id: "90D", label: "90D", description: "Operational view focused on the current 90-day window." },
  { id: "12M", label: "12M", description: "Annual trend view using the same backend rollup contract." },
  { id: "3Y", label: "3Y", description: "Rolling 3-year baseline for the Safety health score." },
];

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Safety dashboard data could not be loaded.";
}

function buildCountNote(metrics: {
  open_findings: number;
  open_incidents: number;
  open_near_misses: number;
  overdue_corrective_actions: number;
}) {
  return `${metrics.open_incidents} incident(s), ${metrics.open_near_misses} near miss(es), ${metrics.open_findings} open finding(s), and ${metrics.overdue_corrective_actions} overdue corrective action(s) are in the current score window.`;
}

function buildScopeLabel(
  scopeType: "FLEET" | "VESSEL",
  scopeId: string,
  selectedVessel?: SafetyDashboardVesselOption | null,
) {
  if (scopeType === "FLEET") {
    return "Fleet scope";
  }
  if (selectedVessel) {
    return `${selectedVessel.vessel_code || selectedVessel.id} - ${selectedVessel.vessel_name}`;
  }
  return scopeId ? `Vessel ${scopeId}` : "Current vessel";
}

function buildVesselOptionLabel(vessel: SafetyDashboardVesselOption) {
  const code = vessel.vessel_code.trim();
  const name = vessel.vessel_name.trim();
  if (code && name) {
    return `${code} - ${name}`;
  }
  return name || code || vessel.id;
}

function DashboardLoadingState() {
  return (
    <section className="space-y-4" role="status">
      {Array.from({ length: 5 }).map((_, index) => (
        <div
          key={index}
          className="h-36 animate-pulse rounded-[1.75rem] border border-slate-200 bg-slate-100"
        />
      ))}
    </section>
  );
}

export default function SafetyDashboardRoute() {
  const auth = useSafetyAuth();
  const bindScope = useSafetyDashboardPeriodStore((state) => state.bindScope);
  const period = useSafetyDashboardPeriodStore((state) => state.period);
  const setPeriod = useSafetyDashboardPeriodStore((state) => state.setPeriod);
  const [exportFormat, setExportFormat] = useState<"excel" | "pdf">("pdf");
  const [exportError, setExportError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [selectedVesselId, setSelectedVesselId] = useState<string>("");
  const canExport = auth.role?.trim().toUpperCase() === "DPA" && auth.hasProcess("SAF_P_023");
  const dashboardScopeKey = buildSafetyDashboardPeriodScopeKey({
    id: auth.user?.id,
    role: auth.role,
    vesselIds: auth.vesselIds,
  });

  useEffect(() => {
    bindScope(dashboardScopeKey);
  }, [bindScope, dashboardScopeKey]);

  const authVesselId = auth.vesselIds[0] ? String(auth.vesselIds[0]) : null;
  const vesselId = auth.isGlobal ? selectedVesselId || null : authVesselId;
  const compositeQuery = useSafetyDashboardComposite(period, vesselId);
  const heinrichQuery = useSafetyDashboardHeinrich(vesselId);
  const repeatRootQuery = useSafetyDashboardRepeatRoot(vesselId);
  const paretoQuery = useSafetyDashboardPareto(vesselId);
  const soiComplianceQuery = useSafetyDashboardSoiCompliance(vesselId);
  const caAgingQuery = useSafetyDashboardCaAging(vesselId);
  const availableVessels = compositeQuery.data?.available_vessels ?? [];
  const selectedVessel = useMemo(
    () => availableVessels.find((vessel) => vessel.id === vesselId) ?? null,
    [availableVessels, vesselId],
  );
  const hasVesselSelector = auth.isGlobal && availableVessels.length > 0;

  useEffect(() => {
    if (!auth.isGlobal) {
      setSelectedVesselId("");
      return;
    }

    if (!selectedVesselId) {
      return;
    }

    if (!availableVessels.some((vessel) => vessel.id === selectedVesselId)) {
      setSelectedVesselId("");
    }
  }, [auth.isGlobal, availableVessels, selectedVesselId]);

  const isLoading =
    compositeQuery.isLoading ||
    heinrichQuery.isLoading ||
    repeatRootQuery.isLoading ||
    paretoQuery.isLoading ||
    soiComplianceQuery.isLoading ||
    caAgingQuery.isLoading;

  const firstError =
    compositeQuery.error ||
    heinrichQuery.error ||
    repeatRootQuery.error ||
    paretoQuery.error ||
    soiComplianceQuery.error ||
    caAgingQuery.error;

  const scopeSummary = compositeQuery.data
    ? buildScopeLabel(compositeQuery.data.scope_type, compositeQuery.data.scope_id, selectedVessel)
    : auth.isGlobal
      ? "Fleet scope"
      : "Current vessel";

  const currentVesselCard = useMemo(() => {
    if (!soiComplianceQuery.data) {
      return {
        applicableAreaCount: 0,
        displayValue: "N/A - awaiting first cycle",
        inspectedAreaCount: 0,
        overdueAreaCount: 0,
        status: "NA" as const,
        vesselLabel: auth.isGlobal ? "Vessel drill-down" : "Current vessel",
      };
    }

    if (auth.isGlobal && !vesselId) {
      return {
        applicableAreaCount: 0,
        displayValue: "Select a vessel to load vessel-level SOI compliance.",
        inspectedAreaCount: 0,
        overdueAreaCount: 0,
        status: "NA" as const,
        vesselLabel: "Vessel drill-down",
      };
    }

    return {
      applicableAreaCount: soiComplianceQuery.data.current_vessel.applicable_area_count,
      displayValue: soiComplianceQuery.data.current_vessel.display_value,
      inspectedAreaCount: soiComplianceQuery.data.current_vessel.inspected_area_count,
      overdueAreaCount: soiComplianceQuery.data.current_vessel.overdue_area_count,
      status:
        soiComplianceQuery.data.current_vessel.status === "GREEN" ||
        soiComplianceQuery.data.current_vessel.status === "AMBER" ||
        soiComplianceQuery.data.current_vessel.status === "RED"
          ? soiComplianceQuery.data.current_vessel.status
          : "NA",
      vesselLabel: selectedVessel
        ? buildVesselOptionLabel(selectedVessel)
        : auth.isGlobal
          ? "Selected vessel"
          : "Current vessel",
    };
  }, [auth.isGlobal, selectedVessel, soiComplianceQuery.data, vesselId]);

  async function handleExport() {
    if (!canExport) {
      return;
    }

    setExportError(null);
    setIsExporting(true);
    try {
      const result = await safetyApi.exportDashboard({
        format: exportFormat,
        period,
        vessel_id: vesselId,
      });
      const downloadUrl = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = result.fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      setExportError(getErrorMessage(error));
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_45%,#dcfce7_100%)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Safety / Dashboard
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">
              Safety Intelligence Dashboard
            </h1>
            <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
              Live operational rollups for incidents, near misses, SOI compliance, repeat
              root-cause clusters, and corrective-action aging.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div>Scope: {scopeSummary}</div>
            <div>Viewer role: {auth.role ?? "Unknown"}</div>
          </div>
        </div>
      </header>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Score window</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Select the backend rollup period. The chosen period is stored per user on this device.
            </p>
          </div>
          <div className="flex flex-col gap-3 lg:items-end">
            {hasVesselSelector ? (
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
                <span>Select vessel drill-down</span>
                <select
                  aria-label="Select vessel drill-down"
                  className="min-w-[18rem] rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-500"
                  onChange={(event) => setSelectedVesselId(event.target.value)}
                  value={selectedVesselId}
                >
                  <option value="">Fleet overview</option>
                  {availableVessels.map((vessel) => (
                    <option key={vessel.id} value={vessel.id}>
                      {buildVesselOptionLabel(vessel)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <div className="flex flex-wrap gap-2">
              {periodOptions.map((option) => {
                const isActive = option.id === period;
                return (
                  <button
                    key={option.id}
                    aria-pressed={isActive}
                    className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "bg-slate-900 text-white"
                        : "border border-slate-300 bg-white text-slate-700 hover:border-slate-500"
                    }`}
                    onClick={() => setPeriod(option.id)}
                    type="button"
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="mt-4 grid gap-3 lg:grid-cols-3">
          {periodOptions.map((option) => (
            <article key={option.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                {option.label}
              </div>
              <div className="mt-2 text-sm leading-6 text-slate-700">{option.description}</div>
            </article>
          ))}
        </div>
      </section>

      {isLoading ? <DashboardLoadingState /> : null}

      {firstError ? (
        <section className="rounded-[1.75rem] border border-rose-200 bg-rose-50 p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-rose-900">Dashboard unavailable</h2>
          <p className="mt-2 text-sm leading-6 text-rose-700">{getErrorMessage(firstError)}</p>
        </section>
      ) : null}

      {!isLoading &&
      !firstError &&
      compositeQuery.data &&
      heinrichQuery.data &&
      repeatRootQuery.data &&
      paretoQuery.data &&
      soiComplianceQuery.data &&
      caAgingQuery.data ? (
        <>
          <SafetyCompositeScoreCard
            componentScores={compositeQuery.data.component_scores}
            compositeScore={compositeQuery.data.composite_score}
            countNote={buildCountNote(compositeQuery.data.metrics)}
            description={`Live ${period} score for ${buildScopeLabel(
              compositeQuery.data.scope_type,
              compositeQuery.data.scope_id,
              selectedVessel,
            )}, calculated from current Safety records between ${compositeQuery.data.window_start} and ${compositeQuery.data.window_end}.`}
            metrics={{
              openFindings: compositeQuery.data.metrics.open_findings,
              openIncidents: compositeQuery.data.metrics.open_incidents,
              openNearMisses: compositeQuery.data.metrics.open_near_misses,
              overdueCorrectiveActions: compositeQuery.data.metrics.overdue_corrective_actions,
              soiComplianceDisplay:
                compositeQuery.data.metrics.soi_compliance_display ?? "N/A",
              soiComplianceLabel: compositeQuery.data.metrics.soi_compliance_label,
            }}
            scoreStatus={compositeQuery.data.score_status}
          />

          <SafetyHeinrichRatioPanel
            confidence={{
              incidentCount12m: heinrichQuery.data.confidence.incident_count_12m,
              nearMissCount12m: heinrichQuery.data.confidence.near_miss_count_12m,
              reason: heinrichQuery.data.confidence.reason,
              status: heinrichQuery.data.confidence.status,
              tooltip: heinrichQuery.data.confidence.tooltip,
            }}
            layers={heinrichQuery.data.layers}
            reportingCultureGap={{
              isGap: heinrichQuery.data.reporting_culture_gap.is_gap,
              message: heinrichQuery.data.reporting_culture_gap.message,
            }}
          />

          <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
            <SafetySoiCompliancePanel
              currentVessel={currentVesselCard}
              fleetAverage={{
                displayValue: soiComplianceQuery.data.fleet_average.display_value,
                note: soiComplianceQuery.data.fleet_average.note,
                vesselCount: soiComplianceQuery.data.fleet_average.vessel_count,
              }}
              label={soiComplianceQuery.data.label}
            />
            <aside className="rounded-[1.75rem] border border-slate-200 bg-slate-900 p-5 text-slate-100 shadow-sm">
              <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-300">
                Rollup Window
              </h2>
              <ul className="mt-4 space-y-3 text-sm leading-6">
                <li>Composite score window: {compositeQuery.data.window_start} to {compositeQuery.data.window_end}.</li>
                <li>Heinrich view: {heinrichQuery.data.window_start} to {heinrichQuery.data.window_end}.</li>
                <li>Repeat-root radar threshold: {repeatRootQuery.data.minimum_repeat_count}+ repeats.</li>
                <li>Pareto total recurring events: {paretoQuery.data.total_occurrences}.</li>
                <li>Oldest open corrective action age: {caAgingQuery.data.oldest_age_days} day(s).</li>
              </ul>
            </aside>
          </section>

          <SafetyRepeatRootRadar
            fleet={repeatRootQuery.data.fleet.map((item) => ({
              categoryName: item.category_name,
              description: item.description,
              occurrences: item.occurrences,
              relativeStrength: item.relative_strength,
              subcodeId: item.subcode_id,
              vesselCount: item.vessel_count,
            }))}
            minimumRepeatCount={repeatRootQuery.data.minimum_repeat_count}
            vessel={repeatRootQuery.data.vessel.map((item) => ({
              categoryName: item.category_name,
              description: item.description,
              occurrences: item.occurrences,
              relativeStrength: item.relative_strength,
              subcodeId: item.subcode_id,
              vesselCount: item.vessel_count,
            }))}
          />

          <SafetyParetoPanel
            entries={paretoQuery.data.entries.map((entry) => ({
              categoryName: entry.category_name,
              cumulativePercent: entry.cumulative_percent,
              description: entry.description,
              occurrences: entry.occurrences,
              rank: entry.rank,
              sharePercent: entry.share_percent,
              subcodeId: entry.subcode_id,
              vesselCode: entry.vessel_code,
              vesselDisplayName: entry.vessel_display_name,
              vesselId: entry.vessel_id,
              vesselName: entry.vessel_name,
              within80Cutoff: entry.within_80_cutoff,
            }))}
            topN={paretoQuery.data.top_n}
            totalOccurrences={paretoQuery.data.total_occurrences}
          />

          <SafetyCaAgingPipeline
            buckets={caAgingQuery.data.buckets}
            label={caAgingQuery.data.label}
            note={caAgingQuery.data.note}
            oldestAgeDays={caAgingQuery.data.oldest_age_days}
            openActionCount={caAgingQuery.data.open_action_count}
          />

          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                  Dashboard Export
                </p>
                <h2 className="mt-2 text-xl font-semibold text-slate-900">
                  Real PDF and Excel export
                </h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                  The export action now calls the live dashboard export endpoint for the selected
                  period and current scope.
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                {canExport
                  ? "Export enabled for DPA with SAF_P_023."
                  : "Export is limited to DPA users with SAF_P_023."}
              </div>
            </div>

            <div className="mt-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap gap-2">
                <button
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    exportFormat === "pdf"
                      ? "bg-slate-900 text-white"
                      : "border border-slate-300 bg-white text-slate-700 hover:border-slate-500"
                  }`}
                  onClick={() => setExportFormat("pdf")}
                  type="button"
                >
                  PDF
                </button>
                <button
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    exportFormat === "excel"
                      ? "bg-slate-900 text-white"
                      : "border border-slate-300 bg-white text-slate-700 hover:border-slate-500"
                  }`}
                  onClick={() => setExportFormat("excel")}
                  type="button"
                >
                  Excel
                </button>
              </div>

              <button
                className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={!canExport || isExporting}
                onClick={handleExport}
                type="button"
              >
                {isExporting ? "Preparing export..." : `Download ${exportFormat.toUpperCase()}`}
              </button>
            </div>

            {exportError ? (
              <p className="mt-4 text-sm text-rose-700" role="alert">
                {exportError}
              </p>
            ) : null}
          </section>
        </>
      ) : null}
    </section>
  );
}
