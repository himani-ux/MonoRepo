const taxonomySections = [
  {
    count: "174 rows",
    title: "M-SCAT taxonomy",
  },
  {
    count: "52 rows",
    title: "Immediate causes",
  },
  {
    count: "7 rows",
    title: "Loss types",
  },
  {
    count: "8 rows",
    title: "Bias guards",
  },
  {
    count: "13 areas",
    title: "SOI area template",
  },
  {
    count: "329 items",
    title: "SOI checklist items",
  },
  {
    count: "versioned",
    title: "SOI checklist versions",
  },
  {
    count: "11 rows",
    title: "Incident types",
  },
] as const;

export default function SafetyTaxonomyAdminPanel() {
  return (
    <section className="space-y-4">
      <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Reference Admin
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">Taxonomy Admin</h2>
      </article>

      <div className="grid gap-4 xl:grid-cols-2">
        {taxonomySections.map((section) => (
          <article
            key={section.title}
            className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">{section.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{section.count}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
