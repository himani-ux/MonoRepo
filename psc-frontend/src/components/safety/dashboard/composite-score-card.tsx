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
  AMBER: "border-amber-200 bg-amber-50 text-amber-950",
  GREEN: "border-emerald-200 bg-emerald-50 text-emerald-950",
  RED: "border-rose-200 bg-rose-50 text-rose-950",
} as const;

const componentLabels: Record<string, string> = {
  open_findings: "Open findings",
  open_incidents: "Open incidents",
  open_near_misses: "Open near misses",
  overdue_corrective_actions: "Overdue CAs",
  soi_compliance: "SOI Compliance %",
};

export default function SafetyCompositeScoreCard({
  componentScores,
  compositeScore,
  countNote,
  description,
  metrics,
  scoreStatus,
}: SafetyCompositeScoreCardProps) {
  return (
    <section className={`rounded-[2rem] border px-6 py-6 shadow-sm ${statusClassNames[scoreStatus]}`}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Safety Health Score
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">{compositeScore}</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">{description}</p>
        </div>
        <div className="rounded-2xl border border-current/20 bg-white/70 px-4 py-3 text-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Current signal
          </div>
          <div className="mt-2 text-lg font-semibold text-slate-900">{scoreStatus}</div>
          <div className="mt-2 text-sm text-slate-700">{countNote}</div>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-5">
        <article className="rounded-2xl border border-white/60 bg-white/80 px-4 py-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Open incidents
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.openIncidents}</div>
        </article>
        <article className="rounded-2xl border border-white/60 bg-white/80 px-4 py-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Open near misses
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.openNearMisses}</div>
        </article>
        <article className="rounded-2xl border border-white/60 bg-white/80 px-4 py-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Open findings
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.openFindings}</div>
        </article>
        <article className="rounded-2xl border border-white/60 bg-white/80 px-4 py-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Overdue CAs
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.overdueCorrectiveActions}</div>
        </article>
        <article className="rounded-2xl border border-white/60 bg-white/80 px-4 py-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {metrics.soiComplianceLabel}
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{metrics.soiComplianceDisplay}</div>
        </article>
      </div>

      <div className="mt-6 grid gap-3 lg:grid-cols-5">
        {Object.entries(componentScores).map(([key, value]) => (
          <article
            key={key}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm"
          >
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              {componentLabels[key] ?? key}
            </div>
            <div className="mt-3 h-2 rounded-full bg-slate-100">
              <div
                className="h-2 rounded-full bg-slate-900 transition-all"
                style={{ width: `${value}%` }}
              />
            </div>
            <div className="mt-3 text-sm font-medium text-slate-700">{value} / 100</div>
          </article>
        ))}
      </div>
    </section>
  );
}
