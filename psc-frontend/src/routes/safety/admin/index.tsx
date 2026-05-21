import { Link } from "react-router-dom";

import { useSafetyAuth } from "../../../hooks/safety/use-auth";

const adminCards = [
  {
    description: "M-SCAT, immediate causes, loss types, SOI template rows, checklist versions, and bias-guard visibility.",
    href: "/safety/admin/taxonomy",
    title: "Taxonomy Admin",
  },
  {
    description: "Navigator and Sinkfast seeded worked examples plus the DPA-managed case-study surface.",
    href: "/safety/admin/case-studies",
    title: "Case Study Library",
  },
] as const;

export default function SafetyAdminIndexRoute() {
  const auth = useSafetyAuth();
  const canOpenAuditorExport = auth.hasForm("SAF_F_020");

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#fff7ed_0%,#ffffff_48%,#dcfce7_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Admin
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Safety Admin</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Step 7.7 replaces the earlier placeholder shell with the DPA-only reference-data
          surfaces behind
          {" "}
          <code>SAF_F_018</code>
          . This handover page keeps the admin routes explicit while the backend now owns the
          actual reference CRUD and case-study seed contracts.
        </p>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        {adminCards.map((card) => (
          <article
            key={card.title}
            className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm"
          >
            <h2 className="text-xl font-semibold text-slate-900">{card.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{card.description}</p>
            <Link
              className="mt-5 inline-flex rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              to={card.href}
            >
              Open {card.title}
            </Link>
          </article>
        ))}
        {canOpenAuditorExport ? (
          <article className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Auditor Export</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Export the Auditor leave-behind ZIP from the dedicated Safety route protected by
              <code> SAF_F_020</code>.
            </p>
            <Link
              className="mt-5 inline-flex rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              to="/safety/admin/auditor-export"
            >
              Open Auditor Export
            </Link>
          </article>
        ) : null}
      </div>
    </section>
  );
}
