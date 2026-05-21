export interface SafetyCaAgingBucket {
  bucket: string;
  count: number;
  label: string;
}

export interface SafetyCaAgingPipelineProps {
  buckets: SafetyCaAgingBucket[];
  label: string;
  note: string;
  oldestAgeDays: number;
  openActionCount: number;
}

export default function SafetyCaAgingPipeline({
  buckets,
  label,
  note,
  oldestAgeDays,
  openActionCount,
}: SafetyCaAgingPipelineProps) {
  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            {label}
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            Corrective action pressure by age band
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{note}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          {openActionCount} open action{openActionCount === 1 ? "" : "s"} with the oldest aging at{" "}
          {oldestAgeDays} day{oldestAgeDays === 1 ? "" : "s"}.
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {buckets.map((bucket) => (
          <article
            key={bucket.bucket}
            className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4 shadow-sm"
          >
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              {bucket.label}
            </div>
            <div className="mt-3 text-3xl font-semibold text-slate-900">{bucket.count}</div>
            <div className="mt-3 h-2 rounded-full bg-white">
              <div
                className="h-2 rounded-full bg-slate-900"
                style={{
                  width: `${Math.min(bucket.count * 22, 100)}%`,
                }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
