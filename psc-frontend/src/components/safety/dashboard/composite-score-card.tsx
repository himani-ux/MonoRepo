export interface SafetyCompositeScoreCardProps {
  componentScores: Record<string, number>;
  compositeScore: number;
  countNote: string;
  description: string;
  metrics: {
    openFindings: number;
    openIncidents: number;
    openNearMisses: number;
    overdueCorrectiveActions: number;
    soiComplianceDisplay: string;
    soiComplianceLabel: string;
  };
  scoreStatus: "AMBER" | "GREEN" | "RED";
}

const statusClassNames = {
  AMBER: "border-amber-300 bg-amber-50 text-amber-900",
  GREEN: "border-emerald-300 bg-emerald-50 text-emerald-900",
  RED: "border-rose-300 bg-rose-50 text-rose-900",
} as const;

const statusLabels: Record<SafetyCompositeScoreCardProps["scoreStatus"], string> = {
  AMBER: "Watch",
  GREEN: "Good",
  RED: "Needs attention",
};

export default function SafetyCompositeScoreCard({
  compositeScore,
  countNote,
  description,
  metrics,
  scoreStatus,
}: SafetyCompositeScoreCardProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white px-5 py-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Safety score
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">{compositeScore}</h2>
          <p className="mt-2 text-sm font-semibold text-slate-800">
            0 to 100 scale. Higher is better.
          </p>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
            This combines open incidents, near misses, findings, overdue actions, and SOI checks for the selected view. {description}
          </p>
        </div>
        <div className={`rounded-md border px-4 py-3 text-sm ${statusClassNames[scoreStatus]}`}>
          <div className="text-xs font-semibold uppercase tracking-[0.18em]">Overall condition</div>
          <div className="mt-2 text-lg font-semibold">{statusLabels[scoreStatus]}</div>
          <div className="mt-2 text-sm text-slate-700">{countNote}</div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <article className="rounded-md border border-slate-200 bg-slate-50 px-4 py-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Open incidents
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.openIncidents}</div>
        </article>
        <article className="rounded-md border border-slate-200 bg-slate-50 px-4 py-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Open near misses
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.openNearMisses}</div>
        </article>
        <article className="rounded-md border border-slate-200 bg-slate-50 px-4 py-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Open findings
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.openFindings}</div>
        </article>
        <article className="rounded-md border border-slate-200 bg-slate-50 px-4 py-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Overdue actions
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.overdueCorrectiveActions}</div>
        </article>
        <article className="rounded-md border border-slate-200 bg-slate-50 px-4 py-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {metrics.soiComplianceLabel}
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.soiComplianceDisplay}</div>
        </article>
      </div>
    </section>
  );
}
