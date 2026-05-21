const legacySectionItems = [
  "1. Structured Review",
  "2. Outstanding Items",
  "3. Safety Practice",
  "4. Security",
  "5. Environment",
  "6. Health",
  "7. Crew",
  "8. Findings & Corrective Measures",
  "9. Miscellaneous",
  "10. Office Review",
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
            10-Section Legacy PDF
          </h2>
          <p className="mt-3 max-w-3xl text-sm text-slate-600">
            Step 6.4 now exposes the live backend route at
            {" "}
            <code>/api/safety/scm/:id/pdf/</code>
            {" "}
            and keeps the
            {" "}
            <code>/api/safety/export/scm/:id/pdf/</code>
            {" "}
            alias alive for docs drift. The PDF preserves the locked legacy
            {" "}
            <code>vw_GetSCM_Master</code>
            {" "}
            10-section order, adds the Closed-Since-Last summary block at the top,
            and keeps attendance plus signature status inline.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Permission: <span className="font-semibold text-slate-900">SAF_P_023</span>
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
                Master + CO + attendee signature status
              </li>
            </ul>
          </article>
        </div>
      </div>
    </section>
  );
}
