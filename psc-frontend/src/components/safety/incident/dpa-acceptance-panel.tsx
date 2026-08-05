import type { SafetyIncidentPhase7Preflight } from "../../../schemas/safety/incident-phase7";

interface SafetyDpaAcceptancePanelProps {
  blockers?: string[];
  preflight: SafetyIncidentPhase7Preflight;
}

function formatBlockerLabel(value: string) {
  return value.replace(/_/g, " ");
}

export default function SafetyDpaAcceptancePanel({
  blockers,
  preflight,
}: SafetyDpaAcceptancePanelProps) {
  const visibleBlockers = blockers ?? preflight.blockers;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Root causes
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {preflight.root_count}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Actions
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {Object.values(preflight.recommendation_tier_count).reduce((sum, count) => sum + Number(count || 0), 0)}
          </p>
        </article>
      </section>

      <section className="grid gap-6">
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Before Office Review Approval</h3>
          {visibleBlockers.length === 0 ? (
            <p className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              Ready for office approval.
            </p>
          ) : (
            <ul className="space-y-2 text-sm text-slate-700">
              {visibleBlockers.map((blocker) => (
                <li
                  key={blocker}
                  className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 capitalize text-amber-900"
                >
                  {formatBlockerLabel(blocker)}
                </li>
              ))}
            </ul>
          )}

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            <p className="font-semibold text-slate-900">Draft PDF</p>
            <p className="mt-2">{preflight.pdf_preview.message}</p>
          </div>
        </div>

      </section>
    </div>
  );
}
