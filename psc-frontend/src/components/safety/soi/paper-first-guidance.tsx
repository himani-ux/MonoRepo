const PAPER_FIRST_STEPS = [
  {
    body: "Generate the checklist as PDF or Excel. The first download allocates the unique paper link ID.",
    title: "1. Download",
  },
  {
    body: "Run the inspection on paper with the Safety Officer and cross-functional assistant signatures captured on the checklist.",
    title: "2. Field work on paper",
  },
  {
    body: "File the signed paper in the ship SMS filing system. The paper copy remains the checklist record of truth.",
    title: "3. File in SMS",
  },
  {
    body: "Register findings in VIMS by the same checklist unique ID. No scan upload exists in this workflow.",
    title: "4. Register findings digitally",
  },
];

export default function SafetyPaperFirstGuidance() {
  return (
    <section className="rounded-[1.75rem] border border-rose-200 bg-gradient-to-br from-white via-rose-50 to-amber-50 p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Paper-first guidance</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Step 4.5 keeps the paper checklist authoritative. VIMS generates the pack
            and preserves the unique link ID, but the per-item checklist stays on paper.
          </p>
        </div>
        <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-rose-800">
          No scan upload
        </span>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {PAPER_FIRST_STEPS.map((step) => (
          <article
            key={step.title}
            className="rounded-2xl border border-white/80 bg-white/90 p-4 shadow-sm"
          >
            <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              {step.title}
            </h3>
            <p className="mt-3 text-sm leading-6 text-slate-700">{step.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
