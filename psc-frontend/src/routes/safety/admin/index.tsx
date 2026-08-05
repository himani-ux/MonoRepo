import { Link } from "react-router-dom";

import { useSafetyAuth } from "../../../hooks/safety/use-auth";

const adminCards = [
  {
    description: "Manage cause lists, loss types, SOI templates, checklist versions, and review visibility.",
    href: "/safety/admin/taxonomy",
    title: "Safety Lists",
  },
  {
    description: "Manage training and review case studies.",
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
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Safety Admin</h1>
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
            <p className="mt-3 text-sm leading-6 text-slate-600">Export the Safety audit package.</p>
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
