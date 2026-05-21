export interface SafetyHeinrichLayer {
  actual: number;
  benchmark: number;
  key: string;
  label: string;
  variance: number;
}

export interface SafetyHeinrichRatioPanelProps {
  confidence: {
    incidentCount12m: number;
    nearMissCount12m: number;
    reason: string;
    status: "AMBER" | "GREEN" | "RED";
    tooltip: string;
  };
  layers: SafetyHeinrichLayer[];
  reportingCultureGap: {
    isGap: boolean;
    message: string;
  };
}

const confidenceClassNames = {
  AMBER: "border-amber-200 bg-amber-50 text-amber-900",
  GREEN: "border-emerald-200 bg-emerald-50 text-emerald-900",
  RED: "border-rose-200 bg-rose-50 text-rose-900",
} as const;

export default function SafetyHeinrichRatioPanel({
  confidence,
  layers,
  reportingCultureGap,
}: SafetyHeinrichRatioPanelProps) {
  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Heinrich Ratio
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            Reporting-culture pyramid
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Rolling 3-year benchmark overlay using the stronger five-layer Safety
            dashboard contract from the docsuite.
          </p>
        </div>
        <div
          aria-label={`Confidence ${confidence.status}: ${confidence.tooltip}`}
          className={`rounded-2xl border px-4 py-3 text-sm ${confidenceClassNames[confidence.status]}`}
          title={confidence.tooltip}
        >
          <div className="text-xs font-semibold uppercase tracking-[0.18em]">
            Confidence
          </div>
          <div className="mt-2 text-lg font-semibold">{confidence.status}</div>
          <div className="mt-2 leading-6">
            {confidence.reason}
            <div className="text-xs">
              12M sample: {confidence.incidentCount12m} incidents / {confidence.nearMissCount12m} near misses
            </div>
          </div>
        </div>
      </div>

      {reportingCultureGap.isGap ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          {reportingCultureGap.message}
        </div>
      ) : null}

      <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            <tr>
              <th className="px-4 py-3">Layer</th>
              <th className="px-4 py-3">Benchmark</th>
              <th className="px-4 py-3">Actual</th>
              <th className="px-4 py-3">Ratio</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {layers.map((layer) => {
              const ratio = layer.benchmark > 0 ? Math.min((layer.actual / layer.benchmark) * 100, 100) : 0;
              return (
                <tr key={layer.key}>
                  <td className="px-4 py-3 font-medium text-slate-900">{layer.label}</td>
                  <td className="px-4 py-3 text-slate-600">{layer.benchmark}</td>
                  <td className="px-4 py-3 text-slate-900">{layer.actual}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-full max-w-[140px] rounded-full bg-slate-100">
                        <div
                          className="h-2 rounded-full bg-slate-900"
                          style={{ width: `${ratio}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-slate-600">
                        {layer.variance >= 0 ? "+" : ""}
                        {layer.variance}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
