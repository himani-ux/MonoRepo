import { Link, useParams } from "react-router-dom";

interface SafetyWorkflowBlockedProps {
  area: string;
  backLabel?: string;
  backTo?: string;
  requiredApi: string[];
  requiredGuarantees: string[];
  title: string;
}

export default function SafetyWorkflowBlocked({
  area,
  backLabel = "Back to Safety",
  backTo = "/safety",
  requiredApi,
  requiredGuarantees,
  title,
}: SafetyWorkflowBlockedProps) {
  const { findId, id } = useParams();
  const recordId = findId ?? id;

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-700">
          {area}
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-amber-950">{title}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-amber-900">
          This page is not available yet.
        </p>
        {recordId ? (
          <p className="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
            Record ID: {recordId}
          </p>
        ) : null}
      </header>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
            Pending work
          </h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-700">
            {requiredApi.map((item) => (
              <li
                key={item}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                {item}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
            SSOT guarantees before release
          </h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-700">
            {requiredGuarantees.map((item) => (
              <li
                key={item}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <Link
        className="inline-flex rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-700"
        to={backTo}
      >
        {backLabel}
      </Link>
    </section>
  );
}
