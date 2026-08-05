import type { SafetyIncidentPhase5Assessment } from "../../../schemas/safety/incident-phase5";

interface SafetyHumanFactorsPanelProps {
  assessment: SafetyIncidentPhase5Assessment | null | undefined;
}

export function SafetyHumanFactorsPanel({
  assessment,
}: SafetyHumanFactorsPanelProps) {
  const shell = assessment?.human_factors_payload?.shell as
    | { selected?: string; notes?: string }
    | undefined;
  const domains = assessment?.human_factors_payload?.domains as
    | Record<string, { considered?: boolean; not_applicable?: boolean; notes?: string }>
    | undefined;
  const entries = Object.entries(domains ?? {});

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        Human factors review
      </p>
      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        Human Factors
      </h2>
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
          Selected factor
        </p>
        <p className="mt-2 text-sm font-semibold text-slate-900">
          {shell?.selected?.replaceAll("_", " ") || "Not selected"}
        </p>
        {shell?.notes ? (
          <p className="mt-2 break-words text-sm leading-6 text-slate-700">{shell.notes}</p>
        ) : null}
      </div>
      <div className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
        {entries.length > 0 ? (
          entries.map(([domain, value]) => (
            <article
              key={domain}
              className="min-w-0 rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                {domain.replaceAll("_", " ")}
              </p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                {value.not_applicable ? "N/A" : value.considered ? "Considered" : "Pending"}
              </p>
              <p className="mt-2 break-words text-sm leading-6 text-slate-900">
                {value.notes?.trim() || "Reviewed"}
              </p>
            </article>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
            No human-factor domain notes have been saved yet.
          </div>
        )}
      </div>
    </section>
  );
}

export default SafetyHumanFactorsPanel;
