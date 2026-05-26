const caseStudies = [
  {
    basic: "5, 8, 12",
    immediate: "5, 10x2, 16, 17, 39",
    summary: "Grounding worked solution for bridge-team supervision, alarm management, and route review.",
    title: "Navigator",
    type: "Type 14 Grounding",
  },
  {
    basic: "4.9, 5, 9, 12.7, 16",
    immediate: "2, 4, 8, 17, 25, 33",
    summary: "Pump-room explosion worked solution focused on permits, gas detection, tanker competence, and supervision.",
    title: "Sinkfast",
    type: "Type 16/17 Fire and Explosion",
  },
] as const;

export default function SafetyCaseStudyLibraryPanel() {
  return (
    <section className="space-y-4">
      <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Case Study Library
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">Navigator + Sinkfast</h2>
      </article>

      <div className="grid gap-4 xl:grid-cols-2">
        {caseStudies.map((study) => (
          <article
            key={study.title}
            className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">{study.title}</h3>
                <p className="mt-1 text-sm text-slate-600">{study.type}</p>
              </div>
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">
                Seeded
              </span>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-700">{study.summary}</p>
            <dl className="mt-4 grid gap-3 text-sm text-slate-700">
              <div className="rounded-2xl bg-slate-50 px-4 py-3">
                <dt className="font-semibold text-slate-900">Immediate codes</dt>
                <dd className="mt-1">{study.immediate}</dd>
              </div>
              <div className="rounded-2xl bg-slate-50 px-4 py-3">
                <dt className="font-semibold text-slate-900">Basic codes</dt>
                <dd className="mt-1">{study.basic}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
