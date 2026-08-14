export interface SafetyCompositeScoreCardProps {
  componentScores: Record<string, number>;
  countNote: string;
  description: string;
  metrics: {
    openFindings: number;
    openIncidents: number;
    openNearMisses: number;
    overdueCorrectiveActions: number;
    soiComplianceDisplay: string;
    soiComplianceLabel: string;
    totalCorrectiveActions: number;
    totalFindings: number;
    totalIncidents: number;
    totalNearMisses: number;
  };
  scoreStatus: "AMBER" | "GREEN" | "RED";
}

const statusClassNames = {
  AMBER: "border-amber-200 bg-amber-50 text-amber-800",
  GREEN: "border-emerald-200 bg-emerald-50 text-emerald-800",
  RED: "border-rose-200 bg-rose-50 text-rose-800",
} as const;

const statusLabels: Record<SafetyCompositeScoreCardProps["scoreStatus"], string> = {
  AMBER: "Watch",
  GREEN: "Good",
  RED: "Needs attention",
};

const openWorkColors = ["#5b8db8", "#5aa59d", "#d69a61", "#d97979"];
const pieCenter = 64;
const pieRadius = 50;

function HoverDetail({ text }: { text: string }) {
  return (
    <div
      className="pointer-events-none absolute right-3 top-3 z-20 hidden max-w-[18rem] rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-medium leading-5 text-slate-700 shadow-lg group-hover:block group-focus-within:block"
      role="note"
    >
      {text}
    </div>
  );
}

function formatScoreLabel(key: string) {
  const labels: Record<string, string> = {
    open_findings: "Finding closure",
    open_incidents: "Incident control",
    open_near_misses: "Near miss follow-up",
    overdue_corrective_actions: "Action closure",
    soi_compliance: "SOI checks",
  };
  if (labels[key]) {
    return labels[key];
  }
  return key
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getScorePartStatus(value: number) {
  if (value >= 80) {
    return {
      className: "border-teal-200 bg-teal-100 text-teal-800",
      label: "Good",
      progressClassName: "bg-teal-500",
    };
  }
  if (value >= 60) {
    return {
      className: "border-amber-200 bg-amber-100 text-amber-800",
      label: "Watch",
      progressClassName: "bg-amber-400",
    };
  }
  return {
    className: "border-rose-200 bg-rose-100 text-rose-800",
    label: "Needs attention",
    progressClassName: "bg-rose-400",
  };
}

function polarToCartesian(angle: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return {
    x: pieCenter + pieRadius * Math.cos(radians),
    y: pieCenter + pieRadius * Math.sin(radians),
  };
}

function buildPieSlices(
  data: Array<{ color: string; label: string; value: number }>,
  total: number,
) {
  let startAngle = 0;
  return data.map((item) => {
    const angle = total > 0 ? (Math.max(0, item.value) / total) * 360 : 0;
    const endAngle = startAngle + angle;
    const start = polarToCartesian(startAngle);
    const end = polarToCartesian(endAngle);
    const largeArc = angle > 180 ? 1 : 0;
    const path =
      angle >= 360
        ? ""
        : [
            `M ${pieCenter} ${pieCenter}`,
            `L ${start.x} ${start.y}`,
            `A ${pieRadius} ${pieRadius} 0 ${largeArc} 1 ${end.x} ${end.y}`,
            "Z",
          ].join(" ");
    const slice = {
      ...item,
      angle,
      path,
      percent: total > 0 ? Math.round((Math.max(0, item.value) / total) * 100) : 0,
    };
    startAngle = endAngle;
    return slice;
  });
}

export default function SafetyCompositeScoreCard({
  componentScores,
  countNote,
  description,
  metrics,
  scoreStatus,
}: SafetyCompositeScoreCardProps) {
  const metricCards = [
    {
      help: "All incident reports counted in the selected period and vessel view.",
      label: "Total incidents",
      value: metrics.totalIncidents,
    },
    {
      help: "All near miss reports counted in the selected period and vessel view.",
      label: "Total near misses",
      value: metrics.totalNearMisses,
    },
    {
      help: "All SOI findings counted in the selected period and vessel view.",
      label: "Total findings",
      value: metrics.totalFindings,
    },
    {
      help: "All corrective actions counted in the selected period and vessel view.",
      label: "Total actions",
      value: metrics.totalCorrectiveActions,
    },
    {
      help: "How many planned SOI checks are currently completed or still acceptable.",
      label: metrics.soiComplianceLabel,
      value: metrics.soiComplianceDisplay,
    },
  ];

  const openWorkData = [
    { color: openWorkColors[0], label: "Incidents", value: metrics.openIncidents },
    { color: openWorkColors[1], label: "Near misses", value: metrics.openNearMisses },
    { color: openWorkColors[2], label: "Findings", value: metrics.openFindings },
    { color: openWorkColors[3], label: "Overdue", value: metrics.overdueCorrectiveActions },
  ];

  const scoreBreakdownData = Object.entries(componentScores)
    .map(([key, value]) => ({
      label: formatScoreLabel(key),
      value: Math.max(0, Math.min(100, Number(value) || 0)),
    }))
    .filter((item) => item.label && Number.isFinite(item.value))
    .sort((left, right) => left.value - right.value);
  const totalOpenWork = openWorkData.reduce((sum, item) => sum + item.value, 0);
  const pieSlices = buildPieSlices(openWorkData, totalOpenWork);
  const weakestScorePart = scoreBreakdownData[0] ?? null;

  return (
    <section className="space-y-4">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <article
          className={`group relative rounded-lg border px-4 py-4 shadow-sm ${statusClassNames[scoreStatus]}`}
          tabIndex={0}
        >
          <HoverDetail text="A quick health check for the selected view. It summarizes whether safety work is normal, needs watching, or needs attention." />
          <div className="text-xs font-semibold uppercase tracking-[0.14em]">Overall status</div>
          <div className="mt-2 text-2xl font-semibold">{statusLabels[scoreStatus]}</div>
          <div className="mt-1 text-sm font-medium">Based on current checks</div>
        </article>

        {metricCards.map((card) => (
          <article
            key={card.label}
            className="group relative rounded-lg border border-sky-100 bg-white px-4 py-4 shadow-sm"
            tabIndex={0}
          >
            <HoverDetail text={card.help} />
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {card.label}
            </div>
            <div className="mt-2 text-2xl font-semibold text-slate-900">{card.value}</div>
          </article>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <article
          className="group relative flex h-full flex-col rounded-lg border border-sky-100 bg-sky-50/40 p-4 shadow-sm"
          tabIndex={0}
        >
          <HoverDetail text="Shows only the work still waiting for action, split by report type." />
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Open work</h2>
              <p className="mt-1 text-xs text-slate-500">Current items by type.</p>
            </div>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-sky-100">
              {metrics.openIncidents +
                metrics.openNearMisses +
                metrics.openFindings +
                metrics.overdueCorrectiveActions}{" "}
              open items
            </span>
          </div>
          <div className="mt-5 flex flex-1 flex-col items-center justify-center gap-5">
            <div className="relative h-72 w-72 max-w-full sm:h-80 sm:w-80">
              <svg
                aria-label="Open work chart"
                className="h-full w-full"
                role="img"
                viewBox="0 0 128 128"
              >
                <circle
                  cx={pieCenter}
                  cy={pieCenter}
                  fill="#eef6f9"
                  r={pieRadius}
                />
                {totalOpenWork > 0
                  ? pieSlices.map((slice) =>
                      slice.angle >= 360 ? (
                        <circle
                          key={slice.label}
                          cx={pieCenter}
                          cy={pieCenter}
                          fill={slice.color}
                          r={pieRadius}
                          stroke="#ffffff"
                          strokeWidth="2"
                        />
                      ) : (
                        <path
                          key={slice.label}
                          d={slice.path}
                          fill={slice.color}
                          stroke="#ffffff"
                          strokeLinejoin="round"
                          strokeWidth="2"
                        />
                      ),
                    )
                  : null}
                <circle
                  cx={pieCenter}
                  cy={pieCenter}
                  fill="none"
                  r={pieRadius}
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              </svg>
            </div>

            <div className="grid w-full gap-3 sm:grid-cols-2">
              {pieSlices.map((item) => (
                <div key={item.label} className="flex items-center justify-between gap-3 rounded-md bg-white px-3 py-2 ring-1 ring-sky-100">
                  <span className="flex min-w-0 items-center gap-2 text-sm font-medium text-slate-700">
                    <span
                      aria-hidden="true"
                      className="h-3 w-3 shrink-0 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="truncate">{item.label}</span>
                  </span>
                  <span className="text-sm font-semibold text-slate-900">
                    {item.value}
                    {totalOpenWork > 0 ? (
                      <span className="ml-2 text-xs font-medium text-slate-500">{item.percent}%</span>
                    ) : null}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article
          className="group relative rounded-lg border border-teal-200 bg-[#e6f1ef] p-4 shadow-sm"
          tabIndex={0}
        >
          <HoverDetail text="Shows which safety areas are helping or lowering the overall status. The lowest item appears first." />
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Score breakdown</h2>
              <p className="mt-1 text-xs text-slate-500">Lowest score appears first.</p>
            </div>
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusClassNames[scoreStatus]}`}>
              {statusLabels[scoreStatus]}
            </span>
          </div>
          {scoreBreakdownData.length > 0 ? (
            <div className="mt-5 space-y-4">
              {weakestScorePart ? (
                <div className="rounded-md border border-teal-200 bg-[#d8ece8] px-4 py-3 shadow-sm">
                  <div className="text-xs font-semibold uppercase text-teal-700">
                    Pulling score down most
                  </div>
                  <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-slate-900">
                      {weakestScorePart.label}
                    </div>
                    <div className="text-2xl font-semibold text-slate-900">
                      {weakestScorePart.value}
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="space-y-3">
                {scoreBreakdownData.map((item) => {
                  const status = getScorePartStatus(item.value);
                  return (
                    <div key={item.label} className="rounded-md bg-[#f3faf8] px-3 py-3 shadow-sm ring-1 ring-teal-100">
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-slate-900">
                            {item.label}
                          </div>
                          <div className="mt-1 text-xs text-slate-500">Score out of 100</div>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${status.className}`}>
                            {status.label}
                          </span>
                          <span className="w-9 text-right text-sm font-semibold text-slate-900">
                            {item.value}
                          </span>
                        </div>
                      </div>
                      <div className="mt-3 h-2 rounded-full bg-teal-100/80">
                        <div
                          className={`h-2 rounded-full ${status.progressClassName}`}
                          style={{ width: `${item.value}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="mt-4 flex h-52 items-center justify-center rounded-md bg-[#f3faf8] text-sm text-slate-500">
              Score details are not available.
            </div>
          )}
        </article>
      </div>

      <p className="rounded-lg border border-sky-100 bg-white px-4 py-3 text-sm leading-6 text-slate-700 shadow-sm">
        {countNote} {description}
      </p>
    </section>
  );
}
