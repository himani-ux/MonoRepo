import { formatVesselName, type SafetyVesselDisplaySource } from "../../../lib/safety/vessel-display";

export interface SafetyParetoEntry {
  categoryName: string;
  cumulativePercent: number;
  description: string;
  occurrences: number;
  rank: number;
  sharePercent: number;
  subcodeId: string;
  vesselCode?: string | null;
  vesselDisplayName?: string | null;
  vesselId: string;
  vesselName?: string | null;
  within80Cutoff: boolean;
}

export interface SafetyParetoPanelProps {
  entries: SafetyParetoEntry[];
  topN: number;
  totalOccurrences: number;
}

export default function SafetyParetoPanel({
  entries,
  topN,
  totalOccurrences,
}: SafetyParetoPanelProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Top causes
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            Top repeat issues over the last 12 months
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Ranked by repeat count so the strongest problem areas are easier to review.
          </p>
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Top {topN} causes covering {totalOccurrences} repeat events
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="mt-5 rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
          No repeat cause data is available for the current review window.
        </div>
      ) : (
        <div className="mt-5 space-y-3">
          {entries.map((entry) => (
            <article
              key={`${entry.vesselId}-${entry.subcodeId}`}
              className={`rounded-md border px-4 py-4 shadow-sm ${
                entry.within80Cutoff
                  ? "border-emerald-200 bg-emerald-50/60"
                  : "border-slate-200 bg-slate-50"
              }`}
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    <span>#{entry.rank}</span>
                    <span>{formatVesselName({
                      vessel_code: entry.vesselCode,
                      vessel_display_name: entry.vesselDisplayName,
                      vessel_id: entry.vesselId,
                      vessel_name: entry.vesselName,
                    } satisfies SafetyVesselDisplaySource)}</span>
                  </div>
                  <h3 className="mt-2 text-base font-semibold text-slate-900">
                    {entry.description}
                  </h3>
                  <p className="mt-1 text-sm text-slate-600">{entry.categoryName}</p>
                </div>

                <div className="flex flex-wrap gap-4 text-sm text-slate-700">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Occurrences
                    </div>
                    <div className="mt-1 text-lg font-semibold text-slate-900">{entry.occurrences}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Share
                    </div>
                    <div className="mt-1 text-lg font-semibold text-slate-900">{entry.sharePercent}%</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Cumulative
                    </div>
                    <div className="mt-1 text-lg font-semibold text-slate-900">{entry.cumulativePercent}%</div>
                  </div>
                </div>
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_160px] lg:items-center">
                <div className="h-3 rounded-full bg-white">
                  <div
                    className="h-3 rounded-full bg-slate-900"
                    style={{ width: `${Math.min(entry.sharePercent, 100)}%` }}
                  />
                </div>
                <div className="rounded-full border border-slate-300 bg-white px-3 py-1 text-center text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                  {entry.within80Cutoff ? "Main issue" : "Other issue"}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
