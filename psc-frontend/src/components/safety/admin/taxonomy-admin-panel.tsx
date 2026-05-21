const taxonomySections = [
  {
    action: "SAF_P_018",
    count: "174 rows",
    endpoint: "/api/safety/reference/mscat/",
    title: "M-SCAT taxonomy",
  },
  {
    action: "SAF_P_018",
    count: "52 rows",
    endpoint: "/api/safety/reference/immediate-causes/",
    title: "Immediate causes",
  },
  {
    action: "SAF_P_018",
    count: "7 rows",
    endpoint: "/api/safety/reference/loss-types/",
    title: "Loss types",
  },
  {
    action: "read only",
    count: "8 rows",
    endpoint: "/api/safety/reference/bias-guards/",
    title: "Bias guards",
  },
  {
    action: "SAF_P_019",
    count: "13 areas",
    endpoint: "/api/safety/reference/soi-areas/",
    title: "SOI area template",
  },
  {
    action: "SAF_P_019",
    count: "329 items",
    endpoint: "/api/safety/reference/soi-items/",
    title: "SOI checklist items",
  },
  {
    action: "SAF_P_019",
    count: "versioned",
    endpoint: "/api/safety/reference/soi-checklist-versions/",
    title: "SOI checklist versions",
  },
  {
    action: "SAF_P_018",
    count: "11 rows",
    endpoint: "/api/safety/reference/incident-types/",
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
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Step 7.7 completes the DPA-only reference-data surface behind
          {" "}
          <code>SAF_F_018</code>
          {" "}
          and splits write actions between
          {" "}
          <code>SAF_P_018</code>
          {" "}
          for incident-side reference data and
          {" "}
          <code>SAF_P_019</code>
          {" "}
          for SOI taxonomy maintenance.
        </p>
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
              <span className="rounded-full border border-slate-300 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-600">
                {section.action}
              </span>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-700">
              Endpoint:
              {" "}
              <code>{section.endpoint}</code>
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
