export interface SafetyRepeatRootRadarItem {
  categoryName: string;
  description: string;
  occurrences: number;
  relativeStrength: number;
  subcodeId: string;
  vesselCount: number;
}

export interface SafetyRepeatRootRadarProps {
  fleet: SafetyRepeatRootRadarItem[];
  minimumRepeatCount: number;
  vessel: SafetyRepeatRootRadarItem[];
}

function buildRadarPoints(items: SafetyRepeatRootRadarItem[]) {
  if (items.length === 0) {
    return "";
  }

  return items.map((item, index) => {
    const angle = ((Math.PI * 2) / items.length) * index - Math.PI / 2;
    const radius = 30 + (item.relativeStrength / 100) * 70;
    const x = 110 + Math.cos(angle) * radius;
    const y = 110 + Math.sin(angle) * radius;
    return `${x},${y}`;
  }).join(" ");
}

function SafetyRadarScope({
  items,
  title,
}: {
  items: SafetyRepeatRootRadarItem[];
  title: string;
}) {
  if (items.length === 0) {
    return (
      <article className="rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
        <h3 className="font-semibold text-slate-900">{title}</h3>
        <p className="mt-2 leading-6">No repeat issues met the current level.</p>
      </article>
    );
  }

  const points = buildRadarPoints(items.slice(0, 6));

  return (
    <article className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        <div className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
          Top {items.length}
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)] lg:items-center">
        <svg
          aria-label={`${title} repeat issue chart`}
          className="mx-auto"
          height="220"
          viewBox="0 0 220 220"
          width="220"
        >
          <circle cx="110" cy="110" r="30" fill="none" stroke="#e2e8f0" />
          <circle cx="110" cy="110" r="65" fill="none" stroke="#cbd5e1" strokeDasharray="4 6" />
          <circle cx="110" cy="110" r="100" fill="none" stroke="#94a3b8" strokeDasharray="4 6" />
          {items.slice(0, 6).map((item, index) => {
            const angle = ((Math.PI * 2) / Math.min(items.length, 6)) * index - Math.PI / 2;
            const x = 110 + Math.cos(angle) * 100;
            const y = 110 + Math.sin(angle) * 100;
            return (
              <line
                key={item.subcodeId}
                x1="110"
                x2={x}
                y1="110"
                y2={y}
                stroke="#cbd5e1"
                strokeDasharray="3 5"
              />
            );
          })}
          <polygon fill="rgba(15, 23, 42, 0.16)" points={points} stroke="#0f172a" strokeWidth="2" />
          {items.slice(0, 6).map((item, index) => {
            const angle = ((Math.PI * 2) / Math.min(items.length, 6)) * index - Math.PI / 2;
            const radius = 30 + (item.relativeStrength / 100) * 70;
            const x = 110 + Math.cos(angle) * radius;
            const y = 110 + Math.sin(angle) * radius;
            return <circle key={`${item.subcodeId}-dot`} cx={x} cy={y} fill="#0f172a" r="4" />;
          })}
        </svg>

        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.subcodeId} className="rounded-md border border-white bg-white px-4 py-3 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-slate-900">{item.description}</div>
                  <div className="mt-1 text-xs text-slate-500">{item.categoryName}</div>
                </div>
                <div className="text-right text-sm font-semibold text-slate-900">
                  {item.occurrences}
                  <div className="text-xs font-medium text-slate-500">
                    {item.vesselCount} vessel{item.vesselCount === 1 ? "" : "s"}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}

export default function SafetyRepeatRootRadar({
  fleet,
  minimumRepeatCount,
  vessel,
}: SafetyRepeatRootRadarProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Repeat issues
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            Recurring safety issues
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Shows issues that are appearing again across the fleet or the selected vessel.
          </p>
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Showing {minimumRepeatCount}+ repeats
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        <SafetyRadarScope items={fleet} title="Fleet" />
        <SafetyRadarScope items={vessel} title="Current vessel" />
      </div>
    </section>
  );
}
