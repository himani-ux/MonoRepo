const legacySectionItems = [
  "1. Structured Review",
  "2. Quality and Safety Practice",
  "3. Security",
  "4. Environment",
  "5. Health",
  "6. Crew Welfare",
  "7. PSC Findings & Corrective Measures",
  "8. Minutes of Meeting",
  "9. Office Review",
];

export default function SafetyScmPdfRoute() {
  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            SCM Export
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">
            SCM Legacy PDF
          </h2>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
            Legacy Section Order
          </h3>
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            {legacySectionItems.map((item) => (
              <li
                key={item}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-4">
          <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
              Summary Blocks
            </h3>
            <ul className="mt-4 space-y-2 text-sm text-slate-700">
              <li className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                Closed-Since-Last SCM Summary
              </li>
              <li className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                Attendance + WRH flags
              </li>
              <li className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                Master and CO signature box
              </li>
            </ul>
          </article>
        </div>
      </div>
    </section>
  );
}
